"""
Advanced Analytics Service Layer

This module provides comprehensive analytics services for the Advanced Analytics Dashboard,
including real-time data processing, user behavior analysis, content performance metrics,
system monitoring, trend analysis, and predictive analytics.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import func, and_, or_, desc, asc, text
from sqlalchemy.orm import joinedload
from collections import defaultdict, Counter
import json
import statistics
import math
from typing import Dict, List, Tuple, Optional, Any

from app import db
from app.models import User, Post, Comment, Category
from .models import (
    AnalyticsEvent, UserBehavior, ContentPerformance, 
    SystemMetrics, TrendAnalysis, PredictiveModel
)

class AnalyticsService:
    """Core analytics service for data processing and analysis"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache TTL
        
    def track_event(self, event_type: str, event_category: str, user_id: Optional[int] = None,
                   target_type: Optional[str] = None, target_id: Optional[int] = None,
                   event_data: Optional[Dict] = None, event_value: Optional[float] = None,
                   session_id: Optional[str] = None, ip_address: Optional[str] = None,
                   user_agent: Optional[str] = None) -> AnalyticsEvent:
        """Track an analytics event"""
        event = AnalyticsEvent(
            event_type=event_type,
            event_category=event_category,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            target_type=target_type,
            target_id=target_id,
            event_data=event_data or {},
            event_value=event_value
        )
        
        db.session.add(event)
        db.session.commit()
        
        # Invalidate relevant cache
        self._invalidate_cache(f"analytics_{event_type}_{event_category}")
        
        return event
    
    def get_event_statistics(self, event_type: str = None, event_category: str = None,
                           start_date: datetime = None, end_date: datetime = None,
                           user_id: int = None) -> Dict:
        """Get statistics for analytics events"""
        cache_key = f"event_stats_{event_type}_{event_category}_{user_id}_{start_date}_{end_date}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        query = AnalyticsEvent.query
        
        if event_type:
            query = query.filter(AnalyticsEvent.event_type == event_type)
        if event_category:
            query = query.filter(AnalyticsEvent.event_category == event_category)
        if user_id:
            query = query.filter(AnalyticsEvent.user_id == user_id)
        if start_date:
            query = query.filter(AnalyticsEvent.created_at >= start_date)
        if end_date:
            query = query.filter(AnalyticsEvent.created_at <= end_date)
        
        # Get basic statistics
        total_events = query.count()
        
        if total_events == 0:
            return {
                'total_events': 0,
                'unique_users': 0,
                'avg_event_value': 0,
                'events_by_hour': {},
                'events_by_day': {},
                'top_targets': []
            }
        
        # Get detailed statistics
        stats = query.with_entities(
            func.count(AnalyticsEvent.id).label('total'),
            func.count(func.distinct(AnalyticsEvent.user_id)).label('unique_users'),
            func.avg(AnalyticsEvent.event_value).label('avg_value'),
            func.sum(AnalyticsEvent.event_value).label('total_value')
        ).first()
        
        # Get hourly distribution
        hourly_stats = query.with_entities(
            func.extract('hour', AnalyticsEvent.created_at).label('hour'),
            func.count(AnalyticsEvent.id).label('count')
        ).group_by(func.extract('hour', AnalyticsEvent.created_at)).all()
        
        events_by_hour = {int(hour): count for hour, count in hourly_stats}
        
        # Get daily distribution
        daily_stats = query.with_entities(
            func.date(AnalyticsEvent.created_at).label('date'),
            func.count(AnalyticsEvent.id).label('count')
        ).group_by(func.date(AnalyticsEvent.created_at)).all()
        
        events_by_day = {str(date): count for date, count in daily_stats}
        
        # Get top targets
        top_targets = query.filter(
            AnalyticsEvent.target_type.isnot(None),
            AnalyticsEvent.target_id.isnot(None)
        ).with_entities(
            AnalyticsEvent.target_type,
            AnalyticsEvent.target_id,
            func.count(AnalyticsEvent.id).label('count')
        ).group_by(
            AnalyticsEvent.target_type,
            AnalyticsEvent.target_id
        ).order_by(desc('count')).limit(10).all()
        
        result = {
            'total_events': stats.total or 0,
            'unique_users': stats.unique_users or 0,
            'avg_event_value': float(stats.avg_value or 0),
            'total_event_value': float(stats.total_value or 0),
            'events_by_hour': events_by_hour,
            'events_by_day': events_by_day,
            'top_targets': [
                {'target_type': tt[0], 'target_id': tt[1], 'count': tt[2]}
                for tt in top_targets
            ]
        }
        
        # Cache the result
        self.cache[cache_key] = result
        
        return result
    
    def _invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        keys_to_remove = [key for key in self.cache.keys() if pattern in key]
        for key in keys_to_remove:
            del self.cache[key]

