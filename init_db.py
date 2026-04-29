#!/usr/bin/env python3
"""
Database initialization script.
Run this script to create the database tables and initial admin user.
"""
import os
import sys
from app import create_app, db
from app.models import User, Repository, Category, Badge
from getpass import getpass

def create_admin_user():
    """Create an admin user interactively"""
    print("\n=== Creating Admin User ===")
    username = input("Enter admin username: ")
    email = input("Enter admin email: ")
    password = getpass("Enter admin password: ")
    password_confirm = getpass("Confirm admin password: ")
    
    if password != password_confirm:
        print("Passwords do not match!")
        return False
    
    if len(password) < 8:
        print("Password must be at least 8 characters!")
        return False
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        print(f"User '{username}' already exists!")
        return False
    
    if User.query.filter_by(email=email).first():
        print(f"Email '{email}' already registered!")
        return False
    
    # Create admin user
    admin = User(username=username, email=email, is_admin=True)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    
    print(f"\n✓ Admin user '{username}' created successfully!")
    return True

def sync_github_repos():
    """Sync repositories from GitHub"""
    print("\n=== Syncing GitHub Repositories ===")
    try:
        import requests
        from config import Config
        
        org = Config.GITHUB_ORG
        url = f'https://api.github.com/orgs/{org}/repos'
        headers = {}
        if Config.GITHUB_TOKEN:
            headers['Authorization'] = f'token {Config.GITHUB_TOKEN}'
        
        print(f"Fetching repositories from {org}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        repos_data = response.json()
        
        synced_count = 0
        for repo_data in repos_data:
            existing = Repository.query.filter_by(github_url=repo_data['html_url']).first()
            if not existing:
                repo = Repository(
                    name=repo_data['name'],
                    description=repo_data.get('description', ''),
                    github_url=repo_data['html_url'],
                    stars=repo_data.get('stargazers_count', 0),
                    language=repo_data.get('language')
                )
                db.session.add(repo)
                synced_count += 1
            else:
                existing.stars = repo_data.get('stargazers_count', 0)
                existing.language = repo_data.get('language')
        
        db.session.commit()
        print(f"✓ Synced {synced_count} new repositories!")
        return True
    except Exception as e:
        print(f"✗ Error syncing repositories: {e}")
        return False

def create_initial_categories():
    """Create initial categories"""
    print("Creating initial categories...")
    categories = [
        {'name': 'General', 'description': 'General discussions', 'color': '#00f5ff'},
        {'name': 'Development', 'description': 'Development topics', 'color': '#ff00ff'},
        {'name': 'Bugs', 'description': 'Bug reports', 'color': '#ff0044'},
        {'name': 'Feature Requests', 'description': 'Feature suggestions', 'color': '#00ff88'},
        {'name': 'Help', 'description': 'Help and support', 'color': '#ffaa00'},
    ]
    
    for cat_data in categories:
        if not Category.query.filter_by(name=cat_data['name']).first():
            category = Category(**cat_data)
            db.session.add(category)
    
    db.session.commit()
    print("✓ Initial categories created!")

def create_initial_badges():
    """Create initial badges"""
    print("Creating initial badges...")
    badges = [
        {'name': 'First Post', 'description': 'Created your first post', 'icon': '🎯', 'color': '#ff00ff'},
        {'name': 'Active Contributor', 'description': 'Posted 10 times', 'icon': '⭐', 'color': '#ffaa00'},
        {'name': 'Helpful', 'description': 'Received 10 upvotes', 'icon': '👍', 'color': '#00ff88'},
        {'name': 'Veteran', 'description': 'Member for 1 year', 'icon': '🏆', 'color': '#00f5ff'},
        {'name': 'Moderator', 'description': 'Forum moderator', 'icon': '🛡️', 'color': '#ff0044'},
    ]
    
    for badge_data in badges:
        if not Badge.query.filter_by(name=badge_data['name']).first():
            badge = Badge(**badge_data)
            db.session.add(badge)
    
    db.session.commit()
    print("✓ Initial badges created!")

def main():
    """Main initialization function"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created!")
        
        # Create initial categories
        create_initial_categories()
        
        # Create initial badges
        create_initial_badges()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Creating default admin user...")
            admin = User(username='admin', email='autobotsolution@gmail.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin user created (username: admin, password: admin123)")
        
        print("\n=== Initialization Complete ===")

if __name__ == '__main__':
    main()
