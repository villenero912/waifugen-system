"""
Database Models for Elite 8 AI Video Generation System

This module provides comprehensive database management using PostgreSQL
for tracking jobs, campaigns, users, and system state.
FIX v2: migrado de SQLite a PostgreSQL.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import contextmanager
from enum import Enum
import threading
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Status of a generation job"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PostStatus(Enum):
    """Status of a social media post"""
    SCHEDULED = "scheduled"
    UPLOADING = "uploading"
    PUBLISHED = "published"
    FAILED = "failed"


class Platform(Enum):
    """Supported platforms"""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    LINE = "line"
    NICONICO = "niconico"


@dataclass
class Character:
    """Character configuration for video generation"""
    id: str
    name: str
    trigger_word: str
    model_preferred: str
    resolution: str
    style_tags: List[str]
    priority: int
    reels_per_week: int
    created_at: datetime
    updated_at: datetime


@dataclass
class VideoJob:
    """Video generation job"""
    id: str
    character_id: str
    prompt: str
    duration_seconds: int
    status: JobStatus
    platform: Platform
    scheduled_time: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    output_path: Optional[str]
    error_message: Optional[str]
    credits_used: int
    quality_score: Optional[float]
    created_at: datetime


@dataclass
class SocialPost:
    """Social media post record"""
    id: str
    job_id: str
    platform: Platform
    post_status: PostStatus
    post_id: Optional[str]  # Platform's post ID
    post_url: Optional[str]
    caption: str
    tags: List[str]
    scheduled_time: datetime
    published_at: Optional[datetime]
    views: int
    likes: int
    comments: int
    shares: int
    error_message: Optional[str]
    created_at: datetime


@dataclass
class Campaign:
    """Posting campaign"""
    id: str
    name: str
    character_ids: List[str]
    daily_posts: int
    start_date: datetime
    end_date: Optional[datetime]
    platforms: List[Platform]
    status: str
    created_at: datetime


@dataclass
class CreditTransaction:
    """Credit usage transaction"""
    id: str
    job_id: str
    platform: Platform
    credits_used: int
    cost_usd: float
    transaction_type: str
    created_at: datetime


class DatabaseManager:
    """
    Central database manager for Elite 8 system
    
    Handles all SQLite database operations including:
    - Job tracking and management
    - Character configuration
    - Social post records
    - Campaign management
    - Credit usage tracking
    """
    
    def __init__(self, db_url: str = None):
        """
        Initialize database manager
        
        Args:
            db_url: PostgreSQL connection URL
        """
        if db_url is None:
            db_url = os.getenv(
                "DATABASE_URL",
                "postgresql://waifugen_user:WaifuGen2026Secure@postgres:5432/waifugen_production"
            )
        
        self.db_url = db_url
        
        # Connection pool for thread safety
        self._local = threading.local()
        self._lock = threading.Lock()
        
        # Initialize database
        self._init_database()
        
        logger.info("DatabaseManager initialized with PostgreSQL")
    
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            try:
                self._local.connection = psycopg2.connect(
                    self.db_url,
                    cursor_factory=RealDictCursor,
                    connect_timeout=10
                )
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                raise
        
        return self._local.connection
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
    
    def _init_database(self):
        """Initialize database schema"""
        with self.transaction() as conn:
            with conn.cursor() as cur:
                # Characters table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS characters (
                        id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        trigger_word VARCHAR(255) NOT NULL,
                        model_preferred VARCHAR(255) DEFAULT 'seedance_1.5_pro',
                        resolution VARCHAR(50) DEFAULT '720p',
                        style_tags TEXT,
                        priority INTEGER DEFAULT 5,
                        reels_per_week INTEGER DEFAULT 7,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Video jobs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS video_jobs (
                        id VARCHAR(255) PRIMARY KEY,
                        character_id VARCHAR(255) NOT NULL,
                        prompt TEXT NOT NULL,
                        duration_seconds INTEGER DEFAULT 15,
                        status VARCHAR(50) DEFAULT 'pending',
                        platform VARCHAR(50) DEFAULT 'tiktok',
                        scheduled_time TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        output_path TEXT,
                        error_message TEXT,
                        credits_used INTEGER DEFAULT 0,
                        quality_score NUMERIC,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_character FOREIGN KEY (character_id) REFERENCES characters(id)
                    )
                """)
                
                # Social posts table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS social_posts (
                        id VARCHAR(255) PRIMARY KEY,
                        job_id VARCHAR(255) NOT NULL,
                        platform VARCHAR(50) NOT NULL,
                        post_status VARCHAR(50) DEFAULT 'scheduled',
                        post_id VARCHAR(255),
                        post_url TEXT,
                        caption TEXT,
                        tags TEXT,
                        scheduled_time TIMESTAMP,
                        published_at TIMESTAMP,
                        views INTEGER DEFAULT 0,
                        likes INTEGER DEFAULT 0,
                        comments INTEGER DEFAULT 0,
                        shares INTEGER DEFAULT 0,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_job FOREIGN KEY (job_id) REFERENCES video_jobs(id)
                    )
                """)
                
                # Campaigns table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS campaigns (
                        id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        character_ids TEXT NOT NULL,
                        daily_posts INTEGER DEFAULT 4,
                        start_date TIMESTAMP NOT NULL,
                        end_date TIMESTAMP,
                        platforms TEXT NOT NULL,
                        status VARCHAR(50) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Credit transactions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS credit_transactions (
                        id VARCHAR(255) PRIMARY KEY,
                        job_id VARCHAR(255),
                        platform VARCHAR(50),
                        credits_used INTEGER DEFAULT 0,
                        cost_usd NUMERIC DEFAULT 0.0,
                        transaction_type VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # System state table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS system_state (
                        key VARCHAR(255) PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes (PostgreSQL handles this similarly)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_video_jobs_status ON video_jobs(status)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_video_jobs_scheduled ON video_jobs(scheduled_time)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_social_posts_status ON social_posts(post_status)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_social_posts_platform ON social_posts(platform)")
                
                logger.info("Database schema initialized")
    
    # Character operations
    def add_character(
        self,
        name: str,
        trigger_word: str,
        model_preferred: str = "seedance_1.5_pro",
        resolution: str = "720p",
        style_tags: List[str] = None,
        priority: int = 5,
        reels_per_week: int = 7
    ) -> str:
        """Add a new character"""
        character_id = str(uuid.uuid4())[:8]
        
        with self.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO characters
                    (id, name, trigger_word, model_preferred, resolution, style_tags, priority, reels_per_week)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    character_id,
                    name,
                    trigger_word,
                    model_preferred,
                    resolution,
                    json.dumps(style_tags or []),
                    priority,
                    reels_per_week
                ))
        
        logger.info(f"Added character: {name} ({character_id})")
        return character_id
    
    def get_character(self, character_id: str) -> Optional[Dict]:
        """Get character by ID"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM characters WHERE id = %s",
                (character_id,)
            )
            row = cur.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_all_characters(self) -> List[Dict]:
        """Get all characters"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM characters ORDER BY priority DESC")
            rows = cur.fetchall()
        return [dict(row) for row in rows]
    
    def update_character(self, character_id: str, **kwargs) -> bool:
        """Update character fields"""
        if not kwargs:
            return False
        
        set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
        values = list(kwargs.values()) + [character_id]
        
        with self.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE characters SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    values
                )
        
        return True
    
    # Video job operations
    def create_job(
        self,
        character_id: str,
        prompt: str,
        duration_seconds: int = 15,
        platform: str = "tiktok",
        scheduled_time: datetime = None
    ) -> str:
        """Create a new video generation job"""
        job_id = str(uuid.uuid4())[:12]
        
        with self.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO video_jobs
                    (id, character_id, prompt, duration_seconds, status, platform, scheduled_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    job_id,
                    character_id,
                    prompt,
                    duration_seconds,
                    JobStatus.PENDING.value,
                    platform,
                    scheduled_time.isoformat() if scheduled_time else None
                ))
        
        logger.info(f"Created job: {job_id} for character {character_id}")
        return job_id
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        output_path: str = None,
        error_message: str = None,
        credits_used: int = None,
        quality_score: float = None
    ):
        """Update job status"""
        with self.transaction() as conn:
            with conn.cursor() as cur:
                updates = ["status = %s"]
                params = [status.value]
                
                if status == JobStatus.PROCESSING:
                    updates.append("started_at = %s")
                    params.append(datetime.now())
                elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    updates.append("completed_at = %s")
                    params.append(datetime.now())
                
                if output_path:
                    updates.append("output_path = %s")
                    params.append(output_path)
                
                if error_message:
                    updates.append("error_message = %s")
                    params.append(error_message)
                
                if credits_used is not None:
                    updates.append("credits_used = %s")
                    params.append(credits_used)
                
                if quality_score is not None:
                    updates.append("quality_score = %s")
                    params.append(quality_score)
                
                params.append(job_id)
                
                cur.execute(
                    f"UPDATE video_jobs SET {', '.join(updates)} WHERE id = %s",
                    params
                )
        
        logger.info(f"Updated job {job_id} to {status.value}")
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM video_jobs WHERE id = %s",
                (job_id,)
            )
            row = cur.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_pending_jobs(self, limit: int = 10) -> List[Dict]:
        """Get pending jobs sorted by scheduled time"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM video_jobs
                WHERE status IN ('pending', 'queued')
                ORDER BY scheduled_time ASC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_jobs_by_status(self, status: JobStatus, limit: int = 100) -> List[Dict]:
        """Get jobs by status"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM video_jobs
                WHERE status = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (status.value, limit))
            rows = cur.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job statistics"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            # Total jobs
            cur.execute("SELECT COUNT(*) FROM video_jobs")
            total = cur.fetchone()['count']
            
            # Jobs by status
            status_counts = {}
            for status in JobStatus:
                cur.execute(
                    "SELECT COUNT(*) FROM video_jobs WHERE status = %s",
                    (status.value,)
                )
                count = cur.fetchone()['count']
                status_counts[status.value] = count
            
            # Today's jobs
            today = datetime.now()
            cur.execute("""
                SELECT COUNT(*) FROM video_jobs
                WHERE created_at::date = %s::date
            """, (today,))
            today_count = cur.fetchone()['count']
            
            # Credits used today
            cur.execute("""
                SELECT COALESCE(SUM(credits_used), 0) FROM video_jobs
                WHERE completed_at::date = %s::date AND status = 'completed'
            """, (today,))
            today_credits = cur.fetchone()['coalesce']
            
            return {
                "total_jobs": total,
                "by_status": status_counts,
                "today_jobs": today_count,
                "today_credits_used": float(today_credits)
            }
    
    # Social post operations
    def create_post(
        self,
        job_id: str,
        platform: str,
        caption: str,
        tags: List[str],
        scheduled_time: datetime
    ) -> str:
        """Create a new social post record"""
        post_id = str(uuid.uuid4())[:12]
        
        with self.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO social_posts
                    (id, job_id, platform, caption, tags, scheduled_time, post_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    post_id,
                    job_id,
                    platform,
                    caption,
                    json.dumps(tags),
                    scheduled_time,
                    PostStatus.SCHEDULED.value
                ))
        
        logger.info(f"Created post: {post_id} for {platform}")
        return post_id
    
    def update_post_status(
        self,
        post_id: str,
        post_status: PostStatus,
        post_id_platform: str = None,
        post_url: str = None,
        published_at: datetime = None,
        error_message: str = None,
        engagement: Dict = None
    ):
        """Update post status and engagement metrics"""
        with self.transaction() as conn:
            with conn.cursor() as cur:
                updates = ["post_status = %s"]
                params = [post_status.value]
                
                if post_id_platform:
                    updates.append("post_id = %s")
                    params.append(post_id_platform)
                
                if post_url:
                    updates.append("post_url = %s")
                    params.append(post_url)
                
                if published_at:
                    updates.append("published_at = %s")
                    params.append(published_at)
                
                if error_message:
                    updates.append("error_message = %s")
                    params.append(error_message)
                
                if engagement:
                    updates.append("views = %s")
                    params.append(engagement.get("views", 0))
                    updates.append("likes = %s")
                    params.append(engagement.get("likes", 0))
                    updates.append("comments = %s")
                    params.append(engagement.get("comments", 0))
                    updates.append("shares = %s")
                    params.append(engagement.get("shares", 0))
                
                params.append(post_id)
                
                cur.execute(
                    f"UPDATE social_posts SET {', '.join(updates)} WHERE id = %s",
                    params
                )
    
    def get_post(self, post_id: str) -> Optional[Dict]:
        """Get post by ID"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM social_posts WHERE id = %s",
                (post_id,)
            )
            row = cur.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_scheduled_posts(self, platform: str = None) -> List[Dict]:
        """Get scheduled posts"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            if platform:
                cur.execute("""
                    SELECT * FROM social_posts
                    WHERE post_status = 'scheduled' AND platform = %s
                    ORDER BY scheduled_time ASC
                """, (platform,))
            else:
                cur.execute("""
                    SELECT * FROM social_posts
                    WHERE post_status = 'scheduled'
                    ORDER BY scheduled_time ASC
                """)
            rows = cur.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_post_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get post statistics for recent days"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            start_date = (datetime.now() - timedelta(days=days))
            
            # Total posts
            cur.execute("SELECT COUNT(*) as count FROM social_posts")
            total = cur.fetchone()['count']
            
            # Posts by platform
            platform_counts = {}
            for platform in Platform:
                cur.execute(
                    "SELECT COUNT(*) as count FROM social_posts WHERE platform = %s",
                    (platform.value,)
                )
                count = cur.fetchone()['count']
                platform_counts[platform.value] = count
            
            # Published recently
            cur.execute("""
                SELECT COUNT(*) as count FROM social_posts
                WHERE post_status = 'published' AND published_at >= %s
            """, (start_date,))
            published = cur.fetchone()['count']
            
            # Total engagement
            cur.execute("""
                SELECT
                    COALESCE(SUM(views), 0) as total_views,
                    COALESCE(SUM(likes), 0) as total_likes,
                    COALESCE(SUM(comments), 0) as total_comments,
                    COALESCE(SUM(shares), 0) as total_shares
                FROM social_posts
                WHERE published_at >= %s
            """, (start_date,))
            engagement = cur.fetchone()
            
            return {
                "total_posts": total,
                "by_platform": platform_counts,
                "published_recently": published,
                "engagement_7days": {
                    "views": engagement['total_views'],
                    "likes": engagement['total_likes'],
                    "comments": engagement['total_comments'],
                    "shares": engagement['total_shares']
                }
            }
    
    # Campaign operations
    def create_campaign(
        self,
        name: str,
        character_ids: List[str],
        daily_posts: int = 4,
        start_date: datetime = None,
        platforms: List[str] = None
    ) -> str:
        """Create a new campaign"""
        campaign_id = str(uuid.uuid4())[:12]
        
        with self.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO campaigns
                    (id, name, character_ids, daily_posts, start_date, platforms, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    campaign_id,
                    name,
                    json.dumps(character_ids),
                    daily_posts,
                    (start_date or datetime.now()),
                    json.dumps(platforms or ["tiktok", "instagram", "youtube"]),
                    "active"
                ))
        
        logger.info(f"Created campaign: {name} ({campaign_id})")
        return campaign_id
    
    def get_active_campaigns(self) -> List[Dict]:
        """Get all active campaigns"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM campaigns
                WHERE status = 'active'
                ORDER BY created_at DESC
            """)
            rows = cur.fetchall()
        
        return [dict(row) for row in rows]
    
    # Credit transaction operations
    def log_credit_transaction(
        self,
        job_id: str,
        platform: str,
        credits_used: int,
        cost_usd: float,
        transaction_type: str = "generation"
    ):
        """Log a credit transaction"""
        transaction_id = str(uuid.uuid4())[:12]
        
        with self.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO credit_transactions
                    (id, job_id, platform, credits_used, cost_usd, transaction_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    transaction_id,
                    job_id,
                    platform,
                    credits_used,
                    cost_usd,
                    transaction_type
                ))
    
    def get_credit_usage(self, days: int = 30) -> Dict[str, Any]:
        """Get credit usage statistics"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            start_date = (datetime.now() - timedelta(days=days))
            
            # Total credits
            cur.execute("SELECT COALESCE(SUM(credits_used), 0) as total FROM credit_transactions")
            total = cur.fetchone()['total']
            
            # Credits by platform
            platform_usage = {}
            for platform in Platform:
                cur.execute("""
                    SELECT COALESCE(SUM(credits_used), 0) as usage FROM credit_transactions
                    WHERE platform = %s
                """, (platform.value,))
                credits = cur.fetchone()['usage']
                platform_usage[platform.value] = credits
            
            # Credits recent
            cur.execute("""
                SELECT COALESCE(SUM(credits_used), 0) as recent FROM credit_transactions
                WHERE created_at >= %s
            """, (start_date,))
            recent = cur.fetchone()['recent']
            
            # Cost
            cur.execute("SELECT COALESCE(SUM(cost_usd), 0) as cost FROM credit_transactions")
            total_cost = cur.fetchone()['cost']
            
            return {
                "total_credits": int(total),
                "by_platform": platform_usage,
                "credits_30days": int(recent),
                "total_cost_usd": float(total_cost)
            }
    
    # System state operations
    def set_state(self, key: str, value: Any):
        """Set a system state value"""
        with self.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO system_state (key, value, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    updated_at = CURRENT_TIMESTAMP
                """, (key, json.dumps(value)))
    
    def get_state(self, key: str, default=None) -> Any:
        """Get a system state value"""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT value FROM system_state WHERE key = %s",
                (key,)
            )
            row = cur.fetchone()
        
        if row:
            return json.loads(row[0])
        return default
    
    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
        logger.info("Database connection closed")


# Convenience functions
def get_db(db_path: str = None) -> DatabaseManager:
    """Get a database manager instance"""
    return DatabaseManager(db_path)


def init_sample_data(db: DatabaseManager = None):
    """Initialize sample data for testing"""
    if db is None:
        db = DatabaseManager()
    
    # Add sample characters
    characters = [
        ("Miyuki Sakura", "miyuki_kpop_v1", "seedance_1.5_pro", "720p", ["Kpop", "Dance", "Cute"], 1),
        ("Airi Neo", "airi_cyber_v1", "seedance_1.5_pro", "720p", ["Cyber", "Neon", "Futuristic"], 1),
        ("Hana Nakamura", "hana_soft_v1", "seedance_1.5_pro", "720p", ["Romantic", "Soft", "Emotional"], 1),
        ("Aiko Hayashi", "aiko_pro_v1", "seedance_1.5_pro", "720p", ["Professional", "Career", "Lifestyle"], 1),
        ("Rio Mizuno", "rio_chill_v1", "wan_2.5", "480p", ["Chill", "Relaxed"], 2),
        ("Ren Ohashi", "ren_creative_v1", "wan_2.5", "480p", ["Creative", "Artistic"], 2),
        ("Chiyo Sasaki", "chiyo_fresh_v1", "wan_2.5", "480p", ["Fresh", "Perspective"], 2),
        ("Jin Kawasaki", "jin_bold_v1", "wan_2.5", "480p", ["Bold", "Confident"], 2),
    ]
    
    for char in characters:
        try:
            db.add_character(*char)
        except Exception as e:
            logger.debug(f"Character may already exist: {e}")
    
    # Create sample campaign
    try:
        db.create_campaign(
            name="Daily Elite 8 Content",
            character_ids=["miyuki_sakura", "airi_neo", "hana_nakamura", "aiko_hayashi"],
            daily_posts=4,
            platforms=["tiktok", "instagram", "youtube"]
        )
    except Exception as e:
        logger.debug(f"Campaign may already exist: {e}")
    
    logger.info("Sample data initialized")
    return db


# Export classes and functions
__all__ = [
    "DatabaseManager",
    "JobStatus",
    "PostStatus",
    "Platform",
    "Character",
    "VideoJob",
    "SocialPost",
    "Campaign",
    "CreditTransaction",
    "get_db",
    "init_sample_data"
]
