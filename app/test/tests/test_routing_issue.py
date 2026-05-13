#!/usr/bin/env python3
"""
Test script to debug the routing version detection issue
"""

import sys
sys.path.insert(0, '/home/robbie/Desktop/repo-forum')

from app.api.gateway.routing import GatewayRouter
from app.api.gateway.gateway_manager import APIGatewayManager, GatewayConfig

def test_version_detection():
    """Test version detection to identify the issue"""
    
    # Create manager and router
    manager = APIGatewayManager(GatewayConfig())
    router = GatewayRouter(manager)
    
    print("Testing version detection...")
    
    # Test path-based versioning
    version = router.detect_version("/api/v1/users")
    print(f"Path version detection: '{version}'")
    
    # Test header-based versioning (this should work but path detection happens first)
    version = router.detect_version("/api/v1/users", {"API-Version": "v1.0"})
    print(f"Header version detection: '{version}'")
    
    # Test header-only (no path version)
    version = router.detect_version("/api/users", {"API-Version": "v1.0"})
    print(f"Header-only version detection: '{version}'")
    
    # Test the regex pattern
    import re
    pattern = re.compile(r'^/api/v(\d+(?:\.\d+)*)/')
    match = pattern.match("/api/v1/users")
    if match:
        print(f"Regex match group 1: '{match.group(1)}'")

if __name__ == "__main__":
    test_version_detection()
