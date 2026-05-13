"""
Performance optimizations for Social Features System
"""

import json
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, g
from app import db, cache
from app.user.social.models import UserFollow, UserFriend, SocialActivity, UserGroup, GroupMember, UserRecommendation


class SocialPerformanceOptimizer:
    """Optimizes social features performance through caching and query optimization."""
    
    @staticmethod
    def cache_key(user_id, data_type, *args):
        """Generate cache key for social data."""
        return f"social:{user_id}:{data_type}:{':'.join(map(str, args))}"
    
    @staticmethod
    def get_cached_social_data(user_id, data_type, timeout=300):
        """Get cached social data."""
        cache_key = SocialPerformanceOptimizer.cache_key(user_id, data_type)
        return cache.get(cache_key)
    
    @staticmethod
    def set_cached_social_data(user_id, data_type, data, timeout=300):
        """Set cached social data."""
        cache_key = SocialPerformanceOptimizer.cache_key(user_id, data_type)
        cache.set(cache_key, data, timeout=timeout)
    
    @staticmethod
    def invalidate_social_cache(user_id, data_type=None):
        """Invalidate social cache."""
        if data_type:
            cache_key = SocialPerformanceOptimizer.cache_key(user_id, data_type)
            cache.delete(cache_key)
        else:
            # Invalidate all social cache for user
            pattern = f"social:{user_id}:*"
            cache.delete_pattern(pattern)
    
    @staticmethod
    def get_optimized_social_profile(user_id):
        """Get optimized social profile with caching."""
        cache_key = SocialPerformanceOptimizer.cache_key(user_id, 'profile')
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Batch all social queries
        # Followers count
        followers_count = db.session.query(UserFollow).filter(
            UserFollow.following_id == user_id
        ).count()
        
        # Following count
        following_count = db.session.query(UserFollow).filter(
            UserFollow.follower_id == user_id
        ).count()
        
        # Friends count
        friends_count = db.session.query(UserFriend).filter(
            db.or_(
                db.and_(UserFriend.user1_id == user_id, UserFriend.status == 'accepted'),
                db.and_(UserFriend.user2_id == user_id, UserFriend.status == 'accepted')
            )
        ).count()
        
        # Pending friend requests
        pending_requests_count = db.session.query(UserFriend).filter(
            UserFriend.user2_id == user_id,
            UserFriend.status == 'pending'
        ).count()
        
        # Groups count
        groups_count = db.session.query(UserGroup).filter(
            UserGroup.creator_id == user_id
        ).count()
        
        # Member groups count
        member_groups_count = db.session.query(GroupMember).filter(
            GroupMember.user_id == user_id
        ).count()
        
        # Recent followers (limit 5)
        recent_followers = db.session.query(
            User.id, User.username, User.avatar_url, UserFollow.created_at
        ).join(UserFollow).filter(
            UserFollow.following_id == user_id
        ).order_by(UserFollow.created_at.desc()).limit(5).all()
        
        # Recent friends (limit 5)
        recent_friends = db.session.query(
            User.id, User.username, User.avatar_url, UserFriend.updated_at
        ).join(UserFriend).filter(
            db.or_(
                db.and_(UserFriend.user1_id == user_id, UserFriend.status == 'accepted'),
                db.and_(UserFriend.user2_id == user_id, UserFriend.status == 'accepted')
            )
        ).order_by(UserFriend.updated_at.desc()).limit(5).all()
        
        # Recent activities (limit 10)
        recent_activities = db.session.query(
            SocialActivity.activity_type,
            SocialActivity.action,
            SocialActivity.description,
            SocialActivity.target_type,
            SocialActivity.target_id,
            SocialActivity.created_at
        ).filter(
            SocialActivity.user_id == user_id,
            SocialActivity.is_public == True
        ).order_by(SocialActivity.created_at.desc()).limit(10).all()
        
        # Build profile data
        profile_data = {
            'followers_count': followers_count,
            'following_count': following_count,
            'friends_count': friends_count,
            'pending_requests_count': pending_requests_count,
            'groups_count': groups_count,
            'member_groups_count': member_groups_count,
            'recent_followers': [
                {
                    'id': f.id,
                    'username': f.username,
                    'avatar_url': f.avatar_url,
                    'followed_at': f.created_at.isoformat()
                }
                for f in recent_followers
            ],
            'recent_friends': [
                {
                    'id': f.id,
                    'username': f.username,
                    'avatar_url': f.avatar_url,
                    'friend_since': f.updated_at.isoformat()
                }
                for f in recent_friends
            ],
            'recent_activities': [
                {
                    'activity_type': a.activity_type,
                    'action': a.action,
                    'description': a.description,
                    'target_type': a.target_type,
                    'target_id': a.target_id,
                    'created_at': a.created_at.isoformat()
                }
                for a in recent_activities
            ]
        }
        
        load_time = time.time() - start_time
        profile_data['load_time'] = load_time
        
        # Cache for 5 minutes
        cache.set(cache_key, profile_data, timeout=300)
        
        return profile_data
    
    @staticmethod
    def get_optimized_followers(user_id, limit=20, offset=0):
        """Get optimized followers list with caching."""
        cache_key = SocialPerformanceOptimizer.cache_key(user_id, 'followers', limit, offset)
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Optimized query with pagination
        followers = db.session.query(
            User.id, User.username, User.avatar_url, User.bio,
            UserFollow.created_at, UserFollow.is_mutual, UserFollow.is_close_friend
        ).join(UserFollow).filter(
            UserFollow.following_id == user_id
        ).order_by(UserFollow.created_at.desc()).offset(offset).limit(limit).all()
        
        followers_data = []
        for follower in followers:
            followers_data.append({
                'id': follower.id,
                'username': follower.username,
                'avatar_url': follower.avatar_url,
                'bio': follower.bio,
                'followed_at': follower.created_at.isoformat(),
                'is_mutual': follower.is_mutual,
                'is_close_friend': follower.is_close_friend
            })
        
        load_time = time.time() - start_time
        result = {
            'followers': followers_data,
            'load_time': load_time,
            'has_more': len(followers_data) == limit
        }
        
        # Cache for 3 minutes
        cache.set(cache_key, result, timeout=180)
        
        return result
    
    @staticmethod
    def get_optimized_friends(user_id, limit=20, offset=0):
        """Get optimized friends list with caching."""
        cache_key = SocialPerformanceOptimizer.cache_key(user_id, 'friends', limit, offset)
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Optimized query for friends
        friends_query = db.session.query(
            User.id, User.username, User.avatar_url, User.bio,
            UserFriend.created_at, UserFriend.responded_at, UserFriend.is_close_friend, UserFriend.friend_group
        ).join(UserFriend).filter(
            db.or_(
                db.and_(UserFriend.user1_id == user_id, UserFriend.status == 'accepted'),
                db.and_(UserFriend.user2_id == user_id, UserFriend.status == 'accepted')
            )
        ).order_by(UserFriend.updated_at.desc()).offset(offset).limit(limit)
        
        friends = []
        for friend in friends_query:
            friends.append({
                'id': friend.id,
                'username': friend.username,
                'avatar_url': friend.avatar_url,
                'bio': friend.bio,
                'friend_since': friend.responded_at.isoformat() if friend.responded_at else friend.created_at.isoformat(),
                'is_close_friend': friend.is_close_friend,
                'friend_group': friend.friend_group
            })
        
        load_time = time.time() - start_time
        result = {
            'friends': friends,
            'load_time': load_time,
            'has_more': len(friends) == limit
        }
        
        # Cache for 3 minutes
        cache.set(cache_key, result, timeout=180)
        
        return result
    
    @staticmethod
    def get_optimized_activity_feed(user_id, limit=50, include_friends=True):
        """Get optimized activity feed with caching."""
        cache_key = SocialPerformanceOptimizer.cache_key(user_id, 'feed', limit, int(include_friends))
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Build base query
        query = SocialActivity.query.filter(SocialActivity.is_public == True)
        
        if include_friends:
            # Get friend IDs
            friend_ids = db.session.query(
                db.case(
                    (UserFriend.user1_id == user_id, UserFriend.user2_id),
                    else_=UserFriend.user1_id
                )
            ).filter(
                db.or_(
                    db.and_(UserFriend.user1_id == user_id, UserFriend.status == 'accepted'),
                    db.and_(UserFriend.user2_id == user_id, UserFriend.status == 'accepted')
                )
            ).all()
            
            friend_ids = [fid[0] for fid in friend_ids]
            friend_ids.append(user_id)  # Include own activities
            
            query = query.filter(SocialActivity.user_id.in_(friend_ids))
        else:
            query = query.filter(SocialActivity.user_id == user_id)
        
        # Execute query with ordering and limit
        activities = query.order_by(SocialActivity.created_at.desc()).limit(limit).all()
        
        activities_data = []
        for activity in activities:
            activity_data = {
                'id': activity.id,
                'user_id': activity.user_id,
                'activity_type': activity.activity_type,
                'action': activity.action,
                'description': activity.description,
                'target_type': activity.target_type,
                'target_id': activity.target_id,
                'created_at': activity.created_at.isoformat()
            }
            
            # Only include metadata if it exists
            if activity.metadata:
                activity_data['metadata'] = activity.metadata
            
            activities_data.append(activity_data)
        
        load_time = time.time() - start_time
        result = {
            'activities': activities_data,
            'load_time': load_time,
            'include_friends': include_friends
        }
        
        # Cache for 2 minutes (activity feeds change frequently)
        cache.set(cache_key, result, timeout=120)
        
        return result
    
    @staticmethod
    def get_optimized_user_groups(user_id, include_members=False):
        """Get optimized user groups with caching."""
        cache_key = SocialPerformanceOptimizer.cache_key(user_id, 'groups', int(include_members))
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Get groups created by user
        created_groups = db.session.query(UserGroup).filter(
            UserGroup.creator_id == user_id
        ).order_by(UserGroup.created_at.desc()).all()
        
        # Get groups user is member of
        member_groups = db.session.query(UserGroup).join(GroupMember).filter(
            GroupMember.user_id == user_id,
            UserGroup.creator_id != user_id  # Exclude created groups
        ).order_by(GroupMember.joined_at.desc()).all()
        
        groups_data = []
        
        # Process created groups
        for group in created_groups:
            group_data = {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'creator_id': group.creator_id,
                'is_private': group.is_private,
                'group_type': group.group_type,
                'color': group.color,
                'icon': group.icon,
                'created_at': group.created_at.isoformat(),
                'member_count': group.get_member_count(),
                'is_creator': True,
                'is_admin': True
            }
            
            if include_members:
                members = db.session.query(
                    User.id, User.username, User.avatar_url, GroupMember.is_admin, GroupMember.joined_at
                ).join(GroupMember).filter(
                    GroupMember.group_id == group.id
                ).order_by(GroupMember.joined_at.asc()).limit(10).all()
                
                group_data['members'] = [
                    {
                        'id': m.id,
                        'username': m.username,
                        'avatar_url': m.avatar_url,
                        'is_admin': m.is_admin,
                        'joined_at': m.joined_at.isoformat()
                    }
                    for m in members
                ]
            
            groups_data.append(group_data)
        
        # Process member groups
        for group in member_groups:
            group_data = {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'creator_id': group.creator_id,
                'is_private': group.is_private,
                'group_type': group.group_type,
                'color': group.color,
                'icon': group.icon,
                'created_at': group.created_at.isoformat(),
                'member_count': group.get_member_count(),
                'is_creator': False,
                'is_admin': GroupMember.is_admin(group.id, user_id)
            }
            
            if include_members:
                members = db.session.query(
                    User.id, User.username, User.avatar_url, GroupMember.is_admin, GroupMember.joined_at
                ).join(GroupMember).filter(
                    GroupMember.group_id == group.id
                ).order_by(GroupMember.joined_at.asc()).limit(10).all()
                
                group_data['members'] = [
                    {
                        'id': m.id,
                        'username': m.username,
                        'avatar_url': m.avatar_url,
                        'is_admin': m.is_admin,
                        'joined_at': m.joined_at.isoformat()
                    }
                    for m in members
                ]
            
            groups_data.append(group_data)
        
        load_time = time.time() - start_time
        result = {
            'groups': groups_data,
            'load_time': load_time,
            'total_groups': len(groups_data)
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, result, timeout=300)
        
        return result
    
    @staticmethod
    def get_optimized_recommendations(user_id, recommendation_type=None, limit=20):
        """Get optimized user recommendations with caching."""
        cache_key = SocialPerformanceOptimizer.cache_key(user_id, 'recommendations', recommendation_type or 'all', limit)
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Build query
        query = UserRecommendation.query.filter(
            UserRecommendation.user_id == user_id,
            UserRecommendation.is_dismissed == False,
            UserRecommendation.expires_at > datetime.utcnow()
        )
        
        if recommendation_type:
            query = query.filter(UserRecommendation.recommendation_type == recommendation_type)
        
        recommendations = query.order_by(UserRecommendation.score.desc()).limit(limit).all()
        
        recommendations_data = []
        for rec in recommendations:
            # Get recommended user info
            from app.models import User
            recommended_user = User.query.get(rec.recommended_user_id)
            
            if recommended_user:
                recommendations_data.append({
                    'id': rec.id,
                    'recommended_user': {
                        'id': recommended_user.id,
                        'username': recommended_user.username,
                        'avatar_url': recommended_user.avatar_url,
                        'bio': recommended_user.bio
                    },
                    'recommendation_type': rec.recommendation_type,
                    'score': rec.score,
                    'reason': rec.reason,
                    'created_at': rec.created_at.isoformat(),
                    'expires_at': rec.expires_at.isoformat()
                })
        
        load_time = time.time() - start_time
        result = {
            'recommendations': recommendations_data,
            'load_time': load_time,
            'recommendation_type': recommendation_type
        }
        
        # Cache for 10 minutes
        cache.set(cache_key, result, timeout=600)
        
        return result
    
    @staticmethod
    def batch_social_profiles(user_ids):
        """Batch get social profiles for multiple users."""
        profiles = {}
        
        # Batch query for all counts
        user_ids_tuple = tuple(user_ids)
        
        # Batch followers counts
        followers_counts = db.session.query(
            UserFollow.following_id,
            db.func.count(UserFollow.id).label('count')
        ).filter(UserFollow.following_id.in_(user_ids_tuple)).group_by(UserFollow.following_id).all()
        
        followers_dict = {count.following_id: count.count for count in followers_counts}
        
        # Batch following counts
        following_counts = db.session.query(
            UserFollow.follower_id,
            db.func.count(UserFollow.id).label('count')
        ).filter(UserFollow.follower_id.in_(user_ids_tuple)).group_by(UserFollow.follower_id).all()
        
        following_dict = {count.follower_id: count.count for count in following_counts}
        
        # Batch friends counts
        friend_counts = db.session.query(
            db.func.count(UserFriend.id).label('count')
        ).filter(
            db.or_(
                db.and_(UserFriend.user1_id.in_(user_ids_tuple), UserFriend.status == 'accepted'),
                db.and_(UserFriend.user2_id.in_(user_ids_tuple), UserFriend.status == 'accepted')
            )
        ).group_by(
            db.case(
                (UserFriend.user1_id.in_(user_ids_tuple), UserFriend.user1_id),
                else_=UserFriend.user2_id
            )
        ).all()
        
        friend_dict = {count[0]: count.count for count in friend_counts}
        
        # Build profiles
        for user_id in user_ids:
            profiles[user_id] = {
                'followers_count': followers_dict.get(user_id, 0),
                'following_count': following_dict.get(user_id, 0),
                'friends_count': friend_dict.get(user_id, 0)
            }
        
        return profiles


