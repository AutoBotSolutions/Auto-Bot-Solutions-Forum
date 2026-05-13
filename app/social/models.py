"""
Social Relationships Models
Auto Bot Solutions Forum

This module implements advanced user relationship models including
social connections, role hierarchies, and user analytics relationships.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, Table, JSON, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from app import db
from app.models import User

# Association tables for many-to-many relationships
user_followers = Table(
    'user_followers',
    db.Model.metadata,
    Column('follower_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('following_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc)),
    Index('idx_user_followers_follower', 'follower_id'),
    Index('idx_user_followers_following', 'following_id'),
    Index('idx_user_followers_created', 'created_at'),
    extend_existing=True
)

user_friends = Table(
    'user_friends',
    db.Model.metadata,
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('friend_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc)),
    Column('confirmed_at', DateTime),
    Column('initiator_id', Integer, ForeignKey('user.id')),
    Index('idx_user_friends_user', 'user_id'),
    Index('idx_user_friends_friend', 'friend_id'),
    Index('idx_user_friends_confirmed', 'confirmed_at'),
    extend_existing=True
)

user_blocks = Table(
    'user_blocks',
    db.Model.metadata,
    Column('blocker_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('blocked_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc)),
    Column('reason', Text),
    Index('idx_user_blocks_blocker', 'blocker_id'),
    Index('idx_user_blocks_blocked', 'blocked_id'),
    extend_existing=True
)


class UserConnection(db.Model):
    """User connection tracking with relationship analytics"""
    __tablename__ = 'user_connections'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    connected_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    connection_type = Column(String(50), nullable=False)  # follow, friend, block, mute, etc.
    status = Column(String(20), default='active')  # active, inactive, pending, blocked
    strength = Column(Float, default=0.0)  # Relationship strength score (0.0-1.0)
    interaction_count = Column(Integer, default=0)
    last_interaction = Column(DateTime)
    connection_metadata = Column(JSON)  # Additional connection metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id], backref='social_connections')
    connected_user = relationship('User', foreign_keys=[connected_user_id], backref='incoming_social_connections')
    
    # Table options
    __table_args__ = {'extend_existing': True}
    
    def __repr__(self):
        return f'<UserConnection {self.user_id} -> {self.connected_user_id} ({self.connection_type})>'
    
    @hybrid_property
    def is_active(self):
        """Check if connection is active"""
        return self.status == 'active'
    
    @hybrid_property
    def is_mutual(self):
        """Check if this is a mutual connection (both users have the same connection type)"""
        if self.connection_type in ['follow', 'friend']:
            reverse_connection = UserConnection.query.filter_by(
                user_id=self.connected_user_id,
                connected_user_id=self.user_id,
                connection_type=self.connection_type,
                status='active'
            ).first()
            return reverse_connection is not None
        return False
    
    def update_strength(self, interaction_weight=0.1):
        """Update connection strength based on interactions"""
        self.interaction_count += 1
        self.strength = min(1.0, self.strength + interaction_weight)
        self.last_interaction = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class UserSocialProfile(db.Model):
    """Extended user social profile with analytics"""
    __tablename__ = 'user_social_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, unique=True)
    
    # Social metrics
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    friends_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    
    # Engagement metrics
    avg_post_engagement = Column(Float, default=0.0)
    response_rate = Column(Float, default=0.0)
    interaction_frequency = Column(Float, default=0.0)  # Interactions per day
    social_influence_score = Column(Float, default=0.0)  # 0.0-1.0
    
    # Social preferences
    privacy_level = Column(String(20), default='public')  # public, friends, private
    allow_follow_requests = Column(Boolean, default=True)
    allow_friend_requests = Column(Boolean, default=True)
    show_online_status = Column(Boolean, default=True)
    show_activity_status = Column(Boolean, default=True)
    
    # Social settings
    auto_follow_back = Column(Boolean, default=False)
    notification_preferences = Column(JSON)  # Email, push, in-app notifications
    content_filters = Column(JSON)  # Content filtering preferences
    
    # Analytics data
    social_analytics = Column(JSON)  # Detailed social analytics
    last_analytics_update = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship('User', backref='social_profile', uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_social_profiles_user', 'user_id'),
        Index('idx_user_social_profiles_followers', 'followers_count'),
        Index('idx_user_social_profiles_influence', 'social_influence_score'),
        Index('idx_user_social_profiles_privacy', 'privacy_level'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<UserSocialProfile {self.user_id} (Influence: {self.social_influence_score})>'
    
    @hybrid_property
    def is_public_profile(self):
        """Check if user has a public profile"""
        return self.privacy_level == 'public'
    
    @hybrid_property
    def social_activity_level(self):
        """Calculate social activity level based on metrics"""
        activity_score = (
            self.posts_count * 0.3 +
            self.comments_count * 0.2 +
            self.likes_count * 0.1 +
            self.shares_count * 0.2 +
            self.followers_count * 0.2
        )
        
        if activity_score < 10:
            return 'low'
        elif activity_score < 100:
            return 'medium'
        else:
            return 'high'
    
    def update_social_metrics(self):
        """Update social metrics based on current data"""
        from app.models import Post, Comment
        
        # Update counts
        self.posts_count = Post.query.filter_by(user_id=self.user_id).count()
        self.comments_count = Comment.query.filter_by(user_id=self.user_id).count()
        
        # Update connection counts
        self.followers_count = UserConnection.query.filter_by(
            connected_user_id=self.user_id,
            connection_type='follow',
            status='active'
        ).count()
        
        self.following_count = UserConnection.query.filter_by(
            user_id=self.user_id,
            connection_type='follow',
            status='active'
        ).count()
        
        self.friends_count = UserConnection.query.filter_by(
            user_id=self.user_id,
            connection_type='friend',
            status='active'
        ).count()
        
        # Calculate engagement metrics
        if self.posts_count > 0:
            total_engagement = self.likes_count + self.comments_count + self.shares_count
            self.avg_post_engagement = total_engagement / self.posts_count
        
        # Update influence score
        self.calculate_influence_score()
        
        self.updated_at = datetime.now(timezone.utc)
    
    def calculate_influence_score(self):
        """Calculate social influence score based on multiple factors"""
        # Base score from followers
        followers_score = min(1.0, self.followers_count / 1000.0) * 0.4
        
        # Activity score
        activity_score = min(1.0, self.social_activity_level_score() / 100.0) * 0.3
        
        # Engagement score
        engagement_score = min(1.0, self.avg_post_engagement / 50.0) * 0.2
        
        # Recency score (based on recent activity)
        recency_score = self.calculate_recency_score() * 0.1
        
        self.social_influence_score = followers_score + activity_score + engagement_score + recency_score
    
    def social_activity_level_score(self):
        """Calculate numeric social activity level score"""
        return (
            self.posts_count * 2 +
            self.comments_count +
            self.likes_count * 0.5 +
            self.shares_count * 1.5
        )
    
    def calculate_recency_score(self):
        """Calculate recency score based on last activity"""
        if not self.last_analytics_update:
            return 0.0
        
        days_since_activity = (datetime.now(timezone.utc) - self.last_analytics_update).days
        
        if days_since_activity < 1:
            return 1.0
        elif days_since_activity < 7:
            return 0.8
        elif days_since_activity < 30:
            return 0.5
        else:
            return 0.2


class UserGroup(db.Model):
    """User groups for community organization"""
    __tablename__ = 'user_groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    group_type = Column(String(50), default='community')  # community, organization, team, club
    privacy = Column(String(20), default='public')  # public, private, invite_only
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Group settings
    max_members = Column(Integer, default=1000)
    require_approval = Column(Boolean, default=False)
    allow_invites = Column(Boolean, default=True)
    allow_posts = Column(Boolean, default=True)
    moderated = Column(Boolean, default=False)
    
    # Group statistics
    member_count = Column(Integer, default=0)
    post_count = Column(Integer, default=0)
    activity_score = Column(Float, default=0.0)
    
    # Group metadata
    tags = Column(JSON)  # Group tags for categorization
    rules = Column(JSON)  # Group rules and guidelines
    settings = Column(JSON)  # Additional group settings
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    archived_at = Column(DateTime)
    
    # Relationships
    creator = relationship('User', foreign_keys=[creator_id], backref='social_created_groups')
    members = relationship('UserGroupMembership', primaryjoin='app.social.models.UserGroup.id == UserGroupMembership.group_id', backref='user_group', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        Index('idx_user_groups_name', 'name'),
        Index('idx_user_groups_type', 'group_type'),
        Index('idx_user_groups_privacy', 'privacy'),
        Index('idx_user_groups_creator', 'creator_id'),
        Index('idx_user_groups_activity', 'activity_score'),
        Index('idx_user_groups_created', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<UserGroup {self.name} ({self.group_type})>'
    
    @hybrid_property
    def is_active(self):
        """Check if group is active (not archived)"""
        return self.archived_at is None
    
    @hybrid_property
    def is_public(self):
        """Check if group is public"""
        return self.privacy == 'public'
    
    @hybrid_property
    def can_join_directly(self):
        """Check if users can join directly without approval"""
        return self.privacy == 'public' and not self.require_approval
    
    def add_member(self, user, role='member'):
        """Add a member to the group"""
        existing_membership = UserGroupMembership.query.filter_by(
            user_id=user.id,
            group_id=self.id
        ).first()
        
        if existing_membership:
            return False  # User already a member
        
        membership = UserGroupMembership(
            user_id=user.id,
            group_id=self.id,
            role=role
        )
        
        db.session.add(membership)
        self.member_count += 1
        self.updated_at = datetime.now(timezone.utc)
        
        return membership
    
    def remove_member(self, user):
        """Remove a member from the group"""
        membership = UserGroupMembership.query.filter_by(
            user_id=user.id,
            group_id=self.id
        ).first()
        
        if not membership:
            return False  # User not a member
        
        db.session.delete(membership)
        self.member_count -= 1
        self.updated_at = datetime.now(timezone.utc)
        
        return True
    
    def update_activity_score(self):
        """Update group activity score based on recent activity"""
        # This would typically be calculated based on recent posts, comments, etc.
        # For now, using a simple calculation based on member count and post count
        base_score = (self.member_count * 0.3 + self.post_count * 0.7) / 100.0
        self.activity_score = min(1.0, base_score)
        self.updated_at = datetime.now(timezone.utc)


class UserGroupMembership(db.Model):
    """User group membership with roles and permissions"""
    __tablename__ = 'user_group_memberships'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    group_id = Column(Integer, ForeignKey('user_groups.id'), nullable=False)
    role = Column(String(50), default='member')  # member, moderator, admin, owner
    status = Column(String(20), default='active')  # active, inactive, banned, pending
    permissions = Column(JSON)  # Specific permissions for this member
    
    # Membership metadata
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    invited_by = Column(Integer, ForeignKey('user.id'))
    last_activity = Column(DateTime)
    contribution_score = Column(Float, default=0.0)  # User's contribution to the group
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id], backref='social_group_memberships')
    group = relationship('app.social.models.UserGroup')
    inviter = relationship('User', foreign_keys=[invited_by])
    
    # Indexes
    __table_args__ = (
        Index('idx_user_group_memberships_user', 'user_id'),
        Index('idx_user_group_memberships_group', 'group_id'),
        Index('idx_user_group_memberships_role', 'role'),
        Index('idx_user_group_memberships_status', 'status'),
        Index('idx_user_group_memberships_joined', 'joined_at'),
        Index('idx_user_group_memberships_composite', 'user_id', 'group_id', 'status'),
    )
    
    def __repr__(self):
        return f'<UserGroupMembership {self.user_id} in {self.group_id} ({self.role})>'
    
    @hybrid_property
    def is_active(self):
        """Check if membership is active"""
        return self.status == 'active'
    
    @hybrid_property
    def is_moderator(self):
        """Check if user has moderator privileges"""
        return self.role in ['moderator', 'admin', 'owner']
    
    @hybrid_property
    def is_admin(self):
        """Check if user has admin privileges"""
        return self.role in ['admin', 'owner']
    
    @hybrid_property
    def is_owner(self):
        """Check if user is the group owner"""
        return self.role == 'owner'
    
    def update_contribution(self, activity_weight=0.1):
        """Update user's contribution score to the group"""
        self.contribution_score = min(1.0, self.contribution_score + activity_weight)
        self.last_activity = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        if not self.permissions:
            # Default permissions based on role
            role_permissions = {
                'owner': ['all'],
                'admin': ['manage_members', 'manage_content', 'moderate', 'view_analytics'],
                'moderator': ['moderate', 'manage_content'],
                'member': ['view_content', 'participate']
            }
            return permission in role_permissions.get(self.role, [])
        
        return permission in self.permissions


