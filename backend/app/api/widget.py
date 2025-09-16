from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime, timedelta
from ..database.database import get_db
from ..database import models
from ..services.rag import RAGService
from ..core.chatbot_factory import ChatbotFactory
from ..config import settings
from ..utils.security import sanitize_html, validate_input_length, sanitize_sql_input
import hashlib
import hmac
import time
import re

router = APIRouter()
logger = logging.getLogger(__name__)

# Rate limiting storage (در production باید از Redis استفاده شود)
rate_limit_storage = {}

def verify_widget_key(site_id: int, public_key: str, db: Session) -> bool:
    """تأیید کلید عمومی ویجت"""
    try:
        website = db.query(models.Website).filter(
            models.Website.id == site_id,
            models.Website.status == "ready"
        ).first()
        
        if not website:
            return False
            
        # در اینجا می‌توانید منطق تأیید کلید را پیاده‌سازی کنید
        # فعلاً برای سادگی، هر کلید معتبر در نظر گرفته می‌شود
        return True
        
    except Exception as e:
        logger.error(f"خطا در تأیید کلید ویجت: {str(e)}")
        return False

def check_rate_limit(client_ip: str, site_id: int, limit: int = 100, window: int = 3600) -> bool:
    """بررسی محدودیت نرخ درخواست"""
    current_time = time.time()
    key = f"{client_ip}:{site_id}"
    
    if key not in rate_limit_storage:
        rate_limit_storage[key] = {"count": 0, "reset_time": current_time + window}
    
    if current_time > rate_limit_storage[key]["reset_time"]:
        rate_limit_storage[key] = {"count": 0, "reset_time": current_time + window}
    
    if rate_limit_storage[key]["count"] >= limit:
        return False
    
    rate_limit_storage[key]["count"] += 1
    return True

