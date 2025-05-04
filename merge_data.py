# merge_data.py  

import pandas as pd  
import json  

def merge_crawled_data(scrapy_output='output.json', selenium_output='selenium_output.json', output_file='merged_output.json'):  
    """ادغام داده‌های خزش شده از منابع مختلف"""  
    # خواندن داده‌های Scrapy  
    with open(scrapy_output, 'r', encoding='utf-8') as f:  
        scrapy_data = json.load(f)  
    
    # خواندن داده‌های Selenium  
    with open(selenium_output, 'r', encoding='utf-8') as f:  
        selenium_data = json.load(f)  
    
    # ایجاد دیکشنری برای ردیابی URL‌های منحصر به فرد  
    url_to_data = {}  
    
    # ادغام داده‌ها  
    for item in scrapy_data:  
        url = item.get('url')  
        url_to_data[url] = item  
    
    for item in selenium_data:  
        url = item.get('url')  
        if url in url_to_data:  
            # ادغام محتوا با اولویت دادن به محتوای طولانی‌تر  
            if len(item.get('content', '')) > len(url_to_data[url].get('content', '')):  
                url_to_data[url]['content'] = item.get('content', '')  
            
            # اگر عنوان وجود ندارد، از عنوان Selenium استفاده کنید  
            if not url_to_data[url].get('title') and item.get('title'):  
                url_to_data[url]['title'] = item.get('title')  
        else:  
            url_to_data[url] = item  
    
    # تبدیل دیکشنری به لیست  
    merged_data = list(url_to_data.values())  
    
    # ذخیره داده‌های ادغام شده  
    with open(output_file, 'w', encoding='utf-8') as f:  
        json.dump(merged_data, f, ensure_ascii=False, indent=2)  
    
    print(f"ادغام داده‌ها انجام شد. {len(merged_data)} صفحه منحصر به فرد در {output_file} ذخیره شد.")  
    
    return merged_data  

if __name__ == "__main__":  
    # اگر هر دو فایل خروجی وجود داشته باشند، آنها را ادغام کنید  
    import os  
    if os.path.exists('output.json') and os.path.exists('selenium_output.json'):  
        merge_crawled_data()  
    else:  
        print("یک یا هر دو فایل خروجی وجود ندارند.")  
