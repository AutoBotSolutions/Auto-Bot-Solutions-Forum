"""
Social Features System

This module implements social features including connections, networking, activity feeds,
user recommendations, social discovery, connection suggestions, and network analytics.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import User
from app.user.models import UserSocialConnection, UserAnalytics
import json
from sqlalchemy import func, desc, and_, or_


class SocialConnectionManager:
    """Social connection management system"""
    
    @staticmethod
    def create_connection(user_id, connected_user_id, connection_type='follow', privacy_settings=None, message=None):
        """Create a social connection"""
        # Prevent self-connections
        if user_id == connected_user_id:
            return {'success': False, 'message': 'Cannot connect to yourself'}
        
        # Check if connection already exists
        existing = UserSocialConnection.query.filter_by(
            user_id=user_id,
            connected_user_id=connected_user_id,
            connection_type=connection_type,
            status='active'
        ).first()
        
        if existing:
            return {'success': False, 'message': 'Connection already exists'}
        
        # Create connection
        connection = UserSocialConnection.create_connection(
            user_id=user_id,
            connected_user_id=connected_user_id,
            connection_type=connection_type,
            privacy_settings=privacy_settings or {}
        )
        
        # Track analytics
        SocialConnectionManager._track_connection_analytics(user_id, connected_user_id, connection_type, 'created')
        
        # Create notification for connection request (if applicable)
        if connection_type in ['friend', 'colleague']:
            SocialNotificationManager.create_connection_notification(
                user_id=connected_user_id,
                from_user_id=user_id,
                connection_type=connection_type,
                message=message
            )
        
        return {
            'success': True,
            'connection_id': connection.id,
            'message': f'{connection_type.title()} connection created successfully'
        }
    
    @staticmethod
    def accept_connection(connection_id, user_id):
        """Accept a pending connection request"""
        connection = UserSocialConnection.query.filter_by(
            id=connection_id,
            connected_user_id=user_id,
            status='pending'
        ).first()
        
        if not connection:
            return {'success': False, 'message': 'Connection request not found'}
        
        connection.update_status('active')
        SocialConnectionManager._track_connection_analytics(
            connection.user_id, 
            connection.connected_user_id, 
            connection.connection_type, 
            'accepted'
        )
        
        return {
            'success': True,
            'message': 'Connection request accepted'
        }
    
    @staticmethod
    def decline_connection(connection_id, user_id):
        """Decline a pending connection request"""
        connection = UserSocialConnection.query.filter_by(
            id=connection_id,
            connected_user_id=user_id,
            status='pending'
        ).first()
        
        if not connection:
            return {'success': False, 'message': 'Connection request not found'}
        
        connection.update_status('declined')
        SocialConnectionManager._track_connection_analytics(
            connection.user_id, 
            connection.connected_user_id, 
            connection.connection_type, 
            'declined'
        )
        
        return {
            'success': True,
            'message': 'Connection request declined'
        }
    
    @staticmethod
    def remove_connection(user_id, connected_user_id, connection_type=None):
        """Remove a social connection"""
        query = UserSocialConnection.query.filter_by(
            user_id=user_id,
            connected_user_id=connected_user_id,
            status='active'
        )
        
        if connection_type:
            query = query.filter_by(connection_type=connection_type)
        
        connection = query.first()
        
        if not connection:
            return {'success': False, 'message': 'Connection not found'}
        
        connection.delete_connection()
        SocialConnectionManager._track_connection_analytics(
            user_id, 
            connected_user_id, 
            connection.connection_type, 
            'removed'
        )
        
        return {
            'success': True,
            'message': 'Connection removed successfully'
        }
    
    @staticmethod
    def get_connections(user_id, connection_type=None, status='active', limit=None, offset=0):
        """Get user's social connections"""
        connections = UserSocialConnection.get_connections(user_id, connection_type, status)
        
        if limit:
            connections = connections.limit(limit).offset(offset)
        
        result = []
        for connection in connections:
            connected_user = User.query.get(connection.connected_user_id)
            if connected_user:
                result.append({
                    'connection_id': connection.id,
                    'user': {
                        'id': connected_user.id,
                        'username': connected_user.username,
                        'email': connected_user.email,
                        'avatar_url': getattr(connected_user, 'avatar_url', None)
                    },
                    'connection_type': connection.connection_type,
                    'status': connection.status,
                    'privacy_settings': connection.privacy_settings,
                    'created_at': connection.created_at.isoformat(),
                    'updated_at': connection.updated_at.isoformat()
                })
        
        return result
    
    @staticmethod
    def get_mutual_connections(user_id, other_user_id):
        """Get mutual connections between two users"""
        user_connections = UserSocialConnection.get_following(user_id)
        other_connections = UserSocialConnection.get_following(other_user_id)
        
        user_following_ids = {conn.connected_user_id for conn in user_connections}
        other_following_ids = {conn.connected_user_id for conn in other_connections}
        
        mutual_ids = user_following_ids.intersection(other_following_ids)
        
        mutual_users = []
        for user_id in mutual_ids:
            user = User.query.get(user_id)
            if user:
                mutual_users.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'avatar_url': getattr(user, 'avatar_url', None)
                })
        
        return mutual_users
    
    @staticmethod
    def get_connection_stats(user_id):
        """Get user's connection statistics"""
        following = UserSocialConnection.get_following(user_id)
        followers = UserSocialConnection.get_followers(user_id)
        friends = UserSocialConnection.get_friends(user_id)
        
        # Get connections by type
        connections_by_type = {}
        for connection in following:
            conn_type = connection.connection_type
            if conn_type not in connections_by_type:
                connections_by_type[conn_type] = 0
            connections_by_type[conn_type] += 1
        
        return {
            'following_count': len(following),
            'followers_count': len(followers),
            'friends_count': len(friends),
            'connections_by_type': connections_by_type,
            'total_connections': len(following) + len(followers)
        }
    
    @staticmethod
    def _track_connection_analytics(user_id, connected_user_id, connection_type, action):
        """Track connection analytics"""
        metadata = {
            'connected_user_id': connected_user_id,
            'connection_type': connection_type,
            'action': action
        }
        
        UserAnalytics.track_metric(
            user_id=user_id,
            metric_type='social_connection',
            value=1,
            metadata=metadata
        )


