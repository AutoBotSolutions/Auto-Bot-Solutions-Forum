"""
Admin System Models

This module contains database models for the admin system's role and permission management,
including user roles, groups, permissions, and access control.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models import User


class Permission(db.Model):
    """Permission model for defining system permissions"""
    
    __tablename__ = 'permissions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False, index=True)
    resource = db.Column(db.String(100), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    is_system = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    roles = db.relationship('RolePermission', back_populates='permission', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    def to_dict(self):
        """Convert permission to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'category': self.category,
            'resource': self.resource,
            'action': self.action,
            'is_system': self.is_system,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AdminRole(db.Model):
    """Admin role model for role-based access control"""
    
    __tablename__ = 'admin_roles'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.Integer, default=0, nullable=False, index=True)  # Higher level = more permissions
    is_system = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_roles')
    permissions = db.relationship('RolePermission', back_populates='role', cascade='all, delete-orphan')
    users = db.relationship('UserRole', back_populates='role', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AdminRole {self.name}>'
    
    def to_dict(self):
        """Convert role to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'level': self.level,
            'is_system': self.is_system,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'permission_count': len(self.permissions),
            'user_count': len(self.users)
        }
    
    def has_permission(self, permission_name):
        """Check if role has specific permission"""
        return any(rp.permission.name == permission_name for rp in self.permissions if rp.permission.is_active)


class RolePermission(db.Model):
    """Association model for roles and permissions"""
    
    __tablename__ = 'role_permissions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('admin_roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    role = db.relationship('AdminRole', back_populates='permissions')
    permission = db.relationship('Permission', back_populates='roles')
    granter = db.relationship('User', foreign_keys=[granted_by], backref='granted_permissions')
    
    # Unique constraint to prevent duplicate role-permission assignments
    __table_args__ = (
        db.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
        db.Index('idx_role_permission_role', 'role_id'),
        db.Index('idx_role_permission_permission', 'permission_id')
    )
    
    def __repr__(self):
        return f'<RolePermission {self.role.name}:{self.permission.name}>'
    
    def to_dict(self):
        """Convert role permission to dictionary"""
        return {
            'id': self.id,
            'role_id': self.role_id,
            'permission_id': self.permission_id,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'granted_by': self.granted_by,
            'role_name': self.role.name if self.role else None,
            'permission_name': self.permission.name if self.permission else None
        }


class UserGroup(db.Model):
    """User group model for organizing users"""
    
    __tablename__ = 'user_groups'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_system = db.Column(db.Boolean, default=False, nullable=False)
    max_members = db.Column(db.Integer, default=None)  # None for unlimited
    auto_assign = db.Column(db.Boolean, default=False, nullable=False)  # Auto-assign new users
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_groups')
    users = db.relationship('UserGroupMember', back_populates='group', cascade='all, delete-orphan')
    roles = db.relationship('GroupRole', back_populates='group', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<UserGroup {self.name}>'
    
    def to_dict(self):
        """Convert group to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_active': self.is_active,
            'is_system': self.is_system,
            'max_members': self.max_members,
            'auto_assign': self.auto_assign,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'member_count': len(self.users),
            'role_count': len(self.roles)
        }
    
    def add_user(self, user_id, added_by=None):
        """Add user to group"""
        if self.max_members and len(self.users) >= self.max_members:
            raise ValueError(f'Group {self.name} has reached maximum member limit')
        
        # Check if user is already in group
        existing = UserGroupMember.query.filter_by(
            group_id=self.id,
            user_id=user_id
        ).first()
        
        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.left_at = None
                existing.added_by = added_by
                existing.added_at = datetime.utcnow()
                db.session.commit()
            return existing
        
        member = UserGroupMember(
            group_id=self.id,
            user_id=user_id,
            added_by=added_by
        )
        db.session.add(member)
        db.session.commit()
        return member
    
    def remove_user(self, user_id, removed_by=None):
        """Remove user from group"""
        member = UserGroupMember.query.filter_by(
            group_id=self.id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if member:
            member.is_active = False
            member.left_at = datetime.utcnow()
            member.removed_by = removed_by
            db.session.commit()
        
        return member
    
    def is_member(self, user_id):
        """Check if user is active member of group"""
        return UserGroupMember.query.filter_by(
            group_id=self.id,
            user_id=user_id,
            is_active=True
        ).first() is not None


class UserGroupMember(db.Model):
    """Association model for users and groups"""
    
    __tablename__ = 'user_group_members'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    left_at = db.Column(db.DateTime, nullable=True)
    removed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    group = db.relationship('UserGroup', back_populates='users')
    user = db.relationship('User', foreign_keys=[user_id], backref='group_memberships')
    adder = db.relationship('User', foreign_keys=[added_by], backref='added_group_memberships')
    remover = db.relationship('User', foreign_keys=[removed_by], backref='removed_group_memberships')
    
    # Unique constraint to prevent duplicate user-group assignments
    __table_args__ = (
        db.UniqueConstraint('group_id', 'user_id', name='uq_user_group'),
        db.Index('idx_user_group_group', 'group_id'),
        db.Index('idx_user_group_user', 'user_id'),
        db.Index('idx_user_group_active', 'group_id', 'user_id', 'is_active')
    )
    
    def __repr__(self):
        status = 'active' if self.is_active else 'inactive'
        return f'<UserGroupMember {self.user.username}:{self.group.name} ({status})>'
    
    def to_dict(self):
        """Convert group member to dictionary"""
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'is_active': self.is_active,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'added_by': self.added_by,
            'left_at': self.left_at.isoformat() if self.left_at else None,
            'removed_by': self.removed_by,
            'group_name': self.group.name if self.group else None,
            'username': self.user.username if self.user else None
        }


