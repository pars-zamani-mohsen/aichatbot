import sys
import argparse
import pandas as pd
import numpy as np
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import logging
from settings import (
    EMBEDDING_MODEL_NAME,
    CHUNK_SIZE,
    DB_DIRECTORY
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_embeddings(
    input_file,
    output_dir=DB_DIRECTORY,
    model_name=EMBEDDING_MODEL_NAME,
    chunk_size=int(CHUNK_SIZE)
):
    """ایجاد امبدینگ برای متن‌های استخراج شده"""
    try:
        # خواندن داده‌ها
        logger.info(f"خواندن داده‌ها از {input_file}")
        df = pd.read_csv(input_file)
        df['content'] = df['content'].apply(lambda x: x[:1000])

        if df.empty:
            raise ValueError("فایل ورودی خالی است")

        if 'content' not in df.columns:
            raise ValueError("ستون 'content' در داده‌ها یافت نشد")

        # حذف ردیف‌های خالی یا نامعتبر
        df = df.dropna(subset=['content'])
        df = df[df['content'].str.len() > 100]  # حداقل 100 کاراکتر

        if len(df) == 0:
            raise ValueError("هیچ محتوای معتبری برای ایجاد امبدینگ یافت نشد")

        # بارگذاری مدل امبدینگ
        print(f"بارگذاری مدل امبدینگ {model_name}...")
        model = SentenceTransformer(model_name)
        print("مدل با موفقیت بارگذاری شد.")

        # ایجاد امبدینگ‌ها
        embeddings = []
        metadata = []

        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i + chunk_size]
            chunk_embeddings = model.encode(
                chunk['content'].tolist(),
                show_progress_bar=True,
                batch_size=32
            )

            embeddings.extend(chunk_embeddings.tolist())

            chunk_metadata = chunk.apply(
                lambda row: {
                    'url': row['url'],
                    'title': row['title'],
                    'chunk_id': row['chunk_id'],
                    'timestamp': row['timestamp']
                }, axis=1
            ).tolist()

            metadata.extend(chunk_metadata)

            logger.info(f"پردازش شد: {i + len(chunk)} از {len(df)}")

        # ذخیره نتایج
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # ذخیره امبدینگ‌ها
        embeddings_file = output_dir / 'embeddings.json'
        with open(embeddings_file, 'w', encoding='utf-8') as f:
            json.dump(embeddings, f)

        # ذخیره متادیتا
        metadata_file = output_dir / 'metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # ذخیره اطلاعات مدل
        model_info = {
            'model_name': model_name,
            'embedding_size': len(embeddings[0]),
            'num_documents': len(df),
            'columns': df.columns.tolist()
        }

        model_info_file = output_dir / 'model_info.json'
        with open(model_info_file, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)

        print(f"\n=== امبدینگ‌ها با موفقیت ایجاد شدند ===")
        print(f"تعداد اسناد: {len(df)}")
        print(f"اندازه هر امبدینگ: {len(embeddings[0])}")
        print(f"مسیر خروجی: {output_dir}")

        return True

    except Exception as e:
        logger.error(f"خطا در ایجاد امبدینگ‌ها: {str(e)}")
        logger.error(f"خطای اصلی: {str(e)}")
        raise

def parse_args():
    parser = argparse.ArgumentParser(description='ایجاد امبدینگ برای متن‌های استخراج شده')
    parser.add_argument('--input', required=True, help='مسیر فایل CSV ورودی')
    parser.add_argument('--output', default=DB_DIRECTORY, help='مسیر پوشه خروجی')
    parser.add_argument('--model', default=EMBEDDING_MODEL_NAME, help='نام مدل امبدینگ')
    parser.add_argument('--chunk-size', type=int, default=int(CHUNK_SIZE), help='اندازه هر دسته برای پردازش')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    success = create_embeddings(
        args.input,
        args.output,
        args.model,
        args.chunk_size
    )
    sys.exit(0 if success else 1)