"""
Enhanced Search Service

Advanced search functionality with Elasticsearch integration for the Auto Bot Solutions Forum.
This service provides comprehensive search analytics, optimization, and management capabilities.
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

class EnhancedSearchService:
    """Enhanced search service with comprehensive analytics and optimization"""
    
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
        
        # Define mapping
        mapping = {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "standard"},
                    "content": {"type": "text", "analyzer": "standard"},
                    "author": {"type": "text", "analyzer": "standard"},
                    "category": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "content_type": {"type": "keyword"},
                    "content_id": {"type": "integer"}
                }
            }
        }
        
        try:
            if not self.elasticsearch_client.indices.exists(index=index_name):
                self.elasticsearch_client.indices.create(index=index_name, body=mapping)
                logger.info(f"Created Elasticsearch index: {index_name}")
        except Exception as e:
            logger.error(f"Error creating Elasticsearch index: {str(e)}")
    
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
    
    def search(self, query_text, index_name=None, filters=None, sort_options=None, 
               pagination=None, user_id=None, session_id=None):
        """Perform search with analytics tracking"""
        start_time = datetime.utcnow()
        
        # Default index name
        if not index_name:
            index_name = current_app.config.get('ELASTICSEARCH_INDEX', 'forum_search')
        
        # Default pagination
        if not pagination:
            pagination = {'page': 1, 'per_page': 10}
        
        # Default sort
        if not sort_options:
            sort_options = [{'created_at': {'order': 'desc'}}]
        
        # Perform search
        results = []
        total_results = 0
        max_score = 0.0
        query_time_ms = 0.0
        cache_hit = False
        
        if self.elasticsearch_client:
            try:
                search_body = {
                    'query': {
                        'multi_match': {
                            'query': query_text,
                            'fields': ['title^2', 'content', 'author'],
                            'type': 'best_fields'
                        }
                    },
                    'sort': sort_options,
                    'from': (pagination['page'] - 1) * pagination['per_page'],
                    'size': pagination['per_page']
                }
                
                # Add filters if provided
                if filters:
                    search_body['filter'] = filters
                
                response = self.elasticsearch_client.search(index=index_name, body=search_body)
                
                results = response['hits']['hits']
                total_results = response['hits']['total']['value']
                max_score = response['hits']['max_score']
                query_time_ms = response['took']
                
            except Exception as e:
                logger.error(f"Search error: {str(e)}")
        else:
            # Fallback to database search
            results = self._database_search(query_text, filters, sort_options, pagination)
            total_results = len(results)
        
        # Track analytics
        end_time = datetime.utcnow()
        total_time_ms = (end_time - start_time).total_seconds() * 1000
        
        self.track_search_query(
            query_text=query_text,
            index_name=index_name,
            user_id=user_id,
            session_id=session_id,
            filters=filters,
            sort_options=sort_options,
            pagination=pagination,
            total_results=total_results,
            result_count=len(results),
            max_score=max_score,
            query_time_ms=query_time_ms,
            total_time_ms=total_time_ms,
            cache_hit=cache_hit
        )
        
        return {
            'results': results,
            'total_results': total_results,
            'page': pagination['page'],
            'per_page': pagination['per_page'],
            'max_score': max_score,
            'query_time_ms': query_time_ms,
            'total_time_ms': total_time_ms
        }
    
    def _database_search(self, query_text, filters=None, sort_options=None, pagination=None):
        """Fallback database search"""
        # Simple database search implementation
        query = Post.query.filter(
            or_(
                Post.title.contains(query_text),
                Post.content.contains(query_text)
            )
        )
        
        # Apply filters
        if filters:
            if 'category' in filters:
                query = query.join(Category).filter(Category.name == filters['category'])
            if 'author' in filters:
                query = query.join(User).filter(User.username.contains(filters['author']))
        
        # Apply sort
        if sort_options:
            for sort_field, sort_config in sort_options.items():
                if sort_field == 'created_at':
                    if sort_config.get('order') == 'desc':
                        query = query.order_by(Post.created_at.desc())
                    else:
                        query = query.order_by(Post.created_at.asc())
        
        # Apply pagination
        if pagination:
            offset = (pagination['page'] - 1) * pagination['per_page']
            query = query.offset(offset).limit(pagination['per_page'])
        
        results = query.all()
        
        return [
            {
                'id': post.id,
                'title': post.title,
                'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                'author': post.author.username if post.author else 'Anonymous',
                'created_at': post.created_at.isoformat(),
                'content_type': 'post',
                'content_id': post.id
            }
            for post in results
        ]
    
    def index_content(self, content_type, content_id, title, content, author=None, 
                     category=None, tags=None, created_at=None, updated_at=None):
        """Index content in Elasticsearch"""
        if not self.elasticsearch_client:
            return False
        
        index_name = current_app.config.get('ELASTICSEARCH_INDEX', 'forum_search')
        doc_id = f"{content_type}_{content_id}"
        
        doc = {
            'title': title,
            'content': content,
            'content_type': content_type,
            'content_id': content_id,
            'created_at': created_at or datetime.utcnow(),
            'updated_at': updated_at or datetime.utcnow()
        }
        
        if author:
            doc['author'] = author
        if category:
            doc['category'] = category
        if tags:
            doc['tags'] = tags
        
        try:
            self.elasticsearch_client.index(index=index_name, id=doc_id, body=doc)
            return True
        except Exception as e:
            logger.error(f"Error indexing content: {str(e)}")
            return False
    
    def remove_content(self, content_type, content_id):
        """Remove content from search index"""
        if not self.elasticsearch_client:
            return False
        
        index_name = current_app.config.get('ELASTICSEARCH_INDEX', 'forum_search')
        doc_id = f"{content_type}_{content_id}"
        
        try:
            self.elasticsearch_client.delete(index=index_name, id=doc_id)
            return True
        except Exception as e:
            logger.error(f"Error removing from search index: {str(e)}")
            return False


# Global enhanced search service instance
enhanced_search_service = None

def get_enhanced_search_service():
    """Get enhanced search service instance (lazy initialization)"""
    global enhanced_search_service
    if enhanced_search_service is None:
        enhanced_search_service = EnhancedSearchService()
    return enhanced_search_service
