# Notification System API Reference

## Overview

This document provides comprehensive API reference for the notification system endpoints, WebSocket events, and integration patterns. All endpoints require authentication and follow RESTful conventions.

**Base URL:** `http://localhost:5000`  
**WebSocket URL:** `ws://localhost:5003`  
**Authentication:** Bearer token or session-based  
**API Version:** v2.0 (Advanced Features Added)  
**Status:** ✅ Complete with All Advanced Features

## Push Notification API

### Subscribe to Push Notifications

Subscribe the current user to browser push notifications.

**Endpoint:** `POST /api/push/subscribe`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "endpoint": "https://fcm.googleapis.com/fcm/send/dRegV...",
    "keys": {
        "p256dh": "BMwdqMw...",
        "auth": "BwHP..."
    }
}
```

#### Response
```json
{
    "success": true,
    "message": "Successfully subscribed to push notifications",
    "subscription_id": "sub_123456789"
}
```

#### Error Responses
```json
{
    "error": "Invalid subscription data",
    "message": "Missing required fields: endpoint, keys"
}
```

### Unsubscribe from Push Notifications

Remove push notification subscription for the current user.

**Endpoint:** `POST /api/push/unsubscribe`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "endpoint": "https://fcm.googleapis.com/fcm/send/dRegV..."
}
```

#### Response
```json
{
    "success": true,
    "message": "Successfully unsubscribed from push notifications"
}
```

### Get Subscription Status

Retrieve current push notification subscription status and preferences.

**Endpoint:** `GET /api/push/status`  
**Authentication:** Required

#### Response
```json
{
    "subscribed": true,
    "endpoint": "https://fcm.googleapis.com/fcm/send/dRegV...",
    "preferences": {
        "enabled": true,
        "types": ["comment", "message", "system"],
        "quiet_hours": {
            "enabled": false,
            "start": "22:00",
            "end": "08:00"
        }
    },
    "subscription_date": "2026-05-12T10:30:00Z"
}
```

### Update Push Notification Preferences

Update user preferences for push notifications.

**Endpoint:** `GET/POST /api/push/preferences`  
**Authentication:** Required  
**Content-Type:** `application/json` (POST only)

#### GET Response
```json
{
    "preferences": {
        "enabled": true,
        "types": ["comment", "message", "system"],
        "frequency": "all",
        "quiet_hours": {
            "enabled": false,
            "start": "22:00",
            "end": "08:00"
        }
    }
}
```

#### POST Request Body
```json
{
    "enabled": true,
    "types": ["comment", "message"],
    "frequency": "important",
    "quiet_hours": {
        "enabled": true,
        "start": "22:00",
        "end": "08:00"
    }
}
```

#### POST Response
```json
{
    "success": true,
    "message": "Preferences updated successfully",
    "preferences": {
        "enabled": true,
        "types": ["comment", "message"],
        "frequency": "important",
        "quiet_hours": {
            "enabled": true,
            "start": "22:00",
            "end": "08:00"
        }
    }
}
```

### Send Test Push Notification

Send a test push notification to the current user (for development/testing).

