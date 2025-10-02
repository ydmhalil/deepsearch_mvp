# DeepSearch MVP - Frontend Development Prompt

## 📋 Proje Özeti
Savunma sanayi şirketleri için geliştirilmiş **offline belge arama ve RAG sistemi**. 
Kullanıcılar yerel belgelerini yükleyebilir, AI destekli arama yapabilir ve 
conversational AI ile etkileşimde bulunabilir.

## 🏗️ Mevcut Backend Teknoloji Stack
- **Framework**: Flask (Python)
- **Vector Database**: FAISS (Facebook AI Similarity Search)
- **Embedding Model**: sentence-transformers (all-MiniLM-L6-v2 + domain-specific)
- **LLM**: Ollama + Gemma2 (local inference)
- **Document Processing**: PyPDF2, python-docx, openpyxl, python-pptx
- **Authentication**: Flask-Login with session management
- **Storage**: Local filesystem + SQLite for metadata

## 🎨 Frontend Gereksinimleri

### 1. **Ana Sayfa (Landing Page)**
- **Hero Section**: Gradient background, search bar prominent
- **Feature Cards**: Document upload, AI search, analytics
- **Statistics Grid**: Total documents, indexed files, recent searches
- **CTA Buttons**: "Doküman Yükle", "Arama Yap", "Analytics"

### 2. **Doküman Yükleme Sayfası**
- **Drag & Drop Area**: Multi-file upload (PDF, DOCX, XLSX, PPTX, TXT)
- **Progress Indicators**: Real-time upload progress with file previews
- **File List**: Uploaded documents with status (indexed/pending)
- **Validation**: File type, size limits (50MB), error handling
- **Batch Operations**: Select multiple files, bulk delete/index

### 3. **Arama Sonuçları Sayfası**
- **Search Interface**: Query input with type selection (semantic/keyword/comprehensive)
- **Results Grid**: Document cards with relevance scores, snippets
- **Filters Sidebar**: File type, date range, relevance threshold
- **Pagination**: Handle 100+ results efficiently
- **Preview Modal**: Quick document preview without navigation

### 4. **RAG Chat Interface**
- **Chat Window**: WhatsApp-style conversation UI
- **Message Types**: User queries, AI responses, source citations
- **Typing Indicators**: Real-time response generation feedback
- **Session Management**: Multiple chat sessions, history
- **Quick Actions**: Predefined questions, follow-up suggestions
- **Source References**: Clickable document references with highlights

### 5. **Doküman Önizleme**
- **Document Viewer**: Text display with zoom, wrap controls
- **Toolbar**: Print, copy, download, navigation controls
- **Statistics**: Character count, word count, file size
- **Search Highlighting**: Highlight search terms in document
- **Responsive Text**: Mobile-friendly text rendering

### 6. **Dashboard & Analytics**
- **Usage Statistics**: Search frequency, popular documents
- **System Status**: Index health, processing queue
- **User Activity**: Recent searches, session analytics
- **Performance Metrics**: Response times, success rates

## 🎯 Teknik Gereksinimler

### **Frontend Framework Seçimi**
**Önerilen**: Modern React/Vue.js SPA VEYA Flask+Jinja2 (mevcut backend ile uyum)

```javascript
// React örneği - API Integration
const searchDocuments = async (query, searchType) => {
  const response = await fetch('/api/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      query, 
      search_type: searchType,
      top_k: 10 
    })
  });
  return response.json();
};
```

### **Backend API Endpoints (Mevcut)**
```python
# Ana endpoint'ler
POST /api/search          # Doküman arama
POST /upload_file         # Dosya yükleme  
POST /rag/query          # RAG chat
GET  /preview            # Doküman önizleme
POST /index_file         # Dosya indeksleme
GET  /analytics          # İstatistikler
```

### **State Management**
```javascript
// Global state structure
{
  documents: [],
  searchResults: [],
  chatSessions: [],
  currentUser: {},
  systemStatus: {
    indexedFiles: 0,
    processingQueue: 0,
    systemHealth: 'good'
  }
}
```

## 🎨 Tasarım Sistemi Gereksinimleri

### **Renk Paleti** (Mevcut CSS değişkenleri)
```css
:root {
  --primary-color: #667eea;
  --primary-dark: #4f46e5;
  --primary-light: #f0f4ff;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --danger-color: #ef4444;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --background-light: #f8fafc;
  --border-color: #e5e7eb;
}
```

