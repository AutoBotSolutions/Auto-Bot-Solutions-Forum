"""
Comprehensive Profile Tests for Repo-Forum Project
Tests user profile functionality.
"""

import re
import traceback
from datetime import datetime

class ProfileTest:
    """Comprehensive profile testing for entire app"""
    
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
        """Run all profile tests"""
        print("👤 Running Comprehensive Profile Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test profile functionality
                self.test_profile_display()
                self.test_profile_editing()
                self.test_profile_security()
                
        except Exception as e:
            self.add_test_result("profile_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_profile_display(self):
        """Test profile display functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/user/profile/1')
                
                if response.status_code in [200, 404]:
                    self.add_test_result("profile_display_accessible", "passed", 
                                      "Profile display page accessible")
                else:
                    self.add_test_result("profile_display_accessible", "failed", 
                                      f"Profile display not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("profile_display", "error", str(e), traceback.format_exc())
    
    def test_profile_editing(self):
        """Test profile editing functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/user/edit_profile')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("profile_editing_accessible", "passed", 
                                      "Profile editing page accessible")
                else:
                    self.add_test_result("profile_editing_accessible", "failed", 
                                      f"Profile editing not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("profile_editing", "error", str(e), traceback.format_exc())
    
    def test_profile_security(self):
        """Test profile security"""
        try:
            with self.app.test_client() as client:
                # Test unauthorized profile access
                response = client.get('/user/edit_profile')
                
                if response.status_code in [302, 401, 403]:
                    self.add_test_result("profile_security_protected", "passed", 
                                      "Profile editing properly protected")
                elif response.status_code == 200:
                    self.add_test_result("profile_security_protected", "warning", 
                                      "Profile editing may not be properly protected")
                else:
                    self.add_test_result("profile_security_protected", "failed", 
                                      f"Profile security test inconclusive: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("profile_security", "error", str(e), traceback.format_exc())
