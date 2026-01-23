#!/bin/bash
#
# Video Production Script - Content Automation Pipeline
# Automates video content creation for both phases AND KARAOKE generation
#
# Usage:
#   ./scripts/produce.sh --phase 1 --character yuki-chan --audio audio.mp3
#   ./scripts/produce.sh --phase 2 --character kenji-rojo --audio podcast.mp3 --quality high
#   ./scripts/produce.sh --all --character mika-sweet --audio script.mp3
#
# KARAOKE USAGE:
#   ./scripts/produce.sh --karaoke --lyrics lyrics.txt --style anime --audience teens --character singer-avatar
#   ./scripts/produce.sh --karaoke --lyrics song.lrc --style kpop --audience general --audio mixed.mp3
#
# Options:
#   --phase, -p         Production phase (1 or 2)
#   --character, -c     Character ID
#   --audio, -a         Path to audio file
#   --variant, -v       Character variant (default, casual, performance, etc.)
#   --quality, -q       Output quality (low, medium, high, ultra)
#   --title, -t         Video title
#   --output, -o        Specific output path
#   --all               Generate avatar + video in the specified phase
#   --batch             Batch mode (reads jobs from JSON file)
#   --generate-avatar   Only generate avatar
#   --create-video      Only create video (requires existing avatar)
#   --stats             Show production statistics
#
# KARAOKE OPTIONS:
#   --karaoke           Enable karaoke mode (generate singing avatar video)
#   --lyrics, -l        Path to lyrics file (.txt or .lrc format)
#   --style, -s         Visual style: anime, kpop, minimalist, classic (default: anime)
#   --audience, -aud    Target audience: children, teens, young_adults, general (default: general)
#   --language, -lang   Lyrics language: ja, en, es, ko, zh (auto-detect if not specified)
#   --music, -m         Background music source: pixabay or file (default: pixabay)
#   --music-query, -q   Search query for Pixabay music
#   --no-subtitles      Disable subtitle overlay
#   --romanize          Show romanized lyrics (for non-Latin scripts)
#   --help, -h          Show this help
#

set -euo pipefail

# ============================================
# CONFIGURATION
# ============================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config/avatars"
SRC_DIR="$PROJECT_ROOT/src"
ASSETS_DIR="$PROJECT_ROOT/assets"
OUTPUT_DIR="$ASSETS_DIR/output"
TMP_DIR="$PROJECT_ROOT/tmp"
LOGS_DIR="$PROJECT_ROOT/logs"

# Karaoke specific paths
KARAOKE_LYRICS_DIR="$PROJECT_ROOT/karaoke_lyrics"
KARAOKE_VOICES_DIR="$PROJECT_ROOT/karaoke_voices"
KARAOKE_MIXED_DIR="$PROJECT_ROOT/karaoke_mixed"
KARAOKE_VIDEOS_DIR="$PROJECT_ROOT/karaoke_videos"
MUSIC_LIBRARY_DIR="$PROJECT_ROOT/music_library"

# Verify directory structure
mkdir -p "$OUTPUT_DIR/phase1" "$OUTPUT_DIR/phase2" "$OUTPUT_DIR/thumbnails"
mkdir -p "$ASSETS_DIR/avatars/generated" "$ASSETS_DIR/avatars/variants"
mkdir -p "$ASSETS_DIR/audio"
mkdir -p "$TMP_DIR/phase1" "$TMP_DIR/phase2" "$TMP_DIR/subtitles"
mkdir -p "$LOGS_DIR"
mkdir -p "$KARAOKE_LYRICS_DIR" "$KARAOKE_VOICES_DIR" "$KARAOKE_MIXED_DIR" "$KARAOKE_VIDEOS_DIR"
mkdir -p "$MUSIC_LIBRARY_DIR/downloads"

