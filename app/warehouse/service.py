"""
Data Warehouse Service

Comprehensive data warehouse service for analytics data warehouse, aggregation pipelines,
historical data storage, and data archiving for the Auto Bot Solutions Forum.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from flask import current_app
from sqlalchemy import and_, or_, desc, func
from app import db
from app.warehouse.models import DataWarehouse, AggregationPipeline, HistoricalData, DataArchive

logger = logging.getLogger(__name__)

class DataWarehouseService:
    """Comprehensive data warehouse service for analytics and historical data"""
    
    def __init__(self):
        self.enabled = current_app.config.get('DATA_WAREHOUSE_ENABLED', True)
        self.processing_enabled = current_app.config.get('WAREHOUSE_PROCESSING_ENABLED', True)
        self.archiving_enabled = current_app.config.get('DATA_ARCHIVING_ENABLED', True)
        self.retention_enabled = current_app.config.get('DATA_RETENTION_ENABLED', True)
    
    def create_warehouse(self, warehouse_name, warehouse_type, warehouse_category,
                          storage_engine='postgresql', storage_config=None, schema_definition=None,
                          table_mappings=None, data_retention_days=365, archiving_enabled=True,
                          compression_enabled=True, encryption_enabled=False, processing_enabled=True,
                          processing_interval=3600, batch_size=1000, metadata=None):
        """Create a new data warehouse"""
        if not self.enabled:
            return None
        
        try:
            warehouse = DataWarehouse.create_warehouse(
                warehouse_name=warehouse_name,
                warehouse_type=warehouse_type,
                warehouse_category=warehouse_category,
                storage_engine=storage_engine,
                storage_config=storage_config,
                schema_definition=schema_definition,
                table_mappings=table_mappings,
                data_retention_days=data_retention_days,
                archiving_enabled=archiving_enabled,
                compression_enabled=compression_enabled,
                encryption_enabled=encryption_enabled,
                processing_enabled=processing_enabled,
                processing_interval=processing_interval,
                batch_size=batch_size,
                metadata=metadata
            )
            
            # Initialize warehouse storage
            self._initialize_warehouse_storage(warehouse)
            
            return warehouse
            
        except Exception as e:
            logger.error(f"Error creating data warehouse {warehouse_name}: {str(e)}")
            return None
    
    def _initialize_warehouse_storage(self, warehouse):
        """Initialize warehouse storage"""
        try:
            # This would initialize the actual database/storage for the warehouse
            # For now, just log the initialization
            logger.info(f"Initialized storage for warehouse {warehouse.warehouse_name}")
            
            # Update warehouse status
            warehouse.update_health_status('healthy')
            
        except Exception as e:
            logger.error(f"Error initializing storage for warehouse {warehouse.warehouse_name}: {str(e)}")
            warehouse.update_health_status('unhealthy')
            raise
    
    def get_warehouse(self, warehouse_id=None, warehouse_name=None):
        """Get data warehouse by ID or name"""
        if not self.enabled:
            return None
        
        try:
            if warehouse_id:
                return DataWarehouse.query.get(warehouse_id)
            elif warehouse_name:
                return DataWarehouse.get_warehouse_by_name(warehouse_name)
            return None
            
        except Exception as e:
            logger.error(f"Error getting warehouse: {str(e)}")
            return None
    
    def create_aggregation_pipeline(self, warehouse_id, pipeline_name, pipeline_type, pipeline_category,
                                 source_tables=None, source_filters=None, source_joins=None,
                                 aggregation_config=None, group_by_fields=None, aggregate_functions=None,
                                 having_conditions=None, target_table=None, target_schema=None,
                                 update_strategy='append', schedule_type='interval', schedule_config=None,
                                 metadata=None):
        """Create an aggregation pipeline"""
        if not self.enabled:
            return None
        
        try:
            pipeline = AggregationPipeline.create_pipeline(
                warehouse_id=warehouse_id,
                pipeline_name=pipeline_name,
                pipeline_type=pipeline_type,
                pipeline_category=pipeline_category,
                source_tables=source_tables,
                source_filters=source_filters,
                source_joins=source_joins,
                aggregation_config=aggregation_config,
                group_by_fields=group_by_fields,
                aggregate_functions=aggregate_functions,
                having_conditions=having_conditions,
                target_table=target_table,
                target_schema=target_schema,
                update_strategy=update_strategy,
                schedule_type=schedule_type,
                schedule_config=schedule_config,
                metadata=metadata
            )
            
            # Calculate next run time
            pipeline.calculate_next_run_time()
            
            return pipeline
            
        except Exception as e:
            logger.error(f"Error creating aggregation pipeline {pipeline_name}: {str(e)}")
            return None
    
    def execute_aggregation_pipeline(self, pipeline_id):
        """Execute an aggregation pipeline"""
        if not self.processing_enabled:
            return False
        
        try:
            pipeline = AggregationPipeline.query.get(pipeline_id)
            if not pipeline:
                return False
            
            start_time = time.time()
            
            # Update pipeline status to running
            pipeline.update_status('running')
            
            # Execute aggregation based on type
            if pipeline.pipeline_type == 'hourly':
                success = self._execute_hourly_aggregation(pipeline)
            elif pipeline.pipeline_type == 'daily':
                success = self._execute_daily_aggregation(pipeline)
            elif pipeline.pipeline_type == 'weekly':
                success = self._execute_weekly_aggregation(pipeline)
            elif pipeline.pipeline_type == 'monthly':
                success = self._execute_monthly_aggregation(pipeline)
            else:
                success = self._execute_custom_aggregation(pipeline)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            if success:
                # Update metrics
                records_processed = self._get_processed_records_count(pipeline)
                pipeline.update_metrics(processing_time_ms, records_processed)
                pipeline.update_status('active', 'success')
            else:
                pipeline.update_status('error', 'failed')
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing aggregation pipeline {pipeline_id}: {str(e)}")
            
            # Update pipeline status
            pipeline = AggregationPipeline.query.get(pipeline_id)
            if pipeline:
                pipeline.update_status('error', 'failed', str(e))
            
            return False
    
    def _execute_hourly_aggregation(self, pipeline):
        """Execute hourly aggregation"""
        try:
            # Get source data for the last hour
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            return self._execute_time_based_aggregation(pipeline, start_time, end_time)
            
        except Exception as e:
            logger.error(f"Error executing hourly aggregation: {str(e)}")
            return False
    
    def _execute_daily_aggregation(self, pipeline):
        """Execute daily aggregation"""
        try:
            # Get source data for the last day
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=1)
            
            return self._execute_time_based_aggregation(pipeline, start_time, end_time)
            
        except Exception as e:
            logger.error(f"Error executing daily aggregation: {str(e)}")
            return False
    
    def _execute_weekly_aggregation(self, pipeline):
        """Execute weekly aggregation"""
        try:
            # Get source data for the last week
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(weeks=1)
            
            return self._execute_time_based_aggregation(pipeline, start_time, end_time)
            
        except Exception as e:
            logger.error(f"Error executing weekly aggregation: {str(e)}")
            return False
    
    def _execute_monthly_aggregation(self, pipeline):
        """Execute monthly aggregation"""
        try:
            # Get source data for the last month
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            
            return self._execute_time_based_aggregation(pipeline, start_time, end_time)
            
        except Exception as e:
            logger.error(f"Error executing monthly aggregation: {str(e)}")
            return False
    
    def _execute_custom_aggregation(self, pipeline):
        """Execute custom aggregation based on schedule config"""
        try:
            schedule_config = pipeline.schedule_config or {}
            
            # Parse date range from schedule config
            start_date_str = schedule_config.get('start_date')
            end_date_str = schedule_config.get('end_date')
            
            if start_date_str and end_date_str:
                start_time = datetime.fromisoformat(start_date_str)
                end_time = datetime.fromisoformat(end_date_str)
            else:
                # Default to last 24 hours
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=24)
            
            return self._execute_time_based_aggregation(pipeline, start_time, end_time)
            
        except Exception as e:
            logger.error(f"Error executing custom aggregation: {str(e)}")
            return False
    
    def _execute_time_based_aggregation(self, pipeline, start_time, end_time):
        """Execute time-based aggregation"""
        try:
            # Get warehouse
            warehouse = DataWarehouse.query.get(pipeline.warehouse_id)
            if not warehouse:
                return False
            
            # This would execute the actual aggregation query
            # For now, simulate the process
            
            # Simulate data processing
            batch_size = pipeline.batch_size
            total_records = 0
            
            # Simulate processing batches
            while True:
                # Simulate fetching batch of records
                batch_records = min(batch_size, 1000)  # Simulate batch size
                if batch_records == 0:
                    break
                
                # Simulate processing time
                time.sleep(0.01)  # Simulate processing delay
                
                total_records += batch_records
                
                # Check if we should stop (simulate end of data)
                if total_records >= 10000:  # Simulate max records
                    break
            
            # Store aggregated results
            self._store_aggregated_results(pipeline, total_records, start_time, end_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing time-based aggregation: {str(e)}")
            return False
    
    def _get_processed_records_count(self, pipeline):
        """Get number of processed records for a pipeline"""
        try:
            # This would query the target table to get actual record count
            # For now, return a simulated value
            return 1000
            
        except Exception as e:
            logger.error(f"Error getting processed records count: {str(e)}")
            return 0
    
    def _store_aggregated_results(self, pipeline, record_count, start_time, end_time):
        """Store aggregated results in target table"""
        try:
            # This would store the actual aggregated results
            # For now, just log the operation
            logger.info(f"Stored {record_count} aggregated records for pipeline {pipeline.pipeline_name}")
            
            # Update warehouse metrics
            warehouse = DataWarehouse.query.get(pipeline.warehouse_id)
            if warehouse:
                warehouse.update_metrics(row_count=warehouse.row_count + record_count)
            
        except Exception as e:
            logger.error(f"Error storing aggregated results: {str(e)}")
    
    def archive_historical_data(self, warehouse_id, table_name, source_table, data_timestamp,
                               record_type='snapshot', archival_reason=None, retention_policy=None):
        """Archive historical data"""
        if not self.archiving_enabled:
            return None
        
        try:
            # Get source data to archive
            source_data = self._get_source_data_for_archiving(source_table, data_timestamp)
            
            if not source_data:
                return None
            
            # Create historical data records
            archived_records = []
            for record in source_data:
                historical_data = HistoricalData.create_historical_data(
                    warehouse_id=warehouse_id,
                    table_name=table_name,
                    source_table=source_table,
                    data_content=record,
                    data_timestamp=data_timestamp,
                    record_type=record_type,
                    archival_reason=archival_reason,
                    retention_policy=retention_policy
                )
                archived_records.append(historical_data)
            
            logger.info(f"Archived {len(archived_records)} records from {source_table}")
            
            return archived_records
            
        except Exception as e:
            logger.error(f"Error archiving historical data: {str(e)}")
            return None
    
    def _get_source_data_for_archiving(self, source_table, data_timestamp):
        """Get source data for archiving"""
        try:
            # This would query the actual source table
            # For now, return simulated data
            
            # Simulate getting data from source table
            sample_data = []
            for i in range(100):  # Simulate 100 records
                sample_data.append({
                    'id': i,
                    'timestamp': data_timestamp.isoformat(),
                    'data': f'sample_data_{i}',
                    'created_at': data_timestamp.isoformat()
                })
            
            return sample_data
            
        except Exception as e:
            logger.error(f"Error getting source data for archiving: {str(e)}")
            return []
    
    def create_data_archive(self, warehouse_id, archive_name, archive_type, archive_category,
                            archive_start_date, archive_end_date, archive_config=None,
                            compression_config=None, encryption_config=None, retention_policy=None,
                            retention_days=2555, storage_type='local', metadata=None):
        """Create a data archive"""
        if not self.archiving_enabled:
            return None
        
        try:
            archive = DataArchive.create_archive(
                warehouse_id=warehouse_id,
                archive_name=archive_name,
                archive_type=archive_type,
                archive_category=archive_category,
                archive_start_date=archive_start_date,
                archive_end_date=archive_end_date,
                archive_config=archive_config,
                compression_config=compression_config,
                encryption_config=encryption_config,
                retention_policy=retention_policy,
                retention_days=retention_days,
                storage_type=storage_type,
                metadata=metadata
            )
            
            # Initialize archive storage
            self._initialize_archive_storage(archive)
            
            return archive
            
        except Exception as e:
            logger.error(f"Error creating data archive {archive_name}: {str(e)}")
            return None
    
    def _initialize_archive_storage(self, archive):
        """Initialize archive storage"""
        try:
            # This would initialize the actual storage for the archive
            # For now, just log the initialization
            logger.info(f"Initialized storage for archive {archive.archive_name}")
            
        except Exception as e:
            logger.error(f"Error initializing storage for archive {archive.archive_name}: {str(e)}")
            raise
    
    def execute_archive_creation(self, archive_id):
        """Execute archive creation process"""
        if not self.archiving_enabled:
            return False
        
        try:
            archive = DataArchive.query.get(archive_id)
            if not archive:
                return False
            
            start_time = time.time()
            
            # Get historical data for the archive period
            historical_data = HistoricalData.get_historical_data_by_date_range(
                archive.warehouse_id,
                archive.archive_start_date,
                archive.archive_end_date
            )
            
            # Group data by table
            data_by_table = {}
            for record in historical_data:
                table_name = record.table_name
                if table_name not in data_by_table:
                    data_by_table[table_name] = []
                data_by_table[table_name].append(record)
            
            # Update archive metrics
            table_count = len(data_by_table)
            record_count = len(historical_data)
            total_size = sum(record.data_size_bytes for record in historical_data)
            
            # Store archive data
            self._store_archive_data(archive, data_by_table)
            
            # Calculate compression
            compressed_size = total_size * 0.7  # Simulate 30% compression
            compression_ratio = compressed_size / total_size if total_size > 0 else 0
            
            # Update archive metrics
            archive.update_metrics(
                table_count=table_count,
                record_count=record_count,
                total_size_bytes=total_size,
                compressed_size_bytes=compressed_size
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Archive {archive.archive_name} created in {processing_time:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing archive creation {archive_id}: {str(e)}")
            return False
    
    def _store_archive_data(self, archive, data_by_table):
        """Store archive data"""
        try:
            # This would store the actual archive data
            # For now, just log the operation
            total_records = sum(len(data) for data in data_by_table.values())
            logger.info(f"Stored {total_records} records in archive {archive.archive_name}")
            
        except Exception as e:
            logger.error(f"Error storing archive data: {str(e)}")
    
    def cleanup_expired_data(self, warehouse_id=None):
        """Clean up expired historical data and archives"""
        if not self.retention_enabled:
            return False
        
        try:
            # Clean up expired historical data
            expired_data = HistoricalData.get_expired_data(warehouse_id)
            expired_count = 0
            
            for data in expired_data:
                data.expire_data()
                expired_count += 1
            
            logger.info(f"Expired {expired_count} historical data records")
            
            # Clean up expired archives
            expired_archives = DataArchive.get_expired_archives()
            expired_archive_count = 0
            
            for archive in expired_archives:
                archive.expire_archive()
                expired_archive_count += 1
            
            logger.info(f"Expired {expired_archive_count} archives")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {str(e)}")
            return False
    
    def get_warehouse_health(self, warehouse_id):
        """Get warehouse health status"""
        try:
            warehouse = DataWarehouse.query.get(warehouse_id)
            if not warehouse:
                return None
            
            # Get pipeline health
            pipelines = AggregationPipeline.get_pipelines_by_warehouse(warehouse_id)
            total_pipelines = len(pipelines)
            active_pipelines = len([p for p in pipelines if p.status == 'active'])
            healthy_pipelines = len([p for p in pipelines if p.health_status == 'healthy'])
            
            # Get storage health
            storage_health = self._check_storage_health(warehouse)
            
            return {
                'warehouse_id': warehouse_id,
                'warehouse_name': warehouse.warehouse_name,
                'status': warehouse.status,
                'health_status': warehouse.health_status,
                'total_pipelines': total_pipelines,
                'active_pipelines': active_pipelines,
                'healthy_pipelines': healthy_pipelines,
                'storage_health': storage_health,
                'last_health_check': warehouse.last_health_check.isoformat() if warehouse.last_health_check else None
            }
            
        except Exception as e:
            logger.error(f"Error getting warehouse health {warehouse_id}: {str(e)}")
            return None
    
    def _check_storage_health(self, warehouse):
        """Check warehouse storage health"""
        try:
            # This would check the actual storage health
            # For now, return simulated health status
            
            return {
                'status': 'healthy',
                'available_space': warehouse.total_size_bytes - warehouse.used_size_bytes,
                'utilization': warehouse.used_size_bytes / max(warehouse.total_size_bytes, 1),
                'connection_status': 'connected'
            }
            
        except Exception as e:
            logger.error(f"Error checking storage health: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def get_warehouse_metrics(self, warehouse_id):
        """Get warehouse performance metrics"""
        try:
            warehouse = DataWarehouse.query.get(warehouse_id)
            if not warehouse:
                return None
            
            # Get pipeline metrics
            pipelines = AggregationPipeline.get_pipelines_by_warehouse(warehouse_id)
            total_pipelines = len(pipelines)
            active_pipelines = len([p for p in pipelines if p.status == 'active'])
            
            # Calculate pipeline metrics
            avg_processing_time = 0
            total_records_processed = sum(p.records_processed for p in pipelines)
            records_per_hour = sum(p.records_per_hour for p in pipelines)
            
            if pipelines:
                avg_processing_time = sum(p.avg_processing_time_ms for p in pipelines) / len(pipelines)
            
            # Get historical data metrics
            historical_stats = HistoricalData.get_historical_stats(warehouse_id, days=7)
            
            # Get archive metrics
            archive_stats = DataArchive.get_archive_stats(warehouse_id)
            
            return {
                'warehouse_id': warehouse_id,
                'warehouse_name': warehouse.warehouse_name,
                'timestamp': datetime.utcnow().isoformat(),
                'storage': {
                    'total_size_bytes': warehouse.total_size_bytes,
                    'used_size_bytes': warehouse.used_size_bytes,
                    'utilization': warehouse.used_size_bytes / max(warehouse.total_size_bytes, 1),
                    'compression_ratio': warehouse.compression_ratio,
                    'table_count': warehouse.table_count,
                    'row_count': warehouse.row_count
                },
                'pipelines': {
                    'total_pipelines': total_pipelines,
                    'active_pipelines': active_pipelines,
                    'avg_processing_time_ms': avg_processing_time,
                    'total_records_processed': total_records_processed,
                    'records_per_hour': records_per_hour
                },
                'historical_data': historical_stats,
                'archives': archive_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting warehouse metrics {warehouse_id}: {str(e)}")
            return None
    
    def get_system_overview(self):
        """Get system-wide overview of all warehouses"""
        try:
            warehouses = DataWarehouse.get_active_warehouses()
            
            overview = {
                'total_warehouses': len(warehouses),
                'warehouses': [],
                'system_metrics': {
                    'total_pipelines': 0,
                    'active_pipelines': 0,
                    'total_historical_records': 0,
                    'total_archives': 0,
                    'total_storage_bytes': 0
                }
            }
            
            for warehouse in warehouses:
                warehouse_info = {
                    'warehouse_id': warehouse.warehouse_id,
                    'warehouse_name': warehouse.warehouse_name,
                    'warehouse_type': warehouse.warehouse_type,
                    'status': warehouse.status,
                    'health_status': warehouse.health_status,
                    'storage_utilization': warehouse.used_size_bytes / max(warehouse.total_size_bytes, 1)
                }
                overview['warehouses'].append(warehouse_info)
                
                # Update system metrics
                pipelines = AggregationPipeline.get_pipelines_by_warehouse(warehouse.warehouse_id)
                overview['system_metrics']['total_pipelines'] += len(pipelines)
                overview['system_metrics']['active_pipelines'] += len([p for p in pipelines if p.status == 'active'])
                
                overview['system_metrics']['total_storage_bytes'] += warehouse.used_size_bytes
            
            # Get historical data stats
            historical_stats = HistoricalData.get_historical_stats()
            overview['system_metrics']['total_historical_records'] = historical_stats['total_records']
            
            # Get archive stats
            archive_stats = DataArchive.get_archive_stats()
            overview['system_metrics']['total_archives'] = archive_stats['total_archives']
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting system overview: {str(e)}")
            return None


# Global data warehouse service instance
data_warehouse_service = None

def get_data_warehouse_service():
    """Get data warehouse service instance (lazy initialization)"""
    global data_warehouse_service
    if data_warehouse_service is None:
        data_warehouse_service = DataWarehouseService()
    return data_warehouse_service
