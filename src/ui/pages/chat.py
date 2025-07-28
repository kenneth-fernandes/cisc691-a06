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
    if "visa_messages" not in st.session_state:
        st.session_state.visa_messages = []
    if "general_messages" not in st.session_state:
        st.session_state.general_messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "visa_session_id" not in st.session_state:
        st.session_state.visa_session_id = str(uuid.uuid4())
    if "general_session_id" not in st.session_state:
        st.session_state.general_session_id = str(uuid.uuid4())
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "api_client" not in st.session_state:
        st.session_state.api_client = get_api_client()
    if "current_provider" not in st.session_state:
        st.session_state.current_provider = "google"  # Default provider
    if "expert_mode" not in st.session_state:
        st.session_state.expert_mode = "General"
    if "last_expert_mode" not in st.session_state:
        st.session_state.last_expert_mode = "General"

def display_chat_message(role, content, time_taken=None, mode_indicator=None):
    """Display a chat message with optional timing and mode indicator"""
    with st.chat_message(role):
        st.write(content)
        
        # Display metadata (time and mode)
        metadata_parts = []
        if time_taken:
            metadata_parts.append(f"⏱️ Response time: {time_taken:.2f}s")
        if mode_indicator and role == "assistant":
            metadata_parts.append(f"🎯 Mode: {mode_indicator}")
        
        if metadata_parts:
            st.caption(" | ".join(metadata_parts))

def get_context_aware_messages():
    """Get messages for current mode and handle context switching"""
    current_mode = st.session_state.get('expert_mode', 'General')
    
    # Handle mode switching - preserve separate message histories
    if current_mode != st.session_state.last_expert_mode:
        # Save current messages to appropriate history
        if st.session_state.last_expert_mode == "Visa Expert":
            st.session_state.visa_messages = st.session_state.messages.copy()
        else:
            st.session_state.general_messages = st.session_state.messages.copy()
        
        # Load messages for new mode
        if current_mode == "Visa Expert":
            st.session_state.messages = st.session_state.visa_messages.copy()
            st.session_state.session_id = st.session_state.visa_session_id
        else:
            st.session_state.messages = st.session_state.general_messages.copy()
            st.session_state.session_id = st.session_state.general_session_id
        
        st.session_state.last_expert_mode = current_mode
    
    return st.session_state.messages

def get_welcome_message():
    """Get mode-specific welcome message with data status"""
    current_mode = st.session_state.get('expert_mode', 'General')
    
    if current_mode == "Visa Expert":
        # Check if API is available for additional context
        try:
            api_client = st.session_state.api_client
            db_stats = api_client.get_database_stats()
            data_status = ""
            
            if "error" not in db_stats:
                total_records = db_stats.get('total_records', 'N/A')
                latest_bulletin = db_stats.get('latest_bulletin_date', 'N/A')
                data_status = f"\n\n📊 **Data Status**: {total_records} records available | Latest: {latest_bulletin}"
            
        except:
            data_status = ""
            
        return f"""*🎯 **Visa Expert Mode Active**
        
I'm specialized in U.S. visa bulletin analysis and can help with:
        • Historical trend analysis for EB and FB categories
        • Country-specific processing insights (India, China, Mexico, Philippines)
        • Priority date predictions and movement forecasts
        • Visa category comparisons and recommendations{data_status}
        
💡 **Tip**: Use the Quick Actions in the sidebar for common queries!
        
Send a message to start your visa consultation!*"""
    else:
        return "*🤖 **General Assistant Mode**\n\nI'm here to help with any questions or tasks. Send a message to start the conversation!*"

def render_chat_page():
    """Render the main chat interface with visa integration"""
    current_mode = st.session_state.get('expert_mode', 'General')
    mode_icon = "🎯" if current_mode == "Visa Expert" else "🤖"
    
    st.title(f"{mode_icon} AI Agent Chat - {current_mode} Mode")
    
    # Initialize session state
    init_session_state()
    
    # Get context-aware messages
    messages = get_context_aware_messages()
    
    # Display mode switching notification
    if current_mode != st.session_state.get('last_displayed_mode', 'General'):
        mode_color = "#1f77b4" if current_mode == "Visa Expert" else "#666666"
        st.markdown(
            f"""
            <div style='background-color: {mode_color}20; 
                        border-left: 4px solid {mode_color}; 
                        padding: 10px; 
                        margin: 10px 0;
                        border-radius: 5px;'>
                {mode_icon} <strong>Switched to {current_mode} Mode</strong><br>
                <small>{'Specialized visa analysis capabilities activated' if current_mode == 'Visa Expert' else 'General AI assistance mode activated'}</small>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.session_state.last_displayed_mode = current_mode
    
    # Create main chat container
    chat_container = st.container()
    
    # Create processing indicator container
    processing_container = st.container()
    
    # Handle quick action queries
    quick_action_query = st.session_state.pop('quick_action_query', None)
    if quick_action_query and not st.session_state.processing:
        prompt = quick_action_query
    else:
        prompt = None
    
    # Handle user input at bottom
    placeholder_text = "AI is thinking..." if st.session_state.processing else "Type your message here..."
    
    if not prompt:
        prompt = st.chat_input(placeholder_text, disabled=st.session_state.processing)
    
    if prompt:
        # Set processing state
        st.session_state.processing = True
        
        # Display previous messages first
        with chat_container:
            for message in messages:
                display_chat_message(
                    message["role"],
                    message["content"],
                    message.get("time_taken"),
                    message.get("mode")
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
                
                # Create agent config based on current mode
                mode = "visa_expert" if current_mode == "Visa Expert" else "general"
                
                agent_config = {
                    "agent_type": "default",  # Always use default agent type
                    "provider": st.session_state.current_provider,
                    "mode": mode
                }
                
                # Call API with enhanced error handling
                try:
                    api_response = st.session_state.api_client.chat_with_agent(
                        message=prompt,
                        session_id=st.session_state.session_id,
                        config=agent_config
                    )
                    
                    time_taken = time.time() - start_time
                    
                    # Handle API response with visa-specific error messages
                    if "error" in api_response:
                        error_msg = api_response['error']
                        if current_mode == "Visa Expert" and "data" in error_msg.lower():
                            response = f"🚫 **Visa Data Issue**: {error_msg}\n\n💡 **Suggestion**: Try asking about general visa trends or check if the visa database is properly initialized."
                        else:
                            response = f"❌ **Error**: {error_msg}"
                    else:
                        response = api_response.get("response", "No response received")
                        
                        # Add helpful context for visa responses
                        if current_mode == "Visa Expert" and response and len(response) > 100:
                            if any(keyword in prompt.lower() for keyword in ['predict', 'forecast', 'future', 'next']):
                                response += "\n\n📊 *Predictions are based on historical patterns and may vary due to policy changes.*"
                            elif any(keyword in prompt.lower() for keyword in ['trend', 'analysis', 'history']):
                                response += "\n\n📈 *Analysis based on historical visa bulletin data from 2020-2025.*"
                
                except Exception as e:
                    time_taken = time.time() - start_time
                    if current_mode == "Visa Expert":
                        response = f"🚫 **Visa Expert Service Unavailable**: {str(e)}\n\n🔄 **Try**: Switching to General mode or restarting the application."
                    else:
                        response = f"❌ **Service Error**: {str(e)}"
        
        # Add AI response to state with mode indicator
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "time_taken": time_taken,
            "mode": current_mode
        })
        
        # Reset processing state
        st.session_state.processing = False
        
        # Rerun to update chat history
        st.rerun()
    else:
        # Just display existing messages
        with chat_container:
            for message in messages:
                display_chat_message(
                    message["role"],
                    message["content"],
                    message.get("time_taken"),
                    message.get("mode")
                )
    
    # Display mode-specific welcome message for empty chat
    if not messages:
        st.markdown(get_welcome_message())