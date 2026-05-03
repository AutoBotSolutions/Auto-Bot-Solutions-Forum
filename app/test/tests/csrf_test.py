"""
Comprehensive CSRF Tests for Repo-Forum Project
Tests CSRF protection functionality.
"""

import re
import traceback
from datetime import datetime

class CSRFTest:
    """Comprehensive CSRF testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "security",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all CSRF tests"""
        print("🔒 Running Comprehensive CSRF Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test CSRF functionality
                self.test_csrf_configuration()
                self.test_csrf_tokens()
                self.test_csrf_protection()
                
        except Exception as e:
            self.add_test_result("csrf_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_csrf_configuration(self):
        """Test CSRF configuration"""
        try:
            if hasattr(self.app, 'config'):
                config = self.app.config
                
                if config.get('WTF_CSRF_ENABLED', False):
                    self.add_test_result("csrf_configuration_enabled", "passed", 
                                      "CSRF protection is enabled")
                else:
                    self.add_test_result("csrf_configuration_enabled", "failed", 
                                      "CSRF protection is disabled")
            else:
                self.add_test_result("csrf_configuration", "failed", 
                                  "App configuration not accessible")
                
        except Exception as e:
            self.add_test_result("csrf_configuration", "error", str(e), traceback.format_exc())
    
    def test_csrf_tokens(self):
        """Test CSRF token functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/auth/login')
                
                if response.status_code == 200:
                    if b'csrf' in response.data.lower():
                        self.add_test_result("csrf_tokens_present", "passed", 
                                          "CSRF tokens present in forms")
                    else:
                        self.add_test_result("csrf_tokens_present", "warning", 
                                          "CSRF tokens not found in forms")
                else:
                    self.add_test_result("csrf_tokens_testing", "skipped", 
                                      "Login form not accessible")
                
        except Exception as e:
            self.add_test_result("csrf_tokens", "error", str(e), traceback.format_exc())
    
    def test_csrf_protection(self):
        """Test CSRF protection functionality"""
        try:
            with self.app.test_client() as client:
                response = client.post('/auth/login', data={
                    'username': 'test',
                    'password': 'test'
                })
                
                if response.status_code in [400, 403]:
                    self.add_test_result("csrf_protection_working", "passed", 
                                      "CSRF protection working")
                else:
                    self.add_test_result("csrf_protection_working", "warning", 
                                      "CSRF protection may not be working")
                
        except Exception as e:
            self.add_test_result("csrf_protection", "error", str(e), traceback.format_exc())
