from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, URLField, FileField
from wtforms.validators import DataRequired, Email, ValidationError, Length, URL, Optional
from app.models import User
import json

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Username already taken.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Email already registered.')

# Advanced Profile Customization Forms

class ProfileThemeForm(FlaskForm):
    """Form for profile theme and skin selection"""
    theme = SelectField('Theme', choices=[
        ('default', 'Default'),
        ('dark', 'Dark'),
        ('minimal', 'Minimal'),
        ('colorful', 'Colorful'),
        ('modern', 'Modern'),
        ('classic', 'Classic'),
        ('ocean', 'Ocean'),
        ('forest', 'Forest'),
        ('sunset', 'Sunset'),
        ('midnight', 'Midnight')
    ], validators=[DataRequired()])
    
    skin = SelectField('Skin Variant', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto (System Preference)')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Apply Theme')

class ProfileBannerForm(FlaskForm):
    """Form for profile banner image"""
    banner_url = URLField('Banner Image URL', validators=[Optional(), URL()])
    banner_file = FileField('Upload Banner Image', validators=[Optional()])
    submit = SubmitField('Update Banner')

class ProfileLayoutForm(FlaskForm):
    """Form for profile layout customization"""
    layout_style = SelectField('Layout Style', choices=[
        ('default', 'Default'),
        ('sidebar_left', 'Sidebar Left'),
        ('sidebar_right', 'Sidebar Right'),
        ('grid', 'Grid'),
        ('magazine', 'Magazine'),
        ('minimal', 'Minimal')
    ], validators=[DataRequired()])
    
    columns = SelectField('Columns', choices=[
        ('1', 'Single Column'),
        ('2', 'Two Columns'),
        ('3', 'Three Columns')
    ], validators=[DataRequired()])
    
    show_bio = BooleanField('Show Bio Section')
    show_stats = BooleanField('Show Statistics')
    show_activity = BooleanField('Show Recent Activity')
    show_badges = BooleanField('Show Badges')
    show_social_links = BooleanField('Show Social Links')
    
    submit = SubmitField('Update Layout')

class ProfileWidgetsForm(FlaskForm):
    """Form for profile widget configuration"""
    widget_recent_posts = BooleanField('Recent Posts Widget')
    widget_recent_posts_position = SelectField('Recent Posts Position', choices=[
        ('sidebar', 'Sidebar'),
        ('main', 'Main Content'),
        ('footer', 'Footer')
    ])
    
    widget_recent_comments = BooleanField('Recent Comments Widget')
    widget_recent_comments_position = SelectField('Recent Comments Position', choices=[
        ('sidebar', 'Sidebar'),
        ('main', 'Main Content'),
        ('footer', 'Footer')
    ])
    
    widget_user_stats = BooleanField('User Statistics Widget')
    widget_user_stats_position = SelectField('User Stats Position', choices=[
        ('sidebar', 'Sidebar'),
        ('main', 'Main Content'),
        ('footer', 'Footer')
    ])
    
    widget_social_links = BooleanField('Social Links Widget')
    widget_social_links_position = SelectField('Social Links Position', choices=[
        ('sidebar', 'Sidebar'),
        ('main', 'Main Content'),
        ('footer', 'Footer')
    ])
    
    widget_custom_text = BooleanField('Custom Text Widget')
    widget_custom_text_content = TextAreaField('Custom Text Content')
    widget_custom_text_position = SelectField('Custom Text Position', choices=[
        ('sidebar', 'Sidebar'),
        ('main', 'Main Content'),
        ('footer', 'Footer')
    ])
    
    submit = SubmitField('Update Widgets')

