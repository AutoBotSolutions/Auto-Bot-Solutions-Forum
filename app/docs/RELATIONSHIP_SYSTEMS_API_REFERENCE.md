# Relationship Systems API Reference
## Auto Bot Solutions Forum

**Version:** 1.0.0  
**Last Updated:** May 13, 2026  
**Status:** ✅ Implemented and Debugged

---

## Overview

This document provides comprehensive API reference for the Advanced User Relationships and Content Relationships systems implemented in the Auto Bot Solutions Forum.

### Base URL
```
https://api.autobotsolutions.com/v1
```

### Authentication
All API endpoints require authentication using Bearer tokens:
```http
Authorization: Bearer <your_jwt_token>
```

### Response Format
All responses follow a consistent format:
```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "timestamp": "2026-05-13T12:00:00Z"
}
```

---

## Advanced User Relationships API

### Social Connections

#### Follow User
**POST** `/social/connections/follow`

Creates a follow relationship between users.

**Request Body:**
```json
{
  "following_id": 123,
  "strength": 0.1
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "connection_id": 456,
    "following_id": 123,
    "connection_type": "follow",
    "status": "active",
    "strength": 0.1,
    "created_at": "2026-05-13T12:00:00Z"
  },
  "message": "Successfully followed user"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid following_id or already following
- `404 Not Found`: User not found
- `429 Too Many Requests`: Rate limit exceeded

#### Unfollow User
**DELETE** `/social/connections/follow/{following_id}`

Removes a follow relationship.

**Response:**
```json
{
  "success": true,
  "data": {
    "connection_id": 456,
    "status": "inactive"
  },
  "message": "Successfully unfollowed user"
}
```

#### Send Friend Request
**POST** `/social/connections/friend-request`

Sends a friend request to another user.

**Request Body:**
```json
{
  "recipient_id": 123,
  "message": "I'd like to connect with you!"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "request_id": 789,
    "recipient_id": 123,
    "status": "pending",
    "created_at": "2026-05-13T12:00:00Z"
  },
  "message": "Friend request sent successfully"
}
```

#### Accept Friend Request
**POST** `/social/connections/friend-request/accept`

Accepts a friend request and creates mutual friendship.

**Request Body:**
```json
{
  "friend_id": 123,
  "request_id": 789
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "friendship_id": 101112,
    "friend_id": 123,
    "status": "active",
    "created_at": "2026-05-13T12:00:00Z"
  },
  "message": "Friend request accepted"
}
```

#### Block User
**POST** `/social/connections/block`

Blocks a user and removes existing connections.

**Request Body:**
```json
{
  "blocked_id": 123,
  "reason": "Inappropriate behavior"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "block_id": 131415,
    "blocked_id": 123,
    "reason": "Inappropriate behavior",
    "created_at": "2026-05-13T12:00:00Z"
  },
  "message": "User blocked successfully"
}
```

#### Get User Connections
**GET** `/social/connections`

Retrieves all connections for the authenticated user.

**Query Parameters:**
- `type` (optional): Filter by connection type (follow, friend, block, mute)
- `status` (optional): Filter by status (active, inactive)
- `limit` (optional): Maximum number of results (default: 20)
- `offset` (optional): Offset for pagination (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "connections": [
      {
        "id": 456,
        "user_id": 123,
        "connected_user_id": 456,
        "connection_type": "follow",
        "status": "active",
        "strength": 0.5,
        "created_at": "2026-05-13T12:00:00Z",
        "user": {
          "id": 456,
          "username": "johndoe",
          "first_name": "John",
          "last_name": "Doe",
          "avatar_url": "https://example.com/avatar.jpg"
        }
      }
    ],
    "total_count": 150,
    "limit": 20,
    "offset": 0
  },
  "message": "Connections retrieved successfully"
}
```

### Social Groups

#### Create Group
**POST** `/social/groups`

Creates a new social group.

**Request Body:**
```json
{
  "name": "Tech Enthusiasts",
  "description": "A group for technology enthusiasts",
  "group_type": "community",
  "privacy": "public",
  "icon": "tech",
  "color": "#007bff"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "group_id": 789,
    "name": "Tech Enthusiasts",
    "description": "A group for technology enthusiasts",
    "group_type": "community",
    "privacy": "public",
    "creator_id": 123,
    "member_count": 1,
    "is_active": true,
    "created_at": "2026-05-13T12:00:00Z"
  },
  "message": "Group created successfully"
}
```

