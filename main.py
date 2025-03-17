import streamlit as st
from auth.manager import authenticate_user, register_user, create_session, validate_session
from chat.interface import render_chat_interface, load_user_sessions
from utils.styles import load_styles
from models.database import Session, User, UserSession

def main():
    load_styles()
    initialize_session_state()
    
    # Check for session token in query params
    if not st.session_state.get("session_token"):
        session_token = st.query_params.get("session")
        if session_token:
            st.session_state.session_token = session_token

    # Validate session token if exists
    if st.session_state.get("session_token") and not st.session_state.get("user_id"):
        user_id = validate_session(st.session_state.session_token)
        if user_id:
            st.session_state.user_id = user_id
            st.query_params["session"] = st.session_state.session_token
        else:
            clear_user_session()

    # Verify session validity for authenticated users
    if st.session_state.get("user_id"):
        verify_user_session()
        if st.query_params.get("session") != st.session_state.session_token:
            st.query_params["session"] = st.session_state.session_token
    
    with st.sidebar:
        render_navigation()
    
    if st.session_state.get("user_id"):
        render_authenticated_interface()
    else:
        render_auth_interface()

def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        'user_id': None,
        'sessions': [],
        'current_session': None,
        'session_loaded': False,
        'session_token': None
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    
    # Initialize current page from query params or default
    st.session_state.setdefault("current_page", st.query_params.get("page", "Chat"))

def verify_user_session():
    """Verify session validity on each load"""
    db = Session()
    try:
        user = db.query(User).get(st.session_state.user_id)
        if not user:
            clear_user_session()
    finally:
        db.close()

def clear_user_session():
    """Clear all session data and cookies"""
    if st.session_state.get("user_id"):
        db = Session()
        try:
            db.query(UserSession).filter_by(user_id=st.session_state.user_id).delete()
            db.commit()
        finally:
            db.close()
    
    keys = ['user_id', 'sessions', 'current_session', 'session_loaded', 'session_token']
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]
    
    st.query_params.clear()
    st.rerun()

def render_navigation():
    """Render sidebar navigation"""
    with st.sidebar:
        st.markdown("# 🏦 FinNav")
        st.markdown("---")
        
        nav_items = {
            "💬 Chat": "Chat",
            "📊 Budgeting": "Budgeting",
            "📈 Investments": "Investments",
            "🎮 Finance Games": "Games",
            "📚 Learning Hub": "Learning"
        }
        
        for icon, label in nav_items.items():
            btn_type = "primary" if st.session_state.current_page == label else "secondary"
            if st.button(
                f"{icon} {label}",
                key=label,
                use_container_width=True,
                type=btn_type
            ):
                st.session_state.current_page = label
                st.query_params["page"] = label
        
        st.markdown("---")
        
        if st.session_state.user_id:
            if st.button("🚪 Logout", use_container_width=True):
                clear_user_session()

def render_authenticated_interface():
    """Main interface for logged-in users"""
    if not st.session_state.session_loaded:
        load_user_sessions()
        st.session_state.session_loaded = True
    
    if st.session_state.current_page == "Chat":
        render_chat_interface()
    else:
        st.title(f"🚧 {st.session_state.current_page}")
        st.write("Feature coming soon!")

def render_auth_interface():
    """Authentication page"""
    st.title("🔐 Student Finance Assistant")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("Login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if user_id := authenticate_user(username, password):
                    session_token = create_session(user_id)
                    st.session_state.session_token = session_token
                    st.session_state.user_id = user_id
                    st.query_params["session"] = session_token
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    with tab2:
        with st.form("Register"):
            new_user = st.text_input("Choose Username")
            new_pass = st.text_input("Choose Password", type="password")
            if st.form_submit_button("Create Account"):
                if register_user(new_user, new_pass):
                    st.success("Account created! Please login")
                else:
                    st.error("Username already exists")

if __name__ == "__main__":
    main()