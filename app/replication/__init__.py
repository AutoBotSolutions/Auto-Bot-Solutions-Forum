"""
Replication Module

Data replication system for the Auto Bot Solutions Forum with master-slave replication,
multi-master replication, replication monitoring, and conflict resolution.
"""

from .models import ReplicationCluster, ReplicationNode, ReplicationEvent, ReplicationConflict
from .service import DataReplicationService, get_data_replication_service
from .utils import (
    ReplicationMode, ConsistencyLevel, ConflictType, ConflictSeverity, ReplicationEvent as ReplicationEventInfo,
    ConflictInfo, ReplicationMonitor, ReplicationValidator, ReplicationOptimizer, ReplicationUtils,
    replication_monitor, replication_validator, replication_optimizer, replication_utils
)
from .config import (
    DATA_REPLICATION_ENABLED, MASTER_SLAVE_REPLICATION_ENABLED, MULTI_MASTER_REPLICATION_ENABLED,
    CONFLICT_RESOLUTION_ENABLED, REPLICATION_MONITORING_ENABLED, CLUSTER_CONFIG, REPLICATION_CONFIG,
    CONFLICT_RESOLUTION_CONFIG, FAILOVER_CONFIG, CONNECTION_CONFIG, MONITORING_CONFIG,
    PERFORMANCE_CONFIG, SECURITY_CONFIG, DATABASE_TYPE_CONFIGS, CLUSTER_TEMPLATES,
    NODE_TEMPLATES, get_replication_config, validate_replication_config
)

__all__ = [
    # Models
    'ReplicationCluster',
    'ReplicationNode',
    'ReplicationEvent',
    'ReplicationConflict',
    
    # Services
    'DataReplicationService',
    'get_data_replication_service',
    
    # Utilities
    'ReplicationMode',
    'ConsistencyLevel',
    'ConflictType',
    'ConflictSeverity',
    'ReplicationEventInfo',
    'ConflictInfo',
    'ReplicationMonitor',
    'ReplicationValidator',
    'ReplicationOptimizer',
    'ReplicationUtils',
    'replication_monitor',
    'replication_validator',
    'replication_optimizer',
    'replication_utils',
    
    # Configuration
    'DATA_REPLICATION_ENABLED',
    'MASTER_SLAVE_REPLICATION_ENABLED',
    'MULTI_MASTER_REPLICATION_ENABLED',
    'CONFLICT_RESOLUTION_ENABLED',
    'REPLICATION_MONITORING_ENABLED',
    'CLUSTER_CONFIG',
    'REPLICATION_CONFIG',
    'CONFLICT_RESOLUTION_CONFIG',
    'FAILOVER_CONFIG',
    'CONNECTION_CONFIG',
    'MONITORING_CONFIG',
    'PERFORMANCE_CONFIG',
    'SECURITY_CONFIG',
    'DATABASE_TYPE_CONFIGS',
    'CLUSTER_TEMPLATES',
    'NODE_TEMPLATES',
    'get_replication_config',
    'validate_replication_config'
]
