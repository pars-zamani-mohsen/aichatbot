from pathlib import Path
import chromadb
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from .database.database import get_db
from .database.models import Website
from .schemas import ChatRequest
from .core.config import Settings, CHROMA_BASE_DIR

app = FastAPI()
settings = Settings()

@app.post("/api/chat")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """پردازش پیام کاربر و پاسخ با استفاده از knowledge base"""
    try:
        # دریافت اطلاعات سایت
        website = db.query(Website).filter(Website.id == chat_request.website_id).first()
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
            
        # بررسی وجود collection_name
        if not website.collection_name:
            raise HTTPException(status_code=400, detail="کالکشن برای این وب‌سایت ایجاد نشده است")
            
        # تنظیم مسیر صحیح برای ChromaDB
        kb_dir = Path("/var/www/html/ai/backend/knowledge_base") / website.collection_name
        logger.info(f"Using knowledge base directory: {kb_dir}")
        
        if not kb_dir.exists():
            raise HTTPException(status_code=400, detail=f"پوشه knowledge base برای این وب‌سایت یافت نشد: {kb_dir}")
            
        # بررسی وجود فایل chroma.sqlite3
        chroma_db_file = kb_dir / "chroma.sqlite3"
        logger.info(f"Checking for chroma.sqlite3 at: {chroma_db_file}")
        
        if not chroma_db_file.exists():
            raise HTTPException(status_code=400, detail=f"فایل chroma.sqlite3 در مسیر {kb_dir} یافت نشد")
            
        # ایجاد کلاینت ChromaDB با مسیر صحیح
        try:
            client = chromadb.PersistentClient(path=str(kb_dir))
            logger.info(f"ChromaDB client created with path: {kb_dir}")
        except Exception as e:
            logger.error(f"خطا در ایجاد کلاینت ChromaDB: {str(e)}")
            raise HTTPException(status_code=500, detail=f"خطا در اتصال به ChromaDB: {str(e)}")
        
        # بررسی وجود کالکشن
        try:
            collections = client.list_collections()
            collection_names = [c.name for c in collections]
            logger.info(f"Available collections in {kb_dir}: {collection_names}")
            
            if website.collection_name not in collection_names:
                raise HTTPException(status_code=400, detail=f"کالکشن {website.collection_name} در ChromaDB یافت نشد")
            
            collection = client.get_collection(name=website.collection_name)
            logger.info(f"Collection {website.collection_name} retrieved successfully")
        except Exception as e:
            logger.error(f"خطا در بررسی کالکشن‌ها: {str(e)}")
            raise HTTPException(status_code=500, detail=f"خطا در بررسی کالکشن‌ها: {str(e)}")
        
        # جستجو در کالکشن
        try:
            results = collection.query(
                query_texts=[chat_request.message],
                n_results=5
            )
            logger.info("Search completed successfully")
        except Exception as e:
            logger.error(f"خطا در جستجوی کالکشن: {str(e)}")
            raise HTTPException(status_code=500, detail=f"خطا در جستجو: {str(e)}")
        
        # آماده‌سازی پاسخ
        response = {
            "message": "نتایج جستجو:",
            "results": results
        }
        
        return response
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"خطا در پردازش پیام: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
