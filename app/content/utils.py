"""
Content Relationships Utilities
Auto Bot Solutions Forum

This module provides utility functions for content relationships,
including validation, calculations, and helper functions.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy import and_, or_, func, desc
from app.models import User
from .models import (
    ContentRelationship, ContentVersion, ContentAnalytics, ContentModeration,
    ContentArchive, ContentRecommendation, ContentTag, ContentCategory
)


class ContentValidators:
    """Validation utilities for content relationships"""
    
    @staticmethod
    def validate_content_type(content_type: str) -> bool:
        """Validate content type"""
        valid_types = ['post', 'comment', 'article', 'page', 'story', 'tutorial', 'news', 'blog']
        return content_type in valid_types
    
    @staticmethod
    def validate_content_status(status: str) -> bool:
        """Validate content status"""
        valid_statuses = ['draft', 'published', 'archived', 'deleted']
        return status in valid_statuses
    
    @staticmethod
    def validate_visibility(visibility: str) -> bool:
        """Validate content visibility"""
        valid_visibility = ['public', 'private', 'friends', 'unlisted']
        return visibility in valid_statuses
    
    @staticmethod
    def validate_moderation_status(status: str) -> bool:
        """Validate moderation status"""
        valid_statuses = ['pending', 'approved', 'rejected', 'flagged']
        return status in valid_statuses
    
    @staticmethod
    def validate_moderation_priority(priority: str) -> bool:
        """Validate moderation priority"""
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        return priority in valid_priorities
    
    @staticmethod
    def validate_content_length(content: str, min_length: int = 10, max_length: int = 50000) -> bool:
        """Validate content length"""
        return min_length <= len(content) <= max_length
    
    @staticmethod
    def validate_title(title: str, min_length: int = 3, max_length: int = 255) -> bool:
        """Validate title length"""
        return min_length <= len(title.strip()) <= max_length
    
    @staticmethod
    def validate_slug(slug: str) -> bool:
        """Validate slug format"""
        import re
        # Allow lowercase letters, numbers, hyphens, and underscores
        return bool(re.match(r'^[a-z0-9_-]+$', slug))
    
    @staticmethod
    def validate_severity(severity: int) -> bool:
        """Validate severity level"""
        return 1 <= severity <= 5


class ContentCalculators:
    """Calculation utilities for content relationships"""
    
    @staticmethod
    def calculate_engagement_score(content: ContentRelationship) -> float:
        """Calculate engagement score for content"""
        if content.view_count == 0:
            return 0.0
        
        total_engagement = (
            content.like_count * 1.0 +
            content.comment_count * 2.0 +
            content.share_count * 3.0 +
            content.bookmark_count * 1.5
        )
        
        engagement_rate = total_engagement / content.view_count
        
        # Normalize to 0.0-1.0 range
        return min(1.0, engagement_rate / 10.0)
    
    @staticmethod
    def calculate_quality_score(content: ContentRelationship) -> float:
        """Calculate quality score for content"""
        score = 0.0
        
        # Content length factor
        if content.content:
            length = len(content.content)
            if 100 <= length <= 2000:
                score += 0.3
            elif 2000 < length <= 5000:
                score += 0.2
            elif length > 5000:
                score += 0.1
        
        # Title presence factor
        if content.title and len(content.title.strip()) > 0:
            score += 0.2
        
        # Summary presence factor
        if content.summary and len(content.summary.strip()) > 0:
            score += 0.1
        
        # Metadata factor
        if content.metadata:
            score += 0.1
        
        # Tags factor
        if content.tags:
            score += min(0.2, len(content.tags) * 0.05)
        
        # Categories factor
        if content.categories:
            score += min(0.1, len(content.categories) * 0.05)
        
        return min(1.0, score)
    
    @staticmethod
    def calculate_trending_score(content: ContentRelationship, hours: int = 24) -> float:
        """Calculate trending score for content"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get recent analytics
        analytics = ContentAnalytics.query.filter_by(content_id=content.id).first()
        if not analytics:
            return 0.0
        
        # Calculate recent views and engagement
        recent_views = analytics.views_today if hours <= 24 else 0
        recent_engagement = analytics.total_engagements  # Simplified
        
        # Time decay factor
        days_since_creation = (datetime.now(timezone.utc) - content.created_at).days
        time_factor = max(0.1, 1.0 - (days_since_creation / 30))
        
        # Calculate trending score
        base_score = (recent_views * 0.6 + recent_engagement * 0.4) / 100.0
        trending_score = base_score * time_factor
        
        return min(1.0, trending_score)
    
    @staticmethod
    def calculate_readability_score(content: str) -> float:
        """Calculate readability score using simplified metrics"""
        if not content:
            return 0.0
        
        # Basic readability metrics
        words = content.split()
        sentences = content.split('.')
        
        if not words or not sentences:
            return 0.0
        
        # Average words per sentence
        avg_words_per_sentence = len(words) / len(sentences)
        
        # Average sentence length (ideal: 15-20 words)
        if 15 <= avg_words_per_sentence <= 20:
            sentence_score = 1.0
        elif 10 <= avg_words_per_sentence <= 25:
            sentence_score = 0.8
        else:
            sentence_score = 0.5
        
        # Average word length (ideal: 4-5 characters)
        avg_word_length = sum(len(word) for word in words) / len(words)
        if 4 <= avg_word_length <= 5:
            word_score = 1.0
        elif 3 <= avg_word_length <= 6:
            word_score = 0.8
        else:
            word_score = 0.6
        
        # Content length factor
        length = len(content)
        if 100 <= length <= 2000:
            length_score = 1.0
        elif 50 <= length <= 5000:
            length_score = 0.8
        else:
            length_score = 0.5
        
        # Calculate overall score
        readability_score = (sentence_score * 0.4 + word_score * 0.3 + length_score * 0.3)
        
        return readability_score
    
    @staticmethod
    def calculate_sentiment_score(content: str) -> float:
        """Calculate sentiment score (simplified)"""
        if not content:
            return 0.0
        
        # Simple sentiment analysis using word lists
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied', 'delighted',
            'beautiful', 'awesome', 'brilliant', 'outstanding', 'perfect'
        }
        
        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate',
            'dislike', 'angry', 'sad', 'disappointed', 'frustrated', 'annoyed',
            'ugly', 'stupid', 'ridiculous', 'pathetic', 'useless'
        }
        
        content_lower = content.lower()
        words = content_lower.split()
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_words = len(words)
        if total_words == 0:
            return 0.0
        
        # Calculate sentiment score (-1.0 to 1.0)
        sentiment_score = (positive_count - negative_count) / total_words
        
        return max(-1.0, min(1.0, sentiment_score))
    
    @staticmethod
    def calculate_content_similarity(content1: ContentRelationship, 
                                  content2: ContentRelationship) -> float:
        """Calculate similarity between two content items"""
        similarity = 0.0
        
        # Text similarity (simplified)
        if content1.content and content2.content:
            text1 = content1.content.lower()
            text2 = content2.content.lower()
            
            # Simple word overlap similarity
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            if words1 and words2:
                intersection = len(words1.intersection(words2))
                union = len(words1.union(words2))
                text_similarity = intersection / union if union > 0 else 0
                similarity += text_similarity * 0.4
        
        # Tag similarity
        tags1 = set(tag.name for tag in content1.tags)
        tags2 = set(tag.name for tag in content2.tags)
        
        if tags1 and tags2:
            intersection = len(tags1.intersection(tags2))
            union = len(tags1.union(tags2))
            tag_similarity = intersection / union if union > 0 else 0
            similarity += tag_similarity * 0.3
        
        # Category similarity
        categories1 = set(cat.id for cat in content1.categories)
        categories2 = set(cat.id for cat in content2.categories)
        
        if categories1 and categories2:
            intersection = len(categories1.intersection(categories2))
            union = len(categories1.union(categories2))
            category_similarity = intersection / union if union > 0 else 0
            similarity += category_similarity * 0.2
        
        # Content type similarity
        if content1.content_type == content2.content_type:
            similarity += 0.1
        
        return min(1.0, similarity)
    
    @staticmethod
    def calculate_reading_time(content: str, words_per_minute: int = 200) -> int:
        """Calculate estimated reading time in minutes"""
        if not content:
            return 0
        
        word_count = len(content.split())
        reading_time = max(1, word_count // words_per_minute)
        
        return reading_time
    
    @staticmethod
    def calculate_complexity_score(content: str) -> float:
        """Calculate content complexity score"""
        if not content:
            return 0.0
        
        # Complexity factors
        words = content.split()
        sentences = content.split('.')
        
        if not words or not sentences:
            return 0.0
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        
        # Long words (> 6 characters)
        long_words = sum(1 for word in words if len(word) > 6)
        long_word_ratio = long_words / len(words)
        
        # Punctuation density
        punctuation = sum(1 for char in content if char in '.!?;:,')
        punctuation_ratio = punctuation / len(content)
        
        # Calculate complexity score
        complexity_score = 0.0
        
        # Sentence length factor (higher = more complex)
        if avg_sentence_length > 20:
            complexity_score += 0.3
        elif avg_sentence_length > 15:
            complexity_score += 0.2
        
        # Long word factor
        if long_word_ratio > 0.2:
            complexity_score += 0.3
        elif long_word_ratio > 0.1:
            complexity_score += 0.2
        
        # Punctuation factor
        if punctuation_ratio > 0.05:
            complexity_score += 0.2
        elif punctuation_ratio > 0.03:
            complexity_score += 0.1
        
        # Content length factor
        if len(content) > 5000:
            complexity_score += 0.2
        elif len(content) > 2000:
            complexity_score += 0.1
        
        return min(1.0, complexity_score)


class ContentHelpers:
    """Helper functions for content relationships"""
    
    @staticmethod
    def generate_slug(title: str) -> str:
        """Generate URL-friendly slug from title"""
        import re
        import uuid
        
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        # Ensure uniqueness by adding UUID if needed
        existing = ContentRelationship.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{uuid.uuid4().hex[:8]}"
        
        return slug
    
    @staticmethod
    def extract_keywords(content: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from content"""
        if not content:
            return []
        
        # Simple keyword extraction
        words = content.lower().split()
        
        # Remove common stop words
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are',
            'was', 'were', 'be', 'have', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Count word frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_words[:max_keywords]]
    
    @staticmethod
    def generate_summary(content: str, max_length: int = 200) -> str:
        """Generate content summary"""
        if not content or len(content) <= max_length:
            return content
        
        # Simple summary: first paragraph or first N characters
        sentences = content.split('.')
        
        # Try to get first complete sentence
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) <= max_length and len(sentence) > 20:
                return sentence
        
        # Fallback to first N characters
        summary = content[:max_length].strip()
        if len(content) > max_length:
            summary += '...'
        
        return summary
    
    @staticmethod
    def get_content_excerpt(content: str, start_pos: int = 0, length: int = 200) -> str:
        """Get excerpt from content"""
        if not content:
            return ''
        
        content_length = len(content)
        
        if start_pos >= content_length:
            return ''
        
        end_pos = min(start_pos + length, content_length)
        excerpt = content[start_pos:end_pos]
        
        # Add ellipsis if truncated
        if end_pos < content_length:
            excerpt += '...'
        
        return excerpt
    
    @staticmethod
    def format_content_metrics(content: ContentRelationship) -> Dict[str, Any]:
        """Format content metrics for display"""
        metrics = {
            'basic_metrics': {
                'view_count': content.view_count,
                'like_count': content.like_count,
                'comment_count': content.comment_count,
                'share_count': content.share_count,
                'bookmark_count': content.bookmark_count
            },
            'calculated_metrics': {
                'engagement_rate': content.engagement_rate,
                'content_score': content.content_score,
                'trending_score': content.trending_score
            },
            'quality_metrics': {
                'quality_score': content.quality_score,
                'sentiment_score': content.sentiment_score,
                'readability_score': content.readability_score,
                'complexity_score': content.complexity_score
            }
        }
        
        # Add content length metrics
        if content.content:
            word_count = len(content.content.split())
            reading_time = ContentCalculators.calculate_reading_time(content.content)
            
            metrics['content_metrics'] = {
                'content_length': len(content.content),
                'word_count': word_count,
                'reading_time_minutes': reading_time
            }
        
        return metrics
    
    @staticmethod
    def get_content_stats(user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get content statistics for a user"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get user's content
        content_list = ContentRelationship.query.filter(
            and_(
                ContentRelationship.author_id == user_id,
                ContentRelationship.created_at >= cutoff_date
            )
        ).all()
        
        if not content_list:
            return {
                'total_content': 0,
                'total_views': 0,
                'total_engagement': 0,
                'avg_engagement_rate': 0.0,
                'content_by_type': {},
                'most_viewed': None,
                'most_engaged': None
            }
        
        # Calculate statistics
        total_views = sum(content.view_count for content in content_list)
        total_engagement = sum(
            content.like_count + content.comment_count + content.share_count + content.bookmark_count
            for content in content_list
        )
        
        avg_engagement_rate = sum(content.engagement_rate for content in content_list) / len(content_list)
        
        # Content by type
        content_by_type = {}
        for content in content_list:
            content_type = content.content_type
            content_by_type[content_type] = content_by_type.get(content_type, 0) + 1
        
        # Most viewed content
        most_viewed = max(content_list, key=lambda x: x.view_count) if content_list else None
        
        # Most engaged content
        most_engaged = max(content_list, key=lambda x: x.engagement_score) if content_list else None
        
        return {
            'total_content': len(content_list),
            'total_views': total_views,
            'total_engagement': total_engagement,
            'avg_engagement_rate': avg_engagement_rate,
            'content_by_type': content_by_type,
            'most_viewed': {
                'id': most_viewed.id,
                'title': most_viewed.title,
                'views': most_viewed.view_count
            } if most_viewed else None,
            'most_engaged': {
                'id': most_engaged.id,
                'title': most_engaged.title,
                'engagement_score': most_engaged.engagement_score
            } if most_engaged else None
        }
    
    @staticmethod
    def get_content_recommendations(user_id: int, content_type: str = None,
                                    limit: int = 20) -> List[Dict[str, Any]]:
        """Get content recommendations for user"""
        # This is a simplified implementation
        # In a real system, you'd use the ContentRecommendationService
        
        # Get user's reading history and preferences
        user_content = ContentRelationship.query.filter_by(author_id=user_id).all()
        if not user_content:
            return []
        
        # Get content with similar tags or categories
        user_tags = set()
        user_categories = set()
        
        for content in user_content:
            user_tags.update(tag.name for tag in content.tags)
            user_categories.update(cat.id for cat in content.categories)
        
        # Find similar content
        similar_content = ContentRelationship.query.filter(
            and_(
                ContentRelationship.author_id != user_id,
                ContentRelationship.status == 'published',
                ContentRelationship.visibility == 'public'
            )
        )
        
        if content_type:
            similar_content = similar_content.filter_by(content_type=content_type)
        
        similar_content = similar_content.limit(limit * 2).all()
        
        # Score and filter recommendations
        recommendations = []
        for content in similar_content:
            score = 0.0
            
            # Tag similarity
            content_tags = set(tag.name for tag in content.tags)
            if user_tags and content_tags:
                intersection = len(user_tags.intersection(content_tags))
                union = len(user_tags.union(content_tags))
                tag_similarity = intersection / union if union > 0 else 0
                score += tag_similarity * 0.4
            
            # Category similarity
            content_categories = set(cat.id for cat in content.categories)
            if user_categories and content_categories:
                intersection = len(user_categories.intersection(content_categories))
                union = len(user_categories.union(content_categories))
                category_similarity = intersection / union if union > 0 else 0
                score += category_similarity * 0.3
            
            # Content type match
            user_content_types = set(content.content_type for content in user_content)
            if content.content_type in user_content_types:
                score += 0.2
            
            # Quality score
            score += content.content_score * 0.1
            
            if score > 0.3:  # Minimum similarity threshold
                recommendations.append({
                    'content_id': content.id,
                    'title': content.title,
                    'summary': content.summary,
                    'content_type': content.content_type,
                    'engagement_score': content.engagement_score,
                    'recommendation_score': score,
                    'reason': 'Similar to your content'
                })
        
        # Sort by score and limit
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return recommendations[:limit]
    
    @staticmethod
    def search_content(query: str, content_type: str = None, user_id: int = None,
                       limit: int = 20) -> List[Dict[str, Any]]:
        """Search content"""
        if not query or len(query.strip()) < 2:
            return []
        
        # Build search query
        search_query = ContentRelationship.query.filter(
            and_(
                ContentRelationship.status == 'published',
                or_(
                    ContentRelationship.title.ilike(f'%{query}%'),
                    ContentRelationship.content.ilike(f'%{query}%'),
                    ContentRelationship.summary.ilike(f'%{query}%')
                )
            )
        )
        
        # Apply filters
        if content_type:
            search_query = search_query.filter_by(content_type=content_type)
        
        if user_id:
            # Include user's own content even if not public
            search_query = search_query.filter(
                or_(
                    ContentRelationship.visibility == 'public',
                    ContentRelationship.author_id == user_id
                )
            )
        else:
            search_query = search_query.filter_by(visibility='public')
        
        # Order by relevance (simplified)
        search_query = search_query.order_by(
            ContentRelationship.content_score.desc(),
            ContentRelationship.created_at.desc()
        )
        
        results = search_query.limit(limit).all()
        
        # Format results
        search_results = []
        for content in results:
            search_results.append({
                'content_id': content.id,
                'title': content.title,
                'summary': content.summary,
                'content_type': content.content_type,
                'author': {
                    'id': content.author.id,
                    'username': content.author.username,
                    'first_name': content.author.first_name,
                    'last_name': content.author.last_name
                },
                'metrics': {
                    'view_count': content.view_count,
                    'engagement_score': content.engagement_score,
                    'content_score': content.content_score
                },
                'created_at': content.created_at.isoformat()
            })
        
        return search_results
    
    @staticmethod
    def get_content_by_tags(tag_names: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """Get content by tags"""
        if not tag_names:
            return []
        
        # Find tags
        tags = ContentTag.query.filter(ContentTag.name.in_(tag_names)).all()
        if not tags:
            return []
        
        tag_ids = [tag.id for tag in tags]
        
        # Get content with these tags
        content_list = ContentRelationship.query.filter(
            and_(
                ContentRelationship.status == 'published',
                ContentRelationship.visibility == 'public'
            )
        ).join(content_tags).filter(content_tags.c.tag_id.in_(tag_ids)).distinct().limit(limit).all()
        
        # Format results
        results = []
        for content in content_list:
            results.append({
                'content_id': content.id,
                'title': content.title,
                'summary': content.summary,
                'content_type': content.content_type,
                'tags': [{'id': tag.id, 'name': tag.name} for tag in content.tags],
                'engagement_score': content.engagement_score,
                'created_at': content.created_at.isoformat()
            })
        
        return results
    
    @staticmethod
    def get_content_by_categories(category_ids: List[int], limit: int = 20) -> List[Dict[str, Any]]:
        """Get content by categories"""
        if not category_ids:
            return []
        
        # Get content with these categories
        content_list = ContentRelationship.query.filter(
            and_(
                ContentRelationship.status == 'published',
                ContentRelationship.visibility == 'public'
            )
        ).join(content_categories).filter(content_categories.c.category_id.in_(category_ids)).distinct().limit(limit).all()
        
        # Format results
        results = []
        for content in content_list:
            results.append({
                'content_id': content.id,
                'title': content.title,
                'summary': content.summary,
                'content_type': content.content_type,
                'categories': [{'id': cat.id, 'name': cat.name} for cat in content.categories],
                'engagement_score': content.engagement_score,
                'created_at': content.created_at.isoformat()
            })
        
        return results
    
    @staticmethod
    def get_trending_tags(limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending tags"""
        # Get tags sorted by trending score
        tags = ContentTag.query.order_by(
            ContentTag.trending_score.desc()
        ).limit(limit).all()
        
        results = []
        for tag in tags:
            results.append({
                'tag_id': tag.id,
                'name': tag.name,
                'description': tag.description,
                'usage_count': tag.usage_count,
                'trending_score': tag.trending_score,
                'is_trending': tag.is_trending
            })
        
        return results
    
    @staticmethod
    def get_popular_categories(limit: int = 20) -> List[Dict[str, Any]]:
        """Get popular categories"""
        # Get categories sorted by content count
        categories = ContentCategory.query.filter_by(is_active=True).order_by(
            ContentCategory.content_count.desc()
        ).limit(limit).all()
        
        results = []
        for category in categories:
            results.append({
                'category_id': category.id,
                'name': category.name,
                'description': category.description,
                'content_count': category.content_count,
                'view_count': category.view_count,
                'full_path': category.full_path
            })
        
        return results


class ContentProcessor:
    """Processor for content operations and events"""
    
    @staticmethod
    def process_content_creation(content_id: int, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process content creation event"""
        content = ContentRelationship.query.get(content_id)
        if not content:
            return {'success': False, 'error': 'Content not found'}
        
        # Update content metrics
        content.update_metrics()
        
        # Auto-moderate content
        from .service import ContentModerationService
        moderation_service = ContentModerationService()
        moderation_result = moderation_service.auto_moderate_content(content_id)
        
        # Update trending scores
        from .service import ContentAnalyticsService
        analytics_service = ContentAnalyticsService()
        analytics_service.update_trending_scores()
        
        return {
            'success': True,
            'moderation_result': moderation_result,
            'message': 'Content creation processed successfully'
        }
    
    @staticmethod
    def process_content_update(content_id: int, changes: List[str], user_id: int) -> Dict[str, Any]:
        """Process content update event"""
        content = ContentRelationship.query.get(content_id)
        if not content:
            return {'success': False, 'error': 'Content not found'}
        
        # Update content metrics
        content.update_metrics()
        
        # Re-moderate content if significant changes
        significant_changes = ['title', 'content']
        if any(change in significant_changes for change in changes):
            from .service import ContentModerationService
            moderation_service = ContentModerationService()
            moderation_result = moderation_service.auto_moderate_content(content_id)
        else:
            moderation_result = {'success': True, 'flagged': False}
        
        return {
            'success': True,
            'changes': changes,
            'moderation_result': moderation_result,
            'message': 'Content update processed successfully'
        }
    
    @staticmethod
    def process_content_view(content_id: int, user_id: int = None,
                           view_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process content view event"""
        from .service import ContentAnalyticsService
        analytics_service = ContentAnalyticsService()
        
        # Track view
        result = analytics_service.track_content_view(content_id, user_id, view_data)
        
        # Update trending scores periodically
        if content_id % 100 == 0:  # Update every 100th view to reduce load
            analytics_service.update_trending_scores()
        
        return result
    
    @staticmethod
    def process_content_engagement(content_id: int, engagement_type: str,
                                    user_id: int = None, engagement_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process content engagement event"""
        from .service import ContentAnalyticsService
        analytics_service = ContentAnalyticsService()
        
        # Track engagement
        result = analytics_service.track_content_engagement(content_id, engagement_type, user_id, engagement_data)
        
        # Update content metrics
        content = ContentRelationship.query.get(content_id)
        if content:
            content.update_metrics()
        
        return result
    
    @staticmethod
    def process_content_moderation(content_id: int, action: str, reviewer_id: int,
                                     reason: str = None, notes: str = None) -> Dict[str, Any]:
        """Process content moderation event"""
        from .service import ContentModerationService
        moderation_service = ContentModerationService()
        
        # Process moderation
        result = moderation_service.review_content(content_id, reviewer_id, action, reason, notes)
        
        return result
    
    @staticmethod
    def generate_content_digest(user_id: int, days: int = 7) -> Dict[str, Any]:
        """Generate content digest for user"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get user's content
        user_content = ContentRelationship.query.filter(
            and_(
                ContentRelationship.author_id == user_id,
                ContentRelationship.created_at >= cutoff_date
            )
        ).all()
        
        if not user_content:
            return {
                'success': True,
                'digest': {
                    'period': f'{days} days',
                    'total_content': 0,
                    'total_views': 0,
                    'total_engagement': 0,
                    'top_content': []
                }
            }
        
        # Calculate statistics
        total_views = sum(content.view_count for content in user_content)
        total_engagement = sum(
            content.like_count + content.comment_count + content.share_count + content.bookmark_count
            for content in user_content
        )
        
        # Get top content
        top_content = sorted(user_content, key=lambda x: x.engagement_score, reverse=True)[:5]
        
        top_content_list = []
        for content in top_content:
            top_content_list.append({
                'content_id': content.id,
                'title': content.title,
                'content_type': content.content_type,
                'views': content.view_count,
                'engagement_score': content.engagement_score,
                'created_at': content.created_at.isoformat()
            })
        
        return {
            'success': True,
            'digest': {
                'period': f'{days} days',
                'total_content': len(user_content),
                'total_views': total_views,
                'total_engagement': total_engagement,
                'top_content': top_content_list
            }
        }
    
    @staticmethod
    def cleanup_old_archives():
        """Clean up expired archived content"""
        expired_archives = ContentArchive.query.filter(
            ContentArchive.is_expired == True
        ).all()
        
        deleted_count = 0
        for archive in expired_archives:
            if archive.auto_delete:
                db.session.delete(archive)
                deleted_count += 1
        
        db.session.commit()
        
        return deleted_count
    
    @staticmethod
    def update_tag_trending_scores():
        """Update trending scores for all tags"""
        tags = ContentTag.query.all()
        
        for tag in tags:
            tag.calculate_trending_score()
        
        db.session.commit()
        
        return len(tags)
    
    @staticmethod
    def update_category_content_counts():
        """Update content counts for all categories"""
        categories = ContentCategory.query.filter_by(is_active=True).all()
        
        for category in categories:
            category.update_content_count()
        
        db.session.commit()
        
        return len(categories)
