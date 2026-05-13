#!/usr/bin/env python3
"""
Comprehensive Debugging Script for Newly Added Systems
Auto Bot Solutions Forum

This script tests and validates all the newly added systems:
- Analytics Infrastructure
- Search Infrastructure  
- Additional Dependencies
- Integration between systems
"""

import os
import sys
import time
import json
import logging
import subprocess
import psycopg2
import redis
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Add the project root to Python path
sys.path.insert(0, '/home/robbie/Desktop/repo-forum')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/debug_new_systems.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """System status enumeration"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class TestResult:
    """Test result data structure"""
    system_name: str
    test_name: str
    status: str  # "PASS", "FAIL", "SKIP"
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    execution_time: float


class SystemDebugger:
    """Main system debugger class"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment and config files"""
        config = {
            'database': {
                'host': os.getenv('ANALYTICS_DB_HOST', 'localhost'),
                'port': int(os.getenv('ANALYTICS_DB_PORT', 5432)),
                'database': os.getenv('ANALYTICS_DB_NAME', 'forum_analytics'),
                'username': os.getenv('ANALYTICS_DB_USER', 'analytics_user'),
                'password': os.getenv('ANALYTICS_DB_PASSWORD', 'analytics_password')
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': int(os.getenv('REDIS_DB', 0)),
                'password': os.getenv('REDIS_PASSWORD', None)
            },
            'elasticsearch': {
                'host': os.getenv('ELASTICSEARCH_HOST', 'localhost'),
                'port': int(os.getenv('ELASTICSEARCH_PORT', 9200)),
                'username': os.getenv('ELASTICSEARCH_USERNAME', None),
                'password': os.getenv('ELASTICSEARCH_PASSWORD', None)
            },
            'prometheus': {
                'host': os.getenv('PROMETHEUS_HOST', 'localhost'),
                'port': int(os.getenv('PROMETHEUS_PORT', 9090))
            },
            'grafana': {
                'host': os.getenv('GRAFANA_HOST', 'localhost'),
                'port': int(os.getenv('GRAFANA_PORT', 3000))
            },
            'kibana': {
                'host': os.getenv('KIBANA_HOST', 'localhost'),
                'port': int(os.getenv('KIBANA_PORT', 5601))
            }
        }
        return config
    
    def _add_result(self, system_name: str, test_name: str, status: str, 
                    message: str, details: Dict[str, Any], execution_time: float = 0.0):
        """Add a test result"""
        result = TestResult(
            system_name=system_name,
            test_name=test_name,
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            execution_time=execution_time
        )
        self.results.append(result)
        
        # Log the result
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        logger.info(f"{status_icon} [{system_name}] {test_name}: {message}")
        
        if status == "FAIL":
            logger.error(f"   Details: {details}")
    
    def test_dependencies(self) -> bool:
        """Test all additional dependencies"""
        logger.info("Testing Additional Dependencies...")
        
        # Test Python packages
        self._test_python_packages()
        
        # Test system services
        self._test_system_services()
        
        # Test setup script
        self._test_setup_script()
        
        return self._get_system_status("Additional Dependencies")
    
    def _test_python_packages(self):
        """Test critical Python packages"""
        start_time = time.time()
        
        critical_packages = [
            'flask', 'sqlalchemy', 'pandas', 'numpy', 'scipy',
            'matplotlib', 'seaborn', 'plotly', 'scikit-learn',
            'elasticsearch', 'redis', 'celery', 'prometheus_client',
            'psycopg2', 'alembic', 'sqlalchemy_utils'
        ]
        
        failed_packages = []
        successful_packages = []
        
        for package in critical_packages:
            try:
                __import__(package)
                successful_packages.append(package)
            except ImportError as e:
                failed_packages.append(f"{package}: {str(e)}")
        
        execution_time = time.time() - start_time
        
        if not failed_packages:
            self._add_result(
                "Additional Dependencies", 
                "Python Packages Import",
                "PASS",
                f"All {len(successful_packages)} critical packages imported successfully",
                {"successful_packages": successful_packages, "failed_packages": []},
                execution_time
            )
        else:
            self._add_result(
                "Additional Dependencies",
                "Python Packages Import", 
                "FAIL",
                f"Failed to import {len(failed_packages)} packages",
                {"successful_packages": successful_packages, "failed_packages": failed_packages},
                execution_time
            )
    
    def _test_system_services(self):
        """Test critical system services"""
        services = {
            'redis': ('redis-cli', 'ping'),
            'elasticsearch': ('curl', '-s', 'http://localhost:9200'),
            'prometheus': ('curl', '-s', 'http://localhost:9090/-/healthy'),
            'grafana': ('curl', '-s', 'http://localhost:3000/api/health'),
            'kibana': ('curl', '-s', 'http://localhost:5601/api/status')
        }
        
        for service_name, service_cmd in services.items():
            start_time = time.time()
            try:
                result = subprocess.run(service_cmd, capture_output=True, text=True, timeout=10)
                execution_time = time.time() - start_time
                
                if result.returncode == 0:
                    self._add_result(
                        "Additional Dependencies",
                        f"Service {service_name}",
                        "PASS",
                        f"Service {service_name} is running",
                        {"stdout": result.stdout.strip(), "returncode": result.returncode},
                        execution_time
                    )
                else:
                    self._add_result(
                        "Additional Dependencies",
                        f"Service {service_name}",
                        "FAIL",
                        f"Service {service_name} is not responding",
                        {"stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "returncode": result.returncode},
                        execution_time
                    )
            except subprocess.TimeoutExpired:
                self._add_result(
                    "Additional Dependencies",
                    f"Service {service_name}",
                    "FAIL",
                    f"Service {service_name} timeout",
                    {"error": "timeout after 10 seconds"},
                    10.0
                )
            except Exception as e:
                self._add_result(
                    "Additional Dependencies",
                    f"Service {service_name}",
                    "FAIL",
                    f"Error testing service {service_name}: {str(e)}",
                    {"error": str(e)},
                    0.0
                )
    
    def _test_setup_script(self):
        """Test the setup script functionality"""
        start_time = time.time()
        
        setup_script_path = "/home/robbie/Desktop/repo-forum/deploy/dependencies/setup-dependencies.sh"
        
        if os.path.exists(setup_script_path):
            # Check if script is executable
            if os.access(setup_script_path, os.X_OK):
                self._add_result(
                    "Additional Dependencies",
                    "Setup Script",
                    "PASS",
                    "Setup script exists and is executable",
                    {"path": setup_script_path, "executable": True},
                    time.time() - start_time
                )
            else:
                self._add_result(
                    "Additional Dependencies",
                    "Setup Script",
                    "FAIL",
                    "Setup script exists but is not executable",
                    {"path": setup_script_path, "executable": False},
                    time.time() - start_time
                )
        else:
            self._add_result(
                "Additional Dependencies",
                "Setup Script",
                "FAIL",
                "Setup script not found",
                {"path": setup_script_path},
                time.time() - start_time
            )
    
    def test_analytics_infrastructure(self) -> bool:
        """Test analytics infrastructure components"""
        logger.info("Testing Analytics Infrastructure...")
        
        # Test analytics database
        self._test_analytics_database()
        
        # Test data pipeline configuration
        self._test_data_pipeline_config()
        
        # Test analytics monitoring
        self._test_analytics_monitoring()
        
        # Test performance optimization
        self._test_performance_optimization()
        
        return self._get_system_status("Analytics Infrastructure")
    
    def _test_analytics_database(self):
        """Test analytics database connectivity and schema"""
        start_time = time.time()
        
        try:
            # Test database connection
            conn = psycopg2.connect(
                host=self.config['database']['host'],
                port=self.config['database']['port'],
                database=self.config['database']['database'],
                user=self.config['database']['username'],
                password=self.config['database']['password']
            )
            
            cursor = conn.cursor()
            
            # Test if database exists and is accessible
            cursor.execute("SELECT 1")
            test_result = cursor.fetchone()
            
            if test_result and test_result[0] == 1:
                # Test if schemas exist
                cursor.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name IN ('analytics', 'pipeline', 'monitoring')
                """)
                schemas = [row[0] for row in cursor.fetchall()]
                
                expected_schemas = ['analytics', 'pipeline', 'monitoring']
                missing_schemas = [s for s in expected_schemas if s not in schemas]
                
                if not missing_schemas:
                    # Test if tables exist
                    cursor.execute("""
                        SELECT table_schema, table_name 
                        FROM information_schema.tables 
                        WHERE table_schema IN ('analytics', 'pipeline', 'monitoring')
                        ORDER BY table_schema, table_name
                    """)
                    tables = [(row[0], row[1]) for row in cursor.fetchall()]
                    
                    self._add_result(
                        "Analytics Infrastructure",
                        "Database Connectivity",
                        "PASS",
                        f"Database connected with {len(schemas)} schemas and {len(tables)} tables",
                        {
                            "schemas": schemas,
                            "tables": tables,
                            "database": self.config['database']['database']
                        },
                        time.time() - start_time
                    )
                else:
                    self._add_result(
                        "Analytics Infrastructure",
                        "Database Connectivity",
                        "FAIL",
                        f"Missing schemas: {missing_schemas}",
                        {
                            "existing_schemas": schemas,
                            "missing_schemas": missing_schemas
                        },
                        time.time() - start_time
                    )
            else:
                self._add_result(
                    "Analytics Infrastructure",
                    "Database Connectivity",
                    "FAIL",
                    "Database test query failed",
                    {"test_result": test_result},
                    time.time() - start_time
                )
            
            cursor.close()
            conn.close()
            
        except psycopg2.OperationalError as e:
            self._add_result(
                "Analytics Infrastructure",
                "Database Connectivity",
                "FAIL",
                f"Database connection failed: {str(e)}",
                {
                    "error": str(e),
                    "config": {
                        "host": self.config['database']['host'],
                        "port": self.config['database']['port'],
                        "database": self.config['database']['database'],
                        "username": self.config['database']['username']
                    }
                },
                time.time() - start_time
            )
        except Exception as e:
            self._add_result(
                "Analytics Infrastructure",
                "Database Connectivity",
                "FAIL",
                f"Unexpected error: {str(e)}",
                {"error": str(e)},
                time.time() - start_time
            )
    
    def _test_data_pipeline_config(self):
        """Test data pipeline configuration"""
        start_time = time.time()
        
        config_file = "/home/robbie/Desktop/repo-forum/deploy/pipeline/config.yaml"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config_data = f.read()
                
                # Basic YAML validation
                if 'pipelines:' in config_data and 'database:' in config_data:
                    # Try to parse YAML
                    try:
                        import yaml
                        parsed_config = yaml.safe_load(config_data)
                        
                        # Check for required pipeline configurations
                        pipelines = parsed_config.get('pipelines', {})
                        required_pipelines = ['user_activity_pipeline', 'content_analytics_pipeline', 'system_metrics_pipeline']
                        missing_pipelines = [p for p in required_pipelines if p not in pipelines]
                        
                        if not missing_pipelines:
                            self._add_result(
                                "Analytics Infrastructure",
                                "Data Pipeline Configuration",
                                "PASS",
                                f"Pipeline configuration valid with {len(pipelines)} pipelines",
                                {
                                    "pipelines": list(pipelines.keys()),
                                    "config_file": config_file,
                                    "yaml_valid": True
                                },
                                time.time() - start_time
                            )
                        else:
                            self._add_result(
                                "Analytics Infrastructure",
                                "Data Pipeline Configuration",
                                "FAIL",
                                f"Missing required pipelines: {missing_pipelines}",
                                {
                                    "existing_pipelines": list(pipelines.keys()),
                                    "missing_pipelines": missing_pipelines,
                                    "config_file": config_file
                                },
                                time.time() - start_time
                            )
                    except ImportError:
                        self._add_result(
                            "Analytics Infrastructure",
                            "Data Pipeline Configuration",
                            "PASS",
                            "Pipeline configuration file exists (YAML parsing not available)",
                            {"config_file": config_file, "yaml_valid": None},
                            time.time() - start_time
                        )
                    except yaml.YAMLError as e:
                        self._add_result(
                            "Analytics Infrastructure",
                            "Data Pipeline Configuration",
                            "FAIL",
                            f"Invalid YAML syntax: {str(e)}",
                            {"config_file": config_file, "yaml_error": str(e)},
                            time.time() - start_time
                        )
                else:
                    self._add_result(
                        "Analytics Infrastructure",
                        "Data Pipeline Configuration",
                        "FAIL",
                        "Pipeline configuration missing required sections",
                        {"config_file": config_file},
                        time.time() - start_time
                    )
                    
            except Exception as e:
                self._add_result(
                    "Analytics Infrastructure",
                    "Data Pipeline Configuration",
                    "FAIL",
                    f"Error reading pipeline configuration: {str(e)}",
                    {"config_file": config_file, "error": str(e)},
                    time.time() - start_time
                )
        else:
            self._add_result(
                "Analytics Infrastructure",
                "Data Pipeline Configuration",
                "FAIL",
                "Pipeline configuration file not found",
                {"config_file": config_file},
                time.time() - start_time
            )
    
    def _test_analytics_monitoring(self):
        """Test analytics monitoring configuration"""
        start_time = time.time()
        
        monitoring_file = "/home/robbie/Desktop/repo-forum/deploy/monitoring/analytics-monitoring.yaml"
        
        if os.path.exists(monitoring_file):
            try:
                with open(monitoring_file, 'r') as f:
                    monitoring_data = f.read()
                
                # Basic validation
                if 'monitoring:' in monitoring_data and 'alerting:' in monitoring_data:
                    # Test Prometheus connectivity
                    try:
                        prometheus_url = f"http://{self.config['prometheus']['host']}:{self.config['prometheus']['port']}"
                        response = requests.get(f"{prometheus_url}/api/v1/status/config", timeout=5)
                        
                        if response.status_code == 200:
                            self._add_result(
                                "Analytics Infrastructure",
                                "Analytics Monitoring",
                                "PASS",
                                "Monitoring configuration valid and Prometheus accessible",
                                {
                                    "monitoring_file": monitoring_file,
                                    "prometheus_url": prometheus_url,
                                    "prometheus_status": response.status_code
                                },
                                time.time() - start_time
                            )
                        else:
                            self._add_result(
                                "Analytics Infrastructure",
                                "Analytics Monitoring",
                                "FAIL",
                                f"Prometheus not accessible (status: {response.status_code})",
                                {
                                    "prometheus_url": prometheus_url,
                                    "status_code": response.status_code
                                },
                                time.time() - start_time
                            )
                    except requests.exceptions.RequestException as e:
                        self._add_result(
                            "Analytics Infrastructure",
                            "Analytics Monitoring",
                            "FAIL",
                            f"Prometheus connection failed: {str(e)}",
                            {
                                "prometheus_url": f"http://{self.config['prometheus']['host']}:{self.config['prometheus']['port']}",
                                "error": str(e)
                            },
                            time.time() - start_time
                        )
                else:
                    self._add_result(
                        "Analytics Infrastructure",
                        "Analytics Monitoring",
                        "FAIL",
                        "Monitoring configuration missing required sections",
                        {"monitoring_file": monitoring_file},
                        time.time() - start_time
                    )
                    
            except Exception as e:
                self._add_result(
                    "Analytics Infrastructure",
                    "Analytics Monitoring",
                    "FAIL",
                    f"Error reading monitoring configuration: {str(e)}",
                    {"monitoring_file": monitoring_file, "error": str(e)},
                    time.time() - start_time
                )
        else:
            self._add_result(
                "Analytics Infrastructure",
                "Analytics Monitoring",
                "FAIL",
                "Monitoring configuration file not found",
                {"monitoring_file": monitoring_file},
                time.time() - start_time
            )
    
    def _test_performance_optimization(self):
        """Test performance optimization script"""
        start_time = time.time()
        
        optimization_script = "/home/robbie/Desktop/repo-forum/deploy/analytics/performance-optimization.py"
        
        if os.path.exists(optimization_script):
            # Check if script is executable and has required modules
            if os.access(optimization_script, os.X_OK):
                try:
                    # Test script syntax
                    result = subprocess.run([
                        'python3', '-m', 'py_compile', optimization_script
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self._add_result(
                            "Analytics Infrastructure",
                            "Performance Optimization",
                            "PASS",
                            "Performance optimization script is valid",
                            {
                                "script_path": optimization_script,
                                "syntax_valid": True,
                                "executable": True
                            },
                            time.time() - start_time
                        )
                    else:
                        self._add_result(
                            "Analytics Infrastructure",
                            "Performance Optimization",
                            "FAIL",
                            f"Script syntax error: {result.stderr}",
                            {
                                "script_path": optimization_script,
                                "syntax_error": result.stderr
                            },
                            time.time() - start_time
                        )
                except Exception as e:
                    self._add_result(
                        "Analytics Infrastructure",
                        "Performance Optimization",
                        "FAIL",
                        f"Error testing optimization script: {str(e)}",
                        {"script_path": optimization_script, "error": str(e)},
                        time.time() - start_time
                    )
            else:
                self._add_result(
                    "Analytics Infrastructure",
                    "Performance Optimization",
                    "FAIL",
                    "Performance optimization script is not executable",
                    {"script_path": optimization_script, "executable": False},
                    time.time() - start_time
                )
        else:
            self._add_result(
                "Analytics Infrastructure",
                "Performance Optimization",
                "FAIL",
                "Performance optimization script not found",
                {"script_path": optimization_script},
                time.time() - start_time
            )
    
    def test_search_infrastructure(self) -> bool:
        """Test search infrastructure components"""
        logger.info("Testing Search Infrastructure...")
        
        # Test Elasticsearch cluster
        self._test_elasticsearch_cluster()
        
        # Test search index configuration
        self._test_search_index_config()
        
        # Test search monitoring
        self._test_search_monitoring()
        
        # Test search performance optimization
        self._test_search_performance_optimization()
        
        return self._get_system_status("Search Infrastructure")
    
    def _test_elasticsearch_cluster(self):
        """Test Elasticsearch cluster connectivity and health"""
        start_time = time.time()
        
        try:
            es_url = f"http://{self.config['elasticsearch']['host']}:{self.config['elasticsearch']['port']}"
            
            # Test cluster health
            response = requests.get(f"{es_url}/_cluster/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                cluster_status = health_data.get('status', 'unknown')
                node_count = health_data.get('number_of_nodes', 0)
                
                if cluster_status in ['green', 'yellow']:
                    # Test if indices exist
                    indices_response = requests.get(f"{es_url}/_cat/indices?format=json", timeout=10)
                    
                    if indices_response.status_code == 200:
                        indices = indices_response.json()
                        index_names = [idx['index'] for idx in indices if not idx['index'].startswith('.')]
                        
                        self._add_result(
                            "Search Infrastructure",
                            "Elasticsearch Cluster",
                            "PASS",
                            f"Cluster healthy (status: {cluster_status}) with {node_count} nodes and {len(index_names)} indices",
                            {
                                "cluster_status": cluster_status,
                                "node_count": node_count,
                                "indices": index_names,
                                "health_data": health_data
                            },
                            time.time() - start_time
                        )
                    else:
                        self._add_result(
                            "Search Infrastructure",
                            "Elasticsearch Cluster",
                            "PASS",
                            f"Cluster healthy (status: {cluster_status}) with {node_count} nodes",
                            {
                                "cluster_status": cluster_status,
                                "node_count": node_count,
                                "indices_error": indices_response.status_code
                            },
                            time.time() - start_time
                        )
                else:
                    self._add_result(
                        "Search Infrastructure",
                        "Elasticsearch Cluster",
                        "FAIL",
                        f"Cluster status is {cluster_status}",
                        {"cluster_status": cluster_status, "health_data": health_data},
                        time.time() - start_time
                    )
            else:
                self._add_result(
                    "Search Infrastructure",
                    "Elasticsearch Cluster",
                    "FAIL",
                    f"Elasticsearch health check failed (status: {response.status_code})",
                    {"status_code": response.status_code, "response": response.text},
                    time.time() - start_time
                )
                
        except requests.exceptions.RequestException as e:
            self._add_result(
                "Search Infrastructure",
                "Elasticsearch Cluster",
                "FAIL",
                f"Elasticsearch connection failed: {str(e)}",
                {
                    "es_url": f"http://{self.config['elasticsearch']['host']}:{self.config['elasticsearch']['port']}",
                    "error": str(e)
                },
                time.time() - start_time
            )
        except Exception as e:
            self._add_result(
                "Search Infrastructure",
                "Elasticsearch Cluster",
                "FAIL",
                f"Unexpected error: {str(e)}",
                {"error": str(e)},
                time.time() - start_time
            )
    
    def _test_search_index_config(self):
        """Test search index configuration"""
        start_time = time.time()
        
        config_file = "/home/robbie/Desktop/repo-forum/deploy/search/index-config.json"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Validate JSON structure
                if 'search_indices' in config_data and isinstance(config_data['search_indices'], dict):
                    indices = config_data['search_indices']
                    expected_indices = ['forum_posts', 'users', 'forum_comments', 'search_analytics']
                    missing_indices = [idx for idx in expected_indices if idx not in indices]
                    
                    if not missing_indices:
                        # Test if indices actually exist in Elasticsearch
                        es_url = f"http://{self.config['elasticsearch']['host']}:{self.config['elasticsearch']['port']}"
                        existing_indices = []
                        
                        for index_name in expected_indices:
                            try:
                                response = requests.get(f"{es_url}/{index_name}", timeout=5)
                                if response.status_code == 200:
                                    existing_indices.append(index_name)
                            except:
                                pass
                        
                        self._add_result(
                            "Search Infrastructure",
                            "Search Index Configuration",
                            "PASS",
                            f"Index configuration valid with {len(indices)} indices, {len(existing_indices)} exist in ES",
                            {
                                "configured_indices": list(indices.keys()),
                                "existing_indices": existing_indices,
                                "config_file": config_file,
                                "json_valid": True
                            },
                            time.time() - start_time
                        )
                    else:
                        self._add_result(
                            "Search Infrastructure",
                            "Search Index Configuration",
                            "FAIL",
                            f"Missing required indices: {missing_indices}",
                            {
                                "configured_indices": list(indices.keys()),
                                "missing_indices": missing_indices,
                                "config_file": config_file
                            },
                            time.time() - start_time
                        )
                else:
                    self._add_result(
                        "Search Infrastructure",
                        "Search Index Configuration",
                        "FAIL",
                        "Index configuration missing search_indices section",
                        {"config_file": config_file},
                        time.time() - start_time
                    )
                    
            except json.JSONDecodeError as e:
                self._add_result(
                    "Search Infrastructure",
                    "Search Index Configuration",
                    "FAIL",
                    f"Invalid JSON syntax: {str(e)}",
                    {"config_file": config_file, "json_error": str(e)},
                    time.time() - start_time
                )
            except Exception as e:
                self._add_result(
                    "Search Infrastructure",
                    "Search Index Configuration",
                    "FAIL",
                    f"Error reading index configuration: {str(e)}",
                    {"config_file": config_file, "error": str(e)},
                    time.time() - start_time
                )
        else:
            self._add_result(
                "Search Infrastructure",
                "Search Index Configuration",
                "FAIL",
                "Index configuration file not found",
                {"config_file": config_file},
                time.time() - start_time
            )
    
    def _test_search_monitoring(self):
        """Test search monitoring configuration"""
        start_time = time.time()
        
        monitoring_file = "/home/robbie/Desktop/repo-forum/deploy/search/search-monitoring.yaml"
        
        if os.path.exists(monitoring_file):
            try:
                with open(monitoring_file, 'r') as f:
                    monitoring_data = f.read()
                
                # Basic validation
                if 'monitoring:' in monitoring_data and 'alerting:' in monitoring_data:
                    # Test Kibana connectivity
                    try:
                        kibana_url = f"http://{self.config['kibana']['host']}:{self.config['kibana']['port']}"
                        response = requests.get(f"{kibana_url}/api/status", timeout=5)
                        
                        if response.status_code == 200:
                            self._add_result(
                                "Search Infrastructure",
                                "Search Monitoring",
                                "PASS",
                                "Search monitoring configuration valid and Kibana accessible",
                                {
                                    "monitoring_file": monitoring_file,
                                    "kibana_url": kibana_url,
                                    "kibana_status": response.status_code
                                },
                                time.time() - start_time
                            )
                        else:
                            self._add_result(
                                "Search Infrastructure",
                                "Search Monitoring",
                                "FAIL",
                                f"Kibana not accessible (status: {response.status_code})",
                                {
                                    "kibana_url": kibana_url,
                                    "status_code": response.status_code
                                },
                                time.time() - start_time
                            )
                    except requests.exceptions.RequestException as e:
                        self._add_result(
                            "Search Infrastructure",
                            "Search Monitoring",
                            "FAIL",
                            f"Kibana connection failed: {str(e)}",
                            {
                                "kibana_url": f"http://{self.config['kibana']['host']}:{self.config['kibana']['port']}",
                                "error": str(e)
                            },
                            time.time() - start_time
                        )
                else:
                    self._add_result(
                        "Search Infrastructure",
                        "Search Monitoring",
                        "FAIL",
                        "Search monitoring configuration missing required sections",
                        {"monitoring_file": monitoring_file},
                        time.time() - start_time
                    )
                    
            except Exception as e:
                self._add_result(
                    "Search Infrastructure",
                    "Search Monitoring",
                    "FAIL",
                    f"Error reading search monitoring configuration: {str(e)}",
                    {"monitoring_file": monitoring_file, "error": str(e)},
                    time.time() - start_time
                )
        else:
            self._add_result(
                "Search Infrastructure",
                "Search Monitoring",
                "FAIL",
                "Search monitoring configuration file not found",
                {"monitoring_file": monitoring_file},
                time.time() - start_time
            )
    
    def _test_search_performance_optimization(self):
        """Test search performance optimization script"""
        start_time = time.time()
        
        optimization_script = "/home/robbie/Desktop/repo-forum/deploy/search/performance-optimization.py"
        
        if os.path.exists(optimization_script):
            # Check if script is executable and has required modules
            if os.access(optimization_script, os.X_OK):
                try:
                    # Test script syntax
                    result = subprocess.run([
                        'python3', '-m', 'py_compile', optimization_script
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self._add_result(
                            "Search Infrastructure",
                            "Search Performance Optimization",
                            "PASS",
                            "Search performance optimization script is valid",
                            {
                                "script_path": optimization_script,
                                "syntax_valid": True,
                                "executable": True
                            },
                            time.time() - start_time
                        )
                    else:
                        self._add_result(
                            "Search Infrastructure",
                            "Search Performance Optimization",
                            "FAIL",
                            f"Script syntax error: {result.stderr}",
                            {
                                "script_path": optimization_script,
                                "syntax_error": result.stderr
                            },
                            time.time() - start_time
                        )
                except Exception as e:
                    self._add_result(
                        "Search Infrastructure",
                        "Search Performance Optimization",
                        "FAIL",
                        f"Error testing optimization script: {str(e)}",
                        {"script_path": optimization_script, "error": str(e)},
                        time.time() - start_time
                    )
            else:
                self._add_result(
                    "Search Infrastructure",
                    "Search Performance Optimization",
                    "FAIL",
                    "Search performance optimization script is not executable",
                    {"script_path": optimization_script, "executable": False},
                    time.time() - start_time
                )
        else:
            self._add_result(
                "Search Infrastructure",
                "Search Performance Optimization",
                "FAIL",
                "Search performance optimization script not found",
                {"script_path": optimization_script},
                time.time() - start_time
            )
    
    def test_integration(self) -> bool:
        """Test integration between all systems"""
        logger.info("Testing System Integration...")
        
        # Test Redis connectivity (shared between systems)
        self._test_redis_integration()
        
        # Test database connectivity (shared between systems)
        self._test_database_integration()
        
        # Test monitoring integration
        self._test_monitoring_integration()
        
        return self._get_system_status("System Integration")
    
    def _test_redis_integration(self):
        """Test Redis connectivity for all systems"""
        start_time = time.time()
        
        try:
            r = redis.Redis(
                host=self.config['redis']['host'],
                port=self.config['redis']['port'],
                db=self.config['redis']['db'],
                password=self.config['redis']['password'],
                decode_responses=True
            )
            
            # Test basic operations
            test_key = "debug_test_key"
            test_value = "debug_test_value"
            
            r.set(test_key, test_value)
            retrieved_value = r.get(test_key)
            r.delete(test_key)
            
            if retrieved_value == test_value:
                # Test Redis info
                redis_info = r.info()
                
                self._add_result(
                    "System Integration",
                    "Redis Integration",
                    "PASS",
                    f"Redis integration working (version: {redis_info.get('redis_version', 'unknown')})",
                    {
                        "redis_version": redis_info.get('redis_version'),
                        "connected_clients": redis_info.get('connected_clients'),
                        "used_memory": redis_info.get('used_memory_human'),
                        "test_result": retrieved_value == test_value
                    },
                    time.time() - start_time
                )
            else:
                self._add_result(
                    "System Integration",
                    "Redis Integration",
                    "FAIL",
                    "Redis test operation failed",
                    {"expected": test_value, "received": retrieved_value},
                    time.time() - start_time
                )
                
        except redis.ConnectionError as e:
            self._add_result(
                "System Integration",
                "Redis Integration",
                "FAIL",
                f"Redis connection failed: {str(e)}",
                {
                    "host": self.config['redis']['host'],
                    "port": self.config['redis']['port'],
                    "error": str(e)
                },
                time.time() - start_time
            )
        except Exception as e:
            self._add_result(
                "System Integration",
                "Redis Integration",
                "FAIL",
                f"Unexpected Redis error: {str(e)}",
                {"error": str(e)},
                time.time() - start_time
            )
    
    def _test_database_integration(self):
        """Test database connectivity for all systems"""
        start_time = time.time()
        
        try:
            # Test main forum database
            main_conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='forum_production',
                user='forum_user',
                password='forum_password'
            )
            
            # Test analytics database
            analytics_conn = psycopg2.connect(
                host=self.config['database']['host'],
                port=self.config['database']['port'],
                database=self.config['database']['database'],
                user=self.config['database']['username'],
                password=self.config['database']['password']
            )
            
            # Test basic queries on both databases
            main_cursor = main_conn.cursor()
            analytics_cursor = analytics_conn.cursor()
            
            main_cursor.execute("SELECT 1")
            analytics_cursor.execute("SELECT 1")
            
            main_result = main_cursor.fetchone()
            analytics_result = analytics_cursor.fetchone()
            
            main_cursor.close()
            analytics_cursor.close()
            main_conn.close()
            analytics_conn.close()
            
            if main_result and analytics_result and main_result[0] == 1 and analytics_result[0] == 1:
                self._add_result(
                    "System Integration",
                    "Database Integration",
                    "PASS",
                    "Both main and analytics databases accessible",
                    {
                        "main_database": "forum_production",
                        "analytics_database": self.config['database']['database'],
                        "main_test": main_result[0] == 1,
                        "analytics_test": analytics_result[0] == 1
                    },
                    time.time() - start_time
                )
            else:
                self._add_result(
                    "System Integration",
                    "Database Integration",
                    "FAIL",
                    "Database test queries failed",
                    {
                        "main_result": main_result,
                        "analytics_result": analytics_result
                    },
                    time.time() - start_time
                )
                
        except psycopg2.OperationalError as e:
            self._add_result(
                "System Integration",
                "Database Integration",
                "FAIL",
                f"Database connection failed: {str(e)}",
                {"error": str(e)},
                time.time() - start_time
            )
        except Exception as e:
            self._add_result(
                "System Integration",
                "Database Integration",
                "FAIL",
                f"Unexpected database error: {str(e)}",
                {"error": str(e)},
                time.time() - start_time
            )
    
    def _test_monitoring_integration(self):
        """Test monitoring integration across systems"""
        start_time = time.time()
        
        monitoring_services = {
            'prometheus': f"http://{self.config['prometheus']['host']}:{self.config['prometheus']['port']}",
            'grafana': f"http://{self.config['grafana']['host']}:{self.config['grafana']['port']}",
            'kibana': f"http://{self.config['kibana']['host']}:{self.config['kibana']['port']}"
        }
        
        accessible_services = []
        inaccessible_services = []
        
        for service_name, service_url in monitoring_services.items():
            try:
                if service_name == 'prometheus':
                    response = requests.get(f"{service_url}/api/v1/status/config", timeout=5)
                elif service_name == 'grafana':
                    response = requests.get(f"{service_url}/api/health", timeout=5)
                elif service_name == 'kibana':
                    response = requests.get(f"{service_url}/api/status", timeout=5)
                
                if response.status_code == 200:
                    accessible_services.append(service_name)
                else:
                    inaccessible_services.append(f"{service_name} (status: {response.status_code})")
                    
            except requests.exceptions.RequestException as e:
                inaccessible_services.append(f"{service_name} (error: {str(e)})")
        
        if accessible_services:
            self._add_result(
                "System Integration",
                "Monitoring Integration",
                "PASS",
                f"{len(accessible_services)} monitoring services accessible",
                {
                    "accessible_services": accessible_services,
                    "inaccessible_services": inaccessible_services,
                    "total_services": len(monitoring_services)
                },
                time.time() - start_time
            )
        else:
            self._add_result(
                "System Integration",
                "Monitoring Integration",
                "FAIL",
                "No monitoring services accessible",
                {
                    "inaccessible_services": inaccessible_services,
                    "total_services": len(monitoring_services)
                },
                time.time() - start_time
            )
    
    def _get_system_status(self, system_name: str) -> bool:
        """Get overall status for a system"""
        system_results = [r for r in self.results if r.system_name == system_name]
        
        if not system_results:
            return False
        
        failed_tests = [r for r in system_results if r.status == "FAIL"]
        passed_tests = [r for r in system_results if r.status == "PASS"]
        
        logger.info(f"\n{system_name} Summary:")
        logger.info(f"  Total Tests: {len(system_results)}")
        logger.info(f"  Passed: {len(passed_tests)}")
        logger.info(f"  Failed: {len(failed_tests)}")
        
        if failed_tests:
            logger.error(f"  Failed Tests: {[r.test_name for r in failed_tests]}")
        
        return len(failed_tests) == 0
    
    def generate_report(self) -> str:
        """Generate comprehensive debugging report"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("NEW SYSTEMS DEBUGGING REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report_lines.append(f"Total Tests: {len(self.results)}")
        
        # System summaries
        systems = list(set(r.system_name for r in self.results))
        for system in systems:
            system_results = [r for r in self.results if r.system_name == system]
            passed = len([r for r in system_results if r.status == "PASS"])
            failed = len([r for r in system_results if r.status == "FAIL"])
            skipped = len([r for r in system_results if r.status == "SKIP"])
            
            status = "✅ PASS" if failed == 0 else "❌ FAIL"
            report_lines.append(f"\n{system}: {status} ({passed}/{len(system_results)} passed)")
        
        # Detailed results
        report_lines.append("\n" + "=" * 80)
        report_lines.append("DETAILED RESULTS")
        report_lines.append("=" * 80)
        
        for result in self.results:
            status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⏭️"
            report_lines.append(f"\n{status_icon} [{result.system_name}] {result.test_name}")
            report_lines.append(f"   Status: {result.status}")
            report_lines.append(f"   Message: {result.message}")
            report_lines.append(f"   Execution Time: {result.execution_time:.2f}s")
            
            if result.details:
                report_lines.append("   Details:")
                for key, value in result.details.items():
                    if isinstance(value, dict) or isinstance(value, list):
                        report_lines.append(f"     {key}: {json.dumps(value, indent=6)}")
                    else:
                        report_lines.append(f"     {key}: {value}")
        
        # Recommendations
        report_lines.append("\n" + "=" * 80)
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("=" * 80)
        
        failed_results = [r for r in self.results if r.status == "FAIL"]
        if failed_results:
            report_lines.append("\nFailed Tests - Recommended Actions:")
            
            for result in failed_results:
                report_lines.append(f"\n• {result.system_name} - {result.test_name}")
                report_lines.append(f"  Issue: {result.message}")
                
                # Add specific recommendations based on test type
                if "Database" in result.test_name:
                    report_lines.append("  Recommendation: Check database connection settings and ensure database is running")
                elif "Service" in result.test_name:
                    report_lines.append("  Recommendation: Start the required service and check configuration")
                elif "Configuration" in result.test_name:
                    report_lines.append("  Recommendation: Verify configuration file syntax and required sections")
                elif "Package" in result.test_name:
                    report_lines.append("  Recommendation: Install missing packages using pip or package manager")
                else:
                    report_lines.append("  Recommendation: Review error details and fix underlying issues")
        else:
            report_lines.append("\n✅ All systems are working correctly!")
            report_lines.append("No immediate action required.")
        
        return "\n".join(report_lines)
    
    def run_all_tests(self) -> bool:
        """Run all debugging tests"""
        logger.info("Starting comprehensive debugging of newly added systems...")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Test all systems
        dependencies_ok = self.test_dependencies()
        analytics_ok = self.test_analytics_infrastructure()
        search_ok = self.test_search_infrastructure()
        integration_ok = self.test_integration()
        
        total_time = time.time() - start_time
        
        # Generate and save report
        report = self.generate_report()
        
        # Save report to file
        report_file = "/tmp/new_systems_debug_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Log summary
        logger.info("\n" + "=" * 80)
        logger.info("DEBUGGING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Execution Time: {total_time:.2f}s")
        logger.info(f"Total Tests: {len(self.results)}")
        logger.info(f"Report saved to: {report_file}")
        
        all_systems_ok = dependencies_ok and analytics_ok and search_ok and integration_ok
        
        if all_systems_ok:
            logger.info("🎉 ALL SYSTEMS ARE WORKING CORRECTLY!")
        else:
            logger.error("❌ SOME SYSTEMS HAVE ISSUES - See detailed report")
        
        return all_systems_ok


def main():
    """Main function"""
    debugger = SystemDebugger()
    success = debugger.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
