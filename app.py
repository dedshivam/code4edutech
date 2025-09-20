import streamlit as st
import os
from database_postgres import init_database
from dashboard import render_dashboard
from auth import require_authentication, render_user_info, check_authentication

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
    
    # Check authentication first
    if not require_authentication():
        return
    
    st.title("🎯 AI-Powered Resume Evaluation System")
    st.markdown("**Innomatics Research Labs** - Automated Resume Relevance Check")
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.warning("⚠️ OpenAI API Key not configured. AI features will use rule-based fallbacks.")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Dashboard", "Upload Job Description", "Upload Resume", "Batch Evaluation", "Analytics", "Student Portal"]
    )
    
    # Render user info in sidebar
    render_user_info()
    
    # Render selected page
    render_dashboard(page)

if __name__ == "__main__":
    main()
