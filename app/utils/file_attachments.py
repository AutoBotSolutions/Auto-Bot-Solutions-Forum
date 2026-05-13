"""
File Attachment Utilities

Provides comprehensive file attachment functionality including:
- File upload validation and security
- Image processing and thumbnail generation
- File type detection and categorization
- Attachment management and analytics
- File deduplication and storage optimization
"""

import os
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
from flask import current_app
from app import db
from app.models import MessageAttachment, User


class FileAttachmentManager:
    """Advanced file attachment manager with security and processing capabilities"""
    
    def __init__(self):
        self.allowed_extensions = self._get_allowed_extensions()
        self.max_file_size = self._get_max_file_size()
        self.upload_folder = self._get_upload_folder()
        self.thumbnail_size = (200, 200)
        self.preview_size = (800, 600)
        
        # Ensure upload directories exist
        self._ensure_directories()
    
    def _get_allowed_extensions(self) -> Dict[str, List[str]]:
        """Get allowed file extensions by category"""
        return {
            'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'],
            'document': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'xls', 'xlsx', 'ppt', 'pptx'],
            'video': ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'],
            'audio': ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma'],
            'archive': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2'],
            'other': []
        }
    
    def _get_max_file_size(self) -> Dict[str, int]:
        """Get maximum file sizes by category (in bytes)"""
        return {
            'image': 10 * 1024 * 1024,  # 10MB
            'document': 50 * 1024 * 1024,  # 50MB
            'video': 100 * 1024 * 1024,  # 100MB
            'audio': 20 * 1024 * 1024,  # 20MB
            'archive': 100 * 1024 * 1024,  # 100MB
            'other': 10 * 1024 * 1024   # 10MB
        }
    
    def _get_upload_folder(self) -> str:
        """Get upload folder path"""
        return os.path.join(current_app.instance_path, 'uploads')
    
    def _ensure_directories(self):
        """Ensure upload directories exist"""
        directories = [
            self.upload_folder,
            os.path.join(self.upload_folder, 'images'),
            os.path.join(self.upload_folder, 'documents'),
            os.path.join(self.upload_folder, 'videos'),
            os.path.join(self.upload_folder, 'audio'),
            os.path.join(self.upload_folder, 'archives'),
            os.path.join(self.upload_folder, 'other'),
            os.path.join(self.upload_folder, 'thumbnails'),
            os.path.join(self.upload_folder, 'previews')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def validate_file(self, file) -> Tuple[bool, Dict]:
        """
        Validate uploaded file
        
        Args:
            file: File object from request
            
        Returns:
            Tuple of (is_valid, validation_result)
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        if not file or file.filename == '':
            result['valid'] = False
            result['errors'].append('No file selected')
            return result['valid'], result
        
        # Get file info
        filename = secure_filename(file.filename)
        file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
        file_size = len(file.read())
        file.seek(0)  # Reset file pointer
        
        # Store file info
        result['file_info'] = {
            'filename': filename,
            'extension': file_extension,
            'size': file_size,
            'size_display': self._format_file_size(file_size)
        }
        
        # Check file extension
        category = self._get_file_category(file_extension)
        if not category:
            result['valid'] = False
            result['errors'].append(f'File type .{file_extension} is not allowed')
            return result['valid'], result
        
        # Check file size
        max_size = self.max_file_size[category]
        if file_size > max_size:
            result['valid'] = False
            result['errors'].append(f'File size {result["file_info"]["size_display"]} exceeds maximum {self._format_file_size(max_size)} for {category} files')
            return result['valid'], result
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            result['warnings'].append('Could not determine MIME type')
        
        result['file_info']['category'] = category
        result['file_info']['mime_type'] = mime_type
        
        return result['valid'], result
    
    def _get_file_category(self, extension: str) -> Optional[str]:
        """Get file category based on extension"""
        for category, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return category
        return None
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def calculate_file_hash(self, file) -> str:
        """
        Calculate SHA-256 hash of file content
        
        Args:
            file: File object
            
        Returns:
            SHA-256 hash as hex string
        """
        hash_sha256 = hashlib.sha256()
        
        # Read file in chunks to handle large files
        file.seek(0)
        while chunk := file.read(4096):
            hash_sha256.update(chunk)
        
        file.seek(0)  # Reset file pointer
        return hash_sha256.hexdigest()
    
    def save_file(self, file, category: str, filename: str) -> str:
        """
        Save file to appropriate directory
        
        Args:
            file: File object
            category: File category
            filename: Secure filename
            
        Returns:
            Path to saved file
        """
        category_folder = os.path.join(self.upload_folder, category)
        file_path = os.path.join(category_folder, filename)
        
        # Ensure filename is unique
        counter = 1
        while os.path.exists(file_path):
            name, ext = os.path.splitext(filename)
            file_path = os.path.join(category_folder, f"{name}_{counter}{ext}")
            counter += 1
        
        # Save file
        file.save(file_path)
        return file_path
    
    def create_thumbnail(self, file_path: str, thumbnail_path: str) -> bool:
        """
        Create thumbnail for image file
        
        Args:
            file_path: Path to original image
            thumbnail_path: Path to save thumbnail
            
        Returns:
            Success status
        """
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(thumbnail_path, 'JPEG', quality=85)
                return True
        except Exception as e:
            current_app.logger.error(f"Error creating thumbnail: {e}")
            return False
    
    def create_preview(self, file_path: str, preview_path: str, category: str) -> bool:
        """
        Create preview for file
        
        Args:
            file_path: Path to original file
            preview_path: Path to save preview
            category: File category
            
        Returns:
            Success status
        """
        try:
            if category == 'image':
                # Create larger preview for images
                with Image.open(file_path) as img:
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    img.thumbnail(self.preview_size, Image.Resampling.LANCZOS)
                    img.save(preview_path, 'JPEG', quality=85)
                    return True
            
            elif category == 'document':
                # For documents, create a simple text preview if possible
                if file_path.lower().endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(500)  # First 500 characters
                    with open(preview_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return True
            
            return False
        except Exception as e:
            current_app.logger.error(f"Error creating preview: {e}")
            return False
    
    def upload_attachment(self, file, message_id: int, user_id: int) -> Tuple[bool, Dict]:
        """
        Upload and process file attachment
        
        Args:
            file: File object from request
            message_id: ID of message to attach to
            user_id: ID of user uploading file
            
        Returns:
            Tuple of (success, result)
        """
        result = {
            'success': False,
            'attachment_id': None,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        # Validate file
        is_valid, validation_result = self.validate_file(file)
        if not is_valid:
            result['errors'] = validation_result['errors']
            return False, result
        
        result['warnings'] = validation_result['warnings']
        result['file_info'] = validation_result['file_info']
        
        try:
            # Calculate file hash
            file_hash = self.calculate_file_hash(file)
            
            # Check for duplicate files
            existing_attachment = MessageAttachment.query.filter_by(file_hash=file_hash).first()
            if existing_attachment:
                result['warnings'].append('File already exists, creating reference to existing attachment')
                # Create new attachment record pointing to same file
                attachment = MessageAttachment(
                    message_id=message_id,
                    filename=existing_attachment.filename,
                    original_filename=validation_result['file_info']['filename'],
                    file_path=existing_attachment.file_path,
                    file_size=validation_result['file_info']['size'],
                    file_type=validation_result['file_info'].get('mime_type', 'application/octet-stream'),
                    file_category=validation_result['file_info']['category'],
                    file_hash=file_hash,
                    thumbnail_path=existing_attachment.thumbnail_path,
                    preview_path=existing_attachment.preview_path,
                    upload_ip=request.remote_addr if 'request' in globals() else None
                )
            else:
                # Save file
                category = validation_result['file_info']['category']
                filename = validation_result['file_info']['filename']
                file_path = self.save_file(file, category, filename)
                
                # Create thumbnail and preview for images
                thumbnail_path = None
                preview_path = None
                
                if category == 'image':
                    thumbnail_filename = f"thumb_{filename}"
                    thumbnail_path = os.path.join(self.upload_folder, 'thumbnails', thumbnail_filename)
                    self.create_thumbnail(file_path, thumbnail_path)
                    
                    preview_filename = f"preview_{filename}"
                    preview_path = os.path.join(self.upload_folder, 'previews', preview_filename)
                    self.create_preview(file_path, preview_path, category)
                
                elif category == 'document':
                    preview_filename = f"preview_{filename}"
                    preview_path = os.path.join(self.upload_folder, 'previews', preview_filename)
                    self.create_preview(file_path, preview_path, category)
                
                # Create attachment record
                attachment = MessageAttachment(
                    message_id=message_id,
                    filename=filename,
                    original_filename=validation_result['file_info']['filename'],
                    file_path=file_path,
                    file_size=validation_result['file_info']['size'],
                    file_type=validation_result['file_info'].get('mime_type', 'application/octet-stream'),
                    file_category=category,
                    file_hash=file_hash,
                    thumbnail_path=thumbnail_path,
                    preview_path=preview_path,
                    upload_ip=request.remote_addr if 'request' in globals() else None
                )
            
            db.session.add(attachment)
            db.session.commit()
            
            result['success'] = True
            result['attachment_id'] = attachment.id
            result['file_info']['attachment_id'] = attachment.id
            result['file_info']['thumbnail_url'] = attachment.get_thumbnail_url()
            result['file_info']['preview_url'] = attachment.get_preview_url()
            result['file_info']['download_url'] = attachment.get_download_url()
            
            return True, result
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error uploading attachment: {e}")
            result['errors'].append(f'Upload failed: {str(e)}')
            return False, result
    
    def get_attachment(self, attachment_id: int, user_id: int) -> Optional[MessageAttachment]:
        """
        Get attachment with permission check
        
        Args:
            attachment_id: Attachment ID
            user_id: User ID requesting attachment
            
        Returns:
            Attachment object or None if not found/authorized
        """
        attachment = MessageAttachment.query.get(attachment_id)
        
        if not attachment:
            return None
        
        # Check if user has permission to access this attachment
        message = attachment.message
        if message.sender_id != user_id and message.receiver_id != user_id:
            return None
        
        return attachment
    
    def delete_attachment(self, attachment_id: int, user_id: int) -> bool:
        """
        Delete attachment with permission check
        
        Args:
            attachment_id: Attachment ID
            user_id: User ID deleting attachment
            
        Returns:
            Success status
        """
        attachment = self.get_attachment(attachment_id, user_id)
        
        if not attachment:
            return False
        
        try:
            # Delete physical files
            if os.path.exists(attachment.file_path):
                os.remove(attachment.file_path)
            
            if attachment.thumbnail_path and os.path.exists(attachment.thumbnail_path):
                os.remove(attachment.thumbnail_path)
            
            if attachment.preview_path and os.path.exists(attachment.preview_path):
                os.remove(attachment.preview_path)
            
            # Delete database record
            db.session.delete(attachment)
            db.session.commit()
            
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting attachment: {e}")
            return False
    
    def get_user_attachments(self, user_id: int, page: int = 1, per_page: int = 20) -> Dict:
        """
        Get all attachments for user's messages
        
        Args:
            user_id: User ID
            page: Page number
            per_page: Results per page
            
        Returns:
            Dictionary with attachments and pagination info
        """
        # Get attachments from messages where user is sender or receiver
        attachments = MessageAttachment.query.join(Message).filter(
            (Message.sender_id == user_id) | (Message.receiver_id == user_id)
        ).order_by(MessageAttachment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'attachments': attachments.items,
            'total': attachments.total,
            'page': attachments.page,
            'per_page': per_page,
            'total_pages': attachments.pages
        }
    
    def get_attachment_analytics(self, user_id: int = None, days: int = 30) -> Dict:
        """
        Get attachment analytics
        
        Args:
            user_id: User ID (None for all users)
            days: Number of days to analyze
            
        Returns:
            Analytics dictionary
        """
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = MessageAttachment.query.filter(MessageAttachment.created_at >= start_date)
        
        if user_id:
            query = query.join(Message).filter(
                (Message.sender_id == user_id) | (Message.receiver_id == user_id)
            )
        
        attachments = query.all()
        
        # Calculate analytics
        total_attachments = len(attachments)
        total_size = sum(att.file_size for att in attachments)
        category_counts = {}
        download_counts = {}
        
        for attachment in attachments:
            category = attachment.file_category
            category_counts[category] = category_counts.get(category, 0) + 1
            download_counts[attachment.id] = attachment.download_count
        
        # Most downloaded attachments
        most_downloaded = sorted(
            attachments, 
            key=lambda x: x.download_count, 
            reverse=True
        )[:5]
        
        return {
            'total_attachments': total_attachments,
            'total_size': total_size,
            'total_size_display': self._format_file_size(total_size),
            'average_size': self._format_file_size(total_size // total_attachments) if total_attachments > 0 else '0 B',
            'category_distribution': category_counts,
            'most_downloaded': [
                {
                    'id': att.id,
                    'filename': att.original_filename,
                    'downloads': att.download_count,
                    'category': att.file_category
                }
                for att in most_downloaded
            ],
            'days_analyzed': days
        }


def validate_attachment_file(file) -> Tuple[bool, Dict]:
    """
    Validate attachment file (convenience function)
    
    Args:
        file: File object from request
        
    Returns:
        Tuple of (is_valid, validation_result)
    """
    manager = FileAttachmentManager()
    return manager.validate_file(file)


def upload_message_attachment(file, message_id: int, user_id: int) -> Tuple[bool, Dict]:
    """
    Upload message attachment (convenience function)
    
    Args:
        file: File object from request
        message_id: ID of message to attach to
        user_id: ID of user uploading file
        
    Returns:
        Tuple of (success, result)
    """
    manager = FileAttachmentManager()
    return manager.upload_attachment(file, message_id, user_id)


def get_user_attachment_analytics(user_id: int = None, days: int = 30) -> Dict:
    """
    Get attachment analytics (convenience function)
    
    Args:
        user_id: User ID (None for all users)
        days: Number of days to analyze
        
    Returns:
        Analytics dictionary
    """
    manager = FileAttachmentManager()
    return manager.get_attachment_analytics(user_id, days)
