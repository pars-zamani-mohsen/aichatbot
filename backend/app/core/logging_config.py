import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    # ایجاد پوشه logs اگر وجود ندارد
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # تنظیم فرمت لاگ
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # تنظیم handler برای فایل
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # تنظیم handler برای کنسول
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # تنظیم لاگر اصلی
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def get_logger(name):
    """
    دریافت یک لاگر با نام مشخص
    """
    return logging.getLogger(name)

# تنظیم لاگرهای خاص
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("fastapi").setLevel(logging.INFO) 