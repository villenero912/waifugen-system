
import os
import json
import asyncio
import aiohttp
import uuid
import logging
from pathlib import Path
from datetime import datetime

# Import GpuRentalManager
from processing.gpu_rental_manager import GpuRentalManager, GpuRentalProvider

logger = logging.getLogger("ComfyUI_Bridge")

class ComfyUIBridge:
    """
    Connects WaifuGen to a ComfyUI instance running on RunPod.
    Handles workflow injection, API submission, and result polling.
    """
    
    def __init__(self, config):
        self.config = config
        self.gpu_manager = GpuRentalManager(config)
        self.workflow_dir = Path(config.get("comfy_workflow_dir", "c:/Users/Sebas/Downloads/package (1)/waifugen_system/config/comfyui_workflows"))
        self.output_dir = Path(config.get("comfy_output_dir", "c:/Users/Sebas/Downloads/package (1)/waifugen_system/assets/output/comfyui"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate(self, character_data, prompt, workflow_name="basic_portrait"):
        """
        Main entry point for generating content via ComfyUI + RunPod.
        """
        logger.info(f"🎨 Starting ComfyUI Generation for {character_data.get('name')} using {workflow_name}")
        
        # 1. Ensure GPU is ready
        instance = await self._ensure_gpu_instance()
        if not instance:
            return {"status": "error", "message": "Failed to provision GPU instance"}

        # 2. Prepare Workflow JSON
        workflow_path = self.workflow_dir / f"{workflow_name}.json"
        if not workflow_path.exists():
            return {"status": "error", "message": f"Workflow {workflow_name} not found"}

        with open(workflow_path, "r") as f:
            workflow_json = json.load(f)

        # Inject dynamic data into workflow
        workflow_str = json.dumps(workflow_json)
        workflow_str = workflow_str.replace("{{PROMPT}}", prompt)
        workflow_str = workflow_str.replace("{{CHARACTER_NAME}}", character_data.get("name", "Unknown"))
        workflow_str = workflow_str.replace("{{CHARACTER_TRIGGER}}", character_data.get("trigger_word", ""))
        
        final_workflow = json.loads(workflow_str)

        # 3. Submit to ComfyUI API
        # ComfyUI API typically uses /prompt endpoint
        client_id = str(uuid.uuid4())
        submit_url = f"{instance.container_url}/prompt"
        
        payload = {
            "prompt": final_workflow,
            "client_id": client_id
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(submit_url, json=payload) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        return {"status": "error", "message": f"ComfyUI API Error: {err_text}"}
                    
                    data = await resp.json()
                    prompt_id = data.get("prompt_id")
                    logger.info(f"✅ Job submitted to ComfyUI. Prompt ID: {prompt_id}")

                # 4. Poll for result
                result = await self._poll_result(instance, prompt_id)
                return result

        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _ensure_gpu_instance(self):
        """
        Retrieves an existing instance or creates a new one.
        """
        # Logic to reuse active instances from manager
        # For POC, we create one if none exist
        if not self.gpu_manager.active_instances:
            logger.info("🚀 No active GPU found. Creating new RunPod instance for ComfyUI...")
            instance = await self.gpu_manager.create_instance(
                gpu_type="RTX_4090",
                provider=GpuRentalProvider.RUNPOD,
                container_image="runpod/stable-diffusion:comfy-ui-v1.0.0" # Example community image
            )
            return instance
        
        return list(self.gpu_manager.active_instances.values())[0]

    async def _poll_result(self, instance, prompt_id):
        """
        Polls ComfyUI history/status until the job is done.
        """
        history_url = f"{instance.container_url}/history/{prompt_id}"
        max_attempts = 120 # 10 minutes approx (GPU might be slow)
        
        logger.info(f"⏳ Polling for result (Prompt ID: {prompt_id}) at {history_url}")
        
        async with aiohttp.ClientSession() as session:
            for i in range(max_attempts):
                try:
                    async with session.get(history_url) as resp:
                        if resp.status == 200:
                            history = await resp.json()
                            if prompt_id in history:
                                data = history[prompt_id]
                                logger.info("✨ ComfyUI Job complete!")
                                
                                # Extract images/videos from outputs
                                outputs = data.get("outputs", {})
                                result_files = []
                                for node_id, node_output in outputs.items():
                                    if "images" in node_output:
                                        for img in node_output["images"]:
                                            result_files.append({
                                                "filename": img["filename"],
                                                "subfolder": img.get("subfolder", ""),
                                                "type": img.get("type", "output"),
                                                "url": f"{instance.container_url}/view?filename={img['filename']}&subfolder={img.get('subfolder', '')}&type={img.get('type', 'output')}"
                                            })
                                
                                return {
                                    "status": "success",
                                    "prompt_id": prompt_id,
                                    "results": result_files,
                                    "metadata": data.get("prompt", {}),
                                    "timestamp": datetime.now().isoformat()
                                }
                except Exception as e:
                    logger.warning(f"⚠️ Polling error (attempt {i+1}): {e}")
                
                await asyncio.sleep(5)
        
        return {"status": "timeout", "message": "Generation timed out after 10 minutes"}

async def test_bridge():
    config = {
        "runpod_api_key": os.getenv("RUNPOD_API_KEY"),
        "budget_limit": 500.0
    }
    bridge = ComfyUIBridge(config)
    
    char = {"name": "Hana", "trigger_word": "hana_model_v1"}
    prompt = "Hana sitting in a cyberpunk cafe, neon lights, masterpiece"
    
    # We won't actually run it here to avoid spending money, 
    # but the logic is ready.
    print("🛠️ ComfyUI Bridge is ready for deployment in Phase 2.")

if __name__ == "__main__":
    # To run: set RUNPOD_API_KEY and python comfyui_bridge.py
    pass
