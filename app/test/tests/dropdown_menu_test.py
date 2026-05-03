"""
Dropdown Menu Testing Module
Tests dropdown menu functionality, links, and navigation
"""

import json
import re
import traceback
from datetime import datetime
from flask import Flask
from app import create_app, db
from app.models import User
from flask_login import login_user

class DropdownMenuTest:
    """Comprehensive dropdown menu testing"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
        self.page_content = None
    
    def run_all_tests(self):
        """Run all dropdown menu tests"""
        print("🎯 Running Dropdown Menu Tests...")
        
        # Initialize app
        try:
            self.app = create_app()
        except Exception as e:
            self.add_test_result("app_initialization", "error", str(e), traceback.format_exc())
            return self.test_results
        
        # Run individual tests
        self.test_page_content_extraction()
        self.test_dropdown_menu_links()
        self.test_dropdown_javascript_functionality()
        self.test_menu_item_navigation()
        self.test_menu_item_accessibility()
        self.test_dropdown_visual_elements()
        
        return self.test_results
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result"""
        result = {
            "test_name": test_name,
            "category": "dropdown_menu",
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
    
    def test_page_content_extraction(self):
        """Test extraction of admin users page content"""
        try:
            from app.admin.routes import users
            
            with self.app.app_context():
                admin_user = User.query.filter_by(username='admin').first()
                if not admin_user:
                    self.add_test_result("page_content_extraction", "failed", "Admin user not found")
                    return
                
                # Extract page content
                with self.app.test_request_context('/admin/users/', method='GET'):
                    login_user(admin_user)
                    result = users()
                    
                    if isinstance(result, str):
                        self.page_content = result
                        self.add_test_result("page_content_extraction", "passed", 
                                          f"Page content extracted ({len(result)} characters)")
                        
                        # Save content for analysis
                        content_file = self.framework.output_dir / "fixtures" / "admin_users_page.html"
                        content_file.parent.mkdir(exist_ok=True)
                        with open(content_file, 'w') as f:
                            f.write(result)
                        
                        self.add_test_result("page_content_saved", "passed", 
                                          f"Page content saved to {content_file}")
                    else:
                        self.add_test_result("page_content_extraction", "failed", 
                                          f"Unexpected result type: {type(result)}")
        
        except Exception as e:
            self.add_test_result("page_content_extraction", "error", str(e), traceback.format_exc())
    
    def test_dropdown_menu_links(self):
        """Test dropdown menu link extraction and validation"""
        if not self.page_content:
            self.add_test_result("dropdown_menu_links", "skipped", "No page content available")
            return
        
        try:
            # Extract only user action dropdown links (exclude navigation dropdowns)
            # Look for dropdown items within user action contexts
            user_action_dropdowns = re.findall(r'<div class="dropdown-menu"[^>]*role="menu"[^>]*aria-label="User management actions">(.*?)</div>', self.page_content, re.DOTALL)
            
            # If no specific dropdowns found, try a broader pattern
            if not user_action_dropdowns:
                # Look for dropdown menus that contain user action links
                user_action_dropdowns = re.findall(r'<div class="dropdown-menu"[^>]*>.*?href="/admin/users/\d+.*?</div>', self.page_content, re.DOTALL)
            
            user_action_links = []
            for dropdown_content in user_action_dropdowns:
                # Remove extra whitespace and normalize the content
                normalized_content = re.sub(r'\s+', ' ', dropdown_content.strip())
                links = re.findall(r'href=\"([^\"]+)\" class=\"dropdown-item\"', normalized_content)
                user_action_links.extend(links)
            
            # If still no links found, extract all user action links from the entire page
            if not user_action_links:
                # Extract all user action links from the page with normalized content
                normalized_page = re.sub(r'\s+', ' ', self.page_content)
                user_action_links = re.findall(r'href=\"(/admin/users/\d+/[^\"]+)\" class=\"dropdown-item\"', normalized_page)
            
            if user_action_links:
                self.add_test_result("dropdown_links_found", "passed", 
                                  f"Found {len(user_action_links)} user action dropdown links",
                                  {"links": user_action_links})
                
                # Validate link patterns
                valid_patterns = [
                    r'/admin/users/\d+/view',
                    r'/admin/users/\d+/edit',
                    r'/admin/users/\d+/reset-password',
                    r'/admin/users/\d+/suspend',
                    r'/admin/users/\d+/unsuspend',
                    r'/admin/users/\d+/ban',
                    r'/admin/users/\d+/unban',
                    r'/admin/users/\d+/toggle-admin',
                    r'/admin/users/\d+/delete'
                ]
                
                valid_links = []
                invalid_links = []
                
                for link in user_action_links:
                    is_valid = any(re.match(pattern, link) for pattern in valid_patterns)
                    if is_valid:
                        valid_links.append(link)
                    else:
                        invalid_links.append(link)
                
                if invalid_links:
                    self.add_test_result("dropdown_links_validation", "failed", 
                                      f"Found {len(invalid_links)} invalid user action links",
                                      {"invalid_links": invalid_links})
                else:
                    self.add_test_result("dropdown_links_validation", "passed", 
                                      f"All {len(valid_links)} user action links have valid patterns")
                
                # Check for expected menu items
                expected_items = ['View Details', 'Edit Profile', 'Reset Password', 'Suspend', 'Ban', 'Toggle Admin', 'Delete']
                found_items = []
                
                for item in expected_items:
                    if item in self.page_content:
                        found_items.append(item)
                
                if len(found_items) == len(expected_items):
                    self.add_test_result("dropdown_menu_items", "passed", 
                                      f"All expected menu items found: {expected_items}")
                else:
                    missing_items = [item for item in expected_items if item not in found_items]
                    self.add_test_result("dropdown_menu_items", "failed", 
                                      f"Missing menu items: {missing_items}")
            else:
                self.add_test_result("dropdown_links_found", "failed", "No dropdown menu links found")
        
        except Exception as e:
            self.add_test_result("dropdown_menu_links", "error", str(e), traceback.format_exc())
    
    def test_dropdown_javascript_functionality(self):
        """Test dropdown JavaScript functionality"""
        if not self.page_content:
            self.add_test_result("dropdown_javascript", "skipped", "No page content available")
            return
        
        try:
            # Check for JavaScript elements
            js_elements = [
                ('toggleDropdown function', 'function toggleDropdown'),
                ('Event listeners', 'addEventListener'),
                ('DOM ready event', 'DOMContentLoaded'),
                ('Click outside handler', 'document.addEventListener'),
                ('Dropdown buttons', 'dropdown-btn'),
                ('Dropdown menus', 'dropdown-menu'),
                ('Three dot icons', '⋮')
            ]
            
            passed_js = 0
            for element_name, element_pattern in js_elements:
                if element_pattern in self.page_content:
                    passed_js += 1
                else:
                    self.add_test_result(f"js_element_{element_name.replace(' ', '_')}", "failed", 
                                      f"Missing JavaScript element: {element_name}")
            
            if passed_js == len(js_elements):
                self.add_test_result("dropdown_javascript", "passed", 
                                  f"All {len(js_elements)} JavaScript elements found")
            else:
                self.add_test_result("dropdown_javascript", "failed", 
                                  f"Only {passed_js}/{len(js_elements)} JavaScript elements found")
        
        except Exception as e:
            self.add_test_result("dropdown_javascript", "error", str(e), traceback.format_exc())
    
    def test_menu_item_navigation(self):
        """Test dropdown menu item navigation to actual routes"""
        try:
            from app.admin.routes import view_user, edit_user, reset_user_password, suspend_user, ban_user, toggle_admin
            
            with self.app.app_context():
                admin_user = User.query.filter_by(username='admin').first()
                test_user = User.query.filter(User.username != 'admin').first()
                
                if not test_user:
                    self.add_test_result("menu_item_navigation", "skipped", "No test user found")
                    return
                
                # Test navigation to each dropdown menu item
                navigation_tests = [
                    ('view_user', view_user, test_user.id, '/admin/users/2/view'),
                    ('edit_user', edit_user, test_user.id, '/admin/users/2/edit'),
                    ('reset_user_password', reset_user_password, test_user.id, '/admin/users/2/reset-password'),
                    ('suspend_user', suspend_user, test_user.id, '/admin/users/2/suspend'),
                    ('ban_user', ban_user, test_user.id, '/admin/users/2/ban'),
                    ('toggle_admin', toggle_admin, test_user.id, '/admin/users/2/toggle-admin')
                ]
                
                passed_navigation = 0
                for route_name, route_func, user_id, expected_path in navigation_tests:
                    try:
                        with self.app.test_request_context(expected_path, method='GET'):
                            login_user(admin_user)
                            result = route_func(user_id)
                            
                            if hasattr(result, 'status_code'):
                                if result.status_code in [200, 302]:
                                    passed_navigation += 1
                                else:
                                    self.add_test_result(f"navigation_{route_name}", "failed", 
                                                      f"Route returns {result.status_code}")
                            elif isinstance(result, str):
                                passed_navigation += 1
                            else:
                                self.add_test_result(f"navigation_{route_name}", "failed", 
                                                  f"Route returns unexpected type: {type(result)}")
                    
                    except Exception as e:
                        self.add_test_result(f"navigation_{route_name}", "error", str(e))
                
                if passed_navigation == len(navigation_tests):
                    self.add_test_result("menu_item_navigation", "passed", 
                                      f"All {len(navigation_tests)} dropdown menu items navigate correctly")
                else:
                    self.add_test_result("menu_item_navigation", "failed", 
                                      f"Only {passed_navigation}/{len(navigation_tests)} menu items navigate correctly")
        
        except Exception as e:
            self.add_test_result("menu_item_navigation", "error", str(e), traceback.format_exc())
    
    def test_menu_item_accessibility(self):
        """Test dropdown menu accessibility features"""
        if not self.page_content:
            self.add_test_result("menu_item_accessibility", "skipped", "No page content available")
            return
        
        try:
            # Check for accessibility attributes
            accessibility_features = [
                ('ARIA labels', 'aria-label='),
                ('ARIA expanded', 'aria-expanded='),
                ('ARIA haspopup', 'aria-haspopup='),
                ('Role attributes', 'role='),
                ('Title attributes', 'title='),
                ('Button roles', 'role=\"button\"'),
                ('Menu roles', 'role=\"menu\"'),
                ('Menu item roles', 'role=\"menuitem\"')
            ]
            
            passed_a11y = 0
            for feature_name, feature_pattern in accessibility_features:
                if feature_pattern in self.page_content:
                    passed_a11y += 1
                else:
                    self.add_test_result(f"a11y_{feature_name.replace(' ', '_')}", "failed", 
                                      f"Missing accessibility feature: {feature_name}")
            
            if passed_a11y >= len(accessibility_features) * 0.7:  # 70% pass rate
                self.add_test_result("menu_item_accessibility", "passed", 
                                  f"Good accessibility: {passed_a11y}/{len(accessibility_features)} features found")
            else:
                self.add_test_result("menu_item_accessibility", "failed", 
                                  f"Poor accessibility: only {passed_a11y}/{len(accessibility_features)} features found")
        
        except Exception as e:
            self.add_test_result("menu_item_accessibility", "error", str(e), traceback.format_exc())
    
    def test_dropdown_visual_elements(self):
        """Test dropdown visual elements and styling"""
        if not self.page_content:
            self.add_test_result("dropdown_visual_elements", "skipped", "No page content available")
            return
        
        try:
            # Check for visual elements
            visual_elements = [
                ('Three dot icons', '⋮'),
                ('Dropdown buttons', 'action-btn dropdown-btn'),
                ('Dropdown menus', 'dropdown-menu'),
                ('Dropdown items', 'dropdown-item'),
                ('Action dropdowns', 'action-dropdown'),
                ('CSS styling', 'dropdown-btn'),
                ('Hover effects', ':hover'),
                ('Transitions', 'transition:')
            ]
            
            passed_visual = 0
            for element_name, element_pattern in visual_elements:
                if element_pattern in self.page_content:
                    passed_visual += 1
                else:
                    self.add_test_result(f"visual_{element_name.replace(' ', '_')}", "failed", 
                                      f"Missing visual element: {element_name}")
            
            if passed_visual >= len(visual_elements) * 0.6:  # 60% pass rate
                self.add_test_result("dropdown_visual_elements", "passed", 
                                  f"Good visual elements: {passed_visual}/{len(visual_elements)} found")
            else:
                self.add_test_result("dropdown_visual_elements", "failed", 
                                  f"Poor visual elements: only {passed_visual}/{len(visual_elements)} found")
        
        except Exception as e:
            self.add_test_result("dropdown_visual_elements", "error", str(e), traceback.format_exc())
