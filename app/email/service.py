"""
Email Service Module

Handles email sending, template rendering, queue management,
and error handling for the Auto Bot Solutions Forum.
"""

import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from flask import current_app, render_template
from sqlalchemy.exc import SQLAlchemyError
import redis
import json
import traceback

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for handling email operations"""
    
    def __init__(self):
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection for email queue"""
        try:
            if current_app.config.get('MAIL_QUEUE_ENABLED'):
                self.redis_client = redis.from_url(
                    current_app.config.get('MAIL_QUEUE_URL', 'redis://localhost:6379/0')
                )
                self.redis_client.ping()
                logger.info("Email queue Redis connection established")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis for email queue: {e}")
            self.redis_client = None
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        template: str,
        context: Dict[str, Any],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: str = 'normal'
    ) -> bool:
        """
        Send email using template
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template: Template name (without .html)
            context: Template context variables
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            attachments: List of attachment dictionaries (optional)
            priority: Email priority ('low', 'normal', 'high')
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if email sending is suppressed
            if current_app.config.get('MAIL_SUPPRESS_SEND'):
                logger.info(f"Email sending suppressed. Would send to {to_email}: {subject}")
                return True
            
            # Queue email if queue is enabled
            if self.redis_client and priority != 'high':
                return self._queue_email(
                    to_email, subject, template, context, cc, bcc, attachments, priority
                )
            
            # Send email immediately
            return self._send_immediately(
                to_email, subject, template, context, cc, bcc, attachments
            )
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _send_immediately(
        self,
        to_email: str,
        subject: str,
        template: str,
        context: Dict[str, Any],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email immediately without queuing"""
        try:
            # Render template
            html_content = render_template(f'email/{template}.html', **context)
            text_content = render_template(f'email/{template}.txt', **context)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = current_app.config.get('MAIL_DEFAULT_SENDER')
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Send email
            return self._send_with_smtp(msg, [to_email] + (cc or []) + (bcc or []))
            
        except Exception as e:
            logger.error(f"Failed to send email immediately: {str(e)}")
            return False
    
    def _queue_email(
        self,
        to_email: str,
        subject: str,
        template: str,
        context: Dict[str, Any],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: str = 'normal'
    ) -> bool:
        """Queue email for later sending"""
        try:
            email_data = {
                'to_email': to_email,
                'subject': subject,
                'template': template,
                'context': context,
                'cc': cc,
                'bcc': bcc,
                'attachments': attachments,
                'priority': priority,
                'attempts': 0,
                'created_at': datetime.utcnow().isoformat(),
                'next_retry': datetime.utcnow().isoformat()
            }
            
            # Add to queue based on priority
            queue_key = f'email_queue:{priority}'
            self.redis_client.lpush(queue_key, json.dumps(email_data))
            
            logger.info(f"Email queued for {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue email: {str(e)}")
            return False
    
    def _send_with_smtp(self, msg: MIMEMultipart, recipients: List[str]) -> bool:
        """Send email using SMTP"""
        try:
            server = smtplib.SMTP(
                current_app.config.get('MAIL_SERVER'),
                current_app.config.get('MAIL_PORT')
            )
            
            if current_app.config.get('MAIL_USE_TLS'):
                server.starttls()
            
            if current_app.config.get('MAIL_USERNAME') and current_app.config.get('MAIL_PASSWORD'):
                server.login(
                    current_app.config.get('MAIL_USERNAME'),
                    current_app.config.get('MAIL_PASSWORD')
                )
            
            # Send email
            server.sendmail(
                current_app.config.get('MAIL_DEFAULT_SENDER'),
                recipients,
                msg.as_string()
            )
            
            server.quit()
            logger.info(f"Email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP send failed: {str(e)}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email"""
        try:
            part = MIMEBase(
                attachment.get('maintype', 'application'),
                attachment.get('subtype', 'octet-stream')
            )
            
            part.set_payload(attachment.get('payload'))
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment.get("filename", "attachment")}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment: {str(e)}")
    
    def process_queue(self) -> int:
        """Process email queue and send queued emails"""
        if not self.redis_client:
            logger.warning("Redis not available for queue processing")
            return 0
        
        processed = 0
        max_attempts = current_app.config.get('MAIL_RETRY_ATTEMPTS', 3)
        retry_delay = current_app.config.get('MAIL_RETRY_DELAY', 60)
        
        # Process queues by priority
        priorities = ['high', 'normal', 'low']
        
        for priority in priorities:
            queue_key = f'email_queue:{priority}'
            
            while True:
                try:
                    # Get email from queue
                    email_data_json = self.redis_client.rpop(queue_key)
                    if not email_data_json:
                        break
                    
                    email_data = json.loads(email_data_json)
                    
                    # Check if it's time to retry
                    next_retry = datetime.fromisoformat(email_data['next_retry'])
                    if datetime.utcnow() < next_retry:
                        # Put back in queue
                        self.redis_client.lpush(queue_key, email_data_json)
                        break
                    
                    # Send email
                    success = self._send_immediately(
                        email_data['to_email'],
                        email_data['subject'],
                        email_data['template'],
                        email_data['context'],
                        email_data['cc'],
                        email_data['bcc'],
                        email_data['attachments']
                    )
                    
                    if success:
                        processed += 1
                        logger.info(f"Queued email sent successfully to {email_data['to_email']}")
                    else:
                        # Handle retry logic
                        email_data['attempts'] += 1
                        
                        if email_data['attempts'] < max_attempts:
                            # Schedule retry
                            next_retry = datetime.utcnow() + timedelta(seconds=retry_delay)
                            email_data['next_retry'] = next_retry.isoformat()
                            
                            # Put back in queue
                            self.redis_client.lpush(queue_key, json.dumps(email_data))
                            logger.warning(f"Email failed, retry {email_data['attempts']}/{max_attempts}")
                        else:
                            # Max attempts reached, move to failed queue
                            failed_queue_key = 'email_queue:failed'
                            self.redis_client.lpush(failed_queue_key, email_data_json)
                            logger.error(f"Email failed permanently after {max_attempts} attempts")
                
                except Exception as e:
                    logger.error(f"Error processing queue: {str(e)}")
                    break
        
        return processed
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get email queue status"""
        if not self.redis_client:
            return {'error': 'Redis not available'}
        
        status = {}
        priorities = ['high', 'normal', 'low']
        
        for priority in priorities:
            queue_key = f'email_queue:{priority}'
            status[priority] = self.redis_client.llen(queue_key)
        
        # Add failed queue count
        status['failed'] = self.redis_client.llen('email_queue:failed')
        
        return status
    
    def preview_email(
        self,
        template: str,
        context: Dict[str, Any],
        format_type: str = 'html'
    ) -> str:
        """Preview email template without sending"""
        try:
            if format_type == 'html':
                return render_template(f'email/{template}.html', **context)
            else:
                return render_template(f'email/{template}.txt', **context)
        except Exception as e:
            logger.error(f"Failed to preview email template: {str(e)}")
            return f"Error previewing template: {str(e)}"

# Global email service instance
email_service = EmailService()
