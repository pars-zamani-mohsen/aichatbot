#!/usr/bin/env python3
"""
API endpoints برای مدیریت اعلان‌ها
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
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
        notifications = NotificationService.get_user_notifications(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
            category=category
        )
        
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
        success = NotificationService.mark_as_read(
            db=db,
            notification_id=notification_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="اعلان یافت نشد")
        
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

@router.post("/test")
async def create_test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ایجاد اعلان تست (فقط برای توسعه)"""
    try:
        notification = NotificationService.create_notification(
            db=db,
            user_id=current_user.id,
            title="اعلان تست",
            message="این یک اعلان تست است برای بررسی عملکرد سیستم اعلان‌ها.",
            notification_type="info",
            category="system",
            extra_data={"test": True}
        )
        
        if not notification:
            raise HTTPException(status_code=500, detail="خطا در ایجاد اعلان تست")
        
        return {"message": "اعلان تست ایجاد شد", "notification_id": notification.id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating test notification: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در ایجاد اعلان تست")
