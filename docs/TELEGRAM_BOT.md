# Telegram Bot Integration Guide

This document provides comprehensive documentation for the Telegram Bot integration in the ELITE 8 AI Video Generation System.

## Overview

The Telegram Bot provides real-time notifications and an interactive command interface for monitoring and controlling the production system. Administrators can receive instant alerts, query system status, and perform basic operations directly from Telegram.

## Features

### Notifications

The bot sends notifications for the following events:

- **Video Production**: Notifications when video generation starts, completes, or fails
- **Uploads**: Notifications for social media uploads (success/failure)
- **Credit Alerts**: Warnings when credits fall below thresholds (80% warning, 95% critical)
- **Budget Alerts**: Notifications when budget usage exceeds limits
- **System Errors**: Critical system errors and failures
- **Daily/Weekly Reports**: Automated summary reports at configured times

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Display welcome message and command list |
| `/help` | Show all available commands |
| `/status` | Get full system status overview |
| `/credits` | View current A2E API credit status |
| `/daily` | Get today's production summary |
| `/weekly` | Get weekly production report |
| `/character` | View character rotation status |
| `/platform` | View platform distribution statistics |
| `/budget` | View current budget status |
| `/schedule` | View scheduler job status |
| `/restart` | Restart production system |
| `/pause` | Pause all production |
| `/resume` | Resume production |

## Installation

### Prerequisites

1. A Telegram account
2. Access to @BotFather on Telegram
3. Python 3.8+ with required dependencies

### Setup Steps

#### 1. Create a Telegram Bot

1. Open Telegram and search for @BotFather
2. Send `/newbot` to create a new bot
3. Follow the prompts to set a name and username
4. Copy the HTTP API token provided (save this securely)

#### 2. Configure the Bot

Edit the configuration file:

```bash
nano config/monitoring/telegram_config.json
```

Update the following values:

```json
{
    "enabled": true,
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "admin_chat_ids": [123456789],
    "monitoring_chat_ids": [123456789],
    "notify_on_video_complete": true,
    "notify_on_video_failed": true,
    "notify_on_upload_complete": true,
    "notify_on_upload_failed": true,
    "notify_on_credit_warning": true,
    "daily_summary_enabled": true,
    "daily_summary_time": "20:00"
}
```

#### 3. Get Your Chat ID

1. Start a chat with your bot
2. Send any message to the bot
3. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find the `chat.id` value in the response
5. Add this ID to both `admin_chat_ids` and `monitoring_chat_ids`

#### 4. Install Dependencies

```bash
pip install python-telegram-bot aiohttp
```

#### 5. Test the Bot

```bash
python -m src.monitoring.telegram_bot
```

## Usage

### Basic Usage

#### Starting the Bot

```python
from src.monitoring import create_telegram_bot, TelegramConfig

# Load configuration
config = TelegramConfig.from_json("config/monitoring/telegram_config.json")

# Create and start bot
bot = create_telegram_bot(config)
await bot.initialize()
await bot.start()
```

#### Sending Notifications

```python
from src.monitoring import TelegramBot, NotificationType

# Queue a notification
bot.queue_notification(
    notification_type=NotificationType.VIDEO_COMPLETED,
    title="Video Completed",
    message="Karaoke video for Yuki-chan completed successfully",
    details="Duration: 45s | Credits: 50 | Cost: $0.50"
)
```

#### Integrating with Production Monitor

```python
from src.monitoring import ProductionMonitor, create_telegram_bot

# Create production monitor
monitor = ProductionMonitor()

# Create bot with monitor reference
bot = create_telegram_bot(
    config_path="config/monitoring/telegram_config.json",
    production_monitor=monitor
)

# Start both
await monitor.initialize()
await bot.initialize()
await bot.start()
```

### Advanced Configuration

#### Webhook Mode

For production environments, webhook mode is recommended:

```json
{
    "webhook_url": "https://your-domain.com/webhook",
    "webhook_secret": "your_webhook_secret"
}
```

Set up the webhook endpoint:

```python
from telegram import Update
from telegram.ext import ContextTypes
import json

async def webhook_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Process update
    pass

# In your web server
@app.post("/webhook")
async def telegram_webhook(request: Request):
    # Verify signature
    secret = config.webhook_secret
    # Process update
    return {"ok": True}
```

#### Multiple Chat IDs

Configure multiple chat IDs for different notification purposes:

```json
{
    "admin_chat_ids": [123456789, 987654321],
    "monitoring_chat_ids": [-1001234567890]
}
```

- `admin_chat_ids`: Users who can send commands
- `monitoring_chat_ids`: Channels/groups for notifications only

#### Custom Notification Settings

Fine-tune which notifications to send:

```json
{
    "notify_on_video_complete": true,
    "notify_on_video_failed": true,
    "notify_on_upload_complete": true,
    "notify_on_upload_failed": true,
    "notify_on_credit_warning": true,
    "daily_summary_enabled": true,
    "daily_summary_time": "20:00"
}
```

### Command Examples

#### Status Command Response

