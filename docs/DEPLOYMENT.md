# 🚀 راهنمای Deployment روی Production

## 📋 مراحل کلی
1. **آماده‌سازی سرور**
2. **نصب dependencies**
3. **تنظیم environment variables**
4. **تنظیم database**
5. **Deploy کردن backend**
6. **Deploy کردن frontend**
7. **تنظیم reverse proxy (nginx)**
8. **تنظیم SSL/HTTPS**
9. **تنظیم systemd services**
10. **تنظیم monitoring و backup**

---

## 🖥️ مرحله 1: آماده‌سازی سرور

### نصب packages مورد نیاز:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx postgresql postgresql-contrib git curl

# CentOS/RHEL
sudo yum update
sudo yum install -y python3 python3-pip nodejs npm nginx postgresql postgresql-server git curl
```

### نصب Docker (اختیاری):
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

---

## 🗄️ مرحله 2: تنظیم Database

### نصب و تنظیم PostgreSQL:
```bash
# Ubuntu/Debian
sudo systemctl start postgresql
sudo systemctl enable postgresql

# ایجاد کاربر و دیتابیس
sudo -u postgres psql
```

```sql
-- در PostgreSQL
CREATE DATABASE ai_db;
CREATE USER ai_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_db TO ai_user;
\q
```

---

## ⚙️ مرحله 3: تنظیم Environment Variables

### ایجاد فایل .env در backend:
```bash
cd /var/www/html/ai/backend
cp ../env.example .env
nano .env
```

### محتوای .env:
```env
# Database Configuration
DATABASE_URL=postgresql://ai_user:your_secure_password@localhost/ai_db

# Security Settings
SECRET_KEY=your_super_secret_key_here_make_it_long_and_random_at_least_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Model API Keys
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# System Settings
SYSTEM_TIMEZONE=Asia/Tehran
ENABLE_OPENAI=true
ENABLE_GEMINI=true
ENABLE_LOCAL=false

# Production Settings
DEBUG=false
ENVIRONMENT=production
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads

# ChromaDB Settings
CHROMA_PERSIST_DIRECTORY=chroma_db
CHROMA_ANONYMIZED_TELEMETRY=false

# CORS Settings
CORS_ORIGINS=["http://localhost:3000", "https://your-domain.com"]
CORS_ALLOW_CREDENTIALS=true
```

---

## 🔧 مرحله 4: Deploy Backend

### نصب dependencies:
```bash
cd /var/www/html/ai/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### اجرای migrations:
```bash
# از root directory
cd /var/www/html/ai
alembic upgrade head
```

### ایجاد admin user:
```bash
cd backend
source venv/bin/activate
python create_admin_user.py
```

### تست backend:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🎨 مرحله 5: Deploy Frontend

### نصب dependencies:
```bash
cd /var/www/html/ai/frontend
npm install
```

### Build کردن برای production:
```bash
npm run build
```

### تست frontend:
```bash
# نصب serve برای تست
npm install -g serve
serve -s build -l 3000
```

---

## 🌐 مرحله 6: تنظیم Nginx

### ایجاد فایل nginx config:
```bash
sudo nano /etc/nginx/sites-available/ai-chatbot
```

### محتوای nginx config:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Frontend
    location / {
        root /var/www/html/ai/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Cache static files
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }

    # WebSocket support (اگر نیاز باشد)
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### فعال کردن سایت:
```bash
sudo ln -s /etc/nginx/sites-available/ai-chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔒 مرحله 7: تنظیم SSL/HTTPS

### نصب Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
```

### دریافت SSL certificate:
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### تنظیم auto-renewal:
```bash
sudo crontab -e
# اضافه کردن این خط:
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 🚀 مرحله 8: تنظیم Systemd Services

### ایجاد service برای backend:
```bash
sudo nano /etc/systemd/system/ai-backend.service
```

### محتوای backend service:
```ini
[Unit]
Description=AI Chatbot Backend
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/html/ai/backend
Environment=PATH=/var/www/html/ai/backend/venv/bin
ExecStart=/var/www/html/ai/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### فعال کردن و شروع service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-backend
sudo systemctl start ai-backend
sudo systemctl status ai-backend
```

---

## 🔧 مرحله 9: تنظیمات نهایی

### تنظیم permissions:
```bash
sudo chown -R www-data:www-data /var/www/html/ai
sudo chmod -R 755 /var/www/html/ai
```

### تنظیم firewall:
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### تنظیم log rotation:
```bash
sudo nano /etc/logrotate.d/ai-chatbot
```

```conf
/var/www/html/ai/backend/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

