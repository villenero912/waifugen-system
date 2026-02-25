"""
Subscribers Module - Phase 2

This module provides comprehensive subscriber management capabilities for Phase 2 platforms
including OnlyFans, XVideos, Pornhub, and Japanese platforms (FC2, Fantia, Line).
"""

from .phase2_subscriber_manager import (
    SubscriberManager,
    Subscriber,
    TierHistory,
    EngagementMetrics,
    WinbackCampaign,
    DatabaseConnection,
    SubscriptionTier,
    SubscriptionStatus,
    Platform
)

def create_subscriber_manager(db_config: dict) -> SubscriberManager:
    """
    Create a subscriber manager instance.
    
    Args:
        db_config: Database configuration dictionary
        
    Returns:
        Initialized SubscriberManager instance
    """
    db_connection = DatabaseConnection(db_config)
    return SubscriberManager(db_connection)

__all__ = [
    'SubscriberManager',
    'Subscriber',
    'TierHistory',
    'EngagementMetrics', 
    'WinbackCampaign',
    'DatabaseConnection',
    'SubscriptionTier',
    'SubscriptionStatus',
    'Platform',
    'create_subscriber_manager'
]