#### Join Group
**POST** `/social/groups/{group_id}/join`

Joins a user to a group.

**Request Body:**
```json
{
  "invitation_code": "optional-invitation-code"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "membership_id": 101112,
    "group_id": 789,
    "user_id": 123,
    "role": "member",
    "status": "active",
    "joined_at": "2026-05-13T12:00:00Z"
  },
  "message": "Successfully joined group"
}
```

#### Leave Group
**DELETE** `/social/groups/{group_id}/leave`

Removes a user from a group.

**Response:**
```json
{
  "success": true,
  "data": {
    "membership_id": 101112,
    "status": "inactive",
    "left_at": "2026-05-13T12:00:00Z"
  },
  "message": "Successfully left group"
}
```

#### Get Group Members
**GET** `/social/groups/{group_id}/members`

Retrieves all members of a group.

**Query Parameters:**
- `role` (optional): Filter by role (owner, admin, moderator, member)
- `status` (optional): Filter by status (active, inactive)
- `limit` (optional): Maximum number of results (default: 20)
- `offset` (optional): Offset for pagination (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "members": [
      {
        "membership_id": 101112,
        "user_id": 123,
        "group_id": 789,
        "role": "member",
        "status": "active",
        "joined_at": "2026-05-13T12:00:00Z",
        "contribution_score": 0.8,
        "user": {
          "id": 123,
          "username": "johndoe",
          "first_name": "John",
          "last_name": "Doe",
          "avatar_url": "https://example.com/avatar.jpg"
        }
      }
    ],
    "total_count": 50,
    "limit": 20,
    "offset": 0
  },
  "message": "Group members retrieved successfully"
}
```

### Social Analytics

#### Get User Analytics
**GET** `/social/analytics/user/{user_id}`

Retrieves comprehensive analytics for a user.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "period_days": 30,
    "network_metrics": {
      "followers_count": 150,
      "following_count": 75,
      "friends_count": 25,
      "blocked_count": 5,
      "network_size": 225,
      "engagement_rate": 0.15
    },
    "influence_metrics": {
      "influence_score": 0.75,
      "reach": 1250,
      "impressions": 5000,
      "engagement": 750
    },
    "activity_metrics": {
      "posts_created": 15,
      "comments_made": 45,
      "likes_given": 120,
      "shares_made": 8,
      "activity_level": "high"
    },
    "growth_metrics": {
      "followers_growth": 0.12,
      "engagement_growth": 0.08,
      "activity_growth": 0.15
    }
  },
  "message": "User analytics retrieved successfully"
}
```

#### Get Social Trends
**GET** `/social/analytics/trends`

Retrieves social activity trends.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)
- `type` (optional): Trend type (connections, groups, activity)

**Response:**
```json
{
  "success": true,
  "data": {
    "period_days": 30,
    "trends": {
      "connections": {
        "total_created": 1250,
        "daily_average": 41.67,
        "growth_rate": 0.15,
        "trending_types": ["follow", "friend"]
      },
      "groups": {
        "total_created": 45,
        "daily_average": 1.5,
        "growth_rate": 0.08,
        "popular_types": ["community", "team"]
      },
      "activity": {
        "total_activities": 3500,
        "daily_average": 116.67,
        "growth_rate": 0.12,
        "popular_types": ["post", "comment"]
      }
    }
  },
  "message": "Social trends retrieved successfully"
}
```

### Social Activity

#### Get Activity Feed
**GET** `/social/activity/feed`

Retrieves personalized activity feed for the authenticated user.

**Query Parameters:**
- `limit` (optional): Maximum number of activities (default: 20)
- `offset` (optional): Offset for pagination (default: 0)
- `type` (optional): Filter by activity type

**Response:**
```json
{
  "success": true,
  "data": {
    "activities": [
      {
        "id": 123456,
        "user_id": 123,
        "activity_type": "post",
        "target_id": 789,
        "visibility": "public",
        "metadata": {
          "title": "My New Post",
          "summary": "Check out my latest post!"
        },
        "created_at": "2026-05-13T12:00:00Z",
        "user": {
          "id": 123,
          "username": "johndoe",
          "first_name": "John",
          "last_name": "Doe",
          "avatar_url": "https://example.com/avatar.jpg"
        }
      }
    ],
    "total_count": 100,
    "limit": 20,
    "offset": 0
  },
  "message": "Activity feed retrieved successfully"
}
```

