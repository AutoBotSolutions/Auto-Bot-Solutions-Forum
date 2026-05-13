"""
Search Integration Configuration

Configuration settings for Elasticsearch integration, search index management,
full-text search capabilities, and search analytics.
"""

import os
from datetime import timedelta

# Search Integration Configuration
SEARCH_INTEGRATION_ENABLED = True
ELASTICSEARCH_ENABLED = True
SEARCH_ANALYTICS_ENABLED = True
SEARCH_OPTIMIZATION_ENABLED = True
FULL_TEXT_SEARCH_ENABLED = True

# Elasticsearch Configuration
ELASTICSEARCH_CONFIG = {
    'enabled': True,
    'hosts': ['localhost:9200'],
    'timeout': 30,
    'max_retries': 3,
    'retry_on_timeout': True,
    'sniff_on_start': True,
    'sniff_on_connection_fail': True,
    'sniffer_timeout': 10,
    'sniff_delay': 100,
    'max_connections_per_node': 10,
    'http_compress': True,
    'verify_certs': True,
    'ca_certs': None,
    'client_key': None,
    'client_cert': None
}

# Index Configuration
INDEX_CONFIG = {
    'enabled': True,
    'default_shards': 1,
    'default_replicas': 1,
    'default_refresh_interval': '1s',
    'default_max_result_window': 10000,
    'auto_create_index': True,
    'auto_expand_replicas': True,
    'auto_expand_replicas_max': 10,
    'mapping_total_fields_limit': 1000,
    'max_depth': 20,
    'max_nesting_depth': 20,
    'max_script_length': 32768
}

# Search Configuration
SEARCH_CONFIG = {
    'enabled': True,
    'default_size': 10,
    'default_from': 0,
    'max_size': 100,
    'max_from': 10000,
    'timeout': 30,
    'request_cache': True,
    'preference': '_local',
    'routing': None,
    'pre_filter_shard_size': 128,
    'max_concurrent_shard_requests': 5,
    'seq_no_primary_term': True,
    'track_total_hits': True,
    'track_scores': True
}

# Analytics Configuration
ANALYTICS_CONFIG = {
    'enabled': True,
    'retention_days': 90,
    'aggregation_intervals': {
        'hourly': {'enabled': True, 'retention_days': 30},
        'daily': {'enabled': True, 'retention_days': 365},
        'weekly': {'enabled': True, 'retention_days': 1095},
        'monthly': {'enabled': True, 'retention_days': 1825}
    },
    'metrics_collection': {
        'enabled': True,
        'interval': 60,  # seconds
        'batch_size': 1000,
        'max_batch_size': 10000
    },
    'query_analysis': {
        'enabled': True,
        'analyze_slow_queries': True,
        'slow_query_threshold': 1000,  # milliseconds
        'analyze_zero_results': True,
        'analyze_popular_queries': True
    },
    'performance_monitoring': {
        'enabled': True,
        'monitor_query_time': True,
        'monitor_index_size': True,
        'monitor_cache_hit_rate': True,
        'monitor_error_rate': True
    }
}

# Optimization Configuration
OPTIMIZATION_CONFIG = {
    'enabled': True,
    'auto_optimization': True,
    'optimization_intervals': {
        'daily': {'enabled': True, 'hour': 2},
        'weekly': {'enabled': True, 'day': 1},
        'monthly': {'enabled': True, 'day_of_week': 1}
    },
    'optimization_types': {
        'performance': {'enabled': True, 'priority': 'high'},
        'quality': {'enabled': True, 'priority': 'medium'},
        'relevance': {'enabled': True, 'priority': 'medium'},
        'indexing': {'enabled': True, 'priority': 'low'}
    },
    'optimization_thresholds': {
        'slow_query_threshold': 1000,  # milliseconds
        'low_relevance_threshold': 0.3,
        'high_memory_threshold': 0.8,
        'error_rate_threshold': 0.05
    },
    'rollback_enabled': True,
    'rollback_timeout': 3600  # 1 hour
}

