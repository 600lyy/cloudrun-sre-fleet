from google.adk.agents import LlmAgent
from google.adk.apps import App

from .agents.latency_expert import LatencyExpert
from .agents.capacity_planner import CapacityPlanner
from .plugins import TokenUsagePlugin

SERVICE_GROUPS = {
    "tier_1_apis": ["gccrfiletransfereuw101", "gccrpdhproductapifavoriteseuw101", "auth-svc"],
    "internal_batch": ["data-processor", "image-resizer"],
    "legacy_backbone": ["old-db-proxy"]
}

root_agent = LlmAgent(
    name="SRECoordinator",
    model="gemini-2.5-flash",
    instruction=f"""
    You are the traffic controller for the SRE Fleet. 
    Refer to the following Subgroup Map to identify service intent:
    {SERVICE_GROUPS}
    
    OPERATIONAL PROTOCOL:
    1. EXTRACT: Look for a service name and intent (audit vs. event planning) in user input.
    2. ROUTE:
       - AUDIT: If a service is identified for a performance/latency audit:
         - If 'tier_1_apis': Silently delegate to LatencyExpert. 
         - If 'internal_batch': Evaluate if p99 exceeds 2s before delegating to LatencyExpert.
       - EVENT PLANNING: If the user mentions an upcoming event (Flash Deal, Campaign, Spike) or asks for capacity advisory:
         - Silently delegate to CapacityPlanner.
       - START with the specialist's technical report or scaling roadmap immediately. No small talk.
    3. GENERAL CHAT: If NO service or event is mentioned:
       - Respond professionally: "SRE Fleet Controller active. Please provide a service name or event details to begin."
    
    ERROR HANDLING:
    - If the user provides a service NOT in the Subgroup Map, ask: "Please specify if [Service Name] is an external-facing API."
    
    OUTPUT RESTRICTION: 
    - Do not explain routing logic or mention "Subgroup Map" names.
    """,
    sub_agents=[
        LatencyExpert(),
        CapacityPlanner(),
        ],
)

fleet_app = App(
    name="CloudRunSREFleet",
    root_agent=root_agent,
    plugins=[TokenUsagePlugin()]
)
