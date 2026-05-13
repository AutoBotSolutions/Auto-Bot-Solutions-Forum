"""
Message Search Utilities

Provides comprehensive search functionality for messages including:
- Full-text search with keyword extraction
- Advanced search with Boolean operators
- Search result highlighting
- Search analytics tracking
- Content analysis and sentiment detection
"""

import re
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from flask import current_app
from sqlalchemy import text, or_, and_, func
from app import db
from app.models import Message, MessageSearchIndex, MessageSearchAnalytics, User


class MessageSearchEngine:
    """Advanced message search engine with full-text search capabilities"""
    
    def __init__(self):
        self.stop_words = self._load_stop_words()
        self.search_analytics_enabled = True
    
    def _load_stop_words(self) -> set:
        """Load common stop words for filtering"""
        return {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
            'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
            'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
            'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my',
            'one', 'all', 'would', 'there', 'their', 'what', 'so',
            'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go',
            'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just',
            'him', 'know', 'take', 'people', 'into', 'year', 'your',
            'good', 'some', 'could', 'them', 'see', 'other', 'than',
            'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think',
            'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work',
            'first', 'well', 'way', 'even', 'new', 'want', 'because',
            'any', 'these', 'give', 'day', 'most', 'us', 'is', 'was',
            'are', 'been', 'has', 'had', 'were', 'said', 'did', 'getting',
            'made', 'find', 'where', 'much', 'too', 'very', 'still',
            'being', 'going', 'why', 'before', 'never', 'here', 'more'
        }
    
    def search_messages(
        self,
        query: str,
        user_id: int,
        filters: Optional[Dict] = None,
        sort_by: str = 'relevance',
        page: int = 1,
        per_page: int = 20,
        search_type: str = 'basic'
    ) -> Dict:
        """
        Search messages with advanced filtering and sorting
        
        Args:
            query: Search query string
            user_id: User ID performing the search
            filters: Dictionary of search filters
            sort_by: Sort method ('relevance', 'date', 'sender')
            page: Page number
            per_page: Results per page
            search_type: Type of search ('basic', 'advanced', 'boolean')
        
        Returns:
            Dictionary with search results and metadata
        """
        start_time = time.time()
        
        # Build base query
        base_query = self._build_base_query(user_id, filters)
        
        # Apply search conditions
        if search_type == 'boolean':
            search_conditions = self._build_boolean_search(query)
        elif search_type == 'advanced':
            search_conditions = self._build_advanced_search(query)
        else:
            search_conditions = self._build_basic_search(query)
        
        # Apply search to base query
        search_query = base_query.filter(search_conditions)
        
        # Apply sorting
        search_query = self._apply_sorting(search_query, sort_by)
        
        # Execute search with pagination
        total_results = search_query.count()
        results = search_query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Calculate search time
        search_time = time.time() - start_time
        
        # Record search analytics
        if self.search_analytics_enabled:
            self._record_search_analytics(
                user_id=user_id,
                query=query,
                search_type=search_type,
                results_count=total_results,
                search_time=search_time,
                filters=filters,
                sort_by=sort_by
            )
        
        # Process results with highlighting
        processed_results = []
        for message in results:
            processed_message = {
                'id': message.id,
                'sender_id': message.sender_id,
                'receiver_id': message.receiver_id,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'is_read': message.is_read,
                'sender_name': message.sender.username if message.sender else 'Unknown',
                'highlighted_content': self._highlight_search_terms(message.content, query),
                'relevance_score': self._calculate_relevance_score(message, query)
            }
            processed_results.append(processed_message)
        
        return {
            'results': processed_results,
            'total_results': total_results,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_results + per_page - 1) // per_page,
            'search_time': search_time,
            'query': query,
            'filters': filters or {},
            'sort_by': sort_by,
            'search_type': search_type
        }
    
    def _build_base_query(self, user_id: int, filters: Optional[Dict]) -> db.Query:
        """Build base query for message search"""
        # Base query - user can only search messages they sent or received
        query = Message.query.filter(
            or_(
                Message.sender_id == user_id,
                Message.receiver_id == user_id
            ),
            Message.is_deleted == False
        )
        
        # Apply filters
        if filters:
            # Date filter
            if 'date_from' in filters:
                query = query.filter(Message.created_at >= filters['date_from'])
            if 'date_to' in filters:
                query = query.filter(Message.created_at <= filters['date_to'])
            
            # Sender filter
            if 'sender_id' in filters:
                query = query.filter(Message.sender_id == filters['sender_id'])
            
            # Status filter
            if 'is_read' in filters:
                query = query.filter(Message.is_read == filters['is_read'])
            
            # Priority filter
            if 'priority' in filters:
                query = query.filter(Message.priority == filters['priority'])
            
            # Attachment filter
            if 'has_attachments' in filters:
                query = query.filter(Message.has_attachments == filters['has_attachments'])
            
            # Thread filter
            if 'thread_id' in filters:
                query = query.filter(Message.thread_id == filters['thread_id'])
        
        return query
    
    def _build_basic_search(self, query: str) -> db.sql.expression.BooleanClauseList:
        """Build basic search conditions"""
        if not query.strip():
            return True
        
        # Split query into terms
        terms = query.split()
        conditions = []
        
        for term in terms:
            if term.lower() not in self.stop_words:
                # Search in message content
                content_condition = Message.content.ilike(f'%{term}%')
                conditions.append(content_condition)
        
        if conditions:
            return and_(*conditions)
        else:
            return True
    
    def _build_advanced_search(self, query: str) -> db.sql.expression.BooleanClauseList:
        """Build advanced search with field-specific operators"""
        if not query.strip():
            return True
        
        conditions = []
        
        # Parse advanced search syntax
        # Format: field:value OR "exact phrase" OR -exclude_term
        pattern = r'(\w+):(["\']?[^"\'\s]+["\']?)|(["\'][^"\']+["\'])|(-\w+)'
        matches = re.findall(pattern, query)
        
        for match in matches:
            field, value, exact_phrase, exclude_term = match
            
            if field and value:
                # Field-specific search
                if field.lower() == 'sender':
                    # Search by sender username
                    user = User.query.filter(User.username.ilike(f'%{value}%')).first()
                    if user:
                        conditions.append(Message.sender_id == user.id)
                elif field.lower() == 'content':
                    conditions.append(Message.content.ilike(f'%{value}%'))
                elif field.lower() == 'date':
                    # Parse date and filter
                    try:
                        date_obj = datetime.strptime(value, '%Y-%m-%d')
                        conditions.append(func.date(Message.created_at) == date_obj.date())
                    except ValueError:
                        pass
            
            elif exact_phrase:
                # Exact phrase search
                clean_phrase = exact_phrase.strip('"\'')
                conditions.append(Message.content.ilike(f'%{clean_phrase}%'))
            
            elif exclude_term:
                # Exclude term
                clean_term = exclude_term.lstrip('-')
                conditions.append(~Message.content.ilike(f'%{clean_term}%'))
        
        # If no specific conditions found, fall back to basic search
        if not conditions:
            return self._build_basic_search(query)
        
        return and_(*conditions)
    
    def _build_boolean_search(self, query: str) -> db.sql.expression.BooleanClauseList:
        """Build Boolean search with AND, OR, NOT operators"""
        if not query.strip():
            return True
        
        # Parse Boolean operators
        # Replace operators with SQL-friendly equivalents
        processed_query = query
        
        # Handle quoted phrases
        quoted_phrases = re.findall(r'"([^"]+)"', processed_query)
        for phrase in quoted_phrases:
            placeholder = f"QUOTE_{len(phrase)}"
            processed_query = processed_query.replace(f'"{phrase}"', placeholder)
        
        # Handle NOT operator
        not_terms = re.findall(r'NOT\s+(\w+)', processed_query)
        exclude_conditions = []
        for term in not_terms:
            exclude_conditions.append(~Message.content.ilike(f'%{term}%'))
            processed_query = processed_query.replace(f'NOT {term}', '')
        
        # Handle AND/OR operators
        and_terms = re.findall(r'AND\s+(\w+)', processed_query)
        or_terms = re.findall(r'OR\s+(\w+)', processed_query)
        
        include_conditions = []
        
        # Add quoted phrases
        for phrase in quoted_phrases:
            include_conditions.append(Message.content.ilike(f'%{phrase}%'))
        
        # Add remaining terms
        remaining_terms = re.findall(r'\b\w+\b', processed_query)
        for term in remaining_terms:
            if term.upper() not in ['AND', 'OR', 'NOT'] and term.lower() not in self.stop_words:
                include_conditions.append(Message.content.ilike(f'%{term}%'))
        
        # Combine conditions
        all_conditions = []
        
        if include_conditions:
            if or_terms:
                # Use OR for specified terms
                all_conditions.append(or_(*include_conditions))
            else:
                # Use AND for all terms
                all_conditions.append(and_(*include_conditions))
        
        if exclude_conditions:
            all_conditions.extend(exclude_conditions)
        
        if all_conditions:
            return and_(*all_conditions)
        else:
            return True
    
    def _apply_sorting(self, query: db.Query, sort_by: str) -> db.Query:
        """Apply sorting to search results"""
        if sort_by == 'date':
            return query.order_by(Message.created_at.desc())
        elif sort_by == 'sender':
            return query.join(User, Message.sender_id == User.id).order_by(User.username)
        elif sort_by == 'relevance':
            # For relevance, we'd ideally use search index scores
            # For now, sort by creation date as a proxy
            return query.order_by(Message.created_at.desc())
        else:
            return query.order_by(Message.created_at.desc())
    
    def _highlight_search_terms(self, content: str, query: str) -> str:
        """Highlight search terms in message content"""
        if not query.strip():
            return content
        
        # Extract search terms
        terms = re.findall(r'\b\w+\b', query.lower())
        terms = [term for term in terms if term.lower() not in self.stop_words]
        
        highlighted_content = content
        for term in terms:
            # Case-insensitive highlighting
            pattern = re.compile(f'({re.escape(term)})', re.IGNORECASE)
            highlighted_content = pattern.sub(r'<mark>\1</mark>', highlighted_content)
        
        return highlighted_content
    
    def _calculate_relevance_score(self, message: Message, query: str) -> float:
        """Calculate relevance score for a message"""
        if not query.strip():
            return 1.0
        
        score = 0.0
        terms = re.findall(r'\b\w+\b', query.lower())
        terms = [term for term in terms if term.lower() not in self.stop_words]
        
        content_lower = message.content.lower()
        
        for term in terms:
            # Exact matches get higher score
            if term in content_lower:
                score += 1.0
                
                # Bonus for term frequency
                term_count = content_lower.count(term)
                if term_count > 1:
                    score += 0.5 * (term_count - 1)
        
        # Normalize score
        if terms:
            score = score / len(terms)
        
        return min(score, 5.0)  # Cap at 5.0
    
    def _record_search_analytics(
        self,
        user_id: int,
        query: str,
        search_type: str,
        results_count: int,
        search_time: float,
        filters: Optional[Dict],
        sort_by: str
    ):
        """Record search analytics"""
        try:
            analytics = MessageSearchAnalytics(
                user_id=user_id,
                search_query=query,
                search_type=search_type,
                results_count=results_count,
                search_time=search_time,
                filters=json.dumps(filters) if filters else None,
                sort_by=sort_by
            )
            db.session.add(analytics)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to record search analytics: {e}")
            db.session.rollback()


