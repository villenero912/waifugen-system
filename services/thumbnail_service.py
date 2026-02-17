#!/usr/bin/env python3
"""
Secured Thumbnail Service with API Key Authentication
Fixes: Missing authentication vulnerability
"""

import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Tuple
from functools import wraps
from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageDraw, ImageFont
import requests

# Configure logging (sanitized)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security: API Key from environment
API_KEY = os.getenv('THUMBNAIL_SERVICE_API_KEY')
if not API_KEY:
    logger.error("THUMBNAIL_SERVICE_API_KEY not set! Service will reject all requests.")

# Platform configurations
PLATFORM_CONFIGS = {
    'tiktok': {'width': 1080, 'height': 1920, 'aspect_ratio': '9:16', 'format': 'JPEG', 'quality': 90},
    'instagram': {'width': 1080, 'height': 1920, 'aspect_ratio': '9:16', 'format': 'JPEG', 'quality': 90},
    'youtube': {'width': 1280, 'height': 720, 'aspect_ratio': '16:9', 'format': 'JPEG', 'quality': 95}
}

CHARACTER_COLORS = {
    'Miyuki Sakura': {'primary': '#FF69B4', 'secondary': '#FFB6C1'},
    'Airi Neo': {'primary': '#9D4EDD', 'secondary': '#C77DFF'},
    'Aiko Hayashi': {'primary': '#E63946', 'secondary': '#F1FAEE'},
    'Rio Mizuno': {'primary': '#06FFA5', 'secondary': '#FFFB46'},
    'Chiyo Sasaki': {'primary': '#8B4513', 'secondary': '#D2691E'},
    'default': {'primary': '#FF1493', 'secondary': '#FFB6C1'}
}


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning(f"Request without API key from {request.remote_addr}")
            return jsonify({'error': 'API key required'}), 401
        
        if api_key != API_KEY:
            logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def validate_input(video_url: str, platform: str, character_name: str) -> Tuple[bool, str]:
    """Validate and sanitize inputs"""
    # Validate URL
    if not video_url or not video_url.startswith(('http://', 'https://')):
        return False, "Invalid video URL"
    
    # Validate platform
    if platform.lower() not in PLATFORM_CONFIGS:
        return False, f"Invalid platform. Must be one of: {', '.join(PLATFORM_CONFIGS.keys())}"
    
    # Validate character name (prevent path traversal)
    if not character_name or len(character_name) > 100:
        return False, "Invalid character name"
    
    if any(char in character_name for char in ['/', '\\', '..', '<', '>', '|']):
        return False, "Character name contains invalid characters"
    
    return True, "OK"


