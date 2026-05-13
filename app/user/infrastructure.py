"""
User Management Infrastructure Components

This module provides infrastructure components for user management systems including:
- Profile image storage and management
- Theme management system
- Profile backup strategies
- Profile performance monitoring
- Social graph database operations
- Social feed processing
- Social analytics infrastructure
- Social performance monitoring
- Analytics data warehouse
- Real-time analytics processing
- Analytics visualization
- Analytics performance monitoring
"""

import os
import json
import time
import hashlib
import shutil
from datetime import datetime, timedelta
from PIL import Image, ImageOps
from flask import current_app
from app import db, cache
from app.models import User
from app.user.social.models import UserFollow, UserFriend, SocialActivity
from app.user.analytics.models import UserBehavior, UserEngagement


class ProfileInfrastructure:
    """Profile infrastructure management system."""
    
    @staticmethod
    def get_profile_storage_path():
        """Get profile storage path."""
        return current_app.config.get('USER_PROFILE_UPLOAD_PATH', 'uploads/profiles')
    
    @staticmethod
    def ensure_storage_directories():
        """Ensure all storage directories exist."""
        storage_path = ProfileInfrastructure.get_profile_storage_path()
        directories = [
            storage_path,
            os.path.join(storage_path, 'avatars'),
            os.path.join(storage_path, 'banners'),
            os.path.join(storage_path, 'themes'),
            os.path.join(storage_path, 'backups')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def store_profile_image(user_id, image_file, image_type='avatar'):
        """Store and optimize profile image."""
        ProfileInfrastructure.ensure_storage_directories()
        
        # Generate unique filename
        timestamp = int(time.time())
        filename = f"{user_id}_{timestamp}_{image_type}.jpg"
        storage_path = ProfileInfrastructure.get_profile_storage_path()
        file_path = os.path.join(storage_path, image_type, filename)
        
        try:
            # Open and optimize image
            image = Image.open(image_file)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize based on image type
            if image_type == 'avatar':
                image = ImageOps.fit(image, (200, 200), Image.Resampling.LANCZOS)
            elif image_type == 'banner':
                image = ImageOps.fit(image, (1200, 400), Image.Resampling.LANCZOS)
            
            # Save optimized image
            image.save(file_path, 'JPEG', quality=85, optimize=True)
            
            # Return relative path for database storage
            return os.path.join(image_type, filename)
            
        except Exception as e:
            current_app.logger.error(f"Error storing profile image: {e}")
            return None
    
    @staticmethod
    def delete_profile_image(image_path):
        """Delete profile image."""
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
                return True
            except Exception as e:
                current_app.logger.error(f"Error deleting profile image: {e}")
        return False
    
    @staticmethod
    def create_profile_backup(user_id):
        """Create profile data backup."""
        user = User.query.get(user_id)
        if not user:
            return None
        
        backup_data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'backup_date': datetime.utcnow().isoformat(),
            'profile_data': {
                'bio': user.bio,
                'location': user.location,
                'website': user.website,
                'avatar_url': user.avatar_url,
                'profile_theme': user.profile_theme,
                'profile_skin': user.profile_skin,
                'profile_banner_url': user.profile_banner_url,
                'profile_layout': user.profile_layout,
                'profile_widgets': user.profile_widgets,
                'profile_privacy': user.profile_privacy,
                'profile_custom_css': user.profile_custom_css,
                'profile_color_scheme': user.profile_color_scheme,
                'profile_show_badges': user.profile_show_badges,
                'profile_show_stats': user.profile_show_stats,
                'profile_show_activity': user.profile_show_activity,
                'profile_allow_messages': user.profile_allow_messages,
                'profile_allow_friend_requests': user.profile_allow_friend_requests,
                'profile_public_profile': user.profile_public_profile
            },
            'preferences': {
                'user_preferences': user.user_preferences,
                'notification_preferences': user.notification_preferences,
                'accessibility_preferences': user.accessibility_preferences,
                'social_preferences': user.social_preferences,
                'analytics_preferences': user.analytics_preferences
            }
        }
        
        # Save backup to file
        ProfileInfrastructure.ensure_storage_directories()
        backup_path = os.path.join(
            ProfileInfrastructure.get_profile_storage_path(),
            'backups',
            f"profile_backup_{user_id}_{int(time.time())}.json"
        )
        
        try:
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            return backup_path
        except Exception as e:
            current_app.logger.error(f"Error creating profile backup: {e}")
            return None
    
    @staticmethod
    def restore_profile_backup(user_id, backup_path):
        """Restore profile from backup."""
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Restore profile data
            profile_data = backup_data.get('profile_data', {})
            for key, value in profile_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            # Restore preferences
            preferences = backup_data.get('preferences', {})
            for key, value in preferences.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            db.session.commit()
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error restoring profile backup: {e}")
            return False
    
    @staticmethod
    def get_profile_performance_metrics(user_id):
        """Get profile performance metrics."""
        cache_key = f"profile_infrastructure:performance:{user_id}"
        cached_metrics = cache.get(cache_key)
        
        if cached_metrics:
            return cached_metrics
        
        try:
            # Profile load time
            start_time = time.time()
            user = User.query.get(user_id)
            profile_load_time = time.time() - start_time
            
            # Social data load time
            start_time = time.time()
            follower_count = UserFollow.query.filter_by(following_id=user_id).count()
            following_count = UserFollow.query.filter_by(follower_id=user_id).count()
            social_load_time = time.time() - start_time
            
            # Activity data load time
            start_time = time.time()
            activity_count = SocialActivity.query.filter_by(user_id=user_id).count()
            activity_load_time = time.time() - start_time
            
            metrics = {
                'profile_load_time': profile_load_time,
                'social_load_time': social_load_time,
                'activity_load_time': activity_load_time,
                'follower_count': follower_count,
                'following_count': following_count,
                'activity_count': activity_count,
                'total_load_time': profile_load_time + social_load_time + activity_load_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, metrics, timeout=300)
            return metrics
            
        except Exception as e:
            current_app.logger.error(f"Error getting profile performance metrics: {e}")
            return None


