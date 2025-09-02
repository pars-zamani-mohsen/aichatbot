import chromadb
from pathlib import Path

# تعریف مسیر پایه
BASE_DIR = Path("/var/www/html/ai/backend")
collection_name = "parsicanada.com"

# ایجاد کلاینت ChromaDB
client = chromadb.PersistentClient(path=str(BASE_DIR / "knowledge_base" / collection_name))

# دریافت لیست کالکشن‌ها
collections = client.list_collections()
print(f"کالکشن‌های موجود: {collections}")

# بررسی وجود کالکشن
try:
    collection = client.get_collection(name=collection_name)
    print(f"کالکشن {collection_name} یافت شد.")
    print(f"تعداد اسناد: {collection.count()}")
except Exception as e:
    print(f"خطا در دریافت کالکشن: {str(e)}") 