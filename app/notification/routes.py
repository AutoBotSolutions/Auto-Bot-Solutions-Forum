from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Notification

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('notification/notifications.html', notifications=notifications, unread_count=unread_count)

@notification_bp.route('/<int:notification_id>/read')
@login_required
def mark_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
        if notification.link:
            return redirect(notification.link)
    return redirect(url_for('notification.notifications'))

@notification_bp.route('/read_all')
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notification.notifications'))
