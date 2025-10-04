import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [row[0] for row in tables])

# If users table exists, show schema
if any('users' in table for table in tables):
    cursor.execute("PRAGMA table_info(users)")
    schema = cursor.fetchall()
    print("Users table schema:")
    for row in schema:
        print(f"  {row[1]} ({row[2]})")
    
    # Show sample data
    cursor.execute("SELECT * FROM users LIMIT 3")
    users = cursor.fetchall()
    print("Sample users:")
    for user in users:
        print(f"  {user}")

conn.close()