"""
Gateway Routing

Handles API versioning routing and request routing logic for the API gateway.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from flask import request, g
from urllib.parse import urlparse
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class GatewayRouter:
    """Gateway routing handler for API versioning and request routing"""
    
    def __init__(self, gateway_manager):
        self.gateway_manager = gateway_manager
        self.version_patterns = {}
        self.route_cache = {}
        self._register_default_patterns()
    
    def _register_default_patterns(self):
        """Register default versioning patterns"""
        # Path-based versioning: /api/v1/users
        self.version_patterns['path'] = re.compile(r'^/api/v(\d+(?:\.\d+)*)/')
        
        # Header-based versioning: API-Version: v1.0
        self.version_patterns['header'] = 'API-Version'
        
        # Query parameter versioning: ?version=v1.0
        self.version_patterns['query'] = 'version'
        
        # Subdomain versioning: v1.api.example.com
        self.version_patterns['subdomain'] = re.compile(r'^v(\d+(?:\.\d+)*)\.')
    
    def detect_version(self, request_path: str, headers: Dict[str, str] = None, 
                     query_params: Dict[str, str] = None) -> Optional[str]:
        """Detect API version from request"""
        headers = headers or {}
        query_params = query_params or {}
        
        # 1. Path-based versioning
        path_match = self.version_patterns['path'].match(request_path)
        if path_match:
            version = "v" + path_match.group(1)
            logger.debug(f"Detected version from path: {version}")
            return version
        
        # 2. Header-based versioning
        header_version = headers.get(self.version_patterns['header'])
        if header_version:
            logger.debug(f"Detected version from header: {header_version}")
            return header_version
        
        # 3. Query parameter versioning
        query_version = query_params.get(self.version_patterns['query'])
        if query_version:
            logger.debug(f"Detected version from query: {query_version}")
            return query_version
        
        # 4. Subdomain versioning
        host = headers.get('Host', '')
        subdomain_match = self.version_patterns['subdomain'].match(host)
        if subdomain_match:
            version = "v" + subdomain_match.group(1)
            logger.debug(f"Detected version from subdomain: {version}")
            return version
        
        # 5. Default version
        default_version = self.gateway_manager.config.default_version
        logger.debug(f"Using default version: {default_version}")
        return default_version
    
    def rewrite_path_for_version(self, original_path: str, version: str) -> str:
        """Rewrite path to include version if needed"""
        # If path already has version, don't modify
        if self.version_patterns['path'].match(original_path):
            return original_path
        
        # Add version to path
        if original_path.startswith('/api/'):
            return f"/api/v{version}{original_path[4:]}"
        else:
            return f"/api/v{version}{original_path}"
    
    def _path_matches(self, request_path: str, route_path: str) -> bool:
        """Check if request path matches route path"""
        # Simple exact match for now
        # In production, this would support regex patterns
        return request_path == route_path
    
    def route_request(self, request_path: str, method: str, 
                      headers: Dict[str, str] = None, 
                      query_params: Dict[str, str] = None) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Route request to appropriate service"""
        headers = headers or {}
        query_params = query_params or {}
        
        # Detect version
        version = self.detect_version(request_path, headers, query_params)
        
        # Get route configuration
        route_config = self.gateway_manager.get_route_for_request(request_path, version, method)
        if not route_config:
            return None, None
        
        # Rewrite path if needed
        target_path = request_path
        if self.gateway_manager.config.enable_versioning:
            target_path = self.rewrite_path_for_version(request_path, version)
        
        # Build routing context
        routing_context = {
            'original_path': request_path,
            'target_path': target_path,
            'detected_version': version,
            'method': method,
            'service_name': route_config.service_name,
            'service_url': route_config.service_url,
            'timeout': route_config.timeout,
            'retries': route_config.retries,
            'headers': headers,
            'query_params': query_params
        }
        
        return target_path, routing_context
    
    def get_route_cache_key(self, request_path: str, method: str, 
                           version: str = None) -> str:
        """Generate cache key for route lookup"""
        version = version or self.gateway_manager.config.default_version
        return f"{method}:{request_path}:{version}"
    
    def cache_route(self, request_path: str, method: str, version: str, 
                   route_config: Dict[str, Any]):
        """Cache route configuration"""
        cache_key = self.get_route_cache_key(request_path, method, version)
        self.route_cache[cache_key] = route_config
    
    def get_cached_route(self, request_path: str, method: str, 
                          version: str = None) -> Optional[Dict[str, Any]]:
        """Get cached route configuration"""
        cache_key = self.get_route_cache_key(request_path, method, version)
        return self.route_cache.get(cache_key)
    
    def clear_route_cache(self):
        """Clear route cache"""
        self.route_cache.clear()
        logger.info("Route cache cleared")
    
    def validate_version(self, version: str) -> bool:
        """Validate version format"""
        try:
            # Check if version matches semantic versioning pattern
            version_pattern = re.compile(r'^\d+(?:\.\d+)*(?:\.\d+)?$')
            return bool(version_pattern.match(version))
        except Exception:
            return False
    
    def get_version_info(self, version: str) -> Dict[str, Any]:
        """Get information about a version"""
        # Get all routes for this version
        version_routes = []
        for route_key, route_config in self.gateway_manager.routes.items():
            route_path, route_version = route_key.split(":", 1)
            if route_version == version:
                version_routes.append({
                    'path': route_path,
                    'service_name': route_config.service_name,
                    'methods': route_config.methods
                })
        
        return {
            'version': version,
            'valid': self.validate_version(version),
            'routes': version_routes,
            'is_default': version == self.gateway_manager.config.default_version,
            'supported_methods': list(set(
                method for route in version_routes 
                for method in route['methods']
            ))
        }
    
    def get_all_versions(self) -> List[str]:
        """Get all available versions"""
        versions = set()
        for route_key in self.gateway_manager.routes:
            _, version = route_key.split(":", 1)
            versions.add(version)
        return sorted(list(versions), key=self._version_sort_key)
    
    def _version_sort_key(self, version: str) -> Tuple[int, int, int]:
        """Sort version strings properly"""
        try:
            parts = version.split('.')
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return (major, minor, patch)
        except (ValueError, IndexError):
            return (0, 0, 0)
    
    def check_version_compatibility(self, requested_version: str, 
                                 available_version: str) -> Dict[str, Any]:
        """Check version compatibility"""
        try:
            req_parts = [int(x) for x in requested_version.split('.')]
            avail_parts = [int(x) for x in available_version.split('.')]
            
            # Pad with zeros to make same length
            max_len = max(len(req_parts), len(avail_parts))
            req_parts.extend([0] * (max_len - len(req_parts)))
            avail_parts.extend([0] * (max_len - len(avail_parts)))
            
            # Compare versions
            if req_parts == avail_parts:
                return {'compatible': True, 'status': 'exact_match'}
            elif req_parts < avail_parts:
                return {'compatible': True, 'status': 'older_version'}
            elif req_parts > avail_parts:
                return {'compatible': False, 'status': 'newer_version'}
            else:
                return {'compatible': False, 'status': 'incompatible'}
        
        except (ValueError, AttributeError):
            return {'compatible': False, 'status': 'invalid_format'}
    
    def get_migration_path(self, from_version: str, to_version: str) -> List[Dict[str, Any]]:
        """Get migration path between versions"""
        try:
            from_parts = [int(x) for x in from_version.split('.')]
            to_parts = [int(x) for x in to_version.split('.')]
            
            # Simple incremental migration path
            path = []
            current = from_parts.copy()
            
            while current != to_parts:
                # Increment version
                if len(current) == 1:
                    current[0] += 1
                elif len(current) == 2:
                    if current[1] < 9:
                        current[1] += 1
                    else:
                        current[1] = 0
                        current[0] += 1
                else:
                    if current[2] < 9:
                        current[2] += 1
                    elif current[1] < 9:
                        current[1] += 1
                        current[2] = 0
                    else:
                        current[1] = 0
                        current[0] += 1
                        current[2] = 0
                
                path.append({
                    'version': '.'.join(str(x) for x in current),
                    'type': 'incremental',
                    'breaking_changes': self._has_breaking_changes(current, from_parts)
                })
                
                if current == to_parts:
                    break
            
            return path
        
        except (ValueError, AttributeError):
            return []
    
    def _has_breaking_changes(self, current_version: List[int], 
                              from_version: List[int]) -> bool:
        """Check if version increment has breaking changes"""
        # Major version changes are breaking
        if current_version[0] > from_version[0]:
            return True
        
        # Minor version changes might be breaking
        if len(current_version) > 1 and current_version[1] > from_version[1]:
            return True
        
        return False
    
    def handle_version_deprecation(self, version: str) -> Dict[str, Any]:
        """Handle version deprecation warnings"""
        # In production, this would check deprecation dates
        # For now, return basic deprecation info
        all_versions = self.get_all_versions()
        
        if version not in all_versions:
            return {'deprecated': False}
        
        version_index = all_versions.index(version)
        latest_index = len(all_versions) - 1
        
        if version_index < latest_index:
            versions_behind = latest_index - version_index
            return {
                'deprecated': True,
                'versions_behind': versions_behind,
                'recommended_version': all_versions[-1],
                'warning': f"Version {version} is {versions_behind} versions behind latest"
            }
        
        return {'deprecated': False}
    
    def add_route_pattern(self, name: str, pattern: str, pattern_type: str = 'regex'):
        """Add custom route pattern for version detection"""
        if pattern_type == 'regex':
            self.version_patterns[name] = re.compile(pattern)
        else:
            self.version_patterns[name] = pattern
        
        logger.info(f"Added route pattern: {name} ({pattern_type})")
    
    def remove_route_pattern(self, name: str):
        """Remove a route pattern"""
        if name in self.version_patterns:
            del self.version_patterns[name]
            logger.info(f"Removed route pattern: {name}")
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            'total_routes': len(self.gateway_manager.routes),
            'total_services': len(self.gateway_manager.services),
            'cached_routes': len(self.route_cache),
            'version_patterns': list(self.version_patterns.keys()),
            'available_versions': self.get_all_versions(),
            'default_version': self.gateway_manager.config.default_version
        }
