# Content Relationships System
## Auto Bot Solutions Forum

**Version:** 1.0.0  
**Last Updated:** May 13, 2026  
**Status:** ✅ Implemented and Debugged

---

## Overview

The Content Relationships System provides comprehensive content management, versioning, analytics, moderation, and personalization capabilities for the Auto Bot Solutions Forum. It enables sophisticated content relationships, automated moderation, and intelligent content recommendations.

### Key Features
- **Content Versioning**: Complete version history and change tracking
- **Content Analytics**: Performance metrics and engagement tracking
- **Content Moderation**: Automated moderation with review workflows
- **Content Archiving**: Long-term storage with retention policies
- **Content Recommendations**: Personalized content recommendations
- **Content Relationships**: Sophisticated content categorization and linking
- **Quality Scoring**: Automated content quality assessment

---

## Architecture

### System Components

#### **Models Layer**
- `ContentRelationship`: Core content management with relationships
- `ContentVersion`: Versioning and history tracking
- `ContentAnalytics`: Performance metrics and engagement data
- `ContentModeration`: Moderation workflow and review tracking
- `ContentArchive`: Archiving and retention management
- `ContentRecommendation`: Personalization and recommendations
- `ContentTag`: Tag management and categorization
- `ContentCategory`: Hierarchical category organization

#### **Service Layer**
- `ContentService`: Core content management operations
- `ContentAnalyticsService`: Analytics and trending analysis
- `ContentModerationService`: Automated moderation system
- `ContentRecommendationService`: Content personalization

#### **Utility Layer**
- `ContentValidators`: Input validation and business rules
- `ContentCalculators`: Quality scoring and metrics calculations
- `ContentHelpers`: Common content operations and helpers
- `ContentProcessor`: Event processing and content workflows

#### **Configuration Layer**
- `ContentRelationshipsConfig`: Centralized configuration management
- Content types, moderation rules, analytics settings
- Archiving policies and recommendation parameters

---

## Models Documentation

### ContentRelationship

**Purpose:** Core model for managing content with relationships, metadata, and analytics.

#### Fields
```python
class ContentRelationship(db.Model):
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    original_id = Column(Integer)  # Reference to original content
    content_type = Column(String(50), nullable=False)  # post, comment, article, etc.
    title = Column(String(255))
    content = Column(Text)
    summary = Column(Text)
    author_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    language = Column(String(10), default='en')
    status = Column(String(20), default='published')  # published, draft, archived, deleted
    visibility = Column(String(20), default='public')  # public, private, friends, unlisted
    
    # Metrics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    bookmark_count = Column(Integer, default=0)
    
    # Quality scores
    quality_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    trending_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    
    # SEO and discovery
    slug = Column(String(255))
    meta_description = Column(Text)
    meta_keywords = Column(JSON)
    
    # Settings
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
```

#### Content Types
- **post**: Standard forum post
- **comment**: Comment on content
- **article**: Long-form article
- **page**: Static page content
- **story**: Narrative content
- **tutorial**: Educational content
- **news**: News article
- **blog**: Blog post

#### Status Values
- **draft**: Unpublished draft
- **published**: Published content
- **archived**: Archived content
- **deleted**: Soft-deleted content

#### Visibility Levels
- **public**: Visible to everyone
- **private**: Visible only to author
- **friends**: Visible to friends only
- **unlisted**: Visible with direct link only

#### Hybrid Properties
- `is_published`: Returns True if status is 'published'
- `is_public`: Returns True if visibility is 'public'
- `is_archived`: Returns True if content is archived
- `is_deleted`: Returns True if content is deleted
- `engagement_rate`: Calculates engagement rate based on views and interactions
- `content_score`: Overall content quality score

#### Methods
- `create_version(change_summary, change_type)`: Creates a new version
- `update_metrics()`: Updates content metrics and scores
- `add_relationship(target_content, relationship_type, strength)`: Adds content relationship
- `archive()`: Archives the content
- `restore()`: Restores from archive
- `soft_delete()`: Soft deletes the content
- `generate_slug()`: Generates URL-friendly slug

### ContentVersion

**Purpose:** Tracks content version history with change management.

