import { useState } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';
import type { Document, ProfessionalCategory, SecurityLevel } from '../types';

interface DocumentDetailModalProps {
  document: Document | null;
  categories: ProfessionalCategory[];
  securityLevels: SecurityLevel[];
  isOpen: boolean;
  onClose: () => void;
  onSave: (document: Document) => void;
}

export default function DocumentDetailModal({
  document,
  categories,
  securityLevels,
  isOpen,
  onClose,
  onSave
}: DocumentDetailModalProps) {
  const [formData, setFormData] = useState<{
    categoryId: string;
    securityLevelId: string;
    notes: string;
  }>({
    categoryId: document?.classification?.category.id.toString() || '',
    securityLevelId: document?.classification?.security_level.id.toString() || '',
    notes: ''
  });

  const [loading, setLoading] = useState(false);

  if (!isOpen || !document) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Call API to update document classification
      const response = await fetch('/api/classification/classify-document', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: document.id,
          category_id: parseInt(formData.categoryId),
          security_level_id: parseInt(formData.securityLevelId),
          classified_by: 1, // Current user ID
          notes: formData.notes
        })
      });

      if (response.ok) {
        // Update local document data
        const updatedDocument = {
          ...document,
          classification: {
            category: {
              id: parseInt(formData.categoryId),
              name: categories.find(c => c.id === parseInt(formData.categoryId))?.name || '',
              confidence: 1.0
            },
            security_level: {
              id: parseInt(formData.securityLevelId),
              name: securityLevels.find(s => s.id === parseInt(formData.securityLevelId))?.name || '',
              level_number: securityLevels.find(s => s.id === parseInt(formData.securityLevelId))?.level_number || 1
            },
            access_granted: true
          }
        };
        
        onSave(updatedDocument);
        onClose();
      } else {
        throw new Error('Classification failed');
      }
    } catch (error) {
      console.error('Failed to classify document:', error);
      alert('Belge sınıflandırması başarısız oldu');
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Belge Detayları</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Document Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dosya Adı
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded">
                {document.filename}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dosya Türü
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded">
                {document.file_type?.toUpperCase()}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dosya Boyutu
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded">
                {formatFileSize(document.file_size)}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Yüklenme Tarihi
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded">
                {new Date(document.upload_date).toLocaleString('tr-TR')}
              </p>
            </div>
          </div>

          {/* Current Classification */}
          {document.classification && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-900 mb-2">Mevcut Sınıflandırma</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-blue-700">Kategori:</span>
                  <span className="ml-2 font-medium">{document.classification.category.name}</span>
                </div>
                <div>
                  <span className="text-blue-700">Güvenlik Seviyesi:</span>
                  <span className="ml-2 font-medium">{document.classification.security_level.name}</span>
                </div>
              </div>
            </div>
          )}

          {/* Classification Form */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Yeni Sınıflandırma</h3>
            
            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
                Kategori *
              </label>
              <select
                id="category"
                required
                value={formData.categoryId}
                onChange={(e) => setFormData({ ...formData, categoryId: e.target.value })}
                className="input-field"
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
              <label htmlFor="securityLevel" className="block text-sm font-medium text-gray-700 mb-2">
                Güvenlik Seviyesi *
              </label>
              <select
                id="securityLevel"
                required
                value={formData.securityLevelId}
                onChange={(e) => setFormData({ ...formData, securityLevelId: e.target.value })}
                className="input-field"
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
              <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
                Notlar
              </label>
              <textarea
                id="notes"
                rows={3}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Sınıflandırma hakkında notlar..."
                className="input-field"
              />
            </div>
          </div>

          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-yellow-800">
                <p className="font-medium mb-1">Dikkat!</p>
                <p>
                  Bu işlem belgenin erişim yetkilerini değiştirecektir. 
                  Sadece yetki sahibi kullanıcılar bu belgeye erişebilecektir.
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
              disabled={loading}
            >
              İptal
            </button>
            <button
              type="submit"
              className="btn-primary flex items-center gap-2"
              disabled={loading || !formData.categoryId || !formData.securityLevelId}
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Sınıflandır
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}