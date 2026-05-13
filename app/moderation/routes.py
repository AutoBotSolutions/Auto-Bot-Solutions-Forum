"""
Automated Content Moderation Routes

This module contains Flask routes and API endpoints for the content moderation system,
including moderation queue management, content analysis, spam detection, and quality assessment.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, asc, func
from app import db
from app.models import User, Post, Comment
from .models import (
    ModerationQueue, ContentAnalysis, ModerationAction, ModerationRule,
    SpamDetection, ContentQuality, ModerationPattern, ModerationHistory
)
from .forms import (
    ModerationQueueForm, ContentAnalysisForm, ModerationActionForm,
    ModerationRuleForm, SpamDetectionForm, ContentQualityForm,
    ModerationPatternForm, ModerationSettingsForm, BulkModerationForm,
    ModerationSearchForm, ContentReviewForm, ModerationReportForm
)
from .service import (
    ModerationService, ContentAnalysisService, SpamDetectionService,
    ContentQualityService, ModerationQueueService, ModerationRuleService,
    AutomatedModerationService
)

moderation_bp = Blueprint('moderation', __name__, url_prefix='/moderation')


def check_moderator_permission():
    """Check if user has moderator permission"""
    if not current_user.is_authenticated:
        return False
    return current_user.is_admin or current_user.is_moderator


def check_admin_permission():
    """Check if user has admin permission"""
    if not current_user.is_authenticated:
        return False
    return current_user.is_admin


@moderation_bp.route('/')
@login_required
def index():
    """Moderation dashboard"""
    
    if not check_moderator_permission():
        flash('You do not have permission to access the moderation dashboard.', 'error')
        return redirect(url_for('main.index'))
    
    # Get moderation statistics
    moderation_service = ModerationService()
    queue_stats = moderation_service.get_queue_stats()
    
    # Get recent queue items
    recent_items = moderation_service.get_queue_items(status='pending', limit=10)
    
    # Get recent actions
    recent_actions = ModerationAction.query.order_by(
        ModerationAction.created_at.desc()
    ).limit(10).all()
    
    # Get system stats
    total_analyses = ContentAnalysis.query.count()
    total_spam_detections = SpamDetection.query.count()
    total_quality_assessments = ContentQuality.query.count()
    
    return render_template('moderation/index.html',
                         queue_stats=queue_stats,
                         recent_items=recent_items,
                         recent_actions=recent_actions,
                         total_analyses=total_analyses,
                         total_spam_detections=total_spam_detections,
                         total_quality_assessments=total_quality_assessments)


@moderation_bp.route('/queue')
@login_required
def queue():
    """Moderation queue"""
    
    if not check_moderator_permission():
        flash('You do not have permission to access the moderation queue.', 'error')
        return redirect(url_for('main.index'))
    
    form = ModerationQueueForm()
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = ModerationQueue.query
    
    # Apply filters
    if form.status.data:
        query = query.filter(ModerationQueue.status == form.status.data)
    
    if form.priority.data:
        query = query.filter(ModerationQueue.priority == form.priority.data)
    
    if form.content_type.data:
        query = query.filter(ModerationQueue.content_type == form.content_type.data)
    
    if form.date_from.data:
        query = query.filter(ModerationQueue.created_at >= form.date_from.data)
    
    if form.date_to.data:
        query = query.filter(ModerationQueue.created_at <= form.date_to.data)
    
    if form.min_spam_score.data is not None:
        query = query.filter(ModerationQueue.spam_score >= form.min_spam_score.data)
    
    if form.max_spam_score.data is not None:
        query = query.filter(ModerationQueue.spam_score <= form.max_spam_score.data)
    
    if form.min_quality_score.data is not None:
        query = query.filter(ModerationQueue.quality_score >= form.min_quality_score.data)
    
    if form.max_quality_score.data is not None:
        query = query.filter(ModerationQueue.quality_score <= form.max_quality_score.data)
    
    if form.search.data:
        search_term = f"%{form.search.data}%"
        query = query.filter(
            or_(
                ModerationQueue.content_data['text'].astext.ilike(search_term),
                ModerationQueue.review_notes.ilike(search_term)
            )
        )
    
    # Order and paginate
    query = query.order_by(
        ModerationQueue.priority.desc(),
        ModerationQueue.created_at.asc()
    )
    
    limit = int(form.limit.data) if form.limit.data else 25
    items = query.paginate(page=page, per_page=limit, error_out=False)
    
    return render_template('moderation/queue.html', form=form, items=items)


@moderation_bp.route('/queue/<int:queue_id>')
@login_required
def queue_detail(queue_id):
    """Queue item detail"""
    
    if not check_moderator_permission():
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))
    
    queue_item = ModerationQueue.query.get_or_404(queue_id)
    
    # Get related analyses
    analysis = ContentAnalysis.query.filter_by(
        content_type=queue_item.content_type,
        content_id=queue_item.content_id
    ).first()
    
    spam_detection = SpamDetection.query.filter_by(
        content_type=queue_item.content_type,
        content_id=queue_item.content_id
    ).first()
    
    quality_assessment = ContentQuality.query.filter_by(
        content_type=queue_item.content_type,
        content_id=queue_item.content_id
    ).first()
    
    # Get related actions
    actions = ModerationAction.query.filter_by(
        target_type=queue_item.content_type,
        target_id=queue_item.content_id
    ).order_by(ModerationAction.created_at.desc()).all()
    
    # Get history
    history = ModerationHistory.query.filter_by(
        target_type=queue_item.content_type,
        target_id=queue_item.content_id
    ).order_by(ModerationHistory.created_at.desc()).limit(20).all()
    
    return render_template('moderation/queue_detail.html',
                         queue_item=queue_item,
                         analysis=analysis,
                         spam_detection=spam_detection,
                         quality_assessment=quality_assessment,
                         actions=actions,
                         history=history)


@moderation_bp.route('/queue/<int:queue_id>/review', methods=['GET', 'POST'])
@login_required
def review_queue_item(queue_id):
    """Review queue item"""
    
    if not check_moderator_permission():
        flash('You do not have permission to review this item.', 'error')
        return redirect(url_for('main.index'))
    
    queue_item = ModerationQueue.query.get_or_404(queue_id)
    
    if queue_item.status != 'pending':
        flash('This item has already been reviewed.', 'warning')
        return redirect(url_for('moderation.queue_detail', queue_id=queue_id))
    
    form = ContentReviewForm()
    form.queue_id.data = queue_id
    
    if form.validate_on_submit():
        # Update queue item
        moderation_service = ModerationService()
        moderation_service.update_queue_status(
            queue_id=queue_id,
            status=form.review_decision.data,
            reviewer_id=current_user.id,
            notes=form.review_notes.data
        )
        
        # Create moderation action
        action = ModerationAction(
            action_type=form.review_decision.data,
            action_reason=form.action_reason.data,
            action_description=form.review_notes.data,
            target_type=queue_item.content_type,
            target_id=queue_item.content_id,
            actor_type='moderator',
            actor_id=current_user.id,
            severity='medium',  # Could be based on form
            confidence=form.confidence.data,
            automated=False,
            appealable=form.allow_appeal.data,
            appeal_deadline=datetime.utcnow() + timedelta(days=form.appeal_deadline_days.data) if form.allow_appeal.data else None
        )
        
        db.session.add(action)
        db.session.commit()
        
        # Handle edit action
        if form.review_decision.data == 'edit' and form.edited_content.data:
            # Update the actual content (implementation depends on content type)
            pass
        
        flash('Review submitted successfully.', 'success')
        return redirect(url_for('moderation.queue_detail', queue_id=queue_id))
    
    return render_template('moderation/review.html', form=form, queue_item=queue_item)


@moderation_bp.route('/queue/<int:queue_id>/approve', methods=['POST'])
@login_required
def approve_queue_item(queue_id):
    """Approve queue item"""
    
    if not check_moderator_permission():
        return jsonify({'error': 'Permission denied'}), 403
    
    queue_item = ModerationQueue.query.get_or_404(queue_id)
    
    if queue_item.status != 'pending':
        return jsonify({'error': 'Item already reviewed'}), 400
    
    moderation_service = ModerationService()
    moderation_service.update_queue_status(
        queue_id=queue_id,
        status='approved',
        reviewer_id=current_user.id,
        notes='Approved by moderator'
    )
    
    return jsonify({'success': True, 'status': 'approved'})


@moderation_bp.route('/queue/<int:queue_id>/reject', methods=['POST'])
@login_required
def reject_queue_item(queue_id):
    """Reject queue item"""
    
    if not check_moderator_permission():
        return jsonify({'error': 'Permission denied'}), 403
    
    queue_item = ModerationQueue.query.get_or_404(queue_id)
    
    if queue_item.status != 'pending':
        return jsonify({'error': 'Item already reviewed'}), 400
    
    moderation_service = ModerationService()
    moderation_service.update_queue_status(
        queue_id=queue_id,
        status='rejected',
        reviewer_id=current_user.id,
        notes='Rejected by moderator'
    )
    
    return jsonify({'success': True, 'status': 'rejected'})


@moderation_bp.route('/queue/bulk-action', methods=['POST'])
@login_required
def bulk_queue_action():
    """Bulk action on queue items"""
    
    if not check_moderator_permission():
        return jsonify({'error': 'Permission denied'}), 403
    
    form = BulkModerationForm()
    
    if not form.validate_on_submit():
        return jsonify({'error': 'Invalid form data'}), 400
    
    try:
        selected_items = [int(item_id) for item_id in form.selected_items.data.split(',')]
        
        actions_taken = []
        for item_id in selected_items:
            queue_item = ModerationQueue.query.get(item_id)
            if queue_item and queue_item.status == 'pending':
                # Update queue item
                moderation_service = ModerationService()
                moderation_service.update_queue_status(
                    queue_id=item_id,
                    status=form.action_type.data,
                    reviewer_id=current_user.id,
                    notes=form.action_description.data
                )
                
                # Create moderation action
                action = ModerationAction(
                    action_type=form.action_type.data,
                    action_reason=form.action_reason.data,
                    action_description=form.action_description.data,
                    target_type=queue_item.content_type,
                    target_id=queue_item.content_id,
                    actor_type='moderator',
                    actor_id=current_user.id,
                    severity=form.severity.data,
                    confidence=form.confidence.data,
                    automated=False
                )
                
                db.session.add(action)
                actions_taken.append(item_id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'actions_taken': len(actions_taken),
            'message': f'Bulk action applied to {len(actions_taken)} items'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@moderation_bp.route('/analysis')
@login_required
def analysis():
    """Content analysis"""
    
    if not check_moderator_permission():
        flash('You do not have permission to access content analysis.', 'error')
        return redirect(url_for('main.index'))
    
    form = ContentAnalysisForm()
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = ContentAnalysis.query
    
    # Apply filters
    if form.content_type.data:
        query = query.filter(ContentAnalysis.content_type == form.content_type.data)
    
    if form.language.data:
        query = query.filter(ContentAnalysis.language_detected == form.language.data)
    
    if form.sentiment.data:
        query = query.filter(ContentAnalysis.sentiment_label == form.sentiment.data)
    
    if form.min_grammar_score.data is not None:
        query = query.filter(ContentAnalysis.grammar_score >= form.min_grammar_score.data)
    
    if form.min_spelling_score.data is not None:
        query = query.filter(ContentAnalysis.spelling_score >= form.min_spelling_score.data)
    
    if form.min_coherence_score.data is not None:
        query = query.filter(ContentAnalysis.coherence_score >= form.min_coherence_score.data)
    
    if form.min_word_count.data:
        query = query.filter(ContentAnalysis.word_count >= form.min_word_count.data)
    
    if form.max_word_count.data:
        query = query.filter(ContentAnalysis.word_count <= form.max_word_count.data)
    
    if form.min_readability.data is not None:
        query = query.filter(ContentAnalysis.readability_score >= form.min_readability.data)
    
    if form.max_readability.data is not None:
        query = query.filter(ContentAnalysis.readability_score <= form.max_readability.data)
    
    if form.date_from.data:
        query = query.filter(ContentAnalysis.created_at >= form.date_from.data)
    
    if form.date_to.data:
        query = query.filter(ContentAnalysis.created_at <= form.date_to.data)
    
    if form.search.data:
        search_term = f"%{form.search.data}%"
        query = query.filter(
            or_(
                ContentAnalysis.primary_topic.ilike(search_term),
                ContentAnalysis.topics.astext.ilike(search_term)
            )
        )
    
    # Order and paginate
    query = query.order_by(ContentAnalysis.created_at.desc())
    
    limit = int(form.limit.data) if form.limit.data else 25
    items = query.paginate(page=page, per_page=limit, error_out=False)
    
    return render_template('moderation/analysis.html', form=form, items=items)


@moderation_bp.route('/spam')
@login_required
def spam():
    """Spam detection"""
    
    if not check_moderator_permission():
        flash('You do not have permission to access spam detection.', 'error')
        return redirect(url_for('main.index'))
    
    form = SpamDetectionForm()
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = SpamDetection.query
    
    # Apply filters
    if form.is_spam.data is not None:
        query = query.filter(SpamDetection.is_spam == form.is_spam.data)
    
    if form.spam_type.data:
        query = query.filter(SpamDetection.spam_type == form.spam_type.data)
    
    if form.min_overall_score.data is not None:
        query = query.filter(SpamDetection.overall_score >= form.min_overall_score.data)
    
    if form.max_overall_score.data is not None:
        query = query.filter(SpamDetection.overall_score <= form.max_overall_score.data)
    
    if form.min_confidence.data is not None:
        query = query.filter(SpamDetection.confidence >= form.min_confidence.data)
    
    if form.content_type.data:
        query = query.filter(SpamDetection.content_type == form.content_type.data)
    
    if form.date_from.data:
        query = query.filter(SpamDetection.created_at >= form.date_from.data)
    
    if form.date_to.data:
        query = query.filter(SpamDetection.created_at <= form.date_to.data)
    
    if form.search.data:
        search_term = f"%{form.search.data}%"
        query = query.filter(
            or_(
                SpamDetection.detected_keywords.astext.ilike(search_term),
                SpamDetection.detected_patterns.astext.ilike(search_term)
            )
        )
    
    # Order and paginate
    query = query.order_by(SpamDetection.created_at.desc())
    
    limit = int(form.limit.data) if form.limit.data else 25
    items = query.paginate(page=page, per_page=limit, error_out=False)
    
    return render_template('moderation/spam.html', form=form, items=items)


@moderation_bp.route('/quality')
@login_required
def quality():
    """Content quality"""
    
    if not check_moderator_permission():
        flash('You do not have permission to access content quality.', 'error')
        return redirect(url_for('main.index'))
    
    form = ContentQualityForm()
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = ContentQuality.query
    
    # Apply filters
    if form.quality_grade.data:
        query = query.filter(ContentQuality.quality_grade == form.quality_grade.data)
    
    if form.min_overall_score.data is not None:
        query = query.filter(ContentQuality.overall_score >= form.min_overall_score.data)
    
    if form.max_overall_score.data is not None:
        query = query.filter(ContentQuality.overall_score <= form.max_overall_score.data)
    
    if form.min_content_quality.data is not None:
        query = query.filter(ContentQuality.content_quality >= form.min_content_quality.data)
    
    if form.min_presentation_quality.data is not None:
        query = query.filter(ContentQuality.presentation_quality >= form.min_presentation_quality.data)
    
    if form.min_originality_score.data is not None:
        query = query.filter(ContentQuality.originality_score >= form.min_originality_score.data)
    
    if form.min_grammar_score.data is not None:
        query = query.filter(ContentQuality.grammar_score >= form.min_grammar_score.data)
    
    if form.min_spelling_score.data is not None:
        query = query.filter(ContentQuality.spelling_score >= form.min_spelling_score.data)
    
    if form.min_structure_score.data is not None:
        query = query.filter(ContentQuality.structure_score >= form.min_structure_score.data)
    
    if form.min_coherence_score.data is not None:
        query = query.filter(ContentQuality.coherence_score >= form.min_coherence_score.data)
    
    if form.content_type.data:
        query = query.filter(ContentQuality.content_type == form.content_type.data)
    
    if form.min_word_count.data:
        query = query.filter(ContentQuality.word_count >= form.min_word_count.data)
    
    if form.max_word_count.data:
        query = query.filter(ContentQuality.word_count <= form.max_word_count.data)
    
    if form.date_from.data:
        query = query.filter(ContentQuality.created_at >= form.date_from.data)
    
    if form.date_to.data:
        query = query.filter(ContentQuality.created_at <= form.date_to.data)
    
    if form.search.data:
        search_term = f"%{form.search.data}%"
        query = query.filter(
            ContentQuality.improvement_suggestions.astext.ilike(search_term)
        )
    
    # Order and paginate
    query = query.order_by(ContentQuality.created_at.desc())
    
    limit = int(form.limit.data) if form.limit.data else 25
    items = query.paginate(page=page, per_page=limit, error_out=False)
    
    return render_template('moderation/quality.html', form=form, items=items)


@moderation_bp.route('/rules')
@login_required
def rules():
    """Moderation rules"""
    
    if not check_admin_permission():
        flash('You do not have permission to access moderation rules.', 'error')
        return redirect(url_for('main.index'))
    
    rules = ModerationRule.query.order_by(
        ModerationRule.priority.desc(),
        ModerationRule.name.asc()
    ).all()
    
    return render_template('moderation/rules.html', rules=rules)


@moderation_bp.route('/rules/create', methods=['GET', 'POST'])
@login_required
def create_rule():
    """Create moderation rule"""
    
    if not check_admin_permission():
        flash('You do not have permission to create moderation rules.', 'error')
        return redirect(url_for('main.index'))
    
    form = ModerationRuleForm()
    
    if form.validate_on_submit():
        rule_service = ModerationRuleService()
        rule = rule_service.create_rule(
            name=form.name.data,
            description=form.description.data,
            rule_type=form.rule_type.data,
            conditions=json.loads(form.conditions.data) if form.conditions.data else {},
            action_type=form.action_type.data,
            action_parameters=json.loads(form.action_parameters.data) if form.action_parameters.data else {},
            priority=form.priority.data,
            confidence_threshold=form.confidence_threshold.data,
            auto_apply=form.auto_apply.data,
            created_by=current_user.id
        )
        
        flash(f'Rule "{rule.name}" created successfully.', 'success')
        return redirect(url_for('moderation.rules'))
    
    return render_template('moderation/create_rule.html', form=form)


@moderation_bp.route('/rules/<int:rule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rule(rule_id):
    """Edit moderation rule"""
    
    if not check_admin_permission():
        flash('You do not have permission to edit moderation rules.', 'error')
        return redirect(url_for('main.index'))
    
    rule = ModerationRule.query.get_or_404(rule_id)
    form = ModerationRuleForm(obj=rule)
    form.rule_id = rule_id
    
    if form.validate_on_submit():
        rule.name = form.name.data
        rule.description = form.description.data
        rule.rule_type = form.rule_type.data
        rule.content_types = form.content_types.data
        rule.conditions = json.loads(form.conditions.data) if form.conditions.data else {}
        rule.patterns = json.loads(form.patterns.data) if form.patterns.data else {}
        rule.action_type = form.action_type.data
        rule.action_parameters = json.loads(form.action_parameters.data) if form.action_parameters.data else {}
        rule.priority = form.priority.data
        rule.confidence_threshold = form.confidence_threshold.data
        rule.auto_apply = form.auto_apply.data
        rule.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Rule "{rule.name}" updated successfully.', 'success')
        return redirect(url_for('moderation.rules'))
    
    # Populate form fields from rule object
    form.conditions.data = json.dumps(rule.conditions) if rule.conditions else ''
    form.patterns.data = json.dumps(rule.patterns) if rule.patterns else ''
    form.action_parameters.data = json.dumps(rule.action_parameters) if rule.action_parameters else ''
    
    return render_template('moderation/edit_rule.html', form=form, rule=rule)


@moderation_bp.route('/rules/<int:rule_id>/toggle', methods=['POST'])
@login_required
def toggle_rule(rule_id):
    """Toggle rule active status"""
    
    if not check_admin_permission():
        return jsonify({'error': 'Permission denied'}), 403
    
    rule = ModerationRule.query.get_or_404(rule_id)
    rule.is_active = not rule.is_active
    rule.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'active': rule.is_active,
        'message': f'Rule "{rule.name}" {"activated" if rule.is_active else "deactivated"}'
    })


@moderation_bp.route('/patterns')
@login_required
def patterns():
    """Moderation patterns"""
    
    if not check_admin_permission():
        flash('You do not have permission to access moderation patterns.', 'error')
        return redirect(url_for('main.index'))
    
    patterns = ModerationPattern.query.order_by(
        ModerationPattern.category.asc(),
        ModerationPattern.name.asc()
    ).all()
    
    return render_template('moderation/patterns.html', patterns=patterns)


@moderation_bp.route('/patterns/create', methods=['GET', 'POST'])
@login_required
def create_pattern():
    """Create moderation pattern"""
    
    if not check_admin_permission():
        flash('You do not have permission to create moderation patterns.', 'error')
        return redirect(url_for('main.index'))
    
    form = ModerationPatternForm()
    
    if form.validate_on_submit():
        pattern = ModerationPattern(
            name=form.name.data,
            description=form.description.data,
            pattern_type=form.pattern_type.data,
            pattern_data=json.loads(form.pattern_data.data) if form.pattern_data.data else {},
            match_type=form.match_type.data,
            case_sensitive=form.case_sensitive.data,
            weight=form.weight.data,
            category=form.category.data,
            severity=form.severity.data,
            created_by=current_user.id
        )
        
        db.session.add(pattern)
        db.session.commit()
        
        flash(f'Pattern "{pattern.name}" created successfully.', 'success')
        return redirect(url_for('moderation.patterns'))
    
    return render_template('moderation/create_pattern.html', form=form)


@moderation_bp.route('/actions')
@login_required
def actions():
    """Moderation actions"""
    
    if not check_moderator_permission():
        flash('You do not have permission to access moderation actions.', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = ModerationAction.query
    
    # Apply filters
    action_type = request.args.get('action_type')
    if action_type:
        query = query.filter(ModerationAction.action_type == action_type)
    
    actor_type = request.args.get('actor_type')
    if actor_type:
        query = query.filter(ModerationAction.actor_type == actor_type)
    
    automated = request.args.get('automated')
    if automated is not None:
        is_automated = automated.lower() == 'true'
        query = query.filter(ModerationAction.automated == is_automated)
    
    # Order and paginate
    query = query.order_by(ModerationAction.created_at.desc())
    
    items = query.paginate(page=page, per_page=25, error_out=False)
    
    return render_template('moderation/actions.html', items=items)


@moderation_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Moderation settings"""
    
    if not check_admin_permission():
        flash('You do not have permission to access moderation settings.', 'error')
        return redirect(url_for('main.index'))
    
    form = ModerationSettingsForm()
    
    if form.validate_on_submit():
        # Save settings to configuration
        settings = {
            'enable_automated_moderation': form.enable_automated_moderation.data,
            'enable_spam_detection': form.enable_spam_detection.data,
            'enable_quality_assessment': form.enable_quality_assessment.data,
            'spam_threshold': form.spam_threshold.data,
            'quality_threshold': form.quality_threshold.data,
            'auto_action_threshold': form.auto_action_threshold.data,
            'max_queue_age': form.max_queue_age.data,
            'auto_process_interval': form.auto_process_interval.data,
            'notify_moderators': form.notify_moderators.data,
            'notify_admins': form.notify_admins.data,
            'enable_email_notifications': form.enable_email_notifications.data,
            'moderation_email': form.moderation_email.data,
            'max_concurrent_analyses': form.max_concurrent_analyses.data,
            'analysis_timeout': form.analysis_timeout.data,
            'enable_caching': form.enable_caching.data,
            'cache_ttl': form.cache_ttl.data
        }
        
        # Save to configuration (implementation depends on your config system)
        current_app.config.update(settings)
        
        flash('Moderation settings saved successfully.', 'success')
        return redirect(url_for('moderation.settings'))
    
    # Load current settings
    form.enable_automated_moderation.data = current_app.config.get('MODERATION_ENABLE_AUTOMATED', True)
    form.enable_spam_detection.data = current_app.config.get('MODERATION_ENABLE_SPAM_DETECTION', True)
    form.enable_quality_assessment.data = current_app.config.get('MODERATION_ENABLE_QUALITY_ASSESSMENT', True)
    form.spam_threshold.data = current_app.config.get('MODERATION_SPAM_THRESHOLD', 0.7)
    form.quality_threshold.data = current_app.config.get('MODERATION_QUALITY_THRESHOLD', 0.3)
    form.auto_action_threshold.data = current_app.config.get('MODERATION_AUTO_ACTION_THRESHOLD', 0.8)
    form.max_queue_age.data = current_app.config.get('MODERATION_MAX_QUEUE_AGE', 24)
    form.auto_process_interval.data = current_app.config.get('MODERATION_AUTO_PROCESS_INTERVAL', 5)
    form.notify_moderators.data = current_app.config.get('MODERATION_NOTIFY_MODERATORS', True)
    form.notify_admins.data = current_app.config.get('MODERATION_NOTIFY_ADMINS', True)
    form.enable_email_notifications.data = current_app.config.get('MODERATION_ENABLE_EMAIL_NOTIFICATIONS', True)
    form.moderation_email.data = current_app.config.get('MODERATION_EMAIL', '')
    form.max_concurrent_analyses.data = current_app.config.get('MODERATION_MAX_CONCURRENT_ANALYSES', 10)
    form.analysis_timeout.data = current_app.config.get('MODERATION_ANALYSIS_TIMEOUT', 30)
    form.enable_caching.data = current_app.config.get('MODERATION_ENABLE_CACHING', True)
    form.cache_ttl.data = current_app.config.get('MODERATION_CACHE_TTL', 60)
    
    return render_template('moderation/settings.html', form=form)


