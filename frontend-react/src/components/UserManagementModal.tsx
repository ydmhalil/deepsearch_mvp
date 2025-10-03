import { useState, useEffect } from 'react';
import { 
  X, 
  Save, 
  User, 
  Shield, 
  Plus,
  Trash2
} from 'lucide-react';
import type { ProfessionalCategory, SecurityLevel } from '../types';

interface UserPermission {
  id?: number;
  category_id?: number;
  security_level_id?: number;
  permission_type: 'read' | 'write' | 'admin';
  expires_at?: string;
  notes?: string;
}

interface User {
  id?: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'manager' | 'user';
  is_active: boolean;
  created_at?: string;
  permissions?: UserPermission[];
}

interface UserManagementModalProps {
  user: User | null;
  categories: ProfessionalCategory[];
  securityLevels: SecurityLevel[];
  isOpen: boolean;
  onClose: () => void;
  onSave: (user: User) => void;
  isCreate?: boolean;
}

const USER_ROLES = [
  { value: 'admin', label: 'Admin', description: 'Tam sistem erişimi' },
  { value: 'manager', label: 'Yönetici', description: 'Departman yönetimi' },
  { value: 'user', label: 'Kullanıcı', description: 'Temel erişim' }
];

const PERMISSION_TYPES = [
  { value: 'read', label: 'Okuma', color: 'bg-blue-100 text-blue-800' },
  { value: 'write', label: 'Yazma', color: 'bg-green-100 text-green-800' },
  { value: 'admin', label: 'Yönetici', color: 'bg-purple-100 text-purple-800' }
];

