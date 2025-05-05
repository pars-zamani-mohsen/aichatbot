import chromadb
import json
from pathlib import Path
import argparse
from datetime import datetime
import logging
from tqdm import tqdm

class KnowledgeBaseCreator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_data(self, embeddings_dir):
        """Load embeddings and metadata from files"""
        embeddings_path = Path(embeddings_dir) / 'embeddings.json'
        metadata_path = Path(embeddings_dir) / 'metadata.json'
        model_info_path = Path(embeddings_dir) / 'model_info.json'

        if not all(p.exists() for p in [embeddings_path, metadata_path, model_info_path]):
            raise FileNotFoundError("فایل‌های مورد نیاز یافت نشدند!")

        with open(embeddings_path) as f:
            embeddings = json.load(f)
        with open(metadata_path) as f:
            metadata = json.load(f)
        with open(model_info_path) as f:
            model_info = json.load(f)

        return embeddings, metadata, model_info

    def create_knowledge_base(self, embeddings_dir='embeddings', collection_name='website_data'):
        """Create and populate the knowledge base"""
        try:
            # Load data
            embeddings, metadata, model_info = self.load_data(embeddings_dir)

            if not metadata or not embeddings:
                raise ValueError("داده‌های ورودی خالی هستند!")

            # Create client and collection
            client = chromadb.PersistentClient(path="knowledge_base")
            print("کلاینت ChromaDB در مسیر knowledge_base ایجاد شد.")

            # Delete collection if exists
            try:
                client.delete_collection(collection_name)
            except:
                pass

            collection = client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            print(f"مدل استفاده شده: {model_info['model_name']}")
            print(f"ابعاد امبدینگ: {model_info['embedding_dimension']}")

            # Prepare data for insertion
            ids = [str(i) for i in range(len(metadata))]
            documents = [item['content'] for item in metadata]
            metadatas = [{
                'url': item['url'],
                'title': item['title'],
                'chunk_id': item['chunk_id'],
                'content_length': item['content_length']
            } for item in metadata]

            # Add data to collection in batches
            batch_size = 100
            for i in tqdm(range(0, len(ids), batch_size), desc="افزودن به پایگاه دانش"):
                batch_end = min(i + batch_size, len(ids))
                collection.add(
                    ids=ids[i:batch_end],
                    embeddings=embeddings[i:batch_end],
                    documents=documents[i:batch_end],
                    metadatas=metadatas[i:batch_end]
                )

            # Save database info
            db_info = {
                'collection_name': collection_name,
                'total_documents': len(ids),
                'model': model_info['model_name'],
                'embedding_dimension': model_info['embedding_dimension'],
                'created_at': datetime.now().isoformat()
            }

            with open('knowledge_base/db_info.json', 'w') as f:
                json.dump(db_info, f, indent=2)

            print(f"پایگاه دانش با {len(ids)} امبدینگ ایجاد شد.")
            print("اطلاعات پایگاه دانش در knowledge_base/db_info.json ذخیره شدند.")

        except Exception as e:
            self.logger.error(f"خطا در ایجاد پایگاه دانش: {str(e)}")
            raise

def parse_args():
    parser = argparse.ArgumentParser(description='ایجاد پایگاه دانش از امبدینگ‌ها')
    parser.add_argument('--embeddings_dir', type=str, default='embeddings',
                      help='مسیر دایرکتوری امبدینگ‌ها')
    parser.add_argument('--collection', type=str, default='website_data',
                      help='نام کالکشن در پایگاه دانش')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    creator = KnowledgeBaseCreator()
    creator.create_knowledge_base(embeddings_dir=args.embeddings_dir, collection_name=args.collection)