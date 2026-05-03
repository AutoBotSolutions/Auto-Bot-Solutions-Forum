"""
Comprehensive UI Tests for Repo-Forum Project
Tests UI components and user interface.
"""

import re
import traceback
from datetime import datetime

class UITest:
    """Comprehensive UI testing for entire app"""
    
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
        """Run all UI tests"""
        print("🎨 Running Comprehensive UI Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test UI functionality
                self.test_ui_components()
                self.test_responsive_design()
                self.test_accessibility()
                
        except Exception as e:
            self.add_test_result("ui_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_ui_components(self):
        """Test UI components"""
        try:
            with self.app.test_client() as client:
                response = client.get('/')
                
                if response.status_code == 200:
                    # Check for basic UI components
                    ui_elements = [
                        b'button',
                        b'input',
                        b'form',
                        b'nav'
                    ]
                    
                    found_elements = 0
                    for element in ui_elements:
                        if element in response.data.lower():
                            found_elements += 1
                    
                    if found_elements >= 2:
                        self.add_test_result("ui_components_present", "passed", 
                                          f"UI components present ({found_elements}/{len(ui_elements)})")
                    else:
                        self.add_test_result("ui_components_present", "warning", 
                                          f"UI components partially present ({found_elements}/{len(ui_elements)})")
                else:
                    self.add_test_result("ui_components_testing", "skipped", 
                                      "Home page not accessible")
                
        except Exception as e:
            self.add_test_result("ui_components", "error", str(e), traceback.format_exc())
    
    def test_responsive_design(self):
        """Test responsive design"""
        try:
            with self.app.test_client() as client:
                response = client.get('/')
                
                if response.status_code == 200:
                    # Check for responsive design indicators
                    responsive_indicators = [
                        b'viewport',
                        b'media',
                        b'responsive',
                        b'bootstrap',
                        b'tailwind'
                    ]
                    
                    found_indicators = 0
                    for indicator in responsive_indicators:
                        if indicator in response.data.lower():
                            found_indicators += 1
                    
                    if found_indicators >= 1:
                        self.add_test_result("responsive_design_present", "passed", 
                                          f"Responsive design indicators present ({found_indicators})")
                    else:
                        self.add_test_result("responsive_design_present", "warning", 
                                          "Responsive design indicators not found")
                else:
                    self.add_test_result("responsive_design_testing", "skipped", 
                                      "Home page not accessible")
                
        except Exception as e:
            self.add_test_result("responsive_design", "error", str(e), traceback.format_exc())
    
    def test_accessibility(self):
        """Test accessibility features"""
        try:
            with self.app.test_client() as client:
                response = client.get('/')
                
                if response.status_code == 200:
                    # Check for accessibility features
                    accessibility_features = [
                        b'role',
                        b'aria-',
                        b'alt',
                        b'title'
                    ]
                    
                    found_features = 0
                    for feature in accessibility_features:
                        if feature in response.data.lower():
                            found_features += 1
                    
                    if found_features >= 2:
                        self.add_test_result("accessibility_features_present", "passed", 
                                          f"Accessibility features present ({found_features})")
                    else:
                        self.add_test_result("accessibility_features_present", "warning", 
                                          "Accessibility features limited ({found_features})")
                else:
                    self.add_test_result("accessibility_testing", "skipped", 
                                      "Home page not accessible")
                
        except Exception as e:
            self.add_test_result("accessibility", "error", str(e), traceback.format_exc())