# Environment variables (load from .env if exists)
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# ============================================
# UTILITY FUNCTIONS
# ============================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" >> "$LOGS_DIR/production.log"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [OK] $1" >> "$LOGS_DIR/production.log"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $1" >> "$LOGS_DIR/production.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >> "$LOGS_DIR/production.log"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        missing+=("pip3")
    fi
    
    # Check FFmpeg (required for Phase 2)
    if ! command -v ffmpeg &> /dev/null; then
        log_warning "FFmpeg not found - some Phase 2 functions will not be available"
    fi
    
    # Check FFprobe
    if ! command -v ffprobe &> /dev/null; then
        log_warning "FFprobe not found - some functions will not be available"
    fi
    
    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_error "Please install the missing dependencies"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

check_config() {
    if [ ! -f "$CONFIG_DIR/characters.json" ]; then
        log_error "Configuration file not found: $CONFIG_DIR/characters.json"
        exit 1
    fi
}

get_character_list() {
    python3 -c "
import json
with open('$CONFIG_DIR/characters.json', 'r') as f:
    config = json.load(f)
    characters = list(config.get('characters', {}).keys())
    print(' '.join(characters))
" 2>/dev/null || echo ""
}

get_character_variants() {
    local char_id=$1
    python3 -c "
import json
with open('$CONFIG_DIR/characters.json', 'r') as f:
    config = json.load(f)
    variants = config.get('characters', {}).get('$char_id', {}).get('supported_variants', ['default'])
    print(' '.join(variants))
" 2>/dev/null || echo "default"
}

# ============================================
# KARAOKE UTILITY FUNCTIONS
# ============================================

check_karaoke_dependencies() {
    log_info "Checking karaoke dependencies..."

    local missing=()

    # Check Python dependencies
    if ! python3 -c "import aiohttp" 2>/dev/null; then
        missing+=("aiohttp")
    fi

    # Check FFmpeg (critical for karaoke)
    if ! command -v ffmpeg &> /dev/null; then
        missing+=("ffmpeg")
    fi

    # Check if advanced_karaoke.py exists
    if [ ! -f "$SCRIPT_DIR/advanced_karaoke.py" ]; then
        log_warning "advanced_karaoke.py not found - karaoke features may be limited"
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        log_warning "Missing dependencies: ${missing[*]}"
        log_warning "Karaoke generation may not work correctly"
    else
        log_success "Karaoke dependencies are available"
    fi
}

validate_lyrics_file() {
    local lyrics_file=$1

    if [ ! -f "$lyrics_file" ]; then
        log_error "Lyrics file not found: $lyrics_file"
        return 1
    fi

    local file_ext="${lyrics_file##*.}"
    if [[ "$file_ext" != "txt" && "$file_ext" != "lrc" ]]; then
        log_warning "Unknown lyrics format: .$file_ext (expecting .txt or .lrc)"
        log_info "Will attempt to parse as plain text"
    fi

    local line_count=$(wc -l < "$lyrics_file")
    if [ "$line_count" -lt 2 ]; then
        log_error "Lyrics file is too short (minimum 2 lines required)"
        return 1
    fi

    log_success "Lyrics file validated: $line_count lines"
    return 0
}

get_style_preset() {
    local style=$1

    case $style in
        anime)
            echo "anime"
            ;;
        kpop)
            echo "kpop"
            ;;
        minimalist)
            echo "minimalist"
            ;;
        classic)
            echo "classic"
            ;;
        neon)
            echo "neon"
            ;;
        *)
            log_warning "Unknown style: $style, using default (anime)"
            echo "anime"
            ;;
    esac
}

get_audience_profile() {
    local audience=$1

    case $audience in
        children|kids|kids)
            echo "children"
            ;;
        teens|teenagers|adolescentes)
            echo "teens"
            ;;
        young_adults|adultos_jovenes|youngadults)
            echo "young_adults"
            ;;
        general|general)
            echo "general"
            ;;
        *)
            log_warning "Unknown audience: $audience, using default (general)"
            echo "general"
            ;;
    esac
}

# ============================================
# AVATAR GENERATION
# ============================================

