# Search System Guide

## Overview

The Search System provides Elasticsearch integration with comprehensive search analytics, optimization management, and performance tracking. This guide covers implementation details, usage patterns, and best practices.

## Quick Start

### Basic Search

```python
from app.search.enhanced_service import get_enhanced_search_service

# Get search service
search_service = get_enhanced_search_service()

# Perform search
results = search_service.search(
    query_text="python tutorial",
    filters={"category": "programming"},
    pagination={"page": 1, "per_page": 10}
)
```

### Advanced Search with Analytics

```python
# Search with analytics tracking
results = search_service.search(
    query_text="machine learning",
    index_name="posts_index",
    user_id=current_user.id,
    filters={"category": "technology"},
    sort_options=[{"created_at": {"order": "desc"}}],
    pagination={"page": 1, "per_page": 20}
)

# Track search analytics automatically included
print(f"Found {results['total_results']} results in {results['query_time_ms']}ms")
```

## Core Components

### SearchIndex Model

The `SearchIndex` model provides Elasticsearch index management with statistics and health monitoring.

#### Key Features
- **Index Management**: Create, update, and delete search indices
- **Statistics Tracking**: Monitor index performance and health
- **Configuration Management**: Manage index settings and mappings
- **Health Monitoring**: Track index status and performance

#### Usage Examples

```python
from app.search.models import SearchIndex

# Create search index
index = SearchIndex.create_index(
    index_name="posts_index",
    index_type="posts",
    index_config={
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 1
        }
    },
    mapping_config={
        "properties": {
            "title": {"type": "text", "analyzer": "standard"},
            "content": {"type": "text", "analyzer": "standard"},
            "author": {"type": "keyword"},
            "category": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "created_at": {"type": "date"}
        }
    }
)

# Update index statistics
SearchIndex.update_index_stats(
    index_name="posts_index",
    document_count=1000,
    index_size_bytes=5242880,  # 5MB
    avg_query_time_ms=150.0,
    queries_per_hour=500,
    cache_hit_ratio=0.75
)

# Get index by type
posts_index = SearchIndex.get_index_by_type("posts")

# Get all active indices
all_indices = SearchIndex.get_all_active_indices()
```

### SearchQuery Model

The `SearchQuery` model provides search query tracking with analytics and performance metrics.

#### Key Features
- **Query Tracking**: Log all search queries with metadata
- **Performance Metrics**: Track query execution time and results
- **User Behavior**: Track user interactions with search results
- **Analytics**: Popular queries, no-result queries, search patterns

#### Usage Examples

```python
from app.search.models import SearchQuery

# Track search query
query = SearchQuery.track_query(
    query_text="python web development",
    index_name="posts_index",
    user_id=123,
    session_id="session_456",
    filters={"category": "programming"},
    sort_options=[{"relevance": {"order": "desc"}}],
    pagination={"page": 1, "per_page": 10},
    total_results=25,
    result_count=10,
    max_score=2.5,
    query_time_ms=45.0,
    total_time_ms=120.0,
    cache_hit=False,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)

# Update query with user behavior
query.update_results(
    clicked_results=[1, 3, 5],  # Result positions clicked
    query_success=True,
    abandoned=False
)

# Get popular queries
popular_queries = SearchQuery.get_popular_queries(
    index_name="posts_index",
    hours=24,
    limit=10
)

# Get no-result queries
no_result_queries = SearchQuery.get_no_result_queries(
    index_name="posts_index",
    hours=24,
    limit=10
)

# Get query analytics
analytics = SearchQuery.get_query_analytics(
    index_name="posts_index",
    hours=24
)
```

### SearchAnalytics Model

The `SearchAnalytics` model provides search performance metrics and optimization tracking.

#### Key Features
- **Performance Metrics**: Track search performance over time
- **Aggregation**: Hourly, daily, weekly, monthly aggregations
- **Optimization Tracking**: Monitor search optimization effectiveness
- **Health Monitoring**: Track search system health

#### Usage Examples

