import sqlite3
import os

# Check admin user in the new database
db_path = os.path.join('config', 'users.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT username, role FROM users WHERE role = 'admin'")
admin_users = cursor.fetchall()
print("Admin users:", admin_users)

# Check admin user details
cursor.execute("SELECT username, password_hash, role FROM users WHERE username = 'admin'")
admin_detail = cursor.fetchone()
print("Admin details:", admin_detail)

# Test password hash
if admin_detail:
    from werkzeug.security import check_password_hash
    password_hash = admin_detail[1]
    is_valid = check_password_hash(password_hash, 'admin123')
    print(f"Password 'admin123' is valid: {is_valid}")

conn.close()