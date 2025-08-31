from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, WebSocketException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Dict, Optional
import json
import uuid
from ..database.database import get_db
from ..database import models
from ..database.models import User
from . import schemas
from .auth import get_current_user
from ..services.rag import RAGService
from ..config import settings
from jose import JWTError, jwt
from ..core.chatbot_factory import ChatbotFactory
from ..services.notification_service import NotificationService
from ..services.system_settings_service import SystemSettingsService
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

def get_collection_name_from_website_id(db: Session, website_id: int) -> str:
    """تبدیل website_id به collection_name"""
    try:
        logger.info(f"جستجوی وب‌سایت با شناسه {website_id}")
        
        # جستجوی مستقیم با id
        website = db.query(models.Website).get(website_id)
        
        if not website:
            logger.error(f"وب‌سایت با شناسه {website_id} یافت نشد")
            # بررسی همه وب‌سایت‌ها برای دیباگ
            all_websites = db.query(models.Website).all()
            logger.info(f"تعداد کل وب‌سایت‌ها در دیتابیس: {len(all_websites)}")
            for w in all_websites:
                logger.info(f"وب‌سایت موجود - ID: {w.id}, URL: {w.url}, Status: {w.status}")
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="وب‌سایت یافت نشد"
            )
            
        logger.info(f"وب‌سایت یافت شد - وضعیت: {website.status}, کالکشن: {website.collection_name}")
        
        if website.status != "ready":
            logger.error(f"وب‌سایت با شناسه {website_id} هنوز آماده نیست (وضعیت: {website.status})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"وب‌سایت هنوز آماده نیست (وضعیت: {website.status})"
            )
            
        if not website.collection_name:
            logger.error(f"کالکشن برای وب‌سایت {website_id} ایجاد نشده است")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="کالکشن برای این وب‌سایت ایجاد نشده است"
            )
            
        logger.info(f"کالکشن {website.collection_name} برای وب‌سایت {website_id} یافت شد")
        return website.collection_name
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در دریافت نام کالکشن: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در دریافت نام کالکشن: {str(e)}"
        )

# مدیریت اتصالات WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}  # {session_id: WebSocket}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)

manager = ConnectionManager()

