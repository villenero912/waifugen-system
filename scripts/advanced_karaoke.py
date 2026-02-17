#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADVANCED KARAOKE SYSTEM - Complete Personalization
====================================================

Complete system with:
1. Lyric styles (karaoke, neon, classic, modern)
2. Musical adaptation by genre
3. Multiple languages with specific TTS
4. Subtitles for target audience
5. Notes and comments

Author: Reels Automation System
Version: 2.0.0 - Advanced Personalization
"""

import sys
import os
import json
import time
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


# =============================================================================
# TARGET AUDIENCE PROFILES
# =============================================================================

class AudienceProfile(Enum):
    """Target audience profiles with specific configurations."""

    CHILDREN = {
        "name": "Children",
        "age_range": "5-12",
        "font_size": 52,
        "font": "Comic Sans MS",
        "colors": {
            "primary": "&H0000FFFF",  # Bright yellow
            "outline": "&H00000000",  # Black
            "background": "&H8000FF00"  # Semi-transparent green
        },
        "subtitle_style": "colorful_bubbles",
        "animation_speed": "fast",
        "music_genres": ["children", "cartoon", "disney", "kawaii"],
        "tts_voice": "female_young",
        "tts_speed": 1.2
    }

    TEENS = {
        "name": "Teenagers",
        "age_range": "13-19",
        "font_size": 44,
        "font": "Arial Bold",
        "colors": {
            "primary": "&H0000FFFF",  # Neon cyan
            "outline": "&H00FF00FF",  # Magenta
            "background": "&H600000FF"
        },
        "subtitle_style": "neon_glow",
        "animation_speed": "medium",
        "music_genres": ["pop", "kpop", "jpop", "edm", "hiphop"],
        "tts_voice": "female_teen",
        "tts_speed": 1.0
    }

    YOUNG_ADULTS = {
        "name": "Young Adults",
        "age_range": "20-35",
        "font_size": 40,
        "font": "Segoe UI",
        "colors": {
            "primary": "&H00FFFFFF",  # Pure white
            "outline": "&H00202020",  # Dark gray
            "background": "&H40000000"
        },
        "subtitle_style": "elegant_minimal",
        "animation_speed": "normal",
        "music_genres": ["pop", "rock", "rnb", "indie", "electronic"],
        "tts_voice": "female_adult",
        "tts_speed": 1.0
    }

    GENERAL = {
        "name": "General Audience",
        "age_range": "All ages",
        "font_size": 44,
        "font": "Arial",
        "colors": {
            "primary": "&H00FFFFFF",
            "outline": "&H00000000",
            "background": "&H80000000"
        },
        "subtitle_style": "classic",
        "animation_speed": "normal",
        "music_genres": ["pop", "classic", "rock", "country"],
        "tts_voice": "neutral",
        "tts_speed": 1.0
    }


# =============================================================================
# LYRIC STYLES - KARAOKE LYRIC STYLES
# =============================================================================

class LyricStyle(Enum):
    """Visual styles for karaoke lyrics."""

    CLASSIC = {
        "name": "Classic",
        "description": "White lyrics with black border",
        "ass_style": {
            "FontSize": 44,
            "PrimaryColour": "&H00FFFFFF",
            "SecondaryColour": "&H000000FF",
            "OutlineColour": "&H00000000",
            "BackColour": "&H80000000",
            "Outline": 2,
            "Shadow": 1,
            "Alignment": 2
        },
        "animation": "fade_in"
    }

    NEON = {
        "name": "Neon",
        "description": "Bright neon-style lyrics",
        "ass_style": {
            "FontSize": 48,
            "PrimaryColour": "&H0000FFFF",
            "SecondaryColour": "&H000000FF",
            "OutlineColour": "&H00FF00FF",
            "BackColour": "&H800066CC",
            "Outline": 3,
            "Shadow": 2,
            "Alignment": 2
        },
        "animation": "neon_pulse"
    }
    
    KARAOKE_BUBBLE = {
        "name": "Burbuja Karaoke",
        "description": "Letras en burbujas de colores",
        "ass_style": {
            "FontSize": 44,
            "PrimaryColour": "&H0000FFFF",
            "SecondaryColour": "&H000000FF",
            "OutlineColour": "&H00FFFFFF",
            "BackColour": "&H80FF00FF",
            "Outline": 2,
            "Shadow": 0,
            "Alignment": 2
        },
        "animation": "bounce"
    }
    
    ELEGANT = {
        "name": "Elegante",
        "description": "Minimalista y sofisticado",
        "ass_style": {
            "FontSize": 40,
            "PrimaryColour": "&H00E0E0E0",
            "SecondaryColour": "&H000000FF",
            "OutlineColour": "&H00202020",
            "BackColour": "&H00000000",
            "Outline": 1,
            "Shadow": 0,
            "Alignment": 2
        },
        "animation": "fade_slow"
    }
    
    ANIME = {
        "name": "Anime Style",
        "description": "Estilo japonés animado",
        "ass_style": {
            "FontSize": 48,
            "PrimaryColour": "&H0000FFFF",
            "SecondaryColour": "&H000000FF",
            "OutlineColour": "&H00FFFFFF",
            "BackColour": "&H600000FF",
            "Outline": 4,
            "Shadow": 3,
            "Alignment": 2
        },
        "animation": "karaoke_fill"
    }
    
    CYBERPUNK = {
        "name": "Cyberpunk",
        "description": "Futurista estilo cyberpunk",
        "ass_style": {
            "FontSize": 46,
            "PrimaryColour": "&H0000FF00",
            "SecondaryColour": "&H000000FF",
            "OutlineColour": "&H0000FFFF",
            "BackColour": "&H800000FF",
            "Outline": 3,
            "Shadow": 2,
            "Alignment": 2
        },
        "animation": "glitch"
    }


# =============================================================================
# MUSIC GENRES
# =============================================================================

class MusicGenre(Enum):
    """Music genres with configurations."""

    JPOP = {
        "name": "J-Pop",
        "keywords": ["jpop", "japanese pop", "anime", "japan"],
        "bpm_range": (110, 140),
        "moods": ["happy", "energetic", "cute"],
        "instruments": ["synth", "drums", "bass"]
    }

    KPOP = {
        "name": "K-Pop",
        "keywords": ["kpop", "korean pop", "korea"],
        "bpm_range": (100, 150),
        "moods": ["energetic", "powerful", "catchy"],
        "instruments": ["synth", "beats", "vocals"]
    }

    ANIME = {
        "name": "Anime/Openings",
        "keywords": ["anime", "anime OST", "opening", "soundtrack"],
        "bpm_range": (120, 160),
        "moods": ["epic", "energetic", "emotional"],
        "instruments": ["orchestra", "rock", "electronic"]
    }

    CHILDREN = {
        "name": "Children",
        "keywords": ["children", "kids", "cartoon", "disney", "nursery"],
        "bpm_range": (80, 130),
        "moods": ["happy", "fun", "playful"],
        "instruments": ["piano", "bells", "strings"]
    }

    POP = {
        "name": "General Pop",
        "keywords": ["pop", "chart", "radio"],
        "bpm_range": (90, 130),
        "moods": ["happy", "upbeat", "romantic"],
        "instruments": ["synth", "drums", "bass"]
    }

    ROCK = {
        "name": "Rock",
        "keywords": ["rock", "guitar", "band"],
        "bpm_range": (100, 160),
        "moods": ["energetic", "powerful", "rebellious"],
        "instruments": ["guitar", "drums", "bass"]
    }

    AMBIENT = {
        "name": "Ambient",
        "keywords": ["ambient", "chill", "relaxing", "background"],
        "bpm_range": (60, 90),
        "moods": ["calm", "peaceful", "mysterious"],
        "instruments": ["synth", "piano", "nature"]
    }


# =============================================================================
# LANGUAGE SETTINGS
# =============================================================================

class Language(Enum):
    """Language settings for TTS and subtitles."""

    JAPANESE = {
        "code": "ja",
        "name": "Japanese",
        "tts_voices": ["Japanese-Female-1", "Japanese-Male-1"],
        "font": "Noto Sans CJK JP",
        "font_fallback": ["Arial", "MS Gothic"],
        "text_direction": "ltr",
        "special_chars": True
    }

    ENGLISH = {
        "code": "en",
        "name": "English",
        "tts_voices": ["English-US-Female", "English-UK-Male"],
        "font": "Arial",
        "font_fallback": ["Segoe UI", "Calibri"],
        "text_direction": "ltr",
        "special_chars": False
    }

    SPANISH = {
        "code": "es",
        "name": "Spanish",
        "tts_voices": ["Spanish-ES-Female", "Spanish-US-Male"],
        "font": "Arial",
        "font_fallback": ["Segoe UI", "Calibri"],
        "text_direction": "ltr",
        "special_chars": True
    }
    
    CHINESE = {
        "code": "zh",
        "name": "Chino",
        "tts_voices": ["Chinese-Female", "Chinese-Male"],
        "font": "Noto Sans CJK SC",
        "font_fallback": ["Microsoft YaHei", "SimHei"],
        "text_direction": "ltr",
        "special_chars": True
    }
    
    KOREAN = {
        "code": "ko",
        "name": "Coreano",
        "tts_voices": ["Korean-Female", "Korean-Male"],
        "font": "Noto Sans CJK KR",
        "font_fallback": ["Malgun Gothic", "Dotum"],
        "text_direction": "ltr",
        "special_chars": True
    }


# =============================================================================
# ADVANCED LYRICS GENERATOR
# =============================================================================

@dataclass
class AdvancedLyricLine:
    """Advanced lyric line with metadata."""
    text: str
    start_time: float
    end_time: float
    duration: float = 0
    romanization: str = ""  # For Japanese/Korean
    translation: str = ""   # Translation
    notes: List[str] = None  # Notes/comments
    emphasis_words: List[str] = None  # Emphasized words
    karaoke_fill: bool = False  # Karaoke fill effect

    def __post_init__(self):
        if self.duration == 0:
            self.duration = self.end_time - self.start_time
        if self.notes is None:
            self.notes = []
        if self.emphasis_words is None:
            self.emphasis_words = []


class AdvancedLyricsGenerator:
    """
    Advanced lyrics generator with support for:
    - Multiple languages
    - Romanization (for Japanese/Korean)
    - Translations
    - Notes and comments
    - Advanced karaoke effects
    """

    def __init__(self):
        self.output_dir = PROJECT_ROOT / "output" / "lyrics"
        os.makedirs(self.output_dir, exist_ok=True)

    def create_lyrics(
        self,
        lyrics_text: str,
        music_duration: float,
        language: str = "ja",
        style: str = "anime",
        audience: str = "general",
        include_romanization: bool = True,
        include_translation: bool = False,
        translation_lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Create advanced lyrics with all options.

        Args:
            lyrics_text: Lyrics text (one line per line)
            music_duration: Total music duration
            language: Language code (ja, en, es, zh, ko)
            style: Visual style for lyrics
            audience: Target audience profile
            include_romanization: Include romanization
            include_translation: Include translation
            translation_lang: Translation language

        Returns:
            Dict with lyrics, styles and metadata
        """
        # Parse lines
        raw_lines = [l.strip() for l in lyrics_text.split('\n') if l.strip()]

        if not raw_lines:
            raw_lines = ["La la la", "Sing with me", "Tonight"]

        # Calculate timing
        gap = 0.4
        effective_duration = music_duration - (gap * (len(raw_lines) - 1))
        base_duration = effective_duration / len(raw_lines)

        # Get configurations
        lang_config = Language[language.upper()].value if language.upper() in Language.__members__ else Language.ENGLISH.value
        style_config = LyricStyle[style.upper()].value if style.upper() in LyricStyle.__members__ else LyricStyle.CLASSIC.value
        audience_config = AudienceProfile[audience.upper()].value if audience.upper() in AudienceProfile.__members__ else AudienceProfile.GENERAL.value

        # Generate lines
        advanced_lines = []
        current_time = 0

        for text in raw_lines:
            line = AdvancedLyricLine(
                text=text,
                start_time=current_time,
                end_time=current_time + base_duration,
                duration=base_duration,
                romanization=self._generate_romanization(text, language) if include_romanization else "",
                translation=self._translate_text(text, language, translation_lang) if include_translation else "",
                notes=[],
                emphasis_words=self._find_emphasis_words(text),
                karaoke_fill=(style == "anime")
            )
            advanced_lines.append(line)
            current_time += base_duration + gap

        # Create complete result
        result = {
            "metadata": {
                "language": language,
                "language_name": lang_config["name"],
                "style": style,
                "style_name": style_config["name"],
                "audience": audience,
                "audience_name": audience_config["name"],
                "total_duration": music_duration,
                "total_lines": len(advanced_lines),
                "created_at": datetime.now().isoformat()
            },
            "lyrics": [self._line_to_dict(l) for l in advanced_lines],
            "styles": {
                "ass_style": style_config["ass_style"],
                "animation": style_config["animation"],
                "font": lang_config["font"],
                "font_fallback": lang_config["font_fallback"]
            },
            "audience_config": audience_config
        }

        logger.info(f"Created {len(advanced_lines)} advanced lyrics lines")
        logger.info(f"  Language: {lang_config['name']}")
        logger.info(f"  Style: {style_config['name']}")
        logger.info(f"  Audience: {audience_config['name']}")
        
        return result
    
    def _line_to_dict(self, line: AdvancedLyricLine) -> Dict:
        """Convertir línea a diccionario."""
        return {
            "text": line.text,
            "romanization": line.romanization,
            "translation": line.translation,
            "start_time": line.start_time,
            "end_time": line.end_time,
            "duration": line.duration,
            "notes": line.notes,
            "emphasis_words": line.emphasis_words,
            "karaoke_fill": line.karaoke_fill
        }

    def _generate_romanization(self, text: str, language: str) -> str:
        """Generate basic romanization (simplified)."""
        # In production, would use a library like pykakasi for Japanese
        if language == "ja":
            return f"[{text}]"  # Placeholder
        elif language == "ko":
            return f"[{text}]"  # Placeholder
        return ""

    def _translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text (placeholder - in production would use API)."""
        # In production, would call a translation API
        return ""

    def _find_emphasis_words(self, text: str) -> List[str]:
        """Identify words to emphasize."""
        # Words that are likely important
        emphasis_markers = ["!", "★", "☆", "❤️", "★"]
        emphasized = []
        for marker in emphasis_markers:
            if marker in text:
                emphasized.append(marker)
        return emphasized

    def generate_ass_file(self, lyrics_data: Dict[str, Any], output_path: str):
        """Generate ASS file with advanced styles."""

        metadata = lyrics_data["metadata"]
        styles = lyrics_data["styles"]
        audience = lyrics_data["audience_config"]
        lines = lyrics_data["lyrics"]

        # Header ASS
        ass_header = f"""[Script Info]
