from uuid import uuid4

import json

from fastapi import (
    FastAPI,
    HTTPException
)

from fastapi.responses import (
    StreamingResponse
)

from pydantic import (
    BaseModel,
    Field
)

from langchain_core.messages import (
    HumanMessage,
    AIMessage
)

from src.graph.workflow import (
    build_graph
)

from src.db.database import (
    init_database,
    create_conversation,
    get_conversations,
    get_conversation,
    get_messages,
    get_message_count,
    save_message,
    update_conversation_title,
    delete_conversation,
    get_recent_messages,
)


# =========================================================
# App initialization
# =========================================================

app = FastAPI(
    title="Travel AI Assistant API",
    version="1.0.0",
    description=(
        "Backend API for the "
        "Agentic Travel Assistant."
    )
)


# Create database tables
init_database()


# Build graph only once
graph = build_graph()


# =========================================================
# Request / Response models
# =========================================================

class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1
    )

    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    services: list[str]
    sources: list[str]


# =========================================================
# Helpers
# =========================================================

def create_title(
    question: str,
    max_length: int = 45
):
    """
    Create a simple conversation title
    without using another LLM call.
    """

    title = " ".join(
        question.strip().split()
    )

    if len(title) > max_length:
        title = (
            title[:max_length].rstrip()
            + "..."
        )

    return title


def build_conversation_messages(
    session_id: str,
    question: str,
    restore_limit: int = 6
):
    """
    Restore recent conversation history only
    when LangGraph has no in-memory state
    for this session.
    """

    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    # Check whether LangGraph already
    # remembers this conversation.
    try:
        snapshot = graph.get_state(
            config
        )

        state_values = (
            snapshot.values
            if snapshot
            else {}
        )

        existing_messages = (
            state_values.get(
                "messages",
                []
            )
        )

    except Exception:
        existing_messages = []

    # LangGraph already remembers the session.
    # Only send the current user message.
    if existing_messages:
        return [
            HumanMessage(
                content=question
            )
        ]

    # LangGraph memory is empty.
    # Restore recent messages from SQLite.
    database_messages = (
        get_recent_messages(
            session_id=session_id,
            limit=restore_limit
        )
    )

    restored_messages = []

    for message in database_messages:
        role = message.get(
            "role"
        )

        content = message.get(
            "content",
            ""
        )

        if role == "user":
            restored_messages.append(
                HumanMessage(
                    content=content
                )
            )

        elif role == "assistant":
            restored_messages.append(
                AIMessage(
                    content=content
                )
            )

    # Add the current user message
    restored_messages.append(
        HumanMessage(
            content=question
        )
    )

    return restored_messages


# Human-friendly service names
SERVICE_LABELS = {
    "general": (
        "Using general knowledge"
    ),
    "weather": (
        "Checking weather"
    ),
    "places": (
        "Searching local places"
    ),
    "rag": (
        "Retrieving travel knowledge"
    ),
    "analytics": (
        "Analysing tourism data"
    )
}


def make_sse_event(
    event_type: str,
    data: dict
):
    """
    Convert data into SSE format.
    """

    payload = json.dumps(
        data,
        ensure_ascii=False
    )

    return (
        f"event: {event_type}\n"
        f"data: {payload}\n\n"
    )


# =========================================================
# Basic endpoints
# =========================================================

@app.get("/")
def root():
    return {
        "message": (
            "Travel AI Assistant API "
            "is running."
        )
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# =========================================================
# Normal chat
# =========================================================

@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest
):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail=(
                "Question cannot be empty."
            )
        )

    session_id = (
        request.session_id
        or str(uuid4())
    )

    # Make sure conversation exists
    create_conversation(
        session_id=session_id
    )

    is_first_message = (
        get_message_count(
            session_id
        ) == 0
    )

    try:
        conversation_messages = (
            build_conversation_messages(
                session_id=session_id,
                question=question,
                restore_limit=6
            )
        )

        result = graph.invoke(
            {
                "question": question,

                "messages": (
                    conversation_messages
                )
            },

            config={
                "configurable": {
                    "thread_id": session_id
                }
            }
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        ) from error

    answer = result.get(
        "answer",
        ""
    )

    services = result.get(
        "services",
        []
    )

    sources = result.get(
        "sources",
        []
    )

    # Save user message
    save_message(
        session_id=session_id,
        role="user",
        content=question
    )

    # Save assistant message
    save_message(
        session_id=session_id,
        role="assistant",
        content=answer,
        services=services,
        sources=sources
    )

    # Use the first question as title
    if is_first_message:
        update_conversation_title(
            session_id=session_id,
            title=create_title(
                question
            )
        )

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        services=services,
        sources=sources
    )


# =========================================================
# Streaming chat
# =========================================================

