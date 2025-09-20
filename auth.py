import streamlit as st
import bcrypt
import secrets
from datetime import datetime, timedelta
from database_postgres import save_user, get_user_by_username, save_session, get_session

def hash_password(password):
    """Hash password using bcrypt with salt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, password_hash):
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def generate_session_token():
    """Generate secure session token"""
    return secrets.token_urlsafe(32)

def login_user(username, password):
    """Authenticate user and create session"""
    user = get_user_by_username(username)
    if user and verify_password(password, user[3]):  # user[3] is password_hash
        # Create session
        session_token = generate_session_token()
        expires_at = datetime.now() + timedelta(hours=24)
        
        session_id = save_session(user[0], session_token, expires_at)
        if session_id:
            st.session_state.authenticated = True
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.email = user[2]
            st.session_state.location = user[4]
            st.session_state.role = user[5]
            st.session_state.session_token = session_token
            return True
    return False

def register_user(username, email, password, location, role='placement_team'):
    """Register new user"""
    # Check if user already exists
    existing_user = get_user_by_username(username)
    if existing_user:
        return False, "Username already exists"
    
    # Hash password
    password_hash = hash_password(password)
    
    # Save user
    user_id = save_user(username, email, password_hash, location, role)
    if user_id:
        return True, "User registered successfully"
    else:
        return False, "Registration failed"

def logout_user():
    """Logout user and clear session"""
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    if 'user_id' in st.session_state:
        del st.session_state.user_id
    if 'username' in st.session_state:
        del st.session_state.username
    if 'email' in st.session_state:
        del st.session_state.email
    if 'location' in st.session_state:
        del st.session_state.location
    if 'role' in st.session_state:
        del st.session_state.role
    if 'session_token' in st.session_state:
        del st.session_state.session_token

def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        return False
    
    if 'session_token' not in st.session_state:
        return False
    
    # Verify session is still valid
    session = get_session(st.session_state.session_token)
    if not session:
        logout_user()
        return False
    
    return True

def require_authentication():
    """Decorator to require authentication for pages"""
    if not check_authentication():
        render_login_page()
        return False
    return True

def render_login_page():
    """Render login/registration page"""
    st.title("🔐 Resume Evaluation System - Login")
    st.markdown("**Innomatics Research Labs** - Placement Team Portal")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if username and password:
                    if login_user(username, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
    
    with tab2:
        st.subheader("Register New Account")
        with st.form("register_form"):
            new_username = st.text_input("Username", key="reg_username")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
            location = st.selectbox("Location", 
                                  ["Hyderabad", "Bangalore", "Pune", "Delhi NCR", "Other"],
                                  key="reg_location")
            role = st.selectbox("Role", 
                              ["placement_team", "admin", "mentor"],
                              key="reg_role")
            
            register_button = st.form_submit_button("Register")
            
            if register_button:
                if not all([new_username, new_email, new_password, confirm_password, location]):
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    success, message = register_user(new_username, new_email, new_password, location, role)
                    if success:
                        st.success(message)
                        st.info("You can now login with your new account")
                    else:
                        st.error(message)

def render_user_info():
    """Render user information in sidebar"""
    if check_authentication():
        st.sidebar.markdown("---")
        st.sidebar.subheader("👤 User Info")
        st.sidebar.write(f"**Username:** {st.session_state.username}")
        st.sidebar.write(f"**Location:** {st.session_state.location}")
        st.sidebar.write(f"**Role:** {st.session_state.role.title()}")
        
        if st.sidebar.button("Logout"):
            logout_user()
            st.rerun()

def get_user_location():
    """Get current user's location"""
    if check_authentication():
        return st.session_state.location
    return None

def get_user_role():
    """Get current user's role"""
    if check_authentication():
        return st.session_state.role
    return None

def is_admin():
    """Check if current user is admin"""
    return get_user_role() == 'admin'

def can_access_analytics():
    """Check if user can access analytics"""
    role = get_user_role()
    return role in ['admin', 'placement_team']