import chromadb
import json
import os
import requests
from sentence_transformers import SentenceTransformer
import argparse

class RAGChatbot:
    def __init__(self, db_directory="knowledge_base", collection_name="website_data",
                 model_name="gemma3:latest"):
        """مقداردهی اولیه چت‌بات RAG با استفاده از مدل محلی Ollama"""

        # تنظیم مدل و API
        self.model_name = model_name
        self.base_url = "http://localhost:11434"

        # بررسی دسترسی به Ollama
        self.check_ollama_connection()

        # خواندن اطلاعات پایگاه دانش
        db_info_file = os.path.join(db_directory, 'db_info.json')
        try:
            with open(db_info_file, 'r', encoding='utf-8') as f:
                self.db_info = json.load(f)
            print("اطلاعات پایگاه دانش بارگذاری شد.")
        except FileNotFoundError:
            self.db_info = {'model': 'all-MiniLM-L6-v2'}
            print("هشدار: فایل اطلاعات پایگاه دانش یافت نشد. از مدل پیش‌فرض استفاده می‌شود.")

        # بارگذاری مدل امبدینگ و اتصال به پایگاه دانش
        self.setup_embedding_model()
        self.setup_database(db_directory, collection_name)

        # تنظیم پرامپت سیستم
        self.system_prompt = """شما یک دستیار هوشمند هستید که به سوالات کاربران پاسخ می‌دهید.
برای پاسخ به سوالات کاربر، از اطلاعات زیر استفاده کنید. اگر اطلاعات کافی در منابع نیست، این را صادقانه به کاربر بگویید.
پاسخ‌های خود را به زبان فارسی ارائه دهید و به صورت طبیعی و محاوره‌ای صحبت کنید."""

    def check_ollama_connection(self):
        """بررسی اتصال به Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise ConnectionError("خطا در اتصال به Ollama")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"خطا در اتصال به Ollama: {e}")

    def setup_embedding_model(self):
        """راه‌اندازی مدل امبدینگ"""
        self.embedding_model_name = self.db_info.get('model', 'all-MiniLM-L6-v2')
        print(f"بارگذاری مدل امبدینگ {self.embedding_model_name}...")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

    def setup_database(self, db_directory, collection_name):
        """راه‌اندازی پایگاه داده"""
        self.db_client = chromadb.PersistentClient(path=db_directory)
        try:
            self.collection = self.db_client.get_collection(name=collection_name)
            print(f"کالکشن {collection_name} با موفقیت بارگذاری شد.")
        except Exception as e:
            raise Exception(f"خطا در بارگذاری کالکشن: {e}")

    def get_relevant_context(self, query, n_results=5):
        """استخراج متن مرتبط با پرس‌وجو از پایگاه دانش"""
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        if not results["documents"] or not results["documents"][0]:
            return "اطلاعاتی یافت نشد."

        context = ""
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            title = meta.get('title', 'بدون عنوان')
            url = meta.get('url', 'بدون URL')
            context += f"\n=== منبع {i+1}: {title} ===\nURL: {url}\n{doc}\n"

        return context

    def answer_question(self, query, chat_history=None, n_results=5):
        """پاسخ به پرس‌وجوی کاربر با استفاده از RAG"""
        relevant_context = self.get_relevant_context(query, n_results)
        prompt = self._build_prompt(query, relevant_context, chat_history)

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                headers={'Content-Type': 'application/json'},
                timeout=60
            )

            if response.status_code == 200:
                answer = response.json().get("response", "").strip()
                return answer, relevant_context
            else:
                raise Exception(f"خطا از سمت Ollama: {response.text}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"خطا در ارتباط با Ollama: {e}")

    def _build_prompt(self, query, context, chat_history=None):
        """ساخت پرامپت کامل"""
        prompt = self.system_prompt + f"\n\nاطلاعات مرتبط:\n{context}\n\n"

        if chat_history:
            for msg in chat_history:
                role = msg["role"]
                content = msg["content"]
                prompt += f"{'User' if role == 'user' else 'Assistant'}: {content}\n"

        prompt += f"User: {query}\nAssistant:"
        return prompt

    def chat_loop(self, n_results=5):
        """حلقه اصلی تعامل با کاربر"""
        print(f"\n=== چت‌بات RAG (با استفاده از مدل {self.model_name}) ===")
        print("برای خروج، عبارت 'exit' یا 'quit' را وارد کنید.\n")

        chat_history = []
        while True:
            query = input("\nشما: ").strip()
            if query.lower() in ['exit', 'quit', 'خروج']:
                print("\nخداحافظ!")
                break

            try:
                answer, _ = self.answer_question(query, chat_history, n_results)
                print(f"\nچت‌بات: {answer}")

                chat_history.append({"role": "user", "content": query})
                chat_history.append({"role": "assistant", "content": answer})

                if len(chat_history) > 6:
                    chat_history = chat_history[-6:]
            except Exception as e:
                print(f"\nخطا در پاسخگویی: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='چت‌بات RAG با مدل محلی')
    parser.add_argument('--db_dir', default='knowledge_base', help='مسیر پایگاه دانش')
    parser.add_argument('--collection', default='website_data', help='نام کالکشن')
    parser.add_argument('--model', default='gemma3:latest', help='نام مدل Ollama')

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