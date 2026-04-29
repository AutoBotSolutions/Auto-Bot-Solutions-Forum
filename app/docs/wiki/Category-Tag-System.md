# Category/Tag System

## Overview

Categories organize posts into logical groups with custom colors. Users can filter posts by category.

## Components

### Category Model
```python
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#00f5ff')
```

## Features

- Custom category names
- Category descriptions
- Custom colors (hex)
- Admin management
- Category filtering on forum index
- Posts can have one category

## Category Filter UI

- Horizontal filter bar
- Color-coded buttons
- Active state styling
- Hover effects
- "All Posts" option

## Admin Management

- Create categories
- Delete categories
- View category stats
- Color picker input
