import streamlit as st
import os
from database_postgres import init_database
from dashboard import render_dashboard
from auth import require_authentication, render_user_info, check_authentication

def main():
    # Set page config first (must be first Streamlit command)
    st.set_page_config(
        page_title="InnoVantage Resume Evaluation System",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'mailto:support@innomatics.in',
            'Report a bug': 'mailto:tech-support@innomatics.in',
            'About': 'InnoVantage - AI-Powered Resume Evaluation System v2.0'
        }
    )
    
    # Note: Database initialization moved after page selection to allow Student Portal access
    
    # Modern header with gradient-style design
    st.markdown("""<div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #1f77b4, #ff7f0e); border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0; font-size: 2.5rem;'>🎯 InnoVantage</h1>
        <h3 style='color: white; margin: 0; font-weight: 300;'>AI-Powered Resume Evaluation System</h3>
        <p style='color: white; margin: 0; opacity: 0.9;'>Innomatics Research Labs • Advanced Talent Analytics Platform</p>
    </div>""", unsafe_allow_html=True)
    
    # Modern sidebar navigation with icons
    st.sidebar.markdown("""<div style='text-align: center; padding: 1rem; background: #f0f2f6; border-radius: 10px; margin-bottom: 1rem;'>
        <h2 style='margin: 0; color: #1f77b4;'>🧭 Navigation</h2>
    </div>""", unsafe_allow_html=True)
    
    page_options = {
        "👨‍🎓 Student Portal": "Student Portal",
        "📊 Dashboard": "Dashboard", 
        "📝 Job Descriptions": "Upload Job Description",
        "📄 Resume Upload": "Upload Resume",
        "🚀 Batch Processing": "Batch Evaluation",
        "📈 Analytics": "Analytics"
    }
    
    selected_page = st.sidebar.selectbox(
        "Choose your destination:",
        list(page_options.keys()),
        format_func=lambda x: x
    )
    page = page_options[selected_page]
    
    # Check if student portal is selected (no authentication required)
    if page == "Student Portal":
        st.sidebar.markdown("""<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; text-align: center; color: white; margin-bottom: 1rem;'>
            <h4 style='margin: 0; color: white;'>👨‍🎓 Student Portal</h4>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>No login required</p>
        </div>""", unsafe_allow_html=True)
        
        # Check for OpenAI API key warning for students
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.markdown("""<div style='background: #e1f5fe; border-left: 4px solid #01579b; padding: 1rem; border-radius: 5px; margin: 1rem 0;'>
                <p style='margin: 0; color: #01579b;'>ℹ️ <strong>Notice:</strong> Some AI features may be limited. Contact your placement coordinator for assistance.</p>
            </div>""", unsafe_allow_html=True)
        
        # Render student portal
        render_dashboard(page)
        return
    
    # Initialize database for authenticated pages only
    if 'initialized' not in st.session_state:
        try:
            if init_database():
                st.session_state.initialized = True
            else:
                st.error("❌ Database initialization failed. Please check your database configuration.")
                st.info("💡 **Tip**: Ensure PostgreSQL is running or check your environment variables.")
                st.stop()
        except Exception as e:
            st.error(f"❌ Database connection error: {str(e)}")
            st.info("💡 **Tip**: Check your DATABASE_URL and ensure the database service is running.")
            st.stop()
    
    # For all other pages, require authentication
    if not require_authentication():
        st.markdown("""<div style='background: #fff3e0; border-left: 4px solid #ef6c00; padding: 1.5rem; border-radius: 10px; text-align: center; margin: 2rem 0;'>
            <h3 style='margin: 0; color: #ef6c00;'>🔒 Staff Access Required</h3>
            <p style='margin: 0.5rem 0 0 0; color: #bf360c;'>Please login to access placement team features</p>
        </div>""", unsafe_allow_html=True)
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
