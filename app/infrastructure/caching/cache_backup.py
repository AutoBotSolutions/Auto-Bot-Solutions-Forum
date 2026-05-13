"""
Cache Backup Manager

Manages backup strategies and operations for cache infrastructure including
automated backups, restoration, and disaster recovery.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import threading
import os
import gzip
import shutil
import subprocess
from pathlib import Path
import redis
from redis.cluster import RedisCluster

logger = logging.getLogger(__name__)

class BackupType(Enum):
    """Backup types"""
    FULL = "full"
    INCREMENTAL = "incremental"
    SNAPSHOT = "snapshot"
    RDB = "rdb"
    AOF = "aof"

class BackupStatus(Enum):
    """Backup status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BackupConfig:
    """Backup configuration"""
    backup_dir: str = "/var/cache/backups"
    backup_interval: int = 3600  # 1 hour
    retention_days: int = 7
    compression_enabled: bool = True
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    remote_backup_enabled: bool = False
    remote_backup_url: Optional[str] = None
    max_concurrent_backups: int = 2
    backup_timeout: int = 3600  # 1 hour
    verify_backup: bool = True
    backup_on_shutdown: bool = True

@dataclass
class BackupJob:
    """Backup job definition"""
    id: str
    backup_type: BackupType
    nodes: List[str] = field(default_factory=list)
    status: BackupStatus = BackupStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: int = 0
    error_message: Optional[str] = None
    progress: float = 0.0

@dataclass
class BackupStats:
    """Backup statistics"""
    total_backups: int = 0
    successful_backups: int = 0
    failed_backups: int = 0
    total_size: int = 0
    avg_backup_time: float = 0.0
    last_backup_time: Optional[datetime] = None
    next_backup_time: Optional[datetime] = None

