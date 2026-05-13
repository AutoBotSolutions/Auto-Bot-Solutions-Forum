"""
Bulk Processor

Processes bulk operations with batching, validation, and error handling.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Iterator
from datetime import datetime
import json
import csv
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

from .bulk_manager import BulkOperation, BulkOperationConfig, BulkOperationType

logger = logging.getLogger(__name__)

class BulkProcessor:
    """Processes bulk operations with advanced features"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processors = {}
        self.validators = {}
        self.transformers = {}
    
    def register_processor(self, resource_type: str, operation_type: BulkOperationType, 
                          processor: Callable):
        """Register a processor for specific resource and operation type"""
        if resource_type not in self.processors:
            self.processors[resource_type] = {}
        self.processors[resource_type][operation_type] = processor
    
    def register_validator(self, resource_type: str, validator: Callable):
        """Register a validator for a resource type"""
        self.validators[resource_type] = validator
    
    def register_transformer(self, resource_type: str, transformer: Callable):
        """Register a transformer for a resource type"""
        self.transformers[resource_type] = transformer
    
    def process_operation(self, operation: BulkOperation) -> Dict[str, Any]:
        """Process a bulk operation"""
        try:
            # Get processor
            processors = self.processors.get(operation.resource_type, {})
            processor = processors.get(operation.config.operation_type)
            
            if not processor:
                raise ValueError(f"No processor found for {operation.config.operation_type.value} on {operation.resource_type}")
            
            # Validate data if validator exists
            if operation.resource_type in self.validators:
                validator = self.validators[operation.resource_type]
                validation_result = validator(operation.data)
                if not validation_result['valid']:
                    return {
                        'success': False,
                        'errors': validation_result['errors'],
                        'processed': 0,
                        'successful': 0,
                        'failed': 0
                    }
            
            # Transform data if transformer exists
            if operation.resource_type in self.transformers:
                transformer = self.transformers[operation.resource_type]
                operation.data = transformer(operation.data)
            
            # Process with batching
            return self._process_with_batches(operation, processor)
        
        except Exception as e:
            logger.error(f"Error processing bulk operation: {e}")
            return {
                'success': False,
                'errors': [str(e)],
                'processed': 0,
                'successful': 0,
                'failed': 0
            }
    
    def _process_with_batches(self, operation: BulkOperation, processor: Callable) -> Dict[str, Any]:
        """Process operation in batches"""
        batch_size = operation.config.batch_size
        total_items = len(operation.data)
        
        processed = 0
        successful = 0
        failed = 0
        errors = []
        
        # Create batches
        batches = self._create_batches(operation.data, batch_size)
        
        # Process batches
        if operation.config.max_workers > 1:
            # Parallel processing
            results = self._process_batches_parallel(operation, batches, processor)
        else:
            # Sequential processing
            results = self._process_batches_sequential(operation, batches, processor)
        
        # Aggregate results
        for result in results:
            processed += result['processed']
            successful += result['successful']
            failed += result['failed']
            errors.extend(result['errors'])
        
        return {
            'success': failed == 0 or operation.config.continue_on_error,
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
    
    def _create_batches(self, data: List[Dict[str, Any]], batch_size: int) -> List[List[Dict[str, Any]]]:
        """Create batches from data"""
        batches = []
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batches.append(batch)
        return batches
    
    def _process_batches_sequential(self, operation: BulkOperation, 
                                   batches: List[List[Dict[str, Any]]], 
                                   processor: Callable) -> List[Dict[str, Any]]:
        """Process batches sequentially"""
        results = []
        
        for i, batch in enumerate(batches):
            try:
                result = processor(batch, operation.config)
                result['batch_index'] = i
                results.append(result)
                
                # Update progress
                operation.update_progress(
                    processed=sum(r['processed'] for r in results),
                    successful=sum(r['successful'] for r in results),
                    failed=sum(r['failed'] for r in results)
                )
                
            except Exception as e:
                logger.error(f"Error processing batch {i}: {e}")
                results.append({
                    'batch_index': i,
                    'processed': len(batch),
                    'successful': 0,
                    'failed': len(batch),
                    'errors': [str(e)]
                })
                
                if not operation.config.continue_on_error:
                    break
        
        return results
    
    def _process_batches_parallel(self, operation: BulkOperation, 
                                 batches: List[List[Dict[str, Any]]], 
                                 processor: Callable) -> List[Dict[str, Any]]:
        """Process batches in parallel"""
        futures = {}
        results = []
        
        # Submit batches for processing
        for i, batch in enumerate(batches):
            future = self.executor.submit(self._process_single_batch, processor, batch, operation.config, i)
            futures[future] = i
        
        # Collect results
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                
                # Update progress
                operation.update_progress(
                    processed=sum(r['processed'] for r in results),
                    successful=sum(r['successful'] for r in results),
                    failed=sum(r['failed'] for r in results)
                )
                
            except Exception as e:
                batch_index = futures[future]
                logger.error(f"Error processing batch {batch_index}: {e}")
                results.append({
                    'batch_index': batch_index,
                    'processed': len(batches[batch_index]),
                    'successful': 0,
                    'failed': len(batches[batch_index]),
                    'errors': [str(e)]
                })
                
                if not operation.config.continue_on_error:
                    # Cancel remaining futures
                    for f in futures:
                        if not f.done():
                            f.cancel()
                    break
        
        # Sort results by batch index
        results.sort(key=lambda x: x['batch_index'])
        return results
    
    def _process_single_batch(self, processor: Callable, batch: List[Dict[str, Any]], 
                             config: BulkOperationConfig, batch_index: int) -> Dict[str, Any]:
        """Process a single batch"""
        try:
            return processor(batch, config)
        except Exception as e:
            logger.error(f"Error in batch {batch_index}: {e}")
            return {
                'batch_index': batch_index,
                'processed': len(batch),
                'successful': 0,
                'failed': len(batch),
                'errors': [str(e)]
            }

class CSVProcessor:
    """Processes CSV files for bulk operations"""
    
    def __init__(self):
        self.field_mappings = {}
        self.validators = {}
    
    def register_field_mapping(self, resource_type: str, mapping: Dict[str, str]):
        """Register field mapping for CSV columns"""
        self.field_mappings[resource_type] = mapping
    
    def register_validator(self, resource_type: str, validator: Callable):
        """Register CSV validator for resource type"""
        self.validators[resource_type] = validator
    
    def parse_csv(self, csv_content: str, resource_type: str, 
                  delimiter: str = ',', has_header: bool = True) -> List[Dict[str, Any]]:
        """Parse CSV content into data list"""
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
            
            data = []
            field_mapping = self.field_mappings.get(resource_type, {})
            
            for row_num, row in enumerate(csv_reader, 1):
                try:
                    # Apply field mapping
                    mapped_row = {}
                    for csv_field, data_field in field_mapping.items():
                        if csv_field in row:
                            mapped_row[data_field] = row[csv_field]
                    
                    # Add unmapped fields
                    for field, value in row.items():
                        if field not in field_mapping:
                            mapped_row[field] = value
                    
                    # Add row number for error tracking
                    mapped_row['_row_number'] = row_num
                    
                    data.append(mapped_row)
                
                except Exception as e:
                    logger.error(f"Error parsing CSV row {row_num}: {e}")
                    continue
            
            # Validate data if validator exists
            if resource_type in self.validators:
                validator = self.validators[resource_type]
                validation_result = validator(data)
                if not validation_result['valid']:
                    raise ValueError(f"CSV validation failed: {validation_result['errors']}")
            
            return data
        
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise
    
    def generate_csv(self, data: List[Dict[str, Any]], resource_type: str,
                    field_mapping: Dict[str, str] = None) -> str:
        """Generate CSV content from data"""
        try:
            if not data:
                return ""
            
            # Use provided mapping or registered mapping
            mapping = field_mapping or self.field_mappings.get(resource_type, {})
            
            # Reverse mapping for CSV headers
            reverse_mapping = {v: k for k, v in mapping.items() if v != k}
            
            output = io.StringIO()
            
            # Get all fields from first item and apply reverse mapping
            first_item = data[0]
            csv_fields = []
            
            for field in first_item.keys():
                if field in reverse_mapping:
                    csv_fields.append(reverse_mapping[field])
                elif field not in mapping:
                    csv_fields.append(field)
                else:
                    csv_fields.append(field)  # Use original field name
            
            # Create CSV writer
            csv_writer = csv.DictWriter(output, fieldnames=csv_fields)
            csv_writer.writeheader()
            
            # Write data rows
            for item in data:
                csv_row = {}
                
                for field, value in item.items():
                    if field in reverse_mapping:
                        csv_row[reverse_mapping[field]] = value
                    elif field not in mapping:
                        csv_row[field] = value
                    else:
                        csv_row[field] = value
                
                csv_writer.writerow(csv_row)
            
            return output.getvalue()
        
        except Exception as e:
            logger.error(f"Error generating CSV: {e}")
            raise

class JSONProcessor:
    """Processes JSON files for bulk operations"""
    
    def __init__(self):
        self.validators = {}
        self.transformers = {}
    
    def register_validator(self, resource_type: str, validator: Callable):
        """Register JSON validator for resource type"""
        self.validators[resource_type] = validator
    
    def register_transformer(self, resource_type: str, transformer: Callable):
        """Register JSON transformer for resource type"""
        self.transformers[resource_type] = transformer
    
    def parse_json(self, json_content: str, resource_type: str) -> List[Dict[str, Any]]:
        """Parse JSON content into data list"""
        try:
            data = json.loads(json_content)
            
            # Ensure data is a list
            if not isinstance(data, list):
                if isinstance(data, dict):
                    data = [data]
                else:
                    raise ValueError("JSON data must be an object or array of objects")
            
            # Validate data if validator exists
            if resource_type in self.validators:
                validator = self.validators[resource_type]
                validation_result = validator(data)
                if not validation_result['valid']:
                    raise ValueError(f"JSON validation failed: {validation_result['errors']}")
            
            # Transform data if transformer exists
            if resource_type in self.transformers:
                transformer = self.transformers[resource_type]
                data = transformer(data)
            
            return data
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            raise
    
    def generate_json(self, data: List[Dict[str, Any]], resource_type: str,
                     pretty_print: bool = True) -> str:
        """Generate JSON content from data"""
        try:
            if pretty_print:
                return json.dumps(data, indent=2, default=str)
            else:
                return json.dumps(data, default=str)
        
        except Exception as e:
            logger.error(f"Error generating JSON: {e}")
            raise

class ExcelProcessor:
    """Processes Excel files for bulk operations"""
    
    def __init__(self):
        try:
            import pandas as pd
            self.pd = pd
        except ImportError:
            self.pd = None
            logger.warning("pandas not available, Excel processing disabled")
        
        self.field_mappings = {}
        self.validators = {}
    
    def register_field_mapping(self, resource_type: str, mapping: Dict[str, str]):
        """Register field mapping for Excel columns"""
        self.field_mappings[resource_type] = mapping
    
    def register_validator(self, resource_type: str, validator: Callable):
        """Register Excel validator for resource type"""
        self.validators[resource_type] = validator
    
    def parse_excel(self, file_content: bytes, resource_type: str, 
                   sheet_name: str = None) -> List[Dict[str, Any]]:
        """Parse Excel file content into data list"""
        if not self.pd:
            raise ImportError("pandas is required for Excel processing")
        
        try:
            # Read Excel file
            df = self.pd.read_excel(io.BytesIO(file_content), sheet_name=sheet_name)
            
            # Convert to list of dictionaries
            data = df.to_dict('records')
            
            # Apply field mapping
            field_mapping = self.field_mappings.get(resource_type, {})
            if field_mapping:
                mapped_data = []
                for row in data:
                    mapped_row = {}
                    for excel_field, data_field in field_mapping.items():
                        if excel_field in row:
                            mapped_row[data_field] = row[excel_field]
                    
                    # Add unmapped fields
                    for field, value in row.items():
                        if field not in field_mapping:
                            mapped_row[field] = value
                    
                    mapped_data.append(mapped_row)
                
                data = mapped_data
            
            # Validate data if validator exists
            if resource_type in self.validators:
                validator = self.validators[resource_type]
                validation_result = validator(data)
                if not validation_result['valid']:
                    raise ValueError(f"Excel validation failed: {validation_result['errors']}")
            
            return data
        
        except Exception as e:
            logger.error(f"Error parsing Excel file: {e}")
            raise
    
    def generate_excel(self, data: List[Dict[str, Any]], resource_type: str,
                     field_mapping: Dict[str, str] = None) -> bytes:
        """Generate Excel file content from data"""
        if not self.pd:
            raise ImportError("pandas is required for Excel processing")
        
        try:
            if not data:
                return b""
            
            # Use provided mapping or registered mapping
            mapping = field_mapping or self.field_mappings.get(resource_type, {})
            
            # Apply field mapping
            if mapping:
                mapped_data = []
                for item in data:
                    mapped_row = {}
                    for field, value in item.items():
                        if field in mapping:
                            mapped_row[mapping[field]] = value
                        else:
                            mapped_row[field] = value
                    mapped_data.append(mapped_row)
                data = mapped_data
            
            # Create DataFrame
            df = self.pd.DataFrame(data)
            
            # Generate Excel file
            output = io.BytesIO()
            with self.pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            
            return output.getvalue()
        
        except Exception as e:
            logger.error(f"Error generating Excel file: {e}")
            raise

class BulkDataProcessor:
    """Unified bulk data processor supporting multiple formats"""
    
    def __init__(self):
        self.csv_processor = CSVProcessor()
        self.json_processor = JSONProcessor()
        self.excel_processor = ExcelProcessor()
        self.supported_formats = ['csv', 'json', 'excel']
    
    def process_file(self, file_content: Union[str, bytes], file_format: str, 
                    resource_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Process file content based on format"""
        file_format = file_format.lower()
        
        if file_format == 'csv':
            return self.csv_processor.parse_csv(file_content, resource_type, **kwargs)
        elif file_format == 'json':
            return self.json_processor.parse_json(file_content, resource_type)
        elif file_format == 'excel':
            return self.excel_processor.parse_excel(file_content, resource_type, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
    
    def generate_file(self, data: List[Dict[str, Any]], file_format: str, 
                     resource_type: str, **kwargs) -> Union[str, bytes]:
        """Generate file content based on format"""
        file_format = file_format.lower()
        
        if file_format == 'csv':
            return self.csv_processor.generate_csv(data, resource_type, **kwargs)
        elif file_format == 'json':
            return self.json_processor.generate_json(data, resource_type, **kwargs)
        elif file_format == 'excel':
            return self.excel_processor.generate_excel(data, resource_type, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
    
    def register_field_mapping(self, resource_type: str, format_type: str, mapping: Dict[str, str]):
        """Register field mapping for format and resource type"""
        if format_type == 'csv':
            self.csv_processor.register_field_mapping(resource_type, mapping)
        elif format_type == 'excel':
            self.excel_processor.register_field_mapping(resource_type, mapping)
    
    def register_validator(self, resource_type: str, format_type: str, validator: Callable):
        """Register validator for format and resource type"""
        if format_type == 'csv':
            self.csv_processor.register_validator(resource_type, validator)
        elif format_type == 'json':
            self.json_processor.register_validator(resource_type, validator)
        elif format_type == 'excel':
            self.excel_processor.register_validator(resource_type, validator)
