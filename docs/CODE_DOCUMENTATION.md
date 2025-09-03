# مستندات کد - سیستم چت‌بات هوشمند

## فهرست مطالب
- [معماری کلی](#معماری-کلی)
- [ساختار پروژه](#ساختار-پروژه)
- [کامپوننت‌های کلیدی](#کامپوننت‌های-کلیدی)
- [جریان داده](#جریان-داده)
- [نکات توسعه](#نکات-توسعه)

## معماری کلی

### الگوی معماری
این پروژه از معماری **Layered Architecture** با **Service-Oriented** استفاده می‌کند:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                        │
├─────────────────────────────────────────────────────────────┤
│                    API Gateway (FastAPI)                   │
├─────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Auth Service│ │ Chat Service│ │ Crawl Service│          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
├─────────────────────────────────────────────────────────────┤
│                    Data Access Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ PostgreSQL  │ │ ChromaDB    │ │ Redis Cache │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### تکنولوژی‌های استفاده شده
- **Backend**: FastAPI, Python 3.9+
- **Frontend**: React 18, Material-UI
- **Database**: PostgreSQL, ChromaDB
- **Cache**: Redis
- **AI Models**: OpenAI GPT, Google Gemini, Ollama
- **Authentication**: JWT
- **Deployment**: Docker, Nginx

## ساختار پروژه

```
ai/
├── backend/                          # سرور backend
│   ├── app/                         # کد اصلی برنامه
│   │   ├── api/                     # API endpoints
│   │   ├── core/                    # منطق اصلی
│   │   ├── database/                # مدل‌ها و دیتابیس
│   │   ├── middleware/              # middleware ها
│   │   ├── services/                # سرویس‌های کسب و کار
│   │   └── utils/                   # ابزارهای کمکی
│   ├── knowledge_base/              # پایگاه دانش
│   ├── processed_data/              # داده‌های پردازش شده
│   └── migrations/                  # تغییرات دیتابیس
├── frontend/                        # کلاینت frontend
│   ├── src/                         # کد اصلی React
│   │   ├── components/              # کامپوننت‌ها
│   │   ├── services/                # سرویس‌های API
│   │   ├── contexts/                # React Context ها
│   │   └── utils/                   # ابزارهای کمکی
│   └── public/                      # فایل‌های استاتیک
└── docs/                            # مستندات
```

## کامپوننت‌های کلیدی

### 1. Authentication System

#### کلاس‌های اصلی
- `AuthService`: مدیریت احراز هویت
- `JWTManager`: مدیریت توکن‌های JWT
- `PasswordManager`: مدیریت رمزهای عبور

#### جریان احراز هویت
```python
# 1. کاربر درخواست ورود می‌دهد
POST /api/auth/login

# 2. سیستم رمز را بررسی می‌کند
if verify_password(plain_password, hashed_password):
    # 3. توکن JWT ایجاد می‌شود
    access_token = create_access_token(data={"sub": user.email})
    
# 4. توکن به کاربر برگردانده می‌شود
return {"access_token": access_token, "token_type": "bearer"}
```

### 2. Chatbot Management System

#### کلاس‌های اصلی
- `ChatbotManager`: مدیریت چت‌بات‌ها
- `ChatbotFactory`: ایجاد چت‌بات‌های مختلف
- `RAGService`: سرویس RAG

#### مدیریت همزمانی
```python
class ChatbotManager:
    def __init__(self):
        self._chatbots: Dict[str, Any] = {}
        self._session_chatbots: Dict[str, Any] = {}
        self._locks: Dict[str, RLock] = defaultdict(RLock)
        self._max_concurrent_chats = 50
```

#### جریان چت
```python
# 1. دریافت درخواست چت
chat_request = ChatCreate(
    website_id=1,
    message="سوال کاربر",
    chatbot_type="openai"
)

# 2. بررسی دسترسی و دریافت چت‌بات
chatbot = chatbot_manager.get_chatbot(
    collection_name="website_collection",
    chatbot_type="openai",
    session_id="unique_session_id"
)

# 3. پردازش سوال و دریافت پاسخ
response = chatbot.ask(chat_request.message)

# 4. آزادسازی چت‌بات
chatbot_manager.release_chatbot(collection_name, chatbot_type, session_id)
```

### 3. Web Crawling System

#### کلاس‌های اصلی
- `WebCrawlerPipeline`: کراولینگ وب‌سایت‌ها
- `EmbeddingPipeline`: ایجاد embeddings
- `ChromaDBService`: مدیریت پایگاه دانش

#### جریان کراولینگ
```python
# 1. شروع کراولینگ
crawler = WebCrawlerPipeline(website_url, settings)
await crawler.run_async()

# 2. پردازش داده‌ها
embedder = EmbeddingPipeline(domain)
embedder.run()

# 3. ذخیره در ChromaDB
collection.add(
    embeddings=embeddings,
    documents=documents,
    metadatas=metadata
)
```

### 4. RAG (Retrieval-Augmented Generation)

#### کامپوننت‌ها
- `HybridSearcher`: جستجوی ترکیبی (BM25 + Vector)
- `EmbeddingService`: سرویس embeddings
- `PromptManager`: مدیریت prompt ها

#### جریان RAG
```python
# 1. جستجو در پایگاه دانش
searcher = HybridSearcher(collection)
results = searcher.search(query, top_k=5)

# 2. ترکیب نتایج با context
context = "\n".join([doc.content for doc in results])

# 3. ارسال به مدل AI
prompt = f"Context: {context}\nQuestion: {query}\nAnswer:"
response = ai_model.generate(prompt)
```

## جریان داده

### 1. جریان ایجاد وب‌سایت
```
User Request → API Gateway → Website Service → Crawler Service → 
Embedding Service → ChromaDB → Success Response
```

### 2. جریان چت
```
User Message → API Gateway → Chat Service → RAG Service → 
AI Model → Response → Database → User
```

### 3. جریان احراز هویت
```
Login Request → Auth Service → Password Verification → 
JWT Generation → Token Response → User Session
```

## نکات توسعه

### 1. Error Handling
```python
try:
    result = some_operation()
except SpecificException as e:
    logger.error(f"Specific error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### 2. Logging
```python
import logging

logger = logging.getLogger(__name__)

# لاگ کردن با context
logger.info(f"Processing website {website_id} with {page_count} pages")
logger.error(f"Failed to crawl {url}: {str(e)}")
```

### 3. Configuration Management
```python
from app.config import settings

# استفاده از تنظیمات
max_pages = settings.MAX_PAGES
api_key = settings.OPENAI_API_KEY
debug_mode = settings.DEBUG_MODE
```

### 4. Database Transactions
```python
from sqlalchemy.orm import Session

def create_website(db: Session, website_data: dict):
    try:
        website = Website(**website_data)
        db.add(website)
        db.commit()
        db.refresh(website)
        return website
    except Exception as e:
        db.rollback()
        raise e
```

### 5. Async Operations
```python
import asyncio
from typing import List

async def process_multiple_websites(urls: List[str]):
    tasks = [process_single_website(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## تست و Debugging

### 1. Unit Tests
```python
import pytest
from app.services.chat_service import ChatService

def test_chat_service_creation():
    service = ChatService()
    assert service is not None
    assert hasattr(service, 'process_message')
```

### 2. Integration Tests
```python
def test_chat_flow():
    # تست کامل جریان چت
    response = client.post("/api/chats/", json=chat_data)
    assert response.status_code == 200
    assert "answer" in response.json()
```

### 3. Debug Mode
```python
# فعال کردن debug mode
export DEBUG=true

# لاگ‌های verbose نمایش داده می‌شوند
logger.info("Debug information")
```

## Performance Optimization

### 1. Caching
```python
from app.services.cache_service import CacheService

cache = CacheService()

# کش کردن نتایج جستجو
@cache.memoize(ttl=3600)
def search_documents(query: str):
    return perform_search(query)
```

### 2. Connection Pooling
```python
# تنظیمات connection pool
DATABASE_URL = "postgresql://user:pass@host/db?pool_size=20&max_overflow=30"
```

### 3. Async Processing
```python
# پردازش همزمان چندین درخواست
async def process_batch(requests: List[Request]):
    semaphore = asyncio.Semaphore(10)  # محدودیت همزمانی
    
    async def process_single(req):
        async with semaphore:
            return await process_request(req)
    
    tasks = [process_single(req) for req in requests]
    return await asyncio.gather(*tasks)
```

## Security Considerations

### 1. Input Validation
```python
from pydantic import BaseModel, validator

class ChatCreate(BaseModel):
    message: str
    website_id: int
    
    @validator('message')
    def validate_message(cls, v):
        if len(v) > 1000:
            raise ValueError('Message too long')
        return v.strip()
```

### 2. Rate Limiting
```python
from app.middleware.rate_limiter import RateLimiter

@RateLimiter(requests=20, window=60)
async def chat_endpoint(request: Request):
    # endpoint logic
    pass
```

### 3. SQL Injection Prevention
```python
# استفاده از ORM به جای raw SQL
websites = db.query(Website).filter(Website.owner_id == user_id).all()

# یا استفاده از parameterized queries
query = "SELECT * FROM websites WHERE owner_id = :owner_id"
result = db.execute(query, {"owner_id": user_id})
```

## Deployment

### 1. Environment Variables
```bash
# .env file
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@host/db
OPENAI_API_KEY=your_api_key
```

### 2. Docker Configuration
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0"
    }
```

## Monitoring و Observability

### 1. Metrics
```python
from prometheus_client import Counter, Histogram

# شمارش درخواست‌ها
request_counter = Counter('http_requests_total', 'Total HTTP requests')

# اندازه‌گیری زمان پاسخ
response_time = Histogram('http_response_time_seconds', 'Response time in seconds')
```

### 2. Tracing
```python
import logging

# اضافه کردن correlation ID
logger.info(f"[{request_id}] Processing request")
```

### 3. Error Tracking
```python
import sentry_sdk

sentry_sdk.init(dsn="your_sentry_dsn")

# ارسال خطاها به Sentry
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```
