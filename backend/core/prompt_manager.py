from typing import Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self):
        # تعریف انواع پرسش و الگوهای آن‌ها
        self.query_patterns = {
            'procedural': r'(چگونه|چطور|روش|نحوه)',
            'comparative': r'(تفاوت|مقایسه|فرق|بهتر|بدتر)',
            'reasoning': r'(چرا|دلیل|علت)',
            'faq': r'(متداول|رایج|معمول|سوال)',
            'technical': r'(فنی|تخصصی|مشخصات|ویژگی)',
        }

        # پرامپت‌های پایه
        self.base_prompts = {
            'general': """به عنوان دستیار هوشمند فارسی‌زبان:
- از اطلاعات ارائه شده برای پاسخگویی استفاده کنید
- در صورت نبود اطلاعات کافی، صادقانه اعلام کنید
- به زبان طبیعی و محاوره‌ای پاسخ دهید
- از اطلاعات خارج از متن استفاده نکنید""",

            'faq': """به عنوان دستیار پاسخگوی سوالات متداول:
- پاسخ را کوتاه و مفید ارائه دهید
- فقط به موضوع اصلی سوال بپردازید
- از مثال‌های کاربردی استفاده کنید""",

            'technical': """به عنوان دستیار فنی متخصص:
- پاسخ‌های دقیق و تخصصی ارائه دهید
- با جزئیات کافی توضیح دهید
- در صورت نیاز، مراحل را گام به گام شرح دهید
- به منابع و مستندات استناد کنید"""
        }

        # دستورالعمل‌های خاص برای هر نوع پرسش
        self.instructions = {
            'procedural': "\nلطفاً مراحل را به صورت گام به گام توضیح دهید:",
            'comparative': "\nلطفاً مقایسه را با ذکر نکات کلیدی انجام دهید:",
            'reasoning': "\nلطفاً دلایل را با جزئیات کافی شرح دهید:",
            'general': "\nلطفاً پاسخ را مختصر و مفید ارائه دهید:"
        }

    def detect_query_type(self, query: str) -> str:
        """تشخیص نوع پرسش با استفاده از الگوهای منظم"""
        try:
            query = query.strip().replace('؟', '').lower()

            for q_type, pattern in self.query_patterns.items():
                if re.search(pattern, query):
                    logger.info(f"Query type detected: {q_type}")
                    return q_type

            return 'general'

        except Exception as e:
            logger.error(f"Error in query type detection: {str(e)}")
            return 'general'

    def get_prompt(self, query: str, context: str, prompt_type: Optional[str] = None) -> str:
        """ساخت پرامپت نهایی با ترکیب اجزای مختلف"""
        try:
            # تشخیص نوع پرامپت اگر مشخص نشده باشد
            if not prompt_type:
                prompt_type = 'technical' if 'technical' in self.detect_query_type(query) else 'general'

            # انتخاب پرامپت پایه
            base_prompt = self.base_prompts.get(prompt_type, self.base_prompts['general'])

            # تشخیص نوع سوال برای دستورالعمل
            query_type = self.detect_query_type(query)
            instruction = self.instructions.get(query_type, self.instructions['general'])

            # ساخت پرامپت نهایی
            prompt = f"{base_prompt}\n\nمتن مرجع:\n{context}\n{instruction}\n\nسوال: {query}\nپاسخ:"

            logger.info(f"Generated prompt for type: {prompt_type}, query type: {query_type}")
            return prompt

        except Exception as e:
            logger.error(f"Error in prompt generation: {str(e)}")
            # بازگشت به ساده‌ترین حالت در صورت بروز خطا
            return f"لطفاً با توجه به این اطلاعات:\n{context}\n\nبه این سوال پاسخ دهید:\n{query}"