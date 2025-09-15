from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
from sqlalchemy.orm import Session
from ..services.pipeline import WebCrawlerPipeline, EmbeddingPipeline
from ..services.domain_verification import DomainVerificationService
from ..database.models import Website, Chat
from ..database.database import get_db
from . import schemas
import logging
import json
import tempfile
import os
import io
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path
try:
    import pandas as pd
except ImportError:
    pd = None
from ..database.models import User
from .auth import get_current_user
from ..services.notification_service import NotificationService
from ..services.system_settings_service import SystemSettingsService
from ..config import settings

def verify_website_ownership(website_id: int, user_id: int, db: Session) -> Website:
    """بررسی مالکیت وب‌سایت (جداسازی tenant)"""
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.owner_id == user_id
    ).first()
    
    if not website:
        raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
    
    return website

def validate_crawl_settings(settings: dict) -> dict:
    """اعتبارسنجی تنظیمات کراولینگ"""
    validated = {}
    
    # اعتبارسنجی max_pages
    if 'max_pages' in settings:
        max_pages = settings['max_pages']
        if not isinstance(max_pages, int) or max_pages < 1 or max_pages > 1000:
            raise HTTPException(
                status_code=400, 
                detail="حداکثر تعداد صفحات باید بین 1 تا 1000 باشد"
            )
        validated['max_pages'] = max_pages
    
    # اعتبارسنجی max_depth
    if 'max_depth' in settings:
        max_depth = settings['max_depth']
        if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 10:
            raise HTTPException(
                status_code=400, 
                detail="حداکثر عمق باید بین 1 تا 10 باشد"
            )
        validated['max_depth'] = max_depth
    
    # اعتبارسنجی delay
    if 'delay' in settings:
        delay = settings['delay']
        if not isinstance(delay, (int, float)) or delay < 0.1 or delay > 60:
            raise HTTPException(
                status_code=400, 
                detail="تأخیر باید بین 0.1 تا 60 ثانیه باشد"
            )
        validated['delay'] = float(delay)
    
    # اعتبارسنجی respect_robots
    if 'respect_robots' in settings:
        validated['respect_robots'] = bool(settings['respect_robots'])
    
    # اعتبارسنجی user_agent
    if 'user_agent' in settings:
        user_agent = settings['user_agent']
        if not isinstance(user_agent, str) or len(user_agent) > 200:
            raise HTTPException(
                status_code=400, 
                detail="User Agent باید رشته‌ای با حداکثر 200 کاراکتر باشد"
            )
        validated['user_agent'] = user_agent
    
    return validated

