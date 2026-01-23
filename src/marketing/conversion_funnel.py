"""
Conversion Funnel Configuration - Phase 2

This module defines the complete conversion funnel strategy for the ELITE 8 AI Video Generation System,
including multi-stage engagement, audience nurturing, and monetization pathways.

The funnel is designed for anime/waifu content creators targeting social media growth
with automated video production and cross-platform distribution.

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


class FunnelStage(Enum):
    """Stages of the conversion funnel"""
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    INTENT = "intent"
    PURCHASE = "purchase"
    LOYALTY = "loyalty"


class ContentCategory(Enum):
    """Content categories for different funnel stages"""
    VIRAL = "viral"           # High engagement, shareable
    EDUCATIONAL = "educational"  # How-to, tips
    BEHIND_SCENES = "bts"     # Character lore, production
    PROMOTIONAL = "promo"     # New features, announcements
    COMMUNITY = "community"   # User interaction, challenges


class PlatformTarget(Enum):
    """Target platforms for content distribution"""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE_SHORTS = "youtube_shorts"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    DISCORD = "discord"


@dataclass
class FunnelStep:
    """Individual step in the conversion funnel"""
    name: str
    stage: str
    content_types: List[str]
    platforms: List[str]
    engagement_goal: float  # Target engagement rate
    conversion_rate: float  # Expected conversion to next stage
    frequency_per_day: int
    duration_hours: int  # How long content remains relevant
    
    metrics: Dict = field(default_factory=dict)
    target_audience: List[str] = field(default_factory=list)


@dataclass
class FunnelConfig:
    """Complete funnel configuration"""
    funnel_name: str
    description: str
    stages: List[FunnelStep]
    total_budget_monthly: float
    target_revenue: float
    kpi_targets: Dict = field(default_factory=dict)
    audience_segments: List[Dict] = field(default_factory=list)
    
    @classmethod
    def from_json(cls, config_path: str) -> 'FunnelConfig':
        """Load configuration from JSON file"""
        path = Path(config_path)
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                
                stages = [
                    FunnelStep(**step) for step in data.get('stages', [])
                ]
                
                return cls(
                    funnel_name=data.get('funnel_name', ''),
                    description=data.get('description', ''),
                    stages=stages,
                    total_budget_monthly=data.get('total_budget_monthly', 0),
                    target_revenue=data.get('target_revenue', 0),
                    kpi_targets=data.get('kpi_targets', {}),
                    audience_segments=data.get('audience_segments', [])
                )
        return cls(
            funnel_name="default",
            description="Default conversion funnel",
            stages=[],
            total_budget_monthly=0,
            target_revenue=0
        )


class ConversionFunnel:
    """
    Complete conversion funnel management system.
    
    Features:
    - Multi-stage funnel configuration
    - Content scheduling by stage
    - Performance tracking per stage
    - A/B testing support
    - Revenue attribution
    - Audience segmentation
    """
    
    def __init__(self, config: FunnelConfig = None):
        """
        Initialize conversion funnel.
        
        Args:
            config: Funnel configuration
        """
        self.config = config or FunnelConfig(
            funnel_name="ELITE 8 Content Funnel",
            description="Conversion funnel for AI-generated anime content",
            stages=[],
            total_budget_monthly=500.0,
            target_revenue=2000.0
        )
        
        self.stage_performance: Dict[str, Dict] = defaultdict(lambda: {
            "impressions": 0,
            "engagements": 0,
            "conversions": 0,
            "revenue": 0.0,
            "content_count": 0
        })
        
        self.content_queue: List[Dict] = []
        self.audience_data: Dict[str, Dict] = {}
        
        logger.info(f"Conversion Funnel initialized: {self.config.funnel_name}")
    
    def get_funnel_stages(self) -> List[FunnelStep]:
        """Get all configured funnel stages"""
        return self.config.stages
    
    def get_stage_by_name(self, stage_name: str) -> Optional[FunnelStep]:
        """Get a specific funnel stage by name"""
        for stage in self.config.stages:
            if stage.name == stage_name:
                return stage
        return None
    
    def add_stage(self, stage: FunnelStep):
        """Add a new stage to the funnel"""
        self.config.stages.append(stage)
        logger.info(f"Added funnel stage: {stage.name}")
    
    def get_content_for_stage(
        self,
        stage: FunnelStage,
        region: str = "global"
    ) -> List[Dict[str, Any]]:
        """
        Get content recommendations for a specific funnel stage.
        
        Args:
            stage: Target funnel stage
            region: Target region
            
        Returns:
            List of content recommendations
        """
        stage_config = self.get_stage_by_name(stage.value)
        
        if not stage_config:
            return []
        
        content_plan = []
        
        for content_type in stage_config.content_types:
            for platform in stage_config.platforms:
                content_plan.append({
                    "content_type": content_type,
                    "platform": platform,
                    "stage": stage.value,
                    "engagement_goal": stage_config.engagement_goal,
                    "frequency": stage_config.frequency_per_day,
                    "optimal_duration_hours": stage_config.duration_hours
                })
        
        return content_plan
    
    def track_content_published(
        self,
        content_id: str,
        stage: str,
        platform: str,
        character: str
    ):
        """Track published content for analytics"""
        if stage in self.stage_performance:
            self.stage_performance[stage]["content_count"] += 1
            
        logger.info(f"Content tracked: {content_id} | Stage: {stage} | Platform: {platform}")
    
    def track_engagement(
        self,
        content_id: str,
        stage: str,
        impressions: int,
        engagements: int,
        conversions: int = 0,
        revenue: float = 0.0
    ):
        """Track engagement metrics for content"""
        if stage in self.stage_performance:
            perf = self.stage_performance[stage]
            perf["impressions"] += impressions
            perf["engagements"] += engagements
            perf["conversions"] += conversions
            perf["revenue"] += revenue
        
        engagement_rate = (engagements / impressions * 100) if impressions > 0 else 0
        conversion_rate = (conversions / engagements * 100) if engagements > 0 else 0
        
        return {
            "engagement_rate": round(engagement_rate, 2),
            "conversion_rate": round(conversion_rate, 2)
        }
    
    def get_funnel_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive funnel performance metrics.
        
        Returns:
            Dictionary with funnel analytics
        """
        total_impressions = 0
        total_engagements = 0
        total_conversions = 0
        total_revenue = 0.0
        
        stage_metrics = {}
        
        for stage_name, metrics in self.stage_performance.items():
            total_impressions += metrics["impressions"]
            total_engagements += metrics["engagements"]
            total_conversions += metrics["conversions"]
            total_revenue += metrics["revenue"]
            
            engagement_rate = (
                metrics["engagements"] / metrics["impressions"] * 100
                if metrics["impressions"] > 0 else 0
            )
            
            stage_metrics[stage_name] = {
                "impressions": metrics["impressions"],
                "engagements": metrics["engagements"],
                "engagement_rate": round(engagement_rate, 2),
                "conversions": metrics["conversions"],
                "revenue": round(metrics["revenue"], 2),
                "content_published": metrics["content_count"]
            }
        
        return {
            "funnel_name": self.config.funnel_name,
            "total_impressions": total_impressions,
            "total_engagements": total_engagements,
            "overall_engagement_rate": round(
                total_engagements / total_impressions * 100, 2
            ) if total_impressions > 0 else 0,
            "total_conversions": total_conversions,
            "total_revenue": round(total_revenue, 2),
            "by_stage": stage_metrics,
            "budget_used": self.get_budget_usage(),
            "roi_percent": round(
                (total_revenue - self.get_budget_usage()) / 
                self.get_budget_usage() * 100, 2
            ) if self.get_budget_usage() > 0 else 0
        }
    
    def get_budget_usage(self) -> float:
        """Calculate total budget used"""
        # This would integrate with actual cost tracking
        return self.config.total_budget_monthly * 0.3  # Placeholder
    
    def generate_content_schedule(self, days: int = 7) -> List[Dict]:
        """
        Generate a content schedule for the next N days.
        
        Args:
            days: Number of days to schedule
            
        Returns:
            List of scheduled content items
        """
        schedule = []
        today = datetime.now()
        
        for day in range(days):
            current_date = today + timedelta(days=day)
            
            for stage in self.config.stages:
                for content_type in stage.content_types:
                    for platform in stage.platforms:
                        if stage.frequency_per_day > 0:
                            for freq in range(stage.frequency_per_day):
                                schedule.append({
                                    "date": current_date.strftime("%Y-%m-%d"),
                                    "time": f"{9 + (freq * 4)}:00",  # Spread throughout day
                                    "stage": stage.name,
                                    "content_type": content_type,
                                    "platform": platform,
                                    "character": self._get_recommended_character(stage.name),
                                    "duration_seconds": self._get_optimal_duration(content_type)
                                })
        
        return schedule
    
    def _get_recommended_character(self, stage: str) -> str:
        """Get recommended character for funnel stage"""
        character_preferences = {
            "awareness": ["yuki-chan", "aurelia-viral"],
            "interest": ["haruka-chan", "ren-official"],
            "consideration": ["miyuki-premium", "kaito-san"],
            "intent": ["chiyo-sasaki", "jin-kawasaki"],
            "purchase": ["hana-nakamura", "rio-mizuno"],
            "loyalty": ["airi-neo", "miyuki-sakura"]
        }
        
        return character_preferences.get(stage, ["yuki-chan"])[0]
    
    def _get_optimal_duration(self, content_type: str) -> int:
        """Get optimal video duration for content type"""
        durations = {
            "karaoke": 45,
            "reel": 30,
            "short": 15,
            "bts": 60,
            "lore": 120,
            "grwm": 90
        }
        
        return durations.get(content_type, 30)
    
    def get_audience_insights(self) -> Dict[str, Any]:
        """Get audience insights and segmentation data"""
        return {
            "total_audience_size": 10000,  # Placeholder
            "segments": self.config.audience_segments,
            "demographics": {
                "age_18_24": 0.35,
                "age_25_34": 0.45,
                "age_35_44": 0.15,
                "age_45_plus": 0.05
            },
            "top_regions": [
                {"region": "North America", "percentage": 0.40},
                {"region": "Europe", "percentage": 0.30},
                {"region": "Asia", "percentage": 0.20},
                {"region": "Other", "percentage": 0.10}
            ],
            "engagement_patterns": {
                "peak_hours": ["12:00", "18:00", "21:00"],
                "best_days": ["Tuesday", "Thursday", "Saturday"],
                "avg_watch_time": "45 seconds"
            }
        }
    
    def calculate_projection(
        self,
        current_metrics: Dict[str, float],
        weeks_ahead: int = 4
    ) -> Dict[str, Any]:
        """
        Calculate future projections based on current performance.
        
        Args:
            current_metrics: Current performance metrics
            weeks_ahead: Number of weeks to project
            
        Returns:
            Projection data
        """
        growth_rate = 1.15  # 15% weekly growth assumption
        
        projections = {
            "projected_revenue": [],
            "projected_audience": [],
            "projected_content": []
        }
        
        current_revenue = current_metrics.get("revenue", 0)
        current_audience = current_metrics.get("audience", 1000)
        current_content = current_metrics.get("content_published", 10)
        
        for week in range(1, weeks_ahead + 1):
            projected_revenue = current_revenue * (growth_rate ** week)
            projected_audience = current_audience * (growth_rate ** week)
            projected_content = current_content * week
            
            projections["projected_revenue"].append({
                "week": week,
                "revenue": round(projected_revenue, 2)
            })
            projections["projected_audience"].append({
                "week": week,
                "audience": round(projected_audience)
            })
            projections["projected_content"].append({
                "week": week,
                "content_count": projected_content
            })
        
        return {
            "current_metrics": current_metrics,
            "growth_rate": growth_rate,
            "projections": projections,
            "roi_target": self.config.target_revenue
        }


