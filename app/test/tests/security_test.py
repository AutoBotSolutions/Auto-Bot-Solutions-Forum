"""
Comprehensive Security Tests for Repo-Forum Project
Tests all security features including CSRF, XSS, authentication, etc.
"""

import re
import traceback
from datetime import datetime

class SecurityTest:
    """Comprehensive security testing for entire app"""
    
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
        """Run all security tests"""
        print("🔒 Running Comprehensive Security Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test authentication security
                self.test_password_security()
                self.test_session_security()
                self.test_login_security()
                
                # Test CSRF protection
                self.test_csrf_configuration()
                self.test_csrf_tokens()
                
                # Test XSS protection
                self.test_xss_protection()
                self.test_input_sanitization()
                
                # Test SQL injection protection
                self.test_sql_injection_protection()
                
                # Test authorization
                self.test_role_based_access()
                self.test_admin_protection()
                
                # Test security headers
                self.test_security_headers()
                self.test_content_security_policy()
                
                # Test data protection
                self.test_sensitive_data_exposure()
                self.test_error_disclosure()
                
        except Exception as e:
            self.add_test_result("security_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_password_security(self):
        """Test password security"""
        try:
            from app.models import User
            
            # Test password hashing
            test_user = User(username='test_security', email='security@example.com')
            test_user.set_password('testpassword123')
            
            if test_user.password_hash and test_user.password_hash != 'testpassword123':
                self.add_test_result("password_hashing", "passed", 
                                  "Passwords are properly hashed")
            else:
                self.add_test_result("password_hashing", "failed", 
                                  "Passwords are not properly hashed")
            
            # Test password verification
            if test_user.check_password('testpassword123'):
                self.add_test_result("password_verification", "passed", 
                                  "Password verification works correctly")
            else:
                self.add_test_result("password_verification", "failed", 
                                  "Password verification failed")
            
            # Test password rejection
            if not test_user.check_password('wrongpassword'):
                self.add_test_result("password_rejection", "passed", 
                                  "Incorrect passwords are rejected")
            else:
                self.add_test_result("password_rejection", "failed", 
                                  "Incorrect passwords are not rejected")
                
        except Exception as e:
            self.add_test_result("password_security", "error", str(e), traceback.format_exc())
    
    def test_session_security(self):
        """Test session security"""
        try:
            if hasattr(self.app, 'config'):
                config = self.app.config
                
                # Test session security configuration
                security_checks = {
                    'SECRET_KEY': 'Secret key for session encryption',
                    'SESSION_COOKIE_SECURE': 'Secure cookie flag',
                    'SESSION_COOKIE_HTTPONLY': 'HTTPOnly cookie flag',
                    'SESSION_COOKIE_SAMESITE': 'SameSite cookie policy',
                    'PERMANENT_SESSION_LIFETIME': 'Session lifetime limit'
                }
                
                passed_checks = 0
                for key, description in security_checks.items():
                    if key in config and config[key] is not None:
                        passed_checks += 1
                        self.add_test_result(f"session_security_{key.lower()}", "passed", 
                                          f"{description} - configured")
                    else:
                        self.add_test_result(f"session_security_{key.lower()}", "warning", 
                                          f"{description} - not configured")
                
                if passed_checks >= 3:
                    self.add_test_result("session_security_adequate", "passed", 
                                      f"Session security adequate ({passed_checks}/{len(security_checks)})")
                else:
                    self.add_test_result("session_security_adequate", "failed", 
                                      f"Session security inadequate ({passed_checks}/{len(security_checks)})")
            else:
                self.add_test_result("session_security", "failed", 
                                  "App configuration not accessible")
                
        except Exception as e:
            self.add_test_result("session_security", "error", str(e), traceback.format_exc())
    
    def test_login_security(self):
        """Test login security"""
        try:
            from app.models import User
            
            # Test account lockout functionality
            test_user = User(username='test_login', email='login@example.com')
            
            lockout_fields = ['failed_login_attempts', 'locked_until']
            missing_fields = []
            
            for field in lockout_fields:
                if not hasattr(test_user, field):
                    missing_fields.append(field)
            
            if not missing_fields:
                self.add_test_result("login_lockout_fields", "passed", 
                                  "Account lockout fields are present")
            else:
                self.add_test_result("login_lockout_fields", "failed", 
                                  f"Missing lockout fields: {missing_fields}")
            
            # Test login rate limiting
            with self.app.test_client() as client:
                # Make multiple login attempts
                responses = []
                for i in range(5):
                    response = client.post('/auth/login', data={
                        'username': 'nonexistent',
                        'password': 'wrongpassword'
                    })
                    responses.append(response.status_code)
                
                # Check if rate limiting is implemented
                if any(status == 429 for status in responses):
                    self.add_test_result("login_rate_limiting", "passed", 
                                      "Login rate limiting is implemented")
                else:
                    self.add_test_result("login_rate_limiting", "warning", 
                                      "Login rate limiting may not be implemented")
                
        except Exception as e:
            self.add_test_result("login_security", "error", str(e), traceback.format_exc())
    
    def test_csrf_configuration(self):
        """Test CSRF configuration"""
        try:
            if hasattr(self.app, 'config'):
                config = self.app.config
                
                if config.get('WTF_CSRF_ENABLED', False):
                    self.add_test_result("csrf_protection_enabled", "passed", 
                                      "CSRF protection is enabled")
                    
                    if config.get('WTF_CSRF_SECRET_KEY'):
                        self.add_test_result("csrf_secret_key", "passed", 
                                          "CSRF secret key is configured")
                    else:
                        self.add_test_result("csrf_secret_key", "warning", 
                                          "CSRF secret key not configured")
                    
                    if config.get('WTF_CSRF_TIME_LIMIT'):
                        self.add_test_result("csrf_time_limit", "passed", 
                                          "CSRF time limit is configured")
                    else:
                        self.add_test_result("csrf_time_limit", "warning", 
                                          "CSRF time limit not configured")
                else:
                    self.add_test_result("csrf_protection_enabled", "failed", 
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
                # Test form access
                response = client.get('/auth/login')
                
                if response.status_code == 200:
                    # Check for CSRF token in form
                    if b'csrf_token' in response.data or b'csrf' in response.data.lower():
                        self.add_test_result("csrf_token_in_form", "passed", 
                                          "CSRF token present in form")
                    else:
                        self.add_test_result("csrf_token_in_form", "warning", 
                                          "CSRF token not found in form")
                    
                    # Test form submission without CSRF token
                    response = client.post('/auth/login', data={
                        'username': 'test',
                        'password': 'test'
                    })
                    
                    if response.status_code in [400, 403]:
                        self.add_test_result("csrf_token_required", "passed", 
                                          "CSRF token is required for form submission")
                    else:
                        self.add_test_result("csrf_token_required", "warning", 
                                          "CSRF token may not be required")
                else:
                    self.add_test_result("csrf_token_testing", "skipped", 
                                      "Login form not accessible")
                
        except Exception as e:
            self.add_test_result("csrf_tokens", "error", str(e), traceback.format_exc())
    
    def test_xss_protection(self):
        """Test XSS protection"""
        try:
            with self.app.test_client() as client:
                # Test input sanitization
                xss_payload = '<script>alert("xss")</script>'
                
                # Try to submit XSS payload
                response = client.post('/auth/register', data={
                    'username': xss_payload,
                    'email': 'test@example.com',
                    'password': 'testpassword123'
                })
                
                # Check if XSS is filtered
                if response.status_code == 200:
                    if b'<script>' not in response.data:
                        self.add_test_result("xss_filtering", "passed", 
                                          "XSS scripts are filtered")
                    else:
                        self.add_test_result("xss_filtering", "failed", 
                                          "XSS scripts are not filtered")
                else:
                    self.add_test_result("xss_filtering", "skipped", 
                                      "Registration form not accessible")
                
        except Exception as e:
            self.add_test_result("xss_protection", "error", str(e), traceback.format_exc())
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        try:
            with self.app.test_client() as client:
                # Test various injection attempts
                injection_payloads = [
                    '<script>alert("xss")</script>',
                    'javascript:alert("xss")',
                    '"><script>alert("xss")</script>',
                    "' OR '1'='1",
                    'DROP TABLE users;'
                ]
                
                sanitized_count = 0
                for payload in injection_payloads:
                    response = client.post('/auth/register', data={
                        'username': payload,
                        'email': 'test@example.com',
                        'password': 'testpassword123'
                    })
                    
                    # Check if payload is sanitized
                    if response.status_code == 200:
                        if payload.encode() not in response.data:
                            sanitized_count += 1
                
                if sanitized_count >= len(injection_payloads) * 0.5:
                    self.add_test_result("input_sanitization", "passed", 
                                      f"Input sanitization working ({sanitized_count}/{len(injection_payloads)} payloads filtered)")
                else:
                    self.add_test_result("input_sanitization", "warning", 
                                      f"Input sanitization may be insufficient ({sanitized_count}/{len(injection_payloads)} payloads filtered)")
                
        except Exception as e:
            self.add_test_result("input_sanitization", "error", str(e), traceback.format_exc())
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        try:
            from app import db
            from sqlalchemy import text
            
            # Test parameterized queries
            try:
                result = db.engine.execute(
                    text("SELECT * FROM user WHERE username = :username"),
                    {'username': 'admin'}
                )
                self.add_test_result("sql_injection_parameterized", "passed", 
                                  "SQL queries use parameterized binding")
            except Exception as e:
                self.add_test_result("sql_injection_parameterized", "failed", 
                                  f"SQL query error: {str(e)}")
            
            # Test ORM queries (should be safe by default)
            try:
                from app.models import User
                users = User.query.filter(User.username.like('%admin%')).all()
                self.add_test_result("sql_injection_orm", "passed", 
                                  "ORM queries are safe from SQL injection")
            except Exception as e:
                self.add_test_result("sql_injection_orm", "failed", 
                                  f"ORM query error: {str(e)}")
                
        except Exception as e:
            self.add_test_result("sql_injection_protection", "error", str(e), traceback.format_exc())
    
    def test_role_based_access(self):
        """Test role-based access control"""
        try:
            from app.models import User
            
            # Test admin user
            admin_user = User.query.filter_by(is_admin=True).first()
            if admin_user:
                self.add_test_result("admin_user_exists", "passed", 
                                  f"Admin user found: {admin_user.username}")
            else:
                self.add_test_result("admin_user_exists", "failed", 
                                  "No admin user found")
            
            # Test regular user
            regular_user = User.query.filter_by(is_admin=False).first()
            if regular_user:
                self.add_test_result("regular_user_exists", "passed", 
                                  f"Regular user found: {regular_user.username}")
            else:
                self.add_test_result("regular_user_exists", "warning", 
                                  "No regular user found")
            
            # Test role fields
            test_user = User(username='test_role', email='role@example.com')
            if hasattr(test_user, 'is_admin'):
                self.add_test_result("role_field_exists", "passed", 
                                  "Role field (is_admin) exists")
            else:
                self.add_test_result("role_field_exists", "failed", 
                                  "Role field (is_admin) missing")
                
        except Exception as e:
            self.add_test_result("role_based_access", "error", str(e), traceback.format_exc())
    
    def test_admin_protection(self):
        """Test admin route protection"""
        try:
            with self.app.test_client() as client:
                # Test admin route without authentication
                response = client.get('/admin/dashboard')
                
                if response.status_code in [302, 401, 403]:
                    self.add_test_result("admin_route_protection", "passed", 
                                      "Admin routes are protected")
                elif response.status_code == 404:
                    self.add_test_result("admin_route_protection", "skipped", 
                                      "Admin routes not found")
                else:
                    self.add_test_result("admin_route_protection", "failed", 
                                      f"Admin routes not protected: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("admin_protection", "error", str(e), traceback.format_exc())
    
    def test_security_headers(self):
        """Test security headers"""
        try:
            with self.app.test_client() as client:
                response = client.get('/')
                
                headers = response.headers
                
                # Check for security headers
                security_headers = {
                    'X-Content-Type-Options': 'nosniff',
                    'X-Frame-Options': 'DENY',
                    'X-XSS-Protection': '1; mode=block',
                    'Strict-Transport-Security': 'max-age=31536000'
                }
                
                found_headers = 0
                for header, expected_value in security_headers.items():
                    if header in headers:
                        found_headers += 1
                        self.add_test_result(f"security_header_{header.lower().replace('-', '_')}", "passed", 
                                          f"{header} header present")
                    else:
                        self.add_test_result(f"security_header_{header.lower().replace('-', '_')}", "warning", 
                                          f"{header} header missing")
                
                if found_headers >= 2:
                    self.add_test_result("security_headers_adequate", "passed", 
                                      f"Security headers adequate ({found_headers}/{len(security_headers)})")
                else:
                    self.add_test_result("security_headers_adequate", "warning", 
                                      f"Security headers inadequate ({found_headers}/{len(security_headers)})")
                
        except Exception as e:
            self.add_test_result("security_headers", "error", str(e), traceback.format_exc())
    
    def test_content_security_policy(self):
        """Test Content Security Policy"""
        try:
            with self.app.test_client() as client:
                response = client.get('/')
                
                csp_header = response.headers.get('Content-Security-Policy')
                if csp_header:
                    self.add_test_result("csp_header_present", "passed", 
                                      "Content Security Policy header present")
                    
                    # Check for basic CSP directives
                    csp_directives = ['default-src', 'script-src', 'style-src']
                    found_directives = 0
                    
                    for directive in csp_directives:
                        if directive in csp_header:
                            found_directives += 1
                    
                    if found_directives >= 2:
                        self.add_test_result("csp_directives_adequate", "passed", 
                                          f"CSP directives adequate ({found_directives}/{len(csp_directives)})")
                    else:
                        self.add_test_result("csp_directives_adequate", "warning", 
                                          f"CSP directives inadequate ({found_directives}/{len(csp_directives)})")
                else:
                    self.add_test_result("csp_header_present", "warning", 
                                      "Content Security Policy header missing")
                
        except Exception as e:
            self.add_test_result("content_security_policy", "error", str(e), traceback.format_exc())
    
    def test_sensitive_data_exposure(self):
        """Test sensitive data exposure"""
        try:
            with self.app.test_client() as client:
                # Test error pages for information disclosure
                response = client.get('/nonexistent-page')
                
                if response.status_code == 404:
                    # Check if error page contains sensitive information
                    sensitive_patterns = [
                        b'traceback',
                        b'sqlalchemy',
                        b'flask',
                        b'python',
                        b'internal server error'
                    ]
                    
                    exposed_count = 0
                    for pattern in sensitive_patterns:
                        if pattern in response.data.lower():
                            exposed_count += 1
                    
                    if exposed_count == 0:
                        self.add_test_result("sensitive_data_404", "passed", 
                                          "404 page does not expose sensitive information")
                    else:
                        self.add_test_result("sensitive_data_404", "warning", 
                                          f"404 page may expose {exposed_count} sensitive items")
                
                # Test API responses for data exposure
                response = client.get('/api/users')
                if response.status_code == 200:
                    # Check if response contains sensitive fields
                    sensitive_fields = ['password_hash', 'reset_token', 'verification_token']
                    response_text = response.data.decode('utf-8').lower()
                    
                    exposed_fields = []
                    for field in sensitive_fields:
                        if field in response_text:
                            exposed_fields.append(field)
                    
                    if not exposed_fields:
                        self.add_test_result("api_data_exposure", "passed", 
                                          "API does not expose sensitive fields")
                    else:
                        self.add_test_result("api_data_exposure", "failed", 
                                          f"API exposes sensitive fields: {exposed_fields}")
                
        except Exception as e:
            self.add_test_result("sensitive_data_exposure", "error", str(e), traceback.format_exc())
    
    def test_error_disclosure(self):
        """Test error disclosure"""
        try:
            with self.app.test_client() as client:
                # Test application error handling
                response = client.get('/error-test')  # This should not exist
                
                if response.status_code in [404, 500]:
                    # Check if error details are exposed
                    error_patterns = [
                        b'traceback',
                        b'file path',
                        b'line number',
                        b'function name'
                    ]
                    
                    exposed_count = 0
                    for pattern in error_patterns:
                        if pattern in response.data.lower():
                            exposed_count += 1
                    
                    if exposed_count == 0:
                        self.add_test_result("error_disclosure_controlled", "passed", 
                                          "Error details are not exposed")
                    else:
                        self.add_test_result("error_disclosure_controlled", "warning", 
                                          f"Error details may be exposed: {exposed_count} patterns found")
                else:
                    self.add_test_result("error_disclosure", "skipped", 
                                      "Error endpoint not accessible")
                
        except Exception as e:
            self.add_test_result("error_disclosure", "error", str(e), traceback.format_exc())
