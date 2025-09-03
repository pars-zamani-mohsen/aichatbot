# 🤖 سیستم چت‌بات هوشمند با قابلیت RAG

یک سیستم چت‌بات پیشرفته که از تکنولوژی RAG (Retrieval-Augmented Generation) برای ارائه پاسخ‌های دقیق و مبتنی بر دانش استفاده می‌کند.

## ✨ ویژگی‌های کلیدی

- 🔐 **احراز هویت پیشرفته**: JWT، 2FA، Rate Limiting
- 🌐 **کراولینگ هوشمند**: کراولینگ خودکار وب‌سایت‌ها
- 🤖 **چت‌بات چندگانه**: پشتیبانی از OpenAI، Gemini، Ollama
- 📊 **داشبورد جامع**: آمار و گزارشات پیشرفته
- 🔍 **جستجوی ترکیبی**: BM25 + Vector Search
- 📱 **رابط کاربری مدرن**: React + Material-UI
- 🚀 **عملکرد بالا**: Async processing، Connection pooling
- 🛡️ **امنیت قوی**: CORS، Security Headers، Input Validation

## 🏗️ معماری سیستم

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
│                    AI & ML Layer                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ RAG Service │ │ Embedding   │ │ AI Models   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ PostgreSQL  │ │ ChromaDB    │ │ Redis Cache │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+

### نصب Backend

```bash
# کلون کردن پروژه
git clone https://github.com/your-username/ai-chatbot.git
cd ai-chatbot/backend

# ایجاد virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# یا
venv\Scripts\activate  # Windows

# نصب dependencies
pip install -r requirements.txt

# تنظیم متغیرهای محیطی
cp .env.example .env
# ویرایش فایل .env با مقادیر مناسب

# اجرای migrations
alembic upgrade head

# راه‌اندازی سرور
python run.py
```

### نصب Frontend

```bash
cd ../frontend

# نصب dependencies
npm install

# راه‌اندازی در حالت development
npm start

# ساخت برای production
npm run build
```

### نصب با Docker

```bash
# راه‌اندازی تمام سرویس‌ها
docker-compose up -d

# بررسی وضعیت
docker-compose ps
```

## 📚 مستندات

### 📖 [مستندات API](docs/API_DOCUMENTATION.md)
- نقاط پایانی API
- مدل‌های داده
- مثال‌های استفاده
- کدهای خطا

### 🏗️ [مستندات کد](docs/CODE_DOCUMENTATION.md)
- معماری سیستم
- کامپوننت‌های کلیدی
- جریان داده
- نکات توسعه

### 📊 [نمودارهای معماری](docs/ARCHITECTURE_DIAGRAMS.md)
- نمودارهای Mermaid
- جریان داده
- معماری امنیت
- نمودار Deployment

### 🔧 [راهنمای عیب‌یابی](docs/TROUBLESHOOTING_GUIDE.md)
- مشکلات رایج
- راه‌حل‌ها
- Debugging
- Performance tuning

## 🎯 استفاده

### 1. احراز هویت

```bash
# ورود کاربر
curl -X POST "http://localhost:5000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### 2. ایجاد وب‌سایت

```bash
# ایجاد وب‌سایت جدید
curl -X POST "http://localhost:5000/api/websites/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "name": "وب‌سایت نمونه"}'
```

### 3. شروع چت

```bash
# ارسال پیام
curl -X POST "http://localhost:5000/api/chats/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"website_id": 1, "message": "سلام", "chatbot_type": "openai"}'
```

## 🔧 تنظیمات

### متغیرهای محیطی

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/ai_database

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# AI Models
OPENAI_API_KEY=your-openai-key
GEMINI_API_KEY=your-gemini-key

# System
DEBUG=false
LOG_LEVEL=INFO
TIMEZONE=Asia/Tehran
```

### تنظیمات Rate Limiting

```python
# تنظیم از طریق API
from app.services.system_settings_service import SystemSettingsService

service = SystemSettingsService()
service.set_rate_limit_settings("chat", 20, 60)      # 20 درخواست در 60 ثانیه
service.set_rate_limit_settings("crawl", 5, 300)    # 5 درخواست در 300 ثانیه
```

## 🧪 تست

### تست Backend

