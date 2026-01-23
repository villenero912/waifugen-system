"""
Alert System Module

This module provides comprehensive alerting for the ELITE 8 AI Video Generation System,
handling credit warnings, production failures, budget exceeded, and system errors.

Features:
- Credit threshold alerts (warning, critical)
- Budget monitoring and alerts
- Production failure notifications
- System health alerts
- Alert escalation and acknowledgment
- Alert history and statistics
- Integration with Telegram bot for notifications

Version: 1.0.0
Created: 2026-01-22
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """Alert categories"""
    CREDITS = "credits"
    BUDGET = "budget"
    PRODUCTION = "production"
    UPLOAD = "upload"
    SYSTEM = "system"
    PROXY = "proxy"
    SCHEDULER = "scheduler"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"


@dataclass
class AlertRule:
    """Rule for triggering alerts"""
    name: str
    category: str
    severity: str
    condition: str  # Python expression
    threshold: float
    message: str
    enabled: bool = True
    cooldown_seconds: int = 300
    notify_telegram: bool = True
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate if alert should trigger"""
        try:
            # Create safe evaluation context
            eval_context = {
                'value': context.get(self.name, 0),
                'threshold': self.threshold,
                'context': context
            }
            return eval(eval_context.get('condition', 'False'), {"__builtins__": {}}, eval_context)
        except Exception as e:
            logger.error(f"Failed to evaluate alert rule {self.name}: {e}")
            return False


@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_name: str
    category: str
    severity: str
    title: str
    message: str
    value: float
    threshold: float
    status: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "value": self.value,
            "threshold": self.threshold,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "metadata": self.metadata
        }


@dataclass
class AlertConfig:
    """Configuration for alert system"""
    enabled: bool = True
    check_interval: int = 60  # seconds
    max_active_alerts: int = 50
    alert_history_days: int = 7
    
    # Credit thresholds
    credit_warning_percent: float = 80.0
    credit_critical_percent: float = 95.0
    daily_credits_warning: int = 10
    daily_credits_critical: int = 5
    
    # Budget thresholds
    budget_warning_percent: float = 80.0
    budget_critical_percent: float = 95.0
    
    # Production thresholds
    consecutive_failures_warning: int = 3
    consecutive_failures_critical: int = 5
    failure_rate_warning: float = 0.2  # 20%
    failure_rate_critical: float = 0.4  # 40%
    
    # Storage
    storage_path: str = "data/alerts.db"
    
    @classmethod
    def from_json(cls, config_path: str) -> 'AlertConfig':
        """Load configuration from JSON file"""
        path = Path(config_path)
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()


