"""
Database initialization script for DeepSearch User Management
Creates SQLite database with user management tables
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_database():
    """Initialize SQLite database with required tables"""
    
    # Create config directory if it doesn't exist
    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    os.makedirs(config_dir, exist_ok=True)
    
    # Database path
    db_path = os.path.join(config_dir, 'users.db')
    
    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"🗄️ Creating database at: {db_path}")
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create search_logs table for analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT NOT NULL,
            results_count INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            response_time REAL,
            filters TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create documents table for file management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            file_type TEXT,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER,
            user_id INTEGER,
            indexed_date DATETIME,
            is_indexed BOOLEAN DEFAULT 0,
            is_processed BOOLEAN DEFAULT 0,
            file_hash TEXT,
            chunks_file TEXT,
            index_file TEXT,
            meta_file TEXT,
            FOREIGN KEY (uploaded_by) REFERENCES users (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create settings table for system configuration
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create saved_searches table for bookmarks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            query TEXT NOT NULL,
            filters TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_used DATETIME,
            use_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create security tables for enterprise features
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            user_id INTEGER,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rate_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            request_count INTEGER DEFAULT 1,
            window_start DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_request DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            ip_address TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            attempt_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_agent TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            document_id INTEGER,
            title TEXT NOT NULL,
            url TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            business_category TEXT,
            sentiment_score REAL,
            key_topics TEXT,
            summary TEXT,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
    ''')
    
    # Create default admin user if not exists
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        admin_password_hash = generate_password_hash('admin123', method='pbkdf2:sha256')
        cursor.execute('''
            INSERT INTO users (username, password_hash, role) 
            VALUES (?, ?, ?)
        ''', ('admin', admin_password_hash, 'admin'))
        print("👤 Created default admin user: admin / admin123")
    
    # Insert default settings
    default_settings = [
        ('max_file_size', '50', 'Maximum file size in MB'),
        ('max_concurrent_users', '10', 'Maximum concurrent users'),
        ('session_timeout', '3600', 'Session timeout in seconds'),
        ('search_results_per_page', '20', 'Search results per page'),
        ('enable_file_upload', '1', 'Enable file upload functionality')
    ]
    
    for key, value, description in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value, description) 
            VALUES (?, ?, ?)
        ''', (key, value, description))
    
    # Commit changes
    conn.commit()
    
    print("✅ Database tables created successfully!")
    print("📊 Tables: users, search_logs, documents, settings, saved_searches")
    print("🔒 Security tables: security_events, user_sessions, rate_limits, login_attempts")
    print("📚 Additional tables: bookmarks, document_insights")
    print("🔑 Default admin user created")
    
    # Display table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"📋 Database contains {len(tables)} tables: {[t[0] for t in tables]}")
    
    conn.close()
    return db_path

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(__file__), 'config', 'users.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn

if __name__ == "__main__":
    db_path = init_database()
    print(f"🎉 Database initialized at: {db_path}")