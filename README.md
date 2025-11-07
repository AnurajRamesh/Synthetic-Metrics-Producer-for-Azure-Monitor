# Synthetic Metrics Producer for Azure Monitor

This Python script (`synthetic_metrics_producer.py`) generates synthetic CPU% and latency time-series data and uploads them to Azure Monitor using the **Logs Ingestion API** via the `azure-monitor-ingestion` SDK.

It is useful for testing or validating custom log ingestion setups in Azure Monitor.

---

## Overview

The script:

- Generates synthetic `cpu_percent` and `latency_ms` metrics.
- Sends these metrics to a Data Collection Rule (DCR) stream through a Data Collection Endpoint (DCE).
- Uses Azure AD credentials (Client ID, Tenant ID, Secret) to authenticate with Azure Monitor.

---

## Prerequisites

Before running the script, ensure you have:

1. **Python 3.8+**
2. Installed the following dependencies:

```bash
pip install -r requirements.txt
```

3. Access to an **Azure subscription** with permission to create:
   - A **Data Collection Endpoint (DCE)**
   - A **Data Collection Rule (DCR)**
   - An **Azure AD App Registration** (for authentication)

---

## Environment Variables Setup

The script reads required configuration from environment variables (using `.env` if present).  
Below explains how to obtain each one from Azure.

### 1. DATA_COLLECTION_ENDPOINT

This is the **Data Collection Endpoint (DCE)** ingestion URL.

**Steps:**

1. Go to **Azure Portal** → **Monitor** → **Data Collection Endpoints**.
2. Select your DCE or create one if needed.
3. Copy the **Logs Ingestion** from the Overview page.

Example value:

```
https://testdce.germanywestcentral.ingest.monitor.azure.com
```

Set it in your environment file '.env':

```bash
DATA_COLLECTION_ENDPOINT=https://testdce.germanywestcentral.ingest.monitor.azure.com
```

---

### 2. LOGS_DCR_RULE_ID

This is the **Resource ID** of your Data Collection Rule (DCR).

**Steps:**

1. In the Azure Portal → **Monitor** → **Data Collection Rules**.
2. Select your rule or create one if needed.
3. Copy the **immutable ID** from the Properties page.

Example value:

```
dcr-abc123e2a4fpqrstu79137be9ae0949d
```

Set it in your environment file:

```bash
LOGS_DCR_RULE_ID=dcr-abc123e2a4fpqrstu79137be9ae0949d
```

---

### 3. LOGS_DCR_STREAM_NAME

This is the **stream name** configured in your DCR for custom logs.

**Steps:**

1. Open your DCR Overview in the Azure Portal.
2. Navigate to the **dataSources** tab.
3. Find the stream name under the logFiles, usually of the form:
   ```
   Custom-<TableName>_CL
   ```

Example:

```
Custom-Metrics_CL
```

Set it in your environment file:

```bash
LOGS_DCR_STREAM_NAME=Custom-Metrics_CL
```

---

### 4. AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET

These are from your **Azure AD App Registration** used for authentication.

**Steps:**

1. In the Azure Portal → Search for **Microsoft Entra ID** → Go to **App registrations**.
2. Register a new app (or use an existing one).
3. Copy these values:
   - **Application (client) ID** → `AZURE_CLIENT_ID`
   - **Directory (tenant) ID** → `AZURE_TENANT_ID`
4. Under **Certificates & Secrets** on the left side, create a **New client secret**.
   - Copy the **Value** → `AZURE_CLIENT_SECRET`

Grant the app permissions:

- Go to your **DCR** → **Access control (IAM)** on left side.
- Add role assignment:
  - Role: **Monitoring Metrics Publisher** (or **Monitoring Contributor**)
  - Member: the app you just created.

Set it in your environment file:

```bash
AZURE_CLIENT_ID=aaaa1111-bbbb-2222-cccc-3333dddd4444
AZURE_TENANT_ID=11111111-2222-3333-4444-555555555555
AZURE_CLIENT_SECRET=uniquesecretvalue
```

---

## Running the Script

Once environment variables are set, you can run:

```bash
python synthetic_metrics_producer.py
```

The script will continuously generate and upload synthetic data to Azure Monitor.  
Press `Ctrl+C` to stop gracefully.

---

## Example `.env` File

If using `python-dotenv`, create a `.env` file in the same directory as your script:

```
DATA_COLLECTION_ENDPOINT=https://testdce.germanywestcentral.ingest.monitor.azure.com
LOGS_DCR_RULE_ID=dcr-abc123e2a4fpqrstu79137be9ae0949d
LOGS_DCR_STREAM_NAME=Custom-Metrics_CL
AZURE_CLIENT_ID=aaaa1111-bbbb-2222-cccc-3333dddd4444
AZURE_TENANT_ID=11111111-2222-3333-4444-555555555555
AZURE_CLIENT_SECRET=uniquesecretvalue
```

Then simply run:

```bash
python synthetic_metrics_producer.py
```

---

## Monitoring Logs in Azure

- Go to the Log Analytics Workspace (LAW) → Select the created LAW
- In the Logs → Select the Kusto Query Language (KQL) Mode
- Type below code to view the last 10 logs:

```bash
  Metrics_CL
  | sort by TimeGenerated desc
  | take 10
```

## Notes

- Ensure the **DCE** and **DCR** are in the **same Azure region**.
- The service principal must have ingestion permissions for the DCR.
- You can adjust the data rate and batch size in `main()`.