generate_avatar() {
    local character=$1
    local variant=${2:-default}
    local provider=${3:-dalle3}
    
    log_info "Generating avatar for: $character (variant: $variant)"
    
    cd "$PROJECT_ROOT"
    python3 "$SRC_DIR/avatar_generator.py" \
        --character "$character" \
        --variant "$variant" \
        --provider "$provider"
    
    if [ $? -eq 0 ]; then
        log_success "Avatar generated successfully"
        return 0
    else
        log_error "Error generating avatar"
        return 1
    fi
}

generate_all_variants() {
    local character=$1
    local provider=${2:-dalle3}
    
    log_info "Generating all variants for: $character"
    
    local variants=$(get_character_variants "$character")
    local success_count=0
    local fail_count=0
    
    for variant in $variants; do
        if generate_avatar "$character" "$variant" "$provider"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
    done
    
    log_info "Generation completed: $success_count successful, $fail_count failed"
}

# ============================================
# PHASE 1 PRODUCTION (API)
# ============================================

production_phase1() {
    local character=$1
    local audio=$2
    local variant=${3:-default}
    local title=${4:-"${character}_short"}
    
    log_info "Starting Phase 1 production for: $character"
    log_info "Audio: $audio"
    
    # Find generated avatar
    local avatar_path="$ASSETS_DIR/avatars/generated/opt_${character}_${variant}_"*.png
    local avatar_count=$(find "$ASSETS_DIR/avatars/generated" -name "opt_${character}_${variant}_*.png" 2>/dev/null | wc -l)
    
    if [ "$avatar_count" -eq 0 ]; then
        log_warning "No avatar found for $character ($variant)"
        log_info "Generating avatar first..."
        if ! generate_avatar "$character" "$variant"; then
            log_error "Could not generate avatar"
            return 1
        fi
        avatar_path="$ASSETS_DIR/avatars/generated/opt_${character}_${variant}_"*.png
    fi
    
    # Use most recent avatar
    avatar_path=$(find "$ASSETS_DIR/avatars/generated" -name "opt_${character}_${variant}_*.png" -type f -printf '%T+ %p\n' 2>/dev/null | sort | tail -1 | cut -d' ' -f2-)
    
    if [ -z "$avatar_path" ]; then
        log_error "Could not find avatar file"
        return 1
    fi
    
    log_info "Using avatar: $avatar_path"
    
    # Verify audio exists
    if [ ! -f "$audio" ]; then
        log_error "Audio file not found: $audio"
        return 1
    fi
    
    # Verify API key (supports both VIDEO_A2E_API_KEY and A2E_API_KEY)
    if [ -z "${A2E_API_KEY:-}" ] && [ -z "${VIDEO_A2E_API_KEY:-}" ]; then
        log_error "A2E_API_KEY or VIDEO_A2E_API_KEY environment variable not configured"
        log_error "Run: source scripts/load_env.sh"
        return 1
    fi

    # Use whichever API key is available
    if [ -n "${VIDEO_A2E_API_KEY:-}" ]; then
        A2E_API_KEY="$VIDEO_A2E_API_KEY"
    fi

    # Execute production using orchestrator with A2E Integration
    cd "$PROJECT_ROOT"
    python3 -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from production_orchestrator import ProductionOrchestrator

async def main():
    orchestrator = ProductionOrchestrator()
    try:
        result = await orchestrator.run_phase1_pipeline(
            character_id='$character',
            audio_path='$audio',
            variant='$variant',
            title='$title'
        )
        if result.success:
            print(f'Success: {result.output_path}')
        else:
            print(f'Failed: {result.error_message}')
            sys.exit(1)
    finally:
        await orchestrator.close()

asyncio.run(main())
"
    
    if [ $? -eq 0 ]; then
        log_success "Phase 1 production completed"
        return 0
    else
        log_error "Error in Phase 1 production"
        return 1
    fi
}

# ============================================
# PHASE 2 PRODUCTION (LOCAL)
# ============================================

