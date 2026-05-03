"""
Parallel Test Execution Support for Repo-Forum Project
Provides multi-threaded test execution capabilities for improved performance.
"""

import threading
import queue
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import traceback

@dataclass
class ParallelTestResult:
    """Result of a parallel test execution"""
    test_name: str
    category: str
    status: str
    message: str
    details: Optional[Dict[str, Any]]
    timestamp: datetime
    execution_time: float
    worker_id: int

class ParallelTestExecutor:
    """Manages parallel execution of test categories"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.results = []
        self.execution_stats = {}
        self.start_time = None
        self.end_time = None
    
    def execute_category_parallel(self, category: str, test_classes: List[tuple]) -> List[ParallelTestResult]:
        """Execute tests for a category in parallel"""
        self.start_time = datetime.utcnow()
        category_results = []
        
        print(f"🔄 Running {category.upper()} tests in parallel with {self.max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all test classes to the executor
            future_to_test = {}
            worker_id = 0
            
            for test_class_name in test_classes:
                future = executor.submit(self._execute_test_class, test_class_name, category, worker_id)
                future_to_test[future] = (test_class_name, worker_id)
                worker_id = (worker_id + 1) % self.max_workers
            
            # Collect results as they complete
            for future in as_completed(future_to_test):
                test_class_name, worker_id = future_to_test[future]
                
                try:
                    result = future.result()
                    category_results.append(result)
                    print(f"✅ Completed {test_class_name} on worker {worker_id}")
                except Exception as e:
                    # Create error result
                    error_result = ParallelTestResult(
                        test_name=test_class_name,
                        category=category,
                        status="error",
                        message=str(e),
                        details={"traceback": traceback.format_exc()},
                        timestamp=datetime.utcnow(),
                        execution_time=0.0,
                        worker_id=worker_id
                    )
                    category_results.append(error_result)
                    print(f"❌ Error in {test_class_name} on worker {worker_id}: {e}")
        
        self.end_time = datetime.utcnow()
        self.execution_stats[category] = {
            'total_tests': len(category_results),
            'passed': len([r for r in category_results if r.status == 'passed']),
            'failed': len([r for r in category_results if r.status == 'failed']),
            'errors': len([r for r in category_results if r.status == 'error']),
            'execution_time': (self.end_time - self.start_time).total_seconds()
        }
        
        return category_results
    
    def _execute_test_class(self, test_class_name: str, category: str, worker_id: int) -> ParallelTestResult:
        """Execute a single test class"""
        start_time = time.time()
        
        try:
            # Import and initialize test class
            from app.test import TestFramework
            framework = TestFramework()
            
            # Import the test class based on name
            test_class = self._import_test_class(test_class_name)
            test_instance = test_class(framework)
            
            # Execute all tests in the class
            if hasattr(test_instance, 'run_all_tests'):
                results = test_instance.run_all_tests()
                
                execution_time = time.time() - start_time
                
                # Count results
                passed = len([r for r in results if r['status'] == 'passed'])
                failed = len([r for r in results if r['status'] == 'failed'])
                errors = len([r for r in results if r['status'] == 'error'])
                
                return ParallelTestResult(
                    test_name=test_class_name,
                    category=category,
                    status="passed" if errors == 0 else "failed",
                    message=f"Passed: {passed}, Failed: {failed}, Errors: {errors}",
                    details={"results": results, "total_tests": len(results)},
                    timestamp=datetime.utcnow(),
                    execution_time=execution_time,
                    worker_id=worker_id
                )
            else:
                raise AttributeError(f"Method run_all_tests not found in {test_class_name}")
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            return ParallelTestResult(
                test_name=test_class_name,
                category=category,
                status="error",
                message=str(e),
                details={"traceback": traceback.format_exc()},
                timestamp=datetime.utcnow(),
                execution_time=execution_time,
                worker_id=worker_id
            )
    
    def _import_test_class(self, class_name: str):
        """Import test class by name"""
        # Map class names to their modules
        class_mappings = {
            'AdminRoutesTest': 'app.test.tests.admin_routes_test',
            'AdminFormsTest': 'app.test.tests.admin_forms_test',
            'AuthTest': 'app.test.tests.auth_test',
            'SessionTest': 'app.test.tests.session_test',
            'ForumTest': 'app.test.tests.forum_test',
            'PostTest': 'app.test.tests.post_test',
            'CommentTest': 'app.test.tests.comment_test',
            'APITest': 'app.test.tests.api_test',
            'APISecurityTest': 'app.test.tests.api_security_test',
            'UserTest': 'app.test.tests.user_test',
            'ProfileTest': 'app.test.tests.profile_test',
            'MessageTest': 'app.test.tests.message_test',
            'NotificationTest': 'app.test.tests.notification_test',
            'DatabaseTest': 'app.test.tests.database_test',
            'ModelTest': 'app.test.tests.model_test',
            'SecurityTest': 'app.test.tests.security_test',
            'CSRFTest': 'app.test.tests.csrf_test',
            'TemplateTest': 'app.test.tests.template_test',
            'UITest': 'app.test.tests.ui_test',
            'IntegrationTest': 'app.test.tests.integration_test',
            'PerformanceTest': 'app.test.tests.performance_test'
        }
        
        if class_name not in class_mappings:
            raise ImportError(f"Unknown test class: {class_name}")
        
        module_name = class_mappings[class_name]
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)
    
    def execute_all_categories_parallel(self, category_map: Dict[str, List[tuple]]) -> Dict[str, List[ParallelTestResult]]:
        """Execute all test categories in parallel"""
        print(f"🚀 Starting parallel execution of {len(category_map)} categories...")
        
        all_results = {}
        
        # Execute categories one by one (could be further parallelized)
        for category, test_classes in category_map.items():
            print(f"\n{'='*60}")
            print(f"🔄 Executing category: {category}")
            print(f"{'='*60}")
            
            category_results = self.execute_category_parallel(category, test_classes)
            all_results[category] = category_results
            
            # Print category summary
            passed = len([r for r in category_results if r.status == 'passed'])
            failed = len([r for r in category_results if r.status == 'failed'])
            errors = len([r for r in category_results if r.status == 'error'])
            
            print(f"\n📊 {category.upper()} Summary:")
            print(f"   Total: {len(category_results)}")
            print(f"   Passed: {passed}")
            print(f"   Failed: {failed}")
            print(f"   Errors: {errors}")
            print(f"   Time: {self.execution_stats[category]['execution_time']:.2f}s")
        
        return all_results
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of parallel execution"""
        total_tests = sum(stats['total_tests'] for stats in self.execution_stats.values())
        total_passed = sum(stats['passed'] for stats in self.execution_stats.values())
        total_failed = sum(stats['failed'] for stats in self.execution_stats.values())
        total_errors = sum(stats['errors'] for stats in self.execution_stats.values())
        total_time = sum(stats['execution_time'] for stats in self.execution_stats.values())
        
        return {
            'total_categories': len(self.execution_stats),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_errors': total_errors,
            'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'total_execution_time': total_time,
            'max_workers': self.max_workers,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'category_stats': self.execution_stats
        }

