"""
Template rendering helper to bypass Flask-Login interference
"""

from flask import current_app
from app import db


def render_template_bypass(template_name, **context):
    """
    Render template bypassing Flask-Login's ensure_sync wrapper
    
    This function bypasses the Flask-Login interference with template rendering
    by using Jinja2 directly and ensuring the current_user is bound to the session.
    
    Args:
        template_name: Name of the template to render
        **context: Template context variables
        
    Returns:
        Rendered template string
    """
    # Ensure current_user is bound to session if it exists in context
    if 'current_user' in context:
        db.session.add(context['current_user'])
        db.session.flush()
    
    # Get template and render directly
    template = current_app.jinja_env.get_template(template_name)
    return template.render(**context)
