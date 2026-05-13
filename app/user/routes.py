from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from app import db
from app.models import User, Post, Comment

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).limit(10).all()
    comments = Comment.query.filter_by(user_id=user.id).order_by(Comment.created_at.desc()).limit(10).all()
    total_posts = Post.query.filter_by(user_id=user.id).count()
    total_comments = Comment.query.filter_by(user_id=user.id).count()
    
    return render_template('user/profile.html', 
                          user=user, 
                          posts=posts, 
                          comments=comments,
                          total_posts=total_posts,
                          total_comments=total_comments)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    from app.user.forms import EditProfileForm
    form = EditProfileForm(current_user.username, current_user.email)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.profile', username=current_user.username))
    
    return render_template('user/edit_profile.html', form=form)

# Advanced Profile Customization Routes

@user_bp.route('/profile/customization')
@login_required
def profile_customization():
    """Main profile customization dashboard"""
    return render_template('user/profile_customization.html', 
                         theme=current_user.get_profile_theme(),
                         layout=current_user.get_profile_layout(),
                         widgets=current_user.get_profile_widgets(),
                         privacy=current_user.get_profile_privacy(),
                         colors=current_user.get_color_scheme())

@user_bp.route('/profile/theme', methods=['GET', 'POST'])
@login_required
def profile_theme():
    """Profile theme customization"""
    from app.user.forms import ProfileThemeForm
    form = ProfileThemeForm()
    
    if form.validate_on_submit():
        current_user.set_profile_theme(form.theme.data, form.skin.data)
        db.session.commit()
        flash('Profile theme updated successfully!', 'success')
        return redirect(url_for('user.profile_customization'))
    
    # Pre-fill current values
    form.theme.data = current_user.profile_theme or 'default'
    form.skin.data = current_user.profile_skin or 'light'
    
    return render_template('user/profile_theme.html', form=form)

@user_bp.route('/profile/banner', methods=['GET', 'POST'])
@login_required
def profile_banner():
    """Profile banner customization"""
    from app.user.forms import ProfileBannerForm
    form = ProfileBannerForm()
    
    if form.validate_on_submit():
        # Handle file upload
        if form.banner_file.data:
            filename = secure_filename(form.banner_file.data.filename)
            if filename:
                # Create upload directory if it doesn't exist
                upload_dir = os.path.join(current_app.static_folder, 'uploads', 'banners')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save file with unique name
                unique_filename = f"user_{current_user.id}_{filename}"
                file_path = os.path.join(upload_dir, unique_filename)
                form.banner_file.data.save(file_path)
                
                # Update banner URL
                banner_url = url_for('static', filename=f'uploads/banners/{unique_filename}')
                current_user.update_profile_banner(banner_url)
        
        # Handle URL input
        elif form.banner_url.data:
            current_user.update_profile_banner(form.banner_url.data)
        
        db.session.commit()
        flash('Profile banner updated successfully!', 'success')
        return redirect(url_for('user.profile_customization'))
    
    return render_template('user/profile_banner.html', form=form)

