import { useState, useEffect } from 'react';
import { 
  Users, 
  FileText, 
  Shield, 
  Settings, 
  BarChart3, 
  Plus,
  Search,
  Eye,
  Edit,
  Trash2,
  Download,
  Upload,
  AlertCircle,
  CheckCircle,
  Clock,
  UserCheck,
  CheckSquare,
  Square,
  MoreHorizontal,
  XCircle
} from 'lucide-react';
import { api } from '../utils/api';
import type { Document, ProfessionalCategory, SecurityLevel } from '../types';
import DocumentDetailModal from '../components/DocumentDetailModal';
import CreateCategoryModal from '../components/CreateCategoryModal';
import DocumentPreviewModal from '../components/DocumentPreviewModal';
import BulkActionsModal from '../components/BulkActionsModal';
import EditCategoryModal from '../components/EditCategoryModal';
import UserManagementModal from '../components/UserManagementModal';
import SecuritySettingsModal from '../components/SecuritySettingsModal';
import ConfirmationModal from '../components/ConfirmationModal';
import { useToast } from '../components/ToastProvider';

interface AdminStats {
  total_documents: number;
  classified_documents: number;
  pending_classification: number;
  total_users: number;
  active_sessions: number;
  recent_uploads: number;
}

interface TabItem {
  id: string;
  name: string;
  icon: React.ComponentType<any>;
  count?: number;
}

