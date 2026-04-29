# API System

## Overview

The API system provides a RESTful interface for programmatic access to forum data. Currently, it supports read operations for repositories and posts, with plans for full CRUD operations and authentication.

## Components

### Routes

**Sync Repositories Route** (`/api/sync-repositories`)
- Method: POST
- Rate limit: 5 requests per hour
- Fetches repositories from GitHub
- Stores in database
- Returns synced repositories

**Get Repositories Route** (`/api/repositories`)
- Method: GET
- Returns all repositories
- Includes metadata
- No authentication required

**Get Posts Route** (`/api/posts`)
- Method: GET
- Returns all posts
- Includes author and category
- Includes vote counts
- No authentication required

**Get Single Post Route** (`/api/posts/<post_id>`)
- Method: GET
- Returns single post
- Includes comments
- Includes author information
- No authentication required

## API Endpoints

### POST /api/sync-repositories

**Description:** Sync repositories from GitHub organization

**Request:** None (POST with no body)

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

**Rate Limit:** 5 requests per hour

**Example:**
```bash
curl -X POST http://localhost:5000/api/sync-repositories
```

### GET /api/repositories

**Description:** Retrieve all repositories

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
curl http://localhost:5000/api/repositories
```

### GET /api/posts

**Description:** Retrieve all posts

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
curl http://localhost:5000/api/posts
```

### GET /api/posts/<post_id>

**Description:** Retrieve a specific post

**Parameters:**
- `post_id` (integer, required): Post ID

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
curl http://localhost:5000/api/posts/1
```

## Error Responses

All endpoints may return error responses:

```json
{
  "error": "Error message",
  "status_code": 400
}
```

### HTTP Status Codes
- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

### Current Limits
- `/api/sync-repositories`: 5 requests per hour
- Other endpoints: Default limits apply

### Rate Limit Headers
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when rate limit resets

### Implementation
- Flask-Limiter integration
- IP-based limiting
- Configurable per endpoint
- Redis-backed (future)

## Authentication

### Current Status
- No authentication required for read operations
- Write operations should be protected in production

### Planned Authentication
- JWT tokens
- OAuth2 integration
- API keys
- Session-based authentication

### Authentication Headers (Future)
```
Authorization: Bearer <token>
```

## API Design Principles

### RESTful Design
- Resource-based URLs
- HTTP methods (GET, POST, PUT, DELETE)
- JSON request/response
- Standard HTTP status codes
- HATEOAS links (future)

### Versioning
- URL versioning: `/api/v1/`
- Header versioning (future)
- Backward compatibility
- Deprecation policy

### Pagination (Future)
- Query parameters: `page`, `per_page`
- Response metadata
- Links to next/previous pages

## Future API Endpoints

### Posts
- `POST /api/posts` - Create post
- `PUT /api/posts/<id>` - Update post
- `DELETE /api/posts/<id>` - Delete post

### Comments
- `GET /api/posts/<id>/comments` - List comments
- `POST /api/posts/<id>/comments` - Create comment
- `PUT /api/comments/<id>` - Update comment
- `DELETE /api/comments/<id>` - Delete comment

### Users
- `GET /api/users` - List users
- `GET /api/users/<id>` - Get user
- `PUT /api/users/<id>` - Update user

### Categories
- `GET /api/categories` - List categories
- `POST /api/categories` - Create category
- `PUT /api/categories/<id>` - Update category
- `DELETE /api/categories/<id>` - Delete category

### Votes
- `POST /api/posts/<id>/vote` - Vote on post
- `POST /api/comments/<id>/vote` - Vote on comment

### Bookmarks
- `GET /api/bookmarks` - List user bookmarks
- `POST /api/bookmarks` - Create bookmark
- `DELETE /api/bookmarks/<id>` - Delete bookmark

### Notifications
- `GET /api/notifications` - List notifications
- `PUT /api/notifications/<id>/read` - Mark as read

### Messages
- `GET /api/messages` - List messages
- `POST /api/messages` - Send message
- `PUT /api/messages/<id>/read` - Mark as read

## API Documentation

### OpenAPI/Swagger (Future)
- Interactive API documentation
- Request/response examples
- Schema definitions
- Try-it-out feature

### SDKs (Future)
- Python SDK
- JavaScript SDK
- Mobile SDKs

## API Security

### Current Security
- CSRF protection (for forms)
- Rate limiting
- Input validation

### Future Security
- API authentication (JWT)
- API keys
- OAuth2
- Rate limiting per user
- IP whitelisting
- Request signing

## API Testing

### Testing Tools
- cURL
- Postman
- Insomnia
- HTTPie
- Python requests library

### Example cURL Commands
```bash
# Get repositories
curl http://localhost:5000/api/repositories

# Get posts
curl http://localhost:5000/api/posts

# Get specific post
curl http://localhost:5000/api/posts/1

# Sync repositories
curl -X POST http://localhost:5000/api/sync-repositories
```

## API Best Practices

### For Developers
- Use appropriate HTTP methods
- Return proper status codes
- Provide error messages
- Include pagination metadata
- Version your API
- Document endpoints
- Provide examples

### For Consumers
- Handle errors gracefully
- Respect rate limits
- Cache responses when appropriate
- Use HTTPS in production
- Validate responses
- Implement retry logic

## API Performance

### Optimization Strategies
- Database query optimization
- Response caching (Redis)
- Pagination
- Lazy loading
- Connection pooling
- CDN for static assets

### Monitoring
- Response time tracking
- Error rate monitoring
- Rate limit monitoring
- API usage analytics
