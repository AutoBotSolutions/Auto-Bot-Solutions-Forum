/**
 * Enhanced Voting and Reputation System JavaScript
 * 
 * This file provides client-side functionality for the enhanced voting and reputation system,
 * including voting interfaces, real-time updates, and reputation visualization.
 */

class ReputationVotingSystem {
    constructor() {
        this.voteModal = null;
        this.currentTarget = null;
        this.votingInProgress = false;
        this.reputationData = new Map();
        this.init();
    }

    init() {
        this.setupVoteModals();
        this.setupVotingButtons();
        this.setupReputationBadges();
        this.setupRealTimeUpdates();
        this.setupTooltips();
        this.setupProgressBars();
    }

    setupVoteModals() {
        // Initialize Bootstrap modal
        this.voteModal = new bootstrap.Modal(document.getElementById('voteModal'));
        
        // Handle modal events
        const modal = document.getElementById('voteModal');
        if (modal) {
            modal.addEventListener('show.bs.modal', (event) => {
                this.handleModalShow(event);
            });
            
            modal.addEventListener('hidden.bs.modal', (event) => {
                this.handleModalHidden(event);
            });
        }
    }

    setupVotingButtons() {
        // Setup voting buttons on posts and comments
        document.addEventListener('click', (event) => {
            if (event.target.matches('.vote-button')) {
                event.preventDefault();
                this.handleVoteClick(event.target);
            }
        });

        // Setup quick vote buttons (upvote/downvote without modal)
        document.addEventListener('click', (event) => {
            if (event.target.matches('.quick-vote')) {
                event.preventDefault();
                this.handleQuickVote(event.target);
            }
        });
    }

    setupReputationBadges() {
        // Enhance reputation badges with tooltips and animations
        document.querySelectorAll('.reputation-badge').forEach(badge => {
            this.enhanceReputationBadge(badge);
        });
    }

    setupRealTimeUpdates() {
        // Setup real-time updates for vote counts and reputation
        if (typeof io !== 'undefined') {
            this.setupWebSocketUpdates();
        } else {
            // Fallback to periodic updates
            this.setupPeriodicUpdates();
        }
    }

    setupTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    setupProgressBars() {
        // Animate progress bars on page load
        document.querySelectorAll('.progress-bar').forEach(bar => {
            const progress = bar.getAttribute('data-progress');
            if (progress) {
                setTimeout(() => {
                    bar.style.width = progress + '%';
                    bar.classList.add('progress-bar-animated');
                }, 100);
            }
        });
    }

    handleVoteClick(button) {
        if (this.votingInProgress) {
            this.showNotification('Voting in progress, please wait...', 'warning');
            return;
        }

        const targetType = button.getAttribute('data-target-type');
        const targetId = button.getAttribute('data-target-id');
        
        if (!targetType || !targetId) {
            console.error('Missing target information');
            return;
        }

        this.currentTarget = { type: targetType, id: parseInt(targetId) };
        this.openVoteModal(button);
    }

    handleQuickVote(button) {
        if (this.votingInProgress) {
            this.showNotification('Voting in progress, please wait...', 'warning');
            return;
        }

        const voteType = button.getAttribute('data-vote-type');
        const targetType = button.getAttribute('data-target-type');
        const targetId = button.getAttribute('data-target-id');
        
        if (!voteType || !targetType || !targetId) {
            console.error('Missing voting information');
            return;
        }

        this.castQuickVote(voteType, targetType, parseInt(targetId), button);
    }

    openVoteModal(button) {
        const modalUrl = button.getAttribute('data-modal-url') || 
                        `/reputation/vote/${this.currentTarget.type}/${this.currentTarget.id}`;
        
        // Load modal content via AJAX
        fetch(modalUrl)
            .then(response => response.text())
            .then(html => {
                const modalContainer = document.getElementById('voteModal');
                if (modalContainer) {
                    // Update modal content
                    const modalBody = modalContainer.querySelector('.modal-body');
                    if (modalBody) {
                        // Parse the HTML and extract the body content
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const newBody = doc.querySelector('.modal-body');
                        if (newBody) {
                            modalBody.innerHTML = newBody.innerHTML;
                        }
                    }
                    
                    // Show modal
                    this.voteModal.show();
                    
                    // Reinitialize tooltips in modal
                    this.setupTooltips();
                }
            })
            .catch(error => {
                console.error('Error loading vote modal:', error);
                this.showNotification('Error loading voting interface', 'error');
            });
    }

