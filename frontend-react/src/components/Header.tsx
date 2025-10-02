import { Link, useLocation } from 'react-router-dom';
import { Search, Upload, MessageSquare, BarChart3, Shield } from 'lucide-react';

export default function Header() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Ana Sayfa', icon: Shield },
    { path: '/upload', label: 'Yükle', icon: Upload },
    { path: '/search', label: 'Ara', icon: Search },
    { path: '/chat', label: 'RAG Chat', icon: MessageSquare },
    { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <Shield className="w-8 h-8 text-[var(--primary-color)]" />
            <span className="text-xl font-bold text-gray-900">DeepSearch</span>
          </Link>

          <nav className="hidden md:flex space-x-1">
            {navItems.map(({ path, label, icon: Icon }) => (
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
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Sistem Aktif</span>
            </div>
          </div>
        </div>

        <nav className="md:hidden pb-4 flex space-x-1 overflow-x-auto">
          {navItems.map(({ path, label, icon: Icon }) => (
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
