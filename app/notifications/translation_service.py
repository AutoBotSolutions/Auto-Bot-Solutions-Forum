"""
Notification Translation Service

This module provides translation capabilities for notifications,
supporting multiple languages and localization features.
"""

from datetime import datetime
from flask import current_app
from flask_babel import gettext, ngettext
import json
import re
from typing import Dict, List, Optional, Tuple

from app.models import User


class NotificationTranslationService:
    """Service for translating notifications to user's preferred language"""
    
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano',
            'pt': 'Português',
            'ru': 'Русский',
            'zh': '中文',
            'ja': '日本語',
            'ko': '한국어',
            'ar': 'العربية',
            'hi': 'हिन्दी'
        }
        
        # Translation templates for common notification types
        self.translation_templates = {
            'comment': {
                'en': '{username} commented on your post "{post_title}"',
                'es': '{username} comentó en tu publicación "{post_title}"',
                'fr': '{username} a commenté votre publication "{post_title}"',
                'de': '{username} hat deinen Beitrag "{post_title}" kommentiert',
                'it': '{username} ha commentato il tuo post "{post_title}"',
                'pt': '{username} comentou em seu post "{post_title}"',
                'ru': '{username} прокомментировал вашу публикацию "{post_title}"',
                'zh': '{username} 评论了你的帖子 "{post_title}"',
                'ja': '{username}があなたの投稿「{post_title}」にコメントしました',
                'ko': '{username}님이 게시물 "{post_title}"에 댓글을 달았습니다',
                'ar': '{username} علق على منشورك "{post_title}"',
                'hi': '{username} ने आपकी पोस्ट "{post_title}" पर टिप्पणी की'
            },
            'message': {
                'en': 'You have a new message from {sender_name}',
                'es': 'Tienes un nuevo mensaje de {sender_name}',
                'fr': 'Vous avez un nouveau message de {sender_name}',
                'de': 'Sie haben eine neue Nachricht von {sender_name}',
                'it': 'Hai un nuovo messaggio da {sender_name}',
                'pt': 'Você tem uma nova mensagem de {sender_name}',
                'ru': 'У вас новое сообщение от {sender_name}',
                'zh': '您收到来自 {sender_name} 的新消息',
                'ja': '{sender_name}から新しいメッセージがあります',
                'ko': '{sender_name}님으로부터 새 메시지가 있습니다',
                'ar': 'لديك رسالة جديدة من {sender_name}',
                'hi': 'आपके पास {sender_name} से एक नया संदेश है'
            },
            'system': {
                'en': 'System notification: {message}',
                'es': 'Notificación del sistema: {message}',
                'fr': 'Notification système : {message}',
                'de': 'Systembenachrichtigung: {message}',
                'it': 'Notifica di sistema: {message}',
                'pt': 'Notificação do sistema: {message}',
                'ru': 'Системное уведомление: {message}',
                'zh': '系统通知：{message}',
                'ja': 'システム通知：{message}',
                'ko': '시스템 알림: {message}',
                'ar': 'إشعار النظام: {message}',
                'hi': 'सिस्टम अधिसूचना: {message}'
            },
            'moderation': {
                'en': 'Moderation action: {action} on {content_type}',
                'es': 'Acción de moderación: {action} en {content_type}',
                'fr': 'Action de modération : {action} sur {content_type}',
                'de': 'Moderationsaktion: {action} auf {content_type}',
                'it': 'Azione di moderazione: {action} su {content_type}',
                'pt': 'Ação de moderação: {action} em {content_type}',
                'ru': 'Действие модерации: {action} над {content_type}',
                'zh': '审核操作：{action} 在 {content_type}',
                'ja': 'モデレーション操作：{content_type}に{action}',
                'ko': '중재 작업: {content_type}에 {action}',
                'ar': 'إجراء الإشراف: {action} على {content_type}',
                'hi': 'मॉडरेशन कार्रवाई: {content_type} पर {action}'
            },
            'security': {
                'en': 'Security alert: {alert_type}',
                'es': 'Alerta de seguridad: {alert_type}',
                'fr': 'Alerte de sécurité : {alert_type}',
                'de': 'Sicherheitswarnung: {alert_type}',
                'it': 'Allarme di sicurezza: {alert_type}',
                'pt': 'Alerta de segurança: {alert_type}',
                'ru': 'Предупреждение безопасности: {alert_type}',
                'zh': '安全警报：{alert_type}',
                'ja': 'セキュリティアラート：{alert_type}',
                'ko': '보안 알림: {alert_type}',
                'ar': 'تنبيه أمني: {alert_type}',
                'hi': 'सुरक्षा चेतावनी: {alert_type}'
            }
        }
        
        # Common action translations
        self.action_translations = {
            'approved': {
                'en': 'approved',
                'es': 'aprobado',
                'fr': 'approuvé',
                'de': 'genehmigt',
                'it': 'approvato',
                'pt': 'aprovado',
                'ru': 'одобрено',
                'zh': '已批准',
                'ja': '承認済み',
                'ko': '승인됨',
                'ar': 'موافق عليه',
                'hi': 'स्वीकृत'
            },
            'rejected': {
                'en': 'rejected',
                'es': 'rechazado',
                'fr': 'rejeté',
                'de': 'abgelehnt',
                'it': 'rifiutato',
                'pt': 'rejeitado',
                'ru': 'отклонено',
                'zh': '已拒绝',
                'ja': '拒否されました',
                'ko': '거부됨',
                'ar': 'مرفوض',
                'hi': 'अस्वीकृत'
            },
            'deleted': {
                'en': 'deleted',
                'es': 'eliminado',
                'fr': 'supprimé',
                'de': 'gelöscht',
                'it': 'eliminato',
                'pt': 'excluído',
                'ru': 'удалено',
                'zh': '已删除',
                'ja': '削除されました',
                'ko': '삭제됨',
                'ar': 'تم حذفه',
                'hi': 'हटा दिया गया'
            },
            'flagged': {
                'en': 'flagged',
                'es': 'marcado',
                'fr': 'signalé',
                'de': 'markiert',
                'it': 'segnalato',
                'pt': 'marcado',
                'ru': 'помечено',
                'zh': '已标记',
                'ja': 'フラグが付けられました',
                'ko': '플래그 지정됨',
                'ar': 'تم وضع علامة',
                'hi': 'चिह्नित'
            }
        }
    
    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        try:
            user = User.query.get(user_id)
            if user and hasattr(user, 'language_preference'):
                return user.language_preference or 'en'
            
            # Check if user has language preference in profile
            if user and hasattr(user, 'profile') and user.profile:
                return user.profile.language or 'en'
            
            return 'en'  # Default to English
        except Exception:
            return 'en'
    
    def translate_notification(self, notification_data: Dict, user_id: int) -> Dict:
        """Translate notification to user's preferred language"""
        try:
            user_language = self.get_user_language(user_id)
            
            # If user prefers English or language not supported, return original
            if user_language == 'en' or user_language not in self.supported_languages:
                return notification_data
            
            # Create a copy to avoid modifying original
            translated_data = notification_data.copy()
            
            # Translate title/content based on notification type
            notification_type = notification_data.get('type', 'system')
            
            if notification_type in self.translation_templates:
                template = self.translation_templates[notification_type].get(user_language)
                if template:
                    # Extract variables from the original content
                    variables = self._extract_variables(notification_data)
                    translated_content = template.format(**variables)
                    translated_data['content'] = translated_content
            
            # Translate action if present
            if 'action' in notification_data:
                action = notification_data['action']
                if action in self.action_translations:
                    translated_action = self.action_translations[action].get(user_language, action)
                    translated_data['action'] = translated_action
            
            # Add translation metadata
            translated_data['translated'] = True
            translated_data['original_language'] = 'en'
            translated_data['target_language'] = user_language
            
            return translated_data
            
        except Exception as e:
            current_app.logger.error(f"Translation error: {str(e)}")
            # Return original data if translation fails
            return notification_data
    
    def _extract_variables(self, notification_data: Dict) -> Dict:
        """Extract variables from notification data for template substitution"""
        variables = {}
        
        # Common variables
        if 'username' in notification_data:
            variables['username'] = notification_data['username']
        if 'sender_name' in notification_data:
            variables['sender_name'] = notification_data['sender_name']
        if 'post_title' in notification_data:
            variables['post_title'] = notification_data['post_title']
        if 'message' in notification_data:
            variables['message'] = notification_data['message']
        if 'action' in notification_data:
            variables['action'] = notification_data['action']
        if 'content_type' in notification_data:
            variables['content_type'] = notification_data['content_type']
        if 'alert_type' in notification_data:
            variables['alert_type'] = notification_data['alert_type']
        
        # Try to extract from content if not directly available
        content = notification_data.get('content', '')
        
        # Extract username from common patterns
        username_match = re.search(r'(\w+)\s+(?:commented|messaged|posted)', content, re.IGNORECASE)
        if username_match and 'username' not in variables:
            variables['username'] = username_match.group(1)
        
        # Extract post title from quotes
        title_match = re.search(r'"([^"]+)"', content)
        if title_match and 'post_title' not in variables:
            variables['post_title'] = title_match.group(1)
        
        return variables
    
    def translate_bulk_notifications(self, notifications: List[Dict], user_id: int) -> List[Dict]:
        """Translate multiple notifications for a user"""
        translated_notifications = []
        
        for notification in notifications:
            translated = self.translate_notification(notification, user_id)
            translated_notifications.append(translated)
        
        return translated_notifications
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get all supported languages"""
        return self.supported_languages.copy()
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if a language is supported"""
        return language_code in self.supported_languages
    
    def set_user_language_preference(self, user_id: int, language_code: str) -> bool:
        """Set user's language preference"""
        try:
            if not self.is_language_supported(language_code):
                return False
            
            user = User.query.get(user_id)
            if user:
                # Store language preference in user profile or preferences
                if hasattr(user, 'language_preference'):
                    user.language_preference = language_code
                elif hasattr(user, 'profile') and user.profile:
                    user.profile.language = language_code
                else:
                    # Store in JSON preferences if no dedicated field
                    preferences = {}
                    if hasattr(user, 'preferences') and user.preferences:
                        try:
                            preferences = json.loads(user.preferences) if isinstance(user.preferences, str) else user.preferences
                        except:
                            pass
                    
                    preferences['language'] = language_code
                    user.preferences = json.dumps(preferences)
                
                from app import db
                db.session.commit()
                return True
            
            return False
        except Exception as e:
            current_app.logger.error(f"Error setting language preference: {str(e)}")
            return False
    
    def translate_text(self, text: str, target_language: str, source_language: str = 'en') -> str:
        """Simple text translation using templates (for basic phrases)"""
        try:
            if target_language == source_language:
                return text
            
            # Check if text matches any known patterns
            for notification_type, templates in self.translation_templates.items():
                for lang, template in templates.items():
                    if lang == source_language:
                        # Try to match the pattern
                        variables = self._extract_variables_from_text(text, template)
                        if variables:
                            target_template = templates.get(target_language)
                            if target_template:
                                return target_template.format(**variables)
            
            # Return original text if no pattern match found
            return text
        except Exception as e:
            current_app.logger.error(f"Text translation error: {str(e)}")
            return text
    
    def _extract_variables_from_text(self, text: str, template: str) -> Optional[Dict]:
        """Extract variables from text based on template pattern"""
        try:
            # Simple pattern matching for {variable} placeholders
            template_vars = re.findall(r'\{(\w+)\}', template)
            if not template_vars:
                return None
            
            # This is a simplified approach - in production, you'd use more sophisticated NLP
            variables = {}
            
            # Extract username
            username_match = re.search(r'(\w+)', text)
            if username_match and 'username' in template_vars:
                variables['username'] = username_match.group(1)
            
            # Extract quoted content
            quoted_match = re.search(r'"([^"]+)"', text)
            if quoted_match and 'post_title' in template_vars:
                variables['post_title'] = quoted_match.group(1)
            
            # Extract sender name
            sender_match = re.search(r'from\s+(\w+)', text, re.IGNORECASE)
            if sender_match and 'sender_name' in template_vars:
                variables['sender_name'] = sender_match.group(1)
            
            return variables if variables else None
        except Exception:
            return None
    
    def get_translation_statistics(self) -> Dict:
        """Get translation usage statistics"""
        try:
            # This would typically query a database for translation metrics
            # For now, return basic info
            return {
                'supported_languages': len(self.supported_languages),
                'available_languages': list(self.supported_languages.keys()),
                'template_types': list(self.translation_templates.keys()),
                'action_types': list(self.action_translations.keys())
            }
        except Exception as e:
            current_app.logger.error(f"Error getting translation statistics: {str(e)}")
            return {}


# Singleton instance
notification_translation_service = NotificationTranslationService()
