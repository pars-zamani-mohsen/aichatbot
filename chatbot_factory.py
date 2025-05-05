import os
from chatbot_rag import RAGChatbot as OpenAIChatbot
from chatbot_rag_local import RAGChatbot as LocalChatbot
from chatbot_rag_gemini import RAGChatbot as GeminiChatbot

class ChatbotFactory:
     @staticmethod
     def create_chatbot(chatbot_type="online", **kwargs):
         if chatbot_type == "local":
             return LocalChatbot(
                 db_directory=kwargs.get('db_directory', 'knowledge_base'),
                 collection_name=kwargs.get('collection_name', 'website_data'),
                 model_name=kwargs.get('model_name', 'llama3.2:latest')
             )
         elif chatbot_type == "gemini":
             api_key = kwargs.get('api_key') or os.environ.get('GOOGLE_API_KEY')
             return GeminiChatbot(
                 db_directory=kwargs.get('db_directory', 'knowledge_base'),
                 collection_name=kwargs.get('collection_name', 'website_data'),
                 api_key=api_key,
                 model_name=kwargs.get('model_name', 'gemini-2.0-flash')  # تغییر به مدل صحیح
             )
         else:  # online (openai)
             return OpenAIChatbot(
                 db_directory=kwargs.get('db_directory', 'knowledge_base'),
                 collection_name=kwargs.get('collection_name', 'website_data'),
                 api_key=kwargs.get('api_key'),
                 model_name=kwargs.get('model_name', 'gpt-4.1')
             )