from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import os
from app import db
from app.models import Message, User, MessageSearchAnalytics
from app.message.forms import MessageForm, MessageSearchForm, MessageThreadForm, MessageTemplateForm, MessageComposeForm, MessageAttachmentForm, MessageForwardForm, MessageQuoteForm, MessageExportForm
from app.utils.message_search import MessageSearchEngine, get_search_suggestions, get_popular_search_terms
from app.utils.message_threading import MessageThreadingEngine
from app.utils.rich_text import RichTextProcessor, MessageTemplateManager, format_message_content, generate_message_preview
from app.utils.file_attachments import FileAttachmentManager, upload_message_attachment
from app.utils.message_forwarding import MessageForwardingManager, forward_message, create_message_quote, export_message
from app.models import MessageAttachment, MessageForward

message_bp = Blueprint('message', __name__, url_prefix='/messages')

@message_bp.route('/')
def inbox():
    try:
        # Manual authentication check to avoid Flask-Login decorator interference
        from flask_login import current_user
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        # Get messages for the current user
        user_inbox = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).all()
        unread_count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
        
        # Bypass Flask-Login's ensure_sync wrapper using helper function
        from app.utils.template_helper import render_template_bypass
        return render_template_bypass('message/inbox.html', messages=user_inbox, unread_count=unread_count, current_user=current_user)
        
    except Exception as e:
        # Log error and re-raise
        try:
            from app.error_system import monitor_error
            monitor_error(e, context={'route_function': 'inbox', 'blueprint': 'message'})
        except:
            pass
        raise e

@message_bp.route('/test-template-error')
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
                         context={'route_function': 'test_template_error', 'blueprint': 'message', 'test_route': True},
                         additional_data={
                             'request_endpoint': request.endpoint if request else None,
                             'route_type': 'test_route_no_auth'
                         })
        except:
            pass  # Don't let error monitoring fail
        raise route_error

@message_bp.route('/sent')
@login_required
def sent():
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    return render_template('message/sent.html', sent_messages=sent_messages)

@message_bp.route('/new', methods=['GET', 'POST'])
def new_message():
    try:
        # Manual authentication check to avoid Flask-Login decorator interference
        from flask_login import current_user
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        form = MessageForm()
        users = User.query.filter(User.id != current_user.id).all()
        if form.validate_on_submit():
            message = Message(
                sender_id=current_user.id,
                receiver_id=form.receiver.data,
                subject=form.subject.data,
                content=form.content.data
            )
            db.session.add(message)
            db.session.commit()
            
            receiver = User.query.get(form.receiver.data)
            create_notification(
                form.receiver.data,
                f'New message from {current_user.username}',
                url_for('message.inbox'),
                notification_type='message'
            )
            
            flash('Message sent successfully!', 'success')
            return redirect(url_for('message.inbox'))
        
        # Bypass Flask-Login's ensure_sync wrapper using helper function
        from app.utils.template_helper import render_template_bypass
        return render_template_bypass('message/new_message.html', form=form, users=users, current_user=current_user)
        
    except Exception as e:
        # Log error and re-raise
        try:
            from app.error_system import monitor_error
            monitor_error(e, context={'route_function': 'new_message', 'blueprint': 'message'})
        except:
            pass
        raise e

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

# Search Routes
@message_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search_messages():
    """Advanced message search with filtering options"""
    form = MessageSearchForm()
    search_results = None
    search_engine = MessageSearchEngine()
    
    # Populate sender choices
    users = User.query.filter(User.id != current_user.id).all()
    form.sender_id.choices = [(0, 'All Senders')] + [(user.id, user.username) for user in users]
    
    if form.validate_on_submit():
        # Build filters dictionary
        filters = {}
        
        if form.date_from.data:
            filters['date_from'] = form.date_from.data
        if form.date_to.data:
            filters['date_to'] = form.date_to.data
        if form.sender_id.data and form.sender_id.data != 0:
            filters['sender_id'] = form.sender_id.data
        if form.is_read.data != '':
            filters['is_read'] = form.is_read.data
        if form.priority.data:
            filters['priority'] = form.priority.data
        if form.has_attachments.data != '':
            filters['has_attachments'] = form.has_attachments.data
        if form.thread_id.data:
            filters['thread_id'] = form.thread_id.data
        
        # Perform search
        search_results = search_engine.search_messages(
            query=form.query.data or '',
            user_id=current_user.id,
            filters=filters,
            sort_by=form.sort_by.data,
            page=form.page.data,
            per_page=form.per_page.data,
            search_type=form.search_type.data
        )
        
        return render_template('message/search_results.html', 
                             form=form, 
                             search_results=search_results,
                             users=users)
    
    return render_template('message/search.html', form=form, users=users)

