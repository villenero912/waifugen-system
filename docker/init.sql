-- =============================================================================
-- PostgreSQL Initialization Script - Phase 2 Complete Database Schema
-- =============================================================================
-- Creates all required tables for the JAV Automation System Phase 2
-- Including: subscriber management, revenue tracking, DM automation, analytics
-- 
-- This file is used by docker-compose.yml postgres service
-- Last Updated: 2026-01-19
-- =============================================================================

-- =============================================================================
-- PHASE 1 TABLES (Critical for daily content generation)
-- =============================================================================

-- Characters table - Elite 8 and beyond
CREATE TABLE IF NOT EXISTS characters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    trigger_word VARCHAR(50) NOT NULL,
    age INT NOT NULL,
    style TEXT NOT NULL,
    personality TEXT NOT NULL,
    voice_model VARCHAR(100) DEFAULT 'en_US-amy-medium',
    lora_strength DECIMAL(3,2) DEFAULT 0.8,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Publications queue for Workflow 02 context
CREATE TABLE IF NOT EXISTS publications_queue (
    id SERIAL PRIMARY KEY,
    video_url TEXT NOT NULL,
    caption TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Social accounts for milestone tracking
CREATE TABLE IF NOT EXISTS social_accounts (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    username VARCHAR(100),
    followers INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Content reels table
CREATE TABLE IF NOT EXISTS reels (
    id SERIAL PRIMARY KEY,
    character_id INT REFERENCES characters(id),
    prompt TEXT,
    video_prompt TEXT,
    voice_script TEXT,
    video_url TEXT,
    voice_url TEXT,
    video_path TEXT,
    platform VARCHAR(50),
    duration INT,
    quality_tier VARCHAR(20) DEFAULT 'standard',
    nsfw_level INT DEFAULT 0,
    credits_used INT,
    cost_usd DECIMAL(10,4),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    has_subtitles BOOLEAN DEFAULT false,
    has_music BOOLEAN DEFAULT false,
    production_quality VARCHAR(50) DEFAULT 'standard',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Social media comments (Scraped)
CREATE TABLE IF NOT EXISTS social_comments (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    post_id VARCHAR(255) NOT NULL,
    user_name VARCHAR(255),
    comment_text TEXT NOT NULL,
    replied BOOLEAN DEFAULT false,
    replied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Automated replies log
CREATE TABLE IF NOT EXISTS comment_replies (
    id SERIAL PRIMARY KEY,
    comment_id INT REFERENCES social_comments(id),
    character_id INT REFERENCES characters(id),
    reply_text TEXT NOT NULL,
    sentiment VARCHAR(20),
    platform VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- NSFW Content tracking (Phase 2 escalation)
CREATE TABLE IF NOT EXISTS nsfw_content (
    id SERIAL PRIMARY KEY,
    character_id INT REFERENCES characters(id),
    nsfw_level INT NOT NULL,
    fetish_category VARCHAR(100),
    prompt TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    pricing_tier DECIMAL(10,2),
    production_method VARCHAR(50),
    video_url TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Seed Elite 8 Characters
INSERT INTO characters (id, name, trigger_word, age, style, personality, active) VALUES
(1, 'Miyuki Sakura', 'miysak_v1', 22, 'elegant, soft features, cute girlfriend', 'sweet, encouraging, girlfriend experience', true),
(16, 'Hana Nakamura', 'hannak_v1', 22, 'floral spring aesthetic, ethereal', 'gentle, nurturing, emotional romantic', true),
(10, 'Airi Neo', 'airineo_fusion', 24, 'cyborg, cyber-kimono, futuristic neon', 'energetic, tech-savvy, confident cyber AI', true),
(5, 'Aiko Hayashi', 'aikoch_v1', 24, 'minimalist, professional, elegant businesswoman', 'professional, warm, sophisticated', true),
(19, 'Rio Mizuno', 'riomiz_v1', 23, 'tropical beach, hydro aesthetic, athletic', 'active, teasing, beach lifestyle', true),
(15, 'Chiyo Sasaki', 'chisak_v1', 65, 'traditional kimono, mature elegant', 'wise, sophisticated, traditional', true),
(20, 'Mika Sweet', 'mikasweet_v1', 25, 'sweet playful, cute aesthetic', 'playful, flirty, energetic', true),
(21, 'Momoka AV', 'momoka_av_v1', 28, 'provocative bold, adult industry', 'confident, seductive, direct', true)
ON CONFLICT (id) DO NOTHING;

-- PHASE 1 CORE TABLES (Legacy and Auth)
-- =============================================================================

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content generated by the system
CREATE TABLE IF NOT EXISTS generated_content (
    id SERIAL PRIMARY KEY,
    content_id VARCHAR(255) UNIQUE NOT NULL,
    content_type VARCHAR(100),
    platform VARCHAR(100),
    title TEXT,
    description TEXT,
    video_url TEXT,
    thumbnail_url TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP
);

-- Platform credentials (encrypted)
CREATE TABLE IF NOT EXISTS platform_credentials (
    id SERIAL PRIMARY KEY,
    platform_name VARCHAR(100) UNIQUE NOT NULL,
    api_key_encrypted TEXT,
    api_secret_encrypted TEXT,
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expiry TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Revenue tracking (original table, expanded for Phase 2)
CREATE TABLE IF NOT EXISTS revenue_records (
    id SERIAL PRIMARY KEY,
    content_id VARCHAR(255),
    platform VARCHAR(100) NOT NULL,
    revenue_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    views INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5, 4) DEFAULT 0,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 2),
    metric_unit VARCHAR(50),
    metadata JSONB,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Proxy usage tracking
CREATE TABLE IF NOT EXISTS proxy_usage (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(100) NOT NULL,
    geo_target VARCHAR(10),
    data_used_gb DECIMAL(10, 2),
    cost_incurred DECIMAL(10, 2),
    usage_date DATE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- PHASE 2 TABLES - SUBSCRIBER MANAGEMENT
-- =============================================================================

-- Main subscribers table for Phase 2 platforms
CREATE TABLE IF NOT EXISTS phase2_subscribers (
    id SERIAL PRIMARY KEY,
    subscriber_id VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    platform_user_id VARCHAR(255),
    username VARCHAR(255),
    display_name VARCHAR(255),
    email VARCHAR(255),
    tier VARCHAR(50) DEFAULT 'basic',
    subscription_status VARCHAR(50) DEFAULT 'active',
    subscription_start_date TIMESTAMP,
    subscription_end_date TIMESTAMP,
    next_billing_date TIMESTAMP,
    monthly_rate DECIMAL(10, 2),
    lifetime_value DECIMAL(12, 2) DEFAULT 0,
    total_spent DECIMAL(12, 2) DEFAULT 0,
    source_platform VARCHAR(100),
    referral_code VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP,
    churned_at TIMESTAMP
);

-- Subscription tier history for tracking upgrades/downgrades
CREATE TABLE IF NOT EXISTS subscription_tier_history (
    id SERIAL PRIMARY KEY,
    subscriber_id VARCHAR(255) NOT NULL,
    from_tier VARCHAR(50),
    to_tier VARCHAR(50) NOT NULL,
    reason VARCHAR(255),
    is_upgrade BOOLEAN DEFAULT FALSE,
    effective_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    price_change DECIMAL(10, 2),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PPV (Pay-Per-View) content purchases
CREATE TABLE IF NOT EXISTS ppv_purchases (
    id SERIAL PRIMARY KEY,
    purchase_id VARCHAR(255) UNIQUE NOT NULL,
    subscriber_id VARCHAR(255) NOT NULL,
    content_id VARCHAR(255),
    content_type VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    price_paid DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    discount_applied DECIMAL(10, 2) DEFAULT 0,
    tier_discount_percent INTEGER DEFAULT 0,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_granted BOOLEAN DEFAULT TRUE,
    access_expiry TIMESTAMP,
    metadata JSONB
);

-- Direct messages sent to subscribers
CREATE TABLE IF NOT EXISTS dm_sequences (
    id SERIAL PRIMARY KEY,
    sequence_id VARCHAR(255) UNIQUE NOT NULL,
    subscriber_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    sequence_type VARCHAR(50) NOT NULL,
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB
);

-- Individual DM messages in sequences
CREATE TABLE IF NOT EXISTS dm_messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    sequence_id VARCHAR(255) NOT NULL,
    subscriber_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    step_number INTEGER NOT NULL,
    message_template_id VARCHAR(255),
    message_content TEXT,
    message_type VARCHAR(50),
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    response_received BOOLEAN DEFAULT FALSE,
    response_content TEXT,
    engagement_score DECIMAL(5, 4),
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscriber engagement metrics
CREATE TABLE IF NOT EXISTS subscriber_engagement (
    id SERIAL PRIMARY KEY,
    subscriber_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    engagement_date DATE NOT NULL,
    messages_sent INTEGER DEFAULT 0,
    messages_received INTEGER DEFAULT 0,
    content_views INTEGER DEFAULT 0,
    content_completions INTEGER DEFAULT 0,
    likes_given INTEGER DEFAULT 0,
    comments_made INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    dm_conversations INTEGER DEFAULT 0,
    engagement_score DECIMAL(5, 4) DEFAULT 0,
    active_session_count INTEGER DEFAULT 1,
    last_activity TIME,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subscriber_id, platform, engagement_date)
);

-- Content consumption tracking per subscriber
CREATE TABLE IF NOT EXISTS content_consumption (
    id SERIAL PRIMARY KEY,
    consumption_id VARCHAR(255) UNIQUE NOT NULL,
    subscriber_id VARCHAR(255) NOT NULL,
    content_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    content_type VARCHAR(100),
    character_id VARCHAR(255),
    view_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    watch_duration_seconds INTEGER,
    watch_percentage DECIMAL(5, 2),
    completed BOOLEAN DEFAULT FALSE,
    liked BOOLEAN DEFAULT FALSE,
    saved BOOLEAN DEFAULT FALSE,
    shared BOOLEAN DEFAULT FALSE,
    metadata JSONB
);

-- Winback campaign tracking
CREATE TABLE IF NOT EXISTS winback_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(255) UNIQUE NOT NULL,
    subscriber_id VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(50) NOT NULL,
    days_since_churn INTEGER NOT NULL,
    offer_type VARCHAR(100),
    discount_percent INTEGER,
    offer_start_date TIMESTAMP,
    offer_end_date TIMESTAMP,
    offer_claimed BOOLEAN DEFAULT FALSE,
    claimed_at TIMESTAMP,
    reactivated BOOLEAN DEFAULT FALSE,
    reactivated_at TIMESTAMP,
    reactivation_value DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'pending',
    attempts_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- PHASE 2 TABLES - REVENUE AND ANALYTICS
-- =============================================================================

-- Detailed revenue breakdown by transaction
CREATE TABLE IF NOT EXISTS revenue_transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    subscriber_id VARCHAR(255),
    platform VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    tier VARCHAR(50),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    platform_fee DECIMAL(10, 2),
    net_revenue DECIMAL(10, 2),
    character_id VARCHAR(255),
    content_id VARCHAR(255),
    payment_method VARCHAR(50),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payout_date TIMESTAMP,
    payout_status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB
);

-- Daily revenue summary
CREATE TABLE IF NOT EXISTS daily_revenue_summary (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    summary_date DATE NOT NULL,
    total_subscriptions INTEGER DEFAULT 0,
    new_subscriptions INTEGER DEFAULT 0,
    churned_subscriptions INTEGER DEFAULT 0,
    subscription_revenue DECIMAL(12, 2) DEFAULT 0,
    ppv_revenue DECIMAL(12, 2) DEFAULT 0,
    custom_content_revenue DECIMAL(12, 2) DEFAULT 0,
    dm_revenue DECIMAL(12, 2) DEFAULT 0,
    total_revenue DECIMAL(12, 2) DEFAULT 0,
    platform_fees DECIMAL(12, 2) DEFAULT 0,
    net_revenue DECIMAL(12, 2) DEFAULT 0,
    average_revenue_per_subscriber DECIMAL(10, 4),
    currency VARCHAR(10) DEFAULT 'USD',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, summary_date)
);

-- Monthly analytics and KPIs
CREATE TABLE IF NOT EXISTS monthly_analytics (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    analytics_month DATE NOT NULL,
    kpi_name VARCHAR(100) NOT NULL,
    kpi_value DECIMAL(15, 4),
    kpi_unit VARCHAR(50),
    target_value DECIMAL(15, 4),
    variance_percent DECIMAL(10, 4),
    trend_direction VARCHAR(10),
    metadata JSONB,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, analytics_month, kpi_name)
);

-- Key Performance Indicators aggregated view
CREATE TABLE IF NOT EXISTS kpi_dashboard (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(20) DEFAULT 'daily',
    
    -- Subscription KPIs
    total_subscribers INTEGER DEFAULT 0,
    active_subscribers INTEGER DEFAULT 0,
    new_subscribers INTEGER DEFAULT 0,
    churned_subscribers INTEGER DEFAULT 0,
    subscriber_growth_rate DECIMAL(8, 4) DEFAULT 0,
    churn_rate DECIMAL(8, 4) DEFAULT 0,
    retention_rate DECIMAL(8, 4) DEFAULT 0,
    
    -- Revenue KPIs
    monthly_recurring_revenue DECIMAL(14, 2) DEFAULT 0,
    total_revenue DECIMAL(14, 2) DEFAULT 0,
    average_revenue_per_subscriber DECIMAL(10, 4) DEFAULT 0,
    lifetime_value DECIMAL(12, 2) DEFAULT 0,
    revenue_growth_rate DECIMAL(8, 4) DEFAULT 0,
    
    -- Engagement KPIs
    engagement_rate DECIMAL(8, 4) DEFAULT 0,
    dm_response_rate DECIMAL(8, 4) DEFAULT 0,
    content_completion_rate DECIMAL(8, 4) DEFAULT 0,
    subscriber_activity_rate DECIMAL(8, 4) DEFAULT 0,
    
    -- Conversion KPIs
    conversion_rate DECIMAL(8, 4) DEFAULT 0,
    upsell_rate DECIMAL(8, 4) DEFAULT 0,
    ppv_conversion_rate DECIMAL(8, 4) DEFAULT 0,
    
    -- Tier distribution
    basic_subscribers INTEGER DEFAULT 0,
    premium_subscribers INTEGER DEFAULT 0,
    vip_subscribers INTEGER DEFAULT 0,
    tier_upgrades INTEGER DEFAULT 0,
    
    -- Platform-specific
    views_total INTEGER DEFAULT 0,
    likes_total INTEGER DEFAULT 0,
    comments_total INTEGER DEFAULT 0,
    shares_total INTEGER DEFAULT 0,
    
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, period_start, period_type)
);

-- =============================================================================
-- PHASE 2 TABLES - AUTOMATION AND CAMPAIGNS
-- =============================================================================

-- DM automation templates
CREATE TABLE IF NOT EXISTS dm_templates (
    id SERIAL PRIMARY KEY,
    template_id VARCHAR(255) UNIQUE NOT NULL,
    template_name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    platform VARCHAR(50),
    character_id VARCHAR(255),
    language VARCHAR(10),
    subject_line TEXT,
    message_body TEXT,
    variables JSONB,
    conditions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    avg_response_rate DECIMAL(8, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Automation campaigns
CREATE TABLE IF NOT EXISTS automation_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(255) UNIQUE NOT NULL,
    campaign_name VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(50) NOT NULL,
    platform VARCHAR(50),
    character_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'draft',
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    target_audience JSONB,
    targeting_rules JSONB,
    template_id VARCHAR(255),
    sequence_config JSONB,
    total_targets INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    converted_count INTEGER DEFAULT 0,
    revenue_generated DECIMAL(12, 2) DEFAULT 0,
    budget DECIMAL(10, 2),
    cost_per_conversion DECIMAL(10, 4),
    roi_percent DECIMAL(10, 2),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaign performance tracking
CREATE TABLE IF NOT EXISTS campaign_performance (
    id SERIAL PRIMARY KEY,
    performance_id VARCHAR(255) UNIQUE NOT NULL,
    campaign_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 4),
    recorded_date DATE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(campaign_id, metric_name, recorded_date)
);

-- =============================================================================
-- PHASE 2 TABLES - CHARACTER AND CONTENT PERFORMANCE
-- =============================================================================

-- Character performance metrics
CREATE TABLE IF NOT EXISTS character_performance (
    id SERIAL PRIMARY KEY,
    character_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    performance_date DATE NOT NULL,
    total_subscribers INTEGER DEFAULT 0,
    new_subscribers INTEGER DEFAULT 0,
    churned_subscribers INTEGER DEFAULT 0,
    total_revenue DECIMAL(12, 2) DEFAULT 0,
    subscription_revenue DECIMAL(12, 2) DEFAULT 0,
    ppv_revenue DECIMAL(12, 2) DEFAULT 0,
    custom_content_revenue DECIMAL(12, 2) DEFAULT 0,
    dm_revenue DECIMAL(12, 2) DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    engagement_rate DECIMAL(8, 4) DEFAULT 0,
    avg_response_rate DECIMAL(8, 4) DEFAULT 0,
    avg_session_duration DECIMAL(10, 2) DEFAULT 0,
    content_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, platform, performance_date)
);

-- Content performance by type
CREATE TABLE IF NOT EXISTS content_performance (
    id SERIAL PRIMARY KEY,
    content_id VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    character_id VARCHAR(255),
    platform VARCHAR(50) NOT NULL,
    publish_date TIMESTAMP,
    total_views INTEGER DEFAULT 0,
    unique_viewers INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    dislikes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    watch_time_seconds INTEGER DEFAULT 0,
    avg_watch_percentage DECIMAL(8, 4) DEFAULT 0,
    completion_rate DECIMAL(8, 4) DEFAULT 0,
    engagement_rate DECIMAL(8, 4) DEFAULT 0,
    revenue_generated DECIMAL(12, 2) DEFAULT 0,
    cpm DECIMAL(10, 4),
    rpm DECIMAL(10, 4),
    content_quality_score DECIMAL(5, 2),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- PHASE 2 TABLES - JAPANESE PLATFORM SPECIFIC
-- =============================================================================

-- Japanese platform specific tracking
CREATE TABLE IF NOT EXISTS japanese_platform_metrics (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    metric_date DATE NOT NULL,
    total_fans INTEGER DEFAULT 0,
    total_content INTEGER DEFAULT 0,
    daily_views INTEGER DEFAULT 0,
    daily_revenue DECIMAL(12, 2) DEFAULT 0,
    tip_amount DECIMAL(12, 2) DEFAULT 0,
    sales_amount DECIMAL(12, 2) DEFAULT 0,
    ranking_position INTEGER,
    trending_score DECIMAL(10, 4),
    new_followers INTEGER DEFAULT 0,
    engagement_rate DECIMAL(8, 4) DEFAULT 0,
    proxy_data_used_gb DECIMAL(10, 2) DEFAULT 0,
    proxy_cost DECIMAL(10, 2) DEFAULT 0,
    net_revenue DECIMAL(12, 2) DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, metric_date)
);

-- FC2 specific data
CREATE TABLE IF NOT EXISTS fc2_data (
    id SERIAL PRIMARY KEY,
    fc2_id VARCHAR(255) NOT NULL,
    content_id VARCHAR(255),
    video_code VARCHAR(100),
    title TEXT,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    favorites INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    revenue_share DECIMAL(8, 4),
    estimated_revenue DECIMAL(12, 2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Fantia specific data
CREATE TABLE IF NOT EXISTS fantia_data (
    id SERIAL PRIMARY KEY,
    fantia_id VARCHAR(255) NOT NULL,
    content_id VARCHAR(255),
    post_id VARCHAR(100),
    title TEXT,
    content_type VARCHAR(100),
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    bookmark_count INTEGER DEFAULT 0,
    price DECIMAL(10, 2),
    sales_count INTEGER DEFAULT 0,
    revenue DECIMAL(12, 2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =============================================================================

-- Subscriber indexes
CREATE INDEX IF NOT EXISTS idx_phase2_subscribers_platform ON phase2_subscribers(platform);
CREATE INDEX IF NOT EXISTS idx_phase2_subscribers_tier ON phase2_subscribers(tier);
CREATE INDEX IF NOT EXISTS idx_phase2_subscribers_status ON phase2_subscribers(subscription_status);
CREATE INDEX IF NOT EXISTS idx_phase2_subscribers_ltv ON phase2_subscribers(lifetime_value DESC);
CREATE INDEX IF NOT EXISTS idx_phase2_subscribers_created ON phase2_subscribers(created_at);
CREATE INDEX IF NOT EXISTS idx_phase2_subscribers_churned ON phase2_subscribers(churned_at);

-- Subscription history indexes
CREATE INDEX IF NOT EXISTS idx_sub_history_subscriber ON subscription_tier_history(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_sub_history_date ON subscription_tier_history(effective_date);

-- PPV purchases indexes
CREATE INDEX IF NOT EXISTS idx_ppv_subscriber ON ppv_purchases(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_ppv_platform ON ppv_purchases(platform);
CREATE INDEX IF NOT EXISTS idx_ppv_date ON ppv_purchases(purchase_date);

-- DM sequences indexes
CREATE INDEX IF NOT EXISTS idx_dm_sequences_subscriber ON dm_sequences(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_dm_sequences_status ON dm_sequences(status);
CREATE INDEX IF NOT EXISTS idx_dm_sequences_type ON dm_sequences(sequence_type);

-- DM messages indexes
CREATE INDEX IF NOT EXISTS idx_dm_messages_sequence ON dm_messages(sequence_id);
CREATE INDEX IF NOT EXISTS idx_dm_messages_subscriber ON dm_messages(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_dm_messages_status ON dm_messages(status);
CREATE INDEX IF NOT EXISTS idx_dm_messages_sent ON dm_messages(sent_at);

-- Engagement indexes
CREATE INDEX IF NOT EXISTS idx_engagement_subscriber ON subscriber_engagement(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_engagement_date ON subscriber_engagement(engagement_date);
CREATE INDEX IF NOT EXISTS idx_engagement_score ON subscriber_engagement(engagement_score DESC);

-- Revenue indexes
CREATE INDEX IF NOT EXISTS idx_revenue_trans_platform ON revenue_transactions(platform);
CREATE INDEX IF NOT EXISTS idx_revenue_trans_type ON revenue_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_revenue_trans_date ON revenue_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_revenue_trans_subscriber ON revenue_transactions(subscriber_id);

-- Daily summary indexes
CREATE INDEX IF NOT EXISTS idx_daily_revenue_platform_date ON daily_revenue_summary(platform, summary_date);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_monthly_analytics_platform_date ON monthly_analytics(platform, analytics_month);
CREATE INDEX IF NOT EXISTS idx_kpi_dashboard_period ON kpi_dashboard(platform, period_start, period_type);

-- Campaign indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_type ON automation_campaigns(campaign_type);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON automation_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaign_performance_campaign ON campaign_performance(campaign_id);

-- Content performance indexes
CREATE INDEX IF NOT EXISTS idx_content_perf_platform ON content_performance(platform);
CREATE INDEX IF NOT EXISTS idx_content_perf_type ON content_performance(content_type);
CREATE INDEX IF NOT EXISTS idx_content_perf_revenue ON content_performance(revenue_generated DESC);
CREATE INDEX IF NOT EXISTS idx_content_perf_date ON content_performance(publish_date);

-- Japanese platform indexes
CREATE INDEX IF NOT EXISTS idx_jp_metrics_platform_date ON japanese_platform_metrics(platform, metric_date);
CREATE INDEX IF NOT EXISTS idx_fc2_id ON fc2_data(fc2_id);
CREATE INDEX IF NOT EXISTS idx_fantia_id ON fantia_data(fantia_id);

-- Queue optimization indexes
CREATE INDEX IF NOT EXISTS idx_publications_queue_status ON publications_queue(status);
CREATE INDEX IF NOT EXISTS idx_publications_queue_created ON publications_queue(created_at);
CREATE INDEX IF NOT EXISTS idx_social_accounts_platform ON social_accounts(platform);

-- =============================================================================
-- TABLE COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE phase2_subscribers IS 'Main subscriber table for Phase 2 platforms (OnlyFans, XVideos, Pornhub, etc.)';
COMMENT ON TABLE subscription_tier_history IS 'Tracks all tier changes (upgrades/downgrades) per subscriber';
COMMENT ON TABLE ppv_purchases IS 'Records all Pay-Per-View content purchases by subscribers';
COMMENT ON TABLE dm_sequences IS 'DM automation sequences assigned to subscribers';
COMMENT ON TABLE dm_messages IS 'Individual messages within DM automation sequences';
COMMENT ON TABLE subscriber_engagement IS 'Daily engagement metrics per subscriber';
COMMENT ON TABLE content_consumption IS 'Tracks what content each subscriber views';
COMMENT ON TABLE winback_campaigns IS 'Churn recovery campaigns for inactive subscribers';
COMMENT ON TABLE revenue_transactions IS 'Detailed revenue breakdown by transaction';
COMMENT ON TABLE daily_revenue_summary IS 'Aggregated daily revenue metrics per platform';
COMMENT ON TABLE monthly_analytics IS 'Monthly KPI calculations for each platform';
COMMENT ON TABLE kpi_dashboard IS 'Aggregated dashboard metrics for reporting';
COMMENT ON TABLE dm_templates IS 'Reusable DM message templates for automation';
COMMENT ON TABLE automation_campaigns IS 'Marketing and engagement automation campaigns';
COMMENT ON TABLE campaign_performance IS 'Daily performance metrics per campaign';
COMMENT ON TABLE character_performance IS 'Performance metrics per character by platform';
COMMENT ON TABLE content_performance IS 'Individual content performance tracking';
COMMENT ON TABLE japanese_platform_metrics IS 'Japanese platform (FC2, Fantia, Line) specific metrics';
COMMENT ON TABLE fc2_data IS 'FC2 platform content and performance data';
COMMENT ON TABLE fantia_data IS 'Fantia platform content and performance data';

-- =============================================================================
-- VIEW DEFINITIONS FOR COMMON QUERIES
-- =============================================================================

-- Active subscribers view
CREATE OR REPLACE VIEW v_active_subscribers AS
SELECT 
    platform,
    tier,
    COUNT(*) as subscriber_count,
    SUM(monthly_rate) as monthly_revenue,
    AVG(lifetime_value) as avg_ltv
FROM phase2_subscribers
WHERE subscription_status = 'active'
GROUP BY platform, tier;

-- Daily revenue aggregation view
CREATE OR REPLACE VIEW v_daily_revenue AS
SELECT 
    platform,
    summary_date,
    total_revenue,
    net_revenue,
    total_subscriptions,
    new_subscriptions,
    churned_subscriptions,
    average_revenue_per_subscriber
FROM daily_revenue_summary
ORDER BY platform, summary_date DESC;

-- Subscriber engagement leaderboard
CREATE OR REPLACE VIEW v_engagement_leaderboard AS
SELECT 
    subscriber_id,
    platform,
    SUM(engagement_score) as total_score,
    SUM(content_views) as total_views,
    SUM(messages_received) as total_messages,
    COUNT(DISTINCT engagement_date) as active_days,
    AVG(engagement_score) as avg_daily_score
FROM subscriber_engagement
GROUP BY subscriber_id, platform
ORDER BY total_score DESC;

-- Content performance ranking
CREATE OR REPLACE VIEW v_content_ranking AS
SELECT 
    content_id,
    content_type,
    character_id,
    platform,
    total_views,
    engagement_rate,
    revenue_generated,
    completion_rate,
    content_quality_score,
    publish_date
FROM content_performance
ORDER BY revenue_generated DESC, engagement_rate DESC;

-- =============================================================================
-- FUNCTIONS FOR AUTOMATED CALCULATIONS
-- =============================================================================

-- Calculate subscriber lifetime value
CREATE OR REPLACE FUNCTION calculate_subscriber_ltv(p_subscriber_id VARCHAR)
RETURNS DECIMAL AS $$
DECLARE
    v_total_spent DECIMAL;
    v_subscription_months INTEGER;
    v_retention_rate DECIMAL;
    v_monthly_churn DECIMAL;
    v_ltv DECIMAL;
BEGIN
    SELECT 
        COALESCE(SUM(total_spent), 0),
        EXTRACT(MONTH FROM AGE(COALESCE(subscription_end_date, CURRENT_TIMESTAMP), subscription_start_date)),
        retention_rate,
        churn_rate / 12.0
    INTO v_total_spent, v_subscription_months, v_retention_rate, v_monthly_churn
    FROM phase2_subscribers
    WHERE subscriber_id = p_subscriber_id
    GROUP BY subscription_start_date, subscription_end_date, retention_rate, churn_rate;
    
    IF v_subscription_months > 0 AND v_monthly_churn > 0 THEN
        v_ltv := v_total_spent / (1 - POWER((1 - v_retention_rate), v_subscription_months));
    ELSE
        v_ltv := v_total_spent * 12;
    END IF;
    
    RETURN v_ltv;
END;
$$ LANGUAGE plpgsql;

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update timestamp trigger to relevant tables
CREATE TRIGGER update_phase2_subscribers_timestamp
    BEFORE UPDATE ON phase2_subscribers
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_dm_templates_timestamp
    BEFORE UPDATE ON dm_templates
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_automation_campaigns_timestamp
    BEFORE UPDATE ON automation_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_content_performance_timestamp
    BEFORE UPDATE ON content_performance
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- =============================================================================
-- END OF DATABASE SCHEMA
-- =============================================================================