@user_bp.route('/profile/layout', methods=['GET', 'POST'])
@login_required
def profile_layout():
    """Profile layout customization"""
    from app.user.forms import ProfileLayoutForm
    form = ProfileLayoutForm()
    
    if form.validate_on_submit():
        current_layout = current_user.get_profile_layout()
        
        # Update layout configuration
        layout_config = {
            'layout': form.layout_style.data,
            'columns': int(form.columns.data),
            'sections': current_layout.get('sections', [])
        }
        
        # Update section visibility
        for section in layout_config['sections']:
            if section['id'] == 'bio':
                section['visible'] = form.show_bio.data
            elif section['id'] == 'stats':
                section['visible'] = form.show_stats.data
            elif section['id'] == 'activity':
                section['visible'] = form.show_activity.data
            elif section['id'] == 'badges':
                section['visible'] = form.show_badges.data
            elif section['id'] == 'social_links':
                section['visible'] = form.show_social_links.data
        
        current_user.set_profile_layout(layout_config)
        db.session.commit()
        flash('Profile layout updated successfully!', 'success')
        return redirect(url_for('user.profile_customization'))
    
    # Pre-fill current values
    current_layout = current_user.get_profile_layout()
    form.layout_style.data = current_layout.get('layout', 'default')
    form.columns.data = str(current_layout.get('columns', 2))
    
    # Set section visibility
    for section in current_layout.get('sections', []):
        if section['id'] == 'bio':
            form.show_bio.data = section.get('visible', True)
        elif section['id'] == 'stats':
            form.show_stats.data = section.get('visible', True)
        elif section['id'] == 'activity':
            form.show_activity.data = section.get('visible', True)
        elif section['id'] == 'badges':
            form.show_badges.data = section.get('visible', True)
        elif section['id'] == 'social_links':
            form.show_social_links.data = section.get('visible', True)
    
    return render_template('user/profile_layout.html', form=form)

@user_bp.route('/profile/widgets', methods=['GET', 'POST'])
@login_required
def profile_widgets():
    """Profile widget customization"""
    from app.user.forms import ProfileWidgetsForm
    form = ProfileWidgetsForm()
    
    if form.validate_on_submit():
        widgets_config = {
            'widgets': [
                {
                    'id': 'recent_posts',
                    'enabled': form.widget_recent_posts.data,
                    'position': form.widget_recent_posts_position.data
                },
                {
                    'id': 'recent_comments',
                    'enabled': form.widget_recent_comments.data,
                    'position': form.widget_recent_comments_position.data
                },
                {
                    'id': 'user_stats',
                    'enabled': form.widget_user_stats.data,
                    'position': form.widget_user_stats_position.data
                },
                {
                    'id': 'social_links',
                    'enabled': form.widget_social_links.data,
                    'position': form.widget_social_links_position.data
                },
                {
                    'id': 'custom_text',
                    'enabled': form.widget_custom_text.data,
                    'position': form.widget_custom_text_position.data,
                    'content': form.widget_custom_text_content.data
                }
            ]
        }
        
        current_user.set_profile_widgets(widgets_config)
        db.session.commit()
        flash('Profile widgets updated successfully!', 'success')
        return redirect(url_for('user.profile_customization'))
    
    # Pre-fill current values
    current_widgets = current_user.get_profile_widgets()
    for widget in current_widgets.get('widgets', []):
        if widget['id'] == 'recent_posts':
            form.widget_recent_posts.data = widget.get('enabled', True)
            form.widget_recent_posts_position.data = widget.get('position', 'sidebar')
        elif widget['id'] == 'recent_comments':
            form.widget_recent_comments.data = widget.get('enabled', True)
            form.widget_recent_comments_position.data = widget.get('position', 'sidebar')
        elif widget['id'] == 'user_stats':
            form.widget_user_stats.data = widget.get('enabled', True)
            form.widget_user_stats_position.data = widget.get('position', 'main')
        elif widget['id'] == 'social_links':
            form.widget_social_links.data = widget.get('enabled', True)
            form.widget_social_links_position.data = widget.get('position', 'footer')
        elif widget['id'] == 'custom_text':
            form.widget_custom_text.data = widget.get('enabled', False)
            form.widget_custom_text_content.data = widget.get('content', '')
            form.widget_custom_text_position.data = widget.get('position', 'sidebar')
    
    return render_template('user/profile_widgets.html', form=form)

