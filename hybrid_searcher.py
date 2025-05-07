# hybrid_searcher.py
from rank_bm25 import BM25Okapi
import numpy as np
from typing import Dict, List

class HybridSearcher:
    def __init__(self, collection):
        self.collection = collection
        self.bm25 = None
        self.documents: List[str] = []
        self._initialize()

    def _initialize(self):
        """آماده‌سازی موتور جستجو"""
        results = self.collection.get()
        if results and 'documents' in results:
            self.documents = results['documents']
            tokenized_docs = [doc.split() for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_docs)

    def search(self, query: str, n_results: int = 5) -> Dict:
        """جستجوی ترکیبی"""
        # جستجوی معنایی
        query_embedding = self.collection._embedding_function([query])[0]
        vector_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )

        # ترکیب نتایج (فعلاً فقط نتایج برداری برمی‌گرداند)
        return vector_results