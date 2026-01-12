-- ============================================
-- STARTUP CONTACTS - CRM TABLE
-- ============================================
-- Exécute ce fichier dans Supabase SQL Editor

-- Table pour tracker les contacts avec les startups
CREATE TABLE startup_contacts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    startup_id TEXT NOT NULL REFERENCES daily_launches(id) ON DELETE CASCADE,
    contacted_by TEXT NOT NULL CHECK (contacted_by IN ('Ethan', 'Théo')),
    contacted_at DATE DEFAULT CURRENT_DATE,
    contact_method TEXT CHECK (contact_method IN ('email', 'linkedin', 'twitter', 'other')),
    notes TEXT,
    status TEXT DEFAULT 'contacted' CHECK (status IN ('to_contact', 'contacted', 'responded', 'meeting', 'not_interested', 'converted')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(startup_id)
);

-- Index pour les requêtes fréquentes
CREATE INDEX idx_startup_contacts_status ON startup_contacts(status);
CREATE INDEX idx_startup_contacts_contacted_by ON startup_contacts(contacted_by);
CREATE INDEX idx_startup_contacts_contacted_at ON startup_contacts(contacted_at DESC);

-- Commentaire
COMMENT ON TABLE startup_contacts IS 'Suivi des contacts avec les startups (CRM)';

-- Enable RLS (Row Level Security) - optionnel mais recommandé
ALTER TABLE startup_contacts ENABLE ROW LEVEL SECURITY;

-- Policy pour permettre tout (à ajuster selon vos besoins)
CREATE POLICY "Allow all operations" ON startup_contacts FOR ALL USING (true) WITH CHECK (true);
