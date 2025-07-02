"""
Main Streamlit application entry point
"""
import streamlit as st
from ui.components.sidebar import render_sidebar
from ui.pages.chat import render_chat_page

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="AI Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Render sidebar
    render_sidebar()
    
    # Render main chat interface
    render_chat_page()

if __name__ == "__main__":
    main()