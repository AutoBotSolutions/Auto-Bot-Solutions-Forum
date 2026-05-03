"""
Test Configuration Management for Repo-Forum Project
Provides flexible test configuration and environment management.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict

@dataclass
class TestDatabaseConfig:
    """Database configuration for testing"""
    url: str = "sqlite:///:memory:"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600

@dataclass
class TestSecurityConfig:
    """Security configuration for testing"""
    secret_key: str = "test-secret-key-change-in-production"
    csrf_enabled: bool = True
    csrf_time_limit: int = 3600
    session_secure: bool = False
    session_httponly: bool = True
    session_samesite: str = "Lax"
    password_hash_rounds: int = 12

@dataclass
class TestPerformanceConfig:
    """Performance configuration for testing"""
    slow_test_threshold: float = 1.0
    very_slow_test_threshold: float = 5.0
    memory_limit_mb: int = 512
    timeout_seconds: int = 300
    parallel_workers: int = 4
    enable_profiling: bool = False

@dataclass
class TestReportingConfig:
    """Reporting configuration for testing"""
    output_format: str = "json"
    generate_html: bool = True
    generate_coverage: bool = False
    include_performance: bool = True
    save_screenshots: bool = False
    max_report_history: int = 10

@dataclass
class TestIntegrationConfig:
    """Integration testing configuration"""
    api_timeout: int = 30
    external_services: Dict[str, str] = None
    mock_external_apis: bool = True
    test_real_apis: bool = False
    api_rate_limit: int = 100

@dataclass
class TestConfig:
    """Main test configuration"""
    database: TestDatabaseConfig = TestDatabaseConfig()
    security: TestSecurityConfig = TestSecurityConfig()
    performance: TestPerformanceConfig = TestPerformanceConfig()
    reporting: TestReportingConfig = TestReportingConfig()
    integration: TestIntegrationConfig = TestIntegrationConfig()
    
    # General settings
    debug: bool = False
    verbose: bool = True
    fail_fast: bool = False
    random_seed: int = 42
    test_data_cleanup: bool = True
    use_isolated_database: bool = False

class TestConfigManager:
    """Manages test configuration loading and validation"""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        self.config_file = Path(config_file) if config_file else None
        self.config = TestConfig()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file and environment variables"""
        # Load from file if exists
        if self.config_file and self.config_file.exists():
            self._load_from_file()
        
        # Override with environment variables
        self._load_from_environment()
        
        # Validate configuration
        self._validate_config()
    
    def _load_from_file(self):
        """Load configuration from file (JSON or YAML)"""
        try:
            with open(self.config_file, 'r') as f:
                if self.config_file.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            # Update configuration with loaded data
            self._update_config(data)
            
        except Exception as e:
            print(f"Warning: Could not load config file {self.config_file}: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'TEST_DATABASE_URL': ('database.url', str),
            'TEST_DATABASE_ECHO': ('database.echo', bool),
            'TEST_SECRET_KEY': ('security.secret_key', str),
            'TEST_CSRF_ENABLED': ('security.csrf_enabled', bool),
            'TEST_DEBUG': ('debug', bool),
            'TEST_VERBOSE': ('verbose', bool),
            'TEST_FAIL_FAST': ('fail_fast', bool),
            'TEST_PARALLEL_WORKERS': ('performance.parallel_workers', int),
            'TEST_SLOW_THRESHOLD': ('performance.slow_test_threshold', float),
            'TEST_OUTPUT_FORMAT': ('reporting.output_format', str),
            'TEST_GENERATE_HTML': ('reporting.generate_html', bool),
            'TEST_USE_ISOLATED_DB': ('use_isolated_database', bool),
        }
        
        for env_var, (config_path, config_type) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_config_value(config_path, value, config_type)
    
    def _update_config(self, data: Dict[str, Any]):
        """Update configuration with data from file"""
        if 'database' in data:
            self._update_dataclass(self.config.database, data['database'])
        if 'security' in data:
            self._update_dataclass(self.config.security, data['security'])
        if 'performance' in data:
            self._update_dataclass(self.config.performance, data['performance'])
        if 'reporting' in data:
            self._update_dataclass(self.config.reporting, data['reporting'])
        if 'integration' in data:
            self._update_dataclass(self.config.integration, data['integration'])
        
        # Update general settings
        for key in ['debug', 'verbose', 'fail_fast', 'random_seed', 'test_data_cleanup', 'use_isolated_database']:
            if key in data:
                setattr(self.config, key, data[key])
    
    def _update_dataclass(self, target_obj: Any, data: Dict[str, Any]):
        """Update a dataclass with data from dictionary"""
        for key, value in data.items():
            if hasattr(target_obj, key):
                setattr(target_obj, key, value)
    
    def _set_config_value(self, config_path: str, value: str, config_type: type):
        """Set a configuration value from environment variable"""
        parts = config_path.split('.')
        obj = self.config
        
        # Navigate to the target object
        for part in parts[:-1]:
            obj = getattr(obj, part)
        
        # Set the value with type conversion
        final_key = parts[-1]
        if config_type == bool:
            value = value.lower() in ['true', '1', 'yes', 'on']
        elif config_type == int:
            value = int(value)
        elif config_type == float:
            value = float(value)
        
        setattr(obj, final_key, value)
    
    def _validate_config(self):
        """Validate configuration values"""
        # Validate database configuration
        if not self.config.database.url:
            raise ValueError("Database URL is required")
        
        # Validate security configuration
        if len(self.config.security.secret_key) < 16:
            print("Warning: Secret key should be at least 16 characters long")
        
        # Validate performance configuration
        if self.config.performance.parallel_workers < 1:
            self.config.performance.parallel_workers = 1
        
        if self.config.performance.slow_test_threshold <= 0:
            self.config.performance.slow_test_threshold = 1.0
        
        # Validate reporting configuration
        valid_formats = ['json', 'text', 'html']
        if self.config.reporting.output_format not in valid_formats:
            self.config.reporting.output_format = 'json'
    
    def get_config(self) -> TestConfig:
        """Get the current configuration"""
        return self.config
    
    def update_config(self, **kwargs):
        """Update configuration with keyword arguments"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                print(f"Warning: Unknown configuration key: {key}")
    
    def save_config(self, file_path: Optional[Union[str, Path]] = None):
        """Save current configuration to file"""
        save_path = Path(file_path) if file_path else self.config_file
        if not save_path:
            raise ValueError("No file path specified for saving configuration")
        
        # Convert configuration to dictionary
        config_dict = asdict(self.config)
        
        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(save_path, 'w') as f:
            if save_path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_dict, f, indent=2)
    
    def create_flask_config(self) -> Dict[str, Any]:
        """Create Flask configuration from test config"""
        flask_config = {
            # Database configuration
            'SQLALCHEMY_DATABASE_URI': self.config.database.url,
            'SQLALCHEMY_ECHO': self.config.database.echo,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_size': self.config.database.pool_size,
                'max_overflow': self.config.database.max_overflow,
                'pool_timeout': self.config.database.pool_timeout,
                'pool_recycle': self.config.database.pool_recycle,
            },
            
            # Security configuration
            'SECRET_KEY': self.config.security.secret_key,
            'WTF_CSRF_ENABLED': self.config.security.csrf_enabled,
            'WTF_CSRF_TIME_LIMIT': self.config.security.csrf_time_limit,
            'SESSION_COOKIE_SECURE': self.config.security.session_secure,
            'SESSION_COOKIE_HTTPONLY': self.config.security.session_httponly,
            'SESSION_COOKIE_SAMESITE': self.config.security.session_samesite,
            
            # Flask configuration
            'DEBUG': self.config.debug,
            'TESTING': True,
        }
        
        return flask_config
    
    def get_environment_overrides(self) -> Dict[str, str]:
        """Get environment variable overrides for current config"""
        overrides = {}
        
        # Database
        overrides['TEST_DATABASE_URL'] = self.config.database.url
        if self.config.database.echo:
            overrides['TEST_DATABASE_ECHO'] = 'true'
        
        # Security
        overrides['TEST_SECRET_KEY'] = self.config.security.secret_key
        if self.config.security.csrf_enabled:
            overrides['TEST_CSRF_ENABLED'] = 'true'
        
        # General
        if self.config.debug:
            overrides['TEST_DEBUG'] = 'true'
        if self.config.verbose:
            overrides['TEST_VERBOSE'] = 'true'
        if self.config.fail_fast:
            overrides['TEST_FAIL_FAST'] = 'true'
        
        return overrides

class TestEnvironmentManager:
    """Manages different test environments"""
    
    def __init__(self):
        self.environments = {
            'unit': TestConfig(
                database=TestDatabaseConfig(url="sqlite:///:memory:"),
                security=TestSecurityConfig(csrf_enabled=False),
                performance=TestPerformanceConfig(parallel_workers=1),
                reporting=TestReportingConfig(generate_html=False)
            ),
            'integration': TestConfig(
                database=TestDatabaseConfig(url="sqlite:///test_integration.db"),
                security=TestSecurityConfig(),
                performance=TestPerformanceConfig(parallel_workers=2),
                reporting=TestReportingConfig(generate_html=True)
            ),
            'performance': TestConfig(
                database=TestDatabaseConfig(url="sqlite:///test_perf.db"),
                security=TestSecurityConfig(),
                performance=TestPerformanceConfig(
                    enable_profiling=True,
                    parallel_workers=1
                ),
                reporting=TestReportingConfig(
                    include_performance=True,
                    generate_html=True
                )
            ),
            'ci': TestConfig(
                database=TestDatabaseConfig(url="sqlite:///:memory:"),
                security=TestSecurityConfig(),
                performance=TestPerformanceConfig(
                    parallel_workers=4,
                    fail_fast=True
                ),
                reporting=TestReportingConfig(
                    output_format="json",
                    generate_html=False
                ),
                verbose=False,
                debug=False
            )
        }
    
    def get_environment_config(self, environment: str) -> TestConfig:
        """Get configuration for a specific environment"""
        if environment not in self.environments:
            raise ValueError(f"Unknown environment: {environment}")
        
        return self.environments[environment]
    
    def list_environments(self) -> list:
        """List available environments"""
        return list(self.environments.keys())
    
    def add_environment(self, name: str, config: TestConfig):
        """Add a new environment"""
        self.environments[name] = config

# Global configuration manager
_config_manager = None

def get_config_manager(config_file: Optional[Union[str, Path]] = None) -> TestConfigManager:
    """Get or create the configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = TestConfigManager(config_file)
    return _config_manager

def get_test_config(environment: Optional[str] = None, 
                   config_file: Optional[Union[str, Path]] = None) -> TestConfig:
    """Get test configuration"""
    if environment:
        env_manager = TestEnvironmentManager()
        return env_manager.get_environment_config(environment)
    else:
        config_manager = get_config_manager(config_file)
        return config_manager.get_config()