# Full-text Search Configuration
FULL_TEXT_CONFIG = {
    'enabled': True,
    'default_analyzer': 'standard',
    'default_search_analyzer': 'standard',
    'analyzers': {
        'standard': {
            'type': 'standard',
            'tokenizer': 'standard',
            'filter': ['lowercase', 'stop']
        },
        'english': {
            'type': 'english',
            'tokenizer': 'standard',
            'filter': ['lowercase', 'stop', 'stemmer']
        },
        'keyword': {
            'type': 'keyword',
            'tokenizer': 'keyword',
            'filter': []
        },
        'whitespace': {
            'type': 'whitespace',
            'tokenizer': 'whitespace',
            'filter': ['lowercase']
        },
        'simple': {
            'type': 'simple',
            'tokenizer': 'lowercase',
            'filter': []
        }
    },
    'tokenizers': {
        'standard': {
            'type': 'standard',
            'max_token_length': 255
        },
        'keyword': {
            'type': 'keyword'
        },
        'whitespace': {
            'type': 'whitespace'
        },
        'lowercase': {
            'type': 'lowercase'
        }
    },
    'filters': {
        'lowercase': {
            'type': 'lowercase'
        },
        'stop': {
            'type': 'stop',
            'stopwords': '_english_'
        },
        'stemmer': {
            'type': 'stemmer',
            'language': 'english'
        },
        'synonym': {
            'type': 'synonym',
            'synonyms': []
        }
    },
    'char_filters': {
        'html_strip': {
            'type': 'html_strip'
        },
        'mapping': {
            'type': 'mapping',
            'mappings': []
        },
        'pattern_replace': {
            'type': 'pattern_replace',
            'patterns': []
        }
    }
}

# Index Templates
INDEX_TEMPLATES = {
    'content_index': {
        'settings': {
            'number_of_shards': 1,
            'number_of_replicas': 1,
            'refresh_interval': '1s'
        },
        'mappings': {
            'properties': {
                'title': {
                    'type': 'text',
                    'analyzer': 'standard',
                    'search_analyzer': 'standard',
                    'fields': {
                        'keyword': {
                            'type': 'keyword'
                        }
                    }
                },
                'content': {
                    'type': 'text',
                    'analyzer': 'english',
                    'search_analyzer': 'standard',
                    'fields': {
                        'keyword': {
                            'type': 'keyword'
                        }
                    }
                },
                'author': {
                    'type': 'text',
                    'analyzer': 'standard',
                    'fields': {
                        'keyword': {
                            'type': 'keyword'
                        }
                    }
                },
                'created_at': {
                    'type': 'date',
                    'format': 'strict_date_optional_time||epoch_millis'
                },
                'tags': {
                    'type': 'keyword'
                },
                'category': {
                    'type': 'keyword'
                }
            }
        }
    },
    'user_index': {
        'settings': {
            'number_of_shards': 1,
            'number_of_replicas': 1,
            'refresh_interval': '1s'
        },
        'mappings': {
            'properties': {
                'username': {
                    'type': 'text',
                    'analyzer': 'standard',
                    'fields': {
                        'keyword': {
                            'type': 'keyword'
                        }
                    }
                },
                'email': {
                    'type': 'keyword'
                },
                'profile': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'created_at': {
                    'type': 'date',
                    'format': 'strict_date_optional_time||epoch_millis'
                },
                'last_login': {
                    'type': 'date',
                    'format': 'strict_date_optional_time||epoch_millis'
                },
                'roles': {
                    'type': 'keyword'
                },
                'status': {
                    'type': 'keyword'
                }
            }
        }
    },
    'forum_index': {
        'settings': {
            'number_of_shards': 2,
            'number_of_replicas': 1,
            'refresh_interval': '1s'
        },
        'mappings': {
            'properties': {
                'title': {
                    'type': 'text',
                    'analyzer': 'standard',
                    'search_analyzer': 'standard',
                    'fields': {
                        'keyword': {
                            'type': 'keyword'
                        }
                    }
                },
                'content': {
                    'type': 'text',
                    'analyzer': 'english',
                    'search_analyzer': 'standard',
                    'fields': {
                        'keyword': {
                            'type': 'keyword'
                        }
                    }
                },
                'author': {
                    'type': 'text',
                    'analyzer': 'standard',
                    'fields': {
                        'keyword': {
                            'type': 'keyword'
                        }
                    }
                },
                'forum': {
                    'type': 'keyword'
                },
                'category': {
                    'type': 'keyword'
                },
                'tags': {
                    'type': 'keyword'
                },
                'created_at': {
                    'type': 'date',
                    'format': 'strict_date_optional_time||epoch_millis'
                },
                'updated_at': {
                    'type': 'date',
                    'format': 'strict_date_optional_time||epoch_millis'
                },
                'replies_count': {
                    'type': 'integer'
                },
                'views_count': {
                    'type': 'integer'
                }
            }
        }
    }
}

