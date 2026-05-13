"""
Advanced User Role Management Models

This module contains models for advanced user role management including:
- Advanced role system
- Role-based permissions
- Role hierarchy
- Role assignment workflows
- Role analytics
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import User
import json


class Role(db.Model):
    """Model for user roles"""
    __tablename__ = 'roles'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')
    icon = db.Column(db.String(50))
    level = db.Column(db.Integer, default=0)  # Role hierarchy level
    is_active = db.Column(db.Boolean, default=True)
    is_system_role = db.Column(db.Boolean, default=False)  # System-defined roles
    is_admin_role = db.Column(db.Boolean, default=False)  # Administrative role
    permissions = db.Column(db.JSON)  # Role permissions
    role_metadata = db.Column(db.JSON)  # Additional role data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', secondary='user_roles', backref='roles')
    role_assignments = db.relationship('RoleAssignment', backref='role', lazy='dynamic')
    role_workflows = db.relationship('RoleWorkflow', backref='role', lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    @staticmethod
    def create_role(name, display_name, description=None, color='#007bff', icon=None, 
                    level=0, permissions=None, is_system_role=False, is_admin_role=False):
        """Create a new role"""
        role = Role(
            name=name,
            display_name=display_name,
            description=description,
            color=color,
            icon=icon,
            level=level,
            permissions=permissions or {},
            is_system_role=is_system_role,
            is_admin_role=is_admin_role
        )
        
        db.session.add(role)
        db.session.commit()
        return role
    
    def has_permission(self, permission):
        """Check if role has a specific permission"""
        if not self.permissions:
            return False
        return self.permissions.get(permission, False)
    
    def add_permission(self, permission, value=True):
        """Add a permission to the role"""
        if not self.permissions:
            self.permissions = {}
        self.permissions[permission] = value
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def remove_permission(self, permission):
        """Remove a permission from the role"""
        if self.permissions and permission in self.permissions:
            del self.permissions[permission]
            self.updated_at = datetime.utcnow()
            db.session.commit()
    
    def get_user_count(self):
        """Get number of users with this role"""
        return len(self.users)
    
    def is_higher_than(self, other_role):
        """Check if this role is higher in hierarchy than another role"""
        return self.level > other_role.level


class Permission(db.Model):
    """Model for permissions"""
    __tablename__ = 'permissions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)  # content, user, admin, system
    resource = db.Column(db.String(50), nullable=False)  # posts, comments, users, roles, etc.
    action = db.Column(db.String(50), nullable=False)  # create, read, update, delete, manage
    is_system_permission = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    role_permissions = db.relationship('RolePermission', backref='permission', lazy='dynamic')
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    @staticmethod
    def create_permission(name, display_name, description, category, resource, action, 
                         is_system_permission=False):
        """Create a new permission"""
        permission = Permission(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            resource=resource,
            action=action,
            is_system_permission=is_system_permission
        )
        
        db.session.add(permission)
        db.session.commit()
        return permission
    
    @staticmethod
    def get_permission_name(resource, action):
        """Generate permission name from resource and action"""
        return f"{resource}_{action}"


# RolePermission model is defined in app/admin/models.py to avoid conflicts


class UserRole(db.Model):
    """Model for user-role assignments"""
    __tablename__ = 'user_roles'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    assignment_metadata = db.Column(db.JSON)  # Assignment metadata
    
    # Foreign key relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='role_assignments')
    role = db.relationship('Role', foreign_keys=[role_id])
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by_id])
    
    # Unique constraint to prevent duplicate assignments
    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', name='unique_user_role'), {'extend_existing': True})
    
    def __repr__(self):
        return f'<UserRole {self.user.username} - {self.role.name}>'
    
    @staticmethod
    def assign_role(user_id, role_id, assigned_by_id=None, expires_at=None, assignment_metadata=None):
        """Assign a role to a user"""
        # Check if assignment already exists
        existing = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
        
        if existing:
            # Update existing assignment
            existing.assigned_by_id = assigned_by_id
            existing.assigned_at = datetime.utcnow()
            existing.expires_at = expires_at
            existing.assignment_metadata = assignment_metadata
            db.session.commit()
            return existing
        
        # Create new assignment
        assignment = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by_id=assigned_by_id,
            expires_at=expires_at,
            assignment_metadata=assignment_metadata
        )
        
        db.session.add(assignment)
        db.session.commit()
        return assignment
    
    @staticmethod
    def remove_role(user_id, role_id):
        """Remove a role from a user"""
        assignment = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
        if assignment:
            assignment.is_active = False
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_user_roles(user_id, active_only=True):
        """Get user's roles"""
        query = UserRole.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
            query = query.filter(
                (UserRole.expires_at.is_(None)) | (UserRole.expires_at > datetime.utcnow())
            )
        return query.all()
    
    def is_expired(self):
        """Check if role assignment is expired"""
        return self.expires_at and self.expires_at <= datetime.utcnow()


