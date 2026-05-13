"""
Distributed Cache Service

Comprehensive distributed cache service for Redis integration, cluster management,
cache synchronization, and failover handling for the Auto Bot Solutions Forum.
"""

import logging
import redis
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from flask import current_app
from sqlalchemy import and_, or_, desc, func
from app import db
from app.distributed_cache.models import CacheCluster, CacheNode, CacheSynchronization, CacheFailover

logger = logging.getLogger(__name__)

class DistributedCacheService:
    """Comprehensive distributed cache service for Redis cluster management"""
    
    def __init__(self):
        self.enabled = current_app.config.get('DISTRIBUTED_CACHE_ENABLED', True)
        self.redis_config = current_app.config.get('REDIS_CONFIG', {})
        self.cluster_config = current_app.config.get('CLUSTER_CONFIG', {})
        self.failover_config = current_app.config.get('FAILOVER_CONFIG', {})
        self.redis_clients = {}  # cluster_id -> Redis client
        self.cluster_connections = {}  # cluster_id -> connection info
        
    def create_cluster(self, cluster_name, cluster_type='redis', cluster_mode='cluster',
                      cluster_config=None, node_config=None, replication_factor=1,
                      shard_count=1, consistency_level='eventual'):
        """Create a new cache cluster"""
        if not self.enabled:
            return None
        
        try:
            cluster = CacheCluster.create_cluster(
                cluster_name=cluster_name,
                cluster_type=cluster_type,
                cluster_mode=cluster_mode,
                cluster_config=cluster_config,
                node_config=node_config,
                replication_factor=replication_factor,
                shard_count=shard_count,
                consistency_level=consistency_level
            )
            
            # Initialize Redis connection for the cluster
            self._initialize_cluster_connection(cluster)
            
            return cluster
            
        except Exception as e:
            logger.error(f"Error creating cache cluster {cluster_name}: {str(e)}")
            return None
    
    def _initialize_cluster_connection(self, cluster):
        """Initialize Redis connection for a cluster"""
        try:
            if cluster.cluster_mode == 'cluster':
                # Redis Cluster connection
                startup_nodes = []
                for node_config in cluster.cluster_config.get('nodes', []):
                    startup_nodes.append({
                        'host': node_config['host'],
                        'port': node_config['port']
                    })
                
                redis_client = redis.RedisCluster(
                    startup_nodes=startup_nodes,
                    decode_responses=True,
                    skip_full_coverage_check=True,
                    max_connections=cluster.cluster_config.get('max_connections', 100)
                )
            else:
                # Standalone Redis connection
                node_config = cluster.cluster_config.get('nodes', [{}])[0]
                redis_client = redis.Redis(
                    host=node_config.get('host', 'localhost'),
                    port=node_config.get('port', 6379),
                    decode_responses=True,
                    max_connections=cluster.cluster_config.get('max_connections', 100)
                )
            
            # Test connection
            redis_client.ping()
            
            self.redis_clients[cluster.cluster_id] = redis_client
            self.cluster_connections[cluster.cluster_id] = {
                'cluster': cluster,
                'client': redis_client,
                'last_check': datetime.utcnow()
            }
            
            logger.info(f"Initialized Redis connection for cluster {cluster.cluster_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Redis connection for cluster {cluster.cluster_name}: {str(e)}")
            raise
    
    def add_node_to_cluster(self, cluster_id, node_name, host, port, node_role='slave',
                           ssl_enabled=False, auth_enabled=False, shard_id=None, shard_slots=0,
                           master_node_id=None):
        """Add a node to a cache cluster"""
        if not self.enabled:
            return None
        
        try:
            node = CacheNode.create_node(
                cluster_id=cluster_id,
                node_name=node_name,
                host=host,
                port=port,
                node_role=node_role,
                ssl_enabled=ssl_enabled,
                auth_enabled=auth_enabled,
                shard_id=shard_id,
                shard_slots=shard_slots,
                master_node_id=master_node_id
            )
            
            # Update cluster metrics
            cluster = CacheCluster.query.get(cluster_id)
            if cluster:
                cluster.update_metrics(total_nodes=len(cluster.nodes))
            
            return node
            
        except Exception as e:
            logger.error(f"Error adding node {node_name} to cluster {cluster_id}: {str(e)}")
            return None
    
    def remove_node_from_cluster(self, node_id):
        """Remove a node from a cache cluster"""
        if not self.enabled:
            return None
        
        try:
            node = CacheNode.query.get(node_id)
            if not node:
                return None
            
            cluster_id = node.cluster_id
            db.session.delete(node)
            db.session.commit()
            
            # Update cluster metrics
            cluster = CacheCluster.query.get(cluster_id)
            if cluster:
                cluster.update_metrics(total_nodes=len(cluster.nodes))
            
            return node
            
        except Exception as e:
            logger.error(f"Error removing node {node_id}: {str(e)}")
            return None
    
    def get_redis_client(self, cluster_id):
        """Get Redis client for a cluster"""
        if cluster_id not in self.redis_clients:
            cluster = CacheCluster.query.get(cluster_id)
            if cluster:
                self._initialize_cluster_connection(cluster)
        
        return self.redis_clients.get(cluster_id)
    
    def set_cache(self, key, value, ttl=None, cluster_id=None, node_id=None):
        """Set cache value in distributed cache"""
        if not self.enabled:
            return False
        
        try:
            # Determine target cluster/node
            if cluster_id is None:
                # Use default cluster or select based on key
                cluster = CacheCluster.query.filter_by(status='active').first()
                if not cluster:
                    return False
                cluster_id = cluster.cluster_id
            
            redis_client = self.get_redis_client(cluster_id)
            if not redis_client:
                return False
            
            # Serialize value if needed
            if not isinstance(value, str):
                value = json.dumps(value)
            
            # Set cache with TTL
            if ttl:
                result = redis_client.setex(key, ttl, value)
            else:
                result = redis_client.set(key, value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def get_cache(self, key, cluster_id=None, node_id=None):
        """Get cache value from distributed cache"""
        if not self.enabled:
            return None
        
        try:
            # Determine target cluster/node
            if cluster_id is None:
                # Try to find key in any active cluster
                clusters = CacheCluster.query.filter_by(status='active').all()
                for cluster in clusters:
                    redis_client = self.get_redis_client(cluster.cluster_id)
                    if redis_client:
                        value = redis_client.get(key)
                        if value is not None:
                            # Try to deserialize
                            try:
                                return json.loads(value)
                            except json.JSONDecodeError:
                                return value
                
                return None
            else:
                redis_client = self.get_redis_client(cluster_id)
                if not redis_client:
                    return None
                
                value = redis_client.get(key)
                if value is not None:
                    # Try to deserialize
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def delete_cache(self, key, cluster_id=None, node_id=None):
        """Delete cache key from distributed cache"""
        if not self.enabled:
            return False
        
        try:
            # Determine target cluster/node
            if cluster_id is None:
                # Delete from all active clusters
                clusters = CacheCluster.query.filter_by(status='active').all()
                results = []
                for cluster in clusters:
                    redis_client = self.get_redis_client(cluster.cluster_id)
                    if redis_client:
                        result = redis_client.delete(key)
                        results.append(result)
                
                return any(results)
            else:
                redis_client = self.get_redis_client(cluster_id)
                if not redis_client:
                    return False
                
                return redis_client.delete(key)
                
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def clear_cluster_cache(self, cluster_id):
        """Clear all cache in a cluster"""
        if not self.enabled:
            return False
        
        try:
            redis_client = self.get_redis_client(cluster_id)
            if not redis_client:
                return False
            
            redis_client.flushdb()
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cluster {cluster_id} cache: {str(e)}")
            return False
    
    def create_synchronization(self, cluster_id, sync_type='incremental', sync_direction='bidirectional',
                             source_node_id=None, target_node_id=None, source_cluster_id=None,
                             target_cluster_id=None, sync_config=None, filter_patterns=None,
                             scheduled_at=None):
        """Create a cache synchronization"""
        if not self.enabled:
            return None
        
        try:
            sync = CacheSynchronization.create_synchronization(
                cluster_id=cluster_id,
                sync_type=sync_type,
                sync_direction=sync_direction,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                source_cluster_id=source_cluster_id,
                target_cluster_id=target_cluster_id,
                sync_config=sync_config,
                filter_patterns=filter_patterns,
                scheduled_at=scheduled_at
            )
            
            return sync
            
        except Exception as e:
            logger.error(f"Error creating synchronization: {str(e)}")
            return None
    
    def execute_synchronization(self, sync_id):
        """Execute cache synchronization"""
        if not self.enabled:
            return False
        
        try:
            sync = CacheSynchronization.query.get(sync_id)
            if not sync:
                return False
            
            sync.start_sync()
            
            # Get source and target Redis clients
            source_client = None
            target_client = None
            
            if sync.source_node_id:
                source_node = CacheNode.query.get(sync.source_node_id)
                source_client = self.get_redis_client(source_node.cluster_id)
            elif sync.source_cluster_id:
                source_client = self.get_redis_client(sync.source_cluster_id)
            
            if sync.target_node_id:
                target_node = CacheNode.query.get(sync.target_node_id)
                target_client = self.get_redis_client(target_node.cluster_id)
            elif sync.target_cluster_id:
                target_client = self.get_redis_client(sync.target_cluster_id)
            
            if not source_client or not target_client:
                sync.fail_sync("Missing source or target connection")
                return False
            
            # Execute synchronization based on type
            if sync.sync_type == 'full':
                self._execute_full_sync(sync, source_client, target_client)
            elif sync.sync_type == 'incremental':
                self._execute_incremental_sync(sync, source_client, target_client)
            elif sync.sync_type == 'key_based':
                self._execute_key_based_sync(sync, source_client, target_client)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing synchronization {sync_id}: {str(e)}")
            return False
    
    def _execute_full_sync(self, sync, source_client, target_client):
        """Execute full synchronization"""
        try:
            # Get all keys from source
            source_keys = source_client.keys('*')
            total_keys = len(source_keys)
            
            sync.update_progress(total_keys=total_keys)
            
            processed_keys = 0
            failed_keys = 0
            data_transferred = 0
            
            for key in source_keys:
                try:
                    # Get value and TTL
                    value = source_client.dump(key)
                    ttl = source_client.ttl(key)
                    
                    # Restore to target
                    if ttl > 0:
                        target_client.restore(key, ttl, value)
                    else:
                        target_client.restore(key, 0, value)
                    
                    processed_keys += 1
                    data_transferred += len(value)
                    
                    # Update progress periodically
                    if processed_keys % 100 == 0:
                        sync.update_progress(processed_keys=processed_keys, failed_keys=failed_keys)
                
                except Exception as e:
                    failed_keys += 1
                    logger.error(f"Error syncing key {key}: {str(e)}")
            
            # Complete synchronization
            sync.complete_sync(
                total_keys=total_keys,
                processed_keys=processed_keys,
                failed_keys=failed_keys,
                data_transferred_bytes=data_transferred
            )
            
        except Exception as e:
            sync.fail_sync(str(e))
            raise
    
    def _execute_incremental_sync(self, sync, source_client, target_client):
        """Execute incremental synchronization"""
        try:
            # Get keys modified since last sync
            last_sync_time = sync.sync_config.get('last_sync_time')
            
            if last_sync_time:
                # This would require Redis keyspace notifications or custom tracking
                # For now, implement as full sync with date filtering
                self._execute_full_sync(sync, source_client, target_client)
            else:
                # First time sync - do full sync
                self._execute_full_sync(sync, source_client, target_client)
            
        except Exception as e:
            sync.fail_sync(str(e))
            raise
    
    def _execute_key_based_sync(self, sync, source_client, target_client):
        """Execute key-based synchronization"""
        try:
            filter_patterns = sync.filter_patterns or ['*']
            
            total_keys = 0
            processed_keys = 0
            failed_keys = 0
            data_transferred = 0
            
            for pattern in filter_patterns:
                try:
                    keys = source_client.keys(pattern)
                    total_keys += len(keys)
                    
                    for key in keys:
                        try:
                            # Get value and TTL
                            value = source_client.dump(key)
                            ttl = source_client.ttl(key)
                            
                            # Restore to target
                            if ttl > 0:
                                target_client.restore(key, ttl, value)
                            else:
                                target_client.restore(key, 0, value)
                            
                            processed_keys += 1
                            data_transferred += len(value)
                        
                        except Exception as e:
                            failed_keys += 1
                            logger.error(f"Error syncing key {key}: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Error processing pattern {pattern}: {str(e)}")
            
            # Complete synchronization
            sync.complete_sync(
                total_keys=total_keys,
                processed_keys=processed_keys,
                failed_keys=failed_keys,
                data_transferred_bytes=data_transferred
            )
            
        except Exception as e:
            sync.fail_sync(str(e))
            raise
    
    def create_failover(self, cluster_id, failover_type, failover_reason, failed_node_id=None,
                       promoted_node_id=None, failover_config=None, recovery_config=None):
        """Create a cache failover"""
        if not self.enabled:
            return None
        
        try:
            failover = CacheFailover.create_failover(
                cluster_id=cluster_id,
                failover_type=failover_type,
                failover_reason=failover_reason,
                failed_node_id=failed_node_id,
                promoted_node_id=promoted_node_id,
                failover_config=failover_config,
                recovery_config=recovery_config
            )
            
            return failover
            
        except Exception as e:
            logger.error(f"Error creating failover: {str(e)}")
            return None
    
    def execute_failover(self, failover_id):
        """Execute cache failover"""
        if not self.enabled:
            return False
        
        try:
            failover = CacheFailover.query.get(failover_id)
            if not failover:
                return False
            
            failover.start_failover()
            
            # Get cluster and nodes
            cluster = CacheCluster.query.get(failover.cluster_id)
            if not cluster:
                failover.fail_failover("Cluster not found")
                return False
            
            # Execute failover based on type
            if failover.failover_type == 'automatic':
                self._execute_automatic_failover(failover, cluster)
            elif failover.failover_type == 'manual':
                self._execute_manual_failover(failover, cluster)
            elif failover.failover_type == 'scheduled':
                self._execute_scheduled_failover(failover, cluster)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing failover {failover_id}: {str(e)}")
            return False
    
    def _execute_automatic_failover(self, failover, cluster):
        """Execute automatic failover"""
        try:
            # Find failed node
            failed_node = None
            if failover.failed_node_id:
                failed_node = CacheNode.query.get(failover.failed_node_id)
            
            if not failed_node:
                failover.fail_failover("Failed node not found")
                return
            
            # Find suitable slave node to promote
            slave_nodes = CacheNode.get_slave_nodes(cluster.cluster_id)
            if not slave_nodes:
                failover.fail_failover("No slave nodes available for promotion")
                return
            
            # Select best slave node (most recent data, lowest lag)
            best_slave = min(slave_nodes, key=lambda n: n.replication_lag)
            
            # Promote slave to master
            best_slave.promote_to_master()
            
            # Update other slaves to point to new master
            for slave in slave_nodes:
                if slave.node_id != best_slave.node_id:
                    slave.master_node_id = best_slave.node_id
                    db.session.commit()
            
            # Update cluster metrics
            cluster.update_metrics(
                master_nodes=len(CacheNode.get_master_nodes(cluster.cluster_id)),
                slave_nodes=len(CacheNode.get_slave_nodes(cluster.cluster_id))
            )
            
            # Complete failover
            failover.complete_failover(
                promoted_node_id=best_slave.node_id,
                affected_keys=failed_node.total_keys,
                recovered_keys=best_slave.total_keys
            )
            
        except Exception as e:
            failover.fail_failover(str(e))
            raise
    
    def _execute_manual_failover(self, failover, cluster):
        """Execute manual failover"""
        try:
            # Manual failover uses specified promoted node
            if not failover.promoted_node_id:
                failover.fail_failover("Promoted node not specified for manual failover")
                return
            
            promoted_node = CacheNode.query.get(failover.promoted_node_id)
            if not promoted_node:
                failover.fail_failover("Promoted node not found")
                return
            
            # Promote specified node to master
            promoted_node.promote_to_master()
            
            # Update other nodes
            all_nodes = CacheNode.get_nodes_by_cluster(cluster.cluster_id)
            for node in all_nodes:
                if node.node_id != promoted_node.node_id and node.node_role == 'slave':
                    node.master_node_id = promoted_node.node_id
                    db.session.commit()
            
            # Update cluster metrics
            cluster.update_metrics(
                master_nodes=len(CacheNode.get_master_nodes(cluster.cluster_id)),
                slave_nodes=len(CacheNode.get_slave_nodes(cluster.cluster_id))
            )
            
            # Complete failover
            failover.complete_failover(promoted_node_id=promoted_node.node_id)
            
        except Exception as e:
            failover.fail_failover(str(e))
            raise
    
    def _execute_scheduled_failover(self, failover, cluster):
        """Execute scheduled failover"""
        try:
            # Scheduled failover is similar to manual but with preparation
            self._execute_manual_failover(failover, cluster)
            
        except Exception as e:
            failover.fail_failover(str(e))
            raise
    
    def get_cluster_health(self, cluster_id):
        """Get cluster health status"""
        try:
            cluster = CacheCluster.query.get(cluster_id)
            if not cluster:
                return None
            
            # Get Redis client
            redis_client = self.get_redis_client(cluster_id)
            if not redis_client:
                return {
                    'cluster_id': cluster_id,
                    'status': 'error',
                    'message': 'Redis connection not available'
                }
            
            # Get cluster info
            cluster_info = {}
            try:
                if cluster.cluster_mode == 'cluster':
                    cluster_info = redis_client.cluster_info()
                else:
                    cluster_info = redis_client.info()
            except Exception as e:
                logger.error(f"Error getting cluster info: {str(e)}")
                cluster_info = {}
            
            # Get node status
            nodes = CacheNode.get_nodes_by_cluster(cluster_id)
            node_status = []
            
            for node in nodes:
                node_status.append({
                    'node_id': node.node_id,
                    'node_name': node.node_name,
                    'node_role': node.node_role,
                    'status': node.status,
                    'health_status': node.health_status,
                    'connection_status': node.connection_status,
                    'memory_utilization': node.memory_utilization,
                    'cpu_utilization': node.cpu_utilization,
                    'hit_rate': node.hit_rate,
                    'connections': node.connections
                })
            
            return {
                'cluster_id': cluster_id,
                'cluster_name': cluster.cluster_name,
                'status': cluster.status,
                'health_status': cluster.health_status,
                'cluster_info': cluster_info,
                'nodes': node_status,
                'total_nodes': len(nodes),
                'active_nodes': len([n for n in nodes if n.status == 'active']),
                'healthy_nodes': len([n for n in nodes if n.health_status == 'healthy'])
            }
            
        except Exception as e:
            logger.error(f"Error getting cluster health {cluster_id}: {str(e)}")
            return None
    
    def get_cluster_metrics(self, cluster_id):
        """Get cluster performance metrics"""
        try:
            cluster = CacheCluster.query.get(cluster_id)
            if not cluster:
                return None
            
            # Get Redis client
            redis_client = self.get_redis_client(cluster_id)
            if not redis_client:
                return None
            
            # Get Redis info
            redis_info = redis_client.info()
            
            # Calculate metrics
            metrics = {
                'cluster_id': cluster_id,
                'cluster_name': cluster.cluster_name,
                'timestamp': datetime.utcnow().isoformat(),
                'memory': {
                    'total': redis_info.get('maxmemory', 0),
                    'used': redis_info.get('used_memory', 0),
                    'utilization': redis_info.get('used_memory', 0) / max(redis_info.get('maxmemory', 1), 1),
                    'peak': redis_info.get('used_memory_peak', 0),
                    'fragmentation_ratio': redis_info.get('mem_fragmentation_ratio', 0)
                },
                'performance': {
                    'total_commands_processed': redis_info.get('total_commands_processed', 0),
                    'commands_per_sec': redis_info.get('instantaneous_ops_per_sec', 0),
                    'keyspace_hits': redis_info.get('keyspace_hits', 0),
                    'keyspace_misses': redis_info.get('keyspace_misses', 0),
                    'hit_rate': redis_info.get('keyspace_hits', 0) / max(redis_info.get('keyspace_hits', 0) + redis_info.get('keyspace_misses', 0), 1),
                    'expired_keys': redis_info.get('expired_keys', 0),
                    'evicted_keys': redis_info.get('evicted_keys', 0)
                },
                'connections': {
                    'connected_clients': redis_info.get('connected_clients', 0),
                    'blocked_clients': redis_info.get('blocked_clients', 0),
                    'client_recent_max_input_buffer': redis_info.get('client_recent_max_input_buffer', 0)
                },
                'persistence': {
                    'last_save_time': redis_info.get('last_save_time', 0),
                    'last_bg_save_status': redis_info.get('last_bg_save_status', 'unknown'),
                    'aof_current_rewrite_time_sec': redis_info.get('aof_current_rewrite_time_sec', 0),
                    'rdb_current_save_time_sec': redis_info.get('rdb_current_save_time_sec', 0)
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting cluster metrics {cluster_id}: {str(e)}")
            return None
    
    def cleanup_expired_data(self, hours=24):
        """Clean up expired distributed cache data"""
        try:
            # Clean up old synchronizations
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            old_syncs = CacheSynchronization.query.filter(
                CacheSynchronization.created_at < cutoff_time,
                CacheSynchronization.sync_status.in_(['completed', 'failed'])
            ).count()
            
            if old_syncs > 0:
                CacheSynchronization.query.filter(
                    CacheSynchronization.created_at < cutoff_time,
                    CacheSynchronization.sync_status.in_(['completed', 'failed'])
                ).delete()
                logger.info(f"Cleaned up {old_syncs} old synchronizations")
            
            # Clean up old failovers
            old_failovers = CacheFailover.query.filter(
                CacheFailover.created_at < cutoff_time,
                CacheFailover.failover_status.in_(['completed', 'failed'])
            ).count()
            
            if old_failovers > 0:
                CacheFailover.query.filter(
                    CacheFailover.created_at < cutoff_time,
                    CacheFailover.failover_status.in_(['completed', 'failed'])
                ).delete()
                logger.info(f"Cleaned up {old_failovers} old failovers")
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {str(e)}")
            db.session.rollback()


# Global distributed cache service instance
distributed_cache_service = None

def get_distributed_cache_service():
    """Get distributed cache service instance (lazy initialization)"""
    global distributed_cache_service
    if distributed_cache_service is None:
        distributed_cache_service = DistributedCacheService()
    return distributed_cache_service
