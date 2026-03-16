import os
from pathlib import Path
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from tools.registry import TOOL_DECLARATIONS

# Google Search lives in its own isolated sub-agent
search_agent = Agent(
    name="search_agent",
    model=os.getenv("COGNITO_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025"),
    tools=[google_search],
    instruction="Search the web and return factual, grounded results."
)

# Noop functions for the six custom tools — interceptor handles actual execution
def _make_noop(decl: dict):
    async def noop(**kwargs) -> dict:
        return {}
    noop.__name__ = decl["name"]
    noop.__doc__ = decl.get("description", "")
    return noop

agent = Agent(
    name="cognito_agent",
    model=os.getenv("COGNITO_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025"),
    tools=[AgentTool(agent=search_agent)] + [_make_noop(decl) for decl in TOOL_DECLARATIONS],
    instruction=Path("SYSTEM_PROMPT.md").read_text()
)