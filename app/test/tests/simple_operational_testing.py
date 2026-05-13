#!/usr/bin/env python3
"""
Simple Operational Testing Script for Admin Systems
Tests individual components without requiring Flask app initialization
"""

import sys
import os
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_analytics_models():
    """Test analytics model definitions"""
    print("=" * 60)
    print("Testing Analytics Models")
    print("=" * 60)
    
    results = {}
    
    try:
        # Test importing analytics models
        print("Testing Analytics model imports...")
        
        # Test basic imports
        import app.analytics.models as analytics_models
        
        # Check if model classes exist
        if hasattr(analytics_models, 'AnalyticsEvent'):
            print("✅ AnalyticsEvent model found")
            results['analytics_event_model'] = "SUCCESS: AnalyticsEvent model exists"
        else:
            results['analytics_event_model'] = "FAILED: AnalyticsEvent model not found"
        
        if hasattr(analytics_models, 'UserBehavior'):
            print("✅ UserBehavior model found")
            results['user_behavior_model'] = "SUCCESS: UserBehavior model exists"
        else:
            results['user_behavior_model'] = "FAILED: UserBehavior model not found"
        
        if hasattr(analytics_models, 'ContentPerformance'):
            print("✅ ContentPerformance model found")
            results['content_performance_model'] = "SUCCESS: ContentPerformance model exists"
        else:
            results['content_performance_model'] = "FAILED: ContentPerformance model not found"
        
        if hasattr(analytics_models, 'SystemMetrics'):
            print("✅ SystemMetrics model found")
            results['system_metrics_model'] = "SUCCESS: SystemMetrics model exists"
        else:
            results['system_metrics_model'] = "FAILED: SystemMetrics model not found"
        
        if hasattr(analytics_models, 'TrendAnalysis'):
            print("✅ TrendAnalysis model found")
            results['trend_analysis_model'] = "SUCCESS: TrendAnalysis model exists"
        else:
            results['trend_analysis_model'] = "FAILED: TrendAnalysis model not found"
        
        if hasattr(analytics_models, 'PredictiveModel'):
            print("✅ PredictiveModel model found")
            results['predictive_model_model'] = "SUCCESS: PredictiveModel exists"
        else:
            results['predictive_model_model'] = "FAILED: PredictiveModel not found"
        
        # Test model structure
        print("\nTesting Analytics model structure...")
        analytics_event_class = getattr(analytics_models, 'AnalyticsEvent', None)
        if analytics_event_class:
            # Check for key attributes
            required_fields = ['event_type', 'event_category', 'user_id', 'target_type', 'target_id']
            for field in required_fields:
                if hasattr(analytics_event_class, field):
                    print(f"✅ AnalyticsEvent.{field} attribute found")
                else:
                    print(f"❌ AnalyticsEvent.{field} attribute missing")
        
    except Exception as e:
        results['analytics_models'] = f"FAILED: {str(e)}"
        print(f"❌ Analytics models test failed: {e}")
        traceback.print_exc()
    
    return results

def test_notifications_models():
    """Test notifications model definitions"""
    print("\n" + "=" * 60)
    print("Testing Notifications Models")
    print("=" * 60)
    
    results = {}
    
    try:
        print("Testing Notifications model imports...")
        
        import app.notifications.models as notifications_models
        
        # Check if model classes exist
        if hasattr(notifications_models, 'AdminNotification'):
            print("✅ AdminNotification model found")
            results['admin_notification_model'] = "SUCCESS: AdminNotification model exists"
        else:
            results['admin_notification_model'] = "FAILED: AdminNotification model not found"
        
        if hasattr(notifications_models, 'NotificationTemplate'):
            print("✅ NotificationTemplate model found")
            results['notification_template_model'] = "SUCCESS: NotificationTemplate model exists"
        else:
            results['notification_template_model'] = "FAILED: NotificationTemplate model not found"
        
        if hasattr(notifications_models, 'NotificationPreference'):
            print("✅ NotificationPreference model found")
            results['notification_preference_model'] = "SUCCESS: NotificationPreference model exists"
        else:
            results['notification_preference_model'] = "FAILED: NotificationPreference model not found"
        
        if hasattr(notifications_models, 'NotificationDelivery'):
            print("✅ NotificationDelivery model found")
            results['notification_delivery_model'] = "SUCCESS: NotificationDelivery model exists"
        else:
            results['notification_delivery_model'] = "FAILED: NotificationDelivery model not found"
        
        if hasattr(notifications_models, 'NotificationCategory'):
            print("✅ NotificationCategory model found")
            results['notification_category_model'] = "SUCCESS: NotificationCategory model exists"
        else:
            results['notification_category_model'] = "FAILED: NotificationCategory model not found"
        
    except Exception as e:
        results['notifications_models'] = f"FAILED: {str(e)}"
        print(f"❌ Notifications models test failed: {e}")
        traceback.print_exc()
    
    return results

