import { useState, useEffect } from 'react';
import { 
  X, 
  Save, 
  Shield, 
  Lock, 
  Key, 
  Eye,
  FileText,
  Users,
  Settings,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';

interface SecuritySetting {
  key: string;
  value: string | number | boolean;
  type: 'string' | 'number' | 'boolean' | 'select';
  options?: string[];
  category: 'authentication' | 'authorization' | 'audit' | 'privacy';
  title: string;
  description: string;
  sensitive?: boolean;
}

interface AuditLog {
  id: number;
  user_id: number;
  username: string;
  action: string;
  resource_type: string;
  resource_id?: number;
  details: string;
  ip_address: string;
  timestamp: string;
}

interface SecuritySettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SECURITY_CATEGORIES = [
  {
    key: 'authentication',
    title: 'Kimlik Doğrulama',
    icon: Key,
    description: 'Kullanıcı giriş ve parola ayarları'
  },
  {
    key: 'authorization',
    title: 'Yetkilendirme',
    icon: Shield,
    description: 'Erişim kontrolleri ve izinler'
  },
  {
    key: 'audit',
    title: 'Denetim',
    icon: FileText,
    description: 'Sistem günlükleri ve izleme'
  },
  {
    key: 'privacy',
    title: 'Gizlilik',
    icon: Eye,
    description: 'Veri koruma ve gizlilik'
  }
];

const DEFAULT_SETTINGS: SecuritySetting[] = [
  // Authentication
  {
    key: 'min_password_length',
    value: 8,
    type: 'number',
    category: 'authentication',
    title: 'Minimum Parola Uzunluğu',
    description: 'Kullanıcı parolalarının minimum karakter sayısı'
  },
  {
    key: 'password_complexity',
    value: true,
    type: 'boolean',
    category: 'authentication',
    title: 'Karmaşık Parola Zorunluluğu',
    description: 'Parolada büyük/küçük harf, rakam ve özel karakter zorunluluğu'
  },
  {
    key: 'session_timeout',
    value: 480,
    type: 'number',
    category: 'authentication',
    title: 'Oturum Zaman Aşımı (dakika)',
    description: 'Kullanıcı oturumunun otomatik olarak sonlanma süresi'
  },
  {
    key: 'max_login_attempts',
    value: 5,
    type: 'number',
    category: 'authentication',
    title: 'Maksimum Giriş Denemesi',
    description: 'Hesap kilitlenmeden önce izin verilen başarısız giriş sayısı'
  },
  {
    key: 'lockout_duration',
    value: 30,
    type: 'number',
    category: 'authentication',
    title: 'Hesap Kilitlenme Süresi (dakika)',
    description: 'Başarısız girişler sonrası hesabın kilitli kalacağı süre'
  },
  
  // Authorization
  {
    key: 'default_user_role',
    value: 'user',
    type: 'select',
    options: ['user', 'manager', 'admin'],
    category: 'authorization',
    title: 'Varsayılan Kullanıcı Rolü',
    description: 'Yeni kullanıcılar için atanacak varsayılan rol'
  },
  {
    key: 'permission_inheritance',
    value: true,
    type: 'boolean',
    category: 'authorization',
    title: 'İzin Kalıtımı',
    description: 'Üst kategorilerden alt kategorilere izin kalıtımı'
  },
  {
    key: 'guest_access_enabled',
    value: false,
    type: 'boolean',
    category: 'authorization',
    title: 'Misafir Erişimi',
    description: 'Kayıtsız kullanıcıların sisteme erişimine izin ver'
  },
  {
    key: 'admin_approval_required',
    value: true,
    type: 'boolean',
    category: 'authorization',
    title: 'Yönetici Onayı Gerekli',
    description: 'Yeni kullanıcı kayıtları için yönetici onayı zorunluluğu'
  },
  
  // Audit
  {
    key: 'audit_enabled',
    value: true,
    type: 'boolean',
    category: 'audit',
    title: 'Denetim Günlüğü Aktif',
    description: 'Sistem işlemlerinin günlüğe kaydedilmesi'
  },
  {
    key: 'audit_retention_days',
    value: 90,
    type: 'number',
    category: 'audit',
    title: 'Günlük Saklama Süresi (gün)',
    description: 'Denetim günlüklerinin sistemde tutulacağı süre'
  },
  {
    key: 'audit_sensitive_data',
    value: false,
    type: 'boolean',
    category: 'audit',
    title: 'Hassas Veri Günlüğü',
    description: 'Hassas veri erişimlerinin detaylı günlüğe kaydedilmesi'
  },
  
  // Privacy
  {
    key: 'data_encryption',
    value: true,
    type: 'boolean',
    category: 'privacy',
    title: 'Veri Şifreleme',
    description: 'Hassas verilerin şifrelenmiş olarak saklanması'
  },
  {
    key: 'anonymize_logs',
    value: false,
    type: 'boolean',
    category: 'privacy',
    title: 'Günlükleri Anonimleştir',
    description: 'Günlüklerde kişisel verilerin anonimleştirilmesi'
  },
  {
    key: 'data_retention_days',
    value: 365,
    type: 'number',
    category: 'privacy',
    title: 'Veri Saklama Süresi (gün)',
    description: 'Kullanıcı verilerinin sistemde tutulacağı maksimum süre'
  }
];

export default function SecuritySettingsModal({ isOpen, onClose }: SecuritySettingsModalProps) {
  const [settings, setSettings] = useState<SecuritySetting[]>(DEFAULT_SETTINGS);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [activeCategory, setActiveCategory] = useState<'authentication' | 'authorization' | 'audit' | 'privacy'>('authentication');
  const [activeTab, setActiveTab] = useState<'settings' | 'audit'>('settings');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSecuritySettings();
      if (activeTab === 'audit') {
        loadAuditLogs();
      }
    }
  }, [isOpen, activeTab]);

  const loadSecuritySettings = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/security/settings');
      if (response.ok) {
        const data = await response.json();
        // Merge with default settings
        const mergedSettings = DEFAULT_SETTINGS.map(defaultSetting => {
          const serverSetting = data.settings.find((s: any) => s.key === defaultSetting.key);
          return serverSetting ? { ...defaultSetting, value: serverSetting.value } : defaultSetting;
        });
        setSettings(mergedSettings);
      }
    } catch (error) {
      console.error('Failed to load security settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAuditLogs = async () => {
    try {
      const response = await fetch('/api/security/audit-logs?limit=50');
      if (response.ok) {
        const data = await response.json();
        setAuditLogs(data.logs || []);
      }
    } catch (error) {
      console.error('Failed to load audit logs:', error);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      const settingsToSave = settings.map(setting => ({
        key: setting.key,
        value: setting.value,
        category: setting.category
      }));

      const response = await fetch('/api/security/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: settingsToSave })
      });

      if (response.ok) {
        // Show success message
        alert('Güvenlik ayarları başarıyla kaydedildi');
      } else {
        throw new Error('Ayarlar kaydedilemedi');
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Ayarlar kaydedilirken bir hata oluştu');
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (key: string, value: string | number | boolean) => {
    setSettings(prev => prev.map(setting => 
      setting.key === key ? { ...setting, value } : setting
    ));
  };

  const renderSettingInput = (setting: SecuritySetting) => {
    const commonProps = {
      id: setting.key,
      disabled: saving
    };

    switch (setting.type) {
      case 'boolean':
        return (
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={setting.value as boolean}
              onChange={(e) => updateSetting(setting.key, e.target.checked)}
              className="rounded border-gray-300 text-[var(--primary-color)] focus:ring-[var(--primary-color)]"
              {...commonProps}
            />
            <span className="text-sm">Aktif</span>
          </label>
        );
      
      case 'number':
        return (
          <input
            type="number"
            value={setting.value as number}
            onChange={(e) => updateSetting(setting.key, parseInt(e.target.value) || 0)}
            className="input-field w-32"
            min="0"
            {...commonProps}
          />
        );
      
      case 'select':
        return (
          <select
            value={setting.value as string}
            onChange={(e) => updateSetting(setting.key, e.target.value)}
            className="input-field w-40"
            {...commonProps}
          >
            {setting.options?.map(option => (
              <option key={option} value={option}>
                {option === 'user' ? 'Kullanıcı' : 
                 option === 'manager' ? 'Yönetici' : 
                 option === 'admin' ? 'Admin' : option}
              </option>
            ))}
          </select>
        );
      
      default:
        return (
          <input
            type={setting.sensitive ? 'password' : 'text'}
            value={setting.value as string}
            onChange={(e) => updateSetting(setting.key, e.target.value)}
            className="input-field w-64"
            {...commonProps}
          />
        );
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('tr-TR');
  };

  const getActionIcon = (action: string) => {
    if (action.includes('login')) return <Key className="w-4 h-4 text-blue-500" />;
    if (action.includes('create')) return <Users className="w-4 h-4 text-green-500" />;
    if (action.includes('delete')) return <X className="w-4 h-4 text-red-500" />;
    if (action.includes('update')) return <Settings className="w-4 h-4 text-orange-500" />;
    return <Shield className="w-4 h-4 text-gray-500" />;
  };

  if (!isOpen) return null;

  const currentCategorySettings = settings.filter(setting => setting.category === activeCategory);
  const currentCategoryInfo = SECURITY_CATEGORIES.find(cat => cat.key === activeCategory)!;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Shield className="w-6 h-6 text-[var(--primary-color)]" />
            Güvenlik Ayarları
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={saving}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              onClick={() => setActiveTab('settings')}
              className={`py-3 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'settings'
                  ? 'border-[var(--primary-color)] text-[var(--primary-color)]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Settings className="w-4 h-4 inline mr-2" />
              Ayarlar
            </button>
            <button
              onClick={() => setActiveTab('audit')}
              className={`py-3 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'audit'
                  ? 'border-[var(--primary-color)] text-[var(--primary-color)]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <FileText className="w-4 h-4 inline mr-2" />
              Denetim Günlükleri ({auditLogs.length})
            </button>
          </nav>
        </div>

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="flex h-[600px]">
            {/* Category Sidebar */}
            <div className="w-64 border-r border-gray-200 bg-gray-50">
              <div className="p-4">
                <h3 className="font-medium text-gray-900 mb-3">Kategoriler</h3>
                <div className="space-y-1">
                  {SECURITY_CATEGORIES.map(category => {
                    const Icon = category.icon;
                    const settingsCount = settings.filter(s => s.category === category.key).length;
                    
                    return (
                      <button
                        key={category.key}
                        onClick={() => setActiveCategory(category.key as any)}
                        className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                          activeCategory === category.key
                            ? 'bg-[var(--primary-color)] text-white'
                            : 'hover:bg-gray-100 text-gray-700'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Icon className="w-4 h-4" />
                          <div>
                            <div className="font-medium text-sm">{category.title}</div>
                            <div className={`text-xs ${
                              activeCategory === category.key ? 'text-white/80' : 'text-gray-500'
                            }`}>
                              {settingsCount} ayar
                            </div>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Settings Content */}
            <div className="flex-1 p-6">
              {loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <RefreshCw className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-3" />
                    <p className="text-gray-500">Ayarlar yükleniyor...</p>
                  </div>
                </div>
              ) : (
                <>
                  {/* Category Header */}
                  <div className="mb-6">
                    <div className="flex items-center gap-3 mb-2">
                      <currentCategoryInfo.icon className="w-6 h-6 text-[var(--primary-color)]" />
                      <h3 className="text-lg font-semibold text-gray-900">
                        {currentCategoryInfo.title}
                      </h3>
                    </div>
                    <p className="text-gray-600">{currentCategoryInfo.description}</p>
                  </div>

                  {/* Settings List */}
                  <div className="space-y-6">
                    {currentCategorySettings.map(setting => (
                      <div key={setting.key} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <label htmlFor={setting.key} className="block font-medium text-gray-900 mb-1">
                              {setting.title}
                              {setting.sensitive && (
                                <Lock className="w-4 h-4 inline ml-2 text-orange-500" />
                              )}
                            </label>
                            <p className="text-sm text-gray-600">{setting.description}</p>
                          </div>
                          <div className="flex-shrink-0">
                            {renderSettingInput(setting)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Audit Tab */}
        {activeTab === 'audit' && (
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Denetim Günlükleri</h3>
                <p className="text-gray-600">Sistem işlemlerinin detaylı geçmişi</p>
              </div>
              <button
                onClick={loadAuditLogs}
                className="btn-secondary flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Yenile
              </button>
            </div>

            {auditLogs.length > 0 ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Zaman
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Kullanıcı
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          İşlem
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Kaynak
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          IP Adresi
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Detaylar
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {auditLogs.map(log => (
                        <tr key={log.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                            {formatTimestamp(log.timestamp)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                            {log.username}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              {getActionIcon(log.action)}
                              <span className="text-sm text-gray-900">{log.action}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                            {log.resource_type}
                            {log.resource_id && ` #${log.resource_id}`}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                            {log.ip_address}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">
                            {log.details}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p>Henüz denetim günlüğü bulunmuyor</p>
              </div>
            )}
          </div>
        )}

        {/* Actions - Only for settings tab */}
        {activeTab === 'settings' && (
          <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <AlertTriangle className="w-4 h-4 text-orange-500" />
              Güvenlik ayarlarını değiştirmek sistem genelinde etkili olacaktır
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary"
                disabled={saving}
              >
                İptal
              </button>
              <button
                onClick={saveSettings}
                className="btn-primary flex items-center gap-2"
                disabled={saving}
              >
                {saving ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Ayarları Kaydet
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}