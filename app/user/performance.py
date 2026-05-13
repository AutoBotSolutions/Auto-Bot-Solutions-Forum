"""
Performance optimization service for user management systems
"""

import json
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, g
from app import db, cache
from app.models import User
from app.user.social.models import UserFollow, UserFriend, SocialActivity


class ProfilePerformanceOptimizer:
    """Optimizes profile loading and caching performance."""
    
    @staticmethod
    def cache_key(user_id, data_type, *args):
        """Generate cache key for profile data."""
        return f"profile:{user_id}:{data_type}:{':'.join(map(str, args))}"
    
    @staticmethod
    def get_cached_profile_data(user_id, data_type='basic', timeout=300):
        """Get cached profile data."""
        cache_key = ProfilePerformanceOptimizer.cache_key(user_id, data_type)
        return cache.get(cache_key)
    
    @staticmethod
    def set_cached_profile_data(user_id, data_type, data, timeout=300):
        """Set cached profile data."""
        cache_key = ProfilePerformanceOptimizer.cache_key(user_id, data_type)
        cache.set(cache_key, data, timeout=timeout)
    
    @staticmethod
    def invalidate_profile_cache(user_id, data_type=None):
        """Invalidate profile cache."""
        if data_type:
            cache_key = ProfilePerformanceOptimizer.cache_key(user_id, data_type)
            cache.delete(cache_key)
        else:
            # Invalidate all profile cache for user
            pattern = f"profile:{user_id}:*"
            cache.delete_pattern(pattern)
    
    @staticmethod
    def get_optimized_profile(user_id, include_social=True, include_analytics=False):
        """Get optimized profile with caching."""
        cache_key = ProfilePerformanceOptimizer.cache_key(
            user_id, 'optimized', int(include_social), int(include_analytics)
        )
        
        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Build profile data
        user = User.query.get(user_id)
        if not user:
            return None
        
        start_time = time.time()
        
        # Basic profile data
        profile_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'bio': user.bio,
            'location': user.location,
            'website': user.website,
            'avatar_url': user.avatar_url,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_active': user.is_active,
            'is_verified': user.is_verified
        }
        
        # Profile customization (fast JSON parsing)
        if user.user_preferences:
            try:
                preferences = json.loads(user.user_preferences) if isinstance(user.user_preferences, str) else user.user_preferences
                profile_data['preferences'] = preferences
            except (json.JSONDecodeError, TypeError):
                profile_data['preferences'] = {}
        else:
            profile_data['preferences'] = {}
        
        # Profile theme
        profile_data['theme'] = user.get_profile_theme()
        
        # Profile layout
        profile_data['layout'] = user.get_profile_layout()
        
        # Profile widgets
        profile_data['widgets'] = user.get_profile_widgets()
        
        # Profile privacy
        profile_data['privacy'] = user.get_profile_privacy()
        
        # Social data (optimized queries)
        if include_social:
            social_data = ProfilePerformanceOptimizer.get_optimized_social_data(user_id)
            profile_data['social'] = social_data
        
        # Analytics data (cached)
        if include_analytics:
            analytics_data = ProfilePerformanceOptimizer.get_optimized_analytics_data(user_id)
            profile_data['analytics'] = analytics_data
        
        # Cache the result
        cache_time = time.time() - start_time
        profile_data['load_time'] = cache_time
        cache.set(cache_key, profile_data, timeout=300)
        
        return profile_data
    
    @staticmethod
    def get_optimized_social_data(user_id):
        """Get optimized social data with caching."""
        cache_key = ProfilePerformanceOptimizer.cache_key(user_id, 'social')
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Optimized queries using subqueries and joins
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
        
        # Get recent followers (limit 5)
        recent_followers = db.session.query(User).join(UserFollow).filter(
            UserFollow.following_id == user_id
        ).order_by(UserFollow.created_at.desc()).limit(5).all()
        
        # Get recent friends (limit 5)
        recent_friends = db.session.query(User).join(UserFriend).filter(
            db.or_(
                db.and_(UserFriend.user1_id == user_id, UserFriend.status == 'accepted'),
                db.and_(UserFriend.user2_id == user_id, UserFriend.status == 'accepted')
            )
        ).order_by(UserFriend.updated_at.desc()).limit(5).all()
        
        social_data = {
            'followers_count': followers_count,
            'following_count': following_count,
            'friends_count': friends_count,
            'recent_followers': [
                {'id': f.id, 'username': f.username, 'avatar_url': f.avatar_url}
                for f in recent_followers
            ],
            'recent_friends': [
                {'id': f.id, 'username': f.username, 'avatar_url': f.avatar_url}
                for f in recent_friends
            ]
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, social_data, timeout=300)
        
        return social_data
    
    @staticmethod
    def get_optimized_analytics_data(user_id):
        """Get optimized analytics data with caching."""
        cache_key = ProfilePerformanceOptimizer.cache_key(user_id, 'analytics')
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Get recent engagement (last 7 days)
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        
        from app.user.analytics.models import UserEngagement, UserBehavior
        
        recent_engagement = db.session.query(UserEngagement).filter(
            UserEngagement.user_id == user_id,
            UserEngagement.date >= week_ago
        ).order_by(UserEngagement.date.desc()).all()
        
        # Get behavior stats
        behavior_stats = db.session.query(
            UserBehavior.behavior_type,
            db.func.count(UserBehavior.id).label('count')
        ).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= week_ago
        ).group_by(UserBehavior.behavior_type).all()
        
        analytics_data = {
            'recent_engagement': [
                {
                    'date': eng.date.isoformat(),
                    'engagement_score': eng.engagement_score,
                    'total_actions': eng.total_actions
                }
                for eng in recent_engagement
            ],
            'behavior_stats': [
                {'type': stat.behavior_type, 'count': stat.count}
                for stat in behavior_stats
            ]
        }
        
        # Cache for 10 minutes
        cache.set(cache_key, analytics_data, timeout=600)
        
        return analytics_data
    
    @staticmethod
    def batch_profile_optimization(user_ids, include_social=True, include_analytics=False):
        """Batch optimize multiple profiles."""
        profiles = {}
        
        # Use bulk queries for better performance
        users = User.query.filter(User.id.in_(user_ids)).all()
        user_dict = {user.id: user for user in users}
        
        # Batch social data
        social_data = {}
        if include_social:
            social_data = ProfilePerformanceOptimizer.batch_get_social_data(user_ids)
        
        # Batch analytics data
        analytics_data = {}
        if include_analytics:
            analytics_data = ProfilePerformanceOptimizer.batch_get_analytics_data(user_ids)
        
        # Build profiles
        for user_id in user_ids:
            user = user_dict.get(user_id)
            if not user:
                continue
            
            profile_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'bio': user.bio,
                'location': user.location,
                'website': user.website,
                'avatar_url': user.avatar_url,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'theme': user.get_profile_theme(),
                'layout': user.get_profile_layout(),
                'widgets': user.get_profile_widgets(),
                'privacy': user.get_profile_privacy()
            }
            
            if include_social and user_id in social_data:
                profile_data['social'] = social_data[user_id]
            
            if include_analytics and user_id in analytics_data:
                profile_data['analytics'] = analytics_data[user_id]
            
            profiles[user_id] = profile_data
        
        return profiles
    
    @staticmethod
    def batch_get_social_data(user_ids):
        """Batch get social data for multiple users."""
        social_data = {}
        
        # Batch follower counts
        follower_counts = db.session.query(
            UserFollow.following_id,
            db.func.count(UserFollow.id).label('count')
        ).filter(UserFollow.following_id.in_(user_ids)).group_by(UserFollow.following_id).all()
        
        follower_dict = {count.following_id: count.count for count in follower_counts}
        
        # Batch following counts
        following_counts = db.session.query(
            UserFollow.follower_id,
            db.func.count(UserFollow.id).label('count')
        ).filter(UserFollow.follower_id.in_(user_ids)).group_by(UserFollow.follower_id).all()
        
        following_dict = {count.follower_id: count.count for count in following_counts}
        
        # Batch friend counts
        friend_counts = db.session.query(
            db.func.count(UserFriend.id).label('count')
        ).filter(
            db.or_(
                db.and_(UserFriend.user1_id.in_(user_ids), UserFriend.status == 'accepted'),
                db.and_(UserFriend.user2_id.in_(user_ids), UserFriend.status == 'accepted')
            )
        ).group_by(
            db.case(
                (UserFriend.user1_id.in_(user_ids), UserFriend.user1_id),
                else_=UserFriend.user2_id
            )
        ).all()
        
        friend_dict = {count[0]: count.count for count in friend_counts}
        
        # Build social data for each user
        for user_id in user_ids:
            social_data[user_id] = {
                'followers_count': follower_dict.get(user_id, 0),
                'following_count': following_dict.get(user_id, 0),
                'friends_count': friend_dict.get(user_id, 0)
            }
        
        return social_data
    
    @staticmethod
    def batch_get_analytics_data(user_ids):
        """Batch get analytics data for multiple users."""
        analytics_data = {}
        
        from app.user.analytics.models import UserEngagement
        
        # Batch recent engagement
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        
        recent_engagements = db.session.query(UserEngagement).filter(
            UserEngagement.user_id.in_(user_ids),
            UserEngagement.date >= week_ago
        ).order_by(UserEngagement.date.desc()).all()
        
        # Group by user
        engagement_by_user = {}
        for eng in recent_engagements:
            if eng.user_id not in engagement_by_user:
                engagement_by_user[eng.user_id] = []
            engagement_by_user[eng.user_id].append(eng)
        
        # Build analytics data for each user
        for user_id in user_ids:
            user_engagements = engagement_by_user.get(user_id, [])
            
            analytics_data[user_id] = {
                'recent_engagement': [
                    {
                        'date': eng.date.isoformat(),
                        'engagement_score': eng.engagement_score,
                        'total_actions': eng.total_actions
                    }
                    for eng in user_engagements[:7]  # Last 7 days
                ]
            }
        
        return analytics_data
    
    @staticmethod
    def preload_user_profiles(user_ids, priority='normal'):
        """Preload user profiles into cache."""
        if priority == 'high':
            timeout = 600  # 10 minutes
        elif priority == 'normal':
            timeout = 300  # 5 minutes
        else:
            timeout = 180  # 3 minutes
        
        # Batch load profiles
        profiles = ProfilePerformanceOptimizer.batch_profile_optimization(
            user_ids, include_social=True, include_analytics=False
        )
        
        # Cache each profile
        for user_id, profile_data in profiles.items():
            cache_key = ProfilePerformanceOptimizer.cache_key(user_id, 'optimized', 1, 0)
            cache.set(cache_key, profile_data, timeout=timeout)
    
    @staticmethod
    def warm_profile_cache(user_id):
        """Warm up profile cache for a user."""
        # Load all profile variations
        variations = [
            (False, False),  # Basic only
            (True, False),    # With social
            (False, True),    # With analytics
            (True, True)      # With both
        ]
        
        for include_social, include_analytics in variations:
            ProfilePerformanceOptimizer.get_optimized_profile(
                user_id, include_social=include_social, include_analytics=include_analytics
            )


