"""
Social Login Forms

Forms for social login management and account linking
for the Auto Bot Solutions Forum.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional
from flask import current_app
from app.auth.social_config import get_provider_config, get_available_providers

class SocialLoginForm(FlaskForm):
    """Form for social login selection"""
    provider = SelectField('Social Login Provider', 
                          choices=[('google', 'Google'), ('github', 'GitHub')],
                          validators=[DataRequired(message='Please select a provider')])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update choices with available providers
        self.provider.choices = []
        for provider in get_available_providers():
            config = get_provider_config(provider)
            self.provider.choices.append((provider, config.get('name', provider.title())))

class LinkSocialAccountForm(FlaskForm):
    """Form for linking social account to existing user"""
    provider = SelectField('Provider', 
                          choices=[('google', 'Google'), ('github', 'GitHub')],
                          validators=[DataRequired(message='Please select a provider')])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update choices with available providers
        self.provider.choices = []
        for provider in get_available_providers():
            config = get_provider_config(provider)
            self.provider.choices.append((provider, config.get('name', provider.title())))

class SocialAccountSettingsForm(FlaskForm):
    """Form for social account settings"""
    # This form is primarily for display and confirmation
    pass

class SocialProfileImportForm(FlaskForm):
    """Form for importing profile data from social accounts"""
    import_avatar = BooleanField('Import Avatar', default=True)
    import_bio = BooleanField('Import Bio', default=True)
    import_name = BooleanField('Import Name', default=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class SocialConflictResolutionForm(FlaskForm):
    """Form for resolving social login conflicts"""
    action = SelectField('Action', 
                         choices=[
                             ('link', 'Link to existing account'),
                             ('create', 'Create new account'),
                             ('cancel', 'Cancel')
                         ],
                         validators=[DataRequired(message='Please choose an action')])
    
    email = StringField('Email Address', 
                       validators=[DataRequired(), Email(), Length(max=120)],
                       description='Enter email to link to existing account')
    
    password = StringField('Password', 
                          validators=[Optional(), Length(min=6, max=128)],
                          description='Enter password to verify account ownership')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def validate_email(self, field):
        """Validate email exists in system"""
        from app.models import User
        if self.action.data == 'link':
            user = User.query.filter_by(email=field.data).first()
            if not user:
                raise ValidationError('No account found with this email address')
    
    def validate_password(self, field):
        """Validate password if linking to existing account"""
        from app.models import User
        if self.action.data == 'link' and field.data:
            user = User.query.filter_by(email=self.email.data).first()
            if user and not user.check_password(field.data):
                raise ValidationError('Invalid password for this account')

class SocialAccountUnlinkForm(FlaskForm):
    """Form for unlinking social account"""
    confirm = BooleanField('I understand that unlinking will remove access to this social account',
                           validators=[DataRequired(message='You must confirm to unlink the account')])
    
    password = StringField('Password', 
                          validators=[DataRequired(), Length(min=6, max=128)],
                          description='Enter your password to confirm unlinking')
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def validate_password(self, field):
        """Validate user password"""
        if not self.user.check_password(field.data):
            raise ValidationError('Invalid password')

class SocialAccountPreferencesForm(FlaskForm):
    """Form for social account preferences"""
    auto_login = BooleanField('Use this account for automatic login', default=False)
    profile_sync = BooleanField('Sync profile information', default=True)
    email_notifications = BooleanField('Receive email notifications', default=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
