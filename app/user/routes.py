from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User, Post, Comment

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).limit(10).all()
    comments = Comment.query.filter_by(user_id=user.id).order_by(Comment.created_at.desc()).limit(10).all()
    total_posts = Post.query.filter_by(user_id=user.id).count()
    total_comments = Comment.query.filter_by(user_id=user.id).count()
    
    return render_template('user/profile.html', 
                          user=user, 
                          posts=posts, 
                          comments=comments,
                          total_posts=total_posts,
                          total_comments=total_comments)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    from app.user.forms import EditProfileForm
    form = EditProfileForm(current_user.username, current_user.email)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.profile', username=current_user.username))
    
    return render_template('user/edit_profile.html', form=form)
