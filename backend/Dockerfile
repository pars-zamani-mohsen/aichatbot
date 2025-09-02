FROM python:3.8-slim

WORKDIR /app

# نصب وابستگی‌های سیستم
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# کپی فایل‌های پروژه
COPY requirements.txt .
COPY app/ app/

# نصب وابستگی‌های پایتون
RUN pip install --no-cache-dir -r requirements.txt

# ایجاد دایرکتوری داده
RUN mkdir -p data

# تنظیم متغیرهای محیطی
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# اجرای برنامه
CMD ["python", "run.py"] 