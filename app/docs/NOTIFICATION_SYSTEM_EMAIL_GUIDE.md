# Notification System Email Guide

## Overview

The notification system includes a comprehensive email notification service that delivers notifications to users via SMTP. This guide covers email template creation, delivery management, and integration patterns.

**Email Service:** `app/email/notification_service.py`  
**Template Directory:** `app/templates/email/notifications/`  
**Delivery Method:** Background threading (non-blocking)

## Email Service Architecture

### Service Components
- **Email Notification Service** - Main service class
- **Template Engine** - Jinja2 template rendering
- **SMTP Integration** - Flask-Mail for email delivery
- **Background Processing** - Threading for non-blocking sends
- **Delivery Tracking** - Analytics integration

### Email Flow
```
Notification Created → Check Preferences → Render Template → Send Email → Track Analytics
```

## Email Templates

### Template Structure
Email templates are located in `app/templates/email/notifications/` and follow a consistent naming convention:

- `{type}.html` - HTML version of email
- `{type}.txt` - Plain text version of email  
- `{type}_subject.txt` - Email subject line

### Available Templates

#### Comment Notifications
**Files:** `notification_comment.html`, `notification_comment.txt`, `notification_comment_subject.txt`

**Purpose:** Notifies users when someone comments on their posts

**Variables:**
- `user` - User object receiving notification
- `notification` - Notification object
- `post` - Post object (if available)
- `comment` - Comment object (if available)
- `site_name` - Site name from config

**Subject Template:**
```text
New comment on your post: "{{ post.title if post else 'Forum Post' }}"
```

#### Message Notifications  
**Files:** `notification_message.html`, `notification_message.txt`, `notification_message_subject.txt`

**Purpose:** Notifies users when they receive new messages

**Variables:**
- `user` - User object receiving notification
- `notification` - Notification object
- `message` - Message object (if available)
- `sender` - Sender user object (if available)
- `site_name` - Site name from config

**Subject Template:**
```text
New message from {{ sender.username if sender else 'Forum User' }}
```

#### Default Notifications
**File:** `notification_default.html`

**Purpose:** Fallback template for system notifications

**Variables:**
- `user` - User object receiving notification
- `notification` - Notification object
- `site_name` - Site name from config

## Email Service API

### EmailNotificationService Class

#### Initialization
```python
from app.email.notification_service import email_notification_service

# Service is automatically initialized
# Access via singleton instance
service = email_notification_service
```

#### send_notification_email()
Send email notification to user.

```python
def send_notification_email(self, user_id: int, notification_id: int, 
                         template_name: str = 'notification_default') -> bool:
    """
    Send email notification to user
    
    Args:
        user_id: User ID to send email to
        notification_id: Notification ID to include
        template_name: Template name to use (without extension)
    
    Returns:
        bool: Success status
    """
```

**Example Usage:**
```python
success = email_notification_service.send_notification_email(
    user_id=123,
    notification_id=456,
    template_name='notification_comment'
)
```

#### send_bulk_notifications()
Send bulk email notifications.

```python
def send_bulk_notifications(self, notifications: List[Dict], 
                          template_name: str = 'notification_default') -> Dict:
    """
    Send bulk email notifications
    
    Args:
        notifications: List of notification dictionaries
        template_name: Template name to use
    
    Returns:
        Dict: Results with success/failure counts
    """
```

**Example Usage:**
```python
notifications = [
    {'user_id': 1, 'notification_id': 123},
    {'user_id': 2, 'notification_id': 124}
]

results = email_notification_service.send_bulk_notifications(
    notifications,
    'notification_message'
)
```

#### send_digest_email()
Send daily/weekly digest of notifications.

```python
def send_digest_email(self, user_id: int, notifications: List[Notification], 
                     digest_type: str = 'daily') -> bool:
    """
    Send digest email to user
    
    Args:
        user_id: User ID to send digest to
        notifications: List of notifications to include
        digest_type: Type of digest ('daily', 'weekly', 'monthly')
    
    Returns:
        bool: Success status
    """
```

#### send_welcome_email()
Send welcome email to new users.

```python
def send_welcome_email(self, user_id: int) -> bool:
    """
    Send welcome email to new user
    
    Args:
        user_id: User ID to send welcome email to
    
    Returns:
        bool: Success status
    """
```

