# Admin System

## Overview

The admin system provides administrative control over the forum, including user management, content moderation, repository management, category management, and badge management. It is accessible only to users with admin privileges.

## Components

### Admin Decorator

The `admin_required` decorator ensures only admin users can access admin routes:

```python
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function
```

### Forms

**CategoryForm** (`app/admin/forms.py`)
- Name field
- Description field
- Color field (hex)
- Submit button

**BadgeForm** (`app/admin/forms.py`)
- Name field
- Description field
- Icon field
- Color field (hex)
- Submit button

### Routes

**Dashboard Route** (`/admin/dashboard`)
- Requires admin privileges
- Displays system statistics
- Shows recent users (last 5)
- Shows recent posts (last 5)
- Navigation links to admin sections

**Users Route** (`/admin/users`)
- Requires admin privileges
- Lists all users
- Shows user metadata
- Actions:
  - Toggle admin status
  - Delete user
  - Add/remove badges

**Delete User Route** (`/admin/users/<user_id>/delete`)
- Requires admin privileges
- Deletes user account
- Cascades to related data
- Flash confirmation

**Toggle Admin Route** (`/admin/users/<user_id>/toggle_admin`)
- Requires admin privileges
- Toggles user admin status
- Flash confirmation

**Posts Route** (`/admin/posts`)
- Requires admin privileges
- Lists all posts
- Shows post metadata
- Actions:
  - View post
  - Delete post

**Delete Post Route** (`/admin/posts/<post_id>/delete`)
- Requires admin privileges
- Deletes post
- Cascades to comments and votes
- Flash confirmation

**Comments Route** (`/admin/comments`)
- Requires admin privileges
- Lists all comments
- Shows comment metadata
- Actions:
  - View comment
  - Delete comment

**Delete Comment Route** (`/admin/comments/<comment_id>/delete`)
- Requires admin privileges
- Deletes comment
- Cascades to votes
- Flash confirmation

**Repositories Route** (`/admin/repositories`)
- Requires admin privileges
- Lists all repositories
- Shows repository metadata
- Actions:
  - Sync repositories
  - Delete repository

**Delete Repository Route** (`/admin/repositories/<repo_id>/delete`)
- Requires admin privileges
- Deletes repository
- Cascades to related posts
- Flash confirmation

**Categories Route** (`/admin/categories`)
- Requires admin privileges
- Lists all categories
- Shows category metadata
- Actions:
  - Create category
  - Delete category
  - View posts in category

**Create Category Route** (`/admin/categories/create`)
- Requires admin privileges
- Method: GET, POST
- Creates new category
- Validates form input
- Flash confirmation

**Delete Category Route** (`/admin/categories/<category_id>/delete`)
- Requires admin privileges
- Deletes category
- Cascades to related posts
- Flash confirmation

**Badges Route** (`/admin/badges`)
- Requires admin privileges
- Lists all badges
- Shows badge metadata
- Actions:
  - Create badge
  - Delete badge
  - View badge users

**Create Badge Route** (`/admin/badges/create`)
- Requires admin privileges
- Method: GET, POST
- Creates new badge
- Validates form input
- Flash confirmation

**Delete Badge Route** (`/admin/badges/<badge_id>/delete`)
- Requires admin privileges
- Deletes badge
- Removes from all users
- Flash confirmation

**Add Badge to User Route** (`/admin/users/<user_id>/add_badge/<badge_id>`)
- Requires admin privileges
- Assigns badge to user
- Prevents duplicates
- Flash confirmation

**Remove Badge from User Route** (`/admin/users/<user_id>/remove_badge/<badge_id>`)
- Requires admin privileges
- Removes badge from user
- Flash confirmation

## Dashboard Statistics

The dashboard displays:
- Total users count
- Total posts count
- Total comments count
- Total repositories count
- Total categories count
- Total badges count
- Recent users (last 5)
- Recent posts (last 5)

## User Management

### Actions

**Toggle Admin**
- Promotes or demotes user to admin
- Changes `is_admin` flag
- Immediate effect on permissions

**Delete User**
- Deletes user account
- Cascades to:
  - User's posts
  - User's comments
  - User's votes
  - User's bookmarks
  - User's messages
  - User's notifications
  - User's badges

