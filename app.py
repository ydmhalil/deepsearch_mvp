from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash, jsonify, make_response
from flask_session import Session
import os
import time
from embed_index import search
from reporter import generate_report
from urllib.parse import quote_plus, unquote_plus
from markupsafe import escape
from auth import login_required, admin_required, user_manager, get_current_user
from init_database import init_database, get_db_connection
from upload_manager import upload_manager
from advanced_search import search_manager
from search_optimizer import search_optimizer
from kobi_reporting import kobi_reporting
from document_insights import insights_engine
from security_manager import security_manager
from database_optimizer import db_optimizer, get_optimized_user_documents, get_dashboard_analytics_optimized
from faiss_optimizer import faiss_optimizer
from resource_manager import memory_manager, resource_manager, optimize_system_performance, get_system_health
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

# Initialize security tables
security_manager.initialize_security_tables()

# Security middleware
@app.before_request
def security_middleware():
    """Apply security checks to all requests"""
    
    # Skip security checks for static files
    if request.endpoint and request.endpoint.startswith('static'):
        return
    
    # Rate limiting
    endpoint = request.endpoint or 'unknown'
    rate_check = security_manager.check_rate_limit(endpoint)
    if not rate_check['allowed']:
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': rate_check.get('message', 'Too many requests'),
            'reset_time': rate_check.get('reset_time')
        }), 429
    
    # Input validation for POST/PUT requests
    if request.method in ['POST', 'PUT'] and request.content_type:
        if 'application/json' in request.content_type:
            try:
                json_data = request.get_json()
                if json_data:
                    for key, value in json_data.items():
                        if isinstance(value, str):
                            validation = security_manager.validate_input(value, 'general')
                            if not validation['is_valid']:
                                security_manager.log_security_event(
                                    'malicious_input_blocked',
                                    f"Blocked malicious input in {key}: {validation['threats_detected']}",
                                    'high'
                                )
                                return jsonify({
                                    'error': 'Invalid input detected',
                                    'message': 'Request contains potentially malicious content'
                                }), 400
            except:
                pass  # Invalid JSON, let the endpoint handle it
        
        elif 'application/x-www-form-urlencoded' in request.content_type:
            for key, value in request.form.items():
                validation = security_manager.validate_input(value, 'general')
                if not validation['is_valid']:
                    security_manager.log_security_event(
                        'malicious_input_blocked',
                        f"Blocked malicious form input in {key}: {validation['threats_detected']}",
                        'high'
                    )
                    flash('Güvenlik nedeniyle istek engellendi', 'error')
                    return redirect(request.referrer or url_for('index'))

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "font-src 'self' https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self';"
    )
    return response

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Input validation
        if not username or not password:
            flash('Kullanıcı adı ve şifre gerekli', 'error')
            return render_template('login.html')
        
        # Validate username for security threats
        username_validation = security_manager.validate_input(username, 'general')
        if not username_validation['is_valid']:
            security_manager.log_security_event(
                'malicious_login_attempt',
                f"Malicious username detected: {username_validation['threats_detected']}",
                'high'
            )
            flash('Geçersiz kullanıcı adı formatı', 'error')
            return render_template('login.html')
        
        # Check if account is locked due to failed attempts
        if not security_manager.track_login_attempt(username, False):  # Pre-check
            flash('Hesap geçici olarak kilitli. Lütfen daha sonra tekrar deneyin.', 'error')
            return render_template('login.html')
        
        # Attempt authentication
        result = user_manager.authenticate_user(username, password)
        
        # Track the actual login result
        login_allowed = security_manager.track_login_attempt(username, result['success'])
        
        if result['success'] and login_allowed:
            user = result['user']
            
            # Create secure session
            session_token = security_manager.create_secure_session(user['id'])
            if session_token:
                session['session_token'] = session_token
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                
                # Log successful login
                security_manager.log_security_event(
                    'successful_login',
                    f"User {username} logged in successfully",
                    'low'
                )
                
                flash(f'Hoş geldiniz, {user["username"]}!', 'success')
                
                # Redirect to next page or index
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('index'))
            else:
                flash('Oturum oluşturulamadı. Lütfen tekrar deneyin.', 'error')
        else:
            if not login_allowed:
                flash('Çok fazla başarısız deneme. Hesap geçici olarak kilitli.', 'error')
            else:
                flash(result['message'], 'error')
            
            # Log failed login
            security_manager.log_security_event(
                'failed_login',
                f"Failed login attempt for {username}",
                'medium'
            )
    
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
    session_token = session.get('session_token')
    
    # Invalidate session in database
    if session_token:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE user_sessions 
                SET is_active = FALSE 
                WHERE session_token = ?
            ''', (session_token,))
            conn.commit()
        except Exception as e:
            print(f"Session invalidation error: {e}")
        finally:
            conn.close()
    
    # Log logout event
    security_manager.log_security_event(
        'user_logout',
        f"User {username} logged out",
        'low'
    )
    
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
    q = request.form.get('query', '').strip()
    if not q:
        return redirect(url_for('index'))
    
    # Security validation for search query
    query_validation = security_manager.validate_input(q, 'search_query')
    if not query_validation['is_valid']:
        security_manager.log_security_event(
            'malicious_search_blocked',
            f"Blocked malicious search query: {query_validation['threats_detected']}",
            'medium'
        )
        flash('Güvenlik nedeniyle arama engellendi', 'error')
        return redirect(url_for('index'))
    
    # Use sanitized query
    q = query_validation['sanitized']
    
    # Parse filters from form
    filters = {}
    
    # File type filters
    file_types = request.form.getlist('file_types')
    if file_types:
        filters['file_types'] = file_types
    
    # Date range filters
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    
    # Additional filters
    if request.form.get('indexed_only'):
        filters['indexed_only'] = True
    if request.form.get('user_files_only'):
        filters['user_files_only'] = True
    
    # Check cache first - DISABLED FOR DEBUGGING
    current_user = get_current_user()
    # cached_results = search_optimizer.get_cached_result(q, filters)
    cached_results = None  # Force fresh search every time
    
    if cached_results:
        results = cached_results
        error = None
    else:
        # Perform enterprise search
        try:
            print(f"DEBUG: Performing enterprise search for query: '{q}'")
            
            # Use enterprise search engine
            try:
                from enterprise_search import get_enterprise_search_engine
                enterprise_search = get_enterprise_search_engine()
                
                # Convert filters to enterprise format
                top_k = filters.get('limit', 20) if filters else 20
                
                # Perform enterprise search
                search_results = enterprise_search.search(q, top_k=top_k, filters=filters)
                
                # Convert enterprise results to legacy format for compatibility
                results = []
                for result in search_results:
                    results.append({
                        'file_path': result.file_path,
                        'snippet': result.snippet,
                        'score': result.score,
                        'chunk_id': result.chunk_id,
                        'metadata': result.metadata,
                        'relevance_factors': result.relevance_factors
                    })
                
                print(f"DEBUG: Enterprise search results count: {len(results)}")
                for i, r in enumerate(results[:3]):
                    score = r.get('score', 0)
                    file_name = r.get('file_path', 'unknown').split('\\')[-1]
                    search_type = r.get('metadata', {}).get('search_type', 'unknown')
                    print(f"DEBUG: Result {i+1}: {file_name} - Score: {score:.3f} - Type: {search_type}")
                
            except Exception as enterprise_error:
                print(f"DEBUG: Enterprise search failed, falling back to legacy: {enterprise_error}")
                # Fallback to legacy search
                results = search_manager.search_with_filters(
                    q, 
                    filters=filters if filters else None,
                    user_id=session.get('user_id')
                )
            
            # Cache the results
            search_optimizer.cache_search_result(q, filters, results)
            
            error = None
        except Exception as e:
            results = []
            error = str(e)
    
    # Process results for display
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
        
        # Get document info if available
        doc_info = r.get('doc_info', {})
        
        enriched.append({
            'score': r.get('enhanced_score', r.get('similarity', r.get('score', 0))),
            'file_path': fp,
            'file_name': os.path.basename(fp),
            'snippet': snippet,
            'chunk_info': chunk_info,
            'doc_info': doc_info,
            'download_url': '/file?path=' + quote_plus(fp)
        })
    
    current_user = get_current_user()
    response = make_response(render_template('results.html', 
                         query=q, 
                         results=enriched, 
                         error=error, 
                         current_user=current_user,
                         applied_filters=filters,
                         search_timestamp=time.time()))
    
    # Prevent caching of search results
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

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

# File upload routes
@app.route('/upload')
@login_required
def upload_page():
    """File upload interface"""
    current_user = get_current_user()
    uploaded_files = upload_manager.get_uploaded_files(
        user_id=current_user['id'] if current_user['role'] != 'admin' else None,
        include_all=current_user['role'] == 'admin'
    )
    upload_stats = upload_manager.get_upload_stats()
    return render_template('upload.html', 
                         current_user=current_user, 
                         uploaded_files=uploaded_files,
                         upload_stats=upload_stats)

@app.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload with security validation"""
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': 'Dosya seçilmedi'})
    
    files = request.files.getlist('files')
    results = []
    
    for file in files:
        # Security validation
        if file.filename:
            file_validation = security_manager.validate_file_upload(file, file.filename)
            
            if not file_validation['is_valid']:
                # Log security event
                security_manager.log_security_event(
                    'malicious_file_upload_blocked',
                    f"Blocked file upload: {file.filename} - Threats: {file_validation['threats_detected']}",
                    'high'
                )
                
                results.append({
                    'filename': file.filename,
                    'result': {
                        'success': False, 
                        'message': f'Güvenlik nedeniyle dosya reddedildi: {", ".join(file_validation["threats_detected"])}'
                    }
                })
                continue
            
            # Use sanitized filename
            original_filename = file.filename
            file.filename = file_validation['sanitized_filename']
            
            # Proceed with upload
            result = upload_manager.save_uploaded_file(file, session.get('user_id'))
            
            # Log successful upload
            if result['success']:
                security_manager.log_security_event(
                    'file_upload_success',
                    f"File uploaded successfully: {file.filename} (original: {original_filename})",
                    'low'
                )
            
            results.append({
                'filename': original_filename,
                'result': result
            })
        else:
            results.append({
                'filename': 'Unknown',
                'result': {'success': False, 'message': 'Geçersiz dosya adı'}
            })
    
    return jsonify({'success': True, 'results': results})

@app.route('/delete_file/<int:document_id>', methods=['POST'])
@login_required
def delete_file(document_id):
    """Delete uploaded file"""
    current_user = get_current_user()
    result = upload_manager.delete_file(
        document_id, 
        current_user['id'],
        is_admin=current_user['role'] == 'admin'
    )
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')
    
    return redirect(url_for('upload_page'))

@app.route('/index_file/<int:document_id>', methods=['POST'])
@login_required
def index_file(document_id):
    """Index uploaded file for search"""
    result = upload_manager.process_file_for_indexing(document_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')
    
    return redirect(url_for('upload_page'))

@app.route('/upload_stats')
@login_required
def upload_stats_api():
    """Get upload statistics (AJAX)"""
    stats = upload_manager.get_upload_stats()
    return jsonify(stats)

# Search API endpoints
@app.route('/search_suggestions')
@login_required
def search_suggestions():
    """Get search suggestions (AJAX)"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    # Use optimized suggestions with user personalization
    current_user = get_current_user()
    suggestions = search_optimizer.get_search_suggestions(
        query, 
        user_id=current_user['id'],
        limit=5
    )
    return jsonify({'suggestions': suggestions})

@app.route('/popular_searches')
@login_required
def popular_searches():
    """Get popular searches (AJAX)"""
    popular = search_manager.get_popular_searches(days=30, limit=5)
    return jsonify({'popular': popular})

@app.route('/search_analytics')
@login_required
def search_analytics():
    """Get search analytics (AJAX)"""
    current_user = get_current_user()
    user_id = None if current_user['role'] == 'admin' else current_user['id']
    
    analytics = search_manager.get_search_analytics(user_id=user_id, days=30)
    return jsonify(analytics)

# Search history and bookmarks
@app.route('/search_history')
@login_required
def search_history_page():
    """Search history page"""
    current_user = get_current_user()
    user_id = current_user['id']
    
    # Get recent searches
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT query, results_count, timestamp, response_time, filters
        FROM search_logs 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 20
    ''', (user_id,))
    
    recent_searches = [dict(row) for row in cursor.fetchall()]
    
    # Get saved searches
    cursor.execute('''
        SELECT id, name, query, filters, created_at, last_used, use_count
        FROM saved_searches 
        WHERE user_id = ? 
        ORDER BY last_used DESC, created_at DESC
    ''', (user_id,))
    
    saved_searches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Get analytics
    analytics = search_manager.get_search_analytics(user_id=user_id, days=30)
    
    return render_template('search_history.html',
                         current_user=current_user,
                         recent_searches=recent_searches,
                         saved_searches=saved_searches,
                         analytics=analytics)

