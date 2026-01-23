"""
Hybrid Video Processing Module

This module provides a hybrid video processing system that intelligently routes
generation requests between the A2E API and GPU rental services based on content
characteristics, cost optimization, and quality requirements.

The hybrid approach provides:
- Intelligent routing between A2E API and GPU rental
- Cost optimization through automatic method selection
- Long-form video processing via segmentation
- Fallback mechanisms for reliability
- Unified interface for both processing methods
"""

import json
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProcessingMethod(Enum):
    """
    Enum representing available video processing methods.
    
    A2E_API: Use the standard A2E API for video generation
    GPU_RENTAL: Use GPU rental services for processing
    AUTO: System automatically selects the best method
    """
    A2E_API = "a2e_api"
    GPU_RENTAL = "gpu_rental"
    AUTO = "auto"


class VideoDurationCategory(Enum):
    """
    Categorization of video duration for processing decisions.
    
    SHORT: Videos under 60 seconds - ideal for A2E API
    MEDIUM: Videos from 1-5 minutes - requires careful method selection
    LONG: Videos over 5 minutes - requires GPU rental or segmentation
    """
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ProcessingPriority(Enum):
    """
    Priority levels for processing requests.
    
    URGENT: Process immediately, cost is secondary concern
    NORMAL: Standard processing with balanced cost/time trade-off
    BUDGET: Minimize cost, time is not critical
    """
    URGENT = "urgent"
    NORMAL = "normal"
    BUDGET = "budget"


@dataclass
class ProcessingRequest:
    """
    Data class representing a video processing request.
    
    Attributes:
        request_id: Unique identifier for the request
        character_id: Character to use for the video
        script: Script content for the video
        duration_seconds: Target duration in seconds
        processing_method: Preferred or automatic processing method
        priority: Processing priority level
        quality_settings: Quality configuration options
        output_format: Desired output format
        metadata: Additional metadata for processing
    """
    request_id: str
    character_id: str
    script: str
    duration_seconds: float
    processing_method: ProcessingMethod = ProcessingMethod.AUTO
    priority: ProcessingPriority = ProcessingPriority.NORMAL
    quality_settings: Dict[str, Any] = field(default_factory=dict)
    output_format: str = "mp4"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """
    Data class representing a processing result.
    
    Attributes:
        request_id: Associated request ID
        success: Whether processing succeeded
        output_path: Path to the generated video file
        processing_method: Method used for processing
        duration_seconds: Actual duration of generated video
        file_size_bytes: Size of the output file
        cost_usd: Cost incurred for processing
        processing_time_seconds: Total processing time
        error_message: Error message if processing failed
        metadata: Additional processing metadata
    """
    request_id: str
    success: bool
    output_path: Optional[str] = None
    processing_method: Optional[ProcessingMethod] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    cost_usd: float = 0.0
    processing_time_seconds: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostEstimate:
    """
    Data class representing a cost estimate for processing.
    
    Attributes:
        method: Processing method for the estimate
        estimated_cost: Estimated cost in USD
        estimated_time: Estimated processing time in seconds
        confidence: Confidence level of the estimate (0-1)
        notes: Additional notes about the estimate
    """
    method: ProcessingMethod
    estimated_cost: float
    estimated_time: float
    confidence: float = 0.9
    notes: str = ""


