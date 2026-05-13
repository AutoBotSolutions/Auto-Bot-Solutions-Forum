"""
API Version Manager

Manages API versions, compatibility, and deprecation policies.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import re

class VersionStatus(Enum):
    """API version status"""
    ACTIVE = "active"
    DEPRECATED = "deprecated" 
    SUNSET = "sunset"
    DEVELOPMENT = "development"

class APIVersion:
    """Represents an API version"""
    
    def __init__(self, version: str, status: VersionStatus, 
                 deprecation_date: Optional[datetime] = None,
                 sunset_date: Optional[datetime] = None,
                 description: str = ""):
        self.version = version
        self.status = status
        self.deprecation_date = deprecation_date
        self.sunset_date = sunset_date
        self.description = description
        self.endpoints = {}
        self.created_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """Check if version is active"""
        return self.status == VersionStatus.ACTIVE
    
    def is_deprecated(self) -> bool:
        """Check if version is deprecated"""
        return self.status == VersionStatus.DEPRECATED
    
    def is_sunset(self) -> bool:
        """Check if version is sunset"""
        return self.status == VersionStatus.SUNSET
    
    def days_until_sunset(self) -> Optional[int]:
        """Get days until sunset"""
        if not self.sunset_date:
            return None
        return (self.sunset_date - datetime.utcnow()).days
    
    def add_endpoint(self, path: str, handler: Callable, methods: List[str]):
        """Add endpoint to version"""
        self.endpoints[path] = {
            'handler': handler,
            'methods': methods
        }

class APIVersionManager:
    """Manages API versions and routing"""
    
    def __init__(self, default_version: str = "v1"):
        self.default_version = default_version
        self.versions: Dict[str, APIVersion] = {}
        self.version_patterns: Dict[str, str] = {}
        self.compatibility_matrix: Dict[str, List[str]] = {}
        self._initialize_default_versions()
    
    def _initialize_default_versions(self):
        """Initialize default API versions"""
        # v1 - Current stable version
        self.register_version(
            version="v1",
            status=VersionStatus.ACTIVE,
            description="Current stable API version"
        )
        
        # v2 - Development version
        self.register_version(
            version="v2", 
            status=VersionStatus.DEVELOPMENT,
            description="Next generation API in development"
        )
        
        # Set up compatibility
        self.set_compatibility("v1", ["v1"])
        self.set_compatibility("v2", ["v2", "v1"])  # v2 can handle v1 requests
    
    def register_version(self, version: str, status: VersionStatus = VersionStatus.ACTIVE,
                        deprecation_date: Optional[datetime] = None,
                        sunset_date: Optional[datetime] = None,
                        description: str = ""):
        """Register a new API version"""
        self.versions[version] = APIVersion(
            version=version,
            status=status,
            deprecation_date=deprecation_date,
            sunset_date=sunset_date,
            description=description
        )
        
        # Set up version pattern
        self.version_patterns[version] = f"/api/{version}"
    
    def get_version(self, version: str) -> Optional[APIVersion]:
        """Get version by name"""
        return self.versions.get(version)
    
    def get_active_versions(self) -> List[APIVersion]:
        """Get all active versions"""
        return [v for v in self.versions.values() if v.is_active()]
    
    def get_deprecated_versions(self) -> List[APIVersion]:
        """Get all deprecated versions"""
        return [v for v in self.versions.values() if v.is_deprecated()]
    
    def get_sunset_versions(self) -> List[APIVersion]:
        """Get all sunset versions"""
        return [v for v in self.versions.values() if v.is_sunset()]
    
    def deprecate_version(self, version: str, deprecation_date: datetime, 
                         sunset_date: datetime):
        """Deprecate a version"""
        if version in self.versions:
            self.versions[version].status = VersionStatus.DEPRECATED
            self.versions[version].deprecation_date = deprecation_date
            self.versions[version].sunset_date = sunset_date
    
    def sunset_version(self, version: str):
        """Sunset a version"""
        if version in self.versions:
            self.versions[version].status = VersionStatus.SUNSET
    
    def set_compatibility(self, version: str, compatible_versions: List[str]):
        """Set compatible versions for backward compatibility"""
        self.compatibility_matrix[version] = compatible_versions
    
    def get_compatible_versions(self, version: str) -> List[str]:
        """Get versions compatible with given version"""
        return self.compatibility_matrix.get(version, [version])
    
    def is_version_compatible(self, requested_version: str, 
                            supported_version: str) -> bool:
        """Check if versions are compatible"""
        compatible = self.get_compatible_versions(supported_version)
        return requested_version in compatible
    
    def parse_version_from_path(self, path: str) -> Optional[str]:
        """Extract version from URL path"""
        # Pattern: /api/v1/...
        match = re.match(r'/api/([^/]+)/', path)
        if match:
            return match.group(1)
        return None
    
    def get_version_from_request(self, request_headers: Dict[str, str], 
                               request_path: str) -> str:
        """Get version from request headers or path"""
        # Check Accept-Version header first
        accept_version = request_headers.get('Accept-Version')
        if accept_version and accept_version in self.versions:
            return accept_version
        
        # Check API-Version header
        api_version = request_headers.get('API-Version')
        if api_version and api_version in self.versions:
            return api_version
        
        # Extract from path
        path_version = self.parse_version_from_path(request_path)
        if path_version and path_version in self.versions:
            return path_version
        
        # Return default version
        return self.default_version
    
    def get_versioned_url(self, base_url: str, version: str) -> str:
        """Get versioned URL"""
        version_obj = self.get_version(version)
        if not version_obj:
            raise ValueError(f"Unknown version: {version}")
        
        pattern = self.version_patterns.get(version, f"/api/{version}")
        return f"{base_url}{pattern}"
    
    def get_endpoint_handler(self, version: str, path: str, method: str) -> Optional[Callable]:
        """Get endpoint handler for version"""
        version_obj = self.get_version(version)
        if not version_obj:
            return None
        
        # Remove version prefix from path
        version_pattern = self.version_patterns.get(version, f"/api/{version}")
        clean_path = path.replace(version_pattern, "", 1)
        
        # Find endpoint
        if clean_path in version_obj.endpoints:
            endpoint = version_obj.endpoints[clean_path]
            if method.upper() in endpoint['methods']:
                return endpoint['handler']
        
        return None
    
    def register_endpoint(self, version: str, path: str, handler: Callable, 
                          methods: List[str]):
        """Register endpoint for specific version"""
        version_obj = self.get_version(version)
        if not version_obj:
            raise ValueError(f"Unknown version: {version}")
        
        version_obj.add_endpoint(path, handler, methods)
    
    def get_version_info(self, version: str) -> Dict[str, Any]:
        """Get version information"""
        version_obj = self.get_version(version)
        if not version_obj:
            return {}
        
        return {
            'version': version_obj.version,
            'status': version_obj.status.value,
            'description': version_obj.description,
            'created_at': version_obj.created_at.isoformat(),
            'deprecation_date': version_obj.deprecation_date.isoformat() if version_obj.deprecation_date else None,
            'sunset_date': version_obj.sunset_date.isoformat() if version_obj.sunset_date else None,
            'days_until_sunset': version_obj.days_until_sunset(),
            'endpoint_count': len(version_obj.endpoints),
            'compatible_versions': self.get_compatible_versions(version)
        }
    
    def get_all_versions_info(self) -> Dict[str, Any]:
        """Get information about all versions"""
        return {
            'default_version': self.default_version,
            'versions': {
                version: self.get_version_info(version)
                for version in self.versions
            },
            'active_count': len(self.get_active_versions()),
            'deprecated_count': len(self.get_deprecated_versions()),
            'sunset_count': len(self.get_sunset_versions())
        }
    
    def validate_version_request(self, version: str, request_path: str) -> Dict[str, Any]:
        """Validate version request"""
        version_obj = self.get_version(version)
        if not version_obj:
            return {
                'valid': False,
                'error': 'Unknown version',
                'available_versions': list(self.versions.keys())
            }
        
        if version_obj.is_sunset():
            return {
                'valid': False,
                'error': 'Version has been sunset',
                'sunset_date': version_obj.sunset_date.isoformat(),
                'recommended_version': self.default_version
            }
        
        if version_obj.is_deprecated():
            return {
                'valid': True,
                'warning': 'Version is deprecated',
                'deprecation_date': version_obj.deprecation_date.isoformat(),
                'sunset_date': version_obj.sunset_date.isoformat(),
                'days_until_sunset': version_obj.days_until_sunset(),
                'recommended_version': self.default_version
            }
        
        return {'valid': True}

# Global version manager instance
version_manager = APIVersionManager()