class ProfilePrivacyForm(FlaskForm):
    """Form for profile privacy settings"""
    public_profile = BooleanField('Make Profile Public')
    show_email = BooleanField('Show Email Address')
    show_location = BooleanField('Show Location')
    show_website = BooleanField('Show Website')
    show_bio = BooleanField('Show Bio')
    show_activity = BooleanField('Show Recent Activity')
    show_stats = BooleanField('Show Statistics')
    show_badges = BooleanField('Show Badges')
    allow_messages = BooleanField('Allow Messages')
    allow_friend_requests = BooleanField('Allow Friend Requests')
    searchable = BooleanField('Allow Profile Search')
    indexable = BooleanField('Allow Search Engine Indexing')
    
    submit = SubmitField('Update Privacy Settings')

class ProfileColorSchemeForm(FlaskForm):
    """Form for profile color scheme customization"""
    primary_color = StringField('Primary Color', validators=[Optional(), Length(min=7, max=7)])
    secondary_color = StringField('Secondary Color', validators=[Optional(), Length(min=7, max=7)])
    accent_color = StringField('Accent Color', validators=[Optional(), Length(min=7, max=7)])
    background_color = StringField('Background Color', validators=[Optional(), Length(min=7, max=7)])
    text_color = StringField('Text Color', validators=[Optional(), Length(min=7, max=7)])
    link_color = StringField('Link Color', validators=[Optional(), Length(min=7, max=7)])
    border_color = StringField('Border Color', validators=[Optional(), Length(min=7, max=7)])
    
    custom_css = TextAreaField('Custom CSS', validators=[Optional()])
    
    submit = SubmitField('Update Color Scheme')

class ProfileCustomCSSForm(FlaskForm):
    """Form for custom CSS input"""
    custom_css = TextAreaField('Custom CSS Code', validators=[Optional()])
    submit = SubmitField('Update CSS')

class ProfileResetForm(FlaskForm):
    """Form to reset profile customization"""
    reset_theme = BooleanField('Reset Theme to Default')
    reset_layout = BooleanField('Reset Layout to Default')
    reset_widgets = BooleanField('Reset Widgets to Default')
    reset_privacy = BooleanField('Reset Privacy to Default')
    reset_colors = BooleanField('Reset Colors to Default')
    reset_css = BooleanField('Remove Custom CSS')
    
    confirm_reset = BooleanField('I understand this will reset my selected customizations', validators=[DataRequired()])
    submit = SubmitField('Reset Selected Customizations')

# User Preference System Forms

class UserPreferencesForm(FlaskForm):
    """Form for comprehensive user preferences"""
    # Display Preferences
    theme_preference = SelectField('Default Theme', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto')
    ])
    
    language_preference = SelectField('Language', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('pt', 'Portuguese'),
        ('ru', 'Russian'),
        ('ja', 'Japanese'),
        ('ko', 'Korean'),
        ('zh', 'Chinese'),
        ('ar', 'Arabic'),
        ('hi', 'Hindi')
    ])
    
    timezone = SelectField('Timezone', choices=[
        ('UTC', 'UTC'),
        ('EST', 'Eastern Time'),
        ('CST', 'Central Time'),
        ('MST', 'Mountain Time'),
        ('PST', 'Pacific Time')
    ])
    
    date_format = SelectField('Date Format', choices=[
        ('MM/DD/YYYY', 'MM/DD/YYYY'),
        ('DD/MM/YYYY', 'DD/MM/YYYY'),
        ('YYYY-MM-DD', 'YYYY-MM-DD'),
        ('DD MMM YYYY', 'DD MMM YYYY')
    ])
    
    time_format = SelectField('Time Format', choices=[
        ('12-hour', '12-hour (AM/PM)'),
        ('24-hour', '24-hour')
    ])
    
    # Notification Preferences
    email_notifications = BooleanField('Email Notifications')
    push_notifications = BooleanField('Push Notifications')
    desktop_notifications = BooleanField('Desktop Notifications')
    
    # Content Preferences
    show_sensitive_content = BooleanField('Show Sensitive Content')
    auto_play_videos = BooleanField('Auto-play Videos')
    show_avatars = BooleanField('Show User Avatars')
    show_signatures = BooleanField('Show User Signatures')
    
    # Privacy Preferences
    show_online_status = BooleanField('Show Online Status')
    allow_tagging = BooleanField('Allow Users to Tag Me')
    allow_mentions = BooleanField('Allow Users to Mention Me')
    
    submit = SubmitField('Update Preferences')

