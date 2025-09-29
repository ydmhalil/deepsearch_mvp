# DeepSearch MVP - AI Agent Instructions

This is an offline document search and RAG system with a multi-stage pipeline and Flask web interface.

## Architecture Overview

**Core Pipeline**: `ingest.py` → `embed_index.py` → Flask app (`app.py`) → RAG (`rag.py`/`reporter.py`)

1. **Document Ingestion** (`ingest.py`): Scans directories, extracts text from PDF/DOCX/TXT using `utils.py`, chunks text via `chunker.py` 
2. **Embedding & Indexing** (`embed_index.py`): Creates FAISS vector index with sentence-transformers embeddings
3. **Web Search Interface** (`app.py`): Flask app serving search UI and file preview/download
4. **RAG Reporting** (`rag.py`, `reporter.py`): Generates summarized reports from search results

## Key Patterns & Conventions

### Error-Safe ML Dependencies
All ML imports (faiss, sentence-transformers, transformers) are wrapped in try/catch with helpful error messages:
```python
def _import_faiss():
    try:
        import faiss
        return faiss
    except Exception as e:
        raise ImportError("faiss is required for index operations: " + str(e))
```

### File Path Security 
`app.py` uses `safe_path()` to prevent directory traversal attacks - all file operations must go through this validation.

### Chunking Strategy
`chunker.py` implements sliding window with overlap (default: 800 tokens, 160 overlap) returning structured metadata including token positions and chunk IDs.

### Data Storage Convention
- `./data/chunks.jsonl`: Raw text chunks with metadata
- `./data/faiss.index`: FAISS vector index 
- `./data/meta.pkl`: Chunk metadata (file paths, positions)
- Reports saved to `./data/report*.txt`

## Development Workflow

### Environment Setup (Windows PowerShell)
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Testing with Sample Data
Use `example_docs/` folder to test without PDF/ML dependencies:
```powershell
python ingest.py --source .\example_docs --output .\data\chunks.jsonl
python embed_index.py build --chunks .\data\chunks.jsonl --index .\data\faiss.index --meta .\data\meta.pkl
python embed_index.py search --index .\data\faiss.index --meta .\data\meta.pkl --query "test query" --topk 5
```

### Flask Development
- Run with `python app.py` (debug=False, reloader=False to avoid Windows file watching issues)
- Production: Use waitress WSGI server (already in requirements.txt)
- UI supports Turkish language (templates have Turkish labels)

## Important Gotchas

- **First Run**: sentence-transformers downloads models (~100MB) - ensure internet access or pre-cache models
- **File Encoding**: `utils.py` tries UTF-8 first, falls back to latin-1 for problematic text files
- **Memory Limits**: File previews limited to 50KB, search snippets to 800 chars to prevent memory issues
- **Model Consistency**: Same embedding model must be used for both indexing and search (default: 'all-MiniLM-L6-v2')

## Integration Points

- **FAISS Index**: Normalized vectors for cosine similarity via inner product
- **Chunking Metadata**: Preserved through entire pipeline for result tracing
- **Flask Security**: Path validation prevents file system traversal
- **Report Generation**: `reporter.py` wraps `rag.py` with file I/O interface