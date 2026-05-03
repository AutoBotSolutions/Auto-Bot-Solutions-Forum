from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Message, User
from app.message.forms import MessageForm

message_bp = Blueprint('message', __name__, url_prefix='/messages')

@message_bp.route('/')
@login_required
def inbox():
    messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).all()
    unread_count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return render_template('message/inbox.html', messages=messages, unread_count=unread_count)

@message_bp.route('/sent')
@login_required
def sent():
    messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    return render_template('message/sent.html', messages=messages)

@message_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_message():
    form = MessageForm()
    users = User.query.filter(User.id != current_user.id).all()
    if form.validate_on_submit():
        message = Message(
            sender_id=current_user.id,
            receiver_id=form.receiver.data,
            content=form.content.data
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('message.inbox'))
    return render_template('message/new_message.html', form=form, users=users)

@message_bp.route('/<int:message_id>/read')
@login_required
def mark_read(message_id):
    message = Message.query.get_or_404(message_id)
    if message.receiver_id == current_user.id:
        message.is_read = True
        db.session.commit()
    return redirect(url_for('message.inbox'))

@message_bp.route('/<int:message_id>/delete')
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.sender_id == current_user.id or message.receiver_id == current_user.id:
        db.session.delete(message)
        db.session.commit()
        flash('Message deleted successfully!', 'success')
    return redirect(url_for('message.inbox'))
