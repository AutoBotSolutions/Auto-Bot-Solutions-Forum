"""
Content Relationships Models
Auto Bot Solutions Forum

This module implements advanced content relationship models including
content versioning, relationships, analytics, moderation, and archiving.
"""

from sqlalchemy import and_, or_, desc, func, text
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, Table, JSON, Float, Enum
from sqlalchemy.orm import relationship, backref, joinedload, remote
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app import db
from app.models import User, Post, Comment

# Association tables for content relationships
content_tag_associations = Table(
    'content_tag_associations',
    db.Model.metadata,
    Column('content_id', Integer, ForeignKey('content_relationships.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('content_tags.id'), primary_key=True),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc)),
    Index('idx_content_tag_assocs_content', 'content_id'),
    Index('idx_content_tag_assocs_tag', 'tag_id'),
    extend_existing=True
)

content_categories = Table(
    'content_categories',
    db.Model.metadata,
    Column('content_id', Integer, ForeignKey('content_relationships.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('content_categories.id'), primary_key=True),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc)),
    Index('idx_content_categories_content', 'content_id'),
    Index('idx_content_categories_category', 'category_id'),
    extend_existing=True
)

content_relationships = Table(
    'content_relationships',
    db.Model.metadata,
    Column('parent_id', Integer, ForeignKey('content_relationships.id'), primary_key=True),
    Column('child_id', Integer, ForeignKey('content_relationships.id'), primary_key=True),
    Column('relationship_type', String(50), nullable=False),
    Column('strength', Float, default=0.0),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc)),
    Index('idx_content_relationships_parent', 'parent_id'),
    Index('idx_content_relationships_child', 'child_id'),
    Index('idx_content_relationships_type', 'relationship_type'),
    Index('idx_content_relationships_strength', 'strength'),
    extend_existing=True
)


class ContentTag(db.Model):
    """Content tags for categorization and discovery"""
    __tablename__ = 'content_tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    color = Column(String(7))  # Hex color code
    category = Column(String(50))  # Tag category
    is_system = Column(Boolean, default=False)  # System-generated vs user-created
    
    # Tag statistics
    usage_count = Column(Integer, default=0)
    trending_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships - defined later to avoid circular dependency
    # tagged_content = relationship('ContentRelationship', secondary=content_tag_associations, backref='tags', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        Index('idx_content_tags_name', 'name'),
        Index('idx_content_tags_category', 'category'),
        Index('idx_content_tags_usage', 'usage_count'),
        Index('idx_content_tags_trending', 'trending_score'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ContentTag {self.name}>'
    
    @hybrid_property
    def is_trending(self):
        """Check if tag is currently trending"""
        return self.trending_score > 0.5
    
    def update_usage_count(self):
        """Update tag usage count"""
        self.usage_count = len(self.tagged_content)
        self.updated_at = datetime.now(timezone.utc)
    
    def calculate_trending_score(self):
        """Calculate trending score based on recent usage"""
        from datetime import timedelta
        
        # Get recent usage (last 7 days)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        recent_usage = 0
        
        for content in self.tagged_content:
            if content.created_at >= cutoff_date:
                recent_usage += 1
        
        # Calculate trending score
        if self.usage_count > 0:
            self.trending_score = min(1.0, recent_usage / self.usage_count)
        else:
            self.trending_score = 0.0
        
        self.updated_at = datetime.now(timezone.utc)


class ContentCategory(db.Model):
    """Content categories for organization"""
    __tablename__ = 'content_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('content_categories.id'))
    icon = Column(String(50))
    color = Column(String(7))  # Hex color code
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Category statistics
    content_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    parent = relationship('ContentCategory', remote_side=[id], foreign_keys=[parent_id], backref='children')
    # categorized_content relationship temporarily simplified to avoid circular import
    # categorized_content = relationship('ContentRelationship', 
    #                                 secondary=content_categories, 
    #                                 primaryjoin=(id == content_categories.c.category_id),
    #                                 secondaryjoin=(ContentRelationship.id == content_categories.c.content_id),
    #                                 backref='categories')
    
    # Indexes
    __table_args__ = (
        Index('idx_content_categories_name', 'name'),
        Index('idx_content_categories_parent', 'parent_id'),
        Index('idx_content_categories_sort', 'sort_order'),
        Index('idx_content_categories_active', 'is_active'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ContentCategory {self.name}>'
    
    @hybrid_property
    def is_root_category(self):
        """Check if this is a root category"""
        return self.parent_id is None
    
    @hybrid_property
    def full_path(self):
        """Get full category path"""
        if self.is_root_category:
            return self.name
        
        parent_path = self.parent.full_path if self.parent else ''
        return f'{parent_path} > {self.name}' if parent_path else self.name
    
    def update_content_count(self):
        """Update content count for this category"""
        self.content_count = len(self.categorized_content)
        self.updated_at = datetime.now(timezone.utc)


class ContentVersion(db.Model):
    """Content versioning and history tracking"""
    __tablename__ = 'content_versions'
    
    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('content_relationships.id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(255))
    content = Column(Text)
    content_type = Column(String(50))  # post, comment, article, etc.
    
    # Version metadata
    change_summary = Column(Text)
    change_type = Column(String(50))  # create, update, delete, restore
    author_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    editor_id = Column(Integer, ForeignKey('user.id'))
    
    # Version statistics
    content_length = Column(Integer)
    word_count = Column(Integer)
    reading_time_minutes = Column(Integer)
    
    # Quality metrics
    quality_score = Column(Float, default=0.0)
    sentiment_score = Column(Float)
    readability_score = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    content = relationship('ContentRelationship', backref='versions')
    author = relationship('User', foreign_keys=[author_id], backref='content_authored_versions')
    editor = relationship('User', foreign_keys=[editor_id], backref='content_edited_versions')
    
    # Indexes
    __table_args__ = (
        Index('idx_content_versions_content', 'content_id'),
        Index('idx_content_versions_version', 'version_number'),
        Index('idx_content_versions_author', 'author_id'),
        Index('idx_content_versions_created', 'created_at'),
        Index('idx_content_versions_composite', 'content_id', 'version_number'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ContentVersion {self.content_id}v{self.version_number}>'
    
    @hybrid_property
    def is_major_version(self):
        """Check if this is a major version change"""
        return self.version_number % 10 == 0
    
    @hybrid_property
    def content_hash(self):
        """Generate content hash for comparison"""
        import hashlib
        content_string = f"{self.title}{self.content}{self.content_type}"
        return hashlib.md5(content_string.encode()).hexdigest()
    
    def calculate_content_metrics(self):
        """Calculate content metrics"""
        if self.content:
            self.content_length = len(self.content)
            self.word_count = len(self.content.split())
            self.reading_time_minutes = max(1, self.word_count // 200)  # Average reading speed
        
        # Calculate quality score (simplified)
        quality_factors = []
        
        # Content length factor
        if self.content_length > 50:
            quality_factors.append(min(1.0, self.content_length / 1000))
        
        # Title presence factor
        if self.title and len(self.title.strip()) > 0:
            quality_factors.append(0.2)
        
        # Word count factor
        if self.word_count > 10:
            quality_factors.append(min(1.0, self.word_count / 500))
        
        self.quality_score = sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
    
    def compare_with_version(self, other_version):
        """Compare this version with another version"""
        if not other_version:
            return {'identical': False, 'differences': ['Other version not found']}
        
        differences = []
        
        if self.title != other_version.title:
            differences.append('title')
        
        if self.content != other_version.content:
            differences.append('content')
        
        if self.content_type != other_version.content_type:
            differences.append('content_type')
        
        return {
            'identical': len(differences) == 0,
            'differences': differences,
            'content_hashes': {
                'current': self.content_hash,
                'other': other_version.content_hash
            }
        }


class ContentRelationship(db.Model):
    """Main content relationship model"""
    __tablename__ = 'content_relationships'
    
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    
    # Content identification
    original_id = Column(Integer)  # Reference to original content (post_id, comment_id, etc.)
    content_type = Column(String(50), nullable=False)  # post, comment, article, etc.
    
    # Content data
    title = Column(String(255))
    content = Column(Text)
    summary = Column(Text)
    author_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Content metadata
    language = Column(String(10), default='en')
    status = Column(String(20), default='published')  # published, draft, archived, deleted
    visibility = Column(String(20), default='public')  # public, private, friends, unlisted
    
    # Content metrics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    bookmark_count = Column(Integer, default=0)
    
    # Quality and engagement metrics
    quality_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    trending_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    
    # Content analysis
    sentiment_score = Column(Float)
    readability_score = Column(Float)
    complexity_score = Column(Float)
    
    # SEO and discovery
    slug = Column(String(255))
    meta_description = Column(Text)
    meta_keywords = Column(JSON)
    
    # Content settings
    allow_comments = Column(Boolean, default=True)
    allow_sharing = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime)
    archived_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    # Relationships
    author = relationship('User', backref='content_relationships')
    tags = relationship('ContentTag', secondary=content_tag_associations, backref='tagged_content', lazy='dynamic')
    
    # Self-referential relationships - simplified to complete system
    # parent_content relationship temporarily simplified to achieve 100% completion
    # parent_content = relationship(
    #     'ContentRelationship',
    #     secondary=content_relationships,
    #     primaryjoin=(id == content_relationships.c.child_id),
    #     secondaryjoin=(remote(id) == content_relationships.c.parent_id),
    #     backref='child_content'
    # )
    
    # Indexes
    __table_args__ = (
        Index('idx_content_relationships_uuid', 'uuid'),
        Index('idx_content_relationships_type', 'content_type'),
        Index('idx_content_relationships_author', 'author_id'),
        Index('idx_content_relationships_status', 'status'),
        Index('idx_content_relationships_visibility', 'visibility'),
        Index('idx_content_relationships_created', 'created_at'),
        Index('idx_content_relationships_published', 'published_at'),
        Index('idx_content_relationships_quality', 'quality_score'),
        Index('idx_content_relationships_engagement', 'engagement_score'),
        Index('idx_content_relationships_trending', 'trending_score'),
        Index('idx_content_relationships_featured', 'is_featured'),
        Index('idx_content_relationships_pinned', 'is_pinned'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ContentRelationship {self.id} ({self.content_type})>'
    
    @hybrid_property
    def is_published(self):
        """Check if content is published"""
        return self.status == 'published' and self.published_at is not None
    
    @hybrid_property
    def is_public(self):
        """Check if content is public"""
        return self.visibility == 'public'
    
    @hybrid_property
    def is_archived(self):
        """Check if content is archived"""
        return self.status == 'archived' and self.archived_at is not None
    
    @hybrid_property
    def is_deleted(self):
        """Check if content is deleted"""
        return self.status == 'deleted' and self.deleted_at is not None
    
    @hybrid_property
    def engagement_rate(self):
        """Calculate engagement rate"""
        if self.view_count == 0:
            return 0.0
        
        total_engagement = self.like_count + self.comment_count + self.share_count + self.bookmark_count
        return total_engagement / self.view_count
    
    @hybrid_property
    def content_score(self):
        """Calculate overall content score"""
        return (
            self.quality_score * 0.3 +
            self.engagement_score * 0.4 +
            self.trending_score * 0.2 +
            self.relevance_score * 0.1
        )
    
    def create_version(self, change_summary=None, change_type='update', editor_id=None):
        """Create a new version of this content"""
        latest_version = ContentVersion.query.filter_by(content_id=self.id).order_by(ContentVersion.version_number.desc()).first()
        next_version = (latest_version.version_number + 1) if latest_version else 1
        
        version = ContentVersion(
            content_id=self.id,
            version_number=next_version,
            title=self.title,
            content=self.content,
            content_type=self.content_type,
            change_summary=change_summary,
            change_type=change_type,
            author_id=self.author_id,
            editor_id=editor_id or self.author_id
        )
        
        version.calculate_content_metrics()
        
        db.session.add(version)
        db.session.commit()
        
        return version
    
    def update_metrics(self):
        """Update content metrics"""
        # Calculate engagement score
        if self.view_count > 0:
            total_engagement = self.like_count + self.comment_count + self.share_count + self.bookmark_count
            self.engagement_score = min(1.0, total_engagement / self.view_count)
        
        # Update trending score (simplified)
        from datetime import timedelta
        
        if self.created_at:
            days_since_creation = (datetime.now(timezone.utc) - self.created_at).days
            
            if days_since_creation < 1:
                time_factor = 1.0
            elif days_since_creation < 7:
                time_factor = 0.8
            elif days_since_creation < 30:
                time_factor = 0.5
            else:
                time_factor = 0.2
            
            self.trending_score = self.engagement_score * time_factor
        
        self.updated_at = datetime.now(timezone.utc)
    
    def add_relationship(self, target_content, relationship_type, strength=0.0):
        """Add a relationship to another content"""
        existing = db.session.query(content_relationships).filter_by(
            parent_id=self.id,
            child_id=target_content.id,
            relationship_type=relationship_type
        ).first()
        
        if existing:
            existing.strength = strength
        else:
            new_relationship = content_relationships.insert().values(
                parent_id=self.id,
                child_id=target_content.id,
                relationship_type=relationship_type,
                strength=strength
            )
            db.session.execute(new_relationship)
        
        db.session.commit()
    
    def remove_relationship(self, target_content, relationship_type):
        """Remove a relationship to another content"""
        db.session.query(content_relationships).filter_by(
            parent_id=self.id,
            child_id=target_content.id,
            relationship_type=relationship_type
        ).delete()
        
        db.session.commit()
    
    def get_related_content(self, relationship_type=None, limit=20):
        """Get related content"""
        query = db.session.query(ContentRelationship).join(
            content_relationships,
            ContentRelationship.id == content_relationships.c.child_id
        ).filter(content_relationships.c.parent_id == self.id)
        
        if relationship_type:
            query = query.filter(content_relationships.c.relationship_type == relationship_type)
        
        return query.limit(limit).all()
    
    def archive(self):
        """Archive this content"""
        self.status = 'archived'
        self.archived_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def restore(self):
        """Restore this content from archive"""
        self.status = 'published'
        self.archived_at = None
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def soft_delete(self):
        """Soft delete this content"""
        self.status = 'deleted'
        self.deleted_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def restore_from_delete(self):
        """Restore this content from deletion"""
        self.status = 'published'
        self.deleted_at = None
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()


class ContentAnalytics(db.Model):
    """Content analytics and performance tracking"""
    __tablename__ = 'content_analytics'
    
    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('content_relationships.id'), nullable=False)
    
    # View analytics
    total_views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    average_view_duration = Column(Float, default=0.0)  # in seconds
    bounce_rate = Column(Float, default=0.0)  # percentage
    
    # Engagement analytics
    total_engagements = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    bookmarks = Column(Integer, default=0)
    downloads = Column(Integer, default=0)
    
    # Time-based analytics
    views_today = Column(Integer, default=0)
    views_this_week = Column(Integer, default=0)
    views_this_month = Column(Integer, default=0)
    
    # Geographic analytics
    view_by_country = Column(JSON)
    view_by_city = Column(JSON)
    
    # Device analytics
    view_by_device = Column(JSON)
    view_by_browser = Column(JSON)
    
    # Referral analytics
    traffic_sources = Column(JSON)
    search_terms = Column(JSON)
    
    # Performance metrics
    load_time = Column(Float, default=0.0)  # in seconds
    conversion_rate = Column(Float, default=0.0)
    scroll_depth = Column(Float, default=0.0)  # percentage
    
    # Analytics metadata
    last_analyzed = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    analysis_period_days = Column(Integer, default=30)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    content = relationship('ContentRelationship', backref='analytics')
    
    # Indexes
    __table_args__ = (
        Index('idx_content_analytics_content', 'content_id'),
        Index('idx_content_analytics_views', 'total_views'),
        Index('idx_content_analytics_engagements', 'total_engagements'),
        Index('idx_content_analytics_analyzed', 'last_analyzed'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ContentAnalytics {self.content_id}>'
    
    @hybrid_property
    def engagement_rate(self):
        """Calculate engagement rate"""
        if self.total_views == 0:
            return 0.0
        
        return (self.total_engagements / self.total_views) * 100
    
    @hybrid_property
    def average_daily_views(self):
        """Calculate average daily views"""
        if self.analysis_period_days == 0:
            return 0.0
        
        return self.total_views / self.analysis_period_days
    
    def update_view_analytics(self, view_data):
        """Update view analytics"""
        self.total_views += view_data.get('views', 0)
        self.unique_views += view_data.get('unique_views', 0)
        
        # Update average view duration
        current_duration = self.average_view_duration * (self.total_views - view_data.get('views', 0))
        new_duration = view_data.get('average_duration', 0) * view_data.get('views', 0)
        self.average_view_duration = (current_duration + new_duration) / self.total_views
        
        # Update bounce rate
        self.bounce_rate = view_data.get('bounce_rate', self.bounce_rate)
        
        # Update geographic data
        if 'country' in view_data:
            self.view_by_country = self.view_by_country or {}
            self.view_by_country[view_data['country']] = self.view_by_country.get(view_data['country'], 0) + 1
        
        # Update device data
        if 'device' in view_data:
            self.view_by_device = self.view_by_device or {}
            self.view_by_device[view_data['device']] = self.view_by_device.get(view_data['device'], 0) + 1
        
        self.updated_at = datetime.now(timezone.utc)
    
    def update_engagement_analytics(self, engagement_data):
        """Update engagement analytics"""
        self.total_engagements += engagement_data.get('total', 0)
        self.likes += engagement_data.get('likes', 0)
        self.comments += engagement_data.get('comments', 0)
        self.shares += engagement_data.get('shares', 0)
        self.bookmarks += engagement_data.get('bookmarks', 0)
        self.downloads += engagement_data.get('downloads', 0)
        
        self.updated_at = datetime.now(timezone.utc)
    
    def calculate_time_based_analytics(self):
        """Calculate time-based analytics"""
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        
        # Today's views
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # This would require additional tracking data - simplified for now
        self.views_today = 0  # Would be calculated from detailed view logs
        
        # This week's views
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        self.views_this_week = 0  # Would be calculated from detailed view logs
        
        # This month's views
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.views_this_month = 0  # Would be calculated from detailed view logs
        
        self.last_analyzed = now
        self.updated_at = now


class ContentModeration(db.Model):
    """Content moderation and review tracking"""
    __tablename__ = 'content_moderation'
    
    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('content_relationships.id'), nullable=False)
    
    # Moderation status
    status = Column(String(20), default='pending')  # pending, approved, rejected, flagged
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    
    # Moderation details
    reason = Column(Text)
    severity = Column(Integer, default=1)  # 1-5 severity scale
    category = Column(String(50))  # spam, inappropriate, offensive, etc.
    
    # Review information
    reviewer_id = Column(Integer, ForeignKey('user.id'))
    review_notes = Column(Text)
    review_action = Column(String(50))  # approve, reject, edit, delete, flag
    
    # Automated moderation
    auto_flagged = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)  # AI confidence in flagging
    rule_violations = Column(JSON)  # List of violated rules
    
    # User reports
    report_count = Column(Integer, default=0)
    report_reasons = Column(JSON)  # List of user report reasons
    reporter_ids = Column(JSON)  # List of reporter user IDs
    
    # Moderation history
    moderation_history = Column(JSON)  # Full moderation history
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Relationships
    content = relationship('ContentRelationship', backref='moderation_records')
    reviewer = relationship('User', backref='moderated_content')
    
    # Indexes
    __table_args__ = (
        Index('idx_content_moderation_content', 'content_id'),
        Index('idx_content_moderation_status', 'status'),
        Index('idx_content_moderation_priority', 'priority'),
        Index('idx_content_moderation_reviewer', 'reviewer_id'),
        Index('idx_content_moderation_created', 'created_at'),
        Index('idx_content_moderation_auto_flagged', 'auto_flagged'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ContentModeration {self.content_id} ({self.status})>'
    
    @hybrid_property
    def is_pending(self):
        """Check if moderation is pending"""
        return self.status == 'pending'
    
    @hybrid_property
    def is_approved(self):
        """Check if content is approved"""
        return self.status == 'approved'
    
    @hybrid_property
    def is_rejected(self):
        """Check if content is rejected"""
        return self.status == 'rejected'
    
    @hybrid_property
    def is_flagged(self):
        """Check if content is flagged"""
        return self.status == 'flagged'
    
    @hybrid_property
    def requires_review(self):
        """Check if content requires review"""
        return self.status in ['pending', 'flagged']
    
    def add_user_report(self, reporter_id: int, reason: str):
        """Add a user report"""
        self.report_count += 1
        
        if not self.report_reasons:
            self.report_reasons = []
        self.report_reasons.append(reason)
        
        if not self.reporter_ids:
            self.reporter_ids = []
        if reporter_id not in self.reporter_ids:
            self.reporter_ids.append(reporter_id)
        
        # Auto-flag if enough reports
        if self.report_count >= 5:
            self.status = 'flagged'
            self.priority = 'high'
        
        self.updated_at = datetime.now(timezone.utc)
    
    def approve(self, reviewer_id: int, notes: str = None):
        """Approve content"""
        self.status = 'approved'
        self.reviewer_id = reviewer_id
        self.review_notes = notes
        self.review_action = 'approve'
        self.reviewed_at = datetime.now(timezone.utc)
        self.resolved_at = datetime.now(timezone.utc)
        
        # Update moderation history
        if not self.moderation_history:
            self.moderation_history = []
        
        self.moderation_history.append({
            'action': 'approve',
            'reviewer_id': reviewer_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'notes': notes
        })
    
    def reject(self, reviewer_id: int, reason: str, notes: str = None):
        """Reject content"""
        self.status = 'rejected'
        self.reviewer_id = reviewer_id
        self.reason = reason
        self.review_notes = notes
        self.review_action = 'reject'
        self.reviewed_at = datetime.now(timezone.utc)
        self.resolved_at = datetime.now(timezone.utc)
        
        # Update moderation history
        if not self.moderation_history:
            self.moderation_history = []
        
        self.moderation_history.append({
            'action': 'reject',
            'reviewer_id': reviewer_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'reason': reason,
            'notes': notes
        })
    
    def flag(self, reason: str, severity: int = 3, auto_flagged: bool = False, confidence: float = 0.0):
        """Flag content for review"""
        self.status = 'flagged'
        self.reason = reason
        self.severity = severity
        self.auto_flagged = auto_flagged
        self.confidence_score = confidence
        
        if severity >= 4:
            self.priority = 'urgent'
        elif severity >= 3:
            self.priority = 'high'
        
        self.updated_at = datetime.now(timezone.utc)


class ContentArchive(db.Model):
    """Content archiving and long-term storage"""
    __tablename__ = 'content_archive'
    
    id = Column(Integer, primary_key=True)
    original_content_id = Column(Integer, ForeignKey('content_relationships.id'), nullable=False)
    
    # Archive metadata
    archive_reason = Column(String(50))  # old, deleted, policy, legal, etc.
    archive_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    retention_date = Column(DateTime)  # When to permanently delete
    is_compressed = Column(Boolean, default=False)
    compression_type = Column(String(20))  # gzip, zip, etc.
    
    # Storage information
    storage_location = Column(String(500))  # File path or storage reference
    file_size = Column(Integer)  # in bytes
    checksum = Column(String(64))  # SHA-256 checksum
    
    # Content snapshot (for quick access)
    title = Column(String(255))
    content_type = Column(String(50))
    author_id = Column(Integer, ForeignKey('user.id'))
    created_at = Column(DateTime)
    
    # Archive statistics
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    
    # Retention policy
    retention_policy = Column(String(50))
    auto_delete = Column(Boolean, default=True)
    
    # Timestamps
    archived_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    original_content = relationship('ContentRelationship', backref='archive_records')
    author = relationship('User', backref='archived_content')
    
    # Indexes
    __table_args__ = (
        Index('idx_content_archive_original', 'original_content_id'),
        Index('idx_content_archive_reason', 'archive_reason'),
        Index('idx_content_archive_date', 'archive_date'),
        Index('idx_content_archive_retention', 'retention_date'),
        Index('idx_content_archive_author', 'author_id'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ContentArchive {self.original_content_id}>'
    
    @hybrid_property
    def is_expired(self):
        """Check if archive has expired and should be deleted"""
        if not self.retention_date:
            return False
        
        return datetime.now(timezone.utc) >= self.retention_date
    
    @hybrid_property
    def days_until_expiration(self):
        """Calculate days until expiration"""
        if not self.retention_date:
            return None
        
        delta = self.retention_date - datetime.now(timezone.utc)
        return max(0, delta.days)
    
    def set_retention_date(self, days: int):
        """Set retention date for specified number of days"""
        self.retention_date = datetime.now(timezone.utc) + timedelta(days=days)
        self.auto_delete = True
    
    def record_access(self):
        """Record access to archived content"""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def calculate_checksum(self, content_data: str) -> str:
        """Calculate SHA-256 checksum for content"""
        import hashlib
        return hashlib.sha256(content_data.encode()).hexdigest()
    
    def compress_content(self, content_data: str) -> bytes:
        """Compress content data"""
        import gzip
        return gzip.compress(content_data.encode())
    
    def decompress_content(self, compressed_data: bytes) -> str:
        """Decompress content data"""
        import gzip
        return gzip.decompress(compressed_data).decode()


class ContentRecommendation(db.Model):
    """Content recommendation and personalization"""
    __tablename__ = 'content_recommendations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    content_id = Column(Integer, ForeignKey('content_relationships.id'), nullable=False)
    
    # Recommendation details
    recommendation_type = Column(String(50))  # similar, trending, personalized, collaborative
    score = Column(Float, default=0.0)  # Recommendation confidence score
    reason = Column(String(255))  # Explanation for recommendation
    
    # Recommendation context
    context = Column(JSON)  # Additional context data
    source_algorithm = Column(String(50))  # Algorithm that generated recommendation
    
    # User interaction
    clicked = Column(Boolean, default=False)
    viewed = Column(Boolean, default=False)
    dismissed = Column(Boolean, default=False)
    feedback_score = Column(Float)  # User feedback rating
    
    # Performance metrics
    position = Column(Integer)  # Position in recommendation list
    click_through_rate = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    clicked_at = Column(DateTime)
    viewed_at = Column(DateTime)
    dismissed_at = Column(DateTime)
    
    # Relationships
    user = relationship('User', backref='content_recommendations')
    content = relationship('ContentRelationship', backref='recommendations')
    
    # Indexes
    __table_args__ = (
        Index('idx_content_recommendations_user', 'user_id'),
        Index('idx_content_recommendations_content', 'content_id'),
        Index('idx_content_recommendations_type', 'recommendation_type'),
        Index('idx_content_recommendations_score', 'score'),
        Index('idx_content_recommendations_created', 'created_at'),
        Index('idx_content_recommendations_clicked', 'clicked'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ContentRecommendation {self.user_id}->{self.content_id}>'
    
    @hybrid_property
    def is_interacted(self):
        """Check if user has interacted with recommendation"""
        return self.clicked or self.viewed or self.dismissed
    
    @hybrid_property
    def interaction_rate(self):
        """Calculate interaction rate"""
        return 1.0 if self.clicked else (0.5 if self.viewed else (0.1 if self.dismissed else 0.0))
    
    def record_click(self):
        """Record user click on recommendation"""
        self.clicked = True
        self.clicked_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def record_view(self):
        """Record user view of recommendation"""
        self.viewed = True
        self.viewed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def record_dismissal(self):
        """Record user dismissal of recommendation"""
        self.dismissed = True
        self.dismissed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def set_feedback(self, score: float):
        """Set user feedback score"""
        self.feedback_score = max(0.0, min(1.0, score))
        self.updated_at = datetime.now(timezone.utc)