def test_moderation_models():
    """Test moderation model definitions"""
    print("\n" + "=" * 60)
    print("Testing Moderation Models")
    print("=" * 60)
    
    results = {}
    
    try:
        print("Testing Moderation model imports...")
        
        import app.moderation.models as moderation_models
        
        # Check if model classes exist
        if hasattr(moderation_models, 'ModerationQueue'):
            print("✅ ModerationQueue model found")
            results['moderation_queue_model'] = "SUCCESS: ModerationQueue model exists"
        else:
            results['moderation_queue_model'] = "FAILED: ModerationQueue model not found"
        
        if hasattr(moderation_models, 'ContentAnalysis'):
            print("✅ ContentAnalysis model found")
            results['content_analysis_model'] = "SUCCESS: ContentAnalysis model exists"
        else:
            results['content_analysis_model'] = "FAILED: ContentAnalysis model not found"
        
        if hasattr(moderation_models, 'ModerationAction'):
            print("✅ ModerationAction model found")
            results['moderation_action_model'] = "SUCCESS: ModerationAction model exists"
        else:
            results['moderation_action_model'] = "FAILED: ModerationAction model not found"
        
        if hasattr(moderation_models, 'SpamDetection'):
            print("✅ SpamDetection model found")
            results['spam_detection_model'] = "SUCCESS: SpamDetection model exists"
        else:
            results['spam_detection_model'] = "FAILED: SpamDetection model not found"
        
        if hasattr(moderation_models, 'ContentQuality'):
            print("✅ ContentQuality model found")
            results['content_quality_model'] = "SUCCESS: ContentQuality model exists"
        else:
            results['content_quality_model'] = "FAILED: ContentQuality model not found"
        
        if hasattr(moderation_models, 'ModerationRule'):
            print("✅ ModerationRule model found")
            results['moderation_rule_model'] = "SUCCESS: ModerationRule model exists"
        else:
            results['moderation_rule_model'] = "FAILED: ModerationRule model not found"
        
        if hasattr(moderation_models, 'ModerationHistory'):
            print("✅ ModerationHistory model found")
            results['moderation_history_model'] = "SUCCESS: ModerationHistory model exists"
        else:
            results['moderation_history_model'] = "FAILED: ModerationHistory model not found"
        
        if hasattr(moderation_models, 'ModerationPattern'):
            print("✅ ModerationPattern model found")
            results['moderation_pattern_model'] = "SUCCESS: ModerationPattern model exists"
        else:
            results['moderation_pattern_model'] = "FAILED: ModerationPattern model not found"
        
    except Exception as e:
        results['moderation_models'] = f"FAILED: {str(e)}"
        print(f"❌ Moderation models test failed: {e}")
        traceback.print_exc()
    
    return results

