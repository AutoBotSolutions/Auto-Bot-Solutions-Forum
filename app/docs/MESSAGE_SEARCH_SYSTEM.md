# Message Search and Filtering System

## Overview

The Message Search and Filtering System provides comprehensive search capabilities for private messages with advanced filtering, Boolean operators, search analytics, and export functionality. This system enables users to efficiently find and organize their messages with enterprise-grade search features.

## Features

### 🔍 **Search Capabilities**
- **Full-text search** with keyword extraction and relevance scoring
- **Advanced search** with Boolean operators (AND, OR, NOT)
- **Field-specific search** (sender:john, content:hello, date:2024-01-01)
- **Search result highlighting** with HTML markup
- **Search suggestions** based on user history
- **Popular search terms** tracking

### 📊 **Filtering Options**
- **Date filtering** (from/to dates)
- **Sender filtering** (specific users)
- **Status filtering** (read/unread)
- **Priority filtering** (low, normal, high, urgent)
- **Attachment filtering** (with/without attachments)
- **Thread filtering** (specific conversations)

### 📈 **Analytics and Export**
- **Search analytics** with query tracking and performance metrics
- **Search result export** to CSV format
- **Popular terms** identification
- **Search session** tracking

## Architecture

### Core Components

#### **MessageSearchEngine** (`app/utils/message_search.py`)
```python
class MessageSearchEngine:
    """Advanced message search engine with full-text search capabilities"""
    
    def search_messages(self, query, user_id, filters=None, sort_by='relevance', 
                        page=1, per_page=20, search_type='basic')
    def _build_basic_search(self, query)
    def _build_advanced_search(self, query)
    def _build_boolean_search(self, query)
    def _highlight_search_terms(self, content, query)
    def _calculate_relevance_score(self, message, query)
```

#### **MessageSearchIndex** (Database Model)
```python
class MessageSearchIndex(db.Model):
    """Model for message search indexing"""
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    content_vector = db.Column(db.Text)  # Full-text search vector
    keywords = db.Column(db.Text)  # Extracted keywords
    search_rank = db.Column(db.Float)  # Search ranking score
    word_count = db.Column(db.Integer)
    sentiment_score = db.Column(db.Float)
```

#### **MessageSearchAnalytics** (Database Model)
```python
class MessageSearchAnalytics(db.Model):
    """Model for tracking search analytics"""
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    search_query = db.Column(db.Text)
    search_type = db.Column(db.String(20))  # 'basic', 'advanced', 'boolean'
    results_count = db.Column(db.Integer)
    search_time = db.Column(db.Float)  # Search execution time
    filters = db.Column(db.Text)  # JSON of applied filters
```

## API Endpoints

### Search Routes

#### **GET/POST `/messages/search`**
**Advanced message search with filtering options**

**Parameters:**
- `query` (string): Search query
- `date_from` (date): Filter messages from this date
- `date_to` (date): Filter messages to this date
- `sender_id` (integer): Filter by specific sender
- `is_read` (boolean): Filter by read status
- `priority` (string): Filter by priority level
- `has_attachments` (boolean): Filter by attachment presence
- `thread_id` (integer): Filter by specific thread
- `sort_by` (string): Sort method ('relevance', 'date', 'sender')
- `search_type` (string): Search type ('basic', 'advanced', 'boolean')
- `page` (integer): Page number
- `per_page` (integer): Results per page

**Response:**
```json
{
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
            "relevance_score": 4.5
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
```

#### **GET `/messages/search/advanced`**
**Advanced search with Boolean operators and field-specific search**

#### **GET `/messages/search/export`**
**Export search results to CSV format**

**Parameters:**
- `query` (string): Search query
- `search_type` (string): Search type
- `sort_by` (string): Sort method
- All filter parameters from basic search

#### **GET `/messages/search/suggestions`**
**Get search suggestions based on query**

**Parameters:**
- `q` (string): Search query
- `limit` (integer): Maximum suggestions (default: 10)