```bash
cd backend

# اجرای تست‌ها
pytest

# تست با coverage
pytest --cov=app

# تست performance
pytest tests/test_performance.py
```

### تست Frontend

```bash
cd frontend

# اجرای تست‌ها
npm test

# تست با coverage
npm run test:coverage
```

### تست API

```bash
# تست endpoints
curl -X GET "http://localhost:5000/api/health"

# تست احراز هویت
curl -X POST "http://localhost:5000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'
```

## 📊 Monitoring

### Health Checks

```bash
# بررسی وضعیت سیستم
curl "http://localhost:5000/health"

# بررسی وضعیت دیتابیس
curl "http://localhost:5000/health/db"

# بررسی وضعیت ChromaDB
curl "http://localhost:5000/health/chroma"
```

### Metrics

```bash
# آمار سیستم
curl "http://localhost:5000/metrics"

# آمار چت‌بات
curl "http://localhost:5000/api/dashboard/admin/stats"
```

## 🚀 Deployment

### Production Deployment

```bash
# اجرای اسکریپت deployment
./deploy.sh

# یا دستی
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

```bash
# Production settings
export DEBUG=false
export LOG_LEVEL=WARNING
export DATABASE_URL="postgresql://prod_user:prod_pass@prod_host/prod_db"
```

### SSL Configuration

```bash
# تنظیم SSL با Let's Encrypt
sudo certbot --nginx -d yourdomain.com

# تنظیم Nginx
sudo nano /etc/nginx/sites-available/ai-chatbot
```

## 🔒 امنیت

### ویژگی‌های امنیتی

- ✅ JWT Authentication
- ✅ Rate Limiting
- ✅ CORS Protection
- ✅ Input Validation
- ✅ SQL Injection Prevention
- ✅ XSS Protection
- ✅ CSRF Protection
- ✅ Security Headers

### تنظیمات امنیتی

```python
# Security Headers
SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
}
```

## 📈 Performance

### بهینه‌سازی‌ها

- 🚀 Async Processing
- 🗄️ Connection Pooling
- 💾 Redis Caching
- 🔍 Query Optimization
- 📊 Database Indexing

### Benchmark Results

```
Concurrent Users: 100
Response Time: < 2s
Throughput: 50 req/s
Memory Usage: < 512MB
CPU Usage: < 30%
```

## 🤝 مشارکت

### راهنمای مشارکت

1. Fork پروژه
2. ایجاد feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit تغییرات (`git commit -m 'Add some AmazingFeature'`)
4. Push به branch (`git push origin feature/AmazingFeature`)
5. ایجاد Pull Request

### استانداردهای کد

- استفاده از Black برای formatting
- پیروی از PEP 8
- نوشتن docstring برای تمام توابع
- تست‌نویسی برای کدهای جدید

## 📝 تغییرات

### نسخه 1.0.0
- ✅ احراز هویت JWT
- ✅ سیستم چت‌بات RAG
- ✅ کراولینگ وب‌سایت
- ✅ داشبورد مدیریتی
- ✅ API کامل

### نسخه 1.1.0
- ✅ بهبود عملکرد
- ✅ اضافه کردن monitoring
- ✅ بهینه‌سازی دیتابیس
- ✅ بهبود امنیت

## 📄 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است. برای جزئیات بیشتر فایل [LICENSE](LICENSE) را مطالعه کنید.

## 📞 پشتیبانی

### راه‌های ارتباطی

- 📧 ایمیل: support@example.com
- 🐛 GitHub Issues: [اینجا](https://github.com/your-username/ai-chatbot/issues)
- 📖 مستندات: [اینجا](https://docs.example.com)
- 💬 Discord: [اینجا](https://discord.gg/your-server)

### منابع مفید

- [مستندات FastAPI](https://fastapi.tiangolo.com/)
- [مستندات React](https://reactjs.org/docs/)
- [مستندات PostgreSQL](https://www.postgresql.org/docs/)
- [مستندات ChromaDB](https://docs.trychroma.com/)

## 🙏 تشکر

از تمام افرادی که در توسعه این پروژه مشارکت کرده‌اند تشکر می‌کنیم:

- تیم توسعه
- جامعه open source
- کاربران و تست‌کنندگان

---

⭐ اگر این پروژه برایتان مفید بود، لطفاً آن را star کنید! 