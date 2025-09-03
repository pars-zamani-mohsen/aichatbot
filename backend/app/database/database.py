from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

# ایجاد موتور دیتابیس با تنظیمات connection pool بهینه
engine = create_engine(
    settings.DATABASE_URL,
    # Connection Pool Settings
    pool_size=20,  # تعداد اتصالات در pool
    max_overflow=30,  # حداکثر اتصالات اضافی
    pool_timeout=30,  # timeout برای دریافت اتصال (ثانیه)
    pool_recycle=1800,  # بازیافت اتصالات بعد از 30 دقیقه
    pool_pre_ping=True,  # بررسی سلامت اتصال قبل از استفاده
    
    # Performance Settings
    echo=False,  # نمایش SQL queries در console
    echo_pool=False,  # نمایش اطلاعات pool
    
    # Connection Settings
    connect_args={
        "connect_timeout": 10,  # timeout برای اتصال اولیه
        "application_name": "ai_chatbot"  # نام اپلیکیشن
    },
    
    # Query Optimization
    execution_options={
        "compiled_cache": None,  # استفاده از cache برای compiled queries
        "autocommit": False
    }
)

# ایجاد جلسه sync
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ایجاد کلاس پایه برای مدل‌ها
Base = declarative_base()

# تابع برای دریافت جلسه دیتابیس sync
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Async Database Engine (اگر DATABASE_URL async باشد)
async_engine = None
AsyncSessionLocal = None

if settings.DATABASE_URL.startswith("postgresql+asyncpg://"):
    async_engine = create_async_engine(
        settings.DATABASE_URL,
        # Connection Pool Settings
        pool_size=20,
        max_overflow=30,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        
        # Performance Settings
        echo=False,
        echo_pool=False,
        
        # Connection Settings
        connect_args={
            "connect_timeout": 10,
            "application_name": "ai_chatbot_async"
        }
    )
    
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

# تابع برای دریافت جلسه دیتابیس async
async def get_async_db():
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database not configured")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# تابع برای بستن async engine
async def close_async_engine():
    if async_engine:
        await async_engine.dispose() 