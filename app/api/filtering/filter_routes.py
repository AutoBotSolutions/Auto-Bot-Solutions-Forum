"""
Filtering API Routes

Flask routes for filtering, pagination, and search functionality.
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

filtering_bp = Blueprint('filtering', __name__, url_prefix='/api/filter')

@filtering_bp.route('/schema/<resource>', methods=['GET'])
def get_filter_schema(resource: str):
    """Get filter schema for a resource"""
    try:
        from .filter_manager import FilterManager
        
        fm = FilterManager()
        
        # Get resource-specific fields
        if resource == 'posts':
            _register_post_fields(fm)
        elif resource == 'users':
            _register_user_fields(fm)
        elif resource == 'comments':
            _register_comment_fields(fm)
        else:
            return jsonify({
                'success': False,
                'error': 'Resource not found',
                'message': f'No filter schema found for resource: {resource}'
            }), 404
        
        schema = fm.get_filter_schema()
        
        return jsonify({
            'success': True,
            'data': {
                'resource': resource,
                'schema': schema
            }
        })
    except Exception as e:
        logger.error(f"Error getting filter schema: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@filtering_bp.route('/operators', methods=['GET'])
def get_filter_operators():
    """Get available filter operators"""
    try:
        from .filter_manager import FilterOperator
        
        operators = {
            op.value: {
                'name': op.value,
                'description': _get_operator_description(op),
                'types': _get_operator_types(op)
            }
            for op in FilterOperator
        }
        
        return jsonify({
            'success': True,
            'data': {
                'operators': operators,
                'examples': {
                    'equals': {'field': 'title', 'operator': 'eq', 'value': 'Example Title'},
                    'contains': {'field': 'content', 'operator': 'contains', 'value': 'search term'},
                    'between': {'field': 'created_at', 'operator': 'between', 'value': ['2024-01-01', '2024-12-31']},
                    'in': {'field': 'tags', 'operator': 'in', 'value': ['tag1', 'tag2', 'tag3']}
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting filter operators: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@filtering_bp.route('/pagination/types', methods=['GET'])
def get_pagination_types():
    """Get available pagination types"""
    try:
        from .pagination_manager import PaginationType
        
        types = {
            'offset': {
                'name': 'offset',
                'description': 'Traditional offset-based pagination',
                'parameters': ['page', 'per_page', 'offset'],
                'pros': ['Simple to implement', 'Random access'],
                'cons': ['Performance issues with large offsets', 'Inconsistent with real-time data']
            },
            'cursor': {
                'name': 'cursor',
                'description': 'Cursor-based pagination for real-time data',
                'parameters': ['cursor', 'limit'],
                'pros': ['Consistent results', 'Good for real-time data', 'Efficient'],
                'cons': ['No random access', 'More complex']
            },
            'page': {
                'name': 'page',
                'description': 'Page-based pagination',
                'parameters': ['page', 'per_page'],
                'pros': ['User-friendly', 'Easy to understand'],
                'cons': ['Performance issues with large pages']
            },
            'seek': {
                'name': 'seek',
                'description': 'Seek method pagination',
                'parameters': ['seek_value', 'seek_field', 'per_page'],
                'pros': ['Efficient for indexed fields', 'Good for large datasets'],
                'cons': ['Requires indexed seek field', 'Limited to one direction']
            }
        }
        
        return jsonify({
            'success': True,
            'data': {
                'types': types,
                'default': 'offset'
            }
        })
    except Exception as e:
        logger.error(f"Error getting pagination types: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@filtering_bp.route('/validate', methods=['POST'])
def validate_filters():
    """Validate filter parameters"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        resource = data.get('resource')
        filters = data.get('filters', {})
        pagination = data.get('pagination', {})
        
        if not resource:
            return jsonify({
                'success': False,
                'error': 'Resource is required'
            }), 400
        
        # Initialize managers
        from .filter_manager import FilterManager
        from .pagination_manager import PaginationManager
        
        fm = FilterManager()
        pm = PaginationManager()
        
        # Register resource-specific fields
        if resource == 'posts':
            _register_post_fields(fm)
        elif resource == 'users':
            _register_user_fields(fm)
        elif resource == 'comments':
            _register_comment_fields(fm)
        else:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404
        
        # Validate filters
        validation_errors = []
        for field_name, filter_data in filters.items():
            if isinstance(filter_data, dict):
                operator = filter_data.get('operator', 'eq')
                value = filter_data.get('value')
                
                try:
                    from .filter_manager import FilterOperator
                    op = FilterOperator(operator)
                    if not fm.validate_filter(field_name, op, value):
                        validation_errors.append(f"Invalid filter for field {field_name}")
                except ValueError:
                    validation_errors.append(f"Invalid operator {operator} for field {field_name}")
            else:
                if not fm.validate_filter(field_name, FilterOperator.EQUALS, filter_data):
                    validation_errors.append(f"Invalid filter for field {field_name}")
        
        # Validate pagination
        pagination_params = pm.parse_pagination_params(pagination)
        is_valid, pagination_errors = pm.validate_pagination_params(pagination_params, resource)
        
        if not is_valid:
            validation_errors.extend(pagination_errors)
        
        return jsonify({
            'success': len(validation_errors) == 0,
            'data': {
                'valid': len(validation_errors) == 0,
                'errors': validation_errors,
                'parsed_filters': filters,
                'parsed_pagination': pagination_params
            }
        })
    except Exception as e:
        logger.error(f"Error validating filters: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@filtering_bp.route('/examples/<resource>', methods=['GET'])
def get_filter_examples(resource: str):
    """Get filter examples for a resource"""
    try:
        examples = _get_resource_examples(resource)
        
        if not examples:
            return jsonify({
                'success': False,
                'error': 'Resource not found',
                'message': f'No examples found for resource: {resource}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'resource': resource,
                'examples': examples
            }
        })
    except Exception as e:
        logger.error(f"Error getting filter examples: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@filtering_bp.route('/query-builder', methods=['POST'])
def build_query():
    """Build query from filter parameters"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        resource = data.get('resource')
        filters = data.get('filters', {})
        search = data.get('search')
        pagination = data.get('pagination', {})
        sort = data.get('sort')
        
        if not resource:
            return jsonify({
                'success': False,
                'error': 'Resource is required'
            }), 400
        
        # Initialize managers
        from .filter_manager import FilterManager, FilterGroup, FilterCondition, FilterOperator
        from .pagination_manager import PaginationManager
        
        fm = FilterManager()
        pm = PaginationManager()
        
        # Register resource-specific fields
        if resource == 'posts':
            _register_post_fields(fm)
        elif resource == 'users':
            _register_user_fields(fm)
        elif resource == 'comments':
            _register_comment_fields(fm)
        else:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404
        
        # Build filter group
        filter_group = None
        if filters:
            conditions = []
            for field_name, filter_data in filters.items():
                if isinstance(filter_data, dict):
                    operator = filter_data.get('operator', 'eq')
                    value = filter_data.get('value')
                    
                    try:
                        op = FilterOperator(operator)
                        condition = FilterCondition(field_name, op, value)
                        conditions.append(condition)
                    except ValueError:
                        return jsonify({
                            'success': False,
                            'error': f'Invalid operator: {operator}'
                        }), 400
                else:
                    condition = FilterCondition(field_name, FilterOperator.EQUALS, filter_data)
                    conditions.append(condition)
            
            if conditions:
                filter_group = FilterGroup(conditions, 'AND')
        
        # Parse pagination
        pagination_params = pm.parse_pagination_params(pagination)
        
        # Parse sort
        sort_fields = []
        if sort:
            sort_fields = pm._parse_sort_param(sort)
        
        # Generate query plan
        query_plan = {
            'resource': resource,
            'filters': filter_group.to_dict() if filter_group else None,
            'search': search,
            'pagination': pagination_params,
            'sort': [
                {
                    'field': sf.name,
                    'direction': sf.direction.value
                }
                for sf in sort_fields
            ],
            'sql_preview': _generate_sql_preview(resource, filter_group, search, sort_fields),
            'estimated_cost': pm.estimate_query_cost(pagination_params)
        }
        
        return jsonify({
            'success': True,
            'data': query_plan
        })
    except Exception as e:
        logger.error(f"Error building query: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@filtering_bp.route('/stats', methods=['GET'])
def get_filtering_stats():
    """Get filtering system statistics"""
    try:
        # This would typically come from actual usage data
        stats = {
            'total_requests': 10000,
            'filtered_requests': 7500,
            'search_requests': 2500,
            'popular_filters': {
                'title': 3000,
                'created_at': 2500,
                'tags': 2000,
                'author': 1500,
                'status': 1000
            },
            'popular_search_terms': [
                {'term': 'python', 'count': 500},
                {'term': 'javascript', 'count': 450},
                {'term': 'tutorial', 'count': 400},
                {'term': 'help', 'count': 350},
                {'term': 'error', 'count': 300}
            ],
            'pagination_types': {
                'offset': 6000,
                'cursor': 1500,
                'page': 2000,
                'seek': 500
            },
            'average_per_page': 25,
            'average_filter_count': 2.5,
            'cache_hit_rate': 0.75
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting filtering stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

def _register_post_fields(fm):
    """Register post-specific filter fields"""
    from .filter_manager import FilterType, FilterOperator
    
    fm.register_field('title', FilterType.STRING, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
        FilterOperator.STARTS_WITH, FilterOperator.ENDS_WITH,
        FilterOperator.IN, FilterOperator.NOT_IN,
        FilterOperator.REGEX, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Post title")
    
    fm.register_field('content', FilterType.STRING, [
        FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
        FilterOperator.REGEX, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Post content")
    
    fm.register_field('author', FilterType.STRING, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.IN, FilterOperator.NOT_IN,
        FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Post author")
    
    fm.register_field('status', FilterType.STRING, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.IN, FilterOperator.NOT_IN,
        FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Post status", choices=['draft', 'published', 'archived'])
    
    fm.register_field('tags', FilterType.LIST, [
        FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
        FilterOperator.IN, FilterOperator.NOT_IN,
        FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Post tags")
    
    fm.register_field('view_count', FilterType.INTEGER, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUAL,
        FilterOperator.BETWEEN, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "View count")
    
    fm.register_field('like_count', FilterType.INTEGER, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUAL,
        FilterOperator.BETWEEN, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Like count")
    
    fm.register_field('created_at', FilterType.DATETIME, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUAL,
        FilterOperator.BETWEEN, FilterOperator.DATE_GREATER_THAN,
        FilterOperator.DATE_LESS_THAN, FilterOperator.DATE_BETWEEN,
        FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Creation date")
    
    fm.register_field('updated_at', FilterType.DATETIME, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUAL,
        FilterOperator.BETWEEN, FilterOperator.DATE_GREATER_THAN,
        FilterOperator.DATE_LESS_THAN, FilterOperator.DATE_BETWEEN,
        FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Update date")

def _register_user_fields(fm):
    """Register user-specific filter fields"""
    from .filter_manager import FilterType, FilterOperator
    
    fm.register_field('username', FilterType.STRING, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
        FilterOperator.STARTS_WITH, FilterOperator.ENDS_WITH,
        FilterOperator.IN, FilterOperator.NOT_IN,
        FilterOperator.REGEX, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Username")
    
    fm.register_field('email', FilterType.STRING, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
        FilterOperator.IN, FilterOperator.NOT_IN,
        FilterOperator.REGEX, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Email address")
    
    fm.register_field('role', FilterType.STRING, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.IN, FilterOperator.NOT_IN,
        FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "User role", choices=['user', 'admin', 'moderator'])
    
    fm.register_field('is_active', FilterType.BOOLEAN, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Active status")
    
    fm.register_field('created_at', FilterType.DATETIME, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUAL,
        FilterOperator.BETWEEN, FilterOperator.DATE_GREATER_THAN,
        FilterOperator.DATE_LESS_THAN, FilterOperator.DATE_BETWEEN,
        FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Registration date")

def _register_comment_fields(fm):
    """Register comment-specific filter fields"""
    from .filter_manager import FilterType, FilterOperator
    
    fm.register_field('content', FilterType.STRING, [
        FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
        FilterOperator.REGEX, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Comment content")
    
    fm.register_field('author', FilterType.STRING, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.IN, FilterOperator.NOT_IN,
        FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Comment author")
    
    fm.register_field('post_id', FilterType.INTEGER, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.IN, FilterOperator.NOT_IN,
        FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Post ID")
    
    fm.register_field('created_at', FilterType.DATETIME, [
        FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
        FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUAL,
        FilterOperator.BETWEEN, FilterOperator.DATE_GREATER_THAN,
        FilterOperator.DATE_LESS_THAN, FilterOperator.DATE_BETWEEN,
        FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
    ], "Creation date")

def _get_operator_description(operator):
    """Get description for filter operator"""
    descriptions = {
        'eq': 'Equals',
        'ne': 'Not equals',
        'gt': 'Greater than',
        'gte': 'Greater than or equal',
        'lt': 'Less than',
        'lte': 'Less than or equal',
        'in': 'In list',
        'nin': 'Not in list',
        'contains': 'Contains',
        'not_contains': 'Does not contain',
        'starts_with': 'Starts with',
        'ends_with': 'Ends with',
        'regex': 'Regular expression',
        'is_null': 'Is null',
        'is_not_null': 'Is not null',
        'between': 'Between',
        'date_gt': 'Date greater than',
        'date_lt': 'Date less than',
        'date_between': 'Date between'
    }
    return descriptions.get(operator.value, operator.value)

def _get_operator_types(operator):
    """Get compatible types for filter operator"""
    from .filter_manager import FilterType
    
    type_mapping = {
        FilterOperator.EQUALS: [FilterType.STRING, FilterType.INTEGER, FilterType.FLOAT, FilterType.BOOLEAN, FilterType.DATE, FilterType.DATETIME],
        FilterOperator.NOT_EQUALS: [FilterType.STRING, FilterType.INTEGER, FilterType.FLOAT, FilterType.BOOLEAN, FilterType.DATE, FilterType.DATETIME],
        FilterOperator.GREATER_THAN: [FilterType.INTEGER, FilterType.FLOAT, FilterType.DATE, FilterType.DATETIME],
        FilterOperator.GREATER_THAN_OR_EQUAL: [FilterType.INTEGER, FilterType.FLOAT, FilterType.DATE, FilterType.DATETIME],
        FilterOperator.LESS_THAN: [FilterType.INTEGER, FilterType.FLOAT, FilterType.DATE, FilterType.DATETIME],
        FilterOperator.LESS_THAN_OR_EQUAL: [FilterType.INTEGER, FilterType.FLOAT, FilterType.DATE, FilterType.DATETIME],
        FilterOperator.IN: [FilterType.STRING, FilterType.INTEGER, FilterType.FLOAT, FilterType.LIST],
        FilterOperator.NOT_IN: [FilterType.STRING, FilterType.INTEGER, FilterType.FLOAT, FilterType.LIST],
        FilterOperator.CONTAINS: [FilterType.STRING, FilterType.LIST],
        FilterOperator.NOT_CONTAINS: [FilterType.STRING, FilterType.LIST],
        FilterOperator.STARTS_WITH: [FilterType.STRING],
        FilterOperator.ENDS_WITH: [FilterType.STRING],
        FilterOperator.REGEX: [FilterType.STRING],
        FilterOperator.IS_NULL: [FilterType.STRING, FilterType.INTEGER, FilterType.FLOAT, FilterType.BOOLEAN, FilterType.DATE, FilterType.DATETIME],
        FilterOperator.IS_NOT_NULL: [FilterType.STRING, FilterType.INTEGER, FilterType.FLOAT, FilterType.BOOLEAN, FilterType.DATE, FilterType.DATETIME],
        FilterOperator.BETWEEN: [FilterType.INTEGER, FilterType.FLOAT, FilterType.DATE, FilterType.DATETIME],
        FilterOperator.DATE_GREATER_THAN: [FilterType.DATE, FilterType.DATETIME],
        FilterOperator.DATE_LESS_THAN: [FilterType.DATE, FilterType.DATETIME],
        FilterOperator.DATE_BETWEEN: [FilterType.DATE, FilterType.DATETIME]
    }
    
    return [t.value for t in type_mapping.get(operator, [])]

def _get_resource_examples(resource):
    """Get filter examples for a resource"""
    examples = {
        'posts': {
            'simple_filters': {
                'title_equals': {
                    'description': 'Find posts with specific title',
                    'params': {'filter_title': 'Python Tutorial'},
                    'url': '/api/posts?filter_title=Python+Tutorial'
                },
                'status_published': {
                    'description': 'Find published posts',
                    'params': {'filter_status': 'published'},
                    'url': '/api/posts?filter_status=published'
                },
                'recent_posts': {
                    'description': 'Find posts from last 7 days',
                    'params': {'filter_created_at': 'date_gt:2024-05-05'},
                    'url': '/api/posts?filter_created_at=date_gt:2024-05-05'
                }
            },
            'complex_filters': {
                'popular_recent': {
                    'description': 'Find popular posts from last month',
                    'params': {
                        'filters': {
                            'view_count': {'operator': 'gt', 'value': 100},
                            'created_at': {'operator': 'date_gt', 'value': '2024-04-12'}
                        }
                    },
                    'url': '/api/posts?filters={"view_count":{"operator":"gt","value":100},"created_at":{"operator":"date_gt","value":"2024-04-12"}}'
                },
                'tagged_posts': {
                    'description': 'Find posts with specific tags',
                    'params': {
                        'filters': {
                            'tags': {'operator': 'in', 'value': ['python', 'tutorial']},
                            'status': {'operator': 'eq', 'value': 'published'}
                        }
                    },
                    'url': '/api/posts?filters={"tags":{"operator":"in","value":["python","tutorial"]},"status":{"operator":"eq","value":"published"}}'
                }
            },
            'search_examples': {
                'content_search': {
                    'description': 'Search in post content',
                    'params': {'q': 'python programming'},
                    'url': '/api/posts?q=python+programming'
                },
                'title_search': {
                    'description': 'Search in post titles',
                    'params': {'search': 'tutorial', 'search_fields': ['title']},
                    'url': '/api/posts?search=tutorial&search_fields=title'
                }
            }
        },
        'users': {
            'simple_filters': {
                'active_users': {
                    'description': 'Find active users',
                    'params': {'filter_is_active': True},
                    'url': '/api/users?filter_is_active=true'
                },
                'admin_users': {
                    'description': 'Find admin users',
                    'params': {'filter_role': 'admin'},
                    'url': '/api/users?filter_role=admin'
                }
            }
        },
        'comments': {
            'simple_filters': {
                'recent_comments': {
                    'description': 'Find recent comments',
                    'params': {'filter_created_at': 'date_gt:2024-05-05'},
                    'url': '/api/comments?filter_created_at=date_gt:2024-05-05'
                }
            }
        }
    }
    
    return examples.get(resource, {})

def _generate_sql_preview(resource, filter_group, search, sort_fields):
    """Generate SQL preview for query"""
    # This is a simplified SQL preview generation
    # In production, you would use the actual query builder
    
    table_name = resource
    where_clauses = []
    
    if filter_group:
        # Convert filter group to SQL WHERE clause
        for condition in filter_group.conditions:
            field = condition.field
            operator = condition.operator.value
            value = condition.value
            
            if operator == 'eq':
                where_clauses.append(f"{field} = '{value}'")
            elif operator == 'contains':
                where_clauses.append(f"{field} LIKE '%{value}%'")
            elif operator == 'gt':
                where_clauses.append(f"{field} > {value}")
            elif operator == 'in':
                if isinstance(value, list):
                    values = "', '".join(str(v) for v in value)
                    where_clauses.append(f"{field} IN ('{values}')")
    
    if search:
        where_clauses.append(f"(title LIKE '%{search}%' OR content LIKE '%{search}%')")
    
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    order_clauses = []
    for sort_field in sort_fields:
        direction = "ASC" if sort_field.direction.value == "asc" else "DESC"
        order_clauses.append(f"{sort_field.name} {direction}")
    
    order_clause = "ORDER BY " + ", ".join(order_clauses) if order_clauses else ""
    
    sql = f"SELECT * FROM {table_name} {where_clause} {order_clause} LIMIT 20"
    
    return sql.strip()
