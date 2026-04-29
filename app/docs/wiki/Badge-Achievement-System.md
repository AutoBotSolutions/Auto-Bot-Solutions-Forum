# Badge/Achievement System

## Overview

Badges and achievements recognize user contributions and milestones. Admins can create badges and assign them to users.

## Components

### Badge Model
```python
class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(32), default='★')
    color = db.Column(db.String(7), default='#ff00ff')
```

### User-Badges Association
- Many-to-many relationship
- Users can have multiple badges
- Badges can be assigned to multiple users

## Features

- Custom badge icons (emoji)
- Custom badge colors
- Badge descriptions
- Admin management
- Profile display
- Admin assignment/removal

## Badge Display

- Shown on user profiles
- Icon and name
- Color-coded
- Hover effects
- Sci-fi themed styling
