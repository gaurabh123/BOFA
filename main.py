import streamlit as st
from auth.manager import authenticate_user, register_user, create_session, validate_session
from chat.interface import render_chat_interface, load_user_sessions
from utils.styles import load_styles
from models.database import Session, User, UserSession
import time

def financial_questionnaire():
    st.subheader("Financial Profile Setup")
    profile = {}
    
    col1, col2 = st.columns(2)
    with col1:
        profile['age'] = st.number_input("Age", min_value=13, max_value=100)
        profile['income'] = st.number_input("Monthly Income ($)", min_value=0)
    with col2:
        profile['expenses'] = st.number_input("Monthly Expenses ($)", min_value=0)
        profile['debt'] = st.number_input("Current Debt ($)", min_value=0)
    
    profile['goals'] = st.multiselect(
        "Financial Goals",
        ["Debt Reduction", "Savings Growth", "Investing", "Budgeting", "Credit Building"]
    )
    
    profile['risk_tolerance'] = st.select_slider(
        "Risk Tolerance",
        options=["Very Conservative", "Conservative", "Moderate", "Aggressive", "Very Aggressive"]
    )

    profile['student_status'] = st.selectbox(
        "Student Status",
        ["High School", "Undergraduate", "Graduate", "PhD Candidate"]
    )

    profile['graduation_year'] = st.number_input(
        "Expected Graduation Year", 
        min_value=2024, 
        max_value=2030
    )
    
    return profile

def main():
    load_styles()
    initialize_session_state()
    
    if not st.session_state.get("session_token"):
        session_token = st.query_params.get("session")
        if session_token:
            st.session_state.session_token = session_token

    if st.session_state.get("session_token") and not st.session_state.get("user_id"):
        user_id = validate_session(st.session_state.session_token)
        if user_id:
            st.session_state.user_id = user_id
            st.query_params["session"] = st.session_state.session_token
        else:
            clear_user_session()

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
    defaults = {
        'user_id': None,
        'sessions': [],
        'current_session': None,
        'session_loaded': False,
        'session_token': None
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    st.session_state.setdefault("current_page", st.query_params.get("page", "Chat"))

def verify_user_session():
    db = Session()
    try:
        user = db.get(User, st.session_state.user_id)  
        if not user:
            clear_user_session()
    finally:
        db.close()

def clear_user_session():
    if st.session_state.get("user_id"):
        db = Session()
        try:
            db.query(UserSession).filter_by(user_id=st.session_state.user_id).delete()
            db.commit()
        finally:
            db.close()
    
    keys = ['user_id', 'sessions', 'current_session', 'session_loaded', 'session_token']
    for key in keys:
        st.session_state.pop(key, None)
    
    st.query_params.clear()
    st.rerun()

def render_navigation():
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
            if st.button(f"{icon} {label}", key=label, use_container_width=True, type=btn_type):
                st.session_state.current_page = label
                st.query_params["page"] = label
        st.markdown("---")
        if st.session_state.user_id and st.button("🚪 Logout", use_container_width=True):
            clear_user_session()

def render_authenticated_interface():
    if not st.session_state.session_loaded:
        load_user_sessions()
        st.session_state.session_loaded = True
    
    if st.session_state.current_page == "Chat":
        render_chat_interface()
    else:
        st.title(f"🚧 {st.session_state.current_page}")
        st.write("Feature coming soon!")

def render_auth_interface():
    st.title("🔐 Student Finance Assistant")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("Login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if not username or not password:
                    st.error("Please fill in all fields")
                elif user_id := authenticate_user(username, password):
                    session_token = create_session(user_id)
                    st.session_state.update({
                        'user_id': user_id,
                        'session_token': session_token
                    })
                    st.query_params["session"] = session_token
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    with tab2:
        with st.form("Register"):
            new_user = st.text_input("Choose Username")
            new_pass = st.text_input("Choose Password", type="password")
            profile = financial_questionnaire()
            
            if st.form_submit_button("Create Account"):
                errors = []
                if len(new_user.strip()) < 4:
                    errors.append("Username must be at least 4 characters")
                if len(new_pass) < 8:
                    errors.append("Password must be at least 8 characters")
                if not profile.get('age'):
                    errors.append("Age is required")
                if not profile.get('goals'):
                    errors.append("Select at least one financial goal")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    try:
                        if register_user(new_user, new_pass, profile):
                            user_id = authenticate_user(new_user, new_pass)
                            if user_id:
                                session_token = create_session(user_id)
                                st.session_state.update({
                                    'user_id': user_id,
                                    'session_token': session_token
                                })
                                st.query_params["session"] = session_token
                                st.toast("🎉 Account created successfully!", icon="✅")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Auto-login failed")
                        else:
                            st.error("Username already exists")
                    except Exception as e:
                        st.error(f"Registration failed: {str(e)}")

if __name__ == "__main__":
    main()