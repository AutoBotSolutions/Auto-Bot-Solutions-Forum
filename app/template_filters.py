import markdown
import bleach
from flask import Blueprint

def init_template_filters(app):
    @app.template_filter('markdown')
    def markdown_filter(text):
        if not text:
            return ''
        
        # Configure allowed HTML tags
        allowed_tags = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'b', 'i', 'strong', 'em', 'p', 'br',
            'ul', 'ol', 'li',
            'a', 'code', 'pre', 'blockquote',
            'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
        ]
        
        allowed_attributes = {
            'a': ['href', 'title'],
            'code': ['class'],
            'pre': ['class']
        }
        
        # Convert markdown to HTML
        html = markdown.markdown(text, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br'])
        
        # Sanitize HTML
        clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes)
        
        return clean_html
