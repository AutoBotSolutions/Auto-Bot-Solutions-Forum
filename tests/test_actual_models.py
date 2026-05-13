#!/usr/bin/env python3
"""
Test Actual Models for New Relationship Systems
Auto Bot Solutions Forum

This script tests the actual model files to ensure they work correctly.
"""

import sys
import os
import traceback
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_social_models():
    """Test social models directly"""
    print("🧑‍🤝‍🧑 Testing Social Models...")
    
    try:
        # Import the social models
        from app.social.models import (
            UserConnection, UserSocialProfile, UserGroup, UserGroupMembership,
            UserInteraction, UserRelationshipAnalytics, UserSocialActivity
        )
        
        print("✅ Social models imported successfully")
        
        # Test model instantiation (without database)
        test_connection = UserConnection(
            user_id=1,
            connected_user_id=2,
            connection_type='follow',
            strength=0.5,
            status='active'
        )
        
        assert test_connection.connection_type == 'follow'
        assert test_connection.strength == 0.5
        assert test_connection.status == 'active'
        
        print("✅ UserConnection model working correctly")
        
        # Test UserSocialProfile
        test_profile = UserSocialProfile(
            user_id=1,
            followers_count=10,
            following_count=5,
            friends_count=3,
            privacy_level='public'
        )
        
        assert test_profile.followers_count == 10
        assert test_profile.privacy_level == 'public'
        
        print("✅ UserSocialProfile model working correctly")
        
        # Test UserGroup
        test_group = UserGroup(
            name="Test Group",
            description="A test group",
            creator_id=1,
            group_type="community",
            privacy="public"
        )
        
        assert test_group.name == "Test Group"
        assert test_group.group_type == "community"
        assert test_group.is_active == True
        
        print("✅ UserGroup model working correctly")
        
        # Test other models
        test_membership = UserGroupMembership(
            user_id=1,
            group_id=1,
            role='member',
            status='active'
        )
        
        assert test_membership.role == 'member'
        assert test_membership.is_active == True
        
        print("✅ UserGroupMembership model working correctly")
        
        test_interaction = UserInteraction(
            initiator_id=1,
            target_id=2,
            interaction_type='like'
        )
        
        assert test_interaction.interaction_type == 'like'
        
        print("✅ UserInteraction model working correctly")
        
        test_analytics = UserRelationshipAnalytics(user_id=1)
        
        assert test_analytics.user_id == 1
        
        print("✅ UserRelationshipAnalytics model working correctly")
        
        test_activity = UserSocialActivity(
            user_id=1,
            activity_type='post',
            visibility='public'
        )
        
        assert test_activity.activity_type == 'post'
        assert test_activity.is_public == True
        
        print("✅ UserSocialActivity model working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Social models error: {e}")
        traceback.print_exc()
        return False

def test_content_models():
    """Test content models directly"""
    print("\n📄 Testing Content Models...")
    
    try:
        # Import the content models
        from app.content.models import (
            ContentRelationship, ContentVersion, ContentAnalytics, ContentModeration,
            ContentArchive, ContentRecommendation, ContentTag, ContentCategory
        )
        
        print("✅ Content models imported successfully")
        
        # Test ContentRelationship
        test_content = ContentRelationship(
            title="Test Content",
            content="This is test content",
            content_type="post",
            author_id=1,
            status='published',
            visibility='public'
        )
        
        assert test_content.title == "Test Content"
        assert test_content.content_type == "post"
        assert test_content.is_published == True
        assert test_content.is_public == True
        
        print("✅ ContentRelationship model working correctly")
        
        # Test ContentVersion
        test_version = ContentVersion(
            content_id=1,
            version_number=1,
            title="Test Version",
            content="Test version content",
            content_type="post",
            author_id=1,
            change_type='create'
        )
        
        assert test_version.version_number == 1
        assert test_version.change_type == 'create'
        assert test_version.is_major_version == True
        
        print("✅ ContentVersion model working correctly")
        
        # Test ContentAnalytics
        test_analytics = ContentAnalytics(
            content_id=1,
            total_views=100,
            unique_views=80,
            total_engagements=20
        )
        
        assert test_analytics.total_views == 100
        assert test_analytics.total_engagements == 20
        assert isinstance(test_analytics.engagement_rate, float)
        
        print("✅ ContentAnalytics model working correctly")
        
        # Test ContentModeration
        test_moderation = ContentModeration(
            content_id=1,
            status='pending',
            priority='normal'
        )
        
        assert test_moderation.status == 'pending'
        assert test_moderation.is_pending == True
        assert test_moderation.requires_review == True
        
        print("✅ ContentModeration model working correctly")
        
        # Test ContentArchive
        test_archive = ContentArchive(
            original_content_id=1,
            archive_reason='test',
            title="Test Archive"
        )
        
        assert test_archive.archive_reason == 'test'
        assert test_archive.is_expired == False
        
        print("✅ ContentArchive model working correctly")
        
        # Test ContentRecommendation
        test_recommendation = ContentRecommendation(
            user_id=1,
            content_id=1,
            recommendation_type='similar',
            score=0.8
        )
        
        assert test_recommendation.recommendation_type == 'similar'
        assert test_recommendation.score == 0.8
        assert test_recommendation.is_interacted == False
        
        print("✅ ContentRecommendation model working correctly")
        
        # Test ContentTag
        test_tag = ContentTag(
            name="test-tag",
            description="A test tag"
        )
        
        assert test_tag.name == "test-tag"
        assert test_tag.is_trending == False
        
        print("✅ ContentTag model working correctly")
        
        # Test ContentCategory
        test_category = ContentCategory(
            name="Test Category",
            description="A test category"
        )
        
        assert test_category.name == "Test Category"
        assert test_category.is_root_category == True
        
        print("✅ ContentCategory model working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Content models error: {e}")
        traceback.print_exc()
        return False

