"""
Dashboard Module

This module provides web-based dashboard generation for the ELITE 8 AI Video Generation System,
displaying real-time metrics, alerts, production status, and system health.

Features:
- Real-time metrics display
- Production statistics with charts
- Alert summary and management
- System health indicators
- Character rotation status
- Exportable reports (HTML, JSON)
- Responsive design for mobile/desktop

Version: 1.0.0
Created: 2026-01-22
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DashboardConfig:
    """Configuration for dashboard"""
    output_dir: str = "output/dashboard"
    refresh_interval: int = 60  # seconds
    title: str = "ELITE 8 System Dashboard"
    theme: str = "dark"
    show_charts: bool = True
    show_alerts: bool = True
    show_metrics: bool = True
    
    @classmethod
    def from_json(cls, config_path: str) -> 'DashboardConfig':
        """Load configuration from JSON file"""
        path = Path(config_path)
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()


class Dashboard:
    """
    Dashboard generator for system monitoring and reporting.
    
    Provides:
    - HTML dashboard generation
    - JSON status reports
    - Real-time data integration
    - Responsive design
    - Alert management interface
    """
    
    def __init__(self, config: DashboardConfig = None):
        """
        Initialize dashboard.
        
        Args:
            config: Dashboard configuration
        """
        self.config = config or DashboardConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Dashboard initialized")
    
    def generate_dashboard(
        self,
        production_stats: Dict = None,
        metrics: Dict = None,
        alerts: List = None,
        system_health: Dict = None
    ) -> str:
        """
        Generate complete HTML dashboard.
        
        Args:
            production_stats: Production statistics
            metrics: System metrics
            alerts: Active alerts
            system_health: System health status
            
        Returns:
            HTML dashboard string
        """
        # Load data if not provided
        production_stats = production_stats or self._load_production_stats()
        metrics = metrics or self._load_metrics()
        alerts = alerts or []
        system_health = system_health or self._check_system_health()
        
        html_content = self._build_html(
            production_stats=production_stats,
            metrics=metrics,
            alerts=alerts,
            system_health=system_health
        )
        
        return html_content
    
    def save_dashboard(
        self,
        production_stats: Dict = None,
        metrics: Dict = None,
        alerts: List = None,
        system_health: Dict = None,
        filename: str = "dashboard.html"
    ) -> Path:
        """
        Generate and save dashboard to file.
        
        Args:
            production_stats: Production statistics
            metrics: System metrics
            alerts: Active alerts
            system_health: System health status
            filename: Output filename
            
        Returns:
            Path to saved dashboard
        """
        html_content = self.generate_dashboard(
            production_stats=production_stats,
            metrics=metrics,
            alerts=alerts,
            system_health=system_health
        )
        
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Dashboard saved to {output_path}")
        return output_path
    
    def generate_status_report(self) -> Dict[str, Any]:
        """Generate JSON status report"""
        production_stats = self._load_production_stats()
        system_health = self._check_system_health()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "system": system_health,
            "production": production_stats,
            "status": "healthy" if system_health.get("overall_status") == "healthy" else "warning"
        }
    
    def _load_production_stats(self) -> Dict:
        """Load production statistics"""
        stats_path = Path("data/production_stats.json")
        if stats_path.exists():
            try:
                with open(stats_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load production stats: {e}")
        return {
            "total_videos": 0,
            "total_credits": 0,
            "total_cost": 0,
            "by_platform": {},
            "by_character": {},
            "daily_totals": {}
        }
    
    def _load_metrics(self) -> Dict:
        """Load current metrics"""
        metrics_path = Path("data/metrics.json")
        if metrics_path.exists():
            try:
                with open(metrics_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metrics: {e}")
        return {}
    
    def _check_system_health(self) -> Dict:
        """Check system health"""
        health = {
            "overall_status": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            import psutil
            
            # CPU
            cpu = psutil.cpu_percent(interval=1)
            health["components"]["cpu"] = {
                "status": "healthy" if cpu < 80 else "warning" if cpu < 95 else "critical",
                "value": f"{cpu}%"
            }
            
            # Memory
            memory = psutil.virtual_memory()
            mem_status = "healthy" if memory.percent < 80 else "warning" if memory.percent < 95 else "critical"
            health["components"]["memory"] = {
                "status": mem_status,
                "value": f"{memory.percent}%",
                "available_gb": round(memory.available / 1e9, 2)
            }
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_status = "healthy" if disk.percent < 80 else "warning" if disk.percent < 95 else "critical"
            health["components"]["disk"] = {
                "status": disk_status,
                "value": f"{disk.percent}%",
                "free_gb": round(disk.free / 1e9, 2)
            }
            
            # Overall status
            statuses = [c["status"] for c in health["components"].values()]
            if "critical" in statuses:
                health["overall_status"] = "critical"
            elif "warning" in statuses:
                health["overall_status"] = "warning"
                
        except Exception as e:
            logger.error(f"Failed to check system health: {e}")
            health["overall_status"] = "unknown"
            health["error"] = str(e)
        
        return health
    
    def _build_html(
        self,
        production_stats: Dict,
        metrics: Dict,
        alerts: List,
        system_health: Dict
    ) -> str:
        """Build HTML dashboard"""
        
        # Determine theme colors
        if self.config.theme == "dark":
            bg_color = "#1a1a2e"
            card_bg = "#16213e"
            text_color = "#eaeaea"
            accent_color = "#0f3460"
            success_color = "#4caf50"
            warning_color = "#ff9800"
            danger_color = "#f44336"
        else:
            bg_color = "#f5f5f5"
            card_bg = "#ffffff"
            text_color = "#333333"
            accent_color = "#2196f3"
            success_color = "#4caf50"
            warning_color = "#ff9800"
            danger_color = "#f44336"
        
        # Build components
        header = self._build_header()
        summary_cards = self._build_summary_cards(production_stats, system_health)
        charts_section = self._build_charts_section(production_stats)
        alerts_section = self._build_alerts_section(alerts)
        metrics_table = self._build_metrics_table(metrics)
        footer = self._build_footer()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: {bg_color};
            color: {text_color};
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, {accent_color}, #1a1a2e);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }}
        
        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            opacity: 0.8;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin-top: 15px;
        }}
        
        .status-healthy {{ background-color: {success_color}; }}
        .status-warning {{ background-color: {warning_color}; }}
        .status-critical {{ background-color: {danger_color}; }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background-color: {card_bg};
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
        }}
        
        .card h2 {{
            font-size: 1.3em;
            margin-bottom: 20px;
            color: {accent_color};
            border-bottom: 2px solid {accent_color};
            padding-bottom: 10px;
        }}
        
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 15px;
            background-color: {bg_color};
            border-radius: 10px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: {accent_color};
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.7;
            margin-top: 5px;
        }}
        
        .alert-item {{
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 10px;
            border-left: 4px solid;
        }}
        
        .alert-info {{ border-color: #2196f3; background-color: rgba(33, 150, 243, 0.1); }}
        .alert-warning {{ border-color: {warning_color}; background-color: rgba(255, 152, 0, 0.1); }}
        .alert-error {{ border-color: {danger_color}; background-color: rgba(244, 67, 54, 0.1); }}
        .alert-critical {{ border-color: #9c27b0; background-color: rgba(156, 39, 176, 0.1); }}
        
        .alert-title {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .alert-time {{
            font-size: 0.8em;
            opacity: 0.6;
        }}
        
        .chart-container {{
            position: relative;
            height: 300px;
            margin: 20px 0;
        }}
        
        .metrics-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .metrics-table th, .metrics-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid {bg_color};
        }}
        
        .metrics-table th {{
            background-color: {accent_color};
            color: white;
        }}
        
        .metrics-table tr:hover {{
            background-color: {bg_color};
        }}
        
        .health-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        
        .health-healthy {{ background-color: {success_color}; }}
        .health-warning {{ background-color: {warning_color}; }}
        .health-critical {{ background-color: {danger_color}; }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            opacity: 0.6;
            font-size: 0.9em;
        }}
        
        .no-data {{
            text-align: center;
            padding: 40px;
            opacity: 0.5;
        }}
        
        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
            
            .stat-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {header}
        
        {summary_cards}
        
        <div class="grid">
            {charts_section}
        </div>
        
        {alerts_section}
        
        {metrics_table}
        
        {footer}
    </div>
    
    <script>
        // Auto-refresh functionality
        setTimeout(function() {{
            location.reload();
        }}, {self.config.refresh_interval * 1000});
        
        // Simple chart drawing (using CSS)
        document.querySelectorAll('.bar-chart').forEach(chart => {{
            const bars = chart.querySelectorAll('.bar');
            bars.forEach(bar => {{
                const value = bar.dataset.value;
                const max = chart.dataset.max || 100;
                bar.style.height = (value / max * 100) + '%';
            }});
        }});
    </script>
</body>
</html>"""
        
        return html
    
    def _build_header(self) -> str:
        """Build dashboard header"""
        status = "healthy"
        status_text = "System Healthy"
        
        return f"""
        <div class="header">
            <h1>{self.config.title}</h1>
            <p>Real-time monitoring and production tracking</p>
            <span class="status-badge status-{status}">{status_text}</span>
            <p style="margin-top: 15px; font-size: 0.9em;">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """
    
    def _build_summary_cards(self, production_stats: Dict, system_health: Dict) -> str:
        """Build summary statistic cards"""
        
        total_videos = production_stats.get("total_videos", 0)
        total_credits = production_stats.get("total_credits", 0)
        total_cost = production_stats.get("total_cost", 0)
        
        today = datetime.now().strftime("%Y-%m-%d")
        daily = production_stats.get("daily_totals", {}).get(today, {})
        today_videos = daily.get("videos", 0)
        today_cost = daily.get("cost", 0)
        
        # Platform distribution
        by_platform = production_stats.get("by_platform", {})
        platforms_html = ""
        for platform, count in by_platform.items():
            platforms_html += f"<div class='stat-item'><div class='stat-value'>{count}</div><div class='stat-label'>{platform}</div></div>"
        
        if not platforms_html:
            platforms_html = "<div class='no-data'>No data yet</div>"
        
        return f"""
        <div class="grid">
            <div class="card">
                <h2>Production Overview</h2>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value">{total_videos}</div>
                        <div class="stat-label">Total Videos</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{int(total_credits)}</div>
                        <div class="stat-label">Total Credits</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${total_cost:.2f}</div>
                        <div class="stat-label">Total Cost</div>
                    </div>
                    <div class='stat-item'>
                        <div class='stat-value'>{today_videos}</div>
                        <div class='stat-label'>Today Videos</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Today's Progress</h2>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value">{today_videos}</div>
                        <div class="stat-label">Videos Created</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${today_cost:.2f}</div>
                        <div class="stat-label">Cost Today</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">4</div>
                        <div class="stat-label">Daily Target</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{int((today_videos / 4) * 100) if today_videos > 0 else 0}%</div>
                        <div class="stat-label">Progress</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Platform Distribution</h2>
                <div class="stat-grid">
                    {platforms_html}
                </div>
            </div>
            
            <div class="card">
                <h2>System Health</h2>
                <div class="stat-grid">
                    {self._build_health_items(system_health)}
                </div>
            </div>
        </div>
        """
    
    def _build_health_items(self, system_health: Dict) -> str:
        """Build system health items"""
        components = system_health.get("components", {})
        items_html = ""
        
        for name, data in components.items():
            status = data.get("status", "unknown")
            value = data.get("value", "N/A")
            label = name.upper()
            items_html += f"""
            <div class="stat-item">
                <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                    <span class="health-indicator health-{status}"></span>
                    <span style="font-weight: bold;">{label}</span>
                </div>
                <div class="stat-value" style="font-size: 1.5em;">{value}</div>
            </div>
            """
        
        if not items_html:
            items_html = "<div class='no-data'>No health data</div>"
        
        return items_html
    
    def _build_charts_section(self, production_stats: Dict) -> str:
        """Build charts section"""
        
        by_platform = production_stats.get("by_platform", {})
        by_character = production_stats.get("by_character", {})
        
        # Build platform bar chart
        max_platform_val = max(by_platform.values()) if by_platform else 1
        platform_bars = ""
        for platform, count in by_platform.items():
            percentage = (count / max_platform_val) * 100
            platform_bars += f"""
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>{platform}</span>
                    <span>{count}</span>
                </div>
                <div style="background-color: #2a2a4a; border-radius: 5px; height: 25px;">
                    <div style="background: linear-gradient(90deg, #0f3460, #1a1a2e); width: {percentage}%; height: 100%; border-radius: 5px;"></div>
                </div>
            </div>
            """
        
        if not platform_bars:
            platform_bars = "<div class='no-data'>No platform data</div>"
        
        # Build character distribution
        max_char_val = max(by_character.values()) if by_character else 1
        character_bars = ""
        for char, count in by_character.items():
            percentage = (count / max_char_val) * 100
            character_bars += f"""
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>{char}</span>
                    <span>{count}</span>
                </div>
                <div style="background-color: #2a2a4a; border-radius: 5px; height: 25px;">
                    <div style="background: linear-gradient(90deg, #4caf50, #45a049); width: {percentage}%; height: 100%; border-radius: 5px;"></div>
                </div>
            </div>
            """
        
        if not character_bars:
            character_bars = "<div class='no-data'>No character data</div>"
        
        return f"""
        <div class="card" style="grid-column: span 2;">
            <h2>Platform Distribution</h2>
            {platform_bars}
        </div>
        
        <div class="card" style="grid-column: span 2;">
            <h2>Character Usage</h2>
            {character_bars}
        </div>
        """
    
    def _build_alerts_section(self, alerts: List) -> str:
        """Build alerts section"""
        if not alerts:
            return """
            <div class="card" style="grid-column: span 4;">
                <h2>Active Alerts</h2>
                <div class="no-data">No active alerts</div>
            </div>
            """
        
        alerts_html = ""
        for alert in alerts[:10]:  # Show max 10 alerts
            severity_class = f"alert-{alert.get('severity', 'info')}"
            alerts_html += f"""
            <div class="alert-item {severity_class}">
                <div class="alert-title">{html.escape(alert.get('title', 'Unknown Alert'))}</div>
                <div>{html.escape(alert.get('message', ''))}</div>
                <div class="alert-time">{alert.get('created_at', 'Unknown time')}</div>
            </div>
            """
        
        return f"""
        <div class="card" style="grid-column: span 4;">
            <h2>Active Alerts ({len(alerts)})</h2>
            {alerts_html}
        </div>
        """
    
    def _build_metrics_table(self, metrics: Dict) -> str:
        """Build metrics table"""
        if not metrics:
            return """
            <div class="card" style="grid-column: span 4;">
                <h2>System Metrics</h2>
                <div class="no-data">No metrics available</div>
            </div>
            """
        
        rows = ""
        for name, data in metrics.items():
            value = data.get("value", "N/A")
            timestamp = data.get("timestamp", "N/A")
            rows += f"""
            <tr>
                <td>{html.escape(name)}</td>
                <td>{html.escape(str(value))}</td>
                <td>{html.escape(str(timestamp))}</td>
            </tr>
            """
        
        return f"""
        <div class="card" style="grid-column: span 4;">
            <h2>System Metrics</h2>
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Last Updated</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """
    
    def _build_footer(self) -> str:
        """Build dashboard footer"""
        return """
        <div class="footer">
            <p>ELITE 8 AI Video Generation System - Dashboard</p>
            <p>Auto-refreshes every 60 seconds</p>
        </div>
        """
    
    def generate_report(self, report_type: str = "daily") -> Dict[str, Any]:
        """
        Generate a report.
        
        Args:
            report_type: Type of report (daily, weekly, monthly)
            
        Returns:
            Report dictionary
        """
        if report_type == "daily":
            return self._generate_daily_report()
        elif report_type == "weekly":
            return self._generate_weekly_report()
        elif report_type == "monthly":
            return self._generate_monthly_report()
        else:
            return self.generate_status_report()
    
    def _generate_daily_report(self) -> Dict[str, Any]:
        """Generate daily report"""
        production_stats = self._load_production_stats()
        today = datetime.now().strftime("%Y-%m-%d")
        daily = production_stats.get("daily_totals", {}).get(today, {})
        
        return {
            "report_type": "daily",
            "date": today,
            "generated_at": datetime.now().isoformat(),
            "videos_created": daily.get("videos", 0),
            "credits_used": daily.get("credits", 0),
            "cost": daily.get("cost", 0),
            "platforms_used": production_stats.get("by_platform", {}),
            "characters_used": production_stats.get("by_character", {}),
            "target_videos": 4,
            "achievement_percentage": (daily.get("videos", 0) / 4) * 100
        }
    
    def _generate_weekly_report(self) -> Dict[str, Any]:
        """Generate weekly report"""
        production_stats = self._load_production_stats()
        daily_totals = production_stats.get("daily_totals", {})
        
        # Get last 7 days
        days = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily = daily_totals.get(date, {})
            days.append({
                "date": date,
                "videos": daily.get("videos", 0),
                "cost": daily.get("cost", 0)
            })
        
        return {
            "report_type": "weekly",
            "period": f"Last 7 days",
            "generated_at": datetime.now().isoformat(),
            "daily_breakdown": days,
            "total_videos": sum(d["videos"] for d in days),
            "total_cost": sum(d["cost"] for d in days),
            "average_daily_videos": sum(d["videos"] for d in days) / 7,
            "platforms_used": production_stats.get("by_platform", {}),
            "characters_used": production_stats.get("by_character", {})
        }
    
    def _generate_monthly_report(self) -> Dict[str, Any]:
        """Generate monthly report"""
        production_stats = self._load_production_stats()
        
        return {
            "report_type": "monthly",
            "month": datetime.now().strftime("%Y-%m"),
            "generated_at": datetime.now().isoformat(),
            "total_videos": production_stats.get("total_videos", 0),
            "total_credits": production_stats.get("total_credits", 0),
            "total_cost": production_stats.get("total_cost", 0),
            "platforms_used": production_stats.get("by_platform", {}),
            "characters_used": production_stats.get("by_character", {}),
            "content_types": production_stats.get("by_content_type", {})
        }


