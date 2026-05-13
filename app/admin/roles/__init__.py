"""
Advanced User Role Management Package

This package contains all advanced user role management functionality including:
- Advanced role system
- Role-based permissions
- Role hierarchy
- Role assignment workflows
- Role analytics
"""

from .models import (
    Role, Permission, RolePermission, UserRole, RoleAssignment, 
    RoleWorkflow, RoleAnalytics, RoleHierarchy
)

from .forms import (
    RoleForm, PermissionForm, RolePermissionForm, AssignRoleForm, RemoveRoleForm,
    RoleRequestForm, RoleApprovalForm, RoleWorkflowForm, RoleHierarchyForm,
    UserSearchForm, RoleAnalyticsForm, BulkRoleAssignmentForm, BulkRoleRemovalForm,
    RoleTemplateForm, RoleImportForm, RoleExportForm, RoleSettingsForm,
    RoleAuditForm, PermissionCheckForm, RoleComparisonForm
)

from .routes import roles_bp

__all__ = [
    # Models
    'Role', 'Permission', 'RolePermission', 'UserRole', 'RoleAssignment', 
    'RoleWorkflow', 'RoleAnalytics', 'RoleHierarchy',
    
    # Forms
    'RoleForm', 'PermissionForm', 'RolePermissionForm', 'AssignRoleForm', 'RemoveRoleForm',
    'RoleRequestForm', 'RoleApprovalForm', 'RoleWorkflowForm', 'RoleHierarchyForm',
    'UserSearchForm', 'RoleAnalyticsForm', 'BulkRoleAssignmentForm', 'BulkRoleRemovalForm',
    'RoleTemplateForm', 'RoleImportForm', 'RoleExportForm', 'RoleSettingsForm',
    'RoleAuditForm', 'PermissionCheckForm', 'RoleComparisonForm',
    
    # Blueprint
    'roles_bp'
]
