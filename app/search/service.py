"""
Search Service

Advanced search functionality with Elasticsearch integration for the Auto Bot Solutions Forum.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from flask import current_app
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, RequestError
from sqlalchemy import and_, or_, desc, func
from app import db
from app.search.models import SearchIndex, SearchQuery, SearchAnalytics, SearchOptimization
from app.models import User, Post, Comment, Category

logger = logging.getLogger(__name__)

class SearchService:
    """Advanced search service with Elasticsearch integration"""
    
    def __init__(self):
        self.elasticsearch_client = None
        self.cache_enabled = current_app.config.get('SEARCH_CACHE_ENABLED', True)
        self.cache_timeout = current_app.config.get('SEARCH_CACHE_TIMEOUT', 300)  # 5 minutes
        self._init_elasticsearch()
    
    def _init_elasticsearch(self):
        """Initialize Elasticsearch client"""
        try:
            elasticsearch_url = current_app.config.get('ELASTICSEARCH_URL', 'http://localhost:9200')
            self.elasticsearch_client = Elasticsearch([elasticsearch_url])
            
            # Test connection
            if self.elasticsearch_client.ping():
                logger.info("Connected to Elasticsearch")
                self._create_index()
            else:
                logger.warning("Elasticsearch connection failed, using database fallback")
                self.elasticsearch_client = None
        except Exception as e:
            logger.warning(f"Elasticsearch not available: {str(e)}")
            self.elasticsearch_client = None
    
    def _create_index(self):
        """Create Elasticsearch index with proper mapping"""
        if not self.elasticsearch_client:
            return
        
        index_name = current_app.config.get('ELASTICSEARCH_INDEX', 'forum_search')
        
        # Define mapping for search index
        mapping = {
            "mappings": {
                "properties": {
                    "content_type": {"type": "keyword"},
                    "content_id": {"type": "integer"},
                    "indexed_content": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "title": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "search_vector": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "author_id": {"type": "integer"},
                    "category_id": {"type": "integer"},
                    "tags": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "view_count": {"type": "integer"},
                    "vote_score": {"type": "integer"},
                    "comment_count": {"type": "integer"},
                    "relevance_score": {"type": "float"}
                }
            }
        }
        
        try:
            if not self.elasticsearch_client.indices.exists(index=index_name):
                self.elasticsearch_client.indices.create(index=index_name, body=mapping)
                logger.info(f"Created Elasticsearch index: {index_name}")
        except Exception as e:
            logger.error(f"Error creating Elasticsearch index: {str(e)}")
    
    def index_content(self, content_type: str, content_id: int, force: bool = False):
        """Index content in Elasticsearch"""
        if not self.elasticsearch_client:
            return False
        
        try:
            # Get search index from database
            search_index = SearchIndex.query.filter_by(
                content_type=content_type,
                content_id=content_id
            ).first()
            
            if not search_index:
                return False
            
            # Prepare document for Elasticsearch
            doc = search_index.to_dict()
            index_name = current_app.config.get('ELASTICSEARCH_INDEX', 'forum_search')
            doc_id = f"{content_type}_{content_id}"
            
            # Index document
            self.elasticsearch_client.index(
                index=index_name,
                id=doc_id,
                body=doc,
                refresh=True if force else 'wait_for'
            )
            
            logger.debug(f"Indexed {content_type} {content_id} in Elasticsearch")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing content: {str(e)}")
            return False
    
    def search(self, query: str, filters: Dict[str, Any] = None, 
               page: int = 1, per_page: int = 20, 
               user_id: int = None, ip_address: str = None) -> Dict[str, Any]:
        """
        Perform search with Elasticsearch or database fallback
        
        Args:
            query: Search query string
            filters: Search filters (date, author, category, tags)
            page: Page number
            per_page: Results per page
            user_id: User ID for analytics
            ip_address: IP address for analytics
            
        Returns:
            Dictionary with search results and metadata
        """
        start_time = datetime.utcnow()
        
        if self.elasticsearch_client:
            results = self._search_elasticsearch(query, filters, page, per_page)
        else:
            results = self._search_database(query, filters, page, per_page)
        
        # Log search analytics
        search_time = (datetime.utcnow() - start_time).total_seconds()
        self._log_search_analytics(query, results['total'], user_id, ip_address)
        
        # Add search metadata
        results['search_time'] = search_time
        results['query'] = query
        results['page'] = page
        results['per_page'] = per_page
        results['filters'] = filters or {}
        
        return results
    
    def _search_elasticsearch(self, query: str, filters: Dict[str, Any], 
                            page: int, per_page: int) -> Dict[str, Any]:
        """Search using Elasticsearch"""
        try:
            index_name = current_app.config.get('ELASTICSEARCH_INDEX', 'forum_search')
            
            # Build Elasticsearch query
            es_query = self._build_elasticsearch_query(query, filters)
            
            # Add pagination and sorting
            from_num = (page - 1) * per_page
            es_query['from'] = from_num
            es_query['size'] = per_page
            
            # Sort by relevance score, then by date
            es_query['sort'] = [
                {"relevance_score": {"order": "desc"}},
                {"created_at": {"order": "desc"}}
            ]
            
            # Execute search
            response = self.elasticsearch_client.search(index=index_name, body=es_query)
            
            # Process results
            hits = response['hits']
            results = []
            
            for hit in hits['hits']:
                result = hit['_source']
                result['score'] = hit['_score']
                result['highlight'] = hit.get('highlight', {})
                results.append(result)
            
            return {
                'results': results,
                'total': hits['total']['value'],
                'pages': (hits['total']['value'] + per_page - 1) // per_page,
                'has_next': from_num + per_page < hits['total']['value'],
                'has_prev': page > 1
            }
            
        except Exception as e:
            logger.error(f"Elasticsearch search error: {str(e)}")
            # Fallback to database search
            return self._search_database(query, filters, page, per_page)
    
    def _build_elasticsearch_query(self, query: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build Elasticsearch query with filters"""
        es_query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "indexed_content": {},
                    "search_vector": {}
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            }
        }
        
        # Add main search query
        if query:
            es_query['query']['bool']['must'].append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title^3",
                        "indexed_content^2",
                        "search_vector"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        else:
            es_query['query']['bool']['must'].append({"match_all": {}})
        
        # Add filters
        if filters:
            # Content type filter
            if 'content_type' in filters:
                es_query['query']['bool']['filter'].append({
                    "term": {"content_type": filters['content_type']}
                })
            
            # Author filter
            if 'author_id' in filters:
                es_query['query']['bool']['filter'].append({
                    "term": {"author_id": filters['author_id']}
                })
            
            # Category filter
            if 'category_id' in filters:
                es_query['query']['bool']['filter'].append({
                    "term": {"category_id": filters['category_id']}
                })
            
            # Tags filter
            if 'tags' in filters and filters['tags']:
                es_query['query']['bool']['filter'].append({
                    "terms": {"tags": filters['tags']}
                })
            
            # Date range filter
            if 'date_from' in filters or 'date_to' in filters:
                date_range = {}
                if 'date_from' in filters:
                    date_range['gte'] = filters['date_from'].isoformat()
                if 'date_to' in filters:
                    date_range['lte'] = filters['date_to'].isoformat()
                
                es_query['query']['bool']['filter'].append({
                    "range": {"created_at": date_range}
                })
        
        return es_query
    
    def _search_database(self, query: str, filters: Dict[str, Any], 
                        page: int, per_page: int) -> Dict[str, Any]:
        """Search using database (fallback)"""
        try:
            # Build database query
            db_query = SearchIndex.query
            
            # Add text search
            if query:
                search_terms = query.split()
                search_conditions = []
                
                for term in search_terms:
                    search_conditions.append(
                        or_(
                            SearchIndex.title.ilike(f'%{term}%'),
                            SearchIndex.indexed_content.ilike(f'%{term}%'),
                            SearchIndex.search_vector.ilike(f'%{term}%')
                        )
                    )
                
                if search_conditions:
                    db_query = db_query.filter(and_(*search_conditions))
            
            # Add filters
            if filters:
                # Content type filter
                if 'content_type' in filters:
                    db_query = db_query.filter(SearchIndex.content_type == filters['content_type'])
                
                # Author filter
                if 'author_id' in filters:
                    db_query = db_query.filter(SearchIndex.author_id == filters['author_id'])
                
                # Category filter
                if 'category_id' in filters:
                    db_query = db_query.filter(SearchIndex.category_id == filters['category_id'])
                
                # Tags filter
                if 'tags' in filters and filters['tags']:
                    for tag in filters['tags']:
                        db_query = db_query.filter(SearchIndex.tags.like(f'%{tag}%'))
                
                # Date range filter
                if 'date_from' in filters:
                    db_query = db_query.filter(SearchIndex.created_at >= filters['date_from'])
                if 'date_to' in filters:
                    db_query = db_query.filter(SearchIndex.created_at <= filters['date_to'])
            
            # Order by relevance score and date
            db_query = db_query.order_by(desc(SearchIndex.relevance_score), desc(SearchIndex.created_at))
            
            # Paginate
            pagination = db_query.paginate(page=page, per_page=per_page, error_out=False)
            
            # Convert to results format
            results = []
            for item in pagination.items:
                result = item.to_dict()
                result['score'] = item.relevance_score
                results.append(result)
            
            return {
                'results': results,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
            
        except Exception as e:
            logger.error(f"Database search error: {str(e)}")
            return {
                'results': [],
                'total': 0,
                'pages': 0,
                'has_next': False,
                'has_prev': False
            }
    
    def _log_search_analytics(self, query: str, result_count: int, 
                            user_id: int = None, ip_address: str = None):
        """Log search analytics"""
        try:
            SearchAnalytics.log_search(
                query=query,
                result_count=result_count,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=None  # Could be added from request
            )
        except Exception as e:
            logger.error(f"Error logging search analytics: {str(e)}")
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on popular queries"""
        try:
            # Get popular queries that start with the query
            from sqlalchemy import func
            
            suggestions = SearchAnalytics.query.filter(
                SearchAnalytics.search_query.like(f'{query}%')
            ).group_by(
                SearchAnalytics.search_query
            ).order_by(
                desc(func.sum(SearchAnalytics.search_count))
            ).limit(limit).all()
            
            return [s.search_query for s in suggestions]
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {str(e)}")
            return []
    
    def get_popular_searches(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular searches"""
        try:
            popular = SearchAnalytics.get_popular_queries(days=days, limit=limit)
            
            return [
                {
                    'query': item.search_query,
                    'count': item.search_count,
                    'avg_results': item.avg_result_position
                }
                for item in popular
            ]
            
        except Exception as e:
            logger.error(f"Error getting popular searches: {str(e)}")
            return []
    
    def reindex_all_content(self):
        """Reindex all content in Elasticsearch"""
        if not self.elasticsearch_client:
            logger.warning("Elasticsearch not available for reindexing")
            return False
        
        try:
            index_name = current_app.config.get('ELASTICSEARCH_INDEX', 'forum_search')
            
            # Delete existing index
            if self.elasticsearch_client.indices.exists(index=index_name):
                self.elasticsearch_client.indices.delete(index=index_name)
            
            # Create new index
            self._create_index()
            
            # Reindex all content
            total_indexed = 0
            
            # Index posts
            posts = Post.query.all()
            for post in posts:
                if SearchIndex.create_from_post(post):
                    self.index_content('post', post.id, force=True)
                    total_indexed += 1
            
            # Index comments
            comments = Comment.query.all()
            for comment in comments:
                if SearchIndex.create_from_comment(comment):
                    self.index_content('comment', comment.id, force=True)
                    total_indexed += 1
            
            # Index users
            users = User.query.all()
            for user in users:
                if SearchIndex.create_from_user(user):
                    self.index_content('user', user.id, force=True)
                    total_indexed += 1
            
            logger.info(f"Reindexed {total_indexed} items in Elasticsearch")
            return True
            
        except Exception as e:
            logger.error(f"Error reindexing content: {str(e)}")
            return False
    
    def update_search_index(self, content_type: str, content_id: int):
        """Update search index for specific content"""
        try:
            # Create/update search index
            if content_type == 'post':
                post = Post.query.get(content_id)
                if post:
                    SearchIndex.create_from_post(post)
                    self.index_content('post', content_id)
            
            elif content_type == 'comment':
                comment = Comment.query.get(content_id)
                if comment:
                    SearchIndex.create_from_comment(comment)
                    self.index_content('comment', content_id)
            
            elif content_type == 'user':
                user = User.query.get(content_id)
                if user:
                    SearchIndex.create_from_user(user)
                    self.index_content('user', content_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating search index: {str(e)}")
            return False
    
    def delete_from_index(self, content_type: str, content_id: int):
        """Delete content from search index"""
        try:
            # Delete from database
            SearchIndex.query.filter_by(
                content_type=content_type,
                content_id=content_id
            ).delete()
            db.session.commit()
            
            # Delete from Elasticsearch
            if self.elasticsearch_client:
                index_name = current_app.config.get('ELASTICSEARCH_INDEX', 'forum_search')
                doc_id = f"{content_type}_{content_id}"
                
                try:
                    self.elasticsearch_client.delete(index=index_name, id=doc_id)
                except:
                    pass  # Document might not exist
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from search index: {str(e)}")
            return False

    def track_search_query(self, query_text, index_name, user_id=None, session_id=None,
                          filters=None, sort_options=None, pagination=None, total_results=0,
                          result_count=0, max_score=0.0, query_time_ms=0.0, total_time_ms=0.0,
                          cache_hit=False, ip_address=None, user_agent=None, referrer=None):
        """Track a search query for analytics"""
        return SearchQuery.track_query(
            query_text=query_text,
            index_name=index_name,
            session_id=session_id,
            user_id=user_id,
            filters=filters,
            sort_options=sort_options,
            pagination=pagination,
            total_results=total_results,
            result_count=result_count,
            max_score=max_score,
            query_time_ms=query_time_ms,
            total_time_ms=total_time_ms,
            cache_hit=cache_hit,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer
        )
    
    def record_search_metric(self, index_name, metric_type, metric_value, metric_unit=None,
                             aggregation_period='hourly', sample_count=1, metadata=None):
        """Record a search analytics metric"""
        return SearchAnalytics.record_metric(
            index_name=index_name,
            metric_type=metric_type,
            metric_value=metric_value,
            metric_unit=metric_unit,
            aggregation_period=aggregation_period,
            sample_count=sample_count,
            metadata=metadata
        )
    
    def get_search_analytics(self, index_name=None, hours=24):
        """Get comprehensive search analytics"""
        return {
            'query_analytics': SearchQuery.get_query_analytics(index_name, hours),
            'popular_queries': SearchQuery.get_popular_queries(index_name, hours, 10),
            'no_result_queries': SearchQuery.get_no_result_queries(index_name, hours, 10),
            'performance_summary': SearchAnalytics.get_performance_summary(index_name, hours)
        }
    
    def manage_search_index(self, index_name, index_type, index_config=None, mapping_config=None, settings_config=None):
        """Create and manage search indices"""
        return SearchIndex.create_index(
            index_name=index_name,
            index_type=index_type,
            index_config=index_config,
            mapping_config=mapping_config,
            settings_config=settings_config
        )
    
    def update_index_stats(self, index_name, document_count=None, index_size_bytes=None,
                          avg_query_time_ms=None, queries_per_hour=None, cache_hit_ratio=None):
        """Update search index statistics"""
        return SearchIndex.update_index_stats(
            index_name=index_name,
            document_count=document_count,
            index_size_bytes=index_size_bytes,
            avg_query_time_ms=avg_query_time_ms,
            queries_per_hour=queries_per_hour,
            cache_hit_ratio=cache_hit_ratio
        )
    
    def create_optimization(self, index_name, optimization_type, optimization_data,
                          reason=None, priority='medium', auto_generated=False):
        """Create a search optimization"""
        return SearchOptimization.create_optimization(
            index_name=index_name,
            optimization_type=optimization_type,
            optimization_data=optimization_data,
            reason=reason,
            priority=priority,
            auto_generated=auto_generated
        )
    
    def get_pending_optimizations(self, index_name=None):
        """Get pending search optimizations"""
        return SearchOptimization.get_pending_optimizations(index_name)
    
    def apply_optimization(self, optimization_id):
        """Apply a search optimization"""
        optimization = SearchOptimization.query.get(optimization_id)
        if optimization:
            optimization.apply_optimization()
            return optimization
        return None
    
    def get_optimization_history(self, index_name=None, optimization_type=None, limit=20):
        """Get optimization history"""
        return SearchOptimization.get_optimization_history(index_name, optimization_type, limit)


# Global search service instance (will be initialized when needed)
search_service = None

def get_search_service():
    """Get search service instance (lazy initialization)"""
    global search_service
    if search_service is None:
        search_service = SearchService()
    return search_service
