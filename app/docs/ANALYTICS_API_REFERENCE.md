# Analytics API Reference

**Version:** 1.0.0  
**Last Updated:** May 11, 2026  
**Base URL:** `/analytics/api`  

---

## 📋 Overview

The Analytics API provides comprehensive endpoints for accessing analytics data, tracking events, and retrieving system metrics. All endpoints require authentication and return JSON responses with consistent structure.

### Authentication
All API endpoints require user authentication. Include session cookies or authentication headers in requests.

### Response Format
All successful responses follow this structure:
```json
{
    "success": true,
    "data": { ... },
    "message": "Success message (optional)"
}
```

Error responses:
```json
{
    "success": false,
    "error": "Error message",
    "error_code": "ERROR_CODE"
}
```

---

## 🔌 API Endpoints

### Events API

#### Get Events Statistics
```http
GET /analytics/api/events
```

Retrieve analytics events statistics with optional filtering.

**Parameters:**
- `event_type` (optional) - Filter by event type (view, click, vote, comment, search, share, bookmark, download, session)
- `event_category` (optional) - Filter by event category (upvote, downvote, start, end, internal, external)
- `user_id` (optional) - Filter by specific user ID
- `start_date` (optional) - Filter events from this date (YYYY-MM-DD)
- `end_date` (optional) - Filter events until this date (YYYY-MM-DD)
- `aggregation` (optional) - Aggregate data by (daily, weekly, monthly)
- `limit` (optional) - Maximum number of results (default: 100)

**Example Request:**
```http
GET /analytics/api/events?event_type=view&start_date=2026-05-01&end_date=2026-05-11&aggregation=daily
```

**Example Response:**
```json
{
    "success": true,
    "data": {
        "total_events": 15420,
        "unique_users": 892,
        "avg_event_value": 1.2,
        "events_by_hour": {
            "9": 234,
            "10": 456,
            "11": 678,
            "12": 789,
            "13": 567,
            "14": 890,
            "15": 1234,
            "16": 987,
            "17": 654,
            "18": 432,
            "19": 321,
            "20": 210,
            "21": 198,
            "22": 187,
            "23": 176
        },
        "events_by_day": {
            "2026-05-10": 1234,
            "2026-05-11": 1456
        },
        "events_by_type": {
            "view": 8923,
            "click": 3456,
            "vote": 1234,
            "comment": 987,
            "search": 654,
            "share": 234,
            "bookmark": 123,
            "download": 45
        },
        "top_targets": [
            {
                "target_type": "post",
                "target_id": 1234,
                "count": 89
            },
            {
                "target_type": "post",
                "target_id": 5678,
                "count": 67
            }
        ]
    }
}
```

#### Track Event
```http
POST /analytics/api/track-event
```

Track an analytics event in real-time.

**Request Body:**
```json
{
    "event_type": "click",
    "event_category": "button",
    "target_type": "post",
    "target_id": 1234,
    "event_data": {
        "button": "upvote",
        "page": "/posts/1234"
    },
    "event_value": 1.0,
    "session_id": "session_123456"
}
```

**Required Fields:**
- `event_type` - Type of event (view, click, vote, comment, search, share, bookmark, download, session)

**Optional Fields:**
- `event_category` - Category of event
- `target_type` - Type of target (post, comment, user, category)
- `target_id` - ID of target
- `event_data` - Additional event data (JSON object)
- `event_value` - Numerical value for the event
- `session_id` - Session identifier

**Example Response:**
```json
{
    "success": true,
    "event_id": 123456,
    "message": "Event tracked successfully"
}
```

---

### User Behavior API

#### Get User Behavior
```http
GET /analytics/api/user-behavior/<user_id>
```

Retrieve comprehensive user behavior analytics.

**Path Parameters:**
- `user_id` - ID of the user

**Example Request:**
```http
GET /analytics/api/user-behavior/1
```

