from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import json
import re
from typing import List, Dict, Tuple
from classification_manager import classification_manager
from upload_manager import upload_manager

def find_keyword_matches(text: str, query: str) -> List[Dict]:
    """Metinde arama kelimelerinin geçtiği bölümleri bulur"""
    matches = []
    query_words = query.lower().split()
    
    # Metni cümlelere böl
    sentences = re.split(r'[.!?]+', text)
    
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_lower = sentence.lower()
        matched_words = []
        
        # Her kelimeyi kontrol et
        for word in query_words:
            if word in sentence_lower:
                matched_words.append(word)
        
        # Eğer en az bir kelime eşleşirse
        if matched_words:
            # Context için önceki ve sonraki cümleleri de al
            context_start = max(0, i - 1)
            context_end = min(len(sentences), i + 2)
            context = '. '.join(sentences[context_start:context_end]).strip()
            
            matches.append({
                'sentence': sentence,
                'context': context[:300] + ('...' if len(context) > 300 else ''),
                'matched_words': matched_words,
                'match_count': len(matched_words),
                'sentence_index': i
            })
    
    # En çok eşleşen cümleleri döndür (max 3)
    matches.sort(key=lambda x: x['match_count'], reverse=True)
    return matches[:3]

def calculate_semantic_relevance(query: str, text: str) -> Dict:
    """Sorgu ile metin arasındaki anlam ilişkisini değerlendirir"""
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Basit anahtar kelime analizi
    keywords = query_lower.split()
    total_words = len(text_lower.split())
    
    # Exact matches
    exact_matches = sum(1 for word in keywords if word in text_lower)
    
    # Semantic categories (domain-specific)
    financial_terms = ['finansal', 'rapor', 'gelir', 'gider', 'kar', 'zarar', 'bilanço', 'bütçe', 'maliyet']
    security_terms = ['güvenlik', 'koruma', 'siber', 'siber güvenlik', 'protokol', 'şifre', 'erişim']
    technical_terms = ['roket', 'motor', 'teknoloji', 'sistem', 'mühendislik', 'tasarım', 'test']
    
    category_matches = {
        'finansal': sum(1 for term in financial_terms if term in text_lower),
        'güvenlik': sum(1 for term in security_terms if term in text_lower),
        'teknik': sum(1 for term in technical_terms if term in text_lower)
    }
    
    # Dominant category
    dominant_category = max(category_matches.items(), key=lambda x: x[1])
    
    return {
        'exact_keyword_matches': exact_matches,
        'total_keywords': len(keywords),
        'match_ratio': round(exact_matches / len(keywords) * 100, 1) if keywords else 0,
        'word_density': round(exact_matches / total_words * 100, 2) if total_words > 0 else 0,
        'dominant_category': dominant_category[0] if dominant_category[1] > 0 else 'genel',
        'category_strength': dominant_category[1]
    }

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
    """Search API for React frontend with classification filtering"""
    try:
        print("DEBUG - API search called!")
        
        data = request.get_json()
        query = data.get('query', '').strip()
        search_type = data.get('search_type', 'semantic')
        top_k = min(data.get('top_k', 5), 5)  # Limit to max 5 results
        user_id = data.get('user_id', 1)  # Default admin user for testing
        category_filter = data.get('category_filter', [])  # List of category IDs
        security_level_filter = data.get('security_level_filter', [])  # List of security level IDs
        
        print(f"DEBUG - Query: '{query}', Top-K: {top_k}, User: {user_id}")
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        # Import search function
        from embed_index import search
        
        # Real search using FAISS
        results = search(
            query=query,
            index_path='./data/faiss.index',
            meta_path='./data/meta.pkl',
            top_k=top_k,  # This should limit results
            use_domain_embedding=True  # Use same embedding as index building
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
            
            # ** YENİ: Kelime eşleşmeleri ve anlam analizi **
            keyword_matches = find_keyword_matches(text_content, query)
            semantic_analysis = calculate_semantic_relevance(query, text_content)
            
            # Bölüm bilgisini belirle
            section_info = result.get('section', 'Belirtilmemiş')
            if not section_info or section_info == 'None':
                # İlk cümleden bölüm adını tahmin et
                first_sentence = text_content.split('.')[0][:100]
                section_info = first_sentence if len(first_sentence) > 10 else 'Giriş Bölümü'
            
            # ** YENİ: Auto-classify document for search results **
            document_id = i + 1  # Temporary document ID for demo
            auto_classification = classification_manager.auto_classify_document(
                document_content=text_content,
                document_id=document_id,
                classified_by=user_id
            )
            
            # Check user access to this document
            if auto_classification:
                # Create a temporary document classification record for access check
                temp_doc_classification = {
                    'category_id': auto_classification['category_id'],
                    'security_level_id': auto_classification['security_level_id'],
                    'level_number': next((sl['level_number'] for sl in classification_manager.get_security_levels() 
                                         if sl['id'] == auto_classification['security_level_id']), 1),
                    'category_name': auto_classification['category_name'],
                    'security_level_name': auto_classification['security_level_name']
                }
                
                # Check access
                user_perms = classification_manager.get_user_permissions(user_id)
                user_categories = [cat['category_id'] for cat in user_perms['categories']]
                user_max_level = user_perms['max_security_level']
                
                category_access = temp_doc_classification['category_id'] in user_categories
                security_access = user_max_level >= temp_doc_classification['level_number']
                has_access = category_access and security_access
                
                # Apply category and security level filters
                if category_filter and temp_doc_classification['category_id'] not in category_filter:
                    continue
                if security_level_filter and temp_doc_classification['security_level_id'] not in security_level_filter:
                    continue
                
                # Skip if user doesn't have access
                if not has_access:
                    print(f"DEBUG [{i}] - Access denied for user {user_id}")
                    continue
                
                classification_info = {
                    'category': {
                        'id': auto_classification['category_id'],
                        'name': auto_classification['category_name'],
                        'confidence': auto_classification['confidence']
                    },
                    'security_level': {
                        'id': auto_classification['security_level_id'],
                        'name': auto_classification['security_level_name'],
                        'level_number': temp_doc_classification['level_number']
                    },
                    'access_granted': True
                }
            else:
                # Default open access for unclassified documents
                classification_info = {
                    'category': {'id': 0, 'name': 'Sınıflandırılmamış', 'confidence': 0.0},
                    'security_level': {'id': 1, 'name': 'Açık', 'level_number': 1},
                    'access_granted': True
                }
            
            formatted_results.append({
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'chunk_text': text_content[:500] + ('...' if len(text_content) > 500 else ''),
                'score': similarity_percentage,
                'metadata': {
                    'page': result.get('page', None),
                    'section': section_info
                },
                # ** YENİ ALANLAR **
                'keyword_matches': keyword_matches,
                'semantic_analysis': semantic_analysis,
                'highlights': {
                    'matched_words': list(set([word for match in keyword_matches for word in match['matched_words']])),
                    'best_context': keyword_matches[0]['context'] if keyword_matches else text_content[:200] + '...'
                },
                # ** CLASSIFICATION INFO **
                'classification': classification_info
            })
        
        # Sort by similarity score in DESCENDING order (highest similarity first)
        formatted_results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"DEBUG - Final formatted results: {[(r['file_name'], r['score']) for r in formatted_results]}")
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'query': query,
            'search_type': search_type,
            'total_results': len(formatted_results),
            'filtered_by_permissions': True,
            'user_permissions': classification_manager.get_user_permissions(user_id)
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in search API: {str(e)}")
        print(f"Full traceback: {error_trace}")
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
    """File upload API for React frontend with database storage"""
    try:
        print("DEBUG - Upload file API called!")
        
        # Get user ID (default to admin for testing)
        user_id = request.form.get('user_id', 1)
        
        files = request.files.getlist('file')
        results = []
        
        if not files or not any(file.filename for file in files):
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        for file in files:
            if file and file.filename:
                print(f"DEBUG - Processing file: {file.filename}")
                
                # Save file using upload manager
                upload_result = upload_manager.save_uploaded_file(file, user_id)
                
                if upload_result['success']:
                    print(f"DEBUG - File saved: {upload_result}")
                    
                    # Process and index the file
                    process_result = upload_manager.process_file(upload_result['document_id'])
                    
                    # Auto-classify if processing succeeded
                    classification_result = None
                    if process_result.get('success'):
                        try:
                            # Get text content for classification
                            text_content = process_result.get('text_content', '')
                            
                            if text_content.strip():
                                classification_result = classification_manager.auto_classify_document(
                                    document_content=text_content,
                                    document_id=upload_result['document_id'],
                                    classified_by=user_id
                                )
                                print(f"DEBUG - Auto-classification: {classification_result}")
                                
                                # If auto-classification failed, set default values
                                if not classification_result:
                                    classification_result = {
                                        'category_name': 'Sınıflandırılmamış',
                                        'security_level_name': 'Açık',
                                        'confidence': 0.0,
                                        'message': 'Could not auto-classify document'
                                    }
                        except Exception as e:
                            print(f"DEBUG - Auto-classification failed: {e}")
                            classification_result = {
                                'category_name': 'Hata',
                                'security_level_name': 'Açık', 
                                'confidence': 0.0,
                                'error': str(e)
                            }
                    
                    results.append({
                        'success': True,
                        'document_id': upload_result['document_id'],
                        'filename': upload_result['filename'],
                        'file_size': upload_result['file_size'],
                        'file_type': upload_result.get('file_type', 'unknown'),
                        'processing': process_result,
                        'classification': classification_result,
                        'message': 'File uploaded and processed successfully'
                    })
                else:
                    print(f"DEBUG - Upload failed: {upload_result}")
                    results.append({
                        'success': False,
                        'filename': file.filename,
                        'error': upload_result.get('message', 'Upload failed')
                    })
        
        # Check if we need to rebuild FAISS index
        successful_uploads = [r for r in results if r['success']]
        if successful_uploads:
            print("DEBUG - Rebuilding FAISS index...")
            try:
                # Trigger FAISS index rebuild
                rebuild_result = rebuild_search_index()
                print(f"DEBUG - Index rebuild result: {rebuild_result}")
            except Exception as e:
                print(f"DEBUG - Index rebuild failed: {e}")
        
        return jsonify({
            'success': len(successful_uploads) > 0,
            'uploaded_files': results,
            'total_uploaded': len(successful_uploads),
            'total_failed': len(results) - len(successful_uploads)
        })
        
    except Exception as e:
        print(f"ERROR in upload API: {str(e)}")
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'}), 500

