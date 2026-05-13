"""
Unit tests for the User Analytics System
"""

import pytest
from datetime import datetime, timedelta
from app.user.analytics.models import UserBehavior, UserEngagement, UserPerformance, UserSegment, UserPrediction, UserDashboard, SegmentUser


class TestUserBehavior:
    """Test suite for user behavior functionality."""

    def test_track_behavior(self, sample_user):
        """Test tracking user behavior."""
        behavior = UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='login',
            action='logged_in',
            target_type='user',
            target_id=sample_user.id,
            session_id='test_session_123',
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0',
            referrer='https://example.com',
            duration=120,
            metadata={'login_method': 'password'}
        )
        
        assert behavior is not None
        assert behavior.user_id == sample_user.id
        assert behavior.behavior_type == 'login'
        assert behavior.action == 'logged_in'
        assert behavior.target_type == 'user'
        assert behavior.target_id == sample_user.id
        assert behavior.session_id == 'test_session_123'
        assert behavior.ip_address == '127.0.0.1'
        assert behavior.user_agent == 'Mozilla/5.0'
        assert behavior.referrer == 'https://example.com'
        assert behavior.duration == 120
        assert behavior.metadata['login_method'] == 'password'

    def test_track_behavior_minimal(self, sample_user):
        """Test tracking behavior with minimal data."""
        behavior = UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='view',
            action='viewed_page'
        )
        
        assert behavior is not None
        assert behavior.user_id == sample_user.id
        assert behavior.behavior_type == 'view'
        assert behavior.action == 'viewed_page'
        assert behavior.target_type is None
        assert behavior.target_id is None
        assert behavior.session_id is None
        assert behavior.ip_address is None

    def test_get_user_behaviors(self, sample_user):
        """Test getting user behaviors."""
        # Create multiple behaviors
        behaviors_data = [
            ('login', 'logged_in'),
            ('post', 'created'),
            ('comment', 'created'),
            ('view', 'viewed_page'),
            ('logout', 'logged_out')
        ]
        
        for behavior_type, action in behaviors_data:
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type=behavior_type,
                action=action
            )
        
        # Get all behaviors
        all_behaviors = UserBehavior.get_user_behaviors(sample_user.id)
        assert len(all_behaviors) == 5
        
        # Get behaviors by type
        login_behaviors = UserBehavior.get_user_behaviors(sample_user.id, behavior_type='login')
        assert len(login_behaviors) == 1
        assert login_behaviors[0].behavior_type == 'login'

    def test_get_user_behaviors_with_date_range(self, sample_user):
        """Test getting user behaviors with date range."""
        # Create behaviors with different dates
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        # Create behavior today
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='login',
            action='logged_in',
            created_at=today
        )
        
        # Create behavior yesterday
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='post',
            action='created',
            created_at=yesterday
        )
        
        # Create behavior a week ago
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='comment',
            action='created',
            created_at=week_ago
        )
        
        # Get behaviors from last 3 days
        recent_behaviors = UserBehavior.get_user_behaviors(sample_user.id, days=3)
        assert len(recent_behaviors) == 2
        
        # Get behaviors from last 10 days
        all_behaviors = UserBehavior.get_user_behaviors(sample_user.id, days=10)
        assert len(all_behaviors) == 3

    def test_behavior_types(self, sample_user):
        """Test different behavior types."""
        behavior_types = ['login', 'logout', 'post', 'comment', 'like', 'share', 'view', 'search']
        
        for behavior_type in behavior_types:
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type=behavior_type,
                action='test_action'
            )
        
        # Count behaviors by type
        for behavior_type in behavior_types:
            behaviors = UserBehavior.get_user_behaviors(sample_user.id, behavior_type=behavior_type)
            assert len(behaviors) == 1
            assert behaviors[0].behavior_type == behavior_type

    def test_behavior_metadata(self, sample_user):
        """Test behavior metadata handling."""
        metadata = {
            'device_type': 'mobile',
            'browser': 'chrome',
            'location': 'US',
            'session_length': 300,
            'page_views': 5
        }
        
        behavior = UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='session',
            action='started',
            metadata=metadata
        )
        
        assert behavior.metadata['device_type'] == 'mobile'
        assert behavior.metadata['browser'] == 'chrome'
        assert behavior.metadata['location'] == 'US'
        assert behavior.metadata['session_length'] == 300
        assert behavior.metadata['page_views'] == 5


