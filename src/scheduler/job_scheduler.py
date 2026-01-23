"""
Job Scheduler for Elite 8 AI Video Generation System

This module provides comprehensive scheduling capabilities for:
- Video generation jobs
- Social media posting
- Character rotation
- Credit monitoring alerts
"""

import os
import json
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import croniter
import pytz

from .models import (
    DatabaseManager,
    JobStatus,
    PostStatus,
    Platform,
    get_db,
    init_sample_data
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of scheduled tasks"""
    VIDEO_GENERATION = "video_generation"
    SOCIAL_POST = "social_post"
    CREDIT_CHECK = "credit_check"
    METRICS_REPORT = "metrics_report"
    CHARACTER_ROTATION = "character_rotation"


@dataclass
class ScheduledTask:
    """A scheduled task"""
    id: str
    task_type: ScheduleType
    cron_expression: str
    function_name: str
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    timezone: str = "Asia/Tokyo"


@dataclass
class PostingSlot:
    """A scheduled posting slot"""
    time: str  # "08:00"
    platforms: List[str]
    character_ids: List[str]
    daily_order: int
    timezone: str = "Asia/Tokyo"


class JobScheduler:
    """
    Central job scheduler for Elite 8 automation
    
    Handles:
    - Cron-based task scheduling
    - Video generation job queuing
    - Social media posting automation
    - Character rotation management
    - Daily/weekly scheduling patterns
    """
    
    def __init__(self, db: DatabaseManager = None, config_path: str = None):
        """
        Initialize the job scheduler
        
        Args:
            db: Database manager instance
            config_path: Path to scheduler configuration
        """
        self.db = db or get_db()
        self.config_path = config_path
        
        # Load configuration
        self.config = self._load_config()
        
        # Task tracking
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # Scheduler state
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Posting schedule
        self.posting_slots = self._load_posting_slots()
        
        # Initialize default tasks
        self._init_default_tasks()
        
        logger.info("JobScheduler initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load scheduler configuration"""
        if self.config_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            default_config = project_root / "config" / "scheduler_config.json"
            
            self.config_path = os.getenv(
                "SCHEDULER_CONFIG_PATH",
                str(default_config)
            )
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default scheduler configuration"""
        return {
            "enabled": True,
            "check_interval_seconds": 60,
            "posting_slots": {
                "morning": {"time": "08:00", "platforms": ["tiktok", "instagram"]},
                "afternoon": {"time": "12:00", "platforms": ["instagram", "youtube"]},
                "evening": {"time": "18:00", "platforms": ["tiktok", "youtube"]},
                "night": {"time": "21:00", "platforms": ["instagram", "tiktok", "youtube"]}
            },
            "character_rotation": {
                "enabled": True,
                "strategy": "round_robin",
                "characters_per_slot": 2
            },
            "default_timezone": "Asia/Tokyo"
        }
    
    def _load_posting_slots(self) -> List[PostingSlot]:
        """Load posting slots from configuration"""
        slots = []
        config_slots = self.config.get("posting_slots", {})
        
        for i, (name, slot_config) in enumerate(config_slots.items(), 1):
            slot = PostingSlot(
                time=slot_config.get("time", "12:00"),
                platforms=slot_config.get("platforms", ["tiktok"]),
                character_ids=[],  # Will be populated from character rotation
                daily_order=i,
                timezone=self.config.get("default_timezone", "Asia/Tokyo")
            )
            slots.append(slot)
        
        return sorted(slots, key=lambda x: x.time)
    
    def _init_default_tasks(self):
        """Initialize default scheduled tasks"""
        
        # Credit check every hour
        self.add_task(
            task_type=ScheduleType.CREDIT_CHECK,
            cron_expression="0 * * * *",
            function_name="check_credits",
            enabled=True
        )
        
        # Daily metrics report at midnight
        self.add_task(
            task_type=ScheduleType.METRICS_REPORT,
            cron_expression="0 0 * * *",
            function_name="generate_daily_report",
            enabled=True
        )
        
        # Character rotation check every hour
        self.add_task(
            task_type=ScheduleType.CHARACTER_ROTATION,
            cron_expression="0 * * * *",
            function_name="rotate_characters",
            enabled=True
        )
    
    def add_task(
        self,
        task_type: ScheduleType,
        cron_expression: str,
        function_name: str,
        enabled: bool = True,
        parameters: Dict[str, Any] = None,
        timezone: str = "Asia/Tokyo"
    ) -> str:
        """Add a new scheduled task"""
        task_id = str(uuid.uuid4())[:8]
        
        task = ScheduledTask(
            id=task_id,
            task_type=task_type,
            cron_expression=cron_expression,
            function_name=function_name,
            enabled=enabled,
            parameters=parameters or {},
            timezone=timezone
        )
        
        self.tasks[task_id] = task
        
        # Calculate next run time
        task.next_run = self._get_next_run_time(cron_expression, timezone)
        
        logger.info(f"Added task: {task_type.value} ({task_id})")
        return task_id
    
    def _get_next_run_time(
        self,
        cron_expression: str,
        timezone: str = "Asia/Tokyo"
    ) -> Optional[datetime]:
        """Calculate next run time from cron expression"""
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            cron = croniter.croniter(cron_expression, now)
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"Failed to parse cron expression: {e}")
            return None
    
    def register_handler(self, function_name: str, handler: Callable):
        """Register a handler function for a task"""
        self.task_handlers[function_name] = handler
        logger.info(f"Registered handler: {function_name}")
    
    async def start(self):
        """Start the scheduler"""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        logger.info("Scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all running tasks
        for task_id, task in self.running_tasks.items():
            task.cancel()
        
        logger.info("Scheduler stopped")
    
    async def _run_scheduler(self):
        """Main scheduler loop"""
        check_interval = self.config.get("check_interval_seconds", 60)
        
        while self._running:
            try:
                # Check and execute due tasks
                for task_id, task in self.tasks.items():
                    if not task.enabled:
                        continue
                    
                    if task.next_run and datetime.now() >= task.next_run:
                        await self._execute_task(task)
                        
                        # Calculate next run
                        task.next_run = self._get_next_run_time(
                            task.cron_expression,
                            task.timezone
                        )
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(check_interval)
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        task_id = task.id
        
        if task_id in self.running_tasks:
            logger.warning(f"Task {task_id} is already running")
            return
        
        logger.info(f"Executing task: {task.task_type.value}")
        
        # Create task
        handler = self.task_handlers.get(task.function_name)
        
        async def wrapper():
            try:
                if handler:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(**task.parameters)
                    else:
                        handler(**task.parameters)
                else:
                    await self._default_handler(task)
                
                task.last_run = datetime.now()
                logger.info(f"Task {task.task_type.value} completed")
            
            except Exception as e:
                logger.error(f"Task {task.task_type.value} failed: {e}")
            
            finally:
                self.running_tasks.pop(task_id, None)
        
        self.running_tasks[task_id] = asyncio.create_task(wrapper())
    
    async def _default_handler(self, task: ScheduledTask):
        """Default task handler for built-in tasks"""
        if task.task_type == ScheduleType.CREDIT_CHECK:
            await self._check_credits()
        elif task.task_type == ScheduleType.METRICS_REPORT:
            await self._generate_daily_report()
        elif task.task_type == ScheduleType.CHARACTER_ROTATION:
            await self._rotate_characters()
        elif task.task_type == ScheduleType.VIDEO_GENERATION:
            await self._generate_scheduled_videos()
        elif task.task_type == ScheduleType.SOCIAL_POST:
            await self._post_scheduled_content()
    
    # Built-in task handlers
    async def _check_credits(self):
        """Check A2E credits and send alerts"""
        try:
            # Get credit usage from database
            usage = self.db.get_credit_usage(days=30)
            monthly_budget = 3600  # From pro_plan_optimized.json
            
            if usage["total_credits"] >= monthly_budget * 0.8:
                logger.warning(
                    f"Credit alert: {usage['total_credits']}/{monthly_budget} "
                    f"({usage['total_credits']/monthly_budget*100:.1f}%)"
                )
            
            # Store state
            self.db.set_state("last_credit_check", datetime.now().isoformat())
            
        except Exception as e:
            logger.error(f"Credit check failed: {e}")
    
    async def _generate_daily_report(self):
        """Generate daily metrics report"""
        try:
            # Get daily stats
            job_stats = self.db.get_job_stats()
            post_stats = self.db.get_post_stats(days=1)
            credit_usage = self.db.get_credit_usage(days=1)
            
            report = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "jobs": job_stats,
                "posts": post_stats,
                "credits_used_today": credit_usage["credits_30days"],
                "generated_at": datetime.now().isoformat()
            }
            
            # Store report
            self.db.set_state("daily_report", report)
            
            logger.info(f"Daily report generated: {report}")
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
    
    async def _rotate_characters(self):
        """Rotate character usage based on schedule"""
        try:
            characters = self.db.get_all_characters()
            
            if not characters:
                return
            
            # Get current rotation index from state
            rotation_index = self.db.get_state("character_rotation_index", 0)
            
            # Update character rotation
            self.db.set_state("character_rotation_index", (rotation_index + 1) % len(characters))
            
            logger.info(f"Character rotation updated: index {rotation_index}")
            
        except Exception as e:
            logger.error(f"Character rotation failed: {e}")
    
    async def _generate_scheduled_videos(self):
        """Generate videos for scheduled jobs"""
        try:
            pending_jobs = self.db.get_pending_jobs(limit=10)
            
            for job in pending_jobs:
                if job.get("scheduled_time"):
                    scheduled = datetime.fromisoformat(job["scheduled_time"])
                    if datetime.now() >= scheduled:
                        # Trigger video generation
                        logger.info(f"Triggering video generation for job: {job['id']}")
                        # In a real implementation, this would call the A2E client
                        self.db.update_job_status(job["id"], JobStatus.QUEUED)
            
        except Exception as e:
            logger.error(f"Video generation scheduling failed: {e}")
    
    async def _post_scheduled_content(self):
        """Post scheduled content to social media"""
        try:
            scheduled_posts = self.db.get_scheduled_posts()
            
            for post in scheduled_posts:
                if post.get("scheduled_time"):
                    scheduled = datetime.fromisoformat(post["scheduled_time"])
                    if datetime.now() >= scheduled:
                        # Trigger social post
                        logger.info(f"Triggering social post: {post['id']}")
                        # In a real implementation, this would call the social media client
                        
        except Exception as e:
            logger.error(f"Social posting scheduling failed: {e}")
    
    # Public scheduling methods
    async def schedule_video_generation(
        self,
        character_id: str,
        prompt: str,
        scheduled_time: datetime,
        duration_seconds: int = 15,
        platform: str = "tiktok"
    ) -> str:
        """
        Schedule a video generation job
        
        Args:
            character_id: Character to use
            prompt: Generation prompt
            scheduled_time: When to generate
            duration_seconds: Video duration
            platform: Target platform
            
        Returns:
            Job ID
        """
        job_id = self.db.create_job(
            character_id=character_id,
            prompt=prompt,
            duration_seconds=duration_seconds,
            platform=platform,
            scheduled_time=scheduled_time
        )
        
        logger.info(f"Scheduled video generation: {job_id} at {scheduled_time}")
        return job_id
    
    async def schedule_social_post(
        self,
        job_id: str,
        platform: str,
        caption: str,
        tags: List[str],
        scheduled_time: datetime
    ) -> str:
        """
        Schedule a social media post
        
        Args:
            job_id: Associated video job
            platform: Platform to post to
            caption: Post caption
            tags: Hashtags
            scheduled_time: When to post
            
        Returns:
            Post ID
        """
        post_id = self.db.create_post(
            job_id=job_id,
            platform=platform,
            caption=caption,
            tags=tags,
            scheduled_time=scheduled_time
        )
        
        logger.info(f"Scheduled social post: {post_id} at {scheduled_time}")
        return post_id
    
    async def schedule_daily_content(
        self,
        character_ids: List[str],
        platforms: List[str],
        start_date: datetime = None,
        days: int = 7
    ) -> List[str]:
        """
        Schedule daily content for multiple characters and platforms
        
        Args:
            character_ids: Characters to use
            platforms: Platforms to post to
            start_date: Starting date
            days: Number of days to schedule
            
        Returns:
            List of job/post IDs
        """
        if start_date is None:
            start_date = datetime.now()
        
        ids = []
        timezone = pytz.timezone(self.config.get("default_timezone", "Asia/Tokyo"))
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            for slot in self.posting_slots:
                # Parse slot time
                hour, minute = map(int, slot.time.split(":"))
                
                for platform in platforms:
                    if platform not in slot.platforms:
                        continue
                    
                    # Select character for this slot
                    char_index = (day * len(slot.character_ids) + slot.daily_order - 1) % len(character_ids)
                    character_id = character_ids[char_index]
                    
                    # Calculate scheduled time
                    scheduled = current_date.replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )
                    scheduled = timezone.localize(scheduled)
                    
                    if scheduled <= datetime.now(timezone):
                        continue
                    
                    # Generate prompt (simplified)
                    character = self.db.get_character(character_id)
                    prompt = f"Generate engaging content for {character['name']}" if character else "Generate content"
                    
                    # Schedule video generation
                    job_id = await self.schedule_video_generation(
                        character_id=character_id,
                        prompt=prompt,
                        scheduled_time=scheduled,
                        platform=platform
                    )
                    ids.append(job_id)
        
        logger.info(f"Scheduled {len(ids)} content items for {days} days")
        return ids
    
    def get_upcoming_tasks(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get upcoming scheduled tasks"""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        
        tasks = []
        for task_id, task in self.tasks.items():
            if not task.enabled:
                continue
            
            if task.next_run and now <= task.next_run <= cutoff:
                tasks.append({
                    "id": task_id,
                    "type": task.task_type.value,
                    "next_run": task.next_run.isoformat(),
                    "function": task.function_name
                })
        
        return sorted(tasks, key=lambda x: x["next_run"])
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "running": self._running,
            "enabled": self.config.get("enabled", True),
            "tasks_count": len(self.tasks),
            "running_tasks": len(self.running_tasks),
            "posting_slots": len(self.posting_slots),
            "upcoming_tasks": self.get_upcoming_tasks(),
            "next_check": (datetime.now() + timedelta(
                seconds=self.config.get("check_interval_seconds", 60)
            )).isoformat()
        }
    
    async def close(self):
        """Close the scheduler"""
        await self.stop()
        self.db.close()


