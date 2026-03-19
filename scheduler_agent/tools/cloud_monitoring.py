import time
import os
import asyncio

from google.cloud.monitoring_v3 import MetricServiceAsyncClient, TimeInterval, Aggregation


async def get_cloud_run_metrics(service_name: str, project_id: str = None) -> dict:
    """
    Expert Tool: Fetches CPU, Memory, and Requests in parallel.
    Includes robust error handling for API timeouts or permission issues.
    """
    client = MetricServiceAsyncClient()
    project_id = project_id or os.environ.get("PROJECT_ID", None)
    if not project_id:
        return {
            "status": "error",
            "message": "CRITICAL: No Project ID provided and Project ID not found in the env. I cannot access Google Cloud to verify egress-test."
        }

    project_name = f"projects/{project_id}"

    now = time.time()
    interval = TimeInterval(mapping={
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

        # aligner = Aggregation.Aligner.ALIGN_SUM if m_type == "requests" else Aggregation.Aligner.ALIGN_MEAN

        aggregation = Aggregation({
            "alignment_period": {"seconds": 60},
            "per_series_aligner": Aggregation.Aligner.ALIGN_DELTA,
            "cross_series_reducer": Aggregation.Reducer.REDUCE_MEAN,
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
    