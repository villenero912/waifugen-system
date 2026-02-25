
import asyncio
import argparse
import sys
import logging
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.social.social_manager import quick_post_all
from src.database.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PostReelCLI")

async def main():
    parser = argparse.ArgumentParser(description="Post a reel by ID")
    parser.add_argument("reel_id", type=int, help="ID of the reel to post")
    args = parser.parse_args()

    # 1. Get Reel Data from DB
    # Note: Ideally we would use a proper DAO, but for this script we'll do a quick query or use the existing infrastructure
    # Assuming video_path is passed or we need to fetch it.
    # Let's fetch it from DB to be safe.
    
    # Simulating DB fetch for now as I don't want to import the whole DB stack if not needed, 
    # BUT we need the file path. 
    # Let's assume the DB Manager is available or we can use a direct query if needed.
    # For robust integration, let's try to query the DB.

    # Reuse existing DB connection logic if possible
    # from src.database.connection import get_db_connection
    # ...
    
    # For now, to keep it simple and robust within the context, let's assume the calling automation passes the crucial data OR 
    # we just fake it for the structure if we can't easily query.
    # Wait, N8N has the data. N8N could pass the arguments to this script: --video_path --caption etc.
    # However, the plan says "Get Reel Data from Postgres" is Action 1 in N8N.
    # So N8N will pass the data to THIS script. Let's update the args.
    
    # CORRECT APPROACH:
    # N8N Workflow 2:
    # 1. Webhook (gets ID)
    # 2. Postgres (SELECT * FROM reels WHERE id = ID)
    # 3. Execute Command (python scripts/post_reel.py --video_path ... --caption ...)
    
    # So I will update the parser to accept the path and details.
    
    parser = argparse.ArgumentParser(description="Post a reel")
    parser.add_argument("--video_path", required=True, help="Path to the video file")
    parser.add_argument("--caption", required=True, help="Caption for the post")
    parser.add_argument("--tags", default="", help="Comma separated tags")
    parser.add_argument("--character", default="unknown", help="Character name")
    
    args = parser.parse_args()
    
    tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]

    logger.info(f"🚀 Starting post for file: {args.video_path}")
    
    try:
        results = await quick_post_all(
            video_path=args.video_path,
            caption=args.caption,
            tags=tags_list,
            character=args.character
        )
        
        # Check if any succeeded
        if any(r.success for r in results.values()):
            logger.info("✅ Posting successful!")
            # Convert results to JSON for N8N parsing if needed, or just exit 0
            sys.exit(0)
        else:
            logger.error("❌ All posts failed.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