@router.post("/", response_model=schemas.ChatResponse)
async def create_chat(
    chat: schemas.ChatCreate,
    chatbot_type: str = "openai",
    db: Session = Depends(get_db)
):
    """ارسال پرسش به چت‌بات"""
    try:
        logger.info(f"درخواست چت جدید - وب‌سایت: {chat.website_id}, نوع چت‌بات: {chatbot_type}")
        
        # بررسی وجود سایت
        website = db.query(models.Website).filter(
            models.Website.id == chat.website_id,
            models.Website.status == "ready"
        ).first()
        
        if website is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="سایت یافت نشد یا هنوز آماده نیست"
            )
        
        # دریافت collection_name از website_id
        collection_name = get_collection_name_from_website_id(db, chat.website_id)
        logger.info(f"استفاده از کالکشن: {collection_name}")
        
        # دریافت تنظیمات RAG
        rag_settings = SystemSettingsService.get_rag_settings(db)
        default_k = rag_settings.get('default_k', 5)
        max_response_length = rag_settings.get('max_response_length', 500)
        default_temperature = rag_settings.get('default_temperature', 0.7)
        default_language = rag_settings.get('default_language', 'fa')
        
        # ایجاد چت‌بات با collection_name صحیح و تنظیمات RAG
        chatbot = ChatbotFactory.create_chatbot(
            chatbot_type=chatbot_type,
            collection_name=collection_name,
            k=default_k,
            max_length=max_response_length,
            temperature=default_temperature,
            language=default_language
        )
        logger.info("چت‌بات با موفقیت ایجاد شد")
        
        # بررسی وجود چت قبلی
        db_chat = None
        if chat.chat_id:
            db_chat = db.query(models.Chat).filter(
                models.Chat.id == chat.chat_id,
                models.Chat.website_id == chat.website_id
            ).first()
            logger.info(f"چت قبلی یافت شد: {db_chat.id if db_chat else 'خیر'}")
        
        # اگر چت قبلی وجود نداشت، یک چت جدید ایجاد کن
        if not db_chat:
            db_chat = models.Chat(
                website_id=chat.website_id,
                session_id=chat.session_id
            )
            db.add(db_chat)
            db.commit()
            db.refresh(db_chat)
            logger.info(f"چت جدید ایجاد شد: {db_chat.id}")
            
            # ارسال اعلان چت جدید
            NotificationService.notify_new_conversation(
                db=db,
                user_id=website.owner_id,
                website_name=website.name or website.url,
                chat_id=db_chat.id
            )
        
        # ذخیره پیام کاربر
        user_message = models.Message(
            chat_id=db_chat.id,
            role="user",
            content=chat.message
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        logger.info(f"پیام کاربر ذخیره شد - ID: {user_message.id}, Content: {user_message.content[:100]}...")
        
        # ارسال پرسش به چت‌بات
        logger.info(f"ارسال پرسش به چت‌بات: {chat.message[:100]}...")
        response = chatbot.ask(chat.message)
        logger.info(f"پاسخ از چت‌بات دریافت شد - Answer: {response['answer'][:100]}...")
        logger.info(f"منابع پاسخ: {response['sources']}")
        
        # بررسی ساختار پاسخ
        if not isinstance(response, dict):
            logger.error(f"پاسخ چت‌بات در فرمت نامعتبر است: {type(response)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="پاسخ چت‌بات در فرمت نامعتبر است"
            )
        
        if 'answer' not in response:
            logger.error(f"پاسخ چت‌بات فیلد 'answer' ندارد: {response}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="پاسخ چت‌بات فیلد 'answer' ندارد"
            )
        
        # ذخیره پاسخ چت‌بات
        try:
            assistant_message = models.Message(
                chat_id=db_chat.id,
                role="assistant",
                content=response["answer"],
                sources=response.get("sources", [])
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            logger.info(f"پاسخ چت‌بات ذخیره شد - ID: {assistant_message.id}, Content: {assistant_message.content[:100]}...")
            logger.info(f"منابع ذخیره شده: {assistant_message.sources}")
        except Exception as e:
            logger.error(f"خطا در ذخیره پاسخ چت‌بات: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"خطا در ذخیره پاسخ چت‌بات: {str(e)}"
            )
        
        # دریافت پیام‌های چت
        messages = db.query(models.Message).filter(
            models.Message.chat_id == db_chat.id
        ).order_by(models.Message.created_at).all()
        
        logger.info(f"تعداد پیام‌های دریافت شده: {len(messages)}")
        for msg in messages:
            logger.info(f"پیام - ID: {msg.id}, Role: {msg.role}, Content: {msg.content[:100]}...")
            if msg.role == "assistant":
                logger.info(f"منابع پیام: {msg.sources}")
        
        # تبدیل پیام‌ها به فرمت مناسب
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at,
                "sources": msg.sources if msg.role == "assistant" else None
            }
            formatted_messages.append(formatted_msg)
            logger.info(f"پیام فرمت شده - Role: {formatted_msg['role']}, Content: {formatted_msg['content'][:100]}...")
            if formatted_msg['role'] == "assistant":
                logger.info(f"منابع پیام فرمت شده: {formatted_msg['sources']}")
        
        response_data = {
            "id": db_chat.id,
            "website_id": db_chat.website_id,
            "message": chat.message,
            "response": response["answer"],
            "session_id": db_chat.session_id,
            "created_at": db_chat.created_at,
            "error": None,
            "messages": formatted_messages
        }
        
        logger.info(f"پاسخ نهایی - تعداد پیام‌ها: {len(formatted_messages)}")
        return response_data
        
    except Exception as e:
        logger.error(f"خطا در پردازش درخواست چت: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/list", response_model=List[schemas.Chat])
async def get_chats(
    website_id: Optional[int] = Query(None, description="فیلتر بر اساس شناسه وب‌سایت"),
    skip: int = Query(0, description="تعداد رکوردهای رد شده"),
    limit: int = Query(100, description="حداکثر تعداد رکوردهای برگشتی"),
    db: Session = Depends(get_db)
):
    """دریافت لیست چت‌ها"""
    try:
        query = db.query(models.Chat)
        if website_id is not None:
            query = query.filter(models.Chat.website_id == website_id)
        chats = query.offset(skip).limit(limit).all()
        return chats
        
    except Exception as e:
        logger.error(f"خطا در دریافت لیست چت‌ها: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{chat_id}", response_model=schemas.Chat)
async def get_chat(
    chat_id: int,
    db: Session = Depends(get_db)
):
    """دریافت اطلاعات یک چت"""
    try:
        chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="چت یافت نشد")
        return chat
        
    except Exception as e:
        logger.error(f"خطا در دریافت اطلاعات چت: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{chat_id}/messages", response_model=List[schemas.Message])
