"""
Piper TTS Client - Local Text-to-Speech Integration
Provides high-quality voice generation using Piper TTS
"""

import asyncio
import subprocess
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class PiperTTSClient:
    """
    Client for Piper TTS (Text-to-Speech) service
    Generates natural-sounding voice audio from text
    """
    
    def __init__(self, piper_host: str = "piper", piper_port: int = 10200):
        self.piper_host = piper_host
        self.piper_port = piper_port
        self.voices_dir = Path("/voices")
        
    async def generate_speech(
        self,
        text: str,
        voice: str = "en_US-amy-medium",
        output_path: str = "/tmp/output.wav",
        speed: float = 1.0
    ) -> Optional[str]:
        """
        Generate speech from text using Piper TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice model to use (default: en_US-amy-medium)
            output_path: Where to save the audio file
            speed: Speaking speed multiplier (0.5 = slow, 2.0 = fast)
            
        Returns:
            Path to generated audio file, or None if failed
        """
        try:
            # Prepare command
            cmd = [
                "docker", "exec", "-i", "waifugen_piper",
                "piper",
                "--model", voice,
                "--output_file", output_path,
            ]
            
            if speed != 1.0:
                cmd.extend(["--length_scale", str(1.0 / speed)])
            
            # Run Piper TTS
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send text via stdin
            stdout, stderr = await process.communicate(input=text.encode('utf-8'))
            
            if process.returncode == 0:
                logger.info(f"Generated speech for: {text[:50]}... -> {output_path}")
                return output_path
            else:
                logger.error(f"Piper TTS failed: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return None
    
    def list_available_voices(self) -> list:
        """
        List all available voice models
        
        Returns:
            List of voice model names
        """
        # Default voices included
        return [
            "en_US-amy-medium",      # English (US) - Female
            "en_GB-alan-medium",     # English (GB) - Male
            "es_ES-mls-medium",      # Spanish - Neural
            "ja_JP-ayumi-medium",    # Japanese - Female (if downloaded)
        ]
    
    async def test_connection(self) -> bool:
        """
        Test if Piper TTS service is available
        
        Returns:
            True if service is responding
        """
        try:
            result = await self.generate_speech(
                "Test",
                output_path="/tmp/test_piper.wav"
            )
            return result is not None
        except Exception:
            return False


# Usage example
if __name__ == "__main__":
    async def main():
        client = PiperTTSClient()
        
        # Test connection
        if await client.test_connection():
            print("✅ Piper TTS is working!")
        else:
            print("❌ Piper TTS connection failed")
        
        # Generate sample
        result = await client.generate_speech(
            "Hello, I am Miyuki. Welcome to my channel!",
            voice="en_US-amy-medium",
            output_path="/tmp/miyuki_intro.wav"
        )
        
        if result:
            print(f"Audio generated: {result}")
    
    asyncio.run(main())
