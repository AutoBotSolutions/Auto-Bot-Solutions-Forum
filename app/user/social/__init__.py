"""
Social Features Package

This package contains all social features functionality including:
- User following/friend system
- User connections and networking
- Social activity feeds
- User recommendations
- Social sharing options
"""

from .models import (
    UserFollow, UserFriend, SocialActivity, UserRecommendation, 
    SocialShare, UserGroup, GroupMember
)

from .forms import (
    FollowUserForm, UnfollowUserForm, SendFriendRequestForm, RespondFriendRequestForm,
    BlockUserForm, UnblockUserForm, CreateGroupForm, EditGroupForm, AddGroupMemberForm,
    RemoveGroupMemberForm, SocialShareForm, UserRecommendationForm, DismissRecommendationForm,
    SearchUsersForm, SocialActivityFilterForm, PrivacySettingsForm, SocialPreferencesForm
)

from .routes import social_bp

__all__ = [
    # Models
    'UserFollow', 'UserFriend', 'SocialActivity', 'UserRecommendation', 
    'SocialShare', 'UserGroup', 'GroupMember',
    
    # Forms
    'FollowUserForm', 'UnfollowUserForm', 'SendFriendRequestForm', 'RespondFriendRequestForm',
    'BlockUserForm', 'UnblockUserForm', 'CreateGroupForm', 'EditGroupForm', 'AddGroupMemberForm',
    'RemoveGroupMemberForm', 'SocialShareForm', 'UserRecommendationForm', 'DismissRecommendationForm',
    'SearchUsersForm', 'SocialActivityFilterForm', 'PrivacySettingsForm', 'SocialPreferencesForm',
    
    # Blueprint
    'social_bp'
]
