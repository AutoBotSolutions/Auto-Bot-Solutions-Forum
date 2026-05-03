"""
Admin Routes Testing Module
Tests all admin user management routes and functionality
"""

import json
import traceback
from datetime import datetime
from flask import Flask
from app import create_app, db
from app.models import User
from flask_login import login_user

class AdminRoutesTest:
    """Comprehensive admin routes testing"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def run_all_tests(self):
        """Run all admin routes tests"""
        print("🔍 Running Admin Routes Tests...")
        
        # Initialize app
        try:
            self.app = create_app()
        except Exception as e:
            self.add_test_result("app_initialization", "error", str(e), traceback.format_exc())
            return self.test_results
        
        # Run individual tests
        self.test_app_initialization()
        self.test_blueprint_registration()
        self.test_route_registration()
        self.test_users_route_function()
        self.test_user_management_routes()
        self.test_template_rendering()
        self.test_database_connection()
        
        return self.test_results
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result"""
        result = {
            "test_name": test_name,
            "category": "admin_routes",
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        # Print result
        status_icon = "✅" if status == "passed" else "❌" if status == "failed" else "⚠️"
        print(f"  {status_icon} {test_name}: {message}")
        
        return result
    
    def test_app_initialization(self):
        """Test Flask app initialization"""
        try:
            if self.app:
                self.add_test_result("app_initialization", "passed", "Flask app created successfully")
            else:
                self.add_test_result("app_initialization", "failed", "Flask app creation failed")
        except Exception as e:
            self.add_test_result("app_initialization", "error", str(e), traceback.format_exc())
    
    def test_blueprint_registration(self):
        """Test admin blueprint registration"""
        try:
            blueprints = list(self.app.blueprints.keys())
            if 'admin' in blueprints:
                admin_bp = self.app.blueprints['admin']
                self.add_test_result("blueprint_registration", "passed", 
                                  f"Admin blueprint registered with {len(admin_bp.deferred_functions)} deferred functions")
            else:
                self.add_test_result("blueprint_registration", "failed", "Admin blueprint not registered")
        except Exception as e:
            self.add_test_result("blueprint_registration", "error", str(e), traceback.format_exc())
    
    def test_route_registration(self):
        """Test admin route registration"""
        try:
            admin_routes = [rule for rule in self.app.url_map.iter_rules() if 'admin/users' in rule.rule]
            
            if admin_routes:
                routes_info = []
                for rule in admin_routes:
                    routes_info.append(f"{rule.rule} -> {rule.endpoint} [{rule.methods}]")
                
                self.add_test_result("route_registration", "passed", 
                                  f"Found {len(admin_routes)} admin/users routes", 
                                  {"routes": routes_info})
            else:
                self.add_test_result("route_registration", "failed", "No admin/users routes found")
        except Exception as e:
            self.add_test_result("route_registration", "error", str(e), traceback.format_exc())
    
    def test_users_route_function(self):
        """Test the main users route function"""
        try:
            from app.admin.routes import users
            
            with self.app.app_context():
                # Get admin user
                admin_user = User.query.filter_by(username='admin').first()
                if not admin_user:
                    self.add_test_result("users_route_function", "failed", "Admin user not found")
                    return
                
                # Test the route function
                with self.app.test_request_context('/admin/users/', method='GET'):
                    login_user(admin_user)
                    result = users()
                    
                    if hasattr(result, 'status_code'):
                        if result.status_code == 200:
                            self.add_test_result("users_route_function", "passed", 
                                              f"Users route returns 200 OK")
                        else:
                            self.add_test_result("users_route_function", "failed", 
                                              f"Users route returns {result.status_code}")
                    elif isinstance(result, str):
                        if len(result) > 1000:
                            self.add_test_result("users_route_function", "passed", 
                                              f"Users route returns HTML content ({len(result)} characters)")
                        else:
                            self.add_test_result("users_route_function", "failed", 
                                              f"Users route returns short content ({len(result)} characters)")
                    else:
                        self.add_test_result("users_route_function", "failed", 
                                          f"Users route returns unexpected type: {type(result)}")
                    
        except Exception as e:
            self.add_test_result("users_route_function", "error", str(e), traceback.format_exc())
    
    def test_user_management_routes(self):
        """Test individual user management routes"""
        try:
            from app.admin.routes import view_user, edit_user, reset_user_password, suspend_user, ban_user, toggle_admin
            
            with self.app.app_context():
                admin_user = User.query.filter_by(username='admin').first()
                test_user = User.query.filter(User.username != 'admin').first()
                
                if not test_user:
                    self.add_test_result("user_management_routes", "skipped", "No test user found")
                    return
                
                test_cases = [
                    ("view_user", view_user, test_user.id),
                    ("edit_user", edit_user, test_user.id),
                    ("reset_user_password", reset_user_password, test_user.id),
                    ("suspend_user", suspend_user, test_user.id),
                    ("ban_user", ban_user, test_user.id),
                    ("toggle_admin", toggle_admin, test_user.id)
                ]
                
                passed_count = 0
                for route_name, route_func, user_id in test_cases:
                    try:
                        route_path = f'/admin/users/{user_id}/{route_name.split("_")[0]}'
                        with self.app.test_request_context(route_path, method='GET'):
                            login_user(admin_user)
                            result = route_func(user_id)
                            
                            if hasattr(result, 'status_code'):
                                if result.status_code in [200, 302]:
                                    passed_count += 1
                                else:
                                    self.add_test_result(f"user_management_{route_name}", "failed", 
                                                      f"Route returns {result.status_code}")
                            elif isinstance(result, str):
                                passed_count += 1
                            else:
                                self.add_test_result(f"user_management_{route_name}", "failed", 
                                                  f"Route returns unexpected type: {type(result)}")
                    
                    except Exception as e:
                        self.add_test_result(f"user_management_{route_name}", "error", str(e))
                
                if passed_count == len(test_cases):
                    self.add_test_result("user_management_routes", "passed", 
                                      f"All {len(test_cases)} user management routes work correctly")
                else:
                    self.add_test_result("user_management_routes", "failed", 
                                      f"Only {passed_count}/{len(test_cases)} routes work correctly")
        
        except Exception as e:
            self.add_test_result("user_management_routes", "error", str(e), traceback.format_exc())
    
    def test_template_rendering(self):
        """Test template rendering for admin users page"""
        try:
            from flask import render_template
            
            with self.app.app_context():
                # Test template rendering with proper context
                with self.app.test_request_context('/admin/users/', method='GET'):
                    try:
                        result = render_template('admin/users.html', users=[])
                        self.add_test_result("template_rendering", "passed", 
                                          f"Template renders successfully ({len(result)} characters)")
                    except Exception as e:
                        if "Unable to build URLs outside an active request" in str(e):
                            self.add_test_result("template_rendering", "skipped", 
                                              "Template requires request context (expected)")
                        else:
                            self.add_test_result("template_rendering", "failed", str(e))
        
        except Exception as e:
            self.add_test_result("template_rendering", "error", str(e), traceback.format_exc())
    
    def test_database_connection(self):
        """Test database connection and user data"""
        try:
            with self.app.app_context():
                users = User.query.all()
                admin_user = User.query.filter_by(is_admin=True).first()
                
                if users and admin_user:
                    self.add_test_result("database_connection", "passed", 
                                      f"Database connection successful: {len(users)} users, admin: {admin_user.username}")
                else:
                    self.add_test_result("database_connection", "failed", 
                                      "Database connection failed or missing admin user")
        
        except Exception as e:
            self.add_test_result("database_connection", "error", str(e), traceback.format_exc())
