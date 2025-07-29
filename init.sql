-- Initialize the migrate_dev database
-- This script runs when the PostgreSQL container starts

-- Create the database if it doesn't exist
SELECT 'CREATE DATABASE migrate_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'migrate_dev')\gexec

-- Connect to the migrate_dev database
\c migrate_dev;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Log successful initialization
SELECT 'Database migrate_dev initialized successfully' as status; 