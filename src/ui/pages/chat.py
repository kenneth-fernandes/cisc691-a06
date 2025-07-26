"""
Chat page implementation
"""
import streamlit as st
import time
import uuid
from ui.utils.api_client import get_api_client

def init_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "api_client" not in st.session_state:
        st.session_state.api_client = get_api_client()
    if "current_provider" not in st.session_state:
        st.session_state.current_provider = "google"  # Default provider

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
    
    # Create main chat container
    chat_container = st.container()
    
    # Create processing indicator container
    processing_container = st.container()
    
    # Handle user input at bottom
    placeholder_text = "AI is thinking..." if st.session_state.processing else "Type your message here..."
    
    if prompt := st.chat_input(placeholder_text, disabled=st.session_state.processing):
        # Set processing state
        st.session_state.processing = True
        
        # Display previous messages first
        with chat_container:
            for message in st.session_state.messages:
                display_chat_message(
                    message["role"],
                    message["content"],
                    message.get("time_taken")
                )
        
        # Display new user message
        with chat_container:
            display_chat_message("user", prompt)
        
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Show loading indicator below user message
        with processing_container:
            with st.spinner("AI is thinking..."):
                start_time = time.time()
                
                # Create agent config
                agent_config = {
                    "agent_type": "default",
                    "provider": st.session_state.current_provider,
                    "mode": "general"
                }
                
                # Call API
                api_response = st.session_state.api_client.chat_with_agent(
                    message=prompt,
                    session_id=st.session_state.session_id,
                    config=agent_config
                )
                
                time_taken = time.time() - start_time
                
                # Handle API response
                if "error" in api_response:
                    response = f"Sorry, I encountered an error: {api_response['error']}"
                else:
                    response = api_response.get("response", "No response received")
        
        # Add AI response to state
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "time_taken": time_taken
        })
        
        # Reset processing state
        st.session_state.processing = False
        
        # Rerun to update chat history
        st.rerun()
    else:
        # Just display existing messages
        with chat_container:
            for message in st.session_state.messages:
                display_chat_message(
                    message["role"],
                    message["content"],
                    message.get("time_taken")
                )
    
    # Display welcome message for empty chat
    if not st.session_state.messages:
        st.markdown("*Send a message to start the conversation!*")