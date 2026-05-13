"""
Admin System Services

This module contains service classes for the admin system's role and permission management,
including role-based access control, user management, and security event tracking.
"""

from datetime import datetime, timedelta
from flask import current_app
from flask_login import current_user
from sqlalchemy import and_, or_, desc, func
from app import db
from .models import (
    Permission, AdminRole, RolePermission, UserGroup, UserGroupMember,
    UserRole, GroupRole, AccessLog
)
from app.security.models import SecurityEvent
from app.models import User


class PermissionService:
    """Service for managing permissions"""
    
    @staticmethod
    def create_permission(name, display_name, description, category, resource, action, is_system=False):
        """Create a new permission"""
        permission = Permission(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            resource=resource,
            action=action,
            is_system=is_system
        )
        
        db.session.add(permission)
        db.session.commit()
        return permission
    
    @staticmethod
    def get_permission_by_id(permission_id):
        """Get permission by ID"""
        return Permission.query.get(permission_id)
    
    @staticmethod
    def get_permission_by_name(name):
        """Get permission by name"""
        return Permission.query.filter_by(name=name).first()
    
    @staticmethod
    def get_permissions(category=None, resource=None, is_active=True):
        """Get permissions with optional filtering"""
        query = Permission.query
        
        if category:
            query = query.filter_by(category=category)
        
        if resource:
            query = query.filter_by(resource=resource)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        return query.order_by(Permission.category, Permission.resource, Permission.action).all()
    
    @staticmethod
    def update_permission(permission_id, **kwargs):
        """Update permission"""
        permission = Permission.query.get(permission_id)
        if not permission:
            return None
        
        for key, value in kwargs.items():
            if hasattr(permission, key):
                setattr(permission, key, value)
        
        permission.updated_at = datetime.utcnow()
        db.session.commit()
        return permission
    
    @staticmethod
    def delete_permission(permission_id):
        """Delete permission (soft delete by setting is_active=False)"""
        permission = Permission.query.get(permission_id)
        if not permission:
            return False
        
        permission.is_active = False
        permission.updated_at = datetime.utcnow()
        db.session.commit()
        return True


class RoleService:
    """Service for managing admin roles"""
    
    @staticmethod
    def create_role(name, display_name, description, level=0, is_system=False, created_by=None):
        """Create a new role"""
        role = AdminRole(
            name=name,
            display_name=display_name,
            description=description,
            level=level,
            is_system=is_system,
            created_by=created_by
        )
        
        db.session.add(role)
        db.session.commit()
        return role
    
    @staticmethod
    def get_role_by_id(role_id):
        """Get role by ID"""
        return AdminRole.query.get(role_id)
    
    @staticmethod
    def get_role_by_name(name):
        """Get role by name"""
        return AdminRole.query.filter_by(name=name).first()
    
    @staticmethod
    def get_roles(include_inactive=False):
        """Get all roles"""
        query = AdminRole.query
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        return query.order_by(desc(AdminRole.level), AdminRole.name).all()
    
    @staticmethod
    def update_role(role_id, **kwargs):
        """Update role"""
        role = AdminRole.query.get(role_id)
        if not role:
            return None
        
        # Prevent updating system roles unless explicitly allowed
        if role.is_system and not kwargs.get('allow_system_update', False):
            return None
        
        for key, value in kwargs.items():
            if hasattr(role, key) and key != 'is_system':
                setattr(role, key, value)
        
        role.updated_at = datetime.utcnow()
        db.session.commit()
        return role
    
    @staticmethod
    def delete_role(role_id):
        """Delete role (soft delete by setting is_active=False)"""
        role = AdminRole.query.get(role_id)
        if not role or role.is_system:
            return False
        
        role.is_active = False
        role.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    
    @staticmethod
    def grant_permission_to_role(role_id, permission_id, granted_by=None):
        """Grant permission to role"""
        # Check if already granted
        existing = RolePermission.query.filter_by(
            role_id=role_id,
            permission_id=permission_id
        ).first()
        
        if existing:
            return existing
        
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
            granted_by=granted_by
        )
        
        db.session.add(role_permission)
        db.session.commit()
        return role_permission
    
    @staticmethod
    def revoke_permission_from_role(role_id, permission_id):
        """Revoke permission from role"""
        role_permission = RolePermission.query.filter_by(
            role_id=role_id,
            permission_id=permission_id
        ).first()
        
        if role_permission:
            db.session.delete(role_permission)
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def get_role_permissions(role_id):
        """Get all permissions for a role"""
        return Permission.query.join(RolePermission).filter(
            RolePermission.role_id == role_id,
            Permission.is_active == True
        ).all()