@user_bp.route('/profile/privacy', methods=['GET', 'POST'])
@login_required
def profile_privacy():
    """Profile privacy settings"""
    from app.user.forms import ProfilePrivacyForm
    form = ProfilePrivacyForm()
    
    if form.validate_on_submit():
        privacy_config = {
            'public_profile': form.public_profile.data,
            'show_email': form.show_email.data,
            'show_location': form.show_location.data,
            'show_website': form.show_website.data,
            'show_bio': form.show_bio.data,
            'show_activity': form.show_activity.data,
            'show_stats': form.show_stats.data,
            'show_badges': form.show_badges.data,
            'allow_messages': form.allow_messages.data,
            'allow_friend_requests': form.allow_friend_requests.data,
            'searchable': form.searchable.data,
            'indexable': form.indexable.data
        }
        
        current_user.set_profile_privacy(privacy_config)
        db.session.commit()
        flash('Profile privacy settings updated successfully!', 'success')
        return redirect(url_for('user.profile_customization'))
    
    # Pre-fill current values
    current_privacy = current_user.get_profile_privacy()
    form.public_profile.data = current_privacy.get('public_profile', True)
    form.show_email.data = current_privacy.get('show_email', False)
    form.show_location.data = current_privacy.get('show_location', True)
    form.show_website.data = current_privacy.get('show_website', True)
    form.show_bio.data = current_privacy.get('show_bio', True)
    form.show_activity.data = current_privacy.get('show_activity', True)
    form.show_stats.data = current_privacy.get('show_stats', True)
    form.show_badges.data = current_privacy.get('show_badges', True)
    form.allow_messages.data = current_privacy.get('allow_messages', True)
    form.allow_friend_requests.data = current_privacy.get('allow_friend_requests', True)
    form.searchable.data = current_privacy.get('searchable', True)
    form.indexable.data = current_privacy.get('indexable', True)
    
    return render_template('user/profile_privacy.html', form=form)

@user_bp.route('/profile/colors', methods=['GET', 'POST'])
@login_required
def profile_colors():
    """Profile color scheme customization"""
    from app.user.forms import ProfileColorSchemeForm
    form = ProfileColorSchemeForm()
    
    if form.validate_on_submit():
        color_config = {
            'primary': form.primary_color.data or '#007bff',
            'secondary': form.secondary_color.data or '#6c757d',
            'accent': form.accent_color.data or '#17a2b8',
            'background': form.background_color.data or '#ffffff',
            'text': form.text_color.data or '#212529',
            'link': form.link_color.data or '#007bff',
            'border': form.border_color.data or '#dee2e6'
        }
        
        current_user.set_color_scheme(color_config)
        
        # Handle custom CSS
        if form.custom_css.data:
            current_user.update_custom_css(form.custom_css.data)
        
        db.session.commit()
        flash('Profile color scheme updated successfully!', 'success')
        return redirect(url_for('user.profile_customization'))
    
    # Pre-fill current values
    current_colors = current_user.get_color_scheme()
    form.primary_color.data = current_colors.get('primary', '#007bff')
    form.secondary_color.data = current_colors.get('secondary', '#6c757d')
    form.accent_color.data = current_colors.get('accent', '#17a2b8')
    form.background_color.data = current_colors.get('background', '#ffffff')
    form.text_color.data = current_colors.get('text', '#212529')
    form.link_color.data = current_colors.get('link', '#007bff')
    form.border_color.data = current_colors.get('border', '#dee2e6')
    form.custom_css.data = current_user.profile_custom_css
    
    return render_template('user/profile_colors.html', form=form)

@user_bp.route('/profile/reset', methods=['GET', 'POST'])
@login_required
def profile_reset():
    """Reset profile customization"""
    from app.user.forms import ProfileResetForm
    form = ProfileResetForm()
    
    if form.validate_on_submit():
        if form.reset_theme.data:
            current_user.profile_theme = 'default'
            current_user.profile_skin = 'light'
        
        if form.reset_layout.data:
            current_user.profile_layout = None
        
        if form.reset_widgets.data:
            current_user.profile_widgets = None
        
        if form.reset_privacy.data:
            current_user.profile_privacy = None
        
        if form.reset_colors.data:
            current_user.profile_color_scheme = None
        
        if form.reset_css.data:
            current_user.profile_custom_css = None
        
        current_user.updated_at = current_user.__class__.updated_at.default.arg
        db.session.commit()
        flash('Selected profile customizations have been reset to defaults!', 'success')
        return redirect(url_for('user.profile_customization'))
    
    return render_template('user/profile_reset.html', form=form)

