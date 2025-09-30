"""
Memory and Resource Management Module
Handles memory optimization, resource monitoring, and system scalability
"""

import os
import gc
import psutil
import threading
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps

class MemoryManager:
    """Memory usage monitoring and optimization"""
    
    def __init__(self, warning_threshold: float = 80.0, critical_threshold: float = 90.0):
        self.warning_threshold = warning_threshold  # Memory usage percentage
        self.critical_threshold = critical_threshold
        self.monitoring = False
        self.monitor_thread = None
        self.stats = {
            'peak_memory_mb': 0,
            'current_memory_mb': 0,
            'gc_collections': 0,
            'memory_warnings': 0,
            'last_cleanup': None
        }
        
    def start_monitoring(self, interval: int = 60):
        """Start memory monitoring thread"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logging.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logging.info("Memory monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Memory monitoring loop"""
        while self.monitoring:
            try:
                self._check_memory_usage()
                time.sleep(interval)
            except Exception as e:
                logging.error(f"Memory monitoring error: {e}")
    
    def _check_memory_usage(self):
        """Check current memory usage and take action if needed"""
        try:
            # Process memory
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # System memory
            system_memory = psutil.virtual_memory()
            memory_percent = system_memory.percent
            
            # Update stats
            self.stats['current_memory_mb'] = memory_mb
            if memory_mb > self.stats['peak_memory_mb']:
                self.stats['peak_memory_mb'] = memory_mb
            
            # Check thresholds
            if memory_percent >= self.critical_threshold:
                logging.warning(f"Critical memory usage: {memory_percent:.1f}%")
                self._emergency_cleanup()
                self.stats['memory_warnings'] += 1
                
            elif memory_percent >= self.warning_threshold:
                logging.info(f"High memory usage: {memory_percent:.1f}%")
                self._gentle_cleanup()
                self.stats['memory_warnings'] += 1
                
        except Exception as e:
            logging.error(f"Memory check failed: {e}")
    
    def _gentle_cleanup(self):
        """Gentle memory cleanup"""
        # Force garbage collection
        collected = gc.collect()
        self.stats['gc_collections'] += 1
        self.stats['last_cleanup'] = datetime.now()
        
        logging.info(f"Gentle cleanup: {collected} objects collected")
    
    def _emergency_cleanup(self):
        """Emergency memory cleanup"""
        # Force full garbage collection
        for generation in range(3):
            collected = gc.collect(generation)
            
        self.stats['gc_collections'] += 1
        self.stats['last_cleanup'] = datetime.now()
        
        # Clear caches if available
        try:
            from faiss_optimizer import faiss_optimizer
            faiss_optimizer.clear_cache()
            logging.info("FAISS cache cleared for memory")
        except Exception:
            pass
        
        logging.warning("Emergency cleanup performed")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()
            
            return {
                'process_memory_mb': round(memory_info.rss / 1024 / 1024, 2),
                'system_memory_percent': round(system_memory.percent, 2),
                'system_memory_available_gb': round(system_memory.available / 1024 / 1024 / 1024, 2),
                'peak_memory_mb': self.stats['peak_memory_mb'],
                'gc_collections': self.stats['gc_collections'],
                'memory_warnings': self.stats['memory_warnings'],
                'last_cleanup': self.stats['last_cleanup'].isoformat() if self.stats['last_cleanup'] else None
            }
        except Exception as e:
            logging.error(f"Memory stats error: {e}")
            return {}

class ResourceManager:
    """System resource monitoring and management"""
    
    def __init__(self):
        self.monitoring = False
        self.stats = {
            'cpu_usage_history': [],
            'disk_usage_gb': 0,
            'network_io': {},
            'open_files': 0,
            'active_connections': 0
        }
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get comprehensive system resource information"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('.')
            
            # Network (if available)
            network_io = psutil.net_io_counters()
            
            # Process info
            process = psutil.Process()
            open_files = len(process.open_files())
            connections = len(process.connections())
            
            return {
                'cpu': {
                    'usage_percent': round(cpu_percent, 2),
                    'core_count': cpu_count,
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                },
                'memory': {
                    'total_gb': round(memory.total / 1024 / 1024 / 1024, 2),
                    'available_gb': round(memory.available / 1024 / 1024 / 1024, 2),
                    'usage_percent': round(memory.percent, 2)
                },
                'disk': {
                    'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
                    'used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
                    'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                    'usage_percent': round((disk.used / disk.total) * 100, 2)
                },
                'network': {
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv
                },
                'process': {
                    'open_files': open_files,
                    'connections': connections,
                    'threads': threading.active_count()
                }
            }
            
        except Exception as e:
            logging.error(f"Resource monitoring error: {e}")
            return {}
    
    def check_resource_limits(self) -> Dict[str, Any]:
        """Check if system resources are within safe limits"""
        resources = self.get_system_resources()
        
        warnings = []
        status = "healthy"
        
        # Check CPU
        if resources.get('cpu', {}).get('usage_percent', 0) > 80:
            warnings.append("High CPU usage")
            status = "warning"
            
        # Check memory
        if resources.get('memory', {}).get('usage_percent', 0) > 85:
            warnings.append("High memory usage")
            status = "critical" if status != "critical" else status
            
        # Check disk space
        if resources.get('disk', {}).get('usage_percent', 0) > 90:
            warnings.append("Low disk space")
            status = "critical"
        
        return {
            'status': status,
            'warnings': warnings,
            'resources': resources
        }

