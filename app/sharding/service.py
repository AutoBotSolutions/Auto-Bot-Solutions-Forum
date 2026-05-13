"""
Database Sharding Service

Comprehensive database sharding service for shard management, cross-shard queries,
shard failover, and load balancing for the Auto Bot Solutions Forum.
"""

import logging
import json
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from flask import current_app
from sqlalchemy import and_, or_, desc, func
from app import db
from app.sharding.models import ShardCluster, Shard, CrossShardQuery, ShardFailover

logger = logging.getLogger(__name__)

class DatabaseShardingService:
    """Comprehensive database sharding service"""
    
    def __init__(self):
        self.enabled = current_app.config.get('DATABASE_SHARDING_ENABLED', True)
        self.cross_shard_queries_enabled = current_app.config.get('CROSS_SHARD_QUERIES_ENABLED', True)
        self.failover_enabled = current_app.config.get('SHARD_FAILOVER_ENABLED', True)
        self.load_balancing_enabled = current_app.config.get('LOAD_BALANCING_ENABLED', True)
        self.shard_connections = {}  # shard_id -> connection pool
        self.cluster_connections = {}  # cluster_id -> cluster connection info
        self.load_balancer = None
        self._initialize_load_balancer()
    
    def _initialize_load_balancer(self):
        """Initialize load balancer"""
        if self.load_balancing_enabled:
            self.load_balancer = LoadBalancer()
    
    def create_shard_cluster(self, cluster_name, cluster_type, database_type, sharding_strategy,
                            shard_key=None, shard_count=1, cluster_config=None, connection_config=None,
                            shard_config=None, load_balancing_enabled=True, load_balancing_strategy='round_robin',
                            failover_enabled=True, failover_strategy='automatic', metadata=None):
        """Create a new shard cluster"""
        if not self.enabled:
            return None
        
        try:
            cluster = ShardCluster.create_cluster(
                cluster_name=cluster_name,
                cluster_type=cluster_type,
                database_type=database_type,
                sharding_strategy=sharding_strategy,
                shard_key=shard_key,
                shard_count=shard_count,
                cluster_config=cluster_config,
                connection_config=connection_config,
                shard_config=shard_config,
                load_balancing_enabled=load_balancing_enabled,
                load_balancing_strategy=load_balancing_strategy,
                failover_enabled=failover_enabled,
                failover_strategy=failover_strategy,
                metadata=metadata
            )
            
            # Initialize cluster connections
            self._initialize_cluster_connections(cluster)
            
            return cluster
            
        except Exception as e:
            logger.error(f"Error creating shard cluster {cluster_name}: {str(e)}")
            return None
    
    def _initialize_cluster_connections(self, cluster):
        """Initialize connections for a cluster"""
        try:
            # This would initialize database connections for the cluster
            # For now, just log the initialization
            logger.info(f"Initialized connections for cluster {cluster.cluster_name}")
            
            # Update cluster status
            cluster.update_status('active', 'healthy')
            
        except Exception as e:
            logger.error(f"Error initializing connections for cluster {cluster.cluster_name}: {str(e)}")
            cluster.update_status('error', 'unhealthy')
            raise
    
    def add_shard_to_cluster(self, cluster_id, shard_name, shard_type, host, port, database, username,
                           password_encrypted=None, shard_config=None, connection_pool_config=None,
                           range_start=None, range_end=None, weight=1, priority=1, metadata=None):
        """Add a shard to a cluster"""
        if not self.enabled:
            return None
        
        try:
            shard = Shard.create_shard(
                cluster_id=cluster_id,
                shard_name=shard_name,
                shard_type=shard_type,
                host=host,
                port=port,
                database=database,
                username=username,
                password_encrypted=password_encrypted,
                shard_config=shard_config,
                connection_pool_config=connection_pool_config,
                range_start=range_start,
                range_end=range_end,
                weight=weight,
                priority=priority,
                metadata=metadata
            )
            
            # Initialize shard connection
            self._initialize_shard_connection(shard)
            
            # Update cluster metrics
            cluster = ShardCluster.query.get(cluster_id)
            if cluster:
                shards = Shard.get_shards_by_cluster(cluster_id)
                cluster.update_metrics(total_shards=len(shards))
            
            return shard
            
        except Exception as e:
            logger.error(f"Error adding shard {shard_name} to cluster {cluster_id}: {str(e)}")
            return None
    
    def _initialize_shard_connection(self, shard):
        """Initialize connection for a shard"""
        try:
            # This would initialize the actual database connection for the shard
            # For now, just log the initialization
            logger.info(f"Initialized connection for shard {shard.shard_name}")
            
            # Update shard status
            shard.update_status('active', 'healthy', 'connected')
            
        except Exception as e:
            logger.error(f"Error initializing connection for shard {shard.shard_name}: {str(e)}")
            shard.update_status('error', 'unhealthy', 'error')
            raise
    
    def execute_cross_shard_query(self, cluster_id, query_type, query_category, query_text,
                                 query_params=None, target_shards=None, shard_strategy='all',
                                 execution_strategy='parallel', user_id=None, session_id=None,
                                 ip_address=None):
        """Execute cross-shard query"""
        if not self.cross_shard_queries_enabled:
            return None
        
        try:
            # Create cross-shard query record
            query = CrossShardQuery.create_query(
                cluster_id=cluster_id,
                query_type=query_type,
                query_category=query_category,
                query_text=query_text,
                query_params=query_params,
                target_shards=target_shards,
                shard_strategy=shard_strategy,
                execution_strategy=execution_strategy,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address
            )
            
            # Start query execution
            query.start_execution()
            
            # Execute query based on strategy
            if execution_strategy == 'parallel':
                success = self._execute_parallel_query(query)
            elif execution_strategy == 'sequential':
                success = self._execute_sequential_query(query)
            elif execution_strategy == 'hybrid':
                success = self._execute_hybrid_query(query)
            else:
                success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing cross-shard query: {str(e)}")
            return None
    
    def _execute_parallel_query(self, query):
        """Execute query in parallel across shards"""
        try:
            start_time = time.time()
            
            # Get target shards
            target_shards = self._get_target_shards(query)
            
            if not target_shards:
                query.fail_execution("No target shards found")
                return False
            
            # Execute query on all shards in parallel
            shard_results = {}
            shard_execution_times = {}
            total_records_affected = 0
            
            # Use threading for parallel execution
            threads = []
            results = {}
            
            for shard in target_shards:
                thread = threading.Thread(
                    target=self._execute_shard_query,
                    args=(shard, query, results)
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Collect results
            for shard_id, result in results.items():
                if result['success']:
                    shard_results[shard_id] = result['data']
                    shard_execution_times[shard_id] = result['execution_time']
                    total_records_affected += result.get('records_affected', 0)
                else:
                    shard_results[shard_id] = None
                    shard_execution_times[shard_id] = result['execution_time']
            
            # Aggregate results
            aggregated_result = self._aggregate_results(query, shard_results)
            
            # Complete query
            total_execution_time = (time.time() - start_time) * 1000
            query.complete_execution(
                total_execution_time_ms=total_execution_time,
                shard_execution_times=shard_execution_times,
                total_records_affected=total_records_affected
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing parallel query: {str(e)}")
            query.fail_execution(str(e))
            return False
    
    def _execute_sequential_query(self, query):
        """Execute query sequentially across shards"""
        try:
            start_time = time.time()
            
            # Get target shards
            target_shards = self._get_target_shards(query)
            
            if not target_shards:
                query.fail_execution("No target shards found")
                return False
            
            # Execute query on shards sequentially
            shard_results = {}
            shard_execution_times = {}
            total_records_affected = 0
            
            for shard in target_shards:
                result = self._execute_single_shard_query(shard, query)
                shard_id = shard.shard_id
                
                if result['success']:
                    shard_results[shard_id] = result['data']
                    shard_execution_times[shard_id] = result['execution_time']
                    total_records_affected += result.get('records_affected', 0)
                else:
                    shard_results[shard_id] = None
                    shard_execution_times[shard_id] = result['execution_time']
            
            # Aggregate results
            aggregated_result = self._aggregate_results(query, shard_results)
            
            # Complete query
            total_execution_time = (time.time() - start_time) * 1000
            query.complete_execution(
                total_execution_time_ms=total_execution_time,
                shard_execution_times=shard_execution_times,
                total_records_affected=total_records_affected
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing sequential query: {str(e)}")
            query.fail_execution(str(e))
            return False
    
    def _execute_hybrid_query(self, query):
        """Execute query using hybrid strategy"""
        try:
            # For now, use parallel execution
            return self._execute_parallel_query(query)
            
        except Exception as e:
            logger.error(f"Error executing hybrid query: {str(e)}")
            query.fail_execution(str(e))
            return False
    
    def _execute_shard_query(self, shard, query, results):
        """Execute query on a single shard (for parallel execution)"""
        try:
            result = self._execute_single_shard_query(shard, query)
            results[shard.shard_id] = result
            
        except Exception as e:
            logger.error(f"Error executing query on shard {shard.shard_name}: {str(e)}")
            results[shard.shard_id] = {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }
    
    def _execute_single_shard_query(self, shard, query):
        """Execute query on a single shard"""
        try:
            start_time = time.time()
            
            # This would execute the actual query on the shard database
            # For now, simulate the execution
            
            # Simulate query execution time
            execution_time_ms = 50 + (hash(query.query_text) % 100)  # Random between 50-150ms
            
            # Simulate records affected
            records_affected = hash(query.query_text) % 1000  # Random between 0-999
            
            # Simulate result data
            result_data = {
                'shard_id': shard.shard_id,
                'shard_name': shard.shard_name,
                'records': records_affected,
                'data': f"Simulated result from {shard.shard_name}"
            }
            
            return {
                'success': True,
                'data': result_data,
                'execution_time': execution_time_ms,
                'records_affected': records_affected
            }
            
        except Exception as e:
            logger.error(f"Error executing single shard query: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0,
                'records_affected': 0
            }
    
    def _get_target_shards(self, query):
        """Get target shards for a query"""
        try:
            cluster = ShardCluster.query.get(query.cluster_id)
            if not cluster:
                return []
            
            if query.shard_strategy == 'all':
                # Get all active shards
                return Shard.get_active_shards(query.cluster_id)
            elif query.shard_strategy == 'specific':
                # Get specific shards from target_shards list
                target_shard_ids = query.target_shards or []
                return Shard.query.filter(
                    Shard.cluster_id == query.cluster_id,
                    Shard.shard_id.in_(target_shard_ids),
                    Shard.status == 'active'
                ).all()
            elif query.shard_strategy == 'intelligent':
                # Use intelligent shard selection based on query analysis
                return self._select_intelligent_shards(cluster, query)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting target shards: {str(e)}")
            return []
    
    def _select_intelligent_shards(self, cluster, query):
        """Select shards intelligently based on query analysis"""
        try:
            # This would implement intelligent shard selection
            # For now, return all active shards
            return Shard.get_active_shards(cluster.id)
            
        except Exception as e:
            logger.error(f"Error selecting intelligent shards: {str(e)}")
            return []
    
    def _aggregate_results(self, query, shard_results):
        """Aggregate results from multiple shards"""
        try:
            # This would implement result aggregation based on query type
            # For now, just combine the results
            aggregated_data = {
                'query_id': query.query_id,
                'shard_count': len(shard_results),
                'successful_shards': len([r for r in shard_results.values() if r is not None]),
                'results': []
            }
            
            for shard_id, result in shard_results.items():
                if result:
                    aggregated_data['results'].append(result)
            
            return aggregated_data
            
        except Exception as e:
            logger.error(f"Error aggregating results: {str(e)}")
            return None
    
    def create_shard_failover(self, cluster_id, failover_type, failover_reason, failed_shard_id=None,
                           promoted_shard_id=None, failover_config=None, recovery_config=None, metadata=None):
        """Create a shard failover"""
        if not self.failover_enabled:
            return None
        
        try:
            failover = ShardFailover.create_failover(
                cluster_id=cluster_id,
                failover_type=failover_type,
                failover_reason=failover_reason,
                failed_shard_id=failed_shard_id,
                promoted_shard_id=promoted_shard_id,
                failover_config=failover_config,
                recovery_config=recovery_config,
                metadata=metadata
            )
            
            return failover
            
        except Exception as e:
            logger.error(f"Error creating shard failover: {str(e)}")
            return None
    
    def execute_shard_failover(self, failover_id):
        """Execute shard failover"""
        if not self.failover_enabled:
            return False
        
        try:
            failover = ShardFailover.query.get(failover_id)
            if not failover:
                return False
            
            failover.start_failover()
            
            # Execute failover based on type
            if failover.failover_type == 'automatic':
                success = self._execute_automatic_failover(failover)
            elif failover.failover_type == 'manual':
                success = self._execute_manual_failover(failover)
            elif failover.failover_type == 'scheduled':
                success = self._execute_scheduled_failover(failover)
            else:
                success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing shard failover {failover_id}: {str(e)}")
            return False
    
    def _execute_automatic_failover(self, failover):
        """Execute automatic failover"""
        try:
            # Get cluster and failed shard
            cluster = ShardCluster.query.get(failover.cluster_id)
            if not cluster:
                failover.fail_failover("Cluster not found")
                return False
            
            failed_shard = None
            if failover.failed_shard_id:
                failed_shard = Shard.query.get(failover.failed_shard_id)
            
            if not failed_shard:
                failover.fail_failover("Failed shard not found")
                return False
            
            # Find suitable shard for failover
            available_shards = Shard.query.filter(
                Shard.cluster_id == failover.cluster_id,
                Shard.status == 'active',
                Shard.shard_id != failover.failed_shard_id
            ).order_by(Shard.priority.asc()).all()
            
            if not available_shards:
                failover.fail_failover("No available shards for failover")
                return False
            
            # Select best shard (highest priority)
            best_shard = available_shards[0]
            
            # Update failed shard status
            failed_shard.update_status('inactive', 'unhealthy', 'disconnected')
            
            # Update failover with promoted shard
            failover.promoted_shard_id = best_shard.shard_id
            db.session.commit()
            
            # Complete failover
            failover.complete_failover(
                affected_connections=failed_shard.active_connections,
                lost_connections=failed_shard.active_connections,
                recovered_connections=best_shard.active_connections
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing automatic failover: {str(e)}")
            failover.fail_failover(str(e))
            return False
    
    def _execute_manual_failover(self, failover):
        """Execute manual failover"""
        try:
            # Manual failover uses specified promoted shard
            if not failover.promoted_shard_id:
                failover.fail_failover("Promoted shard not specified for manual failover")
                return False
            
            promoted_shard = Shard.query.get(failover.promoted_shard_id)
            if not promoted_shard:
                failover.fail_failover("Promoted shard not found")
                return False
            
            # Update failed shard if specified
            if failover.failed_shard_id:
                failed_shard = Shard.query.get(failover.failed_shard_id)
                if failed_shard:
                    failed_shard.update_status('inactive', 'unhealthy', 'disconnected')
            
            # Complete failover
            failover.complete_failover()
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing manual failover: {str(e)}")
            failover.fail_failover(str(e))
            return False
    
    def _execute_scheduled_failover(self, failover):
        """Execute scheduled failover"""
        try:
            # Scheduled failover is similar to manual but with preparation
            return self._execute_manual_failover(failover)
            
        except Exception as e:
            logger.error(f"Error executing scheduled failover: {str(e)}")
            failover.fail_failover(str(e))
            return False
    
    def get_shard_health(self, cluster_id):
        """Get shard health status for a cluster"""
        try:
            cluster = ShardCluster.query.get(cluster_id)
            if not cluster:
                return None
            
            # Get shards for the cluster
            shards = Shard.get_shards_by_cluster(cluster_id)
            
            shard_health = []
            total_connections = 0
            active_connections = 0
            healthy_shards = 0
            
            for shard in shards:
                health_info = {
                    'shard_id': shard.shard_id,
                    'shard_name': shard.shard_name,
                    'shard_type': shard.shard_type,
                    'status': shard.status,
                    'health_status': shard.health_status,
                    'connection_status': shard.connection_status,
                    'total_connections': shard.total_connections,
                    'active_connections': shard.active_connections,
                    'query_per_second': shard.query_per_second,
                    'avg_query_time_ms': shard.avg_query_time_ms,
                    'total_records': shard.total_records,
                    'data_size_bytes': shard.data_size_bytes,
                    'weight': shard.weight,
                    'priority': shard.priority
                }
                shard_health.append(health_info)
                
                total_connections += shard.total_connections
                active_connections += shard.active_connections
                if shard.health_status == 'healthy':
                    healthy_shards += 1
            
            return {
                'cluster_id': cluster_id,
                'cluster_name': cluster.cluster_name,
                'cluster_status': cluster.status,
                'cluster_health_status': cluster.health_status,
                'total_shards': len(shards),
                'healthy_shards': healthy_shards,
                'unhealthy_shards': len(shards) - healthy_shards,
                'total_connections': total_connections,
                'active_connections': active_connections,
                'shards': shard_health
            }
            
        except Exception as e:
            logger.error(f"Error getting shard health {cluster_id}: {str(e)}")
            return None
    
    def get_cluster_metrics(self, cluster_id):
        """Get cluster performance metrics"""
        try:
            cluster = ShardCluster.query.get(cluster_id)
            if not cluster:
                return None
            
            # Get shards for the cluster
            shards = Shard.get_shards_by_cluster(cluster_id)
            
            # Calculate aggregate metrics
            total_connections = sum(shard.total_connections for shard in shards)
            active_connections = sum(shard.active_connections for shard in shards)
            avg_query_time = sum(shard.avg_query_time_ms for shard in shards) / len(shards) if shards else 0
            total_records = sum(shard.total_records for shard in shards)
            total_data_size = sum(shard.data_size_bytes for shard in shards)
            total_index_size = sum(shard.index_size_bytes for shard in shards)
            
            # Get query statistics
            query_stats = CrossShardQuery.get_query_stats(cluster_id, hours=1)
            
            return {
                'cluster_id': cluster_id,
                'cluster_name': cluster.cluster_name,
                'timestamp': datetime.utcnow().isoformat(),
                'connections': {
                    'total_connections': total_connections,
                    'active_connections': active_connections,
                    'utilization': active_connections / max(total_connections, 1)
                },
                'performance': {
                    'avg_query_time_ms': avg_query_time,
                    'query_per_second': cluster.query_per_second,
                    'total_records': total_records,
                    'data_size_bytes': total_data_size,
                    'index_size_bytes': total_index_size
                },
                'query_stats': query_stats,
                'shard_count': len(shards),
                'healthy_shards': len([s for s in shards if s.health_status == 'healthy'])
            }
            
        except Exception as e:
            logger.error(f"Error getting cluster metrics {cluster_id}: {str(e)}")
            return None
    
    def get_system_overview(self):
        """Get system-wide overview of all shard clusters"""
        try:
            clusters = ShardCluster.get_active_clusters()
            
            overview = {
                'total_clusters': len(clusters),
                'clusters': [],
                'system_metrics': {
                    'total_shards': 0,
                    'active_shards': 0,
                    'healthy_shards': 0,
                    'total_connections': 0,
                    'active_connections': 0,
                    'total_records': 0
                }
            }
            
            for cluster in clusters:
                cluster_info = {
                    'cluster_id': cluster.cluster_id,
                    'cluster_name': cluster.cluster_name,
                    'cluster_type': cluster.cluster_type,
                    'database_type': cluster.database_type,
                    'sharding_strategy': cluster.sharding_strategy,
                    'status': cluster.status,
                    'health_status': cluster.health_status,
                    'shard_count': cluster.total_shards,
                    'active_shards': cluster.active_shards,
                    'healthy_shards': cluster.healthy_shards,
                    'total_connections': cluster.total_connections,
                    'active_connections': cluster.active_connections,
                    'query_per_second': cluster.query_per_second
                }
                overview['clusters'].append(cluster_info)
                
                # Update system metrics
                shards = Shard.get_shards_by_cluster(cluster.cluster_id)
                overview['system_metrics']['total_shards'] += len(shards)
                overview['system_metrics']['active_shards'] += len([s for s in shards if s.status == 'active'])
                overview['system_metrics']['healthy_shards'] += len([s for s in shards if s.health_status == 'healthy'])
                overview['system_metrics']['total_connections'] += cluster.total_connections
                overview['system_metrics']['active_connections'] += cluster.active_connections
                overview['system_metrics']['total_records'] += sum(s.total_records for s in shards)
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting system overview: {str(e)}")
            return None


class LoadBalancer:
    """Load balancer for database shards"""
    
    def __init__(self):
        self.strategy = 'round_robin'
        self.current_index = 0
        self.shard_weights = {}
        self.shard_connections = {}
    
    def select_shard(self, shards, strategy=None):
        """Select a shard based on load balancing strategy"""
        if not shards:
            return None
        
        strategy = strategy or self.strategy
        
        if strategy == 'round_robin':
            return self._round_robin_selection(shards)
        elif strategy == 'least_connections':
            return self._least_connections_selection(shards)
        elif strategy == 'weighted':
            return self._weighted_selection(shards)
        else:
            return shards[0]
    
    def _round_robin_selection(self, shards):
        """Round robin selection"""
        shard = shards[self.current_index % len(shards)]
        self.current_index += 1
        return shard
    
    def _least_connections_selection(self, shards):
        """Least connections selection"""
        return min(shards, key=lambda s: s.active_connections)
    
    def _weighted_selection(self, shards):
        """Weighted selection"""
        total_weight = sum(shard.weight for shard in shards)
        if total_weight == 0:
            return shards[0]
        
        import random
        rand = random.random() * total_weight
        current_weight = 0
        
        for shard in shards:
            current_weight += shard.weight
            if rand <= current_weight:
                return shard
        
        return shards[-1]


# Global database sharding service instance
database_sharding_service = None

def get_database_sharding_service():
    """Get database sharding service instance (lazy initialization)"""
    global database_sharding_service
    if database_sharding_service is None:
        database_sharding_service = DatabaseShardingService()
    return database_sharding_service
