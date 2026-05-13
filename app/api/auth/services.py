"""
OAuth2 Authentication Services
Provides business logic for OAuth2 authentication and token management
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import secrets
import hashlib
from flask import current_app

from app import db
from app.models import User
from .models import (
    OAuth2Client, OAuth2Token, OAuth2AuthorizationCode, 
    OAuth2RefreshToken, OAuth2Scope, OAuth2UserConsent
)

class OAuth2Service:
    """OAuth2 Authentication Service"""
    
    @staticmethod
    def create_client(name: str, redirect_uris: List[str], scopes: List[str], 
                     user_id: Optional[int] = None, client_uri: str = '') -> OAuth2Client:
        """Create a new OAuth2 client"""
        
        # Validate scopes
        valid_scopes = OAuth2Scope.validate_scopes(scopes)
        if valid_scopes is None:
            raise ValueError("Invalid scopes provided")
        
        # Generate client credentials
        client_id = secrets.token_urlsafe(32)
        client_secret = secrets.token_urlsafe(64)
        client_id_issued_at = datetime.utcnow()
        client_secret_expires_at = client_id_issued_at + timedelta(days=365)
        
        # Create client
        client = OAuth2Client(
            name=name,
            client_id=client_id,
            client_secret=client_secret,
            client_id_issued_at=client_id_issued_at,
            client_secret_expires_at=client_secret_expires_at,
            client_uri=client_uri,
            redirect_uris=' '.join(redirect_uris),
            default_scopes=' '.join(scopes),
            allowed_scopes=' '.join(scopes),
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(client)
        db.session.commit()
        
        return client
    
    @staticmethod
    def get_client_by_id(client_id: str) -> Optional[OAuth2Client]:
        """Get OAuth2 client by ID"""
        return OAuth2Client.query.filter_by(client_id=client_id, is_active=True).first()
    
    @staticmethod
    def get_client_by_credentials(client_id: str, client_secret: str) -> Optional[OAuth2Client]:
        """Get OAuth2 client by credentials"""
        client = OAuth2Client.query.filter_by(client_id=client_id, is_active=True).first()
        if client and client.client_secret == client_secret:
            return client
        return None
    
    @staticmethod
    def rotate_client_secret(client_id: str) -> str:
        """Rotate client secret"""
        client = OAuth2Service.get_client_by_id(client_id)
        if not client:
            raise ValueError("Client not found")
        
        client.rotate_secret()
        db.session.commit()
        
        return client.client_secret
    
    @staticmethod
    def revoke_client(client_id: str) -> bool:
        """Revoke OAuth2 client"""
        client = OAuth2Service.get_client_by_id(client_id)
        if not client:
            return False
        
        # Revoke all tokens
        OAuth2Token.query.filter_by(client_id=client_id, revoked=False).update({
            'revoked': True,
            'revoked_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        # Revoke all authorization codes
        OAuth2AuthorizationCode.query.filter_by(client_id=client_id, used=False).update({
            'used': True,
            'used_at': datetime.utcnow()
        })
        
        # Deactivate client
        client.is_active = False
        client.updated_at = datetime.utcnow()
        
        db.session.commit()
        return True
    
    @staticmethod
    def create_authorization_code(client_id: str, user_id: int, redirect_uri: str, 
                                scope: str, expires_in: int = 600) -> OAuth2AuthorizationCode:
        """Create authorization code"""
        code = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        auth_code = OAuth2AuthorizationCode(
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            user_id=user_id,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        
        db.session.add(auth_code)
        db.session.commit()
        
        return auth_code
    
    @staticmethod
    def validate_authorization_code(code: str, client_id: str, redirect_uri: str) -> Optional[OAuth2AuthorizationCode]:
        """Validate authorization code"""
        auth_code = OAuth2AuthorizationCode.query.filter_by(
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            used=False
        ).first()
        
        if auth_code and auth_code.is_valid():
            return auth_code
        
        return None
    
    @staticmethod
    def create_access_token(user_id: Optional[int], client_id: str, scope: str, 
                          expires_in: int = 3600, refresh_token_enabled: bool = True) -> OAuth2Token:
        """Create access token"""
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32) if refresh_token_enabled else None
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        token = OAuth2Token(
            user_id=user_id,
            client_id=client_id,
            token_type='Bearer',
            access_token=access_token,
            refresh_token=refresh_token,
            scope=scope,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        
        db.session.add(token)
        db.session.commit()
        
        return token
    
    @staticmethod
    def get_token_by_access_token(access_token: str) -> Optional[OAuth2Token]:
        """Get token by access token"""
        return OAuth2Token.query.filter_by(access_token=access_token).first()
    
    @staticmethod
    def validate_access_token(access_token: str) -> Optional[OAuth2Token]:
        """Validate access token"""
        token = OAuth2Service.get_token_by_access_token(access_token)
        if token and token.is_valid():
            # Mark token as used
            token.mark_used()
            db.session.commit()
            return token
        
        return None
    
    @staticmethod
    def refresh_access_token(refresh_token: str, client_id: str) -> Optional[OAuth2Token]:
        """Refresh access token"""
        token = OAuth2Token.query.filter_by(
            refresh_token=refresh_token,
            client_id=client_id,
            revoked=False
        ).first()
        
        if token and token.is_valid():
            # Create new access token
            new_token = OAuth2Service.create_access_token(
                user_id=token.user_id,
                client_id=client_id,
                scope=token.scope,
                expires_in=3600,
                refresh_token_enabled=True
            )
            
            # Revoke old token
            token.revoke()
            
            return new_token
        
        return None
    
    @staticmethod
    def revoke_token(access_token: str) -> bool:
        """Revoke access token"""
        token = OAuth2Service.get_token_by_access_token(access_token)
        if token:
            token.revoke()
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def revoke_user_tokens(user_id: int, client_id: Optional[str] = None) -> int:
        """Revoke all tokens for a user"""
        query = OAuth2Token.query.filter_by(user_id=user_id, revoked=False)
        
        if client_id:
            query = query.filter_by(client_id=client_id)
        
        count = query.count()
        query.update({
            'revoked': True,
            'revoked_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        db.session.commit()
        return count
    
    @staticmethod
    def get_user_tokens(user_id: int, client_id: Optional[str] = None, 
                       active_only: bool = True) -> List[OAuth2Token]:
        """Get tokens for a user"""
        query = OAuth2Token.query.filter_by(user_id=user_id)
        
        if client_id:
            query = query.filter_by(client_id=client_id)
        
        if active_only:
            query = query.filter_by(revoked=False)
            query = query.filter(OAuth2Token.expires_at > datetime.utcnow())
        
        return query.order_by(OAuth2Token.created_at.desc()).all()
    
    @staticmethod
    def get_client_tokens(client_id: str, active_only: bool = True) -> List[OAuth2Token]:
        """Get tokens for a client"""
        query = OAuth2Token.query.filter_by(client_id=client_id)
        
        if active_only:
            query = query.filter_by(revoked=False)
            query = query.filter(OAuth2Token.expires_at > datetime.utcnow())
        
        return query.order_by(OAuth2Token.created_at.desc()).all()
    
    @staticmethod
    def create_scope(name: str, description: str, is_default: bool = False, 
                    is_public: bool = False, required_user_role: Optional[str] = None) -> OAuth2Scope:
        """Create OAuth2 scope"""
        scope = OAuth2Scope(
            name=name,
            description=description,
            is_default=is_default,
            is_public=is_public,
            required_user_role=required_user_role,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(scope)
        db.session.commit()
        
        return scope
    
    @staticmethod
    def get_scope_by_name(name: str) -> Optional[OAuth2Scope]:
        """Get scope by name"""
        return OAuth2Scope.query.filter_by(name=name, is_active=True).first()
    
    @staticmethod
    def get_all_scopes(active_only: bool = True) -> List[OAuth2Scope]:
        """Get all scopes"""
        query = OAuth2Scope.query
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(OAuth2Scope.name).all()
    
    @staticmethod
    def validate_scopes(scopes: List[str]) -> List[str]:
        """Validate scopes"""
        valid_scopes = []
        
        for scope in scopes:
            scope_obj = OAuth2Scope.query.filter_by(name=scope, is_active=True).first()
            if scope_obj:
                valid_scopes.append(scope)
        
        return valid_scopes
    
    @staticmethod
    def create_user_consent(user_id: int, client_id: str, scopes: List[str], 
                           expires_in: Optional[int] = None) -> OAuth2UserConsent:
        """Create user consent"""
        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Revoke existing consent for this client
        OAuth2UserConsent.query.filter_by(user_id=user_id, client_id=client_id, is_active=True).update({
            'is_active': False,
            'revoked_at': datetime.utcnow()
        })
        
        consent = OAuth2UserConsent(
            user_id=user_id,
            client_id=client_id,
            scopes=' '.join(scopes),
            expires_at=expires_at,
            granted_at=datetime.utcnow()
        )
        
        db.session.add(consent)
        db.session.commit()
        
        return consent
    
    @staticmethod
    def get_user_consent(user_id: int, client_id: str) -> Optional[OAuth2UserConsent]:
        """Get user consent for client"""
        return OAuth2UserConsent.query.filter_by(
            user_id=user_id,
            client_id=client_id,
            is_active=True
        ).first()
    
    @staticmethod
    def revoke_user_consent(user_id: int, client_id: str) -> bool:
        """Revoke user consent"""
        consent = OAuth2UserConsent.query.filter_by(
            user_id=user_id,
            client_id=client_id,
            is_active=True
        ).first()
        
        if consent:
            consent.revoke()
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def get_client_stats(client_id: str) -> Dict[str, Any]:
        """Get client statistics"""
        client = OAuth2Service.get_client_by_id(client_id)
        if not client:
            return {}
        
        # Token stats
        active_tokens = OAuth2Token.query.filter_by(
            client_id=client_id,
            revoked=False
        ).filter(OAuth2Token.expires_at > datetime.utcnow()).count()
        
        total_tokens = OAuth2Token.query.filter_by(client_id=client_id).count()
        
        # Authorization code stats
        active_codes = OAuth2AuthorizationCode.query.filter_by(
            client_id=client_id,
            used=False
        ).filter(OAuth2AuthorizationCode.expires_at > datetime.utcnow()).count()
        
        # User consent stats
        active_consents = OAuth2UserConsent.query.filter_by(
            client_id=client_id,
            is_active=True
        ).count()
        
        return {
            'client_id': client_id,
            'client_name': client.name,
            'active_tokens': active_tokens,
            'total_tokens': total_tokens,
            'active_authorization_codes': active_codes,
            'active_user_consents': active_consents,
            'created_at': client.created_at.isoformat(),
            'is_active': client.is_active,
            'is_secret_expired': client.is_secret_expired()
        }
    
    @staticmethod
    def get_user_stats(user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        # Token stats
        active_tokens = OAuth2Token.query.filter_by(
            user_id=user_id,
            revoked=False
        ).filter(OAuth2Token.expires_at > datetime.utcnow()).count()
        
        total_tokens = OAuth2Token.query.filter_by(user_id=user_id).count()
        
        # Consent stats
        active_consents = OAuth2UserConsent.query.filter_by(
            user_id=user_id,
            is_active=True
        ).count()
        
        # Recent activity
        recent_tokens = OAuth2Token.query.filter_by(user_id=user_id).filter(
            OAuth2Token.created_at > datetime.utcnow() - timedelta(days=30)
        ).count()
        
        return {
            'user_id': user_id,
            'active_tokens': active_tokens,
            'total_tokens': total_tokens,
            'active_consents': active_consents,
            'recent_tokens': recent_tokens
        }
    
    @staticmethod
    def cleanup_expired_tokens() -> int:
        """Clean up expired tokens"""
        expired_tokens = OAuth2Token.query.filter(
            OAuth2Token.expires_at < datetime.utcnow()
        ).count()
        
        OAuth2Token.query.filter(
            OAuth2Token.expires_at < datetime.utcnow()
        ).delete()
        
        db.session.commit()
        
        return expired_tokens
    
    @staticmethod
    def cleanup_expired_authorization_codes() -> int:
        """Clean up expired authorization codes"""
        expired_codes = OAuth2AuthorizationCode.query.filter(
            OAuth2AuthorizationCode.expires_at < datetime.utcnow()
        ).count()
        
        OAuth2AuthorizationCode.query.filter(
            OAuth2AuthorizationCode.expires_at < datetime.utcnow()
        ).delete()
        
        db.session.commit()
        
        return expired_codes
    
    @staticmethod
    def cleanup_expired_consents() -> int:
        """Clean up expired consents"""
        expired_consents = OAuth2UserConsent.query.filter(
            OAuth2UserConsents.expires_at < datetime.utcnow(),
            OAuth2UserConsents.is_active == True
        ).count()
        
        OAuth2UserConsent.query.filter(
            OAuth2UserConsents.expires_at < datetime.utcnow(),
            OAuth2UserConsents.is_active == True
        ).update({
            'is_active': False,
            'revoked_at': datetime.utcnow()
        })
        
        db.session.commit()
        
        return expired_consents


class APIKeyService:
    """API Key Management Service"""
    
    @staticmethod
    def create_key(name: str, user_id: int, permissions: List[str] = None, 
                   expires_in: int = 365 * 24 * 60 * 60, description: str = '', 
                   rate_limit: int = 1000) -> 'APIKey':
        """Create a new API key"""
        from app.models import APIKey
        import secrets
        import hashlib
        
        # Generate API key
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Create API key record
        key_record = APIKey(
            name=name,
            key_hash=key_hash,
            api_key=api_key,  # Store temporarily for creation
            user_id=user_id,
            permissions=permissions or [],
            description=description,
            rate_limit=rate_limit,
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
            created_at=datetime.utcnow()
        )
        
        db.session.add(key_record)
        db.session.commit()
        
        return key_record
    
    @staticmethod
    def get_user_keys(user_id: int, active_only: bool = True) -> List['APIKey']:
        """Get user's API keys"""
        from app.models import APIKey
        
        query = APIKey.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(APIKey.created_at.desc()).all()
    
    @staticmethod
    def get_user_key(user_id: int, key_id: int) -> Optional['APIKey']:
        """Get user's specific API key"""
        from app.models import APIKey
        
        return APIKey.query.filter_by(id=key_id, user_id=user_id).first()
    
    @staticmethod
    def validate_key(api_key: str) -> Optional['APIKey']:
        """Validate API key"""
        from app.models import APIKey
        import hashlib
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        return APIKey.query.filter_by(key_hash=key_hash, is_active=True).first()
    
    @staticmethod
    def revoke_key(user_id: int, key_id: int) -> bool:
        """Revoke API key"""
        from app.models import APIKey
        
        key = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
        if key:
            key.revoke()
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def rotate_key(user_id: int, key_id: int) -> Optional['APIKey']:
        """Rotate API key"""
        from app.models import APIKey
        import secrets
        import hashlib
        
        key = APIKey.query.filter_by(id=key_id, user_id=user_id, is_active=True).first()
        if not key:
            return None
        
        # Generate new API key
        new_api_key = f"ak_{secrets.token_urlsafe(32)}"
        new_key_hash = hashlib.sha256(new_api_key.encode()).hexdigest()
        
        # Update key
        key.key_hash = new_key_hash
        key.api_key = new_api_key  # Store temporarily for rotation
        key.updated_at = datetime.utcnow()
        
        db.session.commit()
        return key
    
    @staticmethod
    def update_key_usage(key_id: int, endpoint: str) -> None:
        """Update API key usage statistics"""
        from app.models import APIKey, APIUsage
        
        # Update key usage
        key = APIKey.query.filter_by(id=key_id).first()
        if key:
            key.update_usage()
        
        # Record usage
        APIUsage.record_usage(key_id, endpoint)
    
    @staticmethod
    def check_rate_limit(key_id: int, limit: int = None, per: int = 3600) -> bool:
        """Check rate limit for API key"""
        from app.models import APIKey, APIUsage
        
        key = APIKey.query.filter_by(id=key_id).first()
        if not key:
            return False
        
        # Use key's rate limit if not provided
        if limit is None:
            limit = key.rate_limit
        
        # Check usage in the last period
        period_start = datetime.utcnow() - timedelta(seconds=per)
        
        usage_count = APIUsage.query.filter(
            APIUsage.api_key_id == key_id,
            APIUsage.last_request >= period_start
        ).count()
        
        return usage_count < limit
    
    @staticmethod
    def get_key_usage_stats(key_id: int, days: int = 30) -> Dict[str, Any]:
        """Get API key usage statistics"""
        from app.models import APIUsage, APIKey
        
        key = APIKey.query.filter_by(id=key_id).first()
        if not key:
            return {}
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get usage records
        usage_records = APIUsage.query.filter(
            APIUsage.api_key_id == key_id,
            APIUsage.created_at >= start_date
        ).all()
        
        # Calculate statistics
        total_requests = sum(record.request_count for record in usage_records)
        unique_endpoints = len(set(record.endpoint for record in usage_records))
        daily_usage = {}
        
        for record in usage_records:
            date_key = record.created_at.date().isoformat()
            if date_key not in daily_usage:
                daily_usage[date_key] = 0
            daily_usage[date_key] += record.request_count
        
        # Get most used endpoints
        endpoint_usage = {}
        for record in usage_records:
            if record.endpoint not in endpoint_usage:
                endpoint_usage[record.endpoint] = 0
            endpoint_usage[record.endpoint] += record.request_count
        
        sorted_endpoints = sorted(endpoint_usage.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'key_id': key_id,
            'key_name': key.name,
            'total_requests': total_requests,
            'unique_endpoints': unique_endpoints,
            'daily_usage': daily_usage,
            'top_endpoints': sorted_endpoints[:10],
            'period_days': days,
            'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
            'usage_count': key.usage_count
        }
    
    @staticmethod
    def get_user_usage_stats(user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get user's API usage statistics"""
        from app.models import APIKey, APIUsage
        
        # Get user's keys
        keys = APIKeyService.get_user_keys(user_id)
        
        if not keys:
            return {
                'user_id': user_id,
                'total_keys': 0,
                'total_requests': 0,
                'active_keys': 0,
                'key_stats': []
            }
        
        # Calculate statistics
        total_requests = 0
        active_keys = 0
        key_stats = []
        
        for key in keys:
            if key.is_valid():
                active_keys += 1
            
            stats = APIKeyService.get_key_usage_stats(key.id, days)
            total_requests += stats.get('total_requests', 0)
            key_stats.append(stats)
        
        return {
            'user_id': user_id,
            'total_keys': len(keys),
            'active_keys': active_keys,
            'total_requests': total_requests,
            'key_stats': key_stats,
            'period_days': days
        }
    
    @staticmethod
    def cleanup_expired_keys() -> int:
        """Clean up expired API keys"""
        from app.models import APIKey
        
        expired_keys = APIKey.query.filter(
            APIKey.expires_at < datetime.utcnow(),
            APIKey.is_active == True
        ).count()
        
        APIKey.query.filter(
            APIKey.expires_at < datetime.utcnow(),
            APIKey.is_active == True
        ).update({
            'is_active': False,
            'revoked_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        db.session.commit()
        return expired_keys


class JWTService:
    """JWT Token Service"""
    
    @staticmethod
    def generate_tokens(user_id: int, additional_claims: Dict[str, Any] = None) -> Dict[str, str]:
        """Generate JWT access and refresh tokens"""
        from flask_jwt_extended import create_access_token, create_refresh_token
        
        claims = additional_claims or {}
        claims['user_id'] = user_id
        
        access_token = create_access_token(
            identity=user_id,
            additional_claims=claims,
            expires_delta=timedelta(hours=1)
        )
        
        refresh_token = create_refresh_token(
            identity=user_id,
            expires_delta=timedelta(days=30)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600
        }
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        """Refresh access token from refresh token"""
        from flask_jwt_extended import create_access_token
        
        # This would need to be implemented with proper JWT refresh logic
        # For now, return None as placeholder
        return None
    
    @staticmethod
    def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return claims"""
        from flask_jwt_extended import decode_token
        
        try:
            claims = decode_token(token)
            return claims
        except Exception:
            return None
    
    @staticmethod
    def revoke_token(token: str) -> bool:
        """Revoke JWT token (add to blacklist)"""
        # This would need to be implemented with JWT blacklisting
        # For now, return True as placeholder
        return True
