from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, BooleanField, SelectField, IntegerField, DateTimeField, FieldList, FormField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange, Regexp

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Description')
    color = StringField('Color (Hex)', validators=[Length(min=7, max=7)], default='#00f5ff')
    submit = SubmitField('Create Category')

class BadgeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Description')
    icon = StringField('Icon', validators=[Length(max=32)], default='★')
    color = StringField('Color (Hex)', validators=[Length(min=7, max=7)], default='#ff00ff')
    submit = SubmitField('Create Badge')

class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    is_admin = BooleanField('Admin Privileges')
    is_active = BooleanField('Account Active')
    is_verified = BooleanField('Email Verified')
    bio = TextAreaField('Bio')
    location = StringField('Location', validators=[Optional(), Length(max=128)])
    website = StringField('Website', validators=[Optional(), Length(max=256)])
    change_password = BooleanField('Change Password')
    password = PasswordField('New Password', validators=[Optional(), Length(min=6, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[
        Optional(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Update User')

class UserSuspendForm(FlaskForm):
    reason = TextAreaField('Suspension Reason', validators=[DataRequired()])
    duration_days = StringField('Duration (days)', validators=[Optional()], 
                               description='Leave empty for indefinite suspension')
    submit = SubmitField('Suspend User')

class UserBanForm(FlaskForm):
    reason = TextAreaField('Ban Reason', validators=[DataRequired()])
    submit = SubmitField('Ban User')

class UserBulkActionForm(FlaskForm):
    action = StringField('Action', validators=[DataRequired()])
    user_ids = StringField('User IDs', validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[Optional()])
    submit = SubmitField('Execute Bulk Action')


# Role and Permission Management Forms

class PermissionForm(FlaskForm):
    """Form for creating and editing permissions"""
    name = StringField('Permission Name', validators=[
        DataRequired(),
        Length(min=3, max=100),
        Regexp(r'^[a-z0-9_:]+$', message='Only lowercase letters, numbers, underscores, and colons allowed')
    ])
    display_name = StringField('Display Name', validators=[
        DataRequired(),
        Length(min=3, max=150)
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    category = SelectField('Category', choices=[
        ('users', 'User Management'),
        ('roles', 'Role Management'),
        ('groups', 'Group Management'),
        ('content', 'Content Management'),
        ('analytics', 'Analytics'),
        ('system', 'System'),
        ('security', 'Security')
    ], validators=[DataRequired()])
    resource = StringField('Resource', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    action = StringField('Action', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Permission')


class RoleForm(FlaskForm):
    """Form for creating and editing roles"""
    name = StringField('Role Name', validators=[
        DataRequired(),
        Length(min=3, max=100),
        Regexp(r'^[a-z0-9_]+$', message='Only lowercase letters, numbers, and underscores allowed')
    ])
    display_name = StringField('Display Name', validators=[
        DataRequired(),
        Length(min=3, max=150)
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    level = IntegerField('Level', validators=[
        DataRequired(),
        NumberRange(min=0, max=100)
    ], default=0)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Role')


class RolePermissionForm(FlaskForm):
    """Form for managing role permissions"""
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    permission_ids = SelectMultipleField('Permissions', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update Permissions')


class UserRoleForm(FlaskForm):
    """Form for assigning roles to users"""
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    expires_at = DateTimeField('Expires At', validators=[Optional()], 
                              format='%Y-%m-%d %H:%M',
                              description='Leave empty for permanent assignment')
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Assign Role')


class UserRoleBulkForm(FlaskForm):
    """Form for bulk role assignments"""
    user_ids = HiddenField('User IDs', validators=[DataRequired()])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    expires_at = DateTimeField('Expires At', validators=[Optional()], 
                              format='%Y-%m-%d %H:%M',
                              description='Leave empty for permanent assignment')
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Bulk Assign Role')


class UserGroupForm(FlaskForm):
    """Form for creating and editing user groups"""
    name = StringField('Group Name', validators=[
        DataRequired(),
        Length(min=3, max=100),
        Regexp(r'^[a-z0-9_]+$', message='Only lowercase letters, numbers, and underscores allowed')
    ])
    display_name = StringField('Display Name', validators=[
        DataRequired(),
        Length(min=3, max=150)
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    max_members = IntegerField('Maximum Members', validators=[
        Optional(),
        NumberRange(min=1)
    ], description='Leave empty for unlimited')
    auto_assign = BooleanField('Auto-assign New Users', default=False)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Group')


class UserGroupMemberForm(FlaskForm):
    """Form for managing group members"""
    group_id = SelectField('Group', coerce=int, validators=[DataRequired()])
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add to Group')


class UserGroupBulkForm(FlaskForm):
    """Form for bulk group membership"""
    user_ids = HiddenField('User IDs', validators=[DataRequired()])
    group_id = SelectField('Group', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Bulk Add to Group')


class GroupRoleForm(FlaskForm):
    """Form for assigning roles to groups"""
    group_id = SelectField('Group', coerce=int, validators=[DataRequired()])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Role to Group')


class SecurityEventForm(FlaskForm):
    """Form for creating security events"""
    event_type = SelectField('Event Type', choices=[
        ('login_attempt', 'Login Attempt'),
        ('login_failed', 'Login Failed'),
        ('permission_denied', 'Permission Denied'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('security_breach', 'Security Breach'),
        ('data_access', 'Data Access'),
        ('system_change', 'System Change'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    severity = SelectField('Severity', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], validators=[DataRequired()])
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=3, max=200)
    ])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=1000)])
    user_id = SelectField('User', coerce=int, validators=[Optional()])
    ip_address = StringField('IP Address', validators=[Optional(), Length(max=45)])
    resource = StringField('Resource', validators=[Optional(), Length(max=100)])
    action = StringField('Action', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Create Security Event')


class SecurityEventFilterForm(FlaskForm):
    """Form for filtering security events"""
    event_type = SelectField('Event Type', choices=[
        ('', 'All Types'),
        ('login_attempt', 'Login Attempt'),
        ('login_failed', 'Login Failed'),
        ('permission_denied', 'Permission Denied'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('security_breach', 'Security Breach'),
        ('data_access', 'Data Access'),
        ('system_change', 'System Change'),
        ('other', 'Other')
    ], filters=[lambda x: x or None])
    severity = SelectField('Severity', choices=[
        ('', 'All Severities'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], filters=[lambda x: x or None])
    resolved = SelectField('Status', choices=[
        ('', 'All'),
        ('true', 'Resolved'),
        ('false', 'Unresolved')
    ], filters=[lambda x: x or None])
    user_id = SelectField('User', coerce=int, filters=[lambda x: x or None])
    start_date = DateTimeField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateTimeField('End Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Filter Events')


class UserPermissionCheckForm(FlaskForm):
    """Form for checking user permissions"""
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    resource = StringField('Resource', validators=[DataRequired(), Length(min=2, max=100)])
    action = StringField('Action', validators=[DataRequired(), Length(min=2, max=50)])
    submit = SubmitField('Check Permission')


class AccessLogFilterForm(FlaskForm):
    """Form for filtering access logs"""
    user_id = SelectField('User', coerce=int, filters=[lambda x: x or None])
    resource = StringField('Resource', validators=[Optional(), Length(max=100)])
    action = StringField('Action', validators=[Optional(), Length(max=50)])
    granted = SelectField('Access Granted', choices=[
        ('', 'All'),
        ('true', 'Granted'),
        ('false', 'Denied')
    ], filters=[lambda x: x or None])
    start_date = DateTimeField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateTimeField('End Date', format='%Y-%m-%d', validators=[Optional()])
    ip_address = StringField('IP Address', validators=[Optional(), Length(max=45)])
    submit = SubmitField('Filter Logs')


class BulkUserManagementForm(FlaskForm):
    """Form for bulk user management operations"""
    user_ids = HiddenField('User IDs', validators=[DataRequired()])
    action = SelectField('Action', choices=[
        ('assign_role', 'Assign Role'),
        ('revoke_role', 'Revoke Role'),
        ('add_to_group', 'Add to Group'),
        ('remove_from_group', 'Remove from Group'),
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('suspend', 'Suspend'),
        ('delete', 'Delete')
    ], validators=[DataRequired()])
    role_id = SelectField('Role', coerce=int, validators=[Optional()])
    group_id = SelectField('Group', coerce=int, validators=[Optional()])
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Execute Bulk Action')