**Endpoint:** `POST /api/push/test`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "title": "Test Notification",
    "body": "This is a test push notification",
    "data": {
        "url": "/notifications",
        "type": "test"
    }
}
```

#### Response
```json
{
    "success": true,
    "message": "Test notification sent successfully",
    "notification_id": "notif_123456"
}
```

### Cleanup Inactive Subscriptions

Remove inactive or invalid push notification subscriptions.

**Endpoint:** `POST /api/push/cleanup`  
**Authentication:** Required

#### Response
```json
{
    "success": true,
    "message": "Cleanup completed",
    "removed_count": 3,
    "removed_subscriptions": [
        "sub_123",
        "sub_456",
        "sub_789"
    ]
}
```

## Analytics API

### Get Delivery Analytics

Retrieve comprehensive delivery analytics for notifications.

**Endpoint:** `GET /api/analytics/notifications/delivery`  
**Authentication:** Required

#### Query Parameters
- `start_date` (optional): ISO date string (default: 30 days ago)
- `end_date` (optional): ISO date string (default: now)

#### Response
```json
{
    "summary": {
        "total_notifications": 1250,
        "read_notifications": 1180,
        "unread_notifications": 70,
        "read_rate": 94.4,
        "period": {
            "start_date": "2026-04-12T00:00:00Z",
            "end_date": "2026-05-12T00:00:00Z"
        }
    },
    "by_type": {
        "comment": 850,
        "message": 300,
        "system": 100
    },
    "daily_trends": [
        {
            "date": "2026-05-12",
            "total": 45,
            "read": 42,
            "read_rate": 93.3
        }
    ],
    "hourly_distribution": [
        {
            "hour": 14,
            "count": 125
        }
    ],
    "user_engagement": {
        "most_active": [
            {
                "user_id": 1,
                "username": "john_doe",
                "notification_count": 45
            }
        ],
        "highest_read_rates": [
            {
                "user_id": 2,
                "username": "jane_smith",
                "total_notifications": 30,
                "read_notifications": 30,
                "read_rate": 100.0
            }
        ]
    },
    "performance": {
        "engagement_rate": 68.5,
        "avg_time_to_read_hours": 2.5,
        "peak_activity_hours": [
            {
                "hour": 14,
                "count": 125,
                "percentage": 10.0
            }
        ],
        "delivery_success_rate": 98.5,
        "push_notification_opt_in_rate": 65.2
    }
}
```

### Get Notification Insights

Retrieve actionable insights and recommendations based on analytics data.

**Endpoint:** `GET /api/analytics/notifications/insights`  
**Authentication:** Required

#### Query Parameters
- `start_date` (optional): ISO date string
- `end_date` (optional): ISO date string

#### Response
```json
{
    "insights": [
        {
            "type": "warning",
            "title": "Low Read Rate",
            "description": "Only 45% of notifications are being read. Consider improving content relevance or timing.",
            "recommendation": "Review notification content and delivery timing"
        },
        {
            "type": "success",
            "title": "High Engagement",
            "description": "Excellent 94.4% read rate shows high user engagement.",
            "recommendation": "Maintain current notification strategy"
        }
    ],
    "summary": {
        "total_insights": 2,
        "critical": 1,
        "positive": 1,
        "informational": 0
    }
}
```

### Export Analytics Data

Export notification analytics data in various formats.

**Endpoint:** `GET /api/analytics/notifications/export`  
**Authentication:** Required

#### Query Parameters
- `format` (optional): `json` or `csv` (default: `json`)
- `start_date` (optional): ISO date string
- `end_date` (optional): ISO date string

#### Response (JSON format)
```json
{
    "summary": {
        "total_notifications": 1250,
        "read_rate": 94.4
    },
    "daily_trends": [...],
    "by_type": {...}
}
```

#### Response (CSV format)
```csv
date,total,read,read_rate
2026-05-12,45,42,93.3
2026-05-11,38,35,92.1
```

### Track Engagement Events

Track user engagement events with notifications.

**Endpoint:** `POST /api/analytics/notifications/track`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "notification_id": 123,
    "action": "viewed",
    "timestamp": "2026-05-12T10:30:00Z",
    "metadata": {
        "source": "websocket",
        "device": "desktop"
    }
}
```

#### Valid Actions
- `viewed` - User viewed the notification
- `clicked` - User clicked notification link
- `dismissed` - User dismissed notification
- `marked_read` - User marked as read

#### Response
```json
{
    "success": true,
    "message": "Event tracked successfully"
}
```

### Get Dashboard Data

Retrieve comprehensive dashboard data for notification analytics.

**Endpoint:** `GET /api/analytics/notifications/dashboard`  
**Authentication:** Required

#### Response
```json
{
    "period": {
        "start_date": "2026-04-12T00:00:00Z",
        "end_date": "2026-05-12T00:00:00Z",
        "days": 30
    },
    "summary": {
        "total_notifications": 1250,
        "read_rate": 94.4
    },
    "key_metrics": {
        "total_notifications": 1250,
        "read_rate": 94.4,
        "engagement_rate": 68.5,
        "delivery_success_rate": 98.5
    },
    "type_distribution": {
        "comment": 850,
        "message": 300,
        "system": 100
    },
    "daily_trends": [...],
    "performance": {...}
}
```

### Get Real-time Metrics

Retrieve current real-time notification metrics.

**Endpoint:** `GET /api/analytics/notifications/realtime`  
**Authentication:** Required