class UserGroupService:
    """Service for managing user groups"""
    
    @staticmethod
    def create_group(name, display_name, description, max_members=None, auto_assign=False, created_by=None):
        """Create a new user group"""
        group = UserGroup(
            name=name,
            display_name=display_name,
            description=description,
            max_members=max_members,
            auto_assign=auto_assign,
            created_by=created_by
        )
        
        db.session.add(group)
        db.session.commit()
        return group
    
    @staticmethod
    def get_group_by_id(group_id):
        """Get group by ID"""
        return UserGroup.query.get(group_id)
    
    @staticmethod
    def get_group_by_name(name):
        """Get group by name"""
        return UserGroup.query.filter_by(name=name).first()
    
    @staticmethod
    def get_groups(include_inactive=False):
        """Get all groups"""
        query = UserGroup.query
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        return query.order_by(UserGroup.name).all()
    
    @staticmethod
    def update_group(group_id, **kwargs):
        """Update group"""
        group = UserGroup.query.get(group_id)
        if not group:
            return None
        
        # Prevent updating system groups unless explicitly allowed
        if group.is_system and not kwargs.get('allow_system_update', False):
            return None
        
        for key, value in kwargs.items():
            if hasattr(group, key) and key != 'is_system':
                setattr(group, key, value)
        
        group.updated_at = datetime.utcnow()
        db.session.commit()
        return group
    
    @staticmethod
    def delete_group(group_id):
        """Delete group (soft delete by setting is_active=False)"""
        group = UserGroup.query.get(group_id)
        if not group or group.is_system:
            return False
        
        group.is_active = False
        group.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    
    @staticmethod
    def add_user_to_group(group_id, user_id, added_by=None):
        """Add user to group"""
        group = UserGroup.query.get(group_id)
        if not group:
            return None
        
        return group.add_user(user_id, added_by)
    
    @staticmethod
    def remove_user_from_group(group_id, user_id, removed_by=None):
        """Remove user from group"""
        group = UserGroup.query.get(group_id)
        if not group:
            return None
        
        return group.remove_user(user_id, removed_by)
    
    @staticmethod
    def get_group_members(group_id, include_inactive=False):
        """Get group members"""
        query = UserGroupMember.query.filter_by(group_id=group_id)
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        return query.order_by(UserGroupMember.added_at).all()
    
    @staticmethod
    def get_user_groups(user_id, include_inactive=False):
        """Get user's groups"""
        query = UserGroupMember.query.filter_by(user_id=user_id)
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        return query.join(UserGroup).filter(
            UserGroup.is_active == True
        ).all()


