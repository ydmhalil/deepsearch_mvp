import { useState } from 'react';
import { 
  X, 
  Save, 
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

interface CreateCategoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (category: ProfessionalCategory) => void;
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

export default function CreateCategoryModal({
  isOpen,
  onClose,
  onSave
}: CreateCategoryModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    color_code: CATEGORY_COLORS[0],
    icon: CATEGORY_ICONS[0].name
  });

  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/classification/categories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const result = await response.json();
        const newCategory: ProfessionalCategory = {
          id: result.category_id,
          name: formData.name,
          description: formData.description,
          color_code: formData.color_code,
          icon: formData.icon,
          is_active: true,
          created_at: new Date().toISOString()
        };
        
        onSave(newCategory);
        setFormData({
          name: '',
          description: '',
          color_code: CATEGORY_COLORS[0],
          icon: CATEGORY_ICONS[0].name
        });
        onClose();
      } else {
        throw new Error('Category creation failed');
      }
    } catch (error) {
      console.error('Failed to create category:', error);
      alert('Kategori oluşturma başarısız oldu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Yeni Kategori Oluştur</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
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
              placeholder="Örn: Finansal Belgeler"
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
              placeholder="Kategori açıklaması..."
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
              disabled={loading || !formData.name.trim()}
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Oluştur
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}