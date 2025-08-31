from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database.database import get_db
from ..database import models
from ..services.email_archive_service import EmailArchiveService
from ..api.auth import get_current_user, oauth2_scheme
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/admin/email-archive")
async def get_admin_email_archive(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    email_type: Optional[str] = Query(None),
    recipient_email: Optional[str] = Query(None),
    is_sent: Optional[bool] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """دریافت لیست ایمیل‌های آرشیو شده (فقط ادمین)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="فقط ادمین می‌تواند به آرشیو ایمیل‌ها دسترسی داشته باشد"
        )
    
    try:
        result = EmailArchiveService.get_emails(
            db=db,
            page=page,
            limit=limit,
            email_type=email_type,
            recipient_email=recipient_email,
            is_sent=is_sent
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting email archive: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطا در دریافت آرشیو ایمیل‌ها"
        )

@router.get("/admin/email-archive/stats")
async def get_admin_email_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """دریافت آمار ایمیل‌ها (فقط ادمین)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="فقط ادمین می‌تواند آمار ایمیل‌ها را مشاهده کند"
        )
    
    try:
        stats = EmailArchiveService.get_email_stats(db)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting email stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطا در دریافت آمار ایمیل‌ها"
        )

@router.get("/admin/email-archive/{email_id}")
async def get_admin_email_detail(
    email_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """دریافت جزئیات یک ایمیل خاص (فقط ادمین)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="فقط ادمین می‌تواند به جزئیات ایمیل دسترسی داشته باشد"
        )
    
    try:
        email = EmailArchiveService.get_email_by_id(db, email_id)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ایمیل یافت نشد"
            )
        
        return email
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطا در دریافت جزئیات ایمیل"
        )

@router.delete("/admin/email-archive/{email_id}")
async def delete_admin_email(
    email_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """حذف ایمیل از آرشیو (فقط ادمین)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="فقط ادمین می‌تواند ایمیل‌ها را حذف کند"
        )
    
    try:
        success = EmailArchiveService.delete_email(db, email_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ایمیل یافت نشد"
            )
        
        return {"message": "ایمیل با موفقیت حذف شد"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطا در حذف ایمیل"
        )

@router.post("/admin/email-archive/retry-failed")
async def retry_failed_emails(
    max_retries: int = Query(3, ge=1, le=10),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """تلاش مجدد برای ارسال ایمیل‌های ناموفق (فقط ادمین)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="فقط ادمین می‌تواند ایمیل‌های ناموفق را ارسال مجدد کند"
        )
    
    try:
        retry_count = EmailArchiveService.retry_failed_emails(db, max_retries)
        return {
            "message": f"{retry_count} ایمیل برای ارسال مجدد آماده شد",
            "retry_count": retry_count
        }
        
    except Exception as e:
        logger.error(f"Error retrying failed emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطا در ارسال مجدد ایمیل‌ها"
        )
