import openai
from typing import List, Dict, Optional
import logging
from pathlib import Path
from ..services.hybrid_searcher import HybridSearcher
from ..services.prompt_manager import PromptManager
from app.config import settings
import chromadb
import httpx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGChatbot:
    def __init__(
        self,
        collection_name: str,
        openai_api_key: str = None,
        model_name: str = None,
        max_tokens: int = None,
        temperature: float = None
    ):
        self.collection_name = collection_name
        self.model_name = model_name or settings.OPENAI_MODEL_NAME
        self.max_tokens = max_tokens or int(settings.MAX_TOKENS)
        self.temperature = temperature or float(settings.TEMPERATURE)
        
        # تنظیم API key
        self.client = openai.OpenAI(
            api_key=openai_api_key or settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE_URL if hasattr(settings, 'OPENAI_API_BASE_URL') and settings.OPENAI_API_BASE_URL else None,
            http_client=httpx.Client(timeout=30.0)
        )

        # ایجاد کلاینت ChromaDB و دریافت کالکشن
        # مسیر دیتابیس باید در پوشه knowledge_base/domain باشد
        db_path = Path("/var/www/html/ai/backend/knowledge_base") / collection_name
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
                
            return [
                f"منبع: {meta.get('url', 'نامشخص')}\n{doc}"
                for doc, meta in zip(results['documents'][0], results['metadatas'][0])
            ]
            
        except Exception as e:
            logger.error(f"خطا در استخراج کانتکست: {str(e)}")
            return []
            
    def _create_messages(self, query: str, context: List[str]) -> List[Dict]:
        """ایجاد لیست پیام‌ها برای API"""
        # پرامپت سیستم
        system_prompt = self.prompt_manager.get_system_prompt()
        
        # پرامپت کاربر با کانتکست
        user_prompt = self.prompt_manager.generate_prompt(query, context)
        
        # ساخت لیست پیام‌ها
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # اضافه کردن تاریخچه چت
        history_length = int(settings.CHAT_HISTORY_LENGTH)
        for msg in self.chat_history[-history_length:]:
            messages.append(msg)
            
        # اضافه کردن پیام جدید
        messages.append({"role": "user", "content": user_prompt})
        
        return messages
        
    def _extract_sources(self, context: List[str]) -> List[Dict]:
        """استخراج منابع از کانتکست"""
        sources = []
        for ctx in context:
            if ctx.startswith("منبع:"):
                url = ctx.split("\n")[0].replace("منبع:", "").strip()
                sources.append({"url": url})
        return sources
        
    def ask(self, question: str) -> Dict:
        """پرسش از چت‌بات"""
        try:
            # استخراج کانتکست
            context = self._extract_context(question)
            
            # ایجاد پیام‌ها
            messages = self._create_messages(question, context)
            
            # ارسال درخواست به API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # استخراج پاسخ
            answer = response.choices[0].message.content
            
            # به‌روزرسانی تاریخچه چت
            self.chat_history.append({"role": "user", "content": question})
            self.chat_history.append({"role": "assistant", "content": answer})
            
            # استخراج منابع
            sources = self._extract_sources(context)
            
            return {
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"خطا در پاسخ به پرسش: {str(e)}")
            return {
                "answer": "متأسفانه در پاسخ به پرسش شما مشکلی پیش آمده است.",
                "sources": []
            }
            
    def reset_chat_history(self):
        """پاک کردن تاریخچه چت"""
        self.chat_history = [] 