class UserRoleService:
    """Service for managing user role assignments"""
    
    @staticmethod
    def assign_role_to_user(user_id, role_id, assigned_by=None, expires_at=None, reason=None):
        """Assign role to user"""
        # Check if already assigned
        existing = UserRole.query.filter_by(
            user_id=user_id,
            role_id=role_id
        ).first()
        
        if existing:
            if not existing.is_active:
                # Reactivate existing assignment
                existing.is_active = True
                existing.assigned_at = datetime.utcnow()
                existing.assigned_by = assigned_by
                existing.expires_at = expires_at
                existing.revoked_at = None
                existing.revoked_by = None
                existing.reason = reason
                db.session.commit()
                return existing
            return existing  # Already active
        
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at,
            reason=reason
        )
        
        db.session.add(user_role)
        db.session.commit()
        return user_role
    
    @staticmethod
    def revoke_role_from_user(user_id, role_id, revoked_by=None, reason=None):
        """Revoke role from user"""
        user_role = UserRole.query.filter_by(
            user_id=user_id,
            role_id=role_id,
            is_active=True
        ).first()
        
        if user_role:
            user_role.is_active = False
            user_role.revoked_at = datetime.utcnow()
            user_role.revoked_by = revoked_by
            user_role.reason = reason
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def get_user_roles(user_id, include_inactive=False, include_expired=False):
        """Get user's roles"""
        query = UserRole.query.filter_by(user_id=user_id)
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        roles = query.join(AdminRole).filter(
            AdminRole.is_active == True
        ).all()
        
        if not include_expired:
            # Filter out expired roles
            roles = [ur for ur in roles if not ur.is_expired()]
        
        return roles
    
    @staticmethod
    def get_role_users(role_id, include_inactive=False, include_expired=False):
        """Get users with specific role"""
        query = UserRole.query.filter_by(role_id=role_id)
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        user_roles = query.join(User).all()
        
        if not include_expired:
            # Filter out expired roles
            user_roles = [ur for ur in user_roles if not ur.is_expired()]
        
        return user_roles


