// Push Notification Manager
class PushNotificationManager {
    constructor() {
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.subscription = null;
        this.isSubscribed = false;
        this.publicKey = 'BLj3Z1x9lKq7i8m9n0o1p2q3r4s5t6u7v8w9x0y1z2a3b4c5d6e7f8g9h0i1j2k3l'; // This should be your VAPID public key
        this.init();
    }

    async init() {
        if (!this.isSupported) {
            console.warn('Push notifications are not supported in this browser');
            return;
        }

        try {
            // Register service worker
            const registration = await navigator.serviceWorker.register('/static/js/service-worker.js');
            console.log('Service Worker registered:', registration);

            // Check existing subscription
            this.subscription = await registration.pushManager.getSubscription();
            this.isSubscribed = this.subscription !== null;

            // Update UI based on subscription status
            this.updateSubscriptionUI();

            // Setup message listener from service worker
            navigator.serviceWorker.addEventListener('message', (event) => {
                this.handleServiceWorkerMessage(event);
            });

        } catch (error) {
            console.error('Error initializing push notifications:', error);
        }
    }

    async subscribeToPush() {
        if (!this.isSupported) {
            throw new Error('Push notifications are not supported');
        }

        try {
            // Get service worker registration
            const registration = await navigator.serviceWorker.ready;

            // Subscribe to push notifications
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.publicKey)
            });

            console.log('Push subscription created:', subscription);

            // Send subscription to server
            await this.sendSubscriptionToServer(subscription);

            // Update state
            this.subscription = subscription;
            this.isSubscribed = true;
            this.updateSubscriptionUI();

            return subscription;

        } catch (error) {
            console.error('Error subscribing to push notifications:', error);
            throw error;
        }
    }

    async unsubscribeFromPush() {
        if (!this.subscription) {
            return;
        }

        try {
            // Unsubscribe from push
            await this.subscription.unsubscribe();
            console.log('Unsubscribed from push notifications');

            // Remove subscription from server
            await this.removeSubscriptionFromServer();

            // Update state
            this.subscription = null;
            this.isSubscribed = false;
            this.updateSubscriptionUI();

        } catch (error) {
            console.error('Error unsubscribing from push notifications:', error);
            throw error;
        }
    }

    async sendSubscriptionToServer(subscription) {
        try {
            const response = await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    subscription: subscription,
                    user_agent: navigator.userAgent
                })
            });

            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }

            const data = await response.json();
            console.log('Subscription sent to server:', data);

        } catch (error) {
            console.error('Error sending subscription to server:', error);
            throw error;
        }
    }

    async removeSubscriptionFromServer() {
        try {
            const response = await fetch('/api/push/unsubscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    subscription: this.subscription
                })
            });

            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }

            console.log('Subscription removed from server');

        } catch (error) {
            console.error('Error removing subscription from server:', error);
            throw error;
        }
    }

    async requestPermission() {
        if (!('Notification' in window)) {
            throw new Error('This browser does not support notifications');
        }

        if (Notification.permission === 'granted') {
            return true;
        }

        if (Notification.permission !== 'denied') {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        }

        return false;
    }

    async toggleSubscription() {
        try {
            // Request notification permission first
            const hasPermission = await this.requestPermission();
            if (!hasPermission) {
                throw new Error('Notification permission denied');
            }

            if (this.isSubscribed) {
                await this.unsubscribeFromPush();
                return false;
            } else {
                await this.subscribeToPush();
                return true;
            }

        } catch (error) {
            console.error('Error toggling subscription:', error);
            throw error;
        }
    }

    updateSubscriptionUI() {
        const toggleButton = document.getElementById('push-toggle');
        const statusText = document.getElementById('push-status');
        const settingsPanel = document.getElementById('push-settings');

        if (toggleButton) {
            toggleButton.textContent = this.isSubscribed ? 'Disable Push Notifications' : 'Enable Push Notifications';
            toggleButton.className = this.isSubscribed ? 'btn-secondary' : 'btn-primary';
        }

        if (statusText) {
            statusText.textContent = this.isSubscribed ? 'Push notifications are enabled' : 'Push notifications are disabled';
        }

        if (settingsPanel) {
            settingsPanel.style.display = this.isSubscribed ? 'block' : 'none';
        }
    }

    handleServiceWorkerMessage(event) {
        const { type, data } = event.data;

        switch (type) {
            case 'NOTIFICATION_CLICKED':
                this.handleNotificationClick(data);
                break;
            case 'NOTIFICATION_DISMISSED':
                this.handleNotificationDismissed(data);
                break;
            case 'SUBSCRIPTION_UPDATED':
                this.handleSubscriptionUpdated(data);
                break;
            default:
                console.log('Unknown message type:', type);
        }
    }

    handleNotificationClick(data) {
        console.log('Notification clicked:', data);
        
        // Track notification click analytics
        this.trackNotificationAction('click', data);
        
        // Optionally navigate to the notification URL
        if (data.url && !window.location.href.includes(data.url)) {
            window.location.href = data.url;
        }
    }

    handleNotificationDismissed(data) {
        console.log('Notification dismissed:', data);
        
        // Track notification dismissal analytics
        this.trackNotificationAction('dismiss', data);
    }

    handleSubscriptionUpdated(data) {
        console.log('Subscription updated:', data);
        
        // Update local state if server changed subscription
        if (data.subscription) {
            this.subscription = data.subscription;
            this.isSubscribed = true;
        } else {
            this.subscription = null;
            this.isSubscribed = false;
        }
        
        this.updateSubscriptionUI();
    }

    async trackNotificationAction(action, data) {
        try {
            await fetch('/api/notifications/track', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    action: action,
                    notification_id: data.notification_id,
                    timestamp: Date.now(),
                    user_agent: navigator.userAgent
                })
            });
        } catch (error) {
            console.error('Error tracking notification action:', error);
        }
    }

    // Utility method to convert VAPID key
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }

    // Check subscription status
    async checkSubscriptionStatus() {
        try {
            const response = await fetch('/api/push/status');
            if (response.ok) {
                const data = await response.json();
                return data.subscribed;
            }
        } catch (error) {
            console.error('Error checking subscription status:', error);
        }
        return false;
    }

    // Update subscription preferences
    async updatePreferences(preferences) {
        try {
            const response = await fetch('/api/push/preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(preferences)
            });

            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error('Error updating push preferences:', error);
            throw error;
        }
    }

    // Get subscription preferences
    async getPreferences() {
        try {
            const response = await fetch('/api/push/preferences');
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error getting push preferences:', error);
        }
        return {};
    }

    // Test push notification
    async sendTestNotification() {
        if (!this.isSubscribed) {
            throw new Error('Not subscribed to push notifications');
        }

        try {
            const response = await fetch('/api/push/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error('Error sending test notification:', error);
            throw error;
        }
    }
}

// Initialize push notification manager
document.addEventListener('DOMContentLoaded', () => {
    window.pushNotificationManager = new PushNotificationManager();
    
    // Add event listeners for push notification controls
    const toggleButton = document.getElementById('push-toggle');
    if (toggleButton) {
        toggleButton.addEventListener('click', async () => {
            try {
                const isSubscribed = await window.pushNotificationManager.toggleSubscription();
                const message = isSubscribed ? 
                    'Push notifications enabled!' : 
                    'Push notifications disabled.';
                
                // Show feedback message
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-success';
                alertDiv.textContent = message;
                alertDiv.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1000;
                    padding: 1rem;
                    border-radius: 5px;
                `;
                document.body.appendChild(alertDiv);
                
                setTimeout(() => alertDiv.remove(), 3000);
                
            } catch (error) {
                console.error('Error toggling push notifications:', error);
                
                // Show error message
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-error';
                alertDiv.textContent = error.message;
                alertDiv.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1000;
                    padding: 1rem;
                    border-radius: 5px;
                    background: #ff4444;
                    color: white;
                `;
                document.body.appendChild(alertDiv);
                
                setTimeout(() => alertDiv.remove(), 3000);
            }
        });
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PushNotificationManager;
}
