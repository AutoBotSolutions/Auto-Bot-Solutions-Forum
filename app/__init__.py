from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__, 
                static_folder=os.path.join(os.path.dirname(__file__), 'static'),
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
    app.config.from_object(config_class)

    db.init_app(app)
    app.db = db  # Ensure database object is accessible on app instance
    login_manager.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    from app.auth.routes import auth_bp
    from app.auth.two_factor_routes import two_factor_bp
    from app.auth.social_routes import social_bp
    from app.auth.session_routes import session_bp
    from app.main.routes import main_bp
    from app.forum.routes import forum_bp
    from app.api.routes import api_bp
    from app.api.push import push_bp
    from app.api.notification_analytics import analytics_bp
    from app.admin.routes import admin_bp
    from app.admin.email import email_bp
    from app.user.routes import user_bp
    from app.notification.routes import notification_bp
    from app.message.routes import message_bp
    from app.search.routes import search_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(session_bp, url_prefix='/auth/sessions')
    app.register_blueprint(search_bp)
    app.register_blueprint(two_factor_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(forum_bp, url_prefix='/forum')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(push_bp, url_prefix='/api/push')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(email_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(notification_bp, url_prefix='/notifications')
    app.register_blueprint(message_bp, url_prefix='/messages')

    # Error handlers
    from app.errors.handlers import page_not_found, internal_server_error
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)

    # Template filters
    from app.template_filters import init_template_filters
    init_template_filters(app)

    # Initialize email queue processor
    if app.config.get('MAIL_QUEUE_ENABLED'):
        from app.email.queue import queue_processor
        queue_processor.start()

    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })

    @app.route('/test-template-error')
    def test_template_error():
        """Test route to trigger template error without authentication"""
        try:
            from app.error_system import monitor_error
            
            # Create test data that will trigger the template error
            test_messages = []
            unread_count = 0
            
            # Try to render the template that's causing issues
            try:
                result = render_template('message/inbox.html', user_inbox=test_messages, unread_count=unread_count)
                return result
            except Exception as template_error:
                # Capture template rendering error with comprehensive details
                monitor_error(template_error, 
                             context={'template_rendering': True, 'template_name': 'message/inbox.html', 'test_route': True},
                             additional_data={
                                 'template_variables': {
                                     'user_inbox': test_messages,
                                     'unread_count': unread_count,
                                     'template_name': 'message/inbox.html'
                                 },
                                 'test_messages_length': len(test_messages),
                                 'unread_count': unread_count,
                                 'route_type': 'test_route_no_auth'
                             })
                raise template_error
                
        except Exception as route_error:
            # Capture route-level error
            try:
                from app.error_system import monitor_error
                monitor_error(route_error, 
                             context={'route_function': 'test_template_error', 'blueprint': 'main', 'test_route': True},
                             additional_data={
                                 'request_endpoint': request.endpoint if request else None,
                                 'route_type': 'test_route_no_auth'
                             })
            except:
                pass  # Don't let error monitoring fail
            raise route_error

    # Initialize OAuth2 for social login
    if app.config.get('SOCIAL_LOGIN_ENABLED'):
        from app.auth.social_config import init_oauth
        init_oauth(app)

    # Initialize WebSocket service for real-time features
    if app.config.get('WEBSOCKET_ENABLED', True):
        from app.websockets.service import WebSocketService
        from app.websockets.events import register_socketio_events
        
        websocket_service = WebSocketService(socketio)
        register_socketio_events(socketio, websocket_service)
        
        # Make websocket service available globally
        app.websocket_service = websocket_service

    # Initialize content management system
    if app.config.get('CONTENT_MANAGEMENT_ENABLED', True):
        from app.content import init_content_management
        init_content_management(app)

    # Initialize file management system
    if app.config.get('FILE_MANAGEMENT_ENABLED', True):
        from app.storage.routes import storage_bp
        app.register_blueprint(storage_bp)

    # Initialize reputation and voting system
    if app.config.get('REPUTATION_SYSTEM_ENABLED', True):
        from app.reputation.routes import reputation_bp
        app.register_blueprint(reputation_bp)

    # Initialize advanced analytics system
    if app.config.get('ANALYTICS_SYSTEM_ENABLED', True):
        from app.analytics.routes import analytics_bp
        app.register_blueprint(analytics_bp)

    # Initialize real-time admin notifications system
    if app.config.get('NOTIFICATIONS_SYSTEM_ENABLED', True):
        from app.notifications.routes import notifications_bp
        app.register_blueprint(notifications_bp)

    # Initialize automated content moderation system
    if app.config.get('MODERATION_SYSTEM_ENABLED', True):
        from app.moderation.routes import moderation_bp
        app.register_blueprint(moderation_bp)

    # Initialize comprehensive error monitoring system
    if app.config.get('ERROR_MONITORING_ENABLED', True):
        from app.error_system import init_comprehensive_error_system
        app = init_comprehensive_error_system(app)

    return app

from app import models
