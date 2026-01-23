"""
A2E.ai API Client for Elite 8 AI Video Generation System

This module provides a comprehensive client for interacting with the a2e.ai API,
supporting authentication, video generation, credit management, and robust error handling.
"""

import os
import json
import time
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import hashlib
import hmac
import secrets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class A2EPlanType(Enum):
    """A2E subscription plan types"""
    FREE = "free"
    PRO = "pro"
    MAX = "max"
    ENTERPRISE = "enterprise"


class A2EModelType(Enum):
    """Available A2E model types for video generation"""
    SEEDANCE_1_5_PRO = "seedance_1.5_pro"
    WAN_2_5 = "wan_2.5"
    WAN_2_6 = "wan_2.6"
    SEEDANCE_1_5_PRO_1080P = "seedance_1.5_pro_1080p"
    WAN_2_5_720P = "wan_2.5_720p"
    WAN_2_5_480P = "wan_2.5_480p"


class VideoResolution(Enum):
    """Video resolution options"""
    SD_480P = {"width": 854, "height": 480}
    HD_720P = {"width": 1280, "height": 720}
    FHD_1080P = {"width": 1920, "height": 1080}


class GenerationStatus(Enum):
    """Status of video generation job"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class A2ECredits:
    """Credit information for A2E account"""
    total_credits: int
    used_credits: int
    remaining_credits: int
    plan_type: A2EPlanType
    last_updated: datetime

    @property
    def usage_percentage(self) -> float:
        """Calculate credit usage percentage"""
        if self.total_credits == 0:
            return 100.0
        return (self.used_credits / self.total_credits) * 100


@dataclass
class GenerationConfig:
    """Configuration for video generation"""
    model: A2EModelType
    resolution: VideoResolution
    duration_seconds: int
    prompt: str
    negative_prompt: str = ""
    character_trigger: str = ""
    style: str = ""
    face_consistency_threshold: float = 0.95
    motion_bucket: int = 127
    cfg_scale: float = 1.5
    num_frames: int = 16
    fps: int = 30
    lora_strength: float = 0.8
    avatar_quality: str = "high"
    priority: str = "normal"


@dataclass
class GenerationJob:
    """Video generation job information"""
    job_id: str
    status: GenerationStatus
    config: GenerationConfig
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    credits_used: int = 0
    face_consistency_score: Optional[float] = None
    quality_score: Optional[int] = None


@dataclass
class GenerationResult:
    """Result of a generation operation"""
    success: bool
    job: Optional[GenerationJob] = None
    error: Optional[str] = None
    retry_recommended: bool = False
    fallback_model: Optional[A2EModelType] = None


class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.requests: List[float] = []
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire permission to make a request"""
        async with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            # Remove old requests from tracking
            self.requests = [t for t in self.requests if t > minute_ago]
            
            # Check if we're at the rate limit
            if len(self.requests) >= self.requests_per_minute:
                wait_time = self.requests[0] - minute_ago + 1
                await asyncio.sleep(wait_time)
                return await self.acquire()
            
            # Check burst limit
            recent_requests = [t for t in self.requests if t > now - 10]
            if len(recent_requests) >= self.burst_limit:
                wait_time = 10 - (now - recent_requests[0])
                await asyncio.sleep(max(0, wait_time))
            
            # Record this request
            self.requests.append(now)
            return True