class HybridVideoProcessor:
    """
    Hybrid video processor that intelligently routes generation requests
    between A2E API and GPU rental services.
    
    This class provides:
    - Intelligent method selection based on content characteristics
    - Cost optimization through automatic routing
    - Long-form video processing via segmentation
    - Unified interface for both processing methods
    - Comprehensive logging and metrics
    - Fallback mechanisms for reliability
    
    Attributes:
        config: Configuration dictionary for the processor
        a2e_client: Client for A2E API interactions
        gpu_manager: Manager for GPU rental services
        metrics: Processing metrics and statistics
    """
    
    # Configuration constants
    MAX_A2E_DURATION_SECONDS = 60  # Maximum duration for A2E API
    SEGMENT_DURATION_SECONDS = 300  # 5 minutes per segment for long videos
    COST_THRESHOLD_LOW = 0.50  # Low cost threshold for budget processing
    COST_THRESHOLD_HIGH = 2.00  # High cost threshold for urgent processing
    
    def __init__(
        self,
        config: Dict[str, Any],
        a2e_client: Optional[Any] = None,
        gpu_manager: Optional[Any] = None
    ):
        """
        Initialize the hybrid video processor.
        
        Args:
            config: Configuration dictionary containing:
                - max_a2e_duration: Maximum duration for A2E API (default: 60s)
                - segment_duration: Duration per segment for long videos (default: 300s)
                - budget_limit: Maximum monthly budget for GPU rental
                - default_quality: Default video quality setting
                - enable_fallback: Enable fallback between methods on failure
                - cache_enabled: Enable caching of processed segments
            a2e_client: Optional A2E API client instance
            gpu_manager: Optional GPU rental manager instance
        """
        self.config = config
        self.a2e_client = a2e_client
        self.gpu_manager = gpu_manager
        
        # Configuration overrides from config dict
        self.max_a2e_duration = config.get("max_a2e_duration", self.MAX_A2E_DURATION_SECONDS)
        self.segment_duration = config.get("segment_duration", self.SEGMENT_DURATION_SECONDS)
        self.budget_limit = config.get("budget_limit", 100.0)
        self.default_quality = config.get("default_quality", "high")
        self.enable_fallback = config.get("enable_fallback", True)
        self.cache_enabled = config.get("cache_enabled", False)
        
        # Initialize metrics tracking
        self.metrics = {
            "total_requests": 0,
            "a2e_requests": 0,
            "gpu_requests": 0,
            "fallback_count": 0,
            "total_cost": 0.0,
            "total_processing_time": 0.0,
            "success_count": 0,
            "failure_count": 0,
            "cost_by_method": {"a2e_api": 0.0, "gpu_rental": 0.0}
        }
        
        # Cache for processed segments
        self.segment_cache: Dict[str, str] = {}
        
        logger.info("Hybrid Video Processor initialized")
        logger.info(f"  Max A2E duration: {self.max_a2e_duration}s")
        logger.info(f"  Segment duration: {self.segment_duration}s")
        logger.info(f"  Fallback enabled: {self.enable_fallback}")
    
    def process_video(self, request: ProcessingRequest) -> ProcessingResult:
        """
        Process a video generation request using the optimal method.
        
        This is the main entry point for video processing. The method analyzes
        the request and selects the best processing approach based on duration,
        cost, priority, and available resources.
        
        Args:
            request: ProcessingRequest containing all necessary information
            
        Returns:
            ProcessingResult with the generated video or error information
        """
        self.metrics["total_requests"] += 1
        start_time = time.time()
        
        request_id = request.request_id
        logger.info(f"Processing request {request_id}")
        logger.info(f"  Duration: {request.duration_seconds}s")
        logger.info(f"  Priority: {request.priority.value}")
        
        # Determine the optimal processing method
        method = self._select_processing_method(request)
        logger.info(f"  Selected method: {method.value}")
        
        # Process based on selected method
        if method == ProcessingMethod.A2E_API:
            return self._process_with_a2e(request, start_time)
        elif method == ProcessingMethod.GPU_RENTAL:
            return self._process_with_gpu(request, start_time)
        else:
            # AUTO mode - try A2E first if suitable
            if request.duration_seconds <= self.max_a2e_duration:
                result = self._process_with_a2e(request, start_time)
                if result.success:
                    return result
                elif self.enable_fallback:
                    logger.warning(f"A2E failed, falling back to GPU rental")
                    self.metrics["fallback_count"] += 1
                    return self._process_with_gpu(request, start_time)
            else:
                return self._process_with_gpu(request, start_time)
    
    def _select_processing_method(self, request: ProcessingRequest) -> ProcessingMethod:
        """
        Select the optimal processing method for a request.
        
        This method analyzes multiple factors to determine the best processing
        approach including duration, priority, cost constraints, and resource
        availability.
        
        Args:
            request: The processing request to analyze
            
        Returns:
            ProcessingMethod enum value indicating the chosen method
        """
        # If user specified a method, respect that choice
        if request.processing_method != ProcessingMethod.AUTO:
            return request.processing_method
        
        # Analyze video duration
        duration_category = self._get_duration_category(request.duration_seconds)
        
        # Decision based on duration and priority
        if request.priority == ProcessingPriority.URGENT:
            # Urgent: prefer A2E for short videos, GPU for long videos
            if duration_category == VideoDurationCategory.SHORT:
                return ProcessingMethod.A2E_API
            else:
                return ProcessingMethod.GPU_RENTAL
        
        elif request.priority == ProcessingPriority.BUDGET:
            # Budget: always prefer the cheaper option
            a2e_estimate = self._estimate_cost(ProcessingMethod.A2E_API, request)
            gpu_estimate = self._estimate_cost(ProcessingMethod.GPU_RENTAL, request)
            
            if a2e_estimate.estimated_cost <= gpu_estimate.estimated_cost:
                return ProcessingMethod.A2E_API
            else:
                return ProcessingMethod.GPU_RENTAL
        
        else:  # NORMAL priority
            # Normal: balance between cost and quality
            if duration_category == VideoDurationCategory.SHORT:
                # Short videos: A2E is usually optimal
                return ProcessingMethod.A2E_API
            elif duration_category == VideoDurationCategory.MEDIUM:
                # Medium videos: consider GPU if budget allows
                if request.metadata.get("use_gpu_for_medium", False):
                    return ProcessingMethod.GPU_RENTAL
                return ProcessingMethod.A2E_API
            else:  # LONG
                # Long videos: require GPU or segmentation
                return ProcessingMethod.GPU_RENTAL
    
    def _get_duration_category(self, duration_seconds: float) -> VideoDurationCategory:
        """
        Categorize video duration for processing decisions.
        
        Args:
            duration_seconds: Duration of the video in seconds
            
        Returns:
            VideoDurationCategory enum value
        """
        if duration_seconds <= 60:
            return VideoDurationCategory.SHORT
        elif duration_seconds <= 300:
            return VideoDurationCategory.MEDIUM
        else:
            return VideoDurationCategory.LONG
    
    def _process_with_a2e(self, request: ProcessingRequest, start_time: float) -> ProcessingResult:
        """
        Process a video request using the A2E API.
        
        This method handles the A2E API processing path, including validation,
        API calls, response handling, and metrics tracking.
        
        Args:
            request: The processing request
            start_time: Timestamp when processing started
            
        Returns:
            ProcessingResult with the outcome
        """
        self.metrics["a2e_requests"] += 1
        request_id = request.request_id
        
        logger.info(f"Processing {request_id} with A2E API")
        
        try:
            # Validate A2E client is available
            if not self.a2e_client:
                raise RuntimeError("A2E client not configured")
            
            # Check if duration is within A2E limits
            if request.duration_seconds > self.max_a2e_duration:
                logger.warning(
                    f"Duration {request.duration_seconds}s exceeds A2E limit "
                    f"{self.max_a2e_duration}s, using GPU rental instead"
                )
                return self._process_with_gpu(request, start_time)
            
            # Call A2E API for video generation
            # The actual implementation depends on the A2E client interface
            result = self.a2e_client.generate_video(
                character_id=request.character_id,
                script=request.script,
                duration=request.duration_seconds,
                quality=request.quality_settings.get("quality", self.default_quality),
                format=request.output_format
            )
            
            # Calculate metrics
            processing_time = time.time() - start_time
            cost = self._calculate_a2e_cost(request.duration_seconds)
            
            # Update metrics
            self.metrics["success_count"] += 1
            self.metrics["total_cost"] += cost
            self.metrics["cost_by_method"]["a2e_api"] += cost
            self.metrics["total_processing_time"] += processing_time
            
            logger.info(f"A2E processing complete for {request_id}")
            logger.info(f"  Cost: ${cost:.4f}, Time: {processing_time:.2f}s")
            
            return ProcessingResult(
                request_id=request_id,
                success=True,
                output_path=result.get("output_path"),
                processing_method=ProcessingMethod.A2E_API,
                duration_seconds=request.duration_seconds,
                cost_usd=cost,
                processing_time_seconds=processing_time,
                metadata=result.get("metadata", {})
            )
            
        except Exception as e:
            error_msg = str(e)
            processing_time = time.time() - start_time
            
            self.metrics["failure_count"] += 1
            self.metrics["total_processing_time"] += processing_time
            
            logger.error(f"A2E processing failed for {request_id}: {error_msg}")
            
            return ProcessingResult(
                request_id=request_id,
                success=False,
                processing_method=ProcessingMethod.A2E_API,
                cost_usd=0.0,
                processing_time_seconds=processing_time,
                error_message=error_msg
            )
    
    def _process_with_gpu(self, request: ProcessingRequest, start_time: float) -> ProcessingResult:
        """
        Process a video request using GPU rental services.
        
        This method handles GPU rental processing, including long-form video
        segmentation, parallel processing of segments, and stitching results.
        
        Args:
            request: The processing request
            start_time: Timestamp when processing started
            
        Returns:
            ProcessingResult with the outcome
        """
        self.metrics["gpu_requests"] += 1
        request_id = request.request_id
        
        logger.info(f"Processing {request_id} with GPU rental")
        
        try:
            # Validate GPU manager is available
            if not self.gpu_manager:
                raise RuntimeError("GPU rental manager not configured")
            
            # Check if segmentation is needed
            if request.duration_seconds > self.segment_duration:
                logger.info(f"Long video detected, will segment into {self.segment_duration}s chunks")
                result = self._process_long_video(request, start_time)
                return result
            else:
                # Process as single segment
                return self._process_gpu_segment(request, start_time)
                
        except Exception as e:
            error_msg = str(e)
            processing_time = time.time() - start_time
            
            self.metrics["failure_count"] += 1
            self.metrics["total_processing_time"] += processing_time
            
            logger.error(f"GPU processing failed for {request_id}: {error_msg}")
            
            # Try fallback to A2E if enabled and method was AUTO
            if self.enable_fallback and request.processing_method == ProcessingMethod.AUTO:
                if request.duration_seconds <= self.max_a2e_duration:
                    logger.info(f"Attempting A2E fallback for {request_id}")
                    self.metrics["fallback_count"] += 1
                    return self._process_with_a2e(request, start_time)
            
            return ProcessingResult(
                request_id=request_id,
                success=False,
                processing_method=ProcessingMethod.GPU_RENTAL,
                cost_usd=0.0,
                processing_time_seconds=processing_time,
                error_message=error_msg
            )
    
    def _process_long_video(
        self,
        request: ProcessingRequest,
        start_time: float
    ) -> ProcessingResult:
        """
        Process a long video by segmenting and processing in chunks.
        
        This method handles the segmentation of long videos, parallel processing
        of segments using GPU resources, and stitching the results into a
        cohesive final video.
        
        Args:
            request: The processing request for the long video
            start_time: Timestamp when processing started
            
        Returns:
            ProcessingResult with the stitched video
        """
        request_id = request.request_id
        duration = request.duration_seconds
        
        # Calculate number of segments
        num_segments = int((duration + self.segment_duration - 1) // self.segment_duration)
        
        logger.info(f"Segmenting video into {num_segments} segments")
        
        # Process each segment
        segment_results = []
        total_cost = 0.0
        
        for segment_idx in range(num_segments):
            segment_start = segment_idx * self.segment_duration
            segment_end = min(segment_start + self.segment_duration, duration)
            segment_duration = segment_end - segment_start
            
            # Check cache if enabled
            cache_key = f"{request.character_id}_{hash(request.script)}"
            if self.cache_enabled and cache_key in self.segment_cache:
                logger.info(f"Using cached segment {segment_idx + 1}/{num_segments}")
                segment_results.append(self.segment_cache[cache_key])
                continue
            
            # Create segment request
            segment_request = ProcessingRequest(
                request_id=f"{request_id}_seg{segment_idx}",
                character_id=request.character_id,
                script=self._extract_segment_script(
                    request.script,
                    segment_start / duration,
                    segment_end / duration
                ),
                duration_seconds=segment_duration,
                processing_method=ProcessingMethod.GPU_RENTAL,
                priority=request.priority,
                quality_settings=request.quality_settings,
                output_format=request.output_format,
                metadata={
                    **request.metadata,
                    "segment_index": segment_idx,
                    "total_segments": num_segments,
                    "segment_start_time": segment_start,
                    "parent_request": request_id
                }
            )
            
            # Process segment
            segment_result = self._process_gpu_segment(segment_request, time.time())
            segment_results.append(segment_result)
            
            if segment_result.success:
                total_cost += segment_result.cost_usd
                # Cache the segment if enabled
                if self.cache_enabled:
                    self.segment_cache[cache_key] = segment_result.output_path
            else:
                logger.error(f"Segment {segment_idx + 1} failed")
                return ProcessingResult(
                    request_id=request_id,
                    success=False,
                    processing_method=ProcessingMethod.GPU_RENTAL,
                    cost_usd=total_cost,
                    processing_time_seconds=time.time() - start_time,
                    error_message=f"Segment {segment_idx + 1} failed: {segment_result.error_message}"
                )
        
        # Stitch segments together
        processing_time = time.time() - start_time
        
        # Update metrics
        self.metrics["success_count"] += 1
        self.metrics["total_cost"] += total_cost
        self.metrics["cost_by_method"]["gpu_rental"] += total_cost
        self.metrics["total_processing_time"] += processing_time
        
        logger.info(f"GPU processing complete for {request_id}")
        logger.info(f"  Segments: {num_segments}, Cost: ${total_cost:.4f}, Time: {processing_time:.2f}s")
        
        # The stitched output path would be created by the actual stitching logic
        output_path = f"/output/{request_id}_stitched.{request.output_format}"
        
        return ProcessingResult(
            request_id=request_id,
            success=True,
            output_path=output_path,
            processing_method=ProcessingMethod.GPU_RENTAL,
            duration_seconds=duration,
            cost_usd=total_cost,
            processing_time_seconds=processing_time,
            metadata={
                "num_segments": num_segments,
                "segment_duration": self.segment_duration,
                "segment_results": [r.output_path for r in segment_results if r.success]
            }
        )
    
    def _process_gpu_segment(
        self,
        request: ProcessingRequest,
        start_time: float
    ) -> ProcessingResult:
        """
        Process a single video segment using GPU rental.
        
        This method handles the actual GPU processing for a video segment,
        including instance management, job submission, and result retrieval.
        
        Args:
            request: The processing request for the segment
            start_time: Timestamp when processing started
            
        Returns:
            ProcessingResult for the segment
        """
        request_id = request.request_id
        
        try:
            # Create or get GPU instance
            gpu_config = self.config.get("gpu_default", {})
            instance = self.gpu_manager.create_instance(
                gpu_type=gpu_config.get("gpu_type", "RTX_4090"),
                container_image=gpu_config.get("container_image", "python:3.11-slim")
            )
            
            # Submit processing job
            job_script = self._generate_processing_script(request)
            job = self.gpu_manager.submit_job(
                instance_id=instance.instance_id,
                job_script=job_script,
                input_data={
                    "character_id": request.character_id,
                    "script": request.script,
                    "duration": request.duration_seconds,
                    "quality": request.quality_settings.get("quality", "high"),
                    "format": request.output_format
                }
            )
            
            # Wait for job completion (simplified - in production, use async polling)
            while job.status not in ["completed", "failed"]:
                time.sleep(10)
                job = self.gpu_manager.get_job_status(job.job_id)
            
            # Calculate cost
            processing_time = time.time() - start_time
            cost = self._calculate_gpu_cost(request.duration_seconds, instance)
            
            if job.status == "completed":
                return ProcessingResult(
                    request_id=request_id,
                    success=True,
                    output_path=job.output_file,
                    processing_method=ProcessingMethod.GPU_RENTAL,
                    duration_seconds=request.duration_seconds,
                    cost_usd=cost,
                    processing_time_seconds=processing_time
                )
            else:
                raise RuntimeError(job.error_message or "GPU job failed")
                
        except Exception as e:
            return ProcessingResult(
                request_id=request_id,
                success=False,
                processing_method=ProcessingMethod.GPU_RENTAL,
                cost_usd=0.0,
                processing_time_seconds=time.time() - start_time,
                error_message=str(e)
            )
    
    def _extract_segment_script(
        self,
        full_script: str,
        start_ratio: float,
        end_ratio: float
    ) -> str:
        """
        Extract a portion of the script for a video segment.
        
        This method handles the logical segmentation of a script based on
        time ratios, ensuring that each segment has coherent content.
        
        Args:
            full_script: The complete script text
            start_ratio: Start position as ratio of total (0-1)
            end_ratio: End position as ratio of total (0-1)
            
        Returns:
            Script text for the segment
        """
        # Simple script segmentation - in production, use more sophisticated NLP
        total_length = len(full_script)
        start_idx = int(total_length * start_ratio)
        end_idx = int(total_length * end_ratio)
        
        return full_script[start_idx:end_idx]
    
    def _generate_processing_script(self, request: ProcessingRequest) -> str:
        """
        Generate the processing script for GPU execution.
        
        This method creates a Python script that will be executed on the
        GPU instance to process the video generation request.
        
        Args:
            request: The processing request
            
        Returns:
            Python script code for GPU execution
        """
        script = f"""
import sys
import json

def process_video():
    input_data = json.loads(sys.stdin.read())
    
    character_id = input_data.get("character_id")
    script = input_data.get("script")
    duration = input_data.get("duration", 60)
    quality = input_data.get("quality", "high")
    format = input_data.get("format", "mp4")
    
    # Video generation logic would go here
    # This is a placeholder for the actual GPU processing
    
    output_path = f"/output/{{character_id}}_{{int(duration)}}s.{{format}}"
    
    result = {{
        "status": "completed",
        "output_path": output_path,
        "duration": duration,
        "quality": quality
    }}
    
    print(json.dumps(result))

if __name__ == "__main__":
    process_video()
"""
        return script
    
    def _estimate_cost(
        self,
        method: ProcessingMethod,
        request: ProcessingRequest
    ) -> CostEstimate:
        """
        Estimate the cost for processing a request with a specific method.
        
        Args:
            method: Processing method to estimate
            request: The processing request
            
        Returns:
            CostEstimate with cost and time projections
        """
        if method == ProcessingMethod.A2E_API:
            cost = self._calculate_a2e_cost(request.duration_seconds)
            time_estimate = request.duration_seconds * 0.5  # Rough time multiplier
            return CostEstimate(
                method=method,
                estimated_cost=cost,
                estimated_time=time_estimate,
                confidence=0.95,
                notes="A2E API cost based on duration"
            )
        else:
            cost = self._calculate_gpu_cost(request.duration_seconds)
            time_estimate = request.duration_seconds * 2.0  # GPU processing overhead
            return CostEstimate(
                method=method,
                estimated_cost=cost,
                estimated_time=time_estimate,
                confidence=0.85,
                notes="GPU rental cost including setup overhead"
            )
    
    def _calculate_a2e_cost(self, duration_seconds: float) -> float:
        """
        Calculate the cost for A2E API processing.
        
        This is a placeholder calculation - actual costs depend on the
        specific A2E API pricing model.
        
        Args:
            duration_seconds: Duration of the video
            
        Returns:
            Cost in USD
        """
        # Example A2E pricing: $0.01 per second
        return duration_seconds * 0.01
    
    def _calculate_gpu_cost(
        self,
        duration_seconds: float,
        instance: Any = None
    ) -> float:
        """
        Calculate the cost for GPU rental processing.
        
        Args:
            duration_seconds: Duration of processing time
            instance: Optional GPU instance for rate calculation
            
        Returns:
            Cost in USD
        """
        # Minimum billing is usually 1 hour for GPU rental
        # Add setup overhead
        setup_overhead = 0.05  # ~3 minutes of setup time
        minimum_billing = 1.0  # hour
        
        processing_hours = (duration_seconds / 3600) + setup_overhead
        processing_hours = max(processing_hours, minimum_billing)
        
        hourly_rate = 0.69  # RTX 4090 default rate
        if instance:
            hourly_rate = instance.hourly_rate
        
        return processing_hours * hourly_rate
    
    def get_cost_estimate(
        self,
        duration_seconds: float,
        priority: ProcessingPriority = ProcessingPriority.NORMAL
    ) -> List[CostEstimate]:
        """
        Get cost estimates for different processing methods.
        
        This method provides a comparison of costs across different processing
        methods to help users make informed decisions.
        
        Args:
            duration_seconds: Target video duration
            priority: Processing priority level
            
        Returns:
            List of CostEstimate objects for comparison
        """
        estimates = []
        
        # Create a dummy request for estimation
        dummy_request = ProcessingRequest(
            request_id="estimate",
            character_id="dummy",
            script="",
            duration_seconds=duration_seconds,
            priority=priority
        )
        
        estimates.append(self._estimate_cost(ProcessingMethod.A2E_API, dummy_request))
        estimates.append(self._estimate_cost(ProcessingMethod.GPU_RENTAL, dummy_request))
        
        return estimates
    
    def get_processing_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive processing metrics and statistics.
        
        Returns:
            Dictionary containing all processing metrics
        """
        total = self.metrics["total_requests"]
        
        return {
            "total_requests": total,
            "a2e_requests": self.metrics["a2e_requests"],
            "gpu_requests": self.metrics["gpu_requests"],
            "fallback_count": self.metrics["fallback_count"],
            "success_rate": (
                self.metrics["success_count"] / total * 100
            ) if total > 0 else 0,
            "total_cost_usd": round(self.metrics["total_cost"], 4),
            "a2e_cost_usd": round(self.metrics["cost_by_method"]["a2e_api"], 4),
            "gpu_cost_usd": round(self.metrics["cost_by_method"]["gpu_rental"], 4),
            "total_processing_time_seconds": round(
                self.metrics["total_processing_time"], 2
            ),
            "average_processing_time_seconds": (
                self.metrics["total_processing_time"] / total
            ) if total > 0 else 0,
            "failures": self.metrics["failure_count"],
            "cache_size": len(self.segment_cache) if self.cache_enabled else 0
        }
    
    def clear_cache(self) -> int:
        """
        Clear the segment cache.
        
        Returns:
            Number of entries removed from the cache
        """
        cache_size = len(self.segment_cache)
        self.segment_cache.clear()
        logger.info(f"Cleared {cache_size} cached segments")
        return cache_size
    
    def cleanup(self) -> None:
        """
        Clean up resources and stop GPU instances.
        
        This method should be called during shutdown to ensure all
        GPU resources are properly released.
        """
        if self.gpu_manager:
            stopped = self.gpu_manager.cleanup_all()
            logger.info(f"Cleaned up {stopped} GPU instances")
        
        self.clear_cache()
        logger.info("Hybrid Video Processor cleanup complete")


class CostOptimizer:
    """
    Utility class for optimizing processing costs across methods.
    
    This class provides methods for analyzing cost patterns, predicting
    optimal method selection, and suggesting cost-saving strategies.
    """
    
    def __init__(self, processor: HybridVideoProcessor):
        """
        Initialize the cost optimizer.
        
        Args:
            processor: HybridVideoProcessor instance to analyze
        """
        self.processor = processor
    
    def get_cost_breakdown(self) -> Dict[str, Any]:
        """
        Get detailed cost breakdown by method and time period.
        
        Returns:
            Dictionary with cost analysis
        """
        metrics = self.processor.get_processing_metrics()
        
        a2e_cost = metrics["a2e_cost_usd"]
        gpu_cost = metrics["gpu_cost_usd"]
        total_cost = metrics["total_cost_usd"]
        
        return {
            "total_cost": total_cost,
            "a2e_cost": a2e_cost,
            "gpu_cost": gpu_cost,
            "cost_distribution": {
                "a2e_api": (a2e_cost / total_cost * 100) if total_cost > 0 else 0,
                "gpu_rental": (gpu_cost / total_cost * 100) if total_cost > 0 else 0
            },
            "cost_per_request": (
                total_cost / metrics["total_requests"]
            ) if metrics["total_requests"] > 0 else 0
        }
    
    def suggest_method(
        self,
        duration_seconds: float,
        budget_limit: Optional[float] = None
    ) -> Tuple[ProcessingMethod, str]:
        """
        Suggest the optimal processing method based on duration and budget.
        
        Args:
            duration_seconds: Target video duration
            budget_limit: Optional budget constraint
            
        Returns:
            Tuple of (recommended method, explanation)
        """
        estimates = self.processor.get_cost_estimate(duration_seconds)
        
        a2e_estimate = estimates[0]
        gpu_estimate = estimates[1]
        
        # Cost-based recommendation
        if a2e_estimate.estimated_cost <= gpu_estimate.estimated_cost:
            if duration_seconds <= self.processor.max_a2e_duration:
                return (
                    ProcessingMethod.A2E_API,
                    f"A2E API is ${a2e_estimate.estimated_cost:.2f} vs GPU ${gpu_estimate.estimated_cost:.2f}"
                )
        
        # Check budget constraint
        if budget_limit:
            if a2e_estimate.estimated_cost <= budget_limit:
                return (
                    ProcessingMethod.A2E_API,
                    f"A2E API fits within ${budget_limit:.2f} budget"
                )
            if gpu_estimate.estimated_cost <= budget_limit:
                return (
                    ProcessingMethod.GPU_RENTAL,
                    f"GPU rental fits within ${budget_limit:.2f} budget"
                )
        
        # Default recommendation
        if duration_seconds <= self.processor.max_a2e_duration:
            return (
                ProcessingMethod.A2E_API,
                "A2E API recommended for short videos"
            )
        else:
            return (
                ProcessingMethod.GPU_RENTAL,
                "GPU rental required for long videos"
            )
