"""
OnlyFans-Specific Conversion Funnel

Platform-optimized funnel for OnlyFans monetization with tiered upsell strategy.

Version: 1.0.0
Created: 2026-01-22
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal

from .conversion_funnel import ConversionFunnel, FunnelStep, FunnelConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OnlyFansTier(Enum):
    """OnlyFans subscription tiers"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"


class OnlyFansContentType(Enum):
    """OnlyFans content types"""
    TEASER = "teaser"
    PHOTOSET = "photoset"
    VIDEO = "video"
    PPV_PHOTO = "ppv_photo"
    PPV_VIDEO = "ppv_video"
    CUSTOM_REQUEST = "custom_request"
    MESSAGE = "dm_message"


@dataclass
class OnlyFansSubscriber:
    """OnlyFans subscriber data"""
    subscriber_id: str
    username: str
    tier: str
    monthly_rate: Decimal
    subscription_start: datetime
    lifetime_value: Decimal = Decimal("0.00")
    ppv_purchases: int = 0
    custom_requests: int = 0
    engagement_score: float = 0.0
    last_tip: Optional[datetime] = None
    last_message: Optional[datetime] = None


@dataclass
class OnlyFansPPVOffer:
    """Pay-Per-View content offer"""
    ppv_id: str
    content_type: str
    title: str
    description: str
    price: Decimal
    nsfw_level: int
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    target_audience: str = "all"


