from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.assistant.agent import run_assistant
from app.assistant.llm_client import ModelClient, get_model_client
from app.assistant.tools.schemas import AssistantContext
from app.dependencies import get_current_user, get_db
from app.models.account import Account
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse, AssistantConversationMessage


router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantChatResponse, summary="Send a message to the assistant")
def chat(
    payload: AssistantChatRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_user),
    client: ModelClient = Depends(get_model_client),
) -> AssistantChatResponse:
    run = run_assistant(
        payload.message,
        [message.as_message() for message in payload.conversation],
        AssistantContext(account_id=account.id, role=account.role.value, db=db),
        client,
    )
    return AssistantChatResponse(
        answer=run.answer,
        conversation=[AssistantConversationMessage.model_validate(message) for message in run.conversation],
        tool_call_count=run.tool_call_count,
        stopped_at_iteration_limit=run.stopped_at_iteration_limit,
    )
