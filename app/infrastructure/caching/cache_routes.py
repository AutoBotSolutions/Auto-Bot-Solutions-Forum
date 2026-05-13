"""
Cache Infrastructure Routes

Flask routes for cache infrastructure management including monitoring,
backup, tuning, and cluster management endpoints.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# This would be initialized in the main app
cache_bp = Blueprint('cache', __name__, url_prefix='/api/infrastructure/cache')

def init_cache_routes(cache_manager, redis_cluster_manager, cache_monitor, cache_backup, cache_tuner):
    """Initialize cache routes with infrastructure components"""
    
    @cache_bp.route('/health', methods=['GET'])
    def cache_health():
        """Get cache infrastructure health status"""
        try:
            # Get health from all components
            cache_health = cache_manager.health_check()
            cluster_health = redis_cluster_manager.health_check()
            
            overall_status = 'healthy'
            issues = []
            
            if cache_health.get('status') != 'healthy':
                overall_status = 'degraded'
                issues.extend(cache_health.get('issues', []))
            
            if cluster_health.get('overall_status') != 'healthy':
                overall_status = 'degraded'
                issues.extend(cluster_health.get('issues', []))
            
            return jsonify({
                'success': True,
                'data': {
                    'overall_status': overall_status,
                    'cache_manager': cache_health,
                    'redis_cluster': cluster_health,
                    'issues': issues,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting cache health: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/stats', methods=['GET'])
    def cache_stats():
        """Get comprehensive cache statistics"""
        try:
            # Get stats from all components
            cache_stats = cache_manager.get_stats()
            cluster_info = redis_cluster_manager.get_cluster_info()
            performance_stats = cache_monitor.get_performance_stats()
            backup_stats = cache_backup.get_backup_stats()
            tuning_stats = cache_tuner.get_tuning_stats()
            
            return jsonify({
                'success': True,
                'data': {
                    'cache_manager': cache_stats,
                    'redis_cluster': cluster_info,
                    'performance': performance_stats,
                    'backup': backup_stats,
                    'tuning': tuning_stats,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/config', methods=['GET'])
    def get_cache_config():
        """Get cache infrastructure configuration"""
        try:
            return jsonify({
                'success': True,
                'data': {
                    'cache_manager': cache_manager.get_config(),
                    'redis_cluster': redis_cluster_manager.get_config(),
                    'cache_monitor': cache_monitor.get_monitoring_status(),
                    'cache_backup': cache_backup.get_config(),
                    'cache_tuner': cache_tuner.get_config()
                }
            })
        except Exception as e:
            logger.error(f"Error getting cache config: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/config', methods=['PUT'])
    def update_cache_config():
        """Update cache infrastructure configuration"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            # Update configurations
            if 'cache_manager' in data:
                cache_manager.update_config(**data['cache_manager'])
            
            if 'redis_cluster' in data:
                redis_cluster_manager.update_config(**data['redis_cluster'])
            
            if 'cache_backup' in data:
                cache_backup.update_config(**data['cache_backup'])
            
            if 'cache_tuner' in data:
                cache_tuner.update_config(**data['cache_tuner'])
            
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Configuration updated successfully'
                }
            })
        except Exception as e:
            logger.error(f"Error updating cache config: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    # Redis Cluster Management Routes
    
    @cache_bp.route('/cluster/info', methods=['GET'])
    def get_cluster_info():
        """Get Redis cluster information"""
        try:
            cluster_info = redis_cluster_manager.get_cluster_info()
            return jsonify({
                'success': True,
                'data': cluster_info
            })
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/cluster/nodes', methods=['GET'])
    def get_cluster_nodes():
        """Get Redis cluster nodes"""
        try:
            cluster_info = redis_cluster_manager.get_cluster_info()
            return jsonify({
                'success': True,
                'data': cluster_info.get('nodes', {})
            })
        except Exception as e:
            logger.error(f"Error getting cluster nodes: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/cluster/nodes/<node_host>/<int:node_port>', methods=['GET'])
    def get_node_stats(node_host: str, node_port: int):
        """Get detailed statistics for a specific node"""
        try:
            node_stats = redis_cluster_manager.get_node_stats(node_host, node_port)
            
            if not node_stats:
                return jsonify({
                    'success': False,
                    'error': 'Node not found'
                }), 404
            
            return jsonify({
                'success': True,
                'data': node_stats
            })
        except Exception as e:
            logger.error(f"Error getting node stats: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/cluster/nodes', methods=['POST'])
    def add_cluster_node():
        """Add new node to Redis cluster"""
        try:
            data = request.get_json()
            
            required_fields = ['host', 'port']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            success = redis_cluster_manager.add_node(
                data['host'], 
                data['port'], 
                data.get('role', 'master')
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'Node {data["host"]}:{data["port"]} added successfully'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to add node'
                }), 500
        
        except Exception as e:
            logger.error(f"Error adding cluster node: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/cluster/nodes/<node_host>/<int:node_port>', methods=['DELETE'])
    def remove_cluster_node(node_host: str, node_port: int):
        """Remove node from Redis cluster"""
        try:
            success = redis_cluster_manager.remove_node(node_host, node_port)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'Node {node_host}:{node_port} removed successfully'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to remove node'
                }), 500
        
        except Exception as e:
            logger.error(f"Error removing cluster node: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/cluster/failover/<node_host>/<int:node_port>', methods=['POST'])
    def trigger_failover(node_host: str, node_port: int):
        """Trigger failover for a cluster node"""
        try:
            success = redis_cluster_manager.failover_node(node_host, node_port)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'Failover triggered for {node_host}:{node_port}'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to trigger failover'
                }), 500
        
        except Exception as e:
            logger.error(f"Error triggering failover: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/cluster/reshard', methods=['POST'])
    def reshard_cluster():
        """Reshard Redis cluster"""
        try:
            data = request.get_json()
            
            required_fields = ['source_host', 'source_port', 'target_host', 'target_port', 'slot_count']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            success = redis_cluster_manager.reshard_cluster(
                data['source_host'],
                data['source_port'],
                data['target_host'],
                data['target_port'],
                data['slot_count']
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': 'Cluster resharded successfully'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to reshard cluster'
                }), 500
        
        except Exception as e:
            logger.error(f"Error resharding cluster: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    # Cache Monitoring Routes
    
    @cache_bp.route('/monitoring/metrics', methods=['GET'])
    def get_monitoring_metrics():
        """Get cache monitoring metrics"""
        try:
            time_window = request.args.get('time_window', 300, type=int)
            metrics_summary = cache_monitor.get_metrics_summary(time_window)
            
            return jsonify({
                'success': True,
                'data': metrics_summary
            })
        except Exception as e:
            logger.error(f"Error getting monitoring metrics: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/monitoring/performance', methods=['GET'])
    def get_performance_stats():
        """Get cache performance statistics"""
        try:
            time_window = request.args.get('time_window', 300, type=int)
            performance_stats = cache_monitor.get_performance_stats(time_window)
            
            return jsonify({
                'success': True,
                'data': {
                    'hit_rate': performance_stats.hit_rate,
                    'miss_rate': performance_stats.miss_rate,
                    'avg_response_time': performance_stats.avg_response_time,
                    'p95_response_time': performance_stats.p95_response_time,
                    'p99_response_time': performance_stats.p99_response_time,
                    'throughput': performance_stats.throughput,
                    'memory_usage': performance_stats.memory_usage,
                    'key_count': performance_stats.key_count,
                    'eviction_rate': performance_stats.eviction_rate,
                    'connection_count': performance_stats.connection_count,
                    'error_rate': performance_stats.error_rate
                }
            })
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/monitoring/alerts', methods=['GET'])
    def get_monitoring_alerts():
        """Get cache monitoring alerts"""
        try:
            alerts = cache_monitor.get_alerts()
            return jsonify({
                'success': True,
                'data': {
                    'alerts': alerts,
                    'total': len(alerts)
                }
            })
        except Exception as e:
            logger.error(f"Error getting monitoring alerts: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/monitoring/alerts', methods=['POST'])
    def create_monitoring_alert():
        """Create a new monitoring alert"""
        try:
            data = request.get_json()
            
            required_fields = ['alert_id', 'name', 'level', 'condition', 'threshold']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            from .cache_monitor import AlertLevel
            
            level = AlertLevel(data['level'])
            cache_monitor.create_alert(
                data['alert_id'],
                data['name'],
                level,
                data['condition'],
                data['threshold'],
                data.get('window', 300)
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Alert created successfully'
                }
            })
        except Exception as e:
            logger.error(f"Error creating monitoring alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/monitoring/alerts/<alert_id>/enable', methods=['POST'])
    def enable_monitoring_alert(alert_id: str):
        """Enable a monitoring alert"""
        try:
            cache_monitor.enable_alert(alert_id)
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Alert {alert_id} enabled'
                }
            })
        except Exception as e:
            logger.error(f"Error enabling monitoring alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/monitoring/alerts/<alert_id>/disable', methods=['POST'])
    def disable_monitoring_alert(alert_id: str):
        """Disable a monitoring alert"""
        try:
            cache_monitor.disable_alert(alert_id)
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Alert {alert_id} disabled'
                }
            })
        except Exception as e:
            logger.error(f"Error disabling monitoring alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/monitoring/alerts/<alert_id>', methods=['DELETE'])
    def delete_monitoring_alert(alert_id: str):
        """Delete a monitoring alert"""
        try:
            cache_monitor.delete_alert(alert_id)
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Alert {alert_id} deleted'
                }
            })
        except Exception as e:
            logger.error(f"Error deleting monitoring alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    # Cache Backup Routes
    
    @cache_bp.route('/backup/jobs', methods=['GET'])
    def get_backup_jobs():
        """Get all backup jobs"""
        try:
            backup_jobs = cache_backup.get_backup_jobs()
            return jsonify({
                'success': True,
                'data': {
                    'jobs': backup_jobs,
                    'total': len(backup_jobs)
                }
            })
        except Exception as e:
            logger.error(f"Error getting backup jobs: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/backup/create', methods=['POST'])
    def create_backup():
        """Create a new backup job"""
        try:
            data = request.get_json()
            
            required_fields = ['backup_id', 'backup_type']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            from .cache_backup import BackupType
            
            backup_type = BackupType(data['backup_type'])
            backup_id = cache_backup.create_backup(
                data['backup_id'],
                backup_type,
                data.get('nodes')
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'backup_id': backup_id,
                    'message': 'Backup job created successfully'
                }
            })
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/backup/<backup_id>/restore', methods=['POST'])
    def restore_backup(backup_id: str):
        """Restore from backup"""
        try:
            data = request.get_json() or {}
            target_nodes = data.get('target_nodes')
            
            success = cache_backup.restore_backup(backup_id, target_nodes)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'Backup {backup_id} restored successfully'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Restore failed'
                }), 500
        
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/backup/<backup_id>/cancel', methods=['POST'])
    def cancel_backup(backup_id: str):
        """Cancel a backup job"""
        try:
            success = cache_backup.cancel_backup(backup_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'Backup {backup_id} cancelled'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to cancel backup'
                }), 500
        
        except Exception as e:
            logger.error(f"Error cancelling backup: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/backup/cleanup', methods=['POST'])
    def cleanup_old_backups():
        """Clean up old backup files"""
        try:
            data = request.get_json() or {}
            retention_days = data.get('retention_days')
            
            if retention_days:
                cache_backup.update_config(retention_days=retention_days)
            
            cleaned_count = cache_backup.cleanup_old_backups()
            
            return jsonify({
                'success': True,
                'data': {
                    'cleaned_files': cleaned_count,
                    'message': f'Cleaned up {cleaned_count} old backup files'
                }
            })
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    # Cache Tuning Routes
    
    @cache_bp.route('/tuning/recommendations', methods=['GET'])
    def get_tuning_recommendations():
        """Get cache tuning recommendations"""
        try:
            limit = request.args.get('limit', 10, type=int)
            recommendations = cache_tuner.get_tuning_recommendations(limit)
            
            return jsonify({
                'success': True,
                'data': {
                    'recommendations': recommendations,
                    'total': len(recommendations)
                }
            })
        except Exception as e:
            logger.error(f"Error getting tuning recommendations: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/tuning/manual', methods=['POST'])
    def manual_tune():
        """Manually trigger cache tuning"""
        try:
            data = request.get_json()
            
            required_fields = ['optimization_type']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            from .cache_tuner import OptimizationType
            
            optimization_type = OptimizationType(data['optimization_type'])
            parameters = data.get('parameters', {})
            
            success = cache_tuner.manual_tune(optimization_type, parameters)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': 'Manual tuning completed successfully'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Manual tuning failed'
                }), 500
        
        except Exception as e:
            logger.error(f"Error performing manual tuning: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/tuning/history', methods=['GET'])
    def get_tuning_history():
        """Get cache tuning history"""
        try:
            limit = request.args.get('limit', 50, type=int)
            history = cache_tuner.get_tuning_history(limit)
            
            return jsonify({
                'success': True,
                'data': {
                    'history': history,
                    'total': len(history)
                }
            })
        except Exception as e:
            logger.error(f"Error getting tuning history: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/tuning/stats', methods=['GET'])
    def get_tuning_stats():
        """Get cache tuning statistics"""
        try:
            tuning_stats = cache_tuner.get_tuning_stats()
            return jsonify({
                'success': True,
                'data': tuning_stats
            })
        except Exception as e:
            logger.error(f"Error getting tuning stats: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    # Cache Operations Routes
    
    @cache_bp.route('/cache/clear', methods=['POST'])
    def clear_cache():
        """Clear cache entries"""
        try:
            data = request.get_json() or {}
            pattern = data.get('pattern', '*')
            level = data.get('level', 'all')
            
            from .cache_manager import CacheLevel
            
            if level == 'all':
                cache_level = CacheLevel.L3
            else:
                cache_level = CacheLevel(level)
            
            cleared_count = cache_manager.clear(pattern, cache_level)
            
            return jsonify({
                'success': True,
                'data': {
                    'cleared_keys': cleared_count,
                    'pattern': pattern,
                    'level': level
                }
            })
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/cache/keys/<key>', methods=['GET'])
    def get_cache_key(key: str):
        """Get value from cache"""
        try:
            level = request.args.get('level', 'l2')
            
            from .cache_manager import CacheLevel
            cache_level = CacheLevel(level)
            
            value = cache_manager.get(key, cache_level)
            
            if value is not None:
                return jsonify({
                    'success': True,
                    'data': {
                        'key': key,
                        'value': value,
                        'level': level
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Key not found'
                }), 404
        
        except Exception as e:
            logger.error(f"Error getting cache key: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/cache/keys/<key>', methods=['PUT'])
    def set_cache_key(key: str):
        """Set value in cache"""
        try:
            data = request.get_json()
            
            if 'value' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Value is required'
                }), 400
            
            value = data['value']
            ttl = data.get('ttl')
            level = data.get('level', 'l2')
            
            from .cache_manager import CacheLevel
            cache_level = CacheLevel(level)
            
            success = cache_manager.set(key, value, ttl, cache_level)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'key': key,
                        'ttl': ttl,
                        'level': level
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to set key'
                }), 500
        
        except Exception as e:
            logger.error(f"Error setting cache key: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @cache_bp.route('/cache/keys/<key>', methods=['DELETE'])
    def delete_cache_key(key: str):
        """Delete key from cache"""
        try:
            level = request.args.get('level', 'l2')
            
            from .cache_manager import CacheLevel
            cache_level = CacheLevel(level)
            
            success = cache_manager.delete(key, cache_level)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'key': key,
                        'level': level
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to delete key'
                }), 500
        
        except Exception as e:
            logger.error(f"Error deleting cache key: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
