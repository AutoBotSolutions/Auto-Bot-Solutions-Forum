"""
Unit tests for the User Preference System
"""

import pytest
import json
from datetime import datetime
from app.models import User
from app.user.forms import UserPreferencesForm, NotificationPreferencesForm, AccessibilityPreferencesForm


class TestUserPreferences:
    """Test suite for user preference functionality."""

    def test_get_default_general_preferences(self, sample_user):
        """Test getting default general preferences."""
        prefs = sample_user.get_general_preferences()
        assert prefs['theme_preference'] == 'light'
        assert prefs['language_preference'] == 'en'
        assert prefs['timezone'] == 'UTC'
        assert prefs['date_format'] == 'MM/DD/YYYY'
        assert prefs['time_format'] == '12-hour'
        assert prefs['email_notifications'] is True
        assert prefs['push_notifications'] is True
        assert prefs['show_sensitive_content'] is False
        assert prefs['auto_play_videos'] is True
        assert prefs['show_avatars'] is True
        assert prefs['allow_tagging'] is True

    def test_set_general_preferences(self, sample_user):
        """Test setting general preferences."""
        prefs = {
            'theme_preference': 'dark',
            'language_preference': 'es',
            'timezone': 'EST',
            'date_format': 'DD/MM/YYYY',
            'time_format': '24-hour',
            'email_notifications': False,
            'push_notifications': False,
            'show_sensitive_content': True,
            'auto_play_videos': False,
            'show_avatars': False,
            'allow_tagging': False
        }
        
        result = sample_user.set_general_preferences(prefs)
        assert result is True
        
        saved_prefs = sample_user.get_general_preferences()
        assert saved_prefs['theme_preference'] == 'dark'
        assert saved_prefs['language_preference'] == 'es'
        assert saved_prefs['timezone'] == 'EST'
        assert saved_prefs['date_format'] == 'DD/MM/YYYY'
        assert saved_prefs['time_format'] == '24-hour'
        assert saved_prefs['email_notifications'] is False
        assert saved_prefs['push_notifications'] is False
        assert saved_prefs['show_sensitive_content'] is True
        assert saved_prefs['auto_play_videos'] is False
        assert saved_prefs['show_avatars'] is False
        assert saved_prefs['allow_tagging'] is False

    def test_get_default_notification_preferences(self, sample_user):
        """Test getting default notification preferences."""
        prefs = sample_user.get_notification_preferences()
        
        # Check email preferences
        assert prefs['email']['new_follower'] is True
        assert prefs['email']['new_message'] is True
        assert prefs['email']['post_reply'] is True
        assert prefs['email']['comment_reply'] is True
        assert prefs['email']['mention'] is True
        assert prefs['email']['badge_earned'] is True
        assert prefs['email']['system_updates'] is False
        
        # Check push preferences
        assert prefs['push']['new_follower'] is True
        assert prefs['push']['system_updates'] is False
        
        # Check in-app preferences
        assert prefs['inapp']['new_follower'] is True
        assert prefs['inapp']['system_updates'] is False
        
        # Check frequency and quiet hours
        assert prefs['frequency'] == 'immediate'
        assert prefs['quiet_hours']['enabled'] is False
        assert prefs['quiet_hours']['start'] == '22:00'
        assert prefs['quiet_hours']['end'] == '08:00'

    def test_set_notification_preferences(self, sample_user):
        """Test setting notification preferences."""
        prefs = {
            'email': {
                'new_follower': False,
                'new_message': False,
                'post_reply': False,
                'comment_reply': False,
                'mention': False,
                'badge_earned': False,
                'system_updates': True
            },
            'push': {
                'new_follower': False,
                'new_message': False,
                'post_reply': False,
                'comment_reply': False,
                'mention': False,
                'badge_earned': False,
                'system_updates': True
            },
            'inapp': {
                'new_follower': False,
                'new_message': False,
                'post_reply': False,
                'comment_reply': False,
                'mention': False,
                'badge_earned': False,
                'system_updates': True
            },
            'frequency': 'daily',
            'quiet_hours': {
                'enabled': True,
                'start': '23:00',
                'end': '07:00'
            }
        }
        
        result = sample_user.set_notification_preferences(prefs)
        assert result is True
        
        saved_prefs = sample_user.get_notification_preferences()
        assert saved_prefs['email']['new_follower'] is False
        assert saved_prefs['email']['system_updates'] is True
        assert saved_prefs['frequency'] == 'daily'
        assert saved_prefs['quiet_hours']['enabled'] is True
        assert saved_prefs['quiet_hours']['start'] == '23:00'
        assert saved_prefs['quiet_hours']['end'] == '07:00'

    def test_get_default_accessibility_preferences(self, sample_user):
        """Test getting default accessibility preferences."""
        prefs = sample_user.get_accessibility_preferences()
        assert prefs['font_size'] == 'medium'
        assert prefs['high_contrast'] is False
        assert prefs['reduce_motion'] is False
        assert prefs['screen_reader_optimized'] is False
        assert prefs['keyboard_navigation'] is False
        assert prefs['color_blind_friendly'] is False
        assert prefs['dyslexia_font'] is False

    def test_set_accessibility_preferences(self, sample_user):
        """Test setting accessibility preferences."""
        prefs = {
            'font_size': 'large',
            'high_contrast': True,
            'reduce_motion': True,
            'screen_reader_optimized': True,
            'keyboard_navigation': True,
            'color_blind_friendly': True,
            'dyslexia_font': True
        }
        
        result = sample_user.set_accessibility_preferences(prefs)
        assert result is True
        
        saved_prefs = sample_user.get_accessibility_preferences()
        assert saved_prefs['font_size'] == 'large'
        assert saved_prefs['high_contrast'] is True
        assert saved_prefs['reduce_motion'] is True
        assert saved_prefs['screen_reader_optimized'] is True
        assert saved_prefs['keyboard_navigation'] is True
        assert saved_prefs['color_blind_friendly'] is True
        assert saved_prefs['dyslexia_font'] is True

    def test_get_default_social_preferences(self, sample_user):
        """Test getting default social preferences."""
        prefs = sample_user.get_social_preferences()
        assert prefs['allow_follow_requests'] is True
        assert prefs['allow_friend_requests'] is True
        assert prefs['show_followers_publicly'] is True
        assert prefs['show_following_publicly'] is True
        assert prefs['show_friends_publicly'] is True
        assert prefs['allow_tagging'] is True
        assert prefs['allow_mentions'] is True
        assert prefs['show_activity_publicly'] is True
        assert prefs['searchable'] is True
        assert prefs['indexable'] is True

    def test_set_social_preferences(self, sample_user):
        """Test setting social preferences."""
        prefs = {
            'allow_follow_requests': False,
            'allow_friend_requests': False,
            'show_followers_publicly': False,
            'show_following_publicly': False,
            'show_friends_publicly': False,
            'allow_tagging': False,
            'allow_mentions': False,
            'show_activity_publicly': False,
            'searchable': False,
            'indexable': False
        }
        
        result = sample_user.set_social_preferences(prefs)
        assert result is True
        
        saved_prefs = sample_user.get_social_preferences()
        assert saved_prefs['allow_follow_requests'] is False
        assert saved_prefs['allow_friend_requests'] is False
        assert saved_prefs['searchable'] is False
        assert saved_prefs['indexable'] is False

    def test_preference_json_handling(self, sample_user):
        """Test JSON handling in preferences."""
        # Test with empty JSON string
        sample_user.user_preferences = ''
        db.session.commit()
        
        prefs = sample_user.get_general_preferences()
        assert prefs['theme_preference'] == 'light'
        
        # Test with malformed JSON
        sample_user.user_preferences = '{invalid json'
        db.session.commit()
        
        prefs = sample_user.get_general_preferences()
        assert prefs['theme_preference'] == 'light'

    def test_preference_partial_update(self, sample_user):
        """Test partial preference updates."""
        # Set initial preferences
        initial_prefs = {
            'theme_preference': 'dark',
            'language_preference': 'fr',
            'timezone': 'PST',
            'email_notifications': False
        }
        sample_user.set_general_preferences(initial_prefs)
        
        # Update only some preferences
        partial_prefs = {
            'theme_preference': 'light',
            'timezone': 'EST'
        }
        sample_user.set_general_preferences(partial_prefs)
        
        # Check that updated preferences changed and others remained
        final_prefs = sample_user.get_general_preferences()
        assert final_prefs['theme_preference'] == 'light'  # Updated
        assert final_prefs['timezone'] == 'EST'  # Updated
        assert final_prefs['language_preference'] == 'fr'  # Unchanged
        assert final_prefs['email_notifications'] is False  # Unchanged

    def test_preference_validation(self, sample_user):
        """Test preference validation."""
        # Test with invalid data types
        invalid_prefs = {
            'theme_preference': 123,  # Should be string
            'email_notifications': 'yes',  # Should be boolean
            'timezone': None  # Should be string
        }
        
        # Should still save but with validation in forms
        result = sample_user.set_general_preferences(invalid_prefs)
        assert result is True
        
        saved_prefs = sample_user.get_general_preferences()
        assert saved_prefs['theme_preference'] == 123
        assert saved_prefs['email_notifications'] == 'yes'
        assert saved_prefs['timezone'] is None


