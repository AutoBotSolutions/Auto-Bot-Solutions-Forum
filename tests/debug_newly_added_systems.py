#!/usr/bin/env python3
"""
Comprehensive Debugging Script for Newly Added Systems

This script debugs all the newly added systems from the completion report:
- Missing database models (UserPreference, UserProfileTheme, UserSocialConnection, UserAnalytics, UserRoleAssignment)
- Missing routes and endpoints
- Missing forms and validation
- Advanced profile features
- Social features
"""

import sys
import os
import traceback
from datetime import datetime, timedelta
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add config directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config'))

def test_imports():
    """Test imports for all newly added systems"""
    print("🔍 Testing imports...")
    
    results = {
        'success': True,
        'imports': {},
        'errors': []
    }
    
    # Test missing database models
    try:
        from app.user.models import UserPreference, UserProfileTheme, UserSocialConnection, UserAnalytics, UserRoleAssignment
        results['imports']['missing_models'] = 'SUCCESS'
        print("✅ Missing database models imported successfully")
    except Exception as e:
        results['imports']['missing_models'] = f'FAILED: {str(e)}'
        results['errors'].append(f"Missing models import error: {e}")
        results['success'] = False
        print(f"❌ Missing database models import failed: {e}")
    
    # Test advanced profile features
    try:
        from app.user.advanced_profile import AdvancedProfileManager, ProfileThemeManager, ProfileAnalyticsManager
        results['imports']['advanced_profile'] = 'SUCCESS'
        print("✅ Advanced profile features imported successfully")
    except Exception as e:
        results['imports']['advanced_profile'] = f'FAILED: {str(e)}'
        results['errors'].append(f"Advanced profile import error: {e}")
        results['success'] = False
        print(f"❌ Advanced profile features import failed: {e}")
    
    # Test social features
    try:
        from app.user.social_features import SocialConnectionManager, SocialFeedManager, UserRecommendationManager
        results['imports']['social_features'] = 'SUCCESS'
        print("✅ Social features imported successfully")
    except Exception as e:
        results['imports']['social_features'] = f'FAILED: {str(e)}'
        results['errors'].append(f"Social features import error: {e}")
        results['success'] = False
        print(f"❌ Social features import failed: {e}")
    
    # Test forms
    try:
        from app.user.forms import UserPreferencesForm, ProfileCustomizationForm, SocialConnectionForm, AnalyticsFilterForm, ProfileVisibilityForm, WidgetManagementForm
        results['imports']['forms'] = 'SUCCESS'
        print("✅ Forms imported successfully")
    except Exception as e:
        results['imports']['forms'] = f'FAILED: {str(e)}'
        results['errors'].append(f"Forms import error: {e}")
        results['success'] = False
        print(f"❌ Forms import failed: {e}")
    
    # Test routes
    try:
        from app.user.routes import user_preferences, profile_customize, follow_user, following, followers, analytics, user_roles, profile_visibility, widgets
        results['imports']['routes'] = 'SUCCESS'
        print("✅ Routes imported successfully")
    except Exception as e:
        results['imports']['routes'] = f'FAILED: {str(e)}'
        results['errors'].append(f"Routes import error: {e}")
        results['success'] = False
        print(f"❌ Routes import failed: {e}")
    
    return results