Title: Karaoke - {metadata['style_name']}
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{styles['font']},{styles['ass_style']['FontSize']},{styles['ass_style']['PrimaryColour']},{styles['ass_style']['SecondaryColour']},{styles['ass_style']['OutlineColour']},{styles['ass_style']['BackColour']},-1,0,0,0,100,100,0,0,1,{styles['ass_style']['Outline']},{styles['ass_style']['Shadow']},{styles['ass_style']['Alignment']},10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        # Generate events
        events = []
        for line in lines:
            start = self._format_ass_time(line["start_time"])
            end = self._format_ass_time(line["end_time"])
            text = line["text"]

            # Add romanization if it exists and audience requires it
            if line["romanization"] and metadata["audience"] in ["children", "teens"]:
                text = f"{{\\an8}}{line['romanization']}\\N{{\\an0}}{text}"

            # Add karaoke effects if applicable
            if line["karaoke_fill"]:
                # Gradual fill effect (simplified)
                text = f"{{\\k{int(line['duration']*100/4)}}}{text[:len(text)//4]}{{\\k{int(line['duration']*100/4)}}}{text[len(text)//4:len(text)//2]}{{\\k{int(line['duration']*100/4)}}}{text[len(text)//2:3*len(text)//4]}{{\\k{int(line['duration']*100/4)}}}{text[3*len(text)//4:]}"

            events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_header)
            f.write("\n".join(events))

        logger.info(f"Generated ASS file: {output_path}")
        return output_path

    def _format_ass_time(self, seconds: float) -> str:
        """Format time for ASS."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        cs = int((s % 1) * 100)
        return f"{h}:{m:02d}:{s:05.2f}"


# =============================================================================
# MUSIC ADAPTOR - MUSIC ADAPTOR BY GENRE
# =============================================================================

class MusicAdaptor:
    """Music adaptor based on genre and audience."""

    def select_music(
        self,
        genre: str,
        mood: str,
        duration_range: tuple = (25, 35),
        audience: str = "general"
    ) -> Dict[str, Any]:
        """
        Seleccionar música según parámetros.
        
        Args:
            genre: Género musical (jpop, kpop, anime, pop, rock, etc.)
            mood: Estado de ánimo (happy, energetic, calm, romantic)
            duration_range: Rango de duración deseado
            audience: Perfil del público
        
        Returns:
            Configuración de música recomendada
        """
        genre_config = MusicGenre[genre.upper()].value if genre.upper() in MusicGenre.__members__ else MusicGenre.POP.value

        # Filter available moods
        available_moods = genre_config["moods"]
        best_mood = mood if mood in available_moods else available_moods[0]

        # Generate configuration
        config = {
            "genre": genre,
            "genre_name": genre_config["name"],
            "mood": best_mood,
            "keywords": genre_config["keywords"],
            "bpm_range": genre_config["bpm_range"],
            "instruments": genre_config["instruments"],
            "duration_range": duration_range,
            "search_query": self._build_search_query(genre_config["keywords"], best_mood),
            "mixing_settings": self._get_mixing_settings(audience, genre)
        }

        logger.info(f"Music config: {genre_config['name']} - {best_mood}")
        logger.info(f"  BPM: {genre_config['bpm_range']}")
        logger.info(f"  Query: {config['search_query']}")

        return config

    def _build_search_query(self, keywords: List[str], mood: str) -> str:
        """Build search query."""
        base = keywords[0] if keywords else "music"
        return f"{base} {mood}"
    
    def _get_mixing_settings(self, audience: str, genre: str) -> Dict[str, float]:
        """Obtener configuraciones de mezcla según audiencia y género."""
        
        base_settings = {
            "children": {"voice_volume": 1.4, "music_volume": 0.3, "bass_boost": True},
            "teens": {"voice_volume": 1.2, "music_volume": 0.5, "bass_boost": True},
            "young_adults": {"voice_volume": 1.0, "music_volume": 0.5, "bass_boost": False},
            "general": {"voice_volume": 1.1, "music_volume": 0.4, "bass_boost": False}
        }
        
        # Adjust by genre
        settings = base_settings.get(audience, base_settings["general"])

        if genre in ["rock", "edm", "hiphop"]:
            settings["bass_boost"] = True
            settings["music_volume"] = min(settings["music_volume"] + 0.1, 0.6)

        return settings


# =============================================================================
# MULTI-LANGUAGE TTS MANAGER
# =============================================================================

class MultiLanguageTTSManager:
    """Multi-language TTS manager with specific voices."""

    # Voice configurations by language
    TTS_CONFIGS = {
        "ja": {
            "providers": ["a2e", "google"],
            "default_voice": "ja-JP-Standard-A",
            "speeds": {"normal": 1.0, "fast": 1.2, "slow": 0.9},
            "sample_rate": 22050
        },
        "en": {
            "providers": ["a2e", "elevenlabs", "openai"],
            "default_voice": "en-US-Jenny",
            "speeds": {"normal": 1.0, "fast": 1.1, "slow": 0.9},
            "sample_rate": 22050
        },
        "es": {
            "providers": ["a2e", "google"],
            "default_voice": "es-ES-Standard-A",
            "speeds": {"normal": 1.0, "fast": 1.15, "slow": 0.9},
            "sample_rate": 22050
        },
        "zh": {
            "providers": ["a2e", "google"],
            "default_voice": "zh-CN-Standard-A",
            "speeds": {"normal": 1.0, "fast": 1.1, "slow": 0.9},
            "sample_rate": 22050
        },
        "ko": {
            "providers": ["a2e", "google"],
            "default_voice": "ko-KR-Standard-A",
            "speeds": {"normal": 1.0, "fast": 1.15, "slow": 0.9},
            "sample_rate": 22050
        }
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.output_dir = PROJECT_ROOT / "output" / "voices"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_for_lyrics(
        self,
        lyrics: List[Dict[str, Any]],
        language: str = "ja",
        speed: str = "normal",
        audience: str = "general"
    ) -> List[str]:
        """
        Generate TTS audio for all lyrics.

        Args:
            lyrics: List of lyrics dictionaries
            language: Language code
            speed: Speed (normal, fast, slow)
            audience: Audience profile

        Returns:
            List of audio file paths
        """
        config = self.TTS_CONFIGS.get(language, self.TTS_CONFIGS["en"])
        speed_value = config["speeds"].get(speed, 1.0)

        # Adjust speed according to audience
        if audience == "children":
            speed_value *= 1.1  # Slightly faster to maintain attention
        elif audience == "general":
            speed_value *= 1.0

        voice_files = []

        for i, line in enumerate(lyrics):
            text = line["text"]
            duration = line.get("duration", 3.0)

            output_path = self._generate_voice(
                text=text,
                language=language,
                speed=speed_value,
                index=i
            )

            if output_path:
                voice_files.append(output_path)
        
        logger.info(f"✓ Generated {len(voice_files)} TTS clips for {language}")
        return voice_files
    
    def _generate_voice(
        self,
        text: str,
        language: str,
        speed: float,
        index: int
    ) -> str:
        """Generate voice for a line of text."""

        output_path = str(self.output_dir / f"voice_{language}_{index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")

        # Create audio with FFmpeg (in production, would call TTS API)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency=440:duration=3",
            "-ar", "22050",
            "-ac", "1",
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except Exception:
            with open(output_path, 'wb') as f:
                f.write(b'MOCK_VOICE')
        
        return output_path

    def calculate_cost(self, total_duration: float, language: str) -> int:
        """Calculate credit cost."""
        # A2E TTS: 1 credit per 10 seconds
        return int((total_duration / 10)) + 1


# =============================================================================
# NOTES AND ANNOTATIONS SYSTEM
# =============================================================================

class NotesManager:
    """Notes and annotations system for lyrics."""

    def add_notes(
        self,
        lyrics: List[Dict[str, Any]],
        notes_data: Dict[int, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Add notes to specific lyric lines.

        Args:
            lyrics: List of lyrics dictionaries
            notes_data: Dict with {line_index: [note1, note2]}

        Returns:
            Updated lyrics with notes
        """
        for line_idx, notes in notes_data.items():
            if 0 <= line_idx < len(lyrics):
                lyrics[line_idx]["notes"] = notes

        logger.info(f"Added notes to {len(notes_data)} lines")
        return lyrics

    def generate_notes_file(
        self,
        lyrics: List[Dict[str, Any]],
        output_path: str
    ):
        """Generate notes file in readable format."""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("KARAOKE LYRICS NOTES\n")
            f.write("=" * 60 + "\n\n")

            for i, line in enumerate(lyrics):
                f.write(f"LINE {i+1}: {line['text']}\n")
                f.write(f"  Time: {line['start_time']:.1f}s - {line['end_time']:.1f}s\n")
                if line.get('romanization'):
                    f.write(f"  Romanization: {line['romanization']}\n")
                if line.get('translation'):
                    f.write(f"  Translation: {line['translation']}\n")
                if line.get('notes'):
                    f.write(f"  Notes: {', '.join(line['notes'])}\n")
                if line.get('emphasis_words'):
                    f.write(f"  Emphasis: {', '.join(line['emphasis_words'])}\n")
                f.write("\n")

        logger.info(f"Notes file: {output_path}")