class FileManager:
    """File handling optimization and management"""
    
    def __init__(self, max_file_size_mb: int = 50, chunk_size: int = 8192):
        self.max_file_size_mb = max_file_size_mb
        self.chunk_size = chunk_size
        
    def safe_file_read(self, file_path: str, max_size_mb: Optional[int] = None) -> str:
        """Safely read file with size limits"""
        max_size = (max_size_mb or self.max_file_size_mb) * 1024 * 1024
        
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size > max_size:
                logging.warning(f"File too large: {file_size / 1024 / 1024:.1f}MB > {max_size_mb}MB")
                # Read only first part of file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(max_size)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        except Exception as e:
            logging.error(f"File read error: {e}")
            return ""
    
    def chunked_file_processor(self, file_path: str, processor_func):
        """Process large files in chunks to avoid memory issues"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    processor_func(chunk)
                    
                    # Allow garbage collection
                    if threading.active_count() > 10:  # If many threads active
                        time.sleep(0.001)  # Small pause
                        
        except Exception as e:
            logging.error(f"Chunked processing error: {e}")
    
    def cleanup_temp_files(self, temp_dir: str = './temp', max_age_hours: int = 24):
        """Clean up old temporary files"""
        if not os.path.exists(temp_dir):
            return 0
        
        cleaned_count = 0
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        try:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                        
            logging.info(f"Cleaned up {cleaned_count} temporary files")
            return cleaned_count
            
        except Exception as e:
            logging.error(f"Temp file cleanup error: {e}")
            return 0

# Decorators for performance monitoring
def monitor_memory_usage(func):
    """Decorator to monitor memory usage of functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get memory before
        process = psutil.Process()
        mem_before = process.memory_info().rss
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Get memory after
            mem_after = process.memory_info().rss
            mem_diff = (mem_after - mem_before) / 1024 / 1024  # MB
            
            if mem_diff > 10:  # Log if more than 10MB difference
                logging.info(f"Function {func.__name__} memory usage: {mem_diff:.1f}MB")
    
    return wrapper

def cache_with_ttl(ttl_seconds: int = 300):
    """Decorator for caching with TTL"""
    def decorator(func):
        cache = {}
        cache_times = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # Check if cached and not expired
            if key in cache and (current_time - cache_times[key]) < ttl_seconds:
                return cache[key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[key] = result
            cache_times[key] = current_time
            
            # Clean old cache entries
            expired_keys = [k for k, t in cache_times.items() if (current_time - t) >= ttl_seconds]
            for k in expired_keys:
                cache.pop(k, None)
                cache_times.pop(k, None)
            
            return result
        
        return wrapper
    return decorator

# Global instances
memory_manager = MemoryManager()
resource_manager = ResourceManager()
file_manager = FileManager()

# Utility functions
def optimize_system_performance():
    """Run system optimization tasks"""
    logging.info("Starting system optimization...")
    
    # Force garbage collection
    collected = gc.collect()
    logging.info(f"Garbage collection: {collected} objects collected")
    
    # Clean temp files
    cleaned_files = file_manager.cleanup_temp_files()
    logging.info(f"Temp file cleanup: {cleaned_files} files removed")
    
    # Clear caches if memory usage is high
    try:
        resources = resource_manager.get_system_resources()
        if resources.get('memory', {}).get('usage_percent', 0) > 75:
            from faiss_optimizer import faiss_optimizer
            faiss_optimizer.clear_cache()
            logging.info("High memory usage detected, caches cleared")
    except Exception:
        pass
    
    logging.info("System optimization completed")

def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health report"""
    return {
        'memory': memory_manager.get_memory_stats(),
        'resources': resource_manager.check_resource_limits(),
        'timestamp': datetime.now().isoformat()
    }

# Auto-start memory monitoring
memory_manager.start_monitoring()