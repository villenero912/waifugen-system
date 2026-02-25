"""
Monitoring Module - Phase 4

This module provides comprehensive monitoring for the ELITE 8 AI Video Generation System,
including production tracking, metrics collection, alerting, and Telegram notifications.

Modules:
- phase1_production_monitor: Production statistics and credit tracking
- telegram_bot: Telegram bot integration for notifications and commands
- metrics_collector: System metrics collection and storage
- alert_system: Alert management and notification
- dashboard: HTML dashboard generation

Version: 4.0.0
Created: 2026-01-22
"""

from .phase1_production_monitor import (
    ProductionMonitor,
    ProductionConfig,
    A2EApiClient,
    A2ECreditStatus,
    VideoProductionStats,
    DailyProductionSummary,
    ProductionStatus,
    ContentType,
    Platform,
    create_production_monitor
)

from .telegram_bot import (
    TelegramBot,
    TelegramConfig,
    NotificationType,
    create_telegram_bot,
    send_telegram_message,
    send_telegram_photo
)

from .metrics_collector import (
    MetricsCollector,
    MetricsConfig,
    Metric,
    MetricType,
    create_metrics_collector
)

from .alert_system import (
    AlertSystem,
    AlertConfig,
    Alert,
    AlertRule,
    AlertSeverity,
    AlertCategory,
    AlertStatus,
    create_alert_system
)

from .dashboard import (
    Dashboard,
    DashboardConfig,
    create_dashboard
)

__all__ = [
    # Production Monitor
    'ProductionMonitor',
    'ProductionConfig',
    'A2EApiClient',
    'A2ECreditStatus',
    'VideoProductionStats',
    'DailyProductionSummary',
    'ProductionStatus',
    'ContentType',
    'Platform',
    'create_production_monitor',
    
    # Telegram Bot
    'TelegramBot',
    'TelegramConfig',
    'NotificationType',
    'create_telegram_bot',
    'send_telegram_message',
    'send_telegram_photo',
    
    # Metrics Collector
    'MetricsCollector',
    'MetricsConfig',
    'Metric',
    'MetricType',
    'create_metrics_collector',
    
    # Alert System
    'AlertSystem',
    'AlertConfig',
    'Alert',
    'AlertRule',
    'AlertSeverity',
    'AlertCategory',
    'AlertStatus',
    'create_alert_system',
    
    # Dashboard
    'Dashboard',
    'DashboardConfig',
    'create_dashboard'
]
