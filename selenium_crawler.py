from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')

    try:
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"خطا در راه‌اندازی Chrome: {e}")
        return None

def crawl_with_selenium(url):
    driver = setup_driver()
    if not driver:
        print("خطا: نمی‌توان ChromeDriver را راه‌اندازی کرد")
        return []

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # اینجا منطق خزش خود را اضافه کنید

        return True
    except Exception as e:
        print(f"خطا در خزش: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    crawl_with_selenium(url)