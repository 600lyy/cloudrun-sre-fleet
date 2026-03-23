# CloudRun SRE Fleet

An AI-powered Site Reliability Engineering (SRE) automation platform built using the `google-adk` framework. This project is designed to autonomously audit, monitor, and manage Google Cloud Run services through a multi-agent system.

## Overview

The SRE Fleet operates as a highly specialized assistant for managing external-facing APIs and internal batch processes on Google Cloud Run. It focuses on maintaining the "Sweet Spot" for services: zero cold starts, sub-300ms p99 latency, and sufficient headroom for traffic spikes, while actively optimizing costs.

The system is designed to run in two primary modes:
1. **Interactive Mode (Advisory):** Users can chat with the SRE agents to investigate latency spikes, analyze current configurations, or plan capacity for upcoming events.
2. **Watchdog Mode (Proactive):** The system continuously monitors service health and generates actionable suggestions when performance thresholds are breached.

## Agent Architecture

The application uses a hierarchical agent structure to route requests and perform specialized tasks.

### 1. SRECoordinator (`scheduler_agent/agent.py`)
The primary traffic controller. It uses a `SERVICE_GROUPS` map to classify services (e.g., `tier_1_apis`, `internal_batch`) and routes user requests based on intent:
- **Audits:** Routes performance and latency investigations to the `LatencyExpert`.
- **Event Planning:** Routes capacity scheduling and scaling advisory to the `CapacityPlanner`.

### 2. LatencyExpert (`scheduler_agent/agents/latency_expert.py`)
A specialized sub-agent dedicated to technical reports and latency root-cause analysis.
- **Dynamic Spike Detection:** Compares real-time 5-minute p99 latency against a 1-hour rolling baseline to detect true latency spikes.
- **Traffic Correlation:** Analyzes request rates to distinguish between autoscaling lag (Cold Starts) and system bottlenecks (Database Locks).
- **Bin-Packing Analysis:** Monitors `max_concurrency_p95` to identify when containers are saturated and need horizontal scaling.
- **Cost Optimization:** Identifies idle instances and recommends downscaling to prevent financial waste.

### 3. CapacityPlanner (`scheduler_agent/agents/capacity_planner.py`)
A specialized sub-agent for event-based scaling and capacity advisory.
- **Event Scaling Roadmaps:** Generates structured plans for upcoming traffic surges (e.g., Flash Deals, Black Friday).
- **Pre-warming:** Recommends proactive `min_instances` tuning to eliminate cold starts before an event begins.
- **Memory Safety:** Advises on `max_concurrency` caps to prevent Out-of-Memory (OOM) crashes during heavy load.

## Tools Layer

The agents interact with Google Cloud Platform via specialized tools located in `scheduler_agent/tools/`:

- `cloud_monitoring.py`: Fetches real-time performance metrics (CPU, Memory, Requests) and granular PromQL latency histograms (p50, p95, p99, max concurrency, idle instances) directly from Google Cloud Monitoring.
- `cloud_run.py`: Interacts with the Cloud Run API to inspect live service configurations (limits, scaling) and simulate configuration patches.

## Installation & Setup

This project uses `uv` for package management and the `google-adk` framework for agent orchestration.

### Prerequisites
- Python 3.12+
- `uv` installed (`pip install uv`)
- Google Cloud SDK (`gcloud`)

### Setup
1. Clone the repository.
2. Install the required dependencies:
   ```bash
   uv sync
   ```
   The project depends on the following key packages:
   - `google-adk`: Agent Development Kit for the multi-agent system.
   - `google-cloud-monitoring`: To fetch metrics and p99 latency histograms.
   - `google-cloud-run`: To inspect and tune service configurations.
   - `httpx`: For asynchronous Prometheus API calls.

3. Authenticate with Google Cloud:
   ```bash
   gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/userinfo.email,openid
   ```

4. Export your GCP Project ID:
   ```bash
   gcloud config set project "your-project-id"
   ```

## Usage & Testing

To test the agents, ensure your Google Cloud credentials are set up (`gcloud auth application-default login`) and the `PROJECT_ID` environment variable is exported.

### Starting the Agent Interface
Run the following command to start the interactive web interface for your SRE agents:
```bash
uv run adk web main:fleet_coordinator
```
This will launch a local web server where you can chat directly with the SRE Coordinator.

### Example Queries for the LatencyExpert (Interactive Audit)
- *"Why did the `auth-svc` latency spike in the last 5 minutes?"*
- *"Can you perform a full technical audit of `gccrfiletransfereuw101`?"*
- *"Are we currently overprovisioned on `data-processor`?"*

### Example Queries for the CapacityPlanner (Event Planning)
- *"We have a Flash Deal starting for the `auth-svc` at 2 PM today. What should our scaling strategy be?"*
- *"Can you check the current scaling profile for `gccrfiletransfereuw101` and advise if we are ready for a 5x traffic spike?"*
- *"I'm worried about OOM crashes during the next big batch run for the `image-resizer`. What `max-concurrency` do you recommend we set?"*
