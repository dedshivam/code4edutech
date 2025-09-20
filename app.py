import streamlit as st
import os
from database import init_database
from dashboard import render_dashboard

# Initialize database on app start
if 'initialized' not in st.session_state:
    init_database()
    st.session_state.initialized = True

def main():
    st.set_page_config(
        page_title="Resume Evaluation System - Innomatics Research Labs",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🎯 AI-Powered Resume Evaluation System")
    st.markdown("**Innomatics Research Labs** - Automated Resume Relevance Check")
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ OpenAI API Key not found. Please set the OPENAI_API_KEY environment variable.")
        st.info("Contact your system administrator to configure the API key.")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Dashboard", "Upload Job Description", "Upload Resume", "Batch Evaluation", "Analytics"]
    )
    
    # Render selected page
    render_dashboard(page)

if __name__ == "__main__":
    main()
