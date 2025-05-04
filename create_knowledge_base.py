# create_knowledge_base.py

import os
import json
import numpy as np
import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm

class KnowledgeBaseCreator:
    def __init__(self, db_directory="knowledge_base"):
        """مقداردهی اولیه کلاس با پوشه پایگاه دانش"""

        self.db_directory = db_directory
        os.makedirs(db_directory, exist_ok=True)

        # ایجاد کلاینت ChromaDB
        self.client = chromadb.PersistentClient(path=db_directory)
        print(f"کلاینت ChromaDB در مسیر {db_directory} ایجاد شد.")

    def create_knowledge_base(self, embeddings_dir="embeddings", collection_name="website_data"):
        """ایجاد پایگاه دانش با استفاده از امبدینگ‌های ذخیره شده"""

        # خواندن فایل‌های امبدینگ و متادیتا
        embeddings_file = os.path.join(embeddings_dir, 'embeddings.json')
        metadata_file = os.path.join(embeddings_dir, 'metadata.json')
        model_info_file = os.path.join(embeddings_dir, 'model_info.json')

        if not os.path.exists(embeddings_file) or not os.path.exists(metadata_file):
            raise FileNotFoundError(f"فایل امبدینگ یا متادیتا در مسیر {embeddings_dir} یافت نشد.")

        # خواندن اطلاعات مدل
        with open(model_info_file, 'r', encoding='utf-8') as f:
            model_info = json.load(f)

        print(f"مدل استفاده شده: {model_info['model_name']}")
        print(f"ابعاد امبدینگ: {model_info['embedding_dimension']}")

        # خواندن امبدینگ‌ها
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            embeddings_data = json.load(f)

        # خواندن متادیتا
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # ایجاد دیکشنری متادیتا برای دسترسی سریع
        metadata_dict = {item['id']: item for item in metadata}

        # حذف کالکشن اگر از قبل وجود دارد
        try:
            self.client.delete_collection(name=collection_name)
            print(f"کالکشن {collection_name} موجود حذف شد.")
        except:
            pass

        # ایجاد کالکشن جدید
        collection = self.client.create_collection(
            name=collection_name,
            metadata={"model": model_info['model_name']}
        )

        print(f"شروع افزودن {len(embeddings_data)} امبدینگ به پایگاه دانش...")

        # افزودن داده‌ها به کالکشن به صورت بسته‌ای
        batch_size = 100
        for i in tqdm(range(0, len(embeddings_data), batch_size)):
            batch = embeddings_data[i:i+batch_size]

            ids = []
            embeddings = []
            documents = []
            metadatas = []

            for item in batch:
                doc_id = item['id']
                embedding = item['embedding']

                if doc_id in metadata_dict:
                    meta = metadata_dict[doc_id]
                    content = meta.get('content', '')

                    ids.append(doc_id)
                    embeddings.append(embedding)
                    documents.append(content)
                    metadatas.append({
                        'url': meta.get('url', ''),
                        'title': meta.get('title', '')
                    })

            if ids:
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )

        # چاپ اطلاعات نهایی
        count = collection.count()
        print(f"پایگاه دانش با {count} امبدینگ ایجاد شد.")

        # ذخیره اطلاعات پایگاه دانش
        db_info = {
            'collection_name': collection_name,
            'total_documents': count,
            'model': model_info['model_name'],
            'embedding_dimension': model_info['embedding_dimension'],
            'created_at': model_info.get('created_at', '')
        }

        db_info_file = os.path.join(self.db_directory, 'db_info.json')
        with open(db_info_file, 'w', encoding='utf-8') as f:
            json.dump(db_info, f, ensure_ascii=False, indent=2)

        print(f"اطلاعات پایگاه دانش در {db_info_file} ذخیره شدند.")

        return count

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='ایجاد پایگاه دانش با استفاده از امبدینگ‌ها')
    parser.add_argument('--embeddings_dir', default='embeddings',
                        help='پوشه حاوی امبدینگ‌های ذخیره شده')
    parser.add_argument('--db_dir', default='knowledge_base',
                        help='پوشه برای ذخیره پایگاه دانش')
    parser.add_argument('--collection', default='website_data',
                        help='نام کالکشن در پایگاه دانش')

    args = parser.parse_args()

    creator = KnowledgeBaseCreator(db_directory=args.db_dir)
    creator.create_knowledge_base(embeddings_dir=args.embeddings_dir, collection_name=args.collection)