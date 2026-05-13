"""
Social Login Configuration

OAuth2 provider configurations for social login integration
for the Auto Bot Solutions Forum.
"""

from authlib.integrations.flask_client import OAuth
from flask import current_app
import logging

logger = logging.getLogger(__name__)

oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with providers"""
    oauth.init_app(app)
    
    # Configure Google OAuth2
    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        logger.info("Google OAuth2 configured")
    else:
        logger.warning("Google OAuth2 not configured - missing client ID or secret")
    
    # Configure GitHub OAuth2
    if app.config.get('GITHUB_CLIENT_ID') and app.config.get('GITHUB_CLIENT_SECRET'):
        oauth.register(
            name='github',
            client_id=app.config['GITHUB_CLIENT_ID'],
            client_secret=app.config['GITHUB_CLIENT_SECRET'],
            access_token_url='https://github.com/login/oauth/access_token',
            authorize_url='https://github.com/login/oauth/authorize',
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'user:email'},
            fetch_token=lambda token: token
        )
        logger.info("GitHub OAuth2 configured")
    else:
        logger.warning("GitHub OAuth2 not configured - missing client ID or secret")

def get_provider_config(provider):
    """Get provider configuration"""
    configs = {
        'google': {
            'name': 'Google',
            'icon': 'fab fa-google',
            'color': '#4285F4',
            'scopes': ['openid', 'email', 'profile']
        },
        'github': {
            'name': 'GitHub',
            'icon': 'fab fa-github',
            'color': '#333333',
            'scopes': ['user:email']
        }
    }
    return configs.get(provider, {})

def get_available_providers():
    """Get list of available OAuth2 providers"""
    providers = []
    app = current_app._get_current_object()
    
    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        providers.append('google')
    
    if app.config.get('GITHUB_CLIENT_ID') and app.config.get('GITHUB_CLIENT_SECRET'):
        providers.append('github')
    
    return providers

def is_provider_available(provider):
    """Check if provider is available"""
    return provider in get_available_providers()