class TestUserEngagement:
    """Test suite for user engagement functionality."""

    def test_calculate_daily_engagement(self, sample_user):
        """Test calculating daily engagement."""
        # Create some behaviors for today
        today = datetime.utcnow().date()
        start_datetime = datetime.combine(today, datetime.min.time())
        
        # Create login behavior
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='login',
            action='logged_in',
            created_at=start_datetime + timedelta(hours=9)
        )
        
        # Create post behavior
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='post',
            action='created',
            created_at=start_datetime + timedelta(hours=10)
        )
        
        # Create comment behavior
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='comment',
            action='created',
            created_at=start_datetime + timedelta(hours=11)
        )
        
        # Calculate engagement
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        
        assert engagement is not None
        assert engagement.user_id == sample_user.id
        assert engagement.date == today
        assert engagement.total_actions == 3
        assert engagement.login_count == 1
        assert engagement.post_count == 1
        assert engagement.comment_count == 1
        assert engagement.engagement_score >= 0

    def test_calculate_engagement_score(self, sample_user):
        """Test engagement score calculation."""
        today = datetime.utcnow().date()
        start_datetime = datetime.combine(today, datetime.min.time())
        
        # Create high-engagement behaviors
        for i in range(10):
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='post',
                action='created',
                created_at=start_datetime + timedelta(hours=i)
            )
        
        # Create session with duration
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='session',
            action='started',
            duration=3600,  # 1 hour
            created_at=start_datetime + timedelta(hours=1)
        )
        
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        
        # Should have high engagement score due to posts and session duration
        assert engagement.engagement_score > 10

    def test_get_engagement_trend(self, sample_user):
        """Test getting engagement trend."""
        # Create engagement data for multiple days
        for days_ago in range(7, 0, -1):
            date = datetime.utcnow().date() - timedelta(days=days_ago)
            UserEngagement.calculate_daily_engagement(sample_user.id, date)
        
        # Get trend
        trend = UserEngagement.get_engagement_trend(sample_user.id, days=7)
        
        assert len(trend) == 7
        
        # Check dates are in ascending order
        for i in range(1, len(trend)):
            assert trend[i].date >= trend[i-1].date

    def test_engagement_metrics(self, sample_user):
        """Test various engagement metrics."""
        today = datetime.utcnow().date()
        start_datetime = datetime.combine(today, datetime.min.time())
        
        # Create different types of behaviors
        behaviors = [
            ('login', 'logged_in', 2),
            ('post', 'created', 5),
            ('comment', 'created', 10),
            ('like', 'created', 15),
            ('share', 'created', 3),
            ('view', 'viewed_page', 20)
        ]
        
        for behavior_type, action, count in behaviors:
            for i in range(count):
                UserBehavior.track_behavior(
                    user_id=sample_user.id,
                    behavior_type=behavior_type,
                    action=action,
                    created_at=start_datetime + timedelta(hours=i)
                )
        
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        
        assert engagement.login_count == 2
        assert engagement.post_count == 5
        assert engagement.comment_count == 10
        assert engagement.like_count == 15
        assert engagement.share_count == 3
        assert engagement.view_count == 20
        assert engagement.total_actions == 55

    def test_session_duration_calculation(self, sample_user):
        """Test session duration calculation."""
        today = datetime.utcnow().date()
        start_datetime = datetime.combine(today, datetime.min.time())
        
        # Create session behaviors with durations
        session_durations = [300, 600, 900, 1200, 1800]  # seconds
        
        for i, duration in enumerate(session_durations):
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='session',
                action='active',
                session_id=f'session_{i}',
                duration=duration,
                created_at=start_datetime + timedelta(hours=i)
            )
        
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        
        # Should sum all session durations
        expected_total = sum(session_durations)
        assert engagement.session_duration == expected_total

    def test_bounce_rate_calculation(self, sample_user):
        """Test bounce rate calculation."""
        today = datetime.utcnow().date()
        start_datetime = datetime.combine(today, datetime.min.time())
        
        # Create single-page sessions (high bounce rate)
        for i in range(5):
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='view',
                action='viewed_page',
                session_id=f'session_{i}',
                target_type='page',
                target_id=1,  # Same page for all
                created_at=start_datetime + timedelta(hours=i)
            )
        
        # Create multi-page sessions (low bounce rate)
        for i in range(5, 10):
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='view',
                action='viewed_page',
                session_id=f'session_{i}',
                target_type='page',
                target_id=i,  # Different pages
                created_at=start_datetime + timedelta(hours=i)
            )
        
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        
        # Should have bounce rate of 0.5 (5 single-page out of 10 total)
        assert engagement.bounce_rate == 0.5


