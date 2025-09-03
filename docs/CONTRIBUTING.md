# راهنمای مشارکت - سیستم چت‌بات هوشمند

## 🎯 مقدمه

از مشارکت شما در توسعه سیستم چت‌بات هوشمند استقبال می‌کنیم! این راهنما به شما کمک می‌کند تا به راحتی در پروژه مشارکت کنید.

## 📋 فهرست مطالب

- [نحوه مشارکت](#نحوه-مشارکت)
- [راه‌اندازی محیط توسعه](#راه‌اندازی-محیط-توسعه)
- [استانداردهای کد](#استانداردهای-کد)
- [نوشتن تست](#نوشتن-تست)
- [ارسال Pull Request](#ارسال-pull-request)
- [گزارش باگ](#گزارش-باگ)
- [درخواست ویژگی](#درخواست-ویژگی)
- [سوالات متداول](#سوالات-متداول)

## 🚀 نحوه مشارکت

### انواع مشارکت

- 🐛 **گزارش باگ**: شناسایی و گزارش مشکلات
- ✨ **درخواست ویژگی**: پیشنهاد ویژگی‌های جدید
- 🔧 **رفع باگ**: حل مشکلات موجود
- 🚀 **ویژگی جدید**: پیاده‌سازی قابلیت‌های جدید
- 📚 **مستندات**: بهبود مستندات پروژه
- 🧪 **تست**: نوشتن تست‌های جدید
- 🌐 **ترجمه**: ترجمه به زبان‌های مختلف

### مراحل مشارکت

1. **Fork کردن پروژه**
2. **ایجاد branch جدید**
3. **انجام تغییرات**
4. **نوشتن تست**
5. **ارسال Pull Request**

## 🛠️ راه‌اندازی محیط توسعه

### پیش‌نیازها

```bash
# Python 3.9+
python --version

# Node.js 16+
node --version

# Git
git --version

# Docker (اختیاری)
docker --version
```

### راه‌اندازی Backend

```bash
# کلون کردن پروژه
git clone https://github.com/your-username/ai-chatbot.git
cd ai-chatbot

# ایجاد branch جدید
git checkout -b feature/your-feature-name

# راه‌اندازی Backend
cd backend

# ایجاد virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# یا
venv\Scripts\activate     # Windows

# نصب dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # برای development

# تنظیم متغیرهای محیطی
cp .env.example .env
# ویرایش فایل .env

# راه‌اندازی دیتابیس
sudo systemctl start postgresql
sudo systemctl start redis

# اجرای migrations
alembic upgrade head

# راه‌اندازی سرور
python run.py
```

### راه‌اندازی Frontend

```bash
cd ../frontend

# نصب dependencies
npm install

# راه‌اندازی در حالت development
npm start

# ساخت برای production
npm run build
```

### راه‌اندازی با Docker

```bash
# راه‌اندازی تمام سرویس‌ها
docker-compose up -d

# بررسی وضعیت
docker-compose ps

# مشاهده لاگ‌ها
docker-compose logs -f
```

## 📝 استانداردهای کد

### Python (Backend)

#### Style Guide

```python
# پیروی از PEP 8
import os
from typing import List, Optional
from datetime import datetime, timedelta

# نام‌گذاری متغیرها
user_name = "John"           # snake_case
MAX_RETRY_COUNT = 3          # UPPER_CASE برای constants
UserModel = User             # PascalCase برای کلاس‌ها

# فاصله‌گذاری
def calculate_score(user_id: int, 
                   score_type: str, 
                   bonus: float = 0.0) -> float:
    """محاسبه امتیاز کاربر.
    
    Args:
        user_id: شناسه کاربر
        score_type: نوع امتیاز
        bonus: امتیاز اضافی
        
    Returns:
        امتیاز کل کاربر
        
    Raises:
        ValueError: اگر نوع امتیاز نامعتبر باشد
    """
    if score_type not in ["daily", "weekly", "monthly"]:
        raise ValueError(f"نوع امتیاز نامعتبر: {score_type}")
    
    # محاسبه امتیاز
    base_score = get_base_score(user_id, score_type)
    total_score = base_score + bonus
    
    return total_score
```

#### Docstring Standards

```python
def process_user_message(message: str, 
                        user_id: int,
                        context: Optional[dict] = None) -> dict:
    """پردازش پیام کاربر و تولید پاسخ.
    
    این تابع پیام کاربر را دریافت کرده، آن را پردازش می‌کند
    و بر اساس context موجود پاسخ مناسب تولید می‌کند.
    
    Args:
        message: متن پیام کاربر
        user_id: شناسه کاربر
        context: اطلاعات اضافی (اختیاری)
        
    Returns:
        دیکشنری حاوی پاسخ و metadata
        
        {
            "response": "پاسخ تولید شده",
            "confidence": 0.95,
            "sources": ["source1", "source2"],
            "processing_time": 0.123
        }
        
    Raises:
        ValueError: اگر پیام خالی باشد
        UserNotFoundError: اگر کاربر یافت نشود
        ProcessingError: اگر خطا در پردازش رخ دهد
        
    Example:
        >>> result = process_user_message("سلام", 123)
        >>> print(result["response"])
        سلام! چطور می‌تونم کمکتون کنم؟
    """
    pass
```

### JavaScript/React (Frontend)

#### Style Guide

```javascript
// استفاده از ES6+ features
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

// نام‌گذاری
const userName = 'John';           // camelCase
const MAX_RETRY_COUNT = 3;         // UPPER_CASE
const UserComponent = () => {};    // PascalCase

// تعریف کامپوننت
const ChatMessage = ({ 
  message, 
  timestamp, 
  isOwn = false,
  onDelete 
}) => {
  // State management
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.content);
  
  // Event handlers
  const handleEdit = useCallback(() => {
    setIsEditing(true);
  }, []);
  
  const handleSave = useCallback(() => {
    // ذخیره تغییرات
    setIsEditing(false);
  }, [editText]);
  
  // Effects
  useEffect(() => {
    if (isEditing) {
      // focus on edit input
    }
  }, [isEditing]);
  
  // Render
  return (
    <div className={`chat-message ${isOwn ? 'own' : 'other'}`}>
      {isEditing ? (
        <input
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          onBlur={handleSave}
          autoFocus
        />
      ) : (
        <div className="message-content">
          {message.content}
          <span className="timestamp">
            {formatTimestamp(timestamp)}
          </span>
        </div>
      )}
      
      {isOwn && (
        <div className="message-actions">
          <button onClick={handleEdit}>ویرایش</button>
          <button onClick={() => onDelete(message.id)}>حذف</button>
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
```

## 🧪 نوشتن تست

### تست Backend (Python)

#### Unit Tests

```python
# tests/test_chat_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.chat_service import ChatService
from app.exceptions import UserNotFoundError, ProcessingError

class TestChatService:
    """تست‌های سرویس چت."""
    
    @pytest.fixture
    def chat_service(self):
        """ایجاد instance سرویس چت برای تست."""
        return ChatService()
    
    @pytest.fixture
    def mock_user(self):
        """ایجاد کاربر mock."""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        user.is_active = True
        return user
    
    def test_process_message_success(self, chat_service, mock_user):
        """تست پردازش موفق پیام."""
        # Arrange
        message = "سلام، چطور هستید؟"
        website_id = 1
        
        with patch.object(chat_service, '_get_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch.object(chat_service, '_process_with_rag') as mock_rag:
                mock_rag.return_value = "سلام! من خوبم، ممنون."
                
                # Act
                result = chat_service.process_message(message, website_id, mock_user.id)
                
                # Assert
                assert result["success"] is True
                assert "سلام! من خوبم، ممنون." in result["response"]
                assert result["processing_time"] > 0
```

### تست Frontend (JavaScript)

#### Component Tests

```javascript
// tests/components/ChatMessage.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatMessage from '../../components/ChatMessage';

describe('ChatMessage Component', () => {
  const mockMessage = {
    id: '1',
    content: 'این یک پیام تست است',
    timestamp: new Date('2024-01-01T12:00:00Z'),
    sender: 'user'
  };
  
  const mockOnDelete = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('نمایش پیام به درستی', () => {
    render(
      <ChatMessage 
        message={mockMessage}
        isOwn={true}
        onDelete={mockOnDelete}
      />
    );
    
    expect(screen.getByText('این یک پیام تست است')).toBeInTheDocument();
    expect(screen.getByText('12:00')).toBeInTheDocument();
  });
  
  test('فراخوانی onDelete هنگام کلیک روی دکمه حذف', () => {
    render(
      <ChatMessage 
        message={mockMessage}
        isOwn={true}
        onDelete={mockOnDelete}
      />
    );
    
    fireEvent.click(screen.getByText('حذف'));
    
    expect(mockOnDelete).toHaveBeenCalledWith('1');
  });
});
```

## 🔄 ارسال Pull Request

### مراحل ارسال PR

1. **Fork کردن پروژه**
2. **ایجاد branch جدید**
3. **انجام تغییرات**
4. **Commit کردن تغییرات**
5. **Push کردن branch**
6. **ایجاد Pull Request**

### قوانین Commit Message

```bash
# فرمت کلی
<type>(<scope>): <description>

# انواع commit
feat: ویژگی جدید
fix: رفع باگ
docs: تغییرات مستندات
style: تغییرات style (کد)
refactor: بازنویسی کد
test: اضافه کردن یا تغییر تست
chore: تغییرات build یا tooling

# مثال‌ها
feat(chat): اضافه کردن قابلیت ویرایش پیام
fix(auth): رفع مشکل JWT expiration
docs(api): به‌روزرسانی مستندات endpoint
```

## 🐛 گزارش باگ

### فرمت گزارش باگ

```markdown
## 🐛 خلاصه باگ
توضیح مختصر از مشکل

## 🔍 مراحل تکرار
1. به صفحه X بروید
2. روی دکمه Y کلیک کنید
3. خطا رخ می‌دهد

## 📱 اطلاعات سیستم
- **سیستم عامل**: Ubuntu 20.04
- **مرورگر**: Chrome 96.0.4664.110
- **نسخه**: 1.0.0

## 📊 رفتار مورد انتظار
توضیح اینکه چه اتفاقی باید می‌افتاد

## ❌ رفتار فعلی
توضیح اینکه چه اتفاقی می‌افتد
```

## ✨ درخواست ویژگی

### فرمت درخواست ویژگی

```markdown
## 🚀 خلاصه ویژگی
توضیح مختصر از ویژگی درخواستی

## 🎯 مشکل حل شده
توضیح اینکه این ویژگی چه مشکلی را حل می‌کند

## 💡 راه‌حل پیشنهادی
توضیح از نحوه پیاده‌سازی

## 📱 نمونه استفاده
```javascript
const newFeature = useNewFeature();
```
```

## ❓ سوالات متداول

### Q: چگونه می‌توانم شروع کنم؟
**A**: ابتدا پروژه را fork کنید، محیط توسعه را راه‌اندازی کنید و یک issue ساده را انتخاب کنید.

### Q: چه نوع تغییراتی پذیرفته می‌شود؟
**A**: تمام تغییرات مفید پذیرفته می‌شوند: رفع باگ، ویژگی جدید، بهبود عملکرد، مستندات.

### Q: چگونه می‌توانم مطمئن شوم که کد من درست است؟
**A**: تست‌ها را اجرا کنید، linting را بررسی کنید و کد خود را review کنید.

## 🤝 ارتباط

### راه‌های ارتباطی

- 📧 **ایمیل**: contributors@example.com
- 💬 **Discord**: [اینجا](https://discord.gg/your-server)
- 🐛 **GitHub Issues**: [اینجا](https://github.com/your-username/ai-chatbot/issues)
- 📖 **مستندات**: [اینجا](https://docs.example.com)

## 🙏 تشکر

از مشارکت شما در بهبود این پروژه تشکر می‌کنیم! هر contribution، حتی کوچک، ارزشمند است.

---

**🎉 به تیم توسعه‌دهندگان بپیوندید!**
