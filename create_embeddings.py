# create_embeddings.py  

import pandas as pd  
import numpy as np  
import os  
from sentence_transformers import SentenceTransformer  
from tqdm import tqdm  
import json  
import time  

class EmbeddingCreator:  
    def __init__(self, model_name="all-MiniLM-L6-v2"):  
        """مقداردهی اولیه کلاس با مدل امبدینگ مناسب"""  
        print(f"بارگذاری مدل امبدینگ {model_name}...")  
        self.model = SentenceTransformer(model_name)  
        self.model_name = model_name  
        print("مدل با موفقیت بارگذاری شد.")  
    
    def create_embeddings(self, input_csv='processed_data/final_processed_data.csv',   
                           output_dir='embeddings'):  
        """ایجاد امبدینگ‌ها برای داده‌های پردازش شده"""  
        
        # اطمینان از وجود پوشه خروجی  
        os.makedirs(output_dir, exist_ok=True)  
        
        # خواندن داده‌های پردازش شده  
        print(f"خواندن داده‌ها از {input_csv}...")  
        df = pd.read_csv(input_csv)  
        
        # نمایش اطلاعات داده‌ها  
        print(f"تعداد رکوردها: {len(df)}")  
        print(f"ستون‌ها: {df.columns.tolist()}")  
        
        # ایجاد ستون شناسه منحصربه‌فرد اگر وجود ندارد  
        if 'id' not in df.columns and 'chunk_id' in df.columns:  
            df['id'] = df['chunk_id']  
        elif 'id' not in df.columns:  
            df['id'] = [f"doc_{i}" for i in range(len(df))]  
        
        # ذخیره داده‌های اصلی در JSON  
        metadata_file = os.path.join(output_dir, 'metadata.json')  
        metadata = df[['id', 'url', 'title', 'content']].to_dict(orient='records')  
        with open(metadata_file, 'w', encoding='utf-8') as f:  
            json.dump(metadata, f, ensure_ascii=False, indent=2)  
        
        print(f"داده‌های متادیتا در {metadata_file} ذخیره شدند.")  
        
        # ایجاد امبدینگ‌ها برای محتوا  
        print("شروع ایجاد امبدینگ‌ها...")  
        start_time = time.time()  
        
        embeddings = []  
        
        # پردازش هر چانک متن  
        for i, row in tqdm(df.iterrows(), total=len(df), desc="ایجاد امبدینگ‌ها"):  
            # اطمینان از اینکه محتوا رشته متنی است  
            if isinstance(row['content'], str) and len(row['content'].strip()) > 0:  
                # ایجاد امبدینگ  
                try:  
                    embedding = self.model.encode(row['content'])  
                    embeddings.append({  
                        'id': row['id'],  
                        'embedding': embedding.tolist()  
                    })  
                except Exception as e:  
                    print(f"خطا در ایجاد امبدینگ برای رکورد {i}: {e}")  
            else:  
                print(f"هشدار: محتوای نامعتبر برای رکورد {i} یافت شد")  
        
        # محاسبه زمان سپری شده  
        elapsed_time = time.time() - start_time  
        print(f"ایجاد امبدینگ‌ها در {elapsed_time:.2f} ثانیه به پایان رسید.")  
        
        # ذخیره امبدینگ‌ها  
        embeddings_file = os.path.join(output_dir, 'embeddings.json')  
        with open(embeddings_file, 'w', encoding='utf-8') as f:  
            json.dump(embeddings, f)  
        
        print(f"امبدینگ‌ها در {embeddings_file} ذخیره شدند.")  
        
        # ذخیره اطلاعات مدل  
        model_info = {  
            'model_name': self.model_name,  
            'embedding_dimension': len(embeddings[0]['embedding']) if embeddings else 0,  
            'total_embeddings': len(embeddings),  
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')  
        }  
        
        model_info_file = os.path.join(output_dir, 'model_info.json')  
        with open(model_info_file, 'w', encoding='utf-8') as f:  
            json.dump(model_info, f, ensure_ascii=False, indent=2)  
        
        print(f"اطلاعات مدل در {model_info_file} ذخیره شدند.")  
        
        return embeddings, metadata  

if __name__ == "__main__":  
    import argparse  
    
    parser = argparse.ArgumentParser(description='ایجاد امبدینگ‌ها برای داده‌های پردازش شده')  
    parser.add_argument('--input', default='processed_data/final_processed_data.csv',   
                        help='مسیر فایل CSV حاوی داده‌های پردازش شده')  
    parser.add_argument('--output', default='embeddings',   
                        help='پوشه خروجی برای ذخیره امبدینگ‌ها')  
    parser.add_argument('--model', default='all-MiniLM-L6-v2',   
                        help='نام مدل sentence-transformers')  
    
    args = parser.parse_args()  
    
    creator = EmbeddingCreator(model_name=args.model)  
    creator.create_embeddings(input_csv=args.input, output_dir=args.output)  