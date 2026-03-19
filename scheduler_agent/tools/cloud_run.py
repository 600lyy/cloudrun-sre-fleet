import os

from google.cloud import run_v2
from google.api_core import exceptions

def get_cloud_run_config(service_name: str, project_id: str = None, region: str = None) -> dict:
    """
    Retrieves the live configuration of a Cloud Run service (v2).
    Returns: min_instances, max_concurrency, and memory limits.
    """
    try:
        client = run_v2.ServicesClient()
        project_id = project_id or os.environ.get("PROJECT_ID", None)
        region = region or os.environ.get("CLOUD_RUN_REGION") or "europe-west1"

        if not project_id:
            return {
                "status": "missing_info",
                "parameter": "project_id",
                "message": "I need a Project ID to access the service configuration."
            }
            
        # The fully qualified name: projects/{project}/locations/{location}/services/{service}
        resource_name = f"projects/{project_id}/locations/{region}/services/{service_name}"
        
        service = client.get_service(name=resource_name)
        
        # Extracting scaling and resource settings from the first container in the template
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
        
        print(f"\n[REAL-TIME AUDIT] Fetched config for {service_name}: {config}")
        return config

    except exceptions.NotFound:
        return {"status": "error", "message": f"Service '{service_name}' not found in {region}."}
    except exceptions.Unauthenticated:
        return {
            "status": "error", 
            "message": "AUTH_FAILED: Your GCP credentials have expired. Run 'gcloud auth application-default login'."
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch config: {str(e)}"}

def patch_cloud_run_config(service_name: str, min_instances: int, max_concurrency: int) -> dict:
    """
    Updates the Cloud Run service configuration.
    Use this to pre-warm (min_instances) or tune engine performance (max_concurrency).
    """
    # V1: Mocking the execution. In V2, this calls the Cloud Run Admin API.
    print(f"\n[EXECUTION] Patching {service_name}:")
    print(f"  -> min-instances: {min_instances}")
    print(f"  -> max-concurrency: {max_concurrency}")
    
    return {
        "status": "success",
        "service": service_name,
        "applied": {"min_instances": min_instances, "concurrency": max_concurrency}
    }
