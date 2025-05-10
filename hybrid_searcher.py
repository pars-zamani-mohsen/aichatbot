from typing import Dict, List, Optional, Tuple
from sentence_transformers import CrossEncoder
from chromadb.api import Collection
from rank_bm25 import BM25Okapi
from langdetect import detect
import numpy as np
import logging
import time
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HybridSearcher:
    def __init__(self, collection: Collection):
        self.collection = collection
        self.documents = []
        self.bm25 = None
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        # اضافه کردن کش
        self.cache = {}
        self.cache_ttl = 3600  # یک ساعت
        self.max_cache_size = 1000
        self._initialize()

    def _get_from_cache(self, query: str, n_results: int) -> Optional[Dict]:
        """بازیابی نتیجه از کش"""
        cache_key = f"{query}_{n_results}"
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return result
            # حذف نتیجه منقضی شده
            del self.cache[cache_key]
        return None

    def _add_to_cache(self, query: str, n_results: int, result: Dict):
        """افزودن نتیجه به کش"""
        cache_key = f"{query}_{n_results}"
        self.cache[cache_key] = (result, time.time())

        # حذف قدیمی‌ترین نتایج اگر کش پر شده
        if len(self.cache) > self.max_cache_size:
            oldest_key = min(self.cache.keys(),
                           key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

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

    def _normalize_text(self, text: str) -> str:
        """نرمال‌سازی متن با پشتیبانی از فارسی و انگلیسی"""
        try:
            text = str(text).strip()

            # تشخیص زبان
            lang = detect(text)

            # حذف کاراکترهای خاص با حفظ حروف فارسی و انگلیسی
            text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)

            if lang == 'fa':
                # نرمال‌سازی کاراکترهای فارسی
                replacements = {
                    'ي': 'ی',
                    'ك': 'ک',
                    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
                    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
                    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
                    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
                }
                for old, new in replacements.items():
                    text = text.replace(old, new)
            else:
                # نرمال‌سازی متن انگلیسی
                text = text.lower()

            # حذف فاصله‌های اضافی
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        except Exception as e:
            logger.warning(f"خطا در نرمال‌سازی متن: {str(e)}")
            return text.lower().strip()

    def _tokenize_text(self, text: str) -> List[str]:
        """تقسیم متن به توکن‌ها با استفاده از نرمال‌سازی بهبود یافته"""
        normalized_text = self._normalize_text(text)
        return normalized_text.split()

    def search(self, query: str, n_results: int = 5) -> Dict:
        """جستجوی ترکیبی با قابلیت کش"""
        if not self.documents:
            return {'documents': [], 'metadatas': [], 'distances': [[]]}

        try:
            # بررسی کش
            cached_result = self._get_from_cache(query, n_results)
            if cached_result:
                return cached_result

            # اجرای جستجو
            result = self._perform_search(query, n_results)

            # ذخیره در کش
            self._add_to_cache(query, n_results, result)

            return result

        except Exception as e:
            print(f"خطا در جستجو: {str(e)}")
            return {'documents': [], 'metadatas': [], 'distances': [[]]}

    def _perform_search(self, query: str, n_results: int) -> Dict:
        """انجام عملیات جستجو با وزن‌دهی پویا"""
        try:
            # جستجوی معنایی
            semantic_results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, len(self.documents))
            )

            # جستجوی BM25
            bm25_scores = self.bm25.get_scores(self._tokenize_text(query))

            # اگر هیچ نتیجه‌ای نداریم
            if len(bm25_scores) == 0:
                return {
                    'documents': [[]],
                    'metadatas': [[]],
                    'distances': [[]]
                }

            # نرمال‌سازی و مرتب‌سازی نتایج BM25
            bm25_scores_normalized = bm25_scores / (np.max(bm25_scores) + 1e-6)
            bm25_indices = np.argsort(bm25_scores)[-n_results:][::-1]

            # ترکیب نتایج
            combined_docs = []
            combined_meta = []
            seen_docs = set()

            # افزودن نتایج معنایی
            if semantic_results.get('documents') and semantic_results['documents'][0]:
                for i, doc in enumerate(semantic_results['documents'][0]):
                    doc_hash = hash(str(doc))
                    if doc_hash not in seen_docs and i < len(semantic_results['metadatas'][0]):
                        seen_docs.add(doc_hash)
                        combined_docs.append(str(doc))
                        combined_meta.append(semantic_results['metadatas'][0][i])

            # افزودن نتایج BM25
            for idx in bm25_indices:
                if idx < len(self.documents):
                    doc = str(self.documents[idx])
                    doc_hash = hash(doc)
                    if doc_hash not in seen_docs:
                        seen_docs.add(doc_hash)
                        combined_docs.append(doc)
                        combined_meta.append({'url': '', 'chunk_id': f'bm25_{idx}'})

            # اگر هیچ نتیجه‌ای نداریم
            if not combined_docs:
                return {
                    'documents': [[]],
                    'metadatas': [[]],
                    'distances': [[]]
                }

            # رتبه‌بندی نهایی با استفاده از متد جدید
            doc_pairs = [(doc, query) for doc in combined_docs]
            cross_scores = self._rerank_results(doc_pairs)

            # محدود کردن تعداد نتایج
            top_k = min(n_results, len(combined_docs))
            sorted_indices = np.argsort(cross_scores)[-top_k:][::-1]

            return {
                'documents': [[combined_docs[i] for i in sorted_indices]],
                'metadatas': [[combined_meta[i] for i in sorted_indices]],
                'distances': [[float(cross_scores[i]) for i in sorted_indices]]
            }

        except Exception as e:
            logger.error(f"خطا در جستجوی ترکیبی: {str(e)}")
            return {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }

    def _dynamic_weighting(self, query: str, semantic_results: Dict, bm25_scores: np.ndarray) -> Tuple[float, float]:
        """تعیین وزن‌های پویا برای نتایج جستجوی معنایی و BM25"""
        try:
            # محاسبه کیفیت نتایج معنایی با بررسی وجود distances
            semantic_quality = 0.0
            if (semantic_results.get('distances') and
                len(semantic_results['distances']) > 0 and
                len(semantic_results['distances'][0]) > 0):
                semantic_quality = np.mean(semantic_results['distances'][0])

            # محاسبه کیفیت نتایج BM25
            bm25_quality = np.mean(bm25_scores) if len(bm25_scores) > 0 else 0.0

            # تنظیم وزن‌ها بر اساس کیفیت نتایج
            total_quality = semantic_quality + bm25_quality
            if total_quality < 1e-6:  # از صفر مطلق اجتناب کنیم
                return 0.7, 0.3  # وزن‌های پیش‌فرض

            semantic_weight = semantic_quality / total_quality
            bm25_weight = bm25_quality / total_quality

            # محدود کردن وزن‌ها در بازه معقول
            semantic_weight = max(0.3, min(0.8, semantic_weight))
            bm25_weight = 1 - semantic_weight

            logger.info(f"Dynamic weights - Semantic: {semantic_weight:.2f}, BM25: {bm25_weight:.2f}")
            return semantic_weight, bm25_weight

        except Exception as e:
            logger.warning(f"خطا در محاسبه وزن‌های پویا: {str(e)}")
            return 0.7, 0.3

    def _rerank_results(self, doc_pairs: List[Tuple[str, str]], batch_size: int = 32) -> np.ndarray:
        """بازمرتب‌سازی نتایج با مدیریت بهتر حافظه و پردازش دسته‌ای"""
        try:
            # تقسیم‌بندی به دسته‌های کوچکتر برای مدیریت حافظه
            n_pairs = len(doc_pairs)
            scores = np.zeros(n_pairs)

            for i in range(0, n_pairs, batch_size):
                batch = doc_pairs[i:min(i + batch_size, n_pairs)]
                batch_scores = self.reranker.predict(batch)
                scores[i:i + len(batch)] = batch_scores

            return scores

        except Exception as e:
            logger.error(f"خطا در بازمرتب‌سازی نتایج: {str(e)}")
            return np.zeros(n_pairs)