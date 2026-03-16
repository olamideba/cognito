import os
from google.adk.agents import Agent
from google.adk.tools import google_search

TOOL_DECLARATIONS = [
    {
        "name": "confirm_session_goal",
        "description": "Saves the user's stated goal and time limit to begin the session.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                },
                "time_limit_minutes": {
                    "type": "integer",
                }
            },
            "required": ["goal", "time_limit_minutes"]
        }
    }
]

agent = Agent(
    name="cognito_agent",
    model="models/gemini-2.5-flash",
    tools=[google_search] + TOOL_DECLARATIONS,
    instruction="Instruction"
)
print("Agent created successfully")
