"""
Content Management Routes

This module contains routes for the enhanced content management system,
including draft management, versioning, scheduling, and collaboration features.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Post, PostVersion, PostCollaborator, User, Category
from app.content.forms import (
    PostForm, DraftForm, VersionForm, ScheduleForm, CollaborationForm,
    ContentSearchForm, BulkActionForm, ExpirationForm, ArchiveForm,
    ContentAnalyticsForm, AutoSaveSettingsForm, VersionCompareForm,
    ContentImportForm, ContentExportForm, ContentPermissionForm
)
from app import db
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

content_bp = Blueprint('content', __name__, url_prefix='/content')

@content_bp.route('/dashboard')
@login_required
def dashboard():
    """Content management dashboard"""
    # Get user's content statistics
    total_posts = Post.query.filter_by(user_id=current_user.id).count()
    published_posts = Post.query.filter_by(user_id=current_user.id, is_draft=False).count()
    draft_posts = Post.query.filter_by(user_id=current_user.id, is_draft=True).count()
    scheduled_posts = Post.query.filter_by(user_id=current_user.id, is_scheduled=True).count()
    
    # Get recent activity
    recent_posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.updated_at.desc()).limit(5).all()
    recent_versions = PostVersion.query.filter_by(edited_by=current_user.id).order_by(PostVersion.created_at.desc()).limit(5).all()
    
    # Get scheduled posts that need attention
    upcoming_scheduled = Post.query.filter_by(user_id=current_user.id, is_scheduled=True).filter(
        Post.scheduled_publish_at <= datetime.utcnow() + timedelta(days=7)
    ).all()
    
    # Get expiring posts
    expiring_posts = Post.query.filter_by(user_id=current_user.id).filter(
        Post.expires_at <= datetime.utcnow() + timedelta(days=7)
    ).filter(Post.expires_at > datetime.utcnow()).all()
    
    return render_template('content/dashboard.html',
                         total_posts=total_posts,
                         published_posts=published_posts,
                         draft_posts=draft_posts,
                         scheduled_posts=scheduled_posts,
                         recent_posts=recent_posts,
                         recent_versions=recent_versions,
                         upcoming_scheduled=upcoming_scheduled,
                         expiring_posts=expiring_posts)

@content_bp.route('/posts')
@login_required
def posts():
    """List and manage posts with advanced filtering"""
    form = ContentSearchForm(request.args)
    query = Post.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if form.validate():
        if form.query.data:
            query = query.filter(Post.title.contains(form.query.data) | Post.content.contains(form.query.data))
        
        if form.content_type.data != 'all':
            if form.content_type.data == 'published':
                query = query.filter_by(is_draft=False)
            elif form.content_type.data == 'draft':
                query = query.filter_by(is_draft=True)
            elif form.content_type.data == 'scheduled':
                query = query.filter_by(is_scheduled=True)
        
        if form.date_from.data:
            query = query.filter(Post.created_at >= form.date_from.data)
        
        if form.date_to.data:
            query = query.filter(Post.created_at <= form.date_to.data)
        
        if form.author_id.data:
            query = query.filter_by(user_id=form.author_id.data)
        
        if form.category_id.data and form.category_id.data != 0:
            query = query.filter_by(category_id=form.category_id.data)
    
    posts = query.order_by(Post.updated_at.desc()).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=20,
        error_out=False
    )
    
    return render_template('content/posts.html', posts=posts, form=form)

@content_bp.route('/drafts')
@login_required
def drafts():
    """Manage draft posts"""
    drafts = Post.query.filter_by(user_id=current_user.id, is_draft=True).order_by(Post.updated_at.desc()).all()
    return render_template('content/drafts.html', drafts=drafts)

@content_bp.route('/scheduled')
@login_required
def scheduled():
    """Manage scheduled posts"""
    scheduled_posts = Post.query.filter_by(user_id=current_user.id, is_scheduled=True).order_by(Post.scheduled_publish_at.asc()).all()
    return render_template('content/scheduled.html', scheduled_posts=scheduled_posts)

@content_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new post with enhanced content management"""
    form = PostForm()
    
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id,
            category_id=form.category_id.data if form.category_id.data else None,
            is_draft=form.is_draft.data,
            is_scheduled=form.is_scheduled.data,
            scheduled_publish_at=form.scheduled_publish_at.data if form.is_scheduled.data else None,
            expires_at=form.expires_at.data,
            engagement_score=form.engagement_score.data or 0.0
        )
        
        db.session.add(post)
        db.session.commit()
        
        # Create initial version
        version = PostVersion(
            post_id=post.id,
            version_number=1,
            title=post.title,
            content=post.content,
            edited_by=current_user.id,
            change_summary='Initial version'
        )
        db.session.add(version)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('content.posts'))
    
    return render_template('content/create_post.html', form=form)

