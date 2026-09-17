# Data Lifecycle Contract

No dataset currently exists in this repository. These zones define the contract for future phases.

| Zone | Purpose | Mutation rule |
|---|---|---|
| Raw | Exact acquired API payloads and captured Kafka batches with provenance | Append-only; never silently corrected |
| Bronze | Parsed, schema-enforced records retaining source fields | Rebuildable from raw |
| Silver | Cleaned, normalized and joined analytical records | Rebuildable and versioned |
| Gold | Model features and dashboard-ready aggregates | Rebuildable and release-tagged |

Local `data/raw`, `data/bronze`, `data/silver`, and `data/gold` directories are ignored staging areas. MinIO is the authoritative development object store once ingestion is implemented.

Future objects must record source, acquisition time in UTC, source period, schema version, checksum where practical, and pipeline version. Synthetic IoT data must be unambiguously marked synthetic and generated from a versioned seed/configuration. It must never be presented as a real Nigerian farm observation.
