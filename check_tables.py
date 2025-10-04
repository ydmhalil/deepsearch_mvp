import sqlite3
import os

db_path = os.path.join('config', 'users.db')
print(f'Database path: {db_path}')
print(f'Database exists: {os.path.exists(db_path)}')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check all tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    print('\nTables in database:')
    for table in tables:
        print(f'  - {table[0]}')
    
    # Check users count
    try:
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        print(f'\nUsers in database: {user_count}')
    except Exception as e:
        print(f'Error checking users: {e}')
    
    # Check categories count
    try:
        cursor.execute('SELECT COUNT(*) FROM professional_categories')
        cat_count = cursor.fetchone()[0]
        print(f'Categories in database: {cat_count}')
    except Exception as e:
        print(f'Error checking categories: {e}')
    
    conn.close()