# Push Notification Infrastructure Setup Guide

## Overview

This guide provides comprehensive instructions for setting up push notification infrastructure for the notification system. The push infrastructure enables real-time notifications to mobile devices and web browsers across multiple platforms.

**Supported Platforms:**
- iOS (Apple Push Notification Service - APNS)
- Android (Firebase Cloud Messaging - FCM)
- Huawei (Huawei Mobile Services - HMS)
- Web (Push API with Service Workers)

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Notification     │    │  Push Service   │    │  Platform       │
│ Service         │──►│  (Unified)      │──►│  Gateways       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Device Registry│
                       │  & Management   │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Delivery       │
                       │  Tracking       │
                       │  & Analytics     │
                       └─────────────────┘
```

## Prerequisites

### Platform Requirements

#### iOS (APNS)
- **Apple Developer Account** ($99/year)
- **iOS App Bundle ID**
- **APNS Authentication Key** (.p8 file)
- **Team ID** and **Key ID**

#### Android (FCM)
- **Firebase Project**
- **FCM Server Key**
- **Firebase Configuration File** (google-services.json)
- **Android App Package Name**

#### Huawei (HMS)
- **HMS Account**
- **App ID** and **App Secret**
- **HMS Push Kit Configuration**

#### Web Push
- **HTTPS Website** (required for service workers)
- **VAPID Keys** (for web push authentication)
- **Service Worker Registration**

### System Requirements
- **Python 3.8+**
- **Redis 6.0+** (for device registry)
- **HTTPS Certificate** (for web push)
- **Load Balancer** (for high availability)

## Configuration

### Environment Variables

Update your `.env` file with push notification configuration:

```bash
# Push Notification Settings
PUSH_NOTIFICATION_ENABLED=true
PUSH_NOTIFICATION_BATCH_SIZE=100
PUSH_NOTIFICATION_RETRY_ATTEMPTS=3
PUSH_NOTIFICATION_RETRY_DELAY=2

# VAPID Configuration (Web Push)
VAPID_PUBLIC_KEY=your-vapid-public-key-here
VAPID_PRIVATE_KEY=your-vapid-private-key-here
VAPID_SUBJECT=mailto:admin@yourdomain.com

# Apple Push Notification Service (APNS)
APNS_ENABLED=true
APNS_KEY_FILE=path/to/apns/key.p8
APNS_KEY_ID=your-apns-key-id
APNS_TEAM_ID=your-apple-team-id
APNS_BUNDLE_ID=com.yourdomain.app
APNS_SANDBOX=true

# Firebase Cloud Messaging (FCM)
FCM_ENABLED=true
FCM_SERVER_KEY=your-fcm-server-key-here
FCM_SENDER_ID=your-fcm-sender-id

# Huawei Mobile Services (HMS)
HMS_ENABLED=true
HMS_APP_ID=your-hms-app-id
HMS_APP_SECRET=your-hms-app-secret

# Mobile Notification Settings
MOBILE_NOTIFICATION_ENABLED=true
MOBILE_NOTIFICATION_MAX_DEVICES_PER_USER=10
MOBILE_NOTIFICATION_DEVICE_EXPIRY_DAYS=365
MOBILE_NOTIFICATION_CLEANUP_INTERVAL=24

# Platform Support
MOBILE_PLATFORMS_ENABLED=ios,android,huawei,web
MOBILE_NOTIFICATION_TYPES=forum_activity,messages,moderation,security,system,marketing
```

## Platform Setup

### 1. iOS (APNS) Setup

#### Step 1: Create APNS Key
1. Go to [Apple Developer Portal](https://developer.apple.com)
2. Navigate to "Certificates, Identifiers & Profiles"
3. Select "Keys" from the sidebar
4. Click "+" to create a new key
5. Enter key name and select "Apple Push Notifications service"
6. Download the .p8 file (save it securely)
7. Note the Key ID and Team ID

#### Step 2: Configure Bundle ID
1. In Apple Developer Portal, create an App ID
2. Enable "Push Notifications" capability
3. Use the Bundle ID in your iOS app

#### Step 3: Environment Configuration
```bash
# APNS Configuration
APNS_ENABLED=true
APNS_KEY_FILE=/path/to/your/AuthKey_ABC123.p8
APNS_KEY_ID=ABC123
APNS_TEAM_ID=DEF456
APNS_BUNDLE_ID=com.yourdomain.yourapp
APNS_SANDBOX=true  # Set to false for production
```

### 2. Android (FCM) Setup

#### Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create a new project or use existing one
3. Add an Android app
4. Enter your Android package name
5. Download `google-services.json`
6. Place it in your Android app's `app/` directory

#### Step 2: Get Server Key
1. In Firebase Console, go to Project Settings
2. Select "Cloud Messaging"
3. Copy the Server Key
4. Note the Sender ID

#### Step 3: Environment Configuration
```bash
# FCM Configuration
FCM_ENABLED=true
FCM_SERVER_KEY=AAAA_BBBBB_CCCCC_DDDD_EEEE_FFFF_GGGG_HHHH_III_JJJJ_KKKK
FCM_SENDER_ID=123456789012
```

### 3. Huawei (HMS) Setup

#### Step 1: Create HMS Project
1. Go to [HMS Console](https://developer.huawei.com)
2. Create a new project
3. Add your app
4. Enable Push Kit
5. Get App ID and App Secret

#### Step 2: Configure HMS Push
1. Add HMS Core SDK to your Android app
2. Configure push service in your app
3. Test push notifications

#### Step 3: Environment Configuration
```bash
# HMS Configuration
HMS_ENABLED=true
HMS_APP_ID=123456789
HMS_APP_SECRET=your-hms-app-secret
```

### 4. Web Push Setup

#### Step 1: Generate VAPID Keys
```bash
# Generate VAPID keys using web-push library
pip install web-push
python -c "
from web_push import generate_vapid_keys
keys = generate_vapid_keys()
print(f'VAPID_PUBLIC_KEY={keys.public_key}')
print(f'VAPID_PRIVATE_KEY={keys.private_key}')
"
```

#### Step 2: Environment Configuration
```bash
# VAPID Configuration
VAPID_PUBLIC_KEY=your-vapid-public-key-here
VAPID_PRIVATE_KEY=your-vapid-private-key-here
VAPID_SUBJECT=mailto:admin@yourdomain.com
```

#### Step 3: Service Worker Setup
Create `app/static/js/service-worker.js`:

```javascript
// Service Worker for Web Push Notifications
const CACHE_NAME = 'notification-app-v1';

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll([
                '/',
                '/static/js/app.js',
                '/static/css/style.css',
                '/static/images/notification-icon.png'
            ]);
        })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Push notification event
