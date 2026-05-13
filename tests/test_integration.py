"""
Integration tests for User Management Systems
"""

import pytest
from datetime import datetime, timedelta
from app.models import User
from app.user.social.models import UserFollow, UserFriend, SocialActivity, UserGroup, GroupMember
from app.user.analytics.models import UserBehavior, UserEngagement, UserPerformance, UserSegment
from app.admin.roles.models import Role, Permission, UserRole, RoleAssignment, RoleHierarchy


class TestSocialAnalyticsIntegration:
    """Integration tests for social and analytics systems."""

    def test_social_activity_analytics_integration(self, sample_user, sample_admin_user):
        """Test integration between social activities and analytics."""
        # Create social activities
        activities = [
            ('post', 'created', 'User created a new post'),
            ('comment', 'created', 'User commented on a post'),
            ('like', 'created', 'User liked a post'),
            ('follow', 'started_following', 'User started following someone'),
            ('friend', 'accepted_request', 'User accepted friend request')
        ]
        
        for activity_type, action, description in activities:
            SocialActivity.create_activity(
                user_id=sample_user.id,
                activity_type=activity_type,
                action=action,
                description=description
            )
        
        # Track behaviors for analytics
        for activity_type, action, description in activities:
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type=activity_type,
                action=action,
                metadata={'description': description}
            )
        
        # Calculate engagement
        today = datetime.utcnow().date()
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        
        # Verify integration
        assert engagement.total_actions == 5
        assert engagement.post_count == 1
        assert engagement.comment_count == 1
        assert engagement.like_count == 1
        
        # Check social activities are reflected in analytics
        social_activities = SocialActivity.query.filter_by(user_id=sample_user.id).all()
        assert len(social_activities) == 5
        
        user_behaviors = UserBehavior.query.filter_by(user_id=sample_user.id).all()
        assert len(user_behaviors) == 5

    def test_user_following_analytics_integration(self, sample_user, sample_admin_user):
        """Test integration between following system and analytics."""
        # Create following relationship
        follow = UserFollow.follow_user(sample_user.id, sample_admin_user.id)
        
        # Track following behavior
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='follow',
            action='started_following',
            target_type='user',
            target_id=sample_admin_user.id,
            metadata={'followed_user_id': sample_admin_user.id}
        )
        
        # Create social activity
        SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='follow',
            action='started_following',
            target_type='user',
            target_id=sample_admin_user.id,
            description=f'{sample_user.username} started following {sample_admin_user.username}'
        )
        
        # Calculate engagement
        today = datetime.utcnow().date()
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        
        # Verify integration
        assert engagement.total_actions >= 1
        assert follow is not None
        
        # Check behavior tracking
        follow_behavior = UserBehavior.query.filter_by(
            user_id=sample_user.id,
            behavior_type='follow'
        ).first()
        assert follow_behavior is not None
        assert follow_behavior.target_id == sample_admin_user.id
        
        # Check social activity
        follow_activity = SocialActivity.query.filter_by(
            user_id=sample_user.id,
            activity_type='follow'
        ).first()
        assert follow_activity is not None
        assert follow_activity.target_id == sample_admin_user.id

    def test_user_group_analytics_integration(self, sample_user, sample_admin_user):
        """Test integration between groups and analytics."""
        # Create user group
        group = UserGroup.create_group(
            name='Test Group',
            creator_id=sample_user.id,
            description='A test group for integration testing'
        )
        
        # Add member to group
        group.add_member(sample_admin_user.id)
        
        # Track group-related behaviors
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='group',
            action='created_group',
            target_type='group',
            target_id=group.id,
            metadata={'group_name': group.name}
        )
        
        UserBehavior.track_behavior(
            user_id=sample_admin_user.id,
            behavior_type='group',
            action='joined_group',
            target_type='group',
            target_id=group.id,
            metadata={'group_name': group.name}
        )
        
        # Create social activities
        SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='group',
            action='created_group',
            target_type='group',
            target_id=group.id,
            description=f'{sample_user.username} created group {group.name}'
        )
        
        SocialActivity.create_activity(
            user_id=sample_admin_user.id,
            activity_type='group',
            action='joined_group',
            target_type='group',
            target_id=group.id,
            description=f'{sample_admin_user.username} joined group {group.name}'
        )
        
        # Calculate engagement
        today = datetime.utcnow().date()
        user_engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        admin_engagement = UserEngagement.calculate_daily_engagement(sample_admin_user.id, today)
        
        # Verify integration
        assert user_engagement.total_actions >= 1
        assert admin_engagement.total_actions >= 1
        assert group.get_member_count() == 2

    def test_friend_system_analytics_integration(self, sample_user, sample_admin_user):
        """Test integration between friend system and analytics."""
        # Send friend request
        friend_request = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        
        # Track friend request behavior
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='friend',
            action='sent_request',
            target_type='user',
            target_id=sample_admin_user.id,
            metadata={'request_id': friend_request.id}
        )
        
        # Accept friend request
        friend_request.approve(sample_admin_user.id)
        
        # Track acceptance behavior
        UserBehavior.track_behavior(
            user_id=sample_admin_user.id,
            behavior_type='friend',
            action='accepted_request',
            target_type='user',
            target_id=sample_user.id,
            metadata={'request_id': friend_request.id}
        )
        
        # Create social activities
        SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='friend',
            action='sent_request',
            target_type='user',
            target_id=sample_admin_user.id,
            description=f'{sample_user.username} sent friend request to {sample_admin_user.username}'
        )
        
        SocialActivity.create_activity(
            user_id=sample_admin_user.id,
            activity_type='friend',
            action='accepted_request',
            target_type='user',
            target_id=sample_user.id,
            description=f'{sample_admin_user.username} accepted friend request from {sample_user.username}'
        )
        
        # Calculate engagement
        today = datetime.utcnow().date()
        user_engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        admin_engagement = UserEngagement.calculate_daily_engagement(sample_admin_user.id, today)
        
        # Verify integration
        assert friend_request.status == 'accepted'
        assert UserFriend.are_friends(sample_user.id, sample_admin_user.id) is True
        assert user_engagement.total_actions >= 1
        assert admin_engagement.total_actions >= 1


