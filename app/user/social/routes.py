"""
Social Features Routes

This module contains routes for user social features including:
- User following/friend system
- User connections and networking
- Social activity feeds
- User recommendations
- Social sharing options
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User
import json
from app.user.social.models import (
    UserFollow, UserFriend, SocialActivity, UserRecommendation, 
    SocialShare, UserGroup, GroupMember
)
from app.user.social.forms import (
    FollowUserForm, UnfollowUserForm, SendFriendRequestForm, RespondFriendRequestForm,
    BlockUserForm, UnblockUserForm, CreateGroupForm, EditGroupForm, AddGroupMemberForm,
    RemoveGroupMemberForm, SocialShareForm, UserRecommendationForm, DismissRecommendationForm,
    SearchUsersForm, SocialActivityFilterForm, PrivacySettingsForm, SocialPreferencesForm
)

social_bp = Blueprint('social', __name__, url_prefix='/social')

# User Following System

@social_bp.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    """Follow a user"""
    form = FollowUserForm()
    form.user_id.data = user_id
    
    if form.validate_on_submit():
        # Check if user exists
        target_user = User.query.get_or_404(user_id)
        
        # Check if already following
        if UserFollow.is_following(current_user.id, user_id):
            flash('You are already following this user.', 'info')
            return redirect(url_for('user.profile', username=target_user.username))
        
        # Create follow relationship
        follow = UserFollow.follow_user(current_user.id, user_id)
        
        if follow:
            # Create social activity
            SocialActivity.create_activity(
                user_id=current_user.id,
                activity_type='follow',
                action='started_following',
                target_type='user',
                target_id=user_id,
                description=f"{current_user.username} started following {target_user.username}"
            )
            
            flash(f'You are now following {target_user.username}!', 'success')
        else:
            flash('Unable to follow user.', 'error')
        
        return redirect(url_for('user.profile', username=target_user.username))
    
    return redirect(request.referrer or url_for('main.index'))

@social_bp.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    """Unfollow a user"""
    form = UnfollowUserForm()
    form.user_id.data = user_id
    
    if form.validate_on_submit():
        # Check if user exists
        target_user = User.query.get_or_404(user_id)
        
        # Remove follow relationship
        if UserFollow.unfollow_user(current_user.id, user_id):
            # Create social activity
            SocialActivity.create_activity(
                user_id=current_user.id,
                activity_type='follow',
                action='stopped_following',
                target_type='user',
                target_id=user_id,
                description=f"{current_user.username} stopped following {target_user.username}",
                is_public=False
            )
            
            flash(f'You have unfollowed {target_user.username}.', 'success')
        else:
            flash('Unable to unfollow user.', 'error')
        
        return redirect(url_for('user.profile', username=target_user.username))
    
    return redirect(request.referrer or url_for('main.index'))

# User Friend System

@social_bp.route('/friend/request/<int:user_id>', methods=['POST'])
@login_required
def send_friend_request(user_id):
    """Send a friend request"""
    form = SendFriendRequestForm()
    form.user_id.data = user_id
    
    if form.validate_on_submit():
        # Check if user exists
        target_user = User.query.get_or_404(user_id)
        
        # Create friend request
        friend_request = UserFriend.send_friend_request(current_user.id, user_id)
        
        if friend_request:
            # Create social activity
            SocialActivity.create_activity(
                user_id=current_user.id,
                activity_type='friend',
                action='sent_request',
                target_type='user',
                target_id=user_id,
                description=f"{current_user.username} sent a friend request to {target_user.username}",
                metadata={'message': form.message.data}
            )
            
            flash(f'Friend request sent to {target_user.username}!', 'success')
        else:
            flash('Unable to send friend request.', 'error')
        
        return redirect(url_for('user.profile', username=target_user.username))
    
    return redirect(request.referrer or url_for('main.index'))

@social_bp.route('/friend/respond/<int:request_id>', methods=['POST'])
@login_required
def respond_friend_request(request_id):
    """Respond to a friend request"""
    form = RespondFriendRequestForm()
    form.request_id.data = request_id
    
    if form.validate_on_submit():
        friend_request = UserFriend.query.get_or_404(request_id)
        
        # Verify user is part of the friendship
        if current_user.id not in [friend_request.user1_id, friend_request.user2_id]:
            flash('Invalid friend request.', 'error')
            return redirect(request.referrer or url_for('main.index'))
        
        if form.action.data == 'accept':
            if UserFriend.accept_friend_request(request_id, current_user.id):
                # Get the other user
                other_user_id = friend_request.user1_id if friend_request.user2_id == current_user.id else friend_request.user2_id
                other_user = User.query.get(other_user_id)
                
                # Create social activity
                SocialActivity.create_activity(
                    user_id=current_user.id,
                    activity_type='friend',
                    action='accepted_request',
                    target_type='user',
                    target_id=other_user_id,
                    description=f"{current_user.username} accepted friend request from {other_user.username}"
                )
                
                flash(f'You are now friends with {other_user.username}!', 'success')
            else:
                flash('Unable to accept friend request.', 'error')
        
        elif form.action.data == 'decline':
            if UserFriend.decline_friend_request(request_id, current_user.id):
                flash('Friend request declined.', 'info')
            else:
                flash('Unable to decline friend request.', 'error')
        
        return redirect(request.referrer or url_for('main.index'))
    
    return redirect(request.referrer or url_for('main.index'))

@social_bp.route('/friend/block/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    """Block a user"""
    form = BlockUserForm()
    form.user_id.data = user_id
    
    if form.validate_on_submit():
        # Check if user exists
        target_user = User.query.get_or_404(user_id)
        
        # Block user
        if UserFriend.block_user(current_user.id, user_id, current_user.id):
            # Create social activity
            SocialActivity.create_activity(
                user_id=current_user.id,
                activity_type='friend',
                action='blocked',
                target_type='user',
                target_id=user_id,
                description=f"{current_user.username} blocked {target_user.username}",
                is_public=False
            )
            
            flash(f'You have blocked {target_user.username}.', 'success')
        else:
            flash('Unable to block user.', 'error')
        
        return redirect(url_for('user.profile', username=target_user.username))
    
    return redirect(request.referrer or url_for('main.index'))

# User Groups System

@social_bp.route('/groups', methods=['GET'])
@login_required
def groups():
    """User groups dashboard"""
    user_groups = UserGroup.query.filter_by(creator_id=current_user.id).all()
    member_groups = [group for group in current_user.groups if group.creator_id != current_user.id]
    
    return render_template('social/groups.html', 
                         created_groups=user_groups,
                         member_groups=member_groups)

@social_bp.route('/groups/create', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create a new user group"""
    form = CreateGroupForm()
    
    if form.validate_on_submit():
        group = UserGroup.create_group(
            name=form.name.data,
            creator_id=current_user.id,
            description=form.description.data,
            is_private=form.is_private.data,
            group_type=form.group_type.data,
            color=form.color.data,
            icon=form.icon.data
        )
        
        flash(f'Group "{group.name}" created successfully!', 'success')
        return redirect(url_for('social.view_group', group_id=group.id))
    
    return render_template('social/create_group.html', form=form)

