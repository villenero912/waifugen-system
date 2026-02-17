#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Karaoke Generator - Simplified Phase 1 System

This module creates karaoke videos with:
- Static high-quality avatar
- Dynamic text effects (no lip-sync required)
- Free music from Pixabay API
- Eye-catching visual effects for retention
- Zero API cost (no A2E needed)

Author: Reels Automation System
Version: 1.0.0 - Phase 1 Optimized
"""

import json
import os
import random
import hashlib
import subprocess
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TextEffect(Enum):
    """Karaoke text effect types."""
    PULSE = "pulse"           # Scale up/down with beat
    GLOW = "glow"             # Glowing text effect
    SLIDE = "slide"           # Slide in from side
    FADE = "fade"             # Fade in/out
    TYPEWRITER = "typewriter" # Typewriter effect
    RAINBOW = "rainbow"       # Color cycling
    SPARKLE = "sparkle"       # Sparkle particles
    WAVE = "wave"             # Wavy text
    HIGHLIGHT = "highlight"   # Highlight background


class TextStyle(Enum):
    """Predefined text styles for maximum engagement."""
    TIKTOK_TRENDING = "tiktok_trending"   # Bold, colorful, punchy
    INSTAGRAM_CLEAN = "instagram_clean"   # Minimal, elegant
    YOUTUBE_THUMB = "youtube_thumb"       # High contrast, readable
    TIKTOK_INTENSE = "tiktok_intense"     # High energy, dynamic


@dataclass
class LyricLine:
    """Represents a single lyric line with timing."""
    text: str
    start_time: float
    end_time: float
    effect: TextEffect = TextEffect.PULSE
    font_size: int = 72
    font_color: str = "#FFFFFF"
    stroke_color: str = "#FF69B4"
    position: Tuple[float, float] = (0.5, 0.7)  # Center, 70% down
    scale_factor: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "effect": self.effect.value,
            "font_size": self.font_size,
            "font_color": self.font_color,
            "stroke_color": self.stroke_color,
            "position": {"x": self.position[0], "y": self.position[1]},
            "scale_factor": self.scale_factor
        }


@dataclass
class KaraokeConfig:
    """Configuration for karaoke video generation."""
    # Video settings
    width: int = 1080
    height: int = 1920
    fps: int = 30
    duration: float = 30.0
    
    # Avatar settings
    avatar_path: str = ""
    avatar_scale: float = 0.8
    avatar_position: Tuple[float, float] = (0.5, 0.4)
    
    # Text settings
    text_style: TextStyle = TextStyle.TIKTOK_TRENDING
    font_path: str = ""
    font_size: int = 72
    font_color: str = "#FFFFFF"
    stroke_color: str = "#000000"
    stroke_width: int = 3
    
    # Effect settings
    background_color: str = "#1a1a2e"
    enable_glow: bool = True
    glow_intensity: float = 0.8
    enable_particles: bool = True
    
    # Output settings
    output_path: str = ""
    quality: str = "high"


@dataclass
class KaraokeResult:
    """Result of karaoke video generation."""
    success: bool
    video_path: str = ""
    thumbnail_path: str = ""
    duration: float = 0.0
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "video_path": self.video_path,
            "thumbnail_path": self.thumbnail_path,
            "duration": self.duration,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


class SimpleKaraokeGenerator:
    """
    Simplified karaoke generator for Phase 1.
    
    Creates engaging karaoke videos with:
    - Static avatar (no lip-sync cost)
    - Dynamic text effects
    - Free music integration
    - Zero API costs
    """
    
    # Text style configurations for engagement
    TEXT_STYLES = {
        TextStyle.TIKTOK_TRENDING: {
            "font_color": "#FFFFFF",
            "stroke_color": "#FF0050",  # TikTok red
            "stroke_width": 4,
            "font_size": 80,
            "effect": TextEffect.PULSE,
            "glow_color": "#FF0050",
            "glow_intensity": 1.0,
            "uppercase": True,
            "bold": True
        },
        TextStyle.INSTAGRAM_CLEAN: {
            "font_color": "#FFFFFF",
            "stroke_color": "#833AB4",  # Instagram purple
            "stroke_width": 2,
            "font_size": 64,
            "effect": TextEffect.FADE,
            "glow_color": "#833AB4",
            "glow_intensity": 0.5,
            "uppercase": False,
            "bold": False
        },
        TextStyle.YOUTUBE_THUMB: {
            "font_color": "#FFFF00",
            "stroke_color": "#FF0000",
            "stroke_width": 6,
            "font_size": 96,
            "effect": TextEffect.GLOW,
            "glow_color": "#FF0000",
            "glow_intensity": 1.5,
            "uppercase": True,
            "bold": True
        },
        TextStyle.TIKTOK_INTENSE: {
            "font_color": "#00F5FF",
            "stroke_color": "#FF00FF",
            "stroke_width": 3,
            "font_size": 88,
            "effect": TextEffect.SPARKLE,
            "glow_color": "#00F5FF",
            "glow_intensity": 1.2,
            "uppercase": True,
            "bold": True
        }
    }
    
    def __init__(self, config: KaraokeConfig = None):
        """
        Initialize the karaoke generator.
        
        Args:
            config: Karaoke configuration
        """
        self.config = config or KaraokeConfig()
        
        # Directories
        self.output_dir = os.environ.get(
            "KARAOKE_OUTPUT_DIR",
            "/workspace/karaoke_output"
        )
        self.tmp_dir = os.environ.get(
            "KARAOKE_TMP_DIR",
            "/workspace/karaoke_tmp"
        )
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.tmp_dir, exist_ok=True)
        
        # Initialize music client
        self.music_client = None
        self._init_music_client()
        
        logger.info("SimpleKaraokeGenerator initialized")
        logger.info(f"  - Output: {self.output_dir}")
        logger.info(f"  - Style: {self.config.text_style.value}")
    
    def _init_music_client(self):
        """Initialize free music client."""
        try:
            from music_generator import FreeMusicAPIClient
            api_key = os.environ.get("PIXABAY_API_KEY", "")
            self.music_client = FreeMusicAPIClient(api_key=api_key) if api_key else None
            if self.music_client:
                logger.info("  - Free music API connected")
        except Exception as e:
            logger.warning(f"Music client init failed: {e}")
            self.music_client = None
    
    def _get_style_settings(self) -> Dict[str, Any]:
        """Get settings for current text style."""
        return self.TEXT_STYLES.get(
            self.config.text_style, 
            self.TEXT_STYLES[TextStyle.TIKTOK_TRENDING]
        ).copy()
    
    def _parse_lyrics(self, lyrics_text: str, duration: float) -> List[LyricLine]:
        """
        Parse lyrics text into timed lines.
        
        Args:
            lyrics_text: Lyrics with newlines
            duration: Total video duration
            
        Returns:
            List of LyricLine objects
        """
        lines = lyrics_text.strip().split('\n')
        lines = [l.strip() for l in lines if l.strip()]
        
        if not lines:
            return []
        
        # Calculate timing for each line
        line_duration = duration / len(lines)
        
        lyrics = []
        for i, line_text in enumerate(lines):
            style = self._get_style_settings()
            
            # Uppercase if style requires
            if style.get("uppercase"):
                line_text = line_text.upper()
            
            lyrics.append(LyricLine(
                text=line_text,
                start_time=i * line_duration,
                end_time=(i + 1) * line_duration,
                effect=style.get("effect", TextEffect.PULSE),
                font_size=style.get("font_size", 72),
                font_color=style.get("font_color", "#FFFFFF"),
                stroke_color=style.get("stroke_color", "#FF69B4"),
                position=(0.5, 0.65),
                scale_factor=1.0
            ))
        
        return lyrics
    
    def _generate_ass_header(self, width: int, height: int, fps: int) -> str:
        """Generate ASS subtitle file header."""
        return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{self.config.font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    def _time_to_ass(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.cc)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"
    
    def _generate_ass_karaoke(
        self, 
        lyrics: List[LyricLine], 
        width: int, 
        height: int,
        fps: int
    ) -> str:
        """Generate ASS subtitle file with karaoke effects."""
        
        style = self._get_style_settings()
        glow_color = style.get("glow_color", "#FF69B4")
        glow_intensity = style.get("glow_intensity", 1.0)
        
        # Convert glow color to ASS format
        if glow_color.startswith("#"):
            r, g, b = glow_color[1:3], glow_color[3:5], glow_color[5:7]
            glow_ass = f"&H00{b}{g}{r}"
        
        content = self._generate_ass_header(width, height, fps)
        
        for line in lyrics:
            start = self._time_to_ass(line.start_time)
            end = self._time_to_ass(line.end_time)
            
            # Position calculation
            pos_x = int(line.position[0] * width)
            pos_y = int(line.position[1] * height)
            
            # Generate effect-specific ASS tags
            effect_tags = self._generate_effect_tags(line.effect, glow_ass, glow_intensity, line.scale_factor)
            
            # Text with stroke (outline) for readability
            text = f"{{\\pos({pos_x},{pos_y})}{effect_tags}}}{line.text}"
            
            content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"
        
        return content
    
    def _generate_effect_tags(
        self, 
        effect: TextEffect, 
        glow_color: str,
        intensity: float,
        scale: float
    ) -> str:
        """Generate ASS tags for text effect."""
        
        tags = ""
        
        # Glow effect
        if self.config.enable_glow:
            blur = int(5 * intensity)
            tags += f"\\blur{blur}"
        
        # Effect-specific transformations
        if effect == TextEffect.PULSE:
            # Scale animation handled by clip in video editor
            tags += "\\fscx120\\fscy120"
        elif effect == TextEffect.GLOW:
            tags += f"\\3a&H40\\3c{glow_color}"
        elif effect == TextEffect.SLIDE:
            tags += "\\move(0,1080,540,648,0,500)"
        elif effect == TextEffect.WAVE:
            tags += "\\frz10"
        
        # Color styling
        tags += f"\\c&H00FFFFFF\\3c&H000000"
        
        return tags
    
    def _create_lyrics_overlay_video(
        self, 
        lyrics: List[LyricLine],
        output_path: str,
        width: int,
        height: int,
        fps: int
    ) -> bool:
        """
        Create video overlay with lyrics using FFmpeg.
        
        Args:
            lyrics: Lyric lines with timing
            output_path: Output video path
            width: Video width
            height: Video height
            fps: Frame rate
            
        Returns:
            True if successful
        """
        # Generate ASS file
        ass_path = os.path.join(self.tmp_dir, f"lyrics_{hash(output_path) % 100000}.ass")
        ass_content = self._generate_ass_karaoke(lyrics, width, height, fps)
        
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        # Create blank video with subtitles
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c={self.config.background_color}:s={width}x{height}:d={self.config.duration}:r={fps}",
                "-vf", f"ass={ass_path}",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "23",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Lyrics overlay created: {output_path}")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating lyrics overlay: {e}")
            return False
        finally:
            if os.path.exists(ass_path):
                os.remove(ass_path)
    
    def _create_final_video(
        self,
        avatar_path: str,
        lyrics_overlay_path: str,
        music_path: str,
        output_path: str,
        width: int,
        height: int,
        fps: int
    ) -> bool:
        """
        Combine avatar and lyrics into final video.
        
        Args:
            avatar_path: Avatar image path
            lyrics_overlay_path: Lyrics video overlay path
            music_path: Background music path
            output_path: Final output path
            width: Video width
            height: Video height
            fps: Frame rate
            
        Returns:
            True if successful
        """
        try:
            # Scale avatar to appropriate size
            scaled_avatar = os.path.join(self.tmp_dir, f"avatar_scaled_{hash(output_path) % 100000}.png")
            
            scale_cmd = [
                "ffmpeg", "-y",
                "-i", avatar_path,
                "-vf", f"scale={int(width * 0.6)}:{int(width * 0.6 * 1.5)}:force_original_aspect_ratio=decrease",
                "-q:v", "2",
                scaled_avatar
            ]
            
            subprocess.run(scale_cmd, capture_output=True, text=True)
            
            # Combine avatar + lyrics + music
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", scaled_avatar,
                "-i", lyrics_overlay_path,
                "-i", music_path,
                "-filter_complex",
                f"[0:v]scale={width}x{height},setpts=PTS-STARTPTS[bg];"
                f"[1:v]setpts=PTS-STARTPTS[lyrics];"
                f"[bg][lyrics]overlay=(W-w)/2:(H-h)*0.3:format=auto[composite];"
                f"[composite][2:a]amix=inputs=1:duration=first[outv][outa]",
                "-map", "[outv]",
                "-map", "[outa]",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "20",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Final video created: {output_path}")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating final video: {e}")
            return False
        finally:
            # Cleanup temp files
            if 'scaled_avatar' in dir() and os.path.exists(scaled_avatar):
                os.remove(scaled_avatar)
    
    async def generate_karaoke(
        self,
        lyrics_text: str,
        music_query: str = "happy anime",
        avatar_path: str = None,
        output_filename: str = None
    ) -> KaraokeResult:
        """
        Generate a complete karaoke video.
        
        Args:
            lyrics_text: Song lyrics (one line per lyric)
            music_query: Query for free music search
            avatar_path: Path to avatar image (auto-generated if None)
            output_filename: Custom output filename
            
        Returns:
            KaraokeResult with video path and details
        """
        start_time = datetime.now()
        
        logger.info("Starting karaoke generation...")
        
        # Generate output filename
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"karaoke_{timestamp}"
        
        output_path = os.path.join(self.output_dir, f"{output_filename}.mp4")
        
        # Parse lyrics
        lyrics = self._parse_lyrics(lyrics_text, self.config.duration)
        
        if not lyrics:
            return KaraokeResult(
                success=False,
                error_message="No lyrics provided"
            )
        
        logger.info(f"Parsed {len(lyrics)} lyric lines")
        
        # Get or create avatar
        if not avatar_path:
            avatar_path = await self._generate_or_get_avatar()
        
        if not avatar_path or not os.path.exists(avatar_path):
            return KaraokeResult(
                success=False,
                error_message="Avatar not available"
            )
        
        # Get music
        music_path = await self._get_music(music_query, self.config.duration)
        
        if not music_path:
            return KaraokeResult(
                success=False,
                error_message="Music not available"
            )
        
        # Create lyrics overlay
        lyrics_overlay_path = os.path.join(self.tmp_dir, f"lyrics_{hash(output_filename)}.mp4")
        
        success = self._create_lyrics_overlay_video(
            lyrics=lyrics,
            output_path=lyrics_overlay_path,
            width=self.config.width,
            height=self.config.height,
            fps=self.config.fps
        )
        
        if not success:
            return KaraokeResult(
                success=False,
                error_message="Failed to create lyrics overlay"
            )
        
        # Create final video
        success = self._create_final_video(
            avatar_path=avatar_path,
            lyrics_overlay_path=lyrics_overlay_path,
            music_path=music_path,
            output_path=output_path,
            width=self.config.width,
            height=self.config.height,
            fps=self.config.fps
        )
        
        if not success:
            return KaraokeResult(
                success=False,
                error_message="Failed to create final video"
            )
        
        # Get video duration
        duration = self._get_video_duration(output_path)
        
        # Create thumbnail
        thumbnail_path = self._create_thumbnail(output_path, avatar_path)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Karaoke generated in {elapsed:.1f}s: {output_path}")
        
        return KaraokeResult(
            success=True,
            video_path=output_path,
            thumbnail_path=thumbnail_path,
            duration=duration,
            metadata={
                "lyrics_count": len(lyrics),
                "music_query": music_query,
                "style": self.config.text_style.value,
                "generation_time": elapsed
            }
        )
    
    async def _generate_or_get_avatar(self) -> str:
        """Generate or get avatar image."""
        # Try to use existing avatar or generate new one
        avatar_path = os.path.join(self.output_dir, "avatars", "default_avatar.png")
        os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
        
        if not os.path.exists(avatar_path):
            # Try to generate using existing avatar generator
            try:
                from avatar_generator import AvatarGenerator
                generator = AvatarGenerator()
                result = await generator.generate_avatar("default", "default")
                if result.success:
                    avatar_path = result.image_path
            except Exception as e:
                logger.warning(f"Avatar generation failed: {e}")
        
        return avatar_path if os.path.exists(avatar_path) else ""
    
    async def _get_music(self, query: str, duration: float) -> str:
        """Get music file from free sources."""
        # Try Pixabay first
        if self.music_client:
            try:
                tracks = await self.music_client.search_and_download(
                    query=query,
                    category="music",
                    limit=1
                )
                if tracks:
                    return tracks[0].file_path
            except Exception as e:
                logger.warning(f"Music download failed: {e}")
        
        # Fallback: create silent audio placeholder
        silent_path = os.path.join(self.tmp_dir, f"silent_{int(duration)}.wav")
        if not os.path.exists(silent_path):
            try:
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "lavfi",
                    "-i", f"sine=frequency=440:duration={duration}",
                    "-af", "adelay=0|0,volume=0.3",
                    silent_path
                ]
                subprocess.run(cmd, capture_output=True, text=True)
            except Exception as e:
                logger.error(f"Silent audio creation failed: {e}")
        
        return silent_path
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception:
            return 0.0
    
    def _create_thumbnail(self, video_path: str, avatar_path: str) -> str:
        """Create thumbnail from video."""
        thumb_path = video_path.replace(".mp4", "_thumb.jpg")
        
        try:
            # Extract frame from video
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-ss", "00:00:01",
                "-vframes", "1",
                "-q:v", "2",
                thumb_path
            ]
            subprocess.run(cmd, capture_output=True, text=True)
            
            if os.path.exists(thumb_path):
                return thumb_path
                
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
        
        return ""
    
    async def close(self):
        """Clean up resources."""
        if self.music_client:
            await self.music_client.close()


def create_default_config() -> KaraokeConfig:
    """Create default karaoke config optimized for engagement."""
    return KaraokeConfig(
        width=1080,
        height=1920,
        fps=30,
        duration=30.0,
        text_style=TextStyle.TIKTOK_TRENDING,
        background_color="#1a1a2e",
        enable_glow=True,
        glow_intensity=1.0,
        enable_particles=True
    )


async def main():
    """Demo function for karaoke generator."""
    print("=" * 60)
    print("🎤 SIMPLE KARAOKE GENERATOR - Phase 1")
    print("   Zero API Cost • High Engagement • Static Avatar")
    print("=" * 60)
    
    # Initialize
    config = create_default_config()
    generator = SimpleKaraokeGenerator(config)
    
    # Sample lyrics (can be replaced with real lyrics)
    sample_lyrics = """
    Hello darkness my old friend
    I've come to talk with you again
    Because a vision softly creeping
    Left its seeds while I was sleeping
    And the vision that was planted in my brain
    Still remains
    Within the sound of silence
    """
    
    print("\n📝 Sample lyrics loaded (Simon & Garfurel - Sound of Silence)")
    print(f"   Lines: {len(sample_lyrics.strip().split(chr(10)))}")
    
    # Generate karaoke
    print("\n🎬 Generating karaoke video...")
    
    result = await generator.generate_karaoke(
        lyrics_text=sample_lyrics,
        music_query="sad piano emotional",
        output_filename="demo_karaoke"
    )
    
    if result.success:
        print(f"\n✅ SUCCESS!")
        print(f"   Video: {result.video_path}")
        print(f"   Duration: {result.duration:.1f}s")
        print(f"   Thumbnail: {result.thumbnail_path}")
        print(f"   Generation time: {result.metadata.get('generation_time', 0):.1f}s")
    else:
        print(f"\n❌ FAILED: {result.error_message}")
    
    # Cleanup
    await generator.close()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    import sys
    asyncio.run(main())
