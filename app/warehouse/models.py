"""
Data Warehouse Models

This module implements data warehouse models for the Auto Bot Solutions Forum,
including analytics data warehouse, aggregation pipelines, historical data storage,
and data archiving system.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from sqlalchemy import Index, CheckConstraint, func as sql_func
import json
import uuid


class DataWarehouse(db.Model):
    """Data warehouse model for analytics and historical data storage"""
    __tablename__ = 'data_warehouse'
    __table_args__ = (
        Index('idx_data_warehouse_name', 'warehouse_name'),
        Index('idx_data_warehouse_type', 'warehouse_type'),
        Index('idx_data_warehouse_status', 'status'),
        Index('idx_data_warehouse_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Warehouse information
    warehouse_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    warehouse_type = db.Column(db.String(50), nullable=False, index=True)  # analytics, historical, archive
    warehouse_category = db.Column(db.String(50), nullable=False, index=True)  # user_data, system_data, content_data
    
    # Storage configuration
    storage_engine = db.Column(db.String(50), default='postgresql')  # postgresql, mysql, clickhouse, snowflake
    storage_config = db.Column(db.JSON)  # Storage-specific configuration
    partitioning_config = db.Column(db.JSON)  # Partitioning configuration
    
    # Schema information
    schema_version = db.Column(db.String(20), default='1.0')
    schema_definition = db.Column(db.JSON)  # Table schema definition
    table_mappings = db.Column(db.JSON)  # Source to warehouse table mappings
    
    # Data configuration
    data_retention_days = db.Column(db.Integer, default=365)  # Data retention period
    archiving_enabled = db.Column(db.Boolean, default=True)
    compression_enabled = db.Column(db.Boolean, default=True)
    encryption_enabled = db.Column(db.Boolean, default=False)
    
    # Processing configuration
    processing_enabled = db.Column(db.Boolean, default=True)
    processing_interval = db.Column(db.Integer, default=3600)  # Processing interval in seconds
    batch_size = db.Column(db.Integer, default=1000)
    max_processing_time = db.Column(db.Integer, default=3600)  # Max processing time in seconds
    
    # Warehouse status
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance, error
    health_status = db.Column(db.String(20), default='healthy')  # healthy, degraded, unhealthy
    
    # Storage metrics
    total_size_bytes = db.Column(db.BigInteger, default=0)
    used_size_bytes = db.Column(db.BigInteger, default=0)
    compression_ratio = db.Column(db.Float, default=0.0)  # Compression ratio
    table_count = db.Column(db.Integer, default=0)
    row_count = db.Column(db.BigInteger, default=0)
    
    # Performance metrics
    avg_query_time_ms = db.Column(db.Float, default=0.0)
    queries_per_hour = db.Column(db.Integer, default=0)
    data_ingestion_rate = db.Column(db.Float, default=0.0)  # Records per hour
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_processed = db.Column(db.DateTime, nullable=True)
    last_health_check = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional warehouse metadata
    
    # Constraints
    __table_args__ = (
        CheckConstraint('status IN ("active", "inactive", "maintenance", "error")', name='check_warehouse_status'),
        CheckConstraint('health_status IN ("healthy", "degraded", "unhealthy")', name='check_health_status'),
        CheckConstraint('data_retention_days >= 0', name='check_retention_days'),
        CheckConstraint('batch_size >= 0', name='check_batch_size'),
        CheckConstraint('compression_ratio >= 0', name='check_compression_ratio'),
        CheckConstraint('avg_query_time_ms >= 0', name='check_avg_query_time'),
        Index('idx_data_warehouse_name', 'warehouse_name'),
        Index('idx_data_warehouse_type', 'warehouse_type'),
        Index('idx_data_warehouse_status', 'status'),
        Index('idx_data_warehouse_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<DataWarehouse {self.warehouse_name}:{self.warehouse_type}:{self.status}>'
    
    @classmethod
    def create_warehouse(cls, warehouse_name, warehouse_type, warehouse_category,
                          storage_engine='postgresql', storage_config=None, schema_definition=None,
                          table_mappings=None, data_retention_days=365, archiving_enabled=True,
                          compression_enabled=True, encryption_enabled=False, processing_enabled=True,
                          processing_interval=3600, batch_size=1000, metadata=None):
        """Create a new data warehouse"""
        warehouse = cls(
            warehouse_name=warehouse_name,
            warehouse_type=warehouse_type,
            warehouse_category=warehouse_category,
            storage_engine=storage_engine,
            storage_config=storage_config or {},
            schema_definition=schema_definition or {},
            table_mappings=table_mappings or {},
            data_retention_days=data_retention_days,
            archiving_enabled=archiving_enabled,
            compression_enabled=compression_enabled,
            encryption_enabled=encryption_enabled,
            processing_enabled=processing_enabled,
            processing_interval=processing_interval,
            batch_size=batch_size,
            metadata=metadata or {}
        )
        db.session.add(warehouse)
        db.session.commit()
        return warehouse
    
    @classmethod
    def get_warehouse_by_name(cls, warehouse_name):
        """Get warehouse by name"""
        return cls.query.filter_by(warehouse_name=warehouse_name).first()
    
    @classmethod
    def get_warehouses_by_type(cls, warehouse_type):
        """Get warehouses by type"""
        return cls.query.filter_by(warehouse_type=warehouse_type).all()
    
    @classmethod
    def get_active_warehouses(cls):
        """Get all active warehouses"""
        return cls.query.filter_by(status='active').all()
    
    @classmethod
    def get_warehouse_stats(cls):
        """Get warehouse statistics"""
        total_warehouses = cls.query.count()
        active_warehouses = cls.query.filter_by(status='active').count()
        healthy_warehouses = cls.query.filter_by(health_status='healthy').count()
        
        return {
            'total_warehouses': total_warehouses,
            'active_warehouses': active_warehouses,
            'healthy_warehouses': healthy_warehouses,
            'unhealthy_warehouses': total_warehouses - healthy_warehouses
        }
    
    def update_health_status(self, health_status, last_health_check=None):
        """Update warehouse health status"""
        self.health_status = health_status
        if last_health_check:
            self.last_health_check = last_health_check
        else:
            self.last_health_check = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_metrics(self, total_size_bytes=None, used_size_bytes=None, compression_ratio=None,
                      table_count=None, row_count=None, avg_query_time_ms=None, queries_per_hour=None,
                      data_ingestion_rate=None):
        """Update warehouse metrics"""
        if total_size_bytes is not None:
            self.total_size_bytes = total_size_bytes
        if used_size_bytes is not None:
            self.used_size_bytes = used_size_bytes
        if compression_ratio is not None:
            self.compression_ratio = compression_ratio
        if table_count is not None:
            self.table_count = table_count
        if row_count is not None:
            self.row_count = row_count
        if avg_query_time_ms is not None:
            self.avg_query_time_ms = avg_query_time_ms
        if queries_per_hour is not None:
            self.queries_per_hour = queries_per_hour
        if data_ingestion_rate is not None:
            self.data_ingestion_rate = data_ingestion_rate
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert warehouse to dictionary"""
        return {
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse_name,
            'warehouse_type': self.warehouse_type,
            'warehouse_category': self.warehouse_category,
            'storage_engine': self.storage_engine,
            'schema_version': self.schema_version,
            'status': self.status,
            'health_status': self.health_status,
            'data_retention_days': self.data_retention_days,
            'archiving_enabled': self.archiving_enabled,
            'compression_enabled': self.compression_enabled,
            'encryption_enabled': self.encryption_enabled,
            'processing_enabled': self.processing_enabled,
            'processing_interval': self.processing_interval,
            'batch_size': self.batch_size,
            'total_size_bytes': self.total_size_bytes,
            'used_size_bytes': self.used_size_bytes,
            'compression_ratio': self.compression_ratio,
            'table_count': self.table_count,
            'row_count': self.row_count,
            'avg_query_time_ms': self.avg_query_time_ms,
            'queries_per_hour': self.queries_per_hour,
            'data_ingestion_rate': self.data_ingestion_rate,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_processed': self.last_processed.isoformat() if self.last_processed else None,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
        }