**Example Response:**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "total_sessions": 45,
        "avg_session_duration": 25.5,
        "engagement_score": 78.5,
        "engagement_level": "engaged",
        "posts_created": 12,
        "comments_created": 34,
        "votes_cast": 67,
        "posts_viewed": 234,
        "most_active_hour": 14,
        "most_active_day": 3,
        "activity_consistency": 0.75,
        "primary_device_type": "desktop",
        "primary_browser": "chrome",
        "primary_os": "windows",
        "first_seen": "2026-04-01T10:00:00Z",
        "last_active": "2026-05-11T15:30:00Z",
        "insights": {
            "activity_pattern": "weekday_active",
            "engagement_trend": "increasing",
            "recommendations": [
                "User shows high engagement during weekday afternoons",
                "Consider targeting content recommendations for 14:00-16:00",
                "User prefers desktop platform - optimize experience accordingly"
            ]
        }
    }
}
```

#### Get User Behavior Insights
```http
GET /analytics/api/user-behavior/<user_id>/insights
```

Retrieve behavioral insights and recommendations for a user.

**Path Parameters:**
- `user_id` - ID of the user

**Example Response:**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "insights": {
            "engagement_level": "highly_engaged",
            "activity_pattern": "consistent_weekday_active",
            "content_preferences": {
                "top_categories": ["technology", "programming", "web-development"],
                "preferred_content_type": "tutorial",
                "avg_reading_time": 12.5
            },
            "behavior_patterns": {
                "peak_activity_hours": [14, 15, 16],
                "most_active_days": [2, 3, 4],
                "session_duration_trend": "increasing"
            },
            "recommendations": [
                {
                    "type": "content",
                    "priority": "high",
                    "message": "User shows high interest in programming tutorials - recommend advanced content"
                },
                {
                    "type": "engagement",
                    "priority": "medium",
                    "message": "Peak activity at 14:00-16:00 - schedule important notifications during this time"
                }
            ]
        }
    }
}
```

---

### Content Performance API

#### Get Content Performance
```http
GET /analytics/api/content-performance/<content_type>/<content_id>
```

Retrieve performance metrics for specific content.

**Path Parameters:**
- `content_type` - Type of content (post, comment)
- `content_id` - ID of the content

**Example Request:**
```http
GET /analytics/api/content-performance/post/1234
```

**Example Response:**
```json
{
    "success": true,
    "data": {
        "content_type": "post",
        "content_id": 1234,
        "total_views": 567,
        "unique_views": 456,
        "avg_view_duration": 125.5,
        "total_votes": 89,
        "upvotes": 78,
        "downvotes": 11,
        "vote_ratio": 0.88,
        "weighted_score": 156.7,
        "total_comments": 23,
        "shares_count": 12,
        "bookmarks_count": 34,
        "quality_score": 82.5,
        "engagement_score": 76.8,
        "performance_score": 79.6,
        "view_trend": "increasing",
        "engagement_trend": "stable",
        "performance_trend": "increasing",
        "first_viewed": "2026-05-01T10:00:00Z",
        "last_viewed": "2026-05-11T15:30:00Z",
        "insights": {
            "performance_level": "high_performing",
            "engagement_quality": "high",
            "view_velocity": "steady_growth",
            "recommendations": [
                "Content shows strong performance - consider featuring",
                "High engagement quality - good for educational content",
                "Steady view growth indicates lasting value"
            ]
        }
    }
}
```

#### Get Top Performing Content
```http
GET /analytics/api/content-performance/top
```

Retrieve top performing content based on specified metrics.

**Parameters:**
- `content_type` (optional) - Filter by content type (post, comment) (default: post)
- `metric` (optional) - Sort by metric (performance_score, engagement_score, total_views, total_votes) (default: performance_score)
- `limit` (optional) - Maximum number of results (default: 10)

**Example Request:**
```http
GET /analytics/api/content-performance/top?content_type=post&metric=performance_score&limit=5
```

**Example Response:**
```json
{
    "success": true,
    "data": {
        "content_type": "post",
        "metric": "performance_score",
        "results": [
            {
                "content_id": 1234,
                "title": "Advanced Flask Tutorial",
                "performance_score": 89.5,
                "engagement_score": 87.2,
                "total_views": 1234,
                "total_votes": 156,
                "vote_ratio": 0.92,
                "total_comments": 45
            },
            {
                "content_id": 5678,
                "title": "Python Best Practices",
                "performance_score": 85.3,
                "engagement_score": 82.1,
                "total_views": 987,
                "total_votes": 134,
                "vote_ratio": 0.89,
                "total_comments": 38
            }
        ]
    }
}
```

---

### System Metrics API

#### Get System Health
```http
GET /analytics/api/system-health
```

Retrieve overall system health status and metrics.

