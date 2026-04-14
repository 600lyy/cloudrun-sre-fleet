import json
import argparse

def patch_cloud_run(service_name, min_instances=None, max_concurrency=None):
    # Simulated execution
    print(json.dumps({
        "status": "success",
        "service": service_name,
        "applied": {"min_instances": min_instances, "max_concurrency": max_concurrency},
        "note": "This is a simulated execution of a Cloud Run config patch."
    }))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Patch Cloud Run config.')
    parser.add_argument('service_name', help='Cloud Run service name')
    parser.add_argument('--min_instances', type=int, help='Min instances')
    parser.add_argument('--max_concurrency', type=int, help='Max concurrency')
    args = parser.parse_args()
    patch_cloud_run(args.service_name, args.min_instances, args.max_concurrency)
