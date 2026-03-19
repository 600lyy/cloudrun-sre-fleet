from google.adk.agents import LlmAgent
from ._prompts import LATENCY_EXPERT_SYSTEM_PROMPT

from scheduler_agent.tools.cloud_monitoring import get_cloud_run_metrics
from scheduler_agent.tools.cloud_run import get_cloud_run_config, patch_cloud_run_config


class LatencyExpert(LlmAgent):
    def __init__(self):
        super().__init__(
            name="LatencyExpert",
            description=""""
                Specialist for high-traffic, external-facing APIs. 
                Use this agent for services where p99 latency, response times, 
                and avoiding cold starts are the top priorities.
            """,
            model="gemini-2.5-flash",
            instruction=LATENCY_EXPERT_SYSTEM_PROMPT, # Imported from _prompts.py
            tools=[
                get_cloud_run_config,
                get_cloud_run_metrics,
                patch_cloud_run_config,
            ]
        )