# Factory function
def create_conversion_funnel(config_path: str = None) -> ConversionFunnel:
    """
    Create and configure a conversion funnel.
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        Initialized ConversionFunnel instance
    """
    if config_path:
        config = FunnelConfig.from_json(config_path)
    else:
        config = FunnelConfig(
            funnel_name="ELITE 8 Anime Content Funnel",
            description="Multi-stage conversion funnel for anime content creators",
            stages=_get_default_stages(),
            total_budget_monthly=500.0,
            target_revenue=2000.0
        )
    
    return ConversionFunnel(config)


def _get_default_stages() -> List[FunnelStep]:
    """Get default funnel stages"""
    return [
        FunnelStep(
            name="awareness",
            stage=FunnelStage.AWARENESS.value,
            content_types=["karaoke", "viral_short"],
            platforms=["tiktok", "instagram_reels"],
            engagement_goal=5.0,
            conversion_rate=2.0,
            frequency_per_day=3,
            duration_hours=24,
            target_audience=["anime_fans", "content_consumers"]
        ),
        FunnelStep(
            name="interest",
            stage=FunnelStage.INTEREST.value,
            content_types=["behind_scenes", "lore_video"],
            platforms=["youtube_shorts", "instagram"],
            engagement_goal=4.0,
            conversion_rate=3.0,
            frequency_per_day=2,
            duration_hours=48,
            target_audience=["engaged_followers", "anime_community"]
        ),
        FunnelStep(
            name="consideration",
            stage=FunnelStage.CONSIDERATION.value,
            content_types=["tutorial", "grwm"],
            platforms=["youtube", "instagram", "tiktok"],
            engagement_goal=3.5,
            conversion_rate=4.0,
            frequency_per_day=1,
            duration_hours=72,
            target_audience=["potential_customers", "loyal_followers"]
        ),
        FunnelStep(
            name="intent",
            stage=FunnelStage.INTENT.value,
            content_types=["promotional", "announcement"],
            platforms=["instagram", "twitter", "discord"],
            engagement_goal=3.0,
            conversion_rate=8.0,
            frequency_per_day=1,
            duration_hours=96,
            target_audience=["high_intent_users", "subscribers"]
        ),
        FunnelStep(
            name="purchase",
            stage=FunnelStage.PURCHASE.value,
            content_types=["direct_promo", "limited_offer"],
            platforms=["instagram", "email", "discord"],
            engagement_goal=2.5,
            conversion_rate=15.0,
            frequency_per_day=1,
            duration_hours=120,
            target_audience=["ready_to_buy", "premium_members"]
        ),
        FunnelStep(
            name="loyalty",
            stage=FunnelStage.LOYALTY.value,
            content_types=["community_content", "exclusive"],
            platforms=["discord", "email", "members_only"],
            engagement_goal=8.0,
            conversion_rate=20.0,
            frequency_per_day=1,
            duration_hours=168,
            target_audience=["existing_customers", "brand_advocates"]
        )
    ]


