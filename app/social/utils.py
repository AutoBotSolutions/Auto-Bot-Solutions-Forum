"""
Social Relationships Utilities
Auto Bot Solutions Forum

This module provides utility functions for social relationships,
including validation, calculations, and helper functions.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy import and_, or_, func, desc
from app.models import User
from .models import (
    UserConnection, UserSocialProfile, UserGroup, UserGroupMembership,
    UserInteraction, UserRelationshipAnalytics, UserSocialActivity
)


class SocialValidators:
    """Validation utilities for social relationships"""
    
    @staticmethod
    def validate_connection_type(connection_type: str) -> bool:
        """Validate connection type"""
        valid_types = ['follow', 'friend', 'block', 'mute', 'custom']
        return connection_type in valid_types
    
    @staticmethod
    def validate_group_type(group_type: str) -> bool:
        """Validate group type"""
        valid_types = ['community', 'organization', 'team', 'club', 'project']
        return group_type in valid_types
    
    @staticmethod
    def validate_group_privacy(privacy: str) -> bool:
        """Validate group privacy setting"""
        valid_privacy = ['public', 'private', 'invite_only']
        return privacy in valid_privacy
    
    @staticmethod
    def validate_activity_visibility(visibility: str) -> bool:
        """Validate activity visibility"""
        valid_visibility = ['public', 'friends', 'private', 'custom']
        return visibility in valid_visibility
    
    @staticmethod
    def validate_user_role(role: str) -> bool:
        """Validate user role in group"""
        valid_roles = ['member', 'moderator', 'admin', 'owner']
        return role in valid_roles
    
    @staticmethod
    def validate_connection_strength(strength: float) -> bool:
        """Validate connection strength (0.0 to 1.0)"""
        return 0.0 <= strength <= 1.0
    
    @staticmethod
    def validate_username_length(username: str) -> bool:
        """Validate username length"""
        return 3 <= len(username) <= 30
    
    @staticmethod
    def validate_group_name_length(name: str) -> bool:
        """Validate group name length"""
        return 3 <= len(name) <= 100
    
    @staticmethod
    def validate_activity_content(content: str) -> bool:
        """Validate activity content"""
        return len(content.strip()) > 0 if content else True


class SocialCalculators:
    """Calculation utilities for social relationships"""
    
    @staticmethod
    def calculate_connection_strength(interactions: List[Dict[str, Any]], days: int = 30) -> float:
        """Calculate connection strength based on interaction history"""
        if not interactions:
            return 0.0
        
        # Weight recent interactions more heavily
        total_strength = 0.0
        current_time = datetime.now(timezone.utc)
        
        for interaction in interactions:
            days_ago = (current_time - interaction['created_at']).days
            
            if days_ago > days:
                continue
            
            # Calculate time decay
            time_weight = max(0.1, 1.0 - (days_ago / days))
            
            # Interaction type weight
            interaction_weights = {
                'like': 0.1,
                'comment': 0.2,
                'share': 0.3,
                'message': 0.4,
                'mention': 0.15,
                'tag': 0.1
            }
            
            type_weight = interaction_weights.get(interaction['type'], 0.1)
            
            # Combined weight
            combined_weight = time_weight * type_weight
            total_strength += combined_weight
        
        # Normalize to 0.0-1.0 range
        max_possible_strength = days * 0.4  # Assuming max one message per day
        normalized_strength = min(1.0, total_strength / max_possible_strength)
        
        return normalized_strength
    
    @staticmethod
    def calculate_social_influence(user_id: int) -> float:
        """Calculate social influence score for a user"""
        # Get user's social profile
        profile = UserSocialProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return 0.0
        
        # Base influence from followers
        followers_score = min(1.0, profile.followers_count / 1000.0) * 0.4
        
        # Activity score
        activity_score = min(1.0, profile.posts_count / 100.0) * 0.2
        
        # Engagement score
        engagement_score = min(1.0, profile.avg_post_engagement / 50.0) * 0.2
        
        # Recency score
        recency_score = SocialCalculators._calculate_recency_score(profile.last_analytics_update) * 0.1
        
        # Quality score
        quality_score = min(1.0, profile.social_influence_score) * 0.1
        
        return followers_score + activity_score + engagement_score + recency_score + quality_score
    
    @staticmethod
    def _calculate_recency_score(last_activity: datetime) -> float:
        """Calculate recency score based on last activity"""
        if not last_activity:
            return 0.0
        
        days_since_activity = (datetime.now(timezone.utc) - last_activity).days
        
        if days_since_activity < 1:
            return 1.0
        elif days_since_activity < 7:
            return 0.8
        elif days_since_activity < 30:
            return 0.5
        elif days_since_activity < 90:
            return 0.3
        else:
            return 0.1
    
    @staticmethod
    def calculate_network_density(user_id: int) -> float:
        """Calculate network density for a user"""
        # Get user's connections
        connections = UserConnection.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()
        
        if len(connections) < 2:
            return 0.0
        
        # Calculate mutual connections
        mutual_count = 0
        for conn in connections:
            if conn.is_mutual:
                mutual_count += 1
        
        # Density calculation
        max_possible_mutual = len(connections) * (len(connections) - 1) / 2
        density = mutual_count / max_possible_mutual if max_possible_mutual > 0 else 0.0
        
        return density
    
    @staticmethod
    def calculate_clustering_coefficient(user_id: int) -> float:
        """Calculate clustering coefficient for a user's network"""
        # Get user's connections
        connections = UserConnection.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()
        
        if len(connections) < 2:
            return 0.0
        
        connected_users = [conn.connected_user_id for conn in connections]
        mutual_connections = 0
        total_possible = 0
        
        # Check connections between user's connections
        for i, user1_id in enumerate(connected_users):
            for user2_id in connected_users[i+1:]:
                total_possible += 1
                
                # Check if these two users are connected
                connection = UserConnection.query.filter(
                    and_(
                        UserConnection.user_id == user1_id,
                        UserConnection.connected_user_id == user2_id,
                        UserConnection.status == 'active'
                    )
                ).first()
                
                if connection:
                    mutual_connections += 1
        
        return mutual_connections / total_possible if total_possible > 0 else 0.0
    
    @staticmethod
    def calculate_betweenness_centrality(user_id: int) -> float:
        """Calculate betweenness centrality (simplified)"""
        # This is a simplified implementation
        # In a real system, you'd use graph algorithms
        
        connections = UserConnection.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()
        
        # Simplified calculation based on connection count and diversity
        base_score = len(connections) / 100.0
        
        # Bonus for connections to different types of users
        diversity_bonus = 0.0
        connected_user_types = set()
        
        for conn in connections:
            # Get connected user's profile to determine type
            profile = UserSocialProfile.query.filter_by(user_id=conn.connected_user_id).first()
            if profile:
                user_type = profile.social_activity_level
                connected_user_types.add(user_type)
        
        diversity_bonus = len(connected_user_types) * 0.1
        
        return min(1.0, base_score + diversity_bonus)
    
    @staticmethod
    def calculate_closeness_centrality(user_id: int) -> float:
        """Calculate closeness centrality (simplified)"""
        # This is a simplified implementation
        # In a real system, you'd use graph algorithms
        
        connections = UserConnection.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()
        
        # Simplified calculation based on connection strength
        total_strength = sum(conn.strength for conn in connections)
        avg_strength = total_strength / len(connections) if connections else 0.0
        
        return avg_strength
    
    @staticmethod
    def calculate_engagement_score(activity: UserSocialActivity) -> float:
        """Calculate engagement score for an activity"""
        base_score = (
            activity.likes_count * 1.0 +
            activity.comments_count * 2.0 +
            activity.shares_count * 3.0 +
            activity.views_count * 0.1
        )
        
        # Time decay factor
        hours_since_creation = (datetime.now(timezone.utc) - activity.created_at).total_seconds() / 3600
        time_decay = max(0.1, 1.0 - (hours_since_creation / (24 * 7)))  # Decay over 1 week
        
        return base_score * time_decay
    
    @staticmethod
    def calculate_group_activity_score(group_id: int, days: int = 30) -> float:
        """Calculate activity score for a group"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get recent activities
        activities = UserSocialActivity.query.filter(
            and_(
                UserSocialActivity.target_type == 'group',
                UserSocialActivity.target_id == group_id,
                UserSocialActivity.created_at >= cutoff_date
            )
        ).all()
        
        if not activities:
            return 0.0
        
        # Calculate activity score based on activity count and engagement
        total_engagement = sum(SocialCalculators.calculate_engagement_score(activity) for activity in activities)
        
        # Normalize based on group size
        group = UserGroup.query.get(group_id)
        if group and group.member_count > 0:
            normalized_score = total_engagement / group.member_count
        else:
            normalized_score = total_engagement
        
        return min(1.0, normalized_score / 100.0)  # Normalize to 0.0-1.0


class SocialHelpers:
    """Helper functions for social relationships"""
    
    @staticmethod
    def get_connection_between_users(user1_id: int, user2_id: int, connection_type: str = None) -> Optional[UserConnection]:
        """Get connection between two users"""
        query = UserConnection.query.filter(
            or_(
                and_(UserConnection.user_id == user1_id, UserConnection.connected_user_id == user2_id),
                and_(UserConnection.user_id == user2_id, UserConnection.connected_user_id == user1_id)
            )
        )
        
        if connection_type:
            query = query.filter_by(connection_type=connection_type)
        
        return query.first()
    
    @staticmethod
    def are_friends(user1_id: int, user2_id: int) -> bool:
        """Check if two users are friends"""
        connection = SocialHelpers.get_connection_between_users(user1_id, user2_id, 'friend')
        return connection is not None and connection.status == 'active'
    
    @staticmethod
    def is_following(user1_id: int, user2_id: int) -> bool:
        """Check if user1 is following user2"""
        connection = UserConnection.query.filter_by(
            user_id=user1_id,
            connected_user_id=user2_id,
            connection_type='follow',
            status='active'
        ).first()
        
        return connection is not None
    
    @staticmethod
    def is_blocked(user1_id: int, user2_id: int) -> bool:
        """Check if user1 is blocked by user2"""
        connection = UserConnection.query.filter_by(
            user_id=user2_id,
            connected_user_id=user1_id,
            connection_type='block',
            status='active'
        ).first()
        
        return connection is not None
    
    @staticmethod
    def can_interact(user1_id: int, user2_id: int) -> bool:
        """Check if user1 can interact with user2"""
        # Users can't interact with themselves
        if user1_id == user2_id:
            return False
        
        # Check if blocked
        if SocialHelpers.is_blocked(user1_id, user2_id):
            return False
        
        # Check privacy settings
        profile = UserSocialProfile.query.filter_by(user_id=user2_id).first()
        if profile:
            if profile.privacy_level == 'private':
                # Only friends can interact with private profiles
                return SocialHelpers.are_friends(user1_id, user2_id)
            elif profile.privacy_level == 'friends':
                # Friends and followers can interact
                return SocialHelpers.are_friends(user1_id, user2_id) or SocialHelpers.is_following(user1_id, user2_id)
        
        return True
    
    @staticmethod
    def get_mutual_friends(user1_id: int, user2_id: int) -> List[int]:
        """Get mutual friends between two users"""
        user1_friends = set()
        user2_friends = set()
        
        # Get user1's friends
        user1_connections = UserConnection.query.filter_by(
            user_id=user1_id,
            connection_type='friend',
            status='active'
        ).all()
        
        for conn in user1_connections:
            user1_friends.add(conn.connected_user_id)
        
        # Get user2's friends
        user2_connections = UserConnection.query.filter_by(
            user_id=user2_id,
            connection_type='friend',
            status='active'
        ).all()
        
        for conn in user2_connections:
            user2_friends.add(conn.connected_user_id)
        
        # Find mutual friends
        mutual_ids = user1_friends.intersection(user2_friends)
        
        return list(mutual_ids)
    
    @staticmethod
    def get_user_social_graph(user_id: int, depth: int = 2) -> Dict[str, Any]:
        """Get user's social graph up to specified depth"""
        graph = {
            'nodes': {user_id: {'id': user_id, 'depth': 0}},
            'edges': []
        }
        
        current_depth = 0
        current_nodes = {user_id}
        visited_nodes = {user_id}
        
        while current_depth < depth:
            next_nodes = set()
            
            for node_id in current_nodes:
                # Get connections for this node
                connections = UserConnection.query.filter_by(
                    user_id=node_id,
                    status='active'
                ).all()
                
                for conn in connections:
                    connected_id = conn.connected_user_id
                    
                    if connected_id not in visited_nodes:
                        # Add node
                        graph['nodes'][connected_id] = {
                            'id': connected_id,
                            'depth': current_depth + 1
                        }
                        visited_nodes.add(connected_id)
                        next_nodes.add(connected_id)
                    
                    # Add edge
                    graph['edges'].append({
                        'from': node_id,
                        'to': connected_id,
                        'type': conn.connection_type,
                        'strength': conn.strength,
                        'mutual': conn.is_mutual
                    })
            
            current_nodes = next_nodes
            current_depth += 1
            
            if not current_nodes:
                break
        
        return graph
    
    @staticmethod
    def get_user_social_circles(user_id: int) -> List[Dict[str, Any]]:
        """Identify user's social circles based on interaction patterns"""
        # Get user's interactions
        interactions = UserInteraction.query.filter_by(initiator_id=user_id).all()
        
        # Group interactions by target users
        user_interactions = {}
        for interaction in interactions:
            target_id = interaction.target_id
            if target_id not in user_interactions:
                user_interactions[target_id] = []
            user_interactions[target_id].append(interaction)
        
        # Simple clustering based on interaction frequency and type
        circles = []
        processed_users = set()
        
        for target_id, user_interaction_list in user_interactions.items():
            if target_id in processed_users:
                continue
            
            # Start a new circle
            circle_users = [target_id]
            processed_users.add(target_id)
            
            # Find users with similar interaction patterns
            for other_id, other_interaction_list in user_interactions.items():
                if other_id in processed_users:
                    continue
                
                # Check if interaction patterns are similar
                if SocialHelpers._similar_interaction_patterns(
                    user_interaction_list, 
                    other_interaction_list
                ):
                    circle_users.append(other_id)
                    processed_users.add(other_id)
            
            if len(circle_users) > 1:
                circles.append({
                    'name': f'Circle {len(circles) + 1}',
                    'members': circle_users,
                    'size': len(circle_users)
                })
        
        return circles
    
    @staticmethod
    def _similar_interaction_patterns(interactions1: List[UserInteraction], 
                                    interactions2: List[UserInteraction]) -> bool:
        """Check if two interaction patterns are similar"""
        # Get interaction types for both users
        types1 = set(interaction.interaction_type for interaction in interactions1)
        types2 = set(interaction.interaction_type for interaction in interactions2)
        
        # Check if they share at least 2 interaction types
        common_types = types1.intersection(types2)
        
        if len(common_types) < 2:
            return False
        
        # Check if interaction frequencies are similar
        freq1 = len(interactions1)
        freq2 = len(interactions2)
        
        # Consider similar if frequencies are within 50% of each other
        if freq1 == 0 or freq2 == 0:
            return False
        
        ratio = max(freq1, freq2) / min(freq1, freq2)
        
        return ratio <= 1.5
    
    @staticmethod
    def get_recommendations_for_user(user_id: int, recommendation_type: str = 'all') -> Dict[str, List[Dict[str, Any]]]:
        """Get recommendations for a user"""
        recommendations = {
            'users_to_follow': [],
            'groups_to_join': [],
            'content_to_see': []
        }
        
        if recommendation_type in ['all', 'users']:
            recommendations['users_to_follow'] = SocialHelpers._get_user_follow_recommendations(user_id)
        
        if recommendation_type in ['all', 'groups']:
            recommendations['groups_to_join'] = SocialHelpers._get_group_recommendations(user_id)
        
        if recommendation_type in ['all', 'content']:
            recommendations['content_to_see'] = SocialHelpers._get_content_recommendations(user_id)
        
        return recommendations
    
    @staticmethod
    def _get_user_follow_recommendations(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user follow recommendations"""
        # Get user's current connections
        current_connections = UserConnection.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()
        
        connected_user_ids = {conn.connected_user_id for conn in current_connections}
        connected_user_ids.add(user_id)  # Exclude self
        
        # Get friends of friends (2nd degree connections)
        friends_of_friends = set()
        
        for conn in current_connections:
            if conn.connection_type == 'friend':
                friend_connections = UserConnection.query.filter_by(
                    user_id=conn.connected_user_id,
                    connection_type='friend',
                    status='active'
                ).all()
                
                for friend_conn in friend_connections:
                    friends_of_friends.add(friend_conn.connected_user_id)
        
        # Remove already connected users
        recommendations = friends_of_friends - connected_user_ids
        
        # Get user details for recommendations
        recommended_users = []
        
        for rec_id in list(recommendations)[:limit]:
            user = User.query.get(rec_id)
            if user:
                # Calculate recommendation score
                score = SocialHelpers._calculate_user_recommendation_score(user_id, rec_id)
                
                recommended_users.append({
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'recommendation_score': score,
                    'reason': 'Friend of friend'
                })
        
        # Sort by recommendation score
        recommended_users.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return recommended_users
    
    @staticmethod
    def _get_group_recommendations(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get group recommendations"""
        # Get user's current groups
        current_groups = UserGroupMembership.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()
        
        current_group_ids = {membership.group_id for membership in current_groups}
        
        # Get groups user's friends are in
        friends = SocialHelpers._get_user_friends(user_id)
        friend_ids = [friend['user_id'] for friend in friends]
        
        friend_groups = set()
        for friend_id in friend_ids:
            friend_memberships = UserGroupMembership.query.filter_by(
                user_id=friend_id,
                status='active'
            ).all()
            
            for membership in friend_memberships:
                friend_groups.add(membership.group_id)
        
        # Remove groups user is already in
        recommended_group_ids = friend_groups - current_group_ids
        
        # Get group details
        recommended_groups = []
        
        for group_id in list(recommended_group_ids)[:limit]:
            group = UserGroup.query.get(group_id)
            if group and group.privacy == 'public':
                # Calculate recommendation score
                score = SocialHelpers._calculate_group_recommendation_score(user_id, group_id)
                
                recommended_groups.append({
                    'group_id': group.id,
                    'name': group.name,
                    'description': group.description,
                    'member_count': group.member_count,
                    'recommendation_score': score,
                    'reason': 'Friends are members'
                })
        
        # Sort by recommendation score
        recommended_groups.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return recommended_groups
    
    @staticmethod
    def _get_content_recommendations(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get content recommendations based on user's social graph"""
        # Get user's connections
        connections = UserConnection.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()
        
        connected_user_ids = [conn.connected_user_id for conn in connections]
        
        # Get popular activities from connections
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        activities = UserSocialActivity.query.filter(
            and_(
                UserSocialActivity.user_id.in_(connected_user_ids),
                UserSocialActivity.created_at >= cutoff_date,
                UserSocialActivity.visibility == 'public'
            )
        ).order_by(desc(UserSocialActivity.engagement_score)).limit(limit).all()
        
        recommended_content = []
        
        for activity in activities:
            user = activity.user
            recommended_content.append({
                'activity_id': activity.id,
                'user_id': activity.user_id,
                'username': user.username if user else 'Unknown',
                'activity_type': activity.activity_type,
                'content': activity.content,
                'engagement_score': activity.engagement_score,
                'created_at': activity.created_at.isoformat(),
                'reason': 'Popular in your network'
            })
        
        return recommended_content
    
    @staticmethod
    def _get_user_friends(user_id: int) -> List[Dict[str, Any]]:
        """Get user's friends"""
        friends = UserConnection.query.filter_by(
            user_id=user_id,
            connection_type='friend',
            status='active'
        ).all()
        
        result = []
        for friend in friends:
            user = User.query.get(friend.connected_user_id)
            if user:
                result.append({
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                })
        
        return result
    
    @staticmethod
    def _calculate_user_recommendation_score(user_id: int, recommended_user_id: int) -> float:
        """Calculate recommendation score for a user"""
        score = 0.0
        
        # Mutual friends bonus
        mutual_friends = SocialHelpers.get_mutual_friends(user_id, recommended_user_id)
        score += len(mutual_friends) * 0.2
        
        # Similar interests bonus (simplified)
        # In a real system, you'd analyze user behavior and preferences
        score += 0.1
        
        # Activity level bonus
        profile = UserSocialProfile.query.filter_by(user_id=recommended_user_id).first()
        if profile:
            score += min(0.3, profile.posts_count / 100.0)
        
        return min(1.0, score)
    
    @staticmethod
    def _calculate_group_recommendation_score(user_id: int, group_id: int) -> float:
        """Calculate recommendation score for a group"""
        score = 0.0
        
        # Friends in group bonus
        friends = SocialHelpers._get_user_friends(user_id)
        friend_ids = [friend['user_id'] for friend in friends]
        
        friend_memberships = UserGroupMembership.query.filter(
            and_(
                UserGroupMembership.user_id.in_(friend_ids),
                UserGroupMembership.group_id == group_id,
                UserGroupMembership.status == 'active'
            )
        ).count()
        
        score += friend_memberships * 0.3
        
        # Group activity bonus
        group = UserGroup.query.get(group_id)
        if group:
            score += min(0.4, group.activity_score)
            
            # Group size bonus (prefer medium-sized groups)
            if 10 <= group.member_count <= 100:
                score += 0.2
            elif group.member_count > 100:
                score += 0.1
        
        return min(1.0, score)


class SocialActivityProcessor:
    """Processor for social activities and events"""
    
    @staticmethod
    def process_interaction(user_id: int, target_user_id: int, interaction_type: str, 
                          context_type: str = None, context_id: int = None) -> Dict[str, Any]:
        """Process a user interaction"""
        # Create interaction record
        interaction = UserInteraction(
            initiator_id=user_id,
            target_id=target_user_id,
            interaction_type=interaction_type,
            context_type=context_type,
            context_id=context_id
        )
        
        db.session.add(interaction)
        
        # Update connection strength
        from .service import SocialService
        social_service = SocialService()
        social_service.update_connection_strength(user_id, target_user_id, interaction_type)
        
        # Create social activity if appropriate
        if interaction_type in ['like', 'comment', 'share']:
            activity = UserSocialActivity(
                user_id=user_id,
                activity_type=f'{interaction_type}_content',
                target_type=context_type,
                target_id=context_id,
                target_user_id=target_user_id,
                visibility='public'
            )
            
            db.session.add(activity)
        
        db.session.commit()
        
        return {
            'success': True,
            'interaction_id': interaction.id,
            'message': 'Interaction processed successfully'
        }
    
    @staticmethod
    def process_connection_change(user_id: int, connected_user_id: int, 
                                connection_type: str, action: str) -> Dict[str, Any]:
        """Process a connection change"""
        if action == 'create':
            from .service import SocialService
            social_service = SocialService()
            
            if connection_type == 'follow':
                return social_service.follow_user(user_id, connected_user_id)
            elif connection_type == 'friend':
                return social_service.send_friend_request(user_id, connected_user_id)
            elif connection_type == 'block':
                return social_service.block_user(user_id, connected_user_id)
        
        elif action == 'remove':
            from .service import SocialService
            social_service = SocialService()
            
            if connection_type == 'follow':
                return social_service.unfollow_user(user_id, connected_user_id)
            elif connection_type == 'block':
                return social_service.unblock_user(user_id, connected_user_id)
        
        return {'success': False, 'error': 'Invalid action or connection type'}
    
    @staticmethod
    def process_group_activity(user_id: int, group_id: int, activity_type: str, 
                             metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a group activity"""
        # Check if user is a member
        membership = UserGroupMembership.query.filter_by(
            user_id=user_id,
            group_id=group_id,
            status='active'
        ).first()
        
        if not membership:
            return {'success': False, 'error': 'Not a member of this group'}
        
        # Create social activity
        activity = UserSocialActivity(
            user_id=user_id,
            activity_type=activity_type,
            target_type='group',
            target_id=group_id,
            metadata=metadata or {},
            visibility='public'
        )
        
        db.session.add(activity)
        
        # Update member contribution score
        membership.update_contribution(0.1)
        
        # Update group activity score
        group = UserGroup.query.get(group_id)
        if group:
            group.update_activity_score()
        
        db.session.commit()
        
        return {
            'success': True,
            'activity_id': activity.id,
            'message': 'Group activity processed successfully'
        }
    
    @staticmethod
    def generate_activity_feed(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Generate personalized activity feed for a user"""
        from .service import SocialAnalyticsService
        analytics_service = SocialAnalyticsService()
        
        return analytics_service.get_user_activity_feed(user_id, limit)
    
    @staticmethod
    def update_trending_activities():
        """Update trending activities (for background processing)"""
        # This would typically be run as a background task
        from .service import SocialAnalyticsService
        analytics_service = SocialAnalyticsService()
        
        # Get top trending activities
        trending = analytics_service.get_trending_social_activities(limit=100)
        
        # Update trending scores in activities
        for i, activity_data in enumerate(trending):
            activity = UserSocialActivity.query.get(activity_data['activity_id'])
            if activity:
                # Update trending score based on position
                activity.metadata = activity.metadata or {}
                activity.metadata['trending_score'] = 100 - i
                activity.metadata['trending_updated'] = datetime.now(timezone.utc).isoformat()
        
        db.session.commit()
        
        return len(trending)
