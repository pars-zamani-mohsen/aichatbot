"""
سرویس نظارت بر عملکرد سیستم
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from functools import wraps
import psutil
import threading
from collections import defaultdict, deque

from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """نظارت بر عملکرد سیستم"""
    
    def __init__(self):
        self.metrics = defaultdict(deque)
        self.max_metrics = 1000  # حداکثر تعداد metrics نگهداری شده
        self.lock = threading.Lock()
        
        # ایجاد metrics اولیه
        self._initialize_default_metrics()
        
        # شروع background monitoring
        self._start_background_monitoring()
    
    def _initialize_default_metrics(self):
        """ایجاد metrics اولیه برای تست"""
        try:
            # ایجاد یک metric سیستم اولیه
            initial_system_metric = {
                'timestamp': datetime.now(),
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'disk_percent': 0.0,
                'memory_available_gb': 0.0,
                'disk_free_gb': 0.0,
                'network_bytes_sent': 0,
                'network_bytes_recv': 0,
                'process_count': 0
            }
            
            # ایجاد یک metric دیتابیس اولیه
            initial_db_metric = {
                'timestamp': datetime.now(),
                'query_name': 'initialization',
                'execution_time': 0.001,
                'success': True,
                'rows_affected': 0
            }
            
            # ایجاد یک metric API اولیه
            initial_api_metric = {
                'timestamp': datetime.now(),
                'endpoint': 'initialization',
                'method': 'GET',
                'response_time': 0.001,
                'status_code': 200,
                'user_id': None
            }
            
            # ایجاد یک metric cache اولیه
            initial_cache_metric = {
                'timestamp': datetime.now(),
                'operation': 'initialization',
                'key': 'initial',
                'success': True,
                'response_time': 0.001
            }
            
            # اضافه کردن metrics اولیه
            self._add_metric('system', initial_system_metric)
            self._add_metric('database_queries', initial_db_metric)
            self._add_metric('api_calls', initial_api_metric)
            self._add_metric('cache_operations', initial_cache_metric)
            
            logger.info("Default metrics initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing default metrics: {e}")
    
    def _start_background_monitoring(self):
        """شروع نظارت background"""
        def monitor_loop():
            while True:
                try:
                    self._collect_system_metrics()
                    time.sleep(60)  # هر دقیقه
                except Exception as e:
                    logger.error(f"Error in performance monitoring: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def _collect_system_metrics(self):
        """جمع‌آوری آمار سیستم"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            metrics = {
                'timestamp': datetime.now(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'process_count': process_count
            }
            
            self._add_metric('system', metrics)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _add_metric(self, category: str, metric: Dict[str, Any]):
        """اضافه کردن metric جدید"""
        with self.lock:
            if category not in self.metrics:
                self.metrics[category] = deque(maxlen=self.max_metrics)
            
            self.metrics[category].append(metric)
    
    def add_query_metric(self, query_name: str, execution_time: float, 
                         success: bool, rows_affected: Optional[int] = None):
        """اضافه کردن metric برای query دیتابیس"""
        metric = {
            'timestamp': datetime.now(),
            'query_name': query_name,
            'execution_time': execution_time,
            'success': success,
            'rows_affected': rows_affected
        }
        
        self._add_metric('database_queries', metric)
    
    def add_api_metric(self, endpoint: str, method: str, response_time: float, 
                       status_code: int, user_id: Optional[int] = None):
        """اضافه کردن metric برای API calls"""
        metric = {
            'timestamp': datetime.now(),
            'endpoint': endpoint,
            'method': method,
            'response_time': response_time,
            'status_code': status_code,
            'user_id': user_id
        }
        
        self._add_metric('api_calls', metric)
    
    def add_cache_metric(self, operation: str, key: str, success: bool, 
                         response_time: float):
        """اضافه کردن metric برای cache operations"""
        metric = {
            'timestamp': datetime.now(),
            'operation': operation,
            'key': key,
            'success': success,
            'response_time': response_time
        }
        
        self._add_metric('cache_operations', metric)
    
    def get_metrics_summary(self, category: str, hours: int = 24) -> Dict[str, Any]:
        """دریافت خلاصه metrics"""
        with self.lock:
            if category not in self.metrics:
                return {}
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [
                m for m in self.metrics[category] 
                if m['timestamp'] > cutoff_time
            ]
            
            if not recent_metrics:
                return {}
            
            # محاسبه آمار
            if category == 'system':
                return self._calculate_system_summary(recent_metrics)
            elif category == 'database_queries':
                return self._calculate_database_summary(recent_metrics)
            elif category == 'api_calls':
                return self._calculate_api_summary(recent_metrics)
            elif category == 'cache_operations':
                return self._calculate_cache_summary(recent_metrics)
            
            return {}
    
    def _calculate_system_summary(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """محاسبه خلاصه آمار سیستم"""
        cpu_values = [m['cpu_percent'] for m in metrics]
        memory_values = [m['memory_percent'] for m in metrics]
        disk_values = [m['disk_percent'] for m in metrics]
        
        return {
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'avg': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'disk': {
                'avg': sum(disk_values) / len(disk_values),
                'max': max(disk_values),
                'min': min(disk_values)
            },
            'sample_count': len(metrics)
        }
    
    def _calculate_database_summary(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """محاسبه خلاصه آمار دیتابیس"""
        execution_times = [m['execution_time'] for m in metrics]
        success_count = sum(1 for m in metrics if m['success'])
        
        return {
            'total_queries': len(metrics),
            'successful_queries': success_count,
            'failed_queries': len(metrics) - success_count,
            'success_rate': success_count / len(metrics) * 100,
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'max_execution_time': max(execution_times),
            'min_execution_time': min(execution_times)
        }
    
    def _calculate_api_summary(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """محاسبه خلاصه آمار API"""
        response_times = [m['response_time'] for m in metrics]
        status_codes = [m['status_code'] for m in metrics]
        
        # گروه‌بندی بر اساس endpoint
        endpoints = defaultdict(list)
        for metric in metrics:
            endpoints[metric['endpoint']].append(metric)
        
        endpoint_stats = {}
        for endpoint, endpoint_metrics in endpoints.items():
            endpoint_response_times = [m['response_time'] for m in endpoint_metrics]
            endpoint_status_codes = [m['status_code'] for m in endpoint_metrics]
            
            endpoint_stats[endpoint] = {
                'call_count': len(endpoint_metrics),
                'avg_response_time': sum(endpoint_response_times) / len(endpoint_response_times),
                'success_rate': sum(1 for s in endpoint_status_codes if s < 400) / len(endpoint_status_codes) * 100
            }
        
        return {
            'total_calls': len(metrics),
            'avg_response_time': sum(response_times) / len(response_times),
            'max_response_time': max(response_times),
            'min_response_time': min(response_times),
            'endpoints': endpoint_stats
        }
    
    def _calculate_cache_summary(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """محاسبه خلاصه آمار cache"""
        success_count = sum(1 for m in metrics if m['success'])
        response_times = [m['response_time'] for m in metrics]
        
        # گروه‌بندی بر اساس operation
        operations = defaultdict(list)
        for metric in metrics:
            operations[metric['operation']].append(metric)
        
        operation_stats = {}
        for operation, operation_metrics in operations.items():
            operation_response_times = [m['response_time'] for m in operation_metrics]
            operation_success_count = sum(1 for m in operation_metrics if m['success'])
            
            operation_stats[operation] = {
                'count': len(operation_metrics),
                'success_count': operation_success_count,
                'success_rate': operation_success_count / len(operation_metrics) * 100,
                'avg_response_time': sum(operation_response_times) / len(operation_response_times)
            }
        
        return {
            'total_operations': len(metrics),
            'successful_operations': success_count,
            'failed_operations': len(metrics) - success_count,
            'success_rate': success_count / len(metrics) * 100,
            'avg_response_time': sum(response_times) / len(response_times),
            'operations': operation_stats
        }
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """دریافت هشدارهای عملکرد"""
        alerts = []
        
        try:
            # بررسی آمار سیستم
            system_summary = self.get_metrics_summary('system', hours=1)
            if system_summary and isinstance(system_summary, dict) and 'cpu' in system_summary:
                try:
                    cpu_avg = system_summary.get('cpu', {}).get('avg', 0)
                    memory_avg = system_summary.get('memory', {}).get('avg', 0)
                    disk_avg = system_summary.get('disk', {}).get('avg', 0)
                    
                    if cpu_avg > 80:
                        alerts.append({
                            'type': 'high_cpu',
                            'severity': 'warning',
                            'message': f'CPU usage is high: {cpu_avg:.1f}%',
                            'timestamp': datetime.now()
                        })
                    
                    if memory_avg > 85:
                        alerts.append({
                            'type': 'high_memory',
                            'severity': 'warning',
                            'message': f'Memory usage is high: {memory_avg:.1f}%',
                            'timestamp': datetime.now()
                        })
                    
                    if disk_avg > 90:
                        alerts.append({
                            'type': 'high_disk',
                            'severity': 'critical',
                            'message': f'Disk usage is critical: {disk_avg:.1f}%',
                            'timestamp': datetime.now()
                        })
                except (KeyError, TypeError, AttributeError) as e:
                    logger.warning(f"Error processing system metrics: {e}")
            
            # بررسی آمار دیتابیس
            db_summary = self.get_metrics_summary('database_queries', hours=1)
            if db_summary and isinstance(db_summary, dict) and db_summary.get('total_queries', 0) > 0:
                try:
                    success_rate = db_summary.get('success_rate', 100)
                    avg_execution_time = db_summary.get('avg_execution_time', 0)
                    
                    if success_rate < 95:
                        alerts.append({
                            'type': 'low_db_success_rate',
                            'severity': 'warning',
                            'message': f'Database success rate is low: {success_rate:.1f}%',
                            'timestamp': datetime.now()
                        })
                    
                    if avg_execution_time > 1.0:  # بیش از 1 ثانیه
                        alerts.append({
                            'type': 'slow_db_queries',
                            'severity': 'warning',
                            'message': f'Database queries are slow: {avg_execution_time:.2f}s avg',
                            'timestamp': datetime.now()
                        })
                except (KeyError, TypeError, AttributeError) as e:
                    logger.warning(f"Error processing database metrics: {e}")
            
            # بررسی آمار API
            api_summary = self.get_metrics_summary('api_calls', hours=1)
            if api_summary and isinstance(api_summary, dict) and api_summary.get('total_calls', 0) > 0:
                try:
                    avg_response_time = api_summary.get('avg_response_time', 0)
                    
                    if avg_response_time > 2.0:  # بیش از 2 ثانیه
                        alerts.append({
                            'type': 'slow_api_responses',
                            'severity': 'warning',
                            'message': f'API responses are slow: {avg_response_time:.2f}s avg',
                            'timestamp': datetime.now()
                        })
                except (KeyError, TypeError, AttributeError) as e:
                    logger.warning(f"Error processing API metrics: {e}")
                    
        except Exception as e:
            logger.error(f"Error in get_performance_alerts: {e}")
            # در صورت خطا، یک هشدار عمومی برگردان
            alerts.append({
                'type': 'system_error',
                'severity': 'warning',
                'message': 'خطا در دریافت هشدارهای عملکرد',
                'timestamp': datetime.now()
            })
        
        return alerts
    
    def clear_old_metrics(self, days: int = 7):
        """پاکسازی metrics قدیمی"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self.lock:
            for category in self.metrics:
                # حذف metrics قدیمی
                self.metrics[category] = deque(
                    [m for m in self.metrics[category] if m['timestamp'] > cutoff_time],
                    maxlen=self.max_metrics
                )
        
        logger.info(f"Cleared metrics older than {days} days")


# Decorator برای نظارت بر عملکرد
def monitor_performance(category: str, operation: str = None):
    """Decorator برای نظارت بر عملکرد توابع"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            rows_affected = None
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise
            finally:
                execution_time = time.time() - start_time
                
                if category == 'database':
                    performance_monitor.add_query_metric(
                        operation or func.__name__,
                        execution_time,
                        success,
                        rows_affected
                    )
                elif category == 'api':
                    performance_monitor.add_api_metric(
                        operation or func.__name__,
                        'GET',  # یا از context دریافت شود
                        execution_time,
                        200 if success else 500
                    )
                elif category == 'cache':
                    performance_monitor.add_cache_metric(
                        operation or func.__name__,
                        'unknown',
                        success,
                        execution_time
                    )
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                logger.error(f"Error in async {func.__name__}: {e}")
                raise
            finally:
                execution_time = time.time() - start_time
                
                if category == 'database':
                    performance_monitor.add_query_metric(
                        operation or func.__name__,
                        execution_time,
                        success
                    )
                elif category == 'api':
                    performance_monitor.add_api_metric(
                        operation or func.__name__,
                        'GET',
                        execution_time,
                        200 if success else 500
                    )
        
        # برگرداندن wrapper مناسب
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


# Instance سراسری
performance_monitor = PerformanceMonitor()

# توابع کمکی
add_query_metric = performance_monitor.add_query_metric
add_api_metric = performance_monitor.add_api_metric
add_cache_metric = performance_monitor.add_cache_metric
get_metrics_summary = performance_monitor.get_metrics_summary
get_performance_alerts = performance_monitor.get_performance_alerts
clear_old_metrics = performance_monitor.clear_old_metrics