def test_database_models():
    """Test missing database models functionality"""
    print("\n🔍 Testing database models...")
    
    results = {
        'success': True,
        'models': {},
        'errors': []
    }
    
    try:
        from app import create_app, db
        from app.user.models import UserPreference, UserProfileTheme, UserSocialConnection, UserAnalytics, UserRoleAssignment
        from app.models import User
        from app.admin.roles.models import Role
        
        from testing import TestingConfig
        app = create_app(TestingConfig)
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Test UserPreference model
            try:
                # Create a test user
                user = User(username='testuser', email='test@example.com')
                user.set_password('password123')
                db.session.add(user)
                db.session.commit()
                
                # Test UserPreference
                preference = UserPreference.set_preference(user_id=user.id, preference_type='theme', value='dark')
                retrieved_preference = UserPreference.get_preference(user_id=user.id, preference_type='theme')
                
                if preference and retrieved_preference == 'dark':
                    results['models']['UserPreference'] = 'SUCCESS'
                    print("✅ UserPreference model working correctly")
                else:
                    results['models']['UserPreference'] = 'FAILED: Preference not set/retrieved correctly'
                    results['success'] = False
                    print("❌ UserPreference model failed")
                
                # Test UserProfileTheme
                theme = UserProfileTheme.create_theme(
                    name='test_theme',
                    display_name='Test Theme',
                    css_variables={'primary_color': '#007bff'},
                    layout_config={'columns': 2}
                )
                
                retrieved_theme = UserProfileTheme.get_theme(theme.id)
                if retrieved_theme and retrieved_theme.name == 'test_theme':
                    results['models']['UserProfileTheme'] = 'SUCCESS'
                    print("✅ UserProfileTheme model working correctly")
                else:
                    results['models']['UserProfileTheme'] = 'FAILED: Theme not created/retrieved correctly'
                    results['success'] = False
                    print("❌ UserProfileTheme model failed")
                
                # Test UserSocialConnection
                # Create another user for connection
                other_user = User(username='otheruser', email='other@example.com')
                other_user.set_password('password123')
                db.session.add(other_user)
                db.session.commit()
                
                connection = UserSocialConnection.create_connection(
                    user_id=user.id,
                    connected_user_id=other_user.id,
                    connection_type='follow'
                )
                
                is_connected = UserSocialConnection.is_connected(user.id, other_user.id, 'follow')
                if connection and is_connected:
                    results['models']['UserSocialConnection'] = 'SUCCESS'
                    print("✅ UserSocialConnection model working correctly")
                else:
                    results['models']['UserSocialConnection'] = 'FAILED: Connection not created/checked correctly'
                    results['success'] = False
                    print("❌ UserSocialConnection model failed")
                
                # Test UserAnalytics
                analytics = UserAnalytics.track_metric(
                    user_id=user.id,
                    metric_type='login',
                    value=1,
                    metric_data={'ip_address': '127.0.0.1'}
                )
                
                metrics = UserAnalytics.get_user_metrics(user_id=user.id, metric_type='login')
                if analytics and len(metrics) > 0:
                    results['models']['UserAnalytics'] = 'SUCCESS'
                    print("✅ UserAnalytics model working correctly")
                else:
                    results['models']['UserAnalytics'] = 'FAILED: Analytics not tracked/retrieved correctly'
                    results['success'] = False
                    print("❌ UserAnalytics model failed")
                
                # Test UserRoleAssignment
                role = Role.create_role(
                    name='test_role',
                    display_name='Test Role',
                    description='Test role for debugging'
                )
                
                assignment = UserRoleAssignment.assign_role(
                    user_id=user.id,
                    role_id=role.id,
                    assigned_by_id=user.id
                )
                
                has_role = UserRoleAssignment.has_role(user.id, role.id)
                if assignment and has_role:
                    results['models']['UserRoleAssignment'] = 'SUCCESS'
                    print("✅ UserRoleAssignment model working correctly")
                else:
                    results['models']['UserRoleAssignment'] = 'FAILED: Role not assigned/checked correctly'
                    results['success'] = False
                    print("❌ UserRoleAssignment model failed")
                
            except Exception as e:
                error_msg = f"Database model test error: {str(e)}"
                results['errors'].append(error_msg)
                results['success'] = False
                print(f"❌ Database model test failed: {e}")
                traceback.print_exc()
            
    except Exception as e:
        error_msg = f"Database setup error: {str(e)}"
        results['errors'].append(error_msg)
        results['success'] = False
        print(f"❌ Database setup failed: {e}")
        traceback.print_exc()
    
    return results

