"""
Preview Generator

This module provides file preview generation capabilities for various file types
including documents, images, videos, and audio files.
"""

import os
import io
import mimetypes
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class PreviewGenerator:
    """File preview generation service"""
    
    def __init__(self, storage_service):
        self.storage_service = storage_service
        self.supported_preview_types = {
            'image': self._generate_image_preview,
            'document': self._generate_document_preview,
            'video': self._generate_video_preview,
            'audio': self._generate_audio_preview,
            'text': self._generate_text_preview
        }
    
    def generate_preview(self, file_path, file_type, original_filename):
        """Generate preview for a file"""
        try:
            if file_type in self.supported_preview_types:
                return self.supported_preview_types[file_type](file_path, original_filename)
            else:
                return self._generate_generic_preview(file_path, original_filename)
        except Exception as e:
            logger.error(f"Preview generation error: {e}")
            return None
    
    def _generate_image_preview(self, file_path, original_filename):
        """Generate preview for image files"""
        try:
            # For images, we can use the original file as preview
            # or generate a smaller version
            preview_path = f"previews/{os.path.basename(file_path)}"
            
            # Check if preview already exists
            if self.storage_service.file_exists(preview_path):
                preview_url = self.storage_service.get_file_url(preview_path)
                return {
                    'type': 'image',
                    'url': preview_url,
                    'path': preview_path,
                    'generated': False
                }
            
            # Create smaller preview
            try:
                # Get file from storage
                if self.storage_service.provider == 'local':
                    full_path = os.path.join(self.storage_service.upload_folder, file_path)
                    if os.path.exists(full_path):
                        with open(full_path, 'rb') as f:
                            image = Image.open(f)
                            
                            # Resize for preview (max 800px)
                            max_size = 800
                            if image.width > max_size or image.height > max_size:
                                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                            
                            # Save preview
                            output = io.BytesIO()
                            if image.mode != 'RGB':
                                image = image.convert('RGB')
                            image.save(output, format='JPEG', quality=85, optimize=True)
                            output.seek(0)
                            
                            # Upload preview
                            upload_result = self.storage_service.upload_file(
                                output,
                                os.path.basename(file_path),
                                folder='previews'
                            )
                            
                            return {
                                'type': 'image',
                                'url': upload_result['url'],
                                'path': upload_result['file_path'],
                                'generated': True
                            }
            except Exception as e:
                logger.warning(f"Could not generate image preview: {e}")
            
            # Fallback to original
            original_url = self.storage_service.get_file_url(file_path)
            return {
                'type': 'image',
                'url': original_url,
                'path': file_path,
                'generated': False
            }
            
        except Exception as e:
            logger.error(f"Image preview error: {e}")
            return None
    
    def _generate_document_preview(self, file_path, original_filename):
        """Generate preview for document files"""
        try:
            # For documents, we can create a thumbnail or use a placeholder
            preview_path = f"previews/{os.path.splitext(os.path.basename(file_path))[0]}_preview.jpg"
            
            # Check if preview already exists
            if self.storage_service.file_exists(preview_path):
                preview_url = self.storage_service.get_file_url(preview_path)
                return {
                    'type': 'document',
                    'url': preview_url,
                    'path': preview_path,
                    'generated': False,
                    'metadata': self._get_document_metadata(original_filename)
                }
            
            # Create document preview placeholder
            try:
                # Create a simple document preview image
                preview_image = self._create_document_placeholder(original_filename)
                
                # Upload preview
                upload_result = self.storage_service.upload_file(
                    preview_image,
                    f"{os.path.splitext(os.path.basename(file_path))[0]}_preview.jpg",
                    folder='previews'
                )
                
                return {
                    'type': 'document',
                    'url': upload_result['url'],
                    'path': upload_result['file_path'],
                    'generated': True,
                    'metadata': self._get_document_metadata(original_filename)
                }
            except Exception as e:
                logger.warning(f"Could not generate document preview: {e}")
            
            # Fallback to placeholder
            return {
                'type': 'document',
                'url': '/static/img/document-placeholder.png',
                'path': None,
                'generated': False,
                'metadata': self._get_document_metadata(original_filename)
            }
            
        except Exception as e:
            logger.error(f"Document preview error: {e}")
            return None
    
    def _generate_video_preview(self, file_path, original_filename):
        """Generate preview for video files"""
        try:
            # For videos, we can extract a frame as thumbnail
            preview_path = f"previews/{os.path.splitext(os.path.basename(file_path))[0]}_thumb.jpg"
            
            # Check if preview already exists
            if self.storage_service.file_exists(preview_path):
                preview_url = self.storage_service.get_file_url(preview_path)
                return {
                    'type': 'video',
                    'thumbnail_url': preview_url,
                    'path': preview_path,
                    'generated': False
                }
            
            # Try to extract video frame (requires ffmpeg)
            try:
                import subprocess
                import tempfile
                
                # Download file temporarily
                if self.storage_service.provider == 'local':
                    video_path = os.path.join(self.storage_service.upload_folder, file_path)
                else:
                    # For cloud storage, we'd need to download first
                    video_path = None
                
                if video_path and os.path.exists(video_path):
                    # Extract frame at 1 second
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        cmd = [
                            'ffmpeg', '-i', video_path, '-ss', '00:00:01', '-vframes', '1',
                            '-y', tmp.name
                        ]
                        subprocess.run(cmd, capture_output=True, check=True)
                        
                        # Upload thumbnail
                        with open(tmp.name, 'rb') as thumb_file:
                            upload_result = self.storage_service.upload_file(
                                thumb_file,
                                f"{os.path.splitext(os.path.basename(file_path))[0]}_thumb.jpg",
                                folder='previews'
                            )
                        
                        # Clean up
                        os.unlink(tmp.name)
                        
                        return {
                            'type': 'video',
                            'thumbnail_url': upload_result['url'],
                            'path': upload_result['file_path'],
                            'generated': True
                        }
            except Exception as e:
                logger.warning(f"Could not extract video frame: {e}")
            
            # Fallback to video placeholder
            return {
                'type': 'video',
                'thumbnail_url': '/static/img/video-placeholder.png',
                'path': None,
                'generated': False
            }
            
        except Exception as e:
            logger.error(f"Video preview error: {e}")
            return None
    
    def _generate_audio_preview(self, file_path, original_filename):
        """Generate preview for audio files"""
        try:
            # For audio, we can show album art or waveform
            return {
                'type': 'audio',
                'thumbnail_url': '/static/img/audio-placeholder.png',
                'path': None,
                'generated': False,
                'metadata': self._get_audio_metadata(original_filename)
            }
            
        except Exception as e:
            logger.error(f"Audio preview error: {e}")
            return None
    
    def _generate_text_preview(self, file_path, original_filename):
        """Generate preview for text files"""
        try:
            # For text files, we can show a snippet
            preview_text = self._extract_text_snippet(file_path)
            
            return {
                'type': 'text',
                'preview_text': preview_text,
                'path': file_path,
                'generated': True
            }
            
        except Exception as e:
            logger.error(f"Text preview error: {e}")
            return None
    
    def _generate_generic_preview(self, file_path, original_filename):
        """Generate generic preview for unsupported file types"""
        try:
            return {
                'type': 'generic',
                'thumbnail_url': '/static/img/file-placeholder.png',
                'path': None,
                'generated': False,
                'metadata': {
                    'filename': original_filename,
                    'size': self.storage_service.get_file_size(file_path)
                }
            }
            
        except Exception as e:
            logger.error(f"Generic preview error: {e}")
            return None
    
    def _create_document_placeholder(self, filename):
        """Create a document placeholder image"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create image
            img = Image.new('RGB', (400, 500), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw document icon
            # Simple rectangle with folded corner
            draw.rectangle([50, 50, 350, 450], fill='white', outline='black', width=2)
            # Folded corner
            draw.polygon([(350, 50), (350, 100), (300, 50)], fill='lightgray', outline='black', width=2)
            
            # Add filename
            try:
                # Try to use a default font
                font = ImageFont.load_default()
                text = os.path.basename(filename)
                if len(text) > 30:
                    text = text[:27] + '...'
                
                # Calculate text position
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_x = (400 - text_width) // 2
                text_y = 250
                
                draw.text((text_x, text_y), text, fill='black', font=font)
            except:
                pass
            
            # Save to bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            
            return output
            
        except Exception as e:
            logger.error(f"Document placeholder error: {e}")
            raise
    
    def _get_document_metadata(self, filename):
        """Get metadata for document files"""
        try:
            ext = os.path.splitext(filename)[1].lower()
            file_type = {
                '.pdf': 'PDF Document',
                '.doc': 'Word Document',
                '.docx': 'Word Document',
                '.xls': 'Excel Spreadsheet',
                '.xlsx': 'Excel Spreadsheet',
                '.ppt': 'PowerPoint Presentation',
                '.pptx': 'PowerPoint Presentation',
                '.txt': 'Text File',
                '.rtf': 'Rich Text Format'
            }.get(ext, 'Document')
            
            return {
                'type': file_type,
                'extension': ext,
                'filename': os.path.basename(filename)
            }
        except:
            return {'type': 'Document', 'filename': os.path.basename(filename)}
    
    def _get_audio_metadata(self, filename):
        """Get metadata for audio files"""
        try:
            ext = os.path.splitext(filename)[1].lower()
            file_type = {
                '.mp3': 'MP3 Audio',
                '.wav': 'WAV Audio',
                '.flac': 'FLAC Audio',
                '.aac': 'AAC Audio',
                '.ogg': 'OGG Audio',
                '.m4a': 'M4A Audio'
            }.get(ext, 'Audio File')
            
            return {
                'type': file_type,
                'extension': ext,
                'filename': os.path.basename(filename)
            }
        except:
            return {'type': 'Audio File', 'filename': os.path.basename(filename)}
    
    def _extract_text_snippet(self, file_path, max_lines=10):
        """Extract text snippet from text file"""
        try:
            if self.storage_service.provider == 'local':
                full_path = os.path.join(self.storage_service.upload_folder, file_path)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        snippet = ''.join(lines[:max_lines])
                        if len(lines) > max_lines:
                            snippet += '\n... (truncated)'
                        return snippet
            else:
                # For cloud storage, we'd need to download first
                return "Text preview not available for cloud storage"
        except Exception as e:
            logger.error(f"Text snippet extraction error: {e}")
            return "Preview not available"
    
    def get_preview_info(self, file_path, file_type, original_filename):
        """Get preview information without generating"""
        try:
            preview_path = f"previews/{os.path.splitext(os.path.basename(file_path))[0]}_preview.jpg"
            
            return {
                'preview_available': self.storage_service.file_exists(preview_path),
                'preview_type': file_type,
                'can_generate': file_type in self.supported_preview_types,
                'supported_formats': list(self.supported_preview_types.keys())
            }
        except Exception as e:
            logger.error(f"Preview info error: {e}")
            return {
                'preview_available': False,
                'preview_type': file_type,
                'can_generate': False,
                'supported_formats': list(self.supported_preview_types.keys())
            }
