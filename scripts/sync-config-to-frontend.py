#!/usr/bin/env python3
"""
اسکریپت برای همگام‌سازی تنظیمات از config.py به frontend
"""

import os
import sys
import subprocess

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
    
    # ساخت API URL
    api_url = f"http://{server_ip}:{backend_port}"
    
    print(f"📋 Configuration from config.py:")
    print(f"   SERVER_IP: {server_ip}")
    print(f"   BACKEND_PORT: {backend_port}")
    print(f"   FRONTEND_PORT: {frontend_port}")
    print(f"   API_URL: {api_url}")
    
    # تنظیم متغیرهای محیطی
    env_vars = {
        'REACT_APP_API_URL': api_url,
        'REACT_APP_SERVER_IP': server_ip,
        'REACT_APP_FRONTEND_PORT': frontend_port,
        'REACT_APP_BACKEND_PORT': backend_port
    }
    
    # ایجاد فایل .env برای frontend
    frontend_env_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', '.env')
    
    print(f"📝 Writing frontend .env file to: {frontend_env_path}")
    
    with open(frontend_env_path, 'w') as f:
        f.write("# Frontend Environment Variables (Auto-generated from config.py)\n")
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print("✅ Frontend environment variables updated successfully!")
    print("📄 Frontend .env content:")
    with open(frontend_env_path, 'r') as f:
        print(f.read())
    
    # تنظیم متغیرهای محیطی برای export
    print("\n🔧 Environment variables to export:")
    for key, value in env_vars.items():
        print(f"export {key}={value}")
    
except ImportError as e:
    print(f"❌ Error importing config: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
