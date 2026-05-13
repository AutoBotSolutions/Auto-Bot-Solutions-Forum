"""
Social Features Forms

This module contains forms for user social features including:
- User following/friend forms
- User group forms
- Social sharing forms
- Social activity forms
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from app.models import User


class FollowUserForm(FlaskForm):
    """Form for following a user"""
    user_id = HiddenField('User ID', validators=[DataRequired()])
    submit = SubmitField('Follow')


class UnfollowUserForm(FlaskForm):
    """Form for unfollowing a user"""
    user_id = HiddenField('User ID', validators=[DataRequired()])
    submit = SubmitField('Unfollow')


class SendFriendRequestForm(FlaskForm):
    """Form for sending friend request"""
    user_id = HiddenField('User ID', validators=[DataRequired()])
    message = TextAreaField('Message (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Send Friend Request')


class RespondFriendRequestForm(FlaskForm):
    """Form for responding to friend request"""
    request_id = HiddenField('Request ID', validators=[DataRequired()])
    action = SelectField('Response', choices=[
        ('accept', 'Accept'),
        ('decline', 'Decline')
    ], validators=[DataRequired()])
    submit = SubmitField('Respond')


class BlockUserForm(FlaskForm):
    """Form for blocking a user"""
    user_id = HiddenField('User ID', validators=[DataRequired()])
    reason = TextAreaField('Reason (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Block User')


class UnblockUserForm(FlaskForm):
    """Form for unblocking a user"""
    user_id = HiddenField('User ID', validators=[DataRequired()])
    submit = SubmitField('Unblock')


class CreateGroupForm(FlaskForm):
    """Form for creating a user group"""
    name = StringField('Group Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    group_type = SelectField('Group Type', choices=[
        ('custom', 'Custom'),
        ('family', 'Family'),
        ('work', 'Work'),
        ('school', 'School'),
        ('friends', 'Friends'),
        ('hobby', 'Hobby'),
        ('community', 'Community')
    ], validators=[DataRequired()])
    
    is_private = BooleanField('Private Group')
    color = StringField('Color', validators=[Optional(), Length(min=7, max=7)])
    icon = StringField('Icon', validators=[Optional(), Length(max=50)])
    
    submit = SubmitField('Create Group')


class EditGroupForm(FlaskForm):
    """Form for editing a user group"""
    name = StringField('Group Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    is_private = BooleanField('Private Group')
    color = StringField('Color', validators=[Optional(), Length(min=7, max=7)])
    icon = StringField('Icon', validators=[Optional(), Length(max=50)])
    
    submit = SubmitField('Update Group')


class AddGroupMemberForm(FlaskForm):
    """Form for adding member to group"""
    username = StringField('Username', validators=[DataRequired()])
    is_admin = BooleanField('Make Admin')
    submit = SubmitField('Add Member')


class RemoveGroupMemberForm(FlaskForm):
    """Form for removing member from group"""
    user_id = HiddenField('User ID', validators=[DataRequired()])
    submit = SubmitField('Remove')


class SocialShareForm(FlaskForm):
    """Form for social sharing"""
    content_type = SelectField('Content Type', choices=[
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('profile', 'Profile')
    ], validators=[DataRequired()])
    
    content_id = HiddenField('Content ID', validators=[DataRequired()])
    platform = SelectField('Platform', choices=[
        ('twitter', 'Twitter/X'),
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('reddit', 'Reddit'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('email', 'Email'),
        ('copy_link', 'Copy Link')
    ], validators=[DataRequired()])
    
    custom_message = TextAreaField('Custom Message', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Share')


class UserRecommendationForm(FlaskForm):
    """Form for user recommendations"""
    user_id = HiddenField('User ID', validators=[DataRequired()])
    recommendation_type = SelectField('Recommendation Type', choices=[
        ('follow', 'Follow'),
        ('friend', 'Friend Request'),
        ('similar_interests', 'Similar Interests'),
        ('mutual_friends', 'Mutual Friends')
    ], validators=[DataRequired()])
    
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Recommend')


class DismissRecommendationForm(FlaskForm):
    """Form for dismissing recommendations"""
    recommendation_id = HiddenField('Recommendation ID', validators=[DataRequired()])
    submit = SubmitField('Dismiss')


class SearchUsersForm(FlaskForm):
    """Form for searching users"""
    query = StringField('Search Users', validators=[DataRequired(), Length(min=2, max=100)])
    search_type = SelectField('Search Type', choices=[
        ('all', 'All Users'),
        ('friends', 'Friends'),
        ('following', 'Following'),
        ('followers', 'Followers'),
        ('mutual_friends', 'Mutual Friends'),
        ('recommendations', 'Recommended')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Search')


class SocialActivityFilterForm(FlaskForm):
    """Form for filtering social activity"""
    activity_type = SelectField('Activity Type', choices=[
        ('all', 'All Activities'),
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('follow', 'Follows'),
        ('friend', 'Friends'),
        ('like', 'Likes'),
        ('share', 'Shares')
    ], validators=[DataRequired()])
    
    time_range = SelectField('Time Range', choices=[
        ('all', 'All Time'),
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('year', 'This Year')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Filter')


class PrivacySettingsForm(FlaskForm):
    """Form for social privacy settings"""
    allow_follow_requests = BooleanField('Allow Follow Requests')
    allow_friend_requests = BooleanField('Allow Friend Requests')
    show_followers_publicly = BooleanField('Show Followers Publicly')
    show_following_publicly = BooleanField('Show Following Publicly')
    show_friends_publicly = BooleanField('Show Friends Publicly')
    allow_tagging = BooleanField('Allow Users to Tag Me')
    allow_mentions = BooleanField('Allow Users to Mention Me')
    show_activity_publicly = BooleanField('Show Activity Publicly')
    
    submit = SubmitField('Update Privacy Settings')


class SocialPreferencesForm(FlaskForm):
    """Form for social preferences"""
    email_new_follower = BooleanField('Email Notifications for New Followers')
    email_friend_request = BooleanField('Email Notifications for Friend Requests')
    email_friend_accepted = BooleanField('Email Notifications for Accepted Friend Requests')
    email_mention = BooleanField('Email Notifications for Mentions')
    email_tag = BooleanField('Email Notifications for Tags')
    
    push_new_follower = BooleanField('Push Notifications for New Followers')
    push_friend_request = BooleanField('Push Notifications for Friend Requests')
    push_friend_accepted = BooleanField('Push Notifications for Accepted Friend Requests')
    push_mention = BooleanField('Push Notifications for Mentions')
    push_tag = BooleanField('Push Notifications for Tags')
    
    submit = SubmitField('Update Social Preferences')
