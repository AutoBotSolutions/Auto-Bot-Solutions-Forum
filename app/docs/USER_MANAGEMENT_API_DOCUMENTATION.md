# User Management Systems API Documentation

**Version:** 1.0.0  
**Last Updated:** May 12, 2026  
**Status:** Production Ready - Fully Implemented and Documented

---

## Overview

This document provides comprehensive API documentation for all user management systems implemented in the Auto Bot Solutions Forum. The API follows RESTful principles and provides endpoints for profile customization, user preferences, social features, analytics, and role management.

## Table of Contents

1. [Authentication](#authentication)
2. [Profile Customization API](#profile-customization-api)
3. [User Preferences API](#user-preferences-api)
4. [Social Features API](#social-features-api)
5. [User Analytics API](#user-analytics-api)
6. [Role Management API](#role-management-api)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Response Formats](#response-formats)

---

## Authentication

All API endpoints require authentication using JWT tokens or session-based authentication.

### Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Authentication Endpoints

#### POST `/api/auth/login`
Login user and receive access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "user": {
      "id": 1,
      "username": "string",
      "email": "string"
    }
  }
}
```

#### POST `/api/auth/logout`
Logout user and invalidate token.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## Profile Customization API

### GET `/api/profile/theme`
Get user's current theme settings.

**Response:**
```json
{
  "success": true,
  "data": {
    "theme": "dark",
    "skin": "dark",
    "custom_colors": {
      "primary": "#007bff",
      "secondary": "#6c757d"
    }
  }
}
```

### PUT `/api/profile/theme`
Update user's theme settings.

**Request Body:**
```json
{
  "theme": "dark",
  "skin": "dark",
  "custom_colors": {
    "primary": "#007bff",
    "secondary": "#6c757d"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Theme updated successfully"
}
```

### GET `/api/profile/layout`
Get user's profile layout configuration.

**Response:**
```json
{
  "success": true,
  "data": {
    "layout": "grid",
    "columns": 2,
    "sections": [
      {
        "id": "bio",
        "visible": true,
        "position": 1
      }
    ]
  }
}
```

### PUT `/api/profile/layout`
Update user's profile layout.

**Request Body:**
```json
{
  "layout": "grid",
  "columns": 3,
  "sections": [
    {
      "id": "bio",
      "visible": true,
      "position": 1
    }
  ]
}
```

### GET `/api/profile/widgets`
Get user's profile widget configuration.

**Response:**
```json
{
  "success": true,
  "data": {
    "widgets": [
      {
        "id": "recent_posts",
        "enabled": true,
        "position": "main",
        "limit": 10
      }
    ]
  }
}
```

### PUT `/api/profile/widgets`
Update user's profile widgets.

**Request Body:**
```json
{
  "widgets": [
    {
      "id": "recent_posts",
      "enabled": true,
      "position": "main",
      "limit": 10
    }
  ]
}
```

### GET `/api/profile/privacy`
Get user's privacy settings.

**Response:**
```json
{
  "success": true,
  "data": {
    "public_profile": true,
    "show_email": false,
    "show_location": true,
    "allow_messages": true,
    "allow_friend_requests": true
  }
}
```

### PUT `/api/profile/privacy`
Update user's privacy settings.

**Request Body:**
```json
{
  "public_profile": true,
  "show_email": false,
  "show_location": true,
  "allow_messages": true,
  "allow_friend_requests": true
}
```

### POST `/api/profile/banner`
Update user's profile banner.

**Request Body:**
```json
{
  "banner_url": "https://example.com/banner.jpg"
}
```

### DELETE `/api/profile/banner`
Remove user's profile banner.

**Response:**
```json
{
  "success": true,
  "message": "Banner removed successfully"
}
```

### POST `/api/profile/reset`
Reset profile customizations.

**Request Body:**
```json
{
  "reset_type": "all"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile customizations reset successfully"
}
```

---

## User Preferences API

### GET `/api/preferences/general`
Get user's general preferences.

**Response:**
```json
{
  "success": true,
  "data": {
    "theme_preference": "light",
    "language_preference": "en",
    "timezone": "UTC",
    "date_format": "MM/DD/YYYY",
    "time_format": "12-hour",
    "email_notifications": true,
    "push_notifications": true
  }
}
```

### PUT `/api/preferences/general`
Update user's general preferences.

**Request Body:**
```json
{
  "theme_preference": "dark",
  "language_preference": "es",
  "timezone": "EST",
  "date_format": "DD/MM/YYYY",
  "time_format": "24-hour",
  "email_notifications": false,
  "push_notifications": false
}
```

### GET `/api/preferences/notifications`
Get user's notification preferences.

**Response:**
```json
{
  "success": true,
  "data": {
    "email": {
      "new_follower": true,
      "new_message": true,
      "post_reply": true,
      "comment_reply": true,
      "mention": true,
      "badge_earned": true,
      "system_updates": false
    },
    "push": {
      "new_follower": true,
      "system_updates": false
    },
    "inapp": {
      "new_follower": true,
      "system_updates": false
    },
    "frequency": "immediate",
    "quiet_hours": {
      "enabled": false,
      "start": "22:00",
      "end": "08:00"
    }
  }
}
```

### PUT `/api/preferences/notifications`
Update user's notification preferences.

**Request Body:**
```json
{
  "email": {
    "new_follower": false,
    "new_message": false,
    "post_reply": false,
    "comment_reply": false,
    "mention": false,
    "badge_earned": false,
    "system_updates": true
  },
  "push": {
    "new_follower": false,
    "system_updates": true
  },
  "inapp": {
    "new_follower": false,
    "system_updates": true
  },
  "frequency": "daily",
  "quiet_hours": {
    "enabled": true,
    "start": "23:00",
    "end": "07:00"
  }
}
```

### GET `/api/preferences/accessibility`
Get user's accessibility preferences.

**Response:**
```json
{
  "success": true,
  "data": {
    "font_size": "medium",
    "high_contrast": false,
    "reduce_motion": false,
    "screen_reader_optimized": false,
    "keyboard_navigation": false,
    "color_blind_friendly": false,
    "dyslexia_font": false
  }
}
```

### PUT `/api/preferences/accessibility`
Update user's accessibility preferences.

**Request Body:**
```json
{
  "font_size": "large",
  "high_contrast": true,
  "reduce_motion": true,
  "screen_reader_optimized": true,
  "keyboard_navigation": true,
  "color_blind_friendly": true,
  "dyslexia_font": true
}
```

### GET `/api/preferences/social`
Get user's social preferences.

**Response:**
```json
{
  "success": true,
  "data": {
    "allow_follow_requests": true,
    "allow_friend_requests": true,
    "show_followers_publicly": true,
    "show_following_publicly": true,
    "show_friends_publicly": true,
    "allow_tagging": true,
    "allow_mentions": true,
    "show_activity_publicly": true,
    "searchable": true,
    "indexable": true
  }
}
```

### PUT `/api/preferences/social`
Update user's social preferences.

**Request Body:**
```json
{
  "allow_follow_requests": false,
  "allow_friend_requests": false,
  "show_followers_publicly": false,
  "show_following_publicly": false,
  "show_friends_publicly": false,
  "allow_tagging": false,
  "allow_mentions": false,
  "show_activity_publicly": false,
  "searchable": false,
  "indexable": false
}
```

---

## Social Features API

### Following System

#### POST `/api/social/follow/{user_id}`
Follow a user.

**Response:**
```json
{
  "success": true,
  "message": "User followed successfully",
  "data": {
    "follow_id": 123,
    "created_at": "2026-05-12T10:30:00Z"
  }
}
```

#### DELETE `/api/social/follow/{user_id}`
Unfollow a user.

**Response:**
```json
{
  "success": true,
  "message": "User unfollowed successfully"
}
```

#### GET `/api/social/followers/{user_id}`
Get user's followers.

**Query Parameters:**
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "followers": [
      {
        "id": 1,
        "username": "user1",
        "avatar_url": "https://example.com/avatar.jpg",
        "followed_at": "2026-05-12T10:30:00Z",
        "is_mutual": true,
        "is_close_friend": false
      }
    ],
    "total_count": 150,
    "has_more": true
  }
}
```

#### GET `/api/social/following/{user_id}`
Get users that user is following.

**Response:**
```json
{
  "success": true,
  "data": {
    "following": [
      {
        "id": 2,
        "username": "user2",
        "avatar_url": "https://example.com/avatar2.jpg",
        "followed_at": "2026-05-12T09:30:00Z",
        "is_mutual": true,
        "is_close_friend": false
      }
    ],
    "total_count": 75,
    "has_more": false
  }
}
```

### Friend System

#### POST `/api/social/friends/request`
Send friend request.

**Request Body:**
```json
{
  "user_id": 123,
  "message": "Let's be friends!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Friend request sent",
  "data": {
    "request_id": 456,
    "status": "pending",
    "created_at": "2026-05-12T10:30:00Z"
  }
}
```

#### GET `/api/social/friends/requests`
Get pending friend requests.

**Response:**
```json
{
  "success": true,
  "data": {
    "requests": [
      {
        "id": 456,
        "user": {
          "id": 123,
          "username": "user123",
          "avatar_url": "https://example.com/avatar.jpg"
        },
        "message": "Let's be friends!",
        "created_at": "2026-05-12T10:30:00Z"
      }
    ]
  }
}
```

#### POST `/api/social/friends/respond/{request_id}`
Respond to friend request.

**Request Body:**
```json
{
  "action": "accept",
  "reason": "Happy to connect!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Friend request accepted",
  "data": {
    "friendship_id": 789,
    "status": "accepted",
    "responded_at": "2026-05-12T10:35:00Z"
  }
}
```

#### GET `/api/social/friends/{user_id}`
Get user's friends.

**Response:**
```json
{
  "success": true,
  "data": {
    "friends": [
      {
        "id": 123,
        "username": "friend123",
        "avatar_url": "https://example.com/avatar.jpg",
        "friend_since": "2026-05-10T15:30:00Z",
        "is_close_friend": false,
        "friend_group": "work"
      }
    ],
    "total_count": 25
  }
}
```

### User Groups

#### POST `/api/social/groups`
Create a new user group.

**Request Body:**
```json
{
  "name": "Developers Group",
  "description": "A group for developers",
  "is_private": false,
  "group_type": "custom",
  "color": "#007bff",
  "icon": "code"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Group created successfully",
  "data": {
    "id": 1,
    "name": "Developers Group",
    "description": "A group for developers",
    "is_private": false,
    "group_type": "custom",
    "color": "#007bff",
    "icon": "code",
    "created_at": "2026-05-12T10:30:00Z"
  }
}
```

#### GET `/api/social/groups/{group_id}`
Get group details.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Developers Group",
    "description": "A group for developers",
    "creator_id": 123,
    "is_private": false,
    "group_type": "custom",
    "color": "#007bff",
    "icon": "code",
    "member_count": 15,
    "created_at": "2026-05-12T10:30:00Z",
    "is_member": true,
    "is_admin": false
  }
}
```

#### POST `/api/social/groups/{group_id}/join`
Join a group.

**Response:**
```json
{
  "success": true,
  "message": "Joined group successfully",
  "data": {
    "membership_id": 456,
    "joined_at": "2026-05-12T10:35:00Z"
  }
}
```

#### DELETE `/api/social/groups/{group_id}/leave`
Leave a group.

**Response:**
```json
{
  "success": true,
  "message": "Left group successfully"
}
```

#### GET `/api/social/groups/{group_id}/members`
Get group members.

**Response:**
```json
{
  "success": true,
  "data": {
    "members": [
      {
        "id": 123,
        "username": "member123",
        "avatar_url": "https://example.com/avatar.jpg",
        "is_admin": true,
        "joined_at": "2026-05-12T10:30:00Z"
      }
    ],
    "total_count": 15
  }
}
```

### Activity Feed

#### GET `/api/social/activity/feed`
Get activity feed.

**Query Parameters:**
- `limit`: Number of activities (default: 50)
- `include_friends`: Include friends' activities (default: true)
- `activity_type`: Filter by activity type (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "activities": [
      {
        "id": 1,
        "user": {
          "id": 123,
          "username": "user123",
          "avatar_url": "https://example.com/avatar.jpg"
        },
        "activity_type": "post",
        "action": "created",
        "description": "User created a new post",
        "target_type": "post",
        "target_id": 456,
        "created_at": "2026-05-12T10:30:00Z",
        "metadata": {
          "title": "My New Post"
        }
      }
    ],
    "has_more": true
  }
}
```

### Recommendations

#### GET `/api/social/recommendations`
Get user recommendations.

**Query Parameters:**
- `type`: Recommendation type (follow, friend, similar_interests)
- `limit`: Number of recommendations (default: 20)

**Response:**
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "id": 789,
        "recommended_user": {
          "id": 456,
          "username": "recommended_user",
          "avatar_url": "https://example.com/avatar.jpg",
          "bio": "Software developer"
        },
        "recommendation_type": "follow",
        "score": 0.85,
        "reason": "Similar interests in programming",
        "created_at": "2026-05-12T10:30:00Z",
        "expires_at": "2026-06-11T10:30:00Z"
      }
    ]
  }
}
```

#### POST `/api/social/recommendations/{recommendation_id}/dismiss`
Dismiss a recommendation.

**Response:**
```json
{
  "success": true,
  "message": "Recommendation dismissed"
}
```

### Social Sharing

#### POST `/api/social/share`
Share content to social platforms.

**Request Body:**
```json
{
  "content_type": "post",
  "content_id": 123,
  "platform": "twitter",
  "custom_message": "Check out this interesting post!",
  "metadata": {
    "hashtags": ["#programming", "#tech"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Content shared successfully",
  "data": {
    "share_id": 101,
    "platform": "twitter",
    "share_url": "https://twitter.com/share/123",
    "created_at": "2026-05-12T10:30:00Z"
  }
}
```

#### GET `/api/social/shares/{user_id}`
Get user's social shares.

**Query Parameters:**
- `platform`: Filter by platform (optional)
- `content_type`: Filter by content type (optional)
- `limit`: Number of shares (default: 50)

**Response:**
```json
{
  "success": true,
  "data": {
    "shares": [
      {
        "id": 101,
        "content_type": "post",
        "content_id": 123,
        "platform": "twitter",
        "share_url": "https://twitter.com/share/123",
        "custom_message": "Check out this interesting post!",
        "created_at": "2026-05-12T10:30:00Z"
      }
    ],
    "total_count": 25
  }
}
```

---

## User Analytics API

### Behavior Tracking

#### POST `/api/analytics/behavior`
Track user behavior.

**Request Body:**
```json
{
  "behavior_type": "login",
  "action": "logged_in",
  "target_type": "user",
  "target_id": 123,
  "session_id": "session_123",
  "duration": 120,
  "metadata": {
    "device_type": "mobile",
    "browser": "chrome"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Behavior tracked successfully",
  "data": {
    "behavior_id": 456,
    "created_at": "2026-05-12T10:30:00Z"
  }
}
```

#### GET `/api/analytics/behaviors/{user_id}`
Get user behaviors.

**Query Parameters:**
- `behavior_type`: Filter by behavior type (optional)
- `days`: Number of days to look back (default: 30)
- `limit`: Number of results (default: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "behaviors": [
      {
        "id": 456,
        "behavior_type": "login",
        "action": "logged_in",
        "target_type": "user",
        "target_id": 123,
        "session_id": "session_123",
        "duration": 120,
        "created_at": "2026-05-12T10:30:00Z",
        "metadata": {
          "device_type": "mobile",
          "browser": "chrome"
        }
      }
    ],
    "total_count": 150,
    "load_time": 0.05
  }
}
```

### Engagement Metrics

#### GET `/api/analytics/engagement/{user_id}`
Get user engagement metrics.

**Query Parameters:**
- `days`: Number of days to look back (default: 30)

**Response:**
```json
{
  "success": true,
  "data": {
    "trend": [
      {
        "date": "2026-05-12",
        "engagement_score": 75.5,
        "total_actions": 15,
        "login_count": 1,
        "post_count": 3,
        "comment_count": 5,
        "like_count": 7,
        "share_count": 2,
        "view_count": 25,
        "session_duration": 3600,
        "pages_viewed": 12,
        "bounce_rate": 0.2
      }
    ],
    "aggregates": {
      "avg_engagement": 72.3,
      "total_actions": 450,
      "max_engagement": 85.0,
      "min_engagement": 45.0
    },
    "load_time": 0.08
  }
}
```

#### POST `/api/analytics/engagement/calculate`
Calculate engagement metrics for a specific date.

**Request Body:**
```json
{
  "date": "2026-05-12"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Engagement calculated successfully",
  "data": {
    "engagement_id": 789,
    "date": "2026-05-12",
    "engagement_score": 75.5,
    "total_actions": 15
  }
}
```

### Performance Metrics

#### GET `/api/analytics/performance/{user_id}`
Get user performance metrics.

**Query Parameters:**
- `period`: Period type (daily, weekly, monthly)
- `days`: Number of days to look back (default: 30)

**Response:**
```json
{
  "success": true,
  "data": {
    "metrics": {
      "content": [
        {
          "metric_name": "post_count",
          "metric_value": 10.0,
          "previous_value": 8.0,
          "change_percentage": 25.0,
          "period_start": "2026-05-05",
          "period_end": "2026-05-12"
        }
      ],
      "engagement": [
        {
          "metric_name": "average_engagement_score",
          "metric_value": 72.3,
          "previous_value": 68.5,
          "change_percentage": 5.5,
          "period_start": "2026-05-05",
          "period_end": "2026-05-12"
        }
      ]
    },
    "total_metrics": 8,
    "load_time": 0.06
  }
}
```

#### POST `/api/analytics/performance/calculate`
Calculate performance metrics.

**Request Body:**
```json
{
  "period": "weekly"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Performance metrics calculated successfully",
  "data": {
    "calculated_metrics": 5
  }
}
```

### User Segmentation

#### GET `/api/analytics/segments`
Get user segments.

**Response:**
```json
{
  "success": true,
  "data": {
    "segments": [
      {
        "id": 1,
        "name": "Active Users",
        "description": "Users with 5+ posts",
        "segment_type": "activity",
        "user_count": 150,
        "is_active": true,
        "created_at": "2026-05-10T10:30:00Z"
      }
    ]
  }
}
```

#### POST `/api/analytics/segments`
Create a new user segment.

**Request Body:**
```json
{
  "name": "Power Users",
  "description": "Users with 50+ posts",
  "segment_type": "activity",
  "criteria": {
    "min_posts": 50,
    "min_engagement_score": 80.0
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Segment created successfully",
  "data": {
    "id": 2,
    "name": "Power Users",
    "user_count": 25
  }
}
```

#### POST `/api/analytics/segments/{segment_id}/apply`
Apply segmentation to users.

**Response:**
```json
{
  "success": true,
  "message": "Segmentation applied successfully",
  "data": {
    "matched_users": 25,
    "segment_id": 2
  }
}
```

### Predictive Analytics

#### GET `/api/analytics/predictions/{user_id}`
Get user predictions.

**Response:**
```json
{
  "success": true,
  "data": {
    "predictions": [
      {
        "id": 101,
        "prediction_type": "churn",
        "prediction_value": 0.15,
        "confidence": 0.75,
        "target_date": "2026-06-11",
        "created_at": "2026-05-12T10:30:00Z",
        "metadata": {
          "algorithm": "engagement_trend",
          "data_points": 30
        }
      }
    ]
  }
}
```

#### POST `/api/analytics/predictions/generate`
Generate predictions for a user.

**Request Body:**
```json
{
  "prediction_type": "churn",
  "prediction_period": 30
}
```

**Response:**
```json
{
  "success": true,
  "message": "Predictions generated successfully",
  "data": {
    "prediction_id": 102,
    "prediction_type": "churn",
    "prediction_value": 0.15,
    "confidence": 0.75
  }
}
```

### Custom Dashboards

#### GET `/api/analytics/dashboards/{user_id}`
Get user's analytics dashboards.

**Response:**
```json
{
  "success": true,
  "data": {
    "dashboards": [
      {
        "id": 1,
        "name": "My Analytics Dashboard",
        "dashboard_type": "custom",
        "is_default": true,
        "is_public": false,
        "created_at": "2026-05-10T10:30:00Z"
      }
    ]
  }
}
```

#### POST `/api/analytics/dashboards`
Create a new analytics dashboard.

**Request Body:**
```json
{
  "name": "Performance Dashboard",
  "dashboard_type": "performance",
  "layout": {
    "columns": 3,
    "auto_refresh": true,
    "refresh_interval": 300
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Dashboard created successfully",
  "data": {
    "id": 2,
    "name": "Performance Dashboard"
  }
}
```

#### GET `/api/analytics/dashboards/{dashboard_id}/data`
Get dashboard data.

**Response:**
```json
{
  "success": true,
  "data": {
    "widget_1": {
      "type": "stats",
      "title": "User Statistics",
      "data": {
        "posts": 25,
        "comments": 50,
        "likes": 100,
        "engagement": 75.5
      }
    },
    "widget_2": {
      "type": "chart",
      "title": "Engagement Trend",
      "data": {
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "values": [65, 70, 75, 72, 78]
      }
    }
  }
}
```

---

## Role Management API

### Roles

#### GET `/api/roles`
Get all roles.

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
        "level": 100,
        "is_active": true,
        "is_system_role": true,
        "is_admin_role": true,
        "user_count": 5,
        "created_at": "2026-05-01T10:30:00Z"
      }
    ]
  }
}
```

#### POST `/api/roles`
Create a new role.

**Request Body:**
```json
{
  "name": "content_manager",
  "display_name": "Content Manager",
  "description": "Manages content and posts",
  "level": 50,
  "color": "#007bff",
  "icon": "edit",
  "is_admin_role": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Role created successfully",
  "data": {
    "id": 2,
    "name": "content_manager",
    "display_name": "Content Manager"
  }
}
```

#### GET `/api/roles/{role_id}`
Get role details.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "admin",
    "display_name": "Administrator",
    "description": "System administrator",
    "level": 100,
    "color": "#dc3545",
    "icon": "shield",
    "is_active": true,
    "is_system_role": true,
    "is_admin_role": true,
    "permissions": {
      "users_manage": true,
      "roles_manage": true
    },
    "user_count": 5,
    "created_at": "2026-05-01T10:30:00Z"
  }
}
```

