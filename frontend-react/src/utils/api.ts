import type { SearchResponse, SearchType, Document, SystemStats } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Network error' }));
    throw new APIError(response.status, error.message || 'Request failed');
  }
  return response.json();
}

export const api = {
  search: async (
    query: string,
    searchType: SearchType = 'semantic',
    topK: number = 10,
    filters?: Record<string, unknown>
  ): Promise<SearchResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, search_type: searchType, top_k: topK, filters }),
    });
    return handleResponse<SearchResponse>(response);
  },

  uploadFile: async (file: File, onProgress?: (progress: number) => void): Promise<{ success: boolean; file_id: string; filename: string }> => {
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = (e.loaded / e.total) * 100;
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new APIError(xhr.status, 'Upload failed'));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new APIError(0, 'Network error'));
      });

      xhr.open('POST', `${API_BASE_URL}/upload_file`);
      xhr.send(formData);
    });
  },

  ragQuery: async (
    question: string,
    sessionId?: string,
    type: 'conversational' | 'comprehensive' = 'conversational'
  ): Promise<{
    success: boolean;
    answer: string;
    sources: Array<{ file_path: string; chunk_text: string; score: number }>;
    follow_up_questions?: string[];
  }> => {
    const response = await fetch(`${API_BASE_URL}/rag/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, session_id: sessionId, type }),
    });
    return handleResponse(response);
  },

  getDocumentPreview: async (path: string): Promise<{ content: string; metadata: Record<string, unknown> }> => {
    const response = await fetch(
      `${API_BASE_URL}/api/document/content?path=${encodeURIComponent(path)}`
    );
    return handleResponse(response);
  },

  getDocuments: async (): Promise<Document[]> => {
    const response = await fetch(`${API_BASE_URL}/api/documents`);
    return handleResponse(response);
  },

  deleteDocument: async (documentId: string): Promise<{ success: boolean }> => {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },

  indexDocument: async (documentId: string): Promise<{ success: boolean }> => {
    const response = await fetch(`${API_BASE_URL}/index_file`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId }),
    });
    return handleResponse(response);
  },

  getAnalytics: async (): Promise<SystemStats> => {
    const response = await fetch(`${API_BASE_URL}/analytics`);
    return handleResponse(response);
  },
};

export const validateFile = (file: File): { valid: boolean; error?: string } => {
  const allowedTypes = ['.pdf', '.docx', '.xlsx', '.pptx', '.txt'];
  const maxSize = 50 * 1024 * 1024;

  const extension = '.' + file.name.split('.').pop()?.toLowerCase();

  if (!allowedTypes.includes(extension)) {
    return { valid: false, error: 'Invalid file type. Allowed: PDF, DOCX, XLSX, PPTX, TXT' };
  }

  if (file.size > maxSize) {
    return { valid: false, error: 'File size exceeds 50MB limit' };
  }

  return { valid: true };
};
