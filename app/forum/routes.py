from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
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

@forum_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
@limiter.limit("20 per hour")
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            post_id=post.id
        )
        db.session.add(comment)
        
        # Create notification for post author if commenter is not the author
        if post.user_id != current_user.id:
            notification = Notification(
                user_id=post.user_id,
                content=f'{current_user.username} commented on your post "{post.title}"',
                link=url_for('forum.post', post_id=post.id)
            )
            db.session.add(notification)
        
        db.session.commit()
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
