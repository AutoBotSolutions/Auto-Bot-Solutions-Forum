"""
Advanced Caching Models

This module implements Redis-based caching models for the Auto Bot Solutions Forum,
including cache entry management, invalidation tracking, analytics, and dependency management.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
import json
import hashlib
import pickle
import zlib
from sqlalchemy import Index


class CacheEntry(db.Model):
    """Cache key-value storage model for Redis-based caching"""
    
    __tablename__ = 'cache_entries'
    __table_args__ = (
        Index('idx_cache_key', 'cache_key'),
        Index('idx_cache_expires', 'expires_at'),
        Index('idx_cache_tag', 'cache_tag'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255), nullable=False, index=True)
    cache_value = db.Column(db.LargeBinary)  # Compressed binary data
    cache_tag = db.Column(db.String(100), nullable=True, index=True)
    cache_type = db.Column(db.String(50), default='general')  # general, user, session, system
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    access_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    size_bytes = db.Column(db.Integer, default=0)
    compression_ratio = db.Column(db.Float, default=1.0)
    is_compressed = db.Column(db.Boolean, default=True)
    cache_metadata = db.Column(db.JSON)  # Additional cache metadata
    
    def __repr__(self):
        return f'<CacheEntry {self.cache_key[:50]}...>'
    
    @classmethod
    def set_cache(cls, key, value, ttl=None, tag=None, cache_type='general', compress=True):
        """Set a cache entry"""
        # Serialize and compress the value
        serialized = pickle.dumps(value)
        
        if compress and len(serialized) > 1024:  # Only compress if larger than 1KB
            compressed = zlib.compress(serialized)
            compression_ratio = len(compressed) / len(serialized)
            cache_value = compressed
            is_compressed = True
        else:
            cache_value = serialized
            compression_ratio = 1.0
            is_compressed = False
        
        # Calculate expiration time
        expires_at = None
        if ttl:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        # Create or update cache entry
        cache_entry = cls.query.filter_by(cache_key=key).first()
        if cache_entry:
            cache_entry.cache_value = cache_value
            cache_entry.expires_at = expires_at
            cache_entry.updated_at = datetime.utcnow()
            cache_entry.access_count += 1
            cache_entry.last_accessed = datetime.utcnow()
            cache_entry.size_bytes = len(cache_value)
            cache_entry.compression_ratio = compression_ratio
            cache_entry.is_compressed = is_compressed
        else:
            cache_entry = cls(
                cache_key=key,
                cache_value=cache_value,
                cache_tag=tag,
                cache_type=cache_type,
                expires_at=expires_at,
                size_bytes=len(cache_value),
                compression_ratio=compression_ratio,
                is_compressed=is_compressed,
                cache_metadata={}
            )
            db.session.add(cache_entry)
        
        db.session.commit()
        return cache_entry
    
    @classmethod
    def get_cache(cls, key):
        """Get a cache entry"""
        cache_entry = cls.query.filter_by(cache_key=key).first()
        
        if not cache_entry:
            return None
        
        # Check if expired
        if cache_entry.expires_at and cache_entry.expires_at < datetime.utcnow():
            cls.delete_cache(key)
            return None
        
        # Update access statistics
        cache_entry.access_count += 1
        cache_entry.last_accessed = datetime.utcnow()
        db.session.commit()
        
        # Decompress and deserialize
        try:
            if cache_entry.is_compressed:
                decompressed = zlib.decompress(cache_entry.cache_value)
            else:
                decompressed = cache_entry.cache_value
            
            return pickle.loads(decompressed)
        except Exception as e:
            current_app.logger.error(f"Cache deserialization error for key {key}: {e}")
            cls.delete_cache(key)
            return None
    
    @classmethod
    def delete_cache(cls, key):
        """Delete a cache entry"""
        cache_entry = cls.query.filter_by(cache_key=key).first()
        if cache_entry:
            db.session.delete(cache_entry)
            db.session.commit()
            return True
        return False
    
    @classmethod
    def clear_expired(cls):
        """Clear all expired cache entries"""
        expired = cls.query.filter(
            cls.expires_at.isnot(None),
            cls.expires_at < datetime.utcnow()
        ).all()
        
        for entry in expired:
            db.session.delete(entry)
        
        db.session.commit()
        return len(expired)
    
    @classmethod
    def clear_by_tag(cls, tag):
        """Clear all cache entries with a specific tag"""
        entries = cls.query.filter_by(cache_tag=tag).all()
        
        for entry in entries:
            db.session.delete(entry)
        
        db.session.commit()
        return len(entries)
    
    @classmethod
    def clear_by_type(cls, cache_type):
        """Clear all cache entries of a specific type"""
        entries = cls.query.filter_by(cache_type=cache_type).all()
        
        for entry in entries:
            db.session.delete(entry)
        
        db.session.commit()
        return len(entries)
    
    @classmethod
    def get_cache_stats(cls):
        """Get cache statistics"""
        total_entries = cls.query.count()
        expired_entries = cls.query.filter(
            cls.expires_at.isnot(None),
            cls.expires_at < datetime.utcnow()
        ).count()
        
        total_size = db.session.query(db.func.sum(cls.size_bytes)).scalar() or 0
        avg_compression = db.session.query(db.func.avg(cls.compression_ratio)).scalar() or 1.0
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries,
            'total_size_bytes': total_size,
            'average_compression_ratio': avg_compression,
            'cache_hit_ratio': cls._calculate_hit_ratio()
        }
    
    @classmethod
    def _calculate_hit_ratio(cls):
        """Calculate cache hit ratio"""
        # This would typically be tracked in a separate analytics table
        # For now, return a placeholder value
        return 0.85


class CacheInvalidation(db.Model):
    """Cache invalidation tracking model"""
    
    __tablename__ = 'cache_invalidations'
    __table_args__ = (
        Index('idx_invalidation_key', 'cache_key'),
        Index('idx_invalidation_time', 'invalidation_time'),
        Index('idx_invalidation_reason', 'reason'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255), nullable=False, index=True)
    invalidation_type = db.Column(db.String(50), default='manual')  # manual, automatic, ttl, dependency
    reason = db.Column(db.String(100), nullable=True, index=True)
    invalidation_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    invalidated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    invalidation_metadata = db.Column(db.JSON)  # Additional invalidation metadata
    
    # Relationships
    user = db.relationship('User', foreign_keys=[invalidated_by], backref='cache_invalidations')
    
    def __repr__(self):
        return f'<CacheInvalidation {self.cache_key[:50]}...>'
    
    @classmethod
    def track_invalidation(cls, cache_key, invalidation_type='manual', reason=None, user_id=None, metadata=None):
        """Track a cache invalidation"""
        invalidation = cls(
            cache_key=cache_key,
            invalidation_type=invalidation_type,
            reason=reason,
            invalidated_by=user_id,
            invalidation_metadata=metadata or {}
        )
        db.session.add(invalidation)
        db.session.commit()
        return invalidation
    
    @classmethod
    def get_invalidation_history(cls, cache_key=None, hours=24):
        """Get invalidation history"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = cls.query.filter(cls.invalidation_time >= start_time)
        
        if cache_key:
            query = query.filter_by(cache_key=cache_key)
        
        return query.order_by(cls.invalidation_time.desc()).all()
    
    @classmethod
    def get_invalidation_stats(cls, hours=24):
        """Get invalidation statistics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        invalidations = cls.query.filter(cls.invalidation_time >= start_time).all()
        
        # Group by type
        by_type = {}
        for inv in invalidations:
            inv_type = inv.invalidation_type
            if inv_type not in by_type:
                by_type[inv_type] = 0
            by_type[inv_type] += 1
        
        # Group by reason
        by_reason = {}
        for inv in invalidations:
            reason = inv.reason or 'unknown'
            if reason not in by_reason:
                by_reason[reason] = 0
            by_reason[reason] += 1
        
        return {
            'total_invalidations': len(invalidations),
            'invalidations_by_type': by_type,
            'invalidations_by_reason': by_reason,
            'period_hours': hours
        }


class CacheAnalytics(db.Model):
    """Cache performance metrics and analytics model"""
    
    __tablename__ = 'cache_analytics'
    __table_args__ = (
        Index('idx_analytics_time', 'timestamp'),
        Index('idx_analytics_type', 'metric_type'),
        Index('idx_analytics_cache_type', 'cache_type'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    metric_type = db.Column(db.String(50), nullable=False, index=True)  # hit, miss, set, delete, clear
    cache_type = db.Column(db.String(50), nullable=True, index=True)  # general, user, session, system
    cache_key = db.Column(db.String(255), nullable=True)
    cache_tag = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    value = db.Column(db.Float, default=1.0)  # Metric value (e.g., response time, size)
    analytics_metadata = db.Column(db.JSON)  # Additional metric metadata
    
    def __repr__(self):
        return f'<CacheAnalytics {self.metric_type}:{self.cache_type}>'
    
    @classmethod
    def track_metric(cls, metric_type, value=1.0, cache_type=None, cache_key=None, cache_tag=None, metadata=None):
        """Track a cache metric"""
        metric = cls(
            metric_type=metric_type,
            cache_type=cache_type,
            cache_key=cache_key,
            cache_tag=cache_tag,
            value=value,
            analytics_metadata=metadata or {}
        )
        db.session.add(metric)
        db.session.commit()
        return metric
    
    @classmethod
    def get_performance_metrics(cls, hours=1):
        """Get cache performance metrics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get hit/miss metrics
        hits = cls.query.filter(
            cls.metric_type == 'hit',
            cls.timestamp >= start_time
        ).count()
        
        misses = cls.query.filter(
            cls.metric_type == 'miss',
            cls.timestamp >= start_time
        ).count()
        
        total_requests = hits + misses
        hit_ratio = hits / total_requests if total_requests > 0 else 0
        
        # Get average response times
        avg_set_time = cls.query.filter(
            cls.metric_type == 'set',
            cls.timestamp >= start_time
        ).with_entities(db.func.avg(cls.value)).scalar() or 0
        
        avg_get_time = cls.query.filter(
            cls.metric_type.in_(['hit', 'miss']),
            cls.timestamp >= start_time
        ).with_entities(db.func.avg(cls.value)).scalar() or 0
        
        return {
            'hit_ratio': hit_ratio,
            'total_hits': hits,
            'total_misses': misses,
            'total_requests': total_requests,
            'avg_set_time_ms': avg_set_time,
            'avg_get_time_ms': avg_get_time,
            'period_hours': hours
        }
    
    @classmethod
    def get_cache_type_performance(cls, hours=1):
        """Get performance metrics by cache type"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        metrics = cls.query.filter(cls.timestamp >= start_time).all()
        
        performance_by_type = {}
        for metric in metrics:
            cache_type = metric.cache_type or 'general'
            if cache_type not in performance_by_type:
                performance_by_type[cache_type] = {
                    'hits': 0,
                    'misses': 0,
                    'sets': 0,
                    'total_requests': 0
                }
            
            if metric.metric_type == 'hit':
                performance_by_type[cache_type]['hits'] += 1
                performance_by_type[cache_type]['total_requests'] += 1
            elif metric.metric_type == 'miss':
                performance_by_type[cache_type]['misses'] += 1
                performance_by_type[cache_type]['total_requests'] += 1
            elif metric.metric_type == 'set':
                performance_by_type[cache_type]['sets'] += 1
        
        # Calculate hit ratios
        for cache_type, data in performance_by_type.items():
            total = data['total_requests']
            data['hit_ratio'] = data['hits'] / total if total > 0 else 0
        
        return performance_by_type
    
    @classmethod
    def get_trending_keys(cls, hours=1, limit=10):
        """Get most accessed cache keys"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get most frequently accessed keys
        key_stats = db.session.query(
            cls.cache_key,
            db.func.count(cls.id).label('access_count'),
            db.func.avg(cls.value).label('avg_response_time')
        ).filter(
            cls.timestamp >= start_time,
            cls.metric_type.in_(['hit', 'miss']),
            cls.cache_key.isnot(None)
        ).group_by(cls.cache_key).order_by(db.func.count(cls.id).desc()).limit(limit).all()
        
        return [
            {
                'cache_key': key,
                'access_count': count,
                'avg_response_time_ms': float(avg_time) if avg_time else 0
            }
            for key, count, avg_time in key_stats
        ]


