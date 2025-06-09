import logging
import sys
from pathlib import Path

def setup_logging():
    # ایجاد دایرکتوری لاگ
    log_dir = Path("/var/www/html/ai/backend/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "app.log"

    # تنظیم فرمت لاگ
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # تنظیم روت لاگر
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # پاک کردن هندلرهای قبلی
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # اضافه کردن هندلر فایل
    file_handler = logging.FileHandler(str(log_path), encoding="utf-8", mode="a")
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)

    # اضافه کردن هندلر کنسول
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(console_handler)

    # تنظیم لاگرهای خاص
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO) 