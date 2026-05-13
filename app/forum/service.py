"""
Forum Service Layer
Auto Bot Solutions Forum

This module provides business logic for forum operations including
post management, comment handling, and forum analytics.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import joinedload
from app import db
from app.models import User, Post, Comment, Category, Repository, AuditLog


class ForumService:
    """Service for managing forum operations and business logic"""
    
    def __init__(self):
        self.default_post_status = 'published'
        self.max_post_length = 50000
        self.max_comment_length = 10000
        self.audit_enabled = True
    
    def create_post(self, user_id: int, title: str, content: str, 
                   category_id: Optional[int] = None, repository_id: Optional[int] = None,
                   tags: Optional[List[str]] = None) -> Optional[Post]:
        """Create a new forum post"""
        try:
            post = Post(
                title=title,
                content=content,
                user_id=user_id,
                category_id=category_id,
                repository_id=repository_id
            )
            
            db.session.add(post)
            db.session.flush()
            
            # Log creation
            if self.audit_enabled:
                AuditLog.log_action(
                    user_id=user_id,
                    action='create_post',
                    target_type='post',
                    target_id=post.id,
                    new_values={'title': title, 'content': content[:100]}
                )
            
            db.session.commit()
            return post
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update_post(self, post_id: int, user_id: int, title: str = None, 
                   content: str = None, category_id: int = None) -> Optional[Post]:
        """Update an existing forum post"""
        try:
            post = Post.query.filter_by(id=post_id, user_id=user_id).first()
            if not post:
                return None
            
            # Store old values for audit
            old_values = {
                'title': post.title,
                'content': post.content,
                'category_id': post.category_id
            }
            
            # Update fields
            if title is not None:
                post.title = title
            if content is not None:
                post.content = content
            if category_id is not None:
                post.category_id = category_id
            
            post.updated_at = datetime.utcnow()
            
            # Log update
            if self.audit_enabled:
                new_values = {
                    'title': post.title,
                    'content': post.content,
                    'category_id': post.category_id
                }
                AuditLog.log_action(
                    user_id=user_id,
                    action='edit_post',
                    target_type='post',
                    target_id=post.id,
                    old_values=old_values,
                    new_values=new_values
                )
            
            db.session.commit()
            return post
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete_post(self, post_id: int, user_id: int) -> bool:
        """Delete a forum post"""
        try:
            post = Post.query.filter_by(id=post_id, user_id=user_id).first()
            if not post:
                return False
            
            # Store old values for audit
            old_values = {
                'title': post.title,
                'content': post.content,
                'category_id': post.category_id
            }
            
            # Delete post (cascade will handle comments)
            db.session.delete(post)
            
            # Log deletion
            if self.audit_enabled:
                AuditLog.log_action(
                    user_id=user_id,
                    action='delete_post',
                    target_type='post',
                    target_id=post_id,
                    old_values=old_values
                )
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def create_comment(self, user_id: int, post_id: int, content: str) -> Optional[Comment]:
        """Create a new comment on a post"""
        try:
            comment = Comment(
                content=content,
                user_id=user_id,
                post_id=post_id
            )
            
            db.session.add(comment)
            db.session.flush()
            
            # Log creation
            if self.audit_enabled:
                AuditLog.log_action(
                    user_id=user_id,
                    action='create_comment',
                    target_type='comment',
                    target_id=comment.id,
                    new_values={'content': content[:100]}
                )
            
            db.session.commit()
            return comment
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update_comment(self, comment_id: int, user_id: int, content: str) -> Optional[Comment]:
        """Update an existing comment"""
        try:
            comment = Comment.query.filter_by(id=comment_id, user_id=user_id).first()
            if not comment:
                return None
            
            # Store old values for audit
            old_values = {'content': comment.content}
            
            # Update content
            comment.content = content
            comment.updated_at = datetime.utcnow()
            
            # Log update
            if self.audit_enabled:
                AuditLog.log_action(
                    user_id=user_id,
                    action='edit_comment',
                    target_type='comment',
                    target_id=comment.id,
                    old_values=old_values,
                    new_values={'content': content}
                )
            
            db.session.commit()
            return comment
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete_comment(self, comment_id: int, user_id: int) -> bool:
        """Delete a comment"""
        try:
            comment = Comment.query.filter_by(id=comment_id, user_id=user_id).first()
            if not comment:
                return False
            
            # Store old values for audit
            old_values = {'content': comment.content}
            
            # Delete comment
            db.session.delete(comment)
            
            # Log deletion
            if self.audit_enabled:
                AuditLog.log_action(
                    user_id=user_id,
                    action='delete_comment',
                    target_type='comment',
                    target_id=comment_id,
                    old_values=old_values
                )
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_posts(self, category_id: Optional[int] = None, 
                  page: int = 1, per_page: int = 20) -> List[Post]:
        """Get forum posts with pagination"""
        query = Post.query
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        return query.order_by(Post.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    def get_post(self, post_id: int) -> Optional[Post]:
        """Get a specific post with comments"""
        return Post.query.options(
            joinedload(Post.comments)
        ).filter_by(id=post_id).first()
    
    def get_user_posts(self, user_id: int, page: int = 1, per_page: int = 20) -> List[Post]:
        """Get posts by a specific user"""
        return Post.query.filter_by(user_id=user_id).order_by(
            Post.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
    
    def search_posts(self, query: str, page: int = 1, per_page: int = 20) -> List[Post]:
        """Search posts by title or content"""
        search_filter = or_(
            Post.title.ilike(f'%{query}%'),
            Post.content.ilike(f'%{query}%')
        )
        
        return Post.query.filter(search_filter).order_by(
            Post.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
    
    def get_popular_posts(self, limit: int = 10) -> List[Post]:
        """Get popular posts based on views and engagement"""
        return Post.query.order_by(
            desc(Post.upvotes + Post.downvotes + Post.view_count)
        ).limit(limit).all()
    
    def get_recent_posts(self, limit: int = 10) -> List[Post]:
        """Get recent posts"""
        return Post.query.order_by(
            desc(Post.created_at)
        ).limit(limit).all()
    
    def moderate_post(self, post_id: int, moderator_id: int, 
                     action: str, reason: str = None) -> bool:
        """Moderate a post (approve, delete, flag)"""
        try:
            post = Post.query.get(post_id)
            if not post:
                return False
            
            old_values = {
                'moderation_status': post.moderation_status,
                'is_flagged': post.is_flagged
            }
            
            if action == 'approve':
                post.moderation_status = 'approved'
                post.is_flagged = False
            elif action == 'delete':
                post.moderation_status = 'deleted'
            elif action == 'flag':
                post.moderation_status = 'flagged'
                post.is_flagged = True
                post.flagged_by = moderator_id
                post.flagged_at = datetime.utcnow()
                post.moderation_reason = reason
            
            new_values = {
                'moderation_status': post.moderation_status,
                'is_flagged': post.is_flagged
            }
            
            # Log moderation action
            if self.audit_enabled:
                AuditLog.log_action(
                    user_id=moderator_id,
                    action=f'moderate_post_{action}',
                    target_type='post',
                    target_id=post_id,
                    old_values=old_values,
                    new_values=new_values
                )
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_flagged_posts(self, page: int = 1, per_page: int = 20) -> List[Post]:
        """Get flagged posts for moderation"""
        return Post.query.filter_by(is_flagged=True).order_by(
            desc(Post.flagged_at)
        ).paginate(page=page, per_page=per_page, error_out=False)
    
    def get_forum_stats(self) -> Dict[str, Any]:
        """Get forum statistics"""
        return {
            'total_posts': Post.query.count(),
            'total_comments': Comment.query.count(),
            'total_users': User.query.count(),
            'flagged_posts': Post.query.filter_by(is_flagged=True).count(),
            'recent_posts': Post.query.filter(
                Post.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
        }
