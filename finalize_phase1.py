# finalize_phase1.py - نسخه اصلاح شده  

import pandas as pd  
import json  
import os  
from datetime import datetime  

def finalize_data_processing(input_csv='processed_data.csv', output_dir='processed_data'):  
    """نهایی کردن پردازش داده‌ها و آماده‌سازی برای فاز بعدی"""  
    
    # بررسی وجود فایل ورودی  
    if not os.path.exists(input_csv):  
        print(f"خطا: فایل {input_csv} وجود ندارد!")  
        print("لطفاً ابتدا process_data.py را اجرا کنید.")  
        # ایجاد یک فایل داده خالی برای ادامه کار  
        empty_df = pd.DataFrame(columns=['url', 'title', 'chunk_id', 'content', 'content_length'])  
        empty_df.to_csv(input_csv, index=False, encoding='utf-8')  
        print(f"یک فایل خالی در {input_csv} ایجاد شد.")  
        df = empty_df  
    else:  
        # خواندن داده‌های پردازش شده  
        df = pd.read_csv(input_csv)  
    
    # اطمینان از وجود پوشه خروجی  
    os.makedirs(output_dir, exist_ok=True)  
    
    # افزودن ستون timestamp  
    now = datetime.now().isoformat()  
    df['processed_timestamp'] = now  
    
    try:  
        # ذخیره داده‌ها در فرمت‌های مختلف  
        
        # CSV - کل داده‌ها  
        df.to_csv(f"{output_dir}/final_processed_data.csv", index=False, encoding='utf-8')  
        
        # JSON - کل داده‌ها  
        df.to_json(f"{output_dir}/final_processed_data.json", orient='records', force_ascii=False, indent=2)  
        
        # اگر داده‌ای وجود ندارد، فرآیند را متوقف کنید  
        if len(df) == 0:  
            print("هشدار: هیچ داده‌ای برای پردازش وجود ندارد!")  
            # ایجاد فایل فهرست خالی  
            index_data = {  
                'total_chunks': 0,  
                'unique_urls': 0,  
                'processed_timestamp': now,  
                'url_files': {}  
            }  
            
            with open(f"{output_dir}/index.json", 'w', encoding='utf-8') as f:  
                json.dump(index_data, f, ensure_ascii=False, indent=2)  
                
            print(f"فایل‌های خالی در پوشه {output_dir} ایجاد شدند.")  
            return df  
        
        # تقسیم داده‌ها بر اساس URL  
        url_groups = df.groupby('url')  
        
        # ایجاد فایل‌های جداگانه برای هر URL  
        url_files = {}  
        for url, group in url_groups:  
            # ایجاد نام فایل بر اساس URL  
            filename = url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_')  
            if len(filename) > 100:  
                filename = filename[:100]  # محدود کردن طول نام فایل  
            
            # ذخیره گروه به عنوان JSON  
            file_path = f"{output_dir}/{filename}.json"  
            group.to_json(file_path, orient='records', force_ascii=False, indent=2)  
            url_files[url] = file_path  
        
        # ایجاد فایل فهرست  
        index_data = {  
            'total_chunks': len(df),  
            'unique_urls': df['url'].nunique(),  
            'processed_timestamp': now,  
            'url_files': url_files  
        }  
        
        with open(f"{output_dir}/index.json", 'w', encoding='utf-8') as f:  
            json.dump(index_data, f, ensure_ascii=False, indent=2)  
        
        print(f"پردازش داده‌ها نهایی شد. فایل‌های خروجی در پوشه {output_dir} ذخیره شدند.")  
        print(f"تعداد کل چانک‌ها: {len(df)}")  
        print(f"تعداد URLهای منحصر به فرد: {df['url'].nunique()}")  
    
    except Exception as e:  
        print(f"خطا در نهایی کردن پردازش داده‌ها: {e}")  
    
    return df  

if __name__ == "__main__":  
    finalize_data_processing()  