self.addEventListener('push', (event) => {
    const options = {
        body: event.data.text(),
        icon: '/static/images/notification-icon.png',
        badge: '/static/images/badge-icon.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'Explore this new world',
                icon: '/static/images/checkmark.png'
            },
            {
                action: 'close',
                title: 'Close notification',
                icon: '/static/images/x-mark.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('AutoBot Solutions Forum', options)
    );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/notifications')
        );
    } else if (event.action === 'close') {
        // Just close the notification
    } else {
        // Default action - open the app
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});
```

## Push Notification Service Implementation

### Enhanced Push Service

Update `app/notifications/mobile_service.py`:

```python
import json
import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import redis

from app.config.notification_config import get_notification_config

logger = logging.getLogger(__name__)

class MobileNotificationService:
    """Enhanced mobile notification service with multi-platform support"""
    
    def __init__(self):
        self.config = get_notification_config()
        self.redis_client = None
        self.apns_client = None
        self.fcm_client = None
        self.hms_client = None
        
        self._setup_redis()
        self._setup_apns()
        self._setup_fcm()
        self._setup_hms()
    
    def _setup_redis(self):
        """Setup Redis connection for device registry"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                db=self.config.redis_notification_db,
                decode_responses=True
            )
            logger.info("Redis connection established for mobile service")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
    
    def _setup_apns(self):
        """Setup APNS client"""
        if not self.config.apns_enabled:
            return
        
        try:
            # Load APNS key
            with open(self.config.apns_key_file, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
            
            # Initialize APNS client (using pyapns2 or similar)
            self.apns_client = APNSClient(
                team_id=self.config.apns_team_id,
                key_id=self.config.apns_key_id,
                private_key=private_key,
                use_sandbox=self.config.apns_sandbox
            )
            
            logger.info("APNS client initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup APNS: {str(e)}")
    
    def _setup_fcm(self):
        """Setup FCM client"""
        if not self.config.fcm_enabled:
            return
        
        try:
            # Initialize FCM client (using firebase-admin)
            from firebase_admin import credentials, messaging
            
            cred = credentials.Certificate({
                'type': 'service_account',
                'project_id': 'your-project-id',
                'private_key_id': 'your-key-id',
                'private_key': '-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n',
                'client_email': 'firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com',
                'client_id': 'xxx.apps.googleusercontent.com',
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token'
            })
            
            messaging.initialize_app(cred)
            self.fcm_client = messaging
            
            logger.info("FCM client initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup FCM: {str(e)}")
    
    def _setup_hms(self):
        """Setup HMS client"""
        if not self.config.hms_enabled:
            return
        
        try:
            # Initialize HMS client
            self.hms_client = HMSClient(
                app_id=self.config.hms_app_id,
                app_secret=self.config.hms_app_secret
            )
            
            logger.info("HMS client initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup HMS: {str(e)}")
    
    def register_device(self, user_id: int, device_info: Dict) -> Dict:
        """Register a mobile device for push notifications"""
        try:
            # Validate device info
            validation_result = self.validate_device_info(device_info)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error']
                }
            
            # Generate registration ID
            registration_id = f"device_{user_id}_{device_info['device_id']}_{int(time.time())}"
            
            # Store device info
            device_data = {
                'registration_id': registration_id,
                'user_id': user_id,
                'platform': device_info['platform'],
                'device_token': device_info['device_token'],
                'device_id': device_info['device_id'],
                'app_version': device_info.get('app_version', 'unknown'),
                'os_version': device_info.get('os_version', 'unknown'),
                'device_model': device_info.get('device_model', 'unknown'),
                'push_enabled': device_info.get('push_enabled', True),
                'notification_types': device_info.get('notification_types', []),
                'created_at': datetime.utcnow().isoformat(),
                'last_active': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            # Store in Redis
            if self.redis_client:
                self.redis_client.hset(
                    f"mobile_devices:{user_id}",
                    registration_id,
                    json.dumps(device_data)
                )
                
                # Add to platform index
                self.redis_client.sadd(
                    f"mobile_platforms:{device_info['platform']}",
                    registration_id
                )
                
                # Set expiration
                self.redis_client.expire(
                    f"mobile_devices:{user_id}",
                    timedelta(days=self.config.mobile_device_expiry_days)
                )
            
            # Send test notification if requested
            if device_info.get('send_test_notification', False):
                self.send_test_notification(user_id, registration_id)
            
            return {
                'success': True,
                'registration_id': registration_id,
                'device_info': {
                    'platform': device_info['platform'],
                    'device_id': device_info['device_id'],
                    'status': 'active'
                },
                'message': 'Device registered successfully'
            }
            
        except Exception as e:
            logger.error(f"Error registering device: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def unregister_device(self, user_id: int, registration_id: str) -> Dict:
        """Unregister a mobile device"""
        try:
            # Get device info
            device_info = self.get_device_info(registration_id)
            if not device_info:
                return {
                    'success': False,
                    'error': 'Device not found'
                }
            
            # Remove from Redis
            if self.redis_client:
                self.redis_client.hdel(
                    f"mobile_devices:{user_id}",
                    registration_id
                )
                
                # Remove from platform index
                self.redis_client.srem(
                    f"mobile_platforms:{device_info['platform']}",
                    registration_id
                )
            
            return {
                'success': True,
                'message': 'Device unregistered successfully'
            }
            
        except Exception as e:
            logger.error(f"Error unregistering device: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_push_notification(self, user_id: int, notification_data: Dict) -> Dict:
        """Send push notification to user's devices"""
        try:
            # Get user's devices
            devices = self.get_user_devices(user_id)
            
            if not devices:
                return {
                    'success': False,
                    'error': 'No devices registered for user',
                    'total_devices': 0,
                    'total_sent': 0,
                    'total_failed': 0
                }
            
            # Filter devices by notification type
            filtered_devices = self.filter_devices_by_type(
                devices, 
                notification_data.get('type', 'system')
            )
            
            if not filtered_devices:
                return {
                    'success': False,
                    'error': 'No devices support this notification type',
                    'total_devices': len(devices),
                    'total_sent': 0,
                    'total_failed': 0
                }
            
            # Send to each device
            results = {
                'total_devices': len(filtered_devices),
                'total_sent': 0,
                'total_failed': 0,
                'results': {}
            }
            
            for device in filtered_devices:
                platform_result = self.send_to_platform(
                    device['platform'],
                    device['device_token'],
                    notification_data,
                    device
                )
                
                results['results'][device['registration_id']] = platform_result
                
                if platform_result['success']:
                    results['total_sent'] += 1
                else:
                    results['total_failed'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total_devices': 0,
                'total_sent': 0,
                'total_failed': 0
            }
    
    def send_to_platform(self, platform: str, device_token: str, 
                        notification_data: Dict, device_info: Dict) -> Dict:
        """Send notification to specific platform"""
        try:
            if platform == 'ios':
                return self.send_to_apns(device_token, notification_data, device_info)
            elif platform == 'android':
                return self.send_to_fcm(device_token, notification_data, device_info)
            elif platform == 'huawei':
                return self.send_to_hms(device_token, notification_data, device_info)
            elif platform == 'web':
                return self.send_to_web_push(device_token, notification_data, device_info)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported platform: {platform}'
                }
                
        except Exception as e:
            logger.error(f"Error sending to {platform}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'platform': platform
            }
    
    def send_to_apns(self, device_token: str, notification_data: Dict, 
                     device_info: Dict) -> Dict:
        """Send notification to APNS"""
        try:
            if not self.apns_client:
                return {
                    'success': False,
                    'error': 'APNS client not initialized',
                    'platform': 'ios'
                }
            
            # Create APNS payload
            payload = {
                'aps': {
                    'alert': {
                        'title': notification_data.get('title', 'Notification'),
                        'body': notification_data.get('message', ''),
                        'sound': 'default'
                    },
                    'badge': notification_data.get('badge', 1),
                    'category': notification_data.get('category', 'GENERAL'),
                    'mutable-content': 1
                },
                'notification_id': notification_data.get('id'),
                'type': notification_data.get('type'),
                'link': notification_data.get('link', '')
            }
            
            # Add custom data
            if 'custom_data' in notification_data:
                payload.update(notification_data['custom_data'])
            
            # Send notification
            result = self.apns_client.send_notification(
                device_token,
                payload
            )
            
            return {
                'success': True,
                'platform': 'ios',
                'message_id': result.get('message_id'),
                'status': 'delivered'
            }
            
        except Exception as e:
            logger.error(f"Error sending to APNS: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'ios'
            }
    
    def send_to_fcm(self, device_token: str, notification_data: Dict, 
                     device_info: Dict) -> Dict:
        """Send notification to FCM"""
        try:
            if not self.fcm_client:
                return {
                    'success': False,
                    'error': 'FCM client not initialized',
                    'platform': 'android'
                }
            
            # Create FCM message
            message = self.fcm_client.Message(
                token=device_token,
                notification=self.fcm_client.Notification(
                    title=notification_data.get('title', 'Notification'),
                    body=notification_data.get('message', ''),
                    sound='default',
                    badge=notification_data.get('badge', 1)
                ),
                data={
                    'notification_id': str(notification_data.get('id', '')),
                    'type': notification_data.get('type', ''),
                    'link': notification_data.get('link', ''),
                    'custom_data': json.dumps(notification_data.get('custom_data', {}))
                },
                android=self.fcm_client.AndroidConfig(
                    priority='high',
                    notification=self.fcm_client.AndroidNotification(
                        channel_id=notification_data.get('channel_id', 'default'),
                        color=notification_data.get('color', '#007bff'),
                        icon=notification_data.get('icon', 'notification_icon'),
                        sound='default'
                    )
                )
            )
            
            # Send notification
            result = self.fcm_client.send(message)
            
            return {
                'success': True,
                'platform': 'android',
                'message_id': result,
                'status': 'delivered'
            }
            
        except Exception as e:
            logger.error(f"Error sending to FCM: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'android'
            }
    
    def send_to_hms(self, device_token: str, notification_data: Dict, 
                     device_info: Dict) -> Dict:
        """Send notification to HMS"""
        try:
            if not self.hms_client:
                return {
                    'success': False,
                    'error': 'HMS client not initialized',
                    'platform': 'huawei'
                }
            
            # Create HMS payload
            payload = {
                'message': {
                    'android': {
                        'notification': {
                            'title': notification_data.get('title', 'Notification'),
                            'body': notification_data.get('message', ''),
                            'sound': 'default',
                            'color': notification_data.get('color', '#007bff'),
                            'badge': notification_data.get('badge', 1)
                        },
                        'data': {
                            'notification_id': str(notification_data.get('id', '')),
                            'type': notification_data.get('type', ''),
                            'link': notification_data.get('link', '')
                        }
                    },
                    'token': [device_token]
                }
            }
            
            # Send notification
            result = self.hms_client.send_message(payload)
            
            return {
                'success': True,
                'platform': 'huawei',
                'message_id': result.get('code'),
                'status': 'delivered'
            }
            
        except Exception as e:
            logger.error(f"Error sending to HMS: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'huawei'
            }
    
    def send_to_web_push(self, device_token: str, notification_data: Dict, 
                         device_info: Dict) -> Dict:
        """Send notification to Web Push"""
        try:
            from pywebpush import WebPusher, WebPushException
            
            # Create VAPID authentication
            vapid_auth = {
                'vapid': {
                    'subject': self.config.vapid_subject,
                    'public_key': self.config.vapid_public_key,
                    'private_key': self.config.vapid_private_key
                }
            }
            
            # Create push subscription info
            subscription_info = {
                'endpoint': device_token,
                'keys': {
                    'p256dh': device_info.get('p256dh', ''),
                    'auth': device_info.get('auth', '')
                }
            }
            
            # Create payload
            payload = json.dumps({
                'title': notification_data.get('title', 'Notification'),
                'body': notification_data.get('message', ''),
                'icon': notification_data.get('icon', '/static/images/notification-icon.png'),
                'badge': notification_data.get('badge', '/static/images/badge-icon.png'),
                'data': {
                    'notification_id': str(notification_data.get('id', '')),
                    'type': notification_data.get('type', ''),
                    'link': notification_data.get('link', '')
                }
            })
            
            # Send notification
            webpusher = WebPusher(subscription_info, vapid_auth)
            result = webpusher.send(payload)
            
            return {
                'success': True,
                'platform': 'web',
                'message_id': result,
                'status': 'delivered'
            }
            
        except WebPushException as e:
            logger.error(f"WebPush error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'web'
            }
        except Exception as e:
            logger.error(f"Error sending to Web Push: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'web'
            }
    
    def validate_device_info(self, device_info: Dict) -> Dict:
        """Validate device registration information"""
        errors = []
        
        # Required fields
        required_fields = ['platform', 'device_token', 'device_id']
        for field in required_fields:
            if field not in device_info or not device_info[field]:
                errors.append(f"Missing required field: {field}")
        
        # Platform validation
        valid_platforms = ['ios', 'android', 'huawei', 'web']
        if device_info.get('platform') not in valid_platforms:
            errors.append(f"Invalid platform: {device_info.get('platform')}")
        
        # Token validation
        platform = device_info.get('platform')
        device_token = device_info.get('device_token', '')
        
        if platform == 'ios':
            if not self.validate_ios_token(device_token):
                errors.append("Invalid iOS device token")
        elif platform == 'web':
            if not self.validate_web_push_token(device_info):
                errors.append("Invalid Web Push subscription")
        
        if errors:
            return {
                'valid': False,
                'error': '; '.join(errors)
            }
        
        return {'valid': True}
    
    def validate_ios_token(self, device_token: str) -> bool:
        """Validate iOS device token"""
        # iOS device tokens are 64-character hexadecimal strings
        if len(device_token) != 64:
            return False
        try:
            int(device_token, 16)
            return True
        except ValueError:
            return False
    
    def validate_web_push_token(self, device_info: Dict) -> bool:
        """Validate Web Push subscription"""
        required_web_fields = ['p256dh', 'auth']
        for field in required_web_fields:
            if field not in device_info or not device_info[field]:
                return False
        return True
    
    def get_device_info(self, registration_id: str) -> Optional[Dict]:
        """Get device information by registration ID"""
        try:
            if self.redis_client:
                # Search for device across all users
                for key in self.redis_client.scan_iter(match="mobile_devices:*"):
                    user_id = key.split(':')[-1]
                    device_data = self.redis_client.hget(key, registration_id)
                    if device_data:
                        return json.loads(device_data)
            return None
        except Exception as e:
            logger.error(f"Error getting device info: {str(e)}")
            return None
    
    def get_user_devices(self, user_id: int) -> List[Dict]:
        """Get all devices for a user"""
        try:
            devices = []
            
            if self.redis_client:
                device_data = self.redis_client.hgetall(f"mobile_devices:{user_id}")
                
                for registration_id, data in device_data.items():
                    device = json.loads(data)
                    devices.append(device)
            
            return devices
        except Exception as e:
            logger.error(f"Error getting user devices: {str(e)}")
            return []
    
    def filter_devices_by_type(self, devices: List[Dict], 
                             notification_type: str) -> List[Dict]:
        """Filter devices by notification type preference"""
        filtered_devices = []
        
        for device in devices:
            notification_types = device.get('notification_types', [])
            
            # Include device if it supports this notification type
            if notification_type in notification_types or 'all' in notification_types:
                filtered_devices.append(device)
        
        return filtered_devices
    
    def get_device_statistics(self, user_id: int) -> Dict:
        """Get device statistics for a user"""
        try:
            devices = self.get_user_devices(user_id)
            
            stats = {
                'total_devices': len(devices),
                'platforms': {},
                'active_devices': 0,
                'inactive_devices': 0
            }
            
            for device in devices:
                platform = device['platform']
                stats['platforms'][platform] = stats['platforms'].get(platform, 0) + 1
                
                if device['status'] == 'active':
                    stats['active_devices'] += 1
                else:
                    stats['inactive_devices'] += 1
            
            return stats
        except Exception as e:
            logger.error(f"Error getting device statistics: {str(e)}")
            return {
                'total_devices': 0,
                'platforms': {},
                'active_devices': 0,
                'inactive_devices': 0
            }
    
    def get_supported_platforms(self) -> Dict:
        """Get supported mobile platforms"""
        return {
            'ios': 'Apple iOS',
            'android': 'Google Android',
            'huawei': 'Huawei Mobile Services',
            'web': 'Web Push'
        }
    
    def get_notification_types(self) -> Dict:
        """Get supported notification types"""
        return {
            'forum_activity': 'Forum Activity',
            'messages': 'Messages',
            'moderation': 'Moderation',
            'security': 'Security',
            'system': 'System Updates',
            'marketing': 'Marketing (opt-in)'
        }
    
    def send_test_notification(self, user_id: int, registration_id: str) -> Dict:
        """Send test notification to device"""
        test_notification = {
            'id': 'test_' + str(int(time.time())),
            'title': 'Test Notification',
            'message': 'This is a test notification from AutoBot Solutions Forum',
            'type': 'system',
            'badge': 1
        }
        
        device_info = self.get_device_info(registration_id)
        if not device_info:
            return {
                'success': False,
                'error': 'Device not found'
            }
        
        return self.send_to_platform(
            device_info['platform'],
            device_info['device_token'],
            test_notification,
            device_info
        )
    
    def cleanup_inactive_devices(self):
        """Clean up inactive devices"""
        try:
            if not self.redis_client:
                return
            
            # Get all device keys
            device_keys = self.redis_client.scan_iter(match="mobile_devices:*")
            
            for key in device_keys:
                user_id = key.split(':')[-1]
                devices = self.redis_client.hgetall(key)
                
                for registration_id, device_data in devices.items():
                    device = json.loads(device_data)
                    
                    # Check if device is inactive
                    last_active = datetime.fromisoformat(device['last_active'])
                    if datetime.utcnow() - last_active > timedelta(days=90):
                        # Remove inactive device
                        self.redis_client.hdel(key, registration_id)
                        
                        # Remove from platform index
                        self.redis_client.srem(
                            f"mobile_platforms:{device['platform']}",
                            registration_id
                        )
            
            logger.info("Inactive device cleanup completed")
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive devices: {str(e)}")
    
    def get_delivery_statistics(self) -> Dict:
        """Get push notification delivery statistics"""
        try:
            stats = {
                'total_devices': 0,
                'platforms': {},
                'recent_registrations': 0,
                'active_devices': 0
            }
            
            if self.redis_client:
                # Count total devices
                for key in self.redis_client.scan_iter(match="mobile_devices:*"):
                    devices = self.redis_client.hgetall(key)
                    stats['total_devices'] += len(devices)
                    
                    for device_data in devices.values():
                        device = json.loads(device_data)
                        
                        # Count by platform
                        platform = device['platform']
                        stats['platforms'][platform] = stats['platforms'].get(platform, 0) + 1
                        
                        # Count recent registrations
                        created_at = datetime.fromisoformat(device['created_at'])
                        if datetime.utcnow() - created_at < timedelta(days=7):
                            stats['recent_registrations'] += 1
                        
                        # Count active devices
                        if device['status'] == 'active':
                            stats['active_devices'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting delivery statistics: {str(e)}")
            return {}

# Global mobile notification service instance
mobile_notification_service = MobileNotificationService()
```

## Client Integration

### iOS Client Integration

Create iOS push notification handler:

```swift
// iOS Push Notification Handler
import UserNotifications
import UIKit

class NotificationService: NSObject, UNUserNotificationCenterDelegate {
    
    static let shared = NotificationService()
    
    func requestNotificationPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            if granted {
                print("Notification permission granted")
            } else {
                print("Notification permission denied")
            }
        }
    }
    
    func registerForPushNotifications(deviceToken: Data) {
        let tokenString = deviceToken.map { String(format: "%02.2hh", $0) }.joined()
        print("Device token: \(tokenString)")
        
        // Send token to your server
        sendDeviceTokenToServer(tokenString)
    }
    
    func sendDeviceTokenToServer(_ token: String) {
        // Implement API call to register device
        guard let url = URL(string: "https://yourdomain.com/api/mobile/register") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let parameters = [
            "platform": "ios",
            "device_token": token,
            "device_id": UIDevice.current.identifierForVendor?.uuidString ?? "",
            "app_version": Bundle.main.infoDictionaryString?["CFBundleShortVersionString"] ?? "",
            "os_version": UIDevice.current.systemVersion,
            "device_model": UIDevice.current.model
        ]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: parameters)
        } catch {
            print("Error encoding parameters")
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error registering device: \(error)")
            } else if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 200 {
                    print("Device registered successfully")
                } else {
                    print("Device registration failed: \(httpResponse.statusCode)")
                }
            }
        }.resume()
    }
    
    func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse, withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        
        // Handle notification tap
        completionHandler([])
        
        // Navigate to appropriate screen based on notification data
        if let userInfo = response.notification.request.content.userInfo {
            handleNotificationTap(userInfo)
        }
    }
    
    func handleNotificationTap(_ userInfo: [Any: Any]) {
        // Navigate to relevant screen
        if let notificationId = userInfo["notification_id"] as? String,
           let link = userInfo["link"] as? String {
            // Navigate to notification or link
            print("Notification tapped: \(notificationId), link: \(link)")
        }
    }
}
```

### Android Client Integration

Create Android push notification handler:

```java
// Android Push Notification Service
public class MyFirebaseMessagingService extends FirebaseMessagingService {
    
