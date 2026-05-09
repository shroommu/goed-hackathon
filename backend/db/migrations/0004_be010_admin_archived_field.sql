-- BE-010: Add archived field to resources and companies for soft delete
-- Migration: 0004_be010_admin_archived_field.sql

-- Add archived column to resources table
ALTER TABLE resources
ADD COLUMN IF NOT EXISTS archived BOOLEAN NOT NULL DEFAULT FALSE;

-- Add archived column to companies table
ALTER TABLE companies
ADD COLUMN IF NOT EXISTS archived BOOLEAN NOT NULL DEFAULT FALSE;

-- Add index for performance on filtered queries
CREATE INDEX IF NOT EXISTS idx_resources_archived ON resources(archived);
CREATE INDEX IF NOT EXISTS idx_companies_archived ON companies(archived);