#### send_password_reset_email()
Send password reset email.

```python
def send_password_reset_email(self, user_id: int, reset_token: str) -> bool:
    """
    Send password reset email
    
    Args:
        user_id: User ID to send reset email to
        reset_token: Password reset token
    
    Returns:
        bool: Success status
    """
```

#### send_verification_email()
Send email verification email.

```python
def send_verification_email(self, user_id: int, verification_token: str) -> bool:
    """
    Send email verification email
    
    Args:
        user_id: User ID to send verification email to
        verification_token: Email verification token
    
    Returns:
        bool: Success status
    """
```

### Helper Methods

#### check_email_preferences()
Check if user has email notifications enabled.

```python
def check_email_preferences(self, user_id: int, notification_type: str = 'all') -> bool:
    """
    Check if user has email notifications enabled
    
    Args:
        user_id: User ID to check
        notification_type: Type of notification to check
    
    Returns:
        bool: True if email notifications enabled
    """
```

#### render_email_template()
Render email template with context.

```python
def render_email_template(self, template_name: str, context: Dict) -> Tuple[str, str]:
    """
    Render email template
    
    Args:
        template_name: Template name (without extension)
        context: Template context variables
    
    Returns:
        Tuple[str, str]: (html_content, text_content)
    """
```

#### track_email_delivery()
Track email delivery analytics.

```python
def track_email_delivery(self, notification_id: int, status: str, 
                        recipient_email: str, error_message: str = None):
    """
    Track email delivery analytics
    
    Args:
        notification_id: Notification ID
        status: Delivery status ('sent', 'failed', 'bounced')
        recipient_email: Recipient email address
        error_message: Error message if failed
    """
```

## Configuration

### Environment Variables
```bash
# SMTP Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@autobotsolutions.com

# Email Notifications
EMAIL_NOTIFICATIONS_ENABLED=true
EMAIL_BATCH_SIZE=50
EMAIL_RETRY_ATTEMPTS=3
EMAIL_RETRY_DELAY=60
```

### Flask Configuration
```python
# In config.py
class Config:
    # Email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@autobotsolutions.com')
    
    # Email notification settings
    EMAIL_NOTIFICATIONS_ENABLED = os.environ.get('EMAIL_NOTIFICATIONS_ENABLED', 'true').lower() in ['true', 'on', '1']
    EMAIL_BATCH_SIZE = int(os.environ.get('EMAIL_BATCH_SIZE', 50))
    EMAIL_RETRY_ATTEMPTS = int(os.environ.get('EMAIL_RETRY_ATTEMPTS', 3))
    EMAIL_RETRY_DELAY = int(os.environ.get('EMAIL_RETRY_DELAY', 60))
```

## Template Development

### Creating New Templates

#### 1. HTML Template
Create `{template_name}.html` in `app/templates/email/notifications/`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background-color: #007bff;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .content {
            padding: 20px;
            background-color: #f8f9fa;
        }
        .button {
            display: inline-block;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 0;
        }
        .footer {
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ site_name }}</h1>
    </div>
    
    <div class="content">
        <h2>{{ subject }}</h2>
        <p>Hello {{ user.username }},</p>
        
        <p>{{ notification.content }}</p>
        
        {% if notification.link %}
        <p>
            <a href="{{ notification.link }}" class="button">
                View {{ notification.type }}
            </a>
        </p>
        {% endif %}
        
        <p>Thank you for using {{ site_name }}!</p>
    </div>
    
    <div class="footer">
        <p>This is an automated message. Please do not reply to this email.</p>
        <p>If you no longer wish to receive these emails, 
           <a href="{{ url_for('auth.settings', _external=True) }}">update your preferences</a>.</p>
    </div>
</body>
</html>
```

#### 2. Plain Text Template
Create `{template_name}.txt` in `app/templates/email/notifications/`:

```text
{{ site_name }} - {{ subject }}

Hello {{ user.username }},

{{ notification.content }}

{% if notification.link %}
View {{ notification.type }}: {{ notification.link }}
{% endif %}

Thank you for using {{ site_name }}!

