from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
from sqlalchemy.orm import Session
from ..services.pipeline import WebCrawlerPipeline, EmbeddingPipeline
from ..database.models import Website
from ..database.database import get_db
from . import schemas
import logging
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path
import pandas as pd
from ..database.models import User
from .auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

async def process_website_background(website_id: int, db: Session):
    """پردازش وب‌سایت در پس‌زمینه"""
    try:
        # دریافت اطلاعات سایت
        website = db.query(Website).filter(Website.id == website_id).first()
        if not website:
            logger.error(f"سایت با شناسه {website_id} یافت نشد")
            return
            
        # به‌روزرسانی وضعیت و collection_name
        website.status = "crawling"
        website.collection_name = website.domain  # تنظیم collection_name قبل از شروع کراولینگ
        db.commit()
        
        try:
            # اجرای فاز 1: کراول
            crawler = WebCrawlerPipeline(website.url)
            if not await crawler.run_async():
                raise Exception("خطا در کراول کردن سایت")
                
            # به‌روزرسانی وضعیت
            website.status = "processing"
            db.commit()
            
            # اجرای فاز 2: امبدینگ
            embedder = EmbeddingPipeline(website.domain)
            if not embedder.run():
                raise Exception("خطا در ایجاد امبدینگ‌ها")
                
            # به‌روزرسانی وضعیت
            website.status = "ready"
            website.crawl_info = {
                'total_pages': len(crawler.data),
                'crawled_at': datetime.now().isoformat()
            }
            db.commit()
            
        except Exception as e:
            logger.error(f"خطا در پردازش سایت {website.url}: {str(e)}")
            website.status = "error"
            website.error_message = str(e)
            db.commit()
            
    except Exception as e:
        logger.error(f"خطای کلی در پردازش سایت: {str(e)}")

@router.post("/websites/crawl", response_model=schemas.Website)
async def crawl_website(
    website: schemas.WebsiteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """کراول کردن وب‌سایت و ذخیره داده‌ها"""
    try:
        # ایجاد رکورد وب‌سایت
        website_record = Website(
            url=str(website.url),
            domain=urlparse(str(website.url)).netloc,
            status="pending",
            owner_id=current_user.id
        )
        db.add(website_record)
        db.commit()
        db.refresh(website_record)
        
        # شروع پردازش در پس‌زمینه
        background_tasks.add_task(process_website_background, website_record.id, db)
        
        return website_record
        
    except Exception as e:
        logger.error(f"خطا در شروع کراول وب‌سایت: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{website_id}", response_model=schemas.Website)
async def get_website(website_id: int, db: Session = Depends(get_db)):
    """دریافت اطلاعات یک وب‌سایت"""
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
    return website

@router.get("/stats/{website_id}")
async def get_website_stats(website_id: int, db: Session = Depends(get_db)):
    """دریافت آمار کراول یک وب‌سایت"""
    try:
        website = db.query(Website).filter(Website.id == website_id).first()
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
            
        # خواندن فایل CSV
        base_dir = Path(__file__).parent.parent.parent
        csv_path = base_dir / "processed_data" / website.domain / "processed_data.csv"
        
        if not csv_path.exists():
            return {
                "website_id": website_id,
                "domain": website.domain,
                "status": website.status,
                "total_pages": 0,
                "message": "هنوز داده‌ای کراول نشده است"
            }
            
        # خواندن تعداد ردیف‌های CSV
        df = pd.read_csv(csv_path)
        total_pages = len(df)
        
        return {
            "website_id": website_id,
            "domain": website.domain,
            "status": website.status,
            "total_pages": total_pages,
            "crawl_info": website.crawl_info
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت آمار: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[schemas.Website])
async def list_websites(db: Session = Depends(get_db)):
    """دریافت لیست همه وب‌سایت‌ها"""
    return db.query(Website).all() 