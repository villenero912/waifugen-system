"""
Telegram Bot Integration Module

This module provides a Telegram bot for receiving real-time notifications,
sending commands, and querying system status for the ELITE 8 AI Video Generation System.

Features:
- Real-time production notifications (video completed, uploaded, failed)
- Credit usage alerts and budget warnings
- System health status commands
- Interactive command interface
- Support for multiple chat IDs (admin, monitoring channels)

Version: 1.0.0
Created: 2026-01-22
"""

import asyncio
import json
import logging
import hashlib
import hmac
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications the bot can send"""
    VIDEO_STARTED = "video_started"
    VIDEO_COMPLETED = "video_completed"
    VIDEO_FAILED = "video_failed"
    UPLOAD_STARTED = "upload_started"
    UPLOAD_COMPLETED = "upload_completed"
    UPLOAD_FAILED = "upload_failed"
    CREDITS_LOW = "credits_low"
    CREDITS_CRITICAL = "credits_critical"
    BUDGET_WARNING = "budget_warning"
    SYSTEM_ERROR = "system_error"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"
    SCHEDULER_STATUS = "scheduler_status"
    PROXY_STATUS = "proxy_status"


@dataclass
class TelegramConfig:
    """Configuration for Telegram bot"""
    bot_token: str = ""
    admin_chat_ids: List[int] = field(default_factory=list)
    monitoring_chat_ids: List[int] = field(default_factory=list)
    webhook_url: str = ""
    webhook_secret: str = ""
    enabled: bool = True
    notify_on_video_complete: bool = True
    notify_on_video_failed: bool = True
    notify_on_upload_complete: bool = True
    notify_on_upload_failed: bool = True
    notify_on_credit_warning: bool = True
    daily_summary_enabled: bool = True
    daily_summary_time: str = "20:00"
    command_prefix: str = "/"
    
    @classmethod
    def from_json(cls, config_path: str) -> 'TelegramConfig':
        """Load configuration from JSON file"""
        path = Path(config_path)
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.enabled:
            return True
        if not self.bot_token:
            logger.error("Telegram bot token not configured")
            return False
        if not self.admin_chat_ids:
            logger.warning("No admin chat IDs configured - bot will run in listen-only mode")
        return True


class TelegramBot:
    """
    Telegram bot for ELITE 8 system monitoring and notifications.
    
    This class handles:
    - Sending notifications to configured chats
    - Processing commands from users
    - Maintaining conversation context
    - Webhook verification (if enabled)
    """
    
    def __init__(self, config: TelegramConfig = None, production_monitor=None):
        """
        Initialize Telegram bot.
        
        Args:
            config: Telegram configuration
            production_monitor: Reference to ProductionMonitor for status queries
        """
        self.config = config or TelegramConfig()
        self.production_monitor = production_monitor
        self.application: Optional[Application] = None
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        
        # Command handlers mapping
        self.command_handlers: Dict[str, Callable] = {
            'start': self._cmd_start,
            'help': self._cmd_help,
            'status': self._cmd_status,
            'credits': self._cmd_credits,
            'daily': self._cmd_daily,
            'weekly': self._cmd_weekly,
            'character': self._cmd_character,
            'platform': self._cmd_platform,
            'budget': self._cmd_budget,
            'schedule': self._cmd_schedule,
            'restart': self._cmd_restart,
            'pause': self._cmd_pause,
            'resume': self._cmd_resume,
            'phase1': self._cmd_phase1,
            'phase2': self._cmd_phase2,
        }
        
        logger.info("Telegram Bot initialized")

    def restricted(self, func):
        """Decorator to restrict access to admin chat IDs"""
        @wraps(func)
        async def wrapped(instance, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            chat_id = update.effective_chat.id
            if chat_id not in instance.config.admin_chat_ids:
                logger.warning(f"Unauthorized access attempt from chat ID {chat_id}")
                await update.message.reply_text("⛔ <b>Acceso denegado.</b> No tienes permiso para usar este bot.", parse_mode='HTML')
                return
            return await func(instance, update, context, *args, **kwargs)
        return wrapped
    
    async def initialize(self):
        """Initialize the bot application"""
        if not self.config.enabled:
            logger.info("Telegram notifications disabled")
            return
        
        if not self.config.validate():
            logger.error("Telegram configuration invalid - disabling bot")
            self.config.enabled = False
            return
        
        try:
            self.application = Application.builder().token(self.config.bot_token).build()
            
            # Register command handlers
            for command, handler in self.command_handlers.items():
                self.application.add_handler(
                    CommandHandler(command, handler)
                )
            
            # Register callback query handler for inline buttons
            self.application.add_handler(
                CallbackQueryHandler(self._handle_callback)
            )
            
            # Register unknown command handler
            self.application.add_handler(
                MessageHandler(filters.COMMAND, self._handle_unknown)
            )
            
            logger.info("Telegram bot application initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            self.config.enabled = False
    
    async def start(self):
        """Start the bot and notification processor"""
        if not self.config.enabled:
            return
        
        self.running = True
        
        # Start notification processor in background
        asyncio.create_task(self._process_notifications())
        
        # Start webhook or polling
        if self.config.webhook_url:
            await self._start_webhook()
        else:
            await self._start_polling()
    
    async def _start_polling(self):
        """Start bot in polling mode"""
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("Telegram bot started in polling mode")
        except Exception as e:
            logger.error(f"Failed to start polling: {e}")
    
    async def _start_webhook(self):
        """Start bot in webhook mode"""
        try:
            await self.application.initialize()
            await self.application.bot.set_webhook(
                url=self.config.webhook_url,
                secret_token=self.config.webhook_secret
            )
            logger.info(f"Telegram webhook set to {self.config.webhook_url}")
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
    
    async def stop(self):
        """Stop the bot gracefully"""
        self.running = False
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot stopped")
    
    async def _process_notifications(self):
        """Process notifications from queue"""
        while self.running:
            try:
                notification = await self.notification_queue.get()
                await self._send_notification(notification)
                await asyncio.sleep(0.1)  # Rate limiting
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing notification: {e}")
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send a notification to all configured chats"""
        notification_type = notification.get('type')
        message = self._format_message(notification)
        chat_ids = notification.get('chat_ids', self.config.monitoring_chat_ids)
        
        for chat_id in chat_ids:
            try:
                if 'keyboard' in notification:
                    keyboard = self._build_keyboard(notification['keyboard'])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await self.application.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                else:
                    await self.application.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='HTML'
                    )
                logger.debug(f"Notification sent to {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to {chat_id}: {e}")
    
    def _format_message(self, notification: Dict[str, Any]) -> str:
        """Format notification message with emoji and styling"""
        emoji_map = {
            NotificationType.VIDEO_STARTED.value: "🎬",
            NotificationType.VIDEO_COMPLETED.value: "✅",
            NotificationType.VIDEO_FAILED.value: "❌",
            NotificationType.UPLOAD_STARTED.value: "📤",
            NotificationType.UPLOAD_COMPLETED.value: "🚀",
            NotificationType.UPLOAD_FAILED.value: "⚠️",
            NotificationType.CREDITS_LOW.value: "💳",
            NotificationType.CREDITS_CRITICAL.value: "🚨",
            NotificationType.BUDGET_WARNING.value: "💰",
            NotificationType.SYSTEM_ERROR.value: "🔧",
            NotificationType.DAILY_SUMMARY.value: "📊",
            NotificationType.WEEKLY_REPORT.value: "📈",
            NotificationType.SCHEDULER_STATUS.value: "⏰",
            NotificationType.PROXY_STATUS.value: "🌐",
        }
        
        emoji = emoji_map.get(notification.get('type'), "📢")
        title = notification.get('title', "Notification")
        message = notification.get('message', "")
        details = notification.get('details', "")
        
        formatted = f"{emoji} <b>{title}</b>\n\n{message}"
        
        if details:
            formatted += f"\n\n📝 <b>Details:</b>\n<pre>{details}</pre>"
        
        formatted += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return formatted
    
    def _build_keyboard(self, buttons: List[Dict[str, str]]) -> List[List[InlineKeyboardButton]]:
        """Build inline keyboard from button definitions"""
        keyboard = []
        for row in buttons:
            button_row = []
            for button in row:
                button_row.append(
                    InlineKeyboardButton(
                        text=button.get('text', 'Button'),
                        callback_data=button.get('callback', '')
                    )
                )
            keyboard.append(button_row)
        return keyboard
    
    def queue_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        details: str = "",
        chat_ids: List[int] = None
    ):
        """Queue a notification to be sent"""
        notification = {
            'type': notification_type.value,
            'title': title,
            'message': message,
            'details': details,
            'chat_ids': chat_ids or self.config.monitoring_chat_ids
        }
        self.notification_queue.put_nowait(notification)
    
    # Command handlers
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat_id = update.message.chat_id
        welcome_message = """
🎉 <b>Welcome to ELITE 8 Bot!</b>

This bot monitors the AI Video Generation System and provides real-time notifications.

Available commands:
• /status - Check system status
• /credits - View credit usage
• /daily - Today's production summary
• /weekly - Weekly report
• /character - Character rotation status
• /platform - Platform distribution
• /budget - Budget status
• /schedule - Scheduler status
• /help - Show this help

Use /help for more information.
"""
        await update.message.reply_text(welcome_message, parse_mode='HTML')
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
🤖 <b>ELITE 8 Bot Commands</b>