class UserInteraction(db.Model):
    """Track user interactions for relationship analytics"""
    __tablename__ = 'user_interactions'
    
    id = Column(Integer, primary_key=True)
    initiator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    target_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    interaction_type = Column(String(50), nullable=False)  # like, comment, share, message, mention, etc.
    context_type = Column(String(50))  # post, comment, message, group, etc.
    context_id = Column(Integer)  # ID of the context object
    
    # Interaction metadata
    interaction_data = Column(JSON)  # Additional interaction data
    sentiment_score = Column(Float)  # Sentiment analysis score (-1.0 to 1.0)
    response_time = Column(Float)  # Time to respond in seconds
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    initiator = relationship('User', foreign_keys=[initiator_id], backref='initiated_interactions')
    target = relationship('User', foreign_keys=[target_id], backref='received_interactions')
    
    # Indexes
    __table_args__ = (
        Index('idx_user_interactions_initiator', 'initiator_id'),
        Index('idx_user_interactions_target', 'target_id'),
        Index('idx_user_interactions_type', 'interaction_type'),
        Index('idx_user_interactions_context', 'context_type', 'context_id'),
        Index('idx_user_interactions_created', 'created_at'),
        Index('idx_user_interactions_composite', 'initiator_id', 'target_id', 'interaction_type'),
    )
    
    def __repr__(self):
        return f'<UserInteraction {self.initiator_id} -> {self.target_id} ({self.interaction_type})>'