class TestUserPerformance:
    """Test suite for user performance functionality."""

    def test_calculate_performance_metrics(self, sample_user):
        """Test calculating performance metrics."""
        # Create some posts for testing
        today = datetime.utcnow().date()
        
        # Create posts in the last week
        for i in range(5):
            post_date = today - timedelta(days=i)
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='post',
                action='created',
                created_at=datetime.combine(post_date, datetime.min.time())
            )
        
        # Calculate weekly performance
        metrics = UserPerformance.calculate_performance_metrics(sample_user.id, 'weekly')
        
        assert len(metrics) >= 1
        
        # Check post count metric
        post_metric = next((m for m in metrics if m.metric_name == 'post_count'), None)
        assert post_metric is not None
        assert post_metric.metric_value == 5.0
        assert post_metric.period == 'weekly'

    def test_performance_change_calculation(self, sample_user):
        """Test performance change calculation."""
        # Create posts in current period
        today = datetime.utcnow().date()
        current_start = today - timedelta(days=7)
        
        for i in range(10):
            post_date = current_start + timedelta(days=i)
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='post',
                action='created',
                created_at=datetime.combine(post_date, datetime.min.time())
            )
        
        # Create posts in previous period
        previous_start = current_start - timedelta(days=7)
        
        for i in range(5):
            post_date = previous_start + timedelta(days=i)
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='post',
                action='created',
                created_at=datetime.combine(post_date, datetime.min.time())
            )
        
        metrics = UserPerformance.calculate_performance_metrics(sample_user.id, 'weekly')
        
        post_metric = next((m for m in metrics if m.metric_name == 'post_count'), None)
        assert post_metric is not None
        assert post_metric.metric_value == 10.0
        assert post_metric.previous_value == 5.0
        assert post_metric.change_percentage == 100.0  # 100% increase

    def test_different_periods(self, sample_user):
        """Test different performance periods."""
        today = datetime.utcnow().date()
        
        # Create posts over the last month
        for i in range(30):
            post_date = today - timedelta(days=i)
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='post',
                action='created',
                created_at=datetime.combine(post_date, datetime.min.time())
            )
        
        # Test different periods
        for period in ['daily', 'weekly', 'monthly']:
            metrics = UserPerformance.calculate_performance_metrics(sample_user.id, period)
            assert len(metrics) >= 1
            
            # Check that period is set correctly
            for metric in metrics:
                assert metric.period == period

    def test_performance_metric_types(self, sample_user):
        """Test different performance metric types."""
        today = datetime.utcnow().date()
        start_datetime = datetime.combine(today, datetime.min.time())
        
        # Create different types of behaviors
        behaviors = [
            ('post', 'created', 3),
            ('comment', 'created', 7),
            ('like', 'created', 12),
            ('share', 'created', 5)
        ]
        
        for behavior_type, action, count in behaviors:
            for i in range(count):
                UserBehavior.track_behavior(
                    user_id=sample_user.id,
                    behavior_type=behavior_type,
                    action=action,
                    created_at=start_datetime + timedelta(hours=i)
                )
        
        metrics = UserPerformance.calculate_performance_metrics(sample_user.id, 'daily')
        
        # Check that we have metrics for different types
        metric_names = [m.metric_name for m in metrics]
        assert 'post_count' in metric_names
        assert 'comment_count' in metric_names
        assert 'like_count' in metric_names
        assert 'share_count' in metric_names


