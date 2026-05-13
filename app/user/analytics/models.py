"""
Advanced User Analytics Models

This module contains models for advanced user analytics including:
- User behavior analytics
- Engagement metrics tracking
- User performance dashboards
- Predictive analytics
- User segmentation
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import User
import json


class UserBehavior(db.Model):
    """Model for tracking user behavior analytics"""
    __tablename__ = 'user_behaviors'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    behavior_type = db.Column(db.String(50), nullable=False)  # login, post, comment, like, share, view
    target_type = db.Column(db.String(50))  # post, comment, user, profile
    target_id = db.Column(db.Integer)
    action = db.Column(db.String(100), nullable=False)  # created, updated, deleted, viewed, clicked
    session_id = db.Column(db.String(255))  # Session identifier
    ip_address = db.Column(db.String(45))  # IP address for tracking
    user_agent = db.Column(db.Text)  # User agent string
    referrer = db.Column(db.String(500))  # Referrer URL
    duration = db.Column(db.Integer)  # Duration in seconds
    behavior_metadata = db.Column(db.JSON)  # Additional behavior data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    user = db.relationship('User', backref='behaviors')
    
    def __repr__(self):
        return f'<UserBehavior {self.user.username} - {self.behavior_type}: {self.action}>'
    
    @staticmethod
    def track_behavior(user_id, behavior_type, action, target_type=None, target_id=None, 
                      session_id=None, ip_address=None, user_agent=None, referrer=None, 
                      duration=None, behavior_metadata=None):
        """Track user behavior"""
        behavior = UserBehavior(
            user_id=user_id,
            behavior_type=behavior_type,
            action=action,
            target_type=target_type,
            target_id=target_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            duration=duration,
            behavior_metadata=behavior_metadata
        )
        
        db.session.add(behavior)
        db.session.commit()
        return behavior
    
    @staticmethod
    def get_user_behaviors(user_id, behavior_type=None, days=30, limit=100):
        """Get user behaviors for analytics"""
        query = UserBehavior.query.filter_by(user_id=user_id)
        
        if behavior_type:
            query = query.filter_by(behavior_type=behavior_type)
        
        # Filter by date range
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(UserBehavior.created_at >= since_date)
        
        return query.order_by(UserBehavior.created_at.desc()).limit(limit).all()


class UserEngagement(db.Model):
    """Model for user engagement metrics"""
    __tablename__ = 'user_engagements'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)  # Daily aggregation
    total_actions = db.Column(db.Integer, default=0)
    login_count = db.Column(db.Integer, default=0)
    post_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    session_duration = db.Column(db.Integer, default=0)  # Total session duration in seconds
    pages_viewed = db.Column(db.Integer, default=0)
    bounce_rate = db.Column(db.Float, default=0.0)  # Bounce rate percentage
    engagement_score = db.Column(db.Float, default=0.0)  # Overall engagement score
    engagement_metadata = db.Column(db.JSON)  # Additional engagement data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationships
    user = db.relationship('User', backref='engagements')
    
    # Unique constraint for daily aggregation
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_daily_engagement'),)
    
    def __repr__(self):
        return f'<UserEngagement {self.user.username} - {self.date}: {self.engagement_score}>'
    
    @staticmethod
    def calculate_daily_engagement(user_id, date=None):
        """Calculate daily engagement metrics for a user"""
        if not date:
            date = datetime.utcnow().date()
        
        # Get or create engagement record
        engagement = UserEngagement.query.filter_by(user_id=user_id, date=date).first()
        if not engagement:
            engagement = UserEngagement(user_id=user_id, date=date)
            db.session.add(engagement)
        
        # Get behaviors for the day
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        behaviors = UserBehavior.query.filter(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= start_datetime,
            UserBehavior.created_at < end_datetime
        ).all()
        
        # Calculate metrics
        engagement.total_actions = len(behaviors)
        engagement.login_count = len([b for b in behaviors if b.behavior_type == 'login'])
        engagement.post_count = len([b for b in behaviors if b.behavior_type == 'post'])
        engagement.comment_count = len([b for b in behaviors if b.behavior_type == 'comment'])
        engagement.like_count = len([b for b in behaviors if b.behavior_type == 'like'])
        engagement.share_count = len([b for b in behaviors if b.behavior_type == 'share'])
        engagement.view_count = len([b for b in behaviors if b.behavior_type == 'view'])
        
        # Calculate session duration
        session_durations = [b.duration for b in behaviors if b.duration is not None]
        engagement.session_duration = sum(session_durations) if session_durations else 0
        
        # Calculate pages viewed (unique pages)
        unique_pages = set()
        for behavior in behaviors:
            if behavior.target_type and behavior.target_id:
                unique_pages.add(f"{behavior.target_type}_{behavior.target_id}")
        engagement.pages_viewed = len(unique_pages)
        
        # Calculate bounce rate (sessions with only one page view)
        sessions = {}
        for behavior in behaviors:
            session_id = behavior.session_id
            if session_id:
                if session_id not in sessions:
                    sessions[session_id] = []
                sessions[session_id].append(behavior)
        
        single_page_sessions = len([s for s in sessions.values() if len(set(f"{b.target_type}_{b.target_id}" for b in s)) == 1])
        total_sessions = len(sessions)
        engagement.bounce_rate = (single_page_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Calculate engagement score (weighted formula)
        engagement.engagement_score = (
            engagement.login_count * 1 +
            engagement.post_count * 5 +
            engagement.comment_count * 3 +
            engagement.like_count * 2 +
            engagement.share_count * 4 +
            engagement.view_count * 0.5
        )
        
        db.session.commit()
        return engagement
    
    @staticmethod
    def get_engagement_trend(user_id, days=30):
        """Get engagement trend for a user"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        engagements = UserEngagement.query.filter(
            UserEngagement.user_id == user_id,
            UserEngagement.date >= start_date,
            UserEngagement.date <= end_date
        ).order_by(UserEngagement.date.asc()).all()
        
        return engagements


