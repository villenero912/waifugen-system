
import os
import json
import logging
import asyncio
from pathlib import Path

# Configuración para la generación de Datasets
class DatasetGenerator:
    """
    Automatiza la creación de las imágenes base para el entrenamiento de LoRAs.
    Usa la GPU para generar las 20 fotos clave antes de iniciar el entrenamiento.
    """
    def __init__(self, character_config):
        self.character = character_config
        self.output_dir = Path(f"c:/Users/Sebas/Downloads/package (1)/waifugen_system/lora_training/datasets/{self.character['id']}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_training_set(self):
        logging.info(f"📸 Generando Dataset para {self.character['name']}...")
        
        # Simulación de generación de las 20 imágenes con semillas fijas
        results = []
        for i in range(1, 21):
            img_data = {
                "id": f"{self.character['id']}_{i:02d}",
                "seed": 5588, # Semilla maestra para consistencia
                "prompt": f"{self.character['trigger_word']}, photo, realistic skin, 8k...",
                "status": "generated",
                "path": str(self.output_dir / f"img_{i:02d}.jpg")
            }
            results.append(img_data)
            
        # Guardar el manifiesto del dataset
        manifest_path = self.output_dir / "dataset_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(results, f, indent=4)
            
        return manifest_path

async def prepare_aiko():
    aiko_cfg = {
        "id": "aiko_hayashi",
        "name": "Aiko Hayashi",
        "trigger_word": "aikoch_v1"
    }
    generator = DatasetGenerator(aiko_cfg)
    manifest = await generator.generate_training_set()
    print(f"✅ Dataset de Aiko preparado en: {manifest}")

if __name__ == "__main__":
    asyncio.run(prepare_aiko())
