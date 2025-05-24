import re
import logging
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self):
        # الگوهای تشخیص نوع پرسش
        self.query_patterns = {
            'procedural': [
                r'چطور|چگونه|راهنمایی|مراحل|قدم|گام|نحوه|روش',
                r'how to|steps|guide|tutorial|process'
            ],
            'comparative': [
                r'مقایسه|تفاوت|شباهت|بهتر|بدتر|قوی‌تر|ضعیف‌تر',
                r'compare|difference|similarity|better|worse|stronger|weaker'
            ],
            'reasoning': [
                r'چرا|دلیل|علت|چرایی|توضیح|تحلیل',
                r'why|reason|cause|explanation|analysis'
            ],
            'faq': [
                r'سوال|پرسش|پرسش‌های متداول|سوالات متداول',
                r'question|faq|frequently asked'
            ],
            'technical': [
                r'خطا|مشکل|ایراد|باک|باگ|کرش|کرش کردن',
                r'error|bug|crash|issue|problem|technical'
            ]
        }
        
        # پرامپت‌های پایه برای هر نوع پرسش
        self.base_prompts = {
            'procedural': """
            شما یک دستیار متخصص هستید که باید مراحل انجام یک کار را به صورت گام به گام توضیح دهید.
            لطفاً مراحل را به ترتیب و با جزئیات کافی توضیح دهید.
            از مثال‌های عملی استفاده کنید و نکات مهم را برجسته کنید.
            """,
            
            'comparative': """
            شما یک تحلیلگر متخصص هستید که باید مقایسه دقیقی بین موارد مختلف ارائه دهید.
            لطفاً نقاط قوت و ضعف هر مورد را بررسی کنید و نتیجه‌گیری منصفانه‌ای ارائه دهید.
            از داده‌های واقعی و مثال‌های عملی استفاده کنید.
            """,
            
            'reasoning': """
            شما یک تحلیلگر منطقی هستید که باید دلایل و علل پدیده‌ها را بررسی کنید.
            لطفاً تحلیل عمیقی ارائه دهید و ارتباطات علت و معلولی را توضیح دهید.
            از منابع معتبر و شواهد علمی استفاده کنید.
            """,
            
            'faq': """
            شما یک متخصص پشتیبانی هستید که باید به سوالات متداول پاسخ دهید.
            لطفاً پاسخ‌های دقیق و کاربردی ارائه دهید.
            از زبان ساده و قابل فهم استفاده کنید و مثال‌های عملی بیاورید.
            """,
            
            'technical': """
            شما یک متخصص فنی هستید که باید مشکلات تکنیکی را برطرف کنید.
            لطفاً راه‌حل‌های دقیق و عملی ارائه دهید.
            مراحل عیب‌یابی و رفع مشکل را به ترتیب توضیح دهید.
            """
        }
        
        # دستورالعمل‌های اضافی برای هر نوع پرسش
        self.instructions = {
            'procedural': [
                "هر مرحله را با شماره مشخص کنید",
                "نکات مهم را برجسته کنید",
                "از مثال‌های عملی استفاده کنید"
            ],
            'comparative': [
                "جدول مقایسه تهیه کنید",
                "نقاط قوت و ضعف را لیست کنید",
                "نتیجه‌گیری نهایی ارائه دهید"
            ],
            'reasoning': [
                "دلایل اصلی را لیست کنید",
                "ارتباطات علت و معلولی را توضیح دهید",
                "از منابع معتبر استفاده کنید"
            ],
            'faq': [
                "پاسخ را کوتاه و مختصر ارائه دهید",
                "از زبان ساده استفاده کنید",
                "مثال‌های عملی بیاورید"
            ],
            'technical': [
                "مراحل عیب‌یابی را به ترتیب توضیح دهید",
                "کدهای خطا را بررسی کنید",
                "راه‌حل‌های جایگزین ارائه دهید"
            ]
        }
        
    def detect_query_type(self, question: str) -> str:
        """تشخیص نوع پرسش"""
        question = question.lower()
        
        # بررسی هر الگو
        for query_type, patterns in self.query_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    logger.info(f"Query type detected: {query_type}")
                    return query_type
                    
        # اگر نوع خاصی تشخیص داده نشد
        return 'general'
        
    def generate_prompt(self, question: str, context: Optional[List[str]] = None) -> str:
        """تولید پرامپت مناسب"""
        # تشخیص نوع پرسش
        query_type = self.detect_query_type(question)
        
        # دریافت پرامپت پایه
        base_prompt = self.base_prompts.get(query_type, self.base_prompts['general'])
        
        # اضافه کردن دستورالعمل‌ها
        instructions = self.instructions.get(query_type, [])
        instructions_text = "\n".join([f"- {instruction}" for instruction in instructions])
        
        # اضافه کردن کانتکست
        context_text = ""
        if context:
            context_text = "\n\nاطلاعات مرتبط:\n" + "\n".join(context)
            
        # ساخت پرامپت نهایی
        prompt = f"""
        {base_prompt}
        
        دستورالعمل‌ها:
        {instructions_text}
        
        {context_text}
        
        پرسش: {question}
        
        لطفاً پاسخ خود را به فارسی ارائه دهید.
        """
        
        return prompt.strip()
        
    def get_system_prompt(self) -> str:
        """دریافت پرامپت سیستم"""
        return """
        شما یک دستیار هوشمند هستید که باید به سوالات کاربران پاسخ دهید.
        پاسخ‌های شما باید:
        1. دقیق و علمی باشند
        2. به زبان فارسی و قابل فهم باشند
        3. از مثال‌های عملی استفاده کنند
        4. منابع معتبر را ذکر کنند
        5. در صورت نیاز، مراحل را به ترتیب توضیح دهند
        
        اگر پاسخ دقیقی نمی‌دانید، صادقانه بگویید که نمی‌دانید.
        """ 