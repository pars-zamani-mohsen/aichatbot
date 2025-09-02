# 🤖 AI Chatbot - RAG System

یک سیستم چت‌بات هوشمند مبتنی بر RAG (Retrieval-Augmented Generation) که می‌تواند از وب‌سایت‌های مختلف اطلاعات استخراج کند و به سؤالات کاربران پاسخ دهد.

## 🚀 شروع سریع

### پیش‌نیازها
- Python 3.8+
- PostgreSQL 13+
- Node.js 16+
- npm

### نصب و راه‌اندازی

#### 1. کلون کردن پروژه
```bash
git clone https://github.com/yourusername/ai-chatbot.git
cd ai-chatbot
```

#### 2. راه‌اندازی Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# تنظیم environment variables
cp ../env.example .env
nano .env  # تنظیم متغیرها

# اجرای migrations
cd ..
alembic upgrade head

# ایجاد admin user
cd backend
python create_admin_user.py

# اجرای سرور
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

#### 3. راه‌اندازی Frontend
```bash
cd frontend
npm install
npm start
```

## 📚 مستندات

### 📖 راهنمای کامل
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - راهنمای کامل deployment روی production
- **[README_DEPLOYMENT.md](docs/README_DEPLOYMENT.md)** - راهنمای سریع deployment
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** - راهنمای مشارکت در پروژه

### 🛠️ ابزارهای مفید
- **[deploy.sh](deploy.sh)** - Script اتوماتیک برای deployment

## 🌟 ویژگی‌ها

- **🤖 چندین مدل AI**: OpenAI GPT, Google Gemini, Local Models
- **🔍 جستجوی هیبریدی**: Semantic + BM25
- **🌐 Web Crawling**: استخراج اطلاعات از وب‌سایت‌ها
- **💬 چت تعاملی**: رابط کاربری مدرن
- **👥 مدیریت کاربران**: سیستم احراز هویت و نقش‌ها
- **📊 داشبورد**: آمار و گزارش‌گیری
- **🔔 اعلان‌ها**: سیستم اطلاع‌رسانی
- **⚙️ تنظیمات پیشرفته**: مدیریت مدل‌ها و timezone
- **🔄 Concurrency**: مدیریت همزمان کاربران
- **📈 Performance**: بهینه‌سازی عملکرد
- **🔒 Security**: احراز هویت و مجوزدهی

## 🏗️ معماری

```
📁 ai-chatbot/
├── 📁 backend/           # FastAPI Backend
│   ├── 📁 app/
│   │   ├── 📁 api/       # API Endpoints
│   │   ├── 📁 core/      # Core Logic (Chatbot, RAG)
│   │   ├── 📁 services/  # Business Logic
│   │   ├── 📁 database/  # Database Models
│   │   └── 📁 middleware/ # Middleware
│   ├── 📁 migrations/    # Database migrations
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile       # Docker configuration
├── 📁 frontend/          # React Frontend
│   ├── 📁 src/
│   │   ├── 📁 components/
│   │   ├── 📁 pages/
│   │   ├── 📁 services/
│   │   └── 📁 contexts/
│   └── package.json
├── 📁 docs/              # مستندات
├── 📄 deploy.sh          # Script deployment
├── 📄 env.example        # Environment variables
└── 📄 text_processor.py  # Text processing utility
```

## 🔧 API Endpoints

### احراز هویت
- `POST /api/auth/login` - ورود کاربر
- `POST /api/auth/register` - ثبت‌نام
- `POST /api/auth/logout` - خروج
- `POST /api/auth/refresh` - تمدید توکن

### وب‌سایت‌ها
- `GET /api/websites` - لیست وب‌سایت‌ها
- `POST /api/websites/crawl` - کراول کردن وب‌سایت
- `GET /api/websites/{id}/rag-settings` - تنظیمات RAG
- `PUT /api/websites/{id}/rag-settings` - بروزرسانی تنظیمات RAG

### چت
- `POST /api/chats/chat` - ارسال پیام
- `GET /api/chats/history` - تاریخچه چت
- `GET /api/chats/{id}/messages` - پیام‌های چت

### داشبورد
- `GET /api/dashboard/stats` - آمار کلی
- `GET /api/dashboard/weekly-stats` - آمار هفتگی
- `GET /api/dashboard/system-settings` - تنظیمات سیستم

### مدیریت سیستم
- `GET /admin/system-status` - وضعیت سیستم
- `PUT /admin/system-settings` - بروزرسانی تنظیمات
- `GET /admin/timezone/available` - timezone های موجود
- `PUT /admin/timezone` - تنظیم timezone

### ویجت
- `POST /api/widget/chat` - چت از طریق ویجت

## 🚀 Deployment

### روش سریع (اتوماتیک)
```bash
./deploy.sh
```

### روش دستی
راهنمای کامل را در [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) مطالعه کنید.

## 🔧 تنظیمات مهم

### Environment Variables
فایل `env.example` شامل تمام متغیرهای مورد نیاز است:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# AI Models
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key

# Security
SECRET_KEY=your_secret_key

# System Settings
SYSTEM_TIMEZONE=Asia/Tehran
ENABLE_OPENAI=true
ENABLE_GEMINI=true
```

### مدل‌های AI
- **OpenAI GPT**: برای پاسخ‌های دقیق و خلاقانه
- **Google Gemini**: برای پردازش متن و تصویر
- **Local Models**: برای استفاده آفلاین

## 📊 Performance & Scalability

### Concurrency Management
- **ChatbotManager**: مدیریت همزمان chatbot instances
- **CrawlerQueue**: مدیریت همزمان crawl tasks
- **RateLimiter**: محدودیت نرخ درخواست

### Optimization
- **Caching**: کش کردن تنظیمات و نتایج
- **Connection Pooling**: مدیریت اتصالات دیتابیس
- **Async Processing**: پردازش غیرهمزمان

## 🛡️ Security

- **JWT Authentication**: احراز هویت امن
- **Role-based Access**: کنترل دسترسی بر اساس نقش
- **Rate Limiting**: محدودیت نرخ درخواست
- **Input Validation**: اعتبارسنجی ورودی‌ها
- **SQL Injection Protection**: محافظت در برابر SQL injection

## 🤝 مشارکت

برای مشارکت در پروژه، [راهنمای مشارکت](docs/CONTRIBUTING.md) را مطالعه کنید.

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است. برای جزئیات بیشتر، فایل [LICENSE](LICENSE) را مطالعه کنید.

---

**🎉 از استفاده از AI Chatbot لذت ببرید!** 