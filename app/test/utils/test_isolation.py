"""
Test Data Isolation and Cleanup Utilities for Repo-Forum Project
Provides test isolation, cleanup, and database management utilities.
"""

import os
import tempfile
import shutil
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator, Optional
from flask import Flask
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class TestDatabaseManager:
    """Manages test database isolation and cleanup"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.test_db_url = None
        self.original_db_url = None
        self.test_engine = None
        self.test_session_factory = None
    
    @contextmanager
    def isolated_database(self) -> Generator[Any, None, None]:
        """Create an isolated test database"""
        try:
            # Store original database URL
            self.original_db_url = self.app.config.get('SQLALCHEMY_DATABASE_URI')
            
            # Create test database URL
            self.test_db_url = self._create_test_db_url()
            
            # Update app configuration
            self.app.config['SQLALCHEMY_DATABASE_URI'] = self.test_db_url
            
            # Create test database
            self._create_test_database()
            
            # Create test engine and session
            self.test_engine = create_engine(self.test_db_url)
            self.test_session_factory = sessionmaker(bind=self.test_engine)
            
            # Create tables
            from app import db
            with self.app.app_context():
                db.create_all()
            
            yield self.test_engine
            
        finally:
            # Cleanup test database
            self._cleanup_test_database()
            
            # Restore original configuration
            if self.original_db_url:
                self.app.config['SQLALCHEMY_DATABASE_URI'] = self.original_db_url
    
    def _create_test_db_url(self) -> str:
        """Create a unique test database URL"""
        if self.original_db_url:
            # For SQLite, create a temporary file
            if 'sqlite' in self.original_db_url:
                test_db_file = tempfile.mktemp(suffix='.db', prefix='test_')
                return f'sqlite:///{test_db_file}'
            
            # For PostgreSQL/MySQL, add test suffix
            if 'postgresql' in self.original_db_url:
                return self.original_db_url.rsplit('/', 1)[0] + f'/test_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            
            if 'mysql' in self.original_db_url:
                return self.original_db_url.rsplit('/', 1)[0] + f'/test_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        # Fallback to SQLite
        test_db_file = tempfile.mktemp(suffix='.db', prefix='test_')
        return f'sqlite:///{test_db_file}'
    
    def _create_test_database(self):
        """Create the test database"""
        if 'postgresql' in self.test_db_url:
            # Create PostgreSQL database
            admin_url = self.test_db_url.rsplit('/', 1)[0] + '/postgres'
            engine = create_engine(admin_url)
            with engine.connect() as conn:
                conn.execute(text("COMMIT"))  # Close any existing transaction
                db_name = self.test_db_url.rsplit('/')[-1]
                conn.execute(text(f"CREATE DATABASE {db_name}"))
            engine.dispose()
        
        elif 'mysql' in self.test_db_url:
            # Create MySQL database
            admin_url = self.test_db_url.rsplit('/', 1)[0]
            engine = create_engine(admin_url)
            with engine.connect() as conn:
                db_name = self.test_db_url.rsplit('/')[-1]
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
            engine.dispose()
    
    def _cleanup_test_database(self):
        """Clean up the test database"""
        if self.test_engine:
            self.test_engine.dispose()
            self.test_engine = None
        
        if self.test_db_url and 'sqlite' in self.test_db_url:
            # Remove SQLite file
            db_file = self.test_db_url.replace('sqlite:///', '')
            if os.path.exists(db_file):
                os.remove(db_file)
        
        elif self.test_db_url and 'postgresql' in self.test_db_url:
            # Drop PostgreSQL database
            try:
                admin_url = self.test_db_url.rsplit('/', 1)[0] + '/postgres'
                engine = create_engine(admin_url)
                with engine.connect() as conn:
                    conn.execute(text("COMMIT"))
                    db_name = self.test_db_url.rsplit('/')[-1]
                    conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
                engine.dispose()
            except Exception as e:
                print(f"Error dropping PostgreSQL database: {e}")
        
        elif self.test_db_url and 'mysql' in self.test_db_url:
            # Drop MySQL database
            try:
                admin_url = self.test_db_url.rsplit('/', 1)[0]
                engine = create_engine(admin_url)
                with engine.connect() as conn:
                    db_name = self.test_db_url.rsplit('/')[-1]
                    conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
                engine.dispose()
            except Exception as e:
                print(f"Error dropping MySQL database: {e}")

class TestSessionManager:
    """Manages test sessions and cleanup"""
    
    def __init__(self, db):
        self.db = db
        self.created_objects = []
        self.sessions = []
    
    @contextmanager
    def test_session(self) -> Generator[Any, None, None]:
        """Create a test session with automatic cleanup"""
        session = self.db.session
        self.sessions.append(session)
        
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def track_object(self, object_type: str, object_id: int):
        """Track an object for cleanup"""
        self.created_objects.append((object_type, object_id))
    
    def cleanup_session(self):
        """Clean up all tracked objects"""
        try:
            # Clean up in reverse order to handle foreign key constraints
            for object_type, object_id in reversed(self.created_objects):
                try:
                    if object_type == 'user':
                        from app.models import User
                        obj = User.query.get(object_id)
                    elif object_type == 'post':
                        from app.models import Post
                        obj = Post.query.get(object_id)
                    elif object_type == 'comment':
                        from app.models import Comment
                        obj = Comment.query.get(object_id)
                    elif object_type == 'category':
                        from app.models import Category
                        obj = Category.query.get(object_id)
                    elif object_type == 'badge':
                        from app.models import Badge
                        obj = Badge.query.get(object_id)
                    else:
                        continue
                    
                    if obj:
                        self.db.session.delete(obj)
                        self.db.session.commit()
                except Exception as e:
                    print(f"Error cleaning up {object_type} {object_id}: {e}")
                    self.db.session.rollback()
            
            self.created_objects.clear()
            
        except Exception as e:
            print(f"Error during session cleanup: {e}")
            self.db.session.rollback()
    
    def reset_session(self):
        """Reset the session"""
        try:
            self.db.session.remove()
            self.created_objects.clear()
        except Exception as e:
            print(f"Error resetting session: {e}")

class TestDataCleaner:
    """Cleans up test data and ensures test isolation"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.cleanup_strategies = {}
    
    def register_cleanup_strategy(self, object_type: str, strategy):
        """Register a cleanup strategy for an object type"""
        self.cleanup_strategies[object_type] = strategy
    
    def cleanup_test_data(self, object_type: str = None, object_id: int = None):
        """Clean up test data"""
        from app import db
        
        with self.app.app_context():
            if object_type and object_id:
                # Clean up specific object
                strategy = self.cleanup_strategies.get(object_type)
                if strategy:
                    strategy(object_id)
                else:
                    self._default_cleanup(object_type, object_id)
            else:
                # Clean up all test data
                self._cleanup_all_test_data()
    
    def _default_cleanup(self, object_type: str, object_id: int):
        """Default cleanup strategy"""
        from app import db
        
        try:
            if object_type == 'user':
                from app.models import User
                obj = User.query.get(object_id)
            elif object_type == 'post':
                from app.models import Post
                obj = Post.query.get(object_id)
            elif object_type == 'comment':
                from app.models import Comment
                obj = Comment.query.get(object_id)
            elif object_type == 'category':
                from app.models import Category
                obj = Category.query.get(object_id)
            elif object_type == 'badge':
                from app.models import Badge
                obj = Badge.query.get(object_id)
            else:
                return
            
            if obj:
                db.session.delete(obj)
                db.session.commit()
        except Exception as e:
            print(f"Error in default cleanup: {e}")
            db.session.rollback()
    
    def _cleanup_all_test_data(self):
        """Clean up all test data"""
        from app import db
        
        try:
            # Clean up in order of dependencies
            cleanup_order = [
                ('comment', Comment),
                ('post', Post),
                ('user', User),
                ('category', Category),
                ('badge', Badge)
            ]
            
            for object_type, model_class in cleanup_order:
                # Delete test objects (those with test_ prefix or created after test start)
                test_objects = model_class.query.filter(
                    model_class.username.like('test_%') if hasattr(model_class, 'username') else True
                ).all()
                
                for obj in test_objects:
                    db.session.delete(obj)
                
                db.session.commit()
                
        except Exception as e:
            print(f"Error cleaning up all test data: {e}")
            db.session.rollback()

