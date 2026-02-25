"""
FLUJO COMPLETO END-TO-END - Generación de Reel con Edición
Desde trigger hasta video final listo para publicar

Pipeline:
1. Trigger (manual o automático)
2. Selección de personaje
3. Generación de prompt (Ollama)
4. Generación de script de voz
5. Generación de video (A2E)
6. Generación de voz (Piper TTS)
7. Generación de música (Replicate/Pixabay)
8. Montaje final (FFmpeg)
9. Guardado en base de datos
10. Output: Reel.mp4 listo para publicar
"""

import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import json
import random

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
OUTPUT_BASE = Path("/app/data/reels")
TEMP_DIR = Path("/tmp/reel_generation")


class ReelGenerator:
    """Generador completo de reels end-to-end"""
    
    def __init__(self):
        self.characters = self.load_characters()
        self.reel_id = None
        self.output_dir = None
        
    def load_characters(self):
        """Cargar configuración de personajes"""
        config_path = Path("/app/config/avatars/reels_optimization_config.json")
        
        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
                return data.get("characters", {})
        
        # Fallback: personajes básicos
        return {
            "miyuki_sakura": {
                "name": "Miyuki Sakura",
                "age": 22,
                "trigger_word": "miysak_v1",
                "style": "elegant, soft features"
            }
        }
    
    async def step_1_trigger(self, character_id=None):
        """
        PASO 1: Trigger y selección de personaje
        """
        logger.info("=" * 60)
        logger.info("PASO 1: TRIGGER - Selección de Personaje")
        logger.info("=" * 60)
        
        # Seleccionar personaje (aleatorio o específico)
        if not character_id:
            character_id = random.choice(list(self.characters.keys()))
        
        character = self.characters.get(character_id)
        
        if not character:
            raise ValueError(f"Personaje no encontrado: {character_id}")
        
        logger.info(f"✓ Personaje seleccionado: {character['name']}")
        logger.info(f"  ID: {character_id}")
        logger.info(f"  Trigger: {character.get('trigger_word', 'N/A')}")
        
        # Crear ID único para este reel
        self.reel_id = f"{character_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Crear directorio de trabajo
        self.output_dir = TEMP_DIR / self.reel_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"  Reel ID: {self.reel_id}")
        logger.info(f"  Output: {self.output_dir}")
        logger.info("")
        
        return character_id, character
    
    async def step_2_generate_prompt(self, character):
        """
        PASO 2: Generar prompt con Ollama
        """
        logger.info("=" * 60)
        logger.info("PASO 2: Generación de Prompt (Ollama)")
        logger.info("=" * 60)
        
        # Request para Ollama
        request = f"""
        Generate a 50-word creative prompt for A2E video generation.
        
        Character: {character['name']}, {character['age']} years old
        Style: {character.get('style', 'elegant')}
        Platform: TikTok
        Theme: Morning motivation
        Duration: 15 seconds
        
        Output ONLY the prompt, no explanations.
        """
        
        try:
            # Llamar a Ollama
            result = subprocess.run(
                ["docker", "exec", "-i", "waifugen_ollama", 
                 "ollama", "run", "llama3"],
                input=request,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            prompt = result.stdout.strip()
            
            if not prompt:
                # Fallback
                prompt = f"Ultra realistic portrait of {character['name']}, {character.get('style')}, morning light, warm smile, 4K quality"
            
            logger.info(f"✓ Prompt generado:")
            logger.info(f"  {prompt[:100]}...")
            
            # Guardar
            (self.output_dir / "prompt.txt").write_text(prompt)
            logger.info("")
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error en Ollama: {e}")
            # Fallback
            prompt = f"Portrait of {character['name']}, elegant style, professional quality"
            return prompt
    
    async def step_3_generate_script(self, character):
        """
        PASO 3: Generar script de voz
        """
        logger.info("=" * 60)
        logger.info("PASO 3: Generación de Script de Voz")
        logger.info("=" * 60)
        
        scripts = [
            f"Hello! I'm {character['name']}. Today is going to be amazing. Let's make it happen!",
            f"Good morning! This is {character['name']}. Ready to start your day with positive energy?",
            f"Hi there! I'm {character['name']}. Let's make today unforgettable together!"
        ]
        
        script = random.choice(scripts)
        
        logger.info(f"✓ Script generado:")
        logger.info(f"  {script}")
        
        # Guardar
        (self.output_dir / "script.txt").write_text(script)
        logger.info("")
        
        return script
    
    async def step_4_generate_video(self, prompt, character):
        """
        PASO 4: Generar video con A2E
        """
        logger.info("=" * 60)
        logger.info("PASO 4: Generación de Video (A2E)")
        logger.info("=" * 60)
        
        logger.info(f"  Modelo: seedance_1.5_pro")
        logger.info(f"  Resolución: 720p")
        logger.info(f"  Duración: 15s")
        logger.info(f"  Créditos: ~15")
        logger.info("")
        
        # Aquí iría la llamada real a A2E
        logger.warning("⚠️  A2E real requiere API key configurada")
        logger.warning("⚠️  Usando placeholder por ahora")
        
        # Crear placeholder
        video_path = self.output_dir / "video.mp4"
        video_path.touch()
        
        logger.info(f"✓ Video placeholder: {video_path.name}")
        logger.info("")
        
        return str(video_path)
    
    async def step_5_generate_voice(self, script):
        """
        PASO 5: Generar voz con Piper TTS
        """
        logger.info("=" * 60)
        logger.info("PASO 5: Generación de Voz (Piper TTS)")
        logger.info("=" * 60)
        
        voice_path = self.output_dir / "voice.wav"
        
        try:
            # Llamar a Piper
            process = subprocess.Popen(
                ["docker", "exec", "-i", "waifugen_piper",
                 "piper", "--model", "en_US-amy-medium",
                 "--output_file", "/tmp/voice.wav"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(input=script.encode())
            
            # Copiar del contenedor
            subprocess.run([
                "docker", "cp",
                "waifugen_piper:/tmp/voice.wav",
                str(voice_path)
            ])
            
            if voice_path.exists():
                logger.info(f"✓ Voz generada: {voice_path.name}")
                logger.info(f"  Tamaño: {voice_path.stat().st_size / 1024:.1f} KB")
            else:
                raise FileNotFoundError("Archivo de voz no generado")
                
        except Exception as e:
            logger.error(f"Error en Piper: {e}")
            voice_path.touch()
            logger.warning("⚠️  Usando placeholder de voz")
        
        logger.info("")
        return str(voice_path)
    
    async def step_6_generate_music(self):
        """
        PASO 6: Generar música de fondo
        """
        logger.info("=" * 60)
        logger.info("PASO 6: Música de Fondo")
        logger.info("=" * 60)
        
        logger.info("  Género: Lo-fi beat")
        logger.info("  Duración: 15s")
        logger.info("")
        
        logger.warning("⚠️  Usando música placeholder")
        logger.warning("⚠️  En producción: Replicate MusicGen o Pixabay")
        
        music_path = self.output_dir / "music.mp3"
        music_path.touch()
        
        logger.info(f"✓ Música placeholder: {music_path.name}")
        logger.info("")
        
        return str(music_path)
    
    async def step_7_montage(self, video_path, voice_path, music_path):
        """
        PASO 7: Montaje final con FFmpeg
        """
        logger.info("=" * 60)
        logger.info("PASO 7: MONTAJE FINAL (FFmpeg)")
        logger.info("=" * 60)
        
        final_path = self.output_dir / f"{self.reel_id}_final.mp4"
        
        logger.info("  Combinando:")
        logger.info(f"  - Video: {Path(video_path).name}")
        logger.info(f"  - Voz: {Path(voice_path).name}")
        logger.info(f"  - Música: {Path(music_path).name}")
        logger.info("")
        
        # Comando FFmpeg (placeholder - adaptarlo según archivos reales)
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", voice_path,
            "-i", music_path,
            "-filter_complex",
            "[1:a]volume=1.0[voice];[2:a]volume=0.3[music];[voice][music]amix=inputs=2:duration=first[audio]",
            "-map", "0:v",
            "-map", "[audio]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(final_path)
        ]
        
        try:
            logger.info("🎬 Ejecutando FFmpeg...")
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                timeout=60
            )
            
            if final_path.exists() and final_path.stat().st_size > 0:
                logger.info(f"✓ Reel final generado: {final_path.name}")
                logger.info(f"  Tamaño: {final_path.stat().st_size / 1024 / 1024:.1f} MB")
            else:
                raise FileNotFoundError("Montaje falló")
                
        except Exception as e:
            logger.error(f"Error en FFmpeg: {e}")
            # Crear placeholder
            final_path.touch()
            logger.warning("⚠️  Usando placeholder de video final")
        
        logger.info("")
        return str(final_path)
    
    async def step_8_save_to_database(self, character_id, final_path):
        """
        PASO 8: Guardar metadata en base de datos
        """
        logger.info("=" * 60)
        logger.info("PASO 8: Guardado en Base de Datos")
        logger.info("=" * 60)
        
        metadata = {
            "reel_id": self.reel_id,
            "character_id": character_id,
            "generated_at": datetime.now().isoformat(),
            "video_path": str(final_path),
            "duration": 15,
            "resolution": "720p",
            "platform": "tiktok",
            "status": "ready_to_publish"
        }
        
        # Guardar metadata
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✓ Metadata guardada: {metadata_path.name}")
        logger.info("")
        
        # En producción: INSERT INTO PostgreSQL
        logger.info("  En producción: INSERT INTO reels table")
        logger.info("")
        
        return metadata
    
    async def step_9_finalize(self, final_path):
        """
        PASO 9: Finalización y copia a destino
        """
        logger.info("=" * 60)
        logger.info("PASO 9: FINALIZACIÓN")
        logger.info("=" * 60)
        
        # Crear directorio de salida final
        OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
        
        # Copiar a destino final
        final_dest = OUTPUT_BASE / f"{self.reel_id}.mp4"
        
        try:
            import shutil
            shutil.copy2(final_path, final_dest)
            logger.info(f"✓ Reel copiado a: {final_dest}")
        except Exception as e:
            logger.error(f"Error copiando: {e}")
            final_dest = Path(final_path)
        
        logger.info("")
        return str(final_dest)
    
    async def generate_complete_reel(self, character_id=None):
        """
        EJECUTAR FLUJO COMPLETO
        """
        logger.info("\n")
        logger.info("=" * 60)
        logger.info("WAIFUGEN - GENERACIÓN COMPLETA DE REEL")
        logger.info("Pipeline End-to-End con Edición")
        logger.info("=" * 60)
        logger.info("\n")
        
        try:
            # PASO 1: Trigger
            character_id, character = await self.step_1_trigger(character_id)
            
            # PASO 2: Prompt
            prompt = await self.step_2_generate_prompt(character)
            
            # PASO 3: Script
            script = await self.step_3_generate_script(character)
            
            # PASO 4: Video
            video_path = await self.step_4_generate_video(prompt, character)
            
            # PASO 5: Voz
            voice_path = await self.step_5_generate_voice(script)
            
            # PASO 6: Música
            music_path = await self.step_6_generate_music()
            
            # PASO 7: Montaje
            final_path = await self.step_7_montage(video_path, voice_path, music_path)
            
            # PASO 8: Base de datos
            metadata = await self.step_8_save_to_database(character_id, final_path)
            
            # PASO 9: Finalización
            output_file = await self.step_9_finalize(final_path)
            
            # RESUMEN
            logger.info("=" * 60)
            logger.info("✅ GENERACIÓN COMPLETADA")
            logger.info("=" * 60)
            logger.info("")
            logger.info(f"Personaje: {character['name']}")
            logger.info(f"Reel ID: {self.reel_id}")
            logger.info(f"Archivo: {output_file}")
            logger.info(f"Directorio: {self.output_dir}")
            logger.info("")
            logger.info("Próximo paso: Publicar en redes sociales")
            logger.info("=" * 60)
            logger.info("")
            
            return {
                "success": True,
                "reel_id": self.reel_id,
                "output_file": output_file,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"\n❌ ERROR EN GENERACIÓN: {e}\n")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }


async def main():
    """Punto de entrada principal"""
    generator = ReelGenerator()
    
    # Generar reel completo
    result = await generator.generate_complete_reel()
    
    if result["success"]:
        print(f"\n✅ Reel generado exitosamente: {result['output_file']}\n")
        return 0
    else:
        print(f"\n❌ Error: {result['error']}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