class ThemeManagementSystem:
    """Theme management system for profiles."""
    
    @staticmethod
    def get_available_themes():
        """Get list of available themes."""
        themes = [
            {
                'id': 'light',
                'name': 'Light Theme',
                'description': 'Clean light theme with high contrast',
                'preview': '/static/themes/light/preview.png',
                'css_variables': {
                    '--bg-primary': '#ffffff',
                    '--bg-secondary': '#f8f9fa',
                    '--text-primary': '#212529',
                    '--text-secondary': '#6c757d',
                    '--accent': '#007bff'
                }
            },
            {
                'id': 'dark',
                'name': 'Dark Theme',
                'description': 'Dark theme optimized for low-light environments',
                'preview': '/static/themes/dark/preview.png',
                'css_variables': {
                    '--bg-primary': '#1a1a1a',
                    '--bg-secondary': '#2d2d2d',
                    '--text-primary': '#ffffff',
                    '--text-secondary': '#b0b0b0',
                    '--accent': '#0d6efd'
                }
            },
            {
                'id': 'auto',
                'name': 'Auto Theme',
                'description': 'Automatically switches between light and dark based on system preference',
                'preview': '/static/themes/auto/preview.png',
                'css_variables': {}
            },
            {
                'id': 'ocean',
                'name': 'Ocean Theme',
                'description': 'Calming ocean-inspired color scheme',
                'preview': '/static/themes/ocean/preview.png',
                'css_variables': {
                    '--bg-primary': '#f0f8ff',
                    '--bg-secondary': '#e6f3ff',
                    '--text-primary': '#1e3a8a',
                    '--text-secondary': '#3b82f6',
                    '--accent': '#0ea5e9'
                }
            },
            {
                'id': 'forest',
                'name': 'Forest Theme',
                'description': 'Natural forest-inspired color scheme',
                'preview': '/static/themes/forest/preview.png',
                'css_variables': {
                    '--bg-primary': '#f0fdf4',
                    '--bg-secondary': '#dcfce7',
                    '--text-primary': '#14532d',
                    '--text-secondary': '#16a34a',
                    '--accent': '#22c55e'
                }
            },
            {
                'id': 'sunset',
                'name': 'Sunset Theme',
                'description': 'Warm sunset-inspired color scheme',
                'preview': '/static/themes/sunset/preview.png',
                'css_variables': {
                    '--bg-primary': '#fff7ed',
                    '--bg-secondary': '#fed7aa',
                    '--text-primary': '#7c2d12',
                    '--text-secondary': '#ea580c',
                    '--accent': '#f97316'
                }
            },
            {
                'id': 'midnight',
                'name': 'Midnight Theme',
                'description': 'Deep dark theme with purple accents',
                'preview': '/static/themes/midnight/preview.png',
                'css_variables': {
                    '--bg-primary': '#0f0f23',
                    '--bg-secondary': '#1a1a2e',
                    '--text-primary': '#e0e0e0',
                    '--text-secondary': '#a0a0a0',
                    '--accent': '#7c3aed'
                }
            },
            {
                'id': 'arctic',
                'name': 'Arctic Theme',
                'description': 'Cool arctic-inspired color scheme',
                'preview': '/static/themes/arctic/preview.png',
                'css_variables': {
                    '--bg-primary': '#f8fafc',
                    '--bg-secondary': '#e2e8f0',
                    '--text-primary': '#0f172a',
                    '--text-secondary': '#475569',
                    '--accent': '#0284c7'
                }
            },
            {
                'id': 'cherry',
                'name': 'Cherry Theme',
                'description': 'Sweet cherry-inspired color scheme',
                'preview': '/static/themes/cherry/preview.png',
                'css_variables': {
                    '--bg-primary': '#fff1f2',
                    '--bg-secondary': '#ffe4e6',
                    '--text-primary': '#881337',
                    '--text-secondary': '#f43f5e',
                    '--accent': '#e11d48'
                }
            },
            {
                'id': 'emerald',
                'name': 'Emerald Theme',
                'description': 'Rich emerald-inspired color scheme',
                'preview': '/static/themes/emerald/preview.png',
                'css_variables': {
                    '--bg-primary': '#f0fdfa',
                    '--bg-secondary': '#ccfbf1',
                    '--text-primary': '#064e3b',
                    '--text-secondary': '#059669',
                    '--accent': '#10b981'
                }
            }
        ]
        
        return themes
    
    @staticmethod
    def get_theme_css(theme_id):
        """Get CSS variables for a theme."""
        themes = ThemeManagementSystem.get_available_themes()
        theme = next((t for t in themes if t['id'] == theme_id), None)
        
        if theme:
            return theme.get('css_variables', {})
        return {}
    
    @staticmethod
    def generate_theme_css(theme_id, custom_colors=None):
        """Generate complete CSS for a theme."""
        base_css = ThemeManagementSystem.get_theme_css(theme_id)
        
        if custom_colors:
            base_css.update(custom_colors)
        
        css_rules = []
        for variable, value in base_css.items():
            css_rules.append(f"  {variable}: {value};")
        
        return f":root {{\n{chr(10).join(css_rules)}\n}}"
    
    @staticmethod
    def create_custom_theme(name, css_variables):
        """Create a custom theme."""
        custom_theme = {
            'id': f"custom_{name.lower().replace(' ', '_')}",
            'name': name,
            'description': 'Custom user-created theme',
            'css_variables': css_variables,
            'custom': True
        }
        
        return custom_theme


