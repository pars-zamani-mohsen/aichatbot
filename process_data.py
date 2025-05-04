# process_data.py - نسخه اصلاح شده  

import json  
import re  
import pandas as pd  
import nltk  
from nltk.tokenize import sent_tokenize  
from bs4 import BeautifulSoup  

# دانلود منابع مورد نیاز NLTK  
nltk.download('punkt')  

def clean_text(text):  
    """تمیزسازی متن از تگ‌های HTML و سایر المان‌های اضافی"""  
    # حذف تگ‌های HTML باقی‌مانده  
    soup = BeautifulSoup(text, "html.parser")  
    text = soup.get_text()  
    
    # حذف کاراکترهای خاص و فرمت‌بندی  
    text = re.sub(r'\s+', ' ', text)  # فضاهای خالی چندگانه را به یک فضا تبدیل می‌کند  
    text = re.sub(r'[^\w\s.,?!:;-]', '', text)  # حذف کاراکترهای خاص به جز علامت‌های نقطه‌گذاری  
    
    return text.strip()  

def chunk_text(text, max_chunk_size=1000, overlap=100):  
    """تقسیم متن به بخش‌های کوچکتر با اندازه مشخص و حفظ همپوشانی"""  
    # اگر متن خالی است یا خیلی کوتاه است، آن را به عنوان یک چانک برگردانید  
    if not text or len(text) <= max_chunk_size:  
        return [text]  
    
    # تلاش برای استفاده از sent_tokenize استاندارد   
    # بدون وابستگی به punkt_tab که ممکن است در دسترس نباشد  
    try:  
        sentences = sent_tokenize(text)  
    except LookupError:  
        # اگر sent_tokenize با خطا مواجه شد، از روش ساده‌تر استفاده کنیم  
        # تقسیم بر اساس نقطه، علامت سوال و علامت تعجب  
        sentences = re.split(r'(?<=[.!?])\s+', text)  
    
    chunks = []  
    current_chunk = ""  
    
    for sentence in sentences:  
        # اگر افزودن جمله جدید باعث می‌شود اندازه چانک بیش از حد مجاز شود  
        if len(current_chunk) + len(sentence) > max_chunk_size:  
            # چانک فعلی را به لیست اضافه کنید  
            if current_chunk:  
                chunks.append(current_chunk.strip())  
            
            # از انتهای چانک قبلی، مقداری همپوشانی برای چانک جدید ایجاد کنید  
            words = current_chunk.split()  
            if len(words) > overlap/5:  # تقریباً تعداد کلمات در همپوشانی  
                overlap_text = ' '.join(words[-int(overlap/5):])  
                current_chunk = overlap_text + ' ' + sentence  
            else:  
                current_chunk = sentence  
        else:  
            # افزودن جمله به چانک فعلی  
            current_chunk += ' ' + sentence if current_chunk else sentence  
    
    # اضافه کردن آخرین چانک  
    if current_chunk:  
        chunks.append(current_chunk.strip())  
    
    return chunks  

def process_crawled_data(input_file='output.json', output_file='processed_data.csv'):  
    """پردازش داده‌های خزیده شده و ذخیره آن‌ها در یک فایل CSV"""  
    # خواندن داده‌های خام  
    try:  
        with open(input_file, 'r', encoding='utf-8') as f:  
            data = json.load(f)  
        
        processed_data = []  
        
        for item in data:  
            url = item.get('url', '')  
            title = item.get('title', '')  
            content = item.get('content', '')  
            
            # تمیزسازی محتوا  
            cleaned_content = clean_text(content)  
            
            # اگر محتوای کافی داریم، چانک‌بندی را انجام دهید  
            if len(cleaned_content) > 200:  # حداقل 200 کاراکتر  
                chunks = chunk_text(cleaned_content)  
                
                # افزودن هر چانک به داده‌های پردازش شده  
                for i, chunk in enumerate(chunks):  
                    processed_data.append({  
                        'url': url,  
                        'title': title,  
                        'chunk_id': f"{url}_{i}",  
                        'content': chunk,  
                        'content_length': len(chunk)  
                    })  
            else:  
                # اگر محتوای کمی داریم، آن را به عنوان یک چانک کامل اضافه کنید  
                processed_data.append({  
                    'url': url,  
                    'title': title,  
                    'chunk_id': url,  
                    'content': cleaned_content,  
                    'content_length': len(cleaned_content)  
                })  
        
        # تبدیل به DataFrame  
        df = pd.DataFrame(processed_data)  
        
        # حذف چانک‌های خالی یا بی‌معنی  
        df = df[df['content_length'] > 50]  # حداقل 50 کاراکتر  
        
        # حذف محتوای تکراری  
        df = df.drop_duplicates(subset=['content'])  
        
        # ذخیره نتایج  
        df.to_csv(output_file, index=False, encoding='utf-8')  
        
        print(f"پردازش داده‌ها انجام شد. {len(df)} چانک متنی در {output_file} ذخیره شد.")  
        
        return df  
    
    except Exception as e:  
        print(f"خطا در پردازش داده‌ها: {e}")  
        # ایجاد یک DataFrame خالی برای جلوگیری از خطاهای بعدی  
        empty_df = pd.DataFrame(columns=['url', 'title', 'chunk_id', 'content', 'content_length'])  
        empty_df.to_csv(output_file, index=False, encoding='utf-8')  
        print(f"یک فایل خالی در {output_file} ایجاد شد.")  
        return empty_df  

if __name__ == "__main__":  
    import sys  
    
    if len(sys.argv) > 1:  
        input_file = sys.argv[1]  
        process_crawled_data(input_file=input_file)  
    else:  
        process_crawled_data()  
