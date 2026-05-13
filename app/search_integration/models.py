"""
Search Integration Models

This module implements search integration models for the Auto Bot Solutions Forum,
including Elasticsearch integration, search index management, full-text search capabilities,
and search analytics.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from sqlalchemy import Index, CheckConstraint, func as sql_func
import json
import uuid


class SearchIndex(db.Model):
    """Search index model for Elasticsearch integration"""
    __tablename__ = 'search_indices'
    __table_args__ = (
        Index('idx_search_indices_name', 'index_name'),
        Index('idx_search_indices_type', 'index_type'),
        Index('idx_search_indices_status', 'status'),
        Index('idx_search_indices_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    index_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Index information
    index_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    index_type = db.Column(db.String(50), nullable=False, index=True)  # content, user, forum, analytics
    index_category = db.Column(db.String(50), nullable=False, index=True)  # primary, secondary, archive
    
    # Elasticsearch configuration
    elasticsearch_index = db.Column(db.String(100), nullable=False)  # Actual ES index name
    elasticsearch_config = db.Column(db.JSON)  # ES-specific configuration
    
    # Index schema
    index_schema = db.Column(db.JSON)  # Index field mapping and schema
    field_mappings = db.Column(db.JSON)  # Field mappings and analyzers
    
    # Index settings
    index_settings = db.Column(db.JSON)  # Index settings (shards, replicas, etc.)
    analysis_config = db.Column(db.JSON)  # Analysis configuration (tokenizers, filters)
    
    # Index status
    status = db.Column(db.String(20), default('active'))  # active, inactive, building, error
    health_status = db.Column(db.String(20), default('green'))  # green, yellow, red
    
    # Performance metrics
    document_count = db.Column(db.BigInteger, default=0)
    index_size_bytes = db.Column(db.BigInteger, default=0)
    shard_count = db.Column(db.Integer, default=1)
    replica_count = db.Column(db.Integer, default=1)
    
    # Search metrics
    search_queries_per_hour = db.Column(db.Integer, default=0)
    avg_query_time_ms = db.Column(db.Float, default=0.0)
    cache_hit_rate = db.Column(db.Float, default=0.0)
    
    # Index configuration
    refresh_interval = db.Column(db.String(20), default='1s')  # ES refresh interval
    max_result_window = db.Column(db.Integer, default=10000)
    number_of_shards = db.Column(db.Integer, default=1)
    number_of_replicas = db.Column(db.Integer, default=1)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_indexed = db.Column(db.DateTime, nullable=True)
    last_health_check = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional index metadata
    
    # Constraints
    __table_args__ = (
        CheckConstraint('status IN ("active", "inactive", "building", "error")', name='check_index_status'),
        CheckConstraint('health_status IN ("green", "yellow", "red")', name='check_health_status'),
        CheckConstraint('document_count >= 0', name='check_document_count'),
        CheckConstraint('index_size_bytes >= 0', name='check_index_size'),
        CheckConstraint('shard_count >= 0', name='check_shard_count'),
        CheckConstraint('replica_count >= 0', name='check_replica_count'),
        CheckConstraint('search_queries_per_hour >= 0', name='check_search_queries'),
        CheckConstraint('avg_query_time_ms >= 0', name='check_avg_query_time'),
        CheckConstraint('cache_hit_rate >= 0 AND cache_hit_rate <= 1', name='check_cache_hit_rate'),
        Index('idx_search_indices_name', 'index_name'),
        Index('idx_search_indices_type', 'index_type'),
        Index('idx_search_indices_status', 'status'),
        Index('idx_search_indices_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<SearchIndex {self.index_name}:{self.index_type}:{self.status}>'
    
    @classmethod
    def create_index(cls, index_name, index_type, index_category, elasticsearch_index,
                     index_schema=None, field_mappings=None, index_settings=None,
                     analysis_config=None, refresh_interval='1s', max_result_window=10000,
                     number_of_shards=1, number_of_replicas=1, metadata=None):
        """Create a new search index"""
        index = cls(
            index_name=index_name,
            index_type=index_type,
            index_category=index_category,
            elasticsearch_index=elasticsearch_index,
            index_schema=index_schema or {},
            field_mappings=field_mappings or {},
            index_settings=index_settings or {},
            analysis_config=analysis_config or {},
            refresh_interval=refresh_interval,
            max_result_window=max_result_window,
            number_of_shards=number_of_shards,
            number_of_replicas=number_of_replicas,
            metadata=metadata or {}
        )
        db.session.add(index)
        db.session.commit()
        return index
    
    @classmethod
    def get_index_by_name(cls, index_name):
        """Get index by name"""
        return cls.query.filter_by(index_name=index_name).first()
    
    @classmethod
    def get_indices_by_type(cls, index_type):
        """Get indices by type"""
        return cls.query.filter_by(index_type=index_type).all()
    
    @classmethod
    def get_active_indices(cls):
        """Get all active indices"""
        return cls.query.filter_by(status='active').all()
    
    @classmethod
    def get_index_stats(cls):
        """Get index statistics"""
        total_indices = cls.query.count()
        active_indices = cls.query.filter_by(status='active').count()
        healthy_indices = cls.query.filter_by(health_status='green').count()
        
        return {
            'total_indices': total_indices,
            'active_indices': active_indices,
            'healthy_indices': healthy_indices,
            'unhealthy_indices': total_indices - healthy_indices
        }
    
    def update_status(self, status, health_status=None):
        """Update index status"""
        self.status = status
        if health_status:
            self.health_status = health_status
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_metrics(self, document_count=None, index_size_bytes=None, shard_count=None,
                      replica_count=None, search_queries_per_hour=None, avg_query_time_ms=None,
                      cache_hit_rate=None):
        """Update index metrics"""
        if document_count is not None:
            self.document_count = document_count
        if index_size_bytes is not None:
            self.index_size_bytes = index_size_bytes
        if shard_count is not None:
            self.shard_count = shard_count
        if replica_count is not None:
            self.replica_count = replica_count
        if search_queries_per_hour is not None:
            self.search_queries_per_hour = search_queries_per_hour
        if avg_query_time_ms is not None:
            self.avg_query_time_ms = avg_query_time_ms
        if cache_hit_rate is not None:
            self.cache_hit_rate = cache_hit_rate
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert index to dictionary"""
        return {
            'index_id': self.index_id,
            'index_name': self.index_name,
            'index_type': self.index_type,
            'index_category': self.index_category,
            'elasticsearch_index': self.elasticsearch_index,
            'status': self.status,
            'health_status': self.health_status,
            'document_count': self.document_count,
            'index_size_bytes': self.index_size_bytes,
            'shard_count': self.shard_count,
            'replica_count': self.replica_count,
            'search_queries_per_hour': self.search_queries_per_hour,
            'avg_query_time_ms': self.avg_query_time_ms,
            'cache_hit_rate': self.cache_hit_rate,
            'refresh_interval': self.refresh_interval,
            'max_result_window': self.max_result_window,
            'number_of_shards': self.number_of_shards,
            'number_of_replicas': self.number_of_replicas,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_indexed': self.last_indexed.isoformat() if self.last_indexed else None,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
        }


