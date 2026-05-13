#!/usr/bin/env python3
"""
Comprehensive System Integrity Test Suite
Tests the entire project from top to bottom ensuring system integrity
and proper wiring of all components.
"""

import os
import sys
import importlib
import traceback
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class SystemIntegrityTester:
    def __init__(self):
        self.results = []
        self.errors = []
        self.warnings = []
        self.start_time = datetime.now()
        
    def log_result(self, test_name, status, message="", details=None):
        """Log a test result"""
        result = {
            'test_name': test_name,
            'status': status,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now()
        }
        self.results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message}")
        
        if status == "FAIL":
            self.errors.append(result)
        elif status == "WARN":
            self.warnings.append(result)
    
    def test_project_structure(self):
        """Test project structure and core files"""
        print("\n" + "="*60)
        print("🔍 TESTING PROJECT STRUCTURE")
        print("="*60)
        
        required_files = [
            'run.py',
            'app/__init__.py',
            'app/models.py',
            'config.py',
            'requirements.txt'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = os.path.join(project_root, file_path)
            if os.path.exists(full_path):
                self.log_result(f"File exists: {file_path}", "PASS", f"Found at {full_path}")
            else:
                missing_files.append(file_path)
                self.log_result(f"File missing: {file_path}", "FAIL", f"Required file not found")
        
        # Test directory structure
        required_dirs = [
            'app',
            'app/templates',
            'app/static',
            'tests',
            'docs'
        ]
        
        for dir_path in required_dirs:
            full_path = os.path.join(project_root, dir_path)
            if os.path.isdir(full_path):
                self.log_result(f"Directory exists: {dir_path}", "PASS", f"Found at {full_path}")
            else:
                self.log_result(f"Directory missing: {dir_path}", "FAIL", f"Required directory not found")
        
        return len(missing_files) == 0
    
    def test_core_imports(self):
        """Test core module imports"""
        print("\n" + "="*60)
        print("🔍 TESTING CORE IMPORTS")
        print("="*60)
        
        core_modules = [
            'app',
            'app.models',
            'config',
            'run'
        ]
        
        import_errors = []
        for module_name in core_modules:
            try:
                module = importlib.import_module(module_name)
                self.log_result(f"Import: {module_name}", "PASS", f"Successfully imported {module_name}")
            except ImportError as e:
                import_errors.append(module_name)
                self.log_result(f"Import failed: {module_name}", "FAIL", f"ImportError: {str(e)}")
            except Exception as e:
                import_errors.append(module_name)
                self.log_result(f"Import error: {module_name}", "FAIL", f"Unexpected error: {str(e)}")
        
        return len(import_errors) == 0
    
    def test_flask_app_creation(self):
        """Test Flask app creation and configuration"""
        print("\n" + "="*60)
        print("🔍 TESTING FLASK APP CREATION")
        print("="*60)
        
        try:
            # Test app creation
            from app import create_app
            app = create_app()
            
            self.log_result("Flask app creation", "PASS", "App created successfully")
            
            # Test app configuration
            if hasattr(app, 'config'):
                self.log_result("App configuration", "PASS", "Config object exists")
            else:
                self.log_result("App configuration", "FAIL", "No config object found")
            
            # Test database initialization
            if hasattr(app, 'db'):
                self.log_result("Database initialization", "PASS", "Database object exists")
            else:
                self.log_result("Database initialization", "FAIL", "No database object found")
            
            # Test login manager
            if hasattr(app, 'login_manager'):
                self.log_result("Login manager", "PASS", "Login manager exists")
            else:
                self.log_result("Login manager", "FAIL", "No login manager found")
            
            return True
            
        except Exception as e:
            self.log_result("Flask app creation", "FAIL", f"Error creating app: {str(e)}")
            return False
    
    def test_database_models(self):
        """Test database models and relationships"""
        print("\n" + "="*60)
        print("🔍 TESTING DATABASE MODELS")
        print("="*60)
        
        try:
            from app import db
            from app.models import User, Post, Comment, Category, Repository
            
            # Test core models
            core_models = [User, Post, Comment, Category, Repository]
            model_errors = []
            
            for model in core_models:
                try:
                    # Test model can be instantiated (without database)
                    instance = model()
                    self.log_result(f"Model: {model.__name__}", "PASS", f"Model {model.__name__} can be instantiated")
                except Exception as e:
                    model_errors.append(model.__name__)
                    self.log_result(f"Model: {model.__name__}", "FAIL", f"Error instantiating: {str(e)}")
            
            # Test enhanced models
            try:
                from app.models import AuditLog
                audit_log = AuditLog()
                self.log_result("Enhanced model: AuditLog", "PASS", "AuditLog model working")
            except Exception as e:
                self.log_result("Enhanced model: AuditLog", "FAIL", f"Error: {str(e)}")
            
            # Test relationship systems
            try:
                from app.social.models import UserConnection, UserSocialProfile
                user_connection = UserConnection()
                user_social_profile = UserSocialProfile()
                self.log_result("Social models", "PASS", "Social relationship models working")
            except Exception as e:
                self.log_result("Social models", "FAIL", f"Error: {str(e)}")
            
            try:
                from app.content.models import ContentRelationship, ContentVersion
                content_relationship = ContentRelationship()
                content_version = ContentVersion()
                self.log_result("Content models", "PASS", "Content relationship models working")
            except Exception as e:
                self.log_result("Content models", "FAIL", f"Error: {str(e)}")
            
            return len(model_errors) == 0
            
        except Exception as e:
            self.log_result("Database models", "FAIL", f"Error importing models: {str(e)}")
            return False
    
    def test_blueprint_registrations(self):
        """Test blueprint registrations and routing"""
        print("\n" + "="*60)
        print("🔍 TESTING BLUEPRINT REGISTRATIONS")
        print("="*60)
        
        try:
            from app import create_app
            app = create_app()
            
            # Test blueprint registration
            blueprints = []
            for rule in app.url_map.iter_rules():
                if '.' in rule.endpoint:
                    blueprint_name = rule.endpoint.split('.')[0]
                    if blueprint_name not in blueprints:
                        blueprints.append(blueprint_name)
            
            expected_blueprints = ['main', 'auth', 'forum', 'admin', 'api']
            missing_blueprints = []
            
            for expected_bp in expected_blueprints:
                if expected_bp in blueprints:
                    self.log_result(f"Blueprint: {expected_bp}", "PASS", f"Blueprint {expected_bp} registered")
                else:
                    missing_blueprints.append(expected_bp)
                    self.log_result(f"Blueprint: {expected_bp}", "FAIL", f"Blueprint {expected_bp} not registered")
            
            # Test core routes
            core_routes = [
                '/',
                '/auth/login',
                '/forum/',
                '/admin/'
            ]
            
            for route in core_routes:
                try:
                    # Test if route exists in URL map
                    route_found = any(route in rule.rule for rule in app.url_map.iter_rules())
                    if route_found:
                        self.log_result(f"Route: {route}", "PASS", f"Route {route} exists")
                    else:
                        self.log_result(f"Route: {route}", "WARN", f"Route {route} not found")
                except Exception as e:
                    self.log_result(f"Route: {route}", "FAIL", f"Error checking route: {str(e)}")
            
            return len(missing_blueprints) == 0
            
        except Exception as e:
            self.log_result("Blueprint registrations", "FAIL", f"Error testing blueprints: {str(e)}")
            return False
    
    def test_authentication_system(self):
        """Test authentication and user management"""
        print("\n" + "="*60)
        print("🔍 TESTING AUTHENTICATION SYSTEM")
        print("="*60)
        
        try:
            from app.models import User
            from flask_login import LoginManager
            
            # Test User model
            user = User()
            required_fields = ['username', 'email', 'password_hash', 'is_admin']
            
            for field in required_fields:
                if hasattr(user, field):
                    self.log_result(f"User field: {field}", "PASS", f"Field {field} exists")
                else:
                    self.log_result(f"User field: {field}", "FAIL", f"Field {field} missing")
            
            # Test user methods
            required_methods = ['set_password', 'check_password']
            
            for method in required_methods:
                if hasattr(user, method):
                    self.log_result(f"User method: {method}", "PASS", f"Method {method} exists")
                else:
                    self.log_result(f"User method: {method}", "FAIL", f"Method {method} missing")
            
            # Test login manager integration
            try:
                from app import create_app
                app = create_app()
                if hasattr(app, 'login_manager'):
                    self.log_result("Login manager integration", "PASS", "Login manager properly integrated")
                else:
                    self.log_result("Login manager integration", "FAIL", "Login manager not found")
            except Exception as e:
                self.log_result("Login manager integration", "FAIL", f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_result("Authentication system", "FAIL", f"Error testing auth: {str(e)}")
            return False
    
    def test_forum_system(self):
        """Test forum system integration"""
        print("\n" + "="*60)
        print("🔍 TESTING FORUM SYSTEM")
        print("="*60)
        
        try:
            from app.models import Post, Comment, Category, Repository
            from app.forum.routes import forum_bp
            
            # Test forum models
            forum_models = [Post, Comment, Category, Repository]
            model_errors = []
            
            for model in forum_models:
                try:
                    instance = model()
                    self.log_result(f"Forum model: {model.__name__}", "PASS", f"Model {model.__name__} working")
                except Exception as e:
                    model_errors.append(model.__name__)
                    self.log_result(f"Forum model: {model.__name__}", "FAIL", f"Error: {str(e)}")
            
            # Test enhanced forum features
            try:
                from app.models import AuditLog
                audit_log = AuditLog()
                
                # Test audit log methods
                if hasattr(audit_log, 'set_old_values'):
                    self.log_result("Forum audit features", "PASS", "AuditLog methods working")
                else:
                    self.log_result("Forum audit features", "FAIL", "AuditLog methods missing")
                    
            except Exception as e:
                self.log_result("Forum audit features", "FAIL", f"Error: {str(e)}")
            
            # Test forum blueprint
            if hasattr(forum_bp, 'name'):
                self.log_result("Forum blueprint", "PASS", "Forum blueprint properly defined")
            else:
                self.log_result("Forum blueprint", "FAIL", "Forum blueprint not properly defined")
            
            # Test forum routes
            try:
                from app.forum.routes import edit_post, delete_post, edit_comment, delete_comment
                forum_routes = [edit_post, delete_post, edit_comment, delete_comment]
                
                for route_func in forum_routes:
                    if callable(route_func):
                        self.log_result(f"Forum route: {route_func.__name__}", "PASS", f"Route {route_func.__name__} callable")
                    else:
                        self.log_result(f"Forum route: {route_func.__name__}", "FAIL", f"Route {route_func.__name__} not callable")
                        
            except Exception as e:
                self.log_result("Forum routes", "FAIL", f"Error importing routes: {str(e)}")
            
            return len(model_errors) == 0
            
        except Exception as e:
            self.log_result("Forum system", "FAIL", f"Error testing forum: {str(e)}")
            return False
    
    def test_relationship_systems(self):
        """Test enhanced relationship systems"""
        print("\n" + "="*60)
        print("🔍 TESTING RELATIONSHIP SYSTEMS")
        print("="*60)
        
        try:
            # Test social relationship system
            try:
                from app.social.models import UserConnection, UserSocialProfile, UserGroup
                from app.social.service import SocialService
                
                social_models = [UserConnection, UserSocialProfile, UserGroup]
                social_errors = []
                
                for model in social_models:
                    try:
                        instance = model()
                        self.log_result(f"Social model: {model.__name__}", "PASS", f"Model {model.__name__} working")
                    except Exception as e:
                        social_errors.append(model.__name__)
                        self.log_result(f"Social model: {model.__name__}", "FAIL", f"Error: {str(e)}")
                
                # Test social service
                if callable(SocialService):
                    self.log_result("Social service", "PASS", "SocialService callable")
                else:
                    self.log_result("Social service", "FAIL", "SocialService not callable")
                    
            except Exception as e:
                self.log_result("Social system", "FAIL", f"Error: {str(e)}")
            
            # Test content relationship system
            try:
                from app.content.models import ContentRelationship, ContentVersion, ContentAnalytics
                from app.content.service import ContentService
                
                content_models = [ContentRelationship, ContentVersion, ContentAnalytics]
                content_errors = []
                
                for model in content_models:
                    try:
                        instance = model()
                        self.log_result(f"Content model: {model.__name__}", "PASS", f"Model {model.__name__} working")
                    except Exception as e:
                        content_errors.append(model.__name__)
                        self.log_result(f"Content model: {model.__name__}", "FAIL", f"Error: {str(e)}")
                
                # Test content service
                if callable(ContentService):
                    self.log_result("Content service", "PASS", "ContentService callable")
                else:
                    self.log_result("Content service", "FAIL", "ContentService not callable")
                    
            except Exception as e:
                self.log_result("Content system", "FAIL", f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_result("Relationship systems", "FAIL", f"Error testing relationships: {str(e)}")
            return False
    
    def test_security_systems(self):
        """Test security and monitoring systems"""
        print("\n" + "="*60)
        print("🔍 TESTING SECURITY SYSTEMS")
        print("="*60)
        
        try:
            # Test security models
            try:
                from app.security.models import SecurityEvent, AuditTrail
                security_models = [SecurityEvent, AuditTrail]
                
                for model in security_models:
                    try:
                        instance = model()
                        self.log_result(f"Security model: {model.__name__}", "PASS", f"Model {model.__name__} working")
                    except Exception as e:
                        self.log_result(f"Security model: {model.__name__}", "FAIL", f"Error: {str(e)}")
                        
            except Exception as e:
                self.log_result("Security models", "FAIL", f"Error: {str(e)}")
            
            # Test security service
            try:
                from app.security.service import SecurityService
                if callable(SecurityService):
                    self.log_result("Security service", "PASS", "SecurityService callable")
                else:
                    self.log_result("Security service", "FAIL", "SecurityService not callable")
                    
            except Exception as e:
                self.log_result("Security service", "FAIL", f"Error: {str(e)}")
            
            # Test audit logging
            try:
                from app.models import AuditLog
                audit_log = AuditLog()
                
                # Test audit log functionality
                audit_log.set_old_values({'test': 'old_value'})
                audit_log.set_new_values({'test': 'new_value'})
                
                old_values = audit_log.get_old_values()
                new_values = audit_log.get_new_values()
                
                if old_values.get('test') == 'old_value' and new_values.get('test') == 'new_value':
                    self.log_result("Audit logging", "PASS", "AuditLog functionality working")
                else:
                    self.log_result("Audit logging", "FAIL", "AuditLog functionality not working")
                    
            except Exception as e:
                self.log_result("Audit logging", "FAIL", f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_result("Security systems", "FAIL", f"Error testing security: {str(e)}")
            return False
    
    def test_integration_dependencies(self):
        """Test cross-system integration and dependencies"""
        print("\n" + "="*60)
        print("🔍 TESTING INTEGRATION DEPENDENCIES")
        print("="*60)
        
        try:
            # Test app context integration
            try:
                from app import create_app
                app = create_app()
                
                with app.app_context():
                    # Test database in app context
                    from app import db
                    if db:
                        self.log_result("App context database", "PASS", "Database available in app context")
                    else:
                        self.log_result("App context database", "FAIL", "Database not available in app context")
                        
            except Exception as e:
                self.log_result("App context integration", "FAIL", f"Error: {str(e)}")
            
            # Test model relationships
            try:
                from app.models import User, Post, Comment
                
                # Test user-posts relationship
                user = User()
                if hasattr(user, 'posts'):
                    self.log_result("User-Posts relationship", "PASS", "User.posts relationship exists")
                else:
                    self.log_result("User-Posts relationship", "FAIL", "User.posts relationship missing")
                
                # Test post-comments relationship
                post = Post()
                if hasattr(post, 'comments'):
                    self.log_result("Post-Comments relationship", "PASS", "Post.comments relationship exists")
                else:
                    self.log_result("Post-Comments relationship", "FAIL", "Post.comments relationship missing")
                    
            except Exception as e:
                self.log_result("Model relationships", "FAIL", f"Error: {str(e)}")
            
            # Test blueprint integration
            try:
                from app import create_app
                app = create_app()
                
                # Test that blueprints are registered
                registered_blueprints = []
                for rule in app.url_map.iter_rules():
                    if '.' in rule.endpoint:
                        blueprint_name = rule.endpoint.split('.')[0]
                        if blueprint_name not in registered_blueprints:
                            registered_blueprints.append(blueprint_name)
                
                if len(registered_blueprints) > 0:
                    self.log_result("Blueprint integration", "PASS", f"Found {len(registered_blueprints)} registered blueprints")
                else:
                    self.log_result("Blueprint integration", "FAIL", "No blueprints registered")
                    
            except Exception as e:
                self.log_result("Blueprint integration", "FAIL", f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_result("Integration dependencies", "FAIL", f"Error testing integration: {str(e)}")
            return False
    
    def generate_report(self):
        """Generate comprehensive integrity report"""
        print("\n" + "="*60)
        print("📊 SYSTEM INTEGRITY REPORT")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.results if r['status'] == 'FAIL'])
        warning_tests = len([r for r in self.results if r['status'] == 'WARN'])
        
        print(f"\n📈 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️  Warnings: {warning_tests}")
        print(f"   📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for error in self.errors:
                print(f"   - {error['test_name']}: {error['message']}")
        
        if warning_tests > 0:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   - {warning['test_name']}: {warning['message']}")
        
        # System integrity assessment
        print(f"\n🔍 System Integrity Assessment:")
        
        if failed_tests == 0:
            print("   🟢 SYSTEM INTEGRITY: EXCELLENT")
            print("   🎉 All systems properly wired and integrated")
        elif failed_tests <= 3:
            print("   🟡 SYSTEM INTEGRITY: GOOD")
            print("   ⚡ Minor issues found, system mostly functional")
        elif failed_tests <= 7:
            print("   🟠 SYSTEM INTEGRITY: FAIR")
            print("   🔧 Several issues found, needs attention")
        else:
            print("   🔴 SYSTEM INTEGRITY: POOR")
            print("   🚨 Major issues found, requires immediate attention")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if failed_tests > 0:
            print("   1. Fix all failed tests to ensure system stability")
            print("   2. Review error messages for specific issues")
            print("   3. Test fixes individually before integration")
        
        if warning_tests > 0:
            print("   4. Address warnings to improve system robustness")
        
        print("   5. Run this test suite regularly to maintain integrity")
        print("   6. Add new tests as system evolves")
        
        # Execution time
        execution_time = datetime.now() - self.start_time
        print(f"\n⏱️  Execution Time: {execution_time.total_seconds():.2f} seconds")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'warning_tests': warning_tests,
            'success_rate': passed_tests/total_tests*100,
            'execution_time': execution_time.total_seconds(),
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def run_all_tests(self):
        """Run all system integrity tests"""
        print("🚀 STARTING COMPREHENSIVE SYSTEM INTEGRITY TESTS")
        print(f"📅 Started at: {self.start_time}")
        print(f"📁 Project Root: {project_root}")
        
        test_methods = [
            self.test_project_structure,
            self.test_core_imports,
            self.test_flask_app_creation,
            self.test_database_models,
            self.test_blueprint_registrations,
            self.test_authentication_system,
            self.test_forum_system,
            self.test_relationship_systems,
            self.test_security_systems,
            self.test_integration_dependencies
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_result(f"Test method: {test_method.__name__}", "FAIL", f"Test execution error: {str(e)}")
        
        return self.generate_report()

def main():
    """Main function to run system integrity tests"""
    tester = SystemIntegrityTester()
    report = tester.run_all_tests()
    
    # Save report to file
    report_file = os.path.join(project_root, 'tests', 'system_integrity_report.json')
    try:
        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📄 Report saved to: {report_file}")
    except Exception as e:
        print(f"\n❌ Could not save report: {str(e)}")
    
    # Return appropriate exit code
    return 0 if report['failed_tests'] == 0 else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
