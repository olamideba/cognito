from google.adk.agents import Agent
from google.adk.tools import google_search

from core.config import Settings, get_settings

settings: Settings = get_settings()

search_agent = Agent(
    name="search_agent",
    model=settings.COGNITO_SEARCH_MODEL,
    tools=[google_search],
    instruction="Search the web and return factual, grounded results.",
)

