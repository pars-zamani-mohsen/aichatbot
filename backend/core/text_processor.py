class TextProcessor:
    def convert_to_english(self, text: str) -> str:
        """تبدیل اعداد فارسی به انگلیسی"""
        persian_digits = {
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
        }
        for persian, english in persian_digits.items():
            text = text.replace(persian, english)
        return text

    def normalize_text(self, text: str) -> str:
        """نرمال‌سازی متن فارسی"""
        # حذف فاصله‌های اضافی
        text = ' '.join(text.split())
        # تبدیل اعداد فارسی به انگلیسی
        text = self.convert_to_english(text)
        return text 