class CreditManager:
    """Manages credit allocation and tracking based on optimization config"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.daily_usage: Dict[str, int] = {}
        self.monthly_usage: Dict[str, int] = {}
        self._initialize_tracking()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the optimization configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file not found"""
        return {
            "target_daily_reels": 4,
            "monthly_credits_available": 3600,
            "credits_per_reel_budget": 30,
            "daily_credit_allocation": {
                "total_available": 60,
                "reels_allocation": 255,
                "buffer_allocation": 15
            }
        }
    
    def _initialize_tracking(self):
        """Initialize daily and monthly usage tracking"""
        today = datetime.now().strftime("%Y-%m-%d")
        month_key = datetime.now().strftime("%Y-%m")
        
        if today not in self.daily_usage:
            self.daily_usage[today] = 0
        if month_key not in self.monthly_usage:
            self.monthly_usage[month_key] = 0
    
    def get_credits_for_model(self, model: A2EModelType, duration: int) -> int:
        """Calculate credits required for a specific model and duration"""
        model_config = self.config.get("model_optimization", {})
        
        model_mapping = {
            A2EModelType.SEEDANCE_1_5_PRO: "primary_model",
            A2EModelType.WAN_2_5: "secondary_model",
            A2EModelType.WAN_2_5_720P: "premium_slots_model",
            A2EModelType.WAN_2_5_480P: "secondary_model",
            A2EModelType.SEEDANCE_1_5_PRO_1080P: "premium_slots_model",
        }
        
        config_key = model_mapping.get(model, "primary_model")
        model_data = model_config.get(config_key, {})
        
        if not model_data:
            return 30  # Default fallback
        
        # Select credit based on duration
        duration_key = f"credits_{duration}s"
        credits = model_data.get(duration_key, model_data.get("credits_15s", 30))
        
        return credits
    
    def check_credit_availability(self, required_credits: int) -> Tuple[bool, int]:
        """Check if enough credits are available"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_allocation = self.config.get("daily_credit_allocation", {}).get("reels_allocation", 255)
        
        current_usage = self.daily_usage.get(today, 0)
        available = daily_allocation - current_usage
        
        if available >= required_credits:
            return True, available
        
        # Check monthly buffer
        month_key = datetime.now().strftime("%Y-%m")
        monthly_used = self.monthly_usage.get(month_key, 0)
        monthly_total = self.config.get("monthly_credits_available", 3600)
        monthly_available = monthly_total - monthly_used
        
        if monthly_available >= required_credits:
            return True, monthly_available
        
        return False, available
    
    def allocate_credits(self, credits_used: int, job_id: str):
        """Record credit allocation for tracking"""
        today = datetime.now().strftime("%Y-%m-%d")
        month_key = datetime.now().strftime("%Y-%m")
        
        if today not in self.daily_usage:
            self.daily_usage[today] = 0
        self.daily_usage[today] += credits_used
        
        if month_key not in self.monthly_usage:
            self.monthly_usage[month_key] = 0
        self.monthly_usage[month_key] += credits_used
        
        logger.info(f"Allocated {credits_used} credits for job {job_id}. Daily: {self.daily_usage[today]}, Monthly: {self.monthly_usage[month_key]}")
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get current usage report"""
        today = datetime.now().strftime("%Y-%m-%d")
        month_key = datetime.now().strftime("%Y-%m")
        
        daily_total = self.config.get("daily_credit_allocation", {}).get("reels_allocation", 255)
        monthly_total = self.config.get("monthly_credits_available", 3600)
        
        return {
            "daily": {
                "used": self.daily_usage.get(today, 0),
                "total": daily_total,
                "percentage": (self.daily_usage.get(today, 0) / daily_total) * 100 if daily_total > 0 else 0
            },
            "monthly": {
                "used": self.monthly_usage.get(month_key, 0),
                "total": monthly_total,
                "percentage": (self.monthly_usage.get(month_key, 0) / monthly_total) * 100 if monthly_total > 0 else 0
            },
            "report_time": datetime.now().isoformat()
        }


