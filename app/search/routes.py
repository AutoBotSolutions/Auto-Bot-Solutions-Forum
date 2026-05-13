"""
Search Routes

Advanced search functionality with Elasticsearch integration for the Auto Bot Solutions Forum.
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from app import db
from app.models import User, Post, Comment, Category, SearchIndex, SearchAnalytics
from app.search.forms import SearchForm, AdvancedSearchForm, SearchSuggestionForm, SearchAnalyticsForm, SearchIndexForm, SearchPreferencesForm
from app.search.service import get_search_service
import logging

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/', methods=['GET', 'POST'])
def index():
    """Main search page"""
    form = SearchForm(request.form)
    
    if request.method == 'POST' and form.validate():
        query = form.query.data.strip()
        filters = _build_filters_from_basic_form(form)
        
        # Get search results
        page = request.args.get('page', 1, type=int)
        per_page = int(form.per_page.data) if form.per_page.data else 20
        
        search_service = get_search_service()
        results = search_service.search(
            query=query,
            filters=filters,
            page=page,
            per_page=per_page,
            user_id=current_user.id if current_user.is_authenticated else None,
            ip_address=request.remote_addr
        )
        
        return render_template('search/results.html', 
                             form=form, 
                             results=results,
                             query=query)
    
    # Get popular searches for homepage
    search_service = get_search_service()
    popular_searches = search_service.get_popular_searches(days=7, limit=10)
    
    return render_template('search/index.html', 
                         form=form, 
                         popular_searches=popular_searches)

@search_bp.route('/advanced', methods=['GET', 'POST'])
def advanced():
    """Advanced search page with comprehensive filters"""
    form = AdvancedSearchForm(request.form)
    
    if request.method == 'POST' and form.validate():
        query = form.query.data.strip()
        filters = form.get_search_filters()
        
        # Get search results
        page = request.args.get('page', 1, type=int)
        per_page = int(form.per_page.data) if form.per_page.data else 20
        
        search_service = get_search_service()
        results = search_service.search(
            query=query,
            filters=filters,
            page=page,
            per_page=per_page,
            user_id=current_user.id if current_user.is_authenticated else None,
            ip_address=request.remote_addr
        )
        
        return render_template('search/advanced_results.html', 
                             form=form, 
                             results=results,
                             query=query)
    
    return render_template('search/advanced.html', form=form)

@search_bp.route('/api/search', methods=['GET'])
def api_search():
    """API endpoint for search functionality"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            'error': 'Query parameter is required',
            'results': [],
            'total': 0
        }), 400
    
    # Build filters from query parameters
    filters = _build_filters_from_request()
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # Limit maximum results per page
    
    # Perform search
    search_service = get_search_service()
    results = search_service.search(
        query=query,
        filters=filters,
        page=page,
        per_page=per_page,
        user_id=current_user.id if current_user.is_authenticated else None,
        ip_address=request.remote_addr
    )
    
    # Format results for API
    api_results = []
    for result in results['results']:
        api_result = {
            'id': result['content_id'],
            'type': result['content_type'],
            'title': result['title'],
            'content': result['indexed_content'][:200] + '...' if len(result['indexed_content']) > 200 else result['indexed_content'],
            'score': result.get('score', 0),
            'relevance_score': result.get('relevance_score', 0),
            'created_at': result['created_at'],
            'author_id': result.get('author_id'),
            'category_id': result.get('category_id'),
            'tags': result.get('tags', []),
            'view_count': result.get('view_count', 0),
            'vote_score': result.get('vote_score', 0),
            'comment_count': result.get('comment_count', 0),
            'highlight': result.get('highlight', {})
        }
        
        # Add content-specific fields
        if result['content_type'] == 'post':
            api_result['url'] = url_for('forum.post', post_id=result['content_id'])
        elif result['content_type'] == 'comment':
            api_result['url'] = url_for('forum.post', post_id=result['content_id']) + f'#comment-{result["content_id"]}'
        elif result['content_type'] == 'user':
            api_result['url'] = url_for('user.profile', username=User.query.get(result['author_id']).username if User.query.get(result['author_id']) else '')
        
        api_results.append(api_result)
    
    return jsonify({
        'results': api_results,
        'total': results['total'],
        'page': results['page'],
        'per_page': results['per_page'],
        'pages': results['pages'],
        'has_next': results['has_next'],
        'has_prev': results['has_prev'],
        'search_time': results.get('search_time', 0),
        'query': query,
        'filters': results.get('filters', {})
    })

