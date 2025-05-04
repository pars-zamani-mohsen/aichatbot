# run_phase1.py - نسخه اصلاح شده  

import os  
import subprocess  
import time  
import shutil  

def run_phase1(start_url, use_selenium=True):  
    """اجرای کامل فاز 1: خزش وب و پردازش داده"""  
    print(f"شروع فاز 1: خزش وب و پردازش داده برای {start_url}")  
    
    # ذخیره مسیر اصلی  
    original_dir = os.getcwd()  
    
    # گام 1: اجرای خزنده Scrapy  
    print("\n=== اجرای خزنده Scrapy ===")  
    scrapy_command = f'cd website_crawler && scrapy crawl website_spider -a start_url="{start_url}"'  
    subprocess.run(scrapy_command, shell=True)  
    
    # کپی فایل output.json از مسیر Scrapy به مسیر اصلی  
    scrapy_output = os.path.join("website_crawler", "output.json")  
    if os.path.exists(scrapy_output):  
        shutil.copy(scrapy_output, "output.json")  
        print(f"فایل output.json از {scrapy_output} به {os.path.join(original_dir, 'output.json')} کپی شد.")  
    else:  
        print(f"هشدار: فایل {scrapy_output} یافت نشد!")  
        # جستجو برای فایل output.json در سایر مسیرها  
        for root, dirs, files in os.walk("."):  
            if "output.json" in files:  
                found_path = os.path.join(root, "output.json")  
                shutil.copy(found_path, "output.json")  
                print(f"فایل output.json از {found_path} به {os.path.join(original_dir, 'output.json')} کپی شد.")  
                break  
    
    # گام 2: اجرای خزنده Selenium (اختیاری)  
    if use_selenium:  
        print("\n=== اجرای خزنده Selenium ===")  
        subprocess.run(f"python selenium_crawler.py {start_url}", shell=True)  
        
        # ادغام داده‌ها  
        selenium_output = "selenium_output.json"  
        if os.path.exists(selenium_output) and os.path.exists("output.json"):  
            print("\n=== ادغام داده‌های خزش شده ===")  
            subprocess.run("python merge_data.py", shell=True)  
            
            # استفاده از داده‌های ادغام شده  
            if os.path.exists("merged_output.json"):  
                shutil.copy("merged_output.json", "output.json")  
    
    # گام 3: پردازش داده‌ها  
    print("\n=== پردازش و تمیزسازی داده‌ها ===")  
    if os.path.exists("output.json"):  
        subprocess.run("python process_data.py", shell=True)  
    else:  
        print("خطا: فایل output.json برای پردازش یافت نشد!")  
    
    # گام 4: تحلیل داده‌ها  
    print("\n=== تحلیل داده‌های پردازش شده ===")  
    subprocess.run("python analyze_data.py", shell=True)  
    
    # گام 5: نهایی کردن پردازش داده‌ها  
    print("\n=== نهایی کردن داده‌های فاز 1 ===")  
    subprocess.run("python finalize_phase1.py", shell=True)  
    
    print("\n=== فاز 1 به پایان رسید ===")  
    print(f"داده‌های پردازش شده در پوشه processed_data ذخیره شدند.")  

if __name__ == "__main__":  
    import sys  
    
    if len(sys.argv) > 1:  
        url = sys.argv[1]  
        # تعیین استفاده از Selenium  
        use_selenium = True  
        if len(sys.argv) > 2 and sys.argv[2].lower() == "false":  
            use_selenium = False  
            
        run_phase1(url, use_selenium)  
    else:  
        print("لطفاً URL سایت مورد نظر را وارد کنید:")  
        print("مثال: python run_phase1.py https://example.com")  
