"""
OAuth2 Authentication System
Provides OAuth2 authentication for API access with support for multiple providers
"""

from flask import Blueprint, request, jsonify, redirect, url_for, session, current_app
from authlib.integrations.flask_client import OAuth
from authlib.integrations.flask_oauth2 import AuthorizationServer, ResourceProtector
from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2TokenMixin,
    OAuth2AuthorizationCodeMixin,
)
from authlib.oidc.core import UserInfo
from werkzeug.security import gen_salt
from datetime import datetime, timedelta
import secrets
import hashlib

from app import db
from app.models import User
from .models import OAuth2Client, OAuth2Token, OAuth2AuthorizationCode, OAuth2RefreshToken
from .services import OAuth2Service

oauth2_bp = Blueprint('oauth2', __name__, url_prefix='/api/auth/oauth2')

# Initialize OAuth
oauth = OAuth()
oauth.init_app(current_app)

# Initialize Authorization Server
authorization = AuthorizationServer()

def query_client(client_id):
    """Query OAuth2 client by client_id"""
    return OAuth2Client.query.filter_by(client_id=client_id).first()

def save_token(token, request, *args, **kwargs):
    """Save OAuth2 token"""
    if request.user:
        token_data = {
            'user_id': request.user.id,
            'client_id': request.client.client_id,
            'token_type': token['token_type'],
            'access_token': token['access_token'],
            'refresh_token': token.get('refresh_token'),
            'scope': token['scope'],
            'revoked': False,
            'expires_at': datetime.utcnow() + timedelta(seconds=token.get('expires_in', 3600)),
            'created_at': datetime.utcnow()
        }
        
        oauth_token = OAuth2Token(**token_data)
        db.session.add(oauth_token)
        db.session.commit()

def generate_client_id():
    """Generate a unique client ID"""
    return secrets.token_urlsafe(32)

def generate_client_secret():
    """Generate a unique client secret"""
    return secrets.token_urlsafe(64)

