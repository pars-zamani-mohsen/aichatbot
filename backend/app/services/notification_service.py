#!/usr/bin/env python3
"""
سرویس اعلان‌ها برای مدیریت اعلان‌های سیستم
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..database import models
from ..api import schemas
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """سرویس مدیریت اعلان‌ها"""
    
    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        category: str = "system",
        extra_data: Optional[Dict[str, Any]] = None
    ) -> models.Notification:
        """ایجاد اعلان جدید"""
        try:
            # دریافت تنظیمات کاربر
            user_settings = db.query(models.UserSettings).filter(
                models.UserSettings.user_id == user_id
            ).first()
            
            if not user_settings:
                logger.warning(f"User settings not found for user {user_id}")
                return None
            
            # ایجاد اعلان
            notification = models.Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                category=category,
                extra_data=extra_data or {}
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # ارسال اعلان بر اساس تنظیمات کاربر
            NotificationService._send_notifications(db, notification, user_settings)
            
            logger.info(f"Notification created for user {user_id}: {title}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    def _send_notifications(
        db: Session,
        notification: models.Notification,
        user_settings: models.UserSettings
    ):
        """ارسال اعلان بر اساس تنظیمات کاربر"""
        try:
            # ارسال ایمیل
            if user_settings.email_notifications:
                NotificationService._send_email_notification(notification)
                notification.is_sent_email = True
            
            # ارسال push notification (در آینده پیاده‌سازی شود)
            if user_settings.push_notifications:
                NotificationService._send_push_notification(notification)
                notification.is_sent_push = True
            
            # ارسال SMS (در آینده پیاده‌سازی شود)
            if user_settings.sms_notifications:
                NotificationService._send_sms_notification(notification)
                notification.is_sent_sms = True
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error sending notifications: {str(e)}")
    
    @staticmethod
    def _send_email_notification(notification: models.Notification):
        """ارسال اعلان از طریق ایمیل"""
        # TODO: پیاده‌سازی ارسال ایمیل
        logger.info(f"Email notification would be sent: {notification.title}")
    
    @staticmethod
    def _send_push_notification(notification: models.Notification):
        """ارسال push notification"""
        # TODO: پیاده‌سازی push notification
        logger.info(f"Push notification would be sent: {notification.title}")
    
    @staticmethod
    def _send_sms_notification(notification: models.Notification):
        """ارسال SMS"""
        # TODO: پیاده‌سازی SMS
        logger.info(f"SMS notification would be sent: {notification.title}")
    
    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
        category: Optional[str] = None
    ) -> List[models.Notification]:
        """دریافت اعلان‌های کاربر"""
        query = db.query(models.Notification).filter(
            models.Notification.user_id == user_id
        )
        
        if unread_only:
            query = query.filter(models.Notification.is_read == False)
        
        if category:
            query = query.filter(models.Notification.category == category)
        
        return query.order_by(
            models.Notification.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def mark_as_read(
        db: Session,
        notification_id: int,
        user_id: int
    ) -> bool:
        """علامت‌گذاری اعلان به عنوان خوانده شده"""
        try:
            notification = db.query(models.Notification).filter(
                models.Notification.id == notification_id,
                models.Notification.user_id == user_id
            ).first()
            
            if notification:
                notification.is_read = True
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def mark_all_as_read(
        db: Session,
        user_id: int,
        category: Optional[str] = None
    ) -> bool:
        """علامت‌گذاری همه اعلان‌ها به عنوان خوانده شده"""
        try:
            query = db.query(models.Notification).filter(
                models.Notification.user_id == user_id,
                models.Notification.is_read == False
            )
            
            if category:
                query = query.filter(models.Notification.category == category)
            
            query.update({"is_read": True})
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def delete_notification(
        db: Session,
        notification_id: int,
        user_id: int
    ) -> bool:
        """حذف اعلان"""
        try:
            notification = db.query(models.Notification).filter(
                models.Notification.id == notification_id,
                models.Notification.user_id == user_id
            ).first()
            
            if notification:
                db.delete(notification)
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting notification: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def get_unread_count(
        db: Session,
        user_id: int,
        category: Optional[str] = None
    ) -> int:
        """دریافت تعداد اعلان‌های نخوانده"""
        query = db.query(models.Notification).filter(
            models.Notification.user_id == user_id,
            models.Notification.is_read == False
        )
        
        if category:
            query = query.filter(models.Notification.category == category)
        
        return query.count()
    
    # متدهای کمکی برای ایجاد اعلان‌های خاص
    @staticmethod
    def notify_new_conversation(
        db: Session,
        user_id: int,
        website_name: str,
        chat_id: int
    ):
        """اعلان چت جدید"""
        if not NotificationService._should_notify(db, user_id, "notify_on_new_conversation"):
            return
        
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="چت جدید",
            message=f"یک چت جدید در وب‌سایت {website_name} شروع شده است.",
            notification_type="info",
            category="conversation",
            extra_data={"chat_id": chat_id, "website_name": website_name}
        )
    
    @staticmethod
    def notify_website_update(
        db: Session,
        user_id: int,
        website_name: str,
        update_type: str
    ):
        """اعلان به‌روزرسانی وب‌سایت"""
        if not NotificationService._should_notify(db, user_id, "notify_on_website_update"):
            return
        
        messages = {
            "crawl_completed": f"کراولینگ وب‌سایت {website_name} با موفقیت تکمیل شد.",
            "crawl_failed": f"کراولینگ وب‌سایت {website_name} با خطا مواجه شد.",
            "domain_verified": f"دامنه وب‌سایت {website_name} تأیید شد.",
            "rag_updated": f"تنظیمات RAG وب‌سایت {website_name} به‌روزرسانی شد."
        }
        
        message = messages.get(update_type, f"وب‌سایت {website_name} به‌روزرسانی شد.")
        
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="به‌روزرسانی وب‌سایت",
            message=message,
            notification_type="success" if "failed" not in update_type else "warning",
            category="website",
            extra_data={"website_name": website_name, "update_type": update_type}
        )
    
    @staticmethod
    def notify_security_event(
        db: Session,
        user_id: int,
        event_type: str,
        details: str
    ):
        """اعلان رویداد امنیتی"""
        messages = {
            "login_attempt": "تلاش ورود ناموفق",
            "2fa_enabled": "احراز هویت دو مرحله‌ای فعال شد",
            "2fa_disabled": "احراز هویت دو مرحله‌ای غیرفعال شد",
            "password_changed": "رمز عبور تغییر یافت",
            "account_locked": "حساب کاربری قفل شد"
        }
        
        title = messages.get(event_type, "رویداد امنیتی")
        
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=details,
            notification_type="warning",
            category="security",
            extra_data={"event_type": event_type}
        )
    
    @staticmethod
    def _should_notify(db: Session, user_id: int, setting_name: str) -> bool:
        """بررسی اینکه آیا باید اعلان ارسال شود یا نه"""
        user_settings = db.query(models.UserSettings).filter(
            models.UserSettings.user_id == user_id
        ).first()
        
        if not user_settings:
            return False
        
        return getattr(user_settings, setting_name, True)
