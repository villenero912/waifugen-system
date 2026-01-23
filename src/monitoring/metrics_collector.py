"""
Metrics Collection Module

This module provides comprehensive metrics collection for system monitoring,
including production statistics, resource utilization, and performance metrics.

Features:
- Production metrics (videos, credits, costs)
- System resource monitoring (CPU, memory, disk, network)
- A2E API usage tracking
- Social media posting metrics
- Proxy bandwidth usage
- Time-series data storage
- Metrics export for Prometheus

Version: 1.0.0
Created: 2026-01-22
"""

import asyncio
import json
import logging
import os
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import sqlite3
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    type: str
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    
    def to_prometheus(self) -> str:
        """Format metric for Prometheus export"""
        label_str = ""
        if self.labels:
            label_parts = [f'{k}="{v}"' for k, v in self.labels.items()]
            label_str = "{" + ",".join(label_parts) + "}"
        
        return f"# HELP {self.name} {self.description}\n# TYPE {self.name} {self.type}\n{self.name}{label_str} {self.value} {int(self.timestamp.timestamp() * 1000)}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.type,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description
        }


@dataclass
class MetricsConfig:
    """Configuration for metrics collection"""
    enabled: bool = True
    collection_interval: int = 60  # seconds
    storage_path: str = "data/metrics.db"
    retention_days: int = 30
    export_prometheus: bool = True
    prometheus_port: int = 9090
    prometheus_path: str = "/metrics"
    track_cpu: bool = True
    track_memory: bool = True
    track_disk: bool = True
    track_network: bool = True
    track_production: bool = True
    track_proxy: bool = True
    
    @classmethod
    def from_json(cls, config_path: str) -> 'MetricsConfig':
        """Load configuration from JSON file"""
        path = Path(config_path)
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()


