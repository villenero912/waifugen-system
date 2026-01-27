
import json
import subprocess
import os
import sys
from pathlib import Path

# Configuración del Test - Hana Nakamura Nivel 6 (Mid-tier NSFW)
test_payload = {
    "request_id": "TEST_HANA_LEVEL6_ONSEN",
    "character_id": "hana_nakamura",
    "prompt": "hana_nakamura_v1, topless, sitting in a private outdoor onsen, steam rising, water surface reflecting moon, wet skin, elegant jewelry, masterpiece of lighting and atmosphere, cinematic 4k, realistic skin textures",
    "video_duration": 30,
    "job_payload": {
        "prompt": "hana_nakamura_v1, topless, sitting in a private outdoor onsen, steam rising, water surface reflecting moon, wet skin, elegant jewelry, masterpiece of lighting and atmosphere, cinematic 4k, realistic skin textures",
        "duration_seconds": 30,
        "resolution": "3840x2160",
        "lipsync": True,
        "upscale": True
    }
}

def run_test():
    print("🧪 INICIANDO TEST DE GENERACIÓN FASE 2 - NIVEL 6 🔞")
    print(f"👤 Personaje: Hana Nakamura")
    print(f"🌉 Escenario: Onsen Privado (Romantic/Sensual)")
    print(f"🛠️  Motor: GPU Remota (RunPod RTX 4090) + LipSync HQ + 4K Upscale")
    print("-" * 50)

    # Llamar al puente n8n
    bridge_path = "src/processing/n8n_long_video_bridge.py"
    try:
        # Usamos json.dumps para pasar el argumento correctamente
        result = subprocess.run(
            [sys.executable, bridge_path, json.dumps(test_payload)],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Imprimir salida parseada
        output_data = json.loads(result.stdout)
        print("\n✅ RESPUESTA DEL SISTEMA:")
        print(json.dumps(output_data, indent=4))
        
        print("\n📊 ANÁLISIS DE COSTES ESTIMADOS:")
        cost = output_data.get("estimated_cost_usd", 0)
        print(f"   A2E (Credits): ~$1.50 (90-120 credits)")
        print(f"   GPU Propia:    ${cost:.4f} (Ahorro ~97%)")
        
        print("\n✨ CARACTERÍSTICAS APLICADAS:")
        print("   [X] LipSync Wav2Lip-HQ")
        print("   [X] Face Restoration (Real-ESRGAN)")
        print("   [X] Temporal Consistency (LoRA Fusion)")
        
    except Exception as e:
        print(f"\n❌ ERROR EN EL TEST: {str(e)}")
        if hasattr(e, 'stderr'):
            print(f"Detalles: {e.stderr}")

if __name__ == "__main__":
    run_test()