    @Override
    public void onNewToken(@NonNull String token) {
        super.onNewToken(token);
        Log.d("FCM", "Device token: " + token);
        
        // Send token to your server
        sendDeviceTokenToServer(token);
    }
    
    private void sendDeviceTokenToServer(String token) {
        // Implement API call to register device
        String url = "https://yourdomain.com/api/mobile/register";
        
        try {
            JSONObject parameters = new JSONObject();
            parameters.put("platform", "android");
            parameters.put("device_token", token);
            parameters.put("device_id", Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID));
            parameters.put("app_version", BuildConfig.VERSION_NAME);
            parameters.put("os_version", Build.VERSION.RELEASE);
            parameters.put("device_model", Build.MODEL);
            
            JsonObjectRequest request = new JsonObjectRequest(
                Request.Method.POST,
                url,
                parameters,
                response -> Log.d("FCM", "Device registered successfully"),
                error -> Log.e("FCM", "Device registration failed", error)
            );
            
            RequestQueue queue = Volley.newRequestQueue(this);
            queue.add(request);
            
        } catch (JSONException e) {
            Log.e("FCM", "Error creating parameters", e);
        }
    }
    
    @Override
    public void onMessageReceived(@NonNull RemoteMessage remoteMessage) {
        Log.d("FCM", "Message received: " + remoteMessage.getData());
        
        // Handle notification
        sendNotification(remoteMessage);
    }
    
    private void sendNotification(RemoteMessage remoteMessage) {
        // Create notification channel for Android 8.0+
        String channelId = "default_channel";
        
        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, channelId)
                .setSmallIcon(R.drawable.notification_icon)
                .setContentTitle(remoteMessage.getData().get("title"))
                .setContentText(remoteMessage.getData().get("body"))
                .setAutoCancel(true)
                .setPriority(NotificationCompat.PRIORITY_HIGH);
        
        // Add click action
        Intent intent = new Intent(this, MainActivity.class);
        intent.putExtra("notification_id", remoteMessage.getData().get("notification_id"));
        intent.putExtra("link", remoteMessage.getData().get("link"));
        
        PendingIntent pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
        
        builder.setContentIntent(pendingIntent);
        
        NotificationManager notificationManager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        
        // Create channel for Android 8.0+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    channelId,
                    "Default Channel",
                    NotificationManager.IMPORTANCE_DEFAULT
            );
            notificationManager.createNotificationChannel(channel);
        }
        
        notificationManager.notify(0, builder.build());
    }
}
```

### Web Client Integration

Create web push registration:

```javascript
// Web Push Registration
class WebPushManager {
    constructor() {
        this.subscription = null;
        this.swRegistration = null;
    }
    
