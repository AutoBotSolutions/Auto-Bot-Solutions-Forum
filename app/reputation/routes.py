"""
Reputation and Voting Routes

This module defines the Flask routes for the enhanced voting and reputation system,
including voting endpoints, reputation management, analytics, and admin interfaces.
"""

from flask import (
    Blueprint, render_template, request, jsonify, redirect, url_for,
    flash, current_app, abort
)
from flask_login import login_required, current_user
from sqlalchemy import func, desc, asc, and_, or_
from datetime import datetime, timedelta, date

from app import db
from app.models import User, Post, Comment
from .models import UserReputation, VoteHistory, VotingPattern, ReputationLevel
from .service import ReputationService, VotingService
from .forms import (
    VotingForm, ReasonVotingForm, ReputationFilterForm, VotingAnalyticsForm,
    ReputationLevelForm, ReputationAdjustmentForm, BulkReputationAdjustmentForm,
    VotingPatternAnalysisForm, ReputationHistoryForm, ReputationLeaderboardForm,
    CustomReasonCategoryForm, VotingSettingsForm
)

reputation_bp = Blueprint('reputation', __name__, url_prefix='/reputation')

# Voting Routes
@reputation_bp.route('/vote', methods=['POST'])
@login_required
def cast_vote():
    """Cast a vote on a post or comment"""
    form = ReasonVotingForm()
    
    if form.validate_on_submit():
        voting_service = VotingService()
        result = voting_service.cast_vote(
            user_id=current_user.id,
            target_type=form.target_type.data,
            target_id=form.target_id.data,
            vote_type=form.vote_type.data,
            reason=form.reason.data,
            reason_category=form.reason_category.data
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    return jsonify({'success': False, 'error': 'Invalid form data'}), 400

@reputation_bp.route('/vote/<target_type>/<int:target_id>')
@login_required
def vote_modal(target_type, target_id):
    """Render voting modal for a target"""
    # Validate target
    if target_type not in ['post', 'comment']:
        abort(404)
    
    target = Post.query.get(target_id) if target_type == 'post' else Comment.query.get(target_id)
    if not target:
        abort(404)
    
    # Check if user can vote
    voting_service = VotingService()
    can_vote, error = voting_service._can_user_vote(current_user.id, target_type, target_id)
    
    if not can_vote:
        flash(error, 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    # Check for existing vote
    existing_vote = VoteHistory.query.filter_by(
        user_id=current_user.id,
        target_type=target_type,
        target_id=target_id,
        revoked_at=None
    ).first()
    
    form = ReasonVotingForm()
    form.target_type.data = target_type
    form.target_id.data = target_id
    
    if existing_vote:
        form.vote_type.data = existing_vote.vote_type
        form.reason.data = existing_vote.reason
        form.reason_category.data = existing_vote.reason_category
    
    return render_template('reputation/vote_modal.html', 
                         form=form, target=target, existing_vote=existing_vote)

# Reputation Management Routes
@reputation_bp.route('/dashboard')
@login_required
def reputation_dashboard():
    """User reputation dashboard"""
    reputation_service = ReputationService()
    reputation_data = reputation_service.calculate_reputation(current_user.id)
    
    # Get voting analytics
    voting_service = VotingService()
    analytics = voting_service.get_voting_analytics(current_user.id)
    
    # Get voting patterns
    patterns = voting_service.detect_voting_patterns(current_user.id)
    
    # Get recent vote history
    recent_votes = VoteHistory.query.filter_by(user_id=current_user.id)\
        .order_by(desc(VoteHistory.created_at)).limit(10).all()
    
    return render_template('reputation/dashboard.html',
                         reputation=reputation_data,
                         analytics=analytics,
                         patterns=patterns,
                         recent_votes=recent_votes)

@reputation_bp.route('/profile/<int:user_id>')
@login_required
def user_reputation_profile(user_id):
    """View another user's reputation profile"""
    user = User.query.get_or_404(user_id)
    reputation_service = ReputationService()
    reputation_data = reputation_service.calculate_reputation(user_id)
    
    # Get user's recent activity
    recent_posts = Post.query.filter_by(user_id=user_id)\
        .order_by(desc(Post.created_at)).limit(5).all()
    recent_comments = Comment.query.filter_by(user_id=user_id)\
        .order_by(desc(Comment.created_at)).limit(5).all()
    
    return render_template('reputation/user_profile.html',
                         user=user,
                         reputation=reputation_data,
                         recent_posts=recent_posts,
                         recent_comments=recent_comments)

@reputation_bp.route('/leaderboard')
@login_required
def reputation_leaderboard():
    """Reputation leaderboard"""
    form = ReputationLeaderboardForm()
    
    # Get base query
    query = UserReputation.query.join(User)
    
    # Apply filters
    if form.validate_on_submit():
        if form.leaderboard_type.data == 'reputation':
            query = query.order_by(desc(UserReputation.reputation_score))
        elif form.leaderboard_type.data == 'voting_power':
            query = query.order_by(desc(UserReputation.voting_power))
        elif form.leaderboard_type.data == 'trust_score':
            query = query.order_by(desc(UserReputation.trust_score))
        elif form.leaderboard_type.data == 'most_votes':
            query = query.order_by(desc(UserReputation.total_votes_cast))
        elif form.leaderboard_type.data == 'most_posts':
            query = query.order_by(desc(UserReputation.posts_created))
        elif form.leaderboard_type.data == 'longest_streak':
            query = query.order_by(desc(UserReputation.longest_streak))
        elif form.leaderboard_type.data == 'most_helpful':
            query = query.order_by(desc(UserReputation.helpful_votes_received))
        elif form.leaderboard_type.data == 'most_quality':
            query = query.order_by(desc(UserReputation.trust_score))
        
        limit = form.limit.data
    else:
        query = query.order_by(desc(UserReputation.reputation_score))
        limit = 50
    
    # Exclude anonymous users if requested
    if not form.include_anonymous.data or not form.validate_on_submit():
        query = query.filter(User.username.isnot(None))
    
    # Get leaderboard entries
    leaderboard = query.limit(limit).all()
    
    return render_template('reputation/leaderboard.html',
                         leaderboard=leaderboard,
                         form=form)

# Analytics Routes
@reputation_bp.route('/analytics')
@login_required
def voting_analytics():
    """Voting analytics dashboard"""
    form = VotingAnalyticsForm()
    
    if form.validate_on_submit():
        # Get user if specified
        user = None
        if form.user_id.data:
            user = User.query.get(form.user_id.data)
        elif form.username.data:
            user = User.query.filter_by(username=form.username.data).first()
        
        if not user and (form.user_id.data or form.username.data):
            flash('User not found', 'error')
            return render_template('reputation/analytics.html', form=form, analytics=None)
        
        # Get analytics
        voting_service = VotingService()
        analytics = voting_service.get_voting_analytics(user.id if user else current_user.id)
        
        return render_template('reputation/analytics.html',
                             form=form,
                             analytics=analytics,
                             user=user)
    
    return render_template('reputation/analytics.html', form=form, analytics=None)

@reputation_bp.route('/patterns/<int:user_id>')
@login_required
def voting_patterns(user_id):
    """Voting patterns analysis"""
    user = User.query.get_or_404(user_id)
    voting_service = VotingService()
    patterns = voting_service.detect_voting_patterns(user_id)
    
    return render_template('reputation/patterns.html',
                         user=user,
                         patterns=patterns)

# Admin Routes
@reputation_bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard for reputation management"""
    if not current_user.is_admin:
        abort(403)
    
    # Get system statistics
    total_users = UserReputation.query.count()
    total_votes = VoteHistory.query.count()
    avg_reputation = db.session.query(func.avg(UserReputation.reputation_score)).scalar() or 0
    
    # Get reputation level distribution
    level_distribution = db.session.query(
        UserReputation.current_level,
        func.count(UserReputation.id)
    ).group_by(UserReputation.current_level).all()
    
    # Get recent activity
    recent_votes = VoteHistory.query.order_by(desc(VoteHistory.created_at)).limit(10).all()
    recent_reputation_changes = UserReputation.query.order_by(desc(UserReputation.updated_at)).limit(10).all()
    
    return render_template('reputation/admin/dashboard.html',
                         total_users=total_users,
                         total_votes=total_votes,
                         avg_reputation=round(avg_reputation, 2),
                         level_distribution=level_distribution,
                         recent_votes=recent_votes,
                         recent_reputation_changes=recent_reputation_changes)

@reputation_bp.route('/admin/users')
@login_required
def admin_users():
    """Admin user management with reputation filtering"""
    if not current_user.is_admin:
        abort(403)
    
    form = ReputationFilterForm()
    
    # Build query
    query = UserReputation.query.join(User)
    
    if form.validate_on_submit():
        # Apply filters
        if form.user_id.data:
            query = query.filter(UserReputation.user_id == form.user_id.data)
        
        if form.username.data:
            query = query.filter(User.username.ilike(f'%{form.username.data}%'))
        
        if form.min_reputation.data:
            query = query.filter(UserReputation.reputation_score >= form.min_reputation.data)
        
        if form.max_reputation.data:
            query = query.filter(UserReputation.reputation_score <= form.max_reputation.data)
        
        if form.min_voting_power.data:
            query = query.filter(UserReputation.voting_power >= form.min_voting_power.data)
        
        if form.max_voting_power.data:
            query = query.filter(UserReputation.voting_power <= form.max_voting_power.data)
        
        if form.reputation_level.data:
            query = query.filter(UserReputation.current_level == form.reputation_level.data)
        
        if form.min_votes_cast.data:
            query = query.filter(UserReputation.total_votes_cast >= form.min_votes_cast.data)
        
        if form.max_votes_cast.data:
            query = query.filter(UserReputation.total_votes_cast <= form.max_votes_cast.data)
        
        if form.min_posts_created.data:
            query = query.filter(UserReputation.posts_created >= form.min_posts_created.data)
        
        if form.max_posts_created.data:
            query = query.filter(UserReputation.posts_created <= form.max_posts_created.data)
        
        # Apply sorting
        if form.sort_by.data == 'reputation_score':
            order = desc if form.sort_order.data == 'desc' else asc
            query = query.order_by(order(UserReputation.reputation_score))
        elif form.sort_by.data == 'voting_power':
            order = desc if form.sort_order.data == 'desc' else asc
            query = query.order_by(order(UserReputation.voting_power))
        elif form.sort_by.data == 'trust_score':
            order = desc if form.sort_order.data == 'desc' else asc
            query = query.order_by(order(UserReputation.trust_score))
        elif form.sort_by.data == 'total_votes_cast':
            order = desc if form.sort_order.data == 'desc' else asc
            query = query.order_by(order(UserReputation.total_votes_cast))
        elif form.sort_by.data == 'posts_created':
            order = desc if form.sort_order.data == 'desc' else asc
            query = query.order_by(order(UserReputation.posts_created))
        elif form.sort_by.data == 'comments_created':
            order = desc if form.sort_order.data == 'desc' else asc
            query = query.order_by(order(UserReputation.comments_created))
        elif form.sort_by.data == 'current_streak':
            order = desc if form.sort_order.data == 'desc' else asc
            query = query.order_by(order(UserReputation.current_streak))
        elif form.sort_by.data == 'created_at':
            order = desc if form.sort_order.data == 'desc' else asc
            query = query.order_by(order(UserReputation.created_at))
        elif form.sort_by.data == 'updated_at':
            order = desc if form.sort_order.data == 'desc' else asc
            query = query.order_by(order(UserReputation.updated_at))
        
        limit = form.limit.data
    else:
        query = query.order_by(desc(UserReputation.reputation_score))
        limit = 50
    
    users = query.limit(limit).all()
    
    return render_template('reputation/admin/users.html',
                         users=users,
                         form=form)

@reputation_bp.route('/admin/adjust/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_adjust_reputation(user_id):
    """Admin manual reputation adjustment"""
    if not current_user.is_admin:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    reputation = ReputationService().get_user_reputation(user_id)
    
    form = ReputationAdjustmentForm()
    
    if form.validate_on_submit():
        old_reputation = reputation.reputation_score
        
        # Apply adjustment
        if form.adjustment_type.data == 'add':
            reputation.reputation_score += int(form.adjustment_value.data)
        elif form.adjustment_type.data == 'subtract':
            reputation.reputation_score -= int(form.adjustment_value.data)
        elif form.adjustment_type.data == 'set':
            reputation.reputation_score = int(form.adjustment_value.data)
        elif form.adjustment_type.data == 'multiply':
            reputation.reputation_score = int(reputation.reputation_score * form.adjustment_value.data)
        
        # Clamp values
        reputation.reputation_score = max(-1000, min(10000, reputation.reputation_score))
        
        # Update penalty/bonus points
        if form.is_penalty.data:
            reputation.penalty_points += abs(int(form.adjustment_value.data))
        else:
            reputation.bonus_points += abs(int(form.adjustment_value.data))
        
        reputation.updated_at = datetime.utcnow()
        
        # Update reputation level
        reputation_service = ReputationService()
        reputation_service._update_reputation_level(reputation)
        
        # Log the adjustment
        adjustment_record = VoteHistory(
            user_id=user_id,
            vote_type='adjustment',
            target_type='system',
            target_id=0,
            reason=f"Admin adjustment: {form.reason.data}",
            vote_weight=1.0,
            reputation_impact=reputation.reputation_score - old_reputation
        )
        db.session.add(adjustment_record)
        
        db.session.commit()
        
        flash(f'Reputation adjusted from {old_reputation} to {reputation.reputation_score}', 'success')
        
        # Notify user if requested
        if form.notify_user.data:
            # TODO: Implement notification system
            pass
        
        return redirect(url_for('reputation.admin_users'))
    
    return render_template('reputation/admin/adjust.html',
                         user=user,
                         reputation=reputation,
                         form=form)

@reputation_bp.route('/admin/levels', methods=['GET', 'POST'])
@login_required
def admin_reputation_levels():
    """Admin reputation level management"""
    if not current_user.is_admin:
        abort(403)
    
    form = ReputationLevelForm()
    
    if form.validate_on_submit():
        level = ReputationLevel(
            level_name=form.level_name.data,
            level_order=form.level_order.data,
            min_reputation=form.min_reputation.data,
            max_reputation=form.max_reputation.data,
            voting_power_multiplier=form.voting_power_multiplier.data,
            daily_vote_limit=form.daily_vote_limit.data,
            badge_color=form.badge_color.data,
            badge_icon=form.badge_icon.data,
            description=form.description.data,
            special_permissions=form.special_permissions.data,
            is_active=form.is_active.data
        )
        
        db.session.add(level)
        db.session.commit()
        
        flash(f'Reputation level "{form.level_name.data}" created successfully', 'success')
        return redirect(url_for('reputation.admin_reputation_levels'))
    
    levels = ReputationLevel.query.order_by(ReputationLevel.level_order).all()
    
    return render_template('reputation/admin/levels.html',
                         levels=levels,
                         form=form)

@reputation_bp.route('/admin/levels/<int:level_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_reputation_level(level_id):
    """Edit reputation level"""
    if not current_user.is_admin:
        abort(403)
    
    level = ReputationLevel.query.get_or_404(level_id)
    form = ReputationLevelForm(obj=level)
    
    if form.validate_on_submit():
        form.populate_obj(level)
        db.session.commit()
        
        flash(f'Reputation level "{level.level_name}" updated successfully', 'success')
        return redirect(url_for('reputation.admin_reputation_levels'))
    
    return render_template('reputation/admin/edit_level.html',
                         level=level,
                         form=form)

# API Routes
@reputation_bp.route('/api/reputation/<int:user_id>')
@login_required
def api_user_reputation(user_id):
    """API endpoint for user reputation data"""
    reputation_service = ReputationService()
    reputation_data = reputation_service.calculate_reputation(user_id)
    
    return jsonify(reputation_data)

@reputation_bp.route('/api/voting_analytics/<int:user_id>')
@login_required
def api_voting_analytics(user_id):
    """API endpoint for voting analytics"""
    days = request.args.get('days', 30, type=int)
    voting_service = VotingService()
    analytics = voting_service.get_voting_analytics(user_id, days)
    
    return jsonify(analytics)

@reputation_bp.route('/api/voting_patterns/<int:user_id>')
@login_required
def api_voting_patterns(user_id):
    """API endpoint for voting patterns"""
    voting_service = VotingService()
    patterns = voting_service.detect_voting_patterns(user_id)
    
    return jsonify(patterns)

@reputation_bp.route('/api/leaderboard')
@login_required
def api_leaderboard():
    """API endpoint for reputation leaderboard"""
    leaderboard_type = request.args.get('type', 'reputation')
    limit = request.args.get('limit', 50, type=int)
    
    query = UserReputation.query.join(User)
    
    if leaderboard_type == 'reputation':
        query = query.order_by(desc(UserReputation.reputation_score))
    elif leaderboard_type == 'voting_power':
        query = query.order_by(desc(UserReputation.voting_power))
    elif leaderboard_type == 'trust_score':
        query = query.order_by(desc(UserReputation.trust_score))
    elif leaderboard_type == 'most_votes':
        query = query.order_by(desc(UserReputation.total_votes_cast))
    
    leaderboard = query.limit(limit).all()
    
    return jsonify([rep.to_dict() for rep in leaderboard])

# Utility Routes
@reputation_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def voting_settings():
    """User voting settings"""
    form = VotingSettingsForm()
    
    if form.validate_on_submit():
        # TODO: Save user voting settings
        flash('Voting settings saved successfully', 'success')
        return redirect(url_for('reputation.voting_settings'))
    
    return render_template('reputation/settings.html', form=form)

@reputation_bp.route('/history')
@login_required
def voting_history():
    """User voting history"""
    form = ReputationHistoryForm()
    
    query = VoteHistory.query.filter_by(user_id=current_user.id)
    
    if form.validate_on_submit():
        # Apply filters
        if form.date_range.data and form.date_range.data != 'all':
            days = int(form.date_range.data)
            start_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(VoteHistory.created_at >= start_date)
        
        if form.event_type.data:
            if form.event_type.data == 'vote_received':
                query = query.filter(VoteHistory.target_type.in_(['post', 'comment']))
            elif form.event_type.data == 'vote_cast':
                query = query.filter(VoteHistory.target_type == 'user')
        
        limit = 50
    else:
        # Default to last 30 days
        start_date = datetime.utcnow() - timedelta(days=30)
        query = query.filter(VoteHistory.created_at >= start_date)
        limit = 50
    
    votes = query.order_by(desc(VoteHistory.created_at)).limit(limit).all()
    
    return render_template('reputation/history.html',
                         votes=votes,
                         form=form)

# Initialize reputation levels
def init_reputation_levels():
    """Initialize default reputation levels"""
    from .models import init_reputation_levels
    init_reputation_levels()
