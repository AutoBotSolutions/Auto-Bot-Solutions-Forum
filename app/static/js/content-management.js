/**
 * Content Management JavaScript
 * 
 * This script provides JavaScript functionality for the enhanced content management system,
 * including auto-save, version comparison, collaboration features, and real-time updates.
 */

class ContentManager {
    constructor() {
        this.autoSaveTimer = null;
        this.autoSaveEnabled = true;
        this.lastSaveTime = null;
        this.postId = null;
        this.isDirty = false;
        this.collaborators = new Map();
        this.init();
    }

    init() {
        this.setupAutoSave();
        this.setupCollaboration();
        this.setupVersionComparison();
        this.setupBulkActions();
        this.setupScheduling();
        this.setupNotifications();
    }

    // Auto-save functionality
    setupAutoSave() {
        const form = document.getElementById('postForm');
        if (!form) return;

        const titleField = form.querySelector('#title');
        const contentField = form.querySelector('#contentTextarea');
        const autoSaveCheckbox = form.querySelector('#auto_save_enabled');
        const saveStatus = document.getElementById('autoSaveStatus');

        // Get post ID from form data if exists
        this.postId = form.dataset.postId || null;

        // Toggle auto-save
        if (autoSaveCheckbox) {
            autoSaveCheckbox.addEventListener('change', (e) => {
                this.autoSaveEnabled = e.target.checked;
                if (this.autoSaveEnabled) {
                    this.startAutoSave();
                    this.updateStatus('Auto-save enabled');
                } else {
                    this.stopAutoSave();
                    this.updateStatus('Auto-save disabled');
                }
            });
        }

        // Start auto-save on input
        [titleField, contentField].forEach(field => {
            if (field) {
                field.addEventListener('input', () => {
                    this.isDirty = true;
                    this.startAutoSave();
                });
            }
        });

        // Initial auto-save setup
        if (this.autoSaveEnabled) {
            this.startAutoSave();
        }

        // Warn before leaving if there are unsaved changes
        window.addEventListener('beforeunload', (e) => {
            if (this.isDirty && this.autoSaveEnabled) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            }
        });
    }

    startAutoSave() {
        if (!this.autoSaveEnabled) return;

        this.stopAutoSave(); // Clear existing timer

        this.autoSaveTimer = setTimeout(() => {
            this.autoSave();
        }, 30000); // 30 seconds
    }

    stopAutoSave() {
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
            this.autoSaveTimer = null;
        }
    }

    async autoSave() {
        const form = document.getElementById('postForm');
        if (!form) return;

        const titleField = form.querySelector('#title');
        const contentField = form.querySelector('#contentTextarea');

        const data = {
            title: titleField?.value || '',
            content: contentField?.value || '',
            post_id: this.postId
        };

        try {
            const response = await fetch('/content/auto_save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': form.querySelector('input[name="csrf_token"]')?.value
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.lastSaveTime = new Date(result.saved_at);
                this.updateStatus(`Auto-saved at ${this.lastSaveTime.toLocaleTimeString()}`);
                
                // Update post ID if it's a new post
                if (result.post_id && !this.postId) {
                    this.postId = result.post_id;
                    form.dataset.postId = this.postId;
                }
                
                this.isDirty = false;
            } else {
                this.updateStatus(`Auto-save failed: ${result.error || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`Auto-save error: ${error.message}`, 'error');
        }
    }

    updateStatus(message, type = 'info') {
        const statusElement = document.getElementById('autoSaveStatus');
        if (!statusElement) return;

        const iconClass = type === 'error' ? 'fas fa-exclamation-triangle' : 'fas fa-info-circle';
        const textClass = type === 'error' ? 'text-danger' : 'text-muted';

        statusElement.innerHTML = `<small class="${textClass}"><i class="${iconClass}"></i> ${message}</small>`;
    }

    // Collaboration features
    setupCollaboration() {
        const collaborationForm = document.getElementById('collaborationForm');
        if (!collaborationForm) return;

        collaborationForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addCollaborator();
        });
    }

    async addCollaborator() {
        const form = document.getElementById('collaborationForm');
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                location.reload(); // Refresh to show new collaborator
            } else {
                const error = await response.text();
                this.showNotification('Failed to add collaborator', 'error');
            }
        } catch (error) {
            this.showNotification('Error adding collaborator', 'error');
        }
    }

    // Version comparison
    setupVersionComparison() {
        const compareForm = document.getElementById('versionCompareForm');
        if (!compareForm) return;

        compareForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.compareVersions();
        });
    }

    async compareVersions() {
        const form = document.getElementById('versionCompareForm');
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const html = await response.text();
                document.getElementById('comparisonResult').innerHTML = html;
            } else {
                this.showNotification('Failed to compare versions', 'error');
            }
        } catch (error) {
            this.showNotification('Error comparing versions', 'error');
        }
    }

    // Bulk actions
    setupBulkActions() {
        const bulkActionForm = document.getElementById('bulkActionForm');
        if (!bulkActionForm) return;

        // Handle checkbox selection
        const selectAllCheckbox = document.getElementById('selectAll');
        const postCheckboxes = document.querySelectorAll('input[name="post_ids"]');

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                postCheckboxes.forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                });
                this.updateBulkActionButton();
            });
        }

        postCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBulkActionButton();
            });
        });

        // Handle action changes
        const actionSelect = document.getElementById('action');
        if (actionSelect) {
            actionSelect.addEventListener('change', (e) => {
                this.toggleScheduledDateField(e.target.value);
            });
        }
    }

    updateBulkActionButton() {
        const form = document.getElementById('bulkActionForm');
        const submitButton = form.querySelector('button[type="submit"]');
        const selectedCount = document.querySelectorAll('input[name="post_ids"]:checked').length;

        submitButton.disabled = selectedCount === 0;
        submitButton.textContent = selectedCount > 0 ? 
            `Apply Action (${selectedCount} selected)` : 'Apply Action';
    }

    toggleScheduledDateField(action) {
        const scheduledDateField = document.getElementById('scheduled_date');
        if (scheduledDateField) {
            const container = scheduledDateField.closest('.form-group');
            container.style.display = action === 'schedule' ? 'block' : 'none';
        }
    }

    // Scheduling
    setupScheduling() {
        const isScheduledCheckbox = document.getElementById('is_scheduled');
        const schedulingOptions = document.getElementById('schedulingOptions');

        if (isScheduledCheckbox && schedulingOptions) {
            isScheduledCheckbox.addEventListener('change', (e) => {
                schedulingOptions.style.display = e.target.checked ? 'block' : 'none';
            });
        }
    }

    // Notifications
    setupNotifications() {
        // Initialize notification container if it doesn't exist
        if (!document.getElementById('notificationContainer')) {
            const container = document.createElement('div');
            container.id = 'notificationContainer';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Content search and filtering
    setupContentSearch() {
        const searchForm = document.getElementById('contentSearchForm');
        if (!searchForm) return;

        let searchTimeout;
        const searchInput = searchForm.querySelector('input[name="query"]');

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performSearch(e.target.value);
                }, 500);
            });
        }
    }

    async performSearch(query) {
        const searchForm = document.getElementById('contentSearchForm');
        if (!searchForm) return;

        const formData = new FormData(searchForm);
        formData.set('query', query);

        try {
            const response = await fetch('/content/search', {
                method: 'GET',
                body: formData
            });

            if (response.ok) {
                const html = await response.text();
                document.getElementById('searchResults').innerHTML = html;
            }
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    // Content analytics
    setupAnalytics() {
        const analyticsContainer = document.getElementById('analyticsContainer');
        if (!analyticsContainer) return;

        this.loadAnalyticsData();
    }

    async loadAnalyticsData() {
        const postId = analyticsContainer.dataset.postId;
        if (!postId) return;

        try {
            const response = await fetch(`/content/analytics/${postId}`);
            if (response.ok) {
                const data = await response.json();
                this.renderAnalytics(data);
            }
        } catch (error) {
            console.error('Analytics error:', error);
        }
    }

    renderAnalytics(data) {
        const container = document.getElementById('analyticsContainer');
        // Implementation would depend on the analytics visualization library
        container.innerHTML = `
            <div class="row">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5>Views</h5>
                            <h3>${data.view_count}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5>Engagement</h5>
                            <h3>${data.engagement_score}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5>Comments</h5>
                            <h3>${data.comment_count}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5>Upvotes</h5>
                            <h3>${data.upvote_count}</h3>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Content export
    setupExport() {
        const exportForm = document.getElementById('exportForm');
        if (!exportForm) return;

        exportForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.exportContent();
        });
    }

    async exportContent() {
        const form = document.getElementById('exportForm');
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `content_export_${Date.now()}.${formData.get('format_type')}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                this.showNotification('Export failed', 'error');
            }
        } catch (error) {
            this.showNotification('Export error', 'error');
        }
    }
}

// Initialize content manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.contentManager = new ContentManager();
});

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function truncateText(text, maxLength = 100) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Export for use in other scripts
window.ContentManager = ContentManager;
