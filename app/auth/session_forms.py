"""
Session Management Forms

Forms for session management and security settings
for the Auto Bot Solutions Forum.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, Email, ValidationError
from flask import current_app

class SessionManagementForm(FlaskForm):
    """Form for managing user sessions"""
    # This form is primarily for display and confirmation
    pass

class RevokeSessionForm(FlaskForm):
    """Form for revoking specific session"""
    session_id = StringField('Session ID', validators=[DataRequired()])
    confirm = BooleanField('Confirm session revocation', validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class RevokeAllSessionsForm(FlaskForm):
    """Form for revoking all user sessions"""
    confirm = BooleanField('Confirm revocation of all sessions', validators=[DataRequired()])
    current_session_only = BooleanField('Revoke all sessions except current', default=False)
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=500)])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class SessionPreferencesForm(FlaskForm):
    """Form for session preferences"""
    auto_revoke_inactive = BooleanField('Automatically revoke inactive sessions', default=True)
    inactive_timeout = IntegerField('Inactive session timeout (minutes)', 
                                 validators=[NumberRange(min=5, max=1440)],
                                 default=30)
    max_concurrent_sessions = IntegerField('Maximum concurrent sessions',
                                         validators=[NumberRange(min=1, max=10)],
                                         default=3)
    require_device_verification = BooleanField('Require verification for new devices', default=False)
    session_notifications = BooleanField('Email notifications for new sessions', default=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class SecuritySettingsForm(FlaskForm):
    """Form for security settings"""
    two_factor_required = BooleanField('Require two-factor authentication', default=False)
    ip_whitelist_enabled = BooleanField('Enable IP whitelist', default=False)
    ip_whitelist = TextAreaField('Allowed IP addresses (one per line)', 
                                validators=[Optional(), Length(max=1000)])
    email_alerts = BooleanField('Email alerts for security events', default=True)
    session_monitoring = BooleanField('Enable session monitoring', default=True)
    suspicious_activity_detection = BooleanField('Detect suspicious activity', default=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def validate_ip_whitelist(self, field):
        """Validate IP whitelist format"""
        if self.ip_whitelist_enabled.data and field.data:
            import ipaddress
            lines = field.data.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        ipaddress.ip_network(line, strict=False)
                    except ValueError:
                        raise ValidationError(f'Invalid IP address or network: {line}')

class DeviceTrustForm(FlaskForm):
    """Form for managing trusted devices"""
    device_id = StringField('Device ID', validators=[DataRequired()])
    device_name = StringField('Device Name', validators=[Optional(), Length(max=100)])
    is_trusted = BooleanField('Trust this device', default=True)
    expires_in_days = IntegerField('Trust duration (days)', 
                                 validators=[NumberRange(min=1, max=365)],
                                 default=30)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class SessionAnalyticsForm(FlaskForm):
    """Form for session analytics filtering"""
    date_range = SelectField('Date Range', 
                            choices=[
                                ('today', 'Today'),
                                ('week', 'Last 7 days'),
                                ('month', 'Last 30 days'),
                                ('quarter', 'Last 90 days'),
                                ('year', 'Last year')
                            ],
                            default='week')
    
    event_type = SelectField('Event Type',
                            choices=[
                                ('', 'All Events'),
                                ('login', 'Login'),
                                ('logout', 'Logout'),
                                ('suspicious_activity', 'Suspicious Activity'),
                                ('session_revoked', 'Session Revoked'),
                                ('all_sessions_revoked', 'All Sessions Revoked')
                            ])
    
    severity = SelectField('Severity',
                          choices=[
                              ('', 'All Severities'),
                              ('info', 'Info'),
                              ('warning', 'Warning'),
                              ('critical', 'Critical')
                          ])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class SecurityEventForm(FlaskForm):
    """Form for adding security events (admin use)"""
    event_type = SelectField('Event Type',
                            choices=[
                                ('login', 'Login'),
                                ('logout', 'Logout'),
                                ('suspicious_activity', 'Suspicious Activity'),
                                ('session_revoked', 'Session Revoked'),
                                ('all_sessions_revoked', 'All Sessions Revoked'),
                                ('account_locked', 'Account Locked'),
                                ('account_unlocked', 'Account Unlocked'),
                                ('password_changed', 'Password Changed'),
                                ('2fa_enabled', '2FA Enabled'),
                                ('2fa_disabled', '2FA Disabled')
                            ],
                            validators=[DataRequired()])
    
    severity = SelectField('Severity',
                          choices=[
                              ('info', 'Info'),
                              ('warning', 'Warning'),
                              ('critical', 'Critical')
                          ],
                          validators=[DataRequired()])
    
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=1000)])
    ip_address = StringField('IP Address', validators=[Optional(), Length(max=45)])
    user_agent = TextAreaField('User Agent', validators=[Optional(), Length(max=500)])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def validate_ip_address(self, field):
        """Validate IP address format"""
        if field.data:
            import ipaddress
            try:
                ipaddress.ip_address(field.data)
            except ValueError:
                raise ValidationError('Invalid IP address format')

class SessionExportForm(FlaskForm):
    """Form for exporting session data"""
    format = SelectField('Export Format',
                         choices=[
                             ('json', 'JSON'),
                             ('csv', 'CSV'),
                             ('pdf', 'PDF')
                         ],
                         default='json')
    
    include_sensitive = BooleanField('Include sensitive data', default=False)
    date_range = SelectField('Date Range',
                            choices=[
                                ('week', 'Last 7 days'),
                                ('month', 'Last 30 days'),
                                ('quarter', 'Last 90 days'),
                                ('year', 'Last year')
                            ],
                            default='month')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
