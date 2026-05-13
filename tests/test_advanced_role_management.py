"""
Unit tests for Advanced Role Management and Permission Management features
"""

import pytest
import json
from datetime import datetime, timedelta
from app.admin.roles.models import (
    Role, Permission, RolePermission, UserRole, RoleAssignment, RoleWorkflow,
    RoleHistory, AutomatedRoleAssignment, RoleRequest, GranularPermission,
    RoleGranularPermission, UserGranularPermission, PermissionInheritance,
    PermissionAudit, PermissionAnalytics
)


class TestAdvancedRoleManagement:
    """Test suite for advanced role management functionality."""

    def test_role_history_tracking(self, sample_user, sample_role):
        """Test role assignment history tracking."""
        # Record role assignment
        history = RoleHistory.record_action(
            user_id=sample_user.id,
            role_id=sample_role.id,
            action_type='assigned',
            reason='Test assignment',
            assigned_by_id=sample_user.id
        )
        
        assert history is not None
        assert history.user_id == sample_user.id
        assert history.role_id == sample_role.id
        assert history.action_type == 'assigned'
        assert history.action_reason == 'Test assignment'
        assert history.assigned_by_id == sample_user.id

    def test_get_user_role_history(self, sample_user, sample_role):
        """Test getting user's role history."""
        # Create multiple history entries
        RoleHistory.record_action(sample_user.id, sample_role.id, 'assigned', 'Test assignment')
        RoleHistory.record_action(sample_user.id, sample_role.id, 'renewed', 'Test renewal')
        
        history = RoleHistory.get_user_role_history(sample_user.id)
        
        assert len(history) >= 2
        assert history[0].action_type == 'renewed'  # Most recent first
        assert history[1].action_type == 'assigned'

    def test_automated_role_assignment_creation(self, sample_role):
        """Test creating automated role assignment."""
        conditions = {
            'min_registration_days': 7,
            'min_posts': 10,
            'require_verified': True
        }
        
        assignment = AutomatedRoleAssignment.create_assignment(
            name='Auto Veteran Role',
            description='Automatically assign veteran role',
            role_id=sample_role.id,
            conditions=conditions,
            check_interval=3600,
            auto_remove=True,
            expires_after=30
        )
        
        assert assignment is not None
        assert assignment.name == 'Auto Veteran Role'
        assert assignment.role_id == sample_role.id
        assert assignment.conditions['min_registration_days'] == 7
        assert assignment.conditions['min_posts'] == 10
        assert assignment.auto_remove is True
        assert assignment.expires_after == 30

    def test_automated_role_assignment_eligibility(self, sample_user, sample_role):
        """Test automated role assignment eligibility checking."""
        # Create assignment with conditions
        conditions = {
            'min_registration_days': 7,
            'min_posts': 10,
            'require_verified': True
        }
        
        assignment = AutomatedRoleAssignment.create_assignment(
            name='Test Assignment',
            description='Test automated assignment',
            role_id=sample_role.id,
            conditions=conditions
        )
        
        # Test with user who doesn't meet conditions
        sample_user.created_at = datetime.utcnow() - timedelta(days=5)
        sample_user.is_verified = False
        
        eligible = assignment.check_user_eligibility(sample_user.id)
        assert eligible is False
        
        # Test with user who meets conditions
        sample_user.created_at = datetime.utcnow() - timedelta(days=10)
        sample_user.is_verified = True
        
        # Mock post count
        with pytest.mock.patch.object(sample_user.posts, 'count', return_value=15):
            eligible = assignment.check_user_eligibility(sample_user.id)
            assert eligible is True

    def test_role_request_creation(self, sample_user, sample_role):
        """Test creating role requests."""
        request = RoleRequest.create_request(
            user_id=sample_user.id,
            role_id=sample_role.id,
            reason='I want this role for testing',
            request_type='request'
        )
        
        assert request is not None
        assert request.user_id == sample_user.id
        assert request.role_id == sample_role.id
        assert request.reason == 'I want this role for testing'
        assert request.request_type == 'request'
        assert request.status == 'pending'

    def test_role_request_approval(self, sample_user, sample_role, sample_admin_user):
        """Test approving role requests."""
        request = RoleRequest.create_request(
            user_id=sample_user.id,
            role_id=sample_role.id,
            reason='Test request'
        )
        
        # Approve the request
        success = request.approve(
            reviewed_by_id=sample_admin_user.id,
            comment='Approved for testing',
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        assert success is True
        assert request.status == 'approved'
        assert request.reviewed_by_id == sample_admin_user.id
        assert request.review_comment == 'Approved for testing'

    def test_role_request_rejection(self, sample_user, sample_role, sample_admin_user):
        """Test rejecting role requests."""
        request = RoleRequest.create_request(
            user_id=sample_user.id,
            role_id=sample_role.id,
            reason='Test request'
        )
        
        # Reject the request
        success = request.reject(
            reviewed_by_id=sample_admin_user.id,
            comment='Not eligible yet'
        )
        
        assert success is True
        assert request.status == 'rejected'
        assert request.reviewed_by_id == sample_admin_user.id
        assert request.review_comment == 'Not eligible yet'

    def test_get_pending_role_requests(self, sample_user, sample_role):
        """Test getting pending role requests."""
        # Create multiple requests
        RoleRequest.create_request(sample_user.id, sample_role.id, 'Request 1')
        RoleRequest.create_request(sample_user.id, sample_role.id, 'Request 2')
        
        pending_requests = RoleRequest.get_pending_requests()
        
        assert len(pending_requests) >= 2
        for request in pending_requests:
            assert request.status == 'pending'

    def test_get_user_role_requests(self, sample_user, sample_role):
        """Test getting user's role requests."""
        # Create requests for user
        RoleRequest.create_request(sample_user.id, sample_role.id, 'Request 1')
        RoleRequest.create_request(sample_user.id, sample_role.id, 'Request 2')
        
        user_requests = RoleRequest.get_user_requests(sample_user.id)
        
        assert len(user_requests) >= 2
        for request in user_requests:
            assert request.user_id == sample_user.id


class TestGranularPermissions:
    """Test suite for granular permissions functionality."""

    def test_granular_permission_creation(self):
        """Test creating granular permissions."""
        conditions = {
            'min_user_level': 5,
            'require_verified': True,
            'min_registration_days': 30
        }
        
        permission = GranularPermission.create_permission(
            name='advanced_content_create',
            display_name='Advanced Content Creation',
            description='Create advanced content with conditions',
            category='content',
            resource='posts',
            action='create_advanced',
            conditions=conditions,
            is_system_permission=False
        )
        
        assert permission is not None
        assert permission.name == 'advanced_content_create'
        assert permission.category == 'content'
        assert permission.resource == 'posts'
        assert permission.action == 'create_advanced'
        assert permission.conditions['min_user_level'] == 5
        assert permission.conditions['require_verified'] is True

    def test_granular_permission_conditions_check(self, sample_user):
        """Test granular permission condition checking."""
        conditions = {
            'min_user_level': 5,
            'require_verified': True,
            'min_registration_days': 30
        }
        
        permission = GranularPermission.create_permission(
            name='test_permission',
            display_name='Test Permission',
            description='Test permission with conditions',
            category='test',
            resource='test',
            action='test',
            conditions=conditions
        )
        
        # Test with user who doesn't meet conditions
        sample_user.is_verified = False
        sample_user.created_at = datetime.utcnow() - timedelta(days=10)
        
        meets_conditions = permission.check_conditions(sample_user.id)
        assert meets_conditions is False
        
        # Test with user who meets conditions
        sample_user.is_verified = True
        sample_user.created_at = datetime.utcnow() - timedelta(days=35)
        
        # Mock user level
        with pytest.mock.patch.object(sample_user, 'level', 6):
            meets_conditions = permission.check_conditions(sample_user.id)
            assert meets_conditions is True

    def test_role_granular_permission_assignment(self, sample_role):
        """Test assigning granular permissions to roles."""
        permission = GranularPermission.create_permission(
            name='role_test_permission',
            display_name='Role Test Permission',
            description='Test permission for role',
            category='test',
            resource='test',
            action='test'
        )
        
        role_permission = RoleGranularPermission(
            role_id=sample_role.id,
            permission_id=permission.id,
            granted=True
        )
        
        assert role_permission.role_id == sample_role.id
        assert role_permission.permission_id == permission.id
        assert role_permission.granted is True

    def test_user_granular_permission_assignment(self, sample_user):
        """Test assigning granular permissions to users."""
        permission = GranularPermission.create_permission(
            name='user_test_permission',
            display_name='User Test Permission',
            description='Test permission for user',
            category='test',
            resource='test',
            action='test'
        )
        
        user_permission = UserGranularPermission(
            user_id=sample_user.id,
            permission_id=permission.id,
            granted=True
        )
        
        assert user_permission.user_id == sample_user.id
        assert user_permission.permission_id == permission.id
        assert user_permission.granted is True


class TestPermissionInheritance:
    """Test suite for permission inheritance functionality."""

    def test_permission_inheritance_creation(self, sample_permission):
        """Test creating permission inheritance."""
        conditions = {
            'user_conditions': {
                'min_user_level': 3,
                'require_active_account': True
            }
        }
        
        inheritance = PermissionInheritance.create_inheritance(
            parent_permission_id=sample_permission.id,
            child_permission_id=sample_permission.id + 1,  # Assuming another permission exists
            inheritance_type='conditional',
            conditions=conditions
        )
        
        assert inheritance is not None
        assert inheritance.inheritance_type == 'conditional'
        assert inheritance.conditions['user_conditions']['min_user_level'] == 3

    def test_permission_inheritance_conditions(self, sample_user):
        """Test permission inheritance condition checking."""
        conditions = {
            'user_conditions': {
                'min_user_level': 3,
                'require_active_account': True
            }
        }
        
        inheritance = PermissionInheritance(
            parent_permission_id=1,
            child_permission_id=2,
            inheritance_type='conditional',
            conditions=conditions
        )
        
        # Test with user who meets conditions
        sample_user.is_active = True
        with pytest.mock.patch.object(sample_user, 'level', 4):
            meets_conditions = inheritance.check_inheritance_conditions(sample_user.id)
            assert meets_conditions is True
        
        # Test with user who doesn't meet conditions
        sample_user.is_active = False
        meets_conditions = inheritance.check_inheritance_conditions(sample_user.id)
        assert meets_conditions is False


class TestPermissionAuditing:
    """Test suite for permission auditing functionality."""

    def test_permission_audit_logging(self, sample_user, sample_permission):
        """Test logging permission checks."""
        audit = PermissionAudit.log_permission_check(
            user_id=sample_user.id,
            permission_id=sample_permission.id,
            action_type='checked',
            success=True,
            reason='Permission granted',
            resource_id=123,
            resource_type='post',
            ip_address='192.168.1.1',
            user_agent='Test Agent'
        )
        
        assert audit is not None
        assert audit.user_id == sample_user.id
        assert audit.permission_id == sample_permission.id
        assert audit.action_type == 'checked'
        assert audit.success is True
        assert audit.resource_id == 123
        assert audit.resource_type == 'post'
        assert audit.ip_address == '192.168.1.1'

    def test_get_permission_audit_logs(self, sample_user, sample_permission):
        """Test getting permission audit logs."""
        # Create multiple audit logs
        PermissionAudit.log_permission_check(sample_user.id, sample_permission.id, 'checked', True)
        PermissionAudit.log_permission_check(sample_user.id, sample_permission.id, 'denied', False)
        
        logs = PermissionAudit.get_permission_audit_logs(
            permission_id=sample_permission.id,
            user_id=sample_user.id,
            days=30
        )
        
        assert len(logs) >= 2
        for log in logs:
            assert log.user_id == sample_user.id
            assert log.permission_id == sample_permission.id

    def test_get_permission_usage_stats(self, sample_user, sample_permission):
        """Test getting permission usage statistics."""
        # Create audit logs
        PermissionAudit.log_permission_check(sample_user.id, sample_permission.id, 'checked', True)
        PermissionAudit.log_permission_check(sample_user.id, sample_permission.id, 'checked', False)
        
        stats = PermissionAudit.get_permission_usage_stats(sample_permission.id, days=30)
        
        assert stats['total_checks'] >= 2
        assert stats['successful_checks'] >= 1
        assert stats['failed_checks'] >= 1
        assert stats['unique_users'] >= 1
        assert 'daily_usage' in stats


class TestPermissionAnalytics:
    """Test suite for permission analytics functionality."""

    def test_update_permission_analytics(self, sample_permission):
        """Test updating permission analytics."""
        # Create some audit logs first
        PermissionAudit.log_permission_check(1, sample_permission.id, 'checked', True)
        PermissionAudit.log_permission_check(2, sample_permission.id, 'checked', False)
        
        analytics = PermissionAnalytics.update_permission_analytics(sample_permission.id)
        
        assert analytics is not None
        assert analytics.permission_id == sample_permission.id
        assert analytics.total_checks >= 2
        assert analytics.successful_checks >= 1
        assert analytics.failed_checks >= 1
        assert analytics.unique_users >= 1

    def test_get_permission_trends(self, sample_permission):
        """Test getting permission usage trends."""
        # Create analytics data for multiple days
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        PermissionAnalytics.update_permission_analytics(sample_permission.id, yesterday)
        PermissionAnalytics.update_permission_analytics(sample_permission.id, today)
        
        trends = PermissionAnalytics.get_permission_trends(sample_permission.id, days=7)
        
        assert 'dates' in trends
        assert 'total_checks' in trends
        assert 'success_rate' in trends
        assert 'unique_users' in trends
        assert len(trends['dates']) >= 2


class TestAdvancedRoleManagementIntegration:
    """Test suite for advanced role management integration."""

    def test_automated_assignment_processing(self, sample_user, sample_role):
        """Test processing automated role assignments."""
        # Create automated assignment
        conditions = {
            'min_registration_days': 1,
            'min_posts': 1
        }
        
        assignment = AutomatedRoleAssignment.create_assignment(
            name='Test Auto Assignment',
            description='Test automated assignment',
            role_id=sample_role.id,
            conditions=conditions
        )
        
        # Make user eligible
        sample_user.created_at = datetime.utcnow() - timedelta(days=2)
        
        # Mock post count
        with pytest.mock.patch.object(sample_user.posts, 'count', return_value=5):
            # Process assignment
            success = assignment.assign_role(sample_user.id)
            assert success is True
        
        # Check if role was assigned
        user_role = UserRole.query.filter_by(
            user_id=sample_user.id,
            role_id=sample_role.id
        ).first()
        
        assert user_role is not None
        assert user_role.is_active is True

    def test_role_request_workflow(self, sample_user, sample_role, sample_admin_user):
        """Test complete role request workflow."""
        # Create request
        request = RoleRequest.create_request(
            user_id=sample_user.id,
            role_id=sample_role.id,
            reason='Test workflow request'
        )
        
        assert request.status == 'pending'
        
        # Approve request
        success = request.approve(
            reviewed_by_id=sample_admin_user.id,
            comment='Approved for workflow test'
        )
        
        assert success is True
        assert request.status == 'approved'
        
        # Check role assignment
        user_role = UserRole.query.filter_by(
            user_id=sample_user.id,
            role_id=sample_role.id
        ).first()
        
        assert user_role is not None
        assert user_role.is_active is True
        
        # Check history
        history = RoleHistory.get_user_role_history(sample_user.id, sample_role.id)
        assert len(history) >= 1
        assert history[0].action_type == 'assigned'

    def test_permission_inheritance_chain(self, sample_user):
        """Test permission inheritance chain."""
        # Create parent permission
        parent_permission = GranularPermission.create_permission(
            name='parent_permission',
            display_name='Parent Permission',
            description='Parent permission',
            category='test',
            resource='test',
            action='parent'
        )
        
        # Create child permission
        child_permission = GranularPermission.create_permission(
            name='child_permission',
            display_name='Child Permission',
            description='Child permission',
            category='test',
            resource='test',
            action='child'
        )
        
        # Create inheritance
        inheritance = PermissionInheritance.create_inheritance(
            parent_permission_id=parent_permission.id,
            child_permission_id=child_permission.id,
            inheritance_type='implicit'
        )
        
        assert inheritance.parent_permission_id == parent_permission.id
        assert inheritance.child_permission_id == child_permission.id
        assert inheritance.inheritance_type == 'implicit'

    def test_permission_audit_trail(self, sample_user, sample_permission):
        """Test complete permission audit trail."""
        # Log multiple permission checks
        PermissionAudit.log_permission_check(
            sample_user.id, sample_permission.id, 'checked', True,
            reason='Initial check', ip_address='192.168.1.1'
        )
        
        PermissionAudit.log_permission_check(
            sample_user.id, sample_permission.id, 'denied', False,
            reason='Access denied', ip_address='192.168.1.2'
        )
        
        PermissionAudit.log_permission_check(
            sample_user.id, sample_permission.id, 'granted', True,
            reason='Access granted', ip_address='192.168.1.3'
        )
        
        # Get audit logs
        logs = PermissionAudit.get_permission_audit_logs(
            permission_id=sample_permission.id,
            user_id=sample_user.id
        )
        
        assert len(logs) >= 3
        
        # Check log sequence
        actions = [log.action_type for log in logs]
        assert 'granted' in actions
        assert 'denied' in actions
        assert 'checked' in actions
        
        # Check IP addresses
        ips = [log.ip_address for log in logs]
        assert '192.168.1.1' in ips
        assert '192.168.1.2' in ips
        assert '192.168.1.3' in ips