#### Response
```json
{
    "timestamp": "2026-05-12T10:30:00Z",
    "last_hour": {
        "total": 15,
        "read": 12,
        "read_rate": 80.0
    },
    "last_24_hours": {
        "total": 180,
        "read": 165,
        "read_rate": 91.7
    },
    "current_user": {
        "unread_count": 3
    },
    "system_health": {
        "status": "healthy",
        "websocket_connected": true,
        "push_notification_service": "operational"
    }
}
```

### Compare Periods

Compare notification metrics between two time periods.

**Endpoint:** `GET /api/analytics/notifications/compare`  
**Authentication:** Required

#### Query Parameters
- `period1_start` (required): ISO date string
- `period1_end` (required): ISO date string
- `period2_start` (required): ISO date string
- `period2_end` (required): ISO date string

#### Response
```json
{
    "period1": {
        "start": "2026-04-12T00:00:00Z",
        "end": "2026-04-19T00:00:00Z",
        "summary": {
            "total_notifications": 600,
            "read_rate": 92.0
        }
    },
    "period2": {
        "start": "2026-05-05T00:00:00Z",
        "end": "2026-05-12T00:00:00Z",
        "summary": {
            "total_notifications": 650,
            "read_rate": 94.4
        }
    },
    "changes": {
        "total_notifications": {
            "period1": 600,
            "period2": 650,
            "change": 50,
            "change_percent": 8.33
        },
        "read_rate": {
            "period1": 92.0,
            "period2": 94.4,
            "change": 2.4,
            "change_percent": 2.61
        }
    }
}
```

## WebSocket Events

### Connection and Authentication

All WebSocket connections require authentication via Flask-Login session.

```javascript
const socket = io('ws://localhost:5003', {
    auth: {
        token: 'your-auth-token'
    }
});
```

### Subscribe to Notifications

Subscribe the current user to their notification room.

**Event:** `subscribe_notifications`  
**Data:** `{}` (empty object)

#### Response Events
```javascript
// Unread count update
socket.on('unread_count', (data) => {
    console.log('Unread count:', data.unread_count);
});

// Recent notifications
socket.on('recent_notifications', (data) => {
    console.log('Recent notifications:', data.notifications);
});
```

### Mark Notification as Read

Mark a specific notification as read for the current user.

**Event:** `mark_notification_read`  
**Data:** `{ "notification_id": 123 }`

#### Response Events
```javascript
// Notification marked as read
socket.on('notification_read', (data) => {
    console.log('Notification marked read:', data.notification_id);
});

// Updated unread count
socket.on('unread_count', (data) => {
    console.log('Updated unread count:', data.unread_count);
});
```

### Fetch Unread Count

Request the current unread notification count.

**Event:** `fetch_unread_count`  
**Data:** `{}` (empty object)

#### Response Event
```javascript
socket.on('unread_count', (data) => {
    console.log('Current unread count:', data.unread_count);
});
```

### Fetch Recent Notifications

Request recent notifications for the current user.

**Event:** `fetch_recent_notifications`  
**Data:** `{ "limit": 10 }` (optional limit)

#### Response Event
```javascript
socket.on('recent_notifications', (data) => {
    console.log('Recent notifications:', data.notifications);
});
```

### Real-time Notification Updates

Receive new notifications in real-time.

**Event:** `notification` (server to client)

#### Data Structure
```javascript
{
    "id": 123,
    "content": "John Doe commented on your post",
    "link": "/forum/post/456",
    "is_read": false,
    "created_at": "2026-05-12T10:30:00Z",
    "type": "comment"
}
```

### All Notifications Marked Read

Broadcast when all notifications are marked as read.

**Event:** `all_notifications_marked_read` (server to client)

#### Data Structure
```javascript
{
    "count": 5,
    "unread_count": 0,
    "status": "success"
}
```

## Error Handling

### Standard Error Response Format

All API endpoints return consistent error responses:

```json
{
    "error": "Error type",
    "message": "Human-readable error description",
    "details": {
        "field": "Additional error details"
    }
}
```

### Common HTTP Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### WebSocket Error Events

```javascript
socket.on('error', (error) => {
    console.error('WebSocket error:', error);
});

socket.on('disconnect', (reason) => {
    console.log('Disconnected:', reason);
});
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Push notification endpoints:** 10 requests per minute
- **Analytics endpoints:** 60 requests per minute
- **Tracking endpoints:** 100 requests per minute

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1623456789
```

