from datetime import datetime
import uuid
from typing import Dict, Optional
import chromadb
from settings import DB_DIRECTORY

class CustomerManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DB_DIRECTORY)

    def update_crawl_status(self, customer_id: str, status: str, crawled_at: str = None):
        """Update customer crawl status"""
        try:
            metadata_collection = self.client.get_collection("customers_metadata")
            customer = self.get_customer(customer_id)
            if customer:
                customer["crawl_status"] = status
                customer["crawled_at"] = crawled_at
                metadata_collection.update(
                    ids=[customer_id],
                    documents=[str(customer)],
                    metadatas=[{"domain": customer["domain"]}]
                )
        except Exception as e:
            print(f"Error updating crawl status: {e}")

    def create_customer(self, domain: str) -> Dict:
        """ایجاد مشتری جدید"""
        customer_id = str(uuid.uuid4())
        collection_name = f"site_{customer_id}"

        # ایجاد کالکشن اختصاصی برای وب‌سایت
        self.client.create_collection(name=collection_name)

        customer_data = {
            "customer_id": customer_id,
            "domain": domain,
            "api_key": self._generate_api_key(),
            "collection_name": collection_name,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "crawl_status": "pending",  # وضعیت‌های ممکن: pending, running, completed, failed
            "crawled_at": None
        }

        # ذخیره اطلاعات مشتری
        metadata_collection = self.client.get_or_create_collection("customers_metadata")
        metadata_collection.add(
            documents=[str(customer_data)],
            ids=[customer_id],
            metadatas=[{"domain": domain}]
        )

        return customer_data

    def _generate_api_key(self) -> str:
        """تولید کلید API منحصر به فرد"""
        return f"sk_site_{uuid.uuid4().hex}"

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """دریافت اطلاعات مشتری"""
        try:
            metadata_collection = self.client.get_collection("customers_metadata")
            result = metadata_collection.get(ids=[customer_id])
            if result and result['documents']:
                return eval(result['documents'][0])
            return None
        except Exception:
            return None

    def validate_api_key(self, api_key: str) -> Optional[str]:
        """اعتبارسنجی کلید API و برگرداندن شناسه مشتری"""
        metadata_collection = self.client.get_collection("customers_metadata")
        results = metadata_collection.get()

        for doc in results['documents']:
            customer_data = eval(doc)
            if customer_data.get('api_key') == api_key:
                return customer_data['customer_id']
        return None