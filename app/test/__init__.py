"""
Comprehensive Testing Framework for Repo-Forum Project
Covers all components: authentication, admin, forum, API, database, security, etc.
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime
from pathlib import Path

# Import all advanced utilities for complete integration
from .utils.report_generator import TestReportGenerator
from .utils.fixtures import TestDataFactory, DatabaseFixture
from .utils.test_isolation import TestIsolationManager
from .utils.config_manager import TestConfigManager, get_test_config
from .utils.mocking import MockContext, APIMocker, DatabaseMocker
from .utils.performance import PerformanceMonitor, performance_benchmark
from .utils.parallel_executor import ParallelTestRunner, run_tests_parallel
from .utils.coverage_visualizer import CoverageVisualizer, generate_coverage_report
from .utils.history_tracker import HistoryTracker, track_test_results
from .utils.advanced_profiler import AdvancedProfiler, advanced_profile

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestFramework:
    """Comprehensive testing framework for entire repo-forum project"""
    
    def __init__(self):
        self.output_dir = Path(__file__).parent / "output"
        self.reports_dir = self.output_dir / "reports"
        self.logs_dir = self.output_dir / "logs"
        self.screenshots_dir = self.output_dir / "screenshots"
        self.fixtures_dir = self.output_dir / "fixtures"
        self.coverage_dir = self.output_dir / "coverage"
        self.performance_dir = self.output_dir / "performance"
        self.history_dir = self.output_dir / "history"
        
        # Initialize advanced utilities
        self.report_generator = TestReportGenerator(self.output_dir)
        self.data_factory = TestDataFactory()
        self.config_manager = TestConfigManager()
        self.history_tracker = HistoryTracker(str(self.history_dir))
        self.coverage_visualizer = CoverageVisualizer(str(self.output_dir))
        self.performance_monitor = PerformanceMonitor()
        self.advanced_profiler = AdvancedProfiler()
        
        # Ensure directories exist
        self.output_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.fixtures_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
        self.performance_dir.mkdir(exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
        
        self.test_results = []
        self.current_session = datetime.now().isoformat()
        
        # Test categories for the entire project
        self.test_categories = {
            'admin': 'Admin panel functionality',
            'auth': 'Authentication and authorization',
            'forum': 'Forum posts and discussions',
            'api': 'API endpoints and responses',
            'user': 'User profiles and management',
            'message': 'Messaging system',
            'notification': 'Notification system',
            'database': 'Database models and relationships',
            'security': 'Security and CSRF protection',
            'templates': 'Template rendering and UI',
            'integration': 'Component integration tests',
            'performance': 'Performance and load testing'
        }
    
    def run_full_project_test_suite(self):
        """Run complete test suite for entire project"""
        print("🧪 Starting Comprehensive Repo-Forum Project Test Suite")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"📅 Session: {self.current_session}")
        print(f"📊 Testing {len(self.test_categories)} categories")
        
        # Import and run all test modules
        try:
            all_test_results = []
            
            # Admin Tests
            print("\n🔧 Running Admin Panel Tests...")
            from .tests.admin_routes_test import AdminRoutesTest
            from .tests.admin_forms_test import AdminFormsTest
            admin_routes_test = AdminRoutesTest(self)
            admin_forms_test = AdminFormsTest(self)
            all_test_results.extend(admin_routes_test.run_all_tests())
            all_test_results.extend(admin_forms_test.run_all_tests())
            
            # Authentication Tests
            print("\n🔐 Running Authentication Tests...")
            from .tests.auth_test import AuthTest
            from .tests.session_test import SessionTest
            auth_test = AuthTest(self)
            session_test = SessionTest(self)
            all_test_results.extend(auth_test.run_all_tests())
            all_test_results.extend(session_test.run_all_tests())
            
            # Forum Tests
            print("\n💬 Running Forum Tests...")
            from .tests.forum_test import ForumTest
            from .tests.post_test import PostTest
            from .tests.comment_test import CommentTest
            forum_test = ForumTest(self)
            post_test = PostTest(self)
            comment_test = CommentTest(self)
            all_test_results.extend(forum_test.run_all_tests())
            all_test_results.extend(post_test.run_all_tests())
            all_test_results.extend(comment_test.run_all_tests())
            
            # API Tests
            print("\n🌐 Running API Tests...")
            from .tests.api_test import APITest
            from .tests.api_security_test import APISecurityTest
            api_test = APITest(self)
            api_security_test = APISecurityTest(self)
            all_test_results.extend(api_test.run_all_tests())
            all_test_results.extend(api_security_test.run_all_tests())
            
            # User Tests
            print("\n👤 Running User Management Tests...")
            from .tests.user_test import UserTest
            from .tests.profile_test import ProfileTest
            user_test = UserTest(self)
            profile_test = ProfileTest(self)
            all_test_results.extend(user_test.run_all_tests())
            all_test_results.extend(profile_test.run_all_tests())
            
            # Message Tests
            print("\n📧 Running Message System Tests...")
            from .tests.message_test import MessageTest
            message_test = MessageTest(self)
            all_test_results.extend(message_test.run_all_tests())
            
            # Notification Tests
            print("\n🔔 Running Notification Tests...")
            from .tests.notification_test import NotificationTest
            notification_test = NotificationTest(self)
            all_test_results.extend(notification_test.run_all_tests())
            
            # Database Tests
            print("\n🗄️ Running Database Tests...")
            from .tests.database_test import DatabaseTest
            from .tests.model_test import ModelTest
            database_test = DatabaseTest(self)
            model_test = ModelTest(self)
            all_test_results.extend(database_test.run_all_tests())
            all_test_results.extend(model_test.run_all_tests())
            
            # Security Tests
            print("\n🔒 Running Security Tests...")
            from .tests.security_test import SecurityTest
            from .tests.csrf_test import CSRFTest
            security_test = SecurityTest(self)
            csrf_test = CSRFTest(self)
            all_test_results.extend(security_test.run_all_tests())
            all_test_results.extend(csrf_test.run_all_tests())
            
            # Template Tests
            print("\n🎨 Running Template Tests...")
            from .tests.template_test import TemplateTest
            from .tests.ui_test import UITest
            template_test = TemplateTest(self)
            ui_test = UITest(self)
            all_test_results.extend(template_test.run_all_tests())
            all_test_results.extend(ui_test.run_all_tests())
            
            # Integration Tests
            print("\n🔗 Running Integration Tests...")
            from .tests.integration_test import IntegrationTest
            integration_test = IntegrationTest(self)
            all_test_results.extend(integration_test.run_all_tests())
            
            # Performance Tests
            print("\n⚡ Running Performance Tests...")
            from .tests.performance_test import PerformanceTest
            performance_test = PerformanceTest(self)
            all_test_results.extend(performance_test.run_all_tests())
            
            # Generate comprehensive report
            self.generate_comprehensive_report(all_test_results)
            
            return all_test_results
            
        except Exception as e:
            print(f"❌ Test suite error: {e}")
            traceback.print_exc()
            return []
    
    def run_category_tests(self, category):
        """Run tests for a specific category"""
        if category not in self.test_categories:
            print(f"❌ Unknown category: {category}")
            return []
        
        print(f"🧪 Running {category.upper()} Tests - {self.test_categories[category]}")
        
        # Import and run category-specific tests
        try:
            test_results = []
            
            if category == 'admin':
                from .tests.admin_routes_test import AdminRoutesTest
                from .tests.admin_forms_test import AdminFormsTest
                admin_routes_test = AdminRoutesTest(self)
                admin_forms_test = AdminFormsTest(self)
                test_results.extend(admin_routes_test.run_all_tests())
                test_results.extend(admin_forms_test.run_all_tests())
            
            elif category == 'auth':
                from .tests.auth_test import AuthTest
                from .tests.session_test import SessionTest
                auth_test = AuthTest(self)
                session_test = SessionTest(self)
                test_results.extend(auth_test.run_all_tests())
                test_results.extend(session_test.run_all_tests())
            
            elif category == 'forum':
                from .tests.forum_test import ForumTest
                from .tests.post_test import PostTest
                from .tests.comment_test import CommentTest
                forum_test = ForumTest(self)
                post_test = PostTest(self)
                comment_test = CommentTest(self)
                test_results.extend(forum_test.run_all_tests())
                test_results.extend(post_test.run_all_tests())
                test_results.extend(comment_test.run_all_tests())
            
            elif category == 'api':
                from .tests.api_test import APITest
                from .tests.api_security_test import APISecurityTest
                api_test = APITest(self)
                api_security_test = APISecurityTest(self)
                test_results.extend(api_test.run_all_tests())
                test_results.extend(api_security_test.run_all_tests())
            
            elif category == 'user':
                from .tests.user_test import UserTest
                from .tests.profile_test import ProfileTest
                user_test = UserTest(self)
                profile_test = ProfileTest(self)
                test_results.extend(user_test.run_all_tests())
                test_results.extend(profile_test.run_all_tests())
            
            elif category == 'message':
                from .tests.message_test import MessageTest
                message_test = MessageTest(self)
                test_results.extend(message_test.run_all_tests())
            
            elif category == 'notification':
                from .tests.notification_test import NotificationTest
                notification_test = NotificationTest(self)
                test_results.extend(notification_test.run_all_tests())
            
            elif category == 'database':
                from .tests.database_test import DatabaseTest
                from .tests.model_test import ModelTest
                database_test = DatabaseTest(self)
                model_test = ModelTest(self)
                test_results.extend(database_test.run_all_tests())
                test_results.extend(model_test.run_all_tests())
            
            elif category == 'security':
                from .tests.security_test import SecurityTest
                from .tests.csrf_test import CSRFTest
                security_test = SecurityTest(self)
                csrf_test = CSRFTest(self)
                test_results.extend(security_test.run_all_tests())
                test_results.extend(csrf_test.run_all_tests())
            
            elif category == 'templates':
                from .tests.template_test import TemplateTest
                from .tests.ui_test import UITest
                template_test = TemplateTest(self)
                ui_test = UITest(self)
                test_results.extend(template_test.run_all_tests())
                test_results.extend(ui_test.run_all_tests())
            
            elif category == 'integration':
                from .tests.integration_test import IntegrationTest
                integration_test = IntegrationTest(self)
                test_results.extend(integration_test.run_all_tests())
            
            elif category == 'performance':
                from .tests.performance_test import PerformanceTest
                performance_test = PerformanceTest(self)
                test_results.extend(performance_test.run_all_tests())
            
            # Generate category report
            self.generate_category_report(category, test_results)
            
            return test_results
            
        except Exception as e:
            print(f"❌ Category test error: {e}")
            traceback.print_exc()
            return []
    
    def generate_comprehensive_report(self, test_results):
        """Generate comprehensive test report for entire project"""
        report = {
            "test_session": {
                "timestamp": datetime.now().isoformat(),
                "project": "repo-forum",
                "total_tests": len(test_results),
                "passed": len([r for r in test_results if r["status"] == "passed"]),
                "failed": len([r for r in test_results if r["status"] == "failed"]),
                "skipped": len([r for r in test_results if r["status"] == "skipped"]),
                "errors": len([r for r in test_results if r["status"] == "error"]),
                "categories_tested": len(set(r.get('category', 'unknown') for r in test_results))
            },
            "results": test_results,
            "categories": {},
            "recommendations": [],
            "coverage": self.calculate_coverage(test_results)
        }
        
        # Group results by category
        for result in test_results:
            category = result.get('category', 'unknown')
            if category not in report["categories"]:
                report["categories"][category] = []
            report["categories"][category].append(result)
        
        # Add recommendations based on test results
        failed_tests = [r for r in test_results if r["status"] in ["failed", "error"]]
        if failed_tests:
            report["recommendations"].append("Fix failed tests before deployment")
        
        # Calculate success rate by category
        category_stats = {}
        for category, tests in report["categories"].items():
            passed = len([t for t in tests if t["status"] == "passed"])
            total = len(tests)
            category_stats[category] = {
                "passed": passed,
                "total": total,
                "success_rate": (passed / total * 100) if total > 0 else 0
            }
        
        report["category_stats"] = category_stats
        
        # Save report
        report_file = self.reports_dir / f"full_project_test_report_{self.current_session.replace(':', '-')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generate HTML dashboard
        try:
            from .utils.report_generator import TestReportGenerator
            dashboard_generator = TestReportGenerator(self.output_dir)
            dashboard_file = dashboard_generator.generate_html_dashboard(
                test_results, report["test_session"]
            )
            print(f"🎨 HTML Dashboard Generated: {dashboard_file}")
        except Exception as e:
            print(f"⚠️ HTML Dashboard generation failed: {e}")
        
        # Print summary
        print(f"\n📊 Full Project Test Report Generated: {report_file}")
        session = report["test_session"]
        print(f"✅ Passed: {session['passed']} ({session['passed']/session['total_tests']*100:.1f}%)")
        print(f"❌ Failed: {session['failed']} ({session['failed']/session['total_tests']*100:.1f}%)")
        print(f"⚠️ Skipped: {session['skipped']} ({session['skipped']/session['total_tests']*100:.1f}%)")
        print(f"🚫 Errors: {session['errors']} ({session['errors']/session['total_tests']*100:.1f}%)")
        print(f"📈 Overall Success Rate: {session['passed']/session['total_tests']*100:.1f}%")
        print(f"📊 Categories Tested: {session['categories_tested']}")
        
        return report
    
    def generate_category_report(self, category, test_results):
        """Generate report for specific category"""
        report = {
            "test_session": {
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "description": self.test_categories.get(category, "Unknown category"),
                "total_tests": len(test_results),
                "passed": len([r for r in test_results if r["status"] == "passed"]),
                "failed": len([r for r in test_results if r["status"] == "failed"]),
                "skipped": len([r for r in test_results if r["status"] == "skipped"]),
                "errors": len([r for r in test_results if r["status"] == "error"])
            },
            "results": test_results,
            "recommendations": []
        }
        
        # Add recommendations
        failed_tests = [r for r in test_results if r["status"] in ["failed", "error"]]
        if failed_tests:
            report["recommendations"].append(f"Fix {len(failed_tests)} failed {category} tests")
        
        # Save report
        report_file = self.reports_dir / f"{category}_test_report_{self.current_session.replace(':', '-')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        session = report["test_session"]
        print(f"📊 {category.upper()} Test Report Generated: {report_file}")
        
        if session['total_tests'] > 0:
            print(f"✅ Passed: {session['passed']} ({session['passed']/session['total_tests']*100:.1f}%)")
            print(f"❌ Failed: {session['failed']} ({session['failed']/session['total_tests']*100:.1f}%)")
            print(f"⚠️ Skipped: {session['skipped']} ({session['skipped']/session['total_tests']*100:.1f}%)")
            print(f"📈 Success Rate: {session['passed']/session['total_tests']*100:.1f}%")
        else:
            print(f"⚠️ No tests were executed for {category.upper()} category")
        
        return report
    
    def calculate_coverage(self, test_results):
        """Calculate test coverage metrics"""
        total_tests = len(test_results)
        if total_tests == 0:
            return {"overall": 0, "by_category": {}}
        
        passed_tests = len([r for r in test_results if r["status"] == "passed"])
        overall_coverage = (passed_tests / total_tests) * 100
        
        # Coverage by category
        category_coverage = {}
        for result in test_results:
            category = result.get('category', 'unknown')
            if category not in category_coverage:
                category_coverage[category] = {"total": 0, "passed": 0}
            category_coverage[category]["total"] += 1
            if result["status"] == "passed":
                category_coverage[category]["passed"] += 1
        
        # Calculate percentages
        for category in category_coverage:
            stats = category_coverage[category]
            stats["coverage"] = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        
        return {
            "overall": overall_coverage,
            "by_category": category_coverage
        }
    
    def run_test_suite(self):
        """Legacy method - redirects to full project test suite"""
        return self.run_full_project_test_suite()

# Global test framework instance
test_framework = TestFramework()
