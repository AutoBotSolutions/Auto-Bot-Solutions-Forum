#!/usr/bin/env python3
"""
Test User Creation Script for Auto Bot Solutions Forum

This script creates test users to demonstrate the user management functionality
in the admin panel. It's useful when you need to test user management features
but only have the admin user in the database.

Usage:
    python create_test_users.py

Requirements:
    - Flask app context must be available
    - Run from project root directory
    - Virtual environment activated

Test Users Created:
    - testuser1 (test1@example.com)
    - testuser2 (test2@example.com)
    - moderator1 (mod@example.com)
"""

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import sys

def create_test_users():
    """Create test users for demonstrating user management functionality."""
    
    app = create_app()
    app.app_context().push()
    
    # Test users data
    test_users = [
        {
            'username': 'testuser1',
            'email': 'test1@example.com',
            'password': 'password123',
            'is_admin': False
        },
        {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'password123',
            'is_admin': False
        },
        {
            'username': 'moderator1',
            'email': 'mod@example.com',
            'password': 'password123',
            'is_admin': False
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    print("Creating test users...")
    print("=" * 50)
    
    for user_data in test_users:
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(username=user_data['username']).first()
            
            if existing_user:
                print(f"⚠️  User '{user_data['username']}' already exists - skipping")
                skipped_count += 1
                continue
            
            # Create new user
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password']),
                is_admin=user_data['is_admin']
            )
            
            db.session.add(user)
            db.session.commit()
            
            print(f"✅ Created user: {user_data['username']} ({user_data['email']})")
            created_count += 1
            
        except Exception as e:
            print(f"❌ Error creating user '{user_data['username']}': {str(e)}")
            db.session.rollback()
    
    print("=" * 50)
    print(f"Summary: {created_count} users created, {skipped_count} users skipped")
    
    if created_count > 0:
        print("\n🎉 Test users created successfully!")
        print("\nYou can now:")
        print("1. Login as admin and visit /admin/users/")
        print("2. See the user management options (Toggle Admin, Delete)")
        print("3. Test user management functionality")
        print("\nTest User Credentials:")
        for user_data in test_users:
            print(f"  - {user_data['username']}: {user_data['password']}")
    else:
        print("\nℹ️  No new users created. All test users already exist.")
    
    return created_count, skipped_count

def list_users():
    """List all users in the database."""
    app = create_app()
    app.app_context().push()
    
    users = User.query.order_by(User.created_at.desc()).all()
    
    print("\nCurrent Users:")
    print("=" * 50)
    
    for user in users:
        admin_status = "ADMIN" if user.is_admin else "USER"
        print(f"{user.username:<15} {user.email:<25} {admin_status}")
    
    print(f"\nTotal users: {len(users)}")
    return len(users)

def main():
    """Main function to handle command line arguments."""
    
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        list_users()
        return
    
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        return
    
    try:
        create_test_users()
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
