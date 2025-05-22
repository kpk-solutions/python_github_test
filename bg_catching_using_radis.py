#!/usr/bin/env python3
"""
This script fetches filtered data from BigQuery.
It uses Redis to cache results for faster subsequent access.

✅ Setup Instructions:

1. Install Python packages:
   pip install redis google-cloud-bigquery

2. Start Redis server (if not running):
   sudo apt update && sudo apt install redis
   sudo systemctl start redis

3. Export your Google Cloud credentials:
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account.json"

4. Run the script:
   python3 bigquery_cache_handler.py "some_filter_value"
"""

import redis
import json
import sys
from google.cloud import bigquery

# ----------- Configuration Section -----------

# Connect to Redis server (default localhost)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Connect to BigQuery (Google credentials must be set)
bq_client = bigquery.Client()

# Time-to-live for cache (in seconds)
CACHE_TTL = 300  # 5 minutes

# ----------- Function to Get Data -----------

def get_data_from_bigquery(filter_val):
    """
    Get data from Redis cache or BigQuery if cache is not available.
    """
    cache_key = f"query_{filter_val}"

    # Step 1: Check Redis
    cached_data = redis_client.get(cache_key)
    if cached_data:
        print("[INFO] Returning data from Redis cache.")
        return json.loads(cached_data)

    # Step 2: Query BigQuery
    print("[INFO] Querying BigQuery...")
    query = """
        SELECT * 
        FROM `your_project.your_dataset.your_table`
        WHERE your_column = @filter_val
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("filter_val", "STRING", filter_val)
        ]
    )

    query_job = bq_client.query(query, job_config=job_config)
    rows = list(query_job.result())
    result_data = [dict(row) for row in rows]

    # Step 3: Cache the result in Redis
    redis_client.setex(cache_key, CACHE_TTL, json.dumps(result_data))

    return result_data

# ----------- Entry Point -----------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 bigquery_cache_handler.py <filter_val>")
        sys.exit(1)

    filter_input = sys.argv[1]
    results = get_data_from_bigquery(filter_input)

    print(json.dumps(results, indent=2))
