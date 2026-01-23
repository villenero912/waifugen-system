"""
Phase 2 Regional Configuration

This module defines country and region-specific configurations for the ELITE 8 AI Video Generation System Phase 2 expansion,
including timezone optimization, content localization, platform preferences, and compliance requirements.

Target Markets:
- North America (US, Canada)
- Europe (UK, Germany, France, Spain, Italy)
- Asia Pacific (Japan, South Korea, Australia)
- Latin America (Brazil, Mexico, Argentina)

Version: 2.0.0
Created: 2026-01-22
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Region(Enum):
    """Target regions for Phase 2"""
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    LATIN_AMERICA = "latin_america"
    MIDDLE_EAST = "middle_east"
    AFRICA = "africa"


class Country(Enum):
    """Target countries"""
    # North America
    UNITED_STATES = "US"
    CANADA = "CA"
    MEXICO = "MX"
    
    # Europe
    UNITED_KINGDOM = "GB"
    GERMANY = "DE"
    FRANCE = "FR"
    SPAIN = "ES"
    ITALY = "IT"
    NETHERLANDS = "NL"
    POLAND = "PL"
    
    # Asia Pacific
    JAPAN = "JP"
    SOUTH_KOREA = "KR"
    AUSTRALIA = "AU"
    NEW_ZEALAND = "NZ"
    INDONESIA = "ID"
    PHILIPPINES = "PH"
    
    # Latin America
    BRAZIL = "BR"
    ARGENTINA = "AR"
    COLOMBIA = "CO"
    CHILE = "CL"
    PERU = "PE"


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    PORTUGUESE = "pt"
    JAPANESE = "ja"
    KOREAN = "ko"
    GERMAN = "de"
    FRENCH = "fr"
    ITALIAN = "it"
    CHINESE = "zh"


@dataclass
class TimeWindow:
    """Optimal posting time window"""
    start_hour: int
    end_hour: int
    timezone: str
    best_days: List[str]  # ["Monday", "Tuesday", etc.]
    
    def get_local_time_ranges(self) -> List[str]:
        """Get time ranges in local time"""
        return [f"{self.start_hour:02d}:00 - {self.end_hour:02d}:00"]


@dataclass
class PlatformPreference:
    """Platform preferences for a region"""
    platform: str
    priority: int  # 1 = highest
    content_format: str  # "short", "long", "reel", etc.
    optimal_duration: int  # seconds
    posting_frequency: int  # per day
    
    local_trends: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)


@dataclass
class ComplianceRequirement:
    """Legal/compliance requirements for a region"""
    requires_age_verification: bool = False
    minimum_age: int = 13
    data_retention_days: int = 365
    requires_content_moderation: bool = True
    restricted_content_categories: List[str] = field(default_factory=list)
    platform_specific_rules: Dict = field(default_factory=dict)
    tax_implications: str = ""
    monetization_restrictions: str = ""


@dataclass
class LocalizedContent:
    """Content localization settings"""
    language: str
    character_names_localized: Dict[str, str] = field(default_factory=dict)
    trending_topics: List[str] = field(default_factory=list)
    cultural_notes: List[str] = field(default_factory=list)
    prohibited_content: List[str] = field(default_factory=list)
    holiday_calendar: List[str] = field(default_factory=list)


@dataclass
class CountryConfig:
    """Complete country configuration"""
    country_code: str
    country_name: str
    region: str
    language: str
    timezone: str
    currency: str
    
    # Content preferences
    optimal_posting_windows: List[TimeWindow]
    platform_preferences: List[PlatformPreference]
    
    # Compliance
    compliance: ComplianceRequirement
    
    # Localization
    localization: LocalizedContent
    
    # Market data
    market_size: int  # Estimated audience size
    growth_potential: float  # 0.0 - 1.0
    competition_level: str  # "low", "medium", "high"
    
    # Campaign settings
    daily_budget_usd: float
    target_roas: float  # Return on ad spend target
    
    @classmethod
    def from_json(cls, config_path: str, country_code: str = None) -> 'CountryConfig':
        """Load configuration from JSON file"""
        path = Path(config_path)
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                
                if country_code and country_code in data:
                    country_data = data[country_code]
                    return cls(
                        country_code=country_code,
                        country_name=country_data.get('country_name', ''),
                        region=country_data.get('region', ''),
                        language=country_data.get('language', ''),
                        timezone=country_data.get('timezone', ''),
                        currency=country_data.get('currency', ''),
                        optimal_posting_windows=[
                            TimeWindow(**w) for w in country_data.get('optimal_posting_windows', [])
                        ],
                        platform_preferences=[
                            PlatformPreference(**p) for p in country_data.get('platform_preferences', [])
                        ],
                        compliance=ComplianceRequirement(**country_data.get('compliance', {})),
                        localization=LocalizedContent(**country_data.get('localization', {})),
                        market_size=country_data.get('market_size', 0),
                        growth_potential=country_data.get('growth_potential', 0),
                        competition_level=country_data.get('competition_level', 'medium'),
                        daily_budget_usd=country_data.get('daily_budget_usd', 10),
                        target_roas=country_data.get('target_roas', 3.0)
                    )
        return None


@dataclass
class RegionalStrategy:
    """Complete regional strategy for Phase 2"""
    strategy_name: str
    phase: str = "Phase 2"
    launch_date: str = "2026-02-01"
    
    # Target countries
    target_countries: List[str] = field(default_factory=list)
    priority_countries: List[str] = field(default_factory=list)
    
    # Regional budgets
    total_budget_monthly_usd: float = 1000.0
    budget_allocation: Dict[str, float] = field(default_factory=dict)
    
    # Timeline
    rollout_schedule: Dict[str, str] = field(default_factory=dict)
    
    # KPIs
    kpi_targets: Dict = field(default_factory=dict)
    
    # Expansion criteria
    expansion_triggers: List[str] = field(default_factory=list)


class RegionalManager:
    """
    Regional configuration and management system for Phase 2 expansion.
    
    Features:
    - Multi-country configuration
    - Timezone-optimized posting schedules
    - Platform preference management
    - Compliance tracking
    - Content localization
    - Budget allocation
    - Performance tracking by region
    """
    
    def __init__(self, config: RegionalStrategy = None):
        """
        Initialize regional manager.
        
        Args:
            config: Regional strategy configuration
        """
        self.config = config or RegionalStrategy(
            strategy_name="ELITE 8 Phase 2 Global Expansion",
            target_countries=_get_default_countries(),
            priority_countries=["US", "JP", "BR", "DE", "GB"]
        )
        
        self.country_configs: Dict[str, CountryConfig] = {}
        self.performance_by_region: Dict[str, Dict] = defaultdict(lambda: {
            "impressions": 0,
            "engagements": 0,
            "followers": 0,
            "conversions": 0,
            "revenue": 0.0,
            "content_published": 0
        })
        
        logger.info("Regional Manager initialized")
    
    def load_country_config(self, country_code: str, config_path: str = None):
        """
        Load configuration for a specific country.
        
        Args:
            country_code: ISO country code (e.g., "US", "JP")
            config_path: Path to configuration file
        """
        default_path = "config/phase2/country_configs.json"
        path = config_path or default_path
        
        config = CountryConfig.from_json(path, country_code)
        if config:
            self.country_configs[country_code] = config
            logger.info(f"Loaded configuration for {config.country_name} ({country_code})")
        else:
            logger.warning(f"No configuration found for {country_code}")
    
    def get_optimal_posting_times(
        self,
        country_code: str,
        platform: str = None
    ) -> List[TimeWindow]:
        """
        Get optimal posting times for a country/region.
        
        Args:
            country_code: Target country
            platform: Optional platform filter
            
        Returns:
            List of optimal time windows
        """
        if country_code not in self.country_configs:
            self.load_country_config(country_code)
        
        config = self.country_configs.get(country_code)
        if not config:
            return []
        
        windows = config.optimal_posting_windows
        
        if platform:
            platform_prefs = [
                p for p in config.platform_preferences 
                if p.platform == platform
            ]
            if platform_prefs:
                # Adjust windows based on platform preferences
                pass
        
        return windows
    
    def get_platform_preferences(
        self,
        country_code: str,
        platform: str = None
    ) -> List[PlatformPreference]:
        """
        Get platform preferences for a country.
        
        Args:
            country_code: Target country
            platform: Optional platform filter
            
        Returns:
            List of platform preferences
        """
        if country_code not in self.country_configs:
            self.load_country_config(country_code)
        
        config = self.country_configs.get(country_code)
        if not config:
            return []
        
        prefs = config.platform_preferences
        
        if platform:
            prefs = [p for p in prefs if p.platform == platform]
        
        return sorted(prefs, key=lambda p: p.priority)
    
    def get_localized_content_settings(self, country_code: str) -> Optional[LocalizedContent]:
        """Get content localization settings for a country"""
        if country_code not in self.country_configs:
            self.load_country_config(country_code)
        
        config = self.country_configs.get(country_code)
        return config.localization if config else None
    
    def get_compliance_requirements(
        self,
        country_code: str
    ) -> Optional[ComplianceRequirement]:
        """Get compliance requirements for a country"""
        if country_code not in self.country_configs:
            self.load_country_config(country_code)
        
        config = self.country_configs.get(country_code)
        return config.compliance if config else None
    
    def get_regional_budget_allocation(self) -> Dict[str, float]:
        """Get budget allocation across regions"""
        allocation = {}
        total = self.config.total_budget_monthly_usd
        
        # Default allocation based on market potential
        weights = {
            "US": 0.30,
            "JP": 0.20,
            "BR": 0.15,
            "DE": 0.10,
            "GB": 0.10,
            "OTHER": 0.15
        }
        
        for region, weight in weights.items():
            allocation[region] = total * weight
        
        return allocation
    
    def get_expansion_recommendations(self) -> List[Dict]:
        """
        Get recommendations for regional expansion.
        
        Returns:
            List of expansion recommendations with priority
        """
        recommendations = []
        
        for country_code, config in self.country_configs.items():
            score = (
                config.market_size * 0.3 +
                config.growth_potential * 100 * 0.4 +
                (1.0 if config.competition_level == "low" else 0.5 if config.competition_level == "medium" else 0.2) * 100 * 0.3
            )
            
            recommendations.append({
                "country_code": country_code,
                "country_name": config.country_name,
                "expansion_score": round(score, 2),
                "market_size": config.market_size,
                "growth_potential": config.growth_potential,
                "competition": config.competition_level,
                "recommended_action": "expand" if score > 50 else "monitor" if score > 30 else "delay"
            })
        
        return sorted(recommendations, key=lambda r: r['expansion_score'], reverse=True)
    
    def get_content_calendar(
        self,
        country_code: str,
        days: int = 7
    ) -> List[Dict]:
        """
        Generate a content calendar optimized for a region.
        
        Args:
            country_code: Target country
            days: Number of days to generate
            
        Returns:
            Optimized content calendar
        """
        if country_code not in self.country_configs:
            self.load_country_config(country_code)
        
        config = self.country_configs.get(country_code)
        if not config:
            return []
        
        calendar = []
        today = datetime.now()
        
        # Get optimal windows
        windows = config.optimal_posting_windows
        
        for day in range(days):
            current_date = today + timedelta(days=day)
            day_name = current_date.strftime("%A")
            
            for window in windows:
                if day_name in window.best_days:
                    for platform_pref in config.platform_preferences:
                        if platform_pref.priority <= 3:  # Top 3 platforms
                            calendar.append({
                                "date": current_date.strftime("%Y-%m-%d"),
                                "day": day_name,
                                "time_window": f"{window.start_hour:02d}:00-{window.end_hour:02d}:00",
                                "timezone": window.timezone,
                                "platform": platform_pref.platform,
                                "content_format": platform_pref.content_format,
                                "optimal_duration": platform_pref.optimal_duration,
                                "hashtags": platform_pref.hashtags[:5],
                                "trending_topics": config.localization.trending_topics[:3]
                            })
        
        return calendar
    
    def track_regional_performance(
        self,
        country_code: str,
        impressions: int = 0,
        engagements: int = 0,
        followers: int = 0,
        conversions: int = 0,
        revenue: float = 0.0,
        content_published: int = 0
    ):
        """Track performance metrics for a region"""
        self.performance_by_region[country_code]["impressions"] += impressions
        self.performance_by_region[country_code]["engagements"] += engagements
        self.performance_by_region[country_code]["followers"] += followers
        self.performance_by_region[country_code]["conversions"] += conversions
        self.performance_by_region[country_code]["revenue"] += revenue
        self.performance_by_region[country_code]["content_published"] += content_published
    
    def get_regional_report(self) -> Dict[str, Any]:
        """Get comprehensive regional performance report"""
        total_impressions = 0
        total_engagements = 0
        total_revenue = 0.0
        
        region_reports = {}
        
        for country_code, metrics in self.performance_by_region.items():
            total_impressions += metrics["impressions"]
            total_engagements += metrics["engagements"]
            total_revenue += metrics["revenue"]
            
            engagement_rate = (
                metrics["engagements"] / metrics["impressions"] * 100
                if metrics["impressions"] > 0 else 0
            )
            
            region_reports[country_code] = {
                "impressions": metrics["impressions"],
                "engagements": metrics["engagements"],
                "engagement_rate": round(engagement_rate, 2),
                "followers_gained": metrics["followers"],
                "conversions": metrics["conversions"],
                "revenue": round(metrics["revenue"], 2),
                "content_published": metrics["content_published"]
            }
        
        return {
            "strategy_name": self.config.strategy_name,
            "phase": self.config.phase,
            "total_impressions": total_impressions,
            "total_engagements": total_engagements,
            "overall_engagement_rate": round(
                total_engagements / total_impressions * 100, 2
            ) if total_impressions > 0 else 0,
            "total_revenue": round(total_revenue, 2),
            "by_region": region_reports,
            "budget_allocation": self.get_regional_budget_allocation(),
            "expansion_recommendations": self.get_expansion_recommendations()
        }
    
    def validate_content_for_region(
        self,
        country_code: str,
        content_type: str,
        content_metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        Validate if content is appropriate for a region.
        
        Args:
            country_code: Target country
            content_type: Type of content
            content_metadata: Additional content metadata
            
        Returns:
            Validation result with any restrictions
        """
        if country_code not in self.country_configs:
            self.load_country_config(country_code)
        
        config = self.country_configs.get(country_code)
        if not config:
            return {"valid": False, "reason": "No configuration found"}
        
        issues = []
        warnings = []
        
        # Check prohibited content
        for prohibited in config.localization.prohibited_content:
            if content_type in prohibited.lower():
                issues.append(f"Content type '{content_type}' may be prohibited")
        
        # Check age restrictions
        if content_metadata and content_metadata.get("contains_mature_content"):
            if config.compliance.requires_age_verification:
                warnings.append("Content may require age verification")
        
        # Platform-specific checks
        for rule_key, rule_value in config.compliance.platform_specific_rules.items():
            if content_type in str(rule_value):
                issues.append(f"Platform rule: {rule_key}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "compliance_notes": config.compliance.platform_specific_rules
        }


