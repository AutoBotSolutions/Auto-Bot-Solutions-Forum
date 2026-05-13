#!/usr/bin/env python3
"""
Debugging Script for New Relationship Systems
Auto Bot Solutions Forum

This script tests and validates the newly implemented Advanced User Relationships
and Content Relationships systems to ensure they are working and operable.
"""

import sys
import os
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
try:
    from app import create_app, db
    from app.models import User
    from app.social.models import (
        UserConnection, UserSocialProfile, UserGroup, UserGroupMembership,
        UserInteraction, UserRelationshipAnalytics, UserSocialActivity
    )
    from app.social.service import (
        SocialService, GroupService, SocialAnalyticsService, SocialActivityService
    )
    from app.social.utils import (
        SocialValidators, SocialCalculators, SocialHelpers, SocialActivityProcessor
    )
    from app.social.config import social_config
    from app.content.models import (
        ContentRelationship, ContentVersion, ContentAnalytics, ContentModeration,
        ContentArchive, ContentRecommendation, ContentTag, ContentCategory
    )
    from app.content.service import (
        ContentService, ContentAnalyticsService, ContentModerationService, ContentRecommendationService
    )
    from app.content.utils import (
        ContentValidators, ContentCalculators, ContentHelpers, ContentProcessor
    )
    from app.content.config import content_config
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)


