"""
Search Module

Advanced search functionality with Elasticsearch integration for the Auto Bot Solutions Forum.
Provides comprehensive search analytics, optimization, and management capabilities.
"""

from .models import SearchIndex, SearchQuery, SearchAnalytics, SearchOptimization
from .enhanced_service import EnhancedSearchService, get_enhanced_search_service, enhanced_search_service

__all__ = [
    # Models
    'SearchIndex',
    'SearchQuery',
    'SearchAnalytics', 
    'SearchOptimization',
    
    # Services
    'EnhancedSearchService',
    'enhanced_search_service',
    'get_enhanced_search_service'
]
