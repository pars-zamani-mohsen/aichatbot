from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Any
try:
    import pandas as pd
except ImportError:
    pd = None
from pathlib import Path
import json
from datetime import datetime, timedelta

from ..database.database import get_db
from ..database.models import User, Website, Chat, Message
from .auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت آمار کلی داشبورد"""
    try:
        # آمار وب‌سایت‌ها
        total_websites = db.query(Website).filter(Website.owner_id == current_user.id).count()
        ready_websites = db.query(Website).filter(
            and_(Website.owner_id == current_user.id, Website.status == "ready")
        ).count()
        crawling_websites = db.query(Website).filter(
            and_(Website.owner_id == current_user.id, Website.status == "crawling")
        ).count()
        error_websites = db.query(Website).filter(
            and_(Website.owner_id == current_user.id, Website.status == "error")
        ).count()
        
        # آمار چت‌ها
        total_chats = db.query(Chat).join(Website).filter(Website.owner_id == current_user.id).count()
        
        # آمار پیام‌ها
        total_messages = db.query(Message).join(Chat).join(Website).filter(
            Website.owner_id == current_user.id
        ).count()
        
        # آمار امروز
        today = datetime.now().date()
        today_chats = db.query(Chat).join(Website).filter(
            and_(
                Website.owner_id == current_user.id,
                func.date(Chat.created_at) == today
            )
        ).count()
        
        today_messages = db.query(Message).join(Chat).join(Website).filter(
            and_(
                Website.owner_id == current_user.id,
                func.date(Message.created_at) == today
            )
        ).count()
        
        # آمار صفحات کراول شده
        total_pages = 0
        for website in db.query(Website).filter(Website.owner_id == current_user.id).all():
            if website.crawl_info and 'total_pages' in website.crawl_info:
                total_pages += website.crawl_info['total_pages']
        
        return {
            "websites": {
                "total": total_websites,
                "ready": ready_websites,
                "crawling": crawling_websites,
                "error": error_websites
            },
            "chats": {
                "total": total_chats,
                "today": today_chats
            },
            "messages": {
                "total": total_messages,
                "today": today_messages
            },
            "pages": {
                "total_crawled": total_pages
            }
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت آمار داشبورد: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/websites/{website_id}/detailed-stats")
async def get_website_detailed_stats(
    website_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت آمار تفصیلی یک وب‌سایت"""
    try:
        # بررسی مالکیت
        website = db.query(Website).filter(
            and_(Website.id == website_id, Website.owner_id == current_user.id)
        ).first()
        
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
        
        # آمار چت‌ها
        total_chats = db.query(Chat).filter(Chat.website_id == website_id).count()
        
        # آمار پیام‌ها
        total_messages = db.query(Message).join(Chat).filter(Chat.website_id == website_id).count()
        
        # آمار امروز
        today = datetime.now().date()
        today_chats = db.query(Chat).filter(
            and_(
                Chat.website_id == website_id,
                func.date(Chat.created_at) == today
            )
        ).count()
        
        today_messages = db.query(Message).join(Chat).filter(
            and_(
                Chat.website_id == website_id,
                func.date(Message.created_at) == today
            )
        ).count()
        
        # آمار هفته گذشته
        week_ago = datetime.now().date() - timedelta(days=7)
        weekly_chats = db.query(Chat).filter(
            and_(
                Chat.website_id == website_id,
                func.date(Chat.created_at) >= week_ago
            )
        ).count()
        
        # اطلاعات کراول
        crawl_info = website.crawl_info or {}
        total_pages = crawl_info.get('total_pages', 0)
        last_crawl = crawl_info.get('crawled_at', None)
        
        return {
            "website_id": website_id,
            "website_name": website.name or website.domain,
            "status": website.status,
            "chats": {
                "total": total_chats,
                "today": today_chats,
                "weekly": weekly_chats
            },
            "messages": {
                "total": total_messages,
                "today": today_messages
            },
            "crawl": {
                "total_pages": total_pages,
                "last_crawl": last_crawl,
                "collection_name": website.collection_name
            },
            "settings": {
                "crawl_settings": website.crawl_settings,
                "rag_settings": website.rag_settings,
                "widget_settings": website.widget_settings
            }
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت آمار تفصیلی: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت فعالیت‌های اخیر"""
    try:
        # چت‌های اخیر
        recent_chats = db.query(Chat).join(Website).filter(
            Website.owner_id == current_user.id
        ).order_by(Chat.created_at.desc()).limit(limit).all()
        
        # پیام‌های اخیر
        recent_messages = db.query(Message).join(Chat).join(Website).filter(
            Website.owner_id == current_user.id
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        # وب‌سایت‌های اخیر
        recent_websites = db.query(Website).filter(
            Website.owner_id == current_user.id
        ).order_by(Website.created_at.desc()).limit(limit).all()
        
        return {
            "recent_chats": [
                {
                    "id": chat.id,
                    "website_name": chat.website.name or chat.website.domain,
                    "created_at": chat.created_at.isoformat(),
                    "message_count": len(chat.messages)
                }
                for chat in recent_chats
            ],
            "recent_messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                    "website_name": msg.chat.website.name or msg.chat.website.domain,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in recent_messages
            ],
            "recent_websites": [
                {
                    "id": website.id,
                    "name": website.name or website.domain,
                    "status": website.status,
                    "created_at": website.created_at.isoformat()
                }
                for website in recent_websites
            ]
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت فعالیت‌های اخیر: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