class TestUserSegment:
    """Test suite for user segmentation functionality."""

    def test_create_segment(self, sample_user):
        """Test creating a user segment."""
        segment = UserSegment.create_segment(
            name='Active Users',
            description='Users with 5+ posts',
            segment_type='activity',
            criteria={'min_posts': 5}
        )
        
        assert segment is not None
        assert segment.name == 'Active Users'
        assert segment.description == 'Users with 5+ posts'
        assert segment.segment_type == 'activity'
        assert segment.criteria['min_posts'] == 5
        assert segment.is_active is True

    def test_apply_segmentation_activity(self, sample_user):
        """Test applying activity-based segmentation."""
        # Create some posts for the user
        for i in range(10):
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='post',
                action='created'
            )
        
        # Create segment with min_posts criteria
        segment = UserSegment.create_segment(
            name='Active Users',
            segment_type='activity',
            criteria={'min_posts': 5}
        )
        
        # Apply segmentation
        matched_users = segment.apply_segmentation()
        
        # User should match (has 10 posts, min is 5)
        assert len(matched_users) == 1
        assert matched_users[0].id == sample_user.id
        assert segment.user_count == 1

    def test_apply_segmentation_engagement(self, sample_user):
        """Test applying engagement-based segmentation."""
        # Create engagement data
        today = datetime.utcnow().date()
        engagement = UserEngagement(
            user_id=sample_user.id,
            date=today,
            engagement_score=75.0
        )
        db.session.add(engagement)
        db.session.commit()
        
        # Create segment with engagement criteria
        segment = UserSegment.create_segment(
            name='High Engagement Users',
            segment_type='engagement',
            criteria={'min_engagement_score': 50.0}
        )
        
        # Apply segmentation
        matched_users = segment.apply_segmentation()
        
        # User should match (has 75.0 score, min is 50.0)
        assert len(matched_users) == 1
        assert matched_users[0].id == sample_user.id
        assert segment.user_count == 1

    def test_matches_criteria_activity(self, sample_user):
        """Test matching activity criteria."""
        segment = UserSegment(
            name='Test Segment',
            segment_type='activity',
            criteria={'min_posts': 5, 'max_posts': 15}
        )
        
        # Create 10 posts (should match)
        for i in range(10):
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='post',
                action='created'
            )
        
        assert segment.matches_criteria(sample_user) is True
        
        # Create 20 more posts (should not match)
        for i in range(20):
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='post',
                action='created'
            )
        
        assert segment.matches_criteria(sample_user) is False

    def test_matches_criteria_demographic(self, sample_user):
        """Test matching demographic criteria."""
        # Test registration days criteria
        segment = UserSegment(
            name='Old Users',
            segment_type='demographic',
            criteria={'min_registration_days': 30}
        )
        
        # User was just created, should not match
        assert segment.matches_criteria(sample_user) is False
        
        # Update user creation date to 60 days ago
        sample_user.created_at = datetime.utcnow() - timedelta(days=60)
        db.session.commit()
        
        # Now should match
        assert segment.matches_criteria(sample_user) is True

    def test_segment_user_relationship(self, sample_user, sample_user_segment):
        """Test segment-user relationship."""
        # Apply segmentation to create relationship
        sample_user_segment.apply_segmentation()
        
        # Check relationship exists
        segment_user = SegmentUser.query.filter_by(
            segment_id=sample_user_segment.id,
            user_id=sample_user.id
        ).first()
        
        assert segment_user is not None
        assert segment_user.segment_id == sample_user_segment.id
        assert segment_user.user_id == sample_user.id


