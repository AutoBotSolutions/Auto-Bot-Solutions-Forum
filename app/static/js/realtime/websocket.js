/**
 * WebSocket Client for Real-time Features
 * 
 * This JavaScript file handles the client-side WebSocket functionality for real-time features including:
 * - Live comment notifications
 * - Real-time vote count updates
 * - Online user presence indicators
 * - Real-time typing indicators
 */

class RealtimeWebSocket {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.currentPostId = null;
        this.typingTimer = null;
        this.typingTimeout = 5000; // Stop typing indicator after 5 seconds of inactivity
        
        this.eventHandlers = {
            'connection_established': [],
            'comment_notification': [],
            'vote_update': [],
            'user_status': [],
            'typing_indicator': [],
            'notification': [],
            'system_message': [],
            'online_users': [],
            'error': []
        };
        
        this.init();
    }
    
    init() {
        if (typeof io === 'undefined') {
            console.error('Socket.IO not loaded');
            return;
        }
        
        this.connect();
    }
    
    connect() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true
            });
            
            this.setupEventListeners();
            
        } catch (error) {
            console.error('Failed to connect to WebSocket:', error);
            this.handleReconnect();
        }
    }
    
    setupEventListeners() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.connected = true;
            this.reconnectAttempts = 0;
            
            // Join current post room if we're on a post page
            if (this.currentPostId) {
                this.joinPost(this.currentPostId);
            }
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket disconnected:', reason);
            this.connected = false;
            
            if (reason === 'io server disconnect') {
                // Server disconnected, don't reconnect automatically
                this.handleReconnect();
            }
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.handleReconnect();
        });
        
        // Application events
        this.socket.on('connection_established', (data) => {
            console.log('Connection established:', data);
            this.emit('connection_established', data);
        });
        
        this.socket.on('comment_notification', (data) => {
            console.log('New comment notification:', data);
            this.handleNewComment(data);
            this.emit('comment_notification', data);
        });
        
        this.socket.on('vote_update', (data) => {
            console.log('Vote update:', data);
            this.handleVoteUpdate(data);
            this.emit('vote_update', data);
        });
        
        this.socket.on('user_status', (data) => {
            console.log('User status update:', data);
            this.handleUserStatus(data);
            this.emit('user_status', data);
        });
        
        this.socket.on('typing_indicator', (data) => {
            console.log('Typing indicator:', data);
            this.handleTypingIndicator(data);
            this.emit('typing_indicator', data);
        });
        
        this.socket.on('notification', (data) => {
            console.log('Notification:', data);
            this.handleNotification(data);
            this.emit('notification', data);
        });
        
        this.socket.on('system_message', (data) => {
            console.log('System message:', data);
            this.handleSystemMessage(data);
            this.emit('system_message', data);
        });
        
        this.socket.on('online_users', (data) => {
            console.log('Online users update:', data);
            this.handleOnlineUsers(data);
            this.emit('online_users', data);
        });
        
        this.socket.on('error', (data) => {
            console.error('WebSocket error:', data);
            this.emit('error', data);
        });
        
        this.socket.on('joined_post', (data) => {
            console.log('Joined post room:', data);
        });
        
        this.socket.on('left_post', (data) => {
            console.log('Left post room:', data);
        });
        
        this.socket.on('typing_users', (data) => {
            console.log('Typing users update:', data);
            this.updateTypingUsers(data.typing_users);
        });
    }
    
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnect attempts reached');
            this.emit('error', { message: 'Failed to connect after multiple attempts' });
        }
    }
    
    // Event handling methods
    handleNewComment(data) {
        if (data.comment && data.comment.post_id === this.currentPostId) {
            this.addCommentToPage(data.comment);
        }
        
        // Show notification if it's not the current user's comment
        if (data.comment && data.comment.author && 
            !this.isCurrentUser(data.comment.author.username)) {
            this.showCommentNotification(data.comment);
        }
    }
    
    handleVoteUpdate(data) {
        if (data.content_type === 'post' && data.content_id === this.currentPostId) {
            this.updatePostVotes(data.vote_data);
        } else if (data.content_type === 'comment') {
            this.updateCommentVotes(data.content_id, data.vote_data);
        }
    }
    
    handleUserStatus(data) {
        this.updateUserOnlineStatus(data.user_id, data.is_online);
    }
    
    handleTypingIndicator(data) {
        if (data.post_id === this.currentPostId) {
            this.updateTypingIndicator(data);
        }
    }
    
    handleNotification(data) {
        this.showNotification(data.notification);
    }
    
    handleSystemMessage(data) {
        this.showSystemMessage(data.message, data.message_type);
    }
    
    handleOnlineUsers(data) {
        this.updateOnlineUsersList(data.users);
    }
    
    // UI update methods
    addCommentToPage(comment) {
        const commentsContainer = document.querySelector('.comments-list');
        if (!commentsContainer) return;
        
        const commentElement = this.createCommentElement(comment);
        commentsContainer.appendChild(commentElement);
        
        // Scroll to the new comment
        commentElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
        
        // Update comment count
        this.updateCommentCount(1);
    }
    
    createCommentElement(comment) {
        const div = document.createElement('div');
        div.className = 'comment new-comment';
        div.innerHTML = `
            <div class="comment-header">
                <strong>${this.escapeHtml(comment.author.username)}</strong>
                <span class="comment-time">${this.formatTime(comment.created_at)}</span>
            </div>
            <div class="comment-content">
                ${this.formatContent(comment.content)}
            </div>
            <div class="comment-actions">
                <button class="vote-btn upvote" onclick="voteComment(${comment.id}, 1)">
                    <i class="fas fa-arrow-up"></i> <span class="vote-count">0</span>
                </button>
                <button class="vote-btn downvote" onclick="voteComment(${comment.id}, -1)">
                    <i class="fas fa-arrow-down"></i> <span class="vote-count">0</span>
                </button>
            </div>
        `;
        
        // Add animation
        setTimeout(() => div.classList.add('show'), 10);
        
        return div;
    }
    
    updatePostVotes(voteData) {
        const upvoteElement = document.querySelector('.post-upvotes');
        const downvoteElement = document.querySelector('.post-downvotes');
        
        if (upvoteElement) upvoteElement.textContent = voteData.upvotes;
        if (downvoteElement) downvoteElement.textContent = voteData.downvotes;
        
        // Update vote buttons state
        this.updateVoteButtonState('post', voteData.post_id, voteData.vote_type);
    }
    
    updateCommentVotes(commentId, voteData) {
        const commentElement = document.querySelector(`.comment[data-comment-id="${commentId}"]`);
        if (!commentElement) return;
        
        const upvoteElement = commentElement.querySelector('.upvote .vote-count');
        const downvoteElement = commentElement.querySelector('.downvote .vote-count');
        
        if (upvoteElement) upvoteElement.textContent = voteData.upvotes;
        if (downvoteElement) downvoteElement.textContent = voteData.downvotes;
        
        // Update vote buttons state
        this.updateVoteButtonState('comment', commentId, voteData.vote_type);
    }
    
    updateVoteButtonState(contentType, contentId, voteType) {
        // This would update the visual state of vote buttons
        // Implementation depends on your specific UI
    }
    
    updateUserOnlineStatus(userId, isOnline) {
        const userElements = document.querySelectorAll(`[data-user-id="${userId}"]`);
        userElements.forEach(element => {
            const indicator = element.querySelector('.online-indicator');
            if (indicator) {
                if (isOnline) {
                    indicator.classList.add('online');
                    indicator.title = 'Online';
                } else {
                    indicator.classList.remove('online');
                    indicator.title = 'Offline';
                }
            }
        });
    }
    
    updateTypingIndicator(data) {
        const typingContainer = document.querySelector('.typing-indicators');
        if (!typingContainer) return;
        
        if (data.is_typing) {
            this.addTypingIndicator(data.username);
        } else {
            this.removeTypingIndicator(data.username);
        }
    }
    
    addTypingIndicator(username) {
        const typingContainer = document.querySelector('.typing-indicators');
        if (!typingContainer) return;
        
        // Remove existing indicator for this user
        this.removeTypingIndicator(username);
        
        const indicator = document.createElement('span');
        indicator.className = 'typing-indicator';
        indicator.setAttribute('data-username', username);
        indicator.innerHTML = `<strong>${this.escapeHtml(username)}</strong> is typing...`;
        
        typingContainer.appendChild(indicator);
    }
    
    removeTypingIndicator(username) {
        const indicator = document.querySelector(`.typing-indicator[data-username="${username}"]`);
        if (indicator) {
            indicator.remove();
        }
    }
    
    updateTypingUsers(typingUsers) {
        const typingContainer = document.querySelector('.typing-indicators');
        if (!typingContainer) return;
        
        // Clear existing indicators
        typingContainer.innerHTML = '';
        
        // Add current typing users
        typingUsers.forEach(user => {
            this.addTypingIndicator(user.username);
        });
    }
    
    showCommentNotification(comment) {
        const message = `${comment.author.username} commented: ${this.truncateText(comment.content, 50)}`;
        this.showNotification({
            type: 'comment',
            content: message,
            link: `/forum/post/${comment.post_id}#comment-${comment.id}`
        });
    }
    
    showNotification(notification) {
        // Use browser notification API if available
        if ('Notification' in window && Notification.permission === 'granted') {
            const browserNotification = new Notification('Forum Notification', {
                body: notification.content,
                icon: '/static/images/favicon.ico'
            });
            
            if (notification.link) {
                browserNotification.onclick = () => {
                    window.location.href = notification.link;
                };
            }
        }
        
        // Show in-app notification
        this.showInAppNotification(notification);
    }
    
    showInAppNotification(notification) {
        const notificationContainer = document.querySelector('.notifications-container');
        if (!notificationContainer) return;
        
        const notificationElement = document.createElement('div');
        notificationElement.className = 'notification';
        notificationElement.innerHTML = `
            <div class="notification-content">
                <p>${this.escapeHtml(notification.content)}</p>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        notificationContainer.appendChild(notificationElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notificationElement.remove();
        }, 5000);
    }
    
    showSystemMessage(message, type = 'info') {
        const messageContainer = document.querySelector('.system-messages');
        if (!messageContainer) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `system-message ${type}`;
        messageElement.textContent = message;
        
        messageContainer.appendChild(messageElement);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            messageElement.remove();
        }, 10000);
    }
    
    updateOnlineUsersList(users) {
        const onlineUsersContainer = document.querySelector('.online-users-list');
        if (!onlineUsersContainer) return;
        
        onlineUsersContainer.innerHTML = '';
        
        users.forEach(user => {
            const userElement = document.createElement('div');
            userElement.className = 'online-user';
            userElement.setAttribute('data-user-id', user.user_id);
            userElement.innerHTML = `
                <span class="online-indicator online" title="Online"></span>
                <span class="username">${this.escapeHtml(user.username)}</span>
            `;
            
            onlineUsersContainer.appendChild(userElement);
        });
        
        // Update online count
        const onlineCount = document.querySelector('.online-users-count');
        if (onlineCount) {
            onlineCount.textContent = users.length;
        }
    }
    
    updateCommentCount(delta) {
        const countElement = document.querySelector('.comment-count');
        if (countElement) {
            const currentCount = parseInt(countElement.textContent) || 0;
            countElement.textContent = currentCount + delta;
        }
    }
    
    // Public API methods
    joinPost(postId) {
        if (this.connected && postId) {
            this.currentPostId = postId;
            this.socket.emit('join_post', { post_id: postId });
        }
    }
    
    leavePost() {
        if (this.connected && this.currentPostId) {
            this.socket.emit('leave_post', { post_id: this.currentPostId });
            this.currentPostId = null;
        }
    }
    
    startTyping(postId) {
        if (this.connected && postId) {
            this.socket.emit('start_typing', { post_id: postId });
            
            // Clear existing timer
            if (this.typingTimer) {
                clearTimeout(this.typingTimer);
            }
            
            // Set timer to stop typing indicator
            this.typingTimer = setTimeout(() => {
                this.stopTyping(postId);
            }, this.typingTimeout);
        }
    }
    
    stopTyping(postId) {
        if (this.connected && postId) {
            this.socket.emit('stop_typing', { post_id: postId });
            
            // Clear timer
            if (this.typingTimer) {
                clearTimeout(this.typingTimer);
                this.typingTimer = null;
            }
        }
    }
    
    sendNotification(notification) {
        if (this.connected) {
            this.socket.emit('notification', notification);
        }
    }
    
    // Event system
    on(event, callback) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].push(callback);
        }
    }
    
    emit(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(callback => callback(data));
        }
    }
    
    // Utility methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // Less than 1 minute
            return 'just now';
        } else if (diff < 3600000) { // Less than 1 hour
            return Math.floor(diff / 60000) + ' minutes ago';
        } else if (diff < 86400000) { // Less than 1 day
            return Math.floor(diff / 3600000) + ' hours ago';
        } else {
            return date.toLocaleDateString();
        }
    }
    
    formatContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    isCurrentUser(username) {
        // This should check against the current logged-in user
        // Implementation depends on how you store the current user info
        return false; // Placeholder
    }
    
    // Cleanup
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.connected = false;
        
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
            this.typingTimer = null;
        }
    }
}

// Initialize the WebSocket connection
let realtimeWebSocket = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    // Initialize WebSocket
    realtimeWebSocket = new RealtimeWebSocket();
    
    // Auto-join post room if we're on a post page
    const postElement = document.querySelector('[data-post-id]');
    if (postElement) {
        const postId = parseInt(postElement.getAttribute('data-post-id'));
        realtimeWebSocket.joinPost(postId);
    }
    
    // Setup typing indicator for comment form
    const commentTextarea = document.querySelector('#comment-content');
    if (commentTextarea) {
        let typingTimer = null;
        
        commentTextarea.addEventListener('input', function() {
            const postId = parseInt(document.querySelector('[data-post-id]').getAttribute('data-post-id'));
            
            if (typingTimer) {
                clearTimeout(typingTimer);
            }
            
            realtimeWebSocket.startTyping(postId);
            
            typingTimer = setTimeout(() => {
                realtimeWebSocket.stopTyping(postId);
            }, 3000);
        });
        
        commentTextarea.addEventListener('blur', function() {
            const postId = parseInt(document.querySelector('[data-post-id]').getAttribute('data-post-id'));
            realtimeWebSocket.stopTyping(postId);
        });
    }
});

// Global functions for external access
window.realtimeWebSocket = realtimeWebSocket;

// Helper functions for integration
window.joinPostRoom = function(postId) {
    if (realtimeWebSocket) {
        realtimeWebSocket.joinPost(postId);
    }
};

window.leavePostRoom = function() {
    if (realtimeWebSocket) {
        realtimeWebSocket.leavePost();
    }
};

window.startTypingIndicator = function(postId) {
    if (realtimeWebSocket) {
        realtimeWebSocket.startTyping(postId);
    }
};

window.stopTypingIndicator = function(postId) {
    if (realtimeWebSocket) {
        realtimeWebSocket.stopTyping(postId);
    }
};