def check_abuse(client_ip: str, user_agent: str, message: str) -> bool:
    """بررسی سوءاستفاده"""
    # بررسی طول پیام
    if len(message) > 1000:
        return False
    
    # بررسی کاراکترهای مشکوک
    suspicious_patterns = [
        r'<script',
        r'javascript:',
        r'vbscript:',
        r'onload=',
        r'onerror=',
        r'<iframe',
        r'<object',
        r'<embed',
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            return False
    
    return True

def get_client_ip(request: Request) -> str:
    """دریافت IP کلاینت"""
    # بررسی X-Forwarded-For header
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # بررسی X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # IP مستقیم
    return request.client.host


@router.get("/config")
async def get_widget_config(
    site_id: int,
    key: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """دریافت تنظیمات ویجت"""
    try:
        # Validation
        if not isinstance(site_id, int) or site_id <= 0:
            raise HTTPException(status_code=400, detail="شناسه سایت نامعتبر")
        
        if not key or len(key) > 100:
            raise HTTPException(status_code=400, detail="کلید نامعتبر")
        
        # Sanitize inputs
        key = sanitize_sql_input(key)
        
        # بررسی rate limit
        client_ip = get_client_ip(request)
        if not check_rate_limit(client_ip, site_id, limit=1000, window=3600):
            raise HTTPException(status_code=429, detail="محدودیت نرخ درخواست")
        
        # تأیید کلید
        if not verify_widget_key(site_id, key, db):
            raise HTTPException(status_code=401, detail="کلید نامعتبر")
        
        # دریافت اطلاعات وب‌سایت
        website = db.query(models.Website).filter(
            models.Website.id == site_id,
            models.Website.status == "ready"
        ).first()
        
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
        
        return {
            "site_id": site_id,
            "site_name": website.name or website.domain,
            "widget_title": "پشتیبانی هوشمند",
            "widget_subtitle": "سوال خود را بپرسید",
            "placeholder": "سوال خود را اینجا بنویسید...",
            "send_button": "ارسال",
            "thinking_message": "در حال پردازش...",
            "error_message": "خطا در دریافت پاسخ",
            "no_answer_message": "متأسفانه پاسخ مناسبی برای سوال شما یافت نشد.",
            "theme": {
                "primary_color": "#1976d2",
                "secondary_color": "#dc004e",
                "background_color": "#ffffff",
                "text_color": "#333333",
                "border_radius": "8px"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در دریافت تنظیمات ویجت: {str(e)}")
        raise HTTPException(status_code=500, detail="خطای داخلی سرور")

@router.post("/chat")
async def widget_chat(
    request: Request,
    db: Session = Depends(get_db)
):
    """پردازش چت ویجت"""
    try:
        # دریافت داده‌های درخواست
        body = await request.json()
        site_id = body.get("site_id")
        key = body.get("key")
        message = body.get("message")
        conversation_id = body.get("conversation_id")
        meta = body.get("meta", {})
        
        # Validation
        if not all([site_id, key, message]):
            raise HTTPException(status_code=400, detail="داده‌های ناقص")
        
        if not isinstance(site_id, int) or site_id <= 0:
            raise HTTPException(status_code=400, detail="شناسه سایت نامعتبر")
        
        if not validate_input_length(message, max_length=1000):
            raise HTTPException(status_code=400, detail="پیام خیلی طولانی است")
        
        # Sanitize inputs
        message = sanitize_html(message)
        key = sanitize_sql_input(key)
        
        # بررسی rate limit
        client_ip = get_client_ip(request)
        if not check_rate_limit(client_ip, site_id, limit=50, window=3600):
            raise HTTPException(status_code=429, detail="محدودیت نرخ درخواست")
        
        # بررسی سوءاستفاده
        user_agent = meta.get("user_agent", "")
        if not check_abuse(client_ip, user_agent, message):
            raise HTTPException(status_code=400, detail="درخواست نامعتبر")
        
        # تأیید کلید
        if not verify_widget_key(site_id, key, db):
            raise HTTPException(status_code=401, detail="کلید نامعتبر")
        
        # دریافت اطلاعات وب‌سایت
        website = db.query(models.Website).filter(
            models.Website.id == site_id,
            models.Website.status == "ready"
        ).first()
        
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
        
        # ادامه پردازش چت...
        try:
            # دریافت collection_name از website
            collection_name = website.collection_name
            if not collection_name:
                raise HTTPException(status_code=400, detail="کالکشن برای این وب‌سایت ایجاد نشده است")
            
            # دریافت تنظیمات RAG از وب‌سایت
            rag_settings = website.rag_settings or {}
            chatbot_type = rag_settings.get('chatbot_type', 'openai')
            
            # استفاده از ChatbotFactory برای ایجاد چت‌بات
            chatbot = ChatbotFactory.create_chatbot(
                chatbot_type=chatbot_type,
                collection_name=collection_name,
                max_tokens=rag_settings.get('max_response_length', 500) * 2,
                temperature=rag_settings.get('temperature', 0.7),
                db=db
            )
            
            # ارسال پرسش به چت‌بات
            response = chatbot.ask(message)
            
            # بررسی ساختار پاسخ
            if not isinstance(response, dict) or 'answer' not in response:
                raise HTTPException(status_code=500, detail="پاسخ چت‌بات در فرمت نامعتبر است")
            
            # ایجاد یا دریافت چت موجود
            if conversation_id:
                # استفاده از چت موجود
                chat = db.query(models.Chat).filter(
                    models.Chat.id == conversation_id,
                    models.Chat.website_id == site_id
                ).first()
                if not chat:
                    raise HTTPException(status_code=404, detail="چت یافت نشد")
            else:
                # ایجاد چت جدید
                session_id = f"widget_{site_id}_{int(time.time())}"
                chat = models.Chat(
                    website_id=site_id,
                    session_id=session_id
                )
                db.add(chat)
                db.commit()
                db.refresh(chat)
                conversation_id = chat.id
            
            # ذخیره پیام کاربر
            user_message = models.Message(
                chat_id=conversation_id,
                role="user",
                content=message
            )
            db.add(user_message)
            
            # ذخیره پاسخ چت‌بات
            assistant_message = models.Message(
                chat_id=conversation_id,
                role="assistant",
                content=response["answer"],
                sources=response.get("sources", [])
            )
            db.add(assistant_message)
            
            db.commit()
            
            # بازگرداندن پاسخ
            return {
                "conversation_id": conversation_id,
                "answer": response["answer"],
                "sources": response.get("sources", []),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"خطا در پردازش چت: {str(e)}")
            raise HTTPException(status_code=500, detail=f"خطا در پردازش چت: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در پردازش چت ویجت: {str(e)}")
        raise HTTPException(status_code=500, detail="خطای داخلی سرور")

@router.get("/snippet/{site_id}")
async def get_widget_snippet(
    site_id: int,
    db: Session = Depends(get_db)
):
    """تولید کد اسنیپت ویجت"""
    try:
        # دریافت اطلاعات وب‌سایت
        website = db.query(models.Website).filter(
            models.Website.id == site_id,
            models.Website.status == "ready"
        ).first()
        
        if not website:
            raise HTTPException(status_code=404, detail="وب‌سایت یافت نشد")
        
        # استفاده از کلید عمومی ذخیره شده یا تولید کلید جدید
        if website.public_key:
            public_key = website.public_key
        else:
            public_key = hashlib.md5(f"{site_id}_{website.domain}_{int(time.time())}".encode()).hexdigest()
            # ذخیره کلید در دیتابیس
            website.public_key = public_key
            db.commit()
        
        # تولید کد اسنیپت
        snippet = f'''<!-- ویجت چت هوشمند -->
<script>
(function() {{
    // تنظیمات ویجت
    var config = {{
        siteId: {site_id},
        publicKey: localStorage.getItem('widget_public_key') || '{public_key}',
        apiUrl: '{settings.API_BASE_URL}',
        theme: {{
            primaryColor: '#1976d2',
            secondaryColor: '#dc004e',
            backgroundColor: '#ffffff',
            textColor: '#333333',
            borderRadius: '8px'
        }}
    }};
    
    // متغیر برای نگهداری conversation_id
    var conversationId = null;
    
    // ایجاد استایل ویجت
    var style = document.createElement('style');
    style.textContent = `
        .ai-chat-widget {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
            font-family: 'Vazirmatn', Arial, sans-serif;
            direction: rtl;
        }}
        .ai-chat-button {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background-color: ${{config.theme.primaryColor}};
            color: white;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            transition: all 0.3s ease;
        }}
        .ai-chat-button:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        }}
        .ai-chat-window {{
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 350px;
            height: 500px;
            background-color: ${{config.theme.backgroundColor}};
            border-radius: ${{config.theme.borderRadius}};
            box-shadow: 0 8px 32px rgba(0,0,0,0.15);
            display: none;
            flex-direction: column;
            border: 1px solid #e0e0e0;
        }}
        .ai-chat-header {{
            background-color: ${{config.theme.primaryColor}};
            color: white;
            padding: 15px;
            border-radius: ${{config.theme.borderRadius}} ${{config.theme.borderRadius}} 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .ai-chat-title {{
            font-weight: bold;
            font-size: 16px;
        }}
        .ai-chat-close {{
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            font-size: 20px;
        }}
        .ai-chat-messages {{
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .ai-chat-message {{
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
        }}
        .ai-chat-message.user {{
            background-color: ${{config.theme.primaryColor}};
            color: white;
            align-self: flex-end;
        }}
        .ai-chat-message.assistant {{
            background-color: #f5f5f5;
            color: ${{config.theme.textColor}};
            align-self: flex-start;
        }}
        .ai-chat-input {{
            padding: 15px;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }}
        .ai-chat-input input {{
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 20px;
            outline: none;
        }}
        .ai-chat-input button {{
            padding: 10px 20px;
            background-color: ${{config.theme.primaryColor}};
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
        }}
        .ai-chat-input button:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
        }}
        .ai-chat-sources {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
    `;
    document.head.appendChild(style);
    
    // ایجاد HTML ویجت
    var widget = document.createElement('div');
    widget.className = 'ai-chat-widget';
    widget.innerHTML = `
        <button class="ai-chat-button" onclick="toggleChat()">💬</button>
        <div class="ai-chat-window" id="chatWindow">
            <div class="ai-chat-header">
                <span class="ai-chat-title">پشتیبانی هوشمند</span>
                <button class="ai-chat-close" onclick="toggleChat()">×</button>
            </div>
            <div class="ai-chat-messages" id="chatMessages">
                <div class="ai-chat-message assistant">
                    سلام! چطور می‌تونم کمکتون کنم؟
                </div>
            </div>
            <div class="ai-chat-input">
                <input type="text" id="chatInput" placeholder="سوال خود را اینجا بنویسید..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()" id="sendButton">ارسال</button>
            </div>
        </div>
    `;
    document.body.appendChild(widget);
    
    var conversationId = null;
    var isOpen = false;
    
    // توابع ویجت
    window.toggleChat = function() {{
        var window = document.getElementById('chatWindow');
        isOpen = !isOpen;
        window.style.display = isOpen ? 'flex' : 'none';
        if (isOpen) {{
            document.getElementById('chatInput').focus();
        }}
    }};
    
    window.handleKeyPress = function(event) {{
        if (event.key === 'Enter') {{
            sendMessage();
        }}
    }};
    
    window.sendMessage = async function() {{
        var input = document.getElementById('chatInput');
        var button = document.getElementById('sendButton');
        var messages = document.getElementById('chatMessages');
        var message = input.value.trim();
        
        if (!message) return;
        
        // غیرفعال کردن دکمه
        button.disabled = true;
        button.textContent = 'در حال ارسال...';
        
        // اضافه کردن پیام کاربر
        var userDiv = document.createElement('div');
        userDiv.className = 'ai-chat-message user';
        userDiv.textContent = message;
        messages.appendChild(userDiv);
        
        // پاک کردن ورودی
        input.value = '';
        
        // اسکرول به پایین
        messages.scrollTop = messages.scrollHeight;
        
        try {{
            // ارسال درخواست به سرور
            var response = await fetch(config.apiUrl + '/api/widget/chat', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{
                    site_id: config.siteId,
                    key: config.publicKey,
                    message: message,
                    conversation_id: conversationId,
                    meta: {{
                        user_agent: navigator.userAgent,
                        timestamp: new Date().toISOString()
                    }}
                }})
            }});
            
            var data = await response.json();
            
            if (response.ok && data) {{
                // بررسی و تنظیم conversation_id
                if (data.conversation_id) {{
                    conversationId = data.conversation_id;
                }}
                
                // اضافه کردن پاسخ
                var assistantDiv = document.createElement('div');
                assistantDiv.className = 'ai-chat-message assistant';
                assistantDiv.innerHTML = data.answer || 'پاسخ دریافت شد';
                
                // اضافه کردن منابع
                if (data.sources && data.sources.length > 0) {{
                    var sourcesDiv = document.createElement('div');
                    sourcesDiv.className = 'ai-chat-sources';
                    sourcesDiv.innerHTML = '<strong>منابع:</strong> ' + data.sources.map(s => s.title || s.url).join(', ');
                    assistantDiv.appendChild(sourcesDiv);
                }}
                
                messages.appendChild(assistantDiv);
            }} else {{
                var errorMessage = 'خطا در دریافت پاسخ';
                if (data && data.detail) {{
                    errorMessage = data.detail;
                }}
                throw new Error(errorMessage);
            }}
            
        }} catch (error) {{
            console.error('خطا در ارسال پیام:', error);
            var errorDiv = document.createElement('div');
            errorDiv.className = 'ai-chat-message assistant error';
            var errorText = 'خطا در دریافت پاسخ';
            if (error.message) {{
                errorText = error.message;
            }}
            errorDiv.textContent = errorText + ' - لطفاً دوباره تلاش کنید.';
            messages.appendChild(errorDiv);
        }} finally {{
            // فعال کردن دکمه
            button.disabled = false;
            button.textContent = 'ارسال';
            
            // اسکرول به پایین
            messages.scrollTop = messages.scrollHeight;
        }}
    }};
}})();
</script>'''
        
        return {
            "site_id": site_id,
            "public_key": public_key,
            "snippet": snippet,
            "instructions": "این کد را در بخش <head> یا قبل از تگ </body> وب‌سایت خود قرار دهید."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در تولید اسنیپت ویجت: {str(e)}")
        raise HTTPException(status_code=500, detail="خطای داخلی سرور")