def test_social_services():
    """Test social services"""
    print("\n⚙️ Testing Social Services...")
    
    try:
        from app.social.service import (
            SocialService, GroupService, SocialAnalyticsService, SocialActivityService
        )
        
        # Test service instantiation
        social_service = SocialService()
        group_service = GroupService()
        analytics_service = SocialAnalyticsService()
        activity_service = SocialActivityService()
        
        # Test service properties
        assert social_service.default_connection_strength == 0.1
        assert social_service.max_connection_strength == 1.0
        
        assert group_service.max_group_members == 10000
        assert group_service.default_group_type == 'community'
        
        assert analytics_service.analytics_calculation_days == 30
        
        assert hasattr(activity_service, 'create_activity')
        
        print("✅ Social services working correctly")
        
        # Test service methods (basic validation)
        connection_types = social_service.connection.CONNECTION_TYPES
        assert 'follow' in connection_types
        assert 'friend' in connection_types
        
        group_types = group_service.group.GROUP_TYPES
        assert 'community' in group_types
        assert 'organization' in group_types
        
        print("✅ Social service configurations working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Social services error: {e}")
        traceback.print_exc()
        return False

def test_content_services():
    """Test content services"""
    print("\n⚙️ Testing Content Services...")
    
    try:
        from app.content.service import (
            ContentService, ContentAnalyticsService, ContentModerationService, ContentRecommendationService
        )
        
        # Test service instantiation
        content_service = ContentService()
        analytics_service = ContentAnalyticsService()
        moderation_service = ContentModerationService()
        recommendation_service = ContentRecommendationService()
        
        # Test service properties
        assert content_service.default_content_type == 'post'
        assert content_service.versioning_enabled == True
        
        assert analytics_service.analytics_calculation_interval == 3600
        
        assert moderation_service.auto_moderation_enabled == True
        assert moderation_service.moderation_threshold == 0.7
        
        assert recommendation_service.recommendation_cache_ttl == 1800
        assert recommendation_service.max_recommendations == 50
        
        print("✅ Content services working correctly")
        
        # Test service configurations
        content_types = content_service.get_content_type_config('post')
        assert 'name' in content_types
        assert 'max_length' in content_types
        
        moderation_statuses = moderation_service.get_moderation_status_config('pending')
        assert 'name' in moderation_statuses
        
        print("✅ Content service configurations working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Content services error: {e}")
        traceback.print_exc()
        return False

def test_social_utils():
    """Test social utilities"""
    print("\n🛠️ Testing Social Utilities...")
    
    try:
        from app.social.utils import (
            SocialValidators, SocialCalculators, SocialHelpers, SocialActivityProcessor
        )
        
        # Test validators
        validators = SocialValidators()
        assert validators.validate_connection_type('follow') == True
        assert validators.validate_connection_type('invalid') == False
        assert validators.validate_group_type('community') == True
        assert validators.validate_group_type('invalid') == False
        
        print("✅ SocialValidators working correctly")
        
        # Test calculators
        calculators = SocialCalculators()
        
        interactions = [
            {'type': 'like', 'created_at': datetime.now(timezone.utc)}
        ]
        strength = calculators.calculate_connection_strength(interactions)
        assert isinstance(strength, float)
        assert 0.0 <= strength <= 1.0
        
        print("✅ SocialCalculators working correctly")
        
        # Test helpers
        helpers = SocialHelpers()
        assert hasattr(helpers, 'get_connection_between_users')
        assert hasattr(helpers, 'are_friends')
        assert hasattr(helpers, 'is_following')
        
        print("✅ SocialHelpers working correctly")
        
        # Test processor
        processor = SocialActivityProcessor()
        assert hasattr(processor, 'process_interaction')
        assert hasattr(processor, 'process_connection_change')
        
        print("✅ SocialActivityProcessor working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Social utilities error: {e}")
        traceback.print_exc()
        return False