#### Fields
```python
class ContentVersion(db.Model):
    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('content_relationships.id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(255))
    content = Column(Text)
    content_type = Column(String(50))
    change_summary = Column(Text)
    change_type = Column(String(50))  # create, update, delete, restore
    author_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    editor_id = Column(Integer, ForeignKey('user.id'))
    
    # Content metrics
    content_length = Column(Integer)
    word_count = Column(Integer)
    reading_time_minutes = Column(Integer)
    
    # Quality metrics
    quality_score = Column(Float, default=0.0)
    sentiment_score = Column(Float)
    readability_score = Column(Float)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

#### Change Types
- **create**: Initial content creation
- **update**: Content update
- **delete**: Content deletion
- **restore**: Content restoration

#### Hybrid Properties
- `is_major_version`: Returns True for major version numbers
- `content_hash`: Generates content hash for comparison

#### Methods
- `calculate_content_metrics()`: Calculates content metrics
- `compare_with_version(other_version)`: Compares with another version
- `restore_content()`: Restores content from this version

### ContentAnalytics

**Purpose:** Tracks content performance metrics and engagement data.

#### Fields
```python
class ContentAnalytics(db.Model):
    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('content_relationships.id'), nullable=False)
    
    # View analytics
    total_views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    average_view_duration = Column(Float, default=0.0)
    bounce_rate = Column(Float, default=0.0)
    
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
    load_time = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    scroll_depth = Column(Float, default=0.0)
    
    last_analyzed = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    analysis_period_days = Column(Integer, default=30)
```

#### Hybrid Properties
- `engagement_rate`: Calculates engagement rate
- `average_daily_views`: Calculates average daily views

#### Methods
- `update_view_analytics(view_data)`: Updates view analytics
- `update_engagement_analytics(engagement_data)`: Updates engagement analytics
- `calculate_time_based_analytics()`: Calculates time-based analytics

### ContentModeration

**Purpose:** Manages content moderation workflow and review tracking.

#### Fields
```python
class ContentModeration(db.Model):
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
    confidence_score = Column(Float, default=0.0)
    rule_violations = Column(JSON)
    
    # User reports
    report_count = Column(Integer, default=0)
    report_reasons = Column(JSON)
    reporter_ids = Column(JSON)
    
    # Moderation history
    moderation_history = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime)
    resolved_at = Column(DateTime)
