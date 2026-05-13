"""
Test configuration and fixtures for the Auto Bot Solutions Forum
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from flask import Flask
from app import create_app, db
from app.models import User
from app.admin.roles.models import Role, Permission
from app.user.social.models import UserFollow, UserFriend, SocialActivity, UserGroup, GroupMember
from app.user.analytics.models import UserBehavior, UserEngagement, UserPerformance, UserSegment
from app.admin.roles.models import UserRole, RoleAssignment, RoleHierarchy, RoleAnalytics


@pytest.fixture
def app():
    """Create and configure a test app."""
    # Create a temporary directory for the test database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test.db')
    
    # Set test environment variables
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['TESTING'] = 'True'
    os.environ['WTF_CSRF_ENABLED'] = 'False'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    # Create the app
    app = create_app()
    
    # Configure for testing
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # Clean up
    os.unlink(db_path)
    os.rmdir(temp_dir)


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """Create a database session for testing."""
    with app.app_context():
        yield db


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash='hashed_password',
        is_active=True,
        is_verified=True
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def sample_admin_user(db_session):
    """Create a sample admin user for testing."""
    admin_user = User(
        username='admin',
        email='admin@example.com',
        password_hash='hashed_password',
        is_active=True,
        is_verified=True,
        is_admin=True
    )
    db_session.session.add(admin_user)
    db_session.session.commit()
    return admin_user


@pytest.fixture
def sample_role(db_session):
    """Create a sample role for testing."""
    role = Role(
        name='test_role',
        display_name='Test Role',
        description='A test role',
        level=10,
        is_active=True
    )
    db_session.session.add(role)
    db_session.session.commit()
    return role


@pytest.fixture
def sample_permission(db_session):
    """Create a sample permission for testing."""
    permission = Permission(
        name='test_permission',
        display_name='Test Permission',
        description='A test permission',
        category='test',
        resource='test',
        action='test'
    )
    db_session.session.add(permission)
    db_session.session.commit()
    return permission


@pytest.fixture
def authenticated_client(client, sample_user):
    """Create an authenticated test client."""
    with client.session_transaction() as sess:
        sess['_user_id'] = sample_user.id
        sess['_fresh'] = True
    return client


@pytest.fixture
def admin_client(client, sample_admin_user):
    """Create an admin authenticated test client."""
    with client.session_transaction() as sess:
        sess['_user_id'] = sample_admin_user.id
        sess['_fresh'] = True
    return client


@pytest.fixture
def sample_user_follow(db_session, sample_user, sample_admin_user):
    """Create a sample user follow relationship."""
    follow = UserFollow(
        follower_id=sample_user.id,
        following_id=sample_admin_user.id,
        is_mutual=False
    )
    db_session.session.add(follow)
    db_session.session.commit()
    return follow


@pytest.fixture
def sample_user_friend(db_session, sample_user, sample_admin_user):
    """Create a sample user friend relationship."""
    friend = UserFriend(
        user1_id=sample_user.id,
        user2_id=sample_admin_user.id,
        status='accepted',
        requested_by_id=sample_user.id
    )
    db_session.session.add(friend)
    db_session.session.commit()
    return friend


@pytest.fixture
def sample_social_activity(db_session, sample_user):
    """Create a sample social activity."""
    activity = SocialActivity(
        user_id=sample_user.id,
        activity_type='post',
        action='created',
        target_type='post',
        target_id=1,
        description='Test activity',
        is_public=True
    )
    db_session.session.add(activity)
    db_session.session.commit()
    return activity


@pytest.fixture
def sample_user_group(db_session, sample_user):
    """Create a sample user group."""
    group = UserGroup(
        name='Test Group',
        description='A test group',
        creator_id=sample_user.id,
        is_private=False
    )
    db_session.session.add(group)
    db_session.session.commit()
    return group


@pytest.fixture
def sample_user_behavior(db_session, sample_user):
    """Create a sample user behavior."""
    behavior = UserBehavior(
        user_id=sample_user.id,
        behavior_type='login',
        action='logged_in',
        session_id='test_session',
        ip_address='127.0.0.1',
        user_agent='Test Agent'
    )
    db_session.session.add(behavior)
    db_session.session.commit()
    return behavior


@pytest.fixture
def sample_user_engagement(db_session, sample_user):
    """Create a sample user engagement."""
    engagement = UserEngagement(
        user_id=sample_user.id,
        date=datetime.utcnow().date(),
        total_actions=10,
        login_count=1,
        post_count=2,
        comment_count=3,
        like_count=4,
        share_count=1,
        engagement_score=25.5
    )
    db_session.session.add(engagement)
    db_session.session.commit()
    return engagement


@pytest.fixture
def sample_user_performance(db_session, sample_user):
    """Create a sample user performance."""
    performance = UserPerformance(
        user_id=sample_user.id,
        metric_type='content',
        metric_name='post_count',
        metric_value=10.0,
        previous_value=8.0,
        change_percentage=25.0,
        period='weekly',
        period_start=datetime.utcnow().date() - timedelta(days=7),
        period_end=datetime.utcnow().date()
    )
    db_session.session.add(performance)
    db_session.session.commit()
    return performance


@pytest.fixture
def sample_user_segment(db_session):
    """Create a sample user segment."""
    segment = UserSegment(
        name='Test Segment',
        description='A test segment',
        segment_type='activity',
        criteria={'min_posts': 5},
        user_count=0,
        is_active=True
    )
    db_session.session.add(segment)
    db_session.session.commit()
    return segment


@pytest.fixture
def sample_user_role(db_session, sample_user, sample_role):
    """Create a sample user role assignment."""
    user_role = UserRole(
        user_id=sample_user.id,
        role_id=sample_role.id,
        assigned_by_id=sample_user.id
    )
    db_session.session.add(user_role)
    db_session.session.commit()
    return user_role


@pytest.fixture
def sample_role_assignment(db_session, sample_user, sample_role):
    """Create a sample role assignment workflow."""
    assignment = RoleAssignment(
        user_id=sample_user.id,
        role_id=sample_role.id,
        workflow_type='request',
        status='pending',
        requested_by_id=sample_user.id
    )
    db_session.session.add(assignment)
    db_session.session.commit()
    return assignment


@pytest.fixture
def sample_role_hierarchy(db_session, sample_role):
    """Create a sample role hierarchy."""
    hierarchy = RoleHierarchy(
        parent_role_id=sample_role.id,
        child_role_id=sample_role.id + 1,
        relationship_type='inherits'
    )
    db_session.session.add(hierarchy)
    db_session.session.commit()
    return hierarchy


@pytest.fixture
def sample_role_analytics(db_session, sample_role):
    """Create a sample role analytics."""
    analytics = RoleAnalytics(
        role_id=sample_role.id,
        date=datetime.utcnow().date(),
        user_count=5,
        new_assignments=2,
        removals=1,
        requests=3,
        approvals=2,
        rejections=1
    )
    db_session.session.add(analytics)
    db_session.session.commit()
    return analytics


# Test utilities
def create_test_user(username, email, is_admin=False):
    """Create a test user."""
    user = User(
        username=username,
        email=email,
        password_hash='hashed_password',
        is_active=True,
        is_verified=True,
        is_admin=is_admin
    )
    db.session.add(user)
    db.session.commit()
    return user


def create_test_role(name, display_name, level=0):
    """Create a test role."""
    role = Role(
        name=name,
        display_name=display_name,
        level=level,
        is_active=True
    )
    db.session.add(role)
    db.session.commit()
    return role


def create_test_permission(name, display_name, category, resource, action):
    """Create a test permission."""
    permission = Permission(
        name=name,
        display_name=display_name,
        category=category,
        resource=resource,
        action=action
    )
    db.session.add(permission)
    db.session.commit()
    return permission
