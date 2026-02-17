#!/usr/bin/env python3
"""
DM Execution Script for WaifuGen Phase 2
Sends approved DMs to followers on Instagram/Twitter with IPRoyal proxy rotation
"""

import os
import sys
import argparse
import logging
import time
import random
from datetime import datetime
from typing import Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'waifugen'),
    'user': os.getenv('POSTGRES_USER', 'waifugen'),
    'password': os.getenv('POSTGRES_PASSWORD', '')
}

# IPRoyal Proxy configuration
IPROYAL_CONFIG = {
    'host': os.getenv('IPROYAL_HOST', 'geo.iproyal.com'),
    'port': int(os.getenv('IPROYAL_PORT', 12321)),
    'username': os.getenv('IPROYAL_USERNAME', ''),
    'password': os.getenv('IPROYAL_PASSWORD', '')
}


class DMSender:
    """Handles sending DMs to social media platforms"""
    
    def __init__(self, message_id: str, force: bool = False):
        self.message_id = message_id
        self.force = force
        self.db_conn = None
        self.driver = None
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def get_dm_data(self) -> Optional[Dict]:
        """Retrieve DM data from database"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM dm_messages 
                    WHERE message_id = %s
                """, (self.message_id,))
                dm = cursor.fetchone()
                
                if not dm:
                    logger.error(f"DM with ID {self.message_id} not found")
                    return None
                
                if dm['status'] != 'approved' and not self.force:
                    logger.error(f"DM status is '{dm['status']}', not 'approved'")
                    return None
                
                return dict(dm)
        except Exception as e:
            logger.error(f"Failed to retrieve DM data: {e}")
            raise
    
    def setup_proxy_driver(self, platform: str) -> webdriver.Chrome:
        """Setup Selenium WebDriver with IPRoyal proxy"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Configure proxy
        proxy_url = f"{IPROYAL_CONFIG['username']}:{IPROYAL_CONFIG['password']}@{IPROYAL_CONFIG['host']}:{IPROYAL_CONFIG['port']}"
        chrome_options.add_argument(f'--proxy-server=http://{proxy_url}')
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        driver = webdriver.Chrome(options=chrome_options)
        logger.info(f"WebDriver initialized with IPRoyal proxy for {platform}")
        return driver
    
    def send_instagram_dm(self, dm_data: Dict) -> bool:
        """Send DM via Instagram"""
        try:
            self.driver = self.setup_proxy_driver('instagram')
            
            # Login to Instagram (credentials from env)
            self.driver.get('https://www.instagram.com/accounts/login/')
            time.sleep(random.uniform(2, 4))
            
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'username'))
            )
            password_input = self.driver.find_element(By.NAME, 'password')
            
            # Get character-specific Instagram credentials
            ig_username = os.getenv(f'IG_USERNAME_{dm_data["character_id"]}', '')
            ig_password = os.getenv(f'IG_PASSWORD_{dm_data["character_id"]}', '')
            
            username_input.send_keys(ig_username)
            time.sleep(random.uniform(0.5, 1.5))
            password_input.send_keys(ig_password)
            time.sleep(random.uniform(0.5, 1.5))
            
            login_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
            login_button.click()
            time.sleep(random.uniform(3, 5))
            
            # Navigate to DMs
            self.driver.get('https://www.instagram.com/direct/inbox/')
            time.sleep(random.uniform(2, 4))
            
            # Search for recipient
            search_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@role="button" and contains(text(), "Send message")]'))
            )
            search_button.click()
            time.sleep(random.uniform(1, 2))
            
            search_input = self.driver.find_element(By.XPATH, '//input[@placeholder="Search..."]')
            search_input.send_keys(dm_data['subscriber_id'])
            time.sleep(random.uniform(2, 3))
            
            # Select recipient
            recipient = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f'//div[contains(text(), "{dm_data["subscriber_id"]}")]'))
            )
            recipient.click()
            time.sleep(random.uniform(1, 2))
            
            # Send message
            message_input = self.driver.find_element(By.XPATH, '//textarea[@placeholder="Message..."]')
            message_input.send_keys(dm_data['message_content'])
            time.sleep(random.uniform(0.5, 1.5))
            
            send_button = self.driver.find_element(By.XPATH, '//button[text()="Send"]')
            send_button.click()
            time.sleep(random.uniform(1, 2))
            
            logger.info(f"Instagram DM sent successfully to {dm_data['subscriber_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Instagram DM: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def send_twitter_dm(self, dm_data: Dict) -> bool:
        """Send DM via Twitter API v2"""
        try:
            # Twitter API v2 DM endpoint
            twitter_api_url = 'https://api.twitter.com/2/dm_conversations/with/{participant_id}/messages'
            
            # Get Twitter credentials
            bearer_token = os.getenv(f'TWITTER_BEARER_TOKEN_{dm_data["character_id"]}', '')
            
            headers = {
                'Authorization': f'Bearer {bearer_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'text': dm_data['message_content']
            }
            
            # Get participant ID (would need to be stored in DB)
            participant_id = dm_data.get('twitter_user_id', '')
            
            response = requests.post(
                twitter_api_url.format(participant_id=participant_id),
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                logger.info(f"Twitter DM sent successfully to {dm_data['subscriber_id']}")
                return True
            else:
                logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Twitter DM: {e}")
            return False
    
    def update_dm_status(self, status: str, sent_at: Optional[datetime] = None):
        """Update DM status in database"""
        try:
            with self.db_conn.cursor() as cursor:
                if sent_at:
                    cursor.execute("""
                        UPDATE dm_messages 
                        SET status = %s, sent_at = %s 
                        WHERE message_id = %s
                    """, (status, sent_at, self.message_id))
                else:
                    cursor.execute("""
                        UPDATE dm_messages 
                        SET status = %s 
                        WHERE message_id = %s
                    """, (status, self.message_id))
                self.db_conn.commit()
                logger.info(f"DM status updated to '{status}'")
        except Exception as e:
            logger.error(f"Failed to update DM status: {e}")
            raise
    
    def execute(self) -> bool:
        """Main execution flow"""
        try:
            # Connect to database
            self.connect_db()
            
            # Get DM data
            dm_data = self.get_dm_data()
            if not dm_data:
                return False
            
            # Send DM based on platform
            success = False
            if dm_data['platform'] == 'instagram':
                success = self.send_instagram_dm(dm_data)
            elif dm_data['platform'] == 'twitter':
                success = self.send_twitter_dm(dm_data)
            else:
                logger.error(f"Unsupported platform: {dm_data['platform']}")
                return False
            
            # Update status
            if success:
                self.update_dm_status('sent', datetime.now())
            else:
                self.update_dm_status('failed')
            
            return success
            
        except Exception as e:
            logger.error(f"DM execution failed: {e}")
            return False
        finally:
            if self.db_conn:
                self.db_conn.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Send approved DMs to social media followers')
    parser.add_argument('--id', required=True, help='DM message ID')
    parser.add_argument('--force', action='store_true', help='Force send even if not approved')
    
    args = parser.parse_args()
    
    sender = DMSender(args.id, args.force)
    success = sender.execute()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
