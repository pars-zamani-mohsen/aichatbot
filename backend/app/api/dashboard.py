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
from ..database import models
from ..database.models import User, Website, Chat, Message, Notification
from ..services.system_settings_service import SystemSettingsService
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

@router.get("/user/history")
async def get_user_history(
    page: int = 1,
    limit: int = 20,
    activity_type: str = None,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت تاریخچه فعالیت‌های کاربر"""
    try:
        offset = (page - 1) * limit
        
        # ایجاد query base
        base_query = db.query(Website).filter(Website.owner_id == current_user.id)
        
        # فیلتر بر اساس نوع فعالیت - فعلاً غیرفعال می‌کنیم تا همه فعالیت‌ها نمایش داده شوند
        # if activity_type and activity_type != 'all':
        #     if activity_type == 'website_added':
        #         base_query = base_query.filter(Website.created_at.isnot(None))
        #     elif activity_type == 'website_updated':
        #         base_query = base_query.filter(Website.updated_at.isnot(None))
        
        # فیلتر بر اساس جستجو
        if search:
            base_query = base_query.filter(
                or_(
                    Website.name.contains(search),
                    Website.domain.contains(search)
                )
            )
        
        # دریافت وب‌سایت‌ها - بدون offset و limit برای نمایش همه
        websites = base_query.order_by(Website.created_at.desc()).all()
        
        # دریافت چت‌ها - بدون offset و limit برای نمایش همه
        chats_query = db.query(Chat).join(Website).filter(Website.owner_id == current_user.id)
        # فیلتر بر اساس نوع فعالیت - فعلاً غیرفعال می‌کنیم
        # if activity_type and activity_type != 'all':
        #     if activity_type == 'conversation_started':
        #         chats_query = chats_query.filter(Chat.created_at.isnot(None))
        #     elif activity_type == 'conversation_ended':
        #         # چت‌هایی که پیام دارند (پایان یافته)
        #         chats_query = chats_query.filter(Chat.id.in_(
        #             db.query(Message.chat_id).distinct()
        #         ))
        
        chats = chats_query.order_by(Chat.created_at.desc()).all()
        
        # ترکیب و مرتب‌سازی فعالیت‌ها
        activities = []
        
        # فعالیت‌های وب‌سایت
        for website in websites:
            activities.append({
                "id": f"website_{website.id}",
                "type": "website_added",
                "title": "وب‌سایت جدید اضافه شد",
                "description": f"وب‌سایت {website.name or website.domain} به سیستم اضافه شد",
                "website": website.name or website.domain,
                "timestamp": website.created_at.isoformat() if website.created_at else None,
                "status": "completed",
                "icon": "Language",
                "color": "primary"
            })
            
            # اگر وب‌سایت به‌روزرسانی شده
            if website.updated_at and website.updated_at != website.created_at:
                activities.append({
                    "id": f"website_update_{website.id}",
                    "type": "website_updated",
                    "title": "وب‌سایت به‌روزرسانی شد",
                    "description": f"تنظیمات وب‌سایت {website.name or website.domain} به‌روزرسانی شد",
                    "website": website.name or website.domain,
                    "timestamp": website.updated_at.isoformat(),
                    "status": "completed",
                    "icon": "Edit",
                    "color": "primary"
                })
            
            # اگر کراول تکمیل شده
            if website.status == "ready" and website.crawl_info:
                activities.append({
                    "id": f"crawl_{website.id}",
                    "type": "crawl_completed",
                    "title": "کراول تکمیل شد",
                    "description": f"کراول وب‌سایت {website.name or website.domain} با موفقیت تکمیل شد",
                    "website": website.name or website.domain,
                    "timestamp": website.updated_at.isoformat() if website.updated_at else website.created_at.isoformat(),
                    "status": "completed",
                    "icon": "Language",
                    "color": "info"
                })
        
        # فعالیت‌های چت
        for chat in chats:
            # بررسی اینکه آیا این چت پیام دارد یا نه
            has_messages = db.query(Message).filter(Message.chat_id == chat.id).first() is not None
            
            if has_messages:
                activities.append({
                    "id": f"conversation_end_{chat.id}",
                    "type": "conversation_ended",
                    "title": "گفتگو پایان یافت",
                    "description": f"گفتگوی وب‌سایت {chat.website.name or chat.website.domain} پایان یافت",
                    "website": chat.website.name or chat.website.domain,
                    "timestamp": chat.created_at.isoformat(),
                    "status": "completed",
                    "icon": "Chat",
                    "color": "secondary"
                })
            else:
                activities.append({
                    "id": f"conversation_start_{chat.id}",
                    "type": "conversation_started",
                    "title": "گفتگوی جدید شروع شد",
                    "description": f"گفتگوی جدید در وب‌سایت {chat.website.name or chat.website.domain} شروع شد",
                    "website": chat.website.name or chat.website.domain,
                    "timestamp": chat.created_at.isoformat(),
                    "status": "active",
                    "icon": "Chat",
                    "color": "success"
                })
        
        # مرتب‌سازی بر اساس timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # محاسبه آمار
        total_websites = db.query(Website).filter(Website.owner_id == current_user.id).count()
        total_conversations = db.query(Chat).join(Website).filter(Website.owner_id == current_user.id).count()
        completed_crawls = db.query(Website).filter(
            and_(Website.owner_id == current_user.id, Website.status == "ready")
        ).count()
        
        stats = {
            "websites_added": total_websites,
            "conversations": total_conversations,
            "crawls_completed": completed_crawls,
            "settings_changed": 0  # این می‌تواند بر اساس log های واقعی محاسبه شود
        }
        
        return {
            "activities": activities,
            "stats": stats,
            "total": len(activities),
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت تاریخچه کاربر: {str(e)}")
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

# ==================== مدیریت کاربران ====================

@router.get("/admin/users")
async def get_admin_users(
    page: int = 1,
    limit: int = 20,
    search: str = None,
    role: str = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت لیست کاربران برای ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        offset = (page - 1) * limit
        
        # ایجاد query base
        query = db.query(User)
        
        # فیلتر بر اساس جستجو
        if search:
            query = query.filter(User.email.contains(search))
        
        # فیلتر بر اساس نقش
        if role and role != 'all':
            query = query.filter(User.role == role)
        
        # فیلتر بر اساس وضعیت
        if status and status != 'all':
            if status == 'active':
                query = query.filter(User.is_active == True)
            elif status == 'inactive':
                query = query.filter(User.is_active == False)
        
        # شمارش کل
        total = query.count()
        
        # دریافت کاربران
        users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "websites_count": db.query(Website).filter(Website.owner_id == user.id).count(),
                    "conversations_count": db.query(Chat).join(Website).filter(Website.owner_id == user.id).count()
                }
                for user in users
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت لیست کاربران: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/admin/users/{user_id}")
async def update_admin_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """به‌روزرسانی کاربر توسط ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # پیدا کردن کاربر
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="کاربر یافت نشد")
        
        # به‌روزرسانی فیلدها
        if 'role' in user_data:
            user.role = user_data['role']
        if 'is_active' in user_data:
            user.is_active = user_data['is_active']
        if 'is_verified' in user_data:
            user.is_verified = user_data['is_verified']
        
        db.commit()
        
        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "message": "کاربر با موفقیت به‌روزرسانی شد"
        }
        
    except Exception as e:
        logger.error(f"خطا در به‌روزرسانی کاربر: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/admin/users/{user_id}/password")
