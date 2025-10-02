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

export interface KeywordMatch {
  sentence: string;
  context: string;
  matched_words: string[];
  match_count: number;
  sentence_index: number;
}

export interface SemanticAnalysis {
  exact_keyword_matches: number;
  total_keywords: number;
  match_ratio: number;
  word_density: number;
  dominant_category: string;
  category_strength: number;
}

export interface SearchHighlights {
  matched_words: string[];
  best_context: string;
}

export interface ProfessionalCategory {
  id: number;
  name: string;
  description?: string;
  color_code: string;
  icon: string;
  is_active: boolean;
  created_at: string;
}

export interface SecurityLevel {
  id: number;
  name: string;
  level_number: number;
  description?: string;
  color_code: string;
  requirements?: string;
  is_active: boolean;
}

export interface DocumentClassification {
  category: {
    id: number;
    name: string;
    confidence: number;
  };
  security_level: {
    id: number;
    name: string;
    level_number: number;
  };
  access_granted: boolean;
}

export interface UserPermissions {
  categories: Array<{
    category_id: number;
    category_name: string;
    permission_type: string;
    color_code: string;
    icon: string;
  }>;
  security_levels: Array<{
    security_level_id: number;
    level_name: string;
    level_number: number;
    permission_type: string;
    color_code: string;
  }>;
  max_security_level: number;
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
  keyword_matches?: KeywordMatch[];
  semantic_analysis?: SemanticAnalysis;
  highlights?: SearchHighlights;
  classification?: DocumentClassification;
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