class UserPerformance(db.Model):
    """Model for user performance metrics"""
    __tablename__ = 'user_performances'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)  # posts, comments, likes, engagement, growth
    metric_name = db.Column(db.String(100), nullable=False)  # daily_posts, weekly_comments, etc.
    metric_value = db.Column(db.Float, nullable=False)
    previous_value = db.Column(db.Float)  # Previous period value for comparison
    change_percentage = db.Column(db.Float)  # Percentage change
    period = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    performance_metadata = db.Column(db.JSON)  # Additional performance data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    user = db.relationship('User', backref='performances')
    
    def __repr__(self):
        return f'<UserPerformance {self.user.username} - {self.metric_name}: {self.metric_value}>'
    
    @staticmethod
    def calculate_performance_metrics(user_id, period='weekly', end_date=None):
        """Calculate performance metrics for a user"""
        if not end_date:
            end_date = datetime.utcnow().date()
        
        # Determine period start date
        if period == 'daily':
            start_date = end_date - timedelta(days=1)
        elif period == 'weekly':
            start_date = end_date - timedelta(weeks=1)
        elif period == 'monthly':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(weeks=1)
        
        # Calculate various metrics
        metrics = []
        
        # Posts metric
        posts_count = UserBehavior.query.filter(
            UserBehavior.user_id == user_id,
            UserBehavior.behavior_type == 'post',
            UserBehavior.created_at >= start_date,
            UserBehavior.created_at < end_date + timedelta(days=1)
        ).count()
        
        metrics.append(UserPerformance(
            user_id=user_id,
            metric_type='posts',
            metric_name=f'{period}_posts',
            metric_value=float(posts_count),
            period=period,
            period_start=start_date,
            period_end=end_date
        ))
        
        # Comments metric
        comments_count = UserBehavior.query.filter(
            UserBehavior.user_id == user_id,
            UserBehavior.behavior_type == 'comment',
            UserBehavior.created_at >= start_date,
            UserBehavior.created_at < end_date + timedelta(days=1)
        ).count()
        
        metrics.append(UserPerformance(
            user_id=user_id,
            metric_type='comments',
            metric_name=f'{period}_comments',
            metric_value=float(comments_count),
            period=period,
            period_start=start_date,
            period_end=end_date
        ))
        
        # Engagement metric
        engagement = UserEngagement.query.filter(
            UserEngagement.user_id == user_id,
            UserEngagement.date >= start_date,
            UserEngagement.date <= end_date
        ).all()
        
        total_engagement = sum(e.engagement_score for e in engagement)
        avg_engagement = total_engagement / len(engagement) if engagement else 0
        
        metrics.append(UserPerformance(
            user_id=user_id,
            metric_type='engagement',
            metric_name=f'{period}_engagement_avg',
            metric_value=avg_engagement,
            period=period,
            period_start=start_date,
            period_end=end_date
        ))
        
        # Save all metrics
        for metric in metrics:
            db.session.add(metric)
        
        db.session.commit()
        return metrics


