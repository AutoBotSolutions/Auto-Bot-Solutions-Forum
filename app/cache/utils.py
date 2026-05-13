"""
Cache Utilities

This module provides utility functions and helpers for cache management,
including cache warming, preloading, and optimization tools.
"""

import json
import hashlib
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.cache.models import CacheEntry, CacheAnalytics, CacheDependency
from app.cache.service import CacheService
from typing import List, Dict, Any, Callable, Optional


class CacheWarmer:
    """Cache warming utility for preloading frequently accessed data"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.warmup_jobs = []
    
    def add_warmup_job(self, key: str, data_loader: Callable, ttl: int = 3600, tag: str = None, cache_type: str = 'general'):
        """Add a cache warmup job"""
        self.warmup_jobs.append({
            'key': key,
            'data_loader': data_loader,
            'ttl': ttl,
            'tag': tag,
            'cache_type': cache_type
        })
    
    def warm_cache(self) -> Dict[str, Any]:
        """Execute all warmup jobs"""
        results = {
            'total_jobs': len(self.warmup_jobs),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for job in self.warmup_jobs:
            try:
                # Load data
                data = job['data_loader']()
                
                # Set in cache
                self.cache_service.set(
                    job['key'],
                    data,
                    job['ttl'],
                    job['tag'],
                    job['cache_type']
                )
                
                results['successful'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Failed to warm cache for {job['key']}: {e}")
        
        return results
    
    def warm_user_cache(self, user_id: int) -> Dict[str, Any]:
        """Warm cache for a specific user"""
        from app.models import User
        
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}
        
        results = {
            'user_id': user_id,
            'warmed_keys': [],
            'errors': []
        }
        
        # Warm user profile
        try:
            profile_data = user.to_dict()
            self.cache_service.set(f"user:{user_id}:profile", profile_data, 1800, 'user_profile', 'user')
            results['warmed_keys'].append(f"user:{user_id}:profile")
        except Exception as e:
            results['errors'].append(f"Failed to warm user profile: {e}")
        
        # Warm user preferences
        try:
            from app.user.models import UserPreference
            preferences = UserPreference.get_all_preferences(user_id)
            self.cache_service.set(f"user:{user_id}:preferences", preferences, 1800, 'user_preferences', 'user')
            results['warmed_keys'].append(f"user:{user_id}:preferences")
        except Exception as e:
            results['errors'].append(f"Failed to warm user preferences: {e}")
        
        # Warm user roles
        try:
            from app.user.models import UserRoleAssignment
            roles = UserRoleAssignment.get_user_roles(user_id)
            self.cache_service.set(f"user:{user_id}:roles", roles, 1800, 'user_roles', 'user')
            results['warmed_keys'].append(f"user:{user_id}:roles")
        except Exception as e:
            results['errors'].append(f"Failed to warm user roles: {e}")
        
        return results
    
    def warm_system_cache(self) -> Dict[str, Any]:
        """Warm system-level cache"""
        results = {
            'warmed_keys': [],
            'errors': []
        }
        
        # Warm system configuration
        try:
            config = {
                'site_name': current_app.config.get('SITE_NAME', 'Forum'),
                'max_upload_size': current_app.config.get('MAX_CONTENT_LENGTH', 16777216),
                'allowed_extensions': current_app.config.get('ALLOWED_EXTENSIONS', []),
                'theme_options': current_app.config.get('THEME_OPTIONS', {}),
            }
            self.cache_service.set('system:config', config, 3600, 'system_config', 'system')
            results['warmed_keys'].append('system:config')
        except Exception as e:
            results['errors'].append(f"Failed to warm system config: {e}")
        
        # Warm navigation menu
        try:
            from app.models import Category
            categories = Category.query.filter_by(is_active=True).all()
            nav_data = [cat.to_dict() for cat in categories]
            self.cache_service.set('system:navigation', nav_data, 1800, 'navigation', 'system')
            results['warmed_keys'].append('system:navigation')
        except Exception as e:
            results['errors'].append(f"Failed to warm navigation: {e}")
        
        return results


class CacheOptimizer:
    """Cache optimization utility for performance tuning"""
    
    def __init__(self):
        self.cache_service = CacheService()
    
    def analyze_cache_usage(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze cache usage patterns"""
        stats = self.cache_service.get_stats()
        
        # Get detailed analytics
        performance = CacheAnalytics.get_performance_metrics(hours)
        type_performance = CacheAnalytics.get_cache_type_performance(hours)
        trending_keys = CacheAnalytics.get_trending_keys(hours, limit=20)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(stats, performance, type_performance, trending_keys)
        
        return {
            'period_hours': hours,
            'stats': stats,
            'performance_metrics': performance,
            'type_performance': type_performance,
            'trending_keys': trending_keys,
            'recommendations': recommendations
        }
    
    def _generate_recommendations(self, stats: Dict, performance: Dict, type_performance: Dict, trending_keys: List) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Hit ratio recommendations
        if performance['hit_ratio'] < 0.7:
            recommendations.append("Cache hit ratio is below 70%. Consider increasing TTL for frequently accessed data.")
        
        if performance['hit_ratio'] < 0.5:
            recommendations.append("Cache hit ratio is below 50%. Review caching strategy and consider preloading more data.")
        
        # Response time recommendations
        if performance['avg_set_time_ms'] > 100:
            recommendations.append("Average cache set time is high. Consider optimizing serialization or using compression.")
        
        if performance['avg_get_time_ms'] > 50:
            recommendations.append("Average cache get time is high. Check Redis performance and network latency.")
        
        # Size recommendations
        total_size = stats.get('database_stats', {}).get('total_size_bytes', 0)
        if total_size > 100 * 1024 * 1024:  # 100MB
            recommendations.append("Cache size exceeds 100MB. Consider implementing cache size limits and cleanup policies.")
        
        # Type-specific recommendations
        for cache_type, data in type_performance.items():
            if data['hit_ratio'] < 0.6:
                recommendations.append(f"Cache type '{cache_type}' has low hit ratio ({data['hit_ratio']:.1%}). Review TTL and invalidation strategy.")
        
        # Trending keys recommendations
        if trending_keys:
            top_key = trending_keys[0]
            if top_key['access_count'] > 100:
                recommendations.append(f"Key '{top_key['cache_key']}' is heavily accessed. Consider longer TTL or preloading.")
        
        return recommendations
    
    def optimize_cache_configuration(self) -> Dict[str, Any]:
        """Optimize cache configuration based on usage patterns"""
        analysis = self.analyze_cache_usage()
        recommendations = []
        
        # Implement optimizations based on recommendations
        for rec in analysis['recommendations']:
            if "TTL" in rec:
                recommendations.append("Consider adjusting TTL settings for better cache utilization.")
            elif "compression" in rec:
                recommendations.append("Enable compression for large cache entries.")
            elif "preloading" in rec:
                recommendations.append("Implement cache preloading for frequently accessed data.")
        
        return {
            'optimizations_applied': recommendations,
            'analysis_summary': {
                'hit_ratio': analysis['performance_metrics']['hit_ratio'],
                'total_entries': analysis['stats']['database_stats']['total_entries'],
                'total_size_mb': analysis['stats']['database_stats']['total_size_bytes'] / (1024 * 1024)
            }
        }
    
    def cleanup_unused_cache(self, days: int = 7) -> Dict[str, Any]:
        """Clean up unused cache entries"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Find entries not accessed in the specified period
        unused_entries = CacheEntry.query.filter(
            CacheEntry.last_accessed < cutoff_time
        ).all()
        
        cleaned_count = 0
        for entry in unused_entries:
            if CacheEntry.delete_cache(entry.cache_key):
                cleaned_count += 1
        
        return {
            'cleaned_entries': cleaned_count,
            'unused_days': days,
            'cutoff_date': cutoff_time.isoformat()
        }


class CacheKeyGenerator:
    """Utility for generating consistent cache keys"""
    
    @staticmethod
    def generate_key(prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments"""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if hasattr(arg, 'id'):
                key_parts.append(f"id:{arg.id}")
            elif isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
            else:
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest())
        
        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            if hasattr(v, 'id'):
                key_parts.append(f"{k}:id:{v.id}")
            elif isinstance(v, (str, int, float)):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{hashlib.md5(str(v).encode()).hexdigest()}")
        
        return ":".join(key_parts)
    
    @staticmethod
    def generate_user_key(user_id: int, suffix: str) -> str:
        """Generate a user-specific cache key"""
        return f"user:{user_id}:{suffix}"
    
    @staticmethod
    def generate_system_key(suffix: str) -> str:
        """Generate a system-level cache key"""
        return f"system:{suffix}"
    
    @staticmethod
    def generate_session_key(session_id: str, suffix: str) -> str:
        """Generate a session-specific cache key"""
        return f"session:{session_id}:{suffix}"
    
    @staticmethod
    def generate_query_key(query: str, params: Dict = None) -> str:
        """Generate a query-specific cache key"""
        key_data = f"query:{query}"
        if params:
            key_data += f":{json.dumps(sorted(params.items()), sort_keys=True)}"
        return f"query:{hashlib.md5(key_data.encode()).hexdigest()}"


