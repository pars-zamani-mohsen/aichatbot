from typing import Dict, List
from chromadb.api import Collection  # Fixed import
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

class HybridSearcher:
    def __init__(self, collection: Collection):
        self.collection = collection
        self.documents = []
        self.bm25 = None
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
        """جستجوی ترکیبی"""
        if not self.documents:
            return {'documents': [], 'metadatas': [], 'distances': [[]]}

        try:
            # جستجوی معنایی
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, len(self.documents))
            )

            return results

        except Exception as e:
            print(f"خطا در جستجو: {str(e)}")
            return {'documents': [], 'metadatas': [], 'distances': [[]]}