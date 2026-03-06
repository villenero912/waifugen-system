"""
Test: Sales Connector — Gumroad + Patreon
==========================================
Prueba las conexiones API sin subir archivos reales (dry-run).

Uso:
    python scripts/test_sales_connector.py              # verify only
    python scripts/test_sales_connector.py dry-run      # simula publish

Requiere en .env:
    GUMROAD_ACCESS_TOKEN=...
    PATREON_ACCESS_TOKEN=...
    PATREON_CAMPAIGN_ID=...
"""

import os
import sys
import json
import asyncio
import tempfile
from pathlib import Path

# Resolver path del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "waifugen_mejorado" / "src"))

from api.sales_connector import SalesConnector, LEVEL_PRICING


async def test_verify_credentials():
    """Prueba 1: Verificar tokens de ambas plataformas."""
    print("\n" + "="*55)
    print("🔑 PRUEBA 1: Verificación de Credenciales")
    print("="*55)

    connector = SalesConnector()
    result = await connector.verify_all()

    gum_ok = result.get("gumroad", {}).get("ok", False)
    pat_ok = result.get("patreon", {}).get("ok", False)

    print(f"\n  Gumroad:  {'✅ OK' if gum_ok else '❌ FALLO (configura GUMROAD_ACCESS_TOKEN)'}")
    print(f"  Patreon:  {'✅ OK' if pat_ok else '❌ FALLO (configura PATREON_ACCESS_TOKEN + PATREON_CAMPAIGN_ID)'}")

    if gum_ok:
        user = result["gumroad"].get("user", {})
        print(f"  └─ Cuenta: {user.get('name')} | {user.get('email')}")
    if pat_ok:
        creator = result["patreon"].get("creator", {})
        print(f"  └─ Campaña: {creator.get('full_name')} | {creator.get('email')}")

    await connector.close()
    return gum_ok, pat_ok


async def test_funnel_pricing():
    """Prueba 2: Mostrar la tabla de embudos y precios."""
    print("\n" + "="*55)
    print("📊 PRUEBA 2: Embudos de Ingeniería Social — Tabla de Precios")
    print("="*55)
    print(f"\n  {'Nivel':<8} {'Nombre':<22} {'Pack $':<10} {'Mes $':<10} {'Etapa'}")
    print("  " + "-"*55)
    for level, data in LEVEL_PRICING.items():
        print(
            f"  Lv {level:<5} {data['label']:<22} "
            f"${data['pack_price_usd']:<9.2f} "
            f"${data['monthly_usd']:<9.2f} "
            f"{data['strategy']}"
        )
    print()
    print("  Flujo de embudo:")
    print("    TikTok/IG (SFW, Lv0) → Telegram/LINE (Lv2) → Gumroad Lv4 → Lv6 → Lv8 → PPV Lv10")


async def test_dry_run_gumroad(character_id: str = "aiko_hayashi", level: int = 4):
    """Prueba 3: Simula la creación de un producto en Gumroad (sin llamada real)."""
    print("\n" + "="*55)
    print(f"📦 PRUEBA 3: Dry-Run Gumroad — {character_id} Nivel {level}")
    print("="*55)

    # Crear un archivo MP4 de prueba temporal (1KB vacío)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(b"\x00" * 1024)
        tmp_path = tmp.name

    connector = SalesConnector()
    result = await connector.gumroad.publish_full_pack(
        character_id=character_id,
        nsfw_level=level,
        video_path=tmp_path,
        dry_run=True,
    )
    print(f"\n  Resultado: {'✅' if result.get('ok') else '❌'}")
    print(json.dumps(result, indent=4, ensure_ascii=False))
    await connector.close()
    os.unlink(tmp_path)


async def test_dry_run_manifest(character_id: str = "aiko_hayashi"):
    """Prueba 4: Crea un manifiesto de prueba y simula publish_from_manifest."""
    print("\n" + "="*55)
    print(f"📋 PRUEBA 4: Dry-Run completo desde manifiesto — {character_id}")
    print("="*55)

    manifest_dir = PROJECT_ROOT / "output/phase2/sales"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"TEST_{character_id}_manifest.json"

    # Crear manifiesto de prueba
    test_manifest = {
        "character": character_id,
        "region": "US",
        "video_file": "/tmp/test_video.mp4",
        "nsfw_level": 6,
        "platform_targets": ["gumroad", "patreon"],
        "tags": ["4k", "realistic", "waifu", character_id],
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(test_manifest, f, indent=2, ensure_ascii=False)

    connector = SalesConnector()
    results = await connector.publish_from_manifest(str(manifest_path), dry_run=True)
    await connector.close()

    print(f"\n  Gumroad: {'✅' if results.get('gumroad', {}).get('ok') else '❌'}")
    print(f"  Patreon: {'✅' if results.get('patreon', {}).get('ok') else '❌'}")
    print(f"\n  Manifiesto actualizado: {manifest_path}")

    # Mostrar manifiesto resultante
    with open(manifest_path, "r", encoding="utf-8") as f:
        updated = json.load(f)
    print(f"  Etapa de embudo: {updated.get('funnel_stage')}")
    print(f"  Objetivo: {updated.get('funnel_goal')}")


async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    char = sys.argv[2] if len(sys.argv) > 2 else "aiko_hayashi"
    level = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    print("\n🧪 TEST — Sales Connector (Gumroad + Patreon)")
    print(f"   Modo: {mode} | Personaje: {char} | Nivel: {level}\n")

    if mode in ("all", "verify"):
        await test_verify_credentials()

    if mode in ("all", "funnel"):
        await test_funnel_pricing()

    if mode in ("all", "dry-run"):
        await test_dry_run_gumroad(char, level)
        await test_dry_run_manifest(char)

    print("\n" + "="*55)
    print("✨ Tests completados.")
    print("="*55 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
