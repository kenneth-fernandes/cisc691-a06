"""
Main Streamlit application entry point
"""
import streamlit as st
from ui.components.sidebar import render_sidebar
from ui.pages.chat import render_chat_page
from ui.pages.analytics import render_analytics_page

def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
        <style>
        /* Main containers */
        .main {
            padding: 1rem 2rem;
        }
        .stChatMessage {
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        
        /* Chat input */
        .stChatInputContainer {
            padding: 0.8rem;
            border-radius: 10px;
        }
        
        /* Buttons */
        .stButton button {
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* Response time */
        .stChatMessage caption {
            font-style: italic;
            opacity: 0.7;
            font-size: 0.8em;
            margin-top: 0.3rem;
        }
        
        /* Selectbox */
        .stSelectbox {
            margin-bottom: 1rem;
        }
        
        /* Warning messages */
        .stAlert {
            padding: 0.5rem;
            border-radius: 8px;
            margin: 0.5rem 0;
        }
        
        /* Chat layout */
        .stChatInputContainer {
            background: var(--background-color);
            padding: 1rem;
            margin-top: 1rem;
        }
        
        .main .block-container {
            padding-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="AI Agent Chat",
        page_icon=">",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/your-repo/issues',
            'Report a bug': 'https://github.com/your-repo/issues/new',
            'About': "AI Agent using LangChain with multiple provider support"
        }
    )
    
    # Apply custom CSS
    apply_custom_css()
    
    # Create main layout
    with st.container():
        # Render sidebar
        render_sidebar()
        
        # Page navigation
        page = st.selectbox(
            "Choose a page:",
            ["🤖 Agent Chat", "📊 Visa Analytics"],
            label_visibility="collapsed"
        )
        
        # Render selected page
        if page == "🤖 Agent Chat":
            render_chat_page()
        elif page == "📊 Visa Analytics":
            render_analytics_page()

if __name__ == "__main__":
    main()