def profile_cache_timeout(timeout=300):
    """Decorator to set cache timeout for profile data."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Store original timeout
            original_timeout = getattr(g, 'profile_cache_timeout', 300)
            g.profile_cache_timeout = timeout
            
            try:
                result = f(*args, **kwargs)
                return result
            finally:
                # Restore original timeout
                g.profile_cache_timeout = original_timeout
        
        return decorated_function
    return decorator


def invalidate_profile_on_change(f):
    """Decorator to invalidate profile cache when data changes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user_id from arguments
        user_id = None
        if args and hasattr(args[0], 'id'):
            user_id = args[0].id
        elif 'user_id' in kwargs:
            user_id = kwargs['user_id']
        elif 'id' in kwargs:
            user_id = kwargs['id']
        
        # Execute the function
        result = f(*args, **kwargs)
        
        # Invalidate cache if user_id was found
        if user_id:
            ProfilePerformanceOptimizer.invalidate_profile_cache(user_id)
        
        return result
    
    return decorated_function


class ProfileLazyLoader:
    """Lazy loading for profile components."""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self._user = None
        self._social_data = None
        self._analytics_data = None
        self._theme = None
        self._layout = None
        self._widgets = None
        self._privacy = None
    
    @property
    def user(self):
        """Lazy load user data."""
        if self._user is None:
            self._user = User.query.get(self.user_id)
        return self._user
    
    @property
    def social_data(self):
        """Lazy load social data."""
        if self._social_data is None:
            self._social_data = ProfilePerformanceOptimizer.get_optimized_social_data(self.user_id)
        return self._social_data
    
    @property
    def analytics_data(self):
        """Lazy load analytics data."""
        if self._analytics_data is None:
            self._analytics_data = ProfilePerformanceOptimizer.get_optimized_analytics_data(self.user_id)
        return self._analytics_data
    
    @property
    def theme(self):
        """Lazy load theme data."""
        if self._theme is None:
            self._theme = self.user.get_profile_theme() if self.user else {}
        return self._theme
    
    @property
    def layout(self):
        """Lazy load layout data."""
        if self._layout is None:
            self._layout = self.user.get_profile_layout() if self.user else {}
        return self._layout
    
    @property
    def widgets(self):
        """Lazy load widgets data."""
        if self._widgets is None:
            self._widgets = self.user.get_profile_widgets() if self.user else {}
        return self._widgets
    
    @property
    def privacy(self):
        """Lazy load privacy data."""
        if self._privacy is None:
            self._privacy = self.user.get_profile_privacy() if self.user else {}
        return self._privacy
    
    def get_profile_data(self, components=None):
        """Get specific profile components."""
        if components is None:
            components = ['user', 'theme', 'layout', 'widgets', 'privacy']
        
        data = {}
        
        if 'user' in components:
            data['user'] = self.user
        
        if 'social' in components:
            data['social'] = self.social_data
        
        if 'analytics' in components:
            data['analytics'] = self.analytics_data
        
        if 'theme' in components:
            data['theme'] = self.theme
        
        if 'layout' in components:
            data['layout'] = self.layout
        
        if 'widgets' in components:
            data['widgets'] = self.widgets
        
        if 'privacy' in components:
            data['privacy'] = self.privacy
        
        return data


