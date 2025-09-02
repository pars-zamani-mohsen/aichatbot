import asyncio
import logging
from typing import Dict, Optional, Any
from threading import Lock
import time
from collections import defaultdict
from app.core.chatbot_factory import ChatbotFactory
from app.database.database import SessionLocal

logger = logging.getLogger(__name__)

class ChatbotManager:
    """مدیریت همزمانی چت‌ها و بهینه‌سازی منابع"""
    
    def __init__(self):
        self._chatbots: Dict[str, Any] = {}
        self._locks: Dict[str, Lock] = defaultdict(Lock)
        self._usage_count: Dict[str, int] = defaultdict(int)
        self._last_used: Dict[str, float] = {}
        self._max_concurrent_chats = 50  # حداکثر چت همزمان
        self._chatbot_timeout = 300  # 5 دقیقه timeout
        self._cleanup_interval = 60  # هر 1 دقیقه cleanup
        
    def get_chatbot(self, collection_name: str, chatbot_type: str, db_session) -> Any:
        """دریافت یا ایجاد chatbot با مدیریت همزمانی"""
        chatbot_key = f"{collection_name}_{chatbot_type}"
        
        with self._locks[chatbot_key]:
            # بررسی وجود chatbot
            if chatbot_key in self._chatbots:
                chatbot = self._chatbots[chatbot_key]
                self._usage_count[chatbot_key] += 1
                self._last_used[chatbot_key] = time.time()
                logger.info(f"Using existing chatbot for {chatbot_key}")
                return chatbot
            
            # بررسی محدودیت همزمانی
            if len(self._chatbots) >= self._max_concurrent_chats:
                self._cleanup_old_chatbots()
                
            if len(self._chatbots) >= self._max_concurrent_chats:
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
                
                logger.info(f"Created new chatbot for {chatbot_key}")
                return chatbot
                
            except Exception as e:
                logger.error(f"Error creating chatbot for {chatbot_key}: {e}")
                raise
    
    def release_chatbot(self, collection_name: str, chatbot_type: str):
        """آزادسازی chatbot"""
        chatbot_key = f"{collection_name}_{chatbot_type}"
        
        with self._locks[chatbot_key]:
            if chatbot_key in self._usage_count:
                self._usage_count[chatbot_key] -= 1
                if self._usage_count[chatbot_key] <= 0:
                    self._remove_chatbot(chatbot_key)
    
    def _cleanup_old_chatbots(self):
        """پاکسازی chatbot های قدیمی"""
        current_time = time.time()
        keys_to_remove = []
        
        for key, last_used in self._last_used.items():
            if current_time - last_used > self._chatbot_timeout:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_chatbot(key)
    
    def _remove_chatbot(self, chatbot_key: str):
        """حذف chatbot"""
        if chatbot_key in self._chatbots:
            del self._chatbots[chatbot_key]
            del self._usage_count[chatbot_key]
            del self._last_used[chatbot_key]
            logger.info(f"Removed chatbot {chatbot_key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """دریافت آمار chatbot ها"""
        return {
            "active_chatbots": len(self._chatbots),
            "max_concurrent": self._max_concurrent_chats,
            "usage_count": dict(self._usage_count),
            "last_used": {k: time.time() - v for k, v in self._last_used.items()}
        }

# Instance سراسری
chatbot_manager = ChatbotManager()