class AccessControlService:
    """Service for access control and permission checking"""
    
    @staticmethod
    def user_has_permission(user_id, permission_name):
        """Check if user has specific permission"""
        # Get user's active, non-expired roles
        user_roles = UserRoleService.get_user_roles(user_id)
        
        for user_role in user_roles:
            if user_role.role.has_permission(permission_name):
                return True
        
        return False
    
    @staticmethod
    def user_has_permission_on_resource(user_id, resource, action):
        """Check if user has permission for specific resource and action"""
        permission_name = f"{resource}:{action}"
        return AccessControlService.user_has_permission(user_id, permission_name)
    
    @staticmethod
    def user_has_role(user_id, role_name):
        """Check if user has specific role"""
        user_roles = UserRoleService.get_user_roles(user_id)
        return any(ur.role.name == role_name for ur in user_roles)
    
    @staticmethod
    def user_has_any_role(user_id, role_names):
        """Check if user has any of the specified roles"""
        user_roles = UserRoleService.get_user_roles(user_id)
        user_role_names = {ur.role.name for ur in user_roles}
        return any(role_name in user_role_names for role_name in role_names)
    
    @staticmethod
    def get_user_permissions(user_id):
        """Get all permissions for a user"""
        user_roles = UserRoleService.get_user_roles(user_id)
        permissions = set()
        
        for user_role in user_roles:
            role_permissions = RoleService.get_role_permissions(user_role.role_id)
            permissions.update(rp.name for rp in role_permissions)
        
        # Also get permissions from user's groups
        user_groups = UserGroupService.get_user_groups(user_id)
        for group_member in user_groups:
            group_roles = GroupRole.query.filter_by(
                group_id=group_member.group_id,
                is_active=True
            ).all()
            
            for group_role in group_roles:
                role_permissions = RoleService.get_role_permissions(group_role.role_id)
                permissions.update(rp.name for rp in role_permissions)
        
        return list(permissions)
    
    @staticmethod
    def check_access(user_id, resource, action, ip_address=None, user_agent=None, session_id=None):
        """Check access and log the attempt"""
        permission_name = f"{resource}:{action}"
        granted = AccessControlService.user_has_permission(user_id, permission_name)
        
        # Log the access attempt
        access_log = AccessLog(
            user_id=user_id,
            resource=resource,
            action=action,
            granted=granted,
            reason=f"Permission {'granted' if granted else 'denied'}: {permission_name}",
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
        
        db.session.add(access_log)
        db.session.commit()
        
        return granted
    
    @staticmethod
    def require_permission(permission_name):
        """Decorator to require specific permission"""
        def decorator(f):
            def decorated_function(*args, **kwargs):
                if not current_user.is_authenticated:
                    abort(403)
                
                if not AccessControlService.user_has_permission(current_user.id, permission_name):
                    abort(403)
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def require_role(role_name):
        """Decorator to require specific role"""
        def decorator(f):
            def decorated_function(*args, **kwargs):
                if not current_user.is_authenticated:
                    abort(403)
                
                if not AccessControlService.user_has_role(current_user.id, role_name):
                    abort(403)
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def require_any_role(role_names):
        """Decorator to require any of the specified roles"""
        def decorator(f):
            def decorated_function(*args, **kwargs):
                if not current_user.is_authenticated:
                    abort(403)
                
                if not AccessControlService.user_has_any_role(current_user.id, role_names):
                    abort(403)
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator


class SecurityEventService:
    """Service for managing security events"""
    
    @staticmethod
    def create_security_event(event_type, severity, title, description, user_id=None, 
                            ip_address=None, user_agent=None, resource=None, action=None, details=None):
        """Create a security event"""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            title=title,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            details=details or {}
        )
        
        db.session.add(event)
        db.session.commit()
        return event
    
    @staticmethod
    def get_security_events(event_type=None, severity=None, resolved=None, user_id=None, 
                          start_date=None, end_date=None, limit=None):
        """Get security events with filtering"""
        query = SecurityEvent.query
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        if severity:
            query = query.filter_by(severity=severity)
        
        if resolved is not None:
            query = query.filter_by(resolved=resolved)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(SecurityEvent.created_at >= start_date)
        
        if end_date:
            query = query.filter(SecurityEvent.created_at <= end_date)
        
        query = query.order_by(desc(SecurityEvent.created_at))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def resolve_security_event(event_id, resolved_by):
        """Resolve a security event"""
        event = SecurityEvent.query.get(event_id)
        if not event:
            return False
        
        event.resolved = True
        event.resolved_at = datetime.utcnow()
        event.resolved_by = resolved_by
        
        db.session.commit()
        return True
    
    @staticmethod
    def get_security_stats(days=30):
        """Get security event statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total events
        total_events = SecurityEvent.query.filter(
            SecurityEvent.created_at >= start_date
        ).count()
        
        # Events by severity
        severity_stats = db.session.query(
            SecurityEvent.severity,
            func.count(SecurityEvent.id)
        ).filter(
            SecurityEvent.created_at >= start_date
        ).group_by(SecurityEvent.severity).all()
        
        # Events by type
        type_stats = db.session.query(
            SecurityEvent.event_type,
            func.count(SecurityEvent.id)
        ).filter(
            SecurityEvent.created_at >= start_date
        ).group_by(SecurityEvent.event_type).all()
        
        # Unresolved events
        unresolved_events = SecurityEvent.query.filter(
            SecurityEvent.created_at >= start_date,
            SecurityEvent.resolved == False
        ).count()
        
        return {
            'total_events': total_events,
            'unresolved_events': unresolved_events,
            'severity_breakdown': dict(severity_stats),
            'type_breakdown': dict(type_stats),
            'period_days': days
        }


class UserManagementService:
    """Service for comprehensive user management"""
    
    @staticmethod
    def get_user_summary(user_id):
        """Get comprehensive user summary"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        # Get user's roles
        user_roles = UserRoleService.get_user_roles(user_id)
        role_names = [ur.role.name for ur in user_roles]
        
        # Get user's groups
        user_groups = UserGroupService.get_user_groups(user_id)
        group_names = [ug.group.name for ug in user_groups]
        
        # Get user's permissions
        permissions = AccessControlService.get_user_permissions(user_id)
        
        # Get recent security events
        recent_events = SecurityEvent.query.filter_by(
            user_id=user_id
        ).order_by(desc(SecurityEvent.created_at)).limit(10).all()
        
        # Get recent access logs
        recent_access = AccessLog.query.filter_by(
            user_id=user_id
        ).order_by(desc(AccessLog.created_at)).limit(20).all()
        
        return {
            'user': user,
            'roles': role_names,
            'groups': group_names,
            'permissions': permissions,
            'recent_security_events': recent_events,
            'recent_access_logs': recent_access
        }
    
    @staticmethod
    def bulk_assign_roles(user_ids, role_id, assigned_by=None, expires_at=None, reason=None):
        """Bulk assign role to multiple users"""
        assigned_count = 0
        
        for user_id in user_ids:
            try:
                UserRoleService.assign_role_to_user(
                    user_id, role_id, assigned_by, expires_at, reason
                )
                assigned_count += 1
            except Exception as e:
                current_app.logger.error(f"Failed to assign role {role_id} to user {user_id}: {str(e)}")
        
        return assigned_count
    
    @staticmethod
    def bulk_revoke_roles(user_ids, role_id, revoked_by=None, reason=None):
        """Bulk revoke role from multiple users"""
        revoked_count = 0
        
        for user_id in user_ids:
            try:
                if UserRoleService.revoke_role_from_user(user_id, role_id, revoked_by, reason):
                    revoked_count += 1
            except Exception as e:
                current_app.logger.error(f"Failed to revoke role {role_id} from user {user_id}: {str(e)}")
        
        return revoked_count
    
    @staticmethod
    def bulk_add_to_groups(user_ids, group_id, added_by=None):
        """Bulk add users to group"""
        added_count = 0
        
        for user_id in user_ids:
            try:
                UserGroupService.add_user_to_group(group_id, user_id, added_by)
                added_count += 1
            except Exception as e:
                current_app.logger.error(f"Failed to add user {user_id} to group {group_id}: {str(e)}")
        
        return added_count
    
    @staticmethod
    def bulk_remove_from_groups(user_ids, group_id, removed_by=None):
        """Bulk remove users from group"""
        removed_count = 0
        
        for user_id in user_ids:
            try:
                UserGroupService.remove_user_from_group(group_id, user_id, removed_by)
                removed_count += 1
            except Exception as e:
                current_app.logger.error(f"Failed to remove user {user_id} from group {group_id}: {str(e)}")
        
        return removed_count