#### PUT `/api/roles/{role_id}`
Update role details.

**Request Body:**
```json
{
  "display_name": "Updated Administrator",
  "description": "Updated description",
  "color": "#28a745"
}
```

#### DELETE `/api/roles/{role_id}`
Delete a role.

**Response:**
```json
{
  "success": true,
  "message": "Role deleted successfully"
}
```

### Permissions

#### GET `/api/permissions`
Get all permissions.

**Response:**
```json
{
  "success": true,
  "data": {
    "permissions": [
      {
        "id": 1,
        "name": "users_create",
        "display_name": "Create Users",
        "description": "Permission to create users",
        "category": "user",
        "resource": "users",
        "action": "create",
        "is_system_permission": false,
        "is_active": true
      }
    ]
  }
}
```

#### POST `/api/permissions`
Create a new permission.

**Request Body:**
```json
{
  "name": "posts_moderate",
  "display_name": "Moderate Posts",
  "description": "Permission to moderate posts",
  "category": "content",
  "resource": "posts",
  "action": "moderate"
}
```

#### GET `/api/roles/{role_id}/permissions`
Get role permissions.

**Response:**
```json
{
  "success": true,
  "data": {
    "role_id": 1,
    "permissions": [
      {
        "id": 1,
        "name": "users_manage",
        "display_name": "Manage Users",
        "granted": true,
        "granted_at": "2026-05-01T10:30:00Z"
      }
    ]
  }
}
```