if __name__ == "__main__":
    # Test the conversion funnel
    print("=== Conversion Funnel Configuration ===")
    print()
    
    # Create funnel with defaults
    funnel = create_conversion_funnel()
    
    print(f"Funnel: {funnel.config.funnel_name}")
    print(f"Description: {funnel.config.description}")
    print(f"Monthly Budget: ${funnel.config.total_budget_monthly}")
    print(f"Target Revenue: ${funnel.config.target_revenue}")
    print()
    
    # Show stages
    print("Funnel Stages:")
    for stage in funnel.get_funnel_stages():
        print(f"  • {stage.name} ({stage.stage})")
        print(f"    - Content: {stage.content_types}")
        print(f"    - Platforms: {stage.platforms}")
        print(f"    - Goal: {stage.engagement_goal}% engagement")
        print(f"    - Conversion: {stage.conversion_rate}%")
        print()
    
    # Generate schedule
    print("Generating 7-day content schedule...")
    schedule = funnel.generate_content_schedule(7)
    print(f"Generated {len(schedule)} content items")
    print()
    
    # Show first few items
    print("First 5 scheduled items:")
    for item in schedule[:5]:
        print(f"  • {item['date']} {item['time']} - {item['content_type']} on {item['platform']}")
    
    # Get metrics
    print("\nCurrent funnel metrics:")
    metrics = funnel.get_funnel_metrics()
    print(f"  Total Impressions: {metrics['total_impressions']}")
    print(f"  Total Engagements: {metrics['total_engagements']}")
    print(f"  Engagement Rate: {metrics['overall_engagement_rate']}%")
    print(f"  Total Conversions: {metrics['total_conversions']}")
    print(f"  Total Revenue: ${metrics['total_revenue']}")
