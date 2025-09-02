import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import threading
from queue import Queue, Empty
from app.database.database import SessionLocal
from app.database.models import Website
from app.services.pipeline import WebCrawlerPipeline, EmbeddingPipeline
import time

logger = logging.getLogger(__name__)

class CrawlStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class CrawlTask:
    website_id: int
    url: str
    domain: str
    owner_id: int
    priority: int = 1  # 1=normal, 2=high, 3=urgent
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    status: CrawlStatus = CrawlStatus.PENDING
    error_message: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class CrawlerQueue:
    """مدیریت صف کراولینگ برای جلوگیری از همزمانی بیش از حد"""
    
    def __init__(self, max_concurrent_crawls: int = 3):
        self.max_concurrent_crawls = max_concurrent_crawls
        self.queue = Queue()
        self.active_crawls: Dict[int, CrawlTask] = {}
        self.completed_crawls: List[CrawlTask] = []
        self.lock = threading.Lock()
        self.running = False
        self.worker_thread = None
        
        # آمار
        self.stats = {
            "total_crawls": 0,
            "successful_crawls": 0,
            "failed_crawls": 0,
            "average_duration": 0
        }
    
    def start(self):
        """شروع worker thread"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("Crawler queue worker started")
    
    def stop(self):
        """توقف worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
            logger.info("Crawler queue worker stopped")
    
    def add_crawl_task(self, website_id: int, url: str, domain: str, owner_id: int, priority: int = 1) -> CrawlTask:
        """اضافه کردن وظیفه کراولینگ به صف"""
        task = CrawlTask(
            website_id=website_id,
            url=url,
            domain=domain,
            owner_id=owner_id,
            priority=priority
        )
        
        with self.lock:
            self.queue.put((priority, task))
            self.stats["total_crawls"] += 1
            logger.info(f"Added crawl task for {domain} (priority: {priority})")
        
        return task
    
    def _worker_loop(self):
        """حلقه اصلی worker"""
        while self.running:
            try:
                # بررسی محدودیت همزمانی
                if len(self.active_crawls) >= self.max_concurrent_crawls:
                    time.sleep(1)
                    continue
                
                # دریافت وظیفه از صف
                try:
                    priority, task = self.queue.get(timeout=1)
                except Empty:
                    continue
                
                # شروع کراولینگ
                self._start_crawl(task)
                
            except Exception as e:
                logger.error(f"Error in crawler worker: {e}")
                time.sleep(1)
    
    def _start_crawl(self, task: CrawlTask):
        """شروع کراولینگ"""
        with self.lock:
            task.status = CrawlStatus.RUNNING
            task.started_at = datetime.now()
            self.active_crawls[task.website_id] = task
        
        logger.info(f"Starting crawl for {task.domain}")
        
        # اجرای کراولینگ در thread جداگانه
        thread = threading.Thread(target=self._execute_crawl, args=(task,), daemon=True)
        thread.start()
    
    def _execute_crawl(self, task: CrawlTask):
        """اجرای کراولینگ"""
        db = SessionLocal()
        try:
            # به‌روزرسانی وضعیت وب‌سایت
            website = db.query(Website).filter(Website.id == task.website_id).first()
            if not website:
                raise Exception("Website not found")
            
            website.status = "crawling"
            db.commit()
            
            # اجرای کراولینگ
            crawler = WebCrawlerPipeline(task.url, {
                'max_pages': 100,
                'delay': 1,
                'respect_robots': True
            })
            
            if not crawler.run_async():
                raise Exception("Crawling failed")
            
            # اجرای امبدینگ
            embedder = EmbeddingPipeline(task.domain)
            if not embedder.run():
                raise Exception("Embedding failed")
            
            # تکمیل موفق
            website.status = "ready"
            website.crawl_info = {
                'total_pages': len(crawler.data),
                'crawled_at': datetime.now().isoformat()
            }
            db.commit()
            
            self._complete_crawl(task, CrawlStatus.COMPLETED)
            self.stats["successful_crawls"] += 1
            
        except Exception as e:
            logger.error(f"Crawl failed for {task.domain}: {e}")
            
            # به‌روزرسانی وضعیت خطا
            website = db.query(Website).filter(Website.id == task.website_id).first()
            if website:
                website.status = "error"
                website.error_message = str(e)
                db.commit()
            
            task.error_message = str(e)
            self._complete_crawl(task, CrawlStatus.FAILED)
            self.stats["failed_crawls"] += 1
            
        finally:
            db.close()
    
    def _complete_crawl(self, task: CrawlTask, status: CrawlStatus):
        """تکمیل کراولینگ"""
        with self.lock:
            task.status = status
            task.completed_at = datetime.now()
            
            if task.website_id in self.active_crawls:
                del self.active_crawls[task.website_id]
            
            self.completed_crawls.append(task)
            
            # محاسبه آمار
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                self.stats["average_duration"] = (
                    (self.stats["average_duration"] * (self.stats["successful_crawls"] - 1) + duration) / 
                    self.stats["successful_crawls"]
                )
        
        logger.info(f"Crawl {status.value} for {task.domain}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """دریافت وضعیت صف"""
        with self.lock:
            return {
                "queue_size": self.queue.qsize(),
                "active_crawls": len(self.active_crawls),
                "max_concurrent": self.max_concurrent_crawls,
                "stats": self.stats.copy(),
                "active_tasks": [
                    {
                        "website_id": task.website_id,
                        "domain": task.domain,
                        "started_at": task.started_at.isoformat() if task.started_at else None,
                        "duration": (datetime.now() - task.started_at).total_seconds() if task.started_at else 0
                    }
                    for task in self.active_crawls.values()
                ]
            }
    
    def cancel_crawl(self, website_id: int) -> bool:
        """لغو کراولینگ"""
        with self.lock:
            if website_id in self.active_crawls:
                task = self.active_crawls[website_id]
                task.status = CrawlStatus.CANCELLED
                del self.active_crawls[website_id]
                logger.info(f"Crawl cancelled for website {website_id}")
                return True
        return False

# Instance سراسری
crawler_queue = CrawlerQueue(max_concurrent_crawls=3)