class NotificationPreferencesForm(FlaskForm):
    """Form for notification preferences"""
    # Email Notifications
    email_new_follower = BooleanField('New Follower Notifications')
    email_new_message = BooleanField('New Message Notifications')
    email_post_reply = BooleanField('Post Reply Notifications')
    email_comment_reply = BooleanField('Comment Reply Notifications')
    email_mention = BooleanField('Mention Notifications')
    email_badge_earned = BooleanField('Badge Earned Notifications')
    email_system_updates = BooleanField('System Update Notifications')
    
    # Push Notifications
    push_new_follower = BooleanField('New Follower Push Notifications')
    push_new_message = BooleanField('New Message Push Notifications')
    push_post_reply = BooleanField('Post Reply Push Notifications')
    push_comment_reply = BooleanField('Comment Reply Push Notifications')
    push_mention = BooleanField('Mention Push Notifications')
    push_badge_earned = BooleanField('Badge Earned Push Notifications')
    push_system_updates = BooleanField('System Update Push Notifications')
    
    # In-App Notifications
    inapp_new_follower = BooleanField('New Follower In-App Notifications')
    inapp_new_message = BooleanField('New Message In-App Notifications')
    inapp_post_reply = BooleanField('Post Reply In-App Notifications')
    inapp_comment_reply = BooleanField('Comment Reply In-App Notifications')
    inapp_mention = BooleanField('Mention In-App Notifications')
    inapp_badge_earned = BooleanField('Badge Earned In-App Notifications')
    inapp_system_updates = BooleanField('System Update In-App Notifications')
    
    # Notification Frequency
    notification_frequency = SelectField('Notification Frequency', choices=[
        ('immediate', 'Immediate'),
        ('hourly', 'Hourly Digest'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest')
    ])
    
    # Quiet Hours
    enable_quiet_hours = BooleanField('Enable Quiet Hours')
    quiet_hours_start = SelectField('Quiet Hours Start', choices=[
        ('22:00', '10:00 PM'),
        ('23:00', '11:00 PM'),
        ('00:00', '12:00 AM'),
        ('01:00', '1:00 AM')
    ])
    
    quiet_hours_end = SelectField('Quiet Hours End', choices=[
        ('06:00', '6:00 AM'),
        ('07:00', '7:00 AM'),
        ('08:00', '8:00 AM'),
        ('09:00', '9:00 AM')
    ])
    
    submit = SubmitField('Update Notification Preferences')

class AccessibilityPreferencesForm(FlaskForm):
    """Form for accessibility preferences"""
    font_size = SelectField('Font Size', choices=[
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('extra_large', 'Extra Large')
    ])
    
    high_contrast = BooleanField('High Contrast Mode')
    reduce_motion = BooleanField('Reduce Motion')
    screen_reader_optimized = BooleanField('Screen Reader Optimized')
    keyboard_navigation = BooleanField('Keyboard Navigation Enhanced')
    
    color_blind_friendly = BooleanField('Color Blind Friendly Mode')
    dyslexia_font = BooleanField('Dyslexia-Friendly Font')
    
    submit = SubmitField('Update Accessibility Preferences')

# Missing User Management Forms

class UserPreferencesForm(FlaskForm):
    """Main user preferences form"""
    theme = SelectField('Theme', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto (System Preference)')
    ], validators=[DataRequired()])
    
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('pt', 'Portuguese'),
        ('ru', 'Russian'),
        ('zh', 'Chinese'),
        ('ja', 'Japanese')
    ], validators=[DataRequired()])
    
    timezone = SelectField('Timezone', choices=[
        ('UTC', 'UTC'),
        ('America/New_York', 'Eastern Time'),
        ('America/Chicago', 'Central Time'),
        ('America/Denver', 'Mountain Time'),
        ('America/Los_Angeles', 'Pacific Time'),
        ('Europe/London', 'London'),
        ('Europe/Paris', 'Paris'),
        ('Asia/Tokyo', 'Tokyo'),
        ('Australia/Sydney', 'Sydney')
    ], validators=[DataRequired()])
    
    date_format = SelectField('Date Format', choices=[
        ('%Y-%m-%d', 'YYYY-MM-DD'),
        ('%m/%d/%Y', 'MM/DD/YYYY'),
        ('%d/%m/%Y', 'DD/MM/YYYY'),
        ('%Y/%m/%d', 'YYYY/MM/DD')
    ], validators=[DataRequired()])
    
    time_format = SelectField('Time Format', choices=[
        ('%H:%M', '24 Hour'),
        ('%I:%M %p', '12 Hour')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Update Preferences')

class ProfileCustomizationForm(FlaskForm):
    """Profile customization form with theme selection, banner upload, layout configuration, and widget management"""
    theme = SelectField('Theme', choices=[('default', 'Default')], validators=[DataRequired()])
    
    layout = SelectField('Layout', choices=[
        ('grid', 'Grid Layout'),
        ('list', 'List Layout'),
        ('masonry', 'Masonry Layout'),
        ('cards', 'Card Layout'),
        ('timeline', 'Timeline Layout'),
        ('magazine', 'Magazine Layout')
    ], validators=[DataRequired()])
    
    banner_image = FileField('Banner Image', validators=[Optional()])
    banner_url = URLField('Banner URL', validators=[Optional(), URL()])
    
    widgets = StringField('Widgets', validators=[Optional()])
    
    privacy = SelectField('Privacy Settings', choices=[
        ('public', 'Public'),
        ('friends', 'Friends Only'),
        ('private', 'Private')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Update Profile Customization')

class SocialConnectionForm(FlaskForm):
    """Social connection form with connection type selection, privacy settings, and connection permissions"""
    connection_type = SelectField('Connection Type', choices=[
        ('follow', 'Follow'),
        ('friend', 'Friend Request'),
        ('colleague', 'Colleague'),
        ('family', 'Family'),
        ('acquaintance', 'Acquaintance')
    ], validators=[DataRequired()])
    
    privacy_settings = SelectField('Privacy Settings', choices=[
        ('public', 'Public'),
        ('friends', 'Friends Only'),
        ('private', 'Private'),
        ('custom', 'Custom')
    ], validators=[DataRequired()])
    
    connection_permissions = SelectField('Connection Permissions', choices=[
        ('view_profile', 'View Profile'),
        ('view_activity', 'View Activity'),
        ('send_messages', 'Send Messages'),
        ('see_friends', 'See Friends'),
        ('full_access', 'Full Access')
    ], validators=[DataRequired()])
    
    message = TextAreaField('Message', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Send Connection Request')

class AnalyticsFilterForm(FlaskForm):
    """Analytics filter form with date range selection, metric type selection, filter options, and export options"""
    date_range = SelectField('Date Range', choices=[
        ('7d', 'Last 7 Days'),
        ('30d', 'Last 30 Days'),
        ('90d', 'Last 90 Days'),
        ('6m', 'Last 6 Months'),
        ('1y', 'Last Year'),
        ('custom', 'Custom Range')
    ], validators=[DataRequired()])
    
    start_date = StringField('Start Date', validators=[Optional()])
    end_date = StringField('End Date', validators=[Optional()])
    
    metric_type = SelectField('Metric Type', choices=[
        ('all', 'All Metrics'),
        ('login', 'Login Activity'),
        ('posts', 'Posts'),
        ('comments', 'Comments'),
        ('likes', 'Likes'),
        ('shares', 'Shares'),
        ('views', 'Views'),
        ('engagement', 'Engagement')
    ], validators=[DataRequired()])
    
    filter_options = SelectField('Filter Options', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('hourly', 'Hourly')
    ], validators=[DataRequired()])
    
    export_format = SelectField('Export Format', choices=[
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('pdf', 'PDF')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Apply Filters')

class ProfileVisibilityForm(FlaskForm):
    """Profile visibility settings form"""
    profile_visibility = SelectField('Profile Visibility', choices=[
        ('public', 'Public - Anyone can view'),
        ('friends', 'Friends Only'),
        ('followers', 'Followers Only'),
        ('private', 'Private - Only you')
    ], validators=[DataRequired()])
    
    email_visibility = SelectField('Email Visibility', choices=[
        ('public', 'Public'),
        ('friends', 'Friends Only'),
        ('private', 'Private')
    ], validators=[DataRequired()])
    
    location_visibility = SelectField('Location Visibility', choices=[
        ('public', 'Public'),
        ('friends', 'Friends Only'),
        ('private', 'Private')
    ], validators=[DataRequired()])
    
    website_visibility = SelectField('Website Visibility', choices=[
        ('public', 'Public'),
        ('friends', 'Friends Only'),
        ('private', 'Private')
    ], validators=[DataRequired()])
    
    bio_visibility = SelectField('Bio Visibility', choices=[
        ('public', 'Public'),
        ('friends', 'Friends Only'),
        ('private', 'Private')
    ], validators=[DataRequired()])
    
    search_visibility = SelectField('Search Visibility', choices=[
        ('enabled', 'Enabled in Search'),
        ('disabled', 'Disabled in Search')
    ], validators=[DataRequired()])
    
    social_links_visibility = SelectField('Social Links Visibility', choices=[
        ('public', 'Public'),
        ('friends', 'Friends Only'),
        ('private', 'Private')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Update Visibility Settings')

class WidgetManagementForm(FlaskForm):
    """Widget management form"""
    enabled_widgets = StringField('Enabled Widgets', validators=[Optional()])
    widget_order = StringField('Widget Order', validators=[Optional()])
    widget_settings = StringField('Widget Settings', validators=[Optional()])
    
    submit = SubmitField('Update Widgets')

class RoleRequestForm(FlaskForm):
    """Role request form"""
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    reason = TextAreaField('Reason for Request', validators=[
        DataRequired(), 
        Length(min=10, max=500, message='Reason must be between 10 and 500 characters')
    ])
    
    submit = SubmitField('Submit Request')

class PermissionRequestForm(FlaskForm):
    """Permission request form"""
    permission_id = SelectField('Permission', coerce=int, validators=[DataRequired()])
    resource_id = StringField('Resource ID', validators=[Optional()])
    reason = TextAreaField('Reason for Request', validators=[
        DataRequired(), 
        Length(min=10, max=500, message='Reason must be between 10 and 500 characters')
    ])
    
    submit = SubmitField('Submit Request')

class UserSearchForm(FlaskForm):
    """User search form"""
    query = StringField('Search', validators=[DataRequired(), Length(min=2, max=100)])
    search_type = SelectField('Search Type', choices=[
        ('username', 'Username'),
        ('email', 'Email'),
        ('name', 'Display Name'),
        ('location', 'Location'),
        ('bio', 'Bio')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Search')

class UserReportForm(FlaskForm):
    """User report form"""
    report_type = SelectField('Report Type', choices=[
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('harassment', 'Harassment'),
        ('fake_profile', 'Fake Profile'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    description = TextAreaField('Description', validators=[
        DataRequired(), 
        Length(min=10, max=1000, message='Description must be between 10 and 1000 characters')
    ])
    
    submit = SubmitField('Submit Report')
