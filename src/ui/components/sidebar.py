"""
Sidebar component implementation
"""
import streamlit as st
from utils.config import get_config

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
        config = get_config()
        selected_provider = st.selectbox(
            "Select Provider",
            config.get_supported_providers(),
            index=config.get_supported_providers().index(config.LLM_PROVIDER),
            label_visibility="collapsed"
        )
        
        if selected_provider != config.LLM_PROVIDER:
            st.warning("⚠️ Provider change requires restart")
        
        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Clear chat button
        _, col2, _ = st.columns([1, 2, 1])
        with col2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                if "messages" in st.session_state:
                    st.session_state.messages = []
                if "agent" in st.session_state:
                    st.session_state.agent.clear_history()
                st.rerun()
        
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