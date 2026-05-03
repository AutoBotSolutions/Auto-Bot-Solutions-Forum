"""
Performance Benchmarking and Monitoring for Repo-Forum Project
Provides comprehensive performance testing and benchmarking capabilities.
"""

import time
import psutil
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from functools import wraps
import statistics

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

@dataclass
class BenchmarkResult:
    """Result of a benchmark test"""
    test_name: str
    metrics: List[PerformanceMetric]
    start_time: datetime
    end_time: datetime
    duration: float
    success: bool
    error: Optional[str] = None

class PerformanceMonitor:
    """Monitors performance during test execution"""
    
    def __init__(self):
        self.metrics = []
        self.benchmarks = []
        self.start_time = None
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 0.1  # seconds
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = datetime.utcnow()
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            self._collect_metrics()
            time.sleep(self.monitor_interval)
    
    def _collect_metrics(self):
        """Collect current performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.metrics.append(PerformanceMetric(
                name="cpu_usage",
                value=cpu_percent,
                unit="percent",
                timestamp=datetime.utcnow()
            ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics.append(PerformanceMetric(
                name="memory_usage",
                value=memory.percent,
                unit="percent",
                timestamp=datetime.utcnow()
            ))
            
            # Process memory
            process = psutil.Process()
            process_memory = process.memory_info()
            self.metrics.append(PerformanceMetric(
                name="process_memory_rss",
                value=process_memory.rss / 1024 / 1024,  # MB
                unit="MB",
                timestamp=datetime.utcnow()
            ))
            
            # Process memory (virtual)
            self.metrics.append(PerformanceMetric(
                name="process_memory_vms",
                value=process_memory.vms / 1024 / 1024,  # MB
                unit="MB",
                timestamp=datetime.utcnow()
            ))
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
    
    def add_metric(self, name: str, value: float, unit: str, metadata: Dict = None):
        """Add a custom metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        self.metrics.append(metric)
    
    def get_metrics_by_name(self, name: str) -> List[PerformanceMetric]:
        """Get all metrics with a specific name"""
        return [m for m in self.metrics if m.name == name]
    
    def get_metric_summary(self, name: str) -> Dict[str, float]:
        """Get summary statistics for a metric"""
        metrics = self.get_metrics_by_name(name)
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0
        }
    
    def clear_metrics(self):
        """Clear all collected metrics"""
        self.metrics.clear()

