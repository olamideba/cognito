import os
from pathlib import Path
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

from tools.handlers import (
    handle_confirm_session_goal,
    handle_get_session_timer,
    handle_generate_analogy_visual,
    handle_render_quiz_component,
    handle_submit_quiz_answer,
    handle_update_flow_meter,
)

load_dotenv()

# Google Search lives in its own isolated sub-agent
search_agent = Agent(
    name="search_agent",
    model=os.getenv("COGNITO_SEARCH_MODEL", "gemini-2.5-flash"),
    tools=[google_search],
    instruction="Search the web and return factual, grounded results.",
)

agent = Agent(
    name="cognito_agent",
    model=os.getenv("COGNITO_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025"),
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
