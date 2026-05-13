from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user
from flask import current_app
from sqlalchemy.orm import relationship
from app import db, login_manager
import logging

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(256))
    reset_token = db.Column(db.String(256))
    reset_token_expiration = db.Column(db.DateTime)
    
    # User management fields
    is_active = db.Column(db.Boolean, default=True)  # Account active status
    is_suspended = db.Column(db.Boolean, default=False)  # Temporary suspension
    is_banned = db.Column(db.Boolean, default=False)  # Permanent ban
    suspension_reason = db.Column(db.Text)  # Reason for suspension/ban
    suspension_expires = db.Column(db.DateTime)  # When suspension expires
    banned_at = db.Column(db.DateTime)  # When user was banned
    banned_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Who banned them
    
    # Activity tracking
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)  # Account lockout after failed attempts
    
    # Profile fields
    bio = db.Column(db.Text)
    location = db.Column(db.String(128))
    website = db.Column(db.String(256))
    avatar_url = db.Column(db.String(256))
    
    # Advanced Profile Customization fields
    profile_theme = db.Column(db.String(50), default='default')  # Theme name
    profile_skin = db.Column(db.String(50), default='light')  # Skin variant
    profile_banner_url = db.Column(db.String(256))  # Cover/banner image
    profile_layout = db.Column(db.Text)  # JSON string for layout configuration
    profile_widgets = db.Column(db.Text)  # JSON string for widget configuration
    profile_privacy = db.Column(db.Text)  # JSON string for privacy settings
    profile_custom_css = db.Column(db.Text)  # Custom CSS for profile
    profile_color_scheme = db.Column(db.Text)  # JSON string for color scheme
    profile_show_badges = db.Column(db.Boolean, default=True)
    profile_show_stats = db.Column(db.Boolean, default=True)
    profile_show_activity = db.Column(db.Boolean, default=True)
    profile_allow_messages = db.Column(db.Boolean, default=True)
    profile_allow_friend_requests = db.Column(db.Boolean, default=True)
    profile_public_profile = db.Column(db.Boolean, default=True)
    
    # Two-Factor Authentication fields
    totp_secret = db.Column(db.String(256))  # Encrypted TOTP secret
    is_2fa_enabled = db.Column(db.Boolean, default=False)
    backup_codes_hash = db.Column(db.Text)  # JSON string of hashed backup codes
    last_2fa_used = db.Column(db.DateTime)  # Last time 2FA was used
    
    # Push notification fields
    push_subscriptions = db.Column(db.Text)  # JSON string of push subscriptions
    push_preferences = db.Column(db.Text)  # JSON string of push notification preferences
    push_enabled = db.Column(db.Boolean, default=True)  # Whether push notifications are enabled
    
    # Email notification fields
    email_preferences = db.Column(db.Text)  # JSON string of email notification preferences
    email_enabled = db.Column(db.Boolean, default=True)  # Whether email notifications are enabled
    
    # User Preference System fields
    user_preferences = db.Column(db.Text)  # JSON string of general user preferences
    notification_preferences = db.Column(db.Text)  # JSON string of notification preferences
    accessibility_preferences = db.Column(db.Text)  # JSON string of accessibility preferences
    
    # Social Features fields
    social_preferences = db.Column(db.Text)  # JSON string of social preferences and settings
    
    # Analytics fields
    analytics_preferences = db.Column(db.Text)  # JSON string of analytics preferences
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    posts = db.relationship('Post', foreign_keys='Post.user_id', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    badges = db.relationship('Badge', secondary='user_badges', backref='users')
    
    # Relationship for ban tracking
    ban_actions = db.relationship('User', foreign_keys=[banned_by], backref='banned_users', remote_side=[id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_account_locked(self):
        """Check if account is locked due to failed login attempts"""
        return self.locked_until and self.locked_until > datetime.utcnow()
    
    def can_login(self):
        """Check if user can login (not banned, suspended, or locked)"""
        if self.is_banned:
            return False
        if self.is_suspended and self.suspension_expires and self.suspension_expires > datetime.utcnow():
            return False
        if self.is_account_locked():
            return False
        return self.is_active
    
    def suspend(self, reason, duration_days=None, admin_id=None):
        """Suspend user account"""
        self.is_suspended = True
        self.suspension_reason = reason
        if duration_days:
            from datetime import timedelta
            self.suspension_expires = datetime.utcnow() + timedelta(days=duration_days)
        else:
            self.suspension_expires = None  # Indefinite suspension
        self.updated_at = datetime.utcnow()
    
    def unsuspend(self):
        """Unsuspend user account"""
        self.is_suspended = False
        self.suspension_reason = None
        self.suspension_expires = None
        self.updated_at = datetime.utcnow()
    
    def ban(self, reason, admin_id=None):
        """Permanently ban user account"""
        self.is_banned = True
        self.is_active = False
        self.suspension_reason = reason
        self.banned_at = datetime.utcnow()
        self.banned_by = admin_id
    
    def enable_2fa(self, totp_secret, backup_codes):
        """Enable 2FA for the user"""
        from app.auth.two_factor import two_fa_service
        import json
        
        # Encrypt TOTP secret
        encrypted_secret = two_fa_service.encrypt_data(totp_secret)
        self.totp_secret = encrypted_secret
        
        # Hash backup codes and store as JSON
        backup_codes_data = []
        for code in backup_codes:
            backup_codes_data.append({
                'hash': two_fa_service.hash_backup_code(code),
                'used': False,
                'created_at': datetime.utcnow().isoformat()
            })
        
        self.backup_codes_hash = json.dumps(backup_codes_data)
        self.is_2fa_enabled = True
        self.updated_at = datetime.utcnow()
    
    def disable_2fa(self):
        """Disable 2FA for the user"""
        self.totp_secret = None
        self.backup_codes_hash = None
        self.is_2fa_enabled = False
        self.last_2fa_used = None
        self.updated_at = datetime.utcnow()
    
    def get_totp_secret(self):
        """Get decrypted TOTP secret"""
        if not self.totp_secret:
            return None
        
        try:
            from app.auth.two_factor import two_fa_service
            return two_fa_service.decrypt_data(self.totp_secret)
        except Exception:
            return None
    
    def verify_2fa_token(self, token):
        """Verify 2FA token"""
        if not self.is_2fa_enabled or not self.totp_secret:
            return False
        
        try:
            from app.auth.two_factor import verify_2fa_token
            secret = self.get_totp_secret()
            if secret and verify_2fa_token(secret, token):
                self.last_2fa_used = datetime.utcnow()
                return True
        except Exception as e:
            logger.error(f"Error verifying 2FA token: {str(e)}")
        
        return False
    
    def verify_backup_code(self, provided_code):
        """Verify and use backup code"""
        if not self.is_2fa_enabled or not self.backup_codes_hash:
            return False
        
        try:
            import json
            from app.auth.two_factor import two_fa_service
            
            backup_codes = json.loads(self.backup_codes_hash)
            
            for code_info in backup_codes:
                if not code_info['used']:
                    if two_fa_service.verify_backup_code(code_info['hash'], provided_code):
                        # Mark as used
                        code_info['used'] = True
                        code_info['used_at'] = datetime.utcnow().isoformat()
                        
                        # Update stored codes
                        self.backup_codes_hash = json.dumps(backup_codes)
                        self.last_2fa_used = datetime.utcnow()
                        self.updated_at = datetime.utcnow()
                        
                        return True
            
        except Exception as e:
            logger.error(f"Error verifying backup code: {str(e)}")
        
        return False
    
    def get_unused_backup_codes_count(self):
        """Get count of unused backup codes"""
        if not self.backup_codes_hash:
            return 0
        
        try:
            import json
            backup_codes = json.loads(self.backup_codes_hash)
            return sum(1 for code in backup_codes if not code['used'])
        except Exception:
            return 0
    
    def regenerate_backup_codes(self, new_codes):
        """Regenerate backup codes"""
        from app.auth.two_factor import two_fa_service
        import json
        
        backup_codes_data = []
        for code in new_codes:
            backup_codes_data.append({
                'hash': two_fa_service.hash_backup_code(code),
                'used': False,
                'created_at': datetime.utcnow().isoformat()
            })
        
        self.backup_codes_hash = json.dumps(backup_codes_data)
        self.updated_at = datetime.utcnow()
    
    def get_social_account(self, provider):
        """Get social account for specific provider"""
        for account in self.social_accounts:
            if account.provider == provider and account.is_active:
                return account
        return None
    
    def has_social_account(self, provider):
        """Check if user has social account for provider"""
        return self.get_social_account(provider) is not None
    
    def link_social_account(self, provider, provider_user_id, access_token, 
                           refresh_token=None, expires_at=None, email=None, 
                           name=None, username=None, avatar_url=None, profile_data=None):
        """Link social account to user"""
        # Check if account already exists
        existing = SocialAccount.query.filter_by(
            provider=provider, 
            provider_user_id=provider_user_id
        ).first()
        
        if existing:
            # Update existing account
            existing.update_token(access_token, refresh_token, expires_at)
            existing.is_active = True
            if email:
                existing.email = email
            if name:
                existing.name = name
            if username:
                existing.username = username
            if avatar_url:
                existing.avatar_url = avatar_url
            if profile_data:
                existing.set_profile_data(profile_data)
        else:
            # Create new social account
            social_account = SocialAccount(
                user_id=self.id,
                provider=provider,
                provider_user_id=provider_user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=expires_at,
                email=email,
                name=name,
                username=username,
                avatar_url=avatar_url,
                is_active=True
            )
            if profile_data:
                social_account.set_profile_data(profile_data)
            db.session.add(social_account)
        
        db.session.commit()
    
    def unlink_social_account(self, provider):
        """Unlink social account from user"""
        account = self.get_social_account(provider)
        if account:
            account.is_active = False
            db.session.commit()
            return True
        return False
    
    def get_social_accounts_dict(self):
        """Get social accounts as dictionary"""
        accounts = {}
        for account in self.social_accounts:
            if account.is_active:
                accounts[account.provider] = {
                    'provider_user_id': account.provider_user_id,
                    'email': account.email,
                    'name': account.name,
                    'username': account.username,
                    'avatar_url': account.avatar_url,
                    'created_at': account.created_at.isoformat(),
                    'is_token_expired': account.is_token_expired()
                }
        return accounts
    
    def update_profile_from_social(self, provider):
        """Update user profile from social account data"""
        account = self.get_social_account(provider)
        if not account:
            return False
        
        # Update avatar if not set
        if not self.avatar_url and account.avatar_url:
            self.avatar_url = account.avatar_url
        
        # Update bio if not set and name is available
        if not self.bio and account.name:
            self.bio = f"Connected via {provider.title()}"
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    
    def unban(self):
        """Unban user account"""
        self.is_banned = False
        self.is_active = True
        self.suspension_reason = None
        self.banned_at = None
        self.banned_by = None
        self.updated_at = datetime.utcnow()
    
    def get_active_sessions(self):
        """Get user's active sessions"""
        return [session for session in self.sessions if session.is_active and not session.is_expired()]
    
    def get_session_count(self):
        """Get count of active sessions"""
        return len(self.get_active_sessions())
    
    def revoke_all_sessions(self):
        """Revoke all user sessions"""
        for session in self.sessions:
            session.is_active = False
        db.session.commit()
    
    def revoke_session(self, session_id):
        """Revoke specific session"""
        session = UserSession.query.filter_by(user_id=self.id, session_id=session_id).first()
        if session:
            session.revoke()
            return True
        return False
    
    def create_session(self, session_id, ip_address=None, user_agent=None, device_fingerprint=None, persistent=False):
        """Create new user session"""
        # Revoke existing sessions if not persistent
        if not persistent:
            self.revoke_all_sessions()
        
        # Calculate expiration
        from flask import current_app
        timeout = current_app.config.get('PERMANENT_SESSION_LIFETIME', 3600) if persistent else 1800  # 30 min default
        expires_at = datetime.utcnow() + timedelta(seconds=timeout)
        
        session = UserSession(
            user_id=self.id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            is_persistent=persistent,
            expires_at=expires_at
        )
        db.session.add(session)
        db.session.commit()
        return session
    
    def get_security_events(self, event_type=None, severity=None, limit=50):
        """Get user's security events"""
        query = SecurityEvent.query.filter_by(user_id=self.id)
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        if severity:
            query = query.filter_by(severity=severity)
        
        return query.order_by(SecurityEvent.created_at.desc()).limit(limit).all()
    
    def add_security_event(self, event_type, severity='info', description=None, ip_address=None, user_agent=None, metadata=None):
        """Add security event for user"""
        event = SecurityEvent(
            user_id=self.id,
            event_type=event_type,
            severity=severity,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        if metadata:
            event.set_event_data(metadata)
        db.session.add(event)
        db.session.commit()
    
    def get_session_analytics(self):
        """Get session analytics for user"""
        sessions = self.get_active_sessions()
        
        if not sessions:
            return {
                'total_sessions': 0,
                'devices': [],
                'locations': [],
                'last_activity': None
            }
        
        # Analyze devices
        devices = {}
        for session in sessions:
            device = session.user_agent or 'Unknown'
            if device not in devices:
                devices[device] = 0
            devices[device] += 1
        
        # Analyze locations
        locations = {}
        for session in sessions:
            location = session.location or 'Unknown'
            if location not in locations:
                locations[location] = 0
            locations[location] += 1
        
        return {
            'total_sessions': len(sessions),
            'devices': devices,
            'locations': locations,
            'last_activity': max(s.created_at for s in sessions).isoformat()
        }
    
    def get_account_status(self):
        """Get current account status"""
        if self.is_banned:
            return "Banned"
        elif self.is_suspended:
            if self.suspension_expires and self.suspension_expires > datetime.utcnow():
                return f"Suspended until {self.suspension_expires.strftime('%Y-%m-%d %H:%M')}"
            else:
                return "Suspended"
        elif self.is_account_locked():
            return f"Locked until {self.locked_until.strftime('%Y-%m-%d %H:%M')}"
        elif not self.is_active:
            return "Inactive"
        else:
            return "Active"
    
    def record_login(self):
        """Record successful login"""
        self.last_login = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.login_count += 1
        self.failed_login_attempts = 0
        self.locked_until = None
        self.updated_at = datetime.utcnow()
    
    def record_failed_login(self):
        """Record failed login attempt"""
        self.failed_login_attempts += 1
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        self.updated_at = datetime.utcnow()
    
    def get_user_stats(self):
        """Get user statistics"""
        return {
            'posts_count': self.posts.count(),
            'comments_count': self.comments.count(),
            'badges_count': len(self.badges),
            'login_count': self.login_count,
            'failed_attempts': self.failed_login_attempts,
            'account_age_days': (datetime.utcnow() - self.created_at).days,
            'last_login': self.last_login,
            'last_activity': self.last_activity
        }
    
    # Advanced Profile Customization Methods
    def get_profile_theme(self):
        """Get user's profile theme configuration"""
        return self.profile_theme or 'default'
    
    def set_profile_theme(self, theme, skin='light'):
        """Set user's profile theme and skin"""
        self.profile_theme = theme
        self.profile_skin = skin
        self.updated_at = datetime.utcnow()
    
    def get_profile_layout(self):
        """Get user's profile layout configuration"""
        if self.profile_layout:
            try:
                import json
                return json.loads(self.profile_layout)
            except:
                return self.get_default_layout()
        return self.get_default_layout()
    
    def set_profile_layout(self, layout_config):
        """Set user's profile layout configuration"""
        import json
        self.profile_layout = json.dumps(layout_config)
        self.updated_at = datetime.utcnow()
    
    def get_default_layout(self):
        """Get default profile layout configuration"""
        return {
            'sections': [
                {'id': 'bio', 'order': 1, 'visible': True},
                {'id': 'stats', 'order': 2, 'visible': True},
                {'id': 'activity', 'order': 3, 'visible': True},
                {'id': 'badges', 'order': 4, 'visible': True},
                {'id': 'social_links', 'order': 5, 'visible': True}
            ],
            'layout': 'default',
            'columns': 2
        }
    
    def get_profile_widgets(self):
        """Get user's profile widget configuration"""
        if self.profile_widgets:
            try:
                import json
                return json.loads(self.profile_widgets)
            except:
                return self.get_default_widgets()
        return self.get_default_widgets()
    
    def set_profile_widgets(self, widgets_config):
        """Set user's profile widget configuration"""
        import json
        self.profile_widgets = json.dumps(widgets_config)
        self.updated_at = datetime.utcnow()
    
    def get_default_widgets(self):
        """Get default profile widget configuration"""
        return {
            'widgets': [
                {'id': 'recent_posts', 'enabled': True, 'position': 'sidebar'},
                {'id': 'recent_comments', 'enabled': True, 'position': 'sidebar'},
                {'id': 'user_stats', 'enabled': True, 'position': 'main'},
                {'id': 'social_links', 'enabled': True, 'position': 'footer'},
                {'id': 'custom_text', 'enabled': False, 'position': 'sidebar', 'content': ''}
            ]
        }
    
    def get_profile_privacy(self):
        """Get user's profile privacy settings"""
        if self.profile_privacy:
            try:
                import json
                return json.loads(self.profile_privacy)
            except:
                return self.get_default_privacy()
        return self.get_default_privacy()
    
    def set_profile_privacy(self, privacy_config):
        """Set user's profile privacy settings"""
        import json
        self.profile_privacy = json.dumps(privacy_config)
        self.updated_at = datetime.utcnow()
    
    def get_default_privacy(self):
        """Get default privacy settings"""
        return {
            'public_profile': True,
            'show_email': False,
            'show_location': True,
            'show_website': True,
            'show_bio': True,
            'show_activity': True,
            'show_stats': True,
            'show_badges': True,
            'allow_messages': True,
            'allow_friend_requests': True,
            'searchable': True,
            'indexable': True
        }
    
    def get_color_scheme(self):
        """Get user's profile color scheme"""
        if self.profile_color_scheme:
            try:
                import json
                return json.loads(self.profile_color_scheme)
            except:
                return self.get_default_color_scheme()
        return self.get_default_color_scheme()
    
    def set_color_scheme(self, color_config):
        """Set user's profile color scheme"""
        import json
        self.profile_color_scheme = json.dumps(color_config)
        self.updated_at = datetime.utcnow()
    
    def get_default_color_scheme(self):
        """Get default color scheme"""
        return {
            'primary': '#007bff',
            'secondary': '#6c757d',
            'accent': '#17a2b8',
            'background': '#ffffff',
            'text': '#212529',
            'link': '#007bff',
            'border': '#dee2e6'
        }
    
    def can_view_profile(self, viewer=None):
        """Check if a viewer can see this user's profile"""
        # User can always view their own profile
        if viewer and viewer.id == self.id:
            return True
        
        # Check if profile is public
        privacy = self.get_profile_privacy()
        if not privacy.get('public_profile', True):
            return False
        
        # Check if profile is searchable
        if not privacy.get('searchable', True):
            return False
        
        return True
    
    def can_send_message(self, sender=None):
        """Check if a sender can send a message to this user"""
        if not sender:
            return False
        
        # Users can always message themselves
        if sender.id == self.id:
            return True
        
        privacy = self.get_profile_privacy()
        return privacy.get('allow_messages', True)
    
    def can_send_friend_request(self, requester=None):
        """Check if a user can send a friend request"""
        if not requester:
            return False
        
        # Users can't friend request themselves
        if requester.id == self.id:
            return False
        
        privacy = self.get_profile_privacy()
        return privacy.get('allow_friend_requests', True)
    
    def update_profile_banner(self, banner_url):
        """Update profile banner URL"""
        self.profile_banner_url = banner_url
        self.updated_at = datetime.utcnow()
    
    def update_custom_css(self, css_code):
        """Update custom CSS for profile"""
        self.profile_custom_css = css_code
        self.updated_at = datetime.utcnow()
    
    def reset_profile_customization(self):
        """Reset all profile customization to defaults"""
        self.profile_theme = 'default'
        self.profile_skin = 'light'
        self.profile_layout = None
        self.profile_widgets = None
        self.profile_privacy = None
        self.profile_custom_css = None
        self.profile_color_scheme = None
        self.updated_at = datetime.utcnow()

class Repository(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    github_url = db.Column(db.String(256), unique=True, nullable=False)
    stars = db.Column(db.Integer, default=0)
    forks = db.Column(db.Integer, default=0)
    language = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='repository', lazy='dynamic')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#00f5ff')
    posts = db.relationship('Post', backref='category', lazy='dynamic')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    repository_id = db.Column(db.Integer, db.ForeignKey('repository.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    attachment = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    # Enhanced voting system relationships
    # vote_history = db.relationship('VoteHistory', 
    #                                foreign_keys='VoteHistory.target_id',
    #                                primaryjoin='and_(Post.id == VoteHistory.target_id, VoteHistory.target_type == "post")',
    #                                backref='post_votes', lazy='dynamic')
    
    # Reputation and voting analytics
    reputation_impact = db.Column(db.Float, default=0.0)  # Total reputation impact from votes
    weighted_score = db.Column(db.Float, default=0.0)  # Weighted score considering voter reputation
    last_vote_at = db.Column(db.DateTime)  # When this post was last voted on
    
    # Draft system fields
    is_draft = db.Column(db.Boolean, default=False)
    auto_save_data = db.Column(db.Text)  # JSON data for auto-saved content
    last_saved_at = db.Column(db.DateTime)
    
    # Versioning fields
    version_number = db.Column(db.Integer, default=1)
    parent_post_id = db.Column(db.Integer, db.ForeignKey('post.id'))  # For version history
    
    # Scheduling fields
    scheduled_publish_at = db.Column(db.DateTime)
    is_scheduled = db.Column(db.Boolean, default=False)
    
    # Analytics fields
    view_count = db.Column(db.Integer, default=0)
    engagement_score = db.Column(db.Float, default=0.0)
    search_rank = db.Column(db.Float, default=0.0)
    
    # Collaboration fields
    edit_permissions = db.Column(db.Text)  # JSON data for edit permissions
    
    # Expiration and archiving
    expires_at = db.Column(db.DateTime)
    is_archived = db.Column(db.Boolean, default=False)
    archived_at = db.Column(db.DateTime)
    
    # Moderation fields
    is_flagged = db.Column(db.Boolean, default=False)
    moderation_status = db.Column(db.String(20), default='approved')  # 'approved', 'flagged', 'pending', 'rejected'
    flagged_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Who flagged the post
    flagged_at = db.Column(db.DateTime)  # When it was flagged
    moderation_reason = db.Column(db.Text)  # Reason for moderation action
    
    # Relationships
    versions = db.relationship('PostVersion', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    collaborators = db.relationship('PostCollaborator', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    # files = db.relationship('FileStorage', foreign_keys='file_storage.owner_id', backref='post', lazy='dynamic')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    
    # Enhanced voting system relationships
    # vote_history = db.relationship('VoteHistory', 
    #                                foreign_keys='VoteHistory.target_id',
    #                                primaryjoin='and_(Comment.id == VoteHistory.target_id, VoteHistory.target_type == "comment")',
    #                                backref='comment_votes', lazy='dynamic')
    
    # Reputation and voting analytics
    reputation_impact = db.Column(db.Float, default=0.0)  # Total reputation impact from votes
    weighted_score = db.Column(db.Float, default=0.0)  # Weighted score considering voter reputation
    last_vote_at = db.Column(db.DateTime)  # When this comment was last voted on

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', backref='bookmarks')
    post = relationship('Post', backref='bookmarks')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_bookmark'),)

# Enhanced voting methods for Post model
def add_post_voting_methods():
    """Add enhanced voting methods to Post model"""
    
    def get_user_vote(self, user_id):
        """Get user's vote on this post"""
        from app.reputation.models import VoteHistory
        return VoteHistory.query.filter_by(
            user_id=user_id,
            target_type='post',
            target_id=self.id,
            revoked_at=None
        ).first()
    
    def calculate_weighted_score(self):
        """Calculate weighted score based on voter reputation"""
        from app.reputation.models import VoteHistory, UserReputation
        from app.reputation.service import ReputationService
        
        votes = VoteHistory.query.filter_by(
            target_type='post',
            target_id=self.id,
            revoked_at=None
        ).all()
        
        weighted_score = 0.0
        for vote in votes:
            reputation_service = ReputationService()
            user_reputation = reputation_service.get_user_reputation(vote.user_id)
            weight = user_reputation.voting_power
            
            if vote.vote_type == 'upvote':
                weighted_score += weight
            else:
                weighted_score -= weight
        
        self.weighted_score = weighted_score
        return weighted_score
    
    def update_vote_counts(self):
        """Update vote counts and calculate weighted score"""
        from app.reputation.models import VoteHistory
        
        # Count votes
        votes = VoteHistory.query.filter_by(
            target_type='post',
            target_id=self.id,
            revoked_at=None
        ).all()
        
        self.upvotes = len([v for v in votes if v.vote_type == 'upvote'])
        self.downvotes = len([v for v in votes if v.vote_type == 'downvote'])
        
        # Update weighted score
        self.calculate_weighted_score()
        
        # Update last vote time
        if votes:
            self.last_vote_at = max(v.created_at for v in votes)
    
    def get_vote_summary(self):
        """Get comprehensive vote summary"""
        from app.reputation.models import VoteHistory
        
        votes = VoteHistory.query.filter_by(
            target_type='post',
            target_id=self.id,
            revoked_at=None
        ).all()
        
        summary = {
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'total_votes': len(votes),
            'weighted_score': self.weighted_score,
            'reputation_impact': self.reputation_impact,
            'last_vote_at': self.last_vote_at
        }
        
        # Add reason categories
        reason_categories = {}
        for vote in votes:
            category = vote.reason_category or 'unspecified'
            reason_categories[category] = reason_categories.get(category, 0) + 1
        
        summary['reason_categories'] = reason_categories
        
        return summary
    
    # Add methods to Post class
    Post.get_user_vote = get_user_vote
    Post.calculate_weighted_score = calculate_weighted_score
    Post.update_vote_counts = update_vote_counts
    Post.get_vote_summary = get_vote_summary

# Enhanced voting methods for Comment model
def add_comment_voting_methods():
    """Add enhanced voting methods to Comment model"""
    
    def get_user_vote(self, user_id):
        """Get user's vote on this comment"""
        from app.reputation.models import VoteHistory
        return VoteHistory.query.filter_by(
            user_id=user_id,
            target_type='comment',
            target_id=self.id,
            revoked_at=None
        ).first()
    
    def calculate_weighted_score(self):
        """Calculate weighted score based on voter reputation"""
        from app.reputation.models import VoteHistory, UserReputation
        from app.reputation.service import ReputationService
        
        votes = VoteHistory.query.filter_by(
            target_type='comment',
            target_id=self.id,
            revoked_at=None
        ).all()
        
        weighted_score = 0.0
        for vote in votes:
            reputation_service = ReputationService()
            user_reputation = reputation_service.get_user_reputation(vote.user_id)
            weight = user_reputation.voting_power
            
            if vote.vote_type == 'upvote':
                weighted_score += weight
            else:
                weighted_score -= weight
        
        self.weighted_score = weighted_score
        return weighted_score
    
    def update_vote_counts(self):
        """Update vote counts and calculate weighted score"""
        from app.reputation.models import VoteHistory
        
        # Count votes
        votes = VoteHistory.query.filter_by(
            target_type='comment',
            target_id=self.id,
            revoked_at=None
        ).all()
        
        self.upvotes = len([v for v in votes if v.vote_type == 'upvote'])
        self.downvotes = len([v for v in votes if v.vote_type == 'downvote'])
        
        # Update weighted score
        self.calculate_weighted_score()
        
        # Update last vote time
        if votes:
            self.last_vote_at = max(v.created_at for v in votes)
    
    def get_vote_summary(self):
        """Get comprehensive vote summary"""
        from app.reputation.models import VoteHistory
        
        votes = VoteHistory.query.filter_by(
            target_type='comment',
            target_id=self.id,
            revoked_at=None
        ).all()
        
        summary = {
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'total_votes': len(votes),
            'weighted_score': self.weighted_score,
            'reputation_impact': self.reputation_impact,
            'last_vote_at': self.last_vote_at
        }
        
        # Add reason categories
        reason_categories = {}
        for vote in votes:
            category = vote.reason_category or 'unspecified'
            reason_categories[category] = reason_categories.get(category, 0) + 1
        
        summary['reason_categories'] = reason_categories
        
        return summary
    
    # Add methods to Comment class
    Comment.get_user_vote = get_user_vote
    Comment.calculate_weighted_score = calculate_weighted_score
    Comment.update_vote_counts = update_vote_counts
    Comment.get_vote_summary = get_vote_summary

# Apply the methods when models are imported
add_post_voting_methods()
add_comment_voting_methods()

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(32), default='★')
    color = db.Column(db.String(7), default='#ff00ff')

user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True)
)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    value = db.Column(db.Integer, nullable=False)  # 1 for upvote, -1 for downvote
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PostVersion(db.Model):
    """Model for tracking post editing history and version control"""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text, nullable=False)
    edited_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    change_summary = db.Column(db.String(500))  # Summary of changes made
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    editor = db.relationship('User', backref='edited_versions')

class PostCollaborator(db.Model):
    """Model for managing post collaboration permissions"""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permission_level = db.Column(db.String(20), default='view')  # view, edit, admin
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='collaborations')
    added_by_user = db.relationship('User', foreign_keys=[added_by], backref='added_collaborations')
    
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_post_user_collaborator'),)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(256))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='notifications')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Threading fields
    thread_id = db.Column(db.Integer, db.ForeignKey('message_thread.id'), nullable=True)
    parent_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    thread_level = db.Column(db.Integer, default=0)
    
    # Rich text fields
    content_html = db.Column(db.Text, nullable=True)
    content_format = db.Column(db.String(20), default='text')  # 'text', 'html', 'markdown'
    is_rich_text = db.Column(db.Boolean, default=False)
    
    # Attachment fields
    has_attachments = db.Column(db.Boolean, default=False)
    
    # Search fields
    search_vector = db.Column(db.Text, nullable=True)  # For full-text search
    search_keywords = db.Column(db.Text, nullable=True)  # Extracted keywords
    
    # Forwarding fields
    forwarded_from_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    forwarded_count = db.Column(db.Integer, default=0)
    
    # Status fields
    is_deleted = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    
    # Priority and importance
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    is_starred = db.Column(db.Boolean, default=False)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    
    # Self-referential relationships for threading and forwarding
    parent_message = db.relationship('Message', remote_side=[id], foreign_keys=[parent_message_id])
    forwarded_from = db.relationship('Message', remote_side=[id], foreign_keys=[forwarded_from_id])
    
    # Thread relationship
    thread = db.relationship('MessageThread', backref='messages')

# Social Login Models
class FileStorage(db.Model):
    """Model for storing file metadata and managing cloud storage"""
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)  # Unique filename in storage
    file_path = db.Column(db.String(500), nullable=False)  # Path in cloud storage
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    mime_type = db.Column(db.String(100), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'image', 'document', 'video', 'audio', 'other'
    storage_provider = db.Column(db.String(50), default='local')  # 'local', 's3', 'gcs', etc.
    storage_bucket = db.Column(db.String(100))  # Bucket name for cloud storage
    storage_region = db.Column(db.String(50))  # Storage region
    is_public = db.Column(db.Boolean, default=False)  # Public access flag
    is_processed = db.Column(db.Boolean, default=False)  # Processing status
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User and ownership
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # For file sharing
    
    # File processing and optimization
    thumbnail_path = db.Column(db.String(500))  # Path to thumbnail
    optimized_path = db.Column(db.String(500))  # Path to optimized version
    preview_available = db.Column(db.Boolean, default=False)
    
    # Analytics and tracking
    download_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    last_downloaded = db.Column(db.DateTime)
    
    # Sharing and permissions
    sharing_token = db.Column(db.String(100))  # Unique token for sharing
    expires_at = db.Column(db.DateTime)  # File expiration
    max_downloads = db.Column(db.Integer)  # Maximum download limit
    current_downloads = db.Column(db.Integer, default=0)
    
    # Relationships
    uploader = db.relationship('User', foreign_keys=[uploaded_by], backref='uploaded_files')
    owner = db.relationship('User', foreign_keys=[owner_id], backref='owned_files')

class FileShare(db.Model):
    """Model for managing file sharing permissions"""
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file_storage.id'), nullable=False)
    shared_with = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permission_level = db.Column(db.String(20), default='view')  # 'view', 'download', 'edit'
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    download_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime)
    
    # Relationships
    file = db.relationship('FileStorage', backref='shares')
    shared_user = db.relationship('User', foreign_keys=[shared_with], backref='shared_files')
    sharer = db.relationship('User', foreign_keys=[shared_by], backref='shared_by_me')

class FileAnalytics(db.Model):
    """Model for tracking file analytics and usage patterns"""
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file_storage.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action_type = db.Column(db.String(20), nullable=False)  # 'view', 'download', 'share', 'delete'
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.String(500))
    referrer = db.Column(db.String(500))
    file_size = db.Column(db.Integer)  # File size at time of access
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    file = db.relationship('FileStorage', backref='analytics')
    user = db.relationship('User', backref='file_analytics')

# Social Login Models
class SocialAccount(db.Model):
    """Social account linking for OAuth2 providers"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # 'google', 'github', etc.
    provider_user_id = db.Column(db.String(255), nullable=False)  # Provider's user ID
    access_token = db.Column(db.Text)  # OAuth access token
    refresh_token = db.Column(db.Text)  # OAuth refresh token
    token_expires_at = db.Column(db.DateTime)  # Token expiration
    email = db.Column(db.String(120))  # Email from provider
    name = db.Column(db.String(100))  # Name from provider
    username = db.Column(db.String(64))  # Username from provider
    avatar_url = db.Column(db.String(256))  # Avatar URL from provider
    profile_data = db.Column(db.Text)  # JSON string of profile data
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('social_accounts', lazy=True, cascade='all, delete-orphan'))
    
    # Unique constraint to prevent duplicate social accounts
    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_user_id', name='unique_social_account'),
        db.Index('idx_social_user_provider', 'user_id', 'provider'),
    )
    
    def get_profile_data(self):
        """Get profile data as dictionary"""
        if self.profile_data:
            import json
            return json.loads(self.profile_data)
        return {}
    
    def set_profile_data(self, data):
        """Set profile data from dictionary"""
        import json
        self.profile_data = json.dumps(data)
    
    def is_token_expired(self):
        """Check if access token is expired"""
        if self.token_expires_at:
            return datetime.utcnow() >= self.token_expires_at
        return False
    
    def update_token(self, access_token, refresh_token=None, expires_at=None):
        """Update OAuth tokens"""
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        if expires_at:
            self.token_expires_at = expires_at
        self.updated_at = datetime.utcnow()

class SocialLoginSession(db.Model):
    """Temporary session for OAuth2 flow"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(255), nullable=False)
    redirect_url = db.Column(db.String(500))
    user_data = db.Column(db.Text)  # JSON string of user data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() >= self.expires_at
    
    def get_user_data(self):
        """Get user data as dictionary"""
        if self.user_data:
            import json
            return json.loads(self.user_data)
        return {}
    
    def set_user_data(self, data):
        """Set user data from dictionary"""
        import json
        self.user_data = json.dumps(data)

# Advanced Session Management Models
class UserSession(db.Model):
    """User session tracking and management"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.Text)
    device_fingerprint = db.Column(db.String(255))
    location = db.Column(db.String(255))  # Geolocation data
    is_active = db.Column(db.Boolean, default=True)
    is_persistent = db.Column(db.Boolean, default=False)  # "Remember me" sessions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('sessions', lazy=True, cascade='all, delete-orphan'))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_session_user', 'user_id', 'is_active'),
        db.Index('idx_session_expires', 'expires_at'),
        db.Index('idx_session_activity', 'last_activity'),
    )
    
    def is_expired(self):
        """Check if session is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def extend_session(self, minutes=30):
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        db.session.commit()
    
    def revoke(self):
        """Revoke session"""
        self.is_active = False
        db.session.commit()

class SessionAnalytics(db.Model):
    """Session analytics and monitoring data"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    total_sessions = db.Column(db.Integer, default=0)
    active_sessions = db.Column(db.Integer, default=0)
    unique_users = db.Column(db.Integer, default=0)
    average_session_duration = db.Column(db.Float)  # in minutes
    top_devices = db.Column(db.Text)  # JSON string of device data
    top_locations = db.Column(db.Text)  # JSON string of location data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        db.UniqueConstraint('date', name='unique_session_analytics_date'),
    )
    
    def get_top_devices(self):
        """Get top devices as dictionary"""
        if self.top_devices:
            import json
            return json.loads(self.top_devices)
        return {}
    
    def set_top_devices(self, devices):
        """Set top devices from dictionary"""
        import json
        self.top_devices = json.dumps(devices)
    
    def get_top_locations(self):
        """Get top locations as dictionary"""
        if self.top_locations:
            import json
            return json.loads(self.top_locations)
        return {}
    
    def set_top_locations(self, locations):
        """Set top locations from dictionary"""
        import json
        self.top_locations = json.dumps(locations)

class SecurityEvent(db.Model):
    """Security events and suspicious activity tracking"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_id = db.Column(db.String(255))
    event_type = db.Column(db.String(50), nullable=False)  # 'login', 'logout', 'suspicious', etc.
    severity = db.Column(db.String(20), default='info')  # 'info', 'warning', 'critical'
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    description = db.Column(db.Text)
    event_data = db.Column(db.Text)  # JSON string of additional data (renamed from metadata)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('security_events', lazy=True))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_security_user', 'user_id'),
        db.Index('idx_security_type', 'event_type'),
        db.Index('idx_security_severity', 'severity'),
        db.Index('idx_security_date', 'created_at'),
    )
    
    def get_event_data(self):
        """Get event data as dictionary"""
        if self.event_data:
            import json
            return json.loads(self.event_data)
        return {}
    
    def set_event_data(self, data):
        """Set event data from dictionary"""
        import json
        self.event_data = json.dumps(data)

