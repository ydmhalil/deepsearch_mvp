import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Upload, MessageSquare, FileText, Database, TrendingUp, Shield, Zap, Lock } from 'lucide-react';
import { api } from '../utils/api';
import type { SystemStats } from '../types';

export default function Home() {
  const [stats, setStats] = useState<SystemStats>({
    total_documents: 0,
    indexed_files: 0,
    processing_queue: 0,
    recent_searches: 0,
    system_health: 'good',
  });

  useEffect(() => {
    api.getAnalytics().then(setStats).catch(console.error);
  }, []);

  const features = [
    {
      icon: Upload,
      title: 'Doküman Yükleme',
      description: 'PDF, DOCX, XLSX, PPTX ve TXT formatlarında belgelerinizi güvenle yükleyin',
      link: '/upload',
      color: 'bg-blue-500',
    },
    {
      icon: Search,
      title: 'Akıllı Arama',
      description: 'Semantik, keyword ve kapsamlı arama seçenekleriyle güçlü AI destekli arama',
      link: '/search',
      color: 'bg-green-500',
    },
    {
      icon: MessageSquare,
      title: 'RAG Chat',
      description: 'Belgelerinizle doğal dilde konuşun ve detaylı yanıtlar alın',
      link: '/chat',
      color: 'bg-purple-500',
    },
    {
      icon: TrendingUp,
      title: 'Analytics',
      description: 'Sistem performansını ve kullanım istatistiklerini takip edin',
      link: '/analytics',
      color: 'bg-orange-500',
    },
  ];

  const advantages = [
    {
      icon: Shield,
      title: 'Offline İlk',
      description: 'Tüm verileriniz yerel olarak işlenir, dış API çağrısı yok',
    },
    {
      icon: Zap,
      title: 'Hızlı & Güvenilir',
      description: 'FAISS vektör veritabanı ile saniyeler içinde sonuç',
    },
    {
      icon: Lock,
      title: 'Güvenli',
      description: 'Savunma sanayi için geliştirilmiş, GDPR uyumlu',
    },
  ];

  return (
    <div className="min-h-screen">
      <section className="gradient-bg text-white py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-bold mb-6">
              DeepSearch MVP
            </h1>
            <p className="text-xl md:text-2xl text-blue-100 mb-8">
              Savunma Sanayi için Offline Belge Arama ve RAG Sistemi
            </p>
          </div>

          <div className="max-w-3xl mx-auto">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center space-x-3 mb-4">
                <Search className="w-6 h-6 text-white" />
                <input
                  type="text"
                  placeholder="Belgelerinizde arama yapın..."
                  className="flex-1 bg-white/20 border border-white/30 rounded-lg px-4 py-3 text-white placeholder-blue-200 focus:outline-none focus:ring-2 focus:ring-white/50"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.currentTarget.value) {
                      window.location.href = `/search?q=${encodeURIComponent(e.currentTarget.value)}`;
                    }
                  }}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="text-sm text-blue-100">Popüler aramalar:</span>
                {['güvenlik prosedürleri', 'radar sistemleri', 'roket teknolojisi'].map((term) => (
                  <Link
                    key={term}
                    to={`/search?q=${encodeURIComponent(term)}`}
                    className="text-sm bg-white/20 hover:bg-white/30 px-3 py-1 rounded-full transition-colors"
                  >
                    {term}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-16">
            <div className="card p-6 text-center">
              <FileText className="w-12 h-12 text-[var(--primary-color)] mx-auto mb-3" />
              <div className="text-3xl font-bold text-gray-900 mb-1">{stats.total_documents}</div>
              <div className="text-sm text-gray-600">Toplam Doküman</div>
            </div>
            <div className="card p-6 text-center">
              <Database className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <div className="text-3xl font-bold text-gray-900 mb-1">{stats.indexed_files}</div>
              <div className="text-sm text-gray-600">İndeksli Dosya</div>
            </div>
            <div className="card p-6 text-center">
              <TrendingUp className="w-12 h-12 text-orange-500 mx-auto mb-3" />
              <div className="text-3xl font-bold text-gray-900 mb-1">{stats.recent_searches}</div>
              <div className="text-sm text-gray-600">Son Aramalar</div>
            </div>
            <div className="card p-6 text-center">
              <Shield className="w-12 h-12 text-blue-500 mx-auto mb-3" />
              <div className="text-3xl font-bold text-gray-900 mb-1">
                {stats.system_health === 'good' ? '100%' : '75%'}
              </div>
              <div className="text-sm text-gray-600">Sistem Sağlığı</div>
            </div>
          </div>

          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Özellikler
            </h2>
            <p className="text-lg text-gray-600">
              Savunma sanayi için özel olarak tasarlanmış güçlü özellikler
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {features.map((feature) => (
              <Link
                key={feature.title}
                to={feature.link}
                className="card p-6 hover:scale-105 transition-transform duration-300"
              >
                <div className={`${feature.color} w-12 h-12 rounded-lg flex items-center justify-center mb-4`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </Link>
            ))}
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-8 md:p-12">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Neden DeepSearch?
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {advantages.map((advantage) => (
                <div key={advantage.title} className="text-center">
                  <div className="bg-white w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 shadow-md">
                    <advantage.icon className="w-8 h-8 text-[var(--primary-color)]" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">{advantage.title}</h3>
                  <p className="text-gray-600">{advantage.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="text-center mt-12">
            <Link to="/upload" className="btn-primary inline-flex items-center space-x-2">
              <Upload className="w-5 h-5" />
              <span>Hemen Başla</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