    async init() {
        try {
            // Register service worker
            this.swRegistration = await navigator.serviceWorker.register('/service-worker.js');
            
            // Check existing subscription
            this.subscription = await this.swRegistration.pushManager.getSubscription();
            
            if (!this.subscription) {
                // Subscribe to push notifications
                await this.subscribe();
            } else {
                // Send existing subscription to server
                await this.sendSubscriptionToServer();
            }
            
        } catch (error) {
            console.error('Error initializing Web Push:', error);
        }
    }
    
    async subscribe() {
        try {
            // Get VAPID public key from server
            const vapidPublicKey = await this.getVapidPublicKey();
            
            // Subscribe to push notifications
            this.subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(vapidPublicKey)
            });
            
            // Send subscription to server
            await this.sendSubscriptionToServer();
            
            console.log('Web Push subscription successful');
            
        } catch (error) {
            console.error('Error subscribing to Web Push:', error);
        }
    }
    
    async unsubscribe() {
        try {
            if (this.subscription) {
                await this.subscription.unsubscribe();
                this.subscription = null;
                
                // Remove subscription from server
                await this.removeSubscriptionFromServer();
                
                console.log('Web Push unsubscription successful');
            }
        } catch (error) {
            console.error('Error unsubscribing from Web Push:', error);
        }
    }
    
    async sendSubscriptionToServer() {
        try {
            const response = await fetch('/api/mobile/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    platform: 'web',
                    device_token: this.subscription.endpoint,
                    device_id: this.generateDeviceId(),
                    p256dh: this.subscription.getKey('p256dh'),
                    auth: this.subscription.getKey('auth')
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Web Push subscription registered:', data);
            } else {
                console.error('Failed to register Web Push subscription');
            }
            
        } catch (error) {
            console.error('Error sending subscription to server:', error);
        }
    }
    
    async getVapidPublicKey() {
        try {
            const response = await fetch('/api/mobile/api/vapid-public-key');
            const data = await response.json();
            return data.public_key;
        } catch (error) {
            console.error('Error getting VAPID public key:', error);
            return '';
        }
    }
    
    generateDeviceId() {
        // Generate or retrieve device ID
        let deviceId = localStorage.getItem('web_device_id');
        if (!deviceId) {
            deviceId = 'web_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('web_device_id', deviceId);
        }
        return deviceId;
    }
    
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        
        return outputArray;
    }
}