def test_admin_models():
    """Test admin model definitions"""
    print("\n" + "=" * 60)
    print("Testing Admin Models")
    print("=" * 60)
    
    results = {}
    
    try:
        print("Testing Admin model imports...")
        
        import app.admin.models as admin_models
        
        # Check if model classes exist
        if hasattr(admin_models, 'Permission'):
            print("✅ Permission model found")
            results['permission_model'] = "SUCCESS: Permission model exists"
        else:
            results['permission_model'] = "FAILED: Permission model not found"
        
        if hasattr(admin_models, 'AdminRole'):
            print("✅ AdminRole model found")
            results['admin_role_model'] = "SUCCESS: AdminRole model exists"
        else:
            results['admin_role_model'] = "FAILED: AdminRole model not found"
        
        if hasattr(admin_models, 'RolePermission'):
            print("✅ RolePermission model found")
            results['role_permission_model'] = "SUCCESS: RolePermission model exists"
        else:
            results['role_permission_model'] = "FAILED: RolePermission model not found"
        
        if hasattr(admin_models, 'UserRole'):
            print("✅ UserRole model found")
            results['user_role_model'] = "SUCCESS: UserRole model exists"
        else:
            results['user_role_model'] = "FAILED: UserRole model not found"
        
        if hasattr(admin_models, 'UserGroup'):
            print("✅ UserGroup model found")
            results['user_group_model'] = "SUCCESS: UserGroup model exists"
        else:
            results['user_group_model'] = "FAILED: UserGroup model not found"
        
        if hasattr(admin_models, 'UserGroupMember'):
            print("✅ UserGroupMember model found")
            results['user_group_member_model'] = "SUCCESS: UserGroupMember model exists"
        else:
            results['user_group_member_model'] = "FAILED: UserGroupMember model not found"
        
        if hasattr(admin_models, 'SecurityEvent'):
            print("✅ SecurityEvent model found")
            results['security_event_model'] = "SUCCESS: SecurityEvent model exists"
        else:
            results['security_event_model'] = "FAILED: SecurityEvent model not found"
        
        if hasattr(admin_models, 'AccessLog'):
            print("✅ AccessLog model found")
            results['access_log_model'] = "SUCCESS: AccessLog model exists"
        else:
            results['access_log_model'] = "FAILED: AccessLog model not found"
        
    except Exception as e:
        results['admin_models'] = f"FAILED: {str(e)}"
        print(f"❌ Admin models test failed: {e}")
        traceback.print_exc()
    
    return results

def test_service_imports():
    """Test service class imports"""
    print("\n" + "=" * 60)
    print("Testing Service Class Imports")
    print("=" * 60)
    
    results = {}
    
    try:
        print("Testing Analytics service imports...")
        
        try:
            import app.analytics.service as analytics_service
            print("✅ Analytics service module imported successfully")
            results['analytics_service_import'] = "SUCCESS: Analytics service module imported"
        except Exception as e:
            results['analytics_service_import'] = f"FAILED: {str(e)}"
        
        # Test service classes
        try:
            from app.analytics.service import AnalyticsService
            print("✅ AnalyticsService class found")
            results['analytics_service_class'] = "SUCCESS: AnalyticsService class exists"
        except Exception as e:
            results['analytics_service_class'] = f"FAILED: {str(e)}"
        
        print("\nTesting Notifications service imports...")
        
        try:
            import app.notifications.service as notifications_service
            print("✅ Notifications service module imported successfully")
            results['notifications_service_import'] = "SUCCESS: Notifications service module imported"
        except Exception as e:
            results['notifications_service_import'] = f"FAILED: {str(e)}"
        
        try:
            from app.notifications.service import NotificationService
            print("✅ NotificationService class found")
            results['notification_service_class'] = "SUCCESS: NotificationService class exists"
        except Exception as e:
            results['notification_service_class'] = f"FAILED: {str(e)}"
        
        print("\nTesting Moderation service imports...")
        
        try:
            import app.moderation.service as moderation_service
            print("✅ Moderation service module imported successfully")
            results['moderation_service_import'] = "SUCCESS: Moderation service module imported"
        except Exception as e:
            results['moderation_service_import'] = f"FAILED: {str(e)}"
        
        try:
            from app.moderation.service import ContentAnalysisService
            print("✅ ContentAnalysisService class found")
            results['content_analysis_service_class'] = "SUCCESS: ContentAnalysisService class exists"
        except Exception as e:
            results['content_analysis_service_class'] = f"FAILED: {str(e)}"
        
        print("\nTesting Admin service imports...")
        
        try:
            import app.admin.service as admin_service
            print("✅ Admin service module imported successfully")
            results['admin_service_import'] = "SUCCESS: Admin service module imported"
        except Exception as e:
            results['admin_service_import'] = f"FAILED: {str(e)}"
        
        try:
            from app.admin.service import PermissionService
            print("✅ PermissionService class found")
            results['permission_service_class'] = "SUCCESS: PermissionService class exists"
        except Exception as e:
            results['permission_service_class'] = f"FAILED: {str(e)}"
        
    except Exception as e:
        results['service_imports'] = f"FAILED: {str(e)}"
        print(f"❌ Service imports test failed: {e}")
        traceback.print_exc()
    
    return results