class TestUserPrediction:
    """Test suite for user prediction functionality."""

    def test_predict_churn_risk(self, sample_user):
        """Test churn risk prediction."""
        # Create some engagement data
        today = datetime.utcnow().date()
        for days_ago in range(30):
            date = today - timedelta(days=days_ago)
            engagement = UserEngagement(
                user_id=sample_user.id,
                date=date,
                engagement_score=20.0  # Low engagement
            )
            db.session.add(engagement)
        db.session.commit()
        
        # Predict churn risk
        prediction = UserPrediction.predict_churn_risk(sample_user.id, 30)
        
        assert prediction is not None
        assert prediction.user_id == sample_user.id
        assert prediction.prediction_type == 'churn'
        assert 0.0 <= prediction.prediction_value <= 1.0
        assert prediction.confidence >= 0.0
        assert prediction.target_date == today + timedelta(days=30)

    def test_predict_engagement(self, sample_user):
        """Test engagement prediction."""
        # Create historical engagement data
        today = datetime.utcnow().date()
        for days_ago in range(90):
            date = today - timedelta(days=days_ago)
            engagement = UserEngagement(
                user_id=sample_user.id,
                date=date,
                engagement_score=50.0 + (days_ago * 0.5)  # Increasing trend
            )
            db.session.add(engagement)
        db.session.commit()
        
        # Predict future engagement
        prediction = UserPrediction.predict_engagement(sample_user.id, 30)
        
        assert prediction is not None
        assert prediction.user_id == sample_user.id
        assert prediction.prediction_type == 'engagement'
        assert prediction.prediction_value >= 0.0
        assert prediction.confidence >= 0.0

    def test_create_prediction(self, sample_user):
        """Test creating custom prediction."""
        target_date = datetime.utcnow().date() + timedelta(days=60)
        
        prediction = UserPrediction.create_prediction(
            user_id=sample_user.id,
            prediction_type='growth',
            prediction_value=0.75,
            confidence=0.8,
            target_date=target_date,
            metadata={'algorithm': 'custom', 'factors': ['posts', 'comments']}
        )
        
        assert prediction is not None
        assert prediction.user_id == sample_user.id
        assert prediction.prediction_type == 'growth'
        assert prediction.prediction_value == 0.75
        assert prediction.confidence == 0.8
        assert prediction.target_date == target_date
        assert prediction.metadata['algorithm'] == 'custom'

    def test_prediction_with_actual_value(self, sample_user):
        """Test prediction with actual value comparison."""
        target_date = datetime.utcnow().date() + timedelta(days=30)
        
        # Create prediction
        prediction = UserPrediction.create_prediction(
            user_id=sample_user.id,
            prediction_type='engagement',
            prediction_value=50.0,
            confidence=0.7,
            target_date=target_date
        )
        
        # Update with actual value
        prediction.actual_value = 55.0
        db.session.commit()
        
        assert prediction.actual_value == 55.0

    def test_prediction_metadata(self, sample_user):
        """Test prediction metadata handling."""
        metadata = {
            'algorithm': 'linear_regression',
            'features': ['post_count', 'comment_count', 'login_frequency'],
            'training_data_size': 1000,
            'model_version': '1.0',
            'accuracy': 0.85
        }
        
        prediction = UserPrediction.create_prediction(
            user_id=sample_user.id,
            prediction_type='churn',
            prediction_value=0.3,
            confidence=0.8,
            target_date=datetime.utcnow().date() + timedelta(days=30),
            metadata=metadata
        )
        
        assert prediction.metadata['algorithm'] == 'linear_regression'
        assert prediction.metadata['features'] == ['post_count', 'comment_count', 'login_frequency']
        assert prediction.metadata['training_data_size'] == 1000
        assert prediction.metadata['model_version'] == '1.0'
        assert prediction.metadata['accuracy'] == 0.85


class TestUserDashboard:
    """Test suite for user dashboard functionality."""

    def test_create_dashboard(self, sample_user):
        """Test creating a user dashboard."""
        dashboard = UserDashboard.create_dashboard(
            user_id=sample_user.id,
            name='My Analytics Dashboard',
            dashboard_type='custom',
            layout={'columns': 3, 'auto_refresh': True}
        )
        
        assert dashboard is not None
        assert dashboard.user_id == sample_user.id
        assert dashboard.name == 'My Analytics Dashboard'
        assert dashboard.dashboard_type == 'custom'
        assert dashboard.layout['columns'] == 3
        assert dashboard.layout['auto_refresh'] is True

    def test_get_default_widgets(self):
        """Test getting default widgets."""
        widgets = UserDashboard.get_default_widgets()
        
        assert 'widgets' in widgets
        assert len(widgets['widgets']) >= 1
        
        # Check default widget types
        widget_ids = [w['id'] for w in widgets['widgets']]
        assert 'recent_posts' in widget_ids
        assert 'user_stats' in widget_ids

    def test_get_dashboard_data(self, sample_user, sample_user_dashboard):
        """Test getting dashboard data."""
        # Create some data for the dashboard
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='login',
            action='logged_in'
        )
        
        # Get dashboard data
        dashboard_data = sample_user_dashboard.get_dashboard_data()
        
        assert 'widget_1' in dashboard_data
        assert 'widget_2' in dashboard_data
        assert 'widget_3' in dashboard_data

    def test_dashboard_widget_types(self, sample_user):
        """Test different dashboard widget types."""
        widget_configs = {
            'stats': {'title': 'Statistics', 'metrics': ['posts', 'comments']},
            'chart': {'title': 'Trends', 'chart_type': 'line'},
            'list': {'title': 'Activity', 'limit': 10}
        }
        
        for widget_type, config in widget_configs.items():
            widgets = {'widget_1': {'type': widget_type, **config}}
            
            dashboard = UserDashboard.create_dashboard(
                user_id=sample_user.id,
                name=f'{widget_type.title()} Dashboard',
                widgets=widgets
            )
            
            assert dashboard.widgets['widget_1']['type'] == widget_type
            assert dashboard.widgets['widget_1']['title'] == config['title']

    def test_dashboard_layout_options(self, sample_user):
        """Test different dashboard layout options."""
        layouts = [
            {'columns': 1, 'auto_refresh': False},
            {'columns': 2, 'auto_refresh': True, 'refresh_interval': 300},
            {'columns': 3, 'auto_refresh': True, 'refresh_interval': 600},
            {'columns': 4, 'auto_refresh': False}
        ]
        
        for layout in layouts:
            dashboard = UserDashboard.create_dashboard(
                user_id=sample_user.id,
                name=f'Layout {layout["columns"]} Columns',
                layout=layout
            )
            
            assert dashboard.layout['columns'] == layout['columns']
            assert dashboard.layout['auto_refresh'] == layout['auto_refresh']
            
            if layout.get('refresh_interval'):
                assert dashboard.layout['refresh_interval'] == layout['refresh_interval']


