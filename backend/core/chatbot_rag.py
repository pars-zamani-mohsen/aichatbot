import os
import re
import json
import chromadb
import argparse
from openai import OpenAI
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from core.text_processor import TextProcessor
from core.hybrid_searcher import HybridSearcher
from core.prompt_manager import PromptManager
from chromadb.utils import embedding_functions
from chromadb.utils.embedding_functions import EmbeddingFunction
from chromadb.api.types import EmbeddingFunction

from settings import (
    DB_DIRECTORY,
    COLLECTION_NAME,
    OPENAI_MODEL_NAME,
    EMBEDDING_MODEL_NAME,
    MAX_CHAT_HISTORY
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PERSIAN_STOPWORDS = set([
    "و", "در", "به", "از", "که", "را", "با", "برای", "این", "آن", "یک", "تا", "می", "بر",
    "است", "بود", "شود", "کرد", "های", "هم", "اما", "یا", "اگر", "نیز", "بین", "هر",
    "روی", "پس", "چه", "همه", "چون", "چرا", "کجا", "کی", "چگونه"
])

class SentenceTransformerEmbedding(EmbeddingFunction):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(input)
        return embeddings.tolist()

class RAGChatbot:
    def __init__(self, collection_name: str = COLLECTION_NAME,
                 api_key: Optional[str] = None,
                 model_name: str = OPENAI_MODEL_NAME,
                 db_directory: str = DB_DIRECTORY):
        """Initialize RAG chatbot with dependencies"""

        # Initialize Chroma client
        self.db_client = chromadb.PersistentClient(path=db_directory)

        # Initialize core components
        self.text_processor = TextProcessor()
        self.prompt_manager = PromptManager()

        # Initialize models
        self.embedding_function = SentenceTransformer(EMBEDDING_MODEL_NAME)

        # Set API key and model
        if api_key:
            self.api_key = api_key
        elif 'OPENAI_API_KEY' in os.environ:
            self.api_key = os.environ['OPENAI_API_KEY']
        else:
            raise ValueError("OpenAI API key not specified. Please set it in OPENAI_API_KEY environment variable or pass as parameter.")

        # Create OpenAI client
        self.openai_client = OpenAI(api_key=self.api_key)
        self.model_name = model_name

        # Get or create collection
        self.collection = self.db_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Initialize hybrid searcher
        self.searcher = HybridSearcher(collection=self.collection)

        # Chat history management
        self.chat_history = []
        self.max_history = MAX_CHAT_HISTORY

        # Set system prompt
        self.system_prompt = """You are an intelligent assistant that answers user questions.
        Use the following information to answer user questions. If there isn't enough information in the sources, honestly tell the user.
        Provide your responses in Persian and speak naturally and conversationally.
        """
        self.system_prompt += "\nWhen answering, if information from a specific source is used, cite the source number as [n] in the response text."

    async def get_response(self, query: str, collection_name: str = None) -> str:
        """Get response from chatbot"""
        if collection_name:
            self.collection = self.db_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.searcher = HybridSearcher(collection=self.collection)

        answer, _ = self.answer_question(query, self.chat_history)
        
        # Add to chat history
        self.chat_history.append({"role": "user", "content": query})
        self.chat_history.append({"role": "assistant", "content": answer})

        # Limit chat history length
        if len(self.chat_history) > self.max_history:
            self.chat_history = self.chat_history[-self.max_history:]

        return answer

    @staticmethod
    def is_garbage_context(text):
        # Remove punctuation and split
        words = re.findall(r'\w+', text)
        if not words:
            return True
        stopword_count = sum(1 for w in words if w in PERSIAN_STOPWORDS)
        if len(text.strip()) < 50:
            return True
        if stopword_count / len(words) > 0.7:
            return True
        return False

    def search_knowledge_base(self, query, n_results=5, query_type='general'):
        """جستجو با موتور جستجوی هیبرید"""
        return self.searcher.search(query, n_results, query_type)

    @staticmethod
    def has_phrase_match(query, doc, n=2):
        query_words = query.strip().split()
        for i in range(len(query_words) - n + 1):
            phrase = ' '.join(query_words[i:i+n])
            if re.search(re.escape(phrase), doc):
                return True
        return False

    def get_relevant_context(self, query: str, n_results: int = 3, query_type: str = 'general') -> str:
        """Get relevant context from knowledge base"""
        results = self.searcher.search(query, n_results, query_type)

        if not results or not results["documents"] or not results["documents"][0]:
            return "No information found."

        context = ""
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            title = meta.get('title', 'No title')
            url = meta.get('url', 'No URL')
            context += f"\n=== Source {i+1}: {title} ===\nURL: {url}\n{doc}\n"

        return context

    def answer_question(self, query: str, chat_history=None, n_results=5):
        """Answer user question using RAG"""
        query_type = self.prompt_manager.detect_query_type(query)
        relevant_context = self.get_relevant_context(query, n_results, query_type)

        if relevant_context == "No information found.":
            return "I'm sorry, I couldn't find relevant information in the knowledge base to answer your question.", relevant_context

        prompt = self.prompt_manager.get_prompt(query, relevant_context, query_type)
        messages = [{"role": "system", "content": self.system_prompt + f"\n\nRelevant information:\n{relevant_context}"}]
        if chat_history:
            messages.extend(chat_history[-MAX_CHAT_HISTORY:])
        messages.append({"role": "user", "content": query})

        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.5,
            max_tokens=2000
        )
        answer = response.choices[0].message.content

        # Extract sources
        sources = []
        seen_urls = set()
        for line in relevant_context.split("\n"):
            if line.startswith("URL:"):
                url = line[4:].strip()
                if url not in seen_urls:
                    seen_urls.add(url)
                    sources.append(url)
        if sources:
            answer += "\n\nSources:\n"
            for idx, src in enumerate(sources, 1):
                answer += f"{idx}. [Source {idx}]({src})\n"

        return answer, relevant_context

    def chat_loop(self, n_results=5):
        """Main interaction loop with user"""

        print("\n=== RAG Chatbot ===")
        print("Type 'exit' or 'quit' to end the conversation.\n")

        chat_history = []

        while True:
            # Get query from user
            query = input("\nYou: ")

            # Check for exit
            if query.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break

            # Answer query
            answer, relevant_context = self.answer_question(query, chat_history, n_results)

            # Print answer
            print(f"\nChatbot: {answer}")

            # Add to chat history
            chat_history.append({"role": "user", "content": query})
            chat_history.append({"role": "assistant", "content": answer})

            # Limit chat history length
            if len(chat_history) > MAX_CHAT_HISTORY:
                chat_history = chat_history[-MAX_CHAT_HISTORY:]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='RAG Chatbot')
    parser.add_argument('--db_dir', default='knowledge_base', help='Knowledge base directory')
    parser.add_argument('--collection', default='website_data', help='Collection name')
    parser.add_argument('--api_key', help='OpenAI API key')
    parser.add_argument('--model', default='gpt-3.5-turbo', help='OpenAI model name')

    args = parser.parse_args()

    try:
        chatbot = RAGChatbot(
            db_directory=args.db_dir,
            collection_name=args.collection,
            api_key=args.api_key,
            model_name=args.model
        )
        chatbot.chat_loop()
    except Exception as e:
        print(f"Error running chatbot: {e}")