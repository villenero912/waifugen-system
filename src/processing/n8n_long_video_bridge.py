
import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from processing.comfyui_bridge import ComfyUIBridge

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("N8N_Bridge")

async def run_gpu_production(request_data):
    """
    Bridge between n8n and the Hybrid Video Processor.
    Uses ComfyUI on RunPod for High-Quality, unfiltered production.
    """
    # Load environment variables (they should be loaded by the parent process or N8N)
    config = {
        "runpod_api_key": os.getenv("RUNPOD_API_KEY"),
        "budget_limit": 500.0,
    }

    if not config["runpod_api_key"]:
        logger.error("❌ RUNPOD_API_KEY not found in environment")
        print(json.dumps({"status": "error", "message": "RUNPOD_API_KEY missing"}))
        return

    bridge = ComfyUIBridge(config)
    
    character_data = {
        "id": request_data.get("character_id"),
        "name": request_data.get("character_name", "Unknown"),
        "trigger_word": request_data.get("trigger_word", "")
    }
    
    prompt = request_data.get("prompt")
    workflow = request_data.get("workflow", "basic_portrait")

    logger.info(f"🚀 Dispatching to ComfyUI on RunPod: {character_data['name']}")
    
    try:
        result = await bridge.generate(character_data, prompt, workflow)
        print(json.dumps(result))
    except Exception as e:
        logger.error(f"❌ Bridge execution failed: {e}")
        print(json.dumps({"status": "error", "message": str(e)}))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
            asyncio.run(run_gpu_production(data))
        except Exception as e:
            print(json.dumps({"status": "error", "message": f"Invalid JSON input: {e}"}))
    else:
        print(json.dumps({"status": "error", "message": "No input data provided"}))
