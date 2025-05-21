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
    EMBEDDING_MODEL_NAME,
    SIMILARITY_THRESHOLD
)
from core.text_processor import TextProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HybridSearcher:
    def __init__(self, collection: Collection):
        self.collection = collection
        self.text_processor = TextProcessor()
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Initialize BM25
        self.documents = []
        self._initialize_bm25()

    def _initialize_bm25(self):
        """Initialize BM25 with processed documents"""
        try:
            # Get all documents from collection
            results = self.collection.get()
            if results and results['documents']:
                self.documents = results['documents']
                # Process documents for BM25
                processed_docs = [
                    self.text_processor.normalize_text(doc)
                    for doc in self.documents
                ]
                self.bm25 = BM25Okapi(processed_docs)
            else:
                self.bm25 = None
                logger.warning("No documents found in collection for BM25 initialization")
        except Exception as e:
            logger.error(f"Error initializing BM25: {str(e)}")
            self.bm25 = None

    def search(self, query: str, n_results: int = 5, query_type: str = 'general') -> Dict:
        """Perform hybrid search combining semantic and keyword-based approaches"""
        try:
            # Check cache first
            cached_result = self._get_from_cache(query, n_results)
            if cached_result:
                return cached_result

            # Process query
            processed_query_text = self.text_processor.normalize_text(query)

            # Perform semantic search
            semantic_results = self.collection.query(
                query_texts=[processed_query_text],
                n_results=min(n_results * 2, len(self.documents))
            )

            # Perform BM25 search if available
            if self.bm25:
                bm25_scores = self.bm25.get_scores(processed_query_text)
            else:
                bm25_scores = np.zeros(len(self.documents))

            # Calculate dynamic weights
            sem_w, bm25_w = self._dynamic_weighting(query, semantic_results, bm25_scores)

            # Combine results
            combined_docs, combined_meta = self._combine_results(
                semantic_results, bm25_scores, sem_w, bm25_w
            )

            if not combined_docs:
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

            # Rerank results
            final_scores = self._rerank_results(
                [(doc, processed_query_text) for doc in combined_docs]
            )

            # Get top results
            top_k = min(n_results, len(combined_docs))
            indices = np.argsort(final_scores)[-top_k:][::-1]

            result = {
                'documents': [[combined_docs[i] for i in indices]],
                'metadatas': [[combined_meta[i] for i in indices]],
                'distances': [[float(final_scores[i]) for i in indices]]
            }

            # Cache result
            self._add_to_cache(query, n_results, result)

            return result

        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

    def _combine_results(self, semantic_results: Dict, bm25_scores: np.ndarray,
                        sem_w: float, bm25_w: float) -> Tuple[List[str], List[Dict]]:
        """Combine semantic and BM25 results"""
        try:
            if not semantic_results['documents'][0]:
                return [], []

            # Get unique documents
            seen_docs = set()
            combined_docs = []
            combined_meta = []

            # Process semantic results
            for doc, meta in zip(semantic_results['documents'][0], semantic_results['metadatas'][0]):
                if doc not in seen_docs:
                    seen_docs.add(doc)
                    combined_docs.append(doc)
                    combined_meta.append(meta)

            # Add top BM25 results if not already included
            if len(bm25_scores) > 0:
                top_bm25_indices = np.argsort(bm25_scores)[-len(combined_docs):][::-1]
                for idx in top_bm25_indices:
                    doc = self.documents[idx]
                    if doc not in seen_docs:
                        seen_docs.add(doc)
                        combined_docs.append(doc)
                        combined_meta.append({'source': 'bm25'})

            return combined_docs, combined_meta

        except Exception as e:
            logger.error(f"Error combining results: {str(e)}")
            return [], []

    def _dynamic_weighting(self, query: str, semantic_results: Dict,
                          bm25_scores: np.ndarray) -> Tuple[float, float]:
        """Calculate dynamic weights based on query characteristics"""
        try:
            # Process query
            processed_query = self.text_processor.normalize_text(query)
            query_words = processed_query.split()

            # Calculate query characteristics
            query_length = len(query_words)
            query_complexity = len(set(query_words)) / max(1, query_length)

            # Adjust weights based on query characteristics
            if query_length <= 2:
                # Short queries benefit more from semantic search
                return 0.8, 0.2
            elif query_complexity > 0.7:
                # Complex queries benefit more from semantic search
                return 0.7, 0.3
            else:
                # Balanced approach for medium-length queries
                return 0.6, 0.4

        except Exception as e:
            logger.warning(f"Error in dynamic weighting: {str(e)}")
            return 0.6, 0.4

    def _rerank_results(self, doc_pairs: List[Tuple[str, str]]) -> np.ndarray:
        """Rerank results using cross-encoder"""
        try:
            scores = self.reranker.predict(doc_pairs)
            normalized_scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-6)
            return normalized_scores
        except Exception as e:
            logger.error(f"Error in reranking: {str(e)}")
            return np.zeros(len(doc_pairs))

    def _get_from_cache(self, query: str, n_results: int) -> Optional[Dict]:
        """Get results from cache"""
        cache_key = f"{query}_{n_results}"
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return result
            del self.cache[cache_key]
        return None

    def _add_to_cache(self, query: str, n_results: int, result: Dict):
        """Add results to cache"""
        cache_key = f"{query}_{n_results}"
        self.cache[cache_key] = (result, time.time())