@moderation_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """Advanced search"""
    
    if not check_moderator_permission():
        flash('You do not have permission to access moderation search.', 'error')
        return redirect(url_for('main.index'))
    
    form = ModerationSearchForm()
    results = []
    
    if form.validate_on_submit():
        # Build search query
        query = None
        search_term = f"%{form.query.data}%"
        
        # Search in different tables based on search type
        if form.search_type.data in ['content', 'all']:
            if query is None:
                query = ModerationQueue.query
            else:
                query = query.union(ModerationQueue.query)
            
            query = query.filter(
                or_(
                    ModerationQueue.content_data['text'].astext.ilike(search_term),
                    ModerationQueue.review_notes.ilike(search_term)
                )
            )
        
        if form.search_type.data in ['user', 'all']:
            # Search by user-related content
            pass  # Implementation depends on your user model structure
        
        # Apply filters
        if form.content_types.data:
            query = query.filter(ModerationQueue.content_type.in_(form.content_types.data))
        
        if form.status.data:
            query = query.filter(ModerationQueue.status.in_(form.status.data))
        
        if form.priority.data:
            query = query.filter(ModerationQueue.priority.in_(form.priority.data))
        
        # Apply date range
        if form.date_range.data == 'today':
            query = query.filter(ModerationQueue.created_at >= datetime.utcnow().date())
        elif form.date_range.data == 'week':
            query = query.filter(ModerationQueue.created_at >= datetime.utcnow() - timedelta(days=7))
        elif form.date_range.data == 'month':
            query = query.filter(ModerationQueue.created_at >= datetime.utcnow() - timedelta(days=30))
        elif form.date_range.data == 'year':
            query = query.filter(ModerationQueue.created_at >= datetime.utcnow() - timedelta(days=365))
        elif form.date_range.data == 'custom':
            if form.date_from.data:
                query = query.filter(ModerationQueue.created_at >= form.date_from.data)
            if form.date_to.data:
                query = query.filter(ModerationQueue.created_at <= form.date_to.data)
        
        # Apply score filters
        if form.min_spam_score.data is not None:
            query = query.filter(ModerationQueue.spam_score >= form.min_spam_score.data)
        
        if form.max_spam_score.data is not None:
            query = query.filter(ModerationQueue.spam_score <= form.max_spam_score.data)
        
        if form.min_quality_score.data is not None:
            query = query.filter(ModerationQueue.quality_score >= form.min_quality_score.data)
        
        if form.max_quality_score.data is not None:
            query = query.filter(ModerationQueue.quality_score <= form.max_quality_score.data)
        
        # Order results
        if form.sort_by.data == 'relevance':
            # Simple relevance based on search term match
            pass  # Implementation would require full-text search
        elif form.sort_by.data == 'date':
            if form.sort_order.data == 'desc':
                query = query.order_by(ModerationQueue.created_at.desc())
            else:
                query = query.order_by(ModerationQueue.created_at.asc())
        elif form.sort_by.data == 'spam_score':
            if form.sort_order.data == 'desc':
                query = query.order_by(ModerationQueue.spam_score.desc())
            else:
                query = query.order_by(ModerationQueue.spam_score.asc())
        elif form.sort_by.data == 'quality_score':
            if form.sort_order.data == 'desc':
                query = query.order_by(ModerationQueue.quality_score.desc())
            else:
                query = query.order_by(ModerationQueue.quality_score.asc())
        elif form.sort_by.data == 'priority':
            if form.sort_order.data == 'desc':
                query = query.order_by(ModerationQueue.priority.desc())
            else:
                query = query.order_by(ModerationQueue.priority.asc())
        
        # Limit results
        limit = int(form.limit.data) if form.limit.data else 25
        results = query.limit(limit).all()
    
    return render_template('moderation/search.html', form=form, results=results)