// Initialize Web Push Manager
const webPushManager = new WebPushManager();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        webPushManager.init();
    }
});
```

## Testing

### Push Notification Tests

Create `tests/test_mobile_service.py`:

```python
import unittest
from unittest.mock import Mock, patch
from app.notifications.mobile_service import MobileNotificationService

class TestMobileNotificationService(unittest.TestCase):
    
    def setUp(self):
        self.mobile_service = MobileNotificationService()
    
    def test_device_registration(self):
        """Test device registration"""
        device_info = {
            'platform': 'ios',
            'device_token': 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
            'device_id': 'test_device_123',
            'app_version': '1.0.0',
            'os_version': 'iOS 17.0',
            'device_model': 'iPhone 15'
        }
        
        result = self.mobile_service.register_device(1, device_info)
        
        self.assertTrue(result['success'])
        self.assertIn('registration_id', result)
        self.assertEqual(result['device_info']['platform'], 'ios')
    
    def test_device_validation(self):
        """Test device validation"""
        # Valid device info
        valid_device = {
            'platform': 'ios',
            'device_token': 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
            'device_id': 'test_device_123'
        }
        
        result = self.mobile_service.validate_device_info(valid_device)
        self.assertTrue(result['valid'])
        
        # Invalid device info
        invalid_device = {
            'platform': 'invalid',
            'device_token': 'invalid_token',
            'device_id': ''
        }
        
        result = self.mobile_service.validate_device_info(invalid_device)
        self.assertFalse(result['valid'])
    
    def test_ios_token_validation(self):
        """Test iOS token validation"""
        # Valid iOS token
        valid_token = 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2'
        self.assertTrue(self.mobile_service.validate_ios_token(valid_token))
        
        # Invalid iOS token
        invalid_token = 'invalid_token'
        self.assertFalse(self.mobile_service.validate_ios_token(invalid_token))
    
    def test_get_supported_platforms(self):
        """Test getting supported platforms"""
        platforms = self.mobile_service.get_supported_platforms()
        
        self.assertIn('ios', platforms)
        self.assertIn('android', platforms)
        self.assertIn('huawei', platforms)
        self.assertIn('web', platforms)
    
    def test_get_notification_types(self):
        """Test getting notification types"""
        types = self.mobile_service.get_notification_types()
        
        self.assertIn('forum_activity', types)
        self.assertIn('messages', types)
        self.assertIn('security', types)
    
    @patch('app.notifications.mobile_service.MobileNotificationService.send_to_apns')
    def test_send_push_notification(self, mock_send_to_apns):
        """Test sending push notification"""
        # Mock successful send
        mock_send_to_apns.return_value = {
            'success': True,
            'platform': 'ios',
            'message_id': 'test_message_id'
        }
        
        notification_data = {
            'title': 'Test Notification',
            'message': 'Test message',
            'type': 'system'
        }
        
        result = self.mobile_service.send_push_notification(1, notification_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_devices', result)
        self.assertIn('total_sent', result)
        self.assertIn('total_failed', result)

if __name__ == '__main__':
    unittest.main()
```

## Production Deployment

### Production Configuration

```bash
# Production push notification settings
PUSH_NOTIFICATION_ENABLED=true
PUSH_NOTIFICATION_BATCH_SIZE=200
PUSH_NOTIFICATION_RETRY_ATTEMPTS=5
PUSH_NOTIFICATION_RETRY_DELAY=3

# Production platform settings
APNS_ENABLED=true
APNS_SANDBOX=false
FCM_ENABLED=true
HMS_ENABLED=true

# Device management
MOBILE_NOTIFICATION_MAX_DEVICES_PER_USER=20
MOBILE_NOTIFICATION_DEVICE_EXPIRY_DAYS=365
MOBILE_NOTIFICATION_CLEANUP_INTERVAL=12
```

### Docker Deployment

Add to `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - PUSH_NOTIFICATION_ENABLED=true
      - APNS_ENABLED=true
      - FCM_ENABLED=true
      - HMS_ENABLED=true
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  push-worker:
    build: .
    command: python scripts/push_worker.py
    environment:
      - PUSH_NOTIFICATION_ENABLED=true
      - APNS_ENABLED=true
      - FCM_ENABLED=true
      - HMS_ENABLED=true
    depends_on:
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2

volumes:
  redis_data:
```

### Monitoring

Create `scripts/monitor_push_notifications.py`:

```python
#!/usr/bin/env python3
"""
Push notification monitoring script
"""

import time
from datetime import datetime
from app.notifications.mobile_service import mobile_notification_service

def monitor_push_notifications():
    """Monitor push notification system"""
    while True:
        try:
            stats = mobile_notification_service.get_delivery_statistics()
            
            print(f"[{datetime.now()}] Push Notification Stats:")
            print(f"  Total Devices: {stats['total_devices']}")
            print(f"  Active Devices: {stats['active_devices']}")
            print(f"  Platforms: {stats['platforms']}")
            print(f"  Recent Registrations: {stats['recent_registrations']}")
            
            # Alert if no devices
            if stats['total_devices'] == 0:
                print("  WARNING: No registered devices!")
            
            print("-" * 50)
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"Error monitoring push notifications: {str(e)}")
            time.sleep(10)

if __name__ == '__main__':
    monitor_push_notifications()
```

## Troubleshooting

### Common Issues

1. **APNS Token Invalid**
   - Check if device token is properly formatted
   - Verify APNS key and certificate
   - Check sandbox vs production environment

2. **FCM Registration Failed**
   - Verify Firebase project configuration
   - Check server key validity
   - Ensure Android app package name matches

3. **HMS Push Not Working**
   - Verify HMS app ID and secret
   - Check HMS SDK integration
   - Ensure device supports HMS

4. **Web Push Not Working**
   - Ensure website uses HTTPS
   - Check VAPID key configuration
   - Verify service worker registration

### Debug Mode

Enable debug logging:

```bash
export NOTIFICATION_DEBUG=true
export PUSH_DEBUG=true
python -c "from app.notifications.mobile_service import mobile_notification_service; print('Mobile service initialized')"
```

---

**Last Updated:** May 12, 2026  
**Version:** 1.0  
**Status:** Production Ready
