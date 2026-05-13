"""
Automated Content Moderation Models

This module contains SQLAlchemy models for the content moderation system,
including moderation queue, content analysis, spam detection, quality scoring,
and moderation history tracking.
"""

from datetime import datetime, timezone
from flask import current_app
from app import db
from app.models import User
import json


class ModerationQueue(db.Model):
    """Model for content moderation queue"""
    
    __tablename__ = 'moderation_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Content information
    content_type = db.Column(db.String(50), nullable=False)  # post, comment, user_profile
    content_id = db.Column(db.Integer, nullable=False)
    content_data = db.Column(db.JSON)  # Original content data
    
    # Analysis information
    spam_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    quality_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    toxicity_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    
    # Moderation status
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, flagged
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    # Automated analysis results
    analysis_results = db.Column(db.JSON)  # Detailed analysis results
    detected_issues = db.Column(db.JSON)  # List of detected issues
    
    # Review information
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    review_notes = db.Column(db.Text)
    review_confidence = db.Column(db.Float)  # 0.0-1.0
    
    # Automated actions
    auto_action_taken = db.Column(db.String(50))  # Type of automated action taken
    auto_action_confidence = db.Column(db.Float)  # Confidence in automated action
    auto_action_reason = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime)
    auto_action_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    reviewer = db.relationship('User', backref='moderation_reviews', foreign_keys=[reviewer_id])
    
    # Indexes
    __table_args__ = (
        db.Index('idx_queue_content', 'content_type', 'content_id'),
        db.Index('idx_queue_status', 'status'),
        db.Index('idx_queue_priority', 'priority'),
        db.Index('idx_queue_created', 'created_at'),
        db.Index('idx_queue_spam_score', 'spam_score'),
        db.Index('idx_queue_quality_score', 'quality_score'),
    )
    
    def to_dict(self):
        """Convert moderation queue item to dictionary"""
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'content_data': self.content_data or {},
            'spam_score': self.spam_score,
            'quality_score': self.quality_score,
            'toxicity_score': self.toxicity_score,
            'status': self.status,
            'priority': self.priority,
            'analysis_results': self.analysis_results or {},
            'detected_issues': self.detected_issues or [],
            'reviewer_id': self.reviewer_id,
            'review_notes': self.review_notes,
            'review_confidence': self.review_confidence,
            'auto_action_taken': self.auto_action_taken,
            'auto_action_confidence': self.auto_action_confidence,
            'auto_action_reason': self.auto_action_reason,
            'created_at': self.created_at.isoformat(),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'auto_action_at': self.auto_action_at.isoformat() if self.auto_action_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    def __repr__(self):
        return f'<ModerationQueue {self.id}: {self.content_type} {self.content_id}>'


