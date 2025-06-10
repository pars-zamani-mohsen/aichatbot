from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, WebSocketException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import json
import uuid
from ..database.database import get_db
from ..database import models
from . import schemas
from .auth import get_current_user
from ..services.rag import RAGService
from ..config import settings
from jose import JWTError, jwt
from ..core.chatbot_factory import ChatbotFactory
import logging

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
        
        # ایجاد چت‌بات با collection_name صحیح
        chatbot = ChatbotFactory.create_chatbot(
            chatbot_type=chatbot_type,
            collection_name=collection_name
        )
        logger.info("چت‌بات با موفقیت ایجاد شد")
        
        # ایجاد چت جدید
        db_chat = models.Chat(
            website_id=chat.website_id,
            session_id=chat.session_id
        )
        db.add(db_chat)
        db.commit()
        db.refresh(db_chat)
        
        # ذخیره پیام کاربر
        user_message = models.Message(
            chat_id=db_chat.id,
            role="user",
            content=chat.message
        )
        db.add(user_message)
        db.commit()
        
        # ارسال پرسش به چت‌بات
        logger.info(f"ارسال پرسش به چت‌بات: {chat.message[:100]}...")
        response = chatbot.ask(chat.message)
        logger.info("پاسخ از چت‌بات دریافت شد")
        
        # ذخیره پاسخ چت‌بات
        assistant_message = models.Message(
            chat_id=db_chat.id,
            role="assistant",
            content=response["answer"],
            sources=response["sources"]
        )
        db.add(assistant_message)
        db.commit()
        
        return {
            "id": db_chat.id,
            "website_id": db_chat.website_id,
            "message": chat.message,
            "response": response["answer"],
            "session_id": db_chat.session_id,
            "created_at": db_chat.created_at,
            "error": None
        }
        
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
        rag_service = RAGService(collection_name)
        
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