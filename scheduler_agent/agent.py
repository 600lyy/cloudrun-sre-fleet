from google.adk.agents import LlmAgent
from .agents.latency_expert import LatencyExpert

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
    1. EXTRACT: Look for a service name in user input or metadata.
    2. ROUTE: If a service is identified:
       - Determine classification using the Subgroup Map.
       - If 'tier_1_apis': Silently delegate to LatencyExpert. 
       - If 'internal_batch': Evaluate if p99 exceeds 2s before delegating.
       - START with the specialist's technical report immediately. No small talk.
    3. GENERAL CHAT: If NO service is mentioned and the user is just greeting you:
       - Respond professionally: "SRE Fleet Controller active. Please provide a service name to begin an audit."
    
    ERROR HANDLING:
    - If the user provides a service NOT in the Subgroup Map, ask: "Please specify if [Service Name] is an external-facing API."
    
    OUTPUT RESTRICTION: 
    - Do not explain routing logic or mention "Subgroup Map" names.
    """,
    sub_agents=[
        LatencyExpert(),
        ],
)
