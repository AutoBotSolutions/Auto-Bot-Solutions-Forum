"""
Filter Decorators

Flask decorators for filtering and pagination endpoints.
"""

from functools import wraps
from flask import request, jsonify, g
from typing import Dict, Any, Optional, List, Callable
import logging

from .filter_manager import FilterManager, FilterGroup, FilterOperator
from .pagination_manager import PaginationManager, PaginationType

logger = logging.getLogger(__name__)

def filterable(filter_manager: FilterManager = None, resource: str = None):
    """Decorator to add filtering capabilities to endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Initialize filter manager if not provided
            fm = filter_manager or FilterManager()
            
            # Parse filter parameters
            filter_params = {}
            
            # Parse simple filters (field=value)
            for key, value in request.args.items():
                if key.startswith('filter_'):
                    field_name = key[7:]  # Remove 'filter_' prefix
                    filter_params[field_name] = value
                elif key == 'q':
                    # Search query
                    filter_params['search'] = value
                elif key == 'search':
                    filter_params['search'] = value
            
            # Parse complex filters (JSON format)
            filter_json = request.args.get('filters')
            if filter_json:
                try:
                    import json
                    complex_filters = json.loads(filter_json)
                    filter_params.update(complex_filters)
                except Exception as e:
                    logger.error(f"Error parsing filter JSON: {e}")
                    return jsonify({
                        'error': 'Invalid filter format',
                        'message': 'filters parameter must be valid JSON'
                    }), 400
            
            # Parse filter query string
            filter_query = request.args.get('filter_query')
            if filter_query:
                try:
                    filter_group = fm.parse_filter_query(filter_query)
                    filter_params['filter_group'] = filter_group
                except Exception as e:
                    logger.error(f"Error parsing filter query: {e}")
                    return jsonify({
                        'error': 'Invalid filter query',
                        'message': 'filter_query parameter is invalid'
                    }), 400
            
            # Validate filters
            validation_errors = []
            for field_name, filter_data in filter_params.items():
                if field_name == 'search' or field_name == 'filter_group':
                    continue
                
                if isinstance(filter_data, dict):
                    operator = filter_data.get('operator', 'eq')
                    value = filter_data.get('value')
                    
                    try:
                        op = FilterOperator(operator)
                        if not fm.validate_filter(field_name, op, value):
                            validation_errors.append(f"Invalid filter for field {field_name}")
                    except ValueError:
                        validation_errors.append(f"Invalid operator {operator} for field {field_name}")
                else:
                    # Simple equality filter
                    if not fm.validate_filter(field_name, FilterOperator.EQUALS, filter_data):
                        validation_errors.append(f"Invalid filter for field {field_name}")
            
            if validation_errors:
                return jsonify({
                    'error': 'Validation error',
                    'message': 'Invalid filters provided',
                    'errors': validation_errors
                }), 400
            
            # Store filter manager and params in context
            g.filter_manager = fm
            g.filter_params = filter_params
            g.resource = resource
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def paginated(pagination_manager: PaginationManager = None, 
             default_type: PaginationType = PaginationType.OFFSET,
             default_per_page: int = 20, max_per_page: int = 100):
    """Decorator to add pagination capabilities to endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Initialize pagination manager if not provided
            pm = pagination_manager or PaginationManager()
            pm.default_per_page = default_per_page
            pm.max_per_page = max_per_page
            
            # Parse pagination parameters
            pagination_params = pm.parse_pagination_params(dict(request.args), default_type)
            
            # Validate pagination parameters
            is_valid, errors = pm.validate_pagination_params(pagination_params, g.get('resource'))
            
            if not is_valid:
                return jsonify({
                    'error': 'Validation error',
                    'message': 'Invalid pagination parameters',
                    'errors': errors
                }), 400
            
            # Store pagination manager and params in context
            g.pagination_manager = pm
            g.pagination_params = pagination_params
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sortable(sortable_fields: List[str] = None):
    """Decorator to add sorting capabilities to endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get sort parameters
            sort_param = request.args.get('sort')
            sort_fields = []
            
            if sort_param:
                pm = g.get('pagination_manager')
                if pm:
                    sort_fields = pm._parse_sort_param(sort_param)
                else:
                    pm = PaginationManager()
                    sort_fields = pm._parse_sort_param(sort_param)
                
                # Validate sortable fields
                if sortable_fields:
                    for sort_field in sort_fields:
                        if sort_field.name not in sortable_fields:
                            return jsonify({
                                'error': 'Validation error',
                                'message': f'Cannot sort by field: {sort_field.name}',
                                'sortable_fields': sortable_fields
                            }), 400
            
            # Store sort fields in context
            g.sort_fields = sort_fields
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def searchable(search_fields: List[str] = None, min_length: int = 2):
    """Decorator to add search capabilities to endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get search parameters
            search_term = request.args.get('q') or request.args.get('search')
            
            if search_term and len(search_term) < min_length:
                return jsonify({
                    'error': 'Validation error',
                    'message': f'Search term must be at least {min_length} characters long'
                }), 400
            
            # Store search parameters in context
            g.search_term = search_term
            g.search_fields = search_fields
            g.min_search_length = min_length
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def filterable_response(include_metadata: bool = True, 
                      include_links: bool = True,
                      include_cost_estimate: bool = False):
    """Decorator to format response with filtering and pagination metadata"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the original function
            result = f(*args, **kwargs)
            
            # Handle different result types
            if isinstance(result, tuple) and len(result) == 2:
                # (results, pagination_result)
                results, pagination_result = result
                return _format_filtered_response(
                    results, pagination_result, include_metadata, include_links, include_cost_estimate
                )
            elif isinstance(result, dict) and 'data' in result:
                # Already formatted response
                return result
            else:
                # Simple result - wrap it
                return _format_filtered_response(
                    result, None, include_metadata, include_links, include_cost_estimate
                )
        return decorated_function
    return decorator

def _format_filtered_response(results: Any, pagination_result = None,
                           include_metadata: bool = True,
                           include_links: bool = True,
                           include_cost_estimate: bool = False) -> Dict[str, Any]:
    """Format filtered response with metadata"""
    response = {
        'data': results
    }
    
    if include_metadata:
        metadata = {}
        
        # Add pagination metadata
        if pagination_result:
            pm = g.get('pagination_manager')
            pp = g.get('pagination_params')
            if pm and pp:
                pagination_metadata = pm.get_pagination_metadata(pagination_result, pp)
                metadata['pagination'] = pagination_metadata
        
        # Add filter metadata
        filter_params = g.get('filter_params', {})
        if filter_params:
            metadata['filters'] = {
                'applied': list(filter_params.keys()),
                'count': len(filter_params)
            }
        
        # Add search metadata
        search_term = g.get('search_term')
        if search_term:
            metadata['search'] = {
                'term': search_term,
                'fields': g.get('search_fields', [])
            }
        
        # Add sort metadata
        sort_fields = g.get('sort_fields', [])
        if sort_fields:
            metadata['sort'] = [
                {
                    'field': sf.name,
                    'direction': sf.direction.value
                }
                for sf in sort_fields
            ]
        
        # Add cost estimate
        if include_cost_estimate:
            pm = g.get('pagination_manager')
            pp = g.get('pagination_params')
            if pm and pp:
                cost_estimate = pm.estimate_query_cost(pp)
                metadata['cost_estimate'] = cost_estimate
        
        response['metadata'] = metadata
    
    if include_links and pagination_result:
        # Add pagination links
        request_url = request.base_url + request.path
        pm = g.get('pagination_manager')
        pp = g.get('pagination_params')
        if pm and pp:
            links = pm.create_pagination_links(request_url, pagination_result, pp)
            response['links'] = links
    
    return response

def cache_filtered_response(cache_timeout: int = 300, vary_by: List[str] = None):
    """Decorator to cache filtered responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key based on filters and pagination
            cache_key_parts = [request.endpoint]
            
            # Add filter params to cache key
            filter_params = g.get('filter_params', {})
            if filter_params:
                import json
                filter_hash = hash(json.dumps(filter_params, sort_keys=True))
                cache_key_parts.append(f"filters_{filter_hash}")
            
            # Add pagination params to cache key
            pagination_params = g.get('pagination_params', {})
            if pagination_params:
                page = pagination_params.get('page', 1)
                per_page = pagination_params.get('per_page', 20)
                cache_key_parts.append(f"page_{page}")
                cache_key_parts.append(f"per_page_{per_page}")
            
            # Add search term to cache key
            search_term = g.get('search_term')
            if search_term:
                cache_key_parts.append(f"search_{hash(search_term)}")
            
            # Add sort fields to cache key
            sort_fields = g.get('sort_fields', [])
            if sort_fields:
                sort_hash = hash(json.dumps([sf.name + sf.direction.value for sf in sort_fields]))
                cache_key_parts.append(f"sort_{sort_hash}")
            
            # Add vary_by parameters
            if vary_by:
                for param in vary_by:
                    value = request.args.get(param)
                    if value:
                        cache_key_parts.append(f"{param}_{value}")
            
            cache_key = ":".join(cache_key_parts)
            
            # Try to get from cache
            from flask import current_app
            cache = current_app.extensions.get('cache')
            if cache:
                cached_response = cache.get(cache_key)
                if cached_response:
                    return cached_response
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache the result
            if cache:
                cache.set(cache_key, result, timeout=cache_timeout)
            
            return result
        return decorated_function
    return decorator

