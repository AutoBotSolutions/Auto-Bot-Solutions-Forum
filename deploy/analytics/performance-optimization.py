#!/usr/bin/env python3
"""
Analytics Infrastructure Performance Optimization
Auto Bot Solutions Forum

This module provides performance optimization utilities for the analytics infrastructure,
including database optimization, query optimization, caching strategies, and resource management.
"""

import os
import sys
import time
import logging
import psutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

import psycopg2
import redis
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Optimization types"""
    DATABASE = "database"
    QUERY = "query"
    CACHE = "cache"
    SYSTEM = "system"
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


class DatabaseOptimizer:
    """Database performance optimizer"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.engine = self._create_engine()
    
    def _create_engine(self):
        """Create database engine with optimized settings"""
        connection_string = (
            f"postgresql://{self.db_config['username']}:{self.db_config['password']}"
            f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )
        
        engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False
        )
        return engine
    
    def optimize_database(self) -> OptimizationResult:
        """Optimize database performance"""
        try:
            metrics_before = self._collect_database_metrics()
            
            # Perform optimizations
            self._optimize_indexes()
            self._update_statistics()
            self._optimize_connections()
            self._cleanup_old_data()
            
            metrics_after = self._collect_database_metrics()
            
            # Calculate improvement
            improvement = self._calculate_improvement(metrics_before, metrics_after)
            
            return OptimizationResult(
                optimization_type=OptimizationType.DATABASE,
                success=True,
                message="Database optimization completed successfully",
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                improvement_percentage=improvement,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Database optimization failed: {str(e)}")
            return OptimizationResult(
                optimization_type=OptimizationType.DATABASE,
                success=False,
                message=f"Database optimization failed: {str(e)}",
                metrics_before={},
                metrics_after={},
                improvement_percentage=0.0,
                timestamp=datetime.utcnow()
            )
    
    def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database performance metrics"""
        metrics = {}
        
        try:
            with self.engine.connect() as conn:
                # Connection count
                result = conn.execute(text("SELECT count(*) as count FROM pg_stat_activity WHERE datname = current_database()"))
                metrics['connection_count'] = result.fetchone()[0]
                
                # Database size
                result = conn.execute(text("SELECT pg_database_size(current_database()) / 1024 / 1024 as size_mb"))
                metrics['database_size_mb'] = result.fetchone()[0]
                
                # Query performance
                result = conn.execute(text("""
                    SELECT 
                        avg(mean_exec_time) as avg_query_time,
                        max(mean_exec_time) as max_query_time,
                        sum(calls) as total_calls
                    FROM pg_stat_statements
                """))
                row = result.fetchone()
                metrics['avg_query_time_ms'] = row[0] if row[0] else 0
                metrics['max_query_time_ms'] = row[1] if row[1] else 0
                metrics['total_query_calls'] = row[2] if row[2] else 0
                
                # Index usage
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE schemaname IN ('analytics', 'pipeline', 'monitoring')
                """))
                indexes = result.fetchall()
                metrics['index_count'] = len(indexes)
                metrics['unused_indexes'] = len([idx for idx in indexes if idx[3] == 0])  # idx_scan = 0
                
                # Table statistics
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        n_live_tup,
                        n_dead_tup
                    FROM pg_stat_user_tables
                    WHERE schemaname IN ('analytics', 'pipeline', 'monitoring')
                """))
                tables = result.fetchall()
                metrics['table_count'] = len(tables)
                metrics['total_live_tuples'] = sum([row[4] for row in tables])
                metrics['total_dead_tuples'] = sum([row[5] for row in tables])
                
        except Exception as e:
            logger.error(f"Error collecting database metrics: {str(e)}")
        
        return metrics
    
    def _optimize_indexes(self):
        """Optimize database indexes"""
        try:
            with self.engine.connect() as conn:
                # Analyze index usage
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE schemaname IN ('analytics', 'pipeline', 'monitoring')
                    AND idx_scan = 0
                """))
                unused_indexes = result.fetchall()
                
                # Drop unused indexes (be careful in production)
                for index in unused_indexes:
                    schema, table, index_name = index[0], index[1], index[2]
                    logger.info(f"Found unused index: {schema}.{table}.{index_name}")
                    # Uncomment to actually drop unused indexes
                    # conn.execute(text(f"DROP INDEX IF EXISTS {schema}.{index_name}"))
                
                # Create missing indexes for frequently queried columns
                self._create_missing_indexes(conn)
                
        except Exception as e:
            logger.error(f"Error optimizing indexes: {str(e)}")
    
    def _create_missing_indexes(self, conn):
        """Create missing performance indexes"""
        indexes_to_create = [
            # User activity indexes
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_activity_user_timestamp "
             "ON analytics.user_activity(user_id, activity_timestamp)"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_activity_type_timestamp "
             "ON analytics.user_activity(activity_type, activity_timestamp)"),
            
            # Content analytics indexes
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_analytics_content_timestamp "
             "ON analytics.content_analytics(content_id, action_timestamp)"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_analytics_quality_score "
             "ON analytics.content_analytics(quality_score)"),
            
            # System metrics indexes
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_metrics_name_timestamp "
             "ON analytics.system_metrics(metric_name, metric_timestamp)"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_metrics_source_timestamp "
             "ON analytics.system_metrics(source, metric_timestamp)"),
            
            # Pipeline indexes
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pipeline_run_pipeline_run "
             "ON pipeline.pipeline_run(pipeline_id, run_status)"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pipeline_run_started_at "
             "ON pipeline.pipeline_run(started_at)"),
            
            # Monitoring indexes
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_anomaly_detection_type_detected "
             "ON monitoring.anomaly_detection(anomaly_type, detected_at)"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_anomaly_detection_status "
             "ON monitoring.anomaly_detection(status)")
        ]
        
        for index_sql in indexes_to_create:
            try:
                conn.execute(text(index_sql))
                logger.info(f"Created index: {index_sql}")
            except Exception as e:
                logger.warning(f"Failed to create index: {index_sql}, Error: {str(e)}")
    
    def _update_statistics(self):
        """Update database statistics"""
        try:
            with self.engine.connect() as conn:
                # Update table statistics
                result = conn.execute(text("""
                    SELECT schemaname, tablename 
                    FROM pg_tables 
                    WHERE schemaname IN ('analytics', 'pipeline', 'monitoring')
                """))
                tables = result.fetchall()
                
                for schema, table in tables:
                    try:
                        conn.execute(text(f"ANALYZE {schema}.{table}"))
                        logger.info(f"Updated statistics for {schema}.{table}")
                    except Exception as e:
                        logger.warning(f"Failed to analyze {schema}.{table}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error updating statistics: {str(e)}")
    
    def _optimize_connections(self):
        """Optimize database connection settings"""
        try:
            with self.engine.connect() as conn:
                # Check and optimize connection settings
                settings_to_check = [
                    ("shared_buffers", "256MB"),
                    ("effective_cache_size", "1GB"),
                    ("work_mem", "4MB"),
                    ("maintenance_work_mem", "64MB"),
                    ("checkpoint_completion_target", "0.9"),
                    ("wal_buffers", "16MB"),
                    ("default_statistics_target", "100")
                ]
                
                for setting, recommended_value in settings_to_check:
                    try:
                        result = conn.execute(text(f"SHOW {setting}"))
                        current_value = result.fetchone()[0]
                        logger.info(f"{setting}: {current_value} (recommended: {recommended_value})")
                    except Exception as e:
                        logger.warning(f"Could not check {setting}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error optimizing connections: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old data based on retention policies"""
        try:
            with self.engine.connect() as conn:
                # Clean up old system metrics (keep 30 days)
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                result = conn.execute(text("""
                    DELETE FROM analytics.system_metrics 
                    WHERE metric_timestamp < :cutoff_date
                """), {"cutoff_date": cutoff_date})
                deleted_count = result.rowcount
                logger.info(f"Cleaned up {deleted_count} old system metrics records")
                
                # Clean up old pipeline runs (keep 90 days)
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                result = conn.execute(text("""
                    DELETE FROM pipeline.pipeline_run 
                    WHERE created_at < :cutoff_date
                """), {"cutoff_date": cutoff_date})
                deleted_count = result.rowcount
                logger.info(f"Cleaned up {deleted_count} old pipeline run records")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
    
    def _calculate_improvement(self, metrics_before: Dict[str, Any], metrics_after: Dict[str, Any]) -> float:
        """Calculate improvement percentage"""
        try:
            improvements = []
            
            # Compare query times
            if 'avg_query_time_ms' in metrics_before and 'avg_query_time_ms' in metrics_after:
                before = metrics_before['avg_query_time_ms']
                after = metrics_after['avg_query_time_ms']
                if before > 0:
                    improvement = ((before - after) / before) * 100
                    improvements.append(improvement)
            
            # Compare unused indexes
            if 'unused_indexes' in metrics_before and 'unused_indexes' in metrics_after:
                before = metrics_before['unused_indexes']
                after = metrics_after['unused_indexes']
                if before > 0:
                    improvement = ((before - after) / before) * 100
                    improvements.append(improvement)
            
            return np.mean(improvements) if improvements else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating improvement: {str(e)}")
            return 0.0


class QueryOptimizer:
    """Query performance optimizer"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.engine = create_engine(
            f"postgresql://{db_config['username']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
    
    def optimize_slow_queries(self) -> OptimizationResult:
        """Optimize slow queries"""
        try:
            metrics_before = self._collect_query_metrics()
            
            # Identify and optimize slow queries
            slow_queries = self._identify_slow_queries()
            for query in slow_queries:
                self._optimize_query(query)
            
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
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        avg(mean_exec_time) as avg_time,
                        max(mean_exec_time) as max_time,
                        sum(calls) as total_calls,
                        sum(total_exec_time) as total_time
                    FROM pg_stat_statements
                """))
                row = result.fetchone()
                metrics['avg_query_time_ms'] = row[0] if row[0] else 0
                metrics['max_query_time_ms'] = row[1] if row[1] else 0
                metrics['total_query_calls'] = row[2] if row[2] else 0
                metrics['total_query_time_ms'] = row[3] if row[3] else 0
                
        except Exception as e:
            logger.error(f"Error collecting query metrics: {str(e)}")
        
        return metrics
    
    def _identify_slow_queries(self) -> List[Dict[str, Any]]:
        """Identify slow queries"""
        slow_queries = []
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        query,
                        mean_exec_time,
                        calls,
                        total_exec_time,
                        rows
                    FROM pg_stat_statements
                    WHERE mean_exec_time > 1000  -- queries taking more than 1 second
                    ORDER BY mean_exec_time DESC
                    LIMIT 10
                """))
                
                for row in result:
                    slow_queries.append({
                        'query': row[0],
                        'mean_time': row[1],
                        'calls': row[2],
                        'total_time': row[3],
                        'rows': row[4]
                    })
                    
        except Exception as e:
            logger.error(f"Error identifying slow queries: {str(e)}")
        
        return slow_queries
    
    def _optimize_query(self, query_info: Dict[str, Any]):
        """Optimize a specific query"""
        try:
            query = query_info['query']
            
            # Log the slow query for analysis
            logger.warning(f"Slow query detected: {query[:200]}...")
            logger.info(f"Mean execution time: {query_info['mean_time']:.2f}ms")
            logger.info(f"Total calls: {query_info['calls']}")
            
            # Analyze query plan
            self._analyze_query_plan(query)
            
        except Exception as e:
            logger.error(f"Error optimizing query: {str(e)}")
    
    def _analyze_query_plan(self, query: str):
        """Analyze query execution plan"""
        try:
            with self.engine.connect() as conn:
                # Get query plan
                result = conn.execute(text(f"EXPLAIN ANALYZE {query}"))
                plan_lines = [row[0] for row in result]
                
                # Analyze plan for optimization opportunities
                plan_text = '\n'.join(plan_lines)
                
                if 'Seq Scan' in plan_text:
                    logger.info("Query uses sequential scan - consider adding index")
                
                if 'Sort' in plan_text and 'LIMIT' not in query.upper():
                    logger.info("Query uses sort without limit - consider adding limit")
                
                if 'Nested Loop' in plan_text:
                    logger.info("Query uses nested loop - consider optimizing join order")
                
        except Exception as e:
            logger.error(f"Error analyzing query plan: {str(e)}")
    
    def _calculate_query_improvement(self, metrics_before: Dict[str, Any], metrics_after: Dict[str, Any]) -> float:
        """Calculate query improvement percentage"""
        try:
            if 'avg_query_time_ms' in metrics_before and 'avg_query_time_ms' in metrics_after:
                before = metrics_before['avg_query_time_ms']
                after = metrics_after['avg_query_time_ms']
                if before > 0:
                    return ((before - after) / before) * 100
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating query improvement: {str(e)}")
            return 0.0


class CacheOptimizer:
    """Cache performance optimizer"""
    
    def __init__(self, redis_config: Dict[str, Any]):
        self.redis_config = redis_config
        self.redis_client = redis.Redis(
            host=redis_config['host'],
            port=redis_config['port'],
            db=redis_config.get('db', 0),
            password=redis_config.get('password'),
            decode_responses=True
        )
    
    def optimize_cache(self) -> OptimizationResult:
        """Optimize cache performance"""
        try:
            metrics_before = self._collect_cache_metrics()
            
            # Perform cache optimizations
            self._optimize_memory_usage()
            self._optimize_key_patterns()
            self._cleanup_expired_keys()
            self._optimize_connection_pool()
            
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
            info = self.redis_client.info()
            
            metrics['used_memory_mb'] = info.get('used_memory', 0) / 1024 / 1024
            metrics['used_memory_peak_mb'] = info.get('used_memory_peak', 0) / 1024 / 1024
            metrics['connected_clients'] = info.get('connected_clients', 0)
            metrics['total_commands_processed'] = info.get('total_commands_processed', 0)
            metrics['keyspace_hits'] = info.get('keyspace_hits', 0)
            metrics['keyspace_misses'] = info.get('keyspace_misses', 0)
            metrics['expired_keys'] = info.get('expired_keys', 0)
            metrics['evicted_keys'] = info.get('evicted_keys', 0)
            
            # Calculate hit rate
            hits = metrics['keyspace_hits']
            misses = metrics['keyspace_misses']
            total = hits + misses
            metrics['hit_rate'] = (hits / total * 100) if total > 0 else 0
            
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {str(e)}")
        
        return metrics
    
    def _optimize_memory_usage(self):
        """Optimize Redis memory usage"""
        try:
            # Check memory usage
            info = self.redis_client.info()
            used_memory = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            
            if max_memory > 0:
                memory_usage = (used_memory / max_memory) * 100
                logger.info(f"Memory usage: {memory_usage:.2f}%")
                
                if memory_usage > 80:
                    logger.warning("High memory usage detected, consider increasing maxmemory or optimizing keys")
            
            # Optimize memory policies
            self.redis_client.config_set('maxmemory-policy', 'allkeys-lru')
            
        except Exception as e:
            logger.error(f"Error optimizing memory usage: {str(e)}")
    
    def _optimize_key_patterns(self):
        """Optimize key patterns and expiration"""
        try:
            # Analyze key patterns
            keys = self.redis_client.keys('*')
            key_patterns = {}
            
            for key in keys:
                pattern = key.split(':')[0] if ':' in key else 'default'
                key_patterns[pattern] = key_patterns.get(pattern, 0) + 1
            
            # Log key pattern statistics
            logger.info("Key pattern analysis:")
            for pattern, count in sorted(key_patterns.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {pattern}: {count} keys")
            
            # Set expiration for keys without TTL
            for key in keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -1:  # No expiration set
                    # Set reasonable TTL based on key pattern
                    if 'temp' in key or 'session' in key:
                        self.redis_client.expire(key, 3600)  # 1 hour
                    elif 'cache' in key:
                        self.redis_client.expire(key, 86400)  # 1 day
                    elif 'analytics' in key:
                        self.redis_client.expire(key, 1800)  # 30 minutes
            
        except Exception as e:
            logger.error(f"Error optimizing key patterns: {str(e)}")
    
    def _cleanup_expired_keys(self):
        """Clean up expired keys"""
        try:
            # Redis automatically cleans up expired keys, but we can force cleanup
            # This is more about monitoring and reporting
            info = self.redis_client.info()
            expired_keys = info.get('expired_keys', 0)
            evicted_keys = info.get('evicted_keys', 0)
            
            logger.info(f"Expired keys: {expired_keys}")
            logger.info(f"Evicted keys: {evicted_keys}")
            
            if evicted_keys > 0:
                logger.warning("Keys are being evicted - consider increasing memory or optimizing usage")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired keys: {str(e)}")
    
    def _optimize_connection_pool(self):
        """Optimize Redis connection pool"""
        try:
            # Check connection settings
            info = self.redis_client.info()
            connected_clients = info.get('connected_clients', 0)
            
            logger.info(f"Connected clients: {connected_clients}")
            
            # Optimize connection settings
            self.redis_client.config_set('timeout', 300)
            self.redis_client.config_set('tcp-keepalive', 60)
            self.redis_client.config_set('maxclients', 10000)
            
        except Exception as e:
            logger.error(f"Error optimizing connection pool: {str(e)}")
    
    def _calculate_cache_improvement(self, metrics_before: Dict[str, Any], metrics_after: Dict[str, Any]) -> float:
        """Calculate cache improvement percentage"""
        try:
            improvements = []
            
            # Compare hit rate
            if 'hit_rate' in metrics_before and 'hit_rate' in metrics_after:
                before = metrics_before['hit_rate']
                after = metrics_after['hit_rate']
                if before > 0:
                    improvement = ((after - before) / before) * 100
                    improvements.append(improvement)
            
            # Compare memory usage
            if 'used_memory_mb' in metrics_before and 'used_memory_mb' in metrics_after:
                before = metrics_before['used_memory_mb']
                after = metrics_after['used_memory_mb']
                if before > 0:
                    improvement = ((before - after) / before) * 100
                    improvements.append(improvement)
            
            return np.mean(improvements) if improvements else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating cache improvement: {str(e)}")
            return 0.0


class SystemOptimizer:
    """System resource optimizer"""
    
    def __init__(self):
        self.process = psutil.Process()
    
    def optimize_system(self) -> OptimizationResult:
        """Optimize system resources"""
        try:
            metrics_before = self._collect_system_metrics()
            
            # Perform system optimizations
            self._optimize_cpu_usage()
            self._optimize_memory_usage()
            self._optimize_disk_usage()
            self._optimize_network_usage()
            
            metrics_after = self._collect_system_metrics()
            improvement = self._calculate_system_improvement(metrics_before, metrics_after)
            
            return OptimizationResult(
                optimization_type=OptimizationType.SYSTEM,
                success=True,
                message="System optimization completed successfully",
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                improvement_percentage=improvement,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"System optimization failed: {str(e)}")
            return OptimizationResult(
                optimization_type=OptimizationType.SYSTEM,
                success=False,
                message=f"System optimization failed: {str(e)}",
                metrics_before={},
                metrics_after={},
                improvement_percentage=0.0,
                timestamp=datetime.utcnow()
            )
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics"""
        metrics = {}
        
        try:
            # CPU metrics
            metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
            metrics['cpu_count'] = psutil.cpu_count()
            metrics['load_avg'] = psutil.getloadavg()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics['memory_percent'] = memory.percent
            metrics['memory_available_gb'] = memory.available / 1024 / 1024 / 1024
            metrics['memory_used_gb'] = memory.used / 1024 / 1024 / 1024
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics['disk_percent'] = disk.percent
            metrics['disk_free_gb'] = disk.free / 1024 / 1024 / 1024
            metrics['disk_used_gb'] = disk.used / 1024 / 1024 / 1024
            
            # Network metrics
            network = psutil.net_io_counters()
            metrics['network_bytes_sent'] = network.bytes_sent
            metrics['network_bytes_recv'] = network.bytes_recv
            
            # Process metrics
            metrics['process_cpu_percent'] = self.process.cpu_percent()
            metrics['process_memory_mb'] = self.process.memory_info().rss / 1024 / 1024
            metrics['process_threads'] = self.process.num_threads()
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
        
        return metrics
    
    def _optimize_cpu_usage(self):
        """Optimize CPU usage"""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            logger.info(f"CPU usage: {cpu_percent}%")
            
            if cpu_percent > 80:
                logger.warning("High CPU usage detected")
                # Could implement CPU throttling or process prioritization here
                
        except Exception as e:
            logger.error(f"Error optimizing CPU usage: {str(e)}")
    
    def _optimize_memory_usage(self):
        """Optimize memory usage"""
        try:
            memory = psutil.virtual_memory()
            logger.info(f"Memory usage: {memory.percent}%")
            
            if memory.percent > 85:
                logger.warning("High memory usage detected")
                # Could implement memory cleanup or process termination here
                
        except Exception as e:
            logger.error(f"Error optimizing memory usage: {str(e)}")
    
    def _optimize_disk_usage(self):
        """Optimize disk usage"""
        try:
            disk = psutil.disk_usage('/')
            logger.info(f"Disk usage: {disk.percent}%")
            
            if disk.percent > 85:
                logger.warning("High disk usage detected")
                # Could implement disk cleanup or log rotation here
                
        except Exception as e:
            logger.error(f"Error optimizing disk usage: {str(e)}")
    
    def _optimize_network_usage(self):
        """Optimize network usage"""
        try:
            network = psutil.net_io_counters()
            logger.info(f"Network bytes sent: {network.bytes_sent}")
            logger.info(f"Network bytes received: {network.bytes_recv}")
            
        except Exception as e:
            logger.error(f"Error optimizing network usage: {str(e)}")
    
    def _calculate_system_improvement(self, metrics_before: Dict[str, Any], metrics_after: Dict[str, Any]) -> float:
        """Calculate system improvement percentage"""
        try:
            improvements = []
            
            # Compare CPU usage
            if 'cpu_percent' in metrics_before and 'cpu_percent' in metrics_after:
                before = metrics_before['cpu_percent']
                after = metrics_after['cpu_percent']
                if before > 0:
                    improvement = ((before - after) / before) * 100
                    improvements.append(improvement)
            
            # Compare memory usage
            if 'memory_percent' in metrics_before and 'memory_percent' in metrics_after:
                before = metrics_before['memory_percent']
                after = metrics_after['memory_percent']
                if before > 0:
                    improvement = ((before - after) / before) * 100
                    improvements.append(improvement)
            
            return np.mean(improvements) if improvements else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating system improvement: {str(e)}")
            return 0.0


