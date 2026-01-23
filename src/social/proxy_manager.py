"""
IPRoyal Proxy Manager for Elite 8 AI Video Generation System

This module provides comprehensive proxy management for IPRoyal residential proxies
with budget optimization and automatic failover to direct connection.

Budget: €15/month (~10GB of residential proxies)
Provider: https://iproyal.com
Discount Code: IPR50 ($1.75/GB instead of $7/GB)
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import aiohttp
from collections import deque
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ProxyCredentials:
    """Proxy authentication credentials"""
    username: str
    password: str
    host: str
    port: int
    protocol: str = "http"


@dataclass
class ProxyStats:
    """Proxy usage statistics"""
    total_bytes_used: int = 0
    daily_bytes_used: Dict[str, int] = field(default_factory=dict)
    monthly_bytes_used: Dict[str, int] = field(default_factory=dict)
    requests_made: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_request_time: Optional[datetime] = None
    proxy_failures: int = 0
    direct_fallback_count: int = 0


@dataclass
class BudgetAlert:
    """Budget threshold alert"""
    alert_type: str  # warning, critical, exhausted
    message: str
    bytes_remaining: int
    percentage_used: float
    timestamp: datetime


class ProxyManager:
    """
    Manages IPRoyal residential proxy connections with budget tracking
    and automatic failover to direct connection when proxy is unavailable
    or budget is exhausted.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the proxy manager
        
        Args:
            config_path: Path to IPRoyal configuration file
        """
        default_base = Path(__file__).resolve().parent.parent.parent
        self.config_path = config_path or os.getenv(
            "IPROYAL_CONFIG_PATH",
            str(default_base / "config" / "social" / "iproyal_config.json")
        )
        self.config = self._load_config()
        
        # Proxy credentials from environment
        self.enabled = os.getenv("IPROYAL_ENABLED", "true").lower() == "true"
        self.credentials = self._load_credentials()
        
        # Usage tracking
        self.stats = ProxyStats()
        self.budget_alerts: List[BudgetAlert] = []
        
        # Monthly budget tracking
        self.monthly_budget_gb = self.config.get("budget_allocation", {}).get(
            "monthly_gb_limit", 9
        )
        self.daily_budget_gb = self.config.get("budget_allocation", {}).get(
            "daily_gb_limit", 0.5
        )
        
        # Fail-safe settings
        self.fail_safe = self.config.get("budget_allocation", {}).get(
            "fail_safe_mode", {"enabled": True, "when_gb_remaining": 1}
        )
        self.use_direct_fallback = os.getenv(
            "USE_DIRECT_FALLBACK", "true"
        ).lower() == "true"
        
        # Connection pool
        self._session: Optional[aiohttp.ClientSession] = None
        self._connection_pool = deque()
        
        # Request queue for rate limiting
        self._request_queue: asyncio.Queue = asyncio.Queue()
        self._processing = False
        
        logger.info(f"IPRoyal Proxy Manager initialized (enabled: {self.enabled})")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load IPRoyal configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config not found at {self.config_path}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default IPRoyal configuration"""
        return {
            "provider": {
                "name": "IPRoyal",
                "discount_code": "IPR50",
                "pricing": {
                    "regular_price_per_gb": 7.00,
                    "discounted_price_per_gb": 1.75,
                    "monthly_budget_eur": 15.00,
                    "estimated_monthly_gb": 9
                }
            },
            "proxy_settings": {
                "enabled": True,
                "rotation_type": "rotating",
                "rotation_interval_seconds": 300,
                "sticky_sessions": {"enabled": False, "duration_minutes": 30},
                "protocols": ["http", "https", "socks5"],
                "connection": {
                    "timeout_seconds": 30,
                    "max_retries": 3,
                    "retry_delay_seconds": 5
                }
            },
            "budget_allocation": {
                "monthly_gb_limit": 9,
                "daily_gb_limit": 0.5,
                "per_platform_allocation": {
                    "tiktok": {"percentage": 40, "estimated_gb_per_month": 3.6},
                    "instagram": {"percentage": 35, "estimated_gb_per_month": 3.15},
                    "youtube": {"percentage": 25, "estimated_gb_per_month": 2.25}
                },
                "alert_threshold_percent": 80,
                "fail_safe_mode": {"enabled": True, "when_gb_remaining": 1}
            },
            "usage_optimization": {
                "compress_requests": True,
                "cache_enabled": True,
                "cache_ttl_seconds": 300,
                "batch_api_calls": True,
                "parallel_connections_limit": 5,
                "connection_pool_size": 10
            }
        }
    
    def _load_credentials(self) -> Optional[ProxyCredentials]:
        """Load proxy credentials from environment"""
        if not self.enabled:
            return None
        
        username = os.getenv("IPROYAL_USERNAME")
        password = os.getenv("IPROYAL_PASSWORD")
        host = os.getenv("IPROYAL_HOST", "geo.iproyal.com")
        port = int(os.getenv("IPROYAL_PORT", "12345"))
        protocol = os.getenv("IPROYAL_PROTOCOL", "http")
        
        if not username or not password:
            logger.warning("IPRoyal credentials not configured. Proxy will be disabled.")
            self.enabled = False
            return None
        
        return ProxyCredentials(
            username=username,
            password=password,
            host=host,
            port=port,
            protocol=protocol
        )
    
    def get_proxy_url(self) -> Optional[str]:
        """Get the full proxy URL for connections"""
        if not self.enabled or not self.credentials:
            return None
        
        safe_user = urllib.parse.quote(self.credentials.username)
        safe_pass = urllib.parse.quote(self.credentials.password)
        return f"{self.credentials.protocol}://{safe_user}:{safe_pass}@{self.credentials.host}:{self.credentials.port}"
    
    def get_proxy_dict(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration dictionary for aiohttp"""
        url = self.get_proxy_url()
        if not url:
            return None
        
        return {
            "http": url,
            "https": url
        }
    
    def can_use_proxy(self) -> Tuple[bool, str]:
        """
        Check if proxy can be used within budget
        
        Returns:
            Tuple of (can_use, reason)
        """
        if not self.enabled:
            return False, "Proxy is disabled"
        
        if not self.credentials:
            return False, "No credentials configured"
        
        bytes_remaining = self.get_bytes_remaining()
        
        if bytes_remaining <= 0:
            self._trigger_alert(
                "exhausted",
                "Proxy budget exhausted. Switching to direct connection.",
                bytes_remaining
            )
            return False, "Monthly budget exhausted"
        
        if bytes_remaining < self.fail_safe.get("when_gb_remaining", 1) * 1024 * 1024 * 1024:
            if self.use_direct_fallback:
                return False, f"Low budget ({bytes_remaining / (1024*1024*1024):.2f}GB remaining). Using direct connection."
            else:
                self._trigger_alert(
                    "critical",
                    f"Critical budget warning: {bytes_remaining / (1024*1024*1024):.2f}GB remaining",
                    bytes_remaining
                )
        
        return True, "Proxy available"
    
    def get_bytes_remaining(self) -> int:
        """Get remaining bytes in monthly budget"""
        today = datetime.now().strftime("%Y-%m")
        monthly_used = self.stats.monthly_bytes_used.get(today, 0)
        budget_bytes = self.monthly_budget_gb * 1024 * 1024 * 1024
        
        return max(0, budget_bytes - monthly_used)
    
    def get_usage_percentage(self) -> float:
        """Get percentage of monthly budget used"""
        today = datetime.now().strftime("%Y-%m")
        monthly_used = self.stats.monthly_bytes_used.get(today, 0)
        budget_bytes = self.monthly_budget_gb * 1024 * 1024 * 1024
        
        if budget_bytes == 0:
            return 100.0
        
        return (monthly_used / budget_bytes) * 100
    
    def record_usage(self, bytes_used: int, success: bool = True):
        """
        Record proxy usage for budget tracking
        
        Args:
            bytes_used: Number of bytes transferred
            success: Whether the request was successful
        """
        today = datetime.now().strftime("%Y-%m")
        day = datetime.now().strftime("%Y-%m-%d")
        
        # Update monthly usage
        if today not in self.stats.monthly_bytes_used:
            self.stats.monthly_bytes_used[today] = 0
        self.stats.monthly_bytes_used[today] += bytes_used
        
        # Update daily usage
        if day not in self.stats.daily_bytes_used:
            self.stats.daily_bytes_used[day] = 0
        self.stats.daily_bytes_used[day] += bytes_used
        
        # Update totals
        self.stats.total_bytes_used += bytes_used
        self.stats.requests_made += 1
        
        if success:
            self.stats.successful_requests += 1
        else:
            self.stats.failed_requests += 1
        
        self.stats.last_request_time = datetime.now()
        
        # Check budget thresholds
        usage_pct = self.get_usage_percentage()
        alert_threshold = self.config.get("budget_allocation", {}).get(
            "alert_threshold_percent", 80
        )
        
        if usage_pct >= alert_threshold and usage_pct < 100:
            self._trigger_alert(
                "warning",
                f"Warning: {usage_pct:.1f}% of monthly proxy budget used",
                self.get_bytes_remaining(),
                usage_pct
            )
        
        # Log usage
        remaining_gb = self.get_bytes_remaining() / (1024 * 1024 * 1024)
        logger.debug(f"Proxy usage: {bytes_used / (1024*1024):.2f}MB. Remaining: {remaining_gb:.2f}GB")
    
    def record_failure(self):
        """Record a proxy connection failure"""
        self.stats.proxy_failures += 1
        
        # If too many failures, switch to direct
        if self.stats.proxy_failures >= 5:
            logger.warning("Multiple proxy failures. Consider switching to direct connection.")
    
    def record_direct_fallback(self):
        """Record when falling back to direct connection"""
        self.stats.direct_fallback_count += 1
    
    def _trigger_alert(
        self,
        alert_type: str,
        message: str,
        bytes_remaining: int,
        percentage_used: float = None
    ):
        """Trigger a budget alert"""
        alert = BudgetAlert(
            alert_type=alert_type,
            message=message,
            bytes_remaining=bytes_remaining,
            percentage_used=percentage_used or self.get_usage_percentage(),
            timestamp=datetime.now()
        )
        
        self.budget_alerts.append(alert)
        logger.warning(f"Budget Alert [{alert_type}]: {message}")
        
        # Keep only last 10 alerts
        if len(self.budget_alerts) > 10:
            self.budget_alerts = self.budget_alerts[-10:]
    
    def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proxy"""
        if self._session is None or self._session.closed:
            proxy = self.get_proxy_dict()
            
            # Configure connector with proxy
            connector = aiohttp.TCPConnector(
                limit_per_host=self.config.get("usage_optimization", {}).get(
                    "connection_pool_size", 10
                ),
                ttl_dns_cache=300,
                keepalive_timeout=30
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.config.get("proxy_settings", {}).get(
                    "connection", {}
                ).get("timeout_seconds", 30)
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        
        return self._session
    
    async def make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Tuple[Optional[Dict], bool]:
        """
        Make an HTTP request through the proxy with budget tracking
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional aiohttp arguments
            
        Returns:
            Tuple of (response_data, used_proxy)
        """
        # Check if we can use proxy
        can_use, reason = self.can_use_proxy()
        
        if not can_use:
            logger.info(f"Using direct connection: {reason}")
            self.record_direct_fallback()
            
            # Make direct request
            try:
                session = await self.get_session()
                async with session.request(method, url, **kwargs) as response:
                    data = await response.json() if response.content_type and 'json' in response.content_type else await response.text()
                    return data, False
            except Exception as e:
                logger.error(f"Direct request failed: {e}")
                return None, False
        
        # Get session with proxy
        session = await self.get_session()
        proxy = self.get_proxy_dict()
        
        # Track bytes for response
        kwargs['proxy'] = proxy.get('http')
        
            async with session.request(method, url, **kwargs) as response:
                # Track actual bytes received
                content = await response.read()
                bytes_used = len(content)
                
                # Record usage
                self.record_usage(bytes_used, success=response.status < 400)
                
                # Handle response
                if response.status < 400:
                    try:
                        return json.loads(content), True
                    except json.JSONDecodeError:
                        return content.decode('utf-8', errors='ignore'), True
                else:
                    self.record_failure()
                    return None, True
                    
        except Exception as e:
            logger.error(f"Proxy request failed: {e}")
            self.record_failure()
            return None, True
    
    def get_stats_report(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics report"""
        today = datetime.now().strftime("%Y-%m-%d")
        month = datetime.now().strftime("%Y-%m-%m")
        
        daily_used_mb = self.stats.daily_bytes_used.get(today, 0) / (1024 * 1024)
        monthly_used_gb = sum(self.stats.monthly_bytes_used.values()) / (1024 * 1024 * 1024)
        budget_gb = self.monthly_budget_gb
        
        return {
            "provider": "IPRoyal",
            "budget": {
                "monthly_gb_limit": budget_gb,
                "daily_gb_limit": self.daily_budget_gb,
                "monthly_used_gb": round(monthly_used_gb, 2),
                "daily_used_mb": round(daily_used_mb, 2),
                "remaining_gb": round(budget_gb - monthly_used_gb, 2),
                "usage_percentage": round(self.get_usage_percentage(), 2)
            },
            "requests": {
                "total": self.stats.requests_made,
                "successful": self.stats.successful_requests,
                "failed": self.stats.failed_requests,
                "success_rate": round(
                    (self.stats.successful_requests / self.stats.requests_made * 100)
                    if self.stats.requests_made > 0 else 0, 2
                )
            },
            "fallback": {
                "proxy_failures": self.stats.proxy_failures,
                "direct_fallbacks": self.stats.direct_fallback_count
            },
            "last_request": self.stats.last_request_time.isoformat() if self.stats.last_request_time else None,
            "recent_alerts": [
                {
                    "type": a.alert_type,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in self.budget_alerts[-5:]
            ]
        }
    
    def get_monthly_cost_estimate(self) -> Dict[str, Any]:
        """Estimate monthly cost based on usage"""
        monthly_used_gb = sum(self.stats.monthly_bytes_used.values()) / (1024 * 1024 * 1024)
        
        regular_price = monthly_used_gb * self.config.get("provider", {}).get(
            "pricing", {}
        ).get("regular_price_per_gb", 7.00)
        
        discount_code = self.config.get("provider", {}).get("discount_code", "IPR50")
        discounted_price = monthly_used_gb * self.config.get("provider", {}).get(
            "pricing", {}
        ).get("discounted_price_per_gb", 1.75)
        
        return {
            "monthly_usage_gb": round(monthly_used_gb, 2),
            "regular_cost_usd": round(regular_price, 2),
            "discounted_cost_usd": round(discounted_price, 2),
            "discount_code": discount_code,
            "savings_usd": round(regular_price - discounted_price, 2),
            "budget_eur": self.config.get("provider", {}).get(
                "pricing", {}
            ).get("monthly_budget_eur", 15.00),
            "within_budget": discounted_price <= self.config.get("provider", {}).get(
                "pricing", {}
            ).get("monthly_budget_eur", 15.00)
        }
    
    def reset_daily_usage(self):
        """Reset daily usage tracking (called daily by scheduler)"""
        today = datetime.now().strftime("%Y-%m-%d")
        self.stats.daily_bytes_used[today] = 0
        logger.info("Daily proxy usage reset")
    
    async def close(self):
        """Close the proxy manager and session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        logger.info("IPRoyal Proxy Manager closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        asyncio.get_event_loop().run_until_complete(self.close())
        return False


class SmartProxyRouter:
    """
    Routes requests to appropriate proxy configuration based on platform
    and budget constraints
    """
    
    def __init__(self, proxy_manager: ProxyManager = None):
        """
        Initialize the smart router
        
        Args:
            proxy_manager: Optional proxy manager instance
        """
        self.proxy_manager = proxy_manager or ProxyManager()
        self.platform_configs = {}
    
    def add_platform_config(
        self,
        platform: str,
        proxy_required: bool = True,
        max_retries: int = 3
    ):
        """Add platform-specific configuration"""
        self.platform_configs[platform] = {
            "proxy_required": proxy_required,
            "max_retries": max_retries
        }
    
    async def route_request(
        self,
        platform: str,
        method: str,
        url: str,
        **kwargs
    ) -> Tuple[Optional[Dict], bool]:
        """
        Route a request through the appropriate proxy
        
        Args:
            platform: Platform name (tiktok, instagram, youtube)
            method: HTTP method
            url: Request URL
            **kwargs: Additional arguments
            
        Returns:
            Tuple of (response_data, used_proxy)
        """
        config = self.platform_configs.get(platform, {})
        
        # Try proxy first if allowed
        if config.get("proxy_required", True):
            can_use, reason = self.proxy_manager.can_use_proxy()
            
            if can_use:
                result, used_proxy = await self.proxy_manager.make_request(
                    method, url, **kwargs
                )
                
                if result is not None:
                    return result, used_proxy
                
                # Proxy failed, maybe retry
                retries = config.get("max_retries", 3)
                for _ in range(retries - 1):
                    logger.warning(f"Retrying {platform} request after proxy failure")
                    result, used_proxy = await self.proxy_manager.make_request(
                        method, url, **kwargs
                    )
                    if result is not None:
                        return result, used_proxy
        
        # Fallback to direct connection
        logger.info(f"{platform}: Using direct connection (proxy unavailable or not required)")
        self.proxy_manager.record_direct_fallback()
        
        try:
            session = await self.proxy_manager.get_session()
            async with session.request(method, url, **kwargs) as response:
                data = await response.json() if response.content_type and 'json' in response.content_type else await response.text()
                return data, False
        except Exception as e:
            logger.error(f"Direct request for {platform} failed: {e}")
            return None, False


# Convenience functions

async def quick_proxy_request(
    method: str,
    url: str,
    **kwargs
) -> Tuple[Optional[Dict], bool]:
    """
    Quick proxy request with default settings
    
    Args:
        method: HTTP method
        url: Request URL
        **kwargs: Additional arguments
        
    Returns:
        Tuple of (response_data, used_proxy)
    """
    async with ProxyManager() as manager:
        return await manager.make_request(method, url, **kwargs)


def check_proxy_status() -> Dict[str, Any]:
    """
    Check current proxy status and budget
    
    Returns:
        Status dictionary
    """
    with ProxyManager() as manager:
        can_use, reason = manager.can_use_proxy()
        stats = manager.get_stats_report()
        cost = manager.get_monthly_cost_estimate()
        
        return {
            "proxy_enabled": manager.enabled,
            "can_use_proxy": can_use,
            "reason": reason,
            "budget_remaining_gb": round(manager.get_bytes_remaining() / (1024 * 1024 * 1024), 2),
            "usage_percentage": stats["budget"]["usage_percentage"],
            "estimated_cost_usd": cost["discounted_cost_usd"],
            "within_budget": cost["within_budget"]
        }


# Export classes and functions
__all__ = [
    "ProxyManager",
    "ProxyCredentials",
    "ProxyStats",
    "BudgetAlert",
    "SmartProxyRouter",
    "quick_proxy_request",
    "check_proxy_status"
]
