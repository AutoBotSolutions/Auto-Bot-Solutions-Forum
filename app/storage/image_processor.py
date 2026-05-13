"""
Image Processor

This module provides image optimization and thumbnail generation capabilities
using PIL/Pillow for image processing.
"""

import os
import io
from PIL import Image, ImageOps, ExifTags
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Image processing and optimization service"""
    
    def __init__(self, storage_service):
        self.storage_service = storage_service
        self.thumbnail_sizes = {
            'small': (150, 150),
            'medium': (300, 300),
            'large': (800, 800)
        }
        self.optimization_quality = 85
        self.supported_formats = ['JPEG', 'PNG', 'WEBP', 'GIF']
    
    def process_image(self, file, filename, optimize=True, generate_thumbnails=True):
        """Process uploaded image with optimization and thumbnail generation"""
        try:
            # Reset file pointer
            file.seek(0)
            
            # Open image
            image = Image.open(file)
            
            # Handle orientation based on EXIF data
            image = self._fix_image_orientation(image)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            
            # Get original dimensions
            original_width, original_height = image.size
            
            results = {
                'original_size': (original_width, original_height),
                'file_size': len(file.getvalue()) if hasattr(file, 'getvalue') else 0,
                'format': image.format,
                'thumbnails': {},
                'optimized': None
            }
            
            # Generate optimized version
            if optimize:
                optimized_info = self._optimize_image(image, filename)
                results['optimized'] = optimized_info
            
            # Generate thumbnails
            if generate_thumbnails:
                thumbnails = self._generate_thumbnails(image, filename)
                results['thumbnails'] = thumbnails
            
            return results
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            raise
    
    def _fix_image_orientation(self, image):
        """Fix image orientation based on EXIF data"""
        try:
            # Get EXIF data
            exif = image._getexif()
            
            if exif is not None:
                # Find orientation tag
                for tag, value in exif.items():
                    if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == 'Orientation':
                        if value == 3:
                            image = image.rotate(180, expand=True)
                        elif value == 6:
                            image = image.rotate(270, expand=True)
                        elif value == 8:
                            image = image.rotate(90, expand=True)
                        break
            
            return image
            
        except Exception as e:
            logger.warning(f"Could not fix image orientation: {e}")
            return image
    
    def _optimize_image(self, image, filename):
        """Optimize image for web use"""
        try:
            # Create a copy for optimization
            optimized_image = image.copy()
            
            # Resize if too large (max width 1920px)
            max_width = 1920
            if optimized_image.width > max_width:
                ratio = max_width / optimized_image.width
                new_height = int(optimized_image.height * ratio)
                optimized_image = optimized_image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to RGB for JPEG
            if optimized_image.mode != 'RGB':
                optimized_image = optimized_image.convert('RGB')
            
            # Save optimized version to memory
            output = io.BytesIO()
            
            # Determine format
            original_format = image.format or 'JPEG'
            if original_format == 'PNG':
                optimized_image.save(output, format='PNG', optimize=True)
            elif original_format == 'WEBP':
                optimized_image.save(output, format='WEBP', quality=self.optimization_quality, optimize=True)
            else:
                optimized_image.save(output, format='JPEG', quality=self.optimization_quality, optimize=True)
            
            output.seek(0)
            
            # Generate filename
            base_name, ext = os.path.splitext(filename)
            optimized_filename = f"{base_name}_optimized.jpg"
            
            # Upload optimized image
            upload_result = self.storage_service.upload_file(
                output,
                optimized_filename,
                folder='optimized'
            )
            
            return {
                'filename': optimized_filename,
                'path': upload_result['file_path'],
                'url': upload_result['url'],
                'size': len(output.getvalue()),
                'dimensions': optimized_image.size,
                'format': 'JPEG'
            }
            
        except Exception as e:
            logger.error(f"Image optimization error: {e}")
            raise
    
    def _generate_thumbnails(self, image, filename):
        """Generate thumbnails in multiple sizes"""
        thumbnails = {}
        
        try:
            base_name, ext = os.path.splitext(filename)
            
            for size_name, dimensions in self.thumbnail_sizes.items():
                # Create thumbnail
                thumbnail = self._create_thumbnail(image, dimensions)
                
                # Save to memory
                output = io.BytesIO()
                
                # Convert to RGB for JPEG
                if thumbnail.mode != 'RGB':
                    thumbnail = thumbnail.convert('RGB')
                
                thumbnail.save(output, format='JPEG', quality=80, optimize=True)
                output.seek(0)
                
                # Generate filename
                thumbnail_filename = f"{base_name}_thumb_{size_name}.jpg"
                
                # Upload thumbnail
                upload_result = self.storage_service.upload_file(
                    output,
                    thumbnail_filename,
                    folder='thumbnails'
                )
                
                thumbnails[size_name] = {
                    'filename': thumbnail_filename,
                    'path': upload_result['file_path'],
                    'url': upload_result['url'],
                    'size': len(output.getvalue()),
                    'dimensions': dimensions
                }
            
            return thumbnails
            
        except Exception as e:
            logger.error(f"Thumbnail generation error: {e}")
            raise
    
    def _create_thumbnail(self, image, dimensions):
        """Create thumbnail with specified dimensions"""
        try:
            # Create thumbnail
            thumbnail = image.copy()
            
            # Fit to dimensions maintaining aspect ratio
            thumbnail = ImageOps.fit(thumbnail, dimensions, Image.Resampling.LANCZOS)
            
            return thumbnail
            
        except Exception as e:
            logger.error(f"Thumbnail creation error: {e}")
            raise
    
    def resize_image(self, file, filename, width, height, maintain_aspect=True):
        """Resize image to specified dimensions"""
        try:
            # Reset file pointer
            file.seek(0)
            
            # Open image
            image = Image.open(file)
            
            # Fix orientation
            image = self._fix_image_orientation(image)
            
            # Resize
            if maintain_aspect:
                image.thumbnail((width, height), Image.Resampling.LANCZOS)
            else:
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save to memory
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=self.optimization_quality, optimize=True)
            output.seek(0)
            
            # Generate filename
            base_name, ext = os.path.splitext(filename)
            resized_filename = f"{base_name}_resized_{width}x{height}.jpg"
            
            # Upload resized image
            upload_result = self.storage_service.upload_file(
                output,
                resized_filename,
                folder='resized'
            )
            
            return {
                'filename': resized_filename,
                'path': upload_result['file_path'],
                'url': upload_result['url'],
                'size': len(output.getvalue()),
                'dimensions': image.size
            }
            
        except Exception as e:
            logger.error(f"Image resize error: {e}")
            raise
    
    def crop_image(self, file, filename, x, y, width, height):
        """Crop image to specified dimensions"""
        try:
            # Reset file pointer
            file.seek(0)
            
            # Open image
            image = Image.open(file)
            
            # Fix orientation
            image = self._fix_image_orientation(image)
            
            # Crop image
            cropped_image = image.crop((x, y, x + width, y + height))
            
            # Convert to RGB if necessary
            if cropped_image.mode != 'RGB':
                cropped_image = cropped_image.convert('RGB')
            
            # Save to memory
            output = io.BytesIO()
            cropped_image.save(output, format='JPEG', quality=self.optimization_quality, optimize=True)
            output.seek(0)
            
            # Generate filename
            base_name, ext = os.path.splitext(filename)
            cropped_filename = f"{base_name}_cropped_{width}x{height}.jpg"
            
            # Upload cropped image
            upload_result = self.storage_service.upload_file(
                output,
                cropped_filename,
                folder='cropped'
            )
            
            return {
                'filename': cropped_filename,
                'path': upload_result['file_path'],
                'url': upload_result['url'],
                'size': len(output.getvalue()),
                'dimensions': cropped_image.size
            }
            
        except Exception as e:
            logger.error(f"Image crop error: {e}")
            raise
    
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

    def get_image_info(self, file):
        """Get image information without processing"""
        try:
            # Reset file pointer
            file.seek(0)
            
            # Open image
            image = Image.open(file)
            
            # Get EXIF data
            exif_data = {}
            try:
                exif = image._getexif()
                if exif:
                    for tag, value in exif.items():
                        if tag in ExifTags.TAGS:
                            exif_data[ExifTags.TAGS[tag]] = value
            except:
                pass
            
            return {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'file_size': len(file.getvalue()) if hasattr(file, 'getvalue') else 0,
                'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info,
                'exif': exif_data
            }
            
        except Exception as e:
            logger.error(f"Image info error: {e}")
            raise
    
    def is_supported_format(self, filename):
        """Check if image format is supported"""
        try:
            supported_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            return any(filename.lower().endswith(ext) for ext in supported_extensions)
        except:
            return False
    
    def get_thumbnail_url(self, file_path, size='medium'):
        """Get thumbnail URL for a file"""
        try:
            # Generate thumbnail filename
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            thumbnail_path = f"thumbnails/{base_name}_thumb_{size}.jpg"
            
            # Check if thumbnail exists
            if self.storage_service.file_exists(thumbnail_path):
                return self.storage_service.get_file_url(thumbnail_path)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting thumbnail URL: {e}")
            return None
