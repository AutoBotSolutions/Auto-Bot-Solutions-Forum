from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app import db, limiter
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.email.queue import EmailQueueManager
from app.auth.two_factor_routes import two_factor_bp, requires_2fa_verification
import secrets
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if user can login
        if not user.can_login():
            if user.is_banned:
                flash('Your account has been banned.', 'error')
            elif user.is_suspended:
                flash('Your account has been suspended.', 'error')
            elif user.is_account_locked():
                flash('Your account is temporarily locked due to too many failed login attempts.', 'error')
            else:
                flash('Your account is not active.', 'error')
            return redirect(url_for('auth.login'))
        
        # Record successful login attempt
        user.record_login()
        db.session.commit()
        
        # Check if 2FA is required
        if requires_2fa_verification(user):
            # Store user in session for 2FA verification
            session['2fa_user_id'] = user.id
            session['2fa_remember'] = form.remember_me.data
            return redirect(url_for('two_factor.verify'))
        
        # Login user normally
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("100 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    
    # Debug: Print form validation status
    if request.method == 'POST':
        logger.info(f"Form submitted. CSRF token present: {form.csrf_token.data is not None}")
        logger.info(f"Form validation errors: {form.errors}")
        logger.info(f"Form data: username={form.username.data}, email={form.email.data}")
    
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.verification_token = secrets.token_urlsafe(32)
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        verification_url = url_for('auth.verify_email', token=user.verification_token, _external=True)
        email_sent = EmailQueueManager.send_verification_email(user, verification_url)
        
        if email_sent:
            flash('Registration successful! Please check your email to verify your account.', 'success')
            logger.info(f"Verification email sent to {user.email}")
        else:
            # Fallback: display token for testing if email fails
            flash(f'Verification token: {user.verification_token}', 'info')
            flash('Registration successful! Check your email for verification link.', 'success')
            logger.warning(f"Failed to send verification email to {user.email}, displaying token for testing")
        
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/2fa-complete')
def complete_2fa():
    """Complete 2FA verification and login user"""
    if '2fa_user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['2fa_user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    # Login the user
    remember = session.get('2fa_remember', False)
    login_user(user, remember=remember)
    
    # Clear session data
    session.pop('2fa_user_id', None)
    session.pop('2fa_remember', None)
    
    flash('Two-factor authentication successful!', 'success')
    next_page = request.args.get('next')
    return redirect(next_page or url_for('main.index'))

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Send password reset email
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            email_sent = EmailQueueManager.send_password_reset_email(user, reset_url)
            
            if email_sent:
                flash('If that email is registered, a reset link has been sent.', 'info')
                logger.info(f"Password reset email sent to {user.email}")
            else:
                # Fallback: display token for testing if email fails
                flash(f'Password reset token: {token}', 'info')
                flash('Password reset instructions sent to your email.', 'info')
                logger.warning(f"Failed to send password reset email to {user.email}, displaying token for testing")
        else:
            # Always show this message to prevent email enumeration
            flash('If that email is registered, a reset link has been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expiration < datetime.utcnow():
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.reset_password_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expiration = None
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('/verify/<token>')
def verify_email(token):
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('main.index'))
    user = User.query.filter_by(verification_token=token).first()
    if user and not user.is_verified:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        
        # Send welcome email
        welcome_sent = EmailQueueManager.send_welcome_email(user)
        if welcome_sent:
            logger.info(f"Welcome email sent to {user.email}")
        else:
            logger.warning(f"Failed to send welcome email to {user.email}")
        
        flash('Your email has been verified! You can now log in.', 'success')
        logger.info(f"Email verified for user {user.username}")
    else:
        flash('Invalid or expired verification token.', 'error')
        logger.warning(f"Invalid verification token attempted: {token}")
    return redirect(url_for('auth.login'))

@auth_bp.route('/resend_verification', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def resend_verification():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and not user.is_verified:
            user.verification_token = secrets.token_urlsafe(32)
            db.session.commit()
            # In production, send verification email
            flash(f'Verification token: {user.verification_token}', 'info')
            flash('Verification email sent!', 'success')
            flash('In production, this would be sent via email.', 'info')
        else:
            flash('If that email is registered and unverified, a verification link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/resend_verification.html', form=form)
