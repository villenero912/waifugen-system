#!/usr/bin/env python3
"""
Elite 8 AI Video Generation System - Main Entry Point

This is the main entry point for the ELITE 8 AI Video Generation System,
providing unified access to all system components for both Phase 1 and Phase 2.

Phase 1: Core video generation and social media automation
Phase 2: International expansion, conversion funnels, and subscriber management

Usage:
    python main.py --mode full        # Run full system
    python main.py --mode phase1      # Phase 1 only (social media)
    python main.py --mode phase2      # Phase 2 only (marketing/funnel)
    python main.py --mode generate    # Generate videos only
    python main.py --mode schedule    # Run scheduler only
    python main.py --mode monitor     # Run monitoring only
    python main.py --mode report      # Generate report

Version: 2.0.0
Created: 2026-01-22
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import (
    __version__,
    __phase__,
    get_db,
    get_scheduler,
    get_content_scheduler,
    SocialMediaManager,
    ProxyManager,
    ProductionMonitor,
    TelegramBot,
    MetricsCollector,
    AlertSystem,
    Dashboard,
    ConversionFunnel,
    FunnelStage,
    RegionalManager,
    create_conversion_funnel,
    create_regional_manager,
    create_production_monitor,
    create_telegram_bot,
    create_metrics_collector,
    create_alert_system,
    create_dashboard
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Elite8System:
    """
    Main system controller for ELITE 8 AI Video Generation System.
    
    Provides unified management of:
    - Video generation (A2E API)
    - Social media posting (TikTok, Instagram, YouTube)
    - Scheduling and automation
    - Monitoring and alerts
    - Phase 2 marketing and expansion
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the ELITE 8 system.
        
        Args:
            config_path: Path to main configuration file
        """
        self.config_path = config_path or os.getenv(
            "ELITE8_CONFIG_PATH",
            str(Path(__file__).resolve().parent / "config")
        )
        
        self.config = self._load_config()
        
        # Core components - Phase 1
        self.db = None
        self.scheduler = None
        self.social_manager = None
        self.proxy_manager = None
        
        # Monitoring components
        self.production_monitor = None
        self.telegram_bot = None
        self.metrics_collector = None
        self.alert_system = None
        self.dashboard = None
        
        # Phase 2 components
        self.conversion_funnel = None
        self.regional_manager = None
        
        # System state
        self.running = False
        self.start_time = None
        
        logger.info(f"ELITE 8 System initialized (Phase {__phase__})")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load main configuration"""
        config_file = Path(self.config_path) / "elite8_config.json"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "phase": "2",
            "components": {
                "database": {"enabled": True},
                "scheduler": {"enabled": True},
                "social": {"enabled": True},
                "proxy": {"enabled": True},
                "monitoring": {"enabled": True},
                "telegram": {"enabled": False},
                "metrics": {"enabled": True},
                "alerts": {"enabled": True},
                "dashboard": {"enabled": True},
                "funnel": {"enabled": True},
                "regional": {"enabled": True}
            },
            "phase1": {
                "daily_video_target": 4,
                "platforms": ["tiktok", "instagram", "youtube"],
                "characters": ["yuki-chan", "aurelia-viral", "haruka-chan"]
            },
            "phase2": {
                "enabled": True,
                "target_regions": ["US", "JP", "BR", "DE", "GB"],
                "monthly_budget": 1000.0
            }
        }
    
    async def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing ELITE 8 System components...")
        
        # Initialize database
        if self.config.get("components", {}).get("database", {}).get("enabled"):
            self.db = get_db()
            logger.info("✓ Database initialized")
        
        # Initialize scheduler
        if self.config.get("components", {}).get("scheduler", {}).get("enabled"):
            self.scheduler = get_scheduler(self.db)
            logger.info("✓ Scheduler initialized")
        
        # Initialize social media manager
        if self.config.get("components", {}).get("social", {}).get("enabled"):
            self.social_manager = SocialMediaManager()
            logger.info("✓ Social Media Manager initialized")
        
        # Initialize proxy manager
        if self.config.get("components", {}).get("proxy", {}).get("enabled"):
            self.proxy_manager = ProxyManager()
            await self.proxy_manager.initialize()
            logger.info("✓ Proxy Manager initialized")
        
        # Initialize production monitor
        if self.config.get("components", {}).get("monitoring", {}).get("enabled"):
            self.production_monitor = create_production_monitor()
            logger.info("✓ Production Monitor initialized")
        
        # Initialize Telegram bot
        if self.config.get("components", {}).get("telegram", {}).get("enabled"):
            self.telegram_bot = create_telegram_bot(
                production_monitor=self.production_monitor
            )
            await self.telegram_bot.initialize()
            logger.info("✓ Telegram Bot initialized")
        
        # Initialize metrics collector
        if self.config.get("components", {}).get("metrics", {}).get("enabled"):
            self.metrics_collector = create_metrics_collector()
            await self.metrics_collector.start()
            logger.info("✓ Metrics Collector started")
        
        # Initialize alert system
        if self.config.get("components", {}).get("alerts", {}).get("enabled"):
            self.alert_system = create_alert_system()
            
            # Register Telegram notification for alerts
            if self.telegram_bot:
                def send_alert_notification(alert):
                    self.telegram_bot.queue_notification(
                        notification_type=NotificationType.SYSTEM_ERROR,
                        title=f"Alert: {alert.title}",
                        message=alert.message
                    )
                
                self.alert_system.add_notification_callback(send_alert_notification)
            
            await self.alert_system.start()
            logger.info("✓ Alert System started")
        
        # Initialize dashboard
        if self.config.get("components", {}).get("dashboard", {}).get("enabled"):
            self.dashboard = create_dashboard()
            logger.info("✓ Dashboard initialized")
        
        # Initialize conversion funnel (Phase 2)
        if self.config.get("phase2", {}).get("enabled"):
            self.conversion_funnel = create_conversion_funnel()
            logger.info("✓ Conversion Funnel initialized (Phase 2)")
        
        # Initialize regional manager (Phase 2)
        if self.config.get("components", {}).get("regional", {}).get("enabled"):
            self.regional_manager = create_regional_manager()
            logger.info("✓ Regional Manager initialized (Phase 2)")
        
        logger.info("All components initialized successfully")
    
    async def start(self):
        """Start the system"""
        if self.running:
            logger.warning("System is already running")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("Starting ELITE 8 System...")
        
        # Start Telegram bot
        if self.telegram_bot:
            await self.telegram_bot.start()
        
        # Start scheduler
        if self.scheduler:
            await self.scheduler.start()
        
        logger.info(f"ELITE 8 System started (Phase {__phase__})")
    
    async def stop(self):
        """Stop the system gracefully"""
        if not self.running:
            return
        
        logger.info("Stopping ELITE 8 System...")
        
 # Stop scheduler
        if self.scheduler:
            await self.scheduler.stop()
        
        # Stop Telegram bot
        if self.telegram_bot:
            await self.telegram_bot.stop()
        
        # Stop metrics collector
        if self.metrics_collector:
            await self.metrics_collector.stop()
        
        # Stop alert system
        if self.alert_system:
            await self.alert_system.stop()
        
        # Close database
        if self.db:
            self.db.close()
        
        self.running = False
        
        uptime = datetime.now() - self.start_time
        logger.info(f"ELITE 8 System stopped. Uptime: {uptime}")
    
    async def generate_video(
        self,
        character_id: str,
        prompt: str,
        duration_seconds: int = 30,
        platform: str = "tiktok"
    ) -> Dict[str, Any]:
        """
        Generate a video using A2E API.
        
        Args:
            character_id: Character to use
            prompt: Generation prompt
            duration_seconds: Video duration
            platform: Target platform
            
        Returns:
            Dictionary with job details
        """
        # Record production
        if self.production_monitor:
            stats = self.production_monitor.record_production(
                character_id=character_id,
                content_type="karaoke",
                platform=platform,
                duration_seconds=duration_seconds,
                credits_consumed=duration_seconds * 1.0,  # Estimate
                cost_estimate=duration_seconds * 0.01,   # Estimate
                status="pending"
            )
            
            job_id = stats.production_id
        else:
            import uuid
            job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"Video generation queued: {job_id} for {character_id}")
        
        # In a real implementation, this would call the A2E API
        return {
            "job_id": job_id,
            "character_id": character_id,
            "prompt": prompt,
            "duration": duration_seconds,
            "platform": platform,
            "status": "queued",
            "created_at": datetime.now().isoformat()
        }
    
    async def post_to_social(
        self,
        video_path: str,
        platform: str,
        caption: str,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Post content to social media.
        
        Args:
            video_path: Path to video file
            platform: Target platform
            caption: Post caption
            tags: Hashtags
            
        Returns:
            Dictionary with post result
        """
        if not self.social_manager:
            logger.error("Social Media Manager not initialized")
            return {"success": False, "error": "Manager not initialized"}
        
        result = await self.social_manager.post_video(
            platform=platform,
            video_path=video_path,
            caption=caption,
            tags=tags or []
        )
        
        logger.info(f"Post created: {platform} - {result.get('post_id', 'N/A')}")
        
        return result
    
    async def run_phase1(self):
        """Run Phase 1 operations (social media automation)"""
        logger.info("Running Phase 1 operations...")
        
        phase1_config = self.config.get("phase1", {})
        characters = phase1_config.get("characters", ["yuki-chan"])
        platforms = phase1_config.get("platforms", ["tiktok", "instagram", "youtube"])
        target_videos = phase1_config.get("daily_video_target", 4)
        
        for i in range(target_videos):
            character_id = characters[i % len(characters)]
            platform = platforms[i % len(platforms)]
            
            # Generate video
            await self.generate_video(
                character_id=character_id,
                prompt=f"Generate karaoke content for {character_id}",
                platform=platform
            )
        
        logger.info(f"Phase 1 operations completed: {target_videos} videos queued")
    
    async def run_phase2(self):
        """Run Phase 2 operations (marketing and expansion)"""
        logger.info("Running Phase 2 operations...")
        
        if not self.conversion_funnel:
            logger.warning("Conversion Funnel not initialized")
            return
        
        # Get funnel metrics
        metrics = self.conversion_funnel.get_funnel_metrics()
        logger.info(f"Funnel metrics: {metrics}")
        
        # Get regional report
        if self.regional_manager:
            regional_report = self.regional_manager.get_regional_report()
            logger.info(f"Regional report generated")
            
            # Get content calendar for each target region
            for region in self.config.get("phase2", {}).get("target_regions", []):
                calendar = self.regional_manager.get_content_calendar(region, days=7)
                logger.info(f"Content calendar for {region}: {len(calendar)} items")
        
        logger.info("Phase 2 operations completed")
    
    async def generate_report(self, report_type: str = "full") -> Dict[str, Any]:
        """
        Generate a comprehensive system report.
        
        Args:
            report_type: Type of report (full, daily, weekly, monthly)
            
        Returns:
            Report dictionary
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "system_version": __version__,
            "phase": __phase__,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }
        
        # Production stats
        if self.production_monitor:
            report["production"] = self.production_monitor.get_full_status()
        
        # Scheduler status
        if self.scheduler:
            report["scheduler"] = self.scheduler.get_scheduler_status()
        
        # Funnel metrics (Phase 2)
        if self.conversion_funnel:
            report["funnel"] = self.conversion_funnel.get_funnel_metrics()
        
        # Regional report (Phase 2)
        if self.regional_manager:
            report["regional"] = self.regional_manager.get_regional_report()
        
        # Save report
        report_path = Path("reports") / f"elite8_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Report generated: {report_path}")
        
        return report
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "running": self.running,
            "version": __version__,
            "phase": __phase__,
            "components": {}
        }
        
        # Check each component
        components = [
            ("database", self.db),
            ("scheduler", self.scheduler),
            ("social_manager", self.social_manager),
            ("proxy_manager", self.proxy_manager),
            ("production_monitor", self.production_monitor),
            ("telegram_bot", self.telegram_bot),
            ("metrics_collector", self.metrics_collector),
            ("alert_system", self.alert_system),
            ("conversion_funnel", self.conversion_funnel),
            ("regional_manager", self.regional_manager)
        ]
        
        for name, component in components:
            status["components"][name] = {
                "initialized": component is not None,
                "running": getattr(component, 'running', False) if component else None
            }
        
        return status


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="ELITE 8 AI Video Generation System"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "phase1", "phase2", "generate", "schedule", "monitor", "report"],
        default="full",
        help="System mode to run"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration directory"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and initialize system
    system = Elite8System(config_path=args.config)
    
    try:
        await system.initialize()
        await system.start()
        
        # Run based on mode
        if args.mode == "full":
            await system.run_phase1()
            await system.run_phase2()
        elif args.mode == "phase1":
            await system.run_phase1()
        elif args.mode == "phase2":
            await system.run_phase2()
        elif args.mode == "generate":
            await system.run_phase1()
        elif args.mode == "schedule":
            # Just run scheduler
            while True:
                await asyncio.sleep(60)
        elif args.mode == "monitor":
            await system.generate_report("full")
        elif args.mode == "report":
            report = await system.generate_report("full")
            print(json.dumps(report, indent=2, default=str))
        
        # Keep running for interactive modes
        if args.mode in ["full", "phase1", "phase2"]:
            logger.info("System running. Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(60)
                
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
