from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=False)  # نیاز به فعال‌سازی
    is_verified = Column(Boolean, default=False)  # تأیید ایمیل
    role = Column(String, default="user")  # user, admin
    verification_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # ارتباط با سایت‌ها
    websites = relationship("Website", back_populates="owner")
    
    # ارتباط با تنظیمات
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    
    # ارتباط با اعلان‌ها
    notifications = relationship("Notification", back_populates="user")

class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    domain = Column(String, index=True)
    name = Column(String, nullable=True)  # نام اختیاری وب‌سایت
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
    
    # اطلاعات ویجت
    public_key = Column(String, nullable=True)
    widget_config = Column(JSON, nullable=True)
    
    # تنظیمات اختصاصی وب‌سایت
    crawl_settings = Column(JSON, nullable=True)  # تنظیمات کراولینگ
    rag_settings = Column(JSON, nullable=True)    # تنظیمات RAG
    widget_settings = Column(JSON, nullable=True) # تنظیمات ویجت
    domain_verified = Column(Boolean, default=False)  # تأیید مالکیت دامنه
    verification_token = Column(String, nullable=True)  # توکن تأیید
    
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
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"))
    role = Column(String, nullable=False)  # user یا assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    sources = Column(JSON, nullable=True)  # برای ذخیره منابع در پاسخ‌های assistant

    # رابطه با چت
    chat = relationship("Chat", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, chat_id={self.chat_id}, role={self.role})>"

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # اطلاعات شخصی
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    # تنظیمات امنیت
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_code = Column(String, nullable=True)
    two_factor_expires = Column(DateTime(timezone=True), nullable=True)
    two_factor_attempts = Column(Integer, default=0)
    two_factor_locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Rate limiting برای لاگین
    login_attempts = Column(Integer, default=0)
    login_locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_attempt = Column(DateTime(timezone=True), nullable=True)
    
    # تنظیمات اعلان‌ها
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    notify_on_new_conversation = Column(Boolean, default=True)
    notify_on_website_update = Column(Boolean, default=True)
    
    # تنظیمات ظاهری
    language = Column(String, default="fa")
    theme = Column(String, default="light")
    timezone = Column(String, default="Asia/Tehran")
    
    # تنظیمات RAG
    default_k = Column(Integer, default=5)
    max_response_length = Column(Integer, default=500)
    default_temperature = Column(Integer, default=7)  # 0.7 * 10
    default_language = Column(String, default="fa")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # ارتباط با کاربر
    user = relationship("User", back_populates="settings")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="info")  # info, success, warning, error
    category = Column(String, default="general")  # conversation, website, security, system
    is_read = Column(Boolean, default=False)
    is_sent_email = Column(Boolean, default=False)
    is_sent_push = Column(Boolean, default=False)
    is_sent_sms = Column(Boolean, default=False)
    extra_data = Column(JSON, nullable=True)  # اطلاعات اضافی
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # ارتباط با کاربر
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type})>"

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String, default="string")  # string, integer, float, boolean, json
    description = Column(Text, nullable=True)
    category = Column(String, default="general")  # general, email, security, rag, crawler, storage, notifications
    is_public = Column(Boolean, default=False)  # آیا این تنظیم برای کاربران عادی قابل مشاهده است
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<SystemSettings(key={self.key}, value={self.value})>" 