@message_bp.route('/search/suggestions')
@login_required
def search_suggestions():
    """Get search suggestions based on query"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    suggestions = get_search_suggestions(query, current_user.id, limit)
    
    return jsonify({
        'suggestions': suggestions
    })

@message_bp.route('/search/analytics')
@login_required
def search_analytics():
    """Get search analytics for the current user"""
    days = int(request.args.get('days', 30))
    
    from app.utils.message_search import get_search_analytics_summary
    analytics = get_search_analytics_summary(current_user.id, days)
    popular_terms = get_popular_search_terms(days, 10)
    
    return render_template('message/search_analytics.html',
                         analytics=analytics,
                         popular_terms=popular_terms)

@message_bp.route('/search/export')
@login_required
def export_search_results():
    """Export search results to CSV"""
    query = request.args.get('query', '')
    search_type = request.args.get('search_type', 'basic')
    sort_by = request.args.get('sort_by', 'relevance')
    
    # Build filters from URL parameters
    filters = {}
    if request.args.get('date_from'):
        filters['date_from'] = request.args.get('date_from')
    if request.args.get('date_to'):
        filters['date_to'] = request.args.get('date_to')
    if request.args.get('sender_id'):
        filters['sender_id'] = int(request.args.get('sender_id'))
    if request.args.get('is_read') != '':
        filters['is_read'] = request.args.get('is_read') == 'true'
    if request.args.get('priority'):
        filters['priority'] = request.args.get('priority')
    if request.args.get('has_attachments') != '':
        filters['has_attachments'] = request.args.get('has_attachments') == 'true'
    
    # Perform search
    search_engine = MessageSearchEngine()
    search_results = search_engine.search_messages(
        query=query,
        user_id=current_user.id,
        filters=filters,
        sort_by=sort_by,
        page=1,
        per_page=1000,  # Large number for export
        search_type=search_type
    )
    
    # Generate CSV
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Sender', 'Receiver', 'Content', 'Created At', 'Is Read'])
    
    # Write data
    for result in search_results['results']:
        writer.writerow([
            result['id'],
            result['sender_name'],
            'You' if result['receiver_id'] == current_user.id else result['receiver_id'],
            result['content'],
            result['created_at'],
            result['is_read']
        ])
    
    output.seek(0)
    
    # Create response
    from flask import Response
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=message_search_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )
    
    return response

@message_bp.route('/search/advanced', methods=['GET', 'POST'])
@login_required
def advanced_search():
    """Advanced search with Boolean operators and field-specific search"""
    form = MessageSearchForm()
    search_results = None
    search_engine = MessageSearchEngine()
    
    # Populate sender choices
    users = User.query.filter(User.id != current_user.id).all()
    form.sender_id.choices = [(0, 'All Senders')] + [(user.id, user.username) for user in users]
    
    # Set default search type to boolean for advanced search
    form.search_type.data = 'boolean'
    
    if form.validate_on_submit():
        # Build filters dictionary
        filters = {}
        
        if form.date_from.data:
            filters['date_from'] = form.date_from.data
        if form.date_to.data:
            filters['date_to'] = form.date_to.data
        if form.sender_id.data and form.sender_id.data != 0:
            filters['sender_id'] = form.sender_id.data
        if form.is_read.data != '':
            filters['is_read'] = form.is_read.data
        if form.priority.data:
            filters['priority'] = form.priority.data
        if form.has_attachments.data != '':
            filters['has_attachments'] = form.has_attachments.data
        
        # Perform Boolean search
        search_results = search_engine.search_messages(
            query=form.query.data or '',
            user_id=current_user.id,
            filters=filters,
            sort_by=form.sort_by.data,
            page=form.page.data,
            per_page=form.per_page.data,
            search_type='boolean'
        )
        
        return render_template('message/advanced_search_results.html',
                             form=form,
                             search_results=search_results,
                             users=users)
    
    return render_template('message/advanced_search.html', form=form, users=users)

# Threading Routes
@message_bp.route('/threads')
@login_required
def list_threads():
    """List all threads for the current user"""
    threading_engine = MessageThreadingEngine()
    
    # Get query parameters
    thread_type = request.args.get('type', '')
    include_archived = request.args.get('archived', 'false').lower() == 'true'
    sort_by = request.args.get('sort', 'last_message_at')
    sort_order = request.args.get('order', 'desc')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Get threads
    threads_data = threading_engine.get_user_threads(
        user_id=current_user.id,
        include_archived=include_archived,
        thread_type=thread_type if thread_type else None,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page
    )
    
    return render_template('message/threads.html', 
                         threads=threads_data['threads'],
                         pagination={
                             'total': threads_data['total'],
                             'page': threads_data['page'],
                             'per_page': threads_data['per_page'],
                             'total_pages': threads_data['total_pages']
                         },
                         thread_type=thread_type,
                         include_archived=include_archived,
                         sort_by=sort_by,
                         sort_order=sort_order)

@message_bp.route('/threads/<int:thread_id>')
@login_required
def view_thread(thread_id):
    """View a specific thread with all messages"""
    threading_engine = MessageThreadingEngine()
    
    try:
        # Get thread tree
        thread_tree = threading_engine.get_thread_tree(thread_id, current_user.id)
        
        # Get thread statistics
        thread_stats = threading_engine.get_thread_statistics(thread_id)
        
        # Get participant names
        from app.utils.message_threading import get_thread_participant_names
        participant_names = get_thread_participant_names(thread_id)
        
        return render_template('message/thread_view.html',
                             thread_tree=thread_tree,
                             thread_stats=thread_stats,
                             participant_names=participant_names)
    
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('message.list_threads'))

@message_bp.route('/threads/create', methods=['GET', 'POST'])
@login_required
def create_thread():
    """Create a new message thread"""
    form = MessageThreadForm()
    threading_engine = MessageThreadingEngine()
    
    # Populate participant choices
    users = User.query.filter(User.id != current_user.id, User.is_active == True).all()
    form.participants.choices = [(user.id, user.username) for user in users]
    
    if form.validate_on_submit():
        try:
            # Create thread
            thread = threading_engine.create_thread(
                subject=form.subject.data,
                participant_ids=form.participants.data,
                creator_id=current_user.id,
                thread_type=form.thread_type.data,
                priority=form.priority.data
            )
            
            flash(f'Thread "{thread.subject}" created successfully!', 'success')
            return redirect(url_for('message.view_thread', thread_id=thread.id))
        
        except Exception as e:
            flash(f'Error creating thread: {str(e)}', 'error')
    
    return render_template('message/create_thread.html', form=form, users=users)

@message_bp.route('/threads/<int:thread_id>/reply', methods=['GET', 'POST'])
@login_required
def reply_to_thread(thread_id):
    """Reply to a message in a thread"""
    from app.message.forms import MessageForm
    
    form = MessageForm()
    threading_engine = MessageThreadingEngine()
    
    # Get thread info
    thread = threading_engine.get_user_threads(current_user.id)['threads']
    thread_info = next((t for t in thread if t['id'] == thread_id), None)
    
    if not thread_info:
        flash('Thread not found', 'error')
        return redirect(url_for('message.list_threads'))
    
    # Populate receiver choices (thread participants)
    from app.utils.message_threading import get_thread_participant_names
    participant_names = get_thread_participant_names(thread_id)
    participant_names.pop(current_user.id, None)  # Remove current user
    
    form.receiver_id.choices = [(user_id, username) for user_id, username in participant_names.items()]
    
    if form.validate_on_submit():
        try:
            # Create reply message
            message = Message(
                sender_id=current_user.id,
                receiver_id=form.receiver_id.data,
                content=form.content.data
            )
            
            # Add to thread
            threading_engine.add_message_to_thread(message, thread_id)
            
            db.session.add(message)
            db.session.commit()
            
            flash('Reply sent successfully!', 'success')
            return redirect(url_for('message.view_thread', thread_id=thread_id))
        
        except Exception as e:
            flash(f'Error sending reply: {str(e)}', 'error')
    
    return render_template('message/reply_thread.html', 
                         form=form, 
                         thread_info=thread_info,
                         participant_names=participant_names)

@message_bp.route('/threads/<int:thread_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_thread(thread_id):
    """Edit thread settings and participants"""
    form = MessageThreadForm()
    threading_engine = MessageThreadingEngine()
    
    # Get thread
    thread = MessageThread.query.get(thread_id)
    if not thread:
        flash('Thread not found', 'error')
        return redirect(url_for('message.list_threads'))
    
    # Check authorization
    participants = thread.get_participants()
    if current_user.id not in participants:
        flash('You are not authorized to edit this thread', 'error')
        return redirect(url_for('message.view_thread', thread_id=thread_id))
    
    # Populate form with current data
    if request.method == 'GET':
        form.subject.data = thread.subject
        form.thread_type.data = thread.thread_type
        form.priority.data = thread.priority
        form.participants.data = participants
    
    # Populate participant choices
    users = User.query.filter(User.id != current_user.id, User.is_active == True).all()
    form.participants.choices = [(user.id, user.username) for user in users]
    
    if form.validate_on_submit():
        try:
            # Update thread participants
            threading_engine.update_thread_participants(
                thread_id=thread_id,
                participant_ids=form.participants.data,
                user_id=current_user.id
            )
            
            # Update thread properties
            thread.subject = form.subject.data
            thread.thread_type = form.thread_type.data
            thread.priority = form.priority.data
            
            db.session.commit()
            
            flash('Thread updated successfully!', 'success')
            return redirect(url_for('message.view_thread', thread_id=thread_id))
        
        except Exception as e:
            flash(f'Error updating thread: {str(e)}', 'error')
    
    return render_template('message/edit_thread.html', form=form, thread=thread, users=users)

@message_bp.route('/threads/<int:thread_id>/archive')
@login_required
def archive_thread(thread_id):
    """Archive or unarchive a thread"""
    threading_engine = MessageThreadingEngine()
    
    thread = MessageThread.query.get(thread_id)
    if not thread:
        flash('Thread not found', 'error')
        return redirect(url_for('message.list_threads'))
    
    # Toggle archive status
    new_status = not thread.is_archived
    success = threading_engine.archive_thread(thread_id, current_user.id)
    
    if success:
        status_text = 'archived' if new_status else 'unarchived'
        flash(f'Thread {status_text} successfully!', 'success')
    else:
        flash('Error updating thread status', 'error')
    
    return redirect(url_for('message.list_threads'))

@message_bp.route('/threads/<int:thread_id>/pin')
@login_required
def pin_thread(thread_id):
    """Pin or unpin a thread"""
    threading_engine = MessageThreadingEngine()
    
    thread = MessageThread.query.get(thread_id)
    if not thread:
        flash('Thread not found', 'error')
        return redirect(url_for('message.list_threads'))
    
    # Toggle pin status
    new_status = not thread.is_pinned
    success = threading_engine.pin_thread(thread_id, current_user.id, new_status)
    
    if success:
        status_text = 'pinned' if new_status else 'unpinned'
        flash(f'Thread {status_text} successfully!', 'success')
    else:
        flash('Error updating thread status', 'error')
    
    return redirect(url_for('message.list_threads'))

@message_bp.route('/threads/<int:thread_id>/mute')
@login_required
def mute_thread(thread_id):
    """Mute or unmute a thread"""
    threading_engine = MessageThreadingEngine()
    
    thread = MessageThread.query.get(thread_id)
    if not thread:
        flash('Thread not found', 'error')
        return redirect(url_for('message.list_threads'))
    
    # Toggle mute status
    new_status = not thread.is_muted
    success = threading_engine.mute_thread(thread_id, current_user.id, new_status)
    
    if success:
        status_text = 'muted' if new_status else 'unmuted'
        flash(f'Thread {status_text} successfully!', 'success')
    else:
        flash('Error updating thread status', 'error')
    
    return redirect(url_for('message.list_threads'))

@message_bp.route('/threads/<int:thread_id>/statistics')
@login_required
def thread_statistics(thread_id):
    """View detailed statistics for a thread"""
    threading_engine = MessageThreadingEngine()
    
    try:
        # Get thread statistics
        thread_stats = threading_engine.get_thread_statistics(thread_id)
        
        # Get activity summary
        from app.utils.message_threading import get_thread_activity_summary
        activity_summary = get_thread_activity_summary(thread_id, 30)
        
        return render_template('message/thread_statistics.html',
                             thread_stats=thread_stats,
                             activity_summary=activity_summary)
    
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('message.list_threads'))

@message_bp.route('/threads/suggestions')
@login_required
def thread_participant_suggestions():
    """Get participant suggestions for thread creation"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    from app.utils.message_threading import suggest_thread_participants
    suggestions = suggest_thread_participants(current_user.id, query, limit)
    
    return jsonify({
        'suggestions': suggestions
    })