class CacheBackupManager:
    """Manages cache backup operations and strategies"""
    
    def __init__(self, config: BackupConfig = None, redis_client=None, redis_cluster=None):
        self.config = config or BackupConfig()
        self.redis_client = redis_client
        self.redis_cluster = redis_cluster
        self.backup_jobs: Dict[str, BackupJob] = {}
        self.backup_stats = BackupStats()
        self.backup_thread = None
        self.backup_enabled = True
        self.current_backups = 0
        
        # Ensure backup directory exists
        Path(self.config.backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Start backup scheduler
        self._start_backup_scheduler()
    
    def _start_backup_scheduler(self):
        """Start background backup scheduler"""
        def backup_scheduler():
            while self.backup_enabled:
                try:
                    # Check if it's time for backup
                    if self._should_run_backup():
                        self._run_scheduled_backup()
                    
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Backup scheduler error: {e}")
                    time.sleep(60)
        
        self.backup_thread = threading.Thread(target=backup_scheduler, daemon=True)
        self.backup_thread.start()
        logger.info("Cache backup scheduler started")
    
    def _should_run_backup(self) -> bool:
        """Check if backup should run"""
        if not self.backup_enabled:
            return False
        
        if self.current_backups >= self.config.max_concurrent_backups:
            return False
        
        # Check if enough time has passed since last backup
        if self.backup_stats.last_backup_time:
            elapsed = (datetime.utcnow() - self.backup_stats.last_backup_time).total_seconds()
            return elapsed >= self.config.backup_interval
        
        return True
    
    def _run_scheduled_backup(self):
        """Run scheduled backup"""
        try:
            backup_id = f"scheduled_{int(time.time())}"
            self.create_backup(backup_id, BackupType.FULL)
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
    
    def create_backup(self, backup_id: str, backup_type: BackupType, 
                     nodes: List[str] = None) -> str:
        """Create a backup job"""
        if self.current_backups >= self.config.max_concurrent_backups:
            raise Exception("Maximum concurrent backups reached")
        
        # Determine nodes to backup
        if not nodes:
            nodes = self._get_all_nodes()
        
        # Create backup job
        backup_job = BackupJob(
            id=backup_id,
            backup_type=backup_type,
            nodes=nodes
        )
        
        self.backup_jobs[backup_id] = backup_job
        self.current_backups += 1
        
        # Start backup in background
        threading.Thread(
            target=self._execute_backup,
            args=(backup_job,),
            daemon=True
        ).start()
        
        logger.info(f"Created backup job: {backup_id} ({backup_type.value})")
        return backup_id
    
    def _get_all_nodes(self) -> List[str]:
        """Get all Redis nodes"""
        nodes = []
        
        if self.redis_cluster:
            # Get cluster nodes
            cluster_nodes = self.redis_cluster.cluster_nodes()
            for node_info in cluster_nodes.split('\n'):
                if node_info:
                    parts = node_info.split()
                    if len(parts) >= 2:
                        nodes.append(parts[1])
        elif self.redis_client:
            # Single node
            info = self.redis_client.info()
            host = self.redis_client.connection_pool.get_connection('localhost').host
            port = self.redis_client.connection_pool.get_connection('localhost').port
            nodes.append(f"{host}:{port}")
        
        return nodes
    
    def _execute_backup(self, backup_job: BackupJob):
        """Execute backup job"""
        try:
            backup_job.status = BackupStatus.RUNNING
            backup_job.started_at = datetime.utcnow()
            
            # Create backup file path
            timestamp = backup_job.started_at.strftime("%Y%m%d_%H%M%S")
            filename = f"{backup_job.id}_{backup_job.backup_type.value}_{timestamp}.rdb"
            backup_job.file_path = os.path.join(self.config.backup_dir, filename)
            
            # Execute backup based on type
            if backup_job.backup_type == BackupType.FULL:
                self._execute_full_backup(backup_job)
            elif backup_job.backup_type == BackupType.INCREMENTAL:
                self._execute_incremental_backup(backup_job)
            elif backup_job.backup_type == BackupType.SNAPSHOT:
                self._execute_snapshot_backup(backup_job)
            elif backup_job.backup_type == BackupType.RDB:
                self._execute_rdb_backup(backup_job)
            elif backup_job.backup_type == BackupType.AOF:
                self._execute_aof_backup(backup_job)
            
            # Compress backup if enabled
            if self.config.compression_enabled:
                self._compress_backup(backup_job)
            
            # Verify backup if enabled
            if self.config.verify_backup:
                self._verify_backup(backup_job)
            
            # Upload to remote storage if enabled
            if self.config.remote_backup_enabled:
                self._upload_remote_backup(backup_job)
            
            backup_job.status = BackupStatus.COMPLETED
            backup_job.completed_at = datetime.utcnow()
            backup_job.progress = 100.0
            
            # Update stats
            self.backup_stats.total_backups += 1
            self.backup_stats.successful_backups += 1
            self.backup_stats.total_size += backup_job.file_size
            self.backup_stats.last_backup_time = backup_job.completed_at
            
            # Calculate average backup time
            if backup_job.started_at and backup_job.completed_at:
                backup_time = (backup_job.completed_at - backup_job.started_at).total_seconds()
                total_time = self.backup_stats.avg_backup_time * (self.backup_stats.successful_backups - 1)
                self.backup_stats.avg_backup_time = (total_time + backup_time) / self.backup_stats.successful_backups
            
            logger.info(f"Backup completed: {backup_job.id}")
            
        except Exception as e:
            backup_job.status = BackupStatus.FAILED
            backup_job.error_message = str(e)
            backup_job.completed_at = datetime.utcnow()
            
            self.backup_stats.total_backups += 1
            self.backup_stats.failed_backups += 1
            
            logger.error(f"Backup failed: {backup_job.id} - {e}")
        
        finally:
            self.current_backups -= 1
    
    def _execute_full_backup(self, backup_job: BackupJob):
        """Execute full backup"""
        for i, node in enumerate(backup_job.nodes):
            try:
                backup_job.progress = (i / len(backup_job.nodes)) * 100
                
                # Connect to node
                client = self._get_node_client(node)
                if not client:
                    raise Exception(f"Cannot connect to node: {node}")
                
                # Trigger BGSAVE
                result = client.bgsave()
                if result != 'Background saving started':
                    raise Exception(f"BGSAVE failed: {result}")
                
                # Wait for backup to complete
                self._wait_for_backup_complete(client, backup_job)
                
                # Copy RDB file
                self._copy_rdb_file(client, backup_job, node)
                
            except Exception as e:
                logger.error(f"Full backup failed for node {node}: {e}")
                raise
    
    def _execute_incremental_backup(self, backup_job: BackupJob):
        """Execute incremental backup"""
        # For Redis, incremental backup is not natively supported
        # We'll implement it as a full backup with timestamp comparison
        logger.info("Incremental backup not natively supported, executing as full backup")
        self._execute_full_backup(backup_job)
    
    def _execute_snapshot_backup(self, backup_job: BackupJob):
        """Execute snapshot backup"""
        for i, node in enumerate(backup_job.nodes):
            try:
                backup_job.progress = (i / len(backup_job.nodes)) * 100
                
                # Connect to node
                client = self._get_node_client(node)
                if not client:
                    raise Exception(f"Cannot connect to node: {node}")
                
                # Create snapshot
                result = client.save()  # Synchronous save for snapshot
                if not result:
                    raise Exception("SAVE command failed")
                
                # Copy RDB file
                self._copy_rdb_file(client, backup_job, node)
                
            except Exception as e:
                logger.error(f"Snapshot backup failed for node {node}: {e}")
                raise
    
    def _execute_rdb_backup(self, backup_job: BackupJob):
        """Execute RDB backup"""
        # RDB backup is the same as full backup
        self._execute_full_backup(backup_job)
    
    def _execute_aof_backup(self, backup_job: BackupJob):
        """Execute AOF backup"""
        for i, node in enumerate(backup_job.nodes):
            try:
                backup_job.progress = (i / len(backup_job.nodes)) * 100
                
                # Connect to node
                client = self._get_node_client(node)
                if not client:
                    raise Exception(f"Cannot connect to node: {node}")
                
                # Get AOF file path
                config = client.config_get('appendfilename')
                aof_filename = config.get('appendfilename', 'appendonly.aof')
                
                # Get data directory
                config = client.config_get('dir')
                data_dir = config.get('dir', '/var/lib/redis')
                
                aof_path = os.path.join(data_dir, aof_filename)
                
                # Copy AOF file
                node_suffix = node.replace(':', '_')
                aof_backup_path = backup_job.file_path.replace('.rdb', f'_{node_suffix}.aof')
                
                shutil.copy2(aof_path, aof_backup_path)
                
                # Update file size
                backup_job.file_size += os.path.getsize(aof_backup_path)
                
            except Exception as e:
                logger.error(f"AOF backup failed for node {node}: {e}")
                raise
    
    def _get_node_client(self, node: str):
        """Get Redis client for a specific node"""
        try:
            host, port = node.split(':')
            
            if self.redis_cluster:
                # Get node client from cluster
                for cluster_node in self.redis_cluster.get_nodes():
                    if cluster_node.host == host and cluster_node.port == int(port):
                        return self.redis_cluster.get_redis_connection(cluster_node)
            
            # Create direct connection
            return redis.Redis(
                host=host,
                port=int(port),
                decode_responses=True,
                socket_timeout=30
            )
            
        except Exception as e:
            logger.error(f"Error creating client for node {node}: {e}")
            return None
    
    def _wait_for_backup_complete(self, client: redis.Redis, backup_job: BackupJob, timeout: int = 300):
        """Wait for backup to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                info = client.info('persistence')
                if info.get('bgsave_in_progress', 0) == 0:
                    return
                
                # Update progress
                elapsed = time.time() - start_time
                progress = min((elapsed / timeout) * 90, 90)  # Cap at 90% until completion
                backup_job.progress = progress
                
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error checking backup status: {e}")
                time.sleep(5)
        
        raise Exception("Backup timeout")
    
    def _copy_rdb_file(self, client: redis.Redis, backup_job: BackupJob, node: str):
        """Copy RDB file from node"""
        try:
            # Get RDB file path
            config = client.config_get('dbfilename')
            rdb_filename = config.get('dbfilename', 'dump.rdb')
            
            # Get data directory
            config = client.config_get('dir')
            data_dir = config.get('dir', '/var/lib/redis')
            
            rdb_path = os.path.join(data_dir, rdb_filename)
            
            # Create node-specific backup file
            node_suffix = node.replace(':', '_')
            node_backup_path = backup_job.file_path.replace('.rdb', f'_{node_suffix}.rdb')
            
            # Copy RDB file
            shutil.copy2(rdb_path, node_backup_path)
            
            # Update file size
            backup_job.file_size += os.path.getsize(node_backup_path)
            
        except Exception as e:
            logger.error(f"Error copying RDB file from {node}: {e}")
            raise
    
    def _compress_backup(self, backup_job: BackupJob):
        """Compress backup file"""
        try:
            original_path = backup_job.file_path
            compressed_path = original_path + '.gz'
            
            # Compress file
            with open(original_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Update backup job
            backup_job.file_path = compressed_path
            backup_job.file_size = os.path.getsize(compressed_path)
            
            # Remove original file
            os.remove(original_path)
            
        except Exception as e:
            logger.error(f"Error compressing backup {backup_job.id}: {e}")
            raise
    
    def _verify_backup(self, backup_job: BackupJob):
        """Verify backup integrity"""
        try:
            if backup_job.file_path.endswith('.gz'):
                # Verify compressed file
                with gzip.open(backup_job.file_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB to verify
            else:
                # Verify regular file
                with open(backup_job.file_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB to verify
            
            logger.info(f"Backup verification passed: {backup_job.id}")
            
        except Exception as e:
            logger.error(f"Backup verification failed: {backup_job.id} - {e}")
            raise
    
    def _upload_remote_backup(self, backup_job: BackupJob):
        """Upload backup to remote storage"""
        try:
            if not self.config.remote_backup_url:
                return
            
            # This is a placeholder for remote upload
            # In production, you would implement S3, Azure Blob, etc.
            logger.info(f"Remote upload not implemented: {backup_job.file_path}")
            
        except Exception as e:
            logger.error(f"Error uploading backup {backup_job.id}: {e}")
            # Don't raise error for upload failure
    
    def restore_backup(self, backup_id: str, target_nodes: List[str] = None) -> bool:
        """Restore from backup"""
        try:
            if backup_id not in self.backup_jobs:
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            backup_job = self.backup_jobs[backup_id]
            
            if backup_job.status != BackupStatus.COMPLETED:
                logger.error(f"Backup not completed: {backup_id}")
                return False
            
            if not os.path.exists(backup_job.file_path):
                logger.error(f"Backup file not found: {backup_job.file_path}")
                return False
            
            # Determine target nodes
            if not target_nodes:
                target_nodes = self._get_all_nodes()
            
            # Restore to each node
            for node in target_nodes:
                self._restore_to_node(backup_job, node)
            
            logger.info(f"Backup restored successfully: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {backup_id} - {e}")
            return False
    
    def _restore_to_node(self, backup_job: BackupJob, node: str):
        """Restore backup to specific node"""
        try:
            # Connect to node
            client = self._get_node_client(node)
            if not client:
                raise Exception(f"Cannot connect to node: {node}")
            
            # Get data directory
            config = client.config_get('dir')
            data_dir = config.get('dir', '/var/lib/redis')
            
            # Determine backup file for this node
            node_suffix = node.replace(':', '_')
            if backup_job.backup_type == BackupType.AOF:
                backup_file = backup_job.file_path.replace('.rdb', f'_{node_suffix}.aof')
            else:
                backup_file = backup_job.file_path.replace('.rdb', f'_{node_suffix}.rdb')
            
            # Decompress if needed
            if backup_file.endswith('.gz'):
                decompressed_file = backup_file[:-3]
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(decompressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_file = decompressed_file
            
            # Copy backup file to data directory
            shutil.copy2(backup_file, data_dir)
            
            # Restart Redis to load backup
            self._restart_redis_service(node)
            
            logger.info(f"Backup restored to node: {node}")
            
        except Exception as e:
            logger.error(f"Error restoring to node {node}: {e}")
            raise
    
    def _restart_redis_service(self, node: str):
        """Restart Redis service on node"""
        try:
            # This is a placeholder for service restart
            # In production, you would use systemd, docker, etc.
            logger.info(f"Redis restart not implemented for node: {node}")
            
        except Exception as e:
            logger.error(f"Error restarting Redis on {node}: {e}")
    
    def get_backup_jobs(self) -> List[Dict[str, Any]]:
        """Get all backup jobs"""
        return [
            {
                'id': job.id,
                'backup_type': job.backup_type.value,
                'nodes': job.nodes,
                'status': job.status.value,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'file_path': job.file_path,
                'file_size': job.file_size,
                'error_message': job.error_message,
                'progress': job.progress
            }
            for job in self.backup_jobs.values()
        ]
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup statistics"""
        return {
            'total_backups': self.backup_stats.total_backups,
            'successful_backups': self.backup_stats.successful_backups,
            'failed_backups': self.backup_stats.failed_backups,
            'total_size': self.backup_stats.total_size,
            'avg_backup_time': self.backup_stats.avg_backup_time,
            'last_backup_time': (
                self.backup_stats.last_backup_time.isoformat()
                if self.backup_stats.last_backup_time else None
            ),
            'next_backup_time': (
                (self.backup_stats.last_backup_time + timedelta(seconds=self.config.backup_interval)).isoformat()
                if self.backup_stats.last_backup_time else None
            ),
            'current_backups': self.current_backups,
            'backup_enabled': self.backup_enabled
        }
    
    def cleanup_old_backups(self):
        """Clean up old backup files"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.config.retention_days)
            cleaned_count = 0
            
            # Scan backup directory
            for filename in os.listdir(self.config.backup_dir):
                file_path = os.path.join(self.config.backup_dir, filename)
                
                if os.path.isfile(file_path):
                    # Check file age
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.info(f"Removed old backup: {filename}")
            
            logger.info(f"Cleaned up {cleaned_count} old backup files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return 0
    
    def cancel_backup(self, backup_id: str) -> bool:
        """Cancel a backup job"""
        try:
            if backup_id not in self.backup_jobs:
                return False
            
            backup_job = self.backup_jobs[backup_id]
            
            if backup_job.status in [BackupStatus.COMPLETED, BackupStatus.FAILED, BackupStatus.CANCELLED]:
                return False
            
            backup_job.status = BackupStatus.CANCELLED
            backup_job.completed_at = datetime.utcnow()
            
            logger.info(f"Backup cancelled: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling backup {backup_id}: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get backup configuration"""
        return {
            'backup_dir': self.config.backup_dir,
            'backup_interval': self.config.backup_interval,
            'retention_days': self.config.retention_days,
            'compression_enabled': self.config.compression_enabled,
            'encryption_enabled': self.config.encryption_enabled,
            'remote_backup_enabled': self.config.remote_backup_enabled,
            'remote_backup_url': self.config.remote_backup_url,
            'max_concurrent_backups': self.config.max_concurrent_backups,
            'backup_timeout': self.config.backup_timeout,
            'verify_backup': self.config.verify_backup,
            'backup_on_shutdown': self.config.backup_on_shutdown
        }
    
    def update_config(self, **kwargs):
        """Update backup configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated backup config: {key} = {value}")
    
    def shutdown(self):
        """Shutdown backup manager"""
        try:
            # Stop backup scheduler
            self.backup_enabled = False
            
            # Create backup on shutdown if enabled
            if self.config.backup_on_shutdown:
                try:
                    backup_id = f"shutdown_{int(time.time())}"
                    self.create_backup(backup_id, BackupType.SNAPSHOT)
                except Exception as e:
                    logger.error(f"Shutdown backup failed: {e}")
            
            logger.info("Cache backup manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during backup manager shutdown: {e}")