## Integration Examples

### JavaScript Frontend Integration

```javascript
class NotificationManager {
    constructor() {
        this.socket = io('ws://localhost:5003');
        this.pushManager = new PushNotificationManager();
        this.setupEventHandlers();
    }
    
    async initialize() {
        // Subscribe to WebSocket notifications
        this.socket.emit('subscribe_notifications');
        
        // Initialize push notifications
        await this.pushManager.initialize();
        
        // Fetch current unread count
        this.socket.emit('fetch_unread_count');
    }
    
    setupEventHandlers() {
        // Handle new notifications
        this.socket.on('notification', (notification) => {
            this.displayNotification(notification);
            this.updateUnreadCount();
        });
        
        // Handle unread count updates
        this.socket.on('unread_count', (data) => {
            this.updateUnreadCount(data.unread_count);
        });
    }
    
    async markAsRead(notificationId) {
        this.socket.emit('mark_notification_read', {
            notification_id: notificationId
        });
        
        // Track engagement
        await fetch('/api/analytics/notifications/track', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getAuthToken()}`
            },
            body: JSON.stringify({
                notification_id: notificationId,
                action: 'marked_read'
            })
        });
    }
}
```

### Python Backend Integration

```python
from app.notification.routes import create_notification
from app.analytics.notification_analytics import notification_analytics

# Create notification with multi-channel delivery
notification = create_notification(
    user_id=user.id,
    content=f'{current_user.username} commented on your post "{post.title}"',
    link=url_for('forum.post', post_id=post.id),
    notification_type='comment',
    send_email=True  # Send email notification
)

# Track analytics
notification_analytics.track_notification_delivery(
    notification_id=notification.id,
    delivery_type='websocket',
    status='sent',
    recipient_id=user.id,
    metadata={
        'source': 'forum_comment',
        'post_id': post.id
    }
)
```

### Mobile App Integration

```swift
// Swift iOS example for push notifications
import UserNotifications

class NotificationService {
    func registerForPushNotifications() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
            if granted {
                self.getNotificationSettings()
            }
        }
    }
    
    func getNotificationSettings() {
        UNUserNotificationCenter.current().getNotificationSettings { settings in
            guard settings.authorizationStatus == .authorized else { return }
            
            UIApplication.shared.registerForRemoteNotifications()
        }
    }
    
    func didRegisterForRemoteNotifications(deviceToken: Data) {
        let tokenString = deviceToken.reduce("", {$0 + String(format: "%02x", $1)})
        
        // Send to server
        subscribeToPushNotifications(endpoint: tokenString)
    }
    
    func subscribeToPushNotifications(endpoint: String) {
        guard let url = URL(string: "http://localhost:5000/api/push/subscribe"),
              let token = getAuthToken() else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let payload = [
            "endpoint": "https://fcm.googleapis.com/fcm/send/\(endpoint)",
            "keys": [
                "p256dh": "public-key",
                "auth": "auth-key"
            ]
        ] as [String: Any]
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: payload)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            // Handle response
        }.resume()
    }
}
```

## Advanced Search & Filtering API

### Search Notifications

Search notifications with advanced filtering options.

**Endpoint:** `POST /notifications/search/api`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "query": "comment",
    "filters": {
        "type": ["comment", "message"],
        "priority": ["high", "urgent"],
        "is_read": false,
        "date_range": "last_7_days",
        "content_search": "important"
    },
    "sort": {
        "by": "created_at",
        "order": "desc"
    },
    "pagination": {
        "page": 1,
        "per_page": 25
    }
}
```

#### Response
```json
{
    "success": true,
    "notifications": [
        {
            "id": 1,
            "type": "comment",
            "content": "john_doe commented on your post",
            "created_at": "2026-05-12T10:00:00Z",
            "is_read": false,
            "priority": "high"
        }
    ],
    "total_count": 42,
    "page": 1,
    "per_page": 25
}
```

### Create Custom Filter

Create a custom filter for notifications.