# Initialize default permissions and roles
def initialize_default_permissions():
    """Initialize default system permissions"""
    default_permissions = [
        # User management permissions
        ('users:view', 'View Users', 'View user list and details', 'users', 'view'),
        ('users:create', 'Create Users', 'Create new users', 'users', 'create'),
        ('users:edit', 'Edit Users', 'Edit user information', 'users', 'edit'),
        ('users:delete', 'Delete Users', 'Delete users', 'users', 'delete'),
        ('users:manage_roles', 'Manage User Roles', 'Assign and revoke user roles', 'users', 'manage_roles'),
        
        # Role management permissions
        ('roles:view', 'View Roles', 'View role list and details', 'roles', 'view'),
        ('roles:create', 'Create Roles', 'Create new roles', 'roles', 'create'),
        ('roles:edit', 'Edit Roles', 'Edit role information', 'roles', 'edit'),
        ('roles:delete', 'Delete Roles', 'Delete roles', 'roles', 'delete'),
        ('roles:manage_permissions', 'Manage Role Permissions', 'Grant and revoke role permissions', 'roles', 'manage_permissions'),
        
        # Group management permissions
        ('groups:view', 'View Groups', 'View group list and details', 'groups', 'view'),
        ('groups:create', 'Create Groups', 'Create new groups', 'groups', 'create'),
        ('groups:edit', 'Edit Groups', 'Edit group information', 'groups', 'edit'),
        ('groups:delete', 'Delete Groups', 'Delete groups', 'groups', 'delete'),
        ('groups:manage_members', 'Manage Group Members', 'Add and remove group members', 'groups', 'manage_members'),
        
        # Content management permissions
        ('content:view', 'View Content', 'View all content', 'content', 'view'),
        ('content:edit', 'Edit Content', 'Edit any content', 'content', 'edit'),
        ('content:delete', 'Delete Content', 'Delete any content', 'content', 'delete'),
        ('content:moderate', 'Moderate Content', 'Moderate content', 'content', 'moderate'),
        
        # Analytics permissions
        ('analytics:view', 'View Analytics', 'View analytics dashboard', 'analytics', 'view'),
        ('analytics:export', 'Export Analytics', 'Export analytics data', 'analytics', 'export'),
        
        # System permissions
        ('system:config', 'System Configuration', 'Modify system configuration', 'system', 'config'),
        ('system:logs', 'View System Logs', 'View system logs', 'system', 'logs'),
        ('system:monitor', 'System Monitoring', 'Access system monitoring', 'system', 'monitor'),
        
        # Security permissions
        ('security:view_events', 'View Security Events', 'View security events', 'security', 'view_events'),
        ('security:manage_events', 'Manage Security Events', 'Manage security events', 'security', 'manage_events'),
        ('security:audit', 'Security Audit', 'Access security audit tools', 'security', 'audit'),
    ]
    
    for name, display_name, description, category, resource in default_permissions:
        existing = Permission.query.filter_by(name=name).first()
        if not existing:
            permission = Permission(
                name=name,
                display_name=display_name,
                description=description,
                category=category,
                resource=resource,
                action=resource.split(':')[0] if ':' in resource else 'manage',
                is_system=True
            )
            db.session.add(permission)
    
    db.session.commit()


