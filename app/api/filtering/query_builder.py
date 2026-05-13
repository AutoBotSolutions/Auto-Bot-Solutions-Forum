"""
Query Builder

Builds complex database queries with filtering, sorting, and pagination.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from sqlalchemy import and_, or_, not_, func, desc, asc
from sqlalchemy.orm import Query
from datetime import datetime, timedelta
import logging

from .filter_manager import FilterManager, FilterGroup, FilterCondition
from .pagination_manager import PaginationManager, SortField

logger = logging.getLogger(__name__)

class QueryBuilder:
    """Builds complex database queries"""
    
    def __init__(self, model, session=None):
        self.model = model
        self.session = session
        self.filter_manager = FilterManager()
        self.pagination_manager = PaginationManager()
        self.query = None
        self._initialize_query()
    
    def _initialize_query(self):
        """Initialize base query"""
        if self.session:
            self.query = self.session.query(self.model)
        else:
            self.query = self.model.query
    
    def reset(self):
        """Reset query to base state"""
        self._initialize_query()
        return self
    
    def filter(self, filter_group: FilterGroup) -> 'QueryBuilder':
        """Apply filter group to query"""
        if filter_group and filter_group.conditions:
            self.query = self.filter_manager.build_sqlalchemy_filter(
                self.query, self.model, filter_group
            )
        return self
    
    def filter_by_params(self, filter_params: Dict[str, Any]) -> 'QueryBuilder':
        """Apply filters from parameters"""
        if not filter_params:
            return self
        
        conditions = []
        
        for field_name, filter_data in filter_params.items():
            if isinstance(filter_data, dict):
                # Complex filter with operator
                operator = filter_data.get('operator', 'eq')
                value = filter_data.get('value')
                
                if operator and value is not None:
                    try:
                        from .filter_manager import FilterOperator
                        op = FilterOperator(operator)
                        condition = FilterCondition(field_name, op, value)
                        conditions.append(condition)
                    except ValueError:
                        logger.warning(f"Invalid filter operator: {operator}")
            else:
                # Simple equality filter
                condition = FilterCondition(field_name, FilterOperator.EQUALS, filter_data)
                conditions.append(condition)
        
        if conditions:
            filter_group = FilterGroup(conditions, 'AND')
            self.filter(filter_group)
        
        return self
    
    def search(self, search_term: str, search_fields: List[str] = None) -> 'QueryBuilder':
        """Apply search filter"""
        if not search_term:
            return self
        
        if not search_fields:
            # Use default text fields
            search_fields = ['title', 'content', 'description']
        
        search_conditions = []
        for field_name in search_fields:
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                search_conditions.append(field.contains(search_term))
        
        if search_conditions:
            self.query = self.query.filter(or_(*search_conditions))
        
        return self
    
    def date_range(self, start_date: str = None, end_date: str = None, 
                   date_field: str = 'created_at') -> 'QueryBuilder':
        """Apply date range filter"""
        if not hasattr(self.model, date_field):
            return self
        
        date_field_attr = getattr(self.model, date_field)
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                self.query = self.query.filter(date_field_attr >= start_dt)
            except ValueError:
                logger.warning(f"Invalid start date: {start_date}")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                self.query = self.query.filter(date_field_attr <= end_dt)
            except ValueError:
                logger.warning(f"Invalid end date: {end_date}")
        
        return self
    
    def recent(self, days: int = 7, date_field: str = 'created_at') -> 'QueryBuilder':
        """Filter for recent items"""
        if not hasattr(self.model, date_field):
            return self
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        date_field_attr = getattr(self.model, date_field)
        self.query = self.query.filter(date_field_attr >= cutoff_date)
        
        return self
    
    def popular(self, days: int = 30, count_field: str = 'view_count') -> 'QueryBuilder':
        """Filter for popular items"""
        if not hasattr(self.model, count_field):
            return self
        
        # Apply recent filter first
        self.recent(days)
        
        # Sort by count field
        count_field_attr = getattr(self.model, count_field)
        self.query = self.query.order_by(desc(count_field_attr))
        
        return self
    
    def trending(self, days: int = 7, count_field: str = 'view_count') -> 'QueryBuilder':
        """Filter for trending items"""
        if not hasattr(self.model, count_field):
            return self
        
        # Apply recent filter
        self.recent(days)
        
        # Apply minimum threshold for trending
        count_field_attr = getattr(self.model, count_field)
        self.query = self.query.filter(count_field_attr >= 10)
        
        # Sort by count field
        self.query = self.query.order_by(desc(count_field_attr))
        
        return self
    
    def sort(self, sort_fields: List[SortField]) -> 'QueryBuilder':
        """Apply sorting to query"""
        self.query = self.pagination_manager.apply_sorting(
            self.query, sort_fields, self.model
        )
        return self
    
    def sort_by_params(self, sort_params: str) -> 'QueryBuilder':
        """Apply sorting from parameters"""
        sort_fields = self.pagination_manager._parse_sort_param(sort_params)
        return self.sort(sort_fields)
    
    def paginate(self, pagination_params: Dict[str, Any]) -> tuple:
        """Apply pagination and return results with metadata"""
        paginated_query, pagination_result = self.pagination_manager.apply_pagination(
            self.query, pagination_params
        )
        
        # Execute query
        results = paginated_query.all()
        
        return results, pagination_result
    
    def count(self) -> int:
        """Get count of results"""
        return self.query.count()
    
    def exists(self) -> bool:
        """Check if any results exist"""
        return self.query.first() is not None
    
    def first(self):
        """Get first result"""
        return self.query.first()
    
    def all(self):
        """Get all results"""
        return self.query.all()
    
    def limit(self, limit: int) -> 'QueryBuilder':
        """Apply limit to query"""
        self.query = self.query.limit(limit)
        return self
    
    def offset(self, offset: int) -> 'QueryBuilder':
        """Apply offset to query"""
        self.query = self.query.offset(offset)
        return self
    
    def join(self, *args, **kwargs) -> 'QueryBuilder':
        """Join with other models"""
        self.query = self.query.join(*args, **kwargs)
        return self
    
    def distinct(self) -> 'QueryBuilder':
        """Apply distinct to query"""
        self.query = self.query.distinct()
        return self
    
    def group_by(self, *args) -> 'QueryBuilder':
        """Apply group by to query"""
        self.query = self.query.group_by(*args)
        return self
    
    def having(self, *args) -> 'QueryBuilder':
        """Apply having to query"""
        self.query = self.query.having(*args)
        return self
    
    def with_entities(self, *entities) -> 'QueryBuilder':
        """Change query entities"""
        self.query = self.query.with_entities(*entities)
        return self
    
    def add_columns(self, *columns) -> 'QueryBuilder':
        """Add columns to query"""
        self.query = self.query.add_columns(*columns)
        return self
    
    def get_query(self) -> Query:
        """Get the current query"""
        return self.query
    
    def get_sql(self) -> str:
        """Get SQL representation of query"""
        try:
            return str(self.query.statement.compile(compile_kwargs={"literal_binds": True}))
        except Exception as e:
            logger.error(f"Error getting SQL: {e}")
            return str(self.query)

class AdvancedQueryBuilder(QueryBuilder):
    """Advanced query builder with additional features"""
    
    def __init__(self, model, session=None):
        super().__init__(model, session)
        self.aggregations = {}
        self.having_conditions = []
        self.custom_filters = []
    
    def aggregate(self, field: str, function: str = 'count', alias: str = None) -> 'AdvancedQueryBuilder':
        """Add aggregation to query"""
        if not alias:
            alias = f"{function}_{field}"
        
        field_attr = getattr(self.model, field)
        
        if function == 'count':
            agg_func = func.count(field_attr)
        elif function == 'sum':
            agg_func = func.sum(field_attr)
        elif function == 'avg':
            agg_func = func.avg(field_attr)
        elif function == 'min':
            agg_func = func.min(field_attr)
        elif function == 'max':
            agg_func = func.max(field_attr)
        else:
            raise ValueError(f"Unsupported aggregation function: {function}")
        
        self.aggregations[alias] = agg_func
        return self
    
    def having_count(self, field: str, operator: str, value: int) -> 'AdvancedQueryBuilder':
        """Add having condition for count"""
        self.having_conditions.append({
            'type': 'count',
            'field': field,
            'operator': operator,
            'value': value
        })
        return self
    
    def having_sum(self, field: str, operator: str, value: Union[int, float]) -> 'AdvancedQueryBuilder':
        """Add having condition for sum"""
        self.having_conditions.append({
            'type': 'sum',
            'field': field,
            'operator': operator,
            'value': value
        })
        return self
    
    def having_avg(self, field: str, operator: str, value: Union[int, float]) -> 'AdvancedQueryBuilder':
        """Add having condition for average"""
        self.having_conditions.append({
            'type': 'avg',
            'field': field,
            'operator': operator,
            'value': value
        })
        return self
    
    def apply_aggregations(self) -> 'AdvancedQueryBuilder':
        """Apply aggregations to query"""
        if self.aggregations:
            self.query = self.query.with_entities(*[
                getattr(self.model, field) if field in self.aggregations else getattr(self.model, field)
                for field in set([attr.name for attr in self.model.__table__.columns] + list(self.aggregations.keys()))
            ])
        
        return self
    
    def apply_having_conditions(self) -> 'AdvancedQueryBuilder':
        """Apply having conditions to query"""
        for condition in self.having_conditions:
            field_attr = getattr(self.model, condition['field'])
            
            if condition['type'] == 'count':
                agg_func = func.count(field_attr)
            elif condition['type'] == 'sum':
                agg_func = func.sum(field_attr)
            elif condition['type'] == 'avg':
                agg_func = func.avg(field_attr)
            else:
                continue
            
            operator = condition['operator']
            value = condition['value']
            
            if operator == 'gt':
                self.query = self.query.having(agg_func > value)
            elif operator == 'gte':
                self.query = self.query.having(agg_func >= value)
            elif operator == 'lt':
                self.query = self.query.having(agg_func < value)
            elif operator == 'lte':
                self.query = self.query.having(agg_func <= value)
            elif operator == 'eq':
                self.query = self.query.having(agg_func == value)
            elif operator == 'ne':
                self.query = self.query.having(agg_func != value)
        
        return self
    
    def group_by_field(self, field: str) -> 'AdvancedQueryBuilder':
        """Group by field"""
        field_attr = getattr(self.model, field)
        self.query = self.query.group_by(field_attr)
        return self
    
    def custom_filter(self, filter_func: Callable[[Query], Query]) -> 'AdvancedQueryBuilder':
        """Apply custom filter function"""
        self.custom_filters.append(filter_func)
        self.query = filter_func(self.query)
        return self
    
    def build_advanced_query(self) -> Query:
        """Build the complete advanced query"""
        # Apply aggregations
        if self.aggregations:
            self.apply_aggregations()
        
        # Apply having conditions
        if self.having_conditions:
            self.apply_having_conditions()
        
        return self.query
    
    def execute_with_stats(self) -> Dict[str, Any]:
        """Execute query and return results with statistics"""
        start_time = datetime.utcnow()
        
        # Get count before pagination
        total_count = self.count()
        
        # Execute query
        results = self.all()
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        return {
            'results': results,
            'total_count': total_count,
            'execution_time': execution_time,
            'query_sql': self.get_sql(),
            'aggregations': self.aggregations,
            'having_conditions': self.having_conditions
        }

class SearchQueryBuilder(QueryBuilder):
    """Specialized query builder for search functionality"""
    
    def __init__(self, model, session=None):
        super().__init__(model, session)
        self.search_config = {
            'fields': ['title', 'content', 'description'],
            'weights': {'title': 3.0, 'content': 2.0, 'description': 1.0},
            'min_length': 2,
            'fuzzy_threshold': 0.8
        }
    
    def configure_search(self, fields: List[str] = None, weights: Dict[str, float] = None,
                        min_length: int = 2, fuzzy_threshold: float = 0.8):
        """Configure search settings"""
        if fields:
            self.search_config['fields'] = fields
        if weights:
            self.search_config['weights'] = weights
        self.search_config['min_length'] = min_length
        self.search_config['fuzzy_threshold'] = fuzzy_threshold
    
    def full_text_search(self, search_term: str) -> 'SearchQueryBuilder':
        """Apply full-text search"""
        if not search_term or len(search_term) < self.search_config['min_length']:
            return self
        
        # Split search term into words
        words = search_term.split()
        
        search_conditions = []
        for field_name in self.search_config['fields']:
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                weight = self.search_config['weights'].get(field_name, 1.0)
                
                # Create conditions for each word
                word_conditions = []
                for word in words:
                    word_conditions.append(field.contains(word))
                
                # Combine word conditions with OR
                if word_conditions:
                    field_condition = or_(*word_conditions)
                    search_conditions.append(field_condition)
        
        if search_conditions:
            # Combine all field conditions with OR
            self.query = self.query.filter(or_(*search_conditions))
        
        return self
    
    def fuzzy_search(self, search_term: str) -> 'SearchQueryBuilder':
        """Apply fuzzy search (simplified implementation)"""
        if not search_term:
            return self
        
        # This is a simplified fuzzy search
        # In production, you might use PostgreSQL's pg_trgm or other fuzzy search libraries
        search_conditions = []
        
        for field_name in self.search_config['fields']:
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                
                # Simple fuzzy matching using LIKE
                fuzzy_pattern = f"%{search_term}%"
                search_conditions.append(field.ilike(fuzzy_pattern))
        
        if search_conditions:
            self.query = self.query.filter(or_(*search_conditions))
        
        return self
    
    def ranked_search(self, search_term: str) -> 'SearchQueryBuilder':
        """Apply ranked search with scoring"""
        if not search_term:
            return self
        
        # Add scoring column
        score_expressions = []
        
        for field_name in self.search_config['fields']:
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                weight = self.search_config['weights'].get(field_name, 1.0)
                
                # Simple scoring based on contains
                score_expr = func.coalesce(
                    func.cast(func.case([(field.contains(search_term), weight)], func.Float), 0.0)
                )
                score_expressions.append(score_expr)
        
        if score_expressions:
            # Add score column
            total_score = sum(score_expressions)
            self.query = self.query.add_columns(total_score.label('search_score'))
            
            # Filter to only include results with score > 0
            self.query = self.query.filter(total_score > 0)
            
            # Order by score
            self.query = self.query.order_by(desc(total_score))
        
        return self
    
    def search_with_filters(self, search_term: str, filters: Dict[str, Any] = None,
                          sort: str = None) -> tuple:
        """Execute search with filters and sorting"""
        # Apply search
        self.full_text_search(search_term)
        
        # Apply filters
        if filters:
            self.filter_by_params(filters)
        
        # Apply sorting
        if sort:
            self.sort_by_params(sort)
        else:
            # Default sort by relevance for search
            self.ranked_search(search_term)
        
        # Return results
        return self.all(), self.count()
