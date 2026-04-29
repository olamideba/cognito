from pathlib import Path

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from core.config import get_settings, Settings

from tools.handlers import (
    handle_confirm_session_goal,
    handle_get_session_timer,
    handle_generate_analogy_visual,
    handle_render_quiz_component,
    handle_submit_quiz_answer,
    handle_update_flow_meter,
)

settings: Settings = get_settings()

# Google Search lives in its own isolated sub-agent
search_agent = Agent(
    name="search_agent",
    model=settings.COGNITO_SEARCH_MODEL,
    tools=[google_search],
    instruction="Search the web and return factual, grounded results.",
)

agent = Agent(
    name="cognito_agent",
    model=settings.COGNITO_MODEL,
    tools=[
        AgentTool(agent=search_agent),
        handle_confirm_session_goal,
        handle_get_session_timer,
        handle_generate_analogy_visual,
        handle_render_quiz_component,
        handle_submit_quiz_answer,
        handle_update_flow_meter,
    ],
    instruction=Path("SYSTEM_PROMPT.md").read_text(),
)
