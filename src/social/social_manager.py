"""
Social Media Manager for Elite 8 AI Video Generation System

This module provides a unified interface for managing social media operations
across TikTok, Instagram, and YouTube platforms.
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from .base_client import (
    SocialMediaClient, PlatformType, PostResult, EngagementMetrics, 
    MediaAsset, MultiPlatformPoster, SocialMediaError
)
from .tiktok_client import TikTokClient, TikTokVideoConfig
from .instagram_client import InstagramClient, InstagramReelConfig
from .youtube_client import YouTubeClient, YouTubeShortConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PostingConfig:
    """Configuration for cross-platform posting"""
    platforms: List[PlatformType] = field(default_factory=lambda: [
        PlatformType.TIKTOK, 
        PlatformType.INSTAGRAM, 
        PlatformType.YOUTUBE
    ])
    stagger_minutes: int = 5
    retry_failed: bool = True
    max_retries: int = 2
    parallel_upload: bool = True
    adapt_content: bool = True


@dataclass
class PostCampaign:
    """Represents a multi-platform posting campaign"""
    campaign_id: str
    video_path: str
    caption: str
    tags: List[str]
    character: str
    scheduled_time: datetime
    config: PostingConfig = field(default_factory=PostingConfig)
    results: Dict[PlatformType, PostResult] = field(default_factory=dict)


class SocialMediaManager:
    """
    Unified manager for all social media operations
    
    This class provides:
    - Automatic client initialization and authentication
    - Cross-platform posting orchestration
    - Content adaptation for each platform
    - Scheduling and automation
    - Analytics aggregation
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the social media manager
        """
        # Set dynamic base path for Windows compatibility
        project_root = Path(__file__).resolve().parent.parent.parent
        
        default_config = project_root / "config" / "social" / "social_config.json"
        
        self.config_path = config_path or os.getenv(
            "SOCIAL_CONFIG_PATH",
            str(default_config)
        )
        self.config = self._load_config()
        
        # Initialize platform clients
        self.clients: Dict[PlatformType, SocialMediaClient] = {}
        self.poster = MultiPlatformPoster()
        
        # Initialize clients
        self._init_clients()
        
        # Campaign tracking
        self.active_campaigns: Dict[str, PostCampaign] = {}
        self.completed_campaigns: List[PostCampaign] = []
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("Social Media Manager initialized")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_all()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load social media configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config not found at {self.config_path}")
            return {"platforms": {}}
    
    def _init_clients(self):
        """Initialize platform-specific clients"""
        project_root = Path(__file__).resolve().parent.parent.parent
        
        # TikTok
        if self.config.get("platforms", {}).get("tiktok", {}).get("enabled", False):
            try:
                tiktok_config = os.getenv(
                    "TIKTOK_CONFIG_PATH",
                    str(project_root / "config" / "social" / "tiktok_config.json")
                )
                self.clients[PlatformType.TIKTOK] = TikTokClient(tiktok_config)
                self.poster.add_client(self.clients[PlatformType.TIKTOK])
                logger.info("TikTok client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize TikTok client: {e}")
        
        # Instagram
        if self.config.get("platforms", {}).get("instagram", {}).get("enabled", False):
            try:
                instagram_config = os.getenv(
                    "INSTAGRAM_CONFIG_PATH",
                    str(project_root / "config" / "social" / "instagram_config.json")
                )
                self.clients[PlatformType.INSTAGRAM] = InstagramClient(instagram_config)
                self.poster.add_client(self.clients[PlatformType.INSTAGRAM])
                logger.info("Instagram client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Instagram client: {e}")
        
        # YouTube
        if self.config.get("platforms", {}).get("youtube", {}).get("enabled", False):
            try:
                youtube_config = os.getenv(
                    "YOUTUBE_CONFIG_PATH",
                    str(project_root / "config" / "social" / "youtube_config.json")
                )
                self.clients[PlatformType.YOUTUBE] = YouTubeClient(youtube_config)
                self.poster.add_client(self.clients[PlatformType.YOUTUBE])
                logger.info("YouTube client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize YouTube client: {e}")
    
    def adapt_content(
        self,
        caption: str,
        tags: List[str],
        character: str,
        platform: PlatformType
    ) -> Tuple[str, List[str]]:
        """
        Adapt content for a specific platform
        
        Args:
            caption: Original caption
            tags: Original tags
            character: Character name
            platform: Target platform
            
        Returns:
            Tuple of (adapted_caption, adapted_tags)
        """
        character_branding = self.config.get("character_branding", {}).get(character, {})
        platform_config = character_branding.get(platform.value, {})
        
        # Get platform-specific style tags
        style_tags = platform_config.get("style_tags", [])
        
        # Combine original and style tags
        all_tags = list(set(tags + style_tags))
        
        # Truncate caption if needed
        caption_lengths = {
            PlatformType.TIKTOK: 2200,
            PlatformType.INSTAGRAM: 2200,
            PlatformType.YOUTUBE: 5000
        }
        max_length = caption_lengths.get(platform, 2200)
        adapted_caption = caption[:max_length] if len(caption) > max_length else caption
        
        return adapted_caption, all_tags[:30]
    
    async def post_to_platforms(
        self,
        video_path: str,
        caption: str,
        tags: List[str],
        character: str = "unknown",
        platforms: List[PlatformType] = None,
        duration_seconds: int = 15
    ) -> Dict[PlatformType, PostResult]:
        """
        Post content to specified platforms
        
        Args:
            video_path: Path to video file
            caption: Video caption
            tags: List of hashtags
            character: Character name
            platforms: List of platforms to post to
            duration_seconds: Video duration
            
        Returns:
            Dictionary of platform -> PostResult
        """
        logger.info(f"Posting to platforms: {platforms or 'all'}")
        
        if platforms is None:
            platforms = list(self.clients.keys())
        
        # Prepare media asset
        asset = MediaAsset(
            file_path=video_path,
            file_type="video",
            caption=caption,
            duration_seconds=duration_seconds
        )
        
        results = {}
        
        # Post to each platform
        for platform in platforms:
            if platform not in self.clients:
                logger.warning(f"Client not available for {platform.value}")
                continue
            
            client = self.clients[platform]
            
            try:
                # Adapt content for platform
                adapted_caption, adapted_tags = self.adapt_content(
                    caption, tags, character, platform
                )
                
                # Get platform-specific config
                config = self._get_platform_config(platform)
                
                # Upload
                if platform == PlatformType.TIKTOK:
                    result = await client.upload_video(
                        asset, adapted_caption, adapted_tags, config
                    )
                elif platform == PlatformType.INSTAGRAM:
                    result = await client.upload_video(
                        asset, adapted_caption, adapted_tags, config
                    )
                elif platform == PlatformType.YOUTUBE:
                    result = await client.upload_video(
                        asset, adapted_caption, "", adapted_tags, config
                    )
                else:
                    result = await client.upload_video(asset, adapted_caption, adapted_tags)
                
                results[platform] = result
                
                if result.success:
                    logger.info(f"Posted to {platform.value}: {result.post_id}")
                else:
                    logger.error(f"Failed to post to {platform.value}: {result.error_message}")
                
                # Stagger posts if configured
                if platform != platforms[-1]:
                    await asyncio.sleep(config.get("stagger_minutes", 5) * 60)
            
            except Exception as e:
                logger.error(f"Error posting to {platform.value}: {e}")
                results[platform] = PostResult(
                    success=False,
                    error_message=str(e),
                    platform=platform
                )
        
        return results
    
    def _get_platform_config(self, platform: PlatformType):
        """Get platform-specific upload configuration"""
        if platform == PlatformType.TIKTOK:
            return TikTokVideoConfig(
                visibility="public",
                allow_download=True,
                disable_comments=False
            )
        elif platform == PlatformType.INSTAGRAM:
            return InstagramReelConfig(
                like_and_view_counts_disabled=False
            )
        elif platform == PlatformType.YOUTUBE:
            return YouTubeShortConfig(
                visibility="public",
                made_for_kids=False,
                enable_comments=True
            )
        return None
    
    async def schedule_campaign(
        self,
        video_path: str,
        caption: str,
        tags: List[str],
        character: str,
        scheduled_time: datetime,
        platforms: List[PlatformType] = None
    ) -> str:
        """
        Schedule a posting campaign
        
        Args:
            video_path: Path to video file
            caption: Video caption
            tags: List of hashtags
            character: Character name
            scheduled_time: When to post
            platforms: Platforms to post to
            
        Returns:
            Campaign ID
        """
        import uuid
        
        campaign_id = str(uuid.uuid4())[:8]
        
        campaign = PostCampaign(
            campaign_id=campaign_id,
            video_path=video_path,
            caption=caption,
            tags=tags,
            character=character,
            scheduled_time=scheduled_time,
            config=PostingConfig(platforms=platforms or list(self.clients.keys()))
        )
        
        self.active_campaigns[campaign_id] = campaign
        
        # Schedule the campaign
        asyncio.create_task(self._execute_campaign(campaign))
        
        logger.info(f"Campaign {campaign_id} scheduled for {scheduled_time}")
        return campaign_id
    
    async def _execute_campaign(self, campaign: PostCampaign):
        """Execute a scheduled campaign"""
        now = datetime.now()
        delay = (campaign.scheduled_time - now).total_seconds()
        
        if delay > 0:
            logger.info(f"Waiting {delay}s before executing campaign {campaign.campaign_id}")
            await asyncio.sleep(delay)
        
        # Execute the campaign
        results = await self.post_to_platforms(
            video_path=campaign.video_path,
            caption=campaign.caption,
            tags=campaign.tags,
            character=campaign.character,
            platforms=campaign.config.platforms
        )
        
        campaign.results = results
        self.completed_campaigns.append(campaign)
        self.active_campaigns.pop(campaign.campaign_id, None)
        
        logger.info(f"Campaign {campaign.campaign_id} completed")
    
    async def get_all_engagement(
        self,
        post_id_map: Dict[PlatformType, str]
    ) -> Dict[PlatformType, EngagementMetrics]:
        """
        Get engagement metrics from all platforms for multiple posts
        
        Args:
            post_id_map: Mapping of platform -> post ID
            
        Returns:
            Dictionary of platform -> EngagementMetrics
        """
        return await self.poster.get_all_engagement(post_id_map)
    
    async def get_platform_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status for all platforms
        
        Returns:
            Dictionary of platform -> health status
        """
        health_status = {}
        
        for platform, client in self.clients.items():
            try:
                if hasattr(client, 'authenticate'):
                    is_authenticated = await client.authenticate()
                    
                    if hasattr(client, 'get_user_info'):
                        user_info = await client.get_user_info()
                    else:
                        user_info = {}
                    
                    health_status[platform.value] = {
                        "status": "healthy" if is_authenticated else "degraded",
                        "authenticated": is_authenticated,
                        "user_info": user_info
                    }
                else:
                    health_status[platform.value] = {
                        "status": "unknown",
                        "authenticated": False
                    }
            
            except Exception as e:
                health_status[platform.value] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status
    
    async def close_all(self):
        """Close all platform client sessions"""
        await self.poster.close_all()
        self.executor.shutdown(wait=True)
        logger.info("All social media connections closed")


