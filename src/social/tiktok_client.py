"""
TikTok API Client for Elite 8 AI Video Generation System

This module provides comprehensive integration with the TikTok API for
automated video uploading, engagement tracking, and audience analytics.
"""

import os
import json
import time
import asyncio
import logging
import hashlib
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
class TikTokVideoConfig:
    """Configuration for TikTok video uploads"""
    disable_comments: bool = False
    duet_disabled: bool = False
    stitch_disabled: bool = False
    visibility: str = "public"  # public, private, friends
    allow_download: bool = True
    content_type: str = "video"
    auto_add_music: bool = True
    video_cover_timestamp: int = 0
    reference TikTok API documentation for all available options


class TikTokClient(SocialMediaClient):
    """
    TikTok API Client for automated video operations
    
    This client provides:
    - OAuth 2.0 authentication with TikTok
    - Video upload with metadata
    - Engagement metrics retrieval
    - Hashtag tracking and analytics
    - Comment management
    """
    
    BASE_URL = "https://open.tiktokapis.com/v2"
    
    def __init__(self, config_path: str = None):
        """
        Initialize the TikTok client
        
        Args:
            config_path: Path to TikTok-specific configuration
        """
        super().__init__(PlatformType.TIKTOK, config_path)
        
        # TikTok-specific settings
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        
        # Initialize session for video uploads
        self._upload_session: Optional[aiohttp.ClientSession] = None
        
        logger.info("TikTok client initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get TikTok-specific default configuration"""
        return {
            "platform": "tiktok",
            "rate_limit_rpm": 100,
            "burst_limit": 20,
            "max_video_size_mb": 287.6,  # TikTok's limit is 287.6MB
            "supported_formats": ["mp4", "mov"],
            "max_duration_seconds": 180,  # TikTok max is 10 min but optimal is 3 min
            "min_duration_seconds": 3,
            "optimal_aspect_ratio": "9:16",
            "optimal_resolution": "1080x1920",
            "max_tags": 10,
            "description_max_length": 2200,
            "default_visibility": "public"
        }
    
    async def authenticate(self) -> bool:
        """
        Authenticate with TikTok using OAuth 2.0
        
        Returns:
            True if authentication successful
            
        Raises:
            SocialMediaError: If authentication fails
        """
        logger.info("Authenticating with TikTok API")
        
        if not self.client_key or not self.client_secret:
            raise SocialMediaError(
                "TikTok credentials not configured. Set TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET.",
                self.platform,
                error_code="MISSING_CREDENTIALS"
            )
        
        # Check if we have a valid cached token
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            logger.info("Using cached access token")
            return True
        
        # Get access token using client credentials
        token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        
        session = await self._get_session()
        
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        
        try:
            async with session.post(token_url, data=data) as response:
                result = await response.json()
                
                if "access_token" in result:
                    self.access_token = result["access_token"]
                    self.refresh_token = result.get("refresh_token")
                    expires_in = result.get("expires_in", 86400)
                    self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    
                    logger.info("TikTok authentication successful")
                    return True
                else:
                    raise SocialMediaError(
                        result.get("error_description", "Authentication failed"),
                        self.platform,
                        error_code=result.get("error", "AUTH_FAILED")
                    )
        
        except aiohttp.ClientError as e:
            raise SocialMediaError(
                f"Network error during authentication: {str(e)}",
                self.platform,
                error_code="NETWORK_ERROR",
                retryable=True
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get TikTok-specific headers"""
        headers = super()._get_headers()
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    async def upload_video(
        self,
        asset: MediaAsset,
        caption: str,
        tags: List[str] = None,
        config: TikTokVideoConfig = None
    ) -> PostResult:
        """
        Upload a video to TikTok
        
        Args:
            asset: Media asset containing video file
            caption: Video caption/description
            tags: List of hashtags
            config: Additional TikTok-specific configuration
            
        Returns:
            PostResult with upload status and post ID
        """
        logger.info(f"Uploading video to TikTok: {asset.file_path}")
        
        # Authenticate first
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        # Validate media
        self._validate_media(asset)
        
        # Apply configuration
        if config is None:
            config = TikTokVideoConfig()
        
        # Build the post data
        post_data = self._build_post_data(caption, tags, config)
        
        # Upload the video
        result = await self._upload_video_file(asset, post_data)
        
        return result
    
    def _build_post_data(
        self,
        caption: str,
        tags: List[str],
        config: TikTokVideoConfig
    ) -> Dict[str, Any]:
        """Build the post data payload"""
        # Add hashtags to caption if provided
        full_caption = caption
        if tags:
            hashtag_str = " ".join([f"#{tag}" for tag in tags[:self.config.get("max_tags", 10)]])
            full_caption = f"{caption}\n\n{hashtag_str}"
        
        data = {
            "post_info": {
                "title": full_caption[:self.config.get("description_max_length", 2200)],
                "privacy_level": config.visibility,
                "disable_comments": config.disable_comments,
                "duet_disabled": config.duet_disabled,
                "stitch_disabled": config.stitch_disabled,
                "video_cover_timestamp": config.video_cover_timestamp,
                "content_type": config.content_type,
                "allow_download": config.allow_download
            }
        }
        
        return data
    
    async def _upload_video_file(
        self,
        asset: MediaAsset,
        post_data: Dict[str, Any]
    ) -> PostResult:
        """Upload the video file to TikTok"""
        
        # Initialize upload session
        if self._upload_session is None or self._upload_session.closed:
            timeout = aiohttp.ClientTimeout(total=600, connect=30, sock_read=60)
            self._upload_session = aiohttp.ClientSession(timeout=timeout)
        
        # Prepare file for upload
        file_size = os.path.getsize(asset.file_path)
        
        # Step 1: Initialize upload
        init_url = f"{self.BASE_URL}/post/publish/video/init/"
        
        headers = self._get_headers()
        headers["Content-Length"] = str(file_size)
        
        init_data = {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,  # Single chunk for simplicity
                "video_duration": asset.duration_seconds or 15
            }
        }
        
        try:
            # Initialize upload
            async with self._upload_session.post(
                init_url,
                json=init_data,
                headers=headers
            ) as response:
                init_result = await response.json()
                
                if "publish_id" not in init_result:
                    raise SocialMediaError(
                        f"Upload initialization failed: {init_result}",
                        self.platform,
                        error_code="UPLOAD_INIT_FAILED"
                    )
                
                publish_id = init_result["publish_id"]
            
            # Step 2: Upload video content
            upload_url = init_result.get("upload_url")
            
            # Use a generator to stream the video file in chunks to avoid memory issues
            async def file_sender():
                with open(asset.file_path, "rb") as f:
                    while True:
                        chunk = f.read(10 * 1024 * 1024) # 10MB chunks
                        if not chunk:
                            break
                        yield chunk

            async with self._upload_session.put(
                upload_url,
                data=file_sender(),
                headers={"Content-Type": "video/mp4"}
            ) as upload_response:
                if upload_response.status != 200:
                    raise SocialMediaError(
                        f"Video upload failed: {upload_response.status}",
                        self.platform,
                        error_code="UPLOAD_FAILED"
                    )
            
            # Step 3: Publish the video
            publish_url = f"{self.BASE_URL}/post/publish/video/publish/"
            publish_data = {
                "publish_id": publish_id,
                "post_info": post_data.get("post_info", {})
            }
            
            async with self._upload_session.post(
                publish_url,
                json=publish_data,
                headers=self._get_headers()
            ) as publish_response:
                publish_result = await publish_response.json()
                
                if "data" in publish_result and "publish_id" in publish_result["data"]:
                    post_id = publish_result["data"]["publish_id"]
                    
                    post_result = PostResult(
                        success=True,
                        post_id=post_id,
                        post_url=f"https://www.tiktok.com/@{self._get_username()}/video/{post_id}",
                        status=PostStatus.PUBLISHED,
                        platform=self.platform,
                        published_at=datetime.now(),
                        metadata={
                            "caption": post_data["post_info"].get("title", ""),
                            "privacy_level": post_data["post_info"].get("privacy_level", "public")
                        }
                    )
                    
                    logger.info(f"Video published successfully: {post_id}")
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
    
    def _get_username(self) -> str:
        """Get the authenticated user's username"""
        # In a real implementation, this would come from user info endpoint
        return "elite8_creator"
    
    async def get_post_status(self, post_id: str) -> PostResult:
        """
        Get the status of a TikTok post
        
        Args:
            post_id: The TikTok publish ID
            
        Returns:
            PostResult with current status
        """
        logger.info(f"Checking status for TikTok post: {post_id}")
        
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        # Query post status
        url = f"{self.BASE_URL}/post/query/"
        
        def _check_status():
            return self._make_request(
                "POST",
                url,
                data={"filters": {"publish_id": [post_id]}}
            )
        
        try:
            result = await self._retry_with_backoff(_check_status)
            
            if "data" in result and result["data"]:
                post_data = result["data"][0]
                
                status_map = {
                    "PROCESSING": PostStatus.PROCESSING,
                    "PUBLISHED": PostStatus.PUBLISHED,
                    "FAILED": PostStatus.FAILED
                }
                
                return PostResult(
                    success=post_data.get("status") == "PUBLISHED",
                    post_id=post_id,
                    post_url=f"https://www.tiktok.com/@{self._get_username()}/video/{post_id}",
                    status=status_map.get(post_data.get("status", "PROCESSING"), PostStatus.PROCESSING),
                    platform=self.platform,
                    metadata=post_data
                )
            else:
                return PostResult(
                    success=False,
                    post_id=post_id,
                    error_message="Post not found",
                    platform=self.platform
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
        Get engagement metrics for a TikTok post
        
        Args:
            post_id: The TikTok post ID
            
        Returns:
            EngagementMetrics with view, like, comment, and share counts
        """
        logger.info(f"Fetching engagement for TikTok post: {post_id}")
        
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        # Get video insights
        url = f"{self.BASE_URL}/video/query/"
        
        def _get_insights():
            return self._make_request(
                "POST",
                url,
                data={"filters": {"video_id": [post_id]}}
            )
        
        try:
            result = await self._retry_with_backoff(_get_insights)
            
            if "data" in result and result["data"]:
                video_data = result["data"][0]
                
                metrics = EngagementMetrics(
                    views=video_data.get("view_count", 0),
                    likes=video_data.get("like_count", 0),
                    comments=video_data.get("comment_count", 0),
                    shares=video_data.get("share_count", 0),
                    saves=video_data.get("collect_count", 0),
                    reach=video_data.get("reach", 0),
                    impressions=video_data.get("impression_count", 0),
                    updated_at=datetime.now()
                )
                
                # Calculate engagement rate
                if metrics.views > 0:
                    total_engagement = metrics.likes + metrics.comments + metrics.shares + metrics.saves
                    metrics.engagement_rate = (total_engagement / metrics.views) * 100
                
                return metrics
            
            return EngagementMetrics()
        
        except SocialMediaError:
            return EngagementMetrics()
    
    async def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user
        
        Returns:
            Dictionary with user information
        """
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        url = f"{self.BASE_URL}/user/info/"
        
        def _get_user():
            return self._make_request("GET", url, data={"fields": ["open_id", "union_id", "avatar_url", "display_name", "follower_count", "following_count", "likes_count"]})
        
        result = await self._retry_with_backoff(_get_user)
        return result.get("data", {}).get("user", {})
    
    async def delete_post(self, post_id: str) -> bool:
        """
        Delete a TikTok post
        
        Args:
            post_id: The post ID to delete
            
        Returns:
            True if deletion successful
        """
        logger.info(f"Deleting TikTok post: {post_id}")
        
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        url = f"{self.BASE_URL}/post/publish/video/delete/"
        
        def _delete():
            return self._make_request(
                "POST",
                url,
                data={"publish_id": post_id}
            )
        
        try:
            await self._retry_with_backoff(_delete)
            logger.info(f"Post {post_id} deleted successfully")
            return True
        except SocialMediaError as e:
            logger.error(f"Failed to delete post {post_id}: {e.message}")
            return False
    
    async def get_trending_hashtags(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending hashtags on TikTok
        
        Args:
            count: Number of trending hashtags to return
            
        Returns:
            List of trending hashtag information
        """
        # TikTok doesn't have a public trending hashtags API
        # This would typically use web scraping or third-party data
        logger.info("Getting trending hashtags (using cached data)")
        
        # Return cached trending hashtags
        return [
            {"tag": "fyp", "view_count": 1000000000000},
            {"tag": "foryou", "view_count": 900000000000},
            {"tag": "viral", "view_count": 800000000000},
            {"tag": "trending", "view_count": 700000000000},
            {"tag": "tiktok", "view_count": 600000000000}
        ][:count]
    
    async def close(self):
        """Close the TikTok client and upload session"""
        if self._upload_session and not self._upload_session.closed:
            await self._upload_session.close()
        await super().close()


# Convenience functions

async def quick_tiktok_post(
    video_path: str,
    caption: str,
    tags: List[str] = None
) -> PostResult:
    """
    Quick TikTok video post with default settings
    
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
    
    async with TikTokClient() as client:
        return await client.upload_video(asset, caption, tags)


# Export classes
__all__ = [
    "TikTokClient",
    "TikTokVideoConfig",
    "quick_tiktok_post"
]
