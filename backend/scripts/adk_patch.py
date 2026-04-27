from __future__ import annotations
from google.adk import telemetry
from google.adk.flows.llm_flows import functions
import inspect

def patch_adk_trace_tool_call() -> None:
    signature = inspect.signature(telemetry.trace_tool_call)
    if "response_event_id" in signature.parameters:
        return

    original = telemetry.trace_tool_call

    def trace_tool_call_compat(
        *,
        tool=None,
        args=None,
        function_response_event=None,
        **kwargs,
    ):
        if function_response_event is not None:
            return original(
                tool=tool,
                args=args or {},
                function_response_event=function_response_event,
            )
        # Newer ADK call signature; telemetry only, safe to skip.
        return None

    telemetry.trace_tool_call = trace_tool_call_compat
    functions.trace_tool_call = trace_tool_call_compat
