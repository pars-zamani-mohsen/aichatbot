# مستندات API - سیستم چت‌بات هوشمند

## فهرست مطالب
- [معرفی](#معرفی)
- [احراز هویت](#احراز-هویت)
- [نقاط پایانی API](#نقاط-پایانی-api)
- [مدل‌های داده](#مدل‌های-داده)
- [کدهای خطا](#کدهای-خطا)
- [مثال‌های استفاده](#مثال‌های-استفاده)

## معرفی

این API برای سیستم چت‌بات هوشمند با قابلیت RAG (Retrieval-Augmented Generation) طراحی شده است. سیستم از مدل‌های مختلف AI مانند OpenAI، Gemini و Ollama پشتیبانی می‌کند.

### ویژگی‌های کلیدی
- 🔐 احراز هویت JWT
- 🌐 مدیریت چندین وب‌سایت
- 🤖 پشتیبانی از چندین مدل AI
- 📊 داشبورد و گزارشات
- 🔍 جستجوی هوشمند در اسناد
- 📈 آمار و تحلیل عملکرد

## احراز هویت

### دریافت توکن
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

### پاسخ
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user"
  }
}
```

### استفاده از توکن
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## نقاط پایانی API

### احراز هویت و کاربران

#### ثبت‌نام کاربر جدید
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "password123",
  "full_name": "نام کامل کاربر"
}
```

#### ورود کاربر
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

#### بازیابی رمز عبور
```http
POST /api/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### بازنشانی رمز عبور
```http
POST /api/auth/reset-password
Content-Type: application/json

{
  "token": "reset_token_here",
  "new_password": "newpassword123"
}
```

### مدیریت وب‌سایت‌ها

#### دریافت لیست وب‌سایت‌ها
```http
GET /api/websites/
Authorization: Bearer {token}
```

#### ایجاد وب‌سایت جدید
```http
POST /api/websites/
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://example.com",
  "name": "نام وب‌سایت",
  "description": "توضیحات وب‌سایت"
}
```

#### شروع کراولینگ وب‌سایت
```http
POST /api/websites/{website_id}/crawl
Authorization: Bearer {token}
Content-Type: application/json

{
  "max_pages": 100,
  "max_depth": 3,
  "crawl_delay": 1
}
```

#### دریافت وضعیت کراولینگ
```http
GET /api/websites/{website_id}/status
Authorization: Bearer {token}
```

### چت و گفتگو

#### ایجاد چت جدید
```http
POST /api/chats/
Authorization: Bearer {token}
Content-Type: application/json

{
  "website_id": 1,
  "message": "سوال کاربر",
  "chatbot_type": "openai",
  "session_id": "unique_session_id"
}
```

#### دریافت تاریخچه چت‌ها
```http
GET /api/chats/list?website_id=1
Authorization: Bearer {token}
```

#### دریافت آمار چت‌ها
```http
GET /api/chats/stats?website_id=1
Authorization: Bearer {token}
```

### داشبورد و گزارشات

#### آمار کلی داشبورد
```http
GET /api/dashboard/stats
Authorization: Bearer {token}
```

#### آمار هفتگی
```http
GET /api/dashboard/weekly-stats
Authorization: Bearer {token}
```

#### فعالیت‌های اخیر
```http
GET /api/dashboard/recent-activity?limit=10
Authorization: Bearer {token}
```

#### گزارشات کاربر
```http
GET /api/dashboard/user/reports?time_range=7d
Authorization: Bearer {token}
```

### مدیریت سیستم (فقط ادمین)

#### آمار کلی سیستم
```http
GET /api/dashboard/admin/stats
Authorization: Bearer {token}
```

#### لیست کاربران
```http
GET /api/dashboard/admin/users?page=1&limit=20
Authorization: Bearer {token}
```

#### مدیریت وب‌سایت‌ها
```http
GET /api/dashboard/admin/websites?page=1&limit=20
Authorization: Bearer {token}
```

#### تنظیمات سیستم
```http
GET /api/dashboard/admin/system-settings
Authorization: Bearer {token}
```

## مدل‌های داده

### User
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "نام کامل",
  "role": "user",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "last_login": "2025-01-01T12:00:00Z"
}
```

### Website
```json
{
  "id": 1,
  "url": "https://example.com",
  "name": "نام وب‌سایت",
  "description": "توضیحات",
  "status": "ready",
  "owner_id": 1,
  "collection_name": "example.com",
  "crawl_info": {
    "total_pages": 50,
    "crawled_at": "2025-01-01T00:00:00Z"
  },
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Chat
```json
{
  "id": 1,
  "website_id": 1,
  "session_id": "session_123",
  "created_at": "2025-01-01T00:00:00Z",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "سوال کاربر",
      "created_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "پاسخ چت‌بات",
      "created_at": "2025-01-01T00:00:01Z"
    }
  ]
}
```

## کدهای خطا

### کدهای HTTP
- `200` - موفقیت
- `201` - ایجاد شده
- `400` - درخواست نامعتبر
- `401` - احراز هویت نشده
- `403` - دسترسی غیرمجاز
- `404` - یافت نشد
- `429` - محدودیت نرخ درخواست
- `500` - خطای داخلی سرور

### پیام‌های خطا
```json
{
  "detail": "توضیحات خطا",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

## مثال‌های استفاده

### مثال کامل: ایجاد وب‌سایت و شروع چت

#### 1. ورود کاربر
```bash
curl -X POST "http://localhost:5000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

#### 2. ایجاد وب‌سایت
```bash
curl -X POST "http://localhost:5000/api/websites/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "name": "وب‌سایت نمونه",
    "description": "توضیحات وب‌سایت"
  }'
```

#### 3. شروع کراولینگ
```bash
curl -X POST "http://localhost:5000/api/websites/1/crawl" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "max_pages": 50,
    "max_depth": 2,
    "crawl_delay": 1
  }'
```

#### 4. شروع چت
```bash
curl -X POST "http://localhost:5000/api/chats/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": 1,
    "message": "سلام، لطفاً درباره وب‌سایت توضیح دهید",
    "chatbot_type": "openai",
    "session_id": "chat_session_123"
  }'
```

## نکات مهم

### Rate Limiting
- **چت**: 20 درخواست در هر 60 ثانیه
- **کراول**: 5 درخواست در هر 300 ثانیه
- **API عمومی**: 100 درخواست در هر 60 ثانیه

### Timezone
تمام تاریخ‌ها در timezone سیستم (Asia/Tehran) ذخیره و نمایش داده می‌شوند.

### Session Management
هر چت یک `session_id` منحصر به فرد دارد که برای حفظ context استفاده می‌شود.

### Error Handling
همیشه از try-catch استفاده کنید و کدهای خطا را بررسی کنید.

## پشتیبانی

برای سوالات و مشکلات فنی:
- 📧 ایمیل: support@example.com
- 📖 مستندات: https://docs.example.com
- 🐛 گزارش باگ: https://github.com/example/repo/issues
