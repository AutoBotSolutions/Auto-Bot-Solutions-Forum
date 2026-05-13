#!/usr/bin/env python3
"""
Check what OAuth2 mixins are available in authlib
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    from authlib.integrations.sqla_oauth2 import *
    print("Available OAuth2 mixins:")
    
    # Get all available classes and functions
    import authlib.integrations.sqla_oauth2 as oauth2_module
    available_items = [item for item in dir(oauth2_module) if 'Mixin' in item or 'OAuth2' in item]
    
    for item in available_items:
        print(f"  - {item}")
        
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
