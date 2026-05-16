TOOL_DECLARATIONS = [
    {
        "name": "confirm_session_goal",
        "description": "Saves the user's stated goal and time limit to begin the session. Call this exactly once, after the user has verbally confirmed BOTH their goal and their available time. Do not call this until both values are known.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "A concise description of what the user wants to accomplish in this session. Example: 'Implement binary search in Python'."
                },
                "time_limit_minutes": {
                    "type": "integer",
                    "description": "Duration of the session in minutes, as stated by the user. Must be between 5 and 30."
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
        "description": "Generates a visual diagram or analogy image to help the user understand a concept they are struggling with. Call this after verbal explanations haven't fully resolved confusion, or upon request. The image_prompt MUST be a highly descriptive narrative paragraph, not keyword soup.",
        "parameters": {
            "type": "object",
            "properties": {
                "concept_label": {
                    "type": "string",
                    "description": "A short title for the concept being illustrated. Example: 'Recursion Stack' or 'TCP Handshake'."
                },
                "image_prompt": {
                    "type": "string",
                    "description": "A detailed, descriptive narrative for the image generation model. You MUST explicitly apply one of three design aesthetics based on the context: 1)[Default] 'Hand-drawn sketchbook style, clean line art, pastel yellow and blue, on a grid paper background, live whiteboard session feel.' 2) [Objects] 'Polished 3D render with depth and studio lighting.' 3) [Historical/Textured] 'Retro print, vintage mid-century textbook style, screen-printed.' The prompt MUST end with '16:9 aspect ratio, set against a clean whiteboard-like background.'"
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
                    "items": {"type": "string"},
                    "description": "List of answer options. Required for multiple_choice. Ignored for fill_in_blank and reflection_prompt. For multiple_choice, provide a list of full string options, DO NOT add the letter as a prefix (e.g., ['Photosynthesis', 'Chlorophyll'] is valid, not ['A) Photosynthesis', 'B) Chlorophyll'], not ['A. Photosynthesis', 'B. Chlorophyll])."
                },
                "correct_answer": {
                    "type": "string",
                    "description": "The exact text of the correct answer. For multiple_choice, provide the full string of the option, not just the letter index (e.g., 'Photosynthesis', not 'A', not 'A. Photosynthesis')."
                },
                "hint": {
                    "type": "string",
                    "description": "A brief, Socratic hint shown if the user requests help. It should guide them, not give the answer away."
                }
            },
            "required": ["component_type", "question"]
        }
    },
    {
        "name": "submit_quiz_answer",
        "description": "Submit a user's verbal answer to the rendered quiz component so the UI updates visually. You MUST trigger this whenever a user answers a UI quiz verbally.",
        "parameters": {
            "type": "object",
            "properties": {
                "component_id": {
                    "type": "string",
                    "description": "The ID of the quiz component."
                },
                "answer": {
                    "type": "string",
                    "description": "The answer submitted by the user. If the user answers in natural language, extract the specific keyword or option text that corresponds to their answer (e.g., if the user says 'I think it is A', and option A is 'Photosynthesis', submit 'Photosynthesis')."
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
                    "description": "Brief description of the observed behavior. Example: 'User answered quiz rapidly with high confidence' or 'User expressed frustration with web search delay.'"
                }
            },
            "required": ["signal_type", "delta"]
        }
    }
]