export default function UserManagementModal({
  user,
  categories,
  securityLevels,
  isOpen,
  onClose,
  onSave,
  isCreate = false
}: UserManagementModalProps) {
  const [formData, setFormData] = useState<User>({
    username: '',
    email: '',
    full_name: '',
    role: 'user',
    is_active: true,
    permissions: []
  });

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'basic' | 'permissions'>('basic');

  useEffect(() => {
    if (user && isOpen) {
      setFormData({
        ...user,
        permissions: user.permissions || []
      });
      loadUserPermissions(user.id!);
    } else if (isCreate && isOpen) {
      setFormData({
        username: '',
        email: '',
        full_name: '',
        role: 'user',
        is_active: true,
        permissions: []
      });
    }
  }, [user, isOpen, isCreate]);

  const loadUserPermissions = async (userId: number) => {
    try {
      const response = await fetch(`/api/classification/user-permissions/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setFormData(prev => ({
          ...prev,
          permissions: [
            ...data.permissions.categories.map((cat: any) => ({
              category_id: cat.category_id,
              permission_type: cat.permission_type,
              expires_at: cat.expires_at
            })),
            ...data.permissions.security_levels.map((sec: any) => ({
              security_level_id: sec.security_level_id,
              permission_type: sec.permission_type,
              expires_at: sec.expires_at
            }))
          ]
        }));
      }
    } catch (error) {
      console.error('Failed to load user permissions:', error);
    }
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isCreate && password !== confirmPassword) {
      alert('Parolalar eşleşmiyor');
      return;
    }

    if (isCreate && password.length < 6) {
      alert('Parola en az 6 karakter olmalıdır');
      return;
    }

    setLoading(true);

    try {
      const endpoint = isCreate ? '/api/users' : `/api/users/${user?.id}`;
      const method = isCreate ? 'POST' : 'PUT';
      
      const requestBody: any = {
        ...formData,
        permissions: formData.permissions
      };

      if (isCreate) {
        requestBody.password = password;
      }

      const response = await fetch(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const result = await response.json();
        onSave(isCreate ? { ...formData, id: result.user_id } : formData);
        onClose();
        
        // Reset form
        setFormData({
          username: '',
          email: '',
          full_name: '',
          role: 'user',
          is_active: true,
          permissions: []
        });
        setPassword('');
        setConfirmPassword('');
      } else {
        const error = await response.json();
        throw new Error(error.message || 'İşlem başarısız');
      }
    } catch (error) {
      console.error('Failed to save user:', error);
      alert(error instanceof Error ? error.message : 'Kullanıcı kaydetme başarısız oldu');
    } finally {
      setLoading(false);
    }
  };

  const addPermission = (type: 'category' | 'security_level', id: number) => {
    const newPermission: UserPermission = {
      [type === 'category' ? 'category_id' : 'security_level_id']: id,
      permission_type: 'read'
    };
    
    setFormData(prev => ({
      ...prev,
      permissions: [...(prev.permissions || []), newPermission]
    }));
  };

  const updatePermission = (index: number, updates: Partial<UserPermission>) => {
    setFormData(prev => ({
      ...prev,
      permissions: prev.permissions?.map((perm, i) => 
        i === index ? { ...perm, ...updates } : perm
      ) || []
    }));
  };

  const removePermission = (index: number) => {
    setFormData(prev => ({
      ...prev,
      permissions: prev.permissions?.filter((_, i) => i !== index) || []
    }));
  };

  const getPermissionLabel = (permission: UserPermission) => {
    if (permission.category_id) {
      const category = categories.find(c => c.id === permission.category_id);
      return `Kategori: ${category?.name || 'Bilinmeyen'}`;
    } else if (permission.security_level_id) {
      const level = securityLevels.find(s => s.id === permission.security_level_id);
      return `Güvenlik: ${level?.name || 'Bilinmeyen'}`;
    }
    return 'Bilinmeyen';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {isCreate ? 'Yeni Kullanıcı Ekle' : 'Kullanıcı Düzenle'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={loading}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              onClick={() => setActiveTab('basic')}
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === 'basic'
                  ? 'border-[var(--primary-color)] text-[var(--primary-color)]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <User className="w-4 h-4 inline mr-2" />
              Temel Bilgiler
            </button>
            <button
              onClick={() => setActiveTab('permissions')}
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === 'permissions'
                  ? 'border-[var(--primary-color)] text-[var(--primary-color)]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Shield className="w-4 h-4 inline mr-2" />
              Yetkiler ({formData.permissions?.length || 0})
            </button>
          </nav>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Basic Info Tab */}
          {activeTab === 'basic' && (
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                    Kullanıcı Adı *
                  </label>
                  <input
                    type="text"
                    id="username"
                    required
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="input-field"
                    disabled={!isCreate} // Username cannot be changed
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    E-posta *
                  </label>
                  <input
                    type="email"
                    id="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="input-field"
                  />
                </div>

                <div className="md:col-span-2">
                  <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-2">
                    Ad Soyad *
                  </label>
                  <input
                    type="text"
                    id="full_name"
                    required
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="input-field"
                  />
                </div>

                <div>
                  <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-2">
                    Rol *
                  </label>
                  <select
                    id="role"
                    required
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value as 'admin' | 'manager' | 'user' })}
                    className="input-field"
                  >
                    {USER_ROLES.map(role => (
                      <option key={role.value} value={role.value}>
                        {role.label} - {role.description}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="rounded border-gray-300 text-[var(--primary-color)] focus:ring-[var(--primary-color)]"
                    />
                    <span className="text-sm text-gray-700">Kullanıcı aktif</span>
                  </label>
                </div>
              </div>

              {isCreate && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                  <div>
                    <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                      Parola *
                    </label>
                    <input
                      type="password"
                      id="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="input-field"
                      minLength={6}
                    />
                  </div>

                  <div>
                    <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                      Parola Tekrar *
                    </label>
                    <input
                      type="password"
                      id="confirmPassword"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="input-field"
                      minLength={6}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Permissions Tab */}
          {activeTab === 'permissions' && (
            <div className="p-6 space-y-6">
              {/* Add New Permission */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-3">Yeni Yetki Ekle</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Kategori Yetkisi
                    </label>
                    <div className="space-y-2">
                      {categories.map(category => (
                        <button
                          key={category.id}
                          type="button"
                          onClick={() => addPermission('category', category.id)}
                          className="w-full text-left px-3 py-2 border border-gray-300 rounded hover:bg-gray-50 flex items-center justify-between"
                          disabled={formData.permissions?.some(p => p.category_id === category.id)}
                        >
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: category.color_code }}
                            />
                            <span className="text-sm">{category.name}</span>
                          </div>
                          <Plus className="w-4 h-4 text-gray-400" />
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Güvenlik Seviyesi Yetkisi
                    </label>
                    <div className="space-y-2">
                      {securityLevels.map(level => (
                        <button
                          key={level.id}
                          type="button"
                          onClick={() => addPermission('security_level', level.id)}
                          className="w-full text-left px-3 py-2 border border-gray-300 rounded hover:bg-gray-50 flex items-center justify-between"
                          disabled={formData.permissions?.some(p => p.security_level_id === level.id)}
                        >
                          <div className="flex items-center gap-2">
                            <Shield className="w-4 h-4 text-gray-500" />
                            <span className="text-sm">{level.name} (Seviye {level.level_number})</span>
                          </div>
                          <Plus className="w-4 h-4 text-gray-400" />
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Current Permissions */}
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Mevcut Yetkiler</h3>
                {formData.permissions && formData.permissions.length > 0 ? (
                  <div className="space-y-3">
                    {formData.permissions.map((permission, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <span className="font-medium text-gray-900">
                            {getPermissionLabel(permission)}
                          </span>
                          <button
                            type="button"
                            onClick={() => removePermission(index)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              Yetki Türü
                            </label>
                            <select
                              value={permission.permission_type}
                              onChange={(e) => updatePermission(index, { 
                                permission_type: e.target.value as 'read' | 'write' | 'admin' 
                              })}
                              className="input-field text-sm"
                            >
                              {PERMISSION_TYPES.map(type => (
                                <option key={type.value} value={type.value}>
                                  {type.label}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              Son Geçerlilik (Opsiyonel)
                            </label>
                            <input
                              type="date"
                              value={permission.expires_at || ''}
                              onChange={(e) => updatePermission(index, { expires_at: e.target.value })}
                              className="input-field text-sm"
                            />
                          </div>

                          <div className="flex items-end">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              PERMISSION_TYPES.find(t => t.value === permission.permission_type)?.color
                            }`}>
                              {PERMISSION_TYPES.find(t => t.value === permission.permission_type)?.label}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Shield className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p>Henüz yetki atanmamış</p>
                    <p className="text-sm">Yukarıdaki bölümden yetki ekleyebilirsiniz</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
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
              disabled={loading || !formData.username.trim() || !formData.email.trim() || !formData.full_name.trim()}
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {isCreate ? 'Kullanıcı Oluştur' : 'Değişiklikleri Kaydet'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}