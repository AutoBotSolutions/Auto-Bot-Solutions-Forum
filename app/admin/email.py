"""
Admin Email Management Module

Provides admin interface for email management, preview functionality,
and email queue monitoring for the Auto Bot Solutions Forum.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db, limiter
from app.models import User
from app.email.queue import EmailQueueManager
from app.email.service import email_service
from app.auth.decorators import admin_required
import logging

logger = logging.getLogger(__name__)

email_bp = Blueprint('admin_email', __name__, url_prefix='/admin/email')

@email_bp.route('/')
@login_required
@admin_required
def email_dashboard():
    """Email management dashboard"""
    try:
        queue_stats = EmailQueueManager.get_queue_statistics()
        return render_template('admin/email/dashboard.html', queue_stats=queue_stats)
    except Exception as e:
        logger.error(f"Error loading email dashboard: {str(e)}")
        flash('Error loading email dashboard', 'error')
        return redirect(url_for('admin.dashboard'))

@email_bp.route('/preview')
@login_required
@admin_required
def email_preview():
    """Email preview interface"""
    return render_template('admin/email/preview.html')

@email_bp.route('/preview/render', methods=['POST'])
@login_required
@admin_required
def render_email_preview():
    """Render email preview"""
    try:
        template = request.form.get('template')
        format_type = request.form.get('format', 'html')
        
        # Create sample context based on template
        if template == 'verification':
            sample_user = User(
                username='sample_user',
                email='sample@example.com',
                verification_token='sample_verification_token_12345'
            )
            context = {
                'user': sample_user,
                'verification_url': 'http://localhost:5000/auth/verify/sample_verification_token_12345'
            }
        elif template == 'password_reset':
            sample_user = User(
                username='sample_user',
                email='sample@example.com',
                reset_token='sample_reset_token_67890'
            )
            context = {
                'user': sample_user,
                'reset_url': 'http://localhost:5000/auth/reset_password/sample_reset_token_67890'
            }
        elif template == 'welcome':
            sample_user = User(
                username='sample_user',
                email='sample@example.com'
            )
            context = {
                'user': sample_user,
                'login_url': 'http://localhost:5000/auth/login'
            }
        else:
            return jsonify({'error': 'Invalid template'}), 400
        
        # Render preview
        preview = EmailQueueManager.preview_email(template, context, format_type)
        
        return jsonify({
            'preview': preview,
            'template': template,
            'format': format_type
        })
        
    except Exception as e:
        logger.error(f"Error rendering email preview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@email_bp.route('/queue/status')
@login_required
@admin_required
def queue_status():
    """Get email queue status"""
    try:
        status = EmailQueueManager.get_queue_statistics()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@email_bp.route('/queue/process')
@login_required
@admin_required
@limiter.limit("5 per minute")
def process_queue():
    """Manually process email queue"""
    try:
        processed = email_service.process_queue()
        flash(f'Processed {processed} emails from queue', 'success')
        return redirect(url_for('admin_email.email_dashboard'))
    except Exception as e:
        logger.error(f"Error processing email queue: {str(e)}")
        flash('Error processing email queue', 'error')
        return redirect(url_for('admin_email.email_dashboard'))

@email_bp.route('/test/send', methods=['POST'])
@login_required
@admin_required
@limiter.limit("3 per minute")
def send_test_email():
    """Send test email"""
    try:
        recipient = request.form.get('recipient')
        template = request.form.get('template')
        
        if not recipient or not template:
            flash('Recipient and template are required', 'error')
            return redirect(url_for('admin_email.email_dashboard'))
        
        # Get a sample user for testing
        test_user = User.query.filter_by(email=recipient).first()
        if not test_user:
            # Create a temporary user object for testing
            test_user = User(
                username='test_user',
                email=recipient,
                verification_token='test_verification_token'
            )
        
        # Send test email based on template
        if template == 'verification':
            verification_url = f'http://localhost:5000/auth/verify/{test_user.verification_token}'
            success = EmailQueueManager.send_verification_email(test_user, verification_url)
        elif template == 'password_reset':
            reset_url = f'http://localhost:5000/auth/reset_password/{test_user.verification_token}'
            success = EmailQueueManager.send_password_reset_email(test_user, reset_url)
        elif template == 'welcome':
            success = EmailQueueManager.send_welcome_email(test_user)
        else:
            flash('Invalid template selected', 'error')
            return redirect(url_for('admin_email.email_dashboard'))
        
        if success:
            flash(f'Test {template} email sent to {recipient}', 'success')
            logger.info(f"Test {template} email sent to {recipient}")
        else:
            flash(f'Failed to send test {template} email', 'error')
            logger.error(f"Failed to send test {template} email to {recipient}")
        
        return redirect(url_for('admin_email.email_dashboard'))
        
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        flash('Error sending test email', 'error')
        return redirect(url_for('admin_email.email_dashboard'))

@email_bp.route('/config')
@login_required
@admin_required
def email_config():
    """Email configuration display"""
    from flask import current_app
    
    config = {
        'MAIL_SERVER': current_app.config.get('MAIL_SERVER'),
        'MAIL_PORT': current_app.config.get('MAIL_PORT'),
        'MAIL_USE_TLS': current_app.config.get('MAIL_USE_TLS'),
        'MAIL_USE_SSL': current_app.config.get('MAIL_USE_SSL'),
        'MAIL_USERNAME': current_app.config.get('MAIL_USERNAME'),
        'MAIL_DEFAULT_SENDER': current_app.config.get('MAIL_DEFAULT_SENDER'),
        'MAIL_MAX_EMAILS': current_app.config.get('MAIL_MAX_EMAILS'),
        'MAIL_SUPPRESS_SEND': current_app.config.get('MAIL_SUPPRESS_SEND'),
        'MAIL_QUEUE_ENABLED': current_app.config.get('MAIL_QUEUE_ENABLED'),
        'MAIL_QUEUE_URL': current_app.config.get('MAIL_QUEUE_URL'),
        'MAIL_RETRY_ATTEMPTS': current_app.config.get('MAIL_RETRY_ATTEMPTS'),
        'MAIL_RETRY_DELAY': current_app.config.get('MAIL_RETRY_DELAY')
    }
    
    # Hide sensitive information
    if config.get('MAIL_USERNAME'):
        config['MAIL_USERNAME'] = '***' + config['MAIL_USERNAME'][-4:] if len(config['MAIL_USERNAME']) > 4 else '***'
    if config.get('MAIL_DEFAULT_SENDER') and '@' in config['MAIL_DEFAULT_SENDER']:
        email_parts = config['MAIL_DEFAULT_SENDER'].split('@')
        config['MAIL_DEFAULT_SENDER'] = f'***@{email_parts[1]}'
    
    return render_template('admin/email/config.html', config=config)
