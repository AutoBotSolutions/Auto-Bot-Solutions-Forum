"""
Rich Text Formatting Utilities

Provides comprehensive rich text functionality including:
- WYSIWYG editor integration
- HTML sanitization and security
- Markdown processing
- Emoji and sticker support
- Message templates
- Content preview functionality
"""

import re
import json
import bleach
import markdown
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import current_app
from markupsafe import Markup
from app import db
from app.models import User


class RichTextProcessor:
    """Advanced rich text processor with security and formatting capabilities"""
    
    def __init__(self):
        self.allowed_tags = self._get_allowed_tags()
        self.allowed_attributes = self._get_allowed_attributes()
        self.allowed_styles = self._get_allowed_styles()
        self.emoji_map = self._load_emoji_map()
        self.template_variables = self._load_template_variables()
    
    def _get_allowed_tags(self) -> set:
        """Get allowed HTML tags for sanitization"""
        return {
            'p', 'br', 'strong', 'em', 'u', 'i', 'b', 'span', 'div',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'dl', 'dt', 'dd',
            'blockquote', 'pre', 'code',
            'a', 'img',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'hr', 'sub', 'sup', 'small', 'del', 'ins'
        }
    
    def _get_allowed_attributes(self) -> dict:
        """Get allowed HTML attributes for sanitization"""
        return {
            '*': ['class', 'id', 'style'],
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'td': ['colspan', 'rowspan'],
            'th': ['colspan', 'rowspan'],
            'blockquote': ['cite']
        }
    
    def _get_allowed_styles(self) -> set:
        """Get allowed CSS styles"""
        return {
            'color', 'background-color', 'font-size', 'font-weight',
            'font-style', 'text-decoration', 'text-align',
            'margin', 'padding', 'border', 'display'
        }
    
    def _load_emoji_map(self) -> dict:
        """Load emoji mapping for text to emoji conversion"""
        return {
            # Basic emojis
            ':smile:': '😊',
            ':laugh:': '😂',
            ':heart:': '❤️',
            ':thumbsup:': '👍',
            ':thumbsdown:': '👎',
            ':fire:': '🔥',
            ':star:': '⭐',
            ':check:': '✅',
            ':x:': '❌',
            ':warning:': '⚠️',
            ':info:': 'ℹ️',
            ':question:': '❓',
            ':exclamation:': '❗',
            ':thinking:': '🤔',
            ':ok:': '👌',
            ':wave:': '👋',
            ':pray:': '🙏',
            ':clap:': '👏',
            ':party:': '🎉',
            ':gift:': '🎁',
            ':rocket:': '🚀',
            ':bulb:': '💡',
            ':coffee:': '☕',
            ':pizza:': '🍕',
            ':beer:': '🍺',
            ':cake:': '🎂',
            ':heart_eyes:': '😍',
            ':cry:': '😢',
            ':angry:': '😠',
            ':cool:': '😎',
            ':sleepy:': '😴',
            ':sick:': '🤒',
            ':happy:': '😄',
            ':sad:': '😢',
            ':love:': '😍',
            ':hate:': '😠'
        }
    
    def _load_template_variables(self) -> dict:
        """Load common template variables"""
        return {
            'username': lambda: current_user.username if current_user.is_authenticated else 'Guest',
            'user_email': lambda: current_user.email if current_user.is_authenticated else '',
            'current_date': lambda: datetime.now().strftime('%Y-%m-%d'),
            'current_time': lambda: datetime.now().strftime('%H:%M:%S'),
            'forum_name': lambda: current_app.config.get('FORUM_NAME', 'Auto Bot Solutions Forum'),
            'site_url': lambda: current_app.config.get('SITE_URL', 'http://localhost:5000')
        }
    
    def process_rich_text(
        self,
        content: str,
        content_format: str = 'html',
        sanitize: bool = True,
        enable_emoji: bool = True,
        enable_markdown: bool = True
    ) -> Tuple[str, str]:
        """
        Process rich text content based on format
        
        Args:
            content: Raw content
            content_format: Input format ('text', 'html', 'markdown')
            sanitize: Whether to sanitize HTML
            enable_emoji: Whether to convert emoji shortcodes
            enable_markdown: Whether to process markdown
        
        Returns:
            Tuple of (processed_html, plain_text)
        """
        if not content:
            return '', ''
        
        # Convert based on input format
        if content_format == 'markdown' and enable_markdown:
            html_content = self._process_markdown(content)
        elif content_format == 'text':
            html_content = self._text_to_html(content)
        else:
            html_content = content
        
        # Sanitize HTML
        if sanitize:
            html_content = self._sanitize_html(html_content)
        
        # Convert emoji shortcodes
        if enable_emoji:
            html_content = self._convert_emoji(html_content)
        
        # Generate plain text version
        plain_text = self._html_to_text(html_content)
        
        return html_content, plain_text
    
    def _process_markdown(self, content: str) -> str:
        """Process markdown content to HTML"""
        # Configure markdown processor
        md = markdown.Markdown(
            extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',
                'markdown.extensions.tables',
                'markdown.extensions.fenced_code',
                'markdown.extensions.footnotes',
                'markdown.extensions.attr_list',
                'markdown.extensions.def_list',
                'markdown.extensions.abbr',
                'markdown.extensions.md_in_html'
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True
                }
            }
        )
        
        return md.convert(content)
    
    def _text_to_html(self, content: str) -> str:
        """Convert plain text to basic HTML"""
        # Escape HTML entities
        content = bleach.clean(content, tags=[], strip=True)
        
        # Convert line breaks to <br>
        content = content.replace('\n', '<br>')
        
        # Convert URLs to links
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        content = re.sub(url_pattern, r'<a href="\g<0>" target="_blank">\g<0></a>', content)
        
        return content
    
    def _sanitize_html(self, content: str) -> str:
        """Sanitize HTML content for security"""
        try:
            # Try with styles parameter (newer bleach versions)
            return bleach.clean(
                content,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                styles=self.allowed_styles,
                strip=True
            )
        except TypeError:
            # Fallback for older bleach versions without styles support
            return bleach.clean(
                content,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                strip=True
            )
    
    def _convert_emoji(self, content: str) -> str:
        """Convert emoji shortcodes to actual emojis"""
        for shortcode, emoji in self.emoji_map.items():
            content = content.replace(shortcode, emoji)
        return content
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text"""
        # Simple HTML to text conversion
        text = re.sub(r'<[^>]+>', '', html_content)
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        return text.strip()
    
    def generate_preview(
        self,
        content: str,
        max_length: int = 200,
        content_format: str = 'html'
    ) -> str:
        """
        Generate a preview of content
        
        Args:
            content: Content to preview
            max_length: Maximum preview length
            content_format: Content format
        
        Returns:
            Preview text
        """
        if not content:
            return ''
        
        # Convert to plain text
        if content_format == 'html':
            plain_text = self._html_to_text(content)
        elif content_format == 'markdown':
            html_content, plain_text = self.process_rich_text(content, 'markdown')
        else:
            plain_text = content
        
        # Truncate to max length
        if len(plain_text) > max_length:
            plain_text = plain_text[:max_length].rstrip()
            plain_text += '...'
        
        return plain_text
    
    def validate_formatting(self, content: str, content_format: str) -> Dict:
        """
        Validate rich text content
        
        Args:
            content: Content to validate
            content_format: Format of content
        
        Returns:
            Validation result dictionary
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            # Process content
            html_content, plain_text = self.process_rich_text(content, content_format)
            
            # Basic statistics
            result['stats'] = {
                'character_count': len(plain_text),
                'word_count': len(plain_text.split()),
                'line_count': len(plain_text.split('\n')),
                'has_links': '<a href=' in html_content,
                'has_images': '<img src=' in html_content,
                'has_code': '<code>' in html_content or '<pre>' in html_content
            }
            
            # Validation checks
            if len(plain_text) == 0:
                result['valid'] = False
                result['errors'].append('Content cannot be empty')
            
            if len(plain_text) > 10000:
                result['warnings'].append('Content is very long (>10,000 characters)')
            
            # Format-specific validation
            if content_format == 'html':
                # Check for unclosed tags
                if html_content.count('<') != html_content.count('>'):
                    result['warnings'].append('Possible unclosed HTML tags')
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'Processing error: {str(e)}')
        
        return result


