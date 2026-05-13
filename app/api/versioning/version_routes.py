"""
API Versioning Routes

Flask routes for API version management and information.
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime, timedelta
import logging

from .version_manager import version_manager, VersionStatus
from .version_middleware import get_current_version, APIVersionMiddleware

logger = logging.getLogger(__name__)

version_bp = Blueprint('version', __name__, url_prefix='/api')

@version_bp.route('/versions', methods=['GET'])
def get_versions():
    """Get information about all API versions"""
    try:
        versions_info = version_manager.get_all_versions_info()
        
        return jsonify({
            'success': True,
            'data': versions_info
        })
    except Exception as e:
        logger.error(f"Error getting versions: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@version_bp.route('/versions/<version>', methods=['GET'])
def get_version_info(version: str):
    """Get information about specific API version"""
    try:
        version_info = version_manager.get_version_info(version)
        
        if not version_info:
            return jsonify({
                'success': False,
                'error': 'VersionNotFound',
                'message': f'API version {version} not found',
                'available_versions': list(version_manager.versions.keys())
            }), 404
        
        return jsonify({
            'success': True,
            'data': version_info
        })
    except Exception as e:
        logger.error(f"Error getting version info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@version_bp.route('/versions/current', methods=['GET'])
def get_current_version_info():
    """Get information about current API version"""
    try:
        current = get_current_version()
        
        if not current:
            return jsonify({
                'success': False,
                'error': 'NoVersion',
                'message': 'No API version detected in request'
            }), 400
        
        version_info = version_manager.get_version_info(current)
        
        # Add request-specific information
        version_info['request_path'] = request.path
        version_info['request_method'] = request.method
        version_info['request_headers'] = dict(request.headers)
        
        return jsonify({
            'success': True,
            'data': version_info
        })
    except Exception as e:
        logger.error(f"Error getting current version info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@version_bp.route('/versions/compatibility', methods=['GET'])
def get_compatibility_matrix():
    """Get version compatibility matrix"""
    try:
        matrix = version_manager.compatibility_matrix
        
        return jsonify({
            'success': True,
            'data': {
                'compatibility_matrix': matrix,
                'summary': {
                    'total_versions': len(version_manager.versions),
                    'compatibility_rules': len(matrix)
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting compatibility matrix: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@version_bp.route('/versions/deprecated', methods=['GET'])
def get_deprecated_versions():
    """Get deprecated API versions"""
    try:
        deprecated = version_manager.get_deprecated_versions()
        
        deprecated_info = []
        for version_obj in deprecated:
            info = version_manager.get_version_info(version_obj.version)
            deprecated_info.append(info)
        
        return jsonify({
            'success': True,
            'data': {
                'deprecated_versions': deprecated_info,
                'count': len(deprecated_info),
                'recommendations': [
                    {
                        'version': version_obj.version,
                        'days_until_sunset': version_obj.days_until_sunset(),
                        'action': 'migrate' if version_obj.days_until_sunset() and version_obj.days_until_sunset() < 90 else 'plan_migration'
                    }
                    for version_obj in deprecated
                ]
            }
        })
    except Exception as e:
        logger.error(f"Error getting deprecated versions: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@version_bp.route('/versions/sunset', methods=['GET'])
def get_sunset_versions():
    """Get sunset API versions"""
    try:
        sunset = version_manager.get_sunset_versions()
        
        sunset_info = []
        for version_obj in sunset:
            info = version_manager.get_version_info(version_obj.version)
            sunset_info.append(info)
        
        return jsonify({
            'success': True,
            'data': {
                'sunset_versions': sunset_info,
                'count': len(sunset_info),
                'urgent_actions': [
                    {
                        'version': version_obj.version,
                        'action': 'immediate_migration_required',
                        'sunset_date': version_obj.sunset_date.isoformat() if version_obj.sunset_date else None
                    }
                    for version_obj in sunset
                ]
            }
        })
    except Exception as e:
        logger.error(f"Error getting sunset versions: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@version_bp.route('/versions/health', methods=['GET'])
def get_versions_health():
    """Get health status of API versions"""
    try:
        active = version_manager.get_active_versions()
        deprecated = version_manager.get_deprecated_versions()
        sunset = version_manager.get_sunset_versions()
        
        health_status = 'healthy'
        issues = []
        warnings = []
        
        # Check for versions nearing sunset
        for version_obj in deprecated:
            days_until = version_obj.days_until_sunset()
            if days_until and days_until < 30:
                warnings.append(f"Version {version_obj.version} will be sunset in {days_until} days")
                if days_until < 7:
                    health_status = 'critical'
                    issues.append(f"Version {version_obj.version} will be sunset in {days_until} days")
        
        # Check for too many active versions
        if len(active) > 3:
            warnings.append(f"High number of active versions: {len(active)}")
        
        return jsonify({
            'success': True,
            'data': {
                'health_status': health_status,
                'active_count': len(active),
                'deprecated_count': len(deprecated),
                'sunset_count': len(sunset),
                'issues': issues,
                'warnings': warnings,
                'recommendations': _get_health_recommendations(active, deprecated, sunset)
            }
        })
    except Exception as e:
        logger.error(f"Error getting versions health: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@version_bp.route('/versions/migration/<from_version>/<to_version>', methods=['GET'])
def get_migration_guide(from_version: str, to_version: str):
    """Get migration guide between versions"""
    try:
        from_version_obj = version_manager.get_version(from_version)
        to_version_obj = version_manager.get_version(to_version)
        
        if not from_version_obj:
            return jsonify({
                'success': False,
                'error': 'VersionNotFound',
                'message': f'Source version {from_version} not found'
            }), 404
        
        if not to_version_obj:
            return jsonify({
                'success': False,
                'error': 'VersionNotFound',
                'message': f'Target version {to_version} not found'
            }), 404
        
        migration_guide = _generate_migration_guide(from_version_obj, to_version_obj)
        
        return jsonify({
            'success': True,
            'data': migration_guide
        })
    except Exception as e:
        logger.error(f"Error generating migration guide: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@version_bp.route('/versions/validate', methods=['POST'])
def validate_version_request():
    """Validate version request"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'InvalidRequest',
                'message': 'Request body is required'
            }), 400
        
        version = data.get('version')
        path = data.get('path', request.path)
        
        if not version:
            return jsonify({
                'success': False,
                'error': 'VersionRequired',
                'message': 'Version is required'
            }), 400
        
        validation = version_manager.validate_version_request(version, path)
        
        return jsonify({
            'success': True,
            'data': validation
        })
    except Exception as e:
        logger.error(f"Error validating version request: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

def _get_health_recommendations(active, deprecated, sunset) -> list:
    """Get health recommendations based on version status"""
    recommendations = []
    
    if len(active) > 3:
        recommendations.append("Consider consolidating active versions to reduce maintenance overhead")
    
    if len(deprecated) > 2:
        recommendations.append("Plan migration for deprecated versions to avoid technical debt")
    
    if len(sunset) > 0:
        recommendations.append("Immediately migrate from sunset versions")
    
    for version_obj in deprecated:
        days_until = version_obj.days_until_sunset()
        if days_until and days_until < 30:
            recommendations.append(f"Urgent: Migrate from {version_obj.version} within {days_until} days")
    
    return recommendations

def _generate_migration_guide(from_version, to_version) -> dict:
    """Generate migration guide between versions"""
    guide = {
        'from_version': from_version.version,
        'to_version': to_version.version,
        'migration_steps': [],
        'breaking_changes': [],
        'new_features': [],
        'deprecated_features': [],
        'compatibility_notes': []
    }
    
    # Add basic migration steps
    guide['migration_steps'] = [
        f"1. Update your API client to use version {to_version.version}",
        f"2. Test your integration with the new version",
        f"3. Update any deprecated endpoint calls",
        f"4. Deploy changes to production",
        f"5. Monitor for any issues"
    ]
    
    # Add breaking changes (would be populated from actual version differences)
    if to_version.version > from_version.version:
        guide['breaking_changes'] = [
            f"Endpoint format changed from /api/{from_version.version}/ to /api/{to_version.version}/",
            "Response format may have slight modifications",
            "Some deprecated parameters have been removed"
        ]
    
    # Add new features
    guide['new_features'] = [
        "Enhanced error handling with more detailed error messages",
        "Improved performance with optimized database queries",
        "New authentication methods available",
        "Enhanced caching mechanisms"
    ]
    
    # Add deprecated features
    guide['deprecated_features'] = [
        "Legacy authentication methods",
        "Old response formats",
        "Deprecated query parameters"
    ]
    
    # Add compatibility notes
    guide['compatibility_notes'] = [
        f"Version {to_version.version} is backward compatible with {from_version.version}",
        "Existing integrations should work with minimal changes",
        "Test thoroughly before production deployment"
    ]
    
    return guide