### **Component Library**
```javascript
// Gerekli component'ler
<SearchBar onSearch={handleSearch} />
<DocumentCard document={doc} onPreview={openPreview} />
<ChatInterface sessionId={id} />
<UploadZone onUpload={handleUpload} />
<ProgressBar progress={uploadProgress} />
<Pagination currentPage={page} totalPages={total} />
<FilterSidebar filters={filters} onChange={updateFilters} />
```

### **Responsive Breakpoints**
```css
/* Mobile First Design */
@media (min-width: 768px)  { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
@media (min-width: 1280px) { /* Large Desktop */ }
```

## 🔄 Real-time Features

### **WebSocket Integration** (Optional Enhancement)
```javascript
// Real-time updates için
const socket = new WebSocket('ws://localhost:5000/ws');
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'indexing_complete') {
    updateDocumentStatus(data.documentId, 'indexed');
  }
};
```

### **File Upload Progress**
```javascript
const uploadFile = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  return fetch('/upload_file', {
    method: 'POST',
    body: formData
  }).then(response => response.json());
};
```

## 🛡️ Güvenlik Gereksinimleri

### **Authentication**
```javascript
// JWT token management
const authCheck = () => {
  const token = localStorage.getItem('auth_token');
  return fetch('/api/auth/verify', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
};
```

### **File Validation**
```javascript
const validateFile = (file) => {
  const allowedTypes = ['.pdf', '.docx', '.xlsx', '.pptx', '.txt'];
  const maxSize = 50 * 1024 * 1024; // 50MB
  
  return allowedTypes.includes(getFileExtension(file.name)) && 
         file.size <= maxSize;
};
```

## 📱 Performance Requirements

### **Lazy Loading**
```javascript
// Büyük doküman listleri için
const LazyDocumentList = () => {
  const [documents, setDocuments] = useState([]);
  const [page, setPage] = useState(1);
  
  useEffect(() => {
    loadDocuments(page).then(setDocuments);
  }, [page]);
};
```

### **Caching Strategy**
```javascript
// Search result cache
const searchCache = new Map();
const cachedSearch = (query) => {
  if (searchCache.has(query)) {
    return Promise.resolve(searchCache.get(query));
  }
  return searchDocuments(query).then(results => {
    searchCache.set(query, results);
    return results;
  });
};
```

## 🎯 Kullanıcı Deneyimi (UX) Gereksinimleri

### **Loading States**
- Skeleton screens for document loading
- Progress indicators for file uploads
- Typing indicators for RAG chat
- Search result loading animations

### **Error Handling**
```javascript
const ErrorBoundary = ({ children }) => {
  // Global error handling
  // Network error recovery
  // User-friendly error messages
};
```

### **Accessibility (A11Y)**
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode
- Focus management

### **Mobile Optimization**
- Touch-friendly interface
- Swipe gestures for navigation
- Mobile-first responsive design
- Offline functionality awareness

## 🚀 Deployment Considerations

### **Build Process**
```json
{
  "scripts": {
    "build": "webpack --mode production",
    "dev": "webpack serve --mode development",
    "test": "jest",
    "lint": "eslint src/"
  }
}
```

### **Integration with Flask**
```python
# Flask static file serving
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('dist', filename)
```

## 📋 Acceptance Criteria

### **Functional Requirements**
✅ Tüm API endpoint'leri ile uyumlu çalışma
✅ Multi-format file upload (drag & drop)
✅ Real-time search with type selection
✅ Conversational AI chat interface
✅ Document preview functionality
✅ Responsive design (mobile/tablet/desktop)
✅ User authentication integration

### **Performance Requirements**
✅ Search results < 3 seconds
✅ File upload progress indicators
✅ Lazy loading for large datasets
✅ Optimized bundle size < 2MB
✅ 60fps smooth animations

### **Browser Compatibility**
✅ Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
✅ Mobile browsers (iOS Safari, Chrome Mobile)

## 🎨 Örnek Wireframe Structure