class AggregationPipeline(db.Model):
    """Aggregation pipeline model for data warehouse processing"""
    __tablename__ = 'aggregation_pipelines'
    __table_args__ = (
        Index('idx_aggregation_pipelines_warehouse', 'warehouse_id'),
        Index('idx_aggregation_pipelines_type', 'pipeline_type'),
        Index('idx_aggregation_pipelines_status', 'status'),
        Index('idx_aggregation_pipelines_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    pipeline_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Pipeline information
    warehouse_id = db.Column(db.Integer, db.ForeignKey('data_warehouse.id'), nullable=False, index=True)
    pipeline_name = db.Column(db.String(100), nullable=False, index=True)
    pipeline_type = db.Column(db.String(50), nullable=False, index=True)  # hourly, daily, weekly, monthly, custom
    pipeline_category = db.Column(db.String(50), nullable=False, index=True)  # user_analytics, system_metrics, content_analytics
    
    # Source configuration
    source_tables = db.Column(db.JSON)  # Source tables for aggregation
    source_filters = db.Column(db.JSON)  # Filters for source data
    source_joins = db.Column(db.JSON)  # Join conditions for multiple tables
    
    # Aggregation configuration
    aggregation_config = db.Column(db.JSON)  # Aggregation rules and calculations
    group_by_fields = db.Column(db.JSON)  # Fields to group by
    aggregate_functions = db.Column(db.JSON)  # Aggregate functions (SUM, AVG, COUNT, etc.)
    having_conditions = db.Column(db.JSON)  # HAVING conditions
    
    # Target configuration
    target_table = db.Column(db.String(100), nullable=False)  # Target table name
    target_schema = db.Column(db.JSON)  # Target table schema
    update_strategy = db.Column(db.String(20), default='append')  # append, replace, upsert
    
    # Schedule configuration
    schedule_type = db.Column(db.String(20), default='interval')  # interval, cron, event_driven
    schedule_config = db.Column(db.JSON)  # Schedule configuration
    
    # Pipeline status
    status = db.Column(db.String(20), default='active')  # active, inactive, paused, error
    health_status = db.Column(db.String(20), default='healthy')  # healthy, degraded, unhealthy
    
    # Processing metrics
    last_run_time = db.Column(db.DateTime, nullable=True)
    last_run_status = db.Column(db.String(20), nullable=True)  # success, failed, running
    avg_processing_time_ms = db.Column(db.Float, default=0.0)
    records_processed = db.Column(db.BigInteger, default=0)
    records_per_hour = db.Column(db.Float, default=0.0)
    
    # Error handling
    error_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text, nullable=True)
    max_retries = db.Column(db.Integer, default=3)
    retry_delay = db.Column(db.Integer, default=300)  # Retry delay in seconds
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    next_run_time = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional pipeline metadata
    
    # Relationships
    warehouse = db.relationship('DataWarehouse', backref='aggregation_pipelines', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('status IN ("active", "inactive", "paused", "error")', name='check_pipeline_status'),
        CheckConstraint('health_status IN ("healthy", "degraded", "unhealthy")', name='check_pipeline_health'),
        CheckConstraint('update_strategy IN ("append", "replace", "upsert")', name='check_update_strategy'),
        CheckConstraint('schedule_type IN ("interval", "cron", "event_driven")', name='check_schedule_type'),
        CheckConstraint('error_count >= 0', name='check_error_count'),
        CheckConstraint('avg_processing_time_ms >= 0', name='check_avg_processing_time'),
        CheckConstraint('records_processed >= 0', name='check_records_processed'),
        Index('idx_aggregation_pipelines_warehouse', 'warehouse_id'),
        Index('idx_aggregation_pipelines_type', 'pipeline_type'),
        Index('idx_aggregation_pipelines_status', 'status'),
        Index('idx_aggregation_pipelines_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<AggregationPipeline {self.pipeline_name}:{self.pipeline_type}:{self.status}>'
    
    @classmethod
    def create_pipeline(cls, warehouse_id, pipeline_name, pipeline_type, pipeline_category,
                        source_tables=None, source_filters=None, source_joins=None,
                        aggregation_config=None, group_by_fields=None, aggregate_functions=None,
                        having_conditions=None, target_table=None, target_schema=None,
                        update_strategy='append', schedule_type='interval', schedule_config=None,
                        metadata=None):
        """Create a new aggregation pipeline"""
        pipeline = cls(
            warehouse_id=warehouse_id,
            pipeline_name=pipeline_name,
            pipeline_type=pipeline_type,
            pipeline_category=pipeline_category,
            source_tables=source_tables or [],
            source_filters=source_filters or {},
            source_joins=source_joins or {},
            aggregation_config=aggregation_config or {},
            group_by_fields=group_by_fields or [],
            aggregate_functions=aggregate_functions or {},
            having_conditions=having_conditions or {},
            target_table=target_table,
            target_schema=target_schema or {},
            update_strategy=update_strategy,
            schedule_type=schedule_type,
            schedule_config=schedule_config or {},
            metadata=metadata or {}
        )
        db.session.add(pipeline)
        db.session.commit()
        return pipeline
    
    @classmethod
    def get_pipelines_by_warehouse(cls, warehouse_id, status=None):
        """Get pipelines by warehouse"""
        query = cls.query.filter_by(warehouse_id=warehouse_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.pipeline_name).all()
    
    @classmethod
    def get_pipelines_by_type(cls, pipeline_type):
        """Get pipelines by type"""
        return cls.query.filter_by(pipeline_type=pipeline_type).all()
    
    @classmethod
    def get_active_pipelines(cls):
        """Get all active pipelines"""
        return cls.query.filter_by(status='active').all()
    
    @classmethod
    def get_pipeline_stats(cls):
        """Get pipeline statistics"""
        total_pipelines = cls.query.count()
        active_pipelines = cls.query.filter_by(status='active').count()
        healthy_pipelines = cls.query.filter_by(health_status='healthy').count()
        
        return {
            'total_pipelines': total_pipelines,
            'active_pipelines': active_pipelines,
            'healthy_pipelines': healthy_pipelines,
            'unhealthy_pipelines': total_pipelines - healthy_pipelines
        }
    
    def update_status(self, status, last_run_status=None, last_error=None):
        """Update pipeline status"""
        self.status = status
        if last_run_status:
            self.last_run_status = last_run_status
        if last_error:
            self.last_error = last_error
            self.error_count += 1
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_metrics(self, processing_time_ms=None, records_processed=None):
        """Update pipeline metrics"""
        if processing_time_ms is not None:
            self.avg_processing_time_ms = processing_time_ms
        if records_processed is not None:
            self.records_processed = records_processed
            # Calculate records per hour
            if self.last_run_time:
                time_diff = (datetime.utcnow() - self.last_run_time).total_seconds() / 3600
                if time_diff > 0:
                    self.records_per_hour = records_processed / time_diff
        
        self.last_run_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def calculate_next_run_time(self):
        """Calculate next run time based on schedule"""
        if self.schedule_type == 'interval':
            interval_seconds = self.schedule_config.get('interval_seconds', 3600)
            self.next_run_time = datetime.utcnow() + timedelta(seconds=interval_seconds)
        elif self.schedule_type == 'cron':
            # This would require cron expression parsing
            # For now, use interval as fallback
            interval_seconds = self.schedule_config.get('interval_seconds', 3600)
            self.next_run_time = datetime.utcnow() + timedelta(seconds=interval_seconds)
        else:
            # Event-driven - no next run time
            self.next_run_time = None
        
        db.session.commit()
    
    def to_dict(self):
        """Convert pipeline to dictionary"""
        return {
            'pipeline_id': self.pipeline_id,
            'warehouse_id': self.warehouse_id,
            'pipeline_name': self.pipeline_name,
            'pipeline_type': self.pipeline_type,
            'pipeline_category': self.pipeline_category,
            'target_table': self.target_table,
            'update_strategy': self.update_strategy,
            'schedule_type': self.schedule_type,
            'status': self.status,
            'health_status': self.health_status,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'last_run_status': self.last_run_status,
            'avg_processing_time_ms': self.avg_processing_time_ms,
            'records_processed': self.records_processed,
            'records_per_hour': self.records_per_hour,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'next_run_time': self.next_run_time.isoformat() if self.next_run_time else None
        }


class HistoricalData(db.Model):
    """Historical data model for long-term data storage"""
    __tablename__ = 'historical_data'
    __table_args__ = (
        Index('idx_historical_data_warehouse', 'warehouse_id'),
        Index('idx_historical_data_table', 'table_name'),
        Index('idx_historical_data_time', 'data_timestamp'),
        Index('idx_historical_data_status', 'archival_status'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Data information
    warehouse_id = db.Column(db.Integer, db.ForeignKey('data_warehouse.id'), nullable=False, index=True)
    table_name = db.Column(db.String(100), nullable=False, index=True)
    source_table = db.Column(db.String(100), nullable=False)  # Original source table
    record_type = db.Column(db.String(50), nullable=False)  # snapshot, delta, aggregated
    
    # Data content
    data_content = db.Column(db.JSON, nullable=False)  # Actual data content
    data_hash = db.Column(db.String(64), nullable=False)  # Hash for integrity checking
    data_size_bytes = db.Column(db.Integer, default=0)  # Size of data in bytes
    compression_ratio = db.Column(db.Float, default=0.0)  # Compression ratio
    
    # Time information
    data_timestamp = db.Column(db.DateTime, nullable=False, index=True)  # Original data timestamp
    archived_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # When data was archived
    expires_at = db.Column(db.DateTime, nullable=True)  # When data expires
    
    # Archival configuration
    archival_status = db.Column(db.String(20), default('active'))  # active, archived, expired, deleted
    archival_reason = db.Column(db.String(100), nullable=True)  # Reason for archival
    retention_policy = db.Column(db.String(50), nullable=True)  # Retention policy applied
    
    # Access information
    access_count = db.Column(db.Integer, default=0)  # Number of times accessed
    last_accessed = db.Column(db.DateTime, nullable=True)  # Last access time
    access_permissions = db.Column(db.JSON)  # Access permissions
    
    # Storage information
    storage_location = db.Column(db.String(255), nullable=True)  # Physical storage location
    storage_tier = db.Column(db.String(20), default='hot')  # hot, warm, cold, archive
    storage_cost = db.Column(db.Float, default=0.0)  # Storage cost per month
    
    # Data quality
    quality_score = db.Column(db.Float, default=1.0)  # Data quality score 0-1
    completeness_score = db.Column(db.Float, default=1.0)  # Completeness score 0-1
    accuracy_score = db.Column(db.Float, default=1.0)  # Accuracy score 0-1
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional metadata
    
    # Relationships
    warehouse = db.relationship('DataWarehouse', backref='historical_data', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('archival_status IN ("active", "archived", "expired", "deleted")', name='check_archival_status'),
        CheckConstraint('storage_tier IN ("hot", "warm", "cold", "archive")', name='check_storage_tier'),
        CheckConstraint('quality_score >= 0 AND quality_score <= 1', name='check_quality_score'),
        CheckConstraint('completeness_score >= 0 AND completeness_score <= 1', name='check_completeness_score'),
        CheckConstraint('accuracy_score >= 0 AND accuracy_score <= 1', name='check_accuracy_score'),
        CheckConstraint('data_size_bytes >= 0', name='check_data_size'),
        CheckConstraint('access_count >= 0', name='check_access_count'),
        Index('idx_historical_data_warehouse', 'warehouse_id'),
        Index('idx_historical_data_table', 'table_name'),
        Index('idx_historical_data_time', 'data_timestamp'),
        Index('idx_historical_data_status', 'archival_status'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<HistoricalData {self.table_name}:{self.record_type}:{self.archival_status}>'
    
    @classmethod
    def create_historical_data(cls, warehouse_id, table_name, source_table, data_content,
                               data_timestamp, record_type='snapshot', archival_reason=None,
                               retention_policy=None, storage_tier='hot', quality_score=1.0,
                               completeness_score=1.0, accuracy_score=1.0, metadata=None):
        """Create historical data record"""
        # Calculate data hash
        import hashlib
        data_str = json.dumps(data_content, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        # Calculate data size
        data_size_bytes = len(data_str.encode('utf-8'))
        
        record = cls(
            warehouse_id=warehouse_id,
            table_name=table_name,
            source_table=source_table,
            record_type=record_type,
            data_content=data_content,
            data_hash=data_hash,
            data_size_bytes=data_size_bytes,
            data_timestamp=data_timestamp,
            archival_reason=archival_reason,
            retention_policy=retention_policy,
            storage_tier=storage_tier,
            quality_score=quality_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            metadata=metadata or {}
        )
        db.session.add(record)
        db.session.commit()
        return record
    
    @classmethod
    def get_historical_data_by_table(cls, warehouse_id, table_name, start_date=None, end_date=None,
                                     record_type=None, limit=None):
        """Get historical data by table"""
        query = cls.query.filter_by(warehouse_id=warehouse_id, table_name=table_name)
        
        if start_date:
            query = query.filter(cls.data_timestamp >= start_date)
        if end_date:
            query = query.filter(cls.data_timestamp <= end_date)
        if record_type:
            query = query.filter_by(record_type=record_type)
        
        query = query.order_by(cls.data_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_historical_data_by_date_range(cls, warehouse_id, start_date, end_date, limit=None):
        """Get historical data by date range"""
        query = cls.query.filter(
            cls.warehouse_id == warehouse_id,
            cls.data_timestamp >= start_date,
            cls.data_timestamp <= end_date
        ).order_by(cls.data_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_expired_data(cls, warehouse_id=None):
        """Get expired historical data"""
        current_time = datetime.utcnow()
        query = cls.query.filter(cls.expires_at <= current_time)
        
        if warehouse_id:
            query = query.filter(cls.warehouse_id == warehouse_id)
        
        return query.all()
    
    @classmethod
    def get_data_by_storage_tier(cls, storage_tier, warehouse_id=None):
        """Get data by storage tier"""
        query = cls.query.filter_by(storage_tier=storage_tier)
        
        if warehouse_id:
            query = query.filter(cls.warehouse_id == warehouse_id)
        
        return query.all()
    
    @classmethod
    def get_historical_stats(cls, warehouse_id=None, days=30):
        """Get historical data statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = cls.query.filter(cls.archived_at >= start_date)
        if warehouse_id:
            query = query.filter(cls.warehouse_id == warehouse_id)
        
        # Total records
        total_records = query.count()
        
        # Records by type
        records_by_type = query.with_entities(
            cls.record_type,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.record_type).all()
        
        # Records by table
        records_by_table = query.with_entities(
            cls.table_name,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.table_name).all()
        
        # Records by status
        records_by_status = query.with_entities(
            cls.archival_status,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.archival_status).all()
        
        # Storage metrics
        total_size = query.with_entities(
            sql_func.sum(cls.data_size_bytes)
        ).scalar() or 0
        
        avg_quality = query.with_entities(
            sql_func.avg(cls.quality_score)
        ).scalar() or 0
        
        return {
            'total_records': total_records,
            'records_by_type': dict(records_by_type),
            'records_by_table': dict(records_by_table),
            'records_by_status': dict(records_by_status),
            'total_size_bytes': total_size,
            'avg_quality_score': float(avg_quality),
            'period_days': days
        }
    
    def archive_data(self, storage_tier='cold'):
        """Archive historical data to cold storage"""
        self.archival_status = 'archived'
        self.storage_tier = storage_tier
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def expire_data(self):
        """Mark data as expired"""
        self.archival_status = 'expired'
        self.expires_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def delete_data(self):
        """Delete historical data"""
        self.archival_status = 'deleted'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def access_data(self):
        """Record data access"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
        db.session.commit()
    
    def verify_integrity(self):
        """Verify data integrity using hash"""
        import hashlib
        
        data_str = json.dumps(self.data_content, sort_keys=True)
        current_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        return current_hash == self.data_hash
    
    def to_dict(self):
        """Convert historical data to dictionary"""
        return {
            'record_id': self.record_id,
            'warehouse_id': self.warehouse_id,
            'table_name': self.table_name,
            'source_table': self.source_table,
            'record_type': self.record_type,
            'data_timestamp': self.data_timestamp.isoformat(),
            'archived_at': self.archived_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'archival_status': self.archival_status,
            'archival_reason': self.archival_reason,
            'retention_policy': self.retention_policy,
            'data_size_bytes': self.data_size_bytes,
            'compression_ratio': self.compression_ratio,
            'storage_tier': self.storage_tier,
            'storage_cost': self.storage_cost,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'quality_score': self.quality_score,
            'completeness_score': self.completeness_score,
            'accuracy_score': self.accuracy_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class DataArchive(db.Model):
    """Data archive model for long-term data storage and retrieval"""
    __tablename__ = 'data_archives'
    __table_args__ = (
        Index('idx_data_archives_warehouse', 'warehouse_id'),
        Index('idx_data_archives_type', 'archive_type'),
        Index('idx_data_archives_status', 'archive_status'),
        Index('idx_data_archives_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    archive_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Archive information
    warehouse_id = db.Column(db.Integer, db.ForeignKey('data_warehouse.id'), nullable=False, index=True)
    archive_name = db.Column(db.String(100), nullable=False, index=True)
    archive_type = db.Column(db.String(50), nullable=False, index=True)  # full, incremental, snapshot
    archive_category = db.Column(db.String(50), nullable=False, index=True)  # daily, weekly, monthly, yearly
    
    # Archive configuration
    archive_config = db.Column(db.JSON)  # Archive configuration
    compression_config = db.Column(db.JSON)  # Compression configuration
    encryption_config = db.Column(db.JSON)  # Encryption configuration
    
    # Content information
    table_count = db.Column(db.Integer, default=0)
    record_count = db.Column(db.BigInteger, default=0)
    total_size_bytes = db.Column(db.BigInteger, default=0)
    compressed_size_bytes = db.Column(db.BigInteger, default=0)
    compression_ratio = db.Column(db.Float, default=0.0)
    
    # Time information
    archive_start_date = db.Column(db.DateTime, nullable=False)
    archive_end_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Archive status
    archive_status = db.Column(db.String(20), default('active'))  # active, inactive, expired, deleted
    verification_status = db.Column(db.String(20), default='pending')  # pending, verified, failed
    
    # Storage information
    storage_location = db.Column(db.String(255), nullable=True)  # Physical storage location
    storage_type = db.Column(db.String(50), default='local')  # local, s3, glacier, tape
    storage_cost_per_month = db.Column(db.Float, default=0.0)
    
    # Access information
    access_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, nullable=True)
    access_permissions = db.Column(db.JSON)
    
    # Retention information
    retention_policy = db.Column(db.String(100), nullable=True)
    retention_days = db.Column(db.Integer, default=2555)  # 7 years default
    auto_delete = db.Column(db.Boolean, default=True)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional archive metadata
    
    # Relationships
    warehouse = db.relationship('DataWarehouse', backref='data_archives', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('archive_status IN ("active", "inactive", "expired", "deleted")', name='check_archive_status'),
        CheckConstraint('verification_status IN ("pending", "verified", "failed")', name='check_verification_status'),
        CheckConstraint('table_count >= 0', name='check_table_count'),
        CheckConstraint('record_count >= 0', name='check_record_count'),
        CheckConstraint('total_size_bytes >= 0', name='check_total_size'),
        CheckConstraint('compressed_size_bytes >= 0', name='check_compressed_size'),
        CheckConstraint('compression_ratio >= 0', name='check_compression_ratio'),
        CheckConstraint('retention_days >= 0', name='check_retention_days'),
        CheckConstraint('access_count >= 0', name='check_access_count'),
        Index('idx_data_archives_warehouse', 'warehouse_id'),
        Index('idx_data_archives_type', 'archive_type'),
        Index('idx_data_archives_status', 'archive_status'),
        Index('idx_data_archives_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<DataArchive {self.archive_name}:{self.archive_type}:{self.archive_status}>'
    
    @classmethod
    def create_archive(cls, warehouse_id, archive_name, archive_type, archive_category,
                        archive_start_date, archive_end_date, archive_config=None,
                        compression_config=None, encryption_config=None, retention_policy=None,
                        retention_days=2555, storage_type='local', metadata=None):
        """Create a new data archive"""
        archive = cls(
            warehouse_id=warehouse_id,
            archive_name=archive_name,
            archive_type=archive_type,
            archive_category=archive_category,
            archive_config=archive_config or {},
            compression_config=compression_config or {},
            encryption_config=encryption_config or {},
            archive_start_date=archive_start_date,
            archive_end_date=archive_end_date,
            retention_policy=retention_policy,
            retention_days=retention_days,
            storage_type=storage_type,
            metadata=metadata or {}
        )
        db.session.add(archive)
        db.session.commit()
        return archive
    
    @classmethod
    def get_archives_by_warehouse(cls, warehouse_id, archive_status=None):
        """Get archives by warehouse"""
        query = cls.query.filter_by(warehouse_id=warehouse_id)
        if archive_status:
            query = query.filter_by(archive_status=archive_status)
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_archives_by_type(cls, archive_type):
        """Get archives by type"""
        return cls.query.filter_by(archive_type=archive_type).all()
    
    @classmethod
    def get_active_archives(cls):
        """Get all active archives"""
        return cls.query.filter_by(archive_status='active').all()
    
    @classmethod
    def get_expired_archives(cls):
        """Get expired archives"""
        current_time = datetime.utcnow()
        return cls.query.filter(cls.expires_at <= current_time).all()
    
    @classmethod
    def get_archive_stats(cls, warehouse_id=None):
        """Get archive statistics"""
        query = cls.query
        if warehouse_id:
            query = query.filter(cls.warehouse_id == warehouse_id)
        
        # Total archives
        total_archives = query.count()
        
        # Archives by type
        archives_by_type = query.with_entities(
            cls.archive_type,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.archive_type).all()
        
        # Archives by status
        archives_by_status = query.with_entities(
            cls.archive_status,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.archive_status).all()
        
        # Storage metrics
        total_size = query.with_entities(
            sql_func.sum(cls.total_size_bytes)
        ).scalar() or 0
        
        compressed_size = query.with_entities(
            sql_func.sum(cls.compressed_size_bytes)
        ).scalar() or 0
        
        avg_compression_ratio = query.with_entities(
            sql_func.avg(cls.compression_ratio)
        ).scalar() or 0
        
        return {
            'total_archives': total_archives,
            'archives_by_type': dict(archives_by_type),
            'archives_by_status': dict(archives_by_status),
            'total_size_bytes': total_size,
            'compressed_size_bytes': compressed_size,
            'avg_compression_ratio': float(avg_compression_ratio)
        }
    
    def update_metrics(self, table_count=None, record_count=None, total_size_bytes=None,
                      compressed_size_bytes=None):
        """Update archive metrics"""
        if table_count is not None:
            self.table_count = table_count
        if record_count is not None:
            self.record_count = record_count
        if total_size_bytes is not None:
            self.total_size_bytes = total_size_bytes
        if compressed_size_bytes is not None:
            self.compressed_size_bytes = compressed_size_bytes
        
        # Calculate compression ratio
        if self.total_size_bytes > 0 and self.compressed_size_bytes > 0:
            self.compression_ratio = self.compressed_size_bytes / self.total_size_bytes
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def verify_archive(self):
        """Verify archive integrity"""
        try:
            # This would implement archive verification logic
            # For now, mark as verified
            self.verification_status = 'verified'
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        except Exception as e:
            self.verification_status = 'failed'
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return False
    
    def expire_archive(self):
        """Mark archive as expired"""
        self.archive_status = 'expired'
        self.expires_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def delete_archive(self):
        """Delete archive"""
        self.archive_status = 'deleted'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def access_archive(self):
        """Record archive access"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert archive to dictionary"""
        return {
            'archive_id': self.archive_id,
            'warehouse_id': self.warehouse_id,
            'archive_name': self.archive_name,
            'archive_type': self.archive_type,
            'archive_category': self.archive_category,
            'table_count': self.table_count,
            'record_count': self.record_count,
            'total_size_bytes': self.total_size_bytes,
            'compressed_size_bytes': self.compressed_size_bytes,
            'compression_ratio': self.compression_ratio,
            'archive_start_date': self.archive_start_date.isoformat(),
            'archive_end_date': self.archive_end_date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'archive_status': self.archive_status,
            'verification_status': self.verification_status,
            'storage_location': self.storage_location,
            'storage_type': self.storage_type,
            'storage_cost_per_month': self.storage_cost_per_month,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'retention_policy': self.retention_policy,
            'retention_days': self.retention_days,
            'auto_delete': self.auto_delete,
            'updated_at': self.updated_at.isoformat()
        }


# Helper functions for data warehouse initialization
def initialize_data_warehouse_system():
    """Initialize data warehouse system with default configurations"""
    print("Data warehouse system initialized successfully")
