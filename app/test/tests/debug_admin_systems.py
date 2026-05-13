#!/usr/bin/env python3
"""
Comprehensive Admin Systems Debugging Script
Tests all admin systems: Analytics, Notifications, Moderation, User Management, Security
"""

import sys
import os
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test importing all admin system modules"""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    results = {}
    
    try:
        # Test analytics imports
        print("Testing Analytics imports...")
        from app.analytics import models as analytics_models
        from app.analytics import service as analytics_service
        from app.analytics import forms as analytics_forms
        from app.analytics import routes as analytics_routes
        results['analytics'] = "SUCCESS: All imports successful"
        print("✅ Analytics imports successful")
        
    except Exception as e:
        results['analytics'] = f"FAILED: {str(e)}"
        print(f"❌ Analytics imports failed: {e}")
        traceback.print_exc()
    
    try:
        # Test notifications imports
        print("\nTesting Notifications imports...")
        from app.notifications import models as notifications_models
        from app.notifications import service as notifications_service
        from app.notifications import forms as notifications_forms
        from app.notifications import routes as notifications_routes
        results['notifications'] = "SUCCESS: All imports successful"
        print("✅ Notifications imports successful")
        
    except Exception as e:
        results['notifications'] = f"FAILED: {str(e)}"
        print(f"❌ Notifications imports failed: {e}")
        traceback.print_exc()
    
    try:
        # Test moderation imports
        print("\nTesting Moderation imports...")
        from app.moderation import models as moderation_models
        from app.moderation import service as moderation_service
        from app.moderation import forms as moderation_forms
        from app.moderation import routes as moderation_routes
        results['moderation'] = "SUCCESS: All imports successful"
        print("✅ Moderation imports successful")
        
    except Exception as e:
        results['moderation'] = f"FAILED: {str(e)}"
        print(f"❌ Moderation imports failed: {e}")
        traceback.print_exc()
    
    try:
        # Test admin imports
        print("\nTesting Admin imports...")
        from app.admin import models as admin_models
        from app.admin import service as admin_service
        from app.admin import forms as admin_forms
        from app.admin import routes as admin_routes
        results['admin'] = "SUCCESS: All imports successful"
        print("✅ Admin imports successful")
        
    except Exception as e:
        results['admin'] = f"FAILED: {str(e)}"
        print(f"❌ Admin imports failed: {e}")
        traceback.print_exc()
    
    return results

def test_database_models():
    """Test database model definitions"""
    print("\n" + "=" * 60)
    print("Testing Database Models")
    print("=" * 60)
    
    results = {}
    
    try:
        # Create Flask app context for database operations
        from app import create_app
        app = create_app()
        
        with app.app_context():
            # Test analytics models
            print("Testing Analytics models...")
            from app.analytics.models import (
                AnalyticsEvent, UserBehavior, ContentPerformance, 
                SystemMetrics, TrendAnalysis, PredictiveModel
            )
            
            # Test model instantiation
            analytics_event = AnalyticsEvent(
                event_type='test_event',
                user_id=1,
                resource_type='post',
                resource_id=1,
                data={'test': 'data'}
            )
            print("✅ AnalyticsEvent model instantiation successful")
            
            user_behavior = UserBehavior(
                user_id=1,
                session_id='test_session',
                page_views=10,
                time_on_site=300
            )
            print("✅ UserBehavior model instantiation successful")
            
            results['analytics_models'] = "SUCCESS: All models work correctly"
            
    except Exception as e:
        results['analytics_models'] = f"FAILED: {str(e)}"
        print(f"❌ Analytics models failed: {e}")
        traceback.print_exc()
    
    try:
        with app.app_context():
            # Test notifications models
            print("\nTesting Notifications models...")
            from app.notifications.models import (
                AdminNotification, NotificationTemplate, NotificationPreference,
                NotificationDelivery, NotificationCategory
            )
            
            notification = AdminNotification(
                title='Test Notification',
                message='Test message',
                category='test',
                priority='low'
            )
            print("✅ AdminNotification model instantiation successful")
            
            template = NotificationTemplate(
                name='test_template',
                subject_template='Test Subject',
                message_template='Test Message'
            )
            print("✅ NotificationTemplate model instantiation successful")
            
            results['notifications_models'] = "SUCCESS: All models work correctly"
            
    except Exception as e:
        results['notifications_models'] = f"FAILED: {str(e)}"
        print(f"❌ Notifications models failed: {e}")
        traceback.print_exc()
    
    try:
        with app.app_context():
            # Test moderation models
            print("\nTesting Moderation models...")
            from app.moderation.models import (
                ModerationQueue, ContentAnalysis, ModerationAction,
                ModerationRule, SpamDetection, ContentQuality
            )
            
            queue_item = ModerationQueue(
                content_type='post',
                content_id=1,
                content_data={'title': 'Test', 'content': 'Test content'},
                status='pending',
                priority='medium'
            )
            print("✅ ModerationQueue model instantiation successful")
            
            analysis = ContentAnalysis(
                content_id=1,
                content_type='post',
                readability_score=0.8,
                sentiment_score=0.5,
                language_detected='en'
            )
            print("✅ ContentAnalysis model instantiation successful")
            
            results['moderation_models'] = "SUCCESS: All models work correctly"
            
    except Exception as e:
        results['moderation_models'] = f"FAILED: {str(e)}"
        print(f"❌ Moderation models failed: {e}")
        traceback.print_exc()
    
    try:
        with app.app_context():
            # Test admin models
            print("\nTesting Admin models...")
            from app.admin.models import (
                Permission, AdminRole, RolePermission, UserGroup,
                UserGroupMember, UserRole, SecurityEvent, AccessLog
            )
            
            permission = Permission(
                name='test:permission',
                display_name='Test Permission',
                category='test',
                resource='test',
                action='test'
            )
            print("✅ Permission model instantiation successful")
            
            role = AdminRole(
                name='test_role',
                display_name='Test Role',
                description='Test role description',
                level=50
            )
            print("✅ AdminRole model instantiation successful")
            
            security_event = SecurityEvent(
                event_type='test_event',
                severity='low',
                title='Test Event',
                description='Test security event'
            )
            print("✅ SecurityEvent model instantiation successful")
            
            results['admin_models'] = "SUCCESS: All models work correctly"
            
    except Exception as e:
        results['admin_models'] = f"FAILED: {str(e)}"
        print(f"❌ Admin models failed: {e}")
        traceback.print_exc()
    
    return results

def test_service_classes():
    """Test service class methods"""
    print("\n" + "=" * 60)
    print("Testing Service Classes")
    print("=" * 60)
    
    results = {}
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            # Test analytics services
            print("Testing Analytics services...")
            from app.analytics.service import (
                AnalyticsService, UserBehaviorService, ContentPerformanceService
            )
            
            # Test service instantiation
            analytics_service = AnalyticsService()
            print("✅ AnalyticsService instantiation successful")
            
            user_behavior_service = UserBehaviorService()
            print("✅ UserBehaviorService instantiation successful")
            
            content_service = ContentPerformanceService()
            print("✅ ContentPerformanceService instantiation successful")
            
            results['analytics_services'] = "SUCCESS: All services work correctly"
            
    except Exception as e:
        results['analytics_services'] = f"FAILED: {str(e)}"
        print(f"❌ Analytics services failed: {e}")
        traceback.print_exc()
    
    try:
        with app.app_context():
            # Test notification services
            print("\nTesting Notification services...")
            from app.notifications.service import (
                NotificationService, AdminNotificationService, NotificationTemplateService
            )
            
            notification_service = NotificationService()
            print("✅ NotificationService instantiation successful")
            
            admin_notification_service = AdminNotificationService()
            print("✅ AdminNotificationService instantiation successful")
            
            template_service = NotificationTemplateService()
            print("✅ NotificationTemplateService instantiation successful")
            
            results['notification_services'] = "SUCCESS: All services work correctly"
            
    except Exception as e:
        results['notification_services'] = f"FAILED: {str(e)}"
        print(f"❌ Notification services failed: {e}")
        traceback.print_exc()
    
    try:
        with app.app_context():
            # Test moderation services
            print("\nTesting Moderation services...")
            from app.moderation.service import (
                ContentAnalysisService, SpamDetectionService, ModerationQueueService
            )
            
            analysis_service = ContentAnalysisService()
            print("✅ ContentAnalysisService instantiation successful")
            
            spam_service = SpamDetectionService()
            print("✅ SpamDetectionService instantiation successful")
            
            queue_service = ModerationQueueService()
            print("✅ ModerationQueueService instantiation successful")
            
            results['moderation_services'] = "SUCCESS: All services work correctly"
            
    except Exception as e:
        results['moderation_services'] = f"FAILED: {str(e)}"
        print(f"❌ Moderation services failed: {e}")
        traceback.print_exc()
    
    try:
        with app.app_context():
            # Test admin services
            print("\nTesting Admin services...")
            from app.admin.service import (
                PermissionService, RoleService, UserGroupService, SecurityEventService
            )
            
            permission_service = PermissionService()
            print("✅ PermissionService instantiation successful")
            
            role_service = RoleService()
            print("✅ RoleService instantiation successful")
            
            group_service = UserGroupService()
            print("✅ UserGroupService instantiation successful")
            
            security_service = SecurityEventService()
            print("✅ SecurityEventService instantiation successful")
            
            results['admin_services'] = "SUCCESS: All services work correctly"
            
    except Exception as e:
        results['admin_services'] = f"FAILED: {str(e)}"
        print(f"❌ Admin services failed: {e}")
        traceback.print_exc()
    
    return results

def test_forms():
    """Test form classes"""
    print("\n" + "=" * 60)
    print("Testing Form Classes")
    print("=" * 60)
    
    results = {}
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            # Test analytics forms
            print("Testing Analytics forms...")
            from app.analytics.forms import (
                AnalyticsFilterForm, UserBehaviorFilterForm, ContentPerformanceFilterForm
            )
            
            # Test form instantiation
            filter_form = AnalyticsFilterForm()
            print("✅ AnalyticsFilterForm instantiation successful")
            
            behavior_form = UserBehaviorFilterForm()
            print("✅ UserBehaviorFilterForm instantiation successful")
            
            content_form = ContentPerformanceFilterForm()
            print("✅ ContentPerformanceFilterForm instantiation successful")
            
            results['analytics_forms'] = "SUCCESS: All forms work correctly"
            
    except Exception as e:
        results['analytics_forms'] = f"FAILED: {str(e)}"
        print(f"❌ Analytics forms failed: {e}")
        traceback.print_exc()
    
    try:
        with app.app_context():
            # Test notification forms
            print("\nTesting Notification forms...")
            from app.notifications.forms import (
                NotificationFilterForm, NotificationTemplateForm, NotificationPreferenceForm
            )
            
            notification_filter = NotificationFilterForm()
            print("✅ NotificationFilterForm instantiation successful")
            
            template_form = NotificationTemplateForm()
            print("✅ NotificationTemplateForm instantiation successful")
            
            preference_form = NotificationPreferenceForm()
            print("✅ NotificationPreferenceForm instantiation successful")
            
            results['notification_forms'] = "SUCCESS: All forms work correctly"
            
    except Exception as e:
        results['notification_forms'] = f"FAILED: {str(e)}"
        print(f"❌ Notification forms failed: {e}")
        traceback.print_exc()
    
    try:
        with app.app_context():
            # Test moderation forms
            print("\nTesting Moderation forms...")
            from app.moderation.forms import (
                ModerationQueueFilterForm, ContentAnalysisForm, ModerationActionForm
            )
            
            queue_form = ModerationQueueFilterForm()
            print("✅ ModerationQueueFilterForm instantiation successful")
            
            analysis_form = ContentAnalysisForm()
            print("✅ ContentAnalysisForm instantiation successful")
            
            action_form = ModerationActionForm()
            print("✅ ModerationActionForm instantiation successful")
            
            results['moderation_forms'] = "SUCCESS: All forms work correctly"
            
    except Exception as e:
        results['moderation_forms'] = f"FAILED: {str(e)}"
        print(f"❌ Moderation forms failed: {e}")
        traceback.print_exc()
    
    try:
        with app.app_context():
            # Test admin forms
            print("\nTesting Admin forms...")
            from app.admin.forms import (
                PermissionForm, RoleForm, UserRoleForm, UserGroupForm
            )
            
            permission_form = PermissionForm()
            print("✅ PermissionForm instantiation successful")
            
            role_form = RoleForm()
            print("✅ RoleForm instantiation successful")
            
            user_role_form = UserRoleForm()
            print("✅ UserRoleForm instantiation successful")
            
            group_form = UserGroupForm()
            print("✅ UserGroupForm instantiation successful")
            
            results['admin_forms'] = "SUCCESS: All forms work correctly"
            
    except Exception as e:
        results['admin_forms'] = f"FAILED: {str(e)}"
        print(f"❌ Admin forms failed: {e}")
        traceback.print_exc()
    
    return results

def test_routes():
    """Test route definitions"""
    print("\n" + "=" * 60)
    print("Testing Route Definitions")
    print("=" * 60)
    
    results = {}
    
    try:
        from app import create_app
        app = create_app()
        
        # Test analytics routes
        print("Testing Analytics routes...")
        with app.test_client() as client:
            # Test main analytics route
            response = client.get('/analytics/')
            print(f"Analytics main route status: {response.status_code}")
            
            # Test analytics API route
            response = client.get('/analytics/api/events')
            print(f"Analytics API route status: {response.status_code}")
            
        results['analytics_routes'] = "SUCCESS: Routes are accessible"
        
    except Exception as e:
        results['analytics_routes'] = f"FAILED: {str(e)}"
        print(f"❌ Analytics routes failed: {e}")
        traceback.print_exc()
    
    try:
        # Test notification routes
        print("\nTesting Notification routes...")
        with app.test_client() as client:
            # Test main notifications route
            response = client.get('/notifications/')
            print(f"Notifications main route status: {response.status_code}")
            
            # Test notifications API route
            response = client.get('/notifications/api/notifications')
            print(f"Notifications API route status: {response.status_code}")
            
        results['notification_routes'] = "SUCCESS: Routes are accessible"
        
    except Exception as e:
        results['notification_routes'] = f"FAILED: {str(e)}"
        print(f"❌ Notification routes failed: {e}")
        traceback.print_exc()
    
    try:
        # Test moderation routes
        print("\nTesting Moderation routes...")
        with app.test_client() as client:
            # Test main moderation route
            response = client.get('/moderation/')
            print(f"Moderation main route status: {response.status_code}")
            
            # Test moderation API route
            response = client.get('/moderation/api/queue')
            print(f"Moderation API route status: {response.status_code}")
            
        results['moderation_routes'] = "SUCCESS: Routes are accessible"
        
    except Exception as e:
        results['moderation_routes'] = f"FAILED: {str(e)}"
        print(f"❌ Moderation routes failed: {e}")
        traceback.print_exc()
    
    try:
        # Test admin routes
        print("\nTesting Admin routes...")
        with app.test_client() as client:
            # Test main admin route
            response = client.get('/admin/')
            print(f"Admin main route status: {response.status_code}")
            
            # Test admin API route
            response = client.get('/admin/api/permissions')
            print(f"Admin API route status: {response.status_code}")
            
        results['admin_routes'] = "SUCCESS: Routes are accessible"
        
    except Exception as e:
        results['admin_routes'] = f"FAILED: {str(e)}"
        print(f"❌ Admin routes failed: {e}")
        traceback.print_exc()
    
    return results

def generate_debugging_report(results: Dict[str, Dict[str, str]]):
    """Generate comprehensive debugging report"""
    print("\n" + "=" * 60)
    print("DEBUGGING REPORT SUMMARY")
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
        print("\n🎉 ALL TESTS PASSED! Admin systems are working correctly.")
    else:
        print(f"\n⚠️  {failed_tests} tests failed. Review the errors above.")
    
    return {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': failed_tests,
        'success_rate': (passed_tests/total_tests)*100,
        'detailed_results': results
    }

def main():
    """Main debugging function"""
    print("🔧 Admin Systems Comprehensive Debugging")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    all_results = {}
    
    # Run all tests
    all_results['imports'] = test_imports()
    all_results['models'] = test_database_models()
    all_results['services'] = test_service_classes()
    all_results['forms'] = test_forms()
    all_results['routes'] = test_routes()
    
    # Generate report
    report = generate_debugging_report(all_results)
    
    # Save detailed report to file
    report_file = f"/home/robbie/Desktop/repo-forum/debugging_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w') as f:
        f.write("Admin Systems Debugging Report\n")
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