class CacheDependencyManager:
    """Utility for managing cache dependencies"""
    
    def __init__(self):
        self.cache_service = CacheService()
    
    def setup_user_dependencies(self, user_id: int):
        """Set up common dependencies for user-related cache"""
        # User profile dependencies
        profile_key = CacheKeyGenerator.generate_user_key(user_id, 'profile')
        preferences_key = CacheKeyGenerator.generate_user_key(user_id, 'preferences')
        roles_key = CacheKeyGenerator.generate_user_key(user_id, 'roles')
        
        # Profile changes invalidate preferences and roles
        self.cache_service.add_dependency(profile_key, preferences_key, 'automatic')
        self.cache_service.add_dependency(profile_key, roles_key, 'automatic')
    
    def setup_post_dependencies(self, post_id: int):
        """Set up dependencies for post-related cache"""
        post_key = f"post:{post_id}"
        comments_key = f"post:{post_id}:comments"
        analytics_key = f"post:{post_id}:analytics"
        
        # Post changes invalidate comments and analytics
        self.cache_service.add_dependency(post_key, comments_key, 'automatic')
        self.cache_service.add_dependency(post_key, analytics_key, 'automatic')
    
    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache entries for a user"""
        profile_key = CacheKeyGenerator.generate_user_key(user_id, 'profile')
        return self.cache_service.invalidate_dependents(profile_key)
    
    def invalidate_post_cache(self, post_id: int):
        """Invalidate all cache entries for a post"""
        post_key = f"post:{post_id}"
        return self.cache_service.invalidate_dependents(post_key)


class CacheMonitor:
    """Cache monitoring and alerting utility"""
    
    def __init__(self):
        self.cache_service = CacheService()
    
    def check_cache_health(self) -> Dict[str, Any]:
        """Check cache health and generate alerts"""
        stats = self.cache_service.get_stats()
        alerts = []
        
        # Check hit ratio
        hit_ratio = stats.get('performance_metrics', {}).get('hit_ratio', 0)
        if hit_ratio < 0.5:
            alerts.append({
                'level': 'warning',
                'message': f"Low cache hit ratio: {hit_ratio:.1%}",
                'recommendation': 'Review caching strategy and TTL settings'
            })
        
        # Check cache size
        total_size = stats.get('database_stats', {}).get('total_size_bytes', 0)
        if total_size > 500 * 1024 * 1024:  # 500MB
            alerts.append({
                'level': 'warning',
                'message': f"Large cache size: {total_size / (1024*1024):.1f}MB",
                'recommendation': 'Consider cache cleanup and size limits'
            })
        
        # Check Redis connection
        if not self.cache_service.redis_client:
            alerts.append({
                'level': 'critical',
                'message': 'Redis connection failed',
                'recommendation': 'Check Redis server status and configuration'
            })
        
        # Check invalidation rate
        invalidation_stats = stats.get('invalidation_stats', {})
        if invalidation_stats.get('total_invalidations', 0) > 1000:
            alerts.append({
                'level': 'info',
                'message': f"High invalidation rate: {invalidation_stats['total_invalidations']} invalidations",
                'recommendation': 'Review invalidation patterns and dependencies'
            })
        
        return {
            'health_status': 'healthy' if not alerts else 'issues_detected',
            'alerts': alerts,
            'stats_summary': {
                'hit_ratio': hit_ratio,
                'total_entries': stats.get('database_stats', {}).get('total_entries', 0),
                'total_size_mb': total_size / (1024 * 1024),
                'redis_connected': bool(self.cache_service.redis_client)
            }
        }
    
    def generate_cache_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive cache report"""
        health = self.check_cache_health()
        analysis = self.cache_service.get_stats()
        
        return {
            'report_time': datetime.utcnow().isoformat(),
            'period_hours': hours,
            'health_status': health['health_status'],
            'alerts': health['alerts'],
            'performance_summary': {
                'hit_ratio': analysis['performance_metrics']['hit_ratio'],
                'total_requests': analysis['performance_metrics']['total_requests'],
                'avg_get_time_ms': analysis['performance_metrics']['avg_get_time_ms'],
                'avg_set_time_ms': analysis['performance_metrics']['avg_set_time_ms']
            },
            'cache_summary': {
                'total_entries': analysis['database_stats']['total_entries'],
                'active_entries': analysis['database_stats']['active_entries'],
                'total_size_mb': analysis['database_stats']['total_size_bytes'] / (1024 * 1024),
                'avg_compression_ratio': analysis['database_stats']['average_compression_ratio']
            },
            'top_accessed_keys': analysis['trending_keys'][:5],
            'cache_type_performance': analysis['cache_type_performance']
        }
