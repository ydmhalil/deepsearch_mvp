"""
Advanced Analytics System for DeepSearch
Kullanıcı davranış analitiği ve sistem performans metrikleri
"""

import sqlite3
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchAnalytics:
    """Arama analitik verisi"""
    query: str
    user_id: str
    timestamp: datetime
    results_count: int
    response_time: float
    domain_relevance: float
    embedding_type: str  # 'normal' or 'domain'
    clicked_results: List[str]
    session_id: str
    query_category: str  # 'security', 'technical', 'general' etc.

@dataclass 
class UserBehavior:
    """Kullanıcı davranış verisi"""
    user_id: str
    session_count: int
    total_queries: int
    avg_session_duration: float
    favorite_categories: List[str]
    most_searched_terms: List[str]
    peak_usage_hours: List[int]
    last_activity: datetime

@dataclass
class SystemPerformance:
    """Sistem performans metrikleri"""
    timestamp: datetime
    avg_response_time: float
    search_volume: int
    error_rate: float
    memory_usage: float
    cpu_usage: float
    active_users: int
    popular_queries: List[Tuple[str, int]]

class AdvancedAnalytics:
    """Gelişmiş analitik sistemi"""
    
    def __init__(self, db_path: str = "./config/analytics.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Analytics database'ini başlat"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Search analytics tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    results_count INTEGER,
                    response_time REAL,
                    domain_relevance REAL,
                    embedding_type TEXT,
                    clicked_results TEXT,  -- JSON
                    session_id TEXT,
                    query_category TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User behavior analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_behavior (
                    user_id TEXT PRIMARY KEY,
                    session_count INTEGER DEFAULT 0,
                    total_queries INTEGER DEFAULT 0,
                    avg_session_duration REAL DEFAULT 0,
                    favorite_categories TEXT,  -- JSON
                    most_searched_terms TEXT,  -- JSON
                    peak_usage_hours TEXT,     -- JSON
                    last_activity DATETIME,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    avg_response_time REAL,
                    search_volume INTEGER,
                    error_rate REAL,
                    memory_usage REAL,
                    cpu_usage REAL,
                    active_users INTEGER,
                    popular_queries TEXT,  -- JSON
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Query patterns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    category TEXT,
                    avg_relevance REAL,
                    success_rate REAL,
                    first_seen DATETIME,
                    last_seen DATETIME,
                    UNIQUE(pattern)
                )
            """)
            
            conn.commit()
            
        logger.info("Analytics database initialized successfully")
    
    def log_search(self, analytics: SearchAnalytics):
        """Arama analitiğini kaydet"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO search_analytics 
                    (query, user_id, timestamp, results_count, response_time, 
                     domain_relevance, embedding_type, clicked_results, session_id, query_category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analytics.query,
                    analytics.user_id,
                    analytics.timestamp,
                    analytics.results_count,
                    analytics.response_time,
                    analytics.domain_relevance,
                    analytics.embedding_type,
                    json.dumps(analytics.clicked_results),
                    analytics.session_id,
                    analytics.query_category
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log search analytics: {e}")
    
    def update_user_behavior(self, user_id: str):
        """Kullanıcı davranış verilerini güncelle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Kullanıcının son 30 gündeki aktivitelerini analiz et
                thirty_days_ago = datetime.now() - timedelta(days=30)
                
                cursor.execute("""
                    SELECT query, timestamp, query_category, response_time
                    FROM search_analytics 
                    WHERE user_id = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                """, (user_id, thirty_days_ago))
                
                activities = cursor.fetchall()
                
                if not activities:
                    return
                
                # Analitik hesaplamaları
                queries = [a[0] for a in activities]
                categories = [a[2] for a in activities if a[2]]
                timestamps = [datetime.fromisoformat(a[1]) for a in activities]
                
                session_count = len(set(t.date() for t in timestamps))
                total_queries = len(queries)
                
                # Favori kategoriler
                category_counts = Counter(categories)
                favorite_categories = [cat for cat, count in category_counts.most_common(5)]
                
                # En çok aranan terimler
                term_counts = Counter(queries)
                most_searched_terms = [term for term, count in term_counts.most_common(10)]
                
                # Peak usage hours
                hours = [t.hour for t in timestamps]
                hour_counts = Counter(hours)
                peak_usage_hours = [hour for hour, count in hour_counts.most_common(3)]
                
                # Session duration (basit approximation)
                avg_session_duration = 0
                if len(timestamps) > 1:
                    total_duration = (timestamps[0] - timestamps[-1]).total_seconds()
                    avg_session_duration = total_duration / session_count if session_count > 0 else 0
                
                # Veritabanını güncelle
                cursor.execute("""
                    INSERT OR REPLACE INTO user_behavior 
                    (user_id, session_count, total_queries, avg_session_duration,
                     favorite_categories, most_searched_terms, peak_usage_hours, last_activity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    session_count,
                    total_queries,
                    avg_session_duration,
                    json.dumps(favorite_categories),
                    json.dumps(most_searched_terms),
                    json.dumps(peak_usage_hours),
                    datetime.now()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update user behavior: {e}")
    
    def log_system_performance(self, metrics: SystemPerformance):
        """Sistem performans metriklerini kaydet"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO system_performance 
                    (timestamp, avg_response_time, search_volume, error_rate,
                     memory_usage, cpu_usage, active_users, popular_queries)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp,
                    metrics.avg_response_time,
                    metrics.search_volume,
                    metrics.error_rate,
                    metrics.memory_usage,
                    metrics.cpu_usage,
                    metrics.active_users,
                    json.dumps(metrics.popular_queries)
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log system performance: {e}")
    
    def get_search_trends(self, days: int = 7) -> Dict[str, Any]:
        """Son N günün arama trendlerini getir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_date = datetime.now() - timedelta(days=days)
                
                # Daily search volumes
                cursor.execute("""
                    SELECT DATE(timestamp) as date, COUNT(*) as searches
                    FROM search_analytics 
                    WHERE timestamp > ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (start_date,))
                
                daily_volumes = dict(cursor.fetchall())
                
                # Popular queries
                cursor.execute("""
                    SELECT query, COUNT(*) as frequency
                    FROM search_analytics 
                    WHERE timestamp > ?
                    GROUP BY query
                    ORDER BY frequency DESC
                    LIMIT 10
                """, (start_date,))
                
                popular_queries = cursor.fetchall()
                
                # Category distribution
                cursor.execute("""
                    SELECT query_category, COUNT(*) as frequency
                    FROM search_analytics 
                    WHERE timestamp > ? AND query_category IS NOT NULL
                    GROUP BY query_category
                    ORDER BY frequency DESC
                """, (start_date,))
                
                category_distribution = dict(cursor.fetchall())
                
                # Average response times
                cursor.execute("""
                    SELECT embedding_type, AVG(response_time) as avg_time
                    FROM search_analytics 
                    WHERE timestamp > ? AND response_time IS NOT NULL
                    GROUP BY embedding_type
                """, (start_date,))
                
                response_times = dict(cursor.fetchall())
                
                return {
                    "daily_volumes": daily_volumes,
                    "popular_queries": popular_queries,
                    "category_distribution": category_distribution,
                    "response_times": response_times,
                    "period_days": days
                }
                
        except Exception as e:
            logger.error(f"Failed to get search trends: {e}")
            return {}
    
    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Kullanıcı için insights getir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # User behavior data
                cursor.execute("""
                    SELECT * FROM user_behavior WHERE user_id = ?
                """, (user_id,))
                
                user_data = cursor.fetchone()
                
                if not user_data:
                    return {"error": "User not found"}
                
                # Recent search patterns
                cursor.execute("""
                    SELECT query_category, COUNT(*) as frequency
                    FROM search_analytics 
                    WHERE user_id = ? AND timestamp > ?
                    GROUP BY query_category
                    ORDER BY frequency DESC
                """, (user_id, datetime.now() - timedelta(days=30)))
                
                recent_categories = dict(cursor.fetchall())
                
                # Search efficiency (clicks vs searches)
                cursor.execute("""
                    SELECT 
                        AVG(CASE WHEN clicked_results != '[]' THEN 1.0 ELSE 0.0 END) as click_rate,
                        AVG(domain_relevance) as avg_relevance
                    FROM search_analytics 
                    WHERE user_id = ? AND timestamp > ?
                """, (user_id, datetime.now() - timedelta(days=30)))
                
                efficiency_data = cursor.fetchone()
                
                return {
                    "user_id": user_id,
                    "session_count": user_data[1],
                    "total_queries": user_data[2],
                    "avg_session_duration": user_data[3],
                    "favorite_categories": json.loads(user_data[4] or "[]"),
                    "most_searched_terms": json.loads(user_data[5] or "[]"),
                    "peak_usage_hours": json.loads(user_data[6] or "[]"),
                    "recent_categories": recent_categories,
                    "click_rate": efficiency_data[0] if efficiency_data else 0,
                    "avg_relevance": efficiency_data[1] if efficiency_data else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get user insights: {e}")
            return {"error": str(e)}
    
    def get_system_dashboard(self) -> Dict[str, Any]:
        """Sistem dashboard verilerini getir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Today's metrics
                today = datetime.now().date()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_searches,
                        COUNT(DISTINCT user_id) as unique_users,
                        AVG(response_time) as avg_response_time,
                        AVG(domain_relevance) as avg_relevance
                    FROM search_analytics 
                    WHERE DATE(timestamp) = ?
                """, (today,))
                
                today_metrics = cursor.fetchone()
                
                # Recent system performance
                cursor.execute("""
                    SELECT * FROM system_performance 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                
                latest_performance = cursor.fetchone()
                
                # Query success rate
                cursor.execute("""
                    SELECT 
                        embedding_type,
                        AVG(CASE WHEN results_count > 0 THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM search_analytics 
                    WHERE timestamp > ?
                    GROUP BY embedding_type
                """, (datetime.now() - timedelta(days=7),))
                
                success_rates = dict(cursor.fetchall())
                
                return {
                    "today": {
                        "total_searches": today_metrics[0] if today_metrics else 0,
                        "unique_users": today_metrics[1] if today_metrics else 0,
                        "avg_response_time": today_metrics[2] if today_metrics else 0,
                        "avg_relevance": today_metrics[3] if today_metrics else 0
                    },
                    "system_performance": {
                        "memory_usage": latest_performance[5] if latest_performance else 0,
                        "cpu_usage": latest_performance[6] if latest_performance else 0,
                        "active_users": latest_performance[7] if latest_performance else 0
                    },
                    "success_rates": success_rates
                }
                
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {}
    
    def export_analytics_report(self, days: int = 30) -> str:
        """Analytics raporunu export et"""
        try:
            trends = self.get_search_trends(days)
            dashboard = self.get_system_dashboard()
            
            report = {
                "report_date": datetime.now().isoformat(),
                "period_days": days,
                "search_trends": trends,
                "system_dashboard": dashboard,
                "summary": {
                    "total_searches": sum(trends.get("daily_volumes", {}).values()),
                    "most_popular_query": trends.get("popular_queries", [("N/A", 0)])[0][0],
                    "dominant_category": max(trends.get("category_distribution", {"general": 1}).items(), key=lambda x: x[1])[0]
                }
            }
            
            report_path = f"./data/analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Analytics report exported to {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to export analytics report: {e}")
            return ""

def test_analytics_system():
    """Analytics sistemini test et"""
    print("=== Advanced Analytics System Test ===")
    
    analytics = AdvancedAnalytics()
    
    # Test search analytics
    test_search = SearchAnalytics(
        query="İHA güvenlik prosedürü",
        user_id="test_user",
        timestamp=datetime.now(),
        results_count=5,
        response_time=1.23,
        domain_relevance=0.95,
        embedding_type="domain",
        clicked_results=["doc1.pdf", "doc2.txt"],
        session_id="session_123",
        query_category="security"
    )
    
    analytics.log_search(test_search)
    analytics.update_user_behavior("test_user")
    
    # Get insights
    user_insights = analytics.get_user_insights("test_user")
    print(f"User Insights: {user_insights}")
    
    # Get dashboard
    dashboard = analytics.get_system_dashboard()
    print(f"Dashboard: {dashboard}")
    
    # Export report
    report_path = analytics.export_analytics_report(7)
    print(f"Report exported: {report_path}")

if __name__ == "__main__":
    test_analytics_system()