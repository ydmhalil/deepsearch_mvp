import { Link, useLocation } from 'react-router-dom';
import { Search, Upload, MessageSquare, BarChart3, Shield, Settings, LogOut, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Header() {
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();

  const navItems = [
    { path: '/', label: 'Ana Sayfa', icon: Shield },
    { path: '/upload', label: 'Yükle', icon: Upload },
    { path: '/search', label: 'Ara', icon: Search },
    { path: '/chat', label: 'RAG Chat', icon: MessageSquare },
    { path: '/analytics', label: 'Analytics', icon: BarChart3 },
    { path: '/admin', label: 'Admin', icon: Settings, requiresAuth: true, requiredRole: 'manager' },
  ];

  const isActive = (path: string) => location.pathname === path;

  const filteredNavItems = navItems.filter(item => {
    if (item.requiresAuth && !isAuthenticated) return false;
    if (item.requiredRole && user) {
      const roleHierarchy = { admin: 3, manager: 2, user: 1 };
      const userLevel = roleHierarchy[user.role as keyof typeof roleHierarchy] || 0;
      const requiredLevel = roleHierarchy[item.requiredRole as keyof typeof roleHierarchy] || 0;
      return userLevel >= requiredLevel;
    }
    return true;
  });

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <Shield className="w-8 h-8 text-[var(--primary-color)]" />
            <span className="text-xl font-bold text-gray-900">DeepSearch</span>
          </Link>

          <nav className="hidden md:flex space-x-1">
            {filteredNavItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-200 ${
                  isActive(path)
                    ? 'bg-[var(--primary-light)] text-[var(--primary-dark)]'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{label}</span>
              </Link>
            ))}
          </nav>

          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <div className="flex items-center space-x-3 text-sm text-gray-600">
                  <User className="w-4 h-4" />
                  <span>{user?.full_name || user?.username}</span>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {user?.role === 'admin' ? 'Admin' : user?.role === 'manager' ? 'Yönetici' : 'Kullanıcı'}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="font-medium">Çıkış</span>
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="btn-primary flex items-center space-x-2"
              >
                <User className="w-4 h-4" />
                <span>Giriş Yap</span>
              </Link>
            )}
          </div>
        </div>

        <nav className="md:hidden pb-4 flex space-x-1 overflow-x-auto">
          {filteredNavItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg whitespace-nowrap transition-colors duration-200 ${
                isActive(path)
                  ? 'bg-[var(--primary-light)] text-[var(--primary-dark)]'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{label}</span>
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
