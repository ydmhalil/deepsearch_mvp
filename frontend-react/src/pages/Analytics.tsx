import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, FileText, Search, Clock, Activity } from 'lucide-react';
import { api } from '../utils/api';
import type { SystemStats } from '../types';

export default function Analytics() {
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

  const healthColor =
    stats.system_health === 'good'
      ? 'bg-green-500'
      : stats.system_health === 'warning'
      ? 'bg-yellow-500'
      : 'bg-red-500';

  const healthText =
    stats.system_health === 'good'
      ? 'İyi'
      : stats.system_health === 'warning'
      ? 'Uyarı'
      : 'Hata';

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics</h1>
        <p className="text-gray-600">Sistem performansı ve kullanım istatistikleri</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <FileText className="w-8 h-8 text-[var(--primary-color)]" />
            <span className="text-xs font-medium text-gray-500 uppercase">Toplam</span>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {stats.total_documents}
          </div>
          <div className="text-sm text-gray-600">Doküman</div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <BarChart3 className="w-8 h-8 text-green-500" />
            <span className="text-xs font-medium text-gray-500 uppercase">İndeksli</span>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">{stats.indexed_files}</div>
          <div className="text-sm text-gray-600">Dosya</div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <Search className="w-8 h-8 text-blue-500" />
            <span className="text-xs font-medium text-gray-500 uppercase">Son</span>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">{stats.recent_searches}</div>
          <div className="text-sm text-gray-600">Arama</div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <Activity className="w-8 h-8 text-orange-500" />
            <span className="text-xs font-medium text-gray-500 uppercase">Sağlık</span>
          </div>
          <div className="flex items-center gap-2 mb-1">
            <div className={`w-3 h-3 rounded-full ${healthColor}`}></div>
            <div className="text-3xl font-bold text-gray-900">{healthText}</div>
          </div>
          <div className="text-sm text-gray-600">Sistem Durumu</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-6">
            <TrendingUp className="w-6 h-6 text-[var(--primary-color)]" />
            <h2 className="text-xl font-semibold text-gray-900">Kullanım Trendi</h2>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Doküman Yükleme</span>
                <span className="font-medium text-gray-900">
                  {Math.round((stats.total_documents / 100) * 100)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-[var(--primary-color)] h-full rounded-full"
                  style={{ width: `${Math.min((stats.total_documents / 100) * 100, 100)}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">İndeksleme Oranı</span>
                <span className="font-medium text-gray-900">
                  {stats.total_documents > 0
                    ? Math.round((stats.indexed_files / stats.total_documents) * 100)
                    : 0}
                  %
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-full rounded-full"
                  style={{
                    width: `${
                      stats.total_documents > 0
                        ? (stats.indexed_files / stats.total_documents) * 100
                        : 0
                    }%`,
                  }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Arama Aktivitesi</span>
                <span className="font-medium text-gray-900">
                  {Math.round((stats.recent_searches / 50) * 100)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-full rounded-full"
                  style={{ width: `${Math.min((stats.recent_searches / 50) * 100, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3 mb-6">
            <Clock className="w-6 h-6 text-[var(--primary-color)]" />
            <h2 className="text-xl font-semibold text-gray-900">Sistem Bilgileri</h2>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center py-3 border-b border-gray-200">
              <span className="text-gray-600">Vektör Veritabanı</span>
              <span className="font-medium text-gray-900">FAISS</span>
            </div>

            <div className="flex justify-between items-center py-3 border-b border-gray-200">
              <span className="text-gray-600">Embedding Model</span>
              <span className="font-medium text-gray-900">MiniLM-L6-v2</span>
            </div>

            <div className="flex justify-between items-center py-3 border-b border-gray-200">
              <span className="text-gray-600">LLM Model</span>
              <span className="font-medium text-gray-900">Gemma2</span>
            </div>

            <div className="flex justify-between items-center py-3 border-b border-gray-200">
              <span className="text-gray-600">Desteklenen Formatlar</span>
              <span className="font-medium text-gray-900">5</span>
            </div>

            <div className="flex justify-between items-center py-3">
              <span className="text-gray-600">İşlem Kuyruğu</span>
              <span
                className={`font-medium ${
                  stats.processing_queue > 0 ? 'text-orange-500' : 'text-green-500'
                }`}
              >
                {stats.processing_queue}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-3 mb-6">
          <BarChart3 className="w-6 h-6 text-[var(--primary-color)]" />
          <h2 className="text-xl font-semibold text-gray-900">Özellikler</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
            <div className="text-2xl font-bold text-gray-900 mb-1">185</div>
            <div className="text-sm text-gray-600">Savunma Sanayi Terimi</div>
          </div>

          <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
            <div className="text-2xl font-bold text-gray-900 mb-1">3</div>
            <div className="text-sm text-gray-600">Arama Tipi</div>
          </div>

          <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
            <div className="text-2xl font-bold text-gray-900 mb-1">100%</div>
            <div className="text-sm text-gray-600">Offline Çalışma</div>
          </div>
        </div>
      </div>
    </div>
  );
}