def get_links_count(links_data) -> int:
    """محاسبه تعداد لینک‌ها از داده‌های مختلف"""
    try:
        if isinstance(links_data, list):
            return len(links_data)
        elif isinstance(links_data, str):
            if links_data == '' or links_data == '[]':
                return 0
            # تلاش برای parse کردن JSON string
            try:
                parsed_links = json.loads(links_data)
                if isinstance(parsed_links, list):
                    return len(parsed_links)
            except (json.JSONDecodeError, ValueError):
                pass
            # اگر JSON نباشد، تعداد کاماها را بشماریم (تقریبی)
            return links_data.count(',') + 1 if links_data else 0
        else:
            return 0
    except Exception:
        return 0

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
            # دریافت تنظیمات کراولر سیستم
            crawler_settings = SystemSettingsService.get_crawler_settings(db)
            
            # ترکیب تنظیمات سیستم با تنظیمات اختصاصی وب‌سایت
            crawl_settings = website.crawl_settings or {}
            system_crawl_settings = {
                'max_pages': crawler_settings.get('maxPagesPerSite', 100),
                'crawl_delay': crawler_settings.get('crawlDelay', 1),
                'respect_robots_txt': crawler_settings.get('respectRobotsTxt', True),
                'user_agent': crawler_settings.get('userAgent', 'RAG-Chatbot-Crawler/1.0')
            }
            
            # تنظیمات اختصاصی اولویت دارند
            final_crawl_settings = {**system_crawl_settings, **crawl_settings}
            
            # اجرای فاز 1: کراول با تنظیمات ترکیبی
            crawler = WebCrawlerPipeline(website.url, final_crawl_settings)
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
            
            # ارسال اعلان تکمیل کراولینگ
            NotificationService.notify_website_update(
                db=db,
                user_id=website.owner_id,
                website_name=website.name or website.url,
                update_type="crawl_completed"
            )
            
        except Exception as e:
            logger.error(f"خطا در پردازش سایت {website.url}: {str(e)}")
            website.status = "error"
            website.error_message = str(e)
            db.commit()
            
            # ارسال اعلان خطای کراولینگ
            NotificationService.notify_website_update(
                db=db,
                user_id=website.owner_id,
                website_name=website.name or website.url,
                update_type="crawl_failed"
            )
            
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
            name=website.name,  # ذخیره نام سایت
            status="pending",
            owner_id=current_user.id
        )
        db.add(website_record)
        db.commit()
        db.refresh(website_record)
        
        # استفاده از صف کراولینگ
        from app.services.crawler_queue import crawler_queue
        
        task = crawler_queue.add_crawl_task(
            website_id=website_record.id,
            url=str(website.url),
            domain=website_record.domain,
            owner_id=current_user.id,
            priority=1
        )
        
        logger.info(f"Added crawl task to queue: {task.website_id}")
        
        return website_record
        
    except Exception as e:
        logger.error(f"خطا در شروع کراول وب‌سایت: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{website_id}/delete")
