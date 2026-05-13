"""
Comprehensive Infrastructure Debugging Script

This script tests all newly added infrastructure systems:
- Email delivery optimization and queue monitoring
- Search performance optimization
- Real-time infrastructure monitoring and load balancing
- Email analytics and monitoring systems
- Push notification monitoring and mobile integration
- Notification export capabilities
- API documentation endpoints
"""

import sys
import os
import time
import json
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import importlib.util

# Add the project root to Python path
sys.path.insert(0, '/home/robbie/Desktop/repo-forum')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InfrastructureDebugger:
    """Comprehensive infrastructure debugging system"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.utcnow()
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def run_all_tests(self):
        """Run all infrastructure tests"""
        logger.info("🚀 Starting Comprehensive Infrastructure Debugging")
        logger.info("=" * 60)
        
        test_methods = [
            self.test_email_optimization,
            self.test_search_optimization,
            self.test_realtime_monitoring,
            self.test_email_analytics,
            self.test_push_monitoring,
            self.test_export_system,
            self.test_api_documentation
        ]
        
        for test_method in test_methods:
            try:
                logger.info(f"\n🔍 Testing {test_method.__name__}")
                logger.info("-" * 40)
                test_method()
                logger.info(f"✅ {test_method.__name__} completed")
            except Exception as e:
                logger.error(f"❌ {test_method.__name__} failed: {str(e)}")
                logger.error(traceback.format_exc())
                self.test_results[test_method.__name__] = {
                    'status': 'FAILED',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
        
        self.generate_final_report()
    
    def test_email_optimization(self):
        """Test email delivery optimization and queue monitoring"""
        try:
            # Test import
            from app.email.optimized_delivery import EmailDeliveryOptimizer
            from app.email.queue_monitor import EmailQueueMonitor
            
            self.test_results['email_optimization_import'] = {
                'status': 'PASSED',
                'message': 'Email optimization modules imported successfully'
            }
            
            # Test EmailDeliveryOptimizer initialization
            try:
                optimizer = EmailDeliveryOptimizer()
                self.test_results['email_optimizer_init'] = {
                    'status': 'PASSED',
                    'message': 'EmailDeliveryOptimizer initialized successfully'
                }
            except Exception as e:
                self.test_results['email_optimizer_init'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test EmailQueueMonitor initialization
            try:
                monitor = EmailQueueMonitor()
                self.test_results['email_queue_monitor_init'] = {
                    'status': 'PASSED',
                    'message': 'EmailQueueMonitor initialized successfully'
                }
            except Exception as e:
                self.test_results['email_queue_monitor_init'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test optimization methods
            try:
                test_email_data = {
                    'to': 'test@example.com',
                    'subject': 'Test Email',
                    'content': 'Test content',
                    'priority': 'normal'
                }
                
                result = optimizer.optimize_delivery(test_email_data)
                if result.get('success', False):
                    self.test_results['email_optimization'] = {
                        'status': 'PASSED',
                        'message': 'Email optimization working correctly'
                    }
                else:
                    self.test_results['email_optimization'] = {
                        'status': 'FAILED',
                        'error': result.get('error', 'Unknown error')
                    }
            except Exception as e:
                self.test_results['email_optimization'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test queue monitoring
            try:
                queue_status = monitor.get_queue_status()
                if 'queue_sizes' in queue_status:
                    self.test_results['queue_monitoring'] = {
                        'status': 'PASSED',
                        'message': 'Queue monitoring working correctly'
                    }
                else:
                    self.test_results['queue_monitoring'] = {
                        'status': 'FAILED',
                        'error': 'Queue status not retrieved properly'
                    }
            except Exception as e:
                self.test_results['queue_monitoring'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            logger.info("✅ Email optimization system tests completed")
            
        except Exception as e:
            logger.error(f"❌ Email optimization test failed: {str(e)}")
            raise
    
    def test_search_optimization(self):
        """Test search performance optimization"""
        try:
            # Test import
            from app.notifications.search_optimization import SearchOptimizer
            
            self.test_results['search_optimization_import'] = {
                'status': 'PASSED',
                'message': 'Search optimization module imported successfully'
            }
            
            # Test SearchOptimizer initialization
            try:
                optimizer = SearchOptimizer()
                self.test_results['search_optimizer_init'] = {
                    'status': 'PASSED',
                    'message': 'SearchOptimizer initialized successfully'
                }
            except Exception as e:
                self.test_results['search_optimizer_init'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test search optimization
            try:
                search_params = {
                    'search_query': 'test',
                    'types': ['comment', 'message'],
                    'page': 1,
                    'per_page': 10
                }
                
                result = optimizer.optimize_search_query(1, search_params)
                if result.get('success', False):
                    self.test_results['search_optimization'] = {
                        'status': 'PASSED',
                        'message': 'Search optimization working correctly'
                    }
                else:
                    self.test_results['search_optimization'] = {
                        'status': 'FAILED',
                        'error': result.get('error', 'Unknown error')
                    }
            except Exception as e:
                self.test_results['search_optimization'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test performance report
            try:
                report = optimizer.get_search_performance_report()
                if 'metrics' in report:
                    self.test_results['search_performance_report'] = {
                        'status': 'PASSED',
                        'message': 'Search performance report generated successfully'
                    }
                else:
                    self.test_results['search_performance_report'] = {
                        'status': 'FAILED',
                        'error': 'Performance report not generated properly'
                    }
            except Exception as e:
                self.test_results['search_performance_report'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            logger.info("✅ Search optimization system tests completed")
            
        except Exception as e:
            logger.error(f"❌ Search optimization test failed: {str(e)}")
            raise
    
    def test_realtime_monitoring(self):
        """Test real-time infrastructure monitoring and load balancing"""
        try:
            # Test import
            from app.infrastructure.realtime_monitoring import RealtimeMonitor, LoadBalancer
            
            self.test_results['realtime_monitoring_import'] = {
                'status': 'PASSED',
                'message': 'Realtime monitoring modules imported successfully'
            }
            
            # Test RealtimeMonitor initialization
            try:
                monitor = RealtimeMonitor()
                self.test_results['realtime_monitor_init'] = {
                    'status': 'PASSED',
                    'message': 'RealtimeMonitor initialized successfully'
                }
            except Exception as e:
                self.test_results['realtime_monitor_init'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test LoadBalancer initialization
            try:
                load_balancer = LoadBalancer()
                self.test_results['load_balancer_init'] = {
                    'status': 'PASSED',
                    'message': 'LoadBalancer initialized successfully'
                }
            except Exception as e:
                self.test_results['load_balancer_init'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test infrastructure status
            try:
                status = monitor.get_infrastructure_status()
                if 'current_server' in status:
                    self.test_results['infrastructure_status'] = {
                        'status': 'PASSED',
                        'message': 'Infrastructure status retrieved successfully'
                    }
                else:
                    self.test_results['infrastructure_status'] = {
                        'status': 'FAILED',
                        'error': 'Infrastructure status not retrieved properly'
                    }
            except Exception as e:
                self.test_results['infrastructure_status'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test performance report
            try:
                report = monitor.get_performance_report(24)
                if 'averages' in report:
                    self.test_results['realtime_performance_report'] = {
                        'status': 'PASSED',
                        'message': 'Realtime performance report generated successfully'
                    }
                else:
                    self.test_results['realtime_performance_report'] = {
                        'status': 'FAILED',
                        'error': 'Performance report not generated properly'
                    }
            except Exception as e:
                self.test_results['realtime_performance_report'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            logger.info("✅ Real-time monitoring system tests completed")
            
        except Exception as e:
            logger.error(f"❌ Real-time monitoring test failed: {str(e)}")
            raise
    
    def test_email_analytics(self):
        """Test email analytics and monitoring systems"""
        try:
            # Test import
            from app.email.analytics_system import EmailAnalytics, EmailMetrics
            
            self.test_results['email_analytics_import'] = {
                'status': 'PASSED',
                'message': 'Email analytics modules imported successfully'
            }
            
            # Test EmailAnalytics initialization
            try:
                analytics = EmailAnalytics()
                self.test_results['email_analytics_init'] = {
                    'status': 'PASSED',
                    'message': 'EmailAnalytics initialized successfully'
                }
            except Exception as e:
                self.test_results['email_analytics_init'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test analytics dashboard
            try:
                dashboard = analytics.get_analytics_dashboard('7_days')
                if 'metrics' in dashboard:
                    self.test_results['email_analytics_dashboard'] = {
                        'status': 'PASSED',
                        'message': 'Email analytics dashboard generated successfully'
                    }
                else:
                    self.test_results['email_analytics_dashboard'] = {
                        'status': 'FAILED',
                        'error': 'Analytics dashboard not generated properly'
                    }
            except Exception as e:
                self.test_results['email_analytics_dashboard'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test event tracking
            try:
                analytics.track_email_event('test_email_123', 'sent', user_id=1)
                self.test_results['email_event_tracking'] = {
                    'status': 'PASSED',
                    'message': 'Email event tracking working correctly'
                }
            except Exception as e:
                self.test_results['email_event_tracking'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test report generation
            try:
                report = analytics.generate_report('weekly')
                if 'report_type' in report:
                    self.test_results['email_report_generation'] = {
                        'status': 'PASSED',
                        'message': 'Email report generated successfully'
                    }
                else:
                    self.test_results['email_report_generation'] = {
                        'status': 'FAILED',
                        'error': 'Report not generated properly'
                    }
            except Exception as e:
                self.test_results['email_report_generation'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            logger.info("✅ Email analytics system tests completed")
            
        except Exception as e:
            logger.error(f"❌ Email analytics test failed: {str(e)}")
            raise
    
    def test_push_monitoring(self):
        """Test push notification monitoring and mobile integration"""
        try:
            # Test import
            from app.notifications.push_monitoring import PushNotificationMonitor, PushMetrics, PlatformMetrics
            
            self.test_results['push_monitoring_import'] = {
                'status': 'PASSED',
                'message': 'Push monitoring modules imported successfully'
            }
            
            # Test PushNotificationMonitor initialization
            try:
                monitor = PushNotificationMonitor()
                self.test_results['push_monitor_init'] = {
                    'status': 'PASSED',
                    'message': 'PushNotificationMonitor initialized successfully'
                }
            except Exception as e:
                self.test_results['push_monitor_init'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test push dashboard
            try:
                dashboard = monitor.get_push_dashboard('7_days')
                if 'overall_metrics' in dashboard:
                    self.test_results['push_dashboard'] = {
                        'status': 'PASSED',
                        'message': 'Push dashboard generated successfully'
                    }
                else:
                    self.test_results['push_dashboard'] = {
                        'status': 'FAILED',
                        'error': 'Push dashboard not generated properly'
                    }
            except Exception as e:
                self.test_results['push_dashboard'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test event tracking
            try:
                monitor.track_push_event('test_push_123', 'device_123', 'ios', 'delivered', user_id=1)
                self.test_results['push_event_tracking'] = {
                    'status': 'PASSED',
                    'message': 'Push event tracking working correctly'
                }
            except Exception as e:
                self.test_results['push_event_tracking'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test mobile SDK config
            try:
                config = monitor.generate_mobile_sdk_config()
                if 'api_endpoints' in config:
                    self.test_results['mobile_sdk_config'] = {
                        'status': 'PASSED',
                        'message': 'Mobile SDK config generated successfully'
                    }
                else:
                    self.test_results['mobile_sdk_config'] = {
                        'status': 'FAILED',
                        'error': 'SDK config not generated properly'
                    }
            except Exception as e:
                self.test_results['mobile_sdk_config'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            logger.info("✅ Push monitoring system tests completed")
            
        except Exception as e:
            logger.error(f"❌ Push monitoring test failed: {str(e)}")
            raise
    
    def test_export_system(self):
        """Test notification export capabilities"""
        try:
            # Test import
            from app.notifications.export_system import NotificationExportSystem, ExportConfig
            
            self.test_results['export_system_import'] = {
                'status': 'PASSED',
                'message': 'Export system modules imported successfully'
            }
            
            # Test NotificationExportSystem initialization
            try:
                export_system = NotificationExportSystem()
                self.test_results['export_system_init'] = {
                    'status': 'PASSED',
                    'message': 'NotificationExportSystem initialized successfully'
                }
            except Exception as e:
                self.test_results['export_system_init'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test export configuration
            try:
                config = ExportConfig(
                    format='json',
                    filters={'type': 'comment'},
                    fields=['id', 'type', 'content'],
                    date_range={'type': 'last_7_days'}
                )
                self.test_results['export_config'] = {
                    'status': 'PASSED',
                    'message': 'Export configuration created successfully'
                }
            except Exception as e:
                self.test_results['export_config'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test export templates
            try:
                templates = export_system.get_export_templates()
                if isinstance(templates, list):
                    self.test_results['export_templates'] = {
                        'status': 'PASSED',
                        'message': 'Export templates retrieved successfully'
                    }
                else:
                    self.test_results['export_templates'] = {
                        'status': 'FAILED',
                        'error': 'Export templates not retrieved properly'
                    }
            except Exception as e:
                self.test_results['export_templates'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            # Test export statistics
            try:
                stats = export_system.get_export_statistics(30)
                if 'period_days' in stats:
                    self.test_results['export_statistics'] = {
                        'status': 'PASSED',
                        'message': 'Export statistics retrieved successfully'
                    }
                else:
                    self.test_results['export_statistics'] = {
                        'status': 'FAILED',
                        'error': 'Export statistics not retrieved properly'
                    }
            except Exception as e:
                self.test_results['export_statistics'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
                raise
            
            logger.info("✅ Export system tests completed")
            
        except Exception as e:
            logger.error(f"❌ Export system test failed: {str(e)}")
            raise
    
    def test_api_documentation(self):
        """Test API documentation endpoints"""
        try:
            # Check if documentation files exist
            doc_file = '/home/robbie/Desktop/repo-forum/app/docs/COMPREHENSIVE_API_DOCUMENTATION.md'
            
            if os.path.exists(doc_file):
                self.test_results['api_documentation_exists'] = {
                    'status': 'PASSED',
                    'message': 'API documentation file exists'
                }
                
                # Check file content
                with open(doc_file, 'r') as f:
                    content = f.read()
                    if len(content) > 1000:  # Check if file has substantial content
                        self.test_results['api_documentation_content'] = {
                            'status': 'PASSED',
                            'message': 'API documentation has substantial content'
                        }
                    else:
                        self.test_results['api_documentation_content'] = {
                            'status': 'FAILED',
                            'error': 'API documentation content too short'
                        }
                    
                    # Check for key sections
                    required_sections = [
                        'WebSocket API',
                        'Email API',
                        'Preferences API',
                        'Search API'
                    ]
                    
                    missing_sections = []
                    for section in required_sections:
                        if section not in content:
                            missing_sections.append(section)
                    
                    if not missing_sections:
                        self.test_results['api_documentation_sections'] = {
                            'status': 'PASSED',
                            'message': 'All required API sections present'
                        }
                    else:
                        self.test_results['api_documentation_sections'] = {
                            'status': 'FAILED',
                            'error': f'Missing sections: {missing_sections}'
                        }
            else:
                self.test_results['api_documentation_exists'] = {
                    'status': 'FAILED',
                    'error': 'API documentation file does not exist'
                }
            
            logger.info("✅ API documentation tests completed")
            
        except Exception as e:
            logger.error(f"❌ API documentation test failed: {str(e)}")
            raise
    
    def generate_final_report(self):
        """Generate final debugging report"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 COMPREHENSIVE INFRASTRUCTURE DEBUGGING REPORT")
        logger.info("=" * 60)
        
        # Count test results
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r['status'] == 'PASSED'])
        failed_tests = total_tests - passed_tests
        
        # Calculate success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        # Show detailed results
        logger.info("\n📋 Detailed Test Results:")
        logger.info("-" * 40)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            logger.info(f"{status_icon} {test_name}: {result['message']}")
            if result['status'] == 'FAILED':
                logger.info(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Summary by category
        logger.info("\n📈 Test Summary by System:")
        logger.info("-" * 40)
        
        categories = {
            'Email Optimization': ['email_optimization_import', 'email_optimizer_init', 'email_optimization', 'queue_monitoring'],
            'Search Optimization': ['search_optimization_import', 'search_optimizer_init', 'search_optimization', 'search_performance_report'],
            'Real-time Monitoring': ['realtime_monitoring_import', 'realtime_monitor_init', 'load_balancer_init', 'infrastructure_status', 'realtime_performance_report'],
            'Email Analytics': ['email_analytics_import', 'email_analytics_init', 'email_analytics_dashboard', 'email_event_tracking', 'email_report_generation'],
            'Push Monitoring': ['push_monitoring_import', 'push_monitor_init', 'push_dashboard', 'push_event_tracking', 'mobile_sdk_config'],
            'Export System': ['export_system_import', 'export_system_init', 'export_config', 'export_templates', 'export_statistics'],
            'API Documentation': ['api_documentation_exists', 'api_documentation_content', 'api_documentation_sections']
        }
        
        for category, test_names in categories.items():
            category_passed = 0
            category_total = 0
            
            for test_name in test_names:
                if test_name in self.test_results:
                    category_total += 1
                    if self.test_results[test_name]['status'] == 'PASSED':
                        category_passed += 1
            
            if category_total > 0:
                category_rate = (category_passed / category_total * 100)
                status_icon = "✅" if category_rate == 100 else "⚠️" if category_rate >= 70 else "❌"
                logger.info(f"{status_icon} {category}: {category_passed}/{category_total} ({category_rate:.1f}%)")
        
        # Recommendations
        logger.info("\n💡 Recommendations:")
        logger.info("-" * 40)
        
        if success_rate == 100:
            logger.info("🎉 All systems are working perfectly!")
        elif success_rate >= 80:
            logger.info("✅ Most systems are working well. Check failed tests for minor issues.")
        elif success_rate >= 60:
            logger.info("⚠️ Some systems have issues. Review failed tests and fix critical problems.")
        else:
            logger.info("❌ Multiple systems have issues. Immediate attention required.")
        
        # Failed tests details
        failed_tests_list = [(name, result) for name, result in self.test_results.items() if result['status'] == 'FAILED']
        
        if failed_tests_list:
            logger.info("\n🔧 Failed Tests - Action Required:")
            logger.info("-" * 40)
            
            for test_name, result in failed_tests_list:
                logger.info(f"❌ {test_name}")
                logger.info(f"   Error: {result.get('error', 'Unknown error')}")
                if 'traceback' in result:
                    logger.info(f"   Traceback: {result['traceback'][:200]}...")
        
        # Save report to file
        try:
            report_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': success_rate,
                'test_results': self.test_results,
                'duration': str(datetime.utcnow() - self.start_time)
            }
            
            with open('/home/robbie/Desktop/repo-forum/infrastructure_debug_report.json', 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"\n📄 Detailed report saved to: infrastructure_debug_report.json")
            
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
        
        logger.info("\n🏁 Infrastructure debugging completed!")

if __name__ == '__main__':
    debugger = InfrastructureDebugger()
    debugger.run_all_tests()