def extract_keywords(content: str) -> str:
    """Extract keywords from message content"""
    search_engine = MessageSearchEngine()
    
    # Tokenize and filter
    words = re.findall(r'\b\w+\b', content.lower())
    keywords = [word for word in words if word not in search_engine.stop_words and len(word) > 2]
    
    # Remove duplicates and limit to top keywords
    unique_keywords = list(set(keywords))
    unique_keywords.sort(key=lambda x: len(x), reverse=True)
    
    return json.dumps(unique_keywords[:20])  # Top 20 keywords


def generate_search_vector(content: str) -> str:
    """Generate search vector for full-text search"""
    # Normalize content
    normalized = re.sub(r'[^\w\s]', ' ', content.lower())
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def analyze_content(content: str) -> Dict:
    """Analyze message content for sentiment and other metrics"""
    # Simple sentiment analysis based on positive/negative words
    positive_words = {
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'love', 'like', 'awesome', 'perfect', 'best', 'happy', 'pleased'
    }
    
    negative_words = {
        'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'worst',
        'angry', 'sad', 'upset', 'frustrated', 'disappointed', 'poor'
    }
    
    words = re.findall(r'\b\w+\b', content.lower())
    
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    
    # Calculate sentiment score (-1 to 1)
    total_sentiment_words = positive_count + negative_count
    if total_sentiment_words > 0:
        sentiment = (positive_count - negative_count) / total_sentiment_words
    else:
        sentiment = 0.0
    
    return {
        'sentiment': sentiment,
        'word_count': len(words),
        'positive_words': positive_count,
        'negative_words': negative_count
    }