class RoleAssignment(db.Model):
    """Model for role assignment workflow tracking"""
    __tablename__ = 'role_assignments'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    workflow_type = db.Column(db.String(50), nullable=False)  # request, approval, assignment, removal
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, completed
    requested_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reason = db.Column(db.Text)
    request_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Foreign key relationships
    user = db.relationship('User', foreign_keys=[user_id])
    role = db.relationship('Role', foreign_keys=[role_id])
    requested_by_user = db.relationship('User', foreign_keys=[requested_by_id])
    approved_by_user = db.relationship('User', foreign_keys=[approved_by_id])
    
    def __repr__(self):
        return f'<RoleAssignment {self.user.username} - {self.role.name} ({self.status})>'
    
    @staticmethod
    def create_request(user_id, role_id, requested_by_id, reason=None, request_metadata=None):
        """Create a role assignment request"""
        assignment = RoleAssignment(
            user_id=user_id,
            role_id=role_id,
            workflow_type='request',
            status='pending',
            requested_by_id=requested_by_id,
            reason=reason,
            request_metadata=request_metadata
        )
        
        db.session.add(assignment)
        db.session.commit()
        return assignment
    
    def approve(self, approved_by_id):
        """Approve a role assignment request"""
        self.status = 'approved'
        self.approved_by_id = approved_by_id
        self.updated_at = datetime.utcnow()
        
        # Actually assign the role
        UserRole.assign_role(self.user_id, self.role_id, approved_by_id)
        
        # Mark as completed
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        db.session.commit()
        return True
    
    def reject(self, approved_by_id, reason=None):
        """Reject a role assignment request"""
        self.status = 'rejected'
        self.approved_by_id = approved_by_id
        self.reason = reason
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True


class RoleWorkflow(db.Model):
    """Model for role assignment workflows"""
    __tablename__ = 'role_workflows'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    workflow_type = db.Column(db.String(50), nullable=False)  # self_assign, manager_assign, admin_assign
    is_active = db.Column(db.Boolean, default=True)
    requires_approval = db.Column(db.Boolean, default=True)
    approval_roles = db.Column(db.JSON)  # Roles that can approve
    auto_assign = db.Column(db.Boolean, default=False)
    conditions = db.Column(db.JSON)  # Assignment conditions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationships
    role = db.relationship('Role', backref='workflows')
    
    def __repr__(self):
        return f'<RoleWorkflow {self.name}>'
    
    @staticmethod
    def create_workflow(name, description, role_id, workflow_type, requires_approval=True, 
                       approval_roles=None, auto_assign=False, conditions=None):
        """Create a new role workflow"""
        workflow = RoleWorkflow(
            name=name,
            description=description,
            role_id=role_id,
            workflow_type=workflow_type,
            requires_approval=requires_approval,
            approval_roles=approval_roles or [],
            auto_assign=auto_assign,
            conditions=conditions or {}
        )
        
        db.session.add(workflow)
        db.session.commit()
        return workflow
    
    def can_approve(self, user_id):
        """Check if user can approve assignments for this workflow"""
        if not self.requires_approval:
            return True
        
        user_roles = UserRole.get_user_roles(user_id)
        user_role_ids = [ur.role_id for ur in user_roles]
        
        return any(role_id in self.approval_roles for role_id in user_role_ids)
    
    def meets_conditions(self, user_id):
        """Check if user meets assignment conditions"""
        if not self.conditions:
            return True
        
        user = User.query.get(user_id)
        if not user:
            return False
        
        # Check various conditions (simplified)
        conditions = self.conditions
        
        # Check registration date
        if 'min_registration_days' in conditions:
            min_days = conditions['min_registration_days']
            if (datetime.utcnow() - user.created_at).days < min_days:
                return False
        
        # Check post count
        if 'min_posts' in conditions:
            min_posts = conditions['min_posts']
            if user.posts.count() < min_posts:
                return False
        
        # Check login count
        if 'min_logins' in conditions:
            min_logins = conditions['min_logins']
            if user.login_count < min_logins:
                return False
        
        # Check account age
        if 'min_account_age_days' in conditions:
            min_age = conditions['min_account_age_days']
            if (datetime.utcnow() - user.created_at).days < min_age:
                return False
        
        # Check user level (if implemented)
        if 'min_user_level' in conditions:
            min_level = conditions['min_user_level']
            if hasattr(user, 'level') and user.level < min_level:
                return False
        
        return True
    
    def process_auto_assignment(self, user_id):
        """Process automated role assignment"""
        if not self.auto_assign:
            return False
        
        if not self.meets_conditions(user_id):
            return False
        
        # Check if user already has this role
        existing = UserRole.query.filter_by(user_id=user_id, role_id=self.role_id).first()
        if existing and existing.is_active:
            return False  # User already has the role
        
        # Create role assignment
        assignment = RoleAssignment.create_request(
            user_id=user_id,
            role_id=self.role_id,
            requested_by_id=None,  # System assignment
            reason="Automated role assignment based on workflow conditions",
            request_metadata={'auto_assigned': True, 'workflow_id': self.id}
        )
        
        # If no approval required, assign immediately
        if not self.requires_approval:
            assignment.approve(None)  # System approval
        
        return True


