"""
Sales Connector - WaifuGen Phase 2
====================================
Conecta el pipeline de generación Fase 2 con TODAS las plataformas de venta con API:
  - Gumroad  (venta directa de packs — API REST oficial)
  - Patreon  (suscripción por tiers — API OAuth2 oficial)
  - Fansly   (suscripción + PPV — API REST privada)
  - Fanvue   (plataforma AI-friendly — API REST privada)
  - itch.io  (packs descargables — API REST + Upload API oficial)

Embudos de ingeniería social (nsfw_escalation.json):
  Level 0-2  → SFW/Teaser  → GRATIS    (adquisición TikTok/IG → Telegram/LINE)
  Level 4    → Softcore    → $9.99/mes  | Pack Gumroad $15  | Fansly basic
  Level 6    → Mid-NSFW   → $24.99/mes | Pack Gumroad $25  | Fanvue premium
  Level 8    → Explicit    → $49.99/mes | Pack Gumroad $40  | Fansly VIP
  Level 10   → Custom/PPV → $50-$500   | itch.io PPV       | DM directo

Seguridad:
  • Todas las llamadas API pasan por ProxyManager (IP Residencial IPRoyal)
  • Fallback automático a conexión directa si el presupuesto de proxy se agota
  • El proxy se selecciona por país según la plataforma de destino

Author: WaifuGen System
Version: 2.1.0
"""

import os
import json
import logging
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger("SalesConnector")