@moderation_bp.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    """Moderation reports"""
    
    if not check_admin_permission():
        flash('You do not have permission to access moderation reports.', 'error')
        return redirect(url_for('main.index'))
    
    form = ModerationReportForm()
    
    if form.validate_on_submit():
        # Generate report based on type and date range
        date_from = form.date_from.data
        date_to = form.date_to.data
        
        if form.report_type.data == 'daily':
            date_from = datetime.utcnow().date()
            date_to = datetime.utcnow().date() + timedelta(days=1)
        elif form.report_type.data == 'weekly':
            date_from = datetime.utcnow().date() - timedelta(days=7)
            date_to = datetime.utcnow().date() + timedelta(days=1)
        elif form.report_type.data == 'monthly':
            date_from = datetime.utcnow().date() - timedelta(days=30)
            date_to = datetime.utcnow().date() + timedelta(days=1)
        
        # Generate report data
        report_data = {
            'period': f"{date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}",
            'generated_at': datetime.utcnow().isoformat(),
            'generated_by': current_user.username
        }
        
        if form.include_queue_stats.data:
            report_data['queue_stats'] = {
                'total_pending': ModerationQueue.query.filter(
                    ModerationQueue.created_at.between(date_from, date_to),
                    ModerationQueue.status == 'pending'
                ).count(),
                'total_approved': ModerationQueue.query.filter(
                    ModerationQueue.created_at.between(date_from, date_to),
                    ModerationQueue.status == 'approved'
                ).count(),
                'total_rejected': ModerationQueue.query.filter(
                    ModerationQueue.created_at.between(date_from, date_to),
                    ModerationQueue.status == 'rejected'
                ).count()
            }
        
        if form.include_action_stats.data:
            report_data['action_stats'] = {
                'total_actions': ModerationAction.query.filter(
                    ModerationAction.created_at.between(date_from, date_to)
                ).count(),
                'automated_actions': ModerationAction.query.filter(
                    ModerationAction.created_at.between(date_from, date_to),
                    ModerationAction.automated == True
                ).count(),
                'manual_actions': ModerationAction.query.filter(
                    ModerationAction.created_at.between(date_from, date_to),
                    ModerationAction.automated == False
                ).count()
            }
        
        if form.include_performance_stats.data:
            report_data['performance_stats'] = {
                'total_analyses': ContentAnalysis.query.filter(
                    ContentAnalysis.created_at.between(date_from, date_to)
                ).count(),
                'total_spam_detections': SpamDetection.query.filter(
                    SpamDetection.created_at.between(date_from, date_to)
                ).count(),
                'total_quality_assessments': ContentQuality.query.filter(
                    ContentQuality.created_at.between(date_from, date_to)
                ).count()
            }
        
        if form.include_quality_trends.data:
            # Quality trends data
            quality_data = db.session.query(
                func.date(ContentQuality.created_at).label('date'),
                func.avg(ContentQuality.overall_score).label('avg_score')
            ).filter(
                ContentQuality.created_at.between(date_from, date_to)
            ).group_by(func.date(ContentQuality.created_at)).all()
            
            report_data['quality_trends'] = [
                {'date': str(item.date), 'avg_score': float(item.avg_score)}
                for item in quality_data
            ]
        
        if form.include_spam_trends.data:
            # Spam trends data
            spam_data = db.session.query(
                func.date(SpamDetection.created_at).label('date'),
                func.count(SpamDetection.id).label('total_spam'),
                func.sum(SpamDetection.is_spam.cast(db.Integer)).label('confirmed_spam')
            ).filter(
                SpamDetection.created_at.between(date_from, date_to)
            ).group_by(func.date(SpamDetection.created_at)).all()
            
            report_data['spam_trends'] = [
                {
                    'date': str(item.date),
                    'total_spam': int(item.total_spam),
                    'confirmed_spam': int(item.confirmed_spam or 0)
                }
                for item in spam_data
            ]
        
        # Handle export format
        if form.export_format.data == 'json':
            return jsonify(report_data)
        elif form.export_format.data == 'csv':
            # Generate CSV (implementation depends on your needs)
            pass
        elif form.export_format.data == 'pdf':
            # Generate PDF (implementation depends on your needs)
            pass
        else:  # HTML
            return render_template('moderation/report.html', report_data=report_data)
    
    return render_template('moderation/reports.html', form=form)