production_phase2() {
    local character=$1
    local audio=$2
    local variant=${3:-default}
    local quality=${4:-medium}
    local title=${5:-"${character}_video"}
    
    log_info "Starting Phase 2 production for: $character"
    log_info "Audio: $audio"
    log_info "Quality: $quality"
    
    # Verify FFmpeg
    if ! command -v ffmpeg &> /dev/null; then
        log_error "FFmpeg is not installed. Cannot run Phase 2."
        return 1
    fi
    
    # Find generated avatar
    local avatar_path=$(find "$ASSETS_DIR/avatars/generated" -name "opt_${character}_${variant}_*.png" -type f -printf '%T+ %p\n' 2>/dev/null | sort | tail -1 | cut -d' ' -f2-)
    
    if [ -z "$avatar_path" ]; then
        log_warning "No avatar found for $character ($variant)"
        log_info "Generating avatar first..."
        if ! generate_avatar "$character" "$variant"; then
            log_error "Could not generate avatar"
            return 1
        fi
        avatar_path=$(find "$ASSETS_DIR/avatars/generated" -name "opt_${character}_${variant}_*.png" -type f -printf '%T+ %p\n' 2>/dev/null | sort | tail -1 | cut -d' ' -f2-)
    fi
    
    if [ -z "$avatar_path" ]; then
        log_error "Could not find avatar file"
        return 1
    fi
    
    log_info "Using avatar: $avatar_path"
    
    # Verify audio exists
    if [ ! -f "$audio" ]; then
        log_error "Audio file not found: $audio"
        return 1
    fi
    
    # Execute production
    cd "$PROJECT_ROOT"
    python3 "$SRC_DIR/video_production_p2.py" \
        --avatar "$avatar_path" \
        --audio "$audio" \
        --title "$title" \
        --quality "$quality"
    
    if [ $? -eq 0 ]; then
        log_success "Phase 2 production completed"
        return 0
    else
        log_error "Error in Phase 2 production"
        return 1
    fi
}

# ============================================
# FULL PRODUCTION (BOTH PHASES)
# ============================================

production_all() {
    local character=$1
    local audio=$2
    local variant=${3:-default}

    log_info "Starting full production for: $character"

    # Phase 1: Short video
    log_info "=== PHASE 1: Short Video ==="
    if ! production_phase1 "$character" "$audio" "$variant" "${character}_short"; then
        log_warning "Phase 1 failed, continuing with Phase 2..."
    fi

    # Phase 2: Long video
    log_info "=== PHASE 2: Long Video ==="
    if ! production_phase2 "$character" "$audio" "$variant" "medium" "${character}_long"; then
        log_error "Phase 2 also failed"
        return 1
    fi

    log_success "Full production completed"
}

# ============================================
# KARAOKE PRODUCTION
# ============================================