# Factory function
def create_regional_manager(config_path: str = None) -> RegionalManager:
    """
    Create and configure a regional manager.
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        Initialized RegionalManager instance
    """
    if config_path:
        # Load from file
        with open(config_path, 'r') as f:
            data = json.load(f)
            strategy = RegionalStrategy(**data)
    else:
        strategy = RegionalStrategy(
            strategy_name="ELITE 8 Phase 2 Global Expansion",
            target_countries=_get_default_countries(),
            priority_countries=["US", "JP", "BR", "DE", "GB"]
        )
    
    manager = RegionalManager(strategy)
    
    # Load country configs
    for country in strategy.target_countries:
        manager.load_country_config(country)
    
    return manager


def _get_default_countries() -> List[str]:
    """Get list of default target countries"""
    return [
        # Phase 2 priority countries
        "US", "JP", "BR", "DE", "GB",  # Tier 1
        "FR", "ES", "IT", "AU", "CA",  # Tier 2
        "MX", "AR", "CO", "KR", "NL"   # Tier 3
    ]


if __name__ == "__main__":
    # Test regional configuration
    print("=== Phase 2 Regional Configuration ===")
    print()
    
    # Create regional manager
    manager = create_regional_manager()
    
    print(f"Strategy: {manager.config.strategy_name}")
    print(f"Phase: {manager.config.phase}")
    print(f"Target Countries: {len(manager.config.target_countries)}")
    print(f"Priority Countries: {manager.config.priority_countries}")
    print()
    
    # Show country configurations
    print("Country Configurations:")
    for code, config in manager.country_configs.items():
        print(f"  • {config.country_name} ({code})")
        print(f"    Region: {config.region}")
        print(f"    Language: {config.language}")
        print(f"    Timezone: {config.timezone}")
        print(f"    Market Size: {config.market_size:,}")
        print(f"    Growth Potential: {config.growth_potential}")
        print(f"    Daily Budget: ${config.daily_budget_usd}")
        print()
    
    # Get optimal posting times for US
    print("Optimal Posting Times (US):")
    times = manager.get_optimal_posting_times("US")
    for window in times[:3]:
        print(f"  • {window.timezone}: {window.start_hour}:00-{window.end_hour}:00")
        print(f"    Best Days: {', '.join(window.best_days)}")
    print()
    
    # Get platform preferences for Japan
    print("Platform Preferences (Japan):")
    prefs = manager.get_platform_preferences("JP")
    for pref in prefs[:3]:
        print(f"  • {pref.platform}: Priority {pref.priority}")
        print(f"    Format: {pref.content_format}, Duration: {pref.optimal_duration}s")
    print()
    
    # Get content calendar
    print("Content Calendar (US - 3 days):")
    calendar = manager.get_content_calendar("US", 3)
    for item in calendar[:5]:
        print(f"  • {item['date']} {item['time_window']} - {item['platform']}")
    print()
    
    # Get expansion recommendations
    print("Expansion Recommendations:")
    recommendations = manager.get_expansion_recommendations()
    for rec in recommendations[:5]:
        print(f"  • {rec['country_name']}: Score {rec['expansion_score']} - {rec['recommended_action']}")
    print()
    
    # Regional report
    print("Regional Performance Report:")
    report = manager.get_regional_report()
    print(f"  Total Impressions: {report['total_impressions']}")
    print(f"  Total Engagements: {report['total_engagements']}")
    print(f"  Engagement Rate: {report['overall_engagement_rate']}%")
    print(f"  Total Revenue: ${report['total_revenue']}")
