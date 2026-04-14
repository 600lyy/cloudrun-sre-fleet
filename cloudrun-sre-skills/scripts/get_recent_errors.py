import os
import json
import argparse
import time
from google.cloud import logging
from google.api_core import exceptions

def get_recent_errors(service_name, project_id=None, hours_back=1):
    project_id = project_id or os.environ.get("PROJECT_ID")
    if not project_id:
        print(json.dumps({"status": "error", "message": "Missing Project ID."}))
        return
    try:
        client = logging.Client(project=project_id)
        time_limit = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - hours_back * 3600))
        filter_str = (
            f'resource.type="cloud_run_revision" '
            f'AND resource.labels.service_name="{service_name}" '
            f'AND severity>=ERROR '
            f'AND timestamp>="{time_limit}"'
        )
        entries = list(client.list_entries(filter_=filter_str, max_results=10, order_by=logging.DESCENDING))
        if not entries:
             print(json.dumps({"status": "success", "errors_found": 0}))
             return
        error_summaries = []
        for entry in entries:
            payload = entry.payload
            timestamp = entry.timestamp.isoformat() if entry.timestamp else "unknown"
            msg = payload.get("message", payload.get("error", str(payload))) if isinstance(payload, dict) else str(payload)
            error_summaries.append(f"[{timestamp}] {str(msg)[:200]}")
        print(json.dumps({"status": "success", "errors_found": len(entries), "errors": error_summaries}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get recent error logs.')
    parser.add_argument('service_name', help='Cloud Run service name')
    parser.add_argument('--project_id', help='GCP Project ID')
    parser.add_argument('--hours', type=int, default=1, help='Hours back')
    args = parser.parse_args()
    get_recent_errors(args.service_name, args.project_id, args.hours)
