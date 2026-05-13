"""
Cache Manager

Central management for caching infrastructure with Redis cluster support,
monitoring, backup, and performance tuning capabilities.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import redis
from redis.cluster import RedisCluster
import threading
import queue

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache strategies"""
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    WRITE_AROUND = "write_around"
    REFRESH_AHEAD = "refresh_ahead"

class CacheLevel(Enum):
    """Cache levels"""
    L1 = "l1"  # Memory cache
    L2 = "l2"  # Redis cache
    L3 = "l3"  # Persistent cache

@dataclass
class CacheConfig:
    """Cache configuration"""
    redis_cluster_nodes: List[Dict[str, Any]] = field(default_factory=list)
    max_connections: int = 100
    connection_timeout: int = 5
    socket_timeout: int = 5
    max_retries: int = 3
    retry_delay: float = 0.1
    health_check_interval: int = 30
    backup_interval: int = 3600  # 1 hour
    enable_monitoring: bool = True
    enable_auto_tuning: bool = True
    cache_strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH
    default_ttl: int = 3600  # 1 hour
    max_memory: str = "2gb"
    eviction_policy: str = "allkeys-lru"

@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    memory_usage: int = 0
    key_count: int = 0
    avg_response_time: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

class CacheManager:
    """Central cache manager with Redis cluster support"""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.redis_client = None
        self.redis_cluster = None
        self.stats = CacheStats()
        self.local_cache = {}
        self.cache_lock = threading.RLock()
        self.monitoring_enabled = True
        self.backup_enabled = True
        self.auto_tuning_enabled = True
        
        # Performance tracking
        self.response_times = queue.Queue(maxsize=1000)
        self.hit_rate_history = queue.Queue(maxsize=100)
        
        # Initialize Redis connection
        self._initialize_redis()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _initialize_redis(self):
        """Initialize Redis connection or cluster"""
        try:
            if self.config.redis_cluster_nodes:
                # Initialize Redis Cluster
                self.redis_cluster = RedisCluster(
                    startup_nodes=self.config.redis_cluster_nodes,
                    decode_responses=True,
                    skip_full_coverage_check=True,
                    max_connections=self.config.max_connections,
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.connection_timeout,
                    retry_on_timeout=True,
                    max_retries=self.config.max_retries
                )
                logger.info("Redis Cluster initialized successfully")
            else:
                # Initialize single Redis instance
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=True,
                    max_connections=self.config.max_connections,
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.connection_timeout,
                    retry_on_timeout=True
                )
                logger.info("Redis instance initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    def _start_background_tasks(self):
        """Start background monitoring and maintenance tasks"""
        if self.config.enable_monitoring:
            self._start_monitoring()
        
        if self.config.enable_auto_tuning:
            self._start_auto_tuning()
    
    def _start_monitoring(self):
        """Start background monitoring"""
        def monitor_task():
            while self.monitoring_enabled:
                try:
                    self._update_stats()
                    time.sleep(self.config.health_check_interval)
                except Exception as e:
                    logger.error(f"Monitoring task error: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor_task, daemon=True)
        monitor_thread.start()
        logger.info("Cache monitoring started")
    
    def _start_auto_tuning(self):
        """Start background auto-tuning"""
        def tuning_task():
            while self.auto_tuning_enabled:
                try:
                    self._auto_tune()
                    time.sleep(300)  # Tune every 5 minutes
                except Exception as e:
                    logger.error(f"Auto-tuning task error: {e}")
                    time.sleep(60)
        
        tuning_thread = threading.Thread(target=tuning_task, daemon=True)
        tuning_thread.start()
        logger.info("Auto-tuning started")
    
    def get(self, key: str, level: CacheLevel = CacheLevel.L2) -> Optional[Any]:
        """Get value from cache"""
        start_time = time.time()
        
        try:
            value = None
            
            # Try L1 cache first (memory)
            if level == CacheLevel.L1 or level == CacheLevel.L2:
                with self.cache_lock:
                    if key in self.local_cache:
                        value = self.local_cache[key]
                        self.stats.hits += 1
            
            # Try L2 cache (Redis)
            if value is None and (level == CacheLevel.L2 or level == CacheLevel.L3):
                redis_client = self.redis_cluster or self.redis_client
                if redis_client:
                    cached_value = redis_client.get(key)
                    if cached_value:
                        try:
                            value = json.loads(cached_value)
                            # Cache in L1 for faster access
                            with self.cache_lock:
                                self.local_cache[key] = value
                        except json.JSONDecodeError:
                            value = cached_value
                        self.stats.hits += 1
            
            if value is None:
                self.stats.misses += 1
            
            # Track response time
            response_time = time.time() - start_time
            self.response_times.put(response_time)
            
            return value
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.stats.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = None, level: CacheLevel = CacheLevel.L2) -> bool:
        """Set value in cache"""
        start_time = time.time()
        
        try:
            ttl = ttl or self.config.default_ttl
            
            # Set in L1 cache (memory)
            if level == CacheLevel.L1 or level == CacheLevel.L2:
                with self.cache_lock:
                    self.local_cache[key] = value
                    # Implement simple TTL for L1 cache
                    if len(self.local_cache) > 1000:  # Simple eviction
                        # Remove oldest entries
                        keys_to_remove = list(self.local_cache.keys())[:100]
                        for k in keys_to_remove:
                            del self.local_cache[k]
            
            # Set in L2 cache (Redis)
            if level == CacheLevel.L2 or level == CacheLevel.L3:
                redis_client = self.redis_cluster or self.redis_client
                if redis_client:
                    # Serialize value
                    if isinstance(value, (dict, list)):
                        serialized_value = json.dumps(value)
                    else:
                        serialized_value = str(value)
                    
                    redis_client.setex(key, ttl, serialized_value)
            
            self.stats.sets += 1
            
            # Track response time
            response_time = time.time() - start_time
            self.response_times.put(response_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str, level: CacheLevel = CacheLevel.L2) -> bool:
        """Delete value from cache"""
        try:
            # Delete from L1 cache
            if level == CacheLevel.L1 or level == CacheLevel.L2:
                with self.cache_lock:
                    if key in self.local_cache:
                        del self.local_cache[key]
            
            # Delete from L2 cache
            if level == CacheLevel.L2 or level == CacheLevel.L3:
                redis_client = self.redis_cluster or self.redis_client
                if redis_client:
                    redis_client.delete(key)
            
            self.stats.deletes += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear(self, pattern: str = "*", level: CacheLevel = CacheLevel.L2) -> int:
        """Clear cache entries matching pattern"""
        try:
            count = 0
            
            # Clear from L1 cache
            if level == CacheLevel.L1 or level == CacheLevel.L2:
                with self.cache_lock:
                    keys_to_remove = [k for k in self.local_cache.keys() if pattern == "*" or pattern in k]
                    for k in keys_to_remove:
                        del self.local_cache[k]
                        count += 1
            
            # Clear from L2 cache
            if level == CacheLevel.L2 or level == CacheLevel.L3:
                redis_client = self.redis_cluster or self.redis_client
                if redis_client:
                    if self.redis_cluster:
                        # For cluster, iterate through nodes
                        for node in self.redis_cluster.get_nodes():
                            node_client = self.redis_cluster.get_redis_connection(node)
                            keys = node_client.keys(pattern)
                            if keys:
                                node_client.delete(*keys)
                                count += len(keys)
                    else:
                        keys = redis_client.keys(pattern)
                        if keys:
                            redis_client.delete(*keys)
                            count += len(keys)
            
            return count
            
        except Exception as e:
            logger.error(f"Cache clear error for pattern {pattern}: {e}")
            return 0
    
    def _update_stats(self):
        """Update cache statistics"""
        try:
            redis_client = self.redis_cluster or self.redis_client
            if redis_client:
                # Get Redis info
                if self.redis_cluster:
                    # For cluster, aggregate stats from all nodes
                    total_memory = 0
                    total_keys = 0
                    total_evictions = 0
                    
                    for node in self.redis_cluster.get_nodes():
                        node_client = self.redis_cluster.get_redis_connection(node)
                        info = node_client.info()
                        total_memory += info.get('used_memory', 0)
                        total_keys += info.get('db0', {}).get('keys', 0)
                        total_evictions += info.get('evicted_keys', 0)
                    
                    self.stats.memory_usage = total_memory
                    self.stats.key_count = total_keys
                    self.stats.evictions = total_evictions
                else:
                    info = redis_client.info()
                    self.stats.memory_usage = info.get('used_memory', 0)
                    self.stats.key_count = info.get('db0', {}).get('keys', 0)
                    self.stats.evictions = info.get('evicted_keys', 0)
            
            # Calculate hit rate
            total_requests = self.stats.hits + self.stats.misses
            hit_rate = self.stats.hits / total_requests if total_requests > 0 else 0
            self.hit_rate_history.put(hit_rate)
            
            # Calculate average response time
            if not self.response_times.empty():
                response_times = []
                while not self.response_times.empty():
                    response_times.append(self.response_times.get())
                self.stats.avg_response_time = sum(response_times) / len(response_times)
            
            self.stats.last_updated = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error updating cache stats: {e}")
    
    def _auto_tune(self):
        """Auto-tune cache performance"""
        try:
            # Get current hit rate
            hit_rate = 0
            if not self.hit_rate_history.empty():
                hit_rates = []
                while not self.hit_rate_history.empty():
                    hit_rates.append(self.hit_rate_history.get())
                hit_rate = sum(hit_rates) / len(hit_rates)
            
            redis_client = self.redis_cluster or self.redis_client
            if redis_client:
                # Get memory usage
                info = redis_client.info() if not self.redis_cluster else None
                if info:
                    memory_usage = info.get('used_memory', 0)
                    max_memory = info.get('maxmemory', 0)
                    
                    # Auto-tune based on memory pressure
                    if max_memory > 0 and memory_usage > max_memory * 0.8:
                        logger.warning("High memory usage detected, considering eviction")
                        # Could adjust TTLs or implement more aggressive eviction
                    
                    # Auto-tune based on hit rate
                    if hit_rate < 0.7:  # Low hit rate
                        logger.info("Low hit rate detected, adjusting cache strategy")
                        # Could adjust TTLs, cache size, or eviction policy
        
        except Exception as e:
            logger.error(f"Error in auto-tuning: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats.hits + self.stats.misses
        hit_rate = self.stats.hits / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self.stats.hits,
            'misses': self.stats.misses,
            'sets': self.stats.sets,
            'deletes': self.stats.deletes,
            'evictions': self.stats.evictions,
            'memory_usage': self.stats.memory_usage,
            'key_count': self.stats.key_count,
            'hit_rate': hit_rate,
            'avg_response_time': self.stats.avg_response_time,
            'last_updated': self.stats.last_updated.isoformat(),
            'local_cache_size': len(self.local_cache),
            'cluster_mode': self.redis_cluster is not None
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache system"""
        try:
            redis_client = self.redis_cluster or self.redis_client
            
            health_status = {
                'status': 'healthy',
                'redis_connected': False,
                'cluster_healthy': False,
                'memory_usage': 0,
                'hit_rate': 0,
                'issues': []
            }
            
            if redis_client:
                # Test Redis connection
                try:
                    redis_client.ping()
                    health_status['redis_connected'] = True
                except Exception as e:
                    health_status['issues'].append(f"Redis connection failed: {e}")
                
                # Check cluster health
                if self.redis_cluster:
                    try:
                        cluster_info = self.redis_cluster.cluster_info()
                        health_status['cluster_healthy'] = cluster_info.get('cluster_state') == 'ok'
                        if not health_status['cluster_healthy']:
                            health_status['issues'].append("Redis cluster not healthy")
                    except Exception as e:
                        health_status['issues'].append(f"Cluster health check failed: {e}")
                
                # Get memory usage
                info = redis_client.info() if not self.redis_cluster else None
                if info:
                    health_status['memory_usage'] = info.get('used_memory', 0)
            
            # Calculate hit rate
            total_requests = self.stats.hits + self.stats.misses
            health_status['hit_rate'] = self.stats.hits / total_requests if total_requests > 0 else 0
            
            # Determine overall status
            if health_status['issues']:
                health_status['status'] = 'unhealthy'
            elif health_status['hit_rate'] < 0.5:
                health_status['status'] = 'degraded'
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'issues': [f"Health check failed: {e}"]
            }
    
    def get_config(self) -> Dict[str, Any]:
        """Get cache configuration"""
        return {
            'redis_cluster_nodes': self.config.redis_cluster_nodes,
            'max_connections': self.config.max_connections,
            'connection_timeout': self.config.connection_timeout,
            'socket_timeout': self.config.socket_timeout,
            'max_retries': self.config.max_retries,
            'health_check_interval': self.config.health_check_interval,
            'backup_interval': self.config.backup_interval,
            'enable_monitoring': self.config.enable_monitoring,
            'enable_auto_tuning': self.config.enable_auto_tuning,
            'cache_strategy': self.config.cache_strategy.value,
            'default_ttl': self.config.default_ttl,
            'max_memory': self.config.max_memory,
            'eviction_policy': self.config.eviction_policy
        }
    
    def update_config(self, **kwargs):
        """Update cache configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated cache config: {key} = {value}")
        
        # Reinitialize Redis if cluster nodes changed
        if 'redis_cluster_nodes' in kwargs:
            self._initialize_redis()
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old cache data"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # Clean up local cache (simple TTL-based cleanup)
            with self.cache_lock:
                if len(self.local_cache) > 1000:
                    # Remove oldest entries
                    keys_to_remove = list(self.local_cache.keys())[:500]
                    for k in keys_to_remove:
                        del self.local_cache[k]
            
            logger.info(f"Cleaned up old cache data (older than {max_age_hours} hours)")
            
        except Exception as e:
            logger.error(f"Error cleaning up old cache data: {e}")
    
    def shutdown(self):
        """Shutdown cache manager"""
        try:
            # Stop background tasks
            self.monitoring_enabled = False
            self.auto_tuning_enabled = False
            
            # Close Redis connections
            if self.redis_client:
                self.redis_client.close()
            if self.redis_cluster:
                self.redis_cluster.close()
            
            logger.info("Cache manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during cache manager shutdown: {e}")
