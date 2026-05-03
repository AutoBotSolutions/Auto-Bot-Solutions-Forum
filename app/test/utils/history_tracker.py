"""
Test Result History and Trending for Repo-Forum Project
Tracks test results over time and provides trend analysis.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics

@dataclass
class TestResultSnapshot:
    """Snapshot of test results at a specific time"""
    timestamp: datetime
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    success_rate: float
    execution_time: float
    categories_tested: int
    environment: str
    python_version: str

@dataclass
class TrendAnalysis:
    """Analysis of test result trends"""
    trend_direction: str  # 'improving', 'declining', 'stable'
    success_rate_trend: float
    test_count_trend: float
    performance_trend: float
    confidence_level: float
    recommendations: List[str]

class HistoryTracker:
    """Tracks and analyzes test result history"""
    
    def __init__(self, history_dir: str):
        self.history_dir = Path(history_dir)
        self.history_file = self.history_dir / "test_history.json"
        self.history_dir.mkdir(exist_ok=True)
        self.snapshots = []
        self._load_history()
    
    def _load_history(self):
        """Load existing history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.snapshots = [
                        TestResultSnapshot(
                            timestamp=datetime.fromisoformat(s['timestamp']),
                            total_tests=s['total_tests'],
                            passed=s['passed'],
                            failed=s['failed'],
                            skipped=s['skipped'],
                            errors=s['errors'],
                            success_rate=s['success_rate'],
                            execution_time=s['execution_time'],
                            categories_tested=s['categories_tested'],
                            environment=s.get('environment', 'unknown'),
                            python_version=s.get('python_version', 'unknown')
                        )
                        for s in data.get('snapshots', [])
                    ]
            except Exception as e:
                print(f"Warning: Could not load history: {e}")
                self.snapshots = []
    
    def add_snapshot(self, test_results: List[Dict], execution_time: float, 
                    environment: str = 'local', python_version: str = 'unknown'):
        """Add a new test result snapshot"""
        total_tests = len(test_results)
        passed = len([r for r in test_results if r['status'] == 'passed'])
        failed = len([r for r in test_results if r['status'] == 'failed'])
        skipped = len([r for r in test_results if r['status'] == 'skipped'])
        errors = len([r for r in test_results if r['status'] == 'error'])
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        categories_tested = len(set(r.get('category', 'unknown') for r in test_results))
        
        snapshot = TestResultSnapshot(
            timestamp=datetime.utcnow(),
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            success_rate=success_rate,
            execution_time=execution_time,
            categories_tested=categories_tested,
            environment=environment,
            python_version=python_version
        )
        
        self.snapshots.append(snapshot)
        self._save_history()
        
        return snapshot
    
    def _save_history(self):
        """Save history to file"""
        data = {
            'snapshots': [asdict(s) for s in self.snapshots],
            'last_updated': datetime.utcnow().isoformat(),
            'total_snapshots': len(self.snapshots)
        }
        
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def get_trend_analysis(self, days: int = 30) -> TrendAnalysis:
        """Analyze trends over the specified number of days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_snapshots = [s for s in self.snapshots if s.timestamp >= cutoff_date]
        
        if len(recent_snapshots) < 2:
            return TrendAnalysis(
                trend_direction='stable',
                success_rate_trend=0.0,
                test_count_trend=0.0,
                performance_trend=0.0,
                confidence_level=0.0,
                recommendations=['Insufficient data for trend analysis']
            )
        
        # Calculate trends
        success_rates = [s.success_rate for s in recent_snapshots]
        test_counts = [s.total_tests for s in recent_snapshots]
        execution_times = [s.execution_time for s in recent_snapshots]
        
        # Calculate trend slopes (simple linear regression)
        success_rate_trend = self._calculate_trend(success_rates)
        test_count_trend = self._calculate_trend(test_counts)
        performance_trend = self._calculate_trend(execution_times)
        
        # Determine overall trend direction
        trend_direction = self._determine_trend_direction(
            success_rate_trend, test_count_trend, performance_trend
        )
        
        # Calculate confidence level based on data consistency
        confidence_level = self._calculate_confidence_level(recent_snapshots)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            trend_direction, success_rate_trend, test_count_trend, performance_trend
        )
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            success_rate_trend=success_rate_trend,
            test_count_trend=test_count_trend,
            performance_trend=performance_trend,
            confidence_level=confidence_level,
            recommendations=recommendations
        )
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate simple trend (slope) for a list of values"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope using linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def _determine_trend_direction(self, success_rate_trend: float, 
                                  test_count_trend: float, performance_trend: float) -> str:
        """Determine overall trend direction"""
        # Weight the trends (success rate is most important)
        weighted_trend = (success_rate_trend * 0.5 + 
                          test_count_trend * 0.3 + 
                          (-performance_trend) * 0.2)  # Negative because lower is better for performance
        
        if weighted_trend > 0.5:
            return 'improving'
        elif weighted_trend < -0.5:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_confidence_level(self, snapshots: List[TestResultSnapshot]) -> float:
        """Calculate confidence level based on data consistency"""
        if len(snapshots) < 3:
            return 0.0
        
        # Calculate variance in success rates
        success_rates = [s.success_rate for s in snapshots]
        variance = statistics.variance(success_rates) if len(success_rates) > 1 else 0
        
        # Lower variance = higher confidence
        max_variance = 100.0  # Maximum possible variance for percentages
        confidence = max(0.0, 1.0 - (variance / max_variance))
        
        return confidence
    
    def _generate_recommendations(self, trend_direction: str, success_rate_trend: float,
                                 test_count_trend: float, performance_trend: float) -> List[str]:
        """Generate recommendations based on trend analysis"""
        recommendations = []
        
        if trend_direction == 'declining':
            recommendations.append("⚠️ Test quality is declining - investigate recent changes")
            if success_rate_trend < -1.0:
                recommendations.append("🔍 Success rate dropping significantly - review recent commits")
            if performance_trend > 0.5:
                recommendations.append("⚡ Performance degrading - optimize test execution")
        elif trend_direction == 'improving':
            recommendations.append("✅ Test quality is improving - keep up the good work")
            if success_rate_trend > 1.0:
                recommendations.append("🎯 Success rate improving significantly - great progress!")
        else:
            recommendations.append("📊 Test quality is stable - maintain current practices")
        
        if test_count_trend > 0.5:
            recommendations.append("📈 Test count increasing - consider test organization")
        elif test_count_trend < -0.5:
            recommendations.append("📉 Test count decreasing - ensure coverage is maintained")
        
        return recommendations
    
    def get_statistics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get statistical summary of test results"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_snapshots = [s for s in self.snapshots if s.timestamp >= cutoff_date]
        
        if not recent_snapshots:
            return {'error': 'No data available for the specified period'}
        
        success_rates = [s.success_rate for s in recent_snapshots]
        test_counts = [s.total_tests for s in recent_snapshots]
        execution_times = [s.execution_time for s in recent_snapshots]
        
        return {
            'period_days': days,
            'total_snapshots': len(recent_snapshots),
            'success_rate_stats': {
                'mean': statistics.mean(success_rates),
                'median': statistics.median(success_rates),
                'min': min(success_rates),
                'max': max(success_rates),
                'std_dev': statistics.stdev(success_rates) if len(success_rates) > 1 else 0
            },
            'test_count_stats': {
                'mean': statistics.mean(test_counts),
                'median': statistics.median(test_counts),
                'min': min(test_counts),
                'max': max(test_counts),
                'total': sum(test_counts)
            },
            'performance_stats': {
                'mean': statistics.mean(execution_times),
                'median': statistics.median(execution_times),
                'min': min(execution_times),
                'max': max(execution_times),
                'total': sum(execution_times)
            },
            'period_start': recent_snapshots[0].timestamp.isoformat(),
            'period_end': recent_snapshots[-1].timestamp.isoformat()
        }
    
    def generate_trend_report(self, days: int = 30) -> str:
        """Generate a comprehensive trend report"""
        analysis = self.get_trend_analysis(days)
        stats = self.get_statistics_summary(days)
        
        if 'error' in stats:
            return f"Error: {stats['error']}"
        
        report = f"""
