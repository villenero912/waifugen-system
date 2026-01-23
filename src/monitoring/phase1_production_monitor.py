"""
Phase 1 Production Monitor - A2E API Integration and Content Production Metrics

This module provides comprehensive monitoring for Phase 1 content production,
including A2E API credit tracking, video generation statistics, and budget management.

Version: 1.0.0
Created: 2026-01-20
Migrated: 2026-01-22
"""

import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionStatus(Enum):
    """Status of production operations"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    GENERATING = "generating"
    RENDERING = "rendering"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ContentType(Enum):
    """Types of content produced"""
    KARAOKE = "karaoke"
    REEL = "reel"
    SHORT = "short"
    BEHIND_THE_SCENES = "bts"
    LORE = "lore"
    GRWM = "grwm"


class Platform(Enum):
    """Target platforms for content distribution"""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE_SHORTS = "youtube_shorts"
    FACEBOOK = "facebook"
    DISCORD = "discord"


@dataclass
class A2ECreditStatus:
    """Current status of A2E API credits"""
    plan_name: str
    monthly_allowance: int
    daily_bonus: int
    monthly_used: int
    daily_used: int
    purchased_credits: int = 0
    last_reset: datetime = field(default_factory=datetime.now)
    
    @property
    def monthly_remaining(self) -> int:
        return self.monthly_allowance - self.monthly_used
    
    @property
    def daily_remaining(self) -> int:
        return self.daily_bonus - self.daily_used
    
    @property
    def total_available(self) -> int:
        return self.monthly_remaining + self.daily_remaining + self.purchased_credits
    
    @property
    def usage_percentage(self) -> float:
        if self.monthly_allowance > 0:
            return (self.monthly_used / self.monthly_allowance) * 100
        return 100.0


@dataclass
class VideoProductionStats:
    """Statistics for a single video production"""
    production_id: str
    character_id: str
    content_type: str
    platform: str
    duration_seconds: float
    credits_consumed: float
    cost_estimate: float
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class DailyProductionSummary:
    """Daily summary of production activity"""
    date: datetime
    total_videos: int = 0
    successful_videos: int = 0
    failed_videos: int = 0
    total_duration_seconds: float = 0.0
    total_credits_used: float = 0.0
    total_cost: float = 0.0
    by_platform: Dict[str, int] = field(default_factory=dict)
    by_character: Dict[str, int] = field(default_factory=dict)
    by_content_type: Dict[str, int] = field(default_factory=dict)


@dataclass
class ProductionConfig:
    """Configuration for production monitoring"""
    # A2E API Configuration
    a2e_api_key: str = ""
    a2e_plan: str = "pro"
    monthly_credit_limit: int = 1800
    daily_bonus_credits: int = 60
    max_cost_per_video: float = 50.0
    budget_warning_threshold: float = 0.8
    
    # Production Settings
    daily_video_target: int = 4
    max_concurrent_productions: int = 3
    retry_failed_productions: bool = True
    max_retries: int = 3
    
    # Character Configuration
    characters: List[str] = field(default_factory=lambda: [
        "aurelia-viral", "yuki-chan", "kaito-san", 
        "miyuki-premium", "haruka-chan", "ren-official"
    ])
    
    # Paths
    output_dir: str = "output/phase1"
    temp_dir: str = "temp"
    stats_file: str = "data/production_stats.json"


class A2EApiClient:
    """
    Client for interacting with A2E API to track credits and manage production.
    
    This class handles all API interactions with A2E for:
    - Credit status checking
    - Video generation requests
    - Job status monitoring
    - Credit consumption tracking
    """
    
    BASE_URL = "https://api.a2e.ai/v1"
    
    # Credit costs based on A2E pricing
    CREDIT_COSTS = {
        "avatar_lipsync_per_second": 1.0,
        "tts_a2e_per_10s": 1.0,
        "tts_minimax_per_10s": 2.0,
        "tts_elevenlabs_per_10s": 3.0,
        "face_swap_video_per_second": 1.0,
        "image_to_video_5s": 30.0,
        "image_to_video_10s": 60.0,
        "image_to_video_15s": 90.0,
        "studio_avatar": 100.0,
        "product_avatar": 10.0,
        "upscale_image": 10.0,
    }
    
    def __init__(self, api_key: str, plan: str = "pro"):
        """
        Initialize A2E API client.
        
        Args:
            api_key: A2E API authentication key
            plan: Subscription plan (free, pro, max)
        """
        self.api_key = api_key
        self.plan = plan
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Quality settings based on plan
        if plan == "free":
            self.quality = "720p"
            self.watermark = True
            self.priority = "low"
        elif plan == "pro":
            self.quality = "4K"
            self.watermark = False
            self.priority = "high"
        else:  # max
            self.quality = "4K"
            self.watermark = False
            self.priority = "highest"
        
        logger.info(f"A2E API Client initialized - Plan: {plan}, Quality: {self.quality}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self.session
    
    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def estimate_cost(
        self,
        duration_seconds: float,
        operation_type: str = "avatar_lipsync"
    ) -> float:
        """
        Estimate credit cost for an operation.
        
        Args:
            duration_seconds: Duration of the operation in seconds
            operation_type: Type of operation
            
        Returns:
            Estimated credit cost
        """
        cost_per_second = self.CREDIT_COSTS.get(f"{operation_type}_per_second", 1.0)
        return duration_seconds * cost_per_second
    
    async def get_credit_status(self) -> A2ECreditStatus:
        """
        Get current credit status from API.
        
        Returns:
            A2ECreditStatus with current credit information
        """
        try:
            session = await self._get_session()
            url = f"{self.BASE_URL}/user/credits"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return A2ECreditStatus(
                        plan_name=self.plan,
                        monthly_allowance=data.get("monthly_limit", self.monthly_credit_limit),
                        daily_bonus=self.daily_bonus_credits,
                        monthly_used=data.get("monthly_used", 0),
                        daily_used=data.get("daily_used", 0),
                        purchased_credits=data.get("purchased_credits", 0),
                        last_reset=datetime.fromisoformat(data.get("last_reset", datetime.now().isoformat()))
                    )
                else:
                    logger.warning(f"Failed to get credit status: {response.status}")
                    # Return default status
                    return A2ECreditStatus(
                        plan_name=self.plan,
                        monthly_allowance=self.monthly_credit_limit,
                        daily_bonus=self.daily_bonus_credits,
                        monthly_used=0,
                        daily_used=0
                    )
        except Exception as e:
            logger.error(f"Error getting credit status: {e}")
            return A2ECreditStatus(
                plan_name=self.plan,
                monthly_allowance=self.monthly_credit_limit,
                daily_bonus=self.daily_bonus_credits,
                monthly_used=0,
                daily_used=0
            )
    
    async def create_video_job(
        self,
        image_path: str,
        audio_path: str,
        webhook_url: str = None
    ) -> Dict[str, Any]:
        """
        Create a video generation job.
        
        Args:
            image_path: Path to character image
            audio_path: Path to audio file
            webhook_url: Optional webhook for completion notification
            
        Returns:
            Dict with job_id and status
        """
        try:
            session = await self._get_session()
            url = f"{self.BASE_URL}/avatar/talking"
            
            # Prepare multipart form data
            form = aiohttp.FormData()
            
            with open(image_path, 'rb') as img:
                form.add_field('image', img, filename='image.jpg', content_type='image/jpeg')
            
            with open(audio_path, 'rb') as audio:
                form.add_field('audio', audio, filename='audio.wav', content_type='audio/wav')
            
            form.add_field('quality', self.quality)
            form.add_field('watermark', str(self.watermark).lower())
            form.add_field('output_format', 'mp4')
            
            if webhook_url:
                form.add_field('webhook_url', webhook_url)
            
            async with session.post(url, data=form) as response:
                if response.status in [200, 201, 202]:
                    result = await response.json()
                    return {
                        "success": True,
                        "job_id": result.get("job_id"),
                        "status": "pending"
                    }
                else:
                    error_body = await response.text()
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "details": error_body
                    }
        except Exception as e:
            logger.error(f"Error creating video job: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check status of a video generation job.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Dict with job status information
        """
        try:
            session = await self._get_session()
            url = f"{self.BASE_URL}/jobs/{job_id}/status"
            
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return {"status": "not_found"}
                else:
                    return {"status": "error", "code": response.status}
        except Exception as e:
            logger.error(f"Error checking job status: {e}")
            return {"status": "error", "error": str(e)}


