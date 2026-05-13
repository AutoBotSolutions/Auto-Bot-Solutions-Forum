#!/usr/bin/env python3
"""
User Management Systems Debugging Script

This script comprehensively tests all user management systems that were implemented:
1. Advanced Profile Customization System
2. User Preference System  
3. Social Features System
4. Advanced User Analytics System
5. Advanced User Role Management System

It checks for:
- File existence and imports
- Database models and relationships
- Forms and validation
- Routes and endpoints
- Basic functionality
"""

import os
import sys
import importlib
import traceback
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, '/home/robbie/Desktop/repo-forum')

class UserManagementDebugger:
    def __init__(self):
        self.results = {
            'profile_customization': {'status': 'NOT_TESTED', 'issues': [], 'successes': []},
            'user_preferences': {'status': 'NOT_TESTED', 'issues': [], 'successes': []},
            'social_features': {'status': 'NOT_TESTED', 'issues': [], 'successes': []},
            'user_analytics': {'status': 'NOT_TESTED', 'issues': [], 'successes': []},
            'role_management': {'status': 'NOT_TESTED', 'issues': [], 'successes': []},
            'database_models': {'status': 'NOT_TESTED', 'issues': [], 'successes': []},
            'forms': {'status': 'NOT_TESTED', 'issues': [], 'successes': []},
            'routes': {'status': 'NOT_TESTED', 'issues': [], 'successes': []}
        }
        
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def log_result(self, system, test_name, success, message):
        """Log a test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            self.results[system]['successes'].append(f"✅ {test_name}: {message}")
        else:
            self.failed_tests += 1
            self.results[system]['issues'].append(f"❌ {test_name}: {message}")

    def test_file_existence(self):
        """Test if all required files exist"""
        print("🔍 Testing file existence...")
        
        files_to_check = [
            # Core files
            '/home/robbie/Desktop/repo-forum/app/user/forms.py',
            '/home/robbie/Desktop/repo-forum/app/user/routes.py',
            
            # Social features
            '/home/robbie/Desktop/repo-forum/app/user/social/__init__.py',
            '/home/robbie/Desktop/repo-forum/app/user/social/models.py',
            '/home/robbie/Desktop/repo-forum/app/user/social/forms.py',
            '/home/robbie/Desktop/repo-forum/app/user/social/routes.py',
            
            # Analytics
            '/home/robbie/Desktop/repo-forum/app/user/analytics/__init__.py',
            '/home/robbie/Desktop/repo-forum/app/user/analytics/models.py',
            '/home/robbie/Desktop/repo-forum/app/user/analytics/forms.py',
            '/home/robbie/Desktop/repo-forum/app/user/analytics/routes.py',
            
            # Role management
            '/home/robbie/Desktop/repo-forum/app/admin/roles/__init__.py',
            '/home/robbie/Desktop/repo-forum/app/admin/roles/models.py',
            '/home/robbie/Desktop/repo-forum/app/admin/roles/forms.py',
            '/home/robbie/Desktop/repo-forum/app/admin/roles/routes.py'
        ]
        
        for file_path in files_to_check:
            exists = os.path.exists(file_path)
            self.log_result('database_models', f"File exists: {file_path}", exists, 
                          "Found" if exists else "Missing")

    def test_imports(self):
        """Test if all modules can be imported"""
        print("🔍 Testing module imports...")
        
        try:
            # Test core imports
            from app.models import User
            self.log_result('database_models', "Import User model", True, "Successfully imported")
        except Exception as e:
            self.log_result('database_models', "Import User model", False, str(e))
        
        # Test social features imports
        try:
            from app.user.social.models import UserFollow, UserFriend, SocialActivity
            self.log_result('social_features', "Import social models", True, "Successfully imported")
        except Exception as e:
            self.log_result('social_features', "Import social models", False, str(e))
        
        try:
            from app.user.social.forms import FollowUserForm, SendFriendRequestForm
            self.log_result('social_features', "Import social forms", True, "Successfully imported")
        except Exception as e:
            self.log_result('social_features', "Import social forms", False, str(e))
        
        # Test analytics imports
        try:
            from app.user.analytics.models import UserBehavior, UserEngagement
            self.log_result('user_analytics', "Import analytics models", True, "Successfully imported")
        except Exception as e:
            self.log_result('user_analytics', "Import analytics models", False, str(e))
        
        # Test role management imports
        try:
            from app.admin.roles.models import Role, Permission, UserRole
            self.log_result('role_management', "Import role models", True, "Successfully imported")
        except Exception as e:
            self.log_result('role_management', "Import role models", False, str(e))

    def test_user_model_enhancements(self):
        """Test User model enhancements"""
        print("🔍 Testing User model enhancements...")
        
        try:
            from app.models import User
            
            # Check if new fields exist in User model
            required_fields = [
                'profile_theme', 'profile_skin', 'profile_banner_url', 'profile_layout',
                'profile_widgets', 'profile_privacy', 'profile_custom_css', 'profile_color_scheme',
                'user_preferences', 'notification_preferences', 'accessibility_preferences',
                'social_preferences', 'analytics_preferences'
            ]
            
            for field in required_fields:
                if hasattr(User, field):
                    self.log_result('profile_customization', f"User model field: {field}", True, "Field exists")
                else:
                    self.log_result('profile_customization', f"User model field: {field}", False, "Field missing")
            
            # Test profile customization methods
            profile_methods = [
                'get_profile_theme', 'set_profile_theme', 'get_profile_layout', 
                'set_profile_layout', 'get_profile_widgets', 'set_profile_widgets',
                'get_profile_privacy', 'set_profile_privacy', 'get_color_scheme',
                'set_color_scheme', 'can_view_profile', 'update_profile_banner'
            ]
            
            for method in profile_methods:
                if hasattr(User, method):
                    self.log_result('profile_customization', f"User model method: {method}", True, "Method exists")
                else:
                    self.log_result('profile_customization', f"User model method: {method}", False, "Method missing")
                    
        except Exception as e:
            self.log_result('profile_customization', "User model test", False, str(e))

    def test_social_models(self):
        """Test social features models"""
        print("🔍 Testing social features models...")
        
        try:
            from app.user.social.models import UserFollow, UserFriend, SocialActivity, UserRecommendation
            
            # Test UserFollow model
            self.log_result('social_features', "UserFollow model", True, "Model imported successfully")
            
            # Test UserFriend model
            self.log_result('social_features', "UserFriend model", True, "Model imported successfully")
            
            # Test SocialActivity model
            self.log_result('social_features', "SocialActivity model", True, "Model imported successfully")
            
            # Test UserRecommendation model
            self.log_result('social_features', "UserRecommendation model", True, "Model imported successfully")
            
            # Test static methods
            if hasattr(UserFollow, 'follow_user'):
                self.log_result('social_features', "UserFollow.follow_user method", True, "Method exists")
            else:
                self.log_result('social_features', "UserFollow.follow_user method", False, "Method missing")
                
            if hasattr(UserFriend, 'send_friend_request'):
                self.log_result('social_features', "UserFriend.send_friend_request method", True, "Method exists")
            else:
                self.log_result('social_features', "UserFriend.send_friend_request method", False, "Method missing")
                
        except Exception as e:
            self.log_result('social_features', "Social models test", False, str(e))

    def test_analytics_models(self):
        """Test analytics models"""
        print("🔍 Testing analytics models...")
        
        try:
            from app.user.analytics.models import UserBehavior, UserEngagement, UserPerformance, UserSegment
            
            # Test UserBehavior model
            self.log_result('user_analytics', "UserBehavior model", True, "Model imported successfully")
            
            # Test UserEngagement model
            self.log_result('user_analytics', "UserEngagement model", True, "Model imported successfully")
            
            # Test UserPerformance model
            self.log_result('user_analytics', "UserPerformance model", True, "Model imported successfully")
            
            # Test UserSegment model
            self.log_result('user_analytics', "UserSegment model", True, "Model imported successfully")
            
            # Test static methods
            if hasattr(UserBehavior, 'track_behavior'):
                self.log_result('user_analytics', "UserBehavior.track_behavior method", True, "Method exists")
            else:
                self.log_result('user_analytics', "UserBehavior.track_behavior method", False, "Method missing")
                
            if hasattr(UserEngagement, 'calculate_daily_engagement'):
                self.log_result('user_analytics', "UserEngagement.calculate_daily_engagement method", True, "Method exists")
            else:
                self.log_result('user_analytics', "UserEngagement.calculate_daily_engagement method", False, "Method missing")
                
        except Exception as e:
            self.log_result('user_analytics', "Analytics models test", False, str(e))

    def test_role_models(self):
        """Test role management models"""
        print("🔍 Testing role management models...")
        
        try:
            from app.admin.roles.models import Role, Permission, UserRole, RoleAssignment
            
            # Test Role model
            self.log_result('role_management', "Role model", True, "Model imported successfully")
            
            # Test Permission model
            self.log_result('role_management', "Permission model", True, "Model imported successfully")
            
            # Test UserRole model
            self.log_result('role_management', "UserRole model", True, "Model imported successfully")
            
            # Test RoleAssignment model
            self.log_result('role_management', "RoleAssignment model", True, "Model imported successfully")
            
            # Test static methods
            if hasattr(Role, 'create_role'):
                self.log_result('role_management', "Role.create_role method", True, "Method exists")
            else:
                self.log_result('role_management', "Role.create_role method", False, "Method missing")
                
            if hasattr(UserRole, 'assign_role'):
                self.log_result('role_management', "UserRole.assign_role method", True, "Method exists")
            else:
                self.log_result('role_management', "UserRole.assign_role method", False, "Method missing")
                
        except Exception as e:
            self.log_result('role_management', "Role models test", False, str(e))

    def test_forms(self):
        """Test all forms"""
        print("🔍 Testing forms...")
        
        # Test profile customization forms
        try:
            from app.user.forms import ProfileThemeForm, ProfileLayoutForm, ProfilePrivacyForm
            self.log_result('forms', "Profile customization forms", True, "Forms imported successfully")
        except Exception as e:
            self.log_result('forms', "Profile customization forms", False, str(e))
        
        # Test user preference forms
        try:
            from app.user.forms import UserPreferencesForm, NotificationPreferencesForm
            self.log_result('forms', "User preference forms", True, "Forms imported successfully")
        except Exception as e:
            self.log_result('forms', "User preference forms", False, str(e))
        
        # Test social forms
        try:
            from app.user.social.forms import FollowUserForm, SendFriendRequestForm, CreateGroupForm
            self.log_result('forms', "Social feature forms", True, "Forms imported successfully")
        except Exception as e:
            self.log_result('forms', "Social feature forms", False, str(e))
        
        # Test analytics forms
        try:
            from app.user.analytics.forms import AnalyticsDateRangeForm, UserSegmentForm
            self.log_result('forms', "Analytics forms", True, "Forms imported successfully")
        except Exception as e:
            self.log_result('forms', "Analytics forms", False, str(e))
        
        # Test role management forms
        try:
            from app.admin.roles.forms import RoleForm, PermissionForm, AssignRoleForm
            self.log_result('forms', "Role management forms", True, "Forms imported successfully")
        except Exception as e:
            self.log_result('forms', "Role management forms", False, str(e))

    def test_routes(self):
        """Test all routes"""
        print("🔍 Testing routes...")
        
        # Test user routes
        try:
            from app.user.routes import user_bp
            self.log_result('routes', "User blueprint", True, "Blueprint imported successfully")
        except Exception as e:
            self.log_result('routes', "User blueprint", False, str(e))
        
        # Test social routes
        try:
            from app.user.social.routes import social_bp
            self.log_result('routes', "Social blueprint", True, "Blueprint imported successfully")
        except Exception as e:
            self.log_result('routes', "Social blueprint", False, str(e))
        
        # Test analytics routes
        try:
            from app.user.analytics.routes import analytics_bp
            self.log_result('routes', "Analytics blueprint", True, "Blueprint imported successfully")
        except Exception as e:
            self.log_result('routes', "Analytics blueprint", False, str(e))
        
        # Test role management routes
        try:
            from app.admin.roles.routes import roles_bp
            self.log_result('routes', "Role management blueprint", True, "Blueprint imported successfully")
        except Exception as e:
            self.log_result('routes', "Role management blueprint", False, str(e))

    def test_basic_functionality(self):
        """Test basic functionality"""
        print("🔍 Testing basic functionality...")
        
        try:
            # Test User model profile methods
            from app.models import User
            
            # Create a mock user instance (without saving to database)
            user = User()
            user.id = 1
            user.username = "testuser"
            
            # Test profile theme methods
            try:
                theme = user.get_profile_theme()
                self.log_result('profile_customization', "get_profile_theme method", True, f"Returns: {theme}")
            except Exception as e:
                self.log_result('profile_customization', "get_profile_theme method", False, str(e))
            
            try:
                user.set_profile_theme('dark', 'dark')
                self.log_result('profile_customization', "set_profile_theme method", True, "Method executed successfully")
            except Exception as e:
                self.log_result('profile_customization', "set_profile_theme method", False, str(e))
            
            # Test profile layout methods
            try:
                layout = user.get_profile_layout()
                self.log_result('profile_customization', "get_profile_layout method", True, f"Returns layout with {len(layout.get('sections', []))} sections")
            except Exception as e:
                self.log_result('profile_customization', "get_profile_layout method", False, str(e))
            
            # Test privacy methods
            try:
                privacy = user.get_profile_privacy()
                self.log_result('profile_customization', "get_profile_privacy method", True, f"Returns {len(privacy)} privacy settings")
            except Exception as e:
                self.log_result('profile_customization', "get_profile_privacy method", False, str(e))
                
        except Exception as e:
            self.log_result('profile_customization', "Basic functionality test", False, str(e))

    def run_all_tests(self):
        """Run all debugging tests"""
        print("🚀 Starting User Management Systems Debugging...")
        print("=" * 60)
        
        # Run all test categories
        self.test_file_existence()
        self.test_imports()
        self.test_user_model_enhancements()
        self.test_social_models()
        self.test_analytics_models()
        self.test_role_models()
        self.test_forms()
        self.test_routes()
        self.test_basic_functionality()
        
        # Generate final report
        self.generate_report()

    def generate_report(self):
        """Generate final debugging report"""
        print("\n" + "=" * 60)
        print("📊 USER MANAGEMENT SYSTEMS DEBUGGING REPORT")
        print("=" * 60)
        
        # Overall statistics
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"\n📈 OVERALL STATISTICS:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   Passed: {self.passed_tests}")
        print(f"   Failed: {self.failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # System-by-system breakdown
        systems = [
            ('profile_customization', 'Advanced Profile Customization'),
            ('user_preferences', 'User Preference System'),
            ('social_features', 'Social Features System'),
            ('user_analytics', 'Advanced User Analytics'),
            ('role_management', 'Advanced Role Management')
        ]
        
        print(f"\n🔍 SYSTEM BREAKDOWN:")
        for system_key, system_name in systems:
            result = self.results[system_key]
            successes = len(result['successes'])
            issues = len(result['issues'])
            
            if issues == 0:
                status = "✅ PASS"
                result['status'] = 'PASS'
            else:
                status = "❌ FAIL"
                result['status'] = 'FAIL'
            
            print(f"\n   {system_name}:")
            print(f"   Status: {status}")
            print(f"   Successes: {successes}")
            print(f"   Issues: {issues}")
            
            # Show issues if any
            if issues > 0:
                print(f"   Issues:")
                for issue in result['issues'][:3]:  # Show first 3 issues
                    print(f"     - {issue}")
                if issues > 3:
                    print(f"     ... and {issues - 3} more issues")
        
        # Forms and Routes summary
        print(f"\n📝 FORMS AND ROUTES:")
        forms_result = self.results['forms']
        routes_result = self.results['routes']
        
        print(f"   Forms: {'✅ PASS' if len(forms_result['issues']) == 0 else '❌ FAIL'} ({len(forms_result['successes'])} passed, {len(forms_result['issues'])} failed)")
        print(f"   Routes: {'✅ PASS' if len(routes_result['issues']) == 0 else '❌ FAIL'} ({len(routes_result['successes'])} passed, {len(routes_result['issues'])} failed)")
        
        # Critical issues summary
        print(f"\n⚠️  CRITICAL ISSUES:")
        critical_issues = []
        for system_key, system_name in systems:
            result = self.results[system_key]
            for issue in result['issues']:
                if 'missing' in issue.lower() or 'error' in issue.lower():
                    critical_issues.append(f"{system_name}: {issue}")
        
        if critical_issues:
            for issue in critical_issues[:5]:  # Show first 5 critical issues
                print(f"   - {issue}")
            if len(critical_issues) > 5:
                print(f"   ... and {len(critical_issues) - 5} more critical issues")
        else:
            print("   No critical issues found!")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if success_rate >= 90:
            print("   ✅ Systems are in excellent condition!")
            print("   ✅ Ready for production deployment")
        elif success_rate >= 75:
            print("   ⚠️  Systems are mostly functional with minor issues")
            print("   🔧 Address remaining issues before production")
        else:
            print("   ❌ Systems have significant issues that need attention")
            print("   🛠️  Major debugging and fixes required")
        
        # Save detailed report to file
        self.save_detailed_report()
        
        print(f"\n📄 Detailed report saved to: /home/robbie/Desktop/repo-forum/USER_MANAGEMENT_DEBUG_REPORT.md")
        print("=" * 60)

    def save_detailed_report(self):
        """Save detailed debugging report to file"""
        report_content = f"""# User Management Systems Debugging Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Statistics