# Rich Text Formatting Routes
@message_bp.route('/compose', methods=['GET', 'POST'])
@login_required
def compose_message():
    """Enhanced message composition with rich text support"""
    form = MessageComposeForm()
    threading_engine = MessageThreadingEngine()
    template_manager = MessageTemplateManager()
    
    # Populate receiver choices
    users = User.query.filter(User.id != current_user.id, User.is_active == True).all()
    form.receiver_id.choices = [(user.id, user.username) for user in users]
    
    # Populate template choices
    templates = template_manager.get_user_templates(current_user.id)
    form.use_template.choices = [(0, 'No Template')] + [(t['id'], t['name']) for t in templates]
    
    if form.validate_on_submit():
        try:
            # Process rich text content
            html_content, plain_content = format_message_content(
                form.content.data,
                form.content_format.data,
                sanitize=True,
                enable_emoji=True,
                enable_markdown=True
            )
            
            # Create message
            message = Message(
                sender_id=current_user.id,
                receiver_id=form.receiver_id.data,
                content=plain_content,
                content_html=html_content,
                content_format=form.content_format.data,
                is_rich_text=form.content_format.data != 'text',
                priority=form.priority.data
            )
            
            # Handle threading
            if form.create_thread.data:
                thread = threading_engine.create_thread(
                    subject=form.thread_subject.data or message.content[:100],
                    participant_ids=[current_user.id, form.receiver_id.data],
                    creator_id=current_user.id,
                    priority=form.priority.data
                )
                message.thread_id = thread.id
            
            db.session.add(message)
            db.session.commit()
            
            flash('Message sent successfully!', 'success')
            return redirect(url_for('message.inbox'))
        
        except Exception as e:
            flash(f'Error sending message: {str(e)}', 'error')
    
    return render_template('message/compose.html', form=form, users=users, templates=templates)

