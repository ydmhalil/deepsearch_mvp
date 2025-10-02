import { useState, useCallback } from 'react';
import { Upload as UploadIcon, X, CheckCircle, AlertCircle, FileText, Loader } from 'lucide-react';
import { api, validateFile } from '../utils/api';
import type { UploadProgress } from '../types';

export default function Upload() {
  const [uploadQueue, setUploadQueue] = useState<UploadProgress[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = useCallback(async (files: FileList) => {
    const fileArray = Array.from(files);

    const newUploads: UploadProgress[] = fileArray.map((file) => ({
      filename: file.name,
      progress: 0,
      status: 'uploading',
    }));

    setUploadQueue((prev) => [...prev, ...newUploads]);

    for (let i = 0; i < fileArray.length; i++) {
      const file = fileArray[i];
      const validation = validateFile(file);

      if (!validation.valid) {
        updateUploadStatus(file.name, 0, 'error', validation.error);
        continue;
      }

      try {
        await api.uploadFile(file, (progress) => {
          updateUploadStatus(file.name, progress, 'uploading');
        });

        updateUploadStatus(file.name, 100, 'complete');
      } catch (error) {
        updateUploadStatus(
          file.name,
          0,
          'error',
          error instanceof Error ? error.message : 'Upload failed'
        );
      }
    }
  }, []);

  const updateUploadStatus = (
    filename: string,
    progress: number,
    status: UploadProgress['status'],
    error?: string
  ) => {
    setUploadQueue((prev) =>
      prev.map((item) =>
        item.filename === filename ? { ...item, progress, status, error } : item
      )
    );
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [handleFiles]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const removeUpload = (filename: string) => {
    setUploadQueue((prev) => prev.filter((item) => item.filename !== filename));
  };

  const clearCompleted = () => {
    setUploadQueue((prev) => prev.filter((item) => item.status === 'uploading' || item.status === 'processing'));
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Doküman Yükleme</h1>
        <p className="text-gray-600">
          PDF, DOCX, XLSX, PPTX veya TXT formatlarında belgelerinizi yükleyin
        </p>
      </div>

      <div
        className={`card p-12 mb-8 transition-all duration-300 ${
          isDragging ? 'border-2 border-[var(--primary-color)] bg-[var(--primary-light)]' : ''
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <div className="text-center">
          <div className="mb-6">
            <UploadIcon className="w-16 h-16 mx-auto text-[var(--primary-color)]" />
          </div>
          <h3 className="text-2xl font-semibold text-gray-900 mb-2">
            Dosyaları buraya sürükleyin
          </h3>
          <p className="text-gray-600 mb-6">veya</p>
          <label className="btn-primary cursor-pointer inline-block">
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.xlsx,.pptx,.txt"
              className="hidden"
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
            />
            Dosya Seç
          </label>
          <p className="text-sm text-gray-500 mt-4">
            Maksimum dosya boyutu: 50MB | Desteklenen formatlar: PDF, DOCX, XLSX, PPTX, TXT
          </p>
        </div>
      </div>

      {uploadQueue.length > 0 && (
        <div className="card p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-semibold text-gray-900">
              Yüklenen Dosyalar ({uploadQueue.length})
            </h3>
            <button
              onClick={clearCompleted}
              className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              Tamamlananları Temizle
            </button>
          </div>

          <div className="space-y-4">
            {uploadQueue.map((upload) => (
              <div
                key={upload.filename}
                className="bg-gray-50 rounded-lg p-4 border border-gray-200"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <FileText className="w-5 h-5 text-gray-600 flex-shrink-0" />
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {upload.filename}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    {upload.status === 'uploading' && (
                      <Loader className="w-5 h-5 text-[var(--primary-color)] animate-spin" />
                    )}
                    {upload.status === 'complete' && (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    )}
                    {upload.status === 'error' && (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                    <button
                      onClick={() => removeUpload(upload.filename)}
                      className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {upload.status === 'uploading' && (
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-[var(--primary-color)] h-full transition-all duration-300"
                      style={{ width: `${upload.progress}%` }}
                    />
                  </div>
                )}

                {upload.status === 'complete' && (
                  <p className="text-sm text-green-600">Yükleme tamamlandı</p>
                )}

                {upload.status === 'error' && (
                  <p className="text-sm text-red-600">{upload.error || 'Yükleme hatası'}</p>
                )}

                {upload.status === 'processing' && (
                  <p className="text-sm text-orange-600">İşleniyor...</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6">
          <div className="text-[var(--primary-color)] mb-3">
            <FileText className="w-8 h-8" />
          </div>
          <h4 className="font-semibold text-gray-900 mb-2">Otomatik İndeksleme</h4>
          <p className="text-sm text-gray-600">
            Yüklenen dosyalar otomatik olarak işlenir ve arama için indekslenir
          </p>
        </div>

        <div className="card p-6">
          <div className="text-green-500 mb-3">
            <CheckCircle className="w-8 h-8" />
          </div>
          <h4 className="font-semibold text-gray-900 mb-2">Güvenli Depolama</h4>
          <p className="text-sm text-gray-600">
            Tüm belgeler yerel olarak güvenli şekilde saklanır
          </p>
        </div>

        <div className="card p-6">
          <div className="text-orange-500 mb-3">
            <UploadIcon className="w-8 h-8" />
          </div>
          <h4 className="font-semibold text-gray-900 mb-2">Toplu Yükleme</h4>
          <p className="text-sm text-gray-600">
            Birden fazla dosyayı aynı anda yükleyebilirsiniz
          </p>
        </div>
      </div>
    </div>
  );
}
