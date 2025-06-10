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

# تنظیم لاگر
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
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
        self.debug_mode = settings.DEBUG_MODE

        # تنظیمات کش
        self.cache = {}
        self.cache_ttl = 3600  # یک ساعت
        self.max_cache_size = 1000

        # تنظیم آستانه شباهت
        self.similarity_threshold = 0.45  # کاهش آستانه برای نتایج بیشتر

        self._initialize()

    def _log_debug(self, message: str, *args, **kwargs):
        """لاگ کردن پیام‌ها فقط در حالت دیباگ"""
        if self.debug_mode:
            logger.info(message, *args, **kwargs)

    def _initialize(self):
        """آماده‌سازی موتور جستجو"""
        try:
            results = self.collection.peek()
            if not results or not results['documents']:
                logger.warning("No documents found in collection")
                return

            docs = results['documents']
            if isinstance(docs[0], list):
                self.documents = [str(doc) for doc in docs[0]]
            else:
                self.documents = [str(doc) for doc in docs]

            # فیلتر کردن اسناد خالی یا خیلی کوتاه
            self.documents = [
                doc for doc in self.documents 
                if doc and isinstance(doc, str) and len(doc.strip()) > 50
            ]

            if not self.documents:
                logger.warning("No valid documents found after filtering")
                return

            # لاگ کردن نمونه اسناد فقط در حالت دیباگ
            self._log_debug("Sample documents:")
            for i, doc in enumerate(self.documents[:3]):
                self._log_debug(f"Document {i+1}: {doc[:200]}...")

            # توکن‌سازی اسناد
            tokenized_docs = []
            for doc in self.documents:
                tokens = self._tokenize_text(doc)
                if tokens:  # فقط اسنادی که توکن معتبر دارند
                    tokenized_docs.append(tokens)
                    # لاگ کردن نمونه توکن‌ها فقط در حالت دیباگ
                    if len(tokenized_docs) <= 3:
                        self._log_debug(f"Tokens for document {len(tokenized_docs)}: {tokens[:10]}...")

            if not tokenized_docs:
                logger.warning("No valid tokens found in documents")
                return

            # ایجاد موتور BM25
            self.bm25 = BM25Okapi(tokenized_docs)
            logger.info(f"تعداد اسناد بارگذاری شده: {len(self.documents)}")
            self._log_debug(f"تعداد توکن‌های منحصر به فرد: {len(set([token for doc in tokenized_docs for token in doc]))}")

            # تست جستجوی ساده
            test_query = "آموزش"
            test_tokens = self._tokenize_text(test_query)
            if test_tokens:
                test_scores = self.bm25.get_scores(test_tokens)
                self._log_debug(f"Test BM25 search for 'آموزش': {[f'{score:.4f}' for score in test_scores[:3]]}")

        except Exception as e:
            logger.error(f"خطا در آماده‌سازی: {str(e)}")
            self.documents = []
            self.bm25 = None

    def _normalize_text(self, text: str) -> str:
        """نرمال‌سازی متن با پشتیبانی از فارسی و انگلیسی"""
        try:
            if not text or not isinstance(text, str):
                return ""

            text = str(text).strip()
            if not text:
                return ""

            # تشخیص زبان
            try:
                lang = detect(text)
            except:
                lang = 'fa'  # در صورت خطا، فارسی در نظر گرفته می‌شود

            # حذف کاراکترهای خاص و علائم نگارشی
            text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)

            if lang == 'fa':
                # تبدیل اعداد عربی به فارسی
                replacements = {
                    'ي': 'ی', 'ك': 'ک', 'ة': 'ه',
                    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
                    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
                    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
                    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
                }
                for old, new in replacements.items():
                    text = text.replace(old, new)
            else:
                # تبدیل به حروف کوچک برای انگلیسی
                text = text.lower()

            # حذف فاصله‌های اضافی
            text = re.sub(r'\s+', ' ', text).strip()

            return text

        except Exception as e:
            logger.error(f"خطا در نرمال‌سازی متن: {str(e)}")
            return ""

    def _tokenize_text(self, text: str) -> List[str]:
        """تقسیم متن به توکن‌ها با پشتیبانی فارسی و انگلیسی"""
        try:
            if not text or not isinstance(text, str):
                return []

            normalized = self._normalize_text(text)
            if not normalized:
                return []

            tokens = []
            
            # حذف علامت‌های نگارشی
            normalized = re.sub(r'[؟،؛!?.,:;]', ' ', normalized)
            
            # جستجوی کلمات فارسی
            fa_words = re.findall(r'[\u0600-\u06FF]+', normalized)
            for word in fa_words:
                if len(word) > 1:
                    # اضافه کردن کلمه کامل
                    tokens.append(word)
                    # برای کلمات فارسی، فقط کلمات کامل را نگه می‌داریم
                    # چون n-gram‌ها می‌توانند باعث نویز شوند

            # جستجوی کلمات انگلیسی
            en_words = re.findall(r'[a-zA-Z]+', normalized)
            for word in en_words:
                if len(word) > 1:
                    # اضافه کردن کلمه کامل
                    tokens.append(word.lower())
                    # برای کلمات انگلیسی، n-gram‌ها مفید هستند
                    if len(word) > 5:  # برای کلمات انگلیسی طولانی‌تر
                        # اضافه کردن n-gram‌های 3 حرفی
                        for i in range(len(word)-2):
                            tokens.append(word[i:i+3].lower())

            # جستجوی اعداد
            numbers = re.findall(r'\d+', normalized)
            tokens.extend(numbers)

            # حذف توکن‌های تکراری
            tokens = list(set(tokens))

            # حذف توکن‌های خیلی کوتاه
            tokens = [token for token in tokens if len(token) > 1]

            # حذف توکن‌های عددی خیلی کوتاه
            tokens = [token for token in tokens if not (token.isdigit() and len(token) < 3)]

            # حذف توکن‌های حاوی علامت‌های نگارشی
            tokens = [token for token in tokens if not re.search(r'[؟،؛!?.,:;]', token)]

            # حذف توکن‌های فارسی خیلی کوتاه (کمتر از 3 حرف)
            tokens = [token for token in tokens if not (len(token) < 3 and re.search(r'[\u0600-\u06FF]', token))]

            # مرتب‌سازی توکن‌ها بر اساس طول (طولانی‌ترین اول)
            tokens.sort(key=len, reverse=True)

            # لاگ کردن توکن‌ها فقط در حالت دیباگ
            if len(tokens) > 0:
                self._log_debug(f"Tokens for text '{text[:50]}...': {tokens[:10]}...")

            return tokens

        except Exception as e:
            logger.error(f"خطا در توکن‌سازی: {str(e)}")
            return []

    def search(self, query: str, n_results: int = 5, query_type: str = 'general') -> Dict:
        """جستجو در اسناد با استفاده از ترکیب جستجوی معنایی و BM25"""
        if not self.documents:
            logger.warning("No documents available for search")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'has_results': False}

        try:
            # بررسی اعتبار کوئری
            if not query or not isinstance(query, str):
                logger.warning("Invalid query")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'has_results': False}

            query = query.strip()
            if not query:
                logger.warning("Empty query")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'has_results': False}

            # بررسی توکن‌های کوئری
            query_tokens = self._tokenize_text(query)
            if not query_tokens:
                logger.warning("No valid tokens in query")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'has_results': False}

            result = self._perform_search(query, n_results)

            if not result['documents'][0]:
                logger.info("No relevant documents found in database")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'has_results': False}

            if result['distances'][0]:
                raw_scores = result['distances'][0]
                max_score = max(raw_scores)
                threshold = self.similarity_threshold

                # اگر بهترین امتیاز زیر آستانه است، یعنی اطلاعات مرتبطی در دیتابیس وجود ندارد
                if max_score < threshold:
                    self._log_debug(f"Best match score {max_score:.4f} below threshold {threshold}, no relevant information found")
                    return {'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'has_results': False}

                # نرمال‌سازی امتیازات
                normalized_scores = [score / max_score for score in raw_scores]
                result['distances'][0] = normalized_scores

                self._log_debug(f"Search results - Max score: {max_score:.4f}")
                self._log_debug(f"Normalized scores: {[f'{score:.4f}' for score in normalized_scores]}")

            result['has_results'] = True
            return result

        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'has_results': False}

    def _perform_search(self, query: str, n_results: int) -> Dict:
        try:
            # جستجوی معنایی
            semantic_results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 3, len(self.documents))
            )

            if not semantic_results.get('distances') or not semantic_results['distances'][0]:
                logger.info("No semantic matches found in database")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            semantic_scores = semantic_results['distances'][0]
            
            # اگر همه امتیازات یکسان هستند، یعنی اطلاعات مرتبطی پیدا نشده
            if np.all(semantic_scores == semantic_scores[0]):
                self._log_debug("No distinct semantic matches found")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            # اگر بهترین امتیاز زیر آستانه است، لاگ می‌کنیم اما ادامه می‌دهیم
            max_semantic_score = max(semantic_scores)
            if max_semantic_score < self.similarity_threshold:
                self._log_debug(f"Best semantic score {max_semantic_score:.4f} below threshold {self.similarity_threshold}, but continuing search")

            self._log_debug(f"Semantic Scores: {[f'{score:.4f}' for score in semantic_scores]}")

            # جستجوی BM25
            tokenized_query = self._tokenize_text(query)
            if not tokenized_query:
                logger.info("Query contains no searchable terms")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            bm25_scores = self.bm25.get_scores(tokenized_query)
            if len(bm25_scores) == 0:
                logger.info("No BM25 matches found")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            # نرمال‌سازی امتیازات BM25
            max_bm25_score = max(bm25_scores)
            min_bm25_score = min(bm25_scores)
            if max_bm25_score > min_bm25_score:
                # نرمال‌سازی به بازه [0, 1]
                bm25_scores = (bm25_scores - min_bm25_score) / (max_bm25_score - min_bm25_score)
                self._log_debug(f"BM25 Scores (normalized): {[f'{score:.4f}' for score in bm25_scores]}")
            else:
                logger.info("No relevant BM25 matches found")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            # محاسبه وزن‌های پویا
            sem_w, bm25_w = self._dynamic_weighting(query, semantic_results, bm25_scores)
            self._log_debug(f"Weights - Semantic: {sem_w:.4f}, BM25: {bm25_w:.4f}")

            # ترکیب نتایج
            combined_docs, combined_meta = self._combine_results(
                semantic_results, bm25_scores, sem_w, bm25_w
            )

            if not combined_docs:
                logger.info("No combined matches found")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            # بازمرتب‌سازی با CrossEncoder
            doc_pairs = [(doc, query) for doc in combined_docs]
            rerank_scores = self._rerank_results(doc_pairs)
            
            if len(rerank_scores) == 0:
                logger.info("No reranking scores available")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            # انتخاب بهترین نتایج
            top_k = min(n_results, len(combined_docs))
            indices = None
            final_scores = None

            # اگر همه امتیازات بازمرتب‌سازی یکسان هستند، از امتیازات معنایی استفاده کن
            if np.all(rerank_scores == rerank_scores[0]):
                self._log_debug("Using semantic scores for ranking")
                indices = np.argsort(semantic_scores)[-top_k:][::-1]
                final_scores = [float(semantic_scores[i]) for i in indices]
            else:
                # نرمال‌سازی امتیازات بازمرتب‌سازی
                max_rerank = np.max(rerank_scores)
                min_rerank = np.min(rerank_scores)
                if max_rerank > min_rerank:
                    rerank_scores = (rerank_scores - min_rerank) / (max_rerank - min_rerank)
                else:
                    self._log_debug("No distinct reranking scores available")
                    return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

                self._log_debug(f"Rerank Scores (normalized): {[f'{score:.4f}' for score in rerank_scores]}")
                indices = np.argsort(rerank_scores)[-top_k:][::-1]
                final_scores = [float(rerank_scores[i]) for i in indices]

            if indices is None or final_scores is None:
                logger.info("Failed to generate final results")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            # بررسی کیفیت نهایی نتایج
            if np.all(final_scores == final_scores[0]):
                self._log_debug("No distinct final scores available")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            self._log_debug(f"Final Scores: {[f'{score:.4f}' for score in final_scores]}")

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
        """محاسبه وزن‌های پویا برای ترکیب نتایج معنایی و BM25"""
        try:
            # محاسبه کیفیت جستجوی معنایی
            semantic_quality = 0.0
            if semantic_results.get('distances') and semantic_results['distances'][0]:
                semantic_scores = semantic_results['distances'][0]
                # استفاده از میانگین وزنی برای امتیازات معنایی
                semantic_quality = np.average(semantic_scores, weights=range(1, len(semantic_scores) + 1))

            # محاسبه کیفیت جستجوی BM25
            bm25_quality = 0.0
            if len(bm25_scores) > 0:
                # استفاده از میانگین وزنی برای امتیازات BM25
                bm25_quality = np.average(bm25_scores, weights=range(1, len(bm25_scores) + 1))

            # محاسبه مجموع کیفیت‌ها
            total_quality = semantic_quality + bm25_quality

            # اگر کیفیت کل خیلی پایین است، از وزن‌های پیش‌فرض استفاده کن
            if total_quality < 1e-6:
                return 0.7, 0.3

            # محاسبه وزن‌های نهایی با محدودیت‌های معقول
            semantic_weight = max(0.3, min(0.8, semantic_quality / total_quality))
            bm25_weight = 1 - semantic_weight

            # اطمینان از اینکه مجموع وزن‌ها برابر 1 است
            total_weight = semantic_weight + bm25_weight
            if total_weight != 1.0:
                semantic_weight = semantic_weight / total_weight
                bm25_weight = bm25_weight / total_weight

            return semantic_weight, bm25_weight

        except Exception as e:
            logger.error(f"خطا در محاسبه وزن‌های پویا: {str(e)}")
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
            
            # اگر همه امتیازات یکسان هستند، از امتیازات معنایی استفاده می‌کنیم
            if np.all(scores == scores[0]):
                return np.ones(len(doc_pairs))
            
            # تبدیل امتیازات منفی به مثبت
            if np.any(scores < 0):
                scores = scores - np.min(scores)
            
            # نرمال‌سازی به بازه [0, 1]
            max_score = np.max(scores)
            min_score = np.min(scores)
            
            # اگر همه امتیازات یکسان هستند، یک آرایه با امتیازات یکسان برمی‌گردانیم
            if max_score == min_score:
                return np.ones(len(doc_pairs))
            
            # نرمال‌سازی به بازه [0, 1]
            scores = (scores - min_score) / (max_score - min_score)
            
            logger.info(f"Raw rerank scores: {[f'{score:.4f}' for score in raw_scores]}")
            logger.info(f"Normalized rerank scores: {[f'{score:.4f}' for score in scores]}")
            
            return scores

        except Exception as e:
            logger.error(f"خطا در بازمرتب‌سازی: {str(e)}")
            return np.ones(len(doc_pairs))  # در صورت خطا، امتیازات یکسان برمی‌گردانیم

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