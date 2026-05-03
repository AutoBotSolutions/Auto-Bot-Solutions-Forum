from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Post, Comment, Repository, Category, Badge
from app.admin.forms import CategoryForm, BadgeForm, UserEditForm, UserSuspendForm, UserBanForm, UserBulkActionForm
from app.utils.error_handler import error_reporter, debug_route, validate_admin_access, check_template_rendering, get_system_health_check
import requests
import os

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not current_user.is_authenticated:
                error_reporter.log_warning("Unauthenticated admin access attempt", {
                    'function': f.__name__,
                    'url': request.url if request else None
                })
                flash('Access denied. Admin privileges required.', 'error')
                return redirect(url_for('main.index'))
            
            if not current_user.is_admin:
                error_reporter.log_warning("Non-admin access attempt", {
                    'function': f.__name__,
                    'user_id': current_user.id,
                    'url': request.url if request else None
                })
                flash('Access denied. Admin privileges required.', 'error')
                return redirect(url_for('main.index'))
            
            error_reporter.log_info(f"Admin access granted: {f.__name__}", {
                'user_id': current_user.id,
                'url': request.url if request else None
            })
            
            return f(*args, **kwargs)
            
        except Exception as e:
            error_reporter.log_error(f"Admin decorator error: {e}", {
                'function': f.__name__,
                'user_id': current_user.id if current_user.is_authenticated else None
            })
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('main.index'))
    
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_posts = Post.query.count()
    total_comments = Comment.query.count()
    total_repos = Repository.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          total_users=total_users,
                          total_posts=total_posts,
                          total_comments=total_comments,
                          total_repos=total_repos,
                          recent_users=recent_users,
                          recent_posts=recent_posts)

