from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.assistant.agent import AssistantRun, NoPendingActionError, resume_assistant, run_assistant
from app.assistant.llm_client import ModelClient, get_model_client
from app.assistant.tools.schemas import AssistantContext
from app.dependencies import get_current_user, get_db
from app.models.account import Account
from app.schemas.assistant import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantConfirmRequest,
    AssistantConversationMessage,
    AssistantPendingAction,
)


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
    return _response(run)


@router.post(
    "/confirm",
    response_model=AssistantChatResponse,
    summary="Approve or decline the action the assistant is waiting on",
)
def confirm(
    payload: AssistantConfirmRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_user),
    client: ModelClient = Depends(get_model_client),
) -> AssistantChatResponse:
    try:
        run = resume_assistant(
            [message.as_message() for message in payload.conversation],
            payload.approved,
            AssistantContext(account_id=account.id, role=account.role.value, db=db),
            client,
        )
    except NoPendingActionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _response(run)


def _response(run: AssistantRun) -> AssistantChatResponse:
    return AssistantChatResponse(
        answer=run.answer,
        conversation=[AssistantConversationMessage.model_validate(message) for message in run.conversation],
        tool_call_count=run.tool_call_count,
        stopped_at_iteration_limit=run.stopped_at_iteration_limit,
        pending_action=AssistantPendingAction(**asdict(run.pending_action)) if run.pending_action else None,
    )