class SocialInfrastructure:
    """Social infrastructure management system."""
    
    @staticmethod
    def get_social_graph_data(user_id, depth=2):
        """Get social graph data for visualization."""
        cache_key = f"social_infrastructure:graph:{user_id}:{depth}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Get user's connections
            following = UserFollow.query.filter_by(follower_id=user_id).all()
            followers = UserFollow.query.filter_by(following_id=user_id).all()
            friends = UserFriend.query.filter(
                (UserFriend.user1_id == user_id) | (UserFriend.user2_id == user_id),
                UserFriend.status == 'accepted'
            ).all()
            
            # Build graph data
            nodes = [{'id': user_id, 'label': f'User {user_id}', 'type': 'user'}]
            edges = []
            
            # Add following connections
            for follow in following:
                nodes.append({'id': follow.following_id, 'label': f'User {follow.following_id}', 'type': 'following'})
                edges.append({'from': user_id, 'to': follow.following_id, 'type': 'follows'})
            
            # Add follower connections
            for follow in followers:
                if follow.follower_id not in [node['id'] for node in nodes]:
                    nodes.append({'id': follow.follower_id, 'label': f'User {follow.follower_id}', 'type': 'follower'})
                edges.append({'from': follow.follower_id, 'to': user_id, 'type': 'follows'})
            
            # Add friend connections
            for friend in friends:
                friend_id = friend.user2_id if friend.user1_id == user_id else friend.user1_id
                if friend_id not in [node['id'] for node in nodes]:
                    nodes.append({'id': friend_id, 'label': f'User {friend_id}', 'type': 'friend'})
                edges.append({'from': user_id, 'to': friend_id, 'type': 'friends'})
            
            graph_data = {
                'nodes': nodes,
                'edges': edges,
                'stats': {
                    'following_count': len(following),
                    'followers_count': len(followers),
                    'friends_count': len(friends),
                    'total_connections': len(following) + len(followers)
                }
            }
            
            # Cache for 10 minutes
            cache.set(cache_key, graph_data, timeout=600)
            return graph_data
            
        except Exception as e:
            current_app.logger.error(f"Error getting social graph data: {e}")
            return None
    
    @staticmethod
    def process_social_feed(user_id, limit=50, include_friends=True):
        """Process and optimize social feed."""
        cache_key = f"social_infrastructure:feed:{user_id}:{limit}:{include_friends}"
        cached_feed = cache.get(cache_key)
        
        if cached_feed:
            return cached_feed
        
        try:
            # Get user's following
            following_ids = [f.following_id for f in UserFollow.query.filter_by(follower_id=user_id).all()]
            
            if include_friends:
                # Add friends to following list
                friends = UserFriend.query.filter(
                    (UserFriend.user1_id == user_id) | (UserFriend.user2_id == user_id),
                    UserFriend.status == 'accepted'
                ).all()
                for friend in friends:
                    friend_id = friend.user2_id if friend.user1_id == user_id else friend.user1_id
                    if friend_id not in following_ids:
                        following_ids.append(friend_id)
            
            # Get activities from followed users
            activities = SocialActivity.query.filter(
                SocialActivity.user_id.in_(following_ids),
                SocialActivity.is_public == True
            ).order_by(SocialActivity.created_at.desc()).limit(limit).all()
            
            # Process feed items
            feed_items = []
            for activity in activities:
                feed_items.append({
                    'id': activity.id,
                    'user_id': activity.user_id,
                    'username': activity.user.username if activity.user else 'Unknown',
                    'activity_type': activity.activity_type,
                    'action': activity.action,
                    'description': activity.description,
                    'target_type': activity.target_type,
                    'target_id': activity.target_id,
                    'created_at': activity.created_at.isoformat(),
                    'activity_metadata': activity.activity_metadata
                })
            
            feed_data = {
                'items': feed_items,
                'stats': {
                    'total_items': len(feed_items),
                    'following_count': len(following_ids),
                    'last_updated': datetime.utcnow().isoformat()
                }
            }
            
            # Cache for 3 minutes
            cache.set(cache_key, feed_data, timeout=180)
            return feed_data
            
        except Exception as e:
            current_app.logger.error(f"Error processing social feed: {e}")
            return None
    
    @staticmethod
    def get_social_analytics(user_id, days=30):
        """Get social analytics data."""
        cache_key = f"social_infrastructure:analytics:{user_id}:{days}"
        cached_analytics = cache.get(cache_key)
        
        if cached_analytics:
            return cached_analytics
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get social metrics
            following_count = UserFollow.query.filter_by(follower_id=user_id).count()
            followers_count = UserFollow.query.filter_by(following_id=user_id).count()
            friends_count = UserFriend.query.filter(
                (UserFriend.user1_id == user_id) | (UserFriend.user2_id == user_id),
                UserFriend.status == 'accepted'
            ).count()
            
            # Get activity metrics
            activities = SocialActivity.query.filter(
                SocialActivity.user_id == user_id,
                SocialActivity.created_at >= start_date
            ).all()
            
            # Activity breakdown by type
            activity_types = {}
            for activity in activities:
                activity_type = activity.activity_type
                if activity_type not in activity_types:
                    activity_types[activity_type] = 0
                activity_types[activity_type] += 1
            
            # Growth metrics
            followers_growth = []
            for i in range(days):
                date = datetime.utcnow() - timedelta(days=i)
                count = UserFollow.query.filter_by(following_id=user_id).filter(
                    UserFollow.created_at <= date
                ).count()
                followers_growth.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
            
            analytics_data = {
                'overview': {
                    'following_count': following_count,
                    'followers_count': followers_count,
                    'friends_count': friends_count,
                    'total_activities': len(activities),
                    'engagement_rate': len(activities) / max(followers_count, 1) * 100
                },
                'activity_breakdown': activity_types,
                'followers_growth': list(reversed(followers_growth)),
                'period': f"{days} days",
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Cache for 15 minutes
            cache.set(cache_key, analytics_data, timeout=900)
            return analytics_data
            
        except Exception as e:
            current_app.logger.error(f"Error getting social analytics: {e}")
            return None
    
    @staticmethod
    def get_social_performance_metrics():
        """Get social system performance metrics."""
        cache_key = "social_infrastructure:performance:system"
        cached_metrics = cache.get(cache_key)
        
        if cached_metrics:
            return cached_metrics
        
        try:
            # Database performance metrics
            start_time = time.time()
            total_follows = UserFollow.query.count()
            total_friends = UserFriend.query.count()
            total_activities = SocialActivity.query.count()
            db_query_time = time.time() - start_time
            
            # Cache performance metrics
            start_time = time.time()
            cache_info = cache.cache._cache.info() if hasattr(cache.cache, '_cache') else {}
            cache_time = time.time() - start_time
            
            metrics = {
                'database': {
                    'total_follows': total_follows,
                    'total_friends': total_friends,
                    'total_activities': total_activities,
                    'query_time': db_query_time
                },
                'cache': {
                    'info': cache_info,
                    'query_time': cache_time
                },
                'system': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'uptime': time.time()
                }
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, metrics, timeout=300)
            return metrics
            
        except Exception as e:
            current_app.logger.error(f"Error getting social performance metrics: {e}")
            return None


