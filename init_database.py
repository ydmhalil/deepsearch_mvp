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
    
    # Enterprise Classification Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS professional_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            color_code TEXT DEFAULT '#6366f1',
            icon_name TEXT DEFAULT 'folder',
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            level_number INTEGER UNIQUE NOT NULL,
            description TEXT,
            color_code TEXT DEFAULT '#ef4444',
            access_requirements TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            category_id INTEGER,
            security_level_id INTEGER,
            confidence_score REAL,
            classified_by INTEGER,
            classification_method TEXT DEFAULT 'manual',
            notes TEXT,
            classified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id),
            FOREIGN KEY (category_id) REFERENCES professional_categories (id),
            FOREIGN KEY (security_level_id) REFERENCES security_levels (id),
            FOREIGN KEY (classified_by) REFERENCES users (id)
        )
    ''')
    
    # User Permission Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_category_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            permission_type TEXT NOT NULL,
            granted_by INTEGER,
            granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (category_id) REFERENCES professional_categories (id),
            FOREIGN KEY (granted_by) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_security_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            security_level_id INTEGER NOT NULL,
            permission_type TEXT NOT NULL,
            granted_by INTEGER,
            granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (security_level_id) REFERENCES security_levels (id),
            FOREIGN KEY (granted_by) REFERENCES users (id)
        )
    ''')
    
    # Security and Audit Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER,
            FOREIGN KEY (updated_by) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id INTEGER,
            details TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Add full_name column to users table if it doesn't exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'full_name' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN full_name TEXT')
    
    # Insert default categories
    default_categories = [
        ('Genel', 'Genel dokümanlar', '#6366f1', 'folder'),
        ('Hukuki', 'Hukuki dokümanlar', '#dc2626', 'gavel'),
        ('Teknik', 'Teknik dokümanlar', '#059669', 'cpu'),
        ('Mali', 'Mali dokümanlar', '#d97706', 'dollar-sign'),
        ('İnsan Kaynakları', 'İK dokümanları', '#7c3aed', 'users')
    ]
    
    for name, desc, color, icon in default_categories:
        cursor.execute('''
            INSERT OR IGNORE INTO professional_categories (name, description, color_code, icon_name)
            VALUES (?, ?, ?, ?)
        ''', (name, desc, color, icon))
    
    # Insert default security levels
    default_security_levels = [
        ('Genel', 1, 'Herkes tarafından erişilebilir', '#10b981'),
        ('Dahili', 2, 'Şirket içi personel', '#f59e0b'),
        ('Gizli', 3, 'Yetkili personel', '#ef4444'),
        ('Çok Gizli', 4, 'Üst yönetim', '#7c2d12')
    ]
    
    for name, level, desc, color in default_security_levels:
        cursor.execute('''
            INSERT OR IGNORE INTO security_levels (name, level_number, description, color_code)
            VALUES (?, ?, ?, ?)
        ''', (name, level, desc, color))
    
    # Insert default security settings
    default_security_settings = [
        ('min_password_length', '8', 'authentication'),
        ('password_complexity', 'true', 'authentication'),
        ('session_timeout', '480', 'authentication'),
        ('max_login_attempts', '5', 'authentication'),
        ('lockout_duration', '30', 'authentication'),
        ('default_user_role', 'user', 'authorization'),
        ('permission_inheritance', 'true', 'authorization'),
        ('guest_access_enabled', 'false', 'authorization'),
        ('admin_approval_required', 'true', 'authorization'),
        ('audit_enabled', 'true', 'audit'),
        ('audit_retention_days', '90', 'audit'),
        ('audit_sensitive_data', 'false', 'audit'),
        ('data_encryption', 'true', 'privacy'),
        ('anonymize_logs', 'false', 'privacy'),
        ('data_retention_days', '365', 'privacy')
    ]
    
    for key, value, category in default_security_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO security_settings (setting_key, setting_value, category)
            VALUES (?, ?, ?)
        ''', (key, value, category))
    
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
    print("🏢 Enterprise tables: professional_categories, security_levels, document_classifications")
    print("👤 Permission tables: user_category_permissions, user_security_permissions")
    print("🔐 Audit tables: security_settings, audit_logs")
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