production_karaoke() {
    local character=$1
    local lyrics_file=$2
    local style=${3:-anime}
    local audience=${4:-general}
    local language=${5:-auto}
    local music_source=${6:-pixabay}
    local music_query=${7:-""}
    local audio_file=${8:-""}
    local options=${9:-""}

    log_info "============================================"
    log_info "     KARAOKE PRODUCTION"
    log_info "============================================"
    log_info "Character: $character"
    log_info "Lyrics: $lyrics_file"
    log_info "Style: $style"
    log_info "Audience: $audience"
    log_info "Language: $language"
    log_info "Music Source: $music_source"
    if [ -n "$music_query" ]; then
        log_info "Music Query: $music_query"
    fi
    if [ -n "$audio_file" ]; then
        log_info "Audio File: $audio_file"
    fi
    log_info "============================================"

    # Validate lyrics file
    if ! validate_lyrics_file "$lyrics_file"; then
        return 1
    fi

    # Check dependencies
    check_karaoke_dependencies

    # Verify API keys
    local api_keys_missing=0
    if [ -z "${A2E_API_KEY:-}" ] && [ -z "${VIDEO_A2E_API_KEY:-}" ]; then
        log_warning "A2E_API_KEY not configured - will run in MOCK mode"
        api_keys_missing=1
    fi
    if [ -z "${PIXABAY_API_KEY:-}" ]; then
        log_warning "PIXABAY_API_KEY not configured - cannot download music"
        if [ "$music_source" == "pixabay" ]; then
            log_error "PIXABAY_API_KEY is required for music download"
            return 1
        fi
    fi

    # Validate character/avatar
    local avatar_path=""
    if [ -n "$character" ]; then
        avatar_path=$(find "$ASSETS_DIR/avatars/generated" -name "opt_${character}_*.png" -type f -printf '%T+ %p\n' 2>/dev/null | sort | tail -1 | cut -d' ' -f2-)

        if [ -z "$avatar_path" ]; then
            log_warning "No avatar found for: $character"
            log_info "Karaoke will be generated WITHOUT avatar (audio-only mode)"
        else
            log_info "Using avatar: $avatar_path"
        fi
    fi

    # Get style and audience presets
    local style_preset=$(get_style_preset "$style")
    local audience_profile=$(get_audience_profile "$audience")

    # Generate timestamp for output files
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local output_prefix="$KARAOKE_VIDEOS_DIR/karaoke_${timestamp}"

    # Build Python command
    log_info "Executing advanced karaoke system..."

    cd "$PROJECT_ROOT"

    local python_cmd="python3 $SCRIPT_DIR/advanced_karaoke.py \\
        --lyrics \"$lyrics_file\" \\
        --style \"$style_preset\" \\
        --audience \"$audience_profile\""

    if [ -n "$language" ] && [ "$language" != "auto" ]; then
        python_cmd="$python_cmd --language \"$language\""
    fi

    if [ -n "$character" ]; then
        python_cmd="$python_cmd --character \"$character\""
    fi

    if [ -n "$avatar_path" ]; then
        python_cmd="$python_cmd --avatar \"$avatar_path\""
    fi

    if [ -n "$audio_file" ]; then
        python_cmd="$python_cmd --audio \"$audio_file\""
    elif [ "$music_source" == "pixabay" ] && [ -n "$music_query" ]; then
        python_cmd="$python_cmd --music-query \"$music_query\""
    fi

    if [ "$options" == *"romanize"* ]; then
        python_cmd="$python_cmd --romanize"
    fi

    if [ "$options" == *"no-subtitles"* ]; then
        python_cmd="$python_cmd --no-subtitles"
    fi

    python_cmd="$python_cmd --output \"$output_prefix\""

    log_info "Command: $python_cmd"

    # Execute
    if eval "$python_cmd"; then
        log_success "Karaoke production completed!"

        # List generated files
        log_info "Generated files:"
        ls -lh "${output_prefix}"* 2>/dev/null | while read f; do
            log_info "  - $f"
        done

        return 0
    else
        log_error "Karaoke production failed"
        return 1
    fi
}

# ============================================
# QUICK KARAOKE (Simple mode)
# ============================================

quick_karaoke() {
    local lyrics_file=$1
    local style=${2:-anime}

    log_info "Quick karaoke mode - using defaults"

    local music_query=$(head -1 "$lyrics_file" 2>/dev/null | cut -d' ' -f1-5 | tr ' ' '+')
    if [ -z "$music_query" ]; then
        music_query="jpop+anime"
    fi

    production_karaoke "" "$lyrics_file" "$style" "general" "auto" "pixabay" "$music_query" "" ""
}

# ============================================
# BATCH MODE
# ============================================

production_batch() {
    local batch_file=$1
    
    if [ ! -f "$batch_file" ]; then
        log_error "Batch file not found: $batch_file"
        return 1
    fi
    
    log_info "Running batch production from: $batch_file"
    
    # Batch file must be JSON with format:
    # [
    #   {"character": "yuki-chan", "audio": "audio1.mp3", "phase": 1},
    #   {"character": "kenji-rojo", "audio": "audio2.mp3", "phase": 2, "quality": "high"}
    # ]
    
    python3 -c "
import json
import subprocess
import sys

batch_file = '$batch_file'
with open(batch_file, 'r') as f:
    jobs = json.load(f)

for job in jobs:
    character = job.get('character')
    audio = job.get('audio')
    phase = job.get('phase', 1)
    variant = job.get('variant', 'default')
    quality = job.get('quality', 'medium')
    title = job.get('title', f'{character}_{phase}')
    
    cmd = ['bash', '$0', '--phase', str(phase), '--character', character, '--audio', audio, '--variant', variant, '--title', title]
    if phase == 2:
        cmd.extend(['--quality', quality])
    
    print(f'Running: {\" \".join(cmd)}')
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
"
    
    if [ $? -eq 0 ]; then
        log_success "Batch production completed"
    else
        log_error "Error in batch production"
    fi
}

