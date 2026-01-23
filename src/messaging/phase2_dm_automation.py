"""
Phase 2 DM Automation Module

Comprehensive direct message automation system for Phase 2 platforms,
supporting message sequences, templates, campaigns, and response tracking.

Last Updated: 2026-01-19
Migrated: 2026-01-22
"""

import json
import uuid
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of DM messages"""
    WELCOME = "welcome"
    ONBOARDING = "onboarding"
    PROMOTIONAL = "promotional"
    RETENTION = "retention"
    WINBACK = "winback"
    PPV_ANNOUNCEMENT = "ppv_announcement"
    CUSTOM_CONTENT_OFFER = "custom_content_offer"
    TIP_REQUEST = "tip_request"
    FOLLOW_UP = "follow_up"
    BIRTHDAY = "birthday"
    MILESTONE = "milestone"
    URGENT = "urgent"


class SequenceStatus(Enum):
    """DM sequence statuses"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MessageStatus(Enum):
    """Individual message statuses"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    RESPONDED = "responded"


class Platform(Enum):
    """Supported platforms for DM"""
    ONLYFANS = "onlyfans"
    XVIDEOS = "xvideos"
    PORNHUB = "pornhub"
    FANMART = "fanmart"
    FC2 = "fc2"
    FANTIA = "fantia"
    LINE = "line"


@dataclass
class DMTemplate:
    """DM template data model"""
    id: str
    template_name: str
    template_type: str
    platform: Optional[str]
    character_id: Optional[str]
    language: str
    subject_line: Optional[str]
    message_body: str
    variables: Dict
    conditions: Dict
    is_active: bool
    usage_count: int
    avg_response_rate: Decimal
    created_at: datetime
    updated_at: datetime


@dataclass
class DMSequence:
    """DM sequence definition"""
    id: str
    sequence_id: str
    subscriber_id: str
    platform: str
    sequence_type: str
    current_step: int
    total_steps: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    metadata: Dict


@dataclass
class DMMessage:
    """Individual DM message"""
    id: str
    message_id: str
    sequence_id: str
    subscriber_id: str
    platform: str
    step_number: int
    message_template_id: Optional[str]
    message_content: str
    message_type: str
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    response_received: bool
    response_content: Optional[str]
    engagement_score: Decimal
    status: str
    error_message: Optional[str]
    metadata: Dict
    created_at: datetime


@dataclass
class AutomationCampaign:
    """Automation campaign definition"""
    id: str
    campaign_id: str
    campaign_name: str
    campaign_type: str
    platform: Optional[str]
    character_id: Optional[str]
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    target_audience: Dict
    targeting_rules: Dict
    template_id: Optional[str]
    sequence_config: Dict
    total_targets: int
    sent_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    converted_count: int
    revenue_generated: Decimal
    budget: Optional[Decimal]
    cost_per_conversion: Decimal
    roi_percent: Decimal
    metadata: Dict
    created_at: datetime
    updated_at: datetime


class VariableInterpolator:
    """Handle variable interpolation in message templates"""
    
    VARIABLE_PATTERN = re.compile(r'\{\{([^}]+)\}\}')
    
    SUBSCRIBER_VARIABLES = {
        "subscriber_id", "username", "display_name", "first_name", "last_name",
        "email", "tier", "subscription_status", "months_subscribed",
        "total_spent", "lifetime_value", "last_activity_date"
    }
    
    CONTENT_VARIABLES = {
        "content_title", "content_type", "content_preview", "content_link",
        "character_name", "character_id"
    }
    
    PROMO_VARIABLES = {
        "discount_percent", "discount_code", "offer_end_date", "special_price",
        "bundle_description", "limited_time_offer"
    }
    
    SYSTEM_VARIABLES = {
        "current_date", "current_time", "platform_name", "sender_name",
        "unsubscribe_link", "help_link"
    }
    
    @classmethod
    def interpolate(
        cls,
        template: str,
        variables: Dict[str, Any],
        subscriber_data: Optional[Dict] = None,
        content_data: Optional[Dict] = None,
        promo_data: Optional[Dict] = None
    ) -> str:
        """
        Interpolate variables into template
        
        Args:
            template: Message template with {{variable}} placeholders
            variables: Base variables dict
            subscriber_data: Subscriber-specific data
            content_data: Content-specific data
            promo_data: Promotion-specific data
            
        Returns:
            Interpolated message string
        """
        now = datetime.utcnow()
        
        all_vars = variables.copy()
        
        all_vars.update({
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M:%S"),
            "platform_name": variables.get("platform", "our platform")
        })
        
        if subscriber_data:
            all_vars.update({
                k: v for k, v in subscriber_data.items()
                if k in cls.SUBSCRIBER_VARIABLES
            })
            if subscriber_data.get("display_name"):
                all_vars["first_name"] = subscriber_data["display_name"].split()[0]
        
        if content_data:
            all_vars.update({
                k: v for k, v in content_data.items()
                if k in cls.CONTENT_VARIABLES
            })
        
        if promo_data:
            all_vars.update({
                k: v for k, v in promo_data.items()
                if k in cls.PROMO_VARIABLES
            })
        
        def replace_var(match):
            var_name = match.group(1).strip()
            return str(all_vars.get(var_name, match.group(0)))
        
        return cls.VARIABLE_PATTERN.sub(replace_var, template)
    
    @classmethod
    def extract_variables(cls, template: str) -> List[str]:
        """Extract all variable names from template"""
        return list(cls.VARIABLE_PATTERN.findall(template))


class DatabaseConnection:
    """Database connection manager"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
    
    @contextmanager
    def get_connection(self):
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
            logger.error(f"PostgreSQL connection error: {e}")
            raise
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, commit: bool = True):
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