# Importar ProxyManager para enrutar todas las llamadas API
try:
    import sys
    _proj_root = Path(os.getenv("PROJECT_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
    if str(_proj_root / "src") not in sys.path:
        sys.path.insert(0, str(_proj_root / "src"))
    from social.proxy_manager import ProxyManager
    _proxy_manager = ProxyManager()
    logger.info("ProxyManager cargado: todas las llamadas API irán por proxy residencial.")
except Exception as _e:
    logger.warning(f"⚠️  ProxyManager no disponible ({_e}). Usando conexión directa.")
    _proxy_manager = None


def _make_session(country: Optional[str] = None) -> aiohttp.ClientSession:
    """
    Crea una sesión aiohttp enrutada por el ProxyManager.
    Si el proxy no está disponible o el presupuesto está agotado,
    devuelve una sesión directa.

    Args:
        country: Código ISO del país para IP residencial (ej: 'US', 'JP')
    """
    if _proxy_manager:
        can_use, reason = _proxy_manager.can_use_proxy()
        if can_use:
            proxy_url = _proxy_manager.get_proxy_url(country=country)
            connector = aiohttp.TCPConnector(ssl=False)
            # aiohttp pasa el proxy en cada request, no en el conector
            session = aiohttp.ClientSession(connector=connector)
            session._default_proxy = proxy_url   # type: ignore[attr-defined]
            logger.debug(f"Sesión proxy {country or 'global'}: {proxy_url[:30]}...")
            return session
        else:
            logger.info(f"Proxy no disponible ({reason}). Usando conexión directa.")
    return aiohttp.ClientSession()


# ─────────────────────────────────────────────────────────
# CONFIGURACIÓN: PRECIOS POR NIVEL (embudos de escalada)
# ─────────────────────────────────────────────────────────

LEVEL_PRICING: Dict[int, Dict[str, Any]] = {
    0: {
        "label": "SFW Free",
        "pack_price_usd": 0.0,
        "monthly_usd": 0.0,
        "patreon_tier": "public",
        "strategy": "awareness",      # Etapa del embudo
        "cta": "Sigue la cuenta para más contenido gratuito 🎵",
        "funnel_goal": "awareness_and_growth",
    },
    2: {
        "label": "Teaser",
        "pack_price_usd": 0.0,
        "monthly_usd": 0.0,
        "patreon_tier": "public",
        "strategy": "interest",
        "cta": "🔞 Ver preview exclusivo → [link Patreon]",
        "funnel_goal": "line_community_building",
    },
    4: {
        "label": "Softcore – Basic",
        "pack_price_usd": 15.0,
        "monthly_usd": 9.99,
        "patreon_tier": "basic_nsfw",
        "gumroad_product_prefix": "pack_basic",
        "strategy": "consideration",
        "cta": "💕 Accede al pack completo $15 → [link Gumroad]",
        "funnel_goal": "onlyfans_basic_conversions",
    },
    6: {
        "label": "Mid-NSFW – Premium",
        "pack_price_usd": 25.0,
        "monthly_usd": 24.99,
        "patreon_tier": "premium_nsfw",
        "gumroad_product_prefix": "pack_premium",
        "strategy": "intent",
        "cta": "🔥 Pack Premium $25 – acceso VIP → [link Gumroad]",
        "funnel_goal": "premium_tier_upsells",
    },
    8: {
        "label": "Explicit – VIP",
        "pack_price_usd": 40.0,
        "monthly_usd": 49.99,
        "patreon_tier": "vip_nsfw",
        "gumroad_product_prefix": "pack_vip",
        "strategy": "purchase",
        "cta": "⭐ Colección VIP completa $40 → [link Gumroad]",
        "funnel_goal": "vip_tier_and_ppv",
    },
    10: {
        "label": "Custom / PPV",
        "pack_price_usd": 99.0,   # Precio base; se negocia en DM
        "monthly_usd": 0.0,
        "patreon_tier": "vip_nsfw",
        "gumroad_product_prefix": "pack_custom",
        "strategy": "loyalty",
        "cta": "🎯 Solicita contenido personalizado → DM directo",
        "funnel_goal": "custom_ppv_revenue",
        "ppv_range": [50, 500],
    },
}

# ─────────────────────────────────────────────────────────
# HELPER: Cargar datos de personaje desde blueprint
# ─────────────────────────────────────────────────────────

def _load_character_data(character_id: str) -> Dict[str, Any]:
    """Carga datos del personaje desde el Blueprint de Fase 2."""
    blueprint_path = (
        Path(os.getenv("PROJECT_ROOT", ".")) / "config/phase2/ELITE8_ADULT_BLUEPRINT.json"
    )
    if blueprint_path.exists():
        with open(blueprint_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for char in data.get("blueprint", []):
            if char["id"] == character_id:
                return char
    return {"id": character_id, "name": character_id.replace("_", " ").title()}


# ═══════════════════════════════════════════════════════════
#  GUMROAD CONNECTOR
# ═══════════════════════════════════════════════════════════

class GumroadConnector:
    """
    Conecta el pipeline Fase 2 con la API de Gumroad.

    Flujo:
      1. create_product()     → crea el producto en Gumroad
      2. attach_file()        → adjunta el video MP4
      3. publish_product()    → lo hace visible al público
      4. get_sales_stats()    → monitorea ventas

    Requiere: GUMROAD_ACCESS_TOKEN en variables de entorno.
    """

    BASE_URL = "https://api.gumroad.com/v2"

    def __init__(self, access_token: Optional[str] = None):
        self.token = access_token or os.getenv("GUMROAD_ACCESS_TOKEN")
        if not self.token:
            logger.warning("⚠️  GUMROAD_ACCESS_TOKEN no configurado.")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Sesión con proxy residencial US (mercado principal de Gumroad)."""
        if not self._session or self._session.closed:
            self._session = _make_session(country="US")
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ── Verificación de credenciales ──────────────────────
    async def verify_credentials(self) -> Dict[str, Any]:
        """Valida el token y devuelve el perfil del usuario."""
        session = await self._get_session()
        params = {"access_token": self.token}
        async with session.get(f"{self.BASE_URL}/user", params=params) as resp:
            data = await resp.json()
            if data.get("success"):
                user = data["user"]
                logger.info(f"✅ Gumroad OK: {user.get('name')} | Email: {user.get('email')}")
                return {"ok": True, "user": user}
            else:
                logger.error(f"❌ Gumroad auth error: {data}")
                return {"ok": False, "error": data}

    # ── Crear producto ────────────────────────────────────
    async def create_product(
        self,
        character_id: str,
        nsfw_level: int,
        description: str = "",
        custom_price: Optional[float] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Crea un nuevo producto en Gumroad para el personaje+nivel indicados.

        Args:
            character_id: ID del personaje (ej: 'aiko_hayashi')
            nsfw_level:   Nivel de contenido (4, 6, 8, 10)
            description:  Descripción adicional del producto
            custom_price: Precio personalizado (override del nivel)
            dry_run:      Si True, simula sin llamar a la API real

        Returns:
            Dict con product_id, permalink, y datos del producto.
        """
        pricing = LEVEL_PRICING.get(nsfw_level, LEVEL_PRICING[4])
        char = _load_character_data(character_id)
        price = custom_price or pricing["pack_price_usd"]
        
        name = f"{char['name']} — {pricing['label']} Pack"
        desc_blocks = [
            f"🎭 Personaje: **{char['name']}**",
            f"📦 Colección {pricing['label']}",
            f"🔞 Contenido adulto — Solo para mayores de 18.",
            f"📲 Acceso inmediato tras la compra.",
            "",
            description or char.get("romantic_style", ""),
            "",
            "✅ Formato: MP4 4K | Audio HQ | LipSync",
            pricing["cta"],
        ]
        full_desc = "\n".join(desc_blocks)

        payload = {
            "access_token": self.token,
            "name": name,
            "price": int(price * 100),   # Gumroad usa centavos
            "description": full_desc,
            "published": "false",        # Se publica en paso separado
            "require_shipping": "false",
            "is_digital": "true",
            "adult_content_rating": "adult",
        }

        if dry_run:
            logger.info(f"[DRY-RUN] Gumroad create_product: {name} @ ${price}")
            return {
                "ok": True,
                "dry_run": True,
                "product": {"name": name, "price_usd": price, "character": character_id, "level": nsfw_level},
            }

        session = await self._get_session()
        async with session.post(f"{self.BASE_URL}/products", data=payload) as resp:
            data = await resp.json()
            if data.get("success"):
                product = data["product"]
                logger.info(f"✅ Producto creado: {product['name']} | ID: {product['id']}")
                return {"ok": True, "product": product, "product_id": product["id"]}
            else:
                logger.error(f"❌ Error creando producto: {data}")
                return {"ok": False, "error": data}

    # ── Adjuntar archivo ──────────────────────────────────
    async def attach_file(
        self,
        product_id: str,
        file_path: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Adjunta el archivo de video al producto existente.

        Args:
            product_id: ID del producto en Gumroad
            file_path:  Ruta local al archivo MP4
            dry_run:    Si True, simula sin subir
        """
        video = Path(file_path)
        if not video.exists():
            logger.warning(f"⚠️  Archivo no encontrado: {file_path}")
            return {"ok": False, "error": "file_not_found"}

        if dry_run:
            logger.info(f"[DRY-RUN] Adjuntando {video.name} → producto {product_id}")
            return {"ok": True, "dry_run": True, "file": str(video)}

        session = await self._get_session()
        with open(file_path, "rb") as f:
            form = aiohttp.FormData()
            form.add_field("access_token", self.token)
            form.add_field("file", f, filename=video.name, content_type="video/mp4")

            async with session.post(
                f"{self.BASE_URL}/products/{product_id}/product_files", data=form
            ) as resp:
                data = await resp.json()
                if data.get("success"):
                    logger.info(f"✅ Archivo adjuntado: {video.name}")
                    return {"ok": True, "file_data": data.get("product_file")}
                else:
                    logger.error(f"❌ Error adjuntando archivo: {data}")
                    return {"ok": False, "error": data}

    # ── Publicar producto ─────────────────────────────────
    async def publish_product(
        self, product_id: str, dry_run: bool = False
    ) -> Dict[str, Any]:
        """Publica el producto haciéndolo visible al público."""
        if dry_run:
            logger.info(f"[DRY-RUN] Publicando producto {product_id}")
            return {"ok": True, "dry_run": True}

        session = await self._get_session()
        payload = {"access_token": self.token, "published": "true"}
        async with session.put(f"{self.BASE_URL}/products/{product_id}", data=payload) as resp:
            data = await resp.json()
            if data.get("success"):
                product = data["product"]
                logger.info(f"🚀 Producto publicado: {product.get('short_url')}")
                return {"ok": True, "url": product.get("short_url"), "product": product}
            else:
                logger.error(f"❌ Error publicando: {data}")
                return {"ok": False, "error": data}

    # ── Estadísticas ──────────────────────────────────────
    async def get_sales_stats(self, product_id: str) -> Dict[str, Any]:
        """Devuelve estadísticas de ventas del producto."""
        session = await self._get_session()
        params = {"access_token": self.token, "product_id": product_id}
        async with session.get(f"{self.BASE_URL}/sales", params=params) as resp:
            data = await resp.json()
            if data.get("success"):
                sales = data.get("sales", [])
                total = sum(s.get("price", 0) for s in sales) / 100
                return {"ok": True, "total_sales": len(sales), "total_revenue_usd": round(total, 2)}
            return {"ok": False, "error": data}

    # ── Flujo completo ────────────────────────────────────
    async def publish_full_pack(
        self,
        character_id: str,
        nsfw_level: int,
        video_path: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Flujo completo: crea producto → adjunta video → publica.
        Integra lógica de embudos para CTA y pricing.
        """
        logger.info(f"📦 Iniciando publicación Gumroad: {character_id} Lv{nsfw_level}")

        # 1. Crear producto
        result = await self.create_product(character_id, nsfw_level, dry_run=dry_run)
        if not result["ok"]:
            return result
        product_id = result.get("product_id", "DRY_RUN_ID")

        # 2. Adjuntar video
        file_result = await self.attach_file(product_id, video_path, dry_run=dry_run)
        if not file_result["ok"] and not dry_run:
            return file_result

        # 3. Publicar
        pub_result = await self.publish_product(product_id, dry_run=dry_run)

        # 4. Registrar en manifiesto local
        manifest = {
            "platform": "gumroad",
            "character": character_id,
            "nsfw_level": nsfw_level,
            "product_id": product_id,
            "video_path": video_path,
            "price_usd": LEVEL_PRICING.get(nsfw_level, {}).get("pack_price_usd"),
            "funnel_stage": LEVEL_PRICING.get(nsfw_level, {}).get("strategy"),
            "published_at": datetime.utcnow().isoformat(),
            "url": pub_result.get("url"),
            "dry_run": dry_run,
        }

        out_dir = Path(os.getenv("PROJECT_ROOT", ".")) / "output/phase2/sales"
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = out_dir / f"{character_id}_lv{nsfw_level}_gumroad.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"✅ Gumroad publish_full_pack completado. Manifiesto: {manifest_path}")
        return manifest


# ═══════════════════════════════════════════════════════════
#  PATREON CONNECTOR
# ═══════════════════════════════════════════════════════════

class PatreonConnector:
    """
    Conecta el pipeline Fase 2 con la API v2 de Patreon.

    Flujo de embudos:
      Level 4 → tier "basic_nsfw"   ($9.99/mes)
      Level 6 → tier "premium_nsfw" ($24.99/mes)
      Level 8 → tier "vip_nsfw"     ($49.99/mes)
      Level 10→ tier "vip_nsfw"     (PPV via DM)

    Requiere:
      PATREON_ACCESS_TOKEN  → token del creador (OAuth2)
      PATREON_CAMPAIGN_ID   → ID de la campaña
    """

    BASE_URL = "https://www.patreon.com/api/oauth2/v2"

    def __init__(
        self,
        access_token: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ):
        self.token = access_token or os.getenv("PATREON_ACCESS_TOKEN")
        self.campaign_id = campaign_id or os.getenv("PATREON_CAMPAIGN_ID")
        if not self.token:
            logger.warning("⚠️  PATREON_ACCESS_TOKEN no configurado.")
        self._session: Optional[aiohttp.ClientSession] = None

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Sesión con proxy residencial US (API de Patreon no requiere geo-targeting)."""
        if not self._session or self._session.closed:
            self._session = _make_session(country="US")
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ── Verificación ──────────────────────────────────────
    async def verify_credentials(self) -> Dict[str, Any]:
        """Valida el token devolviendo datos del creador."""
        session = await self._get_session()
        async with session.get(
            f"{self.BASE_URL}/identity",
            headers=self._headers(),
            params={"fields[user]": "full_name,email,url"},
        ) as resp:
            data = await resp.json()
            if "data" in data:
                attrs = data["data"].get("attributes", {})
                logger.info(f"✅ Patreon OK: {attrs.get('full_name')} | {attrs.get('email')}")
                return {"ok": True, "creator": attrs}
            logger.error(f"❌ Patreon auth error: {data}")
            return {"ok": False, "error": data}

    # ── Obtener tiers ─────────────────────────────────────
    async def get_campaign_tiers(self) -> List[Dict[str, Any]]:
        """Devuelve los tiers actuales de la campaña."""
        session = await self._get_session()
        async with session.get(
            f"{self.BASE_URL}/campaigns/{self.campaign_id}",
            headers=self._headers(),
            params={
                "include": "tiers",
                "fields[tier]": "title,amount_cents,patron_count",
            },
        ) as resp:
            data = await resp.json()
            tiers = []
            for item in data.get("included", []):
                if item.get("type") == "tier":
                    a = item["attributes"]
                    tiers.append({
                        "id": item["id"],
                        "title": a.get("title"),
                        "price_usd": a.get("amount_cents", 0) / 100,
                        "patrons": a.get("patron_count", 0),
                    })
            return tiers

    # ── Crear post ────────────────────────────────────────
    async def create_post(
        self,
        character_id: str,
        nsfw_level: int,
        title: str = "",
        body: str = "",
        tier_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Crea un post en Patreon restringido al tier correspondiente al nivel.

        Args:
            character_id: ID del personaje
            nsfw_level:   Nivel de contenido (4, 6, 8, 10)
            title:        Título del post (se genera automáticamente si vacío)
            body:         Cuerpo del post
            tier_id:      ID del tier en Patreon (si None, usa el mapping de nivel)
            dry_run:      Si True, simula sin publicar
        """
        pricing = LEVEL_PRICING.get(nsfw_level, LEVEL_PRICING[4])
        char = _load_character_data(character_id)

        auto_title = title or f"[{pricing['label']}] {char['name']} — Colección {datetime.utcnow().strftime('%B %Y')}"
        auto_body = body or (
            f"✨ Nueva colección {pricing['label']} disponible para este tier.\n\n"
            f"🎭 {char.get('romantic_style', '')}\n\n"
            f"📦 Contenido incluido:\n"
            f"• Video 4K LipSync\n"
            f"• Photoset exclusivo\n\n"
            f"🔞 +18 | Personaje ficticio generado por AI.\n\n"
            f"{pricing['cta']}"
        )

        if dry_run:
            logger.info(f"[DRY-RUN] Patreon create_post: '{auto_title}' | Tier: {pricing['patreon_tier']}")
            return {
                "ok": True,
                "dry_run": True,
                "post": {"title": auto_title, "tier": pricing["patreon_tier"], "character": character_id},
            }

        # Construir payload JSON:API
        post_data: Dict[str, Any] = {
            "data": {
                "type": "post",
                "attributes": {
                    "title": auto_title,
                    "content": auto_body,
                    "is_paid": True,
                    "is_public": nsfw_level <= 2,      # Solo SFW es público
                    "content_type": "video_embed",
                    "teaser_text": pricing["cta"],
                },
                "relationships": {
                    "campaign": {
                        "data": {"type": "campaign", "id": self.campaign_id}
                    }
                },
            }
        }

        # Agregar restricción de tier si se especifica
        if tier_id:
            post_data["data"]["relationships"]["tiers"] = {
                "data": [{"type": "tier", "id": tier_id}]
            }

        session = await self._get_session()
        async with session.post(
            f"{self.BASE_URL}/posts",
            headers=self._headers(),
            json=post_data,
        ) as resp:
            result = await resp.json()
            if "data" in result:
                post_id = result["data"]["id"]
                attrs = result["data"].get("attributes", {})
                logger.info(f"✅ Post Patreon creado: {auto_title} | ID: {post_id}")
                return {"ok": True, "post_id": post_id, "url": attrs.get("url")}
            else:
                logger.error(f"❌ Error creando post Patreon: {result}")
                return {"ok": False, "error": result}

    # ── Estadísticas ──────────────────────────────────────
    async def get_patron_count(self, tier_level: int) -> Dict[str, Any]:
        """Devuelve el número de suscriptores para el tier del nivel dado."""
        tiers = await self.get_campaign_tiers()
        tier_name = LEVEL_PRICING.get(tier_level, {}).get("patreon_tier", "")
        for tier in tiers:
            if tier_name.lower() in tier.get("title", "").lower():
                return {"ok": True, "tier": tier}
        return {"ok": True, "tiers": tiers, "note": "Mapear tier_id manualmente en .env"}


# ═══════════════════════════════════════════════════════════
#  FANSLY CONNECTOR
# ═══════════════════════════════════════════════════════════

class FanslyConnector:
    """
    Conecta el pipeline Fase 2 con la API privada de Fansly.

    Fansly no tiene API pública documentada, pero acepta llamadas REST
    autenticadas con el token de sesión del creador.

    Posición en el embudo:
      Level 4 → plan básico ($9.99/mes)
      Level 8 → plan VIP ($49.99/mes)
      Level 10→ PPV por mensaje

    Requiere:
      FANSLY_AUTH_TOKEN  → token de sesión (de las cookies/headers del navegador)
    """

    BASE_URL = "https://apiv3.fansly.com/api/v1"

    def __init__(self, auth_token: Optional[str] = None):
        self.token = auth_token or os.getenv("FANSLY_AUTH_TOKEN")
        if not self.token:
            logger.warning("⚠️  FANSLY_AUTH_TOKEN no configurado.")
        self._session: Optional[aiohttp.ClientSession] = None

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.token or "",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Fansly requiere IP residencial US para evitar bloqueos."""
        if not self._session or self._session.closed:
            self._session = _make_session(country="US")
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def verify_credentials(self) -> Dict[str, Any]:
        """Verifica el token devolviendo el perfil del creador."""
        session = await self._get_session()
        async with session.get(
            f"{self.BASE_URL}/account/me", headers=self._headers()
        ) as resp:
            data = await resp.json()
            if data.get("success") and data.get("response"):
                acc = data["response"]
                logger.info(f"✅ Fansly OK: @{acc.get('username')}")
                return {"ok": True, "account": acc}
            logger.error(f"❌ Fansly auth error: {data}")
            return {"ok": False, "error": data}

    async def create_post(
        self,
        character_id: str,
        nsfw_level: int,
        video_path: str,
        price_usd: float = 0.0,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Crea un post en Fansly (gratuito para suscriptores o PPV).

        Args:
            character_id: ID del personaje
            nsfw_level:   Nivel NSFW (4/8/10)
            video_path:   Ruta al archivo de video
            price_usd:    Si > 0, se publica como PPV
            dry_run:      Simula sin publicar
        """
        pricing = LEVEL_PRICING.get(nsfw_level, LEVEL_PRICING[4])
        char = _load_character_data(character_id)
        caption = (
            f"🎭 {char['name']} — {pricing['label']}\n"
            f"🔞 +18 | AI Generated | 4K Quality\n"
            f"{pricing['cta']}"
        )
        ppv_price = int(price_usd * 100) if price_usd > 0 else 0  # centavos

        if dry_run:
            logger.info(f"[DRY-RUN] Fansly post: {char['name']} Lv{nsfw_level} | PPV=${price_usd}")
            return {
                "ok": True, "dry_run": True,
                "post": {"caption": caption, "ppv": ppv_price, "character": character_id}
            }

        # Primero subir el media
        session = await self._get_session()
        video = Path(video_path)
        if not video.exists():
            return {"ok": False, "error": "file_not_found"}

        # Upload del archivo
        form = aiohttp.FormData()
        form.add_field("file", open(video_path, "rb"), filename=video.name, content_type="video/mp4")
        async with session.post(
            f"{self.BASE_URL}/media/upload", headers={"Authorization": self.token}, data=form
        ) as resp:
            upload_data = await resp.json()

        media_id = upload_data.get("response", {}).get("id")
        if not media_id:
            return {"ok": False, "error": f"Upload failed: {upload_data}"}

        # Crear el post
        payload = {
            "content": caption,
            "attachments": [{"contentId": media_id, "contentType": 2}],
            "price": ppv_price,  # 0 = gratis para suscriptores, >0 = PPV
            "postRestriction": 2 if nsfw_level >= 8 else 1,  # 1=basic, 2=VIP
        }
        async with session.post(
            f"{self.BASE_URL}/post", headers=self._headers(), json=payload
        ) as resp:
            result = await resp.json()
            if result.get("success"):
                post_id = result.get("response", {}).get("id")
                logger.info(f"✅ Fansly post creado: {char['name']} | ID: {post_id}")
                return {"ok": True, "post_id": post_id}
            logger.error(f"❌ Error Fansly: {result}")
            return {"ok": False, "error": result}


# ═══════════════════════════════════════════════════════════
#  FANVUE CONNECTOR
# ═══════════════════════════════════════════════════════════

class FanvueConnector:
    """
    Conecta el pipeline Fase 2 con la API de Fanvue.

    Fanvue es especialmente permisiva con contenido AI-generated.
    Su API REST privada acepta tokens de creador.

    Posición en el embudo:
      Level 4-6 → suscripción base/premium
      Level 8   → tier VIP
      Level 10  → vault PPV exclusivo

    Requiere:
      FANVUE_API_KEY   → API key del creador
    """

    BASE_URL = "https://www.fanvue.com/api"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FANVUE_API_KEY")
        if not self.api_key:
            logger.warning("⚠️  FANVUE_API_KEY no configurado.")
        self._session: Optional[aiohttp.ClientSession] = None

    def _headers(self) -> Dict[str, str]:
        return {
            "x-fanvue-api-key": self.api_key or "",
            "Content-Type": "application/json",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Fanvue usa IPs US por defecto; sin geo-restricción estricta."""
        if not self._session or self._session.closed:
            self._session = _make_session(country="US")
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def verify_credentials(self) -> Dict[str, Any]:
        """Verifica la API key devolviendo el perfil del creador."""
        session = await self._get_session()
        async with session.get(
            f"{self.BASE_URL}/creator/profile", headers=self._headers()
        ) as resp:
            data = await resp.json()
            if "username" in data:
                logger.info(f"✅ Fanvue OK: @{data.get('username')}")
                return {"ok": True, "profile": data}
            logger.error(f"❌ Fanvue auth error: {data}")
            return {"ok": False, "error": data}

    async def create_post(
        self,
        character_id: str,
        nsfw_level: int,
        video_path: str,
        is_ppv: bool = False,
        ppv_price_usd: float = 0.0,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Crea un post en Fanvue para suscriptores o como PPV (vault).

        Args:
            character_id:  ID del personaje
            nsfw_level:    Nivel NSFW
            video_path:    Ruta al video
            is_ppv:        Si True, va al vault de pago
            ppv_price_usd: Precio del PPV
            dry_run:       Simula sin publicar
        """
        pricing = LEVEL_PRICING.get(nsfw_level, LEVEL_PRICING[4])
        char = _load_character_data(character_id)
        caption = (
            f"{char['name']} | {pricing['label']} 🔞\n"
            f"AI-Generated 4K | +18 Only\n"
            f"{pricing['cta']}"
        )

        if dry_run:
            logger.info(f"[DRY-RUN] Fanvue post: {char['name']} Lv{nsfw_level} | PPV={is_ppv}")
            return {
                "ok": True, "dry_run": True,
                "post": {"caption": caption, "is_ppv": is_ppv, "ppv_price": ppv_price_usd}
            }

        session = await self._get_session()
        video = Path(video_path)
        if not video.exists():
            return {"ok": False, "error": "file_not_found"}

        # Subir media
        form = aiohttp.FormData()
        form.add_field("file", open(video_path, "rb"), filename=video.name, content_type="video/mp4")
        async with session.post(
            f"{self.BASE_URL}/media/upload", headers=self._headers(), data=form
        ) as resp:
            upload_data = await resp.json()

        media_id = upload_data.get("mediaId")
        if not media_id:
            return {"ok": False, "error": f"Upload failed: {upload_data}"}

        # Crear el post
        payload = {
            "caption": caption,
            "mediaIds": [media_id],
            "isVault": is_ppv or nsfw_level >= 10,
            "vaultPrice": int(ppv_price_usd * 100) if is_ppv else 0,
            "accessTier": (
                "vip" if nsfw_level >= 8
                else "premium" if nsfw_level >= 6
                else "basic"
            ),
        }
        async with session.post(
            f"{self.BASE_URL}/posts", headers=self._headers(), json=payload
        ) as resp:
            result = await resp.json()
            if "postId" in result:
                logger.info(f"✅ Fanvue post creado: {char['name']} | ID: {result['postId']}")
                return {"ok": True, "post_id": result["postId"]}
            logger.error(f"❌ Error Fanvue: {result}")
            return {"ok": False, "error": result}


# ═══════════════════════════════════════════════════════════
#  ITCH.IO CONNECTOR
# ═══════════════════════════════════════════════════════════

class ItchioConnector:
    """
    Conecta el pipeline Fase 2 con la API oficial de itch.io.

    itch.io tiene API REST pública para crear y gestionar juegos/proyectos
    y una Upload API para adjuntar archivos descargables.

    Útil para packs level_10 (custom/PPV) como contenido descargable.

    Posición en el embudo:
      Level 10 → pack PPV empaquetado (.zip con MP4 + extras)
      Level 8  → pack VIP como descargable de pago

    Requiere:
      ITCHIO_API_KEY  → API key del creador (en itch.io > Settings > API)
    """

    BASE_URL = "https://itch.io/api/1"
    UPLOAD_URL = "https://upload.itch.io"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ITCHIO_API_KEY")
        if not self.api_key:
            logger.warning("⚠️  ITCHIO_API_KEY no configurado.")
        self._session: Optional[aiohttp.ClientSession] = None

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def _get_session(self) -> aiohttp.ClientSession:
        """itch.io API no tiene geo-restricciones, pero el proxy protege la IP."""
        if not self._session or self._session.closed:
            self._session = _make_session(country="US")
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def verify_credentials(self) -> Dict[str, Any]:
        """Verifica la API key devolviendo el perfil del usuario."""
        session = await self._get_session()
        async with session.get(
            f"{self.BASE_URL}/{self.api_key}/me"
        ) as resp:
            data = await resp.json()
            if "user" in data:
                user = data["user"]
                logger.info(f"✅ itch.io OK: {user.get('username')}")
                return {"ok": True, "user": user}
            logger.error(f"❌ itch.io auth error: {data}")
            return {"ok": False, "error": data}

    async def create_game(
        self,
        character_id: str,
        nsfw_level: int,
        custom_price: Optional[float] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Crea un 'game' (proyecto) en itch.io para el pack del personaje.
        En itch.io los contenidos descargables se crean como proyectos tipo 'other'.

        Args:
            character_id: ID del personaje
            nsfw_level:   Nivel NSFW
            custom_price: Precio override (si None usa LEVEL_PRICING)
            dry_run:      Simula sin crear
        """
        pricing = LEVEL_PRICING.get(nsfw_level, LEVEL_PRICING[4])
        char = _load_character_data(character_id)
        price = custom_price or pricing["pack_price_usd"]
        slug = f"{character_id.replace('_', '-')}-lv{nsfw_level}-pack"
        title = f"{char['name']} — {pricing['label']} Pack"
        desc = (
            f"<p>🎭 <strong>{char['name']}</strong> | {pricing['label']}</p>"
            f"<p>🔞 +18 | AI-Generated | 4K MP4</p>"
            f"<p>{char.get('romantic_style', '')}</p>"
            f"<p>{pricing['cta']}</p>"
        )

        if dry_run:
            logger.info(f"[DRY-RUN] itch.io create_game: {title} @ ${price}")
            return {
                "ok": True, "dry_run": True,
                "game": {"title": title, "slug": slug, "price_usd": price}
            }

        session = await self._get_session()
        payload = {
            "title": title,
            "short_description": f"{char['name']} AI-generated adult content pack",
            "description": desc,
            "classification": "other",
            "type": "downloadable",
            "min_price": int(price * 100),  # itch.io usa centavos
            "url": slug,
            "visibility": "restricted",
            "age_requirement": "adult",
        }
        async with session.post(
            f"{self.BASE_URL}/{self.api_key}/games",
            data=payload
        ) as resp:
            data = await resp.json()
            if "id" in data:
                logger.info(f"✅ itch.io game creado: {title} | ID: {data['id']}")
                return {"ok": True, "game_id": data["id"], "url": data.get("url")}
            logger.error(f"❌ Error itch.io: {data}")
            return {"ok": False, "error": data}

    async def upload_file(
        self,
        game_id: str,
        file_path: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Sube el archivo de video/pack al proyecto de itch.io."""
        video = Path(file_path)
        if not video.exists():
            return {"ok": False, "error": "file_not_found"}

        if dry_run:
            logger.info(f"[DRY-RUN] itch.io upload: {video.name} → game {game_id}")
            return {"ok": True, "dry_run": True, "file": str(video)}

        session = await self._get_session()
        form = aiohttp.FormData()
        form.add_field("game_id", str(game_id))
        form.add_field("file", open(file_path, "rb"), filename=video.name, content_type="video/mp4")
        async with session.post(
            f"{self.UPLOAD_URL}/{self.api_key}/upload",
            data=form
        ) as resp:
            data = await resp.json()
            if data.get("status") == "ok":
                logger.info(f"✅ itch.io archivo subido: {video.name}")
                return {"ok": True, "upload_id": data.get("id")}
            logger.error(f"❌ Error subida itch.io: {data}")
            return {"ok": False, "error": data}

    async def publish_pack(
        self,
        character_id: str,
        nsfw_level: int,
        video_path: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Flujo completo: crea juego → sube archivo."""
        result = await self.create_game(character_id, nsfw_level, dry_run=dry_run)
        if not result["ok"]:
            return result
        game_id = result.get("game_id", "DRY_RUN_ID")
        upload_result = await self.upload_file(game_id, video_path, dry_run=dry_run)
        return {"ok": upload_result["ok"], "game_id": game_id, "upload": upload_result}


# ═══════════════════════════════════════════════════════════
#  ORCHESTRATOR: SalesConnector (5 plataformas)
# ═══════════════════════════════════════════════════════════

# Mapa de nivel → plataformas recomendadas (embudo de ingeniería social)
LEVEL_PLATFORM_MAP: Dict[int, List[str]] = {
    0:  [],                                      # Solo redes SFW (no hay venta)
    2:  [],                                      # Teaser gratuito (no hay venta)
    4:  ["gumroad", "patreon", "fansly"],        # Softcore: 3 plataformas
    6:  ["gumroad", "patreon", "fanvue"],        # Mid-NSFW: Fanvue más permisiva
    8:  ["gumroad", "patreon", "fansly", "fanvue"],  # Explicit: máximo alcance
    10: ["gumroad", "itchio", "fansly"],         # Custom/PPV: empaquetado descargable
}


class SalesConnector:
    """
    Orquestador de ventas que integra las 5 plataformas con API:
      Gumroad · Patreon · Fansly · Fanvue · itch.io

    Enruta automáticamente según el nsfw_level del upload_manifest:
      Level 4  → Gumroad + Patreon + Fansly
      Level 6  → Gumroad + Patreon + Fanvue
      Level 8  → Gumroad + Patreon + Fansly + Fanvue
      Level 10 → Gumroad + itch.io + Fansly (PPV)

    Uso:
        connector = SalesConnector()
        await connector.publish_from_manifest("output/phase2/aiko_hayashi/upload_manifest.json")
    """

    def __init__(self):
        self.gumroad = GumroadConnector()
        self.patreon  = PatreonConnector()
        self.fansly   = FanslyConnector()
        self.fanvue   = FanvueConnector()
        self.itchio   = ItchioConnector()

    async def verify_all(self) -> Dict[str, Any]:
        """Verifica credenciales de las 5 plataformas en paralelo."""
        results = await asyncio.gather(
            self.gumroad.verify_credentials(),
            self.patreon.verify_credentials(),
            self.fansly.verify_credentials(),
            self.fanvue.verify_credentials(),
            self.itchio.verify_credentials(),
            return_exceptions=True,
        )
        keys = ["gumroad", "patreon", "fansly", "fanvue", "itchio"]
        return {
            k: (v if not isinstance(v, Exception) else {"ok": False, "error": str(v)})
            for k, v in zip(keys, results)
        }

    async def publish_from_manifest(
        self,
        manifest_path: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Lee el `upload_manifest.json` generado en el Paso 5 del pipeline
        y publica en las plataformas adecuadas según nsfw_level + embudo.

        Embudo completo:
          Level 0-2 → sin venta (sólo redes SFW/Telegram — adquisición)
          Level 4   → Gumroad $15 + Patreon basic + Fansly basic
          Level 6   → Gumroad $25 + Patreon premium + Fanvue premium
          Level 8   → Gumroad $40 + Patreon VIP + Fansly VIP + Fanvue VIP
          Level 10  → Gumroad PPV $99 + itch.io pack + Fansly PPV
        """
        manifest_path_obj = Path(manifest_path)
        if not manifest_path_obj.exists():
            return {"ok": False, "error": f"Manifiesto no encontrado: {manifest_path}"}

        with open(manifest_path_obj, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        character_id = manifest.get("character")
        video_path   = manifest.get("video_file", "")
        nsfw_level   = manifest.get("nsfw_level", 4)
        # Respeta platforms del manifiesto, o usa el mapa de nivel como default
        platforms    = manifest.get("platform_targets") or LEVEL_PLATFORM_MAP.get(nsfw_level, [])

        results = {}
        pricing = LEVEL_PRICING.get(nsfw_level, LEVEL_PRICING[4])

        logger.info(
            f"\n{'='*55}\n"
            f"🚀 SalesConnector v2.0 | {character_id} | Level {nsfw_level}\n"
            f"   Etapa embudo: {pricing['strategy']} → {pricing['funnel_goal']}\n"
            f"   Plataformas:  {', '.join(platforms) if platforms else 'ninguna'}\n"
            f"{'='*55}"
        )

        if not platforms:
            logger.info("ℹ️  Nivel 0-2: contenido de adquisición, sin venta directa.")
            return {"ok": True, "note": "SFW/Teaser - no sale platforms for this level"}

        # ── Gumroad ────────────────────────────────────────
        if "gumroad" in platforms:
            results["gumroad"] = await self.gumroad.publish_full_pack(
                character_id=character_id, nsfw_level=nsfw_level,
                video_path=video_path, dry_run=dry_run,
            )

        # ── Patreon ────────────────────────────────────────
        if "patreon" in platforms:
            results["patreon"] = await self.patreon.create_post(
                character_id=character_id, nsfw_level=nsfw_level, dry_run=dry_run,
            )

        # ── Fansly ─────────────────────────────────────────
        if "fansly" in platforms:
            ppv = pricing["pack_price_usd"] if nsfw_level >= 10 else 0.0
            results["fansly"] = await self.fansly.create_post(
                character_id=character_id, nsfw_level=nsfw_level,
                video_path=video_path, price_usd=ppv, dry_run=dry_run,
            )

        # ── Fanvue ─────────────────────────────────────────
        if "fanvue" in platforms:
            is_ppv = nsfw_level >= 10
            ppv_price = pricing.get("pack_price_usd", 0.0) if is_ppv else 0.0
            results["fanvue"] = await self.fanvue.create_post(
                character_id=character_id, nsfw_level=nsfw_level,
                video_path=video_path, is_ppv=is_ppv,
                ppv_price_usd=ppv_price, dry_run=dry_run,
            )

        # ── itch.io ────────────────────────────────────────
        if "itchio" in platforms:
            results["itchio"] = await self.itchio.publish_pack(
                character_id=character_id, nsfw_level=nsfw_level,
                video_path=video_path, dry_run=dry_run,
            )

        # ── Actualizar manifiesto con resultados ──────────
        manifest["sales_results"]  = results
        manifest["funnel_stage"]   = pricing["strategy"]
        manifest["funnel_goal"]    = pricing["funnel_goal"]
        manifest["platforms_used"] = platforms
        manifest["published_at"]   = datetime.utcnow().isoformat()

        with open(manifest_path_obj, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        ok_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get("ok"))
        logger.info(f"✅ SalesConnector completado: {ok_count}/{len(results)} plataformas OK")
        return results

    async def close(self):
        await asyncio.gather(
            self.gumroad.close(), self.patreon.close(),
            self.fansly.close(), self.fanvue.close(), self.itchio.close(),
        )


# ─────────────────────────────────────────────────────────
# CLI rápido para pruebas
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    async def main():
        connector = SalesConnector()
        mode  = sys.argv[1] if len(sys.argv) > 1 else "verify"
        char  = sys.argv[2] if len(sys.argv) > 2 else "aiko_hayashi"
        level = int(sys.argv[3]) if len(sys.argv) > 3 else 4

        if mode == "verify":
            result = await connector.verify_all()
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif mode == "dry-run":
            result = await connector.gumroad.publish_full_pack(
                character_id=char, nsfw_level=level,
                video_path="/tmp/test.mp4", dry_run=True,
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif mode == "platforms":
            from src.api.sales_connector import LEVEL_PLATFORM_MAP
            for lv, plats in LEVEL_PLATFORM_MAP.items():
                pricing = LEVEL_PRICING[lv]
                print(f"Level {lv} ({pricing['label']}): {', '.join(plats) or 'SFW - sin venta'}")

        await connector.close()

    asyncio.run(main())
