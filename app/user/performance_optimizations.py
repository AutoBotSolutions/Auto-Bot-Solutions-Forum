"""
Performance Optimization Systems for User Management

This module provides comprehensive performance optimizations for:
- Profile loading performance
- Analytics performance
- Social performance
"""

from datetime import datetime, timedelta
from functools import wraps
from flask import current_app
from app import db
from app.cache.redis_cache import RedisCacheService
from app.models import User
from sqlalchemy import func, and_, or_, text
from sqlalchemy.orm import joinedload, selectinload, lazyload
import json
import time
import logging

logger = logging.getLogger(__name__)

# Initialize cache service
_cache_service = None

def get_cache_service():
    """Get cache service instance"""
    global _cache_service
    if _cache_service is None:
        try:
            _cache_service = RedisCacheService()
        except RuntimeError:
            # Working outside application context, create service with default config
            # Create a custom RedisCacheService that doesn't depend on Flask context
            _cache_service = RedisCacheService(redis_url='redis://localhost:6379/3')
            # Manually set the default TTL since we can't get it from Flask config
            _cache_service.default_ttl = 3600  # 1 hour default
    return _cache_service

# Simple cache interface for performance optimizations
class SimpleCache:
    """Simple cache interface for performance optimizations"""
    
    def __init__(self):
        self.cache_service = get_cache_service()
    
    def get(self, key):
        """Get value from cache"""
        try:
            if self.cache_service.is_available():
                return self.cache_service.get(key)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def set(self, key, value, timeout=None):
        """Set value in cache"""
        try:
            if self.cache_service.is_available():
                ttl = timeout or 300  # Default 5 minutes
                return self.cache_service.set(key, value, ttl)
            return False
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    def delete(self, key):
        """Delete value from cache"""
        try:
            if self.cache_service.is_available():
                return self.cache_service.delete(key)
            return False
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    def delete_many(self, patterns):
        """Delete multiple keys by pattern"""
        try:
            if self.cache_service.is_available():
                deleted_count = 0
                for pattern in patterns:
                    if '*' in pattern:
                        deleted_count += self.cache_service.delete_pattern(pattern)
                    else:
                        if self.cache_service.delete(pattern):
                            deleted_count += 1
                return deleted_count
            return 0
        except Exception as e:
            logger.warning(f"Cache delete_many error: {e}")
            return 0
    
    def get_many(self, keys):
        """Get multiple values from cache"""
        results = {}
        try:
            if self.cache_service.is_available():
                for key in keys:
                    value = self.cache_service.get(key)
                    if value is not None:
                        results[key] = value
            return results
        except Exception as e:
            logger.warning(f"Cache get_many error: {e}")
            return results

# Create cache instance
cache = SimpleCache()


