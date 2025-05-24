import sys
import os
import subprocess
import argparse
import time
import socket
from pathlib import Path
from datetime import datetime

def is_port_in_use(port):
    """بررسی در دسترس بودن پورت"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_phase2(domain,
               embeddings_dir='embeddings',
               db_dir='knowledge_base/{domain}',
               collection_name=None,
               model_name='all-MiniLM-L6-v2',
               test_queries=None,
               start_server=False,
               server_type='default',
               port=5000,
               chunk_size=500):
    """اجرای فاز 2 برای یک سایت مشخص"""

    # تنظیم مسیرها
    site_dir = Path('processed_data') / domain
    if not site_dir.exists():
        raise ValueError(f"داده‌های سایت {domain} یافت نشد!")

    # تنظیم نام کالکشن
    if collection_name is None:
        collection_name = domain.replace('.', '_')

    # ایجاد پوشه‌های خروجی مختص این سایت
    site_embeddings_dir = site_dir / embeddings_dir
    site_embeddings_dir.mkdir(exist_ok=True)

    site_db_dir = site_dir / db_dir
    site_db_dir.mkdir(exist_ok=True)

    print(f"=== فاز 2: ایجاد امبدینگ‌ها و پایگاه دانش برای {domain} ===")

    # گام 1: ایجاد امبدینگ‌ها
    print("\n=== گام 1: ایجاد امبدینگ‌ها ===")
    embed_cmd = [
        "python", "create_embeddings.py",
        "--input", str(site_dir / 'processed_data.csv'),
        "--output", str(site_embeddings_dir),
        "--model", model_name
    ]
    print(f"اجرای دستور: {' '.join(embed_cmd)}")
    subprocess.run(embed_cmd, check=True)

    # گام 2: ایجاد پایگاه دانش
    print("\n=== گام 2: ایجاد پایگاه دانش ===")
    kb_cmd = [
        "python", "create_knowledge_base.py",
        "--embeddings_dir", str(site_embeddings_dir),
        "--collection", collection_name
    ]
    print(f"اجرای دستور: {' '.join(kb_cmd)}")
    subprocess.run(kb_cmd, check=True)

    # گام 3: تست پایگاه دانش (اختیاری)
    if test_queries:
        print("\n=== گام 3: تست پایگاه دانش ===")
        queries_file = site_dir / 'test_queries.txt'
        with open(queries_file, 'w', encoding='utf-8') as f:
            for query in test_queries:
                f.write(query + '\n')

        test_cmd = [
            "python", "test_knowledge_base.py",
            "--db", str(site_db_dir),
            "--collection", collection_name,
            "--queries", str(queries_file)
        ]
        print(f"اجرای دستور: {' '.join(test_cmd)}")
        subprocess.run(test_cmd, check=True)

        if queries_file.exists():
            queries_file.unlink()

    # گام 4: راه‌اندازی سرور (اختیاری)
    if start_server:
        print(f"\n=== گام 4: راه‌اندازی سرور {server_type} در پورت {port} ===")

        if is_port_in_use(port):
            print(f"خطا: پورت {port} در حال استفاده است!")
            return

        server_cmd = [
            "python", "app.py",
            "--type", server_type,
            "--port", str(port),
            "--collection", collection_name,
            "--db-dir", str(site_dir / db_dir)  # Use full path
        ]

        print(f"راه‌اندازی سرور با دستور: {' '.join(server_cmd)}")
        server_process = subprocess.Popen(server_cmd)

        print(f"\nسرور {server_type} برای {domain} در http://localhost:{port} راه‌اندازی شد.")
        print("برای توقف سرور، کلید Ctrl+C را فشار دهید.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nدر حال توقف سرور...")
            server_process.terminate()

    else:
        print(f"\n=== فاز 2 برای {domain} با موفقیت به پایان رسید ===")
        print(f"امبدینگ‌ها در {site_embeddings_dir} ذخیره شدند.")
        print(f"پایگاه دانش در {site_db_dir} ایجاد شد.")
        print("\nبرای راه‌اندازی سرور، از دستور زیر استفاده کنید:")
        print(f"python run_phase2.py {domain} --server [--type <نوع-سرور>] [--port <شماره-پورت>]")

def parse_args():
    parser = argparse.ArgumentParser(description='اجرای فاز 2: ایجاد امبدینگ‌ها و پایگاه دانش')
    parser.add_argument('domain', help='دامنه سایت')
    parser.add_argument('--test', action='store_true',
                      help='آیا پایگاه دانش تست شود؟')
    parser.add_argument('--server', action='store_true',
                      help='آیا سرور راه‌اندازی شود؟')
    parser.add_argument('--type', type=str, default='default',
                      help='نوع سرور (default, gemini, ...)')
    parser.add_argument('--port', type=int, default=5000,
                      help='پورت سرور')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    default_queries = [
        "مراحل اخذ ویزا چیست؟",
        "هزینه مهاجرت به کانادا",
        "شرایط ثبت شرکت",
        "مدارک مورد نیاز",
        "مدت زمان دریافت ویزا"
    ]

    try:
        run_phase2(
            domain=args.domain,
            test_queries=default_queries if args.test else None,
            start_server=args.server,
            server_type=args.type,
            port=args.port,
            chunk_size=500
        )
    except KeyboardInterrupt:
        print("\nعملیات توسط کاربر متوقف شد.")
    except Exception as e:
        print(f"\nخطا: {str(e)}")
        sys.exit(1)