class RoleHistory(db.Model):
    """Model for role assignment history tracking"""
    __tablename__ = 'role_history'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    action_type = db.Column(db.String(20), nullable=False)  # assigned, unassigned, expired, renewed
    action_reason = db.Column(db.Text)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    user = db.relationship('User', foreign_keys=[user_id])
    role = db.relationship('Role', foreign_keys=[role_id])
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_id])
    
    def __repr__(self):
        return f'<RoleHistory {self.user.username} - {self.role.name} - {self.action_type}>'
    
    @staticmethod
    def record_action(user_id, role_id, action_type, reason=None, assigned_by_id=None, expires_at=None):
        """Record role action in history"""
        history = RoleHistory(
            user_id=user_id,
            role_id=role_id,
            action_type=action_type,
            action_reason=reason,
            assigned_by_id=assigned_by_id,
            expires_at=expires_at
        )
        
        db.session.add(history)
        db.session.commit()
        return history
    
    @staticmethod
    def get_user_role_history(user_id, role_id=None):
        """Get user's role history"""
        query = RoleHistory.query.filter_by(user_id=user_id)
        if role_id:
            query = query.filter_by(role_id=role_id)
        
        return query.order_by(RoleHistory.created_at.desc()).all()
    
    @staticmethod
    def get_role_assignments_history(role_id, days=30):
        """Get assignment history for a role"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return RoleHistory.query.filter(
            RoleHistory.role_id == role_id,
            RoleHistory.created_at >= start_date
        ).order_by(RoleHistory.created_at.desc()).all()


class AutomatedRoleAssignment(db.Model):
    """Model for automated role assignment rules"""
    __tablename__ = 'automated_role_assignments'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    conditions = db.Column(db.JSON, nullable=False)  # Assignment conditions
    is_active = db.Column(db.Boolean, default=True)
    check_interval = db.Column(db.Integer, default=3600)  # Check interval in seconds
    last_checked = db.Column(db.DateTime)
    auto_remove = db.Column(db.Boolean, default=False)  # Auto-remove when conditions no longer met
    expires_after = db.Column(db.Integer)  # Auto-expire after N days
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationships
    role = db.relationship('Role', backref='automated_assignments')
    
    def __repr__(self):
        return f'<AutomatedRoleAssignment {self.name}>'
    
    @staticmethod
    def create_assignment(name, description, role_id, conditions, check_interval=3600, 
                        auto_remove=False, expires_after=None):
        """Create automated role assignment"""
        assignment = AutomatedRoleAssignment(
            name=name,
            description=description,
            role_id=role_id,
            conditions=conditions,
            check_interval=check_interval,
            auto_remove=auto_remove,
            expires_after=expires_after
        )
        
        db.session.add(assignment)
        db.session.commit()
        return assignment
    
    def check_user_eligibility(self, user_id):
        """Check if user meets assignment conditions"""
        user = User.query.get(user_id)
        if not user:
            return False
        
        conditions = self.conditions
        
        # Check registration date
        if 'min_registration_days' in conditions:
            min_days = conditions['min_registration_days']
            if (datetime.utcnow() - user.created_at).days < min_days:
                return False
        
        # Check post count
        if 'min_posts' in conditions:
            min_posts = conditions['min_posts']
            if user.posts.count() < min_posts:
                return False
        
        # Check login count
        if 'min_logins' in conditions:
            min_logins = conditions['min_logins']
            if user.login_count < min_logins:
                return False
        
        # Check account age
        if 'min_account_age_days' in conditions:
            min_age = conditions['min_account_age_days']
            if (datetime.utcnow() - user.created_at).days < min_age:
                return False
        
        # Check user level
        if 'min_user_level' in conditions:
            min_level = conditions['min_user_level']
            if hasattr(user, 'level') and user.level < min_level:
                return False
        
        # Check specific user attributes
        if 'is_verified' in conditions:
            if conditions['is_verified'] and not user.is_verified:
                return False
        
        if 'is_active' in conditions:
            if conditions['is_active'] and not user.is_active:
                return False
        
        # Check custom conditions
        if 'custom_conditions' in conditions:
            for condition in conditions['custom_conditions']:
                if not self.evaluate_custom_condition(user, condition):
                    return False
        
        return True
    
    def evaluate_custom_condition(self, user, condition):
        """Evaluate custom condition"""
        # This would be extended with custom condition evaluation logic
        condition_type = condition.get('type')
        condition_field = condition.get('field')
        condition_value = condition.get('value')
        condition_operator = condition.get('operator', 'equals')
        
        if not hasattr(user, condition_field):
            return False
        
        user_value = getattr(user, condition_field)
        
        if condition_operator == 'equals':
            return user_value == condition_value
        elif condition_operator == 'greater_than':
            return user_value > condition_value
        elif condition_operator == 'less_than':
            return user_value < condition_value
        elif condition_operator == 'contains':
            return condition_value in str(user_value)
        
        return False
    
    def assign_role(self, user_id):
        """Assign role to user if eligible"""
        if not self.check_user_eligibility(user_id):
            return False
        
        # Check if user already has this role
        existing = UserRole.query.filter_by(user_id=user_id, role_id=self.role_id).first()
        if existing and existing.is_active:
            return False  # User already has the role
        
        # Calculate expiration
        expires_at = None
        if self.expires_after:
            expires_at = datetime.utcnow() + timedelta(days=self.expires_after)
        
        # Assign role
        UserRole.assign_role(user_id, self.role_id, assigned_by_id=None, expires_at=expires_at)
        
        # Record in history
        RoleHistory.record_action(
            user_id=user_id,
            role_id=self.role_id,
            action_type='assigned',
            reason=f"Automated assignment: {self.name}",
            assigned_by_id=None,
            expires_at=expires_at
        )
        
        return True
    
    def remove_role(self, user_id):
        """Remove role from user if conditions no longer met"""
        if self.check_user_eligibility(user_id):
            return False  # User still meets conditions
        
        # Find and remove role
        assignment = UserRole.query.filter_by(user_id=user_id, role_id=self.role_id).first()
        if assignment and assignment.is_active:
            assignment.is_active = False
            db.session.commit()
            
            # Record in history
            RoleHistory.record_action(
                user_id=user_id,
                role_id=self.role_id,
                action_type='unassigned',
                reason=f"Automated removal: {self.name} - conditions no longer met",
                assigned_by_id=None
            )
            
            return True
        
        return False
    
    @staticmethod
    def process_all_assignments():
        """Process all automated role assignments"""
        assignments = AutomatedRoleAssignment.query.filter_by(is_active=True).all()
        
        processed_count = 0
        for assignment in assignments:
            # Update last checked time
            assignment.last_checked = datetime.utcnow()
            
            # Get all users who don't have this role
            users_without_role = db.session.query(User.id).outerjoin(UserRole).filter(
                UserRole.role_id != assignment.role_id
            ).all()
            
            # Check eligibility and assign
            for user_id_tuple in users_without_role:
                user_id = user_id_tuple[0]
                if assignment.assign_role(user_id):
                    processed_count += 1
            
            # Auto-remove if enabled
            if assignment.auto_remove:
                users_with_role = db.session.query(User.id).join(UserRole).filter(
                    UserRole.role_id == assignment.role_id,
                    UserRole.is_active == True
                ).all()
                
                for user_id_tuple in users_with_role:
                    user_id = user_id_tuple[0]
                    if assignment.remove_role(user_id):
                        processed_count += 1
        
        db.session.commit()
        return processed_count


class RoleRequest(db.Model):
    """Model for role request workflows"""
    __tablename__ = 'role_requests'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    request_type = db.Column(db.String(20), default='request')  # request, renewal, removal
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, withdrawn
    reason = db.Column(db.Text)
    request_metadata = db.Column(db.JSON)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    review_comment = db.Column(db.Text)
    expires_at = db.Column(db.DateTime)
    
    # Foreign key relationships
    user = db.relationship('User', foreign_keys=[user_id])
    role = db.relationship('Role', foreign_keys=[role_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    
    def __repr__(self):
        return f'<RoleRequest {self.user.username} - {self.role.name} - {self.status}>'
    
    @staticmethod
    def create_request(user_id, role_id, reason=None, request_type='request', request_metadata=None):
        """Create a role request"""
        # Check if user already has this role
        existing = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
        if existing and existing.is_active and request_type == 'request':
            return None  # User already has the role
        
        # Check if there's already a pending request
        existing_request = RoleRequest.query.filter_by(
            user_id=user_id, 
            role_id=role_id, 
            status='pending'
        ).first()
        
        if existing_request:
            return None  # Already has a pending request
        
        request = RoleRequest(
            user_id=user_id,
            role_id=role_id,
            reason=reason,
            request_type=request_type,
            request_metadata=request_metadata or {}
        )
        
        db.session.add(request)
        db.session.commit()
        return request
    
    def approve(self, reviewed_by_id, comment=None, expires_at=None):
        """Approve role request"""
        self.status = 'approved'
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by_id = reviewed_by_id
        self.review_comment = comment
        self.expires_at = expires_at
        
        # Assign the role
        UserRole.assign_role(self.user_id, self.role_id, reviewed_by_id, expires_at)
        
        # Record in history
        RoleHistory.record_action(
            user_id=self.user_id,
            role_id=self.role_id,
            action_type='assigned',
            reason=f"Role request approved: {self.reason or 'No reason provided'}",
            assigned_by_id=reviewed_by_id,
            expires_at=expires_at
        )
        
        db.session.commit()
        return True
    
    def reject(self, reviewed_by_id, comment=None):
        """Reject role request"""
        self.status = 'rejected'
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by_id = reviewed_by_id
        self.review_comment = comment
        
        # Record in history
        RoleHistory.record_action(
            user_id=self.user_id,
            role_id=self.role_id,
            action_type='rejected',
            reason=f"Role request rejected: {self.reason or 'No reason provided'}",
            assigned_by_id=reviewed_by_id
        )
        
        db.session.commit()
        return True
    
    def withdraw(self):
        """Withdraw role request"""
        self.status = 'withdrawn'
        db.session.commit()
        return True
    
    @staticmethod
    def get_pending_requests():
        """Get all pending role requests"""
        return RoleRequest.query.filter_by(status='pending').order_by(RoleRequest.requested_at.asc()).all()
    
    @staticmethod
    def get_user_requests(user_id):
        """Get user's role requests"""
        return RoleRequest.query.filter_by(user_id=user_id).order_by(RoleRequest.requested_at.desc()).all()


