import os
import time

from google.cloud import logging
from google.api_core import exceptions

def get_recent_errors(service_name: str, project_id: str = None, hours_back: int = 1) -> dict:
    """
    Expert Tool: Fetches recent ERROR-level logs for a specific Cloud Run service.
    Use this to correlate latency spikes or saturation with actual application crashes (e.g., OOM, timeouts).
    """
    project_id = project_id or os.environ.get("PROJECT_ID", None)
    if not project_id:
        return {
            "status": "error",
            "message": "CRITICAL: No Project ID provided and Project ID not found in the env. I cannot access Google Cloud Logging."
        }

    try:
        client = logging.Client(project=project_id)
        
        # Calculate timestamp for filter
        time_limit = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - hours_back * 3600))
        
        # Construct the advanced logs filter
        # Target specific Cloud Run revision resource and filter for ERROR or higher
        filter_str = (
            f'resource.type="cloud_run_revision" '
            f'AND resource.labels.service_name="{service_name}" '
            f'AND severity>=ERROR '
            f'AND timestamp>="{time_limit}"'
        )
        
        print(f"\n[REAL-TIME AUDIT] Fetching recent errors for {service_name} (Last {hours_back}h)...")
        
        # Fetch entries (limit to 10 to avoid overwhelming context)
        entries = list(client.list_entries(filter_=filter_str, max_results=10, order_by=logging.DESCENDING))
        
        if not entries:
             return {
                 "status": "success",
                 "service": service_name,
                 "errors_found": 0,
                 "message": "No ERROR-level logs found in the specified timeframe."
             }
             
        error_summaries = []
        for entry in entries:
            # Logs can be textPayload or jsonPayload
            payload = entry.payload
            timestamp = entry.timestamp.isoformat() if entry.timestamp else "unknown"
            
            if isinstance(payload, str):
                summary = f"[{timestamp}] {payload[:200]}"
            elif isinstance(payload, dict):
                # Try to extract common error fields from JSON
                msg = payload.get("message", payload.get("error", str(payload)))
                # Convert dict to string if it's still a dict, and truncate
                msg_str = str(msg)[:200]
                summary = f"[{timestamp}] {msg_str}"
            else:
                summary = f"[{timestamp}] Unknown payload format"
                
            error_summaries.append(summary)
            
        return {
            "status": "success",
            "service": service_name,
            "errors_found": len(entries),
            "recent_errors": error_summaries
        }
        
    except exceptions.Unauthenticated:
        raise RuntimeError("TERMINAL_AUTH_ERROR: Re-authentication required.")
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch logs: {str(e)}"}