# Query Configuration
QUERY_CONFIG = {
    'enabled': True,
    'default_query_type': 'full_text',
    'default_fields': ['title', 'content'],
    'default_size': 10,
    'default_sort': [{'_score': {'order': 'desc'}}],
    'highlight_enabled': True,
    'highlight_config': {
        'pre_tags': ['<em>'],
        'post_tags': ['</em>'],
        'fragment_size': 150,
        'number_of_fragments': 3
    },
    'suggest_enabled': True,
    'suggest_config': {
        'completion': {
            'size': 5,
            'skip_duplicates': True
        }
    },
    'aggregation_enabled': True,
    'aggregation_config': {
        'terms_size': 10,
        'date_histogram_interval': 'day',
        'histogram_interval': 10
    }
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'query_caching': {
        'enabled': True,
        'cache_size': 1000,
        'cache_ttl': 300  # 5 minutes
    },
    'result_caching': {
        'enabled': True,
        'cache_size': 500,
        'cache_ttl': 60  # 1 minute
    },
    'connection_pooling': {
        'enabled': True,
        'max_connections': 20,
        'timeout': 30
    },
    'bulk_indexing': {
        'enabled': True,
        'batch_size': 1000,
        'flush_interval': 5000  # 5 seconds
    },
    'scrolling': {
        'enabled': True,
        'scroll_size': 1000,
        'scroll_timeout': '5m'
    }
}

# Security Configuration
SECURITY_CONFIG = {
    'authentication': {
        'enabled': True,
        'username': None,
        'password': None
    },
    'authorization': {
        'enabled': True,
        'rbac_enabled': True,
        'default_role': 'viewer',
        'roles': {
            'admin': ['read', 'write', 'delete', 'manage'],
            'analyst': ['read', 'write'],
            'viewer': ['read']
        }
    },
    'encryption': {
        'enabled': False,
        'algorithm': 'aes256',
        'key_rotation_days': 90,
        'encrypt_at_rest': True,
        'encrypt_in_transit': True
    },
    'audit_logging': {
        'enabled': True,
        'log_all_queries': False,
        'log_sensitive_queries': True,
        'retention_days': 365
    }
}

# Development Configuration
if os.getenv('FLASK_ENV') == 'development':
    SEARCH_INTEGRATION_ENABLED = True
    ELASTICSEARCH_ENABLED = False  # Disabled in development
    SEARCH_ANALYTICS_ENABLED = False
    SEARCH_OPTIMIZATION_ENABLED = False
    FULL_TEXT_SEARCH_ENABLED = False
    
    ELASTICSEARCH_CONFIG['hosts'] = ['localhost:9200']
    INDEX_CONFIG['default_shards'] = 1
    INDEX_CONFIG['default_replicas'] = 0
    
    ANALYTICS_CONFIG['retention_days'] = 7
    OPTIMIZATION_CONFIG['auto_optimization'] = False
    
    PERFORMANCE_CONFIG['query_caching']['enabled'] = False
    PERFORMANCE_CONFIG['result_caching']['enabled'] = False

# Production Configuration
if os.getenv('FLASK_ENV') == 'production':
    SEARCH_INTEGRATION_ENABLED = True
    ELASTICSEARCH_ENABLED = True
    SEARCH_ANALYTICS_ENABLED = True
    SEARCH_OPTIMIZATION_ENABLED = True
    FULL_TEXT_SEARCH_ENABLED = True
    
    ELASTICSEARCH_CONFIG['hosts'] = [
        f"{os.getenv('ELASTICSEARCH_HOST_1', 'localhost')}:{os.getenv('ELASTICSEARCH_PORT_1', '9200')}",
        f"{os.getenv('ELASTICSEARCH_HOST_2', 'localhost')}:{os.getenv('ELASTICSEARCH_PORT_2', '9201')}",
        f"{os.getenv('ELASTICSEARCH_HOST_3', 'localhost')}:{os.getenv('ELASTICSEARCH_PORT_3', '9202')}"
    ]
    ELASTICSEARCH_CONFIG['username'] = os.getenv('ELASTICSEARCH_USERNAME')
    ELASTICSEARCH_CONFIG['password'] = os.getenv('ELASTICSEARCH_PASSWORD')
    
    INDEX_CONFIG['default_shards'] = 3
    INDEX_CONFIG['default_replicas'] = 1
    
    ANALYTICS_CONFIG['retention_days'] = 365
    OPTIMIZATION_CONFIG['auto_optimization'] = True
    
    PERFORMANCE_CONFIG['query_caching']['enabled'] = True
    PERFORMANCE_CONFIG['result_caching']['enabled'] = True

