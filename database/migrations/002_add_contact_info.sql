-- ============================================
-- ADD CONTACT INFO COLUMN TO CRM
-- ============================================
-- Migration pour ajouter le champ contact_info et nouvelles méthodes de contact

-- 1. Supprimer l'ancienne contrainte sur contact_method
ALTER TABLE startup_contacts
DROP CONSTRAINT IF EXISTS startup_contacts_contact_method_check;

-- 2. Ajouter la nouvelle contrainte avec instagram et phone
ALTER TABLE startup_contacts
ADD CONSTRAINT startup_contacts_contact_method_check
CHECK (contact_method IN ('email', 'linkedin', 'twitter', 'instagram', 'phone', 'other'));

-- 3. Ajouter la colonne contact_info pour stocker les coordonnées
-- (email, URL LinkedIn, compte Instagram, numéro de téléphone, etc.)
ALTER TABLE startup_contacts
ADD COLUMN IF NOT EXISTS contact_info TEXT;

-- Commentaire sur la nouvelle colonne
COMMENT ON COLUMN startup_contacts.contact_info IS 'Coordonnées de contact (email, URL LinkedIn, @instagram, téléphone, etc.)';
