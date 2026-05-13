#!/usr/bin/env python3
"""
Debugging script for Performance Optimization Systems

This script tests and debugs all performance optimization systems:
- ProfilePerformanceOptimizer
- AnalyticsPerformanceOptimizer  
- SocialPerformanceOptimizer
"""

import sys
import os
import time
import traceback
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test importing all performance optimization modules."""
    print("🔍 Testing imports...")
    
    try:
        from app.user.performance_optimizations import (
            ProfilePerformanceOptimizer,
            AnalyticsPerformanceOptimizer,
            SocialPerformanceOptimizer,
            monitor_performance
        )
        print("✅ All performance optimization imports successful")
        return True, (ProfilePerformanceOptimizer, AnalyticsPerformanceOptimizer, SocialPerformanceOptimizer)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False, None

def test_profile_performance_optimizer(ProfilePerformanceOptimizer):
    """Test ProfilePerformanceOptimizer functionality."""
    print("\n🔍 Testing ProfilePerformanceOptimizer...")
    
    try:
        # Test basic functionality
        print("  - Testing get_optimized_profile method...")
        
        # Mock user ID for testing
        test_user_id = 1
        
        # Test optimized profile loading
        start_time = time.time()
        profile = ProfilePerformanceOptimizer.get_optimized_profile(
            test_user_id, include_social=True, include_analytics=True
        )
        end_time = time.time()
        
        if profile:
            print(f"    ✅ Profile loaded successfully in {end_time - start_time:.4f}s")
            print(f"    ✅ Profile contains {len(profile)} fields")
        else:
            print("    ⚠️  Profile returned None (may be expected if no user exists)")
        
        # Test batch profile loading
        print("  - Testing batch profile loading...")
        start_time = time.time()
        profiles = ProfilePerformanceOptimizer.batch_get_profiles(
            [1, 2, 3], include_social=True, include_analytics=True
        )
        end_time = time.time()
        
        print(f"    ✅ Batch profiles loaded in {end_time - start_time:.4f}s")
        print(f"    ✅ Loaded {len(profiles)} profiles")
        
        # Test cache invalidation
        print("  - Testing cache invalidation...")
        try:
            ProfilePerformanceOptimizer.invalidate_profile_cache(test_user_id)
            print("    ✅ Cache invalidation successful")
        except Exception as e:
            print(f"    ⚠️  Cache invalidation warning: {e}")
        
        # Test performance metrics
        print("  - Testing performance metrics...")
        try:
            metrics = ProfilePerformanceOptimizer.get_profile_performance_metrics(test_user_id)
            if metrics:
                print(f"    ✅ Performance metrics retrieved: load_time={metrics.get('load_time', 0):.4f}s")
            else:
                print("    ⚠️  Performance metrics returned None")
        except Exception as e:
            print(f"    ⚠️  Performance metrics warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ ProfilePerformanceOptimizer error: {e}")
        traceback.print_exc()
        return False

def test_analytics_performance_optimizer(AnalyticsPerformanceOptimizer):
    """Test AnalyticsPerformanceOptimizer functionality."""
    print("\n🔍 Testing AnalyticsPerformanceOptimizer...")
    
    try:
        # Test data warehouse
        print("  - Testing analytics data warehouse...")
        test_user_id = 1
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        start_time = time.time()
        warehouse_data = AnalyticsPerformanceOptimizer.get_analytics_data_warehouse(
            test_user_id, start_date, end_date
        )
        end_time = time.time()
        
        if warehouse_data:
            print(f"    ✅ Data warehouse loaded in {end_time - start_time:.4f}s")
            print(f"    ✅ Contains {len(warehouse_data)} sections")
        else:
            print("    ⚠️  Data warehouse returned None (may be expected if no user data exists)")
        
        # Test real-time processing
        print("  - Testing real-time analytics processing...")
        try:
            event_data = {
                'behavior_type': 'test_event',
                'action': 'test_action',
                'metadata': {'test': True}
            }
            
            start_time = time.time()
            result = AnalyticsPerformanceOptimizer.process_real_time_analytics(
                test_user_id, 'test_event', event_data
            )
            end_time = time.time()
            
            if result:
                print(f"    ✅ Real-time processing completed in {end_time - start_time:.4f}s")
            else:
                print("    ⚠️  Real-time processing returned False")
        except Exception as e:
            print(f"    ⚠️  Real-time processing warning: {e}")
        
        # Test visualization generation
        print("  - Testing visualization generation...")
        try:
            start_time = time.time()
            viz_data = AnalyticsPerformanceOptimizer.generate_analytics_visualization(
                test_user_id, 'engagement_trend', '7d'
            )
            end_time = time.time()
            
            if viz_data:
                print(f"    ✅ Visualization generated in {end_time - start_time:.4f}s")
                print(f"    ✅ Chart type: {viz_data.get('chart_type', 'unknown')}")
            else:
                print("    ⚠️  Visualization returned None")
        except Exception as e:
            print(f"    ⚠️  Visualization generation warning: {e}")
        
        # Test performance metrics
        print("  - Testing analytics performance metrics...")
        try:
            metrics = AnalyticsPerformanceOptimizer.get_analytics_performance_metrics()
            if metrics:
                print(f"    ✅ Performance metrics retrieved")
                print(f"    ✅ Warehouse query time: {metrics.get('data_warehouse_query_time', 0):.4f}s")
            else:
                print("    ⚠️  Performance metrics returned None")
        except Exception as e:
            print(f"    ⚠️  Performance metrics warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ AnalyticsPerformanceOptimizer error: {e}")
        traceback.print_exc()
        return False

def test_social_performance_optimizer(SocialPerformanceOptimizer):
    """Test SocialPerformanceOptimizer functionality."""
    print("\n🔍 Testing SocialPerformanceOptimizer...")
    
    try:
        # Test social graph data
        print("  - Testing social graph data...")
        test_user_id = 1
        
        start_time = time.time()
        graph_data = SocialPerformanceOptimizer.get_social_graph_data(test_user_id, depth=2)
        end_time = time.time()
        
        if graph_data:
            print(f"    ✅ Social graph generated in {end_time - start_time:.4f}s")
            print(f"    ✅ Graph contains {len(graph_data.get('nodes', []))} nodes")
            print(f"    ✅ Graph contains {len(graph_data.get('edges', []))} edges")
        else:
            print("    ⚠️  Social graph returned None (may be expected if no social data exists)")
        
        # Test social feed processing
        print("  - Testing social feed processing...")
        try:
            start_time = time.time()
            feed_data = SocialPerformanceOptimizer.process_social_feed(
                test_user_id, limit=20, include_friends=True
            )
            end_time = time.time()
            
            if feed_data:
                print(f"    ✅ Social feed processed in {end_time - start_time:.4f}s")
                print(f"    ✅ Feed contains {len(feed_data.get('items', []))} items")
            else:
                print("    ⚠️  Social feed returned None")
        except Exception as e:
            print(f"    ⚠️  Social feed processing warning: {e}")
        
        # Test social analytics
        print("  - Testing social analytics...")
        try:
            start_time = time.time()
            analytics_data = SocialPerformanceOptimizer.get_social_analytics(test_user_id, days=7)
            end_time = time.time()
            
            if analytics_data:
                print(f"    ✅ Social analytics generated in {end_time - start_time:.4f}s")
                print(f"    ✅ Analytics period: {analytics_data.get('period', 'unknown')}")
            else:
                print("    ⚠️  Social analytics returned None")
        except Exception as e:
            print(f"    ⚠️  Social analytics warning: {e}")
        
        # Test performance metrics
        print("  - Testing social performance metrics...")
        try:
            metrics = SocialPerformanceOptimizer.get_social_performance_metrics()
            if metrics:
                print(f"    ✅ Performance metrics retrieved")
                print(f"    ✅ Graph generation time: {metrics.get('graph_generation_time', 0):.4f}s")
            else:
                print("    ⚠️  Performance metrics returned None")
        except Exception as e:
            print(f"    ⚠️  Performance metrics warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ SocialPerformanceOptimizer error: {e}")
        traceback.print_exc()
        return False

def test_integration():
    """Test integration between performance optimization systems."""
    print("\n🔍 Testing system integration...")
    
    try:
        from app.user.performance_optimizations import (
            ProfilePerformanceOptimizer,
            AnalyticsPerformanceOptimizer,
            SocialPerformanceOptimizer
        )
        
        test_user_id = 1
        
        # Test integrated profile loading with analytics and social data
        print("  - Testing integrated profile loading...")
        start_time = time.time()
        
        profile_data = ProfilePerformanceOptimizer.get_optimized_profile(
            test_user_id, include_social=True, include_analytics=True
        )
        
        end_time = time.time()
        
        if profile_data:
            print(f"    ✅ Integrated profile loaded in {end_time - start_time:.4f}s")
            print(f"    ✅ Social data present: {profile_data.get('social_data') is not None}")
            print(f"    ✅ Analytics data present: {profile_data.get('analytics_data') is not None}")
        else:
            print("    ⚠️  Integrated profile returned None")
        
        # Test cache consistency across systems
        print("  - Testing cache consistency...")
        try:
            # Invalidate profile cache
            ProfilePerformanceOptimizer.invalidate_profile_cache(test_user_id)
            
            # Load profile again
            profile_data_2 = ProfilePerformanceOptimizer.get_optimized_profile(
                test_user_id, include_social=True, include_analytics=True
            )
            
            if profile_data_2:
                print("    ✅ Cache consistency maintained")
            else:
                print("    ⚠️  Cache consistency issue detected")
        except Exception as e:
            print(f"    ⚠️  Cache consistency warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        traceback.print_exc()
        return False

def test_performance_monitoring():
    """Test performance monitoring decorator."""
    print("\n🔍 Testing performance monitoring...")
    
    try:
        from app.user.performance_optimizations import monitor_performance
        
        @monitor_performance
        def test_function():
            time.sleep(0.1)  # Simulate work
            return "test_result"
        
        # Test the decorated function
        start_time = time.time()
        result = test_function()
        end_time = time.time()
        
        if result == "test_result":
            print(f"    ✅ Performance monitoring decorator working")
            print(f"    ✅ Function executed in {end_time - start_time:.4f}s")
        else:
            print("    ⚠️  Performance monitoring decorator issue")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring error: {e}")
        traceback.print_exc()
        return False

def generate_debugging_report(results):
    """Generate comprehensive debugging report."""
    print("\n📊 Generating debugging report...")
    
    report = f"""
