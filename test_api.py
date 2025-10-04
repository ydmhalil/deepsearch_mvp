"""
Test Flask server for category API testing
"""
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import sqlite3
import os
import hashlib
import jwt
import datetime
from datetime import datetime, timedelta, UTC

app = Flask(__name__, 
            static_folder='frontend-react/dist',
            static_url_path='')

# JWT Secret Key (in production, use environment variable)
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'

# Enable CORS for all routes
CORS(app, origins=['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5174', 'http://localhost:5001'])

@app.route('/')
def serve_index():
    """Serve the React app"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/admin')
def serve_admin():
    """Serve admin page"""
    return send_from_directory(app.static_folder, 'index.html')

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(__file__), 'config', 'users.db')
    print(f"Database path: {db_path}")  # Debug log
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    
    # Create users table if it doesn't exist
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            requested_role TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add new columns to existing table if they don't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN requested_role TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'pending'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add updated_at column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Ensure demo admin exists in database
    try:
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            admin_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, status, created_at)
                VALUES ('admin', 'admin@deepsearch.com', ?, 'admin', 'active', ?)
            """, (admin_hash, datetime.now().isoformat()))
            print("🔧 Demo admin added to database")
    except Exception as e:
        print(f"Warning: Could not add demo admin: {e}")
    
    conn.commit()
    
    return conn

