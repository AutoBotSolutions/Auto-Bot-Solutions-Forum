"""
OAuth2 Authentication Models
Provides database models for OAuth2 clients, tokens, and authorization codes
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app import db

# Import OAuth2 mixins from authlib
try:
    from authlib.integrations.sqla_oauth2 import (
        OAuth2ClientMixin,
        OAuth2TokenMixin,
        OAuth2AuthorizationCodeMixin
    )
except ImportError:
    # Fallback if authlib is not available
    OAuth2ClientMixin = object
    OAuth2TokenMixin = object
    OAuth2AuthorizationCodeMixin = object

class OAuth2Client(db.Model, OAuth2ClientMixin):
    """OAuth2 Client Model"""
    __tablename__ = 'oauth2_clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    client_id = Column(String(64), unique=True, nullable=False, index=True)
    client_secret = Column(String(128), nullable=False)
    client_id_issued_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    client_secret_expires_at = Column(DateTime, nullable=False)
    client_uri = Column(Text)
    redirect_uris = Column(Text, nullable=False)  # Space-separated URIs
    default_scopes = Column(Text, nullable=False)  # Space-separated scopes
    allowed_scopes = Column(Text, nullable=False)  # Space-separated scopes
    response_types = Column(String(100), default='code')
    grant_types = Column(String(100), default='authorization_code')
    token_endpoint_auth_method = Column(String(50), default='client_secret_basic')
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship('User', backref='oauth2_clients')
    tokens = relationship('OAuth2Token', backref='client', lazy='dynamic')
    authorization_codes = relationship('OAuth2AuthorizationCode', backref='client', lazy='dynamic')
    
    def __repr__(self):
        return f'<OAuth2Client {self.client_id}>'
    
    @property
    def redirect_uri_list(self):
        """Get redirect URIs as list"""
        return self.redirect_uris.split() if self.redirect_uris else []
    
    @property
    def default_scope_list(self):
        """Get default scopes as list"""
        return self.default_scopes.split() if self.default_scopes else []
    
    @property
    def allowed_scope_list(self):
        """Get allowed scopes as list"""
        return self.allowed_scopes.split() if self.allowed_scopes else []
    
    def is_secret_expired(self):
        """Check if client secret is expired"""
        return datetime.utcnow() > self.client_secret_expires_at
    
    def has_scope(self, scope):
        """Check if client has the requested scope"""
        return scope in self.allowed_scope_list
    
    def add_redirect_uri(self, uri):
        """Add a redirect URI"""
        uris = self.redirect_uri_list
        if uri not in uris:
            uris.append(uri)
            self.redirect_uris = ' '.join(uris)
    
    def remove_redirect_uri(self, uri):
        """Remove a redirect URI"""
        uris = self.redirect_uri_list
        if uri in uris:
            uris.remove(uri)
            self.redirect_uris = ' '.join(uris)
    
    def rotate_secret(self):
        """Rotate client secret"""
        import secrets
        self.client_secret = secrets.token_urlsafe(64)
        self.client_secret_expires_at = datetime.utcnow() + timedelta(days=365)
        self.updated_at = datetime.utcnow()

class OAuth2Token(db.Model, OAuth2TokenMixin):
    """OAuth2 Token Model"""
    __tablename__ = 'oauth2_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True, index=True)
    client_id = Column(String(64), ForeignKey('oauth2_clients.client_id'), nullable=False, index=True)
    token_type = Column(String(20), nullable=False, default='Bearer')
    access_token = Column(String(64), unique=True, nullable=False, index=True)
    refresh_token = Column(String(64), unique=True, nullable=True, index=True)
    scope = Column(Text)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship('User', backref='oauth2_tokens')
    client = relationship('OAuth2Client', backref='oauth2_tokens')
    
    def __repr__(self):
        return f'<OAuth2Token {self.access_token[:8]}...>'
    
    def is_expired(self):
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid (not expired and not revoked)"""
        return not self.is_expired() and not self.revoked
    
    def revoke(self):
        """Revoke the token"""
        self.revoked = True
        self.revoked_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_used(self):
        """Mark token as used"""
        self.last_used_at = datetime.utcnow()
        self.usage_count += 1
        self.updated_at = datetime.utcnow()
    
    @property
    def scope_list(self):
        """Get scopes as list"""
        return self.scope.split() if self.scope else []
    
    def has_scope(self, scope):
        """Check if token has the requested scope"""
        return scope in self.scope_list

class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    """OAuth2 Authorization Code Model"""
    __tablename__ = 'oauth2_authorization_codes'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    client_id = Column(String(64), ForeignKey('oauth2_clients.client_id'), nullable=False, index=True)
    redirect_uri = Column(Text, nullable=False)
    scope = Column(Text)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    challenge = Column(String(128))  # PKCE challenge
    challenge_method = Column(String(10))  # PKCE challenge method
    
    # Relationships
    user = relationship('User', backref='oauth2_authorization_codes')
    client = relationship('OAuth2Client', backref='oauth2_authorization_codes')
    
    def __repr__(self):
        return f'<OAuth2AuthorizationCode {self.code[:8]}...>'
    
    def is_expired(self):
        """Check if authorization code is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if authorization code is valid (not expired and not used)"""
        return not self.is_expired() and not self.used
    
    def mark_used(self):
        """Mark authorization code as used"""
        self.used = True
        self.used_at = datetime.utcnow()
    
    @property
    def scope_list(self):
        """Get scopes as list"""
        return self.scope.split() if self.scope else []

