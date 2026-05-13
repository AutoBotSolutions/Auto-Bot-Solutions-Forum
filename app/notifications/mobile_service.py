"""
Mobile App Notifications Service

This module provides mobile app notification support including
push notifications for iOS and Android devices, device management,
and mobile-specific features.
"""

from datetime import datetime, timedelta
from flask import current_app
from typing import Dict, List, Optional, Tuple
import json
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from app.models import User


class MobileNotificationService:
    """Service for mobile app notifications"""
    
    def __init__(self):
        self.supported_platforms = {
            'ios': 'Apple iOS',
            'android': 'Google Android',
            'huawei': 'Huawei HMS',
            'web': 'Web Push'
        }
        
        # Push notification services
        self.push_services = {
            'ios': 'APNS (Apple Push Notification Service)',
            'android': 'FCM (Firebase Cloud Messaging)',
            'huawei': 'HMS (Huawei Mobile Services)',
            'web': 'Web Push API'
        }
        
        # Mobile notification types
        self.mobile_notification_types = {
            'forum_activity': 'Forum Activity',
            'messages': 'Messages',
            'moderation': 'Moderation',
            'security': 'Security',
            'system': 'System Updates',
            'marketing': 'Marketing (opt-in)'
        }
        
        # Device registration status
        self.device_status = {
            'active': 'Device is active and receiving notifications',
            'inactive': 'Device is inactive (no recent activity)',
            'expired': 'Device token has expired',
            'revoked': 'User has revoked notifications'
        }
    
    def register_device(self, user_id: int, device_info: Dict) -> Dict:
        """Register a mobile device for push notifications"""
        try:
            # Validate device information
            required_fields = ['platform', 'device_token', 'device_id']
            for field in required_fields:
                if field not in device_info:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }
            
            platform = device_info['platform']
            if platform not in self.supported_platforms:
                return {
                    'success': False,
                    'error': f'Unsupported platform: {platform}'
                }
            
            # Create device registration record
            device_registration = {
                'user_id': user_id,
                'platform': platform,
                'device_token': device_info['device_token'],
                'device_id': device_info['device_id'],
                'app_version': device_info.get('app_version', '1.0.0'),
                'os_version': device_info.get('os_version'),
                'device_model': device_info.get('device_model'),
                'push_enabled': device_info.get('push_enabled', True),
                'notification_types': device_info.get('notification_types', ['forum_activity', 'messages']),
                'quiet_hours': device_info.get('quiet_hours', {}),
                'created_at': datetime.utcnow().isoformat(),
                'last_active': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            # Store device registration (this would typically save to database)
            registration_id = f"device_{user_id}_{device_info['device_id']}_{datetime.utcnow().timestamp()}"
            device_registration['registration_id'] = registration_id
            
            # Test push notification to verify registration
            if device_info.get('send_test_notification', False):
                test_result = self.send_test_notification(device_registration)
                device_registration['test_result'] = test_result
            
            return {
                'success': True,
                'registration_id': registration_id,
                'device_info': device_registration
            }
            
        except Exception as e:
            current_app.logger.error(f"Device registration error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def unregister_device(self, user_id: int, registration_id: str) -> Dict:
        """Unregister a mobile device"""
        try:
            # This would typically remove from database
            # For now, return success response
            return {
                'success': True,
                'message': f'Device {registration_id} unregistered successfully'
            }
        except Exception as e:
            current_app.logger.error(f"Device unregistration error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_push_notification(self, user_id: int, notification_data: Dict, 
                            target_devices: List[str] = None) -> Dict:
        """Send push notification to mobile devices"""
        try:
            # Get user's registered devices
            user_devices = self._get_user_devices(user_id)
            
            if not user_devices:
                return {
                    'success': False,
                    'error': 'No registered devices found'
                }
            
            # Filter devices if target_devices specified
            if target_devices:
                user_devices = [d for d in user_devices if d['registration_id'] in target_devices]
            
            if not user_devices:
                return {
                    'success': False,
                    'error': 'No matching devices found'
                }
            
            # Prepare notification payload
            payload = self._prepare_mobile_payload(notification_data)
            
            # Send to each platform
            results = {}
            total_sent = 0
            total_failed = 0
            
            for device in user_devices:
                platform = device['platform']
                
                if platform == 'ios':
                    result = self._send_ios_notification(device, payload)
                elif platform == 'android':
                    result = self._send_android_notification(device, payload)
                elif platform == 'huawei':
                    result = self._send_huawei_notification(device, payload)
                elif platform == 'web':
                    result = self._send_web_notification(device, payload)
                else:
                    result = {'success': False, 'error': f'Unsupported platform: {platform}'}
                
                results[device['registration_id']] = result
                
                if result['success']:
                    total_sent += 1
                else:
                    total_failed += 1
            
            return {
                'success': total_sent > 0,
                'total_devices': len(user_devices),
                'total_sent': total_sent,
                'total_failed': total_failed,
                'results': results
            }
            
        except Exception as e:
            current_app.logger.error(f"Push notification error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _prepare_mobile_payload(self, notification_data: Dict) -> Dict:
        """Prepare notification payload for mobile platforms"""
        
        payload = {
            'title': notification_data.get('title', 'New Notification'),
            'body': notification_data.get('message', notification_data.get('content', '')),
            'data': {
                'notification_id': notification_data.get('id'),
                'type': notification_data.get('type', 'system'),
                'link': notification_data.get('link'),
                'priority': notification_data.get('priority', 'normal'),
                'timestamp': datetime.utcnow().isoformat()
            },
            'sound': notification_data.get('sound', 'default'),
            'badge': notification_data.get('badge', 1),
            'click_action': notification_data.get('link', 'app://notifications'),
            'icon': notification_data.get('icon', 'notification_icon'),
            'color': notification_data.get('color', '#007bff')
        }
        
        # Platform-specific adjustments
        if notification_data.get('platform') == 'ios':
            payload.update({
                'mutable_content': True,
                'content_available': notification_data.get('content_available', False),
                'thread_id': notification_data.get('thread_id'),
                'category': notification_data.get('category')
            })
        elif notification_data.get('platform') == 'android':
            payload.update({
                'android_channel_id': notification_data.get('channel_id', 'default'),
                'notification_count': notification_data.get('notification_count'),
                'image': notification_data.get('image'),
                'large_icon': notification_data.get('large_icon'),
                'big_text': notification_data.get('big_text'),
                'style': notification_data.get('style', 'default')
            })
        
        return payload
    
    def _send_ios_notification(self, device: Dict, payload: Dict) -> Dict:
        """Send notification to iOS device via APNS"""
        try:
            # This would integrate with Apple Push Notification Service
            # For now, return simulated success
            
            # In production, you would:
            # 1. Create APNS payload
            # 2. Send to Apple's APNS servers
            # 3. Handle response and errors
            
            apns_payload = {
                'aps': {
                    'alert': {
                        'title': payload['title'],
                        'body': payload['body']
                    },
                    'badge': payload['badge'],
                    'sound': payload['sound'],
                    'mutable-content': payload.get('mutable_content', False)
                },
                'data': payload['data']
            }
            
            # Simulate successful delivery
            return {
                'success': True,
                'platform': 'ios',
                'device_id': device['device_id'],
                'message_id': f"ios_{datetime.utcnow().timestamp()}",
                'status': 'delivered'
            }
            
        except Exception as e:
            current_app.logger.error(f"iOS notification error: {str(e)}")
            return {
                'success': False,
                'platform': 'ios',
                'error': str(e)
            }
    
    def _send_android_notification(self, device: Dict, payload: Dict) -> Dict:
        """Send notification to Android device via FCM"""
        try:
            # This would integrate with Firebase Cloud Messaging
            # For now, return simulated success
            
            fcm_payload = {
                'to': device['device_token'],
                'notification': {
                    'title': payload['title'],
                    'body': payload['body'],
                    'icon': payload['icon'],
                    'color': payload['color'],
                    'sound': payload['sound'],
                    'click_action': payload['click_action']
                },
                'data': payload['data'],
                'android': {
                    'priority': 'high' if payload.get('priority') == 'urgent' else 'normal',
                    'notification': {
                        'channel_id': payload.get('android_channel_id', 'default'),
                        'default_sound': True,
                        'default_vibrate': True
                    }
                }
            }
            
            # Simulate successful delivery
            return {
                'success': True,
                'platform': 'android',
                'device_id': device['device_id'],
                'message_id': f"android_{datetime.utcnow().timestamp()}",
                'status': 'delivered'
            }
            
        except Exception as e:
            current_app.logger.error(f"Android notification error: {str(e)}")
            return {
                'success': False,
                'platform': 'android',
                'error': str(e)
            }
    
    def _send_huawei_notification(self, device: Dict, payload: Dict) -> Dict:
        """Send notification to Huawei device via HMS"""
        try:
            # This would integrate with Huawei Mobile Services
            # For now, return simulated success
            
            hms_payload = {
                'message': {
                    'notification': {
                        'title': payload['title'],
                        'body': payload['body']
                    },
                    'android': {
                        'notification': {
                            'click_action': {
                                'type': 1,
                                'intent': payload['click_action']
                            }
                        },
                        'data': payload['data']
                    },
                    'token': [device['device_token']]
                }
            }
            
            # Simulate successful delivery
            return {
                'success': True,
                'platform': 'huawei',
                'device_id': device['device_id'],
                'message_id': f"huawei_{datetime.utcnow().timestamp()}",
                'status': 'delivered'
            }
            
        except Exception as e:
            current_app.logger.error(f"Huawei notification error: {str(e)}")
            return {
                'success': False,
                'platform': 'huawei',
                'error': str(e)
            }
    
    def _send_web_notification(self, device: Dict, payload: Dict) -> Dict:
        """Send web push notification"""
        try:
            # This would integrate with Web Push API
            # For now, return simulated success
            
            web_payload = {
                'title': payload['title'],
                'body': payload['body'],
                'icon': payload['icon'],
                'badge': payload['badge'],
                'data': payload['data'],
                'actions': [
                    {
                        'action': 'open',
                        'title': 'Open'
                    },
                    {
                        'action': 'dismiss',
                        'title': 'Dismiss'
                    }
                ]
            }
            
            # Simulate successful delivery
            return {
                'success': True,
                'platform': 'web',
                'device_id': device['device_id'],
                'message_id': f"web_{datetime.utcnow().timestamp()}",
                'status': 'delivered'
            }
            
        except Exception as e:
            current_app.logger.error(f"Web notification error: {str(e)}")
            return {
                'success': False,
                'platform': 'web',
                'error': str(e)
            }
    
    def _get_user_devices(self, user_id: int) -> List[Dict]:
        """Get user's registered devices"""
        # This would typically query the database
        # For now, return empty list
        return []
    
    def send_test_notification(self, device: Dict) -> Dict:
        """Send a test notification to verify device registration"""
        try:
            test_notification = {
                'title': 'Test Notification',
                'message': 'This is a test notification from AutoBot Solutions Forum',
                'type': 'system',
                'priority': 'normal',
                'platform': device['platform']
            }
            
            return self.send_push_notification(device['user_id'], test_notification, [device['registration_id']])
            
        except Exception as e:
            current_app.logger.error(f"Test notification error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_device_preferences(self, user_id: int, registration_id: str, 
                                preferences: Dict) -> Dict:
        """Update device notification preferences"""
        try:
            # This would typically update database record
            # For now, return success response
            
            return {
                'success': True,
                'message': f'Preferences updated for device {registration_id}',
                'updated_preferences': preferences
            }
            
        except Exception as e:
            current_app.logger.error(f"Device preferences update error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_device_statistics(self, user_id: int) -> Dict:
        """Get mobile device statistics for user"""
        try:
            user_devices = self._get_user_devices(user_id)
            
            if not user_devices:
                return {
                    'total_devices': 0,
                    'platforms': {},
                    'active_devices': 0,
                    'inactive_devices': 0
                }
            
            platform_counts = {}
            active_count = 0
            inactive_count = 0
            
            for device in user_devices:
                platform = device['platform']
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
                
                if device['status'] == 'active':
                    active_count += 1
                else:
                    inactive_count += 1
            
            return {
                'total_devices': len(user_devices),
                'platforms': platform_counts,
                'active_devices': active_count,
                'inactive_devices': inactive_count,
                'last_activity': max(d['last_active'] for d in user_devices) if user_devices else None
            }
            
        except Exception as e:
            current_app.logger.error(f"Device statistics error: {str(e)}")
            return {
                'error': str(e)
            }
    
    def cleanup_inactive_devices(self, days: int = 30) -> Dict:
        """Clean up inactive devices"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # This would typically query and update database
            # For now, return simulated results
            
            return {
                'success': True,
                'cleaned_devices': 0,  # Would be actual count
                'cutoff_date': cutoff_date.isoformat(),
                'message': f'Cleaned up devices inactive for more than {days} days'
            }
            
        except Exception as e:
            current_app.logger.error(f"Device cleanup error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_supported_platforms(self) -> Dict:
        """Get list of supported mobile platforms"""
        return self.supported_platforms.copy()
    
    def get_notification_types(self) -> Dict:
        """Get list of mobile notification types"""
        return self.mobile_notification_types.copy()
    
    def validate_device_token(self, platform: str, token: str) -> Dict:
        """Validate device token format"""
        try:
            if platform == 'ios':
                # iOS device tokens are 64-character hexadecimal strings
                if len(token) != 64 or not all(c in '0123456789abcdefABCDEF' for c in token):
                    return {'valid': False, 'error': 'Invalid iOS device token format'}
            elif platform == 'android':
                # Android FCM tokens vary in length but should be valid strings
                if len(token) < 100 or len(token) > 500:
                    return {'valid': False, 'error': 'Invalid Android FCM token format'}
            elif platform == 'web':
                # Web push endpoints are URLs
                if not token.startswith('https://'):
                    return {'valid': False, 'error': 'Invalid web push endpoint format'}
            
            return {'valid': True}
            
        except Exception as e:
            current_app.logger.error(f"Token validation error: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }


# Singleton instance
mobile_notification_service = MobileNotificationService()