# User Preference System Routes

@user_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def user_preferences():
    """Main user preferences dashboard"""
    return render_template('user/preferences.html')

@user_bp.route('/preferences/general', methods=['GET', 'POST'])
@login_required
def general_preferences():
    """General user preferences"""
    from app.user.forms import UserPreferencesForm
    form = UserPreferencesForm()
    
    if form.validate_on_submit():
        # Store preferences in JSON format
        preferences = {
            'theme_preference': form.theme_preference.data,
            'language_preference': form.language_preference.data,
            'timezone': form.timezone.data,
            'date_format': form.date_format.data,
            'time_format': form.time_format.data,
            'email_notifications': form.email_notifications.data,
            'push_notifications': form.push_notifications.data,
            'desktop_notifications': form.desktop_notifications.data,
            'show_sensitive_content': form.show_sensitive_content.data,
            'auto_play_videos': form.auto_play_videos.data,
            'show_avatars': form.show_avatars.data,
            'show_signatures': form.show_signatures.data,
            'show_online_status': form.show_online_status.data,
            'allow_tagging': form.allow_tagging.data,
            'allow_mentions': form.allow_mentions.data
        }
        
        # Store in a user preferences field (we'll need to add this to the model)
        current_user.user_preferences = json.dumps(preferences)
        db.session.commit()
        flash('General preferences updated successfully!', 'success')
        return redirect(url_for('user.user_preferences'))
    
    # Load current preferences if they exist
    if hasattr(current_user, 'user_preferences') and current_user.user_preferences:
        try:
            preferences = json.loads(current_user.user_preferences)
            form.theme_preference.data = preferences.get('theme_preference', 'light')
            form.language_preference.data = preferences.get('language_preference', 'en')
            form.timezone.data = preferences.get('timezone', 'UTC')
            form.date_format.data = preferences.get('date_format', 'MM/DD/YYYY')
            form.time_format.data = preferences.get('time_format', '12-hour')
            form.email_notifications.data = preferences.get('email_notifications', True)
            form.push_notifications.data = preferences.get('push_notifications', True)
            form.desktop_notifications.data = preferences.get('desktop_notifications', True)
            form.show_sensitive_content.data = preferences.get('show_sensitive_content', False)
            form.auto_play_videos.data = preferences.get('auto_play_videos', True)
            form.show_avatars.data = preferences.get('show_avatars', True)
            form.show_signatures.data = preferences.get('show_signatures', True)
            form.show_online_status.data = preferences.get('show_online_status', True)
            form.allow_tagging.data = preferences.get('allow_tagging', True)
            form.allow_mentions.data = preferences.get('allow_mentions', True)
        except:
            pass  # Use defaults
    
    return render_template('user/general_preferences.html', form=form)

