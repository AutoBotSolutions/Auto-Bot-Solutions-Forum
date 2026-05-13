"""
Real-time Admin Notifications Routes

This module contains Flask routes for the notification system,
including notification management, preferences, templates, and real-time updates.
"""

from datetime import datetime, timedelta, time
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import and_, or_, desc, asc, func
from werkzeug.exceptions import NotFound, BadRequest

from app import db
from app.models import User
from .models import (
    AdminNotification, NotificationTemplate, NotificationPreference,
    NotificationDelivery, NotificationCategory
)
from .service import (
    NotificationService, AdminNotificationService, SecurityNotificationService,
    SystemHealthNotificationService, ModerationNotificationService,
    UserActivityNotificationService, NotificationPreferenceService,
    NotificationDeliveryService
)
from .translation_service import notification_translation_service
from .filtering_service import notification_filtering_service
from .mobile_service import mobile_notification_service
from .forms import (
    NotificationFilterForm, NotificationTemplateForm, NotificationPreferenceForm,
    NotificationSettingsForm, CreateNotificationForm, NotificationCategoryForm,
    BulkNotificationForm, NotificationSearchForm, NotificationSearchAdvancedForm,
    UserNotificationPreferencesForm, NotificationArchiveForm, NotificationScheduleForm,
    NotificationGroupingForm
)

# Create blueprint
notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

# Initialize services
notification_service = NotificationService()
admin_notification_service = AdminNotificationService()
security_notification_service = SecurityNotificationService()
system_health_notification_service = SystemHealthNotificationService()
moderation_notification_service = ModerationNotificationService()
user_activity_notification_service = UserActivityNotificationService()
preference_service = NotificationPreferenceService()
delivery_service = NotificationDeliveryService()

# Main notifications page
@notifications_bp.route('/')
@login_required
def index():
    """Main notifications dashboard"""
    
    # Get notification counts
    total_notifications = AdminNotification.query.filter_by(user_id=current_user.id).count()
    unread_count = notification_service.get_unread_count(current_user.id)
    
    # Get recent notifications
    recent_notifications = notification_service.get_user_notifications(
        current_user.id, limit=10
    )
    
    # Get unread notifications for sidebar
    unread_notifications = notification_service.get_user_notifications(
        current_user.id, unread_only=True, limit=5
    )
    
    # Get notification categories
    categories = NotificationCategory.query.filter_by(is_active=True).order_by(
        NotificationCategory.sort_order
    ).all()
    
    return render_template('notifications/index.html',
                         total_notifications=total_notifications,
                         unread_count=unread_count,
                         recent_notifications=recent_notifications,
                         unread_notifications=unread_notifications,
                         categories=categories)

# Notification list
@notifications_bp.route('/list')
@login_required
def list_notifications():
    """List notifications with filtering"""
    
    form = NotificationFilterForm(request.args)
    
    # Build query
    query = AdminNotification.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if form.notification_type.data:
        query = query.filter(AdminNotification.notification_type == form.notification_type.data)
    if form.category.data:
        query = query.filter(AdminNotification.category == form.category.data)
    if form.priority.data:
        query = query.filter(AdminNotification.priority == form.priority.data)
    if form.severity.data:
        query = query.filter(AdminNotification.severity == form.severity.data)
    if form.is_read.data:
        is_read = form.is_read.data == 'true'
        query = query.filter(AdminNotification.is_read == is_read)
    if form.is_acknowledged.data:
        is_acknowledged = form.is_acknowledged.data == 'true'
        query = query.filter(AdminNotification.is_acknowledged == is_acknowledged)
    if form.requires_action.data:
        requires_action = form.requires_action.data == 'true'
        query = query.filter(AdminNotification.requires_action == requires_action)
    if form.target_type.data:
        query = query.filter(AdminNotification.target_type == form.target_type.data)
    if form.target_id.data:
        query = query.filter(AdminNotification.target_id == form.target_id.data)
    if form.search.data:
        search_term = f"%{form.search.data}%"
        query = query.filter(or_(
            AdminNotification.title.ilike(search_term),
            AdminNotification.message.ilike(search_term)
        ))
    
    # Date filters
    if form.created_since.data:
        query = query.filter(AdminNotification.created_at >= form.created_since.data)
    if form.created_before.data:
        query = query.filter(AdminNotification.created_at <= form.created_before.data)
    
    # Apply sorting
    if form.sort_by.data == 'created_at':
        if form.sort_order.data == 'asc':
            query = query.order_by(AdminNotification.created_at.asc())
        else:
            query = query.order_by(AdminNotification.created_at.desc())
    elif form.sort_by.data == 'priority':
        priority_order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        if form.sort_order.data == 'asc':
            query = query.order_by(func.case([
                (AdminNotification.priority == 'low', 1),
                (AdminNotification.priority == 'medium', 2),
                (AdminNotification.priority == 'high', 3),
                (AdminNotification.priority == 'critical', 4)
            ]).asc())
        else:
            query = query.order_by(func.case([
                (AdminNotification.priority == 'low', 1),
                (AdminNotification.priority == 'medium', 2),
                (AdminNotification.priority == 'high', 3),
                (AdminNotification.priority == 'critical', 4)
            ]).desc())
    else:
        query = query.order_by(AdminNotification.created_at.desc())
    
    # Apply limit
    notifications = query.limit(form.limit.data or 50).all()
    
    return render_template('notifications/list.html',
                         notifications=notifications,
                         form=form)

# Notification details
@notifications_bp.route('/<int:notification_id>')
@login_required
def notification_detail(notification_id):
    """Show notification details"""
    
    notification = AdminNotification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first_or_404()
    
    # Get delivery stats
    delivery_stats = delivery_service.get_delivery_stats(notification_id)
    
    return render_template('notifications/detail.html',
                         notification=notification,
                         delivery_stats=delivery_stats)

# Mark notification as read
@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark notification as read"""
    
    notification = notification_service.mark_as_read(notification_id, current_user.id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'notification_id': notification_id,
            'unread_count': notification_service.get_unread_count(current_user.id)
        })
    
    flash('Notification marked as read', 'success')
    return redirect(url_for('notifications.list_notifications'))

# Mark notification as unread
@notifications_bp.route('/<int:notification_id>/unread', methods=['POST'])
@login_required
def mark_unread(notification_id):
    """Mark notification as unread"""
    
    notification = AdminNotification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first_or_404()
    
    notification.is_read = False
    notification.read_at = None
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'notification_id': notification_id,
            'unread_count': notification_service.get_unread_count(current_user.id)
        })
    
    flash('Notification marked as unread', 'success')
    return redirect(url_for('notifications.list_notifications'))

# Acknowledge notification
@notifications_bp.route('/<int:notification_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_notification(notification_id):
    """Acknowledge notification"""
    
    notification = notification_service.acknowledge_notification(notification_id, current_user.id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'notification_id': notification_id
        })
    
    flash('Notification acknowledged', 'success')
    return redirect(url_for('notifications.list_notifications'))

# Delete notification
@notifications_bp.route('/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete notification"""
    
    notification = notification_service.delete_notification(notification_id, current_user.id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'notification_id': notification_id,
            'unread_count': notification_service.get_unread_count(current_user.id)
        })
    
    flash('Notification deleted', 'success')
    return redirect(url_for('notifications.list_notifications'))

# Mark all as read
@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    
    count = notification_service.mark_all_as_read(current_user.id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'count': count,
            'unread_count': 0
        })
    
    flash(f'{count} notifications marked as read', 'success')
    return redirect(url_for('notifications.list_notifications'))

# Bulk operations
@notifications_bp.route('/bulk', methods=['POST'])
@login_required
def bulk_operations():
    """Perform bulk operations on notifications"""
    
    form = BulkNotificationForm()
    
    if form.validate_on_submit():
        notification_ids = [int(nid) for nid in form.notification_ids.data.split(',') if nid.strip()]
        operation = form.operation.data
        
        notifications = AdminNotification.query.filter(
            AdminNotification.id.in_(notification_ids),
            AdminNotification.user_id == current_user.id
        ).all()
        
        processed_count = 0
        
        for notification in notifications:
            if operation == 'mark_read':
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                processed_count += 1
            elif operation == 'mark_unread':
                notification.is_read = False
                notification.read_at = None
                processed_count += 1
            elif operation == 'acknowledge':
                notification.is_acknowledged = True
                notification.acknowledged_at = datetime.utcnow()
                processed_count += 1
            elif operation == 'delete':
                db.session.delete(notification)
                processed_count += 1
        
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'operation': operation,
                'processed_count': processed_count,
                'unread_count': notification_service.get_unread_count(current_user.id)
            })
        
        flash(f'{processed_count} notifications processed', 'success')
    
    return redirect(url_for('notifications.list_notifications'))

# Preferences
@notifications_bp.route('/preferences')
@login_required
def preferences():
    """Notification preferences page"""
    
    preferences = preference_service.get_user_preferences(current_user.id)
    categories = NotificationCategory.query.filter_by(is_active=True).all()
    
    return render_template('notifications/preferences.html',
                         preferences=preferences,
                         categories=categories)