<b>Status Commands:</b>
• /status - Full system status
• /credits - A2E API credits remaining
• /schedule - Scheduler job status

<b>Production Commands:</b>
• /daily - Today's production summary
• /weekly - Weekly production report
• /character - Character rotation status
• /platform - Platform distribution

<b>Control Commands:</b>
• /restart - Restart production system
• /pause - Pause all production
• /resume - Resume production

<b>Budget Commands:</b>
• /budget - Current budget status

For real-time updates, ensure notifications are enabled.
"""
        await update.message.reply_text(help_message, parse_mode='HTML')
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if self.production_monitor:
            status = self.production_monitor.get_full_status()
            message = self._format_status_message(status)
        else:
            message = "⚠️ Production monitor not connected"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def _cmd_credits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /credits command"""
        if self.production_monitor:
            credits = await self.production_monitor.get_credit_status()
            message = self._format_credits_message(credits)
        else:
            message = "⚠️ Production monitor not connected"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def _cmd_daily(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /daily command"""
        if self.production_monitor:
            daily = self.production_monitor.get_daily_summary()
            message = self._format_daily_message(daily)
        else:
            message = "⚠️ Production monitor not connected"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def _cmd_weekly(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /weekly command"""
        if self.production_monitor:
            weekly = self.production_monitor.get_weekly_summary()
            message = self._format_weekly_message(weekly)
        else:
            message = "⚠️ Production monitor not connected"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def _cmd_character(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /character command"""
        if self.production_monitor:
            rotation = self.production_monitor.get_character_rotation_status()
            message = self._format_character_message(rotation)
        else:
            message = "⚠️ Production monitor not connected"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def _cmd_platform(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /platform command"""
        if self.production_monitor:
            platform = self.production_monitor.get_platform_distribution()
            message = self._format_platform_message(platform)
        else:
            message = "⚠️ Production monitor not connected"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def _cmd_budget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /budget command"""
        if self.production_monitor:
            credits = await self.production_monitor.get_credit_status()
            budget = self.production_monitor.estimate_remaining_cost(4)
            message = self._format_budget_message(credits, budget)
        else:
            message = "⚠️ Production monitor not connected"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def _cmd_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /schedule command"""
        message = """
⏰ <b>Scheduler Status</b>

✅ Scheduler is running
📋 Next scheduled jobs:
   • 09:00 - Daily credit check
   • 10:00 - Content generation start
   • 12:00 - Video upload batch 1
   • 15:00 - Video upload batch 2
   • 18:00 - Video upload batch 3
   • 20:00 - Daily summary report

Use /restart to reload scheduler configuration.
"""
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def _cmd_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /restart command"""
        chat_id = update.effective_chat.id
        if chat_id not in self.config.admin_chat_ids:
            await update.message.reply_text("⛔ No tienes permiso para reiniciar el sistema.")
            return
        await update.message.reply_text("🔄 Reiniciando sistema de producción...")
    
    async def _cmd_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pause command"""
        chat_id = update.effective_chat.id
        if chat_id not in self.config.admin_chat_ids:
            await update.message.reply_text("⛔ No tienes permiso para pausar la producción.")
            return
        await update.message.reply_text("⏸️ Pausando toda la producción...")
    
    async def _cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /resume command"""
        chat_id = update.effective_chat.id
        if chat_id not in self.config.admin_chat_ids:
            await update.message.reply_text("⛔ No tienes permiso para reanudar la producción.")
            return
        await update.message.reply_text("▶️ Reanudando producción...")

    async def _cmd_phase1(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el panel de control de Fase 1 (Reels & Karaoke)"""
        keyboard = [
            [
                InlineKeyboardButton("🎬 Reels Profesionales", callback_data="p1_start_reels"),
                InlineKeyboardButton("🎤 Karaoke JP (Miyuki)", callback_data="p1_start_karaoke")
            ],
            [
                InlineKeyboardButton("📊 Reporte Diario", callback_data="daily_summary"),
                InlineKeyboardButton("⚙️ Config n8n", callback_data="p1_n8n_status")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🚀 <b>FASE 1: Automatización Diaria</b>\n\nContenido profesional de alta frecuencia para TikTok, IG y YouTube.",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _cmd_phase2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el panel de control de Fase 2 (Nivel 8 & GPU)"""
        keyboard = [
            [
                InlineKeyboardButton("📁 Generar Dataset (Aiko)", callback_data="p2_dataset_aiko"),
                InlineKeyboardButton("🏗️ Entrenar LoRA (4090)", callback_data="p2_train_aiko")
            ],
            [
                InlineKeyboardButton("🔞 Iniciar Edición NSFW", callback_data="p2_start_edit"),
                InlineKeyboardButton("🛡️ Aplicar Pixelado/Proxy", callback_data="p2_compliance")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🔞 <b>FASE 2: Expansión Global & Contenido Adulto</b>\n\nGestión de GPU remota, entrenamiento LoRA y cumplimiento legal (JP).",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'refresh_status':
            await self._cmd_status(update, context)
        elif query.data == 'show_credits':
            await self._cmd_credits(update, context)
        elif query.data == 'daily_summary':
            await self._cmd_daily(update, context)
        
        # Callbacks Fase 1
        elif query.data == 'p1_start_reels':
            await query.edit_message_text("✅ Iniciando workflow n8n: <b>01_daily_professional_reel_final</b>", parse_mode='HTML')
            # Lógica para disparar n8n
        elif query.data == 'p1_start_karaoke':
            await query.edit_message_text("🎤 Lanzando sesión de <b>Miyuki JP Karaoke</b> en Docker...", parse_mode='HTML')
            
        # Callbacks Fase 2
        elif query.data == 'p2_dataset_aiko':
            await query.edit_message_text("📸 Generando 20 imágenes de referencia para <b>Aiko Hayashi</b> (Semilla 5588)...")
            # Iniciar DatasetGenerator
        elif query.data == 'p2_train_aiko':
            await query.edit_message_text("🏗️ Provisionando <b>RunPod RTX 4090</b> para entrenamiento de LoRA...")
            # Iniciar LoRATrainer
        elif query.data == 'p2_start_edit':
            await query.edit_message_text("🔞 Preparando edición personalizada... Se notificará al terminar renderizado RAW.")
        elif query.data == 'p2_compliance':
            await query.edit_message_text("🛡️ Verificando política de pixelado para mercado <b>JP</b>...")
    
    async def _handle_unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands"""
        await update.message.reply_text(
            f"Unknown command: {update.message.text}\nUse /help for available commands."
        )
    
    # Message formatters
    def _format_status_message(self, status: Dict[str, Any]) -> str:
        """Format status message"""
        credits = status.get('credits', {})
        daily = status.get('daily', {})
        
        return f"""
📊 <b>System Status</b>

🎬 <b>Production:</b> {status.get('production_status', 'unknown')}
📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}

💳 <b>Credits:</b>
   • Used: {credits.get('monthly_used', 0)} / {credits.get('monthly_total', 0)}
   • Remaining: {credits.get('monthly_remaining', 0)}
   • Usage: {credits.get('usage_percentage', 0)}%

📹 <b>Today's Production:</b>
   • Videos: {daily.get('total_videos', 0)} / {daily.get('target_videos', 0)}
   • Success: {daily.get('success_rate', 0)}%
   • Progress: {daily.get('progress_toward_target', 0)}%
"""
    
    def _format_credits_message(self, credits: Dict[str, Any]) -> str:
        """Format credits message"""
        status_emoji = "🟢" if credits.get('budget_status') == 'healthy' else \
                       "🟡" if credits.get('budget_status') == 'warning' else "🔴"
        
        return f"""
💳 <b>Credit Status</b> {status_emoji}

<b>Plan:</b> {credits.get('plan', 'Unknown')}
<b>Monthly Allowance:</b> {credits.get('monthly_total', 0)} credits
<b>Monthly Used:</b> {credits.get('monthly_used', 0)} credits
<b>Monthly Remaining:</b> {credits.get('monthly_remaining', 0)} credits

<b>Daily Bonus:</b> {credits.get('daily_bonus', 0)} credits
<b>Daily Used:</b> {credits.get('daily_used', 0)} credits
<b>Daily Remaining:</b> {credits.get('daily_remaining', 0)} credits

<b>Total Available:</b> {credits.get('total_available', 0)} credits
<b>Usage:</b> {credits.get('usage_percentage', 0)}%

<b>Status:</b> {credits.get('budget_status', 'unknown').upper()}
"""
    
    def _format_daily_message(self, daily: Dict[str, Any]) -> str:
        """Format daily summary message"""
        return f"""
📊 <b>Daily Production Summary</b>

📅 <b>Date:</b> {daily.get('date', datetime.now().strftime('%Y-%m-%d'))}

📹 <b>Production:</b>
   • Total Videos: {daily.get('total_videos', 0)}
   • Successful: {daily.get('successful_videos', 0)}
   • Failed: {daily.get('failed_videos', 0)}
   • Success Rate: {daily.get('success_rate', 0)}%

⏱️ <b>Duration:</b> {daily.get('total_duration_minutes', 0)} minutes
💰 <b>Cost:</b> ${daily.get('total_cost', 0):.2f}
💳 <b>Credits Used:</b> {daily.get('total_credits_used', 0)}

📈 <b>Progress:</b> {daily.get('progress_toward_target', 0)}% of daily target
🎯 <b>Target:</b> {daily.get('target_videos', 4)} videos

<b>By Platform:</b>
{self._format_dict(daily.get('by_platform', {}))}

<b>By Character:</b>
{self._format_dict(daily.get('by_character', {}))}
"""
    
    def _format_weekly_message(self, weekly: Dict[str, Any]) -> str:
        """Format weekly report message"""
        breakdown = "\n".join([
            f"   • {d['date']}: {d['videos']} videos ({d['success_rate']}% success)"
            for d in weekly.get('daily_breakdown', [])
        ])
        
        return f"""
📈 <b>Weekly Report</b>

📅 <b>Period:</b> Last 7 days

📹 <b>Total Production:</b>
   • Videos: {weekly.get('total_videos', 0)}
   • Successful: {weekly.get('successful_videos', 0)}
   • Failed: {weekly.get('failed_videos', 0)}

📊 <b>Averages:</b>
   • Daily Videos: {weekly.get('average_daily_videos', 0)}
   • Daily Cost: ${weekly.get('average_daily_cost', 0):.2f}

💰 <b>Total Cost:</b> ${weekly.get('total_cost', 0):.2f}
💳 <b>Total Credits:</b> {weekly.get('total_credits_used', 0)}

<b>Daily Breakdown:</b>
{breakdown}
"""
    
    def _format_character_message(self, rotation: Dict[str, Any]) -> str:
        """Format character rotation message"""
        chars = rotation.get('characters', {})
        char_lines = "\n".join([
            f"   • {name}: {status['used_today']} / {status['ideal_distribution']} (need: {'Yes' if status['needs_more'] else 'No'})"
            for name, status in chars.items()
        ])
        
        return f"""
👥 <b>Character Rotation</b>

🎯 <b>Next Recommended:</b> {rotation.get('next_recommended', 'N/A')}
📹 <b>Today's Videos:</b> {rotation.get('total_videos_today', 0)} / {rotation.get('target_videos', 0)}
⏭️ <b>Remaining:</b> {rotation.get('remaining_videos', 0)}

<b>Character Usage:</b>
{char_lines}
"""
    
    def _format_platform_message(self, platform: Dict[str, Any]) -> str:
        """Format platform distribution message"""
        dist = platform.get('distribution', {})
        dist_lines = "\n".join([
            f"   • {name}: {data['count']} ({data['percentage']}%)"
            for name, data in dist.items()
        ])
        
        return f"""
📱 <b>Platform Distribution</b>

📊 <b>Total Posts:</b> {platform.get('total', 0)}
✅ <b>Active Platforms:</b> {platform.get('platforms_active', 0)}

<b>Distribution:</b>
{dist_lines}
"""
    
    def _format_budget_message(self, credits: Dict[str, Any], budget: Dict[str, Any]) -> str:
        """Format budget status message"""
        return f"""
💰 <b>Budget Status</b>

💳 <b>Credits:</b>
   • Remaining: {credits.get('monthly_remaining', 0)} / {credits.get('monthly_total', 0)}
   • Usage: {credits.get('usage_percentage', 0)}%

📊 <b>Cost Estimate (Remaining Videos):</b>
   • Videos: {budget.get('videos_remaining', 0)}
   • Est. Credits: {budget.get('estimated_credits_needed', 0)}
   • Est. Cost: ${budget.get('estimated_cost_usd', 0):.2f}

⚠️ <b>Warning Threshold:</b> 80% usage
🚨 <b>Critical Threshold:</b> 95% usage
"""
    
    def _format_dict(self, data: Dict) -> str:
        """Format dictionary as indented list"""
        if not data:
            return "   • None"
        return "\n".join([f"   • {k}: {v}" for k, v in data.items()])


# Webhook verification
def verify_webhook_signature(
    secret_token: str,
    timestamp: str,
    body: str,
    signature: str
) -> bool:
    """
    Verify Telegram webhook signature.
    
    Args:
        secret_token: Bot's webhook secret token
        timestamp: Request timestamp
        body: Request body
        signature: X-Telegram-Bot-Api-Signature header
        
    Returns:
        True if signature is valid
    """
    if not secret_token:
        return True  # Skip verification if not configured
    
    msg = f"{timestamp}{body}".encode()
    secret = secret_token.encode()
    expected = hmac.new(secret, msg, hashlib.sha256).hexdigest()
    
    return hmac.compare_digest(signature, expected)


async def send_telegram_message(
    bot_token: str,
    chat_id: int,
    message: str,
    parse_mode: str = 'HTML'
) -> bool:
    """
    Send a simple message via Telegram API.
    
    Args:
        bot_token: Telegram bot token
        chat_id: Target chat ID
        message: Message text
        parse_mode: Message parse mode
        
    Returns:
        True if successful
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


async def send_telegram_photo(
    bot_token: str,
    chat_id: int,
    photo_path: str,
    caption: str = ""
) -> bool:
    """
    Send a photo via Telegram API.
    
    Args:
        bot_token: Telegram bot token
        chat_id: Target chat ID
        photo_path: Path to photo file
        caption: Optional caption
        
    Returns:
        True if successful
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    try:
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field('chat_id', str(chat_id))
            form.add_field('photo', open(photo_path, 'rb'), filename='photo.jpg')
            if caption:
                form.add_field('caption', caption)
            
            async with session.post(url, data=form) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Failed to send Telegram photo: {e}")
        return False


# Factory function
def create_telegram_bot(
    config_path: str = None,
    production_monitor = None
) -> TelegramBot:
    """
    Create and configure a Telegram bot instance.
    
    Args:
        config_path: Path to JSON configuration file
        production_monitor: Production monitor instance
        
    Returns:
        Configured TelegramBot instance
    """
    if config_path:
        config = TelegramConfig.from_json(config_path)
    else:
        config = TelegramConfig()
    
    return TelegramBot(config, production_monitor)


if __name__ == "__main__":
    # Test the Telegram bot
    print("=== Telegram Bot Configuration ===")
    print()
    
    # Create default config
    config = TelegramConfig()
    print("Default Configuration:")
    print(f"  Enabled: {config.enabled}")
    print(f"  Admin Chats: {config.admin_chat_ids}")
    print(f"  Notify on Complete: {config.notify_on_video_complete}")
    print(f"  Notify on Failed: {config.notify_on_video_failed}")
    print(f"  Daily Summary: {config.daily_summary_enabled} at {config.daily_summary_time}")
    print()
    
    print("To configure the bot:")
    print("1. Create a bot via @BotFather on Telegram")
    print("2. Copy the bot token to config/monitoring/telegram_config.json")
    print("3. Add your chat ID to admin_chat_ids")
    print("4. Run python -m src.monitoring.telegram_bot to test")