def test_form_imports():
    """Test form class imports"""
    print("\n" + "=" * 60)
    print("Testing Form Class Imports")
    print("=" * 60)
    
    results = {}
    
    try:
        print("Testing Analytics form imports...")
        
        try:
            import app.analytics.forms as analytics_forms
            print("✅ Analytics forms module imported successfully")
            results['analytics_forms_import'] = "SUCCESS: Analytics forms module imported"
        except Exception as e:
            results['analytics_forms_import'] = f"FAILED: {str(e)}"
        
        try:
            from app.analytics.forms import AnalyticsFilterForm
            print("✅ AnalyticsFilterForm class found")
            results['analytics_filter_form'] = "SUCCESS: AnalyticsFilterForm class exists"
        except Exception as e:
            results['analytics_filter_form'] = f"FAILED: {str(e)}"
        
        print("\nTesting Notifications form imports...")
        
        try:
            import app.notifications.forms as notifications_forms
            print("✅ Notifications forms module imported successfully")
            results['notifications_forms_import'] = "SUCCESS: Notifications forms module imported"
        except Exception as e:
            results['notifications_forms_import'] = f"FAILED: {str(e)}"
        
        try:
            from app.notifications.forms import NotificationFilterForm
            print("✅ NotificationFilterForm class found")
            results['notification_filter_form'] = "SUCCESS: NotificationFilterForm class exists"
        except Exception as e:
            results['notification_filter_form'] = f"FAILED: {str(e)}"
        
        print("\nTesting Moderation form imports...")
        
        try:
            import app.moderation.forms as moderation_forms
            print("✅ Moderation forms module imported successfully")
            results['moderation_forms_import'] = "SUCCESS: Moderation forms module imported"
        except Exception as e:
            results['moderation_forms_import'] = f"FAILED: {str(e)}"
        
        try:
            from app.moderation.forms import ModerationQueueFilterForm
            print("✅ ModerationQueueFilterForm class found")
            results['moderation_queue_filter_form'] = "SUCCESS: ModerationQueueFilterForm class exists"
        except Exception as e:
            results['moderation_queue_filter_form'] = f"FAILED: {str(e)}"
        
        print("\nTesting Admin form imports...")
        
        try:
            import app.admin.forms as admin_forms
            print("✅ Admin forms module imported successfully")
            results['admin_forms_import'] = "SUCCESS: Admin forms module imported"
        except Exception as e:
            results['admin_forms_import'] = f"FAILED: {str(e)}"
        
        try:
            from app.admin.forms import PermissionForm
            print("✅ PermissionForm class found")
            results['permission_form'] = "SUCCESS: PermissionForm class exists"
        except Exception as e:
            results['permission_form'] = f"FAILED: {str(e)}"
        
    except Exception as e:
        results['form_imports'] = f"FAILED: {str(e)}"
        print(f"❌ Form imports test failed: {e}")
        traceback.print_exc()
    
    return results

