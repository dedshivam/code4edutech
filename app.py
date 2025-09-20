import streamlit as st
import os
from database_postgres import init_database
from dashboard import render_dashboard
from auth import require_authentication, render_user_info, check_authentication

def main():
    # Set page config first (must be first Streamlit command)
    st.set_page_config(
        page_title="Resume Evaluation System - Innomatics Research Labs",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database after page config
    if 'initialized' not in st.session_state:
        if init_database():
            st.session_state.initialized = True
        else:
            st.error("❌ System initialization failed. Please contact support for assistance.")
            st.stop()
    
    st.title("🎯 AI-Powered Resume Evaluation System")
    st.markdown("**Innomatics Research Labs** - Automated Resume Relevance Check")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Student Portal", "Dashboard", "Upload Job Description", "Upload Resume", "Batch Evaluation", "Analytics"]
    )
    
    # Check if student portal is selected (no authentication required)
    if page == "Student Portal":
        st.sidebar.info("👨‍🎓 **Student Access**: No login required")
        
        # Check for OpenAI API key warning for students
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.info("ℹ️ Some AI features may be limited. Contact your placement coordinator for assistance.")
        
        # Render student portal
        render_dashboard(page)
        return
    
    # For all other pages, require authentication
    if not require_authentication():
        st.info("🔒 **Staff Access Required**: Please login to access placement team features")
        return
    
    # Check for OpenAI API key for staff
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.warning("⚠️ OpenAI API Key not configured. AI features will use rule-based fallbacks.")
    
    # Render user info in sidebar for authenticated users
    render_user_info()
    
    # Render selected page
    render_dashboard(page)

if __name__ == "__main__":
    main()