class SearchIndex(db.Model):
    """Search index model for Elasticsearch integration"""
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(50), nullable=False)  # 'post', 'comment', 'user'
    content_id = db.Column(db.Integer, nullable=False)
    indexed_content = db.Column(db.Text)
    search_vector = db.Column(db.Text)  # Searchable text content
    title = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    tags = db.Column(db.Text)  # JSON array of tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Search relevance fields
    view_count = db.Column(db.Integer, default=0)
    vote_score = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    relevance_score = db.Column(db.Float, default=0.0)
    
    # Relationships
    author = db.relationship('User', backref='search_indices')
    category = db.relationship('Category', backref='search_indices')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_search_content', 'content_type', 'content_id'),
        db.Index('idx_search_author', 'author_id'),
        db.Index('idx_search_category', 'category_id'),
        db.Index('idx_search_created', 'created_at'),
        db.Index('idx_search_relevance', 'relevance_score'),
    )
    
    def to_dict(self):
        """Convert search index to dictionary for Elasticsearch"""
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'indexed_content': self.indexed_content,
            'search_vector': self.search_vector,
            'title': self.title,
            'author_id': self.author_id,
            'category_id': self.category_id,
            'tags': self.get_tags(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'view_count': self.view_count,
            'vote_score': self.vote_score,
            'comment_count': self.comment_count,
            'relevance_score': self.relevance_score
        }
    
    def get_tags(self):
        """Get tags as list"""
        import json
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []
    
    def set_tags(self, tags):
        """Set tags from list"""
        import json
        self.tags = json.dumps(tags)
    
    def update_relevance_score(self):
        """Calculate and update relevance score"""
        # Base score from engagement
        base_score = (
            self.view_count * 0.1 +
            self.vote_score * 0.5 +
            self.comment_count * 0.3
        )
        
        # Time decay (newer content gets higher score)
        if self.created_at:
            days_old = (datetime.utcnow() - self.created_at).days
            time_factor = max(0.1, 1.0 - (days_old * 0.01))
        else:
            time_factor = 1.0  # Default time factor if created_at is None
        
        self.relevance_score = base_score * time_factor
        db.session.commit()
    
    @staticmethod
    def create_from_post(post):
        """Create search index from post"""
        index = SearchIndex.query.filter_by(
            content_type='post',
            content_id=post.id
        ).first()
        
        if not index:
            index = SearchIndex(
                content_type='post',
                content_id=post.id,
                author_id=post.user_id,
                category_id=post.category_id
            )
            db.session.add(index)
        
        # Update searchable content
        index.title = post.title
        index.indexed_content = f"{post.title} {post.content}"
        index.search_vector = f"{post.title} {post.content} {' '.join(post.get_tags())}"
        index.set_tags(post.get_tags())
        index.view_count = post.view_count
        index.vote_score = post.get_vote_score()
        index.comment_count = len(post.comments)
        index.update_relevance_score()
        
        return index
    
    @staticmethod
    def create_from_comment(comment):
        """Create search index from comment"""
        index = SearchIndex.query.filter_by(
            content_type='comment',
            content_id=comment.id
        ).first()
        
        if not index:
            index = SearchIndex(
                content_type='comment',
                content_id=comment.id,
                author_id=comment.user_id
            )
            db.session.add(index)
        
        # Update searchable content
        post_title = comment.post.title if comment.post else ''
        index.title = f"Comment on: {post_title}"
        index.indexed_content = comment.content
        index.search_vector = comment.content
        index.set_tags([])
        index.vote_score = comment.get_vote_score()
        index.update_relevance_score()
        
        return index
    
    @staticmethod
    def create_from_user(user):
        """Create search index from user"""
        index = SearchIndex.query.filter_by(
            content_type='user',
            content_id=user.id
        ).first()
        
        if not index:
            index = SearchIndex(
                content_type='user',
                content_id=user.id,
                author_id=user.id
            )
            db.session.add(index)
        
        # Update searchable content
        index.title = user.username
        index.indexed_content = f"{user.username} {user.bio or ''}"
        index.search_vector = f"{user.username} {user.bio or ''}"
        index.set_tags([])
        index.update_relevance_score()
        
        return index

