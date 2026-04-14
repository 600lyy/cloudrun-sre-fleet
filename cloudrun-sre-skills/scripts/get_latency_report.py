import os
import json
import argparse
import asyncio
import httpx
import google.auth
import google.auth.transport.requests

async def get_latency_report(service_name, project_id=None, end_timestamp=None):
    project_id = project_id or os.environ.get("PROJECT_ID")
    if not project_id:
        print(json.dumps({"status": "error", "message": "Missing Project ID."}))
        return

    credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    
    url = f"https://monitoring.googleapis.com/v1/projects/{project_id}/location/global/prometheus/api/v1/query"
    headers = {"Authorization": f"Bearer {credentials.token}"}

    async def fetch_promql(promql):
        params = {"query": promql}
        if end_timestamp:
            params["time"] = end_timestamp
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("data", {}).get("result", [])
                if results:
                    val = results[0]["value"][1]
                    return float(val) if val != "NaN" else 0.0
                return 0.0
            except Exception as e:
                return f"Error: {str(e)}"

    metric_latency = "run_googleapis_com:request_latency_e2e_latencies_bucket"
    metric_requests = "run_googleapis_com:request_count"
    filter_str = f"monitored_resource='cloud_run_revision', service_name='{service_name}'"

    tasks = [
        fetch_promql(f"histogram_quantile(0.50, sum by (le) (increase({metric_latency}{{{filter_str}}}[5m])))"),
        fetch_promql(f"histogram_quantile(0.95, sum by (le) (increase({metric_latency}{{{filter_str}}}[5m])))"),
        fetch_promql(f"histogram_quantile(0.99, sum by (le) (increase({metric_latency}{{{filter_str}}}[5m])))"),
        fetch_promql(f"histogram_quantile(0.50, sum by (le) (increase({metric_latency}{{{filter_str}}}[1h])))"),
        fetch_promql(f"histogram_quantile(0.99, sum by (le) (increase({metric_latency}{{{filter_str}}}[1h])))"),
        fetch_promql(f"sum(rate({metric_requests}{{{filter_str}}}[5m]))"),
        fetch_promql(f"sum(rate({metric_requests}{{{filter_str}}}[1h]))"),
        fetch_promql(f"histogram_quantile(0.50, sum by (le) (increase(run_googleapis_com:request_latency_ingress_to_region_bucket{{{filter_str}}}[5m])))"),
        fetch_promql(f"histogram_quantile(0.50, sum by (le) (increase(run_googleapis_com:request_latency_pending_bucket{{{filter_str}}}[5m])))"),
        fetch_promql(f"histogram_quantile(0.50, sum by (le) (increase(run_googleapis_com:request_latency_routing_bucket{{{filter_str}}}[5m])))"),
        fetch_promql(f"histogram_quantile(0.50, sum by (le) (increase(run_googleapis_com:request_latency_user_execution_bucket{{{filter_str}}}[5m])))"),
        fetch_promql(f"histogram_quantile(0.50, sum by (le) (increase(run_googleapis_com:request_latency_response_egress_bucket{{{filter_str}}}[5m])))"),
        fetch_promql(f"histogram_quantile(0.50, sum by (le) (increase(run_googleapis_com:container_max_request_concurrencies_bucket{{{filter_str}}}[5m])))"),
        fetch_promql(f"histogram_quantile(0.95, sum by (le) (increase(run_googleapis_com:container_max_request_concurrencies_bucket{{{filter_str}}}[5m])))"),
        fetch_promql(f"sum(avg_over_time(run_googleapis_com:container_instance_count{{{filter_str}, state='idle'}}[5m]))"),
    ]
    
    report_data = await asyncio.gather(*tasks)
    
    report = {
        "service": service_name,
        "p50_ms": report_data[0], "p95_ms": report_data[1], "p99_ms": report_data[2],
        "baseline_1h_p50_ms": report_data[3], "baseline_1h_p99_ms": report_data[4],
        "req_rate_rps": report_data[5], "baseline_1h_req_rate_rps": report_data[6],
        "ingress_ms": report_data[7], "pending_ms": report_data[8], "routing_ms": report_data[9],
        "user_exec_ms": report_data[10], "egress_ms": report_data[11],
        "concurrency_p50": report_data[12], "concurrency_p95": report_data[13],
        "idle_instances": report_data[14]
    }
    print(json.dumps(report))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get Latency Report.')
    parser.add_argument('service_name', help='Cloud Run service name')
    parser.add_argument('--project_id', help='GCP Project ID')
    parser.add_argument('--time', help='End timestamp (Unix epoch)')
    args = parser.parse_args()
    asyncio.run(get_latency_report(args.service_name, args.project_id, args.time))