#### Create Activity
**POST** `/social/activity`

Creates a new social activity.

**Request Body:**
```json
{
  "activity_type": "post",
  "target_id": 789,
  "visibility": "public",
  "metadata": {
    "title": "My New Post",
    "summary": "Check out my latest post!"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "activity_id": 123456,
    "activity_type": "post",
    "target_id": 789,
    "visibility": "public",
    "created_at": "2026-05-13T12:00:00Z"
  },
  "message": "Activity created successfully"
}
```

---

## Content Relationships API

### Content Management

#### Create Content
**POST** `/content`

Creates new content with relationships.

**Request Body:**
```json
{
  "title": "My New Post",
  "content": "This is the content of my post...",
  "content_type": "post",
  "visibility": "public",
  "summary": "A brief summary of my post",
  "tags": ["introduction", "welcome"],
  "categories": [1, 2],
  "metadata": {
    "mood": "excited",
    "featured": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "content_id": 123456,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "title": "My New Post",
    "content_type": "post",
    "status": "published",
    "visibility": "public",
    "view_count": 0,
    "like_count": 0,
    "comment_count": 0,
    "share_count": 0,
    "quality_score": 0.0,
    "engagement_score": 0.0,
    "created_at": "2026-05-13T12:00:00Z",
    "published_at": "2026-05-13T12:00:00Z"
  },
  "message": "Content created successfully"
}
```

#### Update Content
**PUT** `/content/{content_id}`

Updates existing content.

**Request Body:**
```json
{
  "title": "Updated Post Title",
  "content": "Updated content...",
  "summary": "Updated summary",
  "tags": ["updated", "content"],
  "categories": [1, 3],
  "change_summary": "Updated title and content"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "content_id": 123456,
    "version_id": 789,
    "changes": ["title", "content", "summary", "tags", "categories"],
    "updated_at": "2026-05-13T12:30:00Z"
  },
  "message": "Content updated successfully"
}
```

#### Get Content
**GET** `/content/{content_id}`

Retrieves content with full details.

**Response:**
```json
{
  "success": true,
  "data": {
    "content": {
      "id": 123456,
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "title": "My New Post",
      "content": "This is the content of my post...",
      "summary": "A brief summary of my post",
      "content_type": "post",
      "author": {
        "id": 123,
        "username": "johndoe",
        "first_name": "John",
        "last_name": "Doe",
        "avatar_url": "https://example.com/avatar.jpg"
      },
      "visibility": "public",
      "status": "published",
      "slug": "my-new-post",
      "tags": [
        {
          "id": 1,
          "name": "introduction"
        },
        {
          "id": 2,
          "name": "welcome"
        }
      ],
      "categories": [
        {
          "id": 1,
          "name": "General"
        }
      ],
      "metrics": {
        "view_count": 150,
        "like_count": 25,
        "comment_count": 8,
        "share_count": 3,
        "bookmark_count": 5,
        "engagement_rate": 0.27,
        "content_score": 0.75
      },
      "timestamps": {
        "created_at": "2026-05-13T12:00:00Z",
        "updated_at": "2026-05-13T12:30:00Z",
        "published_at": "2026-05-13T12:00:00Z"
      },
      "settings": {
        "allow_comments": true,
        "allow_sharing": true,
        "is_featured": false,
        "is_pinned": false,
        "is_locked": false
      }
    }
  },
  "message": "Content retrieved successfully"
}
```

#### Get Content List
**GET** `/content`

Retrieves content list with filtering and sorting.

**Query Parameters:**
- `type` (optional): Filter by content type
- `status` (optional): Filter by status (default: published)
- `visibility` (optional): Filter by visibility
- `sort_by` (optional): Sort field (created_at, updated_at, view_count, engagement_score, content_score)
- `order` (optional): Sort order (asc, desc)
- `limit` (optional): Maximum number of results (default: 20)
- `offset` (optional): Offset for pagination (default: 0)
- `featured_only` (optional): Only featured content (default: false)

