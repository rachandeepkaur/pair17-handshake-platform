"""AI Assistant service: the tool-calling agent backed by a local Ollama model."""

from app.core.service_app import create_service_app
from app.routers import assistant

app = create_service_app(
    "assistant",
    (assistant,),
    description="/assistant/chat and /assistant/confirm. GET /health also reports Ollama and platform services.",
    check_platform=True,
    check_ollama=True,
)