    handleModalShow(event) {
        const button = event.relatedTarget;
        const targetType = button.getAttribute('data-target-type');
        const targetId = button.getAttribute('data-target-id');
        
        this.currentTarget = { type: targetType, id: parseInt(targetId) };
    }

    handleModalHidden(event) {
        // Reset form when modal is hidden
        const form = event.target.querySelector('form');
        if (form) {
            form.reset();
        }
        
        this.currentTarget = null;
    }

    castQuickVote(voteType, targetType, targetId, button) {
        this.votingInProgress = true;
        
        // Show loading state
        const originalContent = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;

        const formData = new FormData();
        formData.append('vote_type', voteType);
        formData.append('target_type', targetType);
        formData.append('target_id', targetId);

        fetch('/reputation/vote', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.handleVoteSuccess(data, targetType, targetId);
                this.showNotification('Vote cast successfully!', 'success');
            } else {
                this.showNotification(data.error || 'Failed to cast vote', 'error');
            }
        })
        .catch(error => {
            console.error('Error casting vote:', error);
            this.showNotification('Error casting vote', 'error');
        })
        .finally(() => {
            // Restore button state
            button.innerHTML = originalContent;
            button.disabled = false;
            this.votingInProgress = false;
        });
    }

    handleVoteSuccess(data, targetType, targetId) {
        // Update vote counts
        this.updateVoteCounts(targetType, targetId, data.target_upvotes, data.target_downvotes);
        
        // Update user reputation if needed
        if (data.reputation_impact) {
            this.updateCurrentUserReputation();
        }
        
        // Update voting button states
        this.updateVotingButtons(targetType, targetId, data.vote_type);
        
        // Trigger custom event
        const event = new CustomEvent('voteCast', {
            detail: {
                targetType: targetType,
                targetId: targetId,
                voteType: data.vote_type,
                voteWeight: data.vote_weight
            }
        });
        document.dispatchEvent(event);
    }

    updateVoteCounts(targetType, targetId, upvotes, downvotes) {
        // Find and update vote count elements
        const upvoteElement = document.querySelector(`[data-target-type="${targetType}"][data-target-id="${targetId}"] .upvote-count`);
        const downvoteElement = document.querySelector(`[data-target-type="${targetType}"][data-target-id="${targetId}"] .downvote-count`);
        
        if (upvoteElement) {
            upvoteElement.textContent = upvotes;
            this.animateNumber(upvoteElement, upvotes);
        }
        
        if (downvoteElement) {
            downvoteElement.textContent = downvotes;
            this.animateNumber(downvoteElement, downvotes);
        }
    }

    updateVotingButtons(targetType, targetId, voteType) {
        const container = document.querySelector(`[data-target-type="${targetType}"][data-target-id="${targetId}"]`);
        if (!container) return;

        // Update button states to reflect current vote
        const upvoteButton = container.querySelector('.vote-upvote');
        const downvoteButton = container.querySelector('.vote-downvote');
        
        if (voteType === 'upvote') {
            upvoteButton?.classList.add('active', 'btn-success');
            upvoteButton?.classList.remove('btn-outline-success');
            downvoteButton?.classList.remove('active', 'btn-danger');
            downvoteButton?.classList.add('btn-outline-danger');
        } else if (voteType === 'downvote') {
            downvoteButton?.classList.add('active', 'btn-danger');
            downvoteButton?.classList.remove('btn-outline-danger');
            upvoteButton?.classList.remove('active', 'btn-success');
            upvoteButton?.classList.add('btn-outline-success');
        }
    }

    updateCurrentUserReputation() {
        // Fetch updated reputation data
        fetch('/reputation/api/reputation/' + this.getCurrentUserId())
            .then(response => response.json())
            .then(data => {
                this.reputationData.set(this.getCurrentUserId(), data);
                this.updateReputationDisplay(data);
            })
            .catch(error => {
                console.error('Error fetching reputation data:', error);
            });
    }

    updateReputationDisplay(reputationData) {
        // Update reputation score displays
        document.querySelectorAll('.reputation-score').forEach(element => {
            element.textContent = reputationData.reputation_score;
            this.animateNumber(element, reputationData.reputation_score);
        });
        
        // Update voting power displays
        document.querySelectorAll('.voting-power').forEach(element => {
            element.textContent = reputationData.voting_power.toFixed(2);
        });
        
        // Update reputation level badges
        document.querySelectorAll('.reputation-level').forEach(element => {
            element.textContent = reputationData.current_level;
        });
        
        // Update progress bars
        document.querySelectorAll('.reputation-progress').forEach(element => {
            const progress = (reputationData.level_progress * 100).toFixed(0);
            element.setAttribute('data-progress', progress);
            element.style.width = progress + '%';
        });
    }

    enhanceReputationBadge(badge) {
        // Add tooltip with reputation details
        const level = badge.getAttribute('data-level');
        const score = badge.getAttribute('data-score');
        const power = badge.getAttribute('data-power');
        
        const tooltipContent = `
            <strong>${level}</strong><br>
            Score: ${score}<br>
            Voting Power: ${power}
        `;
        
        badge.setAttribute('data-bs-toggle', 'tooltip');
        badge.setAttribute('data-bs-html', 'true');
        badge.setAttribute('title', tooltipContent);
        
        // Add hover animation
        badge.addEventListener('mouseenter', () => {
            badge.style.transform = 'scale(1.1)';
            badge.style.transition = 'transform 0.2s ease';
        });
        
        badge.addEventListener('mouseleave', () => {
            badge.style.transform = 'scale(1)';
        });
    }

    animateNumber(element, targetValue) {
        const startValue = parseInt(element.textContent) || 0;
        const duration = 500;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const currentValue = Math.floor(startValue + (targetValue - startValue) * progress);
            element.textContent = currentValue;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
        
        // Initialize Bootstrap alert
        const alert = new bootstrap.Alert(notification);
    }

    setupWebSocketUpdates() {
        // Setup WebSocket for real-time updates
        const socket = io();
        
        socket.on('vote_update', (data) => {
            this.handleRealTimeVoteUpdate(data);
        });
        
        socket.on('reputation_update', (data) => {
            this.handleRealTimeReputationUpdate(data);
        });
    }

    setupPeriodicUpdates() {
        // Fallback: Periodic updates every 30 seconds
        setInterval(() => {
            this.updateAllVoteCounts();
        }, 30000);
    }

    handleRealTimeVoteUpdate(data) {
        this.updateVoteCounts(data.target_type, data.target_id, data.upvotes, data.downvotes);
        
        // Show real-time notification
        if (data.user_id !== this.getCurrentUserId()) {
            this.showNotification(`${data.username} voted on a ${data.target_type}`, 'info');
        }
    }

    handleRealTimeReputationUpdate(data) {
        if (data.user_id === this.getCurrentUserId()) {
            this.updateReputationDisplay(data.reputation_data);
        }
    }

    updateAllVoteCounts() {
        // Update all visible vote counts
        document.querySelectorAll('.vote-container').forEach(container => {
            const targetType = container.getAttribute('data-target-type');
            const targetId = container.getAttribute('data-target-id');
            
            if (targetType && targetId) {
                this.fetchVoteCounts(targetType, parseInt(targetId));
            }
        });
    }

    fetchVoteCounts(targetType, targetId) {
        fetch(`/api/${targetType}/${targetId}/votes`)
            .then(response => response.json())
            .then(data => {
                this.updateVoteCounts(targetType, targetId, data.upvotes, data.downvotes);
            })
            .catch(error => {
                console.error('Error fetching vote counts:', error);
            });
    }

    getCurrentUserId() {
        // Get current user ID from page data or meta tag
        return document.body.getAttribute('data-user-id') || 
               document.querySelector('meta[name="user-id"]')?.getAttribute('content');
    }

    // Public API methods
    getReputationData(userId) {
        return this.reputationData.get(userId);
    }

    refreshReputationData(userId) {
        return fetch(`/reputation/api/reputation/${userId}`)
            .then(response => response.json())
            .then(data => {
                this.reputationData.set(userId, data);
                return data;
            });
    }

    openVoteModalForTarget(targetType, targetId) {
        this.currentTarget = { type: targetType, id: targetId };
        this.openVoteModal();
    }
}

// Initialize the voting system when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.reputationVotingSystem = new ReputationVotingSystem();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ReputationVotingSystem;
}
