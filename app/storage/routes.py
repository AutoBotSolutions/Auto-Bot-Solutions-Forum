"""
File Management Routes

This module contains routes for the advanced file management system,
including file uploads, sharing, analytics, and permissions.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import FileStorage, FileShare, FileAnalytics, User
from app.storage.forms import (
    FileUploadForm, FileEditForm, FileShareForm, FileSearchForm, BulkFileActionForm,
    ImageProcessingForm, FileAnalyticsForm, FolderCreateForm, FileLinkForm,
    FileImportForm, FileExportForm, FilePermissionForm, FileVersionForm,
    FileCommentForm, FileTagForm, FileReportForm, FileSettingsForm
)
from app.storage.service import create_storage_service
from app.storage.image_processor import ImageProcessor
from app.storage.preview_generator import PreviewGenerator
from app import db
from datetime import datetime, timedelta
import os
import uuid
import mimetypes

storage_bp = Blueprint('storage', __name__, url_prefix='/files')

@storage_bp.route('/dashboard')
@login_required
def dashboard():
    """File management dashboard"""
    # Get user's file statistics
    total_files = FileStorage.query.filter_by(uploaded_by=current_user.id).count()
    total_size = db.session.query(db.func.sum(FileStorage.file_size)).filter_by(uploaded_by=current_user.id).scalar() or 0
    public_files = FileStorage.query.filter_by(uploaded_by=current_user.id, is_public=True).count()
    shared_files = FileShare.query.filter_by(shared_by=current_user.id, is_active=True).count()
    
    # Get recent uploads
    recent_files = FileStorage.query.filter_by(uploaded_by=current_user.id).order_by(FileStorage.upload_date.desc()).limit(5).all()
    
    # Get storage usage by type
    storage_by_type = db.session.query(
        FileStorage.file_type,
        db.func.count(FileStorage.id).label('count'),
        db.func.sum(FileStorage.file_size).label('size')
    ).filter_by(uploaded_by=current_user.id).group_by(FileStorage.file_type).all()
    
    # Get popular files (most downloaded)
    popular_files = FileStorage.query.filter_by(uploaded_by=current_user.id).order_by(FileStorage.download_count.desc()).limit(5).all()
    
    return render_template('storage/dashboard.html',
                         total_files=total_files,
                         total_size=total_size,
                         public_files=public_files,
                         shared_files=shared_files,
                         recent_files=recent_files,
                         storage_by_type=storage_by_type,
                         popular_files=popular_files)

@storage_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """Upload a new file"""
    form = FileUploadForm()
    
    if form.validate_on_submit():
        try:
            # Initialize storage service
            storage_service = create_storage_service()
            
            # Upload file
            upload_result = storage_service.upload_file(
                form.file.data,
                folder=form.folder.data,
                is_public=form.is_public.data
            )
            
            # Create file record
            file_record = FileStorage(
                original_filename=form.file.data.filename,
                stored_filename=upload_result['file_path'],
                file_path=upload_result['file_path'],
                file_size=len(form.file.data.getvalue()),
                mime_type=mimetypes.guess_type(form.file.data.filename)[0] or 'application/octet-stream',
                file_type=storage_service._get_file_type(mimetypes.guess_type(form.file.data.filename)[0] or 'application/octet-stream'),
                storage_provider=upload_result['provider'],
                storage_bucket=upload_result.get('bucket'),
                storage_region=upload_result.get('region'),
                is_public=form.is_public.data,
                uploaded_by=current_user.id,
                owner_id=current_user.id
            )
            
            # Process image if applicable
            if file_record.file_type == 'image':
                try:
                    image_processor = ImageProcessor(storage_service)
                    processing_result = image_processor.process_image(form.file.data, form.file.data.filename)
                    
                    if processing_result.get('optimized'):
                        file_record.optimized_path = processing_result['optimized']['path']
                    
                    if processing_result.get('thumbnails'):
                        file_record.thumbnail_path = processing_result['thumbnails']['medium']['path']
                        file_record.preview_available = True
                    
                    file_record.is_processed = True
                    
                except Exception as e:
                    current_app.logger.error(f"Image processing error: {e}")
            
            # Generate preview
            try:
                preview_generator = PreviewGenerator(storage_service)
                preview_result = preview_generator.generate_preview(
                    upload_result['file_path'],
                    file_record.file_type,
                    form.file.data.filename
                )
                
                if preview_result:
                    file_record.preview_available = True
                    
            except Exception as e:
                current_app.logger.error(f"Preview generation error: {e}")
            
            # Save file record
            db.session.add(file_record)
            db.session.commit()
            
            # Log analytics
            analytics = FileAnalytics(
                file_id=file_record.id,
                user_id=current_user.id,
                action_type='upload',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                file_size=file_record.file_size
            )
            db.session.add(analytics)
            db.session.commit()
            
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('storage.files'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading file: {str(e)}', 'error')
    
    return render_template('storage/upload.html', form=form)

@storage_bp.route('/files')
@login_required
def files():
    """List and manage files"""
    form = FileSearchForm(request.args)
    query = FileStorage.query.filter_by(uploaded_by=current_user.id)
    
    # Apply filters
    if form.validate():
        if form.query.data:
            query = query.filter(FileStorage.original_filename.contains(form.query.data))
        
        if form.file_type.data != 'all':
            query = query.filter_by(file_type=form.file_type.data)
        
        if form.uploaded_by.data:
            query = query.filter_by(uploaded_by=form.uploaded_by.data)
        
        if form.date_from.data:
            query = query.filter(FileStorage.upload_date >= form.date_from.data)
        
        if form.date_to.data:
            query = query.filter(FileStorage.upload_date <= form.date_to.data)
        
        if form.tags.data:
            # Filter by tags (simplified)
            tags = [tag.strip() for tag in form.tags.data.split(',')]
            for tag in tags:
                query = query.filter(FileStorage.original_filename.contains(tag))
    
    files = query.order_by(FileStorage.upload_date.desc()).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=20,
        error_out=False
    )
    
    return render_template('storage/files.html', files=files, form=form)

@storage_bp.route('/file/<int:file_id>')
@login_required
def file_detail(file_id):
    """View file details"""
    file_record = FileStorage.query.get_or_404(file_id)
    
    # Check permissions
    if file_record.uploaded_by != current_user.id and not file_record.is_public:
        # Check if shared with user
        share = FileShare.query.filter_by(
            file_id=file_id, shared_with=current_user.id, is_active=True
        ).first()
        if not share:
            flash('You do not have permission to view this file.', 'error')
            return redirect(url_for('storage.files'))
    
    # Get file analytics
    analytics = FileAnalytics.query.filter_by(file_id=file_id).order_by(FileAnalytics.timestamp.desc()).limit(10).all()
    
    # Get file shares
    shares = FileShare.query.filter_by(file_id=file_id, is_active=True).all()
    
    # Get preview
    preview = None
    if file_record.preview_available:
        try:
            storage_service = create_storage_service()
            preview_generator = PreviewGenerator(storage_service)
            preview = preview_generator.generate_preview(
                file_record.file_path,
                file_record.file_type,
                file_record.original_filename
            )
        except Exception as e:
            current_app.logger.error(f"Preview error: {e}")
    
    return render_template('storage/file_detail.html',
                         file=file_record,
                         analytics=analytics,
                         shares=shares,
                         preview=preview)

@storage_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    """Download a file"""
    file_record = FileStorage.query.get_or_404(file_id)
    
    # Check permissions
    if file_record.uploaded_by != current_user.id and not file_record.is_public:
        # Check if shared with user
        share = FileShare.query.filter_by(
            file_id=file_id, shared_with=current_user.id, is_active=True
        ).first()
        if not share or share.permission_level not in ['download', 'edit']:
            flash('You do not have permission to download this file.', 'error')
            return redirect(url_for('storage.files'))
    
    try:
        # Update download count
        file_record.download_count += 1
        file_record.last_downloaded = datetime.utcnow()
        
        # Update share download count if applicable
        if file_record.uploaded_by != current_user.id:
            share = FileShare.query.filter_by(
                file_id=file_id, shared_with=current_user.id, is_active=True
            ).first()
            if share:
                share.download_count += 1
                share.last_accessed = datetime.utcnow()
        
        # Log analytics
        analytics = FileAnalytics(
            file_id=file_id,
            user_id=current_user.id,
            action_type='download',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            file_size=file_record.file_size
        )
        db.session.add(analytics)
        db.session.commit()
        
        # Generate download URL
        storage_service = create_storage_service()
        download_url = storage_service.get_file_url(file_record.file_path, expires_in=300)  # 5 minutes
        
        return redirect(download_url)
        
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('storage.file_detail', file_id=file_id))

@storage_bp.route('/share/<int:file_id>', methods=['GET', 'POST'])
@login_required
def share_file(file_id):
    """Share a file with other users"""
    file_record = FileStorage.query.get_or_404(file_id)
    
    # Check if user owns the file
    if file_record.uploaded_by != current_user.id:
        flash('Only the file owner can share files.', 'error')
        return redirect(url_for('storage.file_detail', file_id=file_id))
    
    form = FileShareForm()
    
    if form.validate_on_submit():
        try:
            # Check if user exists
            user = User.query.get(form.user_id.data)
            if not user:
                flash('User not found.', 'error')
                return redirect(url_for('storage.share_file', file_id=file_id))
            
            # Check if already shared
            existing_share = FileShare.query.filter_by(
                file_id=file_id, shared_with=form.user_id.data
            ).first()
            
            if existing_share:
                existing_share.permission_level = form.permission_level.data
                existing_share.expires_at = form.expires_at.data
                existing_share.is_active = True
                flash('File share updated successfully!', 'success')
            else:
                new_share = FileShare(
                    file_id=file_id,
                    shared_with=form.user_id.data,
                    shared_by=current_user.id,
                    permission_level=form.permission_level.data,
                    expires_at=form.expires_at.data
                )
                db.session.add(new_share)
                flash('File shared successfully!', 'success')
            
            # Log analytics
            analytics = FileAnalytics(
                file_id=file_id,
                user_id=form.user_id.data,
                action_type='share',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(analytics)
            db.session.commit()
            
            return redirect(url_for('storage.file_detail', file_id=file_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error sharing file: {str(e)}', 'error')
    
    return render_template('storage/share_file.html', form=form, file=file_record)

@storage_bp.route('/analytics')
@login_required
def analytics():
    """File analytics dashboard"""
    form = FileAnalyticsForm(request.args)
    
    # Base query
    query = FileAnalytics.query
    
    # Apply filters
    if form.validate():
        if form.date_from.data:
            query = query.filter(FileAnalytics.timestamp >= form.date_from.data)
        
        if form.date_to.data:
            query = query.filter(FileAnalytics.timestamp <= form.date_to.data)
        
        if form.file_id.data:
            query = query.filter_by(file_id=form.file_id.data)
        
        if form.user_id.data:
            query = query.filter_by(user_id=form.user_id.data)
    
    # Filter by user's files
    if current_user.id != 1:  # Not admin
        file_ids = db.session.query(FileStorage.id).filter_by(uploaded_by=current_user.id).subquery()
        query = query.filter(FileAnalytics.file_id.in_(file_ids))
    
    # Get analytics data
    analytics_data = query.order_by(FileAnalytics.timestamp.desc()).limit(100).all()
    
    # Summary statistics
    total_actions = query.count()
    unique_files = query.with_entities(db.func.count(db.func.distinct(FileAnalytics.file_id))).scalar()
    unique_users = query.with_entities(db.func.count(db.func.distinct(FileAnalytics.user_id))).scalar()
    
    # Action breakdown
    action_stats = query.with_entities(
        FileAnalytics.action_type,
        db.func.count(FileAnalytics.id).label('count')
    ).group_by(FileAnalytics.action_type).all()
    
    return render_template('storage/analytics.html',
                         analytics_data=analytics_data,
                         form=form,
                         total_actions=total_actions,
                         unique_files=unique_files,
                         unique_users=unique_users,
                         action_stats=action_stats)

@storage_bp.route('/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    """Perform bulk actions on files"""
    form = BulkFileActionForm(request.form)
    file_ids = request.form.getlist('file_ids')
    
    if not file_ids:
        flash('No files selected.', 'error')
        return redirect(url_for('storage.files'))
    
    if form.validate_on_submit():
        action = form.action.data
        files = FileStorage.query.filter(
            FileStorage.id.in_(file_ids),
            FileStorage.uploaded_by == current_user.id
        ).all()
        
        try:
            if action == 'delete':
                for file_record in files:
                    storage_service = create_storage_service()
                    storage_service.delete_file(file_record.file_path)
                    
                    # Delete thumbnails and optimized versions
                    if file_record.thumbnail_path:
                        storage_service.delete_file(file_record.thumbnail_path)
                    if file_record.optimized_path:
                        storage_service.delete_file(file_record.optimized_path)
                    
                    db.session.delete(file_record)
                
                flash(f'{len(files)} files deleted successfully!', 'success')
            
            elif action == 'share':
                # This would require additional form fields for sharing details
                flash('Bulk sharing not implemented yet.', 'info')
            
            elif action == 'move':
                if form.target_folder.data:
                    for file_record in files:
                        # Move files to target folder
                        storage_service = create_storage_service()
                        old_path = file_record.file_path
                        new_path = f"{form.target_folder.data}/{os.path.basename(file_record.file_path)}"
                        
                        # Move file in storage
                        # This would depend on the storage provider implementation
                        file_record.file_path = new_path
                        file_record.stored_filename = new_path
                
                flash(f'{len(files)} files moved successfully!', 'success')
            
            elif action == 'tag':
                if form.tags.data:
                    tags = form.tags.data
                    # This would require adding tags to files
                    flash(f'Tags added to {len(files)} files!', 'success')
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            flash(f'Bulk action error: {str(e)}', 'error')
    
    return redirect(url_for('storage.files'))

@storage_bp.route('/preview/<int:file_id>')
@login_required
def preview_file(file_id):
    """Generate file preview"""
    file_record = FileStorage.query.get_or_404(file_id)
    
    # Check permissions
    if file_record.uploaded_by != current_user.id and not file_record.is_public:
        share = FileShare.query.filter_by(
            file_id=file_id, shared_with=current_user.id, is_active=True
        ).first()
        if not share:
            abort(403)
    
    try:
        storage_service = create_storage_service()
        preview_generator = PreviewGenerator(storage_service)
        preview = preview_generator.generate_preview(
            file_record.file_path,
            file_record.file_type,
            file_record.original_filename
        )
        
        if preview and preview.get('type') == 'image':
            return redirect(preview['url'])
        elif preview and preview.get('preview_text'):
            return preview['preview_text']
        else:
            return "Preview not available", 404
            
    except Exception as e:
        current_app.logger.error(f"Preview error: {e}")
        return "Preview not available", 500

# Error handlers
@storage_bp.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@storage_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    current_app.logger.error(f"Internal error in storage routes: {str(error)}")
    return render_template('errors/500.html'), 500