class SearchAnalytics(db.Model):
    """Search analytics and popular queries tracking"""
    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(255), nullable=False)  # Renamed from 'query' to avoid conflict
    search_date = db.Column(db.Date, default=datetime.utcnow().date)
    search_count = db.Column(db.Integer, default=1)
    result_count = db.Column(db.Integer, default=0)
    avg_result_position = db.Column(db.Float)
    click_through_rate = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref='search_analytics')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_search_query_date', 'search_query', 'search_date'),
        db.Index('idx_search_date', 'search_date'),
        db.Index('idx_search_count', 'search_count'),
    )
    
    @staticmethod
    def log_search(query, result_count, user_id=None, ip_address=None, user_agent=None):
        """Log search query for analytics"""
        from sqlalchemy import func
        
        # Check if query exists for today
        existing = SearchAnalytics.query.filter_by(
            search_query=query,
            search_date=datetime.utcnow().date()
        ).first()
        
        if existing:
            existing.search_count += 1
            # Update average result count
            total_searches = existing.search_count
            existing.avg_result_position = (
                (existing.avg_result_position * (total_searches - 1) + result_count) / total_searches
            )
        else:
            existing = SearchAnalytics(
                search_query=query,
                result_count=result_count,
                avg_result_position=float(result_count),
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(existing)
        
        db.session.commit()
        return existing
    
    @staticmethod
    def get_popular_queries(days=7, limit=10):
        """Get popular search queries"""
        from sqlalchemy import func, desc
        from datetime import date, timedelta
        
        start_date = date.today() - timedelta(days=days)
        
        # Create a custom result object
        class PopularQuery:
            def __init__(self, search_query, search_count, avg_result_position):
                self.search_query = search_query
                self.search_count = search_count
                self.avg_result_position = avg_result_position
        
        # Get aggregated results
        results = db.session.query(
            SearchAnalytics.search_query,
            func.sum(SearchAnalytics.search_count).label('search_count'),
            func.avg(SearchAnalytics.avg_result_position).label('avg_result_position')
        ).filter(
            SearchAnalytics.search_date >= start_date
        ).group_by(
            SearchAnalytics.search_query
        ).order_by(
            desc(func.sum(SearchAnalytics.search_count))
        ).limit(limit).all()
        
        # Convert to PopularQuery objects
        return [
            PopularQuery(
                search_query=result.search_query,
                search_count=int(result.search_count),
                avg_result_position=float(result.avg_result_position) if result.avg_result_position else 0
            )
            for result in results
        ]

class UserSearchPreferences(db.Model):
    """User search preferences and settings"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Display preferences
    results_per_page = db.Column(db.Integer, default=20)
    default_sort = db.Column(db.String(20), default='relevance')
    default_order = db.Column(db.String(10), default='desc')
    
    # Search options
    include_comments = db.Column(db.Boolean, default=True)
    include_users = db.Column(db.Boolean, default=True)
    enable_highlights = db.Column(db.Boolean, default=True)
    show_suggestions = db.Column(db.Boolean, default=True)
    
    # Filter preferences
    auto_apply_filters = db.Column(db.Boolean, default=False)
    remember_filters = db.Column(db.Boolean, default=True)
    
    # Privacy options
    save_search_history = db.Column(db.Boolean, default=True)
    anonymous_search = db.Column(db.Boolean, default=False)
    
    # Advanced preferences
    search_scope = db.Column(db.String(20), default='all')
    time_filter = db.Column(db.String(20))
    language = db.Column(db.String(10))
    min_quality = db.Column(db.String(20))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='search_preferences')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_search_prefs_user', 'user_id'),
    )
    
    def to_dict(self):
        """Convert preferences to dictionary"""
        return {
            'results_per_page': self.results_per_page,
            'default_sort': self.default_sort,
            'default_order': self.default_order,
            'include_comments': self.include_comments,
            'include_users': self.include_users,
            'enable_highlights': self.enable_highlights,
            'show_suggestions': self.show_suggestions,
            'auto_apply_filters': self.auto_apply_filters,
            'remember_filters': self.remember_filters,
            'save_search_history': self.save_search_history,
            'anonymous_search': self.anonymous_search,
            'search_scope': self.search_scope,
            'time_filter': self.time_filter,
            'language': self.language,
            'min_quality': self.min_quality
        }

# API Authentication Models

class APIKey(db.Model):
    """API Key Model for API authentication"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    key_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    api_key = db.Column(db.String(64), nullable=False)  # Only used during creation/rotation
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    permissions = db.Column(db.JSON, default=list)  # List of permissions
    description = db.Column(db.Text)
    rate_limit = db.Column(db.Integer, default=1000)  # Requests per hour
    expires_at = db.Column(db.DateTime, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    usage_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='api_keys')
    usage_logs = db.relationship('APIUsage', backref='key_usage', lazy='dynamic')
    
    def __repr__(self):
        return f'<APIKey {self.name}>'
    
    def is_expired(self):
        """Check if API key is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def is_valid(self):
        """Check if API key is valid (not expired and not revoked)"""
        return self.is_active and not self.is_expired() and not self.revoked_at
    
    def revoke(self):
        """Revoke the API key"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def has_permission(self, permission):
        """Check if API key has the requested permission"""
        return permission in self.permissions
    
    def update_usage(self):
        """Update usage statistics"""
        self.last_used_at = datetime.utcnow()
        self.usage_count += 1
        self.updated_at = datetime.utcnow()

class APIUsage(db.Model):
    """API Usage Tracking Model"""
    __tablename__ = 'api_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=False, index=True)
    endpoint = db.Column(db.String(100), nullable=False)
    request_count = db.Column(db.Integer, default=1)
    last_request = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    api_key = db.relationship('APIKey', backref='usage_records')
    
    def __repr__(self):
        return f'<APIUsage {self.endpoint}>'
    
    @staticmethod
    def record_usage(api_key_id, endpoint):
        """Record API usage"""
        # Find existing usage record for today
        today = datetime.utcnow().date()
        usage = APIUsage.query.filter(
            APIUsage.api_key_id == api_key_id,
            APIUsage.endpoint == endpoint,
            db.func.date(APIUsage.created_at) == today
        ).first()
        
        if usage:
            usage.request_count += 1
            usage.last_request = datetime.utcnow()
        else:
            usage = APIUsage(
                api_key_id=api_key_id,
                endpoint=endpoint,
                request_count=1,
                created_at=datetime.utcnow()
            )
            db.session.add(usage)
        
        db.session.commit()
        return usage

class APICache(db.Model):
    """API Response Cache Model"""
    __tablename__ = 'api_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    cache_data = db.Column(db.JSON, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    hit_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<APICache {self.cache_key[:20]}...>'
    
    def is_expired(self):
        """Check if cache entry is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if cache entry is valid (not expired)"""
        return not self.is_expired()
    
    def hit(self):
        """Record a cache hit"""
        self.hit_count += 1
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def get(cache_key):
        """Get cache entry"""
        cache = APICache.query.filter_by(cache_key=cache_key).first()
        if cache and cache.is_valid():
            cache.hit()
            db.session.commit()
            return cache.cache_data
        return None
    
    @staticmethod
    def set(cache_key, data, expires_in=3600):
        """Set cache entry"""
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        cache = APICache.query.filter_by(cache_key=cache_key).first()
        if cache:
            cache.cache_data = data
            cache.expires_at = expires_at
            cache.updated_at = datetime.utcnow()
        else:
            cache = APICache(
                cache_key=cache_key,
                cache_data=data,
                expires_at=expires_at
            )
            db.session.add(cache)
        
        db.session.commit()
        return cache
    
    @staticmethod
    def delete(cache_key):
        """Delete cache entry"""
        cache = APICache.query.filter_by(cache_key=cache_key).first()
        if cache:
            db.session.delete(cache)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def clear_expired():
        """Clear expired cache entries"""
        expired = APICache.query.filter(
            APICache.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        return expired

# Message System Models

class MessageThread(db.Model):
    """Model for conversation threading"""
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=True)
    participant_ids = db.Column(db.Text, nullable=False)  # JSON array of user IDs
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Thread statistics
    message_count = db.Column(db.Integer, default=0)
    unread_count = db.Column(db.Integer, default=0)
    
    # Thread settings
    is_archived = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_muted = db.Column(db.Boolean, default=False)
    
    # Thread metadata
    thread_type = db.Column(db.String(20), default='private')  # 'private', 'group', 'system'
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    
    def get_participants(self):
        """Get list of participant IDs"""
        import json
        return json.loads(self.participant_ids) if self.participant_ids else []
    
    def set_participants(self, participant_list):
        """Set participant IDs"""
        import json
        self.participant_ids = json.dumps(participant_list)
    
    def add_participant(self, user_id):
        """Add a participant to the thread"""
        participants = self.get_participants()
        if user_id not in participants:
            participants.append(user_id)
            self.set_participants(participants)
    
    def remove_participant(self, user_id):
        """Remove a participant from the thread"""
        participants = self.get_participants()
        if user_id in participants:
            participants.remove(user_id)
            self.set_participants(participants)

class MessageSearchIndex(db.Model):
    """Model for message search indexing"""
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    content_vector = db.Column(db.Text, nullable=False)  # Full-text search vector
    keywords = db.Column(db.Text, nullable=True)  # Extracted keywords
    indexed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Search metadata
    search_rank = db.Column(db.Float, default=1.0)  # Search ranking score
    search_frequency = db.Column(db.Integer, default=0)  # How often searched
    last_searched = db.Column(db.DateTime)
    
    # Content analysis
    word_count = db.Column(db.Integer, default=0)
    language = db.Column(db.String(10), default='en')
    sentiment_score = db.Column(db.Float)  # Sentiment analysis score
    
    # Index status
    is_indexed = db.Column(db.Boolean, default=True)
    index_version = db.Column(db.Integer, default=1)
    
    message = db.relationship('Message', backref='search_index')
    
    @staticmethod
    def index_message(message):
        """Create or update search index for a message"""
        from app.utils.message_search import extract_keywords, generate_search_vector, analyze_content
        
        # Extract keywords and generate search vector
        keywords = extract_keywords(message.content)
        search_vector = generate_search_vector(message.content)
        content_analysis = analyze_content(message.content)
        
        # Create or update index
        search_index = MessageSearchIndex.query.filter_by(message_id=message.id).first()
        if not search_index:
            search_index = MessageSearchIndex(message_id=message.id)
        
        search_index.content_vector = search_vector
        search_index.keywords = keywords
        search_index.word_count = len(message.content.split())
        search_index.sentiment_score = content_analysis.get('sentiment')
        search_index.indexed_at = datetime.utcnow()
        
        db.session.add(search_index)
        db.session.commit()
        
        return search_index

class MessageAttachment(db.Model):
    """Model for message file attachments"""
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'image', 'document', 'video', 'audio', 'other'
    mime_type = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Integer, nullable=False)  # Size in bytes
    
    # File processing
    thumbnail_path = db.Column(db.String(500), nullable=True)
    preview_path = db.Column(db.String(500), nullable=True)
    is_processed = db.Column(db.Boolean, default=False)
    
    # Security and access
    is_public = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)
    last_downloaded = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    message = db.relationship('Message', backref='attachments')
    uploader = db.relationship('User', backref='uploaded_attachments')