---
This is an automated message. Please do not reply to this email.
If you no longer wish to receive these emails, update your preferences at:
{{ url_for('auth.settings', _external=True) }}
```

#### 3. Subject Template
Create `{template_name}_subject.txt` in `app/templates/email/notifications/`:

```text
{{ site_name }}: {{ notification.type|title }}
```

### Template Variables

#### Standard Variables
- `user` - User object receiving notification
- `notification` - Notification object
- `site_name` - Site name from configuration
- `url_for()` - Flask URL generation function

#### Context-Specific Variables
- `post` - Post object (for comment notifications)
- `comment` - Comment object (for comment notifications)
- `message` - Message object (for message notifications)
- `sender` - Sender user object (for message notifications)

#### Custom Variables
Add custom variables in the service method:

```python
# In send_notification_email method
context = {
    'user': user,
    'notification': notification,
    'site_name': current_app.config.get('SITE_NAME', 'AutoBot Solutions Forum'),
    'custom_var': 'custom_value'  # Add custom variables here
}
```

## Integration Examples

### Basic Integration
```python
from app.email.notification_service import email_notification_service

# Send notification email
success = email_notification_service.send_notification_email(
    user_id=current_user.id,
    notification_id=notification.id,
    template_name='notification_comment'
)

if success:
    logger.info(f"Email notification sent to user {current_user.id}")
else:
    logger.error(f"Failed to send email notification to user {current_user.id}")
```

### With Analytics Tracking
```python
from app.email.notification_service import email_notification_service
from app.analytics.notification_analytics import notification_analytics

# Send email notification
success = email_notification_service.send_notification_email(
    user_id=user.id,
    notification_id=notification.id,
    template_name='notification_message'
)

# Track analytics
if success:
    notification_analytics.track_notification_delivery(
        notification_id=notification.id,
        delivery_type='email',
        status='sent',
        recipient_id=user.id,
        metadata={
            'template': 'notification_message',
            'timestamp': datetime.utcnow().isoformat()
        }
    )
else:
    notification_analytics.track_notification_delivery(
        notification_id=notification.id,
        delivery_type='email',
        status='failed',
        recipient_id=user.id,
        metadata={
            'error': 'SMTP delivery failed',
            'template': 'notification_message'
        }
    )
```

### Background Processing
```python
import threading
from app.email.notification_service import email_notification_service

def send_notification_async(user_id, notification_id, template_name):
    """Send notification in background thread"""
    try:
        email_notification_service.send_notification_email(
            user_id=user_id,
            notification_id=notification_id,
            template_name=template_name
        )
    except Exception as e:
        logger.error(f"Background email send failed: {str(e)}")

# Create background thread
thread = threading.Thread(
    target=send_notification_async,
    args=(user.id, notification.id, 'notification_comment')
)
thread.daemon = True
thread.start()
```

### Bulk Email Sending
```python
from app.email.notification_service import email_notification_service

# Prepare bulk notifications
notifications = []
for user in users_to_notify:
    notification = create_notification(user.id, content, link)
    notifications.append({
        'user_id': user.id,
        'notification_id': notification.id
    })

# Send bulk emails
results = email_notification_service.send_bulk_notifications(
    notifications,
    'notification_system'
)

logger.info(f"Bulk email results: {results}")
```

## Testing

### Unit Testing
```python
import pytest
from app.email.notification_service import EmailNotificationService
from app.models import User, Notification

class TestEmailNotificationService:
    def setup_method(self):
        self.service = EmailNotificationService()
        self.service._initialize()
    
    def test_send_notification_email(self):
        """Test sending notification email"""
        # Create test user and notification
        user = User(username='testuser', email='test@example.com')
        notification = Notification(
            user_id=user.id,
            content='Test notification',
            link='/test'
        )
        
        # Mock email sending
        with patch('flask_mail.Message') as mock_message:
            result = self.service.send_notification_email(
                user.id,
                notification.id,
                'notification_default'
            )
            
            assert result is True
            mock_message.assert_called_once()
    
    def test_check_email_preferences(self):
        """Test email preference checking"""
        user = User(id=1, email_enabled=True, email_preferences='{"all": true}')
        
        with patch('app.models.User.query.get', return_value=user):
            result = self.service.check_email_preferences(1, 'comment')
            assert result is True
    
    def test_render_email_template(self):
        """Test template rendering"""
        context = {
            'user': User(username='test'),
            'notification': Notification(content='Test'),
            'site_name': 'Test Site'
        }
        
        html_content, text_content = self.service.render_email_template(
            'notification_default',
            context
        )
        
        assert 'Test notification' in html_content
        assert 'Test notification' in text_content
        assert 'Test Site' in html_content