**Endpoint:** `POST /notifications/filtering/custom`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "name": "My Important Notifications",
    "filters": {
        "type": ["comment", "message"],
        "priority": ["high", "urgent"],
        "is_read": false
    },
    "sort_options": {
        "sort_by": "priority",
        "sort_order": "desc"
    }
}
```

#### Response
```json
{
    "success": true,
    "filter_id": "custom_1_1234567890",
    "name": "My Important Notifications",
    "created_at": "2026-05-12T10:00:00Z"
}
```

### Get Filter Presets

Get available filter presets.

**Endpoint:** `GET /notifications/filtering/api/presets`  
**Authentication:** Required

#### Response
```json
{
    "success": true,
    "presets": {
        "unread_important": {
            "name": "Unread Important",
            "filters": {
                "is_read": false,
                "priority": ["high", "urgent"]
            },
            "sort": ["priority", "created_at"]
        },
        "recent_comments": {
            "name": "Recent Comments",
            "filters": {
                "type": "comment",
                "date_range": "last_7_days"
            },
            "sort": ["created_at"]
        }
    }
}
```

## Notification Archiving API

### Execute Archiving

Execute notification archiving operations.

**Endpoint:** `POST /notifications/archive/execute`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "archive_type": "automatic",
    "rules": {
        "read_older_than": "90_days",
        "unread_older_than": "365_days",
        "keep_important": true,
        "keep_unread": true
    },
    "notification_ids": [1, 2, 3, 4, 5]
}
```

#### Response
```json
{
    "success": true,
    "archived_count": 25,
    "kept_count": 5,
    "archive_id": "archive_1234567890",
    "execution_time": "2.34s"
}
```

### Search Archived Notifications

Search within archived notifications.

**Endpoint:** `POST /notifications/archive/api/search`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "query": "system notification",
    "date_range": "last_90_days",
    "include_archived": true,
    "filters": {
        "type": "system",
        "priority": ["high", "urgent"]
    }
}
```

#### Response
```json
{
    "success": true,
    "archived_notifications": [
        {
            "id": 1,
            "type": "system",
            "content": "System notification message",
            "archived_at": "2026-05-12T10:00:00Z",
            "original_created_at": "2026-02-12T10:00:00Z"
        }
    ],
    "total_count": 15
}
```

### Restore Archived Notifications

Restore notifications from archive.

**Endpoint:** `POST /notifications/archive/restore`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "archive_ids": ["archive_1234567890"],
    "notification_ids": [1, 2, 3],
    "restore_all": false
}
```

#### Response
```json
{
    "success": true,
    "restored_count": 3,
    "failed_count": 0,
    "restored_notifications": [1, 2, 3]
}
```

## Advanced Scheduling API

### Update Notification Schedule

Update user's notification scheduling preferences.

**Endpoint:** `POST /notifications/schedule/update`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "quiet_hours_enabled": true,
    "weekday_start": "22:00",
    "weekday_end": "08:00",
    "weekend_start": "23:00",
    "weekend_end": "09:00",
    "daily_digest_enabled": true,
    "daily_digest_time": "09:00",
    "weekly_summary_enabled": true,
    "weekly_summary_day": "monday",
    "weekly_summary_time": "10:00",
    "emergency_override_urgent": true,
    "emergency_override_security": true
}
```

#### Response
```json
{
    "success": true,
    "message": "Schedule preferences updated successfully",
    "schedule": {
        "quiet_hours_enabled": true,
        "daily_digest_enabled": true,
        "next_digest_time": "2026-05-13T09:00:00Z"
    }
}
```

### Test Digest

Test notification digest generation.

**Endpoint:** `POST /notifications/schedule/test-digest`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "digest_type": "daily",
    "preview_only": true,
    "date_range": "last_24_hours"
}
```

#### Response
```json
{
    "success": true,
    "digest": {
        "type": "daily",
        "notification_count": 15,
        "content": "Daily digest preview...",
        "categories": {
            "comments": 8,
            "messages": 4,
            "system": 3
        }
    }
}
```

### Preview Schedule

Preview upcoming scheduled notifications.

**Endpoint:** `GET /notifications/schedule/preview`  
**Authentication:** Required

#### Response
```json
{
    "success": true,
    "schedule_preview": {
        "next_digest": "2026-05-13T09:00:00Z",
        "quiet_hours_active": false,
        "pending_notifications": 5,
        "scheduled_notifications": [
            {
                "id": 1,
                "type": "digest",
                "scheduled_time": "2026-05-13T09:00:00Z",
                "content": "Daily digest"
            }
        ]
    }
}
```

## Smart Grouping API

