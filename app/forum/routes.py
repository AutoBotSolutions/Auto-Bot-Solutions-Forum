from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from app import db, limiter
from app.models import Post, Comment, Repository, Vote, Category, Bookmark, Notification
from app.forum.forms import PostForm, CommentForm

forum_bp = Blueprint('forum', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'md'}
UPLOAD_FOLDER = 'app/static/uploads'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@forum_bp.route('/')
def index():
    category_id = request.args.get('category', type=int)
    if category_id:
        posts = Post.query.filter_by(category_id=category_id).order_by(Post.created_at.desc()).all()
        category = Category.query.get(category_id)
    else:
        posts = Post.query.order_by(Post.created_at.desc()).all()
        category = None
    categories = Category.query.all()
    return render_template('forum/index.html', posts=posts, categories=categories, current_category=category)

@forum_bp.route('/repository/<int:repo_id>')
def repository_posts(repo_id):
    repository = Repository.query.get_or_404(repo_id)
    posts = repository.posts.order_by(Post.created_at.desc()).all()
    return render_template('forum/repository.html', repository=repository, posts=posts)

@forum_bp.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = post.comments.order_by(Comment.created_at.asc()).all()
    form = CommentForm()
    return render_template('forum/post.html', post=post, comments=comments, form=form)

@forum_bp.route('/create', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour")
def create_post():
    form = PostForm()
    form.repository_id.choices = [(0, 'None')] + [(r.id, r.name) for r in Repository.query.all()]
    form.category_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        attachment = None
        if form.attachment.data and allowed_file(form.attachment.data.filename):
            filename = secure_filename(form.attachment.data.filename)
            # Create uploads directory if it doesn't exist
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            # Add timestamp to filename to make it unique
            import time
            timestamp = str(int(time.time()))
            filename = f"{timestamp}_{filename}"
            form.attachment.data.save(os.path.join(UPLOAD_FOLDER, filename))
            attachment = filename
        
        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id,
            repository_id=form.repository_id.data if form.repository_id.data else None,
            category_id=form.category_id.data if form.category_id.data else None,
            attachment=attachment
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('forum.post', post_id=post.id))
    return render_template('forum/create.html', form=form)

@forum_bp.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
@limiter.limit("20 per hour")
def add_comment(post_id):
    return create_comment(post_id)

@forum_bp.route('/create_comment/<int:post_id>', methods=['POST'])
@login_required
@limiter.limit("20 per hour")
def create_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            post_id=post.id
        )
        db.session.add(comment)
        db.session.flush()  # Get comment ID without committing
        
        # Create notification for post author if commenter is not the author
        if post.user_id != current_user.id:
            from app.notification.routes import create_notification
            notification = create_notification(
                post.user_id,
                f'{current_user.username} commented on your post "{post.title}"',
                url_for('forum.post', post_id=post.id),
                notification_type='comment'
            )
        else:
            db.session.commit()
        
        # Broadcast real-time comment notification
        try:
            from flask import current_app
            if hasattr(current_app, 'websocket_service'):
                comment_data = {
                    'id': comment.id,
                    'content': comment.content,
                    'author': {
                        'id': current_user.id,
                        'username': current_user.username
                    },
                    'created_at': comment.created_at.isoformat(),
                    'post_id': post.id
                }
                current_app.websocket_service.broadcast_new_comment(post.id, comment_data)
                
                # Send notification to post author
                if post.user_id != current_user.id:
                    notification_data = {
                        'id': notification.id if 'notification' in locals() else None,
                        'type': 'comment',
                        'content': f'{current_user.username} commented on your post "{post.title}"',
                        'link': url_for('forum.post', post_id=post.id),
                        'timestamp': comment.created_at.isoformat()
                    }
                    current_app.websocket_service.broadcast_notification(post.user_id, notification_data)
        except Exception as e:
            # Log error but don't fail the comment creation
            import logging
            logging.getLogger(__name__).error(f"WebSocket notification failed: {str(e)}")
        
        flash('Comment added!', 'success')
    return redirect(url_for('forum.post', post_id=post.id))

