"""
Unit tests for the Social Features System
"""

import pytest
from datetime import datetime, timedelta
from app.user.social.models import UserFollow, UserFriend, SocialActivity, UserGroup, GroupMember, UserRecommendation, SocialShare


class TestUserFollow:
    """Test suite for user follow functionality."""

    def test_follow_user(self, sample_user, sample_admin_user):
        """Test following a user."""
        follow = UserFollow.follow_user(sample_user.id, sample_admin_user.id)
        
        assert follow is not None
        assert follow.follower_id == sample_user.id
        assert follow.following_id == sample_admin_user.id
        assert follow.is_mutual is False
        assert follow.is_close_friend is False

    def test_follow_self(self, sample_user):
        """Test following self (should return None)."""
        follow = UserFollow.follow_user(sample_user.id, sample_user.id)
        assert follow is None

    def test_duplicate_follow(self, sample_user, sample_admin_user):
        """Test following same user twice."""
        follow1 = UserFollow.follow_user(sample_user.id, sample_admin_user.id)
        follow2 = UserFollow.follow_user(sample_user.id, sample_admin_user.id)
        
        assert follow1 is not None
        assert follow2 is not None
        assert follow1.id == follow2.id

    def test_mutual_follow(self, sample_user, sample_admin_user):
        """Test mutual following."""
        # First follow
        follow1 = UserFollow.follow_user(sample_user.id, sample_admin_user.id)
        assert follow1.is_mutual is False
        
        # Second follow (mutual)
        follow2 = UserFollow.follow_user(sample_admin_user.id, sample_user.id)
        assert follow2.is_mutual is True
        
        # Check first follow is now mutual
        db.session.refresh(follow1)
        assert follow1.is_mutual is True

    def test_unfollow_user(self, sample_user, sample_admin_user, sample_user_follow):
        """Test unfollowing a user."""
        result = UserFollow.unfollow_user(sample_user.id, sample_admin_user.id)
        assert result is True
        
        # Check follow relationship is removed
        follow = UserFollow.query.filter_by(
            follower_id=sample_user.id,
            following_id=sample_admin_user.id
        ).first()
        assert follow is None

    def test_unfollow_nonexistent(self, sample_user, sample_admin_user):
        """Test unfollowing non-existent relationship."""
        result = UserFollow.unfollow_user(sample_user.id, sample_admin_user.id)
        assert result is False

    def test_is_following(self, sample_user, sample_admin_user, sample_user_follow):
        """Test checking if user is following another."""
        is_following = UserFollow.is_following(sample_user.id, sample_admin_user.id)
        assert is_following is True
        
        is_following_reverse = UserFollow.is_following(sample_admin_user.id, sample_user.id)
        assert is_following_reverse is False

    def test_get_followers(self, sample_user, sample_admin_user, sample_user_follow):
        """Test getting user's followers."""
        followers = UserFollow.get_followers(sample_admin_user.id)
        assert len(followers) == 1
        assert followers[0].follower_id == sample_user.id

    def test_get_following(self, sample_user, sample_admin_user, sample_user_follow):
        """Test getting users that user is following."""
        following = UserFollow.get_following(sample_user.id)
        assert len(following) == 1
        assert following[0].following_id == sample_admin_user.id

    def test_close_friend(self, sample_user, sample_admin_user, sample_user_follow):
        """Test marking as close friend."""
        sample_user_follow.is_close_friend = True
        db.session.commit()
        
        follow = UserFollow.query.filter_by(
            follower_id=sample_user.id,
            following_id=sample_admin_user.id
        ).first()
        assert follow.is_close_friend is True