# ============================================
# STATISTICS
# ============================================

show_stats() {
    echo "============================================"
    echo "     PRODUCTION STATISTICS"
    echo "============================================"
    
    echo ""
    echo "=== Directories ==="
    echo "Project: $PROJECT_ROOT"
    echo "Avatars: $ASSETS_DIR/avatars/generated"
    echo "Output P1: $OUTPUT_DIR/phase1"
    echo "Output P2: $OUTPUT_DIR/phase2"
    
    echo ""
    echo "=== Generated Avatars ==="
    local avatar_count=$(find "$ASSETS_DIR/avatars/generated" -name "opt_*.png" 2>/dev/null | wc -l)
    echo "Total: $avatar_count"
    find "$ASSETS_DIR/avatars/generated" -name "opt_*.png" -type f 2>/dev/null | while read f; do
        echo "  - $(basename "$f")"
    done | head -10
    
    echo ""
    echo "=== Phase 1 Videos ==="
    local p1_count=$(find "$OUTPUT_DIR/phase1" -name "*.mp4" 2>/dev/null | wc -l)
    local p1_size=$(du -sh "$OUTPUT_DIR/phase1" 2>/dev/null | cut -f1 || echo "0")
    echo "Total: $p1_count videos ($p1_size)"
    
    echo ""
    echo "=== Phase 2 Videos ==="
    local p2_count=$(find "$OUTPUT_DIR/phase2" -name "*.mp4" 2>/dev/null | wc -l)
    local p2_size=$(du -sh "$OUTPUT_DIR/phase2" 2>/dev/null | cut -f1 || echo "0")
    echo "Total: $p2_count videos ($p2_size)"
    
    echo ""
    echo "=== Recent Logs ==="
    tail -20 "$LOGS_DIR/production.log" 2>/dev/null || echo "No logs"
}

# ============================================
# HELP
# ============================================

