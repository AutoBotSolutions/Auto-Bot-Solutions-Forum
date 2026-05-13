"""
Unit tests for the Profile Customization System
"""

import pytest
import json
from datetime import datetime
from app.models import User
from app.user.forms import ProfileThemeForm, ProfileLayoutForm, ProfileWidgetsForm, ProfilePrivacyForm


class TestProfileCustomization:
    """Test suite for profile customization functionality."""

    def test_profile_theme_get_default(self, sample_user):
        """Test getting default profile theme."""
        theme = sample_user.get_profile_theme()
        assert theme['theme'] == 'default'
        assert theme['skin'] == 'light'

    def test_profile_theme_set_theme(self, sample_user):
        """Test setting profile theme."""
        result = sample_user.set_profile_theme('dark', 'dark')
        assert result is True
        
        theme = sample_user.get_profile_theme()
        assert theme['theme'] == 'dark'
        assert theme['skin'] == 'dark'

    def test_profile_theme_invalid_theme(self, sample_user):
        """Test setting invalid theme."""
        result = sample_user.set_profile_theme('invalid_theme', 'light')
        assert result is True  # Should still work but with validation
        
        theme = sample_user.get_profile_theme()
        assert theme['theme'] == 'invalid_theme'

    def test_profile_layout_get_default(self, sample_user):
        """Test getting default profile layout."""
        layout = sample_user.get_profile_layout()
        assert layout['layout'] == 'default'
        assert layout['columns'] == 2
        assert 'sections' in layout

    def test_profile_layout_set_layout(self, sample_user):
        """Test setting profile layout."""
        layout_config = {
            'layout': 'grid',
            'columns': 3,
            'sections': [
                {'id': 'bio', 'visible': True, 'position': 1},
                {'id': 'stats', 'visible': False, 'position': 2}
            ]
        }
        
        result = sample_user.set_profile_layout(layout_config)
        assert result is True
        
        layout = sample_user.get_profile_layout()
        assert layout['layout'] == 'grid'
        assert layout['columns'] == 3
        assert len(layout['sections']) == 2

    def test_profile_layout_invalid_json(self, sample_user):
        """Test setting invalid layout JSON."""
        # This should handle the JSON conversion gracefully
        layout_config = "invalid json"
        sample_user.profile_layout = layout_config
        db.session.commit()
        
        # Should return default layout
        layout = sample_user.get_profile_layout()
        assert layout['layout'] == 'default'

    def test_profile_widgets_get_default(self, sample_user):
        """Test getting default profile widgets."""
        widgets = sample_user.get_profile_widgets()
        assert 'widgets' in widgets
        assert len(widgets['widgets']) >= 1
        assert any(w['id'] == 'recent_posts' for w in widgets['widgets'])

    def test_profile_widgets_set_widgets(self, sample_user):
        """Test setting profile widgets."""
        widget_config = {
            'widgets': [
                {
                    'id': 'recent_posts',
                    'enabled': True,
                    'position': 'main',
                    'limit': 10
                },
                {
                    'id': 'user_stats',
                    'enabled': False,
                    'position': 'sidebar'
                }
            ]
        }
        
        result = sample_user.set_profile_widgets(widget_config)
        assert result is True
        
        widgets = sample_user.get_profile_widgets()
        assert len(widgets['widgets']) == 2
        assert widgets['widgets'][0]['id'] == 'recent_posts'
        assert widgets['widgets'][0]['limit'] == 10

    def test_profile_privacy_get_default(self, sample_user):
        """Test getting default profile privacy."""
        privacy = sample_user.get_profile_privacy()
        assert privacy['public_profile'] is True
        assert privacy['show_email'] is False
        assert privacy['show_location'] is True

    def test_profile_privacy_set_privacy(self, sample_user):
        """Test setting profile privacy."""
        privacy_config = {
            'public_profile': False,
            'show_email': True,
            'show_location': False,
            'allow_messages': False,
            'allow_friend_requests': False
        }
        
        result = sample_user.set_profile_privacy(privacy_config)
        assert result is True
        
        privacy = sample_user.get_profile_privacy()
        assert privacy['public_profile'] is False
        assert privacy['show_email'] is True
        assert privacy['show_location'] is False

    def test_profile_can_view_profile_public(self, sample_user):
        """Test viewing public profile."""
        # Set profile as public
        sample_user.set_profile_privacy({'public_profile': True})
        
        # Anyone should be able to view
        assert sample_user.can_view_profile() is True
        assert sample_user.can_view_profile(viewer_id=None) is True

    def test_profile_can_view_profile_private(self, sample_user):
        """Test viewing private profile."""
        # Set profile as private
        sample_user.set_profile_privacy({'public_profile': False})
        
        # No one should be able to view without explicit permission
        assert sample_user.can_view_profile() is False
        assert sample_user.can_view_profile(viewer_id=None) is False

    def test_profile_can_view_profile_self(self, sample_user):
        """Test user can always view own profile."""
        # User should always be able to view their own profile
        assert sample_user.can_view_profile(viewer_id=sample_user.id) is True

    def test_color_scheme_get_default(self, sample_user):
        """Test getting default color scheme."""
        colors = sample_user.get_color_scheme()
        assert 'primary' in colors
        assert 'secondary' in colors
        assert 'background' in colors
        assert colors['primary'] == '#007bff'

    def test_color_scheme_set_colors(self, sample_user):
        """Test setting color scheme."""
        color_config = {
            'primary': '#ff6b6b',
            'secondary': '#4ecdc4',
            'background': '#f8f9fa',
            'text': '#343a40'
        }
        
        result = sample_user.set_color_scheme(color_config)
        assert result is True
        
        colors = sample_user.get_color_scheme()
        assert colors['primary'] == '#ff6b6b'
        assert colors['secondary'] == '#4ecdc4'

    def test_profile_banner_update(self, sample_user):
        """Test updating profile banner."""
        banner_url = 'https://example.com/banner.jpg'
        result = sample_user.update_profile_banner(banner_url)
        assert result is True
        
        assert sample_user.profile_banner_url == banner_url

    def test_profile_banner_get(self, sample_user):
        """Test getting profile banner."""
        # Initially should be None
        assert sample_user.get_profile_banner() is None
        
        # Set banner and test
        banner_url = 'https://example.com/banner.jpg'
        sample_user.update_profile_banner(banner_url)
        
        assert sample_user.get_profile_banner() == banner_url

    def test_reset_customization_all(self, sample_user):
        """Test resetting all customizations."""
        # Set some customizations
        sample_user.set_profile_theme('dark', 'dark')
        sample_user.set_profile_layout({'layout': 'grid'})
        sample_user.set_profile_widgets({'widgets': []})
        sample_user.set_profile_privacy({'public_profile': False})
        sample_user.set_color_scheme({'primary': '#ff0000'})
        
        # Reset all
        sample_user.reset_customization('all')
        
        # Check everything is reset to defaults
        theme = sample_user.get_profile_theme()
        assert theme['theme'] == 'default'
        
        layout = sample_user.get_profile_layout()
        assert layout['layout'] == 'default'
        
        privacy = sample_user.get_profile_privacy()
        assert privacy['public_profile'] is True
        
        colors = sample_user.get_color_scheme()
        assert colors['primary'] == '#007bff'

    def test_reset_customization_specific(self, sample_user):
        """Test resetting specific customizations."""
        # Set multiple customizations
        sample_user.set_profile_theme('dark', 'dark')
        sample_user.set_profile_layout({'layout': 'grid'})
        sample_user.set_profile_privacy({'public_profile': False})
        
        # Reset only theme
        sample_user.reset_customization('theme')
        
        # Check only theme is reset
        theme = sample_user.get_profile_theme()
        assert theme['theme'] == 'default'
        
        layout = sample_user.get_profile_layout()
        assert layout['layout'] == 'grid'
        
        privacy = sample_user.get_profile_privacy()
        assert privacy['public_profile'] is False

    def test_reset_customization_multiple(self, sample_user):
        """Test resetting multiple customizations."""
        # Set multiple customizations
        sample_user.set_profile_theme('dark', 'dark')
        sample_user.set_profile_layout({'layout': 'grid'})
        sample_user.set_profile_privacy({'public_profile': False})
        sample_user.set_color_scheme({'primary': '#ff0000'})
        
        # Reset theme and layout
        sample_user.reset_customization('theme')
        sample_user.reset_customization('layout')
        
        # Check theme and layout are reset
        theme = sample_user.get_profile_theme()
        assert theme['theme'] == 'default'
        
        layout = sample_user.get_profile_layout()
        assert layout['layout'] == 'default'
        
        # Check privacy and colors are not reset
        privacy = sample_user.get_profile_privacy()
        assert privacy['public_profile'] is False
        
        colors = sample_user.get_color_scheme()
        assert colors['primary'] == '#ff0000'


