from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..database.database import get_db
from ..database import models
from . import schemas
from ..config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# تنظیمات رمزنگاری - پشتیبانی از bcrypt و Argon2
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def migrate_password_hash(user: models.User, plain_password: str) -> bool:
    """تبدیل hash قدیمی به Argon2"""
    try:
        # بررسی اینکه آیا hash فعلی bcrypt است
        if user.hashed_password.startswith('$2b$') or user.hashed_password.startswith('$2a$'):
            # اگر bcrypt است، آن را به Argon2 تبدیل کن
            new_hash = pwd_context.hash(plain_password)
            user.hashed_password = new_hash
            return True
        return False
    except Exception:
        return False

def send_verification_email(email: str, token: str):
    """ارسال ایمیل تأیید"""
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = "تأیید حساب کاربری"
        
        body = f"""
        سلام!
        
        برای تأیید حساب کاربری خود، روی لینک زیر کلیک کنید:
        {settings.FRONTEND_URL}/verify-email?token={token}
        
        این لینک تا 24 ساعت معتبر است.
        
        اگر شما این درخواست را نکرده‌اید، این ایمیل را نادیده بگیرید.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"خطا در ارسال ایمیل: {str(e)}")
        return False

def send_reset_password_email(email: str, token: str):
    """ارسال ایمیل بازیابی رمز عبور"""
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = "بازیابی رمز عبور"
        
        body = f"""
        سلام!
        
        برای بازیابی رمز عبور خود، روی لینک زیر کلیک کنید:
        {settings.FRONTEND_URL}/reset-password?token={token}
        
        این لینک تا 1 ساعت معتبر است.
        
        اگر شما این درخواست را نکرده‌اید، این ایمیل را نادیده بگیرید.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"خطا در ارسال ایمیل: {str(e)}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # 7 روز
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="اعتبارنامه‌های نامعتبر",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ایمیل قبلاً ثبت شده است"
        )
    
    # ایجاد توکن تأیید
    verification_token = secrets.token_urlsafe(32)
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password,
        verification_token=verification_token,
        is_active=False,  # نیاز به تأیید
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # ارسال ایمیل تأیید
    if hasattr(settings, 'SMTP_SERVER') and settings.SMTP_SERVER:
        send_verification_email(user.email, verification_token)
    
    return db_user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ایمیل یا رمز عبور اشتباه است",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # بررسی رمز عبور و migration در صورت نیاز
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ایمیل یا رمز عبور اشتباه است",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # migration hash قدیمی به Argon2
    if migrate_password_hash(user, form_data.password):
        db.commit()
    
    # به‌روزرسانی last_login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # بررسی فعال بودن حساب
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="حساب کاربری شما فعال نیست. لطفاً ایمیل خود را تأیید کنید."
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified
        }
    }

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.get("/settings")
async def get_user_settings(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """دریافت تنظیمات کاربر"""
    try:
        # دریافت تنظیمات از دیتابیس
        user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
        
        if not user_settings:
            # اگر تنظیمات وجود ندارد، تنظیمات پیش‌فرض ایجاد کن
            user_settings = models.UserSettings(
                user_id=current_user.id,
                first_name=current_user.email.split('@')[0],
                last_name="",
                phone="",
                two_factor_enabled=False,
                email_notifications=True,
                push_notifications=True,
                sms_notifications=False,
                notify_on_new_conversation=True,
                notify_on_website_update=True,
                language="fa",
                theme="light",
                timezone="Asia/Tehran",
                default_k=5,
                max_response_length=500,
                default_temperature=7,
                default_language="fa"
            )
            db.add(user_settings)
            db.commit()
            db.refresh(user_settings)
        
        return {
            "personal": {
                "firstName": user_settings.first_name or "",
                "lastName": user_settings.last_name or "",
                "email": current_user.email,
                "phone": user_settings.phone or ""
            },
            "security": {
                "twoFactorEnabled": user_settings.two_factor_enabled
            },
            "notifications": {
                "emailNotifications": user_settings.email_notifications,
                "pushNotifications": user_settings.push_notifications,
                "smsNotifications": user_settings.sms_notifications,
                "notifyOnNewConversation": user_settings.notify_on_new_conversation,
                "notifyOnWebsiteUpdate": user_settings.notify_on_website_update
            },
            "appearance": {
                "language": user_settings.language,
                "theme": user_settings.theme,
                "timezone": user_settings.timezone
            },
            "rag": {
                "defaultK": user_settings.default_k,
                "maxResponseLength": user_settings.max_response_length,
                "defaultTemperature": user_settings.default_temperature / 10.0,  # تبدیل به float
                "defaultLanguage": user_settings.default_language
            }
        }
    except Exception as e:
        logger.error(f"خطا در دریافت تنظیمات کاربر: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/settings")
async def update_user_settings(
    settings: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """به‌روزرسانی تنظیمات کاربر"""
    try:
        # دریافت تنظیمات موجود یا ایجاد جدید
        user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
        
        if not user_settings:
            user_settings = models.UserSettings(user_id=current_user.id)
            db.add(user_settings)
        
        # به‌روزرسانی اطلاعات شخصی
        if "personal" in settings:
            personal = settings["personal"]
            user_settings.first_name = personal.get("firstName", "")
            user_settings.last_name = personal.get("lastName", "")
            user_settings.phone = personal.get("phone", "")
        
        # به‌روزرسانی تنظیمات امنیت
        if "security" in settings:
            security = settings["security"]
            user_settings.two_factor_enabled = security.get("twoFactorEnabled", False)
        
        # به‌روزرسانی تنظیمات اعلان‌ها
        if "notifications" in settings:
            notifications = settings["notifications"]
            user_settings.email_notifications = notifications.get("emailNotifications", True)
            user_settings.push_notifications = notifications.get("pushNotifications", True)
            user_settings.sms_notifications = notifications.get("smsNotifications", False)
            user_settings.notify_on_new_conversation = notifications.get("notifyOnNewConversation", True)
            user_settings.notify_on_website_update = notifications.get("notifyOnWebsiteUpdate", True)
        
        # به‌روزرسانی تنظیمات ظاهری
        if "appearance" in settings:
            appearance = settings["appearance"]
            user_settings.language = appearance.get("language", "fa")
            user_settings.theme = appearance.get("theme", "light")
            user_settings.timezone = appearance.get("timezone", "Asia/Tehran")
        
        # به‌روزرسانی تنظیمات RAG
        if "rag" in settings:
            rag = settings["rag"]
            user_settings.default_k = rag.get("defaultK", 5)
            user_settings.max_response_length = rag.get("maxResponseLength", 500)
            user_settings.default_temperature = int(rag.get("defaultTemperature", 0.7) * 10)  # تبدیل به integer
            user_settings.default_language = rag.get("defaultLanguage", "fa")
        
        db.commit()
        db.refresh(user_settings)
        
        logger.info(f"User {current_user.id} updated settings successfully")
        
        return {
            "message": "تنظیمات با موفقیت به‌روزرسانی شد",
            "settings": settings
        }
    except Exception as e:
        logger.error(f"خطا در به‌روزرسانی تنظیمات کاربر: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/change-password")
async def change_password(
    password_data: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """تغییر رمز عبور کاربر"""
    try:
        current_password = password_data.currentPassword
        new_password = password_data.newPassword
        confirm_password = password_data.confirmPassword
        
        # بررسی رمز عبور فعلی
        if not verify_password(current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="رمز عبور فعلی اشتباه است")
        
        # بررسی تطبیق رمز عبور جدید
        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="رمز عبور جدید و تأیید آن مطابقت ندارند")
        
        # بررسی طول رمز عبور
        if len(new_password) < 6:
            raise HTTPException(status_code=400, detail="رمز عبور باید حداقل 6 کاراکتر باشد")
        
        # به‌روزرسانی رمز عبور
        current_user.hashed_password = get_password_hash(new_password)
        db.commit()
        
        return {
            "message": "رمز عبور با موفقیت تغییر کرد"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در تغییر رمز عبور: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh")
async def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    """تازه‌سازی access token با استفاده از refresh token"""
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="توکن نامعتبر است"
            )
        
        user = db.query(models.User).filter(models.User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="کاربر یافت نشد"
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر است"
        )

@router.post("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """تأیید ایمیل کاربر"""
    user = db.query(models.User).filter(models.User.verification_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="توکن تأیید نامعتبر است"
        )
    
    user.is_verified = True
    user.is_active = True
    user.verification_token = None
    db.commit()
    
    return {"message": "ایمیل با موفقیت تأیید شد"}

@router.post("/forgot-password")
async def forgot_password(email: schemas.EmailRequest, db: Session = Depends(get_db)):
    """درخواست بازیابی رمز عبور"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کاربری با این ایمیل یافت نشد"
        )
    
    # ایجاد توکن بازیابی
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # ارسال ایمیل بازیابی
    if hasattr(settings, 'SMTP_SERVER') and settings.SMTP_SERVER:
        send_reset_password_email(email.email, reset_token)
    
    return {"message": "ایمیل بازیابی رمز عبور ارسال شد"}

@router.post("/reset-password")
async def reset_password(reset_data: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    """بازیابی رمز عبور"""
    user = db.query(models.User).filter(
        models.User.reset_token == reset_data.token,
        models.User.reset_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="توکن بازیابی نامعتبر یا منقضی شده است"
        )
    
    # تغییر رمز عبور
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return {"message": "رمز عبور با موفقیت تغییر یافت"}

@router.post("/resend-verification")
async def resend_verification(email: schemas.EmailRequest, db: Session = Depends(get_db)):
    """ارسال مجدد ایمیل تأیید"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کاربری با این ایمیل یافت نشد"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="حساب کاربری قبلاً تأیید شده است"
        )
    
    # ایجاد توکن جدید
    verification_token = secrets.token_urlsafe(32)
    user.verification_token = verification_token
    db.commit()
    
    # ارسال ایمیل تأیید
    if hasattr(settings, 'SMTP_SERVER') and settings.SMTP_SERVER:
        send_verification_email(email.email, verification_token)
    
    return {"message": "ایمیل تأیید مجدداً ارسال شد"} 