#!/bin/bash

# 🚀 AI Chatbot Deployment Script
# این script برای deployment اتوماتیک پروژه استفاده می‌شود

set -e  # در صورت خطا، script متوقف شود

# رنگ‌ها برای output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# توابع کمکی
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# چک کردن root access
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "این script نباید با root اجرا شود!"
        exit 1
    fi
}

# چک کردن dependencies
check_dependencies() {
    log_info "چک کردن dependencies..."
    
    # چک کردن Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 نصب نیست!"
        exit 1
    fi
    
    # چک کردن Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js نصب نیست!"
        exit 1
    fi
    
    # چک کردن npm
    if ! command -v npm &> /dev/null; then
        log_error "npm نصب نیست!"
        exit 1
    fi
    
    # چک کردن git
    if ! command -v git &> /dev/null; then
        log_error "git نصب نیست!"
        exit 1
    fi
    
    log_success "همه dependencies موجود هستند"
}

# نصب system dependencies
install_system_deps() {
    log_info "نصب system dependencies..."
    
    # تشخیص OS
    if [[ -f /etc/debian_version ]]; then
        # Ubuntu/Debian
        sudo apt update
        sudo apt install -y python3-venv nginx postgresql postgresql-contrib curl
    elif [[ -f /etc/redhat-release ]]; then
        # CentOS/RHEL
        sudo yum update -y
        sudo yum install -y python3-venv nginx postgresql postgresql-server curl
    else
        log_error "OS پشتیبانی نمی‌شود!"
        exit 1
    fi
    
    log_success "System dependencies نصب شدند"
}

# تنظیم database
setup_database() {
    log_info "تنظیم database..."
    
    # شروع PostgreSQL
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # ایجاد database و user
    sudo -u postgres psql -c "CREATE DATABASE ai_chatbot;" 2>/dev/null || log_warning "Database قبلاً وجود دارد"
    sudo -u postgres psql -c "CREATE USER ai_user WITH PASSWORD 'ai_chatbot_2024';" 2>/dev/null || log_warning "User قبلاً وجود دارد"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_chatbot TO ai_user;"
    
    log_success "Database تنظیم شد"
}

# نصب backend
install_backend() {
    log_info "نصب backend..."
    
    cd backend
    
    # ایجاد virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # نصب dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # اجرای migrations
    cd ..
    alembic upgrade head
    
    # ایجاد admin user
    cd backend
    source venv/bin/activate
    python create_admin_user.py
    
    cd ..
    log_success "Backend نصب شد"
}

# نصب frontend
install_frontend() {
    log_info "نصب frontend..."
    
    cd frontend
    
    # نصب dependencies
    npm install
    
    # build برای production
    npm run build
    
    cd ..
    log_success "Frontend نصب شد"
}

# تنظیم nginx
setup_nginx() {
    log_info "تنظیم nginx..."
    
    # ایجاد nginx config
    sudo tee /etc/nginx/sites-available/ai-chatbot > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        root /var/www/html/ai/frontend/build;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static files
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
}
EOF
    
    # فعال کردن سایت
    sudo ln -sf /etc/nginx/sites-available/ai-chatbot /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    
    log_success "Nginx تنظیم شد"
}

# تنظیم systemd service
setup_systemd() {
    log_info "تنظیم systemd service..."
    
    # ایجاد service file
    sudo tee /etc/systemd/system/ai-backend.service > /dev/null <<EOF
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
EOF
    
    # فعال کردن و شروع service
    sudo systemctl daemon-reload
    sudo systemctl enable ai-backend
    sudo systemctl start ai-backend
    
    log_success "Systemd service تنظیم شد"
}

# تنظیم permissions
setup_permissions() {
    log_info "تنظیم permissions..."
    
    sudo chown -R www-data:www-data /var/www/html/ai
    sudo chmod -R 755 /var/www/html/ai
    
    log_success "Permissions تنظیم شدند"
}

