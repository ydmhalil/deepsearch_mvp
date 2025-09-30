import argparse
import json
import os
import pickle
import logging
from typing import List, Dict, Any

import numpy as np
from tqdm import tqdm
from faiss_optimizer import faiss_optimizer

# Configure logging
logging.basicConfig(level=logging.INFO)


def _import_faiss():
    try:
        import faiss
        return faiss
    except Exception as e:
        raise ImportError("faiss is required for index operations: " + str(e))


def _import_sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer
    except Exception as e:
        raise ImportError("sentence-transformers is required for embeddings: " + str(e))


def build_index(chunks_path: str, index_path: str, meta_path: str, model_name: str = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2', batch_size: int = 64):
    os.makedirs(os.path.dirname(index_path) or '.', exist_ok=True)
    os.makedirs(os.path.dirname(meta_path) or '.', exist_ok=True)

    SentenceTransformer = _import_sentence_transformer()
    model = SentenceTransformer(model_name)

    texts = []
    metas = []
    with open(chunks_path, 'r', encoding='utf-8') as f:
        for line in f:
            j = json.loads(line)
            texts.append(j.get('text', ''))
            metas.append({'file_path': j.get('file_path'), 'meta': j.get('meta', {})})

    if not texts:
        print('No chunks found in', chunks_path)
        return

    embeds = []
    for i in tqdm(range(0, len(texts), batch_size), desc='Embedding'):
        batch = texts[i:i + batch_size]
        emb = model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
        embeds.append(emb)
    embeddings = np.vstack(embeds).astype('float32')

    # Normalize to use inner product as cosine similarity
    faiss = _import_faiss()
    faiss.normalize_L2(embeddings)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, index_path)
    with open(meta_path, 'wb') as mf:
        pickle.dump(metas, mf)

    print('Index saved to', index_path)
    print('Metadata saved to', meta_path)


def load_index(index_path: str, meta_path: str):
    faiss = _import_faiss()
    index = faiss.read_index(index_path)
    with open(meta_path, 'rb') as mf:
        metas = pickle.load(mf)
    return index, metas


def search(index_path: str, meta_path: str, query: str, model_name: str = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2', top_k: int = 5):
    """Search using optimized FAISS implementation"""
    try:
        # Use optimized search if available
        results = faiss_optimizer.search_optimized(query, topk=top_k)
        
        # Convert to legacy format for compatibility
        legacy_results = []
        for result in results:
            legacy_results.append({
                'score': result['similarity'],
                'file_path': result['file_path'],
                'meta': result['metadata']
            })
        
        return legacy_results
        
    except Exception as e:
        logging.warning(f"Optimized search failed, falling back to standard: {e}")
        
        # Fallback to original implementation
        SentenceTransformer = _import_sentence_transformer()
        model = SentenceTransformer(model_name)
        q_emb = model.encode([query], convert_to_numpy=True).astype('float32')
        faiss = _import_faiss()
        faiss.normalize_L2(q_emb)

        index, metas = load_index(index_path, meta_path)
        D, I = index.search(q_emb, top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0 or idx >= len(metas):
                continue
            m = metas[idx]
            results.append({'score': float(score), 'file_path': m.get('file_path'), 'meta': m.get('meta')})
        return results

def search_batch(queries: List[str], index_path: str = './data/faiss.index', 
                meta_path: str = './data/meta.pkl', top_k: int = 5) -> List[List[Dict]]:
    """Batch search for multiple queries with optimization"""
    try:
        return faiss_optimizer.batch_search(queries, topk=top_k)
    except Exception as e:
        logging.error(f"Batch search failed: {e}")
        return [[] for _ in queries]

def get_search_stats() -> Dict[str, Any]:
    """Get search performance statistics"""
    return faiss_optimizer.get_performance_stats()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd')

    p_build = sub.add_parser('build')
    p_build.add_argument('--chunks', required=True, help='Input chunks JSONL')
    p_build.add_argument('--index', required=True, help='Output FAISS index path')
    p_build.add_argument('--meta', required=True, help='Output metadata (pickle) path')
    p_build.add_argument('--model', default='sentence-transformers/paraphrase-multilingual-mpnet-base-v2')

    p_search = sub.add_parser('search')
    p_search.add_argument('--index', required=True)
    p_search.add_argument('--meta', required=True)
    p_search.add_argument('--query', required=True)
    p_search.add_argument('--model', default='sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
    p_search.add_argument('--topk', type=int, default=5)

    args = parser.parse_args()
    if args.cmd == 'build':
        build_index(args.chunks, args.index, args.meta, model_name=args.model)
    elif args.cmd == 'search':
        res = search(args.index, args.meta, args.query, model_name=args.model, top_k=args.topk)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        parser.print_help()
