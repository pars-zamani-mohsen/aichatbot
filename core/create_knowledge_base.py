import sys
import json
from datetime import datetime
import argparse
from pathlib import Path
import chromadb
from chromadb.config import Settings
import logging
import pandas as pd
from settings import (
    DB_DIRECTORY,
    COLLECTION_NAME
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_knowledge_base(
    embeddings_dir,
    collection_name,
    db_path
):
    """
    ایجاد پایگاه دانش از امبدینگ‌ها
    
    Args:
        embeddings_dir (str): مسیر پوشه امبدینگ‌ها
        collection_name (str): نام کالکشن در پایگاه دانش
        db_path (str): مسیر پایگاه دانش
    
    Returns:
        bool: True در صورت موفقیت، False در صورت خطا
    """
    try:
        embeddings_dir = Path(embeddings_dir)
        # ساخت مسیر پایگاه داده در کنار embeddings
        db_path = embeddings_dir.parent / 'knowledge_base'
        db_path.mkdir(parents=True, exist_ok=True)

        # خواندن فایل‌های امبدینگ
        logger.info("خواندن فایل‌های امبدینگ...")
        with open(embeddings_dir / 'embeddings.json', 'r') as f:
            embeddings = json.load(f)

        with open(embeddings_dir / 'metadata.json', 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        with open(embeddings_dir / 'model_info.json', 'r', encoding='utf-8') as f:
            model_info = json.load(f)

        # بررسی و چاپ ساختار داده‌ها برای دیباگ
        logger.info(f"ساختار metadata: {list(metadata[0].keys()) if metadata else 'خالی'}")

        # تنظیم مسیر پایگاه دانش
        db_path = Path(db_path)
        db_path.mkdir(parents=True, exist_ok=True)

        # ایجاد کلاینت ChromaDB
        logger.info("ایجاد کلاینت ChromaDB...")
        client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(
                anonymized_telemetry=False,
                is_persistent=True
            )
        )

        # حذف کالکشن قبلی با همین نام (اگر وجود داشت)
        try:
            client.delete_collection(collection_name)
            logger.info(f"کالکشن قبلی {collection_name} حذف شد")
        except:
            pass

        # ایجاد کالکشن جدید
        collection = client.create_collection(name=collection_name)

        # خواندن داده‌های اصلی برای دسترسی به محتوا
        logger.info("خواندن داده‌های اصلی...")
        data_df = pd.read_csv(embeddings_dir.parent / 'processed_data.csv')
        content_map = dict(zip(data_df['url'], data_df['content']))

        # تهیه لیست‌ها با بررسی وجود کلیدها
        ids = []
        documents = []
        metadatas = []

        for i, m in enumerate(metadata):
            # بررسی و استخراج فیلدهای اصلی
            doc_id = str(m.get('chunk_id', i))
            title = m.get('title', '')
            url = m.get('url', '')
            timestamp = m.get('timestamp', datetime.now().isoformat())

            # استخراج محتوا از دیتافریم اصلی
            content = content_map.get(url, title)

            ids.append(doc_id)
            documents.append(f"{title}\n\n{content}")
            metadatas.append({
                'url': url,
                'title': title,
                'timestamp': timestamp
            })

        # افزودن داده‌ها به کالکشن
        logger.info("افزودن داده‌ها به کالکشن...")
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        # ذخیره اطلاعات پایگاه دانش
        db_info = {
            'collection_name': collection_name,
            'num_documents': len(documents),
            'model_info': model_info,
            'embedding_size': model_info['embedding_size']
        }

        with open(db_path / 'db_info.json', 'w', encoding='utf-8') as f:
            json.dump(db_info, f, ensure_ascii=False, indent=2)

        logger.info(f"\n=== پایگاه دانش با موفقیت ایجاد شد ===")
        logger.info(f"نام کالکشن: {collection_name}")
        logger.info(f"تعداد اسناد: {len(documents)}")
        logger.info(f"مسیر پایگاه دانش: {db_path}")

        return True

    except Exception as e:
        logger.error(f"خطا در ایجاد پایگاه دانش: {str(e)}")
        raise

def parse_args():
    parser = argparse.ArgumentParser(description='ایجاد پایگاه دانش از امبدینگ‌ها')
    parser.add_argument('--embeddings_dir', required=True, help='مسیر پوشه امبدینگ‌ها')
    parser.add_argument('--collection', default='parsicanada', help='نام کالکشن در پایگاه دانش')
    parser.add_argument('--db-path', default='processed_data/knowledge_base', help='مسیر پایگاه دانش')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    success = create_knowledge_base(
        args.embeddings_dir,
        args.collection,
        args.db_path
    )
    sys.exit(0 if success else 1)