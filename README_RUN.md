Hızlı başlatma (Windows PowerShell):

1) Sanal ortam ve bağımlılıklar

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Ingest (örnek):

```powershell
python ingest.py --source "C:\\path\\to\\shared\\folder" --output .\data\chunks.jsonl
```

3) Embedding ve index oluşturma:

```powershell
python embed_index.py build --chunks .\data\chunks.jsonl --index .\data\faiss.index --meta .\data\meta.pkl
```

4) Arama örneği:

```powershell
python embed_index.py search --index .\data\faiss.index --meta .\data\meta.pkl --query "fırlatma kontrol talimatları" --topk 5
```

Not: İlk kurulumda Sentence-Transformers modelleri indirilecektir. Kurum içi offline kurulum için modelleri önceden indirip modeli local bir yol ile çağırmak gerekir.
