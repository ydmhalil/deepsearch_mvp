from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash, jsonify
from flask_session import Session
import os
from embed_index import search
from reporter import generate_report
from urllib.parse import quote_plus, unquote_plus
from markupsafe import escape
from auth import login_required, admin_required, user_manager, get_current_user
from init_database import init_database, get_db_connection
from datetime import datetime


def safe_path(path: str) -> str:
    # Prevent path traversal: only allow files under project workspace
    base = os.path.abspath(os.path.join(os.getcwd()))
    target = os.path.abspath(path)
    if not target.startswith(base):
        raise ValueError('Invalid path')
    return target

# Initialize Flask app with session configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'deepsearch-mvp-secret-key-change-in-production'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './config/sessions'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Initialize session
Session(app)

# Ensure database is initialized
init_database()

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Kullanıcı adı ve şifre gerekli', 'error')
            return render_template('login.html')
        
        result = user_manager.authenticate_user(username, password)
        
        if result['success']:
            user = result['user']
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            flash(f'Hoş geldiniz, {user["username"]}!', 'success')
            
            # Redirect to next page or index
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash(result['message'], 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password or not confirm_password:
            flash('Tüm alanlar gerekli', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Şifreler eşleşmiyor', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalı', 'error')
            return render_template('register.html')
        
        result = user_manager.register_user(username, password, 'user')
        
        if result['success']:
            flash('Hesabınız başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.', 'success')
            return redirect(url_for('login'))
        else:
            flash(result['message'], 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    username = session.get('username')
    session.clear()
    flash(f'Çıkış yapıldı. Güle güle {username}!', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    current_user = get_current_user()
    return render_template('index.html', current_user=current_user)

@app.route('/search', methods=['POST'])
@login_required
def do_search():
    q = request.form.get('query')
    if not q:
        return redirect(url_for('index'))
    
    # Log the search
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        start_time = datetime.now()
    except Exception as e:
        print(f"Database logging error: {e}")
    
    # perform search and catch errors (e.g., missing ML deps or index)
    try:
        results = search('./data/pdf_test.index','./data/pdf_test.pkl', q, top_k=10)
        error = None
        
        # Log search with results count and response time
        try:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            cursor.execute('''
                INSERT INTO search_logs (user_id, query, results_count, timestamp, response_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (session.get('user_id'), q, len(results), end_time, response_time))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Search logging error: {e}")
            
    except Exception as e:
        results = []
        error = str(e)
        
        # Log failed search
        try:
            cursor.execute('''
                INSERT INTO search_logs (user_id, query, results_count, timestamp, response_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (session.get('user_id'), q, 0, datetime.now(), 0))
            conn.commit()
            conn.close()
        except Exception as db_e:
            print(f"Failed search logging error: {db_e}")
    
    # attach snippet to each result
    enriched = []
    for r in results:
        fp = r.get('file_path')
        snippet = ''
        try:
            real = safe_path(fp)
            with open(real, 'r', encoding='utf-8') as f:
                snippet = f.read(800)
        except Exception:
            snippet = ''
        
        # Extract chunk metadata for UI
        chunk_info = None
        if r.get('meta'):
            chunk_info = {
                'file_type': r['meta'].get('file_type', 'unknown'),
                'chunk_type': r['meta'].get('chunk_type', 'unknown'),
                'structure_type': r['meta'].get('structure_type', 'unknown'),
                'chunk_index': r['meta'].get('chunk_index', 0),
                'total_chunks': r['meta'].get('total_chunks', 1)
            }
        
        enriched.append({
            'score': r.get('score'),
            'file_path': fp,
            'file_name': os.path.basename(fp),
            'snippet': snippet,
            'chunk_info': chunk_info,
            'download_url': '/file?path=' + quote_plus(fp)
        })
    
    current_user = get_current_user()
    return render_template('results.html', query=q, results=enriched, error=error, current_user=current_user)

@app.route('/report', methods=['POST'])
@login_required
def make_report():
    q = request.form.get('query')
    out = './data/report_ui.txt'
    generate_report('./data/pdf_test.index','./data/pdf_test.pkl', q, out)
    return send_file(out, as_attachment=True)


@app.route('/file')
@login_required
def serve_file():
    p = request.args.get('path')
    if not p:
        return 'missing path', 400
    try:
        real = safe_path(unquote_plus(p))
    except Exception:
        return 'invalid path', 400
    if not os.path.exists(real):
        return 'not found', 404
    return send_file(real, as_attachment=True)


@app.route('/preview')
@login_required
def preview():
    p = request.args.get('path')
    if not p:
        return 'missing path', 400
    try:
        real = safe_path(unquote_plus(p))
    except Exception:
        return 'invalid path', 400
    if not os.path.exists(real):
        return 'not found', 404
    # Only allow small previews (first 50k chars) to avoid memory issues
    try:
        with open(real, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(50000)
    except Exception:
        return 'unable to read file', 500
    # escape content to avoid HTML injection
    current_user = get_current_user()
    return render_template('preview.html', file_name=os.path.basename(real), content=escape(content), current_user=current_user)

# User profile and admin routes
@app.route('/profile')
@login_required
def profile():
    current_user = get_current_user()
    return render_template('profile.html', current_user=current_user)

@app.route('/admin')
@admin_required
def admin_panel():
    users = user_manager.get_all_users(include_inactive=True)
    current_user = get_current_user()
    return render_template('admin.html', users=users, current_user=current_user)

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # Disable Flask debug/reloader to avoid watching site-packages which can trigger
    # continuous reloads on Windows. Use a WSGI server (waitress) in production.
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
