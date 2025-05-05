import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import re
import os
from pathlib import Path
import json
import seaborn as sns
from datetime import datetime
import numpy as np

class DataAnalyzer:
    def __init__(self):
        self.output_dir = Path('analysis_results')
        self.output_dir.mkdir(exist_ok=True)

        plt.rcParams['font.family'] = 'Arial'
        sns.set_style("whitegrid")

    def json_serialize(self, obj):
        """Convert numpy/pandas numeric types to Python native types"""
        if isinstance(obj, (np.int8, np.int16, np.int32, np.int64,
                          np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return obj

    def load_data(self, csv_file='processed_data/processed_data.csv'):
        if not Path(csv_file).exists():
            raise FileNotFoundError(f"فایل {csv_file} یافت نشد!")

        df = pd.read_csv(csv_file)
        if df.empty:
            raise ValueError("دیتاست خالی است!")

        # Convert to native Python types
        df['content'] = df['content'].fillna('')
        df['content_length'] = df['content'].str.len()
        df['word_count'] = df['content'].str.split().str.len().fillna(0).astype(int)

        return df

    def generate_basic_stats(self, df):
        stats = {
            'total_pages': int(len(df)),
            'unique_urls': int(df['url'].nunique()),
            'avg_content_length': float(df['content_length'].mean()),
            'avg_word_count': float(df['word_count'].mean()),
            'total_words': int(df['word_count'].sum()),
            'analysis_timestamp': datetime.now().isoformat()
        }

        with open(self.output_dir / 'basic_stats.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        return stats

    def analyze_content_distribution(self, df):
        plt.figure(figsize=(12, 6))
        sns.histplot(data=df, x='content_length', bins=30)
        plt.title('توزیع طول محتوا در صفحات')
        plt.xlabel('طول محتوا (کاراکتر)')
        plt.ylabel('تعداد صفحات')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'content_distribution.png')
        plt.close()

    def analyze_common_words(self, df, min_word_length=3, min_count=2, top_n=30):
        all_text = ' '.join(df['content'].dropna())
        words = re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+', all_text)
        word_counts = Counter(words)

        filtered_words = {
            word: count for word, count in word_counts.items()
            if len(word) >= min_word_length and count >= min_count
        }

        top_words = dict(
            sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:top_n]
        )

        # Ensure all values are native Python integers
        top_words = {k: int(v) for k, v in top_words.items()}

        plt.figure(figsize=(15, 8))
        plt.bar(range(len(top_words)), list(top_words.values()))
        plt.xticks(range(len(top_words)), list(top_words.keys()),
                  rotation=45, ha='right')
        plt.title(f'{top_n} کلمه پرتکرار')
        plt.xlabel('کلمات')
        plt.ylabel('تعداد تکرار')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'common_words.png')
        plt.close()

        with open(self.output_dir / 'word_frequencies.json', 'w', encoding='utf-8') as f:
            json.dump(top_words, f, ensure_ascii=False, indent=2)

    def generate_report(self, stats):
        report = f"""گزارش تحلیل داده‌ها
========================
تاریخ تحلیل: {stats['analysis_timestamp']}

آمار کلی:
---------
تعداد کل صفحات: {stats['total_pages']}
تعداد URLهای یکتا: {stats['unique_urls']}
میانگین طول محتوا: {stats['avg_content_length']:.2f} کاراکتر
میانگین تعداد کلمات: {stats['avg_word_count']:.2f}
مجموع کل کلمات: {stats['total_words']}

فایل‌های خروجی:
--------------
1. نمودار توزیع محتوا: {self.output_dir}/content_distribution.png
2. نمودار کلمات پرتکرار: {self.output_dir}/common_words.png
3. آمار تفصیلی: {self.output_dir}/basic_stats.json
4. فراوانی کلمات: {self.output_dir}/word_frequencies.json
"""
        with open(self.output_dir / 'analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)

        return report

    def run_analysis(self):
        try:
            print("شروع تحلیل داده‌ها...")

            df = self.load_data()
            stats = self.generate_basic_stats(df)
            self.analyze_content_distribution(df)
            self.analyze_common_words(df)
            report = self.generate_report(stats)

            print("\nتحلیل با موفقیت انجام شد!")
            print(f"نتایج در پوشه {self.output_dir} ذخیره شدند.")
            print("\n=== خلاصه گزارش ===")
            print(report)

        except Exception as e:
            print(f"خطا در تحلیل داده‌ها: {str(e)}")
            raise

if __name__ == "__main__":
    analyzer = DataAnalyzer()
    analyzer.run_analysis()