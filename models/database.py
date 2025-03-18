from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password_hash = Column(String(100))
    financial_profile = Column(JSON)
    sessions = relationship("ChatSession", back_populates="user")
    auth_sessions = relationship("UserSession", back_populates="user")

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'))
    content = Column(Text)
    is_bot = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    session = relationship("ChatSession", back_populates="messages")

class UserSession(Base):
    __tablename__ = 'user_sessions'
    session_token = Column(String(100), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)
    user = relationship("User", back_populates="auth_sessions")

engine = create_engine('sqlite:///finance_chatbot.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)