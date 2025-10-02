export interface Document {
  id: string;
  filename: string;
  file_path: string;
  file_size: number;
  file_type: string;
  upload_date: string;
  status: 'pending' | 'processing' | 'indexed' | 'error';
  page_count?: number;
}

export interface SearchResult {
  file_path: string;
  file_name: string;
  chunk_text: string;
  score: number;
  metadata?: {
    page?: number;
    section?: string;
  };
}

export interface SearchResponse {
  success: boolean;
  results: SearchResult[];
  query: string;
  search_type: string;
  total_results: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: SearchResult[];
  follow_up_questions?: string[];
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  created_at: Date;
  updated_at: Date;
}

export interface UploadProgress {
  filename: string;
  progress: number;
  status: 'uploading' | 'processing' | 'complete' | 'error';
  error?: string;
}

export interface SystemStats {
  total_documents: number;
  indexed_files: number;
  processing_queue: number;
  recent_searches: number;
  system_health: 'good' | 'warning' | 'error';
}

export type SearchType = 'semantic' | 'keyword' | 'comprehensive';
