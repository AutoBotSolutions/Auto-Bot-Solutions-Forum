"""
Push Notification API Routes

This module provides API endpoints for managing push notifications,
including subscription management, preferences, and testing.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User
import json
import logging
from datetime import datetime

push_bp = Blueprint('push', __name__, url_prefix='/api/push')

logger = logging.getLogger(__name__)

@push_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Subscribe to push notifications"""
    try:
        data = request.get_json()
        if not data or 'subscription' not in data:
            return jsonify({'error': 'Subscription data required'}), 400

        subscription_data = data['subscription']
        
        # Store subscription in user profile or separate table
        # For now, we'll store it in the user's profile as JSON
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Store subscription data
        push_subscriptions = user.push_subscriptions or []
        
        # Check if subscription already exists
        endpoint = subscription_data.get('endpoint')
        existing_index = None
        
        for i, sub in enumerate(push_subscriptions):
            if sub.get('endpoint') == endpoint:
                existing_index = i
                break
        
        subscription_info = {
            'endpoint': endpoint,
            'keys': subscription_data.get('keys', {}),
            'user_agent': data.get('user_agent', ''),
            'created_at': datetime.utcnow().isoformat(),
            'last_used': datetime.utcnow().isoformat()
        }
        
        if existing_index is not None:
            # Update existing subscription
            push_subscriptions[existing_index] = subscription_info
        else:
            # Add new subscription
            push_subscriptions.append(subscription_info)
        
        user.push_subscriptions = push_subscriptions
        db.session.commit()

        logger.info(f"User {current_user.username} subscribed to push notifications")
        
        return jsonify({
            'success': True,
            'message': 'Successfully subscribed to push notifications',
            'subscription_id': endpoint
        }), 200

    except Exception as e:
        logger.error(f"Error subscribing to push notifications: {str(e)}")
        return jsonify({'error': 'Failed to subscribe to push notifications'}), 500

@push_bp.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """Unsubscribe from push notifications"""
    try:
        data = request.get_json()
        if not data or 'subscription' not in data:
            return jsonify({'error': 'Subscription data required'}), 400

        subscription_data = data['subscription']
        endpoint = subscription_data.get('endpoint')
        
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Remove subscription from user's subscriptions
        push_subscriptions = user.push_subscriptions or []
        push_subscriptions = [sub for sub in push_subscriptions if sub.get('endpoint') != endpoint]
        
        user.push_subscriptions = push_subscriptions
        db.session.commit()

        logger.info(f"User {current_user.username} unsubscribed from push notifications")
        
        return jsonify({
            'success': True,
            'message': 'Successfully unsubscribed from push notifications'
        }), 200

    except Exception as e:
        logger.error(f"Error unsubscribing from push notifications: {str(e)}")
        return jsonify({'error': 'Failed to unsubscribe from push notifications'}), 500

@push_bp.route('/status', methods=['GET'])
@login_required
def status():
    """Get push notification subscription status"""
    try:
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        push_subscriptions = user.push_subscriptions or []
        is_subscribed = len(push_subscriptions) > 0

        return jsonify({
            'subscribed': is_subscribed,
            'subscriptions_count': len(push_subscriptions),
            'last_updated': max([sub.get('created_at', '') for sub in push_subscriptions]) if push_subscriptions else None
        }), 200

    except Exception as e:
        logger.error(f"Error getting push notification status: {str(e)}")
        return jsonify({'error': 'Failed to get subscription status'}), 500

