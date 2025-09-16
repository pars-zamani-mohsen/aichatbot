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
    def __init__(self, collection_name: str, rag_settings: dict = None):
        # تنظیمات OpenAI
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # تنظیمات ChromaDB
        db_path = Path(settings.KNOWLEDGE_BASE_DIR) / collection_name
        logger.info(f"استفاده از مسیر دیتابیس: {db_path}")
        self.chroma_client = chromadb.PersistentClient(path=str(db_path))
        
        # ایجاد یا دریافت collection
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
        except ValueError:
            # اگر collection وجود نداشت، آن را ایجاد کن
            logger.info(f"Creating new collection: {collection_name}")
            self.collection = self.chroma_client.create_collection(name=collection_name)
        
        # تنظیمات مدل امبدینگ
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        
        # تنظیمات RAG
        self.rag_settings = rag_settings or {}
        self.k = self.rag_settings.get("k", 5)
        self.max_response_length = self.rag_settings.get("max_response_length", 500)
        self.temperature = self.rag_settings.get("temperature", 0.7)
        self.tone = self.rag_settings.get("tone", "professional")
        self.language = self.rag_settings.get("language", "persian")
        self.include_sources = self.rag_settings.get("include_sources", True)
        self.max_context_length = self.rag_settings.get("max_context_length", 2000)
        
        # دستورالعمل‌های پایه برای مدل
        self.system_prompt = self._generate_system_prompt()
    
    def _generate_system_prompt(self) -> str:
        """تولید دستورالعمل سیستم بر اساس تنظیمات"""
        base_prompt = """شما یک دستیار هوشمند هستید که به سوالات کاربران پاسخ می‌دهید.
برای پاسخ به سوالات کاربر، از اطلاعات زیر استفاده کنید. اگر اطلاعات کافی در منابع نیست، این را صادقانه به کاربر بگویید.
"""
        
        # تنظیم زبان
        if self.language == "persian":
            base_prompt += "پاسخ‌های خود را به زبان فارسی ارائه دهید و به صورت طبیعی و محاوره‌ای صحبت کنید.\n"
        elif self.language == "english":
            base_prompt += "Provide your answers in English and speak naturally and conversationally.\n"
        
        # تنظیم تن صدا
        tone_instructions = {
            "professional": "پاسخ‌های خود را به صورت حرفه‌ای و رسمی ارائه دهید.\n",
            "friendly": "پاسخ‌های خود را به صورت دوستانه و گرم ارائه دهید.\n",
            "formal": "پاسخ‌های خود را به صورت رسمی و محترمانه ارائه دهید.\n",
            "casual": "پاسخ‌های خود را به صورت غیررسمی و صمیمی ارائه دهید.\n"
        }
        base_prompt += tone_instructions.get(self.tone, tone_instructions["professional"])
        
        # تنظیم طول پاسخ
        base_prompt += f"پاسخ‌های خود را حداکثر {self.max_response_length} کاراکتر نگه دارید.\n"
        
        # تنظیم منابع
        if self.include_sources:
            base_prompt += "هنگام پاسخ، اگر اطلاعاتی از یک منبع خاص استفاده می‌شود، شماره منبع را به صورت [n] در متن پاسخ ذکر کن.\n"
        
        return base_prompt

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

    def get_relevant_context(self, query: str, n_results: int = None) -> str:
        """دریافت متن‌های مرتبط"""
        if n_results is None:
            n_results = self.k
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
                temperature=self.temperature,
                max_tokens=min(self.max_response_length * 2, 4000)  # حداکثر 4000 توکن
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
    
    def add_document(self, text: str, metadata: dict = None):
        """اضافه کردن سند جدید به collection"""
        try:
            # تولید امبدینگ
            embedding = self.embedding_model.encode(text).tolist()
            
            # اضافه کردن به collection
            self.collection.add(
                documents=[text],
                embeddings=[embedding],
                metadatas=[metadata or {}],
                ids=[str(len(self.collection.get()['ids']))]
            )
            
            logger.info(f"سند جدید با موفقیت اضافه شد")
            return True
            
        except Exception as e:
            logger.error(f"خطا در اضافه کردن سند: {str(e)}")
            return False
    
    def update_document(self, document_id: str, text: str, metadata: dict = None):
        """به‌روزرسانی سند موجود"""
        try:
            # تولید امبدینگ جدید
            embedding = self.embedding_model.encode(text).tolist()
            
            # به‌روزرسانی سند
            self.collection.update(
                ids=[document_id],
                documents=[text],
                embeddings=[embedding],
                metadatas=[metadata or {}]
            )
            
            logger.info(f"سند {document_id} با موفقیت به‌روزرسانی شد")
            return True
            
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی سند: {str(e)}")
            return False
    
    def delete_document(self, document_id: str):
        """حذف سند از collection"""
        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"سند {document_id} با موفقیت حذف شد")
            return True
            
        except Exception as e:
            logger.error(f"خطا در حذف سند: {str(e)}")
            return False 