class TestProfileCustomizationForms:
    """Test suite for profile customization forms."""

    def test_profile_theme_form_valid(self):
        """Test valid profile theme form."""
        form = ProfileThemeForm(data={
            'theme': 'dark',
            'skin': 'dark'
        })
        assert form.validate() is True
        assert form.theme.data == 'dark'
        assert form.skin.data == 'dark'

    def test_profile_theme_form_invalid(self):
        """Test invalid profile theme form."""
        form = ProfileThemeForm(data={})
        assert form.validate() is False
        assert 'theme' in form.errors
        assert 'skin' in form.errors

    def test_profile_layout_form_valid(self):
        """Test valid profile layout form."""
        form = ProfileLayoutForm(data={
            'layout_style': 'grid',
            'columns': '3',
            'show_bio': True,
            'show_stats': False
        })
        assert form.validate() is True
        assert form.layout_style.data == 'grid'
        assert form.columns.data == '3'

    def test_profile_layout_form_invalid(self):
        """Test invalid profile layout form."""
        form = ProfileLayoutForm(data={})
        assert form.validate() is False
        assert 'layout_style' in form.errors
        assert 'columns' in form.errors

    def test_profile_widgets_form_valid(self):
        """Test valid profile widgets form."""
        form = ProfileWidgetsForm(data={
            'widget_recent_posts': True,
            'widget_recent_posts_position': 'main',
            'widget_user_stats': False,
            'widget_social_links': True,
            'widget_social_links_position': 'footer'
        })
        assert form.validate() is True
        assert form.widget_recent_posts.data is True
        assert form.widget_user_stats.data is False

    def test_profile_privacy_form_valid(self):
        """Test valid profile privacy form."""
        form = ProfilePrivacyForm(data={
            'public_profile': False,
            'show_email': True,
            'show_location': False,
            'allow_messages': False,
            'allow_friend_requests': False,
            'searchable': False,
            'indexable': False
        })
        assert form.validate() is True
        assert form.public_profile.data is False
        assert form.show_email.data is True

    def test_profile_privacy_form_default(self):
        """Test profile privacy form with defaults."""
        form = ProfilePrivacyForm()
        assert form.public_profile.data is True
        assert form.show_email.data is False
        assert form.show_location.data is True