**Response:**
```json
{
    "suggestions": ["hello world", "help me", "hey there"]
}
```

#### **GET `/messages/search/analytics`**
**Get search analytics for the current user**

**Parameters:**
- `days` (integer): Number of days to analyze (default: 30)

**Response:**
```json
{
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
```

## Search Types

### **Basic Search**
Simple keyword search with automatic stop-word filtering.

**Example:** `hello world message`

### **Advanced Search**
Field-specific search with quoted phrases and exclusions.

**Syntax:**
- `field:value` - Search in specific field
- `"exact phrase"` - Search for exact phrase
- `-exclude_term` - Exclude term from results

**Examples:**
- `sender:john content:hello`
- `"hello world" -goodbye`
- `date:2024-01-01 priority:urgent`

### **Boolean Search**
Advanced Boolean logic with AND, OR, NOT operators.

**Syntax:**
- `term1 AND term2` - Both terms must be present
- `term1 OR term2` - Either term must be present
- `NOT term` - Term must not be present

**Examples:**
- `hello AND world`
- `urgent OR important`
- `hello AND (world OR universe) NOT goodbye`

## Utility Functions

### **Search Utilities** (`app/utils/message_search.py`)

#### **extract_keywords(content)**
Extract relevant keywords from message content.

```python
keywords = extract_keywords("Hello world, this is a test message")
# Returns: '["hello", "world", "test", "message"]'
```

#### **generate_search_vector(content)**
Generate search vector for full-text search.

```python
vector = generate_search_vector("Hello world, this is a test message!")
# Returns: "hello world this is a test message"
```

#### **analyze_content(content)**
Analyze message content for sentiment and metrics.

```python
analysis = analyze_content("This is a good and wonderful message")
# Returns: {'sentiment': 0.8, 'word_count': 7, 'positive_words': 2, 'negative_words': 0}
```

#### **get_search_suggestions(query, user_id, limit)**
Get search suggestions based on user history.

#### **get_popular_search_terms(days, limit)**
Get most popular search terms across all users.

#### **get_search_analytics_summary(user_id, days)**
Get comprehensive search analytics for a user.

## Database Schema

### **Message Model Enhancements**
```sql
ALTER TABLE message ADD COLUMN thread_id INTEGER;
ALTER TABLE message ADD COLUMN parent_message_id INTEGER;
ALTER TABLE message ADD COLUMN thread_level INTEGER DEFAULT 0;
ALTER TABLE message ADD COLUMN content_html TEXT;
ALTER TABLE message ADD COLUMN content_format VARCHAR(20) DEFAULT 'text';
ALTER TABLE message ADD COLUMN is_rich_text BOOLEAN DEFAULT 0;
ALTER TABLE message ADD COLUMN has_attachments BOOLEAN DEFAULT 0;
ALTER TABLE message ADD COLUMN search_vector TEXT;
ALTER TABLE message ADD COLUMN search_keywords TEXT;
ALTER TABLE message ADD COLUMN forwarded_from_id INTEGER;
ALTER TABLE message ADD COLUMN forwarded_count INTEGER DEFAULT 0;
ALTER TABLE message ADD COLUMN is_deleted BOOLEAN DEFAULT 0;
ALTER TABLE message ADD COLUMN is_archived BOOLEAN DEFAULT 0;
ALTER TABLE message ADD COLUMN priority VARCHAR(20) DEFAULT 'normal';
ALTER TABLE message ADD COLUMN is_starred BOOLEAN DEFAULT 0;
```

