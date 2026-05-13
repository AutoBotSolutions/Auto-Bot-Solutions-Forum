from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from app import db
from app.models import User, Post, Comment, Repository, Category, Badge
from app.admin.forms import (
    CategoryForm, BadgeForm, UserEditForm, UserSuspendForm, UserBanForm, UserBulkActionForm,
    PermissionForm, RoleForm, RolePermissionForm, UserRoleForm, UserRoleBulkForm,
    UserGroupForm, UserGroupMemberForm, UserGroupBulkForm, GroupRoleForm,
    SecurityEventForm, SecurityEventFilterForm, UserPermissionCheckForm,
    AccessLogFilterForm, BulkUserManagementForm
)
from app.admin.models import (
    Permission, AdminRole, RolePermission, UserGroup, UserGroupMember,
    UserRole, GroupRole, AccessLog
)
from app.security.models import SecurityEvent
from app.admin.service import (
    PermissionService, RoleService, UserGroupService, UserRoleService,
    AccessControlService, SecurityEventService, UserManagementService
)
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


# Role and Permission Management Routes

@admin_bp.route('/permissions')
@login_required
@admin_required
def permissions():
    """Manage system permissions"""
    permissions = Permission.query.order_by(Permission.category, Permission.resource, Permission.action).all()
    return render_template('admin/permissions.html', permissions=permissions)

