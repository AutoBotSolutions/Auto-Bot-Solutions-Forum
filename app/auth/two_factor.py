"""
Two-Factor Authentication (2FA) Module

Handles TOTP (Time-based One-Time Password) generation,
verification, QR code generation, and backup code management
for the Auto Bot Solutions Forum.
"""

import secrets
import pyotp
import qrcode
import io
import base64
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class TwoFactorAuthService:
    """Service for managing Two-Factor Authentication"""
    
    def __init__(self):
        self.issuer = 'AutoBotSolutions Forum'
        self.key = None
        self.cipher = None
    
    def _get_config_value(self, key, default=None):
        """Get config value safely"""
        try:
            return current_app.config.get(key, default)
        except RuntimeError:
            # Outside application context, return default
            return default
    
    def _ensure_initialized(self):
        """Ensure service is initialized with current app context"""
        if self.cipher is None:
            self.issuer = self._get_config_value('TWO_FA_ISSUER', 'AutoBotSolutions Forum')
            self.key = self._get_encryption_key()
            self.cipher = Fernet(self.key)
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key for storing secrets"""
        key = self._get_config_value('TWO_FA_ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            logger.warning("No TWO_FA_ENCRYPTION_KEY configured, using generated key")
        if isinstance(key, str):
            key = key.encode()
        return key
    
    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, totp_secret: str) -> str:
        """
        Generate QR code for TOTP setup
        
        Args:
            user_email: User's email address
            totp_secret: TOTP secret key
            
        Returns:
            Base64 encoded QR code image
        """
        try:
            self._ensure_initialized()
            
            # Create TOTP URI
            totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
                name=user_email,
                issuer_name=self.issuer
            )
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
            
        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            raise
    
    def verify_totp(self, totp_secret: str, token: str, valid_window: int = 1) -> bool:
        """
        Verify TOTP token
        
        Args:
            totp_secret: TOTP secret key
            token: User-provided token
            valid_window: Number of time windows to check (default: 1)
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(totp_secret)
            return totp.verify(token, valid_window=valid_window)
        except Exception as e:
            logger.error(f"Error verifying TOTP token: {str(e)}")
            return False
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for 2FA
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(code)
        return codes
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            self._ensure_initialized()
            if isinstance(data, str):
                data = data.encode()
            encrypted = self.cipher.encrypt(data)
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            self._ensure_initialized()
            if isinstance(encrypted_data, str):
                encrypted_data = base64.b64decode(encrypted_data)
            decrypted = self.cipher.decrypt(encrypted_data)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            raise
    
    def hash_backup_code(self, code: str) -> str:
        """Hash backup code for storage"""
        import hashlib
        return hashlib.sha256(code.encode()).hexdigest()
    
    def verify_backup_code(self, stored_hash: str, provided_code: str) -> bool:
        """Verify backup code against stored hash"""
        try:
            return self.hash_backup_code(provided_code) == stored_hash
        except Exception as e:
            logger.error(f"Error verifying backup code: {str(e)}")
            return False

class BackupCodeManager:
    """Manager for backup codes"""
    
    def __init__(self):
        self.two_fa_service = TwoFactorAuthService()
    
    def store_backup_codes(self, user_id: int, codes: List[str]) -> List[Dict[str, str]]:
        """
        Store backup codes with their hashes
        
        Args:
            user_id: User ID
            codes: List of backup codes
            
        Returns:
            List of dictionaries with code info (without actual codes)
        """
        stored_codes = []
        for code in codes:
            code_hash = self.two_fa_service.hash_backup_code(code)
            stored_codes.append({
                'hash': code_hash,
                'used': False,
                'created_at': datetime.utcnow().isoformat()
            })
        
        # In a real implementation, these would be stored in the database
        # For now, we'll return the stored codes info
        return stored_codes
    
    def verify_and_use_backup_code(self, user_id: int, provided_code: str, stored_codes: List[Dict]) -> bool:
        """
        Verify and mark backup code as used
        
        Args:
            user_id: User ID
            provided_code: User-provided backup code
            stored_codes: List of stored backup code info
            
        Returns:
            True if code is valid and marked as used, False otherwise
        """
        for code_info in stored_codes:
            if not code_info['used']:
                if self.two_fa_service.verify_backup_code(code_info['hash'], provided_code):
                    # Mark as used (in real implementation, update database)
                    code_info['used'] = True
                    code_info['used_at'] = datetime.utcnow().isoformat()
                    return True
        return False
    
    def get_unused_backup_codes_count(self, stored_codes: List[Dict]) -> int:
        """Get count of unused backup codes"""
        return sum(1 for code in stored_codes if not code['used'])

# Global service instances (will be initialized lazily)
two_fa_service = TwoFactorAuthService()
backup_code_manager = BackupCodeManager()

# Helper functions for 2FA
def generate_totp_setup_data(user_email: str) -> Dict[str, str]:
    """
    Generate complete TOTP setup data for user
    
    Args:
        user_email: User's email address
        
    Returns:
        Dictionary with TOTP setup data
    """
    try:
        # Generate secret
        secret = two_fa_service.generate_totp_secret()
        
        # Generate QR code
        qr_code = two_fa_service.generate_qr_code(user_email, secret)
        
        # Generate backup codes
        backup_codes = two_fa_service.generate_backup_codes()
        
        return {
            'secret': secret,
            'qr_code': qr_code,
            'backup_codes': backup_codes,
            'issuer': two_fa_service.issuer
        }
    except Exception as e:
        logger.error(f"Error generating TOTP setup data: {str(e)}")
        raise

def verify_2fa_token(secret: str, token: str) -> bool:
    """
    Verify 2FA token
    
    Args:
        secret: TOTP secret
        token: User-provided token
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        return two_fa_service.verify_totp(secret, token)
    except Exception as e:
        logger.error(f"Error verifying 2FA token: {str(e)}")
        return False

def format_backup_codes_for_display(codes: List[str]) -> str:
    """
    Format backup codes for display
    
    Args:
        codes: List of backup codes
        
    Returns:
        Formatted string of backup codes
    """
    formatted_codes = []
    for i, code in enumerate(codes, 1):
        formatted_codes.append(f"{i}. {code}")
    return "\n".join(formatted_codes)

# Import datetime for backup code management
from datetime import datetime