class TestUserFriend:
    """Test suite for user friend functionality."""

    def test_send_friend_request(self, sample_user, sample_admin_user):
        """Test sending a friend request."""
        friend_request = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        
        assert friend_request is not None
        assert friend_request.user1_id == sample_user.id
        assert friend_request.user2_id == sample_admin_user.id
        assert friend_request.status == 'pending'
        assert friend_request.requested_by_id == sample_user.id

    def test_send_friend_request_self(self, sample_user):
        """Test sending friend request to self (should return None)."""
        friend_request = UserFriend.send_friend_request(
            sample_user.id, sample_user.id, sample_user.id
        )
        assert friend_request is None

    def test_duplicate_friend_request(self, sample_user, sample_admin_user):
        """Test sending duplicate friend request."""
        request1 = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        request2 = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        
        assert request1 is not None
        assert request2 is not None
        assert request1.id == request2.id

    def test_accept_friend_request(self, sample_user, sample_admin_user):
        """Test accepting a friend request."""
        friend_request = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        
        result = UserFriend.accept_friend_request(friend_request.id, sample_admin_user.id)
        assert result is True
        
        db.session.refresh(friend_request)
        assert friend_request.status == 'accepted'
        assert friend_request.responded_at is not None

    def test_accept_friend_request_unauthorized(self, sample_user, sample_admin_user):
        """Test accepting friend request by unauthorized user."""
        friend_request = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        
        # Try to accept with wrong user
        result = UserFriend.accept_friend_request(friend_request.id, sample_user.id)
        assert result is False

    def test_decline_friend_request(self, sample_user, sample_admin_user):
        """Test declining a friend request."""
        friend_request = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        
        result = UserFriend.decline_friend_request(friend_request.id, sample_admin_user.id)
        assert result is True
        
        db.session.refresh(friend_request)
        assert friend_request.status == 'declined'
        assert friend_request.responded_at is not None

    def test_are_friends(self, sample_user, sample_admin_user):
        """Test checking if users are friends."""
        # Initially not friends
        assert UserFriend.are_friends(sample_user.id, sample_admin_user.id) is False
        
        # Send and accept request
        friend_request = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        UserFriend.accept_friend_request(friend_request.id, sample_admin_user.id)
        
        # Now they should be friends
        assert UserFriend.are_friends(sample_user.id, sample_admin_user.id) is True

    def test_get_friends(self, sample_user, sample_admin_user):
        """Test getting user's friends."""
        # Create friendship
        friend_request = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        UserFriend.accept_friend_request(friend_request.id, sample_admin_user.id)
        
        friends = UserFriend.get_friends(sample_user.id)
        assert len(friends) == 1
        assert friends[0].user2_id == sample_admin_user.id

    def test_get_pending_requests(self, sample_user, sample_admin_user):
        """Test getting pending friend requests."""
        # Send request
        friend_request = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        
        pending = UserFriend.get_pending_requests(sample_admin_user.id)
        assert len(pending) == 1
        assert pending[0].id == friend_request.id

    def test_friend_request_history(self, sample_user, sample_admin_user):
        """Test friend request history."""
        # Send and decline request
        friend_request = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        UserFriend.decline_friend_request(friend_request.id, sample_admin_user.id)
        
        # Send new request
        new_request = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        
        # Should get the new pending request
        pending = UserFriend.get_pending_requests(sample_admin_user.id)
        assert len(pending) == 1
        assert pending[0].id == new_request.id


