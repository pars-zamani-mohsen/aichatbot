from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from typing import List
from sqlalchemy.orm import Session
from ..services.pipeline import WebCrawlerPipeline, EmbeddingPipeline
from ..services.domain_verification import DomainVerificationService
from ..services.file_processor import FileProcessor
from ..database.models import Website, Chat, Message
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

def clean_dataframe_for_json(df):
    """تمیز کردن DataFrame برای تبدیل به JSON"""
    import numpy as np
    
    # کپی DataFrame
    df_clean = df.copy()
    
    # جایگزینی NaN با None
    df_clean = df_clean.replace({np.nan: None})
    
    # جایگزینی infinite values با None
    df_clean = df_clean.replace({np.inf: None, -np.inf: None})
    
    # تبدیل تمام ستون‌ها به string برای اطمینان
    for col in df_clean.columns:
        df_clean[col] = df_clean[col].astype(str)
        # جایگزینی 'None' با None
        df_clean[col] = df_clean[col].replace('None', None)
        df_clean[col] = df_clean[col].replace('nan', None)
    
    return df_clean

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
            priority=1,
            max_pages=website.max_pages or 50,  # کراول کامل سایت
            max_depth=website.max_depth or 3    # عمق 3 سطح
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
        
        # پیدا کردن تمام چت‌های مربوط به این وب‌سایت
        chats = db.query(Chat).filter(Chat.website_id == website_id).all()
        
        # حذف تمام پیام‌های مربوط به این چت‌ها
        for chat in chats:
            db.query(Message).filter(Message.chat_id == chat.id).delete()
        
        # حذف چت‌های مربوطه
        db.query(Chat).filter(Chat.website_id == website_id).delete()
        
        # حذف فایل‌های مربوط به وب‌سایت از سیستم فایل
        try:
            import shutil
            from pathlib import Path
            
            base_dir = Path(__file__).parent.parent.parent
            
            # حذف پوشه‌های مختلف مربوط به وب‌سایت
            directories_to_delete = [
                base_dir / "processed_data" / website.domain,  # داده‌های کراول شده
                base_dir / "uploads" / website.domain,         # فایل‌های آپلود شده
                base_dir / "knowledge_base" / website.domain   # پایگاه دانش
            ]
            
            for directory in directories_to_delete:
                if directory.exists():
                    shutil.rmtree(directory)
                    logger.info(f"Directory {directory} deleted successfully")
                else:
                    logger.info(f"Directory {directory} does not exist, skipping")
                
        except Exception as file_error:
            logger.warning(f"خطا در حذف فایل‌های وب‌سایت: {file_error}")
        
        # حذف collection از ChromaDB
        try:
            from ..services.rag import RAGService
            rag_service = RAGService()
            if hasattr(rag_service, 'collection') and rag_service.collection:
                # حذف collection اگر وجود دارد
                import chromadb
                client = chromadb.PersistentClient(path=rag_service.vector_db_path)
                try:
                    client.delete_collection(name=website.collection_name or f"website_{website_id}")
                    logger.info(f"ChromaDB collection {website.collection_name} deleted successfully")
                except Exception as chroma_error:
                    logger.warning(f"خطا در حذف ChromaDB collection: {chroma_error}")
        except Exception as rag_error:
            logger.warning(f"خطا در حذف RAG data: {rag_error}")
        
        # حذف وب‌سایت
        db.delete(website)
        db.commit()
        
        logger.info(f"Website {website_id} deleted successfully by user {current_user.id}")
        return {"message": "وب‌سایت با موفقیت حذف شد"}
        
    except Exception as e:
        db.rollback()
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