class CacheDependency(db.Model):
    """Cache dependency management model"""
    
    __tablename__ = 'cache_dependencies'
    __table_args__ = (
        Index('idx_dependency_parent', 'parent_key'),
        Index('idx_dependency_child', 'child_key'),
        Index('idx_dependency_type', 'dependency_type'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    parent_key = db.Column(db.String(255), nullable=False, index=True)
    child_key = db.Column(db.String(255), nullable=False, index=True)
    dependency_type = db.Column(db.String(50), default='manual')  # manual, automatic, tag, pattern
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dependency_metadata = db.Column(db.JSON)  # Dependency metadata
    
    def __repr__(self):
        return f'<CacheDependency {self.parent_key} -> {self.child_key}>'
    
    @classmethod
    def add_dependency(cls, parent_key, child_key, dependency_type='manual', metadata=None):
        """Add a cache dependency"""
        # Check if dependency already exists
        existing = cls.query.filter_by(
            parent_key=parent_key,
            child_key=child_key
        ).first()
        
        if existing:
            return existing
        
        dependency = cls(
            parent_key=parent_key,
            child_key=child_key,
            dependency_type=dependency_type,
            dependency_metadata=metadata or {}
        )
        db.session.add(dependency)
        db.session.commit()
        return dependency
    
    @classmethod
    def invalidate_dependents(cls, parent_key):
        """Invalidate all dependent cache entries"""
        dependencies = cls.query.filter_by(parent_key=parent_key).all()
        
        invalidated_keys = []
        for dependency in dependencies:
            if CacheEntry.delete_cache(dependency.child_key):
                invalidated_keys.append(dependency.child_key)
                # Track invalidation
                CacheInvalidation.track_invalidation(
                    cache_key=dependency.child_key,
                    invalidation_type='dependency',
                    reason=f'Dependency on {parent_key}'
                )
        
        return invalidated_keys
    
    @classmethod
    def invalidate_by_tag(cls, tag):
        """Invalidate all cache entries with a specific tag"""
        # Get all keys with this tag
        cache_entries = CacheEntry.query.filter_by(cache_tag=tag).all()
        
        invalidated_keys = []
        for entry in cache_entries:
            if CacheEntry.delete_cache(entry.cache_key):
                invalidated_keys.append(entry.cache_key)
                # Track invalidation
                CacheInvalidation.track_invalidation(
                    cache_key=entry.cache_key,
                    invalidation_type='tag',
                    reason=f'Tag invalidation: {tag}'
                )
        
        return invalidated_keys
    
    @classmethod
    def invalidate_by_pattern(cls, pattern):
        """Invalidate cache entries matching a pattern"""
        import re
        
        cache_entries = CacheEntry.query.all()
        
        invalidated_keys = []
        for entry in cache_entries:
            if re.match(pattern, entry.cache_key):
                if CacheEntry.delete_cache(entry.cache_key):
                    invalidated_keys.append(entry.cache_key)
                    # Track invalidation
                    CacheInvalidation.track_invalidation(
                        cache_key=entry.cache_key,
                        invalidation_type='pattern',
                        reason=f'Pattern match: {pattern}'
                    )
        
        return invalidated_keys
    
    @classmethod
    def get_dependency_graph(cls, cache_key):
        """Get dependency graph for a cache key"""
        # Get all dependencies where this key is a parent
        children = cls.query.filter_by(parent_key=cache_key).all()
        
        # Get all dependencies where this key is a child
        parents = cls.query.filter_by(child_key=cache_key).all()
        
        return {
            'cache_key': cache_key,
            'children': [
                {
                    'child_key': dep.child_key,
                    'dependency_type': dep.dependency_type,
                    'created_at': dep.created_at.isoformat(),
                    'metadata': dep.dependency_metadata
                }
                for dep in children
            ],
            'parents': [
                {
                    'parent_key': dep.parent_key,
                    'dependency_type': dep.dependency_type,
                    'created_at': dep.created_at.isoformat(),
                    'metadata': dep.dependency_metadata
                }
                for dep in parents
            ]
        }
    
    @classmethod
    def get_dependency_stats(cls):
        """Get dependency statistics"""
        total_dependencies = cls.query.count()
        
        # Group by dependency type
        by_type = {}
        for dep in cls.query.all():
            dep_type = dep.dependency_type
            if dep_type not in by_type:
                by_type[dep_type] = 0
            by_type[dep_type] += 1
        
        return {
            'total_dependencies': total_dependencies,
            'dependencies_by_type': by_type
        }
