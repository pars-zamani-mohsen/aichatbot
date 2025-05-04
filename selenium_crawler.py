# selenium_crawler.py  

from selenium import webdriver  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.chrome.service import Service  
from webdriver_manager.chrome import ChromeDriverManager  
from selenium.webdriver.common.by import By  
from bs4 import BeautifulSoup  
import time  
import json  
import os  
from urllib.parse import urlparse, urljoin  

def setup_driver():  
    """راه‌اندازی درایور Selenium"""  
    chrome_options = Options()  
    chrome_options.add_argument("--headless")  # اجرا بدون نمایش مرورگر  
    chrome_options.add_argument("--disable-gpu")  
    chrome_options.add_argument("--no-sandbox")  
    chrome_options.add_argument("--disable-dev-shm-usage")  
    
    service = Service(ChromeDriverManager().install())  
    driver = webdriver.Chrome(service=service, options=chrome_options)  
    
    return driver  

def is_valid_url(url, base_domain):  
    """بررسی معتبر بودن URL برای خزش"""  
    try:  
        parsed = urlparse(url)  
        # بررسی اینکه URL داخلی است  
        return parsed.netloc == base_domain or parsed.netloc == ''  
    except:  
        return False  

def crawl_with_selenium(start_url, output_file='selenium_output.json', max_pages=50):  
    """خزش سایت با استفاده از Selenium"""  
    driver = setup_driver()  
    
    # استخراج دامنه اصلی  
    parsed_url = urlparse(start_url)  
    base_domain = parsed_url.netloc  
    
    visited_urls = set()  
    to_visit = [start_url]  
    results = []  
    
    while to_visit and len(visited_urls) < max_pages:  
        url = to_visit.pop(0)  
        
        if url in visited_urls:  
            continue  
            
        print(f"در حال بازدید از: {url}")  
        
        try:  
            # بازکردن صفحه  
            driver.get(url)  
            
            # منتظر بمانید تا محتوا به طور کامل بارگذاری شود  
            time.sleep(3)  # انتظار برای اجرای جاوااسکریپت  
            
            # افزودن URL به لیست بازدید شده‌ها  
            visited_urls.add(url)  
            
            # استخراج محتوا  
            title = driver.title  
            page_source = driver.page_source  
            
            # استفاده از BeautifulSoup برای پردازش HTML  
            soup = BeautifulSoup(page_source, 'html.parser')  
            
            # استخراج متن صفحه  
            body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""  
            
            # ذخیره داده‌های صفحه  
            results.append({  
                'url': url,  
                'title': title,  
                'content': body_text  
            })  
            
            # یافتن لینک‌های جدید  
            links = driver.find_elements(By.TAG_NAME, 'a')  
            for link in links:  
                try:  
                    href = link.get_attribute('href')  
                    if href and not href.startswith('javascript:') and not href.startswith('#'):  
                        absolute_url = urljoin(url, href)  
                        if is_valid_url(absolute_url, base_domain) and absolute_url not in visited_urls and absolute_url not in to_visit:  
                            to_visit.append(absolute_url)  
                except Exception as e:  
                    print(f"خطا در پردازش لینک: {e}")  
        
        except Exception as e:  
            print(f"خطا در بازدید از {url}: {e}")  
    
    # بستن درایور  
    driver.quit()  
    
    # ذخیره نتایج  
    with open(output_file, 'w', encoding='utf-8') as f:  
        json.dump(results, f, ensure_ascii=False, indent=2)  
    
    print(f"خزش کامل شد. {len(results)} صفحه در {output_file} ذخیره شد.")  
    return results  

if __name__ == "__main__":  
    # URL سایت مورد نظر خود را وارد کنید  
    crawl_with_selenium("https://yourdomain.com")  
