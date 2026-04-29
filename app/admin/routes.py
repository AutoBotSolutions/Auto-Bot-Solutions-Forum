from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Post, Comment, Repository, Category, Badge
from app.admin.forms import CategoryForm, BadgeForm

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
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
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/toggle-admin')
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot modify your own admin status.', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'Admin status updated for {user.username}.', 'success')
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