@forum_bp.route('/vote/post/<int:post_id>/<int:value>')
@login_required
@limiter.limit("30 per minute")
def vote_post(post_id, value):
    if value not in [1, -1]:
        flash('Invalid vote value', 'error')
        return redirect(request.referrer or url_for('forum.index'))
    
    post = Post.query.get_or_404(post_id)
    existing_vote = Vote.query.filter_by(
        user_id=current_user.id,
        post_id=post_id,
        comment_id=None
    ).first()
    
    if existing_vote:
        if existing_vote.value == value:
            db.session.delete(existing_vote)
            if value == 1:
                post.upvotes -= 1
            else:
                post.downvotes -= 1
        else:
            existing_vote.value = value
            if value == 1:
                post.upvotes += 1
                post.downvotes -= 1
            else:
                post.downvotes += 1
                post.upvotes -= 1
    else:
        vote = Vote(user_id=current_user.id, post_id=post_id, value=value)
        db.session.add(vote)
        if value == 1:
            post.upvotes += 1
        else:
            post.downvotes += 1
    
    db.session.commit()
    
    # Broadcast real-time vote update
    try:
        from flask import current_app
        if hasattr(current_app, 'websocket_service'):
            vote_data = {
                'user_id': current_user.id,
                'username': current_user.username,
                'vote_type': 'up' if value == 1 else 'down',
                'upvotes': post.upvotes,
                'downvotes': post.downvotes,
                'total_votes': post.upvotes + post.downvotes,
                'post_id': post.id
            }
            current_app.websocket_service.broadcast_vote_update('post', post.id, vote_data)
    except Exception as e:
        # Log error but don't fail the vote
        import logging
        logging.getLogger(__name__).error(f"WebSocket vote notification failed: {str(e)}")
    
    return redirect(request.referrer or url_for('forum.index'))

@forum_bp.route('/vote/comment/<int:comment_id>/<int:value>')
@login_required
@limiter.limit("30 per minute")
def vote_comment(comment_id, value):
    if value not in [1, -1]:
        flash('Invalid vote value', 'error')
        return redirect(request.referrer or url_for('forum.index'))
    
    comment = Comment.query.get_or_404(comment_id)
    existing_vote = Vote.query.filter_by(
        user_id=current_user.id,
        comment_id=comment_id,
        post_id=None
    ).first()
    
    if existing_vote:
        if existing_vote.value == value:
            db.session.delete(existing_vote)
            if value == 1:
                comment.upvotes -= 1
            else:
                comment.downvotes -= 1
        else:
            existing_vote.value = value
            if value == 1:
                comment.upvotes += 1
                comment.downvotes -= 1
            else:
                comment.downvotes += 1
                comment.upvotes -= 1
    else:
        vote = Vote(user_id=current_user.id, comment_id=comment_id, value=value)
        db.session.add(vote)
        if value == 1:
            comment.upvotes += 1
        else:
            comment.downvotes += 1
    
    db.session.commit()
    
    # Broadcast real-time vote update for comment
    try:
        from flask import current_app
        if hasattr(current_app, 'websocket_service'):
            vote_data = {
                'user_id': current_user.id,
                'username': current_user.username,
                'vote_type': 'up' if value == 1 else 'down',
                'upvotes': comment.upvotes,
                'downvotes': comment.downvotes,
                'total_votes': comment.upvotes + comment.downvotes,
                'comment_id': comment.id,
                'post_id': comment.post_id
            }
            current_app.websocket_service.broadcast_vote_update('comment', comment.id, vote_data)
    except Exception as e:
        # Log error but don't fail the vote
        import logging
        logging.getLogger(__name__).error(f"WebSocket comment vote notification failed: {str(e)}")
    
    return redirect(request.referrer or url_for('forum.index'))

@forum_bp.route('/bookmark/<int:post_id>')
@login_required
def toggle_bookmark(post_id):
    post = Post.query.get_or_404(post_id)
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if bookmark:
        db.session.delete(bookmark)
        flash('Bookmark removed.', 'info')
    else:
        bookmark = Bookmark(user_id=current_user.id, post_id=post_id)
        db.session.add(bookmark)
        flash('Post bookmarked!', 'success')
    
    db.session.commit()
    return redirect(request.referrer or url_for('forum.post', post_id=post_id))

@forum_bp.route('/bookmarks')
@login_required
def bookmarks():
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.created_at.desc()).all()
    return render_template('forum/bookmarks.html', bookmarks=bookmarks)

@forum_bp.route('/search')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return redirect(url_for('forum.index'))
    
    # Search in posts
    posts = Post.query.filter(
        (Post.title.ilike(f'%{query}%')) | 
        (Post.content.ilike(f'%{query}%'))
    ).order_by(Post.created_at.desc()).all()
    
    # Search in comments
    comments = Comment.query.filter(
        Comment.content.ilike(f'%{query}%')
    ).order_by(Comment.created_at.desc()).all()
    
    return render_template('forum/search.html', query=query, posts=posts, comments=comments)

