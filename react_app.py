from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import json

# Create a minimal Flask app for React frontend
app = Flask(__name__, 
            static_folder='frontend-react/dist',
            static_url_path='')

# Enable CORS for React development server
CORS(app, origins=['http://localhost:5173', 'http://localhost:3000'])

@app.route('/')
def index():
    return send_from_directory('frontend-react/dist', 'index.html')

# Serve React assets
@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory('frontend-react/dist/assets', filename)

@app.route('/api/search', methods=['POST'])
def api_search():
    """Search API for React frontend"""
    try:
        print("DEBUG - API search called!")
        
        data = request.get_json()
        query = data.get('query', '').strip()
        search_type = data.get('search_type', 'semantic')
        top_k = min(data.get('top_k', 5), 5)  # Limit to max 5 results
        
        print(f"DEBUG - Query: '{query}', Top-K: {top_k}")
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        # Import search function
        from embed_index import search
        
        # Real search using FAISS
        results = search(
            query=query,
            index_path='./data/faiss.index',
            meta_path='./data/meta.pkl',
            top_k=top_k  # This should limit results
        )
        
        print(f"DEBUG - Total results from FAISS: {len(results)}")
        print(f"DEBUG - Raw results: {results}")
        
        # Format results for React frontend
        formatted_results = []
        
        # Load text chunks directly from chunks.jsonl for text content
        chunks_data = {}
        try:
            with open('./data/chunks.jsonl', 'r', encoding='utf-8') as f:
                for line in f:
                    chunk = json.loads(line.strip())
                    chunks_data[chunk['file_path']] = chunk['text']
        except Exception as e:
            print(f"Warning: Could not load chunks.jsonl: {e}")
        
        for i, result in enumerate(results):
            raw_score = float(result.get('score', 0.0))
            file_name = os.path.basename(result.get('file_path', ''))
            print(f"DEBUG [{i}] - File: {file_name}, Raw Score: {raw_score}")
            
            # FAISS Inner Product distance: LOWER score = BETTER similarity
            # Normalize to percentage where HIGHER percentage = BETTER match
            # Score range is typically 0-2, where 0 = perfect match, 2 = no match
            if raw_score <= 2.0:
                # Convert distance to similarity percentage
                # 0.0 distance -> 100% similarity
                # 2.0 distance -> 0% similarity
                similarity_percentage = round(max(0, (2.0 - raw_score) / 2.0 * 100), 1)
            else:
                # For scores > 2, treat as very low similarity
                similarity_percentage = 0.0
            
            print(f"DEBUG [{i}] - Converted to: {similarity_percentage}%")
            
            file_path = result.get('file_path', '')
            
            # Get text content from chunks.jsonl
            text_content = chunks_data.get(file_path, f"Dosya içeriği: {os.path.basename(file_path)}")
            
            formatted_results.append({
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'chunk_text': text_content[:500] + ('...' if len(text_content) > 500 else ''),
                'score': similarity_percentage,
                'metadata': {
                    'page': result.get('page', None),
                    'section': result.get('section', None)
                }
            })
        
        # Sort by similarity score in DESCENDING order (highest similarity first)
        formatted_results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"DEBUG - Final formatted results: {[(r['file_name'], r['score']) for r in formatted_results]}")
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'query': query,
            'search_type': search_type,
            'total_results': len(formatted_results)
        })
        
    except Exception as e:
        print(f"ERROR in search API: {str(e)}")
        return jsonify({'success': False, 'error': f'Search failed: {str(e)}'}), 500

@app.route('/analytics')
def analytics_api():
    """Analytics API for React frontend"""
    return jsonify({
        'total_documents': 10,
        'indexed_files': 8,
        'processing_queue': 2,
        'recent_searches': 15,
        'system_health': 'good'
    })

@app.route('/upload_file', methods=['POST'])
def upload_file():
    """File upload API for React frontend"""
    try:
        files = request.files.getlist('file')
        results = []
        
        for file in files:
            if file and file.filename:
                results.append({
                    'success': True,
                    'file_id': f"file_{len(results) + 1}",
                    'filename': file.filename
                })
        
        return jsonify({
            'success': True,
            'uploaded_files': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/rag/query', methods=['POST'])
def rag_query():
    """RAG Chat API for React frontend"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        mock_response = {
            'success': True,
            'answer': f'"{question}" sorusuna dair kapsamlı yanıt: Savunma sanayi belgelerinde bu konu ile ilgili detaylı bilgiler bulunmaktadır. Güvenlik prosedürleri çerçevesinde...',
            'sources': [
                {
                    'file_path': './example_docs/flight_manual.txt',
                    'chunk_text': 'İlgili belgede bulunan kaynak metin...',
                    'score': 0.92
                }
            ],
            'follow_up_questions': [
                'Bu konuda daha detaylı bilgi alabilir miyim?',
                'Güvenlik önlemleri nelerdir?'
            ]
        }
        
        return jsonify(mock_response)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# SPA fallback - catch all routes for React Router
@app.route('/<path:path>')
def static_files(path):
    # For all other paths, try to serve from React dist first
    try:
        return send_from_directory('frontend-react/dist', path)
    except:
        # If file not found, fallback to React index.html for client-side routing
        return send_from_directory('frontend-react/dist', 'index.html')

if __name__ == '__main__':
    print("🚀 Starting React Frontend Server...")
    print("📱 React App: http://localhost:5000")
    print("🔧 API Base: http://localhost:5000/api")
    app.run(host='0.0.0.0', port=5000, debug=True)