@social_bp.route('/groups/<int:group_id>')
@login_required
def view_group(group_id):
    """View group details"""
    group = UserGroup.query.get_or_404(group_id)
    
    # Check if user is member or group is public
    if not group.is_private and not group.is_member(current_user.id):
        flash('This is a private group.', 'error')
        return redirect(url_for('social.groups'))
    
    members = GroupMember.query.filter_by(group_id=group_id).all()
    is_admin = GroupMember.is_admin(group_id, current_user.id)
    
    return render_template('social/view_group.html', 
                         group=group,
                         members=members,
                         is_admin=is_admin)

@social_bp.route('/groups/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    """Edit group details"""
    group = UserGroup.query.get_or_404(group_id)
    
    # Check if user is admin
    if not GroupMember.is_admin(group_id, current_user.id):
        flash('You do not have permission to edit this group.', 'error')
        return redirect(url_for('social.view_group', group_id=group_id))
    
    form = EditGroupForm()
    
    if form.validate_on_submit():
        group.name = form.name.data
        group.description = form.description.data
        group.is_private = form.is_private.data
        group.color = form.color.data
        group.icon = form.icon.data
        group.updated_at = group.updated_at.default.arg
        
        db.session.commit()
        flash(f'Group "{group.name}" updated successfully!', 'success')
        return redirect(url_for('social.view_group', group_id=group_id))
    
    # Pre-fill form
    form.name.data = group.name
    form.description.data = group.description
    form.is_private.data = group.is_private
    form.color.data = group.color
    form.icon.data = group.icon
    
    return render_template('social/edit_group.html', form=form, group=group)

@social_bp.route('/groups/<int:group_id>/add_member', methods=['POST'])
@login_required
def add_group_member(group_id):
    """Add member to group"""
    group = UserGroup.query.get_or_404(group_id)
    form = AddGroupMemberForm()
    
    # Check if user is admin
    if not GroupMember.is_admin(group_id, current_user.id):
        flash('You do not have permission to add members to this group.', 'error')
        return redirect(url_for('social.view_group', group_id=group_id))
    
    if form.validate_on_submit():
        # Find user by username
        target_user = User.query.filter_by(username=form.username.data).first()
        
        if not target_user:
            flash('User not found.', 'error')
            return redirect(url_for('social.view_group', group_id=group_id))
        
        # Add member
        if group.add_member(target_user.id, form.is_admin.data):
            flash(f'{target_user.username} added to group successfully!', 'success')
        else:
            flash('User is already a member of this group.', 'info')
        
        return redirect(url_for('social.view_group', group_id=group_id))
    
    return redirect(url_for('social.view_group', group_id=group_id))

# Social Activity Feed

@social_bp.route('/feed')
@login_required
def activity_feed():
    """Social activity feed"""
    form = SocialActivityFilterForm()
    activities = []
    
    if request.args.get('filter'):
        form.activity_type.data = request.args.get('activity_type', 'all')
        form.time_range.data = request.args.get('time_range', 'all')
        
        # Apply filters (simplified for now)
        activities = SocialActivity.get_activity_feed(current_user.id, limit=50)
        
        if form.activity_type.data != 'all':
            activities = [a for a in activities if a.activity_type == form.activity_type.data]
    else:
        activities = SocialActivity.get_activity_feed(current_user.id, limit=50)
    
    return render_template('social/activity_feed.html', 
                         activities=activities,
                         form=form)

# User Recommendations

@social_bp.route('/recommendations')
@login_required
def recommendations():
    """User recommendations"""
    follow_recommendations = UserRecommendation.get_recommendations(
        current_user.id, 'follow', limit=10
    )
    friend_recommendations = UserRecommendation.get_recommendations(
        current_user.id, 'friend', limit=10
    )
    
    return render_template('social/recommendations.html',
                         follow_recommendations=follow_recommendations,
                         friend_recommendations=friend_recommendations)

@social_bp.route('/recommendations/dismiss/<int:recommendation_id>', methods=['POST'])
@login_required
def dismiss_recommendation(recommendation_id):
    """Dismiss a recommendation"""
    form = DismissRecommendationForm()
    form.recommendation_id.data = recommendation_id
    
    if form.validate_on_submit():
        if UserRecommendation.dismiss_recommendation(recommendation_id, current_user.id):
            flash('Recommendation dismissed.', 'info')
        else:
            flash('Unable to dismiss recommendation.', 'error')
    
    return redirect(request.referrer or url_for('social.recommendations'))

# Social Sharing

@social_bp.route('/share', methods=['POST'])
@login_required
def share_content():
    """Share content to social platforms"""
    form = SocialShareForm()
    
    if form.validate_on_submit():
        share = SocialShare.create_share(
            user_id=current_user.id,
            content_type=form.content_type.data,
            content_id=form.content_id.data,
            platform=form.platform.data,
            share_text=form.custom_message.data
        )
        
        if share:
            flash(f'Content shared to {form.platform.data.title()}!', 'success')
        else:
            flash('Unable to share content.', 'error')
        
        return redirect(request.referrer or url_for('main.index'))
    
    return redirect(request.referrer or url_for('main.index'))

# User Search

@social_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search_users():
    """Search for users"""
    form = SearchUsersForm()
    users = []
    
    if form.validate_on_submit() or request.args.get('q'):
        query = request.args.get('q', form.query.data)
        search_type = request.args.get('type', form.search_type.data)
        
        # Search users
        users_query = User.query.filter(
            User.username.ilike(f'%{query}%') |
            User.email.ilike(f'%{query}%')
        )
        
        # Apply search type filter
        if search_type == 'friends':
            # Get user's friends
            friend_ids = []
            friendships = UserFriend.get_friends(current_user.id)
            for friendship in friendships:
                friend_ids.extend([friendship.user1_id, friendship.user2_id])
            users_query = users_query.filter(User.id.in_(friend_ids))
        
        elif search_type == 'following':
            # Get users that current user follows
            following_ids = [f.following_id for f in current_user.following_relationships]
            users_query = users_query.filter(User.id.in_(following_ids))
        
        elif search_type == 'followers':
            # Get users that follow current user
            follower_ids = [f.follower_id for f in current_user.follower_relationships]
            users_query = users_query.filter(User.id.in_(follower_ids))
        
        users = users_query.limit(50).all()
        
        # Update form for template
        form.query.data = query
        form.search_type.data = search_type
    
    return render_template('social/search_users.html', form=form, users=users)

# Social Settings

@social_bp.route('/settings/privacy', methods=['GET', 'POST'])
@login_required
def privacy_settings():
    """Social privacy settings"""
    form = PrivacySettingsForm()
    
    if form.validate_on_submit():
        # Store privacy settings (would need to add fields to User model)
        privacy_settings = {
            'allow_follow_requests': form.allow_follow_requests.data,
            'allow_friend_requests': form.allow_friend_requests.data,
            'show_followers_publicly': form.show_followers_publicly.data,
            'show_following_publicly': form.show_following_publicly.data,
            'show_friends_publicly': form.show_friends_publicly.data,
            'allow_tagging': form.allow_tagging.data,
            'allow_mentions': form.allow_mentions.data,
            'show_activity_publicly': form.show_activity_publicly.data
        }
        
        # Store in user social preferences field (would need to add to User model)
        current_user.social_preferences = json.dumps(privacy_settings)
        db.session.commit()
        
        flash('Privacy settings updated successfully!', 'success')
        return redirect(url_for('social.privacy_settings'))
    
    # Load current settings if they exist
    if hasattr(current_user, 'social_preferences') and current_user.social_preferences:
        try:
            settings = json.loads(current_user.social_preferences)
            form.allow_follow_requests.data = settings.get('allow_follow_requests', True)
            form.allow_friend_requests.data = settings.get('allow_friend_requests', True)
            form.show_followers_publicly.data = settings.get('show_followers_publicly', True)
            form.show_following_publicly.data = settings.get('show_following_publicly', True)
            form.show_friends_publicly.data = settings.get('show_friends_publicly', True)
            form.allow_tagging.data = settings.get('allow_tagging', True)
            form.allow_mentions.data = settings.get('allow_mentions', True)
            form.show_activity_publicly.data = settings.get('show_activity_publicly', True)
        except:
            pass  # Use defaults
    
    return render_template('social/privacy_settings.html', form=form)

@social_bp.route('/settings/preferences', methods=['GET', 'POST'])
@login_required
def social_preferences():
    """Social notification preferences"""
    form = SocialPreferencesForm()
    
    if form.validate_on_submit():
        # Store social preferences
        social_prefs = {
            'email': {
                'new_follower': form.email_new_follower.data,
                'friend_request': form.email_friend_request.data,
                'friend_accepted': form.email_friend_accepted.data,
                'mention': form.email_mention.data,
                'tag': form.email_tag.data
            },
            'push': {
                'new_follower': form.push_new_follower.data,
                'friend_request': form.push_friend_request.data,
                'friend_accepted': form.push_friend_accepted.data,
                'mention': form.push_mention.data,
                'tag': form.push_tag.data
            }
        }
        
        # Store in user social preferences field
        current_user.social_preferences = json.dumps(social_prefs)
        db.session.commit()
        
        flash('Social preferences updated successfully!', 'success')
        return redirect(url_for('social.social_preferences'))
    
    # Load current preferences
    if hasattr(current_user, 'social_preferences') and current_user.social_preferences:
        try:
            prefs = json.loads(current_user.social_preferences)
            
            # Email preferences
            email_prefs = prefs.get('email', {})
            form.email_new_follower.data = email_prefs.get('new_follower', True)
            form.email_friend_request.data = email_prefs.get('friend_request', True)
            form.email_friend_accepted.data = email_prefs.get('friend_accepted', True)
            form.email_mention.data = email_prefs.get('mention', True)
            form.email_tag.data = email_prefs.get('tag', True)
            
            # Push preferences
            push_prefs = prefs.get('push', {})
            form.push_new_follower.data = push_prefs.get('new_follower', True)
            form.push_friend_request.data = push_prefs.get('friend_request', True)
            form.push_friend_accepted.data = push_prefs.get('friend_accepted', True)
            form.push_mention.data = push_prefs.get('mention', True)
            form.push_tag.data = push_prefs.get('tag', True)
        except:
            pass  # Use defaults
    
    return render_template('social/social_preferences.html', form=form)
