"""
Search Index Models

This module implements Elasticsearch integration models for advanced search functionality,
including search index management, query tracking, analytics, and optimization.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from sqlalchemy import Index, func as sql_func
import json
import uuid


class SearchIndex(db.Model):
    """Elasticsearch index management model"""
    __tablename__ = 'search_indices'
    __table_args__ = (
        Index('idx_search_index_name', 'index_name'),
        Index('idx_search_index_type', 'index_type'),
        Index('idx_search_index_status', 'status'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    index_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    index_type = db.Column(db.String(50), nullable=False, index=True)  # posts, users, comments, etc.
    status = db.Column(db.String(20), default='active', index=True)  # active, inactive, rebuilding, error
    
    # Index configuration
    index_config = db.Column(db.JSON)  # Elasticsearch index configuration
    mapping_config = db.Column(db.JSON)  # Field mappings
    settings_config = db.Column(db.JSON)  # Index settings
    
    # Index statistics
    document_count = db.Column(db.Integer, default=0)
    index_size_bytes = db.Column(db.BigInteger, default=0)
    last_sync_at = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20), default='pending')  # pending, syncing, completed, error
    
    # Performance metrics
    avg_query_time_ms = db.Column(db.Float, default=0.0)
    queries_per_hour = db.Column(db.Integer, default=0)
    cache_hit_ratio = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_rebuilt_at = db.Column(db.DateTime)
    
    # Metadata
    index_metadata = db.Column(db.JSON)  # Additional index metadata
    
    def __repr__(self):
        return f'<SearchIndex {self.index_name}:{self.index_type}>'
    
    @classmethod
    def create_index(cls, index_name, index_type, index_config=None, mapping_config=None, settings_config=None):
        """Create a new search index"""
        # Check if index already exists
        existing = cls.query.filter_by(index_name=index_name).first()
        if existing:
            return existing
        
        index = cls(
            index_name=index_name,
            index_type=index_type,
            index_config=index_config or {},
            mapping_config=mapping_config or {},
            settings_config=settings_config or {}
        )
        db.session.add(index)
        db.session.commit()
        return index
    
    @classmethod
    def get_index_by_type(cls, index_type):
        """Get search index by type"""
        return cls.query.filter_by(index_type=index_type, status='active').first()
    
    @classmethod
    def get_all_active_indices(cls):
        """Get all active search indices"""
        return cls.query.filter_by(status='active').all()
    
    @classmethod
    def update_index_stats(cls, index_name, document_count=None, index_size_bytes=None, 
                          avg_query_time_ms=None, queries_per_hour=None, cache_hit_ratio=None):
        """Update index statistics"""
        index = cls.query.filter_by(index_name=index_name).first()
        if not index:
            return None
        
        if document_count is not None:
            index.document_count = document_count
        if index_size_bytes is not None:
            index.index_size_bytes = index_size_bytes
        if avg_query_time_ms is not None:
            index.avg_query_time_ms = avg_query_time_ms
        if queries_per_hour is not None:
            index.queries_per_hour = queries_per_hour
        if cache_hit_ratio is not None:
            index.cache_hit_ratio = cache_hit_ratio
        
        index.updated_at = datetime.utcnow()
        db.session.commit()
        return index
    
    @classmethod
    def mark_for_rebuild(cls, index_name):
        """Mark index for rebuilding"""
        index = cls.query.filter_by(index_name=index_name).first()
        if index:
            index.status = 'rebuilding'
            index.last_rebuilt_at = datetime.utcnow()
            db.session.commit()
        return index
    
    def to_dict(self):
        """Convert index to dictionary"""
        return {
            'id': self.id,
            'index_name': self.index_name,
            'index_type': self.index_type,
            'status': self.status,
            'document_count': self.document_count,
            'index_size_bytes': self.index_size_bytes,
            'avg_query_time_ms': self.avg_query_time_ms,
            'queries_per_hour': self.queries_per_hour,
            'cache_hit_ratio': self.cache_hit_ratio,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'sync_status': self.sync_status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_rebuilt_at': self.last_rebuilt_at.isoformat() if self.last_rebuilt_at else None
        }


class SearchQuery(db.Model):
    """Search query tracking model"""
    __tablename__ = 'search_queries'
    __table_args__ = (
        Index('idx_search_query_session', 'session_id'),
        Index('idx_search_query_user', 'user_id'),
        Index('idx_search_query_time', 'query_timestamp'),
        Index('idx_search_query_index', 'index_name'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True)
    session_id = db.Column(db.String(128), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    
    # Query details
    query_text = db.Column(db.Text, nullable=False)
    query_type = db.Column(db.String(50), default='text')  # text, phrase, wildcard, fuzzy, boolean
    index_name = db.Column(db.String(100), nullable=False, index=True)
    filters = db.Column(db.JSON)  # Applied filters
    sort_options = db.Column(db.JSON)  # Sort options
    pagination = db.Column(db.JSON)  # Pagination info
    
    # Query results
    total_results = db.Column(db.Integer, default=0)
    result_count = db.Column(db.Integer, default=0)  # Actual results returned
    max_score = db.Column(db.Float, default=0.0)
    
    # Performance metrics
    query_time_ms = db.Column(db.Float, default=0.0)  # Elasticsearch query time
    total_time_ms = db.Column(db.Float, default=0.0)  # Total processing time
    cache_hit = db.Column(db.Boolean, default=False)
    
    # User behavior
    clicked_results = db.Column(db.JSON)  # Which results were clicked
    query_success = db.Column(db.Boolean, default=True)  # Did user find what they wanted
    abandoned = db.Column(db.Boolean, default=False)  # Did user abandon search
    
    # Context information
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    query_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = db.relationship('User', backref='search_queries', lazy=True)
    
    def __repr__(self):
        return f'<SearchQuery {self.query_id[:8]}...:{self.query_text[:50]}>'
    
    @classmethod
    def track_query(cls, query_text, index_name, query_type='text', session_id=None, user_id=None,
                   filters=None, sort_options=None, pagination=None, total_results=0,
                   result_count=0, max_score=0.0, query_time_ms=0.0, total_time_ms=0.0,
                   cache_hit=False, ip_address=None, user_agent=None, referrer=None):
        """Track a search query"""
        search_query = cls(
            query_text=query_text,
            query_type=query_type,
            index_name=index_name,
            session_id=session_id,
            user_id=user_id,
            filters=filters or {},
            sort_options=sort_options or {},
            pagination=pagination or {},
            total_results=total_results,
            result_count=result_count,
            max_score=max_score,
            query_time_ms=query_time_ms,
            total_time_ms=total_time_ms,
            cache_hit=cache_hit,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer
        )
        db.session.add(search_query)
        db.session.commit()
        return search_query
    
    @classmethod
    def get_popular_queries(cls, index_name=None, hours=24, limit=10):
        """Get popular search queries"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.session.query(
            cls.query_text,
            sql_func.count(cls.id).label('count'),
            sql_func.avg(cls.result_count).label('avg_results'),
            sql_func.avg(cls.query_time_ms).label('avg_time')
        ).filter(cls.query_timestamp >= start_time)
        
        if index_name:
            query = query.filter_by(index_name=index_name)
        
        results = query.group_by(cls.query_text).order_by(
            sql_func.count(cls.id).desc()
        ).limit(limit).all()
        
        return [
            {
                'query': query_text,
                'count': count,
                'avg_results': float(avg_results) if avg_results else 0,
                'avg_time_ms': float(avg_time) if avg_time else 0
            }
            for query_text, count, avg_results, avg_time in results
        ]
    
    @classmethod
    def get_no_result_queries(cls, index_name=None, hours=24, limit=10):
        """Get queries with no results"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.session.query(
            cls.query_text,
            sql_func.count(cls.id).label('count')
        ).filter(
            cls.query_timestamp >= start_time,
            cls.result_count == 0
        )
        
        if index_name:
            query = query.filter_by(index_name=index_name)
        
        results = query.group_by(cls.query_text).order_by(
            sql_func.count(cls.id).desc()
        ).limit(limit).all()
        
        return [
            {
                'query': query_text,
                'count': count
            }
            for query_text, count in results
        ]
    
    @classmethod
    def get_query_analytics(cls, index_name=None, hours=24):
        """Get search query analytics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = cls.query.filter(cls.query_timestamp >= start_time)
        
        if index_name:
            query = query.filter_by(index_name=index_name)
        
        total_queries = query.count()
        queries_with_results = query.filter(cls.result_count > 0).count()
        avg_query_time = query.with_entities(sql_func.avg(cls.query_time_ms)).scalar() or 0
        avg_total_time = query.with_entities(sql_func.avg(cls.total_time_ms)).scalar() or 0
        cache_hit_rate = query.filter_by(cache_hit=True).count() / max(total_queries, 1)
        
        return {
            'total_queries': total_queries,
            'queries_with_results': queries_with_results,
            'success_rate': (queries_with_results / max(total_queries, 1)) * 100,
            'avg_query_time_ms': float(avg_query_time),
            'avg_total_time_ms': float(avg_total_time),
            'cache_hit_rate': cache_hit_rate * 100,
            'period_hours': hours
        }
    
    def update_results(self, clicked_results=None, query_success=None, abandoned=None):
        """Update query results and user behavior"""
        if clicked_results is not None:
            self.clicked_results = clicked_results
        if query_success is not None:
            self.query_success = query_success
        if abandoned is not None:
            self.abandoned = abandoned
        
        db.session.commit()
    
    def to_dict(self):
        """Convert query to dictionary"""
        return {
            'query_id': self.query_id,
            'query_text': self.query_text,
            'query_type': self.query_type,
            'index_name': self.index_name,
            'total_results': self.total_results,
            'result_count': self.result_count,
            'max_score': self.max_score,
            'query_time_ms': self.query_time_ms,
            'total_time_ms': self.total_time_ms,
            'cache_hit': self.cache_hit,
            'query_success': self.query_success,
            'abandoned': self.abandoned,
            'query_timestamp': self.query_timestamp.isoformat()
        }