class BenchmarkRunner:
    """Runs benchmark tests"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.results = []
    
    @contextmanager
    def benchmark(self, test_name: str):
        """Context manager for benchmarking a test"""
        start_time = datetime.utcnow()
        start_perf = time.perf_counter()
        
        # Clear previous metrics for this test
        self.monitor.clear_metrics()
        self.monitor.start_monitoring()
        
        try:
            yield self
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            self.monitor.stop_monitoring()
            
            end_time = datetime.utcnow()
            end_perf = time.perf_counter()
            duration = end_perf - start_perf
            
            # Create benchmark result
            result = BenchmarkResult(
                test_name=test_name,
                metrics=self.monitor.metrics.copy(),
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                error=error
            )
            
            self.results.append(result)
    
    def run_benchmark(self, test_name: str, test_func: Callable, *args, **kwargs):
        """Run a benchmark test"""
        with self.benchmark(test_name):
            return test_func(*args, **kwargs)
    
    def get_results(self) -> List[BenchmarkResult]:
        """Get all benchmark results"""
        return self.results.copy()
    
    def get_result_by_name(self, test_name: str) -> Optional[BenchmarkResult]:
        """Get benchmark result by name"""
        for result in self.results:
            if result.test_name == test_name:
                return result
        return None
    
    def clear_results(self):
        """Clear all benchmark results"""
        self.results.clear()

class PerformanceProfiler:
    """Profiles performance of functions"""
    
    def __init__(self):
        self.profiles = []
    
    @contextmanager
    def profile(self, function_name: str):
        """Context manager for profiling a function"""
        import cProfile
        import io
        import pstats
        
        profiler = cProfile.Profile()
        
        try:
            profiler.enable()
            yield profiler
        finally:
            profiler.disable()
            
            # Save profile data
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats()
            
            profile_data = {
                'function_name': function_name,
                'timestamp': datetime.utcnow(),
                'profile_output': s.getvalue()
            }
            
            self.profiles.append(profile_data)
    
    def profile_function(self, func: Callable, *args, **kwargs):
        """Profile a function"""
        with self.profile(func.__name__):
            return func(*args, **kwargs)
    
    def get_profiles(self) -> List[Dict]:
        """Get all profiles"""
        return self.profiles.copy()
    
    def clear_profiles(self):
        """Clear all profiles"""
        self.profiles.clear()

class PerformanceComparator:
    """Compares performance across multiple runs"""
    
    def __init__(self):
        self.comparisons = []
    
    def add_comparison(self, test_name: str, baseline: BenchmarkResult, 
                      comparison: BenchmarkResult):
        """Add a performance comparison"""
        comparison_data = {
            'test_name': test_name,
            'baseline': baseline,
            'comparison': comparison,
            'timestamp': datetime.utcnow()
        }
        
        # Calculate differences
        comparison_data['duration_diff'] = comparison.duration - baseline.duration
        comparison_data['duration_percent_change'] = (
            (comparison.duration - baseline.duration) / baseline.duration * 100
        )
        
        # Compare metrics
        metric_comparisons = {}
        for baseline_metric in baseline.metrics:
            comparison_metric = next(
                (m for m in comparison.metrics if m.name == baseline_metric.name),
                None
            )
            
            if comparison_metric:
                metric_comparisons[baseline_metric.name] = {
                    'baseline_value': baseline_metric.value,
                    'comparison_value': comparison_metric.value,
                    'difference': comparison_metric.value - baseline_metric.value,
                    'percent_change': (
                        (comparison_metric.value - baseline_metric.value) / 
                        baseline_metric.value * 100
                    ) if baseline_metric.value != 0 else 0
                }
        
        comparison_data['metric_comparisons'] = metric_comparisons
        self.comparisons.append(comparison_data)
    
    def get_comparisons(self) -> List[Dict]:
        """Get all comparisons"""
        return self.comparisons.copy()
    
    def get_regression_report(self) -> Dict[str, Any]:
        """Generate regression report"""
        regressions = []
        improvements = []
        
        for comparison in self.comparisons:
            # Check for performance regressions
            if comparison['duration_percent_change'] > 10:  # 10% slower
                regressions.append({
                    'test_name': comparison['test_name'],
                    'duration_change': comparison['duration_percent_change'],
                    'severity': 'high' if comparison['duration_percent_change'] > 50 else 'medium'
                })
            elif comparison['duration_percent_change'] < -10:  # 10% faster
                improvements.append({
                    'test_name': comparison['test_name'],
                    'duration_change': comparison['duration_percent_change']
                })
        
        return {
            'regressions': regressions,
            'improvements': improvements,
            'total_comparisons': len(self.comparisons),
            'timestamp': datetime.utcnow()
        }

def performance_benchmark(test_name: str = None):
    """Decorator for performance benchmarking"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = test_name or f"{func.__module__}.{func.__name__}"
            
            monitor = PerformanceMonitor()
            runner = BenchmarkRunner(monitor)
            
            return runner.run_benchmark(name, func, *args, **kwargs)
        
        return wrapper
    return decorator