# Performance monitoring
class ProfilePerformanceMonitor:
    """Monitor profile loading performance."""
    
    @staticmethod
    def track_profile_load(user_id, load_time, components_loaded):
        """Track profile loading performance."""
        cache_key = f"profile_performance:{user_id}:{datetime.utcnow().strftime('%Y%m%d')}"
        
        # Get existing performance data
        performance_data = cache.get(cache_key) or {
            'loads': [],
            'avg_load_time': 0,
            'max_load_time': 0,
            'min_load_time': float('inf'),
            'total_loads': 0
        }
        
        # Update performance data
        performance_data['loads'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'load_time': load_time,
            'components': components_loaded
        })
        
        performance_data['total_loads'] += 1
        performance_data['avg_load_time'] = (
            (performance_data['avg_load_time'] * (performance_data['total_loads'] - 1) + load_time) /
            performance_data['total_loads']
        )
        performance_data['max_load_time'] = max(performance_data['max_load_time'], load_time)
        performance_data['min_load_time'] = min(performance_data['min_load_time'], load_time)
        
        # Keep only last 100 loads
        if len(performance_data['loads']) > 100:
            performance_data['loads'] = performance_data['loads'][-100:]
        
        # Cache for 24 hours
        cache.set(cache_key, performance_data, timeout=86400)
    
    @staticmethod
    def get_performance_stats(user_id, days=7):
        """Get performance statistics for a user."""
        stats = []
        
        for day_offset in range(days):
            date = datetime.utcnow().date() - timedelta(days=day_offset)
            cache_key = f"profile_performance:{user_id}:{date.strftime('%Y%m%d')}"
            day_stats = cache.get(cache_key)
            
            if day_stats:
                stats.append({
                    'date': date.isoformat(),
                    'avg_load_time': day_stats['avg_load_time'],
                    'total_loads': day_stats['total_loads'],
                    'max_load_time': day_stats['max_load_time'],
                    'min_load_time': day_stats['min_load_time']
                })
        
        return sorted(stats, key=lambda x: x['date'])
    
    @staticmethod
    def get_system_performance_stats():
        """Get system-wide performance statistics."""
        # This would typically query a performance monitoring table
        # For now, return mock data
        return {
            'avg_profile_load_time': 0.15,
            'cache_hit_rate': 0.85,
            'total_profiles_loaded': 10000,
            'slow_queries_count': 25
        }
