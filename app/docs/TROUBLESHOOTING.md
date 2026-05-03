# Troubleshooting Guide

This guide covers common issues and their solutions for the AutoBot Solutions Forum.

## Recent Fixes (May 2026)

### Fixed Issues

1. **Jinja2 Template Error - Login Crash**
   - **Problem**: `AttributeError: 'InstrumentedList' object has no attribute 'filter_by'`
   - **Solution**: Changed `current_user.notifications.filter_by()` to use `selectattr()` Jinja2 filter
   - **Files**: `app/templates/base.html`

2. **Create Post Form Not Working**
   - **Problem**: Submit button was unresponsive
   - **Solution**: Added missing form fields, enctype for file uploads, and proper form rendering
   - **Files**: `app/templates/forum/create.html`

3. **Markdown Rendering Issues**
   - **Problem**: Raw HTML tags displayed instead of rendered content
   - **Solution**: Added `|safe` filter and simplified markdown filter
   - **Files**: `app/templates/forum/post.html`, `app/template_filters.py`

4. **Comment Submission AttributeError**
   - **Problem**: `AttributeError: 'Post' object has no attribute 'author_id'`
   - **Solution**: Changed `post.author_id` to `post.user_id` to match model
   - **Files**: `app/forum/routes.py`

5. **Website Repository Links**
   - **Problem**: Links pointing to wrong repository URL
   - **Solution**: Updated all GitHub links to correct repository
   - **Files**: `site/index.html`

6. **Messages Inbox AttributeError**
   - **Problem**: `AttributeError: 'InstrumentedList' object has no attribute 'order_by'`
   - **Solution**: Changed to use proper Message.query for received/sent messages
   - **Files**: `app/message/routes.py`

7. **Admin Dashboard Icon Issues**
   - **Problem**: Emoji icons not displaying correctly
   - **Solution**: Replaced with professional SVG icons and sci-fi styling
   - **Files**: `app/templates/admin/dashboard.html`

8. **Navigation Icon Enhancement**
   - **Problem**: Basic emoji notification icon
   - **Solution**: Replaced with SVG icon and added hover effects
   - **Files**: `app/templates/base.html`, `app/static/css/style.css`

9. **Admin Badges Icon Issues**
   - **Problem**: Badge icons displaying as emojis (🎯, 🏆, etc.)
   - **Solution**: Created comprehensive emoji-to-SVG mapping system
   - **Files**: `app/templates/admin/badges.html`

10. **Menu Bar Layout Issues**
    - **Problem**: Admin button offset causing logout to wrap to next row
    - **Solution**: Created admin dropdown menu and improved responsive design
    - **Files**: `app/templates/base.html`, `app/static/css/style.css`

## Error Monitoring System

### New Error Tracking Features

The forum now includes comprehensive error monitoring:

1. **Error Logger Module** (`error_logger.py`)
   - Detailed error logging with timestamps
   - Request information (URL, method, IP, user agent)
   - Full traceback capture
   - Automatic error file creation

2. **Enhanced Error Handlers** (`app/errors/handlers.py`)
   - Improved 404 and 500 error handling
   - Automatic error logging on exceptions
   - Database rollback on errors

3. **Error Monitoring Script** (`check_errors.py`)
   - Quick error status checking
   - Latest error file access
   - Comprehensive error reporting

### Using Error Monitoring

```bash
# Check latest error
python check_errors.py

# Check error logs
cat logs/forum_errors.log

# Check latest specific error
cat logs/latest_error.txt
```

## Common Issues & Solutions

### Installation Issues

**Python Environment Issues**
```bash
# Ensure correct Python version
python3 --version  # Should be 3.8+

# Create clean virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Database Initialization Issues**
```bash
# Check if database exists
ls instance/

# Reinitialize database
rm instance/forum.db
python init_db.py
```

### Runtime Issues

**Forum Won't Start**
```bash
# Check if port is in use
lsof -i :5000

# Kill existing processes
pkill -f "python run.py"

# Restart forum
python run.py
```

**Template Errors**
- Check all template files for correct syntax
- Verify all template filters are registered
- Ensure `|safe` filter is used for HTML content
- Check variable names match model attributes

**Form Submission Issues**
- Verify CSRF token is present: `{{ form.hidden_tag() }}`
- Check form enctype for file uploads: `enctype="multipart/form-data"`
- Ensure form method is correct: `method="POST"`
- Verify form validation in routes

### Database Issues

**Connection Errors**
```bash
# Check database file permissions
ls -la instance/forum.db

# Verify database schema
sqlite3 instance/forum.db ".schema"
```

**Migration Issues**
```bash
# Reset database (WARNING: This deletes all data)
rm instance/forum.db
python init_db.py
```

### Performance Issues

**Slow Loading**
- Check database size: `ls -lh instance/forum.db`
- Monitor memory usage: `ps aux | grep python`
- Check for long-running queries

**Memory Issues**
- Restart application: `pkill -f python && python run.py`
- Check for memory leaks in long-running processes

## Debug Mode

### Enabling Debug Mode

```bash
# Set debug environment variable
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run with debug
python run.py
```

### Debug Information Available

- Detailed error pages with tracebacks
- Interactive debugger in browser
- Auto-reload on code changes
- Detailed logging output

## Log Files

### Available Logs

1. **Flask Development Log** (terminal output)
2. **Error Log** (`logs/forum_errors.log`)
3. **Latest Error** (`logs/latest_error.txt`)

### Log Analysis

```bash
# Monitor real-time logs
tail -f logs/forum_errors.log

# Search for specific errors
grep "ERROR" logs/forum_errors.log

# Check error frequency
wc -l logs/forum_errors.log
```

## Getting Help

### Self-Service Debugging

1. **Check Error Logs**: Use `check_errors.py` script
2. **Review Recent Changes**: Check git log for recent modifications
3. **Test in Isolation**: Try to reproduce issue in development
4. **Check Configuration**: Verify `.env` settings

### Reporting Issues

When reporting issues, include:

1. **Error Message**: Full error text and traceback
2. **Steps to Reproduce**: Detailed steps to recreate issue
3. **Environment**: OS, Python version, browser
4. **Recent Changes**: Any recent modifications or updates
5. **Log Files**: Relevant log entries

### Emergency Recovery

If forum is completely broken:

```bash
# Reset to working state
git status
git checkout -- app/  # Reset app files
git log --oneline -10   # Check recent commits
git revert HEAD         # Revert last commit if needed

# Reinitialize database
rm instance/forum.db
python init_db.py

# Restart forum
python run.py
```

## Prevention

### Best Practices

1. **Regular Backups**: Backup database and configuration
2. **Test Changes**: Test in development before production
3. **Monitor Logs**: Regularly check error logs
4. **Update Dependencies**: Keep packages up to date
5. **Document Changes**: Update documentation with modifications

### Monitoring Setup

Set up automated monitoring:

```bash
# Add to crontab for daily error check
0 8 * * * cd /path/to/forum && python check_errors.py >> /var/log/forum_monitor.log 2>&1
```

This comprehensive troubleshooting guide should help resolve most common issues with the AutoBot Solutions Forum.
