import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from chromadb import Client, Settings
from chromadb.utils import embedding_functions
import logging
from pathlib import Path
from typing import List, Dict, Optional
from app.config import settings
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance = None
    _model = None
    _client = None
    _collection = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        model_name: str = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
        db_directory: str = None,
        collection_name: str = None
    ):
        if hasattr(self, 'initialized'):
            return
            
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.chunk_size = chunk_size or int(settings.CHUNK_SIZE)
        self.chunk_overlap = chunk_overlap or int(settings.CHUNK_OVERLAP)
        self.db_directory = Path(db_directory or settings.DB_DIRECTORY)
        self.collection_name = collection_name or settings.COLLECTION_NAME
        
        # ایجاد دایرکتوری دیتابیس
        self.db_directory.mkdir(parents=True, exist_ok=True)
        
        # بارگذاری مدل و تنظیمات ChromaDB
        self._initialize_services()
        
        self.initialized = True
        
    def _initialize_services(self):
        """بارگذاری مدل و تنظیمات ChromaDB"""
        start_time = time.time()
        
        # بارگذاری مدل اگر قبلاً بارگذاری نشده
        if EmbeddingService._model is None:
            try:
                logger.info("Loading SentenceTransformer model...")
                EmbeddingService._model = SentenceTransformer(self.model_name)
                logger.info(f"Model {self.model_name} loaded successfully in {time.time() - start_time:.2f} seconds")
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                raise
        
        # تنظیمات ChromaDB اگر قبلاً انجام نشده
        if EmbeddingService._client is None:
            try:
                logger.info("Setting up ChromaDB...")
                EmbeddingService._client = Client(Settings(
                    persist_directory=str(self.db_directory),
                    anonymized_telemetry=False
                ))
                
                # تنظیم تابع embedding
                self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=self.model_name
                )
                
                # ایجاد یا دریافت collection
                EmbeddingService._collection = EmbeddingService._client.get_or_create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function
                )
                
                logger.info(f"ChromaDB setup completed in {time.time() - start_time:.2f} seconds")
                
            except Exception as e:
                logger.error(f"Error setting up ChromaDB: {str(e)}")
                raise
        
        self.model = EmbeddingService._model
        self.client = EmbeddingService._client
        self.collection = EmbeddingService._collection
        
    def _chunk_text(self, text: str) -> List[str]:
        """تقسیم متن به قطعات کوچکتر"""
        if not text:
            return []
            
        start_time = time.time()
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk:
                chunks.append(chunk)
                
        logger.info(f"Text chunking completed in {time.time() - start_time:.2f} seconds")
        return chunks
        
    def _create_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """ایجاد embedding برای متون"""
        try:
            start_time = time.time()
            
            # تقسیم متن‌ها به batch‌های کوچکتر
            batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
            logger.info(f"Processing {len(batches)} batches with batch size {batch_size}")
            
            # پردازش batch‌ها
            results = []
            for i, batch in enumerate(batches):
                batch_result = self.model.encode(
                    batch,
                    show_progress_bar=True,
                    batch_size=batch_size
                )
                results.append(batch_result)
                
                if (i + 1) % 5 == 0:  # لاگ هر 5 batch
                    elapsed = time.time() - start_time
                    logger.info(f"Processed batch {i+1}/{len(batches)} in {elapsed:.2f} seconds")
                
                # پاکسازی حافظه بعد از هر batch
                if i % 10 == 0:
                    import gc
                    gc.collect()
            
            # ترکیب نتایج
            final_result = np.vstack(results)
            logger.info(f"All embeddings created in {time.time() - start_time:.2f} seconds")
            return final_result
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise
            
    def process_text(self, text: str, metadata: Optional[Dict] = None) -> None:
        """پردازش متن و ذخیره در دیتابیس"""
        try:
            start_time = time.time()
            logger.info("Starting text processing...")
            
            # تقسیم متن به قطعات
            chunks = self._chunk_text(text)
            if not chunks:
                logger.warning("No chunks created from text")
                return
                
            logger.info(f"Created {len(chunks)} chunks from text")
            
            # ایجاد embedding
            logger.info("Starting embedding creation...")
            embeddings = self._create_embeddings(chunks)
            logger.info(f"Created embeddings with shape: {embeddings.shape}")
            
            # ساخت ids یکتا برای هر chunk
            logger.info("Generating unique IDs for chunks...")
            ids = [
                (metadata.get("chunk_id") if metadata and metadata.get("chunk_id") else f"{metadata.get('url', '')}_{i}")
                for i in range(len(chunks))
            ]
            
            # ذخیره در دیتابیس به صورت batch‌های کوچکتر
            logger.info("Storing data in ChromaDB...")
            store_start_time = time.time()
            
            # حداکثر اندازه batch برای ChromaDB
            max_batch_size = 5000
            
            # تقسیم داده‌ها به batch‌های کوچکتر
            for i in range(0, len(chunks), max_batch_size):
                batch_end = min(i + max_batch_size, len(chunks))
                logger.info(f"Storing batch {i//max_batch_size + 1} ({i} to {batch_end})")
                
                self.collection.add(
                    ids=ids[i:batch_end],
                    embeddings=embeddings[i:batch_end].tolist(),
                    documents=chunks[i:batch_end],
                    metadatas=[metadata] * (batch_end - i) if metadata else None
                )
                
                # پاکسازی حافظه بعد از هر batch
                import gc
                gc.collect()
            
            store_time = time.time() - store_start_time
            logger.info(f"Data stored in ChromaDB in {store_time:.2f} seconds")
            
            total_time = time.time() - start_time
            logger.info(f"Total processing completed in {total_time:.2f} seconds")
            logger.info(f"Average time per chunk: {total_time/len(chunks):.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise
            
    def process_file(self, file_path: str, metadata: Optional[Dict] = None) -> None:
        """پردازش فایل و ذخیره در دیتابیس"""
        try:
            # خواندن فایل
            df = pd.read_csv(file_path)
            
            # پردازش هر سطر
            for _, row in df.iterrows():
                text = f"{row.get('title', '')} {row.get('text', '')}"
                row_metadata = {
                    'url': row.get('url', ''),
                    'title': row.get('title', ''),
                    **(metadata or {})
                }
                self.process_text(text, row_metadata)
                
            logger.info(f"File {file_path} processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise
            
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """جستجو در دیتابیس"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            return [
                {
                    'text': doc,
                    'metadata': meta,
                    'distance': dist
                }
                for doc, meta, dist in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )
            ]
            
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            raise 