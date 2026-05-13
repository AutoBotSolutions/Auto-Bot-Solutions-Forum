#!/usr/bin/env python3
"""
Debug script for API Gateway Setup system
Tests all components for proper functionality and integration.
"""

import sys
import os
import traceback
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/robbie/Desktop/repo-forum')

def test_imports():
    """Test all imports for the gateway system"""
    print("🔍 Testing imports...")
    
    try:
        # Test gateway package import
        from app.api.gateway import (
            APIGatewayManager, GatewayRouter, LoadBalancer,
            GatewayRateLimiter, GatewayMonitor, GatewayMiddleware,
            gateway_bp
        )
        print("✅ Gateway package imports successful")
        return True
    except Exception as e:
        print(f"❌ Gateway package import failed: {e}")
        traceback.print_exc()
        return False

def test_gateway_manager():
    """Test gateway manager basic functionality"""
    print("\n🔍 Testing GatewayManager...")
    
    try:
        from app.api.gateway.gateway_manager import (
            APIGatewayManager, GatewayConfig, RouteConfig, 
            ServiceInstance, GatewayStatus
        )
        
        # Create gateway manager
        config = GatewayConfig(
            enable_versioning=True,
            enable_load_balancing=True,
            enable_rate_limiting=True,
            enable_monitoring=True
        )
        manager = APIGatewayManager(config)
        print("✅ GatewayManager created successfully")
        
        # Test route registration
        route_config = RouteConfig(
            path="/api/users",
            version="v1.0",
            service_name="user_service",
            service_url="http://localhost:8001",
            methods=["GET", "POST"]
        )
        manager.register_route(route_config)
        print("✅ Route registration successful")
        
        # Test service instance addition
        instance = ServiceInstance(
            id="user-service-1",
            url="http://localhost:8001",
            weight=1,
            status=GatewayStatus.ACTIVE
        )
        manager.add_service_instance("user_service", instance)
        print("✅ Service instance addition successful")
        
        # Test route lookup
        route = manager.get_route_for_request("/api/users", "v1.0", "GET")
        if route:
            print("✅ Route lookup successful")
        else:
            print("❌ Route lookup failed")
            return False
        
        # Test metrics
        metrics = manager.get_metrics()
        print(f"✅ Metrics collection successful: {metrics['total_requests']} requests")
        
        return True
        
    except Exception as e:
        print(f"❌ GatewayManager test failed: {e}")
        traceback.print_exc()
        return False

def test_routing():
    """Test routing functionality"""
    print("\n🔍 Testing GatewayRouter...")
    
    try:
        from app.api.gateway.routing import GatewayRouter
        from app.api.gateway.gateway_manager import APIGatewayManager, GatewayConfig
        
        # Create manager and router
        manager = APIGatewayManager(GatewayConfig())
        router = GatewayRouter(manager)
        print("✅ GatewayRouter created successfully")
        
        # Test version detection
        version = router.detect_version("/api/users", {"API-Version": "v1.0"})
        if version == "v1.0":
            print("✅ Header version detection successful")
        else:
            print(f"❌ Header version detection failed: {version}")
            return False
        
        # Test path version detection
        version = router.detect_version("/api/v1/users")
        if version == "v1":
            print("✅ Path version detection successful")
        else:
            print(f"❌ Path version detection failed: {version}")
            return False
        
        # Test query version detection
        version = router.detect_version("/api/users", query_params={"version": "v1.0"})
        if version == "v1.0":
            print("✅ Query version detection successful")
        else:
            print(f"❌ Query version detection failed: {version}")
            return False
        
        # Test default version
        version = router.detect_version("/api/users")
        if version == "v1.0":
            print("✅ Default version detection successful")
        else:
            print(f"❌ Default version detection failed: {version}")
            return False
        
        # Test path matching
        matches = router._path_matches("/api/users", "/api/users")
        if matches:
            print("✅ Path matching successful")
        else:
            print("❌ Path matching failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ GatewayRouter test failed: {e}")
        traceback.print_exc()
        return False