**Manage Badges**
- Add badge to user
- Remove badge from user
- View user's current badges

## Content Moderation

### Post Moderation

**Delete Post**
- Removes post from forum
- Deletes all comments on post
- Removes all votes on post
- Removes all bookmarks
- Removes from search index

### Comment Moderation

**Delete Comment**
- Removes comment
- Removes votes on comment
- Removes associated notifications

## Repository Management

### Actions

**Sync Repositories**
- Calls GitHub API
- Fetches repositories from organization
- Updates or creates repository records
- Updates metadata (stars, language)

**Delete Repository**
- Removes repository from database
- Cascades to repository-linked posts
- Posts become unlinked

## Category Management

### Actions

**Create Category**
- Sets category name
- Adds description
- Sets color (hex)
- Category immediately available

**Delete Category**
- Removes category
- Posts become uncategorized
- Category color removed

## Badge Management

### Actions

**Create Badge**
- Sets badge name
- Adds description
- Sets icon (emoji)
- Sets color (hex)
- Badge available for assignment

**Delete Badge**
- Removes badge
- Removes from all users
- Badge removed from profiles

**Assign Badge**
- Assigns badge to specific user
- Prevents duplicate assignments
- Badge visible on user profile

**Remove Badge**
- Removes badge from user
- Badge removed from profile
- Can be reassigned later

## Templates

### Dashboard (`admin/dashboard.html`)
- Statistics cards
- Recent users table
- Recent posts table
- Navigation links
- Action buttons

### Users (`admin/users.html`)
- User table with metadata
- Toggle admin button
- Delete button
- Badge management links

### Posts (`admin/posts.html`)
- Post table with metadata
- View button
- Delete button

### Comments (`admin/comments.html`)
- Comment table with metadata
- View button
- Delete button

### Repositories (`admin/repositories.html`)
- Repository table with metadata
- Sync button
- Delete button
- Posts count

### Categories (`admin/categories.html`)
- Category grid display
- Color-coded badges
- Delete button
- Posts count
- View posts link

### Create Category (`admin/create_category.html`)
- Category form
- Color picker input
- Submit button

### Badges (`admin/badges.html`)
- Badge grid display
- Icon and color
- Delete button
- Users count

### Create Badge (`admin/create_badge.html`)
- Badge form
- Icon input
- Color picker input
- Submit button

## Security Considerations

### Access Control
- All routes protected by `admin_required` decorator
- Checks authentication status
- Checks admin flag
- Redirects non-admins to home page

### CSRF Protection
- All forms include CSRF tokens
- Tokens validated on submission
- Prevents cross-site request forgery

### Rate Limiting
- Admin routes should have rate limiting (future enhancement)
- Prevents admin account takeover
- Limits brute force attempts

### Audit Trail
- Consider adding audit logging (future)
- Track admin actions
- Log who did what and when

## Best Practices

### For Admins
- Review reported content regularly
- Use badge system judiciously
- Be cautious with account deletions
- Keep admin credentials secure
- Enable 2FA when available
- Regular security audits

### For Developers
- Log all admin actions
- Implement audit trail
- Add confirmation dialogs
- Consider role-based permissions
- Add admin activity dashboard
- Implement admin session timeout

## Troubleshooting

### Access Denied
- **Problem**: "Access denied" error
  - Verify user has admin flag
  - Check authentication status
  - Ensure session is valid

### User Management Options Not Visible
- **Problem**: No management options visible on user management page
  - **Cause**: Only one admin user exists in database
  - **Solution**: Create test users to demonstrate functionality
  - **Note**: Template prevents self-management for security
  - **Fix**: Use test user creation script to add sample users

### Actions Not Working
- **Problem**: Delete/toggle not working
  - Check CSRF token
  - Verify database connection
  - Check for JavaScript errors

### Stats Not Updating
- **Problem**: Dashboard stats incorrect
  - Check database queries
  - Verify data integrity
  - Restart application

## Future Enhancements

- Role-based permissions (moderator, editor, etc.)
- Bulk actions (delete multiple items)
- Content queue for approval
- Spam detection and auto-moderation
- Admin activity logs
- Audit trail
- Scheduled content moderation
- IP banning
- Content flagging system
- Analytics dashboard
- Export user data (GDPR compliance)