@app.route('/api/classification/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, description, color_code, icon_name, is_active, created_at, updated_at
            FROM professional_categories 
            ORDER BY name
        """)
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'color_code': row[3],
                'icon_name': row[4],
                'is_active': bool(row[5]),
                'created_at': row[6],
                'updated_at': row[7]
            })
        
        print(f"Retrieved {len(categories)} categories from database")  # Debug log
        return jsonify({'categories': categories})
    except Exception as e:
        print(f"Error getting categories: {e}")  # Debug log
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/classification/categories', methods=['POST'])
def create_category():
    """Create new category"""
    conn = None
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug log
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Category name is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if category name already exists
        cursor.execute("SELECT id FROM professional_categories WHERE name = ?", (data['name'],))
        if cursor.fetchone():
            return jsonify({'error': 'Category name already exists'}), 400
        
        # Insert new category
        cursor.execute("""
            INSERT INTO professional_categories 
            (name, description, color_code, icon_name, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['name'],
            data.get('description', ''),
            data.get('color_code', '#6366f1'),
            data.get('icon', 'folder'),
            data.get('is_active', True),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        category_id = cursor.lastrowid
        conn.commit()  # Explicit commit
        
        print(f"Category created with ID: {category_id}")  # Debug log
        return jsonify({'success': True, 'category_id': category_id})
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating category: {e}")  # Debug log
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/classification/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update existing category"""
    conn = None
    try:
        data = request.get_json()
        print(f"Updating category {category_id} with data: {data}")  # Debug log
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if category exists
        cursor.execute("SELECT id FROM professional_categories WHERE id = ?", (category_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Category not found'}), 404
        
        # Update category
        cursor.execute("""
            UPDATE professional_categories 
            SET name = ?, description = ?, color_code = ?, icon_name = ?, updated_at = ?
            WHERE id = ?
        """, (
            data.get('name'),
            data.get('description', ''),
            data.get('color_code', '#6366f1'),
            data.get('icon', 'folder'),
            datetime.now().isoformat(),
            category_id
        ))
        
        conn.commit()  # Explicit commit
        
        print(f"Category {category_id} updated successfully")  # Debug log
        return jsonify({'success': True})
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error updating category: {e}")  # Debug log
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/classification/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete category"""
    conn = None
    try:
        print(f"Deleting category {category_id}")  # Debug log
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if category exists
        cursor.execute("SELECT id FROM professional_categories WHERE id = ?", (category_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Category not found'}), 404
        
        # Delete category
        cursor.execute("DELETE FROM professional_categories WHERE id = ?", (category_id,))
        conn.commit()  # Explicit commit
        
        print(f"Category {category_id} deleted successfully")  # Debug log
        return jsonify({'success': True})
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error deleting category: {e}")  # Debug log
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/classification/categories/<int:category_id>/stats', methods=['GET'])
def get_category_stats(category_id):
    """Get category statistics"""
    try:
        # Mock stats for testing
        stats = {
            'document_count': 5,
            'recent_activity': 2,
            'usage_trend': 'increasing'
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/classification/security-levels', methods=['GET'])
def get_security_levels():
    """Get all security levels"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, level_number, description, color_code, access_requirements, is_active, created_at
                FROM security_levels 
                ORDER BY level_number
            """)
            security_levels = []
            for row in cursor.fetchall():
                security_levels.append({
                    'id': row[0],
                    'name': row[1],
                    'level_number': row[2],
                    'description': row[3],
                    'color_code': row[4],
                    'access_requirements': row[5],
                    'is_active': bool(row[6]),
                    'created_at': row[7]
                })
            
            return jsonify({'security_levels': security_levels})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get all documents"""
    try:
        # Mock documents for testing  
        documents = [
            {
                'id': '1',
                'filename': 'sample_document.pdf',
                'title': 'Sample Document',
                'file_type': 'pdf',
                'status': 'indexed',
                'upload_date': '2024-01-01T00:00:00Z',
                'file_size': 1024000,
                'file_path': '/path/to/sample_document.pdf',
                'page_count': 5,
                'classification': {
                    'category': {
                        'id': 1,
                        'name': 'Genel',
                        'confidence': 0.95
                    },
                    'security_level': {
                        'id': 1,
                        'name': 'Genel',
                        'level_number': 1
                    },
                    'access_granted': True
                }
            },
            {
                'id': '2',
                'filename': 'technical_manual.pdf',
                'title': 'Technical Manual',
                'file_type': 'pdf',
                'status': 'processing',
                'upload_date': '2024-01-02T00:00:00Z',
                'file_size': 2048000,
                'file_path': '/path/to/technical_manual.pdf',
                'page_count': 12,
                'classification': {
                    'category': {
                        'id': 3,
                        'name': 'Teknik',
                        'confidence': 0.92
                    },
                    'security_level': {
                        'id': 2,
                        'name': 'Dahili',
                        'level_number': 2
                    },
                    'access_granted': True
                }
            }
        ]
        # Return the array directly to match frontend expectations
        return jsonify(documents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data - Working version"""
    return jsonify({
        'total_documents': 15,
        'indexed_files': 12,
        'processing_queue': 0,
        'recent_searches': 8,
        'system_health': 'good'
    })

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({'message': 'Test API working!', 'timestamp': datetime.now().isoformat()})

# Demo users for authentication
demo_users = {
    'admin': {
        'password': hashlib.sha256('admin123'.encode()).hexdigest(),
        'role': 'admin'
    },
    'manager': {
        'password': hashlib.sha256('manager123'.encode()).hexdigest(),
        'role': 'manager'
    },
    'user': {
        'password': hashlib.sha256('user123'.encode()).hexdigest(),
        'role': 'user'
    }
}

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Hash password for comparison
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        print(f"🔍 Login attempt: {username}")
        print(f"🔍 Password hash: {password_hash}")
        print(f"🔍 Demo admin hash: {demo_users.get('admin', {}).get('password', 'N/A')}")
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check user in database
            cursor.execute("""
                SELECT username, role, status, is_active 
                FROM users 
                WHERE username = ? AND password_hash = ? AND is_active = 1
            """, (username, password_hash))
            
            user = cursor.fetchone()
            
            if not user:
                # Fall back to demo users if not found in database
                if username in demo_users:
                    if demo_users[username]['password'] == password_hash:
                        user_role = demo_users[username]['role']
                        user_status = 'active'  # Demo users are always active
                    else:
                        return jsonify({'error': 'Invalid credentials'}), 401
                else:
                    return jsonify({'error': 'Invalid credentials'}), 401
            else:
                user_role = user['role']
                user_status = user['status']
                
                # Check if account is pending approval
                if user_status == 'pending':
                    return jsonify({
                        'error': 'Account pending admin approval',
                        'message': 'Your account is waiting for administrator approval. Please contact your system administrator.'
                    }), 403
            
            # Create JWT token
            payload = {
                'username': username,
                'role': user_role,
                'exp': datetime.now(UTC) + timedelta(hours=24)
            }
            token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'username': username,
                    'role': user_role
                }
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if conn:
                conn.close()
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-token', methods=['POST'])
def verify_token():
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token required'}), 400
        
        # Verify token
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        
        return jsonify({
            'valid': True,
            'user': {
                'username': payload['username'],
                'role': payload['role']
            }
        })
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    # Client-side logout (remove token from localStorage)
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    """Get all users (admin only)"""
    print("📋 Admin users endpoint called")  # Debug log
    try:
        # TODO: Add admin authentication check
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, role, requested_role, status, is_active, created_at
                FROM users 
                ORDER BY created_at DESC
            """)
            
            users = []
            for row in cursor.fetchall():
                print(f"Processing user: {row[1]}")  # Debug log
                # Skip demo users (they don't need approval)
                if row[1] in demo_users:
                    print(f"Skipping demo user: {row[1]}")  # Debug log
                    continue
                    
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'role': row[3],
                    'requested_role': row[4],
                    'status': row[5],
                    'is_active': bool(row[6]),
                    'created_at': row[7]
                })
            
            print(f"📊 Returning {len(users)} users")  # Debug log
            return jsonify({'users': users})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/approve', methods=['POST'])
def approve_user_role(user_id):
    """Approve user's requested role (admin only)"""
    try:
        print(f"🔍 Approving user {user_id}")
        # TODO: Add admin authentication check
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get user's requested role
            cursor.execute("SELECT requested_role FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            print(f"🔍 User found: {user}")
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            requested_role = user[0]
            if not requested_role:
                return jsonify({'error': 'No role request to approve'}), 400
            
            print(f"🔍 Approving role: {requested_role}")
            
            # Update user's role and status
            cursor.execute("""
                UPDATE users 
                SET role = ?, status = 'active'
                WHERE id = ?
            """, (requested_role, user_id))
            
            conn.commit()
            
            print(f"✅ User {user_id} approved as {requested_role}")
            return jsonify({'message': f'User role approved as {requested_role}'})
            
        except Exception as e:
            print(f"❌ Error approving user: {e}")
            if conn:
                conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        print(f"❌ Outer error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
def update_user_role(user_id):
    """Update user's role (admin only)"""
    try:
        # TODO: Add admin authentication check
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['user', 'manager', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'User not found'}), 404
            
            # Update user's role
            cursor.execute("""
                UPDATE users 
                SET role = ?, status = 'active'
                WHERE id = ?
            """, (new_role, user_id))
            
            conn.commit()
            
            return jsonify({'message': f'User role updated to {new_role}'})
            
        except Exception as e:
            if conn:
                conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/status', methods=['PUT'])
def update_user_status(user_id):
    """Update user's status (admin only)"""
    try:
        # TODO: Add admin authentication check
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'active', 'inactive']:
            return jsonify({'error': 'Invalid status'}), 400
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'User not found'}), 404
            
            # Update user's status
            cursor.execute("""
                UPDATE users 
                SET status = ?, is_active = ?
                WHERE id = ?
            """, (new_status, 1 if new_status == 'active' else 0, user_id))
            
            conn.commit()
            
            return jsonify({'message': f'User status updated to {new_status}'})
            
        except Exception as e:
            if conn:
                conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        requested_role = data.get('role', 'user')  # Bu artık requested_role
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email and password are required'}), 400
        
        # Validate requested role
        if requested_role not in ['user', 'manager', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if username or email already exists
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                return jsonify({'error': 'Username or email already exists'}), 409
            
            # Insert new user with pending status
            # Actual role is 'user' by default, requested_role stores what they want
            actual_role = 'user'  # Everyone starts as user
            status = 'pending' if requested_role in ['manager', 'admin'] else 'active'
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, requested_role, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, email, password_hash, actual_role, requested_role, status, datetime.now().isoformat()))
            
            conn.commit()
            
            response_message = 'User registered successfully'
            if status == 'pending':
                response_message += '. Role upgrade request pending admin approval.'
            
            return jsonify({
                'message': response_message,
                'user': {
                    'username': username,
                    'email': email,
                    'role': actual_role,
                    'requested_role': requested_role,
                    'status': status
                }
            }), 201
            
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Username or email already exists'}), 409
        except Exception as e:
            if conn:
                conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Test API Server...")
    app.run(host='0.0.0.0', port=5000, debug=False)