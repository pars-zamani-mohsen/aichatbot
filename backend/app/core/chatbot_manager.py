import asyncio
import logging
from typing import Dict, Optional, Any
from threading import Lock, RLock
import time
from collections import defaultdict
from app.core.chatbot_factory import ChatbotFactory
from app.database.database import SessionLocal

logger = logging.getLogger(__name__)

class ChatbotManager:
    """مدیریت همزمانی چت‌ها و بهینه‌سازی منابع"""
    
    def __init__(self):
        self._chatbots: Dict[str, Any] = {}
        self._session_chatbots: Dict[str, Any] = {}  # Session-specific chatbots
        self._locks: Dict[str, RLock] = defaultdict(RLock)
        self._session_locks: Dict[str, RLock] = defaultdict(RLock)
        self._usage_count: Dict[str, int] = defaultdict(int)
        self._session_usage_count: Dict[str, int] = defaultdict(int)
        self._last_used: Dict[str, float] = {}
        self._session_last_used: Dict[str, float] = {}
        self._max_concurrent_chats = 50  # حداکثر چت همزمان
        self._chatbot_timeout = 300  # 5 دقیقه timeout
        self._cleanup_interval = 60  # هر 1 دقیقه cleanup
        self._global_lock = RLock()  # Global lock for cleanup operations
        
    def get_chatbot(self, collection_name: str, chatbot_type: str, db_session, session_id: str = None) -> Any:
        """دریافت یا ایجاد chatbot با مدیریت همزمانی"""
        if session_id:
            # Session-specific chatbot
            return self._get_session_chatbot(collection_name, chatbot_type, db_session, session_id)
        else:
            # Shared chatbot
            return self._get_shared_chatbot(collection_name, chatbot_type, db_session)
    
    def _get_session_chatbot(self, collection_name: str, chatbot_type: str, db_session, session_id: str) -> Any:
        """دریافت chatbot مخصوص session"""
        session_key = f"{collection_name}_{chatbot_type}_{session_id}"
        
        with self._session_locks[session_key]:
            # بررسی وجود chatbot برای این session
            if session_key in self._session_chatbots:
                chatbot = self._session_chatbots[session_key]
                self._session_usage_count[session_key] += 1
                self._session_last_used[session_key] = time.time()
                logger.info(f"Using existing session chatbot for {session_key}")
                return chatbot
            
            # بررسی محدودیت همزمانی
            with self._global_lock:
                total_chatbots = len(self._chatbots) + len(self._session_chatbots)
                if total_chatbots >= self._max_concurrent_chats:
                    self._cleanup_old_chatbots()
                    
                if len(self._chatbots) + len(self._session_chatbots) >= self._max_concurrent_chats:
                    raise Exception("Maximum concurrent chats reached")
            
            # ایجاد chatbot جدید برای این session
            try:
                chatbot = ChatbotFactory.create_chatbot(
                    chatbot_type=chatbot_type,
                    collection_name=collection_name,
                    max_tokens=1000,
                    temperature=0.7,
                    db=db_session
                )
                
                self._session_chatbots[session_key] = chatbot
                self._session_usage_count[session_key] = 1
                self._session_last_used[session_key] = time.time()
                
                logger.info(f"Created new session chatbot for {session_key}")
                return chatbot
                
            except Exception as e:
                logger.error(f"Error creating session chatbot for {session_key}: {e}")
                raise
    
    def _get_shared_chatbot(self, collection_name: str, chatbot_type: str, db_session) -> Any:
        """دریافت chatbot مشترک"""
        chatbot_key = f"{collection_name}_{chatbot_type}"
        
        with self._locks[chatbot_key]:
            # بررسی وجود chatbot
            if chatbot_key in self._chatbots:
                chatbot = self._chatbots[chatbot_key]
                self._usage_count[chatbot_key] += 1
                self._last_used[chatbot_key] = time.time()
                logger.info(f"Using existing shared chatbot for {chatbot_key}")
                return chatbot
            
            # بررسی محدودیت همزمانی
            with self._global_lock:
                total_chatbots = len(self._chatbots) + len(self._session_chatbots)
                if total_chatbots >= self._max_concurrent_chats:
                    self._cleanup_old_chatbots()
                    
                if len(self._chatbots) + len(self._session_chatbots) >= self._max_concurrent_chats:
                    raise Exception("Maximum concurrent chats reached")
            
            # ایجاد chatbot جدید
            try:
                chatbot = ChatbotFactory.create_chatbot(
                    chatbot_type=chatbot_type,
                    collection_name=collection_name,
                    max_tokens=1000,
                    temperature=0.7,
                    db=db_session
                )
                
                self._chatbots[chatbot_key] = chatbot
                self._usage_count[chatbot_key] = 1
                self._last_used[chatbot_key] = time.time()
                
                logger.info(f"Created new shared chatbot for {chatbot_key}")
                return chatbot
                
            except Exception as e:
                logger.error(f"Error creating shared chatbot for {chatbot_key}: {e}")
                raise
    
    def release_chatbot(self, collection_name: str, chatbot_type: str, session_id: str = None):
        """آزادسازی chatbot"""
        if session_id:
            # آزادسازی session chatbot
            session_key = f"{collection_name}_{chatbot_type}_{session_id}"
            with self._session_locks[session_key]:
                if session_key in self._session_usage_count:
                    self._session_usage_count[session_key] -= 1
                    if self._session_usage_count[session_key] <= 0:
                        self._remove_session_chatbot(session_key)
        else:
            # آزادسازی shared chatbot
            chatbot_key = f"{collection_name}_{chatbot_type}"
            with self._locks[chatbot_key]:
                if chatbot_key in self._usage_count:
                    self._usage_count[chatbot_key] -= 1
                    if self._usage_count[chatbot_key] <= 0:
                        self._remove_chatbot(chatbot_key)
    
    def _cleanup_old_chatbots(self):
        """پاکسازی chatbot های قدیمی"""
        current_time = time.time()
        
        # پاکسازی shared chatbots
        keys_to_remove = []
        for key, last_used in self._last_used.items():
            if current_time - last_used > self._chatbot_timeout:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_chatbot(key)
        
        # پاکسازی session chatbots
        session_keys_to_remove = []
        for key, last_used in self._session_last_used.items():
            if current_time - last_used > self._chatbot_timeout:
                session_keys_to_remove.append(key)
        
        for key in session_keys_to_remove:
            self._remove_session_chatbot(key)
    
    def _remove_chatbot(self, chatbot_key: str):
        """حذف shared chatbot"""
        if chatbot_key in self._chatbots:
            del self._chatbots[chatbot_key]
            del self._usage_count[chatbot_key]
            del self._last_used[chatbot_key]
            logger.info(f"Removed shared chatbot {chatbot_key}")
    
    def _remove_session_chatbot(self, session_key: str):
        """حذف session chatbot"""
        if session_key in self._session_chatbots:
            del self._session_chatbots[session_key]
            del self._session_usage_count[session_key]
            del self._session_last_used[session_key]
            logger.info(f"Removed session chatbot {session_key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """دریافت آمار chatbot ها"""
        return {
            "active_shared_chatbots": len(self._chatbots),
            "active_session_chatbots": len(self._session_chatbots),
            "total_active_chatbots": len(self._chatbots) + len(self._session_chatbots),
            "max_concurrent": self._max_concurrent_chats,
            "shared_usage_count": dict(self._usage_count),
            "session_usage_count": dict(self._session_usage_count),
        }
    
    def clear_all(self):
        """پاکسازی همه chatbot ها"""
        with self._global_lock:
            self._chatbots.clear()
            self._session_chatbots.clear()
            self._usage_count.clear()
            self._session_usage_count.clear()
            self._last_used.clear()
            self._session_last_used.clear()
            logger.info("All chatbots cleared")

# Global instance
chatbot_manager = ChatbotManager()
