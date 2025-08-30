from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, cast, Date
from typing import List, Dict, Any
try:
    import pandas as pd
except ImportError:
    pd = None
from pathlib import Path
import json
from datetime import datetime, timedelta, timezone

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
        today = datetime.now(timezone.utc).date()
        today_chats = db.query(Chat).join(Website).filter(
            and_(
                Website.owner_id == current_user.id,
                cast(Chat.created_at, Date) == today
            )
        ).count()
        
        today_messages = db.query(Message).join(Chat).join(Website).filter(
            and_(
                Website.owner_id == current_user.id,
                cast(Message.created_at, Date) == today
            )
        ).count()
        
        # آمار صفحات کراول شده
        total_pages = 0
        for website in db.query(Website).filter(Website.owner_id == current_user.id).all():
            if website.crawl_info and 'total_pages' in website.crawl_info:
                total_pages += website.crawl_info['total_pages']
        
        # محاسبه آمار هفته گذشته برای trend
        week_ago = datetime.now(timezone.utc).date() - timedelta(days=7)
        two_weeks_ago = datetime.now(timezone.utc).date() - timedelta(days=14)
        
        # آمار هفته گذشته
        last_week_chats = db.query(Chat).join(Website).filter(
            and_(
                Website.owner_id == current_user.id,
                cast(Chat.created_at, Date) >= two_weeks_ago,
                cast(Chat.created_at, Date) < week_ago
            )
        ).count()
        
        last_week_messages = db.query(Message).join(Chat).join(Website).filter(
            and_(
                Website.owner_id == current_user.id,
                cast(Message.created_at, Date) >= two_weeks_ago,
                cast(Message.created_at, Date) < week_ago
            )
        ).count()
        
        # محاسبه trend ها
        def calculate_trend(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 1)
        
        return {
            "websites": {
                "total": total_websites,
                "ready": ready_websites,
                "crawling": crawling_websites,
                "error": error_websites
            },
            "chats": {
                "total": total_chats,
                "today": today_chats,
                "trend": calculate_trend(today_chats, last_week_chats)
            },
            "messages": {
                "total": total_messages,
                "today": today_messages,
                "trend": calculate_trend(today_messages, last_week_messages)
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
        today = datetime.now(timezone.utc).date()
        today_chats = db.query(Chat).filter(
            and_(
                Chat.website_id == website_id,
                cast(Chat.created_at, Date) == today
            )
        ).count()
        
        today_messages = db.query(Message).join(Chat).filter(
            and_(
                Chat.website_id == website_id,
                cast(Message.created_at, Date) == today
            )
        ).count()
        
        # آمار هفته گذشته
        week_ago = datetime.now(timezone.utc).date() - timedelta(days=7)
        weekly_chats = db.query(Chat).filter(
            and_(
                Chat.website_id == website_id,
                cast(Chat.created_at, Date) >= week_ago
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

@router.get("/admin/stats")
async def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت آمار کلی داشبورد ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # آمار کلی
        total_users = db.query(User).count()
        total_websites = db.query(Website).count()
        total_chats = db.query(Chat).count()
        total_messages = db.query(Message).count()
        
        # کاربران فعال (آخرین 7 روز)
        week_ago = datetime.now(timezone.utc).date() - timedelta(days=7)
        active_users = db.query(User).filter(
            and_(
                User.last_login.isnot(None),
                cast(User.last_login, Date) >= week_ago
            )
        ).count()
        
        # وب‌سایت‌های فعال
        active_websites = db.query(Website).filter(Website.status == "ready").count()
        
        # آمار امروز
        today = datetime.now(timezone.utc).date()
        today_users = db.query(User).filter(cast(User.created_at, Date) == today).count()
        today_websites = db.query(Website).filter(cast(Website.created_at, Date) == today).count()
        today_chats = db.query(Chat).filter(cast(Chat.created_at, Date) == today).count()
        today_messages = db.query(Message).filter(cast(Message.created_at, Date) == today).count()
        
        # محاسبه آمار هفته گذشته برای trend
        week_ago = datetime.now(timezone.utc).date() - timedelta(days=7)
        two_weeks_ago = datetime.now(timezone.utc).date() - timedelta(days=14)
        
        # آمار هفته گذشته
        last_week_users = db.query(User).filter(
            and_(
                cast(User.created_at, Date) >= two_weeks_ago,
                cast(User.created_at, Date) < week_ago
            )
        ).count()
        
        last_week_websites = db.query(Website).filter(
            and_(
                cast(Website.created_at, Date) >= two_weeks_ago,
                cast(Website.created_at, Date) < week_ago
            )
        ).count()
        
        last_week_chats = db.query(Chat).filter(
            and_(
                cast(Chat.created_at, Date) >= two_weeks_ago,
                cast(Chat.created_at, Date) < week_ago
            )
        ).count()
        
        last_week_messages = db.query(Message).filter(
            and_(
                cast(Message.created_at, Date) >= two_weeks_ago,
                cast(Message.created_at, Date) < week_ago
            )
        ).count()
        
        # محاسبه trend ها
        def calculate_trend(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 1)
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "today_new": today_users,
                "trend": calculate_trend(today_users, last_week_users)
            },
            "websites": {
                "total": total_websites,
                "active": active_websites,
                "today_new": today_websites,
                "trend": calculate_trend(today_websites, last_week_websites)
            },
            "chats": {
                "total": total_chats,
                "today": today_chats,
                "trend": calculate_trend(today_chats, last_week_chats)
            },
            "messages": {
                "total": total_messages,
                "today": today_messages,
                "trend": calculate_trend(today_messages, last_week_messages)
            }
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت آمار ادمین: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/recent-activity")
async def get_admin_recent_activity(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت فعالیت‌های اخیر برای ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # کاربران جدید
        recent_users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
        
        # وب‌سایت‌های جدید
        recent_websites = db.query(Website).order_by(Website.created_at.desc()).limit(limit).all()
        
        # چت‌های جدید
        recent_chats = db.query(Chat).order_by(Chat.created_at.desc()).limit(limit).all()
        
        return {
            "recent_users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "created_at": user.created_at.isoformat(),
                    "is_active": user.is_active
                }
                for user in recent_users
            ],
            "recent_websites": [
                {
                    "id": website.id,
                    "name": website.name or website.domain,
                    "owner_email": website.owner.email,
                    "status": website.status,
                    "created_at": website.created_at.isoformat()
                }
                for website in recent_websites
            ],
            "recent_chats": [
                {
                    "id": chat.id,
                    "website_name": chat.website.name or chat.website.domain,
                    "owner_email": chat.website.owner.email,
                    "created_at": chat.created_at.isoformat(),
                    "message_count": len(chat.messages)
                }
                for chat in recent_chats
            ]
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت فعالیت‌های اخیر ادمین: {str(e)}")
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

@router.get("/weekly-stats")
async def get_weekly_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت آمار هفتگی برای نمودار"""
    try:
        # محاسبه تاریخ‌های هفته گذشته
        today = datetime.now(timezone.utc).date()
        week_ago = today - timedelta(days=7)
        
        # نام‌های روزهای هفته به فارسی
        day_names = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه']
        
        weekly_data = []
        
        for i in range(7):
            current_date = week_ago + timedelta(days=i)
            day_name = day_names[current_date.weekday()]
            
            # آمار چت‌ها برای این روز
            day_chats = db.query(Chat).join(Website).filter(
                and_(
                    Website.owner_id == current_user.id,
                    cast(Chat.created_at, Date) == current_date
                )
            ).count()
            
            # آمار پیام‌ها برای این روز
            day_messages = db.query(Message).join(Chat).join(Website).filter(
                and_(
                    Website.owner_id == current_user.id,
                    cast(Message.created_at, Date) == current_date
                )
            ).count()
            
            # آمار وب‌سایت‌های فعال برای این روز
            day_websites = db.query(Website).filter(
                and_(
                    Website.owner_id == current_user.id,
                    Website.status == "ready"
                )
            ).count()
            
            weekly_data.append({
                "day": day_name,
                "conversations": day_chats,
                "messages": day_messages,
                "websites": day_websites
            })
        
        return weekly_data
        
    except Exception as e:
        logger.error(f"خطا در دریافت آمار هفتگی: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/reports")
async def get_user_reports(
    time_range: str = "7d",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت گزارشات کاربر"""
    try:
        # محاسبه بازه زمانی
        today = datetime.now(timezone.utc).date()
        if time_range == "7d":
            start_date = today - timedelta(days=7)
        elif time_range == "30d":
            start_date = today - timedelta(days=30)
        elif time_range == "90d":
            start_date = today - timedelta(days=90)
        elif time_range == "1y":
            start_date = today - timedelta(days=365)
        else:
            start_date = today - timedelta(days=7)

        # آمار کلی
        total_conversations = db.query(Chat).join(Website).filter(Website.owner_id == current_user.id).count()
        total_messages = db.query(Message).join(Chat).join(Website).filter(Website.owner_id == current_user.id).count()
        active_websites = db.query(Website).filter(
            and_(Website.owner_id == current_user.id, Website.status == "ready")
        ).count()

        # آمار بازه زمانی
        period_conversations = db.query(Chat).join(Website).filter(
            and_(
                Website.owner_id == current_user.id,
                cast(Chat.created_at, Date) >= start_date
            )
        ).count()

        period_messages = db.query(Message).join(Chat).join(Website).filter(
            and_(
                Website.owner_id == current_user.id,
                cast(Message.created_at, Date) >= start_date
            )
        ).count()

        # آمار وب‌سایت‌ها
        websites_stats = []
        user_websites = db.query(Website).filter(Website.owner_id == current_user.id).all()
        
        for website in user_websites:
            website_conversations = db.query(Chat).filter(Chat.website_id == website.id).count()
            website_messages = db.query(Message).join(Chat).filter(Chat.website_id == website.id).count()
            
            # تعداد صفحات کراول شده
            total_pages = 0
            if website.crawl_info and 'total_pages' in website.crawl_info:
                total_pages = website.crawl_info['total_pages']
            
            websites_stats.append({
                "name": website.name or website.domain,
                "conversations": website_conversations,
                "messages": website_messages,
                "pages": total_pages,
                "status": website.status
            })

        # آمار وضعیت گفتگوها
        active_conversations = db.query(Chat).join(Website).filter(
            and_(
                Website.owner_id == current_user.id,
                Chat.id.in_(
                    db.query(Message.chat_id).distinct()
                )
            )
        ).count()

        completed_conversations = db.query(Chat).join(Website).filter(
            and_(
                Website.owner_id == current_user.id,
                ~Chat.id.in_(
                    db.query(Message.chat_id).distinct()
                )
            )
        ).count()

        total_conversations_with_status = active_conversations + completed_conversations
        if total_conversations_with_status > 0:
            active_percentage = round((active_conversations / total_conversations_with_status) * 100)
            completed_percentage = round((completed_conversations / total_conversations_with_status) * 100)
        else:
            active_percentage = 0
            completed_percentage = 0

        # محاسبه رضایت کاربران (شبیه‌سازی)
        satisfaction_rate = 92  # این می‌تواند بر اساس feedback های واقعی محاسبه شود

        return {
            "summary": {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "active_websites": active_websites,
                "satisfaction_rate": satisfaction_rate,
                "period_conversations": period_conversations,
                "period_messages": period_messages
            },
            "websites_stats": websites_stats,
            "conversation_status": [
                {"name": "فعال", "value": active_percentage, "color": "#10b981"},
                {"name": "تکمیل شده", "value": completed_percentage, "color": "#ef4444"}
            ]
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت گزارشات کاربر: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/weekly-stats")
async def get_admin_weekly_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت آمار هفتگی برای ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # محاسبه تاریخ‌های هفته گذشته
        today = datetime.now(timezone.utc).date()
        week_ago = today - timedelta(days=7)
        
        # نام‌های روزهای هفته به فارسی
        day_names = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه']
        
        weekly_data = []
        
        for i in range(7):
            current_date = week_ago + timedelta(days=i)
            day_name = day_names[current_date.weekday()]
            
            # آمار چت‌ها برای این روز
            day_chats = db.query(Chat).filter(
                cast(Chat.created_at, Date) == current_date
            ).count()
            
            # آمار کاربران فعال برای این روز
            day_users = db.query(User).filter(
                and_(
                    User.last_login.isnot(None),
                    cast(User.last_login, Date) == current_date
                )
            ).count()
            
            # آمار وب‌سایت‌های جدید برای این روز
            day_websites = db.query(Website).filter(
                cast(Website.created_at, Date) == current_date
            ).count()
            
            weekly_data.append({
                "day": day_name,
                "conversations": day_chats,
                "users": day_users,
                "websites": day_websites
            })
        
        return weekly_data
        
    except Exception as e:
        logger.error(f"خطا در دریافت آمار هفتگی ادمین: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