def test_file_structure():
    """Test if all required files exist"""
    print("\n" + "=" * 60)
    print("Testing File Structure")
    print("=" * 60)
    
    results = {}
    
    # Test analytics files
    analytics_files = [
        'app/analytics/__init__.py',
        'app/analytics/models.py',
        'app/analytics/service.py',
        'app/analytics/forms.py',
        'app/analytics/routes.py'
    ]
    
    print("Testing Analytics files...")
    for file_path in analytics_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
            results[f'analytics_file_{file_path.split("/")[-1]}'] = "SUCCESS: File exists"
        else:
            print(f"❌ {file_path} missing")
            results[f'analytics_file_{file_path.split("/")[-1]}'] = "FAILED: File missing"
    
    # Test notifications files
    notifications_files = [
        'app/notifications/__init__.py',
        'app/notifications/models.py',
        'app/notifications/service.py',
        'app/notifications/forms.py',
        'app/notifications/routes.py'
    ]
    
    print("\nTesting Notifications files...")
    for file_path in notifications_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
            results[f'notifications_file_{file_path.split("/")[-1]}'] = "SUCCESS: File exists"
        else:
            print(f"❌ {file_path} missing")
            results[f'notifications_file_{file_path.split("/")[-1]}'] = "FAILED: File missing"
    
    # Test moderation files
    moderation_files = [
        'app/moderation/__init__.py',
        'app/moderation/models.py',
        'app/moderation/service.py',
        'app/moderation/forms.py',
        'app/moderation/routes.py'
    ]
    
    print("\nTesting Moderation files...")
    for file_path in moderation_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
            results[f'moderation_file_{file_path.split("/")[-1]}'] = "SUCCESS: File exists"
        else:
            print(f"❌ {file_path} missing")
            results[f'moderation_file_{file_path.split("/")[-1]}'] = "FAILED: File missing"
    
    # Test admin files
    admin_files = [
        'app/admin/models.py',
        'app/admin/service.py',
        'app/admin/forms.py',
        'app/admin/routes.py'
    ]
    
    print("\nTesting Admin files...")
    for file_path in admin_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
            results[f'admin_file_{file_path.split("/")[-1]}'] = "SUCCESS: File exists"
        else:
            print(f"❌ {file_path} missing")
            results[f'admin_file_{file_path.split("/")[-1]}'] = "FAILED: File missing"
    
    return results

def generate_simple_report(results: Dict[str, Dict[str, str]]):
    """Generate comprehensive operational testing report"""
    print("\n" + "=" * 60)
    print("SIMPLE OPERATIONAL TESTING REPORT")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for category, tests in results.items():
        print(f"\n{category.upper()}:")
        for test_name, result in tests.items():
            total_tests += 1
            if "SUCCESS" in result:
                passed_tests += 1
                print(f"  ✅ {test_name}: {result}")
            else:
                failed_tests += 1
                print(f"  ❌ {test_name}: {result}")
    
    print(f"\n" + "=" * 60)
    print("OVERALL RESULTS")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! Admin systems are properly structured.")
        print("\n✅ System Status: CODE STRUCTURE VERIFIED")
        print("✅ All admin system files exist")
        print("✅ All model classes defined")
        print("✅ All service classes importable")
        print("✅ All form classes importable")
        print("✅ File structure complete")
        print("\n⚠️  Note: Runtime testing requires fixing Python environment issue")
        print("      (email.utils module compatibility with Python 3.13.5)")
    else:
        print(f"\n⚠️  {failed_tests} tests failed. Review the errors above.")
        print("Some components may need attention.")
    
    return {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': failed_tests,
        'success_rate': (passed_tests/total_tests)*100,
        'detailed_results': results
    }

def main():
    """Main operational testing function"""
    print("🔧 Admin Systems Simple Operational Testing")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    all_results = {}
    
    # Run all tests
    all_results['file_structure'] = test_file_structure()
    all_results['analytics_models'] = test_analytics_models()
    all_results['notifications_models'] = test_notifications_models()
    all_results['moderation_models'] = test_moderation_models()
    all_results['admin_models'] = test_admin_models()
    all_results['service_imports'] = test_service_imports()
    all_results['form_imports'] = test_form_imports()
    
    # Generate report
    report = generate_simple_report(all_results)
    
    # Save detailed report to file
    report_file = f"/home/robbie/Desktop/repo-forum/simple_operational_testing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w') as f:
        f.write("Admin Systems Simple Operational Testing Report\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write("=" * 60 + "\n\n")
        
        for category, tests in all_results.items():
            f.write(f"{category.upper()}:\n")
            for test_name, result in tests.items():
                f.write(f"  {test_name}: {result}\n")
            f.write("\n")
        
        f.write("=" * 60 + "\n")
        f.write(f"Total Tests: {report['total_tests']}\n")
        f.write(f"Passed: {report['passed_tests']}\n")
        f.write(f"Failed: {report['failed_tests']}\n")
        f.write(f"Success Rate: {report['success_rate']:.1f}%\n")
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    main()
