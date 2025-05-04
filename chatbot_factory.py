# chatbot_factory.py

from chatbot_rag import RAGChatbot as OnlineChatbot
from chatbot_rag_local import RAGChatbot as LocalChatbot

class ChatbotFactory:
    @staticmethod
    def create_chatbot(chatbot_type="online", **kwargs):
        if chatbot_type.lower() == "local":
            return LocalChatbot(
                db_directory=kwargs.get('db_directory', 'knowledge_base'),
                collection_name=kwargs.get('collection_name', 'website_data'),
                model_name=kwargs.get('model_name', 'llama3.2:latest')
            )
        else:  # online
            return OnlineChatbot(
                db_directory=kwargs.get('db_directory', 'knowledge_base'),
                collection_name=kwargs.get('collection_name', 'website_data'),
                api_key=kwargs.get('api_key'),
                model_name=kwargs.get('model_name', 'gpt-3.5-turbo')
            )