class ProfilePerformanceOptimizer:
    """Optimizes profile loading performance with caching and lazy loading strategies."""
    
    @staticmethod
    def get_optimized_profile(user_id, include_social=True, include_analytics=False):
        """Get optimized profile with intelligent caching and lazy loading."""
        cache_key = f"profile:{user_id}:optimized:{include_social}:{include_analytics}"
        
        # Try to get from cache first
        cached_profile = cache.get(cache_key)
        if cached_profile:
            return cached_profile
        
        # Build optimized query with strategic eager loading
        query = User.query
        
        # Always eager load essential profile data
        query = query.options(
            selectinload(User.badges),
            selectinload(User.roles)
        )
        
        # Conditionally load social data with lazy loading
        if include_social:
            query = query.options(
                lazyload(User.following),
                lazyload(User.followers),
                lazyload(User.friends)
            )
        
        # Conditionally load analytics data with lazy loading
        if include_analytics:
            query = query.options(
                lazyload(User.behaviors),
                lazyload(User.engagements)
            )
        
        user = query.filter_by(id=user_id).first()
        
        if not user:
            return None
        
        # Build optimized profile data
        profile_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'bio': user.bio,
            'location': user.location,
            'website': user.website,
            'avatar_url': user.avatar_url,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'last_login': user.last_login,
            'last_activity': user.last_activity,
            'login_count': user.login_count,
            'created_at': user.created_at,
            
            # Profile preferences (always included)
            'profile_preferences': user.get_profile_preferences(),
            'general_preferences': user.get_general_preferences(),
            'notification_preferences': user.get_notification_preferences(),
            'privacy_preferences': user.get_privacy_preferences(),
            'accessibility_preferences': user.get_accessibility_preferences(),
            'display_preferences': user.get_display_preferences(),
            'social_preferences': user.get_social_preferences(),
            
            # Badges and roles (eager loaded)
            'badges': [{'id': badge.id, 'name': badge.name, 'description': badge.description} 
                     for badge in user.badges],
            'roles': [{'id': role.id, 'name': role.name, 'display_name': role.display_name} 
                    for role in user.roles],
            
            # Social data (lazy loaded - will be loaded on demand)
            'social_data': ProfilePerformanceOptimizer._get_social_summary(user) if include_social else None,
            
            # Analytics data (lazy loaded - will be loaded on demand)
            'analytics_data': ProfilePerformanceOptimizer._get_analytics_summary(user) if include_analytics else None,
            
            # Performance metadata
            'cached_at': datetime.utcnow().isoformat(),
            'cache_key': cache_key
        }
        
        # Cache the optimized profile for 5 minutes
        cache.set(cache_key, profile_data, timeout=300)
        
        return profile_data
    
    @staticmethod
    def _get_social_summary(user):
        """Get social data summary with optimized queries."""
        try:
            # Check if social models are available
            if UserFollow is None or UserFriend is None or SocialActivity is None:
                logger.warning("Social models not available, returning None")
                return None
            
            # Use optimized count queries instead of loading all relationships
            following_count = db.session.query(func.count(UserFollow.id)).filter_by(follower_id=user.id).scalar()
            followers_count = db.session.query(func.count(UserFollow.id)).filter_by(following_id=user.id).scalar()
            friends_count = db.session.query(func.count(UserFriend.id)).filter(
                or_(UserFriend.user_id == user.id, UserFriend.friend_id == user.id)
            ).scalar()
            
            # Get recent social activity
            recent_activity = db.session.query(SocialActivity).filter_by(user_id=user.id).order_by(
                SocialActivity.created_at.desc()
            ).limit(5).all()
            
            return {
                'following_count': following_count,
                'followers_count': followers_count,
                'friends_count': friends_count,
                'recent_activity': [
                    {
                        'id': activity.id,
                        'activity_type': activity.activity_type,
                        'created_at': activity.created_at.isoformat()
                    } for activity in recent_activity
                ]
            }
        except Exception as e:
            try:
                current_app.logger.error(f"Error getting social summary for user {user.id}: {e}")
            except RuntimeError:
                logger.error(f"Error getting social summary for user {user.id}: {e}")
            return None
    
    @staticmethod
    def _get_analytics_summary(user):
        """Get analytics data summary with optimized queries."""
        try:
            # Check if analytics models are available
            if UserBehavior is None or UserEngagement is None:
                logger.warning("Analytics models not available, returning None")
                return None
            
            # Use optimized count queries for analytics
            total_behaviors = db.session.query(func.count(UserBehavior.id)).filter_by(user_id=user.id).scalar()
            total_engagements = db.session.query(func.count(UserEngagement.id)).filter_by(user_id=user.id).scalar()
            
            # Get recent engagement score
            recent_engagement = db.session.query(UserEngagement).filter_by(user_id=user.id).order_by(
                UserEngagement.created_at.desc()
            ).first()
            
            # Get behavior summary by type
            behavior_summary = db.session.query(
                UserBehavior.behavior_type,
                func.count(UserBehavior.id).label('count')
            ).filter_by(user_id=user.id).group_by(UserBehavior.behavior_type).all()
            
            return {
                'total_behaviors': total_behaviors,
                'total_engagements': total_engagements,
                'recent_engagement_score': recent_engagement.engagement_score if recent_engagement else 0,
                'behavior_summary': [
                    {'type': behavior.behavior_type, 'count': behavior.count}
                    for behavior in behavior_summary
                ]
            }
        except Exception as e:
            try:
                current_app.logger.error(f"Error getting analytics summary for user {user.id}: {e}")
            except RuntimeError:
                logger.error(f"Error getting analytics summary for user {user.id}: {e}")
            return None
    
    @staticmethod
    def invalidate_profile_cache(user_id):
        """Invalidate profile cache for a user."""
        patterns = [
            f"profile:{user_id}:optimized:*",
            f"profile:{user_id}:*",
            f"user:{user_id}:*"
        ]
        
        for pattern in patterns:
            # Delete all cache keys matching pattern
            try:
                cache.delete_many([pattern])
            except:
                # Fallback to individual key deletion
                keys = cache.cache._cache.keys()
                for key in keys:
                    if pattern.replace('*', '') in key:
                        cache.delete(key)
    
    @staticmethod
    def batch_get_profiles(user_ids, include_social=True, include_analytics=False):
        """Batch get multiple optimized profiles for better performance."""
        profiles = {}
        
        # Try to get from cache first
        cache_keys = [f"profile:{user_id}:optimized:{include_social}:{include_analytics}" 
                     for user_id in user_ids]
        
        cached_data = cache.get_many(cache_keys)
        
        # Identify which profiles need to be fetched from database
        uncached_user_ids = []
        for i, user_id in enumerate(user_ids):
            cache_key = cache_keys[i]
            if cache_key in cached_data:
                profiles[user_id] = cached_data[cache_key]
            else:
                uncached_user_ids.append(user_id)
        
        # Batch fetch uncached profiles
        if uncached_user_ids:
            query = User.query.filter(User.id.in_(uncached_user_ids))
            
            # Apply same optimization strategy as single profile
            query = query.options(
                selectinload(User.badges),
                selectinload(User.roles)
            )
            
            if include_social:
                query = query.options(
                    lazyload(User.following),
                    lazyload(User.followers),
                    lazyload(User.friends)
                )
            
            if include_analytics:
                query = query.options(
                    lazyload(User.behaviors),
                    lazyload(User.engagements)
                )
            
            users = query.all()
            
            # Process and cache each user
            for user in users:
                profile_data = ProfilePerformanceOptimizer.get_optimized_profile(
                    user.id, include_social, include_analytics
                )
                profiles[user.id] = profile_data
        
        return profiles
    
    @staticmethod
    def get_profile_performance_metrics(user_id):
        """Get performance metrics for profile loading."""
        start_time = time.time()
        
        # Test optimized profile loading
        profile = ProfilePerformanceOptimizer.get_optimized_profile(user_id)
        
        end_time = time.time()
        load_time = end_time - start_time
        
        # Get cache statistics
        cache_info = cache.get(f"profile:{user_id}:performance:cache_info")
        if not cache_info:
            cache_info = {
                'cache_hits': 0,
                'cache_misses': 0,
                'total_requests': 0
            }
        
        cache_info['total_requests'] += 1
        if profile and 'cached_at' in profile:
            cache_info['cache_hits'] += 1
        else:
            cache_info['cache_misses'] += 1
        
        cache.set(f"profile:{user_id}:performance:cache_info", cache_info, timeout=3600)
        
        return {
            'load_time': load_time,
            'cache_hit_rate': cache_info['cache_hits'] / cache_info['total_requests'] * 100,
            'total_requests': cache_info['total_requests'],
            'cache_hits': cache_info['cache_hits'],
            'cache_misses': cache_info['cache_misses']
        }