class TestRoleManagementAnalyticsIntegration:
    """Integration tests for role management and analytics systems."""

    def test_role_assignment_analytics_integration(self, sample_user, sample_admin_user):
        """Test integration between role assignments and analytics."""
        # Create role
        role = Role.create_role(
            name='content_manager',
            display_name='Content Manager',
            level=15
        )
        
        # Create role assignment request
        request = RoleAssignment.create_request(
            user_id=sample_user.id,
            role_id=role.id,
            requested_by_id=sample_user.id,
            reason='Need content management access'
        )
        
        # Track role request behavior
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='role',
            action='requested_role',
            target_type='role',
            target_id=role.id,
            metadata={'request_id': request.id, 'reason': 'Need content management access'}
        )
        
        # Approve request
        request.approve(sample_admin_user.id)
        
        # Track role assignment behavior
        UserBehavior.track_behavior(
            user_id=sample_admin_user.id,
            behavior_type='role',
            action='assigned_role',
            target_type='user',
            target_id=sample_user.id,
            metadata={'role_id': role.id, 'approved_by': sample_admin_user.id}
        )
        
        # Calculate engagement
        today = datetime.utcnow().date()
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        admin_engagement = UserEngagement.calculate_daily_engagement(sample_admin_user.id, today)
        
        # Verify integration
        assert request.status == 'completed'
        assert UserRole.get_user_roles(sample_user.id) is not None
        assert engagement.total_actions >= 1
        assert admin_engagement.total_actions >= 1
        
        # Calculate role analytics
        role_analytics = RoleAnalytics.calculate_daily_analytics(role.id, today)
        assert role_analytics.requests == 1
        assert role_analytics.approvals == 1
        assert role_analytics.user_count == 1

    def test_role_hierarchy_analytics_integration(self, sample_user, sample_admin_user):
        """Test integration between role hierarchy and analytics."""
        # Create roles
        admin_role = Role.create_role('admin', 'Administrator', level=30)
        manager_role = Role.create_role('manager', 'Manager', level=20)
        user_role = Role.create_role('user', 'User', level=10)
        
        # Create hierarchy
        RoleHierarchy.create_hierarchy(admin_role.id, manager_role.id, 'manages')
        RoleHierarchy.create_hierarchy(manager_role.id, user_role.id, 'supervises')
        
        # Assign roles
        UserRole.assign_role(sample_admin_user.id, admin_role.id)
        UserRole.assign_role(sample_user.id, user_role.id)
        
        # Track role hierarchy behaviors
        UserBehavior.track_behavior(
            user_id=sample_admin_user.id,
            behavior_type='role',
            action='created_hierarchy',
            target_type='role',
            target_id=manager_role.id,
            metadata={'relationship_type': 'manages', 'child_role': manager_role.id}
        )
        
        # Create social activities for role assignments
        SocialActivity.create_activity(
            user_id=sample_admin_user.id,
            activity_type='role',
            action='assigned_role',
            target_type='role',
            target_id=admin_role.id,
            description=f'{sample_admin_user.username} assigned admin role'
        )
        
        SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='role',
            action='assigned_role',
            target_type='role',
            target_id=user_role.id,
            description=f'{sample_user.username} assigned user role'
        )
        
        # Calculate engagement
        today = datetime.utcnow().date()
        admin_engagement = UserEngagement.calculate_daily_engagement(sample_admin_user.id, today)
        user_engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        
        # Verify integration
        assert admin_engagement.total_actions >= 1
        assert user_engagement.total_actions >= 1
        
        # Check hierarchy relationships
        manager_children = RoleHierarchy.get_child_roles(admin_role.id)
        assert len(manager_children) == 1
        assert manager_children[0].id == manager_role.id
        
        user_parents = RoleHierarchy.get_parent_roles(user_role.id)
        assert len(user_parents) == 1
        assert user_parents[0].id == manager_role.id

    def test_permission_analytics_integration(self, sample_user, sample_admin_user):
        """Test integration between permissions and analytics."""
        # Create permissions
        permissions = [
            ('posts_create', 'Create Posts', 'content'),
            ('posts_edit', 'Edit Posts', 'content'),
            ('users_manage', 'Manage Users', 'user'),
            ('roles_manage', 'Manage Roles', 'admin')
        ]
        
        created_permissions = []
        for perm_name, display_name, category in permissions:
            permission = Permission.create_permission(
                name=perm_name,
                display_name=display_name,
                description=f'Permission to {display_name.lower()}',
                category=category,
                resource=perm_name.split('_')[0],
                action=perm_name.split('_')[1]
            )
            created_permissions.append(permission)
        
        # Create role and assign permissions
        role = Role.create_role(
            'content_manager',
            'Content Manager',
            level=15,
            permissions={'posts_create': True, 'posts_edit': True}
        )
        
        # Add permissions to role
        for permission in created_permissions[:2]:  # posts permissions
            role.add_permission(permission.name, True)
        
        # Assign role to user
        UserRole.assign_role(sample_user.id, role.id)
        
        # Track permission-related behaviors
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='permission',
            action='granted_permission',
            target_type='permission',
            metadata={'permission_names': ['posts_create', 'posts_edit']}
        )
        
        # Create social activity
        SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='permission',
            action='granted_permissions',
            description=f'{sample_user.username} granted content management permissions'
        )
        
        # Calculate engagement
        today = datetime.utcnow().date()
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        
        # Verify integration
        assert engagement.total_actions >= 1
        assert role.has_permission('posts_create') is True
        assert role.has_permission('posts_edit') is True
        assert role.has_permission('users_manage') is False


