import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import magic
import PyPDF2
import pdfplumber
from docx import Document
from ..config import settings

logger = logging.getLogger(__name__)

class FileProcessor:
    """پردازش فایل‌های مختلف و استخراج متن"""
    
    def __init__(self):
        self.allowed_extensions = settings.ALLOWED_FILE_TYPES
        self.max_file_size = settings.MAX_FILE_SIZE
        
    def validate_file(self, file_path: str, filename: str) -> bool:
        """اعتبارسنجی فایل"""
        try:
            # بررسی اندازه فایل
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error(f"File size {file_size} exceeds maximum {self.max_file_size}")
                return False
            
            # بررسی پسوند فایل
            file_ext = filename.split('.')[-1].lower()
            if file_ext not in self.allowed_extensions:
                logger.error(f"File extension {file_ext} not allowed")
                return False
            
            # بررسی نوع فایل با magic (اختیاری)
            try:
                file_type = magic.from_file(file_path, mime=True)
                logger.info(f"File type detected: {file_type}")
            except Exception as e:
                logger.warning(f"Could not detect file type with magic: {e}")
                # ادامه بدون بررسی magic
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return False
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """استخراج متن از فایل PDF"""
        try:
            text = ""
            
            # روش اول: استفاده از pdfplumber (بهتر برای PDF های پیچیده)
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                logger.info(f"PDF text extracted using pdfplumber: {len(text)} characters")
            except Exception as e:
                logger.warning(f"pdfplumber failed, trying PyPDF2: {str(e)}")
                
                # روش دوم: استفاده از PyPDF2 (پشتیبان)
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                logger.info(f"PDF text extracted using PyPDF2: {len(text)} characters")
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """استخراج متن از فایل DOCX"""
        try:
            doc = Document(file_path)
            text = ""
            
            # استخراج متن از پاراگراف‌ها
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            
            # استخراج متن از جداول
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text += cell.text + " "
                    text += "\n"
            
            logger.info(f"DOCX text extracted: {len(text)} characters")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """استخراج متن از فایل TXT"""
        try:
            # تشخیص encoding
            encodings = ['utf-8', 'utf-8-sig', 'cp1256', 'iso-8859-1', 'windows-1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        text = file.read()
                    logger.info(f"TXT text extracted with encoding {encoding}: {len(text)} characters")
                    return text.strip()
                except UnicodeDecodeError:
                    continue
            
            # اگر هیچ encoding کار نکرد، با errors='ignore' بخوان
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
            logger.warning(f"TXT text extracted with errors ignored: {len(text)} characters")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            raise
    
    def extract_text_from_file(self, file_path: str, filename: str) -> str:
        """استخراج متن از فایل بر اساس نوع آن"""
        try:
            # اعتبارسنجی فایل
            if not self.validate_file(file_path, filename):
                raise ValueError("فایل معتبر نیست")
            
            # تشخیص نوع فایل
            file_ext = filename.split('.')[-1].lower()
            
            if file_ext == 'pdf':
                return self.extract_text_from_pdf(file_path)
            elif file_ext in ['docx', 'doc']:
                return self.extract_text_from_docx(file_path)
            elif file_ext == 'txt':
                return self.extract_text_from_txt(file_path)
            else:
                raise ValueError(f"فرمت فایل {file_ext} پشتیبانی نمی‌شود")
                
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}")
            raise
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list:
        """تقسیم متن به قطعات کوچک‌تر"""
        try:
            if not text or len(text.strip()) == 0:
                return []
            
            # پاکسازی متن
            text = text.strip()
            
            # اگر متن کوتاه است، همان را برگردان
            if len(text) <= chunk_size:
                return [text]
            
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + chunk_size
                
                # اگر به انتهای متن رسیدیم
                if end >= len(text):
                    chunks.append(text[start:])
                    break
                
                # پیدا کردن نقطه مناسب برای تقسیم (نقطه، خط جدید، یا فاصله)
                chunk = text[start:end]
                
                # جستجو برای نقطه تقسیم مناسب
                split_point = chunk_size
                for i in range(chunk_size - 1, max(0, chunk_size - 100), -1):
                    if chunk[i] in ['.', '\n', '!', '?', ';']:
                        split_point = i + 1
                        break
                    elif chunk[i] == ' ' and i > chunk_size - 50:
                        split_point = i
                        break
                
                chunks.append(text[start:start + split_point].strip())
                start = start + split_point - overlap
                
                # جلوگیری از حلقه بی‌نهایت
                if start >= len(text):
                    break
            
            logger.info(f"Text chunked into {len(chunks)} pieces")
            return [chunk for chunk in chunks if chunk.strip()]
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise
    
    def process_file(self, file_path: str, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """پردازش کامل فایل و استخراج متن"""
        try:
            # استخراج متن
            text = self.extract_text_from_file(file_path, filename)
            
            if not text or len(text.strip()) == 0:
                raise ValueError("هیچ متنی از فایل استخراج نشد")
            
            # تقسیم به قطعات
            chunks = self.chunk_text(text)
            
            # آماده‌سازی metadata
            file_metadata = {
                'filename': filename,
                'file_type': filename.split('.')[-1].lower(),
                'total_chunks': len(chunks),
                'total_characters': len(text),
                **(metadata or {})
            }
            
            result = {
                'text': text,
                'chunks': chunks,
                'metadata': file_metadata
            }
            
            logger.info(f"File processed successfully: {filename}, {len(chunks)} chunks, {len(text)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise
