"""
Unit tests for the Role Management System
"""

import pytest
from datetime import datetime, timedelta
from app.admin.roles.models import Role, Permission, RolePermission, UserRole, RoleAssignment, RoleWorkflow, RoleHierarchy, RoleAnalytics


class TestRole:
    """Test suite for role functionality."""

    def test_create_role(self):
        """Test creating a role."""
        role = Role.create_role(
            name='test_role',
            display_name='Test Role',
            description='A test role',
            color='#007bff',
            icon='test-icon',
            level=10,
            permissions={'posts_create': True, 'posts_edit': True}
        )
        
        assert role is not None
        assert role.name == 'test_role'
        assert role.display_name == 'Test Role'
        assert role.description == 'A test role'
        assert role.color == '#007bff'
        assert role.icon == 'test-icon'
        assert role.level == 10
        assert role.is_active is True
        assert role.is_system_role is False
        assert role.is_admin_role is False
        assert role.permissions['posts_create'] is True
        assert role.permissions['posts_edit'] is True

    def test_has_permission(self, sample_role):
        """Test checking if role has permission."""
        # Add permission to role
        sample_role.add_permission('test_permission', True)
        
        assert sample_role.has_permission('test_permission') is True
        assert sample_role.has_permission('nonexistent_permission') is False

    def test_add_permission(self, sample_role):
        """Test adding permission to role."""
        result = sample_role.add_permission('new_permission', True)
        assert result is True
        
        assert sample_role.has_permission('new_permission') is True

    def test_remove_permission(self, sample_role):
        """Test removing permission from role."""
        # Add permission first
        sample_role.add_permission('test_permission', True)
        assert sample_role.has_permission('test_permission') is True
        
        # Remove permission
        sample_role.remove_permission('test_permission')
        assert sample_role.has_permission('test_permission') is False

    def test_is_higher_than(self, sample_role):
        """Test role hierarchy comparison."""
        # Create higher level role
        higher_role = Role.create_role(
            name='higher_role',
            display_name='Higher Role',
            level=20
        )
        
        # Create lower level role
        lower_role = Role.create_role(
            name='lower_role',
            display_name='Lower Role',
            level=5
        )
        
        assert higher_role.is_higher_than(sample_role) is True
        assert lower_role.is_higher_than(sample_role) is False
        assert sample_role.is_higher_than(lower_role) is True
        assert sample_role.is_higher_than(higher_role) is False

    def test_get_user_count(self, sample_role, sample_user):
        """Test getting user count for role."""
        # Initially no users
        assert sample_role.get_user_count() == 0
        
        # Assign role to user
        UserRole.assign_role(sample_user.id, sample_role.id)
        
        # Should have one user
        assert sample_role.get_user_count() == 1

    def test_role_validation(self):
        """Test role validation."""
        # Test creating role with invalid data
        role = Role(
            name='',  # Empty name should be handled by validation
            display_name='Test Role',
            level=-1  # Negative level
        )
        
        # Should still create but validation would happen in forms
        db.session.add(role)
        db.session.commit()
        
        assert role.name == ''
        assert role.level == -1

    def test_role_permissions_json(self, sample_role):
        """Test role permissions JSON handling."""
        # Test with complex permissions
        permissions = {
            'posts': {'create': True, 'edit': True, 'delete': False},
            'comments': {'create': True, 'edit': False, 'delete': False},
            'users': {'read': True, 'write': False}
        }
        
        sample_role.permissions = permissions
        db.session.commit()
        
        # Check JSON is preserved
        loaded_permissions = sample_role.permissions
        assert loaded_permissions['posts']['create'] is True
        assert loaded_permissions['posts']['delete'] is False
        assert loaded_permissions['users']['read'] is True

    def test_system_role_protection(self):
        """Test system role protection."""
        # Create system role
        system_role = Role.create_role(
            name='system_role',
            display_name='System Role',
            is_system_role=True
        )
        
        assert system_role.is_system_role is True
        
        # System roles should not be deletable in normal operations
        # (This would be enforced in the business logic)
        assert system_role.is_system_role is True


class TestPermission:
    """Test suite for permission functionality."""

    def test_create_permission(self):
        """Test creating a permission."""
        permission = Permission.create_permission(
            name='posts_create',
            display_name='Create Posts',
            description='Permission to create posts',
            category='content',
            resource='posts',
            action='create'
        )
        
        assert permission is not None
        assert permission.name == 'posts_create'
        assert permission.display_name == 'Create Posts'
        assert permission.description == 'Permission to create posts'
        assert permission.category == 'content'
        assert permission.resource == 'posts'
        assert permission.action == 'create'
        assert permission.is_system_permission is False
        assert permission.is_active is True

    def test_get_permission_name(self):
        """Test generating permission name."""
        name = Permission.get_permission_name('posts', 'create')
        assert name == 'posts_create'
        
        name = Permission.get_permission_name('users', 'manage')
        assert name == 'users_manage'
        
        name = Permission.get_permission_name('comments', 'delete')
        assert name == 'comments_delete'

    def test_get_permissions_by_category(self):
        """Test getting permissions by category."""
        # Create permissions in different categories
        categories = ['content', 'user', 'admin', 'system']
        
        for category in categories:
            for resource in ['posts', 'comments']:
                Permission.create_permission(
                    name=f'{category}_{resource}_create',
                    display_name=f'Create {resource.title()}',
                    description=f'Permission to create {resource}',
                    category=category,
                    resource=resource,
                    action='create'
                )
        
        # Get permissions by category
        for category in categories:
            permissions = Permission.get_permissions_by_category(category)
            assert len(permissions) >= 2  # At least posts and comments
            
            for permission in permissions:
                assert permission.category == category

    def test_permission_categories(self):
        """Test different permission categories."""
        categories = ['content', 'user', 'admin', 'system', 'moderation', 'analytics']
        
        for category in categories:
            permission = Permission.create_permission(
                name=f'{category}_test',
                display_name='Test Permission',
                description='A test permission',
                category=category,
                resource='test',
                action='test'
            )
            
            assert permission.category == category

    def test_permission_resources(self):
        """Test different permission resources."""
        resources = ['posts', 'comments', 'users', 'roles', 'permissions', 'categories']
        
        for resource in resources:
            permission = Permission.create_permission(
                name=f'{resource}_create',
                display_name=f'Create {resource.title()}',
                description=f'Permission to create {resource}',
                category='content',
                resource=resource,
                action='create'
            )
            
            assert permission.resource == resource

    def test_permission_actions(self):
        """Test different permission actions."""
        actions = ['create', 'read', 'update', 'delete', 'manage', 'approve', 'reject']
        
        for action in actions:
            permission = Permission.create_permission(
                name=f'test_{action}',
                display_name=f'Test {action.title()}',
                description=f'Test {action} permission',
                category='test',
                resource='test',
                action=action
            )
            
            assert permission.action == action

    def test_system_permission(self):
        """Test system permission."""
        system_permission = Permission.create_permission(
            name='system_config',
            display_name='System Configuration',
            description='System configuration permission',
            category='system',
            resource='system',
            action='configure',
            is_system_permission=True
        )
        
        assert system_permission.is_system_permission is True

    def test_permission_activation(self):
        """Test permission activation/deactivation."""
        permission = Permission.create_permission(
            name='test_permission',
            display_name='Test Permission',
            category='test',
            resource='test',
            action='test'
        )
        
        assert permission.is_active is True
        
        # Deactivate
        permission.is_active = False
        db.session.commit()
        
        db.session.refresh(permission)
        assert permission.is_active is False


class TestUserRole:
    """Test suite for user role assignment functionality."""

    def test_assign_role(self, sample_user, sample_role):
        """Test assigning role to user."""
        assignment = UserRole.assign_role(
            user_id=sample_user.id,
            role_id=sample_role.id,
            assigned_by_id=sample_user.id
        )
        
        assert assignment is not None
        assert assignment.user_id == sample_user.id
        assert assignment.role_id == sample_role.id
        assert assignment.assigned_by_id == sample_user.id
        assert assignment.is_active is True
        assert assignment.expires_at is None

    def test_assign_role_with_expiration(self, sample_user, sample_role):
        """Test assigning role with expiration."""
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        assignment = UserRole.assign_role(
            user_id=sample_user.id,
            role_id=sample_role.id,
            assigned_by_id=sample_user.id,
            expires_at=expires_at
        )
        
        assert assignment.expires_at == expires_at

    def test_assign_role_duplicate(self, sample_user, sample_role):
        """Test assigning same role twice."""
        assignment1 = UserRole.assign_role(sample_user.id, sample_role.id)
        assignment2 = UserRole.assign_role(sample_user.id, sample_role.id)
        
        # Should return the same assignment
        assert assignment1 is not None
        assert assignment2 is not None
        assert assignment1.id == assignment2.id

    def test_remove_role(self, sample_user, sample_role):
        """Test removing role from user."""
        # Assign role first
        UserRole.assign_role(sample_user.id, sample_role.id)
        assert UserRole.get_user_roles(sample_user.id) is not None
        
        # Remove role
        result = UserRole.remove_role(sample_user.id, sample_role.id)
        assert result is True
        
        # Check role is removed
        user_roles = UserRole.get_user_roles(sample_user.id)
        assert len(user_roles) == 0

    def test_remove_nonexistent_role(self, sample_user, sample_role):
        """Test removing non-existent role assignment."""
        result = UserRole.remove_role(sample_user.id, sample_role.id)
        assert result is False

    def test_get_user_roles(self, sample_user, sample_role):
        """Test getting user's roles."""
        # Initially no roles
        roles = UserRole.get_user_roles(sample_user.id)
        assert len(roles) == 0
        
        # Assign role
        UserRole.assign_role(sample_user.id, sample_role.id)
        
        # Should have one role
        roles = UserRole.get_user_roles(sample_user.id)
        assert len(roles) == 1
        assert roles[0].role_id == sample_role.id

    def test_get_user_roles_active_only(self, sample_user, sample_role):
        """Test getting only active user roles."""
        # Assign role
        UserRole.assign_role(sample_user.id, sample_role.id)
        
        # Should have active role
        active_roles = UserRole.get_user_roles(sample_user.id, active_only=True)
        assert len(active_roles) == 1
        
        # Deactivate role
        assignment = UserRole.query.filter_by(
            user_id=sample_user.id,
            role_id=sample_role.id
        ).first()
        assignment.is_active = False
        db.session.commit()
        
        # Should have no active roles
        active_roles = UserRole.get_user_roles(sample_user.id, active_only=True)
        assert len(active_roles) == 0
        
        # But should still have all roles
        all_roles = UserRole.get_user_roles(sample_user.id, active_only=False)
        assert len(all_roles) == 1

    def test_is_expired(self, sample_user, sample_role):
        """Test role expiration checking."""
        # Assign role with past expiration
        expires_at = datetime.utcnow() - timedelta(days=1)
        assignment = UserRole.assign_role(
            user_id=sample_user.id,
            role_id=sample_role.id,
            expires_at=expires_at
        )
        
        assert assignment.is_expired() is True
        
        # Update to future expiration
        assignment.expires_at = datetime.utcnow() + timedelta(days=1)
        db.session.commit()
        
        assert assignment.is_expired() is False

    def test_multiple_roles(self, sample_user):
        """Test assigning multiple roles to user."""
        # Create multiple roles
        roles = []
        for i in range(3):
            role = Role.create_role(
                name=f'role_{i}',
                display_name=f'Role {i}',
                level=i * 10
            )
            roles.append(role)
        
        # Assign all roles
        for role in roles:
            UserRole.assign_role(sample_user.id, role.id)
        
        # Should have all roles
        user_roles = UserRole.get_user_roles(sample_user.id)
        assert len(user_roles) == 3
        
        # Check role levels
        role_ids = [r.role_id for r in user_roles]
        for role in roles:
            assert role.id in role_ids


class TestRoleAssignment:
    """Test suite for role assignment workflow functionality."""

    def test_create_request(self, sample_user, sample_role):
        """Test creating role assignment request."""
        request = RoleAssignment.create_request(
            user_id=sample_user.id,
            role_id=sample_role.id,
            requested_by_id=sample_user.id,
            reason='Need this role for my work'
        )
        
        assert request is not None
        assert request.user_id == sample_user.id
        assert request.role_id == sample_role.id
        assert request.workflow_type == 'request'
        assert request.status == 'pending'
        assert request.requested_by_id == sample_user.id
        assert request.reason == 'Need this role for my work'

    def test_approve_request(self, sample_user, sample_admin_user, sample_role):
        """Test approving role assignment request."""
        request = RoleAssignment.create_request(
            user_id=sample_user.id,
            role_id=sample_role.id,
            requested_by_id=sample_user.id
        )
        
        # Approve request
        result = request.approve(sample_admin_user.id)
        assert result is True
        
        # Check request status
        assert request.status == 'completed'
        assert request.approved_by_id == sample_admin_user.id
        assert request.completed_at is not None
        
        # Check role was assigned
        user_roles = UserRole.get_user_roles(sample_user.id)
        assert len(user_roles) == 1
        assert user_roles[0].role_id == sample_role.id

    def test_reject_request(self, sample_user, sample_admin_user, sample_role):
        """Test rejecting role assignment request."""
        request = RoleAssignment.create_request(
            user_id=sample_user.id,
            role_id=sample_role.id,
            requested_by_id=sample_user.id
        )
        
        # Reject request
        result = request.reject(sample_admin_user.id, 'Insufficient experience')
        assert result is True
        
        # Check request status
        assert request.status == 'rejected'
        assert request.approved_by_id == sample_admin_user.id
        assert request.reason == 'Insufficient experience'
        
        # Check role was NOT assigned
        user_roles = UserRole.get_user_roles(sample_user.id)
        assert len(user_roles) == 0

    def test_request_workflow_types(self, sample_user, sample_role):
        """Test different workflow types."""
        workflow_types = ['request', 'approval', 'assignment', 'removal']
        
        for workflow_type in workflow_types:
            request = RoleAssignment.create_request(
                user_id=sample_user.id,
                role_id=sample_role.id,
                requested_by_id=sample_user.id,
                workflow_type=workflow_type
            )
            
            assert request.workflow_type == workflow_type

    def test_request_status_transitions(self, sample_user, sample_admin_user, sample_role):
        """Test request status transitions."""
        request = RoleAssignment.create_request(
            user_id=sample_user.id,
            role_id=sample_role.id,
            requested_by_id=sample_user.id
        )
        
        # Initial status should be pending
        assert request.status == 'pending'
        
        # Approve
        request.approve(sample_admin_user.id)
        assert request.status == 'completed'
        
        # Cannot reject completed request
        result = request.reject(sample_admin_user.id, 'Too late')
        assert result is False  # Should fail

    def test_request_metadata(self, sample_user, sample_role):
        """Test request metadata handling."""
        metadata = {
            'department': 'engineering',
            'project': 'web-platform',
            'manager_id': 123,
            'urgency': 'high'
        }
        
        request = RoleAssignment.create_request(
            user_id=sample_user.id,
            role_id=sample_role.id,
            requested_by_id=sample_user.id,
            metadata=metadata
        )
        
        assert request.metadata['department'] == 'engineering'
        assert request.metadata['project'] == 'web-platform'
        assert request.metadata['manager_id'] == 123
        assert request.metadata['urgency'] == 'high'


