from models.database import User, UserSession, Session
import bcrypt
import secrets
from datetime import datetime, timedelta

def authenticate_user(username: str, password: str) -> int:
    """Returns user ID if authenticated, else 0"""
    db = Session()
    try:
        user = db.query(User).filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode(), user.password_hash):
            return user.id
        return 0
    finally:
        db.close()

def register_user(username: str, password: str) -> bool:
    db = Session()
    try:
        if db.query(User).filter_by(username=username).first():
            return False
            
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        new_user = User(username=username, password_hash=hashed)
        db.add(new_user)
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def create_session(user_id: int) -> str:
    """Create and return new session token"""
    db = Session()
    try:
        # Delete existing sessions
        db.query(UserSession).filter_by(user_id=user_id).delete()
        
        # Generate new token
        token = secrets.token_urlsafe(64)
        expires = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession(
            session_token=token,
            user_id=user_id,
            expires_at=expires
        )
        db.add(session)
        db.commit()
        return token
    finally:
        db.close()

def validate_session(token: str) -> int:
    """Validate session token and return user ID if valid"""
    db = Session()
    try:
        session = db.query(UserSession).filter_by(session_token=token).first()
        if session and session.expires_at > datetime.utcnow():
            return session.user_id
        return 0
    finally:
        db.close()