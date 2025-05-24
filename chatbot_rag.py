import chromadb
import json
import os
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from text_processor import TextProcessor
from hybrid_searcher import HybridSearcher
from prompt_manager import PromptManager
from settings import MAX_CHAT_HISTORY
import argparse
import re

try:
    from dotenv import load_dotenv
    load_dotenv()  # متغیرهای محیطی را از فایل .env بارگذاری می‌کند
except ImportError:
    pass  # اگر کتابخانه نصب نشده باشد، نادیده گرفته می‌شود

PERSIAN_STOPWORDS = set([
    "و", "در", "به", "از", "که", "را", "با", "برای", "این", "آن", "یک", "تا", "می", "بر", "است", "بود", "شود", "کرد", "های", "هم", "اما", "یا", "اگر", "نیز", "بین", "هر", "روی", "پس", "چه", "همه", "چون", "چرا", "کجا", "کی", "چگونه"
])

class RAGChatbot:
    def __init__(self, db_directory="knowledge_base/{domain}", collection_name="website_data",
                 api_key=None, model_name="gpt-3.5-turbo"):
        """مقداردهی اولیه چت‌بات RAG"""

        # تنظیم کلید API و مدل
        if api_key:
            self.api_key = api_key
        elif 'OPENAI_API_KEY' in os.environ:
            self.api_key = os.environ['OPENAI_API_KEY']
        else:
            raise ValueError("کلید API OpenAI مشخص نشده است. لطفاً آن را در متغیر محیطی OPENAI_API_KEY تنظیم کنید یا به عنوان پارامتر ارسال کنید.")

        # ایجاد کلاینت OpenAI با API جدید
        self.client = OpenAI(api_key=self.api_key)
        self.model_name = model_name

        # خواندن اطلاعات پایگاه دانش
        db_info_file = os.path.join(db_directory, 'db_info.json')
        if os.path.exists(db_info_file):
            with open(db_info_file, 'r', encoding='utf-8') as f:
                self.db_info = json.load(f)
            print(f"اطلاعات پایگاه دانش بارگذاری شد.")
        else:
            self.db_info = {'model': 'all-MiniLM-L6-v2'}
            print("هشدار: فایل اطلاعات پایگاه دانش یافت نشد. از مدل پیش‌فرض استفاده می‌شود.")

        # بارگذاری مدل امبدینگ
        self.embedding_model_name = self.db_info.get('model', 'all-MiniLM-L6-v2')
        print(f"بارگذاری مدل امبدینگ {self.embedding_model_name}...")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        # اتصال به پایگاه دانش
        self.db_client = chromadb.PersistentClient(path=db_directory)

        # بررسی وجود کالکشن
        try:
            self.collection = self.db_client.get_collection(name=collection_name)
            print(f"کالکشن {collection_name} با موفقیت بارگذاری شد.")
        except Exception as e:
            print(f"خطا در بارگذاری کالکشن: {e}")
            raise

        # دستورالعمل‌های پایه برای مدل
        self.system_prompt = """شما یک دستیار هوشمند هستید که به سوالات کاربران پاسخ می‌دهید.
برای پاسخ به سوالات کاربر، از اطلاعات زیر استفاده کنید. اگر اطلاعات کافی در منابع نیست، این را صادقانه به کاربر بگویید.
پاسخ‌های خود را به زبان فارسی ارائه دهید و به صورت طبیعی و محاوره‌ای صحبت کنید.
"""
        self.system_prompt += "\nهنگام پاسخ، اگر اطلاعاتی از یک منبع خاص استفاده می‌شود، شماره منبع را به صورت [n] در متن پاسخ ذکر کن."
        self.text_processor = TextProcessor()
        self.searcher = HybridSearcher(self.collection)
        self.prompt_manager = PromptManager()

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

    def get_relevant_context(self, query, n_results=3, query_type='general'):
        results = self.search_knowledge_base(query, n_results, query_type)

        if not results or not results["documents"] or not results["documents"][0]:
            return "اطلاعاتی یافت نشد."

        context = ""
        query_words = set(query.strip().split())
        min_overlap = 3  # stricter
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            if RAGChatbot.is_garbage_context(doc):
                continue
            doc_words = set(doc.strip().split())
            overlap = len(query_words & doc_words)
            if len(doc.strip()) < 50 or overlap < min_overlap:
                continue
            if not RAGChatbot.has_phrase_match(query, doc, n=2):
                continue
            title = meta.get('title', 'بدون عنوان')
            url = meta.get('url', 'بدون URL')
            context += f"\n=== منبع {i+1}: {title} ===\nURL: {url}\n{doc}\n"

        if not context:
            return "اطلاعاتی یافت نشد."
        return context

    def answer_question(self, query, chat_history=None, n_results=5):
        query_type = self.prompt_manager.detect_query_type(query)
        relevant_context = self.get_relevant_context(query, n_results, query_type)

        if relevant_context == "اطلاعاتی یافت نشد.":
            return "متاسفم، اطلاعات مرتبطی برای سوال شما در پایگاه دانش پیدا نشد.", relevant_context

        prompt = self.prompt_manager.get_prompt(query, relevant_context, query_type)
        messages = [{"role": "system", "content": self.system_prompt + f"\n\nاطلاعات مرتبط:\n{relevant_context}"}]
        if chat_history:
            messages.extend(chat_history[-MAX_CHAT_HISTORY:])
        messages.append({"role": "user", "content": query})

        response = self.client.chat.completions.create(
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
            answer += "\n\nمنابع:\n"
            for idx, src in enumerate(sources, 1):
                answer += f"{idx}. [منبع {idx}]({src})\n"

        return answer, relevant_context

    def chat_loop(self, n_results=5):
        """حلقه اصلی تعامل با کاربر"""

        print("\n=== چت‌بات RAG ===")
        print("برای خروج، عبارت 'exit' یا 'quit' را وارد کنید.\n")

        chat_history = []

        while True:
            # دریافت پرس‌وجو از کاربر
            query = input("\nشما: ")

            # بررسی خروج
            if query.lower() in ['exit', 'quit', 'خروج']:
                print("\nخداحافظ!")
                break

            # پاسخ به پرس‌وجو
            answer, relevant_context = self.answer_question(query, chat_history, n_results)

            # چاپ پاسخ
            print(f"\nچت‌بات: {answer}")

            # افزودن به تاریخچه چت
            chat_history.append({"role": "user", "content": query})
            chat_history.append({"role": "assistant", "content": answer})

            # محدود کردن طول تاریخچه چت
            if len(chat_history) > MAX_CHAT_HISTORY:
                chat_history = chat_history[-MAX_CHAT_HISTORY:]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='چت‌بات RAG')
    parser.add_argument('--db_dir', default='knowledge_base', help='مسیر پایگاه دانش')
    parser.add_argument('--collection', default='website_data', help='نام کالکشن')
    parser.add_argument('--api_key', help='کلید API OpenAI')
    parser.add_argument('--model', default='gpt-3.5-turbo', help='نام مدل OpenAI')

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
        print(f"خطا در اجرای چت‌بات: {e}")