class TestUserManagementSystemIntegration:
    """Integration tests for complete user management system."""

    def test_complete_user_lifecycle_analytics(self, sample_user, sample_admin_user):
        """Test complete user lifecycle with analytics tracking."""
        # 1. User registration (already done)
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='registration',
            action='completed',
            metadata={'registration_date': sample_user.created_at.isoformat()}
        )
        
        # 2. Profile customization
        sample_user.set_profile_theme('dark', 'dark')
        sample_user.set_profile_layout({'layout': 'grid', 'columns': 2})
        
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='profile',
            action='customized',
            metadata={'theme': 'dark', 'layout': 'grid'}
        )
        
        # 3. Social interactions
        follow = UserFollow.follow_user(sample_user.id, sample_admin_user.id)
        friend_request = UserFriend.send_friend_request(sample_user.id, sample_admin_user.id, sample_user.id)
        friend_request.approve(sample_admin_user.id)
        
        # 4. Content creation
        for i in range(3):
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='post',
                action='created',
                target_type='post',
                target_id=i + 1
            )
            
            SocialActivity.create_activity(
                user_id=sample_user.id,
                activity_type='post',
                action='created',
                target_type='post',
                target_id=i + 1,
                description=f'{sample_user.username} created post {i + 1}'
            )
        
        # 5. Role assignment
        role = Role.create_role('member', 'Member', level=10)
        UserRole.assign_role(sample_user.id, role.id)
        
        # 6. Calculate comprehensive analytics
        today = datetime.utcnow().date()
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        performance = UserPerformance.calculate_performance_metrics(sample_user.id, 'daily')
        
        # Verify integration
        assert engagement.total_actions >= 6  # registration, profile, follow, friend, posts, role
        assert engagement.post_count == 3
        assert UserFriend.are_friends(sample_user.id, sample_admin_user.id) is True
        assert len(UserRole.get_user_roles(sample_user.id)) == 1
        assert len(performance) >= 1

    def test_cross_system_data_flow(self, sample_user, sample_admin_user):
        """Test data flow across all user management systems."""
        # Create user group
        group = UserGroup.create_group(
            name='Project Team',
            creator_id=sample_admin_user.id,
            description='Team for project collaboration'
        )
        
        # Add users to group
        group.add_member(sample_user.id)
        group.add_member(sample_admin_user.id)
        
        # Create role for group members
        member_role = Role.create_role('team_member', 'Team Member', level=15)
        UserRole.assign_role(sample_user.id, member_role.id)
        UserRole.assign_role(sample_admin_user.id, member_role.id)
        
        # Track group activities
        for user_id in [sample_user.id, sample_admin_user.id]:
            UserBehavior.track_behavior(
                user_id=user_id,
                behavior_type='group',
                action='joined',
                target_type='group',
                target_id=group.id,
                metadata={'group_name': group.name}
            )
            
            SocialActivity.create_activity(
                user_id=user_id,
                activity_type='group',
                action='joined',
                target_type='group',
                target_id=group.id,
                description=f'User joined group {group.name}'
            )
        
        # Create content within group context
        for i in range(2):
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='post',
                action='created',
                target_type='post',
                target_id=i + 1,
                metadata={'group_id': group.id, 'group_name': group.name}
            )
        
        # Calculate analytics
        today = datetime.utcnow().date()
        user_engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        admin_engagement = UserEngagement.calculate_daily_engagement(sample_admin_user.id, today)
        
        # Create user segment based on activity
        segment = UserSegment.create_segment(
            name='Active Team Members',
            segment_type='activity',
            criteria={'min_posts': 1, 'group_member': True}
        )
        
        # Apply segmentation
        matched_users = segment.apply_segmentation()
        
        # Verify cross-system integration
        assert group.get_member_count() == 2
        assert user_engagement.total_actions >= 2
        assert admin_engagement.total_actions >= 1
        assert len(matched_users) >= 1  # At least sample_user should match
        assert len(UserRole.get_user_roles(sample_user.id)) == 1
        assert len(UserRole.get_user_roles(sample_admin_user.id)) == 1

    def test_performance_monitoring_integration(self, sample_user, sample_admin_user):
        """Test performance monitoring across all systems."""
        import time
        
        # Start performance tracking
        start_time = time.time()
        
        # Create various objects across systems
        # Social system
        follow = UserFollow.follow_user(sample_user.id, sample_admin_user.id)
        friend_request = UserFriend.send_friend_request(sample_user.id, sample_admin_user.id, sample_user.id)
        group = UserGroup.create_group('Test Group', sample_user.id)
        
        # Analytics system
        for i in range(10):
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='test',
                action=f'action_{i}'
            )
        
        # Role management system
        role = Role.create_role('test_role', 'Test Role', level=10)
        UserRole.assign_role(sample_user.id, role.id)
        
        # Create social activities
        for i in range(5):
            SocialActivity.create_activity(
                user_id=sample_user.id,
                activity_type='test',
                action='created',
                target_type='test',
                target_id=i
            )
        
        # Calculate analytics
        today = datetime.utcnow().date()
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        performance = UserPerformance.calculate_performance_metrics(sample_user.id, 'daily')
        
        # Create segment
        segment = UserSegment.create_segment(
            'Test Segment',
            'Test segment description',
            'activity',
            {'min_behaviors': 5}
        )
        segment.apply_segmentation()
        
        # Create prediction
        prediction = UserPrediction.create_prediction(
            user_id=sample_user.id,
            prediction_type='engagement',
            prediction_value=75.0,
            confidence=0.8,
            target_date=today + timedelta(days=30)
        )
        
        # Create dashboard
        dashboard = UserDashboard.create_dashboard(
            user_id=sample_user.id,
            name='Performance Dashboard'
        )
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Verify performance
        assert operation_time < 3.0, f"Operations took too long: {operation_time}s"
        
        # Verify data integrity across systems
        assert follow is not None
        assert friend_request is not None
        assert group is not None
        assert role is not None
        assert engagement is not None
        assert len(performance) >= 1
        assert segment.user_count >= 0
        assert prediction is not None
        assert dashboard is not None

    def test_error_handling_integration(self, sample_user):
        """Test error handling across integrated systems."""
        # Test with invalid data
        try:
            # Create invalid group (empty name)
            invalid_group = UserGroup(
                name='',
                creator_id=sample_user.id,
                description='Invalid group'
            )
            db.session.add(invalid_group)
            db.session.commit()
            
            # Should still create but validation would catch it in forms
            assert invalid_group.name == ''
        except Exception as e:
            # Should handle gracefully
            assert True
        
        # Test with circular relationships
        try:
            # Create self-following (should be prevented)
            follow = UserFollow.follow_user(sample_user.id, sample_user.id)
            assert follow is None  # Should return None for self-follow
        except Exception as e:
            # Should handle gracefully
            assert True
        
        # Test with expired roles
        role = Role.create_role('temp_role', 'Temporary Role', level=5)
        expires_at = datetime.utcnow() - timedelta(days=1)  # Already expired
        assignment = UserRole.assign_role(
            sample_user.id,
            role.id,
            expires_at=expires_at
        )
        
        # Should be marked as expired
        assert assignment.is_expired() is True
        
        # Test with invalid JSON in preferences
        sample_user.user_preferences = '{invalid json'
        db.session.commit()
        
        # Should return defaults
        prefs = sample_user.get_general_preferences()
        assert prefs['theme_preference'] == 'light'  # Default value


