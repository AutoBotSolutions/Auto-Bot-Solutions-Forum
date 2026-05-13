# Comprehensive Notification System API Documentation

## Overview

This document provides comprehensive API documentation for the notification system, covering all endpoints for WebSocket real-time communication, email delivery, user preferences, and search functionality.

**API Version:** 2.0  
**Base URL:** `https://yourdomain.com/api`  
**WebSocket URL:** `wss://yourdomain.com`  
**Authentication:** Bearer Token / Session-based  

## Table of Contents

1. [WebSocket API](#websocket-api)
2. [Email API](#email-api)
3. [Preferences API](#preferences-api)
4. [Search API](#search-api)
5. [Authentication](#authentication)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Response Formats](#response-formats)

---

## WebSocket API

### Connection

**Endpoint:** `wss://yourdomain.com`  
**Protocol:** Socket.IO  

#### Connection Example

```javascript
import io from 'socket.io-client';

const socket = io('wss://yourdomain.com', {
  auth: {
    token: 'your-auth-token'
  },
  transports: ['websocket', 'polling']
});

socket.on('connect', () => {
  console.log('Connected to notification server');
});
```

### Events

#### Client to Server Events

##### subscribe_notifications
Subscribe to real-time notifications for the authenticated user.

```javascript
socket.emit('subscribe_notifications');
```

**Response:**
```json
{
  "user_id": 123,
  "unread_count": 5,
  "subscription_confirmed": true
}
```

##### mark_notification_read
Mark a specific notification as read.

```javascript
socket.emit('mark_notification_read', {
  notification_id: 456
});
```

**Response:**
```json
{
  "notification_id": 456,
  "user_id": 123,
  "unread_count": 4
}
```

##### fetch_unread_count
Get current unread notification count.

```javascript
socket.emit('fetch_unread_count');
```

**Response:**
```json
{
  "count": 4
}
```

##### fetch_recent_notifications
Fetch recent notifications.

```javascript
socket.emit('fetch_recent_notifications', {
  limit: 10
});
```

**Response:**
```json
{
  "notifications": [
    {
      "id": 456,
      "type": "comment",
      "content": "John commented on your post",
      "link": "/posts/123",
      "created_at": "2026-05-12T10:30:00Z",
      "is_read": false
    }
  ],
  "count": 4
}
```

#### Server to Client Events

##### new_notification
New notification received.

```json
{
  "id": 457,
  "type": "message",
  "content": "You have a new message from Jane",
  "link": "/messages/789",
  "created_at": "2026-05-12T10:35:00Z",
  "unread_count": 5
}
```

##### notification_read
Notification marked as read.

```json
{
  "notification_id": 456,
  "user_id": 123,
  "unread_count": 4
}
```

##### unread_count
Updated unread count.

```json
{
  "count": 4
}
```

##### system_notification
System notification.

```json
{
  "title": "System Maintenance",
  "message": "System will be under maintenance at 11:00 PM",
  "type": "system",
  "timestamp": "2026-05-12T10:40:00Z"
}
```

---

## Email API

### Send Notification Email

**Endpoint:** `POST /api/email/send-notification`  
**Authentication:** Required  
**Rate Limit:** 100 requests per minute

#### Request

```json
{
  "notification_id": 456,
  "user_email": "user@example.com",
  "notification_type": "comment",
  "template_data": {
    "username": "John",
    "content": "New comment on your post",
    "post_title": "Welcome to the Forum",
    "link": "https://yourdomain.com/posts/123"
  },
  "language": "en",
  "priority": "normal"
}
```

#### Response

```json
{
  "success": true,
  "message": "Email queued for delivery",
  "email_id": "email_789",
  "queue_position": 5,
  "estimated_delivery": "2026-05-12T10:31:00Z"
}
```

### Send Bulk Emails

**Endpoint:** `POST /api/email/send-bulk`  
**Authentication:** Required  
**Rate Limit:** 10 requests per minute

#### Request

```json
{
  "notifications": [
    {
      "notification_id": 456,
      "user_email": "user1@example.com",
      "template_data": {
        "username": "User1",
        "content": "Your notification content"
      }
    },
    {
      "notification_id": 457,
      "user_email": "user2@example.com",
      "template_data": {
        "username": "User2",
        "content": "Your notification content"
      }
    }
  ],
  "template_name": "notification_template",
  "language": "en"
}
```

#### Response

```json
{
  "success": true,
  "total_queued": 2,
  "total_failed": 0,
  "batch_id": "batch_456",
  "estimated_completion": "2026-05-12T10:35:00Z"
}
```

### Get Email Status

**Endpoint:** `GET /api/email/status/{email_id}`  
**Authentication:** Required

#### Response

```json
{
  "email_id": "email_789",
  "status": "delivered",
  "sent_at": "2026-05-12T10:30:15Z",
  "delivered_at": "2026-05-12T10:30:45Z",
  "opened_at": "2026-05-12T10:32:00Z",
  "clicked_at": null,
  "bounce_reason": null,
  "delivery_attempts": 1
}
```

### Get Email Analytics

**Endpoint:** `GET /api/email/analytics`  
**Authentication:** Required  
**Query Parameters:**
- `start_date`: Start date (ISO 8601)
- `end_date`: End date (ISO 8601)

#### Response

```json
{
  "period": {
    "start_date": "2026-05-11T00:00:00Z",
    "end_date": "2026-05-12T23:59:59Z"
  },
  "statistics": {
    "total_sent": 1250,
    "total_delivered": 1180,
    "total_opened": 890,
    "total_clicked": 234,
    "total_bounced": 45,
    "delivery_rate": 0.944,
    "open_rate": 0.712,
    "click_rate": 0.187
  },
  "by_type": {
    "comment": {
      "sent": 450,
      "delivered": 425,
      "opened": 320,
      "clicked": 89
    },
    "message": {
      "sent": 380,
      "delivered": 365,
      "opened": 289,
      "clicked": 98
    }
  }
}
```

### Track Email Open

**Endpoint:** `GET /api/email/track-open/{email_id}`  
**Authentication:** None (tracking endpoint)

#### Response
Returns 1x1 transparent GIF image

### Track Email Click

**Endpoint:** `GET /api/email/track-click/{email_id}`  
**Authentication:** None (tracking endpoint)  
**Query Parameters:**
- `url`: Target URL

#### Response
Redirects to target URL

---

## Preferences API

### Get User Preferences

**Endpoint:** `GET /api/notifications/preferences`  
**Authentication:** Required

#### Response

```json
{
  "preferences": {
    "push_enabled": true,
    "email_enabled": true,
    "daily_digest_enabled": true,
    "weekly_summary_enabled": false,
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00",
    "quiet_hours_weekend_enabled": true,
    "quiet_hours_weekend_start": "23:00",
    "quiet_hours_weekend_end": "09:00",
    "notification_types": {
      "comment": {
        "enabled": true,
        "push": true,
        "email": true,
        "priority": "normal"
      },
      "message": {
        "enabled": true,
        "push": true,
        "email": true,
        "priority": "normal"
      },
      "system": {
        "enabled": true,
        "push": true,
        "email": false,
        "priority": "high"
      }
    }
  }
}
```

### Update User Preferences

**Endpoint:** `PUT /api/notifications/preferences`  
**Authentication:** Required

#### Request

```json
{
  "push_enabled": true,
  "email_enabled": true,
  "daily_digest_enabled": false,
  "weekly_summary_enabled": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "23:00",
  "quiet_hours_end": "07:00",
  "notification_types": {
    "comment": {
      "enabled": true,
      "push": true,
      "email": true,
      "priority": "normal"
    },
    "message": {
      "enabled": true,
      "push": false,
      "email": true,
      "priority": "low"
    }
  }
}
```

#### Response

```json
{
  "success": true,
  "message": "Preferences updated successfully",
  "updated_preferences": {
    "push_enabled": true,
    "email_enabled": true,
    "daily_digest_enabled": false,
    "weekly_summary_enabled": true
  }
}
```

### Get Notification Type Preferences

**Endpoint:** `GET /api/notifications/preferences/{type}`  
**Authentication:** Required  
**Path Parameters:**
- `type`: Notification type (comment, message, system, etc.)

#### Response

```json
{
  "type": "comment",
  "preferences": {
    "enabled": true,
    "push": true,
    "email": true,
    "priority": "normal",
    "frequency": "immediate"
  },
  "available_options": {
    "priority": ["low", "normal", "high", "urgent"],
    "frequency": ["immediate", "hourly", "daily", "weekly"]
  }
}
```

### Update Notification Type Preferences

**Endpoint:** `PUT /api/notifications/preferences/{type}`  
**Authentication:** Required

#### Request

```json
{
  "enabled": true,
  "push": true,
  "email": false,
  "priority": "high",
  "frequency": "immediate"
}
```

#### Response

```json
{
  "success": true,
  "message": "Comment preferences updated successfully",
  "preferences": {
    "enabled": true,
    "push": true,
    "email": false,
    "priority": "high",
    "frequency": "immediate"
  }
}
```

### Test Notification Settings

**Endpoint:** `POST /api/notifications/test`  
**Authentication:** Required

#### Request

```json
{
  "type": "comment",
  "channels": ["push", "email"],
  "test_data": {
    "title": "Test Notification",
    "message": "This is a test notification",
    "link": "/notifications"
  }
}
```

#### Response

```json
{
  "success": true,
  "test_results": {
    "push": {
      "sent": true,
      "delivered": true,
      "message": "Test push notification sent successfully"
    },
    "email": {
      "sent": true,
      "queued": true,
      "message": "Test email queued for delivery"
    }
  }
}
```

---

## Search API

### Search Notifications

**Endpoint:** `GET /api/notifications/search`  
**Authentication:** Required  
**Query Parameters:**
- `q`: Search query (string)
- `types`: Notification types (comma-separated)
- `priorities`: Priority levels (comma-separated)
- `is_read`: Read status (true/false)
- `date_range`: Date range (last_24_hours, last_7_days, last_30_days, custom)
- `start_date`: Custom start date (ISO 8601)
- `end_date`: Custom end date (ISO 8601)
- `page`: Page number (default: 1)
- `per_page`: Results per page (default: 20, max: 100)

#### Example Request

```
GET /api/notifications/search?q=welcome&types=comment,message&is_read=false&date_range=last_7_days&page=1&per_page=20
```

#### Response

```json
{
  "success": true,
  "results": [
    {
      "id": 456,
      "type": "comment",
      "content": "John commented on your post 'Welcome to the Forum'",
      "link": "/posts/123",
      "is_read": false,
      "created_at": "2026-05-12T10:30:00Z",
      "priority": "normal",
      "relevance_score": 0.95
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_count": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "search_metadata": {
    "query": "welcome",
    "filters_applied": {
      "types": ["comment", "message"],
      "is_read": false,
      "date_range": "last_7_days"
    },
    "search_time": 0.045,
    "from_cache": false
  }
}
```

### Advanced Search

**Endpoint:** `POST /api/notifications/search/advanced`  
**Authentication:** Required

#### Request

```json
{
  "query": "welcome OR hello",
  "filters": {
    "types": ["comment", "message"],
    "priorities": ["normal", "high"],
    "is_read": false,
    "date_range": {
      "type": "custom",
      "start_date": "2026-05-10T00:00:00Z",
      "end_date": "2026-05-12T23:59:59Z"
    }
  },
  "sort": {
    "field": "created_at",
    "order": "desc"
  },
  "pagination": {
    "page": 1,
    "per_page": 20
  }
}
```

#### Response

```json
{
  "success": true,
  "results": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_count": 15,
    "total_pages": 1
  },
  "search_metadata": {
    "query": "welcome OR hello",
    "search_time": 0.067,
    "from_cache": false,
    "index_used": "notifications_search_gin"
  }
}
```

### Search Suggestions

**Endpoint:** `GET /api/notifications/search/suggestions`  
**Authentication:** Required  
**Query Parameters:**
- `q`: Partial query (string)
- `limit`: Number of suggestions (default: 10)

#### Response

```json
{
  "suggestions": [
    {
      "text": "welcome message",
      "type": "content",
      "count": 5
    },
    {
      "text": "welcome post",
      "type": "content",
      "count": 3
    },
    {
      "text": "comment",
      "type": "notification_type",
      "count": 25
    }
  ]
}
```

### Search Analytics

**Endpoint:** `GET /api/notifications/search/analytics`  
**Authentication:** Required  
**Query Parameters:**
- `period`: Analysis period (7_days, 30_days, 90_days)

#### Response

```json
{
  "period": "30_days",
  "analytics": {
    "total_searches": 1250,
    "unique_users": 89,
    "average_results": 15.5,
    "success_rate": 0.94,
    "popular_queries": [
      {
        "query": "welcome",
        "count": 45,
        "average_results": 8.2
      },
      {
        "query": "comment",
        "count": 38,
        "average_results": 12.5
      }
    ],
    "popular_filters": [
      {
        "filter": "types",
        "usage_count": 234
      },
      {
        "filter": "date_range",
        "usage_count": 189
      }
    ]
  }
}
```

---

## Authentication

### Bearer Token Authentication

Include the token in the Authorization header:

```
Authorization: Bearer your-jwt-token
```

### Session-based Authentication

Use session cookies - no additional headers required.

### WebSocket Authentication

Pass token in the connection options:

```javascript
const socket = io('wss://yourdomain.com', {
  auth: {
    token: 'your-jwt-token'
  }
});
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    },
    "timestamp": "2026-05-12T10:30:00Z",
    "request_id": "req_123456"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input parameters |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### WebSocket Error Events

```javascript
socket.on('error', (error) => {
  console.error('WebSocket error:', error);
});

socket.on('connect_error', (error) => {
  console.error('Connection error:', error);
});
```

---

## Rate Limiting

### API Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Email Send | 100 req/min | 1 minute |
| Bulk Email | 10 req/min | 1 minute |
| Search | 1000 req/min | 1 minute |
| Preferences | 100 req/min | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1652354400
```

### Rate Limit Response

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "retry_after": 45,
    "limit": 100,
    "window": 60
  }
}
```

---

## Response Formats

### Success Response

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "metadata": {
    "timestamp": "2026-05-12T10:30:00Z",
    "request_id": "req_123456",
    "version": "2.0"
  }
}
```

### Paginated Response

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_count": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false,
    "next_page": 2,
    "prev_page": null
  }
}
```

### Cached Response

```json
{
  "success": true,
  "data": [...],
  "metadata": {
    "from_cache": true,
    "cached_at": "2026-05-12T10:25:00Z",
    "cache_ttl": 300
  }
}
```

---

## SDK Examples

### JavaScript/TypeScript SDK

```typescript
class NotificationAPI {
  private baseURL: string;
  private token: string;

  constructor(baseURL: string, token: string) {
    this.baseURL = baseURL;
    this.token = token;
  }

  async searchNotifications(params: SearchParams): Promise<SearchResponse> {
    const response = await fetch(`${this.baseURL}/api/notifications/search`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });

    return response.json();
  }

  async updatePreferences(preferences: UserPreferences): Promise<UpdateResponse> {
    const response = await fetch(`${this.baseURL}/api/notifications/preferences`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(preferences)
    });

    return response.json();
  }
}
```

### Python SDK

```python
import requests
from typing import Dict, List, Optional

class NotificationAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def search_notifications(self, params: Dict) -> Dict:
        response = requests.get(
            f'{self.base_url}/api/notifications/search',
            headers=self.headers,
            params=params
        )
        return response.json()

    def update_preferences(self, preferences: Dict) -> Dict:
        response = requests.put(
            f'{self.base_url}/api/notifications/preferences',
            headers=self.headers,
            json=preferences
        )
        return response.json()
```

---

## Testing

### API Testing Examples

```bash
# Search notifications
curl -X GET "https://yourdomain.com/api/notifications/search?q=welcome" \
  -H "Authorization: Bearer your-token"

# Update preferences
curl -X PUT "https://yourdomain.com/api/notifications/preferences" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"push_enabled": true, "email_enabled": false}'

# Send email notification
curl -X POST "https://yourdomain.com/api/email/send-notification" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"notification_id": 456, "user_email": "user@example.com"}'
```

### WebSocket Testing

```javascript
// Test WebSocket connection
const socket = io('wss://yourdomain.com', {
  auth: { token: 'your-token' }
});

socket.on('connect', () => {
  console.log('Connected');
  
  // Test subscription
  socket.emit('subscribe_notifications');
  
  // Test search
  socket.emit('fetch_recent_notifications', { limit: 5 });
});

socket.on('new_notification', (data) => {
  console.log('New notification:', data);
});
```

---

## Changelog

### v2.0 (2026-05-12)
- Added comprehensive WebSocket API
- Enhanced email delivery optimization
- Added search performance optimization
- Improved error handling and rate limiting
- Added analytics endpoints

### v1.0 (2026-04-15)
- Initial API release
- Basic notification endpoints
- Email delivery functionality
- User preferences management

---

**Last Updated:** May 12, 2026  
**Version:** 2.0  
**Status:** Production Ready
