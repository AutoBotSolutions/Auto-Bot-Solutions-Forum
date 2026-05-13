"""
Social Features Models

This module contains models for user social features including:
- User following/friend system
- User connections and networking
- Social activity feeds
- User recommendations
- Social sharing options
"""

from datetime import datetime, timezone, timedelta
from flask import current_app
from app import db
from app.models import User
import json


class UserFollow(db.Model):
    """Model for user following relationships"""
    __tablename__ = 'user_follows'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship metadata
    is_mutual = db.Column(db.Boolean, default=False)  # Both users follow each other
    is_close_friend = db.Column(db.Boolean, default=False)  # Close friend relationship
    
    # Foreign key relationships
    follower = db.relationship('User', foreign_keys=[follower_id], backref='following_relationships')
    following = db.relationship('User', foreign_keys=[following_id], backref='follower_relationships')
    
    # Unique constraint to prevent duplicate follows
    __table_args__ = (db.UniqueConstraint('follower_id', 'following_id', name='unique_follow'),)
    
    def __repr__(self):
        return f'<UserFollow {self.follower.username} follows {self.following.username}>'
    
    @staticmethod
    def follow_user(follower_id, following_id):
        """Create a new follow relationship"""
        if follower_id == following_id:
            return None  # Users can't follow themselves
        
        # Check if already following
        existing = UserFollow.query.filter_by(
            follower_id=follower_id, 
            following_id=following_id
        ).first()
        
        if existing:
            return existing
        
        # Create new follow relationship
        follow = UserFollow(follower_id=follower_id, following_id=following_id)
        db.session.add(follow)
        
        # Check for mutual follow
        reverse_follow = UserFollow.query.filter_by(
            follower_id=following_id, 
            following_id=follower_id
        ).first()
        
        if reverse_follow:
            follow.is_mutual = True
            reverse_follow.is_mutual = True
        
        db.session.commit()
        return follow
    
    @staticmethod
    def unfollow_user(follower_id, following_id):
        """Remove a follow relationship"""
        follow = UserFollow.query.filter_by(
            follower_id=follower_id, 
            following_id=following_id
        ).first()
        
        if follow:
            db.session.delete(follow)
            
            # Update mutual status on reverse relationship
            reverse_follow = UserFollow.query.filter_by(
                follower_id=following_id, 
                following_id=follower_id
            ).first()
            
            if reverse_follow:
                reverse_follow.is_mutual = False
            
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def is_following(follower_id, following_id):
        """Check if user is following another user"""
        return UserFollow.query.filter_by(
            follower_id=follower_id, 
            following_id=following_id
        ).first() is not None


class UserFriend(db.Model):
    """Model for user friend relationships"""
    __tablename__ = 'user_friends'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined, blocked
    requested_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    
    # Friend relationship metadata
    is_close_friend = db.Column(db.Boolean, default=False)
    friend_group = db.Column(db.String(50))  # Family, Work, School, etc.
    
    # Foreign key relationships
    user1 = db.relationship('User', foreign_keys=[user1_id], backref='friend_relationships_1')
    user2 = db.relationship('User', foreign_keys=[user2_id], backref='friend_relationships_2')
    requested_by = db.relationship('User', foreign_keys=[requested_by_id])
    
    # Unique constraint to prevent duplicate friend requests
    __table_args__ = (db.UniqueConstraint('user1_id', 'user2_id', name='unique_friendship'),)
    
    def __repr__(self):
        return f'<UserFriend {self.user1.username} <-> {self.user2.username} ({self.status})>'
    
    @staticmethod
    def send_friend_request(user1_id, user2_id, requested_by_id=None):
        """Send a friend request"""
        if user1_id == user2_id:
            return None  # Users can't friend themselves
        
        # Check if friendship already exists
        existing = UserFriend.query.filter(
            db.or_(
                db.and_(UserFriend.user1_id == user1_id, UserFriend.user2_id == user2_id),
                db.and_(UserFriend.user1_id == user2_id, UserFriend.user2_id == user1_id)
            )
        ).first()
        
        if existing:
            return existing
        
        # Create new friend request
        if not requested_by_id:
            requested_by_id = user1_id
        
        friend_request = UserFriend(
            user1_id=user1_id,
            user2_id=user2_id,
            requested_by_id=requested_by_id,
            status='pending'
        )
        
        db.session.add(friend_request)
        db.session.commit()
        return friend_request
    
    @staticmethod
    def accept_friend_request(friendship_id, user_id):
        """Accept a friend request"""
        friend_request = UserFriend.query.filter_by(id=friendship_id).first()
        
        if not friend_request:
            return False
        
        # Verify user is part of the friendship
        if user_id not in [friend_request.user1_id, friend_request.user2_id]:
            return False
        
        friend_request.status = 'accepted'
        friend_request.responded_at = datetime.utcnow()
        db.session.commit()
        return True
    
    @staticmethod
    def decline_friend_request(friendship_id, user_id):
        """Decline a friend request"""
        friend_request = UserFriend.query.filter_by(id=friendship_id).first()
        
        if not friend_request:
            return False
        
        # Verify user is part of the friendship
        if user_id not in [friend_request.user1_id, friend_request.user2_id]:
            return False
        
        friend_request.status = 'declined'
        friend_request.responded_at = datetime.utcnow()
        db.session.commit()
        return True
    
    @staticmethod
    def block_user(user1_id, user2_id, blocker_id):
        """Block a user"""
        if user1_id == user2_id:
            return None
        
        # Remove any existing friendship
        existing = UserFriend.query.filter(
            db.or_(
                db.and_(UserFriend.user1_id == user1_id, UserFriend.user2_id == user2_id),
                db.and_(UserFriend.user1_id == user2_id, UserFriend.user2_id == user1_id)
            )
        ).first()
        
        if existing:
            existing.status = 'blocked'
            existing.responded_at = datetime.utcnow()
        else:
            # Create new blocked relationship
            friendship = UserFriend(
                user1_id=user1_id,
                user2_id=user2_id,
                requested_by_id=blocker_id,
                status='blocked',
                responded_at=datetime.utcnow()
            )
            db.session.add(friendship)
        
        db.session.commit()
        return True
    
    @staticmethod
    def get_friends(user_id, status='accepted'):
        """Get user's friends"""
        return UserFriend.query.filter(
            db.or_(
                db.and_(UserFriend.user1_id == user_id, UserFriend.status == status),
                db.and_(UserFriend.user2_id == user_id, UserFriend.status == status)
            )
        ).all()
    
    @staticmethod
    def are_friends(user1_id, user2_id):
        """Check if two users are friends"""
        return UserFriend.query.filter(
            db.or_(
                db.and_(UserFriend.user1_id == user1_id, UserFriend.user2_id == user2_id, UserFriend.status == 'accepted'),
                db.and_(UserFriend.user1_id == user2_id, UserFriend.user2_id == user1_id, UserFriend.status == 'accepted')
            )
        ).first() is not None