@app.route('/save_search', methods=['POST'])
@login_required
def save_search():
    """Save a search as bookmark"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        query = data.get('query', '').strip()
        filters = data.get('filters', '')
        
        if not name or not query:
            return jsonify({'success': False, 'message': 'İsim ve sorgu gerekli'})
        
        current_user = get_current_user()
        user_id = current_user['id']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if already exists
        cursor.execute('''
            SELECT id FROM saved_searches 
            WHERE user_id = ? AND name = ?
        ''', (user_id, name))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Bu isimde bir kayıt zaten var'})
        
        # Save search
        cursor.execute('''
            INSERT INTO saved_searches (user_id, name, query, filters, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, name, query, filters, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Arama başarıyla kaydedildi'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Kaydetme hatası: {str(e)}'})

@app.route('/delete_saved_search/<int:search_id>', methods=['DELETE'])
@login_required
def delete_saved_search(search_id):
    """Delete a saved search"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete only user's own saved searches
        cursor.execute('''
            DELETE FROM saved_searches 
            WHERE id = ? AND user_id = ?
        ''', (search_id, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Kayıt bulunamadı'})
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Kayıt başarıyla silindi'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Silme hatası: {str(e)}'})

@app.route('/use_saved_search/<int:search_id>', methods=['POST'])
@login_required
def use_saved_search(search_id):
    """Use a saved search (update usage stats)"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update usage stats
        cursor.execute('''
            UPDATE saved_searches 
            SET last_used = ?, use_count = use_count + 1
            WHERE id = ? AND user_id = ?
        ''', (datetime.now(), search_id, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# KOBİ Dashboard Routes
@app.route('/kobi/dashboard')
@login_required
def kobi_dashboard():
    """KOBİ business intelligence dashboard"""
    current_user = get_current_user()
    
    # Generate dashboard data
    dashboard_data = kobi_reporting.generate_business_dashboard_data(
        company_id=None,  # For now, show all data
        date_range=30
    )
    
    current_time = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    return render_template('kobi_dashboard.html',
                         current_user=current_user,
                         dashboard_data=dashboard_data,
                         current_time=current_time)

@app.route('/kobi/export/pdf')
@login_required
def export_dashboard_pdf():
    """Export dashboard as PDF"""
    try:
        dashboard_data = kobi_reporting.generate_business_dashboard_data(date_range=30)
        pdf_path = kobi_reporting.generate_pdf_report(dashboard_data)
        
        if pdf_path and os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True, download_name='kobi_dashboard.pdf')
        else:
            flash('PDF raporu oluşturulamadı', 'error')
            return redirect(url_for('kobi_dashboard'))
    except Exception as e:
        flash(f'PDF export hatası: {str(e)}', 'error')
        return redirect(url_for('kobi_dashboard'))

@app.route('/kobi/export/excel')
@login_required
def export_dashboard_excel():
    """Export dashboard as Excel"""
    try:
        dashboard_data = kobi_reporting.generate_business_dashboard_data(date_range=30)
        excel_path = kobi_reporting.generate_excel_report(dashboard_data)
        
        if excel_path and os.path.exists(excel_path):
            return send_file(excel_path, as_attachment=True, download_name='kobi_dashboard.xlsx')
        else:
            flash('Excel raporu oluşturulamadı', 'error')
            return redirect(url_for('kobi_dashboard'))
    except Exception as e:
        flash(f'Excel export hatası: {str(e)}', 'error')
        return redirect(url_for('kobi_dashboard'))

@app.route('/kobi/generate_report/<format>/<type>', methods=['POST'])
@login_required
def generate_custom_report(format, type):
    """Generate custom report"""
    try:
        dashboard_data = kobi_reporting.generate_business_dashboard_data(date_range=30)
        
        if format == 'pdf':
            report_title = "Yönetici Özet Raporu" if type == 'executive' else "KOBİ Detay Raporu"
            file_path = kobi_reporting.generate_pdf_report(dashboard_data, report_title)
            download_name = 'executive_report.pdf' if type == 'executive' else 'detailed_report.pdf'
        elif format == 'excel':
            report_title = "Yönetici Özet Raporu" if type == 'executive' else "KOBİ Detay Raporu"
            file_path = kobi_reporting.generate_excel_report(dashboard_data, report_title)
            download_name = 'executive_report.xlsx' if type == 'executive' else 'detailed_report.xlsx'
        else:
            return jsonify({'success': False, 'message': 'Geçersiz format'})
        
        if file_path and os.path.exists(file_path):
            # Return download URL
            filename = os.path.basename(file_path)
            return jsonify({
                'success': True,
                'download_url': f'/kobi/download_report/{filename}',
                'filename': filename
            })
        else:
            return jsonify({'success': False, 'message': 'Rapor oluşturulamadı'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/kobi/download_report/<filename>')
@login_required
def download_report(filename):
    """Download generated report"""
    try:
        file_path = os.path.join(kobi_reporting.reports_dir, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            flash('Rapor dosyası bulunamadı', 'error')
            return redirect(url_for('kobi_dashboard'))
    except Exception as e:
        flash(f'Download hatası: {str(e)}', 'error')
        return redirect(url_for('kobi_dashboard'))

@app.route('/kobi/recent_reports')
@login_required
def get_recent_reports():
    """Get list of recent reports"""
    try:
        reports = []
        reports_dir = kobi_reporting.reports_dir
        
        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                if filename.endswith(('.pdf', '.xlsx')):
                    file_path = os.path.join(reports_dir, filename)
                    stat = os.stat(file_path)
                    
                    # Determine report type
                    if 'executive' in filename:
                        report_type = 'Yönetici Özet'
                    elif 'detail' in filename:
                        report_type = 'Detaylı Analiz'
                    elif filename.endswith('.pdf'):
                        report_type = 'PDF Rapor'
                    else:
                        report_type = 'Excel Rapor'
                    
                    reports.append({
                        'filename': filename,
                        'type': report_type,
                        'created_at': datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y %H:%M'),
                        'size': f"{stat.st_size / 1024:.1f} KB",
                        'download_url': f'/kobi/download_report/{filename}'
                    })
        
        # Sort by creation time (newest first)
        reports.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({'reports': reports[:10]})  # Last 10 reports
        
    except Exception as e:
        return jsonify({'reports': [], 'error': str(e)})

# Document Insights Routes
@app.route('/insights/dashboard')
@login_required
def insights_dashboard():
    """Document insights and business intelligence dashboard"""
    current_user = get_current_user()
    
    # Generate content trends and insights
    content_trends = insights_engine.generate_content_trends(days_back=30)
    
    # Get business recommendations
    analysis_data = {
        'content_trends': content_trends,
        'document_analytics': kobi_reporting.generate_business_dashboard_data()['document_analytics']
    }
    
    recommendations = insights_engine.generate_business_recommendations(analysis_data)
    
    return render_template('insights_dashboard.html',
                         current_user=current_user,
                         content_trends=content_trends,
                         recommendations=recommendations,
                         analysis_data=analysis_data)

@app.route('/insights/analyze_document', methods=['POST'])
@login_required
def analyze_document():
    """Analyze a specific document and return insights"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({'success': False, 'message': 'Dosya yolu gerekli'})
        
        # Read document content
        try:
            with open(safe_path(file_path), 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(safe_path(file_path), 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Perform analysis
        analysis = insights_engine.analyze_document_content(file_path, content)
        
        # Save analysis to database
        insights_engine.save_analysis_to_db(analysis)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Analiz hatası: {str(e)}'})

@app.route('/insights/content_trends')
@login_required
def get_content_trends():
    """Get content trends analysis (AJAX)"""
    try:
        days = request.args.get('days', 30, type=int)
        trends = insights_engine.generate_content_trends(days_back=days)
        return jsonify(trends)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/insights/document_analysis/<path:filename>')
@login_required
def get_document_analysis(filename):
    """Get stored analysis for a specific document"""
    try:
        analysis = insights_engine.get_analysis_from_db(filename)
        if analysis:
            return jsonify({'success': True, 'analysis': analysis})
        else:
            return jsonify({'success': False, 'message': 'Analiz bulunamadı'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/insights/recommendations')
@login_required
def get_recommendations():
    """Get business recommendations based on current data"""
    try:
        # Get current trends and analytics
        content_trends = insights_engine.generate_content_trends(days_back=30)
        dashboard_data = kobi_reporting.generate_business_dashboard_data()
        
        analysis_data = {
            'content_trends': content_trends,
            'document_analytics': dashboard_data['document_analytics'],
            'user_productivity': dashboard_data['user_productivity']
        }
        
        recommendations = insights_engine.generate_business_recommendations(analysis_data)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'analysis_summary': {
                'total_trends': len(content_trends.get('topic_trends', {})),
                'content_gaps': len(content_trends.get('content_demand', [])),
                'peak_usage_time': content_trends.get('time_patterns', {}).get('peak_hours', [None])[0]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Security Dashboard Routes
@app.route('/security/dashboard')
@admin_required
def security_dashboard():
    """Security monitoring dashboard for admins"""
    current_user = get_current_user()
    
    # Get security summary
    security_summary = security_manager.get_security_summary(days=7)
    
    return render_template('security_dashboard.html',
                         current_user=current_user,
                         security_summary=security_summary)

@app.route('/security/events')
@admin_required
def get_security_events():
    """Get security events (AJAX)"""
    try:
        days = request.args.get('days', 7, type=int)
        summary = security_manager.get_security_summary(days=days)
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/admin/performance')
@admin_required
def performance_dashboard():
    """Performance monitoring dashboard"""
    current_user = get_current_user()
    
    # Get database performance stats
    db_stats = db_optimizer.get_performance_stats()
    
    # Get FAISS performance stats
    search_stats = faiss_optimizer.get_performance_stats()
    
    # Get system health
    system_health = get_system_health()
    
    return render_template('performance_dashboard.html',
                         current_user=current_user,
                         db_stats=db_stats,
                         search_stats=search_stats,
                         system_health=system_health)

@app.route('/admin/performance/api')
@admin_required
def get_performance_stats():
    """Get performance statistics (AJAX)"""
    try:
        return jsonify({
            'database': db_optimizer.get_performance_stats(),
            'search': faiss_optimizer.get_performance_stats(),
            'system': get_system_health()
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/admin/optimize', methods=['POST'])
@admin_required
def optimize_system():
    """Run system optimization"""
    try:
        optimize_system_performance()
        return jsonify({'success': True, 'message': 'Sistem optimizasyonu tamamlandı'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # Disable Flask debug/reloader to avoid watching site-packages which can trigger
    # continuous reloads on Windows. Use a WSGI server (waitress) in production.
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
