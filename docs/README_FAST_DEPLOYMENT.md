# 🚀 راهنمای سریع Deployment

## ⚡ روش سریع (اتوماتیک)

### 1. انتقال پروژه به سرور:
```bash
# روی سرور
cd /var/www/html
git clone https://github.com/your-repo/ai-chatbot.git ai
cd ai
```

### 2. اجرای script اتوماتیک:
```bash
./deploy.sh
```

**این script همه چیز را اتوماتیک انجام می‌دهد!** ✅

---

## 🛠️ روش دستی (مرحله به مرحله)

### مرحله 1: آماده‌سازی سرور
```bash
# نصب dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx postgresql postgresql-contrib git curl

# نصب certbot برای SSL
sudo apt install certbot python3-certbot-nginx
```

### مرحله 2: تنظیم Database
```bash
# شروع PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# ایجاد database
sudo -u postgres psql
CREATE DATABASE ai_db;
CREATE USER ai_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_db TO ai_user;
\q
```

### مرحله 3: تنظیم Environment Variables
```bash
cd /var/www/html/ai/backend
cp ../env.example .env
nano .env
```

**محتویات مهم .env:**
```env
DATABASE_URL=postgresql://ai_user:your_secure_password@localhost/ai_db
SECRET_KEY=your_super_secret_key_here
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
DEBUG=false
ENVIRONMENT=production
SYSTEM_TIMEZONE=Asia/Tehran
ENABLE_OPENAI=true
ENABLE_GEMINI=true
```

### مرحله 4: نصب Backend
```bash
cd /var/www/html/ai/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# اجرای migrations
cd ..
alembic upgrade head

# ایجاد admin user
cd backend
source venv/bin/activate
python create_admin_user.py
```

### مرحله 5: نصب Frontend
```bash
cd /var/www/html/ai/frontend
npm install
npm run build
```

### مرحله 6: تنظیم Nginx
```bash
sudo nano /etc/nginx/sites-available/ai-chatbot
```

**محتویات nginx config:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        root /var/www/html/ai/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:7000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ai-chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### مرحله 7: تنظیم Systemd Service
```bash
sudo nano /etc/systemd/system/ai-backend.service
```

**محتویات service file:**
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
ExecStart=/var/www/html/ai/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 7000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-backend
sudo systemctl start ai-backend
```

### مرحله 8: تنظیم SSL
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### مرحله 9: تنظیم Firewall
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

---

## 🔧 تنظیمات مهم

### 1. API Keys:
- **OpenAI API Key**: از [OpenAI Platform](https://platform.openai.com/api-keys) دریافت کنید
- **Google API Key**: از [Google Cloud Console](https://console.cloud.google.com/) دریافت کنید

### 2. Database Password:
- یک password قوی برای database انتخاب کنید
- در فایل .env استفاده کنید

### 3. Secret Key:
- یک secret key طولانی و تصادفی تولید کنید
- می‌توانید از این command استفاده کنید:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Domain Name:
- domain name خود را در nginx config جایگزین کنید
- در فایل .env در ALLOWED_HOSTS اضافه کنید

---

## 🧪 تست نهایی

### تست Backend:
```bash
curl http://localhost:7000/api/health
```

### تست Frontend:
```bash
curl http://localhost
```

### تست Admin Panel:
- باز کردن https://your-domain.com/admin
- ورود با: admin@example.com / admin123

---

## 🚨 Troubleshooting

### Backend نمی‌شروعد:
```bash
sudo journalctl -u ai-backend -f
```

### Nginx error:
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### Database connection:
```bash
sudo systemctl status postgresql
psql -h localhost -U ai_user -d ai_db
```

---

## 📊 Monitoring

### Status Check:
```bash
sudo systemctl status ai-backend
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Logs:
```bash
# Backend logs
sudo journalctl -u ai-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

---

## 🔄 Update Process

### برای update کردن:
```bash
cd /var/www/html/ai
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ..
alembic upgrade head

# Update frontend
cd frontend
npm install
npm run build

# Restart services
sudo systemctl restart ai-backend
sudo systemctl reload nginx
```

---

## 📞 Support

در صورت بروز مشکل:
1. چک کردن logs
2. بررسی system status
3. تست connectivity
4. بررسی permissions

**🎉 تبریک! پروژه شما آماده production است!**