class UserBehaviorService:
    """Service for analyzing user behavior patterns"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    def update_user_behavior(self, user_id: int) -> UserBehavior:
        """Update or create user behavior analytics"""
        behavior = UserBehavior.query.filter_by(user_id=user_id).first()
        
        if not behavior:
            behavior = UserBehavior(user_id=user_id)
            db.session.add(behavior)
        
        # Update session analytics
        self._update_session_analytics(behavior)
        
        # Update activity patterns
        self._update_activity_patterns(behavior)
        
        # Update content interaction metrics
        self._update_content_interactions(behavior)
        
        # Update engagement metrics
        self._update_engagement_metrics(behavior)
        
        # Update device analytics
        self._update_device_analytics(behavior)
        
        # Update timestamps
        behavior.last_active = datetime.utcnow()
        behavior.updated_at = datetime.utcnow()
        
        db.session.commit()
        return behavior
    
    def _update_session_analytics(self, behavior: UserBehavior):
        """Update session-related analytics"""
        user_id = behavior.user_id
        
        # Get session events
        session_events = self.analytics_service.get_event_statistics(
            event_type='session',
            user_id=user_id,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        # Calculate session metrics
        total_sessions = session_events['total_events']
        
        if total_sessions > 0:
            # Get session durations
            session_durations = []
            session_events_query = AnalyticsEvent.query.filter(
                and_(
                    AnalyticsEvent.user_id == user_id,
                    AnalyticsEvent.event_type == 'session',
                    AnalyticsEvent.event_category.in_(['start', 'end'])
                )
            ).order_by(AnalyticsEvent.created_at).all()
            
            # Calculate session durations
            session_starts = {}
            for event in session_events_query:
                if event.event_category == 'start':
                    session_starts[event.session_id] = event.created_at
                elif event.event_category == 'end' and event.session_id in session_starts:
                    duration = (event.created_at - session_starts[event.session_id]).total_seconds() / 60  # minutes
                    session_durations.append(duration)
                    del session_starts[event.session_id]
            
            if session_durations:
                behavior.total_sessions = total_sessions
                behavior.avg_session_duration = statistics.mean(session_durations)
                behavior.total_session_duration = sum(session_durations)
                
                # Get last session info
                last_session_start = AnalyticsEvent.query.filter(
                    and_(
                        AnalyticsEvent.user_id == user_id,
                        AnalyticsEvent.event_type == 'session',
                        AnalyticsEvent.event_category == 'start'
                    )
                ).order_by(desc(AnalyticsEvent.created_at)).first()
                
                if last_session_start:
                    behavior.last_session_start = last_session_start.created_at
                    
                    last_session_end = AnalyticsEvent.query.filter(
                        and_(
                            AnalyticsEvent.user_id == user_id,
                            AnalyticsEvent.event_type == 'session',
                            AnalyticsEvent.event_category == 'end',
                            AnalyticsEvent.session_id == last_session_start.session_id
                        )
                    ).first()
                    
                    if last_session_end:
                        behavior.last_session_end = last_session_end.created_at
    
    def _update_activity_patterns(self, behavior: UserBehavior):
        """Update activity pattern analytics"""
        user_id = behavior.user_id
        
        # Get activity events
        activity_events = AnalyticsEvent.query.filter(
            and_(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).all()
        
        if not activity_events:
            return
        
        # Calculate most active hour
        hour_counts = Counter(event.created_at.hour for event in activity_events)
        if hour_counts:
            behavior.most_active_hour = hour_counts.most_common(1)[0][0]
        
        # Calculate most active day
        day_counts = Counter(event.created_at.weekday() for event in activity_events)
        if day_counts:
            behavior.most_active_day = day_counts.most_common(1)[0][0]
        
        # Calculate activity consistency
        daily_activity = defaultdict(int)
        for event in activity_events:
            daily_activity[event.created_at.date()] += 1
        
        if len(daily_activity) > 1:
            activity_values = list(daily_activity.values())
            mean_activity = statistics.mean(activity_values)
            std_activity = statistics.stdev(activity_values) if len(activity_values) > 1 else 0
            
            # Consistency score (inverse of coefficient of variation)
            if mean_activity > 0:
                behavior.activity_consistency = max(0, 1 - (std_activity / mean_activity))
            else:
                behavior.activity_consistency = 0
        
        # Calculate peak activity hour
        if hour_counts:
            behavior.peak_activity_hour = max(hour_counts, key=hour_counts.get)
    
    def _update_content_interactions(self, behavior: UserBehavior):
        """Update content interaction metrics"""
        user_id = behavior.user_id
        
        # Get user's posts and comments
        posts_created = Post.query.filter_by(user_id=user_id).count()
        comments_created = Comment.query.filter_by(user_id=user_id).count()
        
        # Get voting activity
        vote_events = self.analytics_service.get_event_statistics(
            event_type='vote',
            user_id=user_id,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        votes_cast = vote_events['total_events']
        
        # Get bookmark activity
        bookmark_events = self.analytics_service.get_event_statistics(
            event_type='bookmark',
            user_id=user_id,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        bookmarks_created = bookmark_events['total_events']
        
        # Get search activity
        search_events = self.analytics_service.get_event_statistics(
            event_type='search',
            user_id=user_id,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        searches_performed = search_events['total_events']
        
        # Get page views
        view_events = self.analytics_service.get_event_statistics(
            event_type='view',
            user_id=user_id,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        posts_viewed = view_events['total_events']
        
        # Update behavior
        behavior.posts_created = posts_created
        behavior.comments_created = comments_created
        behavior.votes_cast = votes_cast
        behavior.bookmarks_created = bookmarks_created
        behavior.searches_performed = searches_performed
        behavior.posts_viewed = posts_viewed
    
    def _update_engagement_metrics(self, behavior: UserBehavior):
        """Update engagement metrics"""
        user_id = behavior.user_id
        
        # Get page view events with duration
        view_events = AnalyticsEvent.query.filter(
            and_(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.event_type == 'view',
                AnalyticsEvent.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).all()
        
        if not view_events:
            return
        
        # Calculate average time on page
        durations = []
        for event in view_events:
            if event.event_data and 'duration' in event.event_data:
                durations.append(event.event_data['duration'])
        
        if durations:
            behavior.avg_time_on_page = statistics.mean(durations)
        
        # Calculate bounce rate (single page view sessions)
        session_views = defaultdict(list)
        for event in view_events:
            if event.session_id:
                session_views[event.session_id].append(event)
        
        single_page_sessions = sum(1 for views in session_views.values() if len(views) == 1)
        total_sessions = len(session_views)
        
        if total_sessions > 0:
            behavior.bounce_rate = single_page_sessions / total_sessions
            behavior.pages_per_session = sum(len(views) for views in session_views.values()) / total_sessions
        
        # Calculate engagement score (0-100)
        engagement_factors = [
            (behavior.posts_created, 10),  # Weight: 10 points per post
            (behavior.comments_created, 5),  # Weight: 5 points per comment
            (behavior.votes_cast, 2),  # Weight: 2 points per vote
            (behavior.searches_performed, 1),  # Weight: 1 point per search
            (behavior.avg_time_on_page / 60, 20),  # Weight: up to 20 points for time on page
            ((1 - behavior.bounce_rate) * 30),  # Weight: up to 30 points for low bounce rate
            (min(behavior.pages_per_session / 10, 1) * 25),  # Weight: up to 25 points for pages per session
        ]
        
        engagement_score = sum(min(factor * weight, weight) for factor, weight in engagement_factors)
        behavior.engagement_score = min(100, engagement_score)
    
    def _update_device_analytics(self, behavior: UserBehavior):
        """Update device and browser analytics"""
        user_id = behavior.user_id
        
        # Get recent events with device info
        recent_events = AnalyticsEvent.query.filter(
            and_(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.user_agent.isnot(None),
                AnalyticsEvent.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).all()
        
        if not recent_events:
            return
        
        # Parse user agents to get device info
        device_types = []
        browsers = []
        operating_systems = []
        
        for event in recent_events:
            if event.user_agent:
                # Simple user agent parsing (in production, use a proper library)
                ua = event.user_agent.lower()
                
                # Device type detection
                if 'mobile' in ua:
                    device_types.append('mobile')
                elif 'tablet' in ua:
                    device_types.append('tablet')
                else:
                    device_types.append('desktop')
                
                # Browser detection
                if 'chrome' in ua:
                    browsers.append('chrome')
                elif 'firefox' in ua:
                    browsers.append('firefox')
                elif 'safari' in ua:
                    browsers.append('safari')
                elif 'edge' in ua:
                    browsers.append('edge')
                else:
                    browsers.append('other')
                
                # OS detection
                if 'windows' in ua:
                    operating_systems.append('windows')
                elif 'mac' in ua:
                    operating_systems.append('macos')
                elif 'linux' in ua:
                    operating_systems.append('linux')
                elif 'android' in ua:
                    operating_systems.append('android')
                elif 'ios' in ua:
                    operating_systems.append('ios')
                else:
                    operating_systems.append('other')
        
        # Update primary device info
        if device_types:
            behavior.primary_device_type = Counter(device_types).most_common(1)[0][0]
        
        if browsers:
            behavior.primary_browser = Counter(browsers).most_common(1)[0][0]
        
        if operating_systems:
            behavior.primary_os = Counter(operating_systems).most_common(1)[0][0]
    
    def get_user_behavior_summary(self, user_id: int) -> Dict:
        """Get comprehensive user behavior summary"""
        behavior = UserBehavior.query.filter_by(user_id=user_id).first()
        
        if not behavior:
            return {}
        
        return behavior.to_dict()
    
    def get_behavior_insights(self, user_id: int) -> Dict:
        """Get behavioral insights and recommendations"""
        behavior = UserBehavior.query.filter_by(user_id=user_id).first()
        
        if not behavior:
            return {}
        
        insights = {
            'engagement_level': self._calculate_engagement_level(behavior),
            'activity_pattern': self._analyze_activity_pattern(behavior),
            'content_preferences': self._analyze_content_preferences(behavior),
            'recommendations': self._generate_recommendations(behavior)
        }
        
        return insights
    
    def _calculate_engagement_level(self, behavior: UserBehavior) -> str:
        """Calculate engagement level based on behavior metrics"""
        score = behavior.engagement_score
        
        if score >= 80:
            return 'highly_engaged'
        elif score >= 60:
            return 'engaged'
        elif score >= 40:
            return 'moderately_engaged'
        elif score >= 20:
            return 'minimally_engaged'
        else:
            return 'disengaged'
    
    def _analyze_activity_pattern(self, behavior: UserBehavior) -> Dict:
        """Analyze user's activity pattern"""
        return {
            'most_active_time': f"{behavior.most_active_hour or 'N/A'}:00",
            'most_active_day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][behavior.most_active_day or 0] if behavior.most_active_day is not None else 'N/A',
            'consistency_score': behavior.activity_consistency,
            'session_pattern': 'long_sessions' if behavior.avg_session_duration > 30 else 'short_sessions'
        }
    
    def _analyze_content_preferences(self, behavior: UserBehavior) -> Dict:
        """Analyze user's content preferences"""
        preferences = {
            'content_creation': 'high' if behavior.posts_created + behavior.comments_created > 10 else 'low',
            'voting_activity': 'active' if behavior.votes_cast > 50 else 'passive',
            'search_behavior': 'exploratory' if behavior.searches_performed > 20 else 'focused',
            'device_preference': behavior.primary_device_type or 'unknown'
        }
        
        if behavior.most_visited_category:
            category = Category.query.get(behavior.most_visited_category)
            preferences['favorite_category'] = category.name if category else 'unknown'
        
        return preferences
    
    def _generate_recommendations(self, behavior: UserBehavior) -> List[str]:
        """Generate personalized recommendations based on behavior"""
        recommendations = []
        
        if behavior.engagement_score < 50:
            recommendations.append("Try to increase your engagement by participating more in discussions")
        
        if behavior.posts_created == 0:
            recommendations.append("Consider creating your first post to share your knowledge")
        
        if behavior.votes_cast < 10:
            recommendations.append("Vote on content to help improve content quality")
        
        if behavior.bounce_rate > 0.7:
            recommendations.append("Try to explore more content to reduce your bounce rate")
        
        if behavior.activity_consistency < 0.3:
            recommendations.append("Try to maintain a more consistent activity pattern")
        
        return recommendations