class MessageTemplateManager:
    """Message template management system"""
    
    def __init__(self):
        self.template_cache = {}
    
    def create_template(
        self,
        name: str,
        content: str,
        user_id: int,
        category: str = 'general',
        variables: Optional[List[str]] = None,
        is_public: bool = False
    ) -> Dict:
        """
        Create a new message template
        
        Args:
            name: Template name
            content: Template content
            user_id: Creator user ID
            category: Template category
            variables: List of template variables
            is_public: Whether template is public
        
        Returns:
            Created template data
        """
        from app.models import MessageTemplate
        
        # Extract variables from content if not provided
        if not variables:
            variables = self._extract_variables(content)
        
        template = MessageTemplate(
            name=name,
            content=content,
            user_id=user_id,
            category=category,
            variables=json.dumps(variables),
            is_public=is_public
        )
        
        db.session.add(template)
        db.session.commit()
        
        return {
            'id': template.id,
            'name': template.name,
            'content': template.content,
            'category': template.category,
            'variables': variables,
            'is_public': template.is_public,
            'created_at': template.created_at.isoformat()
        }
    
    def get_template(self, template_id: int, user_id: int) -> Optional[Dict]:
        """Get a template by ID"""
        from app.models import MessageTemplate
        
        template = MessageTemplate.query.filter_by(id=template_id).first()
        if not template:
            return None
        
        # Check access permissions
        if not template.is_public and template.user_id != user_id:
            return None
        
        return {
            'id': template.id,
            'name': template.name,
            'content': template.content,
            'category': template.category,
            'variables': json.loads(template.variables) if template.variables else [],
            'is_public': template.is_public,
            'created_at': template.created_at.isoformat()
        }
    
    def get_user_templates(
        self,
        user_id: int,
        category: Optional[str] = None,
        include_public: bool = True
    ) -> List[Dict]:
        """Get templates for a user"""
        from app.models import MessageTemplate
        
        query = MessageTemplate.query.filter(
            or_(
                MessageTemplate.user_id == user_id,
                MessageTemplate.is_public == True
            )
        )
        
        if category:
            query = query.filter(MessageTemplate.category == category)
        
        if not include_public:
            query = query.filter(MessageTemplate.user_id == user_id)
        
        templates = query.order_by(MessageTemplate.name).all()
        
        result = []
        for template in templates:
            result.append({
                'id': template.id,
                'name': template.name,
                'content': template.content,
                'category': template.category,
                'variables': json.loads(template.variables) if template.variables else [],
                'is_public': template.is_public,
                'is_owner': template.user_id == user_id,
                'created_at': template.created_at.isoformat()
            })
        
        return result
    
    def render_template(
        self,
        template_id: int,
        user_id: int,
        variables: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Render a template with variables
        
        Args:
            template_id: Template ID
            user_id: User ID
            variables: Variable values
        
        Returns:
            Rendered content
        """
        template_data = self.get_template(template_id, user_id)
        if not template_data:
            return None
        
        content = template_data['content']
        
        # Replace variables
        if variables:
            for var_name, var_value in variables.items():
                placeholder = f'{{{{{var_name}}}}}'
                content = content.replace(placeholder, str(var_value))
        
        # Replace system variables
        processor = RichTextProcessor()
        for var_name, var_func in processor.template_variables.items():
            placeholder = f'{{{{{var_name}}}}}'
            try:
                content = content.replace(placeholder, var_func())
            except:
                content = content.replace(placeholder, f'{{{var_name}}}')
        
        return content
    
    def update_template(
        self,
        template_id: int,
        user_id: int,
        **updates
    ) -> bool:
        """Update a template"""
        from app.models import MessageTemplate
        
        template = MessageTemplate.query.filter_by(id=template_id).first()
        if not template or template.user_id != user_id:
            return False
        
        # Update fields
        if 'name' in updates:
            template.name = updates['name']
        if 'content' in updates:
            template.content = updates['content']
            # Re-extract variables
            variables = self._extract_variables(updates['content'])
            template.variables = json.dumps(variables)
        if 'category' in updates:
            template.category = updates['category']
        if 'is_public' in updates:
            template.is_public = updates['is_public']
        
        db.session.commit()
        
        # Clear cache
        if template_id in self.template_cache:
            del self.template_cache[template_id]
        
        return True
    
    def delete_template(self, template_id: int, user_id: int) -> bool:
        """Delete a template"""
        from app.models import MessageTemplate
        
        template = MessageTemplate.query.filter_by(id=template_id).first()
        if not template or template.user_id != user_id:
            return False
        
        db.session.delete(template)
        db.session.commit()
        
        # Clear cache
        if template_id in self.template_cache:
            del self.template_cache[template_id]
        
        return True
    
    def _extract_variables(self, content: str) -> List[str]:
        """Extract template variables from content"""
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, content)
        return list(set(matches))


def format_message_content(
    content: str,
    content_format: str = 'text',
    sanitize: bool = True,
    enable_emoji: bool = True,
    enable_markdown: bool = True
) -> Tuple[str, str]:
    """
    Format message content based on format
    
    Args:
        content: Raw content
        content_format: Input format
        sanitize: Whether to sanitize HTML
        enable_emoji: Whether to convert emoji shortcodes
        enable_markdown: Whether to process markdown
    
    Returns:
        Tuple of (formatted_html, plain_text)
    """
    processor = RichTextProcessor()
    return processor.process_rich_text(
        content, content_format, sanitize, enable_emoji, enable_markdown
    )


def generate_message_preview(
    content: str,
    max_length: int = 200,
    content_format: str = 'text'
) -> str:
    """
    Generate a preview of message content
    
    Args:
        content: Content to preview
        max_length: Maximum preview length
        content_format: Content format
    
    Returns:
        Preview text
    """
    processor = RichTextProcessor()
    return processor.generate_preview(content, max_length, content_format)


def validate_message_content(
    content: str,
    content_format: str = 'text'
) -> Dict:
    """
    Validate message content
    
    Args:
        content: Content to validate
        content_format: Content format
    
    Returns:
        Validation result
    """
    processor = RichTextProcessor()
    return processor.validate_formatting(content, content_format)


def get_emoji_suggestions(query: str = '', limit: int = 20) -> List[Dict]:
    """
    Get emoji suggestions based on query
    
    Args:
        query: Search query
        limit: Maximum results
    
    Returns:
        List of emoji suggestions
    """
    processor = RichTextProcessor()
    
    suggestions = []
    query_lower = query.lower()
    
    for shortcode, emoji in processor.emoji_map.items():
        if query_lower in shortcode.lower():
            suggestions.append({
                'shortcode': shortcode,
                'emoji': emoji,
                'description': shortcode.replace(':', '').replace('_', ' ').title()
            })
        
        if len(suggestions) >= limit:
            break
    
    return suggestions


def convert_text_to_emoji(text: str) -> str:
    """
    Convert text with emoji shortcodes to actual emojis
    
    Args:
        text: Text to convert
    
    Returns:
        Text with emojis
    """
    processor = RichTextProcessor()
    return processor._convert_emoji(text)