class AnalyticsInfrastructure:
    """Analytics infrastructure management system."""
    
    @staticmethod
    def get_analytics_data_warehouse(user_id, start_date=None, end_date=None):
        """Get analytics data from data warehouse."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        cache_key = f"analytics_infrastructure:warehouse:{user_id}:{start_date}:{end_date}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Get user behaviors
            behaviors = UserBehavior.query.filter(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= start_date,
                UserBehavior.created_at <= end_date
            ).all()
            
            # Get user engagements
            engagements = UserEngagement.query.filter(
                UserEngagement.user_id == user_id,
                UserEngagement.date >= start_date.date(),
                UserEngagement.date <= end_date.date()
            ).all()
            
            # Get user performances
            performances = UserPerformance.query.filter(
                UserPerformance.user_id == user_id,
                UserPerformance.period_start >= start_date,
                UserPerformance.period_end <= end_date
            ).all()
            
            # Aggregate data
            warehouse_data = {
                'behaviors': [
                    {
                        'id': b.id,
                        'behavior_type': b.behavior_type,
                        'action': b.action,
                        'target_type': b.target_type,
                        'target_id': b.target_id,
                        'duration': b.duration,
                        'created_at': b.created_at.isoformat(),
                        'behavior_metadata': b.behavior_metadata
                    } for b in behaviors
                ],
                'engagements': [
                    {
                        'id': e.id,
                        'date': e.date.isoformat(),
                        'total_actions': e.total_actions,
                        'login_count': e.login_count,
                        'post_count': e.post_count,
                        'comment_count': e.comment_count,
                        'like_count': e.like_count,
                        'share_count': e.share_count,
                        'view_count': e.view_count,
                        'session_duration': e.session_duration,
                        'pages_viewed': e.pages_viewed,
                        'bounce_rate': e.bounce_rate,
                        'engagement_score': e.engagement_score,
                        'engagement_metadata': e.engagement_metadata
                    } for e in engagements
                ],
                'performances': [
                    {
                        'id': p.id,
                        'metric_type': p.metric_type,
                        'metric_name': p.metric_name,
                        'metric_value': p.metric_value,
                        'previous_value': p.previous_value,
                        'change_percentage': p.change_percentage,
                        'period': p.period,
                        'period_start': p.period_start.isoformat(),
                        'period_end': p.period_end.isoformat(),
                        'performance_metadata': p.performance_metadata
                    } for p in performances
                ],
                'summary': {
                    'total_behaviors': len(behaviors),
                    'total_engagements': len(engagements),
                    'total_performances': len(performances),
                    'date_range': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                }
            }
            
            # Cache for 10 minutes
            cache.set(cache_key, warehouse_data, timeout=600)
            return warehouse_data
            
        except Exception as e:
            current_app.logger.error(f"Error getting analytics data warehouse: {e}")
            return None
    
    @staticmethod
    def process_real_time_analytics(user_id, event_type, event_data):
        """Process real-time analytics events."""
        try:
            # Create behavior record
            behavior = UserBehavior(
                user_id=user_id,
                behavior_type=event_data.get('behavior_type', 'unknown'),
                action=event_data.get('action', 'unknown'),
                target_type=event_data.get('target_type'),
                target_id=event_data.get('target_id'),
                session_id=event_data.get('session_id'),
                ip_address=event_data.get('ip_address'),
                user_agent=event_data.get('user_agent'),
                referrer=event_data.get('referrer'),
                duration=event_data.get('duration'),
                behavior_metadata=event_data.get('metadata')
            )
            
            db.session.add(behavior)
            
            # Update engagement metrics if needed
            if event_type in ['login', 'post', 'comment', 'like', 'share']:
                today = datetime.utcnow().date()
                engagement = UserEngagement.query.filter_by(
                    user_id=user_id,
                    date=today
                ).first()
                
                if not engagement:
                    engagement = UserEngagement(
                        user_id=user_id,
                        date=today
                    )
                    db.session.add(engagement)
                
                # Update engagement counters
                if event_type == 'login':
                    engagement.login_count += 1
                elif event_type == 'post':
                    engagement.post_count += 1
                elif event_type == 'comment':
                    engagement.comment_count += 1
                elif event_type == 'like':
                    engagement.like_count += 1
                elif event_type == 'share':
                    engagement.share_count += 1
                
                engagement.total_actions += 1
                engagement.engagement_metadata = event_data.get('metadata')
            
            db.session.commit()
            
            # Invalidate relevant caches
            cache.delete_pattern(f"analytics:{user_id}:*")
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error processing real-time analytics: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def generate_analytics_visualization(user_id, chart_type, period='7d'):
        """Generate analytics visualization data."""
        cache_key = f"analytics_infrastructure:visualization:{user_id}:{chart_type}:{period}"
        cached_viz = cache.get(cache_key)
        
        if cached_viz:
            return cached_viz
        
        try:
            # Calculate date range
            days = int(period.replace('d', ''))
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            if chart_type == 'engagement_trend':
                # Get engagement trend data
                engagements = UserEngagement.query.filter(
                    UserEngagement.user_id == user_id,
                    UserEngagement.date >= start_date.date(),
                    UserEngagement.date <= end_date.date()
                ).order_by(UserEngagement.date.asc()).all()
                
                viz_data = {
                    'type': 'line',
                    'title': 'Engagement Trend',
                    'data': {
                        'labels': [e.date.strftime('%Y-%m-%d') for e in engagements],
                        'datasets': [{
                            'label': 'Engagement Score',
                            'data': [e.engagement_score for e in engagements],
                            'borderColor': 'rgb(75, 192, 192)',
                            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                            'fill': True
                        }]
                    }
                }
                
            elif chart_type == 'activity_breakdown':
                # Get activity breakdown
                behaviors = UserBehavior.query.filter(
                    UserBehavior.user_id == user_id,
                    UserBehavior.created_at >= start_date,
                    UserBehavior.created_at <= end_date
                ).all()
                
                # Count by behavior type
                behavior_counts = {}
                for behavior in behaviors:
                    behavior_type = behavior.behavior_type
                    if behavior_type not in behavior_counts:
                        behavior_counts[behavior_type] = 0
                    behavior_counts[behavior_type] += 1
                
                viz_data = {
                    'type': 'pie',
                    'title': 'Activity Breakdown',
                    'data': {
                        'labels': list(behavior_counts.keys()),
                        'datasets': [{
                            'data': list(behavior_counts.values()),
                            'backgroundColor': [
                                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                                '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                            ]
                        }]
                    }
                }
                
            elif chart_type == 'performance_metrics':
                # Get performance metrics
                performances = UserPerformance.query.filter(
                    UserPerformance.user_id == user_id,
                    UserPerformance.period_start >= start_date,
                    UserPerformance.period_end <= end_date
                ).order_by(UserPerformance.period_start.asc()).all()
                
                viz_data = {
                    'type': 'bar',
                    'title': 'Performance Metrics',
                    'data': {
                        'labels': [p.period_start.strftime('%Y-%m-%d') for p in performances],
                        'datasets': [
                            {
                                'label': 'Posts',
                                'data': [p.metric_value for p in performances if p.metric_type == 'posts'],
                                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                                'borderColor': 'rgba(255, 99, 132, 1)',
                                'borderWidth': 1
                            },
                            {
                                'label': 'Comments',
                                'data': [p.metric_value for p in performances if p.metric_type == 'comments'],
                                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                                'borderColor': 'rgba(54, 162, 235, 1)',
                                'borderWidth': 1
                            }
                        ]
                    }
                }
                
            else:
                viz_data = {'error': 'Unknown chart type'}
            
            # Cache for 5 minutes
            cache.set(cache_key, viz_data, timeout=300)
            return viz_data
            
        except Exception as e:
            current_app.logger.error(f"Error generating analytics visualization: {e}")
            return None
    
    @staticmethod
    def get_analytics_performance_metrics():
        """Get analytics system performance metrics."""
        cache_key = "analytics_infrastructure:performance:system"
        cached_metrics = cache.get(cache_key)
        
        if cached_metrics:
            return cached_metrics
        
        try:
            # Database performance metrics
            start_time = time.time()
            total_behaviors = UserBehavior.query.count()
            total_engagements = UserEngagement.query.count()
            total_performances = UserPerformance.query.count()
            db_query_time = time.time() - start_time
            
            # Cache performance metrics
            start_time = time.time()
            cache_info = cache.cache._cache.info() if hasattr(cache.cache, '_cache') else {}
            cache_time = time.time() - start_time
            
            # Processing metrics
            start_time = time.time()
            # Simulate some processing time
            processing_time = time.time() - start_time
            
            metrics = {
                'database': {
                    'total_behaviors': total_behaviors,
                    'total_engagements': total_engagements,
                    'total_performances': total_performances,
                    'query_time': db_query_time
                },
                'cache': {
                    'info': cache_info,
                    'query_time': cache_time
                },
                'processing': {
                    'processing_time': processing_time
                },
                'system': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'uptime': time.time()
                }
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, metrics, timeout=300)
            return metrics
            
        except Exception as e:
            current_app.logger.error(f"Error getting analytics performance metrics: {e}")
            return None
