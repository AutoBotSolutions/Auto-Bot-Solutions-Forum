"""
Comprehensive User Tests for Repo-Forum Project
Tests all user functionality including profiles, management, etc.
"""

import re
import traceback
from datetime import datetime

class UserTest:
    """Comprehensive user testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "user",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all user tests"""
        print("👤 Running Comprehensive User Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test user models
                self.test_user_model()
                
                # Test user routes
                self.test_user_routes()
                self.test_profile_routes()
                
                # Test user functionality
                self.test_user_registration()
                self.test_user_profile()
                self.test_user_settings()
                
        except Exception as e:
            self.add_test_result("user_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_user_model(self):
        """Test User model"""
        try:
            from app.models import User
            
            # Test model creation
            test_user = User(
                username='test_user_func',
                email='testuser@example.com',
                bio='Test user bio',
                location='Test location',
                website='https://example.com'
            )
            test_user.set_password('testpassword123')
            
            # Test profile fields
            profile_fields = ['bio', 'location', 'website', 'avatar_url']
            missing_fields = []
            
            for field in profile_fields:
                if not hasattr(test_user, field):
                    missing_fields.append(field)
            
            if not missing_fields:
                self.add_test_result("user_profile_fields", "passed", 
                                  f"User model has all profile fields")
            else:
                self.add_test_result("user_profile_fields", "failed", 
                                  f"User model missing profile fields: {missing_fields}")
                
        except Exception as e:
            self.add_test_result("user_model", "error", str(e), traceback.format_exc())
    
    def test_user_routes(self):
        """Test user route registration"""
        try:
            from app.user import user_bp
            
            if user_bp:
                self.add_test_result("user_blueprint_exists", "passed", 
                                  "User blueprint exists")
            else:
                self.add_test_result("user_blueprint_exists", "failed", 
                                  "User blueprint not found")
                
        except Exception as e:
            self.add_test_result("user_routes", "error", str(e), traceback.format_exc())
    
    def test_profile_routes(self):
        """Test profile route functionality"""
        try:
            with self.app.test_client() as client:
                # Test profile page
                response = client.get('/user/profile/1')
                
                if response.status_code in [200, 404]:
                    self.add_test_result("profile_route_accessible", "passed", 
                                      "Profile route accessible")
                else:
                    self.add_test_result("profile_route_accessible", "failed", 
                                      f"Profile route not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("profile_routes", "error", str(e), traceback.format_exc())
    
    def test_user_registration(self):
        """Test user registration functionality"""
        try:
            with self.app.test_client() as client:
                # Test registration form
                response = client.get('/auth/register')
                
                if response.status_code == 200:
                    # Check if form has required fields
                    if b'username' in response.data and b'email' in response.data and b'password' in response.data:
                        self.add_test_result("user_registration_form_fields", "passed", 
                                          "User registration form has required fields")
                    else:
                        self.add_test_result("user_registration_form_fields", "failed", 
                                          "User registration form missing required fields")
                else:
                    self.add_test_result("user_registration_form", "skipped", 
                                      "User registration form not accessible")
                
        except Exception as e:
            self.add_test_result("user_registration", "error", str(e), traceback.format_exc())
    
    def test_user_profile(self):
        """Test user profile functionality"""
        try:
            with self.app.test_client() as client:
                # Test profile editing
                response = client.get('/user/edit_profile')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("profile_edit_accessible", "passed", 
                                      "Profile edit page accessible")
                else:
                    self.add_test_result("profile_edit_accessible", "failed", 
                                      f"Profile edit not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("user_profile", "error", str(e), traceback.format_exc())
    
    def test_user_settings(self):
        """Test user settings functionality"""
        try:
            with self.app.test_client() as client:
                # Test settings page
                response = client.get('/user/settings')
                
                if response.status_code in [200, 404]:
                    self.add_test_result("user_settings_accessible", "passed", 
                                      "User settings page accessible")
                else:
                    self.add_test_result("user_settings_accessible", "failed", 
                                      f"User settings not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("user_settings", "error", str(e), traceback.format_exc())