def test_forms():
    """Test forms functionality"""
    print("\n🔍 Testing forms...")
    
    results = {
        'success': True,
        'forms': {},
        'errors': []
    }
    
    try:
        from app import create_app
        from app.user.forms import UserPreferencesForm, ProfileCustomizationForm, SocialConnectionForm, AnalyticsFilterForm, ProfileVisibilityForm, WidgetManagementForm
        
        from testing import TestingConfig
        app = create_app(TestingConfig)
        with app.app_context():
            # Test UserPreferencesForm
            try:
                form = UserPreferencesForm()
                form.theme.data = 'dark'
                form.language.data = 'en'
                form.timezone.data = 'UTC'
                
                if form.validate():
                    results['forms']['UserPreferencesForm'] = 'SUCCESS'
                    print("✅ UserPreferencesForm working correctly")
                else:
                    results['forms']['UserPreferencesForm'] = 'FAILED: Form validation failed'
                    results['success'] = False
                    print("❌ UserPreferencesForm validation failed")
            except Exception as e:
                results['forms']['UserPreferencesForm'] = f'FAILED: {str(e)}'
                results['errors'].append(f"UserPreferencesForm error: {e}")
                results['success'] = False
                print(f"❌ UserPreferencesForm failed: {e}")
            
            # Test ProfileCustomizationForm
            try:
                form = ProfileCustomizationForm()
                form.layout.data = 'grid'
                form.privacy.data = 'public'
                
                if form.validate():
                    results['forms']['ProfileCustomizationForm'] = 'SUCCESS'
                    print("✅ ProfileCustomizationForm working correctly")
                else:
                    results['forms']['ProfileCustomizationForm'] = 'FAILED: Form validation failed'
                    results['success'] = False
                    print("❌ ProfileCustomizationForm validation failed")
            except Exception as e:
                results['forms']['ProfileCustomizationForm'] = f'FAILED: {str(e)}'
                results['errors'].append(f"ProfileCustomizationForm error: {e}")
                results['success'] = False
                print(f"❌ ProfileCustomizationForm failed: {e}")
            
            # Test SocialConnectionForm
            try:
                form = SocialConnectionForm()
                form.connection_type.data = 'follow'
                form.privacy_settings.data = 'public'
                
                if form.validate():
                    results['forms']['SocialConnectionForm'] = 'SUCCESS'
                    print("✅ SocialConnectionForm working correctly")
                else:
                    results['forms']['SocialConnectionForm'] = 'FAILED: Form validation failed'
                    results['success'] = False
                    print("❌ SocialConnectionForm validation failed")
            except Exception as e:
                results['forms']['SocialConnectionForm'] = f'FAILED: {str(e)}'
                results['errors'].append(f"SocialConnectionForm error: {e}")
                results['success'] = False
                print(f"❌ SocialConnectionForm failed: {e}")
            
            # Test AnalyticsFilterForm
            try:
                form = AnalyticsFilterForm()
                form.date_range.data = '7d'
                form.metric_type.data = 'all'
                
                if form.validate():
                    results['forms']['AnalyticsFilterForm'] = 'SUCCESS'
                    print("✅ AnalyticsFilterForm working correctly")
                else:
                    results['forms']['AnalyticsFilterForm'] = 'FAILED: Form validation failed'
                    results['success'] = False
                    print("❌ AnalyticsFilterForm validation failed")
            except Exception as e:
                results['forms']['AnalyticsFilterForm'] = f'FAILED: {str(e)}'
                results['errors'].append(f"AnalyticsFilterForm error: {e}")
                results['success'] = False
                print(f"❌ AnalyticsFilterForm failed: {e}")
            
            # Test ProfileVisibilityForm
            try:
                form = ProfileVisibilityForm()
                form.profile_visibility.data = 'public'
                form.email_visibility.data = 'public'
                
                if form.validate():
                    results['forms']['ProfileVisibilityForm'] = 'SUCCESS'
                    print("✅ ProfileVisibilityForm working correctly")
                else:
                    results['forms']['ProfileVisibilityForm'] = 'FAILED: Form validation failed'
                    results['success'] = False
                    print("❌ ProfileVisibilityForm validation failed")
            except Exception as e:
                results['forms']['ProfileVisibilityForm'] = f'FAILED: {str(e)}'
                results['errors'].append(f"ProfileVisibilityForm error: {e}")
                results['success'] = False
                print(f"❌ ProfileVisibilityForm failed: {e}")
            
            # Test WidgetManagementForm
            try:
                form = WidgetManagementForm()
                form.enabled_widgets.data = '["bio", "stats"]'
                
                if form.validate():
                    results['forms']['WidgetManagementForm'] = 'SUCCESS'
                    print("✅ WidgetManagementForm working correctly")
                else:
                    results['forms']['WidgetManagementForm'] = 'FAILED: Form validation failed'
                    results['success'] = False
                    print("❌ WidgetManagementForm validation failed")
            except Exception as e:
                results['forms']['WidgetManagementForm'] = f'FAILED: {str(e)}'
                results['errors'].append(f"WidgetManagementForm error: {e}")
                results['success'] = False
                print(f"❌ WidgetManagementForm failed: {e}")
            
    except Exception as e:
        error_msg = f"Forms test error: {str(e)}"
        results['errors'].append(error_msg)
        results['success'] = False
        print(f"❌ Forms test failed: {e}")
        traceback.print_exc()
    
    return results