class AnalyticsPerformanceOptimizer:
    """Optimizes analytics performance with real-time processing and caching."""
    
    @staticmethod
    def get_analytics_data_warehouse(user_id, start_date, end_date):
        """Get analytics data from optimized warehouse with caching."""
        cache_key = f"analytics:warehouse:{user_id}:{start_date}:{end_date}"
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Check if analytics models are available
        if UserBehavior is None:
            logger.warning("UserBehavior model not available, returning None")
            return None
        
        # Use optimized database queries
        behaviors_query = db.session.query(UserBehavior).filter(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= start_date,
                UserBehavior.created_at <= end_date
            )
        )
        
        # Use pagination for large datasets
        behaviors = behaviors_query.limit(1000).all()
        
        # Aggregate data efficiently
        aggregated_data = AnalyticsPerformanceOptimizer._aggregate_analytics_data(
            user_id, start_date, end_date, behaviors
        )
        
        # Cache for 10 minutes
        cache.set(cache_key, aggregated_data, timeout=600)
        
        return aggregated_data
    
    @staticmethod
    def _aggregate_analytics_data(user_id, start_date, end_date, behaviors):
        """Aggregate analytics data efficiently."""
        # Pre-aggregate behavior counts by type
        behavior_counts = {}
        for behavior in behaviors:
            behavior_type = behavior.behavior_type
            if behavior_type not in behavior_counts:
                behavior_counts[behavior_type] = 0
            behavior_counts[behavior_type] += 1
        
        # Get engagement data
        engagements = db.session.query(UserEngagement).filter(
            and_(
                UserEngagement.user_id == user_id,
                UserEngagement.created_at >= start_date,
                UserEngagement.created_at <= end_date
            )
        ).all()
        
        # Calculate engagement metrics
        total_engagement_score = sum(eng.engagement_score for eng in engagements)
        avg_engagement_score = total_engagement_score / len(engagements) if engagements else 0
        
        return {
            'user_id': user_id,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'behaviors': {
                'total_count': len(behaviors),
                'behavior_counts': behavior_counts,
                'sample_behaviors': [
                    {
                        'id': behavior.id,
                        'behavior_type': behavior.behavior_type,
                        'action': behavior.action,
                        'created_at': behavior.created_at.isoformat()
                    } for behavior in behaviors[:100]  # Limit sample size
                ]
            },
            'engagements': {
                'total_count': len(engagements),
                'total_score': total_engagement_score,
                'average_score': avg_engagement_score,
                'sample_engagements': [
                    {
                        'id': eng.id,
                        'engagement_type': eng.engagement_type,
                        'engagement_score': eng.engagement_score,
                        'created_at': eng.created_at.isoformat()
                    } for eng in engagements[:50]  # Limit sample size
                ]
            },
            'cached_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def process_real_time_analytics(user_id, event_type, event_data):
        """Process real-time analytics events with optimized performance."""
        try:
            # Create behavior record
            behavior = UserBehavior(
                user_id=user_id,
                behavior_type=event_data.get('behavior_type'),
                action=event_data.get('action'),
                behavior_metadata=event_data.get('metadata', {})
            )
            
            db.session.add(behavior)
            
            # Update engagement metrics if needed
            if event_type in ['login', 'post', 'comment', 'like', 'share']:
                AnalyticsPerformanceOptimizer._update_engagement_metrics(user_id, event_type)
            
            # Invalidate relevant caches
            cache_patterns = [
                f"analytics:warehouse:{user_id}:*",
                f"analytics:dashboard:{user_id}:*",
                f"analytics:realtime:{user_id}:*"
            ]
            
            for pattern in cache_patterns:
                try:
                    cache.delete_many([pattern])
                except:
                    pass  # Ignore cache deletion errors
            
            db.session.commit()
            
            # Update real-time cache
            realtime_key = f"analytics:realtime:{user_id}"
            realtime_data = cache.get(realtime_key) or {}
            
            realtime_data['last_event'] = {
                'type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': event_data
            }
            
            # Update event counts
            if 'event_counts' not in realtime_data:
                realtime_data['event_counts'] = {}
            
            realtime_data['event_counts'][event_type] = realtime_data['event_counts'].get(event_type, 0) + 1
            
            # Cache for 1 minute
            cache.set(realtime_key, realtime_data, timeout=60)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error processing real-time analytics for user {user_id}: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def _update_engagement_metrics(user_id, event_type):
        """Update engagement metrics efficiently."""
        # Calculate engagement score based on event type
        engagement_scores = {
            'login': 1,
            'post': 5,
            'comment': 3,
            'like': 2,
            'share': 4
        }
        
        score = engagement_scores.get(event_type, 1)
        
        # Create or update engagement record
        engagement = UserEngagement(
            user_id=user_id,
            engagement_type=event_type,
            engagement_score=score,
            engagement_metadata={'event_type': event_type}
        )
        
        db.session.add(engagement)
    
    @staticmethod
    def generate_analytics_visualization(user_id, chart_type, period='7d'):
        """Generate analytics visualization with optimized performance."""
        cache_key = f"analytics:viz:{user_id}:{chart_type}:{period}"
        
        # Try cache first
        cached_viz = cache.get(cache_key)
        if cached_viz:
            return cached_viz
        
        # Calculate date range
        end_date = datetime.utcnow()
        if period == '7d':
            start_date = end_date - timedelta(days=7)
        elif period == '30d':
            start_date = end_date - timedelta(days=30)
        elif period == '90d':
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Generate visualization data based on chart type
        if chart_type == 'engagement_trend':
            viz_data = AnalyticsPerformanceOptimizer._generate_engagement_trend(
                user_id, start_date, end_date
            )
        elif chart_type == 'activity_breakdown':
            viz_data = AnalyticsPerformanceOptimizer._generate_activity_breakdown(
                user_id, start_date, end_date
            )
        elif chart_type == 'performance_metrics':
            viz_data = AnalyticsPerformanceOptimizer._generate_performance_metrics(
                user_id, start_date, end_date
            )
        else:
            viz_data = {'error': 'Unknown chart type'}
        
        # Cache for 5 minutes
        cache.set(cache_key, viz_data, timeout=300)
        
        return viz_data
    
    @staticmethod
    def _generate_engagement_trend(user_id, start_date, end_date):
        """Generate engagement trend visualization data."""
        # Use optimized date-based aggregation
        engagement_data = db.session.query(
            func.date(UserEngagement.created_at).label('date'),
            func.sum(UserEngagement.engagement_score).label('total_score'),
            func.count(UserEngagement.id).label('count')
        ).filter(
            and_(
                UserEngagement.user_id == user_id,
                UserEngagement.created_at >= start_date,
                UserEngagement.created_at <= end_date
            )
        ).group_by(func.date(UserEngagement.created_at)).all()
        
        # Format for chart.js
        dates = []
        scores = []
        counts = []
        
        for data in engagement_data:
            dates.append(data.date.isoformat())
            scores.append(float(data.total_score))
            counts.append(data.count)
        
        return {
            'chart_type': 'line',
            'data': {
                'labels': dates,
                'datasets': [
                    {
                        'label': 'Engagement Score',
                        'data': scores,
                        'borderColor': 'rgb(75, 192, 192)',
                        'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    },
                    {
                        'label': 'Activity Count',
                        'data': counts,
                        'borderColor': 'rgb(255, 99, 132)',
                        'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    }
                ]
            }
        }
    
    @staticmethod
    def _generate_activity_breakdown(user_id, start_date, end_date):
        """Generate activity breakdown visualization data."""
        # Use optimized behavior type aggregation
        behavior_data = db.session.query(
            UserBehavior.behavior_type,
            func.count(UserBehavior.id).label('count')
        ).filter(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= start_date,
                UserBehavior.created_at <= end_date
            )
        ).group_by(UserBehavior.behavior_type).all()
        
        # Format for pie chart
        labels = []
        data = []
        colors = []
        
        color_map = {
            'login': '#FF6384',
            'post': '#36A2EB',
            'comment': '#FFCE56',
            'like': '#4BC0C0',
            'share': '#9966FF'
        }
        
        for behavior in behavior_data:
            labels.append(behavior.behavior_type)
            data.append(behavior.count)
            colors.append(color_map.get(behavior.behavior_type, '#CCCCCC'))
        
        return {
            'chart_type': 'pie',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': data,
                    'backgroundColor': colors,
                }]
            }
        }
    
    @staticmethod
    def _generate_performance_metrics(user_id, start_date, end_date):
        """Generate performance metrics visualization data."""
        # Calculate performance metrics
        total_behaviors = db.session.query(func.count(UserBehavior.id)).filter(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= start_date,
                UserBehavior.created_at <= end_date
            )
        ).scalar()
        
        total_engagement = db.session.query(func.sum(UserEngagement.engagement_score)).filter(
            and_(
                UserEngagement.user_id == user_id,
                UserEngagement.created_at >= start_date,
                UserEngagement.created_at <= end_date
            )
        ).scalar() or 0
        
        avg_engagement = total_engagement / total_behaviors if total_behaviors > 0 else 0
        
        return {
            'chart_type': 'bar',
            'data': {
                'labels': ['Total Behaviors', 'Total Engagement', 'Avg Engagement'],
                'datasets': [{
                    'label': 'Performance Metrics',
                    'data': [total_behaviors, total_engagement, avg_engagement],
                    'backgroundColor': ['rgba(255, 99, 132, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(255, 206, 86, 0.2)'],
                    'borderColor': ['rgb(255, 99, 132)', 'rgb(54, 162, 235)', 'rgb(255, 206, 86)'],
                    'borderWidth': 1
                }]
            }
        }
    
    @staticmethod
    def get_analytics_performance_metrics():
        """Get analytics system performance metrics."""
        cache_key = "analytics:performance:metrics"
        
        cached_metrics = cache.get(cache_key)
        if cached_metrics:
            return cached_metrics
        
        # Calculate performance metrics
        start_time = time.time()
        
        # Test data warehouse query
        test_user_id = 1  # Use a test user ID
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        warehouse_data = AnalyticsPerformanceOptimizer.get_analytics_data_warehouse(
            test_user_id, start_date, end_date
        )
        
        warehouse_time = time.time() - start_time
        
        # Test visualization generation
        start_time = time.time()
        
        viz_data = AnalyticsPerformanceOptimizer.generate_analytics_visualization(
            test_user_id, 'engagement_trend', '7d'
        )
        
        viz_time = time.time() - start_time
        
        metrics = {
            'data_warehouse_query_time': warehouse_time,
            'visualization_generation_time': viz_time,
            'total_time': warehouse_time + viz_time,
            'cache_hit_rate': 0,  # Would be calculated from actual usage
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, metrics, timeout=300)
        
        return metrics


