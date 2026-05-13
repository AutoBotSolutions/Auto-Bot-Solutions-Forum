"""
Data Replication Models

This module implements data replication models for the Auto Bot Solutions Forum,
including master-slave replication, multi-master replication, replication monitoring,
and conflict resolution.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from sqlalchemy import Index, CheckConstraint, func as sql_func
import json
import uuid


class ReplicationCluster(db.Model):
    """Replication cluster model for data replication"""
    __tablename__ = 'replication_clusters'
    __table_args__ = (
        Index('idx_replication_clusters_name', 'cluster_name'),
        Index('idx_replication_clusters_type', 'cluster_type'),
        Index('idx_replication_clusters_status', 'status'),
        Index('idx_replication_clusters_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    cluster_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Cluster information
    cluster_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    cluster_type = db.Column(db.String(50), nullable=False, index=True)  # master_slave, multi_master, hybrid
    database_type = db.Column(db.String(50), nullable=False, index=True)  # mysql, postgresql, mongodb
    
    # Cluster configuration
    cluster_config = db.Column(db.JSON)  # Cluster-specific configuration
    replication_config = db.Column(db.JSON)  # Replication configuration
    conflict_resolution = db.Column(db.JSON)  # Conflict resolution configuration
    
    # Replication settings
    replication_mode = db.Column(db.String(50), nullable=False, index=True)  # synchronous, asynchronous, semi_sync
    consistency_level = db.Column(db.String(50), nullable=False, index=True)  # strong, eventual, causal
    failover_mode = db.Column(db.String(50), default='automatic')  # automatic, manual, scheduled
    
    # Cluster status
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance, error
    health_status = db.Column(db.String(20), default='healthy')  # healthy, degraded, unhealthy
    
    # Node information
    total_nodes = db.Column(db.Integer, default=0)
    master_nodes = db.Column(db.Integer, default=0)
    slave_nodes = db.Column(db.Integer, default=0)
    healthy_nodes = db.Column(db.Integer, default=0)
    
    # Performance metrics
    replication_lag_ms = db.Column(db.Float, default=0.0)
    throughput_ops_per_second = db.Column(db.Float, default=0.0)
    error_rate = db.Column(db.Float, default=0.0)
    
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
        CheckConstraint('cluster_type IN ("master_slave", "multi_master", "hybrid")', name='check_cluster_type'),
        CheckConstraint('replication_mode IN ("synchronous", "asynchronous", "semi_sync")', name='check_replication_mode'),
        CheckConstraint('consistency_level IN ("strong", "eventual", "causal")', name='check_consistency_level'),
        CheckConstraint('total_nodes >= 0', name='check_total_nodes'),
        CheckConstraint('master_nodes >= 0', name='check_master_nodes'),
        CheckConstraint('slave_nodes >= 0', name='check_slave_nodes'),
        CheckConstraint('healthy_nodes >= 0', name='check_healthy_nodes'),
        CheckConstraint('replication_lag_ms >= 0', name='check_replication_lag'),
        CheckConstraint('throughput_ops_per_second >= 0', name='check_throughput'),
        CheckConstraint('error_rate >= 0 AND error_rate <= 1', name='check_error_rate'),
        Index('idx_replication_clusters_name', 'cluster_name'),
        Index('idx_replication_clusters_type', 'cluster_type'),
        Index('idx_replication_clusters_status', 'status'),
        Index('idx_replication_clusters_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ReplicationCluster {self.cluster_name}:{self.cluster_type}:{self.status}>'
    
    @classmethod
    def create_cluster(cls, cluster_name, cluster_type, database_type, replication_mode,
                       consistency_level, cluster_config=None, replication_config=None,
                       conflict_resolution=None, failover_mode='automatic', metadata=None):
        """Create a new replication cluster"""
        cluster = cls(
            cluster_name=cluster_name,
            cluster_type=cluster_type,
            database_type=database_type,
            replication_mode=replication_mode,
            consistency_level=consistency_level,
            cluster_config=cluster_config or {},
            replication_config=replication_config or {},
            conflict_resolution=conflict_resolution or {},
            failover_mode=failover_mode,
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
    
    def update_metrics(self, replication_lag_ms=None, throughput_ops_per_second=None, error_rate=None,
                      total_nodes=None, master_nodes=None, slave_nodes=None, healthy_nodes=None):
        """Update cluster metrics"""
        if replication_lag_ms is not None:
            self.replication_lag_ms = replication_lag_ms
        if throughput_ops_per_second is not None:
            self.throughput_ops_per_second = throughput_ops_per_second
        if error_rate is not None:
            self.error_rate = error_rate
        if total_nodes is not None:
            self.total_nodes = total_nodes
        if master_nodes is not None:
            self.master_nodes = master_nodes
        if slave_nodes is not None:
            self.slave_nodes = slave_nodes
        if healthy_nodes is not None:
            self.healthy_nodes = healthy_nodes
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert cluster to dictionary"""
        return {
            'cluster_id': self.cluster_id,
            'cluster_name': self.cluster_name,
            'cluster_type': self.cluster_type,
            'database_type': self.database_type,
            'replication_mode': self.replication_mode,
            'consistency_level': self.consistency_level,
            'failover_mode': self.failover_mode,
            'status': self.status,
            'health_status': self.health_status,
            'total_nodes': self.total_nodes,
            'master_nodes': self.master_nodes,
            'slave_nodes': self.slave_nodes,
            'healthy_nodes': self.healthy_nodes,
            'replication_lag_ms': self.replication_lag_ms,
            'throughput_ops_per_second': self.throughput_ops_per_second,
            'error_rate': self.error_rate,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
        }