---

## 📊 مرحله 10: Monitoring و Maintenance

### نصب monitoring tools:
```bash
# نصب htop برای monitoring
sudo apt install htop

# نصب logwatch برای log monitoring
sudo apt install logwatch
```

### تنظیم backup:
```bash
# ایجاد script backup
nano /var/www/html/ai/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/ai-chatbot"
DATE=$(date +%Y%m%d_%H%M%S)

# ایجاد backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump ai_db > $BACKUP_DIR/db_backup_$DATE.sql

# Backup code
tar -czf $BACKUP_DIR/code_backup_$DATE.tar.gz /var/www/html/ai

# حذف backup های قدیمی (بیشتر از 7 روز)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
chmod +x /var/www/html/ai/backup.sh

# اضافه کردن به crontab
sudo crontab -e
# اضافه کردن این خط:
0 2 * * * /var/www/html/ai/backup.sh
```

---

## 🧪 مرحله 11: تست نهایی

### تست API endpoints:
```bash
# تست health check
curl https://your-domain.com/api/health

# تست admin login
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"your_password"}'
```

### تست frontend:
- باز کردن https://your-domain.com
- تست login/logout
- تست chat functionality
- تست admin panel

---

## 🚨 Troubleshooting

### مشکلات رایج:

#### 1. Backend نمی‌شروعد:
```bash
# چک کردن logs
sudo journalctl -u ai-backend -f

# چک کردن permissions
ls -la /var/www/html/ai/backend/
```

#### 2. Database connection error:
```bash
# تست connection
psql -h localhost -U ai_user -d ai_db

# چک کردن PostgreSQL status
sudo systemctl status postgresql
```

#### 3. Frontend load نمی‌شود:
```bash
# چک کردن nginx logs
sudo tail -f /var/log/nginx/error.log

# چک کردن nginx config
sudo nginx -t
```

#### 4. SSL certificate issues:
```bash
# renew certificate
sudo certbot renew

# چک کردن certificate status
sudo certbot certificates
```

---

## 📈 Performance Optimization

### تنظیمات nginx برای performance:
```nginx
# اضافه کردن به nginx config
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

# تنظیم worker processes
worker_processes auto;
worker_connections 1024;
```

### تنظیمات PostgreSQL:
```bash
# تنظیم shared_buffers
sudo nano /etc/postgresql/*/main/postgresql.conf
# shared_buffers = 256MB
# effective_cache_size = 1GB
```

---

## 🔄 Update Process

### برای update کردن:
```bash
# 1. Backup
/var/www/html/ai/backup.sh

# 2. Pull changes
cd /var/www/html/ai
git pull origin main

# 3. Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# 4. Update frontend
cd ../frontend
npm install
npm run build

# 5. Restart services
sudo systemctl restart ai-backend
sudo systemctl reload nginx
```

---

## ✅ Checklist نهایی

- [ ] سرور آماده شده
- [ ] Database تنظیم شده
- [ ] Environment variables تنظیم شده
- [ ] Backend deploy شده
- [ ] Frontend build شده
- [ ] Nginx تنظیم شده
- [ ] SSL certificate نصب شده
- [ ] Systemd services فعال شده
- [ ] Firewall تنظیم شده
- [ ] Backup system آماده شده
- [ ] Monitoring فعال شده
- [ ] تست نهایی انجام شده

---

## 📞 Support

در صورت بروز مشکل:
1. چک کردن logs
2. بررسی system status
3. تست connectivity
4. بررسی permissions
5. مراجعه به troubleshooting section

**🎉 تبریک! پروژه شما آماده production است!**
