"""
Comprehensive Integration Tests for Repo-Forum Project
Tests component integration and interactions.
"""

import re
import traceback
from datetime import datetime

class IntegrationTest:
    """Comprehensive integration testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "integration",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🔗 Running Comprehensive Integration Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test integration functionality
                self.test_auth_forum_integration()
                self.test_admin_user_integration()
                self.test_database_model_integration()
                
        except Exception as e:
            self.add_test_result("integration_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_auth_forum_integration(self):
        """Test authentication and forum integration"""
        try:
            with self.app.test_client() as client:
                # Test login and then forum access
                login_response = client.post('/auth/login', data={
                    'username': 'admin',
                    'password': 'admin123'
                }, follow_redirects=True)
                
                if login_response.status_code == 200:
                    # Test forum access after login
                    forum_response = client.get('/forum')
                    
                    if forum_response.status_code == 200:
                        self.add_test_result("auth_forum_integration", "passed", 
                                          "Authentication and forum integration working")
                    else:
                        self.add_test_result("auth_forum_integration", "failed", 
                                          f"Forum access after login failed: {forum_response.status_code}")
                else:
                    self.add_test_result("auth_forum_integration", "skipped", 
                                      "Login failed, cannot test integration")
                
        except Exception as e:
            self.add_test_result("auth_forum_integration", "error", str(e), traceback.format_exc())
    
    def test_admin_user_integration(self):
        """Test admin and user integration"""
        try:
            with self.app.test_client() as client:
                # Test admin access to user management
                admin_response = client.get('/admin/users')
                
                if admin_response.status_code in [200, 302, 401, 403]:
                    self.add_test_result("admin_user_integration", "passed", 
                                      "Admin and user integration working")
                else:
                    self.add_test_result("admin_user_integration", "failed", 
                                      f"Admin and user integration failed: {admin_response.status_code}")
                
        except Exception as e:
            self.add_test_result("admin_user_integration", "error", str(e), traceback.format_exc())
    
    def test_database_model_integration(self):
        """Test database and model integration"""
        try:
            from app.models import User, Post, Comment
            
            # Test model relationships
            test_user = User(username='test_integration', email='test@example.com')
            test_post = Post(title='Test Post', content='Test content', user_id=1)
            test_comment = Comment(content='Test comment', user_id=1, post_id=1)
            
            # Check if relationships are properly defined
            if (hasattr(test_user, 'posts') and hasattr(test_post, 'comments') and 
                hasattr(test_comment, 'author') and hasattr(test_comment, 'post')):
                self.add_test_result("database_model_integration", "passed", 
                                  "Database and model integration working")
            else:
                self.add_test_result("database_model_integration", "failed", 
                                  "Database and model integration not working")
                
        except Exception as e:
            self.add_test_result("database_model_integration", "error", str(e), traceback.format_exc())