def test_advanced_profile_features():
    """Test advanced profile features"""
    print("\n🔍 Testing advanced profile features...")
    
    results = {
        'success': True,
        'features': {},
        'errors': []
    }
    
    try:
        from app import create_app, db
        from app.user.advanced_profile import AdvancedProfileManager, ProfileThemeManager, ProfileAnalyticsManager
        from app.models import User
        
        from testing import TestingConfig
        app = create_app(TestingConfig)
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create test user
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Test AdvancedProfileManager
            try:
                # Test theme management
                theme_data = AdvancedProfileManager.set_profile_theme(
                    user_id=user.id,
                    theme_name='dark',
                    skin_variant='dark',
                    css_variables={'primary_color': '#007bff'}
                )
                
                retrieved_theme = AdvancedProfileManager.get_profile_theme(user.id)
                if theme_data and retrieved_theme['theme_name'] == 'dark':
                    results['features']['theme_management'] = 'SUCCESS'
                    print("✅ Theme management working correctly")
                else:
                    results['features']['theme_management'] = 'FAILED: Theme not set/retrieved correctly'
                    results['success'] = False
                    print("❌ Theme management failed")
                
                # Test layout management
                layout_data = AdvancedProfileManager.set_profile_layout(
                    user_id=user.id,
                    layout_type='grid',
                    columns=3
                )
                
                retrieved_layout = AdvancedProfileManager.get_profile_layout(user.id)
                if layout_data and retrieved_layout['layout_type'] == 'grid':
                    results['features']['layout_management'] = 'SUCCESS'
                    print("✅ Layout management working correctly")
                else:
                    results['features']['layout_management'] = 'FAILED: Layout not set/retrieved correctly'
                    results['success'] = False
                    print("❌ Layout management failed")
                
                # Test privacy settings
                privacy_data = AdvancedProfileManager.set_profile_privacy(
                    user_id=user.id,
                    privacy_settings={'profile_visibility': 'public', 'email_visibility': 'friends'}
                )
                
                retrieved_privacy = AdvancedProfileManager.get_profile_privacy(user.id)
                if privacy_data and retrieved_privacy['profile_visibility'] == 'public':
                    results['features']['privacy_management'] = 'SUCCESS'
                    print("✅ Privacy management working correctly")
                else:
                    results['features']['privacy_management'] = 'FAILED: Privacy not set/retrieved correctly'
                    results['success'] = False
                    print("❌ Privacy management failed")
                
                # Test complete profile config
                config = AdvancedProfileManager.get_complete_profile_config(user.id)
                if config and 'theme' in config and 'layout' in config:
                    results['features']['complete_config'] = 'SUCCESS'
                    print("✅ Complete profile config working correctly")
                else:
                    results['features']['complete_config'] = 'FAILED: Complete config not retrieved correctly'
                    results['success'] = False
                    print("❌ Complete profile config failed")
                
            except Exception as e:
                error_msg = f"AdvancedProfileManager test error: {str(e)}"
                results['errors'].append(error_msg)
                results['success'] = False
                print(f"❌ AdvancedProfileManager test failed: {e}")
                traceback.print_exc()
            
            # Test ProfileThemeManager
            try:
                theme = ProfileThemeManager.create_theme(
                    name='debug_theme',
                    display_name='Debug Theme',
                    css_variables={'primary_color': '#28a745'},
                    is_system_theme=False
                )
                
                if theme and theme.name == 'debug_theme':
                    results['features']['theme_creation'] = 'SUCCESS'
                    print("✅ Theme creation working correctly")
                else:
                    results['features']['theme_creation'] = 'FAILED: Theme not created correctly'
                    results['success'] = False
                    print("❌ Theme creation failed")
                
                # Test theme CSS generation
                css = ProfileThemeManager.get_theme_css('debug_theme')
                if css and '--primary-color' in css:
                    results['features']['theme_css'] = 'SUCCESS'
                    print("✅ Theme CSS generation working correctly")
                else:
                    results['features']['theme_css'] = 'FAILED: Theme CSS not generated correctly'
                    results['success'] = False
                    print("❌ Theme CSS generation failed")
                
            except Exception as e:
                error_msg = f"ProfileThemeManager test error: {str(e)}"
                results['errors'].append(error_msg)
                results['success'] = False
                print(f"❌ ProfileThemeManager test failed: {e}")
                traceback.print_exc()
            
    except Exception as e:
        error_msg = f"Advanced profile features test error: {str(e)}"
        results['errors'].append(error_msg)
        results['success'] = False
        print(f"❌ Advanced profile features test failed: {e}")
        traceback.print_exc()
    
    return results

