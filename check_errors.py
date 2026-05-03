#!/usr/bin/env python3
"""
Error monitoring script for AutoBot Forum
This script allows checking errors from the forum application
"""

import os
import sys
from datetime import datetime
from pathlib import Path

def check_latest_error():
    """Check the latest error file"""
    # Use absolute path to ensure file is found regardless of script location
    script_dir = Path(__file__).parent
    error_file = script_dir / 'logs' / 'latest_error.txt'
    
    if error_file.exists():
        print("=== LATEST FORUM ERROR ===")
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    print(content)
                else:
                    print("Latest error file is empty")
        except Exception as e:
            print(f"Error reading latest error file: {e}")
        print("=" * 30)
    else:
        print(f"No error file found at: {error_file}")

def check_error_log():
    """Check the main error log file"""
    # Use absolute path to ensure file is found regardless of script location
    script_dir = Path(__file__).parent
    log_file = script_dir / 'logs' / 'forum_errors.log'
    
    if log_file.exists():
        print("=== FORUM ERROR LOG (Last 20 lines) ===")
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    for line in lines[-20:]:
                        print(line.strip())
                else:
                    print("Error log file is empty")
        except Exception as e:
            print(f"Error reading error log file: {e}")
        print("=" * 40)
    else:
        print(f"No error log file found at: {log_file}")

def check_terminal_output():
    """Check if we can access terminal output from running Flask app"""
    print("=== TERMINAL OUTPUT CHECK ===")
    print("To check real-time errors:")
    print("1. The Flask app is running in background process")
    print("2. Use 'command_status' tool to check recent output")
    print("3. Look for ERROR or Exception messages in output")
    print("=" * 35)

def main():
    """Main function to check all error sources"""
    print(f"AutoBot Forum Error Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Use absolute path for logs directory
    script_dir = Path(__file__).parent
    logs_dir = script_dir / 'logs'
    
    # Check if logs directory exists
    if not logs_dir.exists():
        print("Creating logs directory...")
        try:
            logs_dir.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Error creating logs directory: {e}")
            return
    
    # Check different error sources
    check_latest_error()
    print()
    check_error_log()
    print()
    check_terminal_output()

if __name__ == "__main__":
    main()