class GranularPermission(db.Model):
    """Model for granular permissions with detailed conditions"""
    __tablename__ = 'granular_permissions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    resource = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    conditions = db.Column(db.JSON)  # Specific conditions for permission
    is_system_permission = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    role_permissions = db.relationship('RoleGranularPermission', backref='permission', lazy='dynamic')
    user_permissions = db.relationship('UserGranularPermission', backref='permission', lazy='dynamic')
    
    def __repr__(self):
        return f'<GranularPermission {self.name}>'
    
    @staticmethod
    def create_permission(name, display_name, description, category, resource, action, 
                         conditions=None, is_system_permission=False):
        """Create a new granular permission"""
        permission = GranularPermission(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            resource=resource,
            action=action,
            conditions=conditions or {},
            is_system_permission=is_system_permission
        )
        
        db.session.add(permission)
        db.session.commit()
        return permission
    
    def check_conditions(self, user_id, resource_id=None):
        """Check if user meets permission conditions"""
        if not self.conditions:
            return True
        
        user = User.query.get(user_id)
        if not user:
            return False
        
        conditions = self.conditions
        
        # Check user level conditions
        if 'min_user_level' in conditions:
            min_level = conditions['min_user_level']
            if hasattr(user, 'level') and user.level < min_level:
                return False
        
        # Check account status
        if 'require_active_account' in conditions and conditions['require_active_account']:
            if not user.is_active or user.is_suspended or user.is_banned:
                return False
        
        # Check verification status
        if 'require_verified' in conditions and conditions['require_verified']:
            if not user.is_verified:
                return False
        
        # Check registration date
        if 'min_registration_days' in conditions:
            min_days = conditions['min_registration_days']
            if (datetime.utcnow() - user.created_at).days < min_days:
                return False
        
        # Check post count
        if 'min_posts' in conditions:
            min_posts = conditions['min_posts']
            if user.posts.count() < min_posts:
                return False
        
        # Check resource ownership
        if 'require_ownership' in conditions and conditions['require_ownership'] and resource_id:
            # This would need to be implemented based on resource type
            pass
        
        # Check custom conditions
        if 'custom_conditions' in conditions:
            for condition in conditions['custom_conditions']:
                if not self.evaluate_custom_condition(user, condition):
                    return False
        
        return True
    
    def evaluate_custom_condition(self, user, condition):
        """Evaluate custom condition"""
        condition_type = condition.get('type')
        condition_field = condition.get('field')
        condition_value = condition.get('value')
        condition_operator = condition.get('operator', 'equals')
        
        if not hasattr(user, condition_field):
            return False
        
        user_value = getattr(user, condition_field)
        
        if condition_operator == 'equals':
            return user_value == condition_value
        elif condition_operator == 'greater_than':
            return user_value > condition_value
        elif condition_operator == 'less_than':
            return user_value < condition_value
        elif condition_operator == 'contains':
            return condition_value in str(user_value)
        
        return False


