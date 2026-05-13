"""
Advanced Notification Filtering and Grouping Service

This module provides comprehensive filtering and grouping capabilities
for notifications, including advanced filters, smart grouping, and
integrated search functionality.
"""

from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import and_, or_, desc, asc, func
from typing import Dict, List, Optional, Tuple, Any

from app.models import User
from .models import AdminNotification
from .translation_service import notification_translation_service


class NotificationFilteringService:
    """Service for advanced notification filtering and grouping"""
    
    def __init__(self):
        self.supported_filters = {
            'basic': ['type', 'priority', 'is_read', 'is_archived'],
            'advanced': ['date_range', 'content_search', 'source', 'category'],
            'smart': ['sentiment', 'importance', 'frequency', 'engagement']
        }
        
        self.grouping_strategies = {
            'type': 'Group by notification type',
            'priority': 'Group by priority level',
            'source': 'Group by source',
            'date': 'Group by date/time',
            'content': 'Group by content similarity',
            'smart': 'Smart grouping (AI-powered)'
        }
        
        self.filter_presets = {
            'unread_important': {
                'name': 'Unread Important',
                'filters': {
                    'is_read': False,
                    'priority': ['high', 'urgent']
                },
                'sort': ['priority', 'created_at']
            },
            'recent_comments': {
                'name': 'Recent Comments',
                'filters': {
                    'type': 'comment',
                    'date_range': 'last_7_days'
                },
                'sort': ['created_at']
            },
            'system_alerts': {
                'name': 'System Alerts',
                'filters': {
                    'type': 'system',
                    'priority': ['high', 'urgent']
                },
                'sort': ['priority', 'created_at']
            },
            'security_notifications': {
                'name': 'Security Notifications',
                'filters': {
                    'type': 'security'
                },
                'sort': ['created_at']
            },
            'moderation_actions': {
                'name': 'Moderation Actions',
                'filters': {
                    'type': 'moderation'
                },
                'sort': ['created_at']
            }
        }
    
    def apply_filters(self, user_id: int, filters: Dict, sort_options: Dict = None) -> List[AdminNotification]:
        """Apply comprehensive filters to notifications"""
        try:
            query = AdminNotification.query.filter_by(user_id=user_id)
            
            # Apply basic filters
            query = self._apply_basic_filters(query, filters)
            
            # Apply advanced filters
            query = self._apply_advanced_filters(query, filters)
            
            # Apply smart filters
            query = self._apply_smart_filters(query, filters, user_id)
            
            # Apply sorting
            query = self._apply_sorting(query, sort_options or {})
            
            # Apply pagination
            limit = filters.get('limit', 50)
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except Exception as e:
            current_app.logger.error(f"Filter application error: {str(e)}")
            return []
    
    def _apply_basic_filters(self, query, filters: Dict):
        """Apply basic filters to query"""
        
        # Filter by type
        if 'type' in filters:
            if isinstance(filters['type'], list):
                query = query.filter(AdminNotification.notification_type.in_(filters['type']))
            else:
                query = query.filter(AdminNotification.notification_type == filters['type'])
        
        # Filter by priority
        if 'priority' in filters:
            if isinstance(filters['priority'], list):
                query = query.filter(AdminNotification.priority.in_(filters['priority']))
            else:
                query = query.filter(AdminNotification.priority == filters['priority'])
        
        # Filter by read status
        if 'is_read' in filters:
            query = query.filter(AdminNotification.is_read == filters['is_read'])
        
        # Filter by archived status
        if 'is_archived' in filters:
            query = query.filter(AdminNotification.is_archived == filters['is_archived'])
        
        return query
    
    def _apply_advanced_filters(self, query, filters: Dict):
        """Apply advanced filters to query"""
        
        # Date range filter
        if 'date_range' in filters:
            date_range = filters['date_range']
            now = datetime.utcnow()
            
            if date_range == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(AdminNotification.created_at >= start_date)
            elif date_range == 'yesterday':
                yesterday = now - timedelta(days=1)
                start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                query = query.filter(AdminNotification.created_at.between(start_date, end_date))
            elif date_range == 'last_7_days':
                start_date = now - timedelta(days=7)
                query = query.filter(AdminNotification.created_at >= start_date)
            elif date_range == 'last_30_days':
                start_date = now - timedelta(days=30)
                query = query.filter(AdminNotification.created_at >= start_date)
            elif date_range == 'last_90_days':
                start_date = now - timedelta(days=90)
                query = query.filter(AdminNotification.created_at >= start_date)
            elif date_range == 'this_year':
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(AdminNotification.created_at >= start_date)
            elif date_range == 'custom':
                if 'start_date' in filters:
                    start_date = datetime.fromisoformat(filters['start_date'])
                    query = query.filter(AdminNotification.created_at >= start_date)
                if 'end_date' in filters:
                    end_date = datetime.fromisoformat(filters['end_date'])
                    query = query.filter(AdminNotification.created_at <= end_date)
        
        # Content search filter
        if 'content_search' in filters:
            search_term = f"%{filters['content_search']}%"
            query = query.filter(or_(
                AdminNotification.title.ilike(search_term),
                AdminNotification.message.ilike(search_term)
            ))
        
        # Source filter
        if 'source' in filters:
            if hasattr(AdminNotification, 'source'):
                query = query.filter(AdminNotification.source == filters['source'])
        
        # Category filter
        if 'category' in filters:
            if hasattr(AdminNotification, 'category'):
                query = query.filter(AdminNotification.category == filters['category'])
        
        return query
    
    def _apply_smart_filters(self, query, filters: Dict, user_id: int):
        """Apply smart/AI-powered filters to query"""
        
        # Sentiment filter
        if 'sentiment' in filters:
            # This would integrate with an AI sentiment analysis service
            # For now, we'll use basic keyword-based sentiment detection
            sentiment = filters['sentiment']
            
            if sentiment == 'positive':
                positive_keywords = ['approved', 'success', 'completed', 'welcome', 'congratulations']
                conditions = []
                for keyword in positive_keywords:
                    conditions.append(AdminNotification.message.ilike(f'%{keyword}%'))
                if conditions:
                    query = query.filter(or_(*conditions))
            elif sentiment == 'negative':
                negative_keywords = ['failed', 'error', 'rejected', 'deleted', 'warning', 'alert']
                conditions = []
                for keyword in negative_keywords:
                    conditions.append(AdminNotification.message.ilike(f'%{keyword}%'))
                if conditions:
                    query = query.filter(or_(*conditions))
            elif sentiment == 'neutral':
                # Exclude positive and negative keywords
                all_keywords = ['approved', 'success', 'completed', 'welcome', 'congratulations',
                               'failed', 'error', 'rejected', 'deleted', 'warning', 'alert']
                conditions = []
                for keyword in all_keywords:
                    conditions.append(AdminNotification.message.notilike(f'%{keyword}%'))
                if conditions:
                    query = query.filter(and_(*conditions))
        
        # Importance filter
        if 'importance' in filters:
            importance = filters['importance']
            
            if importance == 'high':
                # High importance = urgent priority or security/system type
                query = query.filter(or_(
                    AdminNotification.priority == 'urgent',
                    AdminNotification.notification_type.in_(['security', 'system'])
                ))
            elif importance == 'medium':
                # Medium importance = high priority or important types
                query = query.filter(and_(
                    AdminNotification.priority != 'urgent',
                    or_(
                        AdminNotification.priority == 'high',
                        AdminNotification.notification_type.in_(['moderation', 'admin'])
                    )
                ))
            elif importance == 'low':
                # Low importance = low/medium priority and regular types
                query = query.filter(and_(
                    AdminNotification.priority.in_(['low', 'medium']),
                    AdminNotification.notification_type.in_(['comment', 'message'])
                ))
        
        # Engagement filter
        if 'engagement' in filters:
            engagement = filters['engagement']
            
            if engagement == 'high':
                # High engagement = notifications that have been read quickly
                # This would require tracking read times
                pass  # Placeholder for future implementation
            elif engagement == 'low':
                # Low engagement = unread notifications
                query = query.filter(AdminNotification.is_read == False)
        
        return query
    
    def _apply_sorting(self, query, sort_options: Dict):
        """Apply sorting to query"""
        
        sort_by = sort_options.get('sort_by', 'created_at')
        sort_order = sort_options.get('sort_order', 'desc')
        
        if sort_by == 'created_at':
            if sort_order == 'desc':
                query = query.order_by(desc(AdminNotification.created_at))
            else:
                query = query.order_by(asc(AdminNotification.created_at))
        elif sort_by == 'priority':
            if sort_order == 'desc':
                query = query.order_by(desc(AdminNotification.priority))
            else:
                query = query.order_by(asc(AdminNotification.priority))
        elif sort_by == 'type':
            if sort_order == 'desc':
                query = query.order_by(desc(AdminNotification.notification_type))
            else:
                query = query.order_by(asc(AdminNotification.notification_type))
        elif sort_by == 'read_status':
            query = query.order_by(AdminNotification.is_read.desc(), desc(AdminNotification.created_at))
        
        return query
    
    def group_notifications(self, notifications: List[AdminNotification], strategy: str = 'type', 
                          user_preferences: Dict = None) -> List[Dict]:
        """Group notifications using specified strategy"""
        
        if strategy not in self.grouping_strategies:
            strategy = 'type'
        
        if strategy == 'type':
            return self._group_by_type(notifications)
        elif strategy == 'priority':
            return self._group_by_priority(notifications)
        elif strategy == 'source':
            return self._group_by_source(notifications)
        elif strategy == 'date':
            return self._group_by_date(notifications)
        elif strategy == 'content':
            return self._group_by_content_similarity(notifications)
        elif strategy == 'smart':
            return self._smart_group(notifications, user_preferences)
        
        return self._group_by_type(notifications)
    
    def _group_by_type(self, notifications: List[AdminNotification]) -> List[Dict]:
        """Group notifications by type"""
        groups = {}
        
        for notification in notifications:
            notification_type = notification.notification_type or 'system'
            
            if notification_type not in groups:
                groups[notification_type] = {
                    'group_key': notification_type,
                    'group_name': notification_type.title(),
                    'group_type': 'type',
                    'notifications': [],
                    'count': 0,
                    'created_at': notification.created_at
                }
            
            groups[notification_type]['notifications'].append(notification)
            groups[notification_type]['count'] += 1
        
        return list(groups.values())
    
    def _group_by_priority(self, notifications: List[AdminNotification]) -> List[Dict]:
        """Group notifications by priority"""
        groups = {}
        
        for notification in notifications:
            priority = notification.priority or 'medium'
            
            if priority not in groups:
                groups[priority] = {
                    'group_key': priority,
                    'group_name': f'{priority.title()} Priority',
                    'group_type': 'priority',
                    'notifications': [],
                    'count': 0,
                    'created_at': notification.created_at
                }
            
            groups[priority]['notifications'].append(notification)
            groups[priority]['count'] += 1
        
        return list(groups.values())
    
    def _group_by_source(self, notifications: List[AdminNotification]) -> List[Dict]:
        """Group notifications by source"""
        groups = {}
        
        for notification in notifications:
            source = getattr(notification, 'source', 'system')
            
            if source not in groups:
                groups[source] = {
                    'group_key': source,
                    'group_name': f'From {source.title()}',
                    'group_type': 'source',
                    'notifications': [],
                    'count': 0,
                    'created_at': notification.created_at
                }
            
            groups[source]['notifications'].append(notification)
            groups[source]['count'] += 1
        
        return list(groups.values())
    
    def _group_by_date(self, notifications: List[AdminNotification]) -> List[Dict]:
        """Group notifications by date"""
        groups = {}
        
        for notification in notifications:
            # Group by day
            date_key = notification.created_at.date().isoformat()
            
            if date_key not in groups:
                groups[date_key] = {
                    'group_key': date_key,
                    'group_name': self._format_date_group(notification.created_at),
                    'group_type': 'date',
                    'notifications': [],
                    'count': 0,
                    'created_at': notification.created_at
                }
            
            groups[date_key]['notifications'].append(notification)
            groups[date_key]['count'] += 1
        
        return list(groups.values())
    
    def _group_by_content_similarity(self, notifications: List[AdminNotification]) -> List[Dict]:
        """Group notifications by content similarity"""
        groups = []
        processed = set()
        
        for i, notification in enumerate(notifications):
            if notification.id in processed:
                continue
            
            similar_notifications = [notification]
            processed.add(notification.id)
            
            # Find similar notifications
            for j, other_notification in enumerate(notifications):
                if i != j and other_notification.id not in processed:
                    similarity = self._calculate_content_similarity(
                        notification.message, 
                        other_notification.message
                    )
                    
                    if similarity >= 0.7:  # 70% similarity threshold
                        similar_notifications.append(other_notification)
                        processed.add(other_notification.id)
            
            if len(similar_notifications) > 1:
                groups.append({
                    'group_key': f'similar_{len(groups)}',
                    'group_name': f'Similar Content ({len(similar_notifications)} items)',
                    'group_type': 'content_similarity',
                    'notifications': similar_notifications,
                    'count': len(similar_notifications),
                    'created_at': notification.created_at
                })
            else:
                # Individual notification
                groups.append({
                    'group_key': f'individual_{notification.id}',
                    'group_name': 'Individual',
                    'group_type': 'individual',
                    'notifications': [notification],
                    'count': 1,
                    'created_at': notification.created_at
                })
        
        return groups
    
    def _smart_group(self, notifications: List[AdminNotification], user_preferences: Dict = None) -> List[Dict]:
        """Smart grouping using multiple strategies"""
        if not user_preferences:
            user_preferences = {}
        
        # Determine best grouping strategy based on user preferences and notification characteristics
        strategy = user_preferences.get('preferred_grouping', 'type')
        
        # If user has no preference, choose based on notification count and types
        if not user_preferences:
            types = set(n.notification_type for n in notifications)
            if len(types) == 1 and len(notifications) > 5:
                strategy = 'content'  # Group by content if many notifications of same type
            elif len(notifications) > 10:
                strategy = 'priority'  # Group by priority for large lists
            else:
                strategy = 'type'  # Default to type grouping
        
        return self.group_notifications(notifications, strategy, user_preferences)
    
    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        try:
            # Simple word-based similarity calculation
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
        except Exception:
            return 0.0
    
    def _format_date_group(self, date: datetime) -> str:
        """Format date for grouping display"""
        now = datetime.utcnow()
        today = now.date()
        notification_date = date.date()
        
        if notification_date == today:
            return 'Today'
        elif notification_date == today - timedelta(days=1):
            return 'Yesterday'
        elif notification_date >= today - timedelta(days=7):
            return 'This Week'
        elif notification_date >= today - timedelta(days=30):
            return 'This Month'
        else:
            return date.strftime('%B %Y')
    
    def get_filter_presets(self) -> Dict:
        """Get available filter presets"""
        return self.filter_presets.copy()
    
    def get_grouping_strategies(self) -> Dict:
        """Get available grouping strategies"""
        return self.grouping_strategies.copy()
    
    def create_custom_filter(self, user_id: int, name: str, filters: Dict, 
                            sort_options: Dict = None) -> Dict:
        """Create a custom filter preset"""
        try:
            # This would typically save to a database
            # For now, return the filter configuration
            custom_filter = {
                'id': f'custom_{user_id}_{datetime.utcnow().timestamp()}',
                'name': name,
                'user_id': user_id,
                'filters': filters,
                'sort_options': sort_options or {},
                'created_at': datetime.utcnow().isoformat(),
                'is_custom': True
            }
            
            return custom_filter
        except Exception as e:
            current_app.logger.error(f"Error creating custom filter: {str(e)}")
            return {}
    
    def analyze_notification_patterns(self, user_id: int, days: int = 30) -> Dict:
        """Analyze notification patterns for insights"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            notifications = AdminNotification.query.filter(
                AdminNotification.user_id == user_id,
                AdminNotification.created_at >= start_date
            ).all()
            
            if not notifications:
                return {'message': 'No notifications to analyze'}
            
            # Type distribution
            type_counts = {}
            priority_counts = {}
            daily_counts = {}
            
            for notification in notifications:
                # Type distribution
                notification_type = notification.notification_type or 'system'
                type_counts[notification_type] = type_counts.get(notification_type, 0) + 1
                
                # Priority distribution
                priority = notification.priority or 'medium'
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
                
                # Daily distribution
                date_key = notification.created_at.date().isoformat()
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
            
            # Calculate patterns
            total_notifications = len(notifications)
            most_common_type = max(type_counts.items(), key=lambda x: x[1]) if type_counts else ('system', 0)
            most_common_priority = max(priority_counts.items(), key=lambda x: x[1]) if priority_counts else ('medium', 0)
            
            # Peak activity day
            peak_day = max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else (None, 0)
            
            return {
                'period_days': days,
                'total_notifications': total_notifications,
                'average_per_day': total_notifications / days,
                'type_distribution': type_counts,
                'priority_distribution': priority_counts,
                'daily_distribution': daily_counts,
                'most_common_type': most_common_type,
                'most_common_priority': most_common_priority,
                'peak_activity_day': peak_day,
                'insights': self._generate_insights(type_counts, priority_counts, daily_counts)
            }
            
        except Exception as e:
            current_app.logger.error(f"Error analyzing patterns: {str(e)}")
            return {'error': str(e)}
    
    def _generate_insights(self, type_counts: Dict, priority_counts: Dict, daily_counts: Dict) -> List[str]:
        """Generate insights from notification data"""
        insights = []
        
        # Type insights
        if type_counts:
            total_type_notifications = sum(type_counts.values())
            for notification_type, count in type_counts.items():
                percentage = (count / total_type_notifications) * 100
                if percentage > 50:
                    insights.append(f"You receive {percentage:.1f}% {notification_type} notifications")
        
        # Priority insights
        urgent_count = priority_counts.get('urgent', 0)
        if urgent_count > 0:
            insights.append(f"You received {urgent_count} urgent notifications")
        
        # Activity insights
        if len(daily_counts) > 1:
            daily_values = list(daily_counts.values())
            avg_daily = sum(daily_values) / len(daily_values)
            max_daily = max(daily_values)
            
            if max_daily > avg_daily * 2:
                insights.append("You have some very busy notification days")
        
        return insights


# Singleton instance
notification_filtering_service = NotificationFilteringService()
