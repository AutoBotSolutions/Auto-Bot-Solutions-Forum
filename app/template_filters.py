import markdown
import bleach
from flask import Blueprint

def init_template_filters(app):
    @app.template_filter('markdown')
    def markdown_filter(text):
        if not text:
            return ''
        
        # Convert markdown to HTML with basic extensions
        html = markdown.markdown(text, extensions=['fenced_code', 'tables'])
        
        # Basic HTML sanitization
        allowed_tags = ['p', 'br', 'strong', 'em', 'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'blockquote']
        allowed_attributes = {'a': ['href']}
        
        clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes)
        
        return clean_html