class RoleGranularPermission(db.Model):
    """Model for role-granular permission relationships"""
    __tablename__ = 'role_granular_permissions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('granular_permissions.id'), nullable=False)
    granted = db.Column(db.Boolean, default=True)
    granted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Foreign key relationships
    role = db.relationship('Role', backref='granular_permissions')
    granted_by_user = db.relationship('User', foreign_keys=[granted_by_id])
    
    # Unique constraint to prevent duplicates
    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id', name='unique_role_granular_permission'), {'extend_existing': True})
    
    def __repr__(self):
        return f'<RoleGranularPermission {self.role.name} - {self.permission.name}>'


class UserGranularPermission(db.Model):
    """Model for user-granular permission relationships"""
    __tablename__ = 'user_granular_permissions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('granular_permissions.id'), nullable=False)
    granted = db.Column(db.Boolean, default=True)
    granted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Foreign key relationships
    user = db.relationship('User', backref='granular_permissions')
    granted_by_user = db.relationship('User', foreign_keys=[granted_by_id])
    
    # Unique constraint to prevent duplicates
    __table_args__ = (db.UniqueConstraint('user_id', 'permission_id', name='unique_user_granular_permission'), {'extend_existing': True})
    
    def __repr__(self):
        return f'<UserGranularPermission {self.user.username} - {self.permission.name}>'


