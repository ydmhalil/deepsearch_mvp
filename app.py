from flask import Flask, render_template, request, send_file, redirect, url_for
import os
from embed_index import search
from reporter import generate_report
from urllib.parse import quote_plus, unquote_plus
from markupsafe import escape


def safe_path(path: str) -> str:
    # Prevent path traversal: only allow files under project workspace
    base = os.path.abspath(os.path.join(os.getcwd()))
    target = os.path.abspath(path)
    if not target.startswith(base):
        raise ValueError('Invalid path')
    return target

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def do_search():
    q = request.form.get('query')
    if not q:
        return redirect(url_for('index'))
    # perform search and catch errors (e.g., missing ML deps or index)
    try:
        results = search('./data/pdf_test.index','./data/pdf_test.pkl', q, top_k=10)
        error = None
    except Exception as e:
        results = []
        error = str(e)
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
    return render_template('results.html', query=q, results=enriched, error=error)

@app.route('/report', methods=['POST'])
def make_report():
    q = request.form.get('query')
    out = './data/report_ui.txt'
    generate_report('./data/pdf_test.index','./data/pdf_test.pkl', q, out)
    return send_file(out, as_attachment=True)


@app.route('/file')
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
    return render_template('preview.html', file_name=os.path.basename(real), content=escape(content))

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # Disable Flask debug/reloader to avoid watching site-packages which can trigger
    # continuous reloads on Windows. Use a WSGI server (waitress) in production.
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
