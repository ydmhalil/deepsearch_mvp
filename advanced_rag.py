"""
Advanced RAG (Retrieval Augmented Generation) System
Savunma Sanayi için özelleştirilmiş AI-powered document Q&A sistemi
"""

import os
import json
import pickle
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# LangChain imports
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import BaseRetriever

# Domain-specific embedding sistemi
from domain_embeddings import TurkishDefenseEmbedding
from defense_vocabulary import DefenseVocabulary
from langchain.callbacks.manager import CallbackManagerForRetrieverRun

# Local imports
from embed_index import load_index

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RAGConfig:
    """RAG sistem konfigürasyonu"""
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_retrieval_docs: int = 5
    temperature: float = 0.1
    max_tokens: int = 512
    
class DeepSearchRetriever:
    """DeepSearch FAISS index'i için domain-aware özel retriever"""
    
    def __init__(self, index_path: str, meta_path: str, embedding_model: str, use_domain_embedding: bool = True):
        self.index_path = index_path
        self.meta_path = meta_path
        self.use_domain_embedding = use_domain_embedding
        self.index = None
        self.metas = None
        
        # Domain-specific embedding sistemi
        if use_domain_embedding:
            try:
                self.domain_embedding_system = TurkishDefenseEmbedding()
                if self.domain_embedding_system.initialize():
                    logger.info("Using Turkish Defense Domain-Specific Embedding for retrieval")
                else:
                    logger.warning("Domain embedding failed, falling back to base model")
                    self.use_domain_embedding = False
            except Exception as e:
                logger.error(f"Domain embedding initialization failed: {e}")
                self.use_domain_embedding = False
        
        if not self.use_domain_embedding:
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cpu'}
            )
        
        self._load_index()
    
    def _load_index(self):
        """FAISS index ve metadata'yı yükle"""
        try:
            # Mevcut FAISS index'i yükle
            self.index, self.metas = load_index(self.index_path, self.meta_path)
            logger.info(f"FAISS index loaded: {len(self.metas)} documents")
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            raise
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Query'e göre ilgili dokümanları getir (domain-aware)"""
        try:
            # Domain-specific query enhancement
            if self.use_domain_embedding:
                # Query analysis ve enhancement
                query_analysis = self.domain_embedding_system.analyze_query_complexity(query)
                logger.info(f"Query domain relevance: {query_analysis['domain_relevance']:.2f}")
                
                # Enhanced query encoding
                query_embedding = self.domain_embedding_system.encode_query(
                    query, enhance_domain_terms=True
                )
            else:
                # Base embedding
                query_embedding = self.embedding_model.embed_query(query)
            
            # FAISS ile arama yap
            import faiss
            import numpy as np
            
            query_vector = np.array([query_embedding], dtype='float32')
            faiss.normalize_L2(query_vector)
            
            # En benzer dokümanları bul
            scores, indices = self.index.search(query_vector, k=5)
            
            documents = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self.metas):
                    continue
                
                meta = self.metas[idx]
                
                # Dosya içeriğini oku
                try:
                    with open(meta.get('file_path', ''), 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception:
                    content = meta.get('text', '')
                
                # Document objesi oluştur
                doc = Document(
                    page_content=content[:2000],  # İlk 2000 karakter
                    metadata={
                        'source': meta.get('file_path', ''),
                        'score': float(score),
                        'chunk_id': meta.get('chunk_id', ''),
                        'file_type': meta.get('file_type', ''),
                        'timestamp': datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            logger.info(f"Retrieved {len(documents)} documents for query: {query}")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []

class AdvancedRAGSystem:
    """Gelişmiş RAG Sistemi - Savunma Sanayi için optimize edilmiş"""
    
    def __init__(self, config: RAGConfig = None):
        self.config = config or RAGConfig()
        self.retriever = None
        self.qa_chain = None
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Türkçe ve savunma sanayi için optimize edilmiş prompt'lar"""
        
        # Genel Q&A için prompt
        self.qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
Aşağıdaki belge içeriklerini kullanarak soruyu yanıtlayın. Savunma sanayi terminolojisini dikkate alın.

BELGE İÇERİKLERİ:
{context}

SORU: {question}

YANITLAMA TALİMATLARI:
1. Sadece verilen belge içeriklerine dayanarak yanıt verin
2. Teknik terimler için net açıklamalar yapın
3. Güvenlik prosedürlerini vurgulayın
4. Belirsizlik varsa belirtin
5. Kaynak belgeleri referans gösterin

YANIT:
"""
        )
        
        # Özet çıkarma için prompt
        self.summary_prompt = PromptTemplate(
            input_variables=["context"],
            template="""
Aşağıdaki savunma sanayi belgelerinin kapsamlı bir özetini çıkarın:

BELGELER:
{context}

ÖZETİN İÇERMESİ GEREKENLER:
1. Ana konular ve temel bulgular
2. Kritik güvenlik prosedürleri
3. Teknik spesifikasyonlar
4. Risk değerlendirmeleri
5. Öneriler ve eylem planları

ÖZET:
"""
        )
    
    def initialize(self, index_path: str, meta_path: str, use_domain_embedding: bool = True):
        """RAG sistemini başlat"""
        try:
            # Retriever'ı başlat (domain embedding ile)
            self.retriever = DeepSearchRetriever(
                index_path=index_path,
                meta_path=meta_path,
                embedding_model=self.config.embedding_model,
                use_domain_embedding=use_domain_embedding
            )
            
            logger.info("Advanced RAG System initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            return False
    
    def query_documents(self, question: str, query_type: str = "qa") -> Dict[str, Any]:
        """Belgeleri sorgula ve AI-powered yanıt üret"""
        
        if not self.retriever:
            return {
                "error": "RAG system not initialized",
                "success": False
            }
        
        try:
            # İlgili dokümanları getir
            relevant_docs = self.retriever.get_relevant_documents(question)
            
            if not relevant_docs:
                return {
                    "answer": "Bu konu hakkında belgelerimde bilgi bulunamadı.",
                    "sources": [],
                    "success": True
                }
            
            # Context hazırla
            context = "\n\n".join([
                f"BELGE: {doc.metadata.get('source', 'Unknown')}\n"
                f"İÇERİK: {doc.page_content}"
                for doc in relevant_docs
            ])
            
            # Prompt seç
            if query_type == "summary":
                prompt = self.summary_prompt.format(context=context)
            else:
                prompt = self.qa_prompt.format(context=context, question=question)
            
            # AI yanıtı simüle et (şimdilik rule-based)
            ai_response = self._generate_response(prompt, relevant_docs, question)
            
            # Kaynak bilgileri hazırla
            sources = [
                {
                    "file_path": doc.metadata.get('source', ''),
                    "score": doc.metadata.get('score', 0),
                    "chunk_id": doc.metadata.get('chunk_id', ''),
                    "preview": doc.page_content[:200] + "..."
                }
                for doc in relevant_docs
            ]
            
            return {
                "answer": ai_response,
                "sources": sources,
                "context": context,
                "query_type": query_type,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in query_documents: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def _generate_response(self, prompt: str, docs: List[Document], question: str) -> str:
        """AI yanıtı üret (Ollama LLM entegrasyonu ile)"""
        
        try:
            # Dokümanlarda context hazırla
            if not docs:
                return "Bu konu hakkında belgelerimde bilgi bulunamadı."
            
            # En iyi eşleşen belgeleri seç
            best_docs = sorted(docs, key=lambda x: x.metadata.get('score', 0), reverse=True)[:3]
            
            # Context metni oluştur
            context_parts = []
            for doc in best_docs:
                source = doc.metadata.get('source', 'Bilinmeyen kaynak')
                content = doc.page_content[:800]  # İlk 800 karakter
                context_parts.append(f"KAYNAK: {os.path.basename(source)}\nİÇERİK: {content}")
            
            context = "\n\n---\n\n".join(context_parts)
            
            # Ollama için optimize edilmiş prompt
            ollama_prompt = f"""Sen bir savunma sanayi belge analiz uzmanısın. Aşağıdaki belgelerden elde ettiğin bilgilere dayanarak kullanıcının sorusunu yanıtla.

BELGE İÇERİKLERİ:
{context}

KULLANICI SORUSU: {question}

YANITLAMA KURALLARI:
1. Sadece verilen belge içeriklerine dayanarak yanıt ver
2. Teknik terimler için açıklamalar yap
3. Güvenlik ve prosedürler önemli ise vurgula
4. Kısa, net ve Türkçe yanıt ver
5. Bilgi yetersizse belirt

YANITUN:"""

            # Ollama API çağrısı
            import requests
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:latest",
                    "prompt": ollama_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Düşük temperature = daha tutarlı yanıtlar
                        "top_p": 0.9,
                        "num_ctx": 4096,
                        "num_predict": 512   # Maksimum yanıt uzunluğu
                    }
                },
                timeout=60  # Timeout'u 60 saniyeye çıkar
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '').strip()
                
                if ai_response:
                    # Kaynak bilgilerini ekle
                    sources = [os.path.basename(doc.metadata.get('source', '')) for doc in best_docs]
                    source_info = f"\n\n**Kaynaklar:** {', '.join(set(sources))}"
                    return ai_response + source_info
                else:
                    return self._fallback_response(docs, question)
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return self._fallback_response(docs, question)
                
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            return self._fallback_response(docs, question)
    
    def _fallback_response(self, docs: List[Document], question: str) -> str:
        """LLM kullanılamadığında geri dönüş yanıtı"""
        
        # Basit rule-based response generation
        key_terms = {
            'güvenlik': 'Güvenlik prosedürleri',
            'prosedür': 'İşletim prosedürleri', 
            'risk': 'Risk değerlendirmesi',
            'teknik': 'Teknik spesifikasyonlar',
            'rapor': 'Rapor ve analiz',
            'sistem': 'Sistem gereksinimleri'
        }
        
        # Soru analizi
        question_lower = question.lower()
        relevant_category = None
        
        for term, category in key_terms.items():
            if term in question_lower:
                relevant_category = category
                break
        
        # Yanıt oluştur
        response_parts = []
        
        if relevant_category:
            response_parts.append(f"**{relevant_category}** konusında bulgular:")
        
        # En iyi eşleşen belgeleri analiz et
        best_docs = sorted(docs, key=lambda x: x.metadata.get('score', 0), reverse=True)[:3]
        
        for i, doc in enumerate(best_docs, 1):
            source = doc.metadata.get('source', 'Bilinmeyen kaynak')
            content_preview = doc.page_content[:300]
            
            response_parts.append(f"\n**Kaynak {i}:** {os.path.basename(source)}")
            response_parts.append(f"**İçerik:** {content_preview}...")
            
            # Score'a göre güvenilirlik
            score = doc.metadata.get('score', 0)
            if score > 0.8:
                confidence = "Yüksek"
            elif score > 0.6:
                confidence = "Orta"
            else:
                confidence = "Düşük"
            
            response_parts.append(f"**Güvenilirlik:** {confidence}")
        
        # Özet ve öneriler
        response_parts.append(f"\n**Özet:** Sorgunuz '{question}' hakkında {len(docs)} belgede ilgili bilgi bulundu.")
        response_parts.append("**Öneri:** Detaylı bilgi için kaynak belgeleri inceleyiniz.")
        
        return "\n".join(response_parts)
    
    def generate_comprehensive_report(self, query: str, max_docs: int = 10) -> Dict[str, Any]:
        """Kapsamlı AI raporu üret"""
        
        try:
            # Geniş kapsamlı arama
            relevant_docs = self.retriever.get_relevant_documents(query)
            
            if not relevant_docs:
                return {
                    "error": "No relevant documents found",
                    "success": False
                }
            
            # Rapor bölümleri
            report_sections = {}
            
            # 1. Executive Summary
            summary_result = self.query_documents(
                f"{query} - kapsamlı özet",
                query_type="summary"
            )
            report_sections["executive_summary"] = summary_result.get("answer", "")
            
            # 2. Key Findings
            findings_result = self.query_documents(
                f"{query} - ana bulgular ve kritik noktalar"
            )
            report_sections["key_findings"] = findings_result.get("answer", "")
            
            # 3. Technical Analysis
            technical_result = self.query_documents(
                f"{query} - teknik analiz ve spesifikasyonlar"
            )
            report_sections["technical_analysis"] = technical_result.get("answer", "")
            
            # 4. Risk Assessment
            risk_result = self.query_documents(
                f"{query} - risk değerlendirmesi ve güvenlik"
            )
            report_sections["risk_assessment"] = risk_result.get("answer", "")
            
            # 5. Recommendations
            recommendations_result = self.query_documents(
                f"{query} - öneriler ve eylem planı"
            )
            report_sections["recommendations"] = recommendations_result.get("answer", "")
            
            # Tüm kaynak belgeleri topla
            all_sources = []
            for doc in relevant_docs:
                all_sources.append({
                    "file_path": doc.metadata.get('source', ''),
                    "score": doc.metadata.get('score', 0),
                    "preview": doc.page_content[:150] + "..."
                })
            
            return {
                "query": query,
                "report_sections": report_sections,
                "sources": all_sources,
                "total_documents": len(relevant_docs),
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {
                "error": str(e),
                "success": False
            }

# Test ve örnek kullanım
def test_rag_system():
    """RAG sistemini test et (domain embedding ile)"""
    
    config = RAGConfig()
    rag = AdvancedRAGSystem(config)
    
    # Test data paths - domain embedding indexi kullan
    index_path = "./data/faiss_domain.index"
    meta_path = "./data/meta_domain.pkl"
    
    # Fallback to regular index if domain index doesn't exist
    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        print("⚠️ Domain-specific index not found, using regular index")
        index_path = "./data/faiss.index"
        meta_path = "./data/meta.pkl"
        
        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            print("❌ FAISS index files not found. Please run embed_index.py first.")
            return
    
    # Initialize with domain embedding
    if rag.initialize(index_path, meta_path, use_domain_embedding=True):
        print("✅ RAG System initialized successfully with domain embedding")
        
        # Test sorguları (defense domain specific)
        test_queries = [
            "İHA güvenlik prosedürleri nelerdir?",
            "Radar sistem gereksinimleri hakkında bilgi ver",
            "TSK tehdit değerlendirmesi nasıl yapılmalı?",
            "F-16 bakım prosedürleri"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: {query}")
            result = rag.query_documents(query)
            
            if result["success"]:
                print(f"✅ Answer: {result['answer'][:200]}...")
                print(f"📚 Sources: {len(result['sources'])} documents")
            else:
                print(f"❌ Error: {result['error']}")
    
    else:
        print("❌ Failed to initialize RAG system")

if __name__ == "__main__":
    test_rag_system()