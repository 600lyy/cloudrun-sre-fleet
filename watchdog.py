import asyncio
import time
from google.genai import types
from google.adk.apps import App
from google.adk.runners import Runner

from scheduler_agent.agent import SERVICE_GROUPS
from scheduler_agent.agents.latency_expert import LatencyExpert
from scheduler_agent.plugins import TokenUsagePlugin

async def run_watchdog_audit():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] STARTING WATCHDOG AUDIT...")
    
    # Instantiate the LatencyExpert directly for the Watchdog loop
    # This ensures the Watchdog uses the exact same reasoning and tools as the interactive expert.
    watchdog_app = App(
        name="WatchdogLatencyAuditor",
        root_agent=LatencyExpert(),
        plugins=[TokenUsagePlugin()]
    )

    runner = Runner(
        app=watchdog_app, 
        auto_create_session=True,
    )
    
    # Use a timestamped session ID for each watchdog run
    session_id = f"watchdog-audit-{int(time.time())}"

    # For now we only audit 'tier_1_apis'
    tier_1_services = SERVICE_GROUPS.get("tier_1_apis", [])

    for service_name in tier_1_services:
        print(f"\n==================================================")
        print(f"  -> Asking LatencyExpert to audit: {service_name}")
        print(f"==================================================")
        
        # This query triggers the agent's internal logic:
        # 1. Config Check -> 2. Metrics Check -> 3. Latency Audit -> 4. Analysis
        query = (
            f"Please perform a proactive watchdog audit on the service '{service_name}'. "
            f"Check its current configuration, pull its live telemetry, and provide a "
            f"technical analysis including suggestions for flattening latency curves or "
            f"optimizing costs if you detect idle instances."
        )
        
        # Construct the proper ADK Content object
        content = types.Content(role='user', parts=[types.Part.from_text(text=query)])
        
        async for event in runner.run_async(
            user_id="watchdog-system",
            session_id=session_id,
            new_message=content
        ):
            # Extract and stream the agent's textual response
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
        
        print("\n") # formatting break after the agent finishes speaking

    await runner.close()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] WATCHDOG AUDIT COMPLETE.\n")

if __name__ == "__main__":
    asyncio.run(run_watchdog_audit())
