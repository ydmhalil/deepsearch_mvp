from typing import List, Dict
import math


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 160) -> List[Dict]:
    """Chunk text into pieces with overlap. Returns list of dicts with 'text' and 'meta' keys."""
    if not text:
        return []
    tokens = text.split()
    if len(tokens) <= chunk_size:
        return [{'text': text, 'meta': {'tokens': len(tokens)}}]
    chunks = []
    start = 0
    chunk_id = 0
    step = chunk_size - overlap
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append({'text': ' '.join(chunk_tokens), 'meta': {'chunk_id': chunk_id, 'start_token': start, 'end_token': end}})
        chunk_id += 1
        if end == len(tokens):
            break
        start += step
    return chunks
