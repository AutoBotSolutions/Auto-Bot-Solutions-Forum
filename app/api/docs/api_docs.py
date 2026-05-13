"""
API Documentation Blueprint
Provides routes for API documentation and Swagger UI
"""

from flask import Blueprint, render_template, jsonify, request
from flask import current_app, g
from typing import Dict, Any, Optional

from .openapi import OpenAPIService
from .swagger_ui import SwaggerUIService

# Create blueprint
api_docs_bp = Blueprint('api_docs', __name__, 
                        url_prefix='/api/docs',
                        template_folder='templates')

@api_docs_bp.route('/')
def docs_index():
    """API documentation index page"""
    return render_template('docs_index.html')

@api_docs_bp.route('/swagger')
def swagger_ui():
    """Swagger UI interactive documentation"""
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    return swagger_service.get_swagger_html()

@api_docs_bp.route('/openapi.json')
def openapi_spec():
    """OpenAPI specification as JSON"""
    openapi_service = current_app.extensions.get('openapi_service')
    if not openapi_service:
        return jsonify({'error': 'OpenAPI service not available'}), 503
    
    return jsonify(openapi_service.get_spec())

@api_docs_bp.route('/openapi.yaml')
def openapi_yaml():
    """OpenAPI specification as YAML"""
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    try:
        return swagger_service.get_openapi_yaml(), 200, {
            'Content-Type': 'text/x-yaml'
        }
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_docs_bp.route('/config')
def swagger_config():
    """Swagger UI configuration"""
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    return swagger_service.get_config_json(), 200, {
        'Content-Type': 'application/json'
    }

@api_docs_bp.route('/info')
def api_info():
    """API information summary"""
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    return jsonify(swagger_service.get_api_info())

@api_docs_bp.route('/validate')
def validate_spec():
    """Validate OpenAPI specification"""
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    return jsonify(swagger_service.validate_openapi_spec())

@api_docs_bp.route('/search')
def search_endpoints():
    """Search API endpoints"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    results = swagger_service.search_endpoints(query)
    return jsonify({
        'query': query,
        'results': results,
        'count': len(results)
    })

@api_docs_bp.route('/endpoint/<path:path>')
def endpoint_details(path):
    """Get detailed information about a specific endpoint"""
    method = request.args.get('method', '').upper()
    if not method:
        return jsonify({'error': 'Method parameter is required'}), 400
    
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    details = swagger_service.get_endpoint_details(path, method)
    if not details:
        return jsonify({'error': 'Endpoint not found'}), 404
    
    return jsonify(details)

@api_docs_bp.route('/schema/<schema_name>')
def schema_details(schema_name):
    """Get detailed information about a specific schema"""
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    details = swagger_service.get_schema_details(schema_name)
    if not details:
        return jsonify({'error': 'Schema not found'}), 404
    
    return jsonify(details)

@api_docs_bp.route('/export')
def export_specification():
    """Export OpenAPI specification"""
    format_type = request.args.get('format', 'json').lower()
    if format_type not in ['json', 'yaml']:
        return jsonify({'error': 'Invalid format. Supported formats: json, yaml'}), 400
    
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    try:
        content = swagger_service.export_specification(format_type)
        
        if format_type == 'json':
            return content, 200, {
                'Content-Type': 'application/json',
                'Content-Disposition': 'attachment; filename=openapi.json'
            }
        else:
            return content, 200, {
                'Content-Type': 'text/x-yaml',
                'Content-Disposition': 'attachment; filename=openapi.yaml'
            }
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_docs_bp.route('/client-code')
def generate_client_code():
    """Generate client code for API endpoint"""
    endpoint_path = request.args.get('path', '')
    method = request.args.get('method', '').upper()
    language = request.args.get('language', 'javascript').lower()
    
    if not endpoint_path or not method:
        return jsonify({'error': 'path and method parameters are required'}), 400
    
    if language not in ['javascript', 'python', 'curl']:
        return jsonify({'error': 'Invalid language. Supported languages: javascript, python, curl'}), 400
    
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    try:
        code = swagger_service.generate_client_code(language, endpoint_path, method)
        if not code:
            return jsonify({'error': 'Endpoint not found'}), 404
        
        return jsonify({
            'language': language,
            'endpoint': endpoint_path,
            'method': method,
            'code': code
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_docs_bp.route('/theme', methods=['POST'])
def update_theme():
    """Update Swagger UI theme"""
    theme = request.json.get('theme', 'light')
    if theme not in ['light', 'dark', 'material']:
        return jsonify({'error': 'Invalid theme. Supported themes: light, dark, material'}), 400
    
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    swagger_service.set_theme(theme)
    return jsonify({'message': f'Theme updated to {theme}'})

@api_docs_bp.route('/config', methods=['POST'])
def update_config():
    """Update Swagger UI configuration"""
    config_updates = request.json
    if not config_updates:
        return jsonify({'error': 'No configuration updates provided'}), 400
    
    swagger_service = current_app.extensions.get('swagger_service')
    if not swagger_service:
        return jsonify({'error': 'Swagger UI service not available'}), 503
    
    swagger_service.update_config(**config_updates)
    return jsonify({'message': 'Configuration updated successfully'})

@api_docs_bp.route('/health')
def health_check():
    """Health check for API documentation service"""
    openapi_service = current_app.extensions.get('openapi_service')
    swagger_service = current_app.extensions.get('swagger_service')
    
    status = {
        'status': 'healthy',
        'services': {
            'openapi': openapi_service is not None,
            'swagger_ui': swagger_service is not None
        },
        'timestamp': current_app.config.get('CURRENT_TIME', 'unknown')
    }
    
    if not (openapi_service and swagger_service):
        status['status'] = 'degraded'
    
    return jsonify(status)

# Error handlers
@api_docs_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found',
        'path': request.path
    }), 404

@api_docs_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred',
        'path': request.path
    }), 500

def init_api_docs(app):
    """Initialize API documentation services"""
    # Create OpenAPI service
    openapi_service = OpenAPIService(
        title=app.config.get('API_TITLE', 'Auto Bot Solutions Forum API'),
        version=app.config.get('API_VERSION', '1.0.0'),
        description=app.config.get('API_DESCRIPTION', 'RESTful API for Auto Bot Solutions Forum')
    )
    
    # Initialize default components
    openapi_service.initialize_default_components()
    
    # Generate OpenAPI spec from Flask routes
    if app.config.get('AUTO_GENERATE_DOCS', True):
        openapi_service.generate_from_flask_routes(app)
    
    # Create Swagger UI service
    swagger_service = SwaggerUIService(openapi_service)
    
    # Configure Swagger UI
    swagger_config = app.config.get('SWAGGER_CONFIG', {})
    if swagger_config:
        swagger_service.update_config(**swagger_config)
    
    # Set theme
    theme = app.config.get('SWAGGER_THEME', 'light')
    swagger_service.set_theme(theme)
    
    # Store services in app context
    app.extensions['openapi_service'] = openapi_service
    app.extensions['swagger_service'] = swagger_service
    
    # Register blueprint
    app.register_blueprint(api_docs_bp)
    
    # Add custom CSS/JS if configured
    custom_css = app.config.get('SWAGGER_CUSTOM_CSS', [])
    for css in custom_css:
        swagger_service.add_custom_css(css)
    
    custom_js = app.config.get('SWAGGER_CUSTOM_JS', [])
    for js in custom_js:
        swagger_service.add_custom_js(js)
    
    app.logger.info('API documentation services initialized')
    
    return openapi_service, swagger_service