class TestUserPreferenceForms:
    """Test suite for user preference forms."""

    def test_user_preferences_form_valid(self):
        """Test valid user preferences form."""
        form = UserPreferencesForm(data={
            'theme_preference': 'dark',
            'language_preference': 'es',
            'timezone': 'EST',
            'date_format': 'DD/MM/YYYY',
            'time_format': '24-hour',
            'email_notifications': True,
            'push_notifications': False,
            'desktop_notifications': True,
            'show_sensitive_content': False,
            'auto_play_videos': False,
            'show_avatars': True,
            'show_signatures': False,
            'show_online_status': True,
            'allow_tagging': False,
            'allow_mentions': True
        })
        assert form.validate() is True
        assert form.theme_preference.data == 'dark'
        assert form.language_preference.data == 'es'
        assert form.email_notifications.data is True

    def test_user_preferences_form_invalid(self):
        """Test invalid user preferences form."""
        form = UserPreferencesForm(data={})
        assert form.validate() is False
        assert 'theme_preference' in form.errors
        assert 'language_preference' in form.errors
        assert 'timezone' in form.errors
        assert 'date_format' in form.errors
        assert 'time_format' in form.errors

    def test_notification_preferences_form_valid(self):
        """Test valid notification preferences form."""
        form = NotificationPreferencesForm(data={
            'email_new_follower': True,
            'email_new_message': False,
            'email_post_reply': True,
            'email_comment_reply': False,
            'email_mention': True,
            'email_badge_earned': False,
            'email_system_updates': True,
            'push_new_follower': True,
            'push_new_message': False,
            'push_system_updates': False,
            'inapp_new_follower': True,
            'inapp_new_message': False,
            'inapp_system_updates': False,
            'notification_frequency': 'daily',
            'enable_quiet_hours': True,
            'quiet_hours_start': '23:00',
            'quiet_hours_end': '07:00'
        })
        assert form.validate() is True
        assert form.email_new_follower.data is True
        assert form.email_new_message.data is False
        assert form.notification_frequency.data == 'daily'
        assert form.enable_quiet_hours.data is True

    def test_notification_preferences_form_invalid(self):
        """Test invalid notification preferences form."""
        form = NotificationPreferencesForm(data={})
        assert form.validate() is False
        assert 'notification_frequency' in form.errors

    def test_accessibility_preferences_form_valid(self):
        """Test valid accessibility preferences form."""
        form = AccessibilityPreferencesForm(data={
            'font_size': 'large',
            'high_contrast': True,
            'reduce_motion': True,
            'screen_reader_optimized': True,
            'keyboard_navigation': True,
            'color_blind_friendly': True,
            'dyslexia_font': True
        })
        assert form.validate() is True
        assert form.font_size.data == 'large'
        assert form.high_contrast.data is True
        assert form.reduce_motion.data is True

    def test_accessibility_preferences_form_invalid(self):
        """Test invalid accessibility preferences form."""
        form = AccessibilityPreferencesForm(data={})
        assert form.validate() is False
        assert 'font_size' in form.errors


