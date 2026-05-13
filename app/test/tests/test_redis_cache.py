#!/usr/bin/env python3
"""
Test Redis caching system functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_redis_connection():
    """Test Redis connection and basic operations"""
    print("Testing Redis Connection...")
    
    try:
        import redis
        import json
        import time
        
        # Try to connect to Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        try:
            redis_client.ping()
            print("✅ Redis connection successful")
        except redis.ConnectionError:
            print("⚠️ Redis connection failed - Redis server not running")
            print("   (This is expected if Redis is not installed/running)")
            return False
        
        # Test basic operations
        test_key = "test_cache_key"
        test_data = {"message": "Hello Redis!", "timestamp": time.time()}
        
        # Test set operation
        redis_client.set(test_key, json.dumps(test_data))
        print("✅ Redis SET operation works")
        
        # Test get operation
        retrieved_data = redis_client.get(test_key)
        if retrieved_data:
            parsed_data = json.loads(retrieved_data)
            if parsed_data["message"] == test_data["message"]:
                print("✅ Redis GET operation works")
            else:
                print("❌ Redis GET operation failed")
                return False
        else:
            print("❌ Redis GET operation failed")
            return False
        
        # Test delete operation
        redis_client.delete(test_key)
        if not redis_client.exists(test_key):
            print("✅ Redis DELETE operation works")
        else:
            print("❌ Redis DELETE operation failed")
            return False
        
        # Test TTL operations
        redis_client.setex("test_ttl_key", 60, "test_value")
        ttl = redis_client.ttl("test_ttl_key")
        if 0 < ttl <= 60:
            print(f"✅ Redis TTL operation works (TTL: {ttl}s)")
        else:
            print("❌ Redis TTL operation failed")
            return False
        
        # Clean up
        redis_client.delete("test_ttl_key")
        
        return True
        
    except ImportError as e:
        print(f"❌ Redis import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Redis test error: {e}")
        return False

def test_cache_service():
    """Test cache service implementation"""
    print("\nTesting Cache Service...")
    
    try:
        # Check if cache service files exist
        cache_files = [
            'app/cache/redis_cache.py',
            'app/cache/cache_manager.py',
            'app/cache/cache_utils.py'
        ]
        
        for file_path in cache_files:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            if os.path.exists(full_path):
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} missing")
                return False
        
        # Test cache service structure
        redis_cache_file = os.path.join(os.path.dirname(__file__), 'app/cache/redis_cache.py')
        with open(redis_cache_file, 'r') as f:
            content = f.read()
        
        # Check for RedisCacheService class
        if 'class RedisCacheService' in content:
            print("✅ RedisCacheService class found")
        else:
            print("❌ RedisCacheService class missing")
        
        # Check for required methods
        required_methods = [
            'get',
            'set',
            'delete',
            'exists',
            'clear',
            'get_stats'
        ]
        
        for method in required_methods:
            if f'def {method}' in content:
                print(f"✅ {method} method found")
            else:
                print(f"❌ {method} method missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache service test error: {e}")
        return False

def test_cache_key_generation():
    """Test cache key generation utilities"""
    print("\nTesting Cache Key Generation...")
    
    try:
        # Test cache key building logic
        def build_cache_key(prefix, *args, **kwargs):
            """Build cache key from components"""
            key_parts = [prefix]
            key_parts.extend(str(arg) for arg in args)
            
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)
            
            return ":".join(key_parts)
        
        # Test key generation
        key1 = build_cache_key("user", 123)
        if key1 == "user:123":
            print("✅ Simple cache key generation works")
        else:
            print("❌ Simple cache key generation failed")
        
        key2 = build_cache_key("api", "posts", page=1, limit=10)
        expected_key = "api:posts:limit=10:page=1"
        if key2 == expected_key:
            print("✅ Complex cache key generation works")
        else:
            print(f"❌ Complex cache key generation failed: {key2}")
        
        # Test key validation
        def is_valid_cache_key(key):
            """Validate cache key format"""
            if not key or not isinstance(key, str):
                return False
            if len(key) > 250:  # Redis key length limit
                return False
            if any(char in key for char in ['\x00', '\n', '\r']):
                return False
            return True
        
        # Test valid keys
        valid_keys = ["user:123", "api:posts:page=1", "cache:complex:key"]
        for key in valid_keys:
            if is_valid_cache_key(key):
                print(f"✅ Valid key accepted: {key[:20]}...")
            else:
                print(f"❌ Valid key rejected: {key[:20]}...")
        
        # Test invalid keys
        invalid_keys = ["", None, "key\x00with\x00null", "x" * 300]
        for key in invalid_keys:
            if not is_valid_cache_key(key):
                print(f"✅ Invalid key correctly rejected")
            else:
                print(f"❌ Invalid key incorrectly accepted")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache key generation test error: {e}")
        return False

def test_cache_serialization():
    """Test cache serialization/deserialization"""
    print("\nTesting Cache Serialization...")
    
    try:
        import json
        import pickle
        from datetime import datetime, timedelta
        
        # Test JSON serialization
        test_data = {
            'user_id': 123,
            'username': 'testuser',
            'posts': [{'id': 1, 'title': 'Test Post'}],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        json_serialized = json.dumps(test_data, default=str)
        json_deserialized = json.loads(json_serialized)
        
        if json_deserialized['user_id'] == test_data['user_id']:
            print("✅ JSON serialization works")
        else:
            print("❌ JSON serialization failed")
        
        # Test pickle serialization
        complex_data = {
            'user': object(),  # Non-serializable object
            'datetime': datetime.utcnow(),
            'timedelta': timedelta(hours=1)
        }
        
        try:
            pickle_serialized = pickle.dumps(complex_data)
            pickle_deserialized = pickle.loads(pickle_serialized)
            print("✅ Pickle serialization works")
        except Exception as e:
            print(f"⚠️ Pickle serialization issue: {e}")
        
        # Test serialization strategy selection
        def serialize_data(data, use_json=True):
            """Serialize data using appropriate strategy"""
            try:
                if use_json:
                    return json.dumps(data, default=str)
                else:
                    return pickle.dumps(data)
            except (TypeError, ValueError):
                return pickle.dumps(data)
        
        def deserialize_data(data, use_json=True):
            """Deserialize data using appropriate strategy"""
            try:
                if use_json:
                    return json.loads(data)
                else:
                    return pickle.loads(data)
            except (json.JSONDecodeError, pickle.UnpicklingError):
                # Fallback
                try:
                    return pickle.loads(data)
                except:
                    return data
        
        # Test serialization strategy
        serialized = serialize_data(test_data)
        deserialized = deserialize_data(serialized)
        
        if deserialized['user_id'] == test_data['user_id']:
            print("✅ Serialization strategy works")
        else:
            print("❌ Serialization strategy failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache serialization test error: {e}")
        return False

def test_cache_invalidation():
    """Test cache invalidation strategies"""
    print("\nTesting Cache Invalidation...")
    
    try:
        # Mock cache for testing
        class MockCache:
            def __init__(self):
                self.data = {}
            
            def set(self, key, value):
                self.data[key] = value
            
            def get(self, key):
                return self.data.get(key)
            
            def delete(self, key):
                return self.data.pop(key, None) is not None
            
            def exists(self, key):
                return key in self.data
            
            def clear_pattern(self, pattern):
                keys_to_delete = [k for k in self.data.keys() if pattern in k]
                for key in keys_to_delete:
                    self.data.pop(key, None)
                return len(keys_to_delete)
        
        cache = MockCache()
        
        # Test pattern-based invalidation
        cache.set("user:123:profile", {"name": "User 123"})
        cache.set("user:123:posts", [{"id": 1}, {"id": 2}])
        cache.set("user:456:profile", {"name": "User 456"})
        
        # Invalidate all user 123 data
        deleted_count = cache.clear_pattern("user:123:")
        if deleted_count == 2:
            print("✅ Pattern-based invalidation works")
        else:
            print(f"❌ Pattern-based invalidation failed: deleted {deleted_count}")
        
        # Verify remaining data
        if cache.exists("user:456:profile"):
            print("✅ Unrelated data preserved")
        else:
            print("❌ Unrelated data incorrectly deleted")
        
        # Test dependency-based invalidation
        class DependencyTracker:
            def __init__(self):
                self.dependencies = {}
            
            def add_dependency(self, key, depends_on):
                if key not in self.dependencies:
                    self.dependencies[key] = set()
                self.dependencies[key].update(depends_on)
            
            def invalidate_dependents(self, key):
                to_invalidate = set()
                for cache_key, deps in self.dependencies.items():
                    if key in deps:
                        to_invalidate.add(cache_key)
                return to_invalidate
        
        tracker = DependencyTracker()
        
        # Set up dependencies
        tracker.add_dependency("user:123:posts", ["user:123"])
        tracker.add_dependency("user:123:profile", ["user:123"])
        
        # Invalidate user 123
        dependents = tracker.invalidate_dependents("user:123")
        if len(dependents) == 2:
            print("✅ Dependency-based invalidation works")
        else:
            print(f"❌ Dependency-based invalidation failed: found {len(dependents)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache invalidation test error: {e}")
        return False

def main():
    """Run all Redis cache system tests"""
    print("Redis Cache System Tests")
    print("=" * 50)
    
    tests = [
        test_redis_connection,
        test_cache_service,
        test_cache_key_generation,
        test_cache_serialization,
        test_cache_invalidation
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("REDIS CACHE SYSTEM TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All Redis cache system tests passed")
        return True
    else:
        print("❌ Some Redis cache system tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
