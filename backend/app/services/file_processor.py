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
        self.max_file_size = self._parse_file_size(settings.MAX_FILE_SIZE)
    
    def _parse_file_size(self, size_str: str) -> int:
        """تبدیل string اندازه فایل به bytes"""
        try:
            size_str = size_str.upper().strip()
            
            if size_str.endswith('KB'):
                return int(float(size_str[:-2]) * 1024)
            elif size_str.endswith('MB'):
                return int(float(size_str[:-2]) * 1024 * 1024)
            elif size_str.endswith('GB'):
                return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
            else:
                return int(size_str)
        except (ValueError, AttributeError):
            return 50 * 1024 * 1024
        
    def validate_file(self, file_path: str, filename: str) -> bool:
        """اعتبارسنجی فایل"""
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error(f"File size {file_size} exceeds maximum {self.max_file_size}")
                return False
            
            file_ext = filename.split('.')[-1].lower()
            if file_ext not in self.allowed_extensions:
                logger.error(f"File extension {file_ext} not allowed")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return False
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """استخراج متن از فایل PDF"""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """استخراج متن از فایل DOCX"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """استخراج متن از فایل TXT"""
        try:
            encodings = ['utf-8', 'utf-8-sig', 'cp1256', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        text = file.read()
                    return text.strip()
                except UnicodeDecodeError:
                    continue
            return ""
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            raise
    
    def extract_text_from_file(self, file_path: str, filename: str) -> str:
        """استخراج متن از فایل بر اساس نوع آن"""
        try:
            if not self.validate_file(file_path, filename):
                raise ValueError("فایل معتبر نیست")
            
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
            
            text = text.strip()
            if len(text) <= chunk_size:
                return [text]
            
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + chunk_size
                if end >= len(text):
                    chunks.append(text[start:])
                    break
                
                chunk = text[start:end]
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
                
                if start >= len(text):
                    break
            
            return [chunk for chunk in chunks if chunk.strip()]
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise
    
    def process_file(self, file_path: str, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """پردازش کامل فایل و استخراج متن"""
        try:
            text = self.extract_text_from_file(file_path, filename)
            
            if not text or len(text.strip()) == 0:
                raise ValueError("هیچ متنی از فایل استخراج نشد")
            
            chunks = self.chunk_text(text)
            
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