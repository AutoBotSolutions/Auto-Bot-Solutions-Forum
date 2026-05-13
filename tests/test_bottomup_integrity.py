#!/usr/bin/env python3
"""
Bottom-Up System Integrity Test Suite
Tests the entire project from bottom to top ensuring system integrity
and proper wiring of all components starting from the lowest level.
"""

import os
import sys
import importlib
import traceback
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class BottomUpIntegrityTester:
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
    
    def test_database_configuration(self):
        """Test database configuration at the lowest level"""
        print("\n" + "="*60)
        print("🔍 TESTING DATABASE CONFIGURATION (LOWEST LEVEL)")
        print("="*60)
        
        try:
            # Test configuration file exists
            config_path = os.path.join(project_root, 'config.py')
            if os.path.exists(config_path):
                self.log_result("Config file exists", "PASS", f"Found at {config_path}")
            else:
                self.log_result("Config file missing", "FAIL", "Required config.py not found")
                return False
            
            # Test configuration import
            try:
                import config
                self.log_result("Config import", "PASS", "Configuration imported successfully")
            except ImportError as e:
                self.log_result("Config import", "FAIL", f"ImportError: {str(e)}")
                return False
            
            # Test database configuration
            required_config_vars = ['SQLALCHEMY_DATABASE_URI', 'SQLALCHEMY_TRACK_MODIFICATIONS']
            config_errors = []
            
            for var in required_config_vars:
                if hasattr(config.Config, var):
                    self.log_result(f"Config var: {var}", "PASS", f"{var} configured")
                else:
                    config_errors.append(var)
                    self.log_result(f"Config var: {var}", "FAIL", f"{var} not configured")
            
            # Test database URI format
            if hasattr(config.Config, 'SQLALCHEMY_DATABASE_URI'):
                db_uri = config.Config.SQLALCHEMY_DATABASE_URI
                if db_uri.startswith(('sqlite:///', 'postgresql://', 'mysql://')):
                    self.log_result("Database URI format", "PASS", f"Valid URI: {db_uri.split('://')[0]}://")
                else:
                    self.log_result("Database URI format", "WARN", f"Unusual URI format: {db_uri}")
            
            return len(config_errors) == 0
            
        except Exception as e:
            self.log_result("Database configuration", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_database_connection(self):
        """Test database connection and SQLAlchemy setup"""
        print("\n" + "="*60)
        print("🔍 TESTING DATABASE CONNECTION")
        print("="*60)
        
        try:
            # Test SQLAlchemy import
            try:
                from flask_sqlalchemy import SQLAlchemy
                self.log_result("SQLAlchemy import", "PASS", "SQLAlchemy imported successfully")
            except ImportError as e:
                self.log_result("SQLAlchemy import", "FAIL", f"ImportError: {str(e)}")
                return False
            
            # Test database initialization (without app context)
            try:
                from flask_sqlalchemy import SQLAlchemy
                db = SQLAlchemy()
                self.log_result("Database object creation", "PASS", "SQLAlchemy object created")
            except Exception as e:
                self.log_result("Database object creation", "FAIL", f"Error: {str(e)}")
                return False
            
            # Test database metadata
            try:
                metadata = db.metadata
                if metadata:
                    self.log_result("Database metadata", "PASS", "Metadata accessible")
                else:
                    self.log_result("Database metadata", "FAIL", "Metadata not accessible")
            except Exception as e:
                self.log_result("Database metadata", "FAIL", f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_result("Database connection", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_individual_models_bottomup(self):
        """Test individual database models from bottom up"""
        print("\n" + "="*60)
        print("🔍 TESTING INDIVIDUAL MODELS (BOTTOM-UP)")
        print("="*60)
        
        try:
            # Test basic model imports
            model_files = [
                'app.models',
                'app.content.models',
                'app.social.models',
                'app.security.models'
            ]
            
            import_errors = []
            for model_file in model_files:
                try:
                    importlib.import_module(model_file)
                    self.log_result(f"Model import: {model_file}", "PASS", f"Imported successfully")
                except ImportError as e:
                    import_errors.append(model_file)
                    self.log_result(f"Model import: {model_file}", "FAIL", f"ImportError: {str(e)}")
                except Exception as e:
                    import_errors.append(model_file)
                    self.log_result(f"Model import: {model_file}", "FAIL", f"Error: {str(e)}")
            
            # Test individual model classes (bottom-up approach)
            model_tests = [
                # Core models (bottom level)
                ('User', 'app.models'),
                ('Category', 'app.models'),
                ('Repository', 'app.models'),
                # Forum models (next level)
                ('Post', 'app.models'),
                ('Comment', 'app.models'),
                ('AuditLog', 'app.models'),
                # Content models (higher level)
                ('ContentTag', 'app.content.models'),
                ('ContentCategory', 'app.content.models'),
                ('ContentRelationship', 'app.content.models'),
                # Social models (higher level)
                ('UserConnection', 'app.social.models'),
                ('UserSocialProfile', 'app.social.models'),
                # Security models (highest level)
                ('SecurityEvent', 'app.security.models'),
                ('AuditTrail', 'app.security.models'),
            ]
            
            model_errors = []
            for model_name, module_path in model_tests:
                try:
                    module = importlib.import_module(module_path)
                    model_class = getattr(module, model_name)
                    
                    # Test model instantiation (without database)
                    instance = model_class()
                    self.log_result(f"Model: {model_name}", "PASS", f"Model {model_name} can be instantiated")
                    
                except AttributeError as e:
                    model_errors.append(model_name)
                    self.log_result(f"Model: {model_name}", "FAIL", f"Model not found: {str(e)}")
                except Exception as e:
                    model_errors.append(model_name)
                    self.log_result(f"Model: {model_name}", "FAIL", f"Error instantiating: {str(e)}")
            
            return len(import_errors) == 0 and len(model_errors) == 0
            
        except Exception as e:
            self.log_result("Individual models", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_model_relationships_bottomup(self):
        """Test model relationships from bottom up"""
        print("\n" + "="*60)
        print("🔍 TESTING MODEL RELATIONSHIPS (BOTTOM-UP)")
        print("="*60)
        
        try:
            # Test User model relationships (bottom level)
            try:
                from app.models import User
                user = User()
                
                # Test basic relationship attributes
                user_relationships = ['posts', 'comments', 'audit_logs']
                for rel in user_relationships:
                    if hasattr(user, rel):
                        self.log_result(f"User relationship: {rel}", "PASS", f"Relationship {rel} exists")
                    else:
                        self.log_result(f"User relationship: {rel}", "WARN", f"Relationship {rel} missing")
                        
            except Exception as e:
                self.log_result("User relationships", "FAIL", f"Error: {str(e)}")
            
            # Test Post model relationships (next level)
            try:
                from app.models import Post
                post = Post()
                
                post_relationships = ['author', 'comments', 'tags']
                for rel in post_relationships:
                    if hasattr(post, rel):
                        self.log_result(f"Post relationship: {rel}", "PASS", f"Relationship {rel} exists")
                    else:
                        self.log_result(f"Post relationship: {rel}", "WARN", f"Relationship {rel} missing")
                        
            except Exception as e:
                self.log_result("Post relationships", "FAIL", f"Error: {str(e)}")
            
            # Test Comment model relationships
            try:
                from app.models import Comment
                comment = Comment()
                
                comment_relationships = ['author', 'post']
                for rel in comment_relationships:
                    if hasattr(comment, rel):
                        self.log_result(f"Comment relationship: {rel}", "PASS", f"Relationship {rel} exists")
                    else:
                        self.log_result(f"Comment relationship: {rel}", "WARN", f"Relationship {rel} missing")
                        
            except Exception as e:
                self.log_result("Comment relationships", "FAIL", f"Error: {str(e)}")
            
            # Test AuditLog model relationships
            try:
                from app.models import AuditLog
                audit_log = AuditLog()
                
                audit_relationships = ['user']
                for rel in audit_relationships:
                    if hasattr(audit_log, rel):
                        self.log_result(f"AuditLog relationship: {rel}", "PASS", f"Relationship {rel} exists")
                    else:
                        self.log_result(f"AuditLog relationship: {rel}", "WARN", f"Relationship {rel} missing")
                        
            except Exception as e:
                self.log_result("AuditLog relationships", "FAIL", f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_result("Model relationships", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_service_layer_bottomup(self):
        """Test service layer from bottom up"""
        print("\n" + "="*60)
        print("🔍 TESTING SERVICE LAYER (BOTTOM-UP)")
        print("="*60)
        
        try:
            # Test service imports
            service_modules = [
                'app.forum.service',
                'app.content.service',
                'app.social.service',
                'app.security.service'
            ]
            
            service_errors = []
            for service_module in service_modules:
                try:
                    module = importlib.import_module(service_module)
                    self.log_result(f"Service import: {service_module}", "PASS", f"Imported successfully")
                except ImportError as e:
                    service_errors.append(service_module)
                    self.log_result(f"Service import: {service_module}", "FAIL", f"ImportError: {str(e)}")
                except Exception as e:
                    service_errors.append(service_module)
                    self.log_result(f"Service import: {service_module}", "FAIL", f"Error: {str(e)}")
            
            # Test individual service classes
            service_tests = [
                ('ForumService', 'app.forum.service'),
                ('ContentService', 'app.content.service'),
                ('SocialService', 'app.social.service'),
                ('SecurityService', 'app.security.service'),
            ]
            
            service_class_errors = []
            for service_name, module_path in service_tests:
                try:
                    module = importlib.import_module(module_path)
                    service_class = getattr(module, service_name)
                    
                    # Test service instantiation
                    if callable(service_class):
                        self.log_result(f"Service class: {service_name}", "PASS", f"Service {service_name} callable")
                    else:
                        self.log_result(f"Service class: {service_name}", "FAIL", f"Service {service_name} not callable")
                        
                except AttributeError as e:
                    service_class_errors.append(service_name)
                    self.log_result(f"Service class: {service_name}", "FAIL", f"Service not found: {str(e)}")
                except Exception as e:
                    service_class_errors.append(service_name)
                    self.log_result(f"Service class: {service_name}", "FAIL", f"Error: {str(e)}")
            
            return len(service_errors) == 0 and len(service_class_errors) == 0
            
        except Exception as e:
            self.log_result("Service layer", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_blueprint_registrations_bottomup(self):
        """Test blueprint registrations from bottom up"""
        print("\n" + "="*60)
        print("🔍 TESTING BLUEPRINT REGISTRATIONS (BOTTOM-UP)")
        print("="*60)
        
        try:
            # Test blueprint imports
            blueprint_modules = [
                'app.forum.routes',
                'app.auth.routes',
                'app.admin.routes',
                'app.api.routes'
            ]
            
            blueprint_errors = []
            for blueprint_module in blueprint_modules:
                try:
                    module = importlib.import_module(blueprint_module)
                    self.log_result(f"Blueprint import: {blueprint_module}", "PASS", f"Imported successfully")
                except ImportError as e:
                    blueprint_errors.append(blueprint_module)
                    self.log_result(f"Blueprint import: {blueprint_module}", "FAIL", f"ImportError: {str(e)}")
                except Exception as e:
                    blueprint_errors.append(blueprint_module)
                    self.log_result(f"Blueprint import: {blueprint_module}", "FAIL", f"Error: {str(e)}")
            
            # Test individual blueprints
            blueprint_tests = [
                ('forum_bp', 'app.forum.routes'),
                ('auth_bp', 'app.auth.routes'),
                ('admin_bp', 'app.admin.routes'),
            ]
            
            blueprint_obj_errors = []
            for blueprint_name, module_path in blueprint_tests:
                try:
                    module = importlib.import_module(module_path)
                    blueprint = getattr(module, blueprint_name)
                    
                    if hasattr(blueprint, 'name'):
                        self.log_result(f"Blueprint: {blueprint_name}", "PASS", f"Blueprint {blueprint_name} has name: {blueprint.name}")
                    else:
                        self.log_result(f"Blueprint: {blueprint_name}", "FAIL", f"Blueprint {blueprint_name} missing name")
                        
                except AttributeError as e:
                    blueprint_obj_errors.append(blueprint_name)
                    self.log_result(f"Blueprint: {blueprint_name}", "FAIL", f"Blueprint not found: {str(e)}")
                except Exception as e:
                    blueprint_obj_errors.append(blueprint_name)
                    self.log_result(f"Blueprint: {blueprint_name}", "FAIL", f"Error: {str(e)}")
            
            return len(blueprint_errors) == 0 and len(blueprint_obj_errors) == 0
            
        except Exception as e:
            self.log_result("Blueprint registrations", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_flask_app_initialization(self):
        """Test Flask app initialization"""
        print("\n" + "="*60)
        print("🔍 TESTING FLASK APP INITIALIZATION")
        print("="*60)
        
        try:
            # Test Flask import
            try:
                from flask import Flask
                self.log_result("Flask import", "PASS", "Flask imported successfully")
            except ImportError as e:
                self.log_result("Flask import", "FAIL", f"ImportError: {str(e)}")
                return False
            
            # Test app creation
            try:
                from app import create_app
                app = create_app()
                self.log_result("Flask app creation", "PASS", "App created successfully")
            except Exception as e:
                self.log_result("Flask app creation", "FAIL", f"Error creating app: {str(e)}")
                return False
            
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
            self.log_result("Flask app initialization", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_authentication_system(self):
        """Test authentication system"""
        print("\n" + "="*60)
        print("🔍 TESTING AUTHENTICATION SYSTEM")
        print("="*60)
        
        try:
            # Test Flask-Login import
            try:
                from flask_login import LoginManager
                self.log_result("Flask-Login import", "PASS", "Flask-Login imported successfully")
            except ImportError as e:
                self.log_result("Flask-Login import", "FAIL", f"ImportError: {str(e)}")
                return False
            
            # Test User model authentication methods
            try:
                from app.models import User
                user = User()
                
                auth_methods = ['set_password', 'check_password']
                for method in auth_methods:
                    if hasattr(user, method):
                        self.log_result(f"User auth method: {method}", "PASS", f"Method {method} exists")
                    else:
                        self.log_result(f"User auth method: {method}", "FAIL", f"Method {method} missing")
                        
            except Exception as e:
                self.log_result("User auth methods", "FAIL", f"Error: {str(e)}")
            
            # Test authentication routes
            try:
                from app.auth.routes import auth_bp
                if hasattr(auth_bp, 'name'):
                    self.log_result("Auth blueprint", "PASS", f"Auth blueprint exists: {auth_bp.name}")
                else:
                    self.log_result("Auth blueprint", "FAIL", "Auth blueprint missing name")
                    
            except Exception as e:
                self.log_result("Auth blueprint", "FAIL", f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_result("Authentication system", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_integration_bottomup(self):
        """Test full integration from bottom to top"""
        print("\n" + "="*60)
        print("🔍 TESTING FULL INTEGRATION (BOTTOM-UP)")
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
            
            # Test model integration
            try:
                from app.models import User, Post, Comment, AuditLog
                from app import create_app
                app = create_app()
                
                with app.app_context():
                    # Test model creation in app context
                    user = User()
                    post = Post()
                    comment = Comment()
                    audit_log = AuditLog()
                    
                    self.log_result("Model integration", "PASS", "All models created in app context")
                    
            except Exception as e:
                self.log_result("Model integration", "FAIL", f"Error: {str(e)}")
            
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
                
                expected_blueprints = ['main', 'auth', 'forum', 'admin']
                missing_blueprints = []
                
                for expected_bp in expected_blueprints:
                    if expected_bp in registered_blueprints:
                        self.log_result(f"Blueprint integration: {expected_bp}", "PASS", f"Blueprint {expected_bp} registered")
                    else:
                        missing_blueprints.append(expected_bp)
                        self.log_result(f"Blueprint integration: {expected_bp}", "FAIL", f"Blueprint {expected_bp} not registered")
                    
            except Exception as e:
                self.log_result("Blueprint integration", "FAIL", f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_result("Full integration", "FAIL", f"Error: {str(e)}")
            return False
    
    def generate_report(self):
        """Generate comprehensive bottom-up integrity report"""
        print("\n" + "="*60)
        print("📊 BOTTOM-UP SYSTEM INTEGRITY REPORT")
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
        
        # Bottom-up integrity assessment
        print(f"\n🔍 Bottom-Up Integrity Assessment:")
        
        if failed_tests == 0:
            print("   🟢 SYSTEM INTEGRITY: EXCELLENT")
            print("   🎉 All layers properly wired from bottom to top")
        elif failed_tests <= 3:
            print("   🟡 SYSTEM INTEGRITY: GOOD")
            print("   ⚡ Minor issues found, system mostly functional")
        elif failed_tests <= 7:
            print("   🟠 SYSTEM INTEGRITY: FAIR")
            print("   🔧 Several issues found, needs attention")
        else:
            print("   🔴 SYSTEM INTEGRITY: POOR")
            print("   🚨 Major issues found, requires immediate attention")
        
        # Layer-by-layer analysis
        print(f"\n🏗️  Layer-by-Layer Analysis:")
        
        layer_results = {
            'Database Layer': [r for r in self.results if 'database' in r['test_name'].lower()],
            'Model Layer': [r for r in self.results if 'model' in r['test_name'].lower()],
            'Service Layer': [r for r in self.results if 'service' in r['test_name'].lower()],
            'Blueprint Layer': [r for r in self.results if 'blueprint' in r['test_name'].lower()],
            'Application Layer': [r for r in self.results if 'flask' in r['test_name'].lower() or 'auth' in r['test_name'].lower()],
            'Integration Layer': [r for r in self.results if 'integration' in r['test_name'].lower()]
        }
        
        for layer_name, layer_tests in layer_results.items():
            if layer_tests:
                layer_passed = len([t for t in layer_tests if t['status'] == 'PASS'])
                layer_total = len(layer_tests)
                layer_rate = (layer_passed/layer_total*100) if layer_total > 0 else 0
                
                if layer_rate >= 90:
                    status_icon = "🟢"
                elif layer_rate >= 70:
                    status_icon = "🟡"
                else:
                    status_icon = "🔴"
                
                print(f"   {status_icon} {layer_name}: {layer_passed}/{layer_total} ({layer_rate:.1f}%)")
        
        # Recommendations
        print(f"\n💡 Bottom-Up Recommendations:")
        if failed_tests > 0:
            print("   1. Fix database layer issues first (foundation)")
            print("   2. Resolve model layer conflicts")
            print("   3. Fix service layer integration")
            print("   4. Ensure blueprint registration works")
            print("   5. Validate application layer functionality")
        
        if warning_tests > 0:
            print("   6. Address warnings to improve system robustness")
        
        print("   7. Test changes layer by layer")
        print("   8. Validate integration after each layer fix")
        
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
            'warnings': self.warnings,
            'layer_results': layer_results
        }
    
    def run_all_tests(self):
        """Run all bottom-up integrity tests"""
        print("🚀 STARTING BOTTOM-UP SYSTEM INTEGRITY TESTS")
        print(f"📅 Started at: {self.start_time}")
        print(f"📁 Project Root: {project_root}")
        print("🔍 Testing from bottom (database) to top (integration)")
        
        test_methods = [
            self.test_database_configuration,
            self.test_database_connection,
            self.test_individual_models_bottomup,
            self.test_model_relationships_bottomup,
            self.test_service_layer_bottomup,
            self.test_blueprint_registrations_bottomup,
            self.test_flask_app_initialization,
            self.test_authentication_system,
            self.test_integration_bottomup
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_result(f"Test method: {test_method.__name__}", "FAIL", f"Test execution error: {str(e)}")
        
        return self.generate_report()

def main():
    """Main function to run bottom-up integrity tests"""
    tester = BottomUpIntegrityTester()
    report = tester.run_all_tests()
    
    # Save report to file
    report_file = os.path.join(project_root, 'tests', 'bottomup_integrity_report.json')
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
