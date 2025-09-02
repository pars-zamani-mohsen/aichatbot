# 🤝 راهنمای مشارکت

## 📋 مقدمه

از مشارکت شما در پروژه AI Chatbot خوشحالیم! این راهنما به شما کمک می‌کند تا به راحتی در توسعه این پروژه مشارکت کنید.

## 🚀 شروع کار

### پیش‌نیازها
- Python 3.8+
- PostgreSQL 13+
- Node.js 16+
- npm
- Git

### راه‌اندازی محیط توسعه

#### 1. Fork کردن پروژه
```bash
# Fork کردن پروژه در GitHub
# سپس clone کردن fork شما
git clone https://github.com/your-username/ai-chatbot.git
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
```

#### 3. راه‌اندازی Frontend
```bash
cd frontend
npm install
npm start
```

## 🔧 ساختار پروژه

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
│   └── requirements.txt  # Python dependencies
├── 📁 frontend/          # React Frontend
│   ├── 📁 src/
│   │   ├── 📁 components/
│   │   ├── 📁 pages/
│   │   ├── 📁 services/
│   │   └── 📁 contexts/
│   └── package.json
├── 📁 docs/              # مستندات
└── 📄 env.example        # Environment variables
```

## 📝 قوانین کدنویسی

### Python (Backend)
- از **PEP 8** پیروی کنید
- از **type hints** استفاده کنید
- **Docstrings** برای توابع و کلاس‌ها بنویسید
- از **async/await** برای عملیات I/O استفاده کنید

### JavaScript/React (Frontend)
- از **ES6+** استفاده کنید
- از **functional components** استفاده کنید
- از **hooks** استفاده کنید
- از **Material-UI** برای UI استفاده کنید

### Git Commit Messages
از فرمت زیر استفاده کنید:
```
feat: add new feature
fix: resolve bug
docs: update documentation
style: improve code formatting
refactor: restructure code
test: add unit tests
```

## 🧪 تست‌نویسی

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📚 مستندات

### API Documentation
- از **FastAPI** برای مستندات API استفاده می‌کنیم
- مستندات در `/docs` و `/redoc` قابل دسترسی است

### Code Documentation
- از **docstrings** برای توابع استفاده کنید
- از **comments** برای توضیح منطق پیچیده استفاده کنید

## 🔄 فرآیند مشارکت

### 1. ایجاد Issue
- قبل از شروع کار، یک issue ایجاد کنید
- مشکل یا feature را به خوبی توضیح دهید

### 2. ایجاد Branch
```bash
git checkout -b feature/your-feature-name
# یا
git checkout -b fix/your-bug-fix
```

### 3. توسعه
- کد خود را بنویسید
- تست‌ها را اضافه کنید
- مستندات را بروزرسانی کنید

### 4. Commit و Push
```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature-name
```

### 5. ایجاد Pull Request
- PR را با توضیحات کامل ایجاد کنید
- تست‌ها را اجرا کنید
- کد review را انجام دهید

## 🐛 گزارش باگ

### اطلاعات مورد نیاز
- **توصیف باگ**: توضیح دقیق مشکل
- **مراحل تکرار**: چگونه می‌توان باگ را تکرار کرد
- **رفتار مورد انتظار**: چه اتفاقی باید بیفتد
- **رفتار فعلی**: چه اتفاقی می‌افتد
- **محیط**: OS، Browser، Version

### مثال
```
**توصیف باگ:**
در صفحه login، دکمه ورود کار نمی‌کند.

**مراحل تکرار:**
1. به صفحه login بروید
2. ایمیل و رمز عبور را وارد کنید
3. روی دکمه "ورود" کلیک کنید

**رفتار مورد انتظار:**
کاربر باید وارد سیستم شود.

**رفتار فعلی:**
هیچ اتفاقی نمی‌افتد.

**محیط:**
- OS: Ubuntu 20.04
- Browser: Chrome 91.0.4472.124
- Backend: v1.2.0
```

## 💡 پیشنهادات

### Feature Requests
- **مشکل**: چه مشکلی حل می‌شود؟
- **راه‌حل**: راه‌حل پیشنهادی چیست؟
- **مزایا**: چه مزایایی دارد؟
- **اولویت**: چقدر مهم است؟

## 📞 ارتباط

### کانال‌های ارتباطی
- **Issues**: برای گزارش باگ و feature requests
- **Discussions**: برای سوالات و بحث‌ها
- **Pull Requests**: برای مشارکت در کد

### قوانین ارتباط
- محترمانه باشید
- از زبان فارسی استفاده کنید
- صبور باشید
- کمک کنید

## 🎯 حوزه‌های مشارکت

### Backend
- **API Development**: توسعه endpoint های جدید
- **Database**: بهینه‌سازی queries
- **AI Integration**: بهبود مدل‌های AI
- **Performance**: بهینه‌سازی عملکرد

### Frontend
- **UI/UX**: بهبود رابط کاربری
- **Components**: توسعه کامپوننت‌های جدید
- **State Management**: بهبود مدیریت state
- **Responsive Design**: بهبود responsive بودن

### DevOps
- **Deployment**: بهبود فرآیند deployment
- **Monitoring**: اضافه کردن monitoring
- **Security**: بهبود امنیت
- **Documentation**: بهبود مستندات

## 🏆 تشکر

از مشارکت شما در این پروژه تشکر می‌کنیم! هر contribution، هرچند کوچک، ارزشمند است.

---

**🎉 با هم، می‌توانیم این پروژه را بهتر کنیم!** 