import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.monitoring.telegram_bot import TelegramBot, TelegramConfig, NotificationType

async def test_telegram_alert():
    """Script para probar las alertas de Telegram."""
    # Cargar variables de entorno
    load_dotenv()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ ERROR: Debes configurar TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en tu archivo .env")
        return

    print(f"🚀 Iniciando prueba de Telegram para el chat: {chat_id}")
    
    config = TelegramConfig(
        bot_token=token,
        admin_chat_ids=[int(chat_id)],
        monitoring_chat_ids=[int(chat_id)],
        enabled=True
    )
    
    bot = TelegramBot(config=config)
    
    try:
        await bot.initialize()
        await bot.start()
        
        print("📤 Enviando alerta de prueba...")
        
        bot.queue_notification(
            notification_type=NotificationType.SYSTEM_ERROR,
            title="SISTEMA WAIFUGEN ONLINE",
            message="El sistema de monitoreo de Telegram se ha configurado correctamente. ¡Recibirás alertas de ventas y producción aquí!",
            details="Status: Active\nPhase: 2\nMode: Expert"
        )
        
        # Dar tiempo a que se procese la cola
        await asyncio.sleep(5)
        
        print("✅ Alerta enviada. Revisa tu móvil.")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(test_telegram_alert())
