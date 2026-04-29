# Administrator Guide

## Overview

Complete guide for administrators managing the AutoBot Solutions Forum.

## Accessing Admin Panel

### Requirements
- Admin account with `is_admin=True`
- Created by `init_db.py` script
- Or promoted by existing admin

### Access
1. Login with admin credentials
2. Click "Admin" in navbar
3. Access dashboard and management tools

## Dashboard

### Statistics Overview
- Total users
- Total posts
- Total comments
- Total repositories
- Total categories
- Total badges

### Recent Activity
- Last 5 users registered
- Last 5 posts created
- Quick access to management

## User Management

### Viewing Users
- Navigate to "Users" in admin panel
- View all users with metadata
- See user statistics
- View user badges

### Managing Users

**Toggle Admin Status**
- Promote or demote users to admin
- Immediate effect on permissions
- Use with caution

**Delete User**
- Removes user account
- Cascades to all user data
- Posts, comments, votes deleted
- Cannot be undone

**Manage Badges**
- Add badge to user
- Remove badge from user
- View user's current badges

### User Management Best Practices
- Review new users regularly
- Promote trusted users to admin
- Delete spam accounts promptly
- Keep admin count minimal
- Document admin actions

## Content Moderation

### Post Moderation

**View Posts**
- Navigate to "Posts" in admin panel
- View all posts with metadata
- See vote counts
- View author information

**Delete Post**
- Removes post from forum
- Deletes all comments
- Removes votes
- Cannot be undone

**When to Delete Posts**
- Spam or promotional content
- Offensive or harmful content
- Duplicate posts
- Off-topic posts
- Violates community guidelines

### Comment Moderation

**View Comments**
- Navigate to "Comments" in admin panel
- View all comments with metadata
- See parent post
- View vote counts

**Delete Comment**
- Removes comment
- Removes votes
- Removes notifications
- Cannot be undone

**When to Delete Comments**
- Spam or trolling
- Offensive language
- Personal attacks
- Off-topic comments
- Violates community guidelines

## Repository Management

### Viewing Repositories
- Navigate to "Repositories" in admin panel
- View all synced repositories
- See GitHub metadata
- View post counts

### Syncing Repositories
- Click "Sync" button
- Fetches from GitHub API
- Updates or creates records
- Updates stars and language
- Rate limited to 5/hour

### Deleting Repositories
- Removes repository from database
- Posts become unlinked
- Cannot be undone
- Use with caution

### Repository Management Best Practices
- Sync repositories regularly
- Monitor sync errors
- Keep repository list clean
- Delete unused repositories
- Document repository purposes

## Category Management

### Viewing Categories
- Navigate to "Categories" in admin panel
- View all categories
- See category colors
- View post counts

### Creating Categories
1. Click "Create Category"
2. Enter category name
3. Add description (optional)
4. Choose color (hex)
5. Click "Create Category"

### Deleting Categories
- Removes category
- Posts become uncategorized
- Cannot be undone
- Posts need manual re-categorization

### Category Management Best Practices
- Create meaningful categories
- Use distinct colors
- Keep category count manageable
- Delete unused categories
- Update category descriptions

## Badge Management

### Viewing Badges
- Navigate to "Badges" in admin panel
- View all badges
- See badge icons and colors
- View user counts

### Creating Badges
1. Click "Create Badge"
2. Enter badge name
3. Add description
4. Choose icon (emoji)
5. Choose color (hex)
6. Click "Create Badge"

### Deleting Badges
- Removes badge
- Removes from all users
- Cannot be undone
- Use with caution

### Assigning Badges
- Navigate to user management
- Click "Add Badge"
- Select badge from dropdown
- Badge immediately assigned

### Removing Badges
- Navigate to user management
- Click "Remove Badge"
- Badge immediately removed
- Can be reassigned later

### Badge Management Best Practices
- Create meaningful badges
- Use distinct icons
- Award badges fairly
- Document badge criteria
- Review badge assignments

## Security Considerations

### Admin Account Security
- Use strong passwords
- Enable 2FA when available
- Don't share credentials
- Change passwords regularly
- Monitor failed login attempts

### Session Security
- Log out after admin tasks
- Use secure connections
- Don't use public computers
- Clear browser cache
- Monitor session duration

### Audit Trail (Future)
- Log all admin actions
- Track who did what and when
- Review logs regularly
- Export logs for analysis

## Monitoring and Maintenance

### Regular Tasks
- Review new user registrations
- Check for spam content
- Monitor rate limit violations
- Review reported content
- Sync repositories
- Update categories and badges

### Performance Monitoring
- Monitor database performance
- Check response times
- Monitor disk space
- Review error logs
- Check rate limit usage

## Best Practices

### General
- Be fair and consistent
- Document your actions
- Communicate with users
- Follow community guidelines
- Stay updated on features

### Content Moderation
- Act promptly on reports
- Be objective
- Provide feedback when appropriate
- Consider appeals
- Document decisions

### User Management
- Promote users carefully
- Document admin promotions
- Review admin activity
- Keep admin count minimal
- Rotate admin passwords

## Troubleshooting

### Admin Access Denied
- Verify account has admin flag
- Check authentication status
- Ensure session is valid
- Contact system admin

### Actions Not Working
- Check CSRF token
- Verify database connection
- Check for JavaScript errors
- Refresh the page
- Try different browser

### Stats Not Updating
- Check database queries
- Verify data integrity
- Restart application
- Clear cache

## Getting Help

- Check [Security-System.md](Security-System.md)
- Review [Architecture-System.md](Architecture-System.md)
- Contact system admin for technical issues
- Report bugs via GitHub issues
