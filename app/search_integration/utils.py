"""
Search Integration Utilities

Utility functions and helpers for Elasticsearch integration, search index management,
full-text search capabilities, and search analytics.
"""

import json
import re
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Union
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

from app.search_integration.service import get_search_integration_service


class QueryType(Enum):
    """Search query types"""
    FULL_TEXT = "full_text"
    EXACT = "exact"
    FUZZY = "fuzzy"
    PHRASE = "phrase"
    WILDCARD = "wildcard"
    REGEX = "regex"
    BOOLEAN = "boolean"


class SearchFieldType(Enum):
    """Search field types"""
    TEXT = "text"
    KEYWORD = "keyword"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    BOOLEAN = "boolean"
    GEO_POINT = "geo_point"
    NESTED = "nested"
    OBJECT = "object"


@dataclass
class SearchQuery:
    """Search query structure"""
    query_text: str
    query_type: QueryType
    fields: List[str]
    filters: Dict[str, Any]
    sort: List[Dict[str, Any]]
    pagination: Dict[str, Any]
    boost: float = 1.0
    highlight: bool = False
    aggregations: Dict[str, Any] = None


@dataclass
class IndexMapping:
    """Index mapping definition"""
    field_name: str
    field_type: SearchFieldType
    analyzer: Optional[str] = None
    search_analyzer: Optional[str] = None
    boost: float = 1.0
    properties: Optional[Dict[str, Any]] = None


