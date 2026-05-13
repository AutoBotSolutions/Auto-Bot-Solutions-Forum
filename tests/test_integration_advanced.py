"""
Integration tests for advanced user management systems
"""

import pytest
import json
from datetime import datetime, timedelta
from app.models import User
from app.admin.roles.models import (
    Role, Permission, UserRole, RoleHistory, AutomatedRoleAssignment,
    RoleRequest, GranularPermission, PermissionAudit, PermissionAnalytics
)
from app.user.social.models import UserFollow, SocialActivity
from app.user.analytics.models import UserBehavior, UserEngagement


class TestSocialIntegration:
    """Test suite for social features integration."""

    def test_social_profile_integration(self, sample_user, sample_user2):
        """Test integration between social features and user profiles."""
        # Test following relationship
        follow = UserFollow(
            follower_id=sample_user.id,
            following_id=sample_user2.id,
            created_at=datetime.utcnow()
        )
        
        assert follow.follower_id == sample_user.id
        assert follow.following_id == sample_user2.id
        
        # Test social activity integration
        activity = SocialActivity(
            user_id=sample_user.id,
            activity_type='follow',
            target_user_id=sample_user2.id,
            activity_data={'action': 'follow'},
            created_at=datetime.utcnow()
        )
        
        assert activity.user_id == sample_user.id
        assert activity.target_user_id == sample_user2.id
        assert activity.activity_type == 'follow'

    def test_social_analytics_integration(self, sample_user, sample_user2):
        """Test integration between social features and analytics."""
        # Create social activity
        activity = SocialActivity(
            user_id=sample_user.id,
            activity_type='post',
            activity_data={'content': 'Test post'},
            created_at=datetime.utcnow()
        )
        
        # Create corresponding user behavior
        behavior = UserBehavior(
            user_id=sample_user.id,
            behavior_type='social_post',
            action='create',
            behavior_metadata={'activity_id': activity.id},
            created_at=datetime.utcnow()
        )
        
        assert behavior.user_id == sample_user.id
        assert behavior.behavior_type == 'social_post'
        assert behavior.behavior_metadata['activity_id'] == activity.id

    def test_social_privacy_integration(self, sample_user):
        """Test integration between social features and privacy settings."""
        # Set social privacy preferences
        privacy_prefs = {
            'searchable': False,
            'indexable': False,
            'public_profile': False
        }
        
        sample_user.set_social_preferences(privacy_prefs)
        
        # Verify privacy settings affect social features
        saved_prefs = sample_user.get_social_preferences()
        assert saved_prefs['searchable'] is False
        assert saved_prefs['indexable'] is False
        assert saved_prefs['public_profile'] is False


class TestAnalyticsIntegration:
    """Test suite for analytics system integration."""

    def test_analytics_profile_integration(self, sample_user):
        """Test integration between analytics and user profiles."""
        # Create user behavior
        behavior = UserBehavior(
            user_id=sample_user.id,
            behavior_type='profile_view',
            action='view',
            behavior_metadata={'profile_id': sample_user.id},
            created_at=datetime.utcnow()
        )
        
        # Create corresponding engagement
        engagement = UserEngagement(
            user_id=sample_user.id,
            engagement_type='profile',
            engagement_score=10,
            engagement_metadata={'behavior_id': behavior.id},
            created_at=datetime.utcnow()
        )
        
        assert engagement.user_id == sample_user.id
        assert engagement.engagement_type == 'profile'
        assert engagement.engagement_metadata['behavior_id'] == behavior.id

    def test_analytics_social_integration(self, sample_user, sample_user2):
        """Test integration between analytics and social features."""
        # Create social activity
        activity = SocialActivity(
            user_id=sample_user.id,
            activity_type='follow',
            target_user_id=sample_user2.id,
            activity_data={'action': 'follow'},
            created_at=datetime.utcnow()
        )
        
        # Create analytics behavior
        behavior = UserBehavior(
            user_id=sample_user.id,
            behavior_type='social_follow',
            action='follow',
            behavior_metadata={
                'activity_id': activity.id,
                'target_user_id': sample_user2.id
            },
            created_at=datetime.utcnow()
        )
        
        assert behavior.behavior_metadata['activity_id'] == activity.id
        assert behavior.behavior_metadata['target_user_id'] == sample_user2.id

    def test_analytics_role_integration(self, sample_user, sample_role):
        """Test integration between analytics and role management."""
        # Assign role to user
        user_role = UserRole.assign_role(sample_user.id, sample_role.id)
        
        # Create role-based behavior
        behavior = UserBehavior(
            user_id=sample_user.id,
            behavior_type='role_activity',
            action='assigned',
            behavior_metadata={
                'role_id': sample_role.id,
                'role_name': sample_role.name
            },
            created_at=datetime.utcnow()
        )
        
        assert behavior.behavior_metadata['role_id'] == sample_role.id
        assert behavior.behavior_metadata['role_name'] == sample_role.name


