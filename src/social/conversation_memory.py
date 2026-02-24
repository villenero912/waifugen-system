"""
Conversation Memory for WF03 — Engagement AutoReply

Improvement: Adds per-user conversation context so auto-replies
are consistent and personalized instead of independent responses.

Each user's last N interactions are stored in PostgreSQL and passed
to Ollama as context when generating the next reply.
"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

MAX_HISTORY = 5  # Last 5 interactions per user per character


@dataclass
class UserMessage:
    """Single message in a conversation"""
    user_id: str
    platform: str
    character: str
    user_text: str
    bot_reply: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ConversationMemory:
    """
    Stores and retrieves per-user conversation history.
    Used by WF03 to give Ollama context when generating replies.

    Storage: PostgreSQL (via existing db connection) or in-memory fallback.
    """

    def __init__(self, db_conn=None):
        self.db = db_conn
        self._memory: Dict[str, List[UserMessage]] = {}  # in-memory fallback
        self._ensure_table()

    def _ensure_table(self):
        """Create conversation_history table if it doesn't exist."""
        if not self.db:
            return
        try:
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    platform VARCHAR(50) NOT NULL,
                    character VARCHAR(100) NOT NULL,
                    user_text TEXT NOT NULL,
                    bot_reply TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conv_user_char 
                ON conversation_history(user_id, character, platform)
            """)
        except Exception as e:
            logger.warning(f"Could not create conversation_history table: {e}")

    def get_history(self, user_id: str, platform: str, character: str) -> List[UserMessage]:
        """Get last N messages for a user with a specific character."""
        key = f"{user_id}:{platform}:{character}"

        if self.db:
            try:
                rows = self.db.execute("""
                    SELECT user_id, platform, character, user_text, bot_reply, created_at
                    FROM conversation_history
                    WHERE user_id = %s AND platform = %s AND character = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, platform, character, MAX_HISTORY)).fetchall()
                return [UserMessage(
                    user_id=r[0], platform=r[1], character=r[2],
                    user_text=r[3], bot_reply=r[4], timestamp=str(r[5])
                ) for r in reversed(rows)]
            except Exception as e:
                logger.warning(f"DB read failed, using memory: {e}")

        return self._memory.get(key, [])[-MAX_HISTORY:]

    def save_exchange(self, user_id: str, platform: str, character: str,
                      user_text: str, bot_reply: str):
        """Save a user message + bot reply to history."""
        key = f"{user_id}:{platform}:{character}"
        msg = UserMessage(user_id=user_id, platform=platform, character=character,
                          user_text=user_text, bot_reply=bot_reply)

        if self.db:
            try:
                self.db.execute("""
                    INSERT INTO conversation_history 
                    (user_id, platform, character, user_text, bot_reply)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, platform, character, user_text, bot_reply))
                return
            except Exception as e:
                logger.warning(f"DB write failed, using memory: {e}")

        if key not in self._memory:
            self._memory[key] = []
        self._memory[key].append(msg)
        self._memory[key] = self._memory[key][-MAX_HISTORY:]

    def build_ollama_context(self, user_id: str, platform: str, character: str,
                              new_message: str) -> str:
        """
        Build a context-aware prompt for Ollama that includes conversation history.

        Returns a prompt string ready to send to Ollama.
        """
        history = self.get_history(user_id, platform, character)

        context_lines = []
        if history:
            context_lines.append("Previous conversation with this user:")
            for msg in history:
                context_lines.append(f"  User: {msg.user_text}")
                context_lines.append(f"  {character}: {msg.bot_reply}")
            context_lines.append("")

        context_lines.append(f"User's new message: {new_message}")
        context_lines.append(f"Reply as {character}, staying in character. Keep it short and engaging.")

        return "\n".join(context_lines)

    def get_user_stats(self, user_id: str, platform: str, character: str) -> Dict:
        """Get engagement stats for a user — useful for funnel scoring."""
        history = self.get_history(user_id, platform, character)
        return {
            "total_interactions": len(history),
            "is_repeat_user": len(history) > 1,
            "is_engaged": len(history) >= 3,  # 3+ interactions = high engagement
            "last_interaction": history[-1].timestamp if history else None
        }
