import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search as SearchIcon, Filter, FileText, X, Loader, AlertCircle } from 'lucide-react';
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

          <div className="space-y-4 mb-8">
            {paginatedResults.map((result, index) => (
              <div key={index} className="card p-6 hover:shadow-xl transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <FileText className="w-6 h-6 text-[var(--primary-color)] flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-gray-900 truncate">
                        {result.file_name}
                      </h3>
                      <p className="text-sm text-gray-500 truncate">{result.file_path}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                      {Math.round(result.score)}% eşleşme
                    </span>
                  </div>
                </div>

                <p className="text-gray-700 leading-relaxed mb-3">{result.chunk_text}</p>

                {result.metadata?.page && (
                  <p className="text-sm text-gray-500">Sayfa: {result.metadata.page}</p>
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
