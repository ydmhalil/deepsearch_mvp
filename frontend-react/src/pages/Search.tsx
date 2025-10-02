import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search as SearchIcon, Filter, FileText, X, Loader, AlertCircle, Target, Hash, BookOpen } from 'lucide-react';
import { api } from '../utils/api';
import type { SearchResult, SearchType } from '../types';

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [searchType, setSearchType] = useState<SearchType>('semantic');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedFileTypes, setSelectedFileTypes] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const resultsPerPage = 10;

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
      performSearch(q, searchType);
    }
  }, [searchParams]);

  const performSearch = async (searchQuery: string, type: SearchType) => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.search(searchQuery, type, 50);
      setResults(response.results);
      setCurrentPage(1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Arama başarısız');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setSearchParams({ q: query });
      performSearch(query, searchType);
    }
  };

  const toggleFileType = (type: string) => {
    setSelectedFileTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const filteredResults = results.filter((result) => {
    if (selectedFileTypes.length === 0) return true;
    const extension = result.file_name.split('.').pop()?.toLowerCase();
    return extension && selectedFileTypes.includes(extension);
  });

  const paginatedResults = filteredResults.slice(
    (currentPage - 1) * resultsPerPage,
    currentPage * resultsPerPage
  );

  const totalPages = Math.ceil(filteredResults.length / resultsPerPage);

  const fileTypes = ['pdf', 'docx', 'xlsx', 'pptx', 'txt'];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Belge Arama</h1>

        <form onSubmit={handleSearch} className="mb-6">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <SearchIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Belgelerinizde arama yapın..."
                className="input-field pl-12"
              />
            </div>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? <Loader className="w-5 h-5 animate-spin" /> : 'Ara'}
            </button>
          </div>

          <div className="flex items-center gap-4 mt-4">
            <div className="flex gap-2">
              {(['semantic', 'keyword', 'comprehensive'] as SearchType[]).map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setSearchType(type)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    searchType === type
                      ? 'bg-[var(--primary-color)] text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {type === 'semantic'
                    ? 'Semantik'
                    : type === 'keyword'
                    ? 'Keyword'
                    : 'Kapsamlı'}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Filter className="w-5 h-5" />
              <span>Filtreler</span>
            </button>
          </div>
        </form>

        {showFilters && (
          <div className="card p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-gray-900">Dosya Türü</h3>
              <button
                onClick={() => setShowFilters(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {fileTypes.map((type) => (
                <button
                  key={type}
                  onClick={() => toggleFileType(type)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedFileTypes.includes(type)
                      ? 'bg-[var(--primary-color)] text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  .{type}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="card p-6 mb-6 border-l-4 border-red-500">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-gray-900">Arama Hatası</h3>
              <p className="text-sm text-gray-600">{error}</p>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="text-center py-12">
          <Loader className="w-12 h-12 text-[var(--primary-color)] animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Aranıyor...</p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div>
          <div className="mb-6">
            <p className="text-gray-600">
              <span className="font-semibold">{filteredResults.length}</span> sonuç bulundu
              {selectedFileTypes.length > 0 && (
                <span className="ml-2 text-sm">
                  (Filtre: {selectedFileTypes.map((t) => `.${t}`).join(', ')})
                </span>
              )}
            </p>
          </div>

          <div className="space-y-6 mb-8">
            {paginatedResults.map((result, index) => (
              <div key={index} className="card p-6 hover:shadow-xl transition-shadow border-l-4 border-l-[var(--primary-color)]">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <FileText className="w-6 h-6 text-[var(--primary-color)] flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-gray-900 truncate text-lg">
                        {result.file_name}
                      </h3>
                      <p className="text-sm text-gray-500 truncate">{result.file_path}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                      result.score >= 80 ? 'bg-green-100 text-green-800' :
                      result.score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {Math.round(result.score)}% eşleşme
                    </span>
                  </div>
                </div>

                {/* Classification Info */}
                {result.classification && (
                  <div className="mb-4 p-3 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`w-3 h-3 rounded-full`} style={{backgroundColor: '#667eea'}}></span>
                        <span className="text-sm font-medium text-gray-700">Belge Sınıflandırma</span>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        result.classification.access_granted ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {result.classification.access_granted ? 'Erişim İzni Var' : 'Erişim Kısıtlı'}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <span className="text-gray-500">Kategori:</span>
                        <div className="font-semibold text-gray-900">{result.classification.category.name}</div>
                        {result.classification.category.confidence > 0 && (
                          <div className="text-gray-500">Güven: %{Math.round(result.classification.category.confidence * 100)}</div>
                        )}
                      </div>
                      <div>
                        <span className="text-gray-500">Güvenlik Seviyesi:</span>
                        <div className="font-semibold text-gray-900">
                          {result.classification.security_level.name} (Seviye {result.classification.security_level.level_number})
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Semantic Analysis */}
                {result.semantic_analysis && (
                  <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="w-4 h-4 text-[var(--primary-color)]" />
                      <span className="text-sm font-medium text-gray-700">Anlam Analizi</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                      <div>
                        <span className="text-gray-500">Kelime Eşleşme:</span>
                        <div className="font-semibold text-gray-900">
                          {result.semantic_analysis.exact_keyword_matches}/{result.semantic_analysis.total_keywords}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Eşleşme Oranı:</span>
                        <div className="font-semibold text-gray-900">%{result.semantic_analysis.match_ratio}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Kategori:</span>
                        <div className="font-semibold text-gray-900 capitalize">{result.semantic_analysis.dominant_category}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Kelime Yoğunluğu:</span>
                        <div className="font-semibold text-gray-900">%{result.semantic_analysis.word_density}</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Content Preview */}
                <div className="mb-4">
                  <p className="text-gray-700 leading-relaxed mb-2">{result.chunk_text}</p>
                  
                  {/* Highlighted Keywords */}
                  {result.highlights?.matched_words && result.highlights.matched_words.length > 0 && (
                    <div className="flex items-center gap-2 mb-2">
                      <Hash className="w-4 h-4 text-[var(--primary-color)]" />
                      <span className="text-sm text-gray-600">Eşleşen kelimeler:</span>
                      <div className="flex flex-wrap gap-1">
                        {result.highlights.matched_words.map((word, i) => (
                          <span 
                            key={i} 
                            className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-medium"
                          >
                            {word}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Section and Context */}
                <div className="border-t pt-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Section Info */}
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <BookOpen className="w-4 h-4 text-[var(--primary-color)]" />
                        <span className="text-sm font-medium text-gray-700">Bölüm</span>
                      </div>
                      <p className="text-sm text-gray-600">{result.metadata?.section || 'Belirtilmemiş'}</p>
                      {result.metadata?.page && (
                        <p className="text-xs text-gray-500 mt-1">Sayfa: {result.metadata.page}</p>
                      )}
                    </div>

                    {/* Best Context */}
                    {result.highlights?.best_context && (
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <Target className="w-4 h-4 text-[var(--primary-color)]" />
                          <span className="text-sm font-medium text-gray-700">En İlgili Bağlam</span>
                        </div>
                        <p className="text-sm text-gray-600 italic">"{result.highlights.best_context}"</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Keyword Matches Detail */}
                {result.keyword_matches && result.keyword_matches.length > 0 && (
                  <div className="mt-4 pt-3 border-t">
                    <details className="group">
                      <summary className="cursor-pointer text-sm font-medium text-[var(--primary-color)] hover:text-[var(--primary-dark)] flex items-center gap-2">
                        <span>Detaylı Kelime Eşleşmeleri ({result.keyword_matches.length})</span>
                        <span className="group-open:rotate-180 transition-transform">▼</span>
                      </summary>
                      <div className="mt-3 space-y-2">
                        {result.keyword_matches.slice(0, 3).map((match, i) => (
                          <div key={i} className="p-3 bg-gray-50 rounded">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                {match.match_count} kelime eşleşmesi
                              </span>
                            </div>
                            <p className="text-sm text-gray-700">"{match.context}"</p>
                            <div className="flex flex-wrap gap-1 mt-2">
                              {match.matched_words.map((word, j) => (
                                <span key={j} className="text-xs bg-blue-50 text-blue-700 px-1 py-0.5 rounded">
                                  {word}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Önceki
              </button>
              <span className="text-gray-600">
                Sayfa {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Sonraki
              </button>
            </div>
          )}
        </div>
      )}

      {!loading && !error && results.length === 0 && query && (
        <div className="text-center py-12">
          <SearchIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Sonuç bulunamadı</h3>
          <p className="text-gray-600">
            "{query}" için eşleşen belge bulunamadı. Farklı bir arama terimi deneyin.
          </p>
        </div>
      )}
    </div>
  );
}
