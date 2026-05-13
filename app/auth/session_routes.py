"""
Session Management Routes

Routes for session management, analytics, and security monitoring
for the Auto Bot Solutions Forum.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import UserSession, SessionAnalytics, SecurityEvent
from app.auth.session_service import session_manager
from app.auth.session_forms import SessionManagementForm, RevokeSessionForm, RevokeAllSessionsForm, SessionPreferencesForm, SecuritySettingsForm, SessionAnalyticsForm, SecurityEventForm, SessionExportForm
from app.auth.decorators import admin_required
import logging

logger = logging.getLogger(__name__)

session_bp = Blueprint('session', __name__, url_prefix='/auth/sessions')

@session_bp.route('/')
@login_required
def manage_sessions():
    """Manage user sessions"""
    sessions = current_user.get_active_sessions()
    analytics = current_user.get_session_analytics()
    
    return render_template('auth/sessions/manage.html', 
                         sessions=sessions, 
                         analytics=analytics)

@session_bp.route('/revoke/<session_id>', methods=['POST'])
@login_required
def revoke_session(session_id):
    """Revoke specific session"""
    form = RevokeSessionForm()
    form.session_id.data = session_id
    
    if form.validate_on_submit():
        success = current_user.revoke_session(session_id)
        if success:
            flash('Session revoked successfully.', 'success')
        else:
            flash('Session not found or already revoked.', 'error')
    else:
        flash('Invalid request.', 'error')
    
    return redirect(url_for('session.manage_sessions'))

@session_bp.route('/revoke-all', methods=['GET', 'POST'])
@login_required
def revoke_all_sessions():
    """Revoke all user sessions"""
    form = RevokeAllSessionsForm()
    
    if form.validate_on_submit():
        except_current = None
        if form.current_session_only.data:
            except_current = session.sid if 'sid' in session else None
        
        revoked_count = session_manager.revoke_all_user_sessions(current_user.id, except_current)
        
        if revoked_count > 0:
            flash(f'Revoked {revoked_count} session(s).', 'success')
            
            # Log security event
            current_user.add_security_event(
                event_type='all_sessions_revoked',
                severity='info',
                description=f"User revoked all sessions: {form.reason.data or 'No reason provided'}",
                metadata={
                    'revoked_count': revoked_count,
                    'except_current': except_current is not None
                }
            )
        else:
            flash('No active sessions to revoke.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/sessions/revoke_all.html', form=form)

@session_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def session_preferences():
    """Manage session preferences"""
    form = SessionPreferencesForm()
    
    if form.validate_on_submit():
        # Store preferences in user metadata or separate table
        # For now, we'll store in session
        preferences = {
            'auto_revoke_inactive': form.auto_revoke_inactive.data,
            'inactive_timeout': form.inactive_timeout.data,
            'max_concurrent_sessions': form.max_concurrent_sessions.data,
            'require_device_verification': form.require_device_verification.data,
            'session_notifications': form.session_notifications.data
        }
        
        # Store in session (in production, store in database)
        session['session_preferences'] = preferences
        
        flash('Session preferences updated successfully.', 'success')
        return redirect(url_for('session.manage_sessions'))
    
    # Load current preferences
    preferences = session.get('session_preferences', {})
    form.auto_revoke_inactive.data = preferences.get('auto_revoke_inactive', True)
    form.inactive_timeout.data = preferences.get('inactive_timeout', 30)
    form.max_concurrent_sessions.data = preferences.get('max_concurrent_sessions', 3)
    form.require_device_verification.data = preferences.get('require_device_verification', False)
    form.session_notifications.data = preferences.get('session_notifications', True)
    
    return render_template('auth/sessions/preferences.html', form=form)

@session_bp.route('/analytics')
@login_required
def session_analytics():
    """View session analytics"""
    form = SessionAnalyticsForm()
    
    # Get analytics data
    analytics = session_manager.get_user_session_analytics(current_user.id)
    security_events = current_user.get_security_events(
        event_type=form.event_type.data if form.event_type.data else None,
        severity=form.severity.data if form.severity.data else None,
        limit=50
    )
    
    return render_template('auth/sessions/analytics.html', 
                         analytics=analytics, 
                         security_events=security_events,
                         form=form)

@session_bp.route('/security', methods=['GET', 'POST'])
@login_required
def security_settings():
    """Manage security settings"""
    form = SecuritySettingsForm()
    
    if form.validate_on_submit():
        # Store security settings
        settings = {
            'two_factor_required': form.two_factor_required.data,
            'ip_whitelist_enabled': form.ip_whitelist_enabled.data,
            'ip_whitelist': form.ip_whitelist.data,
            'email_alerts': form.email_alerts.data,
            'session_monitoring': form.session_monitoring.data,
            'suspicious_activity_detection': form.suspicious_activity_detection.data
        }
        
        # Store in user metadata (in production, store in database)
        session['security_settings'] = settings
        
        # Log security event
        current_user.add_security_event(
            event_type='security_settings_updated',
            severity='info',
            description='User updated security settings',
            metadata=settings
        )
        
        flash('Security settings updated successfully.', 'success')
        return redirect(url_for('session.security_settings'))
    
    # Load current settings
    settings = session.get('security_settings', {})
    form.two_factor_required.data = settings.get('two_factor_required', False)
    form.ip_whitelist_enabled.data = settings.get('ip_whitelist_enabled', False)
    form.ip_whitelist.data = settings.get('ip_whitelist', '')
    form.email_alerts.data = settings.get('email_alerts', True)
    form.session_monitoring.data = settings.get('session_monitoring', True)
    form.suspicious_activity_detection.data = settings.get('suspicious_activity_detection', True)
    
    return render_template('auth/sessions/security.html', form=form)

@session_bp.route('/export', methods=['GET', 'POST'])
@login_required
def export_sessions():
    """Export session data"""
    form = SessionExportForm()
    
    if form.validate_on_submit():
        # Get session data based on date range
        sessions = current_user.sessions
        
        # Filter by date range
        date_range = form.date_range.data
        if date_range == 'week':
            from datetime import timedelta
            cutoff = datetime.utcnow() - timedelta(days=7)
            sessions = [s for s in sessions if s.created_at >= cutoff]
        elif date_range == 'month':
            from datetime import timedelta
            cutoff = datetime.utcnow() - timedelta(days=30)
            sessions = [s for s in sessions if s.created_at >= cutoff]
        elif date_range == 'quarter':
            from datetime import timedelta
            cutoff = datetime.utcnow() - timedelta(days=90)
            sessions = [s for s in sessions if s.created_at >= cutoff]
        elif date_range == 'year':
            from datetime import timedelta
            cutoff = datetime.utcnow() - timedelta(days=365)
            sessions = [s for s in sessions if s.created_at >= cutoff]
        
        # Format data based on export format
        export_format = form.format.data
        include_sensitive = form.include_sensitive.data
        
        if export_format == 'json':
            data = []
            for session in sessions:
                session_data = {
                    'session_id': session.session_id,
                    'created_at': session.created_at.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'expires_at': session.expires_at.isoformat(),
                    'is_active': session.is_active,
                    'is_persistent': session.is_persistent
                }
                
                if include_sensitive:
                    session_data.update({
                        'ip_address': session.ip_address,
                        'user_agent': session.user_agent,
                        'device_fingerprint': session.device_fingerprint,
                        'location': session.location
                    })
                
                data.append(session_data)
            
            return jsonify(data), 200, {'Content-Disposition': 'attachment; filename=sessions.json'}
        
        elif export_format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            headers = ['Session ID', 'Created At', 'Last Activity', 'Expires At', 'Active', 'Persistent']
            if include_sensitive:
                headers.extend(['IP Address', 'User Agent', 'Device Fingerprint', 'Location'])
            
            writer.writerow(headers)
            
            # Data rows
            for session in sessions:
                row = [
                    session.session_id,
                    session.created_at.isoformat(),
                    session.last_activity.isoformat(),
                    session.expires_at.isoformat(),
                    session.is_active,
                    session.is_persistent
                ]
                
                if include_sensitive:
                    row.extend([
                        session.ip_address or '',
                        session.user_agent or '',
                        session.device_fingerprint or '',
                        session.location or ''
                    ])
                
                writer.writerow(row)
            
            output.seek(0)
            return output.getvalue(), 200, {'Content-Disposition': 'attachment; filename=sessions.csv'}
        
        # PDF export would require additional libraries
        flash('PDF export not yet implemented.', 'warning')
        return redirect(url_for('session.export_sessions'))
    
    return render_template('auth/sessions/export.html', form=form)

@session_bp.route('/api/session-status')
@login_required
def api_session_status():
    """API endpoint for session status"""
    sessions = current_user.get_active_sessions()
    
    return jsonify({
        'total_sessions': len(sessions),
        'active_sessions': len([s for s in sessions if s.is_active]),
        'persistent_sessions': len([s for s in sessions if s.is_persistent]),
        'last_activity': max(s.last_activity.isoformat() for s in sessions) if sessions else None
    })

@session_bp.route('/api/security-events')
@login_required
def api_security_events():
    """API endpoint for security events"""
    events = current_user.get_security_events(limit=20)
    
    return jsonify({
        'events': [
            {
                'id': event.id,
                'event_type': event.event_type,
                'severity': event.severity,
                'description': event.description,
                'ip_address': event.ip_address,
                'created_at': event.created_at.isoformat(),
                'metadata': event.get_metadata()
            }
            for event in events
        ]
    })

# Admin routes
@session_bp.route('/admin/system-analytics')
@admin_required
def admin_system_analytics():
    """View system-wide session analytics"""
    # Get today's analytics
    analytics = session_manager.get_session_analytics()
    
    # Get historical data
    from datetime import timedelta
    historical_data = []
    for i in range(7):
        date = datetime.utcnow().date() - timedelta(days=i)
        daily_analytics = session_manager.get_session_analytics(date)
        historical_data.append({
            'date': date.isoformat(),
            'total_sessions': daily_analytics.total_sessions,
            'active_sessions': daily_analytics.active_sessions,
            'unique_users': daily_analytics.unique_users
        })
    
    return render_template('auth/sessions/admin/analytics.html', 
                         analytics=analytics, 
                         historical_data=historical_data)

@session_bp.route('/admin/cleanup-expired')
@admin_required
def admin_cleanup_expired():
    """Clean up expired sessions"""
    cleaned_count = session_manager.cleanup_expired_sessions()
    flash(f'Cleaned up {cleaned_count} expired sessions.', 'success')
    return redirect(url_for('session.admin_system_analytics'))

@session_bp.route('/admin/add-security-event', methods=['GET', 'POST'])
@admin_required
def admin_add_security_event():
    """Add security event (admin use)"""
    form = SecurityEventForm()
    
    if form.validate_on_submit():
        # Find user if specified
        user_id = request.args.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                user.add_security_event(
                    event_type=form.event_type.data,
                    severity=form.severity.data,
                    description=form.description.data,
                    ip_address=form.ip_address.data,
                    user_agent=form.user_agent.data
                )
                flash('Security event added successfully.', 'success')
                return redirect(url_for('session.admin_system_analytics'))
            else:
                flash('User not found.', 'error')
        else:
            flash('User ID required.', 'error')
    
    return render_template('auth/sessions/admin/add_event.html', form=form)

# Error handlers
@session_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    flash('Page not found.', 'error')
    return redirect(url_for('main.index'))

@session_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error in session routes: {str(error)}")
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('main.index'))
