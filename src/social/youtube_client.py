"""
YouTube API Client for Elite 8 AI Video Generation System

This module provides comprehensive integration with the YouTube Data API v3
for automated short video uploading, engagement tracking, and channel analytics.
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
import google.oauth2.credentials
import google.auth.transport.requests
from google.auth.exceptions import RefreshError

from .base_client import SocialMediaClient, PlatformType, PostResult, EngagementMetrics, MediaAsset, SocialMediaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class YouTubeShortConfig:
    """Configuration for YouTube Shorts uploads"""
    channel_id: str = None
    made_for_kids: bool = False
    visibility: str = "public"  # public, private, unlisted
    publish_at: datetime = None
    playlist_id: str = None
    category_id: str = "22"  # People & Blogs
    tags: List[str] = field(default_factory=list)
    recording_date: datetime = None
    location: Dict[str, float] = None
    enable_comments: bool = True
    self_declared_made_for_kids: bool = False


class YouTubeClient(SocialMediaClient):
    """
    YouTube Data API v3 Client for automated Shorts operations
    
    This client provides:
    - OAuth 2.0 authentication with YouTube
    - Shorts/video upload with metadata
    - Engagement metrics retrieval
    - Channel and playlist management
    - Thumbnail and caption support
    """
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
    OAUTH_URL = "https://oauth2.googleapis.com"
    
    def __init__(self, config_path: str = None):
        """
        Initialize the YouTube client
        
        Args:
            config_path: Path to YouTube-specific configuration
        """
        super().__init__(PlatformType.YOUTUBE, config_path)
        
        # YouTube-specific credentials
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        
        # Access token (will be refreshed as needed)
        self.access_token = None
        self.token_expiry = None
        
        # Channel information
        self.channel_id = None
        self.channel_info = None
        
        # Initialize session for uploads
        self._upload_session: Optional[aiohttp.ClientSession] = None
        
        logger.info("YouTube client initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get YouTube-specific default configuration"""
        return {
            "platform": "youtube",
            "rate_limit_rpm": 50,
            "burst_limit": 10,
            "max_video_size_mb": 256,  # Shorts limit
            "supported_formats": ["mp4"],
            "max_duration_seconds": 60,  # Shorts max
            "min_duration_seconds": 3,
            "optimal_aspect_ratio": "9:16",
            "optimal_resolution": "1080x1920",
            "max_tags": 15,
            "title_max_length": 100,
            "description_max_length": 5000,
            "default_visibility": "public",
            "default_category": "22",
            "shorts_category": "22"
        }
    
    async def authenticate(self) -> bool:
        """
        Authenticate with YouTube using OAuth 2.0
        
        Returns:
            True if authentication successful
            
        Raises:
            SocialMediaError: If authentication fails
        """
        logger.info("Authenticating with YouTube API")
        
        # Check for cached valid token
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            logger.info("Using cached access token")
            return True
        
        # Check for refresh token
        if not self.refresh_token:
            raise SocialMediaError(
                "YouTube refresh token not configured. Set YOUTUBE_REFRESH_TOKEN.",
                self.platform,
                error_code="MISSING_TOKEN"
            )
        
        # Refresh the access token
        try:
            await self._refresh_access_token()
            
            # Get channel information
            await self._get_channel_info()
            
            logger.info("YouTube authentication successful")
            return True
        
        except SocialMediaError as e:
            raise e
        except Exception as e:
            raise SocialMediaError(
                f"Authentication failed: {str(e)}",
                self.platform,
                error_code="AUTH_FAILED"
            )
    
    async def _refresh_access_token(self):
        """Refresh the OAuth access token"""
        url = f"{self.OAUTH_URL}/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }
        
        session = await self._get_session()
        
        try:
            async with session.post(url, data=data) as response:
                result = await response.json()
                
                if "access_token" in result:
                    self.access_token = result["access_token"]
                    expires_in = result.get("expires_in", 3600)
                    self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    logger.info("Access token refreshed successfully")
                else:
                    raise SocialMediaError(
                        f"Token refresh failed: {result.get('error', 'Unknown error')}",
                        self.platform,
                        error_code="TOKEN_REFRESH_FAILED"
                    )
        
        except aiohttp.ClientError as e:
            raise SocialMediaError(
                f"Network error during token refresh: {str(e)}",
                self.platform,
                error_code="NETWORK_ERROR",
                retryable=True
            )
    
    async def _get_channel_info(self):
        """Get information about the authenticated user's channel"""
        url = f"{self.BASE_URL}/channels"
        
        params = {
            "part": "snippet,statistics,contentDetails",
            "mine": True,
            "key": self.api_key
        }
        
        headers = self._get_headers()
        
        session = await self._get_session()
        
        try:
            async with session.get(url, params=params, headers=headers) as response:
                result = await response.json()
                
                if "items" in result and result["items"]:
                    channel = result["items"][0]
                    self.channel_id = channel["id"]
                    self.channel_info = {
                        "id": channel["id"],
                        "title": channel["snippet"]["title"],
                        "description": channel["snippet"]["description"],
                        "subscriber_count": channel["statistics"].get("subscriberCount", "0"),
                        "video_count": channel["statistics"].get("videoCount", "0"),
                        "view_count": channel["statistics"].get("viewCount", "0"),
                        "uploads_playlist": channel["contentDetails"]["relatedPlaylists"]["uploads"]
                    }
                    logger.info(f"Found YouTube channel: {self.channel_info['title']}")
                else:
                    raise SocialMediaError(
                        "No YouTube channel found for this account",
                        self.platform,
                        error_code="NO_CHANNEL"
                    )
        
        except SocialMediaError:
            raise
        except Exception as e:
            logger.warning(f"Could not get channel info: {e}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get YouTube-specific headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    async def upload_video(
        self,
        asset: MediaAsset,
        title: str,
        description: str = "",
        tags: List[str] = None,
        config: YouTubeShortConfig = None
    ) -> PostResult:
        """
        Upload a YouTube Short
        
        Args:
            asset: Media asset containing video file
            title: Video title
            description: Video description
            tags: List of tags
            config: Additional YouTube-specific configuration
            
        Returns:
            PostResult with upload status and video ID
        """
        logger.info(f"Uploading Short to YouTube: {asset.file_path}")
        
        # Authenticate first
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        # Validate media
        self._validate_media(asset)
        
        # Apply configuration
        if config is None:
            config = YouTubeShortConfig()
        
        # Build metadata
        metadata = self._build_metadata(title, description, tags, config)
        
        # Upload the video
        result = await self._upload_short(asset, metadata, config)
        
        return result
    
    def _build_metadata(
        self,
        title: str,
        description: str,
        tags: List[str],
        config: YouTubeShortConfig
    ) -> Dict[str, Any]:
        """Build video metadata for upload"""
        # Process title
        title = title[:self.config.get("title_max_length", 100)]
        
        # Process description
        description = description[:self.config.get("description_max_length", 5000)]
        
        # Combine tags
        all_tags = tags if tags else []
        all_tags.extend(config.tags)
        all_tags = list(set(all_tags))[:self.config.get("max_tags", 15)]
        
        metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": all_tags,
                "categoryId": config.category_id or self.config.get("default_category", "22")
            },
            "status": {
                "privacyStatus": config.visibility,
                "selfDeclaredMadeForKids": config.made_for_kids,
                "publishAt": config.publish_at.isoformat() if config.publish_at else None,
                "madeForKids": config.made_for_kids,
                "publicStatsViewable": True,
                "comments": {
                    "canView": config.enable_comments,
                    "canInsert": config.enable_comments
                }
            },
            "recordingDetails": {}
        }
        
        # Add location if provided
        if config.location:
            metadata["recordingDetails"]["location"] = {
                "latitude": config.location.get("latitude", 0),
                "longitude": config.location.get("longitude", 0)
            }
        
        # Add recording date if provided
        if config.recording_date:
            metadata["recordingDetails"]["recordingDate"] = config.recording_date.isoformat()
        
        return metadata
    
    async def _upload_short(
        self,
        asset: MediaAsset,
        metadata: Dict[str, Any],
        config: YouTubeShortConfig
    ) -> PostResult:
        """Upload the Short to YouTube"""
        
        # Initialize upload session
        if self._upload_session is None or self._upload_session.closed:
            timeout = aiohttp.ClientTimeout(total=600, connect=30, sock_read=60)
            self._upload_session = aiohttp.ClientSession(timeout=timeout)
        
        # Get file info
        file_size = os.path.getsize(asset.file_path)
        
        # YouTube requires resumable upload for large files
        # Step 1: Initiate resumable upload
        initiate_url = f"{self.UPLOAD_URL}?part=snippet,status,recordingDetails&uploadType=resumable&key={self.api_key}"
        
        initiate_data = json.dumps(metadata)
        
        headers = self._get_headers()
        headers["Content-Length"] = str(len(initiate_data))
        headers["Content-Type"] = "application/json"
        headers["X-Upload-Content-Length"] = str(file_size)
        headers["X-Upload-Content-Type"] = "video/mp4"
        
        try:
            async with self._upload_session.post(
                initiate_url,
                data=initiate_data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise SocialMediaError(
                        f"Upload initiation failed: {error_text}",
                        self.platform,
                        error_code="INIT_FAILED"
                    )
                
                # Get upload location URL
                upload_url = response.headers.get("Location")
                if not upload_url:
                    raise SocialMediaError(
                        "No upload URL received from YouTube",
                        self.platform,
                        error_code="NO_UPLOAD_URL"
                    )
            
            # Step 2: Upload video content
            chunk_size = 10 * 1024 * 1024  # 10MB chunks
            offset = 0
            
            with open(asset.file_path, "rb") as video_file:
                while offset < file_size:
                    chunk = video_file.read(chunk_size)
                    chunk_length = len(chunk)
                    
                    # Calculate content range header
                    content_range = f"bytes {offset}-{offset + chunk_length - 1}/{file_size}"
                    
                    upload_headers = {
                        "Content-Length": str(chunk_length),
                        "Content-Range": content_range,
                        "Content-Type": "video/mp4"
                    }
                    
                    async with self._upload_session.put(
                        upload_url,
                        data=chunk,
                        headers=upload_headers
                    ) as upload_response:
                        if upload_response.status not in [200, 201, 308]:
                            error_text = await upload_response.text()
                            raise SocialMediaError(
                                f"Upload chunk failed: {upload_response.status} - {error_text}",
                                self.platform,
                                error_code="UPLOAD_FAILED"
                            )
                        
                        # Check for completion
                        if upload_response.status in [200, 201]:
                            result = await upload_response.json()
                            video_id = result["id"]
                            
                            post_result = PostResult(
                                success=True,
                                post_id=video_id,
                                post_url=f"https://www.youtube.com/shorts/{video_id}",
                                status=PostStatus.PUBLISHED,
                                platform=self.platform,
                                published_at=datetime.now(),
                                metadata={
                                    "title": metadata["snippet"]["title"],
                                    "description": metadata["snippet"]["description"],
                                    "visibility": metadata["status"]["privacyStatus"],
                                    "duration": asset.duration_seconds
                                }
                            )
                            
                            logger.info(f"Short uploaded successfully: {video_id}")
                            return post_result
                    
                    offset += chunk_length
            
            raise SocialMediaError(
                "Upload completed but no confirmation received",
                self.platform,
                error_code="UPLOAD_INCOMPLETE"
            )
        
        except aiohttp.ClientError as e:
            raise SocialMediaError(
                f"Network error during upload: {str(e)}",
                self.platform,
                error_code="NETWORK_ERROR",
                retryable=True
            )
    
    async def upload_with_url(
        self,
        video_url: str,
        title: str,
        description: str = "",
        tags: List[str] = None,
        config: YouTubeShortConfig = None
    ) -> PostResult:
        """
        Upload a video from a URL (for pre-hosted videos)
        
        Args:
            video_url: URL of the video to upload
            title: Video title
            description: Video description
            tags: List of tags
            config: Additional configuration
            
        Returns:
            PostResult
        """
        if config is None:
            config = YouTubeShortConfig()
        
        metadata = self._build_metadata(title, description, tags, config)
        
        # Use simple upload for URL-based videos
        url = f"{self.UPLOAD_URL}?part=snippet,status,recordingDetails&key={self.api_key}"
        
        body = {
            "snippet": metadata["snippet"],
            "status": metadata["status"],
            "recordingDetails": metadata.get("recordingDetails", {}),
            "contentDetails": {
                "contentRating": {},
                "fileDetails": {
                    "uploader": "Elite 8 System"
                }
            }
        }
        
        # Note: URL upload is limited; for production, use direct file upload
        raise SocialMediaError(
            "URL upload not directly supported. Use file upload instead.",
            self.platform,
            error_code="NOT_IMPLEMENTED"
        )
    
    async def get_post_status(self, video_id: str) -> PostResult:
        """
        Get the status of a YouTube video
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            PostResult with current status
        """
        logger.info(f"Checking status for YouTube video: {video_id}")
        
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        url = f"{self.BASE_URL}/videos"
        
        params = {
            "part": "snippet,status,statistics,contentDetails",
            "id": video_id,
            "key": self.api_key
        }
        
        try:
            session = await self._get_session()
            
            async with session.get(url, params=params, headers=self._get_headers()) as response:
                result = await response.json()
                
                if "items" in result and result["items"]:
                    video = result["items"][0]
                    
                    status_map = {
                        "public": PostStatus.PUBLISHED,
                        "private": PostStatus.DRAFT,
                        "unlisted": PostStatus.SCHEDULED
                    }
                    
                    return PostResult(
                        success=True,
                        post_id=video_id,
                        post_url=f"https://www.youtube.com/shorts/{video_id}",
                        status=status_map.get(video["status"]["privacyStatus"], PostStatus.PUBLISHED),
                        platform=self.platform,
                        published_at=datetime.fromisoformat(
                            video["snippet"]["publishedAt"].replace("Z", "+00:00")
                        ) if "publishedAt" in video["snippet"] else None,
                        metadata={
                            "title": video["snippet"]["title"],
                            "description": video["snippet"]["description"],
                            "privacyStatus": video["status"]["privacyStatus"],
                            "duration": video["contentDetails"].get("duration")
                        }
                    )
                else:
                    return PostResult(
                        success=False,
                        post_id=video_id,
                        error_message="Video not found",
                        platform=self.platform
                    )
        
        except SocialMediaError as e:
            return PostResult(
                success=False,
                post_id=video_id,
                error_message=e.message,
                platform=self.platform
            )
    
    async def get_engagement(self, video_id: str) -> EngagementMetrics:
        """
        Get engagement metrics for a YouTube video
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            EngagementMetrics with view, like, comment, and share counts
        """
        logger.info(f"Fetching engagement for YouTube video: {video_id}")
        
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        url = f"{self.BASE_URL}/videos"
        
        params = {
            "part": "statistics",
            "id": video_id,
            "key": self.api_key
        }
        
        try:
            session = await self._get_session()
            
            async with session.get(url, params=params, headers=self._get_headers()) as response:
                result = await response.json()
            
            metrics = EngagementMetrics()
            
            if "items" in result and result["items"]:
                stats = result["items"][0]["statistics"]
                
                metrics.views = int(stats.get("viewCount", 0))
                metrics.likes = int(stats.get("likeCount", 0))
                metrics.comments = int(stats.get("commentCount", 0))
                
                # Calculate engagement rate
                if metrics.views > 0:
                    total_engagement = metrics.likes + metrics.comments
                    metrics.engagement_rate = (total_engagement / metrics.views) * 100
            
            metrics.updated_at = datetime.now()
            return metrics
        
        except Exception as e:
            logger.warning(f"Failed to fetch engagement: {e}")
            return EngagementMetrics()
    
    async def get_channel_stats(self) -> Dict[str, Any]:
        """
        Get statistics for the authenticated channel
        
        Returns:
            Dictionary with channel statistics
        """
        if not self.channel_info:
            await self.authenticate()
        
        if not self.channel_info:
            return {}
        
        return {
            "subscriber_count": self.channel_info.get("subscriber_count", "0"),
            "video_count": self.channel_info.get("video_count", "0"),
            "view_count": self.channel_info.get("view_count", "0"),
            "uploads_playlist": self.channel_info.get("uploads_playlist")
        }
    
    async def get_channel_videos(
        self,
        max_results: int = 50,
        playlist_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get videos from the channel's uploads playlist
        
        Args:
            max_results: Maximum number of videos to return
            playlist_id: Override playlist ID
            
        Returns:
            List of video information
        """
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        # Get uploads playlist ID
        if not playlist_id:
            if not self.channel_info:
                await self._get_channel_info()
            playlist_id = self.channel_info.get("uploads_playlist")
        
        if not playlist_id:
            return []
        
        url = f"{self.BASE_URL}/playlistItems"
        
        params = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": max_results,
            "key": self.api_key
        }
        
        try:
            session = await self._get_session()
            
            async with session.get(url, params=params, headers=self._get_headers()) as response:
                result = await response.json()
            
            videos = []
            for item in result.get("items", []):
                videos.append({
                    "id": item["contentDetails"]["videoId"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "published_at": item["snippet"]["publishedAt"],
                    "thumbnail": item["snippet"]["thumbnails"].get("medium", {}).get("url")
                })
            
            return videos
        
        except Exception as e:
            logger.error(f"Failed to get channel videos: {e}")
            return []
    
    async def delete_video(self, video_id: str) -> bool:
        """
        Delete a YouTube video
        
        Args:
            video_id: The video ID to delete
            
        Returns:
            True if deletion successful
        """
        logger.info(f"Deleting YouTube video: {video_id}")
        
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        url = f"{self.BASE_URL}/videos"
        
        params = {
            "id": video_id,
            "key": self.api_key
        }
        
        try:
            session = await self._get_session()
            
            async with session.delete(url, params=params, headers=self._get_headers()) as response:
                if response.status == 204:
                    logger.info(f"Video {video_id} deleted successfully")
                    return True
                else:
                    result = await response.json()
                    logger.error(f"Failed to delete video: {result}")
                    return False
        
        except Exception as e:
            logger.error(f"Failed to delete video {video_id}: {e}")
            return False
    
    async def update_video(
        self,
        video_id: str,
        title: str = None,
        description: str = None,
        tags: List[str] = None,
        visibility: str = None
    ) -> bool:
        """
        Update video metadata
        
        Args:
            video_id: The video ID to update
            title: New title
            description: New description
            tags: New tags
            visibility: New privacy status
            
        Returns:
            True if update successful
        """
        logger.info(f"Updating YouTube video: {video_id}")
        
        if not await self.authenticate():
            raise SocialMediaError("Authentication required", self.platform, error_code="NOT_AUTHENTICATED")
        
        # Build update payload
        update_data = {"id": video_id}
        
        if title or description or tags:
            snippet = {}
            if title:
                snippet["title"] = title[:self.config.get("title_max_length", 100)]
            if description:
                snippet["description"] = description[:self.config.get("description_max_length", 5000)]
            if tags:
                snippet["tags"] = list(set(tags))[:self.config.get("max_tags", 15)]
            update_data["snippet"] = snippet
        
        if visibility:
            update_data["status"] = {"privacyStatus": visibility}
        
        url = f"{self.BASE_URL}/videos"
        
        params = {
            "part": ",".join(k for k in update_data.keys() if k != "id"),
            "key": self.api_key
        }
        
        try:
            session = await self._get_session()
            
            async with session.put(
                url,
                params=params,
                json=update_data,
                headers=self._get_headers()
            ) as response:
                if response.status in [200, 201]:
                    logger.info(f"Video {video_id} updated successfully")
                    return True
                else:
                    result = await response.json()
                    logger.error(f"Failed to update video: {result}")
                    return False
        
        except Exception as e:
            logger.error(f"Failed to update video {video_id}: {e}")
            return False
    
    async def close(self):
        """Close the YouTube client and upload session"""
        if self._upload_session and not self._upload_session.closed:
            await self._upload_session.close()
        await super().close()


# Convenience functions

async def quick_youtube_post(
    video_path: str,
    title: str,
    description: str = "",
    tags: List[str] = None
) -> PostResult:
    """
    Quick YouTube Short post with default settings
    
    Args:
        video_path: Path to video file
        title: Video title
        description: Video description
        tags: List of tags
        
    Returns:
        PostResult
    """
    asset = MediaAsset(
        file_path=video_path,
        file_type="video",
        caption=description
    )
    
    async with YouTubeClient() as client:
        return await client.upload_video(asset, title, description, tags)


# Export classes
__all__ = [
    "YouTubeClient",
    "YouTubeShortConfig",
    "quick_youtube_post"
]
