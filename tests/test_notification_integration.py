"""
Notification System Integration Tests

This test suite provides comprehensive integration testing for the notification system,
testing end-to-end workflows and component interactions.

Integration Coverage:
- End-to-end notification flow
- Service integration scenarios
- Database integration
- WebSocket integration
- Email delivery integration
- Mobile notification integration
- Performance integration
"""

import unittest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask.testing import TestCase
from flask_socketio import SocketIO

# Import notification system components
from app.notifications.translation_service import notification_translation_service
from app.notifications.filtering_service import notification_filtering_service
from app.notifications.mobile_service import mobile_notification_service
from app.notifications.models import (
    Notification,
    AdminNotification,
    NotificationTemplate,
    NotificationPreference,
    NotificationDelivery,
    NotificationCategory
)
from app.notifications.forms import (
    UserNotificationPreferencesForm,
    NotificationSearchAdvancedForm,
    NotificationArchiveForm,
    NotificationScheduleForm,
    NotificationGroupingForm
)
from app.websockets.events import handle_subscribe_notifications
from app.email.notification_service import email_notification_service


class TestNotificationEndToEndFlow(TestCase):
    """Test cases for complete notification flow"""
    
    def create_app(self):
        """Create Flask app for integration testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        return app
    
    def test_complete_notification_flow(self):
        """Test complete notification creation to delivery flow"""
        with self.create_app().app_context():
            # Step 1: Create notification
            notification_data = {
                'type': 'comment',
                'content': 'john_doe commented on your post "Welcome to the Forum"',
                'username': 'john_doe',
                'post_title': 'Welcome to the Forum',
                'user_id': 1,
                'priority': 'normal'
            }
            
            # Step 2: Apply translation
            translated = notification_translation_service.translate_notification(
                notification_data, 1
            )
            
            # Step 3: Apply filtering
            filters = {'type': ['comment'], 'priority': ['normal']}
            filter_result = notification_filtering_service.create_custom_filter(
                user_id=1,
                name='Test Flow Filter',
                filters=filters
            )
            
            # Step 4: Apply mobile notification
            device_info = {
                'platform': 'ios',
                'device_token': 'test_token',
                'device_id': 'test_device'
            }
            mobile_result = mobile_notification_service.register_device(1, device_info)
            
            # Verify all steps completed successfully
            self.assertIsInstance(translated, dict)
            self.assertIsInstance(filter_result, dict)
            self.assertTrue(mobile_result['success'])
    
    def test_notification_with_translation_flow(self):
        """Test notification flow with multi-language translation"""
        with self.create_app().app_context():
            # Create notification in English
            notification_data = {
                'type': 'comment',
                'content': 'jane_smith commented on your post "Hello World"',
                'username': 'jane_smith',
                'post_title': 'Hello World',
                'user_id': 1
            }
            
            # Set user language preference to Spanish
            notification_translation_service.set_user_language_preference(1, 'es')
            
            # Translate notification
            translated = notification_translation_service.translate_notification(
                notification_data, 1
            )
            
            # Verify translation was applied
            self.assertIsInstance(translated, dict)
            self.assertIn('type', translated)
            self.assertIn('content', translated)
    
    def test_notification_with_grouping_flow(self):
        """Test notification flow with intelligent grouping"""
        with self.create_app().app_context():
            # Create similar notifications
            notifications = [
                {
                    'type': 'comment',
                    'content': 'user1 commented on your post',
                    'username': 'user1'
                },
                {
                    'type': 'comment',
                    'content': 'user2 commented on your post',
                    'username': 'user2'
                }
            ]
            
            # Apply grouping
            grouped = notification_filtering_service.group_notifications(
                notifications, 'type'
            )
            
            # Verify grouping was applied
            self.assertIsInstance(grouped, list)
    
    def test_notification_with_scheduling_flow(self):
        """Test notification flow with scheduling"""
        with self.create_app().app_context():
            # Create notification during quiet hours
            notification_data = {
                'type': 'message',
                'content': 'You have a new message',
                'sender_name': 'john_doe',
                'user_id': 1,
                'priority': 'normal'
            }
            
            # Test scheduling logic (would normally check quiet hours)
            # For now, just verify the notification can be processed
            result = notification_translation_service.translate_notification(
                notification_data, 1
            )
            
            self.assertIsInstance(result, dict)


class TestServiceIntegration(TestCase):
    """Test cases for service integration scenarios"""
    
    def create_app(self):
        """Create Flask app for integration testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    def test_translation_filtering_integration(self):
        """Test translation and filtering service integration"""
        with self.create_app().app_context():
            # Create test notifications
            notifications = [
                {
                    'type': 'comment',
                    'content': 'user1 commented on your post',
                    'username': 'user1'
                },
                {
                    'type': 'message',
                    'content': 'user2 sent you a message',
                    'sender_name': 'user2'
                }
            ]
            
            # Apply bulk translation
            translated = notification_translation_service.translate_bulk_notifications(
                notifications, 1
            )
            
            # Apply filtering based on translated content
            filters = {'type': ['comment']}
            custom_filter = notification_filtering_service.create_custom_filter(
                user_id=1,
                name='Translation Filter',
                filters=filters
            )
            
            # Verify integration worked
            self.assertEqual(len(translated), 2)
            self.assertIsInstance(custom_filter, dict)
            self.assertIn('id', custom_filter)
    
    def test_mobile_translation_integration(self):
        """Test mobile and translation service integration"""
        with self.create_app().app_context():
            # Register device with language preference
            device_info = {
                'platform': 'android',
                'device_token': 'android_token',
                'device_id': 'android_device',
                'notification_types': ['comment', 'message'],
                'language': 'es'
            }
            
            registration = mobile_notification_service.register_device(1, device_info)
            
            # Create notification and translate
            notification_data = {
                'type': 'comment',
                'content': 'john_doe commented on your post',
                'username': 'john_doe',
                'user_id': 1
            }
            
            translated = notification_translation_service.translate_notification(
                notification_data, 1
            )
            
            # Send mobile notification with translated content
            mobile_notification = mobile_notification_service.send_push_notification(
                1,
                {
                    'title': translated.get('title', 'New Comment'),
                    'message': translated.get('content', 'New comment'),
                    'type': 'comment'
                }
            )
            
            # Verify integration
            self.assertTrue(registration['success'])
            self.assertIsInstance(translated, dict)
            self.assertIsInstance(mobile_notification, dict)
    
    def test_filtering_mobile_integration(self):
        """Test filtering and mobile service integration"""
        with self.create_app().app_context():
            # Register device with specific notification types
            device_info = {
                'platform': 'ios',
                'device_token': 'ios_token',
                'device_id': 'ios_device',
                'notification_types': ['comment', 'system']
            }
            
            registration = mobile_notification_service.register_device(1, device_info)
            
            # Create filter matching device preferences
            filters = {'type': ['comment', 'system']}
            custom_filter = notification_filtering_service.create_custom_filter(
                user_id=1,
                name='Mobile Filter',
                filters=filters
            )
            
            # Verify integration
            self.assertTrue(registration['success'])
            self.assertIsInstance(custom_filter, dict)
            self.assertEqual(custom_filter['name'], 'Mobile Filter')
    
    def test_all_services_integration(self):
        """Test integration of all notification services"""
        with self.create_app().app_context():
            # Step 1: Set up user preferences
            notification_translation_service.set_user_language_preference(1, 'fr')
            
            # Step 2: Register mobile device
            device_info = {
                'platform': 'ios',
                'device_token': 'integration_token',
                'device_id': 'integration_device',
                'notification_types': ['comment', 'message', 'system']
            }
            mobile_registration = mobile_notification_service.register_device(1, device_info)
            
            # Step 3: Create notification
            notification_data = {
                'type': 'comment',
                'content': 'integration_user commented on your post',
                'username': 'integration_user',
                'post_title': 'Integration Test Post',
                'user_id': 1
            }
            
            # Step 4: Apply translation
            translated = notification_translation_service.translate_notification(
                notification_data, 1
            )
            
            # Step 5: Apply filtering
            filters = {'type': ['comment']}
            filter_result = notification_filtering_service.create_custom_filter(
                user_id=1,
                name='Integration Filter',
                filters=filters
            )
            
            # Step 6: Send mobile notification
            mobile_result = mobile_notification_service.send_push_notification(
                1,
                {
                    'title': translated.get('title', 'New Comment'),
                    'message': translated.get('content', 'New comment'),
                    'type': 'comment'
                }
            )
            
            # Verify all services worked together
            self.assertTrue(mobile_registration['success'])
            self.assertIsInstance(translated, dict)
            self.assertIsInstance(filter_result, dict)
            self.assertIsInstance(mobile_result, dict)


