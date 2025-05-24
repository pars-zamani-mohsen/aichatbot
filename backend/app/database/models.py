from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # ارتباط با سایت‌ها
    websites = relationship("Website", back_populates="owner")

class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    domain = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String)  # pending, crawling, processing, ready, error
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # اطلاعات کراولینگ
    crawl_info = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # اطلاعات RAG
    collection_name = Column(String, nullable=True)
    embedding_model = Column(String, nullable=True)
    
    # ارتباط با کاربر
    owner = relationship("User", back_populates="websites")
    
    # ارتباط با چت‌ها
    chats = relationship("Chat", back_populates="website")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"))
    session_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # ارتباط با سایت
    website = relationship("Website", back_populates="chats")
    
    # ارتباط با پیام‌ها
    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    role = Column(String)  # user, assistant
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # اطلاعات RAG
    sources = Column(JSON, nullable=True)
    
    # ارتباط با چت
    chat = relationship("Chat", back_populates="messages") 