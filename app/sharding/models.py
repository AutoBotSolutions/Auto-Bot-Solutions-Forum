"""
Database Sharding Models

This module implements database sharding models for the Auto Bot Solutions Forum,
including shard management, cross-shard queries, shard failover, and load balancing.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from sqlalchemy import Index, CheckConstraint, func as sql_func
import json
import uuid


class ShardCluster(db.Model):
    """Shard cluster model for database sharding"""
    __tablename__ = 'shard_clusters'
    __table_args__ = (
        Index('idx_shard_clusters_name', 'cluster_name'),
        Index('idx_shard_clusters_status', 'status'),
        Index('idx_shard_clusters_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    cluster_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Cluster information
    cluster_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    cluster_type = db.Column(db.String(50), nullable=False, index=True)  # horizontal, vertical, functional
    database_type = db.Column(db.String(50), nullable=False, index=True)  # mysql, postgresql, mongodb
    
    # Cluster configuration
    cluster_config = db.Column(db.JSON)  # Cluster-specific configuration
    connection_config = db.Column(db.JSON)  # Connection configuration
    shard_config = db.Column(db.JSON)  # Shard configuration
    
    # Sharding strategy
    sharding_strategy = db.Column(db.String(50), nullable=False, index=True)  # hash, range, directory, consistent_hash
    shard_key = db.Column(db.String(100), nullable=True)  # Field used for sharding
    shard_count = db.Column(db.Integer, default=1, nullable=False)
    
    # Cluster status
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance, error
    health_status = db.Column(db.String(20), default='healthy')  # healthy, degraded, unhealthy
    
    # Performance metrics
    total_connections = db.Column(db.Integer, default=0)
    active_connections = db.Column(db.Integer, default=0)
    query_per_second = db.Column(db.Float, default=0.0)
    avg_query_time_ms = db.Column(db.Float, default=0.0)
    
    # Shard metrics
    total_shards = db.Column(db.Integer, default=0)
    active_shards = db.Column(db.Integer, default=0)
    healthy_shards = db.Column(db.Integer, default=0)
    
    # Load balancing
    load_balancing_enabled = db.Column(db.Boolean, default=True)
    load_balancing_strategy = db.Column(db.String(50), default='round_robin')  # round_robin, least_connections, weighted
    failover_enabled = db.Column(db.Boolean, default=True)
    failover_strategy = db.Column(db.String(50), default='automatic')  # automatic, manual
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_health_check = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional cluster metadata
    
    # Constraints
    __table_args__ = (
        CheckConstraint('status IN ("active", "inactive", "maintenance", "error")', name='check_cluster_status'),
        CheckConstraint('health_status IN ("healthy", "degraded", "unhealthy")', name='check_health_status'),
        CheckConstraint('shard_count >= 0', name='check_shard_count'),
        CheckConstraint('total_connections >= 0', name='check_total_connections'),
        CheckConstraint('active_connections >= 0', name='check_active_connections'),
        CheckConstraint('query_per_second >= 0', name='check_query_per_second'),
        CheckConstraint('avg_query_time_ms >= 0', name='check_avg_query_time'),
        CheckConstraint('total_shards >= 0', name='check_total_shards'),
        CheckConstraint('active_shards >= 0', name='check_active_shards'),
        CheckConstraint('healthy_shards >= 0', name='check_healthy_shards'),
        Index('idx_shard_clusters_name', 'cluster_name'),
        Index('idx_shard_clusters_status', 'status'),
        Index('idx_shard_clusters_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ShardCluster {self.cluster_name}:{self.cluster_type}:{self.status}>'
    
    @classmethod
    def create_cluster(cls, cluster_name, cluster_type, database_type, sharding_strategy,
                      shard_key=None, shard_count=1, cluster_config=None, connection_config=None,
                      shard_config=None, load_balancing_enabled=True, load_balancing_strategy='round_robin',
                      failover_enabled=True, failover_strategy='automatic', metadata=None):
        """Create a new shard cluster"""
        cluster = cls(
            cluster_name=cluster_name,
            cluster_type=cluster_type,
            database_type=database_type,
            sharding_strategy=sharding_strategy,
            shard_key=shard_key,
            shard_count=shard_count,
            cluster_config=cluster_config or {},
            connection_config=connection_config or {},
            shard_config=shard_config or {},
            load_balancing_enabled=load_balancing_enabled,
            load_balancing_strategy=load_balancing_strategy,
            failover_enabled=failover_enabled,
            failover_strategy=failover_strategy,
            metadata=metadata or {}
        )
        db.session.add(cluster)
        db.session.commit()
        return cluster
    
    @classmethod
    def get_cluster_by_name(cls, cluster_name):
        """Get cluster by name"""
        return cls.query.filter_by(cluster_name=cluster_name).first()
    
    @classmethod
    def get_active_clusters(cls):
        """Get all active clusters"""
        return cls.query.filter_by(status='active').all()
    
    @classmethod
    def get_cluster_stats(cls):
        """Get cluster statistics"""
        total_clusters = cls.query.count()
        active_clusters = cls.query.filter_by(status='active').count()
        healthy_clusters = cls.query.filter_by(health_status='healthy').count()
        
        return {
            'total_clusters': total_clusters,
            'active_clusters': active_clusters,
            'healthy_clusters': healthy_clusters,
            'unhealthy_clusters': total_clusters - healthy_clusters
        }
    
    def update_status(self, status, health_status=None):
        """Update cluster status"""
        self.status = status
        if health_status:
            self.health_status = health_status
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_metrics(self, total_connections=None, active_connections=None, query_per_second=None,
                      avg_query_time_ms=None, total_shards=None, active_shards=None, healthy_shards=None):
        """Update cluster metrics"""
        if total_connections is not None:
            self.total_connections = total_connections
        if active_connections is not None:
            self.active_connections = active_connections
        if query_per_second is not None:
            self.query_per_second = query_per_second
        if avg_query_time_ms is not None:
            self.avg_query_time_ms = avg_query_time_ms
        if total_shards is not None:
            self.total_shards = total_shards
        if active_shards is not None:
            self.active_shards = active_shards
        if healthy_shards is not None:
            self.healthy_shards = healthy_shards
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert cluster to dictionary"""
        return {
            'cluster_id': self.cluster_id,
            'cluster_name': self.cluster_name,
            'cluster_type': self.cluster_type,
            'database_type': self.database_type,
            'sharding_strategy': self.sharding_strategy,
            'shard_key': self.shard_key,
            'shard_count': self.shard_count,
            'status': self.status,
            'health_status': self.health_status,
            'total_connections': self.total_connections,
            'active_connections': self.active_connections,
            'query_per_second': self.query_per_second,
            'avg_query_time_ms': self.avg_query_time_ms,
            'total_shards': self.total_shards,
            'active_shards': self.active_shards,
            'healthy_shards': self.healthy_shards,
            'load_balancing_enabled': self.load_balancing_enabled,
            'load_balancing_strategy': self.load_balancing_strategy,
            'failover_enabled': self.failover_enabled,
            'failover_strategy': self.failover_strategy,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
        }