class TestProfileCustomizationIntegration:
    """Integration tests for profile customization."""

    def test_full_profile_customization_workflow(self, sample_user):
        """Test complete profile customization workflow."""
        # Set theme
        sample_user.set_profile_theme('dark', 'dark')
        theme = sample_user.get_profile_theme()
        assert theme['theme'] == 'dark'
        
        # Set layout
        layout_config = {
            'layout': 'grid',
            'columns': 3,
            'sections': [{'id': 'bio', 'visible': True, 'position': 1}]
        }
        sample_user.set_profile_layout(layout_config)
        layout = sample_user.get_profile_layout()
        assert layout['layout'] == 'grid'
        
        # Set widgets
        widget_config = {
            'widgets': [
                {'id': 'recent_posts', 'enabled': True, 'position': 'main'}
            ]
        }
        sample_user.set_profile_widgets(widget_config)
        widgets = sample_user.get_profile_widgets()
        assert len(widgets['widgets']) == 1
        
        # Set privacy
        privacy_config = {'public_profile': True, 'allow_messages': True}
        sample_user.set_profile_privacy(privacy_config)
        privacy = sample_user.get_profile_privacy()
        assert privacy['public_profile'] is True
        
        # Set colors
        color_config = {'primary': '#ff6b6b', 'secondary': '#4ecdc4'}
        sample_user.set_color_scheme(color_config)
        colors = sample_user.get_color_scheme()
        assert colors['primary'] == '#ff6b6b'
        
        # Test profile visibility
        assert sample_user.can_view_profile() is True

    def test_profile_customization_persistence(self, sample_user):
        """Test that profile customizations persist across sessions."""
        # Set customizations
        sample_user.set_profile_theme('dark', 'dark')
        sample_user.set_profile_layout({'layout': 'grid'})
        
        # Simulate session reload by querying user again
        user_from_db = User.query.get(sample_user.id)
        
        # Check customizations persist
        theme = user_from_db.get_profile_theme()
        assert theme['theme'] == 'dark'
        
        layout = user_from_db.get_profile_layout()
        assert layout['layout'] == 'grid'

    def test_profile_customization_edge_cases(self, sample_user):
        """Test edge cases in profile customization."""
        # Test empty JSON strings
        sample_user.profile_layout = ''
        sample_user.profile_widgets = ''
        sample_user.profile_privacy = ''
        sample_user.profile_color_scheme = ''
        db.session.commit()
        
        # Should return defaults
        layout = sample_user.get_profile_layout()
        assert layout['layout'] == 'default'
        
        widgets = sample_user.get_profile_widgets()
        assert 'widgets' in widgets
        
        privacy = sample_user.get_profile_privacy()
        assert privacy['public_profile'] is True
        
        colors = sample_user.get_color_scheme()
        assert 'primary' in colors
        
        # Test malformed JSON
        sample_user.profile_layout = '{invalid json}'
        db.session.commit()
        
        # Should return defaults
        layout = sample_user.get_profile_layout()
        assert layout['layout'] == 'default'

    def test_profile_customization_performance(self, sample_user):
        """Test performance of profile customization operations."""
        import time
        
        # Test multiple operations
        start_time = time.time()
        
        for i in range(100):
            sample_user.set_profile_theme(f'theme_{i}', 'light')
            sample_user.get_profile_theme()
            sample_user.set_profile_layout({'layout': f'layout_{i}'})
            sample_user.get_profile_layout()
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Should complete 400 operations in reasonable time
        assert operation_time < 2.0, f"Operations took too long: {operation_time}s"