def filter_schema(schema: Dict[str, Any] = None):
    """Decorator to provide filter schema for documentation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Add filter schema to response headers
            fm = g.get('filter_manager')
            if fm:
                filter_schema = fm.get_filter_schema()
                
                # Add to response headers for documentation
                from flask import make_response
                response = make_response(f(*args, **kwargs))
                response.headers['X-Filter-Schema'] = str(filter_schema).replace("'", '"')
                return response
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class FilterMiddleware:
    """Middleware for handling filtering and pagination"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.config.setdefault('FILTER_DEFAULT_PER_PAGE', 20)
        app.config.setdefault('FILTER_MAX_PER_PAGE', 100)
        app.config.setdefault('FILTER_CACHE_TIMEOUT', 300)
        
        # Register error handlers
        @app.errorhandler(400)
        def handle_filter_errors(error):
            """Handle filtering and pagination errors"""
            if hasattr(g, 'filter_errors'):
                return jsonify({
                    'error': 'Filter error',
                    'message': 'Invalid filter parameters',
                    'errors': g.filter_errors
                }), 400
            
            if hasattr(g, 'pagination_errors'):
                return jsonify({
                    'error': 'Pagination error',
                    'message': 'Invalid pagination parameters',
                    'errors': g.pagination_errors
                }), 400
            
            return error
        
        # Add template context processor
        @app.context_processor
        def inject_filter_context():
            """Inject filter context into templates"""
            return {
                'filter_params': g.get('filter_params', {}),
                'pagination_params': g.get('pagination_params', {}),
                'sort_fields': g.get('sort_fields', []),
                'search_term': g.get('search_term')
            }

# Convenience decorators for common use cases
def posts_filterable():
    """Decorator for posts filtering"""
    return filterable(resource='posts')

def users_filterable():
    """Decorator for users filtering"""
    return filterable(resource='users')

def comments_filterable():
    """Decorator for comments filtering"""
    return filterable(resource='comments')

def standard_paginated():
    """Decorator for standard pagination"""
    return paginated(default_per_page=20, max_per_page=100)

def large_paginated():
    """Decorator for large pagination"""
    return paginated(default_per_page=50, max_per_page=500)

def cursor_paginated():
    """Decorator for cursor-based pagination"""
    return paginated(default_type=PaginationType.CURSOR)
