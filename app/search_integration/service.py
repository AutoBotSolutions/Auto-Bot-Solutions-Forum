"""
Search Integration Service

Comprehensive search integration service for Elasticsearch integration, search index management,
full-text search capabilities, and search analytics for the Auto Bot Solutions Forum.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from flask import current_app
from sqlalchemy import and_, or_, desc, func
from app import db
from app.search_integration.models import SearchIndex, SearchQuery, SearchAnalytics, SearchOptimization

logger = logging.getLogger(__name__)

class SearchIntegrationService:
    """Comprehensive search integration service for Elasticsearch"""
    
    def __init__(self):
        self.enabled = current_app.config.get('SEARCH_INTEGRATION_ENABLED', True)
        self.elasticsearch_enabled = current_app.config.get('ELASTICSEARCH_ENABLED', True)
        self.analytics_enabled = current_app.config.get('SEARCH_ANALYTICS_ENABLED', True)
        self.optimization_enabled = current_app.config.get('SEARCH_OPTIMIZATION_ENABLED', True)
        self.elasticsearch_client = None
        self._initialize_elasticsearch()
    
    def _initialize_elasticsearch(self):
        """Initialize Elasticsearch client"""
        if not self.elasticsearch_enabled:
            return
        
        try:
            from elasticsearch import Elasticsearch
            
            es_config = current_app.config.get('ELASTICSEARCH_CONFIG', {})
            hosts = es_config.get('hosts', ['localhost:9200'])
            
            self.elasticsearch_client = Elasticsearch(
                hosts=hosts,
                timeout=es_config.get('timeout', 30),
                max_retries=es_config.get('max_retries', 3),
                retry_on_timeout=True
            )
            
            # Test connection
            if self.elasticsearch_client.ping():
                logger.info("Elasticsearch connection established")
            else:
                logger.error("Failed to ping Elasticsearch")
                self.elasticsearch_client = None
                
        except Exception as e:
            logger.error(f"Error initializing Elasticsearch: {str(e)}")
            self.elasticsearch_client = None
    
    def create_search_index(self, index_name, index_type, index_category, elasticsearch_index,
                            index_schema=None, field_mappings=None, index_settings=None,
                            analysis_config=None, refresh_interval='1s', max_result_window=10000,
                            number_of_shards=1, number_of_replicas=1, metadata=None):
        """Create a new search index"""
        if not self.enabled:
            return None
        
        try:
            # Create index record
            search_index = SearchIndex.create_index(
                index_name=index_name,
                index_type=index_type,
                index_category=index_category,
                elasticsearch_index=elasticsearch_index,
                index_schema=index_schema,
                field_mappings=field_mappings,
                index_settings=index_settings,
                analysis_config=analysis_config,
                refresh_interval=refresh_interval,
                max_result_window=max_result_window,
                number_of_shards=number_of_shards,
                number_of_replicas=number_of_replicas,
                metadata=metadata
            )
            
            # Create Elasticsearch index
            if self.elasticsearch_client:
                self._create_elasticsearch_index(search_index)
            
            return search_index
            
        except Exception as e:
            logger.error(f"Error creating search index {index_name}: {str(e)}")
            return None
    
    def _create_elasticsearch_index(self, search_index):
        """Create Elasticsearch index"""
        try:
            # Prepare index settings
            settings = {
                'number_of_shards': search_index.number_of_shards,
                'number_of_replicas': search_index.number_of_replicas,
                'refresh_interval': search_index.refresh_interval,
                'max_result_window': search_index.max_result_window
            }
            
            # Add custom settings
            if search_index.index_settings:
                settings.update(search_index.index_settings)
            
            # Prepare mappings
            mappings = {}
            if search_index.field_mappings:
                mappings = search_index.field_mappings
            
            # Create index
            index_body = {
                'settings': settings,
                'mappings': mappings
            }
            
            # Create the index in Elasticsearch
            if not self.elasticsearch_client.indices.exists(index=search_index.elasticsearch_index):
                response = self.elasticsearch_client.indices.create(
                    index=search_index.elasticsearch_index,
                    body=index_body
                )
                
                if response.get('acknowledged'):
                    search_index.update_status('active', 'green')
                    logger.info(f"Created Elasticsearch index: {search_index.elasticsearch_index}")
                else:
                    search_index.update_status('error', 'red')
                    logger.error(f"Failed to create Elasticsearch index: {search_index.elasticsearch_index}")
            else:
                logger.info(f"Elasticsearch index already exists: {search_index.elasticsearch_index}")
                search_index.update_status('active', 'green')
                
        except Exception as e:
            logger.error(f"Error creating Elasticsearch index: {str(e)}")
            search_index.update_status('error', 'red')
    
    def index_document(self, index_name, document_id, document_body, refresh=False):
        """Index a document in Elasticsearch"""
        if not self.elasticsearch_client:
            return False
        
        try:
            search_index = SearchIndex.get_index_by_name(index_name)
            if not search_index:
                logger.error(f"Search index not found: {index_name}")
                return False
            
            # Index document
            response = self.elasticsearch_client.index(
                index=search_index.elasticsearch_index,
                id=document_id,
                body=document_body,
                refresh=refresh
            )
            
            if response.get('result') in ['created', 'updated']:
                # Update index metrics
                self._update_index_metrics(search_index)
                return True
            else:
                logger.error(f"Failed to index document: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            return False
    
    def search_documents(self, index_name, query_body, size=10, from_=0):
        """Search documents in Elasticsearch"""
        if not self.elasticsearch_client:
            return None
        
        try:
            search_index = SearchIndex.get_index_by_name(index_name)
            if not search_index:
                logger.error(f"Search index not found: {index_name}")
                return None
            
            start_time = time.time()
            
            # Execute search
            response = self.elasticsearch_client.search(
                index=search_index.elasticsearch_index,
                body=query_body,
                size=size,
                from_=from_
            )
            
            search_time_ms = (time.time() - start_time) * 1000
            
            # Log search query
            self._log_search_query(search_index, query_body, response, search_time_ms)
            
            return response
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return None
    
    def _log_search_query(self, search_index, query_body, response, search_time_ms):
        """Log search query for analytics"""
        if not self.analytics_enabled:
            return
        
        try:
            # Extract query information
            query_text = query_body.get('query', {}).get('match', {}).get('title', '') or \
                        query_body.get('query', {}).get('multi_match', {}).get('query', '') or \
                        str(query_body.get('query', {}))
            
            query_type = self._determine_query_type(query_body)
            
            # Log the query
            search_query = SearchQuery.log_query(
                index_id=search_index.id,
                query_text=query_text,
                query_type=query_type,
                query_category=search_index.index_type,
                query_config=query_body,
                total_hits=response.get('hits', {}).get('total', {}).get('value', 0),
                max_score=response.get('hits', {}).get('max_score', 0.0),
                result_count=len(response.get('hits', {}).get('hits', [])),
                search_time_ms=search_time_ms,
                total_time_ms=search_time_ms
            )
            
            return search_query
            
        except Exception as e:
            logger.error(f"Error logging search query: {str(e)}")
            return None
    
    def _determine_query_type(self, query_body):
        """Determine query type from query body"""
        query = query_body.get('query', {})
        
        if 'match' in query:
            return 'full_text'
        elif 'term' in query:
            return 'exact'
        elif 'fuzzy' in query:
            return 'fuzzy'
        elif 'match_phrase' in query:
            return 'phrase'
        elif 'wildcard' in query:
            return 'wildcard'
        elif 'regexp' in query:
            return 'regex'
        elif 'bool' in query:
            # Check nested queries
            bool_query = query['bool']
            if 'must' in bool_query or 'should' in bool_query:
                return 'boolean'
            else:
                return 'full_text'
        else:
            return 'unknown'
    
    def _update_index_metrics(self, search_index):
        """Update index metrics from Elasticsearch"""
        try:
            # Get index stats
            stats = self.elasticsearch_client.indices.stats(index=search_index.elasticsearch_index)
            
            # Extract metrics
            index_stats = stats['indices'].get(search_index.elasticsearch_index, {})
            
            if index_stats:
                total_docs = index_stats.get('total', {}).get('docs', {}).get('count', 0)
                store_size = index_stats.get('total', {}).get('store', {}).get('size_in_bytes', 0)
                
                search_index.update_metrics(
                    document_count=total_docs,
                    index_size_bytes=store_size
                )
                
        except Exception as e:
            logger.error(f"Error updating index metrics: {str(e)}")
    
    def create_analytics_report(self, index_name, analytics_type, analytics_category,
                                period='daily', hours=24):
        """Create analytics report for search index"""
        if not self.analytics_enabled:
            return None
        
        try:
            search_index = SearchIndex.get_index_by_name(index_name)
            if not search_index:
                return None
            
            # Calculate time period
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Get query statistics
            query_stats = SearchQuery.get_query_stats(hours=hours)
            
            # Get index metrics
            index_stats = self._get_elasticsearch_index_stats(search_index)
            
            # Calculate analytics metrics
            analytics = SearchAnalytics.create_analytics(
                index_id=search_index.id,
                analytics_type=analytics_type,
                analytics_category=analytics_category,
                period=period,
                period_start=start_time,
                period_end=end_time,
                total_queries=query_stats.get('total_queries', 0),
                avg_query_time_ms=query_stats.get('avg_query_time_ms', 0.0),
                avg_search_time_ms=query_stats.get('avg_search_time_ms', 0.0),
                cache_hit_rate=query_stats.get('cache_hit_rate', 0.0),
                unique_users=self._get_unique_users(search_index, hours),
                unique_queries=query_stats.get('total_queries', 0),
                zero_results_queries=self._get_zero_results_queries(search_index, hours),
                avg_results_per_query=self._get_avg_results_per_query(search_index, hours),
                index_size_bytes=index_stats.get('size_in_bytes', 0),
                document_count=index_stats.get('doc_count', 0)
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error creating analytics report: {str(e)}")
            return None
    
    def _get_elasticsearch_index_stats(self, search_index):
        """Get Elasticsearch index statistics"""
        try:
            if not self.elasticsearch_client:
                return {}
            
            stats = self.elasticsearch_client.indices.stats(index=search_index.elasticsearch_index)
            index_stats = stats['indices'].get(search_index.elasticsearch_index, {})
            
            return {
                'doc_count': index_stats.get('total', {}).get('docs', {}).get('count', 0),
                'size_in_bytes': index_stats.get('total', {}).get('store', {}).get('size_in_bytes', 0),
                'search_query_total': index_stats.get('total', {}).get('search', {}).get('query_total', 0),
                'search_query_time_in_millis': index_stats.get('total', {}).get('search', {}).get('query_time_in_millis', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting Elasticsearch index stats: {str(e)}")
            return {}
    
    def _get_unique_users(self, search_index, hours):
        """Get unique users for search queries"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            unique_users = db.session.query(
                SearchQuery.user_id
            ).filter(
                SearchQuery.index_id == search_index.id,
                SearchQuery.query_timestamp >= start_time,
                SearchQuery.user_id.isnot(None)
            ).distinct().count()
            
            return unique_users
            
        except Exception as e:
            logger.error(f"Error getting unique users: {str(e)}")
            return 0
    
    def _get_zero_results_queries(self, search_index, hours):
        """Get zero results queries count"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            zero_results = SearchQuery.query.filter(
                SearchQuery.index_id == search_index.id,
                SearchQuery.query_timestamp >= start_time,
                SearchQuery.total_hits == 0
            ).count()
            
            return zero_results
            
        except Exception as e:
            logger.error(f"Error getting zero results queries: {str(e)}")
            return 0
    
    def _get_avg_results_per_query(self, search_index, hours):
        """Get average results per query"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            avg_results = db.session.query(
                func.avg(SearchQuery.result_count)
            ).filter(
                SearchQuery.index_id == search_index.id,
                SearchQuery.query_timestamp >= start_time
            ).scalar() or 0
            
            return float(avg_results)
            
        except Exception as e:
            logger.error(f"Error getting average results per query: {str(e)}")
            return 0.0
    
    def optimize_index(self, index_name, optimization_type, optimization_category,
                      title, description, issue_type, severity='medium', priority=5):
        """Optimize search index"""
        if not self.optimization_enabled:
            return None
        
        try:
            search_index = SearchIndex.get_index_by_name(index_name)
            if not search_index:
                return None
            
            # Create optimization record
            optimization = SearchOptimization.create_optimization(
                index_id=search_index.id,
                optimization_type=optimization_type,
                optimization_category=optimization_category,
                title=title,
                description=description,
                issue_type=issue_type,
                severity=severity,
                priority=priority,
                old_config=self._get_current_index_config(search_index)
            )
            
            # Start optimization
            optimization.start_optimization()
            
            # Apply optimization based on type
            if optimization_type == 'performance':
                success = self._optimize_for_performance(search_index, optimization)
            elif optimization_type == 'quality':
                success = self._optimize_for_quality(search_index, optimization)
            elif optimization_type == 'relevance':
                success = self._optimize_for_relevance(search_index, optimization)
            elif optimization_type == 'indexing':
                success = self._optimize_for_indexing(search_index, optimization)
            else:
                success = False
            
            if success:
                # Complete optimization
                new_config = self._get_current_index_config(search_index)
                performance_after = self._get_performance_metrics(search_index)
                
                optimization.complete_optimization(
                    performance_after=performance_after,
                    new_config=new_config
                )
                
                logger.info(f"Optimization completed for index {index_name}")
            else:
                # Fail optimization
                optimization.fail_optimization("Optimization failed")
                logger.error(f"Optimization failed for index {index_name}")
            
            return optimization
            
        except Exception as e:
            logger.error(f"Error optimizing index {index_name}: {str(e)}")
            return None
    
    def _optimize_for_performance(self, search_index, optimization):
        """Optimize index for performance"""
        try:
            if not self.elasticsearch_client:
                return False
            
            # Force merge index to reduce segments
            self.elasticsearch_client.indices.forcemerge(
                index=search_index.elasticsearch_index,
                max_num_segments=1
            )
            
            # Refresh index
            self.elasticsearch_client.indices.refresh(index=search_index.elasticsearch_index)
            
            # Update index settings for better performance
            settings = {
                'refresh_interval': '30s',  # Reduce refresh frequency
                'number_of_replicas': 1  # Reduce replicas for performance
            }
            
            self.elasticsearch_client.indices.put_settings(
                index=search_index.elasticsearch_index,
                body={'settings': settings}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing for performance: {str(e)}")
            return False
    
    def _optimize_for_quality(self, search_index, optimization):
        """Optimize index for search quality"""
        try:
            if not self.elasticsearch_client:
                return False
            
            # Update mappings for better quality
            # This would involve analyzing search patterns and improving mappings
            # For now, just refresh the index
            self.elasticsearch_client.indices.refresh(index=search_index.elasticsearch_index)
            
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing for quality: {str(e)}")
            return False
    
    def _optimize_for_relevance(self, search_index, optimization):
        """Optimize index for search relevance"""
        try:
            if not self.elasticsearch_client:
                return False
            
            # This would involve analyzing search results and improving relevance scoring
            # For now, just refresh the index
            self.elasticsearch_client.indices.refresh(index=search_index.elasticsearch_index)
            
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing for relevance: {str(e)}")
            return False
    
    def _optimize_for_indexing(self, search_index, optimization):
        """Optimize index for indexing performance"""
        try:
            if not self.elasticsearch_client:
                return False
            
            # Update index settings for better indexing
            settings = {
                'refresh_interval': '5s',  # More frequent refresh for indexing
                'translog_flush_threshold_size': '1gb'  # Optimize translog
            }
            
            self.elasticsearch_client.indices.put_settings(
                index=search_index.elasticsearch_index,
                body={'settings': settings}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing for indexing: {str(e)}")
            return False
    
    def _get_current_index_config(self, search_index):
        """Get current index configuration"""
        try:
            if not self.elasticsearch_client:
                return {}
            
            # Get index settings
            settings = self.elasticsearch_client.indices.get_settings(index=search_index.elasticsearch_index)
            
            # Get index mappings
            mappings = self.elasticsearch_client.indices.get_mapping(index=search_index.elasticsearch_index)
            
            return {
                'settings': settings.get(search_index.elasticsearch_index, {}).get('settings', {}),
                'mappings': mappings.get(search_index.elasticsearch_index, {}).get('mappings', {})
            }
            
        except Exception as e:
            logger.error(f"Error getting current index config: {str(e)}")
            return {}
    
    def _get_performance_metrics(self, search_index):
        """Get current performance metrics"""
        try:
            # Get recent query performance
            recent_queries = SearchQuery.get_queries_by_index(search_index.id, hours=1)
            
            if not recent_queries:
                return {}
            
            avg_query_time = sum(q.total_time_ms for q in recent_queries) / len(recent_queries)
            avg_search_time = sum(q.search_time_ms for q in recent_queries) / len(recent_queries)
            
            return {
                'avg_query_time_ms': avg_query_time,
                'avg_search_time_ms': avg_search_time,
                'total_queries': len(recent_queries)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}
    
    def get_search_health(self, index_name=None):
        """Get search system health"""
        try:
            health_data = {
                'elasticsearch_connected': self.elasticsearch_client is not None,
                'indices': {},
                'overall_status': 'unknown'
            }
            
            if self.elasticsearch_client:
                # Get Elasticsearch cluster health
                cluster_health = self.elasticsearch_client.cluster.health()
                health_data['cluster_health'] = cluster_health['status']
                health_data['overall_status'] = cluster_health['status']
                
                # Get index health
                if index_name:
                    search_index = SearchIndex.get_index_by_name(index_name)
                    if search_index:
                        health_data['indices'][index_name] = {
                            'status': search_index.status,
                            'health_status': search_index.health_status,
                            'document_count': search_index.document_count,
                            'index_size_bytes': search_index.index_size_bytes
                        }
                else:
                    # Get all indices health
                    indices = SearchIndex.get_active_indices()
                    for index in indices:
                        health_data['indices'][index.index_name] = {
                            'status': index.status,
                            'health_status': index.health_status,
                            'document_count': index.document_count,
                            'index_size_bytes': index.index_size_bytes
                        }
            else:
                health_data['overall_status'] = 'error'
                health_data['error'] = 'Elasticsearch not connected'
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error getting search health: {str(e)}")
            return {'error': str(e), 'overall_status': 'error'}
    
    def get_search_dashboard_data(self, hours=24):
        """Get search dashboard data"""
        try:
            # Get index statistics
            index_stats = SearchIndex.get_index_stats()
            
            # Get query statistics
            query_stats = SearchQuery.get_query_stats(hours=hours)
            
            # Get analytics summary
            analytics_summary = SearchAnalytics.get_analytics_summary(hours=hours)
            
            # Get optimization statistics
            optimization_stats = SearchOptimization.get_optimization_stats(hours=hours)
            
            # Get recent queries
            recent_queries = SearchQuery.query.filter(
                SearchQuery.query_timestamp >= datetime.utcnow() - timedelta(hours=hours)
            ).order_by(SearchQuery.query_timestamp.desc()).limit(20).all()
            
            return {
                'index_stats': index_stats,
                'query_stats': query_stats,
                'analytics_summary': analytics_summary,
                'optimization_stats': optimization_stats,
                'recent_queries': [query.to_dict() for query in recent_queries],
                'period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Error getting search dashboard data: {str(e)}")
            return None


# Global search integration service instance
search_integration_service = None

def get_search_integration_service():
    """Get search integration service instance (lazy initialization)"""
    global search_integration_service
    if search_integration_service is None:
        search_integration_service = SearchIntegrationService()
    return search_integration_service
