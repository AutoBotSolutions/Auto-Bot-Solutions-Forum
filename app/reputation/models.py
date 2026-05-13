"""
Reputation and Voting Models

This module defines the database models for the enhanced voting and reputation system,
including user reputation tracking, voting history, voting patterns, and reputation levels.
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, CheckConstraint
from app import db
from app.models import User, Post, Comment

class UserReputation(db.Model):
    """User reputation tracking and management"""
    __tablename__ = 'user_reputation'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Reputation scores
    reputation_score = db.Column(db.Integer, default=0, nullable=False)
    voting_power = db.Column(db.Float, default=1.0, nullable=False)
    trust_score = db.Column(db.Float, default=0.0, nullable=False)
    
    # Reputation level
    current_level = db.Column(db.String(50), default='Newcomer', nullable=False)
    level_progress = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 to 1.0
    
    # Voting statistics
    total_votes_cast = db.Column(db.Integer, default=0, nullable=False)
    upvotes_given = db.Column(db.Integer, default=0, nullable=False)
    downvotes_given = db.Column(db.Integer, default=0, nullable=False)
    votes_received = db.Column(db.Integer, default=0, nullable=False)
    
    # Quality metrics
    helpful_votes_received = db.Column(db.Integer, default=0, nullable=False)
    controversial_votes = db.Column(db.Integer, default=0, nullable=False)
    consensus_votes = db.Column(db.Integer, default=0, nullable=False)
    
    # Activity metrics
    posts_created = db.Column(db.Integer, default=0, nullable=False)
    comments_created = db.Column(db.Integer, default=0, nullable=False)
    days_active = db.Column(db.Integer, default=0, nullable=False)
    
    # Streaks and consistency
    current_streak = db.Column(db.Integer, default=0, nullable=False)
    longest_streak = db.Column(db.Integer, default=0, nullable=False)
    last_activity_date = db.Column(db.Date, default=datetime.utcnow().date())
    
    # Penalties and bonuses
    penalty_points = db.Column(db.Integer, default=0, nullable=False)
    bonus_points = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='reputation', lazy=True)
    vote_history = db.relationship('VoteHistory', 
                                   foreign_keys='VoteHistory.user_id',
                                   primaryjoin='UserReputation.user_id == VoteHistory.user_id',
                                   backref='user_reputation', lazy='dynamic')
    voting_patterns = db.relationship('VotingPattern', 
                                     foreign_keys='VotingPattern.user_id',
                                     primaryjoin='UserReputation.user_id == VotingPattern.user_id',
                                     backref='user_reputation', lazy='dynamic')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('reputation_score >= -1000', name='check_reputation_min'),
        CheckConstraint('reputation_score <= 10000', name='check_reputation_max'),
        CheckConstraint('voting_power >= 0.1', name='check_voting_power_min'),
        CheckConstraint('voting_power <= 10.0', name='check_voting_power_max'),
        CheckConstraint('trust_score >= 0.0', name='check_trust_score_min'),
        CheckConstraint('trust_score <= 1.0', name='check_trust_score_max'),
        CheckConstraint('level_progress >= 0.0', name='check_level_progress_min'),
        CheckConstraint('level_progress <= 1.0', name='check_level_progress_max'),
        Index('idx_user_reputation_score', 'reputation_score'),
        Index('idx_user_reputation_level', 'current_level'),
        Index('idx_user_reputation_updated', 'updated_at'),
    )
    
    def __repr__(self):
        return f'<UserReputation {self.user_id}: {self.current_level} ({self.reputation_score})>'
    
    def to_dict(self):
        """Convert reputation to dictionary"""
        return {
            'user_id': self.user_id,
            'reputation_score': self.reputation_score,
            'voting_power': self.voting_power,
            'trust_score': self.trust_score,
            'current_level': self.current_level,
            'level_progress': self.level_progress,
            'total_votes_cast': self.total_votes_cast,
            'upvotes_given': self.upvotes_given,
            'downvotes_given': self.downvotes_given,
            'votes_received': self.votes_received,
            'helpful_votes_received': self.helpful_votes_received,
            'posts_created': self.posts_created,
            'comments_created': self.comments_created,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class VoteHistory(db.Model):
    """Detailed voting history and audit trail"""
    __tablename__ = 'vote_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Vote details
    vote_type = db.Column(db.String(10), nullable=False)  # 'upvote', 'downvote'
    target_type = db.Column(db.String(20), nullable=False)  # 'post', 'comment'
    target_id = db.Column(db.Integer, nullable=False)
    
    # Voting reason and context
    reason = db.Column(db.Text)  # User-provided reason for vote
    reason_category = db.Column(db.String(50))  # Predefined reason categories
    context = db.Column(db.Text)  # Additional context or notes
    
    # Weight and impact
    vote_weight = db.Column(db.Float, default=1.0, nullable=False)
    reputation_impact = db.Column(db.Float, default=0.0, nullable=False)
    
    # Metadata
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    referrer = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    revoked_at = db.Column(db.DateTime)  # When vote was revoked/changed
    
    # Relationships
    user = db.relationship('User', backref='vote_history', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('vote_type IN ("upvote", "downvote")', name='check_vote_type'),
        CheckConstraint('target_type IN ("post", "comment")', name='check_target_type'),
        CheckConstraint('vote_weight > 0', name='check_vote_weight_positive'),
        Index('idx_vote_user_target', 'user_id', 'target_type', 'target_id'),
        Index('idx_vote_created', 'created_at'),
        Index('idx_vote_type', 'vote_type'),
        Index('idx_vote_reason_category', 'reason_category'),
        Index('idx_vote_revoked', 'revoked_at'),
    )
    
    def __repr__(self):
        return f'<VoteHistory {self.user_id}: {self.vote_type} on {self.target_type}:{self.target_id}>'
    
    def to_dict(self):
        """Convert vote history to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vote_type': self.vote_type,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'reason': self.reason,
            'reason_category': self.reason_category,
            'vote_weight': self.vote_weight,
            'reputation_impact': self.reputation_impact,
            'created_at': self.created_at.isoformat(),
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None
        }

