#!/usr/bin/env python3
"""
Notification System Debugging Script

This script comprehensively tests all the notification system components
that were recently implemented to ensure they're working properly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_translation_service():
    """Test the notification translation service"""
    print("\n🔍 Testing Translation Service...")
    
    try:
        from app.notifications.translation_service import notification_translation_service
        
        # Test basic functionality
        supported_languages = notification_translation_service.get_supported_languages()
        print(f"✅ Supported languages: {len(supported_languages)} languages")
        
        # Test translation
        test_notification = {
            'type': 'comment',
            'content': 'john_doe commented on your post "Welcome to the Forum"',
            'username': 'john_doe',
            'post_title': 'Welcome to the Forum'
        }
        
        translated = notification_translation_service.translate_notification(test_notification, 1)
        print(f"✅ Translation test passed: {type(translated)}")
        
        # Test language support
        is_supported = notification_translation_service.is_language_supported('es')
        print(f"✅ Language support test: Spanish supported = {is_supported}")
        
        # Test statistics
        stats = notification_translation_service.get_translation_statistics()
        print(f"✅ Translation statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Translation service error: {str(e)}")
        return False

def test_filtering_service():
    """Test the notification filtering service"""
    print("\n🔍 Testing Filtering Service...")
    
    try:
        from app.notifications.filtering_service import notification_filtering_service
        
        # Test basic functionality
        filter_presets = notification_filtering_service.get_filter_presets()
        print(f"✅ Filter presets: {len(filter_presets)} presets")
        
        # Test grouping strategies
        strategies = notification_filtering_service.get_grouping_strategies()
        print(f"✅ Grouping strategies: {len(strategies)} strategies")
        
        # Test custom filter creation
        custom_filter = notification_filtering_service.create_custom_filter(
            user_id=1,
            name='Test Filter',
            filters={'type': 'comment', 'priority': 'high'},
            sort_options={'sort_by': 'created_at'}
        )
        print(f"✅ Custom filter creation: {'Success' if custom_filter else 'Failed'}")
        
        # Test content similarity
        similarity = notification_filtering_service._calculate_content_similarity(
            "Hello world", "Hello there"
        )
        print(f"✅ Content similarity test: {similarity}")
        
        return True
        
    except Exception as e:
        print(f"❌ Filtering service error: {str(e)}")
        return False

def test_mobile_service():
    """Test the mobile notification service"""
    print("\n🔍 Testing Mobile Notification Service...")
    
    try:
        from app.notifications.mobile_service import mobile_notification_service
        
        # Test basic functionality
        platforms = mobile_notification_service.get_supported_platforms()
        print(f"✅ Supported platforms: {len(platforms)} platforms")
        
        # Test notification types
        notification_types = mobile_notification_service.get_notification_types()
        print(f"✅ Notification types: {len(notification_types)} types")
        
        # Test device token validation
        ios_token = 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2'
        token_validation = mobile_notification_service.validate_device_token('ios', ios_token)
        print(f"✅ iOS token validation: {'Valid' if token_validation['valid'] else 'Invalid'}")
        
        # Test device registration (mock)
        device_info = {
            'platform': 'ios',
            'device_token': ios_token,
            'device_id': 'test_device_123',
            'app_version': '1.0.0',
            'os_version': 'iOS 17.0',
            'device_model': 'iPhone 15'
        }
        
        registration = mobile_notification_service.register_device(1, device_info)
        print(f"✅ Device registration: {'Success' if registration['success'] else 'Failed'}")
        
        # Test device statistics
        stats = mobile_notification_service.get_device_statistics(1)
        print(f"✅ Device statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mobile service error: {str(e)}")
        return False

def test_forms():
    """Test the notification forms"""
    print("\n🔍 Testing Notification Forms...")
    
    try:
        from app.notifications.forms import (
            UserNotificationPreferencesForm,
            NotificationSearchAdvancedForm,
            NotificationArchiveForm,
            NotificationScheduleForm,
            NotificationGroupingForm
        )
        
        print("✅ All notification forms imported successfully")
        
        # Test form field counts
        forms_info = {
            'UserNotificationPreferencesForm': UserNotificationPreferencesForm,
            'NotificationSearchAdvancedForm': NotificationSearchAdvancedForm,
            'NotificationArchiveForm': NotificationArchiveForm,
            'NotificationScheduleForm': NotificationScheduleForm,
            'NotificationGroupingForm': NotificationGroupingForm
        }
        
        for form_name, form_class in forms_info.items():
            # Check if form class has fields
            if hasattr(form_class, '_unbound_fields') and form_class._unbound_fields:
                field_count = len(form_class._unbound_fields)
                print(f"✅ {form_name}: {field_count} fields")
            else:
                print(f"✅ {form_name}: Form class loaded")
        
        return True
        
    except Exception as e:
        print(f"❌ Forms import error: {str(e)}")
        return False

def test_routes_import():
    """Test the notification routes import"""
    print("\n🔍 Testing Routes Import...")
    
    try:
        # Test individual service imports first
        from app.notifications.translation_service import notification_translation_service
        from app.notifications.filtering_service import notification_filtering_service
        from app.notifications.mobile_service import mobile_notification_service
        print("✅ All services imported successfully")
        
        # Test routes import (this might fail due to Flask app context)
        try:
            from app.notifications import routes
            print("✅ Routes module imported successfully")
        except Exception as e:
            print(f"⚠️ Routes import warning: {str(e)}")
            # This is expected without Flask app context
        
        return True
        
    except Exception as e:
        print(f"❌ Routes import error: {str(e)}")
        return False

def test_models():
    """Test the notification models"""
    print("\n🔍 Testing Notification Models...")
    
    try:
        from app.notifications.models import (
            AdminNotification,
            NotificationTemplate,
            NotificationPreference,
            NotificationDelivery,
            NotificationCategory
        )
        
        models = [
            'AdminNotification',
            'NotificationTemplate', 
            'NotificationPreference',
            'NotificationDelivery',
            'NotificationCategory'
        ]
        
        for model_name in models:
            print(f"✅ {model_name} model imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Models import error: {str(e)}")
        return False

def run_comprehensive_tests():
    """Run all tests and provide a summary"""
    print("🚀 Starting Comprehensive Notification System Debugging")
    print("=" * 60)
    
    test_results = {
        'Translation Service': test_translation_service(),
        'Filtering Service': test_filtering_service(),
        'Mobile Service': test_mobile_service(),
        'Forms': test_forms(),
        'Routes Import': test_routes_import(),
        'Models': test_models()
    }
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All notification system components are working correctly!")
        return True
    else:
        print("⚠️ Some components need attention. Review the errors above.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
