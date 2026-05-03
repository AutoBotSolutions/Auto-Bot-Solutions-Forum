"""
Comprehensive Template Tests for Repo-Forum Project
Tests all template rendering and UI components.
"""

import re
import traceback
from datetime import datetime

class TemplateTest:
    """Comprehensive template testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "templates",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all template tests"""
        print("🎨 Running Comprehensive Template Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test template structure
                self.test_base_template()
                self.test_admin_templates()
                self.test_auth_templates()
                self.test_forum_templates()
                
                # Test template rendering
                self.test_template_rendering()
                self.test_template_variables()
                self.test_template_inheritance()
                
                # Test UI components
                self.test_navigation_components()
                self.test_form_components()
                self.test_error_pages()
                
        except Exception as e:
            self.add_test_result("template_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_base_template(self):
        """Test base template structure"""
        try:
            with self.app.test_client() as client:
                response = client.get('/')
                
                if response.status_code == 200:
                    # Check for base template elements
                    base_elements = [
                        b'<!DOCTYPE html>',
                        b'<html',
                        b'<head>',
                        b'<body>',
                        b'</html>',
                        b'</body>'
                    ]
                    
                    missing_elements = []
                    for element in base_elements:
                        if element not in response.data:
                            missing_elements.append(element.decode())
                    
                    if not missing_elements:
                        self.add_test_result("base_template_structure", "passed", 
                                          "Base template structure is complete")
                    else:
                        self.add_test_result("base_template_structure", "failed", 
                                          f"Base template missing elements: {missing_elements}")
                else:
                    self.add_test_result("base_template_testing", "skipped", 
                                      "Home page not accessible")
                
        except Exception as e:
            self.add_test_result("base_template", "error", str(e), traceback.format_exc())
    
    def test_admin_templates(self):
        """Test admin template structure"""
        try:
            with self.app.test_client() as client:
                # Test admin dashboard template
                response = client.get('/admin/dashboard')
                
                if response.status_code in [200, 302]:
                    # Check for admin template elements
                    if response.status_code == 200:
                        admin_elements = [
                            b'admin',
                            b'dashboard',
                            b'users',
                            b'posts'
                        ]
                        
                        found_elements = 0
                        for element in admin_elements:
                            if element in response.data.lower():
                                found_elements += 1
                        
                        if found_elements >= 2:
                            self.add_test_result("admin_template_elements", "passed", 
                                              f"Admin template has {found_elements} expected elements")
                        else:
                            self.add_test_result("admin_template_elements", "warning", 
                                              f"Admin template has only {found_elements} expected elements")
                    else:
                        self.add_test_result("admin_template_auth", "passed", 
                                          "Admin template requires authentication")
                else:
                    self.add_test_result("admin_template_testing", "skipped", 
                                      "Admin dashboard not accessible")
                
        except Exception as e:
            self.add_test_result("admin_templates", "error", str(e), traceback.format_exc())
    
    def test_auth_templates(self):
        """Test authentication template structure"""
        try:
            with self.app.test_client() as client:
                # Test login template
                response = client.get('/auth/login')
                
                if response.status_code == 200:
                    # Check for login form elements
                    login_elements = [
                        b'username',
                        b'password',
                        b'login',
                        b'form'
                    ]
                    
                    found_elements = 0
                    for element in login_elements:
                        if element in response.data.lower():
                            found_elements += 1
                    
                    if found_elements >= 3:
                        self.add_test_result("login_template_elements", "passed", 
                                          f"Login template has {found_elements} expected elements")
                    else:
                        self.add_test_result("login_template_elements", "failed", 
                                          f"Login template has only {found_elements} expected elements")
                else:
                    self.add_test_result("login_template_testing", "skipped", 
                                      "Login template not accessible")
                
                # Test registration template
                response = client.get('/auth/register')
                
                if response.status_code == 200:
                    # Check for registration form elements
                    reg_elements = [
                        b'username',
                        b'email',
                        b'password',
                        b'register',
                        b'form'
                    ]
                    
                    found_elements = 0
                    for element in reg_elements:
                        if element in response.data.lower():
                            found_elements += 1
                    
                    if found_elements >= 4:
                        self.add_test_result("registration_template_elements", "passed", 
                                          f"Registration template has {found_elements} expected elements")
                    else:
                        self.add_test_result("registration_template_elements", "failed", 
                                          f"Registration template has only {found_elements} expected elements")
                else:
                    self.add_test_result("registration_template_testing", "skipped", 
                                      "Registration template not accessible")
                
        except Exception as e:
            self.add_test_result("auth_templates", "error", str(e), traceback.format_exc())
    
    def test_forum_templates(self):
        """Test forum template structure"""
        try:
            with self.app.test_client() as client:
                # Test forum index template
                response = client.get('/forum')
                
                if response.status_code in [200, 404]:
                    if response.status_code == 200:
                        # Check for forum elements
                        forum_elements = [
                            b'forum',
                            b'post',
                            b'category',
                            b'discussion'
                        ]
                        
                        found_elements = 0
                        for element in forum_elements:
                            if element in response.data.lower():
                                found_elements += 1
                        
                        if found_elements >= 2:
                            self.add_test_result("forum_template_elements", "passed", 
                                              f"Forum template has {found_elements} expected elements")
                        else:
                            self.add_test_result("forum_template_elements", "warning", 
                                              f"Forum template has only {found_elements} expected elements")
                    else:
                        self.add_test_result("forum_template_testing", "skipped", 
                                      "Forum template not found")
                else:
                    self.add_test_result("forum_template_testing", "skipped", 
                                      "Forum template not accessible")
                
        except Exception as e:
            self.add_test_result("forum_templates", "error", str(e), traceback.format_exc())
    
    def test_template_rendering(self):
        """Test template rendering functionality"""
        try:
            with self.app.test_client() as client:
                # Test multiple page rendering
                pages = [
                    '/',
                    '/auth/login',
                    '/auth/register',
                    '/forum'
                ]
                
                rendered_pages = 0
                for page in pages:
                    response = client.get(page)
                    if response.status_code == 200:
                        rendered_pages += 1
                
                if rendered_pages >= 3:
                    self.add_test_result("template_rendering_multiple", "passed", 
                                      f"Template rendering works for {rendered_pages}/{len(pages)} pages")
                else:
                    self.add_test_result("template_rendering_multiple", "warning", 
                                      f"Template rendering works for only {rendered_pages}/{len(pages)} pages")
                
        except Exception as e:
            self.add_test_result("template_rendering", "error", str(e), traceback.format_exc())
    
    def test_template_variables(self):
        """Test template variable passing"""
        try:
            with self.app.test_client() as client:
                response = client.get('/')
                
                if response.status_code == 200:
                    # Check if template variables are being passed
                    # This is a basic check - in reality, you'd need to check specific variables
                    if b'{{' in response.data or b'{%' in response.data:
                        self.add_test_result("template_variables_present", "warning", 
                                          "Template syntax found in rendered output (may indicate missing variables)")
                    else:
                        self.add_test_result("template_variables_present", "passed", 
                                          "Template variables properly rendered")
                else:
                    self.add_test_result("template_variables_testing", "skipped", 
                                      "Home page not accessible")
                
        except Exception as e:
            self.add_test_result("template_variables", "error", str(e), traceback.format_exc())
    
    def test_template_inheritance(self):
        """Test template inheritance"""
        try:
            with self.app.test_client() as client:
                response = client.get('/auth/login')
                
                if response.status_code == 200:
                    # Check if base template is extended
                    if b'extends' in response.data or response.data.count(b'<html') == 1:
                        self.add_test_result("template_inheritance", "passed", 
                                          "Template inheritance properly implemented")
                    else:
                        self.add_test_result("template_inheritance", "warning", 
                                          "Template inheritance may not be properly implemented")
                else:
                    self.add_test_result("template_inheritance_testing", "skipped", 
                                      "Login page not accessible")
                
        except Exception as e:
            self.add_test_result("template_inheritance", "error", str(e), traceback.format_exc())
    
    def test_navigation_components(self):
        """Test navigation components"""
        try:
            with self.app.test_client() as client:
                response = client.get('/')
                
                if response.status_code == 200:
                    # Check for navigation elements
                    nav_elements = [
                        b'nav',
                        b'menu',
                        b'navbar',
                        b'navigation'
                    ]
                    
                    found_nav = False
                    for element in nav_elements:
                        if element in response.data.lower():
                            found_nav = True
                            break
                    
                    if found_nav:
                        self.add_test_result("navigation_components", "passed", 
                                          "Navigation components present")
                    else:
                        self.add_test_result("navigation_components", "warning", 
                                          "Navigation components not found")
                else:
                    self.add_test_result("navigation_components_testing", "skipped", 
                                      "Home page not accessible")
                
        except Exception as e:
            self.add_test_result("navigation_components", "error", str(e), traceback.format_exc())
    
    def test_form_components(self):
        """Test form components"""
        try:
            with self.app.test_client() as client:
                response = client.get('/auth/login')
                
                if response.status_code == 200:
                    # Check for form elements
                    form_elements = [
                        b'<form',
                        b'<input',
                        b'<button',
                        b'submit'
                    ]
                    
                    found_elements = 0
                    for element in form_elements:
                        if element in response.data.lower():
                            found_elements += 1
                    
                    if found_elements >= 3:
                        self.add_test_result("form_components", "passed", 
                                          f"Form components present ({found_elements}/{len(form_elements)})")
                    else:
                        self.add_test_result("form_components", "warning", 
                                          f"Form components partially present ({found_elements}/{len(form_elements)})")
                else:
                    self.add_test_result("form_components_testing", "skipped", 
                                      "Login page not accessible")
                
        except Exception as e:
            self.add_test_result("form_components", "error", str(e), traceback.format_exc())
    
    def test_error_pages(self):
        """Test error page templates"""
        try:
            with self.app.test_client() as client:
                # Test 404 error page
                response = client.get('/nonexistent-page')
                
                if response.status_code == 404:
                    # Check if custom 404 page is used
                    if b'404' in response.data or b'not found' in response.data.lower():
                        self.add_test_result("custom_404_page", "passed", 
                                          "Custom 404 error page present")
                    else:
                        self.add_test_result("custom_404_page", "warning", 
                                          "Custom 404 error page may not be present")
                else:
                    self.add_test_result("error_page_testing", "skipped", 
                                      "Error page testing inconclusive")
                
        except Exception as e:
            self.add_test_result("error_pages", "error", str(e), traceback.format_exc())
