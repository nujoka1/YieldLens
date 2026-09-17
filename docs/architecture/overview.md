# YieldLens Nigeria Architecture

```mermaid
flowchart LR
    POWER[NASA POWER daily climate]
    SOIL[ISRIC SoilGrids properties]
    FAO[FAOSTAT annual crop data]
    IOT[Synthetic IoT telemetry]

    PY[Python acquisition and validation]
    KAFKA[Apache Kafka streams]
    MINIO[(MinIO object lake)]
    PARQUET[Partitioned Parquet zones]
    SPARK[Apache Spark / PySpark]
    MLLIB[Spark MLlib risk and forecasting]
    POSTGRES[(PostgreSQL serving layer)]
    UI[Streamlit / Plotly dashboard]

    POWER --> PY
    SOIL --> PY
    FAO --> PY
    IOT --> KAFKA
    PY --> KAFKA
    PY --> MINIO
    KAFKA --> MINIO
    MINIO --> PARQUET
    PARQUET --> SPARK
    SPARK --> MLLIB
    MLLIB --> POSTGRES
    POSTGRES --> UI
```

This is the target end-to-end architecture. Phase 1 provisions only the platform components and application foundation; arrows representing acquisition, processing, analytics, and delivery are contracts for later approved phases, not claims of completed integration.
