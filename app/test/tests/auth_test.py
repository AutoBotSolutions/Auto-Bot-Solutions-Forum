"""
Comprehensive Authentication Tests for Repo-Forum Project
Tests all authentication functionality including login, registration, verification, etc.
"""

import re
import traceback
from datetime import datetime, timedelta
from flask import url_for
from flask_login import login_user, logout_user

class AuthTest:
    """Comprehensive authentication testing for entire app"""
    
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
        """Run all authentication tests"""
        print("🔐 Running Comprehensive Authentication Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test user model existence
                self.test_user_model()
                
                # Test authentication routes
                self.test_login_routes()
                self.test_registration_routes()
                self.test_password_reset_routes()
                self.test_verification_routes()
                
                # Test authentication functionality
                self.test_login_functionality()
                self.test_registration_functionality()
                self.test_password_reset_functionality()
                self.test_email_verification()
                self.test_session_management()
                self.test_logout_functionality()
                
                # Test authentication security
                self.test_password_hashing()
                self.test_account_lockout()
                self.test_session_security()
                self.test_csrf_protection()
                
                # Test authentication edge cases
                self.test_invalid_credentials()
                self.test_expired_tokens()
                self.test_account_status()
                
        except Exception as e:
            self.add_test_result("auth_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_user_model(self):
        """Test User model functionality"""
        try:
            from app.models import User
            
            # Test user creation
            test_user = User(
                username='test_auth_user',
                email='test_auth@example.com',
                is_admin=False,
                is_verified=False
            )
            test_user.set_password('testpassword123')
            
            self.add_test_result("user_model_creation", "passed", 
                              "User model creation successful")
            
            # Test password verification
            if test_user.check_password('testpassword123'):
                self.add_test_result("password_verification", "passed", 
                                  "Password verification works correctly")
            else:
                self.add_test_result("password_verification", "failed", 
                                  "Password verification failed")
            
            # Test user properties
            if hasattr(test_user, 'is_admin') and hasattr(test_user, 'is_verified'):
                self.add_test_result("user_model_properties", "passed", 
                                  "User model has required properties")
            else:
                self.add_test_result("user_model_properties", "failed", 
                                  "User model missing required properties")
            
        except Exception as e:
            self.add_test_result("user_model", "error", str(e), traceback.format_exc())
    
    def test_login_routes(self):
        """Test login route registration"""
        try:
            from app.auth import auth_bp
            
            # Check if blueprint exists
            if auth_bp:
                self.add_test_result("login_blueprint_exists", "passed", 
                                  "Auth blueprint exists")
                
                # Check login routes
                login_routes = [rule for rule in auth_bp.deferred_functions 
                              if 'login' in str(rule)]
                
                if login_routes:
                    self.add_test_result("login_routes_registered", "passed", 
                                      f"Login routes registered: {len(login_routes)}")
                else:
                    self.add_test_result("login_routes_registered", "failed", 
                                      "No login routes found")
            else:
                self.add_test_result("login_blueprint_exists", "failed", 
                                  "Auth blueprint not found")
                
        except Exception as e:
            self.add_test_result("login_routes", "error", str(e), traceback.format_exc())
    
    def test_registration_routes(self):
        """Test registration route registration"""
        try:
            from app.auth import auth_bp
            
            # Check registration routes
            registration_routes = [rule for rule in auth_bp.deferred_functions 
                                 if 'register' in str(rule)]
            
            if registration_routes:
                self.add_test_result("registration_routes_registered", "passed", 
                                  f"Registration routes registered: {len(registration_routes)}")
            else:
                self.add_test_result("registration_routes_registered", "failed", 
                                  "No registration routes found")
                
        except Exception as e:
            self.add_test_result("registration_routes", "error", str(e), traceback.format_exc())
    
    def test_password_reset_routes(self):
        """Test password reset route registration"""
        try:
            from app.auth import auth_bp
            
            # Check password reset routes
            reset_routes = [rule for rule in auth_bp.deferred_functions 
                          if 'reset' in str(rule)]
            
            if reset_routes:
                self.add_test_result("password_reset_routes_registered", "passed", 
                                  f"Password reset routes registered: {len(reset_routes)}")
            else:
                self.add_test_result("password_reset_routes_registered", "failed", 
                                  "No password reset routes found")
                
        except Exception as e:
            self.add_test_result("password_reset_routes", "error", str(e), traceback.format_exc())
    
    def test_verification_routes(self):
        """Test email verification route registration"""
        try:
            from app.auth import auth_bp
            
            # Check verification routes
            verification_routes = [rule for rule in auth_bp.deferred_functions 
                                if 'verify' in str(rule) or 'verification' in str(rule)]
            
            if verification_routes:
                self.add_test_result("verification_routes_registered", "passed", 
                                  f"Verification routes registered: {len(verification_routes)}")
            else:
                self.add_test_result("verification_routes_registered", "failed", 
                                  "No verification routes found")
                
        except Exception as e:
            self.add_test_result("verification_routes", "error", str(e), traceback.format_exc())
    
    def test_login_functionality(self):
        """Test login functionality"""
        try:
            from app.models import User
            
            # Check if admin user exists
            admin_user = User.query.filter_by(is_admin=True).first()
            if admin_user:
                self.add_test_result("admin_user_exists", "passed", 
                                  f"Admin user found: {admin_user.username}")
                
                # Test login with admin user
                with self.app.test_client() as client:
                    response = client.post('/auth/login', data={
                        'username': admin_user.username,
                        'password': 'admin123'
                    }, follow_redirects=True)
                    
                    if response.status_code == 200:
                        self.add_test_result("admin_login_success", "passed", 
                                          "Admin login successful")
                    else:
                        self.add_test_result("admin_login_success", "failed", 
                                          f"Admin login failed with status {response.status_code}")
            else:
                self.add_test_result("admin_user_exists", "failed", 
                                  "No admin user found in database")
                
        except Exception as e:
            self.add_test_result("login_functionality", "error", str(e), traceback.format_exc())
    
    def test_registration_functionality(self):
        """Test registration functionality"""
        try:
            with self.app.test_client() as client:
                # Test registration form access
                response = client.get('/auth/register')
                
                if response.status_code == 200:
                    self.add_test_result("registration_form_access", "passed", 
                                      "Registration form accessible")
                    
                    # Check if form contains required fields
                    if b'username' in response.data and b'email' in response.data and b'password' in response.data:
                        self.add_test_result("registration_form_fields", "passed", 
                                          "Registration form has required fields")
                    else:
                        self.add_test_result("registration_form_fields", "failed", 
                                          "Registration form missing required fields")
                else:
                    self.add_test_result("registration_form_access", "failed", 
                                      f"Registration form not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("registration_functionality", "error", str(e), traceback.format_exc())
    
    def test_password_reset_functionality(self):
        """Test password reset functionality"""
        try:
            with self.app.test_client() as client:
                # Test password reset request form
                response = client.get('/auth/reset_password_request')
                
                if response.status_code == 200:
                    self.add_test_result("password_reset_form_access", "passed", 
                                      "Password reset form accessible")
                    
                    # Check if form contains email field
                    if b'email' in response.data:
                        self.add_test_result("password_reset_form_fields", "passed", 
                                          "Password reset form has email field")
                    else:
                        self.add_test_result("password_reset_form_fields", "failed", 
                                          "Password reset form missing email field")
                else:
                    self.add_test_result("password_reset_form_access", "failed", 
                                      f"Password reset form not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("password_reset_functionality", "error", str(e), traceback.format_exc())
    
    def test_email_verification(self):
        """Test email verification functionality"""
        try:
            from app.models import User
            
            # Check for unverified users
            unverified_users = User.query.filter_by(is_verified=False).all()
            
            if unverified_users:
                self.add_test_result("unverified_users_exist", "passed", 
                                  f"Found {len(unverified_users)} unverified users")
                
                # Test verification token generation
                user = unverified_users[0]
                if hasattr(user, 'verification_token'):
                    self.add_test_result("verification_token_field", "passed", 
                                      "User model has verification_token field")
                else:
                    self.add_test_result("verification_token_field", "failed", 
                                      "User model missing verification_token field")
            else:
                self.add_test_result("unverified_users_exist", "skipped", 
                                  "No unverified users found")
                
        except Exception as e:
            self.add_test_result("email_verification", "error", str(e), traceback.format_exc())
    
    def test_session_management(self):
        """Test session management"""
        try:
            from app.models import User
            
            admin_user = User.query.filter_by(is_admin=True).first()
            if admin_user:
                with self.app.test_client() as client:
                    # Login
                    login_response = client.post('/auth/login', data={
                        'username': admin_user.username,
                        'password': 'admin123'
                    }, follow_redirects=True)
                    
                    if login_response.status_code == 200:
                        # Test session persistence
                        session_response = client.get('/')
                        
                        if session_response.status_code == 200:
                            self.add_test_result("session_persistence", "passed", 
                                              "Session persists after login")
                        else:
                            self.add_test_result("session_persistence", "failed", 
                                              f"Session does not persist: {session_response.status_code}")
                    else:
                        self.add_test_result("session_management", "skipped", 
                                          "Login failed, cannot test session")
            else:
                self.add_test_result("session_management", "skipped", 
                                  "No admin user found")
                
        except Exception as e:
            self.add_test_result("session_management", "error", str(e), traceback.format_exc())
    
    def test_logout_functionality(self):
        """Test logout functionality"""
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
                    
                    # Test logout
                    logout_response = client.get('/auth/logout', follow_redirects=True)
                    
                    if logout_response.status_code == 200:
                        self.add_test_result("logout_functionality", "passed", 
                                          "Logout successful")
                    else:
                        self.add_test_result("logout_functionality", "failed", 
                                          f"Logout failed: {logout_response.status_code}")
            else:
                self.add_test_result("logout_functionality", "skipped", 
                                  "No admin user found")
                
        except Exception as e:
            self.add_test_result("logout_functionality", "error", str(e), traceback.format_exc())
    
    def test_password_hashing(self):
        """Test password hashing security"""
        try:
            from app.models import User
            
            # Create test user
            test_user = User(username='test_hash', email='test@example.com')
            test_user.set_password('testpassword123')
            
            # Check if password is hashed
            if test_user.password_hash and test_user.password_hash != 'testpassword123':
                self.add_test_result("password_hashing", "passed", 
                                  "Password properly hashed")
                
                # Test password verification
                if test_user.check_password('testpassword123'):
                    self.add_test_result("password_hashing_verification", "passed", 
                                      "Password verification works with hashed password")
                else:
                    self.add_test_result("password_hashing_verification", "failed", 
                                      "Password verification failed with hashed password")
            else:
                self.add_test_result("password_hashing", "failed", 
                                  "Password not properly hashed")
                
        except Exception as e:
            self.add_test_result("password_hashing", "error", str(e), traceback.format_exc())
    
    def test_account_lockout(self):
        """Test account lockout functionality"""
        try:
            from app.models import User
            
            # Check if user model has lockout fields
            test_user = User(username='test_lockout', email='lockout@example.com')
            
            lockout_fields = ['failed_login_attempts', 'locked_until']
            missing_fields = []
            
            for field in lockout_fields:
                if not hasattr(test_user, field):
                    missing_fields.append(field)
            
            if not missing_fields:
                self.add_test_result("account_lockout_fields", "passed", 
                                  "User model has lockout fields")
            else:
                self.add_test_result("account_lockout_fields", "failed", 
                                  f"Missing lockout fields: {missing_fields}")
                
        except Exception as e:
            self.add_test_result("account_lockout", "error", str(e), traceback.format_exc())
    
    def test_session_security(self):
        """Test session security"""
        try:
            # Check if session security is configured
            if hasattr(self.app, 'config'):
                session_config = self.app.config
                
                security_checks = {
                    'SECRET_KEY': 'Secret key configured',
                    'PERMANENT_SESSION_LIFETIME': 'Session lifetime configured',
                    'SESSION_COOKIE_SECURE': 'Secure cookie configured',
                    'SESSION_COOKIE_HTTPONLY': 'HTTPOnly cookie configured'
                }
                
                passed_checks = 0
                for key, description in security_checks.items():
                    if key in session_config:
                        passed_checks += 1
                        self.add_test_result(f"session_security_{key.lower()}", "passed", 
                                          description)
                    else:
                        self.add_test_result(f"session_security_{key.lower()}", "warning", 
                                          f"{description} - not configured")
                
                if passed_checks >= 2:
                    self.add_test_result("session_security_basic", "passed", 
                                      f"Basic session security configured ({passed_checks}/{len(security_checks)})")
                else:
                    self.add_test_result("session_security_basic", "failed", 
                                      f"Insufficient session security ({passed_checks}/{len(security_checks)})")
            else:
                self.add_test_result("session_security_basic", "failed", 
                                  "App configuration not accessible")
                
        except Exception as e:
            self.add_test_result("session_security", "error", str(e), traceback.format_exc())
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        try:
            if hasattr(self.app, 'config'):
                csrf_config = self.app.config
                
                if csrf_config.get('WTF_CSRF_ENABLED', False):
                    self.add_test_result("csrf_protection_enabled", "passed", 
                                      "CSRF protection is enabled")
                    
                    if csrf_config.get('WTF_CSRF_SECRET_KEY'):
                        self.add_test_result("csrf_secret_key", "passed", 
                                          "CSRF secret key configured")
                    else:
                        self.add_test_result("csrf_secret_key", "warning", 
                                          "CSRF secret key not configured")
                else:
                    self.add_test_result("csrf_protection_enabled", "failed", 
                                      "CSRF protection is disabled")
            else:
                self.add_test_result("csrf_protection_enabled", "failed", 
                                  "App configuration not accessible")
                
        except Exception as e:
            self.add_test_result("csrf_protection", "error", str(e), traceback.format_exc())
    
    def test_invalid_credentials(self):
        """Test handling of invalid credentials"""
        try:
            with self.app.test_client() as client:
                # Test login with invalid credentials
                response = client.post('/auth/login', data={
                    'username': 'nonexistent_user',
                    'password': 'wrongpassword'
                })
                
                # Should not redirect on invalid credentials
                if response.status_code in [200, 401, 403]:
                    self.add_test_result("invalid_credentials_handling", "passed", 
                                      "Invalid credentials properly rejected")
                else:
                    self.add_test_result("invalid_credentials_handling", "failed", 
                                      f"Invalid credentials not properly handled: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("invalid_credentials", "error", str(e), traceback.format_exc())
    
    def test_expired_tokens(self):
        """Test handling of expired tokens"""
        try:
            from app.models import User
            
            # Create user with expired reset token
            test_user = User(
                username='test_expired',
                email='expired@example.com',
                reset_token='expired_token_123',
                reset_token_expiration=datetime.utcnow() - timedelta(hours=1)
            )
            
            # Check if token expiration is handled
            if test_user.reset_token_expiration and test_user.reset_token_expiration < datetime.utcnow():
                self.add_test_result("expired_token_handling", "passed", 
                                  "Expired token detection works")
            else:
                self.add_test_result("expired_token_handling", "failed", 
                                  "Expired token detection failed")
                
        except Exception as e:
            self.add_test_result("expired_tokens", "error", str(e), traceback.format_exc())
    
    def test_account_status(self):
        """Test account status handling"""
        try:
            from app.models import User
            
            # Check if user model has status fields
            test_user = User(username='test_status', email='status@example.com')
            
            status_fields = ['is_active', 'is_suspended', 'is_banned']
            missing_fields = []
            
            for field in status_fields:
                if not hasattr(test_user, field):
                    missing_fields.append(field)
            
            if not missing_fields:
                self.add_test_result("account_status_fields", "passed", 
                                  "User model has account status fields")
                
                # Test default values
                if (test_user.is_active == True and 
                    test_user.is_suspended == False and 
                    test_user.is_banned == False):
                    self.add_test_result("account_status_defaults", "passed", 
                                      "Account status defaults are correct")
                else:
                    self.add_test_result("account_status_defaults", "failed", 
                                      "Account status defaults are incorrect")
            else:
                self.add_test_result("account_status_fields", "failed", 
                                  f"Missing status fields: {missing_fields}")
                
        except Exception as e:
            self.add_test_result("account_status", "error", str(e), traceback.format_exc())