**Example Response:**
```json
{
    "success": true,
    "data": {
        "overall_status": "healthy",
        "critical_issues": [],
        "warnings": [],
        "healthy_metrics": [
            {
                "metric": "avg_response_time",
                "category": "performance",
                "current_value": 125.5,
                "unit": "ms",
                "status": "healthy",
                "threshold_warning": 500.0,
                "threshold_critical": 1000.0
            },
            {
                "metric": "cpu_usage",
                "category": "performance",
                "current_value": 45.2,
                "unit": "%",
                "status": "healthy",
                "threshold_warning": 70.0,
                "threshold_critical": 90.0
            },
            {
                "metric": "memory_usage",
                "category": "performance",
                "current_value": 67.8,
                "unit": "%",
                "status": "healthy",
                "threshold_warning": 80.0,
                "threshold_critical": 95.0
            }
        ],
        "total_metrics": 15,
        "last_updated": "2026-05-11T23:00:00Z",
        "summary": {
            "healthy_count": 15,
            "warning_count": 0,
            "critical_count": 0
        }
    }
}
```

#### Get Performance Metrics
```http
GET /analytics/api/system-metrics/performance
```

Retrieve performance-related system metrics.

**Example Response:**
```json
{
    "success": true,
    "data": {
        "response_time": {
            "current": 125.5,
            "average": 145.2,
            "min": 89.3,
            "max": 234.7,
            "unit": "ms",
            "trend": "improving"
        },
        "cpu_usage": {
            "current": 45.2,
            "average": 52.8,
            "min": 23.1,
            "max": 78.9,
            "unit": "%",
            "trend": "stable"
        },
        "memory_usage": {
            "current": 67.8,
            "average": 71.4,
            "min": 45.6,
            "max": 89.2,
            "unit": "%",
            "trend": "stable"
        },
        "disk_usage": {
            "current": 78.9,
            "average": 76.5,
            "min": 72.1,
            "max": 82.3,
            "unit": "%",
            "trend": "increasing"
        },
        "requests_per_second": {
            "current": 45.7,
            "average": 52.3,
            "min": 12.4,
            "max": 123.8,
            "unit": "req/s",
            "trend": "stable"
        }
    }
}
```

#### Get User Metrics
```http
GET /analytics/api/system-metrics/users
```

Retrieve user-related system metrics.

**Example Response:**
```json
{
    "success": true,
    "data": {
        "active_users": {
            "current": 234,
            "average": 198.5,
            "min": 45,
            "max": 456,
            "unit": "users",
            "trend": "increasing"
        },
        "concurrent_sessions": {
            "current": 156,
            "average": 134.2,
            "min": 23,
            "max": 289,
            "unit": "sessions",
            "trend": "stable"
        },
        "new_users_today": {
            "current": 12,
            "average": 8.5,
            "min": 2,
            "max": 23,
            "unit": "users",
            "trend": "increasing"
        },
        "user_retention": {
            "daily": 0.78,
            "weekly": 0.65,
            "monthly": 0.52,
            "unit": "ratio",
            "trend": "stable"
        }
    }
}
```

---

### Real-time Metrics API

#### Get Real-time Metrics
```http
GET /analytics/api/real-time-metrics
```

Retrieve current real-time system metrics.

**Example Response:**
```json
{
    "success": true,
    "data": {
        "active_users": 234,
        "requests_per_minute": 45,
        "system_load": 0.65,
        "memory_usage": 67.8,
        "disk_usage": 78.9,
        "cache_hit_rate": 0.85,
        "database_connections": 12,
        "error_rate": 0.02,
        "timestamp": "2026-05-11T23:30:00Z"
    }
}
```

---

### Trends API

#### Get Trend Analysis
```http
GET /analytics/api/trends
```

Retrieve trend analysis data with optional filtering.

**Parameters:**
- `target_type` - Type of target (user, content, system, category)
- `target_id` (optional) - ID of specific target
- `metric_name` - Name of metric to analyze
- `period_days` (optional) - Analysis period in days (default: 30)
- `analysis_type` (optional) - Type of analysis (linear, polynomial, exponential, seasonal) (default: linear)

**Example Request:**
```http
GET /analytics/api/trends?target_type=user&target_id=1&metric_name=engagement_score&period_days=30
```

**Example Response:**
```json
{
    "success": true,
    "data": {
        "target_type": "user",
        "target_id": 1,
        "metric_name": "engagement_score",
        "period_days": 30,
        "analysis_type": "linear",
        "trend_direction": "increasing",
        "trend_strength": 0.75,
        "slope": 0.23,
        "correlation": 0.89,
        "confidence_level": 0.95,
        "current_value": 78.5,
        "predicted_value_7d": 80.1,
        "predicted_value_30d": 85.4,
        "prediction_confidence": 0.82,
        "is_anomaly": false,
        "has_seasonality": false,
        "data_points": [
            {
                "date": "2026-04-11",
                "value": 72.3
            },
            {
                "date": "2026-04-12",
                "value": 73.1
            }
        ],
        "insights": [
            "User engagement shows steady upward trend",
            "Strong correlation suggests reliable pattern",
            "No anomalies detected in the analyzed period"
        ]
    }
}
```

