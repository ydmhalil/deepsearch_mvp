"""
FAISS Performance Optimization Module
Provides caching, batch processing, and memory optimization for vector search
"""

import os
import json
import pickle
import hashlib
import threading
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

# Memory-based caching
class SearchCache:
    """In-memory LRU cache for search results"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def _generate_key(self, query: str, topk: int, filters: Dict = None) -> str:
        """Generate cache key from search parameters"""
        key_data = {
            'query': query.lower().strip(),
            'topk': topk,
            'filters': filters or {}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, topk: int, filters: Dict = None) -> Optional[List[Dict]]:
        """Get cached search results"""
        key = self._generate_key(query, topk, filters)
        
        with self.lock:
            if key in self.cache:
                cached_data, timestamp = self.cache[key]
                
                # Check TTL
                if time.time() - timestamp < self.ttl_seconds:
                    self.access_times[key] = time.time()
                    self.stats['hits'] += 1
                    return cached_data
                else:
                    # Expired
                    del self.cache[key]
                    del self.access_times[key]
            
            self.stats['misses'] += 1
            return None
    
    def put(self, query: str, topk: int, results: List[Dict], filters: Dict = None):
        """Cache search results"""
        key = self._generate_key(query, topk, filters)
        
        with self.lock:
            # Evict if at capacity
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            self.cache[key] = (results, time.time())
            self.access_times[key] = time.time()
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times, key=self.access_times.get)
        del self.cache[lru_key]
        del self.access_times[lru_key]
        self.stats['evictions'] += 1
    
    def clear(self):
        """Clear all cached data"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / max(1, total_requests)) * 100
        
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate_percent': round(hit_rate, 2),
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions']
        }