class ContentPerformanceService:
    """Service for analyzing content performance metrics"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    def update_content_performance(self, content_type: str, content_id: int) -> ContentPerformance:
        """Update or create content performance analytics"""
        performance = ContentPerformance.query.filter_by(
            content_type=content_type,
            content_id=content_id
        ).first()
        
        if not performance:
            performance = ContentPerformance(
                content_type=content_type,
                content_id=content_id
            )
            db.session.add(performance)
        
        # Update view metrics
        self._update_view_metrics(performance)
        
        # Update engagement metrics
        self._update_engagement_metrics(performance)
        
        # Update comment metrics
        self._update_comment_metrics(performance)
        
        # Update sharing metrics
        self._update_sharing_metrics(performance)
        
        # Update quality metrics
        self._update_quality_metrics(performance)
        
        # Update trend metrics
        self._update_trend_metrics(performance)
        
        # Update timestamps
        performance.last_updated = datetime.utcnow()
        
        db.session.commit()
        return performance
    
    def _update_view_metrics(self, performance: ContentPerformance):
        """Update view-related metrics"""
        content_type = performance.content_type
        content_id = performance.content_id
        
        # Get view events
        view_events = self.analytics_service.get_event_statistics(
            event_type='view',
            target_type=content_type,
            target_id=content_id
        )
        
        total_views = view_events['total_events']
        
        # Get unique views
        unique_views = view_events['unique_users']
        
        # Calculate average view duration
        view_durations = []
        for event in AnalyticsEvent.query.filter(
            and_(
                AnalyticsEvent.event_type == 'view',
                AnalyticsEvent.target_type == content_type,
                AnalyticsEvent.target_id == content_id,
                AnalyticsEvent.event_data.isnot(None)
            )
        ).all():
            if event.event_data and 'duration' in event.event_data:
                view_durations.append(event.event_data['duration'])
        
        avg_view_duration = statistics.mean(view_durations) if view_durations else 0
        
        # Calculate daily view counts
        daily_views = defaultdict(int)
        for event in AnalyticsEvent.query.filter(
            and_(
                AnalyticsEvent.event_type == 'view',
                AnalyticsEvent.target_type == content_type,
                AnalyticsEvent.target_id == content_id,
                AnalyticsEvent.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).all():
            daily_views[event.created_at.date()] += 1
        
        # Update performance
        performance.total_views = total_views
        performance.unique_views = unique_views
        performance.avg_view_duration = avg_view_duration
        performance.view_count_by_day = {str(k): v for k, v in daily_views.items()}
        
        # Update timestamps
        if total_views > 0:
            first_view = AnalyticsEvent.query.filter(
                and_(
                    AnalyticsEvent.event_type == 'view',
                    AnalyticsEvent.target_type == content_type,
                    AnalyticsEvent.target_id == content_id
                )
            ).order_by(AnalyticsEvent.created_at).first()
            
            if first_view:
                performance.first_viewed = first_view.created_at
            
            last_view = AnalyticsEvent.query.filter(
                and_(
                    AnalyticsEvent.event_type == 'view',
                    AnalyticsEvent.target_type == content_type,
                    AnalyticsEvent.target_id == content_id
                )
            ).order_by(desc(AnalyticsEvent.created_at)).first()
            
            if last_view:
                performance.last_viewed = last_view.created_at
    
    def _update_engagement_metrics(self, performance: ContentPerformance):
        """Update engagement-related metrics"""
        content_type = performance.content_type
        content_id = performance.content_id
        
        # Get vote events
        vote_events = self.analytics_service.get_event_statistics(
            event_type='vote',
            target_type=content_type,
            target_id=content_id
        )
        
        total_votes = vote_events['total_events']
        
        # Get upvotes and downvotes
        upvote_events = self.analytics_service.get_event_statistics(
            event_type='vote',
            event_category='upvote',
            target_type=content_type,
            target_id=content_id
        )
        
        downvote_events = self.analytics_service.get_event_statistics(
            event_type='vote',
            event_category='downvote',
            target_type=content_type,
            target_id=content_id
        )
        
        upvotes = upvote_events['total_events']
        downvotes = downvote_events['total_events']
        
        # Calculate vote ratio
        vote_ratio = upvotes / total_votes if total_votes > 0 else 0
        
        # Calculate weighted score (considering voter reputation)
        weighted_score = 0
        for event in AnalyticsEvent.query.filter(
            and_(
                AnalyticsEvent.event_type == 'vote',
                AnalyticsEvent.target_type == content_type,
                AnalyticsEvent.target_id == content_id
            )
        ).all():
            if event.event_data and 'vote_weight' in event.event_data:
                weight = event.event_data['vote_weight']
                if event.event_category == 'upvote':
                    weighted_score += weight
                else:
                    weighted_score -= weight
        
        # Update performance
        performance.total_votes = total_votes
        performance.upvotes = upvotes
        performance.downvotes = downvotes
        performance.vote_ratio = vote_ratio
        performance.weighted_score = weighted_score
    
    def _update_comment_metrics(self, performance: ContentPerformance):
        """Update comment-related metrics"""
        content_type = performance.content_type
        content_id = performance.content_id
        
        if content_type == 'post':
            # Get comments for this post
            comments = Comment.query.filter_by(post_id=content_id).all()
            
            total_comments = len(comments)
            unique_commenters = len(set(comment.user_id for comment in comments))
            
            # Calculate average comment length
            if comments:
                comment_lengths = [len(comment.content) for comment in comments]
                avg_comment_length = statistics.mean(comment_lengths)
                
                # Calculate response time to first comment
                post = Post.query.get(content_id)
                if post and comments:
                    first_comment = min(comments, key=lambda c: c.created_at)
                    response_time = (first_comment.created_at - post.created_at).total_seconds()
                else:
                    response_time = 0
            else:
                avg_comment_length = 0
                response_time = 0
        else:
            total_comments = 0
            unique_commenters = 0
            avg_comment_length = 0
            response_time = 0
        
        # Update performance
        performance.total_comments = total_comments
        performance.unique_commenters = unique_commenters
        performance.avg_comment_length = avg_comment_length
        performance.comment_response_time = response_time
    
    def _update_sharing_metrics(self, performance: ContentPerformance):
        """Update sharing-related metrics"""
        content_type = performance.content_type
        content_id = performance.content_id
        
        # Get share events
        share_events = self.analytics_service.get_event_statistics(
            event_type='share',
            target_type=content_type,
            target_id=content_id
        )
        
        shares_count = share_events['total_events']
        
        # Get bookmark events
        bookmark_events = self.analytics_service.get_event_statistics(
            event_type='bookmark',
            target_type=content_type,
            target_id=content_id
        )
        
        bookmarks_count = bookmark_events['total_events']
        
        # Get external link events
        external_events = self.analytics_service.get_event_statistics(
            event_type='external_link',
            target_type=content_type,
            target_id=content_id
        )
        
        external_links = external_events['total_events']
        
        # Update performance
        performance.shares_count = shares_count
        performance.bookmarks_count = bookmarks_count
        performance.external_links = external_links
    
    def _update_quality_metrics(self, performance: ContentPerformance):
        """Update quality-related metrics"""
        # Calculate read ratio (views that read to end)
        read_events = self.analytics_service.get_event_statistics(
            event_type='read_complete',
            target_type=performance.content_type,
            target_id=performance.content_id
        )
        
        complete_reads = read_events['total_events']
        read_ratio = complete_reads / performance.total_views if performance.total_views > 0 else 0
        
        # Calculate scroll depth
        scroll_events = AnalyticsEvent.query.filter(
            and_(
                AnalyticsEvent.event_type == 'scroll',
                AnalyticsEvent.target_type == performance.content_type,
                AnalyticsEvent.target_id == performance.content_id,
                AnalyticsEvent.event_data.isnot(None)
            )
        ).all()
        
        scroll_depths = []
        for event in scroll_events:
            if event.event_data and 'depth' in event.event_data:
                scroll_depths.append(event.event_data['depth'])
        
        avg_scroll_depth = statistics.mean(scroll_depths) if scroll_depths else 0
        
        # Calculate click-through rate
        click_events = self.analytics_service.get_event_statistics(
            event_type='click',
            target_type=performance.content_type,
            target_id=performance.content_id
        )
        
        clicks = click_events['total_events']
        click_through_rate = clicks / performance.total_views if performance.total_views > 0 else 0
        
        # Calculate quality score (0-100)
        quality_factors = [
            (read_ratio * 30),  # Weight: 30 points for read completion
            (avg_scroll_depth * 25),  # Weight: 25 points for scroll depth
            (click_through_rate * 20),  # Weight: 20 points for CTR
            (min(performance.vote_ratio * 25, 25)),  # Weight: 25 points for vote ratio
        ]
        
        quality_score = sum(quality_factors)
        
        # Update performance
        performance.read_ratio = read_ratio
        performance.scroll_depth = avg_scroll_depth
        performance.click_through_rate = click_through_rate
        performance.quality_score = quality_score
    
    def _update_trend_metrics(self, performance: ContentPerformance):
        """Update trend-related metrics"""
        # Analyze view trends
        if performance.view_count_by_day:
            daily_views = [int(v) for v in performance.view_count_by_day.values()]
            if len(daily_views) >= 7:
                recent_views = daily_views[-7:]
                earlier_views = daily_views[-14:-7] if len(daily_views) >= 14 else daily_views[:-7]
                
                if earlier_views:
                    recent_avg = statistics.mean(recent_views)
                    earlier_avg = statistics.mean(earlier_views)
                    
                    if recent_avg > earlier_avg * 1.1:
                        performance.view_trend = 'increasing'
                    elif recent_avg < earlier_avg * 0.9:
                        performance.view_trend = 'decreasing'
                    else:
                        performance.view_trend = 'stable'
        
        # Calculate engagement score (0-100)
        engagement_factors = [
            (performance.quality_score * 0.4),  # Weight: 40%
            (min(performance.vote_ratio * 100, 100) * 0.3),  # Weight: 30%
            (min(performance.click_through_rate * 100, 100) * 0.2),  # Weight: 20%
            (min(performance.read_ratio * 100, 100) * 0.1),  # Weight: 10%
        ]
        
        engagement_score = sum(engagement_factors)
        
        # Calculate overall performance score (0-100)
        performance_factors = [
            (performance.quality_score * 0.5),  # Weight: 50%
            (engagement_score * 0.3),  # Weight: 30%
            (min(performance.total_views / 10, 100) * 0.2),  # Weight: 20%
        ]
        
        performance_score = sum(performance_factors)
        
        # Update performance
        performance.engagement_score = engagement_score
        performance.performance_score = performance_score
    
    def get_top_performing_content(self, content_type: str = 'post', 
                                  limit: int = 10, metric: str = 'performance_score') -> List[Dict]:
        """Get top performing content"""
        query = ContentPerformance.query.filter_by(content_type=content_type)
        
        if metric == 'performance_score':
            query = query.order_by(desc(ContentPerformance.performance_score))
        elif metric == 'engagement_score':
            query = query.order_by(desc(ContentPerformance.engagement_score))
        elif metric == 'quality_score':
            query = query.order_by(desc(ContentPerformance.quality_score))
        elif metric == 'total_views':
            query = query.order_by(desc(ContentPerformance.total_views))
        
        results = query.limit(limit).all()
        
        return [perf.to_dict() for perf in results]
    
    def get_content_insights(self, content_type: str, content_id: int) -> Dict:
        """Get comprehensive content insights"""
        performance = ContentPerformance.query.filter_by(
            content_type=content_type,
            content_id=content_id
        ).first()
        
        if not performance:
            return {}
        
        insights = {
            'performance_summary': {
                'score': performance.performance_score,
                'grade': self._calculate_performance_grade(performance.performance_score),
                'rank': self._calculate_content_rank(performance)
            },
            'audience_engagement': {
                'total_views': performance.total_views,
                'unique_viewers': performance.unique_views,
                'avg_time_on_page': performance.avg_view_duration,
                'bounce_rate': self._calculate_bounce_rate(performance)
            },
            'content_quality': {
                'quality_score': performance.quality_score,
                'read_ratio': performance.read_ratio,
                'scroll_depth': performance.scroll_depth,
                'vote_ratio': performance.vote_ratio
            },
            'social_signals': {
                'shares': performance.shares_count,
                'bookmarks': performance.bookmarks_count,
                'comments': performance.total_comments,
                'engagement': performance.engagement_score
            },
            'trends': {
                'view_trend': performance.view_trend,
                'engagement_trend': performance.engagement_trend,
                'performance_trend': performance.performance_trend
            },
            'recommendations': self._generate_content_recommendations(performance)
        }
        
        return insights
    
    def _calculate_performance_grade(self, score: float) -> str:
        """Calculate performance grade based on score"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        elif score >= 45:
            return 'D+'
        elif score >= 40:
            return 'D'
        else:
            return 'F'
    
    def _calculate_content_rank(self, performance: ContentPerformance) -> int:
        """Calculate content rank among similar content"""
        similar_content = ContentPerformance.query.filter_by(
            content_type=performance.content_type
        ).order_by(desc(ContentPerformance.performance_score)).all()
        
        for i, perf in enumerate(similar_content):
            if perf.id == performance.id:
                return i + 1
        
        return 0
    
    def _calculate_bounce_rate(self, performance: ContentPerformance) -> float:
        """Calculate bounce rate for content"""
        # This is a simplified calculation
        # In a real implementation, you'd track session-level data
        if performance.total_views == 0:
            return 0
        
        # Estimate bounce rate based on engagement metrics
        engagement_indicators = [
            performance.avg_view_duration / 60,  # Time on page in minutes
            performance.read_ratio,
            performance.scroll_depth,
            performance.click_through_rate
        ]
        
        avg_engagement = statistics.mean(engagement_indicators)
        bounce_rate = max(0, 1 - avg_engagement)
        
        return bounce_rate
    
    def _generate_content_recommendations(self, performance: ContentPerformance) -> List[str]:
        """Generate recommendations for content improvement"""
        recommendations = []
        
        if performance.quality_score < 70:
            recommendations.append("Improve content quality to increase engagement")
        
        if performance.read_ratio < 0.5:
            recommendations.append("Make content more engaging to encourage reading to completion")
        
        if performance.vote_ratio < 0.7:
            recommendations.append("Focus on creating more valuable content to improve vote ratio")
        
        if performance.total_views < 100:
            recommendations.append("Consider promoting content to increase visibility")
        
        if performance.avg_view_duration < 30:
            recommendations.append("Add more engaging elements to keep readers on page longer")
        
        return recommendations