---

## 📊 Data Models

### AnalyticsEvent
```json
{
    "id": 123456,
    "event_type": "click",
    "event_category": "button",
    "user_id": 1,
    "session_id": "session_123456",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "target_type": "post",
    "target_id": 1234,
    "event_data": {
        "button": "upvote",
        "page": "/posts/1234"
    },
    "event_value": 1.0,
    "created_at": "2026-05-11T15:30:00Z",
    "processed_at": "2026-05-11T15:30:01Z"
}
```

### UserBehavior
```json
{
    "id": 1,
    "user_id": 1,
    "total_sessions": 45,
    "avg_session_duration": 25.5,
    "engagement_score": 78.5,
    "posts_created": 12,
    "comments_created": 34,
    "votes_cast": 67,
    "posts_viewed": 234,
    "most_active_hour": 14,
    "most_active_day": 3,
    "activity_consistency": 0.75,
    "primary_device_type": "desktop",
    "primary_browser": "chrome",
    "primary_os": "windows",
    "first_seen": "2026-04-01T10:00:00Z",
    "last_active": "2026-05-11T15:30:00Z",
    "updated_at": "2026-05-11T15:30:00Z"
}
```

### ContentPerformance
```json
{
    "id": 1,
    "content_type": "post",
    "content_id": 1234,
    "total_views": 567,
    "unique_views": 456,
    "avg_view_duration": 125.5,
    "total_votes": 89,
    "upvotes": 78,
    "downvotes": 11,
    "vote_ratio": 0.88,
    "weighted_score": 156.7,
    "total_comments": 23,
    "shares_count": 12,
    "bookmarks_count": 34,
    "quality_score": 82.5,
    "engagement_score": 76.8,
    "performance_score": 79.6,
    "view_trend": "increasing",
    "engagement_trend": "stable",
    "performance_trend": "increasing",
    "first_viewed": "2026-05-01T10:00:00Z",
    "last_viewed": "2026-05-11T15:30:00Z",
    "created_at": "2026-05-01T10:00:00Z",
    "updated_at": "2026-05-11T15:30:00Z"
}
```

### SystemMetrics
```json
{
    "id": 1,
    "metric_type": "performance",
    "metric_category": "response_time",
    "metric_name": "avg_response_time",
    "current_value": 125.5,
    "previous_value": 134.2,
    "min_value": 89.3,
    "max_value": 234.7,
    "avg_value": 145.2,
    "health_status": "healthy",
    "threshold_warning": 500.0,
    "threshold_critical": 1000.0,
    "response_time": 125.5,
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 78.9,
    "network_io": 12.3,
    "active_users": 234,
    "concurrent_sessions": 156,
    "requests_per_second": 45.7,
    "error_rate": 0.02,
    "db_connections": 12,
    "db_query_time": 25.3,
    "db_size": 1024.5,
    "cache_hit_rate": 0.85,
    "metric_data": {
        "percentile_95": 234.7,
        "percentile_99": 345.6
    },
    "tags": ["performance", "api", "response_time"],
    "recorded_at": "2026-05-11T15:30:00Z",
    "updated_at": "2026-05-11T15:30:00Z"
}
```

---

## 🔧 Error Handling

### Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Access denied |
| `NOT_FOUND` | 404 | Resource not found |
| `METHOD_NOT_ALLOWED` | 405 | HTTP method not allowed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Error Response Format
```json
{
    "success": false,
    "error": "Invalid request parameters",
    "error_code": "INVALID_REQUEST",
    "details": {
        "field": "user_id",
        "message": "User ID must be a positive integer"
    }
}
```

---

## 📈 Rate Limiting

### Rate Limits
- **Events API**: 100 requests per minute per user
- **User Behavior API**: 50 requests per minute per user
- **Content Performance API**: 50 requests per minute per user
- **System Metrics API**: 200 requests per minute per user
- **Real-time Metrics API**: 60 requests per minute per user
- **Trends API**: 30 requests per minute per user

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1652304000
```

---

## 🧪 Testing Examples

### JavaScript Client Example
```javascript
// Track an event
async function trackEvent(eventData) {
    try {
        const response = await fetch('/analytics/api/track-event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(eventData)
        });
        
        const result = await response.json();
        if (result.success) {
            console.log('Event tracked:', result.event_id);
        } else {
            console.error('Tracking failed:', result.error);
        }
    } catch (error) {
        console.error('Network error:', error);
    }
}