class PerformanceOptimizer:
    """Main performance optimization orchestrator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_config = config.get('database', {})
        self.redis_config = config.get('redis', {})
        
        # Initialize optimizers
        self.db_optimizer = DatabaseOptimizer(self.db_config)
        self.query_optimizer = QueryOptimizer(self.db_config)
        self.cache_optimizer = CacheOptimizer(self.redis_config)
        self.system_optimizer = SystemOptimizer()
    
    def run_optimization(self) -> List[OptimizationResult]:
        """Run all performance optimizations"""
        results = []
        
        logger.info("Starting performance optimization...")
        
        # Database optimization
        logger.info("Running database optimization...")
        result = self.db_optimizer.optimize_database()
        results.append(result)
        logger.info(f"Database optimization: {result.message}")
        
        # Query optimization
        logger.info("Running query optimization...")
        result = self.query_optimizer.optimize_slow_queries()
        results.append(result)
        logger.info(f"Query optimization: {result.message}")
        
        # Cache optimization
        logger.info("Running cache optimization...")
        result = self.cache_optimizer.optimize_cache()
        results.append(result)
        logger.info(f"Cache optimization: {result.message}")
        
        # System optimization
        logger.info("Running system optimization...")
        result = self.system_optimizer.optimize_system()
        results.append(result)
        logger.info(f"System optimization: {result.message}")
        
        # Generate summary
        self._generate_optimization_summary(results)
        
        return results
    
    def _generate_optimization_summary(self, results: List[OptimizationResult]):
        """Generate optimization summary report"""
        logger.info("Performance Optimization Summary:")
        logger.info("=" * 50)
        
        for result in results:
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            improvement = f"{result.improvement_percentage:.2f}%" if result.improvement_percentage > 0 else "No improvement"
            logger.info(f"{result.optimization_type.value.upper()}: {status} - {improvement}")
            logger.info(f"  Message: {result.message}")
        
        # Calculate overall improvement
        successful_results = [r for r in results if r.success]
        if successful_results:
            overall_improvement = np.mean([r.improvement_percentage for r in successful_results])
            logger.info(f"Overall improvement: {overall_improvement:.2f}%")
        
        logger.info("=" * 50)


def main():
    """Main function to run performance optimization"""
    # Load configuration
    config = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'forum_analytics',
            'username': 'analytics_user',
            'password': 'analytics_password'
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
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