class SocialActivity(db.Model):
    """Model for social activity feed"""
    __tablename__ = 'social_activities'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # post, comment, follow, friend, like, share
    target_type = db.Column(db.String(50))  # user, post, comment
    target_id = db.Column(db.Integer)
    action = db.Column(db.String(100), nullable=False)  # created, updated, deleted, liked, shared
    description = db.Column(db.Text)
    activity_metadata = db.Column(db.JSON)  # Additional activity data
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    user = db.relationship('User', backref='social_activities')
    
    def __repr__(self):
        return f'<SocialActivity {self.user.username} - {self.activity_type}: {self.action}>'
    
    @staticmethod
    def create_activity(user_id, activity_type, action, target_type=None, target_id=None, 
                       description=None, activity_metadata=None, is_public=True):
        """Create a new social activity"""
        activity = SocialActivity(
            user_id=user_id,
            activity_type=activity_type,
            action=action,
            target_type=target_type,
            target_id=target_id,
            description=description,
            activity_metadata=activity_metadata,
            is_public=is_public
        )
        
        db.session.add(activity)
        db.session.commit()
        return activity
    
    @staticmethod
    def get_activity_feed(user_id, limit=50, include_friends=True):
        """Get activity feed for a user"""
        query = SocialActivity.query.filter_by(is_public=True)
        
        if include_friends:
            # Get friends
            friends = UserFriend.get_friends(user_id)
            friend_ids = [user_id]
            
            for friendship in friends:
                if friendship.user1_id == user_id:
                    friend_ids.append(friendship.user2_id)
                else:
                    friend_ids.append(friendship.user1_id)
            
            query = query.filter(SocialActivity.user_id.in_(friend_ids))
        else:
            query = query.filter_by(user_id=user_id)
        
        return query.order_by(SocialActivity.created_at.desc()).limit(limit).all()


class UserRecommendation(db.Model):
    """Model for user recommendations"""
    __tablename__ = 'user_recommendations'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recommended_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recommendation_type = db.Column(db.String(50), nullable=False)  # follow, friend, similar_interests
    score = db.Column(db.Float, default=0.0)  # Recommendation strength score
    reason = db.Column(db.Text)  # Why this user is recommended
    recommendation_metadata = db.Column(db.JSON)  # Additional recommendation data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_dismissed = db.Column(db.Boolean, default=False)
    
    # Foreign key relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='recommendations_received')
    recommended_user = db.relationship('User', foreign_keys=[recommended_user_id], backref='recommendations_made')
    
    def __repr__(self):
        return f'<UserRecommendation {self.user.username} -> {self.recommended_user.username}>'
    
    @staticmethod
    def create_recommendation(user_id, recommended_user_id, recommendation_type, score=0.0, reason=None, recommendation_metadata=None):
        """Create a new user recommendation"""
        # Check if recommendation already exists
        existing = UserRecommendation.query.filter_by(
            user_id=user_id, 
            recommended_user_id=recommended_user_id,
            recommendation_type=recommendation_type
        ).first()
        
        if existing:
            # Update existing recommendation
            existing.score = max(existing.score, score)
            existing.reason = reason or existing.reason
            existing.recommendation_metadata = recommendation_metadata or existing.recommendation_metadata
            db.session.commit()
            return existing
        
        # Create new recommendation
        recommendation = UserRecommendation(
            user_id=user_id,
            recommended_user_id=recommended_user_id,
            recommendation_type=recommendation_type,
            score=score,
            reason=reason,
            recommendation_metadata=recommendation_metadata,
            expires_at=datetime.utcnow() + timedelta(days=30)  # Expire after 30 days
        )
        
        db.session.add(recommendation)
        db.session.commit()
        return recommendation
    
    @staticmethod
    def get_recommendations(user_id, recommendation_type=None, limit=20):
        """Get recommendations for a user"""
        query = UserRecommendation.query.filter_by(
            user_id=user_id,
            is_dismissed=False
        ).filter(UserRecommendation.expires_at > datetime.utcnow())
        
        if recommendation_type:
            query = query.filter_by(recommendation_type=recommendation_type)
        
        return query.order_by(UserRecommendation.score.desc()).limit(limit).all()
    
    @staticmethod
    def dismiss_recommendation(recommendation_id, user_id):
        """Dismiss a recommendation"""
        recommendation = UserRecommendation.query.filter_by(
            id=recommendation_id,
            user_id=user_id
        ).first()
        
        if recommendation:
            recommendation.is_dismissed = True
            db.session.commit()
            return True
        
        return False


