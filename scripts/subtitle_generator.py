#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle Generator - Subtitle Generator for Videos

This module is responsible for generating, formatting, and processing
subtitles for the generated videos.

Main features:
- SRT and VTT subtitle generation
- Platform-specific subtitle styling
- Timing and audio synchronization
- Karaoke and text effects
- Positioning and animation

Author: Reels Automation System
Version: 1.0.0
"""

import json
import os
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SubtitleFormat(Enum):
    """Subtitle format enumeration."""
    SRT = "srt"
    VTT = "vtt"
    ASS = "ass"
    SBV = "sbv"


class SubtitleStyle(Enum):
    """Subtitle style enumeration."""
    MODERN = "modern"
    CINEMATIC = "cinematic"
    GAMING = "gaming"
    KARAOKE = "karaoke"
    IDOL = "idol"
    SOCIAL = "social"


class AnimationType(Enum):
    """Text animation type enumeration."""
    FADE = "fade"
    TYPEWRITER = "typewriter"
    KARAOKE = "karaoke"
    SLIDE = "slide"
    PULSE = "pulse"
    HIGHLIGHT = "highlight"
    NONE = "none"


@dataclass
class SubtitleLine:
    """Represents a subtitle line."""
    index: int
    start_time: float
    end_time: float
    text: str
    style: SubtitleStyle = SubtitleStyle.MODERN
    animation: AnimationType = AnimationType.FADE
    position: Tuple[float, float] = (0.5, 0.9)  # Normalized (x, y)
    font_size: int = 32
    font_color: str = "#FFFFFF"
    background_color: str = "#00000080"
    font_name: str = "Noto Sans CJK SC"
    bold: bool = False
    italic: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the line to dictionary."""
        return {
            "index": self.index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "text": self.text,
            "style": self.style.value,
            "animation": self.animation.value,
            "position": {"x": self.position[0], "y": self.position[1]},
            "font_size": self.font_size,
            "font_color": self.font_color,
            "background_color": self.background_color,
            "font_name": self.font_name,
            "bold": self.bold,
            "italic": self.italic
        }


