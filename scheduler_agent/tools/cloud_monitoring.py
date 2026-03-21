import time
import os
import asyncio
import httpx


import google.auth
import google.auth.transport.requests
from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import MetricServiceAsyncClient, TimeInterval, Aggregation, QueryServiceAsyncClient, QueryTimeSeriesRequest


async def get_cloud_run_metrics(service_name: str, project_id: str = None) -> dict:
    """
    Expert Tool: Fetches CPU, Memory, and Requests in parallel.
    Includes robust error handling for API timeouts or permission issues.
    """
    client = monitoring_v3.MetricServiceAsyncClient()
    project_id = project_id or os.environ.get("PROJECT_ID", None)
    if not project_id:
        return {
            "status": "error",
            "message": "CRITICAL: No Project ID provided and Project ID not found in the env. I cannot access Google Cloud to verify egress-test."
        }

    project_name = f"projects/{project_id}"

    now = time.time()
    interval = monitoring_v3.TimeInterval(mapping={
        "end_time": {"seconds": int(now)},
        "start_time": {"seconds": int(now - 300)},
        }
    )

    metrics = {
        "cpu": "run.googleapis.com/container/cpu/utilizations",
        "memory": "run.googleapis.com/container/memory/utilizations",
        "requests": "run.googleapis.com/request_count"
    }

    async def fetch_one(m_type, m_path):
        filter_str = (
            f'resource.type = "cloud_run_revision" AND '
            f'resource.labels.service_name = "{service_name}" AND '
            f'metric.type = "{m_path}"'
        )

        aggregation = monitoring_v3.Aggregation({
            "alignment_period": {"seconds": 60},
            "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_DELTA,
            "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_MEAN,
            "group_by_fields": ["resource.label.service_name"],
        })
        
        results = await client.list_time_series(request={
            "name": project_name,
            "filter": filter_str,
            "interval": interval,
            "aggregation": aggregation,
        })

        try:
            points = []
            async for page in results:
                for point in page.points:
                    val = point.value.double_value if "utilization" in m_path else point.value.int64_value
                    points.append(val)
            
            avg_val = round(sum(points) / len(points), 4) if points else 0.0
            return m_type, avg_val
        except Exception as e:
            return m_type, f"Error: {str(e)}"
        
    try:
        tasks = [fetch_one(k, v) for k, v in metrics.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and identify if any specific metric failed
        metrics_summary = {}
        errors = []

        for res in results:
            if isinstance(res, Exception):
                errors.append(f"System Error: {str(res)}")
                continue
            
            m, v = res
            if isinstance(v, str) and v.startswith("Error"):
                errors.append(f"{m}: {v}")
            else:
                metrics_summary[m]=v

        return {
            "status": "partial_success" if errors and metrics_summary else "success" if not errors else "error",
            "service": service_name,
            "data": metrics_summary,
            "errors": errors if errors else None
        }
    except exceptions.Unauthenticated:
        # This stops the tool and tells the LLM EXACTLY what happened
        raise RuntimeError("TERMINAL_AUTH_ERROR: Re-authentication required.")
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

async def get_service_latency_report(service_name: str, project_id: str) -> dict:
    """
    Fetches p50 and p99 latency for a Cloud Run service in parallel.
    Uses the native Prometheus HTTP API to bypass MQL parsing errors.
    """
    # 1. Auth: Get Bearer token for the specific project scope
    credentials, _ = google.auth.default(
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    
    url = f"https://monitoring.googleapis.com/v1/projects/{project_id}/location/global/prometheus/api/v1/query"
    headers = {"Authorization": f"Bearer {credentials.token}"}

    async def fetch(metric_name: str, percentile: float):
        promql = (
            f"histogram_quantile({percentile}, sum by (le) ("
            f"increase({metric_name}{{"
            f"monitored_resource='cloud_run_revision', "
            f"service_name='{service_name}'}}[5m])))"
        )
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, params={"query": promql})
                resp.raise_for_status()
                data = resp.json()
                results = data.get("data", {}).get("result", [])
                return float(results[0]["value"][1]) if results else 0.0
            except Exception as e:
                return f"Error: {str(e)}"

    # Parallel Execution of fetching metrics
    tasks = [
        fetch("run_googleapis_com:request_latency_e2e_latencies_bucket", 0.50),
        fetch("run_googleapis_com:request_latency_e2e_latencies_bucket", 0.90),
        fetch("run_googleapis_com:request_latency_e2e_latencies_bucket", 0.99),
        fetch("run_googleapis_com:request_latency_ingress_to_region_bucket", 0.50),
        fetch("run_googleapis_com:request_latency_pending_bucket", 0.50),
        fetch("run_googleapis_com:request_latency_routing_bucket", 0.50),
        fetch("run_googleapis_com:request_latency_user_execution_bucket", 0.50),
        fetch("run_googleapis_com:request_latency_response_egress_bucket", 0.50),
        fetch("run_googleapis_com:container_max_request_concurrencies_bucket", 0.50),
    ]
    
    report_data = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        "service": service_name,
        "project": project_id,
        "p50_latency_ms": report_data[0],
        "p95_latency_ms": report_data[1],
        "p99_latency_ms": report_data[2],
        "ingress_latecny_ms": report_data[3],
        "pending_latency_ms": report_data[4],
        "routing_latency_ms": report_data[5],
        "user_execution_latency_ms": report_data[6],
        "egress_latency_ms": report_data[7],
        "unit": "millionseconds"
    }