```python
from app.search.models import SearchAnalytics

# Record search performance metric
SearchAnalytics.record_metric(
    index_name="posts_index",
    metric_type="query_time",
    metric_value=45.0,
    metric_unit="ms",
    aggregation_period="hourly",
    sample_count=100,
    min_value=12.0,
    max_value=180.0,
    percentile_95=95.0,
    percentile_99=150.0
)

# Record cache hit rate
SearchAnalytics.record_metric(
    index_name="posts_index",
    metric_type="cache_hit_rate",
    metric_value=0.75,
    metric_unit="percent",
    aggregation_period="hourly"
)

# Get performance metrics
metrics = SearchAnalytics.get_metrics(
    index_name="posts_index",
    metric_type="query_time",
    aggregation_period="daily",
    start_date=datetime.utcnow() - timedelta(days=7),
    limit=30
)

# Get performance summary
summary = SearchAnalytics.get_performance_summary(
    index_name="posts_index",
    hours=24
)
```

### SearchOptimization Model

The `SearchOptimization` model provides search optimization management with automated improvements.

#### Key Features
- **Optimization Management**: Create and track search optimizations
- **Performance Impact**: Measure optimization effectiveness
- **Automated Improvements**: Automated search optimization suggestions
- **Version Control**: Track optimization history and rollbacks

#### Usage Examples

```python
from app.search.models import SearchOptimization

# Create optimization
optimization = SearchOptimization.create_optimization(
    index_name="posts_index",
    optimization_type="mapping",
    optimization_data={
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "suggest": {"type": "completion"}
                }
            }
        }
    },
    reason="Improve search relevance and suggestions",
    priority="high",
    auto_generated=False
)

# Apply optimization
optimization.apply_optimization(applied_config=optimization.optimization_data)

# Evaluate optimization results
optimization.evaluate_optimization(
    performance_before={
        "avg_query_time_ms": 150.0,
        "relevance_score": 0.75,
        "cache_hit_rate": 0.60
    },
    performance_after={
        "avg_query_time_ms": 120.0,
        "relevance_score": 0.85,
        "cache_hit_rate": 0.70
    },
    success_score=85.0
)

# Get pending optimizations
pending = SearchOptimization.get_pending_optimizations(
    index_name="posts_index"
)

# Get optimization history
history = SearchOptimization.get_optimization_history(
    index_name="posts_index",
    optimization_type="mapping",
    limit=20
)
```

## Enhanced Search Service

### EnhancedSearchService

The `EnhancedSearchService` provides complete Elasticsearch integration with analytics.

#### Key Features
- **Full-Text Search**: Advanced search capabilities with Elasticsearch
- **Analytics Integration**: Automatic query tracking and performance monitoring
- **Cache Support**: Search result caching for improved performance
- **Fallback Support**: Database search fallback when Elasticsearch unavailable

#### Usage Examples

```python
from app.search.enhanced_service import get_enhanced_search_service

# Get search service
search_service = get_enhanced_search_service()

# Basic search
results = search_service.search(
    query_text="python tutorial",
    pagination={"page": 1, "per_page": 10}
)

# Advanced search with filters
results = search_service.search(
    query_text="machine learning",
    index_name="posts_index",
    filters={
        "category": "technology",
        "author": "john_doe",
        "date_range": {
            "gte": "2023-01-01",
            "lte": "2023-12-31"
        }
    },
    sort_options=[
        {"relevance": {"order": "desc"}},
        {"created_at": {"order": "desc"}}
    ],
    pagination={"page": 1, "per_page": 20},
    user_id=current_user.id
)

# Search with analytics tracking
results = search_service.search(
    query_text="web development",
    user_id=current_user.id,
    session_id=session.get('session_id'),
    ip_address=request.remote_addr,
    user_agent=request.headers.get('User-Agent')
)

# Get search analytics
analytics = search_service.get_search_analytics(
    index_name="posts_index",
    hours=24
)

# Index content
search_service.index_content(
    content_type="post",
    content_id=123,
    title="Python Web Development Tutorial",
    content="Learn how to build web applications with Python...",
    author="john_doe",
    category="programming",
    tags=["python", "web", "tutorial"],
    created_at=datetime.utcnow()
)

# Remove content from index
search_service.remove_content(
    content_type="post",
    content_id=123
)
```

## Search Implementation

### Flask Application Integration

