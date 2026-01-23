# IPRoyal Proxy Configuration for Elite 8

## Overview

This guide explains how to configure IPRoyal residential proxies for the Elite 8 AI Video Generation System with a budget of **€15/month**.

- **Provider**: [IPRoyal](https://iproyal.com)
- **Discount Code**: `IPR50`
- **Price with Discount**: $1.75/GB (regular $7/GB)
- **Monthly Budget**: ~10GB for approximately €15
- **Pool Size**: 32+ million residential IPs

## Why IPRoyal?

| Feature | IPRoyal | Free Proxies | Other Premium |
|---------|---------|--------------|---------------|
| Monthly Cost | ~€15 | Free | €50-200+ |
| Residential IPs | 32M+ | Rare | 50M+ |
| Clean IPs | Yes | No (blacklisted) | Yes |
| Success Rate | 99%+ | 20-50% | 99%+ |
| Budget Fit | Perfect | Too risky | Over budget |

**Using free proxies is NOT recommended** because:
- IPs are in blacklists
- Easily detected by TikTok/Instagram/YouTube
- High risk of account bans
- Unreliable and slow

## Step 1: Sign Up for IPRoyal

1. Go to [https://iproyal.com](https://iproyal.com)
2. Click "Sign Up" or "Register"
3. Create an account with your email
4. **Use discount code: `IPR50`** at checkout

## Step 2: Purchase Proxy Credits

1. Log in to your IPRoyal dashboard
2. Navigate to "Residential Proxies" → "Buy"
3. Select your plan:
   - **Recommended**: 10GB for $17.50 (with IPR50 discount)
   - This gives you ~10GB/month within your €15 budget
4. Complete payment
5. Your credentials will be available in the dashboard

## Step 3: Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
# Copy the template
cp config/.env.example .env

# Edit with your credentials
nano .env
```

Update these values in `.env`:

```bash
# Enable IPRoyal
IPROYAL_ENABLED=true

# Your IPRoyal credentials (from dashboard)
IPROYAL_USERNAME=your_username_here
IPROYAL_PASSWORD=your_password_here

# Default settings (usually don't need to change)
IPROYAL_HOST=geo.iproyal.com
IPROYAL_PORT=12345
IPROYAL_PROTOCOL=http

# Budget limits
IPROYAL_MONTHLY_GB_LIMIT=10
IPROYAL_DAILY_GB_LIMIT=0.5

# Allow fallback to direct connection if proxy fails
USE_DIRECT_FALLBACK=true
```

## Step 4: Verify Configuration

Run the setup script to verify your configuration:

```bash
bash scripts/setup_iproyal.sh
```

Or test directly with Python:

```python
from src.social import check_proxy_status

status = check_proxy_status()
print(status)
```

Expected output if configured correctly:
```python
{
    'proxy_enabled': True,
    'can_use_proxy': True,
    'budget_remaining_gb': 9.5,
    'usage_percentage': 5.0,
    'estimated_cost_usd': 0.88,
    'within_budget': True
}
```

## Step 5: Monitor Usage

The system automatically tracks proxy usage and sends alerts when:

- **80% budget used**: Warning alert
- **Critical level**: Switch to direct connection automatically
- **Budget exhausted**: All traffic uses direct connection

Check usage statistics:

```python
from src.social import ProxyManager

manager = ProxyManager()
stats = manager.get_stats_report()
print(stats)
```

Example stats output:
```python
{
    'provider': 'IPRoyal',
    'budget': {
        'monthly_gb_limit': 10,
        'monthly_used_gb': 0.5,
        'remaining_gb': 9.5,
        'usage_percentage': 5.0
    },
    'requests': {
        'total': 100,
        'successful': 98,
        'failed': 2,
        'success_rate': 98.0
    },
    'fallback': {
        'proxy_failures': 2,
        'direct_fallbacks': 0
    }
}
```

## Cost Breakdown

| Item | Regular Price | With IPR50 | Your Cost |
|------|---------------|------------|-----------|
| 10GB Residential | $70.00 | $17.50 | ~€15 |
| Per Reel (15s video) | ~$0.24 | ~$0.06 | ~€0.05 |
| 4 Reels/Day | ~$0.96 | ~$0.24 | ~€0.20 |
| 30 Days | ~$28.80 | ~$7.20 | ~€6.00 |

**Your total monthly cost: ~€6-15** (including A2E API + proxies)

## Troubleshooting

### Proxy Connection Failed

```bash
# Test manually
curl -v --proxy http://username:password@geo.iproyal.com:12345 https://api.ipify.org
```

**Solutions:**
1. Check credentials in `.env`
2. Verify you have available GB in your account
3. Try a different port (IPRoyal offers multiple ports)

### Account Banned by Platform

If your social media accounts get banned:

1. **Use multiple accounts** - Create 2-3 accounts per platform
2. **Rotate between accounts** - The system does this automatically
3. **Add human activity** - Like/comment manually occasionally
4. **Vary posting times** - Add random 5-15 minute variations

### Out of Proxy Budget

The system automatically:
1. Sends Telegram/console alerts at 80% usage
2. Falls back to direct connection when budget is critical
3. Continues working with direct connection (higher ban risk)

## Advanced Configuration

### Targeting Specific Countries

Edit `config/social/iproyal_config.json`:

```json
{
  "target_locations": {
    "primary": ["JP", "US", "KR"],
    "fallback": ["GB", "DE", "AU"],
    "rotation_strategy": "round_robin"
  }
}
```

### Adjusting Budget Allocation

```json
{
  "budget_allocation": {
    "monthly_gb_limit": 10,
    "per_platform_allocation": {
      "tiktok": {"percentage": 40},
      "instagram": {"percentage": 35},
      "youtube": {"percentage": 25}
    }
  }
}
```

### Setting Up Telegram Alerts

```bash
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Files Created

| File | Purpose |
|------|---------|
| `config/social/iproyal_config.json` | IPRoyal proxy settings |
| `config/.env.example` | Environment template |
| `src/social/proxy_manager.py` | Proxy management module |
| `scripts/setup_iproyal.sh` | Setup verification script |

## Quick Reference

```bash
# Setup commands
cp config/.env.example .env
nano .env
bash scripts/setup_iproyal.sh

# Test proxy
python3 -c "from src.social import check_proxy_status; print(check_proxy_status())"

# Check usage
python3 -c "from src.social import ProxyManager; m = ProxyManager(); print(m.get_stats_report())"
```

## Support

- **IPRoyal Support**: Available through your dashboard
- **Elite 8 Issues**: Check the main README
- **Discount Code**: Always use `IPR50` for best pricing

---

**Remember**: The key to avoiding bans is not just the proxy, but also varying your posting times, using multiple accounts, and making the content look as human as possible. The Elite 8 system includes these features automatically.
