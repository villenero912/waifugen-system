import os
import requests
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("ReplicateMusic")

class ReplicateMusicGenerator:
    """
    Utility for generating music via Replicate API (MusicGen).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("REPLICATE_API_KEY")
        self.base_url = "https://api.replicate.com/v1"
        
        if not self.api_key:
            logger.error("REPLICATE_API_KEY not found. Music generation will fail.")

    def generate_music(self, prompt: str, duration: int = 15, model: str = "meta/musicgen:671ac645") -> Optional[str]:
        """
        Calls Replicate MusicGen to generate a music track.
        
        Args:
            prompt: Text description of the music (e.g., 'K-pop upbeat dance, 120bpm')
            duration: Duration in seconds
            model: Replicate model identifier
            
        Returns:
            URL of the generated audio file
        """
        if not self.api_key:
            return None

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "version": "671ac64540ef4c2514605978c45480e34c919d36371728cce7183e8460662d51", # Default to MusicGen Melody
            "input": {
                "prompt": prompt,
                "duration": duration,
                "model_version": "stereo-large",
                "output_format": "mp3"
            }
        }

        try:
            # Create prediction
            response = requests.post(f"{self.base_url}/predictions", headers=headers, json=payload)
            response.raise_for_status()
            prediction = response.json()
            prediction_id = prediction["id"]

            # Poll for completion
            logger.info(f"Replicate prediction started: {prediction_id}")
            while True:
                poll_response = requests.get(f"{self.base_url}/predictions/{prediction_id}", headers=headers)
                poll_response.raise_for_status()
                status_data = poll_response.json()
                
                status = status_data["status"]
                if status == "succeeded":
                    output_url = status_data["output"]
                    logger.info(f"Music generation successful: {output_url}")
                    return output_url
                elif status == "failed":
                    logger.error(f"Music generation failed: {status_data.get('error')}")
                    return None
                
                time.sleep(2)  # Wait 2 seconds between polls
                
        except Exception as e:
            logger.error(f"Error calling Replicate API: {e}")
            return None

if __name__ == "__main__":
    # Test generation
    logging.basicConfig(level=logging.INFO)
    gen = ReplicateMusicGenerator()
    test_prompt = "Upbeat K-pop dance track with catchy synth melody, 128bpm"
    result = gen.generate_music(test_prompt)
    print(f"Result: {result}")
