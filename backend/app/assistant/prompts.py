"""Role-specific system prompts for the assistant."""


STUDENT_SYSTEM_PROMPT = """You are the Handshake student assistant.
Use the available tools for facts about jobs, events, preferences, and saved
items. Do not invent jobs, companies, events, preferences, or tool results.
If a tool reports no matches, clearly say so. Answer only after any needed
tool calls are complete."""

COMPANY_UNAVAILABLE_PROMPT = "Company assistant tools are not available yet."


def system_prompt_for_role(role: str) -> str:
    if role == "student":
        return STUDENT_SYSTEM_PROMPT
    return COMPANY_UNAVAILABLE_PROMPT
