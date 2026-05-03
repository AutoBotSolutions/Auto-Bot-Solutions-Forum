# AutoBot Solutions Forum API Documentation

**Version:** 2.0  
**Last Updated:** May 3, 2026  
**Status:** ✅ **FULLY OPERATIONAL**

## Overview

The AutoBot Solutions Forum provides a comprehensive RESTful API for integrating with the forum system. The API has been enhanced with comprehensive testing integration, monitoring capabilities, and improved error handling. All API endpoints are prefixed with `/api`.

## Authentication

Currently, the API does not require authentication for read operations. Write operations should be protected in production by implementing proper authentication. Rate limiting is implemented on sensitive endpoints.

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
