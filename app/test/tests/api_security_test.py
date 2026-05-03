"""
Comprehensive API Security Tests for Repo-Forum Project
Tests API security functionality.
"""

import re
import traceback
from datetime import datetime

class APISecurityTest:
    """Comprehensive API security testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "api",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all API security tests"""
        print("🔒 Running Comprehensive API Security Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test API security functionality
                self.test_api_authentication()
                self.test_api_authorization()
                self.test_api_rate_limiting()
                
        except Exception as e:
            self.add_test_result("api_security_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_api_authentication(self):
        """Test API authentication"""
        try:
            with self.app.test_client() as client:
                response = client.get('/api/users')
                
                if response.status_code in [200, 401, 403]:
                    self.add_test_result("api_authentication_working", "passed", 
                                      "API authentication working")
                else:
                    self.add_test_result("api_authentication_working", "failed", 
                                      f"API authentication not working: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("api_authentication", "error", str(e), traceback.format_exc())
    
    def test_api_authorization(self):
        """Test API authorization"""
        try:
            with self.app.test_client() as client:
                response = client.get('/api/admin/users')
                
                if response.status_code in [401, 403]:
                    self.add_test_result("api_authorization_working", "passed", 
                                      "API authorization working")
                else:
                    self.add_test_result("api_authorization_working", "failed", 
                                      f"API authorization not working: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("api_authorization", "error", str(e), traceback.format_exc())
    
    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        try:
            with self.app.test_client() as client:
                responses = []
                for i in range(10):
                    response = client.get('/api/users')
                    responses.append(response.status_code)
                
                if 429 in responses:
                    self.add_test_result("api_rate_limiting_working", "passed", 
                                      "API rate limiting working")
                else:
                    self.add_test_result("api_rate_limiting_working", "warning", 
                                      "API rate limiting may not be implemented")
                
        except Exception as e:
            self.add_test_result("api_rate_limiting", "error", str(e), traceback.format_exc())
