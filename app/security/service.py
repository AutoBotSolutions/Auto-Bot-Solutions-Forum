"""
Security Service

Comprehensive security monitoring and threat detection service for the Auto Bot Solutions Forum.
Provides security event logging, audit trail management, threat detection, and compliance tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from flask import current_app, request
from sqlalchemy import and_, or_, desc, func
from app import db
from app.security.models import SecurityEvent, AuditTrail, ThreatDetection, ComplianceRecord

logger = logging.getLogger(__name__)

class SecurityService:
    """Comprehensive security service for monitoring and threat detection"""
    
    def __init__(self):
        self.enabled = current_app.config.get('SECURITY_ENABLED', True)
        self.threat_detection_enabled = current_app.config.get('THREAT_DETECTION_ENABLED', True)
        self.audit_trail_enabled = current_app.config.get('AUDIT_TRAIL_ENABLED', True)
        self.compliance_enabled = current_app.config.get('COMPLIANCE_ENABLED', True)
    
    def log_security_event(self, event_type, event_category, description, severity='medium',
                          user_id=None, session_id=None, ip_address=None, user_agent=None,
                          resource_type=None, resource_id=None, action=None, request_method=None,
                          request_url=None, referrer=None, country=None, region=None, city=None,
                          device_type=None, browser=None, operating_system=None, success=True,
                          error_message=None, event_data=None):
        """Log a security event"""
        if not self.enabled:
            return None
        
        try:
            return SecurityEvent.log_event(
                event_type=event_type,
                event_category=event_category,
                description=description,
                severity=severity,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                request_method=request_method,
                request_url=request_url,
                referrer=referrer,
                country=country,
                region=region,
                city=city,
                device_type=device_type,
                browser=browser,
                operating_system=operating_system,
                success=success,
                error_message=error_message,
                event_data=event_data
            )
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")
            return None
    
    def log_audit_action(self, action, action_category, description, user_id=None, user_email=None,
                        username=None, resource_type=None, resource_id=None, resource_name=None,
                        old_values=None, new_values=None, changed_fields=None, ip_address=None,
                        user_agent=None, request_method=None, request_url=None, module_name=None,
                        function_name=None, line_number=None, metadata=None):
        """Log an audit action"""
        if not self.audit_trail_enabled:
            return None
        
        try:
            return AuditTrail.log_action(
                action=action,
                action_category=action_category,
                description=description,
                user_id=user_id,
                user_email=user_email,
                username=username,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                old_values=old_values,
                new_values=new_values,
                changed_fields=changed_fields,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_url=request_url,
                module_name=module_name,
                function_name=function_name,
                line_number=line_number,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error logging audit action: {str(e)}")
            return None
    
    def detect_threat(self, threat_type, threat_category, description, severity='medium',
                      source_ip=None, source_user_id=None, source_user_agent=None,
                      target_type=None, target_id=None, target_details=None,
                      detection_method=None, detection_rules=None, detection_data=None,
                      risk_score=0.0, confidence=0.0, details=None, metadata=None):
        """Detect and log a threat"""
        if not self.threat_detection_enabled:
            return None
        
        try:
            return ThreatDetection.detect_threat(
                threat_type=threat_type,
                threat_category=threat_category,
                description=description,
                severity=severity,
                source_ip=source_ip,
                source_user_id=source_user_id,
                source_user_agent=source_user_agent,
                target_type=target_type,
                target_id=target_id,
                target_details=target_details,
                detection_method=detection_method,
                detection_rules=detection_rules,
                detection_data=detection_data,
                risk_score=risk_score,
                confidence=confidence,
                details=details,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error detecting threat: {str(e)}")
            return None
    
    def create_compliance_record(self, compliance_type, compliance_category, description,
                                compliance_period, period_start, period_end, regulation=None,
                                requirement=None, assessment_method=None, assessor_id=None,
                                evidence_files=None, documentation=None, test_results=None,
                                issues_found=None, remediation_actions=None, remediation_deadline=None,
                                findings=None, recommendations=None, metadata=None):
        """Create a compliance record"""
        if not self.compliance_enabled:
            return None
        
        try:
            return ComplianceRecord.create_compliance_record(
                compliance_type=compliance_type,
                compliance_category=compliance_category,
                description=description,
                compliance_period=compliance_period,
                period_start=period_start,
                period_end=period_end,
                regulation=regulation,
                requirement=requirement,
                assessment_method=assessment_method,
                assessor_id=assessor_id,
                evidence_files=evidence_files,
                documentation=documentation,
                test_results=test_results,
                issues_found=issues_found,
                remediation_actions=remediation_actions,
                remediation_deadline=remediation_deadline,
                findings=findings,
                recommendations=recommendations,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error creating compliance record: {str(e)}")
            return None
    
    def detect_brute_force_attack(self, ip_address, user_id=None, failed_attempts=1):
        """Detect brute force attack attempts"""
        # Get recent failed login attempts
        recent_failures = SecurityEvent.get_failed_login_attempts(
            ip_address=ip_address,
            hours=1
        )
        
        failure_count = len(recent_failures) + failed_attempts
        
        # Detect brute force patterns
        if failure_count >= 5:  # 5 failed attempts in 1 hour
            risk_score = min(failure_count / 10.0, 1.0)  # Scale to 0-1
            confidence = 0.8
            
            return self.detect_threat(
                threat_type='brute_force',
                threat_category='authentication',
                description=f'Brute force attack detected from {ip_address}',
                severity='high' if failure_count >= 10 else 'medium',
                source_ip=ip_address,
                source_user_id=user_id,
                detection_method='pattern_analysis',
                detection_data={
                    'failed_attempts': failure_count,
                    'time_window': '1 hour',
                    'ip_address': ip_address
                },
                risk_score=risk_score,
                confidence=confidence,
                details=f'{failure_count} failed login attempts detected in the last hour'
            )
        
        return None
    
    def detect_suspicious_activity(self, user_id, activity_patterns=None):
        """Detect suspicious user activity patterns"""
        if not activity_patterns:
            return None
        
        # Get user's recent activities
        recent_activities = SecurityEvent.get_user_events(user_id, hours=24)
        
        # Analyze patterns
        suspicious_indicators = []
        
        # Check for rapid login attempts
        login_events = [e for e in recent_activities if e.event_type == 'login']
        if len(login_events) > 10:  # More than 10 logins in 24 hours
            suspicious_indicators.append('excessive_logins')
        
        # Check for unusual access patterns
        unique_ips = set(e.ip_address for e in recent_activities if e.ip_address)
        if len(unique_ips) > 5:  # Access from many different IPs
            suspicious_indicators.append('multiple_ip_access')
        
        # Check for failed authentication
        failed_events = [e for e in recent_activities if not e.success]
        if len(failed_events) > 5:  # Many failed events
            suspicious_indicators.append('high_failure_rate')
        
        if suspicious_indicators:
            risk_score = len(suspicious_indicators) / 3.0  # Scale based on indicators
            confidence = 0.7
            
            return self.detect_threat(
                threat_type='suspicious_activity',
                threat_category='behavior',
                description=f'Suspicious activity detected for user {user_id}',
                severity='medium',
                source_user_id=user_id,
                detection_method='pattern_analysis',
                detection_data={
                    'suspicious_indicators': suspicious_indicators,
                    'total_activities': len(recent_activities),
                    'unique_ips': len(unique_ips),
                    'failed_events': len(failed_events)
                },
                risk_score=risk_score,
                confidence=confidence,
                details=f'Suspicious indicators: {", ".join(suspicious_indicators)}'
            )
        
        return None
    
    def detect_sql_injection_attempt(self, request_data, user_id=None, ip_address=None):
        """Detect SQL injection attempts"""
        # Common SQL injection patterns
        sql_patterns = [
            "union select",
            "select * from",
            "drop table",
            "insert into",
            "update set",
            "delete from",
            "exec(",
            "script>",
            "javascript:",
            "eval(",
            "base64_decode"
        ]
        
        suspicious_patterns = []
        
        # Check request data for suspicious patterns
        for key, value in request_data.items():
            if isinstance(value, str):
                value_lower = value.lower()
                for pattern in sql_patterns:
                    if pattern in value_lower:
                        suspicious_patterns.append(f'{key}: {pattern}')
        
        if suspicious_patterns:
            risk_score = min(len(suspicious_patterns) / 3.0, 1.0)
            confidence = 0.9
            
            return self.detect_threat(
                threat_type='sql_injection',
                threat_category='data',
                description=f'SQL injection attempt detected',
                severity='high',
                source_user_id=user_id,
                source_ip=ip_address,
                detection_method='pattern_matching',
                detection_data={
                    'suspicious_patterns': suspicious_patterns,
                    'request_data_keys': list(request_data.keys())
                },
                risk_score=risk_score,
                confidence=confidence,
                details=f'Suspicious patterns found: {", ".join(suspicious_patterns)}'
            )
        
        return None
    
    def detect_ddos_attack(self, request_rate_threshold=100):
        """Detect potential DDoS attacks"""
        # Get recent security events by IP
        recent_events = SecurityEvent.query.filter(
            SecurityEvent.event_timestamp >= datetime.utcnow() - timedelta(minutes=5)
        ).all()
        
        # Group events by IP address
        ip_counts = {}
        for event in recent_events:
            if event.ip_address:
                ip_counts[event.ip_address] = ip_counts.get(event.ip_address, 0) + 1
        
        # Check for high request rates
        for ip_address, count in ip_counts.items():
            if count >= request_rate_threshold:
                risk_score = min(count / (request_rate_threshold * 2), 1.0)
                confidence = 0.8
                
                return self.detect_threat(
                    threat_type='ddos',
                    threat_category='network',
                    description=f'Potential DDoS attack from {ip_address}',
                    severity='critical',
                    source_ip=ip_address,
                    detection_method='rate_analysis',
                    detection_data={
                        'request_count': count,
                        'time_window': '5 minutes',
                        'threshold': request_rate_threshold
                    },
                    risk_score=risk_score,
                    confidence=confidence,
                    details=f'{count} requests in 5 minutes (threshold: {request_rate_threshold})'
                )
        
        return None
    
    def get_security_dashboard_data(self, hours=24):
        """Get comprehensive security dashboard data"""
        try:
            # Security events summary
            security_summary = SecurityEvent.get_security_summary(hours=hours)
            
            # Threat detection summary
            threat_summary = ThreatDetection.get_threat_summary(hours=hours)
            
            # Audit trail summary
            audit_summary = AuditTrail.get_audit_summary(hours=hours)
            
            # Recent critical events
            critical_events = SecurityEvent.get_events_by_severity('critical', hours=hours, limit=10)
            
            # Active threats
            active_threats = ThreatDetection.get_active_threats(hours=hours)
            
            # Recent failed logins
            failed_logins = SecurityEvent.get_failed_login_attempts(hours=hours, limit=20)
            
            return {
                'security_summary': security_summary,
                'threat_summary': threat_summary,
                'audit_summary': audit_summary,
                'critical_events': [event.to_dict() for event in critical_events],
                'active_threats': [threat.to_dict() for threat in active_threats],
                'failed_logins': [event.to_dict() for event in failed_logins],
                'period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Error getting security dashboard data: {str(e)}")
            return None
    
    def get_user_security_profile(self, user_id, days=30):
        """Get security profile for a specific user"""
        try:
            # User security events
            security_events = SecurityEvent.get_user_events(user_id, days=days, limit=50)
            
            # User audit actions
            audit_actions = AuditTrail.get_user_actions(user_id, days=days, limit=50)
            
            # User threats (as source)
            user_threats = ThreatDetection.query.filter_by(source_user_id=user_id).limit(10).all()
            
            # Calculate security metrics
            total_events = len(security_events)
            failed_events = len([e for e in security_events if not e.success])
            unique_ips = len(set(e.ip_address for e in security_events if e.ip_address))
            
            return {
                'user_id': user_id,
                'total_events': total_events,
                'failed_events': failed_events,
                'success_rate': ((total_events - failed_events) / max(total_events, 1)) * 100,
                'unique_ips': unique_ips,
                'security_events': [event.to_dict() for event in security_events],
                'audit_actions': [action.to_dict() for action in audit_actions],
                'threats': [threat.to_dict() for threat in user_threats],
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting user security profile: {str(e)}")
            return None
    
    def generate_compliance_report(self, compliance_type, period):
        """Generate compliance report"""
        try:
            records = ComplianceRecord.get_records_by_type(compliance_type, limit=100)
            
            # Filter by period if specified
            if period:
                records = [r for r in records if r.compliance_period == period]
            
            summary = ComplianceRecord.get_compliance_summary(compliance_type, period)
            
            return {
                'compliance_type': compliance_type,
                'period': period,
                'summary': summary,
                'records': [record.to_dict() for record in records],
                'total_records': len(records)
            }
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}")
            return None
    
    def cleanup_old_security_data(self, days_to_keep=90):
        """Clean up old security data to manage storage"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Clean up old security events
            old_events = SecurityEvent.query.filter(
                SecurityEvent.event_timestamp < cutoff_date
            ).count()
            
            if old_events > 0:
                SecurityEvent.query.filter(
                    SecurityEvent.event_timestamp < cutoff_date
                ).delete()
                logger.info(f"Cleaned up {old_events} old security events")
            
            # Clean up old audit trails
            old_audits = AuditTrail.query.filter(
                AuditTrail.action_timestamp < cutoff_date
            ).count()
            
            if old_audits > 0:
                AuditTrail.query.filter(
                    AuditTrail.action_timestamp < cutoff_date
                ).delete()
                logger.info(f"Cleaned up {old_audits} old audit trails")
            
            # Clean up resolved threats
            old_threats = ThreatDetection.query.filter(
                and_(
                    ThreatDetection.detected_at < cutoff_date,
                    ThreatDetection.status.in_(['resolved', 'false_positive'])
                )
            ).count()
            
            if old_threats > 0:
                ThreatDetection.query.filter(
                    and_(
                        ThreatDetection.detected_at < cutoff_date,
                        ThreatDetection.status.in_(['resolved', 'false_positive'])
                    )
                ).delete()
                logger.info(f"Cleaned up {old_threats} old resolved threats")
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning up old security data: {str(e)}")
            db.session.rollback()


