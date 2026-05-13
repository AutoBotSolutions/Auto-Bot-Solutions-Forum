"""
Cache Manager
Provides intelligent cache invalidation and warming strategies
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Set, Callable
from threading import Thread, Lock
from collections import defaultdict
import logging
from flask import current_app, g

from .redis_cache import RedisCacheService, CACHE_TTL

logger = logging.getLogger(__name__)

class CacheManager:
    """Intelligent cache manager with invalidation and warming strategies"""
    
    def __init__(self, cache_service: RedisCacheService):
        """Initialize cache manager"""
        self.cache_service = cache_service
        self.invalidation_rules = {}
        self.warming_rules = {}
        self.dependency_graph = defaultdict(set)
        self.cache_stats = defaultdict(int)
        self._lock = Lock()
        
    def register_invalidation_rule(self, pattern: str, invalidator: Callable):
        """Register cache invalidation rule"""
        with self._lock:
            self.invalidation_rules[pattern] = invalidator
            logger.info(f"Registered invalidation rule for pattern: {pattern}")
    
    def register_warming_rule(self, key: str, warmer: Callable, ttl: int = None):
        """Register cache warming rule"""
        with self._lock:
            self.warming_rules[key] = {
                'warmer': warmer,
                'ttl': ttl or CACHE_TTL['MEDIUM'],
                'last_warmed': None
            }
            logger.info(f"Registered warming rule for key: {key}")
    
    def add_dependency(self, child_key: str, parent_key: str):
        """Add cache dependency (child depends on parent)"""
        with self._lock:
            self.dependency_graph[parent_key].add(child_key)
            logger.debug(f"Added dependency: {child_key} depends on {parent_key}")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern"""
        if not self.cache_service.is_available():
            return 0
        
        try:
            # Use Redis pattern matching
            deleted_count = self.cache_service.delete_pattern(f"*{pattern}*")
            
            # Also invalidate dependent keys
            with self._lock:
                for parent_key in list(self.dependency_graph.keys()):
                    if pattern in parent_key:
                        for child_key in self.dependency_graph[parent_key]:
                            self.cache_service.delete(child_key)
                            deleted_count += 1
            
            logger.info(f"Invalidated {deleted_count} cache keys for pattern: {pattern}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error invalidating cache pattern {pattern}: {e}")
            return 0
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate cache keys by tag"""
        # Tags are stored as separate keys with prefix "tag:{tag}"
        tag_key = f"tag:{tag}"
        cached_keys = self.cache_service.get(tag_key)
        
        if cached_keys:
            keys_to_invalidate = cached_keys if isinstance(cached_keys, list) else [cached_keys]
            deleted_count = 0
            
            for key in keys_to_invalidate:
                if self.cache_service.delete(key):
                    deleted_count += 1
            
            # Delete the tag key itself
            self.cache_service.delete(tag_key)
            
            logger.info(f"Invalidated {deleted_count} cache keys for tag: {tag}")
            return deleted_count
        
        return 0
    
    def invalidate_by_user(self, user_id: int) -> int:
        """Invalidate all cache keys for a specific user"""
        pattern = f"user:{user_id}:*"
        return self.invalidate_pattern(pattern)
    
    def invalidate_by_object(self, object_type: str, object_id: int) -> int:
        """Invalidate cache keys for a specific object"""
        pattern = f"{object_type}:{object_id}:*"
        return self.invalidate_pattern(pattern)
    
    def warm_cache(self, key: str = None, force: bool = False) -> int:
        """Warm cache with pre-defined rules"""
        warmed_count = 0
        
        with self._lock:
            if key:
                # Warm specific key
                if key in self.warming_rules:
                    rule = self.warming_rules[key]
                    if force or self._should_warm(rule):
                        if self._warm_key(key, rule):
                            warmed_count += 1
            else:
                # Warm all keys according to rules
                for key, rule in self.warming_rules.items():
                    if force or self._should_warm(rule):
                        if self._warm_key(key, rule):
                            warmed_count += 1
        
        logger.info(f"Warmed {warmed_count} cache keys")
        return warmed_count
    
    def _should_warm(self, rule: Dict[str, Any]) -> bool:
        """Check if cache key should be warmed"""
        last_warmed = rule.get('last_warmed')
        
        if not last_warmed:
            return True
        
        # Check if enough time has passed (half of TTL)
        ttl = rule.get('ttl', CACHE_TTL['MEDIUM'])
        warm_interval = ttl // 2
        
        return (datetime.utcnow() - last_warmed).total_seconds() > warm_interval
    
    def _warm_key(self, key: str, rule: Dict[str, Any]) -> bool:
        """Warm a specific cache key"""
        try:
            warmer = rule['warmer']
            ttl = rule.get('ttl', CACHE_TTL['MEDIUM'])
            
            # Execute warmer function
            data = warmer()
            
            if data is not None:
                # Cache the data
                self.cache_service.set(key, data, ttl)
                
                # Update rule
                rule['last_warmed'] = datetime.utcnow()
                
                logger.debug(f"Warmed cache key: {key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error warming cache key {key}: {e}")
            return False
    
    def set_with_tags(self, key: str, value: Any, tags: List[str], ttl: int = None):
        """Set cache value with tags for easy invalidation"""
        # Set the main cache entry
        self.cache_service.set(key, value, ttl)
        
        # Update tag mappings
        for tag in tags:
            tag_key = f"tag:{tag}"
            existing_keys = self.cache_service.get(tag_key) or []
            
            if key not in existing_keys:
                existing_keys.append(key)
                self.cache_service.set(tag_key, existing_keys, ttl * 2)  # Tags last longer
    
    def get_with_stats(self, key: str) -> tuple[Any, Dict[str, Any]]:
        """Get cache value with statistics"""
        start_time = datetime.utcnow()
        value = self.cache_service.get(key)
        end_time = datetime.utcnow()
        
        # Update statistics
        with self._lock:
            self.cache_stats['requests'] += 1
            if value is not None:
                self.cache_stats['hits'] += 1
            else:
                self.cache_stats['misses'] += 1
        
        stats = {
            'hit': value is not None,
            'response_time_ms': (end_time - start_time).total_seconds() * 1000,
            'cache_available': self.cache_service.is_available()
        }
        
        return value, stats
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.cache_stats.get('requests', 0)
            hits = self.cache_stats.get('hits', 0)
            misses = self.cache_stats.get('misses', 0)
            
            hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_requests': total_requests,
                'hits': hits,
                'misses': misses,
                'hit_rate_percent': round(hit_rate, 2),
                'cache_available': self.cache_service.is_available(),
                'invalidation_rules': len(self.invalidation_rules),
                'warming_rules': len(self.warming_rules),
                'dependencies': len(self.dependency_graph)
            }
    
    def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries"""
        if not self.cache_service.is_available():
            return 0
        
        try:
            # Use Redis to clean up expired keys automatically
            # This is handled by Redis TTL, but we can clean up tag mappings
            pattern = "tag:*"
            keys = self.cache_service.redis_client.keys(self.cache_service._make_key(pattern))
            
            cleaned_count = 0
            for key in keys:
                key_str = key.decode('utf-8')
                tag_name = key_str.replace(self.cache_service.key_prefix + "tag:", "")
                
                # Get cached keys for this tag
                cached_keys = self.cache_service.get(f"tag:{tag_name}")
                if cached_keys:
                    # Check if cached keys still exist
                    valid_keys = []
                    for cached_key in cached_keys:
                        if self.cache_service.exists(cached_key):
                            valid_keys.append(cached_key)
                    
                    if valid_keys:
                        # Update tag with valid keys only
                        self.cache_service.set(f"tag:{tag_name}", valid_keys)
                    else:
                        # Remove empty tag
                        self.cache_service.delete(f"tag:{tag_name}")
                
                cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} tag mappings")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache entries: {e}")
            return 0
    
    def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache based on usage patterns"""
        optimization_results = {
            'actions_taken': [],
            'recommendations': []
        }
        
        try:
            # Get cache statistics
            stats = self.get_cache_stats()
            
            # Analyze hit rate
            if stats['hit_rate_percent'] < 50:
                optimization_results['recommendations'].append(
                    "Low cache hit rate. Consider adjusting TTL values or warming strategies."
                )
            
            # Clean up expired entries
            cleaned_count = self.cleanup_expired_entries()
            if cleaned_count > 0:
                optimization_results['actions_taken'].append(
                    f"Cleaned up {cleaned_count} expired tag mappings"
                )
            
            # Check Redis memory usage
            redis_info = self.cache_service.get_info()
            if redis_info.get('used_memory'):
                memory_mb = redis_info['used_memory'] / (1024 * 1024)
                if memory_mb > 500:  # 500MB threshold
                    optimization_results['recommendations'].append(
                        f"High memory usage: {memory_mb:.2f}MB. Consider reducing TTL or implementing cache eviction."
                    )
            
            # Warm cache if hit rate is low
            if stats['hit_rate_percent'] < 70:
                warmed_count = self.warm_cache(force=True)
                if warmed_count > 0:
                    optimization_results['actions_taken'].append(
                        f"Warmed {warmed_count} cache keys to improve hit rate"
                    )
            
            logger.info("Cache optimization completed")
            
        except Exception as e:
            logger.error(f"Error optimizing cache: {e}")
            optimization_results['error'] = str(e)
        
        return optimization_results
    
    def export_cache_config(self) -> Dict[str, Any]:
        """Export cache configuration for backup/restore"""
        return {
            'invalidation_rules': {
                pattern: str(rule.__name__) if callable(rule) else str(rule)
                for pattern, rule in self.invalidation_rules.items()
            },
            'warming_rules': {
                key: {
                    'warmer': str(rule['warmer'].__name__) if callable(rule['warmer']) else str(rule['warmer']),
                    'ttl': rule['ttl'],
                    'last_warmed': rule['last_warmed'].isoformat() if rule['last_warmed'] else None
                }
                for key, rule in self.warming_rules.items()
            },
            'dependency_graph': {
                parent: list(children)
                for parent, children in self.dependency_graph.items()
            },
            'cache_stats': dict(self.cache_stats)
        }
    
    def reset_stats(self):
        """Reset cache statistics"""
        with self._lock:
            self.cache_stats.clear()
            logger.info("Cache statistics reset")


# Predefined invalidation rules

def invalidate_user_cache(user_id: int, cache_manager: CacheManager):
    """Invalidate all cache entries for a user"""
    return cache_manager.invalidate_by_user(user_id)


def invalidate_post_cache(post_id: int, cache_manager: CacheManager):
    """Invalidate cache entries for a post"""
    # Invalidate post-specific caches
    cache_manager.invalidate_by_object('post', post_id)
    
    # Invalidate post list caches
    cache_manager.invalidate_pattern('posts:list')
    
    # Invalidate user post caches
    cache_manager.invalidate_pattern('user:posts')


def invalidate_comment_cache(comment_id: int, cache_manager: CacheManager):
    """Invalidate cache entries for a comment"""
    # Invalidate comment-specific caches
    cache_manager.invalidate_by_object('comment', comment_id)
    
    # Invalidate post comments cache
    cache_manager.invalidate_pattern('post:comments')


def invalidate_forum_cache(cache_manager: CacheManager):
    """Invalidate general forum caches"""
    patterns = [
        'posts:list',
        'users:list',
        'categories:list',
        'tags:list',
        'search:*'
    ]
    
    for pattern in patterns:
        cache_manager.invalidate_pattern(pattern)


# Predefined warming functions

def warm_popular_posts():
    """Warm cache with popular posts"""
    from app.models import Post
    
    posts = Post.query.filter_by(is_active=True).order_by(Post.upvotes.desc()).limit(20).all()
    
    return [{
        'id': post.id,
        'title': post.title,
        'upvotes': post.upvotes,
        'created_at': post.created_at.isoformat(),
        'author': post.author.username
    } for post in posts]


def warm_active_users():
    """Warm cache with active users"""
    from app.models import User
    
    users = User.query.filter_by(is_active=True).order_by(User.last_login.desc()).limit(50).all()
    
    return [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'post_count': len(user.posts) if hasattr(user, 'posts') else 0
    } for user in users]


def warm_forum_stats():
    """Warm cache with forum statistics"""
    from app.models import Post, User
    
    stats = {
        'total_posts': Post.query.count(),
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'posts_today': Post.query.filter(
            Post.created_at >= datetime.utcnow().date()
        ).count()
    }
    
    return stats


def initialize_cache_manager(app):
    """Initialize cache manager with predefined rules"""
    cache_service = RedisCacheService()
    cache_manager = CacheManager(cache_service)
    
    # Register invalidation rules
    cache_manager.register_invalidation_rule('user:*', invalidate_user_cache)
    cache_manager.register_invalidation_rule('post:*', invalidate_post_cache)
    cache_manager.register_invalidation_rule('comment:*', invalidate_comment_cache)
    cache_manager.register_invalidation_rule('forum:*', invalidate_forum_cache)
    
    # Register warming rules
    cache_manager.register_warming_rule('popular_posts', warm_popular_posts, CACHE_TTL['MEDIUM'])
    cache_manager.register_warming_rule('active_users', warm_active_users, CACHE_TTL['LONG'])
    cache_manager.register_warming_rule('forum_stats', warm_forum_stats, CACHE_TTL['SHORT'])
    
    # Add dependencies
    cache_manager.add_dependency('user:posts', 'user:*')
    cache_manager.add_dependency('post:comments', 'post:*')
    cache_manager.add_dependency('search:results', 'posts:list')
    
    # Store in app context
    app.extensions['cache_manager'] = cache_manager
    app.extensions['cache_service'] = cache_service
    
    logger.info("Cache manager initialized with predefined rules")
    
    return cache_manager
