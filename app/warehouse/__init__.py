"""
Warehouse Module

Data warehouse system for the Auto Bot Solutions Forum with analytics data warehouse,
aggregation pipelines, historical data storage, and data archiving.
"""

from .models import DataWarehouse, AggregationPipeline, HistoricalData, DataArchive
from .service import DataWarehouseService, get_data_warehouse_service
from .utils import (
    AggregationType, ArchiveType, StorageTier, AggregationRule, ArchiveRule,
    AggregationEngine, DataArchiver, RetentionPolicyManager, DataQualityChecker,
    WarehouseMonitor, WarehouseUtils, aggregation_engine, data_archiver,
    retention_policy_manager, data_quality_checker, warehouse_monitor
)
from .config import (
    DATA_WAREHOUSE_ENABLED, WAREHOUSE_PROCESSING_ENABLED, DATA_ARCHIVING_ENABLED,
    DATA_RETENTION_ENABLED, AGGREGATION_ENABLED, WAREHOUSE_CONFIG, STORAGE_CONFIG,
    AGGREGATION_CONFIG, HISTORICAL_CONFIG, ARCHIVING_CONFIG, RETENTION_CONFIG,
    PERFORMANCE_CONFIG, MONITORING_CONFIG, SECURITY_CONFIG, BACKUP_CONFIG,
    SCHEMA_TEMPLATES, AGGREGATION_TEMPLATES, get_warehouse_config,
    validate_warehouse_config
)

__all__ = [
    # Models
    'DataWarehouse',
    'AggregationPipeline',
    'HistoricalData',
    'DataArchive',
    
    # Services
    'DataWarehouseService',
    'get_data_warehouse_service',
    
    # Utilities
    'AggregationType',
    'ArchiveType',
    'StorageTier',
    'AggregationRule',
    'ArchiveRule',
    'AggregationEngine',
    'DataArchiver',
    'RetentionPolicyManager',
    'DataQualityChecker',
    'WarehouseMonitor',
    'WarehouseUtils',
    'aggregation_engine',
    'data_archiver',
    'retention_policy_manager',
    'data_quality_checker',
    'warehouse_monitor',
    
    # Configuration
    'DATA_WAREHOUSE_ENABLED',
    'WAREHOUSE_PROCESSING_ENABLED',
    'DATA_ARCHIVING_ENABLED',
    'DATA_RETENTION_ENABLED',
    'AGGREGATION_ENABLED',
    'WAREHOUSE_CONFIG',
    'STORAGE_CONFIG',
    'AGGREGATION_CONFIG',
    'HISTORICAL_CONFIG',
    'ARCHIVING_CONFIG',
    'RETENTION_CONFIG',
    'PERFORMANCE_CONFIG',
    'MONITORING_CONFIG',
    'SECURITY_CONFIG',
    'BACKUP_CONFIG',
    'SCHEMA_TEMPLATES',
    'AGGREGATION_TEMPLATES',
    'get_warehouse_config',
    'validate_warehouse_config'
]
