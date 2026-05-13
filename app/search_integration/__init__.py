"""
Search Integration Module

Search integration system for the Auto Bot Solutions Forum with Elasticsearch integration,
search index management, full-text search capabilities, and search analytics.
"""

from .models import SearchIndex, SearchQuery, SearchAnalytics, SearchOptimization
from .service import SearchIntegrationService, get_search_integration_service
from .utils import (
    QueryType, SearchFieldType, SearchQuery, IndexMapping, QueryBuilder, IndexManager,
    SearchAnalyzer, PerformanceOptimizer, SearchUtils, query_builder, index_manager,
    search_analyzer, performance_optimizer, search_utils
)
from .config import (
    SEARCH_INTEGRATION_ENABLED, ELASTICSEARCH_ENABLED, SEARCH_ANALYTICS_ENABLED,
    SEARCH_OPTIMIZATION_ENABLED, FULL_TEXT_SEARCH_ENABLED, ELASTICSEARCH_CONFIG,
    INDEX_CONFIG, SEARCH_CONFIG, ANALYTICS_CONFIG, OPTIMIZATION_CONFIG,
    FULL_TEXT_CONFIG, INDEX_TEMPLATES, QUERY_CONFIG, PERFORMANCE_CONFIG,
    SECURITY_CONFIG, SEARCH_FIELD_TYPES, SEARCH_QUERY_TYPES, SEARCH_FILTERS,
    get_search_integration_config, validate_search_integration_config
)

__all__ = [
    # Models
    'SearchIndex',
    'SearchQuery',
    'SearchAnalytics',
    'SearchOptimization',
    
    # Services
    'SearchIntegrationService',
    'get_search_integration_service',
    
    # Utilities
    'QueryType',
    'SearchFieldType',
    'SearchQuery',
    'IndexMapping',
    'QueryBuilder',
    'IndexManager',
    'SearchAnalyzer',
    'PerformanceOptimizer',
    'SearchUtils',
    'query_builder',
    'index_manager',
    'search_analyzer',
    'performance_optimizer',
    'search_utils',
    
    # Configuration
    'SEARCH_INTEGRATION_ENABLED',
    'ELASTICSEARCH_ENABLED',
    'SEARCH_ANALYTICS_ENABLED',
    'SEARCH_OPTIMIZATION_ENABLED',
    'FULL_TEXT_SEARCH_ENABLED',
    'ELASTICSEARCH_CONFIG',
    'INDEX_CONFIG',
    'SEARCH_CONFIG',
    'ANALYTICS_CONFIG',
    'OPTIMIZATION_CONFIG',
    'FULL_TEXT_CONFIG',
    'INDEX_TEMPLATES',
    'QUERY_CONFIG',
    'PERFORMANCE_CONFIG',
    'SECURITY_CONFIG',
    'SEARCH_FIELD_TYPES',
    'SEARCH_QUERY_TYPES',
    'SEARCH_FILTERS',
    'get_search_integration_config',
    'validate_search_integration_config'
]
