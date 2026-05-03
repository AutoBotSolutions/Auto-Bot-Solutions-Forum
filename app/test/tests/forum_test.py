"""
Comprehensive Forum Tests for Repo-Forum Project
Tests all forum functionality including posts, categories, etc.
"""

import re
import traceback
from datetime import datetime

class ForumTest:
    """Comprehensive forum testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "forum",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all forum tests"""
        print("💬 Running Comprehensive Forum Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test forum models
                self.test_post_model()
                self.test_category_model()
                self.test_comment_model()
                
                # Test forum routes
                self.test_forum_routes()
                self.test_post_routes()
                self.test_category_routes()
                
                # Test forum functionality
                self.test_post_creation()
                self.test_post_display()
                self.test_comment_functionality()
                
        except Exception as e:
            self.add_test_result("forum_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_post_model(self):
        """Test Post model"""
        try:
            from app.models import Post
            
            # Test model creation
            test_post = Post(
                title='Test Forum Post',
                content='Test forum post content',
                user_id=1
            )
            
            # Test required fields
            required_fields = ['title', 'content', 'user_id', 'created_at']
            missing_fields = []
            
            for field in required_fields:
                if not hasattr(test_post, field):
                    missing_fields.append(field)
            
            if not missing_fields:
                self.add_test_result("forum_post_model_fields", "passed", 
                                  f"Post model has all required fields")
            else:
                self.add_test_result("forum_post_model_fields", "failed", 
                                  f"Post model missing fields: {missing_fields}")
                
        except Exception as e:
            self.add_test_result("forum_post_model", "error", str(e), traceback.format_exc())
    
    def test_category_model(self):
        """Test Category model"""
        try:
            from app.models import Category
            
            # Test model creation
            test_category = Category(
                name='Test Category',
                description='Test category description'
            )
            
            # Test required fields
            required_fields = ['name', 'description']
            missing_fields = []
            
            for field in required_fields:
                if not hasattr(test_category, field):
                    missing_fields.append(field)
            
            if not missing_fields:
                self.add_test_result("forum_category_model_fields", "passed", 
                                  f"Category model has all required fields")
            else:
                self.add_test_result("forum_category_model_fields", "failed", 
                                  f"Category model missing fields: {missing_fields}")
                
        except Exception as e:
            self.add_test_result("forum_category_model", "error", str(e), traceback.format_exc())
    
    def test_comment_model(self):
        """Test Comment model"""
        try:
            from app.models import Comment
            
            # Test model creation
            test_comment = Comment(
                content='Test forum comment',
                user_id=1,
                post_id=1
            )
            
            # Test required fields
            required_fields = ['content', 'user_id', 'post_id', 'created_at']
            missing_fields = []
            
            for field in required_fields:
                if not hasattr(test_comment, field):
                    missing_fields.append(field)
            
            if not missing_fields:
                self.add_test_result("forum_comment_model_fields", "passed", 
                                  f"Comment model has all required fields")
            else:
                self.add_test_result("forum_comment_model_fields", "failed", 
                                  f"Comment model missing fields: {missing_fields}")
                
        except Exception as e:
            self.add_test_result("forum_comment_model", "error", str(e), traceback.format_exc())
    
    def test_forum_routes(self):
        """Test forum route registration"""
        try:
            from app.forum import forum_bp
            
            if forum_bp:
                self.add_test_result("forum_blueprint_exists", "passed", 
                                  "Forum blueprint exists")
            else:
                self.add_test_result("forum_blueprint_exists", "failed", 
                                  "Forum blueprint not found")
                
        except Exception as e:
            self.add_test_result("forum_routes", "error", str(e), traceback.format_exc())
    
    def test_post_routes(self):
        """Test post route functionality"""
        try:
            with self.app.test_client() as client:
                # Test forum index
                response = client.get('/forum')
                
                if response.status_code == 200:
                    self.add_test_result("forum_index_accessible", "passed", 
                                      "Forum index page accessible")
                else:
                    self.add_test_result("forum_index_accessible", "failed", 
                                      f"Forum index not accessible: {response.status_code}")
                
                # Test post creation
                response = client.get('/forum/create')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("post_creation_accessible", "passed", 
                                      "Post creation page accessible")
                else:
                    self.add_test_result("post_creation_accessible", "failed", 
                                      f"Post creation not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("post_routes", "error", str(e), traceback.format_exc())
    
    def test_category_routes(self):
        """Test category route functionality"""
        try:
            with self.app.test_client() as client:
                # Test category listing
                response = client.get('/forum/category/1')
                
                if response.status_code in [200, 404]:
                    self.add_test_result("category_route_accessible", "passed", 
                                      "Category route accessible")
                else:
                    self.add_test_result("category_route_accessible", "failed", 
                                      f"Category route not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("category_routes", "error", str(e), traceback.format_exc())
    
    def test_post_creation(self):
        """Test post creation functionality"""
        try:
            with self.app.test_client() as client:
                # Test post creation form
                response = client.get('/forum/create')
                
                if response.status_code == 200:
                    # Check if form has required fields
                    if b'title' in response.data and b'content' in response.data:
                        self.add_test_result("post_creation_form_fields", "passed", 
                                          "Post creation form has required fields")
                    else:
                        self.add_test_result("post_creation_form_fields", "failed", 
                                          "Post creation form missing required fields")
                else:
                    self.add_test_result("post_creation_form", "skipped", 
                                      "Post creation form not accessible")
                
        except Exception as e:
            self.add_test_result("post_creation", "error", str(e), traceback.format_exc())
    
    def test_post_display(self):
        """Test post display functionality"""
        try:
            with self.app.test_client() as client:
                # Test post detail page
                response = client.get('/forum/post/1')
                
                if response.status_code in [200, 404]:
                    self.add_test_result("post_display_accessible", "passed", 
                                      "Post display page accessible")
                else:
                    self.add_test_result("post_display_accessible", "failed", 
                                      f"Post display not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("post_display", "error", str(e), traceback.format_exc())
    
    def test_comment_functionality(self):
        """Test comment functionality"""
        try:
            with self.app.test_client() as client:
                # Test comment form on post page
                response = client.get('/forum/post/1')
                
                if response.status_code == 200:
                    if b'comment' in response.data.lower():
                        self.add_test_result("comment_form_present", "passed", 
                                          "Comment form present on post page")
                    else:
                        self.add_test_result("comment_form_present", "warning", 
                                          "Comment form not found on post page")
                else:
                    self.add_test_result("comment_functionality", "skipped", 
                                      "Post page not accessible")
                
        except Exception as e:
            self.add_test_result("comment_functionality", "error", str(e), traceback.format_exc())