**Response:**
```json
{
  "success": true,
  "data": {
    "content": [
      {
        "id": 123456,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "title": "My New Post",
        "summary": "A brief summary of my post",
        "content_type": "post",
        "author": {
          "id": 123,
          "username": "johndoe",
          "first_name": "John",
          "last_name": "Doe"
        },
        "visibility": "public",
        "status": "published",
        "slug": "my-new-post",
        "tags": [
          {
            "id": 1,
            "name": "introduction"
          }
        ],
        "metrics": {
          "view_count": 150,
          "like_count": 25,
          "comment_count": 8,
          "share_count": 3,
          "engagement_rate": 0.27,
          "content_score": 0.75
        },
        "timestamps": {
          "created_at": "2026-05-13T12:00:00Z",
          "updated_at": "2026-05-13T12:30:00Z",
          "published_at": "2026-05-13T12:00:00Z"
        },
        "settings": {
          "is_featured": false,
          "is_pinned": false,
          "is_locked": false
        }
      }
    ],
    "pagination": {
      "total_count": 500,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  },
  "message": "Content list retrieved successfully"
}
```

#### Delete Content
**DELETE** `/content/{content_id}`

Deletes content (soft delete).

**Request Body:**
```json
{
  "reason": "No longer needed"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "content_id": 123456,
    "status": "deleted",
    "deleted_at": "2026-05-13T12:00:00Z"
  },
  "message": "Content deleted successfully"
}
```

#### Archive Content
**POST** `/content/{content_id}/archive`

Archives content with retention policy.

**Request Body:**
```json
{
  "reason": "manual",
  "retention_days": 365
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "content_id": 123456,
    "archive_id": 789,
    "archive_reason": "manual",
    "retention_date": "2027-05-13T12:00:00Z",
    "archived_at": "2026-05-13T12:00:00Z"
  },
  "message": "Content archived successfully"
}
```

### Content Analytics

#### Track View
**POST** `/content/{content_id}/analytics/view`

Tracks content view.

**Request Body:**
```json
{
  "duration": 45.5,
  "device": "mobile",
  "country": "US",
  "city": "New York",
  "browser": "Chrome",
  "source": "direct"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "view_id": 123456789,
    "content_id": 123456,
    "tracked_at": "2026-05-13T12:00:00Z"
  },
  "message": "View tracked successfully"
}
```

#### Track Engagement
**POST** `/content/{content_id}/analytics/engagement`

Tracks content engagement.

**Request Body:**
```json
{
  "type": "like",
  "metadata": {
    "source": "feed",
    "position": 5
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "engagement_id": 987654321,
    "content_id": 123456,
    "engagement_type": "like",
    "tracked_at": "2026-05-13T12:00:00Z"
  },
  "message": "Engagement tracked successfully"
}
```

#### Get Content Analytics
**GET** `/content/{content_id}/analytics`

Retrieves comprehensive analytics for content.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "success": true,
  "data": {
    "analytics": {
      "basic_metrics": {
        "total_views": 1500,
        "unique_views": 1200,
        "average_view_duration": 45.5,
        "bounce_rate": 0.25,
        "engagement_rate": 0.27,
        "average_daily_views": 50
      },
      "engagement_metrics": {
        "total_engagements": 405,
        "likes": 150,
        "comments": 80,
        "shares": 45,
        "bookmarks": 30,
        "downloads": 100
      },
      "time_based_analytics": {
        "views_today": 25,
        "views_this_week": 175,
        "views_this_month": 750
      },
      "geographic_analytics": {
        "US": 800,
        "UK": 300,
        "Canada": 200,
        "Australia": 100,
        "Other": 100
      },
      "device_analytics": {
        "mobile": 900,
        "desktop": 500,
        "tablet": 100
      },
      "traffic_sources": {
        "direct": 600,
        "search": 400,
        "social": 300,
        "referral": 200
      },
      "engagement_trends": {
        "2026-05-01": 15,
        "2026-05-02": 18,
        "2026-05-03": 22,
        "2026-05-04": 20,
        "2026-05-05": 25
      },
      "view_patterns": {
        "hourly_distribution": {
          "0": 5,
          "1": 3,
          "2": 2,
          "3": 4,
          "4": 8,
          "5": 15,
          "6": 25,
          "7": 35,
          "8": 45,
          "9": 55,
          "10": 65,
          "11": 70,
          "12": 75,
          "13": 80,
          "14": 85,
          "15": 80,
          "16": 75,
          "17": 70,
          "18": 65,
          "19": 55,
          "20": 45,
          "21": 35,
          "22": 25,
          "23": 15
        }
      }
    }
  },
  "message": "Content analytics retrieved successfully"
}
```

#### Get Trending Content
**GET** `/content/trending`

Retrieves trending content.

**Query Parameters:**
- `type` (optional): Filter by content type
- `limit` (optional): Maximum number of results (default: 20)
- `hours` (optional): Number of hours to consider (default: 24)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "content_id": 123456,
      "title": "Trending Post",
      "summary": "This post is trending",
      "content_type": "post",
      "author": {
        "id": 123,
        "username": "johndoe",
        "first_name": "John",
        "last_name": "Doe"
      },
      "metrics": {
        "view_count": 500,
        "engagement_score": 0.85,
        "trending_score": 0.92,
        "content_score": 0.78
      },
      "created_at": "2026-05-13T10:00:00Z"
    }
  ],
  "message": "Trending content retrieved successfully"
}
```

