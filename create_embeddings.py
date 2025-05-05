import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import logging
import sys

class EmbeddingCreator:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.output_dir = Path('embeddings')
        self.output_dir.mkdir(exist_ok=True)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_model(self):
        """Load the embedding model"""
        print(f"بارگذاری مدل امبدینگ {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        print("مدل با موفقیت بارگذاری شد.")
        return self.model

    def prepare_data(self):
        """Load and prepare data from processed CSV"""
        input_paths = [
            'processed_data/processed_data.csv',
            'processed_data/final_processed_data.csv',
            'analysis_results/processed_data.csv'
        ]

        df = None
        for path in input_paths:
            if Path(path).exists():
                print(f"خواندن داده‌ها از {path}...")
                try:
                    df = pd.read_csv(path)
                    if not df.empty:
                        print(f"داده‌ها با موفقیت از {path} خوانده شدند.")
                        print(f"تعداد رکوردها: {len(df)}")
                        print(f"ستون‌ها: {list(df.columns)}")
                        print(f"نمونه داده:\n{df.head(1)}")
                        break
                    else:
                        print(f"فایل {path} خالی است.")
                except Exception as e:
                    print(f"خطا در خواندن {path}: {str(e)}")
                    continue

        if df is None or df.empty:
            raise FileNotFoundError("هیچ داده معتبری یافت نشد!")

        required_columns = ['url', 'title', 'content']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"ستون‌های ضروری یافت نشد: {missing_columns}")

        # Clean and prepare content
        df['content'] = df['content'].fillna('')
        df['title'] = df['title'].fillna('')

        # Filter out empty content
        df = df[df['content'].str.strip().str.len() > 0].copy()

        if df.empty:
            raise ValueError("پس از پاکسازی داده‌ها، هیچ محتوای معتبری باقی نماند!")

        # Create chunks
        chunks = []
        chunk_size = 512

        for idx, row in df.iterrows():
            content = str(row['content'])
            title = str(row['title'])

            # Split content into chunks
            words = content.split()
            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i + chunk_size])
                if len(chunk.strip()) > 0:
                    chunks.append({
                        'url': row['url'],
                        'title': title,
                        'chunk_id': f"{idx}-{i//chunk_size}",
                        'content': chunk,
                        'content_length': len(chunk),
                        'processed_timestamp': datetime.now().isoformat()
                    })

        chunks_df = pd.DataFrame(chunks)
        print(f"\nاطلاعات چانک‌ها:")
        print(f"تعداد چانک‌ها: {len(chunks_df)}")
        print(f"ستون‌ها: {list(chunks_df.columns)}")
        print(f"نمونه چانک:\n{chunks_df.head(1)}")

        # Save metadata
        metadata_file = self.output_dir / 'metadata.json'
        chunks_df.to_json(metadata_file, orient='records', force_ascii=False, indent=2)
        print(f"داده‌های متادیتا در {metadata_file} ذخیره شدند.")

        return chunks_df

    def create_embeddings(self, df):
        """Create embeddings for the prepared chunks"""
        if df.empty:
            raise ValueError("هیچ داده‌ای برای ایجاد امبدینگ وجود ندارد!")

        print("شروع ایجاد امبدینگ‌ها...")
        start_time = datetime.now()

        texts = df['content'].tolist()
        embeddings = []

        for text in tqdm(texts, desc="ایجاد امبدینگ‌ها"):
            try:
                embedding = self.model.encode(text)
                embeddings.append(embedding.tolist())
            except Exception as e:
                self.logger.error(f"خطا در ایجاد امبدینگ برای متن: {text[:100]}...")
                self.logger.error(f"خطا: {str(e)}")
                embeddings.append([0] * self.model.get_sentence_embedding_dimension())

        duration = (datetime.now() - start_time).total_seconds()
        print(f"ایجاد امبدینگ‌ها در {duration:.2f} ثانیه به پایان رسید.")

        # Save embeddings
        embeddings_file = self.output_dir / 'embeddings.json'
        with open(embeddings_file, 'w') as f:
            json.dump(embeddings, f)
        print(f"امبدینگ‌ها در {embeddings_file} ذخیره شدند.")

        # Save model info
        model_info = {
            'model_name': self.model_name,
            'embedding_dimension': self.model.get_sentence_embedding_dimension(),
            'total_embeddings': len(embeddings),
            'created_at': datetime.now().isoformat()
        }

        with open(self.output_dir / 'model_info.json', 'w') as f:
            json.dump(model_info, f, indent=2)
        print(f"اطلاعات مدل در {self.output_dir / 'model_info.json'} ذخیره شدند.")

        return embeddings

    def run(self):
        """Run the complete embedding creation pipeline"""
        try:
            self.load_model()
            df = self.prepare_data()
            self.create_embeddings(df)
        except Exception as e:
            self.logger.error(f"خطا در ایجاد امبدینگ‌ها: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        creator = EmbeddingCreator()
        creator.run()
    except Exception as e:
        print(f"\nخطای اصلی: {str(e)}")
        sys.exit(1)