class SocialFeedManager:
    """Social feed generation and management"""
    
    @staticmethod
    def generate_feed(user_id, limit=20, include_types=None, exclude_types=None):
        """Generate social feed for a user"""
        from app.models import Post, Comment
        
        # Get user's connections
        following = UserSocialConnection.get_following(user_id)
        following_ids = [conn.connected_user_id for conn in following]
        
        # Include user's own content
        following_ids.append(user_id)
        
        # Get posts from followed users
        posts_query = Post.query.filter(
            Post.user_id.in_(following_ids)
        ).order_by(desc(Post.created_at))
        
        if include_types:
            posts_query = posts_query.filter(Post.type.in_(include_types))
        
        if exclude_types:
            posts_query = posts_query.filter(~Post.type.in_(exclude_types))
        
        posts = posts_query.limit(limit).all()
        
        # Format feed items
        feed_items = []
        for post in posts:
            author = User.query.get(post.user_id)
            
            # Get engagement metrics
            likes_count = post.likes.count() if hasattr(post, 'likes') else 0
            comments_count = post.comments.count() if hasattr(post, 'comments') else 0
            
            feed_items.append({
                'id': post.id,
                'type': 'post',
                'content': post.content,
                'author': {
                    'id': author.id,
                    'username': author.username,
                    'avatar_url': getattr(author, 'avatar_url', None)
                },
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat() if post.updated_at else None,
                'engagement': {
                    'likes': likes_count,
                    'comments': comments_count,
                    'shares': 0
                },
                'metadata': {
                    'post_type': getattr(post, 'type', 'text'),
                    'is_pinned': getattr(post, 'is_pinned', False),
                    'tags': getattr(post, 'tags', [])
                }
            })
        
        return feed_items
    
    @staticmethod
    def get_activity_feed(user_id, days=7, limit=50):
        """Get user's activity feed"""
        from app.user.models import UserSocialConnection, UserAnalytics
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user's connections
        following = UserSocialConnection.get_following(user_id)
        following_ids = [conn.connected_user_id for conn in following]
        
        # Get activities from connections
        activities = UserAnalytics.query.filter(
            UserAnalytics.user_id.in_(following_ids),
            UserAnalytics.timestamp >= start_date,
            UserAnalytics.timestamp <= end_date,
            UserAnalytics.metric_type.in_(['post_created', 'comment_created', 'like_given', 'share_created'])
        ).order_by(desc(UserAnalytics.timestamp)).limit(limit).all()
        
        # Format activity items
        activity_items = []
        for activity in activities:
            user = User.query.get(activity.user_id)
            metadata = activity.metadata or {}
            
            activity_items.append({
                'id': activity.id,
                'type': activity.metric_type,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'avatar_url': getattr(user, 'avatar_url', None)
                },
                'timestamp': activity.timestamp.isoformat(),
                'metadata': metadata,
                'value': activity.value
            })
        
        return activity_items
    
    @staticmethod
    def get_trending_content(user_id, hours=24, limit=10):
        """Get trending content from user's network"""
        from app.models import Post
        
        # Get user's connections
        following = UserSocialConnection.get_following(user_id)
        following_ids = [conn.connected_user_id for conn in following]
        
        # Get recent posts with high engagement
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        posts = Post.query.filter(
            Post.user_id.in_(following_ids),
            Post.created_at >= start_time
        ).all()
        
        # Calculate engagement scores
        trending_posts = []
        for post in posts:
            engagement_score = SocialFeedManager._calculate_engagement_score(post)
            
            trending_posts.append({
                'post': post,
                'engagement_score': engagement_score
            })
        
        # Sort by engagement score
        trending_posts.sort(key=lambda x: x['engagement_score'], reverse=True)
        
        # Format and return top posts
        result = []
        for item in trending_posts[:limit]:
            post = item['post']
            author = User.query.get(post.user_id)
            
            result.append({
                'id': post.id,
                'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                'author': {
                    'id': author.id,
                    'username': author.username,
                    'avatar_url': getattr(author, 'avatar_url', None)
                },
                'engagement_score': item['engagement_score'],
                'created_at': post.created_at.isoformat()
            })
        
        return result
    
    @staticmethod
    def _calculate_engagement_score(post):
        """Calculate engagement score for a post"""
        score = 0
        
        # Base score from likes
        if hasattr(post, 'likes'):
            score += post.likes.count() * 1
        
        # Score from comments
        if hasattr(post, 'comments'):
            score += post.comments.count() * 2
        
        # Score from shares
        if hasattr(post, 'shares'):
            score += post.shares.count() * 3
        
        # Time decay (newer posts get higher scores)
        hours_old = (datetime.utcnow() - post.created_at).total_seconds() / 3600
        time_factor = max(0.1, 1 - (hours_old / 24))  # Decay over 24 hours
        score *= time_factor
        
        return score


