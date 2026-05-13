/**
 * File Management JavaScript
 * 
 * This script provides JavaScript functionality for the advanced file management system,
 * including file uploads, previews, drag-and-drop, and real-time progress tracking.
 */

class FileManager {
    constructor() {
        this.uploadQueue = [];
        this.isUploading = false;
        this.maxFileSize = 50 * 1024 * 1024; // 50MB
        this.allowedExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'zip', 'rar'];
        this.init();
    }

    init() {
        this.setupDragAndDrop();
        this.setupFileUpload();
        this.setupFilePreview();
        this.setupProgressTracking();
        this.setupBulkActions();
    }

    // Drag and Drop functionality
    setupDragAndDrop() {
        const dropZone = document.getElementById('dropZone');
        if (!dropZone) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.unhighlight, false);
        });

        dropZone.addEventListener('drop', this.handleDrop.bind(this), false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    highlight(e) {
        document.getElementById('dropZone').classList.add('highlight');
    }

    unhighlight(e) {
        document.getElementById('dropZone').classList.remove('highlight');
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    }

    // File Upload functionality
    setupFileUpload() {
        const fileInput = document.getElementById('file');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFiles(e.target.files);
            });
        }
    }

    handleFiles(files) {
        const validFiles = Array.from(files).filter(file => this.validateFile(file));
        
        if (validFiles.length === 0) {
            this.showNotification('No valid files selected', 'error');
            return;
        }

        validFiles.forEach(file => {
            this.addToQueue(file);
        });

        if (!this.isUploading) {
            this.processQueue();
        }
    }

    validateFile(file) {
        // Check file size
        if (file.size > this.maxFileSize) {
            this.showNotification(`File ${file.name} is too large (max 50MB)`, 'error');
            return false;
        }

        // Check file extension
        const extension = file.name.split('.').pop().toLowerCase();
        if (!this.allowedExtensions.includes(extension)) {
            this.showNotification(`File type ${extension} is not allowed`, 'error');
            return false;
        }

        return true;
    }

    addToQueue(file) {
        const fileItem = {
            file: file,
            id: Date.now() + Math.random(),
            status: 'queued',
            progress: 0,
            error: null
        };

        this.uploadQueue.push(fileItem);
        this.updateQueueUI();
        this.showNotification(`${file.name} added to upload queue`, 'info');
    }

    processQueue() {
        if (this.uploadQueue.length === 0) {
            this.isUploading = false;
            return;
        }

        this.isUploading = true;
        const fileItem = this.uploadQueue[0];
        fileItem.status = 'uploading';

        this.uploadFile(fileItem);
    }

    uploadFile(fileItem) {
        const formData = new FormData();
        formData.append('file', fileItem.file);

        // Add other form data if available
        const description = document.getElementById('description');
        const folder = document.getElementById('folder');
        const tags = document.getElementById('tags');
        const isPublic = document.getElementById('is_public');

        if (description) formData.append('description', description.value);
        if (folder) formData.append('folder', folder.value);
        if (tags) formData.append('tags', tags.value);
        if (isPublic) formData.append('is_public', isPublic.checked);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/files/upload');

        // Progress tracking
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                fileItem.progress = percentComplete;
                this.updateProgress(fileItem.id, percentComplete);
            }
        });

        // Completion
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                fileItem.status = 'completed';
                fileItem.progress = 100;
                this.updateProgress(fileItem.id, 100);
                this.showNotification(`${fileItem.file.name} uploaded successfully!`, 'success');
                
                // Remove from queue after delay
                setTimeout(() => {
                    this.removeFromQueue(fileItem.id);
                    this.processQueue();
                }, 1000);
            } else {
                fileItem.status = 'error';
                fileItem.error = 'Upload failed';
                this.showNotification(`Upload failed for ${fileItem.file.name}`, 'error');
                this.removeFromQueue(fileItem.id);
                this.processQueue();
            }
        });

        // Error handling
        xhr.addEventListener('error', () => {
            fileItem.status = 'error';
            fileItem.error = 'Network error';
            this.showNotification(`Network error uploading ${fileItem.file.name}`, 'error');
            this.removeFromQueue(fileItem.id);
            this.processQueue();
        });

        xhr.send(formData);
    }

    updateProgress(fileId, progress) {
        const progressBar = document.getElementById(`progress-${fileId}`);
        if (progressBar) {
            progressBar.style.width = progress + '%';
            progressBar.textContent = Math.round(progress) + '%';
        }
    }

    removeFromQueue(fileId) {
        this.uploadQueue = this.uploadQueue.filter(item => item.id !== fileId);
        this.updateQueueUI();
    }

    updateQueueUI() {
        // This would update the UI to show the upload queue
        // Implementation depends on the specific template structure
    }

    // File Preview functionality
    setupFilePreview() {
        const fileInput = document.getElementById('file');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.showFilePreview(file);
                }
            });
        }
    }

    showFilePreview(file) {
        const previewContainer = document.getElementById('filePreview');
        const previewContent = document.getElementById('previewContent');
        
        if (!previewContainer || !previewContent) return;

        previewContainer.style.display = 'block';

        const fileInfo = `
            <div class="row">
                <div class="col-md-6">
                    <strong>Name:</strong> ${file.name}<br>
                    <strong>Size:</strong> ${this.formatFileSize(file.size)}<br>
                    <strong>Type:</strong> ${file.type || 'Unknown'}
                </div>
                <div class="col-md-6">
                    <strong>Last Modified:</strong> ${new Date(file.lastModified).toLocaleString()}<br>
                    <strong>Extension:</strong> ${this.getFileExtension(file.name)}
                </div>
            </div>
        `;
        
        previewContent.innerHTML = fileInfo;

        // Show image preview if it's an image
        if (file.type && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewContent.innerHTML += `
                    <div class="mt-3">
                        <img src="${e.target.result}" class="img-fluid rounded" alt="Preview">
                    </div>
                `;
            };
            reader.readAsDataURL(file);
        }
    }

    // Progress Tracking
    setupProgressTracking() {
        // Initialize progress tracking elements
        this.setupProgressBars();
        this.setupStatusUpdates();
    }

    setupProgressBars() {
        // Create progress bars for upload queue items
        const progressContainer = document.getElementById('uploadProgress');
        if (progressContainer) {
            progressContainer.style.display = 'block';
        }
    }

    setupStatusUpdates() {
        // Update status messages during upload
        const uploadStatus = document.getElementById('uploadStatus');
        if (uploadStatus) {
            uploadStatus.textContent = 'Preparing upload...';
        }
    }

    // Bulk Actions
    setupBulkActions() {
        const selectAllCheckbox = document.getElementById('selectAll');
        const fileCheckboxes = document.querySelectorAll('input[name="file_ids"]');
        
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                fileCheckboxes.forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                });
                this.updateBulkActionButton();
            });
        }

        fileCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBulkActionButton();
            });
        });

        // Handle action changes
        const actionSelect = document.querySelector('select[name="action"]');
        if (actionSelect) {
            actionSelect.addEventListener('change', (e) => {
                this.toggleActionOptions(e.target.value);
            });
        }
    }

    updateBulkActionButton() {
        const form = document.getElementById('bulkActionForm');
        const submitButton = form.querySelector('button[type="submit"]');
        const selectedCount = document.querySelectorAll('input[name="file_ids"]:checked').length;
        
        submitButton.disabled = selectedCount === 0;
        submitButton.textContent = selectedCount > 0 ? 
            `Apply Action (${selectedCount} selected)` : 'Apply Action';
    }

    toggleActionOptions(action) {
        const targetFolderField = document.getElementById('targetFolderField');
        if (targetFolderField) {
            targetFolderField.style.display = action === 'move' ? 'inline-block' : 'none';
        }
    }

    // Utility functions
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getFileExtension(filename) {
        return filename.split('.').pop().toUpperCase();
    }

    getFileIcon(fileType) {
        const icons = {
            'image': 'image',
            'document': 'file-alt',
            'video': 'video',
            'audio': 'music',
            'other': 'file'
        };
        return icons[fileType] || 'file';
    }

    getFileTypeColor(fileType) {
        const colors = {
            'image': 'primary',
            'document': 'success',
            'video': 'danger',
            'audio': 'info',
            'other': 'secondary'
        };
        return colors[fileType] || 'secondary';
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to notification container
        const container = document.getElementById('notificationContainer');
        if (!container) {
            const newContainer = document.createElement('div');
            newContainer.id = 'notificationContainer';
            newContainer.className = 'notification-container';
            document.body.appendChild(newContainer);
        }
        
        document.getElementById('notificationContainer').appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Image processing
    processImage(fileId) {
        // This would open an image processing modal
        this.showNotification('Image processing feature coming soon!', 'info');
    }

    // File sharing
    copyShareLink(fileId) {
        const shareLink = window.location.origin + '/files/file/' + fileId;
        
        navigator.clipboard.writeText(shareLink).then(() => {
            this.showNotification('Share link copied to clipboard!', 'success');
        }).catch(err => {
            this.showNotification('Failed to copy link', 'error');
        });
    }

    // File deletion
    deleteFile(fileId) {
        if (confirm('Are you sure you want to delete this file? This action cannot be undone.')) {
            fetch('/files/delete/' + fileId, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                }
            })
            .then(response => {
                if (response.ok) {
                    this.showNotification('File deleted successfully', 'success');
                    // Redirect or update UI
                    window.location.href = '/files/files';
                } else {
                    this.showNotification('Failed to delete file', 'error');
                }
            })
            .catch(error => {
                this.showNotification('Error deleting file: ' + error.message, 'error');
            });
        }
    }

    // Search functionality
    setupSearch() {
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            let searchTimeout;
            const searchInput = searchForm.querySelector('input[name="query"]');
            
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(() => {
                        searchForm.submit();
                    }, 500);
                });
            }
        }
    }

    // File preview modal
    showFilePreviewModal(fileId) {
        // This would open a modal with file preview
        fetch('/files/preview/' + fileId)
            .then(response => response.text())
            .then(html => {
                // Create modal and show preview
                const modal = document.createElement('div');
                modal.className = 'modal fade';
                modal.innerHTML = html;
                document.body.appendChild(modal);
                
                const modalInstance = new bootstrap.Modal(modal);
                modalInstance.show();
                
                // Clean up after modal is hidden
                modal.addEventListener('hidden.bs.modal', () => {
                    modal.remove();
                });
            })
            .catch(error => {
                this.showNotification('Error loading preview', 'error');
            });
    }

    // Initialize the file manager
    static init() {
        return new FileManager();
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.fileManager = FileManager.init();
});

// Export for use in other scripts
window.FileManager = FileManager;