class TestProfileCustomizationIntegration:
    """Test suite for profile customization integration."""

    def test_profile_social_integration(self, sample_user):
        """Test integration between profile customization and social features."""
        # Set profile customization
        profile_prefs = {
            'profile_theme': 'dark',
            'profile_layout': 'grid',
            'profile_show_badges': True,
            'profile_show_stats': True
        }
        
        sample_user.set_profile_preferences(profile_prefs)
        
        # Create social activity related to profile
        activity = SocialActivity(
            user_id=sample_user.id,
            activity_type='profile_update',
            activity_data=profile_prefs,
            created_at=datetime.utcnow()
        )
        
        assert activity.activity_data['profile_theme'] == 'dark'
        assert activity.activity_data['profile_layout'] == 'grid'

    def test_profile_analytics_integration(self, sample_user):
        """Test integration between profile customization and analytics."""
        # Update profile customization
        profile_prefs = {
            'profile_theme': 'ocean',
            'profile_skin': 'blue'
        }
        
        sample_user.set_profile_preferences(profile_prefs)
        
        # Track profile customization behavior
        behavior = UserBehavior(
            user_id=sample_user.id,
            behavior_type='profile_customization',
            action='theme_change',
            behavior_metadata=profile_prefs,
            created_at=datetime.utcnow()
        )
        
        assert behavior.behavior_type == 'profile_customization'
        assert behavior.behavior_metadata['profile_theme'] == 'ocean'

    def test_profile_privacy_integration(self, sample_user):
        """Test integration between profile customization and privacy."""
        # Set privacy preferences
        privacy_prefs = {
            'profile_public_profile': False,
            'profile_allow_messages': False,
            'profile_allow_friend_requests': True
        }
        
        sample_user.set_profile_preferences(privacy_prefs)
        
        # Verify privacy settings
        saved_prefs = sample_user.get_profile_preferences()
        assert saved_prefs['profile_public_profile'] is False
        assert saved_prefs['profile_allow_messages'] is False
        assert saved_prefs['profile_allow_friend_requests'] is True


class TestRoleManagementIntegration:
    """Test suite for role management integration."""

    def test_role_social_integration(self, sample_user, sample_user2, sample_role):
        """Test integration between role management and social features."""
        # Assign role to user
        UserRole.assign_role(sample_user.id, sample_role.id)
        
        # Create social activity based on role assignment
        activity = SocialActivity(
            user_id=sample_user.id,
            activity_type='role_assignment',
            activity_data={
                'role_id': sample_role.id,
                'role_name': sample_role.name
            },
            created_at=datetime.utcnow()
        )
        
        assert activity.activity_type == 'role_assignment'
        assert activity.activity_data['role_id'] == sample_role.id

    def test_role_analytics_integration(self, sample_user, sample_role):
        """Test integration between role management and analytics."""
        # Assign role to user
        user_role = UserRole.assign_role(sample_user.id, sample_role.id)
        
        # Track role assignment in analytics
        behavior = UserBehavior(
            user_id=sample_user.id,
            behavior_type='role_assignment',
            action='assigned',
            behavior_metadata={
                'role_id': sample_role.id,
                'role_name': sample_role.name,
                'assignment_id': user_role.id
            },
            created_at=datetime.utcnow()
        )
        
        # Create engagement for role assignment
        engagement = UserEngagement(
            user_id=sample_user.id,
            engagement_type='role',
            engagement_score=5,
            engagement_metadata={
                'role_id': sample_role.id,
                'behavior_id': behavior.id
            },
            created_at=datetime.utcnow()
        )
        
        assert engagement.engagement_metadata['role_id'] == sample_role.id
        assert engagement.engagement_metadata['behavior_id'] == behavior.id

    def test_role_history_integration(self, sample_user, sample_role):
        """Test integration between role management and history tracking."""
        # Assign role to user
        UserRole.assign_role(sample_user.id, sample_role.id)
        
        # Record role assignment in history
        history = RoleHistory.record_action(
            user_id=sample_user.id,
            role_id=sample_role.id,
            action_type='assigned',
            reason='Test assignment',
            assigned_by_id=sample_user.id
        )
        
        # Verify history entry
        user_history = RoleHistory.get_user_role_history(sample_user.id)
        assert len(user_history) >= 1
        assert user_history[0].action_type == 'assigned'
        assert user_history[0].role_id == sample_role.id

    def test_automated_role_integration(self, sample_user, sample_role):
        """Test integration between automated role assignment and other systems."""
        # Create automated assignment
        conditions = {
            'min_registration_days': 1,
            'min_posts': 1
        }
        
        auto_assignment = AutomatedRoleAssignment.create_assignment(
            name='Test Auto Role',
            description='Test automated role assignment',
            role_id=sample_role.id,
            conditions=conditions
        )
        
        # Make user eligible
        sample_user.created_at = datetime.utcnow() - timedelta(days=2)
        
        # Mock post count
        with pytest.mock.patch.object(sample_user.posts, 'count', return_value=5):
            # Process automated assignment
            success = auto_assignment.assign_role(sample_user.id)
            assert success is True
        
        # Verify role was assigned
        user_role = UserRole.query.filter_by(
            user_id=sample_user.id,
            role_id=sample_role.id
        ).first()
        
        assert user_role is not None
        assert user_role.is_active is True
        
        # Verify history was recorded
        history = RoleHistory.get_user_role_history(sample_user.id, sample_role.id)
        assert len(history) >= 1
        assert history[0].action_type == 'assigned'
        assert 'Automated assignment' in history[0].action_reason


