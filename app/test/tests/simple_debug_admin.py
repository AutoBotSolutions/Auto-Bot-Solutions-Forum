#!/usr/bin/env python3
"""
Simple Admin Systems Debugging Script
Focus on core functionality without complex dependencies
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_basic_imports():
    """Test basic imports without Flask context"""
    print("=" * 60)
    print("Testing Basic Module Imports")
    print("=" * 60)
    
    results = {}
    
    # Test analytics imports
    try:
        print("Testing Analytics module imports...")
        import app.analytics.models
        import app.analytics.service
        import app.analytics.forms
        import app.analytics.routes
        print("✅ Analytics imports successful")
        results['analytics'] = "SUCCESS"
    except Exception as e:
        print(f"❌ Analytics imports failed: {e}")
        results['analytics'] = f"FAILED: {str(e)}"
    
    # Test notifications imports
    try:
        print("Testing Notifications module imports...")
        import app.notifications.models
        import app.notifications.service
        import app.notifications.forms
        import app.notifications.routes
        print("✅ Notifications imports successful")
        results['notifications'] = "SUCCESS"
    except Exception as e:
        print(f"❌ Notifications imports failed: {e}")
        results['notifications'] = f"FAILED: {str(e)}"
    
    # Test moderation imports
    try:
        print("Testing Moderation module imports...")
        import app.moderation.models
        import app.moderation.service
        import app.moderation.forms
        import app.moderation.routes
        print("✅ Moderation imports successful")
        results['moderation'] = "SUCCESS"
    except Exception as e:
        print(f"❌ Moderation imports failed: {e}")
        results['moderation'] = f"FAILED: {str(e)}"
    
    # Test admin imports
    try:
        print("Testing Admin module imports...")
        import app.admin.models
        import app.admin.service
        import app.admin.forms
        import app.admin.routes
        print("✅ Admin imports successful")
        results['admin'] = "SUCCESS"
    except Exception as e:
        print(f"❌ Admin imports failed: {e}")
        results['admin'] = f"FAILED: {str(e)}"
    
    return results

def test_model_classes():
    """Test model class definitions without database"""
    print("\n" + "=" * 60)
    print("Testing Model Class Definitions")
    print("=" * 60)
    
    results = {}
    
    try:
        # Test analytics models
        print("Testing Analytics model classes...")
        from app.analytics.models import AnalyticsEvent, UserBehavior, ContentPerformance
        
        # Test class existence
        assert AnalyticsEvent is not None
        assert UserBehavior is not None
        assert ContentPerformance is not None
        print("✅ Analytics model classes exist")
        results['analytics_models'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Analytics models failed: {e}")
        results['analytics_models'] = f"FAILED: {str(e)}"
    
    try:
        # Test notification models
        print("Testing Notifications model classes...")
        from app.notifications.models import AdminNotification, NotificationTemplate
        
        assert AdminNotification is not None
        assert NotificationTemplate is not None
        print("✅ Notifications model classes exist")
        results['notifications_models'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Notifications models failed: {e}")
        results['notifications_models'] = f"FAILED: {str(e)}"
    
    try:
        # Test moderation models
        print("Testing Moderation model classes...")
        from app.moderation.models import ModerationQueue, ContentAnalysis
        
        assert ModerationQueue is not None
        assert ContentAnalysis is not None
        print("✅ Moderation model classes exist")
        results['moderation_models'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Moderation models failed: {e}")
        results['moderation_models'] = f"FAILED: {str(e)}"
    
    try:
        # Test admin models
        print("Testing Admin model classes...")
        from app.admin.models import Permission, AdminRole, SecurityEvent
        
        assert Permission is not None
        assert AdminRole is not None
        assert SecurityEvent is not None
        print("✅ Admin model classes exist")
        results['admin_models'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Admin models failed: {e}")
        results['admin_models'] = f"FAILED: {str(e)}"
    
    return results

def test_service_classes():
    """Test service class definitions"""
    print("\n" + "=" * 60)
    print("Testing Service Class Definitions")
    print("=" * 60)
    
    results = {}
    
    try:
        # Test analytics services
        print("Testing Analytics service classes...")
        from app.analytics.service import AnalyticsService, UserBehaviorService
        
        assert AnalyticsService is not None
        assert UserBehaviorService is not None
        print("✅ Analytics service classes exist")
        results['analytics_services'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Analytics services failed: {e}")
        results['analytics_services'] = f"FAILED: {str(e)}"
    
    try:
        # Test notification services
        print("Testing Notifications service classes...")
        from app.notifications.service import NotificationService, AdminNotificationService
        
        assert NotificationService is not None
        assert AdminNotificationService is not None
        print("✅ Notifications service classes exist")
        results['notifications_services'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Notifications services failed: {e}")
        results['notifications_services'] = f"FAILED: {str(e)}"
    
    try:
        # Test moderation services
        print("Testing Moderation service classes...")
        from app.moderation.service import ContentAnalysisService, ModerationQueueService
        
        assert ContentAnalysisService is not None
        assert ModerationQueueService is not None
        print("✅ Moderation service classes exist")
        results['moderation_services'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Moderation services failed: {e}")
        results['moderation_services'] = f"FAILED: {str(e)}"
    
    try:
        # Test admin services
        print("Testing Admin service classes...")
        from app.admin.service import PermissionService, RoleService, SecurityEventService
        
        assert PermissionService is not None
        assert RoleService is not None
        assert SecurityEventService is not None
        print("✅ Admin service classes exist")
        results['admin_services'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Admin services failed: {e}")
        results['admin_services'] = f"FAILED: {str(e)}"
    
    return results

def test_form_classes():
    """Test form class definitions"""
    print("\n" + "=" * 60)
    print("Testing Form Class Definitions")
    print("=" * 60)
    
    results = {}
    
    try:
        # Test analytics forms
        print("Testing Analytics form classes...")
        from app.analytics.forms import AnalyticsFilterForm, UserBehaviorFilterForm
        
        assert AnalyticsFilterForm is not None
        assert UserBehaviorFilterForm is not None
        print("✅ Analytics form classes exist")
        results['analytics_forms'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Analytics forms failed: {e}")
        results['analytics_forms'] = f"FAILED: {str(e)}"
    
    try:
        # Test notification forms
        print("Testing Notifications form classes...")
        from app.notifications.forms import NotificationFilterForm, NotificationTemplateForm
        
        assert NotificationFilterForm is not None
        assert NotificationTemplateForm is not None
        print("✅ Notifications form classes exist")
        results['notifications_forms'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Notifications forms failed: {e}")
        results['notifications_forms'] = f"FAILED: {str(e)}"
    
    try:
        # Test moderation forms
        print("Testing Moderation form classes...")
        from app.moderation.forms import ModerationQueueFilterForm, ContentAnalysisForm
        
        assert ModerationQueueFilterForm is not None
        assert ContentAnalysisForm is not None
        print("✅ Moderation form classes exist")
        results['moderation_forms'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Moderation forms failed: {e}")
        results['moderation_forms'] = f"FAILED: {str(e)}"
    
    try:
        # Test admin forms
        print("Testing Admin form classes...")
        from app.admin.forms import PermissionForm, RoleForm, UserRoleForm
        
        assert PermissionForm is not None
        assert RoleForm is not None
        assert UserRoleForm is not None
        print("✅ Admin form classes exist")
        results['admin_forms'] = "SUCCESS"
        
    except Exception as e:
        print(f"❌ Admin forms failed: {e}")
        results['admin_forms'] = f"FAILED: {str(e)}"
    
    return results

def test_file_structure():
    """Test that all required files exist"""
    print("\n" + "=" * 60)
    print("Testing File Structure")
    print("=" * 60)
    
    results = {}
    
    required_files = [
        'app/analytics/__init__.py',
        'app/analytics/models.py',
        'app/analytics/service.py',
        'app/analytics/forms.py',
        'app/analytics/routes.py',
        'app/notifications/__init__.py',
        'app/notifications/models.py',
        'app/notifications/service.py',
        'app/notifications/forms.py',
        'app/notifications/routes.py',
        'app/moderation/__init__.py',
        'app/moderation/models.py',
        'app/moderation/service.py',
        'app/moderation/forms.py',
        'app/moderation/routes.py',
        'app/admin/models.py',
        'app/admin/service.py',
        'app/admin/forms.py',
        'app/admin/routes.py'
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} - MISSING")
    
    results['file_structure'] = {
        'existing_files': len(existing_files),
        'missing_files': len(missing_files),
        'missing_list': missing_files
    }
    
    print(f"\nFile Structure Summary:")
    print(f"  Existing files: {len(existing_files)}")
    print(f"  Missing files: {len(missing_files)}")
    
    if missing_files:
        print(f"\nMissing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    
    return results

def generate_summary_report(results):
    """Generate summary report"""
    print("\n" + "=" * 60)
    print("DEBUGGING SUMMARY REPORT")
    print("=" * 60)
    
    total_categories = 0
    successful_categories = 0
    
    for category, tests in results.items():
        total_categories += 1
        print(f"\n{category.upper()}:")
        
        if isinstance(tests, dict):
            category_success = True
            for test_name, result in tests.items():
                if result == "SUCCESS":
                    print(f"  ✅ {test_name}")
                else:
                    print(f"  ❌ {test_name}: {result}")
                    category_success = False
            
            if category_success:
                successful_categories += 1
                print(f"  Status: ✅ SUCCESS")
            else:
                print(f"  Status: ❌ FAILED")
        else:
            # File structure case
            if tests['missing_files'] == 0:
                print(f"  ✅ All {tests['existing_files']} files present")
                successful_categories += 1
            else:
                print(f"  ❌ {tests['missing_files']} files missing")
    
    print(f"\n" + "=" * 60)
    print("OVERALL STATUS")
    print("=" * 60)
    print(f"Categories tested: {total_categories}")
    print(f"Successful categories: {successful_categories}")
    print(f"Failed categories: {total_categories - successful_categories}")
    print(f"Success rate: {(successful_categories/total_categories)*100:.1f}%")
    
    if successful_categories == total_categories:
        print("\n🎉 ALL TESTS PASSED! Admin systems are properly structured.")
    else:
        print(f"\n⚠️  {total_categories - successful_categories} categories have issues.")
    
    return {
        'total_categories': total_categories,
        'successful_categories': successful_categories,
        'success_rate': (successful_categories/total_categories)*100
    }

def main():
    """Main debugging function"""
    print("🔧 Simple Admin Systems Debugging")
    print("=" * 60)
    
    all_results = {}
    
    # Run tests
    all_results['imports'] = test_basic_imports()
    all_results['models'] = test_model_classes()
    all_results['services'] = test_service_classes()
    all_results['forms'] = test_form_classes()
    all_results['file_structure'] = test_file_structure()
    
    # Generate summary
    summary = generate_summary_report(all_results)
    
    return summary

if __name__ == "__main__":
    main()