```

### Integration Testing
```python
def test_email_notification_integration():
    """Test complete email notification flow"""
    with app.test_request_context():
        # Create test user
        user = User(
            username='testuser',
            email='test@example.com',
            email_enabled=True
        )
        db.session.add(user)
        db.session.commit()
        
        # Create notification
        notification = create_notification(
            user.id,
            'Test notification',
            '/test',
            'system'
        )
        
        # Send email notification
        success = email_notification_service.send_notification_email(
            user.id,
            notification.id,
            'notification_default'
        )
        
        # Verify success
        assert success is True
        
        # Check analytics tracking
        analytics = notification_analytics.get_delivery_analytics()
        assert analytics['summary']['total_notifications'] > 0
```

### Email Testing with Mailtrap
```python
# For development/testing with Mailtrap
class TestConfig(Config):
    MAIL_SERVER = 'sandbox.smtp.mailtrap.io'
    MAIL_PORT = 2525
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your-mailtrap-username'
    MAIL_PASSWORD = 'your-mailtrap-password'
```

## Performance Optimization

### Template Caching
```python
from flask_caching import Cache

cache = Cache()

@cache.memoize(timeout=300)  # Cache for 5 minutes
def render_cached_template(template_name, context):
    """Render template with caching"""
    return render_email_template(template_name, context)
```

### Connection Pooling
```python
# Configure SMTP connection pooling
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['MAIL_ASCII_ATTACHMENTS'] = False
```

### Batch Processing
```python
def process_email_batch(notifications, batch_size=50):
    """Process emails in batches to avoid overwhelming SMTP"""
    for i in range(0, len(notifications), batch_size):
        batch = notifications[i:i + batch_size]
        process_batch(batch)
        time.sleep(1)  # Rate limiting
```

## Troubleshooting

### Common Issues

#### SMTP Connection Errors
**Problem:** SMTP connection fails  
**Solution:** Check SMTP configuration, verify credentials, test with telnet

```bash
# Test SMTP connection
telnet smtp.gmail.com 587
```

#### Template Rendering Errors
**Problem:** Template not rendering correctly  
**Solution:** Check template syntax, verify context variables

```python
# Debug template rendering
try:
    html, text = render_email_template('notification_default', context)
except Exception as e:
    logger.error(f"Template rendering error: {e}")
    raise
```

#### Email Not Delivered
**Problem:** Email accepted but not delivered  
**Solution:** Check spam filters, verify sender reputation, examine bounce messages

#### Performance Issues
**Problem:** Slow email sending  
**Solution:** Use background processing, implement batching, optimize templates

### Debugging Tools

#### Email Logging
```python
import logging
logging.getLogger('flask_mail').setLevel(logging.DEBUG)
```

#### SMTP Debug Mode
```python
app.config['MAIL_DEBUG'] = True
app.config['MAIL_SUPPRESS_SEND'] = False
```

#### Template Debugging
```python
def debug_template(template_name, context):
    """Debug template rendering"""
    try:
        html, text = render_email_template(template_name, context)
        print(f"HTML: {html[:200]}...")
        print(f"Text: {text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
```

## Security Considerations

### Data Protection
- **Email Address Privacy:** Store email addresses securely
- **Content Sanitization:** Sanitize email content to prevent XSS
- **Rate Limiting:** Limit email sending frequency

### Authentication
- **SMTP Authentication:** Use secure SMTP authentication
- **TLS/SSL:** Use encrypted connections
- **Credential Security:** Store SMTP credentials securely

### Compliance
- **GDPR Compliance:** Respect email preferences
- **CAN-SPAM Compliance:** Include unsubscribe options
- **Data Retention:** Implement email retention policies

---

**Email Service Version:** 1.0  
**Template Engine:** Jinja2  
**SMTP Library:** Flask-Mail  
**Last Updated:** May 12, 2026
