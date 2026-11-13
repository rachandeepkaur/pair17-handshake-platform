from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from app.assistant import memory
from app.assistant.agent import AssistantRun, NoPendingActionError, resume_assistant, run_assistant
from app.assistant.llm_client import ModelClient, get_model_client
from app.assistant.tools.schemas import AssistantContext
from app.dependencies import get_current_user, get_db
from app.mongo import Doc as Account
from app.schemas.assistant import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantConfirmRequest,
    AssistantConversationMessage,
    AssistantPendingAction,
)


router = APIRouter(prefix="/assistant", tags=["assistant"])


def _context(db: Database, account: Account) -> AssistantContext:
    return AssistantContext(
        account_id=account.id, role=account.role, db=db, memory_prompt=memory.build_memory_prompt_safely(db, account)
    )


@router.post("/chat", response_model=AssistantChatResponse, summary="Send a message to the assistant")
def chat(
    payload: AssistantChatRequest,
    db: Database = Depends(get_db),
    account: Account = Depends(get_current_user),
    client: ModelClient = Depends(get_model_client),
) -> AssistantChatResponse:
    conversation = [message.as_message() for message in payload.conversation]

    # /memory commands are answered directly (no model call). The exchange is shown
    # in the chat but never sent to the model (prompts.without_memory_commands).
    answer = memory.handle_memory_command(db, account, payload.message)
    if answer is not None:
        conversation += [{"role": "user", "content": payload.message}, {"role": "assistant", "content": answer}]
        return AssistantChatResponse(
            answer=answer,
            conversation=[AssistantConversationMessage.model_validate(m) for m in conversation[-50:]],
            tool_call_count=0,
            stopped_at_iteration_limit=False,
        )

    run = run_assistant(payload.message, conversation, _context(db, account), client)
    memory.save_conversation_safely(db, account, run.conversation)
    return _response(run)


@router.post(
    "/confirm",
    response_model=AssistantChatResponse,
    summary="Approve or decline the action the assistant is waiting on",
)
def confirm(
    payload: AssistantConfirmRequest,
    db: Database = Depends(get_db),
    account: Account = Depends(get_current_user),
    client: ModelClient = Depends(get_model_client),
) -> AssistantChatResponse:
    try:
        run = resume_assistant(
            [message.as_message() for message in payload.conversation],
            payload.approved,
            _context(db, account),
            client,
        )
    except NoPendingActionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    memory.save_conversation_safely(db, account, run.conversation)
    return _response(run)


def _response(run: AssistantRun) -> AssistantChatResponse:
    return AssistantChatResponse(
        answer=run.answer,
        conversation=[AssistantConversationMessage.model_validate(message) for message in run.conversation],
        tool_call_count=run.tool_call_count,
        stopped_at_iteration_limit=run.stopped_at_iteration_limit,
        pending_action=AssistantPendingAction(**asdict(run.pending_action)) if run.pending_action else None,
    )