# Factory function
def create_dashboard(config_path: str = None) -> Dashboard:
    """
    Create a dashboard instance.
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        Initialized Dashboard instance
    """
    if config_path:
        config = DashboardConfig.from_json(config_path)
    else:
        config = DashboardConfig()
    
    return Dashboard(config)


if __name__ == "__main__":
    # Test dashboard generation
    print("=== Dashboard Generation ===")
    print()
    
    # Create dashboard
    dashboard = Dashboard()
    
    # Generate and save
    print("Generating dashboard...")
    output_path = dashboard.save_dashboard()
    print(f"Dashboard saved to: {output_path}")
    
    # Generate status report
    print("\nGenerating status report...")
    report = dashboard.generate_status_report()
    print(f"Status: {report.get('status')}")
    
    # Generate daily report
    print("\nGenerating daily report...")
    daily = dashboard.generate_report("daily")
    print(f"Today's videos: {daily.get('videos_created')}")
    print(f"Achievement: {daily.get('achievement_percentage'):.1f}%")
    
    # Generate weekly report
    print("\nGenerating weekly report...")
    weekly = dashboard.generate_report("weekly")
    print(f"Weekly videos: {weekly.get('total_videos')}")
    print(f"Weekly cost: ${weekly.get('total_cost'):.2f}")
