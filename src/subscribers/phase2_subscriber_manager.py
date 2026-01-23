"""
Phase 2 Subscriber Management Module

This module provides comprehensive subscriber management capabilities for Phase 2 platforms
including OnlyFans, XVideos, Pornhub, and Japanese platforms (FC2, Fantia, Line).

Last Updated: 2026-01-19
Migrated: 2026-01-22
"""

import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager


class SubscriptionTier(Enum):
    """Subscription tier definitions"""
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"


class SubscriptionStatus(Enum):
    """Subscription status definitions"""
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    CHURNED = "churned"
    PENDING = "pending"


class Platform(Enum):
    """Supported Phase 2 platforms"""
    ONLYFANS = "onlyfans"
    XVIDEOS = "xvideos"
    PORNHUB = "pornhub"
    FANMART = "fanmart"
    FC2 = "fc2"
    FANTIA = "fantia"
    LINE = "line"


@dataclass
class Subscriber:
    """Subscriber data model"""
    subscriber_id: str
    platform: str
    platform_user_id: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    tier: str = "basic"
    subscription_status: str = "active"
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    monthly_rate: Decimal = Decimal("0.00")
    lifetime_value: Decimal = Decimal("0.00")
    total_spent: Decimal = Decimal("0.00")
    source_platform: Optional[str] = None
    referral_code: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_activity_at: Optional[datetime] = None
    churned_at: Optional[datetime] = None


@dataclass
class TierHistory:
    """Tier change history record"""
    id: int
    subscriber_id: str
    from_tier: Optional[str]
    to_tier: str
    reason: Optional[str]
    is_upgrade: bool
    effective_date: datetime
    price_change: Optional[Decimal]
    metadata: Dict
    created_at: datetime


@dataclass
class EngagementMetrics:
    """Daily engagement metrics for a subscriber"""
    id: int
    subscriber_id: str
    platform: str
    engagement_date: datetime
    messages_sent: int = 0
    messages_received: int = 0
    content_views: int = 0
    content_completions: int = 0
    likes_given: int = 0
    comments_made: int = 0
    shares: int = 0
    time_spent_minutes: int = 0
    dm_conversations: int = 0
    engagement_score: Decimal = Decimal("0.0000")
    active_session_count: int = 1
    last_activity: Optional[datetime] = None
    metadata: Dict


@dataclass
class WinbackCampaign:
    """Winback campaign record for churned subscribers"""
    id: int
    campaign_id: str
    subscriber_id: str
    campaign_type: str
    days_since_churn: int
    offer_type: Optional[str]
    discount_percent: Optional[int]
    offer_start_date: Optional[datetime]
    offer_end_date: Optional[datetime]
    offer_claimed: bool = False
    claimed_at: Optional[datetime] = None
    reactivated: bool = False
    reactivated_at: Optional[datetime] = None
    reactivation_value: Decimal = Decimal("0.00")
    status: str = "pending"
    attempts_count: int = 0
    last_attempt_at: Optional[datetime] = None
    metadata: Dict
    created_at: datetime


class DatabaseConnection:
    """Database connection manager for PostgreSQL"""
    
    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize database connection manager
        
        Args:
            db_config: Dictionary containing database configuration
                - host: Database host
                - port: Database port
                - database: Database name
                - user: Database user
                - password: Database password
        """
        self.db_config = db_config
        self._connection = None
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        try:
            conn = psycopg2.connect(
                host=self.db_config.get("host", os.getenv("DB_HOST", "localhost")),
                port=self.db_config.get("port", os.getenv("DB_PORT", 5432)),
                database=self.db_config.get("database", os.getenv("DB_NAME", "jav_automation")),
                user=self.db_config.get("user", os.getenv("DB_USER", "postgres")),
                password=self.db_config.get("password", os.getenv("DB_PASSWORD", "postgres")),
                connect_timeout=10
            )
            yield conn
        except psycopg2.Error as e:
            # We don't have a logger initialized in this class scope, so we just raise
            # or we could use print, but raising is cleaner for a manager.
            raise e
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, commit: bool = True):
        """Context manager for database cursors"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()


