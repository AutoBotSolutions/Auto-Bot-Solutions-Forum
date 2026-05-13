"""
Notification Export System

This module provides comprehensive notification export capabilities:
- Multiple export formats (CSV, JSON, XML, PDF)
- Scheduled exports
- Filtered exports
- Export templates
- Export analytics
- Data privacy compliance
"""

import time
import json
import csv
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import redis
import sqlite3
from sqlalchemy import text, and_, or_
from io import StringIO, BytesIO
import zipfile
import xml.etree.ElementTree as ET
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from app.config.notification_config import get_notification_config
from app.models import Notification, AdminNotification, User

logger = logging.getLogger(__name__)

@dataclass
class ExportConfig:
    """Export configuration"""
    format: str  # csv, json, xml, pdf
    filters: Dict
    fields: List[str]
    date_range: Dict
    include_metadata: bool = True
    compress: bool = False
    encryption: bool = False

@dataclass
class ExportJob:
    """Export job tracking"""
    job_id: str
    user_id: int
    config: ExportConfig
    status: str  # pending, running, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: int = 0
    record_count: int = 0
    error_message: Optional[str] = None

class NotificationExportSystem:
    """Comprehensive notification export system"""
    
    def __init__(self):
        self.config = get_notification_config()
        self.redis_client = None
        self.db_connection = None
        self.export_queue = deque()
        self.running_jobs = {}
        self.export_history = deque(maxlen=1000)
        
        # Export templates
        self.export_templates = self._initialize_templates()
        
        # Supported formats
        self.supported_formats = ['csv', 'json', 'xml', 'pdf']
        
        # Default fields
        self.default_fields = [
            'id', 'type', 'content', 'link', 'is_read', 'created_at',
            'priority', 'category', 'user_id'
        ]
        
        self._setup_connections()
        self._create_export_tables()
        self._start_export_processor()
    
    def _setup_connections(self):
        """Setup database and Redis connections"""
        try:
            # Redis connection
            self.redis_client = redis.from_url(
                self.config.redis_url,
                db=self.config.redis_notification_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            
            # SQLite export database
            self.db_connection = sqlite3.connect('notification_exports.db', check_same_thread=False)
            self.db_connection.row_factory = sqlite3.Row
            
            logger.info("Export system connections established")
            
        except Exception as e:
            logger.error(f"Failed to setup export connections: {str(e)}")
    
    def _create_export_tables(self):
        """Create export tracking tables"""
        try:
            cursor = self.db_connection.cursor()
            
            # Export jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS export_jobs (
                    job_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    format TEXT NOT NULL,
                    filters TEXT,
                    fields TEXT,
                    date_range TEXT,
                    status TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    started_at DATETIME,
                    completed_at DATETIME,
                    file_path TEXT,
                    file_size INTEGER DEFAULT 0,
                    record_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    include_metadata BOOLEAN DEFAULT 1,
                    compress BOOLEAN DEFAULT 0,
                    encryption BOOLEAN DEFAULT 0
                )
            ''')
            
            # Export statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS export_statistics (
                    date DATE PRIMARY KEY,
                    total_exports INTEGER DEFAULT 0,
                    successful_exports INTEGER DEFAULT 0,
                    failed_exports INTEGER DEFAULT 0,
                    total_records_exported INTEGER DEFAULT 0,
                    average_file_size REAL DEFAULT 0.0,
                    most_popular_format TEXT,
                    average_processing_time REAL DEFAULT 0.0
                )
            ''')
            
            # Export templates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS export_templates (
                    template_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    format TEXT NOT NULL,
                    fields TEXT NOT NULL,
                    filters TEXT,
                    created_by INTEGER,
                    created_at DATETIME NOT NULL,
                    is_public BOOLEAN DEFAULT 0,
                    usage_count INTEGER DEFAULT 0
                )
            ''')
            
            self.db_connection.commit()
            logger.info("Export tables created/verified")
            
        except Exception as e:
            logger.error(f"Error creating export tables: {str(e)}")
    
    def _initialize_templates(self) -> Dict:
        """Initialize default export templates"""
        templates = {
            'basic_notifications': {
                'name': 'Basic Notifications',
                'description': 'All notification data with basic fields',
                'format': 'csv',
                'fields': ['id', 'type', 'content', 'link', 'is_read', 'created_at'],
                'filters': {},
                'include_metadata': False,
                'compress': False
            },
            'complete_notifications': {
                'name': 'Complete Notifications',
                'description': 'All notification data with all available fields',
                'format': 'json',
                'fields': self.default_fields,
                'filters': {},
                'include_metadata': True,
                'compress': True
            },
            'unread_notifications': {
                'name': 'Unread Notifications',
                'description': 'Only unread notifications',
                'format': 'csv',
                'fields': ['id', 'type', 'content', 'link', 'created_at'],
                'filters': {'is_read': False},
                'include_metadata': False,
                'compress': False
            },
            'recent_notifications': {
                'name': 'Recent Notifications',
                'description': 'Notifications from last 30 days',
                'format': 'json',
                'fields': self.default_fields,
                'filters': {'date_range': 'last_30_days'},
                'include_metadata': True,
                'compress': True
            },
            'admin_notifications': {
                'name': 'Admin Notifications',
                'description': 'Administrative notifications only',
                'format': 'csv',
                'fields': ['id', 'title', 'message', 'notification_type', 'priority', 'created_at'],
                'filters': {'type': 'admin'},
                'include_metadata': False,
                'compress': False
            }
        }
        
        # Store templates in database
        cursor = self.db_connection.cursor()
        for template_id, template_data in templates.items():
            cursor.execute('''
                INSERT OR IGNORE INTO export_templates
                (template_id, name, description, format, fields, filters,
                 created_by, created_at, is_public)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                template_id,
                template_data['name'],
                template_data['description'],
                template_data['format'],
                json.dumps(template_data['fields']),
                json.dumps(template_data['filters']),
                0,  # System created
                datetime.utcnow(),
                True
            ))
        
        self.db_connection.commit()
        return templates
    
    def _start_export_processor(self):
        """Start export processor thread"""
        self.export_thread = threading.Thread(
            target=self._export_processor_loop,
            daemon=True
        )
        self.export_thread.start()
        logger.info("Export processor started")
    
    def _export_processor_loop(self):
        """Main export processing loop"""
        while True:
            try:
                if self.export_queue:
                    job = self.export_queue.popleft()
                    self._process_export_job(job)
                else:
                    time.sleep(5)  # Wait for new jobs
                    
            except Exception as e:
                logger.error(f"Export processor error: {str(e)}")
                time.sleep(10)
    
    def create_export_job(self, user_id: int, export_config: ExportConfig) -> str:
        """Create a new export job"""
        try:
            # Generate job ID
            job_id = f"export_{user_id}_{int(time.time())}"
            
            # Create export job
            job = ExportJob(
                job_id=job_id,
                user_id=user_id,
                config=export_config,
                status='pending',
                created_at=datetime.utcnow()
            )
            
            # Store job in database
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO export_jobs
                (job_id, user_id, format, filters, fields, date_range, status,
                 created_at, include_metadata, compress, encryption)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                user_id,
                export_config.format,
                json.dumps(export_config.filters),
                json.dumps(export_config.fields),
                json.dumps(export_config.date_range),
                job.status,
                job.created_at,
                export_config.include_metadata,
                export_config.compress,
                export_config.encryption
            ))
            
            self.db_connection.commit()
            
            # Add to queue
            self.export_queue.append(job)
            self.running_jobs[job_id] = job
            
            logger.info(f"Created export job: {job_id}")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating export job: {str(e)}")
            raise
    
    def _process_export_job(self, job: ExportJob):
        """Process an export job"""
        try:
            # Update job status
            job.status = 'running'
            job.started_at = datetime.utcnow()
            self._update_job_status(job)
            
            # Query notifications based on filters
            notifications = self._query_notifications(job.config)
            job.record_count = len(notifications)
            
            if not notifications:
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                self._update_job_status(job)
                return
            
            # Export data
            file_path, file_size = self._export_data(job, notifications)
            job.file_path = file_path
            job.file_size = file_size
            
            # Update job status
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            self._update_job_status(job)
            
            # Update statistics
            self._update_export_statistics(job)
            
            logger.info(f"Completed export job: {job.job_id}")
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self._update_job_status(job)
            
            logger.error(f"Failed export job {job.job_id}: {str(e)}")
        
        finally:
            # Remove from running jobs
            self.running_jobs.pop(job.job_id, None)
            
            # Add to history
            self.export_history.append(job)
    
    def _query_notifications(self, config: ExportConfig) -> List[Dict]:
        """Query notifications based on export configuration"""
        try:
            # Build base query
            query = Notification.query
            
            # Apply filters
            filters = config.filters
            
            # Date range filter
            if 'date_range' in filters:
                date_range = filters['date_range']
                now = datetime.utcnow()
                
                if date_range == 'last_24_hours':
                    start_date = now - timedelta(hours=24)
                    query = query.filter(Notification.created_at >= start_date)
                elif date_range == 'last_7_days':
                    start_date = now - timedelta(days=7)
                    query = query.filter(Notification.created_at >= start_date)
                elif date_range == 'last_30_days':
                    start_date = now - timedelta(days=30)
                    query = query.filter(Notification.created_at >= start_date)
                elif date_range == 'custom':
                    if 'start_date' in filters:
                        start_date = datetime.fromisoformat(filters['start_date'].replace('Z', '+00:00'))
                        query = query.filter(Notification.created_at >= start_date)
                    if 'end_date' in filters:
                        end_date = datetime.fromisoformat(filters['end_date'].replace('Z', '+00:00'))
                        query = query.filter(Notification.created_at <= end_date)
            
            # Type filter
            if 'type' in filters:
                query = query.filter(Notification.type == filters['type'])
            
            # Read status filter
            if 'is_read' in filters:
                query = query.filter(Notification.is_read == filters['is_read'])
            
            # Priority filter
            if 'priority' in filters:
                query = query.filter(getattr(Notification, 'priority', 'normal') == filters['priority'])
            
            # User filter
            if 'user_id' in filters:
                query = query.filter(Notification.user_id == filters['user_id'])
            
            # Category filter
            if 'category' in filters:
                query = query.filter(Notification.category == filters['category'])
            
            # Execute query
            notifications = query.all()
            
            # Convert to dictionaries
            result = []
            for notification in notifications:
                data = {
                    'id': notification.id,
                    'user_id': notification.user_id,
                    'type': notification.type,
                    'content': notification.content,
                    'link': notification.link,
                    'is_read': notification.is_read,
                    'created_at': notification.created_at.isoformat(),
                    'priority': getattr(notification, 'priority', 'normal'),
                    'category': getattr(notification, 'category', 'general')
                }
                
                # Add metadata if requested
                if config.include_metadata:
                    data['metadata'] = {
                        'exported_at': datetime.utcnow().isoformat(),
                        'export_job_id': getattr(self, 'current_job_id', ''),
                        'export_format': config.format
                    }
                
                # Filter fields
                if config.fields:
                    filtered_data = {}
                    for field in config.fields:
                        if field in data:
                            filtered_data[field] = data[field]
                    data = filtered_data
                
                result.append(data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error querying notifications: {str(e)}")
            raise
    
    def _export_data(self, job: ExportJob, notifications: List[Dict]) -> Tuple[str, int]:
        """Export data to specified format"""
        try:
            # Set current job ID for metadata
            self.current_job_id = job.job_id
            
            # Generate file path
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"export_{job.user_id}_{timestamp}.{job.config.format}"
            file_path = f"exports/{filename}"
            
            # Create export directory if it doesn't exist
            import os
            os.makedirs('exports', exist_ok=True)
            
            # Export based on format
            if job.config.format == 'csv':
                file_path, file_size = self._export_csv(file_path, notifications, job)
            elif job.config.format == 'json':
                file_path, file_size = self._export_json(file_path, notifications, job)
            elif job.config.format == 'xml':
                file_path, file_size = self._export_xml(file_path, notifications, job)
            elif job.config.format == 'pdf':
                file_path, file_size = self._export_pdf(file_path, notifications, job)
            else:
                raise ValueError(f"Unsupported export format: {job.config.format}")
            
            # Compress if requested
            if job.config.compress:
                file_path, file_size = self._compress_file(file_path)
            
            return file_path, file_size
            
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            raise
        finally:
            self.current_job_id = None
    
    def _export_csv(self, file_path: str, notifications: List[Dict], job: ExportJob) -> Tuple[str, int]:
        """Export to CSV format"""
        try:
            output = StringIO()
            
            if notifications:
                fieldnames = notifications[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(notifications)
            
            # Write to file
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                f.write(output.getvalue())
            
            file_size = os.path.getsize(file_path)
            return file_path, file_size
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise
    
    def _export_json(self, file_path: str, notifications: List[Dict], job: ExportJob) -> Tuple[str, int]:
        """Export to JSON format"""
        try:
            export_data = {
                'metadata': {
                    'export_id': job.job_id,
                    'exported_at': datetime.utcnow().isoformat(),
                    'record_count': len(notifications),
                    'format': 'json',
                    'filters': job.config.filters,
                    'fields': job.config.fields
                },
                'data': notifications
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(file_path)
            return file_path, file_size
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            raise
    
    def _export_xml(self, file_path: str, notifications: List[Dict], job: ExportJob) -> Tuple[str, int]:
        """Export to XML format"""
        try:
            root = ET.Element('notifications')
            
            # Add metadata
            metadata = ET.SubElement(root, 'metadata')
            ET.SubElement(metadata, 'export_id').text = job.job_id
            ET.SubElement(metadata, 'exported_at').text = datetime.utcnow().isoformat()
            ET.SubElement(metadata, 'record_count').text = str(len(notifications))
            ET.SubElement(metadata, 'format').text = 'xml'
            
            # Add data
            data = ET.SubElement(root, 'data')
            for notification in notifications:
                notification_elem = ET.SubElement(data, 'notification')
                for key, value in notification.items():
                    elem = ET.SubElement(notification_elem, key)
                    elem.text = str(value)
            
            # Write to file
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            
            file_size = os.path.getsize(file_path)
            return file_path, file_size
            
        except Exception as e:
            logger.error(f"Error exporting to XML: {str(e)}")
            raise
    
    def _export_pdf(self, file_path: str, notifications: List[Dict], job: ExportJob) -> Tuple[str, int]:
        """Export to PDF format"""
        try:
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Add title
            title = Paragraph("Notification Export Report", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Add metadata
            metadata_data = [
                ['Export ID:', job.job_id],
                ['Exported At:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')],
                ['Record Count:', str(len(notifications))],
                ['Format:', 'PDF']
            ]
            
            metadata_table = Table(metadata_data, colWidths=[100, 300])
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(metadata_table)
            story.append(Spacer(1, 12))
            
            # Add notifications data
            if notifications:
                fieldnames = list(notifications[0].keys())
                data = [fieldnames]  # Header row
                
                for notification in notifications[:100]:  # Limit to 100 records for PDF
                    row = [str(notification.get(field, '')) for field in fieldnames]
                    data.append(row)
                
                table = Table(data, colWidths=[50] * len(fieldnames))
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(table)
                
                if len(notifications) > 100:
                    story.append(Spacer(1, 12))
                    note = Paragraph(f"Note: Only first 100 records shown. Total records: {len(notifications)}", styles['Normal'])
                    story.append(note)
            
            # Build PDF
            doc.build(story)
            
            file_size = os.path.getsize(file_path)
            return file_path, file_size
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise
    
    def _compress_file(self, file_path: str) -> Tuple[str, int]:
        """Compress export file"""
        try:
            zip_path = file_path + '.zip'
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_path, os.path.basename(file_path))
            
            # Remove original file
            os.remove(file_path)
            
            file_size = os.path.getsize(zip_path)
            return zip_path, file_size
            
        except Exception as e:
            logger.error(f"Error compressing file: {str(e)}")
            raise
    
    def _update_job_status(self, job: ExportJob):
        """Update job status in database"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                UPDATE export_jobs
                SET status = ?, started_at = ?, completed_at = ?, file_path = ?,
                    file_size = ?, record_count = ?, error_message = ?
                WHERE job_id = ?
            ''', (
                job.status,
                job.started_at,
                job.completed_at,
                job.file_path,
                job.file_size,
                job.record_count,
                job.error_message,
                job.job_id
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")
    
    def _update_export_statistics(self, job: ExportJob):
        """Update export statistics"""
        try:
            cursor = self.db_connection.cursor()
            
            today = datetime.utcnow().date()
            
            # Update or insert daily statistics
            cursor.execute('''
                INSERT OR REPLACE INTO export_statistics
                (date, total_exports, successful_exports, failed_exports,
                 total_records_exported, average_file_size, most_popular_format)
                VALUES (
                    COALESCE((SELECT date FROM export_statistics WHERE date = ?), ?),
                    COALESCE((SELECT total_exports FROM export_statistics WHERE date = ?), 0) + 1,
                    COALESCE((SELECT successful_exports FROM export_statistics WHERE date = ?), 0) + ?,
                    COALESCE((SELECT failed_exports FROM export_statistics WHERE date = ?), 0) + ?,
                    COALESCE((SELECT total_records_exported FROM export_statistics WHERE date = ?), 0) + ?,
                    COALESCE((SELECT average_file_size FROM export_statistics WHERE date = ?), 0),
                    ?
                )
            ''', (
                today, today,
                today, 1 if job.status == 'completed' else 0,
                today, 1 if job.status == 'failed' else 0,
                today, job.record_count,
                today, job.file_size,
                job.config.format
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error updating export statistics: {str(e)}")
    
    def get_export_status(self, job_id: str) -> Dict:
        """Get export job status"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT * FROM export_jobs WHERE job_id = ?
            ''', (job_id,))
            
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            else:
                return {'error': 'Job not found'}
                
        except Exception as e:
            logger.error(f"Error getting export status: {str(e)}")
            return {'error': str(e)}
    
    def get_user_exports(self, user_id: int) -> List[Dict]:
        """Get user's export history"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT * FROM export_jobs 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 50
            ''', (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting user exports: {str(e)}")
            return []
    
    def get_export_templates(self, user_id: Optional[int] = None) -> List[Dict]:
        """Get export templates"""
        try:
            cursor = self.db_connection.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT * FROM export_templates 
                    WHERE is_public = 1 OR created_by = ?
                    ORDER BY name
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT * FROM export_templates 
                    WHERE is_public = 1
                    ORDER BY name
                ''')
            
            templates = []
            for row in cursor.fetchall():
                template = dict(row)
                template['fields'] = json.loads(template['fields'])
                template['filters'] = json.loads(template['filters'])
                templates.append(template)
            
            return templates
            
        except Exception as e:
            logger.error(f"Error getting export templates: {str(e)}")
            return []
    
    def create_export_template(self, user_id: int, template_data: Dict) -> str:
        """Create custom export template"""
        try:
            template_id = f"template_{user_id}_{int(time.time())}"
            
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO export_templates
                (template_id, name, description, format, fields, filters,
                 created_by, created_at, is_public)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                template_id,
                template_data['name'],
                template_data.get('description', ''),
                template_data['format'],
                json.dumps(template_data['fields']),
                json.dumps(template_data.get('filters', {})),
                user_id,
                datetime.utcnow(),
                template_data.get('is_public', False)
            ))
            
            self.db_connection.commit()
            
            logger.info(f"Created export template: {template_id}")
            return template_id
            
        except Exception as e:
            logger.error(f"Error creating export template: {str(e)}")
            raise
    
    def get_export_statistics(self, days: int = 30) -> Dict:
        """Get export statistics"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get daily statistics
            cursor.execute('''
                SELECT date, total_exports, successful_exports, failed_exports,
                       total_records_exported, average_file_size, most_popular_format
                FROM export_statistics
                WHERE date >= date('now', '-{} days')
                ORDER BY date DESC
            '''.format(days))
            
            daily_stats = [dict(row) for row in cursor.fetchall()]
            
            # Get overall statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_exports,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_exports,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_exports,
                    SUM(record_count) as total_records_exported,
                    AVG(file_size) as average_file_size
                FROM export_jobs
                WHERE created_at >= date('now', '-{} days')
            '''.format(days))
            
            overall_stats = dict(cursor.fetchone())
            
            # Get format distribution
            cursor.execute('''
                SELECT format, COUNT(*) as count
                FROM export_jobs
                WHERE created_at >= date('now', '-{} days')
                GROUP BY format
                ORDER BY count DESC
            '''.format(days))
            
            format_distribution = [dict(row) for row in cursor.fetchall()]
            
            return {
                'period_days': days,
                'daily_statistics': daily_stats,
                'overall_statistics': overall_stats,
                'format_distribution': format_distribution
            }
            
        except Exception as e:
            logger.error(f"Error getting export statistics: {str(e)}")
            return {}
    
    def download_export_file(self, job_id: str) -> Optional[str]:
        """Get export file path for download"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT file_path FROM export_jobs WHERE job_id = ? AND status = 'completed'
            ''', (job_id,))
            
            result = cursor.fetchone()
            
            if result and result['file_path'] and os.path.exists(result['file_path']):
                return result['file_path']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting export file: {str(e)}")
            return None
    
    def cleanup_old_exports(self, days: int = 30):
        """Clean up old export files and records"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get old jobs
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT job_id, file_path FROM export_jobs 
                WHERE created_at < ? AND status = 'completed'
            ''', (cutoff_date,))
            
            old_jobs = cursor.fetchall()
            
            # Delete files
            for job_id, file_path in old_jobs:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted old export file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting file {file_path}: {str(e)}")
            
            # Delete database records
            cursor.execute('''
                DELETE FROM export_jobs WHERE created_at < ?
            ''', (cutoff_date,))
            
            self.db_connection.commit()
            
            logger.info(f"Cleaned up {len(old_jobs)} old export jobs")
            
        except Exception as e:
            logger.error(f"Error cleaning up old exports: {str(e)}")

# Global export system instance
notification_export_system = NotificationExportSystem()
