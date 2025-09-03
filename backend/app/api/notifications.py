#!/usr/bin/env python3
"""
API endpoints برای مدیریت اعلان‌ها
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..database import models
from ..database.models import User
from . import schemas
from .auth import get_current_user
from ..services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[schemas.Notification])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """دریافت اعلان‌های کاربر"""
    try:
        logger.info(f"User {current_user.id} requesting notifications")
        
        notifications = NotificationService.get_user_notifications(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
            category=category
        )
        
        logger.info(f"Returning {len(notifications)} notifications for user {current_user.id}")
        return notifications
        
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در دریافت اعلان‌ها")

@router.get("/unread-count")
async def get_unread_count(
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """دریافت تعداد اعلان‌های نخوانده"""
    try:
        count = NotificationService.get_unread_count(
            db=db,
            user_id=current_user.id,
            category=category
        )
        
        return {"unread_count": count}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در دریافت تعداد اعلان‌ها")

@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """علامت‌گذاری اعلان به عنوان خوانده شده"""
    try:
        # ابتدا بررسی کنیم که آیا اعلان وجود دارد
        notification = db.query(models.Notification).filter(
            models.Notification.id == notification_id
        ).first()
        
        if not notification:
            logger.warning(f"Notification {notification_id} not found")
            raise HTTPException(status_code=404, detail="اعلان یافت نشد")
        
        # بررسی کنیم که آیا اعلان متعلق به کاربر فعلی است
        if notification.user_id != current_user.id:
            logger.warning(f"User {current_user.id} tried to access notification {notification_id} owned by user {notification.user_id}")
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # علامت‌گذاری به عنوان خوانده شده
        notification.is_read = True
        db.commit()
        
        logger.info(f"Notification {notification_id} marked as read by user {current_user.id}")
        return {"message": "اعلان به عنوان خوانده شده علامت‌گذاری شد"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در علامت‌گذاری اعلان")

@router.put("/mark-all-read")
async def mark_all_as_read(
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """علامت‌گذاری همه اعلان‌ها به عنوان خوانده شده"""
    try:
        success = NotificationService.mark_all_as_read(
            db=db,
            user_id=current_user.id,
            category=category
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="خطا در علامت‌گذاری اعلان‌ها")
        
        return {"message": "همه اعلان‌ها به عنوان خوانده شده علامت‌گذاری شدند"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در علامت‌گذاری اعلان‌ها")

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """حذف اعلان"""
    try:
        success = NotificationService.delete_notification(
            db=db,
            notification_id=notification_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="اعلان یافت نشد")
        
        return {"message": "اعلان حذف شد"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در حذف اعلان")











@router.get("/admin/")
async def get_admin_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    category: Optional[str] = Query(None),
    notification_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت اعلان‌های سیستم برای ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # ساخت query
        query = db.query(models.Notification).join(models.User)
        
        if unread_only:
            query = query.filter(models.Notification.is_read == False)
        
        if category:
            query = query.filter(models.Notification.category == category)
        
        if notification_type:
            query = query.filter(models.Notification.type == notification_type)
        
        if user_id:
            query = query.filter(models.Notification.user_id == user_id)
        
        if search:
            search_filter = or_(
                models.Notification.title.ilike(f"%{search}%"),
                models.Notification.message.ilike(f"%{search}%"),
                models.User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # شمارش کل
        total = query.count()
        
        # دریافت نتایج
        notifications = query.order_by(
            models.Notification.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return {
            "notifications": [
                {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.type,
                    "category": notification.category,
                    "is_read": notification.is_read,
                    "created_at": notification.created_at.isoformat(),
                    "user_email": notification.user.email,
                    "user_id": notification.user_id,
                    "extra_data": notification.extra_data
                }
                for notification in notifications
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting admin notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در دریافت اعلان‌ها")

@router.delete("/admin/{notification_id}")
async def delete_admin_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """حذف اعلان توسط ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # پیدا کردن اعلان
        notification = db.query(models.Notification).filter(
            models.Notification.id == notification_id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="اعلان یافت نشد")
        
        # حذف اعلان
        db.delete(notification)
        db.commit()
        
        return {"message": "اعلان با موفقیت حذف شد"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting admin notification: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در حذف اعلان")

@router.post("/admin/send")
async def send_admin_notification(
    notification_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ارسال اعلان توسط ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # دریافت کاربران هدف
        user_ids = notification_data.get("user_ids", [])
        if not user_ids:
            # اگر کاربر خاصی انتخاب نشده، به همه کاربران ارسال شود
            users = db.query(models.User).filter(models.User.is_active == True).all()
            user_ids = [user.id for user in users]
        
        # ارسال اعلان به هر کاربر
        sent_count = 0
        for user_id in user_ids:
            notification = NotificationService.create_notification(
                db=db,
                user_id=user_id,
                title=notification_data.get("title", "اعلان سیستم"),
                message=notification_data.get("message", ""),
                notification_type=notification_data.get("type", "info"),
                category=notification_data.get("category", "system"),
                extra_data=notification_data.get("extra_data", {})
            )
            if notification:
                sent_count += 1
        
        return {
            "message": f"اعلان به {sent_count} کاربر ارسال شد",
            "sent_count": sent_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending admin notification: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در ارسال اعلان")