```
Header: [Logo] [Navigation] [User Profile]
├── Ana Sayfa
│   ├── Hero Section (Search Bar)
│   ├── Quick Stats Grid
│   └── Feature Cards
├── Doküman Yükleme
│   ├── Drag & Drop Zone
│   ├── File List
│   └── Progress Area
├── Arama Sonuçları
│   ├── Search Interface
│   ├── Filters Sidebar
│   └── Results Grid
├── RAG Chat
│   ├── Chat Window
│   ├── Input Area
│   └── Session Sidebar
└── Önizleme
    ├── Document Viewer
    ├── Control Toolbar
    └── Stats Panel
```

## 🔧 Mevcut Sistem API Endpoints

### **Arama Endpoints**
```python
POST /api/search
{
  "query": "güvenlik prosedürleri",
  "search_type": "semantic|keyword|comprehensive",
  "top_k": 10,
  "filters": {
    "file_type": ["pdf", "docx"],
    "date_range": "last_month"
  }
}
```

### **Upload Endpoints**
```python
POST /upload_file
Content-Type: multipart/form-data
files: [File1, File2, ...]

Response:
{
  "success": true,
  "uploaded_files": [
    {
      "filename": "document.pdf",
      "file_id": "12345",
      "status": "processing"
    }
  ]
}
```

### **RAG Chat Endpoints**
```python
POST /rag/query
{
  "question": "Güvenlik prosedürleri hakkında bilgi ver",
  "session_id": "abc123",
  "type": "conversational|comprehensive"
}

Response:
{
  "success": true,
  "answer": "Güvenlik prosedürleri...",
  "sources": [
    {
      "file_path": "security.pdf",
      "chunk_text": "...",
      "score": 0.85
    }
  ],
  "follow_up_questions": [
    "Siber güvenlik hakkında ne biliyorsun?",
    "Fiziksel güvenlik önlemleri nelerdir?"
  ]
}
```

### **Preview Endpoints**
```python
GET /preview?path=uploads/document.pdf
Response: HTML page with document content

GET /api/document/content/{document_id}
Response:
{
  "content": "Document text content...",
  "metadata": {
    "file_name": "document.pdf",
    "file_size": 1024000,
    "page_count": 10
  }
}
```

## 🎯 Domain-Specific Features

### **Savunma Sanayi Terminolojisi**
Sistem 185 savunma sanayi terimini anlayabilir:
```javascript
const defenseTerms = {
  "güvenlik": ["security", "safety", "koruma", "emniyet"],
  "savunma": ["defense", "defence", "müdafaa"],
  "sistem": ["system", "architecture", "altyapı"],
  "roket": ["rocket", "missile", "füze"],
  "radar": ["radar", "detection", "algılama"]
  // ... 185 total terms
};
```

### **Turkish Language Optimization**
- Türkçe karakter desteği (ç, ğ, ı, ö, ş, ü)
- Domain-specific embedding model
- Turkish query enhancement
- Multilingual search capabilities

## 📊 Sistem Performance Benchmarks

### **Mevcut Performance Metrikleri**
- **Search Response**: 2-8 seconds average
- **Document Upload**: 2-30 seconds (size dependent)
- **RAG Chat Response**: 30-60 seconds (LLM processing)
- **Document Indexing**: 5-10 seconds per document
- **Memory Usage**: ~8-12 GB (embeddings + LLM)

### **Target Performance Goals**
- **Search Response**: < 3 seconds
- **File Upload**: Real-time progress feedback
- **Chat Response**: < 15 seconds with streaming
- **UI Responsiveness**: 60fps animations
- **Bundle Size**: < 2MB initial load

## 🔒 Security & Compliance

### **Data Privacy**
- Offline-first architecture (no external API calls)
- Local document storage
- Encrypted user sessions
- GDPR compliance ready

### **Authentication Features**
```python
# Mevcut auth system
- User registration/login
- Session management
- Role-based access (admin/user)
- Password policies
- Rate limiting
- Security event logging
```

## 🚀 Deployment Instructions

### **Development Setup**
```bash
# Backend
cd deepsearch_mvp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py

# Frontend (if React/Vue)
npm install
npm run dev
```

### **Production Deployment**
```python
# Flask production config
app.config['DEBUG'] = False
app.config['TESTING'] = False

# Use production WSGI server
# pip install waitress
from waitress import serve
serve(app, host='0.0.0.0', port=5000)
```

Bu prompt ile AI, projenizin tüm teknik gereksinimlerini anlayıp uyumlu bir frontend geliştirebilir! 🚀