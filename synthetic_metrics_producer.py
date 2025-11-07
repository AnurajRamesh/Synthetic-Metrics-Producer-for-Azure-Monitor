"""
synthetic_metrics_producer.py

Generates synthetic CPU% and latency_ms time-series and uploads them
to Azure Monitor using the Logs Ingestion client (azure-monitor-ingestion).

Environment variables required:
 - DATA_COLLECTION_ENDPOINT  
 - LOGS_DCR_RULE_ID         
 - LOGS_DCR_STREAM_NAME     
 - AZURE_CLIENT_ID
 - AZURE_TENANT_ID
 - AZURE_CLIENT_SECRET

Run: python synthetic_metrics_producer.py
Author: Anuraj Ramesh
Date: 2025-11-07
"""
import os
import time
import random
from datetime import datetime, timezone
from azure.identity import ClientSecretCredential
from azure.monitor.ingestion import LogsIngestionClient
from tenacity import retry, wait_exponential, stop_after_attempt
from dotenv import load_dotenv

load_dotenv()

# Config (use env vars)
ENDPOINT = os.environ.get("DATA_COLLECTION_ENDPOINT")
RULE_ID = os.environ.get("LOGS_DCR_RULE_ID")
STREAM_NAME = os.environ.get("LOGS_DCR_STREAM_NAME")

if not (ENDPOINT and RULE_ID and STREAM_NAME):
    raise SystemExit("Set DATA_COLLECTION_ENDPOINT, LOGS_DCR_RULE_ID, LOGS_DCR_STREAM_NAME")

# Use ClientSecretCredential for demo (local). Replace with DefaultAzureCredential / ManagedIdentity in prod.
credential = ClientSecretCredential(
    tenant_id=os.environ["AZURE_TENANT_ID"],
    client_id=os.environ["AZURE_CLIENT_ID"],
    client_secret=os.environ["AZURE_CLIENT_SECRET"],
)

client = LogsIngestionClient(endpoint=ENDPOINT, credential=credential)

def synthetic_point(base_cpu=25.0, base_latency=50.0, spike_prob=0.05):
    """
    Returns a dict representing a single synthetic observation with Time, cpu_percent, latency_ms and host.
    We'll create occasional spikes for realism.
    """
    time_now = datetime.now(timezone.utc).isoformat()
    # baseline noise
    cpu = max(0.0, random.gauss(base_cpu, 5.0))
    latency = max(1.0, random.gauss(base_latency, 10.0))

    # occasional CPU spike
    if random.random() < spike_prob:
        cpu += random.uniform(30, 60)
        latency += random.uniform(100, 400)

    # small diurnal variation (simulate sine wave)
    t = time.time()
    cpu += 10.0 * (0.5 + 0.5 * (random.random() - 0.5)) * (1 + 0.5 * (random.random() - 0.5))

    return {
        "TimeGenerated": time_now,
        "Host": "synthetic-host-1",
        "cpu_percent": round(cpu, 2),
        "latency_ms": round(latency, 2),
        "tags": {"env": "dev", "source": "synthetic-producer"}
    }

@retry(wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(5))
def upload_batch(batch):
    """
    Upload a batch of records to the DCR stream. Tenacity retry handles transient failures.
    """
    # client.upload will raise HttpResponseError on failures
    client.upload(rule_id=RULE_ID, stream_name=STREAM_NAME, logs=batch)
    print(f"Uploaded {len(batch)} records at {datetime.now(timezone.utc).isoformat()}")

def main(cadence_seconds=5, batch_size=10):
    """
    Produce metrics continuously. Aggregates `batch_size` points then upload.
    cadence_seconds: seconds between produced points
    """
    batch = []
    try:
        while True:
            pt = synthetic_point()
            batch.append(pt)
            # flush by size
            if len(batch) >= batch_size:
                upload_batch(batch)
                batch = []
            # Or flush by time — here we simply sleep for cadence
            time.sleep(cadence_seconds)
    except KeyboardInterrupt:
        if batch:
            print("Flushing final batch...")
            upload_batch(batch)
        print("Shutting down producer.")

if __name__ == "__main__":
    main(cadence_seconds=1, batch_size=20)