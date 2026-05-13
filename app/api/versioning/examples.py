"""
API Versioning Examples

Examples of how to use the API versioning system with existing endpoints.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta

from .version_manager import version_manager, VersionStatus
from .version_decorators import (
    api_version, deprecated_endpoint, min_version, max_version,
    versioned_response, beta_feature, experimental_feature
)

# Example: Versioned posts endpoints
posts_v1_bp = Blueprint('posts_v1', __name__, url_prefix='/api/v1')
posts_v2_bp = Blueprint('posts_v2', __name__, url_prefix='/api/v2')

@posts_v1_bp.route('/posts', methods=['GET'])
@api_version('v1')
def get_posts_v1():
    """Get posts - v1 API"""
    posts = [
        {
            'id': 1,
            'title': 'First Post',
            'content': 'This is the first post',
            'author': 'john_doe',
            'created_at': '2024-01-01T00:00:00Z'
        }
    ]
    
    return jsonify({
        'posts': posts,
        'version': 'v1',
        'total': len(posts)
    })

@posts_v2_bp.route('/posts', methods=['GET'])
@api_version('v2')
@versioned_response({
    'v2': {
        'metadata': {
            'api_version': 'v2',
            'response_format': 'enhanced',
            'includes_author_details': True
        }
    }
})
def get_posts_v2():
    """Get posts - v2 API with enhanced response"""
    posts = [
        {
            'id': 1,
            'title': 'First Post',
            'content': 'This is the first post',
            'author': {
                'id': 1,
                'username': 'john_doe',
                'email': 'john@example.com',
                'avatar': 'https://example.com/avatar.jpg'
            },
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-02T12:00:00Z',
            'tags': ['announcement', 'welcome'],
            'view_count': 150,
            'like_count': 25
        }
    ]
    
    return jsonify({
        'posts': posts,
        'version': 'v2',
        'total': len(posts),
        'metadata': {
            'api_version': 'v2',
            'response_format': 'enhanced',
            'includes_author_details': True
        }
    })

@posts_v1_bp.route('/posts/<int:post_id>', methods=['GET'])
@api_version('v1')
@deprecated_endpoint(new_endpoint='/api/v2/posts/{post_id}', 
                   removal_date=datetime.utcnow() + timedelta(days=90))
def get_post_v1(post_id: int):
    """Get single post - v1 API (deprecated)"""
    post = {
        'id': post_id,
        'title': f'Post {post_id}',
        'content': f'Content for post {post_id}',
        'author': 'john_doe',
        'created_at': '2024-01-01T00:00:00Z'
    }
    
    return jsonify(post)

@posts_v2_bp.route('/posts/<int:post_id>', methods=['GET'])
@api_version('v2')
def get_post_v2(post_id: int):
    """Get single post - v2 API"""
    post = {
        'id': post_id,
        'title': f'Post {post_id}',
        'content': f'Content for post {post_id}',
        'author': {
            'id': 1,
            'username': 'john_doe',
            'email': 'john@example.com',
            'avatar': 'https://example.com/avatar.jpg'
        },
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-02T12:00:00Z',
        'tags': ['example'],
        'view_count': 150,
        'like_count': 25,
        'comments_count': 10
    }
    
    return jsonify(post)

# Example: Versioned authentication endpoints
auth_v1_bp = Blueprint('auth_v1', __name__, url_prefix='/api/v1')
auth_v2_bp = Blueprint('auth_v2', __name__, url_prefix='/api/v2')

@auth_v1_bp.route('/auth/login', methods=['POST'])
@api_version('v1')
@deprecated_endpoint(new_endpoint='/api/v2/auth/login')
def login_v1():
    """Login - v1 API (deprecated)"""
    data = request.get_json()
    
    # Simple v1 login
    return jsonify({
        'token': 'simple_token_123',
        'user_id': 1,
        'username': data.get('username'),
        'expires_in': 3600
    })

@auth_v2_bp.route('/auth/login', methods=['POST'])
@api_version('v2')
def login_v2():
    """Login - v2 API with enhanced security"""
    data = request.get_json()
    
    # Enhanced v2 login
    return jsonify({
        'access_token': 'enhanced_jwt_token_456',
        'refresh_token': 'refresh_token_789',
        'token_type': 'Bearer',
        'expires_in': 3600,
        'user': {
            'id': 1,
            'username': data.get('username'),
            'email': 'user@example.com',
            'roles': ['user'],
            'permissions': ['read', 'write']
        }
    })

# Example: Beta and experimental features
@posts_v2_bp.route('/posts/ai-summary', methods=['GET'])
@api_version('v2')
@beta_feature('ai_summary', available_from='v2')
def get_ai_summary():
    """Get AI-generated post summary - beta feature"""
    return jsonify({
        'summary': 'This is an AI-generated summary of the posts',
        'confidence': 0.85,
        'model': 'gpt-4',
        'version': 'beta'
    })

@posts_v2_bp.route('/posts/realtime', methods=['GET'])
@api_version('v2')
@experimental_feature('realtime_updates')
def get_realtime_posts():
    """Get real-time post updates - experimental feature"""
    return jsonify({
        'real_time_updates': True,
        'websocket_url': 'ws://localhost:5000/ws/posts',
        'updates': [],
        'version': 'experimental'
    })

# Example: Version-specific features
@posts_v2_bp.route('/posts/search', methods=['GET'])
@api_version('v2')
@min_version('v2')
def search_posts_v2():
    """Search posts - v2 only feature"""
    query = request.args.get('q', '')
    
    return jsonify({
        'query': query,
        'results': [
            {
                'id': 1,
                'title': f'Result for: {query}',
                'relevance_score': 0.95
            }
        ],
        'total': 1,
        'search_version': 'v2'
    })

# Example: Multiple version support
@posts_v1_bp.route('/posts/popular', methods=['GET'])
@api_version('v1', 'v2')
@versioned_response({
    'v1': {
        'format': 'simple',
        'includes_scores': False
    },
    'v2': {
        'format': 'enhanced',
        'includes_scores': True,
        'includes_trending': True
    }
})
def get_popular_posts():
    """Get popular posts - supported in both v1 and v2"""
    posts = [
        {
            'id': 1,
            'title': 'Popular Post 1',
            'view_count': 1000
        },
        {
            'id': 2,
            'title': 'Popular Post 2',
            'view_count': 800
        }
    ]
    
    current_version = request.headers.get('API-Version', 'v1')
    
    response = {
        'posts': posts,
        'total': len(posts)
    }
    
    if current_version == 'v2':
        # Enhanced v2 response
        for post in posts:
            post['popularity_score'] = post['view_count'] / 1000
            post['trending'] = post['view_count'] > 900
        
        response['metadata'] = {
            'format': 'enhanced',
            'includes_scores': True,
            'includes_trending': True
        }
    else:
        # Simple v1 response
        response['metadata'] = {
            'format': 'simple',
            'includes_scores': False
        }
    
    return jsonify(response)

# Example: Register endpoints with version manager
def register_versioned_endpoints():
    """Register endpoints with version manager"""
    
    # Register v1 posts endpoints
    version_manager.register_endpoint('v1', '/posts', get_posts_v1, ['GET'])
    version_manager.register_endpoint('v1', '/posts/<int:post_id>', get_post_v1, ['GET'])
    version_manager.register_endpoint('v1', '/posts/popular', get_popular_posts, ['GET'])
    
    # Register v2 posts endpoints
    version_manager.register_endpoint('v2', '/posts', get_posts_v2, ['GET'])
    version_manager.register_endpoint('v2', '/posts/<int:post_id>', get_post_v2, ['GET'])
    version_manager.register_endpoint('v2', '/posts/search', search_posts_v2, ['GET'])
    version_manager.register_endpoint('v2', '/posts/popular', get_popular_posts, ['GET'])
    version_manager.register_endpoint('v2', '/posts/ai-summary', get_ai_summary, ['GET'])
    version_manager.register_endpoint('v2', '/posts/realtime', get_realtime_posts, ['GET'])
    
    # Register v1 auth endpoints
    version_manager.register_endpoint('v1', '/auth/login', login_v1, ['POST'])
    
    # Register v2 auth endpoints
    version_manager.register_endpoint('v2', '/auth/login', login_v2, ['POST'])

# Example: Version deprecation setup
def setup_version_deprecation():
    """Set up version deprecation"""
    
    # Deprecate v1 in 30 days, sunset in 90 days
    deprecation_date = datetime.utcnow() + timedelta(days=30)
    sunset_date = datetime.utcnow() + timedelta(days=90)
    
    version_manager.deprecate_version('v1', deprecation_date, sunset_date)

# Example: Usage in Flask app
def create_versioned_app(app):
    """Create Flask app with versioning"""
    
    # Initialize versioning middleware
    from .version_middleware import APIVersionMiddleware
    versioning_middleware = APIVersionMiddleware(app)
    
    # Register blueprints
    app.register_blueprint(posts_v1_bp)
    app.register_blueprint(posts_v2_bp)
    app.register_blueprint(auth_v1_bp)
    app.register_blueprint(auth_v2_bp)
    app.register_blueprint(version_bp)  # Version management endpoints
    
    # Register endpoints
    register_versioned_endpoints()
    
    # Setup deprecation
    setup_version_deprecation()
    
    return app
