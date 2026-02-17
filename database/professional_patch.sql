-- =============================================================================
-- WAIFUGEN PROFESSIONAL SCHEMA PATCH - PHASE 1 & 2
-- =============================================================================

-- Accounts tracking (encrypted credentials)
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    platform VARCHAR(50) NOT NULL,
    account_username VARCHAR(100) NOT NULL,
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    status VARCHAR(20) DEFAULT 'active',
    region VARCHAR(10),
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Advanced Proxy Management (encrypted)
CREATE TABLE IF NOT EXISTS proxies (
    id SERIAL PRIMARY KEY,
    proxy_type VARCHAR(20) DEFAULT 'residential',
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    username VARCHAR(100),
    password_encrypted TEXT,
    region VARCHAR(10),
    in_use BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Mapping many-to-many
CREATE TABLE IF NOT EXISTS character_accounts (
    character_id INTEGER REFERENCES characters(id),
    account_id INTEGER REFERENCES accounts(id),
    PRIMARY KEY (character_id, account_id)
);

-- Profile management
CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    phase INTEGER DEFAULT 1, -- 1: Mainstream, 2: Premium/Adult
    platform VARCHAR(50),
    account_id INTEGER REFERENCES accounts(id),
    status VARCHAR(20) DEFAULT 'active'
);

-- Professional Flow Execution (Postgres version for FlowCoordinator)
CREATE TABLE IF NOT EXISTS flows_execution (
    id SERIAL PRIMARY KEY,
    flow_id VARCHAR(100),
    account_id INTEGER,
    status VARCHAR(50),
    started_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP,
    correlation_id UUID DEFAULT gen_random_uuid(),
    retries INTEGER DEFAULT 0,
    last_error TEXT
);

-- Media Assets Tracking
CREATE TABLE IF NOT EXISTS thumbnails (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES generated_content(id),
    path TEXT NOT NULL,
    url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subtitles (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES generated_content(id),
    path TEXT NOT NULL,
    url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Future scheduling
CREATE TABLE IF NOT EXISTS publication_schedules (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES generated_content(id),
    account_id INTEGER REFERENCES accounts(id),
    scheduled_for TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indices for optimization
CREATE INDEX IF NOT EXISTS idx_accounts_character ON accounts(character_id);
CREATE INDEX IF NOT EXISTS idx_flows_correlation ON flows_execution(correlation_id);
CREATE INDEX IF NOT EXISTS idx_proxies_region ON proxies(region);

-- Update timestamp trigger (if not exists)
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_update_accounts_timestamp ON accounts;
CREATE TRIGGER tr_update_accounts_timestamp
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
