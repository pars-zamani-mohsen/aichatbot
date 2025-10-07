#!/usr/bin/env python3
"""
اسکریپت برای به‌روزرسانی متغیرهای محیطی Docker از config.py
"""

import os
import sys
import re

# اضافه کردن مسیر backend به sys.path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

try:
    from app.config import settings
    
    print("🔧 Reading configuration from config.py...")
    
    # خواندن تنظیمات از config.py
    server_ip = settings.SERVER_IP
    backend_port = settings.BACKEND_PORT
    frontend_port = settings.FRONTEND_PORT
    
    print(f"📋 Configuration from config.py:")
    print(f"   SERVER_IP: {server_ip}")
    print(f"   BACKEND_PORT: {backend_port}")
    print(f"   FRONTEND_PORT: {frontend_port}")
    
    # مسیر فایل .env
    env_file_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    # خواندن فایل .env موجود
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            content = f.read()
        
        # به‌روزرسانی متغیرها
        content = re.sub(r'^SERVER_IP=.*', f'SERVER_IP={server_ip}', content, flags=re.MULTILINE)
        content = re.sub(r'^BACKEND_PORT=.*', f'BACKEND_PORT={backend_port}', content, flags=re.MULTILINE)
        content = re.sub(r'^FRONTEND_PORT=.*', f'FRONTEND_PORT={frontend_port}', content, flags=re.MULTILINE)
        
        # نوشتن فایل به‌روزرسانی شده
        with open(env_file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated .env file with values from config.py")
        print(f"📄 Updated variables:")
        print(f"   SERVER_IP={server_ip}")
        print(f"   BACKEND_PORT={backend_port}")
        print(f"   FRONTEND_PORT={frontend_port}")
    else:
        print(f"❌ .env file not found at: {env_file_path}")
        sys.exit(1)
    
except ImportError as e:
    print(f"❌ Error importing config: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