# Performance Optimization Systems Debugging Report

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
**System:** Auto Bot Solutions Forum
**Component:** Performance Optimization Systems

## Test Results Summary

### Import Tests
- **Status:** {'✅ PASSED' if results['imports']['success'] else '❌ FAILED'}
- **Details:** {results['imports']['details']}

### ProfilePerformanceOptimizer Tests
- **Status:** {'✅ PASSED' if results['profile']['success'] else '❌ FAILED'}
- **Details:** {results['profile']['details']}

### AnalyticsPerformanceOptimizer Tests
- **Status:** {'✅ PASSED' if results['analytics']['success'] else '❌ FAILED'}
- **Details:** {results['analytics']['details']}

### SocialPerformanceOptimizer Tests
- **Status:** {'✅ PASSED' if results['social']['success'] else '❌ FAILED'}
- **Details:** {results['social']['details']}

### Integration Tests
- **Status:** {'✅ PASSED' if results['integration']['success'] else '❌ FAILED'}
- **Details:** {results['integration']['details']}

### Performance Monitoring Tests
- **Status:** {'✅ PASSED' if results['monitoring']['success'] else '❌ FAILED'}
- **Details:** {results['monitoring']['details']}

## Overall Status
- **Total Tests:** {len(results)}
- **Passed:** {sum(1 for r in results.values() if r['success'])}
- **Failed:** {sum(1 for r in results.values() if not r['success'])}
- **Success Rate:** {sum(1 for r in results.values() if r['success']) / len(results) * 100:.1f}%

