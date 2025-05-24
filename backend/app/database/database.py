from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# ایجاد موتور دیتابیس
engine = create_engine(settings.DATABASE_URL)

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