async def change_user_password(
    user_id: int,
    password_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تغییر کلمه عبور کاربر توسط ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # پیدا کردن کاربر
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="کاربر یافت نشد")
        
        # بررسی کلمه عبور جدید
        new_password = password_data.get('new_password')
        if not new_password:
            raise HTTPException(status_code=400, detail="کلمه عبور جدید الزامی است")
        
        if len(new_password) < 6:
            raise HTTPException(status_code=400, detail="کلمه عبور باید حداقل 6 کاراکتر باشد")
        
        # هش کردن کلمه عبور جدید
        from .auth import get_password_hash
        user.hashed_password = get_password_hash(new_password)
        
        db.commit()
        
        return {
            "id": user.id,
            "email": user.email,
            "message": "کلمه عبور کاربر با موفقیت تغییر یافت"
        }
        
    except Exception as e:
        logger.error(f"خطا در تغییر کلمه عبور کاربر: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/users/{user_id}")
async def delete_admin_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """حذف کاربر توسط ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # بررسی اینکه کاربر خودش را حذف نکند
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="نمی‌توانید حساب خودتان را حذف کنید")
        
        # پیدا کردن کاربر
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="کاربر یافت نشد")
        
        # حذف وب‌سایت‌های کاربر
        db.query(Website).filter(Website.owner_id == user_id).delete()
        
        # حذف کاربر
        db.delete(user)
        db.commit()
        
        return {"message": "کاربر با موفقیت حذف شد"}
        
    except Exception as e:
        logger.error(f"خطا در حذف کاربر: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== مدیریت وب‌سایت‌ها ====================

@router.get("/admin/websites")
async def get_admin_websites(
    page: int = 1,
    limit: int = 20,
    search: str = None,
    status: str = None,
    owner_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت لیست وب‌سایت‌ها برای ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        offset = (page - 1) * limit
        
        # ایجاد query base
        query = db.query(Website)
        
        # فیلتر بر اساس جستجو
        if search:
            query = query.filter(
                or_(
                    Website.name.contains(search),
                    Website.domain.contains(search),
                    Website.url.contains(search)
                )
            )
        
        # فیلتر بر اساس وضعیت
        if status and status != 'all':
            query = query.filter(Website.status == status)
        
        # فیلتر بر اساس مالک
        if owner_id:
            query = query.filter(Website.owner_id == owner_id)
        
        # شمارش کل
        total = query.count()
        
        # دریافت وب‌سایت‌ها
        websites = query.order_by(Website.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "websites": [
                {
                    "id": website.id,
                    "name": website.name or website.domain,
                    "domain": website.domain,
                    "url": website.url,
                    "status": website.status,
                    "owner_email": website.owner.email,
                    "owner_id": website.owner_id,
                    "created_at": website.created_at.isoformat(),
                    "updated_at": website.updated_at.isoformat() if website.updated_at else None,
                    "conversations_count": db.query(Chat).filter(Chat.website_id == website.id).count(),
                    "messages_count": db.query(Message).join(Chat).filter(Chat.website_id == website.id).count(),
                    "crawl_info": website.crawl_info
                }
                for website in websites
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت لیست وب‌سایت‌ها: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/admin/websites/{website_id}")
async def update_admin_website(
    website_id: int,
    website_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """به‌روزرسانی وب‌سایت توسط ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # پیدا کردن وب‌سایت
        website = db.query(Website).filter(Website.id == website_id).first()
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
        
        # به‌روزرسانی فیلدها
        if 'status' in website_data:
            website.status = website_data['status']
        if 'name' in website_data:
            website.name = website_data['name']
        if 'crawl_settings' in website_data:
            website.crawl_settings = website_data['crawl_settings']
        if 'rag_settings' in website_data:
            website.rag_settings = website_data['rag_settings']
        
        db.commit()
        
        return {
            "id": website.id,
            "name": website.name,
            "domain": website.domain,
            "status": website.status,
            "updated_at": website.updated_at.isoformat() if website.updated_at else None
        }
        
    except Exception as e:
        logger.error(f"خطا در به‌روزرسانی وب‌سایت: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/websites/{website_id}")
