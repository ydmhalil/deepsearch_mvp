"""
Authentication module for DeepSearch user management
Handles user registration, login, logout, and session management
"""

from functools import wraps
from flask import session, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from init_database import get_db_connection
from datetime import datetime

class UserManager:
    """User management class for authentication operations"""
    
    def __init__(self):
        self.session_timeout = 3600  # 1 hour default
        
    def register_user(self, username, password, role='user'):
        """Register a new user"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if username already exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                conn.close()
                return {'success': False, 'message': 'Kullanıcı adı zaten mevcut'}
            
            # Hash password and create user
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, created_at) 
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, role, datetime.now()))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Kullanıcı başarıyla oluşturuldu', 'user_id': user_id}
            
        except Exception as e:
            return {'success': False, 'message': f'Kullanıcı oluşturulurken hata: {str(e)}'}
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, password_hash, role, is_active 
                FROM users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return {'success': False, 'message': 'Kullanıcı bulunamadı'}
            
            if not user['is_active']:
                conn.close()
                return {'success': False, 'message': 'Kullanıcı hesabı deaktif'}
            
            if not check_password_hash(user['password_hash'], password):
                conn.close()
                return {'success': False, 'message': 'Şifre yanlış'}
            
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now(), user['id']))
            conn.commit()
            conn.close()
            
            return {
                'success': True, 
                'message': 'Giriş başarılı',
                'user': {
                    'id': user['id'],
                    'username': user['username'], 
                    'role': user['role']
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Giriş sırasında hata: {str(e)}'}
    
    def get_user_by_id(self, user_id):
        """Get user information by ID"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, role, created_at, last_login, is_active 
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return dict(user)
            return None
            
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def get_all_users(self, include_inactive=False):
        """Get all users (for admin panel)"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT id, username, role, created_at, last_login, is_active 
                FROM users 
            '''
            if not include_inactive:
                query += ' WHERE is_active = 1'
                
            cursor.execute(query)
            users = cursor.fetchall()
            conn.close()
            
            return [dict(user) for user in users]
            
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def update_user_status(self, user_id, is_active):
        """Activate/deactivate user"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET is_active = ? WHERE id = ?
            ''', (is_active, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error updating user status: {e}")
            return False

# Global user manager instance
user_manager = UserManager()

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Giriş yapmanız gerekiyor', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Giriş yapmanız gerekiyor', 'warning')
            return redirect(url_for('login'))
        
        if session.get('role') != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            flash('Bu sayfaya erişim yetkiniz yok', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged in user info"""
    if 'user_id' in session:
        return user_manager.get_user_by_id(session['user_id'])
    return None