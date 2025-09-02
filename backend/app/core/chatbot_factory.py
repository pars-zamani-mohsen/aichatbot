from typing import Optional
from .chatbot_rag import RAGChatbot
from .chatbot_rag_gemini import RAGChatbotGemini
from .chatbot_rag_local import RAGChatbot as LocalRAGChatbot
from app.config import settings
from app.services.system_settings_service import SystemSettingsService
from sqlalchemy.orm import Session
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ChatbotFactory:
    @staticmethod
    def create_chatbot(
        chatbot_type: str = 'openai',
        collection_name: str = None,
        openai_api_key: str = None,
        google_api_key: str = None,
        ollama_api_url: str = None,
        db: Session = None,
        **kwargs
    ) -> RAGChatbot:
        """
        ایجاد یک نمونه از چت‌بات با توجه به نوع درخواستی
        
        Args:
            chatbot_type: نوع چت‌بات ('openai', 'gemini', یا 'local')
            collection_name: نام کالکشن
            openai_api_key: کلید API اپن‌ای
            google_api_key: کلید API گوگل
            ollama_api_url: آدرس API اولاما
            **kwargs: پارامترهای اضافی
            
        Returns:
            یک نمونه از چت‌بات
        """
        collection_name = collection_name or settings.COLLECTION_NAME
        openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        google_api_key = google_api_key or settings.GOOGLE_API_KEY
        ollama_api_url = ollama_api_url or settings.OLLAMA_API_URL
        
        # بررسی فعال بودن مدل‌ها
        if db:
            try:
                system_settings = SystemSettingsService.get_all_settings(db)
                enable_openai = system_settings.get('enableOpenAI', True)
                enable_gemini = system_settings.get('enableGemini', True)
                enable_local = system_settings.get('enableLocal', False)
                
                logger.info(f"System settings - OpenAI: {enable_openai}, Gemini: {enable_gemini}, Local: {enable_local}")
                
                # بررسی فعال بودن مدل درخواستی
                if chatbot_type == 'openai' and not enable_openai:
                    logger.warning("OpenAI is disabled, falling back to Gemini")
                    chatbot_type = 'gemini' if enable_gemini else 'local' if enable_local else 'openai'
                elif chatbot_type == 'gemini' and not enable_gemini:
                    logger.warning("Gemini is disabled, falling back to OpenAI")
                    chatbot_type = 'openai' if enable_openai else 'local' if enable_local else 'gemini'
                elif chatbot_type == 'local' and not enable_local:
                    logger.warning("Local model is disabled, falling back to OpenAI")
                    chatbot_type = 'openai' if enable_openai else 'gemini' if enable_gemini else 'local'
                    
            except Exception as e:
                logger.error(f"Error checking system settings: {str(e)}")
        
        if chatbot_type == 'openai':
            return RAGChatbot(
                collection_name=collection_name,
                openai_api_key=openai_api_key,
                **kwargs
            )
        elif chatbot_type == 'gemini':
            return RAGChatbotGemini(
                collection_name=collection_name,
                google_api_key=google_api_key,
                **kwargs
            )
        elif chatbot_type == 'local':
            return LocalRAGChatbot(
                collection_name=collection_name,
                ollama_api_url=ollama_api_url,
                **kwargs
            )
        else:
            raise ValueError(f"نوع چت‌بات نامعتبر است: {chatbot_type}") 