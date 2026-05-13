"""
Storage Service

This module provides a unified interface for file storage across multiple providers
including local storage, AWS S3, Google Cloud Storage, and other cloud providers.
"""

import os
import uuid
import mimetypes
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import current_app
import logging

# Conditional imports for cloud storage
try:
    import boto3
    from botocore.exceptions import NoCredentialsError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from google.cloud import storage as gcs
    from google.auth.exceptions import DefaultCredentialsError
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

logger = logging.getLogger(__name__)

class StorageService:
    """Unified storage service for multiple storage providers"""
    
    def __init__(self, provider='local'):
        self.provider = provider
        self._init_provider()
    
    def _init_provider(self):
        """Initialize the storage provider"""
        if self.provider == 's3':
            self._init_s3()
        elif self.provider == 'gcs':
            self._init_gcs()
        elif self.provider == 'local':
            self._init_local()
        else:
            raise ValueError(f"Unsupported storage provider: {self.provider}")
    
    def _init_s3(self):
        """Initialize AWS S3 storage"""
        if not BOTO3_AVAILABLE:
            raise ValueError("boto3 not installed. Install with: pip install boto3")
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
                region_name=current_app.config.get('AWS_REGION', 'us-east-1')
            )
            self.bucket_name = current_app.config.get('AWS_S3_BUCKET')
            self.region = current_app.config.get('AWS_REGION', 'us-east-1')
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 storage initialized for bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except ClientError as e:
            logger.error(f"S3 initialization error: {e}")
            raise
    
    def _init_gcs(self):
        """Initialize Google Cloud Storage"""
        if not GCS_AVAILABLE:
            raise ValueError("google-cloud-storage not installed. Install with: pip install google-cloud-storage")
        
        try:
            self.gcs_client = gcs.Client()
            self.bucket_name = current_app.config.get('GCS_BUCKET')
            self.bucket = self.gcs_client.bucket(self.bucket_name)
            
            # Test connection
            self.bucket.reload()
            logger.info(f"GCS storage initialized for bucket: {self.bucket_name}")
            
        except DefaultCredentialsError:
            logger.error("Google Cloud credentials not found")
            raise
        except Exception as e:
            logger.error(f"GCS initialization error: {e}")
            raise
    
    def _init_local(self):
        """Initialize local storage"""
        self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(self.upload_folder, exist_ok=True)
        logger.info(f"Local storage initialized at: {self.upload_folder}")
    
    def upload_file(self, file, filename=None, folder=None, is_public=False):
        """Upload a file to the storage provider"""
        if not file:
            raise ValueError("No file provided")
        
        # Generate secure filename
        if filename is None:
            filename = secure_filename(file.filename)
        
        # Generate unique filename
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Add folder if specified
        if folder:
            file_path = f"{folder}/{unique_filename}"
        else:
            file_path = unique_filename
        
        # Determine file type
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        file_type = self._get_file_type(mime_type)
        
        try:
            if self.provider == 's3':
                return self._upload_s3(file, file_path, mime_type, is_public)
            elif self.provider == 'gcs':
                return self._upload_gcs(file, file_path, mime_type, is_public)
            elif self.provider == 'local':
                return self._upload_local(file, file_path, mime_type, is_public)
        except Exception as e:
            logger.error(f"Upload error: {e}")
            raise
    
    def _upload_s3(self, file, file_path, mime_type, is_public):
        """Upload file to S3"""
        try:
            # Reset file pointer
            file.seek(0)
            
            # Upload to S3
            extra_args = {
                'ContentType': mime_type,
                'Metadata': {
                    'original_filename': file.filename,
                    'upload_date': datetime.utcnow().isoformat()
                }
            }
            
            if is_public:
                extra_args['ACL'] = 'public-read'
            
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                file_path,
                ExtraArgs=extra_args
            )
            
            # Generate URL
            if is_public:
                url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_path}"
            else:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': file_path},
                    ExpiresIn=3600
                )
            
            return {
                'file_path': file_path,
                'url': url,
                'provider': 's3',
                'bucket': self.bucket_name,
                'region': self.region
            }
            
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            raise
    
    def _upload_gcs(self, file, file_path, mime_type, is_public):
        """Upload file to Google Cloud Storage"""
        try:
            # Reset file pointer
            file.seek(0)
            
            # Create blob
            blob = self.bucket.blob(file_path)
            blob.content_type = mime_type
            
            # Set metadata
            blob.metadata = {
                'original_filename': file.filename,
                'upload_date': datetime.utcnow().isoformat()
            }
            
            # Upload file
            blob.upload_from_file(file)
            
            # Set permissions
            if is_public:
                blob.make_public()
                url = blob.public_url
            else:
                url = blob.generate_signed_url(
                    version='v4',
                    expiration=timedelta(hours=1),
                    method='GET'
                )
            
            return {
                'file_path': file_path,
                'url': url,
                'provider': 'gcs',
                'bucket': self.bucket_name
            }
            
        except Exception as e:
            logger.error(f"GCS upload error: {e}")
            raise
    
    def _upload_local(self, file, file_path, mime_type, is_public):
        """Upload file to local storage"""
        try:
            # Reset file pointer
            file.seek(0)
            
            # Create full path
            full_path = os.path.join(self.upload_folder, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Save file
            file.save(full_path)
            
            # Generate URL (relative path)
            url = f"/{self.upload_folder}/{file_path}"
            
            return {
                'file_path': file_path,
                'url': url,
                'provider': 'local',
                'local_path': full_path
            }
            
        except Exception as e:
            logger.error(f"Local upload error: {e}")
            raise
    
    def get_file_url(self, file_path, expires_in=3600):
        """Get file URL for download/viewing"""
        try:
            if self.provider == 's3':
                return self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': file_path},
                    ExpiresIn=expires_in
                )
            elif self.provider == 'gcs':
                blob = self.bucket.blob(file_path)
                return blob.generate_signed_url(
                    version='v4',
                    expiration=timedelta(seconds=expires_in),
                    method='GET'
                )
            elif self.provider == 'local':
                full_path = os.path.join(self.upload_folder, file_path)
                if os.path.exists(full_path):
                    return f"/{self.upload_folder}/{file_path}"
                else:
                    raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error generating file URL: {e}")
            raise
    
    def delete_file(self, file_path):
        """Delete file from storage"""
        try:
            if self.provider == 's3':
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
            elif self.provider == 'gcs':
                blob = self.bucket.blob(file_path)
                blob.delete()
            elif self.provider == 'local':
                full_path = os.path.join(self.upload_folder, file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                else:
                    raise FileNotFoundError(f"File not found: {file_path}")
            
            logger.info(f"File deleted: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            raise
    
    def file_exists(self, file_path):
        """Check if file exists in storage"""
        try:
            if self.provider == 's3':
                self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
                return True
            elif self.provider == 'gcs':
                blob = self.bucket.blob(file_path)
                return blob.exists()
            elif self.provider == 'local':
                full_path = os.path.join(self.upload_folder, file_path)
                return os.path.exists(full_path)
        except:
            return False
    
    def get_file_size(self, file_path):
        """Get file size in bytes"""
        try:
            if self.provider == 's3':
                response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
                return response['ContentLength']
            elif self.provider == 'gcs':
                blob = self.bucket.blob(file_path)
                blob.reload()
                return blob.size
            elif self.provider == 'local':
                full_path = os.path.join(self.upload_folder, file_path)
                return os.path.getsize(full_path)
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return 0
    
    def _get_file_type(self, mime_type):
        """Determine file type from MIME type"""
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                          'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                          'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']:
            return 'document'
        elif mime_type.startswith('text/'):
            return 'document'
        else:
            return 'other'
    
    def get_provider_info(self):
        """Get storage provider information"""
        return {
            'provider': self.provider,
            'bucket': getattr(self, 'bucket_name', None),
            'region': getattr(self, 'region', None),
            'upload_folder': getattr(self, 'upload_folder', None)
        }

# Factory function for creating storage service
def create_storage_service(provider=None):
    """Create storage service instance"""
    if provider is None:
        provider = current_app.config.get('STORAGE_PROVIDER', 'local')
    
    return StorageService(provider)
