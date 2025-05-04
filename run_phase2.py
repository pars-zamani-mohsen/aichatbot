# run_phase2.py

import os
import subprocess
import argparse
import time

def run_phase2(input_csv='processed_data/final_processed_data.csv',
               embeddings_dir='embeddings',
               db_dir='knowledge_base',
               collection_name='website_data',
               model_name='all-MiniLM-L6-v2',
               test_queries=None,
               start_server=False):
    """اجرای کامل فاز 2: ایجاد امبدینگ‌ها و پایگاه دانش"""

    print(f"=== فاز 2: ایجاد امبدینگ‌ها و پایگاه دانش ===")

    # گام 1: ایجاد امبدینگ‌ها
    print("\n=== گام 1: ایجاد امبدینگ‌ها ===")
    embed_cmd = f"python create_embeddings.py --input {input_csv} --output {embeddings_dir} --model {model_name}"
    print(f"اجرای دستور: {embed_cmd}")
    subprocess.run(embed_cmd, shell=True)

    # گام 2: ایجاد پایگاه دانش
    print("\n=== گام 2: ایجاد پایگاه دانش ===")
    kb_cmd = f"python create_knowledge_base.py --embeddings_dir {embeddings_dir} --db_dir {db_dir} --collection {collection_name}"
    print(f"اجرای دستور: {kb_cmd}")
    subprocess.run(kb_cmd, shell=True)

    # گام 3: تست پایگاه دانش (اختیاری)
    if test_queries:
        print("\n=== گام 3: تست پایگاه دانش ===")

        # ذخیره پرس‌وجوهای تست در فایل موقت
                with open('test_queries.txt', 'w', encoding='utf-8') as f:
                    for query in test_queries:
                        f.write(query + '\n')

                # اجرای تست
                test_cmd = f"python test_knowledge_base.py --queries test_queries.txt --db_dir {db_dir} --collection {collection_name}"
                print(f"اجرای دستور: {test_cmd}")
                subprocess.run(test_cmd, shell=True)

                # حذف فایل موقت
                if os.path.exists('test_queries.txt'):
                    os.remove('test_queries.txt')

            # گام 4: راه‌اندازی سرور وب (اختیاری)
            if start_server:
                print("\n=== گام 4: راه‌اندازی سرور وب ===")
                print("راه‌اندازی سرور Flask در http://localhost:5000")
                print("برای توقف سرور، کلیدهای Ctrl+C را فشار دهید.")

                # اجرای سرور وب
                subprocess.run(f"python app.py --db_dir {db_dir} --collection {collection_name}", shell=True)
            else:
                print("\n=== فاز 2 با موفقیت به پایان رسید ===")
                print(f"امبدینگ‌ها در پوشه {embeddings_dir} ذخیره شدند.")
                print(f"پایگاه دانش در پوشه {db_dir} ایجاد شد.")
                print("\nبرای استفاده از چت‌بات، دستور زیر را اجرا کنید:")
                print(f"python chatbot_rag.py --db_dir {db_dir} --collection {collection_name}")
                print("\nبرای راه‌اندازی سرور وب، دستور زیر را اجرا کنید:")
                print(f"python app.py")

        if __name__ == "__main__":
            parser = argparse.ArgumentParser(description='اجرای فاز 2: ایجاد امبدینگ‌ها و پایگاه دانش')

            parser.add_argument('--input', default='processed_data/final_processed_data.csv',
                                help='مسیر فایل CSV حاوی داده‌های پردازش شده')
            parser.add_argument('--embeddings_dir', default='embeddings',
                                help='پوشه خروجی برای ذخیره امبدینگ‌ها')
            parser.add_argument('--db_dir', default='knowledge_base',
                                help='پوشه برای ذخیره پایگاه دانش')
            parser.add_argument('--collection', default='website_data',
                                help='نام کالکشن در پایگاه دانش')
            parser.add_argument('--model', default='all-MiniLM-L6-v2',
                                help='نام مدل sentence-transformers')
            parser.add_argument('--test', action='store_true',
                                help='آیا پایگاه دانش تست شود؟')
            parser.add_argument('--server', action='store_true',
                                help='آیا سرور وب راه‌اندازی شود؟')

            args = parser.parse_args()

            # پرس‌وجوهای پیش‌فرض برای تست
            default_queries = [
                "چگونه می‌توانم حساب کاربری ایجاد کنم؟",
                "محصولات پرفروش",
                "سیاست بازگشت کالا",
                "راه‌های ارتباط با پشتیبانی",
                "ساعات کاری فروشگاه"
            ]

            run_phase2(
                input_csv=args.input,
                embeddings_dir=args.embeddings_dir,
                db_dir=args.db_dir,
                collection_name=args.collection,
                model_name=args.model,
                test_queries=default_queries if args.test else None,
                start_server=args.server
            )