# API Endpoints

@moderation_bp.route('/api/queue-stats')
@login_required
def api_queue_stats():
    """API endpoint for queue statistics"""
    
    if not check_moderator_permission():
        return jsonify({'error': 'Permission denied'}), 403
    
    moderation_service = ModerationService()
    stats = moderation_service.get_queue_stats()
    
    return jsonify(stats)


@moderation_bp.route('/api/auto-process', methods=['POST'])
@login_required
def api_auto_process():
    """API endpoint for auto-processing queue"""
    
    if not check_admin_permission():
        return jsonify({'error': 'Permission denied'}), 403
    
    queue_service = ModerationQueueService()
    processed_count = queue_service.auto_process_queue()
    
    return jsonify({
        'success': True,
        'processed_count': processed_count,
        'message': f'Auto-processed {processed_count} queue items'
    })


@moderation_bp.route('/api/analyze-content', methods=['POST'])
@login_required
def api_analyze_content():
    """API endpoint for content analysis"""
    
    if not check_moderator_permission():
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    content_type = data.get('content_type')
    content_id = data.get('content_id')
    content_text = data.get('content_text')
    user_id = data.get('user_id')
    metadata = data.get('metadata', {})
    
    if not all([content_type, content_id, content_text]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        automated_service = AutomatedModerationService()
        result = automated_service.moderate_content(
            content_type=content_type,
            content_id=content_id,
            content_text=content_text,
            user_id=user_id,
            metadata=metadata
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@moderation_bp.route('/api/bulk-analyze', methods=['POST'])
@login_required
def api_bulk_analyze():
    """API endpoint for bulk content analysis"""
    
    if not check_admin_permission():
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    content_items = data.get('items', [])
    
    if not content_items:
        return jsonify({'error': 'No items provided'}), 400
    
    results = []
    errors = []
    
    for item in content_items:
        try:
            automated_service = AutomatedModerationService()
            result = automated_service.moderate_content(
                content_type=item.get('content_type'),
                content_id=item.get('content_id'),
                content_text=item.get('content_text'),
                user_id=item.get('user_id'),
                metadata=item.get('metadata', {})
            )
            results.append(result)
        except Exception as e:
            errors.append({
                'item_id': item.get('content_id'),
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'results': results,
        'errors': errors,
        'processed_count': len(results),
        'error_count': len(errors)
    })


@moderation_bp.route('/api/rules/apply', methods=['POST'])
@login_required
def api_apply_rules():
    """API endpoint for applying moderation rules"""
    
    if not check_admin_permission():
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    content_type = data.get('content_type')
    content_id = data.get('content_id')
    content_data = data.get('content_data')
    
    if not all([content_type, content_id, content_data]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        rule_service = ModerationRuleService()
        actions = rule_service.apply_rules(content_type, content_id, content_data)
        
        return jsonify({
            'success': True,
            'actions_taken': len(actions),
            'actions': [action.to_dict() for action in actions]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