class SocialShare(db.Model):
    """Model for social sharing"""
    __tablename__ = 'social_shares'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # post, comment, profile
    content_id = db.Column(db.Integer, nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # twitter, facebook, linkedin, etc.
    share_url = db.Column(db.String(500))
    share_text = db.Column(db.Text)
    share_metadata = db.Column(db.JSON)  # Platform-specific data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    user = db.relationship('User', backref='social_shares')
    
    def __repr__(self):
        return f'<SocialShare {self.user.username} shared {self.content_type} to {self.platform}>'
    
    @staticmethod
    def create_share(user_id, content_type, content_id, platform, share_url=None, share_text=None, share_metadata=None):
        """Create a new social share"""
        share = SocialShare(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id,
            platform=platform,
            share_url=share_url,
            share_text=share_text,
            share_metadata=share_metadata
        )
        
        db.session.add(share)
        db.session.commit()
        return share
    
    @staticmethod
    def get_user_shares(user_id, content_type=None, platform=None, limit=50):
        """Get user's social shares"""
        query = SocialShare.query.filter_by(user_id=user_id)
        
        if content_type:
            query = query.filter_by(content_type=content_type)
        
        if platform:
            query = query.filter_by(platform=platform)
        
        return query.order_by(SocialShare.created_at.desc()).limit(limit).all()


class UserGroup(db.Model):
    """Model for user groups/circles"""
    __tablename__ = 'user_groups'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    group_type = db.Column(db.String(50), default='custom')  # family, work, school, custom
    color = db.Column(db.String(7), default='#007bff')
    icon = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_groups')
    members = db.relationship('User', secondary='group_members', backref='groups')
    
    def __repr__(self):
        return f'<UserGroup {self.name}>'
    
    @staticmethod
    def create_group(name, creator_id, description=None, is_private=False, group_type='custom', color=None, icon=None):
        """Create a new user group"""
        group = UserGroup(
            name=name,
            description=description,
            creator_id=creator_id,
            is_private=is_private,
            group_type=group_type,
            color=color or '#007bff',
            icon=icon
        )
        
        db.session.add(group)
        db.session.commit()
        
        # Add creator as member
        GroupMember.add_member(group.id, creator_id, is_admin=True)
        
        return group
    
    def add_member(self, user_id, is_admin=False):
        """Add a member to the group"""
        return GroupMember.add_member(self.id, user_id, is_admin)
    
    def remove_member(self, user_id):
        """Remove a member from the group"""
        return GroupMember.remove_member(self.id, user_id)
    
    def is_member(self, user_id):
        """Check if user is a member of the group"""
        return GroupMember.query.filter_by(group_id=self.id, user_id=user_id).first() is not None
    
    def get_member_count(self):
        """Get number of members in the group"""
        return GroupMember.query.filter_by(group_id=self.id).count()


class GroupMember(db.Model):
    """Model for group membership"""
    __tablename__ = 'group_members'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    group = db.relationship('UserGroup', backref='membership_records')
    user = db.relationship('User', backref='group_memberships')
    
    # Unique constraint to prevent duplicate memberships
    __table_args__ = (db.UniqueConstraint('group_id', 'user_id', name='unique_group_member'),)
    
    def __repr__(self):
        return f'<GroupMember {self.user.username} in {self.group.name}>'
    
    @staticmethod
    def add_member(group_id, user_id, is_admin=False):
        """Add a member to a group"""
        # Check if already a member
        existing = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if existing:
            return existing
        
        member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            is_admin=is_admin
        )
        
        db.session.add(member)
        db.session.commit()
        return member
    
    @staticmethod
    def remove_member(group_id, user_id):
        """Remove a member from a group"""
        member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        
        if member:
            db.session.delete(member)
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def is_admin(group_id, user_id):
        """Check if user is admin of a group"""
        member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        return member and member.is_admin