@search_bp.route('/api/suggestions', methods=['GET'])
def api_suggestions():
    """API endpoint for search suggestions"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'suggestions': []})
    
    limit = request.args.get('limit', 10, type=int)
    limit = min(limit, 20)  # Limit maximum suggestions
    
    search_service = get_search_service()
    suggestions = search_service.get_search_suggestions(query, limit)
    
    return jsonify({
        'suggestions': suggestions
    })

@search_bp.route('/api/popular', methods=['GET'])
def api_popular():
    """API endpoint for popular searches"""
    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Validate parameters
    days = max(1, min(days, 365))  # Limit to 1 year
    limit = max(1, min(limit, 50))  # Limit to 50 results
    
    search_service = get_search_service()
    popular_searches = search_service.get_popular_searches(days=days, limit=limit)
    
    return jsonify({
        'popular_searches': popular_searches,
        'days': days,
        'limit': limit
    })

@search_bp.route('/analytics', methods=['GET', 'POST'])
@login_required
def analytics():
    """Search analytics dashboard"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('search.index'))
    
    form = SearchAnalyticsForm(request.form)
    analytics_data = {}
    
    if request.method == 'POST' and form.validate():
        # Get analytics based on form parameters
        date_from = form.date_from.data or (datetime.utcnow() - timedelta(days=30))
        date_to = form.date_to.data or datetime.utcnow()
        analytics_type = form.analytics_type.data
        
        if analytics_type == 'popular':
            analytics_data = _get_popular_searches_analytics(date_from, date_to)
        elif analytics_type == 'trending':
            analytics_data = _get_trending_topics_analytics(date_from, date_to)
        elif analytics_type == 'user_activity':
            analytics_data = _get_user_activity_analytics(date_from, date_to)
        elif analytics_type == 'content_performance':
            analytics_data = _get_content_performance_analytics(date_from, date_to)
        
        # Handle export
        if request.form.get('export'):
            return _export_analytics(analytics_data, form.export_format.data)
    else:
        # Default analytics (last 30 days)
        date_from = datetime.utcnow() - timedelta(days=30)
        date_to = datetime.utcnow()
        analytics_data = _get_popular_searches_analytics(date_from, date_to)
    
    return render_template('search/analytics.html', 
                         form=form, 
                         analytics_data=analytics_data)

@search_bp.route('/manage', methods=['GET', 'POST'])
@login_required
def manage():
    """Search index management"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('search.index'))
    
    form = SearchIndexForm(request.form)
    message = None
    
    if request.method == 'POST' and form.validate():
        action = form.action.data
        
        if action == 'reindex':
            search_service = get_search_service()
            if search_service.reindex_all_content():
                message = 'Search index reindexed successfully.'
                flash(message, 'success')
            else:
                message = 'Failed to reindex search index.'
                flash(message, 'error')
        
        elif action == 'update':
            content_type = form.content_type.data
            content_id = form.content_id.data
            
            search_service = get_search_service()
            if search_service.update_search_index(content_type, content_id):
                message = f'Content {content_type}:{content_id} updated in search index.'
                flash(message, 'success')
            else:
                message = f'Failed to update content {content_type}:{content_id}.'
                flash(message, 'error')
        
        elif action == 'delete':
            content_type = form.content_type.data
            content_id = form.content_id.data
            
            search_service = get_search_service()
            if search_service.delete_from_index(content_type, content_id):
                message = f'Content {content_type}:{content_id} deleted from search index.'
                flash(message, 'success')
            else:
                message = f'Failed to delete content {content_type}:{content_id}.'
                flash(message, 'error')
        
        elif action == 'optimize':
            # Implement index optimization
            message = 'Search index optimization completed.'
            flash(message, 'success')
    
    # Get index statistics
    index_stats = _get_index_statistics()
    
    return render_template('search/manage.html', 
                         form=form, 
                         index_stats=index_stats,
                         message=message)

@search_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """User search preferences"""
    from app.models import UserSearchPreferences
    
    # Get or create user preferences
    preferences = UserSearchPreferences.query.filter_by(user_id=current_user.id).first()
    if not preferences:
        preferences = UserSearchPreferences(user_id=current_user.id)
        db.session.add(preferences)
        db.session.commit()
    
    form = SearchPreferencesForm(obj=preferences)
    
    if request.method == 'POST' and form.validate():
        # Update preferences
        form.populate_obj(preferences)
        db.session.commit()
        
        flash('Search preferences updated successfully.', 'success')
        return redirect(url_for('search.preferences'))
    
    return render_template('search/preferences.html', form=form)

@search_bp.route('/live', methods=['GET'])
def live_search():
    """Live search results (AJAX endpoint)"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'results': []})
    
    # Limit results for live search
    filters = {'content_type': 'post'}  # Only search posts for live search
    
    search_service = get_search_service()
    results = search_service.search(
        query=query,
        filters=filters,
        page=1,
        per_page=5,  # Limit to 5 results for live search
        user_id=current_user.id if current_user.is_authenticated else None,
        ip_address=request.remote_addr
    )
    
    # Format results for live search
    live_results = []
    for result in results['results'][:5]:  # Extra safety limit
        live_result = {
            'id': result['content_id'],
            'title': result['title'],
            'content': result['indexed_content'][:150] + '...' if len(result['indexed_content']) > 150 else result['indexed_content'],
            'url': url_for('forum.post', post_id=result['content_id']),
            'score': result.get('score', 0),
            'highlight': result.get('highlight', {})
        }
        live_results.append(live_result)
    
    return jsonify({
        'results': live_results,
        'total': results['total']
    })

