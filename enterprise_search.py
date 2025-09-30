"""
Enterprise Search Engine
Advanced search capabilities for large organizations
"""

import threading
import time
import asyncio
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from collections import defaultdict
import pickle
import json
import hashlib
from datetime import datetime, timedelta
import re

@dataclass
class SearchResult:
    """Enhanced search result with enterprise metadata"""
    file_path: str
    snippet: str
    score: float
    chunk_id: str
    metadata: Dict[str, Any]
    relevance_factors: Dict[str, float]
    department: Optional[str] = None
    classification: Optional[str] = None
    last_modified: Optional[datetime] = None
    access_count: int = 0
    
class EnterpriseSearchEngine:
    """Production-ready search engine for large organizations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.search_cache = {}
        self.cache_lock = threading.RLock()
        self.search_analytics = defaultdict(int)
        self.concurrent_searches = 0
        self.max_concurrent = config.get('max_concurrent_searches', 100)
        self.search_lock = threading.Semaphore(self.max_concurrent)
        
        # Initialize thread pool for parallel processing
        self.executor = ThreadPoolExecutor(
            max_workers=config.get('max_workers', 8),
            thread_name_prefix='SearchWorker'
        )
        
        # Performance monitoring
        self.search_times = []
        self.search_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        
        # Load search models and indexes
        self._initialize_search_components()
    
    def _initialize_search_components(self):
        """Initialize search components with enterprise optimizations"""
        try:
            # Import with error handling
            self._faiss = self._import_faiss()
            self._sentence_transformers = self._import_sentence_transformers()
            
            # Load FAISS index with optimizations
            self.faiss_index = None
            self.metadata = None
            self.model = None
            
            # Load if available
            self._load_search_index()
            
            # Initialize keyword search with advanced features
            self._initialize_keyword_search()
            
            self.logger.info("Enterprise search engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize search components: {e}")
            raise
    
    def _import_faiss(self):
        """Import FAISS with error handling"""
        try:
            import faiss
            return faiss
        except ImportError as e:
            self.logger.warning("FAISS not available, using keyword-only search")
            return None
    
    def _import_sentence_transformers(self):
        """Import sentence transformers with error handling"""
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer
        except ImportError as e:
            self.logger.warning("sentence-transformers not available")
            return None
    
    def _load_search_index(self):
        """Load search index with enterprise optimizations"""
        try:
            if self._faiss and self._sentence_transformers:
                # Try to load FAISS index
                index_path = "./data/faiss.index"
                meta_path = "./data/meta.pkl"
                
                if os.path.exists(index_path) and os.path.exists(meta_path):
                    self.faiss_index = self._faiss.read_index(index_path)
                    
                    with open(meta_path, 'rb') as f:
                        self.metadata = pickle.load(f)
                    
                    # Load embedding model
                    model_name = self.config.get('embedding_model', 'all-MiniLM-L6-v2')
                    self.model = self._sentence_transformers(model_name)
                    
                    self.logger.info(f"FAISS index loaded: {self.faiss_index.ntotal} vectors")
                else:
                    self.logger.warning("FAISS index files not found")
                    
        except Exception as e:
            self.logger.error(f"Failed to load FAISS index: {e}")
            self.faiss_index = None
            self.metadata = None
            self.model = None
    
    def _initialize_keyword_search(self):
        """Initialize advanced keyword search"""
        try:
            # Load document corpus for keyword search
            self.document_corpus = {}
            self.term_frequencies = {}
            self.document_frequencies = {}
            
            # Load chunks for keyword search
            chunks_path = "./data/chunks.jsonl"
            if os.path.exists(chunks_path):
                self._build_keyword_index(chunks_path)
                self.logger.info(f"Keyword index built for {len(self.document_corpus)} documents")
            else:
                self.logger.warning("Chunks file not found for keyword search")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize keyword search: {e}")
    
    def _build_keyword_index(self, chunks_path: str):
        """Build advanced keyword search index"""
        import json
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    chunk = json.loads(line)
                    chunk_id = chunk['chunk_id']
                    text = chunk['text'].lower()
                    file_path = chunk['metadata']['file_path']
                    
                    # Store document content
                    if file_path not in self.document_corpus:
                        self.document_corpus[file_path] = []
                    self.document_corpus[file_path].append({
                        'chunk_id': chunk_id,
                        'text': text,
                        'original_text': chunk['text']
                    })
                    
                    # Build term frequency index
                    words = self._tokenize_advanced(text)
                    term_freq = defaultdict(int)
                    for word in words:
                        term_freq[word] += 1
                    
                    self.term_frequencies[chunk_id] = dict(term_freq)
                    
                    # Update document frequency
                    unique_words = set(words)
                    for word in unique_words:
                        self.document_frequencies[word] = self.document_frequencies.get(word, 0) + 1
                        
                except Exception as e:
                    self.logger.error(f"Error processing chunk: {e}")
                    continue
    
    def _tokenize_advanced(self, text: str) -> List[str]:
        """Advanced tokenization with Turkish language support"""
        # Enhanced tokenization for Turkish
        text = re.sub(r'[^\w\sÇĞıİÖŞÜçğıöşü]', ' ', text)
        words = text.lower().split()
        
        # Filter out very short words and common stop words
        stop_words = {'ve', 'bir', 'bu', 'da', 'de', 'ile', 'için', 'olan', 'olan', 'olarak'}
        words = [w for w in words if len(w) > 2 and w not in stop_words]
        
        return words
    
    async def search_async(self, query: str, top_k: int = 10, filters: Optional[Dict] = None) -> List[SearchResult]:
        """Asynchronous search for better performance"""
        with self.search_lock:
            try:
                start_time = time.time()
                self.concurrent_searches += 1
                
                # Check cache first
                cache_key = self._get_cache_key(query, top_k, filters)
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    self.search_analytics['cache_hits'] += 1
                    return cached_result
                
                # Perform parallel search
                results = await self._parallel_search(query, top_k, filters)
                
                # Cache results
                self._cache_results(cache_key, results)
                
                # Update analytics
                search_time = time.time() - start_time
                self.search_times.append(search_time)
                self.search_analytics['total_searches'] += 1
                self.search_counts[query] += 1
                
                self.logger.info(f"Search completed in {search_time:.3f}s: '{query}' -> {len(results)} results")
                
                return results
                
            except Exception as e:
                self.error_counts[str(e)] += 1
                self.logger.error(f"Search error: {e}")
                raise
            finally:
                self.concurrent_searches -= 1
    
    def search(self, query: str, top_k: int = 10, filters: Optional[Dict] = None) -> List[SearchResult]:
        """Synchronous search wrapper"""
        return asyncio.run(self.search_async(query, top_k, filters))
    
    async def _parallel_search(self, query: str, top_k: int, filters: Optional[Dict]) -> List[SearchResult]:
        """Perform parallel search using multiple strategies"""
        search_tasks = []
        
        # Keyword search task
        keyword_task = asyncio.create_task(
            self._keyword_search_async(query, top_k, filters)
        )
        search_tasks.append(('keyword', keyword_task))
        
        # FAISS search task (if available)
        if self.faiss_index is not None and self.model is not None:
            faiss_task = asyncio.create_task(
                self._faiss_search_async(query, top_k, filters)
            )
            search_tasks.append(('faiss', faiss_task))
        
        # Wait for all searches to complete
        completed_results = {}
        for search_type, task in search_tasks:
            try:
                results = await task
                completed_results[search_type] = results
            except Exception as e:
                self.logger.error(f"{search_type} search failed: {e}")
                completed_results[search_type] = []
        
        # Merge and rank results
        merged_results = self._merge_search_results(completed_results, query)
        
        return merged_results[:top_k]
    
    async def _keyword_search_async(self, query: str, top_k: int, filters: Optional[Dict]) -> List[SearchResult]:
        """Asynchronous keyword search"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._keyword_search_sync, 
            query, top_k, filters
        )
    
    def _keyword_search_sync(self, query: str, top_k: int, filters: Optional[Dict]) -> List[SearchResult]:
        """Synchronous keyword search with advanced scoring"""
        results = []
        query_words = self._tokenize_advanced(query.lower())
        
        if not query_words:
            return results
        
        # Score each document
        document_scores = {}
        
        for file_path, chunks in self.document_corpus.items():
            file_score = 0
            best_chunk = None
            best_snippet = ""
            
            for chunk in chunks:
                chunk_text = chunk['text']
                chunk_score = self._calculate_advanced_score(query_words, chunk_text, file_path)
                
                if chunk_score > file_score:
                    file_score = chunk_score
                    best_chunk = chunk['chunk_id']
                    best_snippet = self._extract_snippet(chunk['original_text'], query)
            
            if file_score > 0:
                document_scores[file_path] = {
                    'score': file_score,
                    'chunk_id': best_chunk,
                    'snippet': best_snippet
                }
        
        # Sort by score and create results
        sorted_docs = sorted(document_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        for file_path, data in sorted_docs[:top_k]:
            results.append(SearchResult(
                file_path=file_path,
                snippet=data['snippet'],
                score=data['score'],
                chunk_id=data['chunk_id'],
                metadata={'search_type': 'keyword'},
                relevance_factors={
                    'keyword_match': data['score'],
                    'file_name_match': self._filename_score(query, file_path)
                }
            ))
        
        return results
    
    def _calculate_advanced_score(self, query_words: List[str], text: str, file_path: str) -> float:
        """Calculate advanced relevance score"""
        score = 0.0
        text_words = text.split()
        
        # 1. Exact phrase matching (highest weight)
        query_phrase = ' '.join(query_words)
        if query_phrase in text:
            score += 10.0
        
        # 2. Individual word matching with TF-IDF like scoring
        for query_word in query_words:
            word_count = text.count(query_word)
            if word_count > 0:
                # Term frequency
                tf = word_count / len(text_words)
                
                # Inverse document frequency approximation
                total_docs = len(self.document_corpus)
                doc_freq = self.document_frequencies.get(query_word, 1)
                idf = math.log(total_docs / doc_freq)
                
                score += tf * idf * 2.0
        
        # 3. Proximity scoring (words close together)
        score += self._proximity_score(query_words, text_words)
        
        # 4. File name relevance
        score += self._filename_score(' '.join(query_words), file_path) * 0.5
        
        # 5. Multi-word query bonus
        if len(query_words) > 1:
            found_words = sum(1 for word in query_words if word in text)
            score += (found_words / len(query_words)) * 1.5
        
        return score
    
    def _proximity_score(self, query_words: List[str], text_words: List[str]) -> float:
        """Calculate proximity score for query words"""
        if len(query_words) < 2:
            return 0.0
        
        proximity_score = 0.0
        
        for i, word1 in enumerate(query_words):
            for word2 in query_words[i+1:]:
                positions1 = [j for j, w in enumerate(text_words) if w == word1]
                positions2 = [j for j, w in enumerate(text_words) if w == word2]
                
                if positions1 and positions2:
                    min_distance = min(abs(p1 - p2) for p1 in positions1 for p2 in positions2)
                    if min_distance <= 5:  # Words within 5 positions
                        proximity_score += 1.0 / (min_distance + 1)
        
        return proximity_score
    
    def _filename_score(self, query: str, file_path: str) -> float:
        """Calculate filename relevance score"""
        import os
        filename = os.path.basename(file_path).lower()
        query_lower = query.lower()
        
        # Exact filename match
        if query_lower in filename:
            return 2.0
        
        # Partial filename match
        query_words = query_lower.split()
        matches = sum(1 for word in query_words if word in filename)
        
        return matches / len(query_words) if query_words else 0.0
    
    async def _faiss_search_async(self, query: str, top_k: int, filters: Optional[Dict]) -> List[SearchResult]:
        """Asynchronous FAISS search"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._faiss_search_sync, 
            query, top_k, filters
        )
    
    def _faiss_search_sync(self, query: str, top_k: int, filters: Optional[Dict]) -> List[SearchResult]:
        """Synchronous FAISS search"""
        if not self.faiss_index or not self.model:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query], normalize_embeddings=True)
            
            # Search FAISS index
            scores, indices = self.faiss_index.search(query_embedding, top_k * 2)  # Get more for filtering
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.metadata):
                    meta = self.metadata[idx]
                    results.append(SearchResult(
                        file_path=meta['file_path'],
                        snippet=self._extract_snippet(meta['text'], query),
                        score=float(score),
                        chunk_id=meta['chunk_id'],
                        metadata={'search_type': 'faiss'},
                        relevance_factors={'embedding_similarity': float(score)}
                    ))
            
            return results
            
        except Exception as e:
            self.logger.error(f"FAISS search error: {e}")
            return []
    
    def _merge_search_results(self, search_results: Dict[str, List[SearchResult]], query: str) -> List[SearchResult]:
        """Merge and rank results from different search strategies"""
        merged = []
        seen_files = set()
        
        # Prioritize keyword search results (better for Turkish)
        if 'keyword' in search_results:
            for result in search_results['keyword']:
                if result.file_path not in seen_files:
                    merged.append(result)
                    seen_files.add(result.file_path)
        
        # Add FAISS results that weren't already included
        if 'faiss' in search_results:
            for result in search_results['faiss']:
                if result.file_path not in seen_files:
                    # Boost FAISS scores to be comparable with keyword scores
                    result.score = result.score * 5.0  # Adjust multiplier as needed
                    merged.append(result)
                    seen_files.add(result.file_path)
        
        # Sort by combined score
        merged.sort(key=lambda x: x.score, reverse=True)
        
        return merged
    
    def _extract_snippet(self, text: str, query: str, max_length: int = 300) -> str:
        """Extract relevant snippet from text"""
        words = query.lower().split()
        text_lower = text.lower()
        
        # Find best position for snippet
        best_pos = 0
        best_score = 0
        
        for i in range(0, len(text) - max_length, 50):
            snippet = text_lower[i:i + max_length]
            score = sum(snippet.count(word) for word in words)
            if score > best_score:
                best_score = score
                best_pos = i
        
        # Extract snippet and add highlighting
        snippet = text[best_pos:best_pos + max_length]
        
        # Add ellipsis if needed
        if best_pos > 0:
            snippet = "..." + snippet
        if best_pos + max_length < len(text):
            snippet = snippet + "..."
        
        return snippet.strip()
    
    def _get_cache_key(self, query: str, top_k: int, filters: Optional[Dict]) -> str:
        """Generate cache key for search"""
        cache_data = {
            'query': query,
            'top_k': top_k,
            'filters': filters or {}
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[SearchResult]]:
        """Get cached search result"""
        with self.cache_lock:
            if cache_key in self.search_cache:
                cached_data = self.search_cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self.config.get('cache_ttl', 3600)):
                    return cached_data['results']
        return None
    
    def _cache_results(self, cache_key: str, results: List[SearchResult]):
        """Cache search results"""
        with self.cache_lock:
            # Limit cache size
            if len(self.search_cache) > self.config.get('cache_size', 1000):
                # Remove oldest entries
                oldest_key = min(self.search_cache.keys(), 
                               key=lambda k: self.search_cache[k]['timestamp'])
                del self.search_cache[oldest_key]
            
            self.search_cache[cache_key] = {
                'results': results,
                'timestamp': datetime.now()
            }
    
    def get_search_analytics(self) -> Dict[str, Any]:
        """Get search performance analytics"""
        avg_search_time = sum(self.search_times) / len(self.search_times) if self.search_times else 0
        
        return {
            'total_searches': self.search_analytics['total_searches'],
            'cache_hits': self.search_analytics['cache_hits'],
            'cache_hit_rate': (self.search_analytics['cache_hits'] / 
                             max(1, self.search_analytics['total_searches'])) * 100,
            'average_search_time': avg_search_time,
            'concurrent_searches': self.concurrent_searches,
            'popular_queries': dict(sorted(self.search_counts.items(), 
                                         key=lambda x: x[1], reverse=True)[:10]),
            'error_summary': dict(self.error_counts),
            'cache_size': len(self.search_cache)
        }
    
    def optimize_performance(self):
        """Optimize search engine performance"""
        try:
            # Clear old cache entries
            current_time = datetime.now()
            cache_ttl = timedelta(seconds=self.config.get('cache_ttl', 3600))
            
            with self.cache_lock:
                expired_keys = [
                    key for key, data in self.search_cache.items()
                    if current_time - data['timestamp'] > cache_ttl
                ]
                for key in expired_keys:
                    del self.search_cache[key]
            
            # Reset analytics if they get too large
            if len(self.search_times) > 10000:
                self.search_times = self.search_times[-5000:]
            
            self.logger.info(f"Performance optimization completed. Cache size: {len(self.search_cache)}")
            
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {e}")


# Global search engine instance
enterprise_search = None

def get_enterprise_search_engine(config: Dict[str, Any] = None) -> EnterpriseSearchEngine:
    """Get global enterprise search engine instance"""
    global enterprise_search
    
    if enterprise_search is None:
        from enterprise_config import ENTERPRISE_CONFIG
        config = config or ENTERPRISE_CONFIG['SEARCH_SETTINGS']
        enterprise_search = EnterpriseSearchEngine(config)
    
    return enterprise_search

# Import required modules
import os
import math