class PermissionInheritance(db.Model):
    """Model for permission inheritance relationships"""
    __tablename__ = 'permission_inheritance'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    parent_permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    child_permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    inheritance_type = db.Column(db.String(20), default='implicit')  # implicit, explicit, conditional
    conditions = db.Column(db.JSON)  # Conditions for inheritance
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    parent_permission = db.relationship('Permission', foreign_keys=[parent_permission_id], backref='child_inheritances')
    child_permission = db.relationship('Permission', foreign_keys=[child_permission_id], backref='parent_inheritances')
    
    # Unique constraint to prevent duplicates
    __table_args__ = (db.UniqueConstraint('parent_permission_id', 'child_permission_id', name='unique_permission_inheritance'), {'extend_existing': True})
    
    def __repr__(self):
        return f'<PermissionInheritance {self.parent_permission.name} -> {self.child_permission.name}>'
    
    @staticmethod
    def create_inheritance(parent_permission_id, child_permission_id, inheritance_type='implicit', conditions=None):
        """Create permission inheritance relationship"""
        inheritance = PermissionInheritance(
            parent_permission_id=parent_permission_id,
            child_permission_id=child_permission_id,
            inheritance_type=inheritance_type,
            conditions=conditions or {}
        )
        
        db.session.add(inheritance)
        db.session.commit()
        return inheritance
    
    def check_inheritance_conditions(self, user_id, resource_id=None):
        """Check if inheritance conditions are met"""
        if not self.conditions:
            return True
        
        conditions = self.conditions
        
        # Check user conditions
        if 'user_conditions' in conditions:
            user_conditions = conditions['user_conditions']
            user = User.query.get(user_id)
            
            if not user:
                return False
            
            # Check user level
            if 'min_user_level' in user_conditions:
                min_level = user_conditions['min_user_level']
                if hasattr(user, 'level') and user.level < min_level:
                    return False
            
            # Check account status
            if 'require_active_account' in user_conditions and user_conditions['require_active_account']:
                if not user.is_active or user.is_suspended or user.is_banned:
                    return False
        
        # Check resource conditions
        if 'resource_conditions' in conditions and resource_id:
            resource_conditions = conditions['resource_conditions']
            # This would need to be implemented based on resource type
            pass
        
        return True


