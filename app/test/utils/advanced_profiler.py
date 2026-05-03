"""
Advanced Performance Profiling for Repo-Forum Project
Provides comprehensive performance analysis and profiling capabilities.
"""

import time
import psutil
import threading
import json
import cProfile
import pstats
import io
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from functools import wraps
import statistics

@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a specific time"""
    timestamp: datetime
    cpu_percent: float
    memory_usage_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    thread_count: int
    process_count: int

@dataclass
class ProfileResult:
    """Result of a profiling session"""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    snapshots: List[PerformanceSnapshot]
    profile_data: Dict[str, Any]
    memory_peak: float
    cpu_average: float
    bottlenecks: List[Dict[str, Any]]

class AdvancedProfiler:
    """Advanced performance profiler with comprehensive metrics"""
    
    def __init__(self, sampling_interval: float = 0.1):
        self.sampling_interval = sampling_interval
        self.snapshots = []
        self.monitoring = False
        self.monitor_thread = None
        self.profiler = None
        self.start_time = None
        
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = datetime.utcnow()
        self.monitoring = True
        self.snapshots = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Start cProfile
        self.profiler = cProfile.Profile()
        self.profiler.enable()
    
    def stop_monitoring(self) -> ProfileResult:
        """Stop monitoring and return results"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        end_time = datetime.utcnow()
        
        # Stop cProfile
        if self.profiler:
            self.profiler.disable()
        
        # Calculate metrics
        duration = (end_time - self.start_time).total_seconds()
        memory_peak = max(s.memory_usage_mb for s in self.snapshots) if self.snapshots else 0
        cpu_average = statistics.mean(s.cpu_percent for s in self.snapshots) if self.snapshots else 0
        
        # Get profile data
        profile_data = self._get_profile_stats()
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(profile_data)
        
        return ProfileResult(
            test_name="unknown",
            start_time=self.start_time,
            end_time=end_time,
            duration=duration,
            snapshots=self.snapshots.copy(),
            profile_data=profile_data,
            memory_peak=memory_peak,
            cpu_average=cpu_average,
            bottlenecks=bottlenecks
        )
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent()
                memory_info = psutil.virtual_memory()
                memory_info_process = process.memory_info()
                disk_io = psutil.disk_io_counters()
                network_io = psutil.net_io_counters()
                
                snapshot = PerformanceSnapshot(
                    timestamp=datetime.utcnow(),
                    cpu_percent=cpu_percent,
                    memory_usage_mb=memory_info_process.rss / 1024 / 1024,
                    memory_percent=memory_info.percent,
                    disk_io_read_mb=disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
                    disk_io_write_mb=disk_io.write_bytes / 1024 / 1024 if disk_io else 0,
                    network_io_sent_mb=network_io.bytes_sent / 1024 / 1024 if network_io else 0,
                    network_io_recv_mb=network_io.bytes_recv / 1024 / 1024 if network_io else 0,
                    thread_count=threading.active_count(),
                    process_count=len(psutil.pids())
                )
                
                self.snapshots.append(snapshot)
                time.sleep(self.sampling_interval)
                
            except Exception as e:
                print(f"Warning: Monitoring error: {e}")
                break
    
    def _get_profile_stats(self) -> Dict[str, Any]:
        """Get cProfile statistics"""
        if not self.profiler:
            return {}
        
        # Create stats object
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats()
        
        # Parse stats
        stats_text = s.getvalue()
        lines = stats_text.split('\n')
        
        # Extract top functions
        functions = []
        for line in lines[5:]:  # Skip header lines
            if line.strip() and not line.startswith(' '):
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        calls = int(parts[0])
                        cumulative_time = float(parts[1])
                        per_call_time = float(parts[2])
                        total_time = float(parts[3])
                        per_call_cumulative = float(parts[4])
                        filename = parts[5:]
                        
                        functions.append({
                            'calls': calls,
                            'cumulative_time': cumulative_time,
                            'per_call_time': per_call_time,
                            'total_time': total_time,
                            'per_call_cumulative': per_call_cumulative,
                            'filename': ' '.join(filename)
                        })
                    except (ValueError, IndexError):
                        continue
        
        return {
            'total_functions': len(functions),
            'top_functions': functions[:10],  # Top 10 functions
            'stats_text': stats_text
        }
    
    def _identify_bottlenecks(self, profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        if not profile_data.get('top_functions'):
            return bottlenecks
        
        # Identify slow functions
        top_functions = profile_data['top_functions']
        avg_time = statistics.mean(f['cumulative_time'] for f in top_functions) if top_functions else 0
        
        for func in top_functions:
            if func['cumulative_time'] > avg_time * 2:  # 2x slower than average
                bottlenecks.append({
                    'type': 'slow_function',
                    'function': func['filename'],
                    'cumulative_time': func['cumulative_time'],
                    'calls': func['calls'],
                    'severity': 'high' if func['cumulative_time'] > avg_time * 3 else 'medium'
                })
        
        # Identify memory issues
        if self.snapshots:
            memory_growth = self.snapshots[-1].memory_usage_mb - self.snapshots[0].memory_usage_mb
            if memory_growth > 50:  # More than 50MB growth
                bottlenecks.append({
                    'type': 'memory_leak',
                    'memory_growth_mb': memory_growth,
                    'severity': 'high' if memory_growth > 100 else 'medium'
                })
        
        # Identify CPU spikes
        cpu_values = [s.cpu_percent for s in self.snapshots]
        if cpu_values:
            cpu_max = max(cpu_values)
            cpu_avg = statistics.mean(cpu_values)
            if cpu_max > cpu_avg * 2:  # CPU spike
                bottlenecks.append({
                    'type': 'cpu_spike',
                    'max_cpu': cpu_max,
                    'avg_cpu': cpu_avg,
                    'severity': 'high' if cpu_max > 80 else 'medium'
                })
        
        return bottlenecks

class PerformanceAnalyzer:
    """Analyzes performance data and generates insights"""
    
    def __init__(self):
        self.profiles = []
    
    def add_profile(self, profile: ProfileResult):
        """Add a profile result for analysis"""
        self.profiles.append(profile)
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.profiles:
            return {'error': 'No performance data available'}
        
        # Calculate overall statistics
        total_duration = sum(p.duration for p in self.profiles)
        avg_duration = total_duration / len(self.profiles)
        max_memory = max(p.memory_peak for p in self.profiles)
        avg_cpu = statistics.mean(p.cpu_average for p in self.profiles)
        
        # Identify common bottlenecks
        all_bottlenecks = []
        for profile in self.profiles:
            all_bottlenecks.extend(profile.bottlenecks)
        
        bottleneck_summary = self._summarize_bottlenecks(all_bottlenecks)
        
        # Performance trends
        performance_trend = self._analyze_performance_trend()
        
        return {
            'summary': {
                'total_profiles': len(self.profiles),
                'total_duration': total_duration,
                'average_duration': avg_duration,
                'max_memory_usage_mb': max_memory,
                'average_cpu_usage': avg_cpu
            },
            'bottleneck_analysis': bottleneck_summary,
            'performance_trend': performance_trend,
            'detailed_profiles': [self._serialize_profile(p) for p in self.profiles]
        }
    
    def _summarize_bottlenecks(self, bottlenecks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize bottlenecks across all profiles"""
        if not bottlenecks:
            return {'total': 0, 'by_type': {}, 'by_severity': {}}
        
        by_type = {}
        by_severity = {'high': 0, 'medium': 0, 'low': 0}
        
        for bottleneck in bottlenecks:
            btype = bottleneck['type']
            severity = bottleneck['severity']
            
            by_type[btype] = by_type.get(btype, 0) + 1
            by_severity[severity] += 1
        
        return {
            'total': len(bottlenecks),
            'by_type': by_type,
            'by_severity': by_severity,
            'most_common': max(by_type.items(), key=lambda x: x[1])[0] if by_type else None
        }
    
    def _analyze_performance_trend(self) -> Dict[str, Any]:
        """Analyze performance trends across profiles"""
        if len(self.profiles) < 2:
            return {'trend': 'insufficient_data'}
        
        durations = [p.duration for p in self.profiles]
        memory_peaks = [p.memory_peak for p in self.profiles]
        cpu_averages = [p.cpu_average for p in self.profiles]
        
        # Simple trend calculation
        duration_trend = self._calculate_simple_trend(durations)
        memory_trend = self._calculate_simple_trend(memory_peaks)
        cpu_trend = self._calculate_simple_trend(cpu_averages)
        
        return {
            'duration_trend': duration_trend,
            'memory_trend': memory_trend,
            'cpu_trend': cpu_trend,
            'overall_trend': self._determine_overall_trend(duration_trend, memory_trend, cpu_trend)
        }
    
    def _calculate_simple_trend(self, values: List[float]) -> str:
        """Calculate simple trend direction"""
        if len(values) < 2:
            return 'stable'
        
        # Compare first half with second half
        mid = len(values) // 2
        first_half_avg = statistics.mean(values[:mid])
        second_half_avg = statistics.mean(values[mid:])
        
        diff = second_half_avg - first_half_avg
        threshold = first_half_avg * 0.1  # 10% threshold
        
        if diff > threshold:
            return 'increasing'
        elif diff < -threshold:
            return 'decreasing'
        else:
            return 'stable'
    
    def _determine_overall_trend(self, duration_trend: str, memory_trend: str, cpu_trend: str) -> str:
        """Determine overall performance trend"""
        # Count trends (excluding stable)
        trends = [t for t in [duration_trend, memory_trend, cpu_trend] if t != 'stable']
        
        if not trends:
            return 'stable'
        
        if len(trends) == 1:
            return trends[0]
        
        # If trends are conflicting, return mixed
        if len(set(trends)) > 1:
            return 'mixed'
        
        return trends[0]
    
    def _serialize_profile(self, profile: ProfileResult) -> Dict[str, Any]:
        """Serialize profile for JSON output"""
        return {
            'test_name': profile.test_name,
            'start_time': profile.start_time.isoformat(),
            'end_time': profile.end_time.isoformat(),
            'duration': profile.duration,
            'memory_peak_mb': profile.memory_peak,
            'cpu_average': profile.cpu_average,
            'bottleneck_count': len(profile.bottlenecks),
            'snapshot_count': len(profile.snapshots)
        }

# Decorators for easy profiling
def advanced_profile(test_name: str = None):
    """Decorator for advanced performance profiling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = test_name or f"{func.__module__}.{func.__name__}"
            
            profiler = AdvancedProfiler()
            profiler.start_monitoring()
            
            try:
                result = func(*args, **kwargs)
                profile_result = profiler.stop_monitoring()
                profile_result.test_name = name
                
                # Store profile for analysis
                analyzer = PerformanceAnalyzer()
                analyzer.add_profile(profile_result)
                
                return result
                
            except Exception as e:
                profiler.stop_monitoring()
                raise e
        
        return wrapper
    return decorator

@contextmanager
def profile_context(test_name: str = None):
    """Context manager for advanced profiling"""
    profiler = AdvancedProfiler()
    profiler.start_monitoring()
    
    try:
        yield profiler
    finally:
        profile_result = profiler.stop_monitoring()
        if test_name:
            profile_result.test_name = test_name

# Utility functions
def generate_performance_report(profiles: List[ProfileResult], output_dir: str) -> str:
    """Generate comprehensive performance report"""
    analyzer = PerformanceAnalyzer()
    for profile in profiles:
        analyzer.add_profile(profile)
    
    report_data = analyzer.generate_performance_report()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"{output_dir}/performance_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    return report_file

def compare_performance(profile1: ProfileResult, profile2: ProfileResult) -> Dict[str, Any]:
    """Compare two performance profiles"""
    return {
        'duration_diff': profile2.duration - profile1.duration,
        'duration_percent_change': ((profile2.duration - profile1.duration) / profile1.duration * 100) if profile1.duration > 0 else 0,
        'memory_peak_diff': profile2.memory_peak - profile1.memory_peak,
        'memory_peak_percent_change': ((profile2.memory_peak - profile1.memory_peak) / profile1.memory_peak * 100) if profile1.memory_peak > 0 else 0,
        'cpu_avg_diff': profile2.cpu_average - profile1.cpu_average,
        'bottleneck_count_diff': len(profile2.bottlenecks) - len(profile1.bottlenecks)
    }
