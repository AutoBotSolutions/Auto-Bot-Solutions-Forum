"""
WebSocket Event Handlers for Real-time Features

This module contains all the SocketIO event handlers for real-time features including:
- Connection and disconnection events
- Comment notifications
- Vote updates
- Typing indicators
- User presence
"""

from flask import request
from flask_socketio import emit, join_room, leave_room, SocketIO
from flask_login import current_user, login_required
from .service import WebSocketService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Global WebSocket service instance
websocket_service: WebSocketService = None

def register_socketio_events(socketio: SocketIO, ws_service: WebSocketService):
    """Register all SocketIO event handlers"""
    global websocket_service
    websocket_service = ws_service
    
    # Connection events
    socketio.on('connect', handle_connect)
    socketio.on('disconnect', handle_disconnect)
    
    # Comment events
    socketio.on('join_post', handle_join_post)
    socketio.on('leave_post', handle_leave_post)
    socketio.on('new_comment', handle_new_comment)
    
    # Vote events
    socketio.on('vote_cast', handle_vote_cast)
    
    # Typing events
    socketio.on('start_typing', handle_start_typing)
    socketio.on('stop_typing', handle_stop_typing)
    
    # Presence events
    socketio.on('update_presence', handle_update_presence)
    socketio.on('get_online_users', handle_get_online_users)
    
    # Notification events
    socketio.on('mark_notification_read', handle_mark_notification_read)
    socketio.on('subscribe_notifications', handle_subscribe_notifications)
    socketio.on('mark_all_notifications_read', handle_mark_all_notifications_read)
    socketio.on('get_unread_count', handle_get_unread_count)
    socketio.on('get_recent_notifications', handle_get_recent_notifications)
    
    logger.info("WebSocket event handlers registered")

