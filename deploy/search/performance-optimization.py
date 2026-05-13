#!/usr/bin/env python3
"""
Search Infrastructure Performance Optimization
Auto Bot Solutions Forum

This module provides performance optimization utilities for the search infrastructure,
including Elasticsearch optimization, index management, query optimization, and monitoring.
"""

import os
import sys
import time
import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, RequestError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Optimization types"""
    INDEX = "index"
    QUERY = "query"
    CACHE = "cache"
    JVM = "jvm"
    NETWORK = "network"


@dataclass
class OptimizationResult:
    """Optimization result"""
    optimization_type: OptimizationType
    success: bool
    message: str
    metrics_before: Dict[str, Any]
    metrics_after: Dict[str, Any]
    improvement_percentage: float
    timestamp: datetime


class ElasticsearchOptimizer:
    """Elasticsearch performance optimizer"""
    
    def __init__(self, es_config: Dict[str, Any]):
        self.es_config = es_config
        self.es = self._create_elasticsearch_client()
    
    def _create_elasticsearch_client(self):
        """Create Elasticsearch client"""
        try:
            es = Elasticsearch([{
                'host': self.es_config['host'],
                'port': self.es_config['port'],
                'username': self.es_config.get('username'),
                'password': self.es_config.get('password')
            }])
            
            # Test connection
            if es.ping():
                logger.info("Successfully connected to Elasticsearch")
                return es
            else:
                raise ConnectionError("Failed to connect to Elasticsearch")
                
        except Exception as e:
            logger.error(f"Error creating Elasticsearch client: {str(e)}")
            raise
    
    def optimize_elasticsearch(self) -> OptimizationResult:
        """Optimize Elasticsearch performance"""
        try:
            metrics_before = self._collect_elasticsearch_metrics()
            
            # Perform optimizations
            self._optimize_cluster_settings()
            self._optimize_index_settings()
            self._optimize_cache_settings()
            self._optimize_jvm_settings()
            self._cleanup_old_indices()
            
            metrics_after = self._collect_elasticsearch_metrics()
            improvement = self._calculate_improvement(metrics_before, metrics_after)
            
            return OptimizationResult(
                optimization_type=OptimizationType.INDEX,
                success=True,
                message="Elasticsearch optimization completed successfully",
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                improvement_percentage=improvement,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Elasticsearch optimization failed: {str(e)}")
            return OptimizationResult(
                optimization_type=OptimizationType.INDEX,
                success=False,
                message=f"Elasticsearch optimization failed: {str(e)}",
                metrics_before={},
                metrics_after={},
                improvement_percentage=0.0,
                timestamp=datetime.utcnow()
            )
    
    def _collect_elasticsearch_metrics(self) -> Dict[str, Any]:
        """Collect Elasticsearch performance metrics"""
        metrics = {}
        
        try:
            # Cluster health
            health = self.es.cluster.health()
            metrics['cluster_status'] = health['status']
            metrics['number_of_nodes'] = health['number_of_nodes']
            metrics['active_shards'] = health['active_shards']
            metrics['unassigned_shards'] = health['unassigned_shards']
            
            # Node stats
            stats = self.es.nodes.stats(metric=['jvm', 'indices', 'process'])
            if stats['nodes']:
                node_id = list(stats['nodes'].keys())[0]
                node_stats = stats['nodes'][node_id]
                
                # JVM metrics
                jvm = node_stats.get('jvm', {})
                metrics['heap_used_percent'] = jvm.get('mem', {}).get('heap_used_percent', 0)
                metrics['heap_used_bytes'] = jvm.get('mem', {}).get('heap_used_in_bytes', 0)
                metrics['heap_committed_bytes'] = jvm.get('mem', {}).get('heap_committed_in_bytes', 0)
                metrics['gc_time_ms'] = sum([
                    gc.get('collection_time_in_millis', 0) 
                    for gc in jvm.get('gc', {}).get('collectors', {}).values()
                ])
                
                # Index metrics
                indices = node_stats.get('indices', {})
                metrics['indexing_rate'] = indices.get('indexing', {}).get('index_total', 0)
                metrics['search_rate'] = indices.get('search', {}).get('query_total', 0)
                metrics['indexing_time_ms'] = indices.get('indexing', {}).get('index_time_in_millis', 0)
                metrics['search_time_ms'] = indices.get('search', {}).get('query_time_in_millis', 0)
                metrics['docs_count'] = indices.get('docs', {}).get('count', 0)
                metrics['store_size_bytes'] = indices.get('store', {}).get('size_in_bytes', 0)
                
                # Process metrics
                process = node_stats.get('process', {})
                metrics['cpu_percent'] = process.get('cpu', {}).get('percent', 0)
                metrics['open_file_descriptors'] = process.get('open_file_descriptors', 0)
            
            # Index stats
            index_stats = self.es.indices.stats()
            metrics['total_indices'] = len(index_stats.get('indices', {}))
            
            # Cache metrics
            cache_stats = self.es.indices.stats(metric=['cache'])
            metrics['query_cache_hit_rate'] = self._calculate_cache_hit_rate(cache_stats, 'query_cache')
            metrics['request_cache_hit_rate'] = self._calculate_cache_hit_rate(cache_stats, 'request_cache')
            
        except Exception as e:
            logger.error(f"Error collecting Elasticsearch metrics: {str(e)}")
        
        return metrics
    
    def _calculate_cache_hit_rate(self, stats: Dict[str, Any], cache_type: str) -> float:
        """Calculate cache hit rate"""
        try:
            total_hits = 0
            total_misses = 0
            
            for index_name, index_stats in stats.get('indices', {}).items():
                cache_stats = index_stats.get('total', {}).get(cache_type, {})
                hits = cache_stats.get('hit_count', 0)
                misses = cache_stats.get('miss_count', 0)
                total_hits += hits
                total_misses += misses
            
            total = total_hits + total_misses
            return (total_hits / total * 100) if total > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating cache hit rate: {str(e)}")
            return 0.0
    
    def _optimize_cluster_settings(self):
        """Optimize cluster-level settings"""
        try:
            settings = {
                "persistent": {
                    # Search settings
                    "search.max_buckets": 10000,
                    "search.max_clause_count": 1024,
                    "search.default_search_timeout": "30s",
                    
                    # Thread pool settings
                    "thread_pool.write.queue_size": 1000,
                    "thread_pool.search.queue_size": 1000,
                    "thread_pool.management.queue_size": 500,
                    
                    # Performance settings
                    "indices.memory.index_buffer_size": "10%",
                    "indices.queries.cache.size": "10%",
                    "indices.fielddata.cache.size": "30%",
                    "indices.requests.cache.size": "1%",
                    
                    # Recovery settings
                    "cluster.routing.allocation.node_initial_primaries_recoveries": 16,
                    "cluster.routing.allocation.node_concurrent_recoveries": 2,
                    "cluster.routing.allocation.cluster_concurrent_rebalance": 2,
                    
                    # Circuit breaker settings
                    "indices.breaker.request.limit": "60%",
                    "indices.breaker.fielddata.limit": "60%",
                    "indices.breaker.total.limit": "70%"
                }
            }
            
            self.es.cluster.put_settings(body=settings)
            logger.info("Applied cluster-level optimizations")
            
        except Exception as e:
            logger.error(f"Error optimizing cluster settings: {str(e)}")
    
    def _optimize_index_settings(self):
        """Optimize index-level settings"""
        try:
            # Get all indices
            indices = self.es.cat.indices(index='*', format='json')
            
            for index in indices:
                index_name = index['index']
                
                # Skip system indices
                if index_name.startswith('.'):
                    continue
                
                # Optimize settings for each index
                settings = {
                    "index": {
                        "refresh_interval": "5s",
                        "number_of_replicas": 0,
                        "max_result_window": 10000,
                        "translog.flush_threshold_size": "512mb",
                        "merge.policy.max_merge_at_once": 5,
                        "merge.policy.segments_per_tier": 10,
                        "merge.policy.max_merged_segment": "5gb"
                    }
                }
                
                try:
                    self.es.indices.put_settings(index=index_name, body=settings)
                    logger.info(f"Optimized settings for index: {index_name}")
                except Exception as e:
                    logger.warning(f"Failed to optimize index {index_name}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error optimizing index settings: {str(e)}")
    
    def _optimize_cache_settings(self):
        """Optimize cache settings"""
        try:
            # Clear caches if hit rates are low
            metrics = self._collect_elasticsearch_metrics()
            
            if metrics.get('query_cache_hit_rate', 0) < 50:
                self.es.indices.clear_cache(index='_all', request=True)
                logger.info("Cleared query cache due to low hit rate")
            
            if metrics.get('request_cache_hit_rate', 0) < 50:
                self.es.indices.clear_cache(index='_all', request=True)
                logger.info("Cleared request cache due to low hit rate")
            
        except Exception as e:
            logger.error(f"Error optimizing cache settings: {str(e)}")
    
    def _optimize_jvm_settings(self):
        """Optimize JVM settings (requires restart)"""
        try:
            # Log current JVM settings
            nodes = self.es.nodes.info()
            if nodes['nodes']:
                node_id = list(nodes['nodes'].keys())[0]
                jvm_info = nodes['nodes'][node_id].get('jvm', {})
                
                logger.info("Current JVM settings:")
                logger.info(f"  Heap size: {jvm_info.get('mem', {}).get('heap_init', 'N/A')}")
                logger.info(f"  GC collectors: {list(jvm_info.get('gc', {}).get('collectors', {}).keys())}")
                
                # Recommendations
                heap_size = jvm_info.get('mem', {}).get('heap_init', 0)
                if heap_size and heap_size < 1073741824:  # Less than 1GB
                    logger.warning("Consider increasing heap size to at least 1GB")
                
        except Exception as e:
            logger.error(f"Error optimizing JVM settings: {str(e)}")
    
    def _cleanup_old_indices(self):
        """Clean up old indices based on retention policy"""
        try:
            # Get all indices
            indices = self.es.cat.indices(index='*', format='json')
            
            for index in indices:
                index_name = index['index']
                
                # Skip system indices and important indices
                if index_name.startswith('.') or index_name in ['forum_posts', 'users', 'forum_comments', 'search_analytics']:
                    continue
                
                # Check if index is old (based on naming convention)
                if self._is_old_index(index_name):
                    try:
                        self.es.indices.delete(index=index_name)
                        logger.info(f"Deleted old index: {index_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete index {index_name}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old indices: {str(e)}")
    
    def _is_old_index(self, index_name: str) -> bool:
        """Check if index is old based on naming convention"""
        try:
            # Look for date patterns in index names
            import re
            
            # Pattern: indexname-YYYY.MM.DD or indexname_YYYYMMDD
            date_patterns = [
                r'.*-(\d{4}\.\d{2}\.\d{2})$',
                r'.*_(\d{8})$',
                r'.*-(\d{4}-\d{2}-\d{2})$'
            ]
            
            for pattern in date_patterns:
                match = re.match(pattern, index_name)
                if match:
                    date_str = match.group(1)
                    
                    # Parse date
                    if '.' in date_str:
                        date_obj = datetime.strptime(date_str, '%Y.%m.%d')
                    elif '-' in date_str:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        date_obj = datetime.strptime(date_str, '%Y%m%d')
                    
                    # Check if older than 30 days
                    return (datetime.utcnow() - date_obj).days > 30
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if index is old: {str(e)}")
            return False
    
    def _calculate_improvement(self, metrics_before: Dict[str, Any], metrics_after: Dict[str, Any]) -> float:
        """Calculate improvement percentage"""
        try:
            improvements = []
            
            # Compare search latency
            if 'search_time_ms' in metrics_before and 'search_time_ms' in metrics_after:
                before = metrics_before['search_time_ms']
                after = metrics_after['search_time_ms']
                if before > 0:
                    improvement = ((before - after) / before) * 100
                    improvements.append(improvement)
            
            # Compare indexing latency
            if 'indexing_time_ms' in metrics_before and 'indexing_time_ms' in metrics_after:
                before = metrics_before['indexing_time_ms']
                after = metrics_after['indexing_time_ms']
                if before > 0:
                    improvement = ((before - after) / before) * 100
                    improvements.append(improvement)
            
            # Compare cache hit rates
            if 'query_cache_hit_rate' in metrics_before and 'query_cache_hit_rate' in metrics_after:
                before = metrics_before['query_cache_hit_rate']
                after = metrics_after['query_cache_hit_rate']
                if before > 0:
                    improvement = ((after - before) / before) * 100
                    improvements.append(improvement)
            
            return sum(improvements) / len(improvements) if improvements else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating improvement: {str(e)}")
            return 0.0


class QueryOptimizer:
    """Query performance optimizer"""
    
    def __init__(self, es_config: Dict[str, Any]):
        self.es_config = es_config
        self.es = Elasticsearch([{
            'host': es_config['host'],
            'port': es_config['port'],
            'username': es_config.get('username'),
            'password': es_config.get('password')
        }])
    
    def optimize_queries(self) -> OptimizationResult:
        """Optimize query performance"""
        try:
            metrics_before = self._collect_query_metrics()
            
            # Perform optimizations
            self._analyze_slow_queries()
            self._optimize_query_templates()
            self._update_search_analytics()
            
            metrics_after = self._collect_query_metrics()
            improvement = self._calculate_query_improvement(metrics_before, metrics_after)
            
            return OptimizationResult(
                optimization_type=OptimizationType.QUERY,
                success=True,
                message="Query optimization completed successfully",
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                improvement_percentage=improvement,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Query optimization failed: {str(e)}")
            return OptimizationResult(
                optimization_type=OptimizationType.QUERY,
                success=False,
                message=f"Query optimization failed: {str(e)}",
                metrics_before={},
                metrics_after={},
                improvement_percentage=0.0,
                timestamp=datetime.utcnow()
            )
    
    def _collect_query_metrics(self) -> Dict[str, Any]:
        """Collect query performance metrics"""
        metrics = {}
        
        try:
            # Get search analytics
            if self.es.indices.exists(index="search_analytics"):
                # Get recent query performance
                result = self.es.search(index="search_analytics", body={
                    "query": {
                        "range": {
                            "timestamp": {
                                "gte": "now-1h"
                            }
                        }
                    },
                    "aggs": {
                        "avg_execution_time": {
                            "avg": {
                                "field": "execution_time_ms"
                            }
                        },
                        "total_queries": {
                            "value_count": {
                                "field": "query_id"
                            }
                        },
                        "slow_queries": {
                            "filter": {
                                "range": {
                                    "execution_time_ms": {
                                        "gte": 1000
                                    }
                                }
                            }
                        }
                    }
                })
                
                aggregations = result.get('aggregations', {})
                metrics['avg_execution_time_ms'] = aggregations.get('avg_execution_time', {}).get('value', 0)
                metrics['total_queries'] = aggregations.get('total_queries', {}).get('value', 0)
                metrics['slow_queries_count'] = aggregations.get('slow_queries', {}).get('doc_count', 0)
                metrics['slow_query_rate'] = (metrics['slow_queries_count'] / metrics['total_queries'] * 100) if metrics['total_queries'] > 0 else 0
            
            # Get index search stats
            stats = self.es.indices.stats(metric=['search'])
            if stats['indices']:
                total_search_time = 0
                total_search_queries = 0
                
                for index_stats in stats['indices'].values():
                    search_stats = index_stats.get('total', {}).get('search', {})
                    total_search_time += search_stats.get('query_time_in_millis', 0)
                    total_search_queries += search_stats.get('query_total', 0)
                
                metrics['avg_search_time_ms'] = (total_search_time / total_search_queries) if total_search_queries > 0 else 0
                metrics['total_search_queries'] = total_search_queries
            
        except Exception as e:
            logger.error(f"Error collecting query metrics: {str(e)}")
        
        return metrics
    
    def _analyze_slow_queries(self):
        """Analyze slow queries from search analytics"""
        try:
            if not self.es.indices.exists(index="search_analytics"):
                return
            
            # Get slow queries
            result = self.es.search(index="search_analytics", body={
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "execution_time_ms": {
                                        "gte": 1000
                                    }
                                }
                            },
                            {
                                "range": {
                                    "timestamp": {
                                        "gte": "now-24h"
                                    }
                                }
                            }
                        ]
                    }
                },
                "sort": [
                    {
                        "execution_time_ms": {
                            "order": "desc"
                        }
                    }
                ],
                "size": 10
            })
            
            slow_queries = result.get('hits', {}).get('hits', [])
            
            for hit in slow_queries:
                query_data = hit['_source']
                logger.warning(f"Slow query detected: {query_data.get('query_text', 'N/A')[:100]}...")
                logger.info(f"  Execution time: {query_data.get('execution_time_ms', 0)}ms")
                logger.info(f"  Results count: {query_data.get('results_count', 0)}")
                logger.info(f"  Index: {query_data.get('index_name', 'N/A')}")
        
        except Exception as e:
            logger.error(f"Error analyzing slow queries: {str(e)}")
    
    def _optimize_query_templates(self):
        """Optimize search query templates"""
        try:
            # Update search templates with optimizations
            templates = {
                "forum_search": {
                    "template": {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "multi_match": {
                                            "query": "{{query_string}}",
                                            "fields": [
                                                "title^3",
                                                "content^2",
                                                "author^1.5",
                                                "tags^2",
                                                "category_name^1.5"
                                            ],
                                            "type": "best_fields",
                                            "fuzziness": "AUTO",
                                            "operator": "and"
                                        }
                                    }
                                ],
                                "filter": [
                                    {
                                        "term": {
                                            "status": "published"
                                        }
                                    }
                                ],
                                "should": [
                                    {
                                        "term": {
                                            "is_pinned": true
                                        }
                                    },
                                    {
                                        "term": {
                                            "is_featured": true
                                        }
                                    }
                                ],
                                "minimum_should_match": "75%"
                            }
                        },
                        "highlight": {
                            "fields": {
                                "title": {},
                                "content": {
                                    "fragment_size": 150,
                                    "number_of_fragments": 3,
                                    "pre_tags": ["<mark>"],
                                    "post_tags": ["</mark>"]
                                }
                            }
                        },
                        "sort": [
                            {
                                "_score": {
                                    "order": "desc"
                                }
                            },
                            {
                                "created_at": {
                                    "order": "desc"
                                }
                            }
                        ],
                        "size": 20,
                        "timeout": "30s"
                    }
                }
            }
            
            for template_name, template in templates.items():
                try:
                    self.es.put_script(id=template_name, body=template)
                    logger.info(f"Updated search template: {template_name}")
                except Exception as e:
                    logger.warning(f"Failed to update template {template_name}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error optimizing query templates: {str(e)}")
    
    def _update_search_analytics(self):
        """Update search analytics with optimization recommendations"""
        try:
            if not self.es.indices.exists(index="search_analytics"):
                return
            
            # Create optimization recommendations index
            if not self.es.indices.exists(index="search_optimization"):
                self.es.indices.create(index="search_optimization", body={
                    "mappings": {
                        "properties": {
                            "recommendation_type": {"type": "keyword"},
                            "description": {"type": "text"},
                            "impact": {"type": "keyword"},
                            "priority": {"type": "keyword"},
                            "created_at": {"type": "date"},
                            "status": {"type": "keyword"}
                        }
                    }
                })
            
            # Add optimization recommendations
            recommendations = [
                {
                    "recommendation_type": "query_optimization",
                    "description": "Consider using more specific queries to reduce execution time",
                    "impact": "high",
                    "priority": "medium",
                    "created_at": datetime.utcnow(),
                    "status": "pending"
                },
                {
                    "recommendation_type": "index_optimization",
                    "description": "Consider optimizing index mappings for better search performance",
                    "impact": "medium",
                    "priority": "low",
                    "created_at": datetime.utcnow(),
                    "status": "pending"
                }
            ]
            
            for rec in recommendations:
                self.es.index(index="search_optimization", body=rec)
            
            logger.info("Added search optimization recommendations")
        
        except Exception as e:
            logger.error(f"Error updating search analytics: {str(e)}")
    
    def _calculate_query_improvement(self, metrics_before: Dict[str, Any], metrics_after: Dict[str, Any]) -> float:
        """Calculate query improvement percentage"""
        try:
            improvements = []
            
            # Compare average execution time
            if 'avg_execution_time_ms' in metrics_before and 'avg_execution_time_ms' in metrics_after:
                before = metrics_before['avg_execution_time_ms']
                after = metrics_after['avg_execution_time_ms']
                if before > 0:
                    improvement = ((before - after) / before) * 100
                    improvements.append(improvement)
            
            # Compare slow query rate
            if 'slow_query_rate' in metrics_before and 'slow_query_rate' in metrics_after:
                before = metrics_before['slow_query_rate']
                after = metrics_after['slow_query_rate']
                if before > 0:
                    improvement = ((before - after) / before) * 100
                    improvements.append(improvement)
            
            return sum(improvements) / len(improvements) if improvements else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating query improvement: {str(e)}")
            return 0.0


class CacheOptimizer:
    """Cache performance optimizer"""
    
    def __init__(self, es_config: Dict[str, Any]):
        self.es_config = es_config
        self.es = Elasticsearch([{
            'host': es_config['host'],
            'port': es_config['port'],
            'username': es_config.get('username'),
            'password': es_config.get('password')
        }])
    
    def optimize_cache(self) -> OptimizationResult:
        """Optimize cache performance"""
        try:
            metrics_before = self._collect_cache_metrics()
            
            # Perform cache optimizations
            self._optimize_query_cache()
            self._optimize_field_data_cache()
            self._optimize_request_cache()
            self._clear_stale_cache()
            
            metrics_after = self._collect_cache_metrics()
            improvement = self._calculate_cache_improvement(metrics_before, metrics_after)
            
            return OptimizationResult(
                optimization_type=OptimizationType.CACHE,
                success=True,
                message="Cache optimization completed successfully",
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                improvement_percentage=improvement,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {str(e)}")
            return OptimizationResult(
                optimization_type=OptimizationType.CACHE,
                success=False,
                message=f"Cache optimization failed: {str(e)}",
                metrics_before={},
                metrics_after={},
                improvement_percentage=0.0,
                timestamp=datetime.utcnow()
            )
    
    def _collect_cache_metrics(self) -> Dict[str, Any]:
        """Collect cache performance metrics"""
        metrics = {}
        
        try:
            # Get cache stats
            stats = self.es.indices.stats(metric=['cache'])
            
            if stats['indices']:
                total_hits = 0
                total_misses = 0
                total_evictions = 0
                total_cache_size = 0
                
                for index_stats in stats['indices'].values():
                    cache_stats = index_stats.get('total', {})
                    
                    # Query cache
                    query_cache = cache_stats.get('query_cache', {})
                    total_hits += query_cache.get('hit_count', 0)
                    total_misses += query_cache.get('miss_count', 0)
                    total_evictions += query_cache.get('evictions', 0)
                    total_cache_size += query_cache.get('cache_size', 0)
                    
                    # Request cache
                    request_cache = cache_stats.get('request_cache', {})
                    total_hits += request_cache.get('hit_count', 0)
                    total_misses += request_cache.get('miss_count', 0)
                    total_evictions += request_cache.get('evictions', 0)
                    total_cache_size += request_cache.get('cache_size', 0)
                    
                    # Field data cache
                    field_data = cache_stats.get('fielddata', {})
                    total_evictions += field_data.get('evictions', 0)
                    total_cache_size += field_data.get('memory_size_in_bytes', 0)
                
                total_requests = total_hits + total_misses
                metrics['hit_rate'] = (total_hits / total_requests * 100) if total_requests > 0 else 0
                metrics['total_evictions'] = total_evictions
                metrics['total_cache_size_bytes'] = total_cache_size
                metrics['total_cache_size_mb'] = total_cache_size / 1024 / 1024
        
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {str(e)}")
        
        return metrics
    
    def _optimize_query_cache(self):
        """Optimize query cache"""
        try:
            # Update query cache settings
            settings = {
                "persistent": {
                    "indices.queries.cache.size": "10%",
                    "indices.queries.cache.expire": "1h"
                }
            }
            
            self.es.cluster.put_settings(body=settings)
            logger.info("Optimized query cache settings")
        
        except Exception as e:
            logger.error(f"Error optimizing query cache: {str(e)}")
    
    def _optimize_field_data_cache(self):
        """Optimize field data cache"""
        try:
            # Update field data cache settings
            settings = {
                "persistent": {
                    "indices.fielddata.cache.size": "30%",
                    "indices.fielddata.cache.expire": "1h"
                }
            }
            
            self.es.cluster.put_settings(body=settings)
            logger.info("Optimized field data cache settings")
        
        except Exception as e:
            logger.error(f"Error optimizing field data cache: {str(e)}")
    
    def _optimize_request_cache(self):
        """Optimize request cache"""
        try:
            # Update request cache settings
            settings = {
                "persistent": {
                    "indices.requests.cache.size": "1%",
                    "indices.requests.cache.expire": "1h"
                }
            }
            
            self.es.cluster.put_settings(body=settings)
            logger.info("Optimized request cache settings")
        
        except Exception as e:
            logger.error(f"Error optimizing request cache: {str(e)}")
    
    def _clear_stale_cache(self):
        """Clear stale cache entries"""
        try:
            # Clear caches if hit rates are low
            metrics = self._collect_cache_metrics()
            
            if metrics.get('hit_rate', 0) < 50:
                self.es.indices.clear_cache(index='_all', request=True)
                logger.info("Cleared all caches due to low hit rate")
        
        except Exception as e:
            logger.error(f"Error clearing stale cache: {str(e)}")
    
    def _calculate_cache_improvement(self, metrics_before: Dict[str, Any], metrics_after: Dict[str, Any]) -> float:
        """Calculate cache improvement percentage"""
        try:
            if 'hit_rate' in metrics_before and 'hit_rate' in metrics_after:
                before = metrics_before['hit_rate']
                after = metrics_after['hit_rate']
                if before > 0:
                    return ((after - before) / before) * 100
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating cache improvement: {str(e)}")
            return 0.0


class PerformanceOptimizer:
    """Main performance optimization orchestrator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.es_config = config.get('elasticsearch', {})
        
        # Initialize optimizers
        self.es_optimizer = ElasticsearchOptimizer(self.es_config)
        self.query_optimizer = QueryOptimizer(self.es_config)
        self.cache_optimizer = CacheOptimizer(self.es_config)
    
    def run_optimization(self) -> List[OptimizationResult]:
        """Run all performance optimizations"""
        results = []
        
        logger.info("Starting search performance optimization...")
        
        # Elasticsearch optimization
        logger.info("Running Elasticsearch optimization...")
        result = self.es_optimizer.optimize_elasticsearch()
        results.append(result)
        logger.info(f"Elasticsearch optimization: {result.message}")
        
        # Query optimization
        logger.info("Running query optimization...")
        result = self.query_optimizer.optimize_queries()
        results.append(result)
        logger.info(f"Query optimization: {result.message}")
        
        # Cache optimization
        logger.info("Running cache optimization...")
        result = self.cache_optimizer.optimize_cache()
        results.append(result)
        logger.info(f"Cache optimization: {result.message}")
        
        # Generate summary
        self._generate_optimization_summary(results)
        
        return results
    
    def _generate_optimization_summary(self, results: List[OptimizationResult]):
        """Generate optimization summary report"""
        logger.info("Search Performance Optimization Summary:")
        logger.info("=" * 50)
        
        for result in results:
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            improvement = f"{result.improvement_percentage:.2f}%" if result.improvement_percentage > 0 else "No improvement"
            logger.info(f"{result.optimization_type.value.upper()}: {status} - {improvement}")
            logger.info(f"  Message: {result.message}")
        
        # Calculate overall improvement
        successful_results = [r for r in results if r.success]
        if successful_results:
            overall_improvement = sum([r.improvement_percentage for r in successful_results]) / len(successful_results)
            logger.info(f"Overall improvement: {overall_improvement:.2f}%")
        
        logger.info("=" * 50)


def main():
    """Main function to run performance optimization"""
    # Load configuration
    config = {
        'elasticsearch': {
            'host': 'localhost',
            'port': 9200,
            'username': None,
            'password': None
        }
    }
    
    # Run optimization
    optimizer = PerformanceOptimizer(config)
    results = optimizer.run_optimization()
    
    # Exit with appropriate code
    failed_count = sum(1 for r in results if not r.success)
    if failed_count > 0:
        logger.error(f"{failed_count} optimizations failed")
        sys.exit(1)
    else:
        logger.info("All optimizations completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
