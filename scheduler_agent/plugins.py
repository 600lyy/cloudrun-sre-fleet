import logging
from typing import Any
from typing_extensions import override

from google.adk.plugins.base_plugin import BasePlugin
from google.adk.models.llm_response import LlmResponse
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext

logger = logging.getLogger("adk_token_usage")

class TokenUsagePlugin(BasePlugin):
    """
    A custom ADK Plugin that tracks total token usage and automatically 
    archives conversational turns into Long-term Memory.
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
        Triggered after every LLM call. Accumulates and logs token usage.
        """
        if llm_response and llm_response.usage_metadata:
            usage = llm_response.usage_metadata
            prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
            candidates_tokens = getattr(usage, "candidates_token_count", 0) or 0
            
            self.total_prompt_tokens += prompt_tokens
            self.total_candidates_tokens += candidates_tokens
            
            print(f"\n[TOKEN TRACKER] Turn Tokens - Input: {prompt_tokens} | Output: {candidates_tokens}")
            print(f"[TOKEN TRACKER] Total Session Tokens - Input: {self.total_prompt_tokens} | Output: {self.total_candidates_tokens} | Total: {self.total_prompt_tokens + self.total_candidates_tokens}\n")
            
            logger.info(f"Token usage - Turn: {prompt_tokens}/{candidates_tokens}, Total: {self.total_prompt_tokens}/{self.total_candidates_tokens}")

    @override
    async def after_run_callback(
        self,
        *,
        invocation_context: InvocationContext,
        **kwargs: Any
    ) -> None:
        """
        Triggered after the conversational turn is complete.
        Archives the current session into the Memory Service.
        """
        try:
            if invocation_context.memory_service and invocation_context.session:
                await invocation_context.memory_service.add_session_to_memory(invocation_context.session)
                print(f"[MEMORY] Session '{invocation_context.session.id}' archived to long-term memory.", flush=True)
        except Exception as e:
            print(f"\n[MEMORY ARCHIVE ERROR] {str(e)}", flush=True)