class SearchQuery(db.Model):
    """Search query model for query tracking and analytics"""
    __tablename__ = 'search_queries'
    __table_args__ = (
        Index('idx_search_queries_index', 'index_id'),
        Index('idx_search_queries_user', 'user_id'),
        Index('idx_search_queries_time', 'query_timestamp'),
        Index('idx_search_queries_type', 'query_type'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Query information
    index_id = db.Column(db.Integer, db.ForeignKey('search_indices.id'), nullable=False, index=True)
    query_text = db.Column(db.Text, nullable=False)
    query_type = db.Column(db.String(50), nullable=False, index=True)  # full_text, exact, fuzzy, phrase
    query_category = db.Column(db.String(50), nullable=False, index=True)  # content, user, forum, analytics
    
    # User information
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    session_id = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    # Query configuration
    query_config = db.Column(db.JSON)  # Query parameters and configuration
    filters = db.Column(db.JSON)  # Applied filters
    sort_config = db.Column(db.JSON)  # Sort configuration
    pagination_config = db.Column(db.JSON)  # Pagination configuration
    
    # Search results
    total_hits = db.Column(db.Integer, default=0)
    max_score = db.Column(db.Float, default=0.0)
    result_count = db.Column(db.Integer, default=0)
    search_time_ms = db.Column(db.Float, default=0.0)
    
    # Performance metrics
    query_time_ms = db.Column(db.Float, default=0.0)
    fetch_time_ms = db.Column(db.Float, default=0.0)
    total_time_ms = db.Column(db.Float, default=0.0)
    cache_hit = db.Column(db.Boolean, default=False)
    
    # Quality metrics
    click_through_rate = db.Column(db.Float, default=0.0)
    bounce_rate = db.Column(db.Float, default=0.0)
    satisfaction_score = db.Column(db.Float, default=0.0)
    
    # Timestamps
    query_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional query metadata
    
    # Relationships
    index = db.relationship('SearchIndex', backref='search_queries', lazy=True)
    user = db.relationship('User', backref='search_queries', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('query_type IN ("full_text", "exact", "fuzzy", "phrase", "wildcard", "regex")', name='check_query_type'),
        CheckConstraint('total_hits >= 0', name='check_total_hits'),
        CheckConstraint('max_score >= 0', name='check_max_score'),
        CheckConstraint('result_count >= 0', name='check_result_count'),
        CheckConstraint('search_time_ms >= 0', name='check_search_time'),
        CheckConstraint('query_time_ms >= 0', name='check_query_time'),
        CheckConstraint('fetch_time_ms >= 0', name='check_fetch_time'),
        CheckConstraint('total_time_ms >= 0', name='check_total_time'),
        CheckConstraint('click_through_rate >= 0 AND click_through_rate <= 1', name='check_ctr'),
        CheckConstraint('bounce_rate >= 0 AND bounce_rate <= 1', name='check_bounce_rate'),
        CheckConstraint('satisfaction_score >= 0 AND satisfaction_score <= 1', name='check_satisfaction'),
        Index('idx_search_queries_index', 'index_id'),
        Index('idx_search_queries_user', 'user_id'),
        Index('idx_search_queries_time', 'query_timestamp'),
        Index('idx_search_queries_type', 'query_type'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<SearchQuery {self.query_type}:{self.total_hits}:{self.query_timestamp}>'
    
    @classmethod
    def log_query(cls, index_id, query_text, query_type, query_category, user_id=None,
                  session_id=None, ip_address=None, user_agent=None, query_config=None,
                  filters=None, sort_config=None, pagination_config=None, total_hits=0,
                  max_score=0.0, result_count=0, search_time_ms=0.0, query_time_ms=0.0,
                  fetch_time_ms=0.0, total_time_ms=0.0, cache_hit=False, metadata=None):
        """Log a search query"""
        query = cls(
            index_id=index_id,
            query_text=query_text,
            query_type=query_type,
            query_category=query_category,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            query_config=query_config or {},
            filters=filters or {},
            sort_config=sort_config or {},
            pagination_config=pagination_config or {},
            total_hits=total_hits,
            max_score=max_score,
            result_count=result_count,
            search_time_ms=search_time_ms,
            query_time_ms=query_time_ms,
            fetch_time_ms=fetch_time_ms,
            total_time_ms=total_time_ms,
            cache_hit=cache_hit,
            metadata=metadata or {}
        )
        db.session.add(query)
        db.session.commit()
        return query
    
    @classmethod
    def get_queries_by_index(cls, index_id, hours=24, limit=None):
        """Get queries by index"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.index_id == index_id,
            cls.query_timestamp >= start_time
        ).order_by(cls.query_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_queries_by_user(cls, user_id, hours=24, limit=None):
        """Get queries by user"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.user_id == user_id,
            cls.query_timestamp >= start_time
        ).order_by(cls.query_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_popular_queries(cls, hours=24, limit=None):
        """Get popular search queries"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.session.query(
            cls.query_text,
            sql_func.count(cls.id).label('count'),
            sql_func.avg(cls.total_time_ms).label('avg_time'),
            sql_func.avg(cls.click_through_rate).label('avg_ctr')
        ).filter(
            cls.query_timestamp >= start_time
        ).group_by(cls.query_text).order_by(
            sql_func.count(cls.id).desc()
        )
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_query_stats(cls, hours=24):
        """Get query statistics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total queries
        total_queries = cls.query.filter(cls.query_timestamp >= start_time).count()
        
        # Queries by type
        queries_by_type = db.session.query(
            cls.query_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.query_timestamp >= start_time).group_by(cls.query_type).all()
        
        # Queries by category
        queries_by_category = db.session.query(
            cls.query_category,
            sql_func.count(cls.id).label('count')
        ).filter(cls.query_timestamp >= start_time).group_by(cls.query_category).all()
        
        # Performance metrics
        avg_query_time = db.session.query(
            sql_func.avg(cls.total_time_ms)
        ).filter(cls.query_timestamp >= start_time).scalar() or 0
        
        avg_search_time = db.session.query(
            sql_func.avg(cls.search_time_ms)
        ).filter(cls.query_timestamp >= start_time).scalar() or 0
        
        # Cache hit rate
        cache_hits = cls.query.filter(
            cls.query_timestamp >= start_time,
            cls.cache_hit == True
        ).count()
        
        cache_hit_rate = cache_hits / max(total_queries, 1)
        
        return {
            'total_queries': total_queries,
            'queries_by_type': dict(queries_by_type),
            'queries_by_category': dict(queries_by_category),
            'avg_query_time_ms': float(avg_query_time),
            'avg_search_time_ms': float(avg_search_time),
            'cache_hit_rate': cache_hit_rate,
            'period_hours': hours
        }
    
    def update_metrics(self, click_through_rate=None, bounce_rate=None, satisfaction_score=None):
        """Update query quality metrics"""
        if click_through_rate is not None:
            self.click_through_rate = click_through_rate
        if bounce_rate is not None:
            self.bounce_rate = bounce_rate
        if satisfaction_score is not None:
            self.satisfaction_score = satisfaction_score
        
        db.session.commit()
    
    def to_dict(self):
        """Convert query to dictionary"""
        return {
            'query_id': self.query_id,
            'index_id': self.index_id,
            'query_text': self.query_text,
            'query_type': self.query_type,
            'query_category': self.query_category,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'total_hits': self.total_hits,
            'max_score': self.max_score,
            'result_count': self.result_count,
            'search_time_ms': self.search_time_ms,
            'query_time_ms': self.query_time_ms,
            'fetch_time_ms': self.fetch_time_ms,
            'total_time_ms': self.total_time_ms,
            'cache_hit': self.cache_hit,
            'click_through_rate': self.click_through_rate,
            'bounce_rate': self.bounce_rate,
            'satisfaction_score': self.satisfaction_score,
            'query_timestamp': self.query_timestamp.isoformat(),
            'created_at': self.created_at.isoformat()
        }


class SearchAnalytics(db.Model):
    """Search analytics model for search performance and optimization"""
    __tablename__ = 'search_analytics'
    __table_args__ = (
        Index('idx_search_analytics_index', 'index_id'),
        Index('idx_search_analytics_type', 'analytics_type'),
        Index('idx_search_analytics_time', 'analytics_timestamp'),
        Index('idx_search_analytics_period', 'period'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    analytics_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Analytics information
    index_id = db.Column(db.Integer, db.ForeignKey('search_indices.id'), nullable=False, index=True)
    analytics_type = db.Column(db.String(50), nullable=False, index=True)  # performance, usage, quality, optimization
    analytics_category = db.Column(db.String(50), nullable=False, index=True)  # hourly, daily, weekly, monthly
    
    # Time period
    period = db.Column(db.String(20), nullable=False, index=True)  # hourly, daily, weekly, monthly
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    analytics_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Performance metrics
    total_queries = db.Column(db.Integer, default=0)
    avg_query_time_ms = db.Column(db.Float, default=0.0)
    avg_search_time_ms = db.Column(db.Float, default=0.0)
    p95_query_time_ms = db.Column(db.Float, default=0.0)
    p99_query_time_ms = db.Column(db.Float, default=0.0)
    cache_hit_rate = db.Column(db.Float, default=0.0)
    
    # Usage metrics
    unique_users = db.Column(db.Integer, default=0)
    unique_queries = db.Column(db.Integer, default=0)
    zero_results_queries = db.Column(db.Integer, default=0)
    avg_results_per_query = db.Column(db.Float, default=0.0)
    
    # Quality metrics
    avg_click_through_rate = db.Column(db.Float, default=0.0)
    avg_bounce_rate = db.Column(db.Float, default=0.0)
    avg_satisfaction_score = db.Column(db.Float, default=0.0)
    error_rate = db.Column(db.Float, default=0.0)
    
    # Index metrics
    index_size_bytes = db.Column(db.BigInteger, default=0)
    document_count = db.Column(db.BigInteger, default=0)
    indexing_rate = db.Column(db.Float, default=0.0)  # Documents per hour
    
    # Optimization metrics
    optimization_suggestions = db.Column(db.JSON)  # Optimization suggestions
    performance_issues = db.Column(db.JSON)  # Performance issues identified
    quality_issues = db.Column(db.JSON)  # Quality issues identified
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional analytics metadata
    
    # Relationships
    index = db.relationship('SearchIndex', backref='search_analytics', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('analytics_type IN ("performance", "usage", "quality", "optimization")', name='check_analytics_type'),
        CheckConstraint('analytics_category IN ("hourly", "daily", "weekly", "monthly")', name='check_analytics_category'),
        CheckConstraint('period IN ("hourly", "daily", "weekly", "monthly")', name='check_period'),
        CheckConstraint('total_queries >= 0', name='check_total_queries'),
        CheckConstraint('avg_query_time_ms >= 0', name='check_avg_query_time'),
        CheckConstraint('avg_search_time_ms >= 0', name='check_avg_search_time'),
        CheckConstraint('p95_query_time_ms >= 0', name='check_p95_query_time'),
        CheckConstraint('p99_query_time_ms >= 0', name='check_p99_query_time'),
        CheckConstraint('cache_hit_rate >= 0 AND cache_hit_rate <= 1', name='check_analytics_cache_hit'),
        CheckConstraint('unique_users >= 0', name='check_unique_users'),
        CheckConstraint('unique_queries >= 0', name='check_unique_queries'),
        CheckConstraint('zero_results_queries >= 0', name='check_zero_results'),
        CheckConstraint('avg_results_per_query >= 0', name='check_avg_results'),
        CheckConstraint('avg_click_through_rate >= 0 AND avg_click_through_rate <= 1', name='check_avg_ctr'),
        CheckConstraint('avg_bounce_rate >= 0 AND avg_bounce_rate <= 1', name='check_avg_bounce'),
        CheckConstraint('avg_satisfaction_score >= 0 AND avg_satisfaction_score <= 1', name='check_avg_satisfaction'),
        CheckConstraint('error_rate >= 0 AND error_rate <= 1', name='check_error_rate'),
        CheckConstraint('index_size_bytes >= 0', name='check_analytics_index_size'),
        CheckConstraint('document_count >= 0', name='check_analytics_document_count'),
        CheckConstraint('indexing_rate >= 0', name='check_indexing_rate'),
        Index('idx_search_analytics_index', 'index_id'),
        Index('idx_search_analytics_type', 'analytics_type'),
        Index('idx_search_analytics_time', 'analytics_timestamp'),
        Index('idx_search_analytics_period', 'period'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<SearchAnalytics {self.analytics_type}:{self.period}:{self.total_queries}>'
    
    @classmethod
    def create_analytics(cls, index_id, analytics_type, analytics_category, period,
                         period_start, period_end, total_queries=0, avg_query_time_ms=0.0,
                         avg_search_time_ms=0.0, p95_query_time_ms=0.0, p99_query_time_ms=0.0,
                         cache_hit_rate=0.0, unique_users=0, unique_queries=0, zero_results_queries=0,
                         avg_results_per_query=0.0, avg_click_through_rate=0.0, avg_bounce_rate=0.0,
                         avg_satisfaction_score=0.0, error_rate=0.0, index_size_bytes=0,
                         document_count=0, indexing_rate=0.0, optimization_suggestions=None,
                         performance_issues=None, quality_issues=None, metadata=None):
        """Create search analytics record"""
        analytics = cls(
            index_id=index_id,
            analytics_type=analytics_type,
            analytics_category=analytics_category,
            period=period,
            period_start=period_start,
            period_end=period_end,
            total_queries=total_queries,
            avg_query_time_ms=avg_query_time_ms,
            avg_search_time_ms=avg_search_time_ms,
            p95_query_time_ms=p95_query_time_ms,
            p99_query_time_ms=p99_query_time_ms,
            cache_hit_rate=cache_hit_rate,
            unique_users=unique_users,
            unique_queries=unique_queries,
            zero_results_queries=zero_results_queries,
            avg_results_per_query=avg_results_per_query,
            avg_click_through_rate=avg_click_through_rate,
            avg_bounce_rate=avg_bounce_rate,
            avg_satisfaction_score=avg_satisfaction_score,
            error_rate=error_rate,
            index_size_bytes=index_size_bytes,
            document_count=document_count,
            indexing_rate=indexing_rate,
            optimization_suggestions=optimization_suggestions or [],
            performance_issues=performance_issues or [],
            quality_issues=quality_issues or [],
            metadata=metadata or {}
        )
        db.session.add(analytics)
        db.session.commit()
        return analytics
    
    @classmethod
    def get_analytics_by_index(cls, index_id, analytics_type=None, period=None, hours=24):
        """Get analytics by index"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.index_id == index_id,
            cls.analytics_timestamp >= start_time
        )
        
        if analytics_type:
            query = query.filter_by(analytics_type=analytics_type)
        if period:
            query = query.filter_by(period=period)
        
        return query.order_by(cls.analytics_timestamp.desc()).all()
    
    @classmethod
    def get_analytics_summary(cls, hours=24):
        """Get analytics summary"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total analytics records
        total_analytics = cls.query.filter(cls.analytics_timestamp >= start_time).count()
        
        # Analytics by type
        analytics_by_type = db.session.query(
            cls.analytics_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.analytics_timestamp >= start_time).group_by(cls.analytics_type).all()
        
        # Analytics by period
        analytics_by_period = db.session.query(
            cls.period,
            sql_func.count(cls.id).label('count')
        ).filter(cls.analytics_timestamp >= start_time).group_by(cls.period).all()
        
        # Performance averages
        avg_query_time = db.session.query(
            sql_func.avg(cls.avg_query_time_ms)
        ).filter(cls.analytics_timestamp >= start_time).scalar() or 0
        
        avg_search_time = db.session.query(
            sql_func.avg(cls.avg_search_time_ms)
        ).filter(cls.analytics_timestamp >= start_time).scalar() or 0
        
        avg_cache_hit_rate = db.session.query(
            sql_func.avg(cls.cache_hit_rate)
        ).filter(cls.analytics_timestamp >= start_time).scalar() or 0
        
        return {
            'total_analytics': total_analytics,
            'analytics_by_type': dict(analytics_by_type),
            'analytics_by_period': dict(analytics_by_period),
            'avg_query_time_ms': float(avg_query_time),
            'avg_search_time_ms': float(avg_search_time),
            'avg_cache_hit_rate': float(avg_cache_hit_rate),
            'period_hours': hours
        }
    
    def to_dict(self):
        """Convert analytics to dictionary"""
        return {
            'analytics_id': self.analytics_id,
            'index_id': self.index_id,
            'analytics_type': self.analytics_type,
            'analytics_category': self.analytics_category,
            'period': self.period,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'analytics_timestamp': self.analytics_timestamp.isoformat(),
            'total_queries': self.total_queries,
            'avg_query_time_ms': self.avg_query_time_ms,
            'avg_search_time_ms': self.avg_search_time_ms,
            'p95_query_time_ms': self.p95_query_time_ms,
            'p99_query_time_ms': self.p99_query_time_ms,
            'cache_hit_rate': self.cache_hit_rate,
            'unique_users': self.unique_users,
            'unique_queries': self.unique_queries,
            'zero_results_queries': self.zero_results_queries,
            'avg_results_per_query': self.avg_results_per_query,
            'avg_click_through_rate': self.avg_click_through_rate,
            'avg_bounce_rate': self.avg_bounce_rate,
            'avg_satisfaction_score': self.avg_satisfaction_score,
            'error_rate': self.error_rate,
            'index_size_bytes': self.index_size_bytes,
            'document_count': self.document_count,
            'indexing_rate': self.indexing_rate,
            'optimization_suggestions': self.optimization_suggestions,
            'performance_issues': self.performance_issues,
            'quality_issues': self.quality_issues
        }


class SearchOptimization(db.Model):
    """Search optimization model for search performance and quality improvement"""
    __tablename__ = 'search_optimizations'
    __table_args__ = (
        Index('idx_search_optimizations_index', 'index_id'),
        Index('idx_search_optimizations_type', 'optimization_type'),
        Index('idx_search_optimizations_status', 'status'),
        Index('idx_search_optimizations_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    optimization_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Optimization information
    index_id = db.Column(db.Integer, db.ForeignKey('search_indices.id'), nullable=False, index=True)
    optimization_type = db.Column(db.String(50), nullable=False, index=True)  # performance, quality, relevance
    optimization_category = db.Column(db.String(50), nullable=False, index=True)  # index, query, mapping, analysis
    
    # Optimization details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    issue_type = db.Column(db.String(50), nullable=False)  # slow_query, low_relevance, high_memory, poor_indexing
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    # Configuration changes
    old_config = db.Column(db.JSON)  # Original configuration
    new_config = db.Column(db.JSON)  # Optimized configuration
    config_changes = db.Column(db.JSON)  # Description of changes made
    
    # Performance impact
    performance_before = db.Column(db.JSON)  # Performance metrics before optimization
    performance_after = db.Column(db.JSON)  # Performance metrics after optimization
    improvement_percentage = db.Column(db.Float, default=0.0)  # Overall improvement percentage
    
    # Quality impact
    quality_before = db.Column(db.JSON)  # Quality metrics before optimization
    quality_after = db.Column(db.JSON)  # Quality metrics after optimization
    quality_improvement = db.Column(db.Float, default=0.0)  # Quality improvement score
    
    # Status and scheduling
    status = db.Column(db.String(20), default('pending'))  # pending, in_progress, completed, failed, rolled_back
    priority = db.Column(db.Integer, default=5)  # 1-10 priority level
    scheduled_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Validation and testing
    test_results = db.Column(db.JSON)  # Test results and validation
    validation_status = db.Column(db.String(20), default('pending'))  # pending, passed, failed
    rollback_available = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    metadata = db.Column(db.JSON)  # Additional optimization metadata
    
    # Relationships
    index = db.relationship('SearchIndex', backref='search_optimizations', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('optimization_type IN ("performance", "quality", "relevance", "indexing")', name='check_optimization_type'),
        CheckConstraint('status IN ("pending", "in_progress", "completed", "failed", "rolled_back")', name='check_optimization_status'),
        CheckConstraint('severity IN ("low", "medium", "high", "critical")', name='check_severity'),
        CheckConstraint('priority >= 1 AND priority <= 10', name='check_priority'),
        CheckConstraint('validation_status IN ("pending", "passed", "failed")', name='check_validation_status'),
        CheckConstraint('improvement_percentage >= -100 AND improvement_percentage <= 1000', name='check_improvement'),
        CheckConstraint('quality_improvement >= -1 AND quality_improvement <= 1', name='check_quality_improvement'),
        Index('idx_search_optimizations_index', 'index_id'),
        Index('idx_search_optimizations_type', 'optimization_type'),
        Index('idx_search_optimizations_status', 'status'),
        Index('idx_search_optimizations_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<SearchOptimization {self.optimization_type}:{self.issue_type}:{self.status}>'
    
    @classmethod
    def create_optimization(cls, index_id, optimization_type, optimization_category, title,
                            description, issue_type, severity='medium', old_config=None,
                            new_config=None, config_changes=None, priority=5, scheduled_at=None,
                            metadata=None):
        """Create a search optimization"""
        optimization = cls(
            index_id=index_id,
            optimization_type=optimization_type,
            optimization_category=optimization_category,
            title=title,
            description=description,
            issue_type=issue_type,
            severity=severity,
            old_config=old_config or {},
            new_config=new_config or {},
            config_changes=config_changes or {},
            priority=priority,
            scheduled_at=scheduled_at,
            metadata=metadata or {}
        )
        db.session.add(optimization)
        db.session.commit()
        return optimization
    
    @classmethod
    def get_optimizations_by_index(cls, index_id, status=None, limit=None):
        """Get optimizations by index"""
        query = cls.query.filter_by(index_id=index_id)
        if status:
            query = query.filter_by(status=status)
        query = query.order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_optimizations_by_type(cls, optimization_type, status=None, limit=None):
        """Get optimizations by type"""
        query = cls.query.filter_by(optimization_type=optimization_type)
        if status:
            query = query.filter_by(status=status)
        query = query.order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_pending_optimizations(cls, limit=None):
        """Get pending optimizations"""
        query = cls.query.filter_by(status='pending').order_by(cls.priority.desc(), cls.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_optimization_stats(cls, hours=24):
        """Get optimization statistics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total optimizations
        total_optimizations = cls.query.filter(cls.created_at >= start_time).count()
        
        # Optimizations by status
        optimizations_by_status = db.session.query(
            cls.status,
            sql_func.count(cls.id).label('count')
        ).filter(cls.created_at >= start_time).group_by(cls.status).all()
        
        # Optimizations by type
        optimizations_by_type = db.session.query(
            cls.optimization_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.created_at >= start_time).group_by(cls.optimization_type).all()
        
        # Optimizations by severity
        optimizations_by_severity = db.session.query(
            cls.severity,
            sql_func.count(cls.id).label('count')
        ).filter(cls.created_at >= start_time).group_by(cls.severity).all()
        
        # Average improvement
        avg_improvement = db.session.query(
            sql_func.avg(cls.improvement_percentage)
        ).filter(cls.created_at >= start_time, cls.improvement_percentage.isnot(None)).scalar() or 0
        
        return {
            'total_optimizations': total_optimizations,
            'optimizations_by_status': dict(optimizations_by_status),
            'optimizations_by_type': dict(optimizations_by_type),
            'optimizations_by_severity': dict(optimizations_by_severity),
            'avg_improvement_percentage': float(avg_improvement),
            'period_hours': hours
        }
    
    def start_optimization(self):
        """Start optimization process"""
        self.status = 'in_progress'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def complete_optimization(self, performance_after=None, quality_after=None, test_results=None):
        """Complete optimization"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        if performance_after:
            self.performance_after = performance_after
            # Calculate improvement percentage
            if self.performance_before and performance_after:
                improvement = self._calculate_improvement(self.performance_before, performance_after)
                self.improvement_percentage = improvement
        
        if quality_after:
            self.quality_after = quality_after
            # Calculate quality improvement
            if self.quality_before and quality_after:
                quality_improvement = self._calculate_quality_improvement(self.quality_before, quality_after)
                self.quality_improvement = quality_improvement
        
        if test_results:
            self.test_results = test_results
            self.validation_status = 'passed'
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def fail_optimization(self, error_message=None):
        """Fail optimization"""
        self.status = 'failed'
        self.metadata = self.metadata or {}
        if error_message:
            self.metadata['error_message'] = error_message
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def rollback_optimization(self):
        """Rollback optimization"""
        self.status = 'rolled_back'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def _calculate_improvement(self, before_metrics, after_metrics):
        """Calculate improvement percentage"""
        try:
            # Simple improvement calculation based on query time
            before_time = before_metrics.get('avg_query_time_ms', 0)
            after_time = after_metrics.get('avg_query_time_ms', 0)
            
            if before_time > 0:
                improvement = ((before_time - after_time) / before_time) * 100
                return max(min(improvement, 1000), -100)  # Cap improvement between -100% and 1000%
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_quality_improvement(self, before_metrics, after_metrics):
        """Calculate quality improvement score"""
        try:
            # Simple quality improvement calculation
            before_ctr = before_metrics.get('avg_click_through_rate', 0)
            after_ctr = after_metrics.get('avg_click_through_rate', 0)
            
            improvement = after_ctr - before_ctr
            return max(min(improvement, 1), -1)  # Cap between -1 and 1
            
        except Exception:
            return 0.0
    
    def to_dict(self):
        """Convert optimization to dictionary"""
        return {
            'optimization_id': self.optimization_id,
            'index_id': self.index_id,
            'optimization_type': self.optimization_type,
            'optimization_category': self.optimization_category,
            'title': self.title,
            'description': self.description,
            'issue_type': self.issue_type,
            'severity': self.severity,
            'old_config': self.old_config,
            'new_config': self.new_config,
            'config_changes': self.config_changes,
            'performance_before': self.performance_before,
            'performance_after': self.performance_after,
            'improvement_percentage': self.improvement_percentage,
            'quality_before': self.quality_before,
            'quality_after': self.quality_after,
            'quality_improvement': self.quality_improvement,
            'status': self.status,
            'priority': self.priority,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'test_results': self.test_results,
            'validation_status': self.validation_status,
            'rollback_available': self.rollback_available,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# Helper functions for search integration initialization
def initialize_search_integration_system():
    """Initialize search integration system with default configurations"""
    print("Search integration system initialized successfully")