async def delete_website(
    website_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """حذف وب‌سایت توسط مالک آن"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # حذف چت‌های مربوطه
        db.query(Chat).filter(Chat.website_id == website_id).delete()
        
        # حذف وب‌سایت
        db.delete(website)
        db.commit()
        
        return {"message": "وب‌سایت با موفقیت حذف شد"}
        
    except Exception as e:
        logger.error(f"خطا در حذف وب‌سایت: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{website_id}", response_model=schemas.Website)
async def get_website(
    website_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت اطلاعات یک وب‌سایت"""
    # بررسی مالکیت وب‌سایت (جداسازی tenant)
    website = verify_website_ownership(website_id, current_user.id, db)
    return website

@router.get("/stats/{website_id}")
async def get_website_stats(
    website_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت آمار کراول یک وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
            
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
async def list_websites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت لیست همه وب‌سایت‌ها"""
    return db.query(Website).filter(Website.owner_id == current_user.id).all()

@router.post("/{website_id}/generate-widget-key")
async def generate_widget_key(
    website_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تولید کلید عمومی برای ویجت"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # بررسی آماده بودن وب‌سایت
        if website.status != "ready":
            raise HTTPException(status_code=400, detail="وب‌سایت آماده نیست")
        
        # تولید کلید عمومی
        import hashlib
        import time
        public_key = hashlib.md5(f"{website_id}_{website.domain}_{int(time.time())}".encode()).hexdigest()
        
        # ذخیره کلید در دیتابیس
        website.public_key = public_key
        db.commit()
        
        return {
            "website_id": website_id,
            "public_key": public_key,
            "message": "کلید عمومی با موفقیت تولید شد"
        }
        
    except Exception as e:
        logger.error(f"خطا در تولید کلید ویجت: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{website_id}/verify-domain")
async def verify_domain_ownership(
    website_id: int,
    verification_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تأیید مالکیت دامنه"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        method = verification_data.get("method", "html")
        token = website.verification_token
        
        if not token:
            # تولید توکن جدید
            token = DomainVerificationService.generate_verification_token()
            website.verification_token = token
            db.commit()
        
        # تأیید مالکیت
        is_valid, message = DomainVerificationService.verify_domain_ownership(
            website.domain, token, method
        )
        
        if is_valid:
            website.domain_verified = True
            db.commit()
        
        return {
            "website_id": website_id,
            "domain": website.domain,
            "method": method,
            "verified": is_valid,
            "message": message,
            "token": token
        }
        
    except Exception as e:
        logger.error(f"خطا در تأیید مالکیت دامنه: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{website_id}/verification-instructions")
async def get_verification_instructions(
    website_id: int,
    method: str = "html",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت دستورالعمل‌های تأیید دامنه"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # تولید یا دریافت توکن
        if not website.verification_token:
            token = DomainVerificationService.generate_verification_token()
            website.verification_token = token
            db.commit()
        else:
            token = website.verification_token
        
        # دریافت دستورالعمل‌ها
        instructions = DomainVerificationService.get_verification_instructions(
            website.domain, token, method
        )
        
        return {
            "website_id": website_id,
            "domain": website.domain,
            "method": method,
            "token": token,
            "instructions": instructions
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت دستورالعمل‌های تأیید: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{website_id}/crawl-settings")
async def update_crawl_settings(
    website_id: int,
    settings: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """به‌روزرسانی تنظیمات کراولینگ وب‌سایت (فقط برای ادمین‌ها)"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="تنظیمات کراولینگ فقط برای ادمین‌ها قابل دسترس است"
            )
        
        # بررسی وجود وب‌سایت
        website = db.query(Website).filter(Website.id == website_id).first()
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
        
        # اعتبارسنجی تنظیمات
        validated_settings = validate_crawl_settings(settings)
        
        # به‌روزرسانی تنظیمات
        website.crawl_settings = validated_settings
        db.commit()
        
        return {
            "website_id": website_id,
            "crawl_settings": validated_settings,
            "message": "تنظیمات کراولینگ با موفقیت به‌روزرسانی شد"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در به‌روزرسانی تنظیمات کراولینگ: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{website_id}/crawl-settings")
async def get_crawl_settings(
    website_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت تنظیمات کراولینگ وب‌سایت (فقط برای ادمین‌ها)"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="تنظیمات کراولینگ فقط برای ادمین‌ها قابل دسترس است"
            )
        
        # بررسی وجود وب‌سایت
        website = db.query(Website).filter(Website.id == website_id).first()
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
        
        return {
            "website_id": website_id,
            "crawl_settings": website.crawl_settings or {},
            "default_settings": {
                "max_pages": 100,
                "max_depth": 3,
                "delay": 1,
                "respect_robots": True,
                "user_agent": "RAG-Crawler/1.0"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در دریافت تنظیمات کراولینگ: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{website_id}/pages")
async def get_website_pages(
    website_id: int,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت لیست صفحات کراول شده یک وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # خواندن فایل CSV
        base_dir = Path(__file__).parent.parent.parent
        csv_path = base_dir / "processed_data" / website.domain / "processed_data.csv"
        
        if not csv_path.exists():
            return {
                "pages": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "message": "هنوز صفحه‌ای کراول نشده است"
            }
        
        # خواندن داده‌ها
        if pd is None:
            raise HTTPException(status_code=500, detail="pandas در دسترس نیست")
        
        df = pd.read_csv(csv_path)
        total_pages = len(df)
        
        # صفحه‌بندی
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        df_page = df.iloc[start_idx:end_idx]
        
        pages = []
        for _, row in df_page.iterrows():
            pages.append({
                "url": row.get('url', ''),
                "title": row.get('title', ''),
                "text": row.get('text', ''),  # کل متن برای ویرایش
                "text_preview": row.get('text', '')[:200] + "..." if len(str(row.get('text', ''))) > 200 else row.get('text', ''),
                "links_count": get_links_count(row.get('links', []))
            })
        
        return {
            "pages": pages,
            "total": total_pages,
            "page": page,
            "limit": limit,
            "total_pages": (total_pages + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت صفحات: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{website_id}/re-crawl")
async def re_crawl_website(
    website_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """شروع مجدد کراولینگ وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # بررسی وضعیت
        if website.status == "crawling":
            raise HTTPException(status_code=400, detail="وب‌سایت در حال کراولینگ است")
        
        # به‌روزرسانی وضعیت
        website.status = "pending"
        website.error_message = None
        db.commit()
        
        # شروع کراولینگ مجدد
        background_tasks.add_task(process_website_background, website_id, db)
        
        return {
            "website_id": website_id,
            "message": "کراولینگ مجدد شروع شد",
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"خطا در شروع کراولینگ مجدد: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{website_id}/pages/{page_url:path}")
async def delete_website_page(
    website_id: int,
    page_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """حذف یک صفحه از وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # خواندن فایل CSV
        base_dir = Path(__file__).parent.parent.parent
        csv_path = base_dir / "processed_data" / website.domain / "processed_data.csv"
        
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="فایل داده یافت نشد")
        
        # خواندن و حذف صفحه
        if pd is None:
            raise HTTPException(status_code=500, detail="pandas در دسترس نیست")
        
        df = pd.read_csv(csv_path)
        original_count = len(df)
        df = df[df['url'] != page_url]
        
        if len(df) == original_count:
            raise HTTPException(status_code=404, detail="صفحه یافت نشد")
        
        # ذخیره مجدد
        df.to_csv(csv_path, index=False)
        
        return {
            "website_id": website_id,
            "page_url": page_url,
            "message": "صفحه با موفقیت حذف شد",
            "remaining_pages": len(df)
        }
        
    except Exception as e:
        logger.error(f"خطا در حذف صفحه: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{website_id}/pages/{page_url:path}")
async def update_website_page(
    website_id: int,
    page_url: str,
    page_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ویرایش محتوای یک صفحه از وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # خواندن فایل CSV
        base_dir = Path(__file__).parent.parent.parent
        csv_path = base_dir / "processed_data" / website.domain / "processed_data.csv"
        
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="فایل داده یافت نشد")
        
        # خواندن و ویرایش صفحه
        if pd is None:
            raise HTTPException(status_code=500, detail="pandas در دسترس نیست")
        
        df = pd.read_csv(csv_path)
        
        # پیدا کردن صفحه
        page_index = df[df['url'] == page_url].index
        if len(page_index) == 0:
            raise HTTPException(status_code=404, detail="صفحه یافت نشد")
        
        # به‌روزرسانی داده‌ها
        if 'title' in page_data:
            df.at[page_index[0], 'title'] = page_data['title']
        if 'text' in page_data:
            df.at[page_index[0], 'text'] = page_data['text']
        
        # ذخیره مجدد
        df.to_csv(csv_path, index=False)
        
        # به‌روزرسانی امبدینگ‌ها اگر متن تغییر کرده
        if 'text' in page_data:
            try:
                from ..services.embedding import EmbeddingService
                embedding_service = EmbeddingService()
                
                # خواندن امبدینگ‌های موجود
                embeddings_path = base_dir / "processed_data" / website.domain / "embeddings.json"
                if embeddings_path.exists():
                    with open(embeddings_path, 'r') as f:
                        embeddings = json.load(f)
                    
                    # تولید امبدینگ جدید
                    new_embedding = embedding_service.generate_embedding(page_data['text'])
                    embeddings[str(page_index[0])] = new_embedding.tolist()
                    
                    # ذخیره امبدینگ‌های به‌روزرسانی شده
                    with open(embeddings_path, 'w') as f:
                        json.dump(embeddings, f)
                    
                    # به‌روزرسانی ChromaDB
                    from ..services.rag import RAGService
                    rag_service = RAGService(collection_name=website.domain)
                    rag_service.update_document(
                        document_id=str(page_index[0]),
                        text=page_data['text'],
                        metadata={'url': page_url, 'title': page_data.get('title', '')}
                    )
                    
            except Exception as e:
                logger.warning(f"خطا در به‌روزرسانی امبدینگ: {str(e)}")
        
        return {
            "website_id": website_id,
            "page_url": page_url,
            "message": "صفحه با موفقیت به‌روزرسانی شد",
            "updated_fields": list(page_data.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در ویرایش صفحه: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{website_id}/pages")
async def add_manual_page(
    website_id: int,
    page_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """اضافه کردن صفحه جدید به صورت دستی"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # اعتبارسنجی داده‌ها
        required_fields = ['url', 'title', 'text']
        for field in required_fields:
            if field not in page_data or not page_data[field]:
                raise HTTPException(status_code=400, detail=f"فیلد {field} الزامی است")
        
        # خواندن فایل CSV
        base_dir = Path(__file__).parent.parent.parent
        csv_path = base_dir / "processed_data" / website.domain / "processed_data.csv"
        
        # ایجاد پوشه اگر وجود ندارد
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        if pd is None:
            raise HTTPException(status_code=500, detail="pandas در دسترس نیست")
        
        # خواندن یا ایجاد DataFrame
        if csv_path.exists():
            df = pd.read_csv(csv_path)
        else:
            df = pd.DataFrame(columns=['url', 'title', 'text', 'links'])
        
        # بررسی تکراری نبودن URL
        if page_data['url'] in df['url'].values:
            raise HTTPException(status_code=400, detail="این URL قبلاً اضافه شده است")
        
        # اضافه کردن صفحه جدید
        new_page = {
            'url': page_data['url'],
            'title': page_data['title'],
            'text': page_data['text'],
            'links': page_data.get('links', [])
        }
        
        df = pd.concat([df, pd.DataFrame([new_page])], ignore_index=True)
        df.to_csv(csv_path, index=False)
        
        # تولید امبدینگ برای صفحه جدید
        try:
            from ..services.embedding import EmbeddingService
            embedding_service = EmbeddingService()
            
            # خواندن امبدینگ‌های موجود
            embeddings_path = base_dir / "processed_data" / website.domain / "embeddings.json"
            embeddings = []
            if embeddings_path.exists():
                with open(embeddings_path, 'r') as f:
                    embeddings = json.load(f)
            
            # تولید امبدینگ جدید
            new_embedding = embedding_service.generate_embedding(page_data['text'])
            embeddings.append(new_embedding.tolist())
            
            # ذخیره امبدینگ‌ها
            with open(embeddings_path, 'w') as f:
                json.dump(embeddings, f)
            
            # اضافه کردن به ChromaDB
            from ..services.rag import RAGService
            rag_service = RAGService(collection_name=website.domain)
            rag_service.add_document(
                text=page_data['text'],
                metadata={'url': page_data['url'], 'title': page_data['title']}
            )
            
        except Exception as e:
            logger.warning(f"خطا در تولید امبدینگ: {str(e)}")
        
        return {
            "website_id": website_id,
            "page_url": page_data['url'],
            "message": "صفحه جدید با موفقیت اضافه شد",
            "total_pages": len(df)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در اضافه کردن صفحه: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{website_id}/pages/search")
async def search_website_pages(
    website_id: int,
    query: str = "",
    filter_by: str = "all",  # all, title, text
    sort_by: str = "title",  # title, url, links_count
    sort_order: str = "asc",  # asc, desc
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """جستجو و فیلتر صفحات وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # خواندن فایل CSV
        base_dir = Path(__file__).parent.parent.parent
        csv_path = base_dir / "processed_data" / website.domain / "processed_data.csv"
        
        if not csv_path.exists():
            return {
                "pages": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "message": "هنوز صفحه‌ای کراول نشده است"
            }
        
        if pd is None:
            raise HTTPException(status_code=500, detail="pandas در دسترس نیست")
        
        df = pd.read_csv(csv_path)
        
        # جستجو
        if query:
            if filter_by == "title":
                mask = df['title'].str.contains(query, case=False, na=False)
            elif filter_by == "text":
                mask = df['text'].str.contains(query, case=False, na=False)
            else:  # all
                mask = (df['title'].str.contains(query, case=False, na=False) | 
                       df['text'].str.contains(query, case=False, na=False))
            df = df[mask]
        
        # مرتب‌سازی
        if sort_by == "title":
            df = df.sort_values('title', ascending=(sort_order == "asc"))
        elif sort_by == "url":
            df = df.sort_values('url', ascending=(sort_order == "asc"))
        elif sort_by == "links_count":
            df['links_count'] = df['links'].apply(lambda x: len(x) if isinstance(x, list) else 0)
            df = df.sort_values('links_count', ascending=(sort_order == "asc"))
        
        total_pages = len(df)
        
        # صفحه‌بندی
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        df_page = df.iloc[start_idx:end_idx]
        
        pages = []
        for _, row in df_page.iterrows():
            pages.append({
                "url": row.get('url', ''),
                "title": row.get('title', ''),
                "text": row.get('text', ''),  # کل متن برای ویرایش
                "text_preview": row.get('text', '')[:200] + "..." if len(str(row.get('text', ''))) > 200 else row.get('text', ''),
                "links_count": get_links_count(row.get('links', []))
            })
        
        return {
            "pages": pages,
            "total": total_pages,
            "page": page,
            "limit": limit,
            "total_pages": (total_pages + limit - 1) // limit,
            "query": query,
            "filter_by": filter_by,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در جستجوی صفحات: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{website_id}/export")
async def export_website_data(
    website_id: int,
    format: str = "csv",  # csv, json
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """صادرات داده‌های وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # خواندن فایل CSV
        base_dir = Path(__file__).parent.parent.parent
        csv_path = base_dir / "processed_data" / website.domain / "processed_data.csv"
        
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="داده‌ای برای صادرات یافت نشد")
        
        if pd is None:
            raise HTTPException(status_code=500, detail="pandas در دسترس نیست")
        
        df = pd.read_csv(csv_path)
        
        if format == "json":
            data = df.to_dict('records')
            return {
                "website_id": website_id,
                "domain": website.domain,
                "format": "json",
                "data": data,
                "total_pages": len(df),
                "exported_at": datetime.now().isoformat()
            }
        else:  # csv
            # ایجاد فایل موقت
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
            df.to_csv(temp_file.name, index=False)
            temp_file.close()
            
            # خواندن محتوای فایل
            with open(temp_file.name, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            # حذف فایل موقت
            os.unlink(temp_file.name)
            
            return {
                "website_id": website_id,
                "domain": website.domain,
                "format": "csv",
                "data": csv_content,
                "total_pages": len(df),
                "exported_at": datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در صادرات داده‌ها: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{website_id}/import")
async def import_website_data(
    website_id: int,
    import_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """واردات داده‌های وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # اعتبارسنجی داده‌ها
        if 'format' not in import_data or 'data' not in import_data:
            raise HTTPException(status_code=400, detail="فرمت و داده الزامی است")
        
        if pd is None:
            raise HTTPException(status_code=500, detail="pandas در دسترس نیست")
        
        base_dir = Path(__file__).parent.parent.parent
        csv_path = base_dir / "processed_data" / website.domain / "processed_data.csv"
        
        # ایجاد پوشه اگر وجود ندارد
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # پردازش داده‌های وارداتی
        if import_data['format'] == 'json':
            df_import = pd.DataFrame(import_data['data'])
        elif import_data['format'] == 'csv':
            df_import = pd.read_csv(io.StringIO(import_data['data']))
        else:
            raise HTTPException(status_code=400, detail="فرمت پشتیبانی نمی‌شود")
        
        # اعتبارسنجی ستون‌های مورد نیاز
        required_columns = ['url', 'title', 'text']
        for col in required_columns:
            if col not in df_import.columns:
                raise HTTPException(status_code=400, detail=f"ستون {col} الزامی است")
        
        # خواندن داده‌های موجود
        if csv_path.exists():
            df_existing = pd.read_csv(csv_path)
            # ترکیب داده‌ها (حذف تکراری‌ها)
            df_combined = pd.concat([df_existing, df_import]).drop_duplicates(subset=['url'], keep='last')
        else:
            df_combined = df_import
        
        # ذخیره داده‌های ترکیبی
        df_combined.to_csv(csv_path, index=False)
        
        # تولید امبدینگ‌های جدید
        try:
            from ..services.embedding import EmbeddingService
            embedding_service = EmbeddingService()
            
            # تولید امبدینگ برای صفحات جدید
            new_embeddings = []
            for _, row in df_import.iterrows():
                embedding = embedding_service.generate_embedding(row['text'])
                new_embeddings.append(embedding.tolist())
            
            # ذخیره امبدینگ‌ها
            embeddings_path = base_dir / "processed_data" / website.domain / "embeddings.json"
            embeddings = []
            if embeddings_path.exists():
                with open(embeddings_path, 'r') as f:
                    embeddings = json.load(f)
            
            embeddings.extend(new_embeddings)
            
            with open(embeddings_path, 'w') as f:
                json.dump(embeddings, f)
            
        except Exception as e:
            logger.warning(f"خطا در تولید امبدینگ: {str(e)}")
        
        return {
            "website_id": website_id,
            "message": "داده‌ها با موفقیت وارد شدند",
            "imported_pages": len(df_import),
            "total_pages": len(df_combined)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در واردات داده‌ها: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{website_id}/rag-settings")
async def update_rag_settings(
    website_id: int,
    settings: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """به‌روزرسانی تنظیمات RAG وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # به‌روزرسانی تنظیمات
        website.rag_settings = settings
        db.commit()
        
        return {
            "website_id": website_id,
            "rag_settings": settings,
            "message": "تنظیمات RAG با موفقیت به‌روزرسانی شد"
        }
        
    except Exception as e:
        logger.error(f"خطا در به‌روزرسانی تنظیمات RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{website_id}/rag-settings")
async def get_rag_settings(
    website_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت تنظیمات RAG وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # دریافت تنظیمات RAG
        rag_settings = website.rag_settings or {}
        
        # تنظیمات پیش‌فرض
        default_settings = {
            "k": 5,
            "max_response_length": 500,
            "temperature": 0.7,
            "tone": "professional",
            "language": "persian",
            "chatbot_type": "openai",
            "include_sources": True,
            "max_context_length": 2000
        }
        
        # ترکیب تنظیمات موجود با پیش‌فرض
        final_settings = {**default_settings, **rag_settings}
        
        # بررسی و تصحیح مدل انتخاب شده
        system_settings = SystemSettingsService.get_all_settings(db)
        current_model = final_settings.get("chatbot_type", "openai")
        
        # بررسی اینکه مدل فعلی فعال است یا نه
        if (current_model == "openai" and not system_settings.get("enableOpenAI", True)) or \
           (current_model == "gemini" and not system_settings.get("enableGemini", True)) or \
           (current_model == "local" and not system_settings.get("enableLocal", False)):
            
            # پیدا کردن مدل جایگزین
            if system_settings.get("enableOpenAI", True):
                final_settings["chatbot_type"] = "openai"
            elif system_settings.get("enableGemini", True):
                final_settings["chatbot_type"] = "gemini"
            elif system_settings.get("enableLocal", False):
                final_settings["chatbot_type"] = "local"
            
            # ذخیره تنظیمات تصحیح شده
            website.rag_settings = final_settings
            db.commit()
            
            if settings.DEBUG_MODE:
                logger.info(f"Website {website_id} chatbot type corrected from {current_model} to {final_settings['chatbot_type']}")
        
        return {
            "website_id": website_id,
            "rag_settings": final_settings,
            "default_settings": default_settings
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت تنظیمات RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

 