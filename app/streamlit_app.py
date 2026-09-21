import json
import os
import time
import uuid

import requests
import streamlit as st


# =========================================================
# Configuration
# =========================================================

API_BASE_URL = os.getenv(
    "TRAVEL_API_URL",
    "http://127.0.0.1:8000"
)

CHAT_URL = (
    f"{API_BASE_URL}/chat"
)

STREAM_CHAT_URL = (
    f"{API_BASE_URL}/chat/stream"
)

CONVERSATIONS_URL = (
    f"{API_BASE_URL}/conversations"
)


st.set_page_config(
    page_title="Travel AI Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    /* Main page */
    .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* Sidebar expanded */
    section[data-testid="stSidebar"][aria-expanded="true"] {
        width: 380px !important;
        min-width: 380px !important;
        max-width: 380px !important;
    }

    section[data-testid="stSidebar"][aria-expanded="true"] > div {
        width: 380px !important;
    }

    /* Sidebar collapsed */
    section[data-testid="stSidebar"][aria-expanded="false"] {
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }

    footer {
        visibility: hidden;
    }

    .travel-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .travel-subtitle {
        font-size: 1rem;
        opacity: 0.72;
        margin-bottom: 2rem;
    }

    .welcome-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 18px;
        padding: 28px;
        margin-top: 20px;
        margin-bottom: 24px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# Session state
# =========================================================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(
        uuid.uuid4()
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# =========================================================
# API helpers
# =========================================================

def fetch_conversations():
    try:
        response = requests.get(
            CONVERSATIONS_URL,
            timeout=5
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "conversations",
            []
        )

    except requests.RequestException:
        return []


def fetch_conversation(
    session_id: str
):
    try:
        response = requests.get(
            f"{CONVERSATIONS_URL}/{session_id}",
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException:
        return None


def delete_conversation_api(
    session_id: str
):
    try:
        response = requests.delete(
            f"{CONVERSATIONS_URL}/{session_id}",
            timeout=5
        )

        response.raise_for_status()

        return True

    except requests.RequestException:
        return False


def send_chat_request(
    question: str
):
    """
    Normal non-streaming request.
    """

    start_time = time.perf_counter()

    response = requests.post(
        CHAT_URL,
        json={
            "question": question,
            "session_id": (
                st.session_state.session_id
            )
        },
        timeout=120
    )

    response.raise_for_status()

    elapsed = (
        time.perf_counter()
        - start_time
    )

    return (
        response.json(),
        elapsed
    )


def stream_chat_request(
    question: str
):
    """
    Send a streaming chat request
    and yield parsed SSE events.
    """

    response = requests.post(
        STREAM_CHAT_URL,
        json={
            "question": question,
            "session_id": (
                st.session_state.session_id
            )
        },
        headers={
            "Accept": "text/event-stream"
        },
        stream=True,
        timeout=120
    )

    response.raise_for_status()

    current_event = None

    for line in response.iter_lines(
        decode_unicode=True,
        chunk_size=1
    ):
        if not line:
            continue

        # -------------------------
        # Event type
        # -------------------------

        if line.startswith(
            "event: "
        ):
            current_event = line[
                len("event: "):
            ]

            continue

        # -------------------------
        # Event data
        # -------------------------

        if not line.startswith(
            "data: "
        ):
            continue

        try:
            data = json.loads(
                line[
                    len("data: "):
                ]
            )

        except json.JSONDecodeError:
            continue

        yield (
            current_event,
            data
        )


# =========================================================
# Conversation helpers
# =========================================================

def start_new_conversation():

    st.session_state.session_id = str(
        uuid.uuid4()
    )

    st.session_state.messages = []

    st.session_state.pending_prompt = None


def load_conversation(
    session_id: str
):

    data = fetch_conversation(
        session_id
    )

    if data is None:
        return False

    database_messages = data.get(
        "messages",
        []
    )

    messages = []

    for message in database_messages:

        messages.append(
            {
                "role": message.get(
                    "role"
                ),

                "content": message.get(
                    "content",
                    ""
                ),

                "services": message.get(
                    "services",
                    []
                ),

                "sources": message.get(
                    "sources",
                    []
                )
            }
        )

    st.session_state.session_id = (
        session_id
    )

    st.session_state.messages = (
        messages
    )

    st.session_state.pending_prompt = None

    return True


def render_metadata(
    services,
    sources,
    response_time=None
):

    parts = []

    if services:

        parts.append(
            "Services: "
            + ", ".join(services)
        )

    if sources:

        parts.append(
            "Sources: "
            + ", ".join(sources)
        )

    if response_time is not None:

        parts.append(
            f"Response time: "
            f"{response_time:.1f}s"
        )

    if parts:

        st.caption(
            " · ".join(parts)
        )


def format_title(
    title: str,
    max_length: int = 32
):

    if not title:
        return "New conversation"

    if len(title) <= max_length:
        return title

    return (
        title[:max_length].rstrip()
        + "..."
    )


# =========================================================
# Delete dialog
# =========================================================

@st.dialog(
    "Delete conversation?"
)
def confirm_delete_dialog(
    session_id: str,
    title: str
):

    st.write(
        "Are you sure you want to "
        "delete this conversation?"
    )

    st.caption(
        title
    )

    st.warning(
        "This action cannot be undone."
    )

    col_cancel, col_delete = (
        st.columns(2)
    )

    with col_cancel:

        if st.button(
            "Cancel",
            use_container_width=True
        ):

            st.rerun()

    with col_delete:

        if st.button(
            "Delete",
            type="primary",
            use_container_width=True
        ):

            deleted = (
                delete_conversation_api(
                    session_id
                )
            )

            if deleted:

                if (
                    session_id
                    == st.session_state.session_id
                ):

                    start_new_conversation()

                st.rerun()

            else:

                st.error(
                    "Could not delete "
                    "conversation."
                )


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    # =====================================================
    # Branding
    # =====================================================

    st.markdown(
        "## ✈️ Travel AI"
    )

    st.caption(
        "Agentic travel assistant "
        "for New Zealand"
    )

    st.divider()

    # =====================================================
    # New conversation
    # =====================================================

    if st.button(
        "＋ New conversation",
        use_container_width=True,
        type="primary"
    ):

        start_new_conversation()

        st.rerun()

    st.caption(
        f"Session: "
        f"{st.session_state.session_id[:8]}"
    )

    # =====================================================
    # Settings
    # =====================================================

    with st.expander(
        "⚙️ Settings",
        expanded=False
    ):

        streaming_enabled = (
            st.toggle(
                "Streaming responses",
                value=True,
                key="streaming_enabled",
                help=(
                    "Display the answer "
                    "while it is being generated."
                )
            )
        )

        show_agent_status = (
            st.toggle(
                "Show agent activity",
                value=True,
                key="show_agent_status",
                help=(
                    "Show what the assistant "
                    "is doing while processing "
                    "the request."
                )
            )
        )

    st.divider()

    # =====================================================
    # Recent conversations
    # =====================================================

    st.markdown(
        "### Recent chats"
    )

    conversations = (
        fetch_conversations()
    )

    # Fixed-height scrollable container
    with st.container(
        height=430,
        border=False
    ):

        if conversations:

            for conversation in conversations:

                session_id = (
                    conversation.get(
                        "session_id"
                    )
                )

                full_title = (
                    conversation.get(
                        "title",
                        "New conversation"
                    )
                )

                title = format_title(
                    full_title
                )

                is_current = (
                    session_id
                    == st.session_state.session_id
                )

                button_label = title

                if is_current:

                    button_label = (
                        f"● {title}"
                    )

                chat_col, delete_col = (
                    st.columns(
                        [5, 1],
                        gap="small"
                    )
                )

                # -------------------------
                # Open conversation
                # -------------------------

                with chat_col:

                    if st.button(
                        button_label,
                        key=(
                            f"conversation_"
                            f"{session_id}"
                        ),
                        use_container_width=True
                    ):

                        loaded = (
                            load_conversation(
                                session_id
                            )
                        )

                        if loaded:

                            st.rerun()

                # -------------------------
                # Delete conversation
                # -------------------------

                with delete_col:

                    if st.button(
                        "✕",
                        key=(
                            f"delete_"
                            f"{session_id}"
                        ),
                        help=(
                            "Delete conversation"
                        ),
                        use_container_width=True
                    ):

                        confirm_delete_dialog(
                            session_id=session_id,
                            title=full_title
                        )

        else:

            st.caption(
                "No saved conversations yet."
            )

    st.divider()

    # =====================================================
    # Capabilities
    # =====================================================

    st.markdown(
        "### Capabilities"
    )

    st.markdown(
        """
        🌦️ Weather forecasts

        📍 Attractions & restaurants

        📚 Travel knowledge

        📊 Tourism analytics

        🧠 Multi-turn memory
        """
    )


# =========================================================
# Header
# =========================================================

st.markdown(
    """
    <div class="travel-title">
        ✈️ Travel AI Assistant
    </div>

    <div class="travel-subtitle">
        Plan New Zealand trips with live weather,
        local places, travel knowledge and tourism data.
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# Welcome page
# =========================================================

if not st.session_state.messages:

    st.markdown(
        """
        <div class="welcome-card">

        <h2>Where would you like to go?</h2>

        Ask a simple question or combine multiple
        requests. The assistant can decide which
        tools are needed and combine the results.

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "#### Try an example"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🌦️ Auckland weather tomorrow",
            use_container_width=True
        ):

            st.session_state.pending_prompt = (
                "What is the weather "
                "in Auckland tomorrow?"
            )

            st.rerun()

        if st.button(
            "📍 Restaurants in Auckland",
            use_container_width=True
        ):

            st.session_state.pending_prompt = (
                "Recommend some restaurants "
                "in Auckland."
            )

            st.rerun()

    with col2:

        if st.button(
            "🏔️ Plan a Queenstown trip",
            use_container_width=True
        ):

            st.session_state.pending_prompt = (
                "I'm planning a trip to "
                "Queenstown next week. "
                "What should I know?"
            )

            st.rerun()

        if st.button(
            "📊 Auckland tourism spending",
            use_container_width=True
        ):

            st.session_state.pending_prompt = (
                "How much did international "
                "visitors spend in Auckland "
                "in July 2026?"
            )

            st.rerun()

    st.caption(
        "You can ask follow-up questions such as "
        '"What about the day after?" or '
        '"Any restaurants there?"'
    )


# =========================================================
# Display conversation
# =========================================================

for message in (
    st.session_state.messages
):

    role = message.get(
        "role"
    )

    avatar = (
        "👤"
        if role == "user"
        else "✈️"
    )

    with st.chat_message(
        role,
        avatar=avatar
    ):

        st.markdown(
            message.get(
                "content",
                ""
            )
        )

        if role == "assistant":

            render_metadata(
                services=message.get(
                    "services",
                    []
                ),

                sources=message.get(
                    "sources",
                    []
                ),

                response_time=message.get(
                    "response_time"
                )
            )


# =========================================================
# Chat input
# =========================================================

typed_question = st.chat_input(
    "Ask about weather, places, trips "
    "or tourism data..."
)


question = None


if st.session_state.pending_prompt:

    question = (
        st.session_state.pending_prompt
    )

    st.session_state.pending_prompt = None


elif typed_question:

    question = typed_question


# =========================================================
# Process message
# =========================================================

if question:

    # =====================================================
    # User message
    # =====================================================

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message(
        "user",
        avatar="👤"
    ):

        st.markdown(
            question
        )

    # =====================================================
    # Assistant response
    # =====================================================

    with st.chat_message(
        "assistant",
        avatar="✈️"
    ):

        start_time = (
            time.perf_counter()
        )

        try:

            # =================================================
            # Streaming mode
            # =================================================

            if streaming_enabled:

                answer = ""
                services = []
                sources = []

                answer_placeholder = (
                    st.empty()
                )

                status_box = None

                # -------------------------
                # Agent activity
                # -------------------------

                if show_agent_status:

                    status_box = st.status(
                        "Understanding your request...",
                        expanded=True
                    )

                # -------------------------
                # Read SSE events
                # -------------------------

                for (
                    event_type,
                    data
                ) in stream_chat_request(
                    question
                ):

                    # =====================
                    # Status
                    # =====================

                    if (
                        event_type
                        == "status"
                    ):

                        message = data.get(
                            "message",
                            ""
                        )

                        if (
                            show_agent_status
                            and status_box
                        ):

                            status_box.update(
                                label=message
                            )

                    # =====================
                    # Planner completed
                    # =====================

                    elif (
                        event_type
                        == "planner_done"
                    ):

                        services = data.get(
                            "services",
                            []
                        )

                        if (
                            show_agent_status
                            and status_box
                        ):

                            status_box.write(
                                "✅ Request understood"
                            )

                    # =====================
                    # Service started
                    # =====================

                    elif (
                        event_type
                        == "service_start"
                    ):

                        message = data.get(
                            "message",
                            ""
                        )

                        if (
                            show_agent_status
                            and status_box
                        ):

                            status_box.write(
                                f"⏳ {message}"
                            )

                    # =====================
                    # Service completed
                    # =====================

                    elif (
                        event_type
                        == "service_done"
                    ):

                        message = data.get(
                            "message",
                            ""
                        )

                        if (
                            show_agent_status
                            and status_box
                        ):

                            status_box.write(
                                f"✅ {message}"
                            )

                    # =====================
                    # Streaming token
                    # =====================

                    elif (
                        event_type
                        == "token"
                    ):

                        token = data.get(
                            "content",
                            ""
                        )

                        if token:

                            answer += token

                            answer_placeholder.markdown(
                                answer + " ▌"
                            )

                    # =====================
                    # Completed
                    # =====================

                    elif (

                            event_type

                            == "done"

                    ):

                        returned_session_id = (

                            data.get(

                                "session_id"

                            )

                        )

                        if returned_session_id:
                            st.session_state.session_id = (

                                returned_session_id

                            )

                        # Use the backend's authoritative

                        # final answer instead of relying

                        # only on streamed token assembly.

                        final_answer = data.get(

                            "answer",

                            ""

                        )

                        if final_answer:
                            answer = final_answer

                            answer_placeholder.markdown(

                                answer

                            )

                        services = data.get(

                            "services",

                            services

                        )

                        sources = data.get(

                            "sources",

                            sources

                        )

                        if (

                                show_agent_status

                                and status_box

                        ):
                            status_box.update(

                                label=(

                                    "Response ready"

                                ),

                                state="complete",

                                expanded=False

                            )

                    # =====================
                    # Backend error
                    # =====================

                    elif (
                        event_type
                        == "error"
                    ):

                        raise RuntimeError(
                            data.get(
                                "message",
                                "Streaming failed."
                            )
                        )

                # -------------------------
                # Remove streaming cursor
                # -------------------------

                if answer:

                    answer_placeholder.markdown(
                        answer
                    )

                else:

                    answer = (
                        "I couldn't generate "
                        "a response."
                    )

                    answer_placeholder.markdown(
                        answer
                    )

                response_time = (
                    time.perf_counter()
                    - start_time
                )

            # =================================================
            # Normal mode
            # =================================================

            else:

                if show_agent_status:

                    with st.status(
                        "Processing your request...",
                        expanded=False
                    ) as status:

                        (
                            data,
                            response_time
                        ) = send_chat_request(
                            question
                        )

                        status.update(
                            label=(
                                "Response ready"
                            ),
                            state="complete"
                        )

                else:

                    with st.spinner(
                        "Thinking..."
                    ):

                        (
                            data,
                            response_time
                        ) = send_chat_request(
                            question
                        )

                answer = data.get(
                    "answer",
                    ""
                )

                services = data.get(
                    "services",
                    []
                )

                sources = data.get(
                    "sources",
                    []
                )

                returned_session_id = (
                    data.get(
                        "session_id"
                    )
                )

                if returned_session_id:

                    st.session_state.session_id = (
                        returned_session_id
                    )

                if not answer:

                    answer = (
                        "I couldn't generate "
                        "a response."
                    )

                st.markdown(
                    answer
                )

            # =================================================
            # Metadata
            # =================================================

            render_metadata(
                services=services,
                sources=sources,
                response_time=response_time
            )

            # =================================================
            # Save UI state
            # =================================================

            st.session_state.messages.append(
                {
                    "role": "assistant",

                    "content": answer,

                    "services": services,

                    "sources": sources,

                    "response_time": (
                        response_time
                    )
                }
            )

            # Refresh sidebar
            time.sleep(0.1)

            st.rerun()


        # =====================================================
        # Errors
        # =====================================================

        except requests.exceptions.ConnectionError:

            st.error(
                "I couldn't connect to the backend. "
                "Please make sure FastAPI is running."
            )


        except requests.exceptions.Timeout:

            st.error(
                "The request took too long. "
                "Please try again."
            )


        except requests.exceptions.HTTPError as error:

            st.error(
                "The backend returned an error."
            )

            with st.expander(
                "Technical details"
            ):

                st.code(
                    str(error)
                )


        except Exception as error:

            st.error(
                "Something went wrong while "
                "processing the request."
            )

            with st.expander(
                "Technical details"
            ):

                st.code(
                    str(error)
                )