class UserRecommendationManager:
    """User recommendation and discovery system"""
    
    @staticmethod
    def get_recommendations(user_id, limit=10, recommendation_type='all'):
        """Get user recommendations"""
        recommendations = []
        
        if recommendation_type in ['all', 'similar_users']:
            similar_users = UserRecommendationManager._get_similar_users(user_id, limit//2)
            recommendations.extend(similar_users)
        
        if recommendation_type in ['all', 'trending_users']:
            trending_users = UserRecommendationManager._get_trending_users(limit//2)
            recommendations.extend(trending_users)
        
        if recommendation_type in ['all', 'mutual_friends']:
            mutual_friends = UserRecommendationManager._get_mutual_friend_recommendations(user_id, limit//2)
            recommendations.extend(mutual_friends)
        
        # Remove duplicates and existing connections
        seen_ids = set()
        filtered_recommendations = []
        
        for rec in recommendations:
            if rec['user']['id'] not in seen_ids:
                # Check if already connected
                if not UserSocialConnection.is_connected(user_id, rec['user']['id'], 'follow'):
                    seen_ids.add(rec['user']['id'])
                    filtered_recommendations.append(rec)
        
        return filtered_recommendations[:limit]
    
    @staticmethod
    def _get_similar_users(user_id, limit=10):
        """Get users with similar interests"""
        user = User.query.get(user_id)
        if not user:
            return []
        
        # Get user's interests (placeholder - would need to implement interest tracking)
        user_interests = getattr(user, 'interests', [])
        
        # Find users with similar interests
        similar_users = []
        
        # This is a simplified implementation
        # In a real system, you'd use more sophisticated similarity algorithms
        all_users = User.query.filter(User.id != user_id).limit(limit * 2).all()
        
        for other_user in all_users:
            # Skip if already connected
            if UserSocialConnection.is_connected(user_id, other_user.id, 'follow'):
                continue
            
            # Calculate similarity score (simplified)
            similarity_score = UserRecommendationManager._calculate_similarity(user, other_user)
            
            if similarity_score > 0.3:  # Threshold for similarity
                similar_users.append({
                    'user': {
                        'id': other_user.id,
                        'username': other_user.username,
                        'email': other_user.email,
                        'avatar_url': getattr(other_user, 'avatar_url', None)
                    },
                    'recommendation_type': 'similar_user',
                    'score': similarity_score,
                    'reason': 'Similar interests and activity patterns'
                })
        
        # Sort by similarity score
        similar_users.sort(key=lambda x: x['score'], reverse=True)
        
        return similar_users[:limit]
    
    @staticmethod
    def _get_trending_users(limit=10):
        """Get trending users based on recent activity"""
        # Get users with high recent activity
        start_time = datetime.utcnow() - timedelta(days=7)
        
        # This is a simplified implementation
        # In a real system, you'd use more sophisticated trending algorithms
        active_users = db.session.query(
            UserAnalytics.user_id,
            func.count(UserAnalytics.id).label('activity_count')
        ).filter(
            UserAnalytics.timestamp >= start_time
        ).group_by(UserAnalytics.user_id).order_by(desc('activity_count')).limit(limit * 2).all()
        
        trending_users = []
        for user_id, activity_count in active_users:
            user = User.query.get(user_id)
            if user:
                trending_users.append({
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'avatar_url': getattr(user, 'avatar_url', None)
                    },
                    'recommendation_type': 'trending_user',
                    'score': activity_count,
                    'reason': f'{activity_count} activities in the last 7 days'
                })
        
        return trending_users[:limit]
    
    @staticmethod
    def _get_mutual_friend_recommendations(user_id, limit=10):
        """Get recommendations based on mutual friends"""
        # Get user's friends
        friends = UserSocialConnection.get_friends(user_id)
        friend_ids = [friend.connected_user_id for friend in friends]
        
        # Get friends of friends
        recommendations = {}
        
        for friend_id in friend_ids:
            friends_of_friend = UserSocialConnection.get_following(friend_id)
            
            for connection in friends_of_friend:
                # Skip if it's the original user or already connected
                if (connection.connected_user_id == user_id or 
                    UserSocialConnection.is_connected(user_id, connection.connected_user_id, 'follow')):
                    continue
                
                # Count mutual friends
                if connection.connected_user_id not in recommendations:
                    recommendations[connection.connected_user_id] = {
                        'user_id': connection.connected_user_id,
                        'mutual_friends': 0,
                        'mutual_friend_ids': []
                    }
                
                recommendations[connection.connected_user_id]['mutual_friends'] += 1
                recommendations[connection.connected_user_id]['mutual_friend_ids'].append(friend_id)
        
        # Convert to list and sort by mutual friends count
        result = []
        for user_id, data in recommendations.items():
            user = User.query.get(user_id)
            if user:
                result.append({
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'avatar_url': getattr(user, 'avatar_url', None)
                    },
                    'recommendation_type': 'mutual_friend',
                    'score': data['mutual_friends'],
                    'reason': f'{data["mutual_friends"]} mutual friends',
                    'mutual_friends': data['mutual_friends'],
                    'mutual_friend_ids': data['mutual_friend_ids']
                })
        
        result.sort(key=lambda x: x['score'], reverse=True)
        
        return result[:limit]
    
    @staticmethod
    def _calculate_similarity(user1, user2):
        """Calculate similarity score between two users"""
        # This is a simplified implementation
        # In a real system, you'd use more sophisticated algorithms
        
        score = 0.0
        
        # Similar registration time (within 6 months)
        if user1.created_at and user2.created_at:
            time_diff = abs((user1.created_at - user2.created_at).days)
            if time_diff <= 180:  # 6 months
                score += 0.2
        
        # Similar activity levels (placeholder)
        # In a real system, you'd compare actual activity patterns
        score += 0.3  # Random similarity for demonstration
        
        return min(score, 1.0)


class SocialDiscoveryManager:
    """Social discovery and exploration system"""
    
    @staticmethod
    def discover_users(user_id, filters=None, limit=20, offset=0):
        """Discover new users based on filters"""
        query = User.query.filter(User.id != user_id)
        
        if filters:
            # Apply filters
            if 'location' in filters and filters['location']:
                query = query.filter(User.location.ilike(f"%{filters['location']}%"))
            
            if 'interests' in filters and filters['interests']:
                # This would require implementing interest tracking
                pass
            
            if 'min_age' in filters:
                # This would require implementing age calculation
                pass
            
            if 'max_age' in filters:
                # This would require implementing age calculation
                pass
        
        # Exclude already connected users
        following = UserSocialConnection.get_following(user_id)
        following_ids = [conn.connected_user_id for conn in following]
        
        if following_ids:
            query = query.filter(~User.id.in_(following_ids))
        
        users = query.limit(limit).offset(offset).all()
        
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'location': getattr(user, 'location', None),
                'bio': getattr(user, 'bio', None),
                'avatar_url': getattr(user, 'avatar_url', None),
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'stats': SocialDiscoveryManager._get_user_stats(user.id)
            })
        
        return result
    
    @staticmethod
    def _get_user_stats(user_id):
        """Get user statistics"""
        from app.models import Post
        
        # Get basic stats
        posts_count = Post.query.filter_by(user_id=user_id).count()
        followers_count = len(UserSocialConnection.get_followers(user_id))
        following_count = len(UserSocialConnection.get_following(user_id))
        
        return {
            'posts': posts_count,
            'followers': followers_count,
            'following': following_count
        }
    
    @staticmethod
    def search_users(query, user_id=None, limit=20):
        """Search for users by username, email, or bio"""
        search_query = f"%{query}%"
        
        users = User.query.filter(
            or_(
                User.username.ilike(search_query),
                User.email.ilike(search_query),
                User.bio.ilike(search_query)
            )
        ).limit(limit).all()
        
        result = []
        for user in users:
            # Skip if searching for self
            if user_id and user.id == user_id:
                continue
            
            result.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'location': getattr(user, 'location', None),
                'bio': getattr(user, 'bio', None),
                'avatar_url': getattr(user, 'avatar_url', None),
                'stats': SocialDiscoveryManager._get_user_stats(user.id),
                'is_connected': UserSocialConnection.is_connected(user_id, user.id, 'follow') if user_id else False
            })
        
        return result


