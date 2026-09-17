-- Runs only when PostgreSQL initializes an empty data volume.
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS metadata;

COMMENT ON SCHEMA analytics IS 'Dashboard-ready aggregates created in later phases';
COMMENT ON SCHEMA metadata IS 'Pipeline run and dataset provenance metadata';
