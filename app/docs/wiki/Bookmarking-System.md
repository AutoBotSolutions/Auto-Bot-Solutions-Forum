# Bookmarking System

## Overview

Users can bookmark posts for quick access. Bookmarks are private to each user with a unique constraint preventing duplicates.

## Components

### Bookmark Model
```python
class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)
```

## Features

- Toggle bookmark on/off
- Unique per user-post pair
- View all bookmarks
- Sorted by bookmark date
- Rate limiting (future)

## Bookmark UI

- Bookmark button on posts
- Star icon
- Navbar link
- Unread count (future)
- Badge indicator