```
📊 System Status

🎬 Production: active
📅 Date: 2026-01-22

💳 Credits:
   • Used: 450 / 1800
   • Remaining: 1350
   • Usage: 25.0%

📹 Today's Production:
   • Videos: 2 / 4
   • Success: 100%
   • Progress: 50%
```

#### Credits Command Response

```
💳 Credit Status 🟢

Plan: pro
Monthly Allowance: 1800 credits
Monthly Used: 450 credits
Monthly Remaining: 1350 credits

Daily Bonus: 60 credits
Daily Used: 15 credits
Daily Remaining: 45 credits

Total Available: 1405 credits
Usage: 25.0%

Status: HEALTHY
```

#### Daily Summary Response

```
📊 Daily Production Summary

📅 Date: 2026-01-22

📹 Production:
   • Total Videos: 2
   • Successful: 2
   • Failed: 0
   • Success Rate: 100%

⏱️ Duration: 75 minutes
💰 Cost: $1.00
💳 Credits Used: 100

📈 Progress: 50% of daily target
🎯 Target: 4 videos

By Platform:
   • tiktok: 1
   • instagram: 1

By Character:
   • yuki-chan: 1
   • aurelia-viral: 1
```

## API Reference

### TelegramConfig

Configuration class for the Telegram bot.

```python
@dataclass
class TelegramConfig:
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
```

### TelegramBot

Main bot class for handling notifications and commands.

```python
class TelegramBot:
    def __init__(self, config: TelegramConfig = None, production_monitor=None)
    
    async def initialize(self)
    async def start(self)
    async def stop(self)
    def queue_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        details: str = "",
        chat_ids: List[int] = None
    )
```

### NotificationType

Enum for different notification types:

```python
class NotificationType(Enum):
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
```

## Troubleshooting

### Bot Not Responding

1. Check bot token validity
2. Verify chat ID is correct
3. Ensure bot is started with `await bot.start()`

```bash
# Test bot token
curl https://api.telegram.org/bot<TOKEN>/getMe
```

### No Notifications Received

1. Check `monitoring_chat_ids` is configured
2. Verify notifications are enabled in config
3. Check bot has permission to send messages

```bash
# Test sending message
curl -X POST \
  https://api.telegram.org/bot<TOKEN>/sendMessage \
  -d chat_id=<CHAT_ID> \
  -d text="Test message"
```

### Webhook Issues

1. Verify webhook URL is accessible (HTTPS required)
2. Check webhook secret matches
3. Ensure SSL certificate is valid

```python
# Set webhook
await application.bot.set_webhook(
    url="https://your-domain.com/webhook",
    secret_token="your_secret"
)
```

## Security Considerations

1. **Token Security**: Never commit bot tokens to version control
2. **Chat ID Protection**: Only add trusted chat IDs
3. **Webhook Security**: Always verify webhook signatures
4. **Rate Limiting**: Telegram has rate limits; queue notifications

Example environment variable usage:

```bash
# .env file
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_WEBHOOK_SECRET=your_secret_here
```

```python
import os

config = TelegramConfig(
    bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
    webhook_secret=os.getenv("TELEGRAM_WEBHOOK_SECRET")
)
```

## Production Deployment

### Using systemd

Create a service file:

```ini
# /etc/systemd/system/elite8-telegram.service
[Unit]
Description=ELITE 8 Telegram Bot
After=network.target

[Service]
Type=simple
User=elite8
WorkingDirectory=/opt/elite8
ExecStart=/opt/elite8/venv/bin/python -m src.monitoring.telegram_bot
Restart=on-failure
Environment=TELEGRAM_BOT_TOKEN=your_token

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable elite8-telegram
sudo systemctl start elite8-telegram
```

### Using Docker

Add to your docker-compose.yml:

```yaml
services:
  telegram-bot:
    build: .
    command: python -m src.monitoring.telegram_bot
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    volumes:
      - ./data:/app/data
```

## Integration with Alert System

The Telegram bot can receive alerts from the AlertSystem:

```python
from src.monitoring import AlertSystem, create_telegram_bot

# Create alert system
alert_system = create_alert_system("config/monitoring/alert_config.json")

# Create bot
bot = create_telegram_bot("config/monitoring/telegram_config.json")

# Register notification callback
def handle_alert(alert):
    bot.queue_notification(
        notification_type=NotificationType.SYSTEM_ERROR,
        title=f"Alert: {alert.title}",
        message=alert.message,
        details=f"Severity: {alert.severity}"
    )

alert_system.add_notification_callback(handle_alert)

# Start both
await alert_system.start()
await bot.start()
```

## Best Practices

1. **Use Webhook Mode**: More efficient for production
2. **Enable Rate Limiting**: Prevent message flooding
3. **Regular Health Checks**: Monitor bot status
4. **Log All Commands**: For audit trail
5. **Test Regularly**: Send test notifications weekly
6. **Backup Configuration**: Keep config files version controlled
7. **Use Environment Variables**: Never hardcode tokens

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-22 | Initial release |

## Support

For issues and questions:
- Check the troubleshooting section
- Review logs in `logs/telegram.log`
- Open an issue on GitHub