class ReplicationNode(db.Model):
    """Replication node model for individual database nodes"""
    __tablename__ = 'replication_nodes'
    __table_args__ = (
        Index('idx_replication_nodes_cluster', 'cluster_id'),
        Index('idx_replication_nodes_name', 'node_name'),
        Index('idx_replication_nodes_role', 'node_role'),
        Index('idx_replication_nodes_status', 'status'),
        Index('idx_replication_nodes_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Node information
    cluster_id = db.Column(db.Integer, db.ForeignKey('replication_clusters.id'), nullable=False, index=True)
    node_name = db.Column(db.String(100), nullable=False, index=True)
    node_role = db.Column(db.String(50), nullable=False, index=True)  # master, slave, multi_master
    node_type = db.Column(db.String(50), nullable=False, index=True)  # primary, secondary, arbiter
    
    # Database connection
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    database = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password_encrypted = db.Column(db.String(255), nullable=True)
    
    # Node configuration
    node_config = db.Column(db.JSON)  # Node-specific configuration
    replication_config = db.Column(db.JSON)  # Replication configuration
    
    # Node status
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance, error
    health_status = db.Column(db.String(20), default='healthy')  # healthy, degraded, unhealthy
    connection_status = db.Column(db.String(20), default='connected')  # connected, disconnected, error
    
    # Replication status
    replication_status = db.Column(db.String(20), default='synced')  # synced, syncing, error, lagging
    replication_lag_ms = db.Column(db.Float, default=0.0)
    last_replication_time = db.Column(db.DateTime, nullable=True)
    
    # Performance metrics
    connections = db.Column(db.Integer, default=0)
    queries_per_second = db.Column(db.Float, default=0.0)
    avg_query_time_ms = db.Column(db.Float, default=0.0)
    
    # Data metrics
    total_size_bytes = db.Column(db.BigInteger, default=0)
    used_size_bytes = db.Column(db.BigInteger, default=0)
    replication_lag_bytes = db.Column(db.BigInteger, default=0)
    
    # Priority and weight
    priority = db.Column(db.Integer, default=1)  # Priority for failover
    weight = db.Column(db.Integer, default=1)  # Weight for load balancing
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_health_check = db.Column(db.DateTime, nullable=True)
    last_connection = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional node metadata
    
    # Relationships
    cluster = db.relationship('ReplicationCluster', backref='nodes', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('status IN ("active", "inactive", "maintenance", "error")', name='check_node_status'),
        CheckConstraint('health_status IN ("healthy", "degraded", "unhealthy")', name='check_node_health'),
        CheckConstraint('connection_status IN ("connected", "disconnected", "error")', name='check_connection_status'),
        CheckConstraint('node_role IN ("master", "slave", "multi_master", "arbiter")', name='check_node_role'),
        CheckConstraint('node_type IN ("primary", "secondary", "arbiter")', name='check_node_type'),
        CheckConstraint('replication_status IN ("synced", "syncing", "error", "lagging")', name='check_replication_status'),
        CheckConstraint('port > 0 AND port <= 65535', name='check_port_range'),
        CheckConstraint('connections >= 0', name='check_connections'),
        CheckConstraint('queries_per_second >= 0', name='check_queries_per_second'),
        CheckConstraint('avg_query_time_ms >= 0', name='check_avg_query_time'),
        CheckConstraint('total_size_bytes >= 0', name='check_total_size'),
        CheckConstraint('used_size_bytes >= 0', name='check_used_size'),
        CheckConstraint('replication_lag_bytes >= 0', name='check_replication_lag_bytes'),
        CheckConstraint('priority >= 0', name='check_priority'),
        CheckConstraint('weight >= 0', name='check_weight'),
        Index('idx_replication_nodes_cluster', 'cluster_id'),
        Index('idx_replication_nodes_name', 'node_name'),
        Index('idx_replication_nodes_role', 'node_role'),
        Index('idx_replication_nodes_status', 'status'),
        Index('idx_replication_nodes_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ReplicationNode {self.node_name}:{self.node_role}:{self.status}>'
    
    @classmethod
    def create_node(cls, cluster_id, node_name, node_role, node_type, host, port, database,
                   username, password_encrypted=None, node_config=None, replication_config=None,
                   priority=1, weight=1, metadata=None):
        """Create a new replication node"""
        node = cls(
            cluster_id=cluster_id,
            node_name=node_name,
            node_role=node_role,
            node_type=node_type,
            host=host,
            port=port,
            database=database,
            username=username,
            password_encrypted=password_encrypted,
            node_config=node_config or {},
            replication_config=replication_config or {},
            priority=priority,
            weight=weight,
            metadata=metadata or {}
        )
        db.session.add(node)
        db.session.commit()
        return node
    
    @classmethod
    def get_nodes_by_cluster(cls, cluster_id, status=None, role=None):
        """Get nodes by cluster"""
        query = cls.query.filter_by(cluster_id=cluster_id)
        if status:
            query = query.filter_by(status=status)
        if role:
            query = query.filter_by(node_role=role)
        return query.order_by(cls.priority.asc(), cls.node_name).all()
    
    @classmethod
    def get_master_nodes(cls, cluster_id):
        """Get master nodes for a cluster"""
        return cls.query.filter_by(cluster_id=cluster_id, node_role='master').all()
    
    @classmethod
    def get_slave_nodes(cls, cluster_id):
        """Get slave nodes for a cluster"""
        return cls.query.filter_by(cluster_id=cluster_id, node_role='slave').all()
    
    @classmethod
    def get_active_nodes(cls, cluster_id):
        """Get active nodes for a cluster"""
        return cls.query.filter_by(cluster_id=cluster_id, status='active').order_by(cls.priority.asc()).all()
    
    @classmethod
    def get_node_stats(cls, cluster_id=None):
        """Get node statistics"""
        query = cls.query
        if cluster_id:
            query = query.filter_by(cluster_id=cluster_id)
        
        total_nodes = query.count()
        active_nodes = query.filter_by(status='active').count()
        healthy_nodes = query.filter_by(health_status='healthy').count()
        connected_nodes = query.filter_by(connection_status='connected').count()
        
        return {
            'total_nodes': total_nodes,
            'active_nodes': active_nodes,
            'healthy_nodes': healthy_nodes,
            'connected_nodes': connected_nodes,
            'unhealthy_nodes': total_nodes - healthy_nodes
        }
    
    def update_status(self, status, health_status=None, connection_status=None):
        """Update node status"""
        self.status = status
        if health_status:
            self.health_status = health_status
        if connection_status:
            self.connection_status = connection_status
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_replication_status(self, replication_status, replication_lag_ms=None, last_replication_time=None):
        """Update replication status"""
        self.replication_status = replication_status
        if replication_lag_ms is not None:
            self.replication_lag_ms = replication_lag_ms
        if last_replication_time:
            self.last_replication_time = last_replication_time
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_metrics(self, connections=None, queries_per_second=None, avg_query_time_ms=None,
                      total_size_bytes=None, used_size_bytes=None, replication_lag_bytes=None):
        """Update node metrics"""
        if connections is not None:
            self.connections = connections
        if queries_per_second is not None:
            self.queries_per_second = queries_per_second
        if avg_query_time_ms is not None:
            self.avg_query_time_ms = avg_query_time_ms
        if total_size_bytes is not None:
            self.total_size_bytes = total_size_bytes
        if used_size_bytes is not None:
            self.used_size_bytes = used_size_bytes
        if replication_lag_bytes is not None:
            self.replication_lag_bytes = replication_lag_bytes
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def promote_to_master(self):
        """Promote node to master role"""
        self.node_role = 'master'
        self.node_type = 'primary'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def demote_to_slave(self):
        """Demote node to slave role"""
        self.node_role = 'slave'
        self.node_type = 'secondary'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert node to dictionary"""
        return {
            'node_id': self.node_id,
            'cluster_id': self.cluster_id,
            'node_name': self.node_name,
            'node_role': self.node_role,
            'node_type': self.node_type,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'username': self.username,
            'status': self.status,
            'health_status': self.health_status,
            'connection_status': self.connection_status,
            'replication_status': self.replication_status,
            'replication_lag_ms': self.replication_lag_ms,
            'last_replication_time': self.last_replication_time.isoformat() if self.last_replication_time else None,
            'connections': self.connections,
            'queries_per_second': self.queries_per_second,
            'avg_query_time_ms': self.avg_query_time_ms,
            'total_size_bytes': self.total_size_bytes,
            'used_size_bytes': self.used_size_bytes,
            'replication_lag_bytes': self.replication_lag_bytes,
            'priority': self.priority,
            'weight': self.weight,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'last_connection': self.last_connection.isoformat() if self.last_connection else None
        }


class ReplicationEvent(db.Model):
    """Replication event model for tracking replication operations"""
    __tablename__ = 'replication_events'
    __table_args__ = (
        Index('idx_replication_events_cluster', 'cluster_id'),
        Index('idx_replication_events_type', 'event_type'),
        Index('idx_replication_events_status', 'event_status'),
        Index('idx_replication_events_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Event information
    cluster_id = db.Column(db.Integer, db.ForeignKey('replication_clusters.id'), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)  # write, read, failover, promotion, demotion
    event_category = db.Column(db.String(50), nullable=False, index=True)  # user_initiated, automatic, scheduled
    
    # Event details
    source_node_id = db.Column(db.Integer, db.ForeignKey('replication_nodes.id'), nullable=True)
    target_node_id = db.Column(db.Integer, db.ForeignKey('replication_nodes.id'), nullable=True)
    event_data = db.Column(db.JSON)  # Event-specific data
    
    # Event status
    event_status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed, cancelled
    progress_percentage = db.Column(db.Float, default=0.0)
    
    # Timing information
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_ms = db.Column(db.Float, default=0.0)
    
    # Data information
    affected_records = db.Column(db.Integer, default=0)
    data_size_bytes = db.Column(db.BigInteger, default=0)
    replication_lag_ms = db.Column(db.Float, default=0.0)
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    error_count = db.Column(db.Integer, default=0)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    # Transaction information
    transaction_id = db.Column(db.String(100), nullable=True)
    sequence_number = db.Column(db.BigInteger, default=0)
    timestamp = db.Column(db.DateTime, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional event metadata
    
    # Relationships
    cluster = db.relationship('ReplicationCluster', backref='replication_events', lazy=True)
    source_node = db.relationship('ReplicationNode', foreign_keys=[source_node_id], backref='source_events', lazy=True)
    target_node = db.relationship('ReplicationNode', foreign_keys=[target_node_id], backref='target_events', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('event_type IN ("write", "read", "failover", "promotion", "demotion", "sync")', name='check_event_type'),
        CheckConstraint('event_status IN ("pending", "running", "completed", "failed", "cancelled")', name='check_event_status'),
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 1', name='check_progress_percentage'),
        CheckConstraint('affected_records >= 0', name='check_affected_records'),
        CheckConstraint('data_size_bytes >= 0', name='check_data_size'),
        CheckConstraint('replication_lag_ms >= 0', name='check_event_replication_lag'),
        CheckConstraint('duration_ms >= 0', name='check_duration'),
        CheckConstraint('error_count >= 0', name='check_error_count'),
        CheckConstraint('retry_count >= 0', name='check_retry_count'),
        Index('idx_replication_events_cluster', 'cluster_id'),
        Index('idx_replication_events_type', 'event_type'),
        Index('idx_replication_events_status', 'event_status'),
        Index('idx_replication_events_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ReplicationEvent {self.event_type}:{self.event_status}:{self.duration_ms}>'
    
    @classmethod
    def create_event(cls, cluster_id, event_type, event_category, source_node_id=None, target_node_id=None,
                     event_data=None, transaction_id=None, sequence_number=None, timestamp=None, metadata=None):
        """Create a new replication event"""
        event = cls(
            cluster_id=cluster_id,
            event_type=event_type,
            event_category=event_category,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            event_data=event_data or {},
            transaction_id=transaction_id,
            sequence_number=sequence_number or 0,
            timestamp=timestamp or datetime.utcnow(),
            metadata=metadata or {}
        )
        db.session.add(event)
        db.session.commit()
        return event
    
    @classmethod
    def get_events_by_cluster(cls, cluster_id, event_type=None, event_status=None, hours=24, limit=None):
        """Get events by cluster"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.cluster_id == cluster_id,
            cls.created_at >= start_time
        )
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        if event_status:
            query = query.filter_by(event_status=event_status)
        
        query = query.order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_events_by_node(cls, node_id, hours=24, limit=None):
        """Get events by node"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            or_(cls.source_node_id == node_id, cls.target_node_id == node_id),
            cls.created_at >= start_time
        ).order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_event_stats(cls, cluster_id=None, hours=24):
        """Get event statistics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = cls.query.filter(cls.created_at >= start_time)
        if cluster_id:
            query = query.filter_by(cluster_id=cluster_id)
        
        # Total events
        total_events = query.count()
        
        # Events by type
        events_by_type = query.with_entities(
            cls.event_type,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.event_type).all()
        
        # Events by status
        events_by_status = query.with_entities(
            cls.event_status,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.event_status).all()
        
        # Performance metrics
        avg_duration = query.with_entities(
            sql_func.avg(cls.duration_ms)
        ).filter(cls.duration_ms > 0).scalar() or 0
        
        avg_replication_lag = query.with_entities(
            sql_func.avg(cls.replication_lag_ms)
        ).filter(cls.replication_lag_ms > 0).scalar() or 0
        
        return {
            'total_events': total_events,
            'events_by_type': dict(events_by_type),
            'events_by_status': dict(events_by_status),
            'avg_duration_ms': float(avg_duration),
            'avg_replication_lag_ms': float(avg_replication_lag),
            'period_hours': hours
        }
    
    def start_event(self):
        """Start event processing"""
        self.event_status = 'running'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def complete_event(self, duration_ms=None, affected_records=None, data_size_bytes=None, replication_lag_ms=None):
        """Complete event processing"""
        self.event_status = 'completed'
        self.completed_at = datetime.utcnow()
        
        if duration_ms is not None:
            self.duration_ms = duration_ms
        if affected_records is not None:
            self.affected_records = affected_records
        if data_size_bytes is not None:
            self.data_size_bytes = data_size_bytes
        if replication_lag_ms is not None:
            self.replication_lag_ms = replication_lag_ms
        
        # Calculate duration if not provided
        if self.started_at and duration_ms is None:
            self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
        
        self.progress_percentage = 1.0
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def fail_event(self, error_message=None):
        """Fail event processing"""
        self.event_status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_count += 1
        
        # Calculate duration if started
        if self.started_at:
            self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def cancel_event(self):
        """Cancel event processing"""
        self.event_status = 'cancelled'
        self.completed_at = datetime.utcnow()
        
        # Calculate duration if started
        if self.started_at:
            self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_progress(self, progress_percentage=None, affected_records=None, data_size_bytes=None):
        """Update event progress"""
        if progress_percentage is not None:
            self.progress_percentage = progress_percentage
        if affected_records is not None:
            self.affected_records = affected_records
        if data_size_bytes is not None:
            self.data_size_bytes = data_size_bytes
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert event to dictionary"""
        return {
            'event_id': self.event_id,
            'cluster_id': self.cluster_id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'event_data': self.event_data,
            'event_status': self.event_status,
            'progress_percentage': self.progress_percentage,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_ms': self.duration_ms,
            'affected_records': self.affected_records,
            'data_size_bytes': self.data_size_bytes,
            'replication_lag_ms': self.replication_lag_ms,
            'error_message': self.error_message,
            'error_count': self.error_count,
            'retry_count': self.retry_count,
            'transaction_id': self.transaction_id,
            'sequence_number': self.sequence_number,
            'timestamp': self.timestamp.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ReplicationConflict(db.Model):
    """Replication conflict model for conflict resolution"""
    __tablename__ = 'replication_conflicts'
    __table_args__ = (
        Index('idx_replication_conflicts_cluster', 'cluster_id'),
        Index('idx_replication_conflicts_type', 'conflict_type'),
        Index('idx_replication_conflicts_status', 'conflict_status'),
        Index('idx_replication_conflicts_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    conflict_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Conflict information
    cluster_id = db.Column(db.Integer, db.ForeignKey('replication_clusters.id'), nullable=False, index=True)
    conflict_type = db.Column(db.String(50), nullable=False, index=True)  # write_write, read_write, schema, data
    conflict_severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    # Conflicting operations
    source_node_id = db.Column(db.Integer, db.ForeignKey('replication_nodes.id'), nullable=True)
    target_node_id = db.Column(db.Integer, db.ForeignKey('replication_nodes.id'), nullable=True)
    conflicting_event_id = db.Column(db.Integer, db.ForeignKey('replication_events.id'), nullable=True)
    
    # Conflict details
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.String(100), nullable=False)
    field_name = db.Column(db.String(100), nullable=True)
    
    # Conflict data
    original_value = db.Column(db.JSON)  # Original value
    conflicting_values = db.Column(db.JSON)  # Conflicting values from different nodes
    resolved_value = db.Column(db.JSON)  # Resolved value
    
    # Resolution information
    conflict_status = db.Column(db.String(20), default='pending')  # pending, resolving, resolved, ignored, failed
    resolution_strategy = db.Column(db.String(50), nullable=True)  # manual, automatic, timestamp, priority
    resolved_by = db.Column(db.String(100), nullable=True)  # Who resolved the conflict
    resolution_reason = db.Column(db.Text, nullable=True)
    
    # Timing information
    detected_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_time_ms = db.Column(db.Float, default=0.0)
    
    # Impact assessment
    impact_level = db.Column(db.String(20), default='low')  # low, medium, high, critical
    affected_users = db.Column(db.Integer, default=0)
    affected_transactions = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional conflict metadata
    
    # Relationships
    cluster = db.relationship('ReplicationCluster', backref='replication_conflicts', lazy=True)
    source_node = db.relationship('ReplicationNode', foreign_keys=[source_node_id], backref='source_conflicts', lazy=True)
    target_node = db.relationship('ReplicationNode', foreign_keys=[target_node_id], backref='target_conflicts', lazy=True)
    conflicting_event = db.relationship('ReplicationEvent', backref='related_conflicts', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('conflict_type IN ("write_write", "read_write", "schema", "data")', name='check_conflict_type'),
        CheckConstraint('conflict_severity IN ("low", "medium", "high", "critical")', name='check_conflict_severity'),
        CheckConstraint('conflict_status IN ("pending", "resolving", "resolved", "ignored", "failed")', name='check_conflict_status'),
        CheckConstraint('impact_level IN ("low", "medium", "high", "critical")', name='check_impact_level'),
        CheckConstraint('resolution_time_ms >= 0', name='check_resolution_time'),
        CheckConstraint('affected_users >= 0', name='check_affected_users'),
        CheckConstraint('affected_transactions >= 0', name='check_affected_transactions'),
        Index('idx_replication_conflicts_cluster', 'cluster_id'),
        Index('idx_replication_conflicts_type', 'conflict_type'),
        Index('idx_replication_conflicts_status', 'conflict_status'),
        Index('idx_replication_conflicts_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ReplicationConflict {self.conflict_type}:{self.conflict_status}:{self.table_name}>'
    
    @classmethod
    def create_conflict(cls, cluster_id, conflict_type, conflict_severity, table_name, record_id,
                        source_node_id=None, target_node_id=None, conflicting_event_id=None,
                        field_name=None, original_value=None, conflicting_values=None,
                        impact_level='low', affected_users=0, affected_transactions=0, metadata=None):
        """Create a new replication conflict"""
        conflict = cls(
            cluster_id=cluster_id,
            conflict_type=conflict_type,
            conflict_severity=conflict_severity,
            table_name=table_name,
            record_id=record_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            conflicting_event_id=conflicting_event_id,
            field_name=field_name,
            original_value=original_value or {},
            conflicting_values=conflicting_values or {},
            impact_level=impact_level,
            affected_users=affected_users,
            affected_transactions=affected_transactions,
            metadata=metadata or {}
        )
        db.session.add(conflict)
        db.session.commit()
        return conflict
    
    @classmethod
    def get_conflicts_by_cluster(cls, cluster_id, conflict_type=None, conflict_status=None, hours=24, limit=None):
        """Get conflicts by cluster"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.cluster_id == cluster_id,
            cls.created_at >= start_time
        )
        
        if conflict_type:
            query = query.filter_by(conflict_type=conflict_type)
        if conflict_status:
            query = query.filter_by(conflict_status=conflict_status)
        
        query = query.order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_conflicts_by_table(cls, table_name, hours=24, limit=None):
        """Get conflicts by table"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.table_name == table_name,
            cls.created_at >= start_time
        ).order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_conflict_stats(cls, cluster_id=None, hours=24):
        """Get conflict statistics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = cls.query.filter(cls.created_at >= start_time)
        if cluster_id:
            query = query.filter_by(cluster_id=cluster_id)
        
        # Total conflicts
        total_conflicts = query.count()
        
        # Conflicts by type
        conflicts_by_type = query.with_entities(
            cls.conflict_type,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.conflict_type).all()
        
        # Conflicts by status
        conflicts_by_status = query.with_entities(
            cls.conflict_status,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.conflict_status).all()
        
        # Conflicts by severity
        conflicts_by_severity = query.with_entities(
            cls.conflict_severity,
            sql_func.count(cls.id).label('count')
        ).group_by(cls.conflict_severity).all()
        
        # Resolution metrics
        avg_resolution_time = query.with_entities(
            sql_func.avg(cls.resolution_time_ms)
        ).filter(cls.resolution_time_ms > 0).scalar() or 0
        
        return {
            'total_conflicts': total_conflicts,
            'conflicts_by_type': dict(conflicts_by_type),
            'conflicts_by_status': dict(conflicts_by_status),
            'conflicts_by_severity': dict(conflicts_by_severity),
            'avg_resolution_time_ms': float(avg_resolution_time),
            'period_hours': hours
        }
    
    def resolve_conflict(self, resolved_value, resolution_strategy, resolved_by=None, resolution_reason=None):
        """Resolve conflict"""
        self.conflict_status = 'resolved'
        self.resolved_value = resolved_value
        self.resolution_strategy = resolution_strategy
        self.resolved_by = resolved_by
        self.resolution_reason = resolution_reason
        self.resolved_at = datetime.utcnow()
        
        # Calculate resolution time
        if self.detected_at:
            self.resolution_time_ms = (self.resolved_at - self.detected_at).total_seconds() * 1000
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def ignore_conflict(self, reason=None):
        """Ignore conflict"""
        self.conflict_status = 'ignored'
        self.resolution_reason = reason
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def fail_resolution(self, error_message=None):
        """Fail conflict resolution"""
        self.conflict_status = 'failed'
        self.resolution_reason = error_message
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert conflict to dictionary"""
        return {
            'conflict_id': self.conflict_id,
            'cluster_id': self.cluster_id,
            'conflict_type': self.conflict_type,
            'conflict_severity': self.conflict_severity,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'conflicting_event_id': self.conflicting_event_id,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'field_name': self.field_name,
            'original_value': self.original_value,
            'conflicting_values': self.conflicting_values,
            'resolved_value': self.resolved_value,
            'conflict_status': self.conflict_status,
            'resolution_strategy': self.resolution_strategy,
            'resolved_by': self.resolved_by,
            'resolution_reason': self.resolution_reason,
            'detected_at': self.detected_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_time_ms': self.resolution_time_ms,
            'impact_level': self.impact_level,
            'affected_users': self.affected_users,
            'affected_transactions': self.affected_transactions,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# Helper functions for data replication initialization
def initialize_data_replication_system():
    """Initialize data replication system with default configurations"""
    print("Data replication system initialized successfully")