show_help() {
    cat << EOF
============================================
     PRODUCTION SCRIPT - Content Pipeline
============================================

Usage: $0 [options]

GENERAL OPTIONS:
  --help, -h              Show this help
  --phase, -p             Production phase (1 or 2)
  --character, -c         Character ID
  --audio, -a             Path to audio file
  --variant, -v           Character variant (default, casual, etc.)
  --quality, -q           Quality: low, medium, high, ultra (Phase 2)
  --title, -t             Video title
  --output, -o            Specific output path

AVATAR OPTIONS:
  --generate-avatar       Only generate avatar
  --all-variants          Generate all character variants

PRODUCTION OPTIONS:
  --all                   Run both phases (1 and 2)
  --batch file.json       Run batch production from JSON
  --stats                 Show statistics

============================================
     KARAOKE PRODUCTION
============================================

KARAOKE OPTIONS:
  --karaoke               Enable karaoke mode
  --lyrics, -l FILE       Lyrics file (.txt or .lrc format)
  --style, -s STYLE       Visual style: anime, kpop, minimalist, classic (default: anime)
  --audience, -aud TYPE   Target audience: children, teens, young_adults, general (default: general)
  --language, -lang LANG  Lyrics language: ja, en, es, ko, zh (auto-detect if not specified)
  --music, -m SOURCE      Music source: pixabay or file (default: pixabay)
  --music-query, -q QUERY Search query for Pixabay music
  --audio FILE            Pre-mixed audio file (overrides music source)
  --no-subtitles          Disable subtitle overlay
  --romanize              Show romanized lyrics (for non-Latin scripts)
  --quick                 Quick karaoke with auto-detected settings

EXAMPLES - AVATAR GENERATION:

  # Generate avatar for a character
  $0 --generate-avatar --character yuki-chan
  $0 --generate-avatar --character kenji-rojo --variant romantic

EXAMPLES - PHASE 1 & 2:

  # Phase 1 production (short video with API)
  $0 --phase 1 --character yuki-chan --audio audio.mp3
  $0 --phase 1 --character kenji-rojo --audio script.mp3 --variant romantic

  # Phase 2 production (long video local)
  $0 --phase 2 --character sora-hime --audio podcast.mp3
  $0 --phase 2 --character mika-sweet --audio audio.mp3 --quality high

  # Full production (both phases)
  $0 --all --character yuki-chan --audio script.mp3

EXAMPLES - KARAOKE:

  # Basic karaoke with anime style
  $0 --karaoke --lyrics song.txt --style anime

  # K-Pop style for teens with character avatar
  $0 --karaoke --lyrics kpop_song.lrc --style kpop --audience teens --character singer-avatar

  # Karaoke with specific music from Pixabay
  $0 --karaoke --lyrics lyrics.txt --music-query "jpop+love+song" --style anime

  # Karaoke with pre-mixed audio (voice + music already combined)
  $0 --karaoke --lyrics song.txt --audio /path/to/mixed_audio.mp3

  # Multilingual support (Japanese with romanized subtitles)
  $0 --karaoke --lyrics japanese_song.lrc --language ja --romanize --style anime

  # Minimalist style for general audience
  $0 --karaoke --lyrics simple.txt --style minimalist --audience general --no-subtitles

  # Quick karaoke (auto-detects from lyrics)
  $0 --karaoke --quick --lyrics song.txt

REQUIREMENTS:
  - Python 3.9+
  - FFmpeg and FFprobe (for Phase 2 and Karaoke)
  - QWEN_API_KEY: For text processing and AI operations (Qwen API)
  - A2E_API_KEY: For video production (Phase 1) - REQUIRED for karaoke lipsync
  - PIXABAY_API_KEY: For music download (Karaoke)

CONFIGURATION FILES:
  - config/avatars/characters.json: Character configuration and prompts

KARAOKE OUTPUT:
  - Lyrics: $PROJECT_ROOT/karaoke_lyrics/
  - Voices: $PROJECT_ROOT/karaoke_voices/
  - Mixed: $PROJECT_ROOT/karaoke_mixed/
  - Videos: $PROJECT_ROOT/karaoke_videos/

EOF
}

# ============================================
# MAIN ENTRY POINT
# ============================================

