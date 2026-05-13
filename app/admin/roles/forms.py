"""
Advanced User Role Management Forms

This module contains forms for advanced user role management including:
- Role creation and editing forms
- Permission management forms
- Role assignment forms
- Role workflow forms
- Role analytics forms
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField, IntegerField, DateField, HiddenField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email
from app.models import User


class RoleForm(FlaskForm):
    """Form for creating and editing roles"""
    name = StringField('Role Name', validators=[DataRequired(), Length(min=2, max=100)])
    display_name = StringField('Display Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    color = StringField('Color', validators=[Optional(), Length(min=7, max=7)])
    icon = StringField('Icon', validators=[Optional(), Length(max=50)])
    level = IntegerField('Hierarchy Level', validators=[Optional(), NumberRange(min=0)])
    is_active = BooleanField('Active Role')
    is_admin_role = BooleanField('Administrative Role')
    
    submit = SubmitField('Save Role')


class PermissionForm(FlaskForm):
    """Form for creating and editing permissions"""
    name = StringField('Permission Name', validators=[DataRequired(), Length(min=2, max=100)])
    display_name = StringField('Display Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    category = SelectField('Category', choices=[
        ('content', 'Content Management'),
        ('user', 'User Management'),
        ('admin', 'Administration'),
        ('system', 'System'),
        ('moderation', 'Moderation'),
        ('analytics', 'Analytics')
    ], validators=[DataRequired()])
    
    resource = SelectField('Resource', choices=[
        ('posts', 'Posts'),
        ('comments', 'Comments'),
        ('users', 'Users'),
        ('roles', 'Roles'),
        ('permissions', 'Permissions'),
        ('categories', 'Categories'),
        ('analytics', 'Analytics'),
        ('settings', 'Settings'),
        ('reports', 'Reports')
    ], validators=[DataRequired()])
    
    action = SelectField('Action', choices=[
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('manage', 'Manage'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('assign', 'Assign'),
        ('revoke', 'Revoke'),
        ('export', 'Export'),
        ('import', 'Import')
    ], validators=[DataRequired()])
    
    is_active = BooleanField('Active Permission')
    
    submit = SubmitField('Save Permission')


class RolePermissionForm(FlaskForm):
    """Form for managing role permissions"""
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    permission_id = SelectField('Permission', coerce=int, validators=[DataRequired()])
    granted = BooleanField('Grant Permission')
    
    submit = SubmitField('Update Permission')


class AssignRoleForm(FlaskForm):
    """Form for assigning roles to users"""
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    expires_at = DateField('Expires At', validators=[Optional()])
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Assign Role')


class RemoveRoleForm(FlaskForm):
    """Form for removing roles from users"""
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Remove Role')


class RoleRequestForm(FlaskForm):
    """Form for requesting roles"""
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[DataRequired(), Length(min=10, max=1000)])
    
    submit = SubmitField('Request Role')


class RoleApprovalForm(FlaskForm):
    """Form for approving/denying role requests"""
    request_id = HiddenField('Request ID', validators=[DataRequired()])
    action = SelectField('Action', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ], validators=[DataRequired()])
    
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=500)])
    expires_at = DateField('Expires At', validators=[Optional()])
    
    submit = SubmitField('Process Request')


class RoleWorkflowForm(FlaskForm):
    """Form for creating and editing role workflows"""
    name = StringField('Workflow Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    workflow_type = SelectField('Workflow Type', choices=[
        ('self_assign', 'Self Assignment'),
        ('manager_assign', 'Manager Assignment'),
        ('admin_assign', 'Admin Assignment'),
        ('auto_assign', 'Automatic Assignment')
    ], validators=[DataRequired()])
    
    is_active = BooleanField('Active Workflow')
    requires_approval = BooleanField('Requires Approval')
    auto_assign = BooleanField('Auto Assign')
    
    # Approval roles (multiple selection)
    approval_roles = SelectField('Approval Roles', choices=[], coerce=int)
    
    # Conditions
    min_registration_days = IntegerField('Minimum Registration Days', validators=[Optional(), NumberRange(min=1)])
    min_posts = IntegerField('Minimum Posts', validators=[Optional(), NumberRange(min=0)])
    require_active_account = BooleanField('Require Active Account')
    require_verified_email = BooleanField('Require Verified Email')
    
    submit = SubmitField('Save Workflow')


class RoleHierarchyForm(FlaskForm):
    """Form for managing role hierarchy"""
    parent_role_id = SelectField('Parent Role', coerce=int, validators=[DataRequired()])
    child_role_id = SelectField('Child Role', coerce=int, validators=[DataRequired()])
    relationship_type = SelectField('Relationship Type', choices=[
        ('inherits', 'Inherits'),
        ('manages', 'Manages'),
        ('oversees', 'Oversees')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Create Hierarchy')


class UserSearchForm(FlaskForm):
    """Form for searching users for role assignment"""
    search_term = StringField('Search Users', validators=[Optional(), Length(max=100)])
    search_type = SelectField('Search Type', choices=[
        ('username', 'Username'),
        ('email', 'Email'),
        ('role', 'Current Role'),
        ('activity', 'Activity Level')
    ], validators=[DataRequired()])
    
    current_role = SelectField('Current Role', choices=[], coerce=int)
    include_inactive = BooleanField('Include Inactive Users')
    
    submit = SubmitField('Search Users')


class RoleAnalyticsForm(FlaskForm):
    """Form for role analytics"""
    role_id = SelectField('Role', choices=[], coerce=int, validators=[DataRequired()])
    date_range = SelectField('Date Range', choices=[
        ('7', 'Last 7 Days'),
        ('30', 'Last 30 Days'),
        ('90', 'Last 90 Days'),
        ('365', 'Last Year')
    ], validators=[DataRequired()])
    
    analytics_type = SelectField('Analytics Type', choices=[
        ('overview', 'Overview'),
        ('assignments', 'Assignments'),
        ('requests', 'Requests'),
        ('trends', 'Trends')
    ], validators=[DataRequired()])
    
    export_format = SelectField('Export Format', choices=[
        ('none', 'No Export'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('pdf', 'PDF')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Generate Analytics')


class BulkRoleAssignmentForm(FlaskForm):
    """Form for bulk role assignments"""
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    user_ids = HiddenField('User IDs', validators=[DataRequired()])
    expires_at = DateField('Expires At', validators=[Optional()])
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Assign Roles')


class BulkRoleRemovalForm(FlaskForm):
    """Form for bulk role removals"""
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    user_ids = HiddenField('User IDs', validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Remove Roles')


class RoleTemplateForm(FlaskForm):
    """Form for creating role templates"""
    template_name = StringField('Template Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    
    # Template permissions
    permissions = FieldList(FormField(PermissionForm), min_entries=0)
    
    submit = SubmitField('Create Template')


class RoleImportForm(FlaskForm):
    """Form for importing roles"""
    import_file = StringField('Import File Path', validators=[Optional(), Length(max=500)])
    import_data = TextAreaField('Import Data (JSON)', validators=[Optional()])
    overwrite_existing = BooleanField('Overwrite Existing Roles')
    
    submit = SubmitField('Import Roles')


class RoleExportForm(FlaskForm):
    """Form for exporting roles"""
    export_format = SelectField('Export Format', choices=[
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xlsx', 'Excel')
    ], validators=[DataRequired()])
    
    include_permissions = BooleanField('Include Permissions')
    include_users = BooleanField('Include Users')
    include_workflows = BooleanField('Include Workflows')
    include_analytics = BooleanField('Include Analytics')
    
    submit = SubmitField('Export Roles')


class RoleSettingsForm(FlaskForm):
    """Form for role system settings"""
    enable_role_requests = BooleanField('Enable Role Requests')
    require_reason_for_requests = BooleanField('Require Reason for Requests')
    auto_approve_low_risk_roles = BooleanField('Auto Approve Low Risk Roles')
    max_roles_per_user = IntegerField('Maximum Roles Per User', validators=[Optional(), NumberRange(min=1)])
    default_role_expiration_days = IntegerField('Default Role Expiration Days', validators=[Optional(), NumberRange(min=1)])
    
    enable_role_hierarchy = BooleanField('Enable Role Hierarchy')
    allow_role_inheritance = BooleanField('Allow Role Inheritance')
    require_highest_role_for_actions = BooleanField('Require Highest Role for Actions')
    
    enable_analytics = BooleanField('Enable Role Analytics')
    analytics_retention_days = IntegerField('Analytics Retention Days', validators=[Optional(), NumberRange(min=30)])
    
    submit = SubmitField('Save Settings')


class RoleAuditForm(FlaskForm):
    """Form for role audit logs"""
    role_id = SelectField('Role', choices=[], coerce=int)
    user_id = SelectField('User', choices=[], coerce=int)
    action_type = SelectField('Action Type', choices=[
        ('all', 'All Actions'),
        ('assignment', 'Assignments'),
        ('removal', 'Removals'),
        ('request', 'Requests'),
        ('approval', 'Approvals'),
        ('rejection', 'Rejections')
    ], validators=[DataRequired()])
    
    date_range = SelectField('Date Range', choices=[
        ('7', 'Last 7 Days'),
        ('30', 'Last 30 Days'),
        ('90', 'Last 90 Days'),
        ('365', 'Last Year')
    ], validators=[DataRequired()])
    
    submit = SubmitField('View Audit Log')


class PermissionCheckForm(FlaskForm):
    """Form for checking user permissions"""
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    permission = StringField('Permission', validators=[DataRequired(), Length(max=100)])
    
    submit = SubmitField('Check Permission')


class RoleComparisonForm(FlaskForm):
    """Form for comparing roles"""
    role1_id = SelectField('Role 1', coerce=int, validators=[DataRequired()])
    role2_id = SelectField('Role 2', coerce=int, validators=[DataRequired()])
    comparison_type = SelectField('Comparison Type', choices=[
        ('permissions', 'Permissions'),
        ('users', 'Users'),
        ('hierarchy', 'Hierarchy'),
        ('analytics', 'Analytics')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Compare Roles')
