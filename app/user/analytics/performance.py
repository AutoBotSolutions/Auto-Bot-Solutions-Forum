"""
Performance optimizations for User Analytics System
"""

import json
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, g
from app import db, cache
from app.user.analytics.models import UserBehavior, UserEngagement, UserPerformance, UserSegment


class AnalyticsPerformanceOptimizer:
    """Optimizes analytics performance through caching and query optimization."""
    
    @staticmethod
    def cache_key(user_id, data_type, *args):
        """Generate cache key for analytics data."""
        return f"analytics:{user_id}:{data_type}:{':'.join(map(str, args))}"
    
    @staticmethod
    def get_cached_analytics(user_id, data_type, timeout=600):
        """Get cached analytics data."""
        cache_key = AnalyticsPerformanceOptimizer.cache_key(user_id, data_type)
        return cache.get(cache_key)
    
    @staticmethod
    def set_cached_analytics(user_id, data_type, data, timeout=600):
        """Set cached analytics data."""
        cache_key = AnalyticsPerformanceOptimizer.cache_key(user_id, data_type)
        cache.set(cache_key, data, timeout=timeout)
    
    @staticmethod
    def invalidate_analytics_cache(user_id, data_type=None):
        """Invalidate analytics cache."""
        if data_type:
            cache_key = AnalyticsPerformanceOptimizer.cache_key(user_id, data_type)
            cache.delete(cache_key)
        else:
            # Invalidate all analytics cache for user
            pattern = f"analytics:{user_id}:*"
            cache.delete_pattern(pattern)
    
    @staticmethod
    def get_optimized_user_behaviors(user_id, behavior_type=None, days=30, limit=100):
        """Get optimized user behaviors with caching."""
        cache_key = AnalyticsPerformanceOptimizer.cache_key(
            user_id, 'behaviors', behavior_type or 'all', days, limit
        )
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Build optimized query
        query = UserBehavior.query.filter(UserBehavior.user_id == user_id)
        
        if behavior_type:
            query = query.filter(UserBehavior.behavior_type == behavior_type)
        
        if days:
            since_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(UserBehavior.created_at >= since_date)
        
        behaviors = query.order_by(UserBehavior.created_at.desc()).limit(limit).all()
        
        # Optimize data serialization
        behaviors_data = []
        for behavior in behaviors:
            behavior_data = {
                'id': behavior.id,
                'behavior_type': behavior.behavior_type,
                'action': behavior.action,
                'target_type': behavior.target_type,
                'target_id': behavior.target_id,
                'session_id': behavior.session_id,
                'duration': behavior.duration,
                'created_at': behavior.created_at.isoformat()
            }
            
            # Only include metadata if it exists
            if behavior.metadata:
                behavior_data['metadata'] = behavior.metadata
            
            behaviors_data.append(behavior_data)
        
        # Cache the result
        load_time = time.time() - start_time
        result = {
            'behaviors': behaviors_data,
            'load_time': load_time,
            'total_count': len(behaviors_data)
        }
        
        cache.set(cache_key, result, timeout=600)  # 10 minutes
        
        return result
    
    @staticmethod
    def get_optimized_engagement_trend(user_id, days=30):
        """Get optimized engagement trend with caching."""
        cache_key = AnalyticsPerformanceOptimizer.cache_key(user_id, 'engagement_trend', days)
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Use optimized query with date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Single query with ordering
        engagements = UserEngagement.query.filter(
            UserEngagement.user_id == user_id,
            UserEngagement.date >= start_date,
            UserEngagement.date <= end_date
        ).order_by(UserEngagement.date.asc()).all()
        
        # Optimize data structure
        trend_data = []
        for engagement in engagements:
            trend_data.append({
                'date': engagement.date.isoformat(),
                'engagement_score': engagement.engagement_score,
                'total_actions': engagement.total_actions,
                'login_count': engagement.login_count,
                'post_count': engagement.post_count,
                'comment_count': engagement.comment_count,
                'like_count': engagement.like_count,
                'share_count': engagement.share_count,
                'view_count': engagement.view_count,
                'session_duration': engagement.session_duration,
                'pages_viewed': engagement.pages_viewed,
                'bounce_rate': engagement.bounce_rate
            })
        
        # Calculate aggregates
        if trend_data:
            avg_engagement = sum(d['engagement_score'] for d in trend_data) / len(trend_data)
            total_actions = sum(d['total_actions'] for d in trend_data)
            max_engagement = max(d['engagement_score'] for d in trend_data)
            min_engagement = min(d['engagement_score'] for d in trend_data)
        else:
            avg_engagement = total_actions = max_engagement = min_engagement = 0
        
        load_time = time.time() - start_time
        result = {
            'trend': trend_data,
            'aggregates': {
                'avg_engagement': avg_engagement,
                'total_actions': total_actions,
                'max_engagement': max_engagement,
                'min_engagement': min_engagement
            },
            'load_time': load_time
        }
        
        cache.set(cache_key, result, timeout=600)
        
        return result
    
    @staticmethod
    def get_optimized_performance_metrics(user_id, period='weekly', days=30):
        """Get optimized performance metrics with caching."""
        cache_key = AnalyticsPerformanceOptimizer.cache_key(user_id, 'performance', period, days)
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Optimized query for performance metrics
        metrics = db.session.query(UserPerformance).filter(
            UserPerformance.user_id == user_id,
            UserPerformance.period == period,
            UserPerformance.period_start >= start_date,
            UserPerformance.period_end <= end_date
        ).order_by(UserPerformance.period_start.desc()).all()
        
        # Group by metric type
        metrics_by_type = {}
        for metric in metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            
            metrics_by_type[metric.metric_type].append({
                'metric_name': metric.metric_name,
                'metric_value': metric.metric_value,
                'previous_value': metric.previous_value,
                'change_percentage': metric.change_percentage,
                'period_start': metric.period_start.isoformat(),
                'period_end': metric.period_end.isoformat()
            })
        
        load_time = time.time() - start_time
        result = {
            'metrics': metrics_by_type,
            'load_time': load_time,
            'total_metrics': len(metrics)
        }
        
        cache.set(cache_key, result, timeout=600)
        
        return result
    
    @staticmethod
    def get_optimized_behavior_stats(user_id, days=30):
        """Get optimized behavior statistics with caching."""
        cache_key = AnalyticsPerformanceOptimizer.cache_key(user_id, 'behavior_stats', days)
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Single query for all behavior stats
        stats = db.session.query(
            UserBehavior.behavior_type,
            UserBehavior.action,
            db.func.count(UserBehavior.id).label('count'),
            db.func.avg(UserBehavior.duration).label('avg_duration'),
            db.func.sum(UserBehavior.duration).label('total_duration')
        ).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= since_date
        ).group_by(
            UserBehavior.behavior_type,
            UserBehavior.action
        ).all()
        
        # Organize stats by behavior type
        stats_by_type = {}
        for stat in stats:
            behavior_type = stat.behavior_type
            if behavior_type not in stats_by_type:
                stats_by_type[behavior_type] = {
                    'total_count': 0,
                    'total_duration': 0,
                    'actions': []
                }
            
            stats_by_type[behavior_type]['total_count'] += stat.count
            stats_by_type[behavior_type]['total_duration'] += stat.total_duration or 0
            
            stats_by_type[behavior_type]['actions'].append({
                'action': stat.action,
                'count': stat.count,
                'avg_duration': float(stat.avg_duration) if stat.avg_duration else 0
            })
        
        load_time = time.time() - start_time
        result = {
            'stats': stats_by_type,
            'load_time': load_time,
            'total_behaviors': sum(s['total_count'] for s in stats_by_type.values())
        }
        
        cache.set(cache_key, result, timeout=600)
        
        return result
    
    @staticmethod
    def batch_user_analytics(user_ids, analytics_types=None):
        """Batch analytics for multiple users."""
        if analytics_types is None:
            analytics_types = ['behaviors', 'engagement_trend', 'performance', 'behavior_stats']
        
        batch_results = {}
        
        for user_id in user_ids:
            user_results = {}
            
            for analytics_type in analytics_types:
                if analytics_type == 'behaviors':
                    user_results[analytics_type] = AnalyticsPerformanceOptimizer.get_optimized_user_behaviors(user_id)
                elif analytics_type == 'engagement_trend':
                    user_results[analytics_type] = AnalyticsPerformanceOptimizer.get_optimized_engagement_trend(user_id)
                elif analytics_type == 'performance':
                    user_results[analytics_type] = AnalyticsPerformanceOptimizer.get_optimized_performance_metrics(user_id)
                elif analytics_type == 'behavior_stats':
                    user_results[analytics_type] = AnalyticsPerformanceOptimizer.get_optimized_behavior_stats(user_id)
            
            batch_results[user_id] = user_results
        
        return batch_results
    
    @staticmethod
    def get_real_time_analytics(user_id):
        """Get real-time analytics data (shorter cache)."""
        cache_key = AnalyticsPerformanceOptimizer.cache_key(user_id, 'realtime')
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Get very recent data (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        recent_behaviors = UserBehavior.query.filter(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= one_hour_ago
        ).order_by(UserBehavior.created_at.desc()).limit(20).all()
        
        # Get today's engagement
        today = datetime.utcnow().date()
        today_engagement = UserEngagement.query.filter_by(
            user_id=user_id,
            date=today
        ).first()
        
        result = {
            'recent_behaviors': [
                {
                    'behavior_type': b.behavior_type,
                    'action': b.action,
                    'created_at': b.created_at.isoformat(),
                    'duration': b.duration
                }
                for b in recent_behaviors
            ],
            'today_engagement': {
                'engagement_score': today_engagement.engagement_score if today_engagement else 0,
                'total_actions': today_engagement.total_actions if today_engagement else 0,
                'login_count': today_engagement.login_count if today_engagement else 0
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache for only 1 minute for real-time data
        cache.set(cache_key, result, timeout=60)
        
        return result
    
    @staticmethod
    def get_analytics_summary(user_id, days=30):
        """Get analytics summary with caching."""
        cache_key = AnalyticsPerformanceOptimizer.cache_key(user_id, 'summary', days)
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Get all analytics data efficiently
        engagement_trend = AnalyticsPerformanceOptimizer.get_optimized_engagement_trend(user_id, days)
        behavior_stats = AnalyticsPerformanceOptimizer.get_optimized_behavior_stats(user_id, days)
        performance_metrics = AnalyticsPerformanceOptimizer.get_optimized_performance_metrics(user_id, 'weekly', days)
        
        # Calculate summary statistics
        summary = {
            'engagement': {
                'avg_score': engagement_trend['aggregates']['avg_engagement'],
                'total_actions': engagement_trend['aggregates']['total_actions'],
                'trend_direction': 'up' if len(engagement_trend['trend']) > 1 and 
                                 engagement_trend['trend'][-1]['engagement_score'] > engagement_trend['trend'][0]['engagement_score'] else 'down'
            },
            'behaviors': {
                'total_types': len(behavior_stats['stats']),
                'most_common_type': max(behavior_stats['stats'].items(), key=lambda x: x[1]['total_count'])[0] if behavior_stats['stats'] else None,
                'total_behaviors': behavior_stats['total_behaviors']
            },
            'performance': {
                'metric_types': list(performance_metrics['metrics'].keys()),
                'total_metrics': performance_metrics['total_metrics']
            },
            'period_days': days
        }
        
        load_time = time.time() - start_time
        summary['load_time'] = load_time
        
        cache.set(cache_key, summary, timeout=600)
        
        return summary


def analytics_cache_timeout(timeout=600):
    """Decorator to set cache timeout for analytics data."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Store original timeout
            original_timeout = getattr(g, 'analytics_cache_timeout', 600)
            g.analytics_cache_timeout = timeout
            
            try:
                result = f(*args, **kwargs)
                return result
            finally:
                # Restore original timeout
                g.analytics_cache_timeout = original_timeout
        
        return decorated_function
    return decorator


def invalidate_analytics_on_change(f):
    """Decorator to invalidate analytics cache when data changes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user_id from arguments
        user_id = None
        if args and hasattr(args[0], 'user_id'):
            user_id = args[0].user_id
        elif 'user_id' in kwargs:
            user_id = kwargs['user_id']
        elif args and hasattr(args[0], 'id'):
            user_id = args[0].id
        
        # Execute the function
        result = f(*args, **kwargs)
        
        # Invalidate cache if user_id was found
        if user_id:
            AnalyticsPerformanceOptimizer.invalidate_analytics_cache(user_id)
        
        return result
    
    return decorated_function


class AnalyticsQueryOptimizer:
    """Optimizes database queries for analytics."""
    
    @staticmethod
    def get_user_behavior_aggregates(user_id, days=30):
        """Get aggregated behavior data with optimized query."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Single query with multiple aggregations
        aggregates = db.session.query(
            db.func.count(UserBehavior.id).label('total_behaviors'),
            db.func.count(db.func.distinct(UserBehavior.behavior_type)).label('unique_types'),
            db.func.count(db.func.distinct(UserBehavior.session_id)).label('unique_sessions'),
            db.func.sum(UserBehavior.duration).label('total_duration'),
            db.func.avg(UserBehavior.duration).label('avg_duration')
        ).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= since_date
        ).first()
        
        return {
            'total_behaviors': aggregates.total_behaviors or 0,
            'unique_types': aggregates.unique_types or 0,
            'unique_sessions': aggregates.unique_sessions or 0,
            'total_duration': aggregates.total_duration or 0,
            'avg_duration': float(aggregates.avg_duration) if aggregates.avg_duration else 0
        }
    
    @staticmethod
    def get_daily_activity_pattern(user_id, days=30):
        """Get daily activity pattern with optimized query."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Single query with date extraction
        daily_stats = db.session.query(
            db.func.date(UserBehavior.created_at).label('date'),
            db.func.count(UserBehavior.id).label('behaviors'),
            db.func.sum(UserBehavior.duration).label('total_duration')
        ).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= since_date
        ).group_by(
            db.func.date(UserBehavior.created_at)
        ).order_by('date').all()
        
        return [
            {
                'date': stat.date.isoformat(),
                'behaviors': stat.behaviors,
                'total_duration': stat.total_duration or 0
            }
            for stat in daily_stats
        ]
    
    @staticmethod
    def get_hourly_activity_pattern(user_id, days=7):
        """Get hourly activity pattern with optimized query."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Single query with hour extraction
        hourly_stats = db.session.query(
            db.func.extract('hour', UserBehavior.created_at).label('hour'),
            db.func.count(UserBehavior.id).label('behaviors')
        ).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= since_date
        ).group_by(
            db.func.extract('hour', UserBehavior.created_at)
        ).order_by('hour').all()
        
        # Fill in missing hours with 0
        hourly_pattern = {int(stat.hour): stat.behaviors for stat in hourly_stats}
        
        return [
            {
                'hour': hour,
                'behaviors': hourly_pattern.get(hour, 0)
            }
            for hour in range(24)
        ]
    
    @staticmethod
    def get_behavior_sequence_analysis(user_id, days=30):
        """Analyze behavior sequences with optimized queries."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get behaviors in order
        behaviors = UserBehavior.query.filter(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= since_date
        ).order_by(UserBehavior.created_at.asc()).all()
        
        # Analyze sequences
        sequences = []
        current_sequence = []
        last_behavior_time = None
        
        for behavior in behaviors:
            if last_behavior_time and (behavior.created_at - last_behavior_time).total_seconds() > 3600:
                # New sequence (gap > 1 hour)
                if current_sequence:
                    sequences.append(current_sequence)
                current_sequence = []
            
            current_sequence.append({
                'behavior_type': behavior.behavior_type,
                'action': behavior.action,
                'timestamp': behavior.created_at.isoformat()
            })
            last_behavior_time = behavior.created_at
        
        if current_sequence:
            sequences.append(current_sequence)
        
        return {
            'total_sequences': len(sequences),
            'avg_sequence_length': sum(len(seq) for seq in sequences) / len(sequences) if sequences else 0,
            'max_sequence_length': max(len(seq) for seq in sequences) if sequences else 0,
            'sequences': sequences[:10]  # Return first 10 sequences
        }


class AnalyticsPerformanceMonitor:
    """Monitor analytics performance."""
    
    @staticmethod
    def track_analytics_query(user_id, query_type, execution_time, result_count):
        """Track analytics query performance."""
        cache_key = f"analytics_performance:{datetime.utcnow().strftime('%Y%m%d')}"
        
        # Get existing performance data
        performance_data = cache.get(cache_key) or {
            'queries': [],
            'avg_execution_time': 0,
            'max_execution_time': 0,
            'min_execution_time': float('inf'),
            'total_queries': 0
        }
        
        # Update performance data
        performance_data['queries'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'query_type': query_type,
            'execution_time': execution_time,
            'result_count': result_count
        })
        
        performance_data['total_queries'] += 1
        performance_data['avg_execution_time'] = (
            (performance_data['avg_execution_time'] * (performance_data['total_queries'] - 1) + execution_time) /
            performance_data['total_queries']
        )
        performance_data['max_execution_time'] = max(performance_data['max_execution_time'], execution_time)
        performance_data['min_execution_time'] = min(performance_data['min_execution_time'], execution_time)
        
        # Keep only last 1000 queries
        if len(performance_data['queries']) > 1000:
            performance_data['queries'] = performance_data['queries'][-1000:]
        
        # Cache for 24 hours
        cache.set(cache_key, performance_data, timeout=86400)
    
    @staticmethod
    def get_performance_stats(days=7):
        """Get performance statistics."""
        stats = []
        
        for day_offset in range(days):
            date = datetime.utcnow().date() - timedelta(days=day_offset)
            cache_key = f"analytics_performance:{date.strftime('%Y%m%d')}"
            day_stats = cache.get(cache_key)
            
            if day_stats:
                stats.append({
                    'date': date.isoformat(),
                    'avg_execution_time': day_stats['avg_execution_time'],
                    'total_queries': day_stats['total_queries'],
                    'max_execution_time': day_stats['max_execution_time'],
                    'min_execution_time': day_stats['min_execution_time']
                })
        
        return sorted(stats, key=lambda x: x['date'])
    
    @staticmethod
    def get_slow_queries(threshold=1.0, limit=50):
        """Get slow queries above threshold."""
        # This would typically query a performance monitoring table
        # For now, return mock data
        return [
            {
                'query_type': 'engagement_trend',
                'execution_time': 1.5,
                'user_id': 123,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
