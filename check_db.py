#!/usr/bin/env python3
"""
Quick database check script
"""
import sqlite3
import os

def check_database():
    db_path = os.path.join(os.path.dirname(__file__), 'config', 'users.db')
    print(f"Database path: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check professional_categories table
        cursor.execute("SELECT COUNT(*) FROM professional_categories")
        count = cursor.fetchone()[0]
        print(f"\n📊 Professional Categories Count: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, name, color_code, icon_name FROM professional_categories LIMIT 5")
            categories = cursor.fetchall()
            print("\n📝 Categories:")
            for cat in categories:
                print(f"  ID: {cat[0]}, Name: {cat[1]}, Color: {cat[2]}, Icon: {cat[3]}")
        
        # Check security_levels table
        cursor.execute("SELECT COUNT(*) FROM security_levels")
        count = cursor.fetchone()[0]
        print(f"\n🔒 Security Levels Count: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, name, level_number FROM security_levels LIMIT 3")
            levels = cursor.fetchall()
            print("\n🛡️ Security Levels:")
            for level in levels:
                print(f"  ID: {level[0]}, Name: {level[1]}, Level: {level[2]}")
        
        conn.close()
        print("\n✅ Database check completed successfully!")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_database()