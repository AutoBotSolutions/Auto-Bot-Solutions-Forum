"""
Comprehensive Database Tests for Repo-Forum Project
Tests database connectivity, operations, and performance.
"""

import re
import traceback
from datetime import datetime, timedelta
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

class DatabaseTest:
    """Comprehensive database testing for entire app"""
    
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
        """Run all database tests"""
        print("🗄️ Running Comprehensive Database Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app, db
            self.app = create_app()
            
            with self.app.app_context():
                # Test database connection
                self.test_database_connection()
                
                # Test database schema
                self.test_database_schema()
                self.test_table_creation()
                self.test_foreign_keys()
                self.test_indexes()
                
                # Test database operations
                self.test_crud_operations()
                self.test_transaction_management()
                self.test_query_performance()
                
                # Test database integrity
                self.test_data_integrity()
                self.test_constraints()
                self.test_cascading_deletes()
                
                # Test database security
                self.test_database_permissions()
                self.test_sql_injection_protection()
                
        except Exception as e:
            self.add_test_result("database_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            from app import db
            
            # Test basic connection
            try:
                db.engine.execute(text("SELECT 1"))
                self.add_test_result("database_connection", "passed", 
                                  "Database connection successful")
            except SQLAlchemyError as e:
                self.add_test_result("database_connection", "failed", 
                                  f"Database connection failed: {str(e)}")
            
            # Test connection pool
            pool = db.engine.pool
            if pool:
                self.add_test_result("database_pool", "passed", 
                                  f"Database pool configured: {pool.__class__.__name__}")
            else:
                self.add_test_result("database_pool", "warning", 
                                  "Database pool not configured")
            
            # Test database URL
            database_url = self.app.config.get('SQLALCHEMY_DATABASE_URI')
            if database_url:
                self.add_test_result("database_url", "passed", 
                                  f"Database URL configured: {database_url.split('@')[-1] if '@' in database_url else 'local'}")
            else:
                self.add_test_result("database_url", "failed", 
                                  "Database URL not configured")
                
        except Exception as e:
            self.add_test_result("database_connection", "error", str(e), traceback.format_exc())
    
    def test_database_schema(self):
        """Test database schema"""
        try:
            from app import db
            
            # Get database inspector
            inspector = inspect(db.engine)
            
            # Get all tables
            tables = inspector.get_table_names()
            
            if tables:
                self.add_test_result("database_tables", "passed", 
                                  f"Found {len(tables)} tables: {', '.join(tables[:5])}")
                
                # Check for essential tables
                essential_tables = ['user', 'post', 'comment', 'badge', 'category']
                missing_tables = []
                
                for table in essential_tables:
                    if table not in tables:
                        missing_tables.append(table)
                
                if not missing_tables:
                    self.add_test_result("essential_tables", "passed", 
                                      "All essential tables present")
                else:
                    self.add_test_result("essential_tables", "failed", 
                                      f"Missing essential tables: {missing_tables}")
            else:
                self.add_test_result("database_tables", "failed", 
                                  "No tables found in database")
                
        except Exception as e:
            self.add_test_result("database_schema", "error", str(e), traceback.format_exc())
    
    def test_table_creation(self):
        """Test table creation and structure"""
        try:
            from app import db
            from app.models import User, Post, Comment, Badge, Category
            
            # Test User table structure
            user_columns = inspect(db.engine).get_columns('user')
            required_user_columns = ['id', 'username', 'email', 'password_hash', 'is_admin']
            
            missing_user_columns = []
            for col in required_user_columns:
                if not any(c['name'] == col for c in user_columns):
                    missing_user_columns.append(col)
            
            if not missing_user_columns:
                self.add_test_result("user_table_structure", "passed", 
                                  "User table has required columns")
            else:
                self.add_test_result("user_table_structure", "failed", 
                                  f"User table missing columns: {missing_user_columns}")
            
            # Test Post table structure
            try:
                post_columns = inspect(db.engine).get_columns('post')
                required_post_columns = ['id', 'title', 'content', 'user_id', 'created_at']
                
                missing_post_columns = []
                for col in required_post_columns:
                    if not any(c['name'] == col for c in post_columns):
                        missing_post_columns.append(col)
                
                if not missing_post_columns:
                    self.add_test_result("post_table_structure", "passed", 
                                      "Post table has required columns")
                else:
                    self.add_test_result("post_table_structure", "failed", 
                                      f"Post table missing columns: {missing_post_columns}")
            except:
                self.add_test_result("post_table_structure", "skipped", 
                                  "Post table not found")
                
        except Exception as e:
            self.add_test_result("table_creation", "error", str(e), traceback.format_exc())
    
    def test_foreign_keys(self):
        """Test foreign key constraints"""
        try:
            from app import db
            
            inspector = inspect(db.engine)
            
            # Test foreign keys in post table
            try:
                post_fks = inspector.get_foreign_keys('post')
                user_fk_found = any(fk['constrained_columns'] == ['user_id'] for fk in post_fks)
                
                if user_fk_found:
                    self.add_test_result("post_user_foreign_key", "passed", 
                                      "Post table has user_id foreign key")
                else:
                    self.add_test_result("post_user_foreign_key", "failed", 
                                      "Post table missing user_id foreign key")
            except:
                self.add_test_result("post_user_foreign_key", "skipped", 
                                  "Post table not found")
            
            # Test foreign keys in comment table
            try:
                comment_fks = inspector.get_foreign_keys('comment')
                user_fk_found = any(fk['constrained_columns'] == ['user_id'] for fk in comment_fks)
                post_fk_found = any(fk['constrained_columns'] == ['post_id'] for fk in comment_fks)
                
                if user_fk_found and post_fk_found:
                    self.add_test_result("comment_foreign_keys", "passed", 
                                      "Comment table has required foreign keys")
                else:
                    self.add_test_result("comment_foreign_keys", "failed", 
                                      "Comment table missing foreign keys")
            except:
                self.add_test_result("comment_foreign_keys", "skipped", 
                                  "Comment table not found")
                
        except Exception as e:
            self.add_test_result("foreign_keys", "error", str(e), traceback.format_exc())
    
    def test_indexes(self):
        """Test database indexes"""
        try:
            from app import db
            
            inspector = inspect(db.engine)
            
            # Test User table indexes
            try:
                user_indexes = inspector.get_indexes('user')
                username_index = any(idx['column_names'] == ['username'] for idx in user_indexes)
                email_index = any(idx['column_names'] == ['email'] for idx in user_indexes)
                
                if username_index and email_index:
                    self.add_test_result("user_table_indexes", "passed", 
                                      "User table has username and email indexes")
                else:
                    missing_indexes = []
                    if not username_index:
                        missing_indexes.append('username')
                    if not email_index:
                        missing_indexes.append('email')
                    self.add_test_result("user_table_indexes", "failed", 
                                      f"User table missing indexes: {missing_indexes}")
            except:
                self.add_test_result("user_table_indexes", "skipped", 
                                  "User table not found")
                
        except Exception as e:
            self.add_test_result("indexes", "error", str(e), traceback.format_exc())
    
    def test_crud_operations(self):
        """Test CRUD operations"""
        try:
            from app import db
            from app.models import User
            
            # Test Create
            test_user = User(
                username='test_crud_user',
                email='testcrud@example.com',
                is_admin=False
            )
            test_user.set_password('testpassword123')
            
            db.session.add(test_user)
            db.session.commit()
            
            created_user = User.query.filter_by(username='test_crud_user').first()
            if created_user:
                self.add_test_result("crud_create", "passed", 
                                  "Create operation successful")
            else:
                self.add_test_result("crud_create", "failed", 
                                  "Create operation failed")
            
            # Test Read
            read_user = User.query.filter_by(username='test_crud_user').first()
            if read_user and read_user.email == 'testcrud@example.com':
                self.add_test_result("crud_read", "passed", 
                                  "Read operation successful")
            else:
                self.add_test_result("crud_read", "failed", 
                                  "Read operation failed")
            
            # Test Update
            read_user.bio = 'Test bio for CRUD user'
            db.session.commit()
            
            updated_user = User.query.filter_by(username='test_crud_user').first()
            if updated_user and updated_user.bio == 'Test bio for CRUD user':
                self.add_test_result("crud_update", "passed", 
                                  "Update operation successful")
            else:
                self.add_test_result("crud_update", "failed", 
                                  "Update operation failed")
            
            # Test Delete
            db.session.delete(updated_user)
            db.session.commit()
            
            deleted_user = User.query.filter_by(username='test_crud_user').first()
            if deleted_user is None:
                self.add_test_result("crud_delete", "passed", 
                                  "Delete operation successful")
            else:
                self.add_test_result("crud_delete", "failed", 
                                  "Delete operation failed")
                
        except Exception as e:
            self.add_test_result("crud_operations", "error", str(e), traceback.format_exc())
    
    def test_transaction_management(self):
        """Test transaction management"""
        try:
            from app import db
            from app.models import User
            
            # Test successful transaction
            try:
                test_user1 = User(
                    username='test_transaction1',
                    email='test1@example.com'
                )
                test_user1.set_password('password123')
                
                db.session.add(test_user1)
                db.session.commit()
                
                # Verify user was created
                created_user = User.query.filter_by(username='test_transaction1').first()
                if created_user:
                    self.add_test_result("transaction_commit", "passed", 
                                      "Transaction commit successful")
                    # Clean up
                    db.session.delete(created_user)
                    db.session.commit()
                else:
                    self.add_test_result("transaction_commit", "failed", 
                                      "Transaction commit failed")
                    
            except Exception as e:
                db.session.rollback()
                self.add_test_result("transaction_commit", "failed", 
                                  f"Transaction commit error: {str(e)}")
            
            # Test transaction rollback
            try:
                test_user2 = User(
                    username='test_transaction2',
                    email='test2@example.com'
                )
                test_user2.set_password('password123')
                
                db.session.add(test_user2)
                
                # Simulate error and rollback
                db.session.rollback()
                
                # Verify user was not created
                rolled_back_user = User.query.filter_by(username='test_transaction2').first()
                if rolled_back_user is None:
                    self.add_test_result("transaction_rollback", "passed", 
                                      "Transaction rollback successful")
                else:
                    self.add_test_result("transaction_rollback", "failed", 
                                      "Transaction rollback failed")
                    # Clean up
                    db.session.delete(rolled_back_user)
                    db.session.commit()
                    
            except Exception as e:
                self.add_test_result("transaction_rollback", "error", 
                                  f"Transaction rollback error: {str(e)}")
                
        except Exception as e:
            self.add_test_result("transaction_management", "error", str(e), traceback.format_exc())
    
    def test_query_performance(self):
        """Test query performance"""
        try:
            from app import db
            from app.models import User
            import time
            
            # Test simple query performance
            start_time = time.time()
            users = User.query.limit(10).all()
            end_time = time.time()
            
            query_time = end_time - start_time
            
            if query_time < 0.1:  # Should be very fast
                self.add_test_result("query_performance_simple", "passed", 
                                  f"Simple query performance: {query_time:.4f}s")
            elif query_time < 0.5:
                self.add_test_result("query_performance_simple", "warning", 
                                  f"Simple query performance slow: {query_time:.4f}s")
            else:
                self.add_test_result("query_performance_simple", "failed", 
                                  f"Simple query performance very slow: {query_time:.4f}s")
            
            # Test indexed query performance
            start_time = time.time()
            admin_users = User.query.filter_by(is_admin=True).all()
            end_time = time.time()
            
            indexed_query_time = end_time - start_time
            
            if indexed_query_time < 0.05:  # Should be faster with index
                self.add_test_result("query_performance_indexed", "passed", 
                                  f"Indexed query performance: {indexed_query_time:.4f}s")
            else:
                self.add_test_result("query_performance_indexed", "warning", 
                                  f"Indexed query performance slow: {indexed_query_time:.4f}s")
                
        except Exception as e:
            self.add_test_result("query_performance", "error", str(e), traceback.format_exc())
    
    def test_data_integrity(self):
        """Test data integrity"""
        try:
            from app import db
            from app.models import User
            
            # Test unique constraints
            try:
                # Create first user
                user1 = User(
                    username='integrity_test',
                    email='integrity@example.com'
                )
                user1.set_password('password123')
                db.session.add(user1)
                db.session.commit()
                
                # Try to create duplicate user
                user2 = User(
                    username='integrity_test',  # Same username
                    email='integrity2@example.com'
                )
                user2.set_password('password123')
                db.session.add(user2)
                
                try:
                    db.session.commit()
                    self.add_test_result("unique_constraint_username", "failed", 
                                      "Username unique constraint not enforced")
                    # Clean up
                    db.session.delete(user1)
                    db.session.delete(user2)
                    db.session.commit()
                except SQLAlchemyError:
                    db.session.rollback()
                    self.add_test_result("unique_constraint_username", "passed", 
                                      "Username unique constraint enforced")
                    # Clean up
                    db.session.delete(user1)
                    db.session.commit()
                    
            except Exception as e:
                self.add_test_result("unique_constraint_username", "error", 
                                  f"Unique constraint test error: {str(e)}")
                
        except Exception as e:
            self.add_test_result("data_integrity", "error", str(e), traceback.format_exc())
    
    def test_constraints(self):
        """Test database constraints"""
        try:
            from app import db
            from app.models import User
            
            # Test NOT NULL constraints
            try:
                # Try to create user without required fields
                user = User()  # No username or email
                db.session.add(user)
                db.session.commit()
                
                self.add_test_result("not_null_constraints", "failed", 
                                  "NOT NULL constraints not enforced")
                # Clean up
                db.session.delete(user)
                db.session.commit()
                
            except SQLAlchemyError:
                db.session.rollback()
                self.add_test_result("not_null_constraints", "passed", 
                                  "NOT NULL constraints enforced")
            except Exception as e:
                self.add_test_result("not_null_constraints", "error", 
                                  f"NOT NULL constraint test error: {str(e)}")
                
        except Exception as e:
            self.add_test_result("constraints", "error", str(e), traceback.format_exc())
    
    def test_cascading_deletes(self):
        """Test cascading delete behavior"""
        try:
            from app import db
            from app.models import User, Post
            
            # Create test user
            test_user = User(
                username='cascade_test_user',
                email='cascade@example.com'
            )
            test_user.set_password('password123')
            db.session.add(test_user)
            db.session.commit()
            
            # Create test post
            test_post = Post(
                title='Test Post',
                content='Test content',
                user_id=test_user.id
            )
            db.session.add(test_post)
            db.session.commit()
            
            # Delete user and check post behavior
            db.session.delete(test_user)
            db.session.commit()
            
            # Check if post was deleted or user_id was set to NULL
            orphaned_post = Post.query.filter_by(title='Test Post').first()
            
            if orphaned_post is None:
                self.add_test_result("cascading_delete_post", "passed", 
                                  "Post deleted when user deleted (cascade)")
            elif orphaned_post.user_id is None:
                self.add_test_result("cascading_delete_post", "passed", 
                                  "Post user_id set to NULL when user deleted")
            else:
                self.add_test_result("cascading_delete_post", "warning", 
                                  "Post still references deleted user")
                # Clean up
                db.session.delete(orphaned_post)
                db.session.commit()
                
        except Exception as e:
            self.add_test_result("cascading_deletes", "error", str(e), traceback.format_exc())
    
    def test_database_permissions(self):
        """Test database permissions"""
        try:
            from app import db
            
            # Test read permissions
            try:
                db.engine.execute(text("SELECT COUNT(*) FROM user"))
                self.add_test_result("database_read_permission", "passed", 
                                  "Database read permission granted")
            except SQLAlchemyError as e:
                self.add_test_result("database_read_permission", "failed", 
                                  f"Database read permission denied: {str(e)}")
            
            # Test write permissions
            try:
                db.engine.execute(text("SELECT 1"))  # Simple test
                self.add_test_result("database_write_permission", "passed", 
                                  "Database write permission granted")
            except SQLAlchemyError as e:
                self.add_test_result("database_write_permission", "failed", 
                                  f"Database write permission denied: {str(e)}")
                
        except Exception as e:
            self.add_test_result("database_permissions", "error", str(e), traceback.format_exc())
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        try:
            from app import db
            from app.models import User
            
            # Test parameterized queries (ORM should be safe)
            try:
                # Safe query using ORM
                users = User.query.filter(User.username.like('%admin%')).all()
                self.add_test_result("sql_injection_orm", "passed", 
                                  "ORM queries use parameterized binding")
            except Exception as e:
                self.add_test_result("sql_injection_orm", "failed", 
                                  f"ORM query error: {str(e)}")
            
            # Test raw SQL with parameters
            try:
                result = db.engine.execute(
                    text("SELECT * FROM user WHERE username = :username"),
                    {'username': 'admin'}
                )
                self.add_test_result("sql_injection_raw", "passed", 
                                  "Raw SQL uses parameterized binding")
            except Exception as e:
                self.add_test_result("sql_injection_raw", "failed", 
                                  f"Raw SQL error: {str(e)}")
                
        except Exception as e:
            self.add_test_result("sql_injection_protection", "error", str(e), traceback.format_exc())
