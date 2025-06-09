from openai import OpenAI
import chromadb
from sentence_transformers import SentenceTransformer
import logging
from ..config import settings
from pathlib import Path

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, collection_name: str):
        # تنظیمات OpenAI
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # تنظیمات ChromaDB
        db_path = Path(settings.KNOWLEDGE_BASE_DIR) / collection_name
        logger.info(f"استفاده از مسیر دیتابیس: {db_path}")
        self.chroma_client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self.chroma_client.get_collection(name=collection_name)
        
        # تنظیمات مدل امبدینگ
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # دستورالعمل‌های پایه برای مدل
        self.system_prompt = """شما یک دستیار هوشمند هستید که به سوالات کاربران پاسخ می‌دهید.
برای پاسخ به سوالات کاربر، از اطلاعات زیر استفاده کنید. اگر اطلاعات کافی در منابع نیست، این را صادقانه به کاربر بگویید.
پاسخ‌های خود را به زبان فارسی ارائه دهید و به صورت طبیعی و محاوره‌ای صحبت کنید.
"""
        self.system_prompt += "\nهنگام پاسخ، اگر اطلاعاتی از یک منبع خاص استفاده می‌شود، شماره منبع را به صورت [n] در متن پاسخ ذکر کن."

    def search_knowledge_base(self, query: str, n_results: int = 5) -> dict:
        """جستجو در پایگاه دانش"""
        try:
            # ایجاد امبدینگ برای پرس‌وجو
            query_embedding = self.embedding_model.encode(query)
            
            # جستجو در پایگاه دانش
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"خطا در جستجوی پایگاه دانش: {str(e)}")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

    def get_relevant_context(self, query: str, n_results: int = 3) -> str:
        """دریافت متن‌های مرتبط"""
        results = self.search_knowledge_base(query, n_results)
        
        if not results or not results["documents"] or not results["documents"][0]:
            return "اطلاعاتی یافت نشد."
        
        context = ""
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            title = meta.get('title', 'بدون عنوان')
            url = meta.get('url', 'بدون URL')
            context += f"\n=== منبع {i+1}: {title} ===\nURL: {url}\n{doc}\n"
        
        return context

    def get_answer(self, query: str) -> tuple:
        """دریافت پاسخ برای پرس‌وجو"""
        try:
            # دریافت متن‌های مرتبط
            relevant_context = self.get_relevant_context(query)
            
            if relevant_context == "اطلاعاتی یافت نشد.":
                return "متاسفم، اطلاعات مرتبطی برای سوال شما در پایگاه دانش پیدا نشد.", []
            
            # ایجاد پیام‌ها برای مدل
            messages = [
                {"role": "system", "content": self.system_prompt + f"\n\nاطلاعات مرتبط:\n{relevant_context}"},
                {"role": "user", "content": query}
            ]
            
            # دریافت پاسخ از مدل
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.5,
                max_tokens=2000
            )
            
            answer = response.choices[0].message.content
            
            # استخراج منابع
            sources = []
            seen_urls = set()
            for line in relevant_context.split("\n"):
                if line.startswith("URL:"):
                    url = line[4:].strip()
                    if url not in seen_urls:
                        seen_urls.add(url)
                        sources.append(url)
            
            return answer, sources
            
        except Exception as e:
            logger.error(f"خطا در دریافت پاسخ: {str(e)}")
            return "متاسفانه در دریافت پاسخ مشکلی پیش آمده است. لطفاً دوباره تلاش کنید.", [] 