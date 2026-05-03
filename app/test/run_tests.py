#!/usr/bin/env python3
"""
Comprehensive Test Runner for Repo-Forum Project
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    parser = argparse.ArgumentParser(description='Run comprehensive repo-forum project tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--category', '-c', 
                       choices=['admin', 'auth', 'forum', 'api', 'user', 'message', 
                               'notification', 'database', 'security', 'templates', 
                               'integration', 'performance'], 
                       help='Run specific test category')
    parser.add_argument('--output', '-o', type=str, default='json', 
                       choices=['json', 'text'], help='Output format')
    parser.add_argument('--full', '-f', action='store_true', 
                       help='Run full project test suite (default)')
    parser.add_argument('--list-categories', '-l', action='store_true', 
                       help='List all available test categories')
    parser.add_argument('--parallel', '-p', action='store_true', 
                       help='Run tests in parallel for improved performance')
    parser.add_argument('--workers', '-w', type=int, default=4, 
                       help='Number of parallel workers (default: 4)')
    parser.add_argument('--coverage', action='store_true', 
                       help='Generate test coverage visualization')
    
    args = parser.parse_args()
    
    # Import and initialize the test framework
    try:
        from app.test import TestFramework
        test_framework = TestFramework()
        
        if args.list_categories:
            print(" Available Test Categories:")
            for category, description in test_framework.test_categories.items():
                print(f"  • {category}: {description}")
            return 0
        
        if args.parallel:
            # Run tests in parallel
            from app.test.utils.parallel_executor import ParallelTestRunner
            print(f"🚀 Running tests in PARALLEL mode with {args.workers} workers...")
            
            runner = ParallelTestRunner(max_workers=args.workers)
            
            if args.category:
                # Run specific category in parallel
                print(f"🔄 Running {args.category.upper()} category in parallel...")
                parallel_results = runner.run_category_parallel(args.category)
                # Convert to framework format
                framework_results = []
                for result in parallel_results:
                    framework_results.append({
                        'test_name': result.test_name,
                        'category': result.category,
                        'status': result.status,
                        'message': result.message,
                        'details': result.details,
                        'timestamp': result.timestamp.isoformat()
                    })
                results = framework_results
            else:
                # Run all categories in parallel
                parallel_results = runner.run_parallel_tests()
                # Convert to framework format
                framework_results = []
                for category, category_results in parallel_results['results'].items():
                    for result in category_results:
                        framework_results.append({
                            'test_name': result.test_name,
                            'category': result.category,
                            'status': result.status,
                            'message': result.message,
                            'details': result.details,
                            'timestamp': result.timestamp.isoformat()
                        })
                
                results = framework_results
                
                # Print parallel execution summary
                summary = parallel_results['summary']
                print(f"\n🎯 Parallel Execution Summary:")
                print(f"   Total Categories: {summary['total_categories']}")
                print(f"   Total Tests: {summary['total_tests']}")
                print(f"   Success Rate: {summary['success_rate']:.1f}%")
                print(f"   Total Time: {summary['total_execution_time']:.2f}s")
                print(f"   Workers Used: {summary['max_workers']}")
                
                # Generate parallel report
                from pathlib import Path
                output_dir = Path("app/test/output")
                output_dir.mkdir(parents=True, exist_ok=True)
                report_file = runner.generate_parallel_report(parallel_results, str(output_dir))
                print(f"📊 Parallel Report Generated: {report_file}")
        else:
            # Run tests sequentially (original behavior)
            if args.category:
                # Run specific category tests
                print(f"🧪 Running {args.category.upper()} tests...")
                results = test_framework.run_category_tests(args.category)
            else:
                # Run full project test suite
                print("🧪 Running Full Project Test Suite...")
                results = test_framework.run_full_project_test_suite()
        
        # Generate coverage visualization if requested
        if args.coverage:
            print("\n📊 Generating coverage visualization...")
            try:
                from app.test.utils.coverage_visualizer import generate_coverage_report
                coverage_report = generate_coverage_report("app/test/output")
                print(f"📈 Coverage visualization generated: {coverage_report}")
            except Exception as e:
                print(f"⚠️ Coverage visualization failed: {e}")
        
        # Print results
        if args.verbose:
            print(f"\n📊 Test Results Summary:")
            print(f"Total Tests: {len(results)}")
            print(f"Passed: {len([r for r in results if r['status'] == 'passed'])}")
            print(f"Failed: {len([r for r in results if r['status'] == 'failed'])}")
            print(f"Skipped: {len([r for r in results if r['status'] == 'skipped'])}")
            print(f"Errors: {len([r for r in results if r['status'] == 'error'])}")
        
        # Calculate success rate
        if results:
            passed = len([r for r in results if r['status'] == 'passed'])
            total = len(results)
            success_rate = (passed / total) * 100
            print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        # Generate report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if args.output == 'json':
            print(f"\n📄 JSON report saved: app/test/output/test_report_{timestamp}.json")
        else:
            print(f"\n📄 Text report saved: app/test/output/test_report_{timestamp}.txt")
        
        return 0 if all(r['status'] in ['passed', 'skipped'] for r in results) else 1
        
    
    except Exception as e:
        print(f"❌ Test runner error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_specific_category(category):
    """Run tests for a specific category"""
    results = []
    
    # Admin tests
    if category == 'admin':
        from app.test.tests.admin_routes_test import AdminRoutesTest
        from app.test.tests.admin_forms_test import AdminFormsTest
        test_class1 = AdminRoutesTest(test_framework)
        test_class2 = AdminFormsTest(test_framework)
        results = test_class1.run_all_tests() + test_class2.run_all_tests()
    
    # Authentication tests
    elif category == 'auth':
        from app.test.tests.auth_test import AuthTest
        from app.test.tests.session_test import SessionTest
        test_class1 = AuthTest(test_framework)
        test_class2 = SessionTest(test_framework)
        results = test_class1.run_all_tests() + test_class2.run_all_tests()
    
    # Forum tests
    elif category == 'forum':
        from app.test.tests.forum_test import ForumTest
        from app.test.tests.post_test import PostTest
        from app.test.tests.comment_test import CommentTest
        test_class1 = ForumTest(test_framework)
        test_class2 = PostTest(test_framework)
        test_class3 = CommentTest(test_framework)
        results = test_class1.run_all_tests() + test_class2.run_all_tests() + test_class3.run_all_tests()
    
    # API tests
    elif category == 'api':
        from app.test.tests.api_test import APITest
        from app.test.tests.api_security_test import APISecurityTest
        test_class1 = APITest(test_framework)
        test_class2 = APISecurityTest(test_framework)
        results = test_class1.run_all_tests() + test_class2.run_all_tests()
    
    # User tests
    elif category == 'user':
        from app.test.tests.user_test import UserTest
        from app.test.tests.profile_test import ProfileTest
        test_class1 = UserTest(test_framework)
        test_class2 = ProfileTest(test_framework)
        results = test_class1.run_all_tests() + test_class2.run_all_tests()
    
    # Communication tests
    elif category == 'message':
        from app.test.tests.message_test import MessageTest
        test_class = MessageTest(test_framework)
        results = test_class.run_all_tests()
    
    elif category == 'notification':
        from app.test.tests.notification_test import NotificationTest
        test_class = NotificationTest(test_framework)
        results = test_class.run_all_tests()
    
    # Database tests
    elif category == 'database':
        from app.test.tests.database_test import DatabaseTest
        from app.test.tests.model_test import ModelTest
        test_class1 = DatabaseTest(test_framework)
        test_class2 = ModelTest(test_framework)
        results = test_class1.run_all_tests() + test_class2.run_all_tests()
    
    # Security tests
    elif category == 'security':
        from app.test.tests.security_test import SecurityTest
        from app.test.tests.csrf_test import CSRFTest
        test_class1 = SecurityTest(test_framework)
        test_class2 = CSRFTest(test_framework)
        results = test_class1.run_all_tests() + test_class2.run_all_tests()
    
    # Template tests
    elif category == 'templates':
        from app.test.tests.template_test import TemplateTest
        from app.test.tests.ui_test import UITest
        test_class1 = TemplateTest(test_framework)
        test_class2 = UITest(test_framework)
        results = test_class1.run_all_tests() + test_class2.run_all_tests()
    
    # Integration tests
    elif category == 'integration':
        from app.test.tests.integration_test import IntegrationTest
        test_class = IntegrationTest(test_framework)
        results = test_class.run_all_tests()
    
    # Performance tests
    elif category == 'performance':
        from app.test.tests.performance_test import PerformanceTest
        test_class = PerformanceTest(test_framework)
        results = test_class.run_all_tests()
    
    # Legacy tests (for backward compatibility)
    elif category == 'admin_routes':
        from app.test.tests.admin_routes_test import AdminRoutesTest
        test_class = AdminRoutesTest(test_framework)
        results = test_class.run_all_tests()
    
    elif category == 'dropdown_menu':
        from app.test.tests.dropdown_menu_test import DropdownMenuTest
        test_class = DropdownMenuTest(test_framework)
        results = test_class.run_all_tests()
    
    elif category == 'authentication':
        from app.test.tests.authentication_test import AuthenticationTest
        test_class = AuthenticationTest(test_framework)
        results = test_class.run_all_tests()
    
    elif category == 'server_config':
        from app.test.tests.server_config_test import ServerConfigTest
        test_class = ServerConfigTest(test_framework)
        results = test_class.run_all_tests()
    
    return results

def generate_json_report(results, output_dir):
    """Generate JSON report"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    report = {
        "test_session": {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "passed": len([r for r in results if r['status'] == 'passed']),
            "failed": len([r for r in results if r['status'] == 'failed']),
            "skipped": len([r for r in results if r['status'] == 'skipped']),
            "errors": len([r for r in results if r['status'] == 'error'])
        },
        "results": results,
        "categories": {
            "admin_routes": [r for r in results if r.get('category') == 'admin_routes'],
            "dropdown_menu": [r for r in results if r.get('category') == 'dropdown_menu'],
            "authentication": [r for r in results if r.get('category') == 'authentication'],
            "server_config": [r for r in results if r.get('category') == 'server_config']
        },
        "recommendations": generate_recommendations(results)
    }
    
    report_file = output_path / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📄 JSON report saved: {report_file}")