class UserRelationshipAnalytics(db.Model):
    """Analytics for user relationships and social patterns"""
    __tablename__ = 'user_relationship_analytics'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Relationship metrics
    total_connections = Column(Integer, default=0)
    active_connections = Column(Integer, default=0)
    mutual_connections = Column(Integer, default=0)
    connection_strength_avg = Column(Float, default=0.0)
    
    # Interaction metrics
    total_interactions = Column(Integer, default=0)
    interactions_sent = Column(Integer, default=0)
    interactions_received = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    
    # Network metrics
    network_density = Column(Float, default=0.0)  # How connected the user's network is
    clustering_coefficient = Column(Float, default=0.0)  # Tendency to form clusters
    betweenness_centrality = Column(Float, default=0.0)  # Influence in network
    closeness_centrality = Column(Float, default=0.0)  # Closeness to other users
    
    # Behavioral patterns
    interaction_frequency = Column(JSON)  # Interaction patterns by time period
    preferred_interaction_types = Column(JSON)  # Most common interaction types
    social_circles = Column(JSON)  # Identified social circles/clusters
    
    # Analytics metadata
    calculation_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    data_period_days = Column(Integer, default=30)  # Period covered by this analytics
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship('User', backref='relationship_analytics')
    
    # Indexes
    __table_args__ = (
        Index('idx_user_relationship_analytics_user', 'user_id'),
        Index('idx_user_relationship_analytics_calculation', 'calculation_date'),
        Index('idx_user_relationship_analytics_connections', 'total_connections'),
        Index('idx_user_relationship_analytics_strength', 'connection_strength_avg'),
    )
    
    def __repr__(self):
        return f'<UserRelationshipAnalytics {self.user_id} (Connections: {self.total_connections})>'
    
    def calculate_analytics(self, days=30):
        """Calculate relationship analytics for the specified period"""
        from sqlalchemy import func, and_
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Connection metrics
        self.total_connections = UserConnection.query.filter_by(user_id=self.user_id).count()
        self.active_connections = UserConnection.query.filter(
            and_(
                UserConnection.user_id == self.user_id,
                UserConnection.last_interaction >= cutoff_date
            )
        ).count()
        
        # Mutual connections
        mutual_count = 0
        connections = UserConnection.query.filter_by(user_id=self.user_id).all()
        for conn in connections:
            if conn.is_mutual:
                mutual_count += 1
        self.mutual_connections = mutual_count
        
        # Average connection strength
        strengths = [c.strength for c in connections]
        self.connection_strength_avg = sum(strengths) / len(strengths) if strengths else 0.0
        
        # Interaction metrics
        self.total_interactions = UserInteraction.query.filter_by(initiator_id=self.user_id).count()
        self.interactions_sent = self.total_interactions
        self.interactions_received = UserInteraction.query.filter_by(target_id=self.user_id).count()
        
        # Calculate network metrics (simplified versions)
        self.calculate_network_metrics()
        
        # Calculate behavioral patterns
        self.calculate_behavioral_patterns(days)
        
        self.data_period_days = days
        self.calculation_date = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def calculate_network_metrics(self):
        """Calculate network topology metrics"""
        # This is a simplified implementation
        # In a real system, you'd use network analysis libraries
        
        # Network density (simplified)
        if self.total_connections > 0:
            max_possible_connections = 1000  # Simplified assumption
            self.network_density = self.total_connections / max_possible_connections
        else:
            self.network_density = 0.0
        
        # Clustering coefficient (simplified)
        if self.mutual_connections > 0 and self.total_connections > 1:
            self.clustering_coefficient = (2 * self.mutual_connections) / (self.total_connections * (self.total_connections - 1))
        else:
            self.clustering_coefficient = 0.0
        
        # Centrality measures (simplified)
        self.betweenness_centrality = min(1.0, self.total_connections / 100.0)
        self.closeness_centrality = min(1.0, self.active_connections / 50.0)
    
    def calculate_behavioral_patterns(self, days=30):
        """Calculate behavioral patterns from interaction data"""
        from sqlalchemy import func
        from datetime import timedelta, datetime
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Interaction frequency by hour of day
        interactions = UserInteraction.query.filter(
            and_(
                UserInteraction.initiator_id == self.user_id,
                UserInteraction.created_at >= cutoff_date
            )
        ).all()
        
        hourly_frequency = {}
        for interaction in interactions:
            hour = interaction.created_at.hour
            hourly_frequency[hour] = hourly_frequency.get(hour, 0) + 1
        
        self.interaction_frequency = hourly_frequency
        
        # Preferred interaction types
        type_counts = {}
        for interaction in interactions:
            interaction_type = interaction.interaction_type
            type_counts[interaction_type] = type_counts.get(interaction_type, 0) + 1
        
        # Sort by frequency and take top 5
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        self.preferred_interaction_types = dict(sorted_types)
        
        # Social circles (simplified - based on interaction clusters)
        self.identify_social_circles(interactions)
    
    def identify_social_circles(self, interactions):
        """Identify social circles based on interaction patterns"""
        # This is a simplified implementation
        # In a real system, you'd use clustering algorithms
        
        # Group interactions by target users
        target_interactions = {}
        for interaction in interactions:
            target_id = interaction.target_id
            if target_id not in target_interactions:
                target_interactions[target_id] = []
            target_interactions[target_id].append(interaction)
        
        # Create circles based on interaction frequency
        circles = {}
        for target_id, user_interactions in target_interactions.items():
            if len(user_interactions) >= 5:  # Threshold for circle membership
                circle_name = f"circle_{len(circles) + 1}"
                circles[circle_name] = {
                    'members': [target_id],
                    'interaction_count': len(user_interactions),
                    'primary_interaction_type': max(
                        [i.interaction_type for i in user_interactions],
                        key=lambda x: [i.interaction_type for i in user_interactions].count(x)
                    )
                }
        
        self.social_circles = circles


