# RAG Chatbot

یک چت‌بات هوشمند مبتنی بر RAG (Retrieval-Augmented Generation) که می‌تواند از وب‌سایت‌های مختلف اطلاعات استخراج کند و به سؤالات کاربران پاسخ دهد.

## ویژگی‌ها

- استخراج اطلاعات از وب‌سایت‌ها
- جستجوی معنایی و هیبریدی
- پشتیبانی از چندین مدل زبانی (OpenAI, Gemini, Ollama)
- رابط کاربری وب
- API RESTful
- ذخیره‌سازی داده‌ها در PostgreSQL
- مدیریت جلسات چت
- پشتیبانی از چند زبان

## پیش‌نیازها

- Python 3.8+
- PostgreSQL 13+
- Docker و Docker Compose
- Ollama (برای مدل‌های محلی)

## نصب

1. مخزن را کلون کنید:
```bash
git clone https://github.com/yourusername/rag-chatbot.git
cd rag-chatbot
```

2. فایل `.env` را ایجاد کنید:
```bash
cp .env.example .env
```

3. متغیرهای محیطی را در `.env` تنظیم کنید.

4. با Docker Compose اجرا کنید:
```bash
docker-compose up -d
```

## استفاده

### API

پس از اجرای برنامه، API در آدرس `http://localhost:8000` در دسترس خواهد بود. مستندات Swagger در آدرس `http://localhost:8000/docs` قابل دسترسی است.

#### مثال‌های API

1. اضافه کردن یک وب‌سایت:
```bash
curl -X POST "http://localhost:8000/api/websites/crawl" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
```

2. جستجو در وب‌سایت‌ها:
```bash
curl -X GET "http://localhost:8000/api/websites/search?query=your%20question"
```

3. ارسال سؤال به چت‌بات:
```bash
curl -X POST "http://localhost:8000/api/chats/chat" \
     -H "Content-Type: application/json" \
     -d '{"question": "your question"}'
```

### رابط کاربری وب

رابط کاربری وب در آدرس `http://localhost:8000` در دسترس است.

## معماری

این پروژه از معماری لایه‌ای استفاده می‌کند:

- **API Layer**: FastAPI برای ارائه API RESTful
- **Service Layer**: سرویس‌های مختلف برای پردازش داده‌ها
- **Core Layer**: کلاس‌های اصلی برای مدیریت چت‌بات و جستجو
- **Database Layer**: SQLAlchemy برای تعامل با پایگاه داده

## مشارکت

لطفاً برای مشارکت در پروژه، [راهنمای مشارکت](CONTRIBUTING.md) را مطالعه کنید.

## مجوز

این پروژه تحت مجوز MIT منتشر شده است. برای جزئیات بیشتر، فایل [LICENSE](LICENSE) را مطالعه کنید. 