def generate_text_report(results, output_dir):
    """Generate text report"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    report_file = output_path / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w') as f:
        f.write("Admin Users Page - Test Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        total_tests = len(results)
        passed = len([r for r in results if r['status'] == 'passed'])
        failed = len([r for r in results if r['status'] == 'failed'])
        skipped = len([r for r in results if r['status'] == 'skipped'])
        errors = len([r for r in results if r['status'] == 'error'])
        
        f.write(f"Summary:\n")
        f.write(f"  Total Tests: {total_tests}\n")
        f.write(f"  Passed: {passed}\n")
        f.write(f"  Failed: {failed}\n")
        f.write(f"  Skipped: {skipped}\n")
        f.write(f"  Errors: {errors}\n\n")
        
        # Results by category
        categories = {}
        for result in results:
            category = result.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        for category, cat_results in categories.items():
            f.write(f"{category.upper()}:\n")
            for result in cat_results:
                status_icon = "✅" if result['status'] == 'passed' else "❌" if result['status'] == 'failed' else "⚠️"
                f.write(f"  {status_icon} {result['test_name']}: {result['message']}\n")
            f.write("\n")
        
        # Recommendations
        recommendations = generate_recommendations(results)
        if recommendations:
            f.write("RECOMMENDATIONS:\n")
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\n")
    
    print(f"📄 Text report saved: {report_file}")

def generate_recommendations(results):
    """Generate recommendations based on test results"""
    recommendations = []
    
    # Analyze failed tests
    failed_tests = [r for r in results if r['status'] in ['failed', 'error']]
    
    if failed_tests:
        failed_categories = set(r.get('category', 'unknown') for r in failed_tests)
        
        if 'admin_routes' in failed_categories:
            recommendations.append("Fix admin route registration and blueprint issues")
        
        if 'dropdown_menu' in failed_categories:
            recommendations.append("Check dropdown menu JavaScript and HTML structure")
        
        if 'authentication' in failed_categories:
            recommendations.append("Review authentication and session management")
        
        if 'server_config' in failed_categories:
            recommendations.append("Fix server configuration and URL mapping issues")
    
    # Analyze specific patterns
    admin_route_failures = [r for r in failed_tests if r.get('category') == 'admin_routes']
    if admin_route_failures:
        route_failures = [r for r in admin_route_failures if 'route' in r['test_name'].lower()]
        if route_failures:
            recommendations.append("Check blueprint deferred functions registration")
    
    # General recommendations
    passed_count = len([r for r in results if r['status'] == 'passed'])
    if passed_count == len(results):
        recommendations.append("All tests passed - system is healthy")
    elif passed_count / len(results) < 0.5:
        recommendations.append("Major issues detected - comprehensive debugging required")
    else:
        recommendations.append("Some issues detected - focus on failed tests")
    
    return recommendations

def print_summary(results):
    """Print test summary"""
    total_tests = len(results)
    passed = len([r for r in results if r['status'] == 'passed'])
    failed = len([r for r in results if r['status'] == 'failed'])
    skipped = len([r for r in results if r['status'] == 'skipped'])
    errors = len([r for r in results if r['status'] == 'error'])
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️ Skipped: {skipped}")
    print(f"🚫 Errors: {errors}")
    print(f"📈 Success Rate: {(passed/total_tests*100):.1f}%")
    
    if failed > 0 or errors > 0:
        print(f"\n🔍 ISSUES FOUND:")
        failed_tests = [r for r in results if r['status'] in ['failed', 'error']]
        for test in failed_tests[:5]:  # Show first 5 issues
            status_icon = "❌" if test['status'] == 'failed' else "🚫"
            print(f"  {status_icon} {test['test_name']}: {test['message']}")
        
        if len(failed_tests) > 5:
            print(f"  ... and {len(failed_tests) - 5} more issues")

if __name__ == '__main__':
    main()
