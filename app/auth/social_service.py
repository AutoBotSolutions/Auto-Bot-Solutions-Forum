"""
Social Login Service

Handles OAuth2 authentication flows, user creation, and social account linking
for the Auto Bot Solutions Forum.
"""

import secrets
import json
from datetime import datetime, timedelta
from flask import current_app, session, url_for, flash, redirect
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, SocialAccount, SocialLoginSession
from app.auth.social_config import oauth, get_provider_config, is_provider_available
import logging

logger = logging.getLogger(__name__)

class SocialAuthService:
    """Service for managing social login authentication"""
    
    def __init__(self):
        self.oauth = oauth
    
    def get_authorization_url(self, provider, redirect_url=None):
        """Get OAuth2 authorization URL for provider"""
        if not is_provider_available(provider):
            raise ValueError(f"Provider {provider} is not available")
        
        # Create session for OAuth2 flow
        session_id = secrets.token_urlsafe(32)
        state = secrets.token_urlsafe(32)
        
        # Store session data
        oauth_session = SocialLoginSession(
            session_id=session_id,
            provider=provider,
            state=state,
            redirect_url=redirect_url or url_for('main.index', _external=True),
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db.session.add(oauth_session)
        db.session.commit()
        
        # Store session_id in user session
        session['social_session_id'] = session_id
        
        # Get OAuth client
        client = self.oauth.create_client(provider)
        
        # Build authorization URL
        config = get_provider_config(provider)
        authorization_url = client.authorize_redirect(
            url_for('auth.social_callback', provider=provider, _external=True),
            state=state,
            **config.get('client_kwargs', {})
        )
        
        return authorization_url
    
    def handle_callback(self, provider, authorization_response):
        """Handle OAuth2 callback"""
        # Get session data
        session_id = session.get('social_session_id')
        if not session_id:
            raise ValueError("No social session found")
        
        oauth_session = SocialLoginSession.query.filter_by(session_id=session_id).first()
        if not oauth_session or oauth_session.is_expired():
            raise ValueError("Social session expired or not found")
        
        if oauth_session.provider != provider:
            raise ValueError("Provider mismatch")
        
        # Verify state
        if authorization_response.get('state') != oauth_session.state:
            raise ValueError("Invalid state parameter")
        
        # Get OAuth client
        client = self.oauth.create_client(provider)
        
        # Exchange authorization code for access token
        token = client.authorize_access_token(authorization_response)
        
        # Get user info from provider
        user_info = self.get_user_info(provider, client, token)
        
        # Find or create user
        user = self.find_or_create_user(provider, user_info, token)
        
        # Link social account
        self.link_social_account(user, provider, user_info, token)
        
        # Clean up session
        db.session.delete(oauth_session)
        db.session.commit()
        session.pop('social_session_id', None)
        
        return user, oauth_session.redirect_url
    
    def get_user_info(self, provider, client, token):
        """Get user information from OAuth2 provider"""
        try:
            if provider == 'google':
                # Google OpenID Connect
                user_info = client.parse_id_token(token)
                return {
                    'id': user_info.get('sub'),
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'username': user_info.get('email', '').split('@')[0],
                    'avatar_url': user_info.get('picture'),
                    'verified': user_info.get('email_verified', False),
                    'profile': user_info
                }
            
            elif provider == 'github':
                # GitHub OAuth2
                resp = client.get('user', token=token)
                user_info = resp.json()
                
                # Get user email (GitHub requires separate request for email)
                email_info = self.get_github_user_email(client, token)
                
                return {
                    'id': str(user_info.get('id')),
                    'email': email_info.get('email'),
                    'name': user_info.get('name'),
                    'username': user_info.get('login'),
                    'avatar_url': user_info.get('avatar_url'),
                    'verified': email_info.get('verified', False),
                    'profile': user_info
                }
            
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            logger.error(f"Error getting user info from {provider}: {str(e)}")
            raise
    
    def get_github_user_email(self, client, token):
        """Get GitHub user email (primary and verified)"""
        try:
            resp = client.get('user/emails', token=token)
            emails = resp.json()
            
            # Find primary email
            for email in emails:
                if email.get('primary') and email.get('verified'):
                    return email
            
            # Fallback to first email
            return emails[0] if emails else {}
            
        except Exception as e:
            logger.error(f"Error getting GitHub user email: {str(e)}")
            return {}
    
    def find_or_create_user(self, provider, user_info, token):
        """Find existing user or create new one"""
        # First, check if there's a social account with this provider
        social_account = SocialAccount.query.filter_by(
            provider=provider,
            provider_user_id=user_info['id']
        ).first()
        
        if social_account and social_account.is_active:
            # Update social account token
            social_account.update_token(
                token.get('access_token'),
                token.get('refresh_token'),
                self.get_token_expiration(token)
            )
            
            # Update user info
            self.update_user_from_social(social_account.user, user_info)
            
            return social_account.user
        
        # Check if there's a user with the same email
        email = user_info.get('email')
        if email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                # Link social account to existing user
                existing_user.link_social_account(
                    provider=provider,
                    provider_user_id=user_info['id'],
                    access_token=token.get('access_token'),
                    refresh_token=token.get('refresh_token'),
                    expires_at=self.get_token_expiration(token),
                    email=user_info.get('email'),
                    name=user_info.get('name'),
                    username=user_info.get('username'),
                    avatar_url=user_info.get('avatar_url'),
                    profile_data=user_info.get('profile')
                )
                
                # Update user profile from social data
                self.update_user_from_social(existing_user, user_info)
                
                return existing_user
        
        # Create new user
        return self.create_user_from_social(provider, user_info, token)
    
    def create_user_from_social(self, provider, user_info, token):
        """Create new user from social login"""
        # Generate username
        username = self.generate_username(user_info.get('username'), user_info.get('name'))
        
        # Generate random password
        password = secrets.token_urlsafe(32)
        
        # Create user
        user = User(
            username=username,
            email=user_info.get('email'),
            is_active=True,
            is_verified=user_info.get('verified', True),  # Assume verified from social provider
            avatar_url=user_info.get('avatar_url')
        )
        user.set_password(password)
        
        # Add bio
        if user_info.get('name'):
            user.bio = f"Connected via {provider.title()}"
        
        db.session.add(user)
        db.session.commit()
        
        # Link social account
        user.link_social_account(
            provider=provider,
            provider_user_id=user_info['id'],
            access_token=token.get('access_token'),
            refresh_token=token.get('refresh_token'),
            expires_at=self.get_token_expiration(token),
            email=user_info.get('email'),
            name=user_info.get('name'),
            username=user_info.get('username'),
            avatar_url=user_info.get('avatar_url'),
            profile_data=user_info.get('profile')
        )
        
        logger.info(f"Created new user {username} via {provider} social login")
        return user
    
    def update_user_from_social(self, user, user_info):
        """Update user profile from social login data"""
        updated = False
        
        # Update avatar if not set
        if not user.avatar_url and user_info.get('avatar_url'):
            user.avatar_url = user_info['avatar_url']
            updated = True
        
        # Update bio if not set
        if not user.bio and user_info.get('name'):
            user.bio = f"Connected via social login"
            updated = True
        
        # Update email verification status
        if not user.is_verified and user_info.get('verified'):
            user.is_verified = True
            updated = True
        
        if updated:
            user.updated_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"Updated user {user.username} from social data")
    
    def link_social_account(self, user, provider, user_info, token):
        """Link social account to user"""
        user.link_social_account(
            provider=provider,
            provider_user_id=user_info['id'],
            access_token=token.get('access_token'),
            refresh_token=token.get('refresh_token'),
            expires_at=self.get_token_expiration(token),
            email=user_info.get('email'),
            name=user_info.get('name'),
            username=user_info.get('username'),
            avatar_url=user_info.get('avatar_url'),
            profile_data=user_info.get('profile')
        )
    
    def get_token_expiration(self, token):
        """Get token expiration time from token data"""
        expires_in = token.get('expires_in')
        if expires_in:
            return datetime.utcnow() + timedelta(seconds=expires_in)
        return None
    
    def generate_username(self, preferred_username, name):
        """Generate unique username from social data"""
        base_username = preferred_username or name or 'user'
        
        # Clean up username
        base_username = base_username.lower().replace(' ', '_').replace('-', '_')
        base_username = ''.join(c for c in base_username if c.isalnum() or c == '_')
        
        # Ensure it starts with letter
        if base_username and base_username[0].isdigit():
            base_username = 'user_' + base_username
        
        # Ensure it's not empty
        if not base_username:
            base_username = 'user'
        
        # Ensure uniqueness
        username = base_username
        counter = 1
        
        while User.query.filter_by(username=username).first():
            username = f"{base_username}_{counter}"
            counter += 1
            
            # Prevent infinite loop
            if counter > 1000:
                username = f"user_{secrets.token_hex(4)}"
                break
        
        return username
    
    def unlink_social_account(self, user, provider):
        """Unlink social account from user"""
        success = user.unlink_social_account(provider)
        if success:
            logger.info(f"Unlinked {provider} account from user {user.username}")
        return success
    
    def refresh_token(self, social_account):
        """Refresh OAuth2 token for social account"""
        try:
            client = self.oauth.create_client(social_account.provider)
            
            if social_account.refresh_token:
                # Use refresh token to get new access token
                token = client.refresh_token(social_account.refresh_token)
                
                # Update token in database
                social_account.update_token(
                    token.get('access_token'),
                    token.get('refresh_token'),
                    self.get_token_expiration(token)
                )
                
                logger.info(f"Refreshed token for {social_account.provider} account")
                return True
            else:
                logger.warning(f"No refresh token available for {social_account.provider} account")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing token for {social_account.provider}: {str(e)}")
            return False
    
    def _generate_device_fingerprint(self, user_agent, ip_address):
        """Generate device fingerprint from user agent and IP"""
        if not user_agent:
            return hashlib.md5(ip_address.encode()).hexdigest()
        
        # Extract key parts from user agent
        import re
        # Extract browser name and version
        browser_match = re.search(r'(Chrome|Firefox|Safari|Edge|Opera)[/\s]\d+', user_agent)
        browser = browser_match.group(0) if browser_match else 'Unknown'
        
        # Extract OS
        os_match = re.search(r'(Windows|Mac|Linux|Android|iOS)', user_agent)
        os = os_match.group(0) if os_match else 'Unknown'
        
        # Create fingerprint
        fingerprint_data = f"{browser}|{os}|{ip_address}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
    
    def _generate_session_id(self):
        """Generate secure session ID"""
        import secrets
        return secrets.token_urlsafe(32)

# Global service instance
social_service = SocialAuthService()