class UserSegment(db.Model):
    """Model for user segmentation"""
    __tablename__ = 'user_segments'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    segment_type = db.Column(db.String(50), nullable=False)  # activity, engagement, behavior, custom
    criteria = db.Column(db.JSON, nullable=False)  # Segmentation criteria
    user_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', secondary='segment_users', backref='segments')
    
    def __repr__(self):
        return f'<UserSegment {self.name}: {self.user_count} users>'
    
    @staticmethod
    def create_segment(name, description, segment_type, criteria):
        """Create a new user segment"""
        segment = UserSegment(
            name=name,
            description=description,
            segment_type=segment_type,
            criteria=criteria
        )
        
        db.session.add(segment)
        db.session.commit()
        
        # Apply segmentation logic
        segment.apply_segmentation()
        
        return segment
    
    def apply_segmentation(self):
        """Apply segmentation criteria to users"""
        # Clear existing segment users
        SegmentUser.query.filter_by(segment_id=self.id).delete()
        
        # Apply criteria (simplified example)
        users = User.query.all()
        matched_users = []
        
        for user in users:
            if self.matches_criteria(user):
                matched_users.append(user)
        
        # Add matched users to segment
        for user in matched_users:
            segment_user = SegmentUser(segment_id=self.id, user_id=user.id)
            db.session.add(segment_user)
        
        # Update user count
        self.user_count = len(matched_users)
        self.updated_at = datetime.utcnow()
        
        db.session.commit()
        return matched_users
    
    def matches_criteria(self, user):
        """Check if user matches segmentation criteria"""
        criteria = self.criteria
        
        # Example criteria matching (would be more sophisticated in production)
        if self.segment_type == 'activity':
            min_posts = criteria.get('min_posts', 0)
            min_comments = criteria.get('min_comments', 0)
            
            user_posts = UserBehavior.query.filter_by(
                user_id=user.id, behavior_type='post'
            ).count()
            user_comments = UserBehavior.query.filter_by(
                user_id=user.id, behavior_type='comment'
            ).count()
            
            return user_posts >= min_posts and user_comments >= min_comments
        
        elif self.segment_type == 'engagement':
            min_engagement = criteria.get('min_engagement_score', 0)
            
            latest_engagement = UserEngagement.query.filter_by(user_id=user.id).order_by(
                UserEngagement.date.desc()
            ).first()
            
            return latest_engagement and latest_engagement.engagement_score >= min_engagement
        
        return False


class SegmentUser(db.Model):
    """Model for segment user relationships"""
    __tablename__ = 'segment_users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    segment_id = db.Column(db.Integer, db.ForeignKey('user_segments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    segment = db.relationship('UserSegment', backref='segment_users')
    user = db.relationship('User', backref='segment_memberships')
    
    # Unique constraint to prevent duplicates
    __table_args__ = (db.UniqueConstraint('segment_id', 'user_id', name='unique_segment_user'),)