class UserSocialActivity(db.Model):
    """Track user social activities for timeline and feed generation"""
    __tablename__ = 'user_social_activities'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    activity_type = Column(String(50), nullable=False)  # post, comment, like, share, follow, join_group, etc.
    
    # Activity content
    content = Column(Text)
    activity_metadata = Column(JSON)  # Activity-specific metadata
    
    # Target information
    target_type = Column(String(50))  # user, post, comment, group, etc.
    target_id = Column(Integer)  # ID of target object
    target_user_id = Column(Integer, ForeignKey('user.id'))  # User who is target of activity (if applicable)
    
    # Visibility and privacy
    visibility = Column(String(20), default='public')  # public, friends, private, custom
    allowed_viewers = Column(JSON)  # List of user IDs who can view this activity
    
    # Engagement metrics
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id], backref='social_activities')
    target_user = relationship('User', foreign_keys=[target_user_id], backref='targeted_activities')
    
    # Indexes
    __table_args__ = (
        Index('idx_user_social_activities_user', 'user_id'),
        Index('idx_user_social_activities_type', 'activity_type'),
        Index('idx_user_social_activities_target', 'target_type', 'target_id'),
        Index('idx_user_social_activities_visibility', 'visibility'),
        Index('idx_user_social_activities_created', 'created_at'),
        Index('idx_user_social_activities_composite', 'user_id', 'activity_type', 'created_at'),
    )
    
    def __repr__(self):
        return f'<UserSocialActivity {self.user_id} ({self.activity_type})>'
    
    @hybrid_property
    def is_public(self):
        """Check if activity is public"""
        return self.visibility == 'public'
    
    @hybrid_property
    def engagement_score(self):
        """Calculate engagement score for this activity"""
        return (
            self.likes_count * 1.0 +
            self.comments_count * 2.0 +
            self.shares_count * 3.0 +
            self.views_count * 0.1
        )
    
    def can_view(self, user_id):
        """Check if a user can view this activity"""
        if self.visibility == 'public':
            return True
        
        if self.visibility == 'private' and self.user_id == user_id:
            return True
        
        if self.visibility == 'friends':
            # Check if users are friends
            friendship = UserConnection.query.filter_by(
                user_id=self.user_id,
                connected_user_id=user_id,
                connection_type='friend',
                status='active'
            ).first()
            return friendship is not None
        
        if self.visibility == 'custom' and self.allowed_viewers:
            return user_id in self.allowed_viewers
        
        return False
    
    def update_engagement(self, engagement_type, increment=1):
        """Update engagement metrics"""
        if engagement_type == 'like':
            self.likes_count += increment
        elif engagement_type == 'comment':
            self.comments_count += increment
        elif engagement_type == 'share':
            self.shares_count += increment
        elif engagement_type == 'view':
            self.views_count += increment
        
        self.updated_at = datetime.now(timezone.utc)
