"""
Social Relationships Service
Auto Bot Solutions Forum

This module provides business logic for managing user relationships,
social connections, groups, and analytics.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import and_, or_, desc, func, text
from sqlalchemy.orm import joinedload
from app import db
from app.models import User
from .models import (
    UserConnection, UserSocialProfile, UserGroup, UserGroupMembership,
    UserInteraction, UserRelationshipAnalytics, UserSocialActivity
)


class SocialService:
    """Service for managing social relationships and connections"""
    
    def __init__(self):
        self.default_connection_strength = 0.1
        self.max_connection_strength = 1.0
        self.influence_calculation_days = 30
    
    def follow_user(self, follower_id: int, following_id: int) -> Dict[str, Any]:
        """Create a follow relationship between users"""
        if follower_id == following_id:
            return {'success': False, 'error': 'Cannot follow yourself'}
        
        # Check if already following
        existing = UserConnection.query.filter_by(
            user_id=follower_id,
            connected_user_id=following_id,
            connection_type='follow',
            status='active'
        ).first()
        
        if existing:
            return {'success': False, 'error': 'Already following this user'}
        
        # Check if blocked
        blocked = UserConnection.query.filter_by(
            user_id=following_id,
            connected_user_id=follower_id,
            connection_type='block',
            status='active'
        ).first()
        
        if blocked:
            return {'success': False, 'error': 'Cannot follow this user'}
        
        # Create follow connection
        connection = UserConnection(
            user_id=follower_id,
            connected_user_id=following_id,
            connection_type='follow',
            strength=self.default_connection_strength
        )
        
        db.session.add(connection)
        
        # Update social profiles
        self._update_follow_count(follower_id, following_id, 'follow')
        
        # Create social activity
        activity = UserSocialActivity(
            user_id=follower_id,
            activity_type='follow',
            target_type='user',
            target_id=following_id,
            target_user_id=following_id,
            visibility='public'
        )
        
        db.session.add(activity)
        db.session.commit()
        
        return {
            'success': True,
            'connection_id': connection.id,
            'message': 'Successfully followed user'
        }
    
    def unfollow_user(self, follower_id: int, following_id: int) -> Dict[str, Any]:
        """Remove a follow relationship"""
        connection = UserConnection.query.filter_by(
            user_id=follower_id,
            connected_user_id=following_id,
            connection_type='follow',
            status='active'
        ).first()
        
        if not connection:
            return {'success': False, 'error': 'Not following this user'}
        
        # Deactivate connection instead of deleting for analytics
        connection.status = 'inactive'
        connection.updated_at = datetime.now(timezone.utc)
        
        # Update social profiles
        self._update_follow_count(follower_id, following_id, 'unfollow')
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Successfully unfollowed user'
        }
    
    def send_friend_request(self, user_id: int, friend_id: int) -> Dict[str, Any]:
        """Send a friend request to another user"""
        if user_id == friend_id:
            return {'success': False, 'error': 'Cannot send friend request to yourself'}
        
        # Check if already friends
        existing = UserConnection.query.filter_by(
            user_id=user_id,
            connected_user_id=friend_id,
            connection_type='friend',
            status='active'
        ).first()
        
        if existing:
            return {'success': False, 'error': 'Already friends with this user'}
        
        # Check for pending request
        pending = UserConnection.query.filter_by(
            user_id=user_id,
            connected_user_id=friend_id,
            connection_type='friend',
            status='pending'
        ).first()
        
        if pending:
            return {'success': False, 'error': 'Friend request already sent'}
        
        # Check if blocked
        blocked = UserConnection.query.filter_by(
            user_id=friend_id,
            connected_user_id=user_id,
            connection_type='block',
            status='active'
        ).first()
        
        if blocked:
            return {'success': False, 'error': 'Cannot send friend request to this user'}
        
        # Create friend request
        connection = UserConnection(
            user_id=user_id,
            connected_user_id=friend_id,
            connection_type='friend',
            status='pending',
            strength=0.0
        )
        
        db.session.add(connection)
        
        # Create social activity (private by default)
        activity = UserSocialActivity(
            user_id=user_id,
            activity_type='friend_request',
            target_type='user',
            target_id=friend_id,
            target_user_id=friend_id,
            visibility='private',
            allowed_viewers=[friend_id]
        )
        
        db.session.add(activity)
        db.session.commit()
        
        return {
            'success': True,
            'connection_id': connection.id,
            'message': 'Friend request sent'
        }
    
    def accept_friend_request(self, user_id: int, requester_id: int) -> Dict[str, Any]:
        """Accept a friend request"""
        # Find the pending request
        request = UserConnection.query.filter_by(
            user_id=requester_id,
            connected_user_id=user_id,
            connection_type='friend',
            status='pending'
        ).first()
        
        if not request:
            return {'success': False, 'error': 'No friend request found'}
        
        # Accept the request
        request.status = 'active'
        request.strength = self.default_connection_strength
        request.updated_at = datetime.now(timezone.utc)
        
        # Create reciprocal connection
        reciprocal = UserConnection(
            user_id=user_id,
            connected_user_id=requester_id,
            connection_type='friend',
            status='active',
            strength=self.default_connection_strength
        )
        
        db.session.add(reciprocal)
        
        # Update social profiles
        self._update_friend_count(user_id, requester_id, 'accept')
        
        # Create social activities
        activity1 = UserSocialActivity(
            user_id=user_id,
            activity_type='friend_accepted',
            target_type='user',
            target_id=requester_id,
            target_user_id=requester_id,
            visibility='private',
            allowed_viewers=[requester_id]
        )
        
        activity2 = UserSocialActivity(
            user_id=requester_id,
            activity_type='friend_request_accepted',
            target_type='user',
            target_id=user_id,
            target_user_id=user_id,
            visibility='private',
            allowed_viewers=[user_id]
        )
        
        db.session.add(activity1)
        db.session.add(activity2)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Friend request accepted'
        }
    
    def decline_friend_request(self, user_id: int, requester_id: int) -> Dict[str, Any]:
        """Decline a friend request"""
        request = UserConnection.query.filter_by(
            user_id=requester_id,
            connected_user_id=user_id,
            connection_type='friend',
            status='pending'
        ).first()
        
        if not request:
            return {'success': False, 'error': 'No friend request found'}
        
        # Remove the request
        db.session.delete(request)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Friend request declined'
        }
    
    def block_user(self, blocker_id: int, blocked_id: int, reason: str = None) -> Dict[str, Any]:
        """Block a user"""
        if blocker_id == blocked_id:
            return {'success': False, 'error': 'Cannot block yourself'}
        
        # Remove any existing connections
        existing_connections = UserConnection.query.filter(
            or_(
                and_(UserConnection.user_id == blocker_id, UserConnection.connected_user_id == blocked_id),
                and_(UserConnection.user_id == blocked_id, UserConnection.connected_user_id == blocker_id)
            )
        ).all()
        
        for conn in existing_connections:
            db.session.delete(conn)
        
        # Create block connection
        block = UserConnection(
            user_id=blocker_id,
            connected_user_id=blocked_id,
            connection_type='block',
            status='active',
            metadata={'reason': reason} if reason else {}
        )
        
        db.session.add(block)
        
        # Update social profiles
        self._update_block_count(blocker_id, blocked_id, 'block')
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'User blocked successfully'
        }
    
    def unblock_user(self, blocker_id: int, blocked_id: int) -> Dict[str, Any]:
        """Unblock a user"""
        block = UserConnection.query.filter_by(
            user_id=blocker_id,
            connected_user_id=blocked_id,
            connection_type='block',
            status='active'
        ).first()
        
        if not block:
            return {'success': False, 'error': 'User is not blocked'}
        
        db.session.delete(block)
        
        # Update social profiles
        self._update_block_count(blocker_id, blocked_id, 'unblock')
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'User unblocked successfully'
        }
    
    def get_user_connections(self, user_id: int, connection_type: str = None, status: str = 'active') -> List[Dict[str, Any]]:
        """Get user's connections"""
        query = UserConnection.query.filter_by(user_id=user_id, status=status)
        
        if connection_type:
            query = query.filter_by(connection_type=connection_type)
        
        connections = query.all()
        
        result = []
        for conn in connections:
            user_data = {
                'connection_id': conn.id,
                'user_id': conn.connected_user_id,
                'connection_type': conn.connection_type,
                'strength': conn.strength,
                'created_at': conn.created_at.isoformat(),
                'last_interaction': conn.last_interaction.isoformat() if conn.last_interaction else None,
                'is_mutual': conn.is_mutual
            }
            
            # Add user details
            user = User.query.get(conn.connected_user_id)
            if user:
                user_data.update({
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                })
            
            result.append(user_data)
        
        return result
    
    def get_user_followers(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's followers"""
        followers = UserConnection.query.filter_by(
            connected_user_id=user_id,
            connection_type='follow',
            status='active'
        ).limit(limit).all()
        
        result = []
        for follow in followers:
            user = User.query.get(follow.user_id)
            if user:
                result.append({
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'followed_at': follow.created_at.isoformat(),
                    'strength': follow.strength
                })
        
        return result
    
    def get_user_following(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get users that this user is following"""
        following = UserConnection.query.filter_by(
            user_id=user_id,
            connection_type='follow',
            status='active'
        ).limit(limit).all()
        
        result = []
        for follow in following:
            user = User.query.get(follow.connected_user_id)
            if user:
                result.append({
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'followed_at': follow.created_at.isoformat(),
                    'strength': follow.strength
                })
        
        return result
    
    def get_user_friends(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's friends"""
        friends = UserConnection.query.filter_by(
            user_id=user_id,
            connection_type='friend',
            status='active'
        ).limit(limit).all()
        
        result = []
        for friend in friends:
            user = User.query.get(friend.connected_user_id)
            if user:
                result.append({
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'friends_since': friend.created_at.isoformat(),
                    'strength': friend.strength
                })
        
        return result
    
    def get_mutual_connections(self, user1_id: int, user2_id: int) -> List[Dict[str, Any]]:
        """Get mutual connections between two users"""
        user1_connections = set()
        user2_connections = set()
        
        # Get user1's connections
        conn1 = UserConnection.query.filter_by(
            user_id=user1_id,
            status='active'
        ).all()
        
        for conn in conn1:
            user1_connections.add(conn.connected_user_id)
        
        # Get user2's connections
        conn2 = UserConnection.query.filter_by(
            user_id=user2_id,
            status='active'
        ).all()
        
        for conn in conn2:
            user2_connections.add(conn.connected_user_id)
        
        # Find mutual connections
        mutual_ids = user1_connections.intersection(user2_connections)
        
        result = []
        for user_id in mutual_ids:
            user = User.query.get(user_id)
            if user:
                result.append({
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                })
        
        return result
    
    def update_connection_strength(self, user_id: int, connected_user_id: int, interaction_type: str) -> bool:
        """Update connection strength based on interaction"""
        connection = UserConnection.query.filter_by(
            user_id=user_id,
            connected_user_id=connected_user_id,
            status='active'
        ).first()
        
        if not connection:
            return False
        
        # Different interaction types have different weights
        interaction_weights = {
            'like': 0.05,
            'comment': 0.1,
            'share': 0.15,
            'message': 0.2,
            'mention': 0.1,
            'tag': 0.05
        }
        
        weight = interaction_weights.get(interaction_type, 0.05)
        connection.update_strength(weight)
        
        db.session.commit()
        return True
    
    def _update_follow_count(self, follower_id: int, following_id: int, action: str):
        """Update follow counts in social profiles"""
        follower_profile = UserSocialProfile.query.filter_by(user_id=follower_id).first()
        following_profile = UserSocialProfile.query.filter_by(user_id=following_id).first()
        
        if action == 'follow':
            if follower_profile:
                follower_profile.following_count += 1
            if following_profile:
                following_profile.followers_count += 1
        elif action == 'unfollow':
            if follower_profile:
                follower_profile.following_count = max(0, follower_profile.following_count - 1)
            if following_profile:
                following_profile.followers_count = max(0, following_profile.followers_count - 1)
    
    def _update_friend_count(self, user1_id: int, user2_id: int, action: str):
        """Update friend counts in social profiles"""
        profile1 = UserSocialProfile.query.filter_by(user_id=user1_id).first()
        profile2 = UserSocialProfile.query.filter_by(user_id=user2_id).first()
        
        if action == 'accept':
            if profile1:
                profile1.friends_count += 1
            if profile2:
                profile2.friends_count += 1
        elif action == 'remove':
            if profile1:
                profile1.friends_count = max(0, profile1.friends_count - 1)
            if profile2:
                profile2.friends_count = max(0, profile2.friends_count - 1)
    
    def _update_block_count(self, blocker_id: int, blocked_id: int, action: str):
        """Update block counts in social profiles"""
        # Block counts are tracked in the connection table itself
        pass


class GroupService:
    """Service for managing user groups"""
    
    def __init__(self):
        self.max_group_members = 10000
        self.default_group_type = 'community'
    
    def create_group(self, creator_id: int, name: str, description: str = None, 
                    group_type: str = None, privacy: str = 'public') -> Dict[str, Any]:
        """Create a new user group"""
        if not name or len(name.strip()) == 0:
            return {'success': False, 'error': 'Group name is required'}
        
        # Check if group name already exists by this user
        existing = UserGroup.query.filter_by(
            creator_id=creator_id,
            name=name.strip()
        ).first()
        
        if existing:
            return {'success': False, 'error': 'Group name already exists'}
        
        # Create group
        group = UserGroup(
            name=name.strip(),
            description=description,
            group_type=group_type or self.default_group_type,
            privacy=privacy,
            creator_id=creator_id,
            member_count=1  # Creator is automatically a member
        )
        
        db.session.add(group)
        db.session.flush()  # Get the group ID
        
        # Add creator as owner
        membership = UserGroupMembership(
            user_id=creator_id,
            group_id=group.id,
            role='owner'
        )
        
        db.session.add(membership)
        db.session.commit()
        
        # Create social activity
        activity = UserSocialActivity(
            user_id=creator_id,
            activity_type='create_group',
            target_type='group',
            target_id=group.id,
            visibility='public'
        )
        
        db.session.add(activity)
        db.session.commit()
        
        return {
            'success': True,
            'group_id': group.id,
            'message': 'Group created successfully'
        }
    
    def join_group(self, user_id: int, group_id: int) -> Dict[str, Any]:
        """Join a group"""
        group = UserGroup.query.get(group_id)
        if not group:
            return {'success': False, 'error': 'Group not found'}
        
        # Check if already a member
        existing = UserGroupMembership.query.filter_by(
            user_id=user_id,
            group_id=group_id
        ).first()
        
        if existing:
            return {'success': False, 'error': 'Already a member of this group'}
        
        # Check if group is full
        if group.member_count >= group.max_members:
            return {'success': False, 'error': 'Group is full'}
        
        # Check if user can join directly
        if not group.can_join_directly:
            return {'success': False, 'error': 'Requires approval to join this group'}
        
        # Check if user is blocked from group
        # This would require additional logic for group-specific blocks
        
        # Add member
        membership = group.add_member(user_id, 'member')
        if membership:
            # Create social activity
            activity = UserSocialActivity(
                user_id=user_id,
                activity_type='join_group',
                target_type='group',
                target_id=group.id,
                visibility='public'
            )
            
            db.session.add(activity)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Joined group successfully'
            }
        
        return {'success': False, 'error': 'Failed to join group'}
    
    def leave_group(self, user_id: int, group_id: int) -> Dict[str, Any]:
        """Leave a group"""
        group = UserGroup.query.get(group_id)
        if not group:
            return {'success': False, 'error': 'Group not found'}
        
        # Check if user is a member
        membership = UserGroupMembership.query.filter_by(
            user_id=user_id,
            group_id=group_id,
            status='active'
        ).first()
        
        if not membership:
            return {'success': False, 'error': 'Not a member of this group'}
        
        # Check if user is the owner
        if membership.role == 'owner':
            # Transfer ownership to another admin or delete group
            admins = UserGroupMembership.query.filter_by(
                group_id=group_id,
                role='admin',
                status='active'
            ).all()
            
            if admins:
                # Transfer ownership to first admin
                new_owner = admins[0]
                new_owner.role = 'owner'
                db.session.delete(membership)
            else:
                # No admins, delete the group
                db.session.delete(group)
        else:
            # Regular member can leave
            group.remove_member(User.query.get(user_id))
        
        # Create social activity
        activity = UserSocialActivity(
            user_id=user_id,
            activity_type='leave_group',
            target_type='group',
            target_id=group_id,
            visibility='private'
        )
        
        db.session.add(activity)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Left group successfully'
        }
    
    def invite_to_group(self, inviter_id: int, user_id: int, group_id: int) -> Dict[str, Any]:
        """Invite a user to join a group"""
        group = UserGroup.query.get(group_id)
        if not group:
            return {'success': False, 'error': 'Group not found'}
        
        # Check if inviter has permission
        inviter_membership = UserGroupMembership.query.filter_by(
            user_id=inviter_id,
            group_id=group_id,
            status='active'
        ).first()
        
        if not inviter_membership or not inviter_membership.is_admin:
            return {'success': False, 'error': 'No permission to invite users'}
        
        # Check if user is already a member
        existing = UserGroupMembership.query.filter_by(
            user_id=user_id,
            group_id=group_id
        ).first()
        
        if existing:
            return {'success': False, 'error': 'User is already a member'}
        
        # Check if group is full
        if group.member_count >= group.max_members:
            return {'success': False, 'error': 'Group is full'}
        
        # Check if group allows invites
        if not group.allow_invites:
            return {'success': False, 'error': 'Group does not allow invites'}
        
        # Add user as pending member
        membership = UserGroupMembership(
            user_id=user_id,
            group_id=group_id,
            role='member',
            status='pending',
            invited_by=inviter_id
        )
        
        db.session.add(membership)
        db.session.commit()
        
        # Create social activity (private to invited user)
        activity = UserSocialActivity(
            user_id=inviter_id,
            activity_type='group_invite',
            target_type='group',
            target_id=group_id,
            visibility='private',
            allowed_viewers=[user_id],
            metadata={'invited_by': inviter_id}
        )
        
        db.session.add(activity)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Invitation sent successfully'
        }
    
    def accept_group_invite(self, user_id: int, group_id: int) -> Dict[str, Any]:
        """Accept a group invitation"""
        membership = UserGroupMembership.query.filter_by(
            user_id=user_id,
            group_id=group_id,
            status='pending'
        ).first()
        
        if not membership:
            return {'success': False, 'error': 'No invitation found'}
        
        # Accept invitation
        membership.status = 'active'
        membership.joined_at = datetime.now(timezone.utc)
        
        # Update group member count
        group = UserGroup.query.get(group_id)
        if group:
            group.member_count += 1
        
        # Create social activity
        activity = UserSocialActivity(
            user_id=user_id,
            activity_type='accept_group_invite',
            target_type='group',
            target_id=group_id,
            visibility='public'
        )
        
        db.session.add(activity)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Invitation accepted successfully'
        }
    
    def decline_group_invite(self, user_id: int, group_id: int) -> Dict[str, Any]:
        """Decline a group invitation"""
        membership = UserGroupMembership.query.filter_by(
            user_id=user_id,
            group_id=group_id,
            status='pending'
        ).first()
        
        if not membership:
            return {'success': False, 'error': 'No invitation found'}
        
        # Remove invitation
        db.session.delete(membership)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Invitation declined'
        }
    
    def get_user_groups(self, user_id: int, status: str = 'active') -> List[Dict[str, Any]]:
        """Get groups that user is a member of"""
        memberships = UserGroupMembership.query.filter_by(
            user_id=user_id,
            status=status
        ).all()
        
        result = []
        for membership in memberships:
            group = membership.group
            result.append({
                'group_id': group.id,
                'name': group.name,
                'description': group.description,
                'group_type': group.group_type,
                'privacy': group.privacy,
                'member_count': group.member_count,
                'role': membership.role,
                'joined_at': membership.joined_at.isoformat() if membership.joined_at else None,
                'is_active': group.is_active
            })
        
        return result
    
    def get_group_members(self, group_id: int, role: str = None) -> List[Dict[str, Any]]:
        """Get members of a group"""
        query = UserGroupMembership.query.filter_by(group_id=group_id, status='active')
        
        if role:
            query = query.filter_by(role=role)
        
        memberships = query.all()
        
        result = []
        for membership in memberships:
            user = membership.user
            result.append({
                'user_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': membership.role,
                'joined_at': membership.joined_at.isoformat() if membership.joined_at else None,
                'contribution_score': membership.contribution_score
            })
        
        return result
    
    def update_group_member_role(self, admin_id: int, group_id: int, member_id: int, new_role: str) -> Dict[str, Any]:
        """Update a member's role in a group"""
        # Check if admin has permission
        admin_membership = UserGroupMembership.query.filter_by(
            user_id=admin_id,
            group_id=group_id,
            status='active'
        ).first()
        
        if not admin_membership or not admin_membership.is_admin:
            return {'success': False, 'error': 'No permission to update member roles'}
        
        # Get member to update
        member_membership = UserGroupMembership.query.filter_by(
            user_id=member_id,
            group_id=group_id,
            status='active'
        ).first()
        
        if not member_membership:
            return {'success': False, 'error': 'Member not found'}
        
        # Don't allow changing owner role
        if member_membership.role == 'owner':
            return {'success': False, 'error': 'Cannot change owner role'}
        
        # Update role
        old_role = member_membership.role
        member_membership.role = new_role
        member_membership.updated_at = datetime.now(timezone.utc)
        
        # Create social activity
        activity = UserSocialActivity(
            user_id=admin_id,
            activity_type='update_member_role',
            target_type='group',
            target_id=group_id,
            visibility='private',
            allowed_viewers=[member_id],
            metadata={
                'member_id': member_id,
                'old_role': old_role,
                'new_role': new_role
            }
        )
        
        db.session.add(activity)
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Member role updated to {new_role}'
        }
    
    def remove_from_group(self, admin_id: int, group_id: int, member_id: int) -> Dict[str, Any]:
        """Remove a member from a group"""
        # Check if admin has permission
        admin_membership = UserGroupMembership.query.filter_by(
            user_id=admin_id,
            group_id=group_id,
            status='active'
        ).first()
        
        if not admin_membership or not admin_membership.is_admin:
            return {'success': False, 'error': 'No permission to remove members'}
        
        # Get member to remove
        member_membership = UserGroupMembership.query.filter_by(
            user_id=member_id,
            group_id=group_id,
            status='active'
        ).first()
        
        if not member_membership:
            return {'success': False, 'error': 'Member not found'}
        
        # Don't allow removing owner
        if member_membership.role == 'owner':
            return {'success': False, 'error': 'Cannot remove group owner'}
        
        # Remove member
        group = UserGroup.query.get(group_id)
        user = User.query.get(member_id)
        
        if group and user:
            group.remove_member(user)
        
        # Create social activity
        activity = UserSocialActivity(
            user_id=admin_id,
            activity_type='remove_member',
            target_type='group',
            target_id=group_id,
            visibility='private',
            allowed_viewers=[member_id],
            metadata={'removed_member_id': member_id}
        )
        
        db.session.add(activity)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Member removed from group'
        }
    
    def get_group_analytics(self, group_id: int) -> Dict[str, Any]:
        """Get analytics for a group"""
        group = UserGroup.query.get(group_id)
        if not group:
            return {'success': False, 'error': 'Group not found'}
        
        # Member statistics
        members = UserGroupMembership.query.filter_by(group_id=group_id, status='active').all()
        role_counts = {}
        for member in members:
            role = member.role
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Activity statistics (simplified)
        activities = UserSocialActivity.query.filter_by(target_type='group', target_id=group_id).count()
        
        # Growth statistics
        recent_members = UserGroupMembership.query.filter(
            and_(
                UserGroupMembership.group_id == group_id,
                UserGroupMembership.status == 'active',
                UserGroupMembership.joined_at >= datetime.now(timezone.utc) - timedelta(days=30)
            )
        ).count()
        
        return {
            'success': True,
            'analytics': {
                'total_members': group.member_count,
                'role_distribution': role_counts,
                'total_activities': activities,
                'new_members_30_days': recent_members,
                'activity_score': group.activity_score,
                'group_type': group.group_type,
                'privacy': group.privacy,
                'created_at': group.created_at.isoformat()
            }
        }