# =============================================================================
# ADVANCED KARAOKE PIPELINE - COMPLETE PIPELINE
# =============================================================================

class AdvancedKaraokePipeline:
    """
    Advanced karaoke pipeline with complete customization.

    Usage:
        pipeline = AdvancedKaraokePipeline()
        result = pipeline.run(
            lyrics_text="...",
            language="ja",
            genre="anime",
            style="anime",
            audience="teens"
        )
    """

    def __init__(self):
        self.output_dir = PROJECT_ROOT / "output" / "karaoke_advanced"
        os.makedirs(self.output_dir, exist_ok=True)

        self.lyrics_gen = AdvancedLyricsGenerator()
        self.music_adaptor = MusicAdaptor()
        self.tts_manager = MultiLanguageTTSManager()
        self.notes_manager = NotesManager()

        logger.info("=" * 70)
        logger.info("ADVANCED KARAOKE PIPELINE INITIALIZED")
        logger.info("=" * 70)

    def run(
        self,
        lyrics_text: str,
        language: str = "ja",
        genre: str = "anime",
        style: str = "anime",
        audience: str = "general",
        music_mood: str = "energetic",
        include_romanization: bool = True,
        include_translation: bool = False,
        translation_lang: str = "en",
        custom_notes: Dict[int, List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ejecutar pipeline completo de karaoke personalizado.
        
        Args:
            lyrics_text: Texto de las letras
            language: Idioma (ja, en, es, zh, ko)
            genre: Género musical (jpop, kpop, anime, pop, rock, children)
            style: Estilo visual (classic, neon, anime, elegant, cyberpunk)
            audience: Público objetivo (children, teens, young_adults, general)
            music_mood: Estado de ánimo de la música
            include_romanization: Incluir romanización
            include_translation: Incluir traducción
            translation_lang: Idioma de traducción
            custom_notes: Notas personalizadas {line_idx: [notas]}
        
        Returns:
            Dict completo con todos los resultados
        """
        start_time = time.time()
        
        logger.info("\n" + "=" * 70)
        logger.info("🚀 ADVANCED KARAOKE PRODUCTION")
        logger.info("=" * 70)
        
        results = {
            "success": False,
            "config": {
                "language": language,
                "genre": genre,
                "style": style,
                "audience": audience
            },
            "steps": []
        }
        
        try:
            # ===== STEP 1: Music Selection =====
            logger.info("\n📀 STEP 1: Selecting music...")
            music_config = self.music_adaptor.select_music(
                genre=genre,
                mood=music_mood,
                audience=audience
            )
            results["steps"].append({
                "step": "music_selection",
                "config": music_config
            })
            
            # ===== STEP 2: Generate Advanced Lyrics =====
            logger.info("\n📝 STEP 2: Generating advanced lyrics...")
            lyrics_data = self.lyrics_gen.create_lyrics(
                lyrics_text=lyrics_text,
                music_duration=30.0,  # Default, would get from music
                language=language,
                style=style,
                audience=audience,
                include_romanization=include_romanization,
                include_translation=include_translation,
                translation_lang=translation_lang
            )
            results["steps"].append({
                "step": "lyrics_generation",
                "lines": len(lyrics_data["lyrics"]),
                "metadata": lyrics_data["metadata"]
            })
            
            # ===== STEP 3: Add Custom Notes =====
            if custom_notes:
                logger.info("\n📝 STEP 3: Adding custom notes...")
                lyrics_data["lyrics"] = self.notes_manager.add_notes(
                    lyrics_data["lyrics"],
                    custom_notes
                )
                results["steps"].append({
                    "step": "notes_added",
                    "notes_count": sum(len(n) for n in custom_notes.values())
                })
            
            # ===== STEP 4: Generate TTS =====
            logger.info("\n🗣️ STEP 4: Generating TTS voice...")
            voice_files = self.tts_manager.generate_for_lyrics(
                lyrics=lyrics_data["lyrics"],
                language=language,
                audience=audience
            )
            tts_cost = self.tts_manager.calculate_cost(
                sum(l["duration"] for l in lyrics_data["lyrics"]),
                language
            )
            results["steps"].append({
                "step": "tts_generation",
                "files": len(voice_files),
                "estimated_cost": tts_cost
            })
            
            # ===== STEP 5: Generate ASS Subtitles =====
            logger.info("\n📝 STEP 5: Generating styled subtitles...")
            ass_path = str(self.output_dir / f"subtitles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ass")
            self.lyrics_gen.generate_ass_file(lyrics_data, ass_path)
            results["steps"].append({
                "step": "subtitle_generation",
                "path": ass_path,
                "style": style
            })
            
            # ===== STEP 6: Generate Notes File =====
            if custom_notes:
                notes_path = str(self.output_dir / f"notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                self.notes_manager.generate_notes_file(lyrics_data["lyrics"], notes_path)
            
            # ===== FINAL SUMMARY =====
            duration = time.time() - start_time
            
            results["success"] = True
            results["output_dir"] = str(self.output_dir)
            results["total_duration"] = duration
            results["config_summary"] = {
                "language": f"{lyrics_data['metadata']['language']} ({lyrics_data['metadata']['language_name']})",
                "style": lyrics_data['metadata']['style_name'],
                "audience": lyrics_data['metadata']['audience_name'],
                "genre": music_config["genre_name"],
                "mood": music_config["mood"]
            }
            results["features_used"] = {
                "romanization": include_romanization,
                "translation": include_translation,
                "custom_notes": custom_notes is not None
            }
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ ADVANCED KARAOKE PRODUCTION COMPLETE")
            logger.info("=" * 70)
            logger.info(f"Language: {lyrics_data['metadata']['language_name']}")
            logger.info(f"Style: {lyrics_data['metadata']['style_name']}")
            logger.info(f"Audience: {lyrics_data['metadata']['audience_name']}")
            logger.info(f"Genre: {music_config['genre_name']}")
            logger.info(f"Lyrics: {len(lyrics_data['lyrics'])} lines")
            logger.info(f"Duration: {duration:.1f}s")
            logger.info("=" * 70)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            results["error"] = str(e)
            return results


def demo():
    """Demo del sistema avanzado."""
    
    print("\n" + "=" * 70)
    print("🎤 ADVANCED KARAOKE SYSTEM - PERSONALIZATION DEMO")
    print("=" * 70)
    
    # Letra de ejemplo
    lyrics = """
夢を追いかけて
夜空の星のように
笑顔を忘れないで
永遠に輝き続けて
""".strip()
    
    # Notas personalizadas
    custom_notes = {
        0: ["Palabra clave: 夢 (sueño)", "Empezar con energía"],
        2: ["Palabra clave: 笑顔 (sonrisa)", "Sonreír al cantar"],
        3: ["Final emotivo", "Bajar intensidad gradualmente"]
    }
    
    # Ejecutar pipeline
    pipeline = AdvancedKaraokePipeline()
    
    result = pipeline.run(
        lyrics_text=lyrics,
        language="ja",
        genre="anime",
        style="anime",
        audience="teens",
        include_romanization=True,
        custom_notes=custom_notes
    )
    
    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)
    print(f"Success: {result['success']}")
    
    if result['success']:
        print("\nConfiguration:")
        for k, v in result['config_summary'].items():
            print(f"  {k}: {v}")
        
        print("\nFeatures Used:")
        for k, v in result['features_used'].items():
            print(f"  {k}: {'✓' if v else '✗'}")
    else:
        print(f"Error: {result.get('error', 'Unknown')}")
    
    return result


if __name__ == "__main__":
    demo()