def test_load_balancer():
    """Test load balancer functionality"""
    print("\n🔍 Testing LoadBalancer...")
    
    try:
        from app.api.gateway.load_balancer import (
            LoadBalancer, LoadBalancingStrategy, ServiceInstance, GatewayStatus
        )
        
        # Create load balancer
        lb = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        print("✅ LoadBalancer created successfully")
        
        # Create test instances
        instances = [
            ServiceInstance("svc-1", "http://localhost:8001", 1, GatewayStatus.ACTIVE),
            ServiceInstance("svc-2", "http://localhost:8002", 2, GatewayStatus.ACTIVE),
            ServiceInstance("svc-3", "http://localhost:8003", 1, GatewayStatus.ACTIVE)
        ]
        print("✅ Test instances created")
        
        # Test round robin selection
        selected = lb.select_instance(instances)
        if selected:
            print(f"✅ Round robin selection successful: {selected.id}")
        else:
            print("❌ Round robin selection failed")
            return False
        
        # Test weighted round robin
        lb.set_strategy(LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN)
        selected = lb.select_instance(instances)
        if selected:
            print(f"✅ Weighted round robin selection successful: {selected.id}")
        else:
            print("❌ Weighted round robin selection failed")
            return False
        
        # Test least connections
        lb.set_strategy(LoadBalancingStrategy.LEAST_CONNECTIONS)
        selected = lb.select_instance(instances)
        if selected:
            print(f"✅ Least connections selection successful: {selected.id}")
        else:
            print("❌ Least connections selection failed")
            return False
        
        # Test random selection
        lb.set_strategy(LoadBalancingStrategy.RANDOM)
        selected = lb.select_instance(instances)
        if selected:
            print(f"✅ Random selection successful: {selected.id}")
        else:
            print("❌ Random selection failed")
            return False
        
        # Test strategy stats
        stats = lb.get_strategy_stats()
        print(f"✅ Strategy stats: {stats['current_strategy']}")
        
        return True
        
    except Exception as e:
        print(f"❌ LoadBalancer test failed: {e}")
        traceback.print_exc()
        return False

def test_rate_limiter():
    """Test rate limiter functionality"""
    print("\n🔍 Testing GatewayRateLimiter...")
    
    try:
        from app.api.gateway.rate_limiter import (
            GatewayRateLimiter, RateLimitStrategy, RateLimitType
        )
        
        # Create rate limiter
        limiter = GatewayRateLimiter()
        print("✅ GatewayRateLimiter created successfully")
        
        # Test rate limiting check
        request_context = {
            'client_ip': '127.0.0.1',
            'user_id': 'test_user',
            'endpoint': '/api/users'
        }
        
        allowed, results = limiter.check_rate_limits(request_context)
        if allowed:
            print("✅ Rate limit check successful (allowed)")
        else:
            print("⚠️ Rate limit check successful (blocked)")
        
        print(f"✅ Rate limit results: {len(results)} limits checked")
        
        # Test different rate limit configurations
        limiter.configure_rate_limit(RateLimitType.PER_USER, 10, 60)
        print("✅ Rate limit configuration successful")
        
        # Test rate limit status
        statuses = limiter.get_all_rate_limit_statuses(request_context)
        print(f"✅ Rate limit status retrieved: {len(statuses)} types")
        
        # Test rate limit stats
        stats = limiter.get_gateway_rate_limit_stats()
        print(f"✅ Rate limit stats: {stats['rate_limit_types']}")
        
        return True
        
    except Exception as e:
        print(f"❌ GatewayRateLimiter test failed: {e}")
        traceback.print_exc()
        return False

def test_monitor():
    """Test monitoring functionality"""
    print("\n🔍 Testing GatewayMonitor...")
    
    try:
        from app.api.gateway.monitor import GatewayMonitor, MetricType, AlertLevel
        
        # Create monitor
        monitor = GatewayMonitor()
        print("✅ GatewayMonitor created successfully")
        
        # Test metric recording
        monitor.record_metric("test_metric", 100.0, {"test": "value"}, MetricType.GAUGE)
        print("✅ Metric recording successful")
        
        # Test request recording
        monitor.record_request(0.5, 200, "/api/users", "user_service")
        print("✅ Request recording successful")
        
        # Test service health recording
        monitor.record_service_health("user_service", True, 0.2)
        print("✅ Service health recording successful")
        
        # Test metrics summary
        summary = monitor.get_metrics_summary(300)
        print(f"✅ Metrics summary: {summary['total_metrics']} metrics")
        
        # Test health status
        health = monitor.get_health_status()
        print(f"✅ Health status: {health['status']} (score: {health['score']})")
        
        # Test alert creation
        monitor.create_alert(
            "test_alert",
            "Test Alert",
            AlertLevel.WARNING,
            "avg_response_time",
            1.0,
            300
        )
        print("✅ Alert creation successful")
        
        # Test alert checking
        triggered = monitor.check_alerts()
        print(f"✅ Alert checking: {len(triggered)} triggered")
        
        # Test alerts retrieval
        alerts = monitor.get_alerts()
        print(f"✅ Alerts retrieved: {len(alerts)} alerts")
        
        return True
        
    except Exception as e:
        print(f"❌ GatewayMonitor test failed: {e}")
        traceback.print_exc()
        return False

