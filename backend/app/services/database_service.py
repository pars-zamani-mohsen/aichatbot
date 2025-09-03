"""
سرویس بهینه‌سازی دیتابیس با async operations
"""

import asyncio
from typing import List, Optional, Any, Dict, Union
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.database.database import get_db, get_async_db
from app.services.cache_service import cache_service, memoize
from app.models import User, Website, Chat, Message, UserSettings, SystemSettings

logger = logging.getLogger(__name__)


class DatabaseService:
    """سرویس بهینه‌سازی دیتابیس"""
    
    def __init__(self):
        self.cache_service = cache_service
    
    @memoize(ttl=300)  # Cache برای 5 دقیقه
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        دریافت کاربر بر اساس ID با cache
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            کاربر یا None
        """
        try:
            db = next(get_db())
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
        finally:
            db.close()
    
    @memoize(ttl=600)  # Cache برای 10 دقیقه
    def get_user_websites(self, user_id: int, status: Optional[str] = None) -> List[Website]:
        """
        دریافت وب‌سایت‌های کاربر با cache
        
        Args:
            user_id: شناسه کاربر
            status: وضعیت وب‌سایت (اختیاری)
            
        Returns:
            لیست وب‌سایت‌ها
        """
        try:
            db = next(get_db())
            query = db.query(Website).filter(Website.owner_id == user_id)
            
            if status:
                query = query.filter(Website.status == status)
            
            # استفاده از selectinload برای بهینه‌سازی
            return query.options(selectinload(Website.owner)).all()
        except Exception as e:
            logger.error(f"Error getting websites for user {user_id}: {e}")
            return []
        finally:
            db.close()
    
    def get_user_chats_optimized(self, user_id: int, website_id: Optional[int] = None, 
                                limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        دریافت چت‌های کاربر با بهینه‌سازی
        
        Args:
            user_id: شناسه کاربر
            website_id: شناسه وب‌سایت (اختیاری)
            limit: تعداد نتایج
            offset: شروع از کدام نتیجه
            
        Returns:
            لیست چت‌ها با اطلاعات اضافی
        """
        try:
            db = next(get_db())
            
            # Query بهینه با join
            query = db.query(
                Chat.id,
                Chat.session_id,
                Chat.created_at,
                Chat.updated_at,
                Website.name.label('website_name'),
                Website.url.label('website_url'),
                func.count(Message.id).label('message_count')
            ).join(Website, Chat.website_id == Website.id)\
             .outerjoin(Message, Chat.id == Message.chat_id)\
             .filter(Website.owner_id == user_id)
            
            if website_id:
                query = query.filter(Chat.website_id == website_id)
            
            # Group by و ordering
            result = query.group_by(Chat.id, Website.name, Website.url)\
                         .order_by(desc(Chat.updated_at))\
                         .limit(limit)\
                         .offset(offset)\
                         .all()
            
            # تبدیل به دیکشنری
            chats = []
            for row in result:
                chats.append({
                    'id': row.id,
                    'session_id': row.session_id,
                    'created_at': row.created_at,
                    'updated_at': row.updated_at,
                    'website_name': row.website_name,
                    'website_url': row.website_url,
                    'message_count': row.message_count
                })
            
            return chats
            
        except Exception as e:
            logger.error(f"Error getting chats for user {user_id}: {e}")
            return []
        finally:
            db.close()
    
    def get_chat_messages_optimized(self, chat_id: int, limit: int = 100, 
                                   offset: int = 0) -> List[Message]:
        """
        دریافت پیام‌های چت با بهینه‌سازی
        
        Args:
            chat_id: شناسه چت
            limit: تعداد نتایج
            offset: شروع از کدام نتیجه
            
        Returns:
            لیست پیام‌ها
        """
        try:
            db = next(get_db())
            
            # Query بهینه با ordering
            messages = db.query(Message)\
                        .filter(Message.chat_id == chat_id)\
                        .order_by(asc(Message.created_at))\
                        .limit(limit)\
                        .offset(offset)\
                        .all()
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages for chat {chat_id}: {e}")
            return []
        finally:
            db.close()
    
    def get_dashboard_stats_optimized(self, user_id: int) -> Dict[str, Any]:
        """
        دریافت آمار داشبورد با بهینه‌سازی
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            دیکشنری آمار
        """
        try:
            db = next(get_db())
            
            # آمار وب‌سایت‌ها
            website_stats = db.query(
                Website.status,
                func.count(Website.id).label('count')
            ).filter(Website.owner_id == user_id)\
             .group_by(Website.status)\
             .all()
            
            # آمار چت‌ها
            chat_stats = db.query(
                func.count(Chat.id).label('total_chats'),
                func.count(Chat.id).filter(Chat.updated_at > func.date_sub(func.now(), 1)).label('recent_chats')
            ).join(Website, Chat.website_id == Website.id)\
             .filter(Website.owner_id == user_id)\
             .first()
            
            # آمار پیام‌ها
            message_stats = db.query(
                func.count(Message.id).label('total_messages'),
                func.count(Message.id).filter(Message.created_at > func.date_sub(func.now(), 1)).label('recent_messages')
            ).join(Chat, Message.chat_id == Chat.id)\
             .join(Website, Chat.website_id == Website.id)\
             .filter(Website.owner_id == user_id)\
             .first()
            
            # تبدیل به دیکشنری
            stats = {
                'websites': {row.status: row.count for row in website_stats},
                'chats': {
                    'total': chat_stats.total_chats or 0,
                    'recent': chat_stats.recent_chats or 0
                },
                'messages': {
                    'total': message_stats.total_messages or 0,
                    'recent': message_stats.recent_messages or 0
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats for user {user_id}: {e}")
            return {}
        finally:
            db.close()
    
    def bulk_create_websites(self, websites_data: List[Dict[str, Any]], user_id: int) -> List[Website]:
        """
        ایجاد چندین وب‌سایت به صورت bulk
        
        Args:
            websites_data: لیست داده‌های وب‌سایت
            user_id: شناسه کاربر
            
        Returns:
            لیست وب‌سایت‌های ایجاد شده
        """
        try:
            db = next(get_db())
            
            websites = []
            for data in websites_data:
                website = Website(
                    url=data['url'],
                    name=data.get('name', ''),
                    description=data.get('description', ''),
                    owner_id=user_id,
                    status='pending'
                )
                websites.append(website)
            
            db.add_all(websites)
            db.commit()
            
            # Invalidate cache
            self.cache_service.invalidate_by_pattern(f"user_websites:{user_id}")
            
            return websites
            
        except Exception as e:
            logger.error(f"Error bulk creating websites for user {user_id}: {e}")
            db.rollback()
            return []
        finally:
            db.close()
    
    def bulk_update_websites(self, website_updates: List[Dict[str, Any]]) -> bool:
        """
        به‌روزرسانی چندین وب‌سایت به صورت bulk
        
        Args:
            website_updates: لیست به‌روزرسانی‌ها
            
        Returns:
            True در صورت موفقیت
        """
        try:
            db = next(get_db())
            
            for update in website_updates:
                website_id = update['id']
                website = db.query(Website).filter(Website.id == website_id).first()
                
                if website:
                    for key, value in update.items():
                        if key != 'id' and hasattr(website, key):
                            setattr(website, key, value)
            
            db.commit()
            
            # Invalidate cache
            self.cache_service.invalidate_by_pattern("user_websites:*")
            
            return True
            
        except Exception as e:
            logger.error(f"Error bulk updating websites: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    async def async_get_user_websites(self, user_id: int) -> List[Website]:
        """
        دریافت وب‌سایت‌های کاربر به صورت async
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            لیست وب‌سایت‌ها
        """
        try:
            async for db in get_async_db():
                # استفاده از async query
                from sqlalchemy import select
                from sqlalchemy.ext.asyncio import AsyncSession
                
                stmt = select(Website).filter(Website.owner_id == user_id)
                result = await db.execute(stmt)
                websites = result.scalars().all()
                
                return websites
                
        except Exception as e:
            logger.error(f"Error async getting websites for user {user_id}: {e}")
            return []
    
    def get_system_performance_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار عملکرد سیستم
        
        Returns:
            دیکشنری آمار عملکرد
        """
        try:
            db = next(get_db())
            
            # آمار کلی
            total_users = db.query(func.count(User.id)).scalar()
            total_websites = db.query(func.count(Website.id)).scalar()
            total_chats = db.query(func.count(Chat.id)).scalar()
            total_messages = db.query(func.count(Message.id)).scalar()
            
            # آمار فعال
            active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
            ready_websites = db.query(func.count(Website.id)).filter(Website.status == 'ready').scalar()
            
            # آمار اخیر
            recent_chats = db.query(func.count(Chat.id))\
                            .filter(Chat.created_at > func.date_sub(func.now(), 1))\
                            .scalar()
            
            recent_messages = db.query(func.count(Message.id))\
                               .filter(Message.created_at > func.date_sub(func.now(), 1))\
                               .scalar()
            
            stats = {
                'total_users': total_users or 0,
                'total_websites': total_websites or 0,
                'total_chats': total_chats or 0,
                'total_messages': total_messages or 0,
                'active_users': active_users or 0,
                'ready_websites': ready_websites or 0,
                'recent_chats': recent_chats or 0,
                'recent_messages': recent_messages or 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system performance stats: {e}")
            return {}
        finally:
            db.close()
    
    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """
        پاکسازی داده‌های قدیمی
        
        Args:
            days: تعداد روزهای نگهداری
            
        Returns:
            دیکشنری تعداد آیتم‌های حذف شده
        """
        try:
            db = next(get_db())
            
            cleanup_date = func.date_sub(func.now(), days)
            
            # حذف چت‌های قدیمی
            old_chats = db.query(Chat).filter(Chat.updated_at < cleanup_date).all()
            old_chat_ids = [chat.id for chat in old_chats]
            
            if old_chat_ids:
                # حذف پیام‌های مربوطه
                db.query(Message).filter(Message.chat_id.in_(old_chat_ids)).delete(synchronize_session=False)
                
                # حذف چت‌ها
                db.query(Chat).filter(Chat.id.in_(old_chat_ids)).delete(synchronize_session=False)
            
            # حذف اعلان‌های قدیمی
            old_notifications = db.query(func.count(Message.id))\
                                 .filter(Message.created_at < cleanup_date)\
                                 .scalar()
            
            if old_notifications:
                db.query(Message).filter(Message.created_at < cleanup_date).delete(synchronize_session=False)
            
            db.commit()
            
            # Invalidate cache
            self.cache_service.invalidate_by_pattern("*")
            
            return {
                'old_chats': len(old_chat_ids),
                'old_notifications': old_notifications or 0
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            db.rollback()
            return {}
        finally:
            db.close()


# Instance سراسری
db_service = DatabaseService()

# توابع کمکی
get_user_by_id = db_service.get_user_by_id
get_user_websites = db_service.get_user_websites
get_user_chats_optimized = db_service.get_user_chats_optimized
get_chat_messages_optimized = db_service.get_chat_messages_optimized
get_dashboard_stats_optimized = db_service.get_dashboard_stats_optimized
bulk_create_websites = db_service.bulk_create_websites
bulk_update_websites = db_service.bulk_update_websites
async_get_user_websites = db_service.async_get_user_websites
get_system_performance_stats = db_service.get_system_performance_stats
cleanup_old_data = db_service.cleanup_old_data