class SocialAnalyticsService:
    """Service for social analytics and insights"""
    
    def __init__(self):
        self.analytics_calculation_days = 30
    
    def calculate_user_social_analytics(self, user_id: int) -> Dict[str, Any]:
        """Calculate comprehensive social analytics for a user"""
        # Get or create analytics record
        analytics = UserRelationshipAnalytics.query.filter_by(user_id=user_id).first()
        
        if not analytics:
            analytics = UserRelationshipAnalytics(user_id=user_id)
        
        # Calculate analytics
        analytics.calculate_analytics(self.analytics_calculation_days)
        
        # Get additional metrics
        social_profile = UserSocialProfile.query.filter_by(user_id=user_id).first()
        
        result = {
            'success': True,
            'analytics': {
                'connection_metrics': {
                    'total_connections': analytics.total_connections,
                    'active_connections': analytics.active_connections,
                    'mutual_connections': analytics.mutual_connections,
                    'connection_strength_avg': analytics.connection_strength_avg
                },
                'interaction_metrics': {
                    'total_interactions': analytics.total_interactions,
                    'interactions_sent': analytics.interactions_sent,
                    'interactions_received': analytics.interactions_received,
                    'avg_response_time': analytics.avg_response_time
                },
                'network_metrics': {
                    'network_density': analytics.network_density,
                    'clustering_coefficient': analytics.clustering_coefficient,
                    'betweenness_centrality': analytics.betweenness_centrality,
                    'closeness_centrality': analytics.closeness_centrality
                },
                'behavioral_patterns': {
                    'interaction_frequency': analytics.interaction_frequency,
                    'preferred_interaction_types': analytics.preferred_interaction_types,
                    'social_circles': analytics.social_circles
                },
                'social_profile': {
                    'followers_count': social_profile.followers_count if social_profile else 0,
                    'following_count': social_profile.following_count if social_profile else 0,
                    'friends_count': social_profile.friends_count if social_profile else 0,
                    'social_influence_score': social_profile.social_influence_score if social_profile else 0.0,
                    'social_activity_level': social_profile.social_activity_level if social_profile else 'low'
                }
            }
        }
        
        return result
    
    def get_connection_analytics(self, user_id: int) -> Dict[str, Any]:
        """Get detailed connection analytics"""
        connections = UserConnection.query.filter_by(user_id=user_id, status='active').all()
        
        # Connection type distribution
        type_counts = {}
        strength_sum = 0
        mutual_count = 0
        
        for conn in connections:
            conn_type = conn.connection_type
            type_counts[conn_type] = type_counts.get(conn_type, 0) + 1
            strength_sum += conn.strength
            if conn.is_mutual:
                mutual_count += 1
        
        # Connection strength distribution
        strength_ranges = {
            'weak': 0,    # 0.0 - 0.3
            'moderate': 0, # 0.3 - 0.7
            'strong': 0   # 0.7 - 1.0
        }
        
        for conn in connections:
            if conn.strength < 0.3:
                strength_ranges['weak'] += 1
            elif conn.strength < 0.7:
                strength_ranges['moderate'] += 1
            else:
                strength_ranges['strong'] += 1
        
        avg_strength = strength_sum / len(connections) if connections else 0.0
        
        return {
            'success': True,
            'analytics': {
                'total_connections': len(connections),
                'connection_types': type_counts,
                'mutual_connections': mutual_count,
                'mutual_ratio': mutual_count / len(connections) if connections else 0.0,
                'avg_strength': avg_strength,
                'strength_distribution': strength_ranges,
                'connection_health': 'good' if avg_strength > 0.5 else 'needs_improvement'
            }
        }
    
    def get_interaction_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get interaction analytics for a user"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        interactions = UserInteraction.query.filter(
            and_(
                UserInteraction.initiator_id == user_id,
                UserInteraction.created_at >= cutoff_date
            )
        ).all()
        
        # Interaction type distribution
        type_counts = {}
        sentiment_scores = []
        response_times = []
        
        for interaction in interactions:
            interaction_type = interaction.interaction_type
            type_counts[interaction_type] = type_counts.get(interaction_type, 0) + 1
            
            if interaction.sentiment_score is not None:
                sentiment_scores.append(interaction.sentiment_score)
            
            if interaction.response_time is not None:
                response_times.append(interaction.response_time)
        
        # Calculate metrics
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # Daily interaction pattern
        daily_pattern = {}
        for interaction in interactions:
            day = interaction.created_at.strftime('%Y-%m-%d')
            daily_pattern[day] = daily_pattern.get(day, 0) + 1
        
        return {
            'success': True,
            'analytics': {
                'total_interactions': len(interactions),
                'interaction_types': type_counts,
                'avg_sentiment_score': avg_sentiment,
                'avg_response_time_hours': avg_response_time / 3600 if avg_response_time else 0.0,
                'daily_pattern': daily_pattern,
                'most_common_type': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
            }
        }
    
    def get_social_graph_analytics(self, user_id: int, depth: int = 2) -> Dict[str, Any]:
        """Get social graph analytics for a user"""
        # This is a simplified implementation
        # In a real system, you'd use graph algorithms
        
        # Get user's connections
        connections = UserConnection.query.filter_by(user_id=user_id, status='active').all()
        
        # Build graph structure
        graph = {
            'nodes': [{'id': user_id, 'label': f'User {user_id}'}],
            'edges': []
        }
        
        node_ids = {user_id}
        
        for conn in connections:
            connected_id = conn.connected_user_id
            if connected_id not in node_ids:
                graph['nodes'].append({'id': connected_id, 'label': f'User {connected_id}'})
                node_ids.add(connected_id)
            
            graph['edges'].append({
                'from': user_id,
                'to': connected_id,
                'weight': conn.strength,
                'type': conn.connection_type,
                'mutual': conn.is_mutual
            })
        
        # Calculate basic graph metrics
        total_nodes = len(graph['nodes'])
        total_edges = len(graph['edges'])
        max_possible_edges = total_nodes * (total_nodes - 1) / 2
        
        return {
            'success': True,
            'analytics': {
                'graph': graph,
                'metrics': {
                    'nodes': total_nodes,
                    'edges': total_edges,
                    'density': total_edges / max_possible_edges if max_possible_edges > 0 else 0.0,
                    'avg_strength': sum(edge['weight'] for edge in graph['edges']) / total_edges if total_edges > 0 else 0.0,
                    'mutual_edges': sum(1 for edge in graph['edges'] if edge['mutual'])
                }
            }
        }
    
    def get_trending_social_activities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trending social activities"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Get activities with highest engagement
        activities = UserSocialActivity.query.filter(
            and_(
                UserSocialActivity.created_at >= cutoff_date,
                UserSocialActivity.visibility == 'public'
            )
        ).order_by(desc(UserSocialActivity.engagement_score)).limit(limit).all()
        
        result = []
        for activity in activities:
            user = activity.user
            result.append({
                'activity_id': activity.id,
                'user_id': activity.user_id,
                'username': user.username if user else 'Unknown',
                'activity_type': activity.activity_type,
                'content': activity.content,
                'engagement_score': activity.engagement_score,
                'likes_count': activity.likes_count,
                'comments_count': activity.comments_count,
                'shares_count': activity.shares_count,
                'created_at': activity.created_at.isoformat()
            })
        
        return result
    
    def get_user_activity_feed(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get personalized activity feed for a user"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Get user's connections
        connections = UserConnection.query.filter_by(user_id=user_id, status='active').all()
        connected_user_ids = [conn.connected_user_id for conn in connections]
        connected_user_ids.append(user_id)  # Include user's own activities
        
        # Get activities from connections
        activities = UserSocialActivity.query.filter(
            and_(
                UserSocialActivity.user_id.in_(connected_user_ids),
                UserSocialActivity.created_at >= cutoff_date,
                UserSocialActivity.visibility.in_(['public', 'friends'])
            )
        ).order_by(desc(UserSocialActivity.created_at)).limit(limit).all()
        
        result = []
        for activity in activities:
            # Check if user can view this activity
            if activity.can_view(user_id):
                user = activity.user
                result.append({
                    'activity_id': activity.id,
                    'user_id': activity.user_id,
                    'username': user.username if user else 'Unknown',
                    'first_name': user.first_name if user else '',
                    'last_name': user.last_name if user else '',
                    'activity_type': activity.activity_type,
                    'content': activity.content,
                    'metadata': activity.metadata,
                    'engagement_score': activity.engagement_score,
                    'likes_count': activity.likes_count,
                    'comments_count': activity.comments_count,
                    'shares_count': activity.shares_count,
                    'created_at': activity.created_at.isoformat(),
                    'can_interact': activity.user_id != user_id
                })
        
        return result


class SocialActivityService:
    """Service for managing social activities"""
    
    def create_activity(self, user_id: int, activity_type: str, content: str = None,
                        target_type: str = None, target_id: int = None,
                        target_user_id: int = None, visibility: str = 'public',
                        allowed_viewers: List[int] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a social activity"""
        activity = UserSocialActivity(
            user_id=user_id,
            activity_type=activity_type,
            content=content,
            target_type=target_type,
            target_id=target_id,
            target_user_id=target_user_id,
            visibility=visibility,
            allowed_viewers=allowed_viewers or [],
            metadata=metadata or {}
        )
        
        db.session.add(activity)
        db.session.commit()
        
        return {
            'success': True,
            'activity_id': activity.id,
            'message': 'Activity created successfully'
        }
    
    def get_user_activities(self, user_id: int, limit: int = 50, activity_type: str = None) -> List[Dict[str, Any]]:
        """Get user's social activities"""
        query = UserSocialActivity.query.filter_by(user_id=user_id)
        
        if activity_type:
            query = query.filter_by(activity_type=activity_type)
        
        activities = query.order_by(desc(UserSocialActivity.created_at)).limit(limit).all()
        
        result = []
        for activity in activities:
            result.append({
                'activity_id': activity.id,
                'activity_type': activity.activity_type,
                'content': activity.content,
                'target_type': activity.target_type,
                'target_id': activity.target_id,
                'target_user_id': activity.target_user_id,
                'visibility': activity.visibility,
                'engagement_score': activity.engagement_score,
                'likes_count': activity.likes_count,
                'comments_count': activity.comments_count,
                'shares_count': activity.shares_count,
                'views_count': activity.views_count,
                'created_at': activity.created_at.isoformat(),
                'updated_at': activity.updated_at.isoformat()
            })
        
        return result
    
    def update_activity_engagement(self, activity_id: int, engagement_type: str, increment: int = 1) -> bool:
        """Update activity engagement metrics"""
        activity = UserSocialActivity.query.get(activity_id)
        if not activity:
            return False
        
        activity.update_engagement(engagement_type, increment)
        db.session.commit()
        
        return True
    
    def delete_activity(self, user_id: int, activity_id: int) -> Dict[str, Any]:
        """Delete a social activity"""
        activity = UserSocialActivity.query.filter_by(id=activity_id, user_id=user_id).first()
        
        if not activity:
            return {'success': False, 'error': 'Activity not found or no permission'}
        
        db.session.delete(activity)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Activity deleted successfully'
        }