class VotingPattern(db.Model):
    """User voting patterns and analytics"""
    __tablename__ = 'voting_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Pattern type and metrics
    pattern_type = db.Column(db.String(50), nullable=False)  # 'consistency', 'bias', 'timing', 'quality'
    pattern_value = db.Column(db.Float, nullable=False)
    pattern_description = db.Column(db.Text)
    
    # Analysis period
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    sample_size = db.Column(db.Integer, default=0, nullable=False)
    
    # Confidence and significance
    confidence_score = db.Column(db.Float, default=0.0, nullable=False)
    statistical_significance = db.Column(db.Float, default=0.0, nullable=False)
    
    # Metadata
    algorithm_version = db.Column(db.String(20), default='1.0')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='voting_patterns', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('pattern_value >= -1.0', name='check_pattern_value_min'),
        CheckConstraint('pattern_value <= 1.0', name='check_pattern_value_max'),
        CheckConstraint('confidence_score >= 0.0', name='check_confidence_min'),
        CheckConstraint('confidence_score <= 1.0', name='check_confidence_max'),
        CheckConstraint('statistical_significance >= 0.0', name='check_significance_min'),
        CheckConstraint('statistical_significance <= 1.0', name='check_significance_max'),
        CheckConstraint('period_end >= period_start', name='check_period_order'),
        Index('idx_pattern_user_type', 'user_id', 'pattern_type'),
        Index('idx_pattern_period', 'period_start', 'period_end'),
        Index('idx_pattern_confidence', 'confidence_score'),
    )
    
    def __repr__(self):
        return f'<VotingPattern {self.user_id}: {self.pattern_type} ({self.pattern_value})>'
    
    def to_dict(self):
        """Convert voting pattern to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'pattern_type': self.pattern_type,
            'pattern_value': self.pattern_value,
            'pattern_description': self.pattern_description,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'sample_size': self.sample_size,
            'confidence_score': self.confidence_score,
            'statistical_significance': self.statistical_significance,
            'created_at': self.created_at.isoformat()
        }

class ReputationLevel(db.Model):
    """Reputation levels and thresholds"""
    __tablename__ = 'reputation_levels'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Level information
    level_name = db.Column(db.String(50), unique=True, nullable=False)
    level_order = db.Column(db.Integer, unique=True, nullable=False)
    min_reputation = db.Column(db.Integer, nullable=False)
    max_reputation = db.Column(db.Integer, nullable=False)
    
    # Benefits and permissions
    voting_power_multiplier = db.Column(db.Float, default=1.0, nullable=False)
    daily_vote_limit = db.Column(db.Integer, default=10, nullable=False)
    special_permissions = db.Column(db.Text)  # JSON string of permissions
    
    # Visual elements
    badge_color = db.Column(db.String(20), default='secondary')
    badge_icon = db.Column(db.String(50))
    description = db.Column(db.Text)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('min_reputation >= 0', name='check_min_reputation_non_negative'),
        CheckConstraint('max_reputation > min_reputation', name='check_max_reputation_greater'),
        CheckConstraint('voting_power_multiplier > 0', name='check_voting_power_positive'),
        CheckConstraint('daily_vote_limit > 0', name='check_daily_vote_limit_positive'),
        CheckConstraint('level_order >= 0', name='check_level_order_non_negative'),
        Index('idx_level_order', 'level_order'),
        Index('idx_level_reputation', 'min_reputation', 'max_reputation'),
    )
    
    def __repr__(self):
        return f'<ReputationLevel {self.level_name} ({self.min_reputation}-{self.max_reputation})>'
    
    def to_dict(self):
        """Convert reputation level to dictionary"""
        return {
            'id': self.id,
            'level_name': self.level_name,
            'level_order': self.level_order,
            'min_reputation': self.min_reputation,
            'max_reputation': self.max_reputation,
            'voting_power_multiplier': self.voting_power_multiplier,
            'daily_vote_limit': self.daily_vote_limit,
            'badge_color': self.badge_color,
            'badge_icon': self.badge_icon,
            'description': self.description,
            'is_active': self.is_active
        }
    
    @classmethod
    def get_level_for_reputation(cls, reputation_score):
        """Get the appropriate level for a given reputation score"""
        return cls.query.filter(
            cls.min_reputation <= reputation_score,
            cls.max_reputation >= reputation_score,
            cls.is_active == True
        ).first()
    
    @classmethod
    def get_all_active_levels(cls):
        """Get all active reputation levels ordered by level order"""
        return cls.query.filter(cls.is_active == True).order_by(cls.level_order).all()

# Initialize default reputation levels
def init_reputation_levels():
    """Initialize default reputation levels if they don't exist"""
    if ReputationLevel.query.count() == 0:
        default_levels = [
            {
                'level_name': 'Newcomer',
                'level_order': 0,
                'min_reputation': 0,
                'max_reputation': 49,
                'voting_power_multiplier': 0.5,
                'daily_vote_limit': 5,
                'badge_color': 'secondary',
                'badge_icon': 'fa-user',
                'description': 'New member of the community'
            },
            {
                'level_name': 'Member',
                'level_order': 1,
                'min_reputation': 50,
                'max_reputation': 199,
                'voting_power_multiplier': 1.0,
                'daily_vote_limit': 10,
                'badge_color': 'primary',
                'badge_icon': 'fa-user-check',
                'description': 'Active community member'
            },
            {
                'level_name': 'Trusted',
                'level_order': 2,
                'min_reputation': 200,
                'max_reputation': 499,
                'voting_power_multiplier': 1.5,
                'daily_vote_limit': 20,
                'badge_color': 'success',
                'badge_icon': 'fa-shield-alt',
                'description': 'Trusted community member'
            },
            {
                'level_name': 'Expert',
                'level_order': 3,
                'min_reputation': 500,
                'max_reputation': 999,
                'voting_power_multiplier': 2.0,
                'daily_vote_limit': 30,
                'badge_color': 'info',
                'badge_icon': 'fa-star',
                'description': 'Expert community contributor'
            },
            {
                'level_name': 'Master',
                'level_order': 4,
                'min_reputation': 1000,
                'max_reputation': 2499,
                'voting_power_multiplier': 3.0,
                'daily_vote_limit': 50,
                'badge_color': 'warning',
                'badge_icon': 'fa-crown',
                'description': 'Master community contributor'
            },
            {
                'level_name': 'Legend',
                'level_order': 5,
                'min_reputation': 2500,
                'max_reputation': 10000,
                'voting_power_multiplier': 5.0,
                'daily_vote_limit': 100,
                'badge_color': 'danger',
                'badge_icon': 'fa-trophy',
                'description': 'Legendary community member'
            }
        ]
        
        for level_data in default_levels:
            level = ReputationLevel(**level_data)
            db.session.add(level)
        
        db.session.commit()
