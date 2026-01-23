# WaifuGen System - Project Documentation

## Project Overview

WaifuGen System is a comprehensive content automation platform designed for multi-platform content creation and subscriber management. The system is organized into two distinct phases:

- **Phase 1**: Content Production - Focuses on video generation, A2E API integration, and content distribution across social media platforms.
- **Phase 2**: Subscriber Management - Handles subscriber relationships, DM automation, and revenue optimization on subscription-based platforms.

## Project Structure

```
waifugen_system/
├── config/                          # Configuration files
│   ├── settings.py                  # Main configuration
│   ├── config.yaml                  # Application settings
│   ├── prompts.yaml                 # System prompts
│   ├── characters/                  # Character configurations
│   └── *.yaml                       # Strategy configurations
├── adapters/                        # Adapter implementations
│   ├── audio/                       # Audio processing adapters
│   ├── llm/                         # LLM adapters (Ollama, etc.)
│   ├── processing/                  # Processing adapters
│   ├── video/                       # Video processing adapters
│   └── visual/                      # Visual processing adapters
├── core/                            # Core components
│   ├── base_adapter.py              # Base adapter class
│   ├── factory.py                   # Factory pattern implementation
│   └── prompt_engine.py             # Prompt management
├── database/                        # Local databases (SQLite)
│   ├── conversion.db                # Conversion tracking database
│   ├── scheduler.db                 # Scheduler database
│   └── schema.sql                   # Database schema definitions
├── docs/                            # Documentation
│   ├── OLLAMA_LOCAL_LLM.md          # Local LLM setup guide
│   ├── STARTER_SQUAD_IMPLEMENTATION_GUIDE.md
│   └── phase1_*.md                  # Phase 1 documentation
├── scripts/                         # Utility scripts
│   ├── install_ollama.sh            # Ollama installation script
│   └── test_ollama.py               # Ollama test script
├── orchestrators/                   # Workflow orchestrators
│   ├── character_manager.py         # Character management
│   └── workflows.py                 # Workflow definitions
├── src/                             # Main source code
│   ├── api/                         # API integrations
│   │   └── a2e_client.py            # A2E API client
│   ├── automation/                  # Automation components
│   │   └── scheduler.py             # Task scheduler
│   ├── core/                        # Core utilities
│   │   ├── config_validator.py      # Configuration validation
│   │   └── logging_config.py        # Logging configuration
│   ├── dashboard/                   # Dashboard components
│   │   └── metrics.py               # Metrics collection
│   ├── messaging/                   # Phase 2: DM Automation
│   │   ├── phase2_dm_automation.py  # DM automation system
│   │   └── __init__.py
│   ├── models/                      # Data models
│   │   └── character_manager.py     # Character models
│   ├── monitoring/                  # Phase 1: Production Monitor
│   │   ├── phase1_production_monitor.py
│   │   └── __init__.py
│   ├── pipeline/                    # Content pipeline
│   │   └── content_generator.py     # Content generation
│   ├── services/                    # Services
│   │   └── local_tts.py             # Local TTS service
│   └── subscribers/                 # Phase 2: Subscriber Management
│       ├── phase2_subscriber_manager.py
│       └── __init__.py
├── tests/                           # Unit tests
├── assets/                          # Static assets
│   └── starter_squad/               # Starter squad characters
├── requirements.txt                 # Python dependencies
├── main.py                          # Application entry point
├── config.yaml                      # Application configuration
└── IMPLEMENTATION_SUMMARY.md        # Implementation summary
```

## Phase 1: Content Production

### Production Monitor (`src/monitoring/`)

The Production Monitor provides comprehensive monitoring for content production:

**Key Features:**
- A2E API credit tracking and budget management
- Video generation statistics and metrics
- Daily/weekly/monthly production summaries
- Character rotation for balanced content distribution
- Platform-specific content distribution tracking

**Classes:**
- `ProductionMonitor`: Central monitoring class
- `A2EApiClient`: API integration for credit management
- `ProductionConfig`: Configuration for production settings
- `A2ECreditStatus`: Credit status data model
- `VideoProductionStats`: Video production statistics
- `DailyProductionSummary`: Daily production metrics

**Usage:**
```python
from src.monitoring import ProductionMonitor, create_production_monitor

monitor = create_production_monitor()
credit_status = monitor.get_credit_status()
daily_summary = monitor.get_daily_summary()
character_status = monitor.get_character_rotation_status()
```

## Phase 2: Subscriber Management

### Subscriber Manager (`src/subscribers/`)

The Subscriber Manager handles all subscriber-related operations:

**Key Features:**
- Complete CRUD operations for subscribers
- Tier management (Basic, Premium, VIP)
- Engagement tracking and scoring
- Winback campaign management
- Lifetime value calculations
- PPV purchase tracking

**Classes:**
- `SubscriberManager`: Main subscriber management class
- `Subscriber`: Subscriber data model
- `TierHistory`: Tier change history
- `EngagementMetrics`: Daily engagement tracking
- `WinbackCampaign`: Winback campaign management
- `DatabaseConnection`: PostgreSQL connection manager

**Usage:**
```python
from src.subscribers import SubscriberManager, DatabaseConnection

db_config = {
    "host": "localhost",
    "database": "jav_automation",
    "user": "postgres",
    "password": "postgres"
}

db = DatabaseConnection(db_config)
manager = SubscriberManager(db)

subscriber = manager.create_subscriber(
    platform="onlyfans",
    username="test_user",
    tier="premium",
    monthly_rate=Decimal("19.99")
)
```

### DM Automation (`src/messaging/`)

The DM Automation system handles direct message campaigns:

**Key Features:**
- DM template creation and management
- Automated message sequences
- Campaign management with targeting
- Response tracking and analytics
- Variable interpolation for personalized messages
- Multi-platform support

**Classes:**
- `DMAutomationManager`: Main automation class
- `DMTemplate`: Message template model
- `DMSequence`: Message sequence definition
- `DMMessage`: Individual message model
- `AutomationCampaign`: Campaign management
- `VariableInterpolator`: Template variable handling

**Usage:**
```python
from src.messaging import DMAutomationManager, DatabaseConnection

db = DatabaseConnection(db_config)
dm = DMAutomationManager(db)

template = dm.create_template(
    template_name="Welcome Message",
    template_type="welcome",
    platform="onlyfans",
    message_body="Hey {{first_name}}! Welcome to our community!"
)

sequence = dm.start_sequence(
    subscriber_id="sub_xxx",
    platform="onlyfans",
    sequence_type="welcome",
    template_ids=[template.id],
    delays_hours=[0, 24, 72]
)
```

## Database Schema

### Phase 2 Tables

**Subscriber Management:**
- `phase2_subscribers`: Main subscriber records
- `subscription_tier_history`: Tier change history
- `subscriber_engagement`: Daily engagement metrics
- `winback_campaigns`: Winback campaign records
- `ppv_purchases`: Pay-per-view purchases

**DM Automation:**
- `dm_templates`: Message templates
- `dm_sequences`: Message sequences
- `dm_messages`: Individual messages
- `automation_campaigns`: Campaign records

## Configuration

### Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=jav_automation
DB_USER=postgres
DB_PASSWORD=postgres

# A2E API
A2E_API_KEY=your_api_key
A2E_PLAN=pro

# Ollama Local LLM
OLLAMA_BASE_URL=http://localhost:11434
```

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables
4. Run database migrations
5. Start the application: `python main.py`

## Support

For issues and questions, please refer to the documentation in the `docs/` directory.

---

**Last Updated:** 2026-01-22
**Version:** 1.0.0
