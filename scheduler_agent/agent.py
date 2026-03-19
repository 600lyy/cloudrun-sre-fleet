from google.adk.agents import LlmAgent
from .agents.latency_expert import LatencyExpert

root_agent = LlmAgent(
    name="SRECoordinator",
    model="gemini-2.5-flash",
    instruction="""
        You are the traffic controller for the SRE Fleet. 
        Your job is to identify if a service is an External-Facing API 
        and route the request to the LatencyExpert.
    """,
    sub_agents=[
        LatencyExpert(),
        ],
)
