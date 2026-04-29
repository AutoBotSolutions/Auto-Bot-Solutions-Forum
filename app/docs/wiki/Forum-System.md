# Forum System

## Overview

The forum system is the core functionality of the application, handling posts, comments, voting, categories, and search. It provides the main discussion platform for users to interact with content.

## Components

### Models

**Post Model** (`app/models.py`)
```python
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    repository_id = db.Column(db.Integer, db.ForeignKey('repository.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    attachment = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
```

**Comment Model** (`app/models.py`)
```python
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
```

### Forms

**PostForm** (`app/forum/forms.py`)
- Title field (min 5, max 256 characters)
- Content field (min 10 characters)
- Repository selection (optional)
- Category selection (optional)
- File attachment (optional)
- Submit button

**CommentForm** (`app/forum/forms.py`)
- Content field
- Submit button

### Routes

**Index Route** (`/forum/`)
- Displays all posts or filtered by category
- Supports category filtering via query parameter
- Shows category filter UI
- Paginated display

**Create Post Route** (`/forum/create`)
- Method: GET, POST
- Requires authentication
- Rate limit: 5 requests per hour
- Handles file uploads
- Creates post with category and repository
- Generates notification for post creation

**Post Detail Route** (`/forum/post/<post_id>`)
- Displays single post with comments
- Shows vote counts
- Displays comment form
- Shows bookmark button

**Add Comment Route** (`/forum/post/<post_id>/comment`)
- Method: POST
- Requires authentication
- Rate limit: 20 requests per hour
- Creates comment on post
- Generates notification for post author

**Vote on Post Route** (`/forum/vote/post/<post_id>/<value>`)
- Requires authentication
- Rate limit: 30 requests per minute
- Value: 1 (upvote) or -1 (downvote)
- Allows vote changing or removal
- Updates post vote counts

**Vote on Comment Route** (`/forum/vote/comment/<comment_id>/<value>`)
- Requires authentication
- Rate limit: 30 requests per minute
- Value: 1 (upvote) or -1 (downvote)
- Allows vote changing or removal
- Updates comment vote counts

**Toggle Bookmark Route** (`/forum/bookmark/<post_id>`)
- Requires authentication
- Adds or removes bookmark
- Unique constraint on user-post pairs
- Flash message feedback

**Bookmarks Route** (`/forum/bookmarks`)
- Requires authentication
- Displays user's bookmarked posts
- Shows post metadata
- Sorted by bookmark date

**Search Route** (`/forum/search`)
- Searches posts by title and content
- Searches comments by content
- Case-insensitive search
- Shows matching results

**Repository Posts Route** (`/forum/repository/<repo_id>`)
- Displays posts for specific repository
- Shows repository metadata
- Repository-linked discussions

## Category System

### Category Model
```python
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#00f5ff')
    posts = db.relationship('Post', backref='category', lazy='dynamic')
```

### Features
- Custom category colors
- Category descriptions
- Category filtering on forum index
- Admin management of categories
- Posts can have one category

## Voting System

### Vote Model
```python
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    value = db.Column(db.Integer, nullable=False)  # 1 or -1
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Features
- Users can upvote or downvote
- One vote per user per item
- Can change vote by voting again
- Can remove vote by voting same value
- Vote counts updated in real-time
- Rate limited to prevent abuse

## Search Functionality

### Implementation
- Uses SQLAlchemy `ilike` for case-insensitive search
- Searches post titles and content
- Searches comment content
- Returns matching posts and comments separately
- Shows search query in UI

### Features
- Case-insensitive matching
- Partial string matching
- Shows number of results
- Links to original content

## File Upload System

### Supported File Types
- Images: PNG, JPG, JPEG, GIF
- Documents: PDF, TXT, MD

### Upload Process
1. User selects file in post form
2. File type validated
3. Filename sanitized with `secure_filename()`
4. Timestamp added for uniqueness
5. File saved to `app/static/uploads/`
6. Filename stored in database
7. File displayed in post with download link

### Security
- File type whitelist
- Filename sanitization
- Unique filenames prevent overwrites
- Files served from static folder
- No size limit (should be added for production)

## Markdown Processing

### Implementation
- Uses python-markdown library
- Extensions: fenced_code, codehilite, tables, nl2br
- HTML sanitization with bleach
- Custom CSS for code blocks and tables

### Supported Markdown
- Headers (H1-H6)
- Bold and italic
- Code blocks with syntax highlighting
- Tables
- Lists (ordered and unordered)
- Blockquotes
- Links
- Horizontal rules
- Line breaks

## Bookmarking System

### Bookmark Model
```python
class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_bookmark'),)
```

### Features
- Toggle bookmark on/off
- Unique constraint prevents duplicates
- View all bookmarks
- Sorted by bookmark date
- Rate limited

## Rate Limiting

### Current Limits
- Create post: 5 requests per hour
- Add comment: 20 requests per hour
- Vote: 30 requests per minute
- Search: No limit
- Bookmark: No limit

### Implementation
- Flask-Limiter integration
- IP-based rate limiting
- Configurable per endpoint
- Redis-backed (future)

## Notification Integration

### Post Creation
- No notification on post creation (self-action)

### Comment Addition
- Notification sent to post author
- Notification includes comment author name
- Notification links to post
- Not sent if commenter is post author

## Templates

### Forum Index (`forum/index.html`)
- Category filter UI
- Post list with metadata
- Vote buttons
- Author links to profiles
- Repository links

### Post Detail (`forum/post.html`)
- Post content with Markdown
- Attachment display
- Vote buttons
- Bookmark button
- Comment section
- Comment form (authenticated users)

### Create Post (`forum/create.html`)
- Post form with all fields
- File upload field
- Repository and category selection
- Form validation errors

### Bookmarks (`forum/bookmarks.html`)
- List of bookmarked posts
- Post metadata
- Author and date information
- Vote counts

### Search Results (`forum/search.html`)
- Matching posts section
- Matching comments section
- Result counts
- Links to original content

## Future Enhancements

- Post editing
- Post pinning/sticky
- Post reporting
- Comment editing
- Nested comments (replies)
- Rich text editor
- Image preview in posts
- Post drafts
- Scheduled posts
- Post analytics
- Related posts
- Advanced search filters
- Full-text search with Elasticsearch
