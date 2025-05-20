from fastapi import FastAPI, HTTPException, Header, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Dict
from datetime import datetime
import os
import asyncio
from decouple import config
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.customer import CustomerManager
from crawler.website_crawler import WebsiteCrawler
from core.chatbot_rag import ChatbotRAG

# تنظیمات اولیه
app = FastAPI(title="Chat Widget API")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# مدیریت سرویس‌ها
customer_manager = CustomerManager()
crawler = WebsiteCrawler()
chatbot = ChatbotRAG()

# تنظیمات CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    config('FRONTEND_URL', default="*")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# تنظیمات آپلود فایل
UPLOAD_DIR = "backend/static/uploads"
ALLOWED_FILE_TYPES = ["image/jpeg", "image/png", "image/gif"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Static files
app.mount("/static", StaticFiles(directory="backend/static"), name="static")
app.mount("/static/uploads", StaticFiles(directory="backend/static/uploads"), name="uploads")

def generate_widget_code(customer_id: str) -> str:
    """تولید کد ویجت برای جاسازی در سایت"""
    base_url = config('BASE_URL')
    return f"""
    <script src="{base_url}/static/widget.js"></script>
    <script>
        new ChatWidget({{
            customerId: '{customer_id}',
            position: 'bottom-right',
            apiUrl: '{base_url}/api'
        }}).init();
    </script>
    """

@app.post("/register")
@limiter.limit("10/minute")
async def register_website(domain: str, request: Request) -> Dict:
    """ثبت وب‌سایت جدید"""
    try:
        # اعتبارسنجی دامنه
        if not domain or len(domain) > 255:
            raise HTTPException(status_code=400, detail="Invalid domain")

        # ایجاد مشتری جدید
        customer_data = customer_manager.create_customer(domain)

        # شروع خزش سایت به صورت async
        asyncio.create_task(crawler.crawl(domain))

        return {
            "status": "success",
            "customer_id": customer_data["customer_id"],
            "api_key": customer_data["api_key"],
            "widget_code": generate_widget_code(customer_data["customer_id"])
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/validate-key")
@limiter.limit("60/minute")
async def validate_key(api_key: str, request: Request) -> Dict:
    """اعتبارسنجی کلید API"""
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")

    customer_id = customer_manager.validate_api_key(api_key)
    if not customer_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {"customer_id": customer_id}

@app.post("/api/chat")
@limiter.limit("30/minute")
async def chat_endpoint(
    message: Dict,
    request: Request,
    customer_id: str = Header(..., alias="X-Customer-ID")
):
    """پردازش پیام چت"""
    try:
        # اعتبارسنجی پیام
        if not message.get("text"):
            raise HTTPException(status_code=400, detail="Message text is required")

        if len(message["text"]) > 1000:
            raise HTTPException(status_code=400, detail="Message too long")

        # اعتبارسنجی مشتری
        customer = customer_manager.get_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # پردازش پیام
        response = await chatbot.get_response(
            query=message["text"],
            collection_name=customer["collection_name"]
        )

        return {
            "status": "success",
            "message": response
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/api/upload")
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    customer_id: str = Header(..., alias="X-Customer-ID")
):
    """آپلود فایل"""
    try:
        # اعتبارسنجی فایل
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(status_code=400, detail="Invalid file type")

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")

        # اعتبارسنجی مشتری
        customer = customer_manager.get_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # ذخیره فایل
        filename = f"{datetime.now().timestamp()}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as buffer:
            buffer.write(content)

        return {
            "status": "success",
            "url": f"{config('BASE_URL')}/static/uploads/{filename}"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/typing")
@limiter.limit("60/minute")
async def typing_status(
    request: Request,
    status: Dict,
    customer_id: str = Header(..., alias="X-Customer-ID")
):
    """دریافت وضعیت تایپ کاربر"""
    try:
        # اعتبارسنجی وضعیت
        if "isTyping" not in status:
            raise HTTPException(status_code=400, detail="isTyping status is required")

        # اعتبارسنجی مشتری
        customer = customer_manager.get_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # در اینجا می‌توانید وضعیت تایپ را ذخیره یا به سایر کاربران ارسال کنید

        return {"status": "success"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status update failed: {str(e)}")