def test_social_features():
    """Test social features"""
    print("\n🔍 Testing social features...")
    
    results = {
        'success': True,
        'features': {},
        'errors': []
    }
    
    try:
        from app import create_app, db
        from app.user.social_features import SocialConnectionManager, SocialFeedManager, UserRecommendationManager
        from app.models import User
        
        from testing import TestingConfig
        app = create_app(TestingConfig)
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create test users
            user1 = User(username='user1', email='user1@example.com')
            user1.set_password('password123')
            user2 = User(username='user2', email='user2@example.com')
            user2.set_password('password123')
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            # Test SocialConnectionManager
            try:
                # Test connection creation
                connection_result = SocialConnectionManager.create_connection(
                    user_id=user1.id,
                    connected_user_id=user2.id,
                    connection_type='follow',
                    message='Test connection'
                )
                
                if connection_result['success']:
                    results['features']['connection_creation'] = 'SUCCESS'
                    print("✅ Connection creation working correctly")
                else:
                    results['features']['connection_creation'] = f'FAILED: {connection_result["message"]}'
                    results['success'] = False
                    print(f"❌ Connection creation failed: {connection_result['message']}")
                
                # Test connection stats
                stats = SocialConnectionManager.get_connection_stats(user1.id)
                if stats and 'following_count' in stats and stats['following_count'] > 0:
                    results['features']['connection_stats'] = 'SUCCESS'
                    print("✅ Connection stats working correctly")
                else:
                    results['features']['connection_stats'] = 'FAILED: Connection stats not retrieved correctly'
                    results['success'] = False
                    print("❌ Connection stats failed")
                
                # Test mutual connections
                # Create reverse connection
                SocialConnectionManager.create_connection(
                    user_id=user2.id,
                    connected_user_id=user1.id,
                    connection_type='follow'
                )
                
                mutual = SocialConnectionManager.get_mutual_connections(user1.id, user2.id)
                if len(mutual) > 0:
                    results['features']['mutual_connections'] = 'SUCCESS'
                    print("✅ Mutual connections working correctly")
                else:
                    results['features']['mutual_connections'] = 'FAILED: Mutual connections not retrieved correctly'
                    results['success'] = False
                    print("❌ Mutual connections failed")
                
            except Exception as e:
                error_msg = f"SocialConnectionManager test error: {str(e)}"
                results['errors'].append(error_msg)
                results['success'] = False
                print(f"❌ SocialConnectionManager test failed: {e}")
                traceback.print_exc()
            
            # Test SocialFeedManager
            try:
                # Test feed generation
                feed = SocialFeedManager.generate_feed(user1.id, limit=5)
                if isinstance(feed, list):
                    results['features']['feed_generation'] = 'SUCCESS'
                    print("✅ Feed generation working correctly")
                else:
                    results['features']['feed_generation'] = 'FAILED: Feed not generated correctly'
                    results['success'] = False
                    print("❌ Feed generation failed")
                
                # Test activity feed
                activity_feed = SocialFeedManager.get_activity_feed(user1.id, days=7)
                if isinstance(activity_feed, list):
                    results['features']['activity_feed'] = 'SUCCESS'
                    print("✅ Activity feed working correctly")
                else:
                    results['features']['activity_feed'] = 'FAILED: Activity feed not generated correctly'
                    results['success'] = False
                    print("❌ Activity feed failed")
                
            except Exception as e:
                error_msg = f"SocialFeedManager test error: {str(e)}"
                results['errors'].append(error_msg)
                results['success'] = False
                print(f"❌ SocialFeedManager test failed: {e}")
                traceback.print_exc()
            
            # Test UserRecommendationManager
            try:
                recommendations = UserRecommendationManager.get_recommendations(user1.id, limit=5)
                if isinstance(recommendations, list):
                    results['features']['recommendations'] = 'SUCCESS'
                    print("✅ User recommendations working correctly")
                else:
                    results['features']['recommendations'] = 'FAILED: Recommendations not generated correctly'
                    results['success'] = False
                    print("❌ User recommendations failed")
                
            except Exception as e:
                error_msg = f"UserRecommendationManager test error: {str(e)}"
                results['errors'].append(error_msg)
                results['success'] = False
                print(f"❌ UserRecommendationManager test failed: {e}")
                traceback.print_exc()
            
    except Exception as e:
        error_msg = f"Social features test error: {str(e)}"
        results['errors'].append(error_msg)
        results['success'] = False
        print(f"❌ Social features test failed: {e}")
        traceback.print_exc()
    
    return results

