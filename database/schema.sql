-- ============================================
-- PRODUCT HUNT DAILY LAUNCHES - SCHEMA COMPLET
-- ============================================
-- Exécute ce fichier dans Supabase SQL Editor

-- Créer la table complète
CREATE TABLE daily_launches (
    -- Clé primaire = ID Product Hunt
    id TEXT PRIMARY KEY,

    -- Informations du produit
    name TEXT NOT NULL,
    tagline TEXT,
    description TEXT,
    url TEXT,
    website TEXT,

    -- Métriques
    votes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,

    -- Dates
    created_at TIMESTAMPTZ,
    featured_at TIMESTAMPTZ,

    -- Maker principal
    maker_name TEXT,
    maker_twitter TEXT,

    -- Topics/catégories
    topics TEXT[] DEFAULT '{}',

    -- Classification B2B/B2C
    business_type TEXT DEFAULT 'UNKNOWN' CHECK (business_type IN ('B2B', 'B2C', 'UNKNOWN')),
    classification_reason TEXT,

    -- Metadata
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour filtrer par date de création
CREATE INDEX idx_daily_launches_created_at ON daily_launches (created_at DESC);

-- Index pour filtrer par type B2B/B2C
CREATE INDEX idx_daily_launches_business_type ON daily_launches (business_type);

-- Commentaire
COMMENT ON TABLE daily_launches IS 'Produits Product Hunt avec classification B2B/B2C';
