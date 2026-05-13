#!/usr/bin/env python3
"""
Check all available items in authlib sqla_oauth2
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    import authlib.integrations.sqla_oauth2 as oauth2_module
    print("All available items in authlib.integrations.sqla_oauth2:")
    
    available_items = [item for item in dir(oauth2_module) if not item.startswith('_')]
    
    for item in sorted(available_items):
        print(f"  - {item}")
        
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