async def read_messages(
    chat_id: int,
    skip: int = Query(0, description="تعداد رکوردهای رد شده"),
    limit: int = Query(100, description="حداکثر تعداد رکوردهای برگشتی"),
    db: Session = Depends(get_db)
):
    """دریافت پیام‌های یک چت"""
    messages = db.query(models.Message).filter(
        models.Message.chat_id == chat_id
    ).offset(skip).limit(limit).all()
    
    return messages

@router.websocket("/ws/{website_id}")
async def websocket_endpoint(websocket: WebSocket, website_id: int, db: Session = Depends(get_db)):
    # --- احراز هویت ---
    token = None
    for header, value in websocket.headers.items():
        if header.lower() == "authorization":
            if value.startswith("Bearer "):
                token = value[7:]
            else:
                token = value
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_email = payload.get("sub")
        if user_email is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    # --- پایان احراز هویت ---

    # بررسی وجود سایت
    website = db.query(models.Website).filter(
        models.Website.id == website_id,
        models.Website.status == "ready"
    ).first()
    
    if website is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # ایجاد شناسه جلسه
    session_id = str(uuid.uuid4())
    
    # ایجاد چت جدید
    db_chat = models.Chat(
        website_id=website_id,
        session_id=session_id
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    
    # اتصال WebSocket
    await manager.connect(websocket, session_id)
    
    try:
        # ایجاد سرویس RAG با collection_name صحیح
        collection_name = get_collection_name_from_website_id(db, website_id)
        
        # دریافت وب‌سایت برای تنظیمات RAG
        website = db.query(models.Website).filter(models.Website.id == website_id).first()
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
        
        # دریافت تنظیمات RAG
        rag_settings = website.rag_settings or {}
        k = rag_settings.get("k", 5)
        max_response_length = rag_settings.get("max_response_length", 500)
        temperature = rag_settings.get("temperature", 0.7)
        tone = rag_settings.get("tone", "professional")
        language = rag_settings.get("language", "persian")
        include_sources = rag_settings.get("include_sources", True)
        max_context_length = rag_settings.get("max_context_length", 2000)
        
        rag_service = RAGService(collection_name, rag_settings)
        
        while True:
            # دریافت پیام از کاربر
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # ذخیره پیام کاربر
            user_message = models.Message(
                chat_id=db_chat.id,
                role="user",
                content=message_data["message"]
            )
            db.add(user_message)
            db.commit()
            
            # دریافت پاسخ از RAG
            answer, sources = rag_service.get_answer(message_data["message"])
            
            # ذخیره پاسخ
            assistant_message = models.Message(
                chat_id=db_chat.id,
                role="assistant",
                content=answer,
                sources=sources
            )
            db.add(assistant_message)
            db.commit()
            
            # ارسال پاسخ به کاربر
            await manager.send_message(
                json.dumps({
                    "message": answer,
                    "sources": sources
                }),
                session_id
            )
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        manager.disconnect(session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/websites/{website_id}/conversations")
async def get_website_conversations(
    website_id: int,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت لیست مکالمات یک وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت
        website = db.query(models.Website).filter(
            and_(models.Website.id == website_id, models.Website.owner_id == current_user.id)
        ).first()
        
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
        
        # دریافت مکالمات
        offset = (page - 1) * limit
        conversations = db.query(models.Chat).filter(
            models.Chat.website_id == website_id
        ).order_by(models.Chat.created_at.desc()).offset(offset).limit(limit).all()
        
        # شمارش کل
        total_conversations = db.query(models.Chat).filter(models.Chat.website_id == website_id).count()
        
        result = []
        for chat in conversations:
            # آخرین پیام
            last_message = db.query(models.Message).filter(
                models.Message.chat_id == chat.id
            ).order_by(models.Message.created_at.desc()).first()
            
            # تعداد پیام‌ها
            message_count = db.query(models.Message).filter(models.Message.chat_id == chat.id).count()
            
            result.append({
                "chat_id": chat.id,
                "session_id": chat.session_id,
                "created_at": chat.created_at.isoformat(),
                "last_message": last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else (last_message.content if last_message else ""),
                "message_count": message_count,
                "last_activity": last_message.created_at.isoformat() if last_message else chat.created_at.isoformat()
            })
        
        return {
            "conversations": result,
            "total": total_conversations,
            "page": page,
            "limit": limit,
            "total_pages": (total_conversations + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت مکالمات: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/conversations")
async def get_user_conversations(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = Query(None, description="فیلتر بر اساس وضعیت"),
    search: Optional[str] = Query(None, description="جستجو در پیام‌ها"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت لیست مکالمات کاربر"""
    try:
        # دریافت وب‌سایت‌های کاربر
        user_websites = db.query(models.Website).filter(
            models.Website.owner_id == current_user.id
        ).all()
        
        if not user_websites:
            return {
                "conversations": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0
            }
        
        website_ids = [website.id for website in user_websites]
        
        # دریافت مکالمات
        offset = (page - 1) * limit
        query = db.query(models.Chat).filter(
            models.Chat.website_id.in_(website_ids)
        )
        
        # فیلتر بر اساس وضعیت
        if status and status != 'all':
            if status == 'active':
                # گفتگوهای فعال: گفتگوهایی که پیام دارند
                query = query.join(models.Message, models.Chat.id == models.Message.chat_id)
            elif status == 'completed':
                # گفتگوهای تکمیل شده: گفتگوهایی که پیام ندارند
                # استفاده از subquery برای یافتن چت‌هایی که پیام ندارند
                from sqlalchemy import exists
                subquery = db.query(models.Message.chat_id).filter(
                    models.Message.chat_id == models.Chat.id
                ).exists()
                query = query.filter(~subquery)
        
        conversations = query.order_by(models.Chat.created_at.desc()).offset(offset).limit(limit).all()
        
        # شمارش کل
        total_conversations = query.count()
        
        result = []
        for chat in conversations:
            # دریافت اطلاعات وب‌سایت
            website = next((w for w in user_websites if w.id == chat.website_id), None)
            
            # آخرین پیام
            last_message = db.query(models.Message).filter(
                models.Message.chat_id == chat.id
            ).order_by(models.Message.created_at.desc()).first()
            
            # تعداد پیام‌ها
            message_count = db.query(models.Message).filter(models.Message.chat_id == chat.id).count()
            
            # فیلتر جستجو - بررسی در نام وب‌سایت و محتوای پیام
            if search:
                search_lower = search.lower()
                website_name = website.name.lower() if website else ""
                message_content = last_message.content.lower() if last_message else ""
                
                if search_lower not in website_name and search_lower not in message_content:
                    continue
            
            result.append({
                "id": chat.id,
                "website": website.name if website else f"Website {chat.website_id}",
                "website_id": chat.website_id,
                "session_id": chat.session_id,
                "message_count": message_count,
                "status": "active" if message_count > 0 else "completed",  # منطق ساده برای وضعیت
                "created_at": chat.created_at.isoformat(),
                "last_message": last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else (last_message.content if last_message else ""),
                "last_activity": last_message.created_at.isoformat() if last_message else chat.created_at.isoformat()
            })
        
        return {
            "conversations": result,
            "total": total_conversations,
            "page": page,
            "limit": limit,
            "total_pages": (total_conversations + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت مکالمات کاربر: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/conversations/{conversation_id}")
async def get_user_conversation_detail(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت جزئیات یک مکالمه کاربر"""
    try:
        # بررسی مالکیت مکالمه
        chat = db.query(models.Chat).join(models.Website).filter(
            and_(
                models.Chat.id == conversation_id,
                models.Website.owner_id == current_user.id
            )
        ).first()
        
        if not chat:
            raise HTTPException(status_code=404, detail="مکالمه یافت نشد")
        
        # دریافت پیام‌ها
        messages = db.query(models.Message).filter(
            models.Message.chat_id == chat.id
        ).order_by(models.Message.created_at).all()
        
        # دریافت اطلاعات وب‌سایت
        website = db.query(models.Website).filter(models.Website.id == chat.website_id).first()
        
        # فرمت پیام‌ها
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content,
                "time": msg.created_at.strftime("%H:%M"),
                "created_at": msg.created_at.isoformat(),
                "sources": msg.sources if msg.role == "assistant" else None
            })
        
        return {
            "id": chat.id,
            "website": website.name if website else f"Website {chat.website_id}",
            "website_id": chat.website_id,
            "session_id": chat.session_id,
            "status": "active" if len(messages) > 0 else "completed",
            "created_at": chat.created_at.isoformat(),
            "message_count": len(messages),
            "messages": formatted_messages
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت جزئیات مکالمه: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/user/conversations/{conversation_id}")
async def delete_user_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """حذف یک مکالمه کاربر"""
    try:
        # بررسی مالکیت مکالمه
        chat = db.query(models.Chat).join(models.Website).filter(
            and_(
                models.Chat.id == conversation_id,
                models.Website.owner_id == current_user.id
            )
        ).first()
        
        if not chat:
            raise HTTPException(status_code=404, detail="مکالمه یافت نشد")
        
        # حذف پیام‌ها
        db.query(models.Message).filter(models.Message.chat_id == chat.id).delete()
        
        # حذف چت
        db.delete(chat)
        db.commit()
        
        return {"message": "مکالمه با موفقیت حذف شد"}
        
    except Exception as e:
        logger.error(f"خطا در حذف مکالمه: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/websites/{website_id}/export")
async def export_conversations(
    website_id: int,
    format: str = "csv",
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export مکالمات یک وب‌سایت"""
    try:
        # بررسی مالکیت وب‌سایت
        website = db.query(models.Website).filter(
            and_(models.Website.id == website_id, models.Website.owner_id == current_user.id)
        ).first()
        
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
        
        # فیلتر تاریخ
        query = db.query(models.Chat).filter(models.Chat.website_id == website_id)
        
        if start_date:
            query = query.filter(models.Chat.created_at >= start_date)
        if end_date:
            query = query.filter(models.Chat.created_at <= end_date)
        
        conversations = query.all()
        
        # آماده‌سازی داده‌ها
        export_data = []
        for chat in conversations:
            messages = db.query(models.Message).filter(models.Message.chat_id == chat.id).order_by(models.Message.created_at).all()
            
            for msg in messages:
                export_data.append({
                    "chat_id": chat.id,
                    "session_id": chat.session_id,
                    "message_id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "sources": msg.sources
                })
        
        if format.lower() == "csv":
            try:
                import pandas as pd
                from io import StringIO
                
                df = pd.DataFrame(export_data)
            except ImportError:
                raise HTTPException(status_code=500, detail="pandas برای export CSV در دسترس نیست")
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            
            from fastapi.responses import Response
            return Response(
                content=csv_buffer.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=conversations_{website.domain}_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        
        elif format.lower() == "json":
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content=export_data,
                headers={"Content-Disposition": f"attachment; filename=conversations_{website.domain}_{datetime.now().strftime('%Y%m%d')}.json"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="فرمت نامعتبر")
        
    except Exception as e:
        logger.error(f"خطا در export مکالمات: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 