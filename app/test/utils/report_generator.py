"""
Advanced Test Report Generator for Repo-Forum Project
Generates HTML dashboard and advanced reporting features.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class TestReportGenerator:
    """Generates advanced HTML test reports and dashboards"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.reports_dir = output_dir / "reports"
        self.dashboards_dir = output_dir / "dashboards"
        
        # Ensure directories exist
        self.dashboards_dir.mkdir(exist_ok=True)
    
    def generate_html_dashboard(self, test_results: List[Dict], session_info: Dict) -> str:
        """Generate comprehensive HTML dashboard"""
        
        # Calculate statistics
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r["status"] == "passed"])
        failed_tests = len([r for r in test_results if r["status"] == "failed"])
        skipped_tests = len([r for r in test_results if r["status"] == "skipped"])
        error_tests = len([r for r in test_results if r["status"] == "error"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Group by category
        categories = {}
        for result in test_results:
            category = result.get("category", "unknown")
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # Generate HTML
        html_content = self._generate_dashboard_html(
            test_results, session_info, categories,
            total_tests, passed_tests, failed_tests, 
            skipped_tests, error_tests, success_rate
        )
        
        # Save dashboard
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dashboard_file = self.dashboards_dir / f"test_dashboard_{timestamp}.html"
        
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(dashboard_file)
    
    def _generate_dashboard_html(self, test_results: List[Dict], session_info: Dict,
                               categories: Dict, total_tests: int, passed_tests: int,
                               failed_tests: int, skipped_tests: int, error_tests: int,
                               success_rate: float) -> str:
        """Generate the HTML dashboard content"""
        
        # Generate category statistics
        category_stats = {}
        for category, tests in categories.items():
            cat_passed = len([t for t in tests if t["status"] == "passed"])
            cat_total = len(tests)
            cat_success_rate = (cat_passed / cat_total * 100) if cat_total > 0 else 0
            
            category_stats[category] = {
                "total": cat_total,
                "passed": cat_passed,
                "failed": len([t for t in tests if t["status"] == "failed"]),
                "skipped": len([t for t in tests if t["status"] == "skipped"]),
                "errors": len([t for t in tests if t["status"] == "error"]),
                "success_rate": cat_success_rate
            }
        
        # Generate test results table rows
        test_rows = ""
        for result in test_results:
            status_class = {
                "passed": "success",
                "failed": "danger", 
                "skipped": "warning",
                "error": "danger"
            }.get(result["status"], "secondary")
            
            test_rows += f"""
                <tr>
                    <td>{result.get('test_name', 'Unknown')}</td>
                    <td><span class="badge bg-secondary">{result.get('category', 'Unknown')}</span></td>
                    <td><span class="badge bg-{status_class}">{result['status'].upper()}</span></td>
                    <td>{result.get('message', 'No message')}</td>
                    <td>{result.get('timestamp', 'Unknown')}</td>
                </tr>
            """
        
        # Generate category cards
        category_cards = ""
        for category, stats in category_stats.items():
            card_color = "success" if stats["success_rate"] >= 90 else "warning" if stats["success_rate"] >= 70 else "danger"
            
            category_cards += f"""
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card border-{card_color}">
                        <div class="card-header bg-{card_color} text-white">
                            <h6 class="mb-0">{category.title()}</h6>
                        </div>
                        <div class="card-body">
                            <div class="row text-center">
                                <div class="col-3">
                                    <h5 class="text-success">{stats['passed']}</h5>
                                    <small class="text-muted">Passed</small>
                                </div>
                                <div class="col-3">
                                    <h5 class="text-danger">{stats['failed']}</h5>
                                    <small class="text-muted">Failed</small>
                                </div>
                                <div class="col-3">
                                    <h5 class="text-warning">{stats['skipped']}</h5>
                                    <small class="text-muted">Skipped</small>
                                </div>
                                <div class="col-3">
                                    <h5 class="text-info">{stats['success_rate']:.1f}%</h5>
                                    <small class="text-muted">Success</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            """
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Repo-Forum Test Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            background-color: #f8f9fa;
        }}
        .dashboard-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
        }}
        .stat-card {{
            border-left: 4px solid #007bff;
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-2px);
        }}
        .chart-container {{
            position: relative;
            height: 300px;
        }}
        .test-table {{
            font-size: 0.9rem;
        }}
        .badge {{
            font-size: 0.8em;
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1><i class="fas fa-flask"></i> Repo-Forum Test Dashboard</h1>
                    <p class="mb-0">Comprehensive Testing Framework Results</p>
                </div>
                <div class="col-md-4 text-end">
                    <h5>{session_info.get('timestamp', datetime.now().isoformat())}</h5>
                    <small>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
                </div>
            </div>
        </div>
    </div>

    <div class="container mt-4">
        <!-- Summary Statistics -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="card-body text-center">
                        <h2 class="text-primary">{total_tests}</h2>
                        <p class="mb-0">Total Tests</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="card-body text-center">
                        <h2 class="text-success">{passed_tests}</h2>
                        <p class="mb-0">Passed</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="card-body text-center">
                        <h2 class="text-danger">{failed_tests}</h2>
                        <p class="mb-0">Failed</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="card-body text-center">
                        <h2 class="text-info">{success_rate:.1f}%</h2>
                        <p class="mb-0">Success Rate</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-chart-pie"></i> Test Results Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="resultsChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-chart-bar"></i> Category Success Rates</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="categoryChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Category Cards -->
        <div class="row mb-4">
            <div class="col-12">
                <h4><i class="fas fa-th-large"></i> Test Categories</h4>
            </div>
            {category_cards}
        </div>

        <!-- Detailed Results Table -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-table"></i> Detailed Test Results</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped test-table">
                                <thead>
                                    <tr>
                                        <th>Test Name</th>
                                        <th>Category</th>
                                        <th>Status</th>
                                        <th>Message</th>
                                        <th>Timestamp</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {test_rows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white text-center py-3 mt-5">
        <p class="mb-0">Repo-Forum Testing Framework &copy; 2026</p>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Results Distribution Chart
        const resultsCtx = document.getElementById('resultsChart').getContext('2d');
        new Chart(resultsCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Passed', 'Failed', 'Skipped', 'Errors'],
                datasets: [{{
                    data: [{passed_tests}, {failed_tests}, {skipped_tests}, {error_tests}],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(220, 53, 69, 0.8)',
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(108, 117, 125, 0.8)'
                    ],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});

        // Category Success Rates Chart
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(categoryCtx, {{
            type: 'bar',
            data: {{
                labels: {list(category_stats.keys())},
                datasets: [{{
                    label: 'Success Rate %',
                    data: {[stats['success_rate'] for stats in category_stats.values()]},
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(23, 162, 184, 0.8)',
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(220, 53, 69, 0.8)',
                        'rgba(108, 117, 125, 0.8)',
                        'rgba(102, 126, 234, 0.8)'
                    ],
                    borderWidth: 1
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
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
        
        return html_template
    
    def generate_trend_report(self, historical_reports: List[Dict]) -> str:
        """Generate trend analysis report"""
        
        if not historical_reports:
            return "<p>No historical data available for trend analysis.</p>"
        
        # Extract trend data
        timestamps = []
        success_rates = []
        total_tests = []
        
        for report in historical_reports:
            session = report.get('test_session', {})
            timestamps.append(session.get('timestamp', ''))
            success_rates.append(session.get('passed', 0) / max(session.get('total_tests', 1), 1) * 100)
            total_tests.append(session.get('total_tests', 0))
        
        # Generate trend HTML
        trend_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Trends - Repo-Forum</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container mt-4">
        <h1><i class="fas fa-chart-line"></i> Test Execution Trends</h1>
        
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Success Rate Trend</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="trendChart" height="100"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        new Chart(trendCtx, {{
            type: 'line',
            data: {{
                labels: {timestamps},
                datasets: [{{
                    label: 'Success Rate %',
                    data: {success_rates},
                    borderColor: 'rgba(40, 167, 69, 1)',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
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
        
        return trend_html