class MetricsCollector:
    """
    Central metrics collection system.
    
    Collects and stores metrics from:
    - System resources (CPU, memory, disk, network)
    - Production statistics (videos, credits, costs)
    - A2E API usage
    - Social media operations
    - Proxy bandwidth
    
    Provides:
    - Real-time metric streaming
    - Historical data storage
    - Prometheus export endpoint
    """
    
    def __init__(self, config: MetricsConfig = None):
        """
        Initialize metrics collector.
        
        Args:
            config: Metrics configuration
        """
        self.config = config or MetricsConfig()
        self.metrics_buffer: List[Metric] = []
        self.running = False
        self.collection_task: Optional[asyncio.Task] = None
        
        # Initialize storage
        self._init_storage()
        
        # Initialize production tracker
        self.production_stats = self._load_production_stats()
        
        logger.info("Metrics Collector initialized")
    
    def _init_storage(self):
        """Initialize SQLite storage for metrics"""
        storage_path = Path(self.config.storage_path)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(storage_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Create tables
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                type TEXT NOT NULL,
                labels TEXT,
                timestamp DATETIME NOT NULL,
                description TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS production_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                labels TEXT,
                UNIQUE(date, metric_name, labels)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
            ON metrics(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_name 
            ON metrics(name)
        """)
        
        self.conn.commit()
        
        # Clean old data
        self._cleanup_old_data()
    
    def _cleanup_old_data(self):
        """Remove metrics older than retention period"""
        try:
            cursor = self.conn.cursor()
            cutoff = datetime.now() - timedelta(days=self.config.retention_days)
            cursor.execute(
                "DELETE FROM metrics WHERE timestamp < ?",
                (cutoff,)
            )
            self.conn.commit()
            logger.info("Old metrics cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
    
    def _load_production_stats(self) -> Dict:
        """Load production statistics from file"""
        stats_path = Path("data/production_stats.json")
        if stats_path.exists():
            try:
                with open(stats_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load production stats: {e}")
        return {
            "total_videos": 0,
            "total_credits": 0,
            "total_cost": 0,
            "by_platform": defaultdict(int),
            "by_character": defaultdict(int),
            "by_content_type": defaultdict(int),
            "daily_totals": {}
        }
    
    def _save_production_stats(self):
        """Save production statistics to file"""
        stats_path = Path("data/production_stats.json")
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(stats_path, 'w') as f:
                json.dump(self.production_stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save production stats: {e}")
    
    async def start(self):
        """Start metrics collection"""
        if not self.config.enabled:
            logger.info("Metrics collection disabled")
            return
        
        self.running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collection started")
    
    async def stop(self):
        """Stop metrics collection"""
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        # Flush buffer
        self._flush_buffer()
        self.conn.close()
        logger.info("Metrics collection stopped")
    
    async def _collection_loop(self):
        """Background collection loop"""
        while self.running:
            try:
                await self.collect_all()
                await asyncio.sleep(self.config.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(5)  # Short delay on error
    
    async def collect_all(self):
        """Collect all enabled metrics"""
        timestamp = datetime.now()
        
        # System metrics
        if self.config.track_cpu:
            self._collect_cpu_metrics(timestamp)
        if self.config.track_memory:
            self._collect_memory_metrics(timestamp)
        if self.config.track_disk:
            self._collect_disk_metrics(timestamp)
        if self.config.track_network:
            self._collect_network_metrics(timestamp)
        
        # Production metrics
        if self.config.track_production:
            await self._collect_production_metrics(timestamp)
        
        # Proxy metrics
        if self.config.track_proxy:
            self._collect_proxy_metrics(timestamp)
        
        # Flush to storage
        self._flush_buffer()
    
    def _collect_cpu_metrics(self, timestamp: datetime):
        """Collect CPU metrics"""
        try:
            # CPU percentage (all cores)
            cpu_percent = psutil.cpu_percent(interval=1)
            self._add_metric(Metric(
                name="system_cpu_percent",
                value=cpu_percent,
                type=MetricType.GAUGE.value,
                labels={"core": "all"},
                timestamp=timestamp,
                description="CPU usage percentage across all cores"
            ))
            
            # Per-core CPU
            for i, percent in enumerate(psutil.cpu_percent(interval=None, percpu=True)):
                self._add_metric(Metric(
                    name="system_cpu_percent",
                    value=percent,
                    type=MetricType.GAUGE.value,
                    labels={"core": f"cpu{i}"},
                    timestamp=timestamp,
                    description=f"CPU usage percentage for core {i}"
                ))
            
            # Load average (if available)
            load_avg = psutil.getloadavg()
            self._add_metric(Metric(
                name="system_load_avg_1m",
                value=load_avg[0],
                type=MetricType.GAUGE.value,
                timestamp=timestamp,
                description="System load average (1 minute)"
            ))
            self._add_metric(Metric(
                name="system_load_avg_5m",
                value=load_avg[1],
                type=MetricType.GAUGE.value,
                timestamp=timestamp,
                description="System load average (5 minutes)"
            ))
            
        except Exception as e:
            logger.error(f"Failed to collect CPU metrics: {e}")
    
    def _collect_memory_metrics(self, timestamp: datetime):
        """Collect memory metrics"""
        try:
            memory = psutil.virtual_memory()
            
            self._add_metric(Metric(
                name="system_memory_bytes",
                value=memory.total,
                type=MetricType.GAUGE.value,
                labels={"type": "total"},
                timestamp=timestamp,
                description="Total system memory in bytes"
            ))
            self._add_metric(Metric(
                name="system_memory_bytes",
                value=memory.used,
                type=MetricType.GAUGE.value,
                labels={"type": "used"},
                timestamp=timestamp,
                description="Used system memory in bytes"
            ))
            self._add_metric(Metric(
                name="system_memory_bytes",
                value=memory.available,
                type=MetricType.GAUGE.value,
                labels={"type": "available"},
                timestamp=timestamp,
                description="Available system memory in bytes"
            ))
            self._add_metric(Metric(
                name="system_memory_percent",
                value=memory.percent,
                type=MetricType.GAUGE.value,
                timestamp=timestamp,
                description="Memory usage percentage"
            ))
            
            # Swap memory
            swap = psutil.swap_memory()
            self._add_metric(Metric(
                name="system_swap_bytes",
                value=swap.used,
                type=MetricType.GAUGE.value,
                labels={"type": "used"},
                timestamp=timestamp,
                description="Used swap memory in bytes"
            ))
            self._add_metric(Metric(
                name="system_swap_percent",
                value=swap.percent,
                type=MetricType.GAUGE.value,
                timestamp=timestamp,
                description="Swap usage percentage"
            ))
            
        except Exception as e:
            logger.error(f"Failed to collect memory metrics: {e}")
    
    def _collect_disk_metrics(self, timestamp: datetime):
        """Collect disk metrics"""
        try:
            disk_usage = psutil.disk_usage('/')
            
            self._add_metric(Metric(
                name="system_disk_bytes",
                value=disk_usage.total,
                type=MetricType.GAUGE.value,
                labels={"type": "total"},
                timestamp=timestamp,
                description="Total disk space in bytes"
            ))
            self._add_metric(Metric(
                name="system_disk_bytes",
                value=disk_usage.used,
                type=MetricType.GAUGE.value,
                labels={"type": "used"},
                timestamp=timestamp,
                description="Used disk space in bytes"
            ))
            self._add_metric(Metric(
                name="system_disk_bytes",
                value=disk_usage.free,
                type=MetricType.GAUGE.value,
                labels={"type": "free"},
                timestamp=timestamp,
                description="Free disk space in bytes"
            ))
            self._add_metric(Metric(
                name="system_disk_percent",
                value=disk_usage.percent,
                type=MetricType.GAUGE.value,
                timestamp=timestamp,
                description="Disk usage percentage"
            ))
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self._add_metric(Metric(
                    name="system_disk_io_bytes",
                    value=disk_io.read_bytes,
                    type=MetricType.COUNTER.value,
                    labels={"type": "read"},
                    timestamp=timestamp,
                    description="Total disk read bytes"
                ))
                self._add_metric(Metric(
                    name="system_disk_io_bytes",
                    value=disk_io.write_bytes,
                    type=MetricType.COUNTER.value,
                    labels={"type": "write"},
                    timestamp=timestamp,
                    description="Total disk write bytes"
                ))
                
        except Exception as e:
            logger.error(f"Failed to collect disk metrics: {e}")
    
    def _collect_network_metrics(self, timestamp: datetime):
        """Collect network metrics"""
        try:
            net_io = psutil.net_io_counters()
            
            self._add_metric(Metric(
                name="system_network_bytes",
                value=net_io.bytes_sent,
                type=MetricType.COUNTER.value,
                labels={"type": "sent"},
                timestamp=timestamp,
                description="Total network bytes sent"
            ))
            self._add_metric(Metric(
                name="system_network_bytes",
                value=net_io.bytes_recv,
                type=MetricType.COUNTER.value,
                labels={"type": "recv"},
                timestamp=timestamp,
                description="Total network bytes received"
            ))
            self._add_metric(Metric(
                name="system_network_packets",
                value=net_io.packets_sent,
                type=MetricType.COUNTER.value,
                labels={"type": "sent"},
                timestamp=timestamp,
                description="Total network packets sent"
            ))
            self._add_metric(Metric(
                name="system_network_packets",
                value=net_io.packets_recv,
                type=MetricType.COUNTER.value,
                labels={"type": "recv"},
                timestamp=timestamp,
                description="Total network packets received"
            ))
            
            # Connection count
            connections = len(psutil.net_connections())
            self._add_metric(Metric(
                name="system_network_connections",
                value=connections,
                type=MetricType.GAUGE.value,
                timestamp=timestamp,
                description="Number of network connections"
            ))
            
        except Exception as e:
            logger.error(f"Failed to collect network metrics: {e}")
    
    async def _collect_production_metrics(self, timestamp: datetime):
        """Collect production metrics"""
        try:
            # Load current stats
            stats = self._load_production_stats()
            
            # Total videos
            self._add_metric(Metric(
                name="production_total_videos",
                value=stats.get("total_videos", 0),
                type=MetricType.COUNTER.value,
                timestamp=timestamp,
                description="Total videos produced"
            ))
            
            # Total credits used
            self._add_metric(Metric(
                name="production_total_credits",
                value=stats.get("total_credits", 0),
                type=MetricType.COUNTER.value,
                timestamp=timestamp,
                description="Total credits used"
            ))
            
            # Total cost
            self._add_metric(Metric(
                name="production_total_cost_usd",
                value=stats.get("total_cost", 0),
                type=MetricType.COUNTER.value,
                timestamp=timestamp,
                description="Total production cost in USD"
            ))
            
            # By platform
            for platform, count in stats.get("by_platform", {}).items():
                self._add_metric(Metric(
                    name="production_videos_total",
                    value=count,
                    type=MetricType.COUNTER.value,
                    labels={"platform": platform},
                    timestamp=timestamp,
                    description=f"Total videos for {platform}"
                ))
            
            # By character
            for character, count in stats.get("by_character", {}).items():
                self._add_metric(Metric(
                    name="production_videos_total",
                    value=count,
                    type=MetricType.COUNTER.value,
                    labels={"character": character},
                    timestamp=timestamp,
                    description=f"Total videos for {character}"
                ))
            
            # By content type
            for content_type, count in stats.get("by_content_type", {}).items():
                self._add_metric(Metric(
                    name="production_videos_total",
                    value=count,
                    type=MetricType.COUNTER.value,
                    labels={"content_type": content_type},
                    timestamp=timestamp,
                    description=f"Total videos of type {content_type}"
                ))
            
            # Today's production
            today = datetime.now().strftime("%Y-%m-%d")
            daily = stats.get("daily_totals", {}).get(today, {})
            self._add_metric(Metric(
                name="production_videos_daily",
                value=daily.get("videos", 0),
                type=MetricType.GAUGE.value,
                timestamp=timestamp,
                description="Videos produced today"
            ))
            self._add_metric(Metric(
                name="production_cost_daily_usd",
                value=daily.get("cost", 0),
                type=MetricType.GAUGE.value,
                timestamp=timestamp,
                description="Cost incurred today"
            ))
            
        except Exception as e:
            logger.error(f"Failed to collect production metrics: {e}")
    
    def _collect_proxy_metrics(self, timestamp: datetime):
        """Collect proxy usage metrics"""
        try:
            # Load proxy stats
            proxy_stats_path = Path("data/proxy_stats.json")
            if proxy_stats_path.exists():
                with open(proxy_stats_path, 'r') as f:
                    proxy_stats = json.load(f)
                
                self._add_metric(Metric(
                    name="proxy_data_used_gb",
                    value=proxy_stats.get("data_used_gb", 0),
                    type=MetricType.GAUGE.value,
                    timestamp=timestamp,
                    description="Proxy data used this month (GB)"
                ))
                self._add_metric(Metric(
                    name="proxy_cost_monthly_usd",
                    value=proxy_stats.get("cost_usd", 0),
                    type=MetricType.GAUGE.value,
                    timestamp=timestamp,
                    description="Proxy cost this month (USD)"
                ))
                self._add_metric(Metric(
                    name="proxy_remaining_budget_usd",
                    value=proxy_stats.get("remaining_budget", 0),
                    type=MetricType.GAUGE.value,
                    timestamp=timestamp,
                    description="Remaining proxy budget (USD)"
                ))
                
        except Exception as e:
            logger.error(f"Failed to collect proxy metrics: {e}")
    
    def record_production(
        self,
        character_id: str,
        content_type: str,
        platform: str,
        credits_used: float,
        cost: float,
        success: bool
    ):
        """Record a production event"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Update totals
        self.production_stats["total_videos"] += 1
        self.production_stats["total_credits"] += credits_used
        self.production_stats["total_cost"] += cost
        
        self.production_stats["by_platform"][platform] += 1
        self.production_stats["by_character"][character_id] += 1
        self.production_stats["by_content_type"][content_type] += 1
        
        # Update daily
        if today not in self.production_stats["daily_totals"]:
            self.production_stats["daily_totals"][today] = {
                "videos": 0,
                "credits": 0,
                "cost": 0
            }
        
        self.production_stats["daily_totals"][today]["videos"] += 1
        self.production_stats["daily_totals"][today]["credits"] += credits_used
        self.production_stats["daily_totals"][today]["cost"] += cost
        
        # Save
        self._save_production_stats()
    
    def _add_metric(self, metric: Metric):
        """Add metric to buffer"""
        self.metrics_buffer.append(metric)
    
    def _flush_buffer(self):
        """Flush metrics buffer to storage"""
        if not self.metrics_buffer:
            return
        
        try:
            cursor = self.conn.cursor()
            
            for metric in self.metrics_buffer:
                cursor.execute("""
                    INSERT INTO metrics 
                    (name, value, type, labels, timestamp, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    metric.name,
                    metric.value,
                    metric.type,
                    json.dumps(metric.labels),
                    metric.timestamp,
                    metric.description
                ))
            
            self.conn.commit()
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics buffer: {e}")
    
    def query_metrics(
        self,
        name: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        labels: Dict = None,
        limit: int = 100
    ) -> List[Metric]:
        """
        Query stored metrics.
        
        Args:
            name: Metric name filter
            start_time: Start of time range
            end_time: End of time range
            labels: Label filters
            limit: Maximum results
            
        Returns:
            List of matching metrics
        """
        query = "SELECT * FROM metrics WHERE 1=1"
        params = []
        
        if name:
            query += " AND name = ?"
            params.append(name)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        if labels:
            for key, value in labels.items():
                query += f" AND labels LIKE ?"
                params.append(f'"{key}": "{value}"')
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append(Metric(
                name=row['name'],
                value=row['value'],
                type=row['type'],
                labels=json.loads(row['labels'] or '{}'),
                timestamp=datetime.fromisoformat(row['timestamp']),
                description=row['description']
            ))
        
        return results
    
    def get_current_values(self) -> Dict[str, Any]:
        """Get current metric values for dashboard"""
        cursor = self.conn.cursor()
        
        # Get latest values for each metric name
        cursor.execute("""
            SELECT name, value, labels, timestamp
            FROM metrics m1
            WHERE timestamp = (
                SELECT MAX(timestamp) FROM metrics m2 WHERE m2.name = m1.name
            )
            ORDER BY name
        """)
        
        metrics = {}
        for row in cursor.fetchall():
            label_key = row['labels'] if row['labels'] else ''
            key = f"{row['name']}{label_key}"
            metrics[key] = {
                "value": row['value'],
                "timestamp": row['timestamp']
            }
        
        return metrics
    
    def export_prometheus(self) -> str:
        """Export all metrics in Prometheus format"""
        lines = []
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT name, type, description
            FROM metrics
        """)
        
        metric_types = {}
        for row in cursor.fetchall():
            metric_types[row['name']] = (row['type'], row['description'])
        
        # Get latest values
        metrics = self.get_current_values()
        
        for key, data in metrics.items():
            name_parts = key.split('{')
            name = name_parts[0]
            labels = name_parts[1].rstrip('}') if len(name_parts) > 1 else ''
            
            metric_type, description = metric_types.get(name, ('gauge', ''))
            
            lines.append(f"# HELP {name} {description}")
            lines.append(f"# TYPE {name} {metric_type}")
            
            if labels:
                lines.append(f"{name}{{{labels}}} {data['value']}")
            else:
                lines.append(f"{name} {data['value']}")
        
        return '\n'.join(lines)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics collection summary"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM metrics")
        total_metrics = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT name) FROM metrics")
        unique_metrics = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM metrics")
        time_range = cursor.fetchone()
        
        return {
            "enabled": self.config.enabled,
            "collection_interval": self.config.collection_interval,
            "total_metrics_collected": total_metrics,
            "unique_metric_names": unique_metrics,
            "oldest_metric": time_range[0],
            "newest_metric": time_range[1],
            "buffer_size": len(self.metrics_buffer),
            "storage_path": self.config.storage_path
        }


# Factory function
def create_metrics_collector(config_path: str = None) -> MetricsCollector:
    """
    Create and initialize a metrics collector.
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        Initialized MetricsCollector instance
    """
    if config_path:
        config = MetricsConfig.from_json(config_path)
    else:
        config = MetricsConfig()
    
    return MetricsCollector(config)


if __name__ == "__main__":
    # Test metrics collection
    print("=== Metrics Collection System ===")
    print()
    
    # Create collector
    collector = MetricsCollector()
    
    # Get summary
    summary = collector.get_summary()
    print("Collector Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()
    
    # Collect metrics once
    print("Collecting metrics...")
    asyncio.run(collector.collect_all())
    
    # Get current values
    values = collector.get_current_values()
    print(f"Collected {len(values)} unique metrics:")
    for key, data in list(values.items())[:10]:
        print(f"  {key}: {data['value']}")
    
    # Export to Prometheus
    prom_output = collector.export_prometheus()
    print(f"\nPrometheus export ({len(prom_output)} chars)")
    print(prom_output[:500] + "..." if len(prom_output) > 500 else prom_output)
    
    # Stop collector
    asyncio.run(collector.stop())
