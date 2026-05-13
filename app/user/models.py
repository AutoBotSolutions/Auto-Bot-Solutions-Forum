"""
Missing User Management Models

This module implements the missing database models that are still marked as "NOT IMPLEMENTED"
in the completion report, including UserPreference, UserProfileTheme, UserSocialConnection, 
UserAnalytics, and UserRoleAssignment models.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import User
import json


class UserPreference(db.Model):
    """User preference management and storage model"""
    
    __tablename__ = 'user_preferences'
    __table_args__ = (db.UniqueConstraint('user_id', 'preference_type', name='unique_user_preference'), {'extend_existing': True})
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    preference_type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('preferences', lazy='dynamic', cascade='all, delete-orphan'))
    
        
    def __repr__(self):
        return f'<UserPreference {self.user_id}:{self.preference_type}>'
    
    @classmethod
    def get_preference(cls, user_id, preference_type):
        """Get a specific preference for a user"""
        preference = cls.query.filter_by(
            user_id=user_id,
            preference_type=preference_type
        ).first()
        return preference.value if preference else None
    
    @classmethod
    def set_preference(cls, user_id, preference_type, value):
        """Set a preference for a user"""
        preference = cls.query.filter_by(
            user_id=user_id,
            preference_type=preference_type
        ).first()
        
        if preference:
            preference.value = value
            preference.updated_at = datetime.utcnow()
        else:
            preference = cls(
                user_id=user_id,
                preference_type=preference_type,
                value=value
            )
            db.session.add(preference)
        
        db.session.commit()
        return preference
    
    @classmethod
    def get_all_preferences(cls, user_id):
        """Get all preferences for a user"""
        preferences = cls.query.filter_by(user_id=user_id).all()
        return {pref.preference_type: pref.value for pref in preferences}
    
    @classmethod
    def delete_preference(cls, user_id, preference_type):
        """Delete a preference for a user"""
        preference = cls.query.filter_by(
            user_id=user_id,
            preference_type=preference_type
        ).first()
        
        if preference:
            db.session.delete(preference)
            db.session.commit()
            return True
        return False


class UserProfileTheme(db.Model):
    """Profile theme and customization management model"""
    
    __tablename__ = 'user_profile_themes'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    css_variables = db.Column(db.JSON)  # CSS custom properties
    layout_config = db.Column(db.JSON)   # Layout configuration
    is_system_theme = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserProfileTheme {self.name}>'
    
    @classmethod
    def create_theme(cls, name, display_name, description=None, css_variables=None, layout_config=None, is_system_theme=False):
        """Create a new profile theme"""
        theme = cls(
            name=name,
            display_name=display_name,
            description=description,
            css_variables=css_variables or {},
            layout_config=layout_config or {},
            is_system_theme=is_system_theme
        )
        db.session.add(theme)
        db.session.commit()
        return theme
    
    @classmethod
    def get_theme(cls, theme_id):
        """Get a theme by ID"""
        return cls.query.get(theme_id)
    
    @classmethod
    def get_theme_by_name(cls, name):
        """Get a theme by name"""
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_all_themes(cls, active_only=True):
        """Get all themes"""
        query = cls.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(cls.display_name).all()
    
    @classmethod
    def get_system_themes(cls):
        """Get all system themes"""
        return cls.query.filter_by(is_system_theme=True, is_active=True).all()
    
    def update_theme(self, **kwargs):
        """Update theme properties"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def deactivate(self):
        """Deactivate the theme"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self


class UserSocialConnection(db.Model):
    """User social connections and following system model"""
    
    __tablename__ = 'user_social_connections'
    __table_args__ = (db.UniqueConstraint('user_id', 'connected_user_id', 'connection_type', name='unique_social_connection'), {'extend_existing': True})
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    connected_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    connection_type = db.Column(db.String(20), nullable=False)  # follow, friend, block, mute
    status = db.Column(db.String(20), default='active')  # active, pending, blocked
    privacy_settings = db.Column(db.JSON)  # Privacy settings for this connection
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('social_connections', lazy='dynamic', cascade='all, delete-orphan'))
    connected_user = db.relationship('User', foreign_keys=[connected_user_id], backref=db.backref('social_connections_received', lazy='dynamic', cascade='all, delete-orphan'))
    
        
    def __repr__(self):
        return f'<UserSocialConnection {self.user_id}->{self.connected_user_id}:{self.connection_type}>'
    
    @classmethod
    def create_connection(cls, user_id, connected_user_id, connection_type='follow', privacy_settings=None):
        """Create a new social connection"""
        # Check if connection already exists
        existing = cls.query.filter_by(
            user_id=user_id,
            connected_user_id=connected_user_id,
            connection_type=connection_type
        ).first()
        
        if existing:
            return existing
        
        connection = cls(
            user_id=user_id,
            connected_user_id=connected_user_id,
            connection_type=connection_type,
            privacy_settings=privacy_settings or {}
        )
        db.session.add(connection)
        db.session.commit()
        return connection
    
    @classmethod
    def get_connections(cls, user_id, connection_type=None, status='active'):
        """Get connections for a user"""
        query = cls.query.filter_by(user_id=user_id)
        if connection_type:
            query = query.filter_by(connection_type=connection_type)
        if status:
            query = query.filter_by(status=status)
        return query.all()
    
    @classmethod
    def get_following(cls, user_id):
        """Get users that this user follows"""
        return cls.query.filter_by(
            user_id=user_id,
            connection_type='follow',
            status='active'
        ).all()
    
    @classmethod
    def get_followers(cls, user_id):
        """Get users that follow this user"""
        return cls.query.filter_by(
            connected_user_id=user_id,
            connection_type='follow',
            status='active'
        ).all()
    
    @classmethod
    def get_friends(cls, user_id):
        """Get mutual friends (both follow each other)"""
        following = cls.query.filter_by(
            user_id=user_id,
            connection_type='follow',
            status='active'
        ).all()
        
        friends = []
        for follow in following:
            mutual = cls.query.filter_by(
                user_id=follow.connected_user_id,
                connected_user_id=user_id,
                connection_type='follow',
                status='active'
            ).first()
            if mutual:
                friends.append(follow)
        
        return friends
    
    @classmethod
    def is_connected(cls, user_id, connected_user_id, connection_type='follow'):
        """Check if two users are connected"""
        return cls.query.filter_by(
            user_id=user_id,
            connected_user_id=connected_user_id,
            connection_type=connection_type,
            status='active'
        ).first() is not None
    
    def update_status(self, status):
        """Update connection status"""
        self.status = status
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def update_privacy_settings(self, privacy_settings):
        """Update privacy settings for the connection"""
        self.privacy_settings = privacy_settings
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def delete_connection(self):
        """Delete the connection"""
        db.session.delete(self)
        db.session.commit()
        return True


class UserAnalytics(db.Model):
    """User analytics and behavior tracking model"""
    
    __tablename__ = 'user_analytics'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)  # login, post, comment, like, share, view
    value = db.Column(db.Float)  # Numeric value for the metric
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    metric_data = db.Column(db.JSON)  # Additional data for the metric
    session_id = db.Column(db.String(255))  # Session identifier
    ip_address = db.Column(db.String(45))  # IP address
    user_agent = db.Column(db.String(500))  # User agent string
    
    # Relationships
    user = db.relationship('User', backref=db.backref('analytics', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<UserAnalytics {self.user_id}:{self.metric_type}:{self.timestamp}>'
    
    @classmethod
    def track_metric(cls, user_id, metric_type, value=None, metric_data=None, session_id=None, ip_address=None, user_agent=None):
        """Track an analytics metric for a user"""
        analytics = cls(
            user_id=user_id,
            metric_type=metric_type,
            value=value,
            metric_data=metric_data or {},
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(analytics)
        db.session.commit()
        return analytics
    
    @classmethod
    def get_user_metrics(cls, user_id, metric_type=None, start_date=None, end_date=None, limit=None):
        """Get analytics metrics for a user"""
        query = cls.query.filter_by(user_id=user_id)
        
        if metric_type:
            query = query.filter_by(metric_type=metric_type)
        
        if start_date:
            query = query.filter(cls.timestamp >= start_date)
        
        if end_date:
            query = query.filter(cls.timestamp <= end_date)
        
        query = query.order_by(cls.timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_metric_summary(cls, user_id, metric_type, start_date=None, end_date=None):
        """Get summary statistics for a specific metric"""
        query = cls.query.filter_by(user_id=user_id, metric_type=metric_type)
        
        if start_date:
            query = query.filter(cls.timestamp >= start_date)
        
        if end_date:
            query = query.filter(cls.timestamp <= end_date)
        
        # Calculate summary statistics
        total_count = query.count()
        total_value = query.with_entities(db.func.sum(cls.value)).scalar() or 0
        avg_value = total_value / total_count if total_count > 0 else 0
        
        return {
            'metric_type': metric_type,
            'total_count': total_count,
            'total_value': total_value,
            'average_value': avg_value,
            'start_date': start_date,
            'end_date': end_date
        }
    
    @classmethod
    def get_activity_summary(cls, user_id, days=30):
        """Get activity summary for a user over a period"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all metrics in the period
        metrics = cls.query.filter(
            cls.user_id == user_id,
            cls.timestamp >= start_date
        ).all()
        
        # Group by metric type
        summary = {}
        for metric in metrics:
            if metric.metric_type not in summary:
                summary[metric.metric_type] = {
                    'count': 0,
                    'total_value': 0,
                    'last_activity': None
                }
            
            summary[metric.metric_type]['count'] += 1
            summary[metric.metric_type]['total_value'] += metric.value or 0
            
            if (summary[metric.metric_type]['last_activity'] is None or 
                metric.timestamp > summary[metric.metric_type]['last_activity']):
                summary[metric.metric_type]['last_activity'] = metric.timestamp
        
        return summary
    
    @classmethod
    def get_trending_metrics(cls, user_id, days=7):
        """Get trending metrics for a user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily metric counts
        daily_metrics = db.session.query(
            db.func.date(cls.timestamp).label('date'),
            cls.metric_type,
            db.func.count(cls.id).label('count')
        ).filter(
            cls.user_id == user_id,
            cls.timestamp >= start_date
        ).group_by(
            db.func.date(cls.timestamp),
            cls.metric_type
        ).order_by('date', 'metric_type').all()
        
        # Organize by metric type
        trending = {}
        for date, metric_type, count in daily_metrics:
            if metric_type not in trending:
                trending[metric_type] = []
            trending[metric_type].append({
                'date': date.isoformat(),
                'count': count
            })
        
        return trending
    
    @classmethod
    def cleanup_old_metrics(cls, days_to_keep=90):
        """Clean up old analytics metrics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted_count = cls.query.filter(cls.timestamp < cutoff_date).delete()
        db.session.commit()
        
        return deleted_count