class QueryBuilder:
    """Query builder for Elasticsearch"""
    
    def __init__(self):
        self.query_builders = {
            QueryType.FULL_TEXT: self._build_full_text_query,
            QueryType.EXACT: self._build_exact_query,
            QueryType.FUZZY: self._build_fuzzy_query,
            QueryType.PHRASE: self._build_phrase_query,
            QueryType.WILDCARD: self._build_wildcard_query,
            QueryType.REGEX: self._build_regex_query,
            QueryType.BOOLEAN: self._build_boolean_query
        }
    
    def build_query(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Build Elasticsearch query"""
        try:
            query_builder = self.query_builders.get(search_query.query_type)
            if query_builder:
                return query_builder(search_query)
            else:
                return self._build_default_query(search_query)
                
        except Exception as e:
            print(f"Error building query: {e}")
            return self._build_default_query(search_query)
    
    def _build_full_text_query(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Build full-text search query"""
        if not search_query.query_text:
            return {"match_all": {}}
        
        query = {
            "bool": {
                "must": []
            }
        }
        
        # Add main query
        if len(search_query.fields) == 1:
            query["bool"]["must"].append({
                "match": {
                    search_query.fields[0]: {
                        "query": search_query.query_text,
                        "boost": search_query.boost
                    }
                }
            })
        else:
            query["bool"]["must"].append({
                "multi_match": {
                    "query": search_query.query_text,
                    "fields": search_query.fields,
                    "type": "best_fields",
                    "boost": search_query.boost
                }
            })
        
        # Add filters
        if search_query.filters:
            query["bool"]["filter"] = self._build_filters(search_query.filters)
        
        return {"query": query}
    
    def _build_exact_query(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Build exact match query"""
        if not search_query.query_text:
            return {"match_all": {}}
        
        query = {
            "bool": {
                "must": []
            }
        }
        
        # Add term query
        if len(search_query.fields) == 1:
            query["bool"]["must"].append({
                "term": {
                    search_query.fields[0]: {
                        "value": search_query.query_text,
                        "boost": search_query.boost
                    }
                }
            })
        else:
            query["bool"]["must"].append({
                "bool": {
                    "should": [
                        {
                            "term": {
                                field: {
                                    "value": search_query.query_text,
                                    "boost": search_query.boost
                                }
                            }
                        } for field in search_query.fields
                    ]
                }
            })
        
        # Add filters
        if search_query.filters:
            query["bool"]["filter"] = self._build_filters(search_query.filters)
        
        return {"query": query}
    
    def _build_fuzzy_query(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Build fuzzy search query"""
        if not search_query.query_text:
            return {"match_all": {}}
        
        query = {
            "bool": {
                "must": []
            }
        }
        
        # Add fuzzy query
        if len(search_query.fields) == 1:
            query["bool"]["must"].append({
                "fuzzy": {
                    search_query.fields[0]: {
                        "query": search_query.query_text,
                        "fuzziness": "AUTO",
                        "boost": search_query.boost
                    }
                }
            })
        else:
            query["bool"]["must"].append({
                "multi_match": {
                    "query": search_query.query_text,
                    "fields": search_query.fields,
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "boost": search_query.boost
                }
            })
        
        # Add filters
        if search_query.filters:
            query["bool"]["filter"] = self._build_filters(search_query.filters)
        
        return {"query": query}
    
    def _build_phrase_query(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Build phrase search query"""
        if not search_query.query_text:
            return {"match_all": {}}
        
        query = {
            "bool": {
                "must": []
            }
        }
        
        # Add phrase query
        if len(search_query.fields) == 1:
            query["bool"]["must"].append({
                "match_phrase": {
                    search_query.fields[0]: {
                        "query": search_query.query_text,
                        "boost": search_query.boost
                    }
                }
            })
        else:
            query["bool"]["must"].append({
                "multi_match": {
                    "query": search_query.query_text,
                    "fields": search_query.fields,
                    "type": "phrase",
                    "boost": search_query.boost
                }
            })
        
        # Add filters
        if search_query.filters:
            query["bool"]["filter"] = self._build_filters(search_query.filters)
        
        return {"query": query}
    
    def _build_wildcard_query(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Build wildcard search query"""
        if not search_query.query_text:
            return {"match_all": {}}
        
        query = {
            "bool": {
                "must": []
            }
        }
        
        # Add wildcard query
        if len(search_query.fields) == 1:
            query["bool"]["must"].append({
                "wildcard": {
                    search_query.fields[0]: {
                        "value": search_query.query_text,
                        "boost": search_query.boost
                    }
                }
            })
        else:
            query["bool"]["must"].append({
                "bool": {
                    "should": [
                        {
                            "wildcard": {
                                field: {
                                    "value": search_query.query_text,
                                    "boost": search_query.boost
                                }
                            }
                        } for field in search_query.fields
                    ]
                }
            })
        
        # Add filters
        if search_query.filters:
            query["bool"]["filter"] = self._build_filters(search_query.filters)
        
        return {"query": query}
    
    def _build_regex_query(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Build regex search query"""
        if not search_query.query_text:
            return {"match_all": {}}
        
        query = {
            "bool": {
                "must": []
            }
        }
        
        # Add regex query
        if len(search_query.fields) == 1:
            query["bool"]["must"].append({
                "regexp": {
                    search_query.fields[0]: {
                        "value": search_query.query_text,
                        "boost": search_query.boost
                    }
                }
            })
        else:
            query["bool"]["must"].append({
                "bool": {
                    "should": [
                        {
                            "regexp": {
                                field: {
                                    "value": search_query.query_text,
                                    "boost": search_query.boost
                                }
                            }
                        } for field in search_query.fields
                    ]
                }
            })
        
        # Add filters
        if search_query.filters:
            query["bool"]["filter"] = self._build_filters(search_query.filters)
        
        return {"query": query}
    
    def _build_boolean_query(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Build boolean query"""
        if not search_query.query_text:
            return {"match_all": {}}
        
        # Parse boolean query text
        boolean_parts = self._parse_boolean_query(search_query.query_text)
        
        query = {
            "bool": {
                "must": [],
                "should": [],
                "must_not": []
            }
        }
        
        for part in boolean_parts:
            part_query = self._build_query_part(part, search_query.fields, search_query.boost)
            
            if part['operator'] == 'AND':
                query["bool"]["must"].append(part_query)
            elif part['operator'] == 'OR':
                query["bool"]["should"].append(part_query)
            elif part['operator'] == 'NOT':
                query["bool"]["must_not"].append(part_query)
        
        # Add filters
        if search_query.filters:
            query["bool"]["filter"] = self._build_filters(search_query.filters)
        
        return {"query": query}
    
    def _parse_boolean_query(self, query_text: str) -> List[Dict[str, Any]]:
        """Parse boolean query text"""
        # Simple boolean query parsing
        # This is a simplified implementation
        parts = []
        
        # Split by AND, OR, NOT
        operators = ['AND', 'OR', 'NOT']
        current_text = query_text
        current_operator = 'AND'
        
        for operator in operators:
            if operator in current_text:
                parts_list = current_text.split(operator)
                if len(parts_list) >= 2:
                    parts.append({
                        'text': parts_list[0].strip(),
                        'operator': operator
                    })
                    current_text = operator.join(parts_list[1:]).strip()
                    current_operator = operator
        
        if current_text:
            parts.append({
                'text': current_text,
                'operator': current_operator
            })
        
        return parts
    
    def _build_query_part(self, part: Dict[str, Any], fields: List[str], boost: float) -> Dict[str, Any]:
        """Build query part for boolean query"""
        text = part['text']
        
        if len(fields) == 1:
            return {
                "match": {
                    fields[0]: {
                        "query": text,
                        "boost": boost
                    }
                }
            }
        else:
            return {
                "multi_match": {
                    "query": text,
                    "fields": fields,
                    "type": "best_fields",
                    "boost": boost
                }
            }
    
    def _build_default_query(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Build default query"""
        return {
            "query": {
                "match_all": {}
            }
        }
    
    def _build_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build filters from filter dictionary"""
        filter_list = []
        
        for field, value in filters.items():
            if isinstance(value, list):
                # Range filter for lists
                if len(value) == 2:
                    filter_list.append({
                        "range": {
                            field: {
                                "gte": value[0],
                                "lte": value[1]
                            }
                        }
                    })
            elif isinstance(value, dict):
                # Complex filter
                filter_list.append(self._build_complex_filter(field, value))
            else:
                # Simple term filter
                filter_list.append({
                    "term": {
                        field: value
                    }
                })
        
        return filter_list
    
    def _build_complex_filter(self, field: str, filter_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build complex filter"""
        filter_type = filter_config.get('type', 'term')
        
        if filter_type == 'range':
            return {
                "range": {
                    field: filter_config.get('value', {})
                }
            }
        elif filter_type == 'terms':
            return {
                "terms": {
                    field: filter_config.get('value', [])
                }
            }
        elif filter_type == 'exists':
            return {
                "exists": {
                    "field": field
                }
            }
        elif filter_type == 'missing':
            return {
                "bool": {
                    "must_not": {
                        "exists": {
                            "field": field
                        }
                    }
                }
            }
        else:
            return {
                "term": {
                    field: filter_config.get('value')
                }
            }


class IndexManager:
    """Index management utility for Elasticsearch"""
    
    def __init__(self):
        self.field_type_mappings = {
            SearchFieldType.TEXT: "text",
            SearchFieldType.KEYWORD: "keyword",
            SearchFieldType.INTEGER: "integer",
            SearchFieldType.FLOAT: "float",
            SearchFieldType.DATE: "date",
            SearchFieldType.BOOLEAN: "boolean",
            SearchFieldType.GEO_POINT: "geo_point",
            SearchFieldType.NESTED: "nested",
            SearchFieldType.OBJECT: "object"
        }
    
    def create_index_mapping(self, mappings: List[IndexMapping]) -> Dict[str, Any]:
        """Create Elasticsearch index mapping"""
        properties = {}
        
        for mapping in mappings:
            field_config = {
                "type": self.field_type_mappings.get(mapping.field_type, "text")
            }
            
            # Add analyzer configuration
            if mapping.analyzer:
                field_config["analyzer"] = mapping.analyzer
            
            if mapping.search_analyzer:
                field_config["search_analyzer"] = mapping.search_analyzer
            
            # Add boost
            if mapping.boost != 1.0:
                field_config["boost"] = mapping.boost
            
            # Add nested properties
            if mapping.properties:
                field_config["properties"] = mapping.properties
            
            properties[mapping.field_name] = field_config
        
        return {"properties": properties}
    
    def create_index_settings(self, number_of_shards=1, number_of_replicas=1,
                             refresh_interval='1s', max_result_window=10000,
                             analysis_config=None) -> Dict[str, Any]:
        """Create Elasticsearch index settings"""
        settings = {
            "number_of_shards": number_of_shards,
            "number_of_replicas": number_of_replicas,
            "refresh_interval": refresh_interval,
            "max_result_window": max_result_window
        }
        
        # Add analysis configuration
        if analysis_config:
            settings["analysis"] = analysis_config
        
        return settings
    
    def validate_mapping(self, mapping: IndexMapping) -> Dict[str, Any]:
        """Validate index mapping"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check field name
        if not mapping.field_name:
            validation_result['errors'].append("Field name is required")
            validation_result['valid'] = False
        
        # Check field type
        if mapping.field_type not in SearchFieldType:
            validation_result['errors'].append(f"Invalid field type: {mapping.field_type}")
            validation_result['valid'] = False
        
        # Check analyzer configuration
        if mapping.analyzer and not self._is_valid_analyzer(mapping.analyzer):
            validation_result['warnings'].append(f"Unknown analyzer: {mapping.analyzer}")
        
        if mapping.search_analyzer and not self._is_valid_analyzer(mapping.search_analyzer):
            validation_result['warnings'].append(f"Unknown search analyzer: {mapping.search_analyzer}")
        
        # Check boost value
        if mapping.boost < 0:
            validation_result['errors'].append("Boost must be non-negative")
            validation_result['valid'] = False
        
        return validation_result
    
    def _is_valid_analyzer(self, analyzer: str) -> bool:
        """Check if analyzer is valid"""
        valid_analyzers = [
            'standard', 'simple', 'whitespace', 'stop', 'keyword',
            'pattern', 'fingerprint', 'snowball', 'english', 'custom'
        ]
        return analyzer in valid_analyzers


class SearchAnalyzer:
    """Search analyzer for query analysis and optimization"""
    
    def __init__(self):
        self.query_patterns = {
            'short_query': 10,  # Less than 10 characters
            'long_query': 100,  # More than 100 characters
            'special_chars': r'[!@#$%^&*()_+=\-\[\]{};:"\\|,.<>/?]',
            'numeric_only': r'^\d+$',
            'all_caps': r'^[A-Z]+$',
            'mixed_case': r'[a-z][A-Z]|[A-Z][a-z]'
        }
    
    def analyze_query(self, query_text: str) -> Dict[str, Any]:
        """Analyze search query"""
        analysis = {
            'query_length': len(query_text),
            'word_count': len(query_text.split()),
            'has_special_chars': bool(re.search(self.query_patterns['special_chars'], query_text)),
            'is_numeric_only': bool(re.match(self.query_patterns['numeric_only'], query_text)),
            'is_all_caps': bool(re.match(self.query_patterns['all_caps'], query_text)),
            'has_mixed_case': bool(re.search(self.query_patterns['mixed_case'], query_text)),
            'is_short': len(query_text) < self.query_patterns['short_query'],
            'is_long': len(query_text) > self.query_patterns['long_query']
        }
        
        # Determine query quality
        analysis['quality_score'] = self._calculate_query_quality(analysis)
        
        # Get suggestions
        analysis['suggestions'] = self._get_query_suggestions(analysis)
        
        return analysis
    
    def _calculate_query_quality(self, analysis: Dict[str, Any]) -> float:
        """Calculate query quality score"""
        score = 1.0
        
        # Penalize very short queries
        if analysis['is_short']:
            score -= 0.3
        
        # Penalize very long queries
        if analysis['is_long']:
            score -= 0.2
        
        # Penalize numeric-only queries
        if analysis['is_numeric_only']:
            score -= 0.4
        
        # Penalize all-caps queries
        if analysis['is_all_caps']:
            score -= 0.1
        
        # Bonus for mixed case (indicates more natural query)
        if analysis['has_mixed_case']:
            score += 0.1
        
        # Bonus for appropriate length
        if 10 <= analysis['query_length'] <= 50:
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _get_query_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Get query improvement suggestions"""
        suggestions = []
        
        if analysis['is_short']:
            suggestions.append("Consider using more specific search terms")
        
        if analysis['is_long']:
            suggestions.append("Consider using boolean operators to refine your search")
        
        if analysis['is_numeric_only']:
            suggestions.append("Add descriptive text to your search")
        
        if analysis['is_all_caps']:
            suggestions.append("Use mixed case for better results")
        
        if analysis['has_special_chars']:
            suggestions.append("Consider removing special characters or using exact match")
        
        if analysis['word_count'] > 10:
            suggestions.append("Consider using quotes for exact phrases")
        
        return suggestions


class PerformanceOptimizer:
    """Performance optimizer for search queries"""
    
    def __init__(self):
        self.optimization_rules = {
            'slow_query_threshold': 1000,  # milliseconds
            'large_result_threshold': 1000,
            'deep_pagination_threshold': 10000,
            'complex_query_threshold': 5  # number of boolean clauses
        }
    
    def optimize_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize search query for better performance"""
        optimized_query = query.copy()
        
        # Add query optimization suggestions
        optimizations = []
        
        # Check for slow query patterns
        if self._has_wildcard_prefix(query):
            optimizations.append("Avoid leading wildcards - use regex instead")
            optimized_query = self._fix_wildcard_prefix(optimized_query)
        
        # Check for large result sets
        if self._has_large_result_set(query):
            optimizations.append("Consider adding size limit or using scroll API")
            optimized_query = self._add_result_limit(optimized_query)
        
        # Check for deep pagination
        if self._has_deep_pagination(query):
            optimizations.append("Consider using search_after instead of from/size")
            optimized_query = self._fix_deep_pagination(optimized_query)
        
        # Check for complex boolean queries
        if self._has_complex_boolean(query):
            optimizations.append("Consider simplifying boolean query structure")
        
        return {
            'optimized_query': optimized_query,
            'optimizations': optimizations,
            'performance_score': self._calculate_performance_score(optimized_query)
        }
    
    def _has_wildcard_prefix(self, query: Dict[str, Any]) -> bool:
        """Check if query has leading wildcard"""
        query_part = query.get('query', {})
        
        # Check for wildcard queries
        if 'wildcard' in query_part:
            return True
        
        # Check for regex queries with leading wildcards
        if 'regexp' in query_part:
            for field, config in query_part['regexp'].items():
                value = config.get('value', '')
                if value.startswith('*'):
                    return True
        
        return False
    
    def _fix_wildcard_prefix(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Fix leading wildcard in query"""
        # This would implement wildcard prefix optimization
        # For now, return the query as-is
        return query
    
    def _has_large_result_set(self, query: Dict[str, Any]) -> bool:
        """Check if query might return large result set"""
        # Check if size is not limited
        size = query.get('size', 10)
        return size > self.optimization_rules['large_result_threshold']
    
    def _add_result_limit(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Add result size limit to query"""
        query['size'] = min(query.get('size', 10), self.optimization_rules['large_result_threshold'])
        return query
    
    def _has_deep_pagination(self, query: Dict[str, Any]) -> bool:
        """Check if query uses deep pagination"""
        from_value = query.get('from', 0)
        size = query.get('size', 10)
        return (from_value + size) > self.optimization_rules['deep_pagination_threshold']
    
    def _fix_deep_pagination(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Fix deep pagination using search_after"""
        # This would implement search_after optimization
        # For now, limit the from value
        query['from'] = min(query.get('from', 0), self.optimization_rules['deep_pagination_threshold'])
        return query
    
    def _has_complex_boolean(self, query: Dict[str, Any]) -> bool:
        """Check if query has complex boolean structure"""
        query_part = query.get('query', {})
        
        if 'bool' in query_part:
            bool_query = query_part['bool']
            clause_count = 0
            
            for clause_type in ['must', 'should', 'must_not', 'filter']:
                clause_count += len(bool_query.get(clause_type, []))
            
            return clause_count > self.optimization_rules['complex_query_threshold']
        
        return False
    
    def _calculate_performance_score(self, query: Dict[str, Any]) -> float:
        """Calculate performance score for query"""
        score = 1.0
        
        # Penalize large result sets
        size = query.get('size', 10)
        if size > 100:
            score -= 0.2
        if size > 1000:
            score -= 0.3
        
        # Penalize deep pagination
        from_value = query.get('from', 0)
        if from_value > 1000:
            score -= 0.2
        if from_value > 10000:
            score -= 0.3
        
        # Penalize complex queries
        if self._has_complex_boolean(query):
            score -= 0.2
        
        # Bonus for limited result sets
        if size <= 50:
            score += 0.1
        
        return max(0.0, min(1.0, score))


class SearchUtils:
    """General search utility functions"""
    
    @staticmethod
    def escape_elasticsearch_query(query_text: str) -> str:
        """Escape special characters in Elasticsearch query"""
        special_chars = ['+', '-', '=', '&&', '||', '>', '<', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':', '\\', '/']
        
        for char in special_chars:
            query_text = query_text.replace(char, f'\\{char}')
        
        return query_text
    
    @staticmethod
    def tokenize_query(query_text: str) -> List[str]:
        """Tokenize query text"""
        # Simple tokenization - split on whitespace and punctuation
        import re
        tokens = re.findall(r'\b\w+\b', query_text.lower())
        return tokens
    
    @staticmethod
    def calculate_relevance_score(document: Dict[str, Any], query_terms: List[str]) -> float:
        """Calculate relevance score for document"""
        score = 0.0
        
        # Get document text (simplified)
        content = str(document.get('content', '')).lower()
        title = str(document.get('title', '')).lower()
        
        # Term frequency scoring
        for term in query_terms:
            # Title matches are worth more
            if term in title:
                score += 2.0
            
            # Content matches
            content_count = content.count(term)
            if content_count > 0:
                score += 1.0 + (content_count * 0.1)
        
        # Normalize score
        if score > 0:
            score = score / len(query_terms)
        
        return score
    
    @staticmethod
    def format_search_results(results: List[Dict[str, Any]], query: SearchQuery) -> List[Dict[str, Any]]:
        """Format search results for display"""
        formatted_results = []
        
        for result in results:
            formatted_result = {
                'id': result.get('_id'),
                'score': result.get('_score', 0.0),
                'source': result.get('_source', {}),
                'highlight': result.get('highlight', {})
            }
            
            # Add excerpt if highlighting is enabled
            if query.highlight and formatted_result['highlight']:
                formatted_result['excerpt'] = SearchUtils._get_best_excerpt(formatted_result['highlight'])
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    @staticmethod
    def _get_best_excerpt(highlights: Dict[str, Any]) -> str:
        """Get best excerpt from highlights"""
        for field, highlight_list in highlights.items():
            if highlight_list:
                # Return the first highlight
                return highlight_list[0]
        
        return ""
    
    @staticmethod
    def build_suggestion_query(original_query: str, field: str = "title") -> Dict[str, Any]:
        """Build suggestion query for autocomplete"""
        return {
            "suggest": {
                "text": original_query,
                "completion": {
                    "field": f"{field}.suggest",
                    "size": 5,
                    "skip_duplicates": True
                }
            }
        }
    
    @staticmethod
    def build_aggregation_query(field: str, size: int = 10) -> Dict[str, Any]:
        """Build aggregation query"""
        return {
            "aggs": {
                f"{field}_terms": {
                    "terms": {
                        "field": field,
                        "size": size
                    }
                }
            }
        }


# Global instances
query_builder = QueryBuilder()
index_manager = IndexManager()
search_analyzer = SearchAnalyzer()
performance_optimizer = PerformanceOptimizer()
search_utils = SearchUtils()
