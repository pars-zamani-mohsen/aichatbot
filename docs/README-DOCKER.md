# AI Chatbot - Docker Deployment

این راهنما برای راه‌اندازی پنل AI Chatbot با استفاده از Docker و Docker Compose است.

## 🚀 ویژگی‌های Docker Setup

- **Backend**: FastAPI با Python 3.11
- **Frontend**: React با Nginx
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Vector DB**: ChromaDB
- **LLM**: Ollama (اختیاری)
- **Reverse Proxy**: Nginx
- **Process Manager**: Supervisor
- **Health Checks**: برای تمام سرویس‌ها

## 📋 پیش‌نیازها

- Docker 20.10+
- Docker Compose 2.0+
- حداقل 4GB RAM
- حداقل 20GB فضای خالی

## 🛠️ نصب و راه‌اندازی

### 1. کلون کردن پروژه
```bash
git clone <repository-url>
cd ai
```

### 2. تنظیم متغیرهای محیطی
```bash
cp env.example env.docker
# فایل env.docker را ویرایش کنید
nano env.docker
```

### 3. راه‌اندازی با اسکریپت خودکار
```bash
./docker-deploy.sh
```

### 4. راه‌اندازی دستی
```bash
# ساخت و راه‌اندازی سرویس‌ها
docker-compose up --build -d

# اجرای migration های دیتابیس
docker-compose exec backend alembic upgrade head
```

## 🌐 دسترسی به سرویس‌ها

| سرویس | URL | توضیحات |
|--------|-----|---------|
| Frontend | http://localhost:3000 | رابط کاربری |
| Backend API | http://localhost:8000 | API اصلی |
| Nginx Proxy | http://localhost | پروکسی اصلی |
| Database | localhost:5432 | PostgreSQL |
| Redis | localhost:6379 | Cache |
| ChromaDB | localhost:8001 | Vector Database |
| Ollama | localhost:11434 | Local LLM |

## 🔧 مدیریت سرویس‌ها

### مشاهده لاگ‌ها
```bash
# تمام لاگ‌ها
docker-compose logs -f

# لاگ سرویس خاص
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### راه‌اندازی مجدد سرویس
```bash
# راه‌اندازی مجدد تمام سرویس‌ها
docker-compose restart

# راه‌اندازی مجدد سرویس خاص
docker-compose restart backend
```

### توقف سرویس‌ها
```bash
# توقف سرویس‌ها
docker-compose down

# توقف و حذف volume ها
docker-compose down -v
```

### پاک‌سازی کامل
```bash
# حذف تمام container ها، image ها و volume ها
docker-compose down --rmi all --volumes --remove-orphans
```

## 📊 مانیتورینگ

### بررسی وضعیت سرویس‌ها
```bash
# وضعیت container ها
docker-compose ps

# استفاده از منابع
docker stats
```

### Health Checks
تمام سرویس‌ها دارای health check هستند:
```bash
# بررسی health check ها
docker-compose exec backend curl -f http://localhost:8000/health
docker-compose exec frontend curl -f http://localhost/health
```

## 🔒 امنیت

### SSL/TLS
برای فعال‌سازی SSL:
1. گواهی‌های SSL را در پوشه `ssl/` قرار دهید
2. تنظیمات nginx را برای HTTPS فعال کنید

### فایروال
پورت‌های پیش‌فرض:
- 80: HTTP
- 443: HTTPS
- 8000: Backend API
- 3000: Frontend
- 5432: PostgreSQL
- 6379: Redis
- 8001: ChromaDB
- 11434: Ollama

## 🗄️ Backup و Restore

### Backup دیتابیس
```bash
# ایجاد backup
docker-compose exec db pg_dump -U ai_user ai_chatbot > backup.sql

# Restore
docker-compose exec -T db psql -U ai_user ai_chatbot < backup.sql
```

### Backup Volume ها
```bash
# ایجاد backup از volume ها
docker run --rm -v ai_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

## 🐛 عیب‌یابی

### مشکلات رایج

1. **Port در حال استفاده**
   ```bash
   # بررسی پورت‌های در حال استفاده
   netstat -tulpn | grep :80
   ```

2. **مشکل در اتصال دیتابیس**
   ```bash
   # بررسی لاگ دیتابیس
   docker-compose logs db
   ```

3. **مشکل در build**
   ```bash
   # پاک‌سازی cache
   docker system prune -a
   ```

### لاگ‌های مفید
```bash
# لاگ supervisor
docker-compose exec backend cat /var/log/supervisor/supervisord.log

# لاگ nginx
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

## 📈 بهینه‌سازی

### تنظیمات حافظه
```yaml
# در docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### تنظیمات CPU
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
        reservations:
          cpus: '1.0'
```

## 🔄 به‌روزرسانی

### به‌روزرسانی کد
```bash
# Pull آخرین تغییرات
git pull

# Rebuild و restart
docker-compose up --build -d
```

### به‌روزرسانی دیتابیس
```bash
# اجرای migration های جدید
docker-compose exec backend alembic upgrade head
```

## 📞 پشتیبانی

در صورت بروز مشکل:
1. لاگ‌ها را بررسی کنید
2. وضعیت container ها را چک کنید
3. Health check ها را تست کنید
4. با تیم توسعه تماس بگیرید

---

**نکته**: این setup برای محیط production طراحی شده و شامل تمام ویژگی‌های امنیتی و مانیتورینگ لازم است.
