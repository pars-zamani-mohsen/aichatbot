class PromptManager:
    def __init__(self):
        # پرامپت‌های پایه برای موقعیت‌های مختلف
        self.base_prompts = {
            'general': """شما یک دستیار هوشمند برای پاسخگویی به سوالات هستید.
برای پاسخ به سوالات کاربر، از اطلاعات زیر استفاده کنید.
اگر اطلاعات کافی در منابع نیست، این را صادقانه به کاربر بگویید.
پاسخ‌های خود را به زبان فارسی ارائه دهید و به صورت طبیعی و محاوره‌ای صحبت کنید.""",

            'faq': """به عنوان دستیار پاسخگوی سوالات متداول،
پاسخ را کوتاه و مفید ارائه دهید.
فقط به موضوع اصلی سوال بپردازید.
اطلاعات و منابع داده شده:""",

            'technical': """به عنوان یک دستیار فنی متخصص،
پاسخ‌های دقیق و تخصصی ارائه دهید.
با استناد به منابع موثق پاسخ دهید.
در صورت نیاز به اطلاعات بیشتر، به منابع تکمیلی ارجاع دهید.
اطلاعات و منابع داده شده:"""
        }

    def get_prompt(self, query: str, context: str, prompt_type: str = 'general') -> str:
        """ساخت پرامپت نهایی براساس نوع درخواست"""

        # انتخاب پرامپت پایه
        base_prompt = self.base_prompts.get(prompt_type, self.base_prompts['general'])

        # تشخیص نوع سوال و افزودن دستورالعمل مناسب
        instruction = self._get_instruction(query)

        # ساخت پرامپت نهایی
        return f"{base_prompt}{instruction}\n\nاطلاعات مرتبط:\n{context}\n\nسوال: {query}\nپاسخ:"

    def _get_instruction(self, query: str) -> str:
        """تعیین دستورالعمل براساس نوع سوال"""
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in ['چگونه', 'چطور', 'روش']):
            return "\nلطفاً مراحل را به صورت گام به گام توضیح دهید."
        elif any(keyword in query_lower for keyword in ['تفاوت', 'مقایسه']):
            return "\nلطفاً مقایسه را به صورت نکته به نکته انجام دهید."
        elif any(keyword in query_lower for keyword in ['چرا', 'دلیل']):
            return "\nلطفاً دلایل را با جزئیات کافی توضیح دهید."
        else:
            return "\nلطفاً پاسخ را مختصر و مفید ارائه دهید."

    def detect_query_type(self, query: str) -> str:
        """تشخیص نوع پرامپت مناسب براساس پرسش"""
        query_lower = query.lower()

        # تشخیص سوالات متداول
        if any(keyword in query_lower for keyword in ['متداول', 'رایج', 'معمول', 'سوال']):
            return 'faq'

        # تشخیص سوالات فنی
        elif any(keyword in query_lower for keyword in ['فنی', 'تخصصی', 'مشخصات', 'ویژگی']):
            return 'technical'

        return 'general'