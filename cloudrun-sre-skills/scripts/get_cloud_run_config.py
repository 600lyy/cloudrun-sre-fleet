import os
import json
import argparse
from google.cloud import run_v2
from google.api_core import exceptions

def get_cloud_run_config(service_name, project_id=None, region=None):
    try:
        client = run_v2.ServicesClient()
        project_id = project_id or os.environ.get("PROJECT_ID")
        region = region or os.environ.get("CLOUD_RUN_REGION") or "europe-west1"

        if not project_id:
            print(json.dumps({"status": "error", "message": "Missing Project ID."}))
            return
            
        resource_name = f"projects/{project_id}/locations/{region}/services/{service_name}"
        service = client.get_service(name=resource_name)
        
        template = service.template
        container = template.containers[0]
        scaling = template.scaling
        resources = container.resources
        
        config = {
            "status": "success",
            "service": service_name,
            "min_instances": scaling.min_instance_count or 0,
            "max_instances": scaling.max_instance_count or "default",
            "max_concurrency": template.max_instance_request_concurrency or 80,
            "memory_limit": resources.limits.get("memory", "unknown"),
            "cpu_limit": resources.limits.get("cpu", "unknown")
        }
        print(json.dumps(config))

    except exceptions.NotFound:
        print(json.dumps({"status": "error", "message": f"Service '{service_name}' not found."}))
    except exceptions.Unauthenticated:
        print(json.dumps({"status": "error", "message": "AUTH_FAILED: GCP credentials expired."}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get Cloud Run config.')
    parser.add_argument('service_name', help='Cloud Run service name')
    parser.add_argument('--project_id', help='GCP Project ID')
    parser.add_argument('--region', help='GCP Region')
    args = parser.parse_args()
    get_cloud_run_config(args.service_name, args.project_id, args.region)
