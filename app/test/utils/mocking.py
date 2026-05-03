"""
Mocking and Stubbing Utilities for Repo-Forum Project
Provides comprehensive mocking capabilities for testing.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from unittest.mock import Mock, MagicMock, patch
from functools import wraps
import requests
from flask import Flask

class MockResponse:
    """Mock HTTP response for API testing"""
    
    def __init__(self, json_data: Dict = None, status_code: int = 200, 
                 text: str = "", headers: Dict = None):
        self.json_data = json_data or {}
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self.content = text.encode('utf-8') if text else json.dumps(json_data).encode('utf-8')
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code} Error")

class APIMocker:
    """Mocks external API calls"""
    
    def __init__(self):
        self.responses = {}
        self.call_history = []
    
    def add_response(self, url: str, method: str = 'GET', response: MockResponse = None):
        """Add a mock response for a URL and method"""
        key = f"{method.upper()}:{url}"
        self.responses[key] = response
    
    def add_json_response(self, url: str, method: str = 'GET', 
                         json_data: Dict = None, status_code: int = 200):
        """Add a JSON response"""
        response = MockResponse(json_data=json_data, status_code=status_code)
        self.add_response(url, method, response)
    
    def add_error_response(self, url: str, method: str = 'GET', 
                          status_code: int = 500, text: str = "Internal Server Error"):
        """Add an error response"""
        response = MockResponse(status_code=status_code, text=text)
        self.add_response(url, method, response)
    
    def get_mock_session(self):
        """Get a mock requests session"""
        session = Mock()
        
        def request_method(method, url, **kwargs):
            key = f"{method.upper()}:{url}"
            
            # Record the call
            self.call_history.append({
                'method': method.upper(),
                'url': url,
                'kwargs': kwargs,
                'timestamp': datetime.utcnow()
            })
            
            # Return mock response or default
            if key in self.responses:
                return self.responses[key]
            else:
                return MockResponse(status_code=404, text="Not Found")
        
        session.get = lambda url, **kwargs: request_method('GET', url, **kwargs)
        session.post = lambda url, **kwargs: request_method('POST', url, **kwargs)
        session.put = lambda url, **kwargs: request_method('PUT', url, **kwargs)
        session.delete = lambda url, **kwargs: request_method('DELETE', url, **kwargs)
        
        return session
    
    def clear(self):
        """Clear all responses and history"""
        self.responses.clear()
        self.call_history.clear()
    
    def get_call_history(self) -> List[Dict]:
        """Get the call history"""
        return self.call_history.copy()

class DatabaseMocker:
    """Mocks database operations"""
    
    def __init__(self):
        self.data = {}
        self.queries = []
    
    def mock_query(self, model_class):
        """Create a mock query for a model class"""
        mock_query = Mock()
        
        def filter_by(**kwargs):
            self.queries.append(('filter_by', kwargs))
            return mock_query
        
        def filter(*args, **kwargs):
            self.queries.append(('filter', args, kwargs))
            return mock_query
        
        def all():
            return self._get_mock_data(model_class)
        
        def first():
            data = self._get_mock_data(model_class)
            return data[0] if data else None
        
        def count():
            return len(self._get_mock_data(model_class))
        
        mock_query.filter_by = filter_by
        mock_query.filter = filter
        mock_query.all = all
        mock_query.first = first
        mock_query.count = count
        
        return mock_query
    
    def add_mock_data(self, model_class, data: List[Dict]):
        """Add mock data for a model class"""
        model_name = model_class.__name__
        self.data[model_name] = data
    
    def _get_mock_data(self, model_class) -> List[Dict]:
        """Get mock data for a model class"""
        model_name = model_class.__name__
        return self.data.get(model_name, [])
    
    def get_query_history(self) -> List[tuple]:
        """Get the query history"""
        return self.queries.copy()
    
    def clear(self):
        """Clear all data and queries"""
        self.data.clear()
        self.queries.clear()

class EmailMocker:
    """Mocks email sending functionality"""
    
    def __init__(self):
        self.sent_emails = []
        self.fail_next_send = False
    
    def send_email(self, to: str, subject: str, body: str, **kwargs):
        """Mock email sending"""
        if self.fail_next_send:
            self.fail_next_send = False
            raise Exception("Email sending failed")
        
        email = {
            'to': to,
            'subject': subject,
            'body': body,
            'timestamp': datetime.utcnow(),
            **kwargs
        }
        self.sent_emails.append(email)
        return True
    
    def get_sent_emails(self) -> List[Dict]:
        """Get all sent emails"""
        return self.sent_emails.copy()
    
    def clear(self):
        """Clear sent emails"""
        self.sent_emails.clear()
        self.fail_next_send = False
    
    def fail_next_email(self):
        """Make the next email send fail"""
        self.fail_next_send = True

class FileMocker:
    """Mocks file operations"""
    
    def __init__(self):
        self.files = {}
        self.read_history = []
        self.write_history = []
    
    def mock_file_exists(self, file_path: str, exists: bool = True):
        """Mock file existence check"""
        def exists_check(path):
            self.read_history.append(('exists', path))
            return exists if path == file_path else os.path.exists(path)
        
        return exists_check
    
    def mock_file_read(self, file_path: str, content: str):
        """Mock file reading"""
        self.files[file_path] = content
        
        def read_file(path):
            self.read_history.append(('read', path))
            if path == file_path:
                return content
            else:
                # Try to read actual file
                try:
                    with open(path, 'r') as f:
                        return f.read()
                except FileNotFoundError:
                    raise FileNotFoundError(f"File not found: {path}")
        
        return read_file
    
    def mock_file_write(self, file_path: str):
        """Mock file writing"""
        def write_file(path, content):
            self.write_history.append(('write', path, content))
            if path == file_path:
                self.files[path] = content
            else:
                # Actually write to file
                with open(path, 'w') as f:
                    f.write(content)
        
        return write_file
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get mock file content"""
        return self.files.get(file_path)
    
    def get_read_history(self) -> List[tuple]:
        """Get read history"""
        return self.read_history.copy()
    
    def get_write_history(self) -> List[tuple]:
        """Get write history"""
        return self.write_history.copy()
    
    def clear(self):
        """Clear all mock data"""
        self.files.clear()
        self.read_history.clear()
        self.write_history.clear()