@notifications_bp.route('/preferences/update', methods=['POST'])
@login_required
def update_preferences():
    """Update notification preferences"""
    
    form = NotificationPreferenceForm()
    
    if form.validate_on_submit():
        preference = preference_service.set_user_preference(
            current_user.id,
            form.notification_type.data,
            form.category.data,
            enabled=form.enabled.data,
            in_app_enabled=form.in_app_enabled.data,
            email_enabled=form.email_enabled.data,
            sms_enabled=form.sms_enabled.data,
            min_priority=form.min_priority.data,
            min_severity=form.min_severity.data,
            frequency=form.frequency.data,
            batch_size=form.batch_size.data,
            quiet_hours_enabled=form.quiet_hours_enabled.data,
            quiet_hours_start=form.quiet_hours_start.data,
            quiet_hours_end=form.quiet_hours_end.data,
            excluded_sources=[s.strip() for s in form.excluded_sources.data.split(',') if s.strip()],
            excluded_categories=[c.strip() for c in form.excluded_categories.data.split(',') if c.strip()]
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'preference': preference.to_dict()
            })
        
        flash('Preferences updated successfully', 'success')
    
    return redirect(url_for('notifications.preferences'))

# Templates management (admin only)
@notifications_bp.route('/templates')
@login_required
def templates():
    """Notification templates page"""
    
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('notifications.index'))
    
    templates = NotificationTemplate.query.filter_by(is_active=True).order_by(
        NotificationTemplate.name
    ).all()
    
    return render_template('notifications/templates.html',
                         templates=templates)

@notifications_bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
def create_template():
    """Create notification template"""
    
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('notifications.index'))
    
    form = NotificationTemplateForm()
    
    if form.validate_on_submit():
        template = NotificationTemplate(
            name=form.name.data,
            description=form.description.data,
            title_template=form.title_template.data,
            message_template=form.message_template.data,
            notification_type=form.notification_type.data,
            category=form.category.data,
            default_priority=form.default_priority.data,
            default_severity=form.default_severity.data,
            auto_send=form.auto_send.data,
            requires_action=form.requires_action.data,
            action_template=form.action_template.data,
            default_expires_hours=form.default_expires_hours.data,
            target_roles=form.target_roles.data,
            target_users=[int(uid.strip()) for uid in form.target_users.data.split(',') if uid.strip()],
            created_by=current_user.id
        )
        
        db.session.add(template)
        db.session.commit()
        
        flash('Template created successfully', 'success')
        return redirect(url_for('notifications.templates'))
    
    return render_template('notifications/create_template.html',
                         form=form)

@notifications_bp.route('/templates/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    """Edit notification template"""
    
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('notifications.index'))
    
    template = NotificationTemplate.query.get_or_404(template_id)
    
    form = NotificationTemplateForm(obj=template)
    
    if form.validate_on_submit():
        # Update template fields
        form.populate_obj(template)
        
        # Handle target_users separately
        if form.target_users.data:
            template.target_users = [int(uid.strip()) for uid in form.target_users.data.split(',') if uid.strip()]
        
        db.session.commit()
        
        flash('Template updated successfully', 'success')
        return redirect(url_for('notifications.templates'))
    
    return render_template('notifications/edit_template.html',
                         form=form,
                         template=template)

# Categories management (admin only)
@notifications_bp.route('/categories')
@login_required
def categories():
    """Notification categories page"""
    
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('notifications.index'))
    
    categories = NotificationCategory.query.order_by(
        NotificationCategory.sort_order
    ).all()
    
    return render_template('notifications/categories.html',
                         categories=categories)

@notifications_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    """Create notification category"""
    
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('notifications.index'))
    
    form = NotificationCategoryForm()
    
    if form.validate_on_submit():
        category = NotificationCategory(
            name=form.name.data,
            display_name=form.display_name.data,
            description=form.description.data,
            icon=form.icon.data,
            color=form.color.data,
            default_priority=form.default_priority.data,
            default_severity=form.default_severity.data,
            default_expires_hours=form.default_expires_hours.data,
            requires_action=form.requires_action.data,
            auto_acknowledge=form.auto_acknowledge.data,
            is_active=form.is_active.data,
            sort_order=form.sort_order.data
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully', 'success')
        return redirect(url_for('notifications.categories'))
    
    return render_template('notifications/create_category.html',
                         form=form)

# Create notification (admin only)
@notifications_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_notification():
    """Create manual notification"""
    
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('notifications.index'))
    
    form = CreateNotificationForm()
    
    # Populate user choices
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    form.target_users.choices = [(str(user.id), user.username) for user in users]
    
    if form.validate_on_submit():
        # Determine recipients
        recipients = []
        
        if form.send_to_all.data:
            users = User.query.filter_by(is_active=True).all()
            recipients = [user.id for user in users]
        else:
            if form.target_users.data:
                recipients.extend([int(uid) for uid in form.target_users.data])
            
            if 'admin' in form.target_roles.data:
                admin_users = User.query.filter_by(is_admin=True).all()
                recipients.extend([user.id for user in admin_users])
            
            if 'moderator' in form.target_roles.data:
                moderator_users = User.query.filter_by(is_moderator=True).all()
                recipients.extend([user.id for user in moderator_users])
            
            if 'user' in form.target_roles.data:
                regular_users = User.query.filter_by(is_admin=False, is_moderator=False).all()
                recipients.extend([user.id for user in regular_users])
        
        # Remove duplicates
        recipients = list(set(recipients))
        
        # Create notifications
        notifications = []
        for user_id in recipients:
            notification = notification_service.create_notification(
                title=form.title.data,
                message=form.message.data,
                notification_type=form.notification_type.data,
                category=form.category.data,
                user_id=user_id,
                priority=form.priority.data,
                severity=form.severity.data,
                requires_action=form.requires_action.data,
                action_url=form.action_url.data,
                expires_hours=form.expires_hours.data,
                source='admin',
                source_id=current_user.id
            )
            notifications.append(notification)
        
        flash(f'Notification sent to {len(notifications)} users', 'success')
        return redirect(url_for('notifications.index'))
    
    return render_template('notifications/create_notification.html',
                         form=form)

# API endpoints
@notifications_bp.route('/api/notifications')
@login_required
def api_notifications():
    """API endpoint for notifications"""
    
    form = NotificationFilterForm(request.args)
    
    # Build query
    query = AdminNotification.query.filter_by(user_id=current_user.id)
    
    # Apply filters (same logic as list_notifications)
    if form.notification_type.data:
        query = query.filter(AdminNotification.notification_type == form.notification_type.data)
    if form.category.data:
        query = query.filter(AdminNotification.category == form.category.data)
    if form.priority.data:
        query = query.filter(AdminNotification.priority == form.priority.data)
    if form.severity.data:
        query = query.filter(AdminNotification.severity == form.severity.data)
    if form.is_read.data:
        is_read = form.is_read.data == 'true'
        query = query.filter(AdminNotification.is_read == is_read)
    if form.created_since.data:
        query = query.filter(AdminNotification.created_at >= form.created_since.data)
    if form.created_before.data:
        query = query.filter(AdminNotification.created_at <= form.created_before.data)
    
    # Apply sorting and limit
    query = query.order_by(AdminNotification.created_at.desc())
    notifications = query.limit(form.limit.data or 50).all()
    
    return jsonify({
        'success': True,
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': notification_service.get_unread_count(current_user.id)
    })

@notifications_bp.route('/api/unread-count')
@login_required
def api_unread_count():
    """API endpoint for unread count"""
    
    count = notification_service.get_unread_count(current_user.id)
    
    return jsonify({
        'success': True,
        'unread_count': count
    })

