from langdetect import detect
import hashlib
from typing import Dict, Optional

class TextProcessor:
    def __init__(self):
        self.seen_contents = set()

    def process_chunk(self, chunk: Dict) -> Optional[Dict]:
        """پردازش و اعتبارسنجی یک تکه متن"""
        if not chunk or 'content' not in chunk:
            return None

        content = chunk['content']

        # حذف محتوای تکراری
        content_hash = self._get_content_hash(content)
        if content_hash in self.seen_contents:
            return None
        self.seen_contents.add(content_hash)

        # تشخیص زبان
        try:
            lang = detect(content)
            if lang not in ['fa', 'en']:
                return None
            chunk['language'] = lang
        except:
            return None

        # بررسی طول محتوا
        if len(content.strip()) < 100:
            return None

        return chunk

    def _get_content_hash(self, text: str) -> str:
        """ایجاد hash از محتوا"""
        return hashlib.md5(text.encode()).hexdigest()