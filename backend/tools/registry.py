TOOL_DECLARATIONS = [
    {
        "name": "confirm_session_goal",
        "description": "Saves the user's stated goal and time limit to begin the session. Call this exactly once, after the user has verbally confirmed both their goal and their available time. Do not call this until both values are known.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "A concise description of what the user wants to accomplish in this session. Example: 'Implement binary search in Python'."
                },
                "time_limit_minutes": {
                    "type": "integer",
                    "description": "Duration of the session in minutes, as stated by the user. Must be between 5 and 120."
                }
            },
            "required": ["goal", "time_limit_minutes"]
        }
    },
    {
        "name": "get_session_timer",
        "description": "Returns the current elapsed time and remaining time for the session. Call this to check how much time is left before the session ends, particularly when deciding whether to prompt a wrap-up.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "generate_analogy_visual",
        "description": "Generates a visual diagram or analogy image to help the user understand a concept they are struggling with. Call this after two Socratic prompts have not resolved the user's confusion. Provide a short concept label and a detailed prompt describing the visual.",
        "parameters": {
            "type": "object",
            "properties": {
                "concept_label": {
                    "type": "string",
                    "description": "A short title for the concept being illustrated. Example: 'Recursion Stack' or 'TCP Handshake'."
                },
                "image_prompt": {
                    "type": "string",
                    "description": "A detailed, descriptive prompt for the image generation model. Describe the visual metaphor, layout, and key elements to include. Example: 'A clean diagram showing a stack of plates being added and removed, each plate labeled with a function call name, with arrows showing push and pop operations.'"
                }
            },
            "required": ["concept_label", "image_prompt"]
        }
    },
    {
        "name": "render_quiz_component",
        "description": "Renders an interactive quiz component in the Socratic Quiz tab. Use this to check the user's understanding after an explanation or when they are stuck. The component type determines the interaction format.",
        "parameters": {
            "type": "object",
            "properties": {
                "component_type": {
                    "type": "string",
                    "enum": ["multiple_choice", "true_false", "fill_in_blank", "reflection_prompt"],
                    "description": "The type of interactive component to render."
                },
                "question": {
                    "type": "string",
                    "description": "The question or prompt text displayed to the user."
                },
                "options": {
                    "type": "array",
                    "items": { "type": "string" },
                    "description": "List of answer options. Required for multiple_choice. Ignored for fill_in_blank and reflection_prompt."
                },
                "correct_answer": {
                    "type": "string",
                    "description": "The correct answer. Used for validation on the backend; not sent to the frontend before the user answers."
                },
                "hint": {
                    "type": "string",
                    "description": "Optional hint text shown if the user requests help."
                }
            },
            "required": ["component_type", "question"]
        }
    },
    {
        "name": "submit_quiz_answer",
        "description": "Submit a user's answer to a rendered quiz component for validation.",
        "parameters": {
            "type": "object",
            "properties": {
                "component_id": {
                    "type": "string",
                    "description": "The ID of the quiz component."
                },
                "answer": {
                    "type": "string",
                    "description": "The answer submitted by the user."
                }
            },
            "required": ["component_id", "answer"]
        }
    },
    {
        "name": "update_flow_meter",
        "description": "Updates the session's flow score based on an observed signal. Call this when you detect a significant behavioral pattern — such as the user being stuck, expressing frustration, or returning to focus. Do not call this more than once per minute.",
        "parameters": {
            "type": "object",
            "properties": {
                "signal_type": {
                    "type": "string",
                    "enum": ["stuck", "frustrated", "distracted", "refocused", "breakthrough"],
                    "description": "The behavioral signal that prompted this update."
                },
                "delta": {
                    "type": "integer",
                    "description": "Score change to apply. Negative values reduce the score (distraction), positive values increase it (refocus). Range: -20 to +10."
                },
                "note": {
                    "type": "string",
                    "description": "Brief description of the observed behavior. Example: 'No typing for 120 seconds on shared screen.'"
                }
            },
            "required": ["signal_type", "delta"]
        }
    }
]

TOOL_NAMES = {t["name"] for t in TOOL_DECLARATIONS}