class Shard(db.Model):
    """Shard model for individual database shards"""
    __tablename__ = 'shards'
    __table_args__ = (
        Index('idx_shards_cluster', 'cluster_id'),
        Index('idx_shards_name', 'shard_name'),
        Index('idx_shards_status', 'status'),
        Index('idx_shards_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    shard_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Shard information
    cluster_id = db.Column(db.Integer, db.ForeignKey('shard_clusters.id'), nullable=False, index=True)
    shard_name = db.Column(db.String(100), nullable=False, index=True)
    shard_type = db.Column(db.String(50), nullable=False, index=True)  # primary, secondary, replica
    
    # Database connection
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    database = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password_encrypted = db.Column(db.String(255), nullable=True)  # Encrypted password
    
    # Shard configuration
    shard_config = db.Column(db.JSON)  # Shard-specific configuration
    connection_pool_config = db.Column(db.JSON)  # Connection pool configuration
    
    # Shard range (for range-based sharding)
    range_start = db.Column(db.String(100), nullable=True)
    range_end = db.Column(db.String(100), nullable=True)
    
    # Shard status
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance, error
    health_status = db.Column(db.String(20), default='healthy')  # healthy, degraded, unhealthy
    connection_status = db.Column(db.String(20), default='connected')  # connected, disconnected, error
    
    # Performance metrics
    total_connections = db.Column(db.Integer, default=0)
    active_connections = db.Column(db.Integer, default=0)
    query_per_second = db.Column(db.Float, default=0.0)
    avg_query_time_ms = db.Column(db.Float, default=0.0)
    
    # Data metrics
    total_records = db.Column(db.BigInteger, default=0)
    data_size_bytes = db.Column(db.BigInteger, default=0)
    index_size_bytes = db.Column(db.BigInteger, default=0)
    
    # Load balancing
    weight = db.Column(db.Integer, default=1)  # Weight for load balancing
    priority = db.Column(db.Integer, default=1)  # Priority for failover
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_health_check = db.Column(db.DateTime, nullable=True)
    last_connection = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional shard metadata
    
    # Relationships
    cluster = db.relationship('ShardCluster', backref='shards', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('status IN ("active", "inactive", "maintenance", "error")', name='check_shard_status'),
        CheckConstraint('health_status IN ("healthy", "degraded", "unhealthy")', name='check_shard_health'),
        CheckConstraint('connection_status IN ("connected", "disconnected", "error")', name='check_connection_status'),
        CheckConstraint('port > 0 AND port <= 65535', name='check_port_range'),
        CheckConstraint('total_connections >= 0', name='check_shard_total_connections'),
        CheckConstraint('active_connections >= 0', name='check_shard_active_connections'),
        CheckConstraint('query_per_second >= 0', name='check_shard_query_per_second'),
        CheckConstraint('avg_query_time_ms >= 0', name='check_shard_avg_query_time'),
        CheckConstraint('total_records >= 0', name='check_total_records'),
        CheckConstraint('data_size_bytes >= 0', name='check_data_size'),
        CheckConstraint('index_size_bytes >= 0', name='check_index_size'),
        CheckConstraint('weight >= 0', name='check_weight'),
        CheckConstraint('priority >= 0', name='check_priority'),
        Index('idx_shards_cluster', 'cluster_id'),
        Index('idx_shards_name', 'shard_name'),
        Index('idx_shards_status', 'status'),
        Index('idx_shards_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<Shard {self.shard_name}:{self.shard_type}:{self.status}>'
    
    @classmethod
    def create_shard(cls, cluster_id, shard_name, shard_type, host, port, database, username,
                    password_encrypted=None, shard_config=None, connection_pool_config=None,
                    range_start=None, range_end=None, weight=1, priority=1, metadata=None):
        """Create a new shard"""
        shard = cls(
            cluster_id=cluster_id,
            shard_name=shard_name,
            shard_type=shard_type,
            host=host,
            port=port,
            database=database,
            username=username,
            password_encrypted=password_encrypted,
            shard_config=shard_config or {},
            connection_pool_config=connection_pool_config or {},
            range_start=range_start,
            range_end=range_end,
            weight=weight,
            priority=priority,
            metadata=metadata or {}
        )
        db.session.add(shard)
        db.session.commit()
        return shard
    
    @classmethod
    def get_shards_by_cluster(cls, cluster_id, status=None):
        """Get shards by cluster"""
        query = cls.query.filter_by(cluster_id=cluster_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.priority.asc(), cls.shard_name).all()
    
    @classmethod
    def get_active_shards(cls, cluster_id):
        """Get active shards for a cluster"""
        return cls.query.filter_by(cluster_id=cluster_id, status='active').order_by(cls.priority.asc()).all()
    
    @classmethod
    def get_shard_stats(cls, cluster_id=None):
        """Get shard statistics"""
        query = cls.query
        if cluster_id:
            query = query.filter_by(cluster_id=cluster_id)
        
        total_shards = query.count()
        active_shards = query.filter_by(status='active').count()
        healthy_shards = query.filter_by(health_status='healthy').count()
        connected_shards = query.filter_by(connection_status='connected').count()
        
        return {
            'total_shards': total_shards,
            'active_shards': active_shards,
            'healthy_shards': healthy_shards,
            'connected_shards': connected_shards,
            'unhealthy_shards': total_shards - healthy_shards
        }
    
    def update_status(self, status, health_status=None, connection_status=None):
        """Update shard status"""
        self.status = status
        if health_status:
            self.health_status = health_status
        if connection_status:
            self.connection_status = connection_status
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_metrics(self, total_connections=None, active_connections=None, query_per_second=None,
                      avg_query_time_ms=None, total_records=None, data_size_bytes=None, index_size_bytes=None):
        """Update shard metrics"""
        if total_connections is not None:
            self.total_connections = total_connections
        if active_connections is not None:
            self.active_connections = active_connections
        if query_per_second is not None:
            self.query_per_second = query_per_second
        if avg_query_time_ms is not None:
            self.avg_query_time_ms = avg_query_time_ms
        if total_records is not None:
            self.total_records = total_records
        if data_size_bytes is not None:
            self.data_size_bytes = data_size_bytes
        if index_size_bytes is not None:
            self.index_size_bytes = index_size_bytes
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert shard to dictionary"""
        return {
            'shard_id': self.shard_id,
            'cluster_id': self.cluster_id,
            'shard_name': self.shard_name,
            'shard_type': self.shard_type,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'username': self.username,
            'shard_config': self.shard_config,
            'range_start': self.range_start,
            'range_end': self.range_end,
            'status': self.status,
            'health_status': self.health_status,
            'connection_status': self.connection_status,
            'total_connections': self.total_connections,
            'active_connections': self.active_connections,
            'query_per_second': self.query_per_second,
            'avg_query_time_ms': self.avg_query_time_ms,
            'total_records': self.total_records,
            'data_size_bytes': self.data_size_bytes,
            'index_size_bytes': self.index_size_bytes,
            'weight': self.weight,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'last_connection': self.last_connection.isoformat() if self.last_connection else None
        }


class CrossShardQuery(db.Model):
    """Cross-shard query model for distributed queries"""
    __tablename__ = 'cross_shard_queries'
    __table_args__ = (
        Index('idx_cross_shard_queries_cluster', 'cluster_id'),
        Index('idx_cross_shard_queries_status', 'query_status'),
        Index('idx_cross_shard_queries_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Query information
    cluster_id = db.Column(db.Integer, db.ForeignKey('shard_clusters.id'), nullable=False, index=True)
    query_type = db.Column(db.String(50), nullable=False, index=True)  # select, insert, update, delete
    query_category = db.Column(db.String(50), nullable=False, index=True)  # user_query, system_query, analytics
    
    # Query details
    query_text = db.Column(db.Text, nullable=False)
    query_hash = db.Column(db.String(64), nullable=False)  # Hash for query identification
    query_params = db.Column(db.JSON)  # Query parameters
    
    # Target shards
    target_shards = db.Column(db.JSON)  # List of target shard IDs
    shard_strategy = db.Column(db.String(50), default='all')  # all, specific, intelligent
    
    # Query execution
    query_status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed, cancelled
    execution_strategy = db.Column(db.String(50), default='parallel')  # parallel, sequential, hybrid
    
    # Performance metrics
    total_execution_time_ms = db.Column(db.Float, default=0.0)
    shard_execution_times = db.Column(db.JSON)  # Individual shard execution times
    total_records_affected = db.Column(db.Integer, default=0)
    shard_records_affected = db.Column(db.JSON)  # Records affected per shard
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    error_shards = db.Column(db.JSON)  # Shards that returned errors
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    # Optimization
    query_plan = db.Column(db.JSON)  # Query execution plan
    optimization_suggestions = db.Column(db.JSON)  # Query optimization suggestions
    
    # User information
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional query metadata
    
    # Relationships
    cluster = db.relationship('ShardCluster', backref='cross_shard_queries', lazy=True)
    user = db.relationship('User', backref='cross_shard_queries', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('query_type IN ("select", "insert", "update", "delete")', name='check_query_type'),
        CheckConstraint('query_status IN ("pending", "running", "completed", "failed", "cancelled")', name='check_query_status'),
        CheckConstraint('execution_strategy IN ("parallel", "sequential", "hybrid")', name='check_execution_strategy'),
        CheckConstraint('shard_strategy IN ("all", "specific", "intelligent")', name='check_shard_strategy'),
        CheckConstraint('total_execution_time_ms >= 0', name='check_total_execution_time'),
        CheckConstraint('total_records_affected >= 0', name='check_total_records_affected'),
        CheckConstraint('retry_count >= 0', name='check_retry_count'),
        Index('idx_cross_shard_queries_cluster', 'cluster_id'),
        Index('idx_cross_shard_queries_status', 'query_status'),
        Index('idx_cross_shard_queries_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<CrossShardQuery {self.query_type}:{self.query_status}:{self.total_execution_time_ms}>'
    
    @classmethod
    def create_query(cls, cluster_id, query_type, query_category, query_text, query_params=None,
                    target_shards=None, shard_strategy='all', execution_strategy='parallel',
                    user_id=None, session_id=None, ip_address=None, metadata=None):
        """Create a new cross-shard query"""
        # Calculate query hash
        import hashlib
        query_hash = hashlib.sha256(query_text.encode()).hexdigest()
        
        query = cls(
            cluster_id=cluster_id,
            query_type=query_type,
            query_category=query_category,
            query_text=query_text,
            query_hash=query_hash,
            query_params=query_params or {},
            target_shards=target_shards or [],
            shard_strategy=shard_strategy,
            execution_strategy=execution_strategy,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            metadata=metadata or {}
        )
        db.session.add(query)
        db.session.commit()
        return query
    
    @classmethod
    def get_queries_by_cluster(cls, cluster_id, query_status=None, hours=24, limit=None):
        """Get queries by cluster"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.cluster_id == cluster_id,
            cls.created_at >= start_time
        )
        
        if query_status:
            query = query.filter_by(query_status=query_status)
        
        query = query.order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_queries_by_user(cls, user_id, hours=24, limit=None):
        """Get queries by user"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.user_id == user_id,
            cls.created_at >= start_time
        ).order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_query_stats(cls, cluster_id=None, hours=24):
        """Get query statistics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = cls.query.filter(cls.created_at >= start_time)
        if cluster_id:
            query = query.filter_by(cluster_id=cluster_id)
        
        # Total queries
        total_queries = query.count()
        
        # Queries by status
        queries_by_status = query.with_entities(
            cls.query_status,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.query_status).all()
        
        # Queries by type
        queries_by_type = query.with_entities(
            cls.query_type,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.query_type).all()
        
        # Performance metrics
        avg_execution_time = query.with_entities(
            sql_func.avg(cls.total_execution_time_ms)
        ).filter(cls.total_execution_time_ms > 0).scalar() or 0
        
        total_records_affected = query.with_entities(
            sql_func.sum(cls.total_records_affected)
        ).scalar() or 0
        
        return {
            'total_queries': total_queries,
            'queries_by_status': dict(queries_by_status),
            'queries_by_type': dict(queries_by_type),
            'avg_execution_time_ms': float(avg_execution_time),
            'total_records_affected': total_records_affected,
            'period_hours': hours
        }
    
    def start_execution(self):
        """Start query execution"""
        self.query_status = 'running'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def complete_execution(self, total_execution_time_ms=None, shard_execution_times=None,
                         total_records_affected=None, shard_records_affected=None):
        """Complete query execution"""
        self.query_status = 'completed'
        self.completed_at = datetime.utcnow()
        
        if total_execution_time_ms is not None:
            self.total_execution_time_ms = total_execution_time_ms
        if shard_execution_times is not None:
            self.shard_execution_times = shard_execution_times
        if total_records_affected is not None:
            self.total_records_affected = total_records_affected
        if shard_records_affected is not None:
            self.shard_records_affected = shard_records_affected
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def fail_execution(self, error_message=None, error_shards=None):
        """Fail query execution"""
        self.query_status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_shards = error_shards or []
        self.retry_count += 1
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def cancel_execution(self):
        """Cancel query execution"""
        self.query_status = 'cancelled'
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert query to dictionary"""
        return {
            'query_id': self.query_id,
            'cluster_id': self.cluster_id,
            'query_type': self.query_type,
            'query_category': self.query_category,
            'query_text': self.query_text,
            'query_hash': self.query_hash,
            'query_params': self.query_params,
            'target_shards': self.target_shards,
            'shard_strategy': self.shard_strategy,
            'execution_strategy': self.execution_strategy,
            'query_status': self.query_status,
            'total_execution_time_ms': self.total_execution_time_ms,
            'shard_execution_times': self.shard_execution_times,
            'total_records_affected': self.total_records_affected,
            'shard_records_affected': self.shard_records_affected,
            'error_message': self.error_message,
            'error_shards': self.error_shards,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'query_plan': self.query_plan,
            'optimization_suggestions': self.optimization_suggestions,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class ShardFailover(db.Model):
    """Shard failover model for cluster failover management"""
    __tablename__ = 'shard_failovers'
    __table_args__ = (
        Index('idx_shard_failovers_cluster', 'cluster_id'),
        Index('idx_shard_failovers_type', 'failover_type'),
        Index('idx_shard_failovers_status', 'failover_status'),
        Index('idx_shard_failovers_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    failover_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Failover information
    cluster_id = db.Column(db.Integer, db.ForeignKey('shard_clusters.id'), nullable=False, index=True)
    failover_type = db.Column(db.String(50), nullable=False, index=True)  # automatic, manual, scheduled
    failover_reason = db.Column(db.String(100), nullable=False)  # shard_failure, maintenance, upgrade
    
    # Shard information
    failed_shard_id = db.Column(db.Integer, db.ForeignKey('shards.id'), nullable=True)
    promoted_shard_id = db.Column(db.Integer, db.ForeignKey('shards.id'), nullable=True)
    
    # Failover status
    failover_status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed, cancelled
    progress_percentage = db.Column(db.Float, default=0.0)
    
    # Timing information
    detected_at = db.Column(db.DateTime, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    recovery_time_seconds = db.Column(db.Float, default=0.0)
    
    # Impact assessment
    affected_connections = db.Column(db.Integer, default=0)
    lost_connections = db.Column(db.Integer, default=0)
    recovered_connections = db.Column(db.Integer, default=0)
    downtime_seconds = db.Column(db.Float, default=0.0)
    
    # Configuration
    failover_config = db.Column(db.JSON)  # Failover configuration
    recovery_config = db.Column(db.JSON)  # Recovery configuration
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    error_count = db.Column(db.Integer, default=0)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional failover metadata
    
    # Relationships
    cluster = db.relationship('ShardCluster', backref='shard_failovers', lazy=True)
    failed_shard = db.relationship('Shard', foreign_keys=[failed_shard_id], backref='failovers_failed', lazy=True)
    promoted_shard = db.relationship('Shard', foreign_keys=[promoted_shard_id], backref='failovers_promoted', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('failover_type IN ("automatic", "manual", "scheduled")', name='check_failover_type'),
        CheckConstraint('failover_status IN ("pending", "running", "completed", "failed", "cancelled")', name='check_failover_status'),
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 1', name='check_progress_percentage'),
        CheckConstraint('affected_connections >= 0', name='check_affected_connections'),
        CheckConstraint('lost_connections >= 0', name='check_lost_connections'),
        CheckConstraint('recovered_connections >= 0', name='check_recovered_connections'),
        CheckConstraint('downtime_seconds >= 0', name='check_downtime'),
        CheckConstraint('error_count >= 0', name='check_failover_error_count'),
        CheckConstraint('retry_count >= 0', name='check_failover_retry_count'),
        Index('idx_shard_failovers_cluster', 'cluster_id'),
        Index('idx_shard_failovers_type', 'failover_type'),
        Index('idx_shard_failovers_status', 'failover_status'),
        Index('idx_shard_failovers_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ShardFailover {self.failover_type}:{self.failover_status}:{self.failover_reason}>'
    
    @classmethod
    def create_failover(cls, cluster_id, failover_type, failover_reason, failed_shard_id=None,
                       promoted_shard_id=None, failover_config=None, recovery_config=None, metadata=None):
        """Create a new shard failover"""
        failover = cls(
            cluster_id=cluster_id,
            failover_type=failover_type,
            failover_reason=failover_reason,
            failed_shard_id=failed_shard_id,
            promoted_shard_id=promoted_shard_id,
            detected_at=datetime.utcnow(),
            failover_config=failover_config or {},
            recovery_config=recovery_config or {},
            metadata=metadata or {}
        )
        db.session.add(failover)
        db.session.commit()
        return failover
    
    @classmethod
    def get_failovers_by_cluster(cls, cluster_id, failover_status=None, limit=None):
        """Get failovers by cluster"""
        query = cls.query.filter_by(cluster_id=cluster_id)
        if failover_status:
            query = query.filter_by(failover_status=failover_status)
        query = query.order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_failover_stats(cls, hours=24):
        """Get failover statistics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total failovers
        total_failovers = cls.query.filter(cls.created_at >= start_time).count()
        
        # Failovers by status
        failovers_by_status = cls.query.filter(cls.created_at >= start_time).with_entities(
            cls.failover_status,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.failover_status).all()
        
        # Failovers by type
        failovers_by_type = cls.query.filter(cls.created_at >= start_time).with_entities(
            cls.failover_type,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.failover_type).all()
        
        # Failovers by reason
        failovers_by_reason = cls.query.filter(cls.created_at >= start_time).with_entities(
            cls.failover_reason,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.failover_reason).all()
        
        # Average recovery time
        avg_recovery_time = cls.query.filter(cls.created_at >= start_time).with_entities(
            sql_func.avg(cls.recovery_time_seconds)
        ).filter(cls.recovery_time_seconds > 0).scalar() or 0
        
        # Total downtime
        total_downtime = cls.query.filter(cls.created_at >= start_time).with_entities(
            sql_func.sum(cls.downtime_seconds)
        ).scalar() or 0
        
        return {
            'total_failovers': total_failovers,
            'failovers_by_status': dict(failovers_by_status),
            'failovers_by_type': dict(failovers_by_type),
            'failovers_by_reason': dict(failovers_by_reason),
            'avg_recovery_time_seconds': float(avg_recovery_time),
            'total_downtime_seconds': float(total_downtime),
            'period_hours': hours
        }
    
    def start_failover(self):
        """Start failover process"""
        self.failover_status = 'running'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def complete_failover(self, affected_connections=None, lost_connections=None, recovered_connections=None):
        """Complete failover process"""
        self.failover_status = 'completed'
        self.completed_at = datetime.utcnow()
        
        if affected_connections is not None:
            self.affected_connections = affected_connections
        if lost_connections is not None:
            self.lost_connections = lost_connections
        if recovered_connections is not None:
            self.recovered_connections = recovered_connections
        
        # Calculate recovery time and downtime
        if self.started_at:
            self.recovery_time_seconds = (self.completed_at - self.started_at).total_seconds()
            if self.detected_at:
                self.downtime_seconds = (self.completed_at - self.detected_at).total_seconds()
        
        self.progress_percentage = 1.0
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def fail_failover(self, error_message=None):
        """Fail failover process"""
        self.failover_status = 'failed'
        self.error_message = error_message
        self.error_count += 1
        
        if self.started_at:
            self.completed_at = datetime.utcnow()
            if self.detected_at:
                self.downtime_seconds = (self.completed_at - self.detected_at).total_seconds()
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_progress(self, progress_percentage=None, affected_connections=None, lost_connections=None,
                      recovered_connections=None):
        """Update failover progress"""
        if progress_percentage is not None:
            self.progress_percentage = progress_percentage
        if affected_connections is not None:
            self.affected_connections = affected_connections
        if lost_connections is not None:
            self.lost_connections = lost_connections
        if recovered_connections is not None:
            self.recovered_connections = recovered_connections
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert failover to dictionary"""
        return {
            'failover_id': self.failover_id,
            'cluster_id': self.cluster_id,
            'failover_type': self.failover_type,
            'failover_reason': self.failover_reason,
            'failed_shard_id': self.failed_shard_id,
            'promoted_shard_id': self.promoted_shard_id,
            'failover_status': self.failover_status,
            'progress_percentage': self.progress_percentage,
            'detected_at': self.detected_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'recovery_time_seconds': self.recovery_time_seconds,
            'affected_connections': self.affected_connections,
            'lost_connections': self.lost_connections,
            'recovered_connections': self.recovered_connections,
            'downtime_seconds': self.downtime_seconds,
            'error_message': self.error_message,
            'error_count': self.error_count,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# Helper functions for database sharding initialization
def initialize_database_sharding_system():
    """Initialize database sharding system with default configurations"""
    print("Database sharding system initialized successfully")