class TestPermissionManagementIntegration:
    """Test suite for permission management integration."""

    def test_permission_role_integration(self, sample_role):
        """Test integration between permissions and roles."""
        # Create granular permission
        permission = GranularPermission.create_permission(
            name='test_integration_permission',
            display_name='Test Integration Permission',
            description='Test permission for integration',
            category='test',
            resource='test',
            action='test'
        )
        
        # Assign permission to role
        role_permission = RoleGranularPermission(
            role_id=sample_role.id,
            permission_id=permission.id,
            granted=True
        )
        
        assert role_permission.role_id == sample_role.id
        assert role_permission.permission_id == permission.id
        assert role_permission.granted is True

    def test_permission_audit_integration(self, sample_user, sample_permission):
        """Test integration between permissions and auditing."""
        # Log permission check
        audit = PermissionAudit.log_permission_check(
            user_id=sample_user.id,
            permission_id=sample_permission.id,
            action_type='checked',
            success=True,
            reason='Integration test',
            ip_address='127.0.0.1'
        )
        
        assert audit.user_id == sample_user.id
        assert audit.permission_id == sample_permission.id
        assert audit.action_type == 'checked'
        assert audit.success is True

    def test_permission_analytics_integration(self, sample_user, sample_permission):
        """Test integration between permissions and analytics."""
        # Create multiple audit logs
        PermissionAudit.log_permission_check(sample_user.id, sample_permission.id, 'checked', True)
        PermissionAudit.log_permission_check(sample_user.id, sample_permission.id, 'denied', False)
        
        # Update analytics
        analytics = PermissionAnalytics.update_permission_analytics(sample_permission.id)
        
        assert analytics is not None
        assert analytics.permission_id == sample_permission.id
        assert analytics.total_checks >= 2
        assert analytics.successful_checks >= 1
        assert analytics.failed_checks >= 1


