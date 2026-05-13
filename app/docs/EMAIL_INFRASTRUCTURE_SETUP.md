# Email Infrastructure Setup Guide

## Overview

This guide provides comprehensive instructions for setting up the email infrastructure for the notification system. The email infrastructure enables reliable email delivery of notifications with queue management, template rendering, and delivery tracking.

**Components:**
- SMTP Server Configuration
- Email Queue Management
- Template System
- Delivery Tracking
- Bounce Handling
- Analytics and Monitoring

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Notification     │    │  Email Queue    │    │  SMTP Server    │
│ Service         │──►│  (Redis/Celery) │──►│  (SendGrid/SMTP)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Delivery       │
                       │  Tracking       │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Analytics      │
                       │  & Monitoring   │
                       └─────────────────┘
```

## Prerequisites

### System Requirements
- **Python 3.8+**
- **Redis 6.0+** (for queue management)
- **SMTP Server** (SendGrid, AWS SES, or custom SMTP)
- **Email Domain** with proper DNS records

### Email Service Options

#### Option 1: SendGrid (Recommended)
- High deliverability
- Easy API integration
- Built-in analytics
- Free tier available

#### Option 2: AWS SES
- Cost-effective for high volume
- Reliable infrastructure
- Good integration with AWS ecosystem

#### Option 3: Custom SMTP
- Full control over infrastructure
- Can use existing email servers
- Requires more maintenance

## Configuration

### Environment Variables

Update your `.env` file with email configuration:

```bash
# Email Notification Settings
EMAIL_NOTIFICATION_ENABLED=true
SMTP_NOTIFICATION_SERVER=smtp.sendgrid.net
SMTP_NOTIFICATION_PORT=587
SMTP_NOTIFICATION_USE_TLS=true
SMTP_NOTIFICATION_USE_SSL=false

# SMTP Authentication
SMTP_NOTIFICATION_USERNAME=apikey
SMTP_NOTIFICATION_PASSWORD=your-sendgrid-api-key
SMTP_NOTIFICATION_DEFAULT_SENDER=noreply@yourdomain.com
SMTP_NOTIFICATION_DEFAULT_SENDER_NAME=AutoBot Solutions Forum

# Email Queue Settings
EMAIL_QUEUE_ENABLED=true
EMAIL_QUEUE_WORKERS=4
EMAIL_QUEUE_MAX_SIZE=1000
EMAIL_QUEUE_PROCESSING_INTERVAL=30
EMAIL_NOTIFICATION_BATCH_SIZE=50

# Email Delivery Settings
EMAIL_NOTIFICATION_RETRY_ATTEMPTS=3
EMAIL_NOTIFICATION_RETRY_DELAY=5
EMAIL_TEMPLATE_CACHE_ENABLED=true
EMAIL_TEMPLATE_DIR=app/templates/email/notifications

# Email Analytics
EMAIL_DELIVERY_TRACKING_ENABLED=true
EMAIL_OPEN_TRACKING_ENABLED=true
EMAIL_CLICK_TRACKING_ENABLED=true
```

### SendGrid Configuration

#### 1. Create SendGrid Account
1. Sign up at [sendgrid.com](https://sendgrid.com)
2. Verify your email domain
3. Create an API key

#### 2. Configure DNS Records
Add these records to your DNS:

```
TXT  @  v=spf1 include:sendgrid.net ~all
TXT  @  v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC...
TXT  sendgrid._domainkey yourdomain.com "k=rsa; t=s; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC..."
```

#### 3. Environment Setup
```bash
# SendGrid specific settings
SMTP_NOTIFICATION_SERVER=smtp.sendgrid.net
SMTP_NOTIFICATION_PORT=587
SMTP_NOTIFICATION_USERNAME=apikey
SMTP_NOTIFICATION_PASSWORD=SG.your-sendgrid-api-key-here
```

### AWS SES Configuration

#### 1. Set up AWS SES
1. Go to AWS Console → Simple Email Service
2. Verify your domain and email addresses
3. Create SMTP credentials

#### 2. Environment Setup
```bash
# AWS SES specific settings
SMTP_NOTIFICATION_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_NOTIFICATION_PORT=587
SMTP_NOTIFICATION_USERNAME=your-smtp-username
SMTP_NOTIFICATION_PASSWORD=your-smtp-password
```

### Custom SMTP Configuration

#### 1. SMTP Server Setup
Configure your SMTP server (Postfix, Exim, etc.)

#### 2. Environment Setup
```bash
# Custom SMTP settings
SMTP_NOTIFICATION_SERVER=smtp.yourdomain.com
SMTP_NOTIFICATION_PORT=587
SMTP_NOTIFICATION_USERNAME=your-smtp-username
SMTP_NOTIFICATION_PASSWORD=your-smtp-password
```

## Email Service Implementation

### Enhanced Email Service

Update `app/email/notification_service.py`:

```python
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.html import MIMEText
from email.utils import formataddr
from jinja2 import Environment, FileSystemLoader, Template
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import redis
import json
import threading
import queue
import time

