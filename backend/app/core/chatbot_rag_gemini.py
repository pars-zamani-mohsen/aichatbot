import google.generativeai as genai
from typing import List, Dict, Optional, Any
import logging
from pathlib import Path
from ..services.hybrid_searcher import HybridSearcher
from ..services.prompt_manager import PromptManager
from app.config import settings
import chromadb
import httpx
import os
import contextlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGChatbotGemini:
    def __init__(
        self,
        collection_name: str,
        google_api_key: str = None,
        model_name: str = None,
        max_tokens: int = None,
        temperature: float = None
    ):
        self.collection_name = collection_name
        self.model_name = model_name or "gemini-1.5-flash"
        self.max_tokens = max_tokens or int(settings.MAX_TOKENS)
        self.temperature = temperature or float(settings.TEMPERATURE)
        
        # تنظیم API key
        try:
            # غیرفعال کردن proxy محیطی موقتاً
            @contextlib.contextmanager
            def no_proxy():
                """Context manager برای غیرفعال کردن proxy"""
                original_env = {}
                proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']
                
                # ذخیره مقادیر اصلی
                for var in proxy_vars:
                    if var in os.environ:
                        original_env[var] = os.environ[var]
                        del os.environ[var]
                
                try:
                    yield
                finally:
                    # بازگرداندن مقادیر اصلی
                    for var, value in original_env.items():
                        os.environ[var] = value
            
            # تنظیم API key و ایجاد مدل
            with no_proxy():
                api_key = google_api_key or getattr(settings, 'GOOGLE_API_KEY', None)
                if not api_key:
                    raise ValueError("Google API key is required")
                
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens,
                    )
                )
                
        except Exception as e:
            logger.error(f"خطا در ایجاد Gemini client: {str(e)}")
            raise

        # ایجاد کلاینت ChromaDB و دریافت کالکشن
        # مسیر دیتابیس باید در پوشه knowledge_base/domain باشد
        db_path = Path("/app/knowledge_base") / collection_name
        logger.info(f"استفاده از مسیر دیتابیس: {db_path}")
        
        if not db_path.exists():
            logger.error(f"مسیر دیتابیس {db_path} وجود ندارد")
            raise ValueError(f"مسیر دیتابیس {db_path} وجود ندارد")
            
        self.db_client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self.db_client.get_collection(name=collection_name)
        
        # ایجاد موتور جستجو
        self.searcher = HybridSearcher(
            collection=self.collection,
            chunk_size=int(settings.CHUNK_SIZE),
            max_tokens=int(settings.MAX_TOKENS),
            tokens_per_min=int(settings.TOKENS_PER_MIN),
            embedding_model=settings.EMBEDDING_MODEL_NAME
        )
        
        # ایجاد مدیر پرامپت
        self.prompt_manager = PromptManager()
        
        # تاریخچه چت
        self.chat_history: List[Dict] = []
        
    def _extract_context(self, query: str, n_results: int = 5) -> List[str]:
        """استخراج کانتکست مرتبط با پرسش"""
        try:
            results = self.searcher.search(query, n_results=n_results)
            if not results['documents'][0]:
                return []
                
            context = []
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                if doc and metadata:
                    # اضافه کردن منبع به کانتکست
                    source = metadata.get('url', '')
                    context.append(f"منبع: {source}\n{doc}")
                    
            return context
            
        except Exception as e:
            logger.error(f"خطا در استخراج کانتکست: {str(e)}")
            return []
    
    def _create_messages(self, query: str, context: List[str]) -> List[Dict]:
        """ایجاد پیام‌ها برای ارسال به مدل"""
        # پرامپت سیستم
        system_prompt = self.prompt_manager.get_system_prompt()
        
        # پرامپت کاربر با کانتکست
        user_prompt = self.prompt_manager.generate_prompt(query, context)
        
        # ساخت لیست پیام‌ها
        messages = [
            {"role": "user", "parts": [system_prompt + "\n\n" + user_prompt]}
        ]
        
        # اضافه کردن تاریخچه چت
        history_length = int(settings.CHAT_HISTORY_LENGTH)
        for msg in self.chat_history[-history_length:]:
            messages.append({"role": msg["role"], "parts": [msg["content"]]})
            
        return messages
        
    def _extract_sources(self, context: List[str]) -> List[Dict]:
        """استخراج منابع از کانتکست"""
        sources = []
        for ctx in context:
            if ctx.startswith("منبع:"):
                url = ctx.split("\n")[0].replace("منبع:", "").strip()
                sources.append({"url": url})
        return sources
        
    def ask(self, query: str) -> Dict[str, Any]:
        """پرسش از چت‌بات با استفاده از RAG"""
        try:
            # تشخیص نوع کوئری
            query_type = self.prompt_manager.detect_query_type(query)
            logger.info(f"Query type detected: {query_type}")
            
            # جستجو در پایگاه دانش
            search_results = self.searcher.search(query, n_results=5, query_type=query_type)
            
            # اگر هیچ نتیجه‌ای پیدا نشد، به کاربر اطلاع دهیم
            if not search_results.get('has_results', False):
                return {
                    "answer": "متأسفانه اطلاعاتی در مورد این موضوع در پایگاه دانش موجود نیست. لطفاً سوال دیگری بپرسید.",
                    "sources": []
                }
            
            # آماده‌سازی متن‌های مرتبط
            relevant_texts = []
            for doc, metadata in zip(search_results['documents'][0], search_results['metadatas'][0]):
                if doc and metadata:
                    relevant_texts.append({
                        'text': doc,
                        'metadata': metadata
                    })
            
            # ایجاد پرامپت
            prompt = self.prompt_manager.create_prompt(
                query=query,
                relevant_texts=relevant_texts,
                query_type=query_type
            )
            
            # ارسال به مدل زبانی
            response = self.model.generate_content(prompt)
            
            if response.text:
                answer = response.text
            else:
                answer = "متأسفانه در پردازش درخواست شما مشکلی پیش آمده است."
            
            # استخراج منابع
            sources = []
            for text in relevant_texts:
                if text['metadata']:
                    sources.append({
                        'title': text['metadata'].get('title', ''),
                        'url': text['metadata'].get('url', ''),
                        'content': text['text'][:200] + '...' if len(text['text']) > 200 else text['text']
                    })
            
            # به‌روزرسانی تاریخچه چت
            self.chat_history.append({"role": "user", "content": query})
            self.chat_history.append({"role": "assistant", "content": answer})
            
            return {
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error in RAG chatbot Gemini: {str(e)}")
            return {
                "answer": "متأسفانه در پردازش درخواست شما مشکلی پیش آمده است. لطفاً دوباره تلاش کنید.",
                "sources": []
            }
            
    def reset_chat_history(self):
        """پاک کردن تاریخچه چت"""
        self.chat_history = [] 