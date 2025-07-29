"""
Sidebar component implementation
"""

import streamlit as st
from ui.utils.api_client import get_api_client


def render_sidebar():
    """Render the sidebar with settings"""
    with st.sidebar:
        # Title with custom styling
        st.markdown(
            """
            <h1 style='text-align: center; margin-bottom: 1.5rem;'>
                ⚙️ Settings
            </h1>
        """,
            unsafe_allow_html=True,
        )

        # Provider selection
        st.markdown(
            "<p style='margin-bottom: 0.5rem; font-weight: 600;'>🔌 Provider</p>",
            unsafe_allow_html=True,
        )

        # Get supported providers from API
        api_client = get_api_client()
        providers_response = api_client.get_supported_providers()

        if "error" not in providers_response:
            supported_providers = providers_response.get(
                "providers", ["google", "openai", "anthropic", "ollama"]
            )
        else:
            supported_providers = [
                "google",
                "openai",
                "anthropic",
                "ollama",
            ]  # Fallback

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
            label_visibility="collapsed",
        )

        # Update provider if changed
        if selected_provider != st.session_state.current_provider:
            st.session_state.current_provider = selected_provider
            # Update agent config via API
            if "session_id" in st.session_state:
                config = {
                    "agent_type": "default",
                    "provider": selected_provider,
                    "mode": st.session_state.get('expert_mode', 'General').lower().replace(' ', '_'),
                }
                api_client.update_agent_config(st.session_state.session_id, config)

        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

        # Visa Expert Mode Selector
        st.markdown(
            "<p style='margin-bottom: 0.5rem; font-weight: 600;'>🎯 Expert Mode</p>",
            unsafe_allow_html=True,
        )

        # Initialize expert mode in session state if not present
        if "expert_mode" not in st.session_state:
            st.session_state.expert_mode = "General"

        expert_modes = ["General", "Visa Expert"]
        expert_mode_descriptions = {
            "General": "General purpose AI assistant",
            "Visa Expert": "Specialized in U.S. visa bulletin analysis",
        }

        selected_mode = st.selectbox(
            "Select Mode",
            expert_modes,
            index=expert_modes.index(st.session_state.expert_mode),
            label_visibility="collapsed",
            help="Choose between general assistance or specialized visa expertise",
        )

        # Display mode description with visual indicator
        mode_icon = "🎯" if selected_mode == "Visa Expert" else "🤖"
        mode_color = "#1f77b4" if selected_mode == "Visa Expert" else "#666666"

        st.markdown(
            f"""
            <div style='background-color: {mode_color}15; 
                        border: 1px solid {mode_color}; 
                        border-radius: 5px; 
                        padding: 8px; 
                        margin: 5px 0;
                        font-size: 0.85em;'>
                {mode_icon} <strong>Active:</strong> {expert_mode_descriptions[selected_mode]}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Update expert mode if changed
        if selected_mode != st.session_state.expert_mode:
            st.session_state.expert_mode = selected_mode
            
            # Update appropriate session ID based on mode
            if selected_mode == "Visa Expert":
                st.session_state.session_id = st.session_state.get('visa_session_id', str(__import__('uuid').uuid4()))
            else:
                st.session_state.session_id = st.session_state.get('general_session_id', str(__import__('uuid').uuid4()))
            
            # Update agent config via API
            mode = "visa_expert" if selected_mode == "Visa Expert" else "general"
            config = {
                "agent_type": "default",  # Always use default agent type
                "provider": st.session_state.current_provider,
                "mode": mode,
            }
            api_client.update_agent_config(st.session_state.session_id, config)
            
            # Show transition feedback
            transition_icon = "🎯" if selected_mode == "Visa Expert" else "🤖"
            st.success(f"{transition_icon} Switched to {selected_mode} mode!")

        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Visa Expert Quick Actions
        if st.session_state.get('expert_mode') == 'Visa Expert':
            st.markdown(
                "<p style='margin-bottom: 0.5rem; font-weight: 600;'>🚀 Quick Actions</p>",
                unsafe_allow_html=True,
            )
            
            quick_actions = [
                "📈 Show EB-2 India trends",
                "🔮 Predict EB-3 China movement", 
                "🌍 Compare all EB categories",
                "📅 Latest bulletin summary"
            ]
            
            selected_action = st.selectbox(
                "Choose a quick action:",
                ["👆 Select an action..."] + quick_actions,
                label_visibility="collapsed"
            )
            
            if selected_action != "👆 Select an action...":
                # Map actions to queries
                action_queries = {
                    "📈 Show EB-2 India trends": "Show me the historical trends for EB-2 India category over the past 2 years",
                    "🔮 Predict EB-3 China movement": "Predict the movement for EB-3 China category for the next 3 months",
                    "🌍 Compare all EB categories": "Compare all Employment-Based categories for India and show which is moving faster",
                    "📅 Latest bulletin summary": "Give me a summary of the latest visa bulletin with key highlights"
                }
                
                if st.button("▶️ Execute Action", use_container_width=True):
                    # Add the query to chat input (we'll handle this in the main chat)
                    st.session_state.quick_action_query = action_queries[selected_action]
                    st.rerun()
            
            st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)

        # Clear chat buttons
        current_mode = st.session_state.get('expert_mode', 'General')
        
        # Clear current mode chat
        if st.button(f"🗑️ Clear {current_mode} Chat", use_container_width=True):
            if "messages" in st.session_state:
                st.session_state.messages = []
            
            # Clear appropriate message history
            if current_mode == "Visa Expert":
                st.session_state.visa_messages = []
                import uuid
                st.session_state.visa_session_id = str(uuid.uuid4())
                st.session_state.session_id = st.session_state.visa_session_id
            else:
                st.session_state.general_messages = []
                import uuid
                st.session_state.general_session_id = str(uuid.uuid4())
                st.session_state.session_id = st.session_state.general_session_id
            
            st.success(f"✅ {current_mode} chat cleared!")
            st.rerun()
        
        # Clear all chats button
        if st.button("🗑️ Clear All Chats", use_container_width=True, help="Clear both General and Visa Expert chat histories"):
            # Clear all message histories
            st.session_state.messages = []
            st.session_state.visa_messages = []
            st.session_state.general_messages = []
            
            # Generate new session IDs
            import uuid
            st.session_state.visa_session_id = str(uuid.uuid4())
            st.session_state.general_session_id = str(uuid.uuid4())
            
            # Set current session ID based on mode
            if current_mode == "Visa Expert":
                st.session_state.session_id = st.session_state.visa_session_id
            else:
                st.session_state.session_id = st.session_state.general_session_id
            
            st.success("✅ All chats cleared!")
            st.rerun()

        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

        # API Status
        st.markdown(
            "<p style='margin-bottom: 0.5rem; font-weight: 600;'>🔗 API Status</p>",
            unsafe_allow_html=True,
        )
        health_response = api_client.health_check()
        if (
            "error" not in health_response
            and health_response.get("status") == "healthy"
        ):
            st.success("✅ Connected")
        else:
            st.error("❌ Disconnected")
            st.caption("Make sure API server is running")

        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

        # About section
        st.markdown(
            """
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
        """,
            unsafe_allow_html=True,
        )