@admin_bp.route('/permissions/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_permission():
    """Create a new permission"""
    form = PermissionForm()
    if form.validate_on_submit():
        try:
            permission = PermissionService.create_permission(
                name=form.name.data,
                display_name=form.display_name.data,
                description=form.description.data,
                category=form.category.data,
                resource=form.resource.data,
                action=form.action.data,
                is_system=False
            )
            flash(f'Permission "{permission.display_name}" created successfully.', 'success')
            return redirect(url_for('admin.permissions'))
        except Exception as e:
            flash(f'Error creating permission: {str(e)}', 'error')
    
    return render_template('admin/create_permission.html', form=form)

@admin_bp.route('/permissions/<int:permission_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_permission(permission_id):
    """Edit permission"""
    permission = Permission.query.get_or_404(permission_id)
    form = PermissionForm(obj=permission)
    
    if form.validate_on_submit():
        try:
            updated_permission = PermissionService.update_permission(
                permission_id,
                name=form.name.data,
                display_name=form.display_name.data,
                description=form.description.data,
                category=form.category.data,
                resource=form.resource.data,
                action=form.action.data,
                is_active=form.is_active.data
            )
            if updated_permission:
                flash(f'Permission "{updated_permission.display_name}" updated successfully.', 'success')
                return redirect(url_for('admin.permissions'))
            else:
                flash('Permission not found.', 'error')
        except Exception as e:
            flash(f'Error updating permission: {str(e)}', 'error')
    
    return render_template('admin/edit_permission.html', form=form, permission=permission)

@admin_bp.route('/permissions/<int:permission_id>/delete')
@login_required
@admin_required
def delete_permission(permission_id):
    """Delete permission"""
    permission = Permission.query.get_or_404(permission_id)
    if permission.is_system:
        flash('Cannot delete system permission.', 'error')
        return redirect(url_for('admin.permissions'))
    
    try:
        if PermissionService.delete_permission(permission_id):
            flash(f'Permission "{permission.display_name}" deleted successfully.', 'success')
        else:
            flash('Permission not found.', 'error')
    except Exception as e:
        flash(f'Error deleting permission: {str(e)}', 'error')
    
    return redirect(url_for('admin.permissions'))

@admin_bp.route('/roles')
@login_required
@admin_required
def roles():
    """Manage system roles"""
    roles = RoleService.get_roles()
    return render_template('admin/roles.html', roles=roles)

@admin_bp.route('/roles/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_role():
    """Create a new role"""
    form = RoleForm()
    if form.validate_on_submit():
        try:
            role = RoleService.create_role(
                name=form.name.data,
                display_name=form.display_name.data,
                description=form.description.data,
                level=form.level.data,
                is_system=False,
                created_by=current_user.id
            )
            flash(f'Role "{role.display_name}" created successfully.', 'success')
            return redirect(url_for('admin.roles'))
        except Exception as e:
            flash(f'Error creating role: {str(e)}', 'error')
    
    return render_template('admin/create_role.html', form=form)

@admin_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_role(role_id):
    """Edit role"""
    role = RoleService.get_role_by_id(role_id)
    if not role:
        flash('Role not found.', 'error')
        return redirect(url_for('admin.roles'))
    
    form = RoleForm(obj=role)
    if form.validate_on_submit():
        try:
            updated_role = RoleService.update_role(
                role_id,
                name=form.name.data,
                display_name=form.display_name.data,
                description=form.description.data,
                level=form.level.data,
                is_active=form.is_active.data
            )
            if updated_role:
                flash(f'Role "{updated_role.display_name}" updated successfully.', 'success')
                return redirect(url_for('admin.roles'))
            else:
                flash('Role not found.', 'error')
        except Exception as e:
            flash(f'Error updating role: {str(e)}', 'error')
    
    return render_template('admin/edit_role.html', form=form, role=role)

@admin_bp.route('/roles/<int:role_id>/delete')
@login_required
@admin_required
def delete_role(role_id):
    """Delete role"""
    role = RoleService.get_role_by_id(role_id)
    if not role or role.is_system:
        flash('Cannot delete system role.', 'error')
        return redirect(url_for('admin.roles'))
    
    try:
        if RoleService.delete_role(role_id):
            flash(f'Role "{role.display_name}" deleted successfully.', 'success')
        else:
            flash('Role not found.', 'error')
    except Exception as e:
        flash(f'Error deleting role: {str(e)}', 'error')
    
    return redirect(url_for('admin.roles'))

@admin_bp.route('/roles/<int:role_id>/permissions', methods=['GET', 'POST'])
@login_required
@admin_required
def role_permissions(role_id):
    """Manage role permissions"""
    role = RoleService.get_role_by_id(role_id)
    if not role:
        flash('Role not found.', 'error')
        return redirect(url_for('admin.roles'))
    
    form = RolePermissionForm()
    form.role_id.choices = [(r.id, r.display_name) for r in RoleService.get_roles()]
    form.permission_ids.choices = [(p.id, f"{p.category} - {p.display_name}") for p in PermissionService.get_permissions()]
    
    if form.validate_on_submit():
        try:
            # Get current permissions
            current_permissions = set(rp.permission_id for rp in role.permissions)
            new_permissions = set(form.permission_ids.data)
            
            # Add new permissions
            for permission_id in new_permissions - current_permissions:
                RoleService.grant_permission_to_role(role_id, permission_id, current_user.id)
            
            # Remove old permissions
            for permission_id in current_permissions - new_permissions:
                RoleService.revoke_permission_from_role(role_id, permission_id)
            
            flash(f'Permissions for role "{role.display_name}" updated successfully.', 'success')
            return redirect(url_for('admin.roles'))
        except Exception as e:
            flash(f'Error updating permissions: {str(e)}', 'error')
    
    # Set current values
    form.role_id.data = role_id
    form.permission_ids.data = [rp.permission_id for rp in role.permissions]
    
    return render_template('admin/role_permissions.html', form=form, role=role)

@admin_bp.route('/user-roles')
@login_required
@admin_required
def user_roles():
    """Manage user role assignments"""
    user_roles = UserRole.query.join(User).join(AdminRole).order_by(User.username, AdminRole.level).all()
    return render_template('admin/user_roles.html', user_roles=user_roles)

@admin_bp.route('/user-roles/assign', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_user_role():
    """Assign role to user"""
    form = UserRoleForm()
    form.user_id.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
    form.role_id.choices = [(r.id, r.display_name) for r in RoleService.get_roles()]
    
    if form.validate_on_submit():
        try:
            user_role = UserRoleService.assign_role_to_user(
                form.user_id.data,
                form.role_id.data,
                assigned_by=current_user.id,
                expires_at=form.expires_at.data,
                reason=form.reason.data
            )
            flash(f'Role assigned successfully.', 'success')
            return redirect(url_for('admin.user_roles'))
        except Exception as e:
            flash(f'Error assigning role: {str(e)}', 'error')
    
    return render_template('admin/assign_user_role.html', form=form)

@admin_bp.route('/user-roles/<int:user_role_id>/revoke')
@login_required
@admin_required
def revoke_user_role(user_role_id):
    """Revoke user role"""
    user_role = UserRole.query.get_or_404(user_role_id)
    
    try:
        if UserRoleService.revoke_role_from_user(user_role.user_id, user_role.role_id, current_user.id):
            flash('Role revoked successfully.', 'success')
        else:
            flash('Role not found.', 'error')
    except Exception as e:
        flash(f'Error revoking role: {str(e)}', 'error')
    
    return redirect(url_for('admin.user_roles'))

@admin_bp.route('/user-groups')
@login_required
@admin_required
def user_groups():
    """Manage user groups"""
    groups = UserGroupService.get_groups()
    return render_template('admin/user_groups.html', groups=groups)

@admin_bp.route('/user-groups/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user_group():
    """Create a new user group"""
    form = UserGroupForm()
    if form.validate_on_submit():
        try:
            group = UserGroupService.create_group(
                name=form.name.data,
                display_name=form.display_name.data,
                description=form.description.data,
                max_members=form.max_members.data,
                auto_assign=form.auto_assign.data,
                created_by=current_user.id
            )
            flash(f'Group "{group.display_name}" created successfully.', 'success')
            return redirect(url_for('admin.user_groups'))
        except Exception as e:
            flash(f'Error creating group: {str(e)}', 'error')
    
    return render_template('admin/create_user_group.html', form=form)

@admin_bp.route('/user-groups/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user_group(group_id):
    """Edit user group"""
    group = UserGroupService.get_group_by_id(group_id)
    if not group:
        flash('Group not found.', 'error')
        return redirect(url_for('admin.user_groups'))
    
    form = UserGroupForm(obj=group)
    if form.validate_on_submit():
        try:
            updated_group = UserGroupService.update_group(
                group_id,
                name=form.name.data,
                display_name=form.display_name.data,
                description=form.description.data,
                max_members=form.max_members.data,
                auto_assign=form.auto_assign.data
            )
            if updated_group:
                flash(f'Group "{updated_group.display_name}" updated successfully.', 'success')
                return redirect(url_for('admin.user_groups'))
            else:
                flash('Group not found.', 'error')
        except Exception as e:
            flash(f'Error updating group: {str(e)}', 'error')
    
    return render_template('admin/edit_user_group.html', form=form, group=group)

@admin_bp.route('/user-groups/<int:group_id>/delete')
@login_required
@admin_required
def delete_user_group(group_id):
    """Delete user group"""
    group = UserGroupService.get_group_by_id(group_id)
    if not group or group.is_system:
        flash('Cannot delete system group.', 'error')
        return redirect(url_for('admin.user_groups'))
    
    try:
        if UserGroupService.delete_group(group_id):
            flash(f'Group "{group.display_name}" deleted successfully.', 'success')
        else:
            flash('Group not found.', 'error')
    except Exception as e:
        flash(f'Error deleting group: {str(e)}', 'error')
    
    return redirect(url_for('admin.user_groups'))

@admin_bp.route('/user-groups/<int:group_id>/members')
@login_required
@admin_required
def group_members(group_id):
    """Manage group members"""
    group = UserGroupService.get_group_by_id(group_id)
    if not group:
        flash('Group not found.', 'error')
        return redirect(url_for('admin.user_groups'))
    
    members = UserGroupService.get_group_members(group_id)
    return render_template('admin/group_members.html', group=group, members=members)

@admin_bp.route('/user-groups/<int:group_id>/add-member', methods=['GET', 'POST'])
@login_required
@admin_required
def add_group_member(group_id):
    """Add member to group"""
    group = UserGroupService.get_group_by_id(group_id)
    if not group:
        flash('Group not found.', 'error')
        return redirect(url_for('admin.user_groups'))
    
    form = UserGroupMemberForm()
    form.user_id.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
    form.group_id.data = group_id
    
    if form.validate_on_submit():
        try:
            member = UserGroupService.add_user_to_group(group_id, form.user_id.data, current_user.id)
            flash(f'User added to group successfully.', 'success')
            return redirect(url_for('admin.group_members', group_id=group_id))
        except Exception as e:
            flash(f'Error adding member: {str(e)}', 'error')
    
    return render_template('admin/add_group_member.html', form=form, group=group)

@admin_bp.route('/user-groups/<int:group_id>/remove-member/<int:user_id>')
@login_required
@admin_required
def remove_group_member(group_id, user_id):
    """Remove member from group"""
    try:
        member = UserGroupService.remove_user_from_group(group_id, user_id, current_user.id)
        flash(f'User removed from group successfully.', 'success')
    except Exception as e:
        flash(f'Error removing member: {str(e)}', 'error')
    
    return redirect(url_for('admin.group_members', group_id=group_id))

@admin_bp.route('/security-events')
@login_required
@admin_required
def security_events():
    """View security events"""
    form = SecurityEventFilterForm()
    form.user_id.choices = [(0, 'All Users')] + [(u.id, u.username) for u in User.query.order_by(User.username).all()]
    
    events = SecurityEventService.get_security_events(
        event_type=form.event_type.data,
        severity=form.severity.data,
        resolved=True if form.resolved.data == 'true' else False if form.resolved.data == 'false' else None,
        user_id=form.user_id.data if form.user_id.data else None,
        start_date=form.start_date.data,
        end_date=form.end_date.data,
        limit=100
    )
    
    return render_template('admin/security_events.html', events=events, form=form)

@admin_bp.route('/security-events/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_security_event():
    """Create security event"""
    form = SecurityEventForm()
    form.user_id.choices = [(0, 'No User')] + [(u.id, u.username) for u in User.query.order_by(User.username).all()]
    
    if form.validate_on_submit():
        try:
            event = SecurityEventService.create_security_event(
                event_type=form.event_type.data,
                severity=form.severity.data,
                title=form.title.data,
                description=form.description.data,
                user_id=form.user_id.data if form.user_id.data else None,
                ip_address=form.ip_address.data,
                resource=form.resource.data,
                action=form.action.data
            )
            flash(f'Security event created successfully.', 'success')
            return redirect(url_for('admin.security_events'))
        except Exception as e:
            flash(f'Error creating security event: {str(e)}', 'error')
    
    return render_template('admin/create_security_event.html', form=form)

@admin_bp.route('/security-events/<int:event_id>/resolve')
@login_required
@admin_required
def resolve_security_event(event_id):
    """Resolve security event"""
    try:
        if SecurityEventService.resolve_security_event(event_id, current_user.id):
            flash('Security event resolved successfully.', 'success')
        else:
            flash('Security event not found.', 'error')
    except Exception as e:
        flash(f'Error resolving security event: {str(e)}', 'error')
    
    return redirect(url_for('admin.security_events'))

@admin_bp.route('/access-logs')
@login_required
@admin_required
def access_logs():
    """View access logs"""
    form = AccessLogFilterForm()
    form.user_id.choices = [(0, 'All Users')] + [(u.id, u.username) for u in User.query.order_by(User.username).all()]
    
    query = AccessLog.query
    
    if form.user_id.data:
        query = query.filter_by(user_id=form.user_id.data)
    
    if form.resource.data:
        query = query.filter(AccessLog.resource.ilike(f'%{form.resource.data}%'))
    
    if form.action.data:
        query = query.filter(AccessLog.action.ilike(f'%{form.action.data}%'))
    
    if form.granted.data:
        query = query.filter_by(granted=form.granted.data == 'true')
    
    if form.start_date.data:
        query = query.filter(AccessLog.created_at >= form.start_date.data)
    
    if form.end_date.data:
        query = query.filter(AccessLog.created_at <= form.end_date.data)
    
    if form.ip_address.data:
        query = query.filter(AccessLog.ip_address.ilike(f'%{form.ip_address.data}%'))
    
    logs = query.order_by(AccessLog.created_at.desc()).limit(200).all()
    
    return render_template('admin/access_logs.html', logs=logs, form=form)

@admin_bp.route('/user-management')
@login_required
@admin_required
def user_management():
    """Advanced user management dashboard"""
    return render_template('admin/user_management.html')

@admin_bp.route('/user-management/check-permission', methods=['GET', 'POST'])
@login_required
@admin_required
def check_user_permission():
    """Check user permission"""
    form = UserPermissionCheckForm()
    form.user_id.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
    
    result = None
    if form.validate_on_submit():
        try:
            has_permission = AccessControlService.user_has_permission_on_resource(
                form.user_id.data,
                form.resource.data,
                form.action.data
            )
            result = {
                'user_id': form.user_id.data,
                'resource': form.resource.data,
                'action': form.action.data,
                'has_permission': has_permission
            }
        except Exception as e:
            flash(f'Error checking permission: {str(e)}', 'error')
    
    return render_template('admin/check_permission.html', form=form, result=result)

@admin_bp.route('/user-management/bulk-action', methods=['POST'])
@login_required
@admin_required
def bulk_user_management_action():
    """Bulk user management action"""
    form = BulkUserManagementForm()
    
    if form.validate_on_submit():
        try:
            user_ids = [int(uid) for uid in form.user_ids.data.split(',')]
            
            if form.action.data == 'assign_role':
                assigned_count = UserManagementService.bulk_assign_roles(
                    user_ids, form.role_id.data, current_user.id, form.expires_at.data, form.reason.data
                )
                flash(f'Role assigned to {assigned_count} users.', 'success')
            
            elif form.action.data == 'revoke_role':
                revoked_count = UserManagementService.bulk_revoke_roles(
                    user_ids, form.role_id.data, current_user.id, form.reason.data
                )
                flash(f'Role revoked from {revoked_count} users.', 'success')
            
            elif form.action.data == 'add_to_group':
                added_count = UserManagementService.bulk_add_to_groups(
                    user_ids, form.group_id.data, current_user.id
                )
                flash(f'Users added to group: {added_count}.', 'success')
            
            elif form.action.data == 'remove_from_group':
                removed_count = UserManagementService.bulk_remove_from_groups(
                    user_ids, form.group_id.data, current_user.id
                )
                flash(f'Users removed from group: {removed_count}.', 'success')
            
            else:
                flash('Action not implemented yet.', 'warning')
                
        except Exception as e:
            flash(f'Error performing bulk action: {str(e)}', 'error')
    
    return redirect(url_for('admin.user_management'))

# API Endpoints

@admin_bp.route('/api/permissions')
@login_required
@admin_required
def api_permissions():
    """API endpoint for permissions"""
    permissions = PermissionService.get_permissions()
    return jsonify([p.to_dict() for p in permissions])

@admin_bp.route('/api/roles')
@login_required
@admin_required
def api_roles():
    """API endpoint for roles"""
    roles = RoleService.get_roles()
    return jsonify([r.to_dict() for r in roles])

@admin_bp.route('/api/user-roles/<int:user_id>')
@login_required
@admin_required
def api_user_roles(user_id):
    """API endpoint for user roles"""
    user_roles = UserRoleService.get_user_roles(user_id)
    return jsonify([ur.to_dict() for ur in user_roles])

@admin_bp.route('/api/user-groups/<int:user_id>')
@login_required
@admin_required
def api_user_groups(user_id):
    """API endpoint for user groups"""
    user_groups = UserGroupService.get_user_groups(user_id)
    return jsonify([ug.to_dict() for ug in user_groups])

@admin_bp.route('/api/security-stats')
@login_required
@admin_required
def api_security_stats():
    """API endpoint for security statistics"""
    stats = SecurityEventService.get_security_stats(days=30)
    return jsonify(stats)

@admin_bp.route('/api/user-permissions/<int:user_id>')
@login_required
@admin_required
def api_user_permissions(user_id):
    """API endpoint for user permissions"""
    permissions = AccessControlService.get_user_permissions(user_id)
    return jsonify(permissions)
