"""
Notification Search Performance Optimization

This module provides advanced search optimization including:
- Query optimization and indexing
- Search result caching
- Performance monitoring
- Search analytics
- Intelligent query routing
"""

import time
import json
import logging
import hashlib
import re
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from functools import lru_cache
import redis
from sqlalchemy import text, and_, or_, func
from sqlalchemy.orm import joinedload

from app.config.notification_config import get_notification_config
from app.models import Notification, AdminNotification, User

logger = logging.getLogger(__name__)

@dataclass
class SearchMetrics:
    """Search performance metrics"""
    query_count: int = 0
    average_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    result_count: int = 0
    error_count: int = 0
    popular_queries: List[str] = None
    slow_queries: List[Dict] = None
    
    def __post_init__(self):
        if self.popular_queries is None:
            self.popular_queries = []
        if self.slow_queries is None:
            self.slow_queries = []

class LRUCache:
    """Thread-safe LRU cache implementation"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # Check TTL
            if time.time() - self.timestamps[key] > self.ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None
            
            # Move to end (most recently used)
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        with self.lock:
            # Remove if exists
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]
            
            # Remove oldest if at capacity
            elif len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            # Add new item
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        """Get cache size"""
        return len(self.cache)

class SearchOptimizer:
    """Advanced search optimization system"""
    
    def __init__(self):
        self.config = get_notification_config()
        self.redis_client = None
        self.metrics = SearchMetrics()
        
        # Query optimization
        self.query_cache = {}
        self.index_suggestions = []
        self.query_patterns = defaultdict(int)
        
        # Performance tracking
        self.query_times = deque(maxlen=1000)
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Search analytics
        self.search_analytics = SearchAnalytics()
        
        self._setup_redis()
        self._initialize_optimizations()
    
    def _setup_redis(self):
        """Setup Redis connection for caching"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                db=self.config.redis_cache_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            logger.info("Redis connection established for search optimizer")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
    
    def _initialize_optimizations(self):
        """Initialize search optimizations"""
        # Define optimal indexes
        self.index_suggestions = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_search_gin ON notifications USING GIN(to_tsvector('english', content || ' ' || COALESCE(link, '')))",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_user_type_date ON notifications(user_id, type, created_at DESC)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_search_composite ON notifications(user_id, is_read, priority, created_at DESC)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_admin_notifications_search ON admin_notifications(title, message, notification_type)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_fulltext ON notifications USING GIN(to_tsvector('english', content)) WHERE content IS NOT NULL"
        ]
    
    def optimize_search_query(self, user_id: int, search_params: Dict) -> Dict:
        """Optimize search query with intelligent routing"""
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(user_id, search_params)
            
            # Check cache first
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.cache_hits += 1
                self._update_metrics(start_time, True)
                return cached_result
            
            self.cache_misses += 1
            
            # Optimize query based on parameters
            optimized_query = self._optimize_query_parameters(search_params)
            
            # Execute optimized search
            results = self._execute_optimized_search(user_id, optimized_query)
            
            # Cache results
            self._cache_result(cache_key, results)
            
            # Track analytics
            self._track_search_analytics(user_id, search_params, results)
            
            self._update_metrics(start_time, False)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in optimized search: {str(e)}")
            self.metrics.error_count += 1
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def _generate_cache_key(self, user_id: int, search_params: Dict) -> str:
        """Generate cache key for search query"""
        # Create normalized key string
        key_data = {
            'user_id': user_id,
            'query': search_params.get('search_query', '').lower().strip(),
            'types': sorted(search_params.get('types', [])),
            'priorities': sorted(search_params.get('priorities', [])),
            'date_range': search_params.get('date_range'),
            'is_read': search_params.get('is_read'),
            'page': search_params.get('page', 1),
            'per_page': min(search_params.get('per_page', 20), 100)  # Limit cache variations
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"search_cache:{key_hash}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached search result"""
        try:
            if not self.redis_client:
                return None
            
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                result = json.loads(cached_data)
                # Check if cache is still valid
                cache_time = result.get('cached_at', 0)
                if time.time() - cache_time < 300:  # 5 minute cache
                    return result
                else:
                    # Remove expired cache
                    self.redis_client.delete(cache_key)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached result: {str(e)}")
            return None
    
    def _cache_result(self, cache_key: str, result: Dict):
        """Cache search result"""
        try:
            if not self.redis_client:
                return
            
            # Add cache metadata
            cached_result = result.copy()
            cached_result['cached_at'] = time.time()
            cached_result['from_cache'] = False
            
            # Cache with expiration
            self.redis_client.setex(
                cache_key,
                300,  # 5 minutes
                json.dumps(cached_result)
            )
            
        except Exception as e:
            logger.error(f"Error caching result: {str(e)}")
    
    def _optimize_query_parameters(self, search_params: Dict) -> Dict:
        """Optimize query parameters for better performance"""
        optimized = search_params.copy()
        
        # Normalize search query
        if 'search_query' in optimized:
            query = optimized['search_query']
            
            # Remove special characters and normalize
            normalized_query = re.sub(r'[^\w\s]', ' ', query.lower())
            normalized_query = re.sub(r'\s+', ' ', normalized_query).strip()
            
            optimized['search_query'] = normalized_query
            
            # Track query patterns
            self.query_patterns[normalized_query] += 1
        
        # Optimize pagination
        if 'per_page' in optimized:
            per_page = optimized['per_page']
            # Limit per_page to reasonable values
            optimized['per_page'] = min(max(per_page, 1), 100)
        
        # Optimize date range
        if 'date_range' in optimized:
            date_range = optimized['date_range']
            if date_range == 'custom':
                # Validate custom dates
                start_date = optimized.get('start_date')
                end_date = optimized.get('end_date')
                
                if start_date and end_date:
                    # Ensure reasonable date range
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    
                    # Limit to 1 year range
                    if end_dt - start_dt > timedelta(days=365):
                        optimized['end_date'] = (start_dt + timedelta(days=365)).isoformat()
        
        return optimized
    
    def _execute_optimized_search(self, user_id: int, search_params: Dict) -> Dict:
        """Execute optimized search query"""
        try:
            # Build base query
            query = Notification.query.filter(Notification.user_id == user_id)
            
            # Apply filters efficiently
            query = self._apply_search_filters(query, search_params)
            
            # Apply text search efficiently
            if search_params.get('search_query'):
                query = self._apply_text_search(query, search_params['search_query'])
            
            # Get total count efficiently
            total_count = query.count()
            
            # Apply pagination
            page = search_params.get('page', 1)
            per_page = search_params.get('per_page', 20)
            offset = (page - 1) * per_page
            
            # Get results with optimized ordering
            results = query.order_by(
                Notification.priority.desc(),
                Notification.created_at.desc()
            ).offset(offset).limit(per_page).all()
            
            # Format results
            formatted_results = [
                {
                    'id': notif.id,
                    'type': notif.type,
                    'content': notif.content,
                    'link': notif.link,
                    'is_read': notif.is_read,
                    'created_at': notif.created_at.isoformat(),
                    'priority': getattr(notif, 'priority', 'normal')
                }
                for notif in results
            ]
            
            return {
                'success': True,
                'results': formatted_results,
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page,
                'from_cache': False
            }
            
        except Exception as e:
            logger.error(f"Error executing optimized search: {str(e)}")
            raise
    
    def _apply_search_filters(self, query, search_params: Dict):
        """Apply search filters efficiently"""
        # Type filter - use IN clause for better performance
        if search_params.get('types'):
            query = query.filter(Notification.type.in_(search_params['types']))
        
        # Priority filter
        if search_params.get('priorities'):
            query = query.filter(getattr(Notification, 'priority', 'normal').in_(search_params['priorities']))
        
        # Read status filter
        if 'is_read' in search_params:
            query = query.filter(Notification.is_read == search_params['is_read'])
        
        # Date range filter
        date_range = search_params.get('date_range')
        if date_range:
            now = datetime.utcnow()
            
            if date_range == 'last_24_hours':
                start_date = now - timedelta(hours=24)
                query = query.filter(Notification.created_at >= start_date)
            elif date_range == 'last_7_days':
                start_date = now - timedelta(days=7)
                query = query.filter(Notification.created_at >= start_date)
            elif date_range == 'last_30_days':
                start_date = now - timedelta(days=30)
                query = query.filter(Notification.created_at >= start_date)
            elif date_range == 'custom':
                start_date = search_params.get('start_date')
                end_date = search_params.get('end_date')
                
                if start_date:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.filter(Notification.created_at >= start_dt)
                
                if end_date:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    query = query.filter(Notification.created_at <= end_dt)
        
        return query
    
    def _apply_text_search(self, query, search_query: str):
        """Apply full-text search efficiently"""
        try:
            # Use PostgreSQL full-text search if available
            if self._supports_fulltext_search():
                # Create tsvector for search
                search_vector = func.to_tsvector('english', Notification.content)
                search_query_ts = func.plainto_tsquery('english', search_query)
                
                query = query.filter(search_vector.op('@@')(search_query_ts))
                
                # Add ranking for relevance
                query = query.add_columns(
                    func.ts_rank(search_vector, search_query_ts).label('relevance')
                )
            else:
                # Fallback to ILIKE search
                search_pattern = f"%{search_query}%"
                query = query.filter(
                    or_(
                        Notification.content.ilike(search_pattern),
                        Notification.link.ilike(search_pattern)
                    )
                )
        
        except Exception as e:
            logger.error(f"Error applying text search: {str(e)}")
            # Fallback to basic search
            search_pattern = f"%{search_query}%"
            query = query.filter(Notification.content.ilike(search_pattern))
        
        return query
    
    def _supports_fulltext_search(self) -> bool:
        """Check if database supports full-text search"""
        try:
            # Test PostgreSQL full-text search support
            result = self.db.session.execute(text("SELECT to_tsvector('english', 'test')"))
            return True
        except:
            return False
    
    def _track_search_analytics(self, user_id: int, search_params: Dict, results: Dict):
        """Track search analytics"""
        try:
            analytics_data = {
                'user_id': user_id,
                'search_query': search_params.get('search_query', ''),
                'filters': {
                    'types': search_params.get('types', []),
                    'priorities': search_params.get('priorities', []),
                    'date_range': search_params.get('date_range'),
                    'is_read': search_params.get('is_read')
                },
                'results_count': results.get('total_count', 0),
                'response_time': time.time(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.search_analytics.record_search(analytics_data)
            
        except Exception as e:
            logger.error(f"Error tracking search analytics: {str(e)}")
    
    def _update_metrics(self, start_time: float, from_cache: bool):
        """Update search performance metrics"""
        response_time = time.time() - start_time
        self.query_times.append(response_time)
        
        # Update average response time
        if self.query_times:
            self.metrics.average_response_time = sum(self.query_times) / len(self.query_times)
        
        # Update cache hit rate
        total_requests = self.cache_hits + self.cache_misses
        if total_requests > 0:
            self.metrics.cache_hit_rate = self.cache_hits / total_requests
        
        # Update query count
        self.metrics.query_count += 1
        
        # Track slow queries
        if response_time > 1.0:  # Queries over 1 second
            slow_query = {
                'response_time': response_time,
                'timestamp': datetime.utcnow().isoformat(),
                'from_cache': from_cache
            }
            self.metrics.slow_queries.append(slow_query)
            
            # Keep only recent slow queries
            if len(self.metrics.slow_queries) > 50:
                self.metrics.slow_queries.pop(0)
    
    def get_search_performance_report(self) -> Dict:
        """Get comprehensive search performance report"""
        try:
            # Get popular queries
            popular_queries = sorted(
                self.query_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Get cache statistics
            cache_stats = {
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'hit_rate': self.metrics.cache_hit_rate
            }
            
            # Get performance percentiles
            if self.query_times:
                sorted_times = sorted(list(self.query_times))
                percentiles = {
                    'p50': sorted_times[len(sorted_times) // 2],
                    'p95': sorted_times[int(len(sorted_times) * 0.95)],
                    'p99': sorted_times[int(len(sorted_times) * 0.99)]
                }
            else:
                percentiles = {'p50': 0, 'p95': 0, 'p99': 0}
            
            return {
                'metrics': asdict(self.metrics),
                'popular_queries': popular_queries,
                'cache_stats': cache_stats,
                'response_time_percentiles': percentiles,
                'index_suggestions': self.index_suggestions,
                'search_analytics': self.search_analytics.get_summary()
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {'error': str(e)}
    
    def create_optimized_indexes(self):
        """Create optimized database indexes"""
        try:
            from app import db
            
            for index_sql in self.index_suggestions:
                try:
                    db.session.execute(text(index_sql))
                    db.session.commit()
                    logger.info(f"Created index: {index_sql}")
                except Exception as e:
                    logger.warning(f"Index creation failed: {e}")
                    db.session.rollback()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
            return False
    
    def clear_search_cache(self, pattern: str = "search_cache:*"):
        """Clear search cache"""
        try:
            if not self.redis_client:
                return False
            
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} search cache entries")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error clearing search cache: {str(e)}")
            return False
    
    def get_cache_statistics(self) -> Dict:
        """Get cache performance statistics"""
        try:
            if not self.redis_client:
                return {'error': 'Redis not available'}
            
            # Get cache info
            cache_info = self.redis_client.info('memory')
            
            # Count cached items
            cache_keys = self.redis_client.keys('search_cache:*')
            
            return {
                'cached_items': len(cache_keys),
                'cache_memory_usage': cache_info.get('used_memory', 0),
                'cache_hit_rate': self.metrics.cache_hit_rate,
                'total_requests': self.cache_hits + self.cache_misses,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses
            }
            
        except Exception as e:
            logger.error(f"Error getting cache statistics: {str(e)}")
            return {'error': str(e)}

class SearchAnalytics:
    """Search analytics and tracking"""
    
    def __init__(self):
        self.search_history = deque(maxlen=10000)
        self.query_frequency = defaultdict(int)
        self.user_search_patterns = defaultdict(list)
        self.popular_filters = defaultdict(int)
    
    def record_search(self, analytics_data: Dict):
        """Record search analytics data"""
        try:
            self.search_history.append(analytics_data)
            
            # Track query frequency
            query = analytics_data['search_query']
            if query:
                self.query_frequency[query] += 1
            
            # Track user search patterns
            user_id = analytics_data['user_id']
            self.user_search_patterns[user_id].append(analytics_data)
            
            # Track popular filters
            filters = analytics_data.get('filters', {})
            for filter_name, filter_value in filters.items():
                if filter_value:
                    self.popular_filters[filter_name] += 1
            
        except Exception as e:
            logger.error(f"Error recording search analytics: {str(e)}")
    
    def get_summary(self) -> Dict:
        """Get search analytics summary"""
        try:
            # Popular queries
            popular_queries = sorted(
                self.query_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Popular filters
            popular_filters = sorted(
                self.popular_filters.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Search statistics
            total_searches = len(self.search_history)
            if total_searches > 0:
                avg_results = sum(s['results_count'] for s in self.search_history) / total_searches
                searches_with_results = sum(1 for s in self.search_history if s['results_count'] > 0)
                success_rate = searches_with_results / total_searches
            else:
                avg_results = 0
                success_rate = 0
            
            return {
                'total_searches': total_searches,
                'average_results': avg_results,
                'success_rate': success_rate,
                'popular_queries': popular_queries,
                'popular_filters': popular_filters,
                'unique_users': len(self.user_search_patterns)
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics summary: {str(e)}")
            return {'error': str(e)}

# Global search optimizer instance
search_optimizer = SearchOptimizer()
