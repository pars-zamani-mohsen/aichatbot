import os
from chatbot_rag import RAGChatbot as OpenAIChatbot
from chatbot_rag_local import RAGChatbot as LocalChatbot
from chatbot_rag_gemini import RAGChatbot as GeminiChatbot

from settings import (
    DB_DIRECTORY, COLLECTION_NAME,
    LOCAL_MODEL_NAME, GEMINI_MODEL_NAME, OPENAI_MODEL_NAME,
    GOOGLE_API_KEY, OPENAI_API_KEY
)

class ChatbotFactory:
    @staticmethod
    def create_chatbot(chatbot_type="online", **kwargs):
        if chatbot_type == "local":
            return LocalChatbot(
                db_directory=kwargs.get('db_directory', DB_DIRECTORY),
                collection_name=kwargs.get('collection_name', COLLECTION_NAME),
                model_name=kwargs.get('model_name', LOCAL_MODEL_NAME)
            )
        elif chatbot_type == "gemini":
            return GeminiChatbot(
                db_directory=kwargs.get('db_directory', DB_DIRECTORY),
                collection_name=kwargs.get('collection_name', COLLECTION_NAME),
                api_key=kwargs.get('api_key', GOOGLE_API_KEY),
                model_name=kwargs.get('model_name', GEMINI_MODEL_NAME)
            )
        else:  # online (openai)
            return OpenAIChatbot(
                db_directory=kwargs.get('db_directory', DB_DIRECTORY),
                collection_name=kwargs.get('collection_name', COLLECTION_NAME),
                api_key=kwargs.get('api_key', OPENAI_API_KEY),
                model_name=kwargs.get('model_name', OPENAI_MODEL_NAME)
            )