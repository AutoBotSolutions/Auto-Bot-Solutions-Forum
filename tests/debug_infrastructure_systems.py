#!/usr/bin/env python3
"""
Infrastructure Systems Debugging Script

This script comprehensively tests all infrastructure components that were implemented:
1. Profile Infrastructure
2. Social Infrastructure  
3. Analytics Infrastructure
4. Theme Management System

It checks for:
- File existence and imports
- Class instantiation and method availability
- Basic functionality testing
- Performance metrics
- Error handling
"""

import os
import sys
import importlib
import traceback
import tempfile
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, '/home/robbie/Desktop/repo-forum')

class InfrastructureDebugger:
    def __init__(self):
        self.results = {
            'profile_infrastructure': {'tests': [], 'passed': 0, 'failed': 0},
            'social_infrastructure': {'tests': [], 'passed': 0, 'failed': 0},
            'analytics_infrastructure': {'tests': [], 'passed': 0, 'failed': 0},
            'theme_management': {'tests': [], 'passed': 0, 'failed': 0},
        }
        self.total_tests = 0
        self.total_passed = 0
        self.total_failed = 0

    def log_test(self, system, test_name, passed, message=""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': 'PASS' if passed else 'FAIL',
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.results[system]['tests'].append(result)
        
        if passed:
            self.results[system]['passed'] += 1
            self.total_passed += 1
        else:
            self.results[system]['failed'] += 1
            self.total_failed += 1
        
        self.total_tests += 1
        
        status_icon = "✅" if passed else "❌"
        print(f"{status_icon} {system}: {test_name}")
        if message:
            print(f"   {message}")

    def test_file_existence(self):
        """Test if infrastructure file exists"""
        print("\n🔍 Testing file existence...")
        
        infrastructure_file = '/home/robbie/Desktop/repo-forum/app/user/infrastructure.py'
        exists = os.path.exists(infrastructure_file)
        
        self.log_test(
            'profile_infrastructure',
            'Infrastructure file exists',
            exists,
            f"File: {infrastructure_file}" if exists else "File not found"
        )
        
        return exists

    def test_imports(self):
        """Test if infrastructure modules can be imported"""
        print("\n🔍 Testing module imports...")
        
        try:
            # Test infrastructure import
            from app.user.infrastructure import ProfileInfrastructure, SocialInfrastructure, AnalyticsInfrastructure, ThemeManagementSystem
            
            self.log_test('profile_infrastructure', 'Import ProfileInfrastructure', True)
            self.log_test('social_infrastructure', 'Import SocialInfrastructure', True)
            self.log_test('analytics_infrastructure', 'Import AnalyticsInfrastructure', True)
            self.log_test('theme_management', 'Import ThemeManagementSystem', True)
            
            return True
            
        except Exception as e:
            self.log_test('profile_infrastructure', 'Import ProfileInfrastructure', False, str(e))
            self.log_test('social_infrastructure', 'Import SocialInfrastructure', False, str(e))
            self.log_test('analytics_infrastructure', 'Import AnalyticsInfrastructure', False, str(e))
            self.log_test('theme_management', 'Import ThemeManagementSystem', False, str(e))
            
            return False

    def test_profile_infrastructure(self):
        """Test ProfileInfrastructure class"""
        print("\n🔍 Testing ProfileInfrastructure...")
        
        try:
            from app.user.infrastructure import ProfileInfrastructure
            
            # Test static methods exist
            methods = [
                'get_profile_storage_path',
                'ensure_storage_directories',
                'store_profile_image',
                'delete_profile_image',
                'create_profile_backup',
                'restore_profile_backup',
                'get_profile_performance_metrics'
            ]
            
            for method in methods:
                if hasattr(ProfileInfrastructure, method):
                    self.log_test('profile_infrastructure', f'Method {method} exists', True)
                else:
                    self.log_test('profile_infrastructure', f'Method {method} exists', False, "Method not found")
            
            # Test storage path method
            try:
                storage_path = ProfileInfrastructure.get_profile_storage_path()
                self.log_test('profile_infrastructure', 'Get storage path', True, f"Path: {storage_path}")
            except Exception as e:
                self.log_test('profile_infrastructure', 'Get storage path', False, str(e))
            
            # Test ensure storage directories
            try:
                ProfileInfrastructure.ensure_storage_directories()
                self.log_test('profile_infrastructure', 'Ensure storage directories', True)
            except Exception as e:
                self.log_test('profile_infrastructure', 'Ensure storage directories', False, str(e))
            
            # Test profile performance metrics (mock user_id)
            try:
                metrics = ProfileInfrastructure.get_profile_performance_metrics(1)
                if metrics:
                    self.log_test('profile_infrastructure', 'Get profile performance metrics', True, f"Metrics keys: {list(metrics.keys())}")
                else:
                    self.log_test('profile_infrastructure', 'Get profile performance metrics', False, "No metrics returned")
            except Exception as e:
                self.log_test('profile_infrastructure', 'Get profile performance metrics', False, str(e))
            
        except Exception as e:
            self.log_test('profile_infrastructure', 'ProfileInfrastructure class test', False, str(e))

    def test_theme_management(self):
        """Test ThemeManagementSystem class"""
        print("\n🔍 Testing ThemeManagementSystem...")
        
        try:
            from app.user.infrastructure import ThemeManagementSystem
            
            # Test static methods exist
            methods = [
                'get_available_themes',
                'get_theme_css',
                'generate_theme_css',
                'create_custom_theme'
            ]
            
            for method in methods:
                if hasattr(ThemeManagementSystem, method):
                    self.log_test('theme_management', f'Method {method} exists', True)
                else:
                    self.log_test('theme_management', f'Method {method} exists', False, "Method not found")
            
            # Test get available themes
            try:
                themes = ThemeManagementSystem.get_available_themes()
                if themes and len(themes) > 0:
                    self.log_test('theme_management', 'Get available themes', True, f"Found {len(themes)} themes")
                    
                    # Test theme CSS generation
                    if themes:
                        theme_id = themes[0]['id']
                        css = ThemeManagementSystem.get_theme_css(theme_id)
                        self.log_test('theme_management', 'Get theme CSS', True, f"CSS variables: {len(css)}")
                        
                        # Test complete CSS generation
                        full_css = ThemeManagementSystem.generate_theme_css(theme_id)
                        self.log_test('theme_management', 'Generate theme CSS', True, f"CSS length: {len(full_css)} chars")
                else:
                    self.log_test('theme_management', 'Get available themes', False, "No themes found")
            except Exception as e:
                self.log_test('theme_management', 'Get available themes', False, str(e))
            
            # Test custom theme creation
            try:
                custom_theme = ThemeManagementSystem.create_custom_theme(
                    "Test Theme",
                    {'--bg-primary': '#ffffff', '--text-primary': '#000000'}
                )
                self.log_test('theme_management', 'Create custom theme', True, f"Theme ID: {custom_theme['id']}")
            except Exception as e:
                self.log_test('theme_management', 'Create custom theme', False, str(e))
            
        except Exception as e:
            self.log_test('theme_management', 'ThemeManagementSystem class test', False, str(e))

    def test_social_infrastructure(self):
        """Test SocialInfrastructure class"""
        print("\n🔍 Testing SocialInfrastructure...")
        
        try:
            from app.user.infrastructure import SocialInfrastructure
            
            # Test static methods exist
            methods = [
                'get_social_graph_data',
                'process_social_feed',
                'get_social_analytics',
                'get_social_performance_metrics'
            ]
            
            for method in methods:
                if hasattr(SocialInfrastructure, method):
                    self.log_test('social_infrastructure', f'Method {method} exists', True)
                else:
                    self.log_test('social_infrastructure', f'Method {method} exists', False, "Method not found")
            
            # Test social graph data (mock user_id)
            try:
                graph_data = SocialInfrastructure.get_social_graph_data(1, depth=1)
                if graph_data:
                    self.log_test('social_infrastructure', 'Get social graph data', True, f"Nodes: {len(graph_data.get('nodes', []))}")
                else:
                    self.log_test('social_infrastructure', 'Get social graph data', False, "No graph data returned")
            except Exception as e:
                self.log_test('social_infrastructure', 'Get social graph data', False, str(e))
            
            # Test social feed processing (mock user_id)
            try:
                feed_data = SocialInfrastructure.process_social_feed(1, limit=10)
                if feed_data:
                    self.log_test('social_infrastructure', 'Process social feed', True, f"Items: {len(feed_data.get('items', []))}")
                else:
                    self.log_test('social_infrastructure', 'Process social feed', False, "No feed data returned")
            except Exception as e:
                self.log_test('social_infrastructure', 'Process social feed', False, str(e))
            
            # Test social analytics (mock user_id)
            try:
                analytics = SocialInfrastructure.get_social_analytics(1, days=7)
                if analytics:
                    self.log_test('social_infrastructure', 'Get social analytics', True, f"Overview keys: {list(analytics.get('overview', {}).keys())}")
                else:
                    self.log_test('social_infrastructure', 'Get social analytics', False, "No analytics returned")
            except Exception as e:
                self.log_test('social_infrastructure', 'Get social analytics', False, str(e))
            
            # Test social performance metrics
            try:
                metrics = SocialInfrastructure.get_social_performance_metrics()
                if metrics:
                    self.log_test('social_infrastructure', 'Get social performance metrics', True, f"Sections: {list(metrics.keys())}")
                else:
                    self.log_test('social_infrastructure', 'Get social performance metrics', False, "No metrics returned")
            except Exception as e:
                self.log_test('social_infrastructure', 'Get social performance metrics', False, str(e))
            
        except Exception as e:
            self.log_test('social_infrastructure', 'SocialInfrastructure class test', False, str(e))

    def test_analytics_infrastructure(self):
        """Test AnalyticsInfrastructure class"""
        print("\n🔍 Testing AnalyticsInfrastructure...")
        
        try:
            from app.user.infrastructure import AnalyticsInfrastructure
            
            # Test static methods exist
            methods = [
                'get_analytics_data_warehouse',
                'process_real_time_analytics',
                'generate_analytics_visualization',
                'get_analytics_performance_metrics'
            ]
            
            for method in methods:
                if hasattr(AnalyticsInfrastructure, method):
                    self.log_test('analytics_infrastructure', f'Method {method} exists', True)
                else:
                    self.log_test('analytics_infrastructure', f'Method {method} exists', False, "Method not found")
            
            # Test analytics data warehouse (mock user_id)
            try:
                start_date = datetime.utcnow() - timedelta(days=7)
                end_date = datetime.utcnow()
                warehouse_data = AnalyticsInfrastructure.get_analytics_data_warehouse(1, start_date, end_date)
                if warehouse_data:
                    self.log_test('analytics_infrastructure', 'Get analytics data warehouse', True, f"Sections: {list(warehouse_data.keys())}")
                else:
                    self.log_test('analytics_infrastructure', 'Get analytics data warehouse', False, "No warehouse data returned")
            except Exception as e:
                self.log_test('analytics_infrastructure', 'Get analytics data warehouse', False, str(e))
            
            # Test real-time analytics processing (mock event)
            try:
                event_data = {
                    'behavior_type': 'test',
                    'action': 'test_action',
                    'target_type': 'test_target',
                    'metadata': {'test': True}
                }
                result = AnalyticsInfrastructure.process_real_time_analytics(1, 'test_event', event_data)
                self.log_test('analytics_infrastructure', 'Process real-time analytics', True, f"Result: {result}")
            except Exception as e:
                self.log_test('analytics_infrastructure', 'Process real-time analytics', False, str(e))
            
            # Test analytics visualization (mock user_id)
            try:
                viz_data = AnalyticsInfrastructure.generate_analytics_visualization(1, 'engagement_trend', '7d')
                if viz_data:
                    self.log_test('analytics_infrastructure', 'Generate analytics visualization', True, f"Chart type: {viz_data.get('type')}")
                else:
                    self.log_test('analytics_infrastructure', 'Generate analytics visualization', False, "No visualization data returned")
            except Exception as e:
                self.log_test('analytics_infrastructure', 'Generate analytics visualization', False, str(e))
            
            # Test analytics performance metrics
            try:
                metrics = AnalyticsInfrastructure.get_analytics_performance_metrics()
                if metrics:
                    self.log_test('analytics_infrastructure', 'Get analytics performance metrics', True, f"Sections: {list(metrics.keys())}")
                else:
                    self.log_test('analytics_infrastructure', 'Get analytics performance metrics', False, "No metrics returned")
            except Exception as e:
                self.log_test('analytics_infrastructure', 'Get analytics performance metrics', False, str(e))
            
        except Exception as e:
            self.log_test('analytics_infrastructure', 'AnalyticsInfrastructure class test', False, str(e))

    def test_integration(self):
        """Test integration between components"""
        print("\n🔍 Testing integration...")
        
        try:
            from app.user.infrastructure import ProfileInfrastructure, ThemeManagementSystem
            
            # Test theme integration with profile
            try:
                themes = ThemeManagementSystem.get_available_themes()
                if themes:
                    storage_path = ProfileInfrastructure.get_profile_storage_path()
                    self.log_test('profile_infrastructure', 'Theme integration test', True, f"Themes: {len(themes)}, Storage: {storage_path}")
                else:
                    self.log_test('profile_infrastructure', 'Theme integration test', False, "No themes available")
            except Exception as e:
                self.log_test('profile_infrastructure', 'Theme integration test', False, str(e))
            
        except Exception as e:
            self.log_test('profile_infrastructure', 'Integration test', False, str(e))

    def generate_report(self):
        """Generate final debugging report"""
        print("\n" + "="*60)
        print("📊 INFRASTRUCTURE SYSTEMS DEBUGGING REPORT")
        print("="*60)
        
        print(f"\n📈 OVERALL STATISTICS:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   Passed: {self.total_passed}")
        print(f"   Failed: {self.total_failed}")
        
        if self.total_tests > 0:
            success_rate = (self.total_passed / self.total_tests) * 100
            print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\n🔍 SYSTEM BREAKDOWN:")
        
        for system, results in self.results.items():
            system_name = system.replace('_', ' ').title()
            total = results['passed'] + results['failed']
            passed = results['passed']
            
            if total > 0:
                success_rate = (passed / total) * 100
                status = "✅ PASS" if success_rate >= 80 else "❌ FAIL"
                print(f"\n   {system_name}:")
                print(f"   Status: {status}")
                print(f"   Successes: {passed}")
                print(f"   Issues: {results['failed']}")
                
                # Show failed tests
                failed_tests = [t for t in results['tests'] if t['status'] == 'FAIL']
                if failed_tests:
                    print(f"   Issues:")
                    for test in failed_tests:
                        print(f"     - ❌ {test['test']}: {test['message']}")
        
        # Generate detailed report file
        report_file = '/home/robbie/Desktop/repo-forum/INFRASTRUCTURE_DEBUG_REPORT.md'
        self.generate_markdown_report(report_file)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        print("="*60)

    def generate_markdown_report(self, filename):
        """Generate markdown report"""
        with open(filename, 'w') as f:
            f.write("# Infrastructure Systems Debugging Report\n\n")
            f.write(f"**Debugging Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"**System Status:** Production Testing\n\n")
            
            f.write("## Overview\n\n")
            f.write("This report details the debugging results for all infrastructure components:\n")
            f.write("1. Profile Infrastructure\n")
            f.write("2. Social Infrastructure\n")
            f.write("3. Analytics Infrastructure\n")
            f.write("4. Theme Management System\n\n")
            
            f.write("## Results Summary\n\n")
            f.write(f"- **Total Tests:** {self.total_tests}\n")
            f.write(f"- **Passed:** {self.total_passed}\n")
            f.write(f"- **Failed:** {self.total_failed}\n")
            
            if self.total_tests > 0:
                success_rate = (self.total_passed / self.total_tests) * 100
                f.write(f"- **Success Rate:** {success_rate:.1f}%\n\n")
            
            f.write("## Detailed Results\n\n")
            
            for system, results in self.results.items():
                system_name = system.replace('_', ' ').title()
                f.write(f"### {system_name}\n\n")
                
                for test in results['tests']:
                    status_icon = "✅" if test['status'] == 'PASS' else "❌"
                    f.write(f"- {status_icon} **{test['test']}** - {test['message']}\n")
                
                f.write("\n")
            
            f.write("## Recommendations\n\n")
            
            if self.total_failed == 0:
                f.write("✅ **All systems are operational and ready for production deployment.**\n")
            else:
                f.write("⚠️ **Some issues found that need to be addressed before production deployment:**\n\n")
                
                for system, results in self.results.items():
                    failed_tests = [t for t in results['tests'] if t['status'] == 'FAIL']
                    if failed_tests:
                        system_name = system.replace('_', ' ').title()
                        f.write(f"### {system_name}\n")
                        for test in failed_tests:
                            f.write(f"- Fix: {test['test']} - {test['message']}\n")
                        f.write("\n")

def main():
    """Main debugging function"""
    print("🚀 Starting Infrastructure Systems Debugging...")
    print("="*60)
    
    debugger = InfrastructureDebugger()
    
    # Run all tests
    debugger.test_file_existence()
    debugger.test_imports()
    debugger.test_profile_infrastructure()
    debugger.test_theme_management()
    debugger.test_social_infrastructure()
    debugger.test_analytics_infrastructure()
    debugger.test_integration()
    
    # Generate report
    debugger.generate_report()

if __name__ == "__main__":
    main()