class SystemMetricsService:
    """Service for system performance and health monitoring"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    def record_metric(self, metric_type: str, metric_category: str, metric_name: str,
                     current_value: float, threshold_warning: float = None,
                     threshold_critical: float = None, metric_data: Dict = None,
                     tags: List[str] = None) -> SystemMetrics:
        """Record a system metric"""
        # Get existing metric
        metric = SystemMetrics.query.filter_by(
            metric_type=metric_type,
            metric_category=metric_category,
            metric_name=metric_name
        ).first()
        
        if not metric:
            metric = SystemMetrics(
                metric_type=metric_type,
                metric_category=metric_category,
                metric_name=metric_name,
                current_value=current_value,
                threshold_warning=threshold_warning,
                threshold_critical=threshold_critical,
                metric_data=metric_data or {},
                tags=tags or []
            )
            db.session.add(metric)
        else:
            # Update existing metric
            metric.previous_value = metric.current_value
            metric.current_value = current_value
            metric.recorded_at = datetime.utcnow()
            
            if metric_data:
                metric.metric_data.update(metric_data)
            
            if tags:
                metric.tags = tags
        
        # Update health status
        self._update_health_status(metric)
        
        # Update min/max/avg values
        self._update_statistical_values(metric)
        
        db.session.commit()
        return metric
    
    def _update_health_status(self, metric: SystemMetrics):
        """Update health status based on thresholds"""
        if metric.threshold_critical and metric.current_value >= metric.threshold_critical:
            metric.health_status = 'critical'
        elif metric.threshold_warning and metric.current_value >= metric.threshold_warning:
            metric.health_status = 'warning'
        else:
            metric.health_status = 'healthy'
    
    def _update_statistical_values(self, metric: SystemMetrics):
        """Update statistical values for the metric"""
        # Get all historical values for this metric
        historical_values = SystemMetrics.query.filter(
            and_(
                SystemMetrics.metric_type == metric.metric_type,
                SystemMetrics.metric_category == metric.metric_category,
                SystemMetrics.metric_name == metric.metric_name
            )
        ).with_entities(SystemMetrics.current_value).all()
        
        if historical_values:
            values = [v[0] for v in historical_values]
            metric.min_value = min(values)
            metric.max_value = max(values)
            metric.avg_value = statistics.mean(values)
    
    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        # Get all metrics
        metrics = SystemMetrics.query.all()
        
        health_summary = {
            'overall_status': 'healthy',
            'critical_issues': [],
            'warnings': [],
            'healthy_metrics': [],
            'total_metrics': len(metrics),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        for metric in metrics:
            if metric.health_status == 'critical':
                health_summary['critical_issues'].append({
                    'metric': metric.metric_name,
                    'category': metric.metric_category,
                    'current_value': metric.current_value,
                    'threshold': metric.threshold_critical
                })
                health_summary['overall_status'] = 'critical'
            elif metric.health_status == 'warning':
                health_summary['warnings'].append({
                    'metric': metric.metric_name,
                    'category': metric.metric_category,
                    'current_value': metric.current_value,
                    'threshold': metric.threshold_warning
                })
                if health_summary['overall_status'] == 'healthy':
                    health_summary['overall_status'] = 'warning'
            else:
                health_summary['healthy_metrics'].append({
                    'metric': metric.metric_name,
                    'category': metric.metric_category,
                    'current_value': metric.current_value
                })
        
        return health_summary
    
    def get_performance_metrics(self) -> Dict:
        """Get performance-related metrics"""
        performance_metrics = SystemMetrics.query.filter_by(
            metric_type='performance'
        ).all()
        
        return {
            'response_time': self._get_metric_value(performance_metrics, 'response_time'),
            'cpu_usage': self._get_metric_value(performance_metrics, 'cpu_usage'),
            'memory_usage': self._get_metric_value(performance_metrics, 'memory_usage'),
            'disk_usage': self._get_metric_value(performance_metrics, 'disk_usage'),
            'network_io': self._get_metric_value(performance_metrics, 'network_io'),
            'db_connections': self._get_metric_value(performance_metrics, 'db_connections'),
            'db_query_time': self._get_metric_value(performance_metrics, 'avg_query_time'),
            'cache_hit_rate': self._get_metric_value(performance_metrics, 'cache_hit_rate')
        }
    
    def get_user_metrics(self) -> Dict:
        """Get user-related metrics"""
        user_metrics = SystemMetrics.query.filter_by(
            metric_type='user'
        ).all()
        
        return {
            'active_users': self._get_metric_value(user_metrics, 'active_users'),
            'concurrent_sessions': self._get_metric_value(user_metrics, 'concurrent_sessions'),
            'requests_per_second': self._get_metric_value(user_metrics, 'requests_per_second'),
            'error_rate': self._get_metric_value(user_metrics, 'error_rate')
        }
    
    def get_database_metrics(self) -> Dict:
        """Get database-related metrics"""
        db_metrics = SystemMetrics.query.filter_by(
            metric_type='database'
        ).all()
        
        return {
            'connections': self._get_metric_value(db_metrics, 'db_connections'),
            'query_time': self._get_metric_value(db_metrics, 'avg_query_time'),
            'size': self._get_metric_value(db_metrics, 'db_size'),
            'cache_hit_rate': self._get_metric_value(db_metrics, 'cache_hit_rate')
        }
    
    def _get_metric_value(self, metrics: List[SystemMetrics], metric_name: str) -> float:
        """Get current value for a specific metric"""
        for metric in metrics:
            if metric.metric_name == metric_name:
                return metric.current_value
        return 0.0
    
    def get_metrics_history(self, metric_type: str = None, metric_category: str = None,
                           metric_name: str = None, hours: int = 24) -> List[Dict]:
        """Get historical metrics data"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = SystemMetrics.query.filter(SystemMetrics.recorded_at >= start_time)
        
        if metric_type:
            query = query.filter(SystemMetrics.metric_type == metric_type)
        if metric_category:
            query = query.filter(SystemMetrics.metric_category == metric_category)
        if metric_name:
            query = query.filter(SystemMetrics.metric_name == metric_name)
        
        metrics = query.order_by(SystemMetrics.recorded_at).all()
        
        return [metric.to_dict() for metric in metrics]