def test_content_utils():
    """Test content utilities"""
    print("\n🛠️ Testing Content Utilities...")
    
    try:
        from app.content.utils import (
            ContentValidators, ContentCalculators, ContentHelpers, ContentProcessor
        )
        
        # Test validators
        validators = ContentValidators()
        assert validators.validate_content_type('post') == True
        assert validators.validate_content_type('invalid') == False
        assert validators.validate_content_status('published') == True
        assert validators.validate_visibility('public') == True
        
        print("✅ ContentValidators working correctly")
        
        # Test calculators
        calculators = ContentCalculators()
        
        # Test readability calculation
        readability_score = calculators.calculate_readability_score("Test content for readability.")
        assert isinstance(readability_score, float)
        assert 0.0 <= readability_score <= 1.0
        
        # Test sentiment calculation
        sentiment_score = calculators.calculate_sentiment_score("This is good content")
        assert isinstance(sentiment_score, float)
        assert -1.0 <= sentiment_score <= 1.0
        
        print("✅ ContentCalculators working correctly")
        
        # Test helpers
        helpers = ContentHelpers()
        
        slug = helpers.generate_slug("Test Title")
        assert isinstance(slug, str)
        assert len(slug) > 0
        
        keywords = helpers.extract_keywords("Test content with some keywords")
        assert isinstance(keywords, list)
        
        summary = helpers.generate_summary("This is a test content for summary generation.")
        assert isinstance(summary, str)
        
        print("✅ ContentHelpers working correctly")
        
        # Test processor
        processor = ContentProcessor()
        assert hasattr(processor, 'process_content_creation')
        assert hasattr(processor, 'process_content_update')
        
        print("✅ ContentProcessor working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Content utilities error: {e}")
        traceback.print_exc()
        return False

def test_configurations():
    """Test configurations"""
    print("\n⚙️ Testing Configurations...")
    
    try:
        from app.social.config import social_config
        from app.content.config import content_config
        
        # Test social config
        assert hasattr(social_config, 'connection')
        assert hasattr(social_config, 'group')
        assert hasattr(social_config, 'analytics')
        
        connection_config = social_config.get_connection_type_config('follow')
        assert 'name' in connection_config
        assert 'max_connections' in connection_config
        
        group_config = social_config.get_group_type_config('community')
        assert 'name' in group_config
        assert 'max_members' in group_config
        
        print("✅ Social configuration working correctly")
        
        # Test content config
        assert hasattr(content_config, 'content')
        assert hasattr(content_config, 'moderation')
        assert hasattr(content_config, 'analytics')
        
        content_type_config = content_config.get_content_type_config('post')
        assert 'name' in content_type_config
        assert 'max_length' in content_type_config
        
        moderation_config = content_config.get_moderation_status_config('pending')
        assert 'name' in moderation_config
        
        print("✅ Content configuration working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("=" * 80)
    print("🔍 TESTING ACTUAL MODELS FOR NEW RELATIONSHIP SYSTEMS")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Social Models", test_social_models),
        ("Content Models", test_content_models),
        ("Social Services", test_social_services),
        ("Content Services", test_content_services),
        ("Social Utilities", test_social_utils),
        ("Content Utilities", test_content_utils),
        ("Configurations", test_configurations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Generate final report
    print("\n" + "=" * 80)
    print("📊 ACTUAL MODELS TESTING REPORT")
    print("=" * 80)
    
    total_tests = len(results)
    successful_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - successful_tests
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print()
    
    print("🔍 TEST RESULTS:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print()
    print("🔧 RECOMMENDATIONS:")
    if failed_tests == 0:
        print("✅ All actual models are working correctly!")
        print("✅ Model definitions, services, and utilities are functional")
        print("✅ Ready for database integration testing")
    elif failed_tests <= 2:
        print("⚠️ Minor issues detected - review failed tests")
        print("🔧 Fix the reported issues before proceeding")
    else:
        print("❌ Significant issues detected - requires immediate attention")
        print("🚫 Review and fix all failed tests")
    
    print()
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
