"""
Content Relationships Service
Auto Bot Solutions Forum

This module provides business logic for managing content relationships,
including versioning, analytics, moderation, archiving, and recommendations.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import and_, or_, desc, func, text
from sqlalchemy.orm import joinedload
from app import db
from app.models import User, Post, Comment
from .models import (
    ContentRelationship, ContentVersion, ContentAnalytics, ContentModeration,
    ContentArchive, ContentRecommendation, ContentTag, ContentCategory, content_tag_associations
)


class ContentService:
    """Service for managing content relationships and operations"""
    
    def __init__(self):
        self.default_content_type = 'post'
        self.max_content_length = 50000
        self.versioning_enabled = True
    
    def create_content(self, user_id: int, title: str, content: str, 
                       content_type: str = None, visibility: str = 'public',
                       summary: str = None, tags: List[str] = None,
                       categories: List[int] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create new content with relationships"""
        if not title or not title.strip():
            return {'success': False, 'error': 'Title is required'}
        
        if not content or not content.strip():
            return {'success': False, 'error': 'Content is required'}
        
        if len(content) > self.max_content_length:
            return {'success': False, 'error': 'Content too long'}
        
        # Create content
        content_relationship = ContentRelationship(
            title=title.strip(),
            content=content.strip(),
            summary=summary,
            content_type=content_type or self.default_content_type,
            author_id=user_id,
            visibility=visibility,
            status='published',
            published_at=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        
        # Generate slug
        content_relationship.slug = self._generate_slug(title)
        
        db.session.add(content_relationship)
        db.session.flush()  # Get the ID
        
        # Create initial version
        if self.versioning_enabled:
            version = content_relationship.create_version(
                change_summary='Initial content creation',
                change_type='create'
            )
        
        # Add tags
        if tags:
            self._add_content_tags(content_relationship.id, tags)
        
        # Add categories
        if categories:
            self._add_content_categories(content_relationship.id, categories)
        
        # Create analytics record
        analytics = ContentAnalytics(content_id=content_relationship.id)
        db.session.add(analytics)
        
        db.session.commit()
        
        return {
            'success': True,
            'content_id': content_relationship.id,
            'version_id': version.id if self.versioning_enabled else None,
            'message': 'Content created successfully'
        }
    
    def update_content(self, content_id: int, user_id: int, title: str = None,
                       content: str = None, summary: str = None, tags: List[str] = None,
                       categories: List[int] = None, change_summary: str = None,
                       metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update existing content"""
        content_relationship = ContentRelationship.query.get(content_id)
        if not content_relationship:
            return {'success': False, 'error': 'Content not found'}
        
        # Check permissions
        if content_relationship.author_id != user_id:
            return {'success': False, 'error': 'No permission to edit this content'}
        
        # Check if content is locked
        if content_relationship.is_locked:
            return {'success': False, 'error': 'Content is locked for editing'}
        
        # Track changes
        changes = []
        
        if title and title.strip() != content_relationship.title:
            changes.append('title')
            content_relationship.title = title.strip()
            content_relationship.slug = self._generate_slug(title.strip())
        
        if content and content.strip() != content_relationship.content:
            changes.append('content')
            content_relationship.content = content.strip()
        
        if summary is not None and summary != content_relationship.summary:
            changes.append('summary')
            content_relationship.summary = summary
        
        if metadata:
            content_relationship.metadata.update(metadata)
            changes.append('metadata')
        
        if not changes:
            return {'success': False, 'error': 'No changes detected'}
        
        # Update tags
        if tags is not None:
            self._update_content_tags(content_id, tags)
            changes.append('tags')
        
        # Update categories
        if categories is not None:
            self._update_content_categories(content_id, categories)
            changes.append('categories')
        
        # Create version
        if self.versioning_enabled:
            version = content_relationship.create_version(
                change_summary=change_summary or f'Updated: {", ".join(changes)}',
                change_type='update',
                editor_id=user_id
            )
        
        content_relationship.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return {
            'success': True,
            'version_id': version.id if self.versioning_enabled else None,
            'changes': changes,
            'message': 'Content updated successfully'
        }
    
    def delete_content(self, content_id: int, user_id: int, reason: str = None) -> Dict[str, Any]:
        """Delete content (soft delete)"""
        content_relationship = ContentRelationship.query.get(content_id)
        if not content_relationship:
            return {'success': False, 'error': 'Content not found'}
        
        # Check permissions
        if content_relationship.author_id != user_id:
            return {'success': False, 'error': 'No permission to delete this content'}
        
        # Soft delete
        content_relationship.soft_delete()
        
        # Create moderation record if reason provided
        if reason:
            moderation = ContentModeration(
                content_id=content_id,
                status='approved',
                reason=reason,
                reviewer_id=user_id,
                review_action='delete'
            )
            db.session.add(moderation)
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Content deleted successfully'
        }
    
    def archive_content(self, content_id: int, user_id: int, reason: str = 'manual',
                       retention_days: int = 365) -> Dict[str, Any]:
        """Archive content"""
        content_relationship = ContentRelationship.query.get(content_id)
        if not content_relationship:
            return {'success': False, 'error': 'Content not found'}
        
        # Check permissions
        if content_relationship.author_id != user_id:
            return {'success': False, 'error': 'No permission to archive this content'}
        
        # Create archive record
        archive = ContentArchive(
            original_content_id=content_id,
            archive_reason=reason,
            title=content_relationship.title,
            content_type=content_relationship.content_type,
            author_id=content_relationship.author_id,
            created_at=content_relationship.created_at
        )
        
        # Set retention date
        archive.set_retention_date(retention_days)
        
        # Archive the content
        content_relationship.archive()
        
        db.session.add(archive)
        db.session.commit()
        
        return {
            'success': True,
            'archive_id': archive.id,
            'retention_date': archive.retention_date.isoformat(),
            'message': 'Content archived successfully'
        }
    
    def get_content(self, content_id: int, user_id: int = None) -> Dict[str, Any]:
        """Get content with full details"""
        content_relationship = ContentRelationship.query.options(
            joinedload(ContentRelationship.author),
            joinedload(ContentRelationship.tags),
            joinedload(ContentRelationship.categories)
        ).get(content_id)
        
        if not content_relationship:
            return {'success': False, 'error': 'Content not found'}
        
        # Check visibility permissions
        if user_id and not self._can_view_content(content_relationship, user_id):
            return {'success': False, 'error': 'No permission to view this content'}
        
        # Get analytics
        analytics = ContentAnalytics.query.filter_by(content_id=content_id).first()
        
        # Get latest version
        latest_version = ContentVersion.query.filter_by(
            content_id=content_id
        ).order_by(ContentRelationship.version_number.desc()).first()
        
        # Get related content
        related_content = content_relationship.get_related_content(limit=5)
        
        result = {
            'success': True,
            'content': {
                'id': content_relationship.id,
                'uuid': str(content_relationship.uuid),
                'title': content_relationship.title,
                'content': content_relationship.content,
                'summary': content_relationship.summary,
                'content_type': content_relationship.content_type,
                'author': {
                    'id': content_relationship.author.id,
                    'username': content_relationship.author.username,
                    'first_name': content_relationship.author.first_name,
                    'last_name': content_relationship.author.last_name
                },
                'visibility': content_relationship.visibility,
                'status': content_relationship.status,
                'slug': content_relationship.slug,
                'tags': [{'id': tag.id, 'name': tag.name} for tag in content_relationship.tags],
                'categories': [{'id': cat.id, 'name': cat.name} for cat in content_relationship.categories],
                'metrics': {
                    'view_count': content_relationship.view_count,
                    'like_count': content_relationship.like_count,
                    'comment_count': content_relationship.comment_count,
                    'share_count': content_relationship.share_count,
                    'bookmark_count': content_relationship.bookmark_count,
                    'engagement_rate': content_relationship.engagement_rate,
                    'content_score': content_relationship.content_score
                },
                'timestamps': {
                    'created_at': content_relationship.created_at.isoformat(),
                    'updated_at': content_relationship.updated_at.isoformat(),
                    'published_at': content_relationship.published_at.isoformat() if content_relationship.published_at else None
                },
                'settings': {
                    'allow_comments': content_relationship.allow_comments,
                    'allow_sharing': content_relationship.allow_sharing,
                    'is_featured': content_relationship.is_featured,
                    'is_pinned': content_relationship.is_pinned,
                    'is_locked': content_relationship.is_locked
                }
            }
        }
        
        if analytics:
            result['content']['analytics'] = {
                'total_views': analytics.total_views,
                'unique_views': analytics.unique_views,
                'average_view_duration': analytics.average_view_duration,
                'bounce_rate': analytics.bounce_rate,
                'engagement_rate': analytics.engagement_rate,
                'average_daily_views': analytics.average_daily_views
            }
        
        if latest_version:
            result['content']['version'] = {
                'version_number': latest_version.version_number,
                'change_summary': latest_version.change_summary,
                'change_type': latest_version.change_type,
                'created_at': latest_version.created_at.isoformat()
            }
        
        if related_content:
            result['content']['related_content'] = [
                {
                    'id': related.id,
                    'title': related.title,
                    'content_type': related.content_type,
                    'engagement_score': related.engagement_score
                }
                for related in related_content
            ]
        
        return result
    
    def get_content_list(self, user_id: int = None, content_type: str = None,
                         status: str = 'published', visibility: str = None,
                         sort_by: str = 'created_at', order: str = 'desc',
                         limit: int = 20, offset: int = 0,
                         featured_only: bool = False) -> Dict[str, Any]:
        """Get content list with filtering and sorting"""
        query = ContentRelationship.query.options(
            joinedload(ContentRelationship.author),
            joinedload(ContentRelationship.tags)
        )
        
        # Apply filters
        if content_type:
            query = query.filter_by(content_type=content_type)
        
        if status:
            query = query.filter_by(status=status)
        
        if visibility:
            query = query.filter_by(visibility=visibility)
        elif user_id:
            # Filter by visibility for authenticated user
            query = query.filter(
                or_(
                    ContentRelationship.visibility == 'public',
                    ContentRelationship.author_id == user_id
                )
            )
        else:
            # Only show public content to unauthenticated users
            query = query.filter_by(visibility='public')
        
        if featured_only:
            query = query.filter_by(is_featured=True)
        
        # Apply sorting
        if sort_by == 'created_at':
            query = query.order_by(ContentRelationship.created_at.desc() if order == 'desc' else ContentRelationship.created_at.asc())
        elif sort_by == 'updated_at':
            query = query.order_by(ContentRelationship.updated_at.desc() if order == 'desc' else ContentRelationship.updated_at.asc())
        elif sort_by == 'view_count':
            query = query.order_by(ContentRelationship.view_count.desc() if order == 'desc' else ContentRelationship.view_count.asc())
        elif sort_by == 'engagement_score':
            query = query.order_by(ContentRelationship.engagement_score.desc() if order == 'desc' else ContentRelationship.engagement_score.asc())
        elif sort_by == 'content_score':
            query = query.order_by(ContentRelationship.content_score.desc() if order == 'desc' else ContentRelationship.content_score.asc())
        else:
            query = query.order_by(ContentRelationship.created_at.desc())
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        content_list = query.offset(offset).limit(limit).all()
        
        # Format results
        results = []
        for content in content_list:
            # Check visibility permissions
            if user_id and not self._can_view_content(content, user_id):
                continue
            
            results.append({
                'id': content.id,
                'uuid': str(content.uuid),
                'title': content.title,
                'summary': content.summary,
                'content_type': content.content_type,
                'author': {
                    'id': content.author.id,
                    'username': content.author.username,
                    'first_name': content.author.first_name,
                    'last_name': content.author.last_name
                },
                'visibility': content.visibility,
                'status': content.status,
                'slug': content.slug,
                'tags': [{'id': tag.id, 'name': tag.name} for tag in content.tags],
                'metrics': {
                    'view_count': content.view_count,
                    'like_count': content.like_count,
                    'comment_count': content.comment_count,
                    'share_count': content.share_count,
                    'engagement_rate': content.engagement_rate,
                    'content_score': content.content_score
                },
                'timestamps': {
                    'created_at': content.created_at.isoformat(),
                    'updated_at': content.updated_at.isoformat(),
                    'published_at': content.published_at.isoformat() if content.published_at else None
                },
                'settings': {
                    'is_featured': content.is_featured,
                    'is_pinned': content.is_pinned,
                    'is_locked': content.is_locked
                }
            })
        
        return {
            'success': True,
            'content': results,
            'pagination': {
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        }
    
    def get_content_versions(self, content_id: int, user_id: int = None) -> Dict[str, Any]:
        """Get version history for content"""
        content_relationship = ContentRelationship.query.get(content_id)
        if not content_relationship:
            return {'success': False, 'error': 'Content not found'}
        
        # Check permissions
        if user_id and not self._can_view_content(content_relationship, user_id):
            return {'success': False, 'error': 'No permission to view this content'}
        
        versions = ContentVersion.query.filter_by(content_id=content_id).order_by(
            ContentVersion.version_number.desc()
        ).all()
        
        result = []
        for version in versions:
            author = version.author
            editor = version.editor
            
            version_data = {
                'id': version.id,
                'version_number': version.version_number,
                'title': version.title,
                'content': version.content,
                'content_type': version.content_type,
                'change_summary': version.change_summary,
                'change_type': version.change_type,
                'author': {
                    'id': author.id,
                    'username': author.username,
                    'first_name': author.first_name,
                    'last_name': author.last_name
                } if author else None,
                'created_at': version.created_at.isoformat(),
                'is_major_version': version.is_major_version,
                'metrics': {
                    'content_length': version.content_length,
                    'word_count': version.word_count,
                    'reading_time_minutes': version.reading_time_minutes,
                    'quality_score': version.quality_score
                }
            }
            
            if editor and editor.id != author.id:
                version_data['editor'] = {
                    'id': editor.id,
                    'username': editor.username,
                    'first_name': editor.first_name,
                    'last_name': editor.last_name
                }
            
            result.append(version_data)
        
        return {
            'success': True,
            'versions': result,
            'total_count': len(result)
        }
    
    def restore_version(self, content_id: int, version_id: int, user_id: int) -> Dict[str, Any]:
        """Restore content to a specific version"""
        content_relationship = ContentRelationship.query.get(content_id)
        if not content_relationship:
            return {'success': False, 'error': 'Content not found'}
        
        # Check permissions
        if content_relationship.author_id != user_id:
            return {'success': False, 'error': 'No permission to restore this content'}
        
        version = ContentVersion.query.get(version_id)
        if not version or version.content_id != content_id:
            return {'success': False, 'error': 'Version not found'}
        
        # Check if content is locked
        if content_relationship.is_locked:
            return {'success': False, 'error': 'Content is locked for editing'}
        
        # Restore content
        old_title = content_relationship.title
        old_content = content_relationship.content
        old_summary = content_relationship.summary
        
        content_relationship.title = version.title
        content_relationship.content = version.content
        content_relationship.summary = version.summary
        content_relationship.updated_at = datetime.now(timezone.utc)
        
        # Create new version documenting the restore
        new_version = content_relationship.create_version(
            change_summary=f'Restored to version {version.version_number}',
            change_type='restore',
            editor_id=user_id
        )
        
        db.session.commit()
        
        return {
            'success': True,
            'version_id': new_version.id,
            'changes': ['title', 'content', 'summary'],
            'message': 'Content restored successfully'
        }
    
    def add_content_relationship(self, parent_id: int, child_id: int, 
                                relationship_type: str, strength: float = 0.0) -> Dict[str, Any]:
        """Add relationship between content items"""
        parent_content = ContentRelationship.query.get(parent_id)
        child_content = ContentRelationship.query.get(child_id)
        
        if not parent_content or not child_content:
            return {'success': False, 'error': 'Content not found'}
        
        # Validate relationship type
        valid_types = ['related', 'series', 'followup', 'reference', 'duplicate', 'translation']
        if relationship_type not in valid_types:
            return {'success': False, 'error': 'Invalid relationship type'}
        
        # Add relationship
        parent_content.add_relationship(child_content, relationship_type, strength)
        
        return {
            'success': True,
            'message': 'Content relationship added successfully'
        }
    
    def remove_content_relationship(self, parent_id: int, child_id: int, 
                                   relationship_type: str) -> Dict[str, Any]:
        """Remove relationship between content items"""
        parent_content = ContentRelationship.query.get(parent_id)
        child_content = ContentRelationship.query.get(child_id)
        
        if not parent_content or not child_content:
            return {'success': False, 'error': 'Content not found'}
        
        # Remove relationship
        parent_content.remove_relationship(child_content, relationship_type)
        
        return {
            'success': True,
            'message': 'Content relationship removed successfully'
        }
    
    def get_related_content(self, content_id: int, relationship_type: str = None,
                           limit: int = 20) -> Dict[str, Any]:
        """Get related content"""
        content_relationship = ContentRelationship.query.get(content_id)
        if not content_relationship:
            return {'success': False, 'error': 'Content not found'}
        
        related_content = content_relationship.get_related_content(relationship_type, limit)
        
        result = []
        for related in related_content:
            result.append({
                'id': related.id,
                'title': related.title,
                'summary': related.summary,
                'content_type': related.content_type,
                'engagement_score': related.engagement_score,
                'content_score': related.content_score,
                'created_at': related.created_at.isoformat()
            })
        
        return {
            'success': True,
            'related_content': result,
            'total_count': len(result)
        }
    
    def _generate_slug(self, title: str) -> str:
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
    
    def _can_view_content(self, content: ContentRelationship, user_id: int) -> bool:
        """Check if user can view content"""
        if content.is_public:
            return True
        
        if not user_id:
            return False
        
        # Author can always view their own content
        if content.author_id == user_id:
            return True
        
        # Check other visibility rules
        if content.visibility == 'private':
            return False
        elif content.visibility == 'friends':
            # Check if user is friends with author
            from app.social.models import UserConnection
            friendship = UserConnection.query.filter_by(
                user_id=content.author_id,
                connected_user_id=user_id,
                connection_type='friend',
                status='active'
            ).first()
            return friendship is not None
        
        return False
    
    def _add_content_tags(self, content_id: int, tags: List[str]):
        """Add tags to content"""
        for tag_name in tags:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
            
            # Find or create tag
            tag = ContentTag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = ContentTag(name=tag_name)
                db.session.add(tag)
                db.session.flush()
            
            # Add tag to content
            if tag not in ContentRelationship.query.get(content_id).tags:
                db.execute(content_tag_associations.insert().values(
                    content_id=content_id,
                    tag_id=tag.id
                ))
            
            tag.update_usage_count()
    
    def _update_content_tags(self, content_id: int, tags: List[str]):
        """Update content tags"""
        # Remove existing tags
        db.execute(content_tag_associations.delete().where(content_tag_associations.c.content_id == content_id))
        
        # Add new tags
        self._add_content_tags(content_id, tags)
    
    def _add_content_categories(self, content_id: int, category_ids: List[int]):
        """Add categories to content"""
        for category_id in category_ids:
            # Check if category exists
            category = ContentCategory.query.get(category_id)
            if not category or not category.is_active:
                continue
            
            # Add category to content
            if category not in ContentRelationship.query.get(content_id).categories:
                db.execute(content_categories.insert().values(
                    content_id=content_id,
                    category_id=category_id
                ))
            
            category.update_content_count()
    
    def _update_content_categories(self, content_id: int, category_ids: List[int]):
        """Update content categories"""
        # Remove existing categories
        db.execute(content_categories.delete().where(content_categories.c.content_id == content_id))
        
        # Add new categories
        self._add_content_categories(content_id, category_ids)


class ContentAnalyticsService:
    """Service for content analytics and insights"""
    
    def __init__(self):
        self.analytics_calculation_interval = 3600  # 1 hour
    
    def track_content_view(self, content_id: int, user_id: int = None,
                          view_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Track content view"""
        content = ContentRelationship.query.get(content_id)
        if not content:
            return {'success': False, 'error': 'Content not found'}
        
        # Update view count
        content.view_count += 1
        
        # Get or create analytics
        analytics = ContentAnalytics.query.filter_by(content_id=content_id).first()
        if not analytics:
            analytics = ContentAnalytics(content_id=content_id)
            db.session.add(analytics)
        
        # Update view analytics
        view_data = view_data or {}
        analytics.update_view_analytics(view_data)
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'View tracked successfully'
        }
    
    def track_content_engagement(self, content_id: int, engagement_type: str,
                                user_id: int = None, engagement_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Track content engagement (like, comment, share, etc.)"""
        content = ContentRelationship.query.get(content_id)
        if not content:
            return {'success': False, 'error': 'Content not found'}
        
        # Update engagement counts
        if engagement_type == 'like':
            content.like_count += 1
        elif engagement_type == 'comment':
            content.comment_count += 1
        elif engagement_type == 'share':
            content.share_count += 1
        elif engagement_type == 'bookmark':
            content.bookmark_count += 1
        
        # Get or create analytics
        analytics = ContentAnalytics.query.filter_by(content_id=content_id).first()
        if not analytics:
            analytics = ContentAnalytics(content_id=content_id)
            db.session.add(analytics)
        
        # Update engagement analytics
        engagement_data = engagement_data or {}
        engagement_data['total'] = 1
        engagement_data[engagement_type + 's'] = 1
        
        analytics.update_engagement_analytics(engagement_data)
        
        # Update content metrics
        content.update_metrics()
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'{engagement_type} tracked successfully'
        }
    
    def get_content_analytics(self, content_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics for content"""
        content = ContentRelationship.query.get(content_id)
        if not content:
            return {'success': False, 'error': 'Content not found'}
        
        analytics = ContentAnalytics.query.filter_by(content_id=content_id).first()
        if not analytics:
            return {'success': False, 'error': 'Analytics not found'}
        
        # Calculate time-based analytics
        analytics.calculate_time_based_analytics()
        
        # Get engagement trends
        engagement_trends = self._get_engagement_trends(content_id, days)
        
        # Get view patterns
        view_patterns = self._get_view_patterns(content_id, days)
        
        return {
            'success': True,
            'analytics': {
                'basic_metrics': {
                    'total_views': analytics.total_views,
                    'unique_views': analytics.unique_views,
                    'average_view_duration': analytics.average_view_duration,
                    'bounce_rate': analytics.bounce_rate,
                    'engagement_rate': analytics.engagement_rate,
                    'average_daily_views': analytics.average_daily_views
                },
                'engagement_metrics': {
                    'total_engagements': analytics.total_engagements,
                    'likes': analytics.likes,
                    'comments': analytics.comments,
                    'shares': analytics.shares,
                    'bookmarks': analytics.bookmarks,
                    'downloads': analytics.downloads
                },
                'time_based_analytics': {
                    'views_today': analytics.views_today,
                    'views_this_week': analytics.views_this_week,
                    'views_this_month': analytics.views_this_month
                },
                'geographic_analytics': analytics.view_by_country or {},
                'device_analytics': analytics.view_by_device or {},
                'traffic_sources': analytics.traffic_sources or {},
                'engagement_trends': engagement_trends,
                'view_patterns': view_patterns
            }
        }
    
    def get_trending_content(self, content_type: str = None, limit: int = 20,
                           hours: int = 24) -> List[Dict[str, Any]]:
        """Get trending content"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = ContentRelationship.query.filter(
            and_(
                ContentRelationship.created_at >= cutoff_date,
                ContentRelationship.status == 'published',
                ContentRelationship.visibility == 'public'
            )
        )
        
        if content_type:
            query = query.filter_by(content_type=content_type)
        
        # Order by trending score
        query = query.order_by(desc(ContentRelationship.trending_score))
        
        trending_content = query.limit(limit).all()
        
        result = []
        for content in trending_content:
            result.append({
                'id': content.id,
                'title': content.title,
                'summary': content.summary,
                'content_type': content.content_type,
                'author': {
                    'id': content.author.id,
                    'username': content.author.username
                },
                'metrics': {
                    'view_count': content.view_count,
                    'engagement_score': content.engagement_score,
                    'trending_score': content.trending_score,
                    'content_score': content.content_score
                },
                'created_at': content.created_at.isoformat()
            })
        
        return result
    
    def get_content_performance_report(self, content_id: int, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        content = ContentRelationship.query.get(content_id)
        if not content:
            return {'success': False, 'error': 'Content not found'}
        
        analytics = ContentAnalytics.query.filter_by(content_id=content_id).first()
        if not analytics:
            return {'success': False, 'error': 'Analytics not found'}
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(content_id, days)
        
        # Get recommendations
        recommendations = self._generate_performance_recommendations(content, analytics, performance_metrics)
        
        return {
            'success': True,
            'report': {
                'content_info': {
                    'id': content.id,
                    'title': content.title,
                    'content_type': content.content_type,
                    'created_at': content.created_at.isoformat()
                },
                'performance_metrics': performance_metrics,
                'recommendations': recommendations,
                'summary': {
                    'overall_score': content.content_score,
                    'performance_grade': self._calculate_performance_grade(content.content_score)
                }
            }
        }
    
    def update_trending_scores(self):
        """Update trending scores for all content"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=24)
        
        content_list = ContentRelationship.query.filter(
            and_(
                ContentRelationship.created_at >= cutoff_date,
                ContentRelationship.status == 'published',
                ContentRelationship.visibility == 'public'
            )
        ).all()
        
        for content in content_list:
            # Calculate trending score based on recent engagement
            analytics = ContentAnalytics.query.filter_by(content_id=content.id).first()
            
            if analytics:
                # Simple trending calculation
                recent_views = analytics.views_today
                recent_engagement = analytics.total_engagements
                
                trending_score = (recent_views * 0.6 + recent_engagement * 0.4) / 100.0
                content.trending_score = min(1.0, trending_score)
        
        db.session.commit()
        
        return len(content_list)
    
    def _get_engagement_trends(self, content_id: int, days: int) -> Dict[str, Any]:
        """Get engagement trends over time"""
        # This is a simplified implementation
        # In a real system, you'd query detailed engagement logs
        
        from datetime import timedelta
        
        trends = {}
        current_date = datetime.now(timezone.utc).date()
        
        for i in range(days):
            date = current_date - timedelta(days=i)
            # Simplified trend data
            trends[date.isoformat()] = {
                'views': 0,  # Would be calculated from logs
                'engagements': 0,  # Would be calculated from logs
                'engagement_rate': 0.0
            }
        
        return trends
    
    def _get_view_patterns(self, content_id: int, days: int) -> Dict[str, Any]:
        """Get view patterns over time"""
        # This is a simplified implementation
        # In a real system, you'd analyze detailed view logs
        
        patterns = {
            'hourly_distribution': {},
            'daily_distribution': {},
            'peak_viewing_hours': [],
            'average_session_duration': 0.0
        }
        
        # Generate sample hourly distribution
        for hour in range(24):
            patterns['hourly_distribution'][hour] = 0  # Would be calculated from logs
        
        return patterns
    
    def _calculate_performance_metrics(self, content_id: int, days: int) -> Dict[str, Any]:
        """Calculate performance metrics"""
        content = ContentRelationship.query.get(content_id)
        analytics = ContentAnalytics.query.filter_by(content_id=content_id).first()
        
        if not content or not analytics:
            return {}
        
        metrics = {
            'view_performance': {
                'total_views': analytics.total_views,
                'daily_average': analytics.average_daily_views,
                'growth_rate': 0.0  # Would calculate from historical data
            },
            'engagement_performance': {
                'engagement_rate': analytics.engagement_rate,
                'total_engagements': analytics.total_engagements,
                'engagement_per_view': analytics.total_engagements / analytics.total_views if analytics.total_views > 0 else 0
            },
            'content_quality': {
                'quality_score': content.quality_score,
                'readability_score': 0.0,  # Would calculate from content analysis
                'content_length': len(content.content) if content.content else 0
            },
            'audience_retention': {
                'bounce_rate': analytics.bounce_rate,
                'average_view_duration': analytics.average_view_duration,
                'return_visitor_rate': 0.0  # Would calculate from analytics
            }
        }
        
        return metrics
    
    def _generate_performance_recommendations(self, content: ContentRelationship,
                                            analytics: ContentAnalytics,
                                            metrics: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # View performance recommendations
        if analytics.total_views < 100:
            recommendations.append("Consider improving SEO and sharing to increase views")
        
        # Engagement recommendations
        if analytics.engagement_rate < 0.05:  # Less than 5%
            recommendations.append("Content has low engagement - consider adding more interactive elements")
        
        # Quality recommendations
        if content.quality_score < 0.5:
            recommendations.append("Content quality score is low - consider improving content structure and readability")
        
        # Retention recommendations
        if analytics.bounce_rate > 0.7:  # More than 70%
            recommendations.append("High bounce rate - consider improving content introduction and relevance")
        
        # Length recommendations
        content_length = len(content.content) if content.content else 0
        if content_length < 500:
            recommendations.append("Content is quite short - consider adding more detail and value")
        elif content_length > 5000:
            recommendations.append("Content is quite long - consider breaking into smaller, focused pieces")
        
        return recommendations
    
    def _calculate_performance_grade(self, score: float) -> str:
        """Calculate performance grade based on score"""
        if score >= 0.8:
            return 'A'
        elif score >= 0.6:
            return 'B'
        elif score >= 0.4:
            return 'C'
        elif score >= 0.2:
            return 'D'
        else:
            return 'F'


class ContentModerationService:
    """Service for content moderation and review"""
    
    def __init__(self):
        self.auto_moderation_enabled = True
        self.moderation_threshold = 0.7
    
    def flag_content(self, content_id: int, reporter_id: int, reason: str,
                    severity: int = 3) -> Dict[str, Any]:
        """Flag content for moderation review"""
        content = ContentRelationship.query.get(content_id)
        if not content:
            return {'success': False, 'error': 'Content not found'}
        
        # Get or create moderation record
        moderation = ContentModeration.query.filter_by(content_id=content_id).first()
        if not moderation:
            moderation = ContentModeration(content_id=content_id)
            db.session.add(moderation)
        
        # Add user report
        moderation.add_user_report(reporter_id, reason)
        
        # Auto-flag if enough reports or high severity
        if moderation.report_count >= 5 or severity >= 4:
            moderation.flag(reason, severity, auto_flagged=True)
        
        db.session.commit()
        
        return {
            'success': True,
            'moderation_id': moderation.id,
            'status': moderation.status,
            'message': 'Content flagged for moderation'
        }
    
    def review_content(self, content_id: int, reviewer_id: int, action: str,
                       reason: str = None, notes: str = None) -> Dict[str, Any]:
        """Review flagged content"""
        moderation = ContentModeration.query.filter_by(content_id=content_id).first()
        if not moderation:
            return {'success': False, 'error': 'No moderation record found'}
        
        content = ContentRelationship.query.get(content_id)
        if not content:
            return {'success': False, 'error': 'Content not found'}
        
        # Apply moderation action
        if action == 'approve':
            moderation.approve(reviewer_id, notes)
        elif action == 'reject':
            moderation.reject(reviewer_id, reason, notes)
            content.soft_delete()
        elif action == 'edit':
            # Would implement content editing functionality
            moderation.approve(reviewer_id, f"Content edited: {notes}")
        elif action == 'delete':
            moderation.reject(reviewer_id, reason, notes)
            content.soft_delete()
        elif action == 'flag':
            moderation.flag(reason, moderation.severity, auto_flagged=False)
        
        db.session.commit()
        
        return {
            'success': True,
            'action': action,
            'message': f'Content {action} successfully'
        }
    
    def get_pending_moderation(self, reviewer_id: int = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pending moderation items"""
        query = ContentModeration.query.filter_by(status='pending')
        
        # Sort by priority
        priority_order = text("CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 WHEN 'low' THEN 4 END")
        query = query.order_by(priority_order, ContentModeration.created_at)
        
        pending_items = query.limit(limit).all()
        
        result = []
        for item in pending_items:
            content = item.content
            
            result.append({
                'moderation_id': item.id,
                'content_id': item.content_id,
                'content': {
                    'title': content.title,
                    'content_type': content.content_type,
                    'author': {
                        'id': content.author.id,
                        'username': content.author.username
                    },
                    'created_at': content.created_at.isoformat()
                },
                'moderation': {
                    'status': item.status,
                    'priority': item.priority,
                    'severity': item.severity,
                    'report_count': item.report_count,
                    'report_reasons': item.report_reasons,
                    'auto_flagged': item.auto_flagged,
                    'confidence_score': item.confidence_score
                }
            })
        
        return result
    
    def auto_moderate_content(self, content_id: int) -> Dict[str, Any]:
        """Automatically moderate content using AI/ML"""
        if not self.auto_moderation_enabled:
            return {'success': False, 'error': 'Auto-moderation is disabled'}
        
        content = ContentRelationship.query.get(content_id)
        if not content:
            return {'success': False, 'error': 'Content not found'}
        
        # This is a simplified implementation
        # In a real system, you'd use actual AI/ML models
        
        # Simple content analysis
        violations = []
        confidence = 0.0
        
        # Check for potentially problematic content
        if content.content:
            content_lower = content.content.lower()
            
            # Simple keyword-based detection (in real system, use sophisticated ML)
            problematic_keywords = ['spam', 'inappropriate', 'offensive', 'hate']
            for keyword in problematic_keywords:
                if keyword in content_lower:
                    violations.append(f"Contains potentially {keyword} content")
                    confidence += 0.2
        
        # Check content length
        if content.content and len(content.content) < 10:
            violations.append("Content too short")
            confidence += 0.1
        
        # Check for excessive capitalization
        if content.content and content.content.isupper():
            violations.append("Excessive capitalization")
            confidence += 0.1
        
        # Determine if content should be flagged
        should_flag = confidence >= self.moderation_threshold
        
        if should_flag and violations:
            # Get or create moderation record
            moderation = ContentModeration.query.filter_by(content_id=content_id).first()
            if not moderation:
                moderation = ContentModeration(content_id=content_id)
                db.session.add(moderation)
            
            # Auto-flag the content
            moderation.flag(
                reason='; '.join(violations),
                severity=3,
                auto_flagged=True,
                confidence=confidence
            )
            
            # Add rule violations
            moderation.rule_violations = violations
            
            db.session.commit()
            
            return {
                'success': True,
                'flagged': True,
                'violations': violations,
                'confidence': confidence,
                'message': 'Content auto-flagged for moderation'
            }
        
        return {
            'success': True,
            'flagged': False,
            'confidence': confidence,
            'message': 'Content passed auto-moderation'
        }
    
    def get_moderation_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get moderation statistics"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        stats = {
            'total_moderated': 0,
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'flagged': 0,
            'auto_flagged': 0,
            'average_resolution_time': 0.0,
            'top_violation_types': {}
        }
        
        # Query moderation records
        moderations = ContentModeration.query.filter(
            ContentModeration.created_at >= cutoff_date
        ).all()
        
        resolution_times = []
        violation_types = {}
        
        for moderation in moderations:
            stats['total_moderated'] += 1
            
            # Count by status
            if moderation.status == 'pending':
                stats['pending'] += 1
            elif moderation.status == 'approved':
                stats['approved'] += 1
            elif moderation.status == 'rejected':
                stats['rejected'] += 1
            elif moderation.status == 'flagged':
                stats['flagged'] += 1
            
            # Count auto-flagged
            if moderation.auto_flagged:
                stats['auto_flagged'] += 1
            
            # Calculate resolution time
            if moderation.resolved_at:
                resolution_time = (moderation.resolved_at - moderation.created_at).total_seconds() / 3600
                resolution_times.append(resolution_time)
            
            # Count violation types
            if moderation.reason:
                violation_type = moderation.reason.split(':')[0]  # Simple categorization
                violation_types[violation_type] = violation_types.get(violation_type, 0) + 1
        
        # Calculate average resolution time
        if resolution_times:
            stats['average_resolution_time'] = sum(resolution_times) / len(resolution_times)
        
        # Get top violation types
        if violation_types:
            sorted_violations = sorted(violation_types.items(), key=lambda x: x[1], reverse=True)
            stats['top_violation_types'] = dict(sorted_violations[:5])
        
        return stats


class ContentRecommendationService:
    """Service for content recommendations and personalization"""
    
    def __init__(self):
        self.recommendation_cache_ttl = 1800  # 30 minutes
        self.max_recommendations = 50
    
    def get_user_recommendations(self, user_id: int, content_type: str = None,
                               limit: int = 20) -> List[Dict[str, Any]]:
        """Get personalized content recommendations for user"""
        # Get user's reading history and preferences
        user_preferences = self._get_user_preferences(user_id)
        
        # Get content candidates
        candidates = self._get_content_candidates(user_id, content_type)
        
        # Score and rank candidates
        scored_candidates = []
        for content in candidates:
            score = self._calculate_recommendation_score(user_id, content, user_preferences)
            scored_candidates.append({
                'content_id': content.id,
                'title': content.title,
                'summary': content.summary,
                'content_type': content.content_type,
                'engagement_score': content.engagement_score,
                'recommendation_score': score,
                'reason': self._generate_recommendation_reason(user_id, content, score)
            })
        
        # Sort by score and limit
        scored_candidates.sort(key=lambda x: x['recommendation_score'], reverse=True)
        recommendations = scored_candidates[:limit]
        
        # Store recommendations in database
        self._store_recommendations(user_id, recommendations)
        
        return recommendations
    
    def get_similar_content(self, content_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get content similar to specified content"""
        content = ContentRelationship.query.get(content_id)
        if not content:
            return []
        
        # Get content with similar tags and categories
        similar_content = ContentRelationship.query.filter(
            and_(
                ContentRelationship.id != content_id,
                ContentRelationship.content_type == content.content_type,
                ContentRelationship.status == 'published',
                ContentRelationship.visibility == 'public'
            )
        ).all()
        
        # Calculate similarity scores
        scored_content = []
        for similar in similar_content:
            similarity_score = self._calculate_content_similarity(content, similar)
            if similarity_score > 0.3:  # Minimum similarity threshold
                scored_content.append({
                    'content_id': similar.id,
                    'title': similar.title,
                    'summary': similar.summary,
                    'content_type': similar.content_type,
                    'engagement_score': similar.engagement_score,
                    'similarity_score': similarity_score
                })
        
        # Sort by similarity and limit
        scored_content.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_content[:limit]
    
    def get_trending_recommendations(self, content_type: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending content recommendations"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=24)
        
        query = ContentRelationship.query.filter(
            and_(
                ContentRelationship.created_at >= cutoff_date,
                ContentRelationship.status == 'published',
                ContentRelationship.visibility == 'public'
            )
        )
        
        if content_type:
            query = query.filter_by(content_type=content_type)
        
        # Order by trending score
        trending_content = query.order_by(desc(ContentRelationship.trending_score)).limit(limit).all()
        
        recommendations = []
        for content in trending_content:
            recommendations.append({
                'content_id': content.id,
                'title': content.title,
                'summary': content.summary,
                'content_type': content.content_type,
                'engagement_score': content.engagement_score,
                'trending_score': content.trending_score,
                'reason': 'Trending content'
            })
        
        return recommendations
    
    def record_recommendation_interaction(self, user_id: int, content_id: int,
                                         interaction_type: str) -> Dict[str, Any]:
        """Record user interaction with recommendation"""
        recommendation = ContentRecommendation.query.filter_by(
            user_id=user_id,
            content_id=content_id
        ).first()
        
        if not recommendation:
            return {'success': False, 'error': 'Recommendation not found'}
        
        # Record interaction
        if interaction_type == 'click':
            recommendation.record_click()
        elif interaction_type == 'view':
            recommendation.record_view()
        elif interaction_type == 'dismiss':
            recommendation.record_dismissal()
        elif interaction_type == 'feedback':
            # Would handle feedback scoring
            pass
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Interaction recorded successfully'
        }
    
    def update_recommendation_performance(self):
        """Update recommendation performance metrics"""
        # Calculate click-through rates for recommendations
        recommendations = ContentRecommendation.query.all()
        
        for recommendation in recommendations:
            if recommendation.position:
                # Calculate CTR based on position (simplified)
                base_ctr = 0.05  # 5% base CTR
                position_factor = max(0.1, 1.0 / recommendation.position)
                expected_ctr = base_ctr * position_factor
                
                if recommendation.viewed:
                    actual_ctr = 1.0 if recommendation.clicked else 0.0
                    recommendation.click_through_rate = actual_ctr
        
        db.session.commit()
        
        return len(recommendations)
    
    def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences and reading history"""
        # This is a simplified implementation
        # In a real system, you'd analyze user's reading history and behavior
        
        preferences = {
            'content_types': ['post', 'article'],  # Default preferences
            'categories': [],  # Would be calculated from user's reading history
            'tags': [],  # Would be calculated from user's reading history
            'engagement_patterns': {
                'preferred_length': 'medium',
                'reading_time_preference': 5,  # minutes
                'interaction_frequency': 'medium'
            }
        }
        
        return preferences
    
    def _get_content_candidates(self, user_id: int, content_type: str = None) -> List[ContentRelationship]:
        """Get content candidates for recommendations"""
        query = ContentRelationship.query.filter(
            and_(
                ContentRelationship.status == 'published',
                ContentRelationship.visibility == 'public'
            )
        )
        
        # Filter by content type
        if content_type:
            query = query.filter_by(content_type=content_type)
        
        # Exclude content user has already interacted with
        # This would require additional tracking data
        
        candidates = query.order_by(ContentRelationship.engagement_score.desc()).limit(100).all()
        
        return candidates
    
    def _calculate_recommendation_score(self, user_id: int, content: ContentRelationship,
                                        user_preferences: Dict[str, Any]) -> float:
        """Calculate recommendation score for content"""
        score = 0.0
        
        # Base score from content quality
        score += content.content_score * 0.3
        
        # Engagement score
        score += content.engagement_score * 0.2
        
        # Recency score (prefer newer content)
        days_since_creation = (datetime.now(timezone.utc) - content.created_at).days
        recency_score = max(0.1, 1.0 - (days_since_creation / 365))
        score += recency_score * 0.1
        
        # Content type preference
        if content.content_type in user_preferences['content_types']:
            score += 0.2
        
        # Length preference
        content_length = len(content.content) if content.content else 0
        if user_preferences['engagement_patterns']['preferred_length'] == 'short' and content_length < 500:
            score += 0.1
        elif user_preferences['engagement_patterns']['preferred_length'] == 'long' and content_length > 2000:
            score += 0.1
        
        # Add some randomness to promote diversity
        import random
        score += random.random() * 0.1
        
        return min(1.0, score)
    
    def _generate_recommendation_reason(self, user_id: int, content: ContentRelationship,
                                       score: float) -> str:
        """Generate reason for recommendation"""
        reasons = []
        
        if score > 0.8:
            reasons.append("Highly recommended content")
        elif content.engagement_score > 0.7:
            reasons.append("Popular content")
        elif content.is_featured:
            reasons.append("Featured content")
        elif content.trending_score > 0.5:
            reasons.append("Trending content")
        else:
            reasons.append("Recommended for you")
        
        return ", ".join(reasons)
    
    def _store_recommendations(self, user_id: int, recommendations: List[Dict[str, Any]]):
        """Store recommendations in database"""
        for i, rec in enumerate(recommendations):
            # Check if recommendation already exists
            existing = ContentRecommendation.query.filter_by(
                user_id=user_id,
                content_id=rec['content_id']
            ).first()
            
            if not existing:
                recommendation = ContentRecommendation(
                    user_id=user_id,
                    content_id=rec['content_id'],
                    recommendation_type='personalized',
                    score=rec['recommendation_score'],
                    reason=rec['reason'],
                    position=i + 1
                )
                db.session.add(recommendation)
        
        db.session.commit()
    
    def _calculate_content_similarity(self, content1: ContentRelationship,
                                      content2: ContentRelationship) -> float:
        """Calculate similarity between two content items"""
        similarity = 0.0
        
        # Tag similarity
        tags1 = set(tag.name for tag in content1.tags)
        tags2 = set(tag.name for tag in content2.tags)
        
        if tags1 and tags2:
            intersection = len(tags1.intersection(tags2))
            union = len(tags1.union(tags2))
            tag_similarity = intersection / union if union > 0 else 0
            similarity += tag_similarity * 0.4
        
        # Category similarity
        categories1 = set(cat.id for cat in content1.categories)
        categories2 = set(cat.id for cat in content2.categories)
        
        if categories1 and categories2:
            intersection = len(categories1.intersection(categories2))
            union = len(categories1.union(categories2))
            category_similarity = intersection / union if union > 0 else 0
            similarity += category_similarity * 0.3
        
        # Content type similarity
        if content1.content_type == content2.content_type:
            similarity += 0.2
        
        # Author similarity (if same author)
        if content1.author_id == content2.author_id:
            similarity += 0.1
        
        return min(1.0, similarity)