class TestUserAnalyticsIntegration:
    """Integration tests for user analytics system."""

    def test_complete_analytics_workflow(self, sample_user):
        """Test complete analytics workflow."""
        # Track user behaviors
        behaviors = [
            ('login', 'logged_in'),
            ('post', 'created'),
            ('comment', 'created'),
            ('like', 'created'),
            ('view', 'viewed_page')
        ]
        
        for behavior_type, action in behaviors:
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type=behavior_type,
                action=action
            )
        
        # Calculate engagement
        today = datetime.utcnow().date()
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        assert engagement.total_actions == 5
        
        # Calculate performance
        performance = UserPerformance.calculate_performance_metrics(sample_user.id, 'daily')
        assert len(performance) >= 1
        
        # Create segment
        segment = UserSegment.create_segment(
            name='Active Users',
            segment_type='activity',
            criteria={'min_posts': 1}
        )
        matched_users = segment.apply_segmentation()
        assert len(matched_users) == 1
        
        # Create prediction
        prediction = UserPrediction.create_prediction(
            user_id=sample_user.id,
            prediction_type='engagement',
            prediction_value=50.0,
            confidence=0.7,
            target_date=today + timedelta(days=30)
        )
        assert prediction is not None
        
        # Create dashboard
        dashboard = UserDashboard.create_dashboard(
            user_id=sample_user.id,
            name='Analytics Dashboard'
        )
        assert dashboard is not None

    def test_analytics_performance(self, sample_user):
        """Test performance of analytics operations."""
        import time
        
        start_time = time.time()
        
        # Create many behaviors
        for i in range(100):
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='test',
                action=f'action_{i}'
            )
        
        # Calculate engagement multiple times
        for i in range(10):
            UserEngagement.calculate_daily_engagement(sample_user.id)
        
        # Create multiple segments
        for i in range(5):
            UserSegment.create_segment(
                name=f'Segment {i}',
                segment_type='activity',
                criteria={'min_posts': i}
            )
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Should complete operations in reasonable time
        assert operation_time < 3.0, f"Operations took too long: {operation_time}s"

    def test_analytics_edge_cases(self, sample_user):
        """Test edge cases in analytics."""
        # Test with no data
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id)
        assert engagement.total_actions == 0
        assert engagement.engagement_score == 0.0
        
        # Test with extreme values
        UserBehavior.track_behavior(
            user_id=sample_user.id,
            behavior_type='test',
            action='test',
            duration=999999,  # Very large duration
            metadata={'very_long_string': 'x' * 10000}  # Very long metadata
        )
        
        behavior = UserBehavior.query.filter_by(user_id=sample_user.id).first()
        assert behavior.duration == 999999
        assert len(behavior.metadata['very_long_string']) == 10000
        
        # Test with future dates
        future_date = datetime.utcnow().date() + timedelta(days=30)
        prediction = UserPrediction.create_prediction(
            user_id=sample_user.id,
            prediction_type='test',
            prediction_value=0.5,
            target_date=future_date
        )
        assert prediction.target_date == future_date

    def test_analytics_data_integrity(self, sample_user):
        """Test analytics data integrity."""
        # Create behaviors with specific timestamps
        today = datetime.utcnow().date()
        
        for i in range(5):
            timestamp = datetime.combine(today, datetime.min.time()) + timedelta(hours=i)
            UserBehavior.track_behavior(
                user_id=sample_user.id,
                behavior_type='test',
                action='test',
                created_at=timestamp
            )
        
        # Calculate engagement
        engagement = UserEngagement.calculate_daily_engagement(sample_user.id, today)
        
        # Verify data integrity
        behaviors = UserBehavior.query.filter_by(user_id=sample_user.id).all()
        assert len(behaviors) == 5
        
        # Check timestamps are preserved
        for i, behavior in enumerate(behaviors):
            expected_hour = i
            actual_hour = behavior.created_at.hour
            assert actual_hour == expected_hour
