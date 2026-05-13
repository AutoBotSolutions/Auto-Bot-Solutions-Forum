from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app import db, socketio
from app.models import Notification
import json
import logging

logger = logging.getLogger(__name__)

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('notification/notifications.html', notifications=notifications, unread_count=unread_count)

@notification_bp.route('/<int:notification_id>/read')
@login_required
def mark_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
        if notification.link:
            return redirect(notification.link)
    return redirect(url_for('notification.notifications'))

@notification_bp.route('/read_all')
@login_required
def mark_all_read():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    # Broadcast real-time update
    socketio.emit('all_notifications_marked_read', {
        'count': count,
        'unread_count': 0,
        'status': 'success'
    }, room=f"user_{current_user.id}")
    
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notification.notifications'))

def create_notification(user_id, content, link=None, notification_type='system', send_email=True):
    """Create a notification with real-time broadcasting, analytics tracking, and email delivery"""
    notification = Notification(
        user_id=user_id,
        content=content,
        link=link
    )
    db.session.add(notification)
    db.session.commit()
    
    # Track notification creation for analytics
    from app.analytics.notification_analytics import notification_analytics
    notification_analytics.track_notification_delivery(
        notification_id=notification.id,
        delivery_type='websocket',
        status='sent',
        recipient_id=user_id,
        metadata={
            'content': content,
            'link': link,
            'type': notification_type,
            'created_at': notification.created_at.isoformat()
        }
    )
    
    # Broadcast real-time notification
    notification_data = {
        'id': notification.id,
        'content': notification.content,
        'link': notification.link,
        'is_read': notification.is_read,
        'created_at': notification.created_at.isoformat(),
        'type': notification_type
    }
    
    socketio.emit('notification', notification_data, room=f"user_{user_id}")
    
    # Update unread count
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    socketio.emit('unread_count', {'unread_count': unread_count}, room=f"user_{user_id}")
    
    # Track WebSocket delivery
    notification_analytics.track_notification_delivery(
        notification_id=notification.id,
        delivery_type='websocket',
        status='delivered',
        recipient_id=user_id,
        metadata={'delivered_at': datetime.utcnow().isoformat()}
    )
    
    # Send email notification if enabled
    if send_email:
        try:
            from app.email.notification_service import email_notification_service
            from threading import Thread
            
            # Send email in background thread to avoid blocking
            email_thread = Thread(
                target=email_notification_service.send_notification_email,
                args=(user_id, notification.id, f'notification_{notification_type}')
            )
            email_thread.daemon = True
            email_thread.start()
            
        except Exception as e:
            logger.error(f"Error queuing email notification: {str(e)}")
    
    return notification

@notification_bp.route('/create', methods=['POST'])
@login_required
def create_notification_route():
    """Create a new notification (for testing/admin use)"""
    content = request.form.get('content')
    user_id = request.form.get('user_id', type=int)
    link = request.form.get('link')
    
    if not content or not user_id:
        flash('Content and user ID are required.', 'error')
        return redirect(url_for('notification.notifications'))
    
    try:
        create_notification(user_id, content, link)
        flash('Notification created successfully.', 'success')
    except Exception as e:
        flash(f'Error creating notification: {str(e)}', 'error')
    
    return redirect(url_for('notification.notifications'))