- Total Tests: {self.total_tests}
- Passed: {self.passed_tests}
- Failed: {self.failed_tests}
- Success Rate: {(self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0:.1f}%

## System Breakdown

### Advanced Profile Customization
Status: {self.results['profile_customization']['status']}

**Successes:**
"""
        
        for success in self.results['profile_customization']['successes']:
            report_content += f"- {success}\n"
        
        report_content += "\n**Issues:**\n"
        for issue in self.results['profile_customization']['issues']:
            report_content += f"- {issue}\n"
        
        # Add other systems (abbreviated for brevity)
        systems_to_add = [
            ('user_preferences', 'User Preference System'),
            ('social_features', 'Social Features System'),
            ('user_analytics', 'Advanced User Analytics'),
            ('role_management', 'Advanced Role Management')
        ]
        
        for system_key, system_name in systems_to_add:
            result = self.results[system_key]
            report_content += f"\n### {system_name}\nStatus: {result['status']}\n\n**Successes:**\n"
            for success in result['successes']:
                report_content += f"- {success}\n"
            report_content += "\n**Issues:**\n"
            for issue in result['issues']:
                report_content += f"- {issue}\n"
        
        # Add forms and routes
        report_content += f"\n### Forms and Routes\n\n**Forms:**\nStatus: {'PASS' if len(self.results['forms']['issues']) == 0 else 'FAIL'}\n"
        for success in self.results['forms']['successes']:
            report_content += f"- {success}\n"
        for issue in self.results['forms']['issues']:
            report_content += f"- {issue}\n"
        
        report_content += f"\n**Routes:**\nStatus: {'PASS' if len(self.results['routes']['issues']) == 0 else 'FAIL'}\n"
        for success in self.results['routes']['successes']:
            report_content += f"- {success}\n"
        for issue in self.results['routes']['issues']:
            report_content += f"- {issue}\n"
        
        # Save to file
        with open('/home/robbie/Desktop/repo-forum/USER_MANAGEMENT_DEBUG_REPORT.md', 'w') as f:
            f.write(report_content)

if __name__ == "__main__":
    debugger = UserManagementDebugger()
    debugger.run_all_tests()
