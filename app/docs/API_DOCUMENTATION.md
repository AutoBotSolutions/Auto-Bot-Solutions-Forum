# API Documentation

**Version:** 1.0.0  
**Implementation Date:** May 12, 2026  
**Status:** Production Ready  
**API Coverage:** Complete for all user management systems

---

## Overview

This document provides comprehensive API documentation for all user management systems including preference management, social features, analytics, role management, and advanced permission management.

---

## Table of Contents

1. [Authentication](#authentication)
2. [User Preferences API](#user-preferences-api)
3. [Social Features API](#social-features-api)
4. [Analytics API](#analytics-api)
5. [Role Management API](#role-management-api)
6. [Permission Management API](#permission-management-api)
7. [Profile Customization API](#profile-customization-api)
8. [Infrastructure API](#infrastructure-api)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)

---

## Authentication

All API endpoints require authentication using JWT tokens or session-based authentication.

### Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Authentication Endpoints

#### POST /api/auth/login
Login user and receive authentication token.

**Request:**
```json
{
    "username": "user@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": 1,
            "username": "user@example.com",
            "email": "user@example.com"
        },
        "expires_in": 3600
    }
}
```

---

## User Preferences API

### GET /api/user/preferences
Get current user's preferences.

**Response:**
```json
{
    "success": true,
    "data": {
        "general": {
            "theme_preference": "light",
            "language_preference": "en",
            "timezone": "UTC",
            "date_format": "MM/DD/YYYY",
            "time_format": "12-hour"
        },
        "notifications": {
            "email_notifications": true,
            "push_notifications": true,
            "in_app_notifications": true,
            "quiet_hours": {
                "enabled": false,
                "start": "22:00",
                "end": "08:00"
            }
        },
        "privacy": {
            "searchable": true,
            "indexable": true,
            "public_profile": true,
            "allow_tagging": true,
            "allow_mentions": true
        },
        "accessibility": {
            "font_size": "medium",
            "high_contrast": false,
            "reduce_motion": false,
            "dyslexia_font": false
        },
        "display": {
            "show_sensitive_content": false,
            "auto_play_videos": true,
            "show_avatars": true,
            "show_signatures": true
        }
    }
}
```

### PUT /api/user/preferences
Update user preferences.

**Request:**
```json
{
    "general": {
        "theme_preference": "dark",
        "language_preference": "es",
        "timezone": "EST"
    },
    "notifications": {
        "email_notifications": false,
        "quiet_hours": {
            "enabled": true,
            "start": "22:00",
            "end": "08:00"
        }
    }
}
```

**Response:**
```json
{
    "success": true,
    "message": "Preferences updated successfully",
    "data": {
        "updated_preferences": {...}
    }
}
```

### GET /api/user/preferences/general
Get general preferences only.

**Response:**
```json
{
    "success": true,
    "data": {
        "theme_preference": "light",
        "language_preference": "en",
        "timezone": "UTC",
        "date_format": "MM/DD/YYYY",
        "time_format": "12-hour"
    }
}
```

### PUT /api/user/preferences/general
Update general preferences.

### GET /api/user/preferences/notifications
Get notification preferences.

### PUT /api/user/preferences/notifications
Update notification preferences.

### GET /api/user/preferences/privacy
Get privacy preferences.

### PUT /api/user/preferences/privacy
Update privacy preferences.

### GET /api/user/preferences/accessibility
Get accessibility preferences.

### PUT /api/user/preferences/accessibility
Update accessibility preferences.

---

## Social Features API

### GET /api/social/following
Get users that current user is following.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20)
- `search` (string): Search term

**Response:**
```json
{
    "success": true,
    "data": {
        "following": [
            {
                "id": 2,
                "username": "user2",
                "email": "user2@example.com",
                "followed_at": "2026-05-12T10:00:00Z",
                "mutual": true
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 1,
            "pages": 1
        }
    }
}
```

### POST /api/social/follow/{user_id}
Follow a user.

**Response:**
```json
{
    "success": true,
    "message": "User followed successfully",
    "data": {
        "follow": {
            "id": 2,
            "username": "user2",
            "followed_at": "2026-05-12T10:00:00Z"
        }
    }
}
```

### DELETE /api/social/follow/{user_id}
Unfollow a user.

### GET /api/social/followers
Get users that follow current user.

### GET /api/social/friends
Get user's friends (mutual follows).

### POST /api/social/friend-request/{user_id}
Send friend request.

### PUT /api/social/friend-request/{request_id}/accept
Accept friend request.

### PUT /api/social/friend-request/{request_id}/reject
Reject friend request.

### GET /api/social/feed
Get social activity feed.

**Query Parameters:**
- `page` (int): Page number
- `per_page` (int): Items per page
- `filter` (string): Filter by activity type
- `search` (string): Search term

**Response:**
```json
{
    "success": true,
    "data": {
        "feed": [
            {
                "id": 1,
                "user": {
                    "id": 2,
                    "username": "user2",
                    "avatar_url": "/uploads/avatars/user2.jpg"
                },
                "activity_type": "post",
                "activity_data": {
                    "content": "Hello world!",
                    "post_id": 123
                },
                "created_at": "2026-05-12T10:00:00Z"
            }
        ],
        "pagination": {...}
    }
}
```

### GET /api/social/recommendations
Get user recommendations.

**Response:**
```json
{
    "success": true,
    "data": {
        "recommendations": [
            {
                "user": {
                    "id": 3,
                    "username": "user3",
                    "bio": "Interesting user bio"
                },
                "reason": "Similar interests",
                "score": 0.85
            }
        ]
    }
}
```

### GET /api/social/groups
Get user's groups.

### POST /api/social/groups
Create new group.

### GET /api/social/groups/{group_id}
Get group details.

### PUT /api/social/groups/{group_id}
Update group details.

### DELETE /api/social/groups/{group_id}
Delete group.

### POST /api/social/groups/{group_id}/join
Join group.

### DELETE /api/social/groups/{group_id}/leave
Leave group.

---

## Analytics API

### GET /api/analytics/dashboard
Get analytics dashboard data.

**Query Parameters:**
- `period` (string): Time period (7d, 30d, 90d)
- `start_date` (date): Start date
- `end_date` (date): End date

**Response:**
```json
{
    "success": true,
    "data": {
        "overview": {
            "total_behaviors": 150,
            "engagement_score": 75.5,
            "active_days": 25,
            "growth_rate": 12.3
        },
        "behaviors": {
            "login_count": 45,
            "post_count": 23,
            "comment_count": 67,
            "like_count": 15
        },
        "engagement": {
            "daily_engagement": [
                {"date": "2026-05-12", "score": 85.2},
                {"date": "2026-05-11", "score": 72.1}
            ],
            "engagement_trend": "up"
        },
        "performance": {
            "avg_response_time": 0.245,
            "page_load_time": 1.2,
            "interaction_rate": 0.68
        }
    }
}
```

### GET /api/analytics/behaviors
Get user behavior analytics.

**Query Parameters:**
- `behavior_type` (string): Filter by behavior type
- `start_date` (date): Start date
- `end_date` (date): End date
- `limit` (int): Limit results

**Response:**
```json
{
    "success": true,
    "data": {
        "behaviors": [
            {
                "id": 1,
                "behavior_type": "login",
                "action": "success",
                "behavior_metadata": {
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0..."
                },
                "created_at": "2026-05-12T10:00:00Z"
            }
        ],
        "summary": {
            "total_behaviors": 150,
            "behavior_types": {
                "login": 45,
                "post": 23,
                "comment": 67,
                "like": 15
            }
        }
    }
}
```

### GET /api/analytics/engagement
Get engagement analytics.

### GET /api/analytics/performance
Get performance analytics.

### GET /api/analytics/segments
Get user segments.

### POST /api/analytics/segments
Create new user segment.

### GET /api/analytics/segments/{segment_id}
Get segment details.

### PUT /api/analytics/segments/{segment_id}
Update segment details.

### DELETE /api/analytics/segments/{segment_id}
Delete segment.

### GET /api/analytics/predictions
Get predictive analytics.

### POST /api/analytics/track
Track user behavior event.

**Request:**
```json
{
    "behavior_type": "custom_action",
    "action": "button_click",
    "behavior_metadata": {
        "button_id": "submit_button",
        "page": "/dashboard"
    }
}
```

### GET /api/analytics/export
Export analytics data.

**Query Parameters:**
- `format` (string): Export format (csv, json, excel)
- `start_date` (date): Start date
- `end_date` (date): End date
- `data_type` (string): Data type (behaviors, engagement, performance)

---

## Role Management API

### GET /api/roles
Get all available roles.

**Response:**
```json
{
    "success": true,
    "data": {
        "roles": [
            {
                "id": 1,
                "name": "admin",
                "display_name": "Administrator",
                "description": "System administrator",
                "color": "#dc3545",
                "icon": "admin",
                "level": 100,
                "is_active": true,
                "permissions": {
                    "users_manage": true,
                    "content_manage": true
                }
            }
        ]
    }
}
```

### GET /api/roles/{role_id}
Get role details.

### POST /api/roles
Create new role (admin only).

**Request:**
```json
{
    "name": "moderator",
    "display_name": "Moderator",
    "description": "Content moderator",
    "color": "#28a745",
    "icon": "moderator",
    "level": 50,
    "permissions": {
        "content_moderate": true,
        "users_warn": true
    }
}
```

### PUT /api/roles/{role_id}
Update role (admin only).

### DELETE /api/roles/{role_id}
Delete role (admin only).

### GET /api/roles/user
Get current user's roles.

**Response:**
```json
{
    "success": true,
    "data": {
        "roles": [
            {
                "id": 2,
                "name": "member",
                "display_name": "Member",
                "assigned_at": "2026-05-12T10:00:00Z",
                "expires_at": null,
                "is_active": true
            }
        ]
    }
}
```

### POST /api/roles/request
Request role assignment.

**Request:**
```json
{
    "role_id": 3,
    "reason": "I want to contribute to the community",
    "request_type": "request"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Role request submitted successfully",
    "data": {
        "request": {
            "id": 1,
            "status": "pending",
            "requested_at": "2026-05-12T10:00:00Z"
        }
    }
}
```

### GET /api/roles/requests
Get user's role requests.

### GET /api/roles/requests/pending
Get pending role requests (admin only).

### PUT /api/roles/requests/{request_id}/approve
Approve role request (admin only).

**Request:**
```json
{
    "comment": "Approved for community contribution",
    "expires_at": "2026-12-31T23:59:59Z"
}
```

### PUT /api/roles/requests/{request_id}/reject
Reject role request (admin only).

**Request:**
```json
{
    "comment": "Not eligible yet, need more activity"
}
```

### GET /api/roles/history
Get role assignment history.

**Response:**
```json
{
    "success": true,
    "data": {
        "history": [
            {
                "id": 1,
                "role": {
                    "id": 2,
                    "name": "member",
                    "display_name": "Member"
                },
                "action_type": "assigned",
                "action_reason": "Automatic assignment",
                "assigned_by": {
                    "id": 1,
                    "username": "admin"
                },
                "created_at": "2026-05-12T10:00:00Z"
            }
        ]
    }
}
```

### GET /api/roles/analytics
Get role analytics (admin only).

### POST /api/roles/bulk-assign
Bulk assign roles (admin only).

**Request:**
```json
{
    "user_ids": [1, 2, 3],
    "role_id": 2,
    "reason": "Bulk assignment for new members"
}
```

### POST /api/roles/bulk-remove
Bulk remove roles (admin only).

---

## Permission Management API

### GET /api/permissions
Get all permissions.

**Response:**
```json
{
    "success": true,
    "data": {
        "permissions": [
            {
                "id": 1,
                "name": "users_manage",
                "display_name": "Manage Users",
                "description": "Can manage user accounts",
                "category": "user",
                "resource": "users",
                "action": "manage",
                "is_system_permission": true
            }
        ]
    }
}
```

### GET /api/permissions/granular
Get granular permissions.

### POST /api/permissions/granular
Create granular permission (admin only).

**Request:**
```json
{
    "name": "advanced_content_create",
    "display_name": "Advanced Content Creation",
    "description": "Create advanced content with conditions",
    "category": "content",
    "resource": "posts",
    "action": "create_advanced",
    "conditions": {
        "min_user_level": 5,
        "require_verified": true,
        "min_registration_days": 30
    }
}
```

### GET /api/permissions/check
Check user permission.

**Request:**
```json
{
    "permission_name": "users_manage",
    "resource_id": 123,
    "resource_type": "user"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "has_permission": true,
        "permission": {
            "id": 1,
            "name": "users_manage",
            "display_name": "Manage Users"
        },
        "conditions_met": true,
        "checked_at": "2026-05-12T10:00:00Z"
    }
}
```

### GET /api/permissions/audit
Get permission audit logs (admin only).

### GET /api/permissions/analytics
Get permission analytics (admin only).

### POST /api/permissions/inheritance
Create permission inheritance (admin only).

### GET /api/permissions/user/{user_id}
Get user's permissions.

---

## Profile Customization API

### GET /api/profile/customization
Get profile customization settings.

**Response:**
```json
{
    "success": true,
    "data": {
        "profile_theme": "light",
        "profile_skin": "default",
        "profile_banner_url": "/uploads/banners/user1.jpg",
        "profile_layout": "grid",
        "profile_widgets": [
            {
                "type": "about",
                "position": "top-left",
                "enabled": true
            }
        ],
        "profile_privacy": {
            "show_badges": true,
            "show_stats": true,
            "show_activity": true
        },
        "profile_custom_css": ".custom-style { color: blue; }",
        "profile_color_scheme": {
            "primary": "#007bff",
            "secondary": "#6c757d"
        }
    }
}
```

### PUT /api/profile/customization
Update profile customization.

**Request:**
```json
{
    "profile_theme": "dark",
    "profile_layout": "list",
    "profile_widgets": [
        {
            "type": "about",
            "position": "top-left",
            "enabled": true
        },
        {
            "type": "stats",
            "position": "top-right",
            "enabled": true
        }
    ]
}
```

### GET /api/profile/themes
Get available themes.

**Response:**
```json
{
    "success": true,
    "data": {
        "themes": [
            {
                "id": "light",
                "name": "Light Theme",
                "description": "Clean light theme",
                "preview": "/themes/light/preview.png"
            },
            {
                "id": "dark",
                "name": "Dark Theme",
                "description": "Dark theme for low-light environments",
                "preview": "/themes/dark/preview.png"
            }
        ]
    }
}
```

### GET /api/profile/themes/{theme_id}
Get theme CSS.

### POST /api/profile/themes
Create custom theme.

### PUT /api/profile/banner
Upload profile banner.

### DELETE /api/profile/banner
Remove profile banner.

---

## Infrastructure API

### GET /api/infrastructure/profile/storage
Get profile storage information.

**Response:**
```json
{
    "success": true,
    "data": {
        "storage_path": "/uploads/profiles",
        "directories": {
            "avatars": "/uploads/profiles/avatars",
            "banners": "/uploads/profiles/banners",
            "themes": "/uploads/profiles/themes"
        },
        "usage": {
            "total_size": "15.2 MB",
            "file_count": 156
        }
    }
}
```

### POST /api/infrastructure/profile/backup
Create profile backup.

### GET /api/infrastructure/profile/backup/{backup_id}
Get profile backup.

### POST /api/infrastructure/profile/restore/{backup_id}
Restore profile backup.

### GET /api/infrastructure/social/graph
Get social graph data.

**Query Parameters:**
- `depth` (int): Graph depth (default: 2)
- `user_id` (int): User ID (optional, defaults to current user)

### GET /api/infrastructure/analytics/warehouse
Get analytics data warehouse.

### POST /api/infrastructure/analytics/real-time
Process real-time analytics event.

### GET /api/infrastructure/analytics/visualization
Generate analytics visualization.

**Query Parameters:**
- `chart_type` (string): Chart type (line, pie, bar)
- `period` (string): Time period (7d, 30d, 90d)
- `metric` (string): Metric to visualize

---

## Error Handling

All API endpoints return consistent error responses.

### Error Response Format
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "field": "email",
            "reason": "Invalid email format"
        }
    }
}
```

### Common Error Codes

- `AUTHENTICATION_REQUIRED`: Authentication required
- `PERMISSION_DENIED`: Insufficient permissions
- `VALIDATION_ERROR`: Input validation failed
- `RESOURCE_NOT_FOUND`: Resource not found
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded
- `INTERNAL_ERROR`: Internal server error

---

## Rate Limiting

API endpoints are rate limited to prevent abuse.

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1649870400
```

### Rate Limits by Endpoint

- Authentication endpoints: 5 requests per minute
- User preferences: 60 requests per minute
- Social features: 100 requests per minute
- Analytics: 200 requests per minute
- Role management: 30 requests per minute
- Permission checks: 500 requests per minute

---

## API Versioning

The API supports versioning through URL paths.

### Current Version: v1
```
/api/v1/user/preferences
/api/v1/social/feed
/api/v1/analytics/dashboard
```

### Version Negotiation
```
Accept: application/vnd.autobot.v1+json
```

---

## Pagination

List endpoints support pagination.

### Pagination Parameters
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)

### Pagination Response
```json
{
    "success": true,
    "data": {
        "items": [...],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 150,
            "pages": 8,
            "has_next": true,
            "has_prev": false
        }
    }
}
```

---

## Search and Filtering

Many endpoints support search and filtering.

### Common Parameters
- `search` (string): Search term
- `filter` (string): Filter by field
- `sort` (string): Sort field
- `order` (string): Sort order (asc, desc)

### Example
```
GET /api/social/feed?search=python&filter=post&sort=created_at&order=desc
```

---

## Webhooks

The API supports webhooks for real-time notifications.

### Webhook Events
- `user.created`: User created
- `user.role_assigned`: Role assigned
- `social.follow`: User followed
- `analytics.behavior`: Behavior tracked

### Webhook Configuration
```json
{
    "url": "https://your-app.com/webhook",
    "events": ["user.created", "social.follow"],
    "secret": "webhook_secret"
}
```

---

**Implementation Status:** ✅ **PRODUCTION READY**  
**Last Updated:** May 12, 2026  
**API Coverage:** Complete for all user management systems  
**Documentation Status:** Comprehensive API reference with examples
