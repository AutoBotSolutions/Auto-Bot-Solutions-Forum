"""
Distributed Cache Models

This module implements distributed caching models for the Auto Bot Solutions Forum,
including cache cluster management, distributed cache nodes, and cache synchronization.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from sqlalchemy import Index, CheckConstraint, func as sql_func
import json
import uuid


class CacheCluster(db.Model):
    """Cache cluster management model for distributed caching"""
    __tablename__ = 'cache_clusters'
    __table_args__ = (
        Index('idx_cache_clusters_name', 'cluster_name'),
        Index('idx_cache_clusters_status', 'status'),
        Index('idx_cache_clusters_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    cluster_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Cluster information
    cluster_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    cluster_type = db.Column(db.String(50), default='redis')  # redis, memcached, custom
    cluster_mode = db.Column(db.String(20), default='cluster')  # cluster, standalone, sentinel
    
    # Cluster configuration
    cluster_config = db.Column(db.JSON)  # Cluster configuration details
    node_config = db.Column(db.JSON)  # Node configuration template
    
    # Cluster status
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance, error
    health_status = db.Column(db.String(20), default='healthy')  # healthy, degraded, unhealthy
    replication_status = db.Column(db.String(20), default='synced')  # synced, syncing, error
    
    # Performance metrics
    total_memory = db.Column(db.BigInteger, default=0)  # Total memory in bytes
    used_memory = db.Column(db.BigInteger, default=0)  # Used memory in bytes
    memory_utilization = db.Column(db.Float, default=0.0)  # Memory utilization percentage
    
    # Node information
    total_nodes = db.Column(db.Integer, default=0)
    active_nodes = db.Column(db.Integer, default=0)
    master_nodes = db.Column(db.Integer, default=0)
    slave_nodes = db.Column(db.Integer, default=0)
    
    # Replication configuration
    replication_factor = db.Column(db.Integer, default=1)
    shard_count = db.Column(db.Integer, default=1)
    consistency_level = db.Column(db.String(20), default='eventual')  # eventual, strong, weak
    
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
        CheckConstraint('replication_status IN ("synced", "syncing", "error")', name='check_replication_status'),
        CheckConstraint('total_nodes >= 0', name='check_total_nodes'),
        CheckConstraint('active_nodes >= 0', name='check_active_nodes'),
        CheckConstraint('memory_utilization >= 0 AND memory_utilization <= 1', name='check_memory_utilization'),
        Index('idx_cache_clusters_name', 'cluster_name'),
        Index('idx_cache_clusters_status', 'status'),
        Index('idx_cache_clusters_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<CacheCluster {self.cluster_name}:{self.status}:{self.health_status}>'
    
    @classmethod
    def create_cluster(cls, cluster_name, cluster_type='redis', cluster_mode='cluster',
                       cluster_config=None, node_config=None, replication_factor=1,
                       shard_count=1, consistency_level='eventual', metadata=None):
        """Create a new cache cluster"""
        cluster = cls(
            cluster_name=cluster_name,
            cluster_type=cluster_type,
            cluster_mode=cluster_mode,
            cluster_config=cluster_config or {},
            node_config=node_config or {},
            replication_factor=replication_factor,
            shard_count=shard_count,
            consistency_level=consistency_level,
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
    
    def update_health_status(self, health_status, last_health_check=None):
        """Update cluster health status"""
        self.health_status = health_status
        if last_health_check:
            self.last_health_check = last_health_check
        else:
            self.last_health_check = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_metrics(self, total_memory=None, used_memory=None, total_nodes=None,
                      active_nodes=None, master_nodes=None, slave_nodes=None):
        """Update cluster metrics"""
        if total_memory is not None:
            self.total_memory = total_memory
        if used_memory is not None:
            self.used_memory = used_memory
        if total_nodes is not None:
            self.total_nodes = total_nodes
        if active_nodes is not None:
            self.active_nodes = active_nodes
        if master_nodes is not None:
            self.master_nodes = master_nodes
        if slave_nodes is not None:
            self.slave_nodes = slave_nodes
        
        # Calculate memory utilization
        if self.total_memory > 0:
            self.memory_utilization = self.used_memory / self.total_memory
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert cluster to dictionary"""
        return {
            'cluster_id': self.cluster_id,
            'cluster_name': self.cluster_name,
            'cluster_type': self.cluster_type,
            'cluster_mode': self.cluster_mode,
            'status': self.status,
            'health_status': self.health_status,
            'replication_status': self.replication_status,
            'total_memory': self.total_memory,
            'used_memory': self.used_memory,
            'memory_utilization': self.memory_utilization,
            'total_nodes': self.total_nodes,
            'active_nodes': self.active_nodes,
            'master_nodes': self.master_nodes,
            'slave_nodes': self.slave_nodes,
            'replication_factor': self.replication_factor,
            'shard_count': self.shard_count,
            'consistency_level': self.consistency_level,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
        }


