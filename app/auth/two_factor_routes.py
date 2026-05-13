"""
Two-Factor Authentication Routes

Routes for 2FA setup, verification, and management
for the Auto Bot Solutions Forum.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app import db, limiter
from app.models import User
from app.auth.two_factor import generate_totp_setup_data, format_backup_codes_for_display
from app.auth.two_factor_forms import (
    TwoFactorSetupForm, TwoFactorVerifyForm, TwoFactorBackupCodeForm,
    TwoFactorDisableForm, TwoFactorRegenerateCodesForm
)
import logging

logger = logging.getLogger(__name__)

two_factor_bp = Blueprint('two_factor', __name__, url_prefix='/auth/2fa')

@two_factor_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """Setup 2FA for the user"""
    if current_user.is_2fa_enabled:
        flash('Two-factor authentication is already enabled for your account.', 'info')
        return redirect(url_for('two_factor.manage'))
    
    if request.method == 'GET':
        # Generate setup data
        setup_data = generate_totp_setup_data(current_user.email)
        
        # Store temporary data in session
        session['temp_totp_secret'] = setup_data['secret']
        session['temp_backup_codes'] = setup_data['backup_codes']
        
        return render_template('auth/2fa/setup.html', 
                             qr_code=setup_data['qr_code'],
                             secret=setup_data['secret'],
                             backup_codes=setup_data['backup_codes'],
                             formatted_backup_codes=format_backup_codes_for_display(setup_data['backup_codes']))
    
    # Handle POST request for verification
    form = TwoFactorSetupForm(user=current_user)
    
    if form.validate_on_submit():
        # Verify the token
        from app.auth.two_factor import verify_2fa_token
        if verify_2fa_token(session['temp_totp_secret'], form.token.data):
            # Enable 2FA for the user
            current_user.enable_2fa(session['temp_totp_secret'], session['temp_backup_codes'])
            db.session.commit()
            
            # Clear session data
            session.pop('temp_totp_secret', None)
            session.pop('temp_backup_codes', None)
            
            flash('Two-factor authentication has been successfully enabled for your account!', 'success')
            logger.info(f"2FA enabled for user {current_user.username}")
            
            return redirect(url_for('two_factor.manage'))
        else:
            flash('Invalid authentication code. Please try again.', 'error')
    
    return render_template('auth/2fa/setup.html', form=form)

@two_factor_bp.route('/verify', methods=['GET', 'POST'])
@login_required
def verify():
    """Verify 2FA token during login"""
    if not current_user.is_2fa_enabled:
        return redirect(url_for('main.index'))
    
    form = TwoFactorVerifyForm(user=current_user)
    
    if form.validate_on_submit():
        # Token is already validated by the form
        if form.remember_device.data:
            # Set device cookie for 30 days
            from datetime import datetime, timedelta
            response = redirect(url_for('auth.complete_2fa'))
            response.set_cookie('2fa_remember', str(current_user.id), 
                             expires=datetime.utcnow() + timedelta(days=30))
            return response
        
        flash('Authentication successful!', 'success')
        return redirect(url_for('auth.complete_2fa'))
    
    return render_template('auth/2fa/verify.html', form=form)

@two_factor_bp.route('/backup-code', methods=['GET', 'POST'])
@login_required
def use_backup_code():
    """Use backup code for 2FA"""
    if not current_user.is_2fa_enabled:
        return redirect(url_for('main.index'))
    
    form = TwoFactorBackupCodeForm(user=current_user)
    
    if form.validate_on_submit():
        # Backup code is already validated by the form
        flash('Backup code used successfully. Please consider regenerating your backup codes.', 'warning')
        return redirect(url_for('two_factor.manage'))
    
    return render_template('auth/2fa/backup_code.html', form=form)

@two_factor_bp.route('/manage')
@login_required
def manage():
    """Manage 2FA settings"""
    if not current_user.is_2fa_enabled:
        flash('Two-factor authentication is not enabled for your account.', 'info')
        return redirect(url_for('two_factor.setup'))
    
    backup_codes_count = current_user.get_unused_backup_codes_count()
    
    return render_template('auth/2fa/manage.html',
                         backup_codes_count=backup_codes_count,
                         last_2fa_used=current_user.last_2fa_used)

@two_factor_bp.route('/disable', methods=['GET', 'POST'])
@login_required
def disable():
    """Disable 2FA"""
    if not current_user.is_2fa_enabled:
        flash('Two-factor authentication is not enabled for your account.', 'info')
        return redirect(url_for('two_factor.setup'))
    
    form = TwoFactorDisableForm(user=current_user)
    
    if form.validate_on_submit():
        # Form is already validated
        current_user.disable_2fa()
        db.session.commit()
        
        flash('Two-factor authentication has been disabled for your account.', 'warning')
        logger.info(f"2FA disabled for user {current_user.username}")
        
        return redirect(url_for('user.profile'))
    
    return render_template('auth/2fa/disable.html', form=form)

@two_factor_bp.route('/regenerate-codes', methods=['GET', 'POST'])
@login_required
def regenerate_codes():
    """Regenerate backup codes"""
    if not current_user.is_2fa_enabled:
        flash('Two-factor authentication is not enabled for your account.', 'info')
        return redirect(url_for('two_factor.setup'))
    
    form = TwoFactorRegenerateCodesForm(user=current_user)
    
    if form.validate_on_submit():
        # Generate new backup codes
        from app.auth.two_factor import two_fa_service
        new_codes = two_fa_service.generate_backup_codes()
        
        # Update user's backup codes
        current_user.regenerate_backup_codes(new_codes)
        db.session.commit()
        
        flash('Backup codes have been regenerated. Please save them in a secure location.', 'success')
        logger.info(f"Backup codes regenerated for user {current_user.username}")
        
        return render_template('auth/2fa/show_backup_codes.html',
                             backup_codes=new_codes,
                             formatted_backup_codes=format_backup_codes_for_display(new_codes))
    
    return render_template('auth/2fa/regenerate_codes.html', form=form)

@two_factor_bp.route('/show-backup-codes')
@login_required
def show_backup_codes():
    """Show current backup codes (only if they haven't been used)"""
    if not current_user.is_2fa_enabled:
        flash('Two-factor authentication is not enabled for your account.', 'info')
        return redirect(url_for('two_factor.setup'))
    
    # This would typically require password confirmation for security
    # For now, we'll just show a message
    flash('For security, please regenerate backup codes to view them.', 'info')
    return redirect(url_for('two_factor.regenerate_codes'))

@two_factor_bp.route('/status')
@login_required
def status():
    """Get 2FA status (AJAX endpoint)"""
    return jsonify({
        'enabled': current_user.is_2fa_enabled,
        'backup_codes_count': current_user.get_unused_backup_codes_count(),
        'last_used': current_user.last_2fa_used.isoformat() if current_user.last_2fa_used else None
    })

# Helper function to check if user needs 2FA verification
def requires_2fa_verification(user):
    """Check if user needs 2FA verification"""
    if not user or not user.is_2fa_enabled:
        return False
    
    # Check if device is remembered
    if request.cookies.get('2fa_remember') == str(user.id):
        return False
    
    return True