@user_bp.route('/preferences/notifications', methods=['GET', 'POST'])
@login_required
def notification_preferences():
    """Notification preferences"""
    from app.user.forms import NotificationPreferencesForm
    form = NotificationPreferencesForm()
    
    if form.validate_on_submit():
        # Store notification preferences
        notification_prefs = {
            'email': {
                'new_follower': form.email_new_follower.data,
                'new_message': form.email_new_message.data,
                'post_reply': form.email_post_reply.data,
                'comment_reply': form.email_comment_reply.data,
                'mention': form.email_mention.data,
                'badge_earned': form.email_badge_earned.data,
                'system_updates': form.email_system_updates.data
            },
            'push': {
                'new_follower': form.push_new_follower.data,
                'new_message': form.push_new_message.data,
                'post_reply': form.push_post_reply.data,
                'comment_reply': form.push_comment_reply.data,
                'mention': form.push_mention.data,
                'badge_earned': form.push_badge_earned.data,
                'system_updates': form.push_system_updates.data
            },
            'inapp': {
                'new_follower': form.inapp_new_follower.data,
                'new_message': form.inapp_new_message.data,
                'post_reply': form.inapp_post_reply.data,
                'comment_reply': form.inapp_comment_reply.data,
                'mention': form.inapp_mention.data,
                'badge_earned': form.inapp_badge_earned.data,
                'system_updates': form.inapp_system_updates.data
            },
            'frequency': form.notification_frequency.data,
            'quiet_hours': {
                'enabled': form.enable_quiet_hours.data,
                'start': form.quiet_hours_start.data,
                'end': form.quiet_hours_end.data
            }
        }
        
        # Store in notification preferences field
        current_user.notification_preferences = json.dumps(notification_prefs)
        db.session.commit()
        flash('Notification preferences updated successfully!', 'success')
        return redirect(url_for('user.user_preferences'))
    
    # Load current notification preferences
    if hasattr(current_user, 'notification_preferences') and current_user.notification_preferences:
        try:
            prefs = json.loads(current_user.notification_preferences)
            
            # Email preferences
            email_prefs = prefs.get('email', {})
            form.email_new_follower.data = email_prefs.get('new_follower', True)
            form.email_new_message.data = email_prefs.get('new_message', True)
            form.email_post_reply.data = email_prefs.get('post_reply', True)
            form.email_comment_reply.data = email_prefs.get('comment_reply', True)
            form.email_mention.data = email_prefs.get('mention', True)
            form.email_badge_earned.data = email_prefs.get('badge_earned', True)
            form.email_system_updates.data = email_prefs.get('system_updates', False)
            
            # Push preferences
            push_prefs = prefs.get('push', {})
            form.push_new_follower.data = push_prefs.get('new_follower', True)
            form.push_new_message.data = push_prefs.get('new_message', True)
            form.push_post_reply.data = push_prefs.get('post_reply', True)
            form.push_comment_reply.data = push_prefs.get('comment_reply', True)
            form.push_mention.data = push_prefs.get('mention', True)
            form.push_badge_earned.data = push_prefs.get('badge_earned', True)
            form.push_system_updates.data = push_prefs.get('system_updates', False)
            
            # In-app preferences
            inapp_prefs = prefs.get('inapp', {})
            form.inapp_new_follower.data = inapp_prefs.get('new_follower', True)
            form.inapp_new_message.data = inapp_prefs.get('new_message', True)
            form.inapp_post_reply.data = inapp_prefs.get('post_reply', True)
            form.inapp_comment_reply.data = inapp_prefs.get('comment_reply', True)
            form.inapp_mention.data = inapp_prefs.get('mention', True)
            form.inapp_badge_earned.data = inapp_prefs.get('badge_earned', True)
            form.inapp_system_updates.data = inapp_prefs.get('system_updates', False)
            
            # Frequency and quiet hours
            form.notification_frequency.data = prefs.get('frequency', 'immediate')
            quiet_hours = prefs.get('quiet_hours', {})
            form.enable_quiet_hours.data = quiet_hours.get('enabled', False)
            form.quiet_hours_start.data = quiet_hours.get('start', '22:00')
            form.quiet_hours_end.data = quiet_hours.get('end', '08:00')
        except:
            pass  # Use defaults
    
    return render_template('user/notification_preferences.html', form=form)

