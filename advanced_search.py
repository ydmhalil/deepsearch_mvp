"""
Advanced search functionality for DeepSearch
Handles filters, ranking, and enhanced search features
"""

from datetime import datetime, timedelta
import os
import re
import logging
from init_database import get_db_connection
from embed_index import search as basic_search
from faiss_optimizer import optimized_search, faiss_optimizer

class AdvancedSearchManager:
    """Manages advanced search features and filters"""
    
    def __init__(self):
        self.supported_file_types = ['pdf', 'docx', 'xlsx', 'pptx', 'txt']
        
    def search_with_filters(self, query, filters=None, user_id=None):
        """
        Perform search with advanced filters using optimized FAISS
        
        filters = {
            'file_types': ['pdf', 'docx'],  # File type filter
            'date_from': '2024-01-01',      # Date range filter
            'date_to': '2024-12-31',
            'min_size': 1024,               # File size filter (bytes)
            'max_size': 10485760,
            'indexed_only': True,           # Only search indexed files
            'user_files_only': False        # Only user's own files
        }
        """
        try:
            # TEMPORARY: Use simple keyword search for better results
            results = self._keyword_search(query)
            
            if not results:
                # Fallback to FAISS search if keyword search fails
                results = optimized_search(query, topk=50, filters=filters)
                
                if not results:
                    # Fallback to basic search if optimized fails
                    logging.warning("Optimized search returned no results, trying basic search")
                    results = basic_search('./data/faiss.index', './data/meta.pkl', query, top_k=50)
                    
                    # Convert basic search results to optimized format
                    results = self._convert_basic_results(results)
                
                if not results:
                    return []
                
                # Apply minimum score threshold to filter out irrelevant results
                results = self._filter_by_relevance(results, min_score=0.15)
            
            # Apply filters if provided (additional filtering beyond FAISS)
            if filters:
                results = self._apply_filters(results, filters, user_id)
            
            # Apply enhanced ranking
            results = self._apply_enhanced_ranking(results, query)
            
            # Log search for analytics
            self._log_search(query, len(results), user_id, filters)
            
            return results
            
        except Exception as e:
            print(f"Advanced search error: {e}")
            return []
    
    def _convert_basic_results(self, basic_results):
        """Convert basic search results to optimized format"""
        converted_results = []
        for result in basic_results:
            converted_result = {
                'rank': len(converted_results) + 1,
                'similarity': result.get('score', 0),
                'file_path': result.get('file_path', ''),
                'chunk_text': result.get('meta', {}).get('chunk_text', ''),
                'start_pos': result.get('meta', {}).get('start_pos', 0),
                'end_pos': result.get('meta', {}).get('end_pos', 0),
                'chunk_id': result.get('meta', {}).get('chunk_id', ''),
                'metadata': result.get('meta', {})
            }
            converted_results.append(converted_result)
        return converted_results
    
    def _keyword_search(self, query):
        """Simple keyword-based search for better Turkish support"""
        import os
        import json
        
        results = []
        query_words = query.lower().split()
        
        # Read chunks file
        chunks_file = './data/chunks.jsonl'
        if not os.path.exists(chunks_file):
            return []
            
        try:
            with open(chunks_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    try:
                        chunk = json.loads(line.strip())
                        text = chunk.get('text', '').lower()
                        file_path = chunk.get('file_path', '')
                        
                        # Calculate keyword match score
                        score = 0.0
                        word_matches = 0
                        
                        for word in query_words:
                            if word in text:
                                word_matches += 1
                                # Exact word match
                                score += 1.0
                                # Boost for title/filename matches
                                if word in file_path.lower():
                                    score += 0.5
                                # Boost for multiple occurrences of the same word
                                word_count = text.count(word)
                                if word_count > 1:
                                    score += (word_count - 1) * 0.1
                        
                        # Strong boost for documents that match ALL query words
                        if word_matches == len(query_words):
                            score += 2.0
                        
                        # Special boost for file name relevance
                        file_name = os.path.basename(file_path).lower()
                        for word in query_words:
                            if word in file_name:
                                score += 1.0
                        
                        # Normalize score by query length
                        if len(query_words) > 0:
                            score = score / len(query_words)
                        
                        if score > 0:
                            results.append({
                                'rank': line_num + 1,
                                'similarity': score,
                                'file_path': file_path,
                                'chunk_text': chunk.get('text', ''),
                                'start_pos': 0,
                                'end_pos': len(chunk.get('text', '')),
                                'chunk_id': chunk.get('meta', {}).get('chunk_id', ''),
                                'metadata': chunk.get('meta', {})
                            })
                            
                    except json.JSONDecodeError:
                        continue
                        
            # Sort by score descending
            results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            
            print(f"Keyword search for '{query}': {len(results)} results")
            for i, r in enumerate(results[:3]):
                file_name = r.get('file_path', 'unknown').split('\\')[-1]
                score = r.get('similarity', 0)
                print(f"  {i+1}. {file_name} - Score: {score:.3f}")
            
            return results[:20]  # Return top 20 results
            
        except Exception as e:
            print(f"Keyword search error: {e}")
            return []
    
    def _filter_by_relevance(self, results, min_score=0.15):
        """Filter out results below minimum relevance threshold"""
        filtered_results = []
        
        for result in results:
            score = result.get('similarity', result.get('score', 0))
            
            # Only include results above threshold
            if score >= min_score:
                filtered_results.append(result)
            else:
                print(f"Filtered out low-relevance result: {result.get('file_path', 'unknown')} (score: {score:.3f})")
        
        print(f"Relevance filtering: {len(results)} → {len(filtered_results)} results (min_score: {min_score})")
        return filtered_results
    
    def _apply_filters(self, results, filters, user_id):
        """Apply various filters to search results"""
        filtered_results = []
        
        # Get document information from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for result in results:
            file_path = result.get('file_path', '')
            
            # Get document info from database
            cursor.execute('''
                SELECT d.*, u.username as uploader_name 
                FROM documents d 
                LEFT JOIN users u ON d.uploaded_by = u.id 
                WHERE d.file_path = ?
            ''', (file_path,))
            
            doc_info = cursor.fetchone()
            
            # If document not in database, use file system info
            if not doc_info:
                if not os.path.exists(file_path):
                    continue
                    
                file_stat = os.stat(file_path)
                doc_info = {
                    'filename': os.path.basename(file_path),
                    'file_size': file_stat.st_size,
                    'upload_date': datetime.fromtimestamp(file_stat.st_mtime),
                    'is_indexed': True,  # Assume indexed if found in search
                    'uploaded_by': None,
                    'uploader_name': 'System'
                }
            else:
                doc_info = dict(doc_info)
            
            # Apply file type filter
            if filters.get('file_types'):
                file_ext = os.path.splitext(doc_info['filename'])[1].lower().lstrip('.')
                if file_ext not in filters['file_types']:
                    continue
            
            # Apply date range filter
            if filters.get('date_from') or filters.get('date_to'):
                upload_date = doc_info.get('upload_date')
                if upload_date:
                    if isinstance(upload_date, str):
                        upload_date = datetime.fromisoformat(upload_date)
                    
                    if filters.get('date_from'):
                        date_from = datetime.fromisoformat(filters['date_from'])
                        if upload_date < date_from:
                            continue
                    
                    if filters.get('date_to'):
                        date_to = datetime.fromisoformat(filters['date_to'])
                        if upload_date > date_to:
                            continue
            
            # Apply file size filter
            file_size = doc_info.get('file_size', 0)
            if filters.get('min_size') and file_size < filters['min_size']:
                continue
            if filters.get('max_size') and file_size > filters['max_size']:
                continue
            
            # Apply indexed only filter
            if filters.get('indexed_only') and not doc_info.get('is_indexed'):
                continue
            
            # Apply user files only filter
            if filters.get('user_files_only') and user_id:
                if doc_info.get('uploaded_by') != user_id:
                    continue
            
            # Add document info to result
            result['doc_info'] = doc_info
            filtered_results.append(result)
        
        conn.close()
        return filtered_results
    
    def _apply_enhanced_ranking(self, results, query):
        """Apply enhanced ranking algorithm"""
        query_words = query.lower().split()
        
        for result in results:
            score = result.get('similarity', result.get('score', 0.0))
            
            # File name matching bonus
            filename = result.get('file_path', '').lower()
            filename_bonus = 0
            for word in query_words:
                if word in filename:
                    filename_bonus += 0.1
            
            # Recent file bonus
            doc_info = result.get('doc_info', {})
            upload_date = doc_info.get('upload_date')
            recency_bonus = 0
            if upload_date:
                if isinstance(upload_date, str):
                    upload_date = datetime.fromisoformat(upload_date)
                days_old = (datetime.now() - upload_date).days
                if days_old < 30:
                    recency_bonus = 0.05 * (30 - days_old) / 30
            
            # File type bonus (PDF and DOCX get slight boost)
            file_ext = os.path.splitext(filename)[1].lower()
            type_bonus = 0.02 if file_ext in ['.pdf', '.docx'] else 0
            
            # Calculate final score
            result['enhanced_score'] = score + filename_bonus + recency_bonus + type_bonus
        
        # Sort by enhanced score
        results.sort(key=lambda x: x.get('enhanced_score', 0), reverse=True)
        return results
    
    def _log_search(self, query, results_count, user_id, filters):
        """Log search for analytics"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Calculate response time (approximate)
            response_time = 0.5  # Placeholder
            
            # Convert filters to JSON string
            filters_json = str(filters) if filters else None
            
            cursor.execute('''
                INSERT INTO search_logs (user_id, query, results_count, timestamp, response_time, filters)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, query, results_count, datetime.now(), response_time, filters_json))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Search logging error: {e}")
    
    def get_search_suggestions(self, query, limit=5):
        """Get search suggestions based on query"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get similar queries from search logs
            cursor.execute('''
                SELECT query, COUNT(*) as frequency
                FROM search_logs 
                WHERE query LIKE ? AND query != ?
                GROUP BY query 
                ORDER BY frequency DESC, timestamp DESC
                LIMIT ?
            ''', (f'%{query}%', query, limit))
            
            suggestions = [row['query'] for row in cursor.fetchall()]
            conn.close()
            
            return suggestions
            
        except Exception as e:
            print(f"Search suggestions error: {e}")
            return []
    
    def get_popular_searches(self, days=30, limit=10):
        """Get popular searches from recent period"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            since_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT query, COUNT(*) as frequency
                FROM search_logs 
                WHERE timestamp > ?
                GROUP BY query 
                ORDER BY frequency DESC
                LIMIT ?
            ''', (since_date, limit))
            
            popular = [{'query': row['query'], 'frequency': row['frequency']} 
                      for row in cursor.fetchall()]
            conn.close()
            
            return popular
            
        except Exception as e:
            print(f"Popular searches error: {e}")
            return []
    
    def get_search_analytics(self, user_id=None, days=30):
        """Get search analytics for dashboard"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            since_date = datetime.now() - timedelta(days=days)
            
            # Base query condition
            where_clause = "WHERE timestamp > ?"
            params = [since_date]
            
            if user_id:
                where_clause += " AND user_id = ?"
                params.append(user_id)
            
            # Total searches
            cursor.execute(f'''
                SELECT COUNT(*) as total_searches,
                       AVG(results_count) as avg_results,
                       AVG(response_time) as avg_response_time
                FROM search_logs {where_clause}
            ''', params)
            
            stats = cursor.fetchone()
            
            # Searches by day
            cursor.execute(f'''
                SELECT DATE(timestamp) as search_date, COUNT(*) as searches
                FROM search_logs {where_clause}
                GROUP BY DATE(timestamp)
                ORDER BY search_date DESC
                LIMIT 30
            ''', params)
            
            daily_searches = [{'date': row['search_date'], 'count': row['searches']} 
                            for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_searches': stats['total_searches'] or 0,
                'avg_results': round(stats['avg_results'] or 0, 1),
                'avg_response_time': round(stats['avg_response_time'] or 0, 3),
                'daily_searches': daily_searches
            }
            
        except Exception as e:
            print(f"Search analytics error: {e}")
            return {
                'total_searches': 0,
                'avg_results': 0,
                'avg_response_time': 0,
                'daily_searches': []
            }

# Global search manager instance
search_manager = AdvancedSearchManager()