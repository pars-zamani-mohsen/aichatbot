import re
from typing import List, Dict
from langdetect import detect
import logging

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """پاکسازی متن"""
    # حذف کاراکترهای خاص
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    
    # حذف فاصله‌های اضافی
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def detect_language(text: str) -> str:
    """تشخیص زبان متن"""
    try:
        return detect(text)
    except Exception as e:
        logger.error(f"خطا در تشخیص زبان: {str(e)}")
        return "unknown"

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """تقسیم متن به قطعات کوچکتر"""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        if end > text_length:
            end = text_length
            
        chunk = text[start:end]
        chunks.append(chunk)
        
        start = end - chunk_overlap
        
    return chunks

def extract_metadata(url: str, title: str = "", content: str = "") -> Dict:
    """استخراج متادیتا از متن"""
    metadata = {
        "url": url,
        "title": title,
        "language": detect_language(content) if content else "unknown",
        "length": len(content) if content else 0
    }
    
    return metadata 