#### PUT `/api/roles/{role_id}/permissions`
Update role permissions.

**Request Body:**
```json
{
  "permissions": [1, 2, 3, 4, 5]
}
```

### Role Assignment

#### GET `/api/roles/assignments`
Get role assignments.

**Query Parameters:**
- `user_id`: Filter by user ID (optional)
- `role_id`: Filter by role ID (optional)
- `active_only`: Show only active assignments (default: true)

**Response:**
```json
{
  "success": true,
  "data": {
    "assignments": [
      {
        "id": 1,
        "user": {
          "id": 123,
          "username": "user123",
          "email": "user@example.com"
        },
        "role": {
          "id": 2,
          "name": "content_manager",
          "display_name": "Content Manager"
        },
        "assigned_by": {
          "id": 1,
          "username": "admin"
        },
        "assigned_at": "2026-05-10T10:30:00Z",
        "expires_at": null,
        "is_active": true
      }
    ]
  }
}
```

#### POST `/api/roles/assign`
Assign role to user.

**Request Body:**
```json
{
  "user_id": 123,
  "role_id": 2,
  "expires_at": "2026-12-31T23:59:59Z",
  "reason": "User needs content management access"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Role assigned successfully",
  "data": {
    "assignment_id": 456,
    "user_id": 123,
    "role_id": 2
  }
}
```

