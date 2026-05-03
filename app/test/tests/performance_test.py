"""
Comprehensive Performance Tests for Repo-Forum Project
Tests performance and load testing functionality.
"""

import re
import traceback
from datetime import datetime
import time

class PerformanceTest:
    """Comprehensive performance testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "performance",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("⚡ Running Comprehensive Performance Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test performance functionality
                self.test_page_load_times()
                self.test_database_query_performance()
                self.test_api_response_times()
                
        except Exception as e:
            self.add_test_result("performance_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_page_load_times(self):
        """Test page load times"""
        try:
            with self.app.test_client() as client:
                pages = ['/', '/auth/login', '/forum']
                
                total_time = 0
                successful_pages = 0
                
                for page in pages:
                    start_time = time.time()
                    response = client.get(page)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        load_time = end_time - start_time
                        total_time += load_time
                        successful_pages += 1
                        
                        if load_time < 0.5:
                            self.add_test_result(f"page_load_time_{page.replace('/', '_')}", "passed", 
                                              f"Page {page} loads in {load_time:.3f}s")
                        else:
                            self.add_test_result(f"page_load_time_{page.replace('/', '_')}", "warning", 
                                              f"Page {page} loads slowly: {load_time:.3f}s")
                
                if successful_pages > 0:
                    avg_time = total_time / successful_pages
                    if avg_time < 0.3:
                        self.add_test_result("page_load_times_average", "passed", 
                                          f"Average page load time: {avg_time:.3f}s")
                    else:
                        self.add_test_result("page_load_times_average", "warning", 
                                          f"Average page load time slow: {avg_time:.3f}s")
                
        except Exception as e:
            self.add_test_result("page_load_times", "error", str(e), traceback.format_exc())
    
    def test_database_query_performance(self):
        """Test database query performance"""
        try:
            from app.models import User
            
            start_time = time.time()
            users = User.query.limit(10).all()
            end_time = time.time()
            
            query_time = end_time - start_time
            
            if query_time < 0.1:
                self.add_test_result("database_query_performance", "passed", 
                                  f"Database query time: {query_time:.3f}s")
            else:
                self.add_test_result("database_query_performance", "warning", 
                                  f"Database query slow: {query_time:.3f}s")
                
        except Exception as e:
            self.add_test_result("database_query_performance", "error", str(e), traceback.format_exc())
    
    def test_api_response_times(self):
        """Test API response times"""
        try:
            with self.app.test_client() as client:
                api_endpoints = ['/api/users', '/api/posts']
                
                total_time = 0
                successful_endpoints = 0
                
                for endpoint in api_endpoints:
                    start_time = time.time()
                    response = client.get(endpoint)
                    end_time = time.time()
                    
                    if response.status_code in [200, 404]:
                        response_time = end_time - start_time
                        total_time += response_time
                        successful_endpoints += 1
                        
                        if response_time < 0.2:
                            self.add_test_result(f"api_response_time_{endpoint.replace('/', '_')}", "passed", 
                                              f"API {endpoint} responds in {response_time:.3f}s")
                        else:
                            self.add_test_result(f"api_response_time_{endpoint.replace('/', '_')}", "warning", 
                                              f"API {endpoint} responds slowly: {response_time:.3f}s")
                
                if successful_endpoints > 0:
                    avg_time = total_time / successful_endpoints
                    if avg_time < 0.15:
                        self.add_test_result("api_response_times_average", "passed", 
                                          f"Average API response time: {avg_time:.3f}s")
                    else:
                        self.add_test_result("api_response_times_average", "warning", 
                                          f"Average API response time slow: {avg_time:.3f}s")
                
        except Exception as e:
            self.add_test_result("api_response_times", "error", str(e), traceback.format_exc())
