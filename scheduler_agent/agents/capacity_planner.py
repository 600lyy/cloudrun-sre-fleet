from google.adk.agents import LlmAgent
from google.adk.tools import load_memory
from ._prompts import CAPACITY_PLANNER_SYSTEM_PROMPT

from scheduler_agent.tools.cloud_monitoring import get_cloud_run_metrics, get_service_latency_report
from scheduler_agent.tools.cloud_run import get_cloud_run_config, patch_cloud_run_config


class CapacityPlanner(LlmAgent):
    def __init__(self):
        super().__init__(
            name="CapacityPlanner",
            description=""""
                Specialist for capacity planning and event-based scaling. 
                Use this agent to schedule workloads for upcoming events (Flash Deals, Campaigns)
                or to get advisory on resource optimization and min/max instances.
            """,
            model="gemini-2.5-flash",
            instruction=CAPACITY_PLANNER_SYSTEM_PROMPT,
            tools=[
                get_cloud_run_config,
                get_cloud_run_metrics,
                patch_cloud_run_config,
                get_service_latency_report,
                load_memory,
            ]
        )
