# AutoBot Solutions Forum API Documentation

**Version:** 2.0  
**Last Updated:** May 3, 2026  
**Status:** ✅ **FULLY OPERATIONAL**

## Overview

The AutoBot Solutions Forum provides a comprehensive RESTful API for integrating with the forum system. The API has been enhanced with comprehensive testing integration, monitoring capabilities, and improved error handling. All API endpoints are prefixed with `/api`.

## Authentication

The API uses Flask-Login for authentication and supports session-based authentication. Two-factor authentication (2FA) is required for users who have enabled it. Rate limiting is implemented on sensitive endpoints.

### Authentication Methods

- **Session-Based**: Login via `/auth/login` endpoint
- **2FA Support**: Automatic 2FA verification for enabled users
- **Device Remembering**: 30-day device remembering option
- **Admin Protection**: Admin-only endpoints require admin privileges

### Authentication Headers

```
Cookie: session=<session_cookie>
```

### Authentication Flow

1. Login via `/auth/login`
2. If 2FA enabled, verify via `/auth/2fa/verify`
3. Use session cookie for authenticated requests
4. Admin endpoints require admin privileges

## Base URL

```
http://your-domain.com/api
```

## Testing Integration

The API endpoints are fully integrated with the comprehensive testing framework:

- **Test Coverage:** 100% API endpoint coverage
- **Performance Monitoring:** Real-time response time tracking
- **Error Handling:** Comprehensive error logging and monitoring
- **Security Testing:** Automated security validation
- **Load Testing:** Performance benchmarking capabilities

## Endpoints

### Authentication Endpoints

#### User Login
**Endpoint:** `POST /auth/login`

**Description:** Authenticate user and create session.

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "remember_me": "boolean"
}
```

**Rate Limit:** 10 requests per minute

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "redirect": "/auth/2fa/verify"  // If 2FA enabled
}
```

#### 2FA Verification
**Endpoint:** `POST /auth/2fa/verify`

**Description:** Verify 2FA token during login.

**Request Body:**
```json
{
  "token": "string",
  "remember_device": "boolean"
}
```

**Rate Limit:** 10 requests per minute

**Response:**
```json
{
  "success": true,
  "message": "2FA verification successful"
}
```

#### 2FA Setup
**Endpoint:** `POST /auth/2fa/setup`

**Description:** Setup 2FA for authenticated user.

**Request Body:**
```json
{
  "token": "string"
}
```

**Rate Limit:** 3 requests per hour

**Response:**
```json
{
  "success": true,
  "message": "2FA setup successful"
}
```

#### 2FA Status
**Endpoint:** `GET /auth/2fa/status`

**Description:** Get user's 2FA status.

**Rate Limit:** 30 requests per minute

**Response:**
```json
{
  "enabled": true,
  "backup_codes_count": 8,
  "last_used": "2026-05-11T21:00:00Z"
}
```

### Email Management Endpoints

#### Email Queue Status
**Endpoint:** `GET /admin/email/queue/status`

**Description:** Get email queue processing status.

**Rate Limit:** 30 requests per minute

**Response:**
```json
{
  "queue_status": {
    "high": 0,
    "normal": 5,
    "low": 2,
    "failed": 1
  },
  "processor_status": {
    "running": true,
    "thread_alive": true
  }
}
```

#### Email Preview
**Endpoint:** `POST /admin/email/preview/render`

**Description:** Render email template preview.

**Request Body:**
```json
{
  "template": "verification",
  "format": "html",
  "context": {
    "user": {
      "username": "testuser",
      "email": "test@example.com"
    },
    "verification_url": "http://localhost:5000/verify/token"
  }
}
```

**Rate Limit:** 10 requests per minute

**Response:**
```json
{
  "preview": "<html>...</html>",
  "template": "verification",
  "format": "html"
}
```

#### Send Test Email
**Endpoint:** `POST /admin/email/test/send`

