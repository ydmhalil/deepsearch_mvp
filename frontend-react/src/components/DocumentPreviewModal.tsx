import { useState, useEffect } from 'react';
import { X, Download, Eye, FileText, AlertCircle, Clock, CheckCircle } from 'lucide-react';
import { api } from '../utils/api';
import type { Document } from '../types';

interface DocumentPreviewModalProps {
  document: Document | null;
  isOpen: boolean;
  onClose: () => void;
}

interface DocumentContent {
  content: string;
  metadata: {
    pages?: number;
    word_count?: number;
    char_count?: number;
    file_type?: string;
  };
}

export default function DocumentPreviewModal({
  document,
  isOpen,
  onClose
}: DocumentPreviewModalProps) {
  const [content, setContent] = useState<DocumentContent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && document) {
      loadDocumentContent();
    }
  }, [isOpen, document]);

  const loadDocumentContent = async () => {
    if (!document) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.getDocumentPreview(document.file_path);
      setContent(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'İçerik yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const downloadDocument = async () => {
    if (!document) return;

    try {
      // Create download link
      const response = await fetch(`/api/documents/${document.id}/download`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = document.filename;
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Dosya indirilemedi');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'indexed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing': return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  if (!isOpen || !document) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 flex-shrink-0">
          <div className="flex items-center gap-3">
            <FileText className="w-6 h-6 text-[var(--primary-color)]" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{document.filename}</h2>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>{formatFileSize(document.file_size)}</span>
                <span>•</span>
                <span>{document.file_type?.toUpperCase()}</span>
                <span>•</span>
                <div className="flex items-center gap-1">
                  {getStatusIcon(document.status)}
                  <span className="capitalize">{document.status}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={downloadDocument}
              className="btn-secondary flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              İndir
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Document Info */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex-shrink-0">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Yüklenme Tarihi:</span>
              <div className="font-medium">{new Date(document.upload_date).toLocaleDateString('tr-TR')}</div>
            </div>
            <div>
              <span className="text-gray-500">Dosya Yolu:</span>
              <div className="font-medium text-xs text-gray-600 truncate">{document.file_path}</div>
            </div>
            {document.page_count && (
              <div>
                <span className="text-gray-500">Sayfa Sayısı:</span>
                <div className="font-medium">{document.page_count}</div>
              </div>
            )}
            {content?.metadata?.word_count && (
              <div>
                <span className="text-gray-500">Kelime Sayısı:</span>
                <div className="font-medium">{content.metadata.word_count.toLocaleString()}</div>
              </div>
            )}
          </div>
        </div>

        {/* Classification Info */}
        {document.classification && (
          <div className="px-6 py-4 border-b border-gray-200 bg-blue-50 flex-shrink-0">
            <h3 className="text-sm font-medium text-blue-900 mb-2">Sınıflandırma Bilgileri</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-blue-700">Kategori:</span>
                <span className="ml-2 font-medium">{document.classification.category.name}</span>
              </div>
              <div>
                <span className="text-blue-700">Güvenlik Seviyesi:</span>
                <span className="ml-2 font-medium">
                  {document.classification.security_level.name} 
                  (Seviye {document.classification.security_level.level_number})
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary-color)] mx-auto mb-4"></div>
                <p className="text-gray-600">İçerik yükleniyor...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">İçerik Yüklenemedi</h3>
                <p className="text-gray-600 mb-4">{error}</p>
                <button 
                  onClick={loadDocumentContent}
                  className="btn-primary"
                >
                  Tekrar Dene
                </button>
              </div>
            </div>
          ) : content ? (
            <div className="h-full overflow-y-auto">
              <div className="p-6">
                {/* Content Preview */}
                <div className="bg-white border border-gray-200 rounded-lg">
                  <div className="border-b border-gray-200 px-4 py-2 bg-gray-50">
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700">Belge İçeriği</span>
                      {content.metadata.char_count && (
                        <span className="text-xs text-gray-500">
                          ({content.metadata.char_count.toLocaleString()} karakter)
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="p-4">
                    {document.file_type === 'pdf' || document.file_type === 'docx' ? (
                      <div className="prose max-w-none">
                        <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed">
                          {content.content.length > 10000 
                            ? content.content.substring(0, 10000) + '\n\n[İçerik kesildi - tam içerik için dosyayı indirin]'
                            : content.content
                          }
                        </pre>
                      </div>
                    ) : document.file_type === 'txt' ? (
                      <div className="font-mono text-sm">
                        <pre className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                          {content.content}
                        </pre>
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">Önizleme Desteklenmiyor</h3>
                        <p className="text-gray-600 mb-4">
                          Bu dosya türü için önizleme mevcut değil. Dosyayı indirerek görüntüleyebilirsiniz.
                        </p>
                        <button
                          onClick={downloadDocument}
                          className="btn-primary flex items-center gap-2 mx-auto"
                        >
                          <Download className="w-4 h-4" />
                          Dosyayı İndir
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Son güncelleme: {new Date(document.upload_date).toLocaleString('tr-TR')}
            </div>
            <button
              onClick={onClose}
              className="btn-secondary"
            >
              Kapat
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}