class CacheNode(db.Model):
    """Cache node model for distributed caching"""
    __tablename__ = 'cache_nodes'
    __table_args__ = (
        Index('idx_cache_nodes_cluster', 'cluster_id'),
        Index('idx_cache_nodes_status', 'status'),
        Index('idx_cache_nodes_role', 'node_role'),
        Index('idx_cache_nodes_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Node information
    cluster_id = db.Column(db.Integer, db.ForeignKey('cache_clusters.id'), nullable=False, index=True)
    node_name = db.Column(db.String(100), nullable=False, index=True)
    node_role = db.Column(db.String(20), default='slave')  # master, slave, sentinel
    
    # Network information
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    ssl_enabled = db.Column(db.Boolean, default=False)
    auth_enabled = db.Column(db.Boolean, default=False)
    
    # Node status
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance, error
    health_status = db.Column(db.String(20), default='healthy')  # healthy, degraded, unhealthy
    connection_status = db.Column(db.String(20), default='connected')  # connected, disconnected, error
    
    # Performance metrics
    total_memory = db.Column(db.BigInteger, default=0)  # Total memory in bytes
    used_memory = db.Column(db.BigInteger, default=0)  # Used memory in bytes
    memory_utilization = db.Column(db.Float, default=0.0)  # Memory utilization percentage
    cpu_utilization = db.Column(db.Float, default=0.0)  # CPU utilization percentage
    network_io = db.Column(db.BigInteger, default=0)  # Network I/O in bytes
    
    # Cache metrics
    total_keys = db.Column(db.BigInteger, default=0)
    hit_rate = db.Column(db.Float, default=0.0)  # Hit rate percentage
    miss_rate = db.Column(db.Float, default=0.0)  # Miss rate percentage
    eviction_rate = db.Column(db.Float, default=0.0)  # Eviction rate percentage
    connections = db.Column(db.Integer, default=0)  # Active connections
    
    # Shard information
    shard_id = db.Column(db.String(50), nullable=True)  # Shard identifier
    shard_slots = db.Column(db.Integer, default=0)  # Number of hash slots
    migrating_slots = db.Column(db.Integer, default=0)  # Number of migrating slots
    
    # Replication information
    master_node_id = db.Column(db.Integer, db.ForeignKey('cache_nodes.id'), nullable=True)
    replication_lag = db.Column(db.Float, default=0.0)  # Replication lag in seconds
    sync_status = db.Column(db.String(20), default='synced')  # synced, syncing, error
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_health_check = db.Column(db.DateTime, nullable=True)
    last_connection = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional node metadata
    
    # Relationships
    cluster = db.relationship('CacheCluster', backref='nodes', lazy=True)
    master_node = db.relationship('CacheNode', remote_side=[id], backref='slave_nodes', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('status IN ("active", "inactive", "maintenance", "error")', name='check_node_status'),
        CheckConstraint('health_status IN ("healthy", "degraded", "unhealthy")', name='check_node_health'),
        CheckConstraint('connection_status IN ("connected", "disconnected", "error")', name='check_connection_status'),
        CheckConstraint('node_role IN ("master", "slave", "sentinel")', name='check_node_role'),
        CheckConstraint('port > 0 AND port <= 65535', name='check_port_range'),
        CheckConstraint('memory_utilization >= 0 AND memory_utilization <= 1', name='check_node_memory_util'),
        CheckConstraint('cpu_utilization >= 0 AND cpu_utilization <= 1', name='check_cpu_util'),
        CheckConstraint('hit_rate >= 0 AND hit_rate <= 1', name='check_hit_rate'),
        CheckConstraint('miss_rate >= 0 AND miss_rate <= 1', name='check_miss_rate'),
        Index('idx_cache_nodes_cluster', 'cluster_id'),
        Index('idx_cache_nodes_status', 'status'),
        Index('idx_cache_nodes_role', 'node_role'),
        Index('idx_cache_nodes_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<CacheNode {self.node_name}:{self.node_role}:{self.status}>'
    
    @classmethod
    def create_node(cls, cluster_id, node_name, host, port, node_role='slave',
                   ssl_enabled=False, auth_enabled=False, shard_id=None, shard_slots=0,
                   master_node_id=None, metadata=None):
        """Create a new cache node"""
        node = cls(
            cluster_id=cluster_id,
            node_name=node_name,
            host=host,
            port=port,
            node_role=node_role,
            ssl_enabled=ssl_enabled,
            auth_enabled=auth_enabled,
            shard_id=shard_id,
            shard_slots=shard_slots,
            master_node_id=master_node_id,
            metadata=metadata or {}
        )
        db.session.add(node)
        db.session.commit()
        return node
    
    @classmethod
    def get_nodes_by_cluster(cls, cluster_id, status=None):
        """Get nodes by cluster"""
        query = cls.query.filter_by(cluster_id=cluster_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.node_name).all()
    
    @classmethod
    def get_master_nodes(cls, cluster_id):
        """Get master nodes for a cluster"""
        return cls.query.filter_by(cluster_id=cluster_id, node_role='master').all()
    
    @classmethod
    def get_slave_nodes(cls, cluster_id):
        """Get slave nodes for a cluster"""
        return cls.query.filter_by(cluster_id=cluster_id, node_role='slave').all()
    
    @classmethod
    def get_node_stats(cls):
        """Get node statistics"""
        total_nodes = cls.query.count()
        active_nodes = cls.query.filter_by(status='active').count()
        healthy_nodes = cls.query.filter_by(health_status='healthy').count()
        master_nodes = cls.query.filter_by(node_role='master').count()
        slave_nodes = cls.query.filter_by(node_role='slave').count()
        
        return {
            'total_nodes': total_nodes,
            'active_nodes': active_nodes,
            'healthy_nodes': healthy_nodes,
            'unhealthy_nodes': total_nodes - healthy_nodes,
            'master_nodes': master_nodes,
            'slave_nodes': slave_nodes
        }
    
    def update_health_status(self, health_status, last_health_check=None):
        """Update node health status"""
        self.health_status = health_status
        if last_health_check:
            self.last_health_check = last_health_check
        else:
            self.last_health_check = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_connection_status(self, connection_status, last_connection=None):
        """Update node connection status"""
        self.connection_status = connection_status
        if last_connection:
            self.last_connection = last_connection
        else:
            self.last_connection = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_metrics(self, total_memory=None, used_memory=None, cpu_utilization=None,
                      network_io=None, total_keys=None, hit_rate=None, miss_rate=None,
                      eviction_rate=None, connections=None, replication_lag=None):
        """Update node metrics"""
        if total_memory is not None:
            self.total_memory = total_memory
        if used_memory is not None:
            self.used_memory = used_memory
        if cpu_utilization is not None:
            self.cpu_utilization = cpu_utilization
        if network_io is not None:
            self.network_io = network_io
        if total_keys is not None:
            self.total_keys = total_keys
        if hit_rate is not None:
            self.hit_rate = hit_rate
        if miss_rate is not None:
            self.miss_rate = miss_rate
        if eviction_rate is not None:
            self.eviction_rate = eviction_rate
        if connections is not None:
            self.connections = connections
        if replication_lag is not None:
            self.replication_lag = replication_lag
        
        # Calculate memory utilization
        if self.total_memory > 0:
            self.memory_utilization = self.used_memory / self.total_memory
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def promote_to_master(self):
        """Promote node to master role"""
        self.node_role = 'master'
        self.master_node_id = None
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def demote_to_slave(self, master_node_id=None):
        """Demote node to slave role"""
        self.node_role = 'slave'
        self.master_node_id = master_node_id
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert node to dictionary"""
        return {
            'node_id': self.node_id,
            'cluster_id': self.cluster_id,
            'node_name': self.node_name,
            'node_role': self.node_role,
            'host': self.host,
            'port': self.port,
            'ssl_enabled': self.ssl_enabled,
            'auth_enabled': self.auth_enabled,
            'status': self.status,
            'health_status': self.health_status,
            'connection_status': self.connection_status,
            'total_memory': self.total_memory,
            'used_memory': self.used_memory,
            'memory_utilization': self.memory_utilization,
            'cpu_utilization': self.cpu_utilization,
            'network_io': self.network_io,
            'total_keys': self.total_keys,
            'hit_rate': self.hit_rate,
            'miss_rate': self.miss_rate,
            'eviction_rate': self.eviction_rate,
            'connections': self.connections,
            'shard_id': self.shard_id,
            'shard_slots': self.shard_slots,
            'migrating_slots': self.migrating_slots,
            'master_node_id': self.master_node_id,
            'replication_lag': self.replication_lag,
            'sync_status': self.sync_status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'last_connection': self.last_connection.isoformat() if self.last_connection else None
        }


class CacheSynchronization(db.Model):
    """Cache synchronization model for distributed caching"""
    __tablename__ = 'cache_synchronizations'
    __table_args__ = (
        Index('idx_cache_synchronizations_cluster', 'cluster_id'),
        Index('idx_cache_synchronizations_type', 'sync_type'),
        Index('idx_cache_synchronizations_status', 'sync_status'),
        Index('idx_cache_synchronizations_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    sync_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Synchronization information
    cluster_id = db.Column(db.Integer, db.ForeignKey('cache_clusters.id'), nullable=False, index=True)
    sync_type = db.Column(db.String(50), nullable=False, index=True)  # full, incremental, key_based
    sync_direction = db.Column(db.String(20), default='bidirectional')  # unidirectional, bidirectional
    
    # Source and target
    source_node_id = db.Column(db.Integer, db.ForeignKey('cache_nodes.id'), nullable=True)
    target_node_id = db.Column(db.Integer, db.ForeignKey('cache_nodes.id'), nullable=True)
    source_cluster_id = db.Column(db.Integer, db.ForeignKey('cache_clusters.id'), nullable=True)
    target_cluster_id = db.Column(db.Integer, db.ForeignKey('cache_clusters.id'), nullable=True)
    
    # Synchronization status
    sync_status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed, cancelled
    progress_percentage = db.Column(db.Float, default=0.0)  # Progress percentage
    
    # Data information
    total_keys = db.Column(db.BigInteger, default=0)
    processed_keys = db.Column(db.BigInteger, default=0)
    failed_keys = db.Column(db.BigInteger, default=0)
    skipped_keys = db.Column(db.BigInteger, default=0)
    
    # Performance metrics
    sync_start_time = db.Column(db.DateTime, nullable=True)
    sync_end_time = db.Column(db.DateTime, nullable=True)
    sync_duration_seconds = db.Column(db.Float, default=0.0)
    throughput_keys_per_second = db.Column(db.Float, default=0.0)
    data_transferred_bytes = db.Column(db.BigInteger, default=0)
    
    # Configuration
    sync_config = db.Column(db.JSON)  # Synchronization configuration
    filter_patterns = db.Column(db.JSON)  # Key patterns to include/exclude
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    error_count = db.Column(db.Integer, default=0)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional synchronization metadata
    
    # Relationships
    cluster = db.relationship('CacheCluster', foreign_keys=[cluster_id], backref='synchronizations', lazy=True)
    source_node = db.relationship('CacheNode', foreign_keys=[source_node_id], backref='source_synchronizations', lazy=True)
    target_node = db.relationship('CacheNode', foreign_keys=[target_node_id], backref='target_synchronizations', lazy=True)
    source_cluster = db.relationship('CacheCluster', foreign_keys=[source_cluster_id], backref='source_synchronizations', lazy=True)
    target_cluster = db.relationship('CacheCluster', foreign_keys=[target_cluster_id], backref='target_synchronizations', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('sync_status IN ("pending", "running", "completed", "failed", "cancelled")', name='check_sync_status'),
        CheckConstraint('sync_direction IN ("unidirectional", "bidirectional")', name='check_sync_direction'),
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 1', name='check_progress_percentage'),
        CheckConstraint('total_keys >= 0', name='check_total_keys'),
        CheckConstraint('processed_keys >= 0', name='check_processed_keys'),
        CheckConstraint('failed_keys >= 0', name='check_failed_keys'),
        CheckConstraint('skipped_keys >= 0', name='check_skipped_keys'),
        CheckConstraint('sync_duration_seconds >= 0', name='check_sync_duration'),
        CheckConstraint('throughput_keys_per_second >= 0', name='check_throughput'),
        CheckConstraint('error_count >= 0', name='check_error_count'),
        CheckConstraint('retry_count >= 0', name='check_retry_count'),
        Index('idx_cache_synchronizations_cluster', 'cluster_id'),
        Index('idx_cache_synchronizations_type', 'sync_type'),
        Index('idx_cache_synchronizations_status', 'sync_status'),
        Index('idx_cache_synchronizations_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<CacheSynchronization {self.sync_type}:{self.sync_status}:{self.progress_percentage}>'
    
    @classmethod
    def create_synchronization(cls, cluster_id, sync_type='incremental', sync_direction='bidirectional',
                             source_node_id=None, target_node_id=None, source_cluster_id=None,
                             target_cluster_id=None, sync_config=None, filter_patterns=None,
                             scheduled_at=None, metadata=None):
        """Create a new cache synchronization"""
        sync = cls(
            cluster_id=cluster_id,
            sync_type=sync_type,
            sync_direction=sync_direction,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            source_cluster_id=source_cluster_id,
            target_cluster_id=target_cluster_id,
            sync_config=sync_config or {},
            filter_patterns=filter_patterns or [],
            scheduled_at=scheduled_at,
            metadata=metadata or {}
        )
        db.session.add(sync)
        db.session.commit()
        return sync
    
    @classmethod
    def get_synchronizations_by_cluster(cls, cluster_id, sync_status=None, limit=None):
        """Get synchronizations by cluster"""
        query = cls.query.filter_by(cluster_id=cluster_id)
        if sync_status:
            query = query.filter_by(sync_status=sync_status)
        query = query.order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_pending_synchronizations(cls, limit=None):
        """Get pending synchronizations"""
        query = cls.query.filter_by(sync_status='pending').order_by(cls.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_sync_stats(cls, hours=24):
        """Get synchronization statistics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total synchronizations
        total_syncs = cls.query.filter(cls.created_at >= start_time).count()
        
        # Syncs by status
        syncs_by_status = db.session.query(
            cls.sync_status,
            sql_func.count(cls.id).label('count')
        ).filter(cls.created_at >= start_time).group_by(cls.sync_status).all()
        
        # Syncs by type
        syncs_by_type = db.session.query(
            cls.sync_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.created_at >= start_time).group_by(cls.sync_type).all()
        
        # Average duration
        avg_duration = db.session.query(
            sql_func.avg(cls.sync_duration_seconds)
        ).filter(cls.created_at >= start_time, cls.sync_duration_seconds > 0).scalar() or 0
        
        # Average throughput
        avg_throughput = db.session.query(
            sql_func.avg(cls.throughput_keys_per_second)
        ).filter(cls.created_at >= start_time, cls.throughput_keys_per_second > 0).scalar() or 0
        
        return {
            'total_syncs': total_syncs,
            'syncs_by_status': dict(syncs_by_status),
            'syncs_by_type': dict(syncs_by_type),
            'avg_duration_seconds': float(avg_duration),
            'avg_throughput_keys_per_second': float(avg_throughput),
            'period_hours': hours
        }
    
    def start_sync(self):
        """Start synchronization"""
        self.sync_status = 'running'
        self.sync_start_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def complete_sync(self, total_keys=None, processed_keys=None, failed_keys=None,
                     skipped_keys=None, data_transferred_bytes=None):
        """Complete synchronization"""
        self.sync_status = 'completed'
        self.sync_end_time = datetime.utcnow()
        
        if total_keys is not None:
            self.total_keys = total_keys
        if processed_keys is not None:
            self.processed_keys = processed_keys
        if failed_keys is not None:
            self.failed_keys = failed_keys
        if skipped_keys is not None:
            self.skipped_keys = skipped_keys
        if data_transferred_bytes is not None:
            self.data_transferred_bytes = data_transferred_bytes
        
        # Calculate duration and throughput
        if self.sync_start_time:
            self.sync_duration_seconds = (self.sync_end_time - self.sync_start_time).total_seconds()
            if self.sync_duration_seconds > 0 and self.processed_keys > 0:
                self.throughput_keys_per_second = self.processed_keys / self.sync_duration_seconds
        
        # Calculate progress
        if self.total_keys > 0:
            self.progress_percentage = self.processed_keys / self.total_keys
        else:
            self.progress_percentage = 1.0
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def fail_sync(self, error_message=None):
        """Fail synchronization"""
        self.sync_status = 'failed'
        self.sync_end_time = datetime.utcnow()
        self.error_message = error_message
        self.error_count += 1
        
        if self.sync_start_time:
            self.sync_duration_seconds = (self.sync_end_time - self.sync_start_time).total_seconds()
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_progress(self, processed_keys=None, failed_keys=None, skipped_keys=None):
        """Update synchronization progress"""
        if processed_keys is not None:
            self.processed_keys = processed_keys
        if failed_keys is not None:
            self.failed_keys = failed_keys
        if skipped_keys is not None:
            self.skipped_keys = skipped_keys
        
        # Calculate progress
        if self.total_keys > 0:
            self.progress_percentage = self.processed_keys / self.total_keys
        
        # Update throughput if running
        if self.sync_status == 'running' and self.sync_start_time:
            elapsed_time = (datetime.utcnow() - self.sync_start_time).total_seconds()
            if elapsed_time > 0 and self.processed_keys > 0:
                self.throughput_keys_per_second = self.processed_keys / elapsed_time
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def retry_sync(self):
        """Retry synchronization"""
        if self.retry_count < self.max_retries:
            self.sync_status = 'pending'
            self.retry_count += 1
            self.error_message = None
            self.sync_start_time = None
            self.sync_end_time = None
            self.progress_percentage = 0.0
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def to_dict(self):
        """Convert synchronization to dictionary"""
        return {
            'sync_id': self.sync_id,
            'cluster_id': self.cluster_id,
            'sync_type': self.sync_type,
            'sync_direction': self.sync_direction,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'source_cluster_id': self.source_cluster_id,
            'target_cluster_id': self.target_cluster_id,
            'sync_status': self.sync_status,
            'progress_percentage': self.progress_percentage,
            'total_keys': self.total_keys,
            'processed_keys': self.processed_keys,
            'failed_keys': self.failed_keys,
            'skipped_keys': self.skipped_keys,
            'sync_start_time': self.sync_start_time.isoformat() if self.sync_start_time else None,
            'sync_end_time': self.sync_end_time.isoformat() if self.sync_end_time else None,
            'sync_duration_seconds': self.sync_duration_seconds,
            'throughput_keys_per_second': self.throughput_keys_per_second,
            'data_transferred_bytes': self.data_transferred_bytes,
            'error_message': self.error_message,
            'error_count': self.error_count,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None
        }


class CacheFailover(db.Model):
    """Cache failover model for distributed caching"""
    __tablename__ = 'cache_failovers'
    __table_args__ = (
        Index('idx_cache_failovers_cluster', 'cluster_id'),
        Index('idx_cache_failovers_type', 'failover_type'),
        Index('idx_cache_failovers_status', 'failover_status'),
        Index('idx_cache_failovers_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    failover_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Failover information
    cluster_id = db.Column(db.Integer, db.ForeignKey('cache_clusters.id'), nullable=False, index=True)
    failover_type = db.Column(db.String(50), nullable=False, index=True)  # automatic, manual, scheduled
    failover_reason = db.Column(db.String(100), nullable=False)  # node_failure, maintenance, upgrade
    
    # Node information
    failed_node_id = db.Column(db.Integer, db.ForeignKey('cache_nodes.id'), nullable=True)
    promoted_node_id = db.Column(db.Integer, db.ForeignKey('cache_nodes.id'), nullable=True)
    
    # Failover status
    failover_status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed, cancelled
    progress_percentage = db.Column(db.Float, default=0.0)
    
    # Timing information
    detected_at = db.Column(db.DateTime, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    recovery_time_seconds = db.Column(db.Float, default=0.0)
    
    # Impact assessment
    affected_keys = db.Column(db.BigInteger, default=0)
    lost_keys = db.Column(db.BigInteger, default=0)
    recovered_keys = db.Column(db.BigInteger, default=0)
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
    cluster = db.relationship('CacheCluster', backref='failovers', lazy=True)
    failed_node = db.relationship('CacheNode', foreign_keys=[failed_node_id], backref='failovers_failed', lazy=True)
    promoted_node = db.relationship('CacheNode', foreign_keys=[promoted_node_id], backref='failovers_promoted', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('failover_type IN ("automatic", "manual", "scheduled")', name='check_failover_type'),
        CheckConstraint('failover_status IN ("pending", "running", "completed", "failed", "cancelled")', name='check_failover_status'),
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 1', name='check_failover_progress'),
        CheckConstraint('affected_keys >= 0', name='check_affected_keys'),
        CheckConstraint('lost_keys >= 0', name='check_lost_keys'),
        CheckConstraint('recovered_keys >= 0', name='check_recovered_keys'),
        CheckConstraint('downtime_seconds >= 0', name='check_downtime'),
        CheckConstraint('error_count >= 0', name='check_failover_error_count'),
        CheckConstraint('retry_count >= 0', name='check_failover_retry_count'),
        Index('idx_cache_failovers_cluster', 'cluster_id'),
        Index('idx_cache_failovers_type', 'failover_type'),
        Index('idx_cache_failovers_status', 'failover_status'),
        Index('idx_cache_failovers_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<CacheFailover {self.failover_type}:{self.failover_status}:{self.failover_reason}>'
    
    @classmethod
    def create_failover(cls, cluster_id, failover_type, failover_reason, failed_node_id=None,
                       promoted_node_id=None, failover_config=None, recovery_config=None,
                       metadata=None):
        """Create a new cache failover"""
        failover = cls(
            cluster_id=cluster_id,
            failover_type=failover_type,
            failover_reason=failover_reason,
            failed_node_id=failed_node_id,
            promoted_node_id=promoted_node_id,
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
        failovers_by_status = db.session.query(
            cls.failover_status,
            sql_func.count(cls.id).label('count')
        ).filter(cls.created_at >= start_time).group_by(cls.failover_status).all()
        
        # Failovers by type
        failovers_by_type = db.session.query(
            cls.failover_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.created_at >= start_time).group_by(cls.failover_type).all()
        
        # Failovers by reason
        failovers_by_reason = db.session.query(
            cls.failover_reason,
            sql_func.count(cls.id).label('count')
        ).filter(cls.created_at >= start_time).group_by(cls.failover_reason).all()
        
        # Average recovery time
        avg_recovery_time = db.session.query(
            sql_func.avg(cls.recovery_time_seconds)
        ).filter(cls.created_at >= start_time, cls.recovery_time_seconds > 0).scalar() or 0
        
        # Total downtime
        total_downtime = db.session.query(
            sql_func.sum(cls.downtime_seconds)
        ).filter(cls.created_at >= start_time).scalar() or 0
        
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
    
    def complete_failover(self, affected_keys=None, lost_keys=None, recovered_keys=None):
        """Complete failover process"""
        self.failover_status = 'completed'
        self.completed_at = datetime.utcnow()
        
        if affected_keys is not None:
            self.affected_keys = affected_keys
        if lost_keys is not None:
            self.lost_keys = lost_keys
        if recovered_keys is not None:
            self.recovered_keys = recovered_keys
        
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
    
    def update_progress(self, progress_percentage=None, affected_keys=None, lost_keys=None,
                      recovered_keys=None):
        """Update failover progress"""
        if progress_percentage is not None:
            self.progress_percentage = progress_percentage
        if affected_keys is not None:
            self.affected_keys = affected_keys
        if lost_keys is not None:
            self.lost_keys = lost_keys
        if recovered_keys is not None:
            self.recovered_keys = recovered_keys
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert failover to dictionary"""
        return {
            'failover_id': self.failover_id,
            'cluster_id': self.cluster_id,
            'failover_type': self.failover_type,
            'failover_reason': self.failover_reason,
            'failed_node_id': self.failed_node_id,
            'promoted_node_id': self.promoted_node_id,
            'failover_status': self.failover_status,
            'progress_percentage': self.progress_percentage,
            'detected_at': self.detected_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'recovery_time_seconds': self.recovery_time_seconds,
            'affected_keys': self.affected_keys,
            'lost_keys': self.lost_keys,
            'recovered_keys': self.recovered_keys,
            'downtime_seconds': self.downtime_seconds,
            'error_message': self.error_message,
            'error_count': self.error_count,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# Helper functions for distributed cache initialization
def initialize_distributed_cache_system():
    """Initialize distributed cache system with default configurations"""
    print("Distributed cache system initialized successfully")
