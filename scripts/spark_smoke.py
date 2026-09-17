"""Tiny synthetic DataFrame job on the standalone worker."""

import hashlib
import json
import shutil
import sys
import uuid
from pathlib import Path
from urllib.request import urlopen

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

with Path(sys.argv[1]).open() as request_file:
    request = json.load(request_file)
run_id = uuid.UUID(request["run_id"]).hex
path = Path("/tmp/yieldlens-smoke") / run_id
with urlopen(request["url"], timeout=20) as response:
    payload = response.read(4097)
if len(payload) > 4096 or hashlib.sha256(payload).hexdigest() != request["sha256"]:
    raise AssertionError("Raw object size/checksum mismatch")
record = json.loads(payload)
if record["synthetic"] is not True or record["run_id"] != run_id:
    raise AssertionError("Invalid smoke provenance")
spark = SparkSession.builder.appName("yieldlens-synthetic-smoke").getOrCreate()
try:
    frame = spark.createDataFrame([record]).repartition(2)
    frame.write.mode("errorifexists").parquet(str(path))
    restored = spark.read.parquet(str(path))
    if restored.count() != 1 or restored.schema != frame.schema:
        raise AssertionError("Parquet row count/schema mismatch")
    value = restored.agg(F.avg("soil_moisture").alias("mean")).first()["mean"]
    if value != 42.0:
        raise AssertionError("Unexpected Spark aggregate")
    print(
        "YIELDLENS_RESULT="
        + json.dumps(
            {
                "synthetic": True,
                "rows": 1,
                "mean_moisture": value,
                "schema": restored.schema.simpleString(),
                "spark_version": spark.version,
                "master": spark.sparkContext.master,
            }
        )
    )
finally:
    spark.stop()
    if path.exists():
        shutil.rmtree(path)