class A2EApiError(Exception):
    """Custom exception for A2E API errors"""
    
    def __init__(self, message: str, status_code: int = None, error_code: str = None, retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.retryable = retryable
    
    def __str__(self):
        base = f"A2E API Error: {self.message}"
        if self.status_code:
            base += f" (Status: {self.status_code})"
        if self.error_code:
            base += f" (Code: {self.error_code})"
        return base


class A2EClient:
    """
    Main client for interacting with a2e.ai API
    
    This client provides:
    - Secure authentication with API key
    - Video generation with multiple model options
    - Credit management and tracking
    - Robust error handling with automatic retries
    - Rate limiting to prevent API abuse
    - Integration with optimization configuration
    """
    
    BASE_URL = "https://api.a2e.ai/v1"
    
    # Supported models with their endpoints
    MODEL_ENDPOINTS = {
        A2EModelType.SEEDANCE_1_5_PRO: "/generate/seedance",
        A2EModelType.SEEDANCE_1_5_PRO_1080P: "/generate/seedance-hd",
        A2EModelType.WAN_2_5: "/generate/wan",
        A2EModelType.WAN_2_5_720P: "/generate/wan-hd",
        A2EModelType.WAN_2_5_480P: "/generate/wan-sd",
        A2EModelType.WAN_2_6: "/generate/wan-2.6",
    }
    
    def __init__(self, config_path: str = None):
        """
        Initialize the A2E API client
        
        Args:
            config_path: Path to the optimization configuration file
        """
        # Load API key from environment
        self.api_key = os.getenv("A2E_API_KEY")
        if not self.api_key:
            raise A2EApiError(
                "A2E_API_KEY environment variable not set. "
                "Please set it before using the client.",
                error_code="MISSING_API_KEY"
            )
        
        # Initialize configuration
        if config_path is None:
            default_base = Path(__file__).resolve().parent.parent.parent
            config_path = os.getenv(
                "A2E_CONFIG_PATH",
                str(default_base / "config" / "avatars" / "pro_plan_optimized.json")
            )
        self.config_path = config_path
        
        # Initialize components
        self.credit_manager = CreditManager(config_path)
        self.rate_limiter = RateLimiter(requests_per_minute=60, burst_limit=10)
        
        # Session for HTTP requests
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Job tracking
        self.active_jobs: Dict[str, GenerationJob] = {}
        self.completed_jobs: List[GenerationJob] = []
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.retry_backoff = 2  # exponential backoff multiplier
        
        # Circuit breaker for API failures
        self._circuit_breaker_trips = 0
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_reset_time = 300  # 5 minutes
        self._last_failure_time: Optional[datetime] = None
        
        logger.info("A2E API Client initialized successfully")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=300, connect=30, sock_read=60, sock_connect=30)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self._get_headers()
            )
        return self._session
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate authentication headers"""
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(8)
        
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Client-Version": "2.0.0",
            "X-Platform": "elite-8-system"
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        files: Dict = None
    ) -> Dict[str, Any]:
        """Make an API request with error handling"""
        
        # Check circuit breaker
        if self._is_circuit_broken():
            raise A2EApiError(
                "Circuit breaker is open. API temporarily unavailable.",
                error_code="CIRCUIT_BROKEN",
                retryable=True
            )
        
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        
        logger.debug(f"Making {method} request to {url}")
        
        try:
            if method.upper() == "GET":
                async with session.get(url, params=data) as response:
                    return await self._handle_response(response)
            elif method.upper() == "POST":
                if files:
                    form = aiohttp.FormData()
                    for key, value in files.items():
                        form.add_field(key, value)
                    if data:
                        for key, value in data.items():
                            form.add_field(key, str(value))
                    async with session.post(url, data=form) as response:
                        return await self._handle_response(response)
                else:
                    async with session.post(url, json=data) as response:
                        return await self._handle_response(response)
            elif method.upper() == "DELETE":
                async with session.delete(url, json=data) as response:
                    return await self._handle_response(response)
            else:
                raise A2EApiError(f"Unsupported HTTP method: {method}")
        
        except aiohttp.ClientError as e:
            self._record_failure()
            raise A2EApiError(
                f"Network error: {str(e)}",
                error_code="NETWORK_ERROR",
                retryable=True
            )
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle API response and raise appropriate errors"""
        status = response.status
        try:
            data = await response.json()
        except Exception:
            data = {"message": await response.text()}
        
        if status == 200:
            return data
        elif status == 400:
            raise A2EApiError(
                data.get("message", "Invalid request"),
                status_code=status,
                error_code=data.get("error_code", "INVALID_REQUEST"),
                retryable=False
            )
        elif status == 401:
            raise A2EApiError(
                "Authentication failed. Check your API key.",
                status_code=status,
                error_code="UNAUTHORIZED",
                retryable=False
            )
        elif status == 403:
            raise A2EApiError(
                "Access forbidden. Check your plan permissions.",
                status_code=status,
                error_code="FORBIDDEN",
                retryable=False
            )
        elif status == 429:
            raise A2EApiError(
                "Rate limit exceeded. Please slow down.",
                status_code=status,
                error_code="RATE_LIMITED",
                retryable=True
            )
        elif status >= 500:
            self._record_failure()
            raise A2EApiError(
                data.get("message", "Server error"),
                status_code=status,
                error_code="SERVER_ERROR",
                retryable=True
            )
        else:
            raise A2EApiError(
                data.get("message", f"Unknown error (status {status})"),
                status_code=status,
                error_code=data.get("error_code", "UNKNOWN"),
                retryable=status >= 500
            )
    
    def _is_circuit_broken(self) -> bool:
        """Check if circuit breaker is active"""
        if self._last_failure_time is None:
            return False
        
        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        if elapsed > self._circuit_breaker_reset_time:
            self._circuit_breaker_trips = 0
            self._last_failure_time = None
            return False
        
        return self._circuit_breaker_trips >= self._circuit_breaker_threshold
    
    def _record_failure(self):
        """Record an API failure for circuit breaker"""
        self._circuit_breaker_trips += 1
        self._last_failure_time = datetime.now()
        
        if self._circuit_breaker_trips >= self._circuit_breaker_threshold:
            logger.warning(f"Circuit breaker tripped after {self._circuit_breaker_trips} failures")
    
    def _reset_circuit_breaker(self):
        """Manually reset the circuit breaker"""
        self._circuit_breaker_trips = 0
        self._last_failure_time = None
        logger.info("Circuit breaker reset")
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute a function with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except A2EApiError as e:
                last_exception = e
                if not e.retryable:
                    raise
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (self.retry_backoff ** attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e.message}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed: {e.message}")
                    raise
    
    async def get_credits(self) -> A2ECredits:
        """
        Get current credit balance and usage
        
        Returns:
            A2ECredits object with current credit information
        """
        logger.info("Fetching credit balance")
        
        def _fetch_credits():
            response = self._make_request("GET", "/account/credits")
            return response
        
        data = await self._retry_with_backoff(_fetch_credits)
        
        # Determine plan type
        plan_type = A2EPlanType.PRO  # Default to Pro for this system
        if "plan_type" in data:
            try:
                plan_type = A2EPlanType(data["plan_type"].lower())
            except ValueError:
                logger.warning(f"Unknown plan type: {data['plan_type']}")
        
        return A2ECredits(
            total_credits=data.get("total_credits", 0),
            used_credits=data.get("used_credits", 0),
            remaining_credits=data.get("remaining_credits", 0),
            plan_type=plan_type,
            last_updated=datetime.now()
        )
    
    async def get_credit_usage_history(self, days: int = 30) -> List[Dict]:
        """Get credit usage history for specified days"""
        logger.info(f"Fetching credit usage history for {days} days")
        
        def _fetch_history():
            return self._make_request("GET", "/account/usage", {"days": days})
        
        data = await self._retry_with_backoff(_fetch_history)
        return data.get("usage", [])
    
    async def generate_video(self, config: GenerationConfig) -> GenerationResult:
        """
        Generate a video using the A2E API
        
        Args:
            config: GenerationConfig with all generation parameters
            
        Returns:
            GenerationResult with job information
        """
        logger.info(f"Starting video generation with {config.model.value}")
        
        # Check credit availability
        required_credits = self.credit_manager.get_credits_for_model(
            config.model, config.duration_seconds
        )
        
        available, current_balance = self.credit_manager.check_credit_availability(required_credits)
        if not available:
            return GenerationResult(
                success=False,
                error=f"Insufficient credits. Required: {required_credits}, Available: {current_balance}",
                retry_recommended=False
            )
        
        # Build the generation payload
        payload = self._build_generation_payload(config)
        
        # Make the API call
        def _submit_generation():
            return self._make_request(
                "POST",
                self.MODEL_ENDPOINTS.get(config.model, "/generate/seedance"),
                data=payload
            )
        
        try:
            response = await self._retry_with_backoff(_submit_generation)
            
            # Create job tracking object
            job_id = response.get("job_id", response.get("id", "unknown"))
            
            job = GenerationJob(
                job_id=job_id,
                status=GenerationStatus.QUEUED,
                config=config,
                created_at=datetime.now(),
                credits_used=required_credits
            )
            
            self.active_jobs[job_id] = job
            
            # Allocate credits
            self.credit_manager.allocate_credits(required_credits, job_id)
            
            logger.info(f"Generation job submitted: {job_id}")
            return GenerationResult(success=True, job=job)
            
        except A2EApiError as e:
            # Determine fallback model
            fallback = self._get_fallback_model(config.model)
            
            return GenerationResult(
                success=False,
                error=e.message,
                retry_recommended=e.retryable,
                fallback_model=fallback
            )
    
    def _build_generation_payload(self, config: GenerationConfig) -> Dict[str, Any]:
        """Build the API payload for video generation"""
        resolution = config.resolution.value
        
        payload = {
            "prompt": config.prompt,
            "negative_prompt": config.negative_prompt or "blurry, low quality, distorted face, artifacts, static, unnatural",
            "duration": config.duration_seconds,
            "resolution": {
                "width": resolution["width"],
                "height": resolution["height"]
            },
            "fps": config.fps,
            "num_frames": config.num_frames,
            "cfg_scale": config.cfg_scale,
            "motion_bucket": config.motion_bucket,
            "lora_strength": config.lora_strength,
            "quality": config.avatar_quality,
            "priority": config.priority,
            "face_consistency_threshold": config.face_consistency_threshold
        }
        
        # Add character trigger if specified
        if config.character_trigger:
            payload["character_trigger"] = config.character_trigger
        
        # Add style if specified
        if config.style:
            payload["style_preset"] = config.style
        
        return payload
    
    def _get_fallback_model(self, current_model: A2EModelType) -> Optional[A2EModelType]:
        """Get fallback model for retry"""
        fallback_map = {
            A2EModelType.SEEDANCE_1_5_PRO_1080P: A2EModelType.SEEDANCE_1_5_PRO,
            A2EModelType.SEEDANCE_1_5_PRO: A2EModelType.WAN_2_5_720P,
            A2EModelType.WAN_2_5_720P: A2EModelType.WAN_2_5_480P,
            A2EModelType.WAN_2_5: A2EModelType.WAN_2_5_480P,
            A2EModelType.WAN_2_6: A2EModelType.WAN_2_5,
        }
        return fallback_map.get(current_model)
    
    async def get_job_status(self, job_id: str) -> GenerationJob:
        """
        Get the status of a generation job
        
        Args:
            job_id: The job ID to check
            
        Returns:
            GenerationJob with updated status
        """
        logger.debug(f"Checking status for job {job_id}")
        
        def _check_status():
            return self._make_request("GET", f"/jobs/{job_id}")
        
        data = await self._retry_with_backoff(_check_status)
        
        # Update existing job or create new one
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
        else:
            # Create placeholder job if not tracked
            job = GenerationJob(
                job_id=job_id,
                status=GenerationStatus.QUEUED,
                config=GenerationConfig(
                    model=A2EModelType.SEEDANCE_1_5_PRO,
                    resolution=VideoResolution.HD_720P,
                    duration_seconds=15,
                    prompt=""
                ),
                created_at=datetime.now()
            )
        
        # Update job status
        status_map = {
            "queued": GenerationStatus.QUEUED,
            "processing": GenerationStatus.PROCESSING,
            "completed": GenerationStatus.COMPLETED,
            "failed": GenerationStatus.FAILED,
            "cancelled": GenerationStatus.CANCELLED
        }
        
        api_status = data.get("status", "queued")
        job.status = status_map.get(api_status, GenerationStatus.QUEUED)
        job.progress = data.get("progress", 0)
        
        if job.status == GenerationStatus.COMPLETED:
            job.completed_at = datetime.now()
            job.output_url = data.get("output_url", data.get("video_url"))
            job.face_consistency_score = data.get("face_consistency_score")
            job.quality_score = data.get("quality_score")
            
            # Move to completed
            self.active_jobs.pop(job_id, None)
            self.completed_jobs.append(job)
            
            logger.info(f"Job {job_id} completed with quality score: {job.quality_score}")
        
        elif job.status == GenerationStatus.FAILED:
            job.completed_at = datetime.now()
            job.error_message = data.get("error_message", data.get("error", "Unknown error"))
            
            # Move to completed
            self.active_jobs.pop(job_id, None)
            self.completed_jobs.append(job)
            
            logger.error(f"Job {job_id} failed: {job.error_message}")
        
        elif job.status == GenerationStatus.PROCESSING:
            job.started_at = job.started_at or datetime.now()
        
        return job
    
    async def wait_for_completion(
        self,
        job_id: str,
        poll_interval: int = 10,
        max_wait: int = 600
    ) -> GenerationJob:
        """
        Wait for a generation job to complete
        
        Args:
            job_id: The job ID to wait for
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait
            
        Returns:
            Completed GenerationJob
        """
        logger.info(f"Waiting for job {job_id} to complete")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            job = await self.get_job_status(job_id)
            
            if job.status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED, GenerationStatus.CANCELLED]:
                return job
            
            logger.debug(f"Job {job_id}: {job.status.value} ({job.progress}%)")
            await asyncio.sleep(poll_interval)
        
        raise A2EApiError(
            f"Job {job_id} did not complete within {max_wait} seconds",
            error_code="TIMEOUT",
            retryable=False
        )
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running generation job
        
        Args:
            job_id: The job ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        logger.info(f"Cancelling job {job_id}")
        
        def _cancel():
            return self._make_request("DELETE", f"/jobs/{job_id}")
        
        try:
            await self._retry_with_backoff(_cancel)
            
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = GenerationStatus.CANCELLED
            
            logger.info(f"Job {job_id} cancelled")
            return True
            
        except A2EApiError as e:
            logger.error(f"Failed to cancel job {job_id}: {e.message}")
            return False
    
    async def list_jobs(
        self,
        status: GenerationStatus = None,
        limit: int = 50
    ) -> List[GenerationJob]:
        """
        List generation jobs
        
        Args:
            status: Filter by status (optional)
            limit: Maximum jobs to return
            
        Returns:
            List of GenerationJob objects
        """
        logger.info("Listing generation jobs")
        
        params = {"limit": limit}
        if status:
            params["status"] = status.value
        
        def _list_jobs():
            return self._make_request("GET", "/jobs", params)
        
        data = await self._retry_with_backoff(_list_jobs)
        
        jobs = []
        for job_data in data.get("jobs", []):
            job = self._job_data_to_job(job_data)
            if status is None or job.status == status:
                jobs.append(job)
                if len(jobs) >= limit:
                    break
        
        return jobs
    
    def _job_data_to_job(self, data: Dict) -> GenerationJob:
        """Convert API job data to GenerationJob object"""
        status_map = {
            "queued": GenerationStatus.QUEUED,
            "processing": GenerationStatus.PROCESSING,
            "completed": GenerationStatus.COMPLETED,
            "failed": GenerationStatus.FAILED,
            "cancelled": GenerationStatus.CANCELLED
        }
        
        # Parse dates
        created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])
        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])
        
        return GenerationJob(
            job_id=data.get("job_id", data.get("id", "unknown")),
            status=status_map.get(data.get("status", "queued"), GenerationStatus.QUEUED),
            config=GenerationConfig(
                model=A2EModelType(data.get("model", "seedance_1.5_pro")),
                resolution=VideoResolution.HD_720P,
                duration_seconds=data.get("duration", 15),
                prompt=data.get("prompt", "")
            ),
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            progress=data.get("progress", 0),
            output_url=data.get("output_url"),
            error_message=data.get("error_message"),
            credits_used=data.get("credits_used", 0)
        )
    
    async def get_available_models(self) -> List[Dict]:
        """Get list of available models and their capabilities"""
        logger.info("Fetching available models")
        
        def _get_models():
            return self._make_request("GET", "/models")
        
        data = await self._retry_with_backoff(_get_models)
        return data.get("models", [])
    
    async def estimate_cost(self, config: GenerationConfig) -> Dict[str, Any]:
        """Estimate the cost for a generation"""
        credits = self.credit_manager.get_credits_for_model(
            config.model, config.duration_seconds
        )
        
        # Convert credits to USD (based on Pro plan: 1800 credits = $9.90)
        cost_per_credit = 9.90 / 1800
        estimated_cost = credits * cost_per_credit
        
        return {
            "credits_required": credits,
            "estimated_cost_usd": round(estimated_cost, 2),
            "model": config.model.value,
            "duration_seconds": config.duration_seconds,
            "resolution": config.resolution.value
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check API health and client status
        
        Returns:
            Health status dictionary
        """
        health = {
            "status": "unknown",
            "api_reachable": False,
            "credits_available": False,
            "circuit_breaker": "closed",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check API reachability
            def _ping():
                return self._make_request("GET", "/health")
            
            await self._retry_with_backoff(_ping)
            health["api_reachable"] = True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
        
        try:
            # Check credits
            credits = await self.get_credits()
            health["credits_available"] = credits.remaining_credits > 0
            health["credit_balance"] = {
                "total": credits.total_credits,
                "remaining": credits.remaining_credits,
                "usage_percentage": credits.usage_percentage
            }
        except Exception as e:
            logger.warning(f"Credit check failed: {e}")
        
        # Circuit breaker status
        health["circuit_breaker"] = "open" if self._is_circuit_broken() else "closed"
        
        # Overall status
        if health["api_reachable"] and health["credits_available"]:
            health["status"] = "healthy"
        elif health["api_reachable"]:
            health["status"] = "degraded"
        else:
            health["status"] = "unhealthy"
        
        return health
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.info("A2E API Client session closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        asyncio.get_event_loop().run_until_complete(self.close())
        return False
    
    def __del__(self):
        """Destructor"""
        if hasattr(self, '_session') and self._session and not self._session.closed:
            asyncio.get_event_loop().run_until_complete(self.close())


# Convenience functions for common operations

async def quick_generate(
    prompt: str,
    duration: int = 15,
    model: A2EModelType = A2EModelType.SEEDANCE_1_5_PRO
) -> GenerationResult:
    """
    Quick video generation with default settings
    
    Args:
        prompt: The generation prompt
        duration: Video duration in seconds
        model: Model to use
        
    Returns:
        GenerationResult
    """
    config_path = os.getenv(
        "A2E_CONFIG_PATH",
        "/workspace/waifugen_system/config/avatars/pro_plan_optimized.json"
    )
    
    async with A2EClient(config_path=config_path) as client:
        resolution = VideoResolution.HD_720P
        if model == A2EModelType.WAN_2_5_480P:
            resolution = VideoResolution.SD_480P
        elif model == A2EModelType.SEEDANCE_1_5_PRO_1080P:
            resolution = VideoResolution.FHD_1080P
        
        gen_config = GenerationConfig(
            model=model,
            resolution=resolution,
            duration_seconds=duration,
            prompt=prompt
        )
        
        result = await client.generate_video(gen_config)
        
        if result.success and result.job:
            final_job = await client.wait_for_completion(result.job.job_id)
            return GenerationResult(success=final_job.status == GenerationStatus.COMPLETED, job=final_job)
        
        return result


async def check_balance() -> Dict[str, Any]:
    """Quick check of credit balance"""
    config_path = os.getenv(
        "A2E_CONFIG_PATH",
        "/workspace/waifugen_system/config/avatars/pro_plan_optimized.json"
    )
    
    async with A2EClient(config_path=config_path) as client:
        credits = await client.get_credits()
        usage = client.credit_manager.get_usage_report()
        
        return {
            "plan": credits.plan_type.value,
            "total_credits": credits.total_credits,
            "remaining_credits": credits.remaining_credits,
            "usage_percentage": round(credits.usage_percentage, 2),
            "daily_usage": usage["daily"],
            "monthly_usage": usage["monthly"]
        }


# Export main classes and functions
__all__ = [
    "A2EClient",
    "A2ECredits",
    "GenerationConfig",
    "GenerationJob",
    "GenerationResult",
    "GenerationStatus",
    "A2EApiError",
    "A2EModelType",
    "VideoResolution",
    "CreditManager",
    "RateLimiter",
    "quick_generate",
    "check_balance"
]