def rebuild_search_index():
    """Rebuild FAISS search index with all processed documents"""
    try:
        # Use existing embed_index.py build functionality
        from embed_index import build_index
        
        chunks_file = './data/chunks.jsonl'
        index_file = './data/faiss.index'
        meta_file = './data/meta.pkl'
        
        # Check if chunks file exists and has content
        if not os.path.exists(chunks_file):
            return {'success': False, 'error': 'No chunks file found'}
        
        # Build the index
        result = build_index(
            chunks_path=chunks_file,
            index_path=index_file,
            meta_path=meta_file
        )
        
        return {
            'success': True,
            'index_file': index_file,
            'meta_file': meta_file,
            'message': 'Search index rebuilt successfully'
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Index rebuild failed: {str(e)}'}

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get list of uploaded documents"""
    try:
        user_id = request.args.get('user_id', 1)
        documents = upload_manager.get_user_documents(user_id)
        
        # Add classification info to each document
        for doc in documents:
            classification = classification_manager.get_document_classification(doc['id'])
            doc['classification'] = classification
        
        return jsonify({
            'success': True,
            'documents': documents
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/documents/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete a document"""
    try:
        user_id = request.args.get('user_id', 1)
        result = upload_manager.delete_document(document_id, user_id)
        
        return jsonify(result)
        
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

# ================== CLASSIFICATION API ENDPOINTS ==================

@app.route('/api/classification/categories', methods=['GET'])
def get_categories():
    """Get all professional categories"""
    try:
        categories = classification_manager.get_professional_categories()
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/classification/security-levels', methods=['GET'])  
def get_security_levels():
    """Get all security levels"""
    try:
        levels = classification_manager.get_security_levels()
        return jsonify({
            'success': True,
            'security_levels': levels
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/classification/user-permissions/<int:user_id>', methods=['GET'])
def get_user_permissions(user_id):
    """Get user permissions"""
    try:
        permissions = classification_manager.get_user_permissions(user_id)
        return jsonify({
            'success': True,
            'permissions': permissions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/classification/classify-document', methods=['POST'])
def classify_document():
    """Classify a document manually"""
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        category_id = data.get('category_id')
        security_level_id = data.get('security_level_id')
        classified_by = data.get('classified_by', 1)  # Default admin
        notes = data.get('notes', '')
        
        classification_id = classification_manager.classify_document(
            document_id=document_id,
            category_id=category_id,
            security_level_id=security_level_id,
            classified_by=classified_by,
            method="manual",
            notes=notes
        )
        
        return jsonify({
            'success': True,
            'classification_id': classification_id,
            'message': 'Document classified successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/classification/auto-classify', methods=['POST'])
def auto_classify_document():
    """Auto-classify a document based on content"""
    try:
        data = request.get_json()
        document_content = data.get('content', '')
        document_id = data.get('document_id')
        classified_by = data.get('classified_by', 1)
        
        result = classification_manager.auto_classify_document(
            document_content=document_content,
            document_id=document_id,
            classified_by=classified_by
        )
        
        if result:
            return jsonify({
                'success': True,
                'classification': result,
                'message': f'Auto-classified as {result["category_name"]} - {result["security_level_name"]} (confidence: {result["confidence"]:.2%})'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Could not auto-classify document. Manual classification required.'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/classification/grant-permission', methods=['POST'])
def grant_permission():
    """Grant permission to user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        security_level_id = data.get('security_level_id')
        permission_type = data.get('permission_type', 'read')
        granted_by = data.get('granted_by', 1)
        expires_at = data.get('expires_at')
        notes = data.get('notes', '')
        
        permission_id = classification_manager.grant_user_permission(
            user_id=user_id,
            category_id=category_id,
            security_level_id=security_level_id,
            permission_type=permission_type,
            granted_by=granted_by,
            expires_at=expires_at,
            notes=notes
        )
        
        return jsonify({
            'success': True,
            'permission_id': permission_id,
            'message': 'Permission granted successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/classification/statistics', methods=['GET'])
def get_classification_statistics():
    """Get classification system statistics"""
    try:
        stats = classification_manager.get_classification_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/classification/check-access/<int:user_id>/<int:document_id>', methods=['GET'])
def check_document_access(user_id, document_id):
    """Check if user has access to a document"""
    try:
        access_check = classification_manager.check_document_access(user_id, document_id)
        
        # Log the access check
        classification_manager.log_document_access(
            user_id=user_id,
            document_id=document_id,
            action="access_check",
            access_granted=access_check['access_granted'],
            reason=access_check['reason'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return jsonify({
            'success': True,
            'access_check': access_check
        })
        
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