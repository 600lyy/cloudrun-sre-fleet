import logging
from typing import Any
from typing_extensions import override

from google.adk.plugins.base_plugin import BasePlugin
from google.adk.models.llm_response import LlmResponse
from google.adk.agents.callback_context import CallbackContext

logger = logging.getLogger("adk_token_usage")

class TokenUsagePlugin(BasePlugin):
    """
    A custom ADK Plugin that tracks the total token usage across all agents
    in the hierarchy and prints the summary to the agent log.
    """
    def __init__(self):
        super().__init__(name="TokenUsagePlugin")
        self.total_prompt_tokens = 0
        self.total_candidates_tokens = 0

    @override
    async def after_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_response: LlmResponse,
        **kwargs: Any
    ) -> None:
        """
        Triggered after every LLM call from any agent in the application.
        Accumulates and logs token usage.
        """
        if llm_response and llm_response.usage_metadata:
            usage = llm_response.usage_metadata
            prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
            candidates_tokens = getattr(usage, "candidates_token_count", 0) or 0
            
            self.total_prompt_tokens += prompt_tokens
            self.total_candidates_tokens += candidates_tokens
            
            # Print to stdout for visibility in CLI and Agent logs
            print(f"\n[TOKEN TRACKER] Turn Tokens - Input: {prompt_tokens} | Output: {candidates_tokens}")
            print(f"[TOKEN TRACKER] Total Session Tokens - Input: {self.total_prompt_tokens} | Output: {self.total_candidates_tokens} | Total: {self.total_prompt_tokens + self.total_candidates_tokens}\n")
            
            # Log for persistent trace records
            logger.info(f"Token usage - Turn: {prompt_tokens}/{candidates_tokens}, Total: {self.total_prompt_tokens}/{self.total_candidates_tokens}")