class MessageForward(db.Model):
    """Model for tracking message forwarding"""
    id = db.Column(db.Integer, primary_key=True)
    original_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    forwarded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    forwarded_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Forward metadata
    forward_method = db.Column(db.String(20), default='manual')  # 'manual', 'auto', 'template'
    forward_note = db.Column(db.Text, nullable=True)  # Optional note added to forward
    is_private_forward = db.Column(db.Boolean, default=False)  # Hide original sender
    
    original_message = db.relationship('Message', foreign_keys=[original_message_id], backref='forwards')
    forwarded_by = db.relationship('User', foreign_keys=[forwarded_by_id], backref='sent_forwards')
    forwarded_to = db.relationship('User', foreign_keys=[forwarded_to_id], backref='received_forwards')

class MessageSearchAnalytics(db.Model):
    """Model for tracking search analytics"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    search_query = db.Column(db.Text, nullable=False)
    search_type = db.Column(db.String(20), default='basic')  # 'basic', 'advanced', 'boolean'
    results_count = db.Column(db.Integer, default=0)
    search_time = db.Column(db.Float, nullable=False)  # Search execution time in seconds
    
    # Search filters used
    filters = db.Column(db.Text, nullable=True)  # JSON of applied filters
    sort_by = db.Column(db.String(20), nullable=True)  # 'relevance', 'date', 'sender'
    
    # User interaction
    clicked_result_id = db.Column(db.Integer, nullable=True)  # Which result was clicked
    session_id = db.Column(db.String(100), nullable=True)  # Search session identifier
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='message_search_analytics')

class MessageTemplate(db.Model):
    """Model for message templates"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), default='general')  # 'general', 'welcome', 'support', etc.
    variables = db.Column(db.Text, nullable=True)  # JSON array of variables
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage statistics
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='message_templates')
    
    def get_variables(self):
        """Get list of template variables"""
        import json
        return json.loads(self.variables) if self.variables else []
    
    def set_variables(self, variables_list):
        """Set template variables"""
        import json
        self.variables = json.dumps(variables_list)
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()

