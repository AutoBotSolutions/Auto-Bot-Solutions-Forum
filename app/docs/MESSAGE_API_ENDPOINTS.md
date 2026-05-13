# Message API Endpoints Documentation

## Overview

This document provides comprehensive API documentation for all Message System endpoints, including the newly implemented Search, Threading, and Rich Text features. All endpoints require user authentication and follow RESTful principles.

## Base URL
```
/api/v1/messages
```

## Authentication

All endpoints require authentication using Flask-Login. Include session cookies or JWT tokens in requests.

## Response Format

### Success Response
```json
{
    "success": true,
    "data": { ... },
    "message": "Operation successful"
}
```

### Error Response
```json
{
    "success": false,
    "error": "Error message",
    "code": "ERROR_CODE"
}
```

## Search Endpoints

### POST `/messages/search`
**Advanced message search with filtering options**

**Request Body:**
```json
{
    "query": "hello world",
    "date_from": "2024-01-01T00:00:00",
    "date_to": "2024-12-31T23:59:59",
    "sender_id": 2,
    "is_read": false,
    "priority": "high",
    "has_attachments": false,
    "thread_id": 1,
    "sort_by": "relevance",
    "search_type": "advanced",
    "page": 1,
    "per_page": 20
}
```

**Parameters:**
- `query` (string, required): Search query
- `date_from` (date, optional): Filter messages from this date
- `date_to` (date, optional): Filter messages to this date
- `sender_id` (integer, optional): Filter by specific sender
- `is_read` (boolean, optional): Filter by read status
- `priority` (string, optional): Filter by priority ('low', 'normal', 'high', 'urgent')
- `has_attachments` (boolean, optional): Filter by attachment presence
- `thread_id` (integer, optional): Filter by specific thread
- `sort_by` (string, optional): Sort method ('relevance', 'date', 'sender')
- `search_type` (string, optional): Search type ('basic', 'advanced', 'boolean')
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Results per page (default: 20)

**Response:**
```json
{
    "success": true,
    "data": {
        "results": [
            {
                "id": 1,
                "sender_id": 2,
                "receiver_id": 1,
                "content": "Hello world",
                "created_at": "2024-01-01T12:00:00",
                "is_read": true,
                "sender_name": "john_doe",
                "highlighted_content": "<mark>Hello</mark> world",
                "relevance_score": 4.5,
                "thread_id": 1,
                "priority": "normal",
                "has_attachments": false
            }
        ],
        "total_results": 25,
        "page": 1,
        "per_page": 20,
        "total_pages": 2,
        "search_time": 0.15,
        "query": "hello",
        "filters": {},
        "sort_by": "relevance"
    }
}
```

### GET `/messages/search/advanced`
**Advanced search with Boolean operators and field-specific search**

**Query Parameters:**
- `q` (string, required): Search query with Boolean operators
- `sort` (string, optional): Sort method (default: 'relevance')
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Results per page (default: 20)

**Example Boolean Queries:**
- `hello AND world` - Both terms must be present
- `urgent OR important` - Either term must be present
- `project AND (urgent OR important) NOT completed` - Complex Boolean logic
- `sender:john content:hello` - Field-specific search

### GET `/messages/search/export`
**Export search results to CSV format**

**Query Parameters:**
- `q` (string, required): Search query
- `search_type` (string, optional): Search type (default: 'basic')
- `sort_by` (string, optional): Sort method (default: 'relevance')
- All filter parameters from basic search

**Response:**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="message_search_results.csv"