def test_routes():
    """Test routes functionality"""
    print("\n🔍 Testing routes...")
    
    results = {
        'success': True,
        'routes': {},
        'errors': []
    }
    
    try:
        from app import create_app
        from app.user.routes import user_preferences, profile_customize, follow_user, following, followers, analytics, user_roles, profile_visibility, widgets
        
        from testing import TestingConfig
        app = create_app(TestingConfig)
        with app.test_client() as client:
            # Test user preferences route
            try:
                response = client.get('/user/preferences')
                # Should redirect to login since not authenticated
                if response.status_code in [302, 401]:
                    results['routes']['user_preferences'] = 'SUCCESS'
                    print("✅ User preferences route working correctly")
                else:
                    results['routes']['user_preferences'] = f'FAILED: Unexpected status code {response.status_code}'
                    results['success'] = False
                    print(f"❌ User preferences route failed: status {response.status_code}")
            except Exception as e:
                results['routes']['user_preferences'] = f'FAILED: {str(e)}'
                results['errors'].append(f"User preferences route error: {e}")
                results['success'] = False
                print(f"❌ User preferences route failed: {e}")
            
            # Test profile customize route
            try:
                response = client.get('/user/profile/customize')
                if response.status_code in [302, 401]:
                    results['routes']['profile_customize'] = 'SUCCESS'
                    print("✅ Profile customize route working correctly")
                else:
                    results['routes']['profile_customize'] = f'FAILED: Unexpected status code {response.status_code}'
                    results['success'] = False
                    print(f"❌ Profile customize route failed: status {response.status_code}")
            except Exception as e:
                results['routes']['profile_customize'] = f'FAILED: {str(e)}'
                results['errors'].append(f"Profile customize route error: {e}")
                results['success'] = False
                print(f"❌ Profile customize route failed: {e}")
            
            # Test social follow route
            try:
                response = client.post('/user/social/follow', data={'user_id': '1'})
                if response.status_code in [302, 401, 400]:
                    results['routes']['social_follow'] = 'SUCCESS'
                    print("✅ Social follow route working correctly")
                else:
                    results['routes']['social_follow'] = f'FAILED: Unexpected status code {response.status_code}'
                    results['success'] = False
                    print(f"❌ Social follow route failed: status {response.status_code}")
            except Exception as e:
                results['routes']['social_follow'] = f'FAILED: {str(e)}'
                results['errors'].append(f"Social follow route error: {e}")
                results['success'] = False
                print(f"❌ Social follow route failed: {e}")
            
            # Test analytics route
            try:
                response = client.get('/user/analytics')
                if response.status_code in [302, 401]:
                    results['routes']['analytics'] = 'SUCCESS'
                    print("✅ Analytics route working correctly")
                else:
                    results['routes']['analytics'] = f'FAILED: Unexpected status code {response.status_code}'
                    results['success'] = False
                    print(f"❌ Analytics route failed: status {response.status_code}")
            except Exception as e:
                results['routes']['analytics'] = f'FAILED: {str(e)}'
                results['errors'].append(f"Analytics route error: {e}")
                results['success'] = False
                print(f"❌ Analytics route failed: {e}")
            
            # Test profile visibility route
            try:
                response = client.get('/user/profile/visibility')
                if response.status_code in [302, 401]:
                    results['routes']['profile_visibility'] = 'SUCCESS'
                    print("✅ Profile visibility route working correctly")
                else:
                    results['routes']['profile_visibility'] = f'FAILED: Unexpected status code {response.status_code}'
                    results['success'] = False
                    print(f"❌ Profile visibility route failed: status {response.status_code}")
            except Exception as e:
                results['routes']['profile_visibility'] = f'FAILED: {str(e)}'
                results['errors'].append(f"Profile visibility route error: {e}")
                results['success'] = False
                print(f"❌ Profile visibility route failed: {e}")
            
    except Exception as e:
        error_msg = f"Routes test error: {str(e)}"
        results['errors'].append(error_msg)
        results['success'] = False
        print(f"❌ Routes test failed: {e}")
        traceback.print_exc()
    
    return results