class AuditLog(db.Model):
    """Model for tracking user actions and system events"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 'create_post', 'edit_post', 'delete_post', etc.
    target_type = db.Column(db.String(50), nullable=False)  # 'post', 'comment', 'user', etc.
    target_id = db.Column(db.Integer, nullable=False)
    
    # Store old and new values as JSON for audit trail
    old_values = db.Column(db.Text, nullable=True)  # JSON string of old values
    new_values = db.Column(db.Text, nullable=True)  # JSON string of new values
    
    # Additional metadata
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6 address
    user_agent = db.Column(db.Text, nullable=True)  # Browser user agent
    session_id = db.Column(db.String(100), nullable=True)  # Session identifier
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def get_old_values(self):
        """Get old values as dictionary"""
        import json
        return json.loads(self.old_values) if self.old_values else {}
    
    def set_old_values(self, values_dict):
        """Set old values from dictionary"""
        import json
        self.old_values = json.dumps(values_dict) if values_dict else None
    
    def get_new_values(self):
        """Get new values as dictionary"""
        import json
        return json.loads(self.new_values) if self.new_values else {}
    
    def set_new_values(self, values_dict):
        """Set new values from dictionary"""
        import json
        self.new_values = json.dumps(values_dict) if values_dict else None
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user.username} on {self.target_type} {self.target_id}>'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
