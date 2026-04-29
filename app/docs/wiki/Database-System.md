# Database System

## Overview

The database system uses PostgreSQL as the primary database with SQLAlchemy ORM for database operations. It includes migrations via Flask-Migrate and supports all forum data including users, posts, comments, votes, and more.

## Database Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- Format: `postgresql://user:password@host:port/database`
- Example: `postgresql://forumuser:password@localhost:5432/forumdb`

### SQLAlchemy Configuration
```python
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
```

## Database Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(256),
    reset_token VARCHAR(256),
    reset_token_expiration TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

#### Repositories Table
```sql
CREATE TABLE repositories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    github_url VARCHAR(256) UNIQUE NOT NULL,
    stars INTEGER DEFAULT 0,
    language VARCHAR(64),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_repositories_github_url ON repositories(github_url);
```

#### Categories Table
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#00f5ff'
);
```

#### Posts Table
```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(256) NOT NULL,
    content TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE SET NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    attachment VARCHAR(256),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0
);

CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX idx_posts_category_id ON posts(category_id);
```

#### Comments Table
```sql
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0
);

CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_created_at ON comments(created_at DESC);
```

#### Votes Table
```sql
CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    value INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (value IN (1, -1))
);

CREATE UNIQUE INDEX idx_votes_user_post ON votes(user_id, post_id) WHERE post_id IS NOT NULL;
CREATE UNIQUE INDEX idx_votes_user_comment ON votes(user_id, comment_id) WHERE comment_id IS NOT NULL;
```

#### Notifications Table
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    link VARCHAR(256),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
```

#### Messages Table
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_receiver_id ON messages(receiver_id);
CREATE INDEX idx_messages_is_read ON messages(is_read);
```

#### Bookmarks Table
```sql
CREATE TABLE bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, post_id)
);

CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
```

#### Badges Table
```sql
CREATE TABLE badges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(32) DEFAULT '★',
    color VARCHAR(7) DEFAULT '#ff00ff'
);
```

#### User_Badges Association Table
```sql
CREATE TABLE user_badges (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, badge_id)
);
```

## Relationships

### One-to-Many Relationships
- User → Posts
- User → Comments
- User → Notifications
- User → Sent Messages
- User → Received Messages
- User → Bookmarks
- Repository → Posts
- Category → Posts
- Post → Comments

### Many-to-Many Relationships
- User ↔ Badges (via user_badges)

### One-to-One Relationships
- None currently

## Migrations

### Flask-Migrate
- Database schema versioning
- Automatic migration generation
- Upgrade/downgrade support
- Migration history tracking

### Migration Commands
```bash
# Generate migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade

# View migration history
flask db history
```

### Initial Migration
- Creates all tables
- Creates indexes
- Creates constraints
- Sets up relationships

## Database Initialization

### init_db.py Script
```python
# Creates admin user
# Creates default categories
# Initializes database
# Run after first migration
```

### Running Initialization
```bash
python init_db.py
```

## Database Operations

### Query Examples

**Get User by Username**
```python
user = User.query.filter_by(username='username').first()
```

**Get Posts with Category**
```python
posts = Post.query.filter_by(category_id=category_id).all()
```

**Get Unread Notifications**
```python
notifications = Notification.query.filter_by(user_id=user.id, is_read=False).all()
```

**Search Posts**
```python
posts = Post.query.filter(
    (Post.title.ilike(f'%{query}%')) | 
    (Post.content.ilike(f'%{query}%'))
).all()
```

## Performance Optimization

### Indexes
- Username index
- Email index
- User foreign key indexes
- Created_at indexes for sorting
- Category index
- Unique constraints for votes and bookmarks

### Query Optimization
- Lazy loading for relationships
- Eager loading when needed
- Query filtering
- Pagination (future)
- Query result caching (future)

### Connection Pooling
- SQLAlchemy connection pooling
- Configurable pool size
- Automatic connection management
- Connection reuse

## Database Backup

### Backup Strategies
- PostgreSQL pg_dump
- Scheduled backups
- Off-site storage
- Point-in-time recovery

### Backup Commands
```bash
# Full backup
pg_dump -U username -d forumdb > backup.sql

# Restore
psql -U username -d forumdb < backup.sql
```

## Database Security

### Access Control
- Database user with limited privileges
- No direct web access to database
- Connection string in environment variables
- SSL/TLS for database connections

### Data Protection
- Passwords hashed before storage
- No plain text passwords
- Sensitive data in environment variables
- Regular security audits

## Database Maintenance

### Regular Tasks
- Vacuum and analyze tables
- Reindex indexes
- Update statistics
- Monitor disk space
- Check for bloat

### Maintenance Commands
```bash
# Vacuum and analyze
VACUUM ANALYZE;

# Reindex
REINDEX DATABASE forumdb;

# Update statistics
ANALYZE;
```

## Database Monitoring

### Metrics to Monitor
- Connection pool usage
- Query performance
- Table sizes
- Index usage
- Disk space
- Slow queries

### Monitoring Tools
- PostgreSQL logs
- Query performance logs
- Connection pool logs
- External monitoring (future)

## Future Enhancements

### Database Features
- Read replicas for scaling
- Partitioning for large tables
- Full-text search (PostgreSQL)
- JSONB fields for flexible data
- Materialized views for common queries
- Database triggers for automation
- Stored procedures for complex operations

### Data Integrity
- Foreign key constraints
- Check constraints
- Unique constraints
- Not null constraints
- Data validation at database level

### Performance
- Connection pooling optimization
- Query result caching (Redis)
- Database connection monitoring
- Automatic failover
- Load balancing
