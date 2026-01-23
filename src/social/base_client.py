"""
Base Social Media Client for Elite 8 AI Video Generation System

This module provides the foundational classes and utilities shared across all
social media platform integrations, including authentication, rate limiting,
and common posting functionality.
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
from enum import Enum
from pathlib import Path
import aiohttp
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """Supported social media platforms"""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"


class PostStatus(Enum):
    """Status of a post operation"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass
class PostResult:
    """Result of a post operation"""
    success: bool
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    status: PostStatus = PostStatus.DRAFT
    error_message: Optional[str] = None
    platform: Optional[PlatformType] = None
    published_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngagementMetrics:
    """Engagement metrics for a post"""
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    reach: int = 0
    impressions: int = 0
    engagement_rate: float = 0.0
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass 
class MediaAsset:
    """Media asset for posting"""
    file_path: str
    file_type: str  # video, image, thumbnail
    caption: str = ""
    alt_text: str = ""
    duration_seconds: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None


class SocialMediaError(Exception):
    """Custom exception for social media operations"""
    
    def __init__(self, message: str, platform: PlatformType = None, 
                 error_code: str = None, retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.platform = platform
        self.error_code = error_code
        self.retryable = retryable
    
    def __str__(self):
        base = f"Social Media Error: {self.message}"
        if self.platform:
            base += f" (Platform: {self.platform.value})"
        if self.error_code:
            base += f" (Code: {self.error_code})"
        return base


class RateLimiter:
    """Rate limiter for API requests to prevent throttling"""
    
    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.requests: List[float] = []
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire permission to make a request"""
        async with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            # Remove old requests from tracking
            self.requests = [t for t in self.requests if t > minute_ago]
            
            # Check if we're at the rate limit
            if len(self.requests) >= self.requests_per_minute:
                wait_time = self.requests[0] - minute_ago + 1
                await asyncio.sleep(wait_time)
                return await self.acquire()
            
            # Check burst limit
            recent_requests = [t for t in self.requests if t > now - 10]
            if len(recent_requests) >= self.burst_limit:
                wait_time = 10 - (now - recent_requests[0])
                await asyncio.sleep(max(0, wait_time))
            
            # Record this request
            self.requests.append(now)
            return True


class SocialMediaClient(ABC):
    """
    Abstract base class for social media platform clients
    
    This class provides common functionality and defines the interface
    that all platform-specific clients must implement.
    """
    
    def __init__(self, platform: PlatformType, config_path: str = None):
        """
        Initialize the social media client
        
        Args:
            platform: The platform type this client handles
            config_path: Path to platform-specific configuration
        """
        self.platform = platform
        self.config_path = config_path
        self.config = self._load_config()
        self.rate_limiter = RateLimiter(
            requests_per_minute=self.config.get("rate_limit_rpm", 60),
            burst_limit=self.config.get("burst_limit", 10)
        )
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Tracking
        self.post_history: Dict[str, PostResult] = {}
        self.metrics_history: Dict[str, EngagementMetrics] = {}
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 5
        self.retry_backoff = 2
        
        logger.info(f"{platform.value.title()} client initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load platform configuration"""
        if self.config_path is None:
            config_path = self._get_default_config_path()
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config not found at {config_path}, using defaults")
            return self._get_default_config()
    
    def _get_default_config_path(self) -> str:
        """Get default config path for this platform"""
        base_path = os.getenv("SOCIAL_CONFIG_PATH", "/workspace/waifugen_system/config")
        return f"{base_path}/social/{self.platform.value}_config.json"
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "platform": self.platform.value,
            "rate_limit_rpm": 60,
            "burst_limit": 10,
            "max_video_size_mb": 500,
            "supported_formats": ["mp4", "mov"],
            "max_duration_seconds": 180,
            "min_duration_seconds": 3
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=300, connect=30, sock_read=60)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def _make_request(
        self,
        method: str,
        url: str,
        data: Dict = None,
        files: Dict = None,
        headers: Dict = None
    ) -> Dict[str, Any]:
        """Make an API request with error handling"""
        
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        session = await self._get_session()
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        logger.debug(f"Making {method} request to {url}")
        
        try:
            if method.upper() == "GET":
                async with session.get(url, params=data, headers=request_headers) as response:
                    return await self._handle_response(response)
            elif method.upper() == "POST":
                if files:
                    form = aiohttp.FormData()
                    for key, value in files.items():
                        form.add_field(key, value)
                    if data:
                        for key, value in data.items():
                            form.add_field(key, str(value))
                    async with session.post(url, data=form, headers=request_headers) as response:
                        return await self._handle_response(response)
                else:
                    async with session.post(url, json=data, headers=request_headers) as response:
                        return await self._handle_response(response)
            elif method.upper() == "DELETE":
                async with session.delete(url, json=data, headers=request_headers) as response:
                    return await self._handle_response(response)
            else:
                raise SocialMediaError(f"Unsupported HTTP method: {method}", self.platform)
        
        except aiohttp.ClientError as e:
            raise SocialMediaError(
                f"Network error: {str(e)}",
                self.platform,
                error_code="NETWORK_ERROR",
                retryable=True
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for requests"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Client-Version": "2.0.0",
            "X-Platform": "elite-8-system"
        }
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle API response and raise appropriate errors"""
        status = response.status
        
        try:
            data = await response.json()
        except Exception:
            data = {"message": await response.text()}
        
        if 200 <= status < 300:
            return data
        elif status == 400:
            raise SocialMediaError(
                data.get("message", "Invalid request"),
                self.platform,
                error_code="INVALID_REQUEST",
                retryable=False
            )
        elif status == 401:
            raise SocialMediaError(
                "Authentication failed. Check your credentials.",
                self.platform,
                error_code="UNAUTHORIZED",
                retryable=False
            )
        elif status == 403:
            raise SocialMediaError(
                "Access forbidden. Check your permissions.",
                self.platform,
                error_code="FORBIDDEN",
                retryable=False
            )
        elif status == 429:
            raise SocialMediaError(
                "Rate limit exceeded. Please slow down.",
                self.platform,
                error_code="RATE_LIMITED",
                retryable=True
            )
        elif status >= 500:
            raise SocialMediaError(
                data.get("message", "Server error"),
                self.platform,
                error_code="SERVER_ERROR",
                retryable=True
            )
        else:
            raise SocialMediaError(
                data.get("message", f"Unknown error (status {status})"),
                self.platform,
                error_code="UNKNOWN",
                retryable=status >= 500
            )
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute a function with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except SocialMediaError as e:
                last_exception = e
                if not e.retryable:
                    raise
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (self.retry_backoff ** attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e.message}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed: {e.message}")
                    raise
    
    def _validate_media(self, asset: MediaAsset) -> bool:
        """Validate media asset for posting"""
        # Check file exists
        if not os.path.exists(asset.file_path):
            raise SocialMediaError(
                f"Media file not found: {asset.file_path}",
                self.platform,
                error_code="FILE_NOT_FOUND"
            )
        
        # Check file size
        max_size_mb = self.config.get("max_video_size_mb", 500)
        file_size_mb = os.path.getsize(asset.file_path) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise SocialMediaError(
                f"File too large: {file_size_mb:.1f}MB > {max_size_mb}MB limit",
                self.platform,
                error_code="FILE_TOO_LARGE"
            )
        
        # Check duration
        if asset.duration_seconds:
            min_duration = self.config.get("min_duration_seconds", 3)
            max_duration = self.config.get("max_duration_seconds", 180)
            if not (min_duration <= asset.duration_seconds <= max_duration):
                raise SocialMediaError(
                    f"Invalid duration: {asset.duration_seconds}s "
                    f"(must be {min_duration}-{max_duration}s)",
                    self.platform,
                    error_code="INVALID_DURATION"
                )
        
        return True
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform"""
        pass
    
    @abstractmethod
    async def upload_video(self, asset: MediaAsset, caption: str, 
                          tags: List[str] = None) -> PostResult:
        """Upload a video to the platform"""
        pass
    
    @abstractmethod
    async def get_post_status(self, post_id: str) -> PostResult:
        """Get the status of a post"""
        pass
    
    @abstractmethod
    async def get_engagement(self, post_id: str) -> EngagementMetrics:
        """Get engagement metrics for a post"""
        pass
    
    @abstractmethod
    async def delete_post(self, post_id: str) -> bool:
        """Delete a post from the platform"""
        pass
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        asyncio.get_event_loop().run_until_complete(self.close())
        return False
    
    def __del__(self):
        """Destructor"""
        if hasattr(self, '_session') and self._session and not self._session.closed:
            asyncio.get_event_loop().run_until_complete(self.close())