### Content Moderation

#### Flag Content
**POST** `/content/{content_id}/moderation/flag`

Flags content for moderation review.

**Request Body:**
```json
{
  "reason": "Inappropriate content",
  "severity": 3
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "moderation_id": 123456,
    "content_id": 123456,
    "status": "flagged",
    "priority": "high",
    "report_count": 1,
    "created_at": "2026-05-13T12:00:00Z"
  },
  "message": "Content flagged for moderation"
}
```

#### Review Content
**POST** `/content/{content_id}/moderation/review`

Reviews flagged content (moderator only).

**Request Body:**
```json
{
  "action": "approve",
  "reason": "Content is appropriate",
  "notes": "Reviewed and approved"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "moderation_id": 123456,
    "action": "approve",
    "reviewer_id": 456,
    "reviewed_at": "2026-05-13T12:30:00Z",
    "resolved_at": "2026-05-13T12:30:00Z"
  },
  "message": "Content review completed"
}
```

#### Get Pending Moderation
**GET** `/content/moderation/pending`

Retrieves pending moderation items (moderator only).

**Query Parameters:**
- `limit` (optional): Maximum number of results (default: 50)
- `priority` (optional): Filter by priority (low, normal, high, urgent)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "moderation_id": 123456,
      "content_id": 123456,
      "content": {
        "title": "Flagged Content",
        "content_type": "post",
        "author": {
          "id": 123,
          "username": "johndoe",
          "first_name": "John",
          "last_name": "Doe"
        },
        "created_at": "2026-05-13T10:00:00Z"
      },
      "moderation": {
        "status": "flagged",
        "priority": "high",
        "severity": 3,
        "report_count": 5,
        "report_reasons": ["Inappropriate content", "Spam"],
        "auto_flagged": false,
        "confidence_score": 0.0
      }
    }
  ],
  "message": "Pending moderation items retrieved successfully"
}
```

### Content Recommendations

#### Get User Recommendations
**GET** `/content/recommendations`

Retrieves personalized content recommendations.

**Query Parameters:**
- `type` (optional): Filter by content type
- `limit` (optional): Maximum number of recommendations (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "content_id": 123456,
      "title": "Recommended Content",
      "summary": "You might like this content",
      "content_type": "post",
      "engagement_score": 0.75,
      "recommendation_score": 0.85,
      "reason": "Based on your reading history",
      "created_at": "2026-05-13T10:00:00Z"
    }
  ],
  "message": "Recommendations retrieved successfully"
}
```

#### Get Similar Content
**GET** `/content/{content_id}/similar`

Retrieves content similar to specified content.