def initialize_default_roles():
    """Initialize default system roles"""
    default_roles = [
        ('super_admin', 'Super Administrator', 'Full system access with all permissions', 100),
        ('admin', 'Administrator', 'Administrative access to most system features', 80),
        ('moderator', 'Moderator', 'Content moderation and user management', 60),
        ('analyst', 'Analyst', 'Access to analytics and reporting', 40),
        ('support', 'Support', 'Limited access for support tasks', 20),
    ]
    
    for name, display_name, description, level in default_roles:
        existing = AdminRole.query.filter_by(name=name).first()
        if not existing:
            role = AdminRole(
                name=name,
                display_name=display_name,
                description=description,
                level=level,
                is_system=True
            )
            db.session.add(role)
    
    db.session.commit()


def setup_default_role_permissions():
    """Setup default permissions for system roles"""
    role_permissions = {
        'super_admin': ['*'],  # All permissions
        'admin': [
            'users:view', 'users:create', 'users:edit', 'users:manage_roles',
            'roles:view', 'roles:create', 'roles:edit', 'roles:manage_permissions',
            'groups:view', 'groups:create', 'groups:edit', 'groups:manage_members',
            'content:view', 'content:edit', 'content:moderate',
            'analytics:view', 'analytics:export',
            'system:config', 'system:logs', 'system:monitor',
            'security:view_events', 'security:manage_events'
        ],
        'moderator': [
            'users:view', 'users:edit',
            'content:view', 'content:edit', 'content:delete', 'content:moderate',
            'analytics:view',
            'security:view_events'
        ],
        'analyst': [
            'analytics:view', 'analytics:export',
            'users:view'
        ],
        'support': [
            'users:view', 'users:edit',
            'content:view'
        ]
    }
    
    for role_name, permissions in role_permissions.items():
        role = AdminRole.query.filter_by(name=role_name).first()
        if not role:
            continue
        
        if '*' in permissions:
            # Grant all permissions
            all_permissions = Permission.query.filter_by(is_active=True).all()
            for permission in all_permissions:
                RoleService.grant_permission_to_role(role.id, permission.id)
        else:
            # Grant specific permissions
            for permission_name in permissions:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission:
                    RoleService.grant_permission_to_role(role.id, permission.id)
    
    db.session.commit()
