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

## 🏗️ معماری

```
📁 ai-chatbot/
├── 📁 backend/           # FastAPI Backend
│   ├── 📁 app/
│   │   ├── 📁 api/       # API Endpoints
│   │   ├── 📁 core/      # Core Logic
│   │   ├── 📁 services/  # Business Logic
│   │   └── 📁 database/  # Database Models
│   └── requirements.txt
├── 📁 frontend/          # React Frontend
│   ├── 📁 src/
│   │   ├── 📁 components/
│   │   ├── 📁 pages/
│   │   └── 📁 services/
│   └── package.json
├── 📁 docs/              # مستندات
├── deploy.sh             # Script deployment
└── env.example           # Environment variables
```

## 🔧 API Endpoints

### احراز هویت
- `POST /api/auth/login` - ورود کاربر
- `POST /api/auth/register` - ثبت‌نام
- `POST /api/auth/logout` - خروج

### وب‌سایت‌ها
- `GET /api/websites` - لیست وب‌سایت‌ها
- `POST /api/websites/crawl` - کراول کردن وب‌سایت
- `GET /api/websites/{id}/rag-settings` - تنظیمات RAG

### چت
- `POST /api/chats/chat` - ارسال پیام
- `GET /api/chats/history` - تاریخچه چت

### داشبورد
- `GET /api/dashboard/stats` - آمار کلی
- `GET /api/dashboard/weekly-stats` - آمار هفتگی

## 🚀 Deployment

برای deployment روی production، از script اتوماتیک استفاده کنید:

```bash
./deploy.sh
```

یا راهنمای کامل را در [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) مطالعه کنید.

## 🤝 مشارکت

برای مشارکت در پروژه، [راهنمای مشارکت](docs/CONTRIBUTING.md) را مطالعه کنید.

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است. برای جزئیات بیشتر، فایل [LICENSE](LICENSE) را مطالعه کنید.

---

**🎉 از استفاده از AI Chatbot لذت ببرید!** 