```

#### Status Values
- **pending**: Awaiting review
- **approved**: Content approved
- **rejected**: Content rejected
- **flagged**: Content flagged for review

#### Priority Levels
- **low**: Low priority (72-hour response)
- **normal**: Normal priority (24-hour response)
- **high**: High priority (8-hour response)
- **urgent**: Urgent priority (2-hour response)

#### Hybrid Properties
- `is_pending`: Returns True if status is 'pending'
- `is_approved`: Returns True if status is 'approved'
- `is_rejected`: Returns True if status is 'rejected'
- `is_flagged`: Returns True if status is 'flagged'
- `requires_review`: Returns True if review is needed

#### Methods
- `add_user_report(reporter_id, reason)`: Adds user report
- `approve(reviewer_id, notes)`: Approves content
- `reject(reviewer_id, reason, notes)`: Rejects content
- `flag(reason, severity, auto_flagged)`: Flags content for review

### ContentArchive

**Purpose:** Manages content archiving with retention policies.

#### Fields
```python
class ContentArchive(db.Model):
    id = Column(Integer, primary_key=True)
    original_content_id = Column(Integer, ForeignKey('content_relationships.id'), nullable=False)
    
    # Archive metadata
    archive_reason = Column(String(50))  # old, deleted, policy, legal, manual
    archive_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    retention_date = Column(DateTime)
    is_compressed = Column(Boolean, default=False)
    compression_type = Column(String(20))
    
    # Storage information
    storage_location = Column(String(500))
    file_size = Column(Integer)
    checksum = Column(String(64))
    
    # Content snapshot
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
```

#### Archive Reasons
- **old**: Old content
- **deleted**: Deleted content
- **policy**: Policy violation
- **legal**: Legal requirement
- **manual**: Manual archive

#### Hybrid Properties
- `is_expired`: Returns True if archive has expired
- `days_until_expiration`: Calculates days until expiration

#### Methods
- `set_retention_date(days)`: Sets retention date
- `record_access()`: Records archive access
- `calculate_checksum(content_data)`: Calculates content checksum
- `compress_content(content_data)`: Compresses content data
- `decompress_content(compressed_data)`: Decompresses content data

### ContentRecommendation

**Purpose:** Manages personalized content recommendations.

#### Fields
```python
class ContentRecommendation(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    content_id = Column(Integer, ForeignKey('content_relationships.id'), nullable=False)
    
    # Recommendation details
    recommendation_type = Column(String(50))  # similar, trending, personalized, collaborative
    score = Column(Float, default=0.0)
    reason = Column(String(255))
    
    # Recommendation context
    context = Column(JSON)
    source_algorithm = Column(String(50))
    
    # User interaction
    clicked = Column(Boolean, default=False)
    viewed = Column(Boolean, default=False)
    dismissed = Column(Boolean, default=False)
    feedback_score = Column(Float)
    
    # Performance metrics
    position = Column(Integer)
    click_through_rate = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    clicked_at = Column(DateTime)
    viewed_at = Column(DateTime)
    dismissed_at = Column(DateTime)
```

#### Recommendation Types
- **similar**: Similar content recommendations
- **trending**: Trending content recommendations
- **personalized**: Personalized recommendations
- **collaborative**: Collaborative filtering recommendations

#### Hybrid Properties
- `is_interacted`: Returns True if user has interacted
- `interaction_rate`: Calculates interaction rate

#### Methods
- `record_click()`: Records user click
- `record_view()`: Records user view
- `record_dismissal()`: Records user dismissal
- `set_feedback(score)`: Sets user feedback score

### ContentTag

**Purpose:** Manages content tagging and categorization.

#### Fields
```python
class ContentTag(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    color = Column(String(7))  # Hex color code
    category = Column(String(50))  # Tag category
    is_system = Column(Boolean, default=False)  # System-generated vs user-created
    
    # Tag statistics
    usage_count = Column(Integer, default=0)
    trending_score = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

#### Hybrid Properties
- `is_trending`: Returns True if tag is trending

#### Methods
- `update_usage_count()`: Updates tag usage count
- `calculate_trending_score()`: Calculates trending score

### ContentCategory

**Purpose:** Manages hierarchical content categories.

#### Fields
```python
class ContentCategory(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('content_categories.id'))
    icon = Column(String(50))
    color = Column(String(7))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Category statistics
    content_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

#### Hybrid Properties
- `is_root_category`: Returns True if this is a root category
- `full_path`: Returns full category path

#### Methods
- `update_content_count()`: Updates content count

---

## Services Documentation

### ContentService

**Purpose:** Core service for managing content operations.

#### Key Methods

##### create_content(user_id, title, content, content_type, visibility, summary, tags, categories, metadata)
```python
def create_content(self, user_id: int, title: str, content: str, content_type: str = None, 
                  visibility: str = 'public', summary: str = None, tags: List[str] = None,
                  categories: List[int] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Creates new content with relationships.
    
    Args:
        user_id: ID of the content author
        title: Content title
        content: Content body
        content_type: Type of content
        visibility: Content visibility level
        summary: Content summary
        tags: List of tags
        categories: List of category IDs
        metadata: Additional metadata
        
    Returns:
        Dict with success status and content data
    """
```

##### update_content(content_id, user_id, title, content, summary, tags, categories, change_summary, metadata)
```python
def update_content(self, content_id: int, user_id: int, title: str = None, content: str = None,
                  summary: str = None, tags: List[str] = None, categories: List[int] = None,
                  change_summary: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Updates existing content.
    
    Args:
        content_id: ID of the content to update
        user_id: ID of the user updating
        title: New title
        content: New content
        summary: New summary
        tags: New tags
        categories: New categories
        change_summary: Summary of changes
        metadata: New metadata
        
    Returns:
        Dict with success status and update details
    """
```

##### delete_content(content_id, user_id, reason)
```python
def delete_content(self, content_id: int, user_id: int, reason: str = None) -> Dict[str, Any]:
    """
    Deletes content (soft delete).
    
    Args:
        content_id: ID of the content to delete
        user_id: ID of the user deleting
        reason: Reason for deletion
        
    Returns:
        Dict with success status and message
    """
```

##### archive_content(content_id, user_id, reason, retention_days)
```python
def archive_content(self, content_id: int, user_id: int, reason: str = 'manual',
                   retention_days: int = 365) -> Dict[str, Any]:
    """
    Archives content.
    
    Args:
        content_id: ID of the content to archive
        user_id: ID of the user archiving
        reason: Reason for archiving
        retention_days: Number of days to retain
        
    Returns:
        Dict with success status and archive details
    """
```

##### get_content(content_id, user_id)
```python
def get_content(self, content_id: int, user_id: int = None) -> Dict[str, Any]:
    """
    Gets content with full details.
    
    Args:
        content_id: ID of the content
        user_id: ID of the requesting user
        
    Returns:
        Dict with success status and content data
    """
```

##### get_content_list(user_id, content_type, status, visibility, sort_by, order, limit, offset, featured_only)
```python
def get_content_list(self, user_id: int = None, content_type: str = None, status: str = 'published',
                    visibility: str = None, sort_by: str = 'created_at', order: str = 'desc',
                    limit: int = 20, offset: int = 0, featured_only: bool = False) -> Dict[str, Any]:
    """
    Gets content list with filtering and sorting.
    
    Args:
        user_id: ID of the requesting user
        content_type: Filter by content type
        status: Filter by status
        visibility: Filter by visibility
        sort_by: Sort field
        order: Sort order
        limit: Maximum number of results
        offset: Offset for pagination
        featured_only: Only featured content
        
    Returns:
        Dict with success status and content list
    """
```

### ContentAnalyticsService

**Purpose:** Service for content analytics and insights.

#### Key Methods

##### track_content_view(content_id, user_id, view_data)
```python
def track_content_view(self, content_id: int, user_id: int = None, view_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Tracks content view.
    
    Args:
        content_id: ID of the content viewed
        user_id: ID of the user viewing
        view_data: Additional view data
        
    Returns:
        Dict with success status and message
    """
```

##### track_content_engagement(content_id, engagement_type, user_id, engagement_data)
```python
def track_content_engagement(self, content_id: int, engagement_type: str, user_id: int = None,
                            engagement_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Tracks content engagement.
    
    Args:
        content_id: ID of the content
        engagement_type: Type of engagement (like, comment, share, bookmark)
        user_id: ID of the user
        engagement_data: Additional engagement data
        
    Returns:
        Dict with success status and message
    """
```

##### get_content_analytics(content_id, days)
```python
def get_content_analytics(self, content_id: int, days: int = 30) -> Dict[str, Any]:
    """
    Gets comprehensive analytics for content.
    
    Args:
        content_id: ID of the content
        days: Number of days to analyze
        
    Returns:
        Dict with success status and analytics data
    """
```

##### get_trending_content(content_type, limit, hours)
```python
def get_trending_content(self, content_type: str = None, limit: int = 20, hours: int = 24) -> List[Dict[str, Any]]:
    """
    Gets trending content.
    
    Args:
        content_type: Filter by content type
        limit: Maximum number of results
        hours: Number of hours to consider
        
    Returns:
        List of trending content dictionaries
    """
```

##### update_trending_scores()
```python
def update_trending_scores(self) -> int:
    """
    Updates trending scores for all content.
    
    Returns:
        Number of content items updated
    """
```

### ContentModerationService

**Purpose:** Service for content moderation and review.

#### Key Methods

##### flag_content(content_id, reporter_id, reason, severity)
```python
def flag_content(self, content_id: int, reporter_id: int, reason: str, severity: int = 3) -> Dict[str, Any]:
    """
    Flags content for moderation review.
    
    Args:
        content_id: ID of the content to flag
        reporter_id: ID of the reporter
        reason: Reason for flagging
        severity: Severity level (1-5)
        
    Returns:
        Dict with success status and moderation data
    """
```

##### review_content(content_id, reviewer_id, action, reason, notes)
```python
def review_content(self, content_id: int, reviewer_id: int, action: str, reason: str = None,
                  notes: str = None) -> Dict[str, Any]:
    """
    Reviews flagged content.
    
    Args:
        content_id: ID of the content to review
        reviewer_id: ID of the reviewer
        action: Review action (approve, reject, edit, delete, flag)
        reason: Reason for action
        notes: Review notes
        
    Returns:
        Dict with success status and action details
    """
```

##### get_pending_moderation(reviewer_id, limit)
```python
def get_pending_moderation(self, reviewer_id: int = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Gets pending moderation items.
    
    Args:
        reviewer_id: ID of the reviewer
        limit: Maximum number of items
        
    Returns:
        List of pending moderation items
    """
```

##### auto_moderate_content(content_id)
```python
def auto_moderate_content(self, content_id: int) -> Dict[str, Any]:
    """
    Automatically moderates content using AI/ML.
    
    Args:
        content_id: ID of the content to moderate
        
    Returns:
        Dict with success status and moderation results
    """
```

### ContentRecommendationService

**Purpose:** Service for content recommendations and personalization.

#### Key Methods

##### get_user_recommendations(user_id, content_type, limit)
```python
def get_user_recommendations(self, user_id: int, content_type: str = None, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Gets personalized content recommendations for user.
    
    Args:
        user_id: ID of the user
        content_type: Filter by content type
        limit: Maximum number of recommendations
        
    Returns:
        List of recommendation dictionaries
    """
```

##### get_similar_content(content_id, limit)
```python
def get_similar_content(self, content_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Gets content similar to specified content.
    
    Args:
        content_id: ID of the reference content
        limit: Maximum number of results
        
    Returns:
        List of similar content dictionaries
    """
```

##### get_trending_recommendations(content_type, limit)
```python
def get_trending_recommendations(self, content_type: str = None, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Gets trending content recommendations.
    
    Args:
        content_type: Filter by content type
        limit: Maximum number of recommendations
        
    Returns:
        List of trending content recommendations
    """
```

##### record_recommendation_interaction(user_id, content_id, interaction_type)
```python
def record_recommendation_interaction(self, user_id: int, content_id: int, interaction_type: str) -> Dict[str, Any]:
    """
    Records user interaction with recommendation.
    
    Args:
        user_id: ID of the user
        content_id: ID of the content
        interaction_type: Type of interaction (click, view, dismiss, feedback)
        
    Returns:
        Dict with success status and message
    """
```

---

## Configuration

### Content Types Configuration

```python
CONTENT_TYPES = {
    'post': {
        'name': 'Post',
        'max_length': 5000,
        'requires_moderation': False,
        'allow_comments': True,
        'allow_sharing': True,
        'default_visibility': 'public'
    },
    'article': {
        'name': 'Article',
        'max_length': 10000,
        'requires_moderation': True,
        'allow_comments': True,
        'allow_sharing': True,
        'default_visibility': 'public'
    },
    'tutorial': {
        'name': 'Tutorial',
        'max_length': 20000,
        'requires_moderation': True,
        'allow_comments': True,
        'allow_sharing': True,
        'default_visibility': 'public'
    }
}
```

### Moderation Configuration

```python
MODERATION_CATEGORIES = {
    'spam': {
        'name': 'Spam',
        'severity': 2,
        'auto_reject': True
    },
    'inappropriate': {
        'name': 'Inappropriate Content',
        'severity': 3,
        'auto_reject': False
    },
    'offensive': {
        'name': 'Offensive Content',
        'severity': 4,
        'auto_reject': True
    },
    'hate': {
        'name': 'Hate Speech',
        'severity': 5,
        'auto_reject': True
    }
}
```

### Analytics Configuration

```python
ENGAGEMENT_WEIGHTS = {
    'like': 1.0,
    'comment': 2.0,
    'share': 3.0,
    'bookmark': 1.5,
    'download': 2.5,
    'view': 0.1
}

QUALITY_WEIGHTS = {
    'content_length': 0.2,
    'title_quality': 0.15,
    'summary_quality': 0.1,
    'metadata_completeness': 0.1,
    'tag_relevance': 0.15,
    'category_appropriateness': 0.1,
    'readability': 0.1,
    'originality': 0.1
}
```

---

## API Reference

### Content Management API

#### Create Content
```http
POST /api/content
Content-Type: application/json
Authorization: Bearer <token>

{
    "title": "My New Post",
    "content": "This is the content of my post...",
    "content_type": "post",
    "visibility": "public",
    "summary": "A brief summary",
    "tags": ["tag1", "tag2"],
    "categories": [1, 2],
    "metadata": {"key": "value"}
}
```

#### Update Content
```http
PUT /api/content/{content_id}
Content-Type: application/json
Authorization: Bearer <token>

{
    "title": "Updated Title",
    "content": "Updated content...",
    "change_summary": "Updated title and content"
}
```

#### Delete Content
```http
DELETE /api/content/{content_id}
Authorization: Bearer <token>

{
    "reason": "No longer needed"
}
```

#### Get Content
```http
GET /api/content/{content_id}
Authorization: Bearer <token>
```

#### Get Content List
```http
GET /api/content?type=post&status=published&sort=created_at&order=desc&limit=20&offset=0
Authorization: Bearer <token>
```

### Content Analytics API

#### Track View
```http
POST /api/content/{content_id}/view
Content-Type: application/json
Authorization: Bearer <token>

{
    "duration": 45.5,
    "device": "mobile",
    "country": "US"
}
```

#### Track Engagement
```http
POST /api/content/{content_id}/engage
Content-Type: application/json
Authorization: Bearer <token>

{
    "type": "like",
    "metadata": {"source": "feed"}
}
```

#### Get Analytics
```http
GET /api/content/{content_id}/analytics?days=30
Authorization: Bearer <token>
```

#### Get Trending Content
```http
GET /api/content/trending?type=post&hours=24&limit=20
Authorization: Bearer <token>
```

### Content Moderation API

#### Flag Content
```http
POST /api/content/{content_id}/flag
Content-Type: application/json
Authorization: Bearer <token>

{
    "reason": "Inappropriate content",
    "severity": 3
}
```

#### Review Content
```http
POST /api/content/{content_id}/review
Content-Type: application/json
Authorization: Bearer <token>

{
    "action": "approve",
    "reason": "Content is appropriate",
    "notes": "Reviewed and approved"
}
```

#### Get Pending Moderation
```http
GET /api/content/moderation/pending?limit=50
Authorization: Bearer <token>
```

### Content Recommendations API

#### Get Recommendations
```http
GET /api/content/recommendations?type=post&limit=20
Authorization: Bearer <token>
```

#### Get Similar Content
```http
GET /api/content/{content_id}/similar?limit=10
Authorization: Bearer <token>
```

#### Record Interaction
```http
POST /api/content/recommendations/{content_id}/interact
Content-Type: application/json
Authorization: Bearer <token>

{
    "type": "click",
    "feedback": 0.8
}
```

---

## Usage Examples

### Basic Content Management

```python
from app.content.service import ContentService

# Initialize service
content_service = ContentService()

# Create content
result = content_service.create_content(
    user_id=current_user_id,
    title="My First Post",
    content="This is the content of my first post...",
    content_type="post",
    visibility="public",
    summary="A brief summary of my post",
    tags=["introduction", "welcome"],
    categories=[1, 2],
    metadata={"mood": "excited"}
)

if result['success']:
    content_id = result['content_id']
    print(f"Created content with ID: {content_id}")
    
    # Update content
    update_result = content_service.update_content(
        content_id=content_id,
        user_id=current_user_id,
        title="Updated Post Title",
        content="Updated content...",
        change_summary="Updated title and content"
    )
    
    if update_result['success']:
        print("Content updated successfully")
```

### Content Analytics

```python
from app.content.service import ContentAnalyticsService

# Initialize service
analytics_service = ContentAnalyticsService()

# Track content view
view_result = analytics_service.track_content_view(
    content_id=content_id,
    user_id=current_user_id,
    view_data={
        "duration": 45.5,
        "device": "mobile",
        "country": "US"
    }
)

# Track engagement
engagement_result = analytics_service.track_content_engagement(
    content_id=content_id,
    engagement_type="like",
    user_id=current_user_id,
    engagement_data={"source": "feed"}
)

# Get content analytics
analytics_data = analytics_service.get_content_analytics(content_id, days=30)
print(f"Total views: {analytics_data['analytics']['basic_metrics']['total_views']}")
print(f"Engagement rate: {analytics_data['analytics']['basic_metrics']['engagement_rate']}")
```

### Content Moderation

```python
from app.content.service import ContentModerationService

# Initialize service
moderation_service = ContentModerationService()

# Flag content
flag_result = moderation_service.flag_content(
    content_id=content_id,
    reporter_id=current_user_id,
    reason="Inappropriate content",
    severity=3
)

# Review content (for moderators)
review_result = moderation_service.review_content(
    content_id=content_id,
    reviewer_id=moderator_id,
    action="approve",
    reason="Content is appropriate",
    notes="Reviewed and approved"
)

# Get pending moderation
pending_items = moderation_service.get_pending_moderation(
    reviewer_id=moderator_id,
    limit=50
)
```

### Content Recommendations

```python
from app.content.service import ContentRecommendationService

# Initialize service
recommendation_service = ContentRecommendationService()

# Get user recommendations
recommendations = recommendation_service.get_user_recommendations(
    user_id=current_user_id,
    content_type="post",
    limit=20
)

print(f"Found {len(recommendations)} recommendations")
for rec in recommendations:
    print(f"- {rec['title']} (Score: {rec['recommendation_score']})")

# Get similar content
similar_content = recommendation_service.get_similar_content(
    content_id=content_id,
    limit=10
)

# Record interaction
interaction_result = recommendation_service.record_recommendation_interaction(
    user_id=current_user_id,
    content_id=content_id,
    interaction_type="click"
)
```

---

## Performance Considerations

### Database Optimization
- **Indexes**: All frequently queried fields properly indexed
- **Partitioning**: Large tables partitioned by date
- **Query Optimization**: Efficient queries with proper joins

### Caching Strategy
- **Redis Caching**: Frequently accessed content cached
- **CDN Integration**: Static content served via CDN
- **Cache Invalidation**: Smart cache invalidation on content changes

### Scalability
- **Horizontal Scaling**: Services designed for horizontal scaling
- **Load Balancing**: Load balancing ready for high traffic
- **Microservices**: Modular design allows independent scaling

---

## Security Considerations

### Content Security
- **Input Validation**: All content validated and sanitized
- **XSS Protection**: Output properly escaped
- **CSRF Protection**: CSRF tokens for forms

### Access Control
- **Role-Based Access**: Different permissions for different roles
- **Content Ownership**: Users can only edit their own content
- **Moderation Access**: Limited access to moderation tools

### Data Privacy
- **Privacy Settings**: User-controlled privacy levels
- **Data Encryption**: Sensitive data encrypted at rest
- **Audit Trails**: Complete audit trail for content changes

---

## Monitoring and Analytics

### Performance Metrics
- **Content Performance**: Track content creation and engagement
- **User Engagement**: Monitor user interaction patterns
- **System Performance**: Track system response times

### Business Analytics
- **Content Growth**: Monitor content creation trends
- **Engagement Trends**: Track engagement over time
- **Quality Metrics**: Monitor content quality scores

### Error Tracking
- **Error Logging**: Comprehensive error logging
- **Performance Monitoring**: Real-time performance monitoring
- **Alert System**: Automated alerts for issues

---

## Troubleshooting

### Common Issues

#### Content Creation Fails
- **Cause**: Missing required fields or validation errors
- **Solution**: Check all required fields and validation rules
- **Code**: `content_service.validate_content_data(data)`

#### Analytics Not Updating
- **Cause**: Analytics service not properly configured
- **Solution**: Check analytics configuration and service status
- **Code**: `analytics_service.check_service_health()`

#### Moderation Not Working
- **Cause**: Moderation rules not properly configured
- **Solution**: Check moderation configuration and rules
- **Code**: `moderation_service.validate_configuration()`

### Debugging Tools

#### Content Debug Mode
```python
# Enable debug mode
content_config.DEBUG_MODE = True

# Get debug information
debug_info = content_service.get_debug_info(content_id)
```

#### Performance Profiling
```python
# Profile content operations
with content_service.profile_operation('create_content'):
    result = content_service.create_content(...)
```

---

## Future Enhancements

### Planned Features
- **AI-Powered Content**: AI-generated content suggestions
- **Advanced Analytics**: Machine learning-powered insights
- **Content Marketplace**: Content buying and selling
- **Collaborative Editing**: Real-time collaborative content editing

### Scalability Improvements
- **Event Sourcing**: Event-driven architecture for content events
- **Microservices**: Split into smaller, focused services
- **Graph Database**: Consider Neo4j for complex content relationships

### API Enhancements
- **GraphQL API**: GraphQL endpoint for complex queries
- **WebSocket Events**: Real-time content event notifications
- **Bulk Operations**: Bulk content operations for admin tasks

---

## Support and Maintenance

### Documentation Updates
- Regular documentation updates with new features
- API documentation kept in sync with implementation
- Troubleshooting guide updated with common issues

### Maintenance Tasks
- Regular performance monitoring and optimization
- Security audits and updates
- Database maintenance and optimization

### Support Channels
- Technical support via GitHub issues
- Community support via forum
- Documentation and guides available

---

**Document Version:** 1.0.0  
**Last Updated:** May 13, 2026  
**Next Review:** June 13, 2026

For questions or support, please refer to the troubleshooting section or create an issue in the project repository.
