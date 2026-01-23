"""
Elite 8 AI Video Generation System - Main Package

This package provides comprehensive AI video generation capabilities
with social media integration, scheduling, monitoring, and Phase 2 expansion.

Phase 1: Core video generation and social media automation (TikTok, Instagram, YouTube)
Phase 2: International expansion, conversion funnels, and subscriber management

Version: 2.0.0
Created: 2026-01-22
"""

__version__ = "2.0.0"
__author__ = "Elite 8 Team"
__phase__ = "Phase 2"

# Core modules - Phase 1
from .api import a2e_client
from .database import (
    DatabaseManager,
    JobStatus,
    PostStatus,
    Platform,
    get_db,
    init_sample_data
)
from .scheduler import (
    JobScheduler,
    ContentScheduler,
    ScheduleType,
    get_scheduler,
    get_content_scheduler
)
from .social import (
    SocialMediaManager,
    PlatformType,
    PostResult,
    EngagementMetrics,
    ProxyManager,
    check_proxy_status,
    quick_post_all
)

# Monitoring modules - Phase 1 & 2
from .monitoring import (
    ProductionMonitor,
    TelegramBot,
    MetricsCollector,
    AlertSystem,
    Dashboard,
    create_production_monitor,
    create_telegram_bot,
    create_metrics_collector,
    create_alert_system,
    create_dashboard
)

# Marketing modules - Phase 2
from .marketing import (
    ConversionFunnel,
    FunnelStage,
    ContentCategory,
    PlatformTarget,
    RegionalManager,
    RegionalStrategy,
    CountryConfig,
    Region,
    Language,
    create_conversion_funnel,
    create_regional_manager
)

# Subscriber management - Phase 2 (for premium platforms)
from .subscribers import (
    SubscriberManager,
    SubscriptionTier,
    SubscriptionStatus,
    Platform as SubscriberPlatform,
    DatabaseConnection,
    create_subscriber_manager
)

__all__ = [
    # Version and metadata
    "__version__",
    "__author__",
    "__phase__",
    
    # API - Phase 1
    "a2e_client",
    
    # Database - Phase 1
    "DatabaseManager",
    "JobStatus",
    "PostStatus",
    "Platform",
    "get_db",
    "init_sample_data",
    
    # Scheduler - Phase 1
    "JobScheduler",
    "ContentScheduler",
    "ScheduleType",
    "get_scheduler",
    "get_content_scheduler",
    
    # Social - Phase 1
    "SocialMediaManager",
    "PlatformType",
    "PostResult",
    "EngagementMetrics",
    "ProxyManager",
    "check_proxy_status",
    "quick_post_all",
    
    # Monitoring - Phase 1 & 2
    "ProductionMonitor",
    "TelegramBot",
    "MetricsCollector",
    "AlertSystem",
    "Dashboard",
    "create_production_monitor",
    "create_telegram_bot",
    "create_metrics_collector",
    "create_alert_system",
    "create_dashboard",
    
    # Marketing - Phase 2
    "ConversionFunnel",
    "FunnelStage",
    "ContentCategory",
    "PlatformTarget",
    "RegionalManager",
    "RegionalStrategy",
    "CountryConfig",
    "Region",
    "Language",
    "create_conversion_funnel",
    "create_regional_manager",
    
    # Subscribers - Phase 2
    "SubscriberManager",
    "SubscriptionTier",
    "SubscriptionStatus",
    "SubscriberPlatform",
    "DatabaseConnection",
    "create_subscriber_manager"
]