class TestSocialActivity:
    """Test suite for social activity functionality."""

    def test_create_activity(self, sample_user):
        """Test creating social activity."""
        activity = SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='post',
            action='created',
            target_type='post',
            target_id=1,
            description='User created a new post',
            metadata={'word_count': 500}
        )
        
        assert activity is not None
        assert activity.user_id == sample_user.id
        assert activity.activity_type == 'post'
        assert activity.action == 'created'
        assert activity.target_type == 'post'
        assert activity.target_id == 1
        assert activity.description == 'User created a new post'
        assert activity.metadata['word_count'] == 500

    def test_get_activity_feed(self, sample_user, sample_admin_user, sample_social_activity):
        """Test getting activity feed."""
        # Create more activities
        for i in range(5):
            SocialActivity.create_activity(
                user_id=sample_admin_user.id,
                activity_type='comment',
                action='created',
                target_type='comment',
                target_id=i + 1,
                description=f'Admin created comment {i + 1}'
            )
        
        # Get feed for sample_user (should include own and friends' activities)
        feed = SocialActivity.get_activity_feed(sample_user.id, limit=10)
        assert len(feed) >= 1  # At least the sample activity
        
        # Get feed without friends
        feed_no_friends = SocialActivity.get_activity_feed(sample_user.id, limit=10, include_friends=False)
        assert len(feed_no_friends) >= 1

    def test_filter_activity_by_type(self, sample_user, sample_admin_user):
        """Test filtering activity by type."""
        # Create different types of activities
        SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='post',
            action='created',
            target_type='post',
            target_id=1
        )
        
        SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='comment',
            action='created',
            target_type='comment',
            target_id=1
        )
        
        SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='like',
            action='created',
            target_type='post',
            target_id=1
        )
        
        # Get all activities
        all_activities = SocialActivity.query.filter_by(user_id=sample_user.id).all()
        assert len(all_activities) == 3
        
        # Filter by type
        post_activities = SocialActivity.query.filter_by(
            user_id=sample_user.id,
            activity_type='post'
        ).all()
        assert len(post_activities) == 1

    def test_activity_privacy(self, sample_user):
        """Test activity privacy settings."""
        # Create public activity
        public_activity = SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='post',
            action='created',
            is_public=True
        )
        
        # Create private activity
        private_activity = SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='message',
            action='sent',
            is_public=False
        )
        
        # Check privacy
        assert public_activity.is_public is True
        assert private_activity.is_public is False

    def test_activity_metadata(self, sample_user):
        """Test activity metadata handling."""
        metadata = {
            'word_count': 500,
            'has_images': True,
            'tags': ['python', 'flask'],
            'sentiment': 0.8
        }
        
        activity = SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='post',
            action='created',
            metadata=metadata
        )
        
        assert activity.metadata['word_count'] == 500
        assert activity.metadata['has_images'] is True
        assert activity.metadata['tags'] == ['python', 'flask']
        assert activity.metadata['sentiment'] == 0.8


class TestUserGroup:
    """Test suite for user group functionality."""

    def test_create_group(self, sample_user):
        """Test creating a user group."""
        group = UserGroup.create_group(
            name='Test Group',
            creator_id=sample_user.id,
            description='A test group',
            is_private=False,
            group_type='custom',
            color='#007bff'
        )
        
        assert group is not None
        assert group.name == 'Test Group'
        assert group.creator_id == sample_user.id
        assert group.description == 'A test group'
        assert group.is_private is False
        assert group.group_type == 'custom'
        assert group.color == '#007bff'
        assert group.is_member(sample_user.id) is True

    def test_add_member(self, sample_user, sample_admin_user, sample_user_group):
        """Test adding member to group."""
        result = sample_user_group.add_member(sample_admin_user.id)
        assert result is True
        assert sample_user_group.is_member(sample_admin_user.id) is True

    def test_remove_member(self, sample_user, sample_admin_user, sample_user_group):
        """Test removing member from group."""
        # Add member first
        sample_user_group.add_member(sample_admin_user.id)
        assert sample_user_group.is_member(sample_admin_user.id) is True
        
        # Remove member
        result = sample_user_group.remove_member(sample_admin_user.id)
        assert result is True
        assert sample_user_group.is_member(sample_admin_user.id) is False

    def test_get_member_count(self, sample_user, sample_user_group):
        """Test getting group member count."""
        count = sample_user_group.get_member_count()
        assert count == 1  # Only the creator
        
        # Add another member
        sample_user_group.add_member(sample_admin_user.id)
        count = sample_user_group.get_member_count()
        assert count == 2

    def test_group_types(self, sample_user):
        """Test different group types."""
        group_types = ['family', 'work', 'school', 'friends', 'hobby', 'community', 'custom']
        
        for group_type in group_types:
            group = UserGroup.create_group(
                name=f'{group_type.title()} Group',
                creator_id=sample_user.id,
                group_type=group_type
            )
            assert group.group_type == group_type

    def test_private_group(self, sample_user, sample_admin_user):
        """Test private group functionality."""
        group = UserGroup.create_group(
            name='Private Group',
            creator_id=sample_user.id,
            is_private=True
        )
        
        # Non-members should not be able to access
        assert group.is_member(sample_admin_user.id) is False
        
        # Add member
        group.add_member(sample_admin_user.id)
        assert group.is_member(sample_admin_user.id) is True

    def test_group_admin(self, sample_user, sample_admin_user, sample_user_group):
        """Test group admin functionality."""
        # Add member as admin
        sample_user_group.add_member(sample_admin_user.id, is_admin=True)
        
        # Check admin status
        is_admin = GroupMember.is_admin(sample_user_group.id, sample_admin_user.id)
        assert is_admin is True
        
        # Check creator is also admin
        is_creator_admin = GroupMember.is_admin(sample_user_group.id, sample_user.id)
        assert is_creator_admin is True