class MultiPlatformPoster:
    """
    Orchestrator for posting to multiple social media platforms
    
    This class manages simultaneous posting to TikTok, Instagram, and YouTube
    with unified reporting and error handling.
    """
    
    def __init__(self):
        self.clients: Dict[PlatformType, SocialMediaClient] = {}
        self.post_history: List[PostResult] = []
    
    def add_client(self, client: SocialMediaClient):
        """Add a platform client"""
        self.clients[client.platform] = client
        logger.info(f"Added {client.platform.value} client")
    
    async def post_to_all(
        self,
        asset: MediaAsset,
        caption: str,
        tags: List[str] = None,
        platforms: List[PlatformType] = None
    ) -> Dict[PlatformType, PostResult]:
        """
        Post content to multiple platforms simultaneously
        
        Args:
            asset: Media asset to post
            caption: Caption for the post
            tags: List of tags/labels
            platforms: List of platforms to post to (None = all)
            
        Returns:
            Dictionary of platform -> PostResult
        """
        if platforms is None:
            platforms = list(self.clients.keys())
        
        results = {}
        
        # Post to each platform concurrently
        tasks = []
        for platform in platforms:
            if platform in self.clients:
                client = self.clients[platform]
                tasks.append(self._post_with_client(client, asset, caption, tags))
        
        if tasks:
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for platform, result in zip(platforms, platform_results):
                if isinstance(result, Exception):
                    results[platform] = PostResult(
                        success=False,
                        error_message=str(result),
                        platform=platform
                    )
                else:
                    results[platform] = result
                    self.post_history.append(result)
        
        return results
    
    async def _post_with_client(
        self,
        client: SocialMediaClient,
        asset: MediaAsset,
        caption: str,
        tags: List[str]
    ) -> PostResult:
        """Post to a single client with retry logic"""
        try:
            return await client.upload_video(asset, caption, tags)
        except SocialMediaError as e:
            logger.error(f"Failed to post to {client.platform.value}: {e.message}")
            return PostResult(
                success=False,
                error_message=e.message,
                platform=client.platform
            )
    
    async def get_all_engagement(
        self,
        post_id_map: Dict[PlatformType, str]
    ) -> Dict[PlatformType, EngagementMetrics]:
        """Get engagement metrics from all platforms"""
        results = {}
        
        tasks = []
        for platform, post_id in post_id_map.items():
            if platform in self.clients:
                client = self.clients[platform]
                tasks.append(client.get_engagement(post_id))
        
        if tasks:
            metrics_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            for platform, metrics in zip(post_id_map.keys(), metrics_list):
                if isinstance(metrics, Exception):
                    logger.error(f"Failed to get metrics from {platform}: {metrics}")
                    results[platform] = EngagementMetrics()
                else:
                    results[platform] = metrics
        
        return results
    
    async def close_all(self):
        """Close all client sessions"""
        for client in self.clients.values():
            await client.close()


# Export classes
__all__ = [
    "PlatformType",
    "PostStatus", 
    "PostResult",
    "EngagementMetrics",
    "MediaAsset",
    "SocialMediaError",
    "RateLimiter",
    "SocialMediaClient",
    "MultiPlatformPoster"
]
