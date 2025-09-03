# راهنمای عیب‌یابی - سیستم چت‌بات هوشمند

## فهرست مطالب
- [مشکلات رایج](#مشکلات-رایج)
- [خطاهای احراز هویت](#خطاهای-احراز-هویت)
- [مشکلات چت و RAG](#مشکلات-چت-و-rag)
- [مشکلات کراولینگ](#مشکلات-کراولینگ)
- [مشکلات دیتابیس](#مشکلات-دیتابیس)
- [مشکلات عملکرد](#مشکلات-عملکرد)
- [مشکلات Deployment](#مشکلات-deployment)
- [لاگ‌ها و Debugging](#لاگ‌ها-و-debugging)

## مشکلات رایج

### 1. سرور راه‌اندازی نمی‌شود

#### علائم
```
Error: ModuleNotFoundError: No module named 'app'
Error: Address already in use
Error: Permission denied
```

#### راه‌حل‌ها

**مشکل ModuleNotFoundError:**
```bash
# اطمینان از اجرا در مسیر درست
cd /var/www/html/ai/backend

# فعال‌سازی virtual environment
source venv/bin/activate

# نصب dependencies
pip install -r requirements.txt

# اجرای سرور
python run.py
```

**مشکل Address already in use:**
```bash
# یافتن process استفاده‌کننده از پورت
sudo lsof -i :5000

# توقف process
sudo kill -9 <PID>

# یا تغییر پورت
export PORT=5001
python run.py
```

**مشکل Permission denied:**
```bash
# تغییر مجوزها
sudo chown -R $USER:$USER /var/www/html/ai
sudo chmod -R 755 /var/www/html/ai

# یا اجرا با sudo
sudo python run.py
```

### 2. خطای اتصال به دیتابیس

#### علائم
```
Error: connection to server at localhost failed
Error: authentication failed
Error: database does not exist
```

#### راه‌حل‌ها

**بررسی وضعیت PostgreSQL:**
```bash
# بررسی وضعیت سرویس
sudo systemctl status postgresql

# راه‌اندازی مجدد
sudo systemctl restart postgresql

# بررسی اتصال
sudo -u postgres psql -c "\l"
```

**بررسی تنظیمات اتصال:**
```bash
# بررسی فایل .env
cat .env | grep DATABASE

# تست اتصال
psql -h localhost -U username -d database_name
```

**ایجاد دیتابیس:**
```bash
sudo -u postgres createdb ai_database
sudo -u postgres psql -c "CREATE USER ai_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_database TO ai_user;"
```

### 3. خطای ChromaDB

#### علائم
```
Error: Collection not found
Error: Failed to connect to ChromaDB
Error: Permission denied to knowledge_base directory
```

#### راه‌حل‌ها

**بررسی مجوزهای ChromaDB:**
```bash
# بررسی مجوزها
ls -la knowledge_base/

# تغییر مجوزها
sudo chown -R $USER:$USER knowledge_base/
sudo chmod -R 755 knowledge_base/
```

**بازسازی کالکشن:**
```python
# اجرای اسکریپت بازسازی
python fix_collection_names.py
```

**بررسی وضعیت ChromaDB:**
```bash
# بررسی process های ChromaDB
ps aux | grep chroma

# راه‌اندازی مجدد
pkill -f chroma
```

## خطاهای احراز هویت

### 1. خطای "اعتبارنامه‌های نامعتبر"

#### علائم
```
HTTP 401: Unauthorized
{"detail": "اعتبارنامه‌های نامعتبر"}
```

#### راه‌حل‌ها

**بررسی توکن:**
```bash
# بررسی اعتبار توکن
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5000/api/auth/me

# دریافت توکن جدید
curl -X POST "http://localhost:5000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "password"}'
```

**بررسی تنظیمات JWT:**
```bash
# بررسی متغیرهای محیطی
echo $SECRET_KEY
echo $JWT_ALGORITHM

# تنظیم مجدد
export SECRET_KEY="your-secret-key"
export JWT_ALGORITHM="HS256"
```

### 2. خطای "توکن منقضی شده"

#### علائم
```
HTTP 401: Token expired
{"detail": "توکن منقضی شده است"}
```

#### راه‌حل‌ها

**تنظیم زمان انقضا:**
```python
# در app/core/auth.py
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 ساعت
```

**بررسی زمان سیستم:**
```bash
# بررسی زمان سیستم
date
timedatectl status

# تنظیم timezone
sudo timedatectl set-timezone Asia/Tehran
```

### 3. مشکل Rate Limiting

#### علائم
```
HTTP 429: Too Many Requests
{"detail": "محدودیت نرخ درخواست"}
```

#### راه‌حل‌ها

**بررسی تنظیمات Rate Limit:**
```bash
# بررسی تنظیمات در دیتابیس
psql -d ai_database -c "SELECT * FROM system_settings WHERE key LIKE '%rate%';"
```

**تنظیم مجدد Rate Limit:**
```python
# تنظیم rate limit جدید
from app.services.system_settings_service import SystemSettingsService

service = SystemSettingsService()
service.set_rate_limit_settings("chat", 50, 60)  # 50 درخواست در 60 ثانیه
```

## مشکلات چت و RAG

### 1. خطای "کالکشن برای این وب‌سایت ایجاد نشده است"

#### علائم
```
HTTP 400: کالکشن برای این وب‌سایت ایجاد نشده است
```

#### راه‌حل‌ها

**اجرای اسکریپت بازسازی:**
```bash
cd backend
python fix_collection_names.py
```

**بررسی وضعیت وب‌سایت:**
```bash
# بررسی وضعیت در دیتابیس
psql -d ai_database -c "SELECT id, url, status, collection_name FROM websites WHERE status = 'ready';"
```

**بازسازی دستی کالکشن:**
```python
from app.services.pipeline import EmbeddingPipeline

# بازسازی embeddings
pipeline = EmbeddingPipeline("example.com")
pipeline.run()
```

### 2. خطای "مدل AI در دسترس نیست"

#### علائم
```
Error: Model not available
Error: API key invalid
Error: Rate limit exceeded
```

#### راه‌حل‌ها

**بررسی API Keys:**
```bash
# بررسی متغیرهای محیطی
echo $OPENAI_API_KEY
echo $GEMINI_API_KEY

# تنظیم مجدد
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
```

**بررسی Rate Limits:**
```bash
# بررسی محدودیت‌های API
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

**تغییر نوع چت‌بات:**
```python
# استفاده از مدل محلی
chatbot_type = "ollama"  # به جای "openai"
```

### 3. مشکل کیفیت پاسخ‌ها

#### علائم
```
پاسخ‌های نامربوط
پاسخ‌های تکراری
پاسخ‌های خالی
```

#### راه‌حل‌ها

**بهبود تنظیمات RAG:**
```python
# تنظیم پارامترهای جستجو
top_k = 10  # افزایش تعداد نتایج
similarity_threshold = 0.7  # تنظیم آستانه شباهت
```

**بازسازی پایگاه دانش:**
```bash
# حذف و بازسازی embeddings
rm -rf knowledge_base/*
python create_knowledge_base.py
```

**تنظیم Prompt Engineering:**
```python
# بهبود prompt ها
system_prompt = """
شما یک دستیار هوشمند هستید که بر اساس اطلاعات ارائه شده پاسخ می‌دهید.
لطفاً فقط از اطلاعات موجود در context استفاده کنید.
اگر اطلاعات کافی نیست، صادقانه بگویید که نمی‌دانید.
"""
```

## مشکلات کراولینگ

### 1. کراولینگ متوقف می‌شود

#### علائم
```
کراولینگ در مرحله "processing" گیر می‌کند
خطای timeout
کراولینگ ناتمام
```

#### راه‌حل‌ها

**بررسی لاگ‌ها:**
```bash
# بررسی لاگ‌های کراولینگ
tail -f logs/crawler.log

# بررسی process های کراولینگ
ps aux | grep crawler
```

**تنظیم timeout:**
```python
# افزایش timeout
crawler_settings = {
    "timeout": 30,
    "max_retries": 3,
    "crawl_delay": 2
}
```

**راه‌اندازی مجدد:**
```bash
# توقف کراولینگ
pkill -f crawler

# راه‌اندازی مجدد
python -m app.services.crawler
```

### 2. خطای "صفحه قابل دسترس نیست"

#### علائم
```
Error: Page not accessible
Error: 403 Forbidden
Error: 429 Too Many Requests
```

#### راه‌حل‌ها

**تنظیم User-Agent:**
```python
# تنظیم User-Agent واقعی
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

**تنظیم Rate Limiting:**
```python
# کاهش سرعت کراولینگ
crawl_delay = 5  # 5 ثانیه بین درخواست‌ها
```

**استفاده از Proxy:**
```python
# تنظیم proxy
proxies = {
    "http": "http://proxy:port",
    "https": "https://proxy:port"
}
```

### 3. مشکل محتوای فارسی

#### علائم
```
کاراکترهای نامفهوم
مشکل encoding
متن‌های شکسته
```

#### راه‌حل‌ها

**تنظیم Encoding:**
```python
# تنظیم encoding صحیح
response.encoding = 'utf-8'
content = response.text.encode('utf-8').decode('utf-8')
```

**پردازش متن فارسی:**
```python
# حذف کاراکترهای اضافی
import re
clean_text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\s\w\.,!?]', '', text)
```

## مشکلات دیتابیس

### 1. خطای "Connection pool exhausted"

#### علائم
```
Error: Connection pool exhausted
Error: Too many connections
```

#### راه‌حل‌ها

**تنظیم Connection Pool:**
```python
# افزایش اندازه pool
DATABASE_URL = "postgresql://user:pass@host/db?pool_size=20&max_overflow=30"
```

**بررسی اتصالات فعال:**
```sql
-- بررسی اتصالات فعال
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- توقف اتصالات غیرضروری
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';
```

### 2. خطای "Table does not exist"

#### علائم
```
Error: relation "table_name" does not exist
Error: table not found
```

#### راه‌حل‌ها

**اجرای migrations:**
```bash
# اجرای migrations
cd backend
alembic upgrade head

# بررسی وضعیت migrations
alembic current
alembic history
```

**بازسازی جداول:**
```bash
# حذف و بازسازی
alembic downgrade base
alembic upgrade head
```

### 3. مشکل Performance دیتابیس

#### علائم
```
کوئری‌های کند
زمان پاسخ بالا
استفاده زیاد CPU
```

#### راه‌حل‌ها

**بهینه‌سازی کوئری:**
```sql
-- اضافه کردن index
CREATE INDEX idx_websites_owner_id ON websites(owner_id);
CREATE INDEX idx_chats_website_id ON chats(website_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- بررسی execution plan
EXPLAIN ANALYZE SELECT * FROM chats WHERE website_id = 1;
```

**تنظیم PostgreSQL:**
```bash
# تنظیمات performance
sudo nano /etc/postgresql/*/main/postgresql.conf

# تنظیمات مهم
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

## مشکلات عملکرد

### 1. سرعت پاسخ کند

#### علائم
```
زمان پاسخ > 5 ثانیه
تأخیر در UI
timeout errors
```

#### راه‌حل‌ها

**بهینه‌سازی RAG:**
```python
# کاهش تعداد نتایج جستجو
top_k = 5  # به جای 10

# استفاده از cache
@cache.memoize(ttl=3600)
def search_documents(query):
    return perform_search(query)
```

**بهینه‌سازی دیتابیس:**
```sql
-- اضافه کردن index های composite
CREATE INDEX idx_chats_website_created ON chats(website_id, created_at);
CREATE INDEX idx_messages_chat_created ON messages(chat_id, created_at);
```

**تنظیم Connection Pooling:**
```python
# تنظیم connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

### 2. مصرف بالای حافظه

#### علائم
```
Memory usage > 80%
Out of memory errors
Slow response times
```

#### راه‌حل‌ها

**بهینه‌سازی Embeddings:**
```python
# کاهش اندازه batch
batch_size = 32  # به جای 64

# آزادسازی حافظه
import gc
gc.collect()
```

**تنظیم ChromaDB:**
```python
# تنظیم cache size
client = chromadb.Client(
    Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./knowledge_base",
        anonymized_telemetry=False
    )
)
```

**محدودیت concurrent requests:**
```python
# تنظیم semaphore
semaphore = asyncio.Semaphore(10)  # حداکثر 10 درخواست همزمان
```

### 3. مشکل Concurrency

#### علائم
```
خطاهای race condition
پاسخ‌های اشتباه
خطاهای session
```

#### راه‌حل‌ها

**بهبود ChatbotManager:**
```python
# استفاده از RLock
from threading import RLock

class ChatbotManager:
    def __init__(self):
        self._locks = defaultdict(RLock)
        self._session_chatbots = {}
```

**مدیریت Session:**
```python
# ایجاد session ID منحصر به فرد
import uuid
session_id = str(uuid.uuid4())

# استفاده از session در چت
chatbot = chatbot_manager.get_chatbot(
    collection_name=collection_name,
    chatbot_type=chatbot_type,
    session_id=session_id
)
```

## مشکلات Deployment

### 1. خطای "Permission denied"

#### علائم
```
Error: Permission denied
Error: Cannot write to directory
Error: Access denied
```

#### راه‌حل‌ها

**تنظیم مجوزها:**
```bash
# تغییر مالکیت
sudo chown -R www-data:www-data /var/www/html/ai
sudo chmod -R 755 /var/www/html/ai

# تنظیم مجوزهای خاص
sudo chmod 755 /var/www/html/ai/backend
sudo chmod 644 /var/www/html/ai/backend/*.py
```

**تنظیم SELinux:**
```bash
# بررسی وضعیت SELinux
sestatus

# تنظیم context
sudo semanage fcontext -a -t httpd_exec_t "/var/www/html/ai/backend(/.*)?"
sudo restorecon -Rv /var/www/html/ai/backend
```

### 2. مشکل Environment Variables

#### علائم
```
Error: Environment variable not set
Error: Configuration not found
```

#### راه‌حل‌ها

**بررسی فایل .env:**
```bash
# بررسی محتوای .env
cat .env

# تنظیم متغیرهای ضروری
export DATABASE_URL="postgresql://user:pass@host/db"
export SECRET_KEY="your-secret-key"
export DEBUG="false"
```

**تنظیم systemd service:**
```bash
# ایجاد فایل service
sudo nano /etc/systemd/system/ai-chatbot.service

# محتوای فایل
[Unit]
Description=AI Chatbot Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/html/ai/backend
Environment=PATH=/var/www/html/ai/backend/venv/bin
ExecStart=/var/www/html/ai/backend/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. مشکل Nginx

#### علائم
```
Error: 502 Bad Gateway
Error: Connection refused
Error: Upstream server unavailable
```

#### راه‌حل‌ها

**بررسی وضعیت Nginx:**
```bash
# بررسی وضعیت
sudo systemctl status nginx

# بررسی لاگ‌ها
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

**تنظیم Nginx configuration:**
```nginx
# فایل /etc/nginx/sites-available/ai-chatbot
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**راه‌اندازی مجدد:**
```bash
# تست configuration
sudo nginx -t

# راه‌اندازی مجدد
sudo systemctl reload nginx
```

## لاگ‌ها و Debugging

### 1. فعال‌سازی Debug Mode

#### تنظیمات
```bash
# فعال‌سازی debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# یا در فایل .env
DEBUG=true
LOG_LEVEL=DEBUG
```

#### بررسی لاگ‌ها
```bash
# لاگ‌های FastAPI
tail -f logs/app.log

# لاگ‌های کراولینگ
tail -f logs/crawler.log

# لاگ‌های سیستم
journalctl -u ai-chatbot -f
```

### 2. بررسی Performance

#### ابزارهای monitoring
```bash
# بررسی CPU و Memory
htop
top

# بررسی Network
netstat -tulpn
ss -tulpn

# بررسی Disk I/O
iotop
iostat
```

#### Profiling کد
```python
# استفاده از cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# کد مورد نظر
your_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats()
```

### 3. بررسی خطاها

#### خطاهای رایج و راه‌حل‌ها

**خطای Import:**
```bash
# بررسی Python path
python -c "import sys; print(sys.path)"

# تنظیم PYTHONPATH
export PYTHONPATH="/var/www/html/ai/backend:$PYTHONPATH"
```

**خطای Database Connection:**
```bash
# تست اتصال
psql -h localhost -U username -d database_name -c "SELECT 1;"

# بررسی تنظیمات PostgreSQL
sudo -u postgres psql -c "SHOW listen_addresses;"
sudo -u postgres psql -c "SHOW port;"
```

**خطای ChromaDB:**
```bash
# بررسی وضعیت ChromaDB
ps aux | grep chroma

# بازسازی ChromaDB
rm -rf knowledge_base/*
python create_knowledge_base.py
```

## نکات پیشگیری

### 1. **Monitoring مداوم**
- استفاده از Prometheus و Grafana
- تنظیم alerting برای مشکلات
- بررسی لاگ‌ها به صورت منظم

### 2. **Backup منظم**
- Backup دیتابیس روزانه
- Backup فایل‌های مهم
- تست restore procedures

### 3. **Security Updates**
- به‌روزرسانی منظم سیستم
- بررسی امنیت dependencies
- استفاده از security headers

### 4. **Performance Tuning**
- بهینه‌سازی کوئری‌ها
- تنظیم cache policies
- monitoring performance metrics

### 5. **Documentation**
- مستندسازی تغییرات
- نگهداری runbooks
- آموزش تیم support

## منابع مفید

### 1. **مستندات رسمی**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

### 2. **ابزارهای Debugging**
- [Postman](https://www.postman.com/) - تست API
- [pgAdmin](https://www.pgadmin.org/) - مدیریت PostgreSQL
- [Redis Commander](https://github.com/joeferner/redis-commander) - مدیریت Redis

### 3. **Monitoring Tools**
- [Prometheus](https://prometheus.io/) - جمع‌آوری metrics
- [Grafana](https://grafana.com/) - visualization
- [ELK Stack](https://www.elastic.co/what-is/elk-stack) - log management

### 4. **Performance Tools**
- [Apache Bench](https://httpd.apache.org/docs/2.4/programs/ab.html) - load testing
- [Locust](https://locust.io/) - stress testing
- [cProfile](https://docs.python.org/3/library/profile.html) - Python profiling
