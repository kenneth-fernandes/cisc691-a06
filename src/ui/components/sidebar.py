"""
Sidebar component implementation
"""
import streamlit as st
from ui.utils.api_client import get_api_client

def render_sidebar():
    """Render the sidebar with settings"""
    with st.sidebar:
        # Title with custom styling
        st.markdown("""
            <h1 style='text-align: center; margin-bottom: 1.5rem;'>
                ⚙️ Settings
            </h1>
        """, unsafe_allow_html=True)
        
        # Provider selection
        st.markdown("<p style='margin-bottom: 0.5rem; font-weight: 600;'>🔌 Provider</p>", unsafe_allow_html=True)
        
        # Get supported providers from API
        api_client = get_api_client()
        providers_response = api_client.get_supported_providers()
        
        if "error" not in providers_response:
            supported_providers = providers_response.get("providers", ["google", "openai", "anthropic", "ollama"])
        else:
            supported_providers = ["google", "openai", "anthropic", "ollama"]  # Fallback
        
        # Initialize provider in session state if not present
        if "current_provider" not in st.session_state:
            st.session_state.current_provider = "google"
        
        # Get current index
        try:
            current_index = supported_providers.index(st.session_state.current_provider)
        except ValueError:
            current_index = 0
            st.session_state.current_provider = supported_providers[0]
        
        selected_provider = st.selectbox(
            "Select Provider",
            supported_providers,
            index=current_index,
            label_visibility="collapsed"
        )
            
        # Update provider if changed
        if selected_provider != st.session_state.current_provider:
            st.session_state.current_provider = selected_provider
            # Update agent config via API
            if "session_id" in st.session_state:
                config = {
                    "agent_type": "default",
                    "provider": selected_provider,
                    "mode": "general"
                }
                api_client.update_agent_config(st.session_state.session_id, config)
        
        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Clear chat button
        _, col2, _ = st.columns([1, 2, 1])
        with col2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                if "messages" in st.session_state:
                    st.session_state.messages = []
                # Clear chat history via API by creating new session
                if "session_id" in st.session_state:
                    import uuid
                    st.session_state.session_id = str(uuid.uuid4())
                st.rerun()
        
        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
        
        # API Status
        st.markdown("<p style='margin-bottom: 0.5rem; font-weight: 600;'>🔗 API Status</p>", unsafe_allow_html=True)
        health_response = api_client.health_check()
        if "error" not in health_response and health_response.get("status") == "healthy":
            st.success("✅ Connected")
        else:
            st.error("❌ Disconnected")
            st.caption("Make sure API server is running")
        
        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
        
        # About section
        st.markdown("""
            <div style='padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;'>
                <h3 style='margin-bottom: 1rem; font-size: 1.1em;'>
                    ℹ️ About
                </h3>
                <p style='font-size: 0.9em; margin-bottom: 1rem;'>
                    AI Agent using LangChain with support for multiple providers.
                </p>
                <p style='font-size: 0.9em; font-weight: 600; margin-bottom: 0.5rem;'>
                    Available Models:
                </p>
                <ul style='font-size: 0.9em; margin-left: 1rem; list-style-type: none;'>
                    <li style='margin: 0.3rem 0;'>🌐 Google Gemini (Free)</li>
                    <li style='margin: 0.3rem 0;'>💻 Ollama (Local)</li>
                    <li style='margin: 0.3rem 0;'>🔷 OpenAI GPT (Paid)</li>
                    <li style='margin: 0.3rem 0;'>🟣 Anthropic (Paid)</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)