class OAuth2RefreshToken(db.Model):
    """OAuth2 Refresh Token Model"""
    __tablename__ = 'oauth2_refresh_tokens'
    
    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('oauth2_tokens.id'), nullable=False)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    token = relationship('OAuth2Token', backref='refresh_tokens')
    
    def __repr__(self):
        return f'<OAuth2RefreshToken {self.refresh_token[:8]}...>'
    
    def is_expired(self):
        """Check if refresh token is expired"""
        return datetime.utcnow() > self.expires_at
    
    def revoke(self):
        """Revoke refresh token"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
    
    def is_valid(self):
        """Check if refresh token is valid"""
        return self.is_active and not self.is_expired()

class OAuth2Scope(db.Model):
    """OAuth2 Scope Model"""
    __tablename__ = 'oauth2_scopes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    required_user_role = Column(String(50), nullable=True)  # Required user role to use this scope
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f'<OAuth2Scope {self.name}>'
    
    @staticmethod
    def get_default_scopes():
        """Get all default scopes"""
        return OAuth2Scope.query.filter_by(is_default=True, is_active=True).all()
    
    @staticmethod
    def get_public_scopes():
        """Get all public scopes"""
        return OAuth2Scope.query.filter_by(is_public=True, is_active=True).all()
    
    @staticmethod
    def validate_scopes(scopes):
        """Validate a list of scopes"""
        scope_list = scopes.split() if isinstance(scopes, str) else scopes
        valid_scopes = []
        
        for scope in scope_list:
            scope_obj = OAuth2Scope.query.filter_by(name=scope, is_active=True).first()
            if scope_obj:
                valid_scopes.append(scope)
            else:
                # Return None for invalid scope
                return None
        
        return valid_scopes

class OAuth2UserConsent(db.Model):
    """OAuth2 User Consent Model"""
    __tablename__ = 'oauth2_user_consents'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    client_id = Column(String(64), ForeignKey('oauth2_clients.client_id'), nullable=False, index=True)
    scopes = Column(Text, nullable=False)  # Space-separated scopes
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship('User', backref='oauth2_consents')
    client = relationship('OAuth2Client', backref='user_consents')
    
    def __repr__(self):
        return f'<OAuth2UserConsent user:{self.user_id} client:{self.client_id}>'
    
    @property
    def scope_list(self):
        """Get scopes as list"""
        return self.scopes.split() if self.scopes else []
    
    def has_scope(self, scope):
        """Check if consent has the requested scope"""
        return scope in self.scope_list
    
    def is_expired(self):
        """Check if consent is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def is_valid(self):
        """Check if consent is valid (not expired and not revoked)"""
        return self.is_active and not self.is_expired()
    
    def revoke(self):
        """Revoke the consent"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()

# Initialize OAuth2 grants (custom implementations for missing mixins)
try:
    from authlib.integrations.sqla_oauth2 import (
        RefreshTokenGrant,
        ClientCredentialsGrant,
    )
except ImportError:
    # Fallback implementations
    RefreshTokenGrant = object
    ClientCredentialsGrant = object

class AuthorizationCodeGrant:
    """Custom Authorization Code Grant"""
    
    def create_authorization_code(self, client, grant_user, request, *args, **kwargs):
        """Create authorization code"""
        code = OAuth2AuthorizationCode(
            code=secrets.token_urlsafe(32),
            client_id=client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user_id=grant_user.id,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            challenge=request.data.get('code_challenge'),
            challenge_method=request.data.get('code_challenge_method')
        )
        db.session.add(code)
        db.session.commit()
        return code
    
    def parse_authorization_code(self, code, client):
        """Parse authorization code"""
        return OAuth2AuthorizationCode.query.filter_by(
            code=code,
            client_id=client.client_id
        ).first()

class RefreshTokenGrant(RefreshTokenGrant):
    """Custom Refresh Token Grant"""
    
    def create_refresh_token(self, token, request, *args, **kwargs):
        """Create refresh token"""
        refresh_token = OAuth2RefreshToken(
            token_id=token.id,
            refresh_token=secrets.token_urlsafe(32),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(refresh_token)
        db.session.commit()
        return refresh_token
    
    def parse_refresh_token(self, refresh_token, client):
        """Parse refresh token"""
        return OAuth2RefreshToken.query.filter_by(
            refresh_token=refresh_token
        ).first()

class ClientCredentialsGrant(ClientCredentialsGrant):
    """Custom Client Credentials Grant"""
    pass

# Initialize OAuth2 endpoints (custom implementations for missing classes)
try:
    from authlib.integrations.sqla_oauth2 import (
        create_bearer_token_validator,
        create_query_token_func,
        create_save_token_func,
        create_revocation_endpoint,
    )
except ImportError:
    # Fallback implementations
    create_bearer_token_validator = None
    create_query_token_func = None
    create_save_token_func = None
    create_revocation_endpoint = None

class TokenEndpoint:
    """Custom Token Endpoint"""
    pass

class RevocationEndpoint:
    """Custom Revocation Endpoint"""
    pass

class IntrospectionEndpoint:
    """Custom Introspection Endpoint"""
    pass
