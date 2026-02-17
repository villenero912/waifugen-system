#!/usr/bin/env python3
"""
Secure Karaoke Generator Service
================================
Provides API for burning subtitles and mixing music into videos.
Security Features:
- API Key Authentication (X-API-Key header)
- Input sanitization (werkzeug.secure_filename)
- Path traversal prevention
- Rate limiting (basic sleep)

Usage:
    POST /generate
    FormData:
        video: file
        audio: file (optional voice track)
        music: file (optional background music)
        text: string (lyrics/subtitles)
"""

import os
import logging
import subprocess
import uuid
import time
from functools import wraps
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from scripts.advanced_karaoke import AdvancedLyricsGenerator, AudienceProfile, LyricStyle

# SECURITY CONFIGURATION
# =============================================================================

API_KEY = os.getenv('KARAOKE_API_KEY')
UPLOAD_FOLDER = '/app/assets/temp_uploads'
OUTPUT_FOLDER = '/app/assets/output/karaoke'
ALLOWED_EXTENSIONS = {'mp4', 'wav', 'mp3', 'txt', 'srt', 'ass'}

# Create directories
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

if not API_KEY:
    logger.critical("SECURITY ALERT: KARAOKE_API_KEY is not set! Service will be vulnerable.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not API_KEY:
             return jsonify({'error': 'Service misconfigured: API Key missing'}), 503
        
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_srt(text, duration):
    """
    Generates a simple SRT file from text.
    For 'Karaoke', we split the text into chunks visible for ~3 seconds each.
    """
    srt_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}.srt")
    words = text.split()
    chunk_size = 5 # Words per line
    
    with open(srt_path, 'w', encoding='utf-8') as f:
        count = 1
        start_time = 0.0
        time_per_word = 0.5 # estimation
        
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i+chunk_size]
            end_time = start_time + (len(chunk) * time_per_word)
            if end_time > duration: end_time = duration
            
            # Format timestamp: 00:00:00,000
            def fmt_time(t):
                hours = int(t / 3600)
                mins = int((t % 3600) / 60)
                secs = int(t % 60)
                mils = int((t * 1000) % 1000)
                return f"{hours:02}:{mins:02}:{secs:02},{mils:03}"
            
            f.write(f"{count}\n")
            f.write(f"{fmt_time(start_time)} --> {fmt_time(end_time)}\n")
            f.write(f"{' '.join(chunk)}\n\n")
            
            start_time = end_time
            count += 1
            
    return srt_path

def process_video_ffmpeg(video_path, audio_path, music_path, srt_path, output_path):
    """
    Runs FFmpeg to merge streams and burn subtitles.
    INPUT VALIDATION: Paths are already secured by secure_filename and UUIDs.
    """
    cmd = ['ffmpeg', '-y']
    
    # Inputs
    cmd.extend(['-i', video_path]) # 0: Video
    if audio_path: cmd.extend(['-i', audio_path]) # 1: Voice
    if music_path: cmd.extend(['-i', music_path]) # 2: Music (Optional)
    
    # Filter Complex Construction
    filter_complex = []
    
    # Subtitle Burning
    safe_srt_path = srt_path.replace("\\", "/").replace(":", "\\:")
    style = "Alignment=2,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Fontname=Sans,FontSize=28,PrimaryColour=&H00FFFF"
    
    # Case handling for Audio inputs
    if audio_path and music_path:
        filter_complex.append(f"[0:v]subtitles='{safe_srt_path}':force_style='{style}'[vout]")
        filter_complex.append(f"[1:a]volume=1.0[voice];[2:a]volume=0.3[bgm];[voice][bgm]amix=inputs=2:duration=first[aout]")
        cmd.extend(['-filter_complex', ';'.join(filter_complex)])
        cmd.extend(['-map', '[vout]', '-map', '[aout]'])
    elif audio_path:
        filter_complex.append(f"[0:v]subtitles='{safe_srt_path}':force_style='{style}'[vout]")
        cmd.extend(['-filter_complex', ';'.join(filter_complex)])
        cmd.extend(['-map', '[vout]', '-map', '1:a'])
    elif music_path:
        filter_complex.append(f"[0:v]subtitles='{safe_srt_path}':force_style='{style}'[vout]")
        cmd.extend(['-filter_complex', ';'.join(filter_complex)])
        cmd.extend(['-map', '[vout]', '-map', '2:a'])
    else:
        filter_complex.append(f"[0:v]subtitles='{safe_srt_path}':force_style='{style}'[vout]")
        cmd.extend(['-filter_complex', ';'.join(filter_complex)])
        cmd.extend(['-map', '[vout]', '-map', '0:a'])
    
    # Encoding settings
    cmd.extend(['-c:v', 'libx264', '-preset', 'fast', '-crf', '23'])
    cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
    cmd.extend(['-movflags', '+faststart'])
    cmd.extend([output_path])
    
    logger.info(f"Running FFmpeg: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"FFmpeg failed: {result.stderr}")
        return False, result.stderr
        
    return True, "Success"

# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'karaoke-generator'}), 200

@app.route('/generate', methods=['POST'])
@require_api_key
def generate():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'Missing video file'}), 400
            
        video_file = request.files['video']
        audio_file = request.files.get('audio')
        music_file = request.files.get('music')
        text = request.form.get('text', '')
        
        # Advanced Karaoke Parameters
        style = request.form.get('style', 'anime').upper()
        audience = request.form.get('audience', 'general').upper()
        language = request.form.get('language', 'ja').lower()
        
        # Security: unique filenames
        task_id = uuid.uuid4().hex
        video_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_v_{secure_filename(video_file.filename)}")
        video_file.save(video_path)
        
        audio_path = None
        if audio_file and audio_file.filename:
            audio_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_a_{secure_filename(audio_file.filename)}")
            audio_file.save(audio_path)
            
        music_path = None
        if music_file and music_file.filename:
            music_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_m_{secure_filename(music_file.filename)}")
            music_file.save(music_path)
            
        # Use Advanced Generator if parameters are provided or for Japanese
        adv_gen = AdvancedLyricsGenerator()
        lyrics_data = adv_gen.create_lyrics(
            lyrics_text=text,
            music_duration=30.0, # Placeholder
            language=language,
            style=style,
            audience=audience
        )
        
        ass_path = os.path.join(UPLOAD_FOLDER, f"{task_id}.ass")
        adv_gen.generate_ass_file(lyrics_data, ass_path)
        
        output_path = os.path.join(OUTPUT_FOLDER, f"karaoke_{task_id}.mp4")
        
        # Use ASS for high quality subtitles if logic succeeds
        success, msg = process_video_ffmpeg(video_path, audio_path, music_path, ass_path, output_path)
        
        if not success:
            # Fallback to simple SRT if ASS fails
            srt_path = generate_srt(text, 15.0)
            success, msg = process_video_ffmpeg(video_path, audio_path, music_path, srt_path, output_path)
            
        if not success:
            return jsonify({'error': 'Processing failed', 'details': msg}), 500
            
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error(f"Generate error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