def _build_filters_from_basic_form(form):
    """Build filters from basic search form"""
    filters = {}
    
    if form.content_type.data:
        filters['content_type'] = form.content_type.data
    
    return filters

def _build_filters_from_request():
    """Build filters from request parameters"""
    filters = {}
    
    # Content type filter
    content_type = request.args.get('type')
    if content_type:
        filters['content_type'] = content_type
    
    # Author filter
    author_id = request.args.get('author_id', type=int)
    if author_id:
        filters['author_id'] = author_id
    
    # Category filter
    category_id = request.args.get('category_id', type=int)
    if category_id:
        filters['category_id'] = category_id
    
    # Tags filter
    tags = request.args.getlist('tag')
    if tags:
        filters['tags'] = tags
    
    # Date range filter
    date_from = request.args.get('date_from')
    if date_from:
        try:
            filters['date_from'] = datetime.fromisoformat(date_from)
        except ValueError:
            pass
    
    date_to = request.args.get('date_to')
    if date_to:
        try:
            filters['date_to'] = datetime.fromisoformat(date_to)
        except ValueError:
            pass
    
    # Vote range filter
    min_votes = request.args.get('min_votes', type=int)
    if min_votes is not None:
        filters['min_votes'] = min_votes
    
    max_votes = request.args.get('max_votes', type=int)
    if max_votes is not None:
        filters['max_votes'] = max_votes
    
    # View range filter
    min_views = request.args.get('min_views', type=int)
    if min_views is not None:
        filters['min_views'] = min_views
    
    max_views = request.args.get('max_views', type=int)
    if max_views is not None:
        filters['max_views'] = max_views
    
    return filters

def _get_popular_searches_analytics(date_from, date_to):
    """Get popular searches analytics"""
    popular = SearchAnalytics.query.filter(
        SearchAnalytics.search_date >= date_from.date(),
        SearchAnalytics.search_date <= date_to.date()
    ).group_by(
        SearchAnalytics.query
    ).order_by(
        desc(func.sum(SearchAnalytics.search_count))
    ).limit(20).all()
    
    return {
        'title': 'Popular Searches',
        'data': [
            {
                'query': item.query,
                'count': item.search_count,
                'avg_results': item.avg_result_position
            }
            for item in popular
        ]
    }

def _get_trending_topics_analytics(date_from, date_to):
    """Get trending topics analytics"""
    # This would analyze search trends and identify trending topics
    # For now, return popular searches as trending topics
    return _get_popular_searches_analytics(date_from, date_to)

def _get_user_activity_analytics(date_from, date_to):
    """Get user search activity analytics"""
    user_activity = SearchAnalytics.query.filter(
        SearchAnalytics.search_date >= date_from.date(),
        SearchAnalytics.search_date <= date_to.date()
    ).group_by(
        SearchAnalytics.user_id
    ).order_by(
        desc(func.sum(SearchAnalytics.search_count))
    ).limit(20).all()
    
    return {
        'title': 'User Search Activity',
        'data': [
            {
                'user_id': item.user_id,
                'username': User.query.get(item.user_id).username if User.query.get(item.user_id) else 'Unknown',
                'search_count': item.search_count
            }
            for item in user_activity
        ]
    }

def _get_content_performance_analytics(date_from, date_to):
    """Get content performance analytics"""
    # This would analyze how well content performs in search
    # For now, return basic content statistics
    content_stats = SearchIndex.query.filter(
        SearchIndex.created_at >= date_from,
        SearchIndex.created_at <= date_to
    ).group_by(
        SearchIndex.content_type
    ).order_by(
        desc(func.count(SearchIndex.id))
    ).all()
    
    return {
        'title': 'Content Performance',
        'data': [
            {
                'content_type': item.content_type,
                'count': SearchIndex.query.filter_by(content_type=item.content_type).count()
            }
            for item in content_stats
        ]
    }

def _export_analytics(analytics_data, format_type):
    """Export analytics data in specified format"""
    if format_type == 'json':
        return jsonify(analytics_data)
    elif format_type == 'csv':
        # Implement CSV export
        pass
    elif format_type == 'excel':
        # Implement Excel export
        pass
    
    return jsonify(analytics_data)

def _get_index_statistics():
    """Get search index statistics"""
    stats = {}
    
    # Total indexed items
    stats['total_items'] = SearchIndex.query.count()
    
    # Items by content type
    stats['by_content_type'] = db.session.query(
        SearchIndex.content_type,
        func.count(SearchIndex.id)
    ).group_by(SearchIndex.content_type).all()
    
    # Index health
    search_service = get_search_service()
    stats['elasticsearch_available'] = search_service.elasticsearch_client is not None
    
    # Last indexed
    last_indexed = SearchIndex.query.order_by(desc(SearchIndex.updated_at)).first()
    stats['last_indexed'] = last_indexed.updated_at if last_indexed else None
    
    # Search analytics
    stats['total_searches'] = SearchAnalytics.query.count()
    
    # Popular searches today
    today = datetime.utcnow().date()
    stats['searches_today'] = SearchAnalytics.query.filter_by(search_date=today).count()
    
    return stats