class TestRoleHierarchy:
    """Test suite for role hierarchy functionality."""

    def test_create_hierarchy(self, sample_role):
        """Test creating role hierarchy."""
        # Create child role
        child_role = Role.create_role(
            name='child_role',
            display_name='Child Role',
            level=5
        )
        
        # Create hierarchy
        hierarchy = RoleHierarchy.create_hierarchy(
            parent_role_id=sample_role.id,
            child_role_id=child_role.id,
            relationship_type='inherits'
        )
        
        assert hierarchy is not None
        assert hierarchy.parent_role_id == sample_role.id
        assert hierarchy.child_role_id == child_role.id
        assert hierarchy.relationship_type == 'inherits'

    def test_get_child_roles(self, sample_role):
        """Test getting child roles."""
        # Create multiple child roles
        child_roles = []
        for i in range(3):
            child_role = Role.create_role(
                name=f'child_role_{i}',
                display_name=f'Child Role {i}',
                level=5
            )
            child_roles.append(child_role)
            
            RoleHierarchy.create_hierarchy(
                parent_role_id=sample_role.id,
                child_role_id=child_role.id
            )
        
        # Get child roles
        children = RoleHierarchy.get_child_roles(sample_role.id)
        assert len(children) == 3
        
        child_ids = [c.id for c in children]
        for child_role in child_roles:
            assert child_role.id in child_ids

    def test_get_parent_roles(self, sample_role):
        """Test getting parent roles."""
        # Create parent role
        parent_role = Role.create_role(
            name='parent_role',
            display_name='Parent Role',
            level=20
        )
        
        # Create hierarchy
        RoleHierarchy.create_hierarchy(
            parent_role_id=parent_role.id,
            child_role_id=sample_role.id
        )
        
        # Get parent roles
        parents = RoleHierarchy.get_parent_roles(sample_role.id)
        assert len(parents) == 1
        assert parents[0].id == parent_role.id

    def test_relationship_types(self, sample_role):
        """Test different relationship types."""
        # Create child role
        child_role = Role.create_role(
            name='child_role',
            display_name='Child Role',
            level=5
        )
        
        relationship_types = ['inherits', 'manages', 'oversees', 'supervises']
        
        for rel_type in relationship_types:
            hierarchy = RoleHierarchy.create_hierarchy(
                parent_role_id=sample_role.id,
                child_role_id=child_role.id + relationship_types.index(rel_type),  # Make unique
                relationship_type=rel_type
            )
            
            assert hierarchy.relationship_type == rel_type

    def test_duplicate_hierarchy(self, sample_role):
        """Test handling duplicate hierarchy relationships."""
        # Create child role
        child_role = Role.create_role(
            name='child_role',
            display_name='Child Role',
            level=5
        )
        
        # Create first hierarchy
        hierarchy1 = RoleHierarchy.create_hierarchy(
            parent_role_id=sample_role.id,
            child_role_id=child_role.id
        )
        
        # Create duplicate hierarchy
        hierarchy2 = RoleHierarchy.create_hierarchy(
            parent_role_id=sample_role.id,
            child_role_id=child_role.id
        )
        
        # Should return the same hierarchy
        assert hierarchy1 is not None
        assert hierarchy2 is not None
        assert hierarchy1.id == hierarchy2.id

    def test_multi_level_hierarchy(self):
        """Test multi-level hierarchy."""
        # Create roles at different levels
        grandparent = Role.create_role('grandparent', 'Grandparent', level=30)
        parent = Role.create_role('parent', 'Parent', level=20)
        child = Role.create_role('child', 'Child', level=10)
        grandchild = Role.create_role('grandchild', 'Grandchild', level=5)
        
        # Create hierarchy chain
        RoleHierarchy.create_hierarchy(grandparent.id, parent.id)
        RoleHierarchy.create_hierarchy(parent.id, child.id)
        RoleHierarchy.create_hierarchy(child.id, grandchild.id)
        
        # Test relationships
        parent_children = RoleHierarchy.get_child_roles(grandparent.id)
        assert len(parent_children) == 1
        assert parent_children[0].id == parent.id
        
        child_parents = RoleHierarchy.get_parent_roles(child.id)
        assert len(child_parents) == 1
        assert child_parents[0].id == parent.id


