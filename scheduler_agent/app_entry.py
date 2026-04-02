import os
import logging
import google.auth
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging

from scheduler_agent.agent_utils.telemetry import setup_telemetry

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize telemetry and auth
setup_telemetry()
_, project_id = google.auth.default()

# Point to the root directory where scheduler_agent lives
AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

# This creates the FastAPI server that ADK uses internally to host your agents
app = get_fast_api_app(
    agents_dir=AGENT_ROOT,
    web=True, # Enable the built-in UI
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    otel_to_cloud=True,
)

app.title = "CloudRun SRE Fleet"
app.description = "API for interacting with the SRE Fleet Agents"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