export default function Admin() {
  const [activeTab, setActiveTab] = useState('overview');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [categories, setCategories] = useState<ProfessionalCategory[]>([]);
  const [securityLevels, setSecurityLevels] = useState<SecurityLevel[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedSecurityLevel, setSelectedSecurityLevel] = useState<string>('');
  
  // Modal states
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [showCreateCategoryModal, setShowCreateCategoryModal] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [showEditCategoryModal, setShowEditCategoryModal] = useState(false);
  const [showUserManagementModal, setShowUserManagementModal] = useState(false);
  const [showSecuritySettingsModal, setShowSecuritySettingsModal] = useState(false);
  const [selectedCategoryForEdit, setSelectedCategoryForEdit] = useState<ProfessionalCategory | null>(null);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [isCreateUser, setIsCreateUser] = useState(false);
  
  // Confirmation modal states
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [confirmationData, setConfirmationData] = useState<{
    title: string;
    message: string;
    type: 'success' | 'danger' | 'warning' | 'info';
    action: () => void;
  } | null>(null);
  
  // Toast hook
  const { showSuccess, showError, showWarning } = useToast();
  
  // Selection states
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
  const [selectAll, setSelectAll] = useState(false);

  const tabs: TabItem[] = [
    { id: 'overview', name: 'Genel Bakış', icon: BarChart3 },
    { id: 'documents', name: 'Belge Yönetimi', icon: FileText, count: documents.length },
    { id: 'categories', name: 'Kategori Yönetimi', icon: Settings, count: categories.length },
    { id: 'users', name: 'Kullanıcı Yönetimi', icon: Users, count: users.length },
    { id: 'security', name: 'Güvenlik Ayarları', icon: Shield },
  ];

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      setLoading(true);
      console.log('🔄 Loading admin data...');
      
      // Load all admin data in parallel with error handling
      const [
        documentsRes,
        categoriesRes,
        securityLevelsRes,
        usersRes,
        analyticsRes
      ] = await Promise.all([
        api.getDocuments().catch(err => { console.warn('Documents fetch failed:', err); return []; }),
        fetch(`${import.meta.env.VITE_API_BASE_URL}/api/classification/categories`).then(res => res.json()).catch(err => { console.warn('Categories fetch failed:', err); return { categories: [] }; }),
        fetch(`${import.meta.env.VITE_API_BASE_URL}/api/classification/security-levels`).then(res => res.json()).catch(err => { console.warn('Security levels fetch failed:', err); return { security_levels: [] }; }),
        fetch(`${import.meta.env.VITE_API_BASE_URL}/api/admin/users`).then(res => res.json()).catch(err => { console.warn('Users fetch failed:', err); return { users: [] }; }),
        fetch(`${import.meta.env.VITE_API_BASE_URL}/analytics`).then(res => res.json()).catch(err => { console.warn('Analytics fetch failed:', err); return {}; })
      ]);

      console.log('📊 Raw API responses:', { documentsRes, categoriesRes, securityLevelsRes, usersRes, analyticsRes });

      // Ensure documentsRes is an array
      const safeDocuments = Array.isArray(documentsRes) ? documentsRes : [];
      
      setDocuments(safeDocuments);
      setCategories(categoriesRes.categories || []);
      setSecurityLevels(securityLevelsRes.security_levels || []);
      setUsers(usersRes.users || []);
      
      console.log('✅ Data set:', { 
        documents: safeDocuments?.length || 0, 
        categories: categoriesRes?.categories?.length || 0, 
        securityLevels: securityLevelsRes?.security_levels?.length || 0,
        users: usersRes?.users?.length || 0
      });
      
      // Create admin stats from analytics data
      if (analyticsRes) {
        setStats({
          total_documents: analyticsRes.total_documents || 0,
          classified_documents: analyticsRes.classified_documents || 0,
          pending_classification: analyticsRes.pending_classification || 0,
          total_users: analyticsRes.total_users || 0,
          active_sessions: analyticsRes.active_sessions || 0,
          recent_uploads: analyticsRes.recent_uploads || 0
        });
      }
      
    } catch (error) {
      console.error('Failed to load admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentClick = (doc: Document) => {
    setSelectedDocument(doc);
    setShowDocumentModal(true);
  };

  const handleDocumentSave = (updatedDoc: Document) => {
    setDocuments(docs => docs.map(doc => 
      doc.id === updatedDoc.id ? updatedDoc : doc
    ));
  };

  const handleCategorySave = (newCategory: ProfessionalCategory) => {
    setCategories(cats => [...cats, newCategory]);
  };

  const handleDeleteCategory = async (categoryId: number) => {
    if (!confirm('Bu kategoriyi silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.')) {
      return;
    }

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/classification/categories/${categoryId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setCategories(cats => cats.filter(cat => cat.id !== categoryId));
        alert('Kategori başarıyla silindi');
      } else {
        throw new Error('Category deletion failed');
      }
    } catch (error) {
      console.error('Failed to delete category:', error);
      alert('Kategori silme işlemi başarısız oldu');
    }
  };

  const handleDocumentPreview = (doc: Document) => {
    setSelectedDocument(doc);
    setShowPreviewModal(true);
  };

  const handleSelectDocument = (docId: string) => {
    setSelectedDocuments(prev => {
      const newSet = new Set(prev);
      if (newSet.has(docId)) {
        newSet.delete(docId);
      } else {
        newSet.add(docId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedDocuments(new Set());
      setSelectAll(false);
    } else {
      setSelectedDocuments(new Set(filteredDocuments.map(doc => doc.id)));
      setSelectAll(true);
    }
  };

  const handleBulkActionComplete = (action: string, count: number) => {
    // Refresh data after bulk action
    loadAdminData();
    setSelectedDocuments(new Set());
    setSelectAll(false);
    setShowBulkModal(false);
    
    // Show success message
    alert(`${action === 'classify' ? 'Sınıflandırma' : action === 'delete' ? 'Silme' : 'İndirme'} işlemi tamamlandı. ${count} belge işlendi.`);
  };

  const getSelectedDocumentObjects = () => {
    return filteredDocuments.filter(doc => selectedDocuments.has(doc.id));
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !selectedCategory || doc.classification?.category.id.toString() === selectedCategory;
    const matchesSecurity = !selectedSecurityLevel || doc.classification?.security_level.id.toString() === selectedSecurityLevel;
    
    return matchesSearch && matchesCategory && matchesSecurity;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'indexed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing': return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // User management functions
  const handleApproveUser = async (userId: number) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/admin/users/${userId}/approve`, {
        method: 'POST',
      });

      if (response.ok) {
        // Reload users data
        loadAdminData();
        showSuccess('Başarılı!', 'Kullanıcı rolü başarıyla onaylandı');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'User approval failed');
      }
    } catch (error) {
      console.error('Failed to approve user:', error);
      showError('Hata!', 'Kullanıcı onaylama işlemi başarısız oldu');
    }
  };

  const handleRejectUser = async (userId: number) => {
    try {
      const response = await fetch(`http://localhost:5001/api/admin/users/${userId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: 'inactive' }),
      });

      if (response.ok) {
        // Reload users data
        loadAdminData();
        showWarning('Reddedildi', 'Kullanıcı talebi reddedildi');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'User rejection failed');
      }
    } catch (error) {
      console.error('Failed to reject user:', error);
      showError('Hata!', 'Kullanıcı reddetme işlemi başarısız oldu');
    }
  };

  const handleToggleUserStatus = async (userId: number, currentStatus: string) => {
    try {
      const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
      const response = await fetch(`http://localhost:5001/api/admin/users/${userId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        // Reload users data
        loadAdminData();
        showSuccess(
          'Durum Güncellendi', 
          `Kullanıcı durumu ${newStatus === 'active' ? 'aktif' : 'pasif'} olarak güncellendi`
        );
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'User status update failed');
      }
    } catch (error) {
      console.error('Failed to update user status:', error);
      showError('Hata!', 'Kullanıcı durumu güncelleme işlemi başarısız oldu');
    }
  };

  const confirmApproveUser = (userId: number, username: string, requestedRole: string) => {
    setConfirmationData({
      title: 'Kullanıcı Onaylama',
      message: `${username} kullanıcısını ${requestedRole} rolü ile onaylamak istediğinizden emin misiniz?`,
      type: 'success',
      action: () => handleApproveUser(userId)
    });
    setShowConfirmation(true);
  };

  const confirmRejectUser = (userId: number, username: string) => {
    setConfirmationData({
      title: 'Kullanıcı Reddetme',
      message: `${username} kullanıcısının rol talebini reddetmek istediğinizden emin misiniz?`,
      type: 'warning',
      action: () => handleRejectUser(userId)
    });
    setShowConfirmation(true);
  };

  const confirmToggleUserStatus = (userId: number, username: string, currentStatus: string) => {
    const newStatus = currentStatus === 'active' ? 'pasif' : 'aktif';
    setConfirmationData({
      title: 'Kullanıcı Durumu Değiştirme',
      message: `${username} kullanıcısının durumunu ${newStatus} yapmak istediğinizden emin misiniz?`,
      type: currentStatus === 'active' ? 'warning' : 'info',
      action: () => handleToggleUserStatus(userId, currentStatus)
    });
    setShowConfirmation(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--primary-color)] mx-auto mb-4"></div>
          <p className="text-gray-600">Admin paneli yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Paneli</h1>
        <p className="text-gray-600">Sistem yönetimi ve belge kontrolü</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                  activeTab === tab.id
                    ? 'border-[var(--primary-color)] text-[var(--primary-color)]'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-5 h-5" />
                {tab.name}
                {tab.count !== undefined && (
                  <span className="bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {stats && [
              {
                title: 'Toplam Belge',
                value: stats.total_documents,
                icon: FileText,
                color: 'bg-blue-500'
              },
              {
                title: 'Sınıflandırılmış',
                value: stats.classified_documents,
                icon: CheckCircle,
                color: 'bg-green-500'
              },
              {
                title: 'Bekleyen Sınıflandırma',
                value: stats.pending_classification,
                icon: Clock,
                color: 'bg-yellow-500'
              },
              {
                title: 'Toplam Kullanıcı',
                value: stats.total_users,
                icon: Users,
                color: 'bg-purple-500'
              },
              {
                title: 'Aktif Oturum',
                value: stats.active_sessions,
                icon: UserCheck,
                color: 'bg-indigo-500'
              },
              {
                title: 'Son Yüklemeler',
                value: stats.recent_uploads,
                icon: Upload,
                color: 'bg-pink-500'
              }
            ].map((stat, index) => {
              const Icon = stat.icon;
              return (
                <div key={index} className="card p-6">
                  <div className="flex items-center">
                    <div className={`${stat.color} p-3 rounded-lg`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                      <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Recent Activity */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Son Aktiviteler</h3>
            <div className="space-y-3">
              {[
                { action: 'Yeni belge yüklendi', file: 'finansal_rapor.pdf', time: '5 dakika önce', type: 'upload' },
                { action: 'Belge sınıflandırıldı', file: 'guvenlik_protokolu.docx', time: '15 dakika önce', type: 'classify' },
                { action: 'Kullanıcı yetkisi güncellendi', file: 'user@company.com', time: '1 saat önce', type: 'permission' },
                { action: 'Arama gerçekleştirildi', file: '"güvenlik protokolleri"', time: '2 saat önce', type: 'search' }
              ].map((activity, index) => (
                <div key={index} className="flex items-center justify-between py-2">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      activity.type === 'upload' ? 'bg-green-500' :
                      activity.type === 'classify' ? 'bg-blue-500' :
                      activity.type === 'permission' ? 'bg-purple-500' :
                      'bg-gray-500'
                    }`} />
                    <div>
                      <p className="text-sm text-gray-900">{activity.action}</p>
                      <p className="text-xs text-gray-500">{activity.file}</p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400">{activity.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'documents' && (
        <div className="space-y-6">
          {/* Filters and Search */}
          <div className="card p-6">
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    placeholder="Belge ara..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="input-field pl-10"
                  />
                </div>
              </div>
              
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="input-field w-full lg:w-48"
              >
                <option value="">Tüm Kategoriler</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id.toString()}>{cat.name}</option>
                ))}
              </select>
              
              <select
                value={selectedSecurityLevel}
                onChange={(e) => setSelectedSecurityLevel(e.target.value)}
                className="input-field w-full lg:w-48"
              >
                <option value="">Tüm Güvenlik Seviyeleri</option>
                {securityLevels.map(level => (
                  <option key={level.id} value={level.id.toString()}>
                    {level.name} (Seviye {level.level_number})
                  </option>
                ))}
              </select>
              
              <button className="btn-primary flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Yeni Belge
              </button>
              
              {selectedDocuments.size > 0 && (
                <button 
                  onClick={() => setShowBulkModal(true)}
                  className="bg-orange-600 hover:bg-orange-700 text-white font-medium px-4 py-2.5 rounded-lg transition-colors duration-200 flex items-center gap-2"
                >
                  <MoreHorizontal className="w-4 h-4" />
                  Toplu İşlem ({selectedDocuments.size})
                </button>
              )}
            </div>
          </div>

          {/* Documents Table */}
          <div className="card overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                Belgeler ({filteredDocuments.length})
              </h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={handleSelectAll}
                        className="flex items-center gap-2"
                      >
                        {selectAll ? (
                          <CheckSquare className="w-4 h-4 text-[var(--primary-color)]" />
                        ) : (
                          <Square className="w-4 h-4 text-gray-400" />
                        )}
                        <span>Seç</span>
                      </button>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Belge
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Kategori
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Güvenlik Seviyesi
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Durum
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Boyut
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tarih
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İşlemler
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredDocuments.map((doc) => (
                    <tr key={doc.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleSelectDocument(doc.id)}
                          className="flex items-center"
                        >
                          {selectedDocuments.has(doc.id) ? (
                            <CheckSquare className="w-4 h-4 text-[var(--primary-color)]" />
                          ) : (
                            <Square className="w-4 h-4 text-gray-400 hover:text-gray-600" />
                          )}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <FileText className="w-5 h-5 text-gray-400 mr-3" />
                          <div>
                            <div className="text-sm font-medium text-gray-900">{doc.filename}</div>
                            <div className="text-sm text-gray-500">{doc.file_type?.toUpperCase()}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {doc.classification ? (
                          <span 
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                            style={{ 
                              backgroundColor: categories.find(c => c.id === doc.classification?.category.id)?.color_code + '20',
                              color: categories.find(c => c.id === doc.classification?.category.id)?.color_code
                            }}
                          >
                            {doc.classification.category.name}
                          </span>
                        ) : (
                          <span className="text-sm text-gray-400">Sınıflandırılmamış</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {doc.classification ? (
                          <span 
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                            style={{ 
                              backgroundColor: securityLevels.find(s => s.id === doc.classification?.security_level.id)?.color_code + '20',
                              color: securityLevels.find(s => s.id === doc.classification?.security_level.id)?.color_code
                            }}
                          >
                            {doc.classification.security_level.name}
                          </span>
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(doc.status)}
                          <span className="text-sm text-gray-600 capitalize">{doc.status}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatFileSize(doc.file_size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {new Date(doc.upload_date).toLocaleDateString('tr-TR')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end gap-2">
                          <button 
                            onClick={() => handleDocumentPreview(doc)}
                            className="text-[var(--primary-color)] hover:text-[var(--primary-dark)]"
                            title="Belge önizleme"
                          >
                            <FileText className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => handleDocumentClick(doc)}
                            className="text-[var(--primary-color)] hover:text-[var(--primary-dark)]"
                            title="Belge detayları"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button className="text-[var(--primary-color)] hover:text-[var(--primary-dark)]">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button className="text-[var(--primary-color)] hover:text-[var(--primary-dark)]">
                            <Download className="w-4 h-4" />
                          </button>
                          <button className="text-red-600 hover:text-red-900">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {filteredDocuments.length === 0 && (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Belge bulunamadı</h3>
                <p className="text-gray-500">Filtreleri değiştirin veya yeni belge yükleyin.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'categories' && (
        <div className="space-y-6">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Kategori Yönetimi</h3>
              <button 
                onClick={() => setShowCreateCategoryModal(true)}
                className="btn-primary flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Yeni Kategori
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map((category) => (
                <div key={category.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: category.color_code }}
                      />
                      <h4 className="font-medium text-gray-900">{category.name}</h4>
                    </div>
                    <div className="flex items-center gap-1">
                      <button 
                        onClick={() => {
                          setSelectedCategoryForEdit(category);
                          setShowEditCategoryModal(true);
                        }}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => handleDeleteCategory(category.id)}
                        className="text-gray-400 hover:text-red-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{category.description}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Oluşturulma: {new Date(category.created_at).toLocaleDateString('tr-TR')}</span>
                    <span className={`px-2 py-1 rounded ${category.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {category.is_active ? 'Aktif' : 'Pasif'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'users' && (
        <div className="space-y-6">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Kullanıcı Yönetimi</h3>
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Kullanıcı ara..."
                    className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <button 
                  onClick={() => {
                    setSelectedUser(null);
                    setIsCreateUser(true);
                    setShowUserManagementModal(true);
                  }}
                  className="btn-primary flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Yeni Kullanıcı
                </button>
              </div>
            </div>
            
            {/* Pending Users Section */}
            {users.filter(user => user.status === 'pending').length > 0 && (
              <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <Clock className="w-5 h-5 text-yellow-600" />
                  <h4 className="font-medium text-yellow-900">Onay Bekleyen Kullanıcılar</h4>
                  <span className="px-2 py-1 bg-yellow-200 text-yellow-800 rounded-full text-xs">
                    {users.filter(user => user.status === 'pending').length}
                  </span>
                </div>
                <div className="space-y-2">
                  {users.filter(user => user.status === 'pending').map(user => (
                    <div key={user.id} className="flex items-center justify-between p-3 bg-white rounded border">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                          <Users className="w-4 h-4 text-yellow-600" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{user.username}</div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                          {user.requested_role} rolü talep ediyor
                        </span>
                        <button
                          onClick={() => confirmApproveUser(user.id, user.username, user.requested_role)}
                          className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm flex items-center gap-1"
                        >
                          <CheckCircle className="w-3 h-3" />
                          Onayla
                        </button>
                        <button
                          onClick={() => confirmRejectUser(user.id, user.username)}
                          className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm flex items-center gap-1"
                        >
                          <XCircle className="w-3 h-3" />
                          Reddet
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Users Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Kullanıcı
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Durum
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Kayıt Tarihi
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İşlemler
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users
                    .filter(user => 
                      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      user.email.toLowerCase().includes(searchQuery.toLowerCase())
                    )
                    .map(user => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                            <Users className="w-4 h-4 text-blue-600" />
                          </div>
                          <div className="ml-3">
                            <div className="text-sm font-medium text-gray-900">
                              {user.username}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {user.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 rounded-full text-xs ${ 
                          user.role === 'admin' 
                            ? 'bg-red-100 text-red-800'
                            : user.role === 'manager'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {user.role === 'admin' ? 'Admin' : user.role === 'manager' ? 'Yönetici' : 'Kullanıcı'}
                        </span>
                        {user.requested_role && user.requested_role !== user.role && (
                          <div className="text-xs text-gray-500 mt-1">
                            {user.requested_role} talep ediyor
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          user.status === 'active' 
                            ? 'bg-green-100 text-green-800'
                            : user.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.status === 'active' ? 'Aktif' : user.status === 'pending' ? 'Beklemede' : 'Pasif'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(user.created_at).toLocaleDateString('tr-TR')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setIsCreateUser(false);
                              setShowUserManagementModal(true);
                            }}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => confirmToggleUserStatus(user.id, user.username, user.status)}
                            className={`text-sm ${
                              user.status === 'active' 
                                ? 'text-red-600 hover:text-red-900' 
                                : 'text-green-600 hover:text-green-900'
                            }`}
                          >
                            {user.status === 'active' ? 'Pasifleştir' : 'Aktifleştir'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {users.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Henüz kullanıcı bulunmuyor</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'security' && (
        <div className="space-y-6">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Güvenlik Ayarları</h3>
              <button 
                onClick={() => setShowSecuritySettingsModal(true)}
                className="btn-primary flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                Ayarları Düzenle
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Shield className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-blue-900">Kimlik Doğrulama</span>
                </div>
                <p className="text-sm text-blue-700">Parola politikaları ve oturum yönetimi</p>
              </div>
              
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Users className="w-5 h-5 text-green-600" />
                  <span className="font-medium text-green-900">Yetkilendirme</span>
                </div>
                <p className="text-sm text-green-700">Erişim kontrolleri ve izinler</p>
              </div>
              
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <FileText className="w-5 h-5 text-purple-600" />
                  <span className="font-medium text-purple-900">Denetim</span>
                </div>
                <p className="text-sm text-purple-700">Sistem günlükleri ve izleme</p>
              </div>
              
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Eye className="w-5 h-5 text-orange-600" />
                  <span className="font-medium text-orange-900">Gizlilik</span>
                </div>
                <p className="text-sm text-orange-700">Veri koruma ve şifreleme</p>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Modals */}
      <DocumentDetailModal
        document={selectedDocument}
        categories={categories}
        securityLevels={securityLevels}
        isOpen={showDocumentModal}
        onClose={() => setShowDocumentModal(false)}
        onSave={handleDocumentSave}
      />
      
      <CreateCategoryModal
        isOpen={showCreateCategoryModal}
        onClose={() => setShowCreateCategoryModal(false)}
        onSave={handleCategorySave}
      />
      
      <DocumentPreviewModal
        document={selectedDocument}
        isOpen={showPreviewModal}
        onClose={() => setShowPreviewModal(false)}
      />
      
      <BulkActionsModal
        selectedDocuments={getSelectedDocumentObjects()}
        categories={categories}
        securityLevels={securityLevels}
        isOpen={showBulkModal}
        onClose={() => setShowBulkModal(false)}
        onActionComplete={handleBulkActionComplete}
      />
      
      <EditCategoryModal
        category={selectedCategoryForEdit}
        isOpen={showEditCategoryModal}
        onClose={() => {
          setShowEditCategoryModal(false);
          setSelectedCategoryForEdit(null);
        }}
        onSave={(updatedCategory) => {
          setCategories(cats => cats.map(cat => 
            cat.id === updatedCategory.id ? updatedCategory : cat
          ));
          setShowEditCategoryModal(false);
          setSelectedCategoryForEdit(null);
        }}
        onDelete={(categoryId) => {
          setCategories(cats => cats.filter(cat => cat.id !== categoryId));
          setShowEditCategoryModal(false);
          setSelectedCategoryForEdit(null);
        }}
      />
      
      <UserManagementModal
        user={selectedUser}
        categories={categories}
        securityLevels={securityLevels}
        isOpen={showUserManagementModal}
        onClose={() => {
          setShowUserManagementModal(false);
          setSelectedUser(null);
          setIsCreateUser(false);
        }}
        onSave={(_savedUser) => {
          // Handle user save - could update a users list here
          setShowUserManagementModal(false);
          setSelectedUser(null);
          setIsCreateUser(false);
        }}
        isCreate={isCreateUser}
      />
      
      <SecuritySettingsModal
        isOpen={showSecuritySettingsModal}
        onClose={() => setShowSecuritySettingsModal(false)}
      />
      
      {/* Confirmation Modal */}
      {confirmationData && (
        <ConfirmationModal
          isOpen={showConfirmation}
          onClose={() => {
            setShowConfirmation(false);
            setConfirmationData(null);
          }}
          onConfirm={confirmationData.action}
          title={confirmationData.title}
          message={confirmationData.message}
          type={confirmationData.type}
          confirmText={confirmationData.type === 'danger' ? 'Sil' : 'Onayla'}
          cancelText="İptal"
        />
      )}
    </div>
  );
}