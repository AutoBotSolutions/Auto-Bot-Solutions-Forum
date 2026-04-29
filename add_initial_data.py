#!/usr/bin/env python3
from app import create_app, db
from app.models import Category, Badge

app = create_app()

with app.app_context():
    # Create categories
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
    
    # Create badges
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
    print(f"Total categories: {Category.query.count()}")
    print(f"Total badges: {Badge.query.count()}")