def get_search_suggestions(query: str, user_id: int, limit: int = 10) -> List[str]:
    """Get search suggestions based on previous searches"""
    # Get recent searches from this user
    recent_searches = MessageSearchAnalytics.query.filter(
        MessageSearchAnalytics.user_id == user_id,
        MessageSearchAnalytics.search_query.ilike(f'%{query}%')
    ).order_by(MessageSearchAnalytics.created_at.desc()).limit(limit * 2).all()
    
    # Extract unique suggestions
    suggestions = []
    seen_queries = set()
    
    for search in recent_searches:
        if search.search_query not in seen_queries and len(suggestions) < limit:
            suggestions.append(search.search_query)
            seen_queries.add(search.search_query)
    
    return suggestions


def get_popular_search_terms(days: int = 30, limit: int = 10) -> List[Dict]:
    """Get popular search terms from analytics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Group by search query and count
    popular_terms = db.session.query(
        MessageSearchAnalytics.search_query,
        func.count(MessageSearchAnalytics.id).label('search_count'),
        func.avg(MessageSearchAnalytics.results_count).label('avg_results')
    ).filter(
        MessageSearchAnalytics.created_at >= start_date
    ).group_by(
        MessageSearchAnalytics.search_query
    ).order_by(
        func.count(MessageSearchAnalytics.id).desc()
    ).limit(limit).all()
    
    return [
        {
            'query': term.search_query,
            'search_count': term.search_count,
            'avg_results': float(term.avg_results)
        }
        for term in popular_terms
    ]


def get_search_analytics_summary(user_id: Optional[int] = None, days: int = 30) -> Dict:
    """Get search analytics summary"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = MessageSearchAnalytics.query.filter(
        MessageSearchAnalytics.created_at >= start_date
    )
    
    if user_id:
        query = query.filter(MessageSearchAnalytics.user_id == user_id)
    
    # Basic statistics
    total_searches = query.count()
    avg_results = db.session.query(func.avg(MessageSearchAnalytics.results_count)).filter(
        MessageSearchAnalytics.created_at >= start_date
    ).scalar() or 0
    
    avg_search_time = db.session.query(func.avg(MessageSearchAnalytics.search_time)).filter(
        MessageSearchAnalytics.created_at >= start_date
    ).scalar() or 0
    
    # Search types distribution
    search_types = db.session.query(
        MessageSearchAnalytics.search_type,
        func.count(MessageSearchAnalytics.id).label('count')
    ).filter(
        MessageSearchAnalytics.created_at >= start_date
    ).group_by(MessageSearchAnalytics.search_type).all()
    
    search_type_distribution = {
        search_type: count for search_type, count in search_types
    }
    
    return {
        'total_searches': total_searches,
        'avg_results_per_search': float(avg_results),
        'avg_search_time': float(avg_search_time),
        'search_type_distribution': search_type_distribution,
        'days_analyzed': days
    }
