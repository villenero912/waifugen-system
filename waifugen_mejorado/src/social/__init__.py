"""
Social Media Integration Module for Elite 8 AI Video Generation System

This module provides comprehensive integration with TikTok, Instagram, and YouTube
APIs for automated video uploading, engagement tracking, and audience analytics.
"""

from .base_client import SocialMediaClient, PlatformType, PostResult, EngagementMetrics
from .tiktok_client import TikTokClient, TikTokVideoConfig
from .instagram_client import InstagramClient, InstagramReelConfig
from .youtube_client import YouTubeClient, YouTubeShortConfig
from .social_manager import (
    SocialMediaManager,
    PostingConfig,
    PostCampaign,
    quick_post_all
)
from .proxy_manager import (
    ProxyManager,
    ProxyCredentials,
    ProxyStats,
    BudgetAlert,
    check_proxy_status
)

__all__ = [
    "SocialMediaClient",
    "PlatformType",
    "PostResult",
    "EngagementMetrics",
    "TikTokClient",
    "TikTokVideoConfig",
    "InstagramClient",
    "InstagramReelConfig",
    "YouTubeClient",
    "YouTubeShortConfig",
    "SocialMediaManager",
    "PostingConfig",
    "PostCampaign",
    "quick_post_all",
    "ProxyManager",
    "ProxyCredentials",
    "ProxyStats",
    "BudgetAlert",
    "check_proxy_status"
]