class TestUserPreferenceIntegration:
    """Integration tests for user preferences."""

    def test_full_preference_workflow(self, sample_user):
        """Test complete preference workflow."""
        # Set general preferences
        general_prefs = {
            'theme_preference': 'dark',
            'language_preference': 'fr',
            'timezone': 'CET',
            'email_notifications': False
        }
        sample_user.set_general_preferences(general_prefs)
        
        # Set notification preferences
        notification_prefs = {
            'email': {'new_follower': False, 'system_updates': True},
            'push': {'new_follower': False, 'system_updates': True},
            'inapp': {'new_follower': True, 'system_updates': False},
            'frequency': 'weekly',
            'quiet_hours': {'enabled': True, 'start': '22:00', 'end': '08:00'}
        }
        sample_user.set_notification_preferences(notification_prefs)
        
        # Set accessibility preferences
        accessibility_prefs = {
            'font_size': 'large',
            'high_contrast': True,
            'reduce_motion': True
        }
        sample_user.set_accessibility_preferences(accessibility_prefs)
        
        # Verify all preferences are set correctly
        general = sample_user.get_general_preferences()
        assert general['theme_preference'] == 'dark'
        assert general['email_notifications'] is False
        
        notifications = sample_user.get_notification_preferences()
        assert notifications['email']['new_follower'] is False
        assert notifications['frequency'] == 'weekly'
        assert notifications['quiet_hours']['enabled'] is True
        
        accessibility = sample_user.get_accessibility_preferences()
        assert accessibility['font_size'] == 'large'
        assert accessibility['high_contrast'] is True

    def test_preference_inheritance(self, sample_user):
        """Test preference inheritance and defaults."""
        # Set only some preferences
        partial_prefs = {
            'theme_preference': 'dark',
            'email_notifications': False
        }
        sample_user.set_general_preferences(partial_prefs)
        
        # Check that set preferences are used and others are defaults
        prefs = sample_user.get_general_preferences()
        assert prefs['theme_preference'] == 'dark'  # Set
        assert prefs['email_notifications'] is False  # Set
        assert prefs['language_preference'] == 'en'  # Default
        assert prefs['timezone'] == 'UTC'  # Default
        assert prefs['push_notifications'] is True  # Default

    def test_preference_persistence(self, sample_user):
        """Test that preferences persist across sessions."""
        # Set preferences
        prefs = {
            'theme_preference': 'dark',
            'language_preference': 'de',
            'timezone': 'GMT'
        }
        sample_user.set_general_preferences(prefs)
        
        # Simulate session reload
        user_from_db = User.query.get(sample_user.id)
        
        # Check preferences persist
        saved_prefs = user_from_db.get_general_preferences()
        assert saved_prefs['theme_preference'] == 'dark'
        assert saved_prefs['language_preference'] == 'de'
        assert saved_prefs['timezone'] == 'GMT'

    def test_preference_edge_cases(self, sample_user):
        """Test edge cases in preference handling."""
        # Test with None values
        prefs = {
            'theme_preference': None,
            'email_notifications': None,
            'timezone': None
        }
        sample_user.set_general_preferences(prefs)
        
        saved_prefs = sample_user.get_general_preferences()
        assert saved_prefs['theme_preference'] is None
        assert saved_prefs['email_notifications'] is None
        assert saved_prefs['timezone'] is None
        
        # Test with empty strings
        prefs = {
            'theme_preference': '',
            'language_preference': '',
            'timezone': ''
        }
        sample_user.set_general_preferences(prefs)
        
        saved_prefs = sample_user.get_general_preferences()
        assert saved_prefs['theme_preference'] == ''
        assert saved_prefs['language_preference'] == ''
        assert saved_prefs['timezone'] == ''

    def test_preference_performance(self, sample_user):
        """Test performance of preference operations."""
        import time
        
        start_time = time.time()
        
        # Test multiple preference operations
        for i in range(100):
            prefs = {
                'theme_preference': f'theme_{i}',
                'email_notifications': i % 2 == 0
            }
            sample_user.set_general_preferences(prefs)
            sample_user.get_general_preferences()
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Should complete 200 operations in reasonable time
        assert operation_time < 1.0, f"Operations took too long: {operation_time}s"

    def test_notification_quiet_hours(self, sample_user):
        """Test notification quiet hours functionality."""
        # Set quiet hours
        notification_prefs = {
            'quiet_hours': {
                'enabled': True,
                'start': '22:00',
                'end': '08:00'
            }
        }
        sample_user.set_notification_preferences(notification_prefs)
        
        prefs = sample_user.get_notification_preferences()
        assert prefs['quiet_hours']['enabled'] is True
        assert prefs['quiet_hours']['start'] == '22:00'
        assert prefs['quiet_hours']['end'] == '08:00'

    def test_accessibility_font_sizes(self, sample_user):
        """Test all accessibility font size options."""
        font_sizes = ['small', 'medium', 'large', 'extra_large']
        
        for font_size in font_sizes:
            prefs = {'font_size': font_size}
            sample_user.set_accessibility_preferences(prefs)
            
            saved_prefs = sample_user.get_accessibility_preferences()
            assert saved_prefs['font_size'] == font_size

    def test_social_privacy_combinations(self, sample_user):
        """Test various social privacy combinations."""
        test_cases = [
            {'searchable': True, 'indexable': True, 'public_profile': True},
            {'searchable': False, 'indexable': False, 'public_profile': False},
            {'searchable': True, 'indexable': False, 'public_profile': True},
            {'searchable': False, 'indexable': True, 'public_profile': False}
        ]
        
        for case in test_cases:
            sample_user.set_social_preferences(case)
            saved_prefs = sample_user.get_social_preferences()
            
            for key, value in case.items():
                assert saved_prefs[key] == value
