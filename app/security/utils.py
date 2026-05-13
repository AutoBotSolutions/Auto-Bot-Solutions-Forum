"""
Security Utilities

Utility functions and helpers for security monitoring, threat detection, and compliance management.
"""

import re
import json
import hashlib
import ipaddress
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from flask import request
from app.security.service import get_security_service


class SecurityUtils:
    """Security utility functions for threat detection and analysis"""
    
    @staticmethod
    def extract_ip_info(ip_address: str) -> Dict[str, Any]:
        """Extract information from IP address"""
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            
            info = {
                'ip_address': ip_address,
                'is_private': ip_obj.is_private,
                'is_loopback': ip_obj.is_loopback,
                'is_multicast': ip_obj.is_multicast,
                'version': ip_obj.version
            }
            
            # Check for suspicious IP ranges
            if not ip_obj.is_private and not ip_obj.is_loopback:
                info['is_public'] = True
                # Add more sophisticated IP analysis here
                # Could integrate with GeoIP databases
            else:
                info['is_public'] = False
            
            return info
            
        except Exception:
            return {
                'ip_address': ip_address,
                'is_private': False,
                'is_loopback': False,
                'is_multicast': False,
                'is_public': False,
                'version': None,
                'error': 'Invalid IP address'
            }
    
    @staticmethod
    def analyze_user_agent(user_agent: str) -> Dict[str, Any]:
        """Analyze user agent string for security insights"""
        if not user_agent:
            return {'error': 'No user agent provided'}
        
        analysis = {
            'user_agent': user_agent,
            'length': len(user_agent),
            'suspicious_patterns': []
        }
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'bot',
            r'crawler',
            r'spider',
            r'scanner',
            r'curl',
            r'wget',
            r'python',
            r'perl',
            r'java',
            r'wget',
            r'powershell',
            r'bash'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                analysis['suspicious_patterns'].append(pattern)
        
        # Detect browser type
        browsers = {
            'chrome': r'chrome/[0-9]',
            'firefox': r'firefox/[0-9]',
            'safari': r'safari/[0-9]',
            'edge': r'edge/[0-9]',
            'opera': r'opera/[0-9]',
            'ie': r'msie|trident'
        }
        
        detected_browsers = []
        for browser, pattern in browsers.items():
            if re.search(pattern, user_agent, re.IGNORECASE):
                detected_browsers.append(browser)
        
        analysis['browsers'] = detected_browsers
        analysis['is_bot'] = len(analysis['suspicious_patterns']) > 0
        analysis['risk_score'] = len(analysis['suspicious_patterns']) / len(suspicious_patterns)
        
        return analysis
    
    @staticmethod
    def detect_sql_injection(input_data: str) -> Dict[str, Any]:
        """Detect SQL injection patterns in input data"""
        if not input_data:
            return {'detected': False, 'patterns': []}
        
        # SQL injection patterns
        sql_patterns = [
            r"union\s+select",
            r"select\s+.*\s+from",
            r"drop\s+table",
            r"insert\s+into",
            r"update\s+.*\s+set",
            r"delete\s+from",
            r"exec\s*\(",
            r"script\s*>",
            r"javascript:",
            r"eval\s*\(",
            r"base64_decode",
            r"system\s*\(",
            r"shell_exec",
            r"passthru",
            r"file_get_contents",
            r"fopen\s*\(",
            r"include\s*",
            r"require\s*"
        ]
        
        detected_patterns = []
        input_lower = input_data.lower()
        
        for pattern in sql_patterns:
            if re.search(pattern, input_lower):
                detected_patterns.append(pattern)
        
        return {
            'detected': len(detected_patterns) > 0,
            'patterns': detected_patterns,
            'risk_score': len(detected_patterns) / len(sql_patterns),
            'input_length': len(input_data)
        }
    
    @staticmethod
    def detect_xss(input_data: str) -> Dict[str, Any]:
        """Detect XSS (Cross-Site Scripting) patterns in input data"""
        if not input_data:
            return {'detected': False, 'patterns': []}
        
        # XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"onfocus\s*=",
            r"onblur\s*=",
            r"onchange\s*=",
            r"onsubmit\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"alert\s*\(",
            r"confirm\s*\(",
            r"prompt\s*\(",
            r"document\.cookie",
            r"window\.location",
            r"document\.write"
        ]
        
        detected_patterns = []
        input_lower = input_data.lower()
        
        for pattern in xss_patterns:
            if re.search(pattern, input_lower, re.IGNORECASE):
                detected_patterns.append(pattern)
        
        return {
            'detected': len(detected_patterns) > 0,
            'patterns': detected_patterns,
            'risk_score': len(detected_patterns) / len(xss_patterns),
            'input_length': len(input_data)
        }
    
    @staticmethod
    def analyze_request_patterns(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request patterns for security threats"""
        analysis = {
            'total_parameters': len(request_data),
            'suspicious_parameters': [],
            'sql_injection_risks': [],
            'xss_risks': [],
            'overall_risk_score': 0.0
        }
        
        sql_risks = []
        xss_risks = []
        
        for key, value in request_data.items():
            if isinstance(value, str):
                # Check for SQL injection
                sql_result = SecurityUtils.detect_sql_injection(value)
                if sql_result['detected']:
                    sql_risks.append({
                        'parameter': key,
                        'patterns': sql_result['patterns'],
                        'risk_score': sql_result['risk_score']
                    })
                
                # Check for XSS
                xss_result = SecurityUtils.detect_xss(value)
                if xss_result['detected']:
                    xss_risks.append({
                        'parameter': key,
                        'patterns': xss_result['patterns'],
                        'risk_score': xss_result['risk_score']
                    })
                
                # Check for suspicious parameter names
                suspicious_param_names = [
                    'admin', 'password', 'secret', 'token', 'key', 'auth',
                    'debug', 'test', 'exec', 'cmd', 'shell', 'system'
                ]
                
                if any(suspicious in key.lower() for suspicious in suspicious_param_names):
                    analysis['suspicious_parameters'].append(key)
        
        analysis['sql_injection_risks'] = sql_risks
        analysis['xss_risks'] = xss_risks
        
        # Calculate overall risk score
        total_risks = len(sql_risks) + len(xss_risks)
        analysis['overall_risk_score'] = min(total_risks / max(len(request_data), 1), 1.0)
        
        return analysis
    
    @staticmethod
    def generate_session_fingerprint(user_id: int, ip_address: str, user_agent: str) -> str:
        """Generate a unique session fingerprint for security tracking"""
        fingerprint_data = f"{user_id}:{ip_address}:{user_agent}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    @staticmethod
    def validate_session_integrity(user_id: int, current_fingerprint: str, 
                                 stored_fingerprint: str) -> bool:
        """Validate session integrity to prevent session hijacking"""
        return current_fingerprint == stored_fingerprint
    
    @staticmethod
    def calculate_risk_score(severity: str, confidence: float, impact: float = 1.0) -> float:
        """Calculate risk score based on severity, confidence, and impact"""
        severity_weights = {
            'low': 0.25,
            'medium': 0.5,
            'high': 0.75,
            'critical': 1.0
        }
        
        severity_weight = severity_weights.get(severity, 0.5)
        return (severity_weight * confidence * impact)
    
    @staticmethod
    def format_threat_description(threat_type: str, details: Dict[str, Any]) -> str:
        """Format threat description for logging"""
        descriptions = {
            'brute_force': "Brute force attack detected",
            'sql_injection': "SQL injection attempt detected",
            'xss': "Cross-site scripting attempt detected",
            'ddos': "Potential DDoS attack detected",
            'suspicious_activity': "Suspicious activity detected",
            'unauthorized_access': "Unauthorized access attempt detected"
        }
        
        base_description = descriptions.get(threat_type, f"Unknown threat type: {threat_type}")
        
        # Add specific details
        if 'source_ip' in details:
            base_description += f" from {details['source_ip']}"
        
        if 'failed_attempts' in details:
            base_description += f" ({details['failed_attempts']} attempts)"
        
        return base_description


class ThreatDetector:
    """Advanced threat detection algorithms"""
    
    def __init__(self):
        self.security_service = get_security_service()
    
    def detect_anomalous_login_patterns(self, user_id: int, login_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect anomalous login patterns"""
        # Get user's recent login history
        recent_logins = self.security_service.log_security_event(
            event_type='login',
            event_category='authentication',
            description='Login attempt',
            user_id=user_id
        )
        
        # Analyze patterns
        anomalies = []
        
        # Check for unusual login time
        current_time = datetime.utcnow()
        usual_hours = [9, 10, 11, 14, 15, 16, 17, 18]  # Business hours
        
        if current_time.hour not in usual_hours:
            anomalies.append('unusual_time')
        
        # Check for unusual location (IP address)
        current_ip = login_data.get('ip_address')
        if current_ip:
            # This would typically involve GeoIP lookup
            pass
        
        # Check for unusual device
        current_user_agent = login_data.get('user_agent')
        if current_user_agent:
            # Compare with previous user agents
            pass
        
        if anomalies:
            return {
                'anomalies': anomalies,
                'risk_score': len(anomalies) / 3.0,
                'confidence': 0.7
            }
        
        return None
    
    def detect_data_exfiltration(self, user_id: int, access_patterns: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Detect potential data exfiltration patterns"""
        if len(access_patterns) < 5:
            return None
        
        # Analyze access patterns
        total_downloads = 0
        unique_resources = set()
        access_frequency = {}
        
        for pattern in access_patterns:
            if pattern.get('action') == 'download':
                total_downloads += 1
            unique_resources.add(pattern.get('resource_id'))
            
            # Track access frequency
            resource_id = pattern.get('resource_id')
            if resource_id:
                access_frequency[resource_id] = access_frequency.get(resource_id, 0) + 1
        
        # Detect suspicious patterns
        suspicious_indicators = []
        
        # High volume downloads
        if total_downloads > 50:
            suspicious_indicators.append('high_volume_downloads')
        
        # Access to many different resources
        if len(unique_resources) > 100:
            suspicious_indicators.append('broad_resource_access')
        
        # Frequent access to same resources
        max_frequency = max(access_frequency.values()) if access_frequency else 0
        if max_frequency > 20:
            suspicious_indicators.append('repeated_access')
        
        if suspicious_indicators:
            risk_score = len(suspicious_indicators) / 3.0
            confidence = 0.8
            
            return {
                'suspicious_indicators': suspicious_indicators,
                'risk_score': risk_score,
                'confidence': confidence,
                'total_downloads': total_downloads,
                'unique_resources': len(unique_resources),
                'max_frequency': max_frequency
            }
        
        return None
    
    def detect_privilege_escalation(self, user_id: int, privilege_changes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Detect potential privilege escalation attempts"""
        if len(privilege_changes) < 3:
            return None
        
        # Analyze privilege change patterns
        escalation_indicators = []
        
        # Rapid privilege changes
        time_window = timedelta(hours=1)
        if len(privilege_changes) > 5:
            escalation_indicators.append('rapid_privilege_changes')
        
        # Changes to high-privilege roles
        high_privilege_roles = ['admin', 'superuser', 'root', 'administrator']
        for change in privilege_changes:
            if change.get('new_role') in high_privilege_roles:
                escalation_indicators.append('high_privilege_access')
                break
        
        # Self-privilege changes
        self_changes = [c for c in privilege_changes if c.get('changed_by') == user_id]
        if len(self_changes) > 2:
            escalation_indicators.append('self_privilege_changes')
        
        if escalation_indicators:
            risk_score = len(escalation_indicators) / 3.0
            confidence = 0.9
            
            return {
                'escalation_indicators': escalation_indicators,
                'risk_score': risk_score,
                'confidence': confidence,
                'total_changes': len(privilege_changes),
                'self_changes': len(self_changes)
            }
        
        return None


class ComplianceHelper:
    """Helper class for compliance management and reporting"""
    
    @staticmethod
    def generate_gdpr_report(user_id: int, days: int = 30) -> Dict[str, Any]:
        """Generate GDPR compliance report for a user"""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get user's data access records
        access_records = AuditTrail.query.filter(
            and_(
                AuditTrail.user_id == user_id,
                AuditTrail.action_timestamp >= start_date
            )
        ).all()
        
        # Get user's security events
        security_events = SecurityEvent.query.filter(
            and_(
                SecurityEvent.user_id == user_id,
                SecurityEvent.event_timestamp >= start_date
            )
        ).all()
        
        # Analyze data processing activities
        data_processing = {
            'access_count': len(access_records),
            'security_events': len(security_events),
            'data_types': set(),
            'processing_purposes': set(),
            'retention_period': days
        }
        
        for record in access_records:
            if record.resource_type:
                data_processing['data_types'].add(record.resource_type)
            if record.action:
                data_processing['processing_purposes'].add(record.action)
        
        return {
            'user_id': user_id,
            'report_period': f"{days} days",
            'generated_at': datetime.utcnow().isoformat(),
            'data_processing': {
                **data_processing,
                'data_types': list(data_processing['data_types']),
                'processing_purposes': list(data_processing['processing_purposes'])
            },
            'access_records': [record.to_dict() for record in access_records],
            'security_events': [event.to_dict() for event in security_events]
        }
    
    @staticmethod
    def generate_security_audit_report(days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive security audit report"""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Security events summary
        security_summary = SecurityEvent.get_security_summary(hours=days*24)
        
        # Threat detection summary
        threat_summary = ThreatDetection.get_threat_summary(hours=days*24)
        
        # Audit trail summary
        audit_summary = AuditTrail.get_audit_summary(hours=days*24)
        
        # Compliance records
        compliance_records = ComplianceRecord.query.filter(
            ComplianceRecord.created_at >= start_date
        ).all()
        
        # Calculate compliance metrics
        total_compliance_records = len(compliance_records)
        compliant_records = len([r for r in compliance_records if r.status == 'compliant'])
        compliance_rate = (compliant_records / max(total_compliance_records, 1)) * 100
        
        return {
            'report_period': f"{days} days",
            'generated_at': datetime.utcnow().isoformat(),
            'security_summary': security_summary,
            'threat_summary': threat_summary,
            'audit_summary': audit_summary,
            'compliance_metrics': {
                'total_records': total_compliance_records,
                'compliant_records': compliant_records,
                'compliance_rate': compliance_rate
            },
            'compliance_records': [record.to_dict() for record in compliance_records]
        }
    
    @staticmethod
    def validate_gdpr_compliance(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GDPR compliance for user data"""
        validation_result = {
            'compliant': True,
            'issues': [],
            'recommendations': []
        }
        
        # Check for required fields
        required_fields = ['email', 'consent_given', 'data_retention_period']
        for field in required_fields:
            if field not in user_data:
                validation_result['issues'].append(f"Missing required field: {field}")
                validation_result['compliant'] = False
        
        # Check consent
        if not user_data.get('consent_given', False):
            validation_result['issues'].append("User consent not recorded")
            validation_result['compliant'] = False
            validation_result['recommendations'].append("Obtain explicit user consent")
        
        # Check data retention
        retention_period = user_data.get('data_retention_period')
        if retention_period and retention_period > 365 * 7:  # 7 years
            validation_result['issues'].append("Data retention period exceeds GDPR limits")
            validation_result['compliant'] = False
            validation_result['recommendations'].append("Reduce data retention period to 7 years or less")
        
        # Check data minimization
        if len(user_data) > 50:  # Arbitrary threshold for data minimization
            validation_result['recommendations'].append("Consider data minimization - collect only necessary data")
        
        return validation_result


class SecurityMonitor:
    """Real-time security monitoring"""
    
    def __init__(self):
        self.security_service = get_security_service()
        self.alert_thresholds = {
            'failed_logins_per_hour': 10,
            'suspicious_activities_per_hour': 20,
            'high_risk_threats_per_hour': 5
        }
    
    def monitor_real_time_threats(self):
        """Monitor for real-time threats"""
        alerts = []
        
        # Check for brute force attacks
        failed_logins = SecurityEvent.get_events_by_type('failed_login', hours=1)
        if len(failed_logins) >= self.alert_thresholds['failed_logins_per_hour']:
            alerts.append({
                'type': 'brute_force_attack',
                'severity': 'high',
                'count': len(failed_logins),
                'message': f"High number of failed login attempts: {len(failed_logins)}"
            })
        
        # Check for suspicious activities
        suspicious_events = SecurityEvent.get_events_by_severity('high', hours=1)
        if len(suspicious_events) >= self.alert_thresholds['suspicious_activities_per_hour']:
            alerts.append({
                'type': 'suspicious_activity_spike',
                'severity': 'medium',
                'count': len(suspicious_events),
                'message': f"High number of suspicious activities: {len(suspicious_events)}"
            })
        
        # Check for high-risk threats
        high_risk_threats = ThreatDetection.get_threats_by_severity('critical', hours=1)
        if len(high_risk_threats) >= self.alert_thresholds['high_risk_threats_per_hour']:
            alerts.append({
                'type': 'critical_threats',
                'severity': 'critical',
                'count': len(high_risk_threats),
                'message': f"High number of critical threats: {len(high_risk_threats)}"
            })
        
        return alerts
    
    def generate_security_alerts(self) -> List[Dict[str, Any]]:
        """Generate security alerts for dashboard"""
        alerts = []
        
        # Real-time monitoring
        real_time_alerts = self.monitor_real_time_threats()
        alerts.extend(real_time_alerts)
        
        # Check for unresolved threats
        active_threats = ThreatDetection.get_active_threats(hours=24)
        if active_threats:
            alerts.append({
                'type': 'active_threats',
                'severity': 'medium',
                'count': len(active_threats),
                'message': f"{len(active_threats)} active threats require attention"
            })
        
        # Check for compliance issues
        non_compliant = ComplianceRecord.get_records_by_status('non_compliant', limit=10)
        if non_compliant:
            alerts.append({
                'type': 'compliance_issues',
                'severity': 'medium',
                'count': len(non_compliant),
                'message': f"{len(non_compliant)} compliance issues need attention"
            })
        
        return alerts
