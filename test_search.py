#!/usr/bin/env python3
"""
Quick search test script to verify model consistency
"""

from embed_index import search

def test_search():
    query = "fırlatma prosedürleri"
    print(f"Testing search for: '{query}'")
    
    try:
        results = search(
            './data/faiss.index', 
            './data/meta.pkl', 
            query, 
            'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
            3
        )
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results):
            print(f"{i+1}. Score: {result['score']:.4f}")
            print(f"   File: {result['file_path']}")
            if 'meta' in result and 'text' in result['meta']:
                text = result['meta']['text'][:100]
                print(f"   Text: {text}...")
            print()
            
    except Exception as e:
        print(f"Search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search()