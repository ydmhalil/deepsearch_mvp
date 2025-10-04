import { useState, useEffect } from 'react';
import { 
  X, 
  Save, 
  Trash2, 
  AlertTriangle, 
  BarChart3,
  Briefcase, 
  Cog, 
  Shield, 
  DollarSign, 
  Scale, 
  Users, 
  Lightbulb, 
  Factory, 
  Folder, 
  File, 
  Bookmark, 
  Tag 
} from 'lucide-react';
import type { ProfessionalCategory } from '../types';

interface EditCategoryModalProps {
  category: ProfessionalCategory | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (category: ProfessionalCategory) => void;
  onDelete: (categoryId: number) => void;
}

const CATEGORY_COLORS = [
  '#667eea', '#06b6d4', '#ef4444', '#10b981', 
  '#f59e0b', '#8b5cf6', '#ec4899', '#84cc16',
  '#6b7280', '#1f2937', '#7c3aed', '#dc2626'
];

const CATEGORY_ICONS = [
  { name: 'briefcase', component: Briefcase },
  { name: 'cog', component: Cog },
  { name: 'shield', component: Shield },
  { name: 'dollar-sign', component: DollarSign },
  { name: 'scale', component: Scale },
  { name: 'users', component: Users },
  { name: 'lightbulb', component: Lightbulb },
  { name: 'factory', component: Factory },
  { name: 'folder', component: Folder },
  { name: 'file', component: File },
  { name: 'bookmark', component: Bookmark },
  { name: 'tag', component: Tag }
];

export default function EditCategoryModal({
  category,
  isOpen,
  onClose,
  onSave,
  onDelete
}: EditCategoryModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    color_code: CATEGORY_COLORS[0],
    icon: CATEGORY_ICONS[0].name,
    is_active: true
  });

  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<{
    document_count: number;
    recent_usage: number;
    last_used: string | null;
  } | null>(null);

  useEffect(() => {
    if (category && isOpen) {
      setFormData({
        name: category.name,
        description: category.description || '',
        color_code: category.color_code,
        icon: category.icon,
        is_active: category.is_active
      });
      
      // Load category statistics
      loadCategoryStats(category.id);
    }
  }, [category, isOpen]);

  const loadCategoryStats = async (categoryId: number) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/classification/categories/${categoryId}/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Failed to load category stats:', error);
    }
  };

  if (!isOpen || !category) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/classification/categories/${category.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const updatedCategory: ProfessionalCategory = {
          ...category,
          ...formData
        };
        
        onSave(updatedCategory);
        onClose();
      } else {
        throw new Error('Category update failed');
      }
    } catch (error) {
      console.error('Failed to update category:', error);
      alert('Kategori güncelleme başarısız oldu');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`"${category.name}" kategorisini silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.`)) {
      return;
    }

    if (stats && stats.document_count > 0) {
      if (!confirm(`Bu kategoride ${stats.document_count} belge bulunuyor. Kategori silindiğinde bu belgeler sınıflandırılmamış olarak işaretlenecek. Devam etmek istediğinizden emin misiniz?`)) {
        return;
      }
    }

    setLoading(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/classification/categories/${category.id}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        onDelete(category.id);
        onClose();
      } else {
        throw new Error('Category deletion failed');
      }
    } catch (error) {
      console.error('Failed to delete category:', error);
      alert('Kategori silme başarısız oldu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Kategori Düzenle</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={loading}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Category Statistics */}
        {stats && (
          <div className="p-6 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="w-5 h-5 text-[var(--primary-color)]" />
              <h3 className="font-medium text-gray-900">Kategori İstatistikleri</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Belge Sayısı:</span>
                <div className="font-medium text-lg">{stats.document_count}</div>
              </div>
              <div>
                <span className="text-gray-500">Son Kullanım:</span>
                <div className="font-medium">
                  {stats.last_used 
                    ? new Date(stats.last_used).toLocaleDateString('tr-TR')
                    : 'Hiç kullanılmamış'
                  }
                </div>
              </div>
              <div>
                <span className="text-gray-500">Aktif Durum:</span>
                <div className={`font-medium ${category.is_active ? 'text-green-600' : 'text-red-600'}`}>
                  {category.is_active ? 'Aktif' : 'Pasif'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Kategori Adı *
            </label>
            <input
              type="text"
              id="name"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input-field"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Açıklama
            </label>
            <textarea
              id="description"
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Renk
            </label>
            <div className="grid grid-cols-6 gap-2">
              {CATEGORY_COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setFormData({ ...formData, color_code: color })}
                  className={`w-8 h-8 rounded-full border-2 transition-all ${
                    formData.color_code === color 
                      ? 'border-gray-900 scale-110' 
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              İkon
            </label>
            <div className="grid grid-cols-6 gap-2">
              {CATEGORY_ICONS.map((iconData) => {
                const IconComponent = iconData.component;
                return (
                  <button
                    key={iconData.name}
                    type="button"
                    onClick={() => setFormData({ ...formData, icon: iconData.name })}
                    className={`w-10 h-10 rounded-lg border-2 flex items-center justify-center transition-all ${
                      formData.icon === iconData.name
                        ? 'border-[var(--primary-color)] bg-[var(--primary-light)]'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <IconComponent className="w-4 h-4" />
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded border-gray-300 text-[var(--primary-color)] focus:ring-[var(--primary-color)]"
              />
              <span className="text-sm text-gray-700">Kategori aktif</span>
            </label>
            <p className="text-xs text-gray-500 mt-1">
              Pasif kategoriler yeni belge sınıflandırmasında kullanılamaz
            </p>
          </div>

          {/* Preview */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Önizleme</h4>
            <div className="flex items-center gap-3">
              <div 
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: formData.color_code }}
              />
              <div>
                <div className="font-medium text-gray-900">
                  {formData.name || 'Kategori Adı'}
                </div>
                {formData.description && (
                  <div className="text-sm text-gray-500">{formData.description}</div>
                )}
              </div>
              <div className={`ml-auto px-2 py-1 rounded text-xs ${
                formData.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {formData.is_active ? 'Aktif' : 'Pasif'}
              </div>
            </div>
          </div>

          {/* Warning for documents */}
          {stats && stats.document_count > 0 && !formData.is_active && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-800">
                  <p className="font-medium mb-1">Dikkat!</p>
                  <p>
                    Bu kategoride {stats.document_count} belge bulunuyor. 
                    Kategoriyi pasif hale getirdiğinizde, mevcut belgeler etkilenmeyecek 
                    ancak yeni belgeler bu kategoriye atanmayacaktır.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700 text-white font-medium px-4 py-2.5 rounded-lg transition-colors duration-200 flex items-center gap-2"
              disabled={loading}
            >
              <Trash2 className="w-4 h-4" />
              Kategoriyi Sil
            </button>

            <div className="flex items-center gap-3">
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
                disabled={loading || !formData.name.trim()}
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Kaydet
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}