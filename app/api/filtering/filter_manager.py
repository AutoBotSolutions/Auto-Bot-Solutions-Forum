"""
Filter Manager

Manages advanced filtering capabilities for API endpoints.
"""

import re
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class FilterOperator(Enum):
    """Filter operators"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "nin"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"
    DATE_GREATER_THAN = "date_gt"
    DATE_LESS_THAN = "date_lt"
    DATE_BETWEEN = "date_between"

class FilterType(Enum):
    """Filter data types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    LIST = "list"
    JSON = "json"

@dataclass
class FilterField:
    """Represents a filterable field"""
    name: str
    field_type: FilterType
    operators: List[FilterOperator]
    description: str = ""
    required: bool = False
    default_value: Any = None
    choices: Optional[List[Any]] = None
    nested: bool = False
    nested_path: Optional[str] = None

class FilterCondition:
    """Represents a single filter condition"""
    
    def __init__(self, field: str, operator: FilterOperator, value: Any):
        self.field = field
        self.operator = operator
        self.value = value
        self.negated = False
    
    def negate(self):
        """Negate the condition"""
        self.negated = True
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'field': self.field,
            'operator': self.operator.value,
            'value': self.value,
            'negated': self.negated
        }

class FilterGroup:
    """Represents a group of filter conditions with logical operators"""
    
    def __init__(self, conditions: List[Union[FilterCondition, 'FilterGroup']] = None, 
                 operator: str = 'AND'):
        self.conditions = conditions or []
        self.operator = operator.upper()  # AND or OR
    
    def add_condition(self, condition: Union[FilterCondition, 'FilterGroup']):
        """Add condition to group"""
        self.conditions.append(condition)
        return self
    
    def add_and(self, condition: Union[FilterCondition, 'FilterGroup']):
        """Add condition with AND operator"""
        if self.operator != 'AND':
            # Wrap existing conditions in a new group
            new_group = FilterGroup(self.conditions, self.operator)
            self.conditions = [new_group]
            self.operator = 'AND'
        self.conditions.append(condition)
        return self
    
    def add_or(self, condition: Union[FilterCondition, 'FilterGroup']):
        """Add condition with OR operator"""
        if self.operator != 'OR':
            # Wrap existing conditions in a new group
            new_group = FilterGroup(self.conditions, self.operator)
            self.conditions = [new_group]
            self.operator = 'OR'
        self.conditions.append(condition)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'operator': self.operator,
            'conditions': [cond.to_dict() if hasattr(cond, 'to_dict') else cond for cond in self.conditions]
        }