class ContentScheduler:
    """
    Automated content scheduling based on optimized posting times
    """
    
    def __init__(self, manager: SocialMediaManager):
        self.manager = manager
        self.schedule_config = manager.config.get("posting_schedule", {})
    
    def get_optimal_times(
        self,
        platform: PlatformType,
        day_of_week: int = None
    ) -> List[datetime]:
        """
        Get optimal posting times for a platform
        
        Args:
            platform: Target platform
            day_of_week: Day of week (0=Monday)
            
        Returns:
            List of optimal posting times
        """
        platform_config = self.manager.config.get("platforms", {}).get(platform.value, {})
        posting_config = platform_config.get("posting", {})
        
        optimal_times = posting_config.get("optimal_times", ["08:00", "12:00", "18:00", "21:00"])
        timezone_str = posting_config.get("timezone", "Asia/Tokyo")
        
        from datetime import datetime
        import pytz
        
        timezone = pytz.timezone(timezone_str)
        now = datetime.now(timezone)
        
        if day_of_week is None:
            day_of_week = now.weekday()
        
        times = []
        for time_str in optimal_times:
            hour, minute = map(int, time_str.split(":"))
            
            posting_time = now.replace(
                hour=hour, 
                minute=minute, 
                second=0, 
                microsecond=0
            )
            
            # If time has passed today, schedule for next occurrence
            if posting_time <= now:
                posting_time += timedelta(days=1)
            
            # Adjust for specific day if needed
            if day_of_week != now.weekday():
                days_ahead = day_of_week - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                posting_time += timedelta(days=days_ahead)
                posting_time = posting_time.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
            
            times.append(posting_time)
        
        return times
    
    def generate_schedule(
        self,
        video_paths: List[str],
        character_rotation: List[str],
        start_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a posting schedule for multiple videos
        
        Args:
            video_paths: List of video file paths
            character_rotation: List of character names in rotation
            start_date: Start date for schedule
            
        Returns:
            List of scheduled posts
        """
        if start_date is None:
            start_date = datetime.now()
        
        schedule = []
        slots = self.schedule_config.get("daily_pattern", {})
        
        for i, video_path in enumerate(video_paths):
            character = character_rotation[i % len(character_rotation)]
            
            for slot_name, slot_info in slots.items():
                time_str = slot_info.get("time", "12:00")
                platforms = slot_info.get("platforms", ["tiktok", "instagram"])
                
                hour, minute = map(int, time_str.split(":"))
                posting_time = start_date.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                
                # Advance to next occurrence
                if posting_time <= start_date:
                    posting_time += timedelta(days=1)
                
                schedule.append({
                    "video_path": video_path,
                    "character": character,
                    "scheduled_time": posting_time,
                    "platforms": [PlatformType(p) for p in platforms],
                    "slot": slot_name
                })
                
                # Move to next day for next video
                start_date += timedelta(days=1)
        
        return schedule


# Convenience functions

async def quick_post_all(
    video_path: str,
    caption: str,
    tags: List[str] = None,
    character: str = "unknown"
) -> Dict[str, PostResult]:
    """
    Quick post to all configured platforms
    
    Args:
        video_path: Path to video file
        caption: Video caption
        tags: List of hashtags
        character: Character name
        
    Returns:
        Dictionary of platform -> PostResult
    """
    async with SocialMediaManager() as manager:
        results = await manager.post_to_platforms(
            video_path=video_path,
            caption=caption,
            tags=tags or [],
            character=character
        )
        return {p.value: r for p, r in results.items()}


async def check_all_platforms() -> Dict[str, Dict]:
    """
    Check health status of all platforms
    
    Returns:
        Health status for each platform
    """
    async with SocialMediaManager() as manager:
        return await manager.get_platform_health()


# Export classes and functions
__all__ = [
    "SocialMediaManager",
    "PostingConfig",
    "PostCampaign",
    "ContentScheduler",
    "quick_post_all",
    "check_all_platforms"
]