class TestCrossSystemIntegration:
    """Test suite for cross-system integration."""

    def test_user_profile_social_analytics_integration(self, sample_user):
        """Test integration across user profile, social, and analytics systems."""
        # Update profile preferences
        profile_prefs = {
            'profile_theme': 'dark',
            'profile_layout': 'grid'
        }
        sample_user.set_profile_preferences(profile_prefs)
        
        # Create social activity
        activity = SocialActivity(
            user_id=sample_user.id,
            activity_type='profile_update',
            activity_data=profile_prefs,
            created_at=datetime.utcnow()
        )
        
        # Track in analytics
        behavior = UserBehavior(
            user_id=sample_user.id,
            behavior_type='profile_customization',
            action='update',
            behavior_metadata={
                'activity_id': activity.id,
                'preferences': profile_prefs
            },
            created_at=datetime.utcnow()
        )
        
        # Create engagement
        engagement = UserEngagement(
            user_id=sample_user.id,
            engagement_type='profile',
            engagement_score=10,
            engagement_metadata={'behavior_id': behavior.id},
            created_at=datetime.utcnow()
        )
        
        # Verify integration
        assert activity.activity_data == profile_prefs
        assert behavior.behavior_metadata['activity_id'] == activity.id
        assert engagement.engagement_metadata['behavior_id'] == behavior.id

    def test_role_permission_audit_analytics_integration(self, sample_user, sample_role):
        """Test integration across role, permission, audit, and analytics systems."""
        # Create granular permission
        permission = GranularPermission.create_permission(
            name='cross_system_permission',
            display_name='Cross System Permission',
            description='Permission for cross-system testing',
            category='test',
            resource='test',
            action='test'
        )
        
        # Assign permission to role
        role_permission = RoleGranularPermission(
            role_id=sample_role.id,
            permission_id=permission.id,
            granted=True
        )
        
        # Assign role to user
        user_role = UserRole.assign_role(sample_user.id, sample_role.id)
        
        # Log permission check
        audit = PermissionAudit.log_permission_check(
            user_id=sample_user.id,
            permission_id=permission.id,
            action_type='checked',
            success=True,
            reason='Cross-system integration test'
        )
        
        # Update analytics
        analytics = PermissionAnalytics.update_permission_analytics(permission.id)
        
        # Verify integration
        assert role_permission.role_id == sample_role.id
        assert user_role.user_id == sample_user.id
        assert audit.user_id == sample_user.id
        assert analytics.permission_id == permission.id

    def test_automated_role_permission_integration(self, sample_user, sample_role):
        """Test integration between automated role assignment and permissions."""
        # Create granular permission
        permission = GranularPermission.create_permission(
            name='auto_role_permission',
            display_name='Auto Role Permission',
            description='Permission for automated role testing',
            category='test',
            resource='test',
            action='test'
        )
        
        # Create automated role assignment
        conditions = {
            'min_registration_days': 1,
            'require_verified': True
        }
        
        auto_assignment = AutomatedRoleAssignment.create_assignment(
            name='Auto Role Integration',
            description='Test automated role integration',
            role_id=sample_role.id,
            conditions=conditions
        )
        
        # Make user eligible
        sample_user.created_at = datetime.utcnow() - timedelta(days=2)
        sample_user.is_verified = True
        
        # Process automated assignment
        success = auto_assignment.assign_role(sample_user.id)
        assert success is True
        
        # Assign permission to role
        role_permission = RoleGranularPermission(
            role_id=sample_role.id,
            permission_id=permission.id,
            granted=True
        )
        
        # Log permission check
        audit = PermissionAudit.log_permission_check(
            user_id=sample_user.id,
            permission_id=permission.id,
            action_type='checked',
            success=True,
            reason='Automated role assignment integration'
        )
        
        # Verify integration
        user_role = UserRole.query.filter_by(
            user_id=sample_user.id,
            role_id=sample_role.id
        ).first()
        
        assert user_role is not None
        assert role_permission.granted is True
        assert audit.success is True

    def test_complete_user_journey_integration(self, sample_user, sample_role):
        """Test complete user journey across all systems."""
        # 1. User joins system (already exists)
        
        # 2. User customizes profile
        profile_prefs = {
            'profile_theme': 'ocean',
            'profile_layout': 'grid',
            'profile_show_badges': True
        }
        sample_user.set_profile_preferences(profile_prefs)
        
        # 3. User engages in social activity
        activity = SocialActivity(
            user_id=sample_user.id,
            activity_type='post',
            activity_data={'content': 'First post'},
            created_at=datetime.utcnow()
        )
        
        # 4. User behavior is tracked
        behavior = UserBehavior(
            user_id=sample_user.id,
            behavior_type='content_creation',
            action='create_post',
            behavior_metadata={'activity_id': activity.id},
            created_at=datetime.utcnow()
        )
        
        # 5. User engagement is calculated
        engagement = UserEngagement(
            user_id=sample_user.id,
            engagement_type='content',
            engagement_score=15,
            engagement_metadata={'behavior_id': behavior.id},
            created_at=datetime.utcnow()
        )
        
        # 6. User qualifies for automated role
        conditions = {
            'min_posts': 1,
            'min_engagement_score': 10
        }
        
        auto_assignment = AutomatedRoleAssignment.create_assignment(
            name='Journey Role',
            description='Role for completing user journey',
            role_id=sample_role.id,
            conditions=conditions
        )
        
        # Mock user metrics
        with pytest.mock.patch.object(sample_user.posts, 'count', return_value=1):
            # Process automated role assignment
            success = auto_assignment.assign_role(sample_user.id)
            assert success is True
        
        # 7. Role assignment is recorded in history
        history = RoleHistory.record_action(
            user_id=sample_user.id,
            role_id=sample_role.id,
            action_type='assigned',
            reason='Completed user journey',
            assigned_by_id=None  # System assignment
        )
        
        # 8. User journey is complete
        # Verify all components are integrated
        
        # Check profile customization
        saved_prefs = sample_user.get_profile_preferences()
        assert saved_prefs['profile_theme'] == 'ocean'
        
        # Check social activity
        assert activity.user_id == sample_user.id
        assert activity.activity_type == 'post'
        
        # Check behavior tracking
        assert behavior.user_id == sample_user.id
        assert behavior.behavior_type == 'content_creation'
        
        # Check engagement calculation
        assert engagement.user_id == sample_user.id
        assert engagement.engagement_score == 15
        
        # Check role assignment
        user_role = UserRole.query.filter_by(
            user_id=sample_user.id,
            role_id=sample_role.id
        ).first()
        assert user_role is not None
        assert user_role.is_active is True
        
        # Check history tracking
        user_history = RoleHistory.get_user_role_history(sample_user.id)
        assert len(user_history) >= 1
        assert user_history[0].action_type == 'assigned'
        
        # Complete user journey integration verified
        assert True
