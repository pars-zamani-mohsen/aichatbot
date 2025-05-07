# chatbot_rag_gemini.py

import chromadb
import json
import os
import requests
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from google.generativeai.types import content_types
import argparse
from text_processor import TextProcessor
from hybrid_searcher import HybridSearcher

class RAGChatbot:
    def __init__(self, db_directory="knowledge_base", collection_name="website_data",
                 api_key=None, model_name="gemini-pro"):
        """مقداردهی اولیه چت‌بات RAG با Gemini"""

        # تنظیم کلید API
        if api_key:
            self.api_key = api_key
        elif 'GOOGLE_API_KEY' in os.environ:
            self.api_key = os.environ['GOOGLE_API_KEY']
        else:
            raise ValueError("کلید API Google مشخص نشده است.")

        # پیکربندی Gemini
        genai.configure(api_key=self.api_key)

        # انتخاب مدل
        self.model = genai.GenerativeModel(model_name)
        self.chat = self.model.start_chat(history=[])

        # تنظیمات پایگاه دانش (مشابه قبل)
        db_info_file = os.path.join(db_directory, 'db_info.json')
        if os.path.exists(db_info_file):
            with open(db_info_file, 'r', encoding='utf-8') as f:
                self.db_info = json.load(f)
        else:
            self.db_info = {'model': 'all-MiniLM-L6-v2'}

        self.embedding_model = SentenceTransformer(self.db_info.get('model', 'all-MiniLM-L6-v2'))
        self.db_client = chromadb.PersistentClient(path=db_directory)
        self.collection = self.db_client.get_collection(name=collection_name)

        self.system_prompt = """شما یک دستیار هوشمند هستید که به سوالات کاربران پاسخ می‌دهید.
برای پاسخ به سوالات کاربر، از اطلاعات زیر استفاده کنید. اگر اطلاعات کافی در منابع نیست، این را صادقانه به کاربر بگویید.
پاسخ‌های خود را به زبان فارسی ارائه دهید و به صورت طبیعی و محاوره‌ای صحبت کنید."""
        self.text_processor = TextProcessor()
        self.searcher = HybridSearcher(self.collection)

    def search_knowledge_base(self, query, n_results=5):
        """جستجو با موتور جستجوی هیبرید"""
        return self.searcher.search(query, n_results)

    def get_relevant_context(self, query, n_results=3):
        """استخراج متن مرتبط"""
        results = self.search_knowledge_base(query, n_results)
        if not results["documents"][0]:
            return "اطلاعاتی یافت نشد."

        context = ""
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            title = meta.get('title', 'بدون عنوان')
            url = meta.get('url', 'بدون URL')
            context += f"\n=== منبع {i+1}: {title} ===\nURL: {url}\n{doc}\n"
        return context

    def answer_question(self, query, chat_history=None, n_results=5):
        """پاسخ به پرس‌وجو با Gemini"""
        try:
            relevant_context = self.get_relevant_context(query, n_results)
            prompt = f"{self.system_prompt}\n\nاطلاعات مرتبط:\n{relevant_context}\n\nسوال: {query}"

            # ارسال پرامپت به Gemini
            response = self.chat.send_message(prompt)
            answer = response.text

            return answer, relevant_context
        except Exception as e:
            raise Exception(f"خطا در دریافت پاسخ از Gemini: {str(e)}")