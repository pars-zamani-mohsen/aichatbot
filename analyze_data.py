# analyze_data.py - نسخه اصلاح شده  

import pandas as pd  
import matplotlib.pyplot as plt  
from collections import Counter  
import re  
import os  

def analyze_dataset(csv_file='processed_data.csv'):  
    """تحلیل داده‌های پردازش شده و نمایش آمار توصیفی"""  
    
    # بررسی وجود فایل  
    if not os.path.exists(csv_file):  
        print(f"خطا: فایل {csv_file} وجود ندارد!")  
        print("لطفاً ابتدا process_data.py را اجرا کنید.")  
        return None  
    
    # خواندن داده‌ها  
    df = pd.read_csv(csv_file)  
    
    # اگر فایل خالی است یا داده‌های کافی ندارد  
    if len(df) == 0:  
        print(f"خطا: فایل {csv_file} خالی است یا داده‌های کافی ندارد!")  
        return None  
    
    # چاپ اطلاعات کلی  
    print(f"تعداد کل چانک‌ها: {len(df)}")  
    print(f"تعداد URLهای منحصر به فرد: {df['url'].nunique()}")  
    
    try:  
        # تحلیل طول محتوا  
        plt.figure(figsize=(10, 6))  
        plt.hist(df['content_length'], bins=30)  
        plt.title('توزیع طول محتوا')  
        plt.xlabel('طول محتوا (تعداد کاراکترها)')  
        plt.ylabel('تعداد چانک‌ها')  
        plt.savefig('content_length_distribution.png')  
        
        # تحلیل کلمات پرتکرار  
        all_text = ' '.join(df['content'].tolist())  
        words = re.findall(r'\b\w+\b', all_text.lower())  
        word_counts = Counter(words)  
        
        # حذف کلمات عمومی و بسیار کوتاه  
        filtered_word_counts = {word: count for word, count in word_counts.items()   
                                if len(word) > 3 and count > 5}  
        
        top_words = dict(sorted(filtered_word_counts.items(), key=lambda x: x[1], reverse=True)[:20])  
        
        plt.figure(figsize=(12, 6))  
        plt.bar(top_words.keys(), top_words.values())  
        plt.title('20 کلمه پرتکرار')  
        plt.xticks(rotation=45, ha='right')  
        plt.tight_layout()  
        plt.savefig('top_words.png')  
        
        # ذخیره نمونه‌هایی از چانک‌ها  
        sample_chunks = df.sample(min(10, len(df)))  
        sample_chunks.to_csv('sample_chunks.csv', index=False)  
        
        print("تحلیل داده‌ها انجام شد. نمودارها و نمونه‌ها ذخیره شدند.")  
    
    except Exception as e:  
        print(f"خطا در تحلیل داده‌ها: {e}")  
    
    return df  

if __name__ == "__main__":  
    analyze_dataset()  
