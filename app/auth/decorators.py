"""
Authentication Decorators

Custom decorators for authentication and authorization
for the Auto Bot Solutions Forum.
"""

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You must be logged in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('You must be an administrator to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def verified_required(f):
    """Decorator to require email verification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You must be logged in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.is_verified:
            flash('You must verify your email to access this page.', 'error')
            return redirect(url_for('auth.verify_email'))
        return f(*args, **kwargs)
    return decorated_function

def active_required(f):
    """Decorator to require active account"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You must be logged in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.can_login():
            if current_user.is_banned:
                flash('Your account has been banned.', 'error')
            elif current_user.is_suspended:
                flash('Your account has been suspended.', 'error')
            else:
                flash('Your account is not active.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