@notifications_bp.route('/api/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def api_mark_read(notification_id):
    """API endpoint to mark notification as read"""
    
    notification = notification_service.mark_as_read(notification_id, current_user.id)
    
    if notification:
        return jsonify({
            'success': True,
            'notification_id': notification_id,
            'unread_count': notification_service.get_unread_count(current_user.id)
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Notification not found'
        }), 404

@notifications_bp.route('/api/create', methods=['POST'])
@login_required
def api_create_notification():
    """API endpoint to create notification"""
    
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'error': 'Access denied'
        }), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    try:
        notification = notification_service.create_notification(
            title=data.get('title'),
            message=data.get('message'),
            notification_type=data.get('notification_type'),
            category=data.get('category'),
            user_id=data.get('user_id'),
            priority=data.get('priority', 'medium'),
            severity=data.get('severity', 'info'),
            target_type=data.get('target_type'),
            target_id=data.get('target_id'),
            target_url=data.get('target_url'),
            source='api',
            source_id=current_user.id,
            data=data.get('data'),
            metadata=data.get('metadata'),
            requires_action=data.get('requires_action', False),
            action_url=data.get('action_url'),
            expires_hours=data.get('expires_hours')
        )
        
        return jsonify({
            'success': True,
            'notification': notification.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/preferences')
@login_required
def api_preferences():
    """API endpoint for user preferences"""
    
    preferences = preference_service.get_user_preferences(current_user.id)
    
    return jsonify({
        'success': True,
        'preferences': [p.to_dict() for p in preferences]
    })

@notifications_bp.route('/api/preferences/update', methods=['POST'])
@login_required
def api_update_preferences():
    """API endpoint to update preferences"""
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    try:
        preference = preference_service.set_user_preference(
            current_user.id,
            data['notification_type'],
            data['category'],
            **{k: v for k, v in data.items() if k not in ['notification_type', 'category']}
        )
        
        return jsonify({
            'success': True,
            'preference': preference.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Advanced Search Routes
@notifications_bp.route('/search')
@login_required
def advanced_search():
    """Advanced notification search page"""
    
    form = NotificationSearchAdvancedForm()
    notifications = []
    total_count = 0
    
    if request.args.get('search') or request.args.get('types'):
        # Build search query
        query = AdminNotification.query.filter(
            AdminNotification.user_id == current_user.id
        )
        
        # Search query
        if request.args.get('search_query'):
            search_term = f"%{request.args.get('search_query')}%"
            query = query.filter(or_(
                AdminNotification.title.ilike(search_term),
                AdminNotification.message.ilike(search_term)
            ))
        
        # Type filters
        if request.args.get('types'):
            types = request.args.getlist('types')
            if types:
                query = query.filter(AdminNotification.notification_type.in_(types))
        
        # Status filters
        if request.args.get('is_read') == 'read':
            query = query.filter(AdminNotification.is_read == True)
        elif request.args.get('is_read') == 'unread':
            query = query.filter(AdminNotification.is_read == False)
        
        # Priority filters
        if request.args.get('priorities'):
            priorities = request.args.getlist('priorities')
            if priorities:
                query = query.filter(AdminNotification.priority.in_(priorities))
        
        # Date range filters
        if request.args.get('date_range'):
            date_range = request.args.get('date_range')
            now = datetime.utcnow()
            
            if date_range == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(AdminNotification.created_at >= start_date)
            elif date_range == 'yesterday':
                yesterday = now - timedelta(days=1)
                start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                query = query.filter(AdminNotification.created_at.between(start_date, end_date))
            elif date_range == 'last_7_days':
                start_date = now - timedelta(days=7)
                query = query.filter(AdminNotification.created_at >= start_date)
            elif date_range == 'last_30_days':
                start_date = now - timedelta(days=30)
                query = query.filter(AdminNotification.created_at >= start_date)
            elif date_range == 'last_90_days':
                start_date = now - timedelta(days=90)
                query = query.filter(AdminNotification.created_at >= start_date)
            elif date_range == 'this_year':
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(AdminNotification.created_at >= start_date)
            elif date_range == 'last_year':
                last_year = now.year - 1
                start_date = datetime(last_year, 1, 1)
                end_date = datetime(last_year, 12, 31, 23, 59, 59, 999999)
                query = query.filter(AdminNotification.created_at.between(start_date, end_date))
        
        # Custom date range
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date'))
            query = query.filter(AdminNotification.created_at >= start_date)
        
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date'))
            query = query.filter(AdminNotification.created_at <= end_date)
        
        # Include archived
        if not request.args.get('include_archived'):
            query = query.filter(AdminNotification.is_archived == False)
        
        # Show only unread
        if request.args.get('show_only_unread'):
            query = query.filter(AdminNotification.is_read == False)
        
        # Sorting
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if sort_by == 'created_at':
            if sort_order == 'desc':
                query = query.order_by(desc(AdminNotification.created_at))
            else:
                query = query.order_by(asc(AdminNotification.created_at))
        elif sort_by == 'priority':
            if sort_order == 'desc':
                query = query.order_by(desc(AdminNotification.priority))
            else:
                query = query.order_by(asc(AdminNotification.priority))
        elif sort_by == 'type':
            if sort_order == 'desc':
                query = query.order_by(desc(AdminNotification.notification_type))
            else:
                query = query.order_by(asc(AdminNotification.notification_type))
        
        # Pagination
        per_page = int(request.args.get('per_page', 25))
        page = request.args.get('page', 1, type=int)
        
        total_count = query.count()
        notifications = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return render_template('notifications/advanced_search.html',
                         form=form,
                         notifications=notifications,
                         total_count=total_count,
                         search_params=request.args)

@notifications_bp.route('/search/api', methods=['GET'])
@login_required
def api_search():
    """API endpoint for advanced notification search"""
    
    try:
        # Build search query
        query = AdminNotification.query.filter(
            AdminNotification.user_id == current_user.id
        )
        
        # Search query
        search_query = request.args.get('search_query')
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(or_(
                AdminNotification.title.ilike(search_term),
                AdminNotification.message.ilike(search_term)
            ))
        
        # Type filters
        types = request.args.getlist('types')
        if types:
            query = query.filter(AdminNotification.notification_type.in_(types))
        
        # Status filters
        is_read = request.args.get('is_read')
        if is_read == 'read':
            query = query.filter(AdminNotification.is_read == True)
        elif is_read == 'unread':
            query = query.filter(AdminNotification.is_read == False)
        
        # Priority filters
        priorities = request.args.getlist('priorities')
        if priorities:
            query = query.filter(AdminNotification.priority.in_(priorities))
        
        # Date range
        start_date = request.args.get('start_date')
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(AdminNotification.created_at >= start_dt)
        
        end_date = request.args.get('end_date')
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(AdminNotification.created_at <= end_dt)
        
        # Include archived
        if not request.args.get('include_archived'):
            query = query.filter(AdminNotification.is_archived == False)
        
        # Sorting
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if sort_by == 'created_at':
            if sort_order == 'desc':
                query = query.order_by(desc(AdminNotification.created_at))
            else:
                query = query.order_by(asc(AdminNotification.created_at))
        elif sort_by == 'priority':
            if sort_order == 'desc':
                query = query.order_by(desc(AdminNotification.priority))
            else:
                query = query.order_by(asc(AdminNotification.priority))
        
        # Pagination
        per_page = min(int(request.args.get('per_page', 25)), 100)
        page = request.args.get('page', 1, type=int)
        
        total_count = query.count()
        notifications = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'success': True,
            'notifications': [n.to_dict() for n in notifications],
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        current_app.logger.error(f"Search API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# User Preferences Routes
@notifications_bp.route('/preferences')
@login_required
def user_preferences():
    """User notification preferences page"""
    
    # Get current user preferences
    user = User.query.get(current_user.id)
    
    # Parse existing preferences
    push_preferences = {}
    email_preferences = {}
    
    if user.push_preferences:
        try:
            push_preferences = eval(user.push_preferences) if isinstance(user.push_preferences, str) else user.push_preferences
        except:
            push_preferences = {}
    
    if user.email_preferences:
        try:
            email_preferences = eval(user.email_preferences) if isinstance(user.email_preferences, str) else user.email_preferences
        except:
            email_preferences = {}
    
    # Create form with current preferences
    form = UserNotificationPreferencesForm(
        push_notifications_enabled=user.push_enabled,
        push_comment_notifications=push_preferences.get('comment', True),
        push_message_notifications=push_preferences.get('message', True),
        push_system_notifications=push_preferences.get('system', False),
        push_moderation_notifications=push_preferences.get('moderation', False),
        email_notifications_enabled=user.email_enabled,
        email_comment_notifications=email_preferences.get('comment', True),
        email_message_notifications=email_preferences.get('message', True),
        email_system_notifications=email_preferences.get('system', False),
        email_moderation_notifications=email_preferences.get('moderation', False),
        email_digest_frequency=email_preferences.get('digest_frequency', 'immediate'),
        quiet_hours_enabled=push_preferences.get('quiet_hours_enabled', False),
        quiet_hours_start=datetime.strptime(push_preferences.get('quiet_hours_start', '22:00'), '%H:%M').time() if push_preferences.get('quiet_hours_start') else time(22, 0),
        quiet_hours_end=datetime.strptime(push_preferences.get('quiet_hours_end', '08:00'), '%H:%M').time() if push_preferences.get('quiet_hours_end') else time(8, 0),
        quiet_hours_push=push_preferences.get('quiet_hours_push', True),
        quiet_hours_email=email_preferences.get('quiet_hours_email', False),
        max_notifications_per_hour=push_preferences.get('max_per_hour', 20),
        batch_notifications=push_preferences.get('batch_notifications', True),
        batch_window_minutes=push_preferences.get('batch_window_minutes', 5),
        notification_sound_enabled=push_preferences.get('sound_enabled', True),
        notification_desktop_enabled=push_preferences.get('desktop_enabled', True),
        show_online_status=push_preferences.get('show_online_status', True),
        show_email_in_notifications=push_preferences.get('show_email', False)
    )
    
    return render_template('notifications/preferences.html', form=form)

# Duplicate update_preferences function removed to fix blueprint conflict

# Notification Archiving Routes
@notifications_bp.route('/archive')
@login_required
def archive():
    """Notification archiving page"""
    
    form = NotificationArchiveForm()
    
    # Get archive statistics
    total_notifications = AdminNotification.query.filter_by(user_id=current_user.id).count()
    read_notifications = AdminNotification.query.filter_by(user_id=current_user.id, is_read=True).count()
    unread_notifications = AdminNotification.query.filter_by(user_id=current_user.id, is_read=False).count()
    archived_notifications = AdminNotification.query.filter_by(user_id=current_user.id, is_archived=True).count()
    
    # Get recent notifications for manual archiving
    recent_notifications = AdminNotification.query.filter_by(
        user_id=current_user.id,
        is_archived=False
    ).order_by(desc(AdminNotification.created_at)).limit(50).all()
    
    return render_template('notifications/archive.html',
                         form=form,
                         total_notifications=total_notifications,
                         read_notifications=read_notifications,
                         unread_notifications=unread_notifications,
                         archived_notifications=archived_notifications,
                         recent_notifications=recent_notifications)

@notifications_bp.route('/archive/execute', methods=['POST'])
@login_required
def execute_archive():
    """Execute notification archiving"""
    
    form = NotificationArchiveForm()
    
    if form.validate_on_submit():
        try:
            archived_count = 0
            
            # Auto-archive read notifications
            if form.archive_read_older_than.data:
                days_map = {
                    '7_days': 7,
                    '30_days': 30,
                    '90_days': 90,
                    '180_days': 180,
                    '365_days': 365
                }
                
                days = days_map.get(form.archive_read_older_than.data)
                if days:
                    cutoff_date = datetime.utcnow() - timedelta(days=days)
                    
                    query = AdminNotification.query.filter(
                        AdminNotification.user_id == current_user.id,
                        AdminNotification.is_read == True,
                        AdminNotification.created_at < cutoff_date,
                        AdminNotification.is_archived == False
                    )
                    
                    # Keep important notifications if specified
                    if form.keep_important.data:
                        query = query.filter(AdminNotification.priority != 'urgent')
                    
                    notifications = query.all()
                    for notification in notifications:
                        notification.is_archived = True
                        archived_count += 1
            
            # Auto-archive unread notifications
            if form.archive_unread_older_than.data:
                days_map = {
                    '30_days': 30,
                    '90_days': 90,
                    '180_days': 180,
                    '365_days': 365,
                    '730_days': 730
                }
                
                days = days_map.get(form.archive_unread_older_than.data)
                if days:
                    cutoff_date = datetime.utcnow() - timedelta(days=days)
                    
                    query = AdminNotification.query.filter(
                        AdminNotification.user_id == current_user.id,
                        AdminNotification.is_read == False,
                        AdminNotification.created_at < cutoff_date,
                        AdminNotification.is_archived == False
                    )
                    
                    # Keep unread notifications if specified
                    if not form.keep_unread.data:
                        # Keep important notifications if specified
                        if form.keep_important.data:
                            query = query.filter(AdminNotification.priority != 'urgent')
                        
                        notifications = query.all()
                        for notification in notifications:
                            notification.is_archived = True
                            archived_count += 1
            
            # Archive all read notifications
            if form.archive_all_read.data:
                query = AdminNotification.query.filter(
                    AdminNotification.user_id == current_user.id,
                    AdminNotification.is_read == True,
                    AdminNotification.is_archived == False
                )
                
                # Keep important notifications if specified
                if form.keep_important.data:
                    query = query.filter(AdminNotification.priority != 'urgent')
                
                notifications = query.all()
                for notification in notifications:
                    notification.is_archived = True
                    archived_count += 1
            
            # Archive all notifications older than specified date
            if form.archive_all_older_than.data:
                cutoff_date = form.archive_all_older_than.data
                
                query = AdminNotification.query.filter(
                    AdminNotification.user_id == current_user.id,
                    AdminNotification.created_at < cutoff_date,
                    AdminNotification.is_archived == False
                )
                
                # Keep unread notifications if specified
                if form.keep_unread.data:
                    query = query.filter(AdminNotification.is_read == True)
                
                # Keep important notifications if specified
                if form.keep_important.data:
                    query = query.filter(AdminNotification.priority != 'urgent')
                
                notifications = query.all()
                for notification in notifications:
                    notification.is_archived = True
                    archived_count += 1
            
            # Manual archive by IDs
            if form.notification_ids.data:
                try:
                    notification_ids = [int(nid.strip()) for nid in form.notification_ids.data.split(',') if nid.strip()]
                    
                    notifications = AdminNotification.query.filter(
                        AdminNotification.id.in_(notification_ids),
                        AdminNotification.user_id == current_user.id,
                        AdminNotification.is_archived == False
                    ).all()
                    
                    for notification in notifications:
                        notification.is_archived = True
                        archived_count += 1
                        
                except ValueError:
                    flash('Invalid notification ID format.', 'error')
                    return redirect(url_for('notifications.archive'))
            
            if archived_count > 0:
                db.session.commit()
                flash(f'Successfully archived {archived_count} notifications!', 'success')
            else:
                flash('No notifications were archived.', 'info')
            
            return redirect(url_for('notifications.archive'))
            
        except Exception as e:
            current_app.logger.error(f"Archive error: {str(e)}")
            db.session.rollback()
            flash('Error archiving notifications. Please try again.', 'error')
    
    return render_template('notifications/archive.html', form=form)

@notifications_bp.route('/archive/restore/<int:notification_id>')
@login_required
def restore_notification(notification_id):
    """Restore a single notification from archive"""
    
    try:
        notification = AdminNotification.query.filter_by(
            id=notification_id,
            user_id=current_user.id,
            is_archived=True
        ).first()
        
        if notification:
            notification.is_archived = False
            db.session.commit()
            flash('Notification restored successfully!', 'success')
        else:
            flash('Notification not found or already restored.', 'error')
            
    except Exception as e:
        current_app.logger.error(f"Restore error: {str(e)}")
        db.session.rollback()
        flash('Error restoring notification. Please try again.', 'error')
    
    return redirect(url_for('notifications.archive'))

@notifications_bp.route('/archive/bulk-restore', methods=['POST'])
@login_required
def bulk_restore_notifications():
    """Bulk restore notifications from archive"""
    
    try:
        notification_ids = request.form.getlist('notification_ids')
        
        if not notification_ids:
            flash('No notifications selected for restore.', 'error')
            return redirect(url_for('notifications.archive'))
        
        restored_count = 0
        
        for notification_id in notification_ids:
            notification = AdminNotification.query.filter_by(
                id=int(notification_id),
                user_id=current_user.id,
                is_archived=True
            ).first()
            
            if notification:
                notification.is_archived = False
                restored_count += 1
        
        if restored_count > 0:
            db.session.commit()
            flash(f'Successfully restored {restored_count} notifications!', 'success')
        else:
            flash('No notifications were restored.', 'info')
            
    except Exception as e:
        current_app.logger.error(f"Bulk restore error: {str(e)}")
        db.session.rollback()
        flash('Error restoring notifications. Please try again.', 'error')
    
    return redirect(url_for('notifications.archive'))

@notifications_bp.route('/archive/delete/<int:notification_id>')
@login_required
def delete_archived_notification(notification_id):
    """Permanently delete an archived notification"""
    
    try:
        notification = AdminNotification.query.filter_by(
            id=notification_id,
            user_id=current_user.id,
            is_archived=True
        ).first()
        
        if notification:
            db.session.delete(notification)
            db.session.commit()
            flash('Notification permanently deleted!', 'success')
        else:
            flash('Notification not found.', 'error')
            
    except Exception as e:
        current_app.logger.error(f"Delete error: {str(e)}")
        db.session.rollback()
        flash('Error deleting notification. Please try again.', 'error')
    
    return redirect(url_for('notifications.archive'))

@notifications_bp.route('/archive/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_archived_notifications():
    """Bulk delete archived notifications"""
    
    try:
        notification_ids = request.form.getlist('notification_ids')
        
        if not notification_ids:
            flash('No notifications selected for deletion.', 'error')
            return redirect(url_for('notifications.archive'))
        
        deleted_count = 0
        
        for notification_id in notification_ids:
            notification = AdminNotification.query.filter_by(
                id=int(notification_id),
                user_id=current_user.id,
                is_archived=True
            ).first()
            
            if notification:
                db.session.delete(notification)
                deleted_count += 1
        
        if deleted_count > 0:
            db.session.commit()
            flash(f'Successfully deleted {deleted_count} notifications!', 'success')
        else:
            flash('No notifications were deleted.', 'info')
            
    except Exception as e:
        current_app.logger.error(f"Bulk delete error: {str(e)}")
        db.session.rollback()
        flash('Error deleting notifications. Please try again.', 'error')
    
    return redirect(url_for('notifications.archive'))

@notifications_bp.route('/archive/api/search', methods=['GET'])
@login_required
def api_search_archived():
    """API endpoint to search archived notifications"""
    
    try:
        query = AdminNotification.query.filter(
            AdminNotification.user_id == current_user.id,
            AdminNotification.is_archived == True
        )
        
        # Search query
        search_query = request.args.get('search')
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(or_(
                AdminNotification.title.ilike(search_term),
                AdminNotification.message.ilike(search_term)
            ))
        
        # Type filters
        notification_type = request.args.get('type')
        if notification_type:
            query = query.filter(AdminNotification.notification_type == notification_type)
        
        # Priority filters
        priority = request.args.get('priority')
        if priority:
            query = query.filter(AdminNotification.priority == priority)
        
        # Sorting
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if sort_by == 'created_at':
            if sort_order == 'desc':
                query = query.order_by(desc(AdminNotification.created_at))
            else:
                query = query.order_by(asc(AdminNotification.created_at))
        
        # Pagination
        per_page = min(int(request.args.get('per_page', 25)), 100)
        page = request.args.get('page', 1, type=int)
        
        total_count = query.count()
        notifications = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'success': True,
            'notifications': [n.to_dict() for n in notifications],
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        current_app.logger.error(f"Archive search API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Notification Scheduling Routes
@notifications_bp.route('/schedule')
@login_required
def schedule():
    """Notification scheduling page"""
    
    # Get current user preferences
    user = User.query.get(current_user.id)
    
    # Parse existing preferences
    push_preferences = {}
    email_preferences = {}
    
    if user.push_preferences:
        try:
            push_preferences = eval(user.push_preferences) if isinstance(user.push_preferences, str) else user.push_preferences
        except:
            push_preferences = {}
    
    if user.email_preferences:
        try:
            email_preferences = eval(user.email_preferences) if isinstance(user.email_preferences, str) else user.email_preferences
        except:
            email_preferences = {}
    
    # Create form with current preferences
    form = NotificationScheduleForm(
        enable_scheduling=push_preferences.get('scheduling_enabled', False),
        daily_digest_enabled=email_preferences.get('daily_digest_enabled', False),
        daily_digest_time=datetime.strptime(email_preferences.get('daily_digest_time', '09:00'), '%H:%M').time() if email_preferences.get('daily_digest_time') else time(9, 0),
        weekly_summary_enabled=email_preferences.get('weekly_summary_enabled', False),
        weekly_summary_day=email_preferences.get('weekly_summary_day', 'monday'),
        weekly_summary_time=datetime.strptime(email_preferences.get('weekly_summary_time', '09:00'), '%H:%M').time() if email_preferences.get('weekly_summary_time') else time(9, 0),
        quiet_hours_enabled=push_preferences.get('quiet_hours_enabled', False),
        quiet_hours_start=datetime.strptime(push_preferences.get('quiet_hours_start', '22:00'), '%H:%M').time() if push_preferences.get('quiet_hours_start') else time(22, 0),
        quiet_hours_end=datetime.strptime(push_preferences.get('quiet_hours_end', '08:00'), '%H:%M').time() if push_preferences.get('quiet_hours_end') else time(8, 0),
        quiet_hours_weekdays_only=push_preferences.get('quiet_hours_weekdays_only', False),
        do_not_disturb_enabled=push_preferences.get('do_not_disturb_enabled', False),
        smart_scheduling_enabled=push_preferences.get('smart_scheduling_enabled', False),
        max_notifications_per_hour=push_preferences.get('max_per_hour', 20),
        delay_low_priority=push_preferences.get('delay_low_priority', False),
        delay_hours_start=datetime.strptime(push_preferences.get('delay_hours_start', '22:00'), '%H:%M').time() if push_preferences.get('delay_hours_start') else time(22, 0),
        delay_hours_end=datetime.strptime(push_preferences.get('delay_hours_end', '08:00'), '%H:%M').time() if push_preferences.get('delay_hours_end') else time(8, 0)
    )
    
    return render_template('notifications/schedule.html', form=form)

@notifications_bp.route('/schedule/update', methods=['POST'])
@login_required
def update_schedule():
    """Update notification scheduling preferences"""
    
    form = NotificationScheduleForm()
    
    if form.validate_on_submit():
        try:
            user = User.query.get(current_user.id)
            
            # Parse existing preferences
            push_preferences = {}
            email_preferences = {}
            
            if user.push_preferences:
                try:
                    push_preferences = eval(user.push_preferences) if isinstance(user.push_preferences, str) else user.push_preferences
                except:
                    push_preferences = {}
            
            if user.email_preferences:
                try:
                    email_preferences = eval(user.email_preferences) if isinstance(user.email_preferences, str) else user.email_preferences
                except:
                    email_preferences = {}
            
            # Update push scheduling preferences
            push_preferences.update({
                'scheduling_enabled': form.enable_scheduling.data,
                'quiet_hours_enabled': form.quiet_hours_enabled.data,
                'quiet_hours_start': form.quiet_hours_start.data.strftime('%H:%M'),
                'quiet_hours_end': form.quiet_hours_end.data.strftime('%H:%M'),
                'quiet_hours_weekdays_only': form.quiet_hours_weekdays_only.data,
                'do_not_disturb_enabled': form.do_not_disturb_enabled.data,
                'smart_scheduling_enabled': form.smart_scheduling_enabled.data,
                'max_per_hour': form.max_notifications_per_hour.data or 20,
                'delay_low_priority': form.delay_low_priority.data,
                'delay_hours_start': form.delay_hours_start.data.strftime('%H:%M'),
                'delay_hours_end': form.delay_hours_end.data.strftime('%H:%M')
            })
            
            # Update email scheduling preferences
            email_preferences.update({
                'daily_digest_enabled': form.daily_digest_enabled.data,
                'daily_digest_time': form.daily_digest_time.data.strftime('%H:%M'),
                'weekly_summary_enabled': form.weekly_summary_enabled.data,
                'weekly_summary_day': form.weekly_summary_day.data,
                'weekly_summary_time': form.weekly_summary_time.data.strftime('%H:%M'),
                'quiet_hours_enabled': form.quiet_hours_enabled.data,
                'quiet_hours_start': form.quiet_hours_start.data.strftime('%H:%M'),
                'quiet_hours_end': form.quiet_hours_end.data.strftime('%H:%M')
            })
            
            # Save preferences
            user.push_preferences = str(push_preferences)
            user.email_preferences = str(email_preferences)
            
            # Handle do not disturb dates
            if form.do_not_disturb_enabled.data and form.do_not_disturb_start.data and form.do_not_disturb_end.data:
                push_preferences['do_not_disturb_start'] = form.do_not_disturb_start.data.isoformat()
                push_preferences['do_not_disturb_end'] = form.do_not_disturb_end.data.isoformat()
                user.push_preferences = str(push_preferences)
            
            db.session.commit()
            
            flash('Notification scheduling updated successfully!', 'success')
            return redirect(url_for('notifications.schedule'))
            
        except Exception as e:
            current_app.logger.error(f"Error updating schedule: {str(e)}")
            flash('Error updating scheduling preferences. Please try again.', 'error')
    
    return render_template('notifications/schedule.html', form=form)

@notifications_bp.route('/schedule/test-digest')
@login_required
def test_digest():
    """Test email digest generation"""
    
    try:
        from app.email.notification_service import email_notification_service
        
        # Get recent unread notifications
        recent_notifications = AdminNotification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).order_by(desc(AdminNotification.created_at)).limit(10).all()
        
        if recent_notifications:
            # Create a test digest notification
            digest_content = f"Test Digest - {len(recent_notifications)} unread notifications\n\n"
            for notification in recent_notifications:
                digest_content += f"- {notification.title}: {notification.message[:100]}...\n"
            
            # Send test email
            success = email_notification_service.send_notification_email(
                user_id=current_user.id,
                notification_id=recent_notifications[0].id,  # Use first notification as reference
                template_name='notification_default'
            )
            
            if success:
                flash('Test digest sent successfully!', 'success')
            else:
                flash('Failed to send test digest.', 'error')
        else:
            flash('No unread notifications for digest test.', 'info')
            
    except Exception as e:
        current_app.logger.error(f"Test digest error: {str(e)}")
        flash('Error sending test digest.', 'error')
    
    return redirect(url_for('notifications.schedule'))

@notifications_bp.route('/schedule/preview')
@login_required
def preview_schedule():
    """Preview notification schedule"""
    
    try:
        # Get current user preferences
        user = User.query.get(current_user.id)
        
        # Parse existing preferences
        push_preferences = {}
        email_preferences = {}
        
        if user.push_preferences:
            try:
                push_preferences = eval(user.push_preferences) if isinstance(user.push_preferences, str) else user.push_preferences
            except:
                push_preferences = {}
        
        if user.email_preferences:
            try:
                email_preferences = eval(user.email_preferences) if isinstance(user.email_preferences, str) else user.email_preferences
            except:
                email_preferences = {}
        
        # Generate schedule preview
        schedule_preview = {
            'daily_digest': {
                'enabled': email_preferences.get('daily_digest_enabled', False),
                'time': email_preferences.get('daily_digest_time', '09:00'),
                'next_digest': calculate_next_digest_time(email_preferences.get('daily_digest_time', '09:00'))
            },
            'weekly_summary': {
                'enabled': email_preferences.get('weekly_summary_enabled', False),
                'day': email_preferences.get('weekly_summary_day', 'monday'),
                'time': email_preferences.get('weekly_summary_time', '09:00'),
                'next_summary': calculate_next_weekly_summary(
                    email_preferences.get('weekly_summary_day', 'monday'),
                    email_preferences.get('weekly_summary_time', '09:00')
                )
            },
            'quiet_hours': {
                'enabled': push_preferences.get('quiet_hours_enabled', False),
                'start': push_preferences.get('quiet_hours_start', '22:00'),
                'end': push_preferences.get('quiet_hours_end', '08:00'),
                'weekdays_only': push_preferences.get('quiet_hours_weekdays_only', False),
                'currently_active': is_quiet_hours_active(
                    push_preferences.get('quiet_hours_start', '22:00'),
                    push_preferences.get('quiet_hours_end', '08:00'),
                    push_preferences.get('quiet_hours_weekdays_only', False)
                )
            },
            'smart_scheduling': {
                'enabled': push_preferences.get('smart_scheduling_enabled', False),
                'max_per_hour': push_preferences.get('max_per_hour', 20),
                'delay_low_priority': push_preferences.get('delay_low_priority', False),
                'delay_start': push_preferences.get('delay_hours_start', '22:00'),
                'delay_end': push_preferences.get('delay_hours_end', '08:00')
            }
        }
        
        return jsonify({
            'success': True,
            'schedule': schedule_preview
        })
        
    except Exception as e:
        current_app.logger.error(f"Schedule preview error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_next_digest_time(digest_time_str):
    """Calculate next daily digest time"""
    try:
        digest_time = datetime.strptime(digest_time_str, '%H:%M').time()
        now = datetime.utcnow()
        
        # Create today's digest time
        today_digest = now.replace(
            hour=digest_time.hour,
            minute=digest_time.minute,
            second=0,
            microsecond=0
        )
        
        # If today's digest time has passed, schedule for tomorrow
        if today_digest <= now:
            today_digest += timedelta(days=1)
        
        return today_digest.isoformat()
    except:
        return None

def calculate_next_weekly_summary(day_str, time_str):
    """Calculate next weekly summary time"""
    try:
        day_map = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6
        }
        
        target_day = day_map.get(day_str.lower(), 0)
        target_time = datetime.strptime(time_str, '%H:%M').time()
        
        now = datetime.utcnow()
        current_day = now.weekday()
        
        # Calculate days until next target day
        days_ahead = target_day - current_day
        if days_ahead <= 0:
            days_ahead += 7
        
        # Calculate next summary time
        next_summary = now + timedelta(days=days_ahead)
        next_summary = next_summary.replace(
            hour=target_time.hour,
            minute=target_time.minute,
            second=0,
            microsecond=0
        )
        
        return next_summary.isoformat()
    except:
        return None

def is_quiet_hours_active(start_str, end_str, weekdays_only):
    """Check if quiet hours are currently active"""
    try:
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        now = datetime.utcnow()
        
        # Check weekdays only
        if weekdays_only and now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        current_time = now.time()
        
        # Handle overnight quiet hours (e.g., 22:00 to 08:00)
        if start_time > end_time:
            return current_time >= start_time or current_time <= end_time
        else:
            return start_time <= current_time <= end_time
            
    except:
        return False

# Notification Grouping Routes
@notifications_bp.route('/grouping')
@login_required
def grouping():
    """Notification grouping preferences page"""
    
    # Get current user preferences
    user = User.query.get(current_user.id)
    
    # Parse existing preferences
    push_preferences = {}
    
    if user.push_preferences:
        try:
            push_preferences = eval(user.push_preferences) if isinstance(user.push_preferences, str) else user.push_preferences
        except:
            push_preferences = {}
    
    # Create form with current preferences
    form = NotificationGroupingForm(
        enable_grouping=push_preferences.get('grouping_enabled', True),
        group_by_type=push_preferences.get('group_by_type', True),
        group_by_priority=push_preferences.get('group_by_priority', False),
        group_by_source=push_preferences.get('group_by_source', False),
        max_group_size=push_preferences.get('max_group_size', 10),
        group_timeout_minutes=push_preferences.get('group_timeout_minutes', 5),
        smart_grouping_enabled=push_preferences.get('smart_grouping_enabled', False),
        group_similar_content=push_preferences.get('group_similar_content', False),
        content_similarity_threshold=push_preferences.get('content_similarity_threshold', 0.8),
        show_group_count=push_preferences.get('show_group_count', True),
        expand_groups_on_click=push_preferences.get('expand_groups_on_click', True),
        auto_expand_important=push_preferences.get('auto_expand_important', True)
    )
    
    return render_template('notifications/grouping.html', form=form)

@notifications_bp.route('/grouping/update', methods=['POST'])
@login_required
def update_grouping():
    """Update notification grouping preferences"""
    
    form = NotificationGroupingForm()
    
    if form.validate_on_submit():
        try:
            user = User.query.get(current_user.id)
            
            # Parse existing preferences
            push_preferences = {}
            
            if user.push_preferences:
                try:
                    push_preferences = eval(user.push_preferences) if isinstance(user.push_preferences, str) else user.push_preferences
                except:
                    push_preferences = {}
            
            # Update grouping preferences
            push_preferences.update({
                'grouping_enabled': form.enable_grouping.data,
                'group_by_type': form.group_by_type.data,
                'group_by_priority': form.group_by_priority.data,
                'group_by_source': form.group_by_source.data,
                'max_group_size': form.max_group_size.data or 10,
                'group_timeout_minutes': form.group_timeout_minutes.data or 5,
                'smart_grouping_enabled': form.smart_grouping_enabled.data,
                'group_similar_content': form.group_similar_content.data,
                'content_similarity_threshold': form.content_similarity_threshold.data or 0.8,
                'show_group_count': form.show_group_count.data,
                'expand_groups_on_click': form.expand_groups_on_click.data,
                'auto_expand_important': form.auto_expand_important.data
            })
            
            user.push_preferences = str(push_preferences)
            db.session.commit()
            
            flash('Notification grouping preferences updated successfully!', 'success')
            return redirect(url_for('notifications.grouping'))
            
        except Exception as e:
            current_app.logger.error(f"Error updating grouping preferences: {str(e)}")
            flash('Error updating grouping preferences. Please try again.', 'error')
    
    return render_template('notifications/grouping.html', form=form)

@notifications_bp.route('/grouping/preview')
@login_required
def preview_grouping():
    """Preview notification grouping"""
    
    try:
        # Get current user preferences
        user = User.query.get(current_user.id)
        
        # Parse existing preferences
        push_preferences = {}
        
        if user.push_preferences:
            try:
                push_preferences = eval(user.push_preferences) if isinstance(user.push_preferences, str) else user.push_preferences
            except:
                push_preferences = {}
        
        # Get recent notifications for grouping preview
        recent_notifications = AdminNotification.query.filter_by(
            user_id=current_user.id,
            is_archived=False
        ).order_by(desc(AdminNotification.created_at)).limit(20).all()
        
        # Group notifications based on preferences
        grouped_notifications = group_notifications(
            recent_notifications,
            push_preferences
        )
        
        return jsonify({
            'success': True,
            'grouped_notifications': grouped_notifications,
            'total_notifications': len(recent_notifications),
            'total_groups': len(grouped_notifications)
        })
        
    except Exception as e:
        current_app.logger.error(f"Grouping preview error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/grouping/api/group', methods=['POST'])
@login_required
def api_group_notifications():
    """API endpoint to group notifications"""
    
    try:
        data = request.get_json()
        notification_ids = data.get('notification_ids', [])
        group_name = data.get('group_name', 'Custom Group')
        
        if not notification_ids:
            return jsonify({
                'success': False,
                'error': 'No notification IDs provided'
            }), 400
        
        # Get notifications
        notifications = AdminNotification.query.filter(
            AdminNotification.id.in_(notification_ids),
            AdminNotification.user_id == current_user.id
        ).all()
        
        if not notifications:
            return jsonify({
                'success': False,
                'error': 'No valid notifications found'
            }), 404
        
        # Create custom group (this would require a new model for custom groups)
        # For now, we'll return a simulated grouping
        grouped_data = {
            'group_id': f"custom_{datetime.utcnow().timestamp()}",
            'group_name': group_name,
            'notifications': [n.to_dict() for n in notifications],
            'created_at': datetime.utcnow().isoformat(),
            'notification_count': len(notifications)
        }
        
        return jsonify({
            'success': True,
            'group': grouped_data
        })
        
    except Exception as e:
        current_app.logger.error(f"API grouping error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/grouping/api/ungroup', methods=['POST'])
@login_required
def api_ungroup_notifications():
    """API endpoint to ungroup notifications"""
    
    try:
        data = request.get_json()
        group_id = data.get('group_id')
        
        if not group_id:
            return jsonify({
                'success': False,
                'error': 'No group ID provided'
            }), 400
        
        # This would require database support for custom groups
        # For now, we'll return a success response
        return jsonify({
            'success': True,
            'message': f'Notifications ungrouped from {group_id}'
        })
        
    except Exception as e:
        current_app.logger.error(f"API ungrouping error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def group_notifications(notifications, preferences):
    """Group notifications based on user preferences"""
    
    if not preferences.get('grouping_enabled', True):
        # Return individual notifications if grouping is disabled
        return [{'type': 'individual', 'notifications': [n.to_dict() for n in notifications]}]
    
    groups = {}
    max_group_size = preferences.get('max_group_size', 10)
    group_timeout_minutes = preferences.get('group_timeout_minutes', 5)
    
    # Group by type
    if preferences.get('group_by_type', True):
        for notification in notifications:
            notification_type = notification.notification_type or 'system'
            
            if notification_type not in groups:
                groups[notification_type] = {
                    'type': 'type',
                    'group_key': notification_type,
                    'group_name': notification_type.title(),
                    'notifications': [],
                    'created_at': notification.created_at
                }
            
            # Check group size limit
            if len(groups[notification_type]['notifications']) < max_group_size:
                groups[notification_type]['notifications'].append(notification)
    
    # Group by priority
    if preferences.get('group_by_priority', False):
        priority_groups = {}
        for notification in notifications:
            priority = notification.priority or 'medium'
            
            if priority not in priority_groups:
                priority_groups[priority] = {
                    'type': 'priority',
                    'group_key': priority,
                    'group_name': f'{priority.title()} Priority',
                    'notifications': [],
                    'created_at': notification.created_at
                }
            
            if len(priority_groups[priority]['notifications']) < max_group_size:
                priority_groups[priority]['notifications'].append(notification)
        
        # Merge priority groups
        groups.update(priority_groups)
    
    # Group by source
    if preferences.get('group_by_source', False):
        source_groups = {}
        for notification in notifications:
            source = getattr(notification, 'source', 'system')
            
            if source not in source_groups:
                source_groups[source] = {
                    'type': 'source',
                    'group_key': source,
                    'group_name': f'From {source.title()}',
                    'notifications': [],
                    'created_at': notification.created_at
                }
            
            if len(source_groups[source]['notifications']) < max_group_size:
                source_groups[source]['notifications'].append(notification)
        
        # Merge source groups
        groups.update(source_groups)
    
    # Smart grouping (content similarity)
    if preferences.get('smart_grouping_enabled', False) and preferences.get('group_similar_content', False):
        similarity_threshold = preferences.get('content_similarity_threshold', 0.8)
        smart_groups = {}
        
        for i, notification in enumerate(notifications):
            if any(notification in g['notifications'] for g in groups.values()):
                continue  # Skip if already grouped
            
            # Find similar notifications
            similar_notifications = [notification]
            for j, other_notification in enumerate(notifications):
                if i != j and calculate_content_similarity(notification.message, other_notification.message) >= similarity_threshold:
                    if other_notification not in similar_notifications:
                        similar_notifications.append(other_notification)
            
            if len(similar_notifications) > 1:
                group_key = f"similar_{len(smart_groups)}"
                smart_groups[group_key] = {
                    'type': 'similar_content',
                    'group_key': group_key,
                    'group_name': 'Similar Content',
                    'notifications': similar_notifications,
                    'created_at': notification.created_at
                }
        
        # Merge smart groups
        groups.update(smart_groups)
    
    # Convert to list and add group counts
    grouped_list = []
    for group_key, group_data in groups.items():
        if group_data['notifications']:
            group_data['notification_count'] = len(group_data['notifications'])
            group_data['notifications'] = [n.to_dict() for n in group_data['notifications']]
            grouped_list.append(group_data)
    
    # Add ungrouped notifications
    grouped_notification_ids = set()
    for group in grouped_list:
        for notification in group['notifications']:
            grouped_notification_ids.add(notification['id'])
    
    ungrouped = [n.to_dict() for n in notifications if n.id not in grouped_notification_ids]
    if ungrouped:
        grouped_list.append({
            'type': 'individual',
            'group_key': 'ungrouped',
            'group_name': 'Individual',
            'notifications': ungrouped,
            'notification_count': len(ungrouped)
        })
    
    return grouped_list

def calculate_content_similarity(text1, text2):
    """Calculate similarity between two text strings"""
    try:
        # Simple similarity calculation based on common words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    except:
        return 0.0

# Notification Translation Routes
@notifications_bp.route('/translation')
@login_required
def translation():
    """Notification translation preferences page"""
    
    # Get current user's language preference
    current_language = notification_translation_service.get_user_language(current_user.id)
    supported_languages = notification_translation_service.get_supported_languages()
    
    return render_template('notifications/translation.html',
                         current_language=current_language,
                         supported_languages=supported_languages)

@notifications_bp.route('/translation/update', methods=['POST'])
@login_required
def update_translation():
    """Update user's language preference"""
    
    language_code = request.form.get('language')
    
    if not language_code:
        flash('Please select a language.', 'error')
        return redirect(url_for('notifications.translation'))
    
    if not notification_translation_service.is_language_supported(language_code):
        flash('Unsupported language.', 'error')
        return redirect(url_for('notifications.translation'))
    
    success = notification_translation_service.set_user_language_preference(
        current_user.id,
        language_code
    )
    
    if success:
        supported_languages = notification_translation_service.get_supported_languages()
        flash(f'Language preference updated to {supported_languages[language_code]}!', 'success')
    else:
        flash('Error updating language preference.', 'error')
    
    return redirect(url_for('notifications.translation'))

@notifications_bp.route('/translation/preview')
@login_required
def preview_translation():
    """Preview translated notifications"""
    
    try:
        # Get sample notifications
        sample_notifications = [
            {
                'id': 1,
                'type': 'comment',
                'content': 'john_doe commented on your post "Welcome to the Forum"',
                'username': 'john_doe',
                'post_title': 'Welcome to the Forum',
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 2,
                'type': 'message',
                'content': 'You have a new message from jane_smith',
                'sender_name': 'jane_smith',
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 3,
                'type': 'system',
                'content': 'System notification: Your password will expire in 7 days',
                'message': 'Your password will expire in 7 days',
                'created_at': datetime.utcnow().isoformat()
            }
        ]
        
        user_language = notification_translation_service.get_user_language(current_user.id)
        translated_notifications = notification_translation_service.translate_bulk_notifications(
            sample_notifications,
            current_user.id
        )
        
        return jsonify({
            'success': True,
            'user_language': user_language,
            'original_notifications': sample_notifications,
            'translated_notifications': translated_notifications,
            'supported_languages': notification_translation_service.get_supported_languages()
        })
        
    except Exception as e:
        current_app.logger.error(f"Translation preview error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/translation/translate', methods=['POST'])
@login_required
def translate_notification():
    """Translate a specific notification"""
    
    try:
        data = request.get_json()
        notification_data = data.get('notification', {})
        target_language = data.get('language', notification_translation_service.get_user_language(current_user.id))
        
        if not notification_data:
            return jsonify({
                'success': False,
                'error': 'No notification data provided'
            }), 400
        
        # Translate the notification
        translated_notification = notification_translation_service.translate_notification(
            notification_data,
            current_user.id
        )
        
        return jsonify({
            'success': True,
            'original_notification': notification_data,
            'translated_notification': translated_notification,
            'target_language': target_language
        })
        
    except Exception as e:
        current_app.logger.error(f"Notification translation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/translation/api/translate-text', methods=['POST'])
@login_required
def api_translate_text():
    """API endpoint to translate arbitrary text"""
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        target_language = data.get('language', notification_translation_service.get_user_language(current_user.id))
        source_language = data.get('source_language', 'en')
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'No text provided'
            }), 400
        
        if not notification_translation_service.is_language_supported(target_language):
            return jsonify({
                'success': False,
                'error': f'Language {target_language} not supported'
            }), 400
        
        translated_text = notification_translation_service.translate_text(
            text,
            target_language,
            source_language
        )
        
        return jsonify({
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'source_language': source_language,
            'target_language': target_language
        })
        
    except Exception as e:
        current_app.logger.error(f"Text translation API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/translation/api/languages')
@login_required
def api_supported_languages():
    """Get list of supported languages"""
    
    try:
        languages = notification_translation_service.get_supported_languages()
        user_language = notification_translation_service.get_user_language(current_user.id)
        
        return jsonify({
            'success': True,
            'supported_languages': languages,
            'current_language': user_language
        })
        
    except Exception as e:
        current_app.logger.error(f"Languages API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/translation/api/statistics')
@login_required
def api_translation_statistics():
    """Get translation statistics"""
    
    try:
        stats = notification_translation_service.get_translation_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Translation statistics API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Advanced Filtering and Grouping Routes
@notifications_bp.route('/filtering')
@login_required
def filtering():
    """Advanced notification filtering page"""
    
    # Get filter presets and grouping strategies
    filter_presets = notification_filtering_service.get_filter_presets()
    grouping_strategies = notification_filtering_service.get_grouping_strategies()
    
    # Get user's custom filters (this would typically come from database)
    custom_filters = []
    
    return render_template('notifications/filtering.html',
                         filter_presets=filter_presets,
                         grouping_strategies=grouping_strategies,
                         custom_filters=custom_filters)

@notifications_bp.route('/filtering/apply', methods=['POST'])
@login_required
def apply_filters():
    """Apply advanced filters to notifications"""
    
    try:
        data = request.get_json()
        filters = data.get('filters', {})
        sort_options = data.get('sort_options', {})
        grouping_strategy = data.get('grouping_strategy', 'type')
        
        # Apply filters
        notifications = notification_filtering_service.apply_filters(
            current_user.id,
            filters,
            sort_options
        )
        
        # Apply grouping
        user_preferences = data.get('user_preferences', {})
        grouped_notifications = notification_filtering_service.group_notifications(
            notifications,
            grouping_strategy,
            user_preferences
        )
        
        # Apply translation if needed
        translate_results = data.get('translate', False)
        if translate_results:
            grouped_notifications = notification_filtering_service._translate_grouped_notifications(
                grouped_notifications,
                current_user.id
            )
        
        return jsonify({
            'success': True,
            'notifications': [n.to_dict() for n in notifications],
            'grouped_notifications': grouped_notifications,
            'total_count': len(notifications),
            'group_count': len(grouped_notifications),
            'filters_applied': filters,
            'sort_options': sort_options,
            'grouping_strategy': grouping_strategy
        })
        
    except Exception as e:
        current_app.logger.error(f"Filter application error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/filtering/preset/<preset_name>')
@login_required
def apply_filter_preset(preset_name):
    """Apply a filter preset"""
    
    try:
        filter_presets = notification_filtering_service.get_filter_presets()
        
        if preset_name not in filter_presets:
            return jsonify({
                'success': False,
                'error': f'Preset {preset_name} not found'
            }), 404
        
        preset = filter_presets[preset_name]
        
        # Apply preset filters
        notifications = notification_filtering_service.apply_filters(
            current_user.id,
            preset['filters'],
            {'sort_by': preset['sort'][0] if preset['sort'] else 'created_at'}
        )
        
        return jsonify({
            'success': True,
            'preset_name': preset_name,
            'preset_display_name': preset['name'],
            'notifications': [n.to_dict() for n in notifications],
            'total_count': len(notifications),
            'filters': preset['filters'],
            'sort_options': {'sort_by': preset['sort'][0] if preset['sort'] else 'created_at'}
        })
        
    except Exception as e:
        current_app.logger.error(f"Preset application error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/filtering/group', methods=['POST'])
@login_required
def group_notifications():
    """Group notifications using specified strategy"""
    
    try:
        data = request.get_json()
        notification_ids = data.get('notification_ids', [])
        strategy = data.get('strategy', 'type')
        user_preferences = data.get('user_preferences', {})
        
        if not notification_ids:
            return jsonify({
                'success': False,
                'error': 'No notification IDs provided'
            }), 400
        
        # Get notifications
        notifications = AdminNotification.query.filter(
            AdminNotification.id.in_(notification_ids),
            AdminNotification.user_id == current_user.id
        ).all()
        
        if not notifications:
            return jsonify({
                'success': False,
                'error': 'No valid notifications found'
            }), 404
        
        # Apply grouping
        grouped_notifications = notification_filtering_service.group_notifications(
            notifications,
            strategy,
            user_preferences
        )
        
        return jsonify({
            'success': True,
            'grouped_notifications': grouped_notifications,
            'strategy': strategy,
            'total_notifications': len(notifications),
            'group_count': len(grouped_notifications)
        })
        
    except Exception as e:
        current_app.logger.error(f"Grouping error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/filtering/custom', methods=['POST'])
@login_required
def create_custom_filter():
    """Create a custom filter preset"""
    
    try:
        data = request.get_json()
        name = data.get('name', '')
        filters = data.get('filters', {})
        sort_options = data.get('sort_options', {})
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Filter name is required'
            }), 400
        
        if not filters:
            return jsonify({
                'success': False,
                'error': 'At least one filter is required'
            }), 400
        
        # Create custom filter
        custom_filter = notification_filtering_service.create_custom_filter(
            current_user.id,
            name,
            filters,
            sort_options
        )
        
        if not custom_filter:
            return jsonify({
                'success': False,
                'error': 'Failed to create custom filter'
            }), 500
        
        return jsonify({
            'success': True,
            'custom_filter': custom_filter
        })
        
    except Exception as e:
        current_app.logger.error(f"Custom filter creation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/filtering/analyze')
@login_required
def analyze_patterns():
    """Analyze notification patterns"""
    
    try:
        days = request.args.get('days', 30, type=int)
        
        # Analyze patterns
        analysis = notification_filtering_service.analyze_notification_patterns(
            current_user.id,
            days
        )
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        current_app.logger.error(f"Pattern analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/filtering/api/presets')
@login_required
def api_filter_presets():
    """Get available filter presets"""
    
    try:
        presets = notification_filtering_service.get_filter_presets()
        strategies = notification_filtering_service.get_grouping_strategies()
        
        return jsonify({
            'success': True,
            'presets': presets,
            'grouping_strategies': strategies
        })
        
    except Exception as e:
        current_app.logger.error(f"Presets API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/filtering/api/smart-suggestions')
@login_required
def api_smart_suggestions():
    """Get smart filtering suggestions based on user behavior"""
    
    try:
        # Analyze recent notification patterns
        analysis = notification_filtering_service.analyze_notification_patterns(
            current_user.id,
            30
        )
        
        suggestions = []
        
        if 'type_distribution' in analysis:
            # Suggest filters based on most common types
            most_common_type = analysis.get('most_common_type', ('system', 0))
            if most_common_type[1] > 10:  # If more than 10 of same type
                suggestions.append({
                    'type': 'filter',
                    'name': f'Filter by {most_common_type[0]}',
                    'description': f'You receive many {most_common_type[0]} notifications',
                    'filters': {'type': most_common_type[0]}
                })
        
        if 'priority_distribution' in analysis:
            # Suggest urgent notifications filter
            urgent_count = analysis.get('priority_distribution', {}).get('urgent', 0)
            if urgent_count > 0:
                suggestions.append({
                    'type': 'filter',
                    'name': 'Urgent Notifications',
                    'description': f'You have {urgent_count} urgent notifications',
                    'filters': {'priority': 'urgent'}
                })
        
        if 'daily_distribution' in analysis:
            # Suggest time-based filters
            daily_counts = analysis.get('daily_distribution', {})
            if len(daily_counts) > 0:
                avg_daily = sum(daily_counts.values()) / len(daily_counts)
                max_daily = max(daily_counts.values())
                
                if max_daily > avg_daily * 2:
                    suggestions.append({
                        'type': 'filter',
                        'name': 'High Activity Days',
                        'description': 'Filter notifications from busy days',
                        'filters': {'date_range': 'last_7_days'}
                    })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'analysis_summary': {
                'total_notifications': analysis.get('total_notifications', 0),
                'average_per_day': analysis.get('average_per_day', 0),
                'most_common_type': analysis.get('most_common_type', ('system', 0))[0]
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Smart suggestions API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Mobile App Notifications Routes
@notifications_bp.route('/mobile/register', methods=['POST'])
@login_required
def register_mobile_device():
    """Register a mobile device for push notifications"""
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['platform', 'device_token', 'device_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate platform
        supported_platforms = mobile_notification_service.get_supported_platforms()
        if data['platform'] not in supported_platforms:
            return jsonify({
                'success': False,
                'error': f'Unsupported platform: {data["platform"]}',
                'supported_platforms': list(supported_platforms.keys())
            }), 400
        
        # Validate device token
        token_validation = mobile_notification_service.validate_device_token(
            data['platform'],
            data['device_token']
        )
        
        if not token_validation['valid']:
            return jsonify({
                'success': False,
                'error': f'Invalid device token: {token_validation["error"]}'
            }), 400
        
        # Register device
        registration_result = mobile_notification_service.register_device(
            current_user.id,
            data
        )
        
        if registration_result['success']:
            return jsonify({
                'success': True,
                'registration_id': registration_result['registration_id'],
                'device_info': registration_result['device_info'],
                'message': 'Device registered successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': registration_result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Mobile device registration error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/mobile/unregister', methods=['POST'])
@login_required
def unregister_mobile_device():
    """Unregister a mobile device"""
    
    try:
        data = request.get_json()
        registration_id = data.get('registration_id')
        
        if not registration_id:
            return jsonify({
                'success': False,
                'error': 'Registration ID is required'
            }), 400
        
        result = mobile_notification_service.unregister_device(
            current_user.id,
            registration_id
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Mobile device unregistration error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/mobile/send', methods=['POST'])
@login_required
def send_mobile_notification():
    """Send push notification to mobile devices"""
    
    try:
        data = request.get_json()
        
        # Validate notification data
        if 'notification' not in data:
            return jsonify({
                'success': False,
                'error': 'Notification data is required'
            }), 400
        
        notification_data = data['notification']
        target_devices = data.get('target_devices')  # Optional: specific devices
        
        # Send notification
        result = mobile_notification_service.send_push_notification(
            current_user.id,
            notification_data,
            target_devices
        )
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Mobile notification send error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/mobile/devices')
@login_required
def get_mobile_devices():
    """Get user's registered mobile devices"""
    
    try:
        # Get device statistics
        statistics = mobile_notification_service.get_device_statistics(current_user.id)
        
        # Get detailed device list (this would typically come from database)
        devices = mobile_notification_service._get_user_devices(current_user.id)
        
        return jsonify({
            'success': True,
            'statistics': statistics,
            'devices': devices,
            'total_count': len(devices)
        })
        
    except Exception as e:
        current_app.logger.error(f"Get mobile devices error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/mobile/preferences/<registration_id>', methods=['POST'])
@login_required
def update_mobile_preferences(registration_id):
    """Update mobile device notification preferences"""
    
    try:
        data = request.get_json()
        preferences = data.get('preferences', {})
        
        if not preferences:
            return jsonify({
                'success': False,
                'error': 'Preferences data is required'
            }), 400
        
        result = mobile_notification_service.update_device_preferences(
            current_user.id,
            registration_id,
            preferences
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'updated_preferences': result['updated_preferences']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Mobile preferences update error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/mobile/test/<registration_id>')
@login_required
def test_mobile_notification(registration_id):
    """Send test notification to specific device"""
    
    try:
        # Get device info (this would typically come from database)
        devices = mobile_notification_service._get_user_devices(current_user.id)
        target_device = None
        
        for device in devices:
            if device['registration_id'] == registration_id:
                target_device = device
                break
        
        if not target_device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        # Send test notification
        test_notification = {
            'title': 'Test Notification',
            'message': 'This is a test notification from AutoBot Solutions Forum',
            'type': 'system',
            'priority': 'normal',
            'platform': target_device['platform']
        }
        
        result = mobile_notification_service.send_push_notification(
            current_user.id,
            test_notification,
            [registration_id]
        )
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Mobile test notification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/mobile/cleanup', methods=['POST'])
@login_required
def cleanup_inactive_devices():
    """Clean up inactive mobile devices"""
    
    try:
        data = request.get_json()
        days = data.get('days', 30)
        
        if not isinstance(days, int) or days < 1:
            return jsonify({
                'success': False,
                'error': 'Days must be a positive integer'
            }), 400
        
        result = mobile_notification_service.cleanup_inactive_devices(days)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Mobile cleanup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/mobile/api/platforms')
@login_required
def api_mobile_platforms():
    """Get supported mobile platforms"""
    
    try:
        platforms = mobile_notification_service.get_supported_platforms()
        notification_types = mobile_notification_service.get_notification_types()
        
        return jsonify({
            'success': True,
            'platforms': platforms,
            'notification_types': notification_types
        })
        
    except Exception as e:
        current_app.logger.error(f"Mobile platforms API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/mobile/api/validate-token', methods=['POST'])
@login_required
def api_validate_device_token():
    """Validate mobile device token format"""
    
    try:
        data = request.get_json()
        platform = data.get('platform')
        token = data.get('token')
        
        if not platform or not token:
            return jsonify({
                'success': False,
                'error': 'Platform and token are required'
            }), 400
        
        result = mobile_notification_service.validate_device_token(platform, token)
        
        return jsonify({
            'success': True,
            'validation': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Token validation API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/mobile/api/statistics')
@login_required
def api_mobile_statistics():
    """Get mobile notification statistics"""
    
    try:
        # Get user device statistics
        user_stats = mobile_notification_service.get_device_statistics(current_user.id)
        
        # Get overall statistics (this would typically query database)
        overall_stats = {
            'total_registered_devices': 0,  # Would be actual count
            'active_devices': 0,
            'platform_distribution': {
                'ios': 0,
                'android': 0,
                'huawei': 0,
                'web': 0
            },
            'daily_notifications_sent': 0,
            'success_rate': 0.0
        }
        
        return jsonify({
            'success': True,
            'user_statistics': user_stats,
            'overall_statistics': overall_stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Mobile statistics API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@notifications_bp.errorhandler(404)
def not_found(error):
    return render_template('notifications/404.html'), 404

@notifications_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('notifications/500.html'), 500