id,sender_id,receiver_id,content,created_at,is_read,sender_name,priority
1,2,1,"Hello world","2024-01-01T12:00:00",true,"john_doe","normal"
```

### GET `/messages/search/suggestions`
**Get search suggestions based on query**

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (integer, optional): Maximum suggestions (default: 10)

**Response:**
```json
{
    "success": true,
    "data": {
        "suggestions": ["hello world", "help me", "hey there"]
    }
}
```

### GET `/messages/search/analytics`
**Get search analytics for the current user**

**Query Parameters:**
- `days` (integer, optional): Number of days to analyze (default: 30)

**Response:**
```json
{
    "success": true,
    "data": {
        "total_searches": 45,
        "avg_results_per_search": 12.5,
        "avg_search_time": 0.18,
        "search_type_distribution": {
            "basic": 30,
            "advanced": 10,
            "boolean": 5
        },
        "popular_terms": [
            {
                "query": "hello",
                "search_count": 8,
                "avg_results": 15
            }
        ]
    }
}
```

## Threading Endpoints

### GET `/messages/threads`
**List all threads for the current user**

**Query Parameters:**
- `type` (string, optional): Filter by thread type ('private', 'group', 'system')
- `archived` (boolean, optional): Include archived threads (default: false)
- `sort` (string, optional): Sort method ('last_message_at', 'message_count', 'created_at')
- `order` (string, optional): Sort order ('asc', 'desc')
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Results per page (default: 20)

**Response:**
```json
{
    "success": true,
    "data": {
        "threads": [
            {
                "id": 1,
                "subject": "Project Discussion",
                "thread_type": "private",
                "priority": "normal",
                "message_count": 15,
                "unread_count": 3,
                "participants": [1, 2, 3],
                "last_message_at": "2024-01-01T12:00:00",
                "created_at": "2024-01-01T10:00:00",
                "is_archived": false,
                "is_pinned": false,
                "is_muted": false
            }
        ],
        "total": 25,
        "page": 1,
        "per_page": 20,
        "total_pages": 2
    }
}
```

### GET `/messages/threads/{thread_id}`
**View a specific thread with all messages**

**Path Parameters:**
- `thread_id` (integer, required): Thread ID

**Response:**
```json
{
    "success": true,
    "data": {
        "thread_tree": {
            "thread_id": 1,
            "messages": [
                {
                    "id": 1,
                    "sender_id": 1,
                    "receiver_id": 2,
                    "content": "Hello everyone!",
                    "created_at": "2024-01-01T10:00:00",
                    "is_read": true,
                    "thread_level": 0,
                    "replies": [
                        {
                            "id": 2,
                            "sender_id": 2,
                            "receiver_id": 1,
                            "content": "Hi there!",
                            "created_at": "2024-01-01T10:05:00",
                            "is_read": true,
                            "thread_level": 1,
                            "replies": []
                        }
                    ]
                }
            ],
            "total_messages": 15
        },
        "thread_stats": {
            "thread_id": 1,
            "total_messages": 15,
            "participant_count": 3,
            "max_thread_depth": 4,
            "thread_duration_days": 5,
            "messages_per_day": 3.0
        },
        "participant_names": {
            "1": "john_doe",
            "2": "jane_smith",
            "3": "bob_wilson"
        }
    }
}
```

### POST `/messages/threads/create`
**Create a new message thread**

**Request Body:**
```json
{
    "subject": "New Project Discussion",
    "participants": [2, 3, 4],
    "thread_type": "private",
    "priority": "normal"
}
```

**Parameters:**
- `subject` (string, required): Thread subject
- `participants` (array, required): List of participant user IDs
- `thread_type` (string, optional): Thread type ('private', 'group', 'system')
- `priority` (string, optional): Thread priority ('low', 'normal', 'high', 'urgent')

**Response:**
```json
{
    "success": true,
    "data": {
        "thread_id": 123,
        "subject": "New Project Discussion",
        "participants": [1, 2, 3, 4],
        "created_at": "2024-01-01T10:00:00"
    },
    "message": "Thread created successfully"
}
```

### POST `/messages/threads/{thread_id}/reply`
**Reply to a message in a thread**

**Path Parameters:**
- `thread_id` (integer, required): Thread ID

**Request Body:**
```json
{
    "receiver_id": 2,
    "content": "Thanks for the update!",
    "parent_message_id": 5,
    "content_format": "text",
    "priority": "normal"
}
```

**Parameters:**
- `receiver_id` (integer, required): Recipient user ID
- `content` (string, required): Message content
- `parent_message_id` (integer, optional): Parent message ID for reply
- `content_format` (string, optional): Content format ('text', 'html', 'markdown')
- `priority` (string, optional): Message priority

**Response:**
```json
{
    "success": true,
    "data": {
        "message_id": 456,
        "thread_id": 123,
        "parent_message_id": 5,
        "thread_level": 2,
        "created_at": "2024-01-01T10:30:00"
    },
    "message": "Reply sent successfully"
}
```

### POST `/messages/threads/{thread_id}/edit`
**Edit thread settings and participants**

**Path Parameters:**
- `thread_id` (integer, required): Thread ID

**Request Body:**
```json
{
    "subject": "Updated Thread Subject",
    "participants": [2, 3, 4, 5],
    "thread_type": "group",
    "priority": "high"
}
```

### GET `/messages/threads/{thread_id}/archive`
**Archive or unarchive a thread**

**Path Parameters:**
- `thread_id` (integer, required): Thread ID

**Response:**
```json
{
    "success": true,
    "data": {
        "thread_id": 123,
        "is_archived": true,
        "archived_at": "2024-01-01T10:00:00"
    },
    "message": "Thread archived successfully"
}
```

### GET `/messages/threads/{thread_id}/pin`
**Pin or unpin a thread**

**Path Parameters:**
- `thread_id` (integer, required): Thread ID

**Response:**
```json
{
    "success": true,
    "data": {
        "thread_id": 123,
        "is_pinned": true,
        "pinned_at": "2024-01-01T10:00:00"
    },
    "message": "Thread pinned successfully"
}
```

### GET `/messages/threads/{thread_id}/mute`
**Mute or unmute a thread**

**Path Parameters:**
- `thread_id` (integer, required): Thread ID

**Response:**
```json
{
    "success": true,
    "data": {
        "thread_id": 123,
        "is_muted": true,
        "muted_at": "2024-01-01T10:00:00"
    },
    "message": "Thread muted successfully"
}
```

### GET `/messages/threads/{thread_id}/statistics`
**View detailed statistics for a thread**

**Path Parameters:**
- `thread_id` (integer, required): Thread ID

**Response:**
```json
{
    "success": true,
    "data": {
        "thread_stats": {
            "thread_id": 1,
            "subject": "Project Discussion",
            "total_messages": 15,
            "participant_count": 3,
            "participants": {
                "1": {
                    "message_count": 8,
                    "first_message": "2024-01-01T10:00:00",
                    "last_message": "2024-01-01T15:00:00"
                }
            },
            "max_thread_depth": 4,
            "depth_distribution": {
                "0": 3,
                "1": 7,
                "2": 4,
                "3": 1
            },
            "thread_duration_days": 5,
            "messages_per_day": 3.0
        },
        "activity_summary": {
            "thread_id": 1,
            "days_analyzed": 30,
            "total_messages": 15,
            "active_participants": [1, 2],
            "daily_activity": {
                "2024-01-01": 8,
                "2024-01-02": 5,
                "2024-01-03": 2
            },
            "messages_per_day": 0.5
        }
    }
}
```

### GET `/messages/threads/suggestions`
**Get participant suggestions for thread creation**

**Query Parameters:**
- `q` (string, required): Search query for usernames
- `limit` (integer, optional): Maximum suggestions (default: 10)

**Response:**
```json
{
    "success": true,
    "data": {
        "suggestions": [
            {
                "id": 2,
                "username": "jane_smith",
                "email": "jane@example.com"
            },
            {
                "id": 3,
                "username": "bob_wilson",
                "email": "bob@example.com"
            }
        ]
    }
}
```

## Rich Text Endpoints

### POST `/messages/compose`
**Enhanced message composition with rich text support**

**Request Body:**
```json
{
    "receiver_id": 2,
    "content": "Hello **world**! This is a **test** message.",
    "content_format": "markdown",
    "priority": "normal",
    "create_thread": false,
    "thread_subject": "",
    "use_template": 0
}
```

**Parameters:**
- `receiver_id` (integer, required): Recipient user ID
- `content` (string, required): Message content
- `content_format` (string, optional): Content format ('text', 'html', 'markdown')
- `priority` (string, optional): Message priority
- `create_thread` (boolean, optional): Create new thread
- `thread_subject` (string, optional): Thread subject (if creating thread)
- `use_template` (integer, optional): Template ID to use

**Response:**
```json
{
    "success": true,
    "data": {
        "message_id": 789,
        "thread_id": 456,
        "content_html": "<p>Hello <strong>world</strong>! This is a <strong>test</strong> message.</p>",
        "content_format": "markdown",
        "created_at": "2024-01-01T10:00:00"
    },
    "message": "Message sent successfully"
}
```

### GET `/messages/templates`
**List message templates for the current user**

**Query Parameters:**
- `category` (string, optional): Filter by template category
- `public` (boolean, optional): Include public templates (default: true)

**Response:**
```json
{
    "success": true,
    "data": {
        "templates": [
            {
                "id": 1,
                "name": "Welcome Message",
                "content": "Hello {{username}}, welcome to {{forum_name}}!",
                "category": "welcome",
                "variables": ["username", "forum_name"],
                "is_public": true,
                "is_owner": false,
                "created_at": "2024-01-01T10:00:00"
            }
        ]
    }
}
```

### POST `/messages/templates/create`
**Create a new message template**

**Request Body:**
```json
{
    "name": "Project Update",
    "content": "Hi {{username}},\n\nThe project status: {{status}}\n\nBest regards,\n{{sender}}",
    "category": "project",
    "variables": "username, status, sender",
    "is_public": false
}
```

**Parameters:**
- `name` (string, required): Template name
- `content` (string, required): Template content
- `category` (string, optional): Template category
- `variables` (string, optional): Comma-separated list of variables
- `is_public` (boolean, optional): Make template public

**Response:**
```json
{
    "success": true,
    "data": {
        "template_id": 101,
        "name": "Project Update",
        "category": "project",
        "created_at": "2024-01-01T10:00:00"
    },
    "message": "Template created successfully"
}
```

### POST `/messages/templates/{template_id}/edit`
**Edit an existing template**

**Path Parameters:**
- `template_id` (integer, required): Template ID

**Request Body:**
```json
{
    "name": "Updated Template Name",
    "content": "Updated content",
    "category": "general",
    "variables": "username, forum_name",
    "is_public": true
}
```

### POST `/messages/templates/{template_id}/delete`
**Delete a template**

**Path Parameters:**
- `template_id` (integer, required): Template ID

**Response:**
```json
{
    "success": true,
    "message": "Template deleted successfully"
}
```

### GET `/messages/templates/{template_id}/preview`
**Preview a template**

**Path Parameters:**
- `template_id` (integer, required): Template ID

**Response:**
```json
{
    "success": true,
    "data": {
        "name": "Welcome Message",
        "preview": "Hello john_doe, welcome to Auto Bot Solutions Forum!",
        "variables": ["username", "forum_name"]
    }
}
```

### POST `/messages/templates/{template_id}/render`
**Render a template with variables**

**Path Parameters:**
- `template_id` (integer, required): Template ID

**Request Body:**
```json
{
    "variables": {
        "username": "john_doe",
        "forum_name": "Auto Bot Solutions Forum"
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "html": "<p>Hello john_doe, welcome to Auto Bot Solutions Forum!</p>",
        "text": "Hello john_doe, welcome to Auto Bot Solutions Forum!"
    }
}
```

### POST `/messages/rich-text/preview`
**Preview rich text content**

**Request Body:**
```json
{
    "content": "Hello **world**! This is a test.",
    "format": "markdown",
    "max_length": 100
}
```

**Parameters:**
- `content` (string, required): Content to preview
- `format` (string, optional): Content format ('text', 'html', 'markdown')
- `max_length` (integer, optional): Maximum preview length

**Response:**
```json
{
    "success": true,
    "data": {
        "preview": "Hello world! This is a test.",
        "html": "<p>Hello <strong>world</strong>! This is a test.</p>"
    }
}
```

### POST `/messages/rich-text/validate`
**Validate rich text content**

**Request Body:**
```json
{
    "content": "Hello **world**!",
    "format": "markdown"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "valid": true,
        "errors": [],
        "warnings": [],
        "stats": {
            "character_count": 14,
            "word_count": 2,
            "line_count": 1,
            "has_links": false,
            "has_images": false,
            "has_code": false
        }
    }
}
```

### POST `/messages/rich-text/format`
**Format rich text content**

**Request Body:**
```json
{
    "content": "Hello **world**!",
    "format": "markdown",
    "sanitize": true,
    "enable_emoji": true,
    "enable_markdown": true
}
```

**Parameters:**
- `content` (string, required): Content to format
- `format` (string, optional): Content format
- `sanitize` (boolean, optional): Sanitize HTML
- `enable_emoji` (boolean, optional): Convert emoji shortcodes
- `enable_markdown` (boolean, optional): Process markdown

**Response:**
```json
{
    "success": true,
    "data": {
        "html": "<p>Hello <strong>world</strong>!</p>",
        "text": "Hello world!"
    }
}
```

### GET `/messages/emoji/suggestions`
**Get emoji suggestions**

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (integer, optional): Maximum suggestions (default: 20)

**Response:**
```json
{
    "success": true,
    "data": {
        "suggestions": [
            {
                "shortcode": ":smile:",
                "emoji": "😊",
                "description": "Smile"
            },
            {
                "shortcode": ":heart:",
                "emoji": "❤️",
                "description": "Heart"
            }
        ]
    }
}
```

## Standard Message Endpoints

### GET `/messages`
**Get user's inbox messages**

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Results per page (default: 20)
- `unread_only` (boolean, optional): Show only unread messages

**Response:**
```json
{
    "success": true,
    "data": {
        "messages": [
            {
                "id": 1,
                "sender_id": 2,
                "receiver_id": 1,
                "content": "Hello world",
                "created_at": "2024-01-01T12:00:00",
                "is_read": false,
                "sender_name": "john_doe",
                "thread_id": 1,
                "priority": "normal"
            }
        ],
        "total": 50,
        "page": 1,
        "per_page": 20,
        "total_pages": 3,
        "unread_count": 15
    }
}
```

### GET `/messages/sent`
**Get user's sent messages**

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Results per page (default: 20)

### GET `/messages/{message_id}`
**Get a specific message**

**Path Parameters:**
- `message_id` (integer, required): Message ID

### POST `/messages/send`
**Send a new message**

**Request Body:**
```json
{
    "receiver_id": 2,
    "content": "Hello world!",
    "content_format": "text",
    "priority": "normal"
}
```

### PUT `/messages/{message_id}/read`
**Mark message as read**

**Path Parameters:**
- `message_id` (integer, required): Message ID

### DELETE `/messages/{message_id}`
**Delete a message**

**Path Parameters:**
- `message_id` (integer, required): Message ID

## Error Codes

| Code | Description |
|------|-------------|
| `AUTH_REQUIRED` | Authentication required |
| `PERMISSION_DENIED` | User does not have permission |
| `NOT_FOUND` | Resource not found |
| `VALIDATION_ERROR` | Input validation failed |
| `RATE_LIMITED` | Too many requests |
| `SERVER_ERROR` | Internal server error |
| `THREAD_NOT_FOUND` | Thread not found |
| `TEMPLATE_NOT_FOUND` | Template not found |
| `INVALID_SEARCH_QUERY` | Invalid search query |
| `CONTENT_TOO_LONG` | Message content too long |

## Rate Limiting

- **Search endpoints**: 100 requests per minute
- **Template endpoints**: 50 requests per minute
- **Message endpoints**: 200 requests per minute
- **Thread endpoints**: 100 requests per minute

## Pagination

All list endpoints support pagination with the following parameters:
- `page`: Page number (default: 1)
- `per_page`: Results per page (default: 20, max: 100)

Response includes pagination metadata:
- `total`: Total number of items
- `page`: Current page number
- `per_page`: Items per page
- `total_pages`: Total number of pages

## Sorting

Endpoints that support sorting use these parameters:
- `sort`: Sort field
- `order`: Sort order ('asc' or 'desc')

Common sort fields:
- `created_at`: Creation time
- `updated_at`: Last update time
- `relevance`: Search relevance score
- `message_count`: Number of messages

## Filtering

Endpoints that support filtering use these common parameters:
- `date_from`: Filter items from this date
- `date_to`: Filter items to this date
- `status`: Filter by status
- `type`: Filter by type
- `category`: Filter by category

## Webhook Support

Some endpoints support webhook notifications:
- `webhook_url`: URL to receive notifications
- `webhook_events`: List of events to subscribe to

## SDK Examples

### JavaScript/Node.js
```javascript
// Search messages
const searchResponse = await fetch('/api/v1/messages/search', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    },
    body: JSON.stringify({
        query: 'hello world',
        search_type: 'advanced',
        page: 1,
        per_page: 20
    })
});

const searchData = await searchResponse.json();
```

### Python
```python
import requests

# Create thread
thread_data = {
    'subject': 'New Discussion',
    'participants': [2, 3],
    'thread_type': 'group'
}

response = requests.post(
    '/api/v1/messages/threads/create',
    json=thread_data,
    headers={'Authorization': f'Bearer {token}'}
)

thread = response.json()
```

### cURL
```bash
# Send message with rich text
curl -X POST /api/v1/messages/compose \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "receiver_id": 2,
    "content": "Hello **world**!",
    "content_format": "markdown",
    "priority": "normal"
  }'
```

## Testing

### Unit Tests
```bash
python -m pytest tests/test_message_api.py
```

### Integration Tests
```bash
python -m pytest tests/test_message_integration.py
```

### Load Testing
```bash
python tests/load_test_message_api.py
```

## Version History

- **v1.0** - Initial API release
- **v1.1** - Added search endpoints
- **v1.2** - Added threading endpoints
- **v1.3** - Added rich text endpoints
- **v1.4** - Added template endpoints

---

**Documentation Version:** 1.0  
**Last Updated:** May 12, 2026  
**System:** Auto Bot Solutions Forum - Message API Endpoints