// Get system health
async function getSystemHealth() {
    try {
        const response = await fetch('/analytics/api/system-health');
        const result = await response.json();
        
        if (result.success) {
            console.log('System health:', result.data.overall_status);
            return result.data;
        } else {
            console.error('Failed to get health:', result.error);
        }
    } catch (error) {
        console.error('Network error:', error);
    }
}
```

### Python Client Example
```python
import requests
from datetime import datetime

class AnalyticsClient:
    def __init__(self, base_url, session):
        self.base_url = base_url
        self.session = session
    
    def track_event(self, event_type, event_category=None, target_type=None, 
                   target_id=None, event_data=None, event_value=None):
        """Track an analytics event"""
        data = {
            'event_type': event_type,
            'event_category': event_category,
            'target_type': target_type,
            'target_id': target_id,
            'event_data': event_data,
            'event_value': event_value
        }
        
        response = self.session.post(
            f'{self.base_url}/track-event',
            json=data
        )
        
        return response.json()
    
    def get_user_behavior(self, user_id):
        """Get user behavior analytics"""
        response = self.session.get(
            f'{self.base_url}/user-behavior/{user_id}'
        )
        
        return response.json()
    
    def get_system_health(self):
        """Get system health status"""
        response = self.session.get(
            f'{self.base_url}/system-health'
        )
        
        return response.json()

# Usage example
client = AnalyticsClient('/analytics/api', requests.Session())

# Track an event
result = client.track_event(
    event_type='click',
    event_category='button',
    target_type='post',
    target_id=1234,
    event_data={'button': 'upvote'},
    event_value=1.0
)

# Get user behavior
user_behavior = client.get_user_behavior(1)

# Get system health
health = client.get_system_health()
```

---

## 📚 SDK Examples

### Node.js SDK
```javascript
class AnalyticsSDK {
    constructor(baseURL, authToken) {
        this.baseURL = baseURL;
        this.authToken = authToken;
    }
    
    async trackEvent(eventType, options = {}) {
        const payload = {
            event_type: eventType,
            ...options
        };
        
        const response = await fetch(`${this.baseURL}/track-event`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.authToken}`
            },
            body: JSON.stringify(payload)
        });
        
        return response.json();
    }
    
    async getUserBehavior(userId) {
        const response = await fetch(`${this.baseURL}/user-behavior/${userId}`, {
            headers: {
                'Authorization': `Bearer ${this.authToken}`
            }
        });
        
        return response.json();
    }
    
    async getSystemHealth() {
        const response = await fetch(`${this.baseURL}/system-health`, {
            headers: {
                'Authorization': `Bearer ${this.authToken}`
            }
        });
        
        return response.json();
    }
}

// Usage
const analytics = new AnalyticsSDK('/analytics/api', 'your-auth-token');

await analytics.trackEvent('click', {
    event_category: 'button',
    target_type: 'post',
    target_id: 1234,
    event_data: { button: 'upvote' }
});

const userBehavior = await analytics.getUserBehavior(1);
const systemHealth = await analytics.getSystemHealth();
```

---

## 🔍 WebSocket Support

### Real-time Updates
For real-time analytics updates, connect to the WebSocket endpoint:

```javascript
const ws = new WebSocket('ws://localhost:5000/analytics/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'system_health':
            updateSystemHealthDisplay(data.data);
            break;
        case 'real_time_metrics':
            updateMetricsDisplay(data.data);
            break;
        case 'user_activity':
            updateUserActivityDisplay(data.data);
            break;
    }
};
```

### WebSocket Events
- `system_health` - System health status updates
- `real_time_metrics` - Real-time metric updates
- `user_activity` - User activity notifications
- `content_performance` - Content performance updates

---

## 📞 Support

### Getting Help
1. **Documentation**: Check this comprehensive API reference
2. **Examples**: Review the testing examples and SDK implementations
3. **Troubleshooting**: Check error codes and common issues
4. **Community**: Post questions in the developer forum

### Reporting Issues
When reporting issues, please include:
- API endpoint and method
- Request parameters and body
- Response status and body
- Error messages and codes
- Timestamp of the request

---

**API Version:** 1.0.0  
**Last Updated:** May 11, 2026  
**Base URL:** `/analytics/api`  
**Status:** Production Ready
