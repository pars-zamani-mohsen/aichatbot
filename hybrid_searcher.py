from typing import Dict, List
from chromadb.api import Collection
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

class HybridSearcher:
    def __init__(self, collection: Collection):
        self.collection = collection
        self.documents = []
        self.bm25 = None
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')  # مدل قوی‌تر
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

            # آماده‌سازی BM25
            if self.documents:
                tokenized_docs = [doc.split() for doc in self.documents]
                self.bm25 = BM25Okapi(tokenized_docs)
                print(f"تعداد اسناد بارگذاری شده: {len(self.documents)}")

        except Exception as e:
            print(f"خطا در آماده‌سازی: {str(e)}")
            self.documents = []
            self.bm25 = None

    def search(self, query: str, n_results: int = 5) -> Dict:
        """جستجوی ترکیبی بهبود یافته"""
        if not self.documents:
            return {'documents': [], 'metadatas': [], 'distances': [[]]}

        try:
            # جستجوی معنایی با تعداد نتایج بیشتر
            semantic_results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 3, len(self.documents))
            )

            # جستجوی لغوی
            bm25_scores = self.bm25.get_scores(query.split())
            bm25_indices = np.argsort(bm25_scores)[-n_results*3:][::-1]

            # ترکیب نتایج با حذف تکرار
            seen_docs = set()
            combined_docs = []
            combined_meta = []
            doc_pairs = []

            # اولویت با نتایج معنایی
            for doc, meta in zip(semantic_results['documents'][0], semantic_results['metadatas'][0]):
                doc_id = meta.get('chunk_id', doc[:100])
                if doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    combined_docs.append(doc)
                    combined_meta.append(meta)
                    doc_pairs.append((doc, query))

            # اضافه کردن نتایج BM25
            for idx in bm25_indices:
                doc = self.documents[idx]
                if doc not in seen_docs:
                    seen_docs.add(doc)
                    combined_docs.append(doc)
                    combined_meta.append({'url': '', 'title': '', 'chunk_id': f'bm25_{idx}'})
                    doc_pairs.append((doc, query))

            # رتبه‌بندی مجدد با امتیازدهی دقیق‌تر
            if doc_pairs:
                scores = self.reranker.predict(
                    doc_pairs,
                    batch_size=32,
                    show_progress_bar=False
                )

                # نرمال‌سازی امتیازها
                scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-6)

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