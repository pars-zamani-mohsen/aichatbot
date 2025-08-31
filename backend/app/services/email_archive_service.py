from sqlalchemy.orm import Session
from ..database import models
from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class EmailArchiveService:
    """سرویس مدیریت آرشیو ایمیل‌ها"""
    
    @classmethod
    def archive_email(
        cls,
        db: Session,
        email_type: str,
        recipient_email: str,
        subject: str,
        body: str,
        from_email: str,
        to_email: str,
        html_body: str = None,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        attachments: List[Dict] = None,
        smtp_server: str = None,
        smtp_port: int = None,
        smtp_username: str = None,
        user_id: int = None,
        website_id: int = None,
        extra_data: Dict = None
    ) -> models.EmailArchive:
        """ذخیره ایمیل در آرشیو"""
        try:
            email_archive = models.EmailArchive(
                email_type=email_type,
                recipient_email=recipient_email,
                subject=subject,
                body=body,
                html_body=html_body,
                from_email=from_email,
                to_email=to_email,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                attachments=attachments,
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                user_id=user_id,
                website_id=website_id,
                extra_data=extra_data,
                is_sent=False
            )
            
            db.add(email_archive)
            db.commit()
            db.refresh(email_archive)
            
            logger.info(f"Email archived: {email_type} to {recipient_email}")
            return email_archive
            
        except Exception as e:
            logger.error(f"Error archiving email: {str(e)}")
            db.rollback()
            return None
    
    @classmethod
    def mark_as_sent(cls, db: Session, email_id: int, error_message: str = None) -> bool:
        """علامت‌گذاری ایمیل به عنوان ارسال شده"""
        try:
            email = db.query(models.EmailArchive).filter(models.EmailArchive.id == email_id).first()
            if not email:
                return False
            
            email.is_sent = error_message is None
            email.sent_at = datetime.now(timezone.utc)
            email.error_message = error_message
            
            if error_message:
                email.retry_count += 1
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error marking email as sent: {str(e)}")
            db.rollback()
            return False
    
    @classmethod
    def get_emails(
        cls,
        db: Session,
        page: int = 1,
        limit: int = 20,
        email_type: str = None,
        recipient_email: str = None,
        is_sent: bool = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """دریافت لیست ایمیل‌های آرشیو شده"""
        try:
            query = db.query(models.EmailArchive)
            
            # فیلترها
            if email_type:
                query = query.filter(models.EmailArchive.email_type == email_type)
            if recipient_email:
                query = query.filter(models.EmailArchive.recipient_email.ilike(f"%{recipient_email}%"))
            if is_sent is not None:
                query = query.filter(models.EmailArchive.is_sent == is_sent)
            if user_id:
                query = query.filter(models.EmailArchive.user_id == user_id)
            
            # مرتب‌سازی بر اساس تاریخ ایجاد (جدیدترین اول)
            query = query.order_by(models.EmailArchive.created_at.desc())
            
            # محاسبه تعداد کل
            total = query.count()
            
            # صفحه‌بندی
            offset = (page - 1) * limit
            emails = query.offset(offset).limit(limit).all()
            
            return {
                "emails": emails,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }
            
        except Exception as e:
            logger.error(f"Error getting emails: {str(e)}")
            return {
                "emails": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0
            }
    
    @classmethod
    def get_email_by_id(cls, db: Session, email_id: int) -> Optional[models.EmailArchive]:
        """دریافت ایمیل بر اساس ID"""
        try:
            return db.query(models.EmailArchive).filter(models.EmailArchive.id == email_id).first()
        except Exception as e:
            logger.error(f"Error getting email by ID: {str(e)}")
            return None
    
    @classmethod
    def delete_email(cls, db: Session, email_id: int) -> bool:
        """حذف ایمیل از آرشیو"""
        try:
            email = db.query(models.EmailArchive).filter(models.EmailArchive.id == email_id).first()
            if not email:
                return False
            
            db.delete(email)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting email: {str(e)}")
            db.rollback()
            return False
    
    @classmethod
    def get_email_stats(cls, db: Session) -> Dict[str, Any]:
        """دریافت آمار ایمیل‌ها"""
        try:
            total_emails = db.query(models.EmailArchive).count()
            sent_emails = db.query(models.EmailArchive).filter(models.EmailArchive.is_sent == True).count()
            failed_emails = db.query(models.EmailArchive).filter(models.EmailArchive.is_sent == False).count()
            
            # آمار بر اساس نوع ایمیل
            email_types = db.query(models.EmailArchive.email_type).distinct().all()
            type_stats = {}
            for email_type in email_types:
                count = db.query(models.EmailArchive).filter(models.EmailArchive.email_type == email_type[0]).count()
                type_stats[email_type[0]] = count
            
            return {
                "total_emails": total_emails,
                "sent_emails": sent_emails,
                "failed_emails": failed_emails,
                "success_rate": (sent_emails / total_emails * 100) if total_emails > 0 else 0,
                "email_types": type_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting email stats: {str(e)}")
            return {
                "total_emails": 0,
                "sent_emails": 0,
                "failed_emails": 0,
                "success_rate": 0,
                "email_types": {}
            }
    
    @classmethod
    def retry_failed_emails(cls, db: Session, max_retries: int = 3) -> int:
        """تلاش مجدد برای ارسال ایمیل‌های ناموفق"""
        try:
            failed_emails = db.query(models.EmailArchive).filter(
                models.EmailArchive.is_sent == False,
                models.EmailArchive.retry_count < max_retries
            ).all()
            
            retry_count = 0
            for email in failed_emails:
                # اینجا می‌توانید منطق ارسال مجدد را اضافه کنید
                # برای مثال، فراخوانی سرویس ارسال ایمیل
                retry_count += 1
            
            return retry_count
            
        except Exception as e:
            logger.error(f"Error retrying failed emails: {str(e)}")
            return 0