class FilterManager:
    """Manages filtering operations"""
    
    def __init__(self):
        self.fields: Dict[str, FilterField] = {}
        self.custom_operators: Dict[str, Callable] = {}
        self._register_default_fields()
        self._register_default_operators()
    
    def _register_default_fields(self):
        """Register default filter fields"""
        # Common string fields
        self.register_field('title', FilterType.STRING, [
            FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
            FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
            FilterOperator.STARTS_WITH, FilterOperator.ENDS_WITH,
            FilterOperator.IN, FilterOperator.NOT_IN,
            FilterOperator.REGEX, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "Title field")
        
        self.register_field('content', FilterType.STRING, [
            FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
            FilterOperator.REGEX, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "Content field")
        
        self.register_field('username', FilterType.STRING, [
            FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
            FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
            FilterOperator.IN, FilterOperator.NOT_IN,
            FilterOperator.REGEX, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "Username field")
        
        self.register_field('email', FilterType.STRING, [
            FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
            FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
            FilterOperator.IN, FilterOperator.NOT_IN,
            FilterOperator.REGEX, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "Email field")
        
        # Numeric fields
        self.register_field('id', FilterType.INTEGER, [
            FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
            FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUAL,
            FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUAL,
            FilterOperator.IN, FilterOperator.NOT_IN,
            FilterOperator.BETWEEN, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "ID field")
        
        self.register_field('view_count', FilterType.INTEGER, [
            FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
            FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUAL,
            FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUAL,
            FilterOperator.BETWEEN, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "View count field")
        
        self.register_field('like_count', FilterType.INTEGER, [
            FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
            FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUAL,
            FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUAL,
            FilterOperator.BETWEEN, FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "Like count field")
        
        # Date fields
        self.register_field('created_at', FilterType.DATETIME, [
            FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
            FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUAL,
            FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUAL,
            FilterOperator.BETWEEN, FilterOperator.DATE_GREATER_THAN,
            FilterOperator.DATE_LESS_THAN, FilterOperator.DATE_BETWEEN,
            FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "Creation date field")
        
        self.register_field('updated_at', FilterType.DATETIME, [
            FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
            FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUAL,
            FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUAL,
            FilterOperator.BETWEEN, FilterOperator.DATE_GREATER_THAN,
            FilterOperator.DATE_LESS_THAN, FilterOperator.DATE_BETWEEN,
            FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "Update date field")
        
        # Boolean fields
        self.register_field('is_active', FilterType.BOOLEAN, [
            FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
            FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "Active status field")
        
        # List fields
        self.register_field('tags', FilterType.LIST, [
            FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
            FilterOperator.IN, FilterOperator.NOT_IN,
            FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "Tags field")
        
        self.register_field('roles', FilterType.LIST, [
            FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
            FilterOperator.IN, FilterOperator.NOT_IN,
            FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL
        ], "Roles field")
    
    def _register_default_operators(self):
        """Register custom operators"""
        self.custom_operators['recent'] = self._operator_recent
        self.custom_operators['popular'] = self._operator_popular
        self.custom_operators['trending'] = self._operator_trending
    
    def register_field(self, name: str, field_type: FilterType, 
                       operators: List[FilterOperator], description: str = "",
                       required: bool = False, default_value: Any = None,
                       choices: Optional[List[Any]] = None, nested: bool = False,
                       nested_path: Optional[str] = None):
        """Register a filterable field"""
        self.fields[name] = FilterField(
            name=name,
            field_type=field_type,
            operators=operators,
            description=description,
            required=required,
            default_value=default_value,
            choices=choices,
            nested=nested,
            nested_path=nested_path
        )
    
    def register_custom_operator(self, name: str, operator_func: Callable):
        """Register a custom operator"""
        self.custom_operators[name] = operator_func
    
    def get_field(self, name: str) -> Optional[FilterField]:
        """Get field by name"""
        return self.fields.get(name)
    
    def get_fields(self) -> Dict[str, FilterField]:
        """Get all registered fields"""
        return self.fields.copy()
    
    def validate_filter(self, field_name: str, operator: FilterOperator, 
                       value: Any) -> bool:
        """Validate filter condition"""
        field = self.get_field(field_name)
        if not field:
            return False
        
        # Check if operator is supported for this field
        if operator not in field.operators:
            return False
        
        # Validate value type
        if not self._validate_value_type(field.field_type, value):
            return False
        
        # Validate choices if specified
        if field.choices and not self._validate_choices(field.choices, value, operator):
            return False
        
        return True
    
    def _validate_value_type(self, field_type: FilterType, value: Any) -> bool:
        """Validate value type for field"""
        try:
            if field_type == FilterType.STRING:
                return isinstance(value, str)
            elif field_type == FilterType.INTEGER:
                return isinstance(value, int) or (isinstance(value, str) and value.isdigit())
            elif field_type == FilterType.FLOAT:
                return isinstance(value, (int, float)) or (isinstance(value, str) and self._is_float(value))
            elif field_type == FilterType.BOOLEAN:
                return isinstance(value, bool) or (isinstance(value, str) and value.lower() in ['true', 'false'])
            elif field_type == FilterType.DATE:
                return isinstance(value, str) and self._is_date(value)
            elif field_type == FilterType.DATETIME:
                return isinstance(value, str) and self._is_datetime(value)
            elif field_type == FilterType.LIST:
                return isinstance(value, (list, str))
            elif field_type == FilterType.JSON:
                return isinstance(value, (dict, str))
            return True
        except Exception:
            return False
    
    def _validate_choices(self, choices: List[Any], value: Any, 
                         operator: FilterOperator) -> bool:
        """Validate value against choices"""
        if operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
            if isinstance(value, list):
                return all(v in choices for v in value)
            return value in choices
        else:
            return value in choices
    
    def _is_float(self, value: str) -> bool:
        """Check if string is a valid float"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _is_date(self, value: str) -> bool:
        """Check if string is a valid date"""
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def _is_datetime(self, value: str) -> bool:
        """Check if string is a valid datetime"""
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False
    
    def parse_filter_query(self, query: str) -> FilterGroup:
        """Parse filter query string into filter group"""
        try:
            # Simple query parsing (can be extended for complex queries)
            conditions = []
            
            # Parse individual conditions
            if '&' in query:
                # AND conditions
                parts = query.split('&')
                for part in parts:
                    condition = self._parse_condition(part.strip())
                    if condition:
                        conditions.append(condition)
                return FilterGroup(conditions, 'AND')
            elif '|' in query:
                # OR conditions
                parts = query.split('|')
                for part in parts:
                    condition = self._parse_condition(part.strip())
                    if condition:
                        conditions.append(condition)
                return FilterGroup(conditions, 'OR')
            else:
                # Single condition
                condition = self._parse_condition(query.strip())
                return FilterGroup([condition], 'AND') if condition else FilterGroup()
        
        except Exception as e:
            logger.error(f"Error parsing filter query: {e}")
            return FilterGroup()
    
    def _parse_condition(self, condition_str: str) -> Optional[FilterCondition]:
        """Parse individual condition string"""
        try:
            # Pattern: field:operator:value
            match = re.match(r'^(\w+):(\w+):(.+)$', condition_str)
            if not match:
                return None
            
            field_name, operator_str, value_str = match.groups()
            
            # Parse operator
            try:
                operator = FilterOperator(operator_str)
            except ValueError:
                return None
            
            # Parse value
            value = self._parse_value(value_str)
            
            return FilterCondition(field_name, operator, value)
        
        except Exception as e:
            logger.error(f"Error parsing condition: {e}")
            return None
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse value string to appropriate type"""
        # Handle lists
        if value_str.startswith('[') and value_str.endswith(']'):
            try:
                return eval(value_str)  # Simple eval for lists (be careful in production)
            except:
                return value_str
        
        # Handle booleans
        if value_str.lower() in ['true', 'false']:
            return value_str.lower() == 'true'
        
        # Handle numbers
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # Handle dates
        if self._is_date(value_str) or self._is_datetime(value_str):
            return value_str
        
        # Default to string
        return value_str
    
    def build_sqlalchemy_filter(self, query, model, filter_group: FilterGroup):
        """Build SQLAlchemy filter from filter group"""
        from sqlalchemy import and_, or_, not_
        
        if not filter_group.conditions:
            return query
        
        conditions = []
        
        for condition in filter_group.conditions:
            if isinstance(condition, FilterCondition):
                sql_condition = self._build_sqlalchemy_condition(model, condition)
                if sql_condition:
                    conditions.append(sql_condition)
            elif isinstance(condition, FilterGroup):
                sub_query = self.build_sqlalchemy_filter(query, model, condition)
                # This would need to be handled differently in actual implementation
                pass
        
        if conditions:
            if filter_group.operator == 'AND':
                query = query.filter(and_(*conditions))
            elif filter_group.operator == 'OR':
                query = query.filter(or_(*conditions))
        
        return query
    
    def _build_sqlalchemy_condition(self, model, condition: FilterCondition):
        """Build SQLAlchemy condition from filter condition"""
        from sqlalchemy import and_, or_, not_
        from sqlalchemy.sql import expression
        
        field = self.get_field(condition.field)
        if not field:
            return None
        
        # Get model attribute
        if field.nested and field.nested_path:
            # Handle nested fields (e.g., user.username)
            attr = getattr(model, field.nested_path)
            attr = getattr(attr, condition.field)
        else:
            attr = getattr(model, condition.field)
        
        # Build condition based on operator
        if condition.operator == FilterOperator.EQUALS:
            return attr == condition.value
        elif condition.operator == FilterOperator.NOT_EQUALS:
            return attr != condition.value
        elif condition.operator == FilterOperator.GREATER_THAN:
            return attr > condition.value
        elif condition.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return attr >= condition.value
        elif condition.operator == FilterOperator.LESS_THAN:
            return attr < condition.value
        elif condition.operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return attr <= condition.value
        elif condition.operator == FilterOperator.IN:
            return attr.in_(condition.value if isinstance(condition.value, list) else [condition.value])
        elif condition.operator == FilterOperator.NOT_IN:
            return attr.notin_(condition.value if isinstance(condition.value, list) else [condition.value])
        elif condition.operator == FilterOperator.CONTAINS:
            return attr.contains(condition.value)
        elif condition.operator == FilterOperator.NOT_CONTAINS:
            return ~attr.contains(condition.value)
        elif condition.operator == FilterOperator.STARTS_WITH:
            return attr.startswith(condition.value)
        elif condition.operator == FilterOperator.ENDS_WITH:
            return attr.endswith(condition.value)
        elif condition.operator == FilterOperator.REGEX:
            return attr.op('~')(condition.value)
        elif condition.operator == FilterOperator.IS_NULL:
            return attr.is_(None)
        elif condition.operator == FilterOperator.IS_NOT_NULL:
            return attr.isnot_(None)
        elif condition.operator == FilterOperator.BETWEEN:
            if isinstance(condition.value, list) and len(condition.value) == 2:
                return attr.between(condition.value[0], condition.value[1])
        elif condition.operator == FilterOperator.DATE_GREATER_THAN:
            if isinstance(condition.value, str):
                date_value = datetime.fromisoformat(condition.value.replace('Z', '+00:00'))
                return attr > date_value
        elif condition.operator == FilterOperator.DATE_LESS_THAN:
            if isinstance(condition.value, str):
                date_value = datetime.fromisoformat(condition.value.replace('Z', '+00:00'))
                return attr < date_value
        elif condition.operator == FilterOperator.DATE_BETWEEN:
            if isinstance(condition.value, list) and len(condition.value) == 2:
                start_date = datetime.fromisoformat(condition.value[0].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(condition.value[1].replace('Z', '+00:00'))
                return attr.between(start_date, end_date)
        
        return None
    
    def _operator_recent(self, query, field: str, value: Any):
        """Custom operator for recent items"""
        if isinstance(value, str):
            # Parse time period (e.g., "7d", "24h", "1w")
            if value.endswith('d'):
                days = int(value[:-1])
                cutoff = datetime.utcnow() - timedelta(days=days)
                return query.filter(getattr(query.column_descriptions[0]['type'], field) >= cutoff)
            elif value.endswith('h'):
                hours = int(value[:-1])
                cutoff = datetime.utcnow() - timedelta(hours=hours)
                return query.filter(getattr(query.column_descriptions[0]['type'], field) >= cutoff)
            elif value.endswith('w'):
                weeks = int(value[:-1])
                cutoff = datetime.utcnow() - timedelta(weeks=weeks)
                return query.filter(getattr(query.column_descriptions[0]['type'], field) >= cutoff)
        return query
    
    def _operator_popular(self, query, field: str, value: Any):
        """Custom operator for popular items"""
        # Sort by field in descending order
        return query.order_by(getattr(query.column_descriptions[0]['type'], field).desc())
    
    def _operator_trending(self, query, field: str, value: Any):
        """Custom operator for trending items"""
        # Complex logic for trending items would go here
        # For now, just sort by recent and popular
        cutoff = datetime.utcnow() - timedelta(days=7)
        return query.filter(
            getattr(query.column_descriptions[0]['type'], field) >= cutoff
        ).order_by(getattr(query.column_descriptions[0]['type'], field).desc())
    
    def get_filter_schema(self) -> Dict[str, Any]:
        """Get filter schema for API documentation"""
        schema = {
            'type': 'object',
            'properties': {},
            'examples': {}
        }
        
        for field_name, field in self.fields.items():
            field_schema = {
                'type': self._get_json_type(field.field_type),
                'description': field.description
            }
            
            if field.choices:
                field_schema['enum'] = field.choices
            
            if field.default_value is not None:
                field_schema['default'] = field.default_value
            
            schema['properties'][field_name] = field_schema
        
        # Add examples
        schema['examples'] = {
            'simple_filter': {
                'title': 'Python Programming',
                'created_at': '2024-01-01'
            },
            'complex_filter': {
                'title': {'contains': 'Python'},
                'view_count': {'gt': 100},
                'created_at': {'between': ['2024-01-01', '2024-12-31']},
                'tags': {'in': ['programming', 'python']}
            }
        }
        
        return schema
    
    def _get_json_type(self, field_type: FilterType) -> str:
        """Convert filter type to JSON schema type"""
        type_mapping = {
            FilterType.STRING: 'string',
            FilterType.INTEGER: 'integer',
            FilterType.FLOAT: 'number',
            FilterType.BOOLEAN: 'boolean',
            FilterType.DATE: 'string',
            FilterType.DATETIME: 'string',
            FilterType.LIST: 'array',
            FilterType.JSON: 'object'
        }
        return type_mapping.get(field_type, 'string')