def profile_performance(function_name: str = None):
    """Decorator for performance profiling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = function_name or f"{func.__module__}.{func.__name__}"
            
            profiler = PerformanceProfiler()
            return profiler.profile_function(func, *args, **kwargs)
        
        return wrapper
    return decorator

class PerformanceReporter:
    """Generates performance reports"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.runner = BenchmarkRunner(self.monitor)
        self.profiler = PerformanceProfiler()
        self.comparator = PerformanceComparator()
    
    def generate_performance_report(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not results:
            return {'error': 'No performance data available'}
        
        # Calculate overall statistics
        durations = [r.duration for r in results if r.success]
        success_rate = len([r for r in results if r.success]) / len(results) * 100
        
        # Metric summaries
        metric_summaries = {}
        all_metrics = []
        for result in results:
            all_metrics.extend(result.metrics)
        
        metric_names = list(set(m.name for m in all_metrics))
        for name in metric_names:
            metric_summaries[name] = self.monitor.get_metric_summary(name)
        
        # Identify slowest tests
        slowest_tests = sorted(
            [(r.test_name, r.duration) for r in results if r.success],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Identify failing tests
        failing_tests = [
            (r.test_name, r.error) for r in results if not r.success
        ]
        
        report = {
            'summary': {
                'total_tests': len(results),
                'successful_tests': len([r for r in results if r.success]),
                'failed_tests': len([r for r in results if not r.success]),
                'success_rate': success_rate,
                'total_duration': sum(durations),
                'average_duration': statistics.mean(durations) if durations else 0,
                'median_duration': statistics.median(durations) if durations else 0
            },
            'slowest_tests': slowest_tests,
            'failing_tests': failing_tests,
            'metric_summaries': metric_summaries,
            'timestamp': datetime.utcnow()
        }
        
        return report
    
    def generate_html_report(self, results: List[BenchmarkResult]) -> str:
        """Generate HTML performance report"""
        report_data = self.generate_performance_report(results)
        
        # Generate performance charts data
        charts_data = self._generate_charts_data(results)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Report - Repo-Forum</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ background-color: #f8f9fa; }}
        .performance-header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .metric-card {{ border-left: 4px solid #007bff; }}
        .slow-test {{ background-color: #fff3cd; }}
    </style>
</head>
<body>
    <div class="performance-header text-white py-4">
        <div class="container">
            <h1><i class="fas fa-tachometer-alt"></i> Performance Report</h1>
            <p>Generated on {report_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>

    <div class="container mt-4">
        <!-- Summary Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h3 class="text-primary">{report_data['summary']['total_tests']}</h3>
                        <p class="mb-0">Total Tests</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h3 class="text-success">{report_data['summary']['success_rate']:.1f}%</h3>
                        <p class="mb-0">Success Rate</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h3 class="text-info">{report_data['summary']['average_duration']:.3f}s</h3>
                        <p class="mb-0">Avg Duration</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h3 class="text-warning">{report_data['summary']['total_duration']:.3f}s</h3>
                        <p class="mb-0">Total Duration</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Performance Charts -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Test Duration Distribution</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="durationChart" height="200"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>CPU Usage Over Time</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="cpuChart" height="200"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Slowest Tests -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Slowest Tests</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Test Name</th>
                                        <th>Duration (s)</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {self._generate_slowest_tests_html(report_data['slowest_tests'])}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Duration Chart
        const durationCtx = document.getElementById('durationChart').getContext('2d');
        new Chart(durationCtx, {{
            type: 'bar',
            data: {{
                labels: {charts_data['test_names']},
                datasets: [{{
                    label: 'Duration (s)',
                    data: {charts_data['durations']},
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // CPU Chart
        const cpuCtx = document.getElementById('cpuChart').getContext('2d');
        new Chart(cpuCtx, {{
            type: 'line',
            data: {{
                labels: {charts_data['cpu_timestamps']},
                datasets: [{{
                    label: 'CPU Usage (%)',
                    data: {charts_data['cpu_values']},
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
        
        return html_template
    
    def _generate_charts_data(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Generate data for charts"""
        test_names = [r.test_name for r in results if r.success]
        durations = [r.duration for r in results if r.success]
        
        # CPU usage data
        cpu_metrics = []
        for result in results:
            cpu_metrics.extend([m for m in result.metrics if m.name == 'cpu_usage'])
        
        cpu_timestamps = [m.timestamp.strftime('%H:%M:%S') for m in cpu_metrics]
        cpu_values = [m.value for m in cpu_metrics]
        
        return {
            'test_names': test_names,
            'durations': durations,
            'cpu_timestamps': cpu_timestamps,
            'cpu_values': cpu_values
        }
    
    def _generate_slowest_tests_html(self, slowest_tests: List[tuple]) -> str:
        """Generate HTML for slowest tests table"""
        rows = ""
        for test_name, duration in slowest_tests:
            status_class = "text-warning" if duration > 1.0 else "text-success"
            rows += f"""
                <tr class="slow-test">
                    <td>{test_name}</td>
                    <td>{duration:.3f}</td>
                    <td><span class="badge {status_class}">{'Slow' if duration > 1.0 else 'Normal'}</span></td>
                </tr>
            """
        return rows