class TestUserRecommendation:
    """Test suite for user recommendation functionality."""

    def test_create_recommendation(self, sample_user, sample_admin_user):
        """Test creating user recommendation."""
        recommendation = UserRecommendation.create_recommendation(
            user_id=sample_user.id,
            recommended_user_id=sample_admin_user.id,
            recommendation_type='follow',
            score=0.8,
            reason='Similar interests in programming',
            metadata={'common_tags': ['python', 'flask']}
        )
        
        assert recommendation is not None
        assert recommendation.user_id == sample_user.id
        assert recommendation.recommended_user_id == sample_admin_user.id
        assert recommendation.recommendation_type == 'follow'
        assert recommendation.score == 0.8
        assert recommendation.reason == 'Similar interests in programming'
        assert recommendation.metadata['common_tags'] == ['python', 'flask']

    def test_duplicate_recommendation(self, sample_user, sample_admin_user):
        """Test handling duplicate recommendations."""
        rec1 = UserRecommendation.create_recommendation(
            user_id=sample_user.id,
            recommended_user_id=sample_admin_user.id,
            recommendation_type='follow',
            score=0.7
        )
        
        rec2 = UserRecommendation.create_recommendation(
            user_id=sample_user.id,
            recommended_user_id=sample_admin_user.id,
            recommendation_type='follow',
            score=0.9  # Higher score should update
        )
        
        assert rec1 is not None
        assert rec2 is not None
        assert rec1.id == rec2.id
        
        # Should have higher score
        db.session.refresh(rec1)
        assert rec1.score == 0.9

    def test_get_recommendations(self, sample_user, sample_admin_user):
        """Test getting user recommendations."""
        # Create different types of recommendations
        UserRecommendation.create_recommendation(
            user_id=sample_user.id,
            recommended_user_id=sample_admin_user.id,
            recommendation_type='follow',
            score=0.8
        )
        
        # Create another user for different recommendation
        other_user = User(username='other', email='other@example.com', password_hash='hash')
        db.session.add(other_user)
        db.session.commit()
        
        UserRecommendation.create_recommendation(
            user_id=sample_user.id,
            recommended_user_id=other_user.id,
            recommendation_type='friend',
            score=0.6
        )
        
        # Get all recommendations
        all_recs = UserRecommendation.get_recommendations(sample_user.id, limit=10)
        assert len(all_recs) == 2
        
        # Get follow recommendations only
        follow_recs = UserRecommendation.get_recommendations(
            sample_user.id, recommendation_type='follow', limit=10
        )
        assert len(follow_recs) == 1
        assert follow_recs[0].recommendation_type == 'follow'

    def test_dismiss_recommendation(self, sample_user, sample_admin_user):
        """Test dismissing recommendations."""
        recommendation = UserRecommendation.create_recommendation(
            user_id=sample_user.id,
            recommended_user_id=sample_admin_user.id,
            recommendation_type='follow',
            score=0.8
        )
        
        # Should be in recommendations
        recs = UserRecommendation.get_recommendations(sample_user.id)
        assert len(recs) == 1
        
        # Dismiss recommendation
        result = UserRecommendation.dismiss_recommendation(recommendation.id, sample_user.id)
        assert result is True
        
        # Should not be in recommendations anymore
        recs = UserRecommendation.get_recommendations(sample_user.id)
        assert len(recs) == 0

    def test_recommendation_scoring(self, sample_user, sample_admin_user):
        """Test recommendation scoring and sorting."""
        # Create multiple recommendations with different scores
        other_user = User(username='other', email='other@example.com', password_hash='hash')
        db.session.add(other_user)
        db.session.commit()
        
        # Create recommendations with different scores
        UserRecommendation.create_recommendation(
            user_id=sample_user.id,
            recommended_user_id=sample_admin_user.id,
            recommendation_type='follow',
            score=0.5
        )
        
        UserRecommendation.create_recommendation(
            user_id=sample_user.id,
            recommended_user_id=other_user.id,
            recommendation_type='follow',
            score=0.9
        )
        
        # Get recommendations (should be sorted by score descending)
        recs = UserRecommendation.get_recommendations(
            sample_user.id, recommendation_type='follow'
        )
        assert len(recs) == 2
        assert recs[0].score >= recs[1].score


