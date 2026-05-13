"""
Cache Tuner

Automatic performance tuning and optimization for cache infrastructure
including memory management, eviction policies, and performance optimization.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import threading
import statistics
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class TuningStrategy(Enum):
    """Cache tuning strategies"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"

class OptimizationType(Enum):
    """Optimization types"""
    MEMORY = "memory"
    EVICTION = "eviction"
    TTL = "ttl"
    CONNECTION = "connection"
    COMPRESSION = "compression"

@dataclass
class TuningConfig:
    """Tuning configuration"""
    strategy: TuningStrategy = TuningStrategy.BALANCED
    tuning_interval: int = 300  # 5 minutes
    memory_threshold: float = 0.8  # 80% memory usage threshold
    hit_rate_threshold: float = 0.7  # 70% hit rate threshold
    response_time_threshold: float = 0.1  # 100ms response time threshold
    enable_auto_tuning: bool = True
    enable_memory_optimization: bool = True
    enable_ttl_optimization: bool = True
    enable_connection_optimization: bool = True
    enable_compression_optimization: bool = True
    max_memory_increase: float = 0.2  # 20% max memory increase
    min_ttl: int = 60  # 1 minute minimum TTL
    max_ttl: int = 86400  # 24 hours maximum TTL
    connection_pool_size: int = 100
    compression_threshold: int = 1024  # Compress values > 1KB

@dataclass
class TuningRecommendation:
    """Tuning recommendation"""
    optimization_type: OptimizationType
    recommendation: str
    current_value: Any
    recommended_value: Any
    impact: str
    confidence: float
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class TuningMetrics:
    """Tuning metrics"""
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    memory_usage: float = 0.0
    memory_usage_percent: float = 0.0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    throughput: float = 0.0
    eviction_rate: float = 0.0
    key_count: int = 0
    connection_count: int = 0
    compression_ratio: float = 0.0

