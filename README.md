DeepSearch MVP

Amaç: Lokal: offline çalışan, dosya sistemindeki belgeleri ingest edip embedding için hazırlanmış chunk'ları oluşturan basit bir örnek.

İçerik:
- requirements.txt
- ingest.py (dosya tarama ve metin çıkarma)
- chunker.py (chunk'lama ve metadata)
- utils.py (dosya okuma, text extraction helpers)

Çalıştırma (Windows PowerShell):

Hızlı test (dependencies yüklemeden):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Örnek klasörü ingest et (example_docs içinde hazır .txt dosyaları var)
python ingest.py --source .\example_docs --output .\data\chunks.jsonl
```

Not: Bu MVP bazı paketlerin (pdfplumber, sentence-transformers vb.) yüklenmesini gerektirebilir. Örnek testi `example_docs` ile yapmak, PDF/DOCX bağımlılıklarını atlamanızı sağlar.

Not: Bu MVP internet erişimi gerektirebilir (ör. bazı pip paketleri indirirken). Prod ortamda paketleri iç ağdan erişilebilir bir paket index'e yüklemeyi öneririm.