class ContentAnalysis(db.Model):
    """Model for content analysis results"""
    
    __tablename__ = 'content_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Content information
    content_type = db.Column(db.String(50), nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)  # For change detection
    
    # Analysis metrics
    word_count = db.Column(db.Integer, default=0)
    character_count = db.Column(db.Integer, default=0)
    sentence_count = db.Column(db.Integer, default=0)
    paragraph_count = db.Column(db.Integer, default=0)
    
    # Content characteristics
    avg_word_length = db.Column(db.Float, default=0.0)
    avg_sentence_length = db.Column(db.Float, default=0.0)
    readability_score = db.Column(db.Float, default=0.0)  # Flesch-Kincaid
    
    # Language analysis
    language_detected = db.Column(db.String(10))
    language_confidence = db.Column(db.Float, default=0.0)
    
    # Sentiment analysis
    sentiment_score = db.Column(db.Float, default=0.0)  # -1.0 to 1.0
    sentiment_label = db.Column(db.String(20))  # positive, negative, neutral
    
    # Topic analysis
    primary_topic = db.Column(db.String(100))
    topic_confidence = db.Column(db.Float, default=0.0)
    topics = db.Column(db.JSON)  # List of topics with confidence scores
    
    # Keyword analysis
    keywords = db.Column(db.JSON)  # Important keywords with scores
    entities = db.Column(db.JSON)  # Named entities detected
    
    # Quality indicators
    grammar_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    spelling_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    coherence_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    
    # Analysis metadata
    analysis_version = db.Column(db.String(20), default='1.0')
    analysis_time = db.Column(db.Float)  # Time taken for analysis in seconds
    confidence_score = db.Column(db.Float, default=0.0)  # Overall confidence
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_analysis_content', 'content_type', 'content_id'),
        db.Index('idx_analysis_hash', 'content_hash'),
        db.Index('idx_analysis_language', 'language_detected'),
        db.Index('idx_analysis_sentiment', 'sentiment_score'),
        db.Index('idx_analysis_quality', 'grammar_score', 'spelling_score'),
    )
    
    def to_dict(self):
        """Convert content analysis to dictionary"""
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'content_hash': self.content_hash,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'sentence_count': self.sentence_count,
            'paragraph_count': self.paragraph_count,
            'avg_word_length': self.avg_word_length,
            'avg_sentence_length': self.avg_sentence_length,
            'readability_score': self.readability_score,
            'language_detected': self.language_detected,
            'language_confidence': self.language_confidence,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'primary_topic': self.primary_topic,
            'topic_confidence': self.topic_confidence,
            'topics': self.topics or [],
            'keywords': self.keywords or [],
            'entities': self.entities or [],
            'grammar_score': self.grammar_score,
            'spelling_score': self.spelling_score,
            'coherence_score': self.coherence_score,
            'analysis_version': self.analysis_version,
            'analysis_time': self.analysis_time,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ContentAnalysis {self.id}: {self.content_type} {self.content_id}>'


class ModerationAction(db.Model):
    """Model for moderation actions taken"""
    
    __tablename__ = 'moderation_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Action information
    action_type = db.Column(db.String(50), nullable=False)  # approve, reject, delete, warn, suspend
    action_reason = db.Column(db.String(100), nullable=False)
    action_description = db.Column(db.Text)
    
    # Target information
    target_type = db.Column(db.String(50), nullable=False)  # post, comment, user
    target_id = db.Column(db.Integer, nullable=False)
    
    # Actor information
    actor_type = db.Column(db.String(20), default='moderator')  # moderator, admin, system
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Action details
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    confidence = db.Column(db.Float, default=0.0)  # 0.0-1.0
    automated = db.Column(db.Boolean, default=False)
    
    # Action data
    action_data = db.Column(db.JSON)  # Additional action data
    previous_state = db.Column(db.JSON)  # State before action
    new_state = db.Column(db.JSON)  # State after action
    
    # Appeal information
    appealable = db.Column(db.Boolean, default=False)
    appeal_deadline = db.Column(db.DateTime)
    appeal_reason = db.Column(db.Text)
    appeal_status = db.Column(db.String(20), default='none')  # none, pending, approved, rejected
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime)
    appealed_at = db.Column(db.DateTime)
    
    # Relationships
    actor = db.relationship('User', backref='moderation_actions', foreign_keys=[actor_id])
    
    # Indexes
    __table_args__ = (
        db.Index('idx_action_target', 'target_type', 'target_id'),
        db.Index('idx_action_actor', 'actor_type', 'actor_id'),
        db.Index('idx_action_type', 'action_type'),
        db.Index('idx_action_created', 'created_at'),
        db.Index('idx_action_automated', 'automated'),
    )
    
    def to_dict(self):
        """Convert moderation action to dictionary"""
        return {
            'id': self.id,
            'action_type': self.action_type,
            'action_reason': self.action_reason,
            'action_description': self.action_description,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'actor_type': self.actor_type,
            'actor_id': self.actor_id,
            'severity': self.severity,
            'confidence': self.confidence,
            'automated': self.automated,
            'action_data': self.action_data or {},
            'previous_state': self.previous_state or {},
            'new_state': self.new_state or {},
            'appealable': self.appealable,
            'appeal_deadline': self.appeal_deadline.isoformat() if self.appeal_deadline else None,
            'appeal_reason': self.appeal_reason,
            'appeal_status': self.appeal_status,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'appealed_at': self.appealed_at.isoformat() if self.appealed_at else None
        }
    
    def __repr__(self):
        return f'<ModerationAction {self.id}: {self.action_type} on {self.target_type} {self.target_id}>'


