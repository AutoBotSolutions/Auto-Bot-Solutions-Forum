"""
Comprehensive Notification System Unit Tests

This test suite provides comprehensive unit testing for all notification system
components including services, models, forms, and API endpoints.

Test Coverage:
- Translation Service
- Filtering Service  
- Mobile Service
- Notification Models
- Notification Forms
- API Endpoints
- Integration Scenarios
"""

import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask.testing import TestCase

# Import notification system components
from app.notifications.translation_service import notification_translation_service
from app.notifications.filtering_service import notification_filtering_service
from app.notifications.mobile_service import mobile_notification_service
from app.notifications.forms import (
    UserNotificationPreferencesForm,
    NotificationSearchAdvancedForm,
    NotificationArchiveForm,
    NotificationScheduleForm,
    NotificationGroupingForm
)
from app.notifications.models import (
    AdminNotification,
    NotificationTemplate,
    NotificationPreference,
    NotificationDelivery,
    NotificationCategory
)


class TestNotificationTranslationService(unittest.TestCase):
    """Test cases for notification translation service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_notification = {
            'type': 'comment',
            'content': 'john_doe commented on your post "Welcome to the Forum"',
            'username': 'john_doe',
            'post_title': 'Welcome to the Forum',
            'created_at': datetime.utcnow().isoformat()
        }
    
    def test_get_supported_languages(self):
        """Test getting supported languages"""
        languages = notification_translation_service.get_supported_languages()
        
        self.assertIsInstance(languages, dict)
        self.assertIn('en', languages)
        self.assertIn('es', languages)
        self.assertIn('fr', languages)
        self.assertEqual(len(languages), 12)
    
    def test_translate_notification(self):
        """Test notification translation"""
        result = notification_translation_service.translate_notification(
            self.test_notification, 
            1
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('type', result)
        self.assertIn('content', result)
        self.assertEqual(result['type'], self.test_notification['type'])
    
    def test_translate_bulk_notifications(self):
        """Test bulk notification translation"""
        notifications = [self.test_notification] * 3
        
        results = notification_translation_service.translate_bulk_notifications(
            notifications, 
            1
        )
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, dict)
            self.assertIn('type', result)
    
    def test_is_language_supported(self):
        """Test language support validation"""
        self.assertTrue(notification_translation_service.is_language_supported('en'))
        self.assertTrue(notification_translation_service.is_language_supported('es'))
        self.assertFalse(notification_translation_service.is_language_supported('invalid'))
    
    def test_set_user_language_preference(self):
        """Test setting user language preference"""
        result = notification_translation_service.set_user_language_preference(
            1, 
            'es'
        )
        
        self.assertIsInstance(result, bool)
        # Note: This would typically save to database, so we just test the method exists
    
    def test_translate_text(self):
        """Test text translation"""
        result = notification_translation_service.translate_text(
            "Hello world",
            'es',
            'en'
        )
        
        self.assertIsInstance(result, str)
        # Note: This would typically use a translation service, so we just test the method exists
    
    def test_get_translation_statistics(self):
        """Test translation statistics"""
        stats = notification_translation_service.get_translation_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('supported_languages', stats)
        self.assertIn('available_languages', stats)


class TestNotificationFilteringService(unittest.TestCase):
    """Test cases for notification filtering service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_filters = {
            'type': ['comment', 'message'],
            'priority': ['high', 'urgent'],
            'is_read': False,
            'date_range': 'last_7_days'
        }
    
    def test_get_filter_presets(self):
        """Test getting filter presets"""
        presets = notification_filtering_service.get_filter_presets()
        
        self.assertIsInstance(presets, dict)
        self.assertIn('unread_important', presets)
        self.assertIn('recent_comments', presets)
        self.assertEqual(len(presets), 5)
    
    def test_get_grouping_strategies(self):
        """Test getting grouping strategies"""
        strategies = notification_filtering_service.get_grouping_strategies()
        
        self.assertIsInstance(strategies, dict)
        self.assertIn('type', strategies)
        self.assertIn('priority', strategies)
        self.assertIn('content', strategies)
        self.assertEqual(len(strategies), 6)
    
    def test_create_custom_filter(self):
        """Test custom filter creation"""
        result = notification_filtering_service.create_custom_filter(
            user_id=1,
            name='Test Filter',
            filters=self.test_filters,
            sort_options={'sort_by': 'created_at'}
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('id', result)
        self.assertIn('name', result)
        self.assertEqual(result['name'], 'Test Filter')
    
    def test_calculate_content_similarity(self):
        """Test content similarity calculation"""
        similarity = notification_filtering_service._calculate_content_similarity(
            "Hello world",
            "Hello there world"
        )
        
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_group_notifications(self):
        """Test notification grouping"""
        # Mock notifications
        notifications = [
            Mock(type='comment', content='Comment 1'),
            Mock(type='comment', content='Comment 2'),
            Mock(type='message', content='Message 1')
        ]
        
        result = notification_filtering_service.group_notifications(
            notifications,
            'type'
        )
        
        self.assertIsInstance(result, list)
        # Note: This would typically query database, so we just test the method exists
    
    def test_analyze_notification_patterns(self):
        """Test pattern analysis"""
        result = notification_filtering_service.analyze_notification_patterns(
            user_id=1,
            days=30
        )
        
        self.assertIsInstance(result, dict)
        # Note: This would typically query database, so we just test the method exists


class TestMobileNotificationService(unittest.TestCase):
    """Test cases for mobile notification service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.device_info = {
            'platform': 'ios',
            'device_token': 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
            'device_id': 'test_device_123',
            'app_version': '1.0.0',
            'os_version': 'iOS 17.0',
            'device_model': 'iPhone 15'
        }
    
    def test_get_supported_platforms(self):
        """Test getting supported platforms"""
        platforms = mobile_notification_service.get_supported_platforms()
        
        self.assertIsInstance(platforms, dict)
        self.assertIn('ios', platforms)
        self.assertIn('android', platforms)
        self.assertIn('huawei', platforms)
        self.assertIn('web', platforms)
        self.assertEqual(len(platforms), 4)
    
    def test_get_notification_types(self):
        """Test getting notification types"""
        types = mobile_notification_service.get_notification_types()
        
        self.assertIsInstance(types, dict)
        self.assertIn('forum_activity', types)
        self.assertIn('messages', types)
        self.assertIn('security', types)
        self.assertEqual(len(types), 6)
    
    def test_validate_device_token(self):
        """Test device token validation"""
        # Test valid iOS token
        result = mobile_notification_service.validate_device_token(
            'ios',
            'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('valid', result)
        self.assertTrue(result['valid'])
        
        # Test invalid token
        result = mobile_notification_service.validate_device_token(
            'ios',
            'invalid'
        )
        
        self.assertFalse(result['valid'])
    
    def test_register_device(self):
        """Test device registration"""
        result = mobile_notification_service.register_device(1, self.device_info)
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('registration_id', result)
        self.assertTrue(result['success'])
    
    def test_unregister_device(self):
        """Test device unregistration"""
        result = mobile_notification_service.unregister_device(
            1,
            'test_registration_id'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        # Note: This would typically delete from database, so we just test the method exists
    
    def test_send_push_notification(self):
        """Test push notification sending"""
        notification_data = {
            'title': 'Test Notification',
            'message': 'This is a test',
            'type': 'system'
        }
        
        result = mobile_notification_service.send_push_notification(
            1,
            notification_data
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        # Note: This would typically send to APNS/FCM, so we just test the method exists
    
    def test_get_device_statistics(self):
        """Test device statistics"""
        stats = mobile_notification_service.get_device_statistics(1)
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_devices', stats)
        # Note: This would typically query database, so we just test the method exists


class TestNotificationForms(TestCase):
    """Test cases for notification forms"""
    
    def create_app(self):
        """Create Flask app for form testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    def test_user_notification_preferences_form(self):
        """Test user notification preferences form"""
        with self.create_app().app_context():
            form = UserNotificationPreferencesForm()
            
            # Test form fields exist
            self.assertTrue(hasattr(form, 'push_enabled'))
            self.assertTrue(hasattr(form, 'email_enabled'))
            self.assertTrue(hasattr(form, 'daily_digest_enabled'))
            self.assertTrue(hasattr(form, 'quiet_hours_enabled'))
            
            # Test form validation
            form_data = {
                'push_enabled': True,
                'email_enabled': True,
                'daily_digest_enabled': False,
                'quiet_hours_enabled': False
            }
            
            form = UserNotificationPreferencesForm(data=form_data)
            self.assertTrue(form.validate())
    
    def test_notification_search_advanced_form(self):
        """Test notification search advanced form"""
        with self.create_app().app_context():
            form = NotificationSearchAdvancedForm()
            
            # Test form fields exist
            self.assertTrue(hasattr(form, 'search_query'))
            self.assertTrue(hasattr(form, 'types'))
            self.assertTrue(hasattr(form, 'priorities'))
            self.assertTrue(hasattr(form, 'date_range'))
            
            # Test form validation
            form_data = {
                'search_query': 'test',
                'types': ['comment', 'message'],
                'priorities': ['high'],
                'date_range': 'last_7_days'
            }
            
            form = NotificationSearchAdvancedForm(data=form_data)
            self.assertTrue(form.validate())
    
    def test_notification_archive_form(self):
        """Test notification archive form"""
        with self.create_app().app_context():
            form = NotificationArchiveForm()
            
            # Test form fields exist
            self.assertTrue(hasattr(form, 'archive_read_older_than'))
            self.assertTrue(hasattr(form, 'archive_unread_older_than'))
            self.assertTrue(hasattr(form, 'keep_important'))
            
            # Test form validation
            form_data = {
                'archive_read_older_than': '90_days',
                'archive_unread_older_than': '365_days',
                'keep_important': True
            }
            
            form = NotificationArchiveForm(data=form_data)
            self.assertTrue(form.validate())
    
    def test_notification_schedule_form(self):
        """Test notification schedule form"""
        with self.create_app().app_context():
            form = NotificationScheduleForm()
            
            # Test form fields exist
            self.assertTrue(hasattr(form, 'quiet_hours_enabled'))
            self.assertTrue(hasattr(form, 'daily_digest_enabled'))
            self.assertTrue(hasattr(form, 'weekly_summary_enabled'))
            
            # Test form validation
            form_data = {
                'quiet_hours_enabled': True,
                'daily_digest_enabled': True,
                'weekly_summary_enabled': False,
                'weekday_start': '22:00',
                'weekday_end': '08:00'
            }
            
            form = NotificationScheduleForm(data=form_data)
            self.assertTrue(form.validate())
    
    def test_notification_grouping_form(self):
        """Test notification grouping form"""
        with self.create_app().app_context():
            form = NotificationGroupingForm()
            
            # Test form fields exist
            self.assertTrue(hasattr(form, 'enable_grouping'))
            self.assertTrue(hasattr(form, 'group_by_type'))
            self.assertTrue(hasattr(form, 'group_by_priority'))
            
            # Test form validation
            form_data = {
                'enable_grouping': True,
                'group_by_type': True,
                'group_by_priority': False,
                'max_group_size': 10
            }
            
            form = NotificationGroupingForm(data=form_data)
            self.assertTrue(form.validate())


class TestNotificationModels(TestCase):
    """Test cases for notification models"""
    
    def create_app(self):
        """Create Flask app for model testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        return app
    
    def test_admin_notification_model(self):
        """Test AdminNotification model"""
        with self.create_app().app_context():
            # Test model attributes
            self.assertTrue(hasattr(AdminNotification, 'id'))
            self.assertTrue(hasattr(AdminNotification, 'user_id'))
            self.assertTrue(hasattr(AdminNotification, 'title'))
            self.assertTrue(hasattr(AdminNotification, 'message'))
            self.assertTrue(hasattr(AdminNotification, 'notification_type'))
            self.assertTrue(hasattr(AdminNotification, 'priority'))
            self.assertTrue(hasattr(AdminNotification, 'is_read'))
            self.assertTrue(hasattr(AdminNotification, 'is_archived'))
            self.assertTrue(hasattr(AdminNotification, 'created_at'))
    
    def test_notification_template_model(self):
        """Test NotificationTemplate model"""
        with self.create_app().app_context():
            # Test model attributes
            self.assertTrue(hasattr(NotificationTemplate, 'id'))
            self.assertTrue(hasattr(NotificationTemplate, 'name'))
            self.assertTrue(hasattr(NotificationTemplate, 'subject_template'))
            self.assertTrue(hasattr(NotificationTemplate, 'content_template'))
            self.assertTrue(hasattr(NotificationTemplate, 'variables'))
            self.assertTrue(hasattr(NotificationTemplate, 'created_at'))
    
    def test_notification_preference_model(self):
        """Test NotificationPreference model"""
        with self.create_app().app_context():
            # Test model attributes
            self.assertTrue(hasattr(NotificationPreference, 'id'))
            self.assertTrue(hasattr(NotificationPreference, 'user_id'))
            self.assertTrue(hasattr(NotificationPreference, 'notification_type'))
            self.assertTrue(hasattr(NotificationPreference, 'enabled'))
            self.assertTrue(hasattr(NotificationPreference, 'frequency'))
            self.assertTrue(hasattr(NotificationPreference, 'created_at'))
    
    def test_notification_delivery_model(self):
        """Test NotificationDelivery model"""
        with self.create_app().app_context():
            # Test model attributes
            self.assertTrue(hasattr(NotificationDelivery, 'id'))
            self.assertTrue(hasattr(NotificationDelivery, 'notification_id'))
            self.assertTrue(hasattr(NotificationDelivery, 'delivery_type'))
            self.assertTrue(hasattr(NotificationDelivery, 'status'))
            self.assertTrue(hasattr(NotificationDelivery, 'sent_at'))
            self.assertTrue(hasattr(NotificationDelivery, 'error_message'))
    
    def test_notification_category_model(self):
        """Test NotificationCategory model"""
        with self.create_app().app_context():
            # Test model attributes
            self.assertTrue(hasattr(NotificationCategory, 'id'))
            self.assertTrue(hasattr(NotificationCategory, 'name'))
            self.assertTrue(hasattr(NotificationCategory, 'description'))
            self.assertTrue(hasattr(NotificationCategory, 'color'))
            self.assertTrue(hasattr(NotificationCategory, 'icon'))
            self.assertTrue(hasattr(NotificationCategory, 'created_at'))


class TestNotificationIntegration(TestCase):
    """Test cases for notification system integration"""
    
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
            # Test that both services can be imported and used together
            test_notifications = [
                {
                    'type': 'comment',
                    'content': 'john_doe commented on your post',
                    'username': 'john_doe'
                }
            ]
            
            # Apply translation
            translated = notification_translation_service.translate_bulk_notifications(
                test_notifications, 1
            )
            
            # Apply filtering
            filters = {'type': ['comment']}
            custom_filter = notification_filtering_service.create_custom_filter(
                user_id=1,
                name='Test Integration Filter',
                filters=filters
            )
            
            self.assertIsInstance(translated, list)
            self.assertIsInstance(custom_filter, dict)
    
    def test_mobile_filtering_integration(self):
        """Test mobile and filtering service integration"""
        with self.create_app().app_context():
            # Test device registration
            device_info = {
                'platform': 'ios',
                'device_token': 'test_token',
                'device_id': 'test_device',
                'notification_types': ['comment', 'message']
            }
            
            registration = mobile_notification_service.register_device(1, device_info)
            
            # Test filtering with mobile preferences
            filters = {'type': ['comment', 'message']}
            custom_filter = notification_filtering_service.create_custom_filter(
                user_id=1,
                name='Mobile Filter',
                filters=filters
            )
            
            self.assertTrue(registration['success'])
            self.assertIsInstance(custom_filter, dict)
    
    def test_service_error_handling(self):
        """Test error handling across services"""
        with self.create_app().app_context():
            # Test translation service error handling
            empty_result = notification_translation_service.translate_notification({}, 1)
            self.assertIsInstance(empty_result, dict)
            
            # Test filtering service error handling
            invalid_filter = notification_filtering_service.create_custom_filter(
                user_id=1,
                name='',  # Invalid empty name
                filters={}
            )
            self.assertIsInstance(invalid_filter, dict)
            
            # Test mobile service error handling
            invalid_token = mobile_notification_service.validate_device_token('ios', '')
            self.assertFalse(invalid_token['valid'])


class TestNotificationAPI(TestCase):
    """Test cases for notification API endpoints"""
    
    def create_app(self):
        """Create Flask app for API testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Import and register blueprint
        from app.notifications.routes import notifications_bp
        app.register_blueprint(notifications_bp)
        
        return app
    
    def test_translation_endpoints(self):
        """Test translation API endpoints"""
        with self.create_app().test_client() as client:
            # Test translation preferences endpoint
            response = client.get('/notifications/translation')
            self.assertEqual(response.status_code, 302)  # Redirect to login
            
            # Test translation API endpoint
            response = client.post('/notifications/translation/api/languages')
            self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_filtering_endpoints(self):
        """Test filtering API endpoints"""
        with self.create_app().test_client() as client:
            # Test filtering endpoint
            response = client.get('/notifications/filtering')
            self.assertEqual(response.status_code, 302)  # Redirect to login
            
            # Test filter presets endpoint
            response = client.get('/notifications/filtering/api/presets')
            self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_mobile_endpoints(self):
        """Test mobile API endpoints"""
        with self.create_app().test_client() as client:
            # Test mobile registration endpoint
            response = client.post('/notifications/mobile/register')
            self.assertEqual(response.status_code, 302)  # Redirect to login
            
            # Test mobile platforms endpoint
            response = client.get('/notifications/mobile/api/platforms')
            self.assertEqual(response.status_code, 302)  # Redirect to login


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
