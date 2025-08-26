import dns.resolver
import requests
from urllib.parse import urlparse
import hashlib
import secrets
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DomainVerificationService:
    """سرویس تأیید مالکیت دامنه"""
    
    @staticmethod
    def generate_verification_token() -> str:
        """تولید توکن تأیید"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_dns_record(domain: str, token: str) -> bool:
        """تأیید رکورد DNS"""
        try:
            # بررسی رکورد TXT
            txt_records = dns.resolver.resolve(domain, 'TXT')
            for record in txt_records:
                if f'rag-verification={token}' in str(record):
                    return True
            
            # بررسی رکورد CNAME
            cname_records = dns.resolver.resolve(domain, 'CNAME')
            for record in cname_records:
                if token in str(record):
                    return True
                    
        except Exception as e:
            logger.error(f"خطا در بررسی DNS برای دامنه {domain}: {str(e)}")
        
        return False
    
    @staticmethod
    def verify_html_file(domain: str, token: str) -> bool:
        """تأیید فایل HTML"""
        try:
            # تلاش برای دریافت فایل verification.html
            url = f"http://{domain}/rag-verification.html"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                if token in content:
                    return True
                    
        except Exception as e:
            logger.error(f"خطا در بررسی فایل HTML برای دامنه {domain}: {str(e)}")
        
        return False
    
    @staticmethod
    def verify_meta_tag(domain: str, token: str) -> bool:
        """تأیید meta tag"""
        try:
            # دریافت صفحه اصلی
            url = f"http://{domain}/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                # بررسی meta tag
                if f'<meta name="rag-verification" content="{token}">' in content:
                    return True
                    
        except Exception as e:
            logger.error(f"خطا در بررسی meta tag برای دامنه {domain}: {str(e)}")
        
        return False
    
    @staticmethod
    def verify_domain_ownership(domain: str, token: str, method: str = "html") -> Tuple[bool, str]:
        """تأیید مالکیت دامنه"""
        try:
            if method == "dns":
                is_valid = DomainVerificationService.verify_dns_record(domain, token)
                return is_valid, "DNS verification completed"
            elif method == "html":
                is_valid = DomainVerificationService.verify_html_file(domain, token)
                return is_valid, "HTML file verification completed"
            elif method == "meta":
                is_valid = DomainVerificationService.verify_meta_tag(domain, token)
                return is_valid, "Meta tag verification completed"
            else:
                return False, "Invalid verification method"
                
        except Exception as e:
            logger.error(f"خطا در تأیید مالکیت دامنه {domain}: {str(e)}")
            return False, f"Verification error: {str(e)}"
    
    @staticmethod
    def get_verification_instructions(domain: str, token: str, method: str) -> Dict[str, str]:
        """دریافت دستورالعمل‌های تأیید"""
        instructions = {
            "dns": {
                "title": "تأیید از طریق DNS",
                "description": "یک رکورد TXT یا CNAME در DNS دامنه خود اضافه کنید",
                "steps": [
                    f"به پنل مدیریت DNS دامنه خود بروید",
                    f"یک رکورد TXT جدید اضافه کنید:",
                    f"نام: {domain}",
                    f"مقدار: rag-verification={token}",
                    "یا یک رکورد CNAME اضافه کنید:",
                    f"نام: {token}.{domain}",
                    f"مقدار: verification.ragchatbot.com"
                ]
            },
            "html": {
                "title": "تأیید از طریق فایل HTML",
                "description": "فایل HTML تأیید را در ریشه وب‌سایت خود قرار دهید",
                "steps": [
                    "فایل زیر را با نام 'rag-verification.html' در ریشه وب‌سایت خود قرار دهید:",
                    f"<html><head><title>RAG Verification</title></head><body>{token}</body></html>",
                    f"سپس آدرس {domain}/rag-verification.html را بررسی کنید"
                ]
            },
            "meta": {
                "title": "تأیید از طریق Meta Tag",
                "description": "Meta tag تأیید را در صفحه اصلی وب‌سایت خود قرار دهید",
                "steps": [
                    "در بخش <head> صفحه اصلی وب‌سایت خود، این خط را اضافه کنید:",
                    f'<meta name="rag-verification" content="{token}">',
                    f"سپس صفحه اصلی {domain} را بررسی کنید"
                ]
            }
        }
        
        return instructions.get(method, {
            "title": "روش نامعتبر",
            "description": "لطفاً روش تأیید معتبری انتخاب کنید",
            "steps": []
        })
