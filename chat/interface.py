import streamlit as st
from models.database import Session, ChatSession, ChatMessage
from chat.logic import FinancialAdvisor
import datetime

def get_user_session_count(user_id: int) -> int:
    """Get total sessions count for a user"""
    db = Session()
    try:
        return db.query(ChatSession).filter_by(user_id=user_id).count()
    finally:
        db.close()

def create_new_session():
    """Create new sequentially numbered session for current user"""
    db = Session()
    try:
        session_num = get_user_session_count(st.session_state.user_id) + 1
        new_session = ChatSession(
            user_id=st.session_state.user_id,
            title=f"Session {session_num} - {datetime.datetime.now().strftime('%b %d %H:%M')}"
        )
        db.add(new_session)
        db.commit()
        
        # Update session list and current session
        st.session_state.sessions = [new_session] + st.session_state.sessions
        st.session_state.current_session = new_session.id
        
    finally:
        db.close()
    # Removed st.rerun() here

def load_user_sessions():
    """Load user-specific sessions from database"""
    db = Session()
    try:
        st.session_state.sessions = db.query(ChatSession).filter_by(
            user_id=st.session_state.user_id
        ).order_by(ChatSession.created_at.desc()).all()
        
        if not st.session_state.sessions:
            create_new_session()
        else:
            st.session_state.current_session = st.session_state.sessions[0].id
    finally:
        db.close()

def render_chat_interface():
    """Main chat interface component"""
    st.header("💬 Financial Chat Assistant")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### Chat Sessions")
        st.button("➕ New Chat", on_click=create_new_session, use_container_width=True)
        
        if st.session_state.sessions:
            selected = st.selectbox(
                "History",
                options=[s.id for s in st.session_state.sessions],
                format_func=lambda x: next(s.title for s in st.session_state.sessions if s.id == x),
                key="session_selector"
            )
            if selected != st.session_state.current_session:
                st.session_state.current_session = selected
                st.rerun()
    
    with col2:
        if st.session_state.current_session:
            db = Session()
            try:
                messages = db.query(ChatMessage).filter_by(
                    session_id=st.session_state.current_session
                ).order_by(ChatMessage.timestamp).all()
                
                for msg in messages:
                    with st.chat_message("assistant" if msg.is_bot else "user"):
                        st.markdown(msg.content)
            finally:
                db.close()
            
            if prompt := st.chat_input("Ask about student finances..."):
                db = Session()
                try:
                    # Save user message
                    user_msg = ChatMessage(
                        session_id=st.session_state.current_session,
                        content=prompt,
                        is_bot=0
                    )
                    db.add(user_msg)
                    
                    # Get and save bot response
                    response = FinancialAdvisor().get_response(prompt)
                    bot_msg = ChatMessage(
                        session_id=st.session_state.current_session,
                        content=response,
                        is_bot=1
                    )
                    db.add(bot_msg)
                    db.commit()
                    st.rerun()
                finally:
                    db.close()
        else:
            create_new_session()