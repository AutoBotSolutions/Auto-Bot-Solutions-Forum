"""
Data Warehouse Utilities

Utility functions and helpers for data warehouse management, aggregation pipelines,
historical data storage, and data archiving.
"""

import json
import time
import threading
import hashlib
import gzip
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Union
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

from app.warehouse.service import get_data_warehouse_service


class AggregationType(Enum):
    """Aggregation types for data warehouse"""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    STDDEV = "stddev"
    VARIANCE = "variance"
    PERCENTILE = "percentile"


class ArchiveType(Enum):
    """Archive types for data warehouse"""
    FULL = "full"
    INCREMENTAL = "incremental"
    SNAPSHOT = "snapshot"
    DELTA = "delta"


class StorageTier(Enum):
    """Storage tiers for data warehouse"""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    ARCHIVE = "archive"


@dataclass
class AggregationRule:
    """Aggregation rule definition"""
    field_name: str
    aggregation_type: AggregationType
    alias: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None


@dataclass
class ArchiveRule:
    """Archive rule definition"""
    table_name: str
    archive_type: ArchiveType
    retention_days: int
    compression: bool = True
    encryption: bool = False
    storage_tier: StorageTier = StorageTier.COLD


class AggregationEngine:
    """Aggregation engine for data warehouse"""
    
    def __init__(self):
        self.aggregation_functions = {
            AggregationType.SUM: self._sum_aggregation,
            AggregationType.AVG: self._avg_aggregation,
            AggregationType.COUNT: self._count_aggregation,
            AggregationType.MIN: self._min_aggregation,
            AggregationType.MAX: self._max_aggregation,
            AggregationType.STDDEV: self._stddev_aggregation,
            AggregationType.VARIANCE: self._variance_aggregation,
            AggregationType.PERCENTILE: self._percentile_aggregation
        }
    
    def execute_aggregation(self, data: List[Dict[str, Any]], rules: List[AggregationRule],
                           group_by_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Execute aggregation on data"""
        try:
            if group_by_fields:
                return self._grouped_aggregation(data, rules, group_by_fields)
            else:
                return self._simple_aggregation(data, rules)
                
        except Exception as e:
            print(f"Error executing aggregation: {e}")
            return []
    
    def _simple_aggregation(self, data: List[Dict[str, Any]], rules: List[AggregationRule]) -> List[Dict[str, Any]]:
        """Execute simple aggregation (no grouping)"""
        if not data:
            return []
        
        result = {}
        
        for rule in rules:
            field_name = rule.field_name
            agg_type = rule.aggregation_type
            alias = rule.alias or f"{agg_type.value}_{field_name}"
            
            # Extract field values
            values = []
            for record in data:
                if field_name in record and record[field_name] is not None:
                    values.append(record[field_name])
            
            # Apply aggregation function
            if values:
                agg_function = self.aggregation_functions.get(agg_type)
                if agg_function:
                    result[alias] = agg_function(values, rule)
                else:
                    result[alias] = None
            else:
                result[alias] = None
        
        return [result]
    
    def _grouped_aggregation(self, data: List[Dict[str, Any]], rules: List[AggregationRule],
                            group_by_fields: List[str]) -> List[Dict[str, Any]]:
        """Execute grouped aggregation"""
        if not data:
            return []
        
        # Group data by group_by_fields
        groups = defaultdict(list)
        
        for record in data:
            # Create group key
            group_key = tuple(record.get(field) for field in group_by_fields)
            groups[group_key].append(record)
        
        # Apply aggregation to each group
        results = []
        
        for group_key, group_data in groups.items():
            result = {}
            
            # Add group by fields to result
            for i, field in enumerate(group_by_fields):
                result[field] = group_key[i]
            
            # Apply aggregation rules
            for rule in rules:
                field_name = rule.field_name
                agg_type = rule.aggregation_type
                alias = rule.alias or f"{agg_type.value}_{field_name}"
                
                # Extract field values from group
                values = []
                for record in group_data:
                    if field_name in record and record[field_name] is not None:
                        values.append(record[field_name])
                
                # Apply aggregation function
                if values:
                    agg_function = self.aggregation_functions.get(agg_type)
                    if agg_function:
                        result[alias] = agg_function(values, rule)
                    else:
                        result[alias] = None
                else:
                    result[alias] = None
            
            results.append(result)
        
        return results
    
    def _sum_aggregation(self, values: List[Any], rule: AggregationRule) -> Union[int, float]:
        """Sum aggregation"""
        try:
            return sum(float(v) for v in values if isinstance(v, (int, float)))
        except Exception:
            return 0
    
    def _avg_aggregation(self, values: List[Any], rule: AggregationRule) -> float:
        """Average aggregation"""
        try:
            numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
            return sum(numeric_values) / len(numeric_values) if numeric_values else 0
        except Exception:
            return 0
    
    def _count_aggregation(self, values: List[Any], rule: AggregationRule) -> int:
        """Count aggregation"""
        return len(values)
    
    def _min_aggregation(self, values: List[Any], rule: AggregationRule) -> Any:
        """Minimum aggregation"""
        try:
            numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
            return min(numeric_values) if numeric_values else None
        except Exception:
            return None
    
    def _max_aggregation(self, values: List[Any], rule: AggregationRule) -> Any:
        """Maximum aggregation"""
        try:
            numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
            return max(numeric_values) if numeric_values else None
        except Exception:
            return None
    
    def _stddev_aggregation(self, values: List[Any], rule: AggregationRule) -> float:
        """Standard deviation aggregation"""
        try:
            numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
            if len(numeric_values) < 2:
                return 0
            
            mean = sum(numeric_values) / len(numeric_values)
            variance = sum((x - mean) ** 2 for x in numeric_values) / len(numeric_values)
            return variance ** 0.5
        except Exception:
            return 0
    
    def _variance_aggregation(self, values: List[Any], rule: AggregationRule) -> float:
        """Variance aggregation"""
        try:
            numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
            if len(numeric_values) < 2:
                return 0
            
            mean = sum(numeric_values) / len(numeric_values)
            return sum((x - mean) ** 2 for x in numeric_values) / len(numeric_values)
        except Exception:
            return 0
    
    def _percentile_aggregation(self, values: List[Any], rule: AggregationRule) -> float:
        """Percentile aggregation"""
        try:
            percentile = rule.conditions.get('percentile', 50) if rule.conditions else 50
            numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
            
            if not numeric_values:
                return 0
            
            numeric_values.sort()
            index = (percentile / 100) * (len(numeric_values) - 1)
            
            if index.is_integer():
                return numeric_values[int(index)]
            else:
                lower_index = int(index)
                upper_index = lower_index + 1
                lower_value = numeric_values[lower_index]
                upper_value = numeric_values[upper_index] if upper_index < len(numeric_values) else lower_value
                fraction = index - lower_index
                return lower_value + fraction * (upper_value - lower_value)
        except Exception:
            return 0


class DataArchiver:
    """Data archiver for historical data storage"""
    
    def __init__(self):
        self.compression_algorithms = {
            'gzip': self._gzip_compress,
            'lz4': self._lz4_compress,
            'none': self._no_compress
        }
        
        self.encryption_algorithms = {
            'aes256': self._aes256_encrypt,
            'none': self._no_encrypt
        }
    
    def archive_data(self, data: List[Dict[str, Any]], archive_rule: ArchiveRule) -> bytes:
        """Archive data according to rule"""
        try:
            # Convert data to JSON
            json_data = json.dumps(data, default=str)
            
            # Apply compression
            compressed_data = self._apply_compression(json_data, archive_rule.compression)
            
            # Apply encryption
            encrypted_data = self._apply_encryption(compressed_data, archive_rule.encryption)
            
            return encrypted_data
            
        except Exception as e:
            print(f"Error archiving data: {e}")
            return b''
    
    def restore_data(self, archived_data: bytes, archive_rule: ArchiveRule) -> List[Dict[str, Any]]:
        """Restore archived data"""
        try:
            # Apply decryption
            decrypted_data = self._apply_decryption(archived_data, archive_rule.encryption)
            
            # Apply decompression
            decompressed_data = self._apply_decompression(decrypted_data, archive_rule.compression)
            
            # Parse JSON
            restored_data = json.loads(decompressed_data)
            
            return restored_data
            
        except Exception as e:
            print(f"Error restoring data: {e}")
            return []
    
    def _apply_compression(self, data: str, compression: bool) -> bytes:
        """Apply compression to data"""
        if not compression:
            return data.encode('utf-8')
        
        try:
            return gzip.compress(data.encode('utf-8'))
        except Exception as e:
            print(f"Error compressing data: {e}")
            return data.encode('utf-8')
    
    def _apply_decompression(self, data: bytes, compression: bool) -> str:
        """Apply decompression to data"""
        if not compression:
            return data.decode('utf-8')
        
        try:
            return gzip.decompress(data).decode('utf-8')
        except Exception as e:
            print(f"Error decompressing data: {e}")
            return data.decode('utf-8')
    
    def _apply_encryption(self, data: bytes, encryption: bool) -> bytes:
        """Apply encryption to data"""
        if not encryption:
            return data
        
        # This would implement actual encryption
        # For now, return data as-is
        return data
    
    def _apply_decryption(self, data: bytes, encryption: bool) -> bytes:
        """Apply decryption to data"""
        if not encryption:
            return data
        
        # This would implement actual decryption
        # For now, return data as-is
        return data
    
    def _gzip_compress(self, data: str) -> bytes:
        """Gzip compression"""
        return gzip.compress(data.encode('utf-8'))
    
    def _lz4_compress(self, data: str) -> bytes:
        """LZ4 compression (placeholder)"""
        return gzip.compress(data.encode('utf-8'))
    
    def _no_compress(self, data: str) -> bytes:
        """No compression"""
        return data.encode('utf-8')
    
    def _aes256_encrypt(self, data: bytes) -> bytes:
        """AES-256 encryption (placeholder)"""
        return data
    
    def _no_encrypt(self, data: bytes) -> bytes:
        """No encryption"""
        return data


class RetentionPolicyManager:
    """Retention policy manager for data warehouse"""
    
    def __init__(self):
        self.retention_policies = {}
        self.lock = threading.Lock()
    
    def add_retention_policy(self, policy_name: str, retention_days: int, 
                           archive_before_delete: bool = True, storage_tier: StorageTier = StorageTier.COLD):
        """Add a retention policy"""
        with self.lock:
            self.retention_policies[policy_name] = {
                'retention_days': retention_days,
                'archive_before_delete': archive_before_delete,
                'storage_tier': storage_tier,
                'created_at': datetime.utcnow()
            }
    
    def get_retention_policy(self, policy_name: str) -> Optional[Dict[str, Any]]:
        """Get retention policy by name"""
        with self.lock:
            return self.retention_policies.get(policy_name)
    
    def should_archive(self, policy_name: str, data_timestamp: datetime) -> bool:
        """Check if data should be archived according to policy"""
        policy = self.get_retention_policy(policy_name)
        if not policy:
            return False
        
        # Calculate age
        age_days = (datetime.utcnow() - data_timestamp).days
        
        # Check if data is old enough to archive
        # Archive when data is 1/3 of retention age
        archive_threshold = policy['retention_days'] / 3
        
        return age_days >= archive_threshold
    
    def should_delete(self, policy_name: str, data_timestamp: datetime) -> bool:
        """Check if data should be deleted according to policy"""
        policy = self.get_retention_policy(policy_name)
        if not policy:
            return False
        
        # Calculate age
        age_days = (datetime.utcnow() - data_timestamp).days
        
        return age_days >= policy['retention_days']
    
    def get_expiration_date(self, policy_name: str, data_timestamp: datetime) -> datetime:
        """Get expiration date for data according to policy"""
        policy = self.get_retention_policy(policy_name)
        if not policy:
            return data_timestamp + timedelta(days=365)  # Default 1 year
        
        return data_timestamp + timedelta(days=policy['retention_days'])
    
    def cleanup_expired_data(self, warehouse_id: int) -> Dict[str, int]:
        """Clean up expired data according to retention policies"""
        try:
            from app.warehouse.models import HistoricalData
            
            expired_count = 0
            archived_count = 0
            
            # Get all historical data
            historical_data = HistoricalData.query.filter_by(warehouse_id=warehouse_id).all()
            
            for data in historical_data:
                # Check each retention policy
                for policy_name, policy in self.retention_policies.items():
                    if self.should_delete(policy_name, data.data_timestamp):
                        if policy['archive_before_delete'] and data.archival_status == 'active':
                            # Archive before delete
                            data.archive_data(policy['storage_tier'].value)
                            archived_count += 1
                        else:
                            # Delete directly
                            data.delete_data()
                            expired_count += 1
                        break
            
            return {
                'expired_count': expired_count,
                'archived_count': archived_count
            }
            
        except Exception as e:
            print(f"Error cleaning up expired data: {e}")
            return {'expired_count': 0, 'archived_count': 0}


class DataQualityChecker:
    """Data quality checker for warehouse data"""
    
    def __init__(self):
        self.quality_rules = {}
        self.lock = threading.Lock()
    
    def add_quality_rule(self, rule_name: str, field_name: str, rule_type: str, 
                        parameters: Dict[str, Any]):
        """Add a data quality rule"""
        with self.lock:
            self.quality_rules[rule_name] = {
                'field_name': field_name,
                'rule_type': rule_type,
                'parameters': parameters,
                'created_at': datetime.utcnow()
            }
    
    def check_data_quality(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check data quality against all rules"""
        try:
            quality_scores = {}
            quality_issues = []
            
            for rule_name, rule in self.quality_rules.items():
                field_name = rule['field_name']
                rule_type = rule['rule_type']
                parameters = rule['parameters']
                
                # Check rule
                rule_score, rule_issues = self._check_rule(data, field_name, rule_type, parameters)
                
                quality_scores[rule_name] = rule_score
                quality_issues.extend(rule_issues)
            
            # Calculate overall quality score
            overall_score = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 1.0
            
            return {
                'overall_score': overall_score,
                'rule_scores': quality_scores,
                'issues': quality_issues,
                'total_records': len(data)
            }
            
        except Exception as e:
            print(f"Error checking data quality: {e}")
            return {'overall_score': 0, 'rule_scores': {}, 'issues': [str(e)], 'total_records': 0}
    
    def _check_rule(self, data: List[Dict[str, Any]], field_name: str, rule_type: str, 
                   parameters: Dict[str, Any]) -> tuple[float, List[str]]:
        """Check individual rule"""
        try:
            issues = []
            valid_records = 0
            
            for record in data:
                if field_name not in record:
                    issues.append(f"Missing field: {field_name}")
                    continue
                
                value = record[field_name]
                
                if rule_type == 'not_null':
                    if value is None:
                        issues.append(f"Null value in field: {field_name}")
                    else:
                        valid_records += 1
                
                elif rule_type == 'range':
                    min_val = parameters.get('min')
                    max_val = parameters.get('max')
                    
                    if min_val is not None and value < min_val:
                        issues.append(f"Value {value} below minimum {min_val} in field: {field_name}")
                    elif max_val is not None and value > max_val:
                        issues.append(f"Value {value} above maximum {max_val} in field: {field_name}")
                    else:
                        valid_records += 1
                
                elif rule_type == 'pattern':
                    pattern = parameters.get('pattern')
                    if pattern and not self._matches_pattern(str(value), pattern):
                        issues.append(f"Value {value} doesn't match pattern {pattern} in field: {field_name}")
                    else:
                        valid_records += 1
                
                elif rule_type == 'data_type':
                    expected_type = parameters.get('type')
                    if expected_type and not isinstance(value, expected_type):
                        issues.append(f"Value {value} is not type {expected_type} in field: {field_name}")
                    else:
                        valid_records += 1
                
                else:
                    valid_records += 1
            
            # Calculate score
            score = valid_records / len(data) if data else 1.0
            
            return score, issues
            
        except Exception as e:
            return 0.0, [f"Error checking rule {rule_type}: {str(e)}"]
    
    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """Check if value matches pattern"""
        import re
        try:
            return bool(re.match(pattern, value))
        except Exception:
            return False


class WarehouseMonitor:
    """Warehouse monitoring utility"""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)
        self.alert_thresholds = {
            'storage_utilization': 0.9,  # 90%
            'processing_time': 60000,  # 60 seconds
            'error_rate': 0.05,  # 5%
            'pipeline_failure_rate': 0.1  # 10%
        }
        self.lock = threading.Lock()
    
    def record_metrics(self, warehouse_id: int, metrics: Dict[str, Any]):
        """Record warehouse metrics"""
        with self.lock:
            metrics['timestamp'] = datetime.utcnow().isoformat()
            metrics['warehouse_id'] = warehouse_id
            self.metrics_history.append(metrics)
            
            # Check for alerts
            self._check_alerts(warehouse_id, metrics)
    
    def _check_alerts(self, warehouse_id: int, metrics: Dict[str, Any]):
        """Check metrics against alert thresholds"""
        alerts = []
        
        # Check storage utilization
        storage_utilization = metrics.get('storage_utilization', 0)
        if storage_utilization > self.alert_thresholds['storage_utilization']:
            alerts.append({
                'type': 'storage_utilization_high',
                'warehouse_id': warehouse_id,
                'value': storage_utilization,
                'threshold': self.alert_thresholds['storage_utilization'],
                'message': f"Storage utilization too high: {storage_utilization:.2%}"
            })
        
        # Check processing time
        processing_time = metrics.get('avg_processing_time_ms', 0)
        if processing_time > self.alert_thresholds['processing_time']:
            alerts.append({
                'type': 'processing_time_high',
                'warehouse_id': warehouse_id,
                'value': processing_time,
                'threshold': self.alert_thresholds['processing_time'],
                'message': f"Processing time too high: {processing_time:.2f}ms"
            })
        
        # Handle alerts
        for alert in alerts:
            self._handle_alert(alert)
    
    def _handle_alert(self, alert: Dict[str, Any]):
        """Handle warehouse alert"""
        try:
            print(f"Warehouse alert: {alert['message']}")
            
            # Could integrate with notification system here
            # For now, just log the alert
            
        except Exception as e:
            print(f"Error handling alert: {e}")
    
    def get_metrics_summary(self, warehouse_id: int, hours: int = 1) -> Dict[str, Any]:
        """Get metrics summary for a warehouse"""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            warehouse_metrics = [
                m for m in self.metrics_history 
                if m.get('warehouse_id') == warehouse_id and 
                datetime.fromisoformat(m['timestamp']) >= cutoff_time
            ]
            
            if not warehouse_metrics:
                return {}
            
            # Calculate averages
            avg_storage_util = sum(m.get('storage_utilization', 0) for m in warehouse_metrics) / len(warehouse_metrics)
            avg_processing_time = sum(m.get('avg_processing_time_ms', 0) for m in warehouse_metrics) / len(warehouse_metrics)
            avg_records_per_hour = sum(m.get('records_per_hour', 0) for m in warehouse_metrics) / len(warehouse_metrics)
            
            return {
                'warehouse_id': warehouse_id,
                'period_hours': hours,
                'sample_count': len(warehouse_metrics),
                'avg_storage_utilization': avg_storage_util,
                'avg_processing_time_ms': avg_processing_time,
                'avg_records_per_hour': avg_records_per_hour,
                'timestamp': datetime.utcnow().isoformat()
            }


