
import os
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PixelationManager")

class PixelationStyle(Enum):
    """Available pixelation styles for censorship."""
    MOSAIC = "mosaic"  # Standard pixelation
    BLUR = "blur"  # Gaussian blur
    BLACK_BAR = "black_bar"  # Solid black bars
    GRADIENT_BLUR = "gradient_blur"  # Smooth gradient fade
    SOLID_COLOR = "solid_color"  # Solid color overlay

class RegionPolicy(Enum):
    """Content policy levels by region."""
    PERMISSIVE = 1  # Minimal censorship
    MODERATE = 2   # Mosaic/pixelation recommended
    RESTRICTIVE = 3  # Full blurring required

@dataclass
class CensorshipRegion:
    """Defines a region to be censored in a video."""
    x: int  # X coordinate (top-left)
    y: int  # Y coordinate (top-left)
    width: int  # Region width
    height: int  # Region height
    style: PixelationStyle = PixelationStyle.MOSAIC
    intensity: int = 10  # Pixelation intensity (1-20)

@dataclass
class RegionalPolicy:
    """Content policy configuration for a specific region."""
    region_code: str
    region_name: str
    policy_level: RegionPolicy
    required_styles: List[PixelationStyle]
    min_pixel_size: int  # Minimum mosaic pixel size
    coverage_requirements: str  # Description of coverage needs
    platform_notes: Dict[str, str]  # Platform-specific notes

# Regional policy configurations (Ported from JAV Project)
REGIONAL_POLICIES = {
    "JP": RegionalPolicy(
        region_code="JP",
        region_name="Japan",
        policy_level=RegionPolicy.RESTRICTIVE, # Ajustado a RESTRICTIVE para Fase 2 JAV
        required_styles=[PixelationStyle.MOSAIC],
        min_pixel_size=12, # Aumentado para cumplimiento legal estricto
        coverage_requirements="Genital area must be covered with mosaic per Art 175",
        platform_notes={
            "fanza": "Mosaic required for all explicit acts",
            "dmm": "Strict internal review for mosaic density"
        }
    ),
    "KR": RegionalPolicy(
        region_code="KR",
        region_name="South Korea",
        policy_level=RegionPolicy.RESTRICTIVE,
        required_styles=[PixelationStyle.MOSAIC],
        min_pixel_size=15,
        coverage_requirements="Full coverage required for genitals",
        platform_notes={"legal": "Strict obscenity laws"}
    ),
    "US": RegionalPolicy(
        region_code="US",
        region_name="United States",
        policy_level=RegionPolicy.PERMISSIVE,
        required_styles=[PixelationStyle.MOSAIC],
        min_pixel_size=5,
        coverage_requirements="Uncensored allowed on most adult platforms",
        platform_notes={"onlyfans": "No censorship required"}
    ),
    "DEFAULT": RegionalPolicy(
        region_code="DEFAULT",
        region_name="International",
        policy_level=RegionPolicy.MODERATE,
        required_styles=[PixelationStyle.MOSAIC],
        min_pixel_size=10,
        coverage_requirements="Standard mosaic for explicit content",
        platform_notes={}
    )
}

class PixelationManager:
    """
    Gestiona el pixelado automático por región para cumplir con las leyes de Japón (Fase 2).
    """
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def get_policy(self, region_code: str) -> RegionalPolicy:
        return REGIONAL_POLICIES.get(region_code.upper(), REGIONAL_POLICIES["DEFAULT"])

    def get_auto_regions(self, width: int, height: int, policy: RegionalPolicy) -> List[CensorshipRegion]:
        """
        Heurística para encontrar la zona genital basada en el plano (9:16).
        """
        regions = []
        if width == 720 and height == 1280 or (width < height): # Vertical
            # Zona pélvica estimada en planos de cuerpo entero/medios
            regions.append(CensorshipRegion(
                x=int(width * 0.3),
                y=int(height * 0.6),
                width=int(width * 0.4),
                height=int(height * 0.15),
                style=PixelationStyle.MOSAIC,
                intensity=policy.min_pixel_size
            ))
        return regions

    def apply_censorship(self, input_path: str, output_path: str, target_region: str):
        policy = self.get_policy(target_region)
        if policy.policy_level == RegionPolicy.PERMISSIVE and target_region != "JP":
            logger.info(f"Pasando video sin pixelar (Región: {target_region})")
            import shutil
            shutil.copy2(input_path, output_path)
            return True

        logger.info(f"🛡️ Aplicando Pixelado Regional ({target_region}) - Política: {policy.policy_level.name}")
        
        # Obtener dimensiones
        cmd_info = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", input_path]
        try:
            info_res = subprocess.run(cmd_info, capture_output=True, text=True)
            info = json.loads(info_res.stdout)
            width = info["streams"][0]["width"]
            height = info["streams"][0]["height"]
        except:
            width, height = 720, 1280

        regions = self.get_auto_regions(width, height, policy)
        if not regions:
            import shutil
            shutil.copy2(input_path, output_path)
            return True

        # Build FFmpeg Filter
        filters = []
        for i, r in enumerate(regions):
            pixel_size = r.intensity
            scaled_w = max(1, r.width // pixel_size)
            scaled_h = max(1, r.height // pixel_size)
            
            crop_filter = f"crop={r.width}:{r.height}:{r.x}:{r.y},scale={scaled_w}:{scaled_h},scale={r.width}:{r.height}:flags=neighbor"
            filters.append(f"[0:v]{crop_filter}[pixel{i}]")
        
        overlay_chain = "[0:v]"
        for i, r in enumerate(regions):
            new_chain = f"ovl{i}"
            filters.append(f"{overlay_chain}[pixel{i}]overlay={r.x}:{r.y}[{new_chain}]")
            overlay_chain = f"[{new_chain}]"
        
        filter_complex = ";".join(filters)
        
        cmd = [
            self.ffmpeg_path, "-y", "-i", input_path,
            "-filter_complex", filter_complex,
            "-map", overlay_chain, "-map", "0:a?",
            "-c:v", "libx264", "-crf", "18", "-preset", "slow",
            "-c:a", "copy",
            output_path
        ]
        
        logger.info(f"Ejecutando FFmpeg: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return True

if __name__ == "__main__":
    # Test simple
    manager = PixelationManager()
    # manager.apply_censorship("video_input.mp4", "video_jp_pixel.mp4", "JP")