### Update Grouping Preferences

Update notification grouping preferences.

**Endpoint:** `POST /notifications/grouping/update`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "enable_grouping": true,
    "group_by_type": true,
    "group_by_priority": false,
    "group_by_source": true,
    "group_by_content": true,
    "max_group_size": 10,
    "similarity_threshold": 0.7,
    "smart_grouping_enabled": true
}
```

#### Response
```json
{
    "success": true,
    "message": "Grouping preferences updated successfully",
    "preferences": {
        "enable_grouping": true,
        "grouping_strategy": "smart",
        "max_group_size": 10
    }
}
```

### Group Notifications

Group notifications using specified strategy.

**Endpoint:** `POST /notifications/grouping/group`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "notification_ids": [1, 2, 3, 4, 5],
    "strategy": "content",
    "group_name": "Recent Comments",
    "user_preferences": {
        "max_group_size": 10
    }
}
```

#### Response
```json
{
    "success": true,
    "grouped_notifications": [
        {
            "group_key": "recent_comments",
            "group_name": "Recent Comments",
            "group_type": "content",
            "notifications": [1, 2, 3],
            "count": 3
        }
    ],
    "total_groups": 1
}
```

### Preview Grouping

Preview how notifications would be grouped.

**Endpoint:** `GET /notifications/grouping/preview`  
**Authentication:** Required

#### Response
```json
{
    "success": true,
    "grouping_preview": {
        "strategy": "smart",
        "groups": [
            {
                "group_key": "comments",
                "group_name": "Comments",
                "count": 8,
                "similarity_score": 0.85
            },
            {
                "group_key": "messages",
                "group_name": "Messages", 
                "count": 4,
                "similarity_score": 0.92
            }
        ]
    }
}
```

## Translation API

### Update Language Preference

Update user's language preference.

**Endpoint:** `POST /notifications/translation/update`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "language": "es"
}
```

#### Response
```json
{
    "success": true,
    "message": "Language preference updated to Spanish",
    "current_language": "es",
    "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko", "ar", "hi"]
}
```

### Translate Notification

Translate a specific notification.

**Endpoint:** `POST /notifications/translation/translate`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "notification": {
        "type": "comment",
        "content": "john_doe commented on your post \"Welcome to the Forum\"",
        "username": "john_doe",
        "post_title": "Welcome to the Forum"
    },
    "target_language": "es"
}
```

#### Response
```json
{
    "success": true,
    "original_notification": {
        "type": "comment",
        "content": "john_doe commented on your post \"Welcome to the Forum\""
    },
    "translated_notification": {
        "type": "comment",
        "content": "john_doe comentó en tu publicación \"Bienvenido al Foro\"",
        "language": "es"
    },
    "target_language": "es"
}
```

### Get Supported Languages

Get list of supported languages.

**Endpoint:** `GET /notifications/translation/api/languages`  
**Authentication:** Required

#### Response
```json
{
    "success": true,
    "supported_languages": {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arabic",
        "hi": "Hindi"
    },
    "current_language": "en"
}
```

### Translate Text

Translate arbitrary text.

**Endpoint:** `POST /notifications/translation/api/translate-text`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "text": "Hello, how are you?",
    "target_language": "es",
    "source_language": "en"
}
```

#### Response
```json
{
    "success": true,
    "original_text": "Hello, how are you?",
    "translated_text": "Hola, ¿cómo estás?",
    "source_language": "en",
    "target_language": "es"
}
```

## Mobile Notifications API

### Register Mobile Device

Register a mobile device for push notifications.

**Endpoint:** `POST /notifications/mobile/register`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "platform": "ios",
    "device_token": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    "device_id": "ios-device-123",
    "app_version": "1.0.0",
    "os_version": "iOS 17.0",
    "device_model": "iPhone 15",
    "push_enabled": true,
    "notification_types": ["comment", "message", "system"],
    "send_test_notification": false
}
```

#### Response
```json
{
    "success": true,
    "registration_id": "device_1_ios-device-123_1234567890",
    "device_info": {
        "platform": "ios",
        "device_id": "ios-device-123",
        "status": "active",
        "created_at": "2026-05-12T10:00:00Z"
    },
    "message": "Device registered successfully"
}
```

### Send Mobile Notification

Send push notification to mobile devices.

