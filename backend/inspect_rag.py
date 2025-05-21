import sys
import chromadb
from settings import DB_DIRECTORY
from models.customer import CustomerManager

def inspect_collection(customer_id):
    cm = CustomerManager()
    customer = cm.get_customer(customer_id)
    if not customer:
        print("Customer not found.")
        return

    collection_name = customer["collection_name"]
    client = chromadb.PersistentClient(path=DB_DIRECTORY)
    collection = client.get_or_create_collection(collection_name)

    # دریافت همه اسناد (ممکن است زیاد باشد، پس فقط 5 تای اول را نمایش می‌دهیم)
    results = collection.get()
    docs = results.get("documents", [])
    metas = results.get("metadatas", [])

    print(f"Collection name: {collection_name}")
    print(f"Total documents: {len(docs)}")
    print("Sample documents:")
    for i, doc in enumerate(docs[:5]):
        print(f"\n--- Document {i+1} ---")
        print(doc)
        if metas and i < len(metas):
            print("Meta:", metas[i])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_rag.py <customer_id>")
    else:
        inspect_collection(sys.argv[1])
