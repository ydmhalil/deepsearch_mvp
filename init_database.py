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
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER,
            indexed_date DATETIME,
            is_indexed BOOLEAN DEFAULT 0,
            FOREIGN KEY (uploaded_by) REFERENCES users (id)
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
    print("📊 Tables: users, search_logs, documents, settings")
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