class DMAutomationManager:
    """
    Comprehensive DM automation system for Phase 2 platforms.
    
    Handles:
    - DM template creation and management
    - Message sequence automation
    - Campaign management
    - Response tracking and analytics
    - Subscriber engagement scoring
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.variable_interpolator = VariableInterpolator()
    
    def create_template(
        self,
        template_name: str,
        template_type: str,
        message_body: str,
        platform: Optional[str] = None,
        character_id: Optional[str] = None,
        language: str = "en",
        subject_line: Optional[str] = None,
        conditions: Optional[Dict] = None
    ) -> DMTemplate:
        """
        Create a new DM template
        
        Args:
            template_name: Human-readable name
            template_type: Type of message
            message_body: Message content with {{variable}} placeholders
            platform: Target platform
            character_id: Character to use
            language: Message language
            subject_line: Subject line for platforms that support it
            conditions: Targeting conditions
            
        Returns:
            Created DMTemplate object
        """
        template_id = f"tmpl_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        variables = self.variable_interpolator.extract_variables(message_body)
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO dm_templates (
                    template_id, template_name, template_type, platform,
                    character_id, language, subject_line, message_body,
                    variables, conditions, is_active, usage_count,
                    avg_response_rate, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                template_id, template_name, template_type, platform,
                character_id, language, subject_line, message_body,
                json.dumps(variables), json.dumps(conditions or {}),
                True, 0, 0.0, now, now
            ))
            
            return DMTemplate(
                id=template_id,
                template_name=template_name,
                template_type=template_type,
                platform=platform,
                character_id=character_id,
                language=language,
                subject_line=subject_line,
                message_body=message_body,
                variables={"extracted": variables},
                conditions=conditions or {},
                is_active=True,
                usage_count=0,
                avg_response_rate=Decimal("0"),
                created_at=now,
                updated_at=now
            )
    
    def get_template(self, template_id: str) -> Optional[DMTemplate]:
        """Get template by ID"""
        with self.db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM dm_templates WHERE template_id = %s
            """, (template_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_template(row)
            return None
    
    def get_templates_by_type(
        self,
        template_type: str,
        platform: Optional[str] = None
    ) -> List[DMTemplate]:
        """Get all templates of a specific type"""
        with self.db.get_cursor(commit=False) as cursor:
            if platform:
                cursor.execute("""
                    SELECT * FROM dm_templates
                    WHERE template_type = %s AND platform = %s AND is_active = true
                    ORDER BY usage_count DESC
                """, (template_type, platform))
            else:
                cursor.execute("""
                    SELECT * FROM dm_templates
                    WHERE template_type = %s AND is_active = true
                    ORDER BY usage_count DESC
                """, (template_type,))
            
            return [self._row_to_template(row) for row in cursor.fetchall()]
    
    def start_sequence(
        self,
        subscriber_id: str,
        platform: str,
        sequence_type: str,
        template_ids: List[str],
        delays_hours: List[int],
        character_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> DMSequence:
        """
        Start a DM sequence for a subscriber
        
        Args:
            subscriber_id: Subscriber ID
            platform: Platform name
            sequence_type: Type of sequence
            template_ids: List of template IDs to use
            delays_hours: Delay in hours between each message
            character_id: Character to use
            metadata: Additional metadata
            
        Returns:
            Created DMSequence object
        """
        sequence_id = f"seq_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        if len(template_ids) != len(delays_hours):
            raise ValueError("template_ids and delays_hours must have same length")
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO dm_sequences (
                    sequence_id, subscriber_id, platform, sequence_type,
                    current_step, total_steps, status, started_at, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                sequence_id, subscriber_id, platform, sequence_type,
                0, len(template_ids), "active", now, json.dumps(metadata or {})
            ))
            
            for i, (template_id, delay) in enumerate(zip(template_ids, delays_hours)):
                template = self.get_template(template_id)
                if not template:
                    logger.warning(f"Template {template_id} not found, skipping")
                    continue
                
                scheduled_at = now + timedelta(hours=delay)
                message_id = f"msg_{uuid.uuid4().hex[:12]}"
                
                cursor.execute("""
                    INSERT INTO dm_messages (
                        message_id, sequence_id, subscriber_id, platform,
                        step_number, message_template_id, message_content,
                        message_type, scheduled_at, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    message_id, sequence_id, subscriber_id, platform,
                    i + 1, template_id, template.message_body,
                    template.template_type, scheduled_at, "scheduled", now
                ))
            
            return DMSequence(
                id=sequence_id,
                sequence_id=sequence_id,
                subscriber_id=subscriber_id,
                platform=platform,
                sequence_type=sequence_type,
                current_step=0,
                total_steps=len(template_ids),
                status="active",
                started_at=now,
                completed_at=None,
                metadata=metadata or {}
            )
    
    def get_active_sequences(
        self,
        platform: Optional[str] = None
    ) -> List[DMSequence]:
        """Get all active DM sequences"""
        with self.db.get_cursor(commit=False) as cursor:
            if platform:
                cursor.execute("""
                    SELECT * FROM dm_sequences
                    WHERE platform = %s AND status = 'active'
                    ORDER BY started_at DESC
                """, (platform,))
            else:
                cursor.execute("""
                    SELECT * FROM dm_sequences
                    WHERE status = 'active'
                    ORDER BY started_at DESC
                """)
            
            return [self._row_to_sequence(row) for row in cursor.fetchall()]
    
    def get_pending_messages(
        self,
        platform: Optional[str] = None,
        limit: int = 100
    ) -> List[DMMessage]:
        """Get messages scheduled to be sent"""
        now = datetime.utcnow()
        
        with self.db.get_cursor(commit=False) as cursor:
            if platform:
                cursor.execute("""
                    SELECT * FROM dm_messages
                    WHERE platform = %s AND status = 'scheduled'
                    AND scheduled_at <= %s
                    ORDER BY scheduled_at ASC
                    LIMIT %s
                """, (platform, now, limit))
            else:
                cursor.execute("""
                    SELECT * FROM dm_messages
                    WHERE status = 'scheduled'
                    AND scheduled_at <= %s
                    ORDER BY scheduled_at ASC
                    LIMIT %s
                """, (now, limit))
            
            return [self._row_to_message(row) for row in cursor.fetchall()]
    
    def send_message(
        self,
        message_id: str,
        subscriber_data: Optional[Dict] = None,
        content_data: Optional[Dict] = None,
        promo_data: Optional[Dict] = None
    ) -> DMMessage:
        """
        Send a scheduled message (placeholder for actual API integration)
        
        Args:
            message_id: Message ID to send
            subscriber_data: Subscriber variables
            content_data: Content variables
            promo_data: Promotion variables
            
        Returns:
            Updated DMMessage object
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM dm_messages WHERE message_id = %s
            """, (message_id,))
            
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Message {message_id} not found")
            
            template_id = row.get("message_template_id")
            template = self.get_template(template_id) if template_id else None
            
            if template:
                interpolated_content = self.variable_interpolator.interpolate(
                    template.message_body,
                    {
                        "platform": row["platform"],
                        "character_id": template.character_id
                    },
                    subscriber_data,
                    content_data,
                    promo_data
                )
                
                cursor.execute("""
                    UPDATE dm_messages
                    SET message_content = %s, sent_at = %s, status = 'sent'
                    WHERE message_id = %s RETURNING *
                """, (interpolated_content, datetime.utcnow(), message_id))
            else:
                cursor.execute("""
                    UPDATE dm_messages
                    SET sent_at = %s, status = 'sent'
                    WHERE message_id = %s RETURNING *
                """, (datetime.utcnow(), message_id))
            
            row = cursor.fetchone()
            return self._row_to_message(row)
    
    def record_response(
        self,
        message_id: str,
        response_content: str,
        engagement_score: Optional[Decimal] = None
    ) -> DMMessage:
        """
        Record subscriber response to a message
        
        Args:
            message_id: Message ID
            response_content: Response text
            engagement_score: Optional engagement score
            
        Returns:
            Updated DMMessage object
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE dm_messages
                SET response_received = true,
                    response_content = %s,
                    status = 'responded',
                    engagement_score = %s
                WHERE message_id = %s RETURNING *
            """, (response_content, engagement_score or Decimal("0.5"), message_id))
            
            row = cursor.fetchone()
            return self._row_to_message(row)
    
    def get_message_analytics(
        self,
        platform: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get DM message analytics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        with self.db.get_cursor(commit=False) as cursor:
            if platform:
                cursor.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE status IN ('sent', 'delivered', 'read', 'responded')) as total_sent,
                        COUNT(*) FILTER (WHERE status = 'delivered') as delivered,
                        COUNT(*) FILTER (WHERE status = 'read') as read,
                        COUNT(*) FILTER (WHERE status = 'responded') as responded,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed
                    FROM dm_messages
                    WHERE platform = %s AND created_at >= %s
                """, (platform, start_date))
            else:
                cursor.execute("""
                    SELECT
                        platform,
                        COUNT(*) FILTER (WHERE status IN ('sent', 'delivered', 'read', 'responded')) as total_sent,
                        COUNT(*) FILTER (WHERE status = 'delivered') as delivered,
                        COUNT(*) FILTER (WHERE status = 'read') as read,
                        COUNT(*) FILTER (WHERE status = 'responded') as responded,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed
                    FROM dm_messages
                    WHERE created_at >= %s
                    GROUP BY platform
                """, (start_date,))
            
            results = cursor.fetchall()
            
            if platform and results:
                row = results[0]
                sent = row["total_sent"] or 0
                delivered = row["delivered"] or 0
                read = row["read"] or 0
                responded = row["responded"] or 0
                
                return {
                    "platform": platform,
                    "period_days": days,
                    "total_sent": sent,
                    "delivered": delivered,
                    "read": read,
                    "responded": responded,
                    "delivery_rate": f"{(delivered/sent*100):.2f}%" if sent > 0 else "0%",
                    "read_rate": f"{(read/sent*100):.2f}%" if sent > 0 else "0%",
                    "response_rate": f"{(responded/sent*100):.2f}%" if sent > 0 else "0%"
                }
            elif results:
                platform_stats = {}
                total_sent = 0
                total_delivered = 0
                total_read = 0
                total_responded = 0
                
                for row in results:
                    p = row["platform"]
                    sent = row["total_sent"] or 0
                    delivered = row["delivered"] or 0
                    read = row["read"] or 0
                    responded = row["responded"] or 0
                    
                    total_sent += sent
                    total_delivered += delivered
                    total_read += read
                    total_responded += responded
                    
                    platform_stats[p] = {
                        "total_sent": sent,
                        "delivered": delivered,
                        "read": read,
                        "responded": responded,
                        "delivery_rate": f"{(delivered/sent*100):.2f}%" if sent > 0 else "0%",
                        "response_rate": f"{(responded/sent*100):.2f}%" if sent > 0 else "0%"
                    }
                
                return {
                    "period_days": days,
                    "platforms": platform_stats,
                    "total_sent": total_sent,
                    "total_delivered": total_delivered,
                    "total_read": total_read,
                    "total_responded": total_responded,
                    "overall_delivery_rate": f"{(total_delivered/total_sent*100):.2f}%" if total_sent > 0 else "0%",
                    "overall_response_rate": f"{(total_responded/total_sent*100):.2f}%" if total_sent > 0 else "0%"
                }
            
            return {"period_days": days, "message": "No message data found"}
    
    def _row_to_template(self, row: Dict) -> DMTemplate:
        return DMTemplate(
            id=row["template_id"],
            template_name=row["template_name"],
            template_type=row["template_type"],
            platform=row.get("platform"),
            character_id=row.get("character_id"),
            language=row.get("language", "en"),
            subject_line=row.get("subject_line"),
            message_body=row["message_body"],
            variables=row.get("variables", {}),
            conditions=row.get("conditions", {}),
            is_active=row.get("is_active", True),
            usage_count=row.get("usage_count", 0),
            avg_response_rate=row.get("avg_response_rate", Decimal("0")),
            created_at=row.get("created_at", datetime.utcnow()),
            updated_at=row.get("updated_at", datetime.utcnow())
        )
    
    def _row_to_sequence(self, row: Dict) -> DMSequence:
        return DMSequence(
            id=row["id"],
            sequence_id=row["sequence_id"],
            subscriber_id=row["subscriber_id"],
            platform=row["platform"],
            sequence_type=row["sequence_type"],
            current_step=row.get("current_step", 0),
            total_steps=row.get("total_steps", 0),
            status=row.get("status", "active"),
            started_at=row.get("started_at", datetime.utcnow()),
            completed_at=row.get("completed_at"),
            metadata=row.get("metadata", {})
        )
    
    def _row_to_message(self, row: Dict) -> DMMessage:
        return DMMessage(
            id=row["id"],
            message_id=row["message_id"],
            sequence_id=row["sequence_id"],
            subscriber_id=row["subscriber_id"],
            platform=row["platform"],
            step_number=row.get("step_number", 0),
            message_template_id=row.get("message_template_id"),
            message_content=row.get("message_content", ""),
            message_type=row.get("message_type", ""),
            scheduled_at=row.get("scheduled_at"),
            sent_at=row.get("sent_at"),
            delivered_at=row.get("delivered_at"),
            read_at=row.get("read_at"),
            response_received=row.get("response_received", False),
            response_content=row.get("response_content"),
            engagement_score=row.get("engagement_score", Decimal("0")),
            status=row.get("status", "pending"),
            error_message=row.get("error_message"),
            metadata=row.get("metadata", {}),
            created_at=row.get("created_at", datetime.utcnow())
        )


class WelcomeSequenceBuilder:
    """Builder class for creating welcome sequences"""
    
    DEFAULT_WELCOME_TEMPLATES = {
        "en": {
            "welcome": {
                "subject": "Welcome to {{platform_name}}!",
                "body": "Hey {{first_name}}! Welcome to our exclusive community!"
            },
            "onboarding_1": {
                "subject": "Getting started tips",
                "body": "Hi {{first_name}}! Here are some tips to get the most out of your subscription."
            }
        },
        "es": {
            "welcome": {
                "subject": "Bienvenido a {{platform_name}}!",
                "body": "Hey {{first_name}}! Bienvenido a nuestra comunidad exclusiva!"
            },
            "onboarding_1": {
                "subject": "Consejos para empezar",
                "body": "Hola {{first_name}}! Aqui tienes algunos consejos."
            }
        }
    }
    
    @classmethod
    def create_welcome_sequence(
        cls,
        dm_manager: DMAutomationManager,
        platform: str,
        language: str = "en",
        character_id: Optional[str] = None
    ) -> Tuple[List[str], List[int]]:
        """Create default welcome sequence templates"""
        templates = cls.DEFAULT_WELCOME_TEMPLATES.get(language, cls.DEFAULT_WELCOME_TEMPLATES["en"])
        template_ids = []
        delays = [0, 24]  # 0h, 24h
        
        for step_name, content in templates.items():
            template = dm_manager.create_template(
                template_name=f"Welcome_{platform}_{step_name}",
                template_type=MessageType.ONBOARDING.value,
                platform=platform,
                character_id=character_id,
                language=language,
                subject_line=content["subject"],
                message_body=content["body"]
            )
            template_ids.append(template.id)
        
        return template_ids, delays


class RetentionSequenceBuilder:
    """Builder class for creating retention sequences"""
    
    DEFAULT_RETENTION_TEMPLATES = {
        "en": {
            "check_in": {
                "subject": "We miss you!",
                "body": "Hey {{first_name}}! It's been a while since we saw you around here..."
            },
            "special_offer": {
                "subject": "A little gift for you",
                "body": "{{first_name}}! We noticed you haven't been as active..."
            }
        },
        "es": {
            "check_in": {
                "subject": "Te echamos de menos!",
                "body": "Hey {{first_name}}! Ha pasado un tiempo desde que te vimos..."
            },
            "special_offer": {
                "subject": "Un pequeno regalo para ti",
                "body": "{{first_name}}! Notamos que no has estado tan activo..."
            }
        }
    }
    
    @classmethod
    def create_retention_sequence(
        cls,
        dm_manager: DMAutomationManager,
        platform: str,
        language: str = "en",
        character_id: Optional[str] = None
    ) -> Tuple[List[str], List[int]]:
        """Create default retention sequence templates"""
        templates = cls.DEFAULT_RETENTION_TEMPLATES.get(language, cls.DEFAULT_RETENTION_TEMPLATES["en"])
        template_ids = []
        delays = [168, 336]  # 7, 14 days
        
        for step_name, content in templates.items():
            template = dm_manager.create_template(
                template_name=f"Retention_{platform}_{step_name}",
                template_type=MessageType.RETENTION.value,
                platform=platform,
                character_id=character_id,
                language=language,
                subject_line=content["subject"],
                message_body=content["body"]
            )
            template_ids.append(template.id)
        
        return template_ids, delays


if __name__ == "__main__":
    import os
    
    def get_db_config():
        """Get database configuration from environment variables"""
        db_config = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": int(os.environ.get("DB_PORT", 5432)),
            "database": os.environ.get("DB_NAME", "jav_automation"),
            "user": os.environ.get("DB_USER"),
            "password": os.environ.get("DB_PASSWORD")
        }
        
        if not db_config["user"] or not db_config["password"]:
            print("[ERROR] Database credentials not configured.")
            return None
        
        return db_config
    
    DB_CONFIG = get_db_config()
    
    if DB_CONFIG is None:
        print("\n[WARNING] Running in test mode without database.")
    else:
        db = DatabaseConnection(DB_CONFIG)
        dm = DMAutomationManager(db)
        
        template = dm.create_template(
            template_name="Welcome Test",
            template_type="onboarding",
            platform="onlyfans",
            language="en",
            subject_line="Welcome {{first_name}}!",
            message_body="Hey {{first_name}}! Welcome to our community!"
        )
        print(f"Created template: {template.id}")
        
        analytics = dm.get_message_analytics(platform="onlyfans", days=30)
        print(f"Message analytics: {json.dumps(analytics, indent=2, default=str)}")
