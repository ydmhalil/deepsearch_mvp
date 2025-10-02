"""
Document Classification and Permission System
Enhanced database schema for professional categorization and security levels
"""

import sqlite3
import os
from datetime import datetime

def create_classification_tables():
    """Create tables for document classification and user permissions"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'config', 'users.db')
    
    # Connect to existing database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🏗️ Creating document classification tables...")
    
    # 1. Professional Categories (Meslek Grupları)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS professional_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            color_code TEXT DEFAULT '#667eea',
            icon TEXT DEFAULT 'folder',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # 2. Security Levels (Gizlilik Seviyeleri)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            level_number INTEGER UNIQUE NOT NULL,
            description TEXT,
            color_code TEXT DEFAULT '#10b981',
            requirements TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # 3. User Permissions (Kullanıcı Yetkileri)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            security_level_id INTEGER,
            permission_type TEXT DEFAULT 'read',
            granted_by INTEGER NOT NULL,
            granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            is_active BOOLEAN DEFAULT 1,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (category_id) REFERENCES professional_categories (id),
            FOREIGN KEY (security_level_id) REFERENCES security_levels (id),
            FOREIGN KEY (granted_by) REFERENCES users (id),
            UNIQUE(user_id, category_id, security_level_id)
        )
    ''')
    
    # 4. Document Classifications (Belge Sınıflandırma)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            security_level_id INTEGER NOT NULL,
            classification_method TEXT DEFAULT 'manual',
            confidence_score REAL DEFAULT 1.0,
            classified_by INTEGER NOT NULL,
            classified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            review_required BOOLEAN DEFAULT 0,
            review_date DATETIME,
            reviewed_by INTEGER,
            notes TEXT,
            FOREIGN KEY (document_id) REFERENCES documents (id),
            FOREIGN KEY (category_id) REFERENCES professional_categories (id),
            FOREIGN KEY (security_level_id) REFERENCES security_levels (id),
            FOREIGN KEY (classified_by) REFERENCES users (id),
            FOREIGN KEY (reviewed_by) REFERENCES users (id),
            UNIQUE(document_id)
        )
    ''')
    
    # 5. Access Audit Log (Erişim Denetim Kaydı)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            document_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            access_granted BOOLEAN NOT NULL,
            reason TEXT,
            ip_address TEXT,
            user_agent TEXT,
            session_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
    ''')
    
    # 6. Classification Rules (Otomatik Sınıflandırma Kuralları)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classification_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            keywords TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            security_level_id INTEGER NOT NULL,
            confidence_threshold REAL DEFAULT 0.8,
            is_active BOOLEAN DEFAULT 1,
            created_by INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES professional_categories (id),
            FOREIGN KEY (security_level_id) REFERENCES security_levels (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    print("✅ Classification tables created successfully!")
    
    # Insert default professional categories
    default_categories = [
        ('Yönetim/İdari', 'Yönetim kurulu, strateji, planlama belgeleri', '#667eea', 'briefcase'),
        ('Mühendislik', 'Teknik çizimler, tasarım, test raporları', '#06b6d4', 'cog'),
        ('Güvenlik', 'Güvenlik protokolleri, siber güvenlik', '#ef4444', 'shield'),
        ('Finans', 'Mali raporlar, bütçe, muhasebe belgeleri', '#10b981', 'dollar-sign'),
        ('Hukuk', 'Sözleşmeler, yasal düzenlemeler, anlaşmalar', '#f59e0b', 'scale'),
        ('İnsan Kaynakları', 'Personel dosyaları, eğitim, özlük işleri', '#8b5cf6', 'users'),
        ('Araştırma & Geliştirme', 'AR-GE projeleri, inovasyon, patent', '#ec4899', 'lightbulb'),
        ('Üretim', 'Üretim süreçleri, kalite kontrol, lojistik', '#84cc16', 'factory')
    ]
    
    for name, desc, color, icon in default_categories:
        cursor.execute('''
            INSERT OR IGNORE INTO professional_categories (name, description, color_code, icon) 
            VALUES (?, ?, ?, ?)
        ''', (name, desc, color, icon))
    
    # Insert default security levels
    default_security_levels = [
        ('Açık', 1, 'Herkese açık belgeler', '#10b981', 'Tüm çalışanlar erişebilir'),
        ('Sınırlı', 2, 'Departman içi belgeler', '#f59e0b', 'Sadece ilgili departman çalışanları'),
        ('Gizli', 3, 'Hassas şirket bilgileri', '#ef4444', 'Üst düzey yönetim ve yetkili personel'),
        ('Çok Gizli', 4, 'En üst seviye gizli belgeler', '#7c3aed', 'Sadece C-level yöneticiler'),
        ('Askeri Gizli', 5, 'Askeri savunma belgeleri', '#1f2937', 'Özel güvenlik izni gerekli')
    ]
    
    for name, level, desc, color, req in default_security_levels:
        cursor.execute('''
            INSERT OR IGNORE INTO security_levels (name, level_number, description, color_code, requirements) 
            VALUES (?, ?, ?, ?, ?)
        ''', (name, level, desc, color, req))
    
    # Insert default classification rules
    default_rules = [
        ('Finansal Belgeler', 'finansal,rapor,bütçe,gelir,gider,kar,zarar,bilanço,mali', 4, 2),  # Finans, Sınırlı
        ('Güvenlik Protokolleri', 'güvenlik,protocol,siber,şifre,erişim,koruma,firewall', 3, 3),  # Güvenlik, Gizli
        ('Teknik Dokümantasyon', 'roket,motor,mühendislik,tasarım,teknik,şema,çizim', 2, 2),      # Mühendislik, Sınırlı
        ('Yönetim Belgeleri', 'strateji,yönetim,planlama,hedef,vizyon,misyon,kurul', 1, 3),       # Yönetim, Gizli
        ('Hukuki Belgeler', 'sözleşme,anlaşma,yasal,hukuk,mahkeme,dava,avukat', 5, 3),           # Hukuk, Gizli
        ('İK Belgeleri', 'personel,çalışan,maaş,özlük,eğitim,performans,işe alım', 6, 2),        # İK, Sınırlı
        ('AR-GE Projeleri', 'araştırma,geliştirme,inovasyon,patent,prototip,deneyim', 7, 4),     # AR-GE, Çok Gizli
        ('Üretim Süreçleri', 'üretim,kalite,kontrol,süreç,prosedür,imalat,fabrika', 8, 2)        # Üretim, Sınırlı
    ]
    
    for name, keywords, cat_id, sec_id in default_rules:
        cursor.execute('''
            INSERT OR IGNORE INTO classification_rules (name, keywords, category_id, security_level_id, created_by) 
            VALUES (?, ?, ?, ?, 1)
        ''', (name, keywords, cat_id, sec_id))
    
    # Grant admin user full permissions
    cursor.execute('SELECT id FROM users WHERE role = "admin" LIMIT 1')
    admin_user = cursor.fetchone()
    
    if admin_user:
        admin_id = admin_user[0]
        # Grant access to all categories and security levels
        for cat_id in range(1, 9):  # 8 categories
            for sec_id in range(1, 6):  # 5 security levels
                cursor.execute('''
                    INSERT OR IGNORE INTO user_permissions (user_id, category_id, security_level_id, permission_type, granted_by) 
                    VALUES (?, ?, ?, 'admin', ?)
                ''', (admin_id, cat_id, sec_id, admin_id))
    
    # Commit changes
    conn.commit()
    
    print("📊 Default categories inserted:")
    print("   • Yönetim/İdari, Mühendislik, Güvenlik, Finans")
    print("   • Hukuk, İnsan Kaynakları, AR-GE, Üretim")
    
    print("🔒 Default security levels inserted:")
    print("   • Açık (1), Sınırlı (2), Gizli (3), Çok Gizli (4), Askeri Gizli (5)")
    
    print("🤖 Default classification rules inserted")
    print("👤 Admin user granted full permissions")
    
    # Display table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%classif%' OR name LIKE '%permission%' OR name LIKE '%security%' OR name LIKE '%professional%' OR name LIKE '%access%'")
    new_tables = cursor.fetchall()
    print(f"🗄️ New tables created: {[t[0] for t in new_tables]}")
    
    conn.close()
    return True

if __name__ == "__main__":
    create_classification_tables()
    print("🎉 Document classification system initialized!")