class PermissionAudit(db.Model):
    """Model for permission auditing"""
    __tablename__ = 'permission_audit'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    action_type = db.Column(db.String(20), nullable=False)  # granted, revoked, checked, denied
    action_reason = db.Column(db.Text)
    resource_id = db.Column(db.Integer)  # ID of the resource being accessed
    resource_type = db.Column(db.String(50))  # Type of resource
    granted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    success = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    user = db.relationship('User', foreign_keys=[user_id])
    permission = db.relationship('Permission', foreign_keys=[permission_id])
    granted_by = db.relationship('User', foreign_keys=[granted_by_id])
    
    def __repr__(self):
        return f'<PermissionAudit {self.user.username} - {self.permission.name} - {self.action_type}>'
    
    @staticmethod
    def log_permission_check(user_id, permission_id, action_type, success=True, reason=None, 
                           resource_id=None, resource_type=None, ip_address=None, user_agent=None):
        """Log permission check"""
        audit = PermissionAudit(
            user_id=user_id,
            permission_id=permission_id,
            action_type=action_type,
            action_reason=reason,
            resource_id=resource_id,
            resource_type=resource_type,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
        
        db.session.add(audit)
        db.session.commit()
        return audit
    
    @staticmethod
    def get_permission_audit_logs(permission_id=None, user_id=None, days=30):
        """Get permission audit logs"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = PermissionAudit.query.filter(PermissionAudit.created_at >= start_date)
        
        if permission_id:
            query = query.filter_by(permission_id=permission_id)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.order_by(PermissionAudit.created_at.desc()).all()
    
    @staticmethod
    def get_permission_usage_stats(permission_id, days=30):
        """Get permission usage statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        logs = PermissionAudit.query.filter(
            PermissionAudit.permission_id == permission_id,
            PermissionAudit.created_at >= start_date
        ).all()
        
        stats = {
            'total_checks': len(logs),
            'successful_checks': len([log for log in logs if log.success]),
            'failed_checks': len([log for log in logs if not log.success]),
            'unique_users': len(set([log.user_id for log in logs])),
            'daily_usage': {}
        }
        
        # Calculate daily usage
        for log in logs:
            date_key = log.created_at.strftime('%Y-%m-%d')
            if date_key not in stats['daily_usage']:
                stats['daily_usage'][date_key] = {'total': 0, 'successful': 0, 'failed': 0}
            
            stats['daily_usage'][date_key]['total'] += 1
            if log.success:
                stats['daily_usage'][date_key]['successful'] += 1
            else:
                stats['daily_usage'][date_key]['failed'] += 1
        
        return stats


class PermissionAnalytics(db.Model):
    """Model for permission analytics"""
    __tablename__ = 'permission_analytics'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_checks = db.Column(db.Integer, default=0)
    successful_checks = db.Column(db.Integer, default=0)
    failed_checks = db.Column(db.Integer, default=0)
    unique_users = db.Column(db.Integer, default=0)
    avg_response_time = db.Column(db.Float)  # Average response time in milliseconds
    peak_usage_hour = db.Column(db.Integer)  # Hour of peak usage
    resource_types = db.Column(db.JSON)  # Resource types accessed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    permission = db.relationship('Permission', backref='analytics')
    
    def __repr__(self):
        return f'<PermissionAnalytics {self.permission.name} - {self.date}>'
    
    @staticmethod
    def update_permission_analytics(permission_id, date=None):
        """Update permission analytics for a specific date"""
        if not date:
            date = datetime.utcnow().date()
        
        # Get audit logs for the date
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        audit_logs = PermissionAudit.query.filter(
            PermissionAudit.permission_id == permission_id,
            PermissionAudit.created_at >= start_datetime,
            PermissionAudit.created_at < end_datetime
        ).all()
        
        if not audit_logs:
            return None
        
        # Calculate analytics
        total_checks = len(audit_logs)
        successful_checks = len([log for log in audit_logs if log.success])
        failed_checks = total_checks - successful_checks
        unique_users = len(set([log.user_id for log in audit_logs]))
        
        # Calculate peak usage hour
        hourly_usage = {}
        for log in audit_logs:
            hour = log.created_at.hour
            hourly_usage[hour] = hourly_usage.get(hour, 0) + 1
        
        peak_usage_hour = max(hourly_usage.keys(), key=lambda k: hourly_usage[k]) if hourly_usage else None
        
        # Calculate resource types
        resource_types = {}
        for log in audit_logs:
            if log.resource_type:
                resource_types[log.resource_type] = resource_types.get(log.resource_type, 0) + 1
        
        # Update or create analytics record
        analytics = PermissionAnalytics.query.filter_by(
            permission_id=permission_id,
            date=date
        ).first()
        
        if analytics:
            analytics.total_checks = total_checks
            analytics.successful_checks = successful_checks
            analytics.failed_checks = failed_checks
            analytics.unique_users = unique_users
            analytics.peak_usage_hour = peak_usage_hour
            analytics.resource_types = resource_types
        else:
            analytics = PermissionAnalytics(
                permission_id=permission_id,
                date=date,
                total_checks=total_checks,
                successful_checks=successful_checks,
                failed_checks=failed_checks,
                unique_users=unique_users,
                peak_usage_hour=peak_usage_hour,
                resource_types=resource_types
            )
            db.session.add(analytics)
        
        db.session.commit()
        return analytics
    
    @staticmethod
    def get_permission_trends(permission_id, days=30):
        """Get permission usage trends"""
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        analytics = PermissionAnalytics.query.filter(
            PermissionAnalytics.permission_id == permission_id,
            PermissionAnalytics.date >= start_date
        ).order_by(PermissionAnalytics.date.asc()).all()
        
        trends = {
            'dates': [],
            'total_checks': [],
            'success_rate': [],
            'unique_users': []
        }
        
        for analytic in analytics:
            trends['dates'].append(analytic.date.strftime('%Y-%m-%d'))
            trends['total_checks'].append(analytic.total_checks)
            
            success_rate = (analytic.successful_checks / analytic.total_checks * 100) if analytic.total_checks > 0 else 0
            trends['success_rate'].append(success_rate)
            trends['unique_users'].append(analytic.unique_users)
        
        return trends


class RoleAnalytics(db.Model):
    """Model for role analytics"""
    __tablename__ = 'role_analytics'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_count = db.Column(db.Integer, default=0)
    new_assignments = db.Column(db.Integer, default=0)
    removals = db.Column(db.Integer, default=0)
    requests = db.Column(db.Integer, default=0)
    approvals = db.Column(db.Integer, default=0)
    rejections = db.Column(db.Integer, default=0)
    analytics_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationships
    role = db.relationship('Role', backref='analytics')
    
    # Unique constraint for daily aggregation
    __table_args__ = (db.UniqueConstraint('role_id', 'date', name='unique_role_analytics'), {'extend_existing': True})
    
    def __repr__(self):
        return f'<RoleAnalytics {self.role.name} - {self.date}: {self.user_count} users>'
    
    @staticmethod
    def calculate_daily_analytics(role_id, date=None):
        """Calculate daily analytics for a role"""
        if not date:
            date = datetime.utcnow().date()
        
        # Get or create analytics record
        analytics = RoleAnalytics.query.filter_by(role_id=role_id, date=date).first()
        if not analytics:
            analytics = RoleAnalytics(role_id=role_id, date=date)
            db.session.add(analytics)
        
        # Calculate metrics for the day
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        # Current user count
        analytics.user_count = UserRole.query.filter(
            UserRole.role_id == role_id,
            UserRole.is_active == True
        ).filter(
            (UserRole.expires_at.is_(None)) | (UserRole.expires_at > datetime.utcnow())
        ).count()
        
        # New assignments
        analytics.new_assignments = RoleAssignment.query.filter(
            RoleAssignment.role_id == role_id,
            RoleAssignment.workflow_type.in_(['assignment', 'request']),
            RoleAssignment.status == 'completed',
            RoleAssignment.created_at >= start_datetime,
            RoleAssignment.created_at < end_datetime
        ).count()
        
        # Removals
        analytics.removals = RoleAssignment.query.filter(
            RoleAssignment.role_id == role_id,
            RoleAssignment.workflow_type == 'removal',
            RoleAssignment.status == 'completed',
            RoleAssignment.created_at >= start_datetime,
            RoleAssignment.created_at < end_datetime
        ).count()
        
        # Requests
        analytics.requests = RoleAssignment.query.filter(
            RoleAssignment.role_id == role_id,
            RoleAssignment.workflow_type == 'request',
            RoleAssignment.created_at >= start_datetime,
            RoleAssignment.created_at < end_datetime
        ).count()
        
        # Approvals
        analytics.approvals = RoleAssignment.query.filter(
            RoleAssignment.role_id == role_id,
            RoleAssignment.status == 'approved',
            RoleAssignment.updated_at >= start_datetime,
            RoleAssignment.updated_at < end_datetime
        ).count()
        
        # Rejections
        analytics.rejections = RoleAssignment.query.filter(
            RoleAssignment.role_id == role_id,
            RoleAssignment.status == 'rejected',
            RoleAssignment.updated_at >= start_datetime,
            RoleAssignment.updated_at < end_datetime
        ).count()
        
        db.session.commit()
        return analytics
    
    @staticmethod
    def get_role_trends(role_id, days=30):
        """Get role analytics trends"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        analytics = RoleAnalytics.query.filter(
            RoleAnalytics.role_id == role_id,
            RoleAnalytics.date >= start_date,
            RoleAnalytics.date <= end_date
        ).order_by(RoleAnalytics.date.asc()).all()
        
        return analytics


class RoleHierarchy(db.Model):
    """Model for role hierarchy relationships"""
    __tablename__ = 'role_hierarchy'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    parent_role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    child_role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    relationship_type = db.Column(db.String(50), default='inherits')  # inherits, manages, oversees
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    parent_role = db.relationship('Role', foreign_keys=[parent_role_id], backref='child_relationships')
    child_role = db.relationship('Role', foreign_keys=[child_role_id], backref='parent_relationships')
    
    # Unique constraint to prevent duplicates
    __table_args__ = (db.UniqueConstraint('parent_role_id', 'child_role_id', name='unique_role_hierarchy'),)
    
    def __repr__(self):
        return f'<RoleHierarchy {self.parent_role.name} -> {self.child_role.name}>'
    
    @staticmethod
    def create_hierarchy(parent_role_id, child_role_id, relationship_type='inherits'):
        """Create a role hierarchy relationship"""
        hierarchy = RoleHierarchy(
            parent_role_id=parent_role_id,
            child_role_id=child_role_id,
            relationship_type=relationship_type
        )
        
        db.session.add(hierarchy)
        db.session.commit()
        return hierarchy
    
    @staticmethod
    def get_child_roles(role_id):
        """Get child roles of a role"""
        relationships = RoleHierarchy.query.filter_by(parent_role_id=role_id).all()
        return [rel.child_role for rel in relationships]
    
    @staticmethod
    def get_parent_roles(role_id):
        """Get parent roles of a role"""
        relationships = RoleHierarchy.query.filter_by(child_role_id=role_id).all()
        return [rel.parent_role for rel in relationships]