class SearchAnalytics(db.Model):
    """Search performance metrics and analytics model"""
    __tablename__ = 'search_analytics'
    __table_args__ = (
        Index('idx_search_analytics_time', 'analytics_timestamp'),
        Index('idx_search_analytics_index', 'index_name'),
        Index('idx_search_analytics_metric', 'metric_type'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    index_name = db.Column(db.String(100), nullable=False, index=True)
    metric_type = db.Column(db.String(50), nullable=False, index=True)  # query_time, cache_hit, result_count, etc.
    metric_value = db.Column(db.Float, nullable=False)
    metric_unit = db.Column(db.String(20), nullable=True)  # ms, percent, count, etc.
    
    # Aggregation period
    aggregation_period = db.Column(db.String(20), default='hourly')  # hourly, daily, weekly, monthly
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    
    # Additional metrics
    sample_count = db.Column(db.Integer, default=0)  # Number of samples in this aggregation
    min_value = db.Column(db.Float, nullable=True)
    max_value = db.Column(db.Float, nullable=True)
    percentile_95 = db.Column(db.Float, nullable=True)
    percentile_99 = db.Column(db.Float, nullable=True)
    
    # Timestamps
    analytics_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Metadata
    analytics_metadata = db.Column(db.JSON)  # Additional analytics metadata
    
    def __repr__(self):
        return f'<SearchAnalytics {self.index_name}:{self.metric_type}:{self.metric_value}>'
    
    @classmethod
    def record_metric(cls, index_name, metric_type, metric_value, metric_unit=None,
                      aggregation_period='hourly', period_start=None, period_end=None,
                      sample_count=1, min_value=None, max_value=None, percentile_95=None,
                      percentile_99=None, metadata=None):
        """Record a search analytics metric"""
        # Set default period if not provided
        if not period_start:
            if aggregation_period == 'hourly':
                period_start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
                period_end = period_start + timedelta(hours=1)
            elif aggregation_period == 'daily':
                period_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                period_end = period_start + timedelta(days=1)
            elif aggregation_period == 'weekly':
                period_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                period_start = period_start - timedelta(days=period_start.weekday())
                period_end = period_start + timedelta(weeks=1)
            elif aggregation_period == 'monthly':
                period_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                period_end = period_start + timedelta(days=30)
            else:
                period_start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
                period_end = period_start + timedelta(hours=1)
        
        # Check if metric already exists for this period
        existing = cls.query.filter_by(
            index_name=index_name,
            metric_type=metric_type,
            aggregation_period=aggregation_period,
            period_start=period_start
        ).first()
        
        if existing:
            # Update existing metric (aggregate)
            existing.sample_count += sample_count
            existing.metric_value = (existing.metric_value * (existing.sample_count - sample_count) + metric_value * sample_count) / existing.sample_count
            
            if min_value is not None and (existing.min_value is None or min_value < existing.min_value):
                existing.min_value = min_value
            if max_value is not None and (existing.max_value is None or max_value > existing.max_value):
                existing.max_value = max_value
            if percentile_95 is not None:
                existing.percentile_95 = percentile_95
            if percentile_99 is not None:
                existing.percentile_99 = percentile_99
            
            existing.analytics_timestamp = datetime.utcnow()
            db.session.commit()
            return existing
        else:
            # Create new metric
            analytics = cls(
                index_name=index_name,
                metric_type=metric_type,
                metric_value=metric_value,
                metric_unit=metric_unit,
                aggregation_period=aggregation_period,
                period_start=period_start,
                period_end=period_end,
                sample_count=sample_count,
                min_value=min_value or metric_value,
                max_value=max_value or metric_value,
                percentile_95=percentile_95 or metric_value,
                percentile_99=percentile_99 or metric_value,
                analytics_metadata=metadata or {}
            )
            db.session.add(analytics)
            db.session.commit()
            return analytics
    
    @classmethod
    def get_metrics(cls, index_name=None, metric_type=None, aggregation_period='hourly',
                    start_date=None, end_date=None, limit=None):
        """Get analytics metrics"""
        query = cls.query.filter_by(aggregation_period=aggregation_period)
        
        if index_name:
            query = query.filter_by(index_name=index_name)
        
        if metric_type:
            query = query.filter_by(metric_type=metric_type)
        
        if start_date:
            query = query.filter(cls.period_start >= start_date)
        
        if end_date:
            query = query.filter(cls.period_end <= end_date)
        
        return query.order_by(cls.period_start.desc()).limit(limit).all()
    
    @classmethod
    def get_performance_summary(cls, index_name=None, hours=24):
        """Get performance summary for search indices"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = cls.query.filter(
            cls.period_start >= start_time,
            cls.aggregation_period == 'hourly'
        )
        
        if index_name:
            query = query.filter_by(index_name=index_name)
        
        metrics = query.all()
        
        summary = {
            'avg_query_time_ms': 0.0,
            'avg_cache_hit_rate': 0.0,
            'avg_result_count': 0.0,
            'total_queries': 0,
            'peak_query_time_ms': 0.0,
            'slow_queries_count': 0
        }
        
        query_times = []
        cache_rates = []
        result_counts = []
        
        for metric in metrics:
            if metric.metric_type == 'query_time':
                query_times.append(metric.metric_value)
                if metric.metric_value > summary['peak_query_time_ms']:
                    summary['peak_query_time_ms'] = metric.metric_value
                if metric.metric_value > 1000:  # Consider queries > 1s as slow
                    summary['slow_queries_count'] += metric.sample_count
            elif metric.metric_type == 'cache_hit_rate':
                cache_rates.append(metric.metric_value)
            elif metric.metric_type == 'result_count':
                result_counts.append(metric.metric_value)
            elif metric.metric_type == 'query_count':
                summary['total_queries'] += metric.metric_value
        
        if query_times:
            summary['avg_query_time_ms'] = sum(query_times) / len(query_times)
        if cache_rates:
            summary['avg_cache_hit_rate'] = sum(cache_rates) / len(cache_rates)
        if result_counts:
            summary['avg_result_count'] = sum(result_counts) / len(result_counts)
        
        return summary
    
    def to_dict(self):
        """Convert analytics to dictionary"""
        return {
            'index_name': self.index_name,
            'metric_type': self.metric_type,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'aggregation_period': self.aggregation_period,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'sample_count': self.sample_count,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'percentile_95': self.percentile_95,
            'percentile_99': self.percentile_99,
            'analytics_timestamp': self.analytics_timestamp.isoformat()
        }


class SearchOptimization(db.Model):
    """Search optimization data model"""
    __tablename__ = 'search_optimization'
    __table_args__ = (
        Index('idx_search_optimization_index', 'index_name'),
        Index('idx_search_optimization_type', 'optimization_type'),
        Index('idx_search_optimization_status', 'status'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    index_name = db.Column(db.String(100), nullable=False, index=True)
    optimization_type = db.Column(db.String(50), nullable=False, index=True)  # mapping, settings, analyzer, synonym
    status = db.Column(db.String(20), default='pending', index=True)  # pending, applied, failed, rolled_back
    
    # Optimization details
    optimization_data = db.Column(db.JSON)  # The optimization configuration
    previous_config = db.Column(db.JSON)  # Previous configuration for rollback
    applied_config = db.Column(db.JSON)  # Actually applied configuration
    
    # Performance impact
    performance_before = db.Column(db.JSON)  # Performance metrics before optimization
    performance_after = db.Column(db.JSON)  # Performance metrics after optimization
    improvement_percent = db.Column(db.Float, default=0.0)  # Performance improvement percentage
    
    # Optimization metadata
    reason = db.Column(db.Text)  # Why this optimization was applied
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    auto_generated = db.Column(db.Boolean, default=False)  # Was this auto-generated?
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applied_at = db.Column(db.DateTime)
    evaluated_at = db.Column(db.DateTime)
    
    # Evaluation results
    success_score = db.Column(db.Float)  # 0-100 score of optimization success
    issues = db.Column(db.JSON)  # Issues found during evaluation
    
    # Metadata
    optimization_metadata = db.Column(db.JSON)  # Additional optimization metadata
    
    def __repr__(self):
        return f'<SearchOptimization {self.index_name}:{self.optimization_type}>'
    
    @classmethod
    def create_optimization(cls, index_name, optimization_type, optimization_data,
                           reason=None, priority='medium', auto_generated=False, metadata=None):
        """Create a search optimization"""
        optimization = cls(
            index_name=index_name,
            optimization_type=optimization_type,
            optimization_data=optimization_data,
            reason=reason,
            priority=priority,
            auto_generated=auto_generated,
            optimization_metadata=metadata or {}
        )
        db.session.add(optimization)
        db.session.commit()
        return optimization
    
    @classmethod
    def get_pending_optimizations(cls, index_name=None):
        """Get pending optimizations"""
        query = cls.query.filter_by(status='pending')
        
        if index_name:
            query = query.filter_by(index_name=index_name)
        
        return query.order_by(cls.priority.desc(), cls.created_at.asc()).all()
    
    @classmethod
    def get_optimization_history(cls, index_name=None, optimization_type=None, limit=20):
        """Get optimization history"""
        query = cls.query
        
        if index_name:
            query = query.filter_by(index_name=index_name)
        
        if optimization_type:
            query = query.filter_by(optimization_type=optimization_type)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    def apply_optimization(self, applied_config=None):
        """Mark optimization as applied"""
        self.status = 'applied'
        self.applied_at = datetime.utcnow()
        if applied_config:
            self.applied_config = applied_config
        db.session.commit()
    
    def mark_failed(self, issues=None):
        """Mark optimization as failed"""
        self.status = 'failed'
        self.issues = issues or []
        self.evaluated_at = datetime.utcnow()
        db.session.commit()
    
    def evaluate_optimization(self, performance_before, performance_after, success_score=None):
        """Evaluate optimization results"""
        self.performance_before = performance_before
        self.performance_after = performance_after
        self.success_score = success_score
        self.evaluated_at = datetime.utcnow()
        
        # Calculate improvement percentage
        if performance_before and performance_after:
            before_time = performance_before.get('avg_query_time_ms', 0)
            after_time = performance_after.get('avg_query_time_ms', 0)
            if before_time > 0:
                self.improvement_percent = ((before_time - after_time) / before_time) * 100
        
        db.session.commit()
    
    def rollback_optimization(self):
        """Rollback optimization"""
        self.status = 'rolled_back'
        self.evaluated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert optimization to dictionary"""
        return {
            'id': self.id,
            'index_name': self.index_name,
            'optimization_type': self.optimization_type,
            'status': self.status,
            'priority': self.priority,
            'auto_generated': self.auto_generated,
            'improvement_percent': self.improvement_percent,
            'success_score': self.success_score,
            'reason': self.reason,
            'created_at': self.created_at.isoformat(),
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'evaluated_at': self.evaluated_at.isoformat() if self.evaluated_at else None
        }