class FAISSOptimizer:
    """FAISS performance optimization and management"""
    
    def __init__(self, index_path: str = './data/faiss.index', 
                 meta_path: str = './data/meta.pkl',
                 cache_size: int = 1000):
        self.index_path = index_path
        self.meta_path = meta_path
        self.cache = SearchCache(max_size=cache_size)
        self.index = None
        self.metadata = None
        self.model = None
        self.last_load_time = 0
        self.load_lock = threading.Lock()
        self.search_stats = {
            'total_searches': 0,
            'avg_search_time': 0,
            'cache_hit_rate': 0
        }
    
    def _import_dependencies(self):
        """Import ML dependencies with error handling"""
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
            return faiss, SentenceTransformer
        except ImportError as e:
            raise ImportError(f"FAISS optimization requires ML dependencies: {e}")
    
    def load_index_and_model(self, force_reload: bool = False):
        """Load FAISS index and model with caching"""
        current_time = time.time()
        
        # Skip loading if recently loaded (unless forced)
        if not force_reload and (current_time - self.last_load_time) < 300:  # 5 minutes
            if self.index is not None and self.model is not None:
                return
        
        with self.load_lock:
            faiss, SentenceTransformer = self._import_dependencies()
            
            # Load FAISS index
            if os.path.exists(self.index_path):
                try:
                    self.index = faiss.read_index(self.index_path)
                    logging.info(f"FAISS index loaded: {self.index.ntotal} vectors")
                except Exception as e:
                    logging.error(f"Failed to load FAISS index: {e}")
                    raise
            else:
                raise FileNotFoundError(f"FAISS index not found: {self.index_path}")
            
            # Load metadata
            if os.path.exists(self.meta_path):
                try:
                    with open(self.meta_path, 'rb') as f:
                        self.metadata = pickle.load(f)
                    logging.info(f"Metadata loaded: {len(self.metadata)} entries")
                except Exception as e:
                    logging.error(f"Failed to load metadata: {e}")
                    raise
            else:
                raise FileNotFoundError(f"Metadata not found: {self.meta_path}")
            
            # Load embedding model
            try:
                self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
                logging.info("Sentence transformer model loaded")
            except Exception as e:
                logging.error(f"Failed to load embedding model: {e}")
                raise
            
            self.last_load_time = current_time
    
    def search_optimized(self, query: str, topk: int = 5, 
                        filters: Dict = None) -> List[Dict[str, Any]]:
        """Optimized search with caching and performance tracking"""
        start_time = time.time()
        
        # Check cache first
        cached_results = self.cache.get(query, topk, filters)
        if cached_results is not None:
            logging.debug(f"Cache hit for query: {query[:50]}...")
            self._update_search_stats(time.time() - start_time, cache_hit=True)
            return cached_results
        
        # Ensure index and model are loaded
        self.load_index_and_model()
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])
            
            # Normalize for cosine similarity
            faiss, _ = self._import_dependencies()
            faiss.normalize_L2(query_embedding)
            
            # Search FAISS index
            distances, indices = self.index.search(query_embedding, topk)
            
            # Process results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx != -1 and idx < len(self.metadata):
                    metadata = self.metadata[idx]
                    
                    # Apply filters if provided
                    if filters and not self._match_filters(metadata, filters):
                        continue
                    
                    result = {
                        'rank': i + 1,
                        'similarity': float(1 - distance),  # Convert distance to similarity
                        'file_path': metadata.get('file_path', ''),
                        'chunk_text': metadata.get('chunk_text', ''),
                        'start_pos': metadata.get('start_pos', 0),
                        'end_pos': metadata.get('end_pos', 0),
                        'chunk_id': metadata.get('chunk_id', ''),
                        'metadata': metadata
                    }
                    results.append(result)
            
            # Cache results
            self.cache.put(query, topk, results, filters)
            
            # Update statistics
            search_time = time.time() - start_time
            self._update_search_stats(search_time, cache_hit=False)
            
            logging.info(f"Search completed: {len(results)} results in {search_time:.3f}s")
            return results
            
        except Exception as e:
            logging.error(f"Search failed: {e}")
            return []
    
    def batch_search(self, queries: List[str], topk: int = 5) -> List[List[Dict]]:
        """Batch search for multiple queries"""
        self.load_index_and_model()
        
        try:
            # Generate embeddings for all queries at once
            query_embeddings = self.model.encode(queries)
            
            # Normalize
            faiss, _ = self._import_dependencies()
            faiss.normalize_L2(query_embeddings)
            
            # Batch search
            distances, indices = self.index.search(query_embeddings, topk)
            
            # Process results for each query
            all_results = []
            for query_idx, (query_distances, query_indices) in enumerate(zip(distances, indices)):
                results = []
                for i, (distance, idx) in enumerate(zip(query_distances, query_indices)):
                    if idx != -1 and idx < len(self.metadata):
                        metadata = self.metadata[idx]
                        result = {
                            'rank': i + 1,
                            'similarity': float(1 - distance),
                            'file_path': metadata.get('file_path', ''),
                            'chunk_text': metadata.get('chunk_text', ''),
                            'metadata': metadata
                        }
                        results.append(result)
                
                all_results.append(results)
            
            return all_results
            
        except Exception as e:
            logging.error(f"Batch search failed: {e}")
            return [[] for _ in queries]
    
    def _match_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Check if metadata matches filters"""
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def _update_search_stats(self, search_time: float, cache_hit: bool = False):
        """Update search performance statistics"""
        self.search_stats['total_searches'] += 1
        
        # Update average search time
        current_avg = self.search_stats['avg_search_time']
        total_searches = self.search_stats['total_searches']
        self.search_stats['avg_search_time'] = (current_avg * (total_searches - 1) + search_time) / total_searches
        
        # Update cache hit rate
        cache_stats = self.cache.get_stats()
        self.search_stats['cache_hit_rate'] = cache_stats['hit_rate_percent']
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        cache_stats = self.cache.get_stats()
        
        # Index statistics
        index_stats = {}
        if self.index is not None:
            index_stats = {
                'total_vectors': self.index.ntotal,
                'vector_dimension': self.index.d,
                'is_trained': self.index.is_trained
            }
        
        return {
            'search_stats': self.search_stats,
            'cache_stats': cache_stats,
            'index_stats': index_stats,
            'model_loaded': self.model is not None,
            'index_loaded': self.index is not None,
            'last_load_time': datetime.fromtimestamp(self.last_load_time).isoformat() if self.last_load_time else None
        }
    
    def optimize_index(self):
        """Optimize FAISS index for better performance"""
        if self.index is None:
            self.load_index_and_model()
        
        try:
            faiss, _ = self._import_dependencies()
            
            # Create optimized index if needed
            if self.index.ntotal > 10000:  # Only for larger indexes
                logging.info("Creating optimized FAISS index...")
                
                # Use IndexIVFFlat for better search performance on larger datasets
                quantizer = faiss.IndexFlatIP(self.index.d)
                nlist = min(100, int(self.index.ntotal ** 0.5))  # Square root heuristic
                
                optimized_index = faiss.IndexIVFFlat(quantizer, self.index.d, nlist)
                
                # Train the index with existing vectors
                # This would require re-adding all vectors, which is expensive
                # For now, we'll just add this as a future enhancement
                logging.info("Index optimization would require rebuilding - skipping for now")
                
        except Exception as e:
            logging.error(f"Index optimization failed: {e}")
    
    def clear_cache(self):
        """Clear search cache"""
        self.cache.clear()
        logging.info("Search cache cleared")
    
    def warm_up_cache(self, common_queries: List[str]):
        """Pre-populate cache with common queries"""
        logging.info(f"Warming up cache with {len(common_queries)} queries...")
        
        for query in common_queries:
            try:
                self.search_optimized(query, topk=5)
            except Exception as e:
                logging.warning(f"Cache warm-up failed for query '{query}': {e}")
        
        logging.info("Cache warm-up completed")

# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'search_times': [],
            'memory_usage': [],
            'cpu_usage': []
        }
    
    def log_search_time(self, search_time: float):
        """Log search execution time"""
        self.metrics['search_times'].append({
            'time': search_time,
            'timestamp': time.time()
        })
        
        # Keep only last 1000 measurements
        if len(self.metrics['search_times']) > 1000:
            self.metrics['search_times'] = self.metrics['search_times'][-1000:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics['search_times']:
            return {'status': 'No performance data available'}
        
        search_times = [m['time'] for m in self.metrics['search_times']]
        
        return {
            'avg_search_time_ms': round(sum(search_times) / len(search_times) * 1000, 2),
            'min_search_time_ms': round(min(search_times) * 1000, 2),
            'max_search_time_ms': round(max(search_times) * 1000, 2),
            'total_searches': len(search_times),
            'searches_per_second': len(search_times) / max(1, (time.time() - self.metrics['search_times'][0]['timestamp']))
        }

# Global instances
faiss_optimizer = FAISSOptimizer()
performance_monitor = PerformanceMonitor()

# Helper functions for integration
def optimized_search(query: str, topk: int = 5, filters: Dict = None) -> List[Dict]:
    """Main search function with optimization"""
    start_time = time.time()
    
    try:
        results = faiss_optimizer.search_optimized(query, topk, filters)
        search_time = time.time() - start_time
        performance_monitor.log_search_time(search_time)
        return results
    except Exception as e:
        logging.error(f"Optimized search failed: {e}")
        return []

def get_search_performance_stats() -> Dict[str, Any]:
    """Get comprehensive search performance statistics"""
    faiss_stats = faiss_optimizer.get_performance_stats()
    perf_stats = performance_monitor.get_performance_summary()
    
    return {
        'faiss_optimizer': faiss_stats,
        'performance_monitor': perf_stats
    }