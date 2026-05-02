from pathlib import Path

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from core.config import Settings, get_settings
from domains.agents.handlers import (
    confirm_session_goal,
    generate_analogy_visual,
    get_session_timer,
    render_quiz_component,
    submit_quiz_answer,
    update_flow_meter,
)
from domains.agents.subagents.search import search_agent

settings: Settings = get_settings()


def build_agent_tools() -> list[object]:
    return [
        AgentTool(agent=search_agent),
        confirm_session_goal,
        get_session_timer,
        generate_analogy_visual,
        render_quiz_component,
        submit_quiz_answer,
        update_flow_meter,
    ]


agent = Agent(
    name="cognito_agent",
    model=settings.COGNITO_MODEL,
    tools=build_agent_tools(),
    instruction=(Path(__file__).resolve().parent / "prompts" / "system.md").read_text(),
)