@forum_bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
@limiter.limit("10 per hour")
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if user is the author or admin
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You can only edit your own posts.', 'error')
        return redirect(url_for('forum.post', post_id=post_id))
    
    form = PostForm(obj=post)
    form.repository_id.choices = [(0, 'None')] + [(r.id, r.name) for r in Repository.query.all()]
    form.category_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        # Store original values for audit trail
        original_title = post.title
        original_content = post.content
        
        # Update post
        post.title = form.title.data
        post.content = form.content.data
        post.repository_id = form.repository_id.data if form.repository_id.data else None
        post.category_id = form.category_id.data if form.category_id.data else None
        post.updated_at = datetime.utcnow()
        
        # Handle attachment update
        if form.attachment.data and allowed_file(form.attachment.data.filename):
            # Remove old attachment if exists
            if post.attachment:
                old_attachment_path = os.path.join(UPLOAD_FOLDER, post.attachment)
                if os.path.exists(old_attachment_path):
                    os.remove(old_attachment_path)
            
            # Save new attachment
            filename = secure_filename(form.attachment.data.filename)
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            
            import time
            timestamp = str(int(time.time()))
            filename = f"{timestamp}_{filename}"
            form.attachment.data.save(os.path.join(UPLOAD_FOLDER, filename))
            post.attachment = filename
        
        db.session.commit()
        
        # Create edit audit log
        from app.models import AuditLog
        audit_log = AuditLog(
            user_id=current_user.id,
            action='edit_post',
            target_type='post',
            target_id=post.id,
            old_values={'title': original_title, 'content': original_content},
            new_values={'title': post.title, 'content': post.content},
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('Post updated successfully!', 'success')
        return redirect(url_for('forum.post', post_id=post_id))
    
    return render_template('forum/edit.html', form=form, post=post)

@forum_bp.route('/delete/<int:post_id>', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if user is the author or admin
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You can only delete your own posts.', 'error')
        return redirect(url_for('forum.post', post_id=post_id))
    
    # Create delete audit log
    from app.models import AuditLog
    audit_log = AuditLog(
        user_id=current_user.id,
        action='delete_post',
        target_type='post',
        target_id=post.id,
        old_values={'title': post.title, 'content': post.content},
        new_values={'deleted': True},
        ip_address=request.remote_addr
    )
    db.session.add(audit_log)
    
    # Remove attachment if exists
    if post.attachment:
        attachment_path = os.path.join(UPLOAD_FOLDER, post.attachment)
        if os.path.exists(attachment_path):
            os.remove(attachment_path)
    
    # Delete post (cascade delete will handle comments and votes)
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('forum.index'))

@forum_bp.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if user is the author or admin
    if comment.user_id != current_user.id and not current_user.is_admin:
        flash('You can only edit your own comments.', 'error')
        return redirect(url_for('forum.post', post_id=comment.post_id))
    
    form = CommentForm(obj=comment)
    
    if form.validate_on_submit():
        # Store original content for audit trail
        original_content = comment.content
        
        # Update comment
        comment.content = form.content.data
        comment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Create edit audit log
        from app.models import AuditLog
        audit_log = AuditLog(
            user_id=current_user.id,
            action='edit_comment',
            target_type='comment',
            target_id=comment.id,
            old_values={'content': original_content},
            new_values={'content': comment.content},
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('Comment updated successfully!', 'success')
        return redirect(url_for('forum.post', post_id=comment.post_id))
    
    return render_template('forum/edit_comment.html', form=form, comment=comment)

@forum_bp.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    
    # Check if user is the author or admin
    if comment.user_id != current_user.id and not current_user.is_admin:
        flash('You can only delete your own comments.', 'error')
        return redirect(url_for('forum.post', post_id=post_id))
    
    # Create delete audit log
    from app.models import AuditLog
    audit_log = AuditLog(
        user_id=current_user.id,
        action='delete_comment',
        target_type='comment',
        target_id=comment.id,
        old_values={'content': comment.content},
        new_values={'deleted': True},
        ip_address=request.remote_addr
    )
    db.session.add(audit_log)
    
    # Delete comment (cascade delete will handle votes)
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('forum.post', post_id=post_id))

@forum_bp.route('/moderate')
@login_required
def moderate_posts():
    # Only admins can access moderation
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('forum.index'))
    
    # Get posts that need moderation (flagged posts)
    posts = Post.query.filter(Post.is_flagged == True).order_by(Post.created_at.desc()).all()
    
    return render_template('forum/moderate.html', posts=posts)

@forum_bp.route('/moderate_post/<int:post_id>/<string:action>', methods=['POST'])
@login_required
def moderate_post(post_id, action):
    # Only admins can moderate
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('forum.index'))
    
    post = Post.query.get_or_404(post_id)
    
    if action == 'approve':
        post.is_flagged = False
        post.moderation_status = 'approved'
        flash('Post approved and unflagged.', 'success')
    elif action == 'delete':
        # Create moderation audit log
        from app.models import AuditLog
        audit_log = AuditLog(
            user_id=current_user.id,
            action='moderate_delete_post',
            target_type='post',
            target_id=post.id,
            old_values={'title': post.title, 'moderation_status': post.moderation_status},
            new_values={'deleted': True, 'moderation_status': 'deleted_by_moderator'},
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        
        # Remove attachment if exists
        if post.attachment:
            attachment_path = os.path.join(UPLOAD_FOLDER, post.attachment)
            if os.path.exists(attachment_path):
                os.remove(attachment_path)
        
        db.session.delete(post)
        flash('Post deleted by moderator.', 'success')
    elif action == 'flag':
        post.is_flagged = True
        post.moderation_status = 'flagged'
        flash('Post flagged for moderation.', 'success')
    
    db.session.commit()
    return redirect(url_for('forum.moderate_posts'))