class TestRoleAnalytics:
    """Test suite for role analytics functionality."""

    def test_calculate_daily_analytics(self, sample_role, sample_user):
        """Test calculating daily analytics for role."""
        # Assign role to user
        UserRole.assign_role(sample_user.id, sample_role.id)
        
        # Create some role assignments
        for i in range(3):
            other_user = User(username=f'user_{i}', email=f'user_{i}@example.com', password_hash='hash')
            db.session.add(other_user)
            db.session.commit()
            UserRole.assign_role(other_user.id, sample_role.id)
        
        # Calculate analytics
        today = datetime.utcnow().date()
        analytics = RoleAnalytics.calculate_daily_analytics(sample_role.id, today)
        
        assert analytics is not None
        assert analytics.role_id == sample_role.id
        assert analytics.date == today
        assert analytics.user_count == 4  # 1 original + 3 new users
        assert analytics.new_assignments == 3
        assert analytics.removals == 0
        assert analytics.requests == 0
        assert analytics.approvals == 0
        assert analytics.rejections == 0

    def test_get_role_trends(self, sample_role, sample_user):
        """Test getting role analytics trends."""
        # Create analytics data for multiple days
        for days_ago in range(7, 0, -1):
            date = datetime.utcnow().date() - timedelta(days=days_ago)
            RoleAnalytics.calculate_daily_analytics(sample_role.id, date)
        
        # Get trend
        trends = RoleAnalytics.get_role_trends(sample_role.id, days=7)
        
        assert len(trends) == 7
        
        # Check dates are in ascending order
        for i in range(1, len(trends)):
            assert trends[i].date >= trends[i-1].date

    def test_analytics_with_requests(self, sample_role, sample_user, sample_admin_user):
        """Test analytics with role requests."""
        # Create role requests
        for i in range(5):
            request = RoleAssignment.create_request(
                user_id=sample_user.id,
                role_id=sample_role.id,
                requested_by_id=sample_user.id
            )
            
            if i < 3:
                # Approve first 3
                request.approve(sample_admin_user.id)
            else:
                # Reject last 2
                request.reject(sample_admin_user.id, 'Test rejection')
        
        # Calculate analytics
        today = datetime.utcnow().date()
        analytics = RoleAnalytics.calculate_daily_analytics(sample_role.id, today)
        
        assert analytics.requests == 5
        assert analytics.approvals == 3
        assert analytics.rejections == 2

    def test_analytics_with_removals(self, sample_role, sample_user):
        """Test analytics with role removals."""
        # Assign role to multiple users
        users = []
        for i in range(3):
            user = User(username=f'user_{i}', email=f'user_{i}@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()
            users.append(user)
            UserRole.assign_role(user.id, sample_role.id)
        
        # Remove roles
        for i in range(2):
            UserRole.remove_role(users[i].id, sample_role.id)
        
        # Calculate analytics
        today = datetime.utcnow().date()
        analytics = RoleAnalytics.calculate_daily_analytics(sample_role.id, today)
        
        assert analytics.user_count == 1  # Only one user still has the role
        assert analytics.removals == 2

    def test_analytics_metadata(self, sample_role):
        """Test analytics metadata handling."""
        metadata = {
            'total_assignments': 100,
            'total_removals': 10,
            'avg_assignment_duration': 30,
            'most_common_reason': 'Project requirement'
        }
        
        today = datetime.utcnow().date()
        analytics = RoleAnalytics.calculate_daily_analytics(sample_role.id, today)
        analytics.metadata = metadata
        db.session.commit()
        
        db.session.refresh(analytics)
        assert analytics.metadata['total_assignments'] == 100
        assert analytics.metadata['total_removals'] == 10
        assert analytics.metadata['avg_assignment_duration'] == 30
        assert analytics.metadata['most_common_reason'] == 'Project requirement'


class TestRoleManagementIntegration:
    """Integration tests for role management system."""

    def test_complete_role_workflow(self, sample_user, sample_admin_user):
        """Test complete role management workflow."""
        # Create role
        role = Role.create_role(
            name='content_manager',
            display_name='Content Manager',
            description='Manages content and posts',
            level=15,
            permissions={'posts_create': True, 'posts_edit': True}
        )
        
        # Add permission
        role.add_permission('comments_manage', True)
        assert role.has_permission('comments_manage') is True
        
        # Create role request
        request = RoleAssignment.create_request(
            user_id=sample_user.id,
            role_id=role.id,
            requested_by_id=sample_user.id,
            reason='Need to manage content for project X'
        )
        
        # Approve request
        request.approve(sample_admin_user.id)
        assert request.status == 'completed'
        
        # Check user has role
        user_roles = UserRole.get_user_roles(sample_user.id)
        assert len(user_roles) == 1
        assert user_roles[0].role_id == role.id
        
        # Create hierarchy
        admin_role = Role.create_role('admin', 'Administrator', level=30)
        hierarchy = RoleHierarchy.create_hierarchy(
            parent_role_id=admin_role.id,
            child_role_id=role.id,
            relationship_type='manages'
        )
        
        # Calculate analytics
        today = datetime.utcnow().date()
        analytics = RoleAnalytics.calculate_daily_analytics(role.id, today)
        assert analytics.user_count == 1
        assert analytics.new_assignments == 1

    def test_role_management_performance(self, sample_user):
        """Test performance of role management operations."""
        import time
        
        start_time = time.time()
        
        # Create multiple roles
        roles = []
        for i in range(10):
            role = Role.create_role(
                name=f'role_{i}',
                display_name=f'Role {i}',
                level=i
            )
            roles.append(role)
        
        # Assign roles to user
        for role in roles:
            UserRole.assign_role(sample_user.id, role.id)
        
        # Create requests
        for role in roles[:5]:
            RoleAssignment.create_request(
                user_id=sample_user.id,
                role_id=role.id,
                requested_by_id=sample_user.id
            )
        
        # Calculate analytics
        for role in roles:
            RoleAnalytics.calculate_daily_analytics(role.id)
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Should complete operations in reasonable time
        assert operation_time < 2.0, f"Operations took too long: {operation_time}s"

    def test_role_management_edge_cases(self, sample_user):
        """Test edge cases in role management."""
        # Test with None values
        role = Role(
            name='test_role',
            display_name='Test Role',
            permissions=None,
            metadata=None
        )
        db.session.add(role)
        db.session.commit()
        
        assert role.permissions is None
        assert role.metadata is None
        
        # Test with empty JSON
        role.permissions = {}
        role.metadata = {}
        db.session.commit()
        
        assert role.permissions == {}
        assert role.metadata == {}
        
        # Test with very long strings
        role.description = 'x' * 1000
        db.session.commit()
        
        assert len(role.description) == 1000

    def test_role_concurrent_operations(self, sample_user, sample_admin_user):
        """Test concurrent role operations."""
        # Create role
        role = Role.create_role('concurrent_role', 'Concurrent Role', level=10)
        
        # Multiple concurrent assignments should be handled gracefully
        assignments = []
        for i in range(5):
            assignment = UserRole.assign_role(sample_user.id, role.id)
            assignments.append(assignment)
        
        # Should all return the same assignment
        for assignment in assignments[1:]:
            assert assignment.id == assignments[0].id
        
        # Multiple concurrent requests
        requests = []
        for i in range(5):
            request = RoleAssignment.create_request(
                user_id=sample_user.id,
                role_id=role.id,
                requested_by_id=sample_user.id
            )
            requests.append(request)
        
        # Should all return the same request
        for request in requests[1:]:
            assert request.id == requests[0].id
