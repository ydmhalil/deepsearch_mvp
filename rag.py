import argparse
import json
import pickle
import os
from typing import List

from embed_index import load_index


def _import_sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer
    except Exception as e:
        raise ImportError("sentence-transformers is required for retrieval: " + str(e))


def retrieve(index_path: str, meta_path: str, query: str, model_name: str = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2', top_k: int = 5):
    SentenceTransformer = _import_sentence_transformer()
    model = SentenceTransformer(model_name)
    q_emb = model.encode([query], convert_to_numpy=True).astype('float32')
    import faiss
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


def summarize_with_transformers(contexts: List[str], model_name: str = 'sshleifer/distilbart-cnn-12-6') -> str:
    try:
        from transformers import pipeline
        summarizer = pipeline('summarization', model=model_name)
        joined = '\n\n'.join(contexts)
        # split if too long for model
        if len(joined) > 2000:
            joined = joined[:2000]
        out = summarizer(joined, truncation=True)
        return out[0]['summary_text']
    except Exception:
        return '\n'.join(c[:300] for c in contexts)


def build_report(results: List[dict]) -> str:
    contexts = []
    for r in results:
        try:
            with open(r['file_path'], 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception:
            text = ''
        snippet = text[:800]
        contexts.append(f"Source: {r['file_path']}\nScore: {r['score']:.3f}\nSnippet:\n{snippet}\n---")
    summary = summarize_with_transformers([c for c in contexts])
    report = f"Query Results Summary:\n\n{summary}\n\nDetails:\n\n" + '\n\n'.join(contexts)
    return report


def main(index_path: str, meta_path: str, query: str, out: str = None):
    results = retrieve(index_path, meta_path, query)
    report = build_report(results)
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(report)
        print('Report written to', out)
    else:
        print(report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', required=True)
    parser.add_argument('--meta', required=True)
    parser.add_argument('--query', required=True)
    parser.add_argument('--out', required=False)
    args = parser.parse_args()
    main(args.index, args.meta, args.query, args.out)