**Endpoint:** `POST /notifications/mobile/send`  
**Authentication:** Required  
**Content-Type:** `application/json`

#### Request Body
```json
{
    "notification": {
        "title": "New Comment",
        "message": "john_doe commented on your post",
        "type": "comment",
        "priority": "normal",
        "link": "/forum/post/123",
        "platform_specific": {
            "ios": {
                "badge": 1,
                "sound": "default",
                "category": "NEW_COMMENT"
            },
            "android": {
                "channel_id": "comments",
                "icon": "notification_icon",
                "color": "#007bff"
            }
        }
    },
    "target_devices": ["device_123", "device_456"]
}
```

#### Response
```json
{
    "success": true,
    "total_devices": 2,
    "total_sent": 2,
    "total_failed": 0,
    "results": {
        "device_123": {
            "success": true,
            "platform": "ios",
            "message_id": "ios_1234567890",
            "status": "delivered"
        },
        "device_456": {
            "success": true,
            "platform": "android",
            "message_id": "android_1234567890",
            "status": "delivered"
        }
    }
}
```

### Get User Devices

Get user's registered mobile devices.

**Endpoint:** `GET /notifications/mobile/devices`  
**Authentication:** Required

#### Response
```json
{
    "success": true,
    "statistics": {
        "total_devices": 2,
        "platforms": {
            "ios": 1,
            "android": 1
        },
        "active_devices": 2,
        "inactive_devices": 0
    },
    "devices": [
        {
            "registration_id": "device_123",
            "platform": "ios",
            "device_id": "ios-device-123",
            "device_model": "iPhone 15",
            "app_version": "1.0.0",
            "status": "active",
            "last_active": "2026-05-12T10:00:00Z"
        }
    ],
    "total_count": 2
}
```

### Test Mobile Notification

Send test notification to specific device.

**Endpoint:** `POST /notifications/mobile/test/<registration_id>`  
**Authentication:** Required

#### Response
```json
{
    "success": true,
    "total_devices": 1,
    "total_sent": 1,
    "total_failed": 0,
    "test_notification": {
        "title": "Test Notification",
        "message": "This is a test notification from AutoBot Solutions Forum",
        "type": "system"
    }
}
```

### Get Supported Platforms

Get supported mobile platforms.

**Endpoint:** `GET /notifications/mobile/api/platforms`  
**Authentication:** Required

#### Response
```json
{
    "success": true,
    "platforms": {
        "ios": "Apple iOS",
        "android": "Google Android",
        "huawei": "Huawei HMS",
        "web": "Web Push"
    },
    "notification_types": {
        "forum_activity": "Forum Activity",
        "messages": "Messages",
        "moderation": "Moderation",
        "security": "Security",
        "system": "System Updates",
        "marketing": "Marketing (opt-in)"
    }
}
```

## Testing

### API Testing Examples

```bash
# Test push notification subscription
curl -X POST http://localhost:5000/api/push/subscribe \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "https://fcm.googleapis.com/fcm/send/test",
    "keys": {
      "p256dh": "test-key",
      "auth": "test-auth"
    }
  }'

# Test analytics endpoint
curl -X GET http://localhost:5000/api/analytics/notifications/delivery \
  -H "Authorization: Bearer your-token"

# Test tracking endpoint
curl -X POST http://localhost:5000/api/analytics/notifications/track \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_id": 123,
    "action": "viewed"
  }'
```

### WebSocket Testing

```javascript
// Connect to WebSocket server
const socket = io('ws://localhost:5003');

// Test subscription
socket.emit('subscribe_notifications');

// Test mark as read
socket.emit('mark_notification_read', {
    notification_id: 123
});

// Listen for events
socket.on('notification', (data) => {
    console.log('Received notification:', data);
});
```

## Security Considerations

### Authentication
- All API endpoints require valid authentication
- WebSocket connections authenticated via Flask-Login
- Token-based authentication for API access

### Data Validation
- Input validation on all endpoints
- SQL injection prevention via ORM
- XSS protection in templates

### Rate Limiting
- Endpoint-specific rate limits
- WebSocket connection limits
- DDoS protection considerations

### Privacy
- User-specific notification access
- Secure data storage
- Audit logging for sensitive operations

---

**API Version:** 1.0  
**Last Updated:** May 12, 2026  
**Documentation Version:** 1.0
