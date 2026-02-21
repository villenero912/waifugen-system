"""
Facebook/Meta API Client for Elite 8 AI Video Generation System

Handles Facebook Reels and Page posts via Meta Graph API.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import aiohttp

from .base_client import SocialMediaClient, PlatformType, PostResult, EngagementMetrics, MediaAsset, SocialMediaError

logger = logging.getLogger(__name__)


@dataclass
class FacebookReelConfig:
    """Configuration for Facebook Reel uploads"""
    visibility: str = "EVERYONE"   # EVERYONE, FRIENDS, ONLY_ME
    allow_comments: bool = True
    allow_share: bool = True
    content_tags: List[str] = None


class FacebookClient(SocialMediaClient):
    """
    Facebook/Meta Graph API Client

    Supports:
    - Facebook Reels upload via resumable upload
    - Page posts with video
    - Engagement metrics (likes, comments, shares, views)
    - Hashtag injection in descriptions
    """

    GRAPH_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, config_path: str = None):
        super().__init__(PlatformType.FACEBOOK, config_path)
        self.access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")

        if not self.access_token:
            logger.warning("FACEBOOK_ACCESS_TOKEN no configurado en .env")
        if not self.page_id:
            logger.warning("FACEBOOK_PAGE_ID no configurado en .env")

    async def authenticate(self) -> bool:
        try:
            url = f"{self.GRAPH_URL}/me"
            params = {"access_token": self.access_token, "fields": "id,name"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if "error" in data:
                        logger.error(f"Facebook auth error: {data['error']}")
                        return False
                    logger.info(f"Facebook auth OK: {data.get('name')}")
                    return True
        except Exception as e:
            logger.error(f"Facebook authenticate: {e}")
            return False

    async def upload_video(
        self,
        video_path: str,
        caption: str,
        tags: List[str] = None,
        config: FacebookReelConfig = None
    ) -> PostResult:
        """Upload a Reel to Facebook Page"""
        if not self.access_token or not self.page_id:
            return PostResult(
                success=False,
                error="FACEBOOK_ACCESS_TOKEN o FACEBOOK_PAGE_ID no configurados"
            )

        config = config or FacebookReelConfig()
        video_file = Path(video_path)
        if not video_file.exists():
            return PostResult(success=False, error=f"Video no encontrado: {video_path}")

        tag_str = " ".join(f"#{t.lstrip('#')}" for t in (tags or []))
        description = f"{caption}\n\n{tag_str}".strip()

        try:
            # Step 1: Initialize upload session
            init_url = f"{self.GRAPH_URL}/{self.page_id}/videos"
            file_size = video_file.stat().st_size

            async with aiohttp.ClientSession() as session:
                # Start upload
                init_data = {
                    "upload_phase": "start",
                    "file_size": file_size,
                    "access_token": self.access_token,
                }
                async with session.post(init_url, data=init_data) as resp:
                    init_resp = await resp.json()
                    if "error" in init_resp:
                        return PostResult(success=False, error=str(init_resp["error"]))
                    upload_session_id = init_resp.get("upload_session_id")
                    video_id = init_resp.get("video_id")

                # Transfer video
                with open(video_path, "rb") as vf:
                    video_bytes = vf.read()

                transfer_data = aiohttp.FormData()
                transfer_data.add_field("upload_phase", "transfer")
                transfer_data.add_field("upload_session_id", upload_session_id)
                transfer_data.add_field("access_token", self.access_token)
                transfer_data.add_field("video_file_chunk",
                                        video_bytes,
                                        filename=video_file.name,
                                        content_type="video/mp4")

                async with session.post(init_url, data=transfer_data) as resp:
                    transfer_resp = await resp.json()
                    if "error" in transfer_resp:
                        return PostResult(success=False, error=str(transfer_resp["error"]))

                # Finish upload
                finish_data = {
                    "upload_phase": "finish",
                    "upload_session_id": upload_session_id,
                    "access_token": self.access_token,
                    "description": description,
                    "content_tags": json.dumps(config.content_tags or []),
                }
                async with session.post(init_url, data=finish_data) as resp:
                    finish_resp = await resp.json()
                    if "error" in finish_resp:
                        return PostResult(success=False, error=str(finish_resp["error"]))

            post_url = f"https://www.facebook.com/reel/{video_id}"
            logger.info(f"Facebook Reel publicado: {post_url}")
            return PostResult(
                success=True,
                post_id=video_id,
                post_url=post_url,
                platform=PlatformType.FACEBOOK,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Facebook upload error: {e}")
            return PostResult(success=False, error=str(e))

    async def get_metrics(self, post_id: str) -> EngagementMetrics:
        try:
            url = f"{self.GRAPH_URL}/{post_id}"
            params = {
                "fields": "likes.summary(true),comments.summary(true),shares,views",
                "access_token": self.access_token
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
            return EngagementMetrics(
                likes=data.get("likes", {}).get("summary", {}).get("total_count", 0),
                comments=data.get("comments", {}).get("summary", {}).get("total_count", 0),
                shares=data.get("shares", {}).get("count", 0),
                views=data.get("views", 0),
                platform=PlatformType.FACEBOOK,
                post_id=post_id
            )
        except Exception as e:
            logger.error(f"Facebook metrics error: {e}")
            return EngagementMetrics(platform=PlatformType.FACEBOOK, post_id=post_id)
