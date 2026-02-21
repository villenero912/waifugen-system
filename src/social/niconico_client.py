"""
Niconico Douga Client for Elite 8 AI Video Generation System

Niconico es la plataforma de vídeo más grande de Japón (anime/cultura otaku).
Comunidad altamente comprometida — ideal para contenido anime/VTuber.
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
class NiconicoVideoConfig:
    """Configuration for Niconico video uploads"""
    category: str = "anime"           # anime, game, music, technology, etc.
    channel_id: str = None            # opcional: subir a canal propio
    watch_hidden: bool = False        # ocultar contador de vistas
    allow_comments: bool = True
    tags: List[str] = None            # máx 10 tags en Niconico


class NiconicoClient(SocialMediaClient):
    """
    Niconico Douga API Client

    Características especiales de Niconico:
    - Comentarios flotantes sobre el vídeo (niconico style)
    - Tags comunitarios editables por usuarios
    - Sistema de puntos (mylist, likes)
    - Ideal para anime, VTuber, gaming, cosplay
    """

    API_BASE = "https://nvapi.nicovideo.jp/v1"
    UPLOAD_BASE = "https://upload.nicovideo.jp/v2"

    def __init__(self, config_path: str = None):
        super().__init__(PlatformType.NICONICO, config_path)
        self.client_id = os.getenv("NICONICO_CLIENT_ID")
        self.client_secret = os.getenv("NICONICO_CLIENT_SECRET")
        self.access_token = None
        self.refresh_token = os.getenv("NICONICO_REFRESH_TOKEN")

        if not self.client_id:
            logger.warning("NICONICO_CLIENT_ID no configurado en .env")

    async def authenticate(self) -> bool:
        """OAuth2 PKCE authentication con Niconico"""
        try:
            if self.refresh_token:
                return await self._refresh_access_token()

            # Token de acceso directo si está configurado
            token = os.getenv("NICONICO_ACCESS_TOKEN")
            if token:
                self.access_token = token
                return True

            logger.warning("Niconico: configura NICONICO_ACCESS_TOKEN o NICONICO_REFRESH_TOKEN")
            return False

        except Exception as e:
            logger.error(f"Niconico authenticate: {e}")
            return False

    async def _refresh_access_token(self) -> bool:
        try:
            url = "https://oauth.nicovideo.jp/oauth2/token"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as resp:
                    result = await resp.json()
                    if "access_token" in result:
                        self.access_token = result["access_token"]
                        logger.info("Niconico token renovado")
                        return True
                    logger.error(f"Niconico token refresh error: {result}")
                    return False
        except Exception as e:
            logger.error(f"Niconico refresh: {e}")
            return False

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Frontend-Id": "6",
            "X-Frontend-Version": "0"
        }

    async def upload_video(
        self,
        video_path: str,
        caption: str,
        tags: List[str] = None,
        config: NiconicoVideoConfig = None
    ) -> PostResult:
        """Subir vídeo a Niconico Douga"""
        if not self.access_token:
            if not await self.authenticate():
                return PostResult(
                    success=False,
                    error="Niconico no autenticado — configura NICONICO_ACCESS_TOKEN"
                )

        config = config or NiconicoVideoConfig()
        video_file = Path(video_path)
        if not video_file.exists():
            return PostResult(success=False, error=f"Video no encontrado: {video_path}")

        # Niconico: máximo 10 tags
        all_tags = list(set((tags or []) + (config.tags or [])))[:10]

        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Reservar sesión de upload
                reserve_url = f"{self.UPLOAD_BASE}/videos"
                reserve_payload = {
                    "title": caption[:100],          # máx 100 chars
                    "description": caption,
                    "category": config.category,
                    "tags": all_tags,
                    "watchBroadcast": "public" if not config.watch_hidden else "hidden",
                }
                async with session.post(reserve_url, headers=self._headers,
                                        data=json.dumps(reserve_payload)) as resp:
                    reserve = await resp.json()
                    if resp.status not in [200, 201]:
                        return PostResult(success=False, error=str(reserve))

                    upload_url = reserve.get("data", {}).get("uploadUrl")
                    video_id = reserve.get("data", {}).get("id")

                # Step 2: Subir el fichero de vídeo
                file_size = video_file.stat().st_size
                upload_headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "video/mp4",
                    "Content-Length": str(file_size),
                }
                with open(video_path, "rb") as vf:
                    async with session.put(upload_url, headers=upload_headers,
                                           data=vf) as resp:
                        if resp.status not in [200, 204]:
                            return PostResult(success=False, error=f"Upload failed: {resp.status}")

                # Step 3: Confirmar upload
                confirm_url = f"{self.UPLOAD_BASE}/videos/{video_id}/commit"
                async with session.post(confirm_url, headers=self._headers) as resp:
                    confirm = await resp.json()
                    if resp.status not in [200, 201]:
                        return PostResult(success=False, error=str(confirm))

            watch_url = f"https://www.nicovideo.jp/watch/{video_id}"
            logger.info(f"Niconico publicado: {watch_url}")
            return PostResult(
                success=True,
                post_id=video_id,
                post_url=watch_url,
                platform=PlatformType.NICONICO,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Niconico upload error: {e}")
            return PostResult(success=False, error=str(e))

    async def get_metrics(self, post_id: str) -> EngagementMetrics:
        try:
            url = f"{self.API_BASE}/video/{post_id}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers) as resp:
                    data = await resp.json()
            video = data.get("data", {}).get("video", {})
            counts = video.get("count", {})
            return EngagementMetrics(
                likes=counts.get("like", 0),
                comments=counts.get("comment", 0),
                shares=counts.get("mylist", 0),
                views=counts.get("view", 0),
                platform=PlatformType.NICONICO,
                post_id=post_id
            )
        except Exception as e:
            logger.error(f"Niconico metrics error: {e}")
            return EngagementMetrics(platform=PlatformType.NICONICO, post_id=post_id)
