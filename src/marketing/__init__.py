"""
Marketing Module - Phase 2

This module provides marketing and growth tools for the ELITE 8 AI Video Generation System,
including conversion funnel management, regional configuration, and audience targeting.

Modules:
- conversion_funnel: Multi-stage conversion funnel for audience growth
- regional_config: Country and region-specific configurations for Phase 2

Version: 2.0.0
Created: 2026-01-22
"""

from .conversion_funnel import (
    ConversionFunnel,
    FunnelConfig,
    FunnelStep,
    FunnelStage,
    ContentCategory,
    PlatformTarget,
    create_conversion_funnel
)

from .regional_config import (
    RegionalManager,
    RegionalStrategy,
    CountryConfig,
    Region,
    Country,
    Language,
    TimeWindow,
    PlatformPreference,
    ComplianceRequirement,
    LocalizedContent,
    create_regional_manager
)

__all__ = [
    # Conversion Funnel
    'ConversionFunnel',
    'FunnelConfig',
    'FunnelStep',
    'FunnelStage',
    'ContentCategory',
    'PlatformTarget',
    'create_conversion_funnel',
    
    # Regional Configuration
    'RegionalManager',
    'RegionalStrategy',
    'CountryConfig',
    'Region',
    'Country',
    'Language',
    'TimeWindow',
    'PlatformPreference',
    'ComplianceRequirement',
    'LocalizedContent',
    'create_regional_manager'
]
