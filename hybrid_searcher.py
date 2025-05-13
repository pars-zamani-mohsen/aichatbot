from typing import Dict, List, Optional, Tuple
from sentence_transformers import CrossEncoder
from chromadb.api import Collection
from rank_bm25 import BM25Okapi
from langdetect import detect
import numpy as np
import logging
import time
import re
from settings import (
    MAX_TOKENS,
    TOKENS_PER_MIN,
    CHUNK_SIZE,
    EMBEDDING_MODEL_NAME
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HybridSearcher:
    def __init__(
        self,
        collection: Collection,
        chunk_size: int = int(CHUNK_SIZE),
        max_tokens: int = int(MAX_TOKENS),
        tokens_per_min: int = int(TOKENS_PER_MIN),
        embedding_model: str = EMBEDDING_MODEL_NAME
    ):
        self.collection = collection
        self.documents = []
        self.bm25 = None
        self.chunk_size = chunk_size
        self.max_tokens = max_tokens
        self.tokens_per_min = tokens_per_min
        self.embedding_model = embedding_model

        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

        # تنظیمات کش
        self.cache = {}
        self.cache_ttl = 3600  # یک ساعت
        self.max_cache_size = 1000

        self._initialize()

    def _initialize(self):
        """آماده‌سازی موتور جستجو"""
        try:
            results = self.collection.peek()
            if not results or not results['documents']:
                return

            docs = results['documents']
            if isinstance(docs[0], list):
                self.documents = [str(doc) for doc in docs[0]]
            else:
                self.documents = [str(doc) for doc in docs]

            self.documents = [doc for doc in self.documents if len(doc.strip()) > 50]

            if self.documents:
                tokenized_docs = [self._tokenize_text(doc) for doc in self.documents]
                self.bm25 = BM25Okapi(tokenized_docs)
                logger.info(f"تعداد اسناد بارگذاری شده: {len(self.documents)}")

        except Exception as e:
            logger.error(f"خطا در آماده‌سازی: {str(e)}")
            self.documents = []
            self.bm25 = None

    def _normalize_text(self, text: str) -> str:
        """نرمال‌سازی متن با پشتیبانی از فارسی و انگلیسی"""
        try:
            text = str(text).strip()
            lang = detect(text)

            text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)

            if lang == 'fa':
                replacements = {
                    'ي': 'ی', 'ك': 'ک',
                    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
                    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
                    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
                    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
                }
                for old, new in replacements.items():
                    text = text.replace(old, new)
            else:
                text = text.lower()

            return re.sub(r'\s+', ' ', text).strip()

        except Exception as e:
            logger.warning(f"خطا در نرمال‌سازی متن: {str(e)}")
            return text.lower().strip()

    def _tokenize_text(self, text: str) -> List[str]:
        """تقسیم متن به توکن‌ها با پشتیبانی فارسی و انگلیسی"""
        try:
            normalized = self._normalize_text(text)
            tokens = []
            words = re.findall(r'[\u0600-\u06FF]+|[a-zA-Z]+|\d+', normalized)

            for word in words:
                if len(word) > 1:
                    tokens.append(word)
                    if re.search(r'[\u0600-\u06FF]', word) and len(word) > 3:
                        for i in range(len(word)-2):
                            tokens.append(word[i:i+3])

            return tokens

        except Exception as e:
            logger.warning(f"خطا در توکن‌سازی: {str(e)}")
            return normalized.split()

    def search(self, query: str, n_results: int = 5) -> Dict:
        """جستجوی ترکیبی با قابلیت کش"""
        if not self.documents:
            return {'documents': [], 'metadatas': [], 'distances': [[]]}

        try:
            cache_key = f"{query}_{n_results}"
            cached = self._get_from_cache(query, n_results)
            if cached:
                return cached

            result = self._perform_search(query, n_results)
            self._add_to_cache(query, n_results, result)
            return result

        except Exception as e:
            logger.error(f"خطا در جستجو: {str(e)}")
            return {'documents': [], 'metadatas': [], 'distances': [[]]}

    def _perform_search(self, query: str, n_results: int) -> Dict:
        """انجام جستجوی ترکیبی"""
        try:
            semantic_results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, len(self.documents))
            )

            bm25_scores = self.bm25.get_scores(self._tokenize_text(query))
            if len(bm25_scores) == 0:
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            sem_w, bm25_w = self._dynamic_weighting(query, semantic_results, bm25_scores)
            combined_docs, combined_meta = self._combine_results(
                semantic_results, bm25_scores, sem_w, bm25_w
            )

            if not combined_docs:
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            final_scores = self._rerank_results(
                [(doc, query) for doc in combined_docs]
            )

            top_k = min(n_results, len(combined_docs))
            indices = np.argsort(final_scores)[-top_k:][::-1]

            return {
                'documents': [[combined_docs[i] for i in indices]],
                'metadatas': [[combined_meta[i] for i in indices]],
                'distances': [[float(final_scores[i]) for i in indices]]
            }

        except Exception as e:
            logger.error(f"خطا در جستجوی ترکیبی: {str(e)}")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

    def _combine_results(self,
                        semantic_results: Dict,
                        bm25_scores: np.ndarray,
                        sem_weight: float,
                        bm25_weight: float) -> Tuple[List[str], List[Dict]]:
        """ترکیب نتایج معنایی و BM25"""
        combined_docs = []
        combined_meta = []
        seen_docs = set()

        if semantic_results.get('documents') and semantic_results['documents'][0]:
            for i, doc in enumerate(semantic_results['documents'][0]):
                doc_hash = hash(str(doc))
                if doc_hash not in seen_docs and i < len(semantic_results['metadatas'][0]):
                    seen_docs.add(doc_hash)
                    combined_docs.append(str(doc))
                    combined_meta.append(semantic_results['metadatas'][0][i])

        bm25_indices = np.argsort(bm25_scores)[-len(bm25_scores):][::-1]
        for idx in bm25_indices:
            if idx < len(self.documents):
                doc = str(self.documents[idx])
                doc_hash = hash(doc)
                if doc_hash not in seen_docs and bm25_scores[idx] > 0:
                    seen_docs.add(doc_hash)
                    combined_docs.append(doc)
                    combined_meta.append({'source': 'bm25', 'index': idx})

        return combined_docs, combined_meta

    def _dynamic_weighting(self,
                          query: str,
                          semantic_results: Dict,
                          bm25_scores: np.ndarray) -> Tuple[float, float]:
        """محاسبه وزن‌های پویا"""
        try:
            semantic_quality = 0.0
            if semantic_results.get('distances') and semantic_results['distances'][0]:
                semantic_quality = np.mean(semantic_results['distances'][0])

            bm25_quality = np.mean(bm25_scores) if len(bm25_scores) > 0 else 0.0
            total_quality = semantic_quality + bm25_quality

            if total_quality < 1e-6:
                return 0.7, 0.3

            semantic_weight = max(0.3, min(0.8, semantic_quality / total_quality))
            bm25_weight = 1 - semantic_weight

            return semantic_weight, bm25_weight

        except Exception as e:
            logger.warning(f"خطا در محاسبه وزن‌های پویا: {str(e)}")
            return 0.7, 0.3

    def _rerank_results(self, doc_pairs: List[Tuple[str, str]]) -> np.ndarray:
        """بازمرتب‌سازی نتایج با CrossEncoder"""
        try:
            return self.reranker.predict(doc_pairs)
        except Exception as e:
            logger.error(f"خطا در بازمرتب‌سازی: {str(e)}")
            return np.zeros(len(doc_pairs))

    def _get_from_cache(self, query: str, n_results: int) -> Optional[Dict]:
        """بازیابی از کش"""
        cache_key = f"{query}_{n_results}"
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return result
            del self.cache[cache_key]
        return None

    def _add_to_cache(self, query: str, n_results: int, result: Dict):
        """افزودن به کش"""
        cache_key = f"{query}_{n_results}"
        self.cache[cache_key] = (result, time.time())

        if len(self.cache) > self.max_cache_size:
            oldest_key = min(self.cache.keys(),
                           key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]