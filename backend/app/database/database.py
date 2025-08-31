from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# ایجاد موتور دیتابیس با تنظیمات connection pool
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,  # تعداد اتصالات در pool
    max_overflow=20,  # حداکثر اتصالات اضافی
    pool_timeout=30,  # timeout برای دریافت اتصال
    pool_recycle=3600,  # بازیافت اتصالات بعد از 1 ساعت
    pool_pre_ping=True  # بررسی سلامت اتصال قبل از استفاده
)

# ایجاد جلسه
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ایجاد کلاس پایه برای مدل‌ها
Base = declarative_base()

# تابع برای دریافت جلسه دیتابیس
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 