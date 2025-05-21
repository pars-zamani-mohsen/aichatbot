import json
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import logging
from settings import (
    DB_DIRECTORY,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    CHUNK_SIZE
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_and_create_kb(domain: str):
    """Process data and create knowledge base for a domain"""
    try:
        # Read processed data
        data_path = Path('backend/processed_data') / domain / 'processed_data.json'
        logger.info(f"Reading processed data from {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Load embedding model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        
        # Create embeddings
        logger.info("Creating embeddings...")
        embeddings = []
        documents = []
        metadatas = []
        ids = []
        
        for i, row in df.iterrows():
            # Create embedding
            embedding = model.encode(row['content'])
            embeddings.append(embedding.tolist())
            
            # Prepare document
            doc = f"{row.get('title', '')}\n\n{row['content']}"
            documents.append(doc)
            
            # Prepare metadata
            metadata = {
                'url': row.get('url', ''),
                'title': row.get('title', ''),
                'timestamp': row.get('timestamp', '')
            }
            metadatas.append(metadata)
            
            # Create ID
            ids.append(str(i))
            
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1} documents")
        
        # Initialize ChromaDB
        logger.info("Initializing ChromaDB...")
        client = chromadb.PersistentClient(
            path=str(Path(DB_DIRECTORY)),
            settings=Settings(
                anonymized_telemetry=False,
                is_persistent=True
            )
        )
        
        # Create or get collection
        collection_name = f"site_{domain}"
        try:
            client.delete_collection(collection_name)
        except:
            pass
        
        collection = client.create_collection(name=collection_name)
        
        # Add documents to collection
        logger.info("Adding documents to collection...")
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Successfully created knowledge base for {domain}")
        logger.info(f"Total documents: {len(documents)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing data and creating knowledge base: {str(e)}")
        raise

if __name__ == "__main__":
    domain = "parsicanada.com"
    process_and_create_kb(domain) 