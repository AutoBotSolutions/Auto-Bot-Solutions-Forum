#!/usr/bin/env python3
"""
Mock Services for Testing
Auto Bot Solutions Forum

This script creates mock services to test the infrastructure configurations
when the actual services are not available.
"""

import os
import sys
import time
import json
import threading
import http.server
import socketserver
from datetime import datetime
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockService:
    """Base class for mock services"""
    
    def __init__(self, name: str, port: int):
        self.name = name
        self.port = port
        self.running = False
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the mock service"""
        if not self.running:
            self.thread = threading.Thread(target=self._run_server)
            self.thread.daemon = True
            self.thread.start()
            time.sleep(0.1)  # Give server time to start
            self.running = True
            logger.info(f"Mock {self.name} started on port {self.port}")
    
    def _run_server(self):
        """Run the HTTP server"""
        handler = self._get_handler()
        self.server = socketserver.TCPServer(("", self.port), handler)
        self.server.serve_forever()
    
    def _get_handler(self):
        """Get the HTTP request handler"""
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = self._get_response()
                self.wfile.write(json.dumps(response).encode())
            
            def _get_response(self):
                return {"status": "ok", "service": self.name}
        
        return Handler
    
    def stop(self):
        """Stop the mock service"""
        if self.running and self.server:
            self.server.shutdown()
            self.running = False
            logger.info(f"Mock {self.name} stopped")


class MockElasticsearch(MockService):
    """Mock Elasticsearch service"""
    
    def __init__(self):
        super().__init__("elasticsearch", 9200)
    
    def _get_handler(self):
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                if self.path == "/_cluster/health":
                    response = {
                        "cluster_name": "mock-cluster",
                        "status": "green",
                        "number_of_nodes": 1,
                        "number_of_data_nodes": 1,
                        "active_primary_shards": 0,
                        "active_shards": 0,
                        "relocating_shards": 0,
                        "initializing_shards": 0,
                        "unassigned_shards": 0,
                        "delayed_unassigned_shards": 0,
                        "number_of_pending_tasks": 0,
                        "number_of_in_flight_fetch": 0,
                        "task_max_waiting_in_queue_millis": 0,
                        "active_shards_percent_as_number": 100.0
                    }
                elif self.path == "/_cat/indices":
                    response = [
                        {"index": "forum_posts", "status": "open", "docs.count": 0},
                        {"index": "users", "status": "open", "docs.count": 0},
                        {"index": "forum_comments", "status": "open", "docs.count": 0}
                    ]
                else:
                    response = {"status": "ok", "service": "elasticsearch"}
                
                self.wfile.write(json.dumps(response).encode())
        
        return Handler


class MockKibana(MockService):
    """Mock Kibana service"""
    
    def __init__(self):
        super().__init__("kibana", 5601)
    
    def _get_handler(self):
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                if self.path == "/api/status":
                    response = {
                        "status": {
                            "overall": {
                                "state": "green",
                                "title": "Green",
                                "nickname": "Looking good",
                                "message": "All services are available"
                            }
                        }
                    }
                else:
                    response = {"status": "ok", "service": "kibana"}
                
                self.wfile.write(json.dumps(response).encode())
        
        return Handler


class MockPrometheus(MockService):
    """Mock Prometheus service"""
    
    def __init__(self):
        super().__init__("prometheus", 9090)
    
    def _get_handler(self):
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                if self.path == "/api/v1/status/config":
                    response = {
                        "status": "success",
                        "data": {
                            "yaml": {
                                "global": {
                                    "scrape_interval": "15s"
                                }
                            }
                        }
                    }
                elif self.path == "/-/healthy":
                    response = {"status": "success"}
                else:
                    response = {"status": "ok", "service": "prometheus"}
                
                self.wfile.write(json.dumps(response).encode())
        
        return Handler


class MockGrafana(MockService):
    """Mock Grafana service"""
    
    def __init__(self):
        super().__init__("grafana", 3000)
    
    def _get_handler(self):
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                if self.path == "/api/health":
                    response = {
                        "commit": "mock-commit",
                        "database": "ok",
                        "version": "9.0.0"
                    }
                else:
                    response = {"status": "ok", "service": "grafana"}
                
                self.wfile.write(json.dumps(response).encode())
        
        return Handler


class MockRedis:
    """Mock Redis service (simple key-value store)"""
    
    def __init__(self):
        self.data = {}
        self.running = False
    
    def start(self):
        """Start mock Redis"""
        self.running = True
        logger.info("Mock Redis started")
    
    def set(self, key: str, value: str):
        """Set a key-value pair"""
        if self.running:
            self.data[key] = value
            return True
        return False
    
    def get(self, key: str):
        """Get a value by key"""
        if self.running and key in self.data:
            return self.data[key]
        return None
    
    def delete(self, key: str):
        """Delete a key"""
        if self.running and key in self.data:
            del self.data[key]
            return True
        return False
    
    def ping(self):
        """Ping the Redis server"""
        return self.running
    
    def stop(self):
        """Stop mock Redis"""
        self.running = False
        self.data.clear()
        logger.info("Mock Redis stopped")


class MockDatabase:
    """Mock PostgreSQL database"""
    
    def __init__(self, name: str):
        self.name = name
        self.running = False
        self.schemas = {}
        self.tables = {}
    
    def start(self):
        """Start mock database"""
        self.running = True
        logger.info(f"Mock database '{self.name}' started")
    
    def create_schema(self, schema_name: str):
        """Create a schema"""
        if self.running:
            self.schemas[schema_name] = {}
            return True
        return False
    
    def create_table(self, schema_name: str, table_name: str, columns: Dict[str, str]):
        """Create a table"""
        if self.running and schema_name in self.schemas:
            self.schemas[schema_name][table_name] = columns
            return True
        return False
    
    def execute_query(self, query: str):
        """Execute a mock query"""
        if self.running:
            if "SELECT 1" in query:
                return [(1,)]
            elif "schema_name" in query:
                return [(schema,) for schema in self.schemas.keys()]
            elif "table_name" in query:
                tables = []
                for schema, schema_tables in self.schemas.items():
                    for table in schema_tables.keys():
                        tables.append((schema, table))
                return tables
        return []
    
    def stop(self):
        """Stop mock database"""
        self.running = False
        self.schemas.clear()
        self.tables.clear()
        logger.info(f"Mock database '{self.name}' stopped")


class MockServiceManager:
    """Manager for all mock services"""
    
    def __init__(self):
        self.elasticsearch = MockElasticsearch()
        self.kibana = MockKibana()
        self.prometheus = MockPrometheus()
        self.grafana = MockGrafana()
        self.redis = MockRedis()
        self.main_db = MockDatabase("forum_production")
        self.analytics_db = MockDatabase("forum_analytics")
        
        # Setup analytics database
        self.analytics_db.create_schema("analytics")
        self.analytics_db.create_schema("pipeline")
        self.analytics_db.create_schema("monitoring")
        
        # Setup main database
        self.main_db.create_schema("public")
    
    def start_all(self):
        """Start all mock services"""
        logger.info("Starting all mock services...")
        
        self.elasticsearch.start()
        self.kibana.start()
        self.prometheus.start()
        self.grafana.start()
        self.redis.start()
        self.main_db.start()
        self.analytics_db.start()
        
        logger.info("All mock services started")
    
    def stop_all(self):
        """Stop all mock services"""
        logger.info("Stopping all mock services...")
        
        self.elasticsearch.stop()
        self.kibana.stop()
        self.prometheus.stop()
        self.grafana.stop()
        self.redis.stop()
        self.main_db.stop()
        self.analytics_db.stop()
        
        logger.info("All mock services stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        return {
            "elasticsearch": {
                "running": self.elasticsearch.running,
                "port": self.elasticsearch.port
            },
            "kibana": {
                "running": self.kibana.running,
                "port": self.kibana.port
            },
            "prometheus": {
                "running": self.prometheus.running,
                "port": self.prometheus.port
            },
            "grafana": {
                "running": self.grafana.running,
                "port": self.grafana.port
            },
            "redis": {
                "running": self.redis.running
            },
            "main_database": {
                "running": self.main_db.running,
                "name": self.main_db.name
            },
            "analytics_database": {
                "running": self.analytics_db.running,
                "name": self.analytics_db.name
            }
        }


def main():
    """Main function to run mock services"""
    manager = MockServiceManager()
    
    try:
        manager.start_all()
        
        print("Mock services are running. Press Ctrl+C to stop.")
        print("Services available:")
        status = manager.get_status()
        for service, info in status.items():
            port = f" (port {info['port']})" if 'port' in info else ""
            print(f"  - {service}: {'✅ Running' if info['running'] else '❌ Stopped'}{port}")
        
        # Keep services running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping mock services...")
        manager.stop_all()
        print("All mock services stopped.")


if __name__ == "__main__":
    main()