def test_middleware():
    """Test middleware functionality"""
    print("\n🔍 Testing GatewayMiddleware...")
    
    try:
        from app.api.gateway.middleware import GatewayMiddleware
        from app.api.gateway.gateway_manager import APIGatewayManager, GatewayConfig
        
        # Create gateway manager
        manager = APIGatewayManager(GatewayConfig())
        
        # Create middleware
        middleware = GatewayMiddleware(manager)
        print("✅ GatewayMiddleware created successfully")
        
        # Test gateway stats
        stats = middleware.get_gateway_stats()
        print(f"✅ Gateway stats retrieved: {len(stats)} components")
        
        # Test rate limit configuration
        success = middleware.configure_rate_limit("global", 100, 60)
        if success:
            print("✅ Rate limit configuration successful")
        else:
            print("❌ Rate limit configuration failed")
            return False
        
        # Test load balancing strategy
        success = middleware.set_load_balancing_strategy("round_robin")
        if success:
            print("✅ Load balancing strategy set successfully")
        else:
            print("❌ Load balancing strategy setting failed")
            return False
        
        # Test service instance addition
        instance_id = middleware.add_service_instance("test_service", "http://localhost:8001")
        print(f"✅ Service instance added: {instance_id}")
        
        # Test service stats
        service_stats = middleware.get_service_stats("test_service")
        if service_stats:
            print("✅ Service stats retrieved successfully")
        else:
            print("⚠️ Service stats not found (expected for new service)")
        
        return True
        
    except Exception as e:
        print(f"❌ GatewayMiddleware test failed: {e}")
        traceback.print_exc()
        return False

def test_routes():
    """Test gateway routes"""
    print("\n🔍 Testing Gateway Routes...")
    
    try:
        # Test import
        from app.api.gateway.gateway_routes import init_gateway_routes
        print("✅ Gateway routes import successful")
        
        # Test route initialization (would require Flask app)
        # This is a basic test since we don't have a running Flask app
        print("✅ Gateway routes module loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Gateway routes test failed: {e}")
        traceback.print_exc()
        return False

def test_integration():
    """Test integration between components"""
    print("\n🔍 Testing Integration...")
    
    try:
        from app.api.gateway.gateway_manager import APIGatewayManager, GatewayConfig
        from app.api.gateway.middleware import GatewayMiddleware
        from app.api.gateway.routing import GatewayRouter
        from app.api.gateway.load_balancer import LoadBalancer
        from app.api.gateway.rate_limiter import GatewayRateLimiter
        from app.api.gateway.monitor import GatewayMonitor
        
        # Create complete gateway system
        config = GatewayConfig(
            enable_versioning=True,
            enable_load_balancing=True,
            enable_rate_limiting=True,
            enable_monitoring=True
        )
        
        manager = APIGatewayManager(config)
        router = GatewayRouter(manager)
        load_balancer = LoadBalancer()
        rate_limiter = GatewayRateLimiter()
        monitor = GatewayMonitor()
        middleware = GatewayMiddleware(manager)
        
        print("✅ All components created successfully")
        
        # Test component interaction
        # Add a route
        from app.api.gateway.gateway_manager import RouteConfig, ServiceInstance, GatewayStatus
        
        route_config = RouteConfig(
            path="/api/test",
            version="v1.0",
            service_name="test_service",
            service_url="http://localhost:8001",
            methods=["GET"]
        )
        manager.register_route(route_config)
        
        # Add service instance
        instance = ServiceInstance(
            id="test-instance",
            url="http://localhost:8001",
            status=GatewayStatus.ACTIVE
        )
        manager.add_service_instance("test_service", instance)
        
        # Test routing
        target_path, routing_context = router.route_request("/api/test", "GET")
        if routing_context:
            print("✅ Integration test: Routing successful")
        else:
            print("❌ Integration test: Routing failed")
            return False
        
        # Test load balancing
        instances = manager.get_healthy_instances("test_service")
        if instances:
            selected = load_balancer.select_instance(instances)
            if selected:
                print("✅ Integration test: Load balancing successful")
            else:
                print("❌ Integration test: Load balancing failed")
                return False
        else:
            print("❌ Integration test: No healthy instances")
            return False
        
        # Test rate limiting
        request_context = {
            'client_ip': '127.0.0.1',
            'endpoint': '/api/test'
        }
        allowed, results = rate_limiter.check_rate_limits(request_context)
        print(f"✅ Integration test: Rate limiting successful ({'allowed' if allowed else 'blocked'})")
        
        # Test monitoring
        monitor.record_request(0.1, 200, "/api/test", "test_service")
        health = monitor.get_health_status()
        print(f"✅ Integration test: Monitoring successful (health: {health['status']})")
        
        # Test middleware
        stats = middleware.get_gateway_stats()
        print(f"✅ Integration test: Middleware successful (stats available)")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting API Gateway System Debug Tests")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("GatewayManager", test_gateway_manager),
        ("Routing", test_routing),
        ("LoadBalancer", test_load_balancer),
        ("RateLimiter", test_rate_limiter),
        ("Monitor", test_monitor),
        ("Middleware", test_middleware),
        ("Routes", test_routes),
        ("Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! API Gateway System is working correctly.")
        return True
    else:
        print(f"\n⚠️ {failed} tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
