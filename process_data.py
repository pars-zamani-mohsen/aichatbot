import json
import pandas as pd
import re
from settings import DB_DIRECTORY
from nltk.tokenize import sent_tokenize
import nltk
nltk.download('punkt')

def clean_text(text):
    if not isinstance(text, str):
        return ""

    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,?!:;-]', '', text)
    return text.strip()

def process_json_data(json_file):
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
        print(f"خطا در خواندن JSON: {e}")
        return []
    except Exception as e:
        print(f"خطا در پردازش داده‌ها: {e}")
        return []

def save_to_csv(data, output_file='processed_data.csv'):
    try:
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"داده‌ها با موفقیت در {output_file} ذخیره شدند")
    except Exception as e:
        print(f"خطا در ذخیره‌سازی CSV: {e}")
        # ایجاد فایل خالی
        pd.DataFrame(columns=['url', 'title', 'content', 'timestamp']).to_csv(output_file, index=False)

def main(input_file='output.json', output_file=f'{DB_DIRECTORY}/processed_data.csv'):
    data = process_json_data(input_file)
    if data:
        save_to_csv(data, output_file)
    else:
        print("هیچ داده‌ای برای پردازش یافت نشد")

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'output.json'
    main(input_file)