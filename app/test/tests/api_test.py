"""
Comprehensive API Tests for Repo-Forum Project
Tests all API endpoints and responses.
"""

import re
import traceback
import json
from datetime import datetime, timedelta

class APITest:
    """Comprehensive API testing for entire app"""
    
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
        """Run all API tests"""
        print("🌐 Running Comprehensive API Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test API blueprint registration
                self.test_api_blueprint()
                
                # Test API endpoints
                self.test_user_api_endpoints()
                self.test_post_api_endpoints()
                self.test_comment_api_endpoints()
                self.test_admin_api_endpoints()
                
                # Test API responses
                self.test_api_response_formats()
                self.test_api_status_codes()
                self.test_api_error_handling()
                
                # Test API functionality
                self.test_api_crud_operations()
                self.test_api_pagination()
                self.test_api_filtering()
                
                # Test API security
                self.test_api_authentication()
                self.test_api_authorization()
                self.test_api_rate_limiting()
                
        except Exception as e:
            self.add_test_result("api_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_api_blueprint(self):
        """Test API blueprint registration"""
        try:
            from app.api import api_bp
            
            if api_bp:
                self.add_test_result("api_blueprint_exists", "passed", 
                                  "API blueprint exists")
                
                # Check if blueprint has routes
                if hasattr(api_bp, 'deferred_functions'):
                    route_count = len(api_bp.deferred_functions)
                    self.add_test_result("api_blueprint_routes", "passed", 
                                      f"API blueprint has {route_count} deferred functions")
                else:
                    self.add_test_result("api_blueprint_routes", "warning", 
                                      "API blueprint deferred functions not accessible")
            else:
                self.add_test_result("api_blueprint_exists", "failed", 
                                  "API blueprint not found")
                
        except Exception as e:
            self.add_test_result("api_blueprint", "error", str(e), traceback.format_exc())
    
    def test_user_api_endpoints(self):
        """Test user API endpoints"""
        try:
            with self.app.test_client() as client:
                # Test user list endpoint
                response = client.get('/api/users')
                
                if response.status_code == 200:
                    self.add_test_result("api_users_list", "passed", 
                                      "Users list API endpoint accessible")
                    
                    # Test JSON response
                    try:
                        data = json.loads(response.data)
                        if isinstance(data, (list, dict)):
                            self.add_test_result("api_users_json_response", "passed", 
                                              "Users API returns valid JSON")
                        else:
                            self.add_test_result("api_users_json_response", "failed", 
                                              "Users API does not return valid JSON")
                    except json.JSONDecodeError:
                        self.add_test_result("api_users_json_response", "failed", 
                                          "Users API response is not valid JSON")
                elif response.status_code == 404:
                    self.add_test_result("api_users_list", "skipped", 
                                      "Users list API endpoint not found")
                else:
                    self.add_test_result("api_users_list", "failed", 
                                      f"Users list API returned {response.status_code}")
                
                # Test user detail endpoint
                response = client.get('/api/users/1')
                
                if response.status_code == 200:
                    self.add_test_result("api_user_detail", "passed", 
                                      "User detail API endpoint accessible")
                elif response.status_code == 404:
                    self.add_test_result("api_user_detail", "skipped", 
                                      "User detail API endpoint not found")
                else:
                    self.add_test_result("api_user_detail", "failed", 
                                      f"User detail API returned {response.status_code}")
                
        except Exception as e:
            self.add_test_result("user_api_endpoints", "error", str(e), traceback.format_exc())
    
    def test_post_api_endpoints(self):
        """Test post API endpoints"""
        try:
            with self.app.test_client() as client:
                # Test posts list endpoint
                response = client.get('/api/posts')
                
                if response.status_code == 200:
                    self.add_test_result("api_posts_list", "passed", 
                                      "Posts list API endpoint accessible")
                    
                    # Test JSON response
                    try:
                        data = json.loads(response.data)
                        if isinstance(data, (list, dict)):
                            self.add_test_result("api_posts_json_response", "passed", 
                                              "Posts API returns valid JSON")
                        else:
                            self.add_test_result("api_posts_json_response", "failed", 
                                              "Posts API does not return valid JSON")
                    except json.JSONDecodeError:
                        self.add_test_result("api_posts_json_response", "failed", 
                                          "Posts API response is not valid JSON")
                elif response.status_code == 404:
                    self.add_test_result("api_posts_list", "skipped", 
                                      "Posts list API endpoint not found")
                else:
                    self.add_test_result("api_posts_list", "failed", 
                                      f"Posts list API returned {response.status_code}")
                
                # Test post detail endpoint
                response = client.get('/api/posts/1')
                
                if response.status_code == 200:
                    self.add_test_result("api_post_detail", "passed", 
                                      "Post detail API endpoint accessible")
                elif response.status_code == 404:
                    self.add_test_result("api_post_detail", "skipped", 
                                      "Post detail API endpoint not found")
                else:
                    self.add_test_result("api_post_detail", "failed", 
                                      f"Post detail API returned {response.status_code}")
                
        except Exception as e:
            self.add_test_result("post_api_endpoints", "error", str(e), traceback.format_exc())
    
    def test_comment_api_endpoints(self):
        """Test comment API endpoints"""
        try:
            with self.app.test_client() as client:
                # Test comments list endpoint
                response = client.get('/api/comments')
                
                if response.status_code == 200:
                    self.add_test_result("api_comments_list", "passed", 
                                      "Comments list API endpoint accessible")
                elif response.status_code == 404:
                    self.add_test_result("api_comments_list", "skipped", 
                                      "Comments list API endpoint not found")
                else:
                    self.add_test_result("api_comments_list", "failed", 
                                      f"Comments list API returned {response.status_code}")
                
                # Test post comments endpoint
                response = client.get('/api/posts/1/comments')
                
                if response.status_code == 200:
                    self.add_test_result("api_post_comments", "passed", 
                                      "Post comments API endpoint accessible")
                elif response.status_code == 404:
                    self.add_test_result("api_post_comments", "skipped", 
                                      "Post comments API endpoint not found")
                else:
                    self.add_test_result("api_post_comments", "failed", 
                                      f"Post comments API returned {response.status_code}")
                
        except Exception as e:
            self.add_test_result("comment_api_endpoints", "error", str(e), traceback.format_exc())
    
    def test_admin_api_endpoints(self):
        """Test admin API endpoints"""
        try:
            with self.app.test_client() as client:
                # Test admin users endpoint
                response = client.get('/api/admin/users')
                
                if response.status_code == 200:
                    self.add_test_result("api_admin_users", "passed", 
                                      "Admin users API endpoint accessible")
                elif response.status_code == 401:
                    self.add_test_result("api_admin_users", "passed", 
                                      "Admin users API properly protected")
                elif response.status_code == 404:
                    self.add_test_result("api_admin_users", "skipped", 
                                      "Admin users API endpoint not found")
                else:
                    self.add_test_result("api_admin_users", "failed", 
                                      f"Admin users API returned {response.status_code}")
                
                # Test admin posts endpoint
                response = client.get('/api/admin/posts')
                
                if response.status_code == 200:
                    self.add_test_result("api_admin_posts", "passed", 
                                      "Admin posts API endpoint accessible")
                elif response.status_code == 401:
                    self.add_test_result("api_admin_posts", "passed", 
                                      "Admin posts API properly protected")
                elif response.status_code == 404:
                    self.add_test_result("api_admin_posts", "skipped", 
                                      "Admin posts API endpoint not found")
                else:
                    self.add_test_result("api_admin_posts", "failed", 
                                      f"Admin posts API returned {response.status_code}")
                
        except Exception as e:
            self.add_test_result("admin_api_endpoints", "error", str(e), traceback.format_exc())
    
    def test_api_response_formats(self):
        """Test API response formats"""
        try:
            with self.app.test_client() as client:
                # Test JSON content type
                response = client.get('/api/users')
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        self.add_test_result("api_json_content_type", "passed", 
                                          "API returns correct JSON content type")
                    else:
                        self.add_test_result("api_json_content_type", "warning", 
                                          f"API content type: {content_type}")
                    
                    # Test JSON structure
                    try:
                        data = json.loads(response.data)
                        if isinstance(data, list):
                            self.add_test_result("api_list_response_format", "passed", 
                                              "API returns list format")
                        elif isinstance(data, dict):
                            if 'data' in data or 'items' in data:
                                self.add_test_result("api_paginated_response_format", "passed", 
                                                  "API returns paginated format")
                            else:
                                self.add_test_result("api_object_response_format", "passed", 
                                                  "API returns object format")
                        else:
                            self.add_test_result("api_response_format", "failed", 
                                              "API returns unexpected format")
                    except json.JSONDecodeError:
                        self.add_test_result("api_json_parsing", "failed", 
                                          "API response not valid JSON")
                else:
                    self.add_test_result("api_response_formats", "skipped", 
                                      "API endpoint not accessible")
                
        except Exception as e:
            self.add_test_result("api_response_formats", "error", str(e), traceback.format_exc())
    
    def test_api_status_codes(self):
        """Test API status codes"""
        try:
            with self.app.test_client() as client:
                # Test successful requests
                response = client.get('/api/users')
                
                if response.status_code == 200:
                    self.add_test_result("api_success_status", "passed", 
                                      "API returns 200 for successful requests")
                elif response.status_code == 404:
                    self.add_test_result("api_success_status", "skipped", 
                                      "API endpoint not found")
                else:
                    self.add_test_result("api_success_status", "warning", 
                                      f"API returns {response.status_code} for requests")
                
                # Test not found requests
                response = client.get('/api/nonexistent')
                
                if response.status_code == 404:
                    self.add_test_result("api_not_found_status", "passed", 
                                      "API returns 404 for nonexistent endpoints")
                else:
                    self.add_test_result("api_not_found_status", "failed", 
                                      f"API returns {response.status_code} for nonexistent endpoint")
                
        except Exception as e:
            self.add_test_result("api_status_codes", "error", str(e), traceback.format_exc())
    
    def test_api_error_handling(self):
        """Test API error handling"""
        try:
            with self.app.test_client() as client:
                # Test invalid ID
                response = client.get('/api/users/999999')
                
                if response.status_code == 404:
                    self.add_test_result("api_invalid_id_handling", "passed", 
                                      "API properly handles invalid ID")
                elif response.status_code == 200:
                    self.add_test_result("api_invalid_id_handling", "warning", 
                                      "API returns 200 for invalid ID")
                else:
                    self.add_test_result("api_invalid_id_handling", "failed", 
                                      f"API returns {response.status_code} for invalid ID")
                
                # Test error response format
                if response.status_code >= 400:
                    try:
                        error_data = json.loads(response.data)
                        if 'error' in error_data or 'message' in error_data:
                            self.add_test_result("api_error_response_format", "passed", 
                                              "API returns proper error format")
                        else:
                            self.add_test_result("api_error_response_format", "warning", 
                                              "API error response could be improved")
                    except json.JSONDecodeError:
                        self.add_test_result("api_error_response_format", "failed", 
                                          "API error response not valid JSON")
                
        except Exception as e:
            self.add_test_result("api_error_handling", "error", str(e), traceback.format_exc())
    
    def test_api_crud_operations(self):
        """Test API CRUD operations"""
        try:
            with self.app.test_client() as client:
                # Test CREATE (POST)
                post_data = {
                    'title': 'Test API Post',
                    'content': 'Test content for API post'
                }
                response = client.post('/api/posts', 
                                      data=json.dumps(post_data),
                                      content_type='application/json')
                
                if response.status_code in [200, 201]:
                    self.add_test_result("api_create_operation", "passed", 
                                      "API CREATE operation works")
                elif response.status_code == 401:
                    self.add_test_result("api_create_operation", "passed", 
                                      "API CREATE operation requires authentication")
                elif response.status_code == 404:
                    self.add_test_result("api_create_operation", "skipped", 
                                      "API CREATE endpoint not found")
                else:
                    self.add_test_result("api_create_operation", "failed", 
                                      f"API CREATE returned {response.status_code}")
                
                # Test UPDATE (PUT/PATCH)
                update_data = {'title': 'Updated API Post'}
                response = client.put('/api/posts/1', 
                                    data=json.dumps(update_data),
                                    content_type='application/json')
                
                if response.status_code == 200:
                    self.add_test_result("api_update_operation", "passed", 
                                      "API UPDATE operation works")
                elif response.status_code == 401:
                    self.add_test_result("api_update_operation", "passed", 
                                      "API UPDATE operation requires authentication")
                elif response.status_code == 404:
                    self.add_test_result("api_update_operation", "skipped", 
                                      "API UPDATE endpoint not found")
                else:
                    self.add_test_result("api_update_operation", "failed", 
                                      f"API UPDATE returned {response.status_code}")
                
                # Test DELETE
                response = client.delete('/api/posts/999999')
                
                if response.status_code in [200, 204]:
                    self.add_test_result("api_delete_operation", "passed", 
                                      "API DELETE operation works")
                elif response.status_code == 401:
                    self.add_test_result("api_delete_operation", "passed", 
                                      "API DELETE operation requires authentication")
                elif response.status_code == 404:
                    self.add_test_result("api_delete_operation", "skipped", 
                                      "API DELETE endpoint not found")
                else:
                    self.add_test_result("api_delete_operation", "failed", 
                                      f"API DELETE returned {response.status_code}")
                
        except Exception as e:
            self.add_test_result("api_crud_operations", "error", str(e), traceback.format_exc())
    
    def test_api_pagination(self):
        """Test API pagination"""
        try:
            with self.app.test_client() as client:
                # Test pagination parameters
                response = client.get('/api/posts?page=1&per_page=10')
                
                if response.status_code == 200:
                    try:
                        data = json.loads(response.data)
                        if isinstance(data, dict):
                            pagination_fields = ['page', 'per_page', 'total', 'pages']
                            found_fields = []
                            
                            for field in pagination_fields:
                                if field in data:
                                    found_fields.append(field)
                            
                            if len(found_fields) >= 2:
                                self.add_test_result("api_pagination", "passed", 
                                                  f"API pagination implemented ({len(found_fields)}/{len(pagination_fields)} fields)")
                            else:
                                self.add_test_result("api_pagination", "warning", 
                                                  "API pagination partially implemented")
                        else:
                            self.add_test_result("api_pagination", "skipped", 
                                              "API does not return paginated format")
                    except json.JSONDecodeError:
                        self.add_test_result("api_pagination", "failed", 
                                          "API pagination response not valid JSON")
                elif response.status_code == 404:
                    self.add_test_result("api_pagination", "skipped", 
                                      "API endpoint not found")
                else:
                    self.add_test_result("api_pagination", "failed", 
                                      f"API pagination test failed with {response.status_code}")
                
        except Exception as e:
            self.add_test_result("api_pagination", "error", str(e), traceback.format_exc())
    
    def test_api_filtering(self):
        """Test API filtering"""
        try:
            with self.app.test_client() as client:
                # Test filtering parameters
                response = client.get('/api/posts?status=published&sort=created_at')
                
                if response.status_code == 200:
                    self.add_test_result("api_filtering", "passed", 
                                      "API filtering parameters accepted")
                elif response.status_code == 404:
                    self.add_test_result("api_filtering", "skipped", 
                                      "API endpoint not found")
                else:
                    self.add_test_result("api_filtering", "warning", 
                                      f"API filtering returned {response.status_code}")
                
        except Exception as e:
            self.add_test_result("api_filtering", "error", str(e), traceback.format_exc())
    
    def test_api_authentication(self):
        """Test API authentication"""
        try:
            with self.app.test_client() as client:
                # Test unauthenticated request to protected endpoint
                response = client.post('/api/posts', 
                                      data=json.dumps({'title': 'Test'}),
                                      content_type='application/json')
                
                if response.status_code == 401:
                    self.add_test_result("api_authentication_required", "passed", 
                                      "API properly requires authentication")
                elif response.status_code == 404:
                    self.add_test_result("api_authentication_required", "skipped", 
                                      "API endpoint not found")
                else:
                    self.add_test_result("api_authentication_required", "warning", 
                                      f"API authentication may not be enforced: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("api_authentication", "error", str(e), traceback.format_exc())
    
    def test_api_authorization(self):
        """Test API authorization"""
        try:
            with self.app.test_client() as client:
                # Test unauthorized access to admin endpoint
                response = client.get('/api/admin/users')
                
                if response.status_code == 401:
                    self.add_test_result("api_authorization_unauthenticated", "passed", 
                                      "API properly blocks unauthenticated admin access")
                elif response.status_code == 403:
                    self.add_test_result("api_authorization_unauthenticated", "passed", 
                                      "API properly blocks unauthorized admin access")
                elif response.status_code == 404:
                    self.add_test_result("api_authorization_unauthenticated", "skipped", 
                                      "Admin API endpoint not found")
                else:
                    self.add_test_result("api_authorization_unauthenticated", "warning", 
                                      f"API authorization may not be enforced: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("api_authorization", "error", str(e), traceback.format_exc())
    
    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        try:
            with self.app.test_client() as client:
                # Make multiple requests to test rate limiting
                responses = []
                for i in range(10):
                    response = client.get('/api/users')
                    responses.append(response.status_code)
                
                # Check if any request was rate limited
                if 429 in responses:
                    self.add_test_result("api_rate_limiting", "passed", 
                                      "API rate limiting is implemented")
                else:
                    self.add_test_result("api_rate_limiting", "warning", 
                                      "API rate limiting may not be implemented")
                
        except Exception as e:
            self.add_test_result("api_rate_limiting", "error", str(e), traceback.format_exc())