class ModerationRule(db.Model):
    """Model for moderation rules"""
    
    __tablename__ = 'moderation_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Rule information
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Rule configuration
    rule_type = db.Column(db.String(50), nullable=False)  # keyword, pattern, spam, quality, toxicity
    content_types = db.Column(db.JSON)  # Types of content this applies to
    
    # Rule conditions
    conditions = db.Column(db.JSON)  # Rule conditions and thresholds
    patterns = db.Column(db.JSON)  # Patterns to match
    
    # Action configuration
    action_type = db.Column(db.String(50), nullable=False)  # approve, reject, delete, warn, flag
    action_parameters = db.Column(db.JSON)  # Parameters for the action
    
    # Rule behavior
    priority = db.Column(db.Integer, default=5)  # 1-10, higher = more priority
    confidence_threshold = db.Column(db.Float, default=0.7)  # Minimum confidence to act
    auto_apply = db.Column(db.Boolean, default=False)  # Whether to apply automatically
    
    # Rule statistics
    total_matches = db.Column(db.Integer, default=0)
    total_actions = db.Column(db.Integer, default=0)
    false_positives = db.Column(db.Integer, default=0)
    last_triggered = db.Column(db.DateTime)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship('User', backref='created_rules')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_rule_type', 'rule_type'),
        db.Index('idx_rule_priority', 'priority'),
        db.Index('idx_rule_active', 'is_active'),
        db.Index('idx_rule_last_triggered', 'last_triggered'),
    )
    
    def to_dict(self):
        """Convert moderation rule to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rule_type': self.rule_type,
            'content_types': self.content_types or [],
            'conditions': self.conditions or {},
            'patterns': self.patterns or {},
            'action_type': self.action_type,
            'action_parameters': self.action_parameters or {},
            'priority': self.priority,
            'confidence_threshold': self.confidence_threshold,
            'auto_apply': self.auto_apply,
            'total_matches': self.total_matches,
            'total_actions': self.total_actions,
            'false_positives': self.false_positives,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by
        }
    
    def __repr__(self):
        return f'<ModerationRule {self.name}>'


class SpamDetection(db.Model):
    """Model for spam detection results"""
    
    __tablename__ = 'spam_detections'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Content information
    content_type = db.Column(db.String(50), nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)
    
    # Spam scores
    overall_score = db.Column(db.Float, nullable=False)  # 0.0-1.0
    keyword_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    pattern_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    behavior_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    metadata_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    
    # Detection details
    is_spam = db.Column(db.Boolean, nullable=False)
    confidence = db.Column(db.Float, nullable=False)  # 0.0-1.0
    spam_type = db.Column(db.String(50))  # promotional, scam, phishing, etc.
    
    # Analysis results
    detected_keywords = db.Column(db.JSON)  # Spam keywords found
    detected_patterns = db.Column(db.JSON)  # Spam patterns matched
    suspicious_metadata = db.Column(db.JSON)  # Suspicious metadata
    
    # User behavior analysis
    user_behavior_score = db.Column(db.Float, default=0.0)
    posting_frequency = db.Column(db.Float, default=0.0)
    account_age_risk = db.Column(db.Float, default=0.0)
    
    # Detection metadata
    detection_version = db.Column(db.String(20), default='1.0')
    detection_time = db.Column(db.Float)  # Time taken for detection
    false_positive_reported = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_spam_content', 'content_type', 'content_id'),
        db.Index('idx_spam_hash', 'content_hash'),
        db.Index('idx_spam_score', 'overall_score'),
        db.Index('idx_spam_is_spam', 'is_spam'),
        db.Index('idx_spam_created', 'created_at'),
    )
    
    def to_dict(self):
        """Convert spam detection to dictionary"""
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'content_hash': self.content_hash,
            'overall_score': self.overall_score,
            'keyword_score': self.keyword_score,
            'pattern_score': self.pattern_score,
            'behavior_score': self.behavior_score,
            'metadata_score': self.metadata_score,
            'is_spam': self.is_spam,
            'confidence': self.confidence,
            'spam_type': self.spam_type,
            'detected_keywords': self.detected_keywords or [],
            'detected_patterns': self.detected_patterns or [],
            'suspicious_metadata': self.suspicious_metadata or {},
            'user_behavior_score': self.user_behavior_score,
            'posting_frequency': self.posting_frequency,
            'account_age_risk': self.account_age_risk,
            'detection_version': self.detection_version,
            'detection_time': self.detection_time,
            'false_positive_reported': self.false_positive_reported,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<SpamDetection {self.id}: {self.content_type} {self.content_id}>'


class ContentQuality(db.Model):
    """Model for content quality assessment"""
    
    __tablename__ = 'content_quality'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Content information
    content_type = db.Column(db.String(50), nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)
    
    # Quality scores
    overall_score = db.Column(db.Float, nullable=False)  # 0.0-1.0
    content_quality = db.Column(db.Float, default=0.0)  # 0.0-1.0
    presentation_quality = db.Column(db.Float, default=0.0)  # 0.0-1.0
    originality_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    engagement_potential = db.Column(db.Float, default=0.0)  # 0.0-1.0
    
    # Quality factors
    grammar_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    spelling_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    structure_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    coherence_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    relevance_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    
    # Content characteristics
    word_count = db.Column(db.Integer, default=0)
    readability_score = db.Column(db.Float, default=0.0)  # Flesch-Kincaid
    complexity_score = db.Column(db.Float, default=0.0)  # Content complexity
    
    # Quality assessment
    quality_grade = db.Column(db.String(10))  # A, B, C, D, F
    improvement_suggestions = db.Column(db.JSON)  # Suggestions for improvement
    best_practices_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    
    # Assessment metadata
    assessment_version = db.Column(db.String(20), default='1.0')
    assessment_time = db.Column(db.Float)  # Time taken for assessment
    confidence = db.Column(db.Float, nullable=False)  # 0.0-1.0
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_quality_content', 'content_type', 'content_id'),
        db.Index('idx_quality_hash', 'content_hash'),
        db.Index('idx_quality_score', 'overall_score'),
        db.Index('idx_quality_grade', 'quality_grade'),
        db.Index('idx_quality_created', 'created_at'),
    )
    
    def to_dict(self):
        """Convert content quality to dictionary"""
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'content_hash': self.content_hash,
            'overall_score': self.overall_score,
            'content_quality': self.content_quality,
            'presentation_quality': self.presentation_quality,
            'originality_score': self.originality_score,
            'engagement_potential': self.engagement_potential,
            'grammar_score': self.grammar_score,
            'spelling_score': self.spelling_score,
            'structure_score': self.structure_score,
            'coherence_score': self.coherence_score,
            'relevance_score': self.relevance_score,
            'word_count': self.word_count,
            'readability_score': self.readability_score,
            'complexity_score': self.complexity_score,
            'quality_grade': self.quality_grade,
            'improvement_suggestions': self.improvement_suggestions or [],
            'best_practices_score': self.best_practices_score,
            'assessment_version': self.assessment_version,
            'assessment_time': self.assessment_time,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ContentQuality {self.id}: {self.content_type} {self.content_id}>'


class ModerationPattern(db.Model):
    """Model for moderation patterns"""
    
    __tablename__ = 'moderation_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Pattern information
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Pattern configuration
    pattern_type = db.Column(db.String(50), nullable=False)  # regex, keyword, behavioral, metadata
    pattern_data = db.Column(db.JSON)  # Pattern definition
    
    # Pattern behavior
    match_type = db.Column(db.String(20), default='any')  # any, all, exact
    case_sensitive = db.Column(db.Boolean, default=False)
    weight = db.Column(db.Float, default=1.0)  # Pattern weight in scoring
    
    # Category and severity
    category = db.Column(db.String(50), nullable=False)  # spam, toxicity, quality, security
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    # Statistics
    total_matches = db.Column(db.Integer, default=0)
    true_positives = db.Column(db.Integer, default=0)
    false_positives = db.Column(db.Integer, default=0)
    accuracy_rate = db.Column(db.Float, default=0.0)  # 0.0-1.0
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship('User', backref='created_patterns')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_pattern_type', 'pattern_type'),
        db.Index('idx_pattern_category', 'category'),
        db.Index('idx_pattern_severity', 'severity'),
        db.Index('idx_pattern_active', 'is_active'),
        db.Index('idx_pattern_accuracy', 'accuracy_rate'),
    )
    
    def to_dict(self):
        """Convert moderation pattern to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'pattern_type': self.pattern_type,
            'pattern_data': self.pattern_data or {},
            'match_type': self.match_type,
            'case_sensitive': self.case_sensitive,
            'weight': self.weight,
            'category': self.category,
            'severity': self.severity,
            'total_matches': self.total_matches,
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'accuracy_rate': self.accuracy_rate,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by
        }
    
    def __repr__(self):
        return f'<ModerationPattern {self.name}>'