### **New Tables**
```sql
CREATE TABLE message_search_index (
    id INTEGER PRIMARY KEY,
    message_id INTEGER REFERENCES message(id),
    content_vector TEXT NOT NULL,
    keywords TEXT,
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    search_rank FLOAT DEFAULT 1.0,
    search_frequency INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    language VARCHAR(10) DEFAULT 'en',
    sentiment_score FLOAT,
    is_indexed BOOLEAN DEFAULT 1,
    index_version INTEGER DEFAULT 1
);

CREATE TABLE message_search_analytics (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES user(id),
    search_query TEXT NOT NULL,
    search_type VARCHAR(20) DEFAULT 'basic',
    results_count INTEGER DEFAULT 0,
    search_time REAL NOT NULL,
    filters TEXT,
    sort_by VARCHAR(20),
    clicked_result_id INTEGER,
    session_id VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Performance Optimization

### **Search Indexing**
- Automatic message indexing on creation/update
- Keyword extraction for faster searches
- Search vector generation for full-text search
- Sentiment analysis for content categorization

### **Query Optimization**
- Efficient database queries with proper indexing
- Search result caching for frequently used queries
- Pagination to handle large result sets
- Relevance scoring for result ranking

### **Analytics Tracking**
- Search performance monitoring
- Popular terms identification
- User behavior analysis
- Search pattern optimization

## Security Considerations

### **Input Validation**
- SQL injection prevention with parameterized queries
- XSS protection in search result highlighting
- Search query length limitations
- Malicious query detection

### **Access Control**
- User-specific search results (only user's own messages)
- Search analytics privacy (user-specific data only)
- Rate limiting on search endpoints
- Search query logging for security monitoring

### **Data Protection**
- Search query encryption in analytics
- Personal data anonymization in reports
- Search history retention policies
- GDPR compliance considerations

## Usage Examples

### **Basic Search**
```python
from app.utils.message_search import MessageSearchEngine

search_engine = MessageSearchEngine()
results = search_engine.search_messages(
    query="hello world",
    user_id=current_user.id,
    page=1,
    per_page=20
)
```

### **Advanced Search with Filters**
```python
filters = {
    'date_from': datetime(2024, 1, 1),
    'sender_id': 2,
    'priority': 'high',
    'is_read': False
}

results = search_engine.search_messages(
    query="urgent project",
    user_id=current_user.id,
    filters=filters,
    sort_by='date',
    search_type='advanced'
)
```

### **Boolean Search**
```python
results = search_engine.search_messages(
    query="project AND (urgent OR important) NOT completed",
    user_id=current_user.id,
    search_type='boolean'
)
```

### **Search Analytics**
```python
from app.utils.message_search import get_search_analytics_summary

analytics = get_search_analytics_summary(current_user.id, days=30)
print(f"Total searches: {analytics['total_searches']}")
print(f"Average results: {analytics['avg_results_per_search']}")
```

## Troubleshooting

### **Common Issues**

#### **Search Results Empty**
- Check if user has messages in the database
- Verify search query is not too restrictive
- Ensure filters are not conflicting

#### **Slow Search Performance**
- Check if search indexes are properly created
- Verify database query optimization
- Consider search result caching

#### **Search Analytics Not Working**
- Ensure analytics tracking is enabled
- Check database connection for analytics storage
- Verify user permissions for analytics access

### **Debug Mode**
Enable debug logging for search operations:

```python
import logging
logging.getLogger('app.utils.message_search').setLevel(logging.DEBUG)
```

## Migration Guide

### **Database Migration**
Run the migration script to add new fields and tables:

```bash
python migrate_message_system.py
```

### **Index Existing Messages**
Create search indexes for existing messages:

```python
from app.utils.message_search import MessageSearchIndex
from app.models import Message

messages = Message.query.all()
for message in messages:
    MessageSearchIndex.index_message(message)
```

## Future Enhancements

### **Planned Features**
- **Elasticsearch Integration** for advanced search capabilities
- **Machine Learning** for search result ranking
- **Voice Search** support
- **Search History** with personalization
- **Advanced Analytics** with visualization dashboard

### **Performance Improvements**
- **Search Result Caching** with Redis
- **Distributed Search** for large datasets
- **Real-time Search** suggestions
- **Search API** rate limiting optimization

---

**Documentation Version:** 1.0  
**Last Updated:** May 12, 2026  
**System:** Auto Bot Solutions Forum - Message Search System
