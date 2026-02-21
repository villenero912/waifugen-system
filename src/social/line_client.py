"""
LINE API Client for Elite 8 AI Video Generation System

LINE es la plataforma de mensajería dominante en Japón (98M usuarios).
Soporta: LINE Official Account, LINE VOOM (equivalente a TikTok/Reels en JP).
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
class LineVoomConfig:
    """Configuration for LINE VOOM posts"""
    visibility: str = "PUBLIC"   # PUBLIC, FRIEND, PRIVATE
    allow_comment: bool = True
    allow_share: bool = True


class LineClient(SocialMediaClient):
    """
    LINE Official Account + LINE VOOM Client

    LINE VOOM = feed de vídeo corto de LINE (mercado japonés)
    LINE Official Account = canal de broadcast a seguidores

    Características:
    - Subida de vídeo a LINE VOOM (vídeos cortos virales JP)
    - Broadcast messages a seguidores del Official Account
    - Métricas de engagement (likes, comentarios, reposts)
    - Sticker packs y mensajes enriquecidos
    """

    MESSAGING_API = "https://api.line.me/v2/bot"
    VOOM_API = "https://api.line.me/v2/content"

    def __init__(self, config_path: str = None):
        super().__init__(PlatformType.LINE, config_path)
        self.channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        self.channel_secret = os.getenv("LINE_CHANNEL_SECRET")

        if not self.channel_access_token:
            logger.warning("LINE_CHANNEL_ACCESS_TOKEN no configurado en .env")

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.channel_access_token}",
            "Content-Type": "application/json"
        }

    async def authenticate(self) -> bool:
        try:
            url = f"{self.MESSAGING_API}/info"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        logger.info(f"LINE auth OK: {data.get('basicId')}")
                        return True
                    logger.error(f"LINE auth error: {data}")
                    return False
        except Exception as e:
            logger.error(f"LINE authenticate: {e}")
            return False

    async def upload_video(
        self,
        video_path: str,
        caption: str,
        tags: List[str] = None,
        config: LineVoomConfig = None
    ) -> PostResult:
        """
        Subir vídeo a LINE VOOM (feed de vídeo corto JP)
        """
        if not self.channel_access_token:
            return PostResult(
                success=False,
                error="LINE_CHANNEL_ACCESS_TOKEN no configurado"
            )

        config = config or LineVoomConfig()
        video_file = Path(video_path)
        if not video_file.exists():
            return PostResult(success=False, error=f"Video no encontrado: {video_path}")

        tag_str = " ".join(f"#{t.lstrip('#')}" for t in (tags or []))
        description = f"{caption}\n\n{tag_str}".strip()

        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Upload video content
                upload_url = f"{self.VOOM_API}/upload"
                headers_upload = {
                    "Authorization": f"Bearer {self.channel_access_token}",
                    "Content-Type": "video/mp4"
                }
                with open(video_path, "rb") as vf:
                    video_bytes = vf.read()

                async with session.post(upload_url, headers=headers_upload, data=video_bytes) as resp:
                    upload_resp = await resp.json()
                    if resp.status != 200:
                        return PostResult(success=False, error=str(upload_resp))
                    content_id = upload_resp.get("contentId")

                # Step 2: Create VOOM post
                post_url = f"{self.VOOM_API}/posts"
                post_data = {
                    "type": "video",
                    "contentId": content_id,
                    "description": description,
                    "visibility": config.visibility,
                    "allowComment": config.allow_comment,
                    "allowShare": config.allow_share
                }
                async with session.post(post_url, headers=self._headers,
                                        data=json.dumps(post_data)) as resp:
                    post_resp = await resp.json()
                    if resp.status not in [200, 201]:
                        return PostResult(success=False, error=str(post_resp))
                    post_id = post_resp.get("postId", content_id)

            result_url = f"https://voom.line.me/post/{post_id}"
            logger.info(f"LINE VOOM publicado: {result_url}")
            return PostResult(
                success=True,
                post_id=post_id,
                post_url=result_url,
                platform=PlatformType.LINE,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"LINE upload error: {e}")
            return PostResult(success=False, error=str(e))

    async def broadcast_message(self, message: str) -> bool:
        """Enviar broadcast a todos los seguidores del Official Account"""
        try:
            url = f"{self.MESSAGING_API}/message/broadcast"
            payload = {
                "messages": [{"type": "text", "text": message}]
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers,
                                        data=json.dumps(payload)) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"LINE broadcast error: {e}")
            return False

    async def get_metrics(self, post_id: str) -> EngagementMetrics:
        try:
            url = f"{self.VOOM_API}/posts/{post_id}/metrics"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers) as resp:
                    data = await resp.json()
            return EngagementMetrics(
                likes=data.get("likeCount", 0),
                comments=data.get("commentCount", 0),
                shares=data.get("shareCount", 0),
                views=data.get("viewCount", 0),
                platform=PlatformType.LINE,
                post_id=post_id
            )
        except Exception as e:
            logger.error(f"LINE metrics error: {e}")
            return EngagementMetrics(platform=PlatformType.LINE, post_id=post_id)
