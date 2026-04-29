# Migration Guide

## Overview

Guide for migrating from other forum platforms to the AutoBot Solutions Forum.

## Supported Migrations

Currently, there is no automated migration tool. Manual migration is required.

## Manual Migration Process

### Step 1: Export Data from Source Forum

**From Discourse**
- Export users, posts, comments
- Use Discourse data export feature
- Export in JSON or CSV format

**From phpBB**
- Export via database dump
- Use phpBB backup tools
- Export users, posts, forums

**From Vanilla Forums**
- Export via admin panel
- Use export functionality
- Export in supported format

### Step 2: Transform Data

**User Mapping**
- Map usernames to new system
- Generate new password hashes
- Create email verification tokens
- Preserve join dates

**Post Mapping**
- Map posts to new format
- Convert formatting (BBCode to Markdown)
- Preserve timestamps
- Map categories/forums

**Comment Mapping**
- Map comments to new system
- Convert formatting
- Preserve nesting (if applicable)
- Map to correct posts

### Step 3: Import Data

**Database Import**
- Write custom import script
- Use SQLAlchemy ORM
- Handle relationships
- Validate data integrity

**Example Import Script**
```python
from app import db, create_app
from app.models import User, Post, Comment

app = create_app()
with app.app_context():
    # Import users
    for user_data in exported_users:
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password_hash=hash_password(user_data['password']),
            created_at=user_data['created_at']
        )
        db.session.add(user)
    
    # Import posts
    for post_data in exported_posts:
        post = Post(
            title=post_data['title'],
            content=convert_to_markdown(post_data['content']),
            user_id=user_map[post_data['user_id']],
            created_at=post_data['created_at']
        )
        db.session.add(post)
    
    db.session.commit()
```

### Step 4: Verify Migration

**Data Verification**
- Check user counts match
- Verify post counts
- Test user logins
- Verify post display
- Check comment threading

**Functional Testing**
- Test posting
- Test commenting
- Test voting
- Test search
- Test user profiles

## Format Conversion

### BBCode to Markdown

**Common BBCode Tags**
- `[b]text[/b]` → `**text**`
- `[i]text[/i]` → `*text*`
- `[url]link[/url]` → `[link](url)`
- `[code]code[/code]` → ```code```
- `[quote]text[/quote]` → `> text`

**Conversion Script**
```python
import re

def bbcode_to_markdown(text):
    # Bold
    text = re.sub(r'\[b\](.*?)\[/b\]', r'**\1**', text)
    # Italic
    text = re.sub(r'\[i\](.*?)\[/i\]', r'*\1*', text)
    # Code
    text = re.sub(r'\[code\](.*?)\[/code\]', r'```\1```', text)
    # Quote
    text = re.sub(r'\[quote\](.*?)\[/quote\]', r'> \1', text)
    return text
```

## Considerations

### Password Migration
- Cannot migrate password hashes
- Users must reset passwords
- Send password reset emails
- Provide migration notice

### Usernames
- Check for duplicates
- Add suffix if needed
- Notify users of changes
- Allow username changes

### Content Formatting
- Convert all formatting
- Test converted content
- Manual review if needed
- Preserve original if possible

### Attachments
- Migrate file attachments
- Update file paths
- Verify file accessibility
- Handle missing files

## Rollback Plan

### Backup Current Data
- Export current database
- Backup user data
- Backup content data
- Store securely

### Rollback Process
- Stop application
- Restore database backup
- Verify data integrity
- Restart application

## Post-Migration Tasks

### User Notifications
- Email users about migration
- Provide new login instructions
- Explain password reset process
- Provide support contact

### Content Review
- Review migrated content
- Fix formatting issues
- Update categories
- Verify links

### Performance Monitoring
- Monitor database performance
- Check response times
- Monitor error rates
- Optimize as needed

## Best Practices

### Before Migration
- Test migration on staging
- Backup all data
- Plan for downtime
- Notify users in advance

### During Migration
- Monitor progress
- Log all actions
- Handle errors gracefully
- Verify data integrity

### After Migration
- Monitor for issues
- Provide support
- Fix formatting issues
- Optimize performance

## Getting Help

- Check [Support.md](../SUPPORT.md)
- Review [Database-System.md](Database-System.md)
- Contact support@autobotsolutions.com
- Hire migration specialist

## Custom Migration Services

For complex migrations or large forums, consider:
- Professional migration services
- Custom script development
- Data migration consulting
- Post-migration support