# Testing Configuration
if os.getenv('FLASK_ENV') == 'testing':
    SEARCH_INTEGRATION_ENABLED = False
    ELASTICSEARCH_ENABLED = False
    SEARCH_ANALYTICS_ENABLED = False
    SEARCH_OPTIMIZATION_ENABLED = False
    FULL_TEXT_SEARCH_ENABLED = False
    
    ANALYTICS_CONFIG['enabled'] = False
    OPTIMIZATION_CONFIG['enabled'] = False
    PERFORMANCE_CONFIG['query_caching']['enabled'] = False
    PERFORMANCE_CONFIG['result_caching']['enabled'] = False

# Environment Variables
ENVIRONMENT_VARIABLES = {
    'SEARCH_INTEGRATION_ENABLED': os.getenv('SEARCH_INTEGRATION_ENABLED', 'True'),
    'ELASTICSEARCH_ENABLED': os.getenv('ELASTICSEARCH_ENABLED', 'True'),
    'SEARCH_ANALYTICS_ENABLED': os.getenv('SEARCH_ANALYTICS_ENABLED', 'True'),
    'SEARCH_OPTIMIZATION_ENABLED': os.getenv('SEARCH_OPTIMIZATION_ENABLED', 'True'),
    'FULL_TEXT_SEARCH_ENABLED': os.getenv('FULL_TEXT_SEARCH_ENABLED', 'True'),
    'ELASTICSEARCH_HOST_1': os.getenv('ELASTICSEARCH_HOST_1', 'localhost'),
    'ELASTICSEARCH_PORT_1': os.getenv('ELASTICSEARCH_PORT_1', '9200'),
    'ELASTICSEARCH_HOST_2': os.getenv('ELASTICSEARCH_HOST_2', 'localhost'),
    'ELASTICSEARCH_PORT_2': os.getenv('ELASTICSEARCH_PORT_2', '9201'),
    'ELASTICSEARCH_HOST_3': os.getenv('ELASTICSEARCH_HOST_3', 'localhost'),
    'ELASTICSEARCH_PORT_3': os.getenv('ELASTICSEARCH_PORT_3', '9202'),
    'ELASTICSEARCH_USERNAME': os.getenv('ELASTICSEARCH_USERNAME'),
    'ELASTICSEARCH_PASSWORD': os.getenv('ELASTICSEARCH_PASSWORD'),
    'ELASTICSEARCH_HTTPS': os.getenv('ELASTICSEARCH_HTTPS', 'False'),
    'ELASTICSEARCH_CA_CERTS': os.getenv('ELASTICSEARCH_CA_CERTS'),
    'ELASTICSEARCH_CLIENT_KEY': os.getenv('ELASTICSEARCH_CLIENT_KEY'),
    'ELASTICSEARCH_CLIENT_CERT': os.getenv('ELASTICSEARCH_CLIENT_CERT'),
    'ELASTICSEARCH_API_KEY': os.getenv('ELASTICSEARCH_API_KEY')
}

# Search Field Types
SEARCH_FIELD_TYPES = {
    'text': {
        'type': 'text',
        'analyzer': 'standard',
        'search_analyzer': 'standard'
    },
    'keyword': {
        'type': 'keyword'
    },
    'integer': {
        'type': 'integer'
    },
    'float': {
        'type': 'float'
    },
    'date': {
        'type': 'date',
        'format': 'strict_date_optional_time||epoch_millis'
    },
    'boolean': {
        'type': 'boolean'
    },
    'geo_point': {
        'type': 'geo_point'
    },
    'nested': {
        'type': 'nested'
    },
    'object': {
        'type': 'object'
    }
}