@dataclass
class SubtitleTrack:
    """Represents a complete subtitle track."""
    id: str
    format: SubtitleFormat
    language: str
    lines: List[SubtitleLine]
    style_config: Dict[str, Any]
    video_duration: float
    generated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the track to dictionary."""
        return {
            "id": self.id,
            "format": self.format.value,
            "language": self.language,
            "lines": [line.to_dict() for line in self.lines],
            "style_config": self.style_config,
            "video_duration": self.video_duration,
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata
        }


class SubtitleGenerator:
    """
    Main class for subtitle generation.
    
    Handles subtitle creation in multiple formats,
    styles, and animations for different platforms.
    """
    
    # Default style configurations
    STYLE_CONFIGS = {
        "modern": {
            "font_size": 32,
            "font_color": "#FFFFFF",
            "background_color": "#00000080",
            "font_name": "Noto Sans CJK SC",
            "position": (0.5, 0.85),
            "animation": "fade",
            "bold": False,
            "italic": False
        },
        "cinematic": {
            "font_size": 28,
            "font_color": "#FFFFFF",
            "background_color": "transparent",
            "font_name": "Noto Sans CJK SC",
            "position": (0.5, 0.9),
            "animation": "fade",
            "bold": False,
            "italic": True
        },
        "gaming": {
            "font_size": 30,
            "font_color": "#00FF00",
            "background_color": "#000000",
            "font_name": "Noto Sans CJK SC",
            "position": (0.5, 0.8),
            "animation": "highlight",
            "bold": True,
            "italic": False
        },
        "karaoke": {
            "font_size": 36,
            "font_color": "#FF69B4",
            "background_color": "#00000080",
            "font_name": "Noto Sans CJK SC",
            "position": (0.5, 0.85),
            "animation": "karaoke",
            "bold": True,
            "italic": False
        },
        "idol": {
            "font_size": 26,
            "font_color": "#FFFFFF",
            "background_color": "#FF69B480",
            "font_name": "Noto Sans CJK SC",
            "position": (0.5, 0.15),
            "animation": "slide",
            "bold": False,
            "italic": False
        },
        "social": {
            "font_size": 28,
            "font_color": "#FFFFFF",
            "background_color": "#000000",
            "font_name": "Noto Sans CJK SC",
            "position": (0.5, 0.82),
            "animation": "fade",
            "bold": False,
            "italic": False
        }
    }
    
    # Font configuration with fallbacks
    FONTS = {
        "primary": "Noto Sans CJK SC",
        "primary_bold": "Noto Sans CJK SC Bold",
        "fallback": "Arial"
    }
    
    # Font verification status
    _FONTS_AVAILABLE = None
    
    def __init__(self, config_base_path: str = None):
        """
        Initialize the subtitle generator.
        
        Args:
            config_base_path: Base path to configuration files
        """
        if config_base_path is None:
            possible_paths = [
                "/workspace/PROJECT_ORGANIZATION/PHASE_1_REELS/configs",
                "/workspace/clean_project/config",
                "./configs",
                "../configs"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    config_base_path = path
                    break
        
        self.config_base_path = config_base_path
        self.templates_config = {}
        self.quality_config = {}
        
        # Output directory
        self.output_dir = os.environ.get(
            "SUBTITLE_OUTPUT_DIR", 
            "/workspace/generated_subtitles"
        )
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load configurations
        self._load_configs()
        
        # Verify fonts availability
        self._verify_fonts()
        
        logger.info(f"SubtitleGenerator initialized")
        logger.info(f"  - Output directory: {self.output_dir}")
        logger.info(f"  - Font verification: {'✓ Passed' if self._FONTS_AVAILABLE else '⚠ Using fallbacks'}")
    
    def _verify_fonts(self) -> bool:
        """
        Verifies if professional fonts are available and sets fallbacks.
        
        Returns:
            True if all fonts are available, False otherwise
        """
        import subprocess
        
        required_fonts = ["Noto Sans CJK SC", "Noto Sans CJK SC Bold"]
        fallback_fonts = ["Arial", "DejaVu Sans"]
        
        available = []
        
        # Check required fonts
        for font in required_fonts:
            try:
                cmd = ["fc-list", f"\"{font}\"", "--format=%{family}\\n"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and font in result.stdout:
                    available.append(font)
            except Exception:
                continue
        
        # Check for fallbacks
        fallback_available = False
        for font in fallback_fonts:
            try:
                cmd = ["fc-list", f"\"{font}\"", "--format=%{family}\\n"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and font in result.stdout:
                    fallback_available = True
                    break
            except Exception:
                continue
        
        if available:
            self._FONTS_AVAILABLE = True
            logger.info(f"✓ Professional fonts verified: {available}")
        else:
            self._FONTS_AVAILABLE = False
            if fallback_available:
                logger.warning(f"⚠ Professional fonts unavailable, using fallbacks")
            else:
                logger.error(f"⚠ No fonts available!")
        
        return self._FONTS_AVAILABLE
    
    def _get_style_config(self, style_name: str) -> Dict[str, Any]:
        """
        Gets style configuration by name with fallback support.
        
        Args:
            style_name: Style name
            
        Returns:
            Style configuration
        """
        style_config = self.STYLE_CONFIGS.get(style_name, self.STYLE_CONFIGS["modern"]).copy()
        
        # Apply font fallback if needed
        if not self._FONTS_AVAILABLE:
            font_name = style_config.get("font_name", "Arial")
            if "Noto Sans CJK SC" in font_name:
                style_config["font_name"] = "Arial"
                logger.debug(f"Font fallback applied for style '{style_name}'")
        
        return style_config
    
    def _load_configs(self) -> None:
        """Load configurations from JSON files."""
        config_paths = {
            "templates_config": os.path.join(self.config_base_path, "reel_templates.json"),
            "quality_config": os.path.join(self.config_base_path, "quality_config.json")
        }
        
        for config_name, config_path in config_paths.items():
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        setattr(self, config_name, json.load(f))
                    logger.info(f"✓ Configuration loaded: {config_name}")
                else:
                    logger.warning(f"⚠ Configuration not found: {config_path}")
                    setattr(self, config_name, {})
            except Exception as e:
                logger.error(f"✗ Error loading {config_name}: {e}")
                setattr(self, config_name, {})
    
    def _get_subtitle_config_from_template(self, template_id: str) -> Dict[str, Any]:
        """
        Extracts subtitle configuration from a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            Subtitle configuration
        """
        templates = self.templates_config.get("templates", {})
        template = templates.get(template_id, {})
        
        return template.get("subtitles", {})
    
    def _get_style_config(self, style_name: str) -> Dict[str, Any]:
        """
        Gets style configuration by name.
        
        Args:
            style_name: Style name
            
        Returns:
            Style configuration
        """
        return self.STYLE_CONFIGS.get(style_name, self.STYLE_CONFIGS["modern"]).copy()
    
    def _merge_style_configs(self, template_config: Dict[str, Any],
                             style_name: str) -> Dict[str, Any]:
        """
        Merges template configuration with default style.
        
        Args:
            template_config: Template configuration
            style_name: Style name
            
        Returns:
            Merged configuration
        """
        style_config = self._get_style_config(style_name)
        
        # Override with template values
        if "font_size" in template_config:
            style_config["font_size"] = template_config["font_size"]
        if "color" in template_config:
            style_config["font_color"] = template_config["color"]
        if "background" in template_config:
            style_config["background_color"] = template_config["background"]
        if "position" in template_config:
            pos = template_config["position"]
            if pos == "bottom":
                style_config["position"] = (0.5, 0.85)
            elif pos == "bottom_third":
                style_config["position"] = (0.5, 0.75)
            elif pos == "center":
                style_config["position"] = (0.5, 0.5)
            elif pos == "top":
                style_config["position"] = (0.5, 0.15)
        
        return style_config
    
    def _calculate_line_duration(self, text: str, style_config: Dict[str, Any]) -> float:
        """
        Calculates approximate duration of a subtitle line.
        
        Args:
            text: Subtitle text
            style_config: Style configuration
            
        Returns:
            Duration in seconds
        """
        # Approximate characters per second
        chars_per_second = 15
        min_duration = 1.5
        max_duration = 6.0
        
        # Adjust for animation
        animation = style_config.get("animation", "fade")
        if animation == "typewriter":
            chars_per_second = 10
        
        duration = len(text) / chars_per_second
        duration = max(min_duration, min(duration, max_duration))
        
        return round(duration, 1)
    
    def generate_subtitles_from_script(self, script, template_id: str = "kawaii_dance",
                                        format: SubtitleFormat = SubtitleFormat.SRT,
                                        language: str = "es") -> SubtitleTrack:
        """
        Generates subtitles from a script.
        
        Args:
            script: Script with dialogue lines
            template_id: Template ID
            format: Output format
            language: Subtitle language
            
        Returns:
            SubtitleTrack with generated subtitles
        """
        subtitle_config = self._get_subtitle_config_from_template(template_id)
        style_name = subtitle_config.get("style", "modern")
        style_config = self._merge_style_configs(subtitle_config, style_name)
        
        lines = []
        current_time = 0.0
        
        for i, script_line in enumerate(script.lines, 1):
            # Get text for subtitle
            subtitle_text = script_line.subtitle_text or script_line.text
            
            # Calculate duration
            duration = self._calculate_line_duration(subtitle_text, style_config)
            
            # Create subtitle line
            subtitle_line = SubtitleLine(
                index=i,
                start_time=current_time,
                end_time=current_time + duration,
                text=subtitle_text,
                style=SubtitleStyle(style_name),
                animation=AnimationType(style_config.get("animation", "fade")),
                position=style_config["position"],
                font_size=style_config["font_size"],
                font_color=style_config["font_color"],
                background_color=style_config["background_color"],
                font_name=style_config["font_name"],
                bold=style_config.get("bold", False),
                italic=style_config.get("italic", False)
            )
            
            lines.append(subtitle_line)
            current_time += duration
        
        # Calculate total video duration
        video_duration = current_time
        
        track = SubtitleTrack(
            id=f"subs_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}",
            format=format,
            language=language,
            lines=lines,
            style_config=style_config,
            video_duration=video_duration,
            generated_at=datetime.now(),
            metadata={
                "template_id": template_id,
                "script_title": script.title
            }
        )
        
        logger.info(f"✓ Subtitles generated: {len(lines)} lines")
        
        return track
    
    def _format_srt_time(self, seconds: float) -> str:
        """Formats time to SRT format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """Formats time to VTT format (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def export_srt(self, track: SubtitleTrack, output_path: str = None) -> str:
        """
        Exports subtitles to SRT format.
        
        Args:
            track: SubtitleTrack to export
            output_path: File path (optional)
            
        Returns:
            Exported file path
        """
        if output_path is None:
            output_path = os.path.join(
                self.output_dir, 
                f"{track.id}.srt"
            )
        
        srt_content = ""
        
        for line in track.lines:
            start = self._format_srt_time(line.start_time)
            end = self._format_srt_time(line.end_time)
            
            srt_content += f"{line.index}\n"
            srt_content += f"{start} --> {end}\n"
            srt_content += f"{line.text}\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        logger.info(f"✓ SRT subtitles exported: {output_path}")
        
        return output_path
    
    def export_vtt(self, track: SubtitleTrack, output_path: str = None) -> str:
        """
        Exports subtitles to VTT format.
        
        Args:
            track: SubtitleTrack to export
            output_path: File path (optional)
            
        Returns:
            Exported file path
        """
        if output_path is None:
            output_path = os.path.join(
                self.output_dir, 
                f"{track.id}.vtt"
            )
        
        vtt_content = "WEBVTT\n\n"
        
        for line in track.lines:
            start = self._format_vtt_time(line.start_time)
            end = self._format_vtt_time(line.end_time)
            
            vtt_content += f"{line.index}\n"
            vtt_content += f"{start} --> {end}\n"
            vtt_content += f"{line.text}\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(vtt_content)
        
        logger.info(f"✓ VTT subtitles exported: {output_path}")
        
        return output_path
    
    def export_ass(self, track: SubtitleTrack, output_path: str = None) -> str:
        """
        Exports subtitles to ASS format (Advanced Substation Alpha).
        
        Args:
            track: SubtitleTrack to export
            output_path: File path (optional)
            
        Returns:
            Exported file path
        """
        if output_path is None:
            output_path = os.path.join(
                self.output_dir, 
                f"{track.id}.ass"
            )
        
        # ASS Header
        ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""
        
        # Default style
        style = track.style_config
        font_color = self._convert_color_to_ass(style["font_color"])
        outline_color = "#000000"
        bg_color = self._convert_color_to_ass(style["background_color"], alpha=True)
        
        alignment_map = {
            (0.5, 0.85): 2,  # Bottom center
            (0.5, 0.75): 2,  # Bottom third
            (0.5, 0.5): 5,   # Center
            (0.5, 0.15): 8   # Top center
        }
        alignment = alignment_map.get(style["position"], 2)
        
        bold = -1 if style.get("bold") else 0
        italic = -1 if style.get("italic") else 0
        
        ass_content += f"""Default,{style['font_name']},{style['font_size']},{font_color},&H000000FF,{outline_color},{bg_color},{bold},{italic},0,100,100,0,0,1,2,0,{alignment},20,20,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # Subtitle events
        for line in track.lines:
            start = self._format_ass_time(line.start_time)
            end = self._format_ass_time(line.end_time)
            
            # Position
            pos_x = int(line.position[0] * 1920)
            pos_y = int(line.position[1] * 1080)
            
            ass_content += (
                f"Dialogue: 0,{start},{end},Default,,0,0,0,,"
                f"{{\\pos({pos_x},{pos_y})}}{line.text}\n"
            )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        logger.info(f"✓ ASS subtitles exported: {output_path}")
        
        return output_path
    
    def _format_ass_time(self, seconds: float) -> str:
        """Formats time to ASS format (H:MM:SS.cc)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"
    
    def _convert_color_to_ass(self, color: str, alpha: bool = False) -> str:
        """
        Converts hex color to ASS format.
        
        Args:
            color: Color in hex format (#RRGGBB or #RRGGBBAA)
            alpha: If True, includes alpha channel
            
        Returns:
            Color in ASS format (&HBBGGRR)
        """
        if color.startswith("#"):
            color = color[1:]
        
        if len(color) == 6:
            r, g, b = color[0:2], color[2:4], color[4:6]
        elif len(color) == 8:
            r, g, b, a = color[0:2], color[2:4], color[4:6], color[6:8]
            if alpha:
                return f"&H{a}{b}{g}{r}"
        else:
            r, g, b = "FF", "FF", "FF"
        
        return f"&H00{b}{g}{r}"
    
    def export_json(self, track: SubtitleTrack, output_path: str = None) -> str:
        """
        Exports subtitles to JSON format.
        
        Args:
            track: SubtitleTrack to export
            output_path: File path (optional)
            
        Returns:
            Exported file path
        """
        if output_path is None:
            output_path = os.path.join(
                self.output_dir, 
                f"{track.id}.json"
            )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(track.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ JSON subtitles exported: {output_path}")
        
        return output_path
    
    def apply_karaoke_effect(self, track: SubtitleTrack, 
                             lyrics: List[Dict[str, str]]) -> SubtitleTrack:
        """
        Applies karaoke effect to subtitles.
        
        Args:
            track: Original SubtitleTrack
            lyrics: Lyrics with timing for each syllable
            
        Returns:
            SubtitleTrack with karaoke effect
        """
        # Modify lines for karaoke effect
        for line in track.lines:
            line.animation = AnimationType.KARAOKE
            line.style = SubtitleStyle.KARAOKE
            line.font_color = "#FF69B4"
        
        logger.info("✓ Karaoke effect applied")
        
        return track
    
    def adjust_timing(self, track: SubtitleTrack, offset: float = 0.0,
                       scale: float = 1.0) -> SubtitleTrack:
        """
        Adjusts subtitle timing.
        
        Args:
            track: Original SubtitleTrack
            offset: Offset in seconds (positive = later)
            scale: Duration scaling factor
            
        Returns:
            SubtitleTrack with adjusted timing
        """
        new_lines = []
        current_time = offset if offset > 0 else 0.0
        
        for line in track.lines:
            new_start = current_time
            new_duration = (line.end_time - line.start_time) * scale
            new_end = new_start + new_duration
            
            new_lines.append(SubtitleLine(
                index=line.index,
                start_time=new_start,
                end_time=new_end,
                text=line.text,
                style=line.style,
                animation=line.animation,
                position=line.position,
                font_size=line.font_size,
                font_color=line.font_color,
                background_color=line.background_color,
                font_name=line.font_name,
                bold=line.bold,
                italic=line.italic
            ))
            
            current_time = new_end
        
        track.lines = new_lines
        track.video_duration = current_time
        
        logger.info(f"✓ Timing adjusted: offset={offset}s, scale={scale}")
        
        return track
    
    def translate_subtitles(self, track: SubtitleTrack, 
                            target_language: str) -> SubtitleTrack:
        """
        Translates subtitles to another language.
        
        Args:
            track: Original SubtitleTrack
            target_language: Target language (ISO code)
            
        Returns:
            Translated SubtitleTrack
        """
        # Translation simulation
        # In production, would use a translation service
        
        language_names = {
            "es": "Spanish",
            "en": "English",
            "ja": "日本語",
            "pt": "Portuguese",
            "fr": "French"
        }
        
        logger.info(f"Translating subtitles to {language_names.get(target_language, target_language)}...")
        
        # In production, would call translation API here
        # For now, just mark the language
        
        track.language = target_language
        track.metadata["original_language"] = track.metadata.get("language", "es")
        track.metadata["translated"] = True
        
        logger.info("✓ Subtitles 'translated' (simulated)")
        
        return track
    
    def merge_subtitle_tracks(self, tracks: List[SubtitleTrack],
                               output_format: SubtitleFormat = SubtitleFormat.SRT) -> SubtitleTrack:
        """
        Combines multiple subtitle tracks.
        
        Args:
            tracks: List of SubtitleTrack to combine
            output_format: Output format
            
        Returns:
            Combined SubtitleTrack
        """
        combined_lines = []
        current_index = 1
        current_time = 0.0
        
        for track in tracks:
            for line in track.lines:
                # Adjust relative timing
                start = current_time
                duration = line.end_time - line.start_time
                end = start + duration
                
                combined_lines.append(SubtitleLine(
                    index=current_index,
                    start_time=start,
                    end_time=end,
                    text=line.text,
                    style=line.style,
                    animation=line.animation,
                    position=line.position,
                    font_size=line.font_size,
                    font_color=line.font_color,
                    background_color=line.background_color,
                    font_name=line.font_name,
                    bold=line.bold,
                    italic=line.italic
                ))
                
                current_index += 1
                current_time = end
        
        combined = SubtitleTrack(
            id=f"subs_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            format=output_format,
            language="multi",
            lines=combined_lines,
            style_config=tracks[0].style_config if tracks else {},
            video_duration=current_time,
            generated_at=datetime.now(),
            metadata={
                "merged": True,
                "original_tracks": [t.id for t in tracks]
            }
        )
        
        logger.info(f"✓ Tracks combined: {len(combined_lines)} total lines")
        
        return combined
    
    def get_available_styles(self) -> List[str]:
        """
        Gets the list of available styles.
        
        Returns:
            List of style names
        """
        return list(self.STYLE_CONFIGS.keys())
    
    def preview_subtitles(self, track: SubtitleTrack, 
                          max_lines: int = 5) -> str:
        """
        Generates a preview of the subtitles.
        
        Args:
            track: SubtitleTrack to preview
            max_lines: Maximum number of lines to display
            
        Returns:
            String with the preview
        """
        preview = f"=== SUBTITLE PREVIEW ({track.format.value.upper()}) ===\n"
        preview += f"Total duration: {track.video_duration:.1f}s | Lines: {len(track.lines)}\n"
        preview += f"Language: {track.language} | Style: {track.style_config}\n"
        preview += "-" * 50 + "\n"
        
        for line in track.lines[:max_lines]:
            start = self._format_srt_time(line.start_time)
            preview += f"[{start}] {line.text}\n"
        
        if len(track.lines) > max_lines:
            preview += f"... and {len(track.lines) - max_lines} more lines\n"
        
        return preview


def main():
    """Main function for Subtitle Generator demonstration."""
    print("=" * 60)
    print("📝 SUBTITLE GENERATOR - Subtitle Generator")
    print("=" * 60)
    
    # Initialize the generator
    generator = SubtitleGenerator()
    
    print("\n📊 Configuration:")
    print(f"  - Available styles: {generator.get_available_styles()}")
    print(f"  - Output directory: {generator.output_dir}")
    
    # Create a simulated script for demonstration
    class MockScript:
        def __init__(self):
            self.title = "Demo Script"
            self.lines = [
                type('Line', (), {
                    'subtitle_text': 'Hello! Welcome to this video.',
                    'text': 'Hello! Welcome to this video.'
                })(),
                type('Line', (), {
                    'subtitle_text': 'Today we will learn something incredible.',
                    'text': 'Today we will learn something incredible.'
                })(),
                type('Line', (), {
                    'subtitle_text': "Don't miss any detail.",
                    'text': "Don't miss any detail."
                })(),
                type('Line', (), {
                    'subtitle_text': 'Like and subscribe.',
                    'text': 'Like and subscribe.'
                })()
            ]
    
    script = MockScript()
    
    # Generate subtitles
    print("\n🎯 Generating subtitles...")
    track = generator.generate_subtitles_from_script(
        script=script,
        template_id="kawaii_dance",
        format=SubtitleFormat.SRT
    )
    
    print(f"\n📝 Generated Subtitles:")
    print(f"  ID: {track.id}")
    print(f"  Format: {track.format.value}")
    print(f"  Language: {track.language}")
    print(f"  Lines: {len(track.lines)}")
    print(f"  Duration: {track.video_duration:.1f}s")
    print(f"  Style: {track.style_config}")
    
    # Show preview
    preview = generator.preview_subtitles(track)
    print(f"\n👁 Preview:")
    print(preview)
    
    # Export in different formats
    print("💾 Exporting formats...")
    srt_path = generator.export_srt(track)
    print(f"  ✓ SRT: {srt_path}")
    
    vtt_path = generator.export_vtt(track)
    print(f"  ✓ VTT: {vtt_path}")
    
    ass_path = generator.export_ass(track)
    print(f"  ✓ ASS: {ass_path}")
    
    json_path = generator.export_json(track)
    print(f"  ✓ JSON: {json_path}")
    
    # Test timing adjustment
    print("\n⏱ Testing timing adjustment...")
    adjusted = generator.adjust_timing(track, offset=0.5, scale=1.0)
    print(f"  ✓ Timing adjusted: {adjusted.video_duration:.1f}s")
    
    print("\n" + "=" * 60)
    print("✨ Process completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