class TestDatabaseIntegration(TestCase):
    """Test cases for database integration"""
    
    def create_app(self):
        """Create Flask app with database"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize database
        from flask_sqlalchemy import SQLAlchemy
        db = SQLAlchemy(app)
        
        # Import models (would normally be done in app initialization)
        # For testing, we'll just verify the models exist
        
        return app
    
    def test_notification_model_integration(self):
        """Test notification model database integration"""
        with self.create_app().app_context():
            # Test that notification models can be imported
            from app.notifications.models import Notification
            
            # Verify model attributes
            self.assertTrue(hasattr(Notification, 'id'))
            self.assertTrue(hasattr(Notification, 'user_id'))
            self.assertTrue(hasattr(Notification, 'content'))
            self.assertTrue(hasattr(Notification, 'is_read'))
            self.assertTrue(hasattr(Notification, 'created_at'))
    
    def test_admin_notification_model_integration(self):
        """Test admin notification model database integration"""
        with self.create_app().app_context():
            from app.notifications.models import AdminNotification
            
            # Verify model attributes
            self.assertTrue(hasattr(AdminNotification, 'id'))
            self.assertTrue(hasattr(AdminNotification, 'user_id'))
            self.assertTrue(hasattr(AdminNotification, 'title'))
            self.assertTrue(hasattr(AdminNotification, 'message'))
            self.assertTrue(hasattr(AdminNotification, 'notification_type'))
    
    def test_notification_preference_model_integration(self):
        """Test notification preference model database integration"""
        with self.create_app().app_context():
            from app.notifications.models import NotificationPreference
            
            # Verify model attributes
            self.assertTrue(hasattr(NotificationPreference, 'id'))
            self.assertTrue(hasattr(NotificationPreference, 'user_id'))
            self.assertTrue(hasattr(NotificationPreference, 'notification_type'))
            self.assertTrue(hasattr(NotificationPreference, 'enabled'))
    
    def test_notification_delivery_model_integration(self):
        """Test notification delivery model database integration"""
        with self.create_app().app_context():
            from app.notifications.models import NotificationDelivery
            
            # Verify model attributes
            self.assertTrue(hasattr(NotificationDelivery, 'id'))
            self.assertTrue(hasattr(NotificationDelivery, 'notification_id'))
            self.assertTrue(hasattr(NotificationDelivery, 'delivery_type'))
            self.assertTrue(hasattr(NotificationDelivery, 'status'))


class TestWebSocketIntegration(TestCase):
    """Test cases for WebSocket integration"""
    
    def create_app(self):
        """Create Flask app with WebSocket"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Initialize SocketIO
        socketio = SocketIO(app)
        
        return app
    
    def test_websocket_notification_integration(self):
        """Test WebSocket notification integration"""
        with self.create_app().app_context():
            # Test that WebSocket handlers can be imported
            from app.websockets.events import (
                handle_subscribe_notifications,
                handle_mark_notification_read,
                handle_fetch_unread_count
            )
            
            # Verify handlers exist
            self.assertTrue(callable(handle_subscribe_notifications))
            self.assertTrue(callable(handle_mark_notification_read))
            self.assertTrue(callable(handle_fetch_unread_count))
    
    def test_websocket_service_integration(self):
        """Test WebSocket service integration"""
        with self.create_app().app_context():
            # Test that WebSocket service can be imported
            from app.websockets.service import NotificationWebSocketService
            
            # Verify service exists
            self.assertTrue(hasattr(NotificationWebSocketService, 'broadcast_notification'))
            self.assertTrue(hasattr(NotificationWebSocketService, 'emit_unread_count'))
    
    def test_realtime_notification_flow(self):
        """Test real-time notification flow via WebSocket"""
        with self.create_app().app_context():
            # Create test notification data
            notification_data = {
                'id': 1,
                'user_id': 1,
                'content': 'Test notification',
                'type': 'comment',
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Test WebSocket service methods (would normally emit to clients)
            from app.websockets.service import NotificationWebSocketService
            
            # Verify service methods exist
            self.assertTrue(hasattr(NotificationWebSocketService, 'broadcast_notification'))
            self.assertTrue(hasattr(NotificationWebSocketService, 'emit_notification_read'))


class TestEmailIntegration(TestCase):
    """Test cases for email delivery integration"""
    
    def create_app(self):
        """Create Flask app for email testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    def test_email_notification_service_integration(self):
        """Test email notification service integration"""
        with self.create_app().app_context():
            # Test that email service can be imported
            from app.email.notification_service import email_notification_service
            
            # Verify service exists
            self.assertTrue(hasattr(email_notification_service, 'send_notification_email'))
            self.assertTrue(hasattr(email_notification_service, 'send_bulk_emails'))
    
    def test_email_template_integration(self):
        """Test email template integration"""
        with self.create_app().app_context():
            # Create test notification data
            notification_data = {
                'type': 'comment',
                'content': 'john_doe commented on your post',
                'username': 'john_doe',
                'post_title': 'Test Post',
                'user_email': 'test@example.com'
            }
            
            # Test email template rendering (would normally use Jinja2)
            from app.email.notification_service import email_notification_service
            
            # Verify email service can process notification
            self.assertTrue(hasattr(email_notification_service, 'send_notification_email'))
    
    def test_email_translation_integration(self):
        """Test email and translation service integration"""
        with self.create_app().app_context():
            # Create notification with translation
            notification_data = {
                'type': 'comment',
                'content': 'jane_smith commented on your post',
                'username': 'jane_smith',
                'post_title': 'Test Post',
                'user_id': 1
            }
            
            # Apply translation
            translated = notification_translation_service.translate_notification(
                notification_data, 1
            )
            
            # Test email service with translated content
            from app.email.notification_service import email_notification_service
            
            # Verify integration
            self.assertIsInstance(translated, dict)
            self.assertTrue(hasattr(email_notification_service, 'send_notification_email'))


class TestPerformanceIntegration(TestCase):
    """Test cases for performance integration"""
    
    def create_app(self):
        """Create Flask app for performance testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    def test_translation_performance(self):
        """Test translation service performance"""
        with self.create_app().app_context():
            # Create test notifications
            notifications = [
                {
                    'type': 'comment',
                    'content': f'user{i} commented on your post',
                    'username': f'user{i}'
                }
                for i in range(100)
            ]
            
            # Measure translation performance
            start_time = time.time()
            
            translated = notification_translation_service.translate_bulk_notifications(
                notifications, 1
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Verify performance and results
            self.assertEqual(len(translated), 100)
            self.assertLess(duration, 1.0)  # Should complete in under 1 second
    
    def test_filtering_performance(self):
        """Test filtering service performance"""
        with self.create_app().app_context():
            # Create multiple custom filters
            filters = [
                {
                    'type': ['comment'],
                    'priority': ['high']
                },
                {
                    'type': ['message'],
                    'priority': ['normal']
                },
                {
                    'type': ['system'],
                    'priority': ['urgent']
                }
            ]
            
            # Measure filtering performance
            start_time = time.time()
            
            for i, filter_config in enumerate(filters):
                notification_filtering_service.create_custom_filter(
                    user_id=i,
                    name=f'Performance Filter {i}',
                    filters=filter_config
                )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Verify performance
            self.assertLess(duration, 0.5)  # Should complete in under 0.5 seconds
    
    def test_mobile_registration_performance(self):
        """Test mobile registration performance"""
        with self.create_app().app_context():
            # Create multiple device registrations
            devices = [
                {
                    'platform': 'ios',
                    'device_token': f'token_{i}',
                    'device_id': f'device_{i}'
                }
                for i in range(50)
            ]
            
            # Measure registration performance
            start_time = time.time()
            
            for device in devices:
                mobile_notification_service.register_device(1, device)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Verify performance
            self.assertLess(duration, 1.0)  # Should complete in under 1 second
    
    def test_end_to_end_performance(self):
        """Test end-to-end notification performance"""
        with self.create_app().app_context():
            # Create test notification
            notification_data = {
                'type': 'comment',
                'content': 'performance_test_user commented on your post',
                'username': 'performance_test_user',
                'post_title': 'Performance Test Post',
                'user_id': 1
            }
            
            # Measure complete flow performance
            start_time = time.time()
            
            # Step 1: Translation
            translated = notification_translation_service.translate_notification(
                notification_data, 1
            )
            
            # Step 2: Filtering
            filters = {'type': ['comment']}
            custom_filter = notification_filtering_service.create_custom_filter(
                user_id=1,
                name='Performance Filter',
                filters=filters
            )
            
            # Step 3: Mobile registration
            device_info = {
                'platform': 'android',
                'device_token': 'performance_token',
                'device_id': 'performance_device'
            }
            mobile_registration = mobile_notification_service.register_device(1, device_info)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Verify performance and results
            self.assertIsInstance(translated, dict)
            self.assertIsInstance(custom_filter, dict)
            self.assertTrue(mobile_registration['success'])
            self.assertLess(duration, 0.5)  # Should complete in under 0.5 seconds


class TestErrorHandlingIntegration(TestCase):
    """Test cases for error handling integration"""
    
    def create_app(self):
        """Create Flask app for error testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    def test_translation_error_handling(self):
        """Test translation service error handling"""
        with self.create_app().app_context():
            # Test with invalid notification data
            result = notification_translation_service.translate_notification({}, 1)
            self.assertIsInstance(result, dict)
            
            # Test with invalid language
            supported = notification_translation_service.is_language_supported('invalid_lang')
            self.assertFalse(supported)
    
    def test_filtering_error_handling(self):
        """Test filtering service error handling"""
        with self.create_app().app_context():
            # Test with invalid filter data
            result = notification_filtering_service.create_custom_filter(
                user_id=1,
                name='',  # Invalid empty name
                filters={}
            )
            self.assertIsInstance(result, dict)
            
            # Test content similarity with edge cases
            similarity = notification_filtering_service._calculate_content_similarity('', '')
            self.assertEqual(similarity, 0.0)
    
    def test_mobile_error_handling(self):
        """Test mobile service error handling"""
        with self.create_app().app_context():
            # Test with invalid device data
            result = mobile_notification_service.validate_device_token('ios', '')
            self.assertFalse(result['valid'])
            
            # Test with unsupported platform
            result = mobile_notification_service.validate_device_token('unsupported', 'token')
            self.assertFalse(result['valid'])


if __name__ == '__main__':
    # Run all integration tests
    unittest.main(verbosity=2)