#### DELETE `/api/roles/assign/{user_id}/{role_id}`
Remove role from user.

**Response:**
```json
{
  "success": true,
  "message": "Role removed successfully"
}
```

### Role Requests

#### GET `/api/roles/requests`
Get role assignment requests.

**Query Parameters:**
- `status`: Filter by status (pending, approved, rejected)
- `workflow_type`: Filter by workflow type

**Response:**
```json
{
  "success": true,
  "data": {
    "requests": [
      {
        "id": 789,
        "user": {
          "id": 123,
          "username": "user123",
          "email": "user@example.com"
        },
        "role": {
          "id": 2,
          "name": "content_manager",
          "display_name": "Content Manager"
        },
        "workflow_type": "request",
        "status": "pending",
        "requested_by": {
          "id": 123,
          "username": "user123"
        },
        "reason": "Need content management access",
        "created_at": "2026-05-12T10:30:00Z"
      }
    ]
  }
}
```

#### POST `/api/roles/requests`
Create role assignment request.

**Request Body:**
```json
{
  "user_id": 123,
  "role_id": 2,
  "reason": "Need content management access for project X"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Role request created successfully",
  "data": {
    "request_id": 790,
    "status": "pending"
  }
}
```

#### POST `/api/roles/requests/{request_id}/process`
Process role request.