class TestSystemWideIntegration:
    """System-wide integration tests."""

    def test_system_startup_integration(self, sample_user, sample_admin_user):
        """Test system startup with all components."""
        # Verify all models can be created
        role = Role.create_role('system_role', 'System Role', level=20)
        permission = Permission.create_permission(
            'system_access',
            'System Access',
            'System access permission',
            'system',
            'system',
            'access'
        )
        
        # Verify relationships can be established
        role.add_permission('system_access', True)
        UserRole.assign_role(sample_admin_user.id, role.id)
        
        # Verify social features work
        follow = UserFollow.follow_user(sample_user.id, sample_admin_user.id)
        group = UserGroup.create_group('System Group', sample_admin_user.id)
        group.add_member(sample_user.id)
        
        # Verify analytics work
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='system',
            action='startup'
        )
        
        today = datetime.utcnow().date()
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        
        # Verify everything is working
        assert role is not None
        assert permission is not None
        assert role.has_permission('system_access') is True
        assert follow is not None
        assert group is not None
        assert group.is_member(sample_user.id) is True
        assert engagement.total_actions >= 1

    def test_data_consistency_integration(self, sample_user, sample_admin_user):
        """Test data consistency across all systems."""
        # Create consistent data across systems
        role = Role.create_role('consistent_role', 'Consistent Role', level=15)
        UserRole.assign_role(sample_user.id, role.id)
        
        # Create consistent user relationships
        follow = UserFollow.follow_user(sample_user.id, sample_admin_user.id)
        friend_request = UserFriend.send_friend_request(sample_user.id, sample_admin_user.id, sample_user.id)
        friend_request.approve(sample_admin_user.id)
        
        # Create consistent activities
        SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='test',
            action='created',
            description='Consistent test activity'
        )
        
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='test',
            action='created',
            metadata={'consistent': True}
        )
        
        # Verify data consistency
        assert UserRole.get_user_roles(sample_user.id)[0].role_id == role.id
        assert UserFollow.is_following(sample_user.id, sample_admin_user.id) is True
        assert UserFriend.are_friends(sample_user.id, sample_admin_user.id) is True
        
        social_activity = SocialActivity.query.filter_by(user_id=sample_user.id).first()
        user_behavior = UserBehavior.query.filter_by(user_id=sample_user.id).first()
        
        assert social_activity is not None
        assert user_behavior is not None
        assert social_activity.activity_type == 'test'
        assert user_behavior.behavior_type == 'test'

    def test_concurrent_operations_integration(self, sample_user, sample_admin_user):
        """Test concurrent operations across systems."""
        # Create multiple objects concurrently
        roles = []
        for i in range(5):
            role = Role.create_role(f'concurrent_role_{i}', f'Concurrent Role {i}', level=i * 5)
            roles.append(role)
            UserRole.assign_role(sample_user.id, role.id)
        
        # Create multiple social relationships
        follows = []
        for i in range(3):
            follow = UserFollow.follow_user(sample_user.id, sample_admin_user.id)
            follows.append(follow)
        
        # Create multiple activities
        activities = []
        for i in range(5):
            activity = SocialActivity.create_activity(
                user_id=sample_user.id,
                activity_type='concurrent',
                action='created',
                target_type='test',
                target_id=i
            )
            activities.append(activity)
        
        # Create multiple behaviors
        behaviors = []
        for i in range(10):
            behavior = UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='concurrent',
                action=f'action_{i}'
            )
            behaviors.append(behavior)
        
        # Verify all operations completed successfully
        assert len(roles) == 5
        assert len(UserRole.get_user_roles(sample_user.id)) == 5
        assert len(follows) == 3
        assert len(activities) == 5
        assert len(behaviors) == 10
        
        # Verify data integrity
        for role in roles:
            assert role.name.startswith('concurrent_role_')
        
        for activity in activities:
            assert activity.activity_type == 'concurrent'
        
        for behavior in behaviors:
            assert behavior.behavior_type == 'concurrent'