class TimeMocker:
    """Mocks time-based operations"""
    
    def __init__(self):
        self.current_time = datetime.utcnow()
        self.time_deltas = []
    
    def set_current_time(self, dt: datetime):
        """Set the current time"""
        self.current_time = dt
    
    def advance_time(self, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0):
        """Advance the current time"""
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        self.current_time += delta
        self.time_deltas.append(delta)
    
    def mock_datetime_now(self):
        """Mock datetime.now()"""
        def now():
            return self.current_time
        
        return now
    
    def mock_time_time(self):
        """Mock time.time()"""
        def time_func():
            return self.current_time.timestamp()
        
        return time_func
    
    def mock_time_sleep(self):
        """Mock time.sleep()"""
        def sleep_func(seconds):
            self.advance_time(seconds=seconds)
        
        return sleep_func

class MockManager:
    """Central manager for all mocks"""
    
    def __init__(self):
        self.api_mocker = APIMocker()
        self.db_mocker = DatabaseMocker()
        self.email_mocker = EmailMocker()
        self.file_mocker = FileMocker()
        self.time_mocker = TimeMocker()
        self.active_patches = []
    
    def setup_api_mocks(self):
        """Setup API mocking"""
        return patch('requests.Session', self.api_mocker.get_mock_session)
    
    def setup_db_mocks(self):
        """Setup database mocking"""
        # This would need to be adapted based on actual ORM usage
        return patch('app.models.User.query', self.db_mocker.mock_query)
    
    def setup_email_mocks(self):
        """Setup email mocking"""
        return patch('app.utils.email.send_email', self.email_mocker.send_email)
    
    def setup_file_mocks(self):
        """Setup file mocking"""
        return [
            patch('os.path.exists', self.file_mocker.mock_file_exists('/test/path')),
            patch('builtins.open', self.file_mocker.mock_file_read('/test/path', 'test content'))
        ]
    
    def setup_time_mocks(self):
        """Setup time mocking"""
        return [
            patch('datetime.datetime.now', self.time_mocker.mock_datetime_now()),
            patch('time.time', self.time_mocker.mock_time_time()),
            patch('time.sleep', self.time_mocker.mock_time_sleep())
        ]
    
    def start_all_mocks(self):
        """Start all mocks"""
        patches = []
        
        # API mocks
        patches.append(self.setup_api_mocks())
        
        # Email mocks
        patches.append(self.setup_email_mocks())
        
        # Time mocks
        patches.extend(self.setup_time_mocks())
        
        # Start all patches
        for patch_obj in patches:
            if patch_obj:
                self.active_patches.append(patch_obj.start())
    
    def stop_all_mocks(self):
        """Stop all active mocks"""
        for patch_obj in self.active_patches:
            try:
                patch_obj.stop()
            except Exception as e:
                print(f"Error stopping mock: {e}")
        
        self.active_patches.clear()
    
    def clear_all_mocks(self):
        """Clear all mock data"""
        self.api_mocker.clear()
        self.db_mocker.clear()
        self.email_mocker.clear()
        self.file_mocker.clear()
        self.time_mocker.time_deltas.clear()

def mock_external_api(url: str, response_data: Dict = None, status_code: int = 200):
    """Decorator to mock external API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mocker = APIMocker()
            mocker.add_json_response(url, 'GET', response_data, status_code)
            
            with patch('requests.Session', mocker.get_mock_session):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def mock_email_sending():
    """Decorator to mock email sending"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            email_mocker = EmailMocker()
            
            with patch('app.utils.email.send_email', email_mocker.send_email):
                result = func(*args, **kwargs)
                
                # You can access email_mocker.get_sent_emails() here if needed
                return result
        
        return wrapper
    return decorator

def mock_time_travel(days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0):
    """Decorator to mock time travel"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time_mocker = TimeMocker()
            
            with patch('datetime.datetime.now', time_mocker.mock_datetime_now()):
                time_mocker.advance_time(days, hours, minutes, seconds)
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Global mock manager instance
mock_manager = MockManager()

def get_mock_manager() -> MockManager:
    """Get the global mock manager"""
    return mock_manager

# Context manager for easy mock usage
class MockContext:
    """Context manager for using mocks"""
    
    def __init__(self, enable_api: bool = True, enable_email: bool = True, 
                 enable_time: bool = False, enable_file: bool = False):
        self.enable_api = enable_api
        self.enable_email = enable_email
        self.enable_time = enable_time
        self.enable_file = enable_file
        self.mock_manager = MockManager()
    
    def __enter__(self):
        if self.enable_api:
            self.mock_manager.setup_api_mocks().start()
        if self.enable_email:
            self.mock_manager.setup_email_mocks().start()
        if self.enable_time:
            for patch in self.mock_manager.setup_time_mocks():
                patch.start()
        if self.enable_file:
            for patch in self.mock_manager.setup_file_mocks():
                patch.start()
        
        return self.mock_manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mock_manager.stop_all_mocks()
        self.mock_manager.clear_all_mocks()
