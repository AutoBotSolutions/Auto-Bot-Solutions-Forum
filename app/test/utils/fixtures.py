"""
Test Data Fixtures for Repo-Forum Project
Provides test data creation and management utilities.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class TestDataFactory:
    """Factory for creating test data"""
    
    def __init__(self, app=None):
        self.app = app
        self._user_counter = 1
        self._post_counter = 1
        self._comment_counter = 1
        self._category_counter = 1
    
    def create_test_user(self, **overrides) -> Dict[str, Any]:
        """Create test user data"""
        user_data = {
            'username': f'testuser{self._user_counter}',
            'email': f'testuser{self._user_counter}@example.com',
            'password': 'testpassword123',
            'is_admin': False,
            'is_verified': True,
            'is_active': True,
            'is_suspended': False,
            'is_banned': False,
            'bio': f'Test user {self._user_counter} bio',
            'location': f'Test City {self._user_counter}',
            'website': f'https://testuser{self._user_counter}.example.com',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        user_data.update(overrides)
        self._user_counter += 1
        
        return user_data
    
    def create_test_admin_user(self, **overrides) -> Dict[str, Any]:
        """Create test admin user data"""
        admin_data = self.create_test_user(
            username=f'testadmin{self._user_counter}',
            email=f'testadmin{self._user_counter}@example.com',
            is_admin=True,
            **overrides
        )
        return admin_data
    
    def create_test_post(self, user_id: int, category_id: Optional[int] = None, **overrides) -> Dict[str, Any]:
        """Create test post data"""
        post_data = {
            'title': f'Test Post {self._post_counter}',
            'content': f'This is test post content number {self._post_counter}. ' * 10,
            'user_id': user_id,
            'category_id': category_id,
            'is_published': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        post_data.update(overrides)
        self._post_counter += 1
        
        return post_data
    
    def create_test_comment(self, user_id: int, post_id: int, **overrides) -> Dict[str, Any]:
        """Create test comment data"""
        comment_data = {
            'content': f'Test comment {self._comment_counter} content.',
            'user_id': user_id,
            'post_id': post_id,
            'is_approved': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        comment_data.update(overrides)
        self._comment_counter += 1
        
        return comment_data
    
    def create_test_category(self, **overrides) -> Dict[str, Any]:
        """Create test category data"""
        category_data = {
            'name': f'Test Category {self._category_counter}',
            'description': f'Test category {self._category_counter} description.',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        category_data.update(overrides)
        self._category_counter += 1
        
        return category_data
    
    def create_test_badge(self, **overrides) -> Dict[str, Any]:
        """Create test badge data"""
        badge_data = {
            'name': f'Test Badge {random.randint(1, 100)}',
            'description': f'Test badge description.',
            'icon': f'test-badge-{random.randint(1, 10)}.png',
            'is_active': True,
            'created_at': datetime.utcnow()
        }
        
        badge_data.update(overrides)
        return badge_data
    
    def create_test_message(self, sender_id: int, recipient_id: int, **overrides) -> Dict[str, Any]:
        """Create test message data"""
        message_data = {
            'subject': f'Test Message {random.randint(1, 1000)}',
            'content': f'Test message content.',
            'sender_id': sender_id,
            'recipient_id': recipient_id,
            'is_read': False,
            'created_at': datetime.utcnow()
        }
        
        message_data.update(overrides)
        return message_data
    
    def create_test_notification(self, user_id: int, **overrides) -> Dict[str, Any]:
        """Create test notification data"""
        notification_data = {
            'title': f'Test Notification',
            'message': f'Test notification message.',
            'user_id': user_id,
            'is_read': False,
            'notification_type': 'info',
            'created_at': datetime.utcnow()
        }
        
        notification_data.update(overrides)
        return notification_data

class DatabaseFixture:
    """Database fixture for creating and cleaning up test data"""
    
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.factory = TestDataFactory(app)
        self._created_objects = []
    
    def create_user(self, **overrides) -> Any:
        """Create a user in the database"""
        from app.models import User
        
        user_data = self.factory.create_test_user(**overrides)
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            is_admin=user_data.get('is_admin', False),
            is_verified=user_data.get('is_verified', True),
            is_active=user_data.get('is_active', True),
            bio=user_data.get('bio'),
            location=user_data.get('location'),
            website=user_data.get('website'),
            created_at=user_data.get('created_at', datetime.utcnow())
        )
        user.set_password(user_data['password'])
        
        self.db.session.add(user)
        self.db.session.commit()
        
        self._created_objects.append(('user', user.id))
        return user
    
    def create_admin_user(self, **overrides) -> Any:
        """Create an admin user in the database"""
        from app.models import User
        
        admin_data = self.factory.create_test_admin_user(**overrides)
        admin = User(
            username=admin_data['username'],
            email=admin_data['email'],
            is_admin=True,
            is_verified=True,
            is_active=True,
            bio=admin_data.get('bio'),
            location=admin_data.get('location'),
            website=admin_data.get('website'),
            created_at=admin_data.get('created_at', datetime.utcnow())
        )
        admin.set_password(admin_data['password'])
        
        self.db.session.add(admin)
        self.db.session.commit()
        
        self._created_objects.append(('user', admin.id))
        return admin
    
    def create_post(self, user_id: int, category_id: Optional[int] = None, **overrides) -> Any:
        """Create a post in the database"""
        from app.models import Post
        
        post_data = self.factory.create_test_post(user_id, category_id, **overrides)
        post = Post(
            title=post_data['title'],
            content=post_data['content'],
            user_id=post_data['user_id'],
            category_id=post_data.get('category_id'),
            created_at=post_data.get('created_at', datetime.utcnow())
        )
        
        self.db.session.add(post)
        self.db.session.commit()
        
        self._created_objects.append(('post', post.id))
        return post
    
    def create_comment(self, user_id: int, post_id: int, **overrides) -> Any:
        """Create a comment in the database"""
        from app.models import Comment
        
        comment_data = self.factory.create_test_comment(user_id, post_id, **overrides)
        comment = Comment(
            content=comment_data['content'],
            user_id=comment_data['user_id'],
            post_id=comment_data['post_id'],
            created_at=comment_data.get('created_at', datetime.utcnow())
        )
        
        self.db.session.add(comment)
        self.db.session.commit()
        
        self._created_objects.append(('comment', comment.id))
        return comment
    
    def create_category(self, **overrides) -> Any:
        """Create a category in the database"""
        from app.models import Category
        
        category_data = self.factory.create_test_category(**overrides)
        category = Category(
            name=category_data['name'],
            description=category_data['description'],
            created_at=category_data.get('created_at', datetime.utcnow())
        )
        
        self.db.session.add(category)
        self.db.session.commit()
        
        self._created_objects.append(('category', category.id))
        return category
    
    def create_badge(self, **overrides) -> Any:
        """Create a badge in the database"""
        from app.models import Badge
        
        badge_data = self.factory.create_test_badge(**overrides)
        badge = Badge(
            name=badge_data['name'],
            description=badge_data['description'],
            icon=badge_data.get('icon'),
            created_at=badge_data.get('created_at', datetime.utcnow())
        )
        
        self.db.session.add(badge)
        self.db.session.commit()
        
        self._created_objects.append(('badge', badge.id))
        return badge
    
    def create_message(self, sender_id: int, recipient_id: int, **overrides) -> Any:
        """Create a message in the database"""
        from app.models import Message
        
        message_data = self.factory.create_test_message(sender_id, recipient_id, **overrides)
        # Note: This would need to be adapted based on actual Message model
        # For now, return a placeholder
        return message_data
    
    def create_notification(self, user_id: int, **overrides) -> Any:
        """Create a notification in the database"""
        from app.models import Notification
        
        notification_data = self.factory.create_test_notification(user_id, **overrides)
        # Note: This would need to be adapted based on actual Notification model
        # For now, return a placeholder
        return notification_data
    
    def cleanup(self):
        """Clean up all created objects"""
        try:
            # Clean up in reverse order to handle foreign key constraints
            for object_type, object_id in reversed(self._created_objects):
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
                    # Log error but continue cleanup
                    print(f"Error cleaning up {object_type} {object_id}: {e}")
                    self.db.session.rollback()
            
            self._created_objects.clear()
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            self.db.session.rollback()

class TestDataSet:
    """Predefined test data sets"""
    
    @staticmethod
    def get_basic_user_set() -> List[Dict[str, Any]]:
        """Get a basic set of test users"""
        return [
            {
                'username': 'basicuser1',
                'email': 'basicuser1@example.com',
                'password': 'testpass123',
                'is_admin': False,
                'is_verified': True
            },
            {
                'username': 'basicuser2',
                'email': 'basicuser2@example.com',
                'password': 'testpass123',
                'is_admin': False,
                'is_verified': True
            }
        ]
    
    @staticmethod
    def get_admin_user_set() -> List[Dict[str, Any]]:
        """Get a set of admin users"""
        return [
            {
                'username': 'admin1',
                'email': 'admin1@example.com',
                'password': 'adminpass123',
                'is_admin': True,
                'is_verified': True
            },
            {
                'username': 'admin2',
                'email': 'admin2@example.com',
                'password': 'adminpass123',
                'is_admin': True,
                'is_verified': True
            }
        ]
    
    @staticmethod
    def get_forum_post_set() -> List[Dict[str, Any]]:
        """Get a set of forum posts"""
        return [
            {
                'title': 'Welcome to the Forum',
                'content': 'This is a welcome post for all new users.',
                'is_published': True
            },
            {
                'title': 'Forum Rules',
                'content': 'Please read and follow the forum rules.',
                'is_published': True
            },
            {
                'title': 'How to Use This Forum',
                'content': 'A guide on how to use this forum effectively.',
                'is_published': True
            }
        ]
    
    @staticmethod
    def get_test_categories() -> List[Dict[str, Any]]:
        """Get a set of test categories"""
        return [
            {
                'name': 'General Discussion',
                'description': 'General forum discussions'
            },
            {
                'name': 'Technical Support',
                'description': 'Get help with technical issues'
            },
            {
                'name': 'Feature Requests',
                'description': 'Suggest new features and improvements'
            }
        ]
