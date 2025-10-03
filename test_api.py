"""
Test Flask server for category API testing
"""
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, 
            static_folder='frontend-react/dist',
            static_url_path='')

# Enable CORS for all routes
CORS(app, origins=['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5001'])

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
    return conn
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
                'id': 1,
                'filename': 'sample_document.pdf',
                'title': 'Sample Document',
                'category': 'Uncategorized',
                'security_level': 'Public',
                'status': 'processed',
                'created_at': '2024-01-01T00:00:00Z',
                'file_size': 1024000,
                'metadata': {}
            }
        ]
        return jsonify({'documents': documents})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data"""
    try:
        # Mock analytics for testing
        analytics = {
            'total_documents': 10,
            'classified_documents': 7,
            'pending_classification': 3,
            'total_users': 5,
            'active_sessions': 2,
            'recent_uploads': 1
        }
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({'message': 'Test API working!', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("🚀 Starting Test API Server...")
    app.run(host='0.0.0.0', port=5001, debug=True)