class UserRoleAssignment(db.Model):
    """Advanced role management and assignment model"""
    
    __tablename__ = 'user_role_assignments'
    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', name='unique_user_role_assignment'), {'extend_existing': True})
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    assignment_reason = db.Column(db.Text)
    assignment_data = db.Column(db.JSON)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('role_assignments', lazy='dynamic', cascade='all, delete-orphan'))
    role = db.relationship('Role', foreign_keys=[role_id], backref=db.backref('user_assignments', lazy='dynamic', cascade='all, delete-orphan'))
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_id])
    
        
    def __repr__(self):
        return f'<UserRoleAssignment {self.user_id}:{self.role_id}>'
    
    @classmethod
    def assign_role(cls, user_id, role_id, assigned_by_id=None, expires_at=None, reason=None, assignment_data=None):
        """Assign a role to a user"""
        # Check if assignment already exists
        existing = cls.query.filter_by(
            user_id=user_id,
            role_id=role_id,
            is_active=True
        ).first()
        
        if existing:
            return existing
        
        assignment = cls(
            user_id=user_id,
            role_id=role_id,
            assigned_by_id=assigned_by_id,
            expires_at=expires_at,
            assignment_reason=reason,
            assignment_data=assignment_data or {}
        )
        db.session.add(assignment)
        db.session.commit()
        return assignment
    
    @classmethod
    def get_user_roles(cls, user_id, active_only=True):
        """Get all roles assigned to a user"""
        query = cls.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @classmethod
    def get_role_users(cls, role_id, active_only=True):
        """Get all users assigned to a role"""
        query = cls.query.filter_by(role_id=role_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @classmethod
    def has_role(cls, user_id, role_id):
        """Check if user has a specific role"""
        return cls.query.filter_by(
            user_id=user_id,
            role_id=role_id,
            is_active=True
        ).first() is not None
    
    @classmethod
    def remove_role(cls, user_id, role_id):
        """Remove a role from a user"""
        assignment = cls.query.filter_by(
            user_id=user_id,
            role_id=role_id,
            is_active=True
        ).first()
        
        if assignment:
            assignment.is_active = False
            db.session.commit()
            return True
        return False
    
    @classmethod
    def update_expiration(cls, user_id, role_id, expires_at):
        """Update role assignment expiration"""
        assignment = cls.query.filter_by(
            user_id=user_id,
            role_id=role_id,
            is_active=True
        ).first()
        
        if assignment:
            assignment.expires_at = expires_at
            db.session.commit()
            return assignment
        return None
    
    @classmethod
    def get_expired_assignments(cls):
        """Get all expired role assignments"""
        return cls.query.filter(
            cls.expires_at < datetime.utcnow(),
            cls.is_active == True
        ).all()
    
    @classmethod
    def process_expired_assignments(cls):
        """Process expired role assignments"""
        expired = cls.get_expired_assignments()
        processed = 0
        
        for assignment in expired:
            assignment.is_active = False
            processed += 1
        
        db.session.commit()
        return processed
    
    def extend_assignment(self, days=30, reason=None):
        """Extend the role assignment"""
        if self.expires_at:
            self.expires_at = self.expires_at + timedelta(days=days)
        else:
            self.expires_at = datetime.utcnow() + timedelta(days=days)
        
        if reason:
            self.assignment_reason = reason
        
        db.session.commit()
        return self
    
    def deactivate(self):
        """Deactivate the role assignment"""
        self.is_active = False
        db.session.commit()
        return self
    
    def is_expired(self):
        """Check if the assignment is expired"""
        return self.expires_at and self.expires_at < datetime.utcnow()
    
    def get_remaining_days(self):
        """Get remaining days until expiration"""
        if not self.expires_at:
            return None
        
        remaining = self.expires_at - datetime.utcnow()
        return max(0, remaining.days)
