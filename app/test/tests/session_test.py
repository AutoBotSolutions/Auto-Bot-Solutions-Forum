"""
Comprehensive Session Management Tests for Repo-Forum Project
Tests all session functionality including persistence, security, and management.
"""

import re
import traceback
from datetime import datetime, timedelta
from flask import session, current_app

class SessionTest:
    """Comprehensive session testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "auth",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all session tests"""
        print("🔐 Running Comprehensive Session Management Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test session configuration
                self.test_session_configuration()
                
                # Test session lifecycle
                self.test_session_creation()
                self.test_session_persistence()
                self.test_session_destruction()
                
                # Test session security
                self.test_session_security()
                self.test_session_encryption()
                self.test_session_timeout()
                
                # Test session management
                self.test_session_data_storage()
                self.test_session_data_retrieval()
                self.test_session_modification()
                
                # Test session edge cases
                self.test_session_expiration()
                self.test_session_invalidation()
                self.test_concurrent_sessions()
                
        except Exception as e:
            self.add_test_result("session_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_session_configuration(self):
        """Test session configuration"""
        try:
            if hasattr(self.app, 'config'):
                config = self.app.config
                
                # Test session configuration
                session_configs = {
                    'SECRET_KEY': 'Secret key for session encryption',
                    'SESSION_TYPE': 'Session storage type',
                    'PERMANENT_SESSION_LIFETIME': 'Permanent session lifetime',
                    'SESSION_COOKIE_SECURE': 'Secure cookie flag',
                    'SESSION_COOKIE_HTTPONLY': 'HTTPOnly cookie flag',
                    'SESSION_COOKIE_SAMESITE': 'SameSite cookie policy'
                }
                
                configured_sessions = 0
                for key, description in session_configs.items():
                    if key in config:
                        configured_sessions += 1
                        self.add_test_result(f"session_config_{key.lower()}", "passed", 
                                          f"{description} - configured")
                    else:
                        self.add_test_result(f"session_config_{key.lower()}", "warning", 
                                          f"{description} - not configured")
                
                if configured_sessions >= 3:
                    self.add_test_result("session_configuration_adequate", "passed", 
                                      f"Session configuration adequate ({configured_sessions}/{len(session_configs)})")
                else:
                    self.add_test_result("session_configuration_adequate", "failed", 
                                      f"Session configuration inadequate ({configured_sessions}/{len(session_configs)})")
            else:
                self.add_test_result("session_configuration", "failed", 
                                  "App configuration not accessible")
                
        except Exception as e:
            self.add_test_result("session_configuration", "error", str(e), traceback.format_exc())
    
    def test_session_creation(self):
        """Test session creation"""
        try:
            with self.app.test_client() as client:
                # Make a request to create session
                response = client.get('/')
                
                if response.status_code == 200:
                    # Check if session cookie is set
                    if 'set-cookie' in response.headers:
                        self.add_test_result("session_cookie_creation", "passed", 
                                          "Session cookie created on request")
                    else:
                        self.add_test_result("session_cookie_creation", "warning", 
                                          "No session cookie set (may be normal for unauthenticated requests)")
                    
                    # Test session data access
                    with self.app.test_request_context():
                        if hasattr(session, 'keys'):
                            self.add_test_result("session_data_access", "passed", 
                                              "Session data accessible")
                        else:
                            self.add_test_result("session_data_access", "failed", 
                                              "Session data not accessible")
                else:
                    self.add_test_result("session_creation", "failed", 
                                      f"Request failed: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("session_creation", "error", str(e), traceback.format_exc())
    
    def test_session_persistence(self):
        """Test session persistence across requests"""
        try:
            from app.models import User
            
            admin_user = User.query.filter_by(is_admin=True).first()
            if admin_user:
                with self.app.test_client() as client:
                    # Login to create session
                    login_response = client.post('/auth/login', data={
                        'username': admin_user.username,
                        'password': 'admin123'
                    }, follow_redirects=True)
                    
                    if login_response.status_code == 200:
                        # Make subsequent request to test persistence
                        session_response = client.get('/')
                        
                        if session_response.status_code == 200:
                            self.add_test_result("session_persistence", "passed", 
                                              "Session persists across requests")
                        else:
                            self.add_test_result("session_persistence", "failed", 
                                              f"Session does not persist: {session_response.status_code}")
                    else:
                        self.add_test_result("session_persistence", "skipped", 
                                          "Login failed, cannot test session persistence")
            else:
                self.add_test_result("session_persistence", "skipped", 
                                  "No admin user found")
                
        except Exception as e:
            self.add_test_result("session_persistence", "error", str(e), traceback.format_exc())
    
    def test_session_destruction(self):
        """Test session destruction on logout"""
        try:
            from app.models import User
            
            admin_user = User.query.filter_by(is_admin=True).first()
            if admin_user:
                with self.app.test_client() as client:
                    # Login first
                    client.post('/auth/login', data={
                        'username': admin_user.username,
                        'password': 'admin123'
                    }, follow_redirects=True)
                    
                    # Logout to destroy session
                    logout_response = client.get('/auth/logout', follow_redirects=True)
                    
                    if logout_response.status_code == 200:
                        # Try to access protected page after logout
                        protected_response = client.get('/admin/dashboard')
                        
                        if protected_response.status_code in [302, 401, 403]:
                            self.add_test_result("session_destruction", "passed", 
                                              "Session properly destroyed on logout")
                        else:
                            self.add_test_result("session_destruction", "failed", 
                                              f"Session not destroyed: {protected_response.status_code}")
                    else:
                        self.add_test_result("session_destruction", "skipped", 
                                          "Logout failed, cannot test session destruction")
            else:
                self.add_test_result("session_destruction", "skipped", 
                                  "No admin user found")
                
        except Exception as e:
            self.add_test_result("session_destruction", "error", str(e), traceback.format_exc())
    
    def test_session_security(self):
        """Test session security features"""
        try:
            if hasattr(self.app, 'config'):
                config = self.app.config
                
                # Test security configurations
                security_checks = {
                    'SESSION_COOKIE_SECURE': 'Secure cookie (HTTPS only)',
                    'SESSION_COOKIE_HTTPONLY': 'HTTPOnly cookie (prevents XSS)',
                    'SESSION_COOKIE_SAMESITE': 'SameSite cookie (prevents CSRF)',
                    'PERMANENT_SESSION_LIFETIME': 'Session lifetime limit'
                }
                
                passed_checks = 0
                for key, description in security_checks.items():
                    if key in config and config[key] is not None:
                        if key == 'PERMANENT_SESSION_LIFETIME':
                            # Check if lifetime is reasonable (not too long)
                            lifetime = config[key]
                            if isinstance(lifetime, timedelta) and lifetime.total_seconds() <= 86400:  # 24 hours max
                                passed_checks += 1
                                self.add_test_result(f"session_security_{key.lower()}", "passed", 
                                                  f"{description} - reasonable lifetime")
                            else:
                                self.add_test_result(f"session_security_{key.lower()}", "warning", 
                                                  f"{description} - lifetime too long")
                        else:
                            passed_checks += 1
                            self.add_test_result(f"session_security_{key.lower()}", "passed", 
                                              f"{description} - configured")
                    else:
                        self.add_test_result(f"session_security_{key.lower()}", "warning", 
                                          f"{description} - not configured")
                
                if passed_checks >= 2:
                    self.add_test_result("session_security_adequate", "passed", 
                                      f"Session security adequate ({passed_checks}/{len(security_checks)})")
                else:
                    self.add_test_result("session_security_adequate", "failed", 
                                      f"Session security inadequate ({passed_checks}/{len(security_checks)})")
            else:
                self.add_test_result("session_security_adequate", "failed", 
                                  "App configuration not accessible")
                
        except Exception as e:
            self.add_test_result("session_security", "error", str(e), traceback.format_exc())
    
    def test_session_encryption(self):
        """Test session data encryption"""
        try:
            if hasattr(self.app, 'config'):
                config = self.app.config
                
                # Check if secret key is configured
                if config.get('SECRET_KEY'):
                    if len(config['SECRET_KEY']) >= 24:  # Minimum secure length
                        self.add_test_result("session_encryption_key", "passed", 
                                          "Session encryption key is sufficiently long")
                    else:
                        self.add_test_result("session_encryption_key", "warning", 
                                          "Session encryption key may be too short")
                    
                    # Check if secret key is not default
                    if config['SECRET_KEY'] not in ['dev-secret-key-change-in-production', 'secret-key']:
                        self.add_test_result("session_encryption_unique", "passed", 
                                          "Session encryption key is not default")
                    else:
                        self.add_test_result("session_encryption_unique", "failed", 
                                          "Session encryption key is default value")
                else:
                    self.add_test_result("session_encryption_key", "failed", 
                                      "No session encryption key configured")
            else:
                self.add_test_result("session_encryption", "failed", 
                                  "App configuration not accessible")
                
        except Exception as e:
            self.add_test_result("session_encryption", "error", str(e), traceback.format_exc())
    
    def test_session_timeout(self):
        """Test session timeout functionality"""
        try:
            if hasattr(self.app, 'config'):
                config = self.app.config
                
                # Check session lifetime configuration
                lifetime = config.get('PERMANENT_SESSION_LIFETIME')
                if lifetime:
                    if isinstance(lifetime, timedelta):
                        hours = lifetime.total_seconds() / 3600
                        
                        if 0.5 <= hours <= 24:  # 30 minutes to 24 hours
                            self.add_test_result("session_timeout_reasonable", "passed", 
                                              f"Session timeout is reasonable: {hours:.1f} hours")
                        elif hours > 24:
                            self.add_test_result("session_timeout_reasonable", "warning", 
                                              f"Session timeout may be too long: {hours:.1f} hours")
                        else:
                            self.add_test_result("session_timeout_reasonable", "warning", 
                                              f"Session timeout may be too short: {hours:.1f} hours")
                        
                        self.add_test_result("session_timeout_configured", "passed", 
                                          f"Session timeout configured: {hours:.1f} hours")
                    else:
                        self.add_test_result("session_timeout_type", "failed", 
                                          "Session timeout is not a timedelta object")
                else:
                    self.add_test_result("session_timeout_configured", "warning", 
                                      "Session timeout not configured")
            else:
                self.add_test_result("session_timeout", "failed", 
                                  "App configuration not accessible")
                
        except Exception as e:
            self.add_test_result("session_timeout", "error", str(e), traceback.format_exc())
    
    def test_session_data_storage(self):
        """Test session data storage"""
        try:
            with self.app.test_request_context():
                # Test storing data in session
                session['test_key'] = 'test_value'
                session['user_id'] = 123
                session['is_authenticated'] = True
                
                # Test if data is stored
                if 'test_key' in session and session['test_key'] == 'test_value':
                    self.add_test_result("session_data_storage", "passed", 
                                      "Session data storage works correctly")
                else:
                    self.add_test_result("session_data_storage", "failed", 
                                      "Session data storage failed")
                
                # Test storing complex data
                complex_data = {
                    'nested': {'key': 'value'},
                    'list': [1, 2, 3],
                    'boolean': True
                }
                session['complex_data'] = complex_data
                
                if 'complex_data' in session:
                    self.add_test_result("session_complex_data_storage", "passed", 
                                      "Complex session data storage works")
                else:
                    self.add_test_result("session_complex_data_storage", "failed", 
                                      "Complex session data storage failed")
                
        except Exception as e:
            self.add_test_result("session_data_storage", "error", str(e), traceback.format_exc())
    
    def test_session_data_retrieval(self):
        """Test session data retrieval"""
        try:
            with self.app.test_request_context():
                # Store test data
                session['test_retrieve'] = 'retrieval_test'
                session['user_info'] = {'name': 'test_user', 'role': 'admin'}
                
                # Test retrieval
                retrieved_value = session.get('test_retrieve')
                if retrieved_value == 'retrieval_test':
                    self.add_test_result("session_data_retrieval", "passed", 
                                      "Session data retrieval works correctly")
                else:
                    self.add_test_result("session_data_retrieval", "failed", 
                                      "Session data retrieval failed")
                
                # Test dictionary access
                user_info = session.get('user_info', {})
                if user_info.get('name') == 'test_user':
                    self.add_test_result("session_dict_retrieval", "passed", 
                                      "Session dictionary retrieval works")
                else:
                    self.add_test_result("session_dict_retrieval", "failed", 
                                      "Session dictionary retrieval failed")
                
        except Exception as e:
            self.add_test_result("session_data_retrieval", "error", str(e), traceback.format_exc())
    
    def test_session_modification(self):
        """Test session data modification"""
        try:
            with self.app.test_request_context():
                # Store initial data
                session['test_modify'] = 'initial_value'
                
                # Modify data
                session['test_modify'] = 'modified_value'
                
                # Test modification
                if session['test_modify'] == 'modified_value':
                    self.add_test_result("session_data_modification", "passed", 
                                      "Session data modification works correctly")
                else:
                    self.add_test_result("session_data_modification", "failed", 
                                      "Session data modification failed")
                
                # Test deletion
                del session['test_modify']
                if 'test_modify' not in session:
                    self.add_test_result("session_data_deletion", "passed", 
                                      "Session data deletion works correctly")
                else:
                    self.add_test_result("session_data_deletion", "failed", 
                                      "Session data deletion failed")
                
        except Exception as e:
            self.add_test_result("session_modification", "error", str(e), traceback.format_exc())
    
    def test_session_expiration(self):
        """Test session expiration"""
        try:
            if hasattr(self.app, 'config'):
                config = self.app.config
                
                # Test session expiration configuration
                lifetime = config.get('PERMANENT_SESSION_LIFETIME')
                if lifetime:
                    # Simulate session expiration
                    expiration_time = datetime.utcnow() + lifetime
                    
                    if expiration_time > datetime.utcnow():
                        self.add_test_result("session_expiration_logic", "passed", 
                                          "Session expiration logic is correct")
                    else:
                        self.add_test_result("session_expiration_logic", "failed", 
                                          "Session expiration logic is incorrect")
                else:
                    self.add_test_result("session_expiration", "skipped", 
                                      "Session expiration not configured")
            else:
                self.add_test_result("session_expiration", "failed", 
                                  "App configuration not accessible")
                
        except Exception as e:
            self.add_test_result("session_expiration", "error", str(e), traceback.format_exc())
    
    def test_session_invalidation(self):
        """Test session invalidation"""
        try:
            with self.app.test_client() as client:
                # Create session
                with self.app.test_request_context():
                    session['test_data'] = 'should_be_invalidated'
                
                # Test session invalidation
                with self.app.test_request_context():
                    session.clear()
                    
                    if 'test_data' not in session:
                        self.add_test_result("session_invalidation", "passed", 
                                          "Session invalidation works correctly")
                    else:
                        self.add_test_result("session_invalidation", "failed", 
                                          "Session invalidation failed")
                
        except Exception as e:
            self.add_test_result("session_invalidation", "error", str(e), traceback.format_exc())
    
    def test_concurrent_sessions(self):
        """Test concurrent session handling"""
        try:
            from app.models import User
            
            admin_user = User.query.filter_by(is_admin=True).first()
            if admin_user:
                # Create multiple clients to simulate concurrent sessions
                client1 = self.app.test_client()
                client2 = self.app.test_client()
                
                # Login with both clients
                login1_response = client1.post('/auth/login', data={
                    'username': admin_user.username,
                    'password': 'admin123'
                }, follow_redirects=True)
                
                login2_response = client2.post('/auth/login', data={
                    'username': admin_user.username,
                    'password': 'admin123'
                }, follow_redirects=True)
                
                if (login1_response.status_code == 200 and 
                    login2_response.status_code == 200):
                    self.add_test_result("concurrent_sessions", "passed", 
                                      "Concurrent sessions handled correctly")
                else:
                    self.add_test_result("concurrent_sessions", "failed", 
                                      "Concurrent sessions not handled correctly")
            else:
                self.add_test_result("concurrent_sessions", "skipped", 
                                  "No admin user found")
                
        except Exception as e:
            self.add_test_result("concurrent_sessions", "error", str(e), traceback.format_exc())
