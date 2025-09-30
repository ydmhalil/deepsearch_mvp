"""
Database Performance Optimization Module
Provides database indexing, query optimization, and connection pooling
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import logging

class DatabaseOptimizer:
    """Database performance optimization and management"""
    
    def __init__(self, db_path: str = 'search_system.db', pool_size: int = 10):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connection_pool = []
        self.pool_lock = threading.Lock()
        self.stats = {
            'queries_executed': 0,
            'avg_query_time': 0,
            'slow_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self._initialize_pool()
        self._create_indexes()
        
    def _initialize_pool(self):
        """Initialize connection pool"""
        with self.pool_lock:
            for _ in range(self.pool_size):
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                
                # Performance optimizations
                conn.execute('PRAGMA journal_mode = WAL')  # Write-Ahead Logging
                conn.execute('PRAGMA synchronous = NORMAL')  # Faster writes
                conn.execute('PRAGMA cache_size = 10000')   # 10MB cache
                conn.execute('PRAGMA temp_store = MEMORY')  # Memory temp tables
                conn.execute('PRAGMA mmap_size = 268435456') # 256MB memory mapped
                
                self.connection_pool.append(conn)
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        conn = None
        try:
            with self.pool_lock:
                if self.connection_pool:
                    conn = self.connection_pool.pop()
                else:
                    # If pool empty, create temporary connection
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = sqlite3.Row
            
            yield conn
            
        finally:
            if conn:
                with self.pool_lock:
                    if len(self.connection_pool) < self.pool_size:
                        self.connection_pool.append(conn)
                    else:
                        conn.close()
    
    def _create_indexes(self):
        """Create performance indexes"""
        indexes = [
            # User tables
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            
            # Documents table
            "CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type)",
            "CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date)",
            "CREATE INDEX IF NOT EXISTS idx_documents_is_processed ON documents(is_processed)",
            
            # Search logs
            "CREATE INDEX IF NOT EXISTS idx_search_logs_user_id ON search_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_search_logs_timestamp ON search_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_search_logs_query ON search_logs(query)",
            
            # Security events
            "CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity)",
            "CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_security_events_ip ON security_events(ip_address)",
            
            # User sessions
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active)",
            
            # Rate limits
            "CREATE INDEX IF NOT EXISTS idx_rate_limits_ip_endpoint ON rate_limits(ip_address, endpoint)",
            "CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_start)",
            
            # Login attempts
            "CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address)",
            "CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(attempt_time)",
            "CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username)",
            
            # Bookmarks
            "CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON bookmarks(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_bookmarks_created_at ON bookmarks(created_at)",
            
            # Document insights
            "CREATE INDEX IF NOT EXISTS idx_document_insights_document_id ON document_insights(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_document_insights_category ON document_insights(business_category)",
            
            # Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_documents_user_date ON documents(user_id, upload_date)",
            "CREATE INDEX IF NOT EXISTS idx_search_logs_user_time ON search_logs(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_security_events_type_time ON security_events(event_type, timestamp)",
        ]
        
        with self.get_connection() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(index_sql)
                except sqlite3.Error as e:
                    # Only log if it's not a "no such table" error since tables might not exist yet
                    if "no such table" not in str(e).lower():
                        logging.warning(f"Index creation failed: {e}")
            conn.commit()
    
    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False, 
                     fetch_all: bool = True) -> Optional[List[Dict]]:
        """Execute query with performance monitoring"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch_one:
                    result = cursor.fetchone()
                    result = dict(result) if result else None
                elif fetch_all:
                    result = [dict(row) for row in cursor.fetchall()]
                else:
                    result = cursor.rowcount
                
                conn.commit()
                
                # Performance tracking
                execution_time = time.time() - start_time
                self.stats['queries_executed'] += 1
                
                # Update average query time
                current_avg = self.stats['avg_query_time']
                total_queries = self.stats['queries_executed']
                self.stats['avg_query_time'] = (current_avg * (total_queries - 1) + execution_time) / total_queries
                
                # Track slow queries (>100ms)
                if execution_time > 0.1:
                    self.stats['slow_queries'] += 1
                    logging.warning(f"Slow query detected: {execution_time:.3f}s - {query[:100]}...")
                
                return result
                
        except sqlite3.Error as e:
            logging.error(f"Database query failed: {e}")
            return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            db_size_mb = (page_count * page_size) / (1024 * 1024)
            
            # Cache statistics
            cursor.execute("PRAGMA cache_size")
            cache_size = cursor.fetchone()[0]
            
            # WAL mode info
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            
            return {
                'database_size_mb': round(db_size_mb, 2),
                'cache_size_pages': cache_size,
                'journal_mode': journal_mode,
                'connection_pool_size': len(self.connection_pool),
                'queries_executed': self.stats['queries_executed'],
                'avg_query_time_ms': round(self.stats['avg_query_time'] * 1000, 2),
                'slow_queries': self.stats['slow_queries'],
                'slow_query_percentage': round((self.stats['slow_queries'] / max(1, self.stats['queries_executed'])) * 100, 2)
            }
    
    def optimize_database(self):
        """Run database optimization commands"""
        optimization_commands = [
            "PRAGMA optimize",           # Query planner optimization
            "VACUUM",                   # Rebuild database file
            "REINDEX",                  # Rebuild all indexes
            "ANALYZE"                   # Update query planner statistics
        ]
        
        with self.get_connection() as conn:
            for command in optimization_commands:
                try:
                    logging.info(f"Running database optimization: {command}")
                    conn.execute(command)
                except sqlite3.Error as e:
                    logging.error(f"Optimization command failed: {command} - {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to maintain performance"""
        cleanup_queries = [
            # Clean old search logs
            f"DELETE FROM search_logs WHERE timestamp < datetime('now', '-{days_to_keep} days')",
            
            # Clean old security events (keep high severity longer)
            f"DELETE FROM security_events WHERE timestamp < datetime('now', '-{days_to_keep} days') AND severity != 'high'",
            f"DELETE FROM security_events WHERE timestamp < datetime('now', '-{days_to_keep * 2} days')",
            
            # Clean old rate limit entries
            f"DELETE FROM rate_limits WHERE window_start < datetime('now', '-1 day')",
            
            # Clean old login attempts
            f"DELETE FROM login_attempts WHERE attempt_time < datetime('now', '-{days_to_keep} days')",
            
            # Clean expired sessions
            "DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP OR is_active = FALSE"
        ]
        
        deleted_rows = 0
        with self.get_connection() as conn:
            for query in cleanup_queries:
                try:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    deleted_rows += cursor.rowcount
                    logging.info(f"Cleanup query executed: {cursor.rowcount} rows deleted")
                except sqlite3.Error as e:
                    logging.error(f"Cleanup failed: {e}")
            
            conn.commit()
        
        return deleted_rows
    
    def close_pool(self):
        """Close all connections in pool"""
        with self.pool_lock:
            for conn in self.connection_pool:
                conn.close()
            self.connection_pool.clear()

# Query optimization helpers
class QueryOptimizer:
    """SQL query optimization utilities"""
    
    @staticmethod
    def paginate_query(base_query: str, page: int = 1, per_page: int = 20) -> str:
        """Add pagination to query"""
        offset = (page - 1) * per_page
        return f"{base_query} LIMIT {per_page} OFFSET {offset}"
    
    @staticmethod
    def add_search_conditions(base_query: str, search_term: str = None, 
                            date_from: str = None, date_to: str = None,
                            additional_filters: Dict[str, Any] = None) -> tuple:
        """Add search conditions to query"""
        conditions = []
        params = []
        
        if search_term:
            conditions.append("(query LIKE ? OR file_name LIKE ?)")
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        if date_from:
            conditions.append("timestamp >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("timestamp <= ?")
            params.append(date_to)
        
        if additional_filters:
            for field, value in additional_filters.items():
                conditions.append(f"{field} = ?")
                params.append(value)
        
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
            optimized_query = f"{base_query} {where_clause}"
        else:
            optimized_query = base_query
        
        return optimized_query, tuple(params)
    
    @staticmethod
    def get_optimized_search_history_query(user_id: int, page: int = 1, 
                                         per_page: int = 20, search_term: str = None) -> tuple:
        """Get optimized search history query"""
        base_query = """
            SELECT sl.*, COUNT(*) OVER() as total_count
            FROM search_logs sl
        """
        
        # Add search conditions
        conditions = ["sl.user_id = ?"]
        params = [user_id]
        
        if search_term:
            conditions.append("sl.query LIKE ?")
            params.append(f"%{search_term}%")
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        # Add ordering and pagination
        query = f"""
            {base_query}
            {where_clause}
            ORDER BY sl.timestamp DESC
            LIMIT ? OFFSET ?
        """
        
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        return query, tuple(params)

# Global optimizer instance with correct database path
import os
db_path = os.path.join(os.path.dirname(__file__), 'config', 'users.db')
db_optimizer = DatabaseOptimizer(db_path=db_path)

# Usage examples and helper functions
def get_optimized_user_documents(user_id: int, page: int = 1, per_page: int = 20, 
                               file_type: str = None) -> List[Dict]:
    """Get user documents with optimization"""
    base_query = """
        SELECT d.*, di.business_category, di.sentiment_score
        FROM documents d
        LEFT JOIN document_insights di ON d.id = di.document_id
    """
    
    conditions = ["d.user_id = ?"]
    params = [user_id]
    
    if file_type:
        conditions.append("d.file_type = ?")
        params.append(file_type)
    
    where_clause = "WHERE " + " AND ".join(conditions)
    
    query = f"""
        {base_query}
        {where_clause}
        ORDER BY d.upload_date DESC
        LIMIT ? OFFSET ?
    """
    
    offset = (page - 1) * per_page
    params.extend([per_page, offset])
    
    return db_optimizer.execute_query(query, tuple(params))

def get_dashboard_analytics_optimized(user_id: int = None, days: int = 30) -> Dict[str, Any]:
    """Get dashboard analytics with optimized queries"""
    # Use single query for multiple metrics
    analytics_query = """
        WITH document_stats AS (
            SELECT 
                COUNT(*) as total_documents,
                COUNT(DISTINCT file_type) as file_types,
                AVG(CASE WHEN is_processed THEN 1 ELSE 0 END) as processing_rate
            FROM documents 
            WHERE user_id = ? OR ? IS NULL
        ),
        search_stats AS (
            SELECT 
                COUNT(*) as total_searches,
                COUNT(DISTINCT query) as unique_queries,
                AVG(results_count) as avg_results
            FROM search_logs 
            WHERE (user_id = ? OR ? IS NULL) 
                AND timestamp >= datetime('now', '-{} days')
        ),
        recent_activity AS (
            SELECT COUNT(*) as recent_documents
            FROM documents 
            WHERE (user_id = ? OR ? IS NULL)
                AND upload_date >= datetime('now', '-{} days')
        )
        SELECT * FROM document_stats, search_stats, recent_activity
    """.format(days, days)
    
    params = [user_id, user_id, user_id, user_id, user_id, user_id]
    result = db_optimizer.execute_query(analytics_query, tuple(params), fetch_one=True)
    
    return result or {}