@content_bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Edit a post with version tracking"""
    post = Post.query.get_or_404(post_id)
    
    # Check permissions
    if post.user_id != current_user.id and not current_user.is_admin:
        # Check if user is a collaborator
        collaborator = PostCollaborator.query.filter_by(
            post_id=post_id, user_id=current_user.id, is_active=True
        ).first()
        if not collaborator or collaborator.permission_level not in ['edit', 'admin']:
            flash('You do not have permission to edit this post.', 'error')
            return redirect(url_for('content.posts'))
    
    form = PostForm(obj=post)
    
    if form.validate_on_submit():
        # Create version before editing
        if not post.is_draft:  # Only create version for non-drafts
            old_version = PostVersion(
                post_id=post.id,
                version_number=post.version_number,
                title=post.title,
                content=post.content,
                edited_by=current_user.id,
                change_summary='Auto-saved version before edit'
            )
            db.session.add(old_version)
        
        # Update post
        post.title = form.title.data
        post.content = form.content.data
        post.category_id = form.category_id.data if form.category_id.data else None
        post.is_draft = form.is_draft.data
        post.is_scheduled = form.is_scheduled.data
        post.scheduled_publish_at = form.scheduled_publish_at.data if form.is_scheduled.data else None
        post.expires_at = form.expires_at.data
        post.engagement_score = form.engagement_score.data or 0.0
        post.version_number += 1
        
        db.session.commit()
        
        flash('Post updated successfully!', 'success')
        return redirect(url_for('content.posts'))
    
    return render_template('content/edit_post.html', form=form, post=post)

@content_bp.route('/auto_save', methods=['POST'])
@login_required
def auto_save():
    """Auto-save post content"""
    data = request.get_json()
    
    post_id = data.get('post_id')
    title = data.get('title')
    content = data.get('content')
    
    if post_id:
        post = Post.query.get_or_404(post_id)
        if post.user_id != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403
    else:
        # Create new draft
        post = Post(
            title=title or 'Untitled Draft',
            content=content or '',
            user_id=current_user.id,
            is_draft=True
        )
        db.session.add(post)
        db.session.flush()  # Get the ID
    
    # Update auto-save data
    post.auto_save_data = json.dumps({
        'title': title,
        'content': content,
        'saved_at': datetime.utcnow().isoformat()
    })
    post.last_saved_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'post_id': post.id,
        'saved_at': post.last_saved_at.isoformat()
    })

@content_bp.route('/versions/<int:post_id>')
@login_required
def versions(post_id):
    """View post version history"""
    post = Post.query.get_or_404(post_id)
    
    # Check permissions
    if post.user_id != current_user.id and not current_user.is_admin:
        collaborator = PostCollaborator.query.filter_by(
            post_id=post_id, user_id=current_user.id, is_active=True
        ).first()
        if not collaborator:
            flash('You do not have permission to view this post\'s versions.', 'error')
            return redirect(url_for('content.posts'))
    
    versions = PostVersion.query.filter_by(post_id=post_id).order_by(PostVersion.version_number.desc()).all()
    return render_template('content/versions.html', post=post, versions=versions)

@content_bp.route('/compare/<int:post_id>', methods=['GET', 'POST'])
@login_required
def compare_versions(post_id):
    """Compare two versions of a post"""
    post = Post.query.get_or_404(post_id)
    
    # Check permissions
    if post.user_id != current_user.id and not current_user.is_admin:
        collaborator = PostCollaborator.query.filter_by(
            post_id=post_id, user_id=current_user.id, is_active=True
        ).first()
        if not collaborator:
            flash('You do not have permission to compare this post\'s versions.', 'error')
            return redirect(url_for('content.posts'))
    
    form = VersionCompareForm()
    versions = PostVersion.query.filter_by(post_id=post_id).order_by(PostVersion.version_number.desc()).all()
    
    if form.validate_on_submit():
        version_from = PostVersion.query.filter_by(
            post_id=post_id, version_number=form.version_from.data
        ).first()
        version_to = PostVersion.query.filter_by(
            post_id=post_id, version_number=form.version_to.data
        ).first()
        
        if version_from and version_to:
            return render_template('content/compare_versions.html',
                                 post=post, version_from=version_from, version_to=version_to)
    
    return render_template('content/compare_versions.html', form=form, post=post, versions=versions)

@content_bp.route('/restore/<int:post_id>/<int:version_number>')
@login_required
def restore_version(post_id, version_number):
    """Restore a post to a specific version"""
    post = Post.query.get_or_404(post_id)
    version = PostVersion.query.filter_by(post_id=post_id, version_number=version_number).first_or_404()
    
    # Check permissions
    if post.user_id != current_user.id and not current_user.is_admin:
        collaborator = PostCollaborator.query.filter_by(
            post_id=post_id, user_id=current_user.id, is_active=True
        ).first()
        if not collaborator or collaborator.permission_level != 'admin':
            flash('You do not have permission to restore this post.', 'error')
            return redirect(url_for('content.posts'))
    
    # Create version before restoring
    old_version = PostVersion(
        post_id=post.id,
        version_number=post.version_number,
        title=post.title,
        content=post.content,
        edited_by=current_user.id,
        change_summary=f'Restored to version {version_number}'
    )
    db.session.add(old_version)
    
    # Restore content
    post.title = version.title
    post.content = version.content
    post.version_number += 1
    
    db.session.commit()
    
    flash(f'Post restored to version {version_number}', 'success')
    return redirect(url_for('content.versions', post_id=post_id))

@content_bp.route('/collaborate/<int:post_id>', methods=['GET', 'POST'])
@login_required
def collaborate(post_id):
    """Manage post collaborators"""
    post = Post.query.get_or_404(post_id)
    
    # Only post owner can manage collaborators
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('Only the post owner can manage collaborators.', 'error')
        return redirect(url_for('content.posts'))
    
    form = CollaborationForm()
    
    if form.validate_on_submit():
        # Check if user exists
        user = User.query.get(form.user_id.data)
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('content.collaborate', post_id=post_id))
        
        # Check if already a collaborator
        existing = PostCollaborator.query.filter_by(post_id=post_id, user_id=user.id).first()
        if existing:
            existing.permission_level = form.permission_level.data
            existing.is_active = form.is_active.data
            flash('Collaborator updated successfully!', 'success')
        else:
            collaborator = PostCollaborator(
                post_id=post_id,
                user_id=user.id,
                permission_level=form.permission_level.data,
                added_by=current_user.id,
                is_active=form.is_active.data
            )
            db.session.add(collaborator)
            flash('Collaborator added successfully!', 'success')
        
        db.session.commit()
        return redirect(url_for('content.collaborate', post_id=post_id))
    
    collaborators = PostCollaborator.query.filter_by(post_id=post_id).all()
    return render_template('content/collaborate.html', form=form, post=post, collaborators=collaborators)

@content_bp.route('/schedule/<int:post_id>', methods=['GET', 'POST'])
@login_required
def schedule_post(post_id):
    """Schedule post publishing"""
    post = Post.query.get_or_404(post_id)
    
    # Check permissions
    if post.user_id != current_user.id and not current_user.is_admin:
        collaborator = PostCollaborator.query.filter_by(
            post_id=post_id, user_id=current_user.id, is_active=True
        ).first()
        if not collaborator or collaborator.permission_level not in ['edit', 'admin']:
            flash('You do not have permission to schedule this post.', 'error')
            return redirect(url_for('content.posts'))
    
    form = ScheduleForm(obj=post)
    
    if form.validate_on_submit():
        post.is_scheduled = form.is_scheduled.data
        post.scheduled_publish_at = form.scheduled_publish_at.data
        
        db.session.commit()
        
        if form.is_scheduled.data:
            flash(f'Post scheduled for {form.scheduled_publish_at.data}', 'success')
        else:
            flash('Scheduling cancelled', 'info')
        
        return redirect(url_for('content.posts'))
    
    return render_template('content/schedule_post.html', form=form, post=post)

@content_bp.route('/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    """Perform bulk actions on posts"""
    form = BulkActionForm(request.form)
    post_ids = request.form.getlist('post_ids')
    
    if not post_ids:
        flash('No posts selected.', 'error')
        return redirect(url_for('content.posts'))
    
    if form.validate_on_submit():
        action = form.action.data
        posts = Post.query.filter(Post.id.in_(post_ids), Post.user_id == current_user.id).all()
        
        for post in posts:
            if action == 'publish':
                post.is_draft = False
                post.is_scheduled = False
            elif action == 'draft':
                post.is_draft = True
                post.is_scheduled = False
            elif action == 'archive':
                post.is_archived = True
                post.archived_at = datetime.utcnow()
            elif action == 'delete':
                db.session.delete(post)
            elif action == 'schedule':
                post.is_scheduled = True
                post.scheduled_publish_at = form.scheduled_date.data
        
        db.session.commit()
        flash(f'Bulk action "{action}" completed successfully!', 'success')
    
    return redirect(url_for('content.posts'))

@content_bp.route('/analytics/<int:post_id>')
@login_required
def analytics(post_id):
    """View post analytics"""
    post = Post.query.get_or_404(post_id)
    
    # Check permissions
    if post.user_id != current_user.id and not current_user.is_admin:
        collaborator = PostCollaborator.query.filter_by(
            post_id=post_id, user_id=current_user.id, is_active=True
        ).first()
        if not collaborator:
            flash('You do not have permission to view this post\'s analytics.', 'error')
            return redirect(url_for('content.posts'))
    
    # Get analytics data
    view_count = post.view_count or 0
    engagement_score = post.engagement_score or 0.0
    comment_count = post.comments.count()
    upvote_count = post.upvotes or 0
    downvote_count = post.downvotes or 0
    
    return render_template('content/analytics.html',
                         post=post,
                         view_count=view_count,
                         engagement_score=engagement_score,
                         comment_count=comment_count,
                         upvote_count=upvote_count,
                         downvote_count=downvote_count)

@content_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_content():
    """Import content from external sources"""
    form = ContentImportForm()
    
    if form.validate_on_submit():
        # Create post from imported content
        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id,
            category_id=form.category_id.data if form.category_id.data else None,
            is_draft=True  # Import as draft by default
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('Content imported successfully!', 'success')
        return redirect(url_for('content.edit_post', post_id=post.id))
    
    return render_template('content/import.html', form=form)

@content_bp.route('/export/<int:post_id>', methods=['GET', 'POST'])
@login_required
def export_content(post_id):
    """Export post content"""
    post = Post.query.get_or_404(post_id)
    
    # Check permissions
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to export this post.', 'error')
        return redirect(url_for('content.posts'))
    
    form = ContentExportForm()
    
    if form.validate_on_submit():
        # Export logic would go here
        flash('Export functionality coming soon!', 'info')
        return redirect(url_for('content.analytics', post_id=post_id))
    
    return render_template('content/export.html', form=form, post=post)

# Error handlers
@content_bp.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@content_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal error in content routes: {str(error)}")
    return render_template('errors/500.html'), 500
