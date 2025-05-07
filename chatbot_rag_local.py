import chromadb
import json
import os
import requests
from sentence_transformers import SentenceTransformer
import argparse
from text_processor import TextProcessor
from hybrid_searcher import HybridSearcher
from prompt_manager import PromptManager

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class RAGChatbot:
    def __init__(self, db_directory="knowledge_base", collection_name="website_data",
                 model_name="llama3.2:latest"):
        """مقداردهی اولیه چت‌بات RAG با استفاده از مدل محلی Ollama"""

        # تنظیم مدل
        self.model_name = model_name

        # Set the correct API endpoint based on model
        self.ollama_api = "http://localhost:11434/api/generate"

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
        self.text_processor = TextProcessor()
        self.searcher = HybridSearcher(self.collection)
        self.prompt_manager = PromptManager()

    def search_knowledge_base(self, query, n_results=5):
        """جستجو با موتور جستجوی هیبرید"""
        return self.searcher.search(query, n_results)

    def get_relevant_context(self, query, n_results=3):
        """استخراج متن مرتبط با پرس‌وجو از پایگاه دانش"""

        results = self.search_knowledge_base(query, n_results)

        if not results or not results["documents"] or not results["documents"][0]:
            return "اطلاعاتی یافت نشد."

        context = ""
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            title = meta.get('title', 'بدون عنوان')
            url = meta.get('url', 'بدون URL')
            context += f"\n=== منبع {i+1}: {title} ===\nURL: {url}\n{doc}\n"

        return context

    def answer_question(self, query, chat_history=None, n_results=5):
        """پاسخ به پرس‌وجوی کاربر با استفاده از RAG"""

        # استخراج اطلاعات مرتبط از پایگاه دانش
        relevant_context = self.get_relevant_context(query, n_results)

        # استفاده از PromptManager برای ساخت پرامپت
        query_type = self.prompt_manager.detect_query_type(query)
        prompt = self.prompt_manager.get_prompt(query, relevant_context, query_type)

        # ساخت پرامپت کامل
        system_message = self.system_prompt + f"\n\nاطلاعات مرتبط:\n{relevant_context}"

        # آماده‌سازی پیام با تاریخچه چت
        full_prompt = system_message + "\n\n"

        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    full_prompt += f"User: {msg['content']}\n"
                else:
                    full_prompt += f"Assistant: {msg['content']}\n"

        full_prompt += f"User: {query}\nAssistant:"

        # ارسال پرامپت به Ollama
        response = requests.post(
            self.ollama_api,
            json={
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            answer = response.json().get("response", "").strip()
            return answer, relevant_context
        else:
            raise Exception(f"خطا در درخواست Ollama: {response.text}")

    def chat_loop(self, n_results=5):
        """حلقه اصلی تعامل با کاربر"""

        print(f"\n=== چت‌بات RAG (با استفاده از مدل محلی {self.model_name}) ===")
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
            try:
                answer, relevant_context = self.answer_question(query, chat_history, n_results)

                # چاپ پاسخ
                print(f"\nچت‌بات: {answer}")

                # افزودن به تاریخچه چت
                chat_history.append({"role": "user", "content": query})
                chat_history.append({"role": "assistant", "content": answer})

                # محدود کردن طول تاریخچه چت
                if len(chat_history) > 6:  # حفظ 3 پرسش و پاسخ آخر
                    chat_history = chat_history[-6:]
            except Exception as e:
                print(f"\nخطا در پاسخگویی: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='چت‌بات RAG با مدل محلی')
    parser.add_argument('--db_dir', default='knowledge_base', help='مسیر پایگاه دانش')
    parser.add_argument('--collection', default='website_data', help='نام کالکشن')
    parser.add_argument('--model', default='llama3.2:latest', help='نام مدل Ollama')

    args = parser.parse_args()

    try:
        chatbot = RAGChatbot(
            db_directory=args.db_dir,
            collection_name=args.collection,
            model_name=args.model
        )
        chatbot.chat_loop()
    except Exception as e:
        print(f"خطا در اجرای چت‌بات: {e}")