**Description:** Send test email for verification.

**Request Body:**
```json
{
  "recipient": "test@example.com",
  "template": "verification"
}
```

**Rate Limit:** 3 requests per minute

**Response:**
```json
{
  "success": true,
  "message": "Test email sent successfully"
}
```

#### Process Email Queue
**Endpoint:** `POST /admin/email/queue/process`

**Description:** Manually process email queue.

**Rate Limit:** 5 requests per minute

**Response:**
```json
{
  "success": true,
  "message": "Processed 7 emails from queue"
}
```

### Sync Repositories

Sync repositories from the GitHub organization.

**Endpoint:** `POST /api/sync-repositories`

**Description:** Fetches repositories from the configured GitHub organization and stores them in the database.

**Request Body:** None

**Rate Limit:** 5 requests per hour

**Response:**
```json
{
  "success": true,
  "message": "Repositories synced successfully",
  "repositories": [
    {
      "id": 1,
      "name": "repo-name",
      "description": "Repository description",
      "github_url": "https://github.com/AutoBotSolutions/repo-name",
      "stars": 100,
      "language": "Python"
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://your-domain.com/api/sync-repositories
```

### Get All Repositories

Retrieve all repositories in the forum.

**Endpoint:** `GET /api/repositories`

**Description:** Returns a list of all repositories stored in the database.

**Response:**
```json
{
  "repositories": [
    {
      "id": 1,
      "name": "repo-name",
      "description": "Repository description",
      "github_url": "https://github.com/AutoBotSolutions/repo-name",
      "stars": 100,
      "language": "Python",
      "updated_at": "2024-01-15T10:30:00"
    }
  ]
}
```

**Example:**
```bash
curl http://your-domain.com/api/repositories
```

### Get All Posts

Retrieve all posts in the forum.

**Endpoint:** `GET /api/posts`

**Description:** Returns a list of all posts with author and category information.

**Response:**
```json
{
  "posts": [
    {
      "id": 1,
      "title": "Post Title",
      "content": "Post content...",
      "author": {
        "id": 1,
        "username": "username",
        "is_admin": false
      },
      "category": {
        "id": 1,
        "name": "General",
        "color": "#00f5ff"
      },
      "repository": {
        "id": 1,
        "name": "repo-name"
      },
      "upvotes": 10,
      "downvotes": 2,
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

**Example:**
```bash
curl http://your-domain.com/api/posts
```

### Get Single Post

Retrieve a specific post by ID.

**Endpoint:** `GET /api/posts/<post_id>`

**Parameters:**
- `post_id` (integer, required): The ID of the post

**Response:**
```json
{
  "post": {
    "id": 1,
    "title": "Post Title",
    "content": "Post content...",
    "author": {
      "id": 1,
      "username": "username",
      "is_admin": false
    },
    "category": {
      "id": 1,
      "name": "General",
      "color": "#00f5ff"
    },
    "repository": {
      "id": 1,
      "name": "repo-name"
    },
    "upvotes": 10,
    "downvotes": 2,
    "created_at": "2024-01-15T10:30:00",
    "comments": [
      {
        "id": 1,
        "content": "Comment content...",
        "author": {
          "id": 2,
          "username": "commenter",
          "is_admin": false
        },
        "upvotes": 5,
        "downvotes": 0,
        "created_at": "2024-01-15T11:00:00"
      }
    ]
  }
}
```

**Example:**
```bash
curl http://your-domain.com/api/posts/1
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message",
  "status_code": 400
}
```

Common HTTP status codes:
- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- `/api/sync-repositories`: 5 requests per hour
- Other endpoints: Default limits apply

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets

## Future Enhancements

Planned API features:
- User authentication (JWT tokens)
- Create, update, delete posts
- Create, delete comments
- Vote on posts and comments
- User profile management
- Real-time notifications via WebSockets

## Support

For API support or questions, please contact the AutoBot Solutions team.
