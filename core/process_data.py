import json
import pandas as pd
import re
import os
from nltk.tokenize import sent_tokenize
import nltk
import logging

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# دانلود پکیج‌های مورد نیاز NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def clean_text(text):
    """پاکسازی متن از کاراکترهای اضافی"""
    if not isinstance(text, str):
        return ""

    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,?!:;-]', '', text)
    return text.strip()

def process_json_data(json_file):
    """
    پردازش داده‌های JSON و تبدیل به فرمت مناسب
    
    Args:
        json_file (str): مسیر فایل JSON ورودی
    
    Returns:
        list: لیست داده‌های پردازش شده
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        processed_data = []
        for item in data:
            processed_item = {
                'url': item.get('url', ''),
                'title': clean_text(item.get('title', '')),
                'content': clean_text(item.get('content', '')),
                'timestamp': item.get('timestamp', '')
            }
            if processed_item['content']:  # فقط آیتم‌های دارای محتوا را اضافه کن
                processed_data.append(processed_item)

        return processed_data
    except json.JSONDecodeError as e:
        logger.error(f"خطا در خواندن JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"خطا در پردازش داده‌ها: {e}")
        return []

def save_to_csv(data, output_file):
    """
    ذخیره داده‌های پردازش شده در فایل CSV
    
    Args:
        data (list): لیست داده‌های پردازش شده
        output_file (str): مسیر فایل CSV خروجی
    
    Returns:
        bool: True در صورت موفقیت، False در صورت خطا
    """
    try:
        # اطمینان از وجود دایرکتوری
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"داده‌ها با موفقیت در {output_file} ذخیره شدند")
        return True
    except Exception as e:
        logger.error(f"خطا در ذخیره‌سازی CSV: {e}")
        return False

def process_website_data(json_file, output_dir='processed_data'):
    """
    پردازش داده‌های سایت و ذخیره در فایل CSV
    
    Args:
        json_file (str): مسیر فایل JSON ورودی
        output_dir (str): دایرکتوری خروجی
    
    Returns:
        bool: True در صورت موفقیت، False در صورت خطا
    """
    try:
        # پردازش داده‌ها
        data = process_json_data(json_file)
        if not data:
            logger.error("هیچ داده‌ای برای پردازش یافت نشد")
            return False

        # ذخیره در CSV
        output_file = os.path.join(output_dir, 'processed_data.csv')
        if save_to_csv(data, output_file):
            logger.info(f"پردازش داده‌ها با موفقیت انجام شد. تعداد رکوردها: {len(data)}")
            return True
        return False

    except Exception as e:
        logger.error(f"خطا در پردازش داده‌های سایت: {e}")
        return False

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'output.json'
    process_website_data(input_file)