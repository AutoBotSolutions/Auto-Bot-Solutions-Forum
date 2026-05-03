from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from flask_login import UserMixin

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
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    posts = db.relationship('Post', backref='author', lazy='dynamic')
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
        self.updated_at = datetime.utcnow()
    
    def unban(self):
        """Unban user account"""
        self.is_banned = False
        self.is_active = True
        self.suspension_reason = None
        self.banned_at = None
        self.banned_by = None
        self.updated_at = datetime.utcnow()
    
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

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_bookmark'),)

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
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