class WarehouseUtils:
    """General warehouse utility functions"""
    
    @staticmethod
    def generate_partition_name(table_name: str, partition_date: datetime) -> str:
        """Generate partition name for table"""
        date_str = partition_date.strftime('%Y_%m_%d')
        return f"{table_name}_{date_str}"
    
    @staticmethod
    def calculate_data_hash(data: Dict[str, Any]) -> str:
        """Calculate hash for data integrity"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    @staticmethod
    def estimate_storage_size(data: List[Dict[str, Any]]) -> int:
        """Estimate storage size in bytes"""
        try:
            json_str = json.dumps(data, default=str)
            return len(json_str.encode('utf-8'))
        except Exception:
            return 1000  # Default estimate
    
    @staticmethod
    def validate_schema(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against schema"""
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            if not data:
                validation_result['errors'].append("No data to validate")
                validation_result['valid'] = False
                return validation_result
            
            # Check required fields
            required_fields = schema.get('required_fields', [])
            for field in required_fields:
                for i, record in enumerate(data):
                    if field not in record:
                        validation_result['errors'].append(f"Missing required field '{field}' in record {i}")
                        validation_result['valid'] = False
            
            # Check field types
            field_types = schema.get('field_types', {})
            for field, expected_type in field_types.items():
                for i, record in enumerate(data):
                    if field in record and record[field] is not None:
                        if not isinstance(record[field], expected_type):
                            validation_result['errors'].append(f"Field '{field}' has wrong type in record {i}")
                            validation_result['valid'] = False
            
            # Check field constraints
            field_constraints = schema.get('field_constraints', {})
            for field, constraints in field_constraints.items():
                for i, record in enumerate(data):
                    if field in record and record[field] is not None:
                        value = record[field]
                        
                        # Check min/max
                        if 'min' in constraints and value < constraints['min']:
                            validation_result['errors'].append(f"Field '{field}' below minimum in record {i}")
                            validation_result['valid'] = False
                        
                        if 'max' in constraints and value > constraints['max']:
                            validation_result['errors'].append(f"Field '{field}' above maximum in record {i}")
                            validation_result['valid'] = False
                        
                        # Check pattern
                        if 'pattern' in constraints:
                            import re
                            if not re.match(constraints['pattern'], str(value)):
                                validation_result['errors'].append(f"Field '{field}' doesn't match pattern in record {i}")
                                validation_result['valid'] = False
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': []
            }
    
    @staticmethod
    def optimize_query_performance(query: str) -> str:
        """Optimize query for better performance"""
        try:
            # This would implement query optimization
            # For now, return the query as-is
            return query
        except Exception as e:
            print(f"Error optimizing query: {e}")
            return query
    
    @staticmethod
    def generate_report_summary(data: List[Dict[str, Any]], metrics: List[str]) -> Dict[str, Any]:
        """Generate summary report from data"""
        try:
            summary = {
                'total_records': len(data),
                'metrics': {}
            }
            
            for metric in metrics:
                values = []
                for record in data:
                    if metric in record and record[metric] is not None:
                        if isinstance(record[metric], (int, float)):
                            values.append(record[metric])
                
                if values:
                    summary['metrics'][metric] = {
                        'count': len(values),
                        'sum': sum(values),
                        'avg': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values)
                    }
                else:
                    summary['metrics'][metric] = {
                        'count': 0,
                        'sum': 0,
                        'avg': 0,
                        'min': 0,
                        'max': 0
                    }
            
            return summary
            
        except Exception as e:
            print(f"Error generating report summary: {e}")
            return {'total_records': 0, 'metrics': {}}


# Global instances
aggregation_engine = AggregationEngine()
data_archiver = DataArchiver()
retention_policy_manager = RetentionPolicyManager()
data_quality_checker = DataQualityChecker()
warehouse_monitor = WarehouseMonitor()