class ModerationHistory(db.Model):
    """Model for moderation history tracking"""
    
    __tablename__ = 'moderation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Event information
    event_type = db.Column(db.String(50), nullable=False)  # analysis, action, appeal, review
    event_description = db.Column(db.Text)
    
    # Target information
    target_type = db.Column(db.String(50), nullable=False)  # post, comment, user
    target_id = db.Column(db.Integer, nullable=False)
    
    # Actor information
    actor_type = db.Column(db.String(20), nullable=False)  # moderator, admin, system, user
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Event data
    event_data = db.Column(db.JSON)  # Detailed event data
    previous_state = db.Column(db.JSON)  # State before event
    new_state = db.Column(db.JSON)  # State after event
    
    # Event metadata
    automated = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float, default=0.0)  # 0.0-1.0
    processing_time = db.Column(db.Float)  # Time taken for processing
    
    # Related entities
    related_action_id = db.Column(db.Integer, db.ForeignKey('moderation_actions.id'))
    related_queue_id = db.Column(db.Integer, db.ForeignKey('moderation_queue.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    actor = db.relationship('User', backref='moderation_history', foreign_keys=[actor_id])
    related_action = db.relationship('ModerationAction', backref='history_entries')
    related_queue = db.relationship('ModerationQueue', backref='history_entries')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_history_target', 'target_type', 'target_id'),
        db.Index('idx_history_actor', 'actor_type', 'actor_id'),
        db.Index('idx_history_event', 'event_type'),
        db.Index('idx_history_created', 'created_at'),
        db.Index('idx_history_automated', 'automated'),
    )
    
    def to_dict(self):
        """Convert moderation history to dictionary"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'event_description': self.event_description,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'actor_type': self.actor_type,
            'actor_id': self.actor_id,
            'event_data': self.event_data or {},
            'previous_state': self.previous_state or {},
            'new_state': self.new_state or {},
            'automated': self.automated,
            'confidence': self.confidence,
            'processing_time': self.processing_time,
            'related_action_id': self.related_action_id,
            'related_queue_id': self.related_queue_id,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ModerationHistory {self.id}: {self.event_type} on {self.target_type} {self.target_id}>'