def handle_connect():
    """Handle client connection"""
    try:
        if current_user.is_authenticated:
            # Add user to connected users
            websocket_service.add_connected_user(
                request.sid, 
                current_user.id, 
                current_user.username
            )
            
            # Send initial data to user
            emit('connection_established', {
                'status': 'connected',
                'user_id': current_user.id,
                'username': current_user.username,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Send online users list
            online_users = websocket_service.get_online_users()
            emit('online_users', {
                'users': online_users,
                'count': len(online_users)
            })
            
            logger.info(f"WebSocket connection established for user {current_user.username}")
        else:
            # Anonymous connection - limited functionality
            emit('connection_established', {
                'status': 'connected',
                'user_id': None,
                'username': 'Anonymous',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info("Anonymous WebSocket connection established")
            
    except Exception as e:
        logger.error(f"Error in handle_connect: {str(e)}")
        emit('error', {'message': 'Connection failed'})

def handle_disconnect():
    """Handle client disconnection"""
    try:
        websocket_service.remove_connected_user(request.sid)
        logger.info(f"WebSocket disconnected: {request.sid}")
    except Exception as e:
        logger.error(f"Error in handle_disconnect: {str(e)}")

def handle_join_post(data):
    """Handle user joining a post room"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        post_id = data.get('post_id')
        if not post_id:
            emit('error', {'message': 'Post ID required'})
            return
        
        # Join post room
        websocket_service.join_post_room(current_user.id, post_id)
        
        # Send current typing users
        typing_users = websocket_service.get_typing_users(post_id)
        emit('typing_users', {
            'post_id': post_id,
            'typing_users': typing_users
        })
        
        emit('joined_post', {
            'post_id': post_id,
            'status': 'success'
        })
        
        logger.info(f"User {current_user.username} joined post {post_id}")
        
    except Exception as e:
        logger.error(f"Error in handle_join_post: {str(e)}")
        emit('error', {'message': 'Failed to join post'})

def handle_leave_post(data):
    """Handle user leaving a post room"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        post_id = data.get('post_id')
        if not post_id:
            emit('error', {'message': 'Post ID required'})
            return
        
        # Leave post room
        websocket_service.leave_post_room(current_user.id, post_id)
        
        # Remove typing indicator
        websocket_service.remove_user_typing(current_user.id, post_id)
        
        emit('left_post', {
            'post_id': post_id,
            'status': 'success'
        })
        
        logger.info(f"User {current_user.username} left post {post_id}")
        
    except Exception as e:
        logger.error(f"Error in handle_leave_post: {str(e)}")
        emit('error', {'message': 'Failed to leave post'})

def handle_new_comment(data):
    """Handle new comment notification"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        post_id = data.get('post_id')
        comment_content = data.get('content')
        
        if not post_id or not comment_content:
            emit('error', {'message': 'Post ID and content required'})
            return
        
        # Create comment data for broadcast
        comment_data = {
            'id': data.get('comment_id'),
            'post_id': post_id,
            'content': comment_content,
            'author': {
                'id': current_user.id,
                'username': current_user.username
            },
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Broadcast to post room
        websocket_service.broadcast_new_comment(post_id, comment_data)
        
        emit('comment_sent', {
            'status': 'success',
            'comment_id': comment_data['id']
        })
        
        logger.info(f"New comment broadcasted for post {post_id} by {current_user.username}")
        
    except Exception as e:
        logger.error(f"Error in handle_new_comment: {str(e)}")
        emit('error', {'message': 'Failed to send comment'})

def handle_vote_cast(data):
    """Handle vote cast notification"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        content_type = data.get('content_type')  # 'post' or 'comment'
        content_id = data.get('content_id')
        vote_type = data.get('vote_type')  # 'up' or 'down'
        
        if not all([content_type, content_id, vote_type]):
            emit('error', {'message': 'Content type, content ID, and vote type required'})
            return
        
        # Create vote data for broadcast
        vote_data = {
            'vote_type': vote_type,
            'user_id': current_user.id,
            'username': current_user.username,
            'post_id': data.get('post_id')  # For comments
        }
        
        # Broadcast vote update
        websocket_service.broadcast_vote_update(content_type, content_id, vote_data)
        
        emit('vote_recorded', {
            'status': 'success',
            'content_type': content_type,
            'content_id': content_id,
            'vote_type': vote_type
        })
        
        logger.info(f"Vote broadcasted for {content_type} {content_id} by {current_user.username}")
        
    except Exception as e:
        logger.error(f"Error in handle_vote_cast: {str(e)}")
        emit('error', {'message': 'Failed to record vote'})

def handle_start_typing(data):
    """Handle user starting to type"""
    try:
        if not current_user.is_authenticated:
            return  # Silently ignore for anonymous users
        
        post_id = data.get('post_id')
        if not post_id:
            return  # Silently ignore invalid data
        
        # Set user as typing
        websocket_service.set_user_typing(
            current_user.id, 
            current_user.username, 
            post_id
        )
        
        logger.debug(f"User {current_user.username} started typing in post {post_id}")
        
    except Exception as e:
        logger.error(f"Error in handle_start_typing: {str(e)}")

def handle_stop_typing(data):
    """Handle user stopping typing"""
    try:
        if not current_user.is_authenticated:
            return  # Silently ignore for anonymous users
        
        post_id = data.get('post_id')
        if not post_id:
            return  # Silently ignore invalid data
        
        # Remove typing indicator
        websocket_service.remove_user_typing(current_user.id, post_id)
        
        logger.debug(f"User {current_user.username} stopped typing in post {post_id}")
        
    except Exception as e:
        logger.error(f"Error in handle_stop_typing: {str(e)}")

def handle_update_presence():
    """Handle presence update (keep-alive)"""
    try:
        if current_user.is_authenticated:
            websocket_service.update_user_activity(request.sid)
            emit('presence_updated', {
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error in handle_update_presence: {str(e)}")

def handle_get_online_users():
    """Handle request for online users list"""
    try:
        online_users = websocket_service.get_online_users()
        emit('online_users', {
            'users': online_users,
            'count': len(online_users),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in handle_get_online_users: {str(e)}")
        emit('error', {'message': 'Failed to get online users'})

def handle_mark_notification_read(data):
    """Handle marking notification as read"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        notification_id = data.get('notification_id')
        if not notification_id:
            emit('error', {'message': 'Notification ID required'})
            return
        
        # Update the database
        from app.models import Notification
        from app import db
        
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=current_user.id
        ).first()
        
        if notification:
            notification.is_read = True
            db.session.commit()
            
            # Get updated unread count
            unread_count = Notification.query.filter_by(
                user_id=current_user.id, 
                is_read=False
            ).count()
            
            # Emit success response
            emit('notification_marked_read', {
                'notification_id': notification_id,
                'unread_count': unread_count,
                'status': 'success'
            })
            
            logger.info(f"User {current_user.username} marked notification {notification_id} as read")
        else:
            emit('error', {'message': 'Notification not found'})
        
    except Exception as e:
        logger.error(f"Error in handle_mark_notification_read: {str(e)}")
        emit('error', {'message': 'Failed to mark notification as read'})

def handle_subscribe_notifications(data):
    """Handle notification subscription"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        # Join user's personal notification room
        from flask_socketio import join_room
        join_room(f"user_{current_user.id}")
        
        # Send current unread count
        from app.models import Notification
        unread_count = Notification.query.filter_by(
            user_id=current_user.id, 
            is_read=False
        ).count()
        
        emit('notification_subscribed', {
            'user_id': current_user.id,
            'unread_count': unread_count,
            'status': 'subscribed'
        })
        
        # Send recent notifications
        recent_notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(5).all()
        
        emit('recent_notifications', {
            'notifications': [{
                'id': n.id,
                'content': n.content,
                'link': n.link,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat()
            } for n in recent_notifications]
        })
        
        logger.info(f"User {current_user.username} subscribed to notifications")
        
    except Exception as e:
        logger.error(f"Error in handle_subscribe_notifications: {str(e)}")
        emit('error', {'message': 'Failed to subscribe to notifications'})

def handle_mark_all_notifications_read(data):
    """Handle marking all notifications as read"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        from app.models import Notification
        from app import db
        
        # Update all unread notifications
        count = Notification.query.filter_by(
            user_id=current_user.id, 
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        
        emit('all_notifications_marked_read', {
            'count': count,
            'unread_count': 0,
            'status': 'success'
        })
        
        logger.info(f"User {current_user.username} marked {count} notifications as read")
        
    except Exception as e:
        logger.error(f"Error in handle_mark_all_notifications_read: {str(e)}")
        emit('error', {'message': 'Failed to mark all notifications as read'})

def handle_get_unread_count(data):
    """Handle getting unread count"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        from app.models import Notification
        unread_count = Notification.query.filter_by(
            user_id=current_user.id, 
            is_read=False
        ).count()
        
        emit('unread_count', {
            'unread_count': unread_count
        })
        
    except Exception as e:
        logger.error(f"Error in handle_get_unread_count: {str(e)}")
        emit('error', {'message': 'Failed to get unread count'})

def handle_get_recent_notifications(data):
    """Handle getting recent notifications"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        limit = data.get('limit', 10)
        
        from app.models import Notification
        recent_notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(limit).all()
        
        emit('recent_notifications', {
            'notifications': [{
                'id': n.id,
                'content': n.content,
                'link': n.link,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat()
            } for n in recent_notifications]
        })
        
    except Exception as e:
        logger.error(f"Error in handle_get_recent_notifications: {str(e)}")
        emit('error', {'message': 'Failed to get recent notifications'})

# Utility functions for external use
def broadcast_new_comment(post_id: int, comment_data: dict):
    """Broadcast new comment to post room (external function)"""
    if websocket_service:
        websocket_service.broadcast_new_comment(post_id, comment_data)

def broadcast_vote_update(content_type: str, content_id: int, vote_data: dict):
    """Broadcast vote update (external function)"""
    if websocket_service:
        websocket_service.broadcast_vote_update(content_type, content_id, vote_data)

def send_user_notification(user_id: int, notification_data: dict):
    """Send notification to specific user (external function)"""
    if websocket_service:
        websocket_service.send_user_notification(user_id, notification_data)

def emit_to_admins(event: str, data: dict):
    """Emit event to all admin users"""
    if websocket_service:
        websocket_service.emit_to_admins(event, data)

def emit_to_moderators(event: str, data: dict):
    """Emit event to all moderator users"""
    if websocket_service:
        websocket_service.emit_to_moderators(event, data)

def emit_to_user(user_id: int, event: str, data: dict):
    """Emit event to specific user"""
    if websocket_service:
        websocket_service.emit_to_user(user_id, event, data)

def broadcast_system_message(message: str, message_type: str = 'info'):
    """Broadcast system message to all users (external function)"""
    if websocket_service:
        websocket_service.broadcast_system_message(message, message_type)

# ... (rest of the code remains the same)