# 📈 Test Result Trend Report

**Period:** Last {days} days  
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Snapshots:** {stats['total_snapshots']}

## 🎯 Trend Analysis

**Overall Trend:** {analysis.trend_direction.upper()}  
**Confidence Level:** {analysis.confidence_level:.1%}

### 📊 Trend Metrics
- **Success Rate Trend:** {analysis.success_rate_trend:+.2f}% per snapshot
- **Test Count Trend:** {analysis.test_count_trend:+.2f} tests per snapshot  
- **Performance Trend:** {analysis.performance_trend:+.2f}s per snapshot

### 💡 Recommendations
{chr(10).join(f"- {rec}" for rec in analysis.recommendations)}

## 📈 Statistics Summary

### ✅ Success Rate Statistics
- **Mean:** {stats['success_rate_stats']['mean']:.1f}%
- **Median:** {stats['success_rate_stats']['median']:.1f}%
- **Range:** {stats['success_rate_stats']['min']:.1f}% - {stats['success_rate_stats']['max']:.1f}%
- **Std Dev:** {stats['success_rate_stats']['std_dev']:.2f}%

### 🧪 Test Count Statistics  
- **Mean:** {stats['test_count_stats']['mean']:.1f} tests
- **Median:** {stats['test_count_stats']['median']:.1f} tests
- **Range:** {stats['test_count_stats']['min']} - {stats['test_count_stats']['max']} tests
- **Total:** {stats['test_count_stats']['total']} tests

### ⚡ Performance Statistics
- **Mean:** {stats['performance_stats']['mean']:.2f}s
- **Median:** {stats['performance_stats']['median']:.2f}s  
- **Range:** {stats['performance_stats']['min']:.2f}s - {stats['performance_stats']['max']:.2f}s
- **Total:** {stats['performance_stats']['total']:.2f}s

## 📅 Period Details
- **Start:** {stats['period_start']}
- **End:** {stats['period_end']}

---
*Report generated by Repo-Forum Testing Framework*
        """
        
        return report.strip()

# Utility function for easy history tracking
def track_test_results(test_results: List[Dict], execution_time: float, 
                       history_dir: str = "app/test/output/history") -> TestResultSnapshot:
    """Utility function to track test results"""
    tracker = HistoryTracker(history_dir)
    return tracker.add_snapshot(test_results, execution_time)
