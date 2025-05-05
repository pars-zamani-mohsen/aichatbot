import os
import subprocess
import argparse
import time
import socket

def is_port_in_use(port):
    """بررسی در دسترس بودن پورت"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_phase2(input_csv='processed_data/final_processed_data.csv',
               embeddings_dir='embeddings',
               db_dir='knowledge_base',
               collection_name='website_data',
               model_name='all-MiniLM-L6-v2',
               test_queries=None,
               start_server=False,
               server_type='default',
               port=5000):
    """اجرای کامل فاز 2: ایجاد امبدینگ‌ها و پایگاه دانش"""

    print(f"=== فاز 2: ایجاد امبدینگ‌ها و پایگاه دانش ===")

    # گام 1: ایجاد امبدینگ‌ها
    print("\n=== گام 1: ایجاد امبدینگ‌ها ===")
    embed_cmd = f"python create_embeddings.py"
    print(f"اجرای دستور: {embed_cmd}")
    subprocess.run(embed_cmd, shell=True, check=True)

    # گام 2: ایجاد پایگاه دانش
    print("\n=== گام 2: ایجاد پایگاه دانش ===")
    kb_cmd = f"python create_knowledge_base.py --collection {collection_name}"
    print(f"اجرای دستور: {kb_cmd}")
    subprocess.run(kb_cmd, shell=True, check=True)

    # گام 3: تست پایگاه دانش (اختیاری)
    if test_queries:
        print("\n=== گام 3: تست پایگاه دانش ===")
        with open('test_queries.txt', 'w', encoding='utf-8') as f:
            for query in test_queries:
                f.write(query + '\n')

        test_cmd = f"python test_knowledge_base.py"
        print(f"اجرای دستور: {test_cmd}")
        subprocess.run(test_cmd, shell=True, check=True)

        if os.path.exists('test_queries.txt'):
            os.remove('test_queries.txt')

    # گام 4: راه‌اندازی سرورها (اختیاری)
    if start_server:
        print(f"\n=== گام 4: راه‌اندازی سرور {server_type} در پورت {port} ===")

        # بررسی پورت
        if is_port_in_use(port):
            print(f"خطا: پورت {port} در حال استفاده است!")
            return

        # راه‌اندازی سرور با پارامترهای مشخص شده
        server_cmd = ["python", "app.py"]
        if server_type != 'default':
            server_cmd.extend(["--type", server_type])
        if port != 5000:
            server_cmd.extend(["--port", str(port)])

        print(f"راه‌اندازی سرور با دستور: {' '.join(server_cmd)}")
        server_process = subprocess.Popen(server_cmd)

        print(f"\nسرور {server_type} در http://localhost:{port} راه‌اندازی شد.")
        print("برای توقف سرور، کلید Ctrl+C را فشار دهید.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nدر حال توقف سرور...")
            server_process.terminate()

    else:
        print("\n=== فاز 2 با موفقیت به پایان رسید ===")
        print(f"امبدینگ‌ها در پوشه {embeddings_dir} ذخیره شدند.")
        print(f"پایگاه دانش در پوشه {db_dir} ایجاد شد.")
        print("\nبرای راه‌اندازی سرور، از دستور زیر استفاده کنید:")
        print("python run_phase2.py --server [--type <نوع-سرور>] [--port <شماره-پورت>]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='اجرای فاز 2: ایجاد امبدینگ‌ها و پایگاه دانش')
    parser.add_argument('--test', action='store_true',
                      help='آیا پایگاه دانش تست شود؟')
    parser.add_argument('--server', action='store_true',
                      help='آیا سرور راه‌اندازی شود؟')
    parser.add_argument('--type', type=str, default='default',
                      help='نوع سرور (default, gemini, ...)')
    parser.add_argument('--port', type=int, default=5000,
                      help='پورت سرور')
    args = parser.parse_args()

    # پرس‌وجوهای پیش‌فرض برای تست
    default_queries = [
        "مراحل اخذ ویزا چیست؟",
        "هزینه مهاجرت به کانادا",
        "شرایط ثبت شرکت",
        "مدارک مورد نیاز",
        "مدت زمان دریافت ویزا"
    ]

    try:
        run_phase2(
            test_queries=default_queries if args.test else None,
            start_server=args.server,
            server_type=args.type,
            port=args.port
        )
    except KeyboardInterrupt:
        print("\nعملیات توسط کاربر متوقف شد.")
    except Exception as e:
        print(f"\nخطا: {str(e)}")