# تنظیم firewall
setup_firewall() {
    log_info "تنظیم firewall..."
    
    sudo ufw allow 22
    sudo ufw allow 80
    sudo ufw allow 443
    sudo ufw --force enable
    
    log_success "Firewall تنظیم شد"
}

# ایجاد backup script
create_backup_script() {
    log_info "ایجاد backup script..."
    
    tee backup.sh > /dev/null <<EOF
#!/bin/bash
BACKUP_DIR="/var/backups/ai-chatbot"
DATE=\$(date +%Y%m%d_%H%M%S)

# ایجاد backup directory
mkdir -p \$BACKUP_DIR

# Backup database
pg_dump ai_chatbot > \$BACKUP_DIR/db_backup_\$DATE.sql

# Backup code
tar -czf \$BACKUP_DIR/code_backup_\$DATE.tar.gz /var/www/html/ai

# حذف backup های قدیمی (بیشتر از 7 روز)
find \$BACKUP_DIR -name "*.sql" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: \$BACKUP_DIR"
EOF
    
    chmod +x backup.sh
    
    # اضافه کردن به crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * /var/www/html/ai/backup.sh") | crontab -
    
    log_success "Backup script ایجاد شد"
}

# تست نهایی
final_test() {
    log_info "انجام تست نهایی..."
    
    # تست backend
    if curl -s http://localhost:8000/api/health > /dev/null; then
        log_success "Backend درست کار می‌کند"
    else
        log_error "Backend کار نمی‌کند!"
        return 1
    fi
    
    # تست nginx
    if curl -s http://localhost > /dev/null; then
        log_success "Nginx درست کار می‌کند"
    else
        log_error "Nginx کار نمی‌کند!"
        return 1
    fi
    
    log_success "همه تست‌ها موفق بودند!"
}

# نمایش اطلاعات نهایی
show_final_info() {
    echo
    echo "🎉 ========================================="
    echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo "🎉 ========================================="
    echo
    echo "📋 اطلاعات مهم:"
    echo "   🌐 Frontend: http://$(hostname -I | awk '{print $1}')"
    echo "   🔧 Backend API: http://$(hostname -I | awk '{print $1}'):8000"
    echo "   👤 Admin Panel: http://$(hostname -I | awk '{print $1}')/admin"
    echo
    echo "🔑 اطلاعات ورود:"
    echo "   📧 Email: admin@example.com"
    echo "   🔐 Password: admin123"
    echo
    echo "📁 مسیرهای مهم:"
    echo "   📂 Project: /var/www/html/ai"
    echo "   📂 Backend: /var/www/html/ai/backend"
    echo "   📂 Frontend: /var/www/html/ai/frontend"
    echo "   📂 Logs: sudo journalctl -u ai-backend"
    echo
    echo "🛠️ دستورات مفید:"
    echo "   🔄 Restart Backend: sudo systemctl restart ai-backend"
    echo "   🔄 Restart Nginx: sudo systemctl restart nginx"
    echo "   📊 Status: sudo systemctl status ai-backend"
    echo "   📝 Logs: sudo journalctl -u ai-backend -f"
    echo
    echo "⚠️  نکات مهم:"
    echo "   1. فایل .env را در backend تنظیم کنید (cp ../env.example .env)"
    echo "   2. API keys را اضافه کنید"
    echo "   3. Domain name را در nginx تنظیم کنید"
    echo "   4. SSL certificate نصب کنید"
    echo
}

# Main function
main() {
    echo "🚀 AI Chatbot Deployment Script"
    echo "================================"
    echo
    
    # چک کردن root
    check_root
    
    # چک کردن dependencies
    check_dependencies
    
    # سوال برای ادامه
    read -p "آیا می‌خواهید deployment را شروع کنید؟ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment لغو شد"
        exit 0
    fi
    
    # اجرای مراحل
    install_system_deps
    setup_database
    install_backend
    install_frontend
    setup_nginx
    setup_systemd
    setup_permissions
    setup_firewall
    create_backup_script
    final_test
    show_final_info
}

# اجرای main function
main "$@"
