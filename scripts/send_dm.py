
import os
import sys
import argparse
import logging
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.messaging.phase2_dm_automation import DMAutomationManager, DatabaseConnection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Execute a specific DM send action')
    parser.add_argument('--id', required=True, help='Message ID of the DM to send')
    parser.add_argument('--force', action='store_true', help='Force send even if not scheduled/pending')
    
    args = parser.parse_args()
    
    # Load env
    load_dotenv()
    
    # DB Connection
    db_config = {
        "host": os.getenv("DB_HOST", "postgres"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "waifugen"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres")
    }
    
    try:
        db = DatabaseConnection(db_config)
        manager = DMAutomationManager(db)
        
        logger.info(f"Attempting to send DM with ID: {args.id}")
        
        # In a real scenario, we might want to fetch subscriber data here to refine the personalization
        # For now, we rely on the manager's interpolation
        
        sent_message = manager.send_message(args.id)
        
        if sent_message and sent_message.status == 'sent':
            print(json.dumps({
                "success": True,
                "message_id": sent_message.message_id,
                "status": "sent",
                "sent_at": str(sent_message.sent_at)
            }))
        else:
            print(json.dumps({
                "success": False,
                "error": "Message status update failed or message not found"
            }))
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to send DM: {e}")
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