# Global security service instance
security_service = None

def get_security_service():
    """Get security service instance (lazy initialization)"""
    global security_service
    if security_service is None:
        security_service = SecurityService()
    return security_service


# Decorators for automatic security logging
def log_security_event(event_type, event_category, severity='medium'):
    """Decorator to automatically log security events"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Get request context if available
                from flask import request, g
                user_id = getattr(g, 'user', {}).get('id') if hasattr(g, 'user') else None
                session_id = getattr(g, 'session', {}).get('id') if hasattr(g, 'session') else None
                
                # Log the event
                get_security_service().log_security_event(
                    event_type=event_type,
                    event_category=event_category,
                    severity=severity,
                    description=f"Function {func.__name__} called",
                    user_id=user_id,
                    session_id=session_id,
                    ip_address=request.remote_addr if request else None,
                    user_agent=request.headers.get('User-Agent') if request else None,
                    request_method=request.method if request else None,
                    request_url=request.url if request else None
                )
                
            except Exception as e:
                logger.error(f"Error in security event logging decorator: {str(e)}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_audit_action(action, action_category):
    """Decorator to automatically log audit actions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Get request context if available
                from flask import request, g
                user_id = getattr(g, 'user', {}).get('id') if hasattr(g, 'user') else None
                user_email = getattr(g, 'user', {}).get('email') if hasattr(g, 'user') else None
                username = getattr(g, 'user', {}).get('username') if hasattr(g, 'user') else None
                
                # Log the audit action
                get_security_service().log_audit_action(
                    action=action,
                    action_category=action_category,
                    description=f"Function {func.__name__} executed",
                    user_id=user_id,
                    user_email=user_email,
                    username=username,
                    ip_address=request.remote_addr if request else None,
                    user_agent=request.headers.get('User-Agent') if request else None,
                    request_method=request.method if request else None,
                    request_url=request.url if request else None,
                    module_name=func.__module__,
                    function_name=func.__name__
                )
                
            except Exception as e:
                logger.error(f"Error in audit action logging decorator: {str(e)}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