class ProductionMonitor:
    """
    Central monitor for Phase 1 content production.
    
    Tracks:
    - A2E API credit usage and budget
    - Video production statistics
    - Daily/weekly/monthly summaries
    - Character rotation and content distribution
    - Platform-specific metrics
    
    This class provides the data layer for the Telegram bot integration.
    """
    
    def __init__(self, config: ProductionConfig = None):
        """
        Initialize production monitor.
        
        Args:
            config: Production configuration
        """
        self.config = config or ProductionConfig()
        self.a2e_client: Optional[A2EApiClient] = None
        self.current_status = ProductionStatus.IDLE
        
        # Production history
        self.production_history: List[VideoProductionStats] = []
        self.daily_summaries: Dict[str, DailyProductionSummary] = {}
        
        # Active jobs tracking
        self.active_jobs: Dict[str, Dict] = {}
        
        # Initialize data file paths
        self.stats_file_path = Path(self.config.stats_file)
        self.stats_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing stats
        self._load_stats()
        
        logger.info("Production Monitor initialized")
    
    def initialize_a2e_client(self, api_key: str = None):
        """Initialize A2E API client with credentials."""
        api_key = api_key or self.config.a2e_api_key
        if api_key:
            self.a2e_client = A2EApiClient(api_key, self.config.a2e_plan)
            logger.info("A2E API client initialized")
        else:
            logger.warning("No A2E API key provided - running in simulation mode")
    
    def _load_stats(self):
        """Load production statistics from file."""
        if self.stats_file_path.exists():
            try:
                with open(self.stats_file_path, 'r') as f:
                    data = json.load(f)
                    self.production_history = [
                        VideoProductionStats(**item) 
                        for item in data.get("production_history", [])
                    ]
                    self.daily_summaries = {
                        date: DailyProductionSummary(**summary)
                        for date, summary in data.get("daily_summaries", {}).items()
                    }
                logger.info(f"Loaded {len(self.production_history)} production records")
            except Exception as e:
                logger.warning(f"Failed to load stats: {e}")
    
    def _save_stats(self):
        """Save production statistics to file."""
        try:
            data = {
                "production_history": [
                    {
                        "production_id": p.production_id,
                        "character_id": p.character_id,
                        "content_type": p.content_type,
                        "platform": p.platform,
                        "duration_seconds": p.duration_seconds,
                        "credits_consumed": p.credits_consumed,
                        "cost_estimate": p.cost_estimate,
                        "status": p.status,
                        "started_at": p.started_at.isoformat() if isinstance(p.started_at, datetime) else p.started_at,
                        "completed_at": p.completed_at.isoformat() if p.completed_at and isinstance(p.completed_at, datetime) else p.completed_at,
                        "error_message": p.error_message,
                        "metadata": p.metadata
                    }
                    for p in self.production_history[-1000:]  # Keep last 1000 records
                ],
                "daily_summaries": {
                    date: {
                        "date": summary.date.isoformat() if isinstance(summary.date, datetime) else summary.date,
                        "total_videos": summary.total_videos,
                        "successful_videos": summary.successful_videos,
                        "failed_videos": summary.failed_videos,
                        "total_duration_seconds": summary.total_duration_seconds,
                        "total_credits_used": summary.total_credits_used,
                        "total_cost": summary.total_cost,
                        "by_platform": summary.by_platform,
                        "by_character": summary.by_character,
                        "by_content_type": summary.by_content_type
                    }
                    for date, summary in self.daily_summaries.items()
                },
                "last_updated": datetime.now().isoformat()
            }
            with open(self.stats_file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    async def get_credit_status(self) -> Dict[str, Any]:
        """
        Get current A2E credit status.
        
        Returns:
            Dict with credit information and budget status
        """
        if self.a2e_client:
            credits = await self.a2e_client.get_credit_status()
        else:
            # Simulated status
            credits = A2ECreditStatus(
                plan_name=self.config.a2e_plan,
                monthly_allowance=self.config.monthly_credit_limit,
                daily_bonus=self.config.daily_bonus_credits,
                monthly_used=0,
                daily_used=0
            )
        
        budget_warning = credits.usage_percentage >= (self.config.budget_warning_threshold * 100)
        
        return {
            "plan": credits.plan_name,
            "monthly_total": credits.monthly_allowance,
            "monthly_used": credits.monthly_used,
            "monthly_remaining": credits.monthly_remaining,
            "daily_bonus": credits.daily_bonus,
            "daily_used": credits.daily_used,
            "daily_remaining": credits.daily_remaining,
            "purchased_credits": credits.purchased_credits,
            "total_available": credits.total_available,
            "usage_percentage": round(credits.usage_percentage, 1),
            "budget_warning": budget_warning,
            "budget_status": "healthy" if not budget_warning else "warning" if credits.usage_percentage < 95 else "critical"
        }
    
    def record_production(
        self,
        character_id: str,
        content_type: str,
        platform: str,
        duration_seconds: float,
        credits_consumed: float,
        cost_estimate: float,
        status: str,
        error_message: str = None,
        metadata: Dict = None
    ) -> VideoProductionStats:
        """
        Record a video production event.
        
        Args:
            character_id: Character used for production
            content_type: Type of content
            platform: Target platform
            duration_seconds: Video duration
            credits_consumed: Credits used
            cost_estimate: Estimated cost
            status: Production status
            error_message: Error message if failed
            metadata: Additional metadata
            
        Returns:
            VideoProductionStats object
        """
        stats = VideoProductionStats(
            production_id=f"prod_{uuid.uuid4().hex[:12]}",
            character_id=character_id,
            content_type=content_type,
            platform=platform,
            duration_seconds=duration_seconds,
            credits_consumed=credits_consumed,
            cost_estimate=cost_estimate,
            status=status,
            started_at=datetime.now(),
            completed_at=datetime.now() if status in ["completed", "failed"] else None,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        self.production_history.append(stats)
        
        # Update daily summary
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.daily_summaries:
            self.daily_summaries[today] = DailyProductionSummary(date=today)
        
        summary = self.daily_summaries[today]
        summary.total_videos += 1
        summary.total_duration_seconds += duration_seconds
        summary.total_credits_used += credits_consumed
        summary.total_cost += cost_estimate
        
        if status == "completed":
            summary.successful_videos += 1
        else:
            summary.failed_videos += 1
        
        summary.by_platform[platform] = summary.by_platform.get(platform, 0) + 1
        summary.by_character[character_id] = summary.by_character.get(character_id, 0) + 1
        summary.by_content_type[content_type] = summary.by_content_type.get(content_type, 0) + 1
        
        # Save to file
        self._save_stats()
        
        logger.info(f"Recorded production: {stats.production_id} - {character_id} - {status}")
        
        return stats
    
    def get_daily_summary(self, date: datetime = None) -> Dict[str, Any]:
        """
        Get production summary for a specific date.
        
        Args:
            date: Date to get summary for (defaults to today)
            
        Returns:
            Dict with daily production summary
        """
        target_date = (date or datetime.now()).strftime("%Y-%m-%d")
        
        if target_date in self.daily_summaries:
            summary = self.daily_summaries[target_date]
            return {
                "date": target_date,
                "total_videos": summary.total_videos,
                "successful_videos": summary.successful_videos,
                "failed_videos": summary.failed_videos,
                "success_rate": round((summary.successful_videos / summary.total_videos * 100) 
                                      if summary.total_videos > 0 else 0, 1),
                "total_duration_minutes": round(summary.total_duration_seconds / 60, 1),
                "total_credits_used": summary.total_credits_used,
                "total_cost": round(summary.total_cost, 2),
                "by_platform": summary.by_platform,
                "by_character": summary.by_character,
                "by_content_type": summary.by_content_type,
                "progress_toward_target": round(
                    (summary.total_videos / self.config.daily_video_target) * 100, 1
                ),
                "target_videos": self.config.daily_video_target
            }
        else:
            return {
                "date": target_date,
                "total_videos": 0,
                "successful_videos": 0,
                "failed_videos": 0,
                "success_rate": 0,
                "total_duration_minutes": 0,
                "total_credits_used": 0,
                "total_cost": 0,
                "by_platform": {},
                "by_character": {},
                "by_content_type": {},
                "progress_toward_target": 0,
                "target_videos": self.config.daily_video_target
            }
    
    def get_weekly_summary(self) -> Dict[str, Any]:
        """Get production summary for the current week."""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        
        weekly_stats = {
            "total_videos": 0,
            "successful_videos": 0,
            "failed_videos": 0,
            "total_credits_used": 0,
            "total_cost": 0,
            "by_platform": {},
            "by_character": {},
            "by_content_type": {},
            "daily_breakdown": []
        }
        
        for i in range(7):
            date = week_start + timedelta(days=i)
            daily = self.get_daily_summary(date)
            weekly_stats["total_videos"] += daily["total_videos"]
            weekly_stats["successful_videos"] += daily["successful_videos"]
            weekly_stats["failed_videos"] += daily["failed_videos"]
            weekly_stats["total_credits_used"] += daily["total_credits_used"]
            weekly_stats["total_cost"] += daily["total_cost"]
            
            for platform, count in daily["by_platform"].items():
                weekly_stats["by_platform"][platform] = weekly_stats["by_platform"].get(platform, 0) + count
            
            for char, count in daily["by_character"].items():
                weekly_stats["by_character"][char] = weekly_stats["by_character"].get(char, 0) + count
            
            for content_type, count in daily["by_content_type"].items():
                weekly_stats["by_content_type"][content_type] = weekly_stats["by_content_type"].get(content_type, 0) + count
            
            weekly_stats["daily_breakdown"].append({
                "date": daily["date"],
                "videos": daily["total_videos"],
                "success_rate": daily["success_rate"]
            })
        
        weekly_stats["average_daily_videos"] = round(weekly_stats["total_videos"] / 7, 1)
        weekly_stats["average_daily_cost"] = round(weekly_stats["total_cost"] / 7, 2)
        
        return weekly_stats
    
    def get_character_rotation_status(self) -> Dict[str, Any]:
        """
        Get status of character rotation for content production.
        
        Returns:
            Dict with character usage statistics and recommendations
        """
        today = datetime.now().strftime("%Y-%m-%d")
        daily = self.get_daily_summary()
        
        character_usage = daily.get("by_character", {})
        total_videos_today = daily["total_videos"]
        
        # Calculate rotation status
        character_status = {}
        for char in self.config.characters:
            used_count = character_usage.get(char, 0)
            # Ideal distribution: target_videos / num_characters
            ideal_per_char = self.config.daily_video_target / len(self.config.characters)
            
            character_status[char] = {
                "used_today": used_count,
                "ideal_distribution": round(ideal_per_char, 1),
                "needs_more": used_count < ideal_per_char,
                "rotation_weight": max(0, ideal_per_char - used_count)
            }
        
        # Recommend next character
        needs_more = [char for char, status in character_status.items() 
                     if status["needs_more"]]
        
        next_recommended = needs_more[0] if needs_more else self.config.characters[0]
        
        return {
            "characters": character_status,
            "next_recommended": next_recommended,
            "total_videos_today": total_videos_today,
            "target_videos": self.config.daily_video_target,
            "remaining_videos": self.config.daily_video_target - total_videos_today
        }
    
    def get_platform_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of content across platforms.
        
        Returns:
            Dict with platform distribution statistics
        """
        today = datetime.now().strftime("%Y-%m-%d")
        daily = self.get_daily_summary()
        
        platform_usage = daily.get("by_platform", {})
        total = daily["total_videos"]
        
        distribution = {}
        for platform in [p.value for p in Platform]:
            count = platform_usage.get(platform, 0)
            distribution[platform] = {
                "count": count,
                "percentage": round((count / total * 100) if total > 0 else 0, 1)
            }
        
        return {
            "distribution": distribution,
            "total": total,
            "platforms_active": len([p for p in distribution.values() if p["count"] > 0])
        }
    
    def estimate_remaining_cost(
        self,
        videos_remaining: int,
        avg_duration: float = 30.0,
        avg_cost_per_second: float = 1.0
    ) -> Dict[str, Any]:
        """
        Estimate cost for remaining videos to produce.
        
        Args:
            videos_remaining: Number of videos still to produce
            avg_duration: Average video duration in seconds
            avg_cost_per_second: Average cost per second in credits
            
        Returns:
            Dict with cost estimates
        """
        total_duration = videos_remaining * avg_duration
        estimated_credits = total_duration * avg_cost_per_second
        estimated_cost = estimated_credits * 0.01  # Assuming $0.01 per credit estimate
        
        return {
            "videos_remaining": videos_remaining,
            "total_duration_seconds": total_duration,
            "estimated_credits_needed": round(estimated_credits, 0),
            "estimated_cost_usd": round(estimated_cost, 2),
            "assumptions": {
                "avg_duration_seconds": avg_duration,
                "cost_per_credit_usd": 0.01
            }
        }
    
    def get_full_status(self) -> Dict[str, Any]:
        """
        Get comprehensive production status.
        
        Returns:
            Dict with complete production status
        """
        credit_status = asyncio.run(self.get_credit_status())
        daily_summary = self.get_daily_summary()
        character_status = self.get_character_rotation_status()
        platform_dist = self.get_platform_distribution()
        weekly_summary = self.get_weekly_summary()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "production_status": self.current_status.value,
            "credits": credit_status,
            "daily": daily_summary,
            "character_rotation": character_status,
            "platform_distribution": platform_dist,
            "weekly": weekly_summary,
            "configuration": {
                "daily_target": self.config.daily_video_target,
                "characters": self.config.characters,
                "active_platforms": [p.value for p in Platform]
            }
        }


# Factory function
def create_production_monitor(config: ProductionConfig = None) -> ProductionMonitor:
    """
    Create and initialize a ProductionMonitor instance.
    
    Args:
        config: Optional production configuration
        
    Returns:
        Initialized ProductionMonitor instance
    """
    return ProductionMonitor(config)


if __name__ == "__main__":
    # Test the production monitor
    monitor = ProductionMonitor()
    
    print("=== Phase 1 Production Monitor ===")
    print()
    
    # Get credit status
    credits = asyncio.run(monitor.get_credit_status())
    print("Credit Status:")
    for key, value in credits.items():
        print(f"  {key}: {value}")
    print()
    
    # Record some test productions
    print("Recording test productions...")
    monitor.record_production(
        character_id="aurelia-viral",
        content_type="karaoke",
        platform="tiktok",
        duration_seconds=30.0,
        credits_consumed=35.0,
        cost_estimate=0.35,
        status="completed"
    )
    monitor.record_production(
        character_id="yuki-chan",
        content_type="reel",
        platform="instagram",
        duration_seconds=45.0,
        credits_consumed=50.0,
        cost_estimate=0.50,
        status="completed"
    )
    print()
    
    # Get daily summary
    daily = monitor.get_daily_summary()
    print("Daily Summary:")
    for key, value in daily.items():
        print(f"  {key}: {value}")
    print()
    
    # Get character rotation status
    rotation = monitor.get_character_rotation_status()
    print("Character Rotation:")
    print(f"  Next recommended: {rotation['next_recommended']}")
    print(f"  Remaining videos: {rotation['remaining_videos']}")
    print()
    
    # Get full status
    status = monitor.get_full_status()
    print("Full Status generated successfully")
