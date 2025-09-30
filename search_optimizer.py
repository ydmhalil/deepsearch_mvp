"""
Search Performance Optimizer
Advanced search ranking and performance optimizations
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
import re

class SearchOptimizer:
    def __init__(self, db_path='config/users.db'):
        self.db_path = db_path
        self.query_cache = {}
        self.max_cache_size = 1000
        self.cache_ttl = 3600  # 1 hour
        
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def enhanced_result_ranking(self, results, query, user_preferences=None):
        """
        Enhanced result ranking algorithm
        Considers: relevance, popularity, freshness, user behavior
        """
        if not results:
            return results
            
        # Get user search history for personalization
        user_patterns = self._get_user_search_patterns(user_preferences.get('user_id') if user_preferences else None)
        
        scored_results = []
        query_terms = self._extract_query_terms(query)
        
        for result in results:
            score = self._calculate_result_score(result, query_terms, user_patterns)
            scored_results.append((score, result))
            
        # Sort by score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [result for score, result in scored_results]
        
    def _extract_query_terms(self, query):
        """Extract and normalize query terms"""
        # Turkish character normalization
        query = query.lower()
        # Split into terms and remove stopwords
        stopwords = {'ve', 'ile', 'için', 'bir', 'bu', 'şu', 'o', 'hangi', 'ne', 'nerede', 'nasıl'}
        terms = [term.strip() for term in re.split(r'[^\w\s]', query) if term.strip() and term not in stopwords]
        return terms
        
    def _calculate_result_score(self, result, query_terms, user_patterns):
        """Calculate comprehensive result score"""
        score = 0.0
        
        # Base relevance score (from FAISS similarity)
        relevance_score = float(result.get('score', 0))
        score += relevance_score * 0.4
        
        # Title/filename match bonus
        filename = result.get('metadata', {}).get('file_path', '').lower()
        content = result.get('content', '').lower()
        
        title_matches = sum(1 for term in query_terms if term in filename)
        content_matches = sum(1 for term in query_terms if term in content)
        
        score += title_matches * 0.2
        score += min(content_matches / len(query_terms), 1.0) * 0.2
        
        # Popularity score (how often accessed)
        popularity = self._get_document_popularity(result.get('metadata', {}).get('file_path'))
        score += popularity * 0.1
        
        # Freshness score (newer documents get slight boost)
        freshness = self._get_document_freshness(result.get('metadata', {}))
        score += freshness * 0.05
        
        # User preference score
        user_preference = self._get_user_preference_score(result, user_patterns)
        score += user_preference * 0.05
        
        return score
        
    def _get_document_popularity(self, file_path):
        """Get document popularity based on access frequency"""
        if not file_path:
            return 0.0
            
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Count how many times this document appeared in search results
            cursor.execute('''
                SELECT COUNT(*) as access_count
                FROM search_logs 
                WHERE results_count > 0 
                AND query LIKE ? 
                AND timestamp > ?
            ''', (f'%{file_path.split("/")[-1]}%', datetime.now() - timedelta(days=30)))
            
            result = cursor.fetchone()
            access_count = result['access_count'] if result else 0
            
            conn.close()
            
            # Normalize to 0-1 range
            return min(access_count / 10.0, 1.0)
            
        except Exception:
            return 0.0
            
    def _get_document_freshness(self, metadata):
        """Calculate freshness score based on document age"""
        try:
            # Try to get document modification time
            mod_time = metadata.get('modified_time')
            if not mod_time:
                return 0.5  # Default score for unknown age
                
            # Convert to datetime if needed
            if isinstance(mod_time, str):
                mod_time = datetime.fromisoformat(mod_time.replace('Z', '+00:00'))
                
            days_old = (datetime.now() - mod_time.replace(tzinfo=None)).days
            
            # Newer documents get higher scores
            if days_old < 7:
                return 1.0
            elif days_old < 30:
                return 0.8
            elif days_old < 90:
                return 0.6
            elif days_old < 365:
                return 0.4
            else:
                return 0.2
                
        except Exception:
            return 0.5
            
    def _get_user_search_patterns(self, user_id):
        """Analyze user search patterns for personalization"""
        if not user_id:
            return {}
            
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get user's recent searches
            cursor.execute('''
                SELECT query, filters 
                FROM search_logs 
                WHERE user_id = ? 
                AND timestamp > ?
                ORDER BY timestamp DESC 
                LIMIT 50
            ''', (user_id, datetime.now() - timedelta(days=30)))
            
            searches = cursor.fetchall()
            conn.close()
            
            # Analyze patterns
            query_terms = []
            file_types = []
            
            for search in searches:
                query_terms.extend(self._extract_query_terms(search['query']))
                
                if search['filters']:
                    try:
                        filters = json.loads(search['filters'])
                        if filters.get('file_types'):
                            file_types.extend(filters['file_types'].split(','))
                    except:
                        pass
                        
            return {
                'frequent_terms': Counter(query_terms).most_common(10),
                'preferred_file_types': Counter(file_types).most_common(5)
            }
            
        except Exception:
            return {}
            
    def _get_user_preference_score(self, result, user_patterns):
        """Calculate score based on user preferences"""
        if not user_patterns:
            return 0.0
            
        score = 0.0
        
        # Check if document contains user's frequent terms
        content = result.get('content', '').lower()
        for term, freq in user_patterns.get('frequent_terms', []):
            if term in content:
                score += 0.1 * (freq / 10.0)
                
        # Check if file type matches user preference
        file_path = result.get('metadata', {}).get('file_path', '')
        file_ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
        
        for file_type, freq in user_patterns.get('preferred_file_types', []):
            if file_type.lower() == file_ext:
                score += 0.2 * (freq / 5.0)
                
        return min(score, 1.0)
        
    def cache_search_result(self, query, filters, results):
        """Cache search results for performance"""
        cache_key = self._generate_cache_key(query, filters)
        
        # Clean old cache entries if needed
        if len(self.query_cache) >= self.max_cache_size:
            self._clean_old_cache_entries()
            
        self.query_cache[cache_key] = {
            'results': results,
            'timestamp': time.time(),
            'access_count': 1
        }
        
    def get_cached_result(self, query, filters):
        """Get cached search result if available and fresh"""
        cache_key = self._generate_cache_key(query, filters)
        
        if cache_key in self.query_cache:
            cached = self.query_cache[cache_key]
            
            # Check if cache is still fresh
            if time.time() - cached['timestamp'] < self.cache_ttl:
                cached['access_count'] += 1
                return cached['results']
            else:
                # Remove stale cache
                del self.query_cache[cache_key]
                
        return None
        
    def _generate_cache_key(self, query, filters):
        """Generate unique cache key for query and filters"""
        filters_str = json.dumps(filters, sort_keys=True) if filters else ''
        return f"{query.lower().strip()}|{filters_str}"
        
    def _clean_old_cache_entries(self):
        """Remove old or less frequently accessed cache entries"""
        current_time = time.time()
        
        # Remove entries older than TTL
        stale_keys = [
            key for key, value in self.query_cache.items()
            if current_time - value['timestamp'] > self.cache_ttl
        ]
        
        for key in stale_keys:
            del self.query_cache[key]
            
        # If still too many, remove least accessed
        if len(self.query_cache) >= self.max_cache_size:
            sorted_entries = sorted(
                self.query_cache.items(),
                key=lambda x: x[1]['access_count']
            )
            
            # Remove bottom 20%
            remove_count = len(sorted_entries) // 5
            for i in range(remove_count):
                key = sorted_entries[i][0]
                del self.query_cache[key]
                
    def get_search_suggestions(self, partial_query, user_id=None, limit=5):
        """Get intelligent search suggestions"""
        suggestions = []
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get popular queries that start with or contain the partial query
            cursor.execute('''
                SELECT query, COUNT(*) as frequency
                FROM search_logs 
                WHERE query LIKE ? 
                AND results_count > 0
                AND timestamp > ?
                GROUP BY query 
                ORDER BY frequency DESC, timestamp DESC
                LIMIT ?
            ''', (f'%{partial_query}%', datetime.now() - timedelta(days=30), limit * 2))
            
            popular_queries = cursor.fetchall()
            
            # Add popular queries
            for row in popular_queries:
                if len(suggestions) < limit:
                    suggestions.append({
                        'text': row['query'],
                        'type': 'popular',
                        'frequency': row['frequency']
                    })
                    
            # If user provided, add personalized suggestions
            if user_id and len(suggestions) < limit:
                cursor.execute('''
                    SELECT query, COUNT(*) as frequency
                    FROM search_logs 
                    WHERE user_id = ?
                    AND query LIKE ? 
                    AND timestamp > ?
                    GROUP BY query 
                    ORDER BY frequency DESC, timestamp DESC
                    LIMIT ?
                ''', (user_id, f'%{partial_query}%', datetime.now() - timedelta(days=90), limit))
                
                personal_queries = cursor.fetchall()
                
                for row in personal_queries:
                    if len(suggestions) < limit:
                        query_text = row['query']
                        # Avoid duplicates
                        if not any(s['text'] == query_text for s in suggestions):
                            suggestions.append({
                                'text': query_text,
                                'type': 'personal',
                                'frequency': row['frequency']
                            })
            
            conn.close()
            
        except Exception as e:
            print(f"Suggestion error: {e}")
            
        return suggestions
        
    def optimize_index_performance(self, index_path):
        """Optimize FAISS index performance"""
        try:
            # Import FAISS with error handling
            try:
                import faiss
            except ImportError:
                print("FAISS not available for optimization")
                return False
                
            # Load existing index
            index = faiss.read_index(index_path)
            
            # Get index info
            print(f"Index type: {type(index)}")
            print(f"Index size: {index.ntotal}")
            print(f"Index dimension: {index.d}")
            
            # For larger indexes, consider using IVF (Inverted File) structure
            if index.ntotal > 10000 and not isinstance(index, faiss.IndexIVF):
                print("Large index detected, considering IVF optimization...")
                
                # Create IVF index for better performance
                ncentroids = min(int(np.sqrt(index.ntotal)), 1000)
                quantizer = faiss.IndexFlatIP(index.d)
                new_index = faiss.IndexIVFFlat(quantizer, index.d, ncentroids)
                
                # Train the index
                vectors = np.array([index.reconstruct(i) for i in range(index.ntotal)])
                new_index.train(vectors)
                new_index.add(vectors)
                
                # Set search parameters
                new_index.nprobe = min(ncentroids // 4, 100)
                
                # Save optimized index
                optimized_path = index_path.replace('.index', '_optimized.index')
                faiss.write_index(new_index, optimized_path)
                
                print(f"Optimized index saved to: {optimized_path}")
                return True
                
            return False
            
        except Exception as e:
            print(f"Index optimization error: {e}")
            return False

# Global optimizer instance
search_optimizer = SearchOptimizer()