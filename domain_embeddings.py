"""
Domain-Specific Embedding System for Defense Industry
Savunma Sanayi için özelleştirilmiş embedding sistemi
"""

import numpy as np
import pickle
import logging
from typing import List, Dict, Any, Optional, Tuple
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

from defense_vocabulary import DefenseVocabulary

logger = logging.getLogger(__name__)

class DefenseEmbeddingSystem:
    """Savunma sanayi için optimize edilmiş embedding sistemi"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.base_model = None
        self.vocab = DefenseVocabulary()
        self.term_embeddings = {}
        self.boost_factors = {}
        self.turkish_optimization = True
        
    def initialize(self):
        """Embedding sistemini başlat"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.base_model = SentenceTransformer(self.model_name)
            
            # Savunma sanayi terimlerinin embeddinglerini önceden hesapla
            self._precompute_defense_embeddings()
            self._setup_boost_factors()
            
            logger.info("Defense embedding system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing embedding system: {e}")
            return False
    
    def _precompute_defense_embeddings(self):
        """Savunma sanayi terimlerinin embeddinglerini önceden hesapla"""
        logger.info("Precomputing defense term embeddings...")
        
        all_terms = []
        
        # Tüm savunma terimlerini topla
        for category, terms in self.vocab.defense_terms.items():
            all_terms.extend(terms)
        
        # Eş anlamlıları ekle
        for term, synonyms in self.vocab.synonyms.items():
            all_terms.append(term)
            all_terms.extend(synonyms)
        
        # Kısaltmaları ekle
        for abbr, full_form in self.vocab.abbreviations.items():
            all_terms.append(abbr)
            all_terms.append(full_form)
        
        # Teknik terimleri ekle
        all_terms.extend(list(self.vocab.technical_terms.keys()))
        
        # Tekrarlananları kaldır
        unique_terms = list(set(all_terms))
        
        # Embeddingleri hesapla
        try:
            embeddings = self.base_model.encode(unique_terms)
            
            # Term embeddinglerini sakla
            for term, embedding in zip(unique_terms, embeddings):
                self.term_embeddings[term.lower()] = embedding
            
            logger.info(f"Precomputed embeddings for {len(unique_terms)} defense terms")
            
        except Exception as e:
            logger.error(f"Error precomputing embeddings: {e}")
    
    def _setup_boost_factors(self):
        """Domain-specific boost faktörlerini ayarla"""
        self.boost_factors = {
            "security": 2.0,      # Güvenlik terimleri
            "threat": 1.8,        # Tehdit terimleri  
            "technical": 1.5,     # Teknik terimler
            "weapon": 1.3,        # Silah sistemleri
            "defense": 1.2,       # Genel savunma
            "default": 1.0        # Normal terimler
        }
    
    def encode_query(self, query: str, enhance_domain_terms: bool = True) -> np.ndarray:
        """Query'yi domain-aware encoding ile vektorize et"""
        try:
            if not self.base_model:
                raise Exception("Embedding model not initialized")
            
            original_query = query
            
            if enhance_domain_terms:
                # Domain-specific query enhancement
                query = self.vocab.expand_query(query)
                logger.debug(f"Enhanced query: {original_query} -> {query}")
            
            # Base embedding
            base_embedding = self.base_model.encode([query])[0]
            
            if enhance_domain_terms:
                # Domain-specific enhancement
                enhanced_embedding = self._enhance_embedding_with_domain_knowledge(
                    base_embedding, original_query
                )
                return enhanced_embedding
            
            return base_embedding
            
        except Exception as e:
            logger.error(f"Error encoding query: {e}")
            return np.zeros(384)  # Default dimension for MiniLM
    
    def _enhance_embedding_with_domain_knowledge(self, base_embedding: np.ndarray, query: str) -> np.ndarray:
        """Embedding'i domain knowledge ile güçlendir"""
        try:
            enhanced_embedding = base_embedding.copy()
            query_lower = query.lower()
            
            # Query'deki savunma terimlerini bul
            detected_terms = []
            for term in self.term_embeddings.keys():
                if term in query_lower:
                    detected_terms.append(term)
            
            if detected_terms:
                # Domain term embeddinglerini weighted olarak ekle
                domain_boost = np.zeros_like(base_embedding)
                total_weight = 0
                
                for term in detected_terms:
                    term_embedding = self.term_embeddings[term]
                    weight = self.vocab.get_term_importance_weight(term)
                    
                    domain_boost += term_embedding * weight
                    total_weight += weight
                
                if total_weight > 0:
                    domain_boost = domain_boost / total_weight
                    
                    # Base embedding ile domain boost'u birleştir
                    alpha = 0.7  # Base embedding ağırlığı
                    beta = 0.3   # Domain boost ağırlığı
                    
                    enhanced_embedding = alpha * base_embedding + beta * domain_boost
                    
                    # Normalize et
                    enhanced_embedding = enhanced_embedding / np.linalg.norm(enhanced_embedding)
            
            return enhanced_embedding
            
        except Exception as e:
            logger.error(f"Error enhancing embedding: {e}")
            return base_embedding
    
    def encode_documents(self, documents: List[str]) -> np.ndarray:
        """Dokümanları encode et"""
        try:
            if not self.base_model:
                raise Exception("Embedding model not initialized")
            
            # Batch encoding for efficiency
            embeddings = self.base_model.encode(documents, show_progress_bar=True)
            return embeddings
            
        except Exception as e:
            logger.error(f"Error encoding documents: {e}")
            return np.array([])
    
    def compute_similarity(self, query_embedding: np.ndarray, doc_embeddings: np.ndarray) -> np.ndarray:
        """Query ve doküman embeddingler arasında similarity hesapla"""
        try:
            # Cosine similarity hesapla
            similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
            
            return similarities
            
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return np.array([])
    
    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Query'nin complexity ve domain relevance analizi"""
        analysis = {
            "original_query": query,
            "expanded_query": self.vocab.expand_query(query),
            "defense_terms": [],
            "technical_terms": [],
            "abbreviations": [],
            "complexity_score": 0,
            "domain_relevance": 0
        }
        
        query_lower = query.lower()
        
        # Savunma terimlerini tespit et
        for term in self.term_embeddings.keys():
            if term in query_lower:
                analysis["defense_terms"].append(term)
        
        # Teknik terimleri tespit et
        for tech_term in self.vocab.technical_terms.keys():
            if tech_term.lower() in query_lower:
                analysis["technical_terms"].append(tech_term)
        
        # Kısaltmaları tespit et
        for abbr in self.vocab.abbreviations.keys():
            if abbr.lower() in query_lower:
                analysis["abbreviations"].append(abbr)
        
        # Complexity score hesapla
        word_count = len(query.split())
        term_count = len(analysis["defense_terms"]) + len(analysis["technical_terms"])
        analysis["complexity_score"] = word_count + (term_count * 2)
        
        # Domain relevance hesapla
        total_terms = len(analysis["defense_terms"]) + len(analysis["technical_terms"]) + len(analysis["abbreviations"])
        analysis["domain_relevance"] = min(total_terms / max(word_count, 1), 1.0)
        
        return analysis
    
    def save_system_state(self, filepath: str):
        """Sistem durumunu kaydet"""
        state = {
            "model_name": self.model_name,
            "term_embeddings": self.term_embeddings,
            "boost_factors": self.boost_factors,
            "turkish_optimization": self.turkish_optimization
        }
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(state, f)
            logger.info(f"Embedding system state saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving system state: {e}")
    
    def load_system_state(self, filepath: str):
        """Sistem durumunu yükle"""
        try:
            with open(filepath, 'rb') as f:
                state = pickle.load(f)
            
            self.model_name = state.get("model_name", "all-MiniLM-L6-v2")
            self.term_embeddings = state.get("term_embeddings", {})
            self.boost_factors = state.get("boost_factors", {})
            self.turkish_optimization = state.get("turkish_optimization", True)
            
            logger.info(f"Embedding system state loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading system state: {e}")