async def delete_admin_website(
    website_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """حذف وب‌سایت توسط ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # پیدا کردن وب‌سایت
        website = db.query(Website).filter(Website.id == website_id).first()
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
        
        # حذف چت‌های مربوطه
        db.query(Chat).filter(Chat.website_id == website_id).delete()
        
        # حذف وب‌سایت
        db.delete(website)
        db.commit()
        
        return {"message": "وب‌سایت با موفقیت حذف شد"}
        
    except Exception as e:
        logger.error(f"خطا در حذف وب‌سایت: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== مدیریت گفتگوها ====================

@router.get("/admin/conversations")
async def get_admin_conversations(
    page: int = 1,
    limit: int = 20,
    search: str = None,
    website_id: int = None,
    user_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت لیست گفتگوها برای ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        offset = (page - 1) * limit
        
        # ایجاد query base با join
        query = db.query(Chat).join(Website)
        
        # فیلتر بر اساس وب‌سایت
        if website_id:
            query = query.filter(Chat.website_id == website_id)
        
        # فیلتر بر اساس کاربر
        if user_id:
            query = query.filter(Website.owner_id == user_id)
        
        # شمارش کل
        total = query.count()
        
        # دریافت گفتگوها
        conversations = query.order_by(Chat.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "conversations": [
                {
                    "id": chat.id,
                    "session_id": chat.session_id,
                    "website_name": chat.website.name or chat.website.domain,
                    "website_id": chat.website_id,
                    "owner_email": chat.website.owner.email,
                    "owner_id": chat.website.owner_id,
                    "created_at": chat.created_at.isoformat(),
                    "updated_at": chat.created_at.isoformat(),  # Chat model doesn't have updated_at
                    "messages_count": db.query(Message).filter(Message.chat_id == chat.id).count(),
                    "last_message": db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at.desc()).first()
                }
                for chat in conversations
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت لیست گفتگوها: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/conversations/{conversation_id}/messages")
async def get_admin_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت پیام‌های یک گفتگو برای ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # پیدا کردن گفتگو
        chat = db.query(Chat).filter(Chat.id == conversation_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="گفتگو یافت نشد")
        
        # دریافت پیام‌ها
        messages = db.query(Message).filter(Message.chat_id == conversation_id).order_by(Message.created_at.asc()).all()
        
        return {
            "conversation": {
                "id": chat.id,
                "session_id": chat.session_id,
                "website_name": chat.website.name or chat.website.domain,
                "owner_email": chat.website.owner.email,
                "created_at": chat.created_at.isoformat()
            },
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت پیام‌های گفتگو: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/conversations/{conversation_id}")
async def delete_admin_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """حذف گفتگو توسط ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # پیدا کردن گفتگو
        chat = db.query(Chat).filter(Chat.id == conversation_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="گفتگو یافت نشد")
        
        # حذف پیام‌های گفتگو
        db.query(Message).filter(Message.chat_id == conversation_id).delete()
        
        # حذف گفتگو
        db.delete(chat)
        db.commit()
        
        return {"message": "گفتگو با موفقیت حذف شد"}
        
    except Exception as e:
        logger.error(f"خطا در حذف گفتگو: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/system-settings")
async def get_admin_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت تنظیمات سیستم برای ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # دریافت تنظیمات از service
        system_settings = SystemSettingsService.get_all_settings(db)
        
        return system_settings
        
    except Exception as e:
        logger.error(f"Error getting system settings: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در دریافت تنظیمات سیستم")

@router.get("/system-settings")
async def get_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت تنظیمات عمومی سیستم برای همه کاربران"""
    try:
        # دریافت تنظیمات عمومی که همه کاربران می‌توانند ببینند
        public_settings = {
            "siteName": SystemSettingsService.get_setting(db, "siteName", "RAG Chatbot System"),
            "siteDescription": SystemSettingsService.get_setting(db, "siteDescription", "سیستم چت‌بات هوشمند"),
            "maintenanceMode": SystemSettingsService.get_setting(db, "maintenanceMode", False),
            "debugMode": SystemSettingsService.get_setting(db, "debugMode", False),
            # تنظیمات مدل‌های چت‌بات
            "enableOpenAI": SystemSettingsService.get_setting(db, "enableOpenAI", True),
            "enableGemini": SystemSettingsService.get_setting(db, "enableGemini", True),
            "enableLocal": SystemSettingsService.get_setting(db, "enableLocal", False)
        }
        
        return public_settings
        
    except Exception as e:
        logger.error(f"Error getting public system settings: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در دریافت تنظیمات سیستم")

@router.put("/admin/system-settings")
async def update_admin_system_settings(
    settings: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """به‌روزرسانی تنظیمات سیستم برای ادمین"""
    try:
        # بررسی نقش ادمین
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
        
        # به‌روزرسانی تنظیمات با استفاده از service
        success_count = 0
        for key, value in settings.items():
            if SystemSettingsService.set_setting(db, key, value):
                success_count += 1
        
        logger.info(f"System settings updated by admin {current_user.email}: {success_count} settings updated")
        
        return {"message": f"تنظیمات سیستم با موفقیت به‌روزرسانی شد ({success_count} تنظیم)"}
        
    except Exception as e:
        logger.error(f"Error updating system settings: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در به‌روزرسانی تنظیمات سیستم")
