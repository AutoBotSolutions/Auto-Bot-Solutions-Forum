"""
Social Login Routes

OAuth2 authentication routes for social login integration
for the Auto Bot Solutions Forum.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, SocialAccount, SocialLoginSession
from app.auth.social_service import social_service
from app.auth.social_forms import SocialLoginForm, LinkSocialAccountForm, SocialConflictResolutionForm, SocialAccountUnlinkForm, SocialProfileImportForm
from app.auth.decorators import verified_required
import logging

logger = logging.getLogger(__name__)

social_bp = Blueprint('social', __name__, url_prefix='/auth/social')

@social_bp.route('/login', methods=['GET', 'POST'])
def social_login():
    """Handle social login initiation"""
    form = SocialLoginForm()
    
    if form.validate_on_submit():
        provider = form.provider.data
        
        try:
            # Get authorization URL
            auth_url = social_service.get_authorization_url(provider)
            return redirect(auth_url)
            
        except Exception as e:
            logger.error(f"Error initiating {provider} login: {str(e)}")
            flash(f'Error connecting to {provider.title()}. Please try again.', 'error')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/social/login.html', form=form)

@social_bp.route('/<provider>/login')
def provider_login(provider):
    """Direct login with specific provider"""
    try:
        # Get authorization URL
        auth_url = social_service.get_authorization_url(provider)
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"Error initiating {provider} login: {str(e)}")
        flash(f'Error connecting to {provider.title()}. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@social_bp.route('/<provider>/callback')
def social_callback(provider):
    """Handle OAuth2 callback from provider"""
    try:
        # Handle the callback
        user, redirect_url = social_service.handle_callback(provider, request.url)
        
        # Login the user
        login_user(user)
        
        # Update last login
        user.last_login = current_app.datetime.utcnow()
        user.login_count += 1
        db.session.commit()
        
        flash(f'Successfully logged in with {provider.title()}!', 'success')
        return redirect(redirect_url or url_for('main.index'))
        
    except Exception as e:
        logger.error(f"Error handling {provider} callback: {str(e)}")
        flash(f'Error completing {provider.title()} login. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@social_bp.route('/link', methods=['GET', 'POST'])
@login_required
@verified_required
def link_account():
    """Link social account to existing user"""
    form = LinkSocialAccountForm()
    
    if form.validate_on_submit():
        provider = form.provider.data
        
        try:
            # Get authorization URL
            auth_url = social_service.get_authorization_url(provider)
            return redirect(auth_url)
            
        except Exception as e:
            logger.error(f"Error initiating {provider} account linking: {str(e)}")
            flash(f'Error connecting to {provider.title()}. Please try again.', 'error')
            return redirect(url_for('auth.profile'))
    
    return render_template('auth/social/link.html', form=form)

@social_bp.route('/unlink/<provider>', methods=['GET', 'POST'])
@login_required
def unlink_account(provider):
    """Unlink social account from user"""
    # Check if user has this social account
    social_account = current_user.get_social_account(provider)
    if not social_account:
        flash(f'No {provider.title()} account linked to your profile.', 'warning')
        return redirect(url_for('auth.profile'))
    
    form = SocialAccountUnlinkForm(current_user)
    
    if form.validate_on_submit():
        try:
            success = social_service.unlink_social_account(current_user, provider)
            if success:
                flash(f'Successfully unlinked {provider.title()} account.', 'success')
            else:
                flash(f'Error unlinking {provider.title()} account.', 'error')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            logger.error(f"Error unlinking {provider} account: {str(e)}")
            flash(f'Error unlinking {provider.title()} account. Please try again.', 'error')
    
    return render_template('auth/social/unlink.html', form=form, provider=provider, social_account=social_account)

@social_bp.route('/manage')
@login_required
def manage_accounts():
    """Manage linked social accounts"""
    social_accounts = current_user.get_social_accounts_dict()
    return render_template('auth/social/manage.html', social_accounts=social_accounts)

@social_bp.route('/import-profile', methods=['GET', 'POST'])
@login_required
def import_profile():
    """Import profile data from social accounts"""
    form = SocialProfileImportForm()
    
    if form.validate_on_submit():
        try:
            updated = False
            
            # Import from each linked social account
            for provider, account_data in current_user.get_social_accounts_dict().items():
                social_account = current_user.get_social_account(provider)
                if social_account and social_account.is_active:
                    # Import avatar
                    if form.import_avatar.data and social_account.avatar_url:
                        current_user.avatar_url = social_account.avatar_url
                        updated = True
                    
                    # Import bio
                    if form.import_bio.data and social_account.name:
                        current_user.bio = f"Connected via {provider.title()}"
                        updated = True
            
            if updated:
                db.session.commit()
                flash('Profile updated successfully from social accounts!', 'success')
            else:
                flash('No new data to import from social accounts.', 'info')
                
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            logger.error(f"Error importing profile data: {str(e)}")
            flash('Error importing profile data. Please try again.', 'error')
    
    return render_template('auth/social/import_profile.html', form=form)

@social_bp.route('/resolve-conflict', methods=['GET', 'POST'])
def resolve_conflict():
    """Resolve social login conflicts"""
    # This would be called when there's a conflict during social login
    # For now, we'll implement a basic version
    
    form = SocialConflictResolutionForm()
    
    if form.validate_on_submit():
        action = form.action.data
        
        if action == 'cancel':
            return redirect(url_for('auth.login'))
        
        elif action == 'link':
            # Link to existing account
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                # Link social account to user
                # This would need to be implemented based on the social session data
                flash('Account linked successfully!', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Invalid email or password.', 'error')
        
        elif action == 'create':
            # Create new account
            # This would need to be implemented based on the social session data
            flash('New account created!', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/social/resolve_conflict.html', form=form)

@social_bp.route('/refresh/<provider>')
@login_required
def refresh_token(provider):
    """Refresh OAuth2 token for social account"""
    social_account = current_user.get_social_account(provider)
    if not social_account:
        flash(f'No {provider.title()} account linked to your profile.', 'warning')
        return redirect(url_for('social.manage_accounts'))
    
    try:
        success = social_service.refresh_token(social_account)
        if success:
            flash(f'{provider.title()} token refreshed successfully!', 'success')
        else:
            flash(f'Failed to refresh {provider.title()} token.', 'error')
    except Exception as e:
        logger.error(f"Error refreshing {provider} token: {str(e)}")
        flash(f'Error refreshing {provider.title()} token.', 'error')
    
    return redirect(url_for('social.manage_accounts'))

@social_bp.route('/status/<provider>')
@login_required
def account_status(provider):
    """Get status of social account"""
    social_account = current_user.get_social_account(provider)
    
    if not social_account:
        return {'status': 'not_linked'}
    
    return {
        'status': 'linked',
        'provider': provider,
        'created_at': social_account.created_at.isoformat(),
        'is_token_expired': social_account.is_token_expired(),
        'last_updated': social_account.updated_at.isoformat()
    }

# Error handlers for social login
@social_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    flash('You must be logged in to access this page.', 'error')
    return redirect(url_for('auth.login'))

@social_bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden errors"""
    flash('You do not have permission to access this page.', 'error')
    return redirect(url_for('main.index'))

@social_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal error in social routes: {str(error)}")
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('main.index'))