```python
from flask import Blueprint, request, jsonify
from app.search.enhanced_service import get_enhanced_search_service

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
def search():
    """Main search endpoint"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    # Parse filters
    filters = {}
    if request.args.get('category'):
        filters['category'] = request.args.get('category')
    if request.args.get('author'):
        filters['author'] = request.args.get('author')
    
    # Parse sort
    sort_options = []
    if request.args.get('sort') == 'newest':
        sort_options = [{'created_at': {'order': 'desc'}}]
    elif request.args.get('sort') == 'oldest':
        sort_options = [{'created_at': {'order': 'asc'}}]
    elif request.args.get('sort') == 'relevance':
        sort_options = [{'_score': {'order': 'desc'}}]
    
    # Perform search
    search_service = get_enhanced_search_service()
    
    try:
        results = search_service.search(
            query_text=query,
            filters=filters,
            sort_options=sort_options,
            pagination={'page': page, 'per_page': per_page},
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        return jsonify({
            'results': results['results'],
            'total': results['total_results'],
            'page': page,
            'per_page': per_page,
            'query_time_ms': results['query_time_ms'],
            'total_time_ms': results['total_time_ms']
        })
        
    except Exception as e:
        return jsonify({'error': 'Search temporarily unavailable'}), 503

@search_bp.route('/search/suggestions')
def search_suggestions():
    """Search suggestions endpoint"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    search_service = get_enhanced_search_service()
    
    try:
        # Use completion suggester
        suggestions = search_service.get_suggestions(query)
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        return jsonify({'suggestions': []})

@search_bp.route('/search/analytics')
def search_analytics():
    """Search analytics endpoint"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    search_service = get_enhanced_search_service()
    analytics = search_service.get_search_analytics(hours=24)
    
    return jsonify(analytics)
```

### Content Indexing

```python
from app.search.enhanced_service import get_enhanced_search_service

class SearchIndexer:
    """Handles content indexing for search"""
    
    def __init__(self):
        self.search_service = get_enhanced_search_service()
    
    def index_post(self, post):
        """Index a post for search"""
        self.search_service.index_content(
            content_type="post",
            content_id=post.id,
            title=post.title,
            content=post.content,
            author=post.author.username if post.author else None,
            category=post.category.name if post.category else None,
            tags=[tag.name for tag in post.tags],
            created_at=post.created_at,
            updated_at=post.updated_at
        )
    
    def index_comment(self, comment):
        """Index a comment for search"""
        self.search_service.index_content(
            content_type="comment",
            content_id=comment.id,
            title=f"Comment on {comment.post.title}",
            content=comment.content,
            author=comment.author.username if comment.author else None,
            created_at=comment.created_at,
            updated_at=comment.updated_at
        )
    
    def index_user(self, user):
        """Index a user profile for search"""
        self.search_service.index_content(
            content_type="user",
            content_id=user.id,
            title=user.username,
            content=user.bio or "",
            author=user.username,
            tags=user.skills or [],
            created_at=user.created_at
        )
    
    def remove_content(self, content_type, content_id):
        """Remove content from search index"""
        self.search_service.remove_content(content_type, content_id)
    
    def batch_index_posts(self, posts):
        """Index multiple posts efficiently"""
        for post in posts:
            self.index_post(post)
    
    def reindex_all_content(self):
        """Reindex all content in the system"""
        # Index posts
        posts = Post.query.all()
        self.batch_index_posts(posts)
        
        # Index comments
        comments = Comment.query.all()
        for comment in comments:
            self.index_comment(comment)
        
        # Index users
        users = User.query.all()
        for user in users:
            self.index_user(user)
```

### Background Search Tasks