class SubscriberManager:
    """
    Comprehensive subscriber management class for Phase 2 platforms.
    
    Handles all subscriber-related operations including:
    - CRUD operations for subscribers
    - Tier management and upgrades/downgrades
    - Engagement tracking
    - Winback campaign management
    - Lifetime value calculations
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize subscriber manager
        
        Args:
            db_connection: DatabaseConnection instance
        """
        self.db = db_connection
    
    def create_subscriber(
        self,
        platform: str,
        username: str,
        tier: str = "basic",
        monthly_rate: Decimal = Decimal("0.00"),
        source_platform: Optional[str] = None,
        referral_code: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Subscriber:
        """
        Create a new subscriber
        
        Args:
            platform: Platform name
            username: Subscriber username
            tier: Subscription tier
            monthly_rate: Monthly subscription rate
            source_platform: Where subscriber came from
            referral_code: Referral code used
            metadata: Additional metadata
            
        Returns:
            Created Subscriber object
        """
        subscriber_id = f"sub_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO phase2_subscribers (
                    subscriber_id, platform, username, tier, monthly_rate,
                    source_platform, referral_code, metadata,
                    subscription_status, subscription_start_date, next_billing_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING *
            """, (
                subscriber_id, platform, username, tier, monthly_rate,
                source_platform, referral_code, json.dumps(metadata or {}),
                "active", now, now + timedelta(days=30)
            ))
            
            row = cursor.fetchone()
            return self._row_to_subscriber(row)
    
    def get_subscriber(self, subscriber_id: str) -> Optional[Subscriber]:
        """
        Get subscriber by ID
        
        Args:
            subscriber_id: Subscriber ID
            
        Returns:
            Subscriber object or None
        """
        with self.db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM phase2_subscribers WHERE subscriber_id = %s
            """, (subscriber_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_subscriber(row)
            return None
    
    def get_subscriber_by_platform(
        self,
        platform: str,
        platform_user_id: str
    ) -> Optional[Subscriber]:
        """
        Get subscriber by platform and platform user ID
        
        Args:
            platform: Platform name
            platform_user_id: User ID on the platform
            
        Returns:
            Subscriber object or None
        """
        with self.db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM phase2_subscribers
                WHERE platform = %s AND platform_user_id = %s
            """, (platform, platform_user_id))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_subscriber(row)
            return None
    
    def update_subscriber(
        self,
        subscriber_id: str,
        **kwargs
    ) -> Optional[Subscriber]:
        """
        Update subscriber fields
        
        Args:
            subscriber_id: Subscriber ID
            **kwargs: Fields to update
            
        Returns:
            Updated Subscriber object or None
        """
        allowed_fields = {
            "display_name", "email", "tier", "subscription_status",
            "subscription_end_date", "next_billing_date", "monthly_rate",
            "source_platform", "referral_code", "metadata"
        }
        
        updates = {}
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == "metadata":
                    updates[key] = json.dumps(value)
                else:
                    updates[key] = value
        
        if not updates:
            return self.get_subscriber(subscriber_id)
        
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [subscriber_id]
        
        with self.db.get_cursor() as cursor:
            cursor.execute(f"""
                UPDATE phase2_subscribers SET {set_clause}
                WHERE subscriber_id = %s RETURNING *
            """, values)
            
            row = cursor.fetchone()
            if row:
                return self._row_to_subscriber(row)
            return None
    
    def upgrade_tier(
        self,
        subscriber_id: str,
        new_tier: str,
        reason: str = "Upgrade",
        metadata: Optional[Dict] = None
    ) -> Tuple[Subscriber, TierHistory]:
        """
        Upgrade subscriber to a higher tier
        
        Args:
            subscriber_id: Subscriber ID
            new_tier: New subscription tier
            reason: Reason for upgrade
            metadata: Additional metadata
            
        Returns:
            Tuple of (updated Subscriber, TierHistory record)
        """
        subscriber = self.get_subscriber(subscriber_id)
        if not subscriber:
            raise ValueError(f"Subscriber {subscriber_id} not found")
        
        old_tier = subscriber.tier
        tier_prices = {
            "basic": Decimal("9.99"),
            "premium": Decimal("19.99"),
            "vip": Decimal("49.99")
        }
        
        old_price = tier_prices.get(old_tier, Decimal("0.00"))
        new_price = tier_prices.get(new_tier, Decimal("0.00"))
        price_change = new_price - old_price
        
        now = datetime.utcnow()
        is_upgrade = new_price > old_price
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE phase2_subscribers
                SET tier = %s, monthly_rate = %s, updated_at = %s
                WHERE subscriber_id = %s RETURNING *
            """, (new_tier, new_price, now, subscriber_id))
            
            updated_subscriber = self._row_to_subscriber(cursor.fetchone())
            
            history_id = str(uuid.uuid4().hex[:12])
            cursor.execute("""
                INSERT INTO subscription_tier_history (
                    id, subscriber_id, from_tier, to_tier, reason,
                    is_upgrade, effective_date, price_change, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *
            """, (
                history_id, subscriber_id, old_tier, new_tier, reason,
                is_upgrade, now, price_change, json.dumps(metadata or {})
            ))
            
            history = TierHistory(
                id=history_id,
                subscriber_id=subscriber_id,
                from_tier=old_tier,
                to_tier=new_tier,
                reason=reason,
                is_upgrade=is_upgrade,
                effective_date=now,
                price_change=price_change,
                metadata=metadata or {},
                created_at=now
            )
            
            return updated_subscriber, history
    
    def record_engagement(
        self,
        subscriber_id: str,
        platform: str,
        engagement_date: datetime,
        messages_sent: int = 0,
        messages_received: int = 0,
        content_views: int = 0,
        content_completions: int = 0,
        likes_given: int = 0,
        comments_made: int = 0,
        shares: int = 0,
        time_spent_minutes: int = 0,
        dm_conversations: int = 0,
        metadata: Optional[Dict] = None
    ) -> EngagementMetrics:
        """
        Record daily engagement metrics for a subscriber
        
        Args:
            subscriber_id: Subscriber ID
            platform: Platform name
            engagement_date: Date of engagement
            messages_sent: Number of messages sent
            messages_received: Number of messages received
            content_views: Number of content views
            content_completions: Number of content completions
            likes_given: Number of likes given
            comments_made: Number of comments made
            shares: Number of shares
            time_spent_minutes: Time spent in minutes
            dm_conversations: Number of DM conversations
            metadata: Additional metadata
            
        Returns:
            EngagementMetrics object
        """
        engagement_score = self._calculate_engagement_score(
            messages_sent, messages_received, content_views,
            content_completions, likes_given, comments_made,
            shares, time_spent_minutes, dm_conversations
        )
        
        metrics_id = str(uuid.uuid4().hex[:12])
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO subscriber_engagement (
                    id, subscriber_id, platform, engagement_date,
                    messages_sent, messages_received, content_views,
                    content_completions, likes_given, comments_made,
                    shares, time_spent_minutes, dm_conversations,
                    engagement_score, metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (subscriber_id, platform, engagement_date)
                DO UPDATE SET
                    messages_sent = EXCLUDED.messages_sent,
                    messages_received = EXCLUDED.messages_received,
                    content_views = EXCLUDED.content_views,
                    content_completions = EXCLUDED.content_completions,
                    likes_given = EXCLUDED.likes_given,
                    comments_made = EXCLUDED.comments_made,
                    shares = EXCLUDED.shares,
                    time_spent_minutes = EXCLUDED.time_spent_minutes,
                    dm_conversations = EXCLUDED.dm_conversations,
                    engagement_score = EXCLUDED.engagement_score,
                    metadata = EXCLUDED.metadata
                RETURNING *
            """, (
                metrics_id, subscriber_id, platform, engagement_date.date(),
                messages_sent, messages_received, content_views,
                content_completions, likes_given, comments_made,
                shares, time_spent_minutes, dm_conversations,
                engagement_score, json.dumps(metadata or {})
            ))
            
            row = cursor.fetchone()
            return EngagementMetrics(
                id=row["id"],
                subscriber_id=row["subscriber_id"],
                platform=row["platform"],
                engagement_date=row["engagement_date"],
                messages_sent=row["messages_sent"],
                messages_received=row["messages_received"],
                content_views=row["content_views"],
                content_completions=row["content_completions"],
                likes_given=row["likes_given"],
                comments_made=row["comments_made"],
                shares=row["shares"],
                time_spent_minutes=row["time_spent_minutes"],
                dm_conversations=row["dm_conversations"],
                engagement_score=row["engagement_score"],
                active_session_count=row["active_session_count"],
                last_activity=row["last_activity"],
                metadata=row["metadata"] if isinstance(row["metadata"], dict) else {}
            )
    
    def get_high_value_subscribers(
        self,
        platform: Optional[str] = None,
        min_ltv: Decimal = Decimal("100.00"),
        limit: int = 100
    ) -> List[Subscriber]:
        """
        Get high-value subscribers based on lifetime value
        
        Args:
            platform: Optional platform filter
            min_ltv: Minimum lifetime value
            limit: Maximum number of subscribers to return
            
        Returns:
            List of Subscriber objects
        """
        with self.db.get_cursor(commit=False) as cursor:
            if platform:
                cursor.execute("""
                    SELECT * FROM phase2_subscribers
                    WHERE platform = %s AND lifetime_value >= %s
                    AND subscription_status = 'active'
                    ORDER BY lifetime_value DESC LIMIT %s
                """, (platform, min_ltv, limit))
            else:
                cursor.execute("""
                    SELECT * FROM phase2_subscribers
                    WHERE lifetime_value >= %s AND subscription_status = 'active'
                    ORDER BY lifetime_value DESC LIMIT %s
                """, (min_ltv, limit))
            
            return [self._row_to_subscriber(row) for row in cursor.fetchall()]
    
    def get_at_risk_subscribers(
        self,
        platform: Optional[str] = None,
        engagement_threshold: Decimal = Decimal("0.1"),
        days_inactive: int = 14
    ) -> List[Subscriber]:
        """
        Get subscribers at risk of churning
        
        Args:
            platform: Optional platform filter
            engagement_threshold: Low engagement score threshold
            days_inactive: Days since last activity
            
        Returns:
            List of Subscriber objects at risk
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
        
        with self.db.get_cursor(commit=False) as cursor:
            if platform:
                cursor.execute("""
                    SELECT DISTINCT s.* FROM phase2_subscribers s
                    LEFT JOIN subscriber_engagement e ON s.subscriber_id = e.subscriber_id
                    WHERE s.platform = %s AND s.subscription_status = 'active'
                    AND (s.last_activity_at IS NULL OR s.last_activity_at < %s)
                    AND (e.engagement_score IS NULL OR e.engagement_score < %s)
                    ORDER BY s.lifetime_value DESC
                """, (platform, cutoff_date, engagement_threshold))
            else:
                cursor.execute("""
                    SELECT DISTINCT s.* FROM phase2_subscribers s
                    LEFT JOIN subscriber_engagement e ON s.subscriber_id = e.subscriber_id
                    WHERE s.subscription_status = 'active'
                    AND (s.last_activity_at IS NULL OR s.last_activity_at < %s)
                    AND (e.engagement_score IS NULL OR e.engagement_score < %s)
                    ORDER BY s.lifetime_value DESC
                """, (cutoff_date, engagement_threshold))
            
            return [self._row_to_subscriber(row) for row in cursor.fetchall()]
    
    def churn_subscriber(
        self,
        subscriber_id: str,
        reason: str = "Voluntary cancellation"
    ) -> Subscriber:
        """
        Mark subscriber as churned
        
        Args:
            subscriber_id: Subscriber ID
            reason: Reason for churning
            
        Returns:
            Updated Subscriber object
        """
        now = datetime.utcnow()
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE phase2_subscribers
                SET subscription_status = 'churned',
                    churned_at = %s,
                    updated_at = %s
                WHERE subscriber_id = %s RETURNING *
            """, (now, now, subscriber_id))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_subscriber(row)
            raise ValueError(f"Subscriber {subscriber_id} not found")
    
    def create_winback_campaign(
        self,
        subscriber_id: str,
        campaign_type: str,
        offer_type: Optional[str] = None,
        discount_percent: Optional[int] = None,
        duration_days: int = 14
    ) -> WinbackCampaign:
        """
        Create a winback campaign for churned subscriber
        
        Args:
            subscriber_id: Subscriber ID
            campaign_type: Type of campaign
            offer_type: Type of offer
            discount_percent: Discount percentage
            duration_days: Offer duration in days
            
        Returns:
            WinbackCampaign object
        """
        campaign_id = f"wb_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        subscriber = self.get_subscriber(subscriber_id)
        if not subscriber:
            raise ValueError(f"Subscriber {subscriber_id} not found")
        
        days_since_churn = 0
        if subscriber.churned_at:
            days_since_churn = (now - subscriber.churned_at).days
        
        offer_start = now
        offer_end = now + timedelta(days=duration_days)
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO winback_campaigns (
                    campaign_id, subscriber_id, campaign_type, days_since_churn,
                    offer_type, discount_percent, offer_start_date, offer_end_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *
            """, (
                campaign_id, subscriber_id, campaign_type, days_since_churn,
                offer_type, discount_percent, offer_start, offer_end
            ))
            
            row = cursor.fetchone()
            return WinbackCampaign(
                id=row["id"],
                campaign_id=row["campaign_id"],
                subscriber_id=row["subscriber_id"],
                campaign_type=row["campaign_type"],
                days_since_churn=row["days_since_churn"],
                offer_type=row["offer_type"],
                discount_percent=row["discount_percent"],
                offer_start_date=row["offer_start_date"],
                offer_end_date=row["offer_end_date"],
                offer_claimed=row["offer_claimed"],
                claimed_at=row["claimed_at"],
                reactivated=row["reactivated"],
                reactivated_at=row["reactivated_at"],
                reactivation_value=row["reactivation_value"],
                status=row["status"],
                attempts_count=row["attempts_count"],
                last_attempt_at=row["last_attempt_at"],
                metadata=row["metadata"] if isinstance(row["metadata"], dict) else {},
                created_at=row["created_at"]
            )
    
    def record_ppv_purchase(
        self,
        subscriber_id: str,
        content_id: str,
        content_type: str,
        platform: str,
        price_paid: Decimal,
        original_price: Optional[Decimal] = None,
        tier_discount_percent: int = 0,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record a PPV (Pay-Per-View) purchase
        
        Args:
            subscriber_id: Subscriber ID
            content_id: Content ID
            content_type: Type of content
            platform: Platform name
            price_paid: Price paid by subscriber
            original_price: Original price before discount
            tier_discount_percent: Discount based on tier
            metadata: Additional metadata
            
        Returns:
            Dictionary with purchase details
        """
        purchase_id = f"ppv_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        discount_applied = (original_price or price_paid) - price_paid
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO ppv_purchases (
                    purchase_id, subscriber_id, content_id, content_type,
                    platform, price_paid, original_price, discount_applied,
                    tier_discount_percent, purchase_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *
            """, (
                purchase_id, subscriber_id, content_id, content_type,
                platform, price_paid, original_price, discount_applied,
                tier_discount_percent, now
            ))
            
            return {
                "purchase_id": purchase_id,
                "subscriber_id": subscriber_id,
                "content_id": content_id,
                "price_paid": str(price_paid),
                "original_price": str(original_price) if original_price else None,
                "discount_applied": str(discount_applied),
                "purchase_date": now.isoformat()
            }
    
    def get_subscriber_stats(
        self,
        platform: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get subscriber statistics for reporting
        
        Args:
            platform: Optional platform filter
            days: Number of days to analyze
            
        Returns:
            Dictionary with subscriber statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        with self.db.get_cursor(commit=False) as cursor:
            if platform:
                cursor.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE subscription_status = 'active') as active_subscribers,
                        COUNT(*) FILTER (WHERE subscription_status = 'churned') as churned_subscribers,
                        COUNT(*) FILTER (WHERE created_at >= %s) as new_subscribers,
                        SUM(monthly_rate) FILTER (WHERE subscription_status = 'active') as mrr,
                        AVG(lifetime_value) FILTER (WHERE subscription_status = 'active') as avg_ltv,
                        COUNT(*) as total_subscribers
                    FROM phase2_subscribers
                    WHERE platform = %s
                """, (start_date, platform))
            else:
                cursor.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE subscription_status = 'active') as active_subscribers,
                        COUNT(*) FILTER (WHERE subscription_status = 'churned') as churned_subscribers,
                        COUNT(*) FILTER (WHERE created_at >= %s) as new_subscribers,
                        SUM(monthly_rate) FILTER (WHERE subscription_status = 'active') as mrr,
                        AVG(lifetime_value) FILTER (WHERE subscription_status = 'active') as avg_ltv,
                        COUNT(*) as total_subscribers,
                        platform
                    FROM phase2_subscribers
                    GROUP BY platform
                """, (start_date,))
            
            results = cursor.fetchall()
            
            if platform:
                row = results[0] if results else {}
                return {
                    "platform": platform,
                    "active_subscribers": row.get("active_subscribers", 0),
                    "churned_subscribers": row.get("churned_subscribers", 0),
                    "new_subscribers": row.get("new_subscribers", 0),
                    "monthly_recurring_revenue": str(row.get("mrr", 0)),
                    "average_ltv": str(row.get("avg_ltv", 0)),
                    "total_subscribers": row.get("total_subscribers", 0),
                    "period_days": days
                }
            else:
                platform_stats = {}
                for row in results:
                    platform_name = row.get("platform", "unknown")
                    platform_stats[platform_name] = {
                        "active_subscribers": row.get("active_subscribers", 0),
                        "churned_subscribers": row.get("churned_subscribers", 0),
                        "new_subscribers": row.get("new_subscribers", 0),
                        "monthly_recurring_revenue": str(row.get("mrr", 0)),
                        "average_ltv": str(row.get("avg_ltv", 0)),
                        "total_subscribers": row.get("total_subscribers", 0)
                    }
                
                totals = {
                    "total_active_subscribers": sum(s["active_subscribers"] for s in platform_stats.values()),
                    "total_churned": sum(s["churned_subscribers"] for s in platform_stats.values()),
                    "total_new_subscribers": sum(s["new_subscribers"] for s in platform_stats.values()),
                    "total_mrr": sum(float(s["monthly_recurring_revenue"]) for s in platform_stats.values()),
                    "platform_breakdown": platform_stats,
                    "period_days": days
                }
                return totals
    
    def _row_to_subscriber(self, row: Dict) -> Subscriber:
        """Convert database row to Subscriber object"""
        return Subscriber(
            subscriber_id=row["subscriber_id"],
            platform=row["platform"],
            platform_user_id=row.get("platform_user_id"),
            username=row.get("username"),
            display_name=row.get("display_name"),
            email=row.get("email"),
            tier=row.get("tier", "basic"),
            subscription_status=row.get("subscription_status", "active"),
            subscription_start_date=row.get("subscription_start_date"),
            subscription_end_date=row.get("subscription_end_date"),
            next_billing_date=row.get("next_billing_date"),
            monthly_rate=row.get("monthly_rate", Decimal("0.00")),
            lifetime_value=row.get("lifetime_value", Decimal("0.00")),
            total_spent=row.get("total_spent", Decimal("0.00")),
            source_platform=row.get("source_platform"),
            referral_code=row.get("referral_code"),
            metadata=row.get("metadata") if isinstance(row.get("metadata"), dict) else {},
            created_at=row.get("created_at", datetime.utcnow()),
            updated_at=row.get("updated_at", datetime.utcnow()),
            last_activity_at=row.get("last_activity_at"),
            churned_at=row.get("churned_at")
        )
    
    def _calculate_engagement_score(
        self,
        messages_sent: int,
        messages_received: int,
        content_views: int,
        content_completions: int,
        likes_given: int,
        comments_made: int,
        shares: int,
        time_spent_minutes: int,
        dm_conversations: int
    ) -> Decimal:
        """
        Calculate engagement score based on weighted metrics
        
        Args:
            messages_sent: Messages sent by subscriber
            messages_received: Messages received by subscriber
            content_views: Content views
            content_completions: Content completions
            likes_given: Likes given
            comments_made: Comments made
            shares: Shares
            time_spent_minutes: Time spent
            dm_conversations: DM conversations
            
        Returns:
            Engagement score (0-1 range)
        """
        weights = {
            "messages_sent": 0.15,
            "messages_received": 0.10,
            "content_views": 0.10,
            "content_completions": 0.20,
            "likes_given": 0.05,
            "comments_made": 0.10,
            "shares": 0.10,
            "time_spent": 0.15,
            "dm_conversations": 0.05
        }
        
        max_values = {
            "messages_sent": 50,
            "messages_received": 100,
            "content_views": 200,
            "content_completions": 50,
            "likes_given": 100,
            "comments_made": 20,
            "shares": 10,
            "time_spent": 120,
            "dm_conversations": 10
        }
        
        normalized = {
            "messages_sent": min(messages_sent / max_values["messages_sent"], 1.0),
            "messages_received": min(messages_received / max_values["messages_received"], 1.0),
            "content_views": min(content_views / max_values["content_views"], 1.0),
            "content_completions": min(content_completions / max_values["content_completions"], 1.0),
            "likes_given": min(likes_given / max_values["likes_given"], 1.0),
            "comments_made": min(comments_made / max_values["comments_made"], 1.0),
            "shares": min(shares / max_values["shares"], 1.0),
            "time_spent": min(time_spent_minutes / max_values["time_spent"], 1.0),
            "dm_conversations": min(dm_conversations / max_values["dm_conversations"], 1.0)
        }
        
        score = sum(normalized[key] * weights[key] for key in weights)
        return Decimal(str(round(min(score, 1.0), 4)))


if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "jav_automation",
        "user": "postgres",
        "password": "postgres"
    }
    
    db = DatabaseConnection(db_config)
    manager = SubscriberManager(db)
    
    subscriber = manager.create_subscriber(
        platform="onlyfans",
        username="test_user",
        tier="premium",
        monthly_rate=Decimal("19.99"),
        source_platform="twitter"
    )
    print(f"Created subscriber: {subscriber.subscriber_id}")
    
    stats = manager.get_subscriber_stats(platform="onlyfans", days=30)
    print(f"Subscriber stats: {stats}")
