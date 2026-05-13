// Service Worker for Push Notifications
const CACHE_NAME = 'autobot-forum-v1';
const NOTIFICATION_CACHE_NAME = 'notifications-v1';

// Files to cache for offline functionality
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/notifications/',
    '/static/images/favicon.ico'
];

// Install event - cache resources
self.addEventListener('install', event => {
    console.log('Service Worker: Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Caching files');
                return cache.addAll(urlsToCache);
            })
            .then(() => {
                console.log('Service Worker: Installation complete');
                return self.skipWaiting();
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activating...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME && cacheName !== NOTIFICATION_CACHE_NAME) {
                        console.log('Service Worker: Clearing old cache');
                        return caches.delete(cacheName);
                    }
                })
            );
        })
        .then(() => {
            console.log('Service Worker: Activation complete');
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version or fetch from network
                return response || fetch(event.request);
            })
    );
});

// Push event - handle push notifications
self.addEventListener('push', event => {
    console.log('Service Worker: Push received');
    
    let notificationData = {
        title: 'AutoBot Solutions Forum',
        body: 'You have a new notification',
        icon: '/static/images/favicon.ico',
        badge: '/static/images/badge.png',
        tag: 'autobot-notification',
        data: {
            url: '/notifications/',
            timestamp: Date.now()
        },
        actions: [
            {
                action: 'view',
                title: 'View Notification'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ],
        vibrate: [200, 100, 200],
        requireInteraction: true,
        silent: false
    };

    if (event.data) {
        try {
            const pushData = event.data.json();
            notificationData = {
                ...notificationData,
                ...pushData,
                title: pushData.title || notificationData.title,
                body: pushData.content || pushData.body || notificationData.body,
                data: {
                    ...notificationData.data,
                    ...pushData.data
                }
            };
        } catch (e) {
            console.error('Service Worker: Error parsing push data', e);
            // Fallback to text data
            notificationData.body = event.data.text() || notificationData.body;
        }
    }

    // Show notification
    event.waitUntil(
        self.registration.showNotification(notificationData.title, notificationData)
    );
});

// Notification click event
self.addEventListener('notificationclick', event => {
    console.log('Service Worker: Notification clicked');
    
    event.notification.close();

    if (event.action === 'dismiss') {
        // User dismissed the notification
        return;
    }

    // Handle notification click
    event.waitUntil(
        clients.matchAll().then(clientList => {
            // Check if a tab is already open
            for (const client of clientList) {
                if (client.url === event.notification.data.url && 'focus' in client) {
                    return client.focus();
                }
            }
            
            // Open new tab if none is open
            if (clients.openWindow) {
                return clients.openWindow(event.notification.data.url || '/notifications/');
            }
        })
    );
});

// Notification close event
self.addEventListener('notificationclose', event => {
    console.log('Service Worker: Notification closed');
    
    // Optionally track notification dismissal
    const notificationData = event.notification.data;
    if (notificationData && notificationData.id) {
        // Send analytics to server
        fetch('/api/notifications/dismissed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                notification_id: notificationData.id,
                timestamp: Date.now()
            })
        }).catch(err => {
            console.error('Service Worker: Error tracking notification dismissal', err);
        });
    }
});

// Background sync for offline notification actions
self.addEventListener('sync', event => {
    console.log('Service Worker: Background sync', event.tag);
    
    if (event.tag === 'notification-sync') {
        event.waitUntil(
            // Sync pending notification actions
            syncNotificationActions()
        );
    }
});

// Periodic sync for checking notifications
self.addEventListener('periodicsync', event => {
    console.log('Service Worker: Periodic sync', event.tag);
    
    if (event.tag === 'notification-check') {
        event.waitUntil(
            // Check for new notifications periodically
            checkForNotifications()
        );
    }
});

// Helper functions
async function syncNotificationActions() {
    try {
        // Get pending actions from IndexedDB
        const pendingActions = await getPendingActions();
        
        for (const action of pendingActions) {
            try {
                await fetch(action.url, {
                    method: action.method,
                    headers: action.headers,
                    body: action.body
                });
                
                // Remove successful action from pending
                await removePendingAction(action.id);
            } catch (error) {
                console.error('Service Worker: Failed to sync action', error);
            }
        }
    } catch (error) {
        console.error('Service Worker: Error in syncNotificationActions', error);
    }
}

async function checkForNotifications() {
    try {
        const response = await fetch('/api/notifications/check', {
            headers: {
                'Cache-Control': 'no-cache'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.has_new && data.notifications) {
                // Show notifications for new items
                for (const notification of data.notifications) {
                    self.registration.showNotification(notification.title, {
                        body: notification.content,
                        icon: '/static/images/favicon.ico',
                        tag: `notification-${notification.id}`,
                        data: {
                            url: notification.link || '/notifications/',
                            id: notification.id
                        }
                    });
                }
            }
        }
    } catch (error) {
        console.error('Service Worker: Error checking notifications', error);
    }
}

// IndexedDB helpers for offline storage
function getPendingActions() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('NotificationActions', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['actions'], 'readonly');
            const store = transaction.objectStore('actions');
            const getRequest = store.getAll();
            
            getRequest.onerror = () => reject(getRequest.error);
            getRequest.onsuccess = () => resolve(getRequest.result || []);
        };
        
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains('actions')) {
                db.createObjectStore('actions', { keyPath: 'id' });
            }
        };
    });
}

function removePendingAction(actionId) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('NotificationActions', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['actions'], 'readwrite');
            const store = transaction.objectStore('actions');
            const deleteRequest = store.delete(actionId);
            
            deleteRequest.onerror = () => reject(deleteRequest.error);
            deleteRequest.onsuccess = () => resolve();
        };
    });
}

// Message handling from main thread
self.addEventListener('message', event => {
    console.log('Service Worker: Message received', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'NOTIFICATION_ACTION') {
        // Handle notification actions from main thread
        handleNotificationAction(event.data);
    }
});

function handleNotificationAction(data) {
    const { action, notificationId, timestamp } = data;
    
    // Store action for background sync if offline
    storeNotificationAction({
        id: `${notificationId}-${timestamp}`,
        action,
        notificationId,
        timestamp,
        url: `/api/notifications/${notificationId}/${action}`,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ timestamp })
    });
}

function storeNotificationAction(action) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('NotificationActions', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['actions'], 'readwrite');
            const store = transaction.objectStore('actions');
            const addRequest = store.add(action);
            
            addRequest.onerror = () => reject(addRequest.error);
            addRequest.onsuccess = () => resolve();
        };
        
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains('actions')) {
                db.createObjectStore('actions', { keyPath: 'id' });
            }
        };
    });
}

console.log('Service Worker: Loaded');
