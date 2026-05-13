"""
Email Queue Management Module

Handles email queue processing, retry logic, and queue monitoring
for the Auto Bot Solutions Forum email system.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from flask import current_app
from .service import email_service

logger = logging.getLogger(__name__)

class EmailQueueProcessor:
    """Background processor for email queue"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.processing_interval = 30  # seconds
    
    def start(self):
        """Start the queue processor thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process_loop, daemon=True)
            self.thread.start()
            logger.info("Email queue processor started")
    
    def stop(self):
        """Stop the queue processor thread"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=10)
            logger.info("Email queue processor stopped")
    
    def _process_loop(self):
        """Main processing loop for email queue"""
        while self.running:
            try:
                processed = email_service.process_queue()
                if processed > 0:
                    logger.info(f"Processed {processed} emails from queue")
                
                # Sleep before next processing cycle
                time.sleep(self.processing_interval)
                
            except Exception as e:
                logger.error(f"Error in email queue processing loop: {str(e)}")
                time.sleep(self.processing_interval)
    
    def get_status(self) -> Dict:
        """Get queue processor status"""
        return {
            'running': self.running,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'queue_status': email_service.get_queue_status()
        }

# Global queue processor instance
queue_processor = EmailQueueProcessor()

class EmailQueueManager:
    """Manager for email queue operations"""
    
    @staticmethod
    def send_verification_email(user, verification_url) -> bool:
        """Send verification email"""
        try:
            context = {
                'user': user,
                'verification_url': verification_url
            }
            
            return email_service.send_email(
                to_email=user.email,
                subject='Verify Your Email - Auto Bot Solutions Forum',
                template='verification',
                context=context,
                priority='high'  # Verification emails are high priority
            )
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(user, reset_url) -> bool:
        """Send password reset email"""
        try:
            context = {
                'user': user,
                'reset_url': reset_url
            }
            
            return email_service.send_email(
                to_email=user.email,
                subject='Reset Your Password - Auto Bot Solutions Forum',
                template='password_reset',
                context=context,
                priority='high'  # Password reset emails are high priority
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user) -> bool:
        """Send welcome email after verification"""
        try:
            context = {
                'user': user,
                'login_url': f"{current_app.config.get('SERVER_NAME', 'localhost:5000')}/login"
            }
            
            return email_service.send_email(
                to_email=user.email,
                subject='Welcome to Auto Bot Solutions Forum!',
                template='welcome',
                context=context,
                priority='normal'
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_security_alert_email(user, alert_type, details: Dict) -> bool:
        """Send security alert email"""
        try:
            context = {
                'user': user,
                'alert_type': alert_type,
                'details': details,
                'timestamp': datetime.utcnow()
            }
            
            return email_service.send_email(
                to_email=user.email,
                subject=f'Security Alert - {alert_type}',
                template='security_alert',
                context=context,
                priority='high'
            )
        except Exception as e:
            logger.error(f"Failed to send security alert email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def get_queue_statistics() -> Dict:
        """Get comprehensive queue statistics"""
        try:
            status = email_service.get_queue_status()
            processor_status = queue_processor.get_status()
            
            return {
                'queue_status': status,
                'processor_status': processor_status,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get queue statistics: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def preview_email(template: str, context: Dict, format_type: str = 'html') -> str:
        """Preview email template"""
        try:
            return email_service.preview_email(template, context, format_type)
        except Exception as e:
            logger.error(f"Failed to preview email template: {str(e)}")
            return f"Error previewing template: {str(e)}"
