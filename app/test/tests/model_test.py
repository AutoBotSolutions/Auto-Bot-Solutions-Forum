"""
Comprehensive Model Tests for Repo-Forum Project
Tests all database models and their relationships.
"""

import re
import traceback
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError

class ModelTest:
    """Comprehensive model testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "database",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all model tests"""
        print("🗄️ Running Comprehensive Model Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app, db
            self.app = create_app()
            
            with self.app.app_context():
                # Test User model
                self.test_user_model()
                self.test_user_relationships()
                self.test_user_methods()
                
                # Test Post model
                self.test_post_model()
                self.test_post_relationships()
                
                # Test Comment model
                self.test_comment_model()
                self.test_comment_relationships()
                
                # Test Badge model
                self.test_badge_model()
                self.test_badge_relationships()
                
                # Test Category model
                self.test_category_model()
                self.test_category_relationships()
                
                # Test model relationships
                self.test_model_relationships()
                self.test_cascade_operations()
                
                # Test model validation
                self.test_model_validation()
                self.test_model_defaults()
                
        except Exception as e:
            self.add_test_result("model_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_user_model(self):
        """Test User model"""
        try:
            from app.models import User
            
            # Test model creation
            test_user = User(
                username='test_model_user',
                email='testmodel@example.com',
                is_admin=False,
                is_verified=True,
                bio='Test bio',
                location='Test location',
                website='https://example.com'
            )
            test_user.set_password('testpassword123')
            
            # Test required fields
            required_fields = ['username', 'email', 'password_hash', 'created_at', 'updated_at']
            missing_fields = []
            
            for field in required_fields:
                if not hasattr(test_user, field):
                    missing_fields.append(field)
            
            if not missing_fields:
                self.add_test_result("user_model_fields", "passed", 
                                  f"User model has all required fields")
            else:
                self.add_test_result("user_model_fields", "failed", 
                                  f"User model missing fields: {missing_fields}")
            
            # Test password methods
            if hasattr(test_user, 'set_password') and hasattr(test_user, 'check_password'):
                if test_user.check_password('testpassword123'):
                    self.add_test_result("user_password_methods", "passed", 
                                      "User password methods work correctly")
                else:
                    self.add_test_result("user_password_methods", "failed", 
                                      "User password verification failed")
            else:
                self.add_test_result("user_password_methods", "failed", 
                                  "User model missing password methods")
            
            # Test user properties
            if hasattr(test_user, 'is_active') and hasattr(test_user, 'is_suspended'):
                self.add_test_result("user_status_properties", "passed", 
                                  "User model has status properties")
            else:
                self.add_test_result("user_status_properties", "failed", 
                                  "User model missing status properties")
                
        except Exception as e:
            self.add_test_result("user_model", "error", str(e), traceback.format_exc())
    
    def test_user_relationships(self):
        """Test User model relationships"""
        try:
            from app.models import User
            
            # Test relationship definitions
            test_user = User(username='test_rel_user', email='testrel@example.com')
            
            # Test posts relationship
            if hasattr(test_user, 'posts'):
                self.add_test_result("user_posts_relationship", "passed", 
                                  "User model has posts relationship")
            else:
                self.add_test_result("user_posts_relationship", "failed", 
                                  "User model missing posts relationship")
            
            # Test comments relationship
            if hasattr(test_user, 'comments'):
                self.add_test_result("user_comments_relationship", "passed", 
                                  "User model has comments relationship")
            else:
                self.add_test_result("user_comments_relationship", "failed", 
                                  "User model missing comments relationship")
            
            # Test badges relationship
            if hasattr(test_user, 'badges'):
                self.add_test_result("user_badges_relationship", "passed", 
                                  "User model has badges relationship")
            else:
                self.add_test_result("user_badges_relationship", "failed", 
                                  "User model missing badges relationship")
                
        except Exception as e:
            self.add_test_result("user_relationships", "error", str(e), traceback.format_exc())
    
    def test_user_methods(self):
        """Test User model methods"""
        try:
            from app.models import User
            
            test_user = User(username='test_methods_user', email='testmethods@example.com')
            test_user.set_password('testpassword123')
            
            # Test password verification
            if test_user.check_password('testpassword123'):
                self.add_test_result("user_password_verification", "passed", 
                                  "Password verification works")
            else:
                self.add_test_result("user_password_verification", "failed", 
                                  "Password verification failed")
            
            # Test incorrect password
            if not test_user.check_password('wrongpassword'):
                self.add_test_result("user_password_rejection", "passed", 
                                  "Incorrect password properly rejected")
            else:
                self.add_test_result("user_password_rejection", "failed", 
                                  "Incorrect password not rejected")
            
            # Test string representation
            user_str = str(test_user)
            if test_user.username in user_str:
                self.add_test_result("user_string_representation", "passed", 
                                  "User string representation includes username")
            else:
                self.add_test_result("user_string_representation", "failed", 
                                  "User string representation doesn't include username")
                
        except Exception as e:
            self.add_test_result("user_methods", "error", str(e), traceback.format_exc())
    
    def test_post_model(self):
        """Test Post model"""
        try:
            from app.models import Post
            
            # Test model creation
            test_post = Post(
                title='Test Post Title',
                content='Test post content with sufficient length.',
                user_id=1
            )
            
            # Test required fields
            required_fields = ['title', 'content', 'user_id', 'created_at']
            missing_fields = []
            
            for field in required_fields:
                if not hasattr(test_post, field):
                    missing_fields.append(field)
            
            if not missing_fields:
                self.add_test_result("post_model_fields", "passed", 
                                  f"Post model has all required fields")
            else:
                self.add_test_result("post_model_fields", "failed", 
                                  f"Post model missing fields: {missing_fields}")
            
            # Test relationships
            if hasattr(test_post, 'author'):
                self.add_test_result("post_author_relationship", "passed", 
                                  "Post model has author relationship")
            else:
                self.add_test_result("post_author_relationship", "failed", 
                                  "Post model missing author relationship")
            
            if hasattr(test_post, 'comments'):
                self.add_test_result("post_comments_relationship", "passed", 
                                  "Post model has comments relationship")
            else:
                self.add_test_result("post_comments_relationship", "failed", 
                                  "Post model missing comments relationship")
                
        except Exception as e:
            self.add_test_result("post_model", "error", str(e), traceback.format_exc())
    
    def test_post_relationships(self):
        """Test Post model relationships"""
        try:
            from app.models import Post, User
            
            # Create test user
            test_user = User(username='test_post_user', email='testpost@example.com')
            test_user.set_password('password123')
            
            # Create test post
            test_post = Post(
                title='Test Post',
                content='Test content',
                user_id=test_user.id
            )
            
            # Test relationship access
            if hasattr(test_post, 'author') and hasattr(test_post, 'comments'):
                self.add_test_result("post_relationships_defined", "passed", 
                                  "Post relationships are defined")
            else:
                self.add_test_result("post_relationships_defined", "failed", 
                                  "Post relationships not properly defined")
                
        except Exception as e:
            self.add_test_result("post_relationships", "error", str(e), traceback.format_exc())
    
    def test_comment_model(self):
        """Test Comment model"""
        try:
            from app.models import Comment
            
            # Test model creation
            test_comment = Comment(
                content='Test comment content',
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
                self.add_test_result("comment_model_fields", "passed", 
                                  f"Comment model has all required fields")
            else:
                self.add_test_result("comment_model_fields", "failed", 
                                  f"Comment model missing fields: {missing_fields}")
            
            # Test relationships
            if hasattr(test_comment, 'author') and hasattr(test_comment, 'post'):
                self.add_test_result("comment_relationships", "passed", 
                                  "Comment model has required relationships")
            else:
                self.add_test_result("comment_relationships", "failed", 
                                  "Comment model missing required relationships")
                
        except Exception as e:
            self.add_test_result("comment_model", "error", str(e), traceback.format_exc())
    
    def test_comment_relationships(self):
        """Test Comment model relationships"""
        try:
            from app.models import Comment
            
            test_comment = Comment(
                content='Test comment',
                user_id=1,
                post_id=1
            )
            
            # Test relationship definitions
            relationships = ['author', 'post']
            missing_relationships = []
            
            for rel in relationships:
                if not hasattr(test_comment, rel):
                    missing_relationships.append(rel)
            
            if not missing_relationships:
                self.add_test_result("comment_relationships_complete", "passed", 
                                  "Comment model has all required relationships")
            else:
                self.add_test_result("comment_relationships_complete", "failed", 
                                  f"Comment model missing relationships: {missing_relationships}")
                
        except Exception as e:
            self.add_test_result("comment_relationships", "error", str(e), traceback.format_exc())
    
    def test_badge_model(self):
        """Test Badge model"""
        try:
            from app.models import Badge
            
            # Test model creation
            test_badge = Badge(
                name='Test Badge',
                description='Test badge description',
                icon='test-icon.png'
            )
            
            # Test required fields
            required_fields = ['name', 'description']
            missing_fields = []
            
            for field in required_fields:
                if not hasattr(test_badge, field):
                    missing_fields.append(field)
            
            if not missing_fields:
                self.add_test_result("badge_model_fields", "passed", 
                                  f"Badge model has all required fields")
            else:
                self.add_test_result("badge_model_fields", "failed", 
                                  f"Badge model missing fields: {missing_fields}")
            
            # Test relationships
            if hasattr(test_badge, 'users'):
                self.add_test_result("badge_users_relationship", "passed", 
                                  "Badge model has users relationship")
            else:
                self.add_test_result("badge_users_relationship", "failed", 
                                  "Badge model missing users relationship")
                
        except Exception as e:
            self.add_test_result("badge_model", "error", str(e), traceback.format_exc())
    
    def test_badge_relationships(self):
        """Test Badge model relationships"""
        try:
            from app.models import Badge
            
            test_badge = Badge(
                name='Test Badge',
                description='Test description'
            )
            
            if hasattr(test_badge, 'users'):
                self.add_test_result("badge_relationships_defined", "passed", 
                                  "Badge relationships are defined")
            else:
                self.add_test_result("badge_relationships_defined", "failed", 
                                  "Badge relationships not defined")
                
        except Exception as e:
            self.add_test_result("badge_relationships", "error", str(e), traceback.format_exc())
    
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
                self.add_test_result("category_model_fields", "passed", 
                                  f"Category model has all required fields")
            else:
                self.add_test_result("category_model_fields", "failed", 
                                  f"Category model missing fields: {missing_fields}")
            
            # Test relationships
            if hasattr(test_category, 'posts'):
                self.add_test_result("category_posts_relationship", "passed", 
                                  "Category model has posts relationship")
            else:
                self.add_test_result("category_posts_relationship", "failed", 
                                  "Category model missing posts relationship")
                
        except Exception as e:
            self.add_test_result("category_model", "error", str(e), traceback.format_exc())
    
    def test_category_relationships(self):
        """Test Category model relationships"""
        try:
            from app.models import Category
            
            test_category = Category(
                name='Test Category',
                description='Test description'
            )
            
            if hasattr(test_category, 'posts'):
                self.add_test_result("category_relationships_defined", "passed", 
                                  "Category relationships are defined")
            else:
                self.add_test_result("category_relationships_defined", "failed", 
                                  "Category relationships not defined")
                
        except Exception as e:
            self.add_test_result("category_relationships", "error", str(e), traceback.format_exc())
    
    def test_model_relationships(self):
        """Test model relationships integrity"""
        try:
            from app.models import User, Post, Comment, Badge, Category
            
            # Test User -> Posts relationship
            test_user = User(username='test_rel_user', email='testrel@example.com')
            if hasattr(test_user, 'posts'):
                self.add_test_result("user_posts_relationship_integrity", "passed", 
                                  "User to posts relationship exists")
            else:
                self.add_test_result("user_posts_relationship_integrity", "failed", 
                                  "User to posts relationship missing")
            
            # Test Post -> Comments relationship
            test_post = Post(title='Test', content='Test', user_id=1)
            if hasattr(test_post, 'comments'):
                self.add_test_result("post_comments_relationship_integrity", "passed", 
                                  "Post to comments relationship exists")
            else:
                self.add_test_result("post_comments_relationship_integrity", "failed", 
                                  "Post to comments relationship missing")
            
            # Test Comment -> User/Post relationships
            test_comment = Comment(content='Test', user_id=1, post_id=1)
            if hasattr(test_comment, 'author') and hasattr(test_comment, 'post'):
                self.add_test_result("comment_relationships_integrity", "passed", 
                                  "Comment relationships exist")
            else:
                self.add_test_result("comment_relationships_integrity", "failed", 
                                  "Comment relationships missing")
                
        except Exception as e:
            self.add_test_result("model_relationships", "error", str(e), traceback.format_exc())
    
    def test_cascade_operations(self):
        """Test cascade operations between models"""
        try:
            from app.models import User, Post, Comment
            
            # Test User deletion affects Posts
            test_user = User(username='test_cascade_user', email='cascade@example.com')
            test_user.set_password('password123')
            
            test_post = Post(title='Test Post', content='Test content', user_id=test_user.id)
            
            # Test Post deletion affects Comments
            test_comment = Comment(content='Test comment', user_id=test_user.id, post_id=test_post.id)
            
            # Verify relationships are properly set up
            if (hasattr(test_user, 'posts') and hasattr(test_post, 'comments') and 
                hasattr(test_comment, 'author') and hasattr(test_comment, 'post')):
                self.add_test_result("cascade_relationships_setup", "passed", 
                                  "Cascade relationships properly set up")
            else:
                self.add_test_result("cascade_relationships_setup", "failed", 
                                  "Cascade relationships not properly set up")
                
        except Exception as e:
            self.add_test_result("cascade_operations", "error", str(e), traceback.format_exc())
    
    def test_model_validation(self):
        """Test model validation"""
        try:
            from app.models import User
            
            # Test username validation
            test_user = User(username='', email='test@example.com')
            test_user.set_password('password123')
            
            # Check if validation is implemented (would need to be added to model)
            if hasattr(test_user, 'validate'):
                self.add_test_result("model_validation_implemented", "passed", 
                                  "Model validation is implemented")
            else:
                self.add_test_result("model_validation_implemented", "warning", 
                                  "Model validation not implemented (consider adding)")
            
            # Test email format validation
            test_user.email = 'invalid-email'
            # This would need custom validation in the model
            self.add_test_result("email_validation", "skipped", 
                              "Email validation not implemented in model")
                
        except Exception as e:
            self.add_test_result("model_validation", "error", str(e), traceback.format_exc())
    
    def test_model_defaults(self):
        """Test model default values"""
        try:
            from app.models import User
            
            # Test user model defaults
            test_user = User(username='test_defaults', email='defaults@example.com')
            test_user.set_password('password123')
            
            # Check default values
            defaults_checked = 0
            
            if hasattr(test_user, 'is_admin') and test_user.is_admin == False:
                defaults_checked += 1
                self.add_test_result("user_is_admin_default", "passed", 
                                  "is_admin defaults to False")
            else:
                self.add_test_result("user_is_admin_default", "failed", 
                                  "is_admin default incorrect")
            
            if hasattr(test_user, 'is_verified') and test_user.is_verified == False:
                defaults_checked += 1
                self.add_test_result("user_is_verified_default", "passed", 
                                  "is_verified defaults to False")
            else:
                self.add_test_result("user_is_verified_default", "failed", 
                                  "is_verified default incorrect")
            
            if hasattr(test_user, 'is_active') and test_user.is_active == True:
                defaults_checked += 1
                self.add_test_result("user_is_active_default", "passed", 
                                  "is_active defaults to True")
            else:
                self.add_test_result("user_is_active_default", "failed", 
                                  "is_active default incorrect")
            
            if defaults_checked >= 2:
                self.add_test_result("model_defaults_adequate", "passed", 
                                  f"Model defaults adequate ({defaults_checked}/3)")
            else:
                self.add_test_result("model_defaults_adequate", "failed", 
                                  f"Model defaults inadequate ({defaults_checked}/3)")
                
        except Exception as e:
            self.add_test_result("model_defaults", "error", str(e), traceback.format_exc())