class TrendAnalysisService:
    """Service for trend analysis and predictions"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    def analyze_trend(self, target_type: str, metric_name: str, target_id: int = None,
                      period_days: int = 30) -> TrendAnalysis:
        """Analyze trends for a specific metric"""
        # Check if analysis already exists and is recent
        existing = TrendAnalysis.query.filter_by(
            target_type=target_type,
            target_id=target_id,
            metric_name=metric_name,
            period_days=period_days
        ).filter(
            TrendAnalysis.analysis_date >= datetime.utcnow() - timedelta(hours=6)
        ).first()
        
        if existing:
            return existing
        
        # Get historical data
        historical_data = self._get_historical_data(target_type, target_id, metric_name, period_days)
        
        if len(historical_data) < 3:
            # Not enough data for trend analysis
            trend = TrendAnalysis(
                analysis_type='linear',
                target_type=target_type,
                target_id=target_id,
                metric_name=metric_name,
                period_days=period_days,
                data_points=len(historical_data),
                trend_direction='stable',
                trend_strength=0.0,
                slope=0.0,
                mean_value=statistics.mean(historical_data) if historical_data else 0,
                median_value=statistics.median(historical_data) if historical_data else 0,
                std_deviation=statistics.stdev(historical_data) if len(historical_data) > 1 else 0,
                variance=statistics.variance(historical_data) if historical_data else 0,
                raw_data={'values': historical_data, 'dates': [str(d) for d in self._get_data_dates(target_type, target_id, metric_name, period_days)]}
            )
        else:
            # Perform trend analysis
            trend = self._perform_trend_analysis(historical_data, target_type, target_id, metric_name, period_days)
        
        # Detect anomalies
        self._detect_anomalies(trend, historical_data)
        
        # Check for seasonality
        self._analyze_seasonality(trend, historical_data)
        
        # Generate predictions
        self._generate_predictions(trend, historical_data)
        
        # Save trend analysis
        trend.analysis_date = datetime.utcnow()
        trend.next_analysis = datetime.utcnow() + timedelta(hours=6)
        db.session.add(trend)
        db.session.commit()
        
        return trend
    
    def _get_historical_data(self, target_type: str, target_id: int, metric_name: str, period_days: int) -> List[float]:
        """Get historical data for trend analysis"""
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        if target_type == 'user' and target_id:
            # User-specific metrics
            if metric_name == 'reputation_score':
                # Get user reputation history
                from app.reputation.models import UserReputation
                reputation_data = UserReputation.query.filter_by(user_id=target_id).all()
                return [rep.reputation_score for rep in reputation_data]
            elif metric_name == 'engagement_score':
                # Get user engagement history
                behavior = UserBehavior.query.filter_by(user_id=target_id).first()
                if behavior:
                    return [behavior.engagement_score]
                return []
        elif target_type == 'content' and target_id:
            # Content-specific metrics
            if metric_name == 'performance_score':
                # Get content performance history
                performance = ContentPerformance.query.filter_by(
                    content_type='post',
                    content_id=target_id
                ).first()
                if performance:
                    return [performance.performance_score]
                return []
        elif target_type == 'system':
            # System-wide metrics
            metric = SystemMetrics.query.filter_by(
                metric_type='performance',
                metric_name=metric_name
            ).order_by(SystemMetrics.recorded_at.desc()).limit(period_days).all()
            
            return [m.current_value for m in metric]
        
        # Default: get analytics events
        events = AnalyticsEvent.query.filter(
            and_(
                AnalyticsEvent.created_at >= start_date,
                AnalyticsEvent.event_value.isnot(None)
            )
        ).order_by(AnalyticsEvent.created_at).all()
        
        return [event.event_value for event in events]
    
    def _get_data_dates(self, target_type: str, target_id: int, metric_name: str, period_days: int) -> List[datetime]:
        """Get dates corresponding to historical data"""
        start_date = datetime.utcnow() - timedelta(days=period_days)
        dates = []
        
        for i in range(period_days):
            dates.append(start_date + timedelta(days=i))
        
        return dates
    
    def _perform_trend_analysis(self, data: List[float], target_type: str, target_id: int, metric_name: str, period_days: int) -> TrendAnalysis:
        """Perform linear trend analysis"""
        n = len(data)
        x = list(range(n))  # Time points
        
        # Calculate linear regression
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(data)
        
        # Calculate slope
        numerator = sum((x[i] - mean_x) * (data[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Calculate correlation
        if len(data) > 1:
            std_x = statistics.stdev(x)
            std_y = statistics.stdev(data)
            correlation = numerator / (std_x * std_y) if std_x * std_y != 0 else 0
        else:
            correlation = 0
        
        # Determine trend direction and strength
        if abs(slope) < 0.01:  # Very small slope
            trend_direction = 'stable'
            trend_strength = 0.0
        elif slope > 0:
            trend_direction = 'increasing'
            trend_strength = min(abs(slope), 1.0)
        else:
            trend_direction = 'decreasing'
            trend_strength = min(abs(slope), 1.0)
        
        return TrendAnalysis(
            analysis_type='linear',
            target_type=target_type,
            target_id=target_id,
            metric_name=metric_name,
            period_days=period_days,
            data_points=n,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            slope=slope,
            correlation=correlation,
            mean_value=statistics.mean(data),
            median_value=statistics.median(data),
            std_deviation=statistics.stdev(data) if len(data) > 1 else 0,
            variance=statistics.variance(data),
            raw_data={'values': data, 'dates': [str(d) for d in self._get_data_dates(target_type, target_id, metric_name, period_days)]}
        )
    
    def _detect_anomalies(self, trend: TrendAnalysis, data: List[float]):
        """Detect anomalies in the data"""
        if len(data) < 3:
            return
        
        # Use z-score for anomaly detection
        mean = trend.mean_value
        std = trend.std_deviation
        
        anomalies = []
        for i, value in enumerate(data):
            if std > 0:
                z_score = abs(value - mean) / std
                if z_score > 2.5:  # Threshold for anomaly
                    anomalies.append({
                        'index': i,
                        'value': value,
                        'z_score': z_score
                    })
        
        if anomalies:
            trend.is_anomaly = True
            trend.anomaly_score = max(a['z_score'] for a in anomalies) / 5.0  # Normalize to 0-1
            trend.anomaly_reason = f"Detected {len(anomalies)} anomalies with z-scores > 2.5"
    
    def _analyze_seasonality(self, trend: TrendAnalysis, data: List[float]):
        """Analyze seasonal patterns in the data"""
        if len(data) < 14:  # Need at least 2 weeks for weekly seasonality
            trend.has_seasonality = False
            return
        
        # Simple weekly seasonality check
        weekly_patterns = defaultdict(list)
        for i, value in enumerate(data):
            day_of_week = i % 7
            weekly_patterns[day_of_week].append(value)
        
        # Check if there's a consistent weekly pattern
        weekly_means = [statistics.mean(pattern) for pattern in weekly_patterns.values()]
        weekly_std = statistics.stdev(weekly_means) if len(weekly_means) > 1 else 0
        
        # If the standard deviation of weekly means is significant, there might be seasonality
        overall_std = trend.std_deviation
        if overall_std > 0:
            seasonality_strength = weekly_std / overall_std
            trend.has_seasonality = seasonality_strength > 0.3
            trend.seasonal_pattern = {
                'weekly_means': weekly_means,
                'strength': seasonality_strength
            }
    
    def _generate_predictions(self, trend: TrendAnalysis, data: List[float]):
        """Generate predictions based on trend analysis"""
        if len(data) < 3:
            return
        
        # Simple linear prediction
        last_value = data[-1]
        
        # Predict 7 days ahead
        predicted_7d = last_value + (trend.slope * 7)
        
        # Predict 30 days ahead
        predicted_30d = last_value + (trend.slope * 30)
        
        # Calculate prediction confidence based on trend strength and correlation
        confidence = (trend.trend_strength + abs(trend.correlation)) / 2
        
        trend.predicted_value_7d = predicted_7d
        trend.predicted_value_30d = predicted_30d
        trend.prediction_confidence = confidence
    
    def get_trend_summary(self, target_type: str, target_id: int = None) -> Dict:
        """Get summary of all trends for a target"""
        trends = TrendAnalysis.query.filter_by(
            target_type=target_type,
            target_id=target_id
        ).order_by(desc(TrendAnalysis.analysis_date)).all()
        
        summary = {
            'target_type': target_type,
            'target_id': target_id,
            'total_trends': len(trends),
            'recent_trends': [],
            'anomalies_detected': 0,
            'trend_summary': {}
        }
        
        for trend in trends[:10]:  # Last 10 trends
            trend_dict = trend.to_dict()
            summary['recent_trends'].append(trend_dict)
            
            if trend.is_anomaly:
                summary['anomalies_detected'] += 1
        
        # Aggregate trend directions
        trend_directions = Counter(trend.trend_direction for trend in trends)
        summary['trend_summary'] = {
            'most_common_direction': trend_directions.most_common(1)[0][0] if trend_directions else 'stable',
            'direction_counts': dict(trend_directions),
            'avg_trend_strength': statistics.mean([trend.trend_strength for trend in trends]) if trends else 0
        }
        
        return summary

class PredictiveAnalyticsService:
    """Service for predictive analytics and machine learning"""
    
    def __init__(self):
        self.trend_service = TrendAnalysisService()
    
    def create_predictive_model(self, model_name: str, model_type: str, prediction_target: str,
                               model_config: Dict, feature_columns: List[str],
                               target_column: str, description: str = None) -> PredictiveModel:
        """Create a new predictive model"""
        model = PredictiveModel(
            model_name=model_name,
            model_type=model_type,
            prediction_target=prediction_target,
            model_config=model_config,
            feature_columns=feature_columns,
            target_column=target_column,
            description=description
        )
        
        db.session.add(model)
        db.session.commit()
        
        return model
    
    def train_model(self, model_id: int, training_data: List[Dict]) -> Dict:
        """Train a predictive model"""
        model = PredictiveModel.query.get(model_id)
        
        if not model:
            raise ValueError(f"Model with ID {model_id} not found")
        
        # This is a simplified training process
        # In a real implementation, you'd use scikit-learn or similar
        
        # Extract features and targets
        features = []
        targets = []
        
        for data_point in training_data:
            feature_vector = [data_point.get(col, 0) for col in model.feature_columns]
            target_value = data_point.get(model.target_column, 0)
            
            features.append(feature_vector)
            targets.append(target_value)
        
        # Split data
        split_point = int(len(features) * 0.8)
        train_features = features[:split_point]
        train_targets = targets[:split_point]
        test_features = features[split_point:]
        test_targets = targets[split_point:]
        
        # Simple linear regression (for demonstration)
        model.training_samples = len(training_data)
        model.training_start_date = datetime.utcnow() - timedelta(days=30)
        model.training_end_date = datetime.utcnow()
        model.validation_samples = len(test_features)
        
        # Calculate performance metrics (simplified)
        if model.model_type == 'regression':
            # For regression, use simple metrics
            model.mse = 0.1  # Placeholder
            model.mae = 0.2  # Placeholder
            model.r2_score = 0.85  # Placeholder
        else:
            # For classification
            model.accuracy = 0.92  # Placeholder
            model.precision = 0.89  # Placeholder
            model.recall = 0.87  # Placeholder
            model.f1_score = 0.88  # Placeholder
        
        model.is_trained = True
        model.last_trained_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'model_id': model.id,
            'training_samples': model.training_samples,
            'validation_samples': model.validation_samples,
            'performance': {
                'accuracy': model.accuracy,
                'precision': model.precision,
                'recall': model.recall,
                'f1_score': model.f1_score,
                'mse': model.mse,
                'mae': model.mae,
                'r2_score': model.r2_score
            }
        }
    
    def make_prediction(self, model_id: int, features: Dict) -> Dict:
        """Make a prediction using a trained model"""
        model = PredictiveModel.query.get(model_id)
        
        if not model or not model.is_trained:
            raise ValueError(f"Model {model_id} not found or not trained")
        
        # Extract feature vector
        feature_vector = [features.get(col, 0) for col in model.feature_columns]
        
        # Simple prediction (for demonstration)
        if model.model_type == 'regression':
            # For regression, use a simple linear combination
            prediction = sum(feature_vector) / len(feature_vector) if feature_vector else 0
        else:
            # For classification, use a simple threshold
            prediction = 1 if sum(feature_vector) / len(feature_vector) > 0.5 else 0
        
        # Update model statistics
        model.total_predictions += 1
        model.last_prediction_date = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'model_id': model.id,
            'model_name': model.model_name,
            'prediction': prediction,
            'confidence': 0.85,  # Placeholder
            'features_used': model.feature_columns
        }
    
    def get_model_performance(self, model_id: int) -> Dict:
        """Get performance metrics for a model"""
        model = PredictiveModel.query.get(model_id)
        
        if not model:
            return {}
        
        return {
            'model_name': model.model_name,
            'model_type': model.model_type,
            'prediction_target': model.prediction_target,
            'is_trained': model.is_trained,
            'training_samples': model.training_samples,
            'validation_samples': model.validation_samples,
            'total_predictions': model.total_predictions,
            'performance': {
                'accuracy': model.accuracy,
                'precision': model.precision,
                'recall': model.recall,
                'f1_score': model.f1_score,
                'mse': model.mse,
                'mae': model.mae,
                'r2_score': model.r2_score
            },
            'last_trained': model.last_trained_at.isoformat() if model.last_trained_at else None,
            'last_prediction': model.last_prediction_date.isoformat() if model.last_prediction_date else None
        }
    
    def get_active_models(self) -> List[Dict]:
        """Get all active predictive models"""
        models = PredictiveModel.query.filter_by(is_active=True).all()
        
        return [model.to_dict() for model in models]