@push_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Get or update push notification preferences"""
    try:
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if request.method == 'GET':
            # Get current preferences
            prefs = user.push_preferences or {
                'enabled_types': ['comment', 'message', 'system'],
                'quiet_hours': {
                    'enabled': False,
                    'start': '22:00',
                    'end': '08:00'
                },
                'frequency': 'all',  # all, important, digest
                'browser_notifications': True,
                'mobile_notifications': True
            }
            
            return jsonify(prefs), 200

        else:  # POST
            # Update preferences
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Preferences data required'}), 400

            # Validate preferences
            valid_types = ['comment', 'message', 'system', 'security', 'moderation']
            enabled_types = data.get('enabled_types', [])
            enabled_types = [t for t in enabled_types if t in valid_types]

            quiet_hours = data.get('quiet_hours', {})
            frequency = data.get('frequency', 'all')
            if frequency not in ['all', 'important', 'digest']:
                frequency = 'all'

            preferences = {
                'enabled_types': enabled_types,
                'quiet_hours': {
                    'enabled': quiet_hours.get('enabled', False),
                    'start': quiet_hours.get('start', '22:00'),
                    'end': quiet_hours.get('end', '08:00')
                },
                'frequency': frequency,
                'browser_notifications': data.get('browser_notifications', True),
                'mobile_notifications': data.get('mobile_notifications', True),
                'updated_at': datetime.utcnow().isoformat()
            }

            user.push_preferences = preferences
            db.session.commit()

            logger.info(f"User {current_user.username} updated push notification preferences")
            
            return jsonify({
                'success': True,
                'message': 'Preferences updated successfully',
                'preferences': preferences
            }), 200

    except Exception as e:
        logger.error(f"Error managing push notification preferences: {str(e)}")
        return jsonify({'error': 'Failed to manage preferences'}), 500

@push_bp.route('/test', methods=['POST'])
@login_required
def test_notification():
    """Send a test push notification"""
    try:
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        push_subscriptions = user.push_subscriptions or []
        if not push_subscriptions:
            return jsonify({'error': 'No active push subscription found'}), 400

        # Here you would typically use a push service like Firebase Cloud Messaging
        # For now, we'll simulate the notification
        test_notification = {
            'title': 'Test Notification',
            'content': 'This is a test push notification from AutoBot Solutions Forum',
            'icon': '/static/images/favicon.ico',
            'tag': 'test-notification',
            'data': {
                'url': '/notifications/',
                'type': 'test',
                'timestamp': datetime.utcnow().isoformat()
            }
        }

        # In a real implementation, you would send this to the push service
        # For demonstration, we'll just log it
        logger.info(f"Test push notification for user {current_user.username}: {test_notification}")

        return jsonify({
            'success': True,
            'message': 'Test notification sent successfully',
            'notification': test_notification
        }), 200

    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        return jsonify({'error': 'Failed to send test notification'}), 500

@push_bp.route('/send', methods=['POST'])
def send_push_notification():
    """Send push notification to a user (internal API)"""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data or 'notification' not in data:
            return jsonify({'error': 'User ID and notification data required'}), 400

        user_id = data['user_id']
        notification_data = data['notification']
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        push_subscriptions = user.push_subscriptions or []
        if not push_subscriptions:
            return jsonify({'error': 'User has no push subscriptions'}), 400

        # Check user preferences
        preferences = user.push_preferences or {}
        notification_type = notification_data.get('type', 'system')
        
        enabled_types = preferences.get('enabled_types', ['comment', 'message', 'system'])
        if notification_type not in enabled_types:
            return jsonify({'success': True, 'message': 'Notification type disabled by user preferences'}), 200

        # Check quiet hours
        quiet_hours = preferences.get('quiet_hours', {})
        if quiet_hours.get('enabled', False):
            current_time = datetime.utcnow().time()
            start_time = datetime.strptime(quiet_hours.get('start', '22:00'), '%H:%M').time()
            end_time = datetime.strptime(quiet_hours.get('end', '08:00'), '%H:%M').time()
            
            if start_time <= current_time or current_time <= end_time:
                return jsonify({'success': True, 'message': 'Notification suppressed during quiet hours'}), 200

        # Prepare notification payload
        payload = {
            'title': notification_data.get('title', 'AutoBot Solutions Forum'),
            'content': notification_data.get('content', notification_data.get('body', '')),
            'icon': notification_data.get('icon', '/static/images/favicon.ico'),
            'badge': notification_data.get('badge', '/static/images/badge.png'),
            'tag': notification_data.get('tag', f'notification-{notification_data.get("id", "unknown")}'),
            'data': {
                'url': notification_data.get('link', '/notifications/'),
                'type': notification_type,
                'id': notification_data.get('id'),
                'timestamp': datetime.utcnow().isoformat()
            },
            'actions': notification_data.get('actions', [
                {'action': 'view', 'title': 'View'},
                {'action': 'dismiss', 'title': 'Dismiss'}
            ]),
            'vibrate': [200, 100, 200],
            'requireInteraction': notification_data.get('urgent', False),
            'silent': False
        }

        # In a real implementation, you would send this to a push service
        # For now, we'll simulate by logging
        logger.info(f"Push notification for user {user_id}: {payload}")

        # Update last used timestamp for subscriptions
        for subscription in push_subscriptions:
            subscription['last_used'] = datetime.utcnow().isoformat()
        
        user.push_subscriptions = push_subscriptions
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Push notification sent successfully',
            'sent_to': len(push_subscriptions),
            'notification': payload
        }), 200

    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        return jsonify({'error': 'Failed to send push notification'}), 500

@push_bp.route('/cleanup', methods=['POST'])
def cleanup_subscriptions():
    """Clean up inactive push subscriptions (admin only)"""
    try:
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403

        # Get all users with push subscriptions
        users = User.query.filter(User.push_subscriptions.isnot(None)).all()
        cleaned_count = 0

        for user in users:
            push_subscriptions = user.push_subscriptions or []
            active_subscriptions = []
            
            for subscription in push_subscriptions:
                # Check if subscription is older than 30 days
                last_used = datetime.fromisoformat(subscription.get('last_used', '1970-01-01'))
                if (datetime.utcnow() - last_used).days <= 30:
                    active_subscriptions.append(subscription)
                else:
                    cleaned_count += 1
            
            user.push_subscriptions = active_subscriptions

        db.session.commit()

        logger.info(f"Cleaned up {cleaned_count} inactive push subscriptions")

        return jsonify({
            'success': True,
            'message': f'Cleaned up {cleaned_count} inactive subscriptions',
            'cleaned_count': cleaned_count
        }), 200

    except Exception as e:
        logger.error(f"Error cleaning up push subscriptions: {str(e)}")
        return jsonify({'error': 'Failed to clean up subscriptions'}), 500