class NetworkAnalyticsManager:
    """Network analytics and insights"""
    
    @staticmethod
    def get_network_analytics(user_id, days=30):
        """Get comprehensive network analytics"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get connection growth
        connection_growth = NetworkAnalyticsManager._get_connection_growth(user_id, start_date, end_date)
        
        # Get engagement metrics
        engagement_metrics = NetworkAnalyticsManager._get_engagement_metrics(user_id, start_date, end_date)
        
        # Get network insights
        network_insights = NetworkAnalyticsManager._get_network_insights(user_id)
        
        return {
            'period': f'{days} days',
            'connection_growth': connection_growth,
            'engagement_metrics': engagement_metrics,
            'network_insights': network_insights,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    
    @staticmethod
    def _get_connection_growth(user_id, start_date, end_date):
        """Get connection growth over time"""
        # Get connections created in the period
        new_connections = UserSocialConnection.query.filter(
            UserSocialConnection.user_id == user_id,
            UserSocialConnection.created_at >= start_date,
            UserSocialConnection.created_at <= end_date,
            UserSocialConnection.status == 'active'
        ).all()
        
        # Group by connection type
        connections_by_type = {}
        for connection in new_connections:
            conn_type = connection.connection_type
            if conn_type not in connections_by_type:
                connections_by_type[conn_type] = 0
            connections_by_type[conn_type] += 1
        
        # Get total connections at start and end
        total_start = UserSocialConnection.query.filter(
            UserSocialConnection.user_id == user_id,
            UserSocialConnection.created_at < start_date,
            UserSocialConnection.status == 'active'
        ).count()
        
        total_end = UserSocialConnection.query.filter(
            UserSocialConnection.user_id == user_id,
            UserSocialConnection.created_at <= end_date,
            UserSocialConnection.status == 'active'
        ).count()
        
        return {
            'new_connections': len(new_connections),
            'connections_by_type': connections_by_type,
            'total_start': total_start,
            'total_end': total_end,
            'growth_rate': ((total_end - total_start) / total_start * 100) if total_start > 0 else 0
        }
    
    @staticmethod
    def _get_engagement_metrics(user_id, start_date, end_date):
        """Get engagement metrics"""
        # Get social activities
        activities = UserAnalytics.query.filter(
            UserAnalytics.user_id == user_id,
            UserAnalytics.timestamp >= start_date,
            UserAnalytics.timestamp <= end_date,
            UserAnalytics.metric_type.in_(['post_created', 'comment_created', 'like_given', 'share_created'])
        ).all()
        
        # Group by activity type
        activities_by_type = {}
        for activity in activities:
            activity_type = activity.metric_type
            if activity_type not in activities_by_type:
                activities_by_type[activity_type] = 0
            activities_by_type[activity_type] += 1
        
        # Calculate engagement rate
        total_activities = len(activities)
        followers_count = len(UserSocialConnection.get_followers(user_id))
        engagement_rate = (total_activities / followers_count * 100) if followers_count > 0 else 0
        
        return {
            'total_activities': total_activities,
            'activities_by_type': activities_by_type,
            'followers_count': followers_count,
            'engagement_rate': engagement_rate
        }
    
    @staticmethod
    def _get_network_insights(user_id):
        """Get network insights and statistics"""
        # Get network statistics
        following = UserSocialConnection.get_following(user_id)
        followers = UserSocialConnection.get_followers(user_id)
        friends = UserSocialConnection.get_friends(user_id)
        
        # Calculate network density
        network_size = len(following) + len(followers)
        mutual_connections = len(friends)
        network_density = (mutual_connections / network_size * 100) if network_size > 0 else 0
        
        # Get most active connections
        active_connections = NetworkAnalyticsManager._get_most_active_connections(user_id)
        
        return {
            'network_size': network_size,
            'following_count': len(following),
            'followers_count': len(followers),
            'friends_count': len(friends),
            'mutual_connections': mutual_connections,
            'network_density': network_density,
            'most_active_connections': active_connections
        }
    
    @staticmethod
    def _get_most_active_connections(user_id, limit=10):
        """Get most active connections"""
        # This is a simplified implementation
        # In a real system, you'd track interaction frequency
        following = UserSocialConnection.get_following(user_id)
        
        active_connections = []
        for connection in following[:limit]:
            user = User.query.get(connection.connected_user_id)
            if user:
                active_connections.append({
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'avatar_url': getattr(user, 'avatar_url', None)
                    },
                    'connection_date': connection.created_at.isoformat(),
                    'activity_score': 1.0  # Placeholder
                })
        
        return active_connections


class SocialNotificationManager:
    """Social notification management"""
    
    @staticmethod
    def create_connection_notification(user_id, from_user_id, connection_type, message=None):
        """Create connection notification"""
        from_user = User.query.get(from_user_id)
        
        notification_data = {
            'type': 'connection_request',
            'from_user': {
                'id': from_user.id,
                'username': from_user.username,
                'avatar_url': getattr(from_user, 'avatar_url', None)
            },
            'connection_type': connection_type,
            'message': message,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Store notification (would need to implement notification system)
        UserAnalytics.track_metric(
            user_id=user_id,
            metric_type='notification_received',
            value=1,
            metadata=notification_data
        )
        
        return notification_data
    
    @staticmethod
    def create_activity_notification(user_id, activity_type, activity_data):
        """Create activity notification"""
        notification_data = {
            'type': activity_type,
            'data': activity_data,
            'created_at': datetime.utcnow().isoformat()
        }
        
        UserAnalytics.track_metric(
            user_id=user_id,
            metric_type='notification_received',
            value=1,
            metadata=notification_data
        )
        
        return notification_data
    
    @staticmethod
    def get_notifications(user_id, limit=20, unread_only=False):
        """Get user notifications"""
        # This would need to be implemented with a proper notification system
        # For now, return analytics-based notifications
        
        notifications = UserAnalytics.query.filter(
            UserAnalytics.user_id == user_id,
            UserAnalytics.metric_type == 'notification_received'
        ).order_by(desc(UserAnalytics.timestamp)).limit(limit).all()
        
        result = []
        for notification in notifications:
            metadata = notification.metadata or {}
            result.append({
                'id': notification.id,
                'type': metadata.get('type', 'notification'),
                'data': metadata.get('data', {}),
                'created_at': notification.timestamp.isoformat(),
                'read': False  # Would need to implement read status tracking
            })
        
        return result