class SocialPerformanceOptimizer:
    """Optimizes social performance with graph optimization and caching."""
    
    @staticmethod
    def get_social_graph_data(user_id, depth=2):
        """Get social graph data with optimized performance."""
        cache_key = f"social:graph:{user_id}:depth:{depth}"
        
        # Try cache first
        cached_graph = cache.get(cache_key)
        if cached_graph:
            return cached_graph
        
        # Check if social models are available
        if UserFollow is None:
            logger.warning("UserFollow model not available, returning None")
            return None
        
        # Use optimized graph building
        graph_data = SocialPerformanceOptimizer._build_optimized_graph(user_id, depth)
        
        # Cache for 10 minutes
        cache.set(cache_key, graph_data, timeout=600)
        
        return graph_data
    
    @staticmethod
    def _build_optimized_graph(user_id, depth):
        """Build social graph with optimized queries."""
        # Get user's direct connections with optimized query
        following = db.session.query(UserFollow).filter_by(follower_id=user_id).all()
        followers = db.session.query(UserFollow).filter_by(following_id=user_id).all()
        
        # Build nodes and edges
        nodes = {'id': user_id, 'label': f'User {user_id}', 'type': 'user'}
        edges = []
        
        # Add following relationships
        for follow in following:
            following_id = follow.following_id
            nodes[following_id] = {'id': following_id, 'label': f'User {following_id}', 'type': 'user'}
            edges.append({
                'from': user_id,
                'to': following_id,
                'type': 'follow',
                'created_at': follow.created_at.isoformat()
            })
        
        # Add follower relationships
        for follow in followers:
            follower_id = follow.follower_id
            nodes[follower_id] = {'id': follower_id, 'label': f'User {follower_id}', 'type': 'user'}
            edges.append({
                'from': follower_id,
                'to': user_id,
                'type': 'follow',
                'created_at': follow.created_at.isoformat()
            })
        
        # Add second-degree connections if depth > 1
        if depth > 1:
            second_degree_ids = set()
            
            for follow in following:
                second_degree_ids.add(follow.following_id)
            
            for follow in followers:
                second_degree_ids.add(follow.follower_id)
            
            # Get connections of second-degree users
            if second_degree_ids:
                second_connections = db.session.query(UserFollow).filter(
                    UserFollow.follower_id.in_(second_degree_ids)
                ).limit(100).all()  # Limit to prevent performance issues
                
                for conn in second_connections:
                    if conn.following_id not in nodes:
                        nodes[conn.following_id] = {
                            'id': conn.following_id, 
                            'label': f'User {conn.following_id}', 
                            'type': 'second_degree'
                        }
                        edges.append({
                            'from': conn.follower_id,
                            'to': conn.following_id,
                            'type': 'follow',
                            'created_at': conn.created_at.isoformat()
                        })
        
        # Convert nodes dict to list
        node_list = list(nodes.values())
        
        # Calculate graph statistics
        stats = {
            'total_nodes': len(node_list),
            'total_edges': len(edges),
            'following_count': len(following),
            'followers_count': len(followers),
            'mutual_connections': SocialPerformanceOptimizer._count_mutual_connections(user_id),
            'graph_density': len(edges) / (len(node_list) * (len(node_list) - 1)) if len(node_list) > 1 else 0
        }
        
        return {
            'nodes': node_list,
            'edges': edges,
            'stats': stats,
            'depth': depth,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _count_mutual_connections(user_id):
        """Count mutual connections efficiently."""
        # Get user's following and followers
        following = db.session.query(UserFollow.following_id).filter_by(follower_id=user_id).subquery()
        followers = db.session.query(UserFollow.follower_id).filter_by(following_id=user_id).subquery()
        
        # Find mutual connections
        mutual = db.session.query(following.c.following_id).filter(
            following.c.following_id.in_(followers)
        ).count()
        
        return mutual
    
    @staticmethod
    def process_social_feed(user_id, limit=50, include_friends=True):
        """Process social feed with optimized performance."""
        cache_key = f"social:feed:{user_id}:{limit}:{include_friends}"
        
        # Try cache first
        cached_feed = cache.get(cache_key)
        if cached_feed:
            return cached_feed
        
        # Get user's following with optimized query
        following_ids = SocialPerformanceOptimizer._get_following_ids(user_id, include_friends)
        
        if not following_ids:
            return {'items': [], 'stats': {'total_items': 0}}
        
        # Get activities with optimized query
        activities = db.session.query(SocialActivity).filter(
            and_(
                SocialActivity.user_id.in_(following_ids),
                SocialActivity.is_public == True
            )
        ).order_by(SocialActivity.created_at.desc()).limit(limit).all()
        
        # Process feed items
        feed_items = []
        user_cache = {}  # Cache user data to avoid repeated queries
        
        for activity in activities:
            # Get user data from cache or query
            if activity.user_id not in user_cache:
                user = db.session.query(User).filter_by(id=activity.user_id).first()
                user_cache[activity.user_id] = {
                    'id': user.id,
                    'username': user.username,
                    'avatar_url': user.avatar_url
                }
            
            feed_item = {
                'id': activity.id,
                'user': user_cache[activity.user_id],
                'activity_type': activity.activity_type,
                'activity_data': activity.activity_data,
                'target_user_id': activity.target_user_id,
                'created_at': activity.created_at.isoformat()
            }
            
            feed_items.append(feed_item)
        
        # Calculate feed statistics
        stats = {
            'total_items': len(feed_items),
            'following_count': len(following_ids),
            'cache_key': cache_key,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        feed_data = {
            'items': feed_items,
            'stats': stats
        }
        
        # Cache for 3 minutes
        cache.set(cache_key, feed_data, timeout=180)
        
        return feed_data
    
    @staticmethod
    def _get_following_ids(user_id, include_friends=True):
        """Get following IDs efficiently."""
        following_ids = db.session.query(UserFollow.following_id).filter_by(follower_id=user_id).all()
        following_ids = [f[0] for f in following_ids]
        
        if include_friends:
            # Add friends (mutual follows)
            friends = db.session.query(UserFriend).filter(
                or_(UserFriend.user_id == user_id, UserFriend.friend_id == user_id)
            ).all()
            
            for friend in friends:
                if friend.user_id == user_id:
                    following_ids.append(friend.friend_id)
                else:
                    following_ids.append(friend.user_id)
        
        return list(set(following_ids))  # Remove duplicates
    
    @staticmethod
    def get_social_analytics(user_id, days=30):
        """Get social analytics with optimized performance."""
        cache_key = f"social:analytics:{user_id}:{days}"
        
        # Try cache first
        cached_analytics = cache.get(cache_key)
        if cached_analytics:
            return cached_analytics
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Use optimized queries for social metrics
        following_growth = SocialPerformanceOptimizer._get_following_growth(user_id, start_date)
        followers_growth = SocialPerformanceOptimizer._get_followers_growth(user_id, start_date)
        activity_summary = SocialPerformanceOptimizer._get_activity_summary(user_id, start_date)
        
        analytics_data = {
            'user_id': user_id,
            'period': f'{days} days',
            'following_growth': following_growth,
            'followers_growth': followers_growth,
            'activity_summary': activity_summary,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Cache for 15 minutes
        cache.set(cache_key, analytics_data, timeout=900)
        
        return analytics_data
    
    @staticmethod
    def _get_following_growth(user_id, start_date):
        """Get following growth analytics."""
        # Get following count over time
        following_data = db.session.query(
            func.date(UserFollow.created_at).label('date'),
            func.count(UserFollow.id).label('count')
        ).filter(
            and_(
                UserFollow.follower_id == user_id,
                UserFollow.created_at >= start_date
            )
        ).group_by(func.date(UserFollow.created_at)).order_by(func.date(UserFollow.created_at)).all()
        
        dates = []
        counts = []
        cumulative_count = 0
        
        for data in following_data:
            cumulative_count += data.count
            dates.append(data.date.isoformat())
            counts.append(cumulative_count)
        
        return {
            'dates': dates,
            'counts': counts,
            'current_count': cumulative_count
        }
    
    @staticmethod
    def _get_followers_growth(user_id, start_date):
        """Get followers growth analytics."""
        # Get followers count over time
        followers_data = db.session.query(
            func.date(UserFollow.created_at).label('date'),
            func.count(UserFollow.id).label('count')
        ).filter(
            and_(
                UserFollow.following_id == user_id,
                UserFollow.created_at >= start_date
            )
        ).group_by(func.date(UserFollow.created_at)).order_by(func.date(UserFollow.created_at)).all()
        
        dates = []
        counts = []
        cumulative_count = 0
        
        for data in followers_data:
            cumulative_count += data.count
            dates.append(data.date.isoformat())
            counts.append(cumulative_count)
        
        return {
            'dates': dates,
            'counts': counts,
            'current_count': cumulative_count
        }
    
    @staticmethod
    def _get_activity_summary(user_id, start_date):
        """Get activity summary analytics."""
        # Get activity summary by type
        activity_data = db.session.query(
            SocialActivity.activity_type,
            func.count(SocialActivity.id).label('count')
        ).filter(
            and_(
                SocialActivity.user_id == user_id,
                SocialActivity.created_at >= start_date
            )
        ).group_by(SocialActivity.activity_type).all()
        
        activity_summary = {}
        total_activities = 0
        
        for data in activity_data:
            activity_summary[data.activity_type] = data.count
            total_activities += data.count
        
        return {
            'by_type': activity_summary,
            'total_activities': total_activities
        }
    
    @staticmethod
    def get_social_performance_metrics():
        """Get social system performance metrics."""
        cache_key = "social:performance:metrics"
        
        cached_metrics = cache.get(cache_key)
        if cached_metrics:
            return cached_metrics
        
        # Calculate performance metrics
        start_time = time.time()
        
        # Test graph generation
        test_user_id = 1
        graph_data = SocialPerformanceOptimizer.get_social_graph_data(test_user_id, depth=2)
        
        graph_time = time.time() - start_time
        
        # Test feed processing
        start_time = time.time()
        
        feed_data = SocialPerformanceOptimizer.process_social_feed(test_user_id, limit=20)
        
        feed_time = time.time() - start_time
        
        # Test analytics generation
        start_time = time.time()
        
        analytics_data = SocialPerformanceOptimizer.get_social_analytics(test_user_id, days=7)
        
        analytics_time = time.time() - start_time
        
        metrics = {
            'graph_generation_time': graph_time,
            'feed_processing_time': feed_time,
            'analytics_generation_time': analytics_time,
            'total_time': graph_time + feed_time + analytics_time,
            'cache_hit_rate': 0,  # Would be calculated from actual usage
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, metrics, timeout=300)
        
        return metrics


# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Log performance metrics (handle application context)
            try:
                from flask import current_app
                current_app.logger.info(f"Performance: {func.__name__} executed in {execution_time:.4f}s")
            except RuntimeError:
                # Working outside application context, use standard logger
                logger.info(f"Performance: {func.__name__} executed in {execution_time:.4f}s")
            
            # Store performance metrics in cache for monitoring
            metrics_key = f"performance:{func.__name__}"
            metrics = cache.get(metrics_key) or {'executions': [], 'avg_time': 0}
            
            metrics['executions'].append({
                'execution_time': execution_time,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Keep only last 100 executions
            if len(metrics['executions']) > 100:
                metrics['executions'] = metrics['executions'][-100:]
            
            # Calculate average time
            metrics['avg_time'] = sum(e['execution_time'] for e in metrics['executions']) / len(metrics['executions'])
            
            cache.set(metrics_key, metrics, timeout=3600)
            
            return result
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            try:
                from flask import current_app
                current_app.logger.error(f"Performance: {func.__name__} failed after {execution_time:.4f}s - {e}")
            except RuntimeError:
                # Working outside application context, use standard logger
                logger.error(f"Performance: {func.__name__} failed after {execution_time:.4f}s - {e}")
            raise
    
    return wrapper


# Import models that are used in the performance optimizers
try:
    from app.user.social.models import UserFollow, UserFriend, SocialActivity
except ImportError as e:
    logger.warning(f"Could not import social models: {e}")
    UserFollow = UserFriend = SocialActivity = None

try:
    from app.user.analytics.models import UserBehavior, UserEngagement
except ImportError as e:
    logger.warning(f"Could not import analytics models: {e}")
    UserBehavior = UserEngagement = None