# Search Query Types
SEARCH_QUERY_TYPES = {
    'full_text': {
        'description': 'Full-text search with relevance scoring',
        'analyzer': 'standard'
    },
    'exact': {
        'description': 'Exact match search',
        'type': 'term'
    },
    'fuzzy': {
        'description': 'Fuzzy search with typo tolerance',
        'fuzziness': 'AUTO'
    },
    'phrase': {
        'description': 'Phrase search for exact phrases',
        'type': 'match_phrase'
    },
    'wildcard': {
        'description': 'Wildcard search with pattern matching',
        'type': 'wildcard'
    },
    'regex': {
        'description': 'Regular expression search',
        'type': 'regexp'
    },
    'boolean': {
        'description': 'Boolean search with AND/OR/NOT operators',
        'type': 'bool'
    }
}

# Search Filters
SEARCH_FILTERS = {
    'range': {
        'description': 'Range filter for numeric and date fields',
        'operators': ['gte', 'gt', 'lte', 'lt']
    },
    'terms': {
        'description': 'Terms filter for multiple values',
        'type': 'terms'
    },
    'exists': {
        'description': 'Exists filter for field presence',
        'type': 'exists'
    },
    'missing': {
        'description': 'Missing filter for field absence',
        'type': 'bool must_not exists'
    },
    'geo_distance': {
        'description': 'Geo distance filter for location-based search',
        'type': 'geo_distance'
    },
    'geo_bounding_box': {
        'description': 'Geo bounding box filter for location-based search',
        'type': 'geo_bounding_box'
    }
}

# Validation Functions
def validate_search_integration_config():
    """Validate search integration configuration"""
    errors = []
    
    # Check required environment variables
    if ELASTICSEARCH_ENABLED:
        if not ELASTICSEARCH_CONFIG['hosts']:
            errors.append("Elasticsearch hosts not configured")
        
        if ELASTICSEARCH_CONFIG.get('username') and not ELASTICSEARCH_CONFIG.get('password'):
            errors.append("Elasticsearch username provided but password missing")
    
    # Check configuration consistency
    if INDEX_CONFIG['default_shards'] < 1:
        errors.append("Default shards must be at least 1")
    
    if INDEX_CONFIG['default_replicas'] < 0:
        errors.append("Default replicas must be non-negative")
    
    if SEARCH_CONFIG['max_size'] < 1:
        errors.append("Max search size must be at least 1")
    
    if SEARCH_CONFIG['max_from'] < 0:
        errors.append("Max search from must be non-negative")
    
    return errors

def get_search_integration_config():
    """Get complete search integration configuration"""
    return {
        'search_integration_enabled': SEARCH_INTEGRATION_ENABLED,
        'elasticsearch_enabled': ELASTICSEARCH_ENABLED,
        'search_analytics_enabled': SEARCH_ANALYTICS_ENABLED,
        'search_optimization_enabled': SEARCH_OPTIMIZATION_ENABLED,
        'full_text_search_enabled': FULL_TEXT_SEARCH_ENABLED,
        'elasticsearch_config': ELASTICSEARCH_CONFIG,
        'index_config': INDEX_CONFIG,
        'search_config': SEARCH_CONFIG,
        'analytics_config': ANALYTICS_CONFIG,
        'optimization_config': OPTIMIZATION_CONFIG,
        'full_text_config': FULL_TEXT_CONFIG,
        'index_templates': INDEX_TEMPLATES,
        'query_config': QUERY_CONFIG,
        'performance_config': PERFORMANCE_CONFIG,
        'security_config': SECURITY_CONFIG,
        'search_field_types': SEARCH_FIELD_TYPES,
        'search_query_types': SEARCH_QUERY_TYPES,
        'search_filters': SEARCH_FILTERS
    }


# Default configurations for different deployment types
DEFAULT_CONFIGS = {
    'small': {
        'index_config': {'default_shards': 1, 'default_replicas': 0},
        'search_config': {'max_size': 50, 'max_from': 1000},
        'performance_config': {'query_caching': {'enabled': False}}
    },
    'medium': {
        'index_config': {'default_shards': 2, 'default_replicas': 1},
        'search_config': {'max_size': 100, 'max_from': 5000},
        'performance_config': {'query_caching': {'enabled': True}}
    },
    'large': {
        'index_config': {'default_shards': 3, 'default_replicas': 2},
        'search_config': {'max_size': 200, 'max_from': 10000},
        'performance_config': {'query_caching': {'enabled': True}}
    }
}