class OnlyFansFunnel(ConversionFunnel):
    """
    OnlyFans-specific conversion funnel with tiered monetization.
    
    Funnel Flow:
    1. Viral Hook (TikTok/Instagram) → Drive traffic
    2. Discord Nurture → Build community
    3. OF Free/Preview → Soft conversion
    4. OF Basic ($9.99) → First monetization
    5. OF Premium ($24.99) → Upsell
    6. OF VIP ($49.99) → Maximum tier
    7. PPV Content → Additional revenue
    8. Custom Requests → Premium revenue
    """
    
    def __init__(self, config: Optional[FunnelConfig] = None):
        """
        Initialize OnlyFans funnel.
        
        Args:
            config: Custom funnel configuration
        """
        if config is None:
            config = self._create_default_config()
        
        super().__init__(config)
        
        self.tier_prices = {
            OnlyFansTier.FREE: Decimal("0.00"),
            OnlyFansTier.BASIC: Decimal("9.99"),
            OnlyFansTier.PREMIUM: Decimal("24.99"),
            OnlyFansTier.VIP: Decimal("49.99")
        }
        
        self.ppv_price_ranges = {
            "photo": (Decimal("5.00"), Decimal("15.00")),
            "video_short": (Decimal("10.00"), Decimal("25.00")),
            "video_long": (Decimal("20.00"), Decimal("50.00")),
            "custom": (Decimal("50.00"), Decimal("500.00"))
        }
        
        logger.info("OnlyFans Funnel initialized with tiered monetization strategy")
    
    def _create_default_config(self) -> FunnelConfig:
        """Create default OnlyFans funnel configuration"""
        stages = [
            FunnelStep(
                name="viral_hook",
                stage="awareness",
                content_types=["trending_dance", "thirst_trap", "teaser_video"],
                platforms=["tiktok", "instagram_reels", "twitter"],
                engagement_goal=8.0,
                conversion_rate=3.0,
                frequency_per_day=3,
                duration_hours=24,
                metrics={"nsfw_level": 0, "cta": "Link in bio 🔥💕"},
                target_audience=["viral_viewers", "casual_fans"]
            ),
            FunnelStep(
                name="discord_nurture",
                stage="interest",
                content_types=["cosplay_tease", "grwm", "behind_scenes"],
                platforms=["discord", "telegram"],
                engagement_goal=6.0,
                conversion_rate=15.0,
                frequency_per_day=2,
                duration_hours=48,
                metrics={"nsfw_level": 2, "cta": "Join OF for exclusive 💕"},
                target_audience=["discord_members", "engaged_followers"]
            ),
            FunnelStep(
                name="of_preview",
                stage="consideration",
                content_types=["preview_content", "teaser_photosets"],
                platforms=["onlyfans_free"],
                engagement_goal=5.0,
                conversion_rate=20.0,
                frequency_per_day=1,
                duration_hours=72,
                metrics={"nsfw_level": 2, "cta": "Subscribe for full content ✨"},
                target_audience=["of_visitors", "interested_users"]
            ),
            FunnelStep(
                name="basic_tier",
                stage="purchase",
                content_types=["lingerie_photosets", "softcore_videos", "dm_access"],
                platforms=["onlyfans_basic"],
                engagement_goal=7.0,
                conversion_rate=25.0,
                frequency_per_day=2,
                duration_hours=168,
                metrics={"nsfw_level": 4, "price": 9.99, "cta": "Upgrade to Premium 🔥"},
                target_audience=["basic_subscribers"]
            ),
            FunnelStep(
                name="premium_tier",
                stage="loyalty",
                content_types=["explicit_videos", "custom_photosets", "priority_dms"],
                platforms=["onlyfans_premium"],
                engagement_goal=8.0,
                conversion_rate=20.0,
                frequency_per_day=1,
                duration_hours=336,
                metrics={"nsfw_level": 6, "price": 24.99, "cta": "Join VIP for ultimate access 💋"},
                target_audience=["premium_subscribers"]
            ),
            FunnelStep(
                name="vip_tier",
                stage="loyalty",
                content_types=["vip_exclusive", "custom_requests", "video_calls"],
                platforms=["onlyfans_vip"],
                engagement_goal=9.0,
                conversion_rate=30.0,
                frequency_per_day=1,
                duration_hours=720,
                metrics={"nsfw_level": 8, "price": 49.99, "cta": "Request custom content 🌟"},
                target_audience=["vip_subscribers"]
            )
        ]
        
        return FunnelConfig(
            funnel_name="OnlyFans Premium Funnel",
            description="Tiered OnlyFans monetization with viral awareness to VIP conversion",
            stages=stages,
            total_budget_monthly=200.0,
            target_revenue=5000.0,
            kpi_targets={
                "viral_views_monthly": 100000,
                "discord_joins_monthly": 5000,
                "of_subscribers_monthly": 750,
                "basic_to_premium_rate": 25,
                "premium_to_vip_rate": 20,
                "ppv_revenue_monthly": 1500,
                "average_ltv": 150
            },
            audience_segments=[
                {"name": "viral_audience", "size": 100000, "conversion_rate": 5.0},
                {"name": "discord_community", "size": 5000, "conversion_rate": 15.0},
                {"name": "of_subscribers", "size": 750, "conversion_rate": 100.0}
            ]
        )
    
    def calculate_tier_upsell(
        self,
        current_tier: str,
        subscriber_ltv: Decimal,
        engagement_score: float
    ) -> Dict[str, Any]:
        """
        Calculate upsell probability for subscriber.
        
        Args:
            current_tier: Current subscription tier
            subscriber_ltv: Lifetime value
            engagement_score: Engagement score (0-1)
            
        Returns:
            Upsell recommendation
        """
        upsell_probability = 0.0
        recommended_tier = current_tier
        
        # High engagement + high LTV = strong upsell candidate
        if engagement_score > 0.7 and subscriber_ltv > Decimal("50.00"):
            if current_tier == OnlyFansTier.BASIC.value:
                recommended_tier = OnlyFansTier.PREMIUM.value
                upsell_probability = 0.35
            elif current_tier == OnlyFansTier.PREMIUM.value:
                recommended_tier = OnlyFansTier.VIP.value
                upsell_probability = 0.25
        elif engagement_score > 0.5:
            if current_tier == OnlyFansTier.BASIC.value:
                recommended_tier = OnlyFansTier.PREMIUM.value
                upsell_probability = 0.20
        
        return {
            "current_tier": current_tier,
            "recommended_tier": recommended_tier,
            "upsell_probability": round(upsell_probability, 2),
            "confidence": "high" if upsell_probability > 0.3 else "medium" if upsell_probability > 0.15 else "low",
            "recommended_action": self._get_upsell_action(current_tier, recommended_tier)
        }
    
    def _get_upsell_action(self, current: str, recommended: str) -> str:
        """Get recommended upsell action"""
        if current == recommended:
            return "maintain_engagement"
        
        actions = {
            ("basic", "premium"): "Send Premium tier preview + 20% discount offer",
            ("premium", "vip"): "Send VIP exclusive content + custom request offer",
            ("basic", "vip"): "Send VIP ultimate package + bonus content"
        }
        
        return actions.get((current, recommended), "continue_nurturing")
    
    def create_ppv_offer(
        self,
        content_type: str,
        nsfw_level: int,
        target_tier: str = "all",
        custom_price: Optional[Decimal] = None
    ) -> OnlyFansPPVOffer:
        """
        Create PPV content offer.
        
        Args:
            content_type: Type of PPV content
            nsfw_level: NSFW rating (0-10)
            target_tier: Target subscriber tier
            custom_price: Custom pricing (optional)
            
        Returns:
            PPV offer object
        """
        ppv_id = f"ppv_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Determine price based on content type and NSFW level
        if custom_price:
            price = custom_price
        else:
            base_price = self._get_ppv_base_price(content_type)
            nsfw_multiplier = 1 + (nsfw_level / 10)
            price = base_price * Decimal(str(nsfw_multiplier))
        
        return OnlyFansPPVOffer(
            ppv_id=ppv_id,
            content_type=content_type,
            title=f"Exclusive {content_type.title()} - Level {nsfw_level}",
            description=f"Premium {content_type} content - {nsfw_level}/10 NSFW rating",
            price=price.quantize(Decimal("0.01")),
            nsfw_level=nsfw_level,
            target_audience=target_tier
        )
    
    def _get_ppv_base_price(self, content_type: str) -> Decimal:
        """Get base PPV price for content type"""
        base_prices = {
            "photo": Decimal("10.00"),
            "photoset": Decimal("15.00"),
            "video_short": Decimal("20.00"),
            "video_long": Decimal("35.00"),
            "custom": Decimal("75.00")
        }
        
        return base_prices.get(content_type, Decimal("15.00"))
    
    def get_revenue_projection(
        self,
        subscribers_by_tier: Dict[str, int],
        ppv_conversion_rate: float = 0.15,
        custom_requests_per_month: int = 5
    ) -> Dict[str, Any]:
        """
        Calculate revenue projection.
        
        Args:
            subscribers_by_tier: Number of subscribers per tier
            ppv_conversion_rate: PPV purchase rate
            custom_requests_per_month: Average custom requests
            
        Returns:
            Revenue projection breakdown
        """
        subscription_revenue = Decimal("0.00")
        
        for tier, count in subscribers_by_tier.items():
            tier_price = self.tier_prices.get(OnlyFansTier[tier.upper()], Decimal("0.00"))
            subscription_revenue += tier_price * count
        
        total_subscribers = sum(subscribers_by_tier.values())
        ppv_purchasers = int(total_subscribers * ppv_conversion_rate)
        ppv_revenue = ppv_purchasers * Decimal("20.00")  # Average PPV price
        
        custom_revenue = Decimal(str(custom_requests_per_month)) * Decimal("150.00")  # Average custom price
        
        total_revenue = subscription_revenue + ppv_revenue + custom_revenue
        
        return {
            "subscription_revenue": float(subscription_revenue),
            "ppv_revenue": float(ppv_revenue),
            "custom_revenue": float(custom_revenue),
            "total_revenue": float(total_revenue),
            "breakdown": {
                "subscriptions": float(subscription_revenue / total_revenue * 100) if total_revenue > 0 else 0,
                "ppv": float(ppv_revenue / total_revenue * 100) if total_revenue > 0 else 0,
                "custom": float(custom_revenue / total_revenue * 100) if total_revenue > 0 else 0
            },
            "subscribers_by_tier": subscribers_by_tier,
            "total_subscribers": total_subscribers
        }
    
    def get_funnel_metrics_onlyfans(self) -> Dict[str, Any]:
        """Get OnlyFans-specific funnel metrics"""
        base_metrics = self.get_funnel_metrics()
        
        # Add OnlyFans-specific metrics
        base_metrics["onlyfans_specific"] = {
            "tier_distribution": {
                "basic": 60,
                "premium": 30,
                "vip": 10
            },
            "average_tier_value": {
                "basic": 9.99,
                "premium": 24.99,
                "vip": 49.99
            },
            "ppv_metrics": {
                "average_purchase": 20.00,
                "purchase_frequency": "2.5x per month",
                "conversion_rate": 15.0
            },
            "custom_requests": {
                "average_price": 150.00,
                "monthly_volume": 5,
                "primary_tier": "vip"
            }
        }
        
        return base_metrics


def create_onlyfans_funnel(character_id: Optional[str] = None) -> OnlyFansFunnel:
    """
    Create OnlyFans funnel instance.
    
    Args:
        character_id: Optional character ID for personalization
        
    Returns:
        Configured OnlyFans funnel
    """
    funnel = OnlyFansFunnel()
    
    if character_id:
        logger.info(f"OnlyFans funnel created for character: {character_id}")
    
    return funnel


if __name__ == "__main__":
    # Test OnlyFans funnel
    print("=== OnlyFans Conversion Funnel ===" )
    print()
    
    funnel = create_onlyfans_funnel("aurelia_viral")
    
    print(f"Funnel: {funnel.config.funnel_name}")
    print(f"Target Revenue: ${funnel.config.target_revenue}")
    print()
    
    # Show funnel stages
    print("Funnel Stages:")
    for stage in funnel.get_funnel_stages():
        nsfw_level = stage.metrics.get("nsfw_level", 0)
        price = stage.metrics.get("price", "Free")
        print(f"  • {stage.name} (NSFW: {nsfw_level}) - ${price}")
        print(f"    Conversion: {stage.conversion_rate}%")
    print()
    
    # Revenue projection
    subs = {"basic": 100, "premium": 40, "vip": 10}
    projection = funnel.get_revenue_projection(subs)
    print(f"Revenue Projection:")
    print(f"  Total Subscribers: {projection['total_subscribers']}")
    print(f"  Monthly Revenue: ${projection['total_revenue']:.2f}")
    print(f"  - Subscriptions: ${projection['subscription_revenue']:.2f}")
    print(f"  - PPV: ${projection['ppv_revenue']:.2f}")
    print(f"  - Custom: ${projection['custom_revenue']:.2f}")