class TestSocialShare:
    """Test suite for social sharing functionality."""

    def test_create_share(self, sample_user):
        """Test creating social share."""
        share = SocialShare.create_share(
            user_id=sample_user.id,
            content_type='post',
            content_id=1,
            platform='twitter',
            share_url='https://twitter.com/share/123',
            share_text='Check out this post!',
            metadata={'hashtags': ['#python', '#flask']}
        )
        
        assert share is not None
        assert share.user_id == sample_user.id
        assert share.content_type == 'post'
        assert share.content_id == 1
        assert share.platform == 'twitter'
        assert share.share_url == 'https://twitter.com/share/123'
        assert share.share_text == 'Check out this post!'
        assert share.metadata['hashtags'] == ['#python', '#flask']

    def test_get_user_shares(self, sample_user):
        """Test getting user's social shares."""
        # Create shares on different platforms
        platforms = ['twitter', 'facebook', 'linkedin', 'reddit']
        
        for i, platform in enumerate(platforms):
            SocialShare.create_share(
                user_id=sample_user.id,
                content_type='post',
                content_id=i + 1,
                platform=platform
            )
        
        # Get all shares
        all_shares = SocialShare.get_user_shares(sample_user.id)
        assert len(all_shares) == len(platforms)
        
        # Get shares by platform
        twitter_shares = SocialShare.get_user_shares(sample_user.id, platform='twitter')
        assert len(twitter_shares) == 1
        assert twitter_shares[0].platform == 'twitter'

    def test_content_types(self, sample_user):
        """Test different content types."""
        content_types = ['post', 'comment', 'profile']
        
        for i, content_type in enumerate(content_types):
            SocialShare.create_share(
                user_id=sample_user.id,
                content_type=content_type,
                content_id=i + 1,
                platform='twitter'
            )
        
        # Get shares by content type
        post_shares = SocialShare.get_user_shares(sample_user.id, content_type='post')
        comment_shares = SocialShare.get_user_shares(sample_user.id, content_type='comment')
        profile_shares = SocialShare.get_user_shares(sample_user.id, content_type='profile')
        
        assert len(post_shares) == 1
        assert len(comment_shares) == 1
        assert len(profile_shares) == 1

    def test_share_platforms(self, sample_user):
        """Test different sharing platforms."""
        platforms = ['twitter', 'facebook', 'linkedin', 'reddit', 'whatsapp', 'telegram', 'email']
        
        for platform in platforms:
            SocialShare.create_share(
                user_id=sample_user.id,
                content_type='post',
                content_id=1,
                platform=platform
            )
        
        # Get shares for each platform
        for platform in platforms:
            shares = SocialShare.get_user_shares(sample_user.id, platform=platform)
            assert len(shares) == 1
            assert shares[0].platform == platform

    def test_share_metadata(self, sample_user):
        """Test share metadata handling."""
        metadata = {
            'hashtags': ['#python', '#flask', '#webdev'],
            'mentions': ['@user1', '@user2'],
            'images': 3,
            'links': ['https://example.com']
        }
        
        share = SocialShare.create_share(
            user_id=sample_user.id,
            content_type='post',
            content_id=1,
            platform='twitter',
            metadata=metadata
        )
        
        assert share.metadata['hashtags'] == ['#python', '#flask', '#webdev']
        assert share.metadata['mentions'] == ['@user1', '@user2']
        assert share.metadata['images'] == 3
        assert share.metadata['links'] == ['https://example.com']


