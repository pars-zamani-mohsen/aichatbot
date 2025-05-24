import google.generativeai as genai
from typing import List, Dict, Optional
import logging
from pathlib import Path
from ..services.hybrid_searcher import HybridSearcher
from ..services.prompt_manager import PromptManager
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGChatbot:
    def __init__(
        self,
        db_directory: str,
        collection_name: str,
        google_api_key: str = None,
        model_name: str = None,
        max_tokens: int = None,
        temperature: float = None
    ):
        self.db_directory = Path(db_directory)
        self.collection_name = collection_name
        self.model_name = model_name or settings.GEMINI_MODEL_NAME
        self.max_tokens = max_tokens or int(settings.MAX_TOKENS)
        self.temperature = temperature or float(settings.TEMPERATURE)
        
        # تنظیم API key
        genai.configure(api_key=google_api_key or settings.GOOGLE_API_KEY)
        
        # ایجاد مدل
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "max_output_tokens": self.max_tokens,
                "temperature": self.temperature
            }
        )
        
        # ایجاد موتور جستجو
        self.searcher = HybridSearcher(
            collection_name=collection_name,
            db_directory=db_directory
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
            
    def _create_prompt(self, query: str, context: List[str]) -> str:
        """ایجاد پرامپت برای مدل"""
        # پرامپت سیستم
        system_prompt = self.prompt_manager.get_system_prompt()
        
        # پرامپت کاربر با کانتکست
        user_prompt = self.prompt_manager.generate_prompt(query, context)
        
        # ساخت پرامپت نهایی
        prompt = f"""
        {system_prompt}
        
        {user_prompt}
        """
        
        return prompt.strip()
        
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
            
            # ایجاد پرامپت
            prompt = self._create_prompt(question, context)
            
            # ارسال درخواست به API
            response = self.model.generate_content(prompt)
            
            # استخراج پاسخ
            answer = response.text
            
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