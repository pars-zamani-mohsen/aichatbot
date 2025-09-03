# 🚀 راهنمای Deployment - سیستم چت‌بات هوشمند

## فهرست مطالب
- [معرفی](#معرفی)
- [پیش‌نیازها](#پیش‌نیازها)
- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [تنظیمات Production](#تنظیمات-production)
- [SSL و Domain](#ssl-و-domain)
- [Monitoring و Logging](#monitoring-و-logging)
- [Backup و Recovery](#backup-و-recovery)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

## معرفی

این راهنما مراحل کامل deployment سیستم چت‌بات هوشمند روی production server را توضیح می‌دهد.

### ویژگی‌های Production
- 🔒 امنیت بالا
- 🚀 عملکرد بهینه
- 📊 Monitoring کامل
- 🔄 Auto-scaling
- 💾 Backup خودکار
- 🛡️ DDoS Protection

## پیش‌نیازها

### سخت‌افزار
```bash
# حداقل نیازمندی‌ها
CPU: 4 cores
RAM: 8GB
Storage: 100GB SSD
Network: 100Mbps

# توصیه شده
CPU: 8+ cores
RAM: 16GB+
Storage: 500GB+ SSD
Network: 1Gbps+
```

### نرم‌افزار
```bash
# سیستم عامل
Ubuntu 20.04 LTS یا 22.04 LTS
CentOS 8+ یا RHEL 8+

# سرویس‌های پایه
Docker 20.10+
Docker Compose 2.0+
Nginx 1.18+
PostgreSQL 13+
Redis 6+
```

### دامنه و SSL
- دامنه معتبر
- گواهی SSL (Let's Encrypt)
- DNS Records

## نصب و راه‌اندازی

### 1. آماده‌سازی سرور

```bash
# به‌روزرسانی سیستم
sudo apt update && sudo apt upgrade -y

# نصب پکیج‌های ضروری
sudo apt install -y curl wget git unzip software-properties-common

# نصب Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# نصب Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# نصب Nginx
sudo apt install -y nginx

# نصب PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# نصب Redis
sudo apt install -y redis-server
```

### 2. کلون کردن پروژه

```bash
# کلون کردن پروژه
git clone https://github.com/your-username/ai-chatbot.git
cd ai-chatbot

# تغییر به branch production
git checkout production
```

### 3. تنظیم Environment Variables

```bash
# ایجاد فایل .env
cp .env.example .env

# ویرایش فایل .env
nano .env
```

#### محتوای فایل .env
```env
# Database
DATABASE_URL=postgresql://ai_user:secure_password@localhost/ai_database
POSTGRES_DB=ai_database
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=secure_password

# Security
SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Models
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key

# System Settings
DEBUG=false
LOG_LEVEL=INFO
TIMEZONE=Asia/Tehran
ENVIRONMENT=production

# Redis
REDIS_URL=redis://localhost:6379

# ChromaDB
CHROMA_BASE_DIR=/var/www/html/ai/backend/knowledge_base

# Rate Limiting
RATE_LIMIT_CHAT=20
RATE_LIMIT_CRAWL=5
RATE_LIMIT_WINDOW=60

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIR=/var/www/html/ai/backend/uploads
```

### 4. تنظیم دیتابیس

```bash
# ورود به PostgreSQL
sudo -u postgres psql

# ایجاد دیتابیس و کاربر
CREATE DATABASE ai_database;
CREATE USER ai_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_database TO ai_user;
ALTER USER ai_user CREATEDB;
\q

# اجرای migrations
cd backend
alembic upgrade head
```

### 5. تنظیم Nginx

```bash
# ایجاد فایل configuration
sudo nano /etc/nginx/sites-available/ai-chatbot
```

#### محتوای فایل Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;
    
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
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health Check
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        # ... rest of proxy settings
    }
}
```

```bash
# فعال‌سازی سایت
sudo ln -s /etc/nginx/sites-available/ai-chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. تنظیم SSL با Let's Encrypt

```bash
# نصب Certbot
sudo apt install -y certbot python3-certbot-nginx

# دریافت گواهی SSL
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# تنظیم auto-renewal
sudo crontab -e
# اضافه کردن این خط:
0 12 * * * /usr/bin/certbot renew --quiet
```

### 7. راه‌اندازی با Docker

```bash
# ساخت Docker images
docker-compose -f docker-compose.prod.yml build

# راه‌اندازی سرویس‌ها
docker-compose -f docker-compose.prod.yml up -d

# بررسی وضعیت
docker-compose -f docker-compose.prod.yml ps
```

## تنظیمات Production

### 1. تنظیمات PostgreSQL

```bash
# ویرایش postgresql.conf
sudo nano /etc/postgresql/*/main/postgresql.conf

# تنظیمات مهم
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 2. تنظیمات Redis

```bash
# ویرایش redis.conf
sudo nano /etc/redis/redis.conf

# تنظیمات مهم
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 3. تنظیمات System

```bash
# تنظیم limits
sudo nano /etc/security/limits.conf

# اضافه کردن این خطوط
www-data soft nofile 65536
www-data hard nofile 65536
root soft nofile 65536
root hard nofile 65536

# تنظیم sysctl
sudo nano /etc/sysctl.conf

# اضافه کردن این خطوط
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
```

### 4. Firewall

```bash
# نصب UFW
sudo apt install -y ufw

# تنظیم قوانین
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22

# فعال‌سازی
sudo ufw enable
```

## Monitoring و Logging

### 1. نصب Prometheus

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
```

### 2. نصب Grafana

```yaml
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana
```

### 3. Log Aggregation

```bash
# نصب Filebeat
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-7.17.0-amd64.deb
sudo dpkg -i filebeat-7.17.0-amd64.deb

# تنظیم Filebeat
sudo nano /etc/filebeat/filebeat.yml
```

## Backup و Recovery

### 1. Backup دیتابیس

```bash
# ایجاد script backup
sudo nano /usr/local/bin/backup-db.sh
```

#### محتوای script backup
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/ai-chatbot"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="ai_database"
DB_USER="ai_user"

# ایجاد پوشه backup
mkdir -p $BACKUP_DIR

# Backup دیتابیس
pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Backup فایل‌ها
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /var/www/html/ai/backend/knowledge_base

# حذف backup های قدیمی (بیش از 30 روز)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# تنظیم مجوزها
sudo chmod +x /usr/local/bin/backup-db.sh

# اضافه کردن به crontab
sudo crontab -e
# اضافه کردن این خط:
0 2 * * * /usr/local/bin/backup-db.sh
```

### 2. Recovery

```bash
# بازیابی دیتابیس
psql -U ai_user -d ai_database < /var/backups/ai-chatbot/db_backup_20240101_120000.sql

# بازیابی فایل‌ها
tar -xzf /var/backups/ai-chatbot/files_backup_20240101_120000.tar.gz -C /
```

## Scaling

### 1. Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  backend:
    image: ai-chatbot-backend
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=postgresql://user:pass@load-balancer/db
    depends_on:
      - load-balancer
```

### 2. Load Balancer

```nginx
# nginx-load-balancer.conf
upstream backend_servers {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Auto-scaling

```bash
# نصب Kubernetes
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# تنظیم HPA (Horizontal Pod Autoscaler)
kubectl autoscale deployment ai-chatbot-backend --cpu-percent=70 --min=2 --max=10
```

## Troubleshooting

### 1. مشکلات رایج

#### سرور راه‌اندازی نمی‌شود
```bash
# بررسی لاگ‌ها
docker-compose logs backend
sudo journalctl -u ai-chatbot -f

# بررسی پورت‌ها
sudo netstat -tulpn | grep :5000
sudo lsof -i :5000
```

#### مشکل دیتابیس
```bash
# بررسی وضعیت PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"

# بررسی اتصالات
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

#### مشکل Nginx
```bash
# بررسی configuration
sudo nginx -t

# بررسی لاگ‌ها
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### 2. Performance Issues

```bash
# بررسی منابع سیستم
htop
iotop
netstat -i

# بررسی دیتابیس
sudo -u postgres psql -c "SELECT * FROM pg_stat_database;"
sudo -u postgres psql -c "SELECT * FROM pg_stat_user_tables;"
```

### 3. Security Issues

```bash
# بررسی فایل‌های log
sudo tail -f /var/log/auth.log
sudo tail -f /var/log/nginx/access.log

# بررسی process های مشکوک
ps aux | grep -v grep | grep -E "(python|node|docker)"
```

## نکات مهم

### 1. **امنیت**
- همیشه از HTTPS استفاده کنید
- فایل‌های حساس را در .env نگه دارید
- Firewall را فعال کنید
- به‌روزرسانی‌های امنیتی را نصب کنید

### 2. **Performance**
- از CDN برای فایل‌های استاتیک استفاده کنید
- Caching را بهینه کنید
- Database indexing را بررسی کنید
- Monitoring را فعال کنید

### 3. **Backup**
- Backup منظم داشته باشید
- Backup را در مکان امن نگه دارید
- Recovery procedure را تست کنید
- Backup automation را پیاده‌سازی کنید

### 4. **Monitoring**
- Health checks را پیاده‌سازی کنید
- Alerting را تنظیم کنید
- Metrics را جمع‌آوری کنید
- Log aggregation را فعال کنید

## منابع مفید

- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

---

**🚀 موفقیت در deployment!**
