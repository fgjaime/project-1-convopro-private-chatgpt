import streamlit as st
from pymongo.errors import PyMongoError

from services.get_models_list import get_ollama_models_list
from services.get_title import get_chat_title
from services.chat_utilities import get_answer
from db.conversations import (
    create_new_conversation,
    add_message,
    get_conversation,
    get_all_conversations,
)

st.set_page_config(page_title="ChatGPT Clone", page_icon="💬", layout="centered")
st.title("🤖 Local ChatGPT Clone")

# ---- Models ----
if "OLLAMA_MODELS" not in st.session_state:
    st.session_state.OLLAMA_MODELS = get_ollama_models_list()

selected_model = st.selectbox("Select Model", st.session_state.OLLAMA_MODELS)

# ---- Session state ----
st.session_state.setdefault("conversation_id", None)
st.session_state.setdefault("conversation_title", None)
st.session_state.setdefault("chat_history", [])  # [{role, content}]

# ---- Sidebar: conversations ----
with st.sidebar:
    st.header("💬 Chat History")
    db_error = None
    try:
        conversations = get_all_conversations()  # {conv_id: title}
    except PyMongoError as exc:
        conversations = {}
        db_error = str(exc)

    if db_error:
        st.error(f"MongoDB auth/connection error: {db_error}")

    if st.button("➕ New Chat"):
        st.session_state.conversation_id = None
        st.session_state.conversation_title = None
        st.session_state.chat_history = []

    for cid, title in conversations.items():
        is_current = cid == st.session_state.conversation_id
        label = f"**{title}**" if is_current else title
        if st.button(label, key=f"conv_{cid}"):
            try:
                doc = get_conversation(cid) or {}
            except PyMongoError as exc:
                st.error(f"Could not load conversation: {exc}")
                doc = {}
            st.session_state.conversation_id = cid
            st.session_state.conversation_title = doc.get("title", "Untitled")
            st.session_state.chat_history = [
                {"role": m["role"], "content": m["content"]}
                for m in doc.get("messages", [])
            ]

# ---- Show chat so far ----
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---- Chat input ----
user_query = st.chat_input("Ask AI...")
if user_query:
    # 1) Show + store user message in UI state
    st.chat_message("user").markdown(user_query)
    st.session_state.chat_history.append({"role": "user", "content": user_query})

    # 2) Persist to DB (create convo on first message, else append)
    if st.session_state.conversation_id is None:
        try:
            title = get_chat_title(selected_model, user_query) or "New Chat"
        except Exception:
            title = "New Chat"
        try:
            conv_id = create_new_conversation(
                title=title, role="user", content=user_query
            )
            st.session_state.conversation_id = conv_id
            st.session_state.conversation_title = title
        except PyMongoError as exc:
            st.error(f"Could not save conversation: {exc}")
    else:
        try:
            add_message(st.session_state.conversation_id, "user", user_query)
        except PyMongoError as exc:
            st.error(f"Could not save message: {exc}")

    # 3) Get assistant response (direct service)
    try:
        assistant_text = str(
            get_answer(selected_model, st.session_state.chat_history) or ""
        )
    except Exception as e:
        assistant_text = f"[Error getting response: {e}]"

    # 4) Show + store assistant message
    with st.chat_message("assistant"):
        st.markdown(assistant_text)
    st.session_state.chat_history.append(
        {"role": "assistant", "content": assistant_text}
    )

    # 5) Persist assistant message
    if st.session_state.conversation_id:
        try:
            add_message(st.session_state.conversation_id, "assistant", assistant_text)
        except PyMongoError as exc:
            st.error(f"Could not save assistant message: {exc}")
