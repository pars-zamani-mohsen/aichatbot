from typing import Optional
from .chatbot_rag import RAGChatbot
from .chatbot_rag_gemini import RAGChatbot as GeminiRAGChatbot
from .chatbot_rag_local import RAGChatbot as LocalRAGChatbot
from app.config import settings
from pathlib import Path

class ChatbotFactory:
    @staticmethod
    def create_chatbot(
        chatbot_type: str = 'openai',
        collection_name: str = None,
        openai_api_key: str = None,
        google_api_key: str = None,
        ollama_api_url: str = None
    ) -> RAGChatbot:
        """
        ایجاد یک نمونه از چت‌بات با توجه به نوع درخواستی
        
        Args:
            chatbot_type: نوع چت‌بات ('openai', 'gemini', یا 'local')
            collection_name: نام کالکشن
            openai_api_key: کلید API اپن‌ای
            google_api_key: کلید API گوگل
            ollama_api_url: آدرس API اولاما
            
        Returns:
            یک نمونه از چت‌بات
        """
        collection_name = collection_name or settings.COLLECTION_NAME
        openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        google_api_key = google_api_key or settings.GOOGLE_API_KEY
        ollama_api_url = ollama_api_url or settings.OLLAMA_API_URL
        
        if chatbot_type == 'openai':
            return RAGChatbot(
                collection_name=collection_name,
                openai_api_key=openai_api_key
            )
        elif chatbot_type == 'gemini':
            return GeminiRAGChatbot(
                collection_name=collection_name,
                google_api_key=google_api_key
            )
        elif chatbot_type == 'local':
            return LocalRAGChatbot(
                collection_name=collection_name,
                ollama_api_url=ollama_api_url
            )
        else:
            raise ValueError(f"نوع چت‌بات نامعتبر است: {chatbot_type}") 