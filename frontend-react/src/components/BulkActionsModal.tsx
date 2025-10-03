import { useState } from 'react';
import { 
  X, 
  CheckSquare, 
  Tag, 
  Trash2, 
  Download, 
  AlertTriangle,
  Loader,
  CheckCircle
} from 'lucide-react';
import type { Document, ProfessionalCategory, SecurityLevel } from '../types';

interface BulkActionsModalProps {
  selectedDocuments: Document[];
  categories: ProfessionalCategory[];
  securityLevels: SecurityLevel[];
  isOpen: boolean;
  onClose: () => void;
  onActionComplete: (action: string, count: number) => void;
}

type BulkActionType = 'classify' | 'delete' | 'download' | 'reindex';

interface BulkClassifyData {
  categoryId: string;
  securityLevelId: string;
  notes: string;
}

export default function BulkActionsModal({
  selectedDocuments,
  categories,
  securityLevels,
  isOpen,
  onClose,
  onActionComplete
}: BulkActionsModalProps) {
  const [activeAction, setActiveAction] = useState<BulkActionType | null>(null);
  const [loading, setLoading] = useState(false);
  const [classifyData, setClassifyData] = useState<BulkClassifyData>({
    categoryId: '',
    securityLevelId: '',
    notes: ''
  });
  const [progress, setProgress] = useState<{current: number; total: number}>({ current: 0, total: 0 });

  if (!isOpen || selectedDocuments.length === 0) return null;

  const handleBulkClassify = async () => {
    if (!classifyData.categoryId || !classifyData.securityLevelId) return;

    setLoading(true);
    setProgress({ current: 0, total: selectedDocuments.length });

    try {
      let successCount = 0;
      
      for (let i = 0; i < selectedDocuments.length; i++) {
        const doc = selectedDocuments[i];
        setProgress({ current: i + 1, total: selectedDocuments.length });

        try {
          const response = await fetch('/api/classification/classify-document', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              document_id: doc.id,
              category_id: parseInt(classifyData.categoryId),
              security_level_id: parseInt(classifyData.securityLevelId),
              classified_by: 1, // Current user ID
              notes: classifyData.notes
            })
          });

          if (response.ok) {
            successCount++;
          }
        } catch (error) {
          console.error(`Failed to classify document ${doc.id}:`, error);
        }

        // Small delay to show progress
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      onActionComplete('classify', successCount);
      setActiveAction(null);
      setClassifyData({ categoryId: '', securityLevelId: '', notes: '' });
      
    } catch (error) {
      console.error('Bulk classification failed:', error);
      alert('Toplu sınıflandırma başarısız oldu');
    } finally {
      setLoading(false);
      setProgress({ current: 0, total: 0 });
    }
  };

  const handleBulkDelete = async () => {
    if (!confirm(`${selectedDocuments.length} belgeyi silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.`)) {
      return;
    }

    setLoading(true);
    setProgress({ current: 0, total: selectedDocuments.length });

    try {
      let successCount = 0;
      
      for (let i = 0; i < selectedDocuments.length; i++) {
        const doc = selectedDocuments[i];
        setProgress({ current: i + 1, total: selectedDocuments.length });

        try {
          const response = await fetch(`/api/documents/${doc.id}`, {
            method: 'DELETE'
          });

          if (response.ok) {
            successCount++;
          }
        } catch (error) {
          console.error(`Failed to delete document ${doc.id}:`, error);
        }

        await new Promise(resolve => setTimeout(resolve, 50));
      }

      onActionComplete('delete', successCount);
      setActiveAction(null);
      
    } catch (error) {
      console.error('Bulk delete failed:', error);
      alert('Toplu silme başarısız oldu');
    } finally {
      setLoading(false);
      setProgress({ current: 0, total: 0 });
    }
  };

  const handleBulkDownload = async () => {
    setLoading(true);
    setProgress({ current: 0, total: selectedDocuments.length });

    try {
      for (let i = 0; i < selectedDocuments.length; i++) {
        const doc = selectedDocuments[i];
        setProgress({ current: i + 1, total: selectedDocuments.length });

        try {
          const response = await fetch(`/api/documents/${doc.id}/download`);
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = window.document.createElement('a');
          a.href = url;
          a.download = doc.filename;
          window.document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          window.document.body.removeChild(a);
        } catch (error) {
          console.error(`Failed to download document ${doc.id}:`, error);
        }

        await new Promise(resolve => setTimeout(resolve, 500)); // Delay between downloads
      }

      onActionComplete('download', selectedDocuments.length);
      setActiveAction(null);
      
    } catch (error) {
      console.error('Bulk download failed:', error);
      alert('Toplu indirme başarısız oldu');
    } finally {
      setLoading(false);
      setProgress({ current: 0, total: 0 });
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const totalSize = selectedDocuments.reduce((acc, doc) => acc + doc.file_size, 0);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Toplu İşlemler ({selectedDocuments.length} belge)
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={loading}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Bar */}
        {loading && (
          <div className="px-6 py-4 border-b border-gray-200 bg-blue-50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-blue-900">İşlem devam ediyor...</span>
              <span className="text-sm text-blue-700">{progress.current}/{progress.total}</span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Selected Documents Summary */}
        <div className="p-6 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Seçili Belgeler</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Toplam Belge:</span>
              <div className="font-medium">{selectedDocuments.length}</div>
            </div>
            <div>
              <span className="text-gray-500">Toplam Boyut:</span>
              <div className="font-medium">{formatFileSize(totalSize)}</div>
            </div>
            <div>
              <span className="text-gray-500">Dosya Türleri:</span>
              <div className="font-medium">
                {Array.from(new Set(selectedDocuments.map(d => d.file_type))).join(', ').toUpperCase()}
              </div>
            </div>
          </div>

          {/* Document List Preview */}
          <div className="mt-4 max-h-32 overflow-y-auto bg-white rounded border">
            {selectedDocuments.slice(0, 5).map((doc) => (
              <div key={doc.id} className="flex items-center justify-between px-3 py-2 border-b border-gray-100 last:border-b-0">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <CheckSquare className="w-4 h-4 text-green-500 flex-shrink-0" />
                  <span className="text-sm text-gray-700 truncate">{doc.filename}</span>
                </div>
                <span className="text-xs text-gray-500 ml-2">{formatFileSize(doc.file_size)}</span>
              </div>
            ))}
            {selectedDocuments.length > 5 && (
              <div className="px-3 py-2 text-xs text-gray-500 text-center bg-gray-50">
                +{selectedDocuments.length - 5} belge daha...
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        {!activeAction && !loading && (
          <div className="p-6 space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Yapılacak İşlemi Seçin</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setActiveAction('classify')}
                className="flex items-center justify-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-[var(--primary-color)] hover:bg-[var(--primary-light)] transition-all group"
              >
                <Tag className="w-6 h-6 text-gray-400 group-hover:text-[var(--primary-color)]" />
                <div className="text-left">
                  <div className="font-medium text-gray-900">Sınıflandır</div>
                  <div className="text-sm text-gray-500">Kategori ve güvenlik seviyesi ata</div>
                </div>
              </button>

              <button
                onClick={() => setActiveAction('download')}
                className="flex items-center justify-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all group"
              >
                <Download className="w-6 h-6 text-gray-400 group-hover:text-green-500" />
                <div className="text-left">
                  <div className="font-medium text-gray-900">İndir</div>
                  <div className="text-sm text-gray-500">Tüm belgeleri indir</div>
                </div>
              </button>

              <button
                onClick={() => setActiveAction('delete')}
                className="flex items-center justify-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-red-500 hover:bg-red-50 transition-all group"
              >
                <Trash2 className="w-6 h-6 text-gray-400 group-hover:text-red-500" />
                <div className="text-left">
                  <div className="font-medium text-gray-900">Sil</div>
                  <div className="text-sm text-gray-500">Belgeleri kalıcı olarak sil</div>
                </div>
              </button>

              <button
                onClick={() => setActiveAction('reindex')}
                className="flex items-center justify-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-yellow-500 hover:bg-yellow-50 transition-all group"
              >
                <CheckCircle className="w-6 h-6 text-gray-400 group-hover:text-yellow-500" />
                <div className="text-left">
                  <div className="font-medium text-gray-900">Yeniden İndeksle</div>
                  <div className="text-sm text-gray-500">Arama indeksini güncelle</div>
                </div>
              </button>
            </div>
          </div>
        )}

        {/* Classify Form */}
        {activeAction === 'classify' && !loading && (
          <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Toplu Sınıflandırma</h3>
              <button
                onClick={() => setActiveAction(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Kategori *
                </label>
                <select
                  value={classifyData.categoryId}
                  onChange={(e) => setClassifyData({ ...classifyData, categoryId: e.target.value })}
                  className="input-field"
                  required
                >
                  <option value="">Kategori seçin</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Güvenlik Seviyesi *
                </label>
                <select
                  value={classifyData.securityLevelId}
                  onChange={(e) => setClassifyData({ ...classifyData, securityLevelId: e.target.value })}
                  className="input-field"
                  required
                >
                  <option value="">Güvenlik seviyesi seçin</option>
                  {securityLevels.map(level => (
                    <option key={level.id} value={level.id}>
                      {level.name} (Seviye {level.level_number})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notlar
                </label>
                <textarea
                  value={classifyData.notes}
                  onChange={(e) => setClassifyData({ ...classifyData, notes: e.target.value })}
                  placeholder="Toplu sınıflandırma notları..."
                  className="input-field"
                  rows={3}
                />
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-yellow-800">
                    <p className="font-medium mb-1">Dikkat!</p>
                    <p>
                      Bu işlem {selectedDocuments.length} belgenin sınıflandırmasını değiştirecektir. 
                      Mevcut sınıflandırmalar üzerine yazılacaktır.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
                <button
                  onClick={() => setActiveAction(null)}
                  className="btn-secondary"
                >
                  İptal
                </button>
                <button
                  onClick={handleBulkClassify}
                  className="btn-primary flex items-center gap-2"
                  disabled={!classifyData.categoryId || !classifyData.securityLevelId}
                >
                  <Tag className="w-4 h-4" />
                  Sınıflandır ({selectedDocuments.length})
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation */}
        {activeAction === 'delete' && !loading && (
          <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Toplu Silme</h3>
              <button
                onClick={() => setActiveAction(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-red-800">
                  <p className="font-medium mb-1">Tehlikeli İşlem!</p>
                  <p>
                    {selectedDocuments.length} belge kalıcı olarak silinecektir. 
                    Bu işlem geri alınamaz ve tüm ilişkili veriler kaybolacaktır.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                onClick={() => setActiveAction(null)}
                className="btn-secondary"
              >
                İptal
              </button>
              <button
                onClick={handleBulkDelete}
                className="bg-red-600 hover:bg-red-700 text-white font-medium px-6 py-2.5 rounded-lg transition-colors duration-200 flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Kalıcı Olarak Sil ({selectedDocuments.length})
              </button>
            </div>
          </div>
        )}

        {/* Download Confirmation */}
        {activeAction === 'download' && !loading && (
          <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Toplu İndirme</h3>
              <button
                onClick={() => setActiveAction(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">İndirme Bilgileri</p>
                <p>
                  {selectedDocuments.length} belge indirilecektir. 
                  Toplam boyut: {formatFileSize(totalSize)}. 
                  Her dosya ayrı ayrı indirilecektir.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                onClick={() => setActiveAction(null)}
                className="btn-secondary"
              >
                İptal
              </button>
              <button
                onClick={handleBulkDownload}
                className="btn-primary flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                İndirmeyi Başlat ({selectedDocuments.length})
              </button>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="p-6 text-center">
            <Loader className="w-8 h-8 text-[var(--primary-color)] animate-spin mx-auto mb-4" />
            <p className="text-gray-600">İşlem devam ediyor...</p>
          </div>
        )}
      </div>
    </div>
  );
}