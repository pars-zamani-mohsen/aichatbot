from typing import Dict, List, Optional, Tuple
from sentence_transformers import CrossEncoder
from chromadb.api import Collection
from rank_bm25 import BM25Okapi
from langdetect import detect
import numpy as np
import logging
import time
import re
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HybridSearcher:
    def __init__(
        self,
        collection: Collection,
        chunk_size: int = None,
        max_tokens: int = None,
        tokens_per_min: int = None,
        embedding_model: str = None
    ):
        self.collection = collection
        self.documents = []
        self.bm25 = None
        self.chunk_size = chunk_size or int(settings.CHUNK_SIZE)
        self.max_tokens = max_tokens or int(settings.MAX_TOKENS)
        self.tokens_per_min = tokens_per_min or int(settings.TOKENS_PER_MIN)
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL_NAME
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

        # تنظیمات کش
        self.cache = {}
        self.cache_ttl = 3600  # یک ساعت
        self.max_cache_size = 1000
        self._initialize()

        # اضافه کردن آستانه شباهت به تنظیمات
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD

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

    def search(self, query: str, n_results: int = 5, query_type: str = 'general') -> Dict:
        if not self.documents:
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

        try:
            result = self._perform_search(query, n_results)

            if result['distances'][0]:
                raw_scores = result['distances'][0]
                max_score = max(raw_scores)
                mean_score = np.mean(raw_scores)
                threshold = self.similarity_threshold

                # نرمال‌سازی امتیازات
                normalized_scores = [score / max_score for score in raw_scores]
                
                # بررسی کیفیت نتایج با امتیازات نرمال‌شده
                if max_score < threshold:
                    logger.info(f"Best score {max_score:.4f} below threshold {threshold}")
                    return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

                # اگر اختلاف بین بهترین امتیاز و میانگین خیلی کم باشد، نتایج را بی‌اعتبار بدان
                if (max_score - mean_score) < 0.1:
                    logger.info(f"Results not distinct enough: max={max_score:.4f}, mean={mean_score:.4f}")
                    return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

                # استفاده از امتیازات نرمال‌شده برای نتایج نهایی
                result['distances'][0] = normalized_scores

                # لاگ کردن اطلاعات بیشتر برای دیباگ
                logger.info(f"Search results - Max score: {max_score:.4f}, Mean score: {mean_score:.4f}")
                logger.info(f"Normalized scores: {[f'{score:.4f}' for score in normalized_scores]}")

            return result

        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

    def _perform_search(self, query: str, n_results: int) -> Dict:
        try:
            # جستجوی معنایی
            semantic_results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, len(self.documents))
            )

            if not semantic_results.get('distances') or not semantic_results['distances'][0]:
                logger.warning("No semantic search results found")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            semantic_scores = semantic_results['distances'][0]
            logger.info(f"Semantic Scores: {[f'{score:.4f}' for score in semantic_scores]}")

            # جستجوی BM25
            bm25_scores = self.bm25.get_scores(self._tokenize_text(query))
            if len(bm25_scores) == 0:
                logger.warning("No BM25 scores found")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            # نرمال‌سازی امتیازات BM25
            if max(bm25_scores) > 0:
                bm25_scores = bm25_scores / max(bm25_scores)

            logger.info(f"BM25 Scores (normalized): {[f'{score:.4f}' for score in bm25_scores]}")

            # محاسبه وزن‌های پویا
            sem_w, bm25_w = self._dynamic_weighting(query, semantic_results, bm25_scores)
            logger.info(f"Weights - Semantic: {sem_w:.4f}, BM25: {bm25_w:.4f}")

            # ترکیب نتایج
            combined_docs, combined_meta = self._combine_results(
                semantic_results, bm25_scores, sem_w, bm25_w
            )

            if not combined_docs:
                logger.warning("No combined results found")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            # بازمرتب‌سازی با CrossEncoder
            doc_pairs = [(doc, query) for doc in combined_docs]
            rerank_scores = self._rerank_results(doc_pairs)
            
            if len(rerank_scores) == 0:
                logger.warning("No reranking scores found")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            # نرمال‌سازی امتیازات بازمرتب‌سازی
            max_rerank = np.max(rerank_scores)
            if max_rerank > 0:
                rerank_scores = rerank_scores / max_rerank

            logger.info(f"Rerank Scores (normalized): {[f'{score:.4f}' for score in rerank_scores]}")

            # انتخاب بهترین نتایج
            top_k = min(n_results, len(combined_docs))
            indices = np.argsort(rerank_scores)[-top_k:][::-1]

            final_scores = [float(rerank_scores[i]) for i in indices]
            logger.info(f"Final Scores: {[f'{score:.4f}' for score in final_scores]}")

            return {
                'documents': [[combined_docs[i] for i in indices]],
                'metadatas': [[combined_meta[i] for i in indices]],
                'distances': [final_scores]
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
            if not doc_pairs:
                return np.array([])

            # دریافت امتیازات خام
            raw_scores = self.reranker.predict(doc_pairs)
            
            # تبدیل امتیازات به آرایه numpy
            scores = np.array(raw_scores)
            
            # اگر همه امتیازات منفی هستند، آنها را به بازه مثبت تبدیل می‌کنیم
            if np.all(scores < 0):
                scores = scores - np.min(scores)
            
            # نرمال‌سازی به بازه [0, 1]
            if np.max(scores) > 0:
                scores = scores / np.max(scores)
            
            logger.info(f"Raw rerank scores: {[f'{score:.4f}' for score in raw_scores]}")
            logger.info(f"Normalized rerank scores: {[f'{score:.4f}' for score in scores]}")
            
            return scores

        except Exception as e:
            logger.error(f"خطا در بازمرتب‌سازی: {str(e)}")
            return np.array([0.0] * len(doc_pairs))

    def _get_from_cache(self, query: str, n_results: int) -> Optional[Dict]:
        """دریافت نتایج از کش"""
        cache_key = f"{query}_{n_results}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                return cache_entry['result']
        return None

    def _add_to_cache(self, query: str, n_results: int, result: Dict):
        """اضافه کردن نتایج به کش"""
        if len(self.cache) >= self.max_cache_size:
            # حذف قدیمی‌ترین ورودی
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]

        cache_key = f"{query}_{n_results}"
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        } 