def social_cache_timeout(timeout=300):
    """Decorator to set cache timeout for social data."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Store original timeout
            original_timeout = getattr(g, 'social_cache_timeout', 300)
            g.social_cache_timeout = timeout
            
            try:
                result = f(*args, **kwargs)
                return result
            finally:
                # Restore original timeout
                g.social_cache_timeout = original_timeout
        
        return decorated_function
    return decorator


def invalidate_social_on_change(f):
    """Decorator to invalidate social cache when data changes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user_id from arguments
        user_id = None
        if args and hasattr(args[0], 'user_id'):
            user_id = args[0].user_id
        elif 'user_id' in kwargs:
            user_id = kwargs['user_id']
        elif args and hasattr(args[0], 'id'):
            user_id = args[0].id
        
        # Execute the function
        result = f(*args, **kwargs)
        
        # Invalidate cache if user_id was found
        if user_id:
            SocialPerformanceOptimizer.invalidate_social_cache(user_id)
        
        return result
    
    return decorated_function


class SocialGraphOptimizer:
    """Optimizes social graph queries and operations."""
    
    @staticmethod
    def get_mutual_followers(user_id1, user_id2, limit=20):
        """Get mutual followers between two users."""
        cache_key = f"social_graph:mutual_followers:{min(user_id1, user_id2)}:{max(user_id1, user_id2)}:{limit}"
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Get followers of user1
        user1_followers = db.session.query(UserFollow.follower_id).filter(
            UserFollow.following_id == user_id1
        ).subquery()
        
        # Get followers of user2
        user2_followers = db.session.query(UserFollow.follower_id).filter(
            UserFollow.following_id == user_id2
        ).subquery()
        
        # Find intersection
        mutual_followers = db.session.query(
            User.id, User.username, User.avatar_url
        ).filter(
            User.id.in_(user1_followers),
            User.id.in_(user2_followers)
        ).limit(limit).all()
        
        result = {
            'mutual_followers': [
                {
                    'id': f.id,
                    'username': f.username,
                    'avatar_url': f.avatar_url
                }
                for f in mutual_followers
            ],
            'load_time': time.time() - start_time
        }
        
        # Cache for 10 minutes
        cache.set(cache_key, result, timeout=600)
        
        return result
    
    @staticmethod
    def get_friends_of_friends(user_id, limit=50):
        """Get friends of friends (second-degree connections)."""
        cache_key = f"social_graph:fof:{user_id}:{limit}"
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Get user's friends
        friends_query = db.session.query(
            db.case(
                (UserFriend.user1_id == user_id, UserFriend.user2_id),
                else_=UserFriend.user1_id
            )
        ).filter(
            db.or_(
                db.and_(UserFriend.user1_id == user_id, UserFriend.status == 'accepted'),
                db.and_(UserFriend.user2_id == user_id, UserFriend.status == 'accepted')
            )
        ).subquery()
        
        # Get friends of friends
        friends_of_friends_query = db.session.query(
            db.case(
                (UserFriend.user1_id.in_(friends_query), UserFriend.user2_id),
                else_=UserFriend.user1_id
            ).label('friend_id')
        ).filter(
            db.or_(
                db.and_(UserFriend.user1_id.in_(friends_query), UserFriend.status == 'accepted'),
                db.and_(UserFriend.user2_id.in_(friends_query), UserFriend.status == 'accepted')
            ),
            db.not_(
                db.or_(
                    db.case(
                        (UserFriend.user1_id.in_(friends_query), UserFriend.user2_id),
                        else_=UserFriend.user1_id
                    ) == user_id,
                    db.case(
                        (UserFriend.user1_id.in_(friends_query), UserFriend.user2_id),
                        else_=UserFriend.user1_id
                    ).in_(friends_query)
                )
            )
        ).distinct().limit(limit).subquery()
        
        # Get user details
        friends_of_friends = db.session.query(
            User.id, User.username, User.avatar_url, User.bio
        ).filter(
            User.id.in_(friends_of_friends_query)
        ).all()
        
        result = {
            'friends_of_friends': [
                {
                    'id': f.id,
                    'username': f.username,
                    'avatar_url': f.avatar_url,
                    'bio': f.bio
                }
                for f in friends_of_friends
            ],
            'load_time': time.time() - start_time
        }
        
        # Cache for 15 minutes
        cache.set(cache_key, result, timeout=900)
        
        return result
    
    @staticmethod
    def get_social_graph_stats(user_id):
        """Get social graph statistics for a user."""
        cache_key = f"social_graph:stats:{user_id}"
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Direct connections
        followers_count = db.session.query(UserFollow).filter(
            UserFollow.following_id == user_id
        ).count()
        
        following_count = db.session.query(UserFollow).filter(
            UserFollow.follower_id == user_id
        ).count()
        
        friends_count = db.session.query(UserFriend).filter(
            db.or_(
                db.and_(UserFriend.user1_id == user_id, UserFriend.status == 'accepted'),
                db.and_(UserFriend.user2_id == user_id, UserFriend.status == 'accepted')
            )
        ).count()
        
        # Second-degree connections (friends of friends)
        friends_query = db.session.query(
            db.case(
                (UserFriend.user1_id == user_id, UserFriend.user2_id),
                else_=UserFriend.user1_id
            )
        ).filter(
            db.or_(
                db.and_(UserFriend.user1_id == user_id, UserFriend.status == 'accepted'),
                db.and_(UserFriend.user2_id == user_id, UserFriend.status == 'accepted')
            )
        ).subquery()
        
        fof_count = db.session.query(
            db.func.count(db.func.distinct(
                db.case(
                    (UserFriend.user1_id.in_(friends_query), UserFriend.user2_id),
                    else_=UserFriend.user1_id
                )
            ))
        ).filter(
            db.or_(
                db.and_(UserFriend.user1_id.in_(friends_query), UserFriend.status == 'accepted'),
                db.and_(UserFriend.user2_id.in_(friends_query), UserFriend.status == 'accepted')
            ),
            db.not_(
                db.or_(
                    db.case(
                        (UserFriend.user1_id.in_(friends_query), UserFriend.user2_id),
                        else_=UserFriend.user1_id
                    ) == user_id,
                    db.case(
                        (UserFriend.user1_id.in_(friends_query), UserFriend.user2_id),
                        else_=UserFriend.user1_id
                    ).in_(friends_query)
                )
            )
        ).scalar()
        
        result = {
            'followers_count': followers_count,
            'following_count': following_count,
            'friends_count': friends_count,
            'friends_of_friends_count': fof_count or 0,
            'network_density': (friends_count / max(followers_count + following_count, 1)) * 100,
            'load_time': time.time() - start_time
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, result, timeout=300)
        
        return result
    
    @staticmethod
    def get_connection_path(user_id1, user_id2, max_depth=3):
        """Find shortest connection path between two users."""
        cache_key = f"social_graph:path:{min(user_id1, user_id2)}:{max(user_id1, user_id2)}:{max_depth}"
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # This is a simplified BFS implementation
        # In production, you'd want a more sophisticated graph algorithm
        
        # Check if they're directly connected
        if UserFriend.are_friends(user_id1, user_id2):
            result = {
                'path': [user_id1, user_id2],
                'depth': 1,
                'found': True,
                'load_time': time.time() - start_time
            }
            cache.set(cache_key, result, timeout=600)
            return result
        
        # Check for mutual friends (depth 2)
        mutual_friends = SocialGraphOptimizer.get_mutual_followers(user_id1, user_id2, limit=1)
        if mutual_friends['mutual_followers']:
            result = {
                'path': [user_id1, mutual_friends['mutual_followers'][0]['id'], user_id2],
                'depth': 2,
                'found': True,
                'load_time': time.time() - start_time
            }
            cache.set(cache_key, result, timeout=600)
            return result
        
        # For depth 3+, you'd implement a full BFS algorithm
        # For now, return not found
        result = {
            'path': [],
            'depth': max_depth,
            'found': False,
            'load_time': time.time() - start_time
        }
        
        cache.set(cache_key, result, timeout=600)
        return result