from app.config.notification_config import get_notification_config

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """Enhanced email notification service with queue management"""
    
    def __init__(self):
        self.config = get_notification_config()
        self.redis_client = None
        self.email_queue = queue.Queue()
        self.queue_workers = []
        self.template_env = None
        self.delivery_stats = {
            'sent': 0,
            'failed': 0,
            'bounced': 0,
            'opened': 0,
            'clicked': 0
        }
        
        self._setup_redis()
        self._setup_templates()
        self._start_queue_workers()
    
    def _setup_redis(self):
        """Setup Redis connection for queue management"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                db=self.config.redis_notification_db,
                decode_responses=True
            )
            logger.info("Redis connection established for email queue")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
    
    def _setup_templates(self):
        """Setup Jinja2 template environment"""
        try:
            template_loader = FileSystemLoader(self.config.email_template_dir)
            self.template_env = Environment(
                loader=template_loader,
                autoescape=True,
                cache_size=100 if self.config.email_template_cache_enabled else 0
            )
            logger.info("Email template environment initialized")
        except Exception as e:
            logger.error(f"Failed to setup email templates: {str(e)}")
    
    def _start_queue_workers(self):
        """Start background workers for email queue processing"""
        if not self.config.email_queue_enabled:
            return
        
        for i in range(self.config.email_queue_workers):
            worker = threading.Thread(
                target=self._queue_worker,
                name=f"EmailWorker-{i}",
                daemon=True
            )
            worker.start()
            self.queue_workers.append(worker)
        
        logger.info(f"Started {self.config.email_queue_workers} email queue workers")
    
    def _queue_worker(self):
        """Background worker for processing email queue"""
        while True:
            try:
                # Get email from queue
                email_data = self._get_from_queue()
                
                if email_data:
                    self._process_email(email_data)
                else:
                    time.sleep(self.config.email_queue_processing_interval)
                    
            except Exception as e:
                logger.error(f"Email queue worker error: {str(e)}")
                time.sleep(5)
    
    def _get_from_queue(self) -> Optional[Dict]:
        """Get email from queue"""
        try:
            # Try Redis queue first
            if self.redis_client:
                result = self.redis_client.lpop('email_queue')
                if result:
                    return json.loads(result)
            
            # Fallback to in-memory queue
            try:
                return self.email_queue.get_nowait()
            except queue.Empty:
                return None
                
        except Exception as e:
            logger.error(f"Error getting email from queue: {str(e)}")
            return None
    
    def _add_to_queue(self, email_data: Dict):
        """Add email to queue"""
        try:
            # Add to Redis queue
            if self.redis_client:
                self.redis_client.rpush('email_queue', json.dumps(email_data))
                # Limit queue size
                self.redis_client.ltrim('email_queue', 0, self.config.email_queue_max_size - 1)
            else:
                # Fallback to in-memory queue
                self.email_queue.put(email_data)
                
            logger.debug(f"Email added to queue: {email_data.get('to')}")
            
        except Exception as e:
            logger.error(f"Error adding email to queue: {str(e)}")
    
    def send_notification_email(self, notification: Dict, user_email: str, 
                             user_language: str = 'en') -> bool:
        """Send notification email"""
        try:
            # Prepare email data
            email_data = {
                'to': user_email,
                'subject': self._render_subject(notification, user_language),
                'html_body': self._render_html_template(notification, user_language),
                'text_body': self._render_text_template(notification, user_language),
                'notification_id': notification.get('id'),
                'notification_type': notification.get('type'),
                'user_id': notification.get('user_id'),
                'language': user_language,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Add to queue
            self._add_to_queue(email_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error queuing notification email: {str(e)}")
            return False
    
    def send_bulk_emails(self, notifications: List[Dict], 
                        recipients: List[str]) -> Dict:
        """Send bulk emails to multiple recipients"""
        results = {
            'queued': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            for i, (notification, recipient) in enumerate(zip(notifications, recipients)):
                try:
                    success = self.send_notification_email(
                        notification, 
                        recipient
                    )
                    
                    if success:
                        results['queued'] += 1
                    else:
                        results['failed'] += 1
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'index': i,
                        'recipient': recipient,
                        'error': str(e)
                    })
            
            logger.info(f"Bulk email queuing completed: {results['queued']} queued, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk email sending: {str(e)}")
            return results
    
    def _process_email(self, email_data: Dict):
        """Process and send email"""
        try:
            # Create message
            message = self._create_email_message(email_data)
            
            # Send email
            success = self._send_email(message, email_data['to'])
            
            if success:
                self._track_delivery(email_data, 'sent')
                self.delivery_stats['sent'] += 1
                logger.info(f"Email sent successfully to {email_data['to']}")
            else:
                self._track_delivery(email_data, 'failed')
                self.delivery_stats['failed'] += 1
                
        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            self._track_delivery(email_data, 'failed')
            self.delivery_stats['failed'] += 1
    
    def _create_email_message(self, email_data: Dict) -> MIMEMultipart:
        """Create email message"""
        message = MIMEMultipart('alternative')
        
        # Set headers
        message['Subject'] = email_data['subject']
        message['From'] = formataddr(
            (self.config.smtp_default_sender_name, 
             self.config.smtp_default_sender)
        )
        message['To'] = email_data['to']
        
        # Add custom headers for tracking
        message['X-Notification-ID'] = str(email_data.get('notification_id', ''))
        message['X-Notification-Type'] = email_data.get('notification_type', '')
        message['X-User-ID'] = str(email_data.get('user_id', ''))
        message['X-Language'] = email_data.get('language', 'en')
        
        # Add HTML part
        if email_data['html_body']:
            html_part = MIMEText(email_data['html_body'], 'html', 'utf-8')
            message.attach(html_part)
        
        # Add text part
        if email_data['text_body']:
            text_part = MIMEText(email_data['text_body'], 'plain', 'utf-8')
            message.attach(text_part)
        
        return message
    
    def _send_email(self, message: MIMEMultipart, to_email: str) -> bool:
        """Send email via SMTP"""
        try:
            # Create SMTP connection
            server = smtplib.SMTP(
                self.config.smtp_server,
                self.config.smtp_port
            )
            
            # Enable TLS if required
            if self.config.smtp_use_tls:
                server.starttls()
            
            # Login if credentials provided
            if self.config.smtp_username and self.config.smtp_password:
                server.login(
                    self.config.smtp_username,
                    self.config.smtp_password
                )
            
            # Send email
            server.send_message(message, to_addrs=[to_email])
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
    
    def _render_subject(self, notification: Dict, language: str = 'en') -> str:
        """Render email subject"""
        try:
            template_name = f"subjects/{notification['type']}_{language}.txt"
            template = self.template_env.get_template(template_name)
            
            return template.render(**notification)
            
        except Exception:
            # Fallback to default subject
            return f"New {notification.get('type', 'Notification')}"
    
    def _render_html_template(self, notification: Dict, language: str = 'en') -> str:
        """Render HTML email template"""
        try:
            template_name = f"{notification['type']}_{language}.html"
            template = self.template_env.get_template(template_name)
            
            # Add common variables
            template_vars = {
                **notification,
                'site_name': 'AutoBot Solutions Forum',
                'site_url': 'https://yourdomain.com',
                'unsubscribe_url': f"https://yourdomain.com/unsubscribe",
                'current_year': datetime.utcnow().year
            }
            
            return template.render(**template_vars)
            
        except Exception as e:
            logger.error(f"Template rendering error: {str(e)}")
            return self._get_fallback_html_template(notification)
    
    def _render_text_template(self, notification: Dict, language: str = 'en') -> str:
        """Render text email template"""
        try:
            template_name = f"{notification['type']}_{language}.txt"
            template = self.template_env.get_template(template_name)
            
            # Add common variables
            template_vars = {
                **notification,
                'site_name': 'AutoBot Solutions Forum',
                'site_url': 'https://yourdomain.com'
            }
            
            return template.render(**template_vars)
            
        except Exception as e:
            logger.error(f"Text template rendering error: {str(e)}")
            return self._get_fallback_text_template(notification)
    
    def _get_fallback_html_template(self, notification: Dict) -> str:
        """Fallback HTML template"""
        return f"""
        <html>
        <body>
            <h2>New {notification.get('type', 'Notification')}</h2>
            <p>{notification.get('content', '')}</p>
            <p><a href="{notification.get('link', '#')}">View Details</a></p>
            <hr>
            <p><small>This is an automated notification from AutoBot Solutions Forum</small></p>
        </body>
        </html>
        """
    
    def _get_fallback_text_template(self, notification: Dict) -> str:
        """Fallback text template"""
        return f"""
        New {notification.get('type', 'Notification')}
        
        {notification.get('content', '')}
        
        View Details: {notification.get('link', '#')}
        
        ---
        This is an automated notification from AutoBot Solutions Forum
        """
    
    def _track_delivery(self, email_data: Dict, status: str):
        """Track email delivery status"""
        try:
            if self.redis_client:
                tracking_data = {
                    'email': email_data['to'],
                    'notification_id': email_data.get('notification_id'),
                    'notification_type': email_data.get('notification_type'),
                    'user_id': email_data.get('user_id'),
                    'status': status,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Store in Redis with expiration
                self.redis_client.setex(
                    f"email_tracking:{email_data.get('notification_id')}",
                    timedelta(days=30),
                    json.dumps(tracking_data)
                )
                
                # Update statistics
                stats_key = f"email_stats:{status}"
                self.redis_client.incr(stats_key)
                self.redis_client.expire(stats_key, timedelta(days=365))
                
        except Exception as e:
            logger.error(f"Error tracking delivery: {str(e)}")
    
    def get_delivery_statistics(self) -> Dict:
        """Get email delivery statistics"""
        try:
            stats = {
                'sent': self.delivery_stats['sent'],
                'failed': self.delivery_stats['failed'],
                'bounced': self.delivery_stats['bounced'],
                'opened': self.delivery_stats['opened'],
                'clicked': self.delivery_stats['clicked']
            }
            
            # Get Redis statistics
            if self.redis_client:
                for status in ['sent', 'failed', 'bounced', 'opened', 'clicked']:
                    key = f"email_stats:{status}"
                    count = self.redis_client.get(key)
                    if count:
                        stats[status] = int(count)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting delivery statistics: {str(e)}")
            return {}
    
    def track_email_open(self, notification_id: str):
        """Track email open event"""
        try:
            self.delivery_stats['opened'] += 1
            
            if self.redis_client:
                self.redis_client.incr(f"email_stats:opened")
                self.redis_client.expire(f"email_stats:opened", timedelta(days=365))
                
                # Update specific notification tracking
                tracking_key = f"email_tracking:{notification_id}"
                tracking_data = self.redis_client.get(tracking_key)
                if tracking_data:
                    data = json.loads(tracking_data)
                    data['opened_at'] = datetime.utcnow().isoformat()
                    self.redis_client.setex(
                        tracking_key,
                        timedelta(days=30),
                        json.dumps(data)
                    )
            
            logger.info(f"Email open tracked for notification {notification_id}")
            
        except Exception as e:
            logger.error(f"Error tracking email open: {str(e)}")
    
    def track_email_click(self, notification_id: str, url: str):
        """Track email click event"""
        try:
            self.delivery_stats['clicked'] += 1
            
            if self.redis_client:
                self.redis_client.incr(f"email_stats:clicked")
                self.redis_client.expire(f"email_stats:clicked", timedelta(days=365))
                
                # Update specific notification tracking
                tracking_key = f"email_tracking:{notification_id}"
                tracking_data = self.redis_client.get(tracking_key)
                if tracking_data:
                    data = json.loads(tracking_data)
                    data['clicked_at'] = datetime.utcnow().isoformat()
                    data['clicked_url'] = url
                    self.redis_client.setex(
                        tracking_key,
                        timedelta(days=30),
                        json.dumps(data)
                    )
            
            logger.info(f"Email click tracked for notification {notification_id}: {url}")
            
        except Exception as e:
            logger.error(f"Error tracking email click: {str(e)}")
    
    def retry_failed_emails(self):
        """Retry failed emails"""
        try:
            # This would typically be called by a scheduled job
            # Implementation depends on your failed email storage strategy
            logger.info("Retrying failed emails...")
            
            # Get failed emails from storage
            # Re-queue them with retry logic
            
        except Exception as e:
            logger.error(f"Error retrying failed emails: {str(e)}")
    
    def cleanup_old_tracking_data(self):
        """Clean up old tracking data"""
        try:
            if self.redis_client:
                # Clean up tracking data older than retention period
                pattern = "email_tracking:*"
                keys = self.redis_client.keys(pattern)
                
                for key in keys:
                    ttl = self.redis_client.ttl(key)
                    if ttl == -1:  # No expiration set
                        self.redis_client.expire(key, timedelta(days=30))
                
                logger.info(f"Cleaned up {len(keys)} tracking entries")
                
        except Exception as e:
            logger.error(f"Error cleaning up tracking data: {str(e)}")

# Global email service instance
email_notification_service = EmailNotificationService()
```

## Email Templates

### Template Structure

Create templates in `app/templates/email/notifications/`:

```
app/templates/email/notifications/
├── subjects/
│   ├── comment_en.txt
│   ├── message_en.txt
│   ├── system_en.txt
│   └── ...
├── comment_en.html
├── comment_en.txt
├── message_en.html
├── message_en.txt
├── system_en.html
├── system_en.txt
└── ...
```

### Example Templates

#### Comment Notification (HTML)
`app/templates/email/notifications/comment_en.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Comment</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .button { display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ site_name }}</h1>
            <p>New Comment Notification</p>
        </div>
        
        <div class="content">
            <h2>Hello {{ username }},</h2>
            
            <p>{{ username }} has commented on your post:</p>
            
            <blockquote>
                <p><strong>{{ post_title }}</strong></p>
                <p>{{ comment_content }}</p>
            </blockquote>
            
            <div style="text-align: center;">
                <a href="{{ site_url }}{{ link }}" class="button">View Comment</a>
            </div>
            
            <p>Best regards,<br>
            The {{ site_name }} Team</p>
        </div>
        
        <div class="footer">
            <p>&copy; {{ current_year }} {{ site_name }}. All rights reserved.</p>
            <p>
                <a href="{{ unsubscribe_url }}">Unsubscribe</a> | 
                <a href="{{ site_url }}/preferences">Notification Preferences</a>
            </p>
        </div>
    </div>
    
    <!-- Tracking pixel for open tracking -->
    <img src="{{ site_url }}/email/track-open/{{ notification_id }}" width="1" height="1" style="display:none;">
</body>
</html>
```

#### Comment Notification (Text)
`app/templates/email/notifications/comment_en.txt`:

```txt
New Comment Notification - {{ site_name }}

Hello {{ username }},

{{ username }} has commented on your post:

Post: {{ post_title }}
Comment: {{ comment_content }}

View the comment here: {{ site_url }}{{ link }}

Best regards,
The {{ site_name }} Team

---
{{ site_url }}
Unsubscribe: {{ unsubscribe_url }}
```

#### Subject Template
`app/templates/email/notifications/subjects/comment_en.txt`:

```txt
New Comment on "{{ post_title }}"
```

## Queue Management

### Celery Integration (Optional)

For advanced queue management, integrate with Celery:

```python
# app/tasks/email_tasks.py
from celery import Celery
from app.email.notification_service import email_notification_service

celery = Celery('email_tasks')

@celery.task(bind=True, max_retries=3)
def send_email_task(self, email_data):
    """Celery task for sending emails"""
    try:
        # Process email
        message = email_notification_service._create_email_message(email_data)
        success = email_notification_service._send_email(message, email_data['to'])
        
        if success:
            email_notification_service._track_delivery(email_data, 'sent')
        else:
            email_notification_service._track_delivery(email_data, 'failed')
        
        return {'success': success, 'to': email_data['to']}
        
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### Redis Queue Monitoring

Create `scripts/monitor_email_queue.py`:

```python
#!/usr/bin/env python3
"""
Email queue monitoring script
"""

import redis
import json
import time
from datetime import datetime
from app.config.notification_config import get_notification_config

def monitor_email_queue():
    """Monitor email queue status"""
    config = get_notification_config()
    
    try:
        redis_client = redis.from_url(
            config.redis_url,
            db=config.redis_notification_db,
            decode_responses=True
        )
        
        while True:
            try:
                # Get queue size
                queue_size = redis_client.llen('email_queue')
                
                # Get processing stats
                stats = {
                    'queue_size': queue_size,
                    'max_size': config.email_queue_max_size,
                    'workers': config.email_queue_workers,
                    'processing_interval': config.email_queue_processing_interval
                }
                
                # Get delivery statistics
                delivery_stats = {}
                for status in ['sent', 'failed', 'bounced', 'opened', 'clicked']:
                    key = f"email_stats:{status}"
                    count = redis_client.get(key)
                    delivery_stats[status] = int(count) if count else 0
                
                print(f"[{datetime.now()}] Email Queue Status:")
                print(f"  Queue Size: {stats['queue_size']}/{stats['max_size']}")
                print(f"  Workers: {stats['workers']}")
                print(f"  Processing Interval: {stats['processing_interval']}s")
                print(f"  Delivery Stats: {delivery_stats}")
                
                # Alert if queue is getting full
                if queue_size > stats['max_size'] * 0.8:
                    print(f"  WARNING: Queue is {queue_size/stats['max_size']*100:.1f}% full!")
                
                print("-" * 50)
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Error monitoring queue: {str(e)}")
                time.sleep(10)
                
    except Exception as e:
        print(f"Failed to connect to Redis: {str(e)}")

if __name__ == '__main__':
    monitor_email_queue()
```

## Delivery Tracking

### Open Tracking

Create tracking endpoint in `app/routes/email.py`:

```python
from flask import Blueprint, request, Response
from app.email.notification_service import email_notification_service

email_bp = Blueprint('email', __name__)

@email_bp.route('/email/track-open/<notification_id>')
def track_email_open(notification_id):
    """Track email open event"""
    email_notification_service.track_email_open(notification_id)
    
    # Return 1x1 transparent pixel
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x00\xf9\x43\x4e\x2d\x01\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x3f\x3f\x3f\x21\xf9\x04\x01\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3b'
    return Response(pixel, mimetype='image/gif')
```

### Click Tracking

```python
@email_bp.route('/email/track-click/<notification_id>')
def track_email_click(notification_id):
    """Track email click event"""
    url = request.args.get('url', '')
    email_notification_service.track_email_click(notification_id, url)
    
    # Redirect to original URL
    if url.startswith('http'):
        return redirect(url)
    else:
        return redirect(url or '/')
```

## Testing

### Email Service Tests

Create `tests/test_email_service.py`:

```python
import unittest
from unittest.mock import Mock, patch
from app.email.notification_service import EmailNotificationService

class TestEmailNotificationService(unittest.TestCase):
    
    def setUp(self):
        self.email_service = EmailNotificationService()
    
    def test_send_notification_email(self):
        """Test sending notification email"""
        notification = {
            'id': 1,
            'type': 'comment',
            'content': 'Test comment',
            'username': 'test_user',
            'post_title': 'Test Post'
        }
        
        result = self.email_service.send_notification_email(
            notification, 
            'test@example.com'
        )
        
        self.assertTrue(result)
    
    def test_send_bulk_emails(self):
        """Test sending bulk emails"""
        notifications = [
            {'id': 1, 'type': 'comment', 'content': 'Comment 1'},
            {'id': 2, 'type': 'message', 'content': 'Message 1'}
        ]
        recipients = ['user1@example.com', 'user2@example.com']
        
        result = self.email_service.send_bulk_emails(
            notifications, 
            recipients
        )
        
        self.assertEqual(result['queued'], 2)
        self.assertEqual(result['failed'], 0)
    
    def test_template_rendering(self):
        """Test email template rendering"""
        notification = {
            'id': 1,
            'type': 'comment',
            'content': 'Test comment',
            'username': 'test_user',
            'post_title': 'Test Post'
        }
        
        html_content = self.email_service._render_html_template(notification)
        text_content = self.email_service._render_text_template(notification)
        
        self.assertIsInstance(html_content, str)
        self.assertIsInstance(text_content, str)
        self.assertIn('Test comment', html_content)
        self.assertIn('Test comment', text_content)
    
    def test_delivery_tracking(self):
        """Test delivery tracking"""
        email_data = {
            'to': 'test@example.com',
            'notification_id': 1,
            'notification_type': 'comment',
            'user_id': 123
        }
        
        # Test tracking
        self.email_service._track_delivery(email_data, 'sent')
        
        # Test statistics
        stats = self.email_service.get_delivery_statistics()
        self.assertIn('sent', stats)
    
    @patch('smtplib.SMTP')
    def test_smtp_sending(self, mock_smtp):
        """Test SMTP email sending"""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        # Test email sending
        message = self.email_service._create_email_message({
            'to': 'test@example.com',
            'subject': 'Test Subject',
            'html_body': '<p>Test HTML</p>',
            'text_body': 'Test text'
        })
        
        result = self.email_service._send_email(message, 'test@example.com')
        
        self.assertTrue(result)
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()

if __name__ == '__main__':
    unittest.main()
```

## Production Deployment

### Production Configuration

```bash
# Production email settings
EMAIL_NOTIFICATION_ENABLED=true
SMTP_NOTIFICATION_SERVER=smtp.sendgrid.net
SMTP_NOTIFICATION_PORT=587
SMTP_NOTIFICATION_USE_TLS=true
SMTP_NOTIFICATION_USERNAME=apikey
SMTP_NOTIFICATION_PASSWORD=your-production-api-key

# Queue settings for production
EMAIL_QUEUE_ENABLED=true
EMAIL_QUEUE_WORKERS=8
EMAIL_QUEUE_MAX_SIZE=5000
EMAIL_QUEUE_PROCESSING_INTERVAL=10
EMAIL_NOTIFICATION_BATCH_SIZE=100

# Tracking enabled
EMAIL_DELIVERY_TRACKING_ENABLED=true
EMAIL_OPEN_TRACKING_ENABLED=true
EMAIL_CLICK_TRACKING_ENABLED=true
```

### Docker Deployment

Add to `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - EMAIL_NOTIFICATION_ENABLED=true
      - SMTP_NOTIFICATION_SERVER=${SMTP_SERVER}
      - SMTP_NOTIFICATION_USERNAME=${SMTP_USERNAME}
      - SMTP_NOTIFICATION_PASSWORD=${SMTP_PASSWORD}
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  email-worker:
    build: .
    command: python scripts/email_worker.py
    environment:
      - EMAIL_NOTIFICATION_ENABLED=true
      - SMTP_NOTIFICATION_SERVER=${SMTP_SERVER}
      - SMTP_NOTIFICATION_USERNAME=${SMTP_USERNAME}
      - SMTP_NOTIFICATION_PASSWORD=${SMTP_PASSWORD}
    depends_on:
      - redis
    restart: unless-stopped
    deploy:
      replicas: 4

volumes:
  redis_data:
```

### Monitoring and Alerting

Create `scripts/email_health_check.py`:

```python
#!/usr/bin/env python3
"""
Email service health check
"""

import requests
import sys
from app.email.notification_service import email_notification_service

def check_email_health():
    """Check email service health"""
    try:
        # Check queue status
        stats = email_notification_service.get_delivery_statistics()
        
        # Check Redis connection
        redis_status = email_notification_service.redis_client is not None
        
        # Check template environment
        template_status = email_notification_service.template_env is not None
        
        print(f"Email Service Health:")
        print(f"  Redis Connection: {'OK' if redis_status else 'FAILED'}")
        print(f"  Template Environment: {'OK' if template_status else 'FAILED'}")
        print(f"  Queue Workers: {len(email_notification_service.queue_workers)}")
        print(f"  Delivery Stats: {stats}")
        
        # Return health status
        if redis_status and template_status:
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        return 2

if __name__ == '__main__':
    sys.exit(check_email_health())
```

## Troubleshooting

### Common Issues

1. **SMTP Authentication Failed**
   - Check API key/credentials
   - Verify SMTP server and port
   - Ensure TLS/SSL settings are correct

2. **Template Not Found**
   - Check template file paths
   - Verify template file permissions
   - Check template syntax

3. **Queue Not Processing**
   - Check Redis connection
   - Verify queue workers are running
   - Check worker logs for errors

4. **High Bounce Rate**
   - Verify email domain DNS records
   - Check email content for spam triggers
   - Monitor sender reputation

### Debug Mode

Enable debug logging:

```bash
export NOTIFICATION_DEBUG=true
export EMAIL_DEBUG=true
python -c "from app.email.notification_service import email_notification_service; print('Email service initialized')"
```

---

**Last Updated:** May 12, 2026  
**Version:** 1.0  
**Status:** Production Ready
