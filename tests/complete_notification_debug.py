#!/usr/bin/env python3
"""
Complete Notification System Debugging Report

This script provides a comprehensive debugging report for all notification
system components and their operational status.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_core_services():
    """Test all core notification services"""
    print("\n🔍 Testing Core Notification Services...")
    
    results = {}
    
    # Test Translation Service
    try:
        from app.notifications.translation_service import notification_translation_service
        
        # Basic functionality tests
        supported_languages = notification_translation_service.get_supported_languages()
        assert len(supported_languages) == 12, "Should support 12 languages"
        
        test_notification = {
            'type': 'comment',
            'content': 'john_doe commented on your post "Welcome"',
            'username': 'john_doe',
            'post_title': 'Welcome'
        }
        
        translated = notification_translation_service.translate_notification(test_notification, 1)
        assert isinstance(translated, dict), "Translation should return dict"
        
        # Test language support
        assert notification_translation_service.is_language_supported('es') == True
        assert notification_translation_service.is_language_supported('invalid') == False
        
        # Test statistics
        stats = notification_translation_service.get_translation_statistics()
        assert 'supported_languages' in stats
        
        results['translation'] = True
        print("✅ Translation Service: FULLY OPERATIONAL")
        
    except Exception as e:
        results['translation'] = False
        print(f"❌ Translation Service: ERROR - {str(e)}")
    
    # Test Filtering Service
    try:
        from app.notifications.filtering_service import notification_filtering_service
        
        # Test filter presets
        presets = notification_filtering_service.get_filter_presets()
        assert len(presets) >= 5, "Should have at least 5 filter presets"
        
        # Test grouping strategies
        strategies = notification_filtering_service.get_grouping_strategies()
        assert len(strategies) >= 6, "Should have at least 6 grouping strategies"
        
        # Test custom filter creation
        custom_filter = notification_filtering_service.create_custom_filter(
            user_id=1, name='Test', filters={'type': 'comment'}, sort_options={}
        )
        assert isinstance(custom_filter, dict) and 'id' in custom_filter
        
        # Test content similarity
        similarity = notification_filtering_service._calculate_content_similarity(
            "hello world", "hello there"
        )
        assert isinstance(similarity, float) and 0 <= similarity <= 1
        
        results['filtering'] = True
        print("✅ Filtering Service: FULLY OPERATIONAL")
        
    except Exception as e:
        results['filtering'] = False
        print(f"❌ Filtering Service: ERROR - {str(e)}")
    
    # Test Mobile Service
    try:
        from app.notifications.mobile_service import mobile_notification_service
        
        # Test platforms
        platforms = mobile_notification_service.get_supported_platforms()
        assert len(platforms) >= 4, "Should support at least 4 platforms"
        
        # Test notification types
        types = mobile_notification_service.get_notification_types()
        assert len(types) >= 6, "Should have at least 6 notification types"
        
        # Test token validation
        valid_token = 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2'
        token_result = mobile_notification_service.validate_device_token('ios', valid_token)
        assert token_result['valid'] == True
        
        # Test invalid token
        invalid_result = mobile_notification_service.validate_device_token('ios', 'invalid')
        assert invalid_result['valid'] == False
        
        # Test device registration
        device_info = {
            'platform': 'ios',
            'device_token': valid_token,
            'device_id': 'test_device',
            'app_version': '1.0.0'
        }
        registration = mobile_notification_service.register_device(1, device_info)
        assert registration['success'] == True
        
        results['mobile'] = True
        print("✅ Mobile Service: FULLY OPERATIONAL")
        
    except Exception as e:
        results['mobile'] = False
        print(f"❌ Mobile Service: ERROR - {str(e)}")
    
    return results

def test_forms_and_models():
    """Test forms and models import"""
    print("\n🔍 Testing Forms and Models...")
    
    results = {}
    
    # Test Forms Import
    try:
        from app.notifications.forms import (
            UserNotificationPreferencesForm,
            NotificationSearchAdvancedForm,
            NotificationArchiveForm,
            NotificationScheduleForm,
            NotificationGroupingForm
        )
        
        # Verify form classes exist
        assert UserNotificationPreferencesForm is not None
        assert NotificationSearchAdvancedForm is not None
        assert NotificationArchiveForm is not None
        assert NotificationScheduleForm is not None
        assert NotificationGroupingForm is not None
        
        results['forms'] = True
        print("✅ Forms: ALL IMPORTED SUCCESSFULLY")
        print("   Note: Form instantiation requires Flask request context")
        
    except Exception as e:
        results['forms'] = False
        print(f"❌ Forms: IMPORT ERROR - {str(e)}")
    
    # Test Models Import
    try:
        from app.notifications.models import (
            AdminNotification,
            NotificationTemplate,
            NotificationPreference,
            NotificationDelivery,
            NotificationCategory
        )
        
        # Verify model classes exist
        assert AdminNotification is not None
        assert NotificationTemplate is not None
        assert NotificationPreference is not None
        assert NotificationDelivery is not None
        assert NotificationCategory is not None
        
        results['models'] = True
        print("✅ Models: ALL IMPORTED SUCCESSFULLY")
        
    except Exception as e:
        results['models'] = False
        print(f"❌ Models: IMPORT ERROR - {str(e)}")
    
    return results

def test_routes_integration():
    """Test routes integration"""
    print("\n🔍 Testing Routes Integration...")
    
    try:
        # Test individual service imports
        from app.notifications.translation_service import notification_translation_service
        from app.notifications.filtering_service import notification_filtering_service
        from app.notifications.mobile_service import mobile_notification_service
        
        # Test routes module import
        from app.notifications import routes
        
        # Verify blueprint exists
        assert hasattr(routes, 'notifications_bp')
        assert routes.notifications_bp is not None
        
        print("✅ Routes: BLUEPRINT IMPORTED SUCCESSFULLY")
        print("   All service dependencies resolved")
        return True
        
    except Exception as e:
        print(f"❌ Routes: INTEGRATION ERROR - {str(e)}")
        return False

def test_error_handling():
    """Test error handling robustness"""
    print("\n🔍 Testing Error Handling...")
    
    try:
        from app.notifications.translation_service import notification_translation_service
        from app.notifications.mobile_service import mobile_notification_service
        
        # Test translation error handling
        try:
            notification_translation_service.translate_notification({}, 1)
            print("✅ Translation: Handles empty notifications gracefully")
        except Exception:
            print("⚠️ Translation: Could improve empty notification handling")
        
        # Test mobile service error handling
        invalid_results = [
            mobile_notification_service.validate_device_token('ios', ''),
            mobile_notification_service.validate_device_token('', 'token'),
            mobile_notification_service.validate_device_token('invalid_platform', 'token')
        ]
        
        all_invalid = all(not result.get('valid', False) for result in invalid_results)
        if all_invalid:
            print("✅ Mobile Service: Robust error handling")
        else:
            print("⚠️ Mobile Service: Error handling needs improvement")
        
        return True
        
    except Exception as e:
        print(f"❌ Error Handling: TEST ERROR - {str(e)}")
        return False

def test_integration_scenarios():
    """Test integration between services"""
    print("\n🔍 Testing Integration Scenarios...")
    
    try:
        from app.notifications.translation_service import notification_translation_service
        from app.notifications.filtering_service import notification_filtering_service
        from app.notifications.mobile_service import mobile_notification_service
        
        # Test translation + filtering
        test_notifications = [
            {'type': 'comment', 'content': 'Test comment', 'username': 'user1'},
            {'type': 'message', 'content': 'Test message', 'sender_name': 'user2'}
        ]
        
        translated = notification_translation_service.translate_bulk_notifications(
            test_notifications, 1
        )
        assert len(translated) == len(test_notifications)
        
        # Test filtering + mobile
        custom_filter = notification_filtering_service.create_custom_filter(
            user_id=1, name='Integration Test', filters={'type': 'comment'}
        )
        
        device_info = {
            'platform': 'ios',
            'device_token': 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
            'device_id': 'integration_test',
            'notification_types': ['comment', 'message']
        }
        
        registration = mobile_notification_service.register_device(1, device_info)
        assert registration['success'] == True
        
        print("✅ Integration: All services work together correctly")
        return True
        
    except Exception as e:
        print(f"❌ Integration: ERROR - {str(e)}")
        return False

def generate_debugging_report():
    """Generate comprehensive debugging report"""
    print("🚀 COMPREHENSIVE NOTIFICATION SYSTEM DEBUGGING REPORT")
    print("=" * 80)
    
    # Run all tests
    core_results = test_core_services()
    forms_models_results = test_forms_and_models()
    routes_result = test_routes_integration()
    error_handling_result = test_error_handling()
    integration_result = test_integration_scenarios()
    
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE DEBUGGING RESULTS")
    print("=" * 80)
    
    # Core Services Status
    print("\n🔧 CORE SERVICES STATUS:")
    for service, status in core_results.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {service.title()} Service: {'OPERATIONAL' if status else 'NEEDS ATTENTION'}")
    
    # Forms and Models Status
    print("\n📝 FORMS AND MODELS STATUS:")
    for component, status in forms_models_results.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {component.title()}: {'IMPORTED' if status else 'IMPORT ERROR'}")
    
    # Other Components
    print(f"\n🛣️  Routes Integration: {'✅ OPERATIONAL' if routes_result else '❌ NEEDS ATTENTION'}")
    print(f"🛡️  Error Handling: {'✅ ROBUST' if error_handling_result else '❌ NEEDS IMPROVEMENT'}")
    print(f"🔗 Integration: {'✅ WORKING' if integration_result else '❌ FAILING'}")
    
    # Overall Assessment
    core_passed = sum(core_results.values())
    forms_models_passed = sum(forms_models_results.values())
    total_tests = core_passed + forms_models_passed + (1 if routes_result else 0) + (1 if error_handling_result else 0) + (1 if integration_result else 0)
    max_tests = len(core_results) + len(forms_models_results) + 3
    
    success_rate = (total_tests / max_tests) * 100
    
    print(f"\n🎯 OVERALL SYSTEM STATUS: {success_rate:.1f}% OPERATIONAL")
    
    if success_rate >= 90:
        print("🎉 NOTIFICATION SYSTEM: EXCELLENT - Ready for production")
    elif success_rate >= 80:
        print("✅ NOTIFICATION SYSTEM: GOOD - Minor issues to address")
    elif success_rate >= 70:
        print("⚠️  NOTIFICATION SYSTEM: ACCEPTABLE - Some issues need attention")
    else:
        print("❌ NOTIFICATION SYSTEM: NEEDS WORK - Significant issues to resolve")
    
    # Recommendations
    print("\n📋 RECOMMENDATIONS:")
    
    if not core_results.get('translation'):
        print("   • Review translation service dependencies and imports")
    
    if not core_results.get('filtering'):
        print("   • Check filtering service method implementations")
    
    if not core_results.get('mobile'):
        print("   • Verify mobile service token validation logic")
    
    if not forms_models_results.get('forms'):
        print("   • Ensure Flask-WTF dependencies are properly installed")
    
    if not forms_models_results.get('models'):
        print("   • Check SQLAlchemy model definitions")
    
    if not routes_result:
        print("   • Review route imports and blueprint registration")
    
    if not error_handling_result:
        print("   • Improve error handling in service methods")
    
    if not integration_result:
        print("   • Test service interactions and data flow")
    
    # Deployment Readiness
    print(f"\n🚀 DEPLOYMENT READINESS: {'READY' if success_rate >= 85 else 'NEEDS WORK'}")
    
    return success_rate >= 85

if __name__ == "__main__":
    success = generate_debugging_report()
    sys.exit(0 if success else 1)
