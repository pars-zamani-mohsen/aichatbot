from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import secrets
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..database.database import get_db
from ..database import models
from . import schemas
from ..config import settings
from ..services.notification_service import NotificationService
from ..services.system_settings_service import SystemSettingsService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.options("/{path:path}")
async def options_handler(path: str):
    """Handle OPTIONS requests for all auth routes"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Max-Age": "86400"
        }
    )

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

def send_verification_email(email: str, token: str, db: Session = None):
    """ارسال ایمیل تأیید"""
    try:
        # دریافت تنظیمات ایمیل از دیتابیس
        if db:
            email_settings = SystemSettingsService.get_email_settings(db)
            smtp_server = email_settings.get('smtp_server', 'smtp.gmail.com')
            smtp_port = email_settings.get('smtp_port', 587)
            smtp_username = email_settings.get('smtp_username', '')
            smtp_password = email_settings.get('smtp_password', '')
            email_from = email_settings.get('email_from', '')
        else:
            # استفاده از تنظیمات پیش‌فرض
            smtp_server = settings.SMTP_SERVER
            smtp_port = settings.SMTP_PORT
            smtp_username = settings.SMTP_USERNAME
            smtp_password = settings.SMTP_PASSWORD
            email_from = settings.SMTP_USERNAME
        
        msg = MIMEMultipart()
        msg['From'] = email_from
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
        
        # آرشیو ایمیل قبل از ارسال (همیشه)
        if db:
            from ..services.email_archive_service import EmailArchiveService
            user = db.query(models.User).filter(models.User.email == email).first()
            user_id = user.id if user else None
            
            EmailArchiveService.archive_email(
                db=db,
                email_type="verification",
                recipient_email=email,
                subject="تأیید حساب کاربری",
                body=body,
                from_email=email_from,
                to_email=email,
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                user_id=user_id,
                extra_data={"token": token}
            )
        
        # بررسی تنظیمات ایمیل برای ارسال
        if not smtp_server or not smtp_username or not smtp_password:
            logger.warning("SMTP settings not configured, skipping email send but archived")
            return False
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        logger.error(f"خطا در ارسال ایمیل: {str(e)}")
        return False

def send_reset_password_email(email: str, token: str, db: Session = None):
    """ارسال ایمیل بازیابی رمز عبور"""
    try:
        # دریافت تنظیمات ایمیل از دیتابیس
        if db:
            email_settings = SystemSettingsService.get_email_settings(db)
            smtp_server = email_settings.get('smtp_server', 'smtp.gmail.com')
            smtp_port = email_settings.get('smtp_port', 587)
            smtp_username = email_settings.get('smtp_username', '')
            smtp_password = email_settings.get('smtp_password', '')
            email_from = email_settings.get('email_from', '')
        else:
            # استفاده از تنظیمات پیش‌فرض
            smtp_server = settings.SMTP_SERVER
            smtp_port = settings.SMTP_PORT
            smtp_username = settings.SMTP_USERNAME
            smtp_password = settings.SMTP_PASSWORD
            email_from = settings.SMTP_USERNAME
        
        msg = MIMEMultipart()
        msg['From'] = email_from
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
        
        # آرشیو ایمیل قبل از ارسال (همیشه)
        if db:
            from ..services.email_archive_service import EmailArchiveService
            user = db.query(models.User).filter(models.User.email == email).first()
            user_id = user.id if user else None
            
            EmailArchiveService.archive_email(
                db=db,
                email_type="reset_password",
                recipient_email=email,
                subject="بازیابی رمز عبور",
                body=body,
                from_email=email_from,
                to_email=email,
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                user_id=user_id,
                extra_data={"token": token}
            )
        
        # بررسی تنظیمات ایمیل برای ارسال
        if not smtp_server or not smtp_username or not smtp_password:
            logger.warning("SMTP settings not configured, skipping email send but archived")
            return False
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        logger.error(f"خطا در ارسال ایمیل: {str(e)}")
        return False

def generate_2fa_code() -> str:
    """تولید کد 6 رقمی برای 2FA"""
    return str(random.randint(100000, 999999))

def send_2fa_code_email(email: str, code: str, db: Session = None):
    """ارسال کد 2FA به ایمیل"""
    try:
        # دریافت تنظیمات ایمیل از دیتابیس
        if db:
            email_settings = SystemSettingsService.get_email_settings(db)
            smtp_server = email_settings.get('smtp_server', 'smtp.gmail.com')
            smtp_port = email_settings.get('smtp_port', 587)
            smtp_username = email_settings.get('smtp_username', '')
            smtp_password = email_settings.get('smtp_password', '')
            email_from = email_settings.get('email_from', '')
        else:
            # استفاده از تنظیمات پیش‌فرض
            smtp_server = settings.SMTP_SERVER
            smtp_port = settings.SMTP_PORT
            smtp_username = settings.SMTP_USERNAME
            smtp_password = settings.SMTP_PASSWORD
            email_from = settings.SMTP_USERNAME
        
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email
        msg['Subject'] = "کد احراز هویت دو مرحله‌ای"
        
        body = f"""
        سلام!
        
        کد احراز هویت شما: {code}
        
        این کد تا 5 دقیقه معتبر است.
        
        اگر شما این درخواست را نکرده‌اید، این ایمیل را نادیده بگیرید.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # آرشیو ایمیل قبل از ارسال (همیشه)
        if db:
            from ..services.email_archive_service import EmailArchiveService
            user = db.query(models.User).filter(models.User.email == email).first()
            user_id = user.id if user else None
            
            EmailArchiveService.archive_email(
                db=db,
                email_type="2fa",
                recipient_email=email,
                subject="کد احراز هویت دو مرحله‌ای",
                body=body,
                from_email=email_from,
                to_email=email,
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                user_id=user_id,
                extra_data={"code": code}
            )
        
        # بررسی تنظیمات ایمیل برای ارسال
        if not smtp_server or not smtp_username or not smtp_password:
            logger.warning("SMTP settings not configured, skipping email send but archived")
            return True
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        logger.error(f"خطا در ارسال کد 2FA: {str(e)}")
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
        # بررسی وجود token
        if not token:
            logger.warning("Token not provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token ارائه نشده است",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # بررسی فرمت token - پشتیبانی از هر دو فرمت
        clean_token = token
        if token.startswith('Bearer '):
            clean_token = token.replace('Bearer ', '')
            logger.debug("Bearer prefix removed from token")
        else:
            logger.debug("Token without Bearer prefix - using as is")
        
        # بررسی طول token
        if len(clean_token) < 10:
            logger.warning(f"Token too short: {len(clean_token)} characters")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token خیلی کوتاه است",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # استفاده از clean_token
        token = clean_token
        
        # بررسی طول token
        if len(token) < 10:
            logger.warning("Token too short")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token خیلی کوتاه است",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # decode کردن JWT
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token منقضی شده است",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token نامعتبر است",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # بررسی payload
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token payload missing 'sub' field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token فاقد اطلاعات کاربر است",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # بررسی زمان انقضا
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            logger.warning("Token expired (from payload)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token منقضی شده است",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = schemas.TokenData(email=email)
        
        # بررسی وجود کاربر در دیتابیس
        user = db.query(models.User).filter(models.User.email == token_data.email).first()
        if user is None:
            logger.warning(f"User not found: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="کاربر یافت نشد",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # بررسی فعال بودن کاربر
        if not user.is_active:
            logger.warning(f"User inactive: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="حساب کاربری غیرفعال است",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # به‌روزرسانی آخرین ورود
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(f"User authenticated successfully: {email}")
        return user
        
    except HTTPException:
        # اگر HTTPException قبلاً raise شده، آن را دوباره raise کن
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="خطا در احراز هویت",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # دریافت تنظیمات امنیت
    security_settings = SystemSettingsService.get_security_settings(db)
    password_min_length = security_settings.get('passwordMinLength', 8)
    require_email_verification = security_settings.get('requireEmailVerification', True)
    
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ایمیل قبلاً ثبت شده است"
        )
    
    # بررسی طول رمز عبور
    if len(user.password) < password_min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"رمز عبور باید حداقل {password_min_length} کاراکتر باشد"
        )
    
    # ایجاد توکن تأیید
    verification_token = secrets.token_urlsafe(32)
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password,
        verification_token=verification_token,
        is_active=not require_email_verification,  # اگر تأیید ایمیل نیاز نیست، کاربر فعال است
        is_verified=not require_email_verification
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # ارسال ایمیل تأیید اگر نیاز باشد
    if require_email_verification:
        send_verification_email(user.email, verification_token, db)
    
    return db_user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """لاگین کاربر"""
    try:
        logger.info(f"درخواست لاگین - ایمیل: {form_data.username}")
        
        # بررسی وجود کاربر
        user = db.query(models.User).filter(models.User.email == form_data.username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ایمیل یا رمز عبور اشتباه است",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # بررسی rate limiting
        user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == user.id).first()
        if not user_settings:
            user_settings = models.UserSettings(user_id=user.id)
            db.add(user_settings)
            db.commit()
        
        # بررسی قفل لاگین
        if user_settings.login_locked_until and user_settings.login_locked_until > datetime.now(timezone.utc):
            remaining_time = user_settings.login_locked_until - datetime.now(timezone.utc)
            minutes = int(remaining_time.total_seconds() // 60)
            seconds = int(remaining_time.total_seconds() % 60)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"حساب کاربری به دلیل تلاش‌های ناموفق قفل شده است. {minutes} دقیقه و {seconds} ثانیه دیگر تلاش کنید."
            )
        
        # بررسی فاصله زمانی بین تلاش‌ها (حداقل 2 ثانیه)
        if user_settings.last_login_attempt:
            time_diff = datetime.now(timezone.utc) - user_settings.last_login_attempt
            if time_diff.total_seconds() < 2:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="لطفاً 2 ثانیه صبر کنید و دوباره تلاش کنید."
                )
        
        # بررسی رمز عبور و migration در صورت نیاز
        if not verify_password(form_data.password, user.hashed_password):
            # افزایش تعداد تلاش‌های ناموفق
            user_settings.login_attempts += 1
            user_settings.last_login_attempt = datetime.now(timezone.utc)
            
            # دریافت تنظیمات امنیت
            security_settings = SystemSettingsService.get_security_settings(db)
            max_login_attempts = security_settings.get('maxLoginAttempts', 5)
            
            # اگر به حداکثر تلاش رسید، قفل کردن برای 30 دقیقه
            if user_settings.login_attempts >= max_login_attempts:
                user_settings.login_locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
                user_settings.login_attempts = 0
                db.commit()
                
                # ارسال اعلان امنیتی
                NotificationService.notify_security_event(
                    db=db,
                    user_id=user.id,
                    event_type="account_locked",
                    details="حساب کاربری به دلیل 5 تلاش ناموفق برای 30 دقیقه قفل شده است."
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="به دلیل 5 تلاش ناموفق، حساب کاربری برای 30 دقیقه قفل شده است."
                )
            
            db.commit()
            remaining_attempts = 5 - user_settings.login_attempts
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"ایمیل یا رمز عبور اشتباه است. {remaining_attempts} تلاش باقی‌مانده است.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # migration hash قدیمی به Argon2
        if migrate_password_hash(user, form_data.password):
            db.commit()
        
        # به‌روزرسانی last_login و reset کردن تلاش‌های ناموفق
        user.last_login = datetime.utcnow()
        user_settings.login_attempts = 0
        user_settings.login_locked_until = None
        user_settings.last_login_attempt = None
        db.commit()
        
        # بررسی فعال بودن حساب
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="حساب کاربری شما فعال نیست. لطفاً ایمیل خود را تأیید کنید."
            )
        
        # بررسی 2FA
        user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == user.id).first()
        
        if user_settings and user_settings.two_factor_enabled:
            # تولید کد 2FA جدید
            code = generate_2fa_code()
            user_settings.two_factor_code = code
            user_settings.two_factor_expires = datetime.now(timezone.utc) + timedelta(minutes=5)
            db.commit()
            
            # ارسال کد به ایمیل
            if send_2fa_code_email(user.email, code, db):
                raise HTTPException(
                    status_code=status.HTTP_202_ACCEPTED,
                    detail="کد احراز هویت دو مرحله‌ای به ایمیل شما ارسال شد",
                    headers={"X-Requires-2FA": "true"}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="خطا در ارسال کد احراز هویت"
                )
        
        # اگر 2FA فعال نیست، لاگین مستقیم
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در لاگین: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطا در ورود به سیستم"
        )

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
        
        # ارسال اعلان امنیتی
        NotificationService.notify_security_event(
            db=db,
            user_id=current_user.id,
            event_type="password_changed",
            details="رمز عبور با موفقیت تغییر یافت."
        )
        
        return {
            "message": "رمز عبور با موفقیت تغییر کرد"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در تغییر رمز عبور: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enable-2fa")
async def enable_2fa(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """فعال‌سازی احراز هویت دو مرحله‌ای"""
    try:
        # دریافت تنظیمات کاربر
        user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
        
        if not user_settings:
            user_settings = models.UserSettings(user_id=current_user.id)
            db.add(user_settings)
        
        # تولید کد 6 رقمی
        code = generate_2fa_code()
        
        # ذخیره کد و زمان انقضا (5 دقیقه)
        user_settings.two_factor_code = code
        user_settings.two_factor_expires = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        db.commit()
        
        # ارسال کد به ایمیل
        if send_2fa_code_email(current_user.email, code, db):
            return {
                "message": "کد احراز هویت به ایمیل شما ارسال شد",
                "email": current_user.email
            }
        else:
            raise HTTPException(status_code=500, detail="خطا در ارسال کد به ایمیل")
            
    except Exception as e:
        logger.error(f"خطا در فعال‌سازی 2FA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-2fa")
async def verify_2fa(
    code_data: schemas.TwoFactorCode,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """تأیید کد 2FA و فعال‌سازی"""
    try:
        
        # دریافت تنظیمات کاربر
        user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
        
        if not user_settings:
            # ایجاد تنظیمات کاربر اگر وجود ندارد
            user_settings = models.UserSettings(user_id=current_user.id)
            db.add(user_settings)
            db.commit()
            db.refresh(user_settings)
        
        if not user_settings.two_factor_code:
            raise HTTPException(status_code=400, detail="کد احراز هویت یافت نشد. لطفاً دوباره درخواست کد دهید.")
        
        # بررسی انقضای کد
        if user_settings.two_factor_expires and user_settings.two_factor_expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="کد احراز هویت منقضی شده است. لطفاً کد جدید درخواست دهید.")
        
        # بررسی صحت کد
        if user_settings.two_factor_code != code_data.code:
            raise HTTPException(status_code=400, detail="کد احراز هویت اشتباه است")
        
        # فعال‌سازی 2FA
        user_settings.two_factor_enabled = True
        user_settings.two_factor_code = None  # پاک کردن کد
        user_settings.two_factor_expires = None
        
        db.commit()
        
        # ارسال اعلان امنیتی
        try:
            NotificationService.notify_security_event(
                db=db,
                user_id=current_user.id,
                event_type="2fa_enabled",
                details="احراز هویت دو مرحله‌ای با موفقیت فعال شد."
            )
        except Exception as e:
            logger.warning(f"Failed to send security notification: {str(e)}")
        
        return {
            "message": "احراز هویت دو مرحله‌ای با موفقیت فعال شد"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در تأیید 2FA: {str(e)}")
        raise HTTPException(status_code=500, detail="خطا در تأیید کد احراز هویت")

@router.post("/disable-2fa")
async def disable_2fa(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """غیرفعال‌سازی احراز هویت دو مرحله‌ای"""
    try:
        # دریافت تنظیمات کاربر
        user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
        
        if not user_settings:
            raise HTTPException(status_code=400, detail="تنظیمات کاربر یافت نشد")
        
        # غیرفعال‌سازی 2FA
        user_settings.two_factor_enabled = False
        user_settings.two_factor_code = None
        user_settings.two_factor_expires = None
        
        db.commit()
        
        # ارسال اعلان امنیتی
        NotificationService.notify_security_event(
            db=db,
            user_id=current_user.id,
            event_type="2fa_disabled",
            details="احراز هویت دو مرحله‌ای غیرفعال شد."
        )
        
        return {
            "message": "احراز هویت دو مرحله‌ای غیرفعال شد"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در غیرفعال‌سازی 2FA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login-2fa")
async def login_with_2fa(
    code_data: schemas.TwoFactorCode,
    db: Session = Depends(get_db)
):
    """لاگین با کد 2FA"""
    try:
        # دریافت کاربر با ایمیل
        user = db.query(models.User).filter(models.User.email == code_data.email).first()
        if not user:
            raise HTTPException(status_code=400, detail="کاربر یافت نشد")
        
        # دریافت تنظیمات کاربر
        user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == user.id).first()
        
        if not user_settings or not user_settings.two_factor_enabled:
            raise HTTPException(status_code=400, detail="احراز هویت دو مرحله‌ای فعال نیست")
        
        # بررسی قفل 2FA
        if user_settings.two_factor_locked_until and user_settings.two_factor_locked_until > datetime.now(timezone.utc):
            remaining_time = user_settings.two_factor_locked_until - datetime.now(timezone.utc)
            minutes = int(remaining_time.total_seconds() // 60)
            seconds = int(remaining_time.total_seconds() % 60)
            raise HTTPException(
                status_code=400, 
                detail=f"حساب کاربری به دلیل تلاش‌های ناموفق قفل شده است. {minutes} دقیقه و {seconds} ثانیه دیگر تلاش کنید."
            )
        
        # بررسی کد
        if user_settings.two_factor_code != code_data.code:
            # افزایش تعداد تلاش‌های ناموفق
            user_settings.two_factor_attempts += 1
            
            # اگر 3 بار تلاش ناموفق، قفل کردن برای 15 دقیقه
            if user_settings.two_factor_attempts >= 3:
                user_settings.two_factor_locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                user_settings.two_factor_attempts = 0
                db.commit()
                raise HTTPException(
                    status_code=400, 
                    detail="به دلیل 3 تلاش ناموفق، حساب کاربری برای 15 دقیقه قفل شده است."
                )
            
            db.commit()
            remaining_attempts = 3 - user_settings.two_factor_attempts
            raise HTTPException(
                status_code=400, 
                detail=f"کد احراز هویت اشتباه است. {remaining_attempts} تلاش باقی‌مانده است."
            )
        
        # بررسی انقضای کد
        if user_settings.two_factor_expires and user_settings.two_factor_expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="کد احراز هویت منقضی شده است")
        
        # پاک کردن کد استفاده شده و reset کردن تلاش‌ها
        user_settings.two_factor_code = None
        user_settings.two_factor_expires = None
        user_settings.two_factor_attempts = 0
        user_settings.two_factor_locked_until = None
        db.commit()
        
        # تولید توکن دسترسی
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role}, 
            expires_delta=access_token_expires
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطا در لاگین 2FA: {str(e)}")
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

@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """تأیید ایمیل کاربر (GET endpoint برای لینک ایمیل)"""
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
    
    # ریدایرکت به صفحه لاگین با پیام موفقیت
    return {"message": "ایمیل با موفقیت تأیید شد", "redirect": "/login"}

@router.post("/verify-email")
async def verify_email_post(token: str, db: Session = Depends(get_db)):
    """تأیید ایمیل کاربر (POST endpoint برای API)"""
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
    user = db.query(models.User).filter(models.User.email == email.email).first()
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
        send_reset_password_email(email.email, reset_token, db)
    else:
        # در محیط local، توکن را در console نمایش دهیم
        if settings.DEBUG_MODE:
            logger.info(f"کد بازیابی کلمه عبور برای {email.email}: {reset_token}")
            logger.info(f"لینک بازیابی: http://localhost:3000/reset-password?token={reset_token}")
    
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

@router.get("/debug/reset-tokens")
async def debug_reset_tokens(db: Session = Depends(get_db)):
    """نمایش توکن‌های بازیابی فعال (فقط برای تست)"""
    try:
        # فقط در محیط development
        import os
        if os.getenv('ENVIRONMENT') != 'development':
            raise HTTPException(status_code=404, detail="Not found")
        
        users_with_tokens = db.query(models.User).filter(
            models.User.reset_token.isnot(None),
            models.User.reset_token_expires > datetime.utcnow()
        ).all()
        
        tokens = []
        for user in users_with_tokens:
            tokens.append({
                "email": user.email,
                "reset_token": user.reset_token,
                "expires_at": user.reset_token_expires.isoformat() if user.reset_token_expires else None,
                "reset_link": f"http://localhost:3000/reset-password?token={user.reset_token}"
            })
        
        return {
            "active_tokens": tokens,
            "count": len(tokens)
        }
        
    except Exception as e:
        logger.error(f"خطا در نمایش توکن‌ها: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 