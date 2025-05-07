from typing import Dict, List
from chromadb.api import Collection
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
import re

class HybridSearcher:
    def __init__(self, collection: Collection):
        self.collection = collection
        self.documents = []
        self.bm25 = None
        # مدل قوی‌تر برای رتبه‌بندی مجدد
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self._initialize()

    def _initialize(self):
        """آماده‌سازی موتور جستجو"""
        try:
            results = self.collection.peek()
            if not results or not results['documents']:
                return

            # تهیه لیست اسناد
            docs = results['documents']
            if isinstance(docs[0], list):
                self.documents = [str(doc) for doc in docs[0]]
            else:
                self.documents = [str(doc) for doc in docs]

            # حذف اسناد خالی یا کوتاه
            self.documents = [doc for doc in self.documents if len(doc.strip()) > 50]

            # آماده‌سازی BM25 با توکن‌های بهتر
            if self.documents:
                tokenized_docs = [self._tokenize_text(doc) for doc in self.documents]
                self.bm25 = BM25Okapi(tokenized_docs)
                print(f"تعداد اسناد بارگذاری شده: {len(self.documents)}")

        except Exception as e:
            print(f"خطا در آماده‌سازی: {str(e)}")
            self.documents = []
            self.bm25 = None

    def _tokenize_text(self, text: str) -> List[str]:
        """تقسیم متن به توکن‌ها با حفظ کلمات فارسی"""
        # حذف کاراکترهای خاص
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', str(text))
        # تبدیل به حروف کوچک برای متون انگلیسی
        text = text.lower()
        # حذف فاصله‌های اضافی
        text = re.sub(r'\s+', ' ', text).strip()
        return text.split()

    def _tokenize_text(self, text: str) -> List[str]:
        """تقسیم متن به توکن‌ها با حفظ کلمات فارسی و انگلیسی"""
        # حذف کاراکترهای خاص
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', str(text))
        # تبدیل به حروف کوچک برای متون انگلیسی
        text = text.lower()
        # حذف فاصله‌های اضافی
        text = re.sub(r'\s+', ' ', text).strip()
        return text.split()

    def search(self, query: str, n_results: int = 5) -> Dict:
        """جستجوی ترکیبی بهبود یافته"""
        if not self.documents:
            return {'documents': [], 'metadatas': [], 'distances': [[]]}

        try:
            # جستجوی معنایی با تعداد نتایج بیشتر
            semantic_results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, len(self.documents))
            )

            # جستجوی BM25 با وزن‌دهی
            bm25_scores = self.bm25.get_scores(self._tokenize_text(query))
            bm25_scores_normalized = bm25_scores / (np.max(bm25_scores) + 1e-6)
            bm25_indices = np.argsort(bm25_scores)[-n_results*2:][::-1]

            # ترکیب نتایج با وزن‌دهی
            combined_docs = []
            combined_meta = []
            doc_pairs = []
            seen_docs = set()

            # اضافه کردن نتایج معنایی با وزن 0.7
            semantic_weight = 0.7
            for doc, meta in zip(semantic_results['documents'][0], semantic_results['metadatas'][0]):
                doc_hash = hash(doc)
                if doc_hash not in seen_docs:
                    seen_docs.add(doc_hash)
                    combined_docs.append(doc)
                    combined_meta.append(meta)
                    doc_pairs.append((doc, query))

            # اضافه کردن نتایج BM25 با وزن 0.3
            bm25_weight = 0.3
            for idx in bm25_indices:
                doc = self.documents[idx]
                doc_hash = hash(doc)
                if doc_hash not in seen_docs:
                    seen_docs.add(doc_hash)
                    combined_docs.append(doc)
                    combined_meta.append({'url': '', 'chunk_id': f'bm25_{idx}'})
                    doc_pairs.append((doc, query))

            # رتبه‌بندی نهایی با Cross-Encoder
            if doc_pairs:
                scores = self.reranker.predict(doc_pairs, batch_size=32, show_progress_bar=False)

                # نرمال‌سازی امتیازها
                scores = (scores - np.min(scores)) / (np.max(scores) - np.min(scores) + 1e-6)

                # انتخاب بهترین نتایج
                sorted_indices = np.argsort(scores)[-n_results:][::-1]

                return {
                    'documents': [[combined_docs[i] for i in sorted_indices]],
                    'metadatas': [[combined_meta[i] for i in sorted_indices]],
                    'distances': [[float(scores[i]) for i in sorted_indices]]
                }

            return semantic_results

        except Exception as e:
            print(f"خطا در جستجو: {str(e)}")
            return {'documents': [], 'metadatas': [], 'distances': [[]]}