@oauth2_bp.route('/register', methods=['POST'])
def register_client():
    """Register a new OAuth2 client"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'redirect_uris', 'scopes']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate client credentials
        client_id = generate_client_id()
        client_secret = generate_client_secret()
        client_id_issued_at = datetime.utcnow()
        client_secret_expires_at = client_id_issued_at + timedelta(days=365)
        
        # Create OAuth2 client
        client = OAuth2Client(
            name=data['name'],
            client_id=client_id,
            client_secret=client_secret,
            client_id_issued_at=client_id_issued_at,
            client_secret_expires_at=client_secret_expires_at,
            client_uri=data.get('client_uri', ''),
            redirect_uris=data['redirect_uris'],
            default_scopes=data['scopes'],
            allowed_scopes=data['scopes'],
            response_types='code',
            grant_types='authorization_code',
            token_endpoint_auth_method='client_secret_basic',
            user_id=data.get('user_id'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(client)
        db.session.commit()
        
        return jsonify({
            'client_id': client_id,
            'client_secret': client_secret,
            'client_id_issued_at': client_id_issued_at.isoformat(),
            'client_secret_expires_at': client_secret_expires_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@oauth2_bp.route('/authorize', methods=['GET', 'POST'])
def authorize():
    """OAuth2 authorization endpoint"""
    try:
        # Get authorization request parameters
        client_id = request.args.get('client_id')
        redirect_uri = request.args.get('redirect_uri')
        response_type = request.args.get('response_type')
        scope = request.args.get('scope')
        state = request.args.get('state')
        
        # Validate client
        client = OAuth2Client.query.filter_by(client_id=client_id).first()
        if not client:
            return jsonify({'error': 'Invalid client'}), 400
        
        # Validate redirect URI
        if redirect_uri not in client.redirect_uris.split():
            return jsonify({'error': 'Invalid redirect URI'}), 400
        
        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Generate authorization code
        code = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        auth_code = OAuth2AuthorizationCode(
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            user_id=request.user.id,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        
        db.session.add(auth_code)
        db.session.commit()
        
        # Build callback URL
        callback_url = f"{redirect_uri}?code={code}"
        if state:
            callback_url += f"&state={state}"
        
        return redirect(callback_url)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@oauth2_bp.route('/token', methods=['POST'])
def issue_token():
    """OAuth2 token endpoint"""
    try:
        grant_type = request.form.get('grant_type')
        
        if grant_type == 'authorization_code':
            return handle_authorization_code_grant()
        elif grant_type == 'refresh_token':
            return handle_refresh_token_grant()
        elif grant_type == 'client_credentials':
            return handle_client_credentials_grant()
        else:
            return jsonify({'error': 'unsupported_grant_type'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def handle_authorization_code_grant():
    """Handle authorization code grant"""
    code = request.form.get('code')
    redirect_uri = request.form.get('redirect_uri')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    
    # Validate client
    client = OAuth2Client.query.filter_by(client_id=client_id).first()
    if not client or client.client_secret != client_secret:
        return jsonify({'error': 'invalid_client'}), 401
    
    # Validate authorization code
    auth_code = OAuth2AuthorizationCode.query.filter_by(
        code=code,
        client_id=client_id,
        redirect_uri=redirect_uri
    ).first()
    
    if not auth_code or auth_code.is_expired():
        return jsonify({'error': 'invalid_grant'}), 400
    
    # Generate access token
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    expires_in = 3600  # 1 hour
    
    # Save token
    token = OAuth2Token(
        user_id=auth_code.user_id,
        client_id=client_id,
        token_type='Bearer',
        access_token=access_token,
        refresh_token=refresh_token,
        scope=auth_code.scope,
        expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
        created_at=datetime.utcnow()
    )
    
    db.session.add(token)
    
    # Delete authorization code
    db.session.delete(auth_code)
    db.session.commit()
    
    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': expires_in,
        'refresh_token': refresh_token,
        'scope': auth_code.scope
    })

def handle_refresh_token_grant():
    """Handle refresh token grant"""
    refresh_token = request.form.get('refresh_token')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    
    # Validate client
    client = OAuth2Client.query.filter_by(client_id=client_id).first()
    if not client or client.client_secret != client_secret:
        return jsonify({'error': 'invalid_client'}), 401
    
    # Find token by refresh token
    token = OAuth2Token.query.filter_by(
        refresh_token=refresh_token,
        client_id=client_id,
        revoked=False
    ).first()
    
    if not token or token.is_expired():
        return jsonify({'error': 'invalid_grant'}), 400
    
    # Generate new access token
    new_access_token = secrets.token_urlsafe(32)
    new_refresh_token = secrets.token_urlsafe(32)
    expires_in = 3600  # 1 hour
    
    # Update token
    token.access_token = new_access_token
    token.refresh_token = new_refresh_token
    token.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    token.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'access_token': new_access_token,
        'token_type': 'Bearer',
        'expires_in': expires_in,
        'refresh_token': new_refresh_token,
        'scope': token.scope
    })

def handle_client_credentials_grant():
    """Handle client credentials grant"""
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    scope = request.form.get('scope', '')
    
    # Validate client
    client = OAuth2Client.query.filter_by(client_id=client_id).first()
    if not client or client.client_secret != client_secret:
        return jsonify({'error': 'invalid_client'}), 401
    
    # Validate scope
    if scope and not all(s in client.allowed_scopes for s in scope.split()):
        return jsonify({'error': 'invalid_scope'}), 400
    
    # Generate access token
    access_token = secrets.token_urlsafe(32)
    expires_in = 3600  # 1 hour
    
    # Save token (no user for client credentials grant)
    token = OAuth2Token(
        client_id=client_id,
        token_type='Bearer',
        access_token=access_token,
        scope=scope,
        expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
        created_at=datetime.utcnow()
    )
    
    db.session.add(token)
    db.session.commit()
    
    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': expires_in,
        'scope': scope
    })

@oauth2_bp.route('/revoke', methods=['POST'])
def revoke_token():
    """Revoke OAuth2 token"""
    try:
        token = request.form.get('token')
        token_hint = request.form.get('token_type_hint', 'access_token')
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')
        
        # Validate client
        client = OAuth2Client.query.filter_by(client_id=client_id).first()
        if not client or client.client_secret != client_secret:
            return jsonify({'error': 'invalid_client'}), 401
        
        # Find and revoke token
        if token_hint == 'access_token':
            oauth_token = OAuth2Token.query.filter_by(
                access_token=token,
                client_id=client_id
            ).first()
        else:
            oauth_token = OAuth2Token.query.filter_by(
                refresh_token=token,
                client_id=client_id
            ).first()
        
        if oauth_token:
            oauth_token.revoked = True
            oauth_token.revoked_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({'message': 'Token revoked successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@oauth2_bp.route('/introspect', methods=['POST'])
def introspect_token():
    """Introspect OAuth2 token"""
    try:
        token = request.form.get('token')
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')
        
        # Validate client
        client = OAuth2Client.query.filter_by(client_id=client_id).first()
        if not client or client.client_secret != client_secret:
            return jsonify({'error': 'invalid_client'}), 401
        
        # Find token
        oauth_token = OAuth2Token.query.filter_by(
            access_token=token,
            client_id=client_id,
            revoked=False
        ).first()
        
        if not oauth_token or oauth_token.is_expired():
            return jsonify({'active': False})
        
        return jsonify({
            'active': True,
            'client_id': oauth_token.client_id,
            'token_type': oauth_token.token_type,
            'scope': oauth_token.scope,
            'exp': int(oauth_token.expires_at.timestamp()),
            'iat': int(oauth_token.created_at.timestamp()),
            'sub': str(oauth_token.user_id) if oauth_token.user_id else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Configure authorization server
def init_oauth2():
    """Initialize OAuth2 server"""
    authorization.init_app(current_app)
    authorization.register_grant(AuthorizationCodeGrant)
    authorization.register_grant(RefreshTokenGrant)
    authorization.register_grant(ClientCredentialsGrant)
    authorization.register_endpoint(TokenEndpoint)
    authorization.register_endpoint(RevocationEndpoint)
    authorization.register_endpoint(IntrospectionEndpoint)