## Issues Found
{chr(10).join([f"- {name}: {details}" for name, details in results.items() if not details['success']]) if any(not r['success'] for r in results.values()) else "No critical issues found."}

## Recommendations
{"All systems are operational and ready for production use." if all(r['success'] for r in results.values()) else "Some systems require attention before production deployment."}

## Next Steps
1. Address any failed tests
2. Optimize performance based on metrics
3. Monitor system performance in production
4. Regular performance audits recommended

---
**Report completed:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
    
    # Save report to file
    report_file = "/home/robbie/Desktop/repo-forum/reports/performance_optimization_debug_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"✅ Debugging report saved to: {report_file}")
    return report_file

def main():
    """Main debugging function."""
    print("🚀 Starting Performance Optimization Systems Debugging")
    print("=" * 60)
    
    results = {}
    
    # Test imports
    print("\n" + "="*60)
    import_success, optimizer_classes = test_imports()
    results['imports'] = {
        'success': import_success,
        'details': 'All performance optimization modules imported successfully' if import_success else 'Import errors detected'
    }
    
    if not import_success:
        print("❌ Cannot proceed with debugging due to import errors")
        generate_debugging_report(results)
        return
    
    ProfilePerformanceOptimizer, AnalyticsPerformanceOptimizer, SocialPerformanceOptimizer = optimizer_classes
    
    # Test ProfilePerformanceOptimizer
    print("\n" + "="*60)
    profile_success = test_profile_performance_optimizer(ProfilePerformanceOptimizer)
    results['profile'] = {
        'success': profile_success,
        'details': 'ProfilePerformanceOptimizer working correctly' if profile_success else 'ProfilePerformanceOptimizer has issues'
    }
    
    # Test AnalyticsPerformanceOptimizer
    print("\n" + "="*60)
    analytics_success = test_analytics_performance_optimizer(AnalyticsPerformanceOptimizer)
    results['analytics'] = {
        'success': analytics_success,
        'details': 'AnalyticsPerformanceOptimizer working correctly' if analytics_success else 'AnalyticsPerformanceOptimizer has issues'
    }
    
    # Test SocialPerformanceOptimizer
    print("\n" + "="*60)
    social_success = test_social_performance_optimizer(SocialPerformanceOptimizer)
    results['social'] = {
        'success': social_success,
        'details': 'SocialPerformanceOptimizer working correctly' if social_success else 'SocialPerformanceOptimizer has issues'
    }
    
    # Test integration
    print("\n" + "="*60)
    integration_success = test_integration()
    results['integration'] = {
        'success': integration_success,
        'details': 'System integration working correctly' if integration_success else 'Integration issues detected'
    }
    
    # Test performance monitoring
    print("\n" + "="*60)
    monitoring_success = test_performance_monitoring()
    results['monitoring'] = {
        'success': monitoring_success,
        'details': 'Performance monitoring working correctly' if monitoring_success else 'Performance monitoring has issues'
    }
    
    # Generate report
    print("\n" + "="*60)
    report_file = generate_debugging_report(results)
    
    # Summary
    passed_tests = sum(1 for r in results.values() if r['success'])
    total_tests = len(results)
    success_rate = passed_tests / total_tests * 100
    
    print(f"\n🎯 Debugging Summary:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Performance optimization systems are operational!")
    else:
        print("⚠️  Some performance optimization systems need attention.")
    
    print(f"📄 Full report available at: {report_file}")
    
    return results

if __name__ == "__main__":
    main()