class TestIsolationManager:
    """Main test isolation manager"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.db_manager = TestDatabaseManager(app)
        self.session_manager = None
        self.data_cleaner = TestDataCleaner(app)
    
    @contextmanager
    def isolated_test_environment(self) -> Generator[Dict[str, Any], None, None]:
        """Create a completely isolated test environment"""
        with self.db_manager.isolated_database() as engine:
            # Create session manager
            from app import db
            self.session_manager = TestSessionManager(db)
            
            try:
                yield {
                    'engine': engine,
                    'session_manager': self.session_manager,
                    'data_cleaner': self.data_cleaner,
                    'app': self.app
                }
            finally:
                # Cleanup
                if self.session_manager:
                    self.session_manager.cleanup_session()
                    self.session_manager = None
    
    def setup_default_cleanup_strategies(self):
        """Setup default cleanup strategies"""
        self.data_cleaner.register_cleanup_strategy('user', self._cleanup_user)
        self.data_cleaner.register_cleanup_strategy('post', self._cleanup_post)
        self.data_cleaner.register_cleanup_strategy('comment', self._cleanup_comment)
    
    def _cleanup_user(self, user_id: int):
        """Cleanup user and related data"""
        from app import db
        from app.models import User, Post, Comment
        
        try:
            user = User.query.get(user_id)
            if user:
                # Delete user's comments
                Comment.query.filter_by(user_id=user_id).delete()
                # Delete user's posts
                Post.query.filter_by(user_id=user_id).delete()
                # Delete user
                db.session.delete(user)
                db.session.commit()
        except Exception as e:
            print(f"Error cleaning up user {user_id}: {e}")
            db.session.rollback()
    
    def _cleanup_post(self, post_id: int):
        """Cleanup post and related data"""
        from app import db
        from app.models import Post, Comment
        
        try:
            post = Post.query.get(post_id)
            if post:
                # Delete post's comments
                Comment.query.filter_by(post_id=post_id).delete()
                # Delete post
                db.session.delete(post)
                db.session.commit()
        except Exception as e:
            print(f"Error cleaning up post {post_id}: {e}")
            db.session.rollback()
    
    def _cleanup_comment(self, comment_id: int):
        """Cleanup comment"""
        from app import db
        from app.models import Comment
        
        try:
            comment = Comment.query.get(comment_id)
            if comment:
                db.session.delete(comment)
                db.session.commit()
        except Exception as e:
            print(f"Error cleaning up comment {comment_id}: {e}")
            db.session.rollback()

# Global isolation manager instance
isolation_manager = None

def get_isolation_manager(app: Flask) -> TestIsolationManager:
    """Get or create the isolation manager"""
    global isolation_manager
    if isolation_manager is None:
        isolation_manager = TestIsolationManager(app)
        isolation_manager.setup_default_cleanup_strategies()
    return isolation_manager