main() {
    # Default values
    PHASE=""
    CHARACTER=""
    AUDIO=""
    VARIANT="default"
    QUALITY="medium"
    TITLE=""
    OUTPUT=""
    MODE=""
    BATCH_FILE=""

    # Karaoke values
    KARAOKE_MODE=false
    LYRICS_FILE=""
    STYLE="anime"
    AUDIENCE="general"
    LANGUAGE="auto"
    MUSIC_SOURCE="pixabay"
    MUSIC_QUERY=""
    ROMANIZE=false
    NO_SUBTITLES=false
    QUICK_KARAOKE=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --phase|-p)
                PHASE="$2"
                shift 2
                ;;
            --character|-c)
                CHARACTER="$2"
                shift 2
                ;;
            --audio|-a)
                AUDIO="$2"
                shift 2
                ;;
            --variant|-v)
                VARIANT="$2"
                shift 2
                ;;
            --quality|-q)
                QUALITY="$2"
                shift 2
                ;;
            --title|-t)
                TITLE="$2"
                shift 2
                ;;
            --output|-o)
                OUTPUT="$2"
                shift 2
                ;;
            --generate-avatar)
                MODE="generate_avatar"
                shift
                ;;
            --all-variants)
                MODE="all_variants"
                shift
                ;;
            --all)
                MODE="all"
                shift
                ;;
            --batch)
                BATCH_FILE="$2"
                MODE="batch"
                shift 2
                ;;
            --stats)
                MODE="stats"
                shift
                ;;
            # Karaoke options
            --karaoke)
                KARAOKE_MODE=true
                shift
                ;;
            --lyrics|-l)
                LYRICS_FILE="$2"
                shift 2
                ;;
            --style|-s)
                STYLE="$2"
                shift 2
                ;;
            --audience|-aud)
                AUDIENCE="$2"
                shift 2
                ;;
            --language|-lang)
                LANGUAGE="$2"
                shift 2
                ;;
            --music|-m)
                MUSIC_SOURCE="$2"
                shift 2
                ;;
            --music-query|-q)
                MUSIC_QUERY="$2"
                shift 2
                ;;
            --romanize)
                ROMANIZE=true
                shift
                ;;
            --no-subtitles)
                NO_SUBTITLES=true
                shift
                ;;
            --quick)
                QUICK_KARAOKE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Handle karaoke mode
    if [ "$KARAOKE_MODE" == true ]; then
        log_info "Karaoke mode enabled"

        if [ "$QUICK_KARAOKE" == true ]; then
            # Quick karaoke - lyrics file required
            if [ -z "$LYRICS_FILE" ]; then
                log_error "--lyrics is required for quick karaoke mode"
                exit 1
            fi
            quick_karaoke "$LYRICS_FILE" "$STYLE"
            exit $?
        fi

        # Full karaoke mode
        if [ -z "$LYRICS_FILE" ]; then
            log_error "--lyrics is required for karaoke mode"
            echo ""
            show_help
            exit 1
        fi

        # Build options string
        local karaoke_options=""
        if [ "$ROMANIZE" == true ]; then
            karaoke_options="romanize"
        fi
        if [ "$NO_SUBTITLES" == true ]; then
            if [ -n "$karaoke_options" ]; then
                karaoke_options="${karaoke_options}:no-subtitles"
            else
                karaoke_options="no-subtitles"
            fi
        fi

        production_karaoke "$CHARACTER" "$LYRICS_FILE" "$STYLE" "$AUDIENCE" "$LANGUAGE" "$MUSIC_SOURCE" "$MUSIC_QUERY" "$AUDIO" "$karaoke_options"
        exit $?
    fi

    # Verify operation mode
    if [ "$MODE" == "stats" ]; then
        show_stats
        exit 0
    fi

    # Verify basic dependencies
    check_dependencies
    check_config

    # Execute according to mode
    case $MODE in
        generate_avatar)
            if [ -z "$CHARACTER" ]; then
                log_error "--character is required to generate avatar"
                exit 1
            fi
            generate_avatar "$CHARACTER" "$VARIANT"
            ;;
        all_variants)
            if [ -z "$CHARACTER" ]; then
                log_error "--character is required"
                exit 1
            fi
            generate_all_variants "$CHARACTER"
            ;;
        all)
            if [ -z "$CHARACTER" ] || [ -z "$AUDIO" ]; then
                log_error "--character and --audio are required for full production"
                exit 1
            fi
            production_all "$CHARACTER" "$AUDIO" "$VARIANT"
            ;;
        batch)
            if [ -z "$BATCH_FILE" ]; then
                log_error "Batch file is required for batch mode"
                exit 1
            fi
            production_batch "$BATCH_FILE"
            ;;
        *)
            # Phase mode
            if [ -z "$PHASE" ]; then
                log_error "A phase must be specified (--phase 1 or --phase 2)"
                echo ""
                show_help
                exit 1
            fi

            if [ -z "$CHARACTER" ]; then
                log_error "--character is required"
                exit 1
            fi

            if [ -z "$AUDIO" ]; then
                log_error "--audio is required"
                exit 1
            fi

            if [ "$PHASE" == "1" ]; then
                production_phase1 "$CHARACTER" "$AUDIO" "$VARIANT" "$TITLE"
            elif [ "$PHASE" == "2" ]; then
                production_phase2 "$CHARACTER" "$AUDIO" "$VARIANT" "$QUALITY" "$TITLE"
            else
                log_error "Invalid phase: $PHASE (must be 1 or 2)"
                exit 1
            fi
            ;;
    esac
}

# Execute main
main "$@"