@user_bp.route('/preferences/accessibility', methods=['GET', 'POST'])
@login_required
def accessibility_preferences():
    """Accessibility preferences"""
    from app.user.forms import AccessibilityPreferencesForm
    form = AccessibilityPreferencesForm()
    
    if form.validate_on_submit():
        # Store accessibility preferences
        accessibility_prefs = {
            'font_size': form.font_size.data,
            'high_contrast': form.high_contrast.data,
            'reduce_motion': form.reduce_motion.data,
            'screen_reader_optimized': form.screen_reader_optimized.data,
            'keyboard_navigation': form.keyboard_navigation.data,
            'color_blind_friendly': form.color_blind_friendly.data,
            'dyslexia_font': form.dyslexia_font.data
        }
        
        # Store in accessibility preferences field
        current_user.accessibility_preferences = json.dumps(accessibility_prefs)
        db.session.commit()
        flash('Accessibility preferences updated successfully!', 'success')
        return redirect(url_for('user.user_preferences'))
    
    # Load current accessibility preferences
    if hasattr(current_user, 'accessibility_preferences') and current_user.accessibility_preferences:
        try:
            prefs = json.loads(current_user.accessibility_preferences)
            form.font_size.data = prefs.get('font_size', 'medium')
            form.high_contrast.data = prefs.get('high_contrast', False)
            form.reduce_motion.data = prefs.get('reduce_motion', False)
            form.screen_reader_optimized.data = prefs.get('screen_reader_optimized', False)
            form.keyboard_navigation.data = prefs.get('keyboard_navigation', False)
            form.color_blind_friendly.data = prefs.get('color_blind_friendly', False)
            form.dyslexia_font.data = prefs.get('dyslexia_font', False)
        except:
            pass  # Use defaults
    
    return render_template('user/accessibility_preferences.html', form=form)

# Missing User Management Routes


@user_bp.route('/profile/customize', methods=['GET', 'POST'])
@login_required
def profile_customize():
    """Profile customization page"""
    from app.user.forms import ProfileCustomizationForm
    from app.user.models import UserProfileTheme
    
    form = ProfileCustomizationForm()
    
    # Get available themes
    themes = UserProfileTheme.get_all_themes(active_only=True)
    form.theme.choices = [(theme.name, theme.display_name) for theme in themes]
    
    if form.validate_on_submit():
        # Save profile customization
        customization = {
            'theme': form.theme.data,
            'layout': form.layout.data,
            'banner_image': form.banner_image.data,
            'widgets': form.widgets.data,
            'privacy': form.privacy.data
        }
        
        UserPreference.set_preference(current_user.id, 'profile_customization', json.dumps(customization))
        flash('Profile customization updated successfully!', 'success')
        return redirect(url_for('user.profile_customize'))
    
    # Load current customization
    customization = UserPreference.get_preference(current_user.id, 'profile_customization')
    if customization:
        try:
            prefs = json.loads(customization)
            form.theme.data = prefs.get('theme', 'default')
            form.layout.data = prefs.get('layout', 'grid')
            form.banner_image.data = prefs.get('banner_image', '')
            form.widgets.data = prefs.get('widgets', [])
            form.privacy.data = prefs.get('privacy', {})
        except:
            pass  # Use defaults
    
    return render_template('user/profile_customize.html', form=form, themes=themes)

@user_bp.route('/social/follow', methods=['POST'])
@login_required
def follow_user():
    """Follow a user"""
    from app.user.models import UserSocialConnection
    from app.models import User
    
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required'}), 400
    
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid user ID'}), 400
    
    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Create follow connection
    connection = UserSocialConnection.create_connection(
        user_id=current_user.id,
        connected_user_id=user_id,
        connection_type='follow'
    )
    
    return jsonify({
        'success': True,
        'message': f'You are now following {user.username}',
        'connection_id': connection.id
    })

@user_bp.route('/social/following')
@login_required
def following():
    """Get users that current user follows"""
    from app.user.models import UserSocialConnection
    from app.models import User
    
    connections = UserSocialConnection.get_following(current_user.id)
    following_users = []
    
    for connection in connections:
        user = User.query.get(connection.connected_user_id)
        if user:
            following_users.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'connection_id': connection.id,
                'connected_at': connection.created_at.isoformat()
            })
    
    return jsonify({
        'success': True,
        'following': following_users,
        'count': len(following_users)
    })

@user_bp.route('/social/followers')
@login_required
def followers():
    """Get users that follow current user"""
    from app.user.models import UserSocialConnection
    from app.models import User
    
    connections = UserSocialConnection.get_followers(current_user.id)
    follower_users = []
    
    for connection in connections:
        user = User.query.get(connection.user_id)
        if user:
            follower_users.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'connection_id': connection.id,
                'connected_at': connection.created_at.isoformat()
            })
    
    return jsonify({
        'success': True,
        'followers': follower_users,
        'count': len(follower_users)
    })

