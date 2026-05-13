"""
Security Module

Advanced security monitoring, threat detection, and compliance tracking for the Auto Bot Solutions Forum.
Provides comprehensive security event logging, audit trail management, threat detection, and regulatory compliance.
"""

from .models import SecurityEvent, AuditTrail, ThreatDetection, ComplianceRecord
from .service import SecurityService, get_security_service, log_security_event, log_audit_action
from .utils import SecurityUtils, ThreatDetector, ComplianceHelper, SecurityMonitor
from .config import (
    SECURITY_ENABLED, THREAT_DETECTION_ENABLED, AUDIT_TRAIL_ENABLED, COMPLIANCE_ENABLED,
    SECURITY_EVENT_CONFIG, THREAT_DETECTION_CONFIG, AUDIT_TRAIL_CONFIG, COMPLIANCE_CONFIG,
    SECURITY_MONITORING_CONFIG, DATA_PROTECTION_CONFIG, SESSION_SECURITY_CONFIG,
    IP_SECURITY_CONFIG, USER_AGENT_SECURITY_CONFIG, API_SECURITY_CONFIG,
    SECURITY_LOGGING_CONFIG, BACKUP_CONFIG, INTEGRATION_CONFIG, PERFORMANCE_CONFIG,
    SECURITY_HEADERS, get_security_config, validate_security_config
)

__all__ = [
    # Models
    'SecurityEvent',
    'AuditTrail', 
    'ThreatDetection',
    'ComplianceRecord',
    
    # Services
    'SecurityService',
    'get_security_service',
    'log_security_event',
    'log_audit_action',
    
    # Utilities
    'SecurityUtils',
    'ThreatDetector',
    'ComplianceHelper',
    'SecurityMonitor',
    
    # Configuration
    'SECURITY_ENABLED',
    'THREAT_DETECTION_ENABLED',
    'AUDIT_TRAIL_ENABLED',
    'COMPLIANCE_ENABLED',
    'SECURITY_EVENT_CONFIG',
    'THREAT_DETECTION_CONFIG',
    'AUDIT_TRAIL_CONFIG',
    'COMPLIANCE_CONFIG',
    'SECURITY_MONITORING_CONFIG',
    'DATA_PROTECTION_CONFIG',
    'SESSION_SECURITY_CONFIG',
    'IP_SECURITY_CONFIG',
    'USER_AGENT_SECURITY_CONFIG',
    'API_SECURITY_CONFIG',
    'SECURITY_LOGGING_CONFIG',
    'BACKUP_CONFIG',
    'INTEGRATION_CONFIG',
    'PERFORMANCE_CONFIG',
    'SECURITY_HEADERS',
    'get_security_config',
    'validate_security_config'
]