class TurkishDefenseEmbedding(DefenseEmbeddingSystem):
    """Türkçe savunma sanayi için optimize edilmiş embedding sistemi"""
    
    def __init__(self):
        # Türkçe destekli model kullan
        super().__init__(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.turkish_patterns = self._setup_turkish_patterns()
    
    def _setup_turkish_patterns(self) -> Dict[str, str]:
        """Türkçe dil özelliklerine göre pattern'lar"""
        return {
            "security_variants": r"güvenlik|emniyet|koruma|savunma",
            "threat_variants": r"tehdit|tehlike|risk|zarar",
            "system_variants": r"sistem|systemi|sistemine|sistemin",
            "procedure_variants": r"prosedür|işlem|yöntem|protokol",
            "technical_variants": r"teknik|teknoloji|teknolojik|mühendislik"
        }
    
    def _preprocess_turkish_text(self, text: str) -> str:
        """Türkçe text preprocessing"""
        # Türkçe karakterleri normalize et
        turkish_chars = {
            'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
            'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C'
        }
        
        normalized = text
        for tr_char, en_char in turkish_chars.items():
            normalized = normalized.replace(tr_char, en_char)
        
        return normalized.lower().strip()

def test_defense_embedding_system():
    """Defense embedding sistemini test et"""
    print("=== Defense Embedding System Test ===")
    
    # Sistem başlat
    embedding_system = TurkishDefenseEmbedding()
    if not embedding_system.initialize():
        print("Failed to initialize embedding system")
        return
    
    # Test queries
    test_queries = [
        "İHA güvenlik prosedürü",
        "radar sistem analizi", 
        "TSK tehdit değerlendirmesi",
        "F-16 bakım raporu",
        "normal döküman arama"
    ]
    
    print("Query Analysis:")
    for query in test_queries:
        analysis = embedding_system.analyze_query_complexity(query)
        print(f"\nQuery: {query}")
        print(f"Expanded: {analysis['expanded_query']}")
        print(f"Defense Terms: {analysis['defense_terms']}")
        print(f"Complexity Score: {analysis['complexity_score']}")
        print(f"Domain Relevance: {analysis['domain_relevance']:.2f}")
    
    # Embedding test
    print("\n=== Embedding Test ===")
    query = "İHA güvenlik prosedürü"
    
    # Normal encoding
    normal_embedding = embedding_system.base_model.encode([query])[0]
    
    # Enhanced encoding
    enhanced_embedding = embedding_system.encode_query(query, enhance_domain_terms=True)
    
    print(f"Query: {query}")
    print(f"Normal embedding shape: {normal_embedding.shape}")
    print(f"Enhanced embedding shape: {enhanced_embedding.shape}")
    print(f"Similarity between normal and enhanced: {cosine_similarity([normal_embedding], [enhanced_embedding])[0][0]:.3f}")

if __name__ == "__main__":
    test_defense_embedding_system()