class TestSocialFeaturesIntegration:
    """Integration tests for social features."""

    def test_complete_social_workflow(self, sample_user, sample_admin_user):
        """Test complete social workflow."""
        # Follow relationship
        follow = UserFollow.follow_user(sample_user.id, sample_admin_user.id)
        assert follow is not None
        
        # Friend request
        friend_request = UserFriend.send_friend_request(
            sample_user.id, sample_admin_user.id, sample_user.id
        )
        assert friend_request is not None
        
        # Accept friend request
        UserFriend.accept_friend_request(friend_request.id, sample_admin_user.id)
        assert UserFriend.are_friends(sample_user.id, sample_admin_user.id) is True
        
        # Create group
        group = UserGroup.create_group(
            name='Test Group',
            creator_id=sample_user.id
        )
        assert group is not None
        
        # Add friend to group
        group.add_member(sample_admin_user.id)
        assert group.is_member(sample_admin_user.id) is True
        
        # Create activity
        activity = SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='group_join',
            action='joined',
            target_type='group',
            target_id=group.id
        )
        assert activity is not None
        
        # Create recommendation
        recommendation = UserRecommendation.create_recommendation(
            user_id=sample_admin_user.id,
            recommended_user_id=sample_user.id,
            recommendation_type='follow',
            score=0.8
        )
        assert recommendation is not None
        
        # Create share
        share = SocialShare.create_share(
            user_id=sample_user.id,
            content_type='group',
            content_id=group.id,
            platform='twitter'
        )
        assert share is not None

    def test_social_performance(self, sample_user, sample_admin_user):
        """Test performance of social operations."""
        import time
        
        start_time = time.time()
        
        # Create multiple social objects
        for i in range(100):
            UserFollow.follow_user(sample_user.id, sample_admin_user.id + i if i > 0 else sample_admin_user.id)
            SocialActivity.create_activity(
                user_id=sample_user.id,
                activity_type='test',
                action='created',
                target_type='test',
                target_id=i
            )
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Should complete 200 operations in reasonable time
        assert operation_time < 2.0, f"Operations took too long: {operation_time}s"

    def test_social_edge_cases(self, sample_user):
        """Test edge cases in social features."""
        # Test with None values
        activity = SocialActivity.create_activity(
            user_id=sample_user.id,
            activity_type='test',
            action='created',
            target_type=None,
            target_id=None,
            metadata=None
        )
        assert activity is not None
        assert activity.target_type is None
        assert activity.target_id is None
        assert activity.metadata is None
        
        # Test with empty strings
        share = SocialShare.create_share(
            user_id=sample_user.id,
            content_type='',
            content_id=0,
            platform='',
            share_text=''
        )
        assert share is not None
        assert share.content_type == ''
        assert share.content_id == 0
        assert share.platform == ''
        assert share.share_text == ''
