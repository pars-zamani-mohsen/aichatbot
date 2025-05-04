# test_knowledge_base.py (نسخه اصلاح شده)

import chromadb
import json
import os
import argparse
from sentence_transformers import SentenceTransformer

class KnowledgeBaseTester:
    def __init__(self, db_directory="knowledge_base", collection_name="website_data"):
        """مقداردهی اولیه تست‌کننده پایگاه دانش"""

        # خواندن اطلاعات پایگاه دانش
        db_info_file = os.path.join(db_directory, 'db_info.json')
        if os.path.exists(db_info_file):
            with open(db_info_file, 'r', encoding='utf-8') as f:
                self.db_info = json.load(f)
            print(f"اطلاعات پایگاه دانش بارگذاری شد: {self.db_info}")
        else:
            self.db_info = {'model': 'all-MiniLM-L6-v2'}
            print("هشدار: فایل اطلاعات پایگاه دانش یافت نشد. از مدل پیش‌فرض استفاده می‌شود.")

        # بارگذاری مدل امبدینگ
        self.model_name = self.db_info.get('model', 'all-MiniLM-L6-v2')
        print(f"بارگذاری مدل امبدینگ {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)

        # اتصال به پایگاه دانش
        self.client = chromadb.PersistentClient(path=db_directory)

        # بررسی وجود کالکشن
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"کالکشن {collection_name} با موفقیت بارگذاری شد.")
        except Exception as e:
            print(f"خطا در بارگذاری کالکشن: {e}")
            raise

    def search(self, query, n_results=5):
        """جستجو در پایگاه دانش با استفاده از پرس‌وجو متنی"""

        # تبدیل پرس‌وجو به امبدینگ
        query_embedding = self.model.encode(query).tolist()

        # انجام جستجو
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        return results

    def test_search(self, queries, n_results=3):
        """اجرای چند پرس‌وجوی نمونه برای بررسی عملکرد پایگاه دانش"""

        print(f"\n=== تست جستجو در پایگاه دانش با {len(queries)} پرس‌وجو ===\n")

        for i, query in enumerate(queries):
            print(f"\nپرس‌وجوی {i+1}: «{query}»")
            print("-" * 50)

            results = self.search(query, n_results=n_results)

            if results and results["documents"]:
                for j, (doc, meta, dist) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    print(f"\nنتیجه {j+1} (فاصله: {dist:.4f}):")
                    print(f"عنوان: {meta.get('title', 'بدون عنوان')}")
                    print(f"URL: {meta.get('url', 'بدون URL')}")
                    print(f"متن: {doc[:200]}..." if len(doc) > 200 else f"متن: {doc}")
            else:
                print("هیچ نتیجه‌ای یافت نشد.")

def read_queries_from_file(filename):
    """خواندن پرس‌وجوها از فایل متنی"""
    queries = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    queries.append(line)
        return queries
    except Exception as e:
        print(f"خطا در خواندن فایل پرس‌وجوها: {e}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='تست پایگاه دانش')
    parser.add_argument('--db_dir', default='knowledge_base', help='مسیر پایگاه دانش')
    parser.add_argument('--collection', default='website_data', help='نام کالکشن')
    parser.add_argument('--queries', help='مسیر فایل حاوی پرس‌وجوها (هر پرس‌وجو در یک خط)')
    parser.add_argument('--n_results', type=int, default=3, help='تعداد نتایج برای هر پرس‌وجو')

    args = parser.parse_args()

    # پرس‌وجوهای پیش‌فرض
    default_queries = [
        "چگونه می‌توانم حساب کاربری ایجاد کنم؟",
        "محصولات پرفروش",
        "سیاست بازگشت کالا",
        "راه‌های ارتباط با پشتیبانی",
        "ساعات کاری فروشگاه"
    ]

    # خواندن پرس‌وجوها از فایل اگر مشخص شده باشد
    if args.queries and os.path.exists(args.queries):
        queries = read_queries_from_file(args.queries)
        if not queries:
            print("هیچ پرس‌وجویی از فایل خوانده نشد. از پرس‌وجوهای پیش‌فرض استفاده می‌شود.")
            queries = default_queries
    else:
        queries = default_queries

    # ایجاد نمونه تست‌کننده و اجرای جستجوهای نمونه
    tester = KnowledgeBaseTester(db_directory=args.db_dir, collection_name=args.collection)
    tester.test_search(queries, n_results=args.n_results)