```python
from celery import Celery
from app.search.enhanced_service import get_enhanced_search_service

celery = Celery('search_tasks')

@celery.task
def index_content_task(content_type, content_id):
    """Background content indexing"""
    search_service = get_enhanced_search_service()
    
    # Get content from database
    if content_type == "post":
        post = Post.query.get(content_id)
        if post:
            search_service.index_content(
                content_type=content_type,
                content_id=content_id,
                title=post.title,
                content=post.content,
                author=post.author.username if post.author else None,
                category=post.category.name if post.category else None,
                tags=[tag.name for tag in post.tags],
                created_at=post.created_at
            )

@celery.task
def remove_content_task(content_type, content_id):
    """Background content removal"""
    search_service = get_enhanced_search_service()
    search_service.remove_content(content_type, content_id)

@celery.task
def optimize_search_index(index_name):
    """Background search index optimization"""
    from app.search.models import SearchOptimization
    
    # Create optimization task
    optimization = SearchOptimization.create_optimization(
        index_name=index_name,
        optimization_type="optimization",
        optimization_data={
            "force_merge": {"max_num_segments": 1}
        },
        reason="Scheduled index optimization",
        auto_generated=True
    )
    
    # Apply optimization
    search_service = get_enhanced_search_service()
    try:
        # Force merge segments
        search_service.optimize_index(index_name)
        optimization.apply_optimization()
    except Exception as e:
        optimization.mark_failed([str(e)])

@celery.task
def generate_search_analytics():
    """Generate daily search analytics"""
    from app.search.models import SearchQuery, SearchAnalytics
    
    # Generate query analytics
    popular_queries = SearchQuery.get_popular_queries(hours=24, limit=50)
    
    for query_data in popular_queries:
        SearchAnalytics.record_metric(
            index_name="posts_index",
            metric_type="popular_query",
            metric_value=query_data['count'],
            metadata={
                "query": query_data['query'],
                "avg_results": query_data['avg_results']
            }
        )
    
    # Generate no-result queries
    no_result_queries = SearchQuery.get_no_result_queries(hours=24, limit=20)
    
    for query_data in no_result_queries:
        SearchAnalytics.record_metric(
            index_name="posts_index",
            metric_type="no_result_query",
            metric_value=query_data['count'],
            metadata={
                "query": query_data['query']
            }
        )
```

## Advanced Search Features

### Search Result Highlighting

```python
from app.search.enhanced_service import get_enhanced_search_service

def search_with_highlighting(query, filters=None):
    """Search with result highlighting"""
    search_service = get_enhanced_search_service()
    
    results = search_service.search(
        query_text=query,
        filters=filters,
        highlight=True,
        highlight_fields=["title", "content"],
        highlight_tags=["<mark>", "</mark>"]
    )
    
    return results

# Usage
results = search_with_highlighting(
    "python programming",
    filters={"category": "technology"}
)

for result in results['results']:
    print(f"Title: {result.get('highlight', {}).get('title', [result['title']])[0]}")
    print(f"Content: {result.get('highlight', {}).get('content', [result['content'][:200] + '...'])[0]}")
```

### Search Suggestions

```python
def get_search_suggestions(partial_query):
    """Get search suggestions based on partial query"""
    search_service = get_enhanced_search_service()
    
    suggestions = search_service.get_suggestions(
        partial_query,
        suggest_field="title_suggest",
        size=10
    )
    
    return suggestions

# Usage
suggestions = get_search_suggestions("pyth")
# Returns: ["python", "python tutorial", "python programming", ...]
```

### Faceted Search

```python
def faceted_search(query, facets=None):
    """Perform faceted search with aggregations"""
    search_service = get_enhanced_search_service()
    
    # Define facets
    search_facets = {
        "categories": {
            "terms": {"field": "category.keyword"}
        },
        "authors": {
            "terms": {"field": "author.keyword"}
        },
        "tags": {
            "terms": {"field": "tags.keyword"}
        },
        "date_ranges": {
            "date_histogram": {
                "field": "created_at",
                "calendar_interval": "month"
            }
        }
    }
    
    results = search_service.search(
        query_text=query,
        facets=search_facets,
        pagination={"page": 1, "per_page": 10}
    )
    
    return results

# Usage
results = faceted_search("python")
facets = results['facets']
print("Categories:", facets['categories']['buckets'])
print("Authors:", facets['authors']['buckets'])
```

### Search Performance Optimization

```python
from app.search.models import SearchOptimization

def optimize_search_performance():
    """Optimize search performance automatically"""
    search_service = get_enhanced_search_service()
    
    # Analyze slow queries
    slow_queries = SearchQuery.query.filter(
        SearchQuery.query_time_ms > 1000  # > 1 second
    ).all()
    
    # Group by query patterns
    query_patterns = {}
    for query in slow_queries:
        pattern = extract_query_pattern(query.query_text)
        if pattern not in query_patterns:
            query_patterns[pattern] = []
        query_patterns[pattern].append(query)
    
    # Generate optimizations
    for pattern, queries in query_patterns.items():
        if len(queries) >= 5:  # Optimize frequently slow patterns
            optimization = SearchOptimization.create_optimization(
                index_name="posts_index",
                optimization_type="query_optimization",
                optimization_data={
                    "query_pattern": pattern,
                    "suggested_mapping": generate_optimized_mapping(pattern),
                    "performance_improvement": estimate_improvement(queries)
                },
                reason=f"Optimize slow query pattern: {pattern}",
                priority="high",
                auto_generated=True
            )
            
            # Apply optimization if confidence is high
            if optimization.optimization_data.get('performance_improvement', 0) > 30:
                search_service.apply_optimization(optimization.id)

def extract_query_pattern(query_text):
    """Extract query pattern from search text"""
    # Simple pattern extraction - can be enhanced with NLP
    words = query_text.lower().split()
    return tuple(sorted(words))

def generate_optimized_mapping(pattern):
    """Generate optimized mapping for query pattern"""
    # Generate field mappings based on query pattern
    return {
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "pattern": {"type": "text", "analyzer": "pattern_analyzer"}
                }
            }
        }
    }

def estimate_improvement(queries):
    """Estimate performance improvement for optimization"""
    avg_time = sum(q.query_time_ms for q in queries) / len(queries)
    # Assume optimization will reduce time by 30%
    return 30.0
```

## Configuration

### Search Configuration

```python
# app/search/config.py
SEARCH_CONFIG = {
    'elasticsearch_url': 'http://localhost:9200',
    'default_index': 'forum_search',
    'cache_enabled': True,
    'cache_timeout': 300,  # 5 minutes
    'max_results': 1000,
    'default_per_page': 10,
    'highlight_enabled': True,
    'suggestions_enabled': True,
    'analytics_enabled': True,
    'optimization_enabled': True
}

# Index configurations
INDEX_CONFIGS = {
    'posts': {
        'settings': {
            'number_of_shards': 3,
            'number_of_replicas': 1,
            'analysis': {
                'analyzer': {
                    'content_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'stop', 'snowball']
                    }
                }
            }
        },
        'mappings': {
            'properties': {
                'title': {
                    'type': 'text',
                    'analyzer': 'content_analyzer',
                    'fields': {
                        'keyword': {'type': 'keyword'},
                        'suggest': {'type': 'completion'}
                    }
                },
                'content': {
                    'type': 'text',
                    'analyzer': 'content_analyzer'
                },
                'author': {'type': 'keyword'},
                'category': {'type': 'keyword'},
                'tags': {'type': 'keyword'},
                'created_at': {'type': 'date'},
                'updated_at': {'type': 'date'}
            }
        }
    }
}
```

### Environment-Specific Configuration

```python
# Development
SEARCH_CONFIG = {
    'elasticsearch_url': 'http://localhost:9200',
    'cache_enabled': False,
    'analytics_enabled': False,
    'optimization_enabled': False
}

# Production
SEARCH_CONFIG = {
    'elasticsearch_url': 'http://es-cluster:9200',
    'cache_enabled': True,
    'cache_timeout': 600,
    'analytics_enabled': True,
    'optimization_enabled': True,
    'cluster_nodes': [
        'http://es-node1:9200',
        'http://es-node2:9200',
        'http://es-node3:9200'
    ]
}
```

## Best Practices

### Query Optimization

```python
# Use specific field searches
results = search_service.search(
    query_text="title:python AND content:web",
    filters={"category": "programming"}
)

# Use appropriate analyzers
results = search_service.search(
    query_text="python programming",
    analyzer="content_analyzer"
)

# Limit result size for performance
results = search_service.search(
    query_text="python",
    pagination={"page": 1, "per_page": 20}
)
```

### Index Management

```python
# Use appropriate sharding strategy
# For high-volume indices
INDEX_CONFIGS['posts']['settings']['number_of_shards'] = 5

# For time-based data
INDEX_CONFIGS['logs']['settings']['number_of_shards'] = 3
INDEX_CONFIGS['logs']['settings']['number_of_replicas'] = 1

# Use index templates for consistent configuration
def setup_index_templates():
    """Setup index templates for consistent configuration"""
    template = {
        "index_patterns": ["posts-*"],
        "template": INDEX_CONFIGS['posts']
    }
    # Apply template to Elasticsearch
```

### Performance Monitoring

```python
from app.search.models import SearchAnalytics, SearchQuery

def monitor_search_performance():
    """Monitor search performance and alert on issues"""
    # Check query time performance
    avg_query_time = SearchAnalytics.get_avg_query_time(hours=1)
    
    if avg_query_time > 500:  # 500ms threshold
        send_alert("Search performance degraded", {
            'avg_query_time_ms': avg_query_time
        })
    
    # Check error rate
    error_rate = SearchQuery.get_error_rate(hours=1)
    
    if error_rate > 0.05:  # 5% error rate threshold
        send_alert("Search error rate high", {
            'error_rate': error_rate
        })
    
    # Check index health
    index_health = get_index_health()
    
    if index_health['status'] != 'green':
        send_alert("Search index health issue", index_health)
```

### Error Handling

```python
from app.search.enhanced_service import get_enhanced_search_service

def robust_search(query, **kwargs):
    """Robust search with fallback"""
    search_service = get_enhanced_search_service()
    
    try:
        # Try Elasticsearch search
        results = search_service.search(query_text=query, **kwargs)
        return results
        
    except ConnectionError:
        # Elasticsearch unavailable, fallback to database search
        return database_search(query, **kwargs)
        
    except Exception as e:
        # Log error and return empty results
        logger.error(f"Search error: {e}")
        return {
            'results': [],
            'total_results': 0,
            'query_time_ms': 0,
            'total_time_ms': 0,
            'error': 'Search temporarily unavailable'
        }

def database_search(query, **kwargs):
    """Fallback database search"""
    # Implement basic database search
    posts = Post.query.filter(
        or_(
            Post.title.contains(query),
            Post.content.contains(query)
        )
    ).limit(kwargs.get('per_page', 10)).all()
    
    return {
        'results': [post.to_dict() for post in posts],
        'total_results': len(posts),
        'query_time_ms': 0,
        'total_time_ms': 0,
        'fallback': True
    }
```

## Monitoring and Debugging

### Search Analytics Dashboard

```python
from flask import Blueprint, render_template, jsonify

search_analytics_bp = Blueprint('search_analytics', __name__)

@search_analytics_bp.route('/search/analytics/dashboard')
def analytics_dashboard():
    """Search analytics dashboard"""
    return render_template('search/analytics_dashboard.html')

@search_analytics_bp.route('/search/analytics/api/metrics')
def analytics_metrics_api():
    """Search analytics API"""
    hours = request.args.get('hours', 24, type=int)
    
    # Query analytics
    query_analytics = SearchQuery.get_query_analytics(hours=hours)
    
    # Popular queries
    popular_queries = SearchQuery.get_popular_queries(hours=hours, limit=10)
    
    # No-result queries
    no_result_queries = SearchQuery.get_no_result_queries(hours=hours, limit=10)
    
    # Performance metrics
    performance_metrics = SearchAnalytics.get_performance_summary(hours=hours)
    
    return jsonify({
        'query_analytics': query_analytics,
        'popular_queries': popular_queries,
        'no_result_queries': no_result_queries,
        'performance_metrics': performance_metrics
    })
```

### Debugging Tools

```python
def debug_search_query(query, **kwargs):
    """Debug search query execution"""
    search_service = get_enhanced_search_service()
    
    print(f"Query: {query}")
    print(f"Filters: {kwargs.get('filters', {})}")
    print(f"Sort: {kwargs.get('sort_options', [])}")
    
    # Check Elasticsearch connection
    if search_service.elasticsearch_client:
        try:
            health = search_service.elasticsearch_client.cluster.health()
            print(f"Elasticsearch health: {health['status']}")
        except Exception as e:
            print(f"Elasticsearch connection error: {e}")
    else:
        print("Elasticsearch not available")
    
    # Execute search with timing
    start_time = time.time()
    results = search_service.search(query_text=query, **kwargs)
    end_time = time.time()
    
    print(f"Search time: {(end_time - start_time) * 1000:.2f}ms")
    print(f"Results: {len(results['results'])}")
    print(f"Total: {results['total_results']}")
    
    return results

def debug_index_mapping(index_name):
    """Debug index mapping"""
    search_service = get_enhanced_search_service()
    
    if search_service.elasticsearch_client:
        try:
            mapping = search_service.elasticsearch_client.indices.get_mapping(index=index_name)
            print(f"Index mapping for {index_name}:")
            print(json.dumps(mapping, indent=2))
        except Exception as e:
            print(f"Error getting mapping: {e}")
```

---

*Guide Last Updated: May 13, 2026*  
*Implementation Status: Production Ready*
