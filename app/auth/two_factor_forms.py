"""
Two-Factor Authentication Forms

Forms for 2FA setup, verification, and management
for the Auto Bot Solutions Forum.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.auth.two_factor import verify_2fa_token

class TwoFactorSetupForm(FlaskForm):
    """Form for 2FA setup verification"""
    token = StringField('Authentication Code', validators=[
        DataRequired(message='Please enter the authentication code'),
        Length(min=6, max=6, message='Authentication code must be 6 digits')
    ])
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def validate_token(self, field):
        """Validate the 2FA token"""
        if self.user and self.user.get_totp_secret():
            if not verify_2fa_token(self.user.get_totp_secret(), field.data):
                raise ValidationError('Invalid authentication code. Please try again.')
        else:
            raise ValidationError('2FA not properly configured.')

class TwoFactorVerifyForm(FlaskForm):
    """Form for 2FA verification during login"""
    token = StringField('Authentication Code', validators=[
        DataRequired(message='Please enter the authentication code'),
        Length(min=6, max=6, message='Authentication code must be 6 digits')
    ])
    remember_device = BooleanField('Remember this device for 30 days')
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def validate_token(self, field):
        """Validate the 2FA token"""
        if self.user:
            # Try TOTP verification first
            if self.user.verify_2fa_token(field.data):
                return
            
            # Try backup code verification
            if self.user.verify_backup_code(field.data):
                return
            
            raise ValidationError('Invalid authentication code or backup code.')
        else:
            raise ValidationError('User not found.')

class TwoFactorBackupCodeForm(FlaskForm):
    """Form for using backup codes"""
    backup_code = StringField('Backup Code', validators=[
        DataRequired(message='Please enter a backup code'),
        Length(min=8, max=8, message='Backup code must be 8 characters')
    ])
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

class TwoFactorDisableForm(FlaskForm):
    """Form for disabling 2FA"""
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password'),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirmation = StringField('Type "DISABLE" to confirm', validators=[
        DataRequired(message='Please type DISABLE to confirm'),
        EqualTo('disable_confirmation', message='Please type DISABLE exactly as shown')
    ])
    disable_confirmation = HiddenField(default='DISABLE')
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def validate_password(self, field):
        """Validate the user's password"""
        if self.user and not self.user.check_password(field.data):
            raise ValidationError('Incorrect password.')

class TwoFactorRegenerateCodesForm(FlaskForm):
    """Form for regenerating backup codes"""
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password'),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def validate_password(self, field):
        """Validate the user's password"""
        if self.user and not self.user.check_password(field.data):
            raise ValidationError('Incorrect password.')