class SocialPerformanceMonitor:
    """Monitor social features performance."""
    
    @staticmethod
    def track_social_operation(user_id, operation_type, execution_time, result_count):
        """Track social operation performance."""
        cache_key = f"social_performance:{datetime.utcnow().strftime('%Y%m%d')}"
        
        # Get existing performance data
        performance_data = cache.get(cache_key) or {
            'operations': [],
            'avg_execution_time': 0,
            'max_execution_time': 0,
            'min_execution_time': float('inf'),
            'total_operations': 0
        }
        
        # Update performance data
        performance_data['operations'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'operation_type': operation_type,
            'execution_time': execution_time,
            'result_count': result_count
        })
        
        performance_data['total_operations'] += 1
        performance_data['avg_execution_time'] = (
            (performance_data['avg_execution_time'] * (performance_data['total_operations'] - 1) + execution_time) /
            performance_data['total_operations']
        )
        performance_data['max_execution_time'] = max(performance_data['max_execution_time'], execution_time)
        performance_data['min_execution_time'] = min(performance_data['min_execution_time'], execution_time)
        
        # Keep only last 1000 operations
        if len(performance_data['operations']) > 1000:
            performance_data['operations'] = performance_data['operations'][-1000:]
        
        # Cache for 24 hours
        cache.set(cache_key, performance_data, timeout=86400)
    
    @staticmethod
    def get_performance_stats(days=7):
        """Get performance statistics."""
        stats = []
        
        for day_offset in range(days):
            date = datetime.utcnow().date() - timedelta(days=day_offset)
            cache_key = f"social_performance:{date.strftime('%Y%m%d')}"
            day_stats = cache.get(cache_key)
            
            if day_stats:
                stats.append({
                    'date': date.isoformat(),
                    'avg_execution_time': day_stats['avg_execution_time'],
                    'total_operations': day_stats['total_operations'],
                    'max_execution_time': day_stats['max_execution_time'],
                    'min_execution_time': day_stats['min_execution_time']
                })
        
        return sorted(stats, key=lambda x: x['date'])
    
    @staticmethod
    def get_slow_operations(threshold=0.5, limit=50):
        """Get slow operations above threshold."""
        # This would typically query a performance monitoring table
        # For now, return mock data
        return [
            {
                'operation_type': 'activity_feed',
                'execution_time': 0.8,
                'user_id': 123,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
