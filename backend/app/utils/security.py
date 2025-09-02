import re
import html
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def sanitize_html(text: str) -> str:
    """پاکسازی HTML tags"""
    # حذف HTML tags
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    # Escape HTML entities
    return html.escape(text)

def validate_email(email: str) -> bool:
    """تأیید فرمت ایمیل"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    """تأیید فرمت URL"""
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))

def validate_filename(filename: str) -> bool:
    """تأیید نام فایل"""
    # حذف کاراکترهای خطرناک
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    return not any(char in filename for char in dangerous_chars)

def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """تأیید پسوند فایل"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions

def validate_input_length(text: str, max_length: int = 1000) -> bool:
    """تأیید طول ورودی"""
    return len(text.strip()) <= max_length

def sanitize_sql_input(text: str) -> str:
    """پاکسازی ورودی برای جلوگیری از SQL injection"""
    # حذف کاراکترهای خطرناک SQL
    dangerous_patterns = [
        r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)',
        r'(\b(script|javascript|vbscript|expression)\b)',
        r'(\b(onload|onerror|onclick|onmouseover)\b)',
        r'(\b(alert|confirm|prompt)\b)',
        r'(\b(document|window|location)\b)',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()