@app.post("/chat/stream")
def chat_stream(
    request: ChatRequest
):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    session_id = (
        request.session_id
        or str(uuid4())
    )

    create_conversation(
        session_id=session_id
    )

    is_first_message = (
        get_message_count(
            session_id
        ) == 0
    )

    conversation_messages = (
        build_conversation_messages(
            session_id=session_id,
            question=question,
            restore_limit=6
        )
    )

    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    def event_generator():
        services = []
        sources = []
        final_answer = ""

        try:
            # ---------------------------------
            # Initial status
            # ---------------------------------

            yield make_sse_event(
                "status",
                {
                    "stage": "planner_start",
                    "message": (
                        "Understanding your request..."
                    )
                }
            )

            # ---------------------------------
            # LangGraph streaming
            #
            # updates:
            #   node completion events
            #
            # messages:
            #   LLM output chunks
            # ---------------------------------

            for stream_mode, stream_data in graph.stream(
                {
                    "question": question,
                    "messages": conversation_messages
                },
                config=config,
                stream_mode=[
                    "updates",
                    "messages"
                ]
            ):

                # =================================
                # NODE UPDATES
                # =================================

                if stream_mode == "updates":

                    update = stream_data

                    # -----------------------------
                    # Planner finished
                    # -----------------------------

                    if "planner" in update:
                        planner_result = (
                            update.get("planner")
                            or {}
                        )

                        services = (
                            planner_result.get(
                                "services",
                                []
                            )
                        )

                        yield make_sse_event(
                            "planner_done",
                            {
                                "services": services,
                                "message": (
                                    "Request understood."
                                )
                            }
                        )

                        for service in services:

                            # General does not run
                            # an external tool.
                            if service == "general":
                                continue

                            label = (
                                SERVICE_LABELS.get(
                                    service,
                                    f"Running {service}"
                                )
                            )

                            yield make_sse_event(
                                "service_start",
                                {
                                    "service": service,
                                    "message": label
                                }
                            )

                    # -----------------------------
                    # Executor finished
                    # -----------------------------

                    elif "executor" in update:
                        executor_result = (
                            update.get("executor")
                            or {}
                        )

                        sources = (
                            executor_result.get(
                                "sources",
                                []
                            )
                        )

                        for service in services:

                            if service == "general":
                                continue

                            label = (
                                SERVICE_LABELS.get(
                                    service,
                                    service
                                )
                            )

                            yield make_sse_event(
                                "service_done",
                                {
                                    "service": service,
                                    "message": label
                                }
                            )

                        yield make_sse_event(
                            "status",
                            {
                                "stage": (
                                    "synthesizer_start"
                                ),
                                "message": (
                                    "Preparing your answer..."
                                )
                            }
                        )

                    # -----------------------------
                    # Synthesizer finished
                    # -----------------------------

                    elif "synthesizer" in update:
                        synth_result = (
                            update.get(
                                "synthesizer"
                            )
                            or {}
                        )

                        # Keep full final answer
                        # for DB persistence.
                        final_answer = (
                            synth_result.get(
                                "answer",
                                ""
                            )
                        )

                        final_sources = (
                            synth_result.get(
                                "sources"
                            )
                        )

                        if final_sources is not None:
                            sources = final_sources

                # =================================
                # LLM MESSAGE STREAM
                # =================================

                elif stream_mode == "messages":

                    message_chunk, metadata = (
                        stream_data
                    )

                    # Planner also uses an LLM.
                    # We DO NOT want to stream
                    # planner JSON to the user.
                    #
                    # Only stream tokens generated
                    # inside final synthesizer.
                    node_name = metadata.get(
                        "langgraph_node"
                    )

                    if node_name != "synthesizer":
                        continue

                    content = getattr(
                        message_chunk,
                        "content",
                        ""
                    )

                    if not content:
                        continue

                    # Some providers may return
                    # structured content.
                    if isinstance(content, str):
                        token_text = content

                    else:
                        token_text = str(content)

                    yield make_sse_event(
                        "token",
                        {
                            "content": token_text
                        }
                    )

            # ---------------------------------
            # Final validation
            # ---------------------------------

            if not final_answer:
                raise RuntimeError(
                    "The assistant did not "
                    "generate a final answer."
                )

            # ---------------------------------
            # Save conversation
            # ---------------------------------

            save_message(
                session_id=session_id,
                role="user",
                content=question
            )

            save_message(
                session_id=session_id,
                role="assistant",
                content=final_answer,
                services=services,
                sources=sources
            )

            if is_first_message:
                update_conversation_title(
                    session_id=session_id,
                    title=create_title(
                        question
                    )
                )

            # ---------------------------------
            # Completion event
            #
            # Do not use this to re-render the
            # whole answer in the frontend.
            # The answer has already streamed
            # through "token" events.
            # ---------------------------------

            yield make_sse_event(
                "done",
                {
                    "session_id": session_id,
                    "answer": final_answer,
                    "services": services,
                    "sources": sources
                }
            )

        except Exception as error:

            yield make_sse_event(
                "error",
                {
                    "message": str(error)
                }
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# =========================================================
# Conversation history
# =========================================================

@app.get("/conversations")
def list_conversations():
    return {
        "conversations": (
            get_conversations()
        )
    }


@app.get(
    "/conversations/{session_id}"
)
def conversation_detail(
    session_id: str
):
    conversation = (
        get_conversation(
            session_id
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conversation not found."
            )
        )

    messages = get_messages(
        session_id
    )

    return {
        "conversation": conversation,
        "messages": messages
    }


@app.delete(
    "/conversations/{session_id}"
)
def remove_conversation(
    session_id: str
):
    conversation = (
        get_conversation(
            session_id
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conversation not found."
            )
        )

    delete_conversation(
        session_id
    )

    return {
        "message": (
            "Conversation deleted."
        ),
        "session_id": session_id
    }
