#!/usr/bin/env python3
"""
Error monitoring script for AutoBot Forum
This script allows checking errors from the forum application
"""

import os
import sys
from datetime import datetime

def check_latest_error():
    """Check the latest error file"""
    error_file = 'logs/latest_error.txt'
    if os.path.exists(error_file):
        print("=== LATEST FORUM ERROR ===")
        with open(error_file, 'r') as f:
            print(f.read())
        print("=" * 30)
    else:
        print("No error file found at logs/latest_error.txt")

def check_error_log():
    """Check the main error log file"""
    log_file = 'logs/forum_errors.log'
    if os.path.exists(log_file):
        print("=== FORUM ERROR LOG (Last 20 lines) ===")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(line.strip())
        print("=" * 40)
    else:
        print("No error log file found at logs/forum_errors.log")

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
    
    # Check if logs directory exists
    if not os.path.exists('logs'):
        print("Creating logs directory...")
        os.makedirs('logs')
    
    # Check different error sources
    check_latest_error()
    print()
    check_error_log()
    print()
    check_terminal_output()

if __name__ == "__main__":
    main()
