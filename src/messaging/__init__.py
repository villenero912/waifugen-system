"""
Messaging Module - Phase 2

This module provides comprehensive direct message automation system for Phase 2 platforms,
supporting message sequences, templates, campaigns, and response tracking.
"""

from .phase2_dm_automation import (
    DMAutomationManager,
    DMTemplate,
    DMSequence,
    DMMessage,
    AutomationCampaign,
    DatabaseConnection,
    VariableInterpolator,
    WelcomeSequenceBuilder,
    RetentionSequenceBuilder,
    MessageType,
    SequenceStatus,
    MessageStatus,
    Platform
)

__all__ = [
    'DMAutomationManager',
    'DMTemplate',
    'DMSequence',
    'DMMessage',
    'AutomationCampaign',
    'DatabaseConnection',
    'VariableInterpolator',
    'WelcomeSequenceBuilder',
    'RetentionSequenceBuilder',
    'MessageType',
    'SequenceStatus',
    'MessageStatus',
    'Platform'
]
