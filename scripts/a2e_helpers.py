"""
A2E Pro - Helper Scripts for Phase 1 Implementation

Quick commands to manage your A2E Pro workflow optimized for 4 daily reels.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.a2e_client import A2EClient, GenerationConfig, A2EModelType, VideoResolution


async def check_credits():
    """Verificar créditos disponibles"""
    print("💳 Verificando créditos A2E...\n")
    
    client = A2EClient()
    credits = await client.get_credits()
    
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Plan: {credits.plan_type.value.upper()}")
    print(f"  Total: {credits.total_credits:,} créditos")
    print(f"  Usados: {credits.used_credits:,} créditos")
    print(f"  Restantes: {credits.remaining_credits:,} créditos")
    print(f"  Uso: {credits.usage_percentage:.1f}%")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    # Calcular cuántos reels puedes generar
    credits_per_reel = 60  # Seedance 720p
    reels_possible = credits.remaining_credits // credits_per_reel
    
    print(f"📹 Reels posibles (Seedance 720p): {reels_possible}")
    
    # Alertas
    if credits.remaining_credits < 500:
        print(f"\n⚠️  ALERTA: Menos de 500 créditos restantes")
        print(f"   Considera comprar topup: +1800 créditos por $19.90")
    
    if credits.usage_percentage > 80:
        print(f"\n🚨 CRÍTICO: Uso superior al 80%")
        print(f"   Topup recomendado urgente")
    
    return credits


async def test_generation(character="miyuki_sakura"):
    """Generar reel de prueba"""
    print(f"🎬 Generando reel de prueba con {character}...\n")
    
    client = A2EClient()
    
    # Mapeo de personajes a trigger words
    triggers = {
        "miyuki_sakura": "miysak_v1",
        "airi_neo": "airineo_fusion",
        "hana_nakamura": "hannak_v1",
        "aiko_hayashi": "aikoch_v1"
    }
    
    trigger = triggers.get(character, "miysak_v1")
    
    config = GenerationConfig(
        model=A2EModelType.SEEDANCE_1_5_PRO,
        resolution=VideoResolution.HD_720P,
        duration_seconds=15,
        prompt=f"{trigger}, japanese woman, happy cute expression, waving hello, studio background, soft lighting, high quality",
        character_trigger=trigger,
        face_consistency_threshold=0.95,
        lora_strength=0.8,
        cfg_scale=1.5
    )
    
    print(f"📊 Configuración:")
    print(f"   Modelo: {config.model.value}")
    print(f"   Resolución: 720p")
    print(f"   Duración: {config.duration_seconds}s")
    print(f"   Créditos: ~60")
    print(f"\n⏳ Generando...")
    
    result = await client.generate_video(config)
    
    if result.success:
        print(f"\n✅ Job ID: {result.job.job_id}")
        print(f"   Status: {result.job.status.value}")
        print(f"\n⏳ Esperando completación...")
        
        final = await client.wait_for_completion(
            result.job.job_id,
            poll_interval=10,
            max_wait=300
        )
        
        if final.status.value == "completed":
            print(f"\n🎉 ¡Completado!")
            print(f"   URL: {final.output_url}")
            print(f"   Face Consistency: {final.face_consistency_score:.2f}")
            print(f"   Quality Score: {final.quality_score}")
            print(f"   Créditos usados: {final.credits_used}")
        else:
            print(f"\n❌ Falló: {final.error_message}")
    else:
        print(f"\n❌ Error: {result.error}")
    
    return result


async def batch_generate_4_reels():
    """Generar 4 reels en batch (ahorro 15%)"""
    print("🎯 Generación en Batch: 4 Reels Diarios\n")
    
    client = A2EClient()
    
    # Verificar créditos primero
    credits = await client.get_credits()
    required = 255  # 60+60+60+75
    
    if credits.remaining_credits < required:
        print(f"❌ Créditos insuficientes")
        print(f"   Necesitas: {required}")
        print(f"   Tienes: {credits.remaining_credits}")
        return
    
    print(f"✅ Créditos suficientes ({credits.remaining_credits:,})")
    print(f"\n📋 Configuración de reels:\n")
    
    # Configurar 4 reels
    configs = [
        {
            "character": "miyuki_sakura",
            "trigger": "miysak_v1",
            "prompt": "energetic morning greeting, waving happily",
            "model": A2EModelType.SEEDANCE_1_5_PRO,
            "credits": 60,
            "slot": "Morning"
        },
        {
            "character": "hana_nakamura",
            "trigger": "hannak_v1",
            "prompt": "soft emotional moment, gentle smile",
            "model": A2EModelType.SEEDANCE_1_5_PRO,
            "credits": 60,
            "slot": "Afternoon"
        },
        {
            "character": "airi_neo",
            "trigger": "airineo_fusion",
            "prompt": "cyberpunk neon energy, futuristic pose",
            "model": A2EModelType.SEEDANCE_1_5_PRO,
            "credits": 60,
            "slot": "Evening"
        },
        {
            "character": "aiko_hayashi",
            "trigger": "aikoch_v1",
            "prompt": "professional elegant pose, confident smile",
            "model": A2EModelType.WAN_2_5_720P,
            "credits": 75,
            "slot": "Night (Premium)"
        }
    ]
    
    for i, cfg in enumerate(configs, 1):
        print(f"   {i}. {cfg['slot']:20} | {cfg['character']:15} | {cfg['credits']} créditos")
    
    print(f"\n   TOTAL: 255 créditos")
    print(f"\n⏳ Iniciando generación...\n")
    
    # Generar todas en paralelo
    tasks = []
    for cfg in configs:
        gen_config = GenerationConfig(
            model=cfg['model'],
            resolution=VideoResolution.HD_720P,
            duration_seconds=15,
            prompt=f"{cfg['trigger']}, japanese woman, {cfg['prompt']}, studio background, professional lighting",
            character_trigger=cfg['trigger'],
            face_consistency_threshold=0.95
        )
        tasks.append(client.generate_video(gen_config))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print(f"\n📊 Resultados:\n")
    successful = 0
    for i, (cfg, result) in enumerate(zip(configs, results), 1):
        if isinstance(result, Exception):
            print(f"   {i}. ❌ {cfg['slot']}: Error")
        elif result.success:
            print(f"   {i}. ✅ {cfg['slot']}: Job {result.job.job_id}")
            successful += 1
        else:
            print(f"   {i}. ❌ {cfg['slot']}: {result.error}")
    
    print(f"\n✅ Exitosos: {successful}/4")
    print(f"💰 Créditos usados: ~{successful * 60 + (75 if successful == 4 else 0)}")
    print(f"\n💡 Ahorro con batch: ~18 créditos (15%)")
    
    return results


async def daily_report():
    """Reporte diario de uso"""
    print("📊 Reporte Diario A2E Pro\n")
    
    client = A2EClient()
    
    # Créditos
    credits = await client.get_credits()
    usage_report = client.credit_manager.get_usage_report()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("💳 CRÉDITOS")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Diario:")
    print(f"  Usados: {usage_report['daily']['used']:,}")
    print(f"  Total: {usage_report['daily']['total']:,}")
    print(f"  Porcentaje: {usage_report['daily']['percentage']:.1f}%")
    print(f"\nMensual:")
    print(f"  Usados: {usage_report['monthly']['used']:,}")
    print(f"  Total: {usage_report['monthly']['total']:,}")
    print(f"  Porcentaje: {usage_report['monthly']['percentage']:.1f}%")
    
    # Proyecciones
    daily_avg = usage_report['daily']['used']
    monthly_projection = daily_avg * 30
    
    print(f"\n📈 PROYECCIONES")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Promedio diario: {daily_avg:,} créditos")
    print(f"Proyección mensual: {monthly_projection:,} créditos")
    
    if monthly_projection > 3600:
        deficit = monthly_projection - 3600
        topups_needed = (deficit // 1800) + 1
        cost = topups_needed * 19.90
        print(f"\n⚠️  Topup necesario:")
        print(f"   Déficit: {deficit:,} créditos")
        print(f"   Topups: {topups_needed} × $19.90")
        print(f"   Costo: ${cost:.2f}")
    else:
        print(f"\n✅ Sin topup necesario este mes")
    
    return usage_report


def main():
    """Menú principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="A2E Pro Helper Scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python a2e_helpers.py credits          # Ver créditos
  python a2e_helpers.py test             # Generar reel de prueba
  python a2e_helpers.py test --character airi_neo  # Test con personaje específico
  python a2e_helpers.py batch            # Generar 4 reels en batch
  python a2e_helpers.py report           # Reporte diario
        """
    )
    
    parser.add_argument(
        'command',
        choices=['credits', 'test', 'batch', 'report'],
        help='Comando a ejecutar'
    )
    
    parser.add_argument(
        '--character',
        choices=['miyuki_sakura', 'airi_neo', 'hana_nakamura', 'aiko_hayashi'],
        default='miyuki_sakura',
        help='Personaje para test (default: miyuki_sakura)'
    )
    
    args = parser.parse_args()
    
    if args.command == 'credits':
        asyncio.run(check_credits())
    elif args.command == 'test':
        asyncio.run(test_generation(args.character))
    elif args.command == 'batch':
        asyncio.run(batch_generate_4_reels())
    elif args.command == 'report':
        asyncio.run(daily_report())


if __name__ == "__main__":
    main()
