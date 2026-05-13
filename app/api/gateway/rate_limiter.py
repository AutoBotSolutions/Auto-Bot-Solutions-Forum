"""
Gateway Rate Limiter

Enhanced rate limiting for API gateway with multiple strategies,
sliding windows, and distributed rate limiting.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import time
import redis
import json
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    DISTRIBUTED = "distributed"

class RateLimitType(Enum):
    """Rate limit types"""
    GLOBAL = "global"
    PER_USER = "per_user"
    PER_IP = "per_ip"
    PER_ENDPOINT = "per_endpoint"
    PER_SERVICE = "per_service"

class RateLimiter:
    """Enhanced rate limiter for API gateway"""
    
    def __init__(self, strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
                 redis_client: redis.Redis = None):
        self.strategy = strategy
        self.redis_client = redis_client
        self.local_limits = {}
        self.sliding_windows = defaultdict(deque)
        self.token_buckets = defaultdict(dict)
        self.leaky_buckets = defaultdict(dict)
        self.fixed_windows = defaultdict(dict)
        
    def check_rate_limit(self, key: str, limit: int, window: int, 
                         identifier: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is rate limited"""
        if self.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._check_fixed_window(key, limit, window, identifier)
        elif self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(key, limit, window, identifier)
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(key, limit, window, identifier)
        elif self.strategy == RateLimitStrategy.LEAKY_BUCKET:
            return self._check_leaky_bucket(key, limit, window, identifier)
        elif self.strategy == RateLimitStrategy.DISTRIBUTED:
            return self._check_distributed(key, limit, window, identifier)
        else:
            return True, {"allowed": True, "strategy": self.strategy.value}
    
    def _check_fixed_window(self, key: str, limit: int, window: int, 
                           identifier: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Fixed window rate limiting"""
        current_time = int(time.time())
        window_start = current_time - (current_time % window)
        window_key = f"{key}:{window_start}:{identifier or 'default'}"
        
        # Check Redis first if available
        if self.redis_client:
            try:
                current_count = self.redis_client.get(window_key)
                if current_count is None:
                    # First request in window
                    self.redis_client.setex(window_key, window, 1)
                    return True, {
                        "allowed": True,
                        "count": 1,
                        "limit": limit,
                        "remaining": limit - 1,
                        "reset_time": window_start + window,
                        "strategy": "fixed_window"
                    }
                else:
                    current_count = int(current_count)
                    if current_count >= limit:
                        return False, {
                            "allowed": False,
                            "count": current_count,
                            "limit": limit,
                            "remaining": 0,
                            "reset_time": window_start + window,
                            "strategy": "fixed_window"
                        }
                    else:
                        self.redis_client.incr(window_key)
                        return True, {
                            "allowed": True,
                            "count": current_count + 1,
                            "limit": limit,
                            "remaining": limit - current_count - 1,
                            "reset_time": window_start + window,
                            "strategy": "fixed_window"
                        }
            except Exception as e:
                logger.error(f"Redis error in fixed window rate limiting: {e}")
                # Fall back to local implementation
        
        # Local implementation
        if window_key not in self.fixed_windows:
            self.fixed_windows[window_key] = {
                "count": 0,
                "window_start": window_start
            }
        
        window_data = self.fixed_windows[window_key]
        
        # Reset if window expired
        if current_time >= window_start + window:
            window_data["count"] = 0
            window_data["window_start"] = window_start
        
        if window_data["count"] >= limit:
            return False, {
                "allowed": False,
                "count": window_data["count"],
                "limit": limit,
                "remaining": 0,
                "reset_time": window_start + window,
                "strategy": "fixed_window"
            }
        
        window_data["count"] += 1
        return True, {
            "allowed": True,
            "count": window_data["count"],
            "limit": limit,
            "remaining": limit - window_data["count"],
            "reset_time": window_start + window,
            "strategy": "fixed_window"
        }
    
    def _check_sliding_window(self, key: str, limit: int, window: int, 
                             identifier: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Sliding window rate limiting"""
        current_time = time.time()
        window_key = f"{key}:{identifier or 'default'}"
        
        # Check Redis first if available
        if self.redis_client:
            try:
                # Remove old requests outside the window
                pipeline = self.redis_client.pipeline()
                pipeline.zremrangebyscore(window_key, 0, current_time - window)
                pipeline.zcard(window_key)
                pipeline.zadd(window_key, {str(current_time): current_time})
                pipeline.expire(window_key, window)
                
                results = pipeline.execute()
                current_count = results[1]
                
                if current_count >= limit:
                    return False, {
                        "allowed": False,
                        "count": current_count,
                        "limit": limit,
                        "remaining": 0,
                        "reset_time": current_time + window,
                        "strategy": "sliding_window"
                    }
                
                return True, {
                    "allowed": True,
                    "count": current_count + 1,
                    "limit": limit,
                    "remaining": limit - current_count - 1,
                    "reset_time": current_time + window,
                    "strategy": "sliding_window"
                }
            except Exception as e:
                logger.error(f"Redis error in sliding window rate limiting: {e}")
                # Fall back to local implementation
        
        # Local implementation
        if window_key not in self.sliding_windows:
            self.sliding_windows[window_key] = deque()
        
        window_data = self.sliding_windows[window_key]
        
        # Remove old requests outside the window
        while window_data and window_data[0] < current_time - window:
            window_data.popleft()
        
        if len(window_data) >= limit:
            return False, {
                "allowed": False,
                "count": len(window_data),
                "limit": limit,
                "remaining": 0,
                "reset_time": window_data[0] + window if window_data else current_time + window,
                "strategy": "sliding_window"
            }
        
        window_data.append(current_time)
        return True, {
            "allowed": True,
            "count": len(window_data),
            "limit": limit,
            "remaining": limit - len(window_data),
            "reset_time": current_time + window,
            "strategy": "sliding_window"
        }
    
    def _check_token_bucket(self, key: str, limit: int, window: int, 
                          identifier: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Token bucket rate limiting"""
        current_time = time.time()
        bucket_key = f"{key}:{identifier or 'default'}"
        refill_rate = limit / window  # tokens per second
        
        # Check Redis first if available
        if self.redis_client:
            try:
                # Get current bucket state
                bucket_data = self.redis_client.hgetall(bucket_key)
                
                if not bucket_data:
                    # Initialize bucket
                    bucket_state = {
                        "tokens": limit - 1,
                        "last_refill": current_time,
                        "capacity": limit,
                        "refill_rate": refill_rate
                    }
                    self.redis_client.hset(bucket_key, mapping=bucket_state)
                    self.redis_client.expire(bucket_key, window * 2)
                    
                    return True, {
                        "allowed": True,
                        "tokens": bucket_state["tokens"],
                        "capacity": limit,
                        "refill_rate": refill_rate,
                        "strategy": "token_bucket"
                    }
                
                tokens = float(bucket_data.get("tokens", limit))
                last_refill = float(bucket_data.get("last_refill", current_time))
                
                # Refill tokens
                time_passed = current_time - last_refill
                tokens_to_add = time_passed * refill_rate
                tokens = min(limit, tokens + tokens_to_add)
                
                if tokens < 1:
                    # Update bucket state
                    self.redis_client.hset(bucket_key, {
                        "tokens": tokens,
                        "last_refill": current_time
                    })
                    
                    return False, {
                        "allowed": False,
                        "tokens": tokens,
                        "capacity": limit,
                        "refill_rate": refill_rate,
                        "wait_time": (1 - tokens) / refill_rate,
                        "strategy": "token_bucket"
                    }
                
                # Consume token
                tokens -= 1
                self.redis_client.hset(bucket_key, {
                    "tokens": tokens,
                    "last_refill": current_time
                })
                
                return True, {
                    "allowed": True,
                    "tokens": tokens,
                    "capacity": limit,
                    "refill_rate": refill_rate,
                    "strategy": "token_bucket"
                }
            except Exception as e:
                logger.error(f"Redis error in token bucket rate limiting: {e}")
                # Fall back to local implementation
        
        # Local implementation
        if bucket_key not in self.token_buckets:
            self.token_buckets[bucket_key] = {
                "tokens": limit,
                "last_refill": current_time,
                "capacity": limit,
                "refill_rate": refill_rate
            }
        
        bucket = self.token_buckets[bucket_key]
        
        # Refill tokens
        time_passed = current_time - bucket["last_refill"]
        tokens_to_add = time_passed * bucket["refill_rate"]
        bucket["tokens"] = min(bucket["capacity"], bucket["tokens"] + tokens_to_add)
        bucket["last_refill"] = current_time
        
        if bucket["tokens"] < 1:
            return False, {
                "allowed": False,
                "tokens": bucket["tokens"],
                "capacity": bucket["capacity"],
                "refill_rate": bucket["refill_rate"],
                "wait_time": (1 - bucket["tokens"]) / bucket["refill_rate"],
                "strategy": "token_bucket"
            }
        
        # Consume token
        bucket["tokens"] -= 1
        
        return True, {
            "allowed": True,
            "tokens": bucket["tokens"],
            "capacity": bucket["capacity"],
            "refill_rate": bucket["refill_rate"],
            "strategy": "token_bucket"
        }
    
    def _check_leaky_bucket(self, key: str, limit: int, window: int, 
                           identifier: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Leaky bucket rate limiting"""
        current_time = time.time()
        bucket_key = f"{key}:{identifier or 'default'}"
        leak_rate = limit / window  # requests per second
        
        # Check Redis first if available
        if self.redis_client:
            try:
                # Get current bucket state
                bucket_data = self.redis_client.hgetall(bucket_key)
                
                if not bucket_data:
                    # Initialize bucket
                    bucket_state = {
                        "queue_size": 1,
                        "last_leak": current_time,
                        "max_size": limit,
                        "leak_rate": leak_rate
                    }
                    self.redis_client.hset(bucket_key, mapping=bucket_state)
                    self.redis_client.expire(bucket_key, window * 2)
                    
                    return True, {
                        "allowed": True,
                        "queue_size": 1,
                        "max_size": limit,
                        "leak_rate": leak_rate,
                        "strategy": "leaky_bucket"
                    }
                
                queue_size = float(bucket_data.get("queue_size", 0))
                last_leak = float(bucket_data.get("last_leak", current_time))
                
                # Leak requests
                time_passed = current_time - last_leak
                requests_to_leak = time_passed * leak_rate
                queue_size = max(0, queue_size - requests_to_leak)
                
                if queue_size >= limit:
                    # Update bucket state
                    self.redis_client.hset(bucket_key, {
                        "queue_size": queue_size,
                        "last_leak": current_time
                    })
                    
                    return False, {
                        "allowed": False,
                        "queue_size": queue_size,
                        "max_size": limit,
                        "leak_rate": leak_rate,
                        "wait_time": (queue_size - limit + 1) / leak_rate,
                        "strategy": "leaky_bucket"
                    }
                
                # Add request to queue
                queue_size += 1
                self.redis_client.hset(bucket_key, {
                    "queue_size": queue_size,
                    "last_leak": current_time
                })
                
                return True, {
                    "allowed": True,
                    "queue_size": queue_size,
                    "max_size": limit,
                    "leak_rate": leak_rate,
                    "strategy": "leaky_bucket"
                }
            except Exception as e:
                logger.error(f"Redis error in leaky bucket rate limiting: {e}")
                # Fall back to local implementation
        
        # Local implementation
        if bucket_key not in self.leaky_buckets:
            self.leaky_buckets[bucket_key] = {
                "queue_size": 0,
                "last_leak": current_time,
                "max_size": limit,
                "leak_rate": leak_rate
            }
        
        bucket = self.leaky_buckets[bucket_key]
        
        # Leak requests
        time_passed = current_time - bucket["last_leak"]
        requests_to_leak = time_passed * bucket["leak_rate"]
        bucket["queue_size"] = max(0, bucket["queue_size"] - requests_to_leak)
        bucket["last_leak"] = current_time
        
        if bucket["queue_size"] >= bucket["max_size"]:
            return False, {
                "allowed": False,
                "queue_size": bucket["queue_size"],
                "max_size": bucket["max_size"],
                "leak_rate": bucket["leak_rate"],
                "wait_time": (bucket["queue_size"] - bucket["max_size"] + 1) / bucket["leak_rate"],
                "strategy": "leaky_bucket"
            }
        
        # Add request to queue
        bucket["queue_size"] += 1
        
        return True, {
            "allowed": True,
            "queue_size": bucket["queue_size"],
            "max_size": bucket["max_size"],
            "leak_rate": bucket["leak_rate"],
            "strategy": "leaky_bucket"
        }
    
    def _check_distributed(self, key: str, limit: int, window: int, 
                          identifier: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Distributed rate limiting using Redis"""
        if not self.redis_client:
            # Fall back to sliding window
            return self._check_sliding_window(key, limit, window, identifier)
        
        current_time = time.time()
        distributed_key = f"rate_limit:{key}:{identifier or 'default'}"
        
        try:
            # Use Redis atomic operations for distributed rate limiting
            pipeline = self.redis_client.pipeline()
            
            # Remove old entries
            pipeline.zremrangebyscore(distributed_key, 0, current_time - window)
            
            # Count current requests
            pipeline.zcard(distributed_key)
            
            # Add current request
            pipeline.zadd(distributed_key, {str(current_time): current_time})
            
            # Set expiration
            pipeline.expire(distributed_key, window)
            
            results = pipeline.execute()
            current_count = results[1]
            
            if current_count >= limit:
                return False, {
                    "allowed": False,
                    "count": current_count,
                    "limit": limit,
                    "remaining": 0,
                    "reset_time": current_time + window,
                    "strategy": "distributed"
                }
            
            return True, {
                "allowed": True,
                "count": current_count + 1,
                "limit": limit,
                "remaining": limit - current_count - 1,
                "reset_time": current_time + window,
                "strategy": "distributed"
            }
        except Exception as e:
            logger.error(f"Redis error in distributed rate limiting: {e}")
            # Fall back to sliding window
            return self._check_sliding_window(key, limit, window, identifier)
    
    def get_rate_limit_status(self, key: str, identifier: str = None) -> Dict[str, Any]:
        """Get current rate limit status"""
        status_key = f"{key}:{identifier or 'default'}"
        
        if self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            if status_key in self.sliding_windows:
                window_data = self.sliding_windows[status_key]
                return {
                    "current_count": len(window_data),
                    "window_data": list(window_data),
                    "strategy": "sliding_window"
                }
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            if status_key in self.token_buckets:
                bucket = self.token_buckets[status_key]
                return {
                    "tokens": bucket["tokens"],
                    "capacity": bucket["capacity"],
                    "refill_rate": bucket["refill_rate"],
                    "strategy": "token_bucket"
                }
        elif self.strategy == RateLimitStrategy.LEAKY_BUCKET:
            if status_key in self.leaky_buckets:
                bucket = self.leaky_buckets[status_key]
                return {
                    "queue_size": bucket["queue_size"],
                    "max_size": bucket["max_size"],
                    "leak_rate": bucket["leak_rate"],
                    "strategy": "leaky_bucket"
                }
        
        return {"strategy": self.strategy.value, "status": "not_available"}
    
    def reset_rate_limit(self, key: str, identifier: str = None):
        """Reset rate limit for a key"""
        status_key = f"{key}:{identifier or 'default'}"
        
        # Remove from local storage
        if status_key in self.sliding_windows:
            del self.sliding_windows[status_key]
        if status_key in self.token_buckets:
            del self.token_buckets[status_key]
        if status_key in self.leaky_buckets:
            del self.leaky_buckets[status_key]
        if status_key in self.fixed_windows:
            del self.fixed_windows[status_key]
        
        # Remove from Redis
        if self.redis_client:
            try:
                self.redis_client.delete(status_key)
            except Exception as e:
                logger.error(f"Error resetting rate limit in Redis: {e}")
        
        logger.info(f"Reset rate limit for key: {status_key}")
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        stats = {
            "strategy": self.strategy.value,
            "redis_available": self.redis_client is not None,
            "local_sliding_windows": len(self.sliding_windows),
            "local_token_buckets": len(self.token_buckets),
            "local_leaky_buckets": len(self.leaky_buckets),
            "local_fixed_windows": len(self.fixed_windows)
        }
        
        if self.redis_client:
            try:
                # Get Redis stats
                redis_keys = self.redis_client.keys("rate_limit:*")
                stats["redis_keys"] = len(redis_keys)
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")
                stats["redis_error"] = str(e)
        
        return stats
    
    def set_strategy(self, strategy: RateLimitStrategy):
        """Change rate limiting strategy"""
        old_strategy = self.strategy
        self.strategy = strategy
        
        # Clear local data when changing strategy
        self.sliding_windows.clear()
        self.token_buckets.clear()
        self.leaky_buckets.clear()
        self.fixed_windows.clear()
        
        logger.info(f"Rate limiting strategy changed from {old_strategy.value} to {strategy.value}")

class GatewayRateLimiter:
    """Gateway-specific rate limiter with multiple rate limit types"""
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.rate_limiters = {}
        self.rate_limit_configs = {}
        
        # Default rate limit configurations
        self.default_configs = {
            RateLimitType.GLOBAL: {"limit": 1000, "window": 60},
            RateLimitType.PER_USER: {"limit": 100, "window": 60},
            RateLimitType.PER_IP: {"limit": 200, "window": 60},
            RateLimitType.PER_ENDPOINT: {"limit": 500, "window": 60},
            RateLimitType.PER_SERVICE: {"limit": 300, "window": 60}
        }
        
        # Initialize default rate limiters
        for limit_type in RateLimitType:
            self.rate_limiters[limit_type] = RateLimiter(
                RateLimitStrategy.SLIDING_WINDOW, redis_client
            )
    
    def check_rate_limits(self, request_context: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check all applicable rate limits"""
        results = []
        overall_allowed = True
        
        # Check each rate limit type
        for limit_type, limiter in self.rate_limiters.items():
            config = self.rate_limit_configs.get(limit_type, self.default_configs[limit_type])
            key = self._get_rate_limit_key(limit_type, request_context)
            
            allowed, result = limiter.check_rate_limit(
                key, config["limit"], config["window"]
            )
            
            result["limit_type"] = limit_type.value
            results.append(result)
            
            if not allowed:
                overall_allowed = False
        
        return overall_allowed, results
    
    def _get_rate_limit_key(self, limit_type: RateLimitType, 
                           request_context: Dict[str, Any]) -> str:
        """Get rate limit key based on type and request context"""
        if limit_type == RateLimitType.GLOBAL:
            return "global"
        elif limit_type == RateLimitType.PER_USER:
            return f"user:{request_context.get('user_id', 'anonymous')}"
        elif limit_type == RateLimitType.PER_IP:
            return f"ip:{request_context.get('client_ip', 'unknown')}"
        elif limit_type == RateLimitType.PER_ENDPOINT:
            return f"endpoint:{request_context.get('endpoint', 'unknown')}"
        elif limit_type == RateLimitType.PER_SERVICE:
            return f"service:{request_context.get('service_name', 'unknown')}"
        else:
            return "unknown"
    
    def configure_rate_limit(self, limit_type: RateLimitType, 
                           limit: int, window: int, 
                           strategy: RateLimitStrategy = None):
        """Configure rate limit for a specific type"""
        self.rate_limit_configs[limit_type] = {"limit": limit, "window": window}
        
        if strategy:
            self.rate_limiters[limit_type].set_strategy(strategy)
        
        logger.info(f"Configured rate limit for {limit_type.value}: {limit}/{window}s")
    
    def get_all_rate_limit_statuses(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get status for all rate limit types"""
        statuses = {}
        
        for limit_type, limiter in self.rate_limiters.items():
            key = self._get_rate_limit_key(limit_type, request_context)
            status = limiter.get_rate_limit_status(key)
            statuses[limit_type.value] = status
        
        return statuses
    
    def get_gateway_rate_limit_stats(self) -> Dict[str, Any]:
        """Get comprehensive rate limiting statistics"""
        stats = {
            "rate_limit_types": list(RateLimitType),
            "configurations": self.rate_limit_configs,
            "default_configurations": self.default_configs,
            "limiter_stats": {}
        }
        
        for limit_type, limiter in self.rate_limiters.items():
            stats["limiter_stats"][limit_type.value] = limiter.get_rate_limit_stats()
        
        return stats