@user_bp.route('/analytics')
@login_required
def analytics():
    """User analytics dashboard"""
    from app.user.models import UserAnalytics
    
    # Get activity summary for last 30 days
    activity_summary = UserAnalytics.get_activity_summary(current_user.id, days=30)
    
    # Get trending metrics for last 7 days
    trending_metrics = UserAnalytics.get_trending_metrics(current_user.id, days=7)
    
    return render_template('user/analytics.html', 
                         activity_summary=activity_summary,
                         trending_metrics=trending_metrics)

@user_bp.route('/roles')
@login_required
def user_roles():
    """User roles management"""
    from app.user.models import UserRoleAssignment
    from app.admin.roles.models import Role
    
    # Get user's current roles
    user_roles = UserRoleAssignment.get_user_roles(current_user.id)
    
    # Get available roles
    available_roles = Role.query.filter_by(is_active=True).all()
    
    return render_template('user/roles.html', 
                         user_roles=user_roles,
                         available_roles=available_roles)

@user_bp.route('/profile/visibility', methods=['GET', 'POST'])
@login_required
def profile_visibility():
    """Profile visibility settings"""
    from app.user.forms import ProfileVisibilityForm
    
    form = ProfileVisibilityForm()
    
    if form.validate_on_submit():
        # Save visibility settings
        visibility_settings = {
            'profile_visibility': form.profile_visibility.data,
            'email_visibility': form.email_visibility.data,
            'location_visibility': form.location_visibility.data,
            'website_visibility': form.website_visibility.data,
            'bio_visibility': form.bio_visibility.data,
            'search_visibility': form.search_visibility.data,
            'social_links_visibility': form.social_links_visibility.data
        }
        
        UserPreference.set_preference(current_user.id, 'profile_visibility', json.dumps(visibility_settings))
        flash('Profile visibility settings updated successfully!', 'success')
        return redirect(url_for('user.profile_visibility'))
    
    # Load current visibility settings
    visibility_settings = UserPreference.get_preference(current_user.id, 'profile_visibility')
    if visibility_settings:
        try:
            settings = json.loads(visibility_settings)
            form.profile_visibility.data = settings.get('profile_visibility', 'public')
            form.email_visibility.data = settings.get('email_visibility', 'public')
            form.location_visibility.data = settings.get('location_visibility', 'public')
            form.website_visibility.data = settings.get('website_visibility', 'public')
            form.bio_visibility.data = settings.get('bio_visibility', 'public')
            form.search_visibility.data = settings.get('search_visibility', 'enabled')
            form.social_links_visibility.data = settings.get('social_links_visibility', 'public')
        except:
            pass  # Use defaults
    
    return render_template('user/profile_visibility.html', form=form)

@user_bp.route('/widgets', methods=['GET', 'POST'])
@login_required
def widgets():
    """Profile widgets management"""
    from app.user.forms import WidgetManagementForm
    
    form = WidgetManagementForm()
    
    if form.validate_on_submit():
        # Save widget configuration
        widget_config = {
            'enabled_widgets': form.enabled_widgets.data,
            'widget_order': form.widget_order.data,
            'widget_settings': form.widget_settings.data
        }
        
        UserPreference.set_preference(current_user.id, 'widgets', json.dumps(widget_config))
        flash('Widget configuration updated successfully!', 'success')
        return redirect(url_for('user.widgets'))
    
    # Load current widget configuration
    widget_config = UserPreference.get_preference(current_user.id, 'widgets')
    if widget_config:
        try:
            config = json.loads(widget_config)
            form.enabled_widgets.data = config.get('enabled_widgets', [])
            form.widget_order.data = config.get('widget_order', [])
            form.widget_settings.data = config.get('widget_settings', {})
        except:
            pass  # Use defaults
    
    return render_template('user/widgets.html', form=form)
