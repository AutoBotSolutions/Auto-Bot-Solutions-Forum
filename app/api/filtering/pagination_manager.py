"""
Pagination Manager

Manages pagination for API endpoints with support for different
pagination strategies and cursor-based pagination.
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PaginationType(Enum):
    """Pagination types"""
    OFFSET = "offset"
    CURSOR = "cursor"
    PAGE = "page"
    SEEK = "seek"

class SortDirection(Enum):
    """Sort directions"""
    ASC = "asc"
    DESC = "desc"

@dataclass
class SortField:
    """Represents a sortable field"""
    name: str
    direction: SortDirection = SortDirection.ASC
    nulls_first: bool = True

@dataclass
class PaginationResult:
    """Pagination result metadata"""
    total_items: int
    total_pages: int
    current_page: int
    per_page: int
    has_next: bool
    has_previous: bool
    next_cursor: Optional[str] = None
    previous_cursor: Optional[str] = None
    first_item_index: int = 0
    last_item_index: int = 0

class PaginationManager:
    """Manages pagination operations"""
    
    def __init__(self):
        self.default_per_page = 20
        self.max_per_page = 100
        self.default_type = PaginationType.OFFSET
        self.sortable_fields: Dict[str, List[str]] = {}
    
    def register_sortable_fields(self, resource: str, fields: List[str]):
        """Register sortable fields for a resource"""
        self.sortable_fields[resource] = fields
    
    def get_sortable_fields(self, resource: str) -> List[str]:
        """Get sortable fields for a resource"""
        return self.sortable_fields.get(resource, [])
    
    def parse_pagination_params(self, params: Dict[str, Any], 
                               pagination_type: PaginationType = None) -> Dict[str, Any]:
        """Parse pagination parameters from request"""
        pagination_type = pagination_type or self.default_type
        
        result = {
            'type': pagination_type,
            'per_page': self.default_per_page,
            'sort_fields': []
        }
        
        if pagination_type == PaginationType.OFFSET:
            result['offset'] = params.get('offset', 0)
            result['page'] = params.get('page', 1)
        elif pagination_type == PaginationType.CURSOR:
            result['cursor'] = params.get('cursor')
            result['limit'] = params.get('limit', self.default_per_page)
        elif pagination_type == PaginationType.PAGE:
            result['page'] = params.get('page', 1)
        elif pagination_type == PaginationType.SEEK:
            result['seek_value'] = params.get('seek_value')
            result['seek_field'] = params.get('seek_field', 'id')
        
        # Parse per_page/limit
        per_page = params.get('per_page') or params.get('limit')
        if per_page:
            try:
                per_page = int(per_page)
                result['per_page'] = min(per_page, self.max_per_page)
            except ValueError:
                pass
        
        # Parse sort parameters
        sort_param = params.get('sort')
        if sort_param:
            result['sort_fields'] = self._parse_sort_param(sort_param)
        
        return result
    
    def _parse_sort_param(self, sort_param: str) -> List[SortField]:
        """Parse sort parameter string"""
        sort_fields = []
        
        if not sort_param:
            return sort_fields
        
        # Parse comma-separated sort fields
        parts = sort_param.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Parse direction
            if part.startswith('-'):
                field_name = part[1:]
                direction = SortDirection.DESC
            elif part.startswith('+'):
                field_name = part[1:]
                direction = SortDirection.ASC
            else:
                field_name = part
                direction = SortDirection.ASC
            
            sort_fields.append(SortField(field_name, direction))
        
        return sort_fields
    
    def validate_pagination_params(self, params: Dict[str, Any], 
                                 resource: str = None) -> Tuple[bool, List[str]]:
        """Validate pagination parameters"""
        errors = []
        
        # Validate per_page
        if params.get('per_page'):
            try:
                per_page = int(params['per_page'])
                if per_page < 1:
                    errors.append("per_page must be at least 1")
                elif per_page > self.max_per_page:
                    errors.append(f"per_page cannot exceed {self.max_per_page}")
            except ValueError:
                errors.append("per_page must be a valid integer")
        
        # Validate page/offset
        if params.get('page'):
            try:
                page = int(params['page'])
                if page < 1:
                    errors.append("page must be at least 1")
            except ValueError:
                errors.append("page must be a valid integer")
        
        if params.get('offset'):
            try:
                offset = int(params['offset'])
                if offset < 0:
                    errors.append("offset cannot be negative")
            except ValueError:
                errors.append("offset must be a valid integer")
        
        # Validate sort fields
        if resource and params.get('sort_fields'):
            sortable_fields = self.get_sortable_fields(resource)
            for sort_field in params['sort_fields']:
                if sort_field.name not in sortable_fields:
                    errors.append(f"Cannot sort by field: {sort_field.name}")
        
        return len(errors) == 0, errors
    
    def apply_pagination(self, query, pagination_params: Dict[str, Any], 
                        pagination_type: PaginationType = None) -> Tuple[Any, PaginationResult]:
        """Apply pagination to query"""
        pagination_type = pagination_type or pagination_params.get('type', self.default_type)
        
        if pagination_type == PaginationType.OFFSET:
            return self._apply_offset_pagination(query, pagination_params)
        elif pagination_type == PaginationType.CURSOR:
            return self._apply_cursor_pagination(query, pagination_params)
        elif pagination_type == PaginationType.PAGE:
            return self._apply_page_pagination(query, pagination_params)
        elif pagination_type == PaginationType.SEEK:
            return self._apply_seek_pagination(query, pagination_params)
        else:
            raise ValueError(f"Unsupported pagination type: {pagination_type}")
    
    def _apply_offset_pagination(self, query, params: Dict[str, Any]) -> Tuple[Any, PaginationResult]:
        """Apply offset-based pagination"""
        per_page = params.get('per_page', self.default_per_page)
        offset = params.get('offset', 0)
        page = params.get('page', 1)
        
        # Calculate actual offset
        if page > 1:
            offset = (page - 1) * per_page
        
        # Get total count
        total_items = query.count()
        
        # Apply pagination
        paginated_query = query.offset(offset).limit(per_page)
        
        # Calculate pagination metadata
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
        current_page = (offset // per_page) + 1
        has_next = current_page < total_pages
        has_previous = current_page > 1
        first_item_index = offset + 1
        last_item_index = min(offset + per_page, total_items)
        
        result = PaginationResult(
            total_items=total_items,
            total_pages=total_pages,
            current_page=current_page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous,
            first_item_index=first_item_index,
            last_item_index=last_item_index
        )
        
        return paginated_query, result
    
    def _apply_cursor_pagination(self, query, params: Dict[str, Any]) -> Tuple[Any, PaginationResult]:
        """Apply cursor-based pagination"""
        per_page = params.get('per_page', self.default_per_page)
        cursor = params.get('cursor')
        
        # Apply cursor filter if provided
        if cursor:
            # Decode cursor and apply filter
            # This is a simplified implementation
            try:
                cursor_data = self._decode_cursor(cursor)
                if cursor_data:
                    field_name, value = cursor_data
                    query = query.filter(getattr(query.column_descriptions[0]['type'], field_name) > value)
            except Exception as e:
                logger.error(f"Error decoding cursor: {e}")
        
        # Apply limit
        paginated_query = query.limit(per_page + 1)  # +1 to check if there's next
        
        # Execute query to get results
        results = paginated_query.all()
        
        # Check if there are more results
        has_next = len(results) > per_page
        if has_next:
            results = results[:-1]  # Remove the extra item
        
        # Generate next cursor
        next_cursor = None
        if has_next and results:
            last_item = results[-1]
            next_cursor = self._encode_cursor(last_item.id, 'id')
        
        # Create pagination result (cursor pagination doesn't have total counts)
        result = PaginationResult(
            total_items=None,  # Not available in cursor pagination
            total_pages=None,
            current_page=None,
            per_page=per_page,
            has_next=has_next,
            has_previous=cursor is not None,
            next_cursor=next_cursor,
            previous_cursor=self._get_previous_cursor(cursor),
            first_item_index=0,
            last_item_index=len(results)
        )
        
        return query.filter(getattr(query.column_descriptions[0]['type'], 'id').in_([r.id for r in results])), result
    
    def _apply_page_pagination(self, query, params: Dict[str, Any]) -> Tuple[Any, PaginationResult]:
        """Apply page-based pagination"""
        per_page = params.get('per_page', self.default_per_page)
        page = params.get('page', 1)
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        total_items = query.count()
        
        # Apply pagination
        paginated_query = query.offset(offset).limit(per_page)
        
        # Calculate pagination metadata
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1
        first_item_index = offset + 1
        last_item_index = min(offset + per_page, total_items)
        
        result = PaginationResult(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous,
            first_item_index=first_item_index,
            last_item_index=last_item_index
        )
        
        return paginated_query, result
    
    def _apply_seek_pagination(self, query, params: Dict[str, Any]) -> Tuple[Any, PaginationResult]:
        """Apply seek method pagination"""
        per_page = params.get('per_page', self.default_per_page)
        seek_value = params.get('seek_value')
        seek_field = params.get('seek_field', 'id')
        
        # Apply seek filter if provided
        if seek_value:
            query = query.filter(getattr(query.column_descriptions[0]['type'], seek_field) > seek_value)
        
        # Apply limit
        paginated_query = query.limit(per_page + 1)  # +1 to check if there's next
        
        # Execute query to get results
        results = paginated_query.all()
        
        # Check if there are more results
        has_next = len(results) > per_page
        if has_next:
            results = results[:-1]  # Remove the extra item
        
        # Generate next seek value
        next_seek_value = None
        if has_next and results:
            last_item = results[-1]
            next_seek_value = str(getattr(last_item, seek_field))
        
        # Create pagination result
        result = PaginationResult(
            total_items=None,  # Not available in seek pagination
            total_pages=None,
            current_page=None,
            per_page=per_page,
            has_next=has_next,
            has_previous=seek_value is not None,
            next_cursor=next_seek_value,
            previous_cursor=seek_value,
            first_item_index=0,
            last_item_index=len(results)
        )
        
        return query.filter(getattr(query.column_descriptions[0]['type'], 'id').in_([r.id for r in results])), result
    
    def _encode_cursor(self, value: Any, field: str) -> str:
        """Encode cursor value"""
        # Simple encoding - in production, use proper encoding
        return f"{field}:{value}"
    
    def _decode_cursor(self, cursor: str) -> Optional[Tuple[str, Any]]:
        """Decode cursor value"""
        try:
            parts = cursor.split(':', 1)
            if len(parts) == 2:
                return parts[0], parts[1]
        except Exception:
            pass
        return None
    
    def _get_previous_cursor(self, current_cursor: Optional[str]) -> Optional[str]:
        """Get previous cursor (would need to be implemented based on context)"""
        # This is a simplified implementation
        return None
    
    def apply_sorting(self, query, sort_fields: List[SortField], model):
        """Apply sorting to query"""
        from sqlalchemy import asc, desc
        
        for sort_field in sort_fields:
            field_attr = getattr(model, sort_field.name, None)
            if field_attr:
                if sort_field.direction == SortDirection.ASC:
                    query = query.order_by(asc(field_attr))
                else:
                    query = query.order_by(desc(field_attr))
        
        return query
    
    def create_pagination_links(self, request_url: str, pagination_result: PaginationResult,
                              pagination_params: Dict[str, Any]) -> Dict[str, str]:
        """Create pagination links"""
        links = {}
        
        if pagination_result.current_page:
            # Self link
            links['self'] = f"{request_url}?page={pagination_result.current_page}&per_page={pagination_result.per_page}"
            
            # First page
            if pagination_result.current_page > 1:
                links['first'] = f"{request_url}?page=1&per_page={pagination_result.per_page}"
            
            # Previous page
            if pagination_result.has_previous:
                prev_page = pagination_result.current_page - 1
                links['prev'] = f"{request_url}?page={prev_page}&per_page={pagination_result.per_page}"
            
            # Next page
            if pagination_result.has_next:
                next_page = pagination_result.current_page + 1
                links['next'] = f"{request_url}?page={next_page}&per_page={pagination_result.per_page}"
            
            # Last page
            if pagination_result.total_pages and pagination_result.current_page < pagination_result.total_pages:
                links['last'] = f"{request_url}?page={pagination_result.total_pages}&per_page={pagination_result.per_page}"
        
        elif pagination_result.next_cursor:
            # Cursor-based pagination
            links['self'] = f"{request_url}?limit={pagination_result.per_page}"
            
            if pagination_result.next_cursor:
                links['next'] = f"{request_url}?cursor={pagination_result.next_cursor}&limit={pagination_result.per_page}"
            
            if pagination_result.previous_cursor:
                links['prev'] = f"{request_url}?cursor={pagination_result.previous_cursor}&limit={pagination_result.per_page}"
        
        return links
    
    def get_pagination_metadata(self, pagination_result: PaginationResult,
                               pagination_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get pagination metadata for API response"""
        metadata = {
            'pagination_type': pagination_params.get('type', self.default_type).value,
            'per_page': pagination_result.per_page,
            'has_next': pagination_result.has_next,
            'has_previous': pagination_result.has_previous
        }
        
        if pagination_result.total_items is not None:
            metadata.update({
                'total_items': pagination_result.total_items,
                'total_pages': pagination_result.total_pages,
                'current_page': pagination_result.current_page,
                'first_item_index': pagination_result.first_item_index,
                'last_item_index': pagination_result.last_item_index
            })
        
        if pagination_result.next_cursor:
            metadata['next_cursor'] = pagination_result.next_cursor
        
        if pagination_result.previous_cursor:
            metadata['previous_cursor'] = pagination_result.previous_cursor
        
        return metadata
    
    def estimate_query_cost(self, pagination_params: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate query cost for pagination"""
        cost = {
            'base_cost': 1,
            'pagination_cost': 0,
            'sort_cost': 0,
            'total_cost': 0
        }
        
        # Pagination cost
        per_page = pagination_params.get('per_page', self.default_per_page)
        if pagination_params.get('type') == PaginationType.OFFSET:
            # Offset pagination gets more expensive with larger offsets
            offset = pagination_params.get('offset', 0)
            cost['pagination_cost'] = 1 + (offset // 1000)  # Additional cost for large offsets
        else:
            # Cursor/seek pagination is more efficient
            cost['pagination_cost'] = 1
        
        # Sort cost
        sort_fields = pagination_params.get('sort_fields', [])
        cost['sort_cost'] = len(sort_fields) * 0.5
        
        # Total cost
        cost['total_cost'] = cost['base_cost'] + cost['pagination_cost'] + cost['sort_cost']
        
        # Recommendations
        cost['recommendations'] = []
        if cost['pagination_cost'] > 5:
            cost['recommendations'].append("Consider using cursor-based pagination for better performance")
        
        if cost['sort_cost'] > 2:
            cost['recommendations'].append("Consider reducing the number of sort fields")
        
        return cost