class UserRole(db.Model):
    """Association model for users and roles"""
    
    __tablename__ = 'user_roles'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('admin_roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # For temporary role assignments
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reason = db.Column(db.Text)  # Reason for assignment/revocation
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='role_assignments')
    role = db.relationship('AdminRole', back_populates='users')
    assigner = db.relationship('User', foreign_keys=[assigned_by], backref='assigned_roles')
    revoker = db.relationship('User', foreign_keys=[revoked_by], backref='revoked_roles')
    
    # Unique constraint to prevent duplicate user-role assignments
    __table_args__ = (
        db.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
        db.Index('idx_user_role_user', 'user_id'),
        db.Index('idx_user_role_role', 'role_id'),
        db.Index('idx_user_role_active', 'user_id', 'role_id', 'is_active')
    )
    
    def __repr__(self):
        status = 'active' if self.is_active else 'inactive'
        return f'<UserRole {self.user.username}:{self.role.name} ({status})>'
    
    def to_dict(self):
        """Convert user role to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'is_active': self.is_active,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'assigned_by': self.assigned_by,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'revoked_by': self.revoked_by,
            'reason': self.reason,
            'role_name': self.role.name if self.role else None,
            'username': self.user.username if self.user else None,
            'is_expired': self.is_expired()
        }
    
    def is_expired(self):
        """Check if role assignment has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if role assignment is valid (active and not expired)"""
        return self.is_active and not self.is_expired()


class GroupRole(db.Model):
    """Association model for groups and roles"""
    
    __tablename__ = 'group_roles'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('admin_roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    group = db.relationship('UserGroup', back_populates='roles')
    role = db.relationship('AdminRole', backref='group_assignments')
    assigner = db.relationship('User', foreign_keys=[assigned_by], backref='assigned_group_roles')
    
    # Unique constraint to prevent duplicate group-role assignments
    __table_args__ = (
        db.UniqueConstraint('group_id', 'role_id', name='uq_group_role'),
        db.Index('idx_group_role_group', 'group_id'),
        db.Index('idx_group_role_role', 'role_id')
    )
    
    def __repr__(self):
        status = 'active' if self.is_active else 'inactive'
        return f'<GroupRole {self.group.name}:{self.role.name} ({status})>'
    
    def to_dict(self):
        """Convert group role to dictionary"""
        return {
            'id': self.id,
            'group_id': self.group_id,
            'role_id': self.role_id,
            'is_active': self.is_active,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'assigned_by': self.assigned_by,
            'group_name': self.group.name if self.group else None,
            'role_name': self.role.name if self.role else None
        }


class AccessLog(db.Model):
    """Access log model for tracking permission checks and access attempts"""
    
    __tablename__ = 'access_logs'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    resource = db.Column(db.String(100), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    granted = db.Column(db.Boolean, nullable=False, index=True)
    reason = db.Column(db.Text)
    ip_address = db.Column(db.String(45), nullable=True, index=True)
    user_agent = db.Column(db.Text)
    session_id = db.Column(db.String(255), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='access_logs')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_access_logs_user_resource', 'user_id', 'resource'),
        db.Index('idx_access_logs_resource_action', 'resource', 'action'),
        db.Index('idx_access_logs_created_at', 'created_at'),
        db.Index('idx_access_logs_granted', 'granted'),
    )
    
    def __repr__(self):
        result = 'GRANTED' if self.granted else 'DENIED'
        return f'<AccessLog {self.user.username if self.user else "Anonymous"}:{self.action}:{self.resource} ({result})>'
    
    def to_dict(self):
        """Convert access log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'resource': self.resource,
            'action': self.action,
            'granted': self.granted,
            'reason': self.reason,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'username': self.user.username if self.user else None
        }


# SecurityEvent model is defined in app/security/models.py to avoid conflicts
