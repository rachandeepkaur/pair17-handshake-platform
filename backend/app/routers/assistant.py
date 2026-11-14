from dataclasses import asdict, replace
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.assistant.agent import AssistantRun, NoPendingActionError, TokenUsage, resume_assistant, run_assistant
from app.assistant.compaction import COMPACT_COMMAND, compact_conversation, compacted_history
from app.assistant.tracing import log_timing, new_trace_id
from app.config import settings
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
    AssistantTokenUsage,
)


router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantChatResponse, summary="Send a message to the assistant")
def chat(
    payload: AssistantChatRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_user),
    client: ModelClient = Depends(get_model_client),
) -> AssistantChatResponse:
    trace_id = new_trace_id()
    request_started_at = perf_counter()
    try:
        conversation = [message.as_message() for message in payload.conversation]
        if payload.message == COMPACT_COMMAND:
            return _compact_response(conversation, client, trace_id)
        run = run_assistant(
            payload.message,
            conversation,
            AssistantContext(account_id=account.id, role=account.role.value, db=db),
            client,
            trace_id=trace_id,
        )
        return _response(_compact_if_needed(run, client, trace_id), trace_id)
    finally:
        log_timing(trace_id, "request", request_started_at, endpoint="chat")


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
    trace_id = new_trace_id()
    request_started_at = perf_counter()
    try:
        run = resume_assistant(
            [message.as_message() for message in payload.conversation],
            payload.approved,
            AssistantContext(account_id=account.id, role=account.role.value, db=db),
            client,
            trace_id=trace_id,
        )
        return _response(_compact_if_needed(run, client, trace_id), trace_id)
    except NoPendingActionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    finally:
        log_timing(trace_id, "request", request_started_at, endpoint="confirm")


def _response(run: AssistantRun, trace_id: str) -> AssistantChatResponse:
    return AssistantChatResponse(
        answer=run.answer,
        conversation=[AssistantConversationMessage.model_validate(message) for message in run.conversation],
        tool_call_count=run.tool_call_count,
        stopped_at_iteration_limit=run.stopped_at_iteration_limit,
        pending_action=AssistantPendingAction(**asdict(run.pending_action)) if run.pending_action else None,
        token_usage=AssistantTokenUsage(**asdict(run.token_usage)),
        trace_id=trace_id,
    )


def _compact_if_needed(run: AssistantRun, client: ModelClient, trace_id: str) -> AssistantRun:
    if run.token_usage.context_percentage < settings.assistant_compaction_threshold_percent:
        return run
    compaction_started_at = perf_counter()
    compaction = compact_conversation(run.conversation, client)
    log_timing(trace_id, "compaction", compaction_started_at)
    if compaction is None:
        return run
    return _with_compaction(run, compaction, include_latest_turn=True)


def _compact_response(conversation: list[dict], client: ModelClient, trace_id: str) -> AssistantChatResponse:
    compaction_started_at = perf_counter()
    compaction = compact_conversation(conversation, client)
    log_timing(trace_id, "compaction", compaction_started_at)
    if compaction is None:
        run = AssistantRun(
            answer="I couldn't compact this conversation right now. Please try again.",
            conversation=[*conversation, {"role": "user", "content": COMPACT_COMMAND}],
            tool_call_count=0,
        )
        return _response(run, trace_id)

    run = AssistantRun(
        answer=(
            "Conversation compacted. "
            f"Context changed from {compaction.before_prompt_tokens} measured tokens to "
            f"about {compaction.after_estimated_tokens} summary tokens."
        ),
        conversation=compacted_history(compaction.summary, conversation, include_latest_turn=False)
        + [
            {"role": "user", "content": COMPACT_COMMAND},
            {
                "role": "assistant",
                "content": (
                    "Conversation compacted. "
                    f"Context changed from {compaction.before_prompt_tokens} measured tokens to "
                    f"about {compaction.after_estimated_tokens} summary tokens."
                ),
            },
        ],
        tool_call_count=0,
        token_usage=TokenUsage(
            prompt_tokens=compaction.prompt_tokens,
            completion_tokens=compaction.completion_tokens,
            total_tokens=compaction.prompt_tokens + compaction.completion_tokens,
            context_percentage=round(compaction.after_estimated_tokens / settings.ollama_num_ctx * 100, 1),
            inference_calls=1,
            context_is_estimate=True,
            compacted=True,
            before_compaction_tokens=compaction.before_prompt_tokens,
            after_compaction_estimate=compaction.after_estimated_tokens,
        ),
    )
    return _response(run, trace_id)


def _with_compaction(run: AssistantRun, compaction, *, include_latest_turn: bool) -> AssistantRun:
    usage = run.token_usage
    return replace(
        run,
        conversation=compacted_history(compaction.summary, run.conversation, include_latest_turn=include_latest_turn),
        token_usage=TokenUsage(
            prompt_tokens=usage.prompt_tokens + compaction.prompt_tokens,
            completion_tokens=usage.completion_tokens + compaction.completion_tokens,
            total_tokens=usage.total_tokens + compaction.prompt_tokens + compaction.completion_tokens,
            context_percentage=round(compaction.after_estimated_tokens / settings.ollama_num_ctx * 100, 1),
            inference_calls=usage.inference_calls + 1,
            context_is_estimate=True,
            compacted=True,
            before_compaction_tokens=compaction.before_prompt_tokens,
            after_compaction_estimate=compaction.after_estimated_tokens,
        ),
    )