**Query Parameters:**
- `limit` (optional): Maximum number of results (default: 10)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "content_id": 123457,
      "title": "Similar Content",
      "summary": "This content is similar to what you viewed",
      "content_type": "post",
      "engagement_score": 0.70,
      "similarity_score": 0.82,
      "created_at": "2026-05-13T09:00:00Z"
    }
  ],
  "message": "Similar content retrieved successfully"
}
```

#### Record Recommendation Interaction
**POST** `/content/recommendations/{content_id}/interact`

Records user interaction with recommendation.

**Request Body:**
```json
{
  "type": "click",
  "feedback": 0.8
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "recommendation_id": 123456789,
    "interaction_type": "click",
    "recorded_at": "2026-05-13T12:00:00Z"
  },
  "message": "Interaction recorded successfully"
}
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "title",
      "reason": "Title is required"
    }
  },
  "timestamp": "2026-05-13T12:00:00Z"
}
```

### Common Error Codes

#### Authentication Errors
- `401 Unauthorized`: Invalid or missing authentication token
- `403 Forbidden`: Insufficient permissions

#### Validation Errors
- `400 Bad Request`: Invalid input data
- `422 Unprocessable Entity`: Data validation failed

#### Resource Errors
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate content)

#### Rate Limiting
- `429 Too Many Requests`: Rate limit exceeded
- `503 Service Unavailable`: Service temporarily unavailable

---

## Rate Limiting

### Rate Limits by Endpoint

#### Social Connections
- Follow/Unfollow: 100 requests per hour
- Friend Requests: 50 requests per hour
- Block/Unblock: 100 requests per hour

#### Content Management
- Create Content: 50 requests per hour
- Update Content: 200 requests per hour
- Delete Content: 100 requests per hour

#### Analytics
- Track View/Engagement: 1000 requests per hour
- Get Analytics: 500 requests per hour

#### Recommendations
- Get Recommendations: 200 requests per hour
- Record Interactions: 500 requests per hour

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## Pagination

### Pagination Parameters
- `limit`: Maximum number of items per page (default: 20, max: 100)
- `offset`: Number of items to skip (default: 0)

### Pagination Response
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "total_count": 500,
      "limit": 20,
      "offset": 0,
      "has_more": true,
      "total_pages": 25,
      "current_page": 1
    }
  }
}
```

---

## Webhooks

### Social Activity Webhook
**Endpoint**: Your configured webhook URL  
**Events**: User follows, friend requests, group joins

**Payload:**
```json
{
  "event": "user.follow",
  "data": {
    "user_id": 123,
    "following_id": 456,
    "timestamp": "2026-05-13T12:00:00Z"
  }
}
```

### Content Activity Webhook
**Endpoint**: Your configured webhook URL  
**Events**: Content created, updated, deleted, flagged

**Payload:**
```json
{
  "event": "content.created",
  "data": {
    "content_id": 123456,
    "author_id": 123,
    "content_type": "post",
    "timestamp": "2026-05-13T12:00:00Z"
  }
}
```

---

## SDK Examples

### Python SDK
```python
from autobotsolutions_sdk import SocialClient, ContentClient

# Initialize clients
social_client = SocialClient(api_key="your-api-key")
content_client = ContentClient(api_key="your-api-key")

# Follow a user
result = social_client.follow_user(following_id=123)
print(f"Follow result: {result}")

# Create content
result = content_client.create_content(
    title="My Post",
    content="This is my post content...",
    content_type="post"
)
print(f"Content created: {result['content_id']}")
```

### JavaScript SDK
```javascript
import { SocialClient, ContentClient } from 'autobotsolutions-sdk';

// Initialize clients
const socialClient = new SocialClient({ apiKey: 'your-api-key' });
const contentClient = new ContentClient({ apiKey: 'your-api-key' });

// Follow a user
const followResult = await socialClient.followUser({ followingId: 123 });
console.log('Follow result:', followResult);

// Create content
const createResult = await contentClient.createContent({
  title: 'My Post',
  content: 'This is my post content...',
  contentType: 'post'
});
console.log('Content created:', createResult.contentId);
```

---

## Testing

### Testing Environment
- **Base URL**: `https://api-test.autobotsolutions.com/v1`
- **Authentication**: Use test API keys
- **Rate Limits**: Relaxed limits for testing

### Test Data
Use the `/test` endpoint to create test data:
```http
POST /test/create-user
POST /test/create-content
POST /test/create-group
```

---

## Changelog

### Version 1.0.0 (2026-05-13)
- Initial release of Advanced User Relationships API
- Initial release of Content Relationships API
- Complete social connections and groups functionality
- Complete content management and analytics functionality
- Automated moderation and recommendations

---

## Support

### Documentation
- [Advanced User Relationships System](ADVANCED_USER_RELATIONSHIPS_SYSTEM.md)
- [Content Relationships System](CONTENT_RELATIONSHIPS_SYSTEM.md)
- [API Documentation](API_DOCUMENTATION.md)

### Support Channels
- **Email**: api-support@autobotsolutions.com
- **GitHub**: Create issues in the project repository
- **Discord**: Join our developer community

### Status Page
- **API Status**: https://status.autobotsolutions.com
- **Uptime History**: Available on status page

---

**Document Version:** 1.0.0  
**Last Updated:** May 13, 2026  
**API Version**: v1.0.0  
**Next Review:** June 13, 2026

For questions or support, please refer to the troubleshooting section or create an issue in the project repository.