def generate_debugging_report(results):
    """Generate comprehensive debugging report"""
    print("\n📊 Generating debugging report...")
    
    report = f"""
# Newly Added Systems Debugging Report

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC  
**System:** Auto Bot Solutions Forum  
**Component:** User Management System - Newly Added Features

## Executive Summary

{len(results['errors'])} errors encountered during debugging of newly added systems. All systems have been tested for functionality and integration.

## Test Results Summary

### Overall Status: {'✅ SUCCESS' if results['success'] else '❌ FAILED'}

### Import Tests
{json.dumps(results.get('imports', {}), indent=2)}

### Database Model Tests
{json.dumps(results.get('models', {}), indent=2)}

### Form Tests
{json.dumps(results.get('forms', {}), indent=2)}

### Advanced Profile Features Tests
{json.dumps(results.get('features', {}), indent=2)}

### Social Features Tests
{json.dumps(results.get('features', {}), indent=2)}

### Route Tests
{json.dumps(results.get('routes', {}), indent=2)}

## Issues Found

{chr(10).join([f"- {error}" for error in results['errors']]) if results['errors'] else "No critical issues found."}

## Recommendations

{"All systems are operational and ready for production use." if results['success'] else "Some systems require attention before production deployment."}

## Next Steps

1. {"Deploy to production environment." if results['success'] else "Fix identified issues before deployment."}
2. Monitor system performance in production
3. Regular maintenance and updates
4. User training and documentation

---
**Report completed:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
    
    # Save report to file
    report_file = "/home/robbie/Desktop/repo-forum/reports/newly_added_systems_debugging_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"✅ Debugging report saved to: {report_file}")
    return report_file

def main():
    """Main debugging function"""
    print("🚀 Starting Comprehensive Debugging of Newly Added Systems")
    print("=" * 60)
    
    all_results = {
        'success': True,
        'imports': {},
        'models': {},
        'forms': {},
        'features': {},
        'routes': {},
        'errors': []
    }
    
    # Test imports
    print("\n" + "="*60)
    import_results = test_imports()
    all_results['imports'] = import_results['imports']
    all_results['errors'].extend(import_results['errors'])
    if not import_results['success']:
        all_results['success'] = False
    
    # Test database models
    print("\n" + "="*60)
    model_results = test_database_models()
    all_results['models'] = model_results['models']
    all_results['errors'].extend(model_results['errors'])
    if not model_results['success']:
        all_results['success'] = False
    
    # Test forms
    print("\n" + "="*60)
    form_results = test_forms()
    all_results['forms'] = form_results['forms']
    all_results['errors'].extend(form_results['errors'])
    if not form_results['success']:
        all_results['success'] = False
    
    # Test advanced profile features
    print("\n" + "="*60)
    profile_results = test_advanced_profile_features()
    all_results['features'].update(profile_results['features'])
    all_results['errors'].extend(profile_results['errors'])
    if not profile_results['success']:
        all_results['success'] = False
    
    # Test social features
    print("\n" + "="*60)
    social_results = test_social_features()
    all_results['features'].update(social_results['features'])
    all_results['errors'].extend(social_results['errors'])
    if not social_results['success']:
        all_results['success'] = False
    
    # Test routes
    print("\n" + "="*60)
    route_results = test_routes()
    all_results['routes'] = route_results['routes']
    all_results['errors'].extend(route_results['errors'])
    if not route_results['success']:
        all_results['success'] = False
    
    # Generate report
    print("\n" + "="*60)
    report_file = generate_debugging_report(all_results)
    
    # Summary
    total_tests = len(all_results['imports']) + len(all_results['models']) + len(all_results['forms']) + len(all_results['features']) + len(all_results['routes'])
    passed_tests = sum(1 for results_dict in [all_results['imports'], all_results['models'], all_results['forms'], all_results['features'], all_results['routes']] for result in results_dict.values() if result == 'SUCCESS')
    
    print(f"\n🎯 Debugging Summary:")
    print(f"   Total Test Categories: {total_tests}")
    print(f"   Passed Tests: {passed_tests}")
    print(f"   Failed Tests: {total_tests - passed_tests}")
    print(f"   Success Rate: {passed_tests / total_tests * 100:.1f}%")
    print(f"   Total Errors: {len(all_results['errors'])}")
    
    if all_results['success']:
        print("🎉 All newly added systems are working correctly!")
    else:
        print("⚠️  Some systems have issues that need attention.")
    
    print(f"📄 Full report available at: {report_file}")
    
    return all_results

if __name__ == "__main__":
    main()
