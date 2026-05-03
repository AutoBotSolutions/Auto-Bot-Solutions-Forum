# Error Monitoring System

The AutoBot Solutions Forum includes a comprehensive error monitoring system to help developers quickly identify and resolve issues.

## Overview

The error monitoring system provides:
- Real-time error capture and logging
- Detailed error information with context
- Easy access to error data for debugging
- Automated error file management

## Components

### 1. Error Logger Module (`error_logger.py`)

**Purpose**: Centralized error logging with detailed context

**Features**:
- Timestamp recording
- Error type and message capture
- Full traceback logging
- Request context (URL, method, IP, user agent)
- Automatic error file creation

**Usage**:
```python
from error_logger import log_error
log_error(exception, current_app)
```

### 2. Enhanced Error Handlers (`app/errors/handlers.py`)

**Purpose**: Improved error handling with automatic logging

**Features**:
- 404 error logging with request details
- 500 error logging with full context
- Database rollback on errors
- Graceful error page rendering

**Error Types Captured**:
- Page not found (404)
- Internal server errors (500)
- Application exceptions

### 3. Error Monitoring Script (`check_errors.py`)

**Purpose**: Quick error status checking and reporting

**Features**:
- Latest error file access
- Error log analysis
- Terminal output monitoring
- Comprehensive error reporting

**Usage**:
```bash
python check_errors.py
```

## File Structure

```
logs/
├── forum_errors.log      # Main error log file
└── latest_error.txt      # Most recent error details
```

## Error Data Captured

### Error Information
- **Timestamp**: UTC timestamp of error occurrence
- **Error Type**: Exception class name
- **Error Message**: Detailed error description
- **Traceback**: Full stack trace for debugging

### Request Context
- **URL**: Requested URL that caused error
- **Method**: HTTP method (GET, POST, etc.)
- **IP Address**: Client IP address
- **User Agent**: Browser/client information

## Usage Guide

### Checking Errors

#### Quick Error Check
```bash
# Run error monitoring script
python check_errors.py

# Output includes:
# - Latest error details
# - Recent error log entries
# - Terminal output status
```

#### Manual Error File Check
```bash
# Check latest error
cat logs/latest_error.txt

# Check full error log
tail -f logs/forum_errors.log

# Search for specific errors
grep "ERROR" logs/forum_errors.log
```

#### Real-time Monitoring
```bash
# Monitor error log in real-time
tail -f logs/forum_errors.log

# Check Flask app output
# Use command_status tool to check running Flask app
```

### Error Log Format

#### Main Error Log (`logs/forum_errors.log`)
```
2024-05-02 23:14:06,721 ERROR: Forum Error: {'timestamp': '2024-05-02T23:14:06.721000', 'error_type': 'AttributeError', 'error_message': "'Post' object has no attribute 'author_id'", ...}
```

#### Latest Error File (`logs/latest_error.txt`)
```
Error occurred at: 2024-05-02T23:14:06.721000
Type: AttributeError
Message: 'Post' object has no attribute 'author_id'
URL: http://127.0.0.1:37821/forum/post/1/comment
Method: POST
IP: 127.0.0.1
User Agent: Mozilla/5.0...

--- Full Traceback ---
Traceback (most recent call last):
  File ".../forum/routes.py", line 94, in add_comment
    if post.author_id != current_user.id:
AttributeError: 'Post' object has no attribute 'author_id'
```

## Integration with Flask App

### Automatic Error Logging

The system automatically logs errors when:
- 404 errors occur (page not found)
- 500 errors occur (internal server error)
- Unhandled exceptions in routes

### Manual Error Logging

For custom error logging in routes:
```python
from error_logger import log_error

try:
    # Your code here
    risky_operation()
except Exception as e:
    log_error(e, current_app)
    flash('An error occurred', 'error')
```

## Configuration

### Log File Location
- Default: `logs/` directory
- Automatically created if doesn't exist
- Configurable in error_logger.py

### Log Rotation
- Manual rotation recommended for production
- Example cron job:
```bash
# Weekly log rotation
0 0 * * 0 cd /path/to/forum && mv logs/forum_errors.log logs/forum_errors_$(date +\%Y\%m\%d).log
```

### Log Retention
- Keep recent logs for debugging
- Archive old logs periodically
- Consider log size limits for production

## Troubleshooting the Error System

### Common Issues

**Log Directory Not Created**
```bash
# Create logs directory manually
mkdir logs
chmod 755 logs
```

**Permission Issues**
```bash
# Check permissions
ls -la logs/

# Fix permissions
chmod 644 logs/*.log
chmod 644 logs/*.txt
```

**Missing Error Files**
```bash
# Trigger a test error to create files
# Visit a non-existent URL to generate 404 error
# Or access the forum with invalid data
```

## Best Practices

### Development
- Check error logs regularly during development
- Use error information to fix issues quickly
- Test error handling in development mode

### Production
- Monitor error logs for issues
- Set up automated error alerts
- Regular log rotation and cleanup
- Backup error logs for analysis

### Security
- Error logs may contain sensitive information
- Restrict access to log files
- Sanitize error messages for public display
- Consider log encryption for sensitive data

## Integration with External Monitoring

### Future Enhancements
- Email notifications for critical errors
- Integration with external monitoring services
- Error aggregation and analytics
- Performance monitoring integration

### External Services
The error system can be extended to work with:
- Sentry.io for error tracking
- Rollbar for error monitoring
- Custom webhook integrations
- Slack/Discord notifications

## Examples

### Recent Errors Fixed Using This System

1. **Jinja2 Template Error**
   - **Error**: `AttributeError: 'InstrumentedList' object has no attribute 'filter_by'`
   - **Solution**: Fixed template filter usage in base.html
   - **Detection**: Error logged during user login

2. **Comment Submission Error**
   - **Error**: `AttributeError: 'Post' object has no attribute 'author_id'`
   - **Solution**: Changed to use `user_id` in forum routes
   - **Detection**: Error logged when user tried to comment

3. **Markdown Rendering Issue**
   - **Error**: Raw HTML tags displayed instead of rendered content
   - **Solution**: Added `|safe` filter to post template
   - **Detection**: User reported via forum post

This error monitoring system significantly improves debugging efficiency and helps maintain forum stability.