**Request Body:**
```json
{
  "action": "approve",
  "reason": "Approved for project requirements",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Role request approved",
  "data": {
    "request_id": 790,
    "status": "completed",
    "processed_at": "2026-05-12T10:35:00Z"
  }
}
```

### Role Analytics

#### GET `/api/roles/analytics/{role_id}`
Get role analytics.

**Query Parameters:**
- `days`: Number of days to look back (default: 30)

**Response:**
```json
{
  "success": true,
  "data": {
    "trends": [
      {
        "date": "2026-05-12",
        "user_count": 15,
        "new_assignments": 2,
        "removals": 1,
        "requests": 3,
        "approvals": 2,
        "rejections": 1
      }
    ],
    "current_stats": {
      "user_count": 15,
      "level": 50,
      "is_admin_role": false
    }
  }
}
```

#### POST `/api/roles/analytics/{role_id}/calculate`
Calculate role analytics for a specific date.

**Request Body:**
```json
{
  "date": "2026-05-12"
}
```

---

## Error Handling

All API endpoints return consistent error responses:

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "username",
      "reason": "Username is required"
    }
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `AUTHENTICATION_ERROR` | Authentication required or failed |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `CONFLICT` | Resource conflict (duplicate, etc.) |
| `RATE_LIMITED` | Rate limit exceeded |
| `INTERNAL_ERROR` | Internal server error |

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

| Endpoint Type | Limit | Window |
|--------------|-------|--------|
| Authentication | 10 requests | 1 minute |
| Profile APIs | 100 requests | 1 minute |
| Social APIs | 200 requests | 1 minute |
| Analytics APIs | 50 requests | 1 minute |
| Role Management | 30 requests | 1 minute |

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1623456789
```

---

## Response Formats

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

### Pagination Response
```json
{
  "success": true,
  "data": {
    "items": [ ... ],
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

### Bulk Operation Response
```json
{
  "success": true,
  "data": {
    "processed": 25,
    "successful": 23,
    "failed": 2,
    "errors": [
      {
        "index": 5,
        "error": "Invalid user ID"
      }
    ]
  }
}
```

---

**Implementation Status**: ✅ COMPLETE  
**API Coverage**: 100% of all user management systems  
**Documentation Quality**: Production Ready  
**Last Updated**: May 12, 2026  

This API documentation provides comprehensive coverage of all user management system endpoints with detailed request/response examples, error handling, and usage guidelines.