class AlertSystem:
    """
    Comprehensive alert system for monitoring and notification.
    
    Features:
    - Rule-based alert triggering
    - Credit and budget monitoring
    - Production failure tracking
    - Alert acknowledgment and resolution
    - Alert history and statistics
    - Telegram notification integration
    """
    
    def __init__(self, config: AlertConfig = None):
        """
        Initialize alert system.
        
        Args:
            config: Alert configuration
        """
        self.config = config or AlertConfig()
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.running = False
        self.check_task: Optional[asyncio.Task] = None
        
        # Notification callbacks
        self.notification_callbacks: List[Callable] = []
        
        # Initialize storage
        self._init_storage()
        
        # Load default rules
        self._load_default_rules()
        
        logger.info("Alert System initialized")
    
    def _init_storage(self):
        """Initialize SQLite storage for alerts"""
        storage_path = Path(self.config.storage_path)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(storage_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                rule_name TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                value REAL NOT NULL,
                threshold REAL NOT NULL,
                status TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                acknowledged_at DATETIME,
                resolved_at DATETIME,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_status 
            ON alerts(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_created 
            ON alerts(created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_category 
            ON alerts(category)
        """)
        
        self.conn.commit()
        
        # Load active alerts
        self._load_active_alerts()
    
    def _load_default_rules(self):
        """Load default alert rules"""
        default_rules = [
            # Credit rules
            AlertRule(
                name="credit_warning",
                category=AlertCategory.CREDITS.value,
                severity=AlertSeverity.WARNING.value,
                condition="value >= threshold",
                threshold=self.config.credit_warning_percent,
                message="Credit usage has reached {value:.1f}%, approaching limit",
                enabled=True,
                cooldown_seconds=3600
            ),
            AlertRule(
                name="credit_critical",
                category=AlertCategory.CREDITS.value,
                severity=AlertSeverity.CRITICAL.value,
                condition="value >= threshold",
                threshold=self.config.credit_critical_percent,
                message="CRITICAL: Credit usage at {value:.1f}%, immediate action required",
                enabled=True,
                cooldown_seconds=3600
            ),
            AlertRule(
                name="daily_credits_low",
                category=AlertCategory.CREDITS.value,
                severity=AlertSeverity.WARNING.value,
                condition="value <= threshold",
                threshold=self.config.daily_credits_warning,
                message="Daily bonus credits running low: {value} remaining",
                enabled=True,
                cooldown_seconds=1800
            ),
            
            # Budget rules
            AlertRule(
                name="budget_warning",
                category=AlertCategory.BUDGET.value,
                severity=AlertSeverity.WARNING.value,
                condition="value >= threshold",
                threshold=self.config.budget_warning_percent,
                message="Budget usage at {value:.1f}%",
                enabled=True,
                cooldown_seconds=3600
            ),
            AlertRule(
                name="budget_exceeded",
                category=AlertCategory.BUDGET.value,
                severity=AlertSeverity.CRITICAL.value,
                condition="value >= threshold",
                threshold=self.config.budget_critical_percent,
                message="BUDGET EXCEEDED: Usage at {value:.1f}%",
                enabled=True,
                cooldown_seconds=0
            ),
            
            # Production rules
            AlertRule(
                name="production_failure_high",
                category=AlertCategory.PRODUCTION.value,
                severity=AlertSeverity.WARNING.value,
                condition="value >= threshold",
                threshold=self.config.failure_rate_warning,
                message="Production failure rate high: {value:.1%}",
                enabled=True,
                cooldown_seconds=1800
            ),
            AlertRule(
                name="consecutive_failures",
                category=AlertCategory.PRODUCTION.value,
                severity=AlertSeverity.ERROR.value,
                condition="value >= threshold",
                threshold=self.config.consecutive_failures_warning,
                message="{value} consecutive production failures detected",
                enabled=True,
                cooldown_seconds=600
            ),
            
            # Upload rules
            AlertRule(
                name="upload_failure",
                category=AlertCategory.UPLOAD.value,
                severity=AlertSeverity.WARNING.value,
                condition="value > 0",
                threshold=1,
                message="Upload failed for {value} video(s)",
                enabled=True,
                cooldown_seconds=300
            ),
            
            # System rules
            AlertRule(
                name="system_cpu_high",
                category=AlertCategory.SYSTEM.value,
                severity=AlertSeverity.WARNING.value,
                condition="value >= threshold",
                threshold=90.0,
                message="CPU usage high: {value:.1f}%",
                enabled=True,
                cooldown_seconds=600
            ),
            AlertRule(
                name="system_memory_low",
                category=AlertCategory.SYSTEM.value,
                severity=AlertSeverity.WARNING.value,
                condition="value <= threshold",
                threshold=100_000_000,  # 100MB
                message="Available memory low: {value / 1e6:.1f}MB",
                enabled=True,
                cooldown_seconds=600
            ),
            AlertRule(
                name="system_disk_low",
                category=AlertCategory.SYSTEM.value,
                severity=AlertSeverity.WARNING.value,
                condition="value <= threshold",
                threshold=1_000_000_000,  # 1GB
                message="Disk space low: {value / 1e9:.1f}GB free",
                enabled=True,
                cooldown_seconds=3600
            ),
            
            # Proxy rules
            AlertRule(
                name="proxy_budget_warning",
                category=AlertCategory.PROXY.value,
                severity=AlertSeverity.WARNING.value,
                condition="value >= threshold",
                threshold=80.0,
                message="Proxy budget usage at {value:.1f}%",
                enabled=True,
                cooldown_seconds=3600
            ),
            AlertRule(
                name="proxy_data_limit",
                category=AlertCategory.PROXY.value,
                severity=AlertSeverity.CRITICAL.value,
                condition="value >= threshold",
                threshold=95.0,
                message="Proxy data limit approaching {value:.1f}%",
                enabled=True,
                cooldown_seconds=0
            ),
        ]
        
        for rule in default_rules:
            self.rules[rule.name] = rule
        
        logger.info(f"Loaded {len(self.rules)} default alert rules")
    
    def _load_active_alerts(self):
        """Load active alerts from storage"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM alerts WHERE status IN ('active', 'acknowledged')"
        )
        
        for row in cursor.fetchall():
            alert = Alert(
                id=row['id'],
                rule_name=row['rule_name'],
                category=row['category'],
                severity=row['severity'],
                title=row['title'],
                message=row['message'],
                value=row['value'],
                threshold=row['threshold'],
                status=row['status'],
                created_at=datetime.fromisoformat(row['created_at']),
                acknowledged_at=datetime.fromisoformat(row['acknowledged_at']) if row['acknowledged_at'] else None,
                resolved_at=datetime.fromisoformat(row['resolved_at']) if row['resolved_at'] else None,
                metadata=json.loads(row['metadata'] or '{}')
            )
            self.active_alerts[alert.id] = alert
        
        logger.info(f"Loaded {len(self.active_alerts)} active alerts")
    
    def add_notification_callback(self, callback: Callable):
        """Add notification callback"""
        self.notification_callbacks.append(callback)
    
    async def start(self):
        """Start alert monitoring"""
        if not self.config.enabled:
            logger.info("Alert system disabled")
            return
        
        self.running = True
        self.check_task = asyncio.create_task(self._check_loop())
        logger.info("Alert system started")
    
    async def stop(self):
        """Stop alert monitoring"""
        self.running = False
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        self.conn.close()
        logger.info("Alert system stopped")
    
    async def _check_loop(self):
        """Background check loop"""
        while self.running:
            try:
                # Build context
                context = await self._build_context()
                
                # Check all rules
                triggered = self._check_rules(context)
                
                # Handle triggered alerts
                for alert in triggered:
                    await self._trigger_alert(alert)
                
                # Clean up expired alerts
                self._cleanup_expired()
                
                await asyncio.sleep(self.config.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert check loop: {e}")
                await asyncio.sleep(5)
    
    async def _build_context(self) -> Dict[str, Any]:
        """Build context for alert evaluation"""
        context = {}
        
        # Load production stats
        try:
            stats_path = Path("data/production_stats.json")
            if stats_path.exists():
                with open(stats_path, 'r') as f:
                    stats = json.load(f)
                
                # Calculate credit usage percentage
                monthly_limit = 1800  # Default monthly limit
                monthly_used = stats.get("total_credits", 0)
                if monthly_limit > 0:
                    context["credit_usage_percent"] = (monthly_used / monthly_limit) * 100
                else:
                    context["credit_usage_percent"] = 0
                
                context["total_credits"] = monthly_used
                context["daily_credits_remaining"] = 60  # Daily bonus
                
                # Production failure rate
                total = stats.get("total_videos", 1)
                if total > 0:
                    # Calculate from history
                    pass  # Would need more detailed stats
                
        except Exception as e:
            logger.error(f"Failed to build production context: {e}")
        
        # Load system metrics
        try:
            import psutil
            
            context["cpu_percent"] = psutil.cpu_percent(interval=1)
            context["memory_available"] = psutil.virtual_memory().available
            context["disk_free"] = psutil.disk_usage('/').free
            
        except Exception as e:
            logger.error(f"Failed to build system context: {e}")
        
        # Load proxy stats
        try:
            proxy_path = Path("data/proxy_stats.json")
            if proxy_path.exists():
                with open(proxy_path, 'r') as f:
                    proxy_stats = json.load(f)
                
                data_used = proxy_stats.get("data_used_gb", 0)
                data_limit = 10.0  # Default 10GB limit
                if data_limit > 0:
                    context["proxy_usage_percent"] = (data_used / data_limit) * 100
                else:
                    context["proxy_usage_percent"] = 0
                
        except Exception as e:
            logger.error(f"Failed to build proxy context: {e}")
        
        return context
    
    def _check_rules(self, context: Dict[str, Any]) -> List[Alert]:
        """Check all rules against context"""
        triggered = []
        
        for name, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # Check cooldown
            recent = [
                alert for alert in self.active_alerts.values()
                if alert.rule_name == name and
                (datetime.now() - alert.created_at).total_seconds() < rule.cooldown_seconds
            ]
            if recent:
                continue
            
            # Evaluate rule
            if rule.evaluate(context):
                alert = Alert(
                    id=f"alert_{int(time.time())}_{name}",
                    rule_name=name,
                    category=rule.category,
                    severity=rule.severity,
                    title=f"{rule.category.upper()}: {rule.name}",
                    message=rule.message.format(**context),
                    value=context.get(name, context.get(rule.name.split('_')[0], 0)),
                    threshold=rule.threshold,
                    status=AlertStatus.ACTIVE.value,
                    created_at=datetime.now(),
                    metadata={"condition": rule.condition, "threshold": rule.threshold}
                )
                triggered.append(alert)
        
        return triggered
    
    async def _trigger_alert(self, alert: Alert):
        """Trigger an alert"""
        # Store alert
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        # Save to storage
        self._save_alert(alert)
        
        # Notify via callbacks
        for callback in self.notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Notification callback failed: {e}")
        
        # Log alert
        logger.warning(f"Alert triggered: {alert.title} - {alert.message}")
    
    def _save_alert(self, alert: Alert):
        """Save alert to storage"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO alerts
            (id, rule_name, category, severity, title, message, value, threshold, 
             status, created_at, acknowledged_at, resolved_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.id,
            alert.rule_name,
            alert.category,
            alert.severity,
            alert.title,
            alert.message,
            alert.value,
            alert.threshold,
            alert.status,
            alert.created_at.isoformat(),
            alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            alert.resolved_at.isoformat() if alert.resolved_at else None,
            json.dumps(alert.metadata)
        ))
        self.conn.commit()
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED.value
            alert.acknowledged_at = datetime.now()
            self._save_alert(alert)
            logger.info(f"Alert acknowledged: {alert_id}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED.value
            alert.resolved_at = datetime.now()
            self._save_alert(alert)
            
            # Remove from active
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False
    
    def _cleanup_expired(self):
        """Clean up expired alerts"""
        cutoff = datetime.now() - timedelta(days=self.config.alert_history_days)
        
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE alerts SET status = ? WHERE status = ? AND created_at < ?",
            (AlertStatus.EXPIRED.value, AlertStatus.ACTIVE.value, cutoff.isoformat())
        )
        self.conn.commit()
    
    def get_active_alerts(self, category: str = None, severity: str = None) -> List[Alert]:
        """Get active alerts with optional filters"""
        alerts = list(self.active_alerts.values())
        
        if category:
            alerts = [a for a in alerts if a.category == category]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda a: (
            ['critical', 'error', 'warning', 'info'].index(a.severity),
            a.created_at
        ))
    
    def get_alert_history(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        category: str = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get alert history"""
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND created_at >= ?"
            params.append(start_time.isoformat())
        if end_time:
            query += " AND created_at <= ?"
            params.append(end_time.isoformat())
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append(Alert(
                id=row['id'],
                rule_name=row['rule_name'],
                category=row['category'],
                severity=row['severity'],
                title=row['title'],
                message=row['message'],
                value=row['value'],
                threshold=row['threshold'],
                status=row['status'],
                created_at=datetime.fromisoformat(row['created_at']),
                acknowledged_at=datetime.fromisoformat(row['acknowledged_at']) if row['acknowledged_at'] else None,
                resolved_at=datetime.fromisoformat(row['resolved_at']) if row['resolved_at'] else None,
                metadata=json.loads(row['metadata'] or '{}')
            ))
        
        return alerts
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        cursor = self.conn.cursor()
        
        # Total alerts
        cursor.execute("SELECT COUNT(*) FROM alerts")
        total = cursor.fetchone()[0]
        
        # Active alerts
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE status IN ('active', 'acknowledged')")
        active = cursor.fetchone()[0]
        
        # By category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM alerts
            GROUP BY category
        """)
        by_category = {row['category']: row['count'] for row in cursor.fetchall()}
        
        # By severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM alerts
            GROUP BY severity
        """)
        by_severity = {row['severity']: row['count'] for row in cursor.fetchall()}
        
        # Last 24 hours
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE created_at >= ?", (yesterday.isoformat(),))
        last_24h = cursor.fetchone()[0]
        
        return {
            "total_alerts": total,
            "active_alerts": active,
            "by_category": by_category,
            "by_severity": by_severity,
            "last_24_hours": last_24h
        }
    
    def trigger_manual_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        category: str = "system",
        metadata: Dict = None
    ) -> Alert:
        """Manually trigger an alert"""
        alert = Alert(
            id=f"alert_manual_{int(time.time())}",
            rule_name="manual",
            category=category,
            severity=severity,
            title=title,
            message=message,
            value=0,
            threshold=0,
            status=AlertStatus.ACTIVE.value,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        self.active_alerts[alert.id] = alert
        self._save_alert(alert)
        
        # Notify
        for callback in self.notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(alert))
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Notification callback failed: {e}")
        
        return alert
    
    def add_rule(self, rule: AlertRule):
        """Add a custom alert rule"""
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove an alert rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
            return True
        return False
    
    def update_rule(self, rule_name: str, **kwargs) -> bool:
        """Update an alert rule"""
        if rule_name in self.rules:
            for key, value in kwargs.items():
                if hasattr(self.rules[rule_name], key):
                    setattr(self.rules[rule_name], key, value)
            logger.info(f"Updated alert rule: {rule_name}")
            return True
        return False


# Factory function
def create_alert_system(config_path: str = None) -> AlertSystem:
    """
    Create and initialize an alert system.
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        Initialized AlertSystem instance
    """
    if config_path:
        config = AlertConfig.from_json(config_path)
    else:
        config = AlertConfig()
    
    return AlertSystem(config)


if __name__ == "__main__":
    # Test alert system
    print("=== Alert System ===")
    print()
    
    # Create alert system
    alert_system = AlertSystem()
    
    # Show configured rules
    print(f"Loaded {len(alert_system.rules)} alert rules:")
    for name, rule in alert_system.rules.items():
        status = "enabled" if rule.enabled else "disabled"
        print(f"  • {name} ({rule.severity}) - {status}")
    print()
    
    # Get stats
    stats = alert_system.get_alert_stats()
    print("Alert Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Trigger test alert
    print("Triggering test alert...")
    alert = alert_system.trigger_manual_alert(
        title="Test Alert",
        message="This is a test alert from the alert system",
        severity="info",
        category="system"
    )
    print(f"Created alert: {alert.id}")
    
    # Get active alerts
    alerts = alert_system.get_active_alerts()
    print(f"Active alerts: {len(alerts)}")
    
    # Resolve alert
    alert_system.resolve_alert(alert.id)
    print("Alert resolved")
    
    # Stop alert system
    asyncio.run(alert_system.stop())