class ParallelTestRunner:
    """Enhanced test runner with parallel execution capabilities"""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ParallelTestExecutor(max_workers)
        self.category_map = {}
        self._setup_category_map()
    
    def _setup_category_map(self):
        """Setup the mapping of categories to test classes"""
        self.category_map = {
            'admin': [
                'AdminRoutesTest',
                'AdminFormsTest'
            ],
            'auth': [
                'AuthTest',
                'SessionTest'
            ],
            'forum': [
                'ForumTest',
                'PostTest',
                'CommentTest'
            ],
            'api': [
                'APITest',
                'APISecurityTest'
            ],
            'user': [
                'UserTest',
                'ProfileTest'
            ],
            'message': [
                'MessageTest'
            ],
            'notification': [
                'NotificationTest'
            ],
            'database': [
                'DatabaseTest',
                'ModelTest'
            ],
            'security': [
                'SecurityTest',
                'CSRFTest'
            ],
            'templates': [
                'TemplateTest',
                'UITest'
            ],
            'integration': [
                'IntegrationTest'
            ],
            'performance': [
                'PerformanceTest'
            ]
        }
    
    def run_parallel_tests(self, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run tests in parallel for specified categories or all categories"""
        if categories:
            # Run only specified categories
            filtered_map = {cat: tests for cat, tests in self.category_map.items() if cat in categories}
            results = self.executor.execute_all_categories_parallel(filtered_map)
        else:
            # Run all categories
            results = self.executor.execute_all_categories_parallel(self.category_map)
        
        summary = self.executor.get_execution_summary()
        
        return {
            'results': results,
            'summary': summary
        }
    
    def run_category_parallel(self, category: str) -> List[ParallelTestResult]:
        """Run tests for a specific category in parallel"""
        if category not in self.category_map:
            raise ValueError(f"Unknown category: {category}")
        
        test_classes = self.category_map[category]
        return self.executor.execute_category_parallel(category, test_classes)
    
    def generate_parallel_report(self, results: Dict[str, Any], output_dir: str) -> str:
        """Generate a comprehensive parallel execution report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{output_dir}/parallel_test_report_{timestamp}.json"
        
        report_data = {
            'execution_type': 'parallel',
            'timestamp': datetime.now().isoformat(),
            'max_workers': self.executor.max_workers,
            'summary': results['summary'],
            'results_by_category': {},
            'performance_analysis': self._analyze_performance(results['results'])
        }
        
        # Convert results to serializable format
        for category, category_results in results['results'].items():
            report_data['results_by_category'][category] = [
                {
                    'test_name': result.test_name,
                    'category': result.category,
                    'status': result.status,
                    'message': result.message,
                    'details': result.details,
                    'timestamp': result.timestamp.isoformat(),
                    'execution_time': result.execution_time,
                    'worker_id': result.worker_id
                }
                for result in category_results
            ]
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return report_file
    
    def _analyze_performance(self, results: Dict[str, List[ParallelTestResult]]) -> Dict[str, Any]:
        """Analyze performance of parallel execution"""
        analysis = {
            'slowest_tests': [],
            'fastest_tests': [],
            'worker_distribution': {},
            'category_performance': {}
        }
        
        all_tests = []
        for category, category_results in results.items():
            category_times = [r.execution_time for r in category_results]
            
            analysis['category_performance'][category] = {
                'avg_time': sum(category_times) / len(category_times) if category_times else 0,
                'max_time': max(category_times) if category_times else 0,
                'min_time': min(category_times) if category_times else 0,
                'total_tests': len(category_results)
            }
            
            all_tests.extend(category_results)
        
        # Find slowest and fastest tests
        sorted_tests = sorted(all_tests, key=lambda x: x.execution_time, reverse=True)
        analysis['slowest_tests'] = [
            {
                'test_name': t.test_name,
                'execution_time': t.execution_time,
                'worker_id': t.worker_id
            }
            for t in sorted_tests[:10]
        ]
        
        analysis['fastest_tests'] = [
            {
                'test_name': t.test_name,
                'execution_time': t.execution_time,
                'worker_id': t.worker_id
            }
            for t in sorted_tests[-10:]
        ]
        
        # Analyze worker distribution
        worker_counts = {}
        for test in all_tests:
            worker_id = test.worker_id
            worker_counts[worker_id] = worker_counts.get(worker_id, 0) + 1
        
        analysis['worker_distribution'] = worker_counts
        
        return analysis

# Utility function for easy parallel execution
def run_tests_parallel(max_workers: int = 4, categories: Optional[List[str]] = None) -> Dict[str, Any]:
    """Utility function to run tests in parallel"""
    runner = ParallelTestRunner(max_workers)
    return runner.run_parallel_tests(categories)
