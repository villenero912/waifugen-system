"""
Instagram API Client for Elite 8 AI Video Generation System

This module provides comprehensive integration with the Instagram Graph API
for automated reel uploading, engagement tracking, and audience analytics.
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import aiohttp

from .base_client import SocialMediaClient, PlatformType, PostResult, EngagementMetrics, MediaAsset, SocialMediaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class InstagramReelConfig:
    """Configuration for Instagram Reel uploads"""
    is_reshare: bool = False
    cover_url: Optional[str] = None
    alt_text: Optional[str] = None
    location_id: Optional[str] = None
    user_tags: List[Dict] = field(default_factory=list)
    like_and_view_counts_disabled: bool = False
    create_audio_mix: bool = False
    audio_mix_id: Optional[str] = None


class InstagramClient(SocialMediaClient):
    """
    Instagram Graph API Client for automated reel operations
    
    This client provides:
    - Facebook OAuth authentication with Instagram permissions
    - Reel/video upload with metadata
    - Engagement metrics retrieval
    - Hashtag and mention tracking
    - Story posting support
    """
    
    BASE_URL = "https://graph.instagram.com/v18.0"
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Instagram client
        
        Args:
            config_path: Path to Instagram-specific configuration
        """
        super().__init__(PlatformType.INSTAGRAM, config_path)
        
        # Instagram-specific credentials (through Facebook)
        self.app_id = os.getenv("INSTAGRAM_APP_ID")
        self.app_secret = os.getenv("INSTAGRAM_APP_SECRET")
        self.access_token = None
        self.instagram_business_account_id = None
        self.user_id = None
        
        # Initialize session for video uploads
        self._upload_session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Instagram client initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get Instagram-specific default configuration"""
        return {
            "platform": "instagram",
            "rate_limit_rpm": 50,
            "burst_limit": 10,
            "max_video_size_mb": 650,  # Instagram's limit
            "supported_formats": ["mp4"],
            "max_duration_seconds": 90,  # Reels max
            "min_duration_seconds": 3,
            "optimal_aspect_ratio": "9:16",
            "optimal_resolution": "1080x1920",
            "max_tags": 30,
            "caption_max_length": 2200,
            "default_visibility": "public"
        }
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Instagram Graph API
        
        Returns:
            True if authentication successful
            
        Raises:
            SocialMediaError: If authentication fails
        """
        logger.info("Authenticating with Instagram Graph API")
        
        # Check for cached token
        if self.access_token and self._is_token_valid():
            logger.info("Using cached access token")
            return True
        
        # Get token from environment or OAuth flow
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        
        if not self.access_token:
            raise SocialMediaError(
                "Instagram access token not configured. Set INSTAGRAM_ACCESS_TOKEN.",
                self.platform,
                error_code="MISSING_TOKEN"
            )
        
        # Get long-lived token if needed
        if self._is_short_lived_token():
            try:
                await self._exchange_for_long_lived_token()
            except SocialMediaError as e:
                logger.warning(f"Could not exchange for long-lived token: {e}")
        
        # Get Instagram Business Account ID
        await self._get_instagram_account()
        
        logger.info("Instagram authentication successful")
        return True
    
    def _is_token_valid(self) -> bool:
        """Check if the current access token is valid"""
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry
    
    def _is_short_lived_token(self) -> bool:
        """Check if the token is short-lived (expires in ~60 days)"""
        # Short-lived tokens don't have expiry info set
        return self.token_expiry is None
    
    async def _exchange_for_long_lived_token(self):
        """Exchange short-lived token for long-lived token"""
        url = "https://graph.facebook.com/v18.0/oauth/access_token"
        
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": self.access_token
        }
        
        session = await self._get_session()
        
        async with session.get(url, params=params) as response:
            result = await response.json()
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                expires_in = result.get("expires_in", 5184000)  # ~60 days default
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                logger.info("Exchanged for long-lived token")
            else:
                raise SocialMediaError(
                    "Failed to exchange for long-lived token",
                    self.platform
                )
    
    async def _get_instagram_account(self):
        """Get the Instagram Business Account ID"""
        url = f"https://graph.facebook.com/v18.0/me"
        
        params = {
            "fields": "instagram_business_account",
            "access_token": self.access_token
        }
        
        session = await self._get_session()
        
        async with session.get(url, params=params) as response:
            result = await response.json()
            
            if "instagram_business_account" in result:
                self.instagram_business_account_id = result["instagram_business_account"]["id"]
                self.user_id = result["id"]
                logger.info(f"Found Instagram Business Account: {self.instagram_business_account_id}")
            else:
                raise SocialMediaError(
                    "No Instagram Business Account found for this user",
                    self.platform,
                    error_code="NO_INSTAGRAM_ACCOUNT"
                )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get Instagram-specific headers"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def upload_video(
        self,
        asset: MediaAsset,
        caption: str,
        tags: List[str] = None,
        config: InstagramReelConfig = None
    ) -> PostResult:
        """
        Upload a video/reel to Instagram
        
        Args:
            asset: Media asset containing video file
            caption: Video caption/description
            tags: List of hashtags
            config: Additional Instagram-specific configuration
            
        Returns:
            PostResult with upload status and post ID
        """
        logger.info(f"Uploading reel to Instagram: {asset.file_path}")
        
        # Authenticate first
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        # Validate media
        self._validate_media(asset)
        
        # Apply configuration
        if config is None:
            config = InstagramReelConfig()
        
        # Upload the reel
        result = await self._upload_reel(asset, caption, tags, config)
        
        return result
    
    async def _upload_reel(
        self,
        asset: MediaAsset,
        caption: str,
        tags: List[str],
        config: InstagramReelConfig
    ) -> PostResult:
        """Upload the reel to Instagram"""
        
        # Initialize upload session
        if self._upload_session is None or self._upload_session.closed:
            timeout = aiohttp.ClientTimeout(total=600, connect=30, sock_read=60)
            self._upload_session = aiohttp.ClientSession(timeout=timeout)
        
        # Prepare file
        file_size = os.path.getsize(asset.file_path)
        
        # [CRITICAL] Instagram Graph API requires a PUBLIC URL for video_url.
        # Local paths (like C:\... or /home/...) will not be accessible by Meta's servers.
        if not asset.file_path.startswith(('http://', 'https://')):
            logger.error(f"Instagram upload requires a public URL, but got local path: {asset.file_path}")
            raise SocialMediaError(
                "Instagram Graph API requires a publicly accessible URL for video uploads. "
                "Local file paths (C:\\... or /workspace/...) are not supported. "
                "Please host the video on a temporary public server (e.g. S3, Cloudinary, etc.) "
                "before attempting to publish to Instagram.",
                self.platform,
                error_code="LOCAL_PATH_NOT_SUPPORTED"
            )
            
        # Build caption with hashtags
        full_caption = caption
        if tags:
            hashtag_str = " ".join([f"#{tag}" for tag in tags[:self.config.get("max_tags", 30)]])
            full_caption = f"{caption}\n\n{hashtag_str}"
        
        # Step 1: Create container
        container_url = f"{self.BASE_URL}/{self.instagram_business_account_id}/media"
        
        container_data = {
            "video_url": asset.file_path,  # URL-based upload or use file
            "caption": full_caption[:self.config.get("caption_max_length", 2200)],
            "media_type": "REELS",
            "is_reshare_disabled": config.is_reshare,
            "like_and_view_counts_disabled": config.like_and_view_counts_disabled,
            "access_token": self.access_token
        }
        
        # For direct file upload, use the container endpoint
        try:
            async with self._upload_session.post(
                container_url,
                data=container_data
            ) as response:
                container_result = await response.json()
                
                if "id" not in container_result:
                    raise SocialMediaError(
                        f"Container creation failed: {container_result}",
                        self.platform,
                        error_code="CONTAINER_FAILED"
                    )
                
                container_id = container_result["id"]
            
            # Step 2: Wait for media processing
            container_status = await self._wait_for_container(container_id)
            
            if not container_status.get("success"):
                error_message = container_status.get("error", {}).get("message", "Processing failed")
                raise SocialMediaError(
                    f"Video processing failed: {error_message}",
                    self.platform,
                    error_code="PROCESSING_FAILED"
                )
            
            # Step 3: Publish the reel
            publish_url = f"{self.BASE_URL}/{self.instagram_business_account_id}/media_publish"
            
            publish_data = {
                "creation_id": container_id,
                "access_token": self.access_token
            }
            
            async with self._upload_session.post(
                publish_url,
                data=publish_data
            ) as publish_response:
                publish_result = await publish_response.json()
                
                if "id" in publish_result:
                    post_id = publish_result["id"]
                    
                    post_result = PostResult(
                        success=True,
                        post_id=post_id,
                        post_url=f"https://www.instagram.com/reel/{post_id}",
                        status=PostStatus.PUBLISHED,
                        platform=self.platform,
                        published_at=datetime.now(),
                        metadata={
                            "caption": full_caption,
                            "media_type": "REELS",
                            "duration": asset.duration_seconds
                        }
                    )
                    
                    logger.info(f"Reel published successfully: {post_id}")
                    return post_result
                else:
                    raise SocialMediaError(
                        f"Publish failed: {publish_result}",
                        self.platform,
                        error_code="PUBLISH_FAILED"
                    )
        
        except aiohttp.ClientError as e:
            raise SocialMediaError(
                f"Network error during upload: {str(e)}",
                self.platform,
                error_code="NETWORK_ERROR",
                retryable=True
            )
    
    async def _wait_for_container(self, container_id: str, max_wait: int = 600) -> Dict:
        """Wait for video container to finish processing"""
        status_url = f"{self.BASE_URL}/{container_id}"
        
        start_time = time.time()
        poll_interval = 5
        
        while time.time() - start_time < max_wait:
            params = {
                "fields": "status,status_code,video_result",
                "access_token": self.access_token
            }
            
            session = await self._get_session()
            
            async with session.get(status_url, params=params) as response:
                result = await response.json()
                
                status_code = result.get("status_code", "IN_PROGRESS")
                
                if status_code == "FINISHED":
                    return {"success": True, "data": result}
                elif status_code == "ERROR":
                    return {"success": False, "error": result}
                
                logger.debug(f"Container {container_id}: {status_code}")
                await asyncio.sleep(poll_interval)
        
        return {"success": False, "error": "Timeout waiting for processing"}
    
    async def upload_video_file(
        self,
        video_path: str,
        caption: str,
        tags: List[str] = None
    ) -> PostResult:
        """
        Upload a video file directly (alternative method)
        
        Args:
            video_path: Path to video file
            caption: Video caption
            tags: List of hashtags
            
        Returns:
            PostResult
        """
        # Read video file
        with open(video_path, "rb") as f:
            video_content = f.read()
        
        asset = MediaAsset(
            file_path=video_path,
            file_type="video",
            caption=caption,
            file_size=len(video_content)
        )
        
        return await self.upload_video(asset, caption, tags)
    
    async def get_post_status(self, post_id: str) -> PostResult:
        """
        Get the status of an Instagram post
        
        Args:
            post_id: The Instagram media ID
            
        Returns:
            PostResult with current status
        """
        logger.info(f"Checking status for Instagram post: {post_id}")
        
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        url = f"{self.BASE_URL}/{post_id}"
        
        params = {
            "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count,reach,impressions",
            "access_token": self.access_token
        }
        
        try:
            session = await self._get_session()
            
            async with session.get(url, params=params) as response:
                result = await response.json()
                
                if "error" in result:
                    return PostResult(
                        success=False,
                        post_id=post_id,
                        error_message=result["error"]["message"],
                        platform=self.platform
                    )
                
                return PostResult(
                    success=True,
                    post_id=post_id,
                    post_url=result.get("permalink", f"https://instagram.com/p/{post_id}"),
                    status=PostStatus.PUBLISHED,
                    platform=self.platform,
                    metadata={
                        "caption": result.get("caption", ""),
                        "media_type": result.get("media_type", "VIDEO"),
                        "timestamp": result.get("timestamp")
                    }
                )
        
        except SocialMediaError as e:
            return PostResult(
                success=False,
                post_id=post_id,
                error_message=e.message,
                platform=self.platform
            )
    
    async def get_engagement(self, post_id: str) -> EngagementMetrics:
        """
        Get engagement metrics for an Instagram post
        
        Args:
            post_id: The Instagram media ID
            
        Returns:
            EngagementMetrics with view, like, comment, and share counts
        """
        logger.info(f"Fetching engagement for Instagram post: {post_id}")
        
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        url = f"{self.BASE_URL}/{post_id}/insights"
        
        params = {
            "metric": "engagement,impressions,reach,likes,comments,saved,shares",
            "period": "lifetime",
            "access_token": self.access_token
        }
        
        try:
            session = await self._get_session()
            
            async with session.get(url, params=params) as response:
                result = await response.json()
            
            metrics = EngagementMetrics()
            
            if "data" in result:
                for insight in result["data"]:
                    name = insight.get("name")
                    values = insight.get("values", [])
                    if values:
                        value = values[0].get("value", 0)
                        
                        if name == "engagement":
                            metrics.engagement_rate = value
                        elif name == "impressions":
                            metrics.impressions = value
                        elif name == "reach":
                            metrics.reach = value
                        elif name == "likes":
                            metrics.likes = value
                        elif name == "comments":
                            metrics.comments = value
                        elif name == "saved":
                            metrics.saves = value
                        elif name == "shares":
                            metrics.shares = value
            
            # Calculate view metrics if not directly available
            if metrics.impressions > 0 and metrics.views == 0:
                # Views often correlate with impressions for video content
                metrics.views = metrics.impressions
            
            metrics.updated_at = datetime.now()
            return metrics
        
        except Exception as e:
            logger.warning(f"Failed to fetch engagement: {e}")
            return EngagementMetrics()
    
    async def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated Instagram account
        
        Returns:
            Dictionary with user information
        """
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        url = f"{self.BASE_URL}/{self.instagram_business_account_id}"
        
        params = {
            "fields": "id,username,name,profile_picture_url,followers_count,follows_count,media_count,biography,website",
            "access_token": self.access_token
        }
        
        try:
            session = await self._get_session()
            
            async with session.get(url, params=params) as response:
                result = await response.json()
                return result
        
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {}
    
    async def get_user_media(
        self,
        limit: int = 25,
        since: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent media from the authenticated account
        
        Args:
            limit: Maximum number of posts to return
            since: Only get posts after this date
            
        Returns:
            List of media items
        """
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        url = f"{self.BASE_URL}/{self.instagram_business_account_id}/media"
        
        params = {
            "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
            "limit": limit,
            "access_token": self.access_token
        }
        
        if since:
            params["since"] = int(since.timestamp())
        
        try:
            session = await self._get_session()
            
            async with session.get(url, params=params) as response:
                result = await response.json()
                return result.get("data", [])
        
        except Exception as e:
            logger.error(f"Failed to get user media: {e}")
            return []
    
    async def delete_post(self, post_id: str) -> bool:
        """
        Delete an Instagram post
        
        Args:
            post_id: The post ID to delete
            
        Returns:
            True if deletion successful
        """
        logger.info(f"Deleting Instagram post: {post_id}")
        
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        url = f"{self.BASE_URL}/{post_id}"
        
        params = {
            "access_token": self.access_token
        }
        
        try:
            session = await self._get_session()
            
            async with session.delete(url, params=params) as response:
                result = await response.json()
                
                if result.get("success", False):
                    logger.info(f"Post {post_id} deleted successfully")
                    return True
                else:
                    logger.error(f"Failed to delete post: {result}")
                    return False
        
        except Exception as e:
            logger.error(f"Failed to delete post {post_id}: {e}")
            return False
    
    async def post_story(
        self,
        asset: MediaAsset,
        link_url: str = None
    ) -> PostResult:
        """
        Post a story to Instagram
        
        Args:
            asset: Media asset (image or video)
            link_url: Optional URL for story link sticker
            
        Returns:
            PostResult
        """
        logger.info(f"Uploading story to Instagram: {asset.file_path}")
        
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        # Stories have different requirements
        self.config["max_duration_seconds"] = 60  # Stories max
        self._validate_media(asset)
        
        url = f"{self.BASE_URL}/{self.instagram_business_account_id}/media"
        
        story_data = {
            "image_url": asset.file_path if asset.file_type == "image" else None,
            "video_url": asset.file_path if asset.file_type == "video" else None,
            "media_type": "STORIES",
            "access_token": self.access_token
        }
        
        if link_url:
            story_data["link_url"] = link_url
        
        try:
            session = await self._get_session()
            
            async with session.post(url, data=story_data) as response:
                result = await response.json()
                
                if "id" in result:
                    return PostResult(
                        success=True,
                        post_id=result["id"],
                        status=PostStatus.PUBLISHED,
                        platform=self.platform,
                        published_at=datetime.now()
                    )
                else:
                    raise SocialMediaError(
                        f"Story upload failed: {result}",
                        self.platform
                    )
        
        except Exception as e:
            return PostResult(
                success=False,
                error_message=str(e),
                platform=self.platform
            )
    
    async def close(self):
        """Close the Instagram client and upload session"""
        if self._upload_session and not self._upload_session.closed:
            await self._upload_session.close()
        await super().close()


# Convenience functions

async def quick_instagram_post(
    video_path: str,
    caption: str,
    tags: List[str] = None
) -> PostResult:
    """
    Quick Instagram reel post with default settings
    
    Args:
        video_path: Path to video file
        caption: Video caption
        tags: List of hashtags
        
    Returns:
        PostResult
    """
    asset = MediaAsset(
        file_path=video_path,
        file_type="video",
        caption=caption
    )
    
    async with InstagramClient() as client:
        return await client.upload_video(asset, caption, tags)


# Export classes
__all__ = [
    "InstagramClient",
    "InstagramReelConfig",
    "quick_instagram_post"
]
