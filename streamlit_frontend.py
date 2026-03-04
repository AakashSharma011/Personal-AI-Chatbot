import streamlit as st
import os

# ===================== Page Configuration =====================
st.set_page_config(
    page_title="Aakash Personal AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure API Key is available for the backend
if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from langgraph_database_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# ===================== Utility Functions =====================
def generate_thread_id():
    return str(uuid.uuid4())

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
    config = {'configurable': {'thread_id': thread_id}}
    state = chatbot.get_state(config)
    return state.values.get('messages', [])

# ===================== Session Setup =====================
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

add_thread(st.session_state['thread_id'])

# ===================== Sidebar =====================
st.sidebar.title("🧠 Aakash Personal AI")

if st.sidebar.button("➕ New Chat"):
    reset_chat()

st.sidebar.markdown("### 💬 Chat History")
for tid in st.session_state['chat_threads'][::-1]:
    str_tid = str(tid)
    title = str_tid[:8] + "..."
    if st.sidebar.button(title, key=str_tid):
        st.session_state['thread_id'] = str_tid
        messages = load_conversation(str_tid)
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

    CONFIG = {
        'configurable': {
            'thread_id': st.session_state['thread_id']
        }
    }

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Invoke backend (using invoke instead of stream to be safer against API errors)
        try:
            response = chatbot.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG
            )
            # The result from invoke is a dictionary with 'messages'. The last one is the AI response.
            ai_msg = response['messages'][-1]
            full_response = ai_msg.content
            message_placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"⚠️ An error occurred: {str(e)}"
            message_placeholder.error(full_response)

    st.session_state['message_history'].append({'role': 'assistant', 'content': full_response})
