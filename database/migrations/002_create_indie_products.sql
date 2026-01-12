-- Migration: Create indie_products table
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS indie_products (
    -- Use URL hash as primary key (Indie Hackers doesn't have IDs)
    id TEXT PRIMARY KEY,

    -- Basic info
    name TEXT NOT NULL,
    tagline TEXT DEFAULT '',
    url TEXT UNIQUE NOT NULL,
    website TEXT,

    -- Indie Hackers specific
    revenue TEXT DEFAULT '',
    stripe_verified BOOLEAN DEFAULT FALSE,
    categories TEXT[] DEFAULT '{}',

    -- Classification (same as Product Hunt)
    business_type TEXT DEFAULT 'UNKNOWN' CHECK (business_type IN ('B2B', 'B2C', 'UNKNOWN')),
    classification_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    scraped_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_indie_products_business_type ON indie_products(business_type);
CREATE INDEX IF NOT EXISTS idx_indie_products_stripe_verified ON indie_products(stripe_verified);
CREATE INDEX IF NOT EXISTS idx_indie_products_scraped_at ON indie_products(scraped_at DESC);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE indie_products ENABLE ROW LEVEL SECURITY;

-- Policy to allow all operations (adjust based on your needs)
CREATE POLICY "Allow all operations on indie_products" ON indie_products
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Trigger to update updated_at on changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_indie_products_updated_at
    BEFORE UPDATE ON indie_products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