@message_bp.route('/templates')
@login_required
def list_templates():
    """List message templates"""
    template_manager = MessageTemplateManager()
    
    category = request.args.get('category', '')
    include_public = request.args.get('public', 'true').lower() == 'true'
    
    templates = template_manager.get_user_templates(
        current_user.id,
        category=category if category else None,
        include_public=include_public
    )
    
    return render_template('message/templates.html', templates=templates)

@message_bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
def create_template():
    """Create a new message template"""
    form = MessageTemplateForm()
    
    if form.validate_on_submit():
        try:
            template_manager = MessageTemplateManager()
            
            # Extract variables from content
            from app.utils.rich_text import MessageTemplateManager
            variables = []
            if form.variables.data:
                variables = [var.strip() for var in form.variables.data.split(',')]
            
            template_data = template_manager.create_template(
                name=form.name.data,
                content=form.content.data,
                user_id=current_user.id,
                category=form.category.data,
                variables=variables,
                is_public=form.is_public.data
            )
            
            flash(f'Template "{template_data["name"]}" created successfully!', 'success')
            return redirect(url_for('message.list_templates'))
        
        except Exception as e:
            flash(f'Error creating template: {str(e)}', 'error')
    
    return render_template('message/create_template.html', form=form)

@message_bp.route('/templates/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    """Edit an existing template"""
    form = MessageTemplateForm()
    template_manager = MessageTemplateManager()
    
    template_data = template_manager.get_template(template_id, current_user.id)
    if not template_data:
        flash('Template not found', 'error')
        return redirect(url_for('message.list_templates'))
    
    # Check ownership
    if not template_data['is_owner']:
        flash('You can only edit your own templates', 'error')
        return redirect(url_for('message.list_templates'))
    
    if request.method == 'GET':
        # Populate form with template data
        form.name.data = template_data['name']
        form.content.data = template_data['content']
        form.category.data = template_data['category']
        form.variables.data = ', '.join(template_data['variables'])
        form.is_public.data = template_data['is_public']
    
    if form.validate_on_submit():
        try:
            # Extract variables
            variables = []
            if form.variables.data:
                variables = [var.strip() for var in form.variables.data.split(',')]
            
            success = template_manager.update_template(
                template_id=template_id,
                user_id=current_user.id,
                name=form.name.data,
                content=form.content.data,
                category=form.category.data,
                is_public=form.is_public.data
            )
            
            if success:
                flash('Template updated successfully!', 'success')
                return redirect(url_for('message.list_templates'))
            else:
                flash('Error updating template', 'error')
        
        except Exception as e:
            flash(f'Error updating template: {str(e)}', 'error')
    
    return render_template('message/edit_template.html', form=form, template=template_data)

@message_bp.route('/templates/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id):
    """Delete a template"""
    template_manager = MessageTemplateManager()
    
    template_data = template_manager.get_template(template_id, current_user.id)
    if not template_data:
        flash('Template not found', 'error')
        return redirect(url_for('message.list_templates'))
    
    # Check ownership
    if not template_data['is_owner']:
        flash('You can only delete your own templates', 'error')
        return redirect(url_for('message.list_templates'))
    
    success = template_manager.delete_template(template_id, current_user.id)
    
    if success:
        flash('Template deleted successfully!', 'success')
    else:
        flash('Error deleting template', 'error')
    
    return redirect(url_for('message.list_templates'))

@message_bp.route('/templates/<int:template_id>/preview')
@login_required
def preview_template(template_id):
    """Preview a template"""
    template_manager = MessageTemplateManager()
    
    template_data = template_manager.get_template(template_id, current_user.id)
    if not template_data:
        return jsonify({'error': 'Template not found'}), 404
    
    # Generate preview
    processor = RichTextProcessor()
    preview_text = processor.generate_preview(template_data['content'], 200)
    
    return jsonify({
        'name': template_data['name'],
        'preview': preview_text,
        'variables': template_data['variables']
    })

@message_bp.route('/templates/<int:template_id>/render', methods=['POST'])
@login_required
def render_template(template_id):
    """Render a template with variables"""
    template_manager = MessageTemplateManager()
    
    template_data = template_manager.get_template(template_id, current_user.id)
    if not template_data:
        return jsonify({'error': 'Template not found'}), 404
    
    # Get variables from request
    variables = request.get_json().get('variables', {})
    
    # Render template
    rendered_content = template_manager.render_template(template_id, current_user.id, variables)
    
    if rendered_content:
        # Format the rendered content
        html_content, plain_content = format_message_content(rendered_content)
        
        return jsonify({
            'html': html_content,
            'text': plain_content
        })
    else:
        return jsonify({'error': 'Failed to render template'}), 500

@message_bp.route('/rich-text/preview', methods=['POST'])
@login_required
def preview_rich_text():
    """Preview rich text content"""
    data = request.get_json()
    
    content = data.get('content', '')
    content_format = data.get('format', 'text')
    max_length = data.get('max_length', 200)
    
    # Generate preview
    processor = RichTextProcessor()
    preview_text = processor.generate_preview(content, max_length, content_format)
    
    return jsonify({
        'preview': preview_text
    })

@message_bp.route('/rich-text/validate', methods=['POST'])
@login_required
def validate_rich_text():
    """Validate rich text content"""
    data = request.get_json()
    
    content = data.get('content', '')
    content_format = data.get('format', 'text')
    
    # Validate content
    processor = RichTextProcessor()
    validation_result = processor.validate_formatting(content, content_format)
    
    return jsonify(validation_result)

@message_bp.route('/emoji/suggestions')
@login_required
def emoji_suggestions():
    """Get emoji suggestions"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))
    
    from app.utils.rich_text import get_emoji_suggestions
    suggestions = get_emoji_suggestions(query, limit)
    
    return jsonify({
        'suggestions': suggestions
    })

@message_bp.route('/rich-text/format', methods=['POST'])
@login_required
def format_rich_text():
    """Format rich text content"""
    data = request.get_json()
    
    content = data.get('content', '')
    content_format = data.get('format', 'text')
    sanitize = data.get('sanitize', True)
    enable_emoji = data.get('enable_emoji', True)
    enable_markdown = data.get('enable_markdown', True)
    
    # Format content
    html_content, plain_content = format_message_content(
        content, content_format, sanitize, enable_emoji, enable_markdown
    )
    
    return jsonify({
        'html': html_content,
        'text': plain_content
    })

# File Attachment Routes
@message_bp.route('/attachments/upload', methods=['POST'])
@login_required
def upload_attachment():
    """Upload file attachment to message"""
    form = MessageAttachmentForm()
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    message_id = request.form.get('message_id', type=int)
    
    if not message_id:
        return jsonify({'success': False, 'error': 'Message ID required'}), 400
    
    # Verify user has permission to attach to this message
    message = Message.query.get(message_id)
    if not message or (message.sender_id != current_user.id and message.receiver_id != current_user.id):
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    # Upload attachment
    success, result = upload_message_attachment(file, message_id, current_user.id)
    
    if success:
        # Update message has_attachments flag
        message.has_attachments = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'attachment': result['file_info']
        })
    else:
        return jsonify({
            'success': False,
            'errors': result['errors'],
            'warnings': result['warnings']
        }), 400

@message_bp.route('/attachments/<int:attachment_id>')
@login_required
def get_attachment(attachment_id):
    """Get attachment information"""
    manager = FileAttachmentManager()
    attachment = manager.get_attachment(attachment_id, current_user.id)
    
    if not attachment:
        return jsonify({'success': False, 'error': 'Attachment not found'}), 404
    
    return jsonify({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.original_filename,
            'file_size': attachment.get_file_size_display(),
            'file_type': attachment.file_type,
            'file_category': attachment.file_category,
            'download_count': attachment.download_count,
            'created_at': attachment.created_at.isoformat(),
            'is_image': attachment.is_image(),
            'is_document': attachment.is_document(),
            'is_video': attachment.is_video(),
            'is_audio': attachment.is_audio(),
            'can_preview': attachment.can_preview(),
            'thumbnail_url': attachment.get_thumbnail_url(),
            'preview_url': attachment.get_preview_url(),
            'download_url': attachment.get_download_url()
        }
    })

@message_bp.route('/attachments/<int:attachment_id>/download')
@login_required
def download_attachment(attachment_id):
    """Download attachment file"""
    manager = FileAttachmentManager()
    attachment = manager.get_attachment(attachment_id, current_user.id)
    
    if not attachment:
        return jsonify({'success': False, 'error': 'Attachment not found'}), 404
    
    # Increment download count
    attachment.download_count += 1
    db.session.commit()
    
    from flask import send_file
    return send_file(
        attachment.file_path,
        as_attachment=True,
        download_name=attachment.original_filename
    )

@message_bp.route('/attachments/<int:attachment_id>/preview')
@login_required
def preview_attachment(attachment_id):
    """Preview attachment file"""
    manager = FileAttachmentManager()
    attachment = manager.get_attachment(attachment_id, current_user.id)
    
    if not attachment:
        return jsonify({'success': False, 'error': 'Attachment not found'}), 404
    
    if not attachment.can_preview():
        return jsonify({'success': False, 'error': 'Preview not available for this file type'}), 400
    
    preview_path = attachment.preview_path
    if not preview_path or not os.path.exists(preview_path):
        return jsonify({'success': False, 'error': 'Preview file not found'}), 404
    
    from flask import send_file
    return send_file(preview_path)

@message_bp.route('/attachments/<int:attachment_id>/thumbnail')
@login_required
def get_attachment_thumbnail(attachment_id):
    """Get attachment thumbnail"""
    manager = FileAttachmentManager()
    attachment = manager.get_attachment(attachment_id, current_user.id)
    
    if not attachment:
        return jsonify({'success': False, 'error': 'Attachment not found'}), 404
    
    if not attachment.is_image():
        return jsonify({'success': False, 'error': 'Thumbnail not available for this file type'}), 400
    
    thumbnail_path = attachment.thumbnail_path
    if not thumbnail_path or not os.path.exists(thumbnail_path):
        return jsonify({'success': False, 'error': 'Thumbnail not found'}), 404
    
    from flask import send_file
    return send_file(thumbnail_path)

@message_bp.route('/attachments/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(attachment_id):
    """Delete attachment"""
    manager = FileAttachmentManager()
    success = manager.delete_attachment(attachment_id, current_user.id)
    
    if success:
        return jsonify({'success': True, 'message': 'Attachment deleted successfully'})
    else:
        return jsonify({'success': False, 'error': 'Failed to delete attachment'}), 400

@message_bp.route('/attachments')
@login_required
def list_attachments():
    """List user's attachments"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    manager = FileAttachmentManager()
    attachments_data = manager.get_user_attachments(current_user.id, page, per_page)
    
    return render_template('message/attachments.html', 
                         attachments=attachments_data['attachments'],
                         pagination={
                             'total': attachments_data['total'],
                             'page': attachments_data['page'],
                             'per_page': attachments_data['per_page'],
                             'total_pages': attachments_data['total_pages']
                         })

@message_bp.route('/attachments/analytics')
@login_required
def attachment_analytics():
    """Get attachment analytics"""
    days = request.args.get('days', 30, type=int)
    
    manager = FileAttachmentManager()
    analytics = manager.get_attachment_analytics(current_user.id, days)
    
    return jsonify({
        'success': True,
        'analytics': analytics
    })

@message_bp.route('/attachments/validate', methods=['POST'])
@login_required
def validate_attachment():
    """Validate file before upload"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    manager = FileAttachmentManager()
    
    is_valid, result = manager.validate_file(file)
    
    return jsonify({
        'success': is_valid,
        'errors': result['errors'],
        'warnings': result['warnings'],
        'file_info': result['file_info']
    })

# Message Forwarding Routes
@message_bp.route('/<int:message_id>/forward', methods=['GET', 'POST'])
@login_required
def forward_message(message_id):
    """Forward a message to another user"""
    message = Message.query.get_or_404(message_id)
    
    # Check permissions
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    form = MessageForwardForm()
    
    # Populate forward_to choices (exclude current user and message participants)
    users = User.query.filter(User.id != current_user.id).all()
    form.forward_to.choices = [(0, 'Select recipient')] + [(user.id, user.username) for user in users]
    
    if request.method == 'POST' and form.validate_on_submit():
        # Forward the message
        success, result = forward_message(
            original_message_id=message_id,
            forward_to=form.forward_to.data,
            forward_by_id=current_user.id,
            forward_note=form.forward_note.data
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Message forwarded successfully',
                'forwarded_message_id': result['forwarded_message_id']
            })
        else:
            return jsonify({
                'success': False,
                'errors': result['errors']
            }), 400
    
    return render_template('message/forward.html', message=message, form=form)

@message_bp.route('/<int:message_id>/quote', methods=['POST'])
@login_required
def quote_message(message_id):
    """Create a quote from a message"""
    message = Message.query.get_or_404(message_id)
    
    # Check permissions
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    data = request.get_json()
    quote_style = data.get('quote_style', 'standard')
    
    # Create quote
    quote_result = create_message_quote(message_id, current_user.id, quote_style)
    
    if quote_result['success']:
        return jsonify({
            'success': True,
            'quote': quote_result['quote'],
            'quote_style': quote_style
        })
    else:
        return jsonify({
            'success': False,
            'errors': quote_result['errors']
        }), 400

@message_bp.route('/<int:message_id>/export', methods=['POST'])
@login_required
def export_message(message_id):
    """Export a message in various formats"""
    message = Message.query.get_or_404(message_id)
    
    # Check permissions
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    data = request.get_json()
    export_format = data.get('export_format', 'json')
    
    # Export message
    export_result = export_message(message_id, current_user.id, export_format)
    
    if export_result['success']:
        return jsonify({
            'success': True,
            'export': export_result['export'],
            'format': export_format,
            'filename': export_result['filename']
        })
    else:
        return jsonify({
            'success': False,
            'errors': export_result['errors']
        }), 400

@message_bp.route('/<int:message_id>/forward-history')
@login_required
def get_forward_history(message_id):
    """Get forward history for a message"""
    message = Message.query.get_or_404(message_id)
    
    # Check permissions
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    manager = MessageForwardingManager()
    history = manager.get_forward_history(message_id, current_user.id)
    
    return jsonify({
        'success': True,
        'history': history
    })

@message_bp.route('/forwards')
@login_required
def list_sent_forwards():
    """List messages forwarded by current user"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    manager = MessageForwardingManager()
    forwards_data = manager.get_user_forwards(current_user.id, page, per_page)
    
    return render_template('message/forwards.html', 
                         forwards=forwards_data['forwards'],
                         pagination={
                             'total': forwards_data['total'],
                             'page': forwards_data['page'],
                             'per_page': forwards_data['per_page'],
                             'total_pages': forwards_data['total_pages']
                         })

@message_bp.route('/received-forwards')
@login_required
def list_received_forwards():
    """List messages forwarded to current user"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    manager = MessageForwardingManager()
    forwards_data = manager.get_user_received_forwards(current_user.id, page, per_page)
    
    return render_template('message/received_forwards.html', 
                         forwards=forwards_data['forwards'],
                         pagination={
                             'total': forwards_data['total'],
                             'page': forwards_data['page'],
                             'per_page': forwards_data['per_page'],
                             'total_pages': forwards_data['total_pages']
                         })

@message_bp.route('/forwarding-analytics')
@login_required
def forwarding_analytics():
    """Get forwarding analytics"""
    days = request.args.get('days', 30, type=int)
    
    manager = MessageForwardingManager()
    analytics = manager.get_forwarding_analytics(current_user.id, days)
    
    return jsonify({
        'success': True,
        'analytics': analytics
    })