class CacheTuner:
    """Automatic cache performance tuner"""
    
    def __init__(self, config: TuningConfig = None, redis_client=None, redis_cluster=None):
        self.config = config or TuningConfig()
        self.redis_client = redis_client
        self.redis_cluster = redis_cluster
        self.tuning_enabled = True
        self.recommendations: List[TuningRecommendation] = []
        self.tuning_history: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.metrics_history = deque(maxlen=100)
        self.tuning_stats = {
            'total_tunings': 0,
            'successful_tunings': 0,
            'failed_tunings': 0,
            'last_tuning_time': None
        }
        
        # Start tuning thread
        self._start_tuning_thread()
    
    def _start_tuning_thread(self):
        """Start background tuning thread"""
        def tuning_loop():
            while self.tuning_enabled:
                try:
                    if self.config.enable_auto_tuning:
                        self._perform_tuning_cycle()
                    time.sleep(self.config.tuning_interval)
                except Exception as e:
                    logger.error(f"Tuning loop error: {e}")
                    time.sleep(60)
        
        tuning_thread = threading.Thread(target=tuning_loop, daemon=True)
        tuning_thread.start()
        logger.info("Cache tuner started")
    
    def _perform_tuning_cycle(self):
        """Perform a complete tuning cycle"""
        try:
            # Collect current metrics
            metrics = self._collect_metrics()
            self.metrics_history.append(metrics)
            
            # Analyze performance
            analysis = self._analyze_performance(metrics)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metrics, analysis)
            
            # Apply recommendations if safe
            if recommendations:
                self._apply_recommendations(recommendations)
            
            # Record tuning cycle
            self._record_tuning_cycle(metrics, analysis, recommendations)
            
        except Exception as e:
            logger.error(f"Tuning cycle failed: {e}")
    
    def _collect_metrics(self) -> TuningMetrics:
        """Collect current cache metrics"""
        metrics = TuningMetrics()
        
        try:
            redis_client = self.redis_cluster or self.redis_client
            
            if redis_client:
                # Get Redis info
                if self.redis_cluster:
                    # Aggregate metrics from cluster nodes
                    total_memory = 0
                    total_keys = 0
                    total_hits = 0
                    total_misses = 0
                    total_ops = 0
                    total_evictions = 0
                    
                    for node in self.redis_cluster.get_nodes():
                        node_client = self.redis_cluster.get_redis_connection(node)
                        info = node_client.info()
                        
                        total_memory += info.get('used_memory', 0)
                        total_keys += info.get('db0', {}).get('keys', 0)
                        total_hits += info.get('keyspace_hits', 0)
                        total_misses += info.get('keyspace_misses', 0)
                        total_ops += info.get('instantaneous_ops_per_sec', 0)
                        total_evictions += info.get('evicted_keys', 0)
                    
                    metrics.memory_usage = total_memory
                    metrics.key_count = total_keys
                    metrics.throughput = total_ops
                    metrics.eviction_rate = total_evictions / 300 if total_evictions > 0 else 0  # Per second
                else:
                    info = redis_client.info()
                    
                    metrics.memory_usage = info.get('used_memory', 0)
                    metrics.key_count = info.get('db0', {}).get('keys', 0)
                    metrics.throughput = info.get('instantaneous_ops_per_sec', 0)
                    metrics.eviction_rate = info.get('evicted_keys', 0) / 300 if info.get('evicted_keys', 0) > 0 else 0
                
                # Calculate hit rate
                hits = info.get('keyspace_hits', 0)
                misses = info.get('keyspace_misses', 0)
                total_requests = hits + misses
                
                if total_requests > 0:
                    metrics.hit_rate = hits / total_requests
                    metrics.miss_rate = misses / total_requests
                
                # Get memory usage percentage
                max_memory = info.get('maxmemory', 0)
                if max_memory > 0:
                    metrics.memory_usage_percent = metrics.memory_usage / max_memory
                
                # Get connection count
                metrics.connection_count = info.get('connected_clients', 0)
        
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
        
        return metrics
    
    def _analyze_performance(self, metrics: TuningMetrics) -> Dict[str, Any]:
        """Analyze performance metrics"""
        analysis = {
            'issues': [],
            'opportunities': [],
            'overall_score': 0.0,
            'recommendations_needed': []
        }
        
        # Analyze hit rate
        if metrics.hit_rate < self.config.hit_rate_threshold:
            analysis['issues'].append(f"Low hit rate: {metrics.hit_rate:.2%}")
            analysis['recommendations_needed'].append('ttl')
            analysis['overall_score'] -= 20
        
        # Analyze memory usage
        if metrics.memory_usage_percent > self.config.memory_threshold:
            analysis['issues'].append(f"High memory usage: {metrics.memory_usage_percent:.2%}")
            analysis['recommendations_needed'].append('memory')
            analysis['recommendations_needed'].append('eviction')
            analysis['overall_score'] -= 25
        
        # Analyze response time (if available)
        if len(self.metrics_history) > 1:
            recent_metrics = list(self.metrics_history)[-10:]
            response_times = [m.avg_response_time for m in recent_metrics if m.avg_response_time > 0]
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                if avg_response_time > self.config.response_time_threshold:
                    analysis['issues'].append(f"High response time: {avg_response_time:.3f}s")
                    analysis['recommendations_needed'].append('connection')
                    analysis['recommendations_needed'].append('compression')
                    analysis['overall_score'] -= 15
        
        # Analyze eviction rate
        if metrics.eviction_rate > 10:  # More than 10 evictions per second
            analysis['issues'].append(f"High eviction rate: {metrics.eviction_rate:.2f}/s")
            analysis['recommendations_needed'].append('memory')
            analysis['recommendations_needed'].append('eviction')
            analysis['overall_score'] -= 10
        
        # Identify opportunities
        if metrics.hit_rate > 0.9:
            analysis['opportunities'].append("Excellent hit rate - consider reducing memory")
        
        if metrics.memory_usage_percent < 0.5:
            analysis['opportunities'].append("Low memory usage - could increase cache size")
        
        # Calculate overall score
        analysis['overall_score'] = max(0, 100 + analysis['overall_score'])
        
        return analysis
    
    def _generate_recommendations(self, metrics: TuningMetrics, analysis: Dict[str, Any]) -> List[TuningRecommendation]:
        """Generate tuning recommendations"""
        recommendations = []
        
        # Memory optimization recommendations
        if 'memory' in analysis['recommendations_needed']:
            if metrics.memory_usage_percent > 0.9:
                recommendations.append(TuningRecommendation(
                    optimization_type=OptimizationType.MEMORY,
                    recommendation="Increase max memory limit",
                    current_value=f"{metrics.memory_usage_percent:.2%}",
                    recommended_value=f"{min(metrics.memory_usage_percent * 1.2, 0.95):.2%}",
                    impact="Reduce evictions and improve hit rate",
                    confidence=0.8
                ))
            elif metrics.memory_usage_percent > 0.8:
                recommendations.append(TuningRecommendation(
                    optimization_type=OptimizationType.EVICTION,
                    recommendation="Change eviction policy to allkeys-lru",
                    current_value="Current eviction policy",
                    recommended_value="allkeys-lru",
                    impact="Better memory utilization",
                    confidence=0.7
                ))
        
        # TTL optimization recommendations
        if 'ttl' in analysis['recommendations_needed']:
            if metrics.hit_rate < 0.5:
                recommendations.append(TuningRecommendation(
                    optimization_type=OptimizationType.TTL,
                    recommendation="Increase TTL for frequently accessed keys",
                    current_value="Current TTL settings",
                    recommended_value=f"TTL: {self.config.max_ttl * 2}s",
                    impact="Improve hit rate",
                    confidence=0.6
                ))
            elif metrics.miss_rate > 0.3:
                recommendations.append(TuningRecommendation(
                    optimization_type=OptimizationType.TTL,
                    recommendation="Reduce TTL for infrequently accessed keys",
                    current_value="Current TTL settings",
                    recommended_value=f"TTL: {self.config.min_ttl}s",
                    impact="Free up memory for hot keys",
                    confidence=0.5
                ))
        
        # Connection optimization recommendations
        if 'connection' in analysis['recommendations_needed']:
            recommendations.append(TuningRecommendation(
                optimization_type=OptimizationType.CONNECTION,
                recommendation="Increase connection pool size",
                current_value=f"Pool size: {self.config.connection_pool_size}",
                recommended_value=f"Pool size: {self.config.connection_pool_size * 2}",
                impact="Reduce connection overhead",
                confidence=0.6
            ))
        
        # Compression optimization recommendations
        if 'compression' in analysis['recommendations_needed']:
            recommendations.append(TuningRecommendation(
                optimization_type=OptimizationType.COMPRESSION,
                recommendation="Enable compression for large values",
                current_value="Compression disabled",
                recommended_value="Compression enabled",
                impact="Reduce memory usage",
                confidence=0.7
            ))
        
        # Store recommendations
        self.recommendations.extend(recommendations)
        
        # Keep only recent recommendations
        if len(self.recommendations) > 50:
            self.recommendations = self.recommendations[-50:]
        
        return recommendations
    
    def _apply_recommendations(self, recommendations: List[TuningRecommendation]):
        """Apply safe tuning recommendations"""
        for recommendation in recommendations:
            try:
                # Only apply high-confidence recommendations
                if recommendation.confidence < 0.7:
                    logger.info(f"Skipping low-confidence recommendation: {recommendation.recommendation}")
                    continue
                
                # Apply recommendation based on type
                if recommendation.optimization_type == OptimizationType.MEMORY:
                    self._apply_memory_optimization(recommendation)
                elif recommendation.optimization_type == OptimizationType.EVICTION:
                    self._apply_eviction_optimization(recommendation)
                elif recommendation.optimization_type == OptimizationType.CONNECTION:
                    self._apply_connection_optimization(recommendation)
                elif recommendation.optimization_type == OptimizationType.COMPRESSION:
                    self._apply_compression_optimization(recommendation)
                
                self.tuning_stats['successful_tunings'] += 1
                logger.info(f"Applied recommendation: {recommendation.recommendation}")
                
            except Exception as e:
                self.tuning_stats['failed_tunings'] += 1
                logger.error(f"Failed to apply recommendation: {e}")
        
        self.tuning_stats['total_tunings'] += len(recommendations)
        self.tuning_stats['last_tuning_time'] = datetime.utcnow()
    
    def _apply_memory_optimization(self, recommendation: TuningRecommendation):
        """Apply memory optimization"""
        try:
            redis_client = self.redis_cluster or self.redis_client
            
            if redis_client:
                # Parse recommended memory value
                if '%' in recommendation.recommended_value:
                    new_percent = float(recommendation.recommended_value.replace('%', ''))
                    
                    # Get current max memory
                    current_max = redis_client.config_get('maxmemory').get('maxmemory', '0')
                    
                    if current_max != '0':
                        current_max_bytes = int(current_max)
                        new_max_bytes = int(current_max_bytes * new_percent)
                        
                        # Apply new max memory
                        redis_client.config_set('maxmemory', new_max_bytes)
                        logger.info(f"Updated maxmemory to {new_max_bytes} bytes")
        
        except Exception as e:
            logger.error(f"Error applying memory optimization: {e}")
            raise
    
    def _apply_eviction_optimization(self, recommendation: TuningRecommendation):
        """Apply eviction optimization"""
        try:
            redis_client = self.redis_cluster or self.redis_client
            
            if redis_client:
                # Set eviction policy
                redis_client.config_set('maxmemory-policy', 'allkeys-lru')
                logger.info("Updated eviction policy to allkeys-lru")
        
        except Exception as e:
            logger.error(f"Error applying eviction optimization: {e}")
            raise
    
    def _apply_connection_optimization(self, recommendation: TuningRecommendation):
        """Apply connection optimization"""
        try:
            # This would require updating the connection pool configuration
            # For now, just log the recommendation
            logger.info(f"Connection optimization recommended: {recommendation.recommended_value}")
        
        except Exception as e:
            logger.error(f"Error applying connection optimization: {e}")
            raise
    
    def _apply_compression_optimization(self, recommendation: TuningRecommendation):
        """Apply compression optimization"""
        try:
            # This would require implementing compression in the cache layer
            # For now, just log the recommendation
            logger.info(f"Compression optimization recommended: {recommendation.recommended_value}")
        
        except Exception as e:
            logger.error(f"Error applying compression optimization: {e}")
            raise
    
    def _record_tuning_cycle(self, metrics: TuningMetrics, analysis: Dict[str, Any], 
                           recommendations: List[TuningRecommendation]):
        """Record tuning cycle for analysis"""
        cycle_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'hit_rate': metrics.hit_rate,
                'memory_usage_percent': metrics.memory_usage_percent,
                'avg_response_time': metrics.avg_response_time,
                'throughput': metrics.throughput,
                'eviction_rate': metrics.eviction_rate,
                'key_count': metrics.key_count,
                'connection_count': metrics.connection_count
            },
            'analysis': {
                'overall_score': analysis['overall_score'],
                'issues_count': len(analysis['issues']),
                'opportunities_count': len(analysis['opportunities'])
            },
            'recommendations_count': len(recommendations),
            'recommendations_applied': len([r for r in recommendations if r.confidence >= 0.7])
        }
        
        self.tuning_history.append(cycle_record)
        
        # Keep only recent history
        if len(self.tuning_history) > 100:
            self.tuning_history = self.tuning_history[-100:]
    
    def manual_tune(self, optimization_type: OptimizationType, parameters: Dict[str, Any]) -> bool:
        """Manually trigger tuning for specific optimization type"""
        try:
            if optimization_type == OptimizationType.MEMORY:
                return self._manual_memory_tune(parameters)
            elif optimization_type == OptimizationType.EVICTION:
                return self._manual_eviction_tune(parameters)
            elif optimization_type == OptimizationType.TTL:
                return self._manual_ttl_tune(parameters)
            elif optimization_type == OptimizationType.CONNECTION:
                return self._manual_connection_tune(parameters)
            elif optimization_type == OptimizationType.COMPRESSION:
                return self._manual_compression_tune(parameters)
            
            return False
        
        except Exception as e:
            logger.error(f"Manual tuning failed: {e}")
            return False
    
    def _manual_memory_tune(self, parameters: Dict[str, Any]) -> bool:
        """Manual memory tuning"""
        try:
            redis_client = self.redis_cluster or self.redis_client
            
            if redis_client and 'max_memory' in parameters:
                new_max_memory = parameters['max_memory']
                redis_client.config_set('maxmemory', new_max_memory)
                logger.info(f"Manual memory tuning: maxmemory set to {new_max_memory}")
                return True
        
        except Exception as e:
            logger.error(f"Manual memory tuning failed: {e}")
        
        return False
    
    def _manual_eviction_tune(self, parameters: Dict[str, Any]) -> bool:
        """Manual eviction tuning"""
        try:
            redis_client = self.redis_cluster or self.redis_client
            
            if redis_client and 'policy' in parameters:
                policy = parameters['policy']
                redis_client.config_set('maxmemory-policy', policy)
                logger.info(f"Manual eviction tuning: policy set to {policy}")
                return True
        
        except Exception as e:
            logger.error(f"Manual eviction tuning failed: {e}")
        
        return False
    
    def _manual_ttl_tune(self, parameters: Dict[str, Any]) -> bool:
        """Manual TTL tuning"""
        try:
            # This would require implementing TTL management
            logger.info(f"Manual TTL tuning requested: {parameters}")
            return True
        
        except Exception as e:
            logger.error(f"Manual TTL tuning failed: {e}")
        
        return False
    
    def _manual_connection_tune(self, parameters: Dict[str, Any]) -> bool:
        """Manual connection tuning"""
        try:
            # This would require updating connection pool configuration
            logger.info(f"Manual connection tuning requested: {parameters}")
            return True
        
        except Exception as e:
            logger.error(f"Manual connection tuning failed: {e}")
        
        return False
    
    def _manual_compression_tune(self, parameters: Dict[str, Any]) -> bool:
        """Manual compression tuning"""
        try:
            # This would require implementing compression configuration
            logger.info(f"Manual compression tuning requested: {parameters}")
            return True
        
        except Exception as e:
            logger.error(f"Manual compression tuning failed: {e}")
        
        return False
    
    def get_tuning_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tuning recommendations"""
        recent_recommendations = self.recommendations[-limit:] if len(self.recommendations) > limit else self.recommendations
        
        return [
            {
                'optimization_type': rec.optimization_type.value,
                'recommendation': rec.recommendation,
                'current_value': rec.current_value,
                'recommended_value': rec.recommended_value,
                'impact': rec.impact,
                'confidence': rec.confidence,
                'created_at': rec.created_at.isoformat()
            }
            for rec in recent_recommendations
        ]
    
    def get_tuning_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tuning history"""
        recent_history = self.tuning_history[-limit:] if len(self.tuning_history) > limit else self.tuning_history
        
        return recent_history
    
    def get_tuning_stats(self) -> Dict[str, Any]:
        """Get tuning statistics"""
        return {
            'total_tunings': self.tuning_stats['total_tunings'],
            'successful_tunings': self.tuning_stats['successful_tunings'],
            'failed_tunings': self.tuning_stats['failed_tunings'],
            'success_rate': (
                self.tuning_stats['successful_tunings'] / self.tuning_stats['total_tunings']
                if self.tuning_stats['total_tunings'] > 0 else 0
            ),
            'last_tuning_time': (
                self.tuning_stats['last_tuning_time'].isoformat()
                if self.tuning_stats['last_tuning_time'] else None
            ),
            'total_recommendations': len(self.recommendations),
            'tuning_enabled': self.tuning_enabled,
            'auto_tuning_enabled': self.config.enable_auto_tuning,
            'tuning_interval': self.config.tuning_interval
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get tuning configuration"""
        return {
            'strategy': self.config.strategy.value,
            'tuning_interval': self.config.tuning_interval,
            'memory_threshold': self.config.memory_threshold,
            'hit_rate_threshold': self.config.hit_rate_threshold,
            'response_time_threshold': self.config.response_time_threshold,
            'enable_auto_tuning': self.config.enable_auto_tuning,
            'enable_memory_optimization': self.config.enable_memory_optimization,
            'enable_ttl_optimization': self.config.enable_ttl_optimization,
            'enable_connection_optimization': self.config.enable_connection_optimization,
            'enable_compression_optimization': self.config.enable_compression_optimization,
            'max_memory_increase': self.config.max_memory_increase,
            'min_ttl': self.config.min_ttl,
            'max_ttl': self.config.max_ttl,
            'connection_pool_size': self.config.connection_pool_size,
            'compression_threshold': self.config.compression_threshold
        }
    
    def update_config(self, **kwargs):
        """Update tuning configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated tuning config: {key} = {value}")
    
    def shutdown(self):
        """Shutdown cache tuner"""
        try:
            # Stop tuning
            self.tuning_enabled = False
            
            logger.info("Cache tuner shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during cache tuner shutdown: {e}")