class ContentScheduler:
    """
    High-level content scheduling with smart features
    
    Features:
    - Optimal posting time calculation
    - Character rotation management
    - Engagement-based scheduling
    """
    
    def __init__(self, scheduler: JobScheduler = None, db: DatabaseManager = None):
        """
        Initialize content scheduler
        
        Args:
            scheduler: Job scheduler instance
            db: Database manager instance
        """
        self.scheduler = scheduler or JobScheduler(db=db)
        self.db = self.scheduler.db
    
    def get_optimal_posting_times(
        self,
        platform: str,
        day_of_week: int = None
    ) -> List[datetime]:
        """
        Get optimal posting times for a platform
        
        Args:
            platform: Target platform
            day_of_week: Day of week (0=Monday)
            
        Returns:
            List of optimal posting times
        """
        timezone = pytz.timezone("Asia/Tokyo")
        now = datetime.now(timezone)
        
        if day_of_week is None:
            day_of_week = now.weekday()
        
        # Platform-specific optimal times
        optimal_times = {
            "tiktok": ["08:00", "12:00", "18:00", "21:00"],
            "instagram": ["08:00", "12:00", "18:00", "21:00"],
            "youtube": ["08:00", "12:00", "18:00", "21:00"]
        }
        
        times = optimal_times.get(platform, ["12:00"])
        result = []
        
        for time_str in times:
            hour, minute = map(int, time_str.split(":"))
            
            posting_time = now.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            
            # If time has passed, schedule for next week
            if posting_time <= now:
                days_ahead = 7 - now.weekday() + day_of_week
                if days_ahead >= 7:
                    days_ahead = day_of_week
                posting_time += timedelta(days=days_ahead)
                posting_time = posting_time.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
            
            result.append(posting_time)
        
        return result
    
    def get_character_for_slot(
        self,
        slot_number: int,
        day_of_week: int = None,
        character_ids: List[str] = None
    ) -> str:
        """
        Get character for a specific posting slot
        
        Args:
            slot_number: Slot number (1-4)
            day_of_week: Day of week
            character_ids: List of character IDs to rotate
            
        Returns:
            Character ID for this slot
        """
        if character_ids is None:
            characters = self.db.get_all_characters()
            character_ids = [c["id"] for c in characters]
        
        if not character_ids:
            return None
        
        if day_of_week is None:
            day_of_week = datetime.now().weekday()
        
        # Rotation algorithm
        index = (slot_number - 1 + day_of_week) % len(character_ids)
        
        return character_ids[index]
    
    async def create_daily_schedule(
        self,
        date: datetime = None,
        character_ids: List[str] = None,
        platforms: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a complete daily posting schedule
        
        Args:
            date: Date to schedule for
            character_ids: Characters to use
            platforms: Platforms to post to
            
        Returns:
            Schedule details
        """
        if date is None:
            date = datetime.now()
        
        if platforms is None:
            platforms = ["tiktok", "instagram", "youtube"]
        
        schedule = {
            "date": date.strftime("%Y-%m-%d"),
            "slots": [],
            "jobs_created": 0,
            "posts_created": 0
        }
        
        for i, slot in enumerate(self.scheduler.posting_slots, 1):
            slot_data = {
                "slot": i,
                "time": slot.time,
                "platforms": slot.platforms,
                "character": None,
                "jobs": []
            }
            
            # Get character for this slot
            character_id = self.get_character_for_slot(
                slot_number=i,
                day_of_week=date.weekday(),
                character_ids=character_ids
            )
            
            if character_id:
                character = self.db.get_character(character_id)
                slot_data["character"] = character
                
                # Schedule for each platform
                for platform in platforms:
                    if platform in slot.platforms:
                        scheduled = self._get_scheduled_time(date, slot.time, platform)
                        
                        # Create video job
                        job_id = await self.scheduler.schedule_video_generation(
                            character_id=character_id,
                            prompt=f"Content for {character['name']} on {platform}",
                            scheduled_time=scheduled,
                            platform=platform
                        )
                        
                        # Create social post
                        post_id = await self.scheduler.schedule_social_post(
                            job_id=job_id,
                            platform=platform,
                            caption=f"Check out this amazing content!",
                            tags=[character["name"].lower().replace(" ", "")],
                            scheduled_time=scheduled
                        )
                        
                        slot_data["jobs"].append({
                            "job_id": job_id,
                            "post_id": post_id,
                            "platform": platform
                        })
                        
                        schedule["jobs_created"] += 1
                        schedule["posts_created"] += 1
            
            schedule["slots"].append(slot_data)
        
        return schedule
    
    def _get_scheduled_time(
        self,
        date: datetime,
        time_str: str,
        platform: str
    ) -> datetime:
        """Get scheduled time for a specific slot and platform"""
        timezone = pytz.timezone("Asia/Tokyo")
        hour, minute = map(int, time_str.split(":"))
        
        scheduled = date.replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        return timezone.localize(scheduled)
    
    async def close(self):
        """Close the content scheduler"""
        await self.scheduler.close()


# Convenience functions
def get_scheduler(db: DatabaseManager = None) -> JobScheduler:
    """Get a scheduler instance"""
    return JobScheduler(db=db)


def get_content_scheduler(scheduler: JobScheduler = None) -> ContentScheduler:
    """Get a content scheduler instance"""
    return ContentScheduler(scheduler=scheduler)


# Export classes and functions
__all__ = [
    "JobScheduler",
    "ContentScheduler",
    "ScheduleType",
    "ScheduledTask",
    "PostingSlot",
    "get_scheduler",
    "get_content_scheduler"
]
