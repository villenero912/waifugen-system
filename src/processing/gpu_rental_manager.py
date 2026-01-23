"""
GPU Rental Manager Module

This module provides functionality for managing GPU rental services like RunPod and Modal.
It is a core component of Phase 2, enabling long-form video processing by leveraging
cloud GPU resources as a cost-effective alternative to traditional API-based rendering.

The module provides:
- GpuRentalProvider enum for supported GPU rental services
- GpuRentalManager class for managing GPU instances, containers, and job processing
- Integration with RunPod and Modal APIs for GPU resource management
- Cost estimation and budget management features
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp
import json
import logging
import time
import os
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GpuRentalProvider(Enum):
    """
    Enum representing supported GPU rental providers.
    
    Each provider has unique API endpoints, pricing models, and capabilities.
    Currently supported:
    - RUNPOD: Cloud GPU platform with containerized deployments
    - MODAL: Serverless GPU platform with easy scaling
    """
    RUNPOD = "runpod"
    MODAL = "modal"


@dataclass
class GpuInstance:
    """
    Data class representing a GPU instance configuration.
    
    Attributes:
        provider: The GPU rental provider (RunPod or Modal)
        instance_id: Unique identifier for the instance
        gpu_type: Type of GPU (e.g., "RTX 4090", "A100")
        gpu_count: Number of GPUs in the instance
        memory_gb: GPU memory in gigabytes
        hourly_rate: Cost per hour in USD
        status: Current instance status
        endpoint_url: API endpoint URL for the instance
        created_at: Timestamp when the instance was created
        container_url: URL for accessing the containerized service
    """
    provider: GpuRentalProvider
    instance_id: str
    gpu_type: str
    gpu_count: int
    memory_gb: int
    hourly_rate: float
    status: str = "pending"
    endpoint_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    container_url: Optional[str] = None


@dataclass
class GpuJob:
    """
    Data class representing a GPU processing job.
    
    Attributes:
        job_id: Unique identifier for the job
        instance_id: GPU instance running the job
        input_file: Path to input file for processing
        output_file: Path where output will be saved
        status: Current job status
        progress: Progress percentage (0-100)
        started_at: When the job started processing
        completed_at: When the job finished
        cost: Total cost incurred for this job
        error_message: Error message if job failed
    """
    job_id: str
    instance_id: str
    input_file: str
    output_file: str
    status: str = "queued"
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cost: float = 0.0
    error_message: Optional[str] = None


class GpuRentalManager:
    """
    Manager class for handling GPU rental operations across different providers.
    
    This class provides a unified interface for managing GPU instances and jobs
    across multiple cloud GPU providers. It handles:
    - Instance lifecycle management (create, start, stop, monitor)
    - Job submission and tracking
    - Cost estimation and budget management
    - Provider-specific API interactions
    
    The manager maintains internal state for active instances and jobs,
    providing a persistent view of GPU resource usage throughout the application lifecycle.
    
    Attributes:
        config: Configuration dictionary containing provider credentials and settings
        active_instances: Dictionary of currently running GPU instances
        completed_jobs: Dictionary of completed processing jobs
        budget_limit: Maximum monthly budget for GPU usage in USD
        current_spend: Total amount spent in the current billing period
    """
    
    # API endpoints for each provider
    RUNPOD_API_BASE = "https://api.runpod.io/v2"
    MODAL_API_BASE = "https://api.modal.com/v1"
    
    # Supported GPU configurations
    SUPPORTED_GPUS = {
        "RTX_4090": {
            "gpu_type": "RTX 4090",
            "memory_gb": 24,
            "gpu_count": 1,
            "hourly_rate": 0.69,
            "provider": GpuRentalProvider.RUNPOD
        },
        "RTX_3090": {
            "gpu_type": "RTX 3090",
            "memory_gb": 24,
            "gpu_count": 1,
            "hourly_rate": 0.50,
            "provider": GpuRentalProvider.RUNPOD
        },
        "A100_40GB": {
            "gpu_type": "A100 40GB",
            "memory_gb": 40,
            "gpu_count": 1,
            "hourly_rate": 1.10,
            "provider": GpuRentalProvider.RUNPOD
        },
        "A100_80GB": {
            "gpu_type": "A100 80GB",
            "memory_gb": 80,
            "gpu_count": 1,
            "hourly_rate": 2.00,
            "provider": GpuRentalProvider.RUNPOD
        },
        "L40S": {
            "gpu_type": "L40S",
            "memory_gb": 48,
            "gpu_count": 1,
            "hourly_rate": 1.50,
            "provider": GpuRentalProvider.RUNPOD
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the GPU Rental Manager with configuration.
        
        Args:
            config: Configuration dictionary containing:
                - runpod_api_key: API key for RunPod (optional)
                - modal_api_key: API key for Modal (optional)
                - budget_limit: Maximum monthly budget in USD
                - default_gpu: Default GPU type to request
                - region: Preferred region for GPU instances
        """
        self.config = config
        self.runpod_api_key = config.get("runpod_api_key", os.environ.get("RUNPOD_API_KEY", ""))
        self.modal_api_key = config.get("modal_api_key", os.environ.get("MODAL_API_KEY", ""))
        self.budget_limit = config.get("budget_limit", 100.0)
        self.default_gpu = config.get("default_gpu", "RTX_4090")
        self.region = config.get("region", "us-east-1")
        
        self.active_instances: Dict[str, GpuInstance] = {}
        self.completed_jobs: Dict[str, GpuJob] = {}
        self.current_spend = 0.0
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"GPU Rental Manager initialized with budget limit: ${self.budget_limit}")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_runpod_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for RunPod API requests.
        
        Returns:
            Dictionary containing Authorization and Content-Type headers.
        """
        return {
            "Authorization": f"Bearer {self.runpod_api_key}",
            "Content-Type": "application/json"
        }
    
    def _get_modal_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for Modal API requests.
        
        Returns:
            Dictionary containing Authorization and Content-Type headers.
        """
        return {
            "Authorization": f"Bearer {self.modal_api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_available_gpus(self, provider: GpuRentalProvider) -> List[Dict[str, Any]]:
        """
        Get list of available GPU types from a provider.
        """
        if provider == GpuRentalProvider.RUNPOD:
            return await self._get_runpod_gpus()
        elif provider == GpuRentalProvider.MODAL:
            return await self._get_modal_gpus()
        return []

    async def _get_runpod_gpus(self) -> List[Dict[str, Any]]:
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.RUNPOD_API_BASE}/gpu/availability",
                headers=self._get_runpod_headers(),
                timeout=30
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("gpus", [])
        except Exception as e:
            logger.error(f"Failed to fetch RunPod GPUs: {e}")
            return []
    
    def _get_modal_gpus(self) -> List[Dict[str, Any]]:
        """
        Fetch available GPU types from Modal.
        
        Returns:
            List of GPU specifications available on Modal.
        """
        try:
            response = requests.get(
                f"{self.MODAL_API_BASE}/gpus",
                headers=self._get_modal_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("gpus", [])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Modal GPUs: {e}")
            return []
    
    async def create_instance(
        self,
        gpu_type: str = "RTX_4090",
        provider: GpuRentalProvider = GpuRentalProvider.RUNPOD,
        container_image: str = "python:3.11-slim"
    ) -> GpuInstance:
        """
        Create and start a new GPU instance.
        """
        if gpu_type not in self.SUPPORTED_GPUS:
            raise ValueError(f"Unsupported GPU type: {gpu_type}")
        
        gpu_spec = self.SUPPORTED_GPUS[gpu_type]
        
        # Check budget before creating
        estimated_cost = gpu_spec["hourly_rate"]
        if self.current_spend + estimated_cost > self.budget_limit:
            raise RuntimeError(
                f"Budget exceeded. Current spend: ${self.current_spend:.2f}, "
                f"Budget limit: ${self.budget_limit:.2f}"
            )
        
        if provider == GpuRentalProvider.RUNPOD:
            return await self._create_runpod_instance(gpu_type, container_image)
        elif provider == GpuRentalProvider.MODAL:
            return await self._create_modal_instance(gpu_type, container_image)
        
        raise ValueError(f"Unsupported provider: {provider}")
    
    async def _create_runpod_instance(
        self,
        gpu_type: str,
        container_image: str
    ) -> GpuInstance:
        """
        Create a GPU instance on RunPod.
        """
        gpu_spec = self.SUPPORTED_GPUS[gpu_type]
        
        request_body = {
            "name": f"waifugen-{gpu_type}-{int(time.time())}",
            "imageName": container_image,
            "gpuTypeId": gpu_type,
            "gpuCount": gpu_spec["gpu_count"],
            "containerDiskInGb": 20,
            "volumeInGb": 50,
            "env": [
                {"key": "PYTHONUNBUFFERED", "value": "1"},
                {"key": "CUDA_VISIBLE_DEVICES", "value": "0"}
            ],
            "ports": "22/tcp,8888/tcp",
            "idleTimeout": 300
        }
        
        try:
            session = await self._get_session()
            async with session.post(
                f"{self.RUNPOD_API_BASE}/pod",
                headers=self._get_runpod_headers(),
                json=request_body,
                timeout=60
            ) as response:
                response.raise_for_status()
                data = await response.json()
                pod_data = data.get("pod", {})
                instance_id = pod_data.get("id")
                
                # Wait for instance to be ready
                instance = await self._wait_for_runpod_instance(instance_id)
                
                logger.info(f"RunPod instance created: {instance_id}")
                return instance
                
        except Exception as e:
            logger.error(f"Failed to create RunPod instance: {e}")
            raise RuntimeError(f"RunPod instance creation failed: {e}")
    
    async def _create_modal_instance(
        self,
        gpu_type: str,
        container_image: str
    ) -> GpuInstance:
        """
        Create a GPU instance on Modal.
        """
        gpu_spec = self.SUPPORTED_GPUS[gpu_type]
        
        request_body = {
            "gpu": gpu_type,
            "image": container_image,
            "timeout": 3600,
            "memory": f"{gpu_spec['memory_gb']}GB"
        }
        
        try:
            session = await self._get_session()
            async with session.post(
                f"{self.MODAL_API_BASE}/functions",
                headers=self._get_modal_headers(),
                json=request_body,
                timeout=60
            ) as response:
                response.raise_for_status()
                function_data = await response.json()
                instance_id = function_data.get("function_id")
                
                instance = GpuInstance(
                    provider=GpuRentalProvider.MODAL,
                    instance_id=instance_id,
                    gpu_type=gpu_spec["gpu_type"],
                    gpu_count=gpu_spec["gpu_count"],
                    memory_gb=gpu_spec["memory_gb"],
                    hourly_rate=gpu_spec["hourly_rate"],
                    status="running"
                )
                
                self.active_instances[instance_id] = instance
                logger.info(f"Modal instance created: {instance_id}")
                return instance
                
        except Exception as e:
            logger.error(f"Failed to create Modal instance: {e}")
            raise RuntimeError(f"Modal instance creation failed: {e}")
    
    async def _wait_for_runpod_instance(self, instance_id: str, timeout: int = 300) -> GpuInstance:
        """
        Wait for a RunPod instance to reach running status.
        """
        start_time = time.time()
        poll_interval = 10
        
        while time.time() - start_time < timeout:
            try:
                session = await self._get_session()
                async with session.get(
                    f"{self.RUNPOD_API_BASE}/pod/{instance_id}",
                    headers=self._get_runpod_headers(),
                    timeout=30
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    pod_data = data.get("pod", {})
                    status = pod_data.get("status")
                    
                    if status == "RUNNING":
                        gpu_type = pod_data.get("gpuType", "RTX 4090")
                        container_url = pod_data.get("directInvokeEndpoint")
                        
                        instance = GpuInstance(
                            provider=GpuRentalProvider.RUNPOD,
                            instance_id=instance_id,
                            gpu_type=gpu_type,
                            gpu_count=pod_data.get("gpuCount", 1),
                            memory_gb=pod_data.get("memoryInGb", 24),
                            hourly_rate=pod_data.get("pricePerHour", 0.69),
                            status=status,
                            endpoint_url=container_url,
                            container_url=f"https://{container_url}" if container_url else None
                        )
                        
                        self.active_instances[instance_id] = instance
                        return instance
                    elif status in ["FAILED", "TERMINATED"]:
                        raise RuntimeError(f"Instance failed to start: {status}")
                        
            except Exception as e:
                logger.warning(f"Error checking instance status: {e}")
            
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Instance {instance_id} did not start within {timeout} seconds")
    
    async def stop_instance(self, instance_id: str) -> bool:
        """
        Stop and terminate a GPU instance.
        """
        if instance_id not in self.active_instances:
            logger.warning(f"Instance {instance_id} not found in active instances")
            return False
        
        instance = self.active_instances[instance_id]
        
        try:
            if instance.provider == GpuRentalProvider.RUNPOD:
                return await self._stop_runpod_instance(instance_id)
            elif instance.provider == GpuRentalProvider.MODAL:
                return await self._stop_modal_instance(instance_id)
        except Exception as e:
            logger.error(f"Failed to stop instance {instance_id}: {e}")
            return False
        
        return False
    
    async def _stop_runpod_instance(self, instance_id: str) -> bool:
        """
        Stop a RunPod instance.
        """
        try:
            session = await self._get_session()
            async with session.delete(
                f"{self.RUNPOD_API_BASE}/pod/{instance_id}",
                headers=self._get_runpod_headers(),
                timeout=30
            ) as response:
                response.raise_for_status()
                
                del self.active_instances[instance_id]
                logger.info(f"RunPod instance stopped: {instance_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to stop RunPod instance: {e}")
            return False
    
    def _stop_modal_instance(self, instance_id: str) -> bool:
        """
        Stop a Modal instance.
        
        Args:
            instance_id: The ID of the Modal instance to stop.
            
        Returns:
            True if stopped successfully.
        """
        try:
            response = requests.delete(
                f"{self.MODAL_API_BASE}/functions/{instance_id}",
                headers=self._get_modal_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            del self.active_instances[instance_id]
            logger.info(f"Modal instance stopped: {instance_id}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to stop Modal instance: {e}")
            return False
    
    async def submit_job(
        self,
        instance_id: str,
        job_script: str,
        input_data: Dict[str, Any]
    ) -> GpuJob:
        """
        Submit a processing job to a GPU instance.
        """
        if instance_id not in self.active_instances:
            raise ValueError(f"Instance {instance_id} not found")
        
        import uuid
        job_id = str(uuid.uuid4())
        
        job = GpuJob(
            job_id=job_id,
            instance_id=instance_id,
            input_file=json.dumps(input_data),
            output_file=f"/tmp/output_{job_id}.json"
        )
        
        instance = self.active_instances[instance_id]
        
        if instance.provider == GpuRentalProvider.RUNPOD:
            await self._submit_runpod_job(job, job_script, input_data)
        elif instance.provider == GpuRentalProvider.MODAL:
            await self._submit_modal_job(job, job_script, input_data)
        
        logger.info(f"Job {job_id} submitted to instance {instance_id}")
        return job
    
    async def _submit_runpod_job(
        self,
        job: GpuJob,
        job_script: str,
        input_data: Dict[str, Any]
    ) -> None:
        """
        Submit a job to a RunPod instance.
        """
        instance = self.active_instances[job.instance_id]
        
        request_body = {
            "input": {
                "script": job_script,
                "data": input_data
            }
        }
        
        try:
            session = await self._get_session()
            async with session.post(
                f"{self.RUNPOD_API_BASE}/run/{instance.instance_id}",
                headers=self._get_runpod_headers(),
                json=request_body,
                timeout=30
            ) as response:
                response.raise_for_status()
                
                job.status = "running"
                job.started_at = datetime.now()
                
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            logger.error(f"Failed to submit job to RunPod: {e}")
            raise
    
    async def _submit_modal_job(
        self,
        job: GpuJob,
        job_script: str,
        input_data: Dict[str, Any]
    ) -> None:
        """
        Submit a job to a Modal instance.
        """
        instance = self.active_instances[job.instance_id]
        
        request_body = {
            "input": {
                "script": job_script,
                "data": input_data
            }
        }
        
        try:
            session = await self._get_session()
            async with session.post(
                f"{self.MODAL_API_BASE}/functions/{instance.instance_id}/call",
                headers=self._get_modal_headers(),
                json=request_body,
                timeout=30
            ) as response:
                response.raise_for_status()
                
                job.status = "running"
                job.started_at = datetime.now()
                
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            logger.error(f"Failed to submit job to Modal: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[GpuJob]:
        """
        Get the current status of a processing job.
        """
        # Search for job in active instances
        for instance_id, instance in self.active_instances.items():
            try:
                session = await self._get_session()
                if instance.provider == GpuRentalProvider.RUNPOD:
                    url = f"{self.RUNPOD_API_BASE}/status/{instance_id}"
                    headers = self._get_runpod_headers()
                else:
                    url = f"{self.MODAL_API_BASE}/functions/{instance_id}/status"
                    headers = self._get_modal_headers()
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Update job tracking (simplified for this proof of concept)
                        logger.debug(f"Status for job in {instance_id}: {data.get('status')}")
            except Exception as e:
                logger.error(f"Error checking status for instance {instance_id}: {e}")
        
        return self.completed_jobs.get(job_id)
    
    def get_instance_status(self, instance_id: str) -> Optional[GpuInstance]:
        """
        Get the current status of a GPU instance.
        
        Args:
            instance_id: ID of the instance to check.
            
        Returns:
            GpuInstance object if found, None otherwise.
        """
        return self.active_instances.get(instance_id)
    
    def estimate_cost(
        self,
        gpu_type: str,
        duration_hours: float
    ) -> float:
        """
        Estimate the cost for using a GPU for a given duration.
        
        Args:
            gpu_type: Type of GPU to use.
            duration_hours: Expected duration of usage in hours.
            
        Returns:
            Estimated cost in USD.
        """
        if gpu_type not in self.SUPPORTED_GPUS:
            raise ValueError(f"Unsupported GPU type: {gpu_type}")
        
        return self.SUPPORTED_GPUS[gpu_type]["hourly_rate"] * duration_hours
    
    def get_cost_report(self) -> Dict[str, Any]:
        """
        Generate a cost report for the current billing period.
        
        Returns:
            Dictionary containing spending summary and budget information.
        """
        return {
            "current_spend": round(self.current_spend, 2),
            "budget_limit": self.budget_limit,
            "remaining_budget": round(self.budget_limit - self.current_spend, 2),
            "budget_usage_percent": round(
                (self.current_spend / self.budget_limit) * 100, 2
            ) if self.budget_limit > 0 else 0,
            "active_instances": len(self.active_instances),
            "completed_jobs": len(self.completed_jobs),
            "report_generated_at": datetime.now().isoformat()
        }
    
    async def cleanup_all(self) -> int:
        """
        Stop all active GPU instances and cleanup resources.
        """
        stopped_count = 0
        instance_ids = list(self.active_instances.keys())
        
        for instance_id in instance_ids:
            if await self.stop_instance(instance_id):
                stopped_count += 1
        
        await self.close()
        logger.info(f"Cleanup complete. Stopped {stopped_count} instances.")
        return stopped_count