@admin_bp.route('/users')
@login_required
@admin_required
@debug_route
def users():
    try:
        error_reporter.log_info("Admin users page accessed", {
            'user_id': current_user.id,
            'url': request.url
        })
        
        # Get users with error handling
        try:
            users = User.query.order_by(User.created_at.desc()).all()
            error_reporter.log_info(f"Retrieved {len(users)} users from database")
        except Exception as e:
            error_reporter.log_error("Failed to retrieve users", {'error': str(e)})
            flash('Error loading user data. Please try again.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Skip template rendering check here since we're in the proper request context
        # The template will be rendered by render_template() below with proper context
        error_reporter.log_info("Proceeding with template rendering", {
            'template': 'admin/users.html',
            'user_count': len(users)
        })
        
        error_reporter.log_info("Admin users page rendered successfully", {
            'user_count': len(users),
            'template': 'admin/users.html'
        })
        
        return render_template('admin/users.html', users=users)
        
    except Exception as e:
        error_reporter.log_error("Admin users page error", {
            'error': str(e),
            'user_id': current_user.id
        })
        flash('An error occurred while loading the users page.', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/error-report')
@login_required
@admin_required
def error_report():
    """Return comprehensive error report for debugging"""
    try:
        report = error_reporter.get_error_report()
        health = get_system_health_check()
        
        return jsonify({
            'error_report': report,
            'health_check': health,
            'timestamp': health['timestamp']
        })
    except Exception as e:
        error_reporter.log_error("Error report generation failed", {'error': str(e)})
        return jsonify({'error': 'Failed to generate error report'}), 500

@admin_bp.route('/users/<int:user_id>/toggle-admin')
@login_required
@admin_required
def toggle_admin(user_id):
    try:
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('You cannot modify your own admin status.', 'error')
            return redirect(url_for('admin.users'))
        
        old_status = "Admin" if user.is_admin else "User"
        user.is_admin = not user.is_admin
        new_status = "Admin" if user.is_admin else "User"
        
        db.session.commit()
        flash(f'Admin status updated for {user.username}: {old_status} → {new_status}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating admin status: {str(e)}', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/delete')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} has been deleted.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    
    if form.validate_on_submit():
        try:
            # Check if username is being changed and if it's already taken
            if form.username.data != user.username:
                existing_user = User.query.filter_by(username=form.username.data).first()
                if existing_user and existing_user.id != user.id:
                    flash('Username already exists.', 'error')
                    return render_template('admin/edit_user.html', form=form, user=user)
            
            # Check if email is being changed and if it's already taken
            if form.email.data != user.email:
                existing_user = User.query.filter_by(email=form.email.data).first()
                if existing_user and existing_user.id != user.id:
                    flash('Email already exists.', 'error')
                    return render_template('admin/edit_user.html', form=form, user=user)
            
            # Update user information
            user.username = form.username.data
            user.email = form.email.data
            user.is_admin = form.is_admin.data
            
            # Update password if change_password is checked
            if form.change_password.data and form.password.data:
                from werkzeug.security import generate_password_hash
                user.password_hash = generate_password_hash(form.password.data)
                flash(f'Password updated for {user.username}.', 'success')
            
            db.session.commit()
            flash(f'User {user.username} has been updated.', 'success')
            return redirect(url_for('admin.users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    return render_template('admin/edit_user.html', form=form, user=user)

@admin_bp.route('/users/<int:user_id>/suspend', methods=['GET', 'POST'])
@login_required
@admin_required
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot suspend your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    form = UserSuspendForm()
    if form.validate_on_submit():
        duration_days = None
        if form.duration_days.data and form.duration_days.data.strip():
            try:
                duration_days = int(form.duration_days.data)
            except ValueError:
                flash('Invalid duration. Please enter a valid number of days.', 'error')
                return render_template('admin/suspend_user.html', form=form, user=user)
        
        user.suspend(form.reason.data, duration_days, current_user.id)
        db.session.commit()
        
        if duration_days:
            flash(f'User {user.username} suspended for {duration_days} days.', 'success')
        else:
            flash(f'User {user.username} suspended indefinitely.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/suspend_user.html', form=form, user=user)

@admin_bp.route('/users/<int:user_id>/unsuspend')
@login_required
@admin_required
def unsuspend_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unsuspend()
    db.session.commit()
    flash(f'User {user.username} has been unsuspended.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/ban', methods=['GET', 'POST'])
@login_required
@admin_required
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot ban your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    form = UserBanForm()
    if form.validate_on_submit():
        user.ban(form.reason.data, current_user.id)
        db.session.commit()
        flash(f'User {user.username} has been permanently banned.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/ban_user.html', form=form, user=user)

@admin_bp.route('/users/<int:user_id>/unban')
@login_required
@admin_required
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unban()
    db.session.commit()
    flash(f'User {user.username} has been unbanned.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/view')
@login_required
@admin_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    stats = user.get_user_stats()
    recent_posts = user.posts.order_by(Post.created_at.desc()).limit(5).all()
    recent_comments = user.comments.order_by(Comment.created_at.desc()).limit(5).all()
    
    return render_template('admin/view_user.html', 
                         user=user, 
                         stats=stats,
                         recent_posts=recent_posts,
                         recent_comments=recent_comments)

@admin_bp.route('/users/<int:user_id>/reset-password')
@login_required
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    # Generate a random password
    import secrets
    import string
    new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    user.set_password(new_password)
    db.session.commit()
    
    flash(f'Password for {user.username} has been reset to: {new_password}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/bulk-action', methods=['POST'])
@login_required
@admin_required
def bulk_user_action():
    form = UserBulkActionForm()
    if form.validate_on_submit():
        try:
            user_ids = [int(uid.strip()) for uid in form.user_ids.data.split(',')]
            action = form.action.data
            reason = form.reason.data or 'Bulk action performed by admin'
            
            affected_users = []
            for uid in user_ids:
                user = User.query.get(uid)
                if user and user.id != current_user.id:
                    if action == 'suspend':
                        user.suspend(reason, None, current_user.id)
                    elif action == 'ban':
                        user.ban(reason, current_user.id)
                    elif action == 'unsuspend':
                        user.unsuspend()
                    elif action == 'unban':
                        user.unban()
                    elif action == 'delete':
                        username = user.username
                        db.session.delete(user)
                        affected_users.append(username)
                        continue
                    affected_users.append(user.username)
            
            db.session.commit()
            flash(f'Bulk {action} completed for {len(affected_users)} users: {", ".join(affected_users)}', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error performing bulk action: {str(e)}', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/posts')
@login_required
@admin_required
def posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/posts.html', posts=posts)

@admin_bp.route('/posts/<int:post_id>/delete')
@login_required
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash(f'Post "{post.title}" has been deleted.', 'success')
    return redirect(url_for('admin.posts'))

@admin_bp.route('/comments')
@login_required
@admin_required
def comments():
    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template('admin/comments.html', comments=comments)

@admin_bp.route('/comments/<int:comment_id>/delete')
@login_required
@admin_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment has been deleted.', 'success')
    return redirect(url_for('admin.comments'))

@admin_bp.route('/repositories')
@login_required
@admin_required
def repositories():
    repos = Repository.query.order_by(Repository.name).all()
    return render_template('admin/repositories.html', repos=repos)

@admin_bp.route('/repositories/<int:repo_id>/delete')
@login_required
@admin_required
def delete_repository(repo_id):
    repo = Repository.query.get_or_404(repo_id)
    db.session.delete(repo)
    db.session.commit()
    flash(f'Repository "{repo.name}" has been deleted.', 'success')
    return redirect(url_for('admin.repositories'))

@admin_bp.route('/api/sync-repositories', methods=['POST'])
@login_required
@admin_required
def sync_repositories():
    try:
        # GitHub API endpoint for organization repositories
        github_token = os.getenv('GITHUB_TOKEN', '')
        org_name = 'AutoBotSolutions'
        
        # Try without authentication first
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AutoBot-Solutions-Forum'
        }
        
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        # Fetch repositories from GitHub
        url = f'https://api.github.com/orgs/{org_name}/repos'
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            # If organization doesn't exist or is not found, try to get the main repo
            repo_url = f'https://api.github.com/repos/{org_name}/Auto-Bot-Solutions-Forum'
            repo_response = requests.get(repo_url, headers=headers)
            
            if repo_response.status_code == 200:
                # Use the single repository as fallback
                repos_data = [repo_response.json()]
            else:
                return jsonify({
                    'success': False, 
                    'error': f'GitHub organization or repository not found. Status: {repo_response.status_code}'
                })
        elif response.status_code != 200:
            return jsonify({'success': False, 'error': f'GitHub API error: {response.status_code} - {response.text}'})
        else:
            repos_data = response.json()
        
        synced_count = 0
        
        for repo_data in repos_data:
            # Check if repository already exists
            existing_repo = Repository.query.filter_by(github_id=repo_data['id']).first()
            
            if existing_repo:
                # Update existing repository
                existing_repo.name = repo_data['name']
                existing_repo.description = repo_data.get('description', '')
                existing_repo.github_url = repo_data['html_url']
                existing_repo.language = repo_data.get('language', '')
                existing_repo.stars = repo_data.get('stargazers_count', 0)
                existing_repo.forks = repo_data.get('forks_count', 0)
                existing_repo.updated_at = repo_data.get('updated_at')
            else:
                # Create new repository
                new_repo = Repository(
                    github_id=repo_data['id'],
                    name=repo_data['name'],
                    description=repo_data.get('description', ''),
                    github_url=repo_data['html_url'],
                    language=repo_data.get('language', ''),
                    stars=repo_data.get('stargazers_count', 0),
                    forks=repo_data.get('forks_count', 0),
                    created_at=repo_data.get('created_at'),
                    updated_at=repo_data.get('updated_at')
                )
                db.session.add(new_repo)
            
            synced_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'synced': synced_count,
            'message': f'Successfully synced {synced_count} repositories'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            color=form.color.data
        )
        db.session.add(category)
        db.session.commit()
        flash(f'Category "{category.name}" has been created.', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/create_category.html', form=form)

@admin_bp.route('/categories/<int:category_id>/delete')
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash(f'Category "{category.name}" has been deleted.', 'success')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/badges')
@login_required
@admin_required
def badges():
    badges = Badge.query.order_by(Badge.name).all()
    return render_template('admin/badges.html', badges=badges)

@admin_bp.route('/badges/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_badge():
    form = BadgeForm()
    if form.validate_on_submit():
        badge = Badge(
            name=form.name.data,
            description=form.description.data,
            icon=form.icon.data,
            color=form.color.data
        )
        db.session.add(badge)
        db.session.commit()
        flash(f'Badge "{badge.name}" has been created.', 'success')
        return redirect(url_for('admin.badges'))
    return render_template('admin/create_badge.html', form=form)

@admin_bp.route('/badges/<int:badge_id>/delete')
@login_required
@admin_required
def delete_badge(badge_id):
    badge = Badge.query.get_or_404(badge_id)
    db.session.delete(badge)
    db.session.commit()
    flash(f'Badge "{badge.name}" has been deleted.', 'success')
    return redirect(url_for('admin.badges'))

@admin_bp.route('/users/<int:user_id>/add_badge/<int:badge_id>')
@login_required
@admin_required
def add_badge_to_user(user_id, badge_id):
    user = User.query.get_or_404(user_id)
    badge = Badge.query.get_or_404(badge_id)
    if badge not in user.badges:
        user.badges.append(badge)
        db.session.commit()
        flash(f'Badge "{badge.name}" added to {user.username}.', 'success')
    else:
        flash(f'{user.username} already has this badge.', 'info')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/remove_badge/<int:badge_id>')
@login_required
@admin_required
def remove_badge_from_user(user_id, badge_id):
    user = User.query.get_or_404(user_id)
    badge = Badge.query.get_or_404(badge_id)
    if badge in user.badges:
        user.badges.remove(badge)
        db.session.commit()
        flash(f'Badge "{badge.name}" removed from {user.username}.', 'success')
    return redirect(url_for('admin.users'))
