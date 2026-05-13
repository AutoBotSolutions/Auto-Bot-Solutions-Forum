"""
Advanced Profile Features System

This module implements advanced profile features including themes, customization,
privacy controls, and profile management capabilities.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import User
from app.user.models import UserPreference, UserProfileTheme
import json
import os
from werkzeug.utils import secure_filename


class AdvancedProfileManager:
    """Advanced profile management system with themes, customization, and privacy controls"""
    
    @staticmethod
    def get_profile_theme(user_id):
        """Get user's profile theme"""
        theme_preference = UserPreference.get_preference(user_id, 'profile_theme')
        if theme_preference:
            try:
                theme_data = json.loads(theme_preference)
                return theme_data
            except:
                pass
        
        # Return default theme
        return {
            'theme_name': 'default',
            'skin_variant': 'light',
            'css_variables': {},
            'layout_config': {}
        }
    
    @staticmethod
    def set_profile_theme(user_id, theme_name, skin_variant='light', css_variables=None, layout_config=None):
        """Set user's profile theme"""
        theme_data = {
            'theme_name': theme_name,
            'skin_variant': skin_variant,
            'css_variables': css_variables or {},
            'layout_config': layout_config or {},
            'updated_at': datetime.utcnow().isoformat()
        }
        
        UserPreference.set_preference(user_id, 'profile_theme', json.dumps(theme_data))
        return theme_data
    
    @staticmethod
    def get_profile_layout(user_id):
        """Get user's profile layout configuration"""
        layout_preference = UserPreference.get_preference(user_id, 'profile_layout')
        if layout_preference:
            try:
                layout_data = json.loads(layout_preference)
                return layout_data
            except:
                pass
        
        # Return default layout
        return {
            'layout_type': 'grid',
            'columns': 2,
            'sidebar_position': 'right',
            'widget_positions': {},
            'responsive_breakpoints': {
                'mobile': 1,
                'tablet': 2,
                'desktop': 3
            }
        }
    
    @staticmethod
    def set_profile_layout(user_id, layout_type, columns=2, sidebar_position='right', widget_positions=None, responsive_breakpoints=None):
        """Set user's profile layout"""
        layout_data = {
            'layout_type': layout_type,
            'columns': columns,
            'sidebar_position': sidebar_position,
            'widget_positions': widget_positions or {},
            'responsive_breakpoints': responsive_breakpoints or {
                'mobile': 1,
                'tablet': 2,
                'desktop': 3
            },
            'updated_at': datetime.utcnow().isoformat()
        }
        
        UserPreference.set_preference(user_id, 'profile_layout', json.dumps(layout_data))
        return layout_data
    
    @staticmethod
    def get_profile_widgets(user_id):
        """Get user's profile widget configuration"""
        widgets_preference = UserPreference.get_preference(user_id, 'profile_widgets')
        if widgets_preference:
            try:
                widgets_data = json.loads(widgets_preference)
                return widgets_data
            except:
                pass
        
        # Return default widgets
        return {
            'enabled_widgets': ['bio', 'recent_posts', 'social_links', 'stats'],
            'widget_order': ['bio', 'stats', 'recent_posts', 'social_links'],
            'widget_settings': {
                'bio': {'expanded': True, 'max_length': 500},
                'recent_posts': {'count': 5, 'show_date': True},
                'social_links': {'show_count': True},
                'stats': {'show_engagement': True}
            }
        }
    
    @staticmethod
    def set_profile_widgets(user_id, enabled_widgets=None, widget_order=None, widget_settings=None):
        """Set user's profile widgets"""
        widgets_data = {
            'enabled_widgets': enabled_widgets or ['bio', 'recent_posts', 'social_links', 'stats'],
            'widget_order': widget_order or ['bio', 'stats', 'recent_posts', 'social_links'],
            'widget_settings': widget_settings or {
                'bio': {'expanded': True, 'max_length': 500},
                'recent_posts': {'count': 5, 'show_date': True},
                'social_links': {'show_count': True},
                'stats': {'show_engagement': True}
            },
            'updated_at': datetime.utcnow().isoformat()
        }
        
        UserPreference.set_preference(user_id, 'profile_widgets', json.dumps(widgets_data))
        return widgets_data
    
    @staticmethod
    def get_profile_privacy(user_id):
        """Get user's profile privacy settings"""
        privacy_preference = UserPreference.get_preference(user_id, 'profile_privacy')
        if privacy_preference:
            try:
                privacy_data = json.loads(privacy_preference)
                return privacy_data
            except:
                pass
        
        # Return default privacy settings
        return {
            'profile_visibility': 'public',
            'email_visibility': 'public',
            'location_visibility': 'public',
            'website_visibility': 'public',
            'bio_visibility': 'public',
            'search_visibility': 'enabled',
            'social_links_visibility': 'public',
            'activity_visibility': 'public',
            'message_permissions': 'friends',
            'connection_requests': 'enabled'
        }
    
    @staticmethod
    def set_profile_privacy(user_id, privacy_settings):
        """Set user's profile privacy settings"""
        current_privacy = AdvancedProfileManager.get_profile_privacy(user_id)
        current_privacy.update(privacy_settings)
        current_privacy['updated_at'] = datetime.utcnow().isoformat()
        
        UserPreference.set_preference(user_id, 'profile_privacy', json.dumps(current_privacy))
        return current_privacy
    
    @staticmethod
    def get_color_scheme(user_id):
        """Get user's color scheme"""
        color_preference = UserPreference.get_preference(user_id, 'color_scheme')
        if color_preference:
            try:
                color_data = json.loads(color_preference)
                return color_data
            except:
                pass
        
        # Return default color scheme
        return {
            'primary_color': '#007bff',
            'secondary_color': '#6c757d',
            'accent_color': '#28a745',
            'background_color': '#ffffff',
            'text_color': '#333333',
            'link_color': '#007bff',
            'border_color': '#dee2e6',
            'custom_colors': {}
        }
    
    @staticmethod
    def set_color_scheme(user_id, color_scheme):
        """Set user's color scheme"""
        current_scheme = AdvancedProfileManager.get_color_scheme(user_id)
        current_scheme.update(color_scheme)
        current_scheme['updated_at'] = datetime.utcnow().isoformat()
        
        UserPreference.set_preference(user_id, 'color_scheme', json.dumps(current_scheme))
        return current_scheme
    
    @staticmethod
    def upload_profile_banner(user_id, banner_file):
        """Upload profile banner image"""
        if not banner_file:
            return {'success': False, 'message': 'No file provided'}
        
        # Validate file
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in banner_file.filename and 
                banner_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return {'success': False, 'message': 'Invalid file type'}
        
        # Generate secure filename
        filename = secure_filename(banner_file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        banner_filename = f"banner_{user_id}_{timestamp}_{filename}"
        
        # Save file
        upload_path = current_app.config.get('PROFILE_UPLOAD_PATH', 'uploads/profiles')
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        
        file_path = os.path.join(upload_path, banner_filename)
        banner_file.save(file_path)
        
        # Update user profile
        banner_url = f"/uploads/profiles/{banner_filename}"
        user = User.query.get(user_id)
        if user:
            user.banner_url = banner_url
            db.session.commit()
        
        return {
            'success': True,
            'message': 'Banner uploaded successfully',
            'banner_url': banner_url,
            'filename': banner_filename
        }
    
    @staticmethod
    def remove_profile_banner(user_id):
        """Remove profile banner image"""
        user = User.query.get(user_id)
        if user and user.banner_url:
            # Delete file if it exists
            file_path = os.path.join(current_app.config.get('PROFILE_UPLOAD_PATH', 'uploads/profiles'), 
                                    os.path.basename(user.banner_url))
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Update user profile
            user.banner_url = None
            db.session.commit()
            
            return {'success': True, 'message': 'Banner removed successfully'}
        
        return {'success': False, 'message': 'No banner to remove'}
    
    @staticmethod
    def get_profile_sections(user_id):
        """Get user's profile section configuration"""
        sections_preference = UserPreference.get_preference(user_id, 'profile_sections')
        if sections_preference:
            try:
                sections_data = json.loads(sections_preference)
                return sections_data
            except:
                pass
        
        # Return default sections
        return {
            'enabled_sections': ['about', 'contact', 'social', 'activity'],
            'section_order': ['about', 'social', 'activity', 'contact'],
            'section_settings': {
                'about': {'expanded': True, 'show_bio': True, 'show_location': True},
                'contact': {'expanded': False, 'show_email': False, 'show_phone': False},
                'social': {'expanded': True, 'show_links': True, 'show_stats': True},
                'activity': {'expanded': True, 'show_posts': True, 'show_comments': True}
            }
        }
    
    @staticmethod
    def set_profile_sections(user_id, enabled_sections=None, section_order=None, section_settings=None):
        """Set user's profile section configuration"""
        sections_data = {
            'enabled_sections': enabled_sections or ['about', 'contact', 'social', 'activity'],
            'section_order': section_order or ['about', 'social', 'activity', 'contact'],
            'section_settings': section_settings or {
                'about': {'expanded': True, 'show_bio': True, 'show_location': True},
                'contact': {'expanded': False, 'show_email': False, 'show_phone': False},
                'social': {'expanded': True, 'show_links': True, 'show_stats': True},
                'activity': {'expanded': True, 'show_posts': True, 'show_comments': True}
            },
            'updated_at': datetime.utcnow().isoformat()
        }
        
        UserPreference.set_preference(user_id, 'profile_sections', json.dumps(sections_data))
        return sections_data
    
    @staticmethod
    def get_complete_profile_config(user_id):
        """Get complete profile configuration"""
        return {
            'theme': AdvancedProfileManager.get_profile_theme(user_id),
            'layout': AdvancedProfileManager.get_profile_layout(user_id),
            'widgets': AdvancedProfileManager.get_profile_widgets(user_id),
            'privacy': AdvancedProfileManager.get_profile_privacy(user_id),
            'color_scheme': AdvancedProfileManager.get_color_scheme(user_id),
            'sections': AdvancedProfileManager.get_profile_sections(user_id)
        }
    
    @staticmethod
    def reset_profile_customization(user_id):
        """Reset all profile customization to defaults"""
        # Reset all preferences to defaults
        defaults = {
            'profile_theme': json.dumps({
                'theme_name': 'default',
                'skin_variant': 'light',
                'css_variables': {},
                'layout_config': {}
            }),
            'profile_layout': json.dumps({
                'layout_type': 'grid',
                'columns': 2,
                'sidebar_position': 'right',
                'widget_positions': {},
                'responsive_breakpoints': {'mobile': 1, 'tablet': 2, 'desktop': 3}
            }),
            'profile_widgets': json.dumps({
                'enabled_widgets': ['bio', 'recent_posts', 'social_links', 'stats'],
                'widget_order': ['bio', 'stats', 'recent_posts', 'social_links'],
                'widget_settings': {
                    'bio': {'expanded': True, 'max_length': 500},
                    'recent_posts': {'count': 5, 'show_date': True},
                    'social_links': {'show_count': True},
                    'stats': {'show_engagement': True}
                }
            }),
            'profile_privacy': json.dumps({
                'profile_visibility': 'public',
                'email_visibility': 'public',
                'location_visibility': 'public',
                'website_visibility': 'public',
                'bio_visibility': 'public',
                'search_visibility': 'enabled',
                'social_links_visibility': 'public',
                'activity_visibility': 'public',
                'message_permissions': 'friends',
                'connection_requests': 'enabled'
            }),
            'color_scheme': json.dumps({
                'primary_color': '#007bff',
                'secondary_color': '#6c757d',
                'accent_color': '#28a745',
                'background_color': '#ffffff',
                'text_color': '#333333',
                'link_color': '#007bff',
                'border_color': '#dee2e6',
                'custom_colors': {}
            }),
            'profile_sections': json.dumps({
                'enabled_sections': ['about', 'contact', 'social', 'activity'],
                'section_order': ['about', 'social', 'activity', 'contact'],
                'section_settings': {
                    'about': {'expanded': True, 'show_bio': True, 'show_location': True},
                    'contact': {'expanded': False, 'show_email': False, 'show_phone': False},
                    'social': {'expanded': True, 'show_links': True, 'show_stats': True},
                    'activity': {'expanded': True, 'show_posts': True, 'show_comments': True}
                }
            })
        }
        
        for preference_type, value in defaults.items():
            UserPreference.set_preference(user_id, preference_type, value)
        
        # Remove banner if exists
        AdvancedProfileManager.remove_profile_banner(user_id)
        
        return {'success': True, 'message': 'Profile customization reset to defaults'}
    
    @staticmethod
    def get_profile_analytics(user_id, days=30):
        """Get profile analytics for a user"""
        from app.user.models import UserAnalytics
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get profile views
        profile_views = UserAnalytics.query.filter(
            UserAnalytics.user_id == user_id,
            UserAnalytics.metric_type == 'profile_view',
            UserAnalytics.timestamp >= start_date,
            UserAnalytics.timestamp <= end_date
        ).count()
        
        # Get profile interactions
        profile_interactions = UserAnalytics.query.filter(
            UserAnalytics.user_id == user_id,
            UserAnalytics.metric_type.in_(['profile_like', 'profile_share', 'profile_follow']),
            UserAnalytics.timestamp >= start_date,
            UserAnalytics.timestamp <= end_date
        ).all()
        
        interactions_by_type = {}
        for interaction in profile_interactions:
            if interaction.metric_type not in interactions_by_type:
                interactions_by_type[interaction.metric_type] = 0
            interactions_by_type[interaction.metric_type] += 1
        
        return {
            'period': f'{days} days',
            'profile_views': profile_views,
            'total_interactions': len(profile_interactions),
            'interactions_by_type': interactions_by_type,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    
    @staticmethod
    def can_view_profile(viewer_id, profile_owner_id):
        """Check if a user can view another user's profile"""
        if viewer_id == profile_owner_id:
            return True
        
        # Get profile owner's privacy settings
        privacy = AdvancedProfileManager.get_profile_privacy(profile_owner_id)
        profile_visibility = privacy.get('profile_visibility', 'public')
        
        if profile_visibility == 'public':
            return True
        elif profile_visibility == 'friends':
            from app.user.models import UserSocialConnection
            return UserSocialConnection.is_connected(viewer_id, profile_owner_id, 'friend')
        elif profile_visibility == 'followers':
            from app.user.models import UserSocialConnection
            return UserSocialConnection.is_connected(viewer_id, profile_owner_id, 'follow')
        elif profile_visibility == 'private':
            return False
        
        return True
    
    @staticmethod
    def get_profile_visibility_settings(user_id):
        """Get detailed visibility settings for a user"""
        privacy = AdvancedProfileManager.get_profile_privacy(user_id)
        
        return {
            'profile_visibility': privacy.get('profile_visibility', 'public'),
            'email_visibility': privacy.get('email_visibility', 'public'),
            'location_visibility': privacy.get('location_visibility', 'public'),
            'website_visibility': privacy.get('website_visibility', 'public'),
            'bio_visibility': privacy.get('bio_visibility', 'public'),
            'search_visibility': privacy.get('search_visibility', 'enabled'),
            'social_links_visibility': privacy.get('social_links_visibility', 'public'),
            'activity_visibility': privacy.get('activity_visibility', 'public'),
            'message_permissions': privacy.get('message_permissions', 'friends'),
            'connection_requests': privacy.get('connection_requests', 'enabled')
        }
    
    @staticmethod
    def update_profile_visibility(user_id, visibility_settings):
        """Update profile visibility settings"""
        return AdvancedProfileManager.set_profile_privacy(user_id, visibility_settings)
    
    @staticmethod
    def get_profile_css_variables(user_id):
        """Get CSS variables for user's profile theme"""
        theme = AdvancedProfileManager.get_profile_theme(user_id)
        color_scheme = AdvancedProfileManager.get_color_scheme(user_id)
        
        # Merge theme and color scheme CSS variables
        css_variables = {}
        css_variables.update(theme.get('css_variables', {}))
        css_variables.update(color_scheme.get('custom_colors', {}))
        
        # Add color scheme variables
        css_variables.update({
            '--primary-color': color_scheme.get('primary_color', '#007bff'),
            '--secondary-color': color_scheme.get('secondary_color', '#6c757d'),
            '--accent-color': color_scheme.get('accent_color', '#28a745'),
            '--background-color': color_scheme.get('background_color', '#ffffff'),
            '--text-color': color_scheme.get('text_color', '#333333'),
            '--link-color': color_scheme.get('link_color', '#007bff'),
            '--border-color': color_scheme.get('border_color', '#dee2e6')
        })
        
        return css_variables
    
    @staticmethod
    def export_profile_config(user_id):
        """Export user's complete profile configuration"""
        config = AdvancedProfileManager.get_complete_profile_config(user_id)
        
        # Add user info
        user = User.query.get(user_id)
        if user:
            config['user_info'] = {
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'banner_url': user.banner_url
            }
        
        # Add export metadata
        config['export_metadata'] = {
            'exported_at': datetime.utcnow().isoformat(),
            'exported_by': user_id,
            'version': '1.0'
        }
        
        return config
    
    @staticmethod
    def import_profile_config(user_id, config_data):
        """Import profile configuration"""
        try:
            # Validate config data
            required_sections = ['theme', 'layout', 'widgets', 'privacy', 'color_scheme']
            for section in required_sections:
                if section not in config_data:
                    return {'success': False, 'message': f'Missing required section: {section}'}
            
            # Import each section
            AdvancedProfileManager.set_profile_theme(
                user_id,
                config_data['theme'].get('theme_name', 'default'),
                config_data['theme'].get('skin_variant', 'light'),
                config_data['theme'].get('css_variables', {}),
                config_data['theme'].get('layout_config', {})
            )
            
            AdvancedProfileManager.set_profile_layout(
                user_id,
                config_data['layout'].get('layout_type', 'grid'),
                config_data['layout'].get('columns', 2),
                config_data['layout'].get('sidebar_position', 'right'),
                config_data['layout'].get('widget_positions', {}),
                config_data['layout'].get('responsive_breakpoints', {})
            )
            
            AdvancedProfileManager.set_profile_widgets(
                user_id,
                config_data['widgets'].get('enabled_widgets'),
                config_data['widgets'].get('widget_order'),
                config_data['widgets'].get('widget_settings')
            )
            
            AdvancedProfileManager.set_profile_privacy(user_id, config_data['privacy'])
            
            AdvancedProfileManager.set_color_scheme(user_id, config_data['color_scheme'])
            
            return {'success': True, 'message': 'Profile configuration imported successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Import failed: {str(e)}'}


class ProfileThemeManager:
    """Profile theme management system"""
    
    @staticmethod
    def create_theme(name, display_name, description=None, css_variables=None, layout_config=None, is_system_theme=False):
        """Create a new profile theme"""
        theme = UserProfileTheme.create_theme(
            name=name,
            display_name=display_name,
            description=description,
            css_variables=css_variables or {},
            layout_config=layout_config or {},
            is_system_theme=is_system_theme
        )
        return theme
    
    @staticmethod
    def get_theme_by_name(name):
        """Get theme by name"""
        return UserProfileTheme.get_theme_by_name(name)
    
    @staticmethod
    def get_all_themes(active_only=True):
        """Get all available themes"""
        return UserProfileTheme.get_all_themes(active_only)
    
    @staticmethod
    def get_system_themes():
        """Get all system themes"""
        return UserProfileTheme.get_system_themes()
    
    @staticmethod
    def update_theme(theme_id, **kwargs):
        """Update theme properties"""
        theme = UserProfileTheme.get_theme(theme_id)
        if theme:
            return theme.update_theme(**kwargs)
        return None
    
    @staticmethod
    def delete_theme(theme_id):
        """Delete a theme"""
        theme = UserProfileTheme.get_theme(theme_id)
        if theme and not theme.is_system_theme:
            db.session.delete(theme)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_theme_css(theme_name):
        """Get CSS for a specific theme"""
        theme = ProfileThemeManager.get_theme_by_name(theme_name)
        if not theme:
            return ''
        
        # Generate CSS from theme configuration
        css_variables = theme.css_variables or {}
        css = f'/* Theme: {theme.display_name} */\n'
        css += ':root {\n'
        
        for var_name, var_value in css_variables.items():
            css += f'  --{var_name}: {var_value};\n'
        
        css += '}\n'
        
        return css


class ProfileAnalyticsManager:
    """Profile analytics and metrics management"""
    
    @staticmethod
    def track_profile_view(user_id, viewer_id=None, ip_address=None, user_agent=None):
        """Track profile view"""
        from app.user.models import UserAnalytics
        
        metadata = {
            'viewer_id': viewer_id,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        return UserAnalytics.track_metric(
            user_id=user_id,
            metric_type='profile_view',
            value=1,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def track_profile_interaction(user_id, interaction_type, target_user_id=None, metadata=None):
        """Track profile interaction"""
        from app.user.models import UserAnalytics
        
        interaction_data = {
            'target_user_id': target_user_id,
            **(metadata or {})
        }
        
        return UserAnalytics.track_metric(
            user_id=user_id,
            metric_type=interaction_type,
            value=1,
            metadata=interaction_data
        )
    
    @staticmethod
    def get_profile_performance_metrics(user_id, days=30):
        """Get profile performance metrics"""
        from app.user.models import UserAnalytics
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all profile-related metrics
        metrics = UserAnalytics.query.filter(
            UserAnalytics.user_id == user_id,
            UserAnalytics.timestamp >= start_date,
            UserAnalytics.timestamp <= end_date,
            UserAnalytics.metric_type.in_(['profile_view', 'profile_like', 'profile_share', 'profile_follow'])
        ).all()
        
        # Calculate metrics
        total_views = len([m for m in metrics if m.metric_type == 'profile_view'])
        total_likes = len([m for m in metrics if m.metric_type == 'profile_like'])
        total_shares = len([m for m in metrics if m.metric_type == 'profile_share'])
        total_follows = len([m for m in metrics if m.metric_type == 'profile_follow'])
        
        return {
            'period': f'{days} days',
            'total_views': total_views,
            'total_likes': total_likes,
            'total_shares': total_shares,
            'total_follows': total_follows,
            'engagement_rate': (total_likes + total_shares + total_follows) / total_views * 100 if total_views > 0 else 0,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    
    @staticmethod
    def get_profile_trends(user_id, days=30):
        """Get profile trends over time"""
        from app.user.models import UserAnalytics
        from sqlalchemy import func, extract
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily profile views
        daily_views = db.session.query(
            extract('day', UserAnalytics.timestamp).label('date'),
            func.count(UserAnalytics.id).label('views')
        ).filter(
            UserAnalytics.user_id == user_id,
            UserAnalytics.metric_type == 'profile_view',
            UserAnalytics.timestamp >= start_date,
            UserAnalytics.timestamp <= end_date
        ).group_by(extract('day', UserAnalytics.timestamp)).all()
        
        # Format for chart
        dates = []
        views = []
        
        for day, count in daily_views:
            dates.append(day.isoformat())
            views.append(count)
        
        return {
            'dates': dates,
            'views': views,
            'period': f'{days} days'
        }