class UserPrediction(db.Model):
    """Model for user predictive analytics"""
    __tablename__ = 'user_predictions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prediction_type = db.Column(db.String(50), nullable=False)  # churn, engagement, growth, activity
    prediction_value = db.Column(db.Float, nullable=False)  # Prediction score (0-1)
    confidence = db.Column(db.Float, nullable=False)  # Confidence score (0-1)
    prediction_date = db.Column(db.Date, nullable=False)  # Date prediction was made
    target_date = db.Column(db.Date, nullable=False)  # Date prediction applies to
    actual_value = db.Column(db.Float)  # Actual value when known
    prediction_metadata = db.Column(db.JSON)  # Additional prediction data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationships
    user = db.relationship('User', backref='predictions')
    
    def __repr__(self):
        return f'<UserPrediction {self.user.username} - {self.prediction_type}: {self.prediction_value}>'
    
    @staticmethod
    def create_prediction(user_id, prediction_type, prediction_value, confidence, 
                        target_date, prediction_metadata=None):
        """Create a new user prediction"""
        prediction = UserPrediction(
            user_id=user_id,
            prediction_type=prediction_type,
            prediction_value=prediction_value,
            confidence=confidence,
            prediction_date=datetime.utcnow().date(),
            target_date=target_date,
            prediction_metadata=prediction_metadata
        )
        
        db.session.add(prediction)
        db.session.commit()
        return prediction
    
    @staticmethod
    def predict_churn_risk(user_id, days=30):
        """Predict churn risk for a user (simplified example)"""
        # Get recent engagement data
        recent_engagement = UserEngagement.query.filter(
            UserEngagement.user_id == user_id,
            UserEngagement.date >= datetime.utcnow().date() - timedelta(days=days)
        ).all()
        
        if not recent_engagement:
            return UserPrediction.create_prediction(
                user_id=user_id,
                prediction_type='churn',
                prediction_value=0.8,  # High churn risk
                confidence=0.7,
                target_date=datetime.utcnow().date() + timedelta(days=30),
                metadata={'reason': 'no_recent_engagement'}
            )
        
        # Calculate average engagement
        avg_engagement = sum(e.engagement_score for e in recent_engagement) / len(recent_engagement)
        
        # Simple churn prediction logic
        if avg_engagement < 5:
            churn_risk = 0.7
            confidence = 0.6
        elif avg_engagement < 10:
            churn_risk = 0.4
            confidence = 0.5
        else:
            churn_risk = 0.1
            confidence = 0.7
        
        return UserPrediction.create_prediction(
            user_id=user_id,
            prediction_type='churn',
            prediction_value=churn_risk,
            confidence=confidence,
            target_date=datetime.utcnow().date() + timedelta(days=30),
            metadata={'avg_engagement': avg_engagement, 'days_analyzed': days}
        )


class UserDashboard(db.Model):
    """Model for user dashboard configurations and data"""
    __tablename__ = 'user_dashboards'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dashboard_type = db.Column(db.String(50), default='custom')  # overview, activity, engagement, custom
    layout = db.Column(db.JSON)  # Dashboard layout configuration
    widgets = db.Column(db.JSON)  # Dashboard widgets configuration
    filters = db.Column(db.JSON)  # Dashboard filters
    is_default = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationships
    user = db.relationship('User', backref='dashboards')
    
    def __repr__(self):
        return f'<UserDashboard {self.user.username} - {self.name}>'
    
    @staticmethod
    def create_dashboard(user_id, name, dashboard_type='custom', layout=None, widgets=None, filters=None):
        """Create a new user dashboard"""
        dashboard = UserDashboard(
            user_id=user_id,
            name=name,
            dashboard_type=dashboard_type,
            layout=layout or UserDashboard.get_default_layout(),
            widgets=widgets or UserDashboard.get_default_widgets(),
            filters=filters or {}
        )
        
        db.session.add(dashboard)
        db.session.commit()
        return dashboard
    
    @staticmethod
    def get_default_layout():
        """Get default dashboard layout"""
        return {
            'columns': 3,
            'widgets': [
                {'id': 'overview_stats', 'column': 1, 'row': 1, 'height': 2},
                {'id': 'activity_chart', 'column': 2, 'row': 1, 'height': 2},
                {'id': 'engagement_metrics', 'column': 3, 'row': 1, 'height': 1},
                {'id': 'recent_activity', 'column': 3, 'row': 2, 'height': 1}
            ]
        }
    
    @staticmethod
    def get_default_widgets():
        """Get default dashboard widgets"""
        return {
            'overview_stats': {
                'type': 'stats',
                'title': 'Overview',
                'metrics': ['posts', 'comments', 'likes', 'engagement']
            },
            'activity_chart': {
                'type': 'chart',
                'title': 'Activity Trend',
                'chart_type': 'line',
                'data_source': 'user_behaviors'
            },
            'engagement_metrics': {
                'type': 'metrics',
                'title': 'Engagement',
                'metrics': ['engagement_score', 'session_duration', 'bounce_rate']
            },
            'recent_activity': {
                'type': 'list',
                'title': 'Recent Activity',
                'limit': 10
            }
        }