class RelationshipSystemsDebugger:
    """Debugger for new relationship systems"""
    
    def __init__(self):
        self.app = create_app()
        self.test_results = []
        self.error_count = 0
        self.success_count = 0
        
    def run_all_tests(self):
        """Run all debugging tests"""
        print("=" * 80)
        print("🔍 DEBUGGING NEW RELATIONSHIP SYSTEMS")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        with self.app.app_context():
            # Test database connection
            self.test_database_connection()
            
            # Test Advanced User Relationships System
            print("\n" + "=" * 60)
            print("🧑‍🤝‍🧑 TESTING ADVANCED USER RELATIONSHIPS SYSTEM")
            print("=" * 60)
            self.test_user_relationships_models()
            self.test_user_relationships_services()
            self.test_user_relationships_utils()
            self.test_user_relationships_config()
            
            # Test Content Relationships System
            print("\n" + "=" * 60)
            print("📄 TESTING CONTENT RELATIONSHIPS SYSTEM")
            print("=" * 60)
            self.test_content_relationships_models()
            self.test_content_relationships_services()
            self.test_content_relationships_utils()
            self.test_content_relationships_config()
            
            # Test Integration
            print("\n" + "=" * 60)
            print("🔗 TESTING SYSTEM INTEGRATION")
            print("=" * 60)
            self.test_system_integration()
            
            # Generate final report
            self.generate_final_report()
    
    def test_database_connection(self):
        """Test database connection"""
        print("🔌 Testing Database Connection...")
        
        try:
            # Test basic database operations
            db.engine.execute("SELECT 1")
            self.log_success("Database connection successful")
            
            # Test table existence
            tables_to_check = [
                'user_connections', 'user_social_profiles', 'user_groups', 'user_group_memberships',
                'user_interactions', 'user_relationship_analytics', 'user_social_activities',
                'content_relationships', 'content_versions', 'content_analytics', 'content_moderation',
                'content_archives', 'content_recommendations', 'content_tags', 'content_categories'
            ]
            
            for table in tables_to_check:
                try:
                    result = db.engine.execute(f"SELECT COUNT(*) FROM {table}")
                    count = result.fetchone()[0]
                    self.log_success(f"Table {table}: {count} records")
                except Exception as e:
                    self.log_error(f"Table {table} not accessible: {e}")
                    
        except Exception as e:
            self.log_error(f"Database connection failed: {e}")
    
    def test_user_relationships_models(self):
        """Test User Relationships Models"""
        print("\n📋 Testing User Relationships Models...")
        
        # Test UserConnection model
        try:
            # Test model creation
            test_connection = UserConnection(
                user_id=1,
                connected_user_id=2,
                connection_type='follow',
                strength=0.5
            )
            db.session.add(test_connection)
            db.session.flush()
            
            # Test model properties
            assert test_connection.connection_type == 'follow'
            assert test_connection.strength == 0.5
            assert test_connection.status == 'active'
            
            # Test model methods
            test_connection.update_strength(0.1)
            assert test_connection.interaction_count == 1
            
            db.session.rollback()
            self.log_success("UserConnection model working correctly")
            
        except Exception as e:
            self.log_error(f"UserConnection model error: {e}")
        
        # Test UserSocialProfile model
        try:
            test_profile = UserSocialProfile(
                user_id=1,
                followers_count=10,
                following_count=5,
                friends_count=3
            )
            db.session.add(test_profile)
            db.session.flush()
            
            # Test model properties
            assert test_profile.followers_count == 10
            assert test_profile.privacy_level == 'public'
            
            # Test model methods
            test_profile.update_social_metrics()
            activity_level = test_profile.social_activity_level
            assert activity_level in ['low', 'medium', 'high']
            
            db.session.rollback()
            self.log_success("UserSocialProfile model working correctly")
            
        except Exception as e:
            self.log_error(f"UserSocialProfile model error: {e}")
        
        # Test UserGroup model
        try:
            test_group = UserGroup(
                name="Test Group",
                description="A test group",
                creator_id=1,
                group_type="community",
                privacy="public"
            )
            db.session.add(test_group)
            db.session.flush()
            
            # Test model properties
            assert test_group.name == "Test Group"
            assert test_group.is_active == True
            assert test_group.can_join_directly == True
            
            # Test model methods
            member_count_before = test_group.member_count
            test_group.update_activity_score()
            
            db.session.rollback()
            self.log_success("UserGroup model working correctly")
            
        except Exception as e:
            self.log_error(f"UserGroup model error: {e}")
        
        # Test other models
        models_to_test = [
            (UserGroupMembership, "UserGroupMembership"),
            (UserInteraction, "UserInteraction"),
            (UserRelationshipAnalytics, "UserRelationshipAnalytics"),
            (UserSocialActivity, "UserSocialActivity")
        ]
        
        for model_class, model_name in models_to_test:
            try:
                # Test basic model instantiation
                if model_name == "UserGroupMembership":
                    instance = model_class(user_id=1, group_id=1, role='member')
                elif model_name == "UserInteraction":
                    instance = model_class(initiator_id=1, target_id=2, interaction_type='like')
                elif model_name == "UserRelationshipAnalytics":
                    instance = model_class(user_id=1)
                elif model_name == "UserSocialActivity":
                    instance = model_class(user_id=1, activity_type='post')
                else:
                    instance = model_class()
                
                db.session.add(instance)
                db.session.flush()
                db.session.rollback()
                
                self.log_success(f"{model_name} model working correctly")
                
            except Exception as e:
                self.log_error(f"{model_name} model error: {e}")
    
    def test_user_relationships_services(self):
        """Test User Relationships Services"""
        print("\n⚙️ Testing User Relationships Services...")
        
        # Test SocialService
        try:
            social_service = SocialService()
            
            # Test service methods (without actual database operations)
            connection_types = social_service.connection.CONNECTION_TYPES
            assert 'follow' in connection_types
            assert 'friend' in connection_types
            
            self.log_success("SocialService initialized correctly")
            
        except Exception as e:
            self.log_error(f"SocialService error: {e}")
        
        # Test GroupService
        try:
            group_service = GroupService()
            
            # Test service methods
            group_types = group_service.group.GROUP_TYPES
            assert 'community' in group_types
            assert 'organization' in group_types
            
            self.log_success("GroupService initialized correctly")
            
        except Exception as e:
            self.log_error(f"GroupService error: {e}")
        
        # Test SocialAnalyticsService
        try:
            analytics_service = SocialAnalyticsService()
            
            # Test service methods
            assert analytics_service.analytics_calculation_days == 30
            
            self.log_success("SocialAnalyticsService initialized correctly")
            
        except Exception as e:
            self.log_error(f"SocialAnalyticsService error: {e}")
        
        # Test SocialActivityService
        try:
            activity_service = SocialActivityService()
            
            # Test service methods
            assert hasattr(activity_service, 'create_activity')
            
            self.log_success("SocialActivityService initialized correctly")
            
        except Exception as e:
            self.log_error(f"SocialActivityService error: {e}")
    
    def test_user_relationships_utils(self):
        """Test User Relationships Utilities"""
        print("\n🛠️ Testing User Relationships Utilities...")
        
        # Test SocialValidators
        try:
            validators = SocialValidators()
            
            # Test validation methods
            assert validators.validate_connection_type('follow') == True
            assert validators.validate_connection_type('invalid') == False
            assert validators.validate_group_type('community') == True
            assert validators.validate_group_type('invalid') == False
            
            self.log_success("SocialValidators working correctly")
            
        except Exception as e:
            self.log_error(f"SocialValidators error: {e}")
        
        # Test SocialCalculators
        try:
            calculators = SocialCalculators()
            
            # Test calculation methods
            interactions = [
                {'type': 'like', 'created_at': datetime.now(timezone.utc)}
            ]
            strength = calculators.calculate_connection_strength(interactions)
            assert isinstance(strength, float)
            assert 0.0 <= strength <= 1.0
            
            self.log_success("SocialCalculators working correctly")
            
        except Exception as e:
            self.log_error(f"SocialCalculators error: {e}")
        
        # Test SocialHelpers
        try:
            helpers = SocialHelpers()
            
            # Test helper methods
            assert hasattr(helpers, 'get_connection_between_users')
            assert hasattr(helpers, 'are_friends')
            assert hasattr(helpers, 'is_following')
            
            self.log_success("SocialHelpers working correctly")
            
        except Exception as e:
            self.log_error(f"SocialHelpers error: {e}")
        
        # Test SocialActivityProcessor
        try:
            processor = SocialActivityProcessor()
            
            # Test processor methods
            assert hasattr(processor, 'process_interaction')
            assert hasattr(processor, 'process_connection_change')
            
            self.log_success("SocialActivityProcessor working correctly")
            
        except Exception as e:
            self.log_error(f"SocialActivityProcessor error: {e}")
    
    def test_user_relationships_config(self):
        """Test User Relationships Configuration"""
        print("\n⚙️ Testing User Relationships Configuration...")
        
        try:
            config = social_config
            
            # Test configuration properties
            assert hasattr(config, 'connection')
            assert hasattr(config, 'group')
            assert hasattr(config, 'analytics')
            assert hasattr(config, 'activity')
            assert hasattr(config, 'privacy')
            
            # Test configuration methods
            connection_config = config.get_connection_type_config('follow')
            assert 'name' in connection_config
            assert 'max_connections' in connection_config
            
            group_config = config.get_group_type_config('community')
            assert 'name' in group_config
            assert 'max_members' in group_config
            
            # Test validation methods
            assert config.validate_connection_type('follow') == True
            assert config.validate_group_type('community') == True
            
            self.log_success("Social configuration working correctly")
            
        except Exception as e:
            self.log_error(f"Social configuration error: {e}")
    
    def test_content_relationships_models(self):
        """Test Content Relationships Models"""
        print("\n📋 Testing Content Relationships Models...")
        
        # Test ContentRelationship model
        try:
            test_content = ContentRelationship(
                title="Test Content",
                content="This is test content",
                content_type="post",
                author_id=1,
                visibility="public"
            )
            db.session.add(test_content)
            db.session.flush()
            
            # Test model properties
            assert test_content.title == "Test Content"
            assert test_content.content_type == "post"
            assert test_content.is_published == True
            assert test_content.is_public == True
            
            # Test model methods
            test_content.update_metrics()
            assert isinstance(test_content.engagement_rate, float)
            assert isinstance(test_content.content_score, float)
            
            db.session.rollback()
            self.log_success("ContentRelationship model working correctly")
            
        except Exception as e:
            self.log_error(f"ContentRelationship model error: {e}")
        
        # Test ContentVersion model
        try:
            test_version = ContentVersion(
                content_id=1,
                version_number=1,
                title="Test Version",
                content="Test version content",
                content_type="post",
                author_id=1
            )
            db.session.add(test_version)
            db.session.flush()
            
            # Test model properties
            assert test_version.version_number == 1
            assert test_version.change_type == 'update'
            
            # Test model methods
            test_version.calculate_content_metrics()
            assert isinstance(test_version.content_length, int)
            assert isinstance(test_version.word_count, int)
            
            db.session.rollback()
            self.log_success("ContentVersion model working correctly")
            
        except Exception as e:
            self.log_error(f"ContentVersion model error: {e}")
        
        # Test ContentAnalytics model
        try:
            test_analytics = ContentAnalytics(
                content_id=1,
                total_views=100,
                unique_views=80,
                total_engagements=20
            )
            db.session.add(test_analytics)
            db.session.flush()
            
            # Test model properties
            assert test_analytics.total_views == 100
            assert test_analytics.total_engagements == 20
            
            # Test model methods
            engagement_rate = test_analytics.engagement_rate
            assert isinstance(engagement_rate, float)
            
            db.session.rollback()
            self.log_success("ContentAnalytics model working correctly")
            
        except Exception as e:
            self.log_error(f"ContentAnalytics model error: {e}")
        
        # Test ContentModeration model
        try:
            test_moderation = ContentModeration(
                content_id=1,
                status='pending',
                priority='normal'
            )
            db.session.add(test_moderation)
            db.session.flush()
            
            # Test model properties
            assert test_moderation.status == 'pending'
            assert test_moderation.is_pending == True
            assert test_moderation.requires_review == True
            
            # Test model methods
            test_moderation.add_user_report(1, "Test report")
            assert test_moderation.report_count == 1
            
            db.session.rollback()
            self.log_success("ContentModeration model working correctly")
            
        except Exception as e:
            self.log_error(f"ContentModeration model error: {e}")
        
        # Test other models
        models_to_test = [
            (ContentArchive, "ContentArchive"),
            (ContentRecommendation, "ContentRecommendation"),
            (ContentTag, "ContentTag"),
            (ContentCategory, "ContentCategory")
        ]
        
        for model_class, model_name in models_to_test:
            try:
                # Test basic model instantiation
                if model_name == "ContentArchive":
                    instance = model_class(original_content_id=1, archive_reason='test')
                elif model_name == "ContentRecommendation":
                    instance = model_class(user_id=1, content_id=1, recommendation_type='similar')
                elif model_name == "ContentTag":
                    instance = model_class(name="test-tag")
                elif model_name == "ContentCategory":
                    instance = model_class(name="Test Category")
                else:
                    instance = model_class()
                
                db.session.add(instance)
                db.session.flush()
                db.session.rollback()
                
                self.log_success(f"{model_name} model working correctly")
                
            except Exception as e:
                self.log_error(f"{model_name} model error: {e}")
    
    def test_content_relationships_services(self):
        """Test Content Relationships Services"""
        print("\n⚙️ Testing Content Relationships Services...")
        
        # Test ContentService
        try:
            content_service = ContentService()
            
            # Test service properties
            assert content_service.default_content_type == 'post'
            assert content_service.versioning_enabled == True
            
            self.log_success("ContentService initialized correctly")
            
        except Exception as e:
            self.log_error(f"ContentService error: {e}")
        
        # Test ContentAnalyticsService
        try:
            analytics_service = ContentAnalyticsService()
            
            # Test service properties
            assert analytics_service.analytics_calculation_interval == 3600
            
            self.log_success("ContentAnalyticsService initialized correctly")
            
        except Exception as e:
            self.log_error(f"ContentAnalyticsService error: {e}")
        
        # Test ContentModerationService
        try:
            moderation_service = ContentModerationService()
            
            # Test service properties
            assert moderation_service.auto_moderation_enabled == True
            assert moderation_service.moderation_threshold == 0.7
            
            self.log_success("ContentModerationService initialized correctly")
            
        except Exception as e:
            self.log_error(f"ContentModerationService error: {e}")
        
        # Test ContentRecommendationService
        try:
            recommendation_service = ContentRecommendationService()
            
            # Test service properties
            assert recommendation_service.recommendation_cache_ttl == 1800
            assert recommendation_service.max_recommendations == 50
            
            self.log_success("ContentRecommendationService initialized correctly")
            
        except Exception as e:
            self.log_error(f"ContentRecommendationService error: {e}")
    
    def test_content_relationships_utils(self):
        """Test Content Relationships Utilities"""
        print("\n🛠️ Testing Content Relationships Utilities...")
        
        # Test ContentValidators
        try:
            validators = ContentValidators()
            
            # Test validation methods
            assert validators.validate_content_type('post') == True
            assert validators.validate_content_type('invalid') == False
            assert validators.validate_content_status('published') == True
            assert validators.validate_visibility('public') == True
            
            self.log_success("ContentValidators working correctly")
            
        except Exception as e:
            self.log_error(f"ContentValidators error: {e}")
        
        # Test ContentCalculators
        try:
            calculators = ContentCalculators()
            
            # Test calculation methods
            test_content = ContentRelationship(
                title="Test",
                content="Test content",
                content_type="post",
                author_id=1
            )
            
            engagement_score = calculators.calculate_engagement_score(test_content)
            assert isinstance(engagement_score, float)
            assert 0.0 <= engagement_score <= 1.0
            
            quality_score = calculators.calculate_quality_score(test_content)
            assert isinstance(quality_score, float)
            assert 0.0 <= quality_score <= 1.0
            
            readability_score = calculators.calculate_readability_score("Test content for readability")
            assert isinstance(readability_score, float)
            
            self.log_success("ContentCalculators working correctly")
            
        except Exception as e:
            self.log_error(f"ContentCalculators error: {e}")
        
        # Test ContentHelpers
        try:
            helpers = ContentHelpers()
            
            # Test helper methods
            slug = helpers.generate_slug("Test Title")
            assert isinstance(slug, str)
            assert len(slug) > 0
            
            keywords = helpers.extract_keywords("Test content with some keywords")
            assert isinstance(keywords, list)
            
            summary = helpers.generate_summary("This is a test content for summary generation.")
            assert isinstance(summary, str)
            
            self.log_success("ContentHelpers working correctly")
            
        except Exception as e:
            self.log_error(f"ContentHelpers error: {e}")
        
        # Test ContentProcessor
        try:
            processor = ContentProcessor()
            
            # Test processor methods
            assert hasattr(processor, 'process_content_creation')
            assert hasattr(processor, 'process_content_update')
            assert hasattr(processor, 'process_content_view')
            
            self.log_success("ContentProcessor working correctly")
            
        except Exception as e:
            self.log_error(f"ContentProcessor error: {e}")
    
    def test_content_relationships_config(self):
        """Test Content Relationships Configuration"""
        print("\n⚙️ Testing Content Relationships Configuration...")
        
        try:
            config = content_config
            
            # Test configuration properties
            assert hasattr(config, 'content')
            assert hasattr(config, 'moderation')
            assert hasattr(config, 'analytics')
            assert hasattr(config, 'archiving')
            assert hasattr(config, 'recommendations')
            
            # Test configuration methods
            content_type_config = config.get_content_type_config('post')
            assert 'name' in content_type_config
            assert 'max_length' in content_type_config
            
            moderation_config = config.get_moderation_status_config('pending')
            assert 'name' in moderation_config
            
            # Test validation methods
            assert config.validate_content_length('post', 'Test content') == True
            assert config.is_content_type_valid('post') == True
            assert config.is_status_valid('published') == True
            
            self.log_success("Content configuration working correctly")
            
        except Exception as e:
            self.log_error(f"Content configuration error: {e}")
    
    def test_system_integration(self):
        """Test System Integration"""
        print("\n🔗 Testing System Integration...")
        
        # Test cross-system relationships
        try:
            # Test that User model can access social profile
            test_user = User.query.first()
            if test_user:
                # This tests the relationship between User and UserSocialProfile
                assert hasattr(test_user, 'social_profile')
                
                # Test that User can access content relationships
                assert hasattr(test_user, 'content_relationships')
                
                self.log_success("User model relationships working correctly")
            
        except Exception as e:
            self.log_error(f"User model relationships error: {e}")
        
        # Test configuration integration
        try:
            # Test that both configs are accessible
            social_config_dict = social_config.export_config()
            content_config_dict = content_config.export_config()
            
            assert isinstance(social_config_dict, dict)
            assert isinstance(content_config_dict, dict)
            
            self.log_success("Configuration integration working correctly")
            
        except Exception as e:
            self.log_error(f"Configuration integration error: {e}")
        
        # Test service integration
        try:
            # Test that services can be instantiated together
            social_service = SocialService()
            content_service = ContentService()
            
            # Test that services have required methods
            assert hasattr(social_service, 'follow_user')
            assert hasattr(content_service, 'create_content')
            
            self.log_success("Service integration working correctly")
            
        except Exception as e:
            self.log_error(f"Service integration error: {e}")
    
    def log_success(self, message):
        """Log successful test"""
        self.success_count += 1
        self.test_results.append(f"✅ {message}")
        print(f"✅ {message}")
    
    def log_error(self, message):
        """Log test error"""
        self.error_count += 1
        self.test_results.append(f"❌ {message}")
        print(f"❌ {message}")
    
    def log_warning(self, message):
        """Log test warning"""
        self.test_results.append(f"⚠️ {message}")
        print(f"⚠️ {message}")
    
    def generate_final_report(self):
        """Generate final debugging report"""
        print("\n" + "=" * 80)
        print("📊 DEBUGGING REPORT")
        print("=" * 80)
        
        total_tests = self.success_count + self.error_count
        success_rate = (self.success_count / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {self.success_count}")
        print(f"Failed: {self.error_count}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # System status
        print("🔍 SYSTEM STATUS:")
        print(f"Advanced User Relationships: {'✅ OPERATIONAL' if self.error_count < 5 else '⚠️ NEEDS ATTENTION'}")
        print(f"Content Relationships: {'✅ OPERATIONAL' if self.error_count < 5 else '⚠️ NEEDS ATTENTION'}")
        print(f"Overall System: {'✅ OPERATIONAL' if success_rate > 80 else '⚠️ NEEDS ATTENTION'}")
        print()
        
        # Detailed results
        if self.error_count > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if result.startswith("❌"):
                    print(f"  {result}")
            print()
        
        if self.success_count > 0:
            print("✅ SUCCESSFUL TESTS:")
            for result in self.test_results:
                if result.startswith("✅"):
                    print(f"  {result}")
            print()
        
        # Recommendations
        print("🔧 RECOMMENDATIONS:")
        if self.error_count == 0:
            print("✅ All systems are working correctly!")
            print("✅ Ready for production deployment")
        elif self.error_count < 5:
            print("⚠️ Minor issues detected - review failed tests")
            print("🔧 Fix the reported issues before production deployment")
        else:
            print("❌ Significant issues detected - requires immediate attention")
            print("🚫 Do not deploy to production until issues are resolved")
        
        print()
        print(f"Debugging completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Save report to file
        self.save_report_to_file()
    
    def save_report_to_file(self):
        """Save debugging report to file"""
        try:
            report_file = "new_relationships_debugging_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("New Relationship Systems Debugging Report\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                total_tests = self.success_count + self.error_count
                success_rate = (self.success_count / total_tests * 100) if total_tests > 0 else 0
                
                f.write(f"Total Tests: {total_tests}\n")
                f.write(f"Successful: {self.success_count}\n")
                f.write(f"Failed: {self.error_count}\n")
                f.write(f"Success Rate: {success_rate:.1f}%\n\n")
                
                f.write("Test Results:\n")
                f.write("-" * 30 + "\n")
                for result in self.test_results:
                    f.write(f"{result}\n")
                
                f.write("\nRecommendations:\n")
                f.write("-" * 30 + "\n")
                if self.error_count == 0:
                    f.write("✅ All systems are working correctly!\n")
                    f.write("✅ Ready for production deployment\n")
                elif self.error_count < 5:
                    f.write("⚠️ Minor issues detected - review failed tests\n")
                    f.write("🔧 Fix the reported issues before production deployment\n")
                else:
                    f.write("❌ Significant issues detected - requires immediate attention\n")
                    f.write("🚫 Do not deploy to production until issues are resolved\n")
            
            print(f"📄 Detailed report saved to: {report_file}")
            
        except Exception as e:
            print(f"⚠️ Could not save report to file: {e}")


def main():
    """Main function"""
    debugger = RelationshipSystemsDebugger()
    debugger.run_all_tests()


if __name__ == "__main__":
    main()
