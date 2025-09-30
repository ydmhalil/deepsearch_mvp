"""
Enterprise Database Optimization
Advanced database performance tuning for large organizations
"""

import sqlite3
import threading
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging
from contextlib import contextmanager
import queue
import weakref
from datetime import datetime, timedelta

@dataclass
class QueryPerformanceMetrics:
    """Track query performance metrics"""
    query: str
    execution_time: float
    rows_affected: int
    timestamp: datetime
    table_name: str
    operation_type: str
    
class EnterpriseDatabase:
    """Enterprise-grade database manager with connection pooling and optimization"""
    
    def __init__(self, db_path: str, config: Dict[str, Any]):
        self.db_path = db_path
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Connection pool
        self.pool_size = config.get('connection_pool_size', 50)
        self.max_overflow = config.get('max_overflow', 100)
        self.pool_timeout = config.get('pool_timeout', 30)
        self.pool_recycle = config.get('pool_recycle', 3600)
        
        # Initialize connection pool
        self.connection_pool = queue.Queue(maxsize=self.pool_size + self.max_overflow)
        self.pool_lock = threading.RLock()
        self.active_connections = weakref.WeakSet()
        
        # Performance monitoring
        self.query_metrics = []
        self.metrics_lock = threading.RLock()
        
        # Query cache
        self.enable_query_cache = config.get('enable_query_cache', True)
        self.query_cache = {}
        self.cache_size = config.get('query_cache_size', 1000)
        self.cache_lock = threading.RLock()
        
        # Initialize database optimizations
        self._initialize_database()
        self._fill_connection_pool()
        
        # Start maintenance thread
        self.maintenance_thread = threading.Thread(target=self._maintenance_worker, daemon=True)
        self.maintenance_thread.start()
    
    def _initialize_database(self):
        """Initialize database with enterprise optimizations"""
        try:
            with self._get_raw_connection() as conn:
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode = WAL")
                
                # Optimize SQLite settings for performance
                conn.execute("PRAGMA synchronous = NORMAL")  # Balance between speed and safety
                conn.execute("PRAGMA cache_size = -64000")   # 64MB cache
                conn.execute("PRAGMA temp_store = MEMORY")   # Use memory for temp tables
                conn.execute("PRAGMA mmap_size = 268435456") # 256MB memory map
                
                # Enable query optimization
                conn.execute("PRAGMA optimize")
                
                # Set busy timeout for concurrent access
                conn.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
                
                # Auto vacuum for maintenance
                if self.config.get('auto_vacuum', 'incremental') == 'incremental':
                    conn.execute("PRAGMA auto_vacuum = INCREMENTAL")
                
                self.logger.info("Database optimizations applied successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database optimizations: {e}")
            raise
    
    def _fill_connection_pool(self):
        """Fill the connection pool with initial connections"""
        for _ in range(self.pool_size):
            try:
                conn = self._create_connection()
                self.connection_pool.put(conn, block=False)
            except queue.Full:
                break
            except Exception as e:
                self.logger.error(f"Failed to create pooled connection: {e}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimizations"""
        conn = sqlite3.Connection(
            self.db_path,
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None  # Autocommit mode
        )
        
        # Enable row factory for better data access
        conn.row_factory = sqlite3.Row
        
        # Apply per-connection optimizations
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -8000")  # 8MB per connection
        conn.execute("PRAGMA temp_store = MEMORY")
        
        return conn
    
    def _get_raw_connection(self) -> sqlite3.Connection:
        """Get a raw connection without pooling (for initialization)"""
        return sqlite3.connect(self.db_path, timeout=30.0)
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        start_time = time.time()
        
        try:
            # Try to get connection from pool
            try:
                conn = self.connection_pool.get(timeout=self.pool_timeout)
            except queue.Empty:
                # Create new connection if pool is empty and under max
                with self.pool_lock:
                    if len(self.active_connections) < self.pool_size + self.max_overflow:
                        conn = self._create_connection()
                    else:
                        # Wait longer for a connection
                        conn = self.connection_pool.get(timeout=self.pool_timeout * 2)
            
            # Check if connection is still valid
            if conn and self._is_connection_valid(conn):
                self.active_connections.add(conn)
                yield conn
            else:
                # Create new connection if invalid
                conn = self._create_connection()
                self.active_connections.add(conn)
                yield conn
                
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            raise
        finally:
            # Return connection to pool
            if conn:
                try:
                    self.active_connections.discard(conn)
                    if self._is_connection_valid(conn):
                        self.connection_pool.put(conn, block=False)
                    else:
                        conn.close()
                except (queue.Full, Exception):
                    # Close connection if pool is full or error occurred
                    conn.close()
    
    def _is_connection_valid(self, conn: sqlite3.Connection) -> bool:
        """Check if connection is still valid"""
        try:
            conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, 
                     cache_key: Optional[str] = None) -> List[sqlite3.Row]:
        """Execute a SELECT query with caching and performance monitoring"""
        start_time = time.time()
        
        # Check cache first
        if cache_key and self.enable_query_cache:
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params or ())
                results = cursor.fetchall()
                
                # Cache results if requested
                if cache_key and self.enable_query_cache:
                    self._cache_result(cache_key, results)
                
                # Record performance metrics
                execution_time = time.time() - start_time
                self._record_query_metrics(query, execution_time, len(results), 'SELECT')
                
                return results
                
        except Exception as e:
            self.logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
            raise
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params or ())
                rows_affected = cursor.rowcount
                
                # Record performance metrics
                execution_time = time.time() - start_time
                operation_type = query.strip().split()[0].upper()
                self._record_query_metrics(query, execution_time, rows_affected, operation_type)
                
                return rows_affected
                
        except Exception as e:
            self.logger.error(f"Update execution failed: {query[:100]}... Error: {e}")
            raise
    
    def execute_batch(self, query: str, params_list: List[Tuple]) -> int:
        """Execute a batch of queries for better performance"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.executemany(query, params_list)
                rows_affected = cursor.rowcount
                
                # Record performance metrics
                execution_time = time.time() - start_time
                operation_type = query.strip().split()[0].upper()
                self._record_query_metrics(query, execution_time, rows_affected, f'BATCH_{operation_type}')
                
                return rows_affected
                
        except Exception as e:
            self.logger.error(f"Batch execution failed: {query[:100]}... Error: {e}")
            raise
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[sqlite3.Row]]:
        """Get cached query result"""
        with self.cache_lock:
            if cache_key in self.query_cache:
                cached_data = self.query_cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < timedelta(hours=1):
                    return cached_data['result']
                else:
                    # Remove expired cache
                    del self.query_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: List[sqlite3.Row]):
        """Cache query result"""
        with self.cache_lock:
            # Limit cache size
            if len(self.query_cache) >= self.cache_size:
                # Remove oldest cache entry
                oldest_key = min(self.query_cache.keys(), 
                               key=lambda k: self.query_cache[k]['timestamp'])
                del self.query_cache[oldest_key]
            
            self.query_cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now()
            }
    
    def _record_query_metrics(self, query: str, execution_time: float, 
                            rows_affected: int, operation_type: str):
        """Record query performance metrics"""
        with self.metrics_lock:
            # Extract table name from query
            table_name = self._extract_table_name(query)
            
            metric = QueryPerformanceMetrics(
                query=query[:200],  # Truncate long queries
                execution_time=execution_time,
                rows_affected=rows_affected,
                timestamp=datetime.now(),
                table_name=table_name,
                operation_type=operation_type
            )
            
            self.query_metrics.append(metric)
            
            # Keep only recent metrics (last 10000)
            if len(self.query_metrics) > 10000:
                self.query_metrics = self.query_metrics[-5000:]
    
    def _extract_table_name(self, query: str) -> str:
        """Extract table name from SQL query"""
        try:
            query_upper = query.upper().strip()
            if query_upper.startswith('SELECT'):
                # Extract from FROM clause
                from_index = query_upper.find('FROM')
                if from_index != -1:
                    after_from = query[from_index + 4:].strip().split()[0]
                    return after_from.strip('`"[]')
            elif any(query_upper.startswith(op) for op in ['INSERT', 'UPDATE', 'DELETE']):
                # Extract table name after operation
                words = query.split()
                if len(words) >= 3:
                    return words[2].strip('`"[]')
        except Exception:
            pass
        return 'unknown'
    
    def _maintenance_worker(self):
        """Background worker for database maintenance"""
        while True:
            try:
                time.sleep(3600)  # Run every hour
                
                # Clean expired cache entries
                self._cleanup_cache()
                
                # Optimize database
                self._optimize_database()
                
                # Clean up old connections
                self._cleanup_connections()
                
            except Exception as e:
                self.logger.error(f"Maintenance worker error: {e}")
    
    def _cleanup_cache(self):
        """Clean up expired cache entries"""
        with self.cache_lock:
            current_time = datetime.now()
            expired_keys = [
                key for key, data in self.query_cache.items()
                if current_time - data['timestamp'] > timedelta(hours=1)
            ]
            for key in expired_keys:
                del self.query_cache[key]
            
            if expired_keys:
                self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _optimize_database(self):
        """Run database optimization"""
        try:
            with self._get_raw_connection() as conn:
                # Run PRAGMA optimize
                conn.execute("PRAGMA optimize")
                
                # Run incremental vacuum if configured
                if self.config.get('auto_vacuum') == 'incremental':
                    conn.execute("PRAGMA incremental_vacuum(1000)")
                
                self.logger.info("Database optimization completed")
                
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
    
    def _cleanup_connections(self):
        """Clean up invalid connections from pool"""
        cleaned_count = 0
        temp_connections = []
        
        # Drain pool and check connections
        while True:
            try:
                conn = self.connection_pool.get(block=False)
                if self._is_connection_valid(conn):
                    temp_connections.append(conn)
                else:
                    conn.close()
                    cleaned_count += 1
            except queue.Empty:
                break
        
        # Put valid connections back
        for conn in temp_connections:
            try:
                self.connection_pool.put(conn, block=False)
            except queue.Full:
                conn.close()
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} invalid connections")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        with self.metrics_lock:
            if not self.query_metrics:
                return {}
            
            total_queries = len(self.query_metrics)
            avg_execution_time = sum(m.execution_time for m in self.query_metrics) / total_queries
            
            # Group by operation type
            operations = {}
            for metric in self.query_metrics:
                op_type = metric.operation_type
                if op_type not in operations:
                    operations[op_type] = {
                        'count': 0,
                        'total_time': 0,
                        'avg_time': 0
                    }
                operations[op_type]['count'] += 1
                operations[op_type]['total_time'] += metric.execution_time
            
            # Calculate averages
            for op_data in operations.values():
                op_data['avg_time'] = op_data['total_time'] / op_data['count']
            
            # Slowest queries
            slowest_queries = sorted(
                self.query_metrics, 
                key=lambda x: x.execution_time, 
                reverse=True
            )[:10]
            
            return {
                'total_queries': total_queries,
                'average_execution_time': avg_execution_time,
                'operations_breakdown': operations,
                'slowest_queries': [
                    {
                        'query': q.query,
                        'execution_time': q.execution_time,
                        'table_name': q.table_name,
                        'operation_type': q.operation_type
                    } for q in slowest_queries
                ],
                'cache_stats': {
                    'cache_size': len(self.query_cache),
                    'cache_limit': self.cache_size
                },
                'connection_stats': {
                    'pool_size': self.connection_pool.qsize(),
                    'active_connections': len(self.active_connections),
                    'max_connections': self.pool_size + self.max_overflow
                }
            }
    
    def optimize_performance(self):
        """Manual performance optimization"""
        try:
            # Clear old metrics
            with self.metrics_lock:
                if len(self.query_metrics) > 5000:
                    self.query_metrics = self.query_metrics[-2500:]
            
            # Clear cache
            with self.cache_lock:
                self.query_cache.clear()
            
            # Optimize database
            self._optimize_database()
            
            # Clean connections
            self._cleanup_connections()
            
            self.logger.info("Manual performance optimization completed")
            
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {e}")

# Global enterprise database instance
enterprise_db = None

def get_enterprise_database(db_path: str = None, config: Dict[str, Any] = None) -> EnterpriseDatabase:
    """Get global enterprise database instance"""
    global enterprise_db
    
    if enterprise_db is None:
        from enterprise_config import ENTERPRISE_CONFIG
        db_path = db_path or "./config/users.db"
        config = config or ENTERPRISE_CONFIG
        enterprise_db = EnterpriseDatabase(db_path, config)
    
    return enterprise_db