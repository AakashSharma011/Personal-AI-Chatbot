import streamlit as st
from langgraph_database_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# ===================== Utility Functions =====================

def generate_thread_id():
    return uuid.uuid4()

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []
    st.rerun()

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

# ===================== Session Setup =====================
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

add_thread(st.session_state['thread_id'])

# ===================== Page Configuration =====================
st.set_page_config(
    page_title="Aakash Personal AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== Custom Styling =====================
st.markdown("""
    <style>
        body {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: white;
        }
        .stApp {
            background-color: rgba(0,0,0,0.9);
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .chat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 1rem;
            padding: 1rem 1.5rem;
            margin: 0.5rem 0;
            box-shadow: 0 0 10px rgba(255,255,255,0.1);
        }
        .user-msg {
            color: #64ffda;
        }
        .ai-msg {
            color: #e6e6e6;
        }
        .sidebar .sidebar-content {
            background: rgba(255,255,255,0.05);
        }
        div[data-testid="stChatInput"] {
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# ===================== Sidebar =====================
st.sidebar.title("🧠 Aakash Personal AI")

if st.sidebar.button("➕ New Chat"):
    reset_chat()

st.sidebar.markdown("### 💬 Chat History")

for tid in st.session_state['chat_threads'][::-1]:
    str_tid = str(tid)
    title = str_tid[:8] + "..."
    if st.sidebar.button(title):
        st.session_state['thread_id'] = tid
        messages = load_conversation(tid)
        formatted_msgs = []
        for msg in messages:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            formatted_msgs.append({'role': role, 'content': msg.content})
        st.session_state['message_history'] = formatted_msgs
        st.rerun()

# ===================== Main Chat Area =====================
st.title("🤖 Aakash Personal AI Assistant")

str_tid = str(st.session_state['thread_id'])
st.markdown(f"**🧾 Thread:** `{str_tid[:12]}...`  •  **{len(st.session_state['message_history'])} messages**")

for message in st.session_state['message_history']:
    css_class = "user-msg" if message['role'] == 'user' else "ai-msg"
    with st.chat_message(message['role']):
        st.markdown(f"<div class='chat-card {css_class}'>{message['content']}</div>", unsafe_allow_html=True)

# ===================== Chat Input =====================
user_input = st.chat_input("💬 Type your message here...")

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message("user"):
        st.markdown(f"<div class='chat-card user-msg'>{user_input}</div>", unsafe_allow_html=True)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    with st.chat_message("assistant"):
        def ai_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_stream())

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