class ThumbnailGenerator:
    """Generates platform-optimized thumbnails"""
    
    def __init__(self, video_url: str, platform: str, character_name: str, text_overlay: str = ''):
        self.video_url = video_url
        self.platform = platform.lower()
        self.character_name = character_name
        self.text_overlay = text_overlay or character_name
        self.config = PLATFORM_CONFIGS.get(self.platform, PLATFORM_CONFIGS['tiktok'])
        self.colors = CHARACTER_COLORS.get(character_name, CHARACTER_COLORS['default'])
        
    def download_video(self, output_path: str) -> bool:
        """Download video from URL with timeout"""
        try:
            # Sanitized logging (no full URL)
            logger.info(f"Downloading video for {self.character_name}")
            response = requests.get(self.video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to download video: {type(e).__name__}")
            return False
    
    def extract_frame(self, video_path: str, output_path: str, timestamp: float = 3.0) -> bool:
        """Extract frame from video using FFmpeg"""
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(timestamp),
                '-vframes', '1',
                '-vf', f'scale={self.config["width"]}:{self.config["height"]}:force_original_aspect_ratio=decrease,pad={self.config["width"]}:{self.config["height"]}:(ow-iw)/2:(oh-ih)/2',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"Frame extracted successfully")
                return True
            else:
                logger.error(f"FFmpeg error: {result.returncode}")
                return False
        except Exception as e:
            logger.error(f"Failed to extract frame: {type(e).__name__}")
            return False
    
    def add_overlay(self, frame_path: str, output_path: str) -> bool:
        """Add text overlay and branding to frame"""
        try:
            img = Image.open(frame_path)
            draw = ImageDraw.Draw(img)
            
            # Add gradient overlay at bottom
            gradient = Image.new('RGBA', (img.width, 300), (0, 0, 0, 0))
            gradient_draw = ImageDraw.Draw(gradient)
            
            for i in range(300):
                alpha = int((i / 300) * 180)
                gradient_draw.rectangle([(0, i), (img.width, i + 1)], fill=(0, 0, 0, alpha))
            
            img.paste(gradient, (0, img.height - 300), gradient)
            draw = ImageDraw.Draw(img)
            
            # Load font
            try:
                font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 80)
                font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 40)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw character name
            text_bbox = draw.textbbox((0, 0), self.text_overlay, font=font_large)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (img.width - text_width) // 2
            text_y = img.height - 200
            
            # Text shadow
            draw.text((text_x + 3, text_y + 3), self.text_overlay, font=font_large, fill=(0, 0, 0, 200))
            # Main text
            draw.text((text_x, text_y), self.text_overlay, font=font_large, fill=self.colors['primary'])
            
            # Watermark
            watermark = "WaifuGen"
            watermark_bbox = draw.textbbox((0, 0), watermark, font=font_small)
            watermark_width = watermark_bbox[2] - watermark_bbox[0]
            watermark_x = img.width - watermark_width - 30
            watermark_y = 30
            
            draw.text((watermark_x, watermark_y), watermark, font=font_small, fill=(255, 255, 255, 180))
            
            # Save
            img.save(output_path, self.config['format'], quality=self.config['quality'])
            logger.info(f"Overlay added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add overlay: {type(e).__name__}")
            return False
    
    def generate(self) -> Tuple[bool, str]:
        """Main generation flow"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            video_path = os.path.join(temp_dir, 'video.mp4')
            frame_path = os.path.join(temp_dir, 'frame.jpg')
            thumbnail_path = os.path.join(temp_dir, 'thumbnail.jpg')
            
            if not self.download_video(video_path):
                return False, "Failed to download video"
            
            if not self.extract_frame(video_path, frame_path):
                return False, "Failed to extract frame"
            
            if not self.add_overlay(frame_path, thumbnail_path):
                return False, "Failed to add overlay"
            
            return True, thumbnail_path
            
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {type(e).__name__}")
            return False, str(e)


@app.route('/generate', methods=['POST'])
@require_api_key  # ← SECURITY: Require API key
def generate_thumbnail():
    """API endpoint to generate thumbnail"""
    try:
        # Get parameters
        video_url = request.form.get('video_url')
        platform = request.form.get('platform', 'tiktok')
        character_name = request.form.get('character_name', 'WaifuGen')
        text_overlay = request.form.get('text_overlay', '')
        
        # Validate inputs
        valid, error = validate_input(video_url, platform, character_name)
        if not valid:
            logger.warning(f"Invalid input: {error}")
            return jsonify({'error': error}), 400
        
        # Generate thumbnail
        generator = ThumbnailGenerator(video_url, platform, character_name, text_overlay)
        success, result = generator.generate()
        
        if success:
            return send_file(result, mimetype='image/jpeg', as_attachment=True, download_name='thumbnail.jpg')
        else:
            return jsonify({'error': result}), 500
            
    except Exception as e:
        logger.error(f"API error: {type(e).__name__}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint (no auth required)"""
    return jsonify({
        'status': 'healthy',
        'service': 'thumbnail-generator',
        'auth': 'enabled' if API_KEY else 'disabled'
    }), 200


if __name__ == '__main__':
    if not API_KEY:
        logger.critical("THUMBNAIL_SERVICE_API_KEY not set! Exiting.")
        exit(1)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
