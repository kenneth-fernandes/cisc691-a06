"""
Chat page implementation
"""
import streamlit as st
import time
from agent.factory import create_agent

def init_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = create_agent("default")

def display_chat_message(role, content, time_taken=None):
    """Display a chat message with optional timing"""
    with st.chat_message(role):
        st.write(content)
        if time_taken:
            st.caption(f"⏱️ Response time: {time_taken:.2f}s")

def render_chat_page():
    """Render the main chat interface"""
    st.title("🤖 AI Agent Chat")
    
    # Initialize session state
    init_session_state()
    
    # Display chat history
    for message in st.session_state.messages:
        display_chat_message(
            message["role"],
            message["content"],
            message.get("time_taken")
        )
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Display user message
        display_chat_message("user", prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get AI response with timing
        start_time = time.time()
        response = st.session_state.agent.chat(prompt)
        time_taken = time.time() - start_time
        
        # Display AI response
        display_chat_message("assistant", response, time_taken)
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "time_taken": time_taken
        })