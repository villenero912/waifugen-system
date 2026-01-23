import os
import json
import asyncio
import logging
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phase2Generator")

class Phase2ContentGenerator:
    """
    Automatiza la generación de contenido de Fase 2 (Adulto) usando la API de A2E.
    Utiliza LoRAs de personajes, niveles de escalada NSFW y prompts curados.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("A2E_API_KEY")
        if not self.api_key:
            logger.warning("A2E_API_KEY no encontrada. Las operaciones fallarán hasta que se configure.")
        
        # Base paths
        self.config_root = Path("config")
        self.output_root = Path("output/phase2")
        self.output_root.mkdir(parents=True, exist_ok=True)
        
        # Cargar recursos
        self._load_configs()

    def _load_configs(self):
        """Carga todas las configuraciones necesarias para la generación."""
        try:
            # Configuración de personajes
            char_path = Path("C:/Users/Sebas/Downloads/package (1)/waifugen_system/config/avatars/elite8_characters.json")
            if char_path.exists():
                with open(char_path, "r", encoding="utf-8") as f:
                    self.characters = json.load(f)["characters"]
            else:
                self.characters = {}

            # Escalada NSFW
            esc_path = Path("C:/Users/Sebas/Downloads/package (1)/waifugen_system/config/funnels/nsfw_escalation.json")
            if esc_path.exists():
                with open(esc_path, "r", encoding="utf-8") as f:
                    self.escalation = json.load(f)["escalation_levels"]
            else:
                self.escalation = []

            # Registro de LoRAs Phase 2
            lora_path = Path("C:/Users/Sebas/Downloads/package (1)/proyecto_waifugen/proyecto_analisis/jav_project_extracted/jav_project/config/phase2_lora_models.json")
            if lora_path.exists():
                with open(lora_path, "r", encoding="utf-8") as f:
                    self.loras = json.load(f)["lora_registry"]
            else:
                self.loras = {}

        except Exception as e:
            logger.error(f"Error cargando configuraciones: {e}")

    def get_character_lo_ras(self, character_id: str, nsfw_level: int) -> List[Dict[str, Any]]:
        """
        Obtiene la combinación optimizada de LoRAs para un personaje y nivel NSFW.
        """
        selected_loras = []
        
        # 1. Base Glamour (Dependiente del nivel)
        if nsfw_level >= 4:
            selected_loras.append({"name": "glamour_elegant_v1", "weight": 0.8})
        
        # 2. Expresiones (Dependiente del nivel)
        if nsfw_level >= 6:
            selected_loras.append({"name": "expressions_passionate_v1", "weight": 0.7})
        elif nsfw_level >= 2:
            selected_loras.append({"name": "expressions_intimate_v1", "weight": 0.65})
            
        # 3. Ropa/Lencería
        if nsfw_level >= 6:
            selected_loras.append({"name": "clothing_lingerie_bold_v1", "weight": 0.75})
        elif nsfw_level >= 4:
            selected_loras.append({"name": "clothing_lingerie_elegant_v1", "weight": 0.75})

        # 4. Poses
        if nsfw_level >= 4:
            selected_loras.append({"name": "poses_boudoir_v1", "weight": 0.75})

        return selected_loras

    def construct_prompt(self, character_id: str, nsfw_level: int, context: str = "") -> str:
        """
        Construye un prompt de alta calidad para la API de A2E.
        """
        # Buscar el trigger word del personaje
        char_data = self.characters.get(character_id, {})
        trigger = char_data.get("trigger_word", f"{character_id}_v1")
        
        prompt_parts = [trigger]
        
        if nsfw_level == 2:
            prompt_parts += ["suggestive expression", "lingerie", "soft lighting", "intimate atmosphere"]
        elif nsfw_level == 4:
            prompt_parts += ["intimate expression", "silk lingerie", "boudoir setting", "sensual reclining"]
        elif nsfw_level == 6:
            prompt_parts += ["passionate expression", "bold lingerie", "chiaroscuro lighting", "dramatic shadows"]
        elif nsfw_level >= 8:
            prompt_parts += ["ecstasy expression", "artistic nudity", "premium production", "4k detail"]
            
        if context:
            prompt_parts.append(context)
            
        prompt_parts += ["high quality", "8k uhd", "professional photography"]
        
        return ", ".join(prompt_parts)

    async def generate_reference_set(self, character_id: str, levels: List[int] = [2, 4, 6]):
        """
        Genera un set de imágenes de referencia para un personaje en múltiples niveles NSFW.
        Estas imágenes servirán como 'visual anchors' para la generación de video.
        """
        logger.info(f"Iniciando generación de set de referencia para {character_id}")
        
        results = []
        for level in levels:
            prompt = self.construct_prompt(character_id, level)
            loras = self.get_character_lo_ras(character_id, level)
            
            logger.info(f"Generando imagen nivel {level} para {character_id}...")
            
            # Aquí iría el llamado real a la API de A2E
            # response = await self.client.generate_image(...)
            
            job_data = {
                "character": character_id,
                "nsfw_level": level,
                "prompt": prompt,
                "loras": loras,
                "resolution": "2048x2048" if level >= 4 else "1024x1024",
                "status": "ready_to_send"
            }
            results.append(job_data)
            
        # Guardar manifiesto de generación
        manifest_path = self.output_root / f"{character_id}_reference_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Manifiesto guardado en: {manifest_path}")
        return results

async def main():
    # Instanciar generador
    gen = Phase2ContentGenerator()
    
    # Generar sets de referencia para los personajes estrella
    stars = ["aurelia_viral", "miysak_v1", "airineo_fusion"]
    for char in stars:
        await gen.generate_reference_set(char)

if __name__ == "__main__":
    asyncio.run(main())