@router.post("/{website_id}/crawl")
async def crawl_specific_urls(
    website_id: int,
    crawl_request: schemas.CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """کراول کردن URL های خاص برای یک وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت
        website = verify_website_ownership(website_id, current_user.id, db)
        
        # اعتبارسنجی درخواست
        if not crawl_request.urls or len(crawl_request.urls) == 0:
            raise HTTPException(status_code=400, detail="حداقل یک URL باید وارد شود")
        
        # شروع کراولینگ برای هر URL
        from app.services.crawler_queue import crawler_queue
        
        tasks = []
        for url in crawl_request.urls:
            task = crawler_queue.add_crawl_task(
                website_id=website_id,
                url=url,
                domain=website.domain,
                owner_id=current_user.id,
                priority=1,
                max_pages=crawl_request.max_pages or 1,
                max_depth=crawl_request.max_depth or 1
            )
            tasks.append(task)
        
        logger.info(f"Added {len(tasks)} crawl tasks for website {website_id}")
        
        return {
            "message": f"کراولینگ {len(crawl_request.urls)} URL شروع شد",
            "website_id": website_id,
            "tasks_count": len(tasks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در شروع کراول URL های خاص: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    query: str = "",
    filter_by: str = "all",
    sort_by: str = "title",
    sort_order: str = "asc",
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
        
        # تمیز کردن DataFrame برای جلوگیری از خطای JSON
        df = clean_dataframe_for_json(df)
        
        # اعمال فیلتر و جستجو
        if query:
            if filter_by == "title":
                df = df[df['title'].str.contains(query, case=False, na=False)]
            elif filter_by == "text":
                df = df[df['text'].str.contains(query, case=False, na=False)]
            elif filter_by == "url":
                df = df[df['url'].str.contains(query, case=False, na=False)]
            else:  # all
                df = df[
                    df['title'].str.contains(query, case=False, na=False) |
                    df['text'].str.contains(query, case=False, na=False) |
                    df['url'].str.contains(query, case=False, na=False)
                ]
        
        # مرتب‌سازی
        if sort_by == "title":
            df = df.sort_values('title', ascending=(sort_order == 'asc'))
        elif sort_by == "url":
            df = df.sort_values('url', ascending=(sort_order == 'asc'))
        elif sort_by == "links_count":
            df['links_count'] = df['links'].apply(get_links_count)
            df = df.sort_values('links_count', ascending=(sort_order == 'asc'))
        elif sort_by == "created_at":
            # اگر ستون created_at وجود دارد
            if 'created_at' in df.columns:
                df = df.sort_values('created_at', ascending=(sort_order == 'asc'))
        
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
                "links_count": get_links_count(row.get('links', [])),
                "source_type": row.get('source_type', 'unknown')  # نوع منبع
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
        
        # حذف از ChromaDB
        try:
            from ..services.rag import RAGService
            rag_service = RAGService(collection_name=website.domain)
            
            # جستجو برای پیدا کردن document در ChromaDB
            results = rag_service.search_knowledge_base(page_url, n_results=1)
            
            if results['documents'][0]:  # اگر document پیدا شد
                # پیدا کردن ID document
                for i, metadata in enumerate(results['metadatas'][0]):
                    if metadata.get('url') == page_url:
                        document_id = results['ids'][0][i]
                        # حذف از ChromaDB
                        rag_service.delete_document(document_id)
                        logger.info(f"Document {document_id} deleted from ChromaDB")
                        break
            
        except Exception as e:
            logger.warning(f"خطا در حذف از ChromaDB: {str(e)}")
        
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
                    
                    # جستجو برای پیدا کردن document در ChromaDB
                    results = rag_service.search_knowledge_base(page_url, n_results=1)
                    
                    if results['documents'][0]:  # اگر document پیدا شد
                        # پیدا کردن ID document
                        for i, metadata in enumerate(results['metadatas'][0]):
                            if metadata.get('url') == page_url:
                                document_id = results['ids'][0][i]
                                # به‌روزرسانی در ChromaDB
                                rag_service.update_document(
                                    document_id=document_id,
                                    text=page_data['text'],
                                    metadata={'url': page_url, 'title': page_data.get('title', '')}
                                )
                                logger.info(f"Document {document_id} updated in ChromaDB")
                                break
                    else:
                        # اگر document پیدا نشد، آن را اضافه کن
                        rag_service.add_document(
                            text=page_data['text'],
                            metadata={'url': page_url, 'title': page_data.get('title', '')}
                        )
                        logger.info(f"New document added to ChromaDB for URL: {page_url}")
                    
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
        logger.info(f"Adding manual page for website {website_id}, data: {page_data}")
        
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        logger.info(f"Website found: {website.domain}")
        
        # اعتبارسنجی داده‌ها
        required_fields = ['url', 'title', 'text']
        for field in required_fields:
            if field not in page_data or not page_data[field]:
                logger.error(f"Missing required field: {field}")
                raise HTTPException(status_code=400, detail=f"فیلد {field} الزامی است")
        
        logger.info("All required fields validated successfully")
        
        # خواندن فایل CSV
        base_dir = Path(__file__).parent.parent.parent
        csv_path = base_dir / "processed_data" / website.domain / "processed_data.csv"
        logger.info(f"CSV path: {csv_path}")
        
        # ایجاد پوشه اگر وجود ندارد
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Directory created/verified")
        
        if pd is None:
            raise HTTPException(status_code=500, detail="pandas در دسترس نیست")
        
        # خواندن یا ایجاد DataFrame
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            logger.info(f"Existing CSV loaded with {len(df)} rows")
        else:
            df = pd.DataFrame(columns=['url', 'title', 'text', 'links', 'source_type'])
            logger.info("New DataFrame created")
        
        # بررسی تکراری نبودن URL (فقط در ستون url، نه در links)
        if page_data['url'] in df['url'].values:
            logger.error(f"URL already exists in main URLs: {page_data['url']}")
            raise HTTPException(status_code=400, detail="این URL قبلاً به عنوان صفحه اصلی اضافه شده است")
        
        # بررسی تکراری نبودن در links (اختیاری - می‌تواند حذف شود)
        # for idx, row in df.iterrows():
        #     if row['links'] and page_data['url'] in row['links']:
        #         logger.warning(f"URL exists in links of row {idx}, but allowing addition")
        
        logger.info("URL validation passed")
        
        # اضافه کردن صفحه جدید
        links_data = page_data.get('links', [])
        if isinstance(links_data, list):
            links_str = json.dumps(links_data)
        else:
            links_str = json.dumps([])
            
        new_page = {
            'url': page_data['url'],
            'title': page_data['title'],
            'text': page_data['text'],
            'links': links_str,
            'source_type': 'text'  # Manual text addition
        }
        
        logger.info(f"New page data: {new_page}")
        
        df = pd.concat([df, pd.DataFrame([new_page])], ignore_index=True)
        logger.info(f"DataFrame updated, new length: {len(df)}")
        
        df.to_csv(csv_path, index=False)
        logger.info("CSV file saved successfully")
        
        # تولید امبدینگ برای صفحه جدید
        try:
            from app.services.rag import RAGService
            from app.services.embedding import EmbeddingService
            
            # ایجاد RAG service برای این وب‌سایت
            rag_service = RAGService(collection_name=website.domain)
            
            # تولید امبدینگ و اضافه کردن به ChromaDB
            success = rag_service.add_document(
                text=page_data['text'],
                metadata={
                    'url': page_data['url'],
                    'title': page_data['title'],
                    'website_id': website_id,
                    'source': 'manual'
                }
            )
            
            if success:
                logger.info("Embedding generated and added to ChromaDB successfully")
            else:
                logger.warning("Failed to generate embedding, but page was saved to CSV")
                
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # صفحه در CSV ذخیره شده، اما embedding تولید نشده
        
        return {
            "website_id": website_id,
            "page_url": page_data['url'],
            "message": "صفحه جدید با موفقیت اضافه شد",
            "total_pages": len(df)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در اضافه کردن صفحه: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"خطا در اضافه کردن صفحه: {str(e)}")

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
                "links_count": get_links_count(row.get('links', [])),
                "source_type": row.get('source_type', 'unknown')  # نوع منبع
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
    export_type: str = "full",  # full, excel_compatible
    max_text_length: int = 1000,  # حداکثر طول متن در هر سلول (فقط برای excel_compatible)
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
        
        # تمیز کردن DataFrame برای جلوگیری از خطای JSON
        df = clean_dataframe_for_json(df)
        
        # تقسیم متن‌های طولانی برای سازگاری با Excel
        if export_type == "excel_compatible":
            df['text'] = df['text'].apply(
                lambda x: str(x)[:max_text_length] + "..." if len(str(x)) > max_text_length else str(x)
            )
        
        if format == "json":
            data = df.to_dict('records')
            return {
                "website_id": website_id,
                "domain": website.domain,
                "format": "json",
                "data": data,
                "total_pages": len(df),
                "exported_at": datetime.now().isoformat(),
                "export_type": export_type,
                "text_truncated": export_type == "excel_compatible",
                "max_text_length": max_text_length if export_type == "excel_compatible" else None
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
                "export_type": export_type,
                "text_truncated": export_type == "excel_compatible",
                "max_text_length": max_text_length if export_type == "excel_compatible" else None,
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
        
        # اضافه کردن source_type اگر وجود ندارد
        if 'source_type' not in df_import.columns:
            df_import['source_type'] = 'import'  # Imported data
        
        # تمیز کردن DataFrame برای جلوگیری از خطای JSON
        df_import = clean_dataframe_for_json(df_import)
        
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

@router.post("/{website_id}/upload")
async def upload_file(
    website_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """آپلود و پردازش فایل برای اضافه کردن به پایگاه دانش"""
    try:
        logger.info(f"File upload request for website {website_id}, file: {file.filename}")
        logger.info(f"File content type: {file.content_type}")
        logger.info(f"File size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # بررسی مالکیت وب‌سایت (جداسازی tenant)
        website = verify_website_ownership(website_id, current_user.id, db)
        logger.info(f"Website found: {website.domain}")
        
        # بررسی فایل
        if not file.filename:
            raise HTTPException(status_code=400, detail="نام فایل الزامی است")
        
        # ایجاد پوشه uploads اگر وجود ندارد
        base_dir = Path(__file__).parent.parent.parent
        upload_dir = base_dir / "uploads" / website.domain
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # ذخیره فایل موقت
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"File saved to: {file_path}")
        
        # پردازش فایل
        file_processor = FileProcessor()
        try:
            result = file_processor.process_file(
                str(file_path), 
                file.filename,
                metadata={
                    'website_id': website_id,
                    'uploaded_by': current_user.email,
                    'upload_date': datetime.now().isoformat(),
                    'source': 'file_upload'
                }
            )
        except Exception as e:
            # حذف فایل موقت در صورت خطا
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=400, detail=f"خطا در پردازش فایل: {str(e)}")
        
        # اضافه کردن به CSV
        csv_path = base_dir / "processed_data" / website.domain / "processed_data.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        if pd is None:
            raise HTTPException(status_code=500, detail="pandas در دسترس نیست")
        
        # خواندن یا ایجاد DataFrame
        if csv_path.exists():
            df = pd.read_csv(csv_path)
        else:
            df = pd.DataFrame(columns=['url', 'title', 'text', 'links', 'source_type'])
        
        # اضافه کردن chunks به DataFrame
        new_rows = []
        for i, chunk in enumerate(result['chunks']):
            # ایجاد URL منحصر به فرد برای هر chunk
            chunk_url = f"file://{website.domain}/{file.filename}#chunk_{i+1}"
            
            new_row = {
                'url': chunk_url,
                'title': f"{file.filename} - بخش {i+1}",
                'text': chunk,
                'links': json.dumps([]),  # فایل‌ها لینک ندارند
                'source_type': 'file'  # File upload
            }
            new_rows.append(new_row)
        
        # اضافه کردن ردیف‌های جدید
        if new_rows:
            df_new = pd.DataFrame(new_rows)
            df = pd.concat([df, df_new], ignore_index=True)
            df.to_csv(csv_path, index=False)
        
        # تولید embedding و اضافه کردن به ChromaDB
        try:
            from ..services.rag import RAGService
            rag_service = RAGService(collection_name=website.domain)
            
            for i, chunk in enumerate(result['chunks']):
                chunk_url = f"file://{website.domain}/{file.filename}#chunk_{i+1}"
                
                success = rag_service.add_document(
                    text=chunk,
                    metadata={
                        'url': chunk_url,
                        'title': f"{file.filename} - بخش {i+1}",
                        'filename': file.filename,
                        'chunk_index': i,
                        'website_id': website_id,
                        'uploaded_by': current_user.email,
                        'upload_date': datetime.now().isoformat(),
                        'source': 'file_upload'
                    }
                )
                
                if not success:
                    logger.warning(f"Failed to add chunk {i+1} to ChromaDB")
            
            logger.info(f"All chunks added to ChromaDB successfully")
            
        except Exception as e:
            logger.warning(f"خطا در تولید embedding: {str(e)}")
        
        # حذف فایل موقت
        if file_path.exists():
            file_path.unlink()
        
        from fastapi.responses import JSONResponse
        
        return JSONResponse(content={
            "website_id": website_id,
            "filename": file.filename,
            "message": "فایل با موفقیت پردازش و اضافه شد",
            "total_chunks": len(result['chunks']),
            "total_characters": result['metadata']['total_characters'],
            "file_type": result['metadata']['file_type']
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در آپلود فایل: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطا در آپلود فایل: {str(e)}")

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

 