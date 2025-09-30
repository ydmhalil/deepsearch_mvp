"""
Document Insights Engine
Advanced content analysis and business intelligence system for documents
Provides automated insights, trends, and recommendations for KOBİ businesses
"""

import sqlite3
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import os
from typing import List, Dict, Any, Tuple
import numpy as np

class DocumentInsightsEngine:
    def __init__(self, db_path='config/users.db', data_dir='data'):
        self.db_path = db_path
        self.data_dir = data_dir
        
        # Turkish business keywords and categories
        self.business_categories = {
            'finance': ['bütçe', 'gelir', 'gider', 'kar', 'zarar', 'muhasebe', 'fatura', 'ödeme', 'kredi', 'yatırım'],
            'hr': ['personel', 'çalışan', 'işe alım', 'maaş', 'izin', 'performans', 'eğitim', 'departman'],
            'operations': ['süreç', 'prosedür', 'operasyon', 'üretim', 'kalite', 'tedarik', 'envanter', 'lojistik'],
            'sales': ['satış', 'müşteri', 'pazarlama', 'kampanya', 'hedef', 'gelir', 'sipariş', 'teklif'],
            'legal': ['sözleşme', 'hukuk', 'yasal', 'mevzuat', 'compliance', 'denetim', 'lisans', 'patent'],
            'strategy': ['strateji', 'planlama', 'hedef', 'vizon', 'misyon', 'analiz', 'rakip', 'pazar']
        }
        
        # Document importance keywords
        self.importance_keywords = {
            'high': ['kritik', 'acil', 'önemli', 'strateji', 'karar', 'yönetim', 'ceo', 'müdür'],
            'medium': ['proje', 'plan', 'rapor', 'analiz', 'değerlendirme', 'sunum'],
            'low': ['bilgi', 'not', 'taslak', 'geçici', 'test', 'deneme']
        }
        
        # Trend detection patterns
        self.trend_patterns = {
            'growth': ['artış', 'büyüme', 'yükseliş', 'gelişim', 'iyileşme', 'pozitif'],
            'decline': ['düşüş', 'azalış', 'gerileme', 'olumsuz', 'negatif', 'kötüleşme'],
            'stable': ['stabil', 'sabit', 'değişmez', 'düzenli', 'normal', 'standart']
        }
        
        # Action-oriented keywords
        self.action_keywords = {
            'planning': ['plan', 'hazırlık', 'tasarım', 'strateji', 'hedef'],
            'execution': ['uygulama', 'gerçekleştirme', 'başlatma', 'devreye alma'],
            'monitoring': ['takip', 'izleme', 'kontrol', 'denetim', 'ölçüm'],
            'improvement': ['iyileştirme', 'geliştirme', 'optimizasyon', 'verimlilik']
        }
        
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def analyze_document_content(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Comprehensive document content analysis
        Returns detailed insights about document content and business relevance
        """
        analysis = {
            'file_path': file_path,
            'content_length': len(content),
            'word_count': len(content.split()),
            'analysis_timestamp': datetime.now().isoformat(),
            'business_categories': self._categorize_content(content),
            'importance_level': self._assess_importance(content),
            'key_topics': self._extract_key_topics(content),
            'sentiment_indicators': self._analyze_sentiment(content),
            'action_items': self._extract_action_items(content),
            'business_entities': self._extract_business_entities(content),
            'document_type': self._classify_document_type(file_path, content),
            'readability_score': self._calculate_readability(content),
            'urgency_indicators': self._detect_urgency(content)
        }
        
        return analysis
        
    def _categorize_content(self, content: str) -> Dict[str, float]:
        """Categorize content into business areas"""
        content_lower = content.lower()
        categories = {}
        
        for category, keywords in self.business_categories.items():
            score = 0
            for keyword in keywords:
                # Count keyword occurrences with weight
                occurrences = len(re.findall(r'\b' + re.escape(keyword) + r'\b', content_lower))
                score += occurrences
            
            # Normalize score based on content length
            categories[category] = min(score / max(len(content.split()) / 100, 1), 10.0)
            
        return categories
        
    def _assess_importance(self, content: str) -> str:
        """Assess document importance level"""
        content_lower = content.lower()
        importance_scores = {'high': 0, 'medium': 0, 'low': 0}
        
        for level, keywords in self.importance_keywords.items():
            for keyword in keywords:
                occurrences = len(re.findall(r'\b' + re.escape(keyword) + r'\b', content_lower))
                importance_scores[level] += occurrences
                
        # Determine highest scoring category
        max_level = max(importance_scores, key=importance_scores.get)
        return max_level if importance_scores[max_level] > 0 else 'medium'
        
    def _extract_key_topics(self, content: str) -> List[str]:
        """Extract key topics and themes from content"""
        # Simple keyword extraction based on frequency
        words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞIÖÇ]{3,}\b', content.lower())
        
        # Remove common stop words
        stop_words = {
            'için', 'olan', 'olarak', 'olan', 'veya', 'ancak', 'fakat', 'çünkü',
            'eğer', 'hangi', 'nerede', 'nasıl', 'neden', 'böyle', 'şöyle',
            'her', 'bir', 'iki', 'üç', 'birkaç', 'çok', 'az', 'fazla'
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Get most frequent words
        word_freq = Counter(filtered_words)
        key_topics = [word for word, freq in word_freq.most_common(10) if freq > 1]
        
        return key_topics
        
    def _analyze_sentiment(self, content: str) -> Dict[str, int]:
        """Basic sentiment analysis for Turkish content"""
        content_lower = content.lower()
        
        positive_words = [
            'başarı', 'iyi', 'mükemmel', 'harika', 'olumlu', 'artış', 'büyüme',
            'gelişim', 'kazanç', 'verimli', 'etkili', 'kaliteli', 'güvenli'
        ]
        
        negative_words = [
            'başarısız', 'kötü', 'olumsuz', 'problem', 'sorun', 'hata', 'kayıp',
            'düşüş', 'gerileme', 'risk', 'tehlike', 'yetersiz', 'eksik'
        ]
        
        neutral_words = [
            'normal', 'standart', 'ortalama', 'rutin', 'düzenli', 'sabit'
        ]
        
        sentiment_scores = {
            'positive': sum(len(re.findall(r'\b' + re.escape(word) + r'\b', content_lower)) for word in positive_words),
            'negative': sum(len(re.findall(r'\b' + re.escape(word) + r'\b', content_lower)) for word in negative_words),
            'neutral': sum(len(re.findall(r'\b' + re.escape(word) + r'\b', content_lower)) for word in neutral_words)
        }
        
        return sentiment_scores
        
    def _extract_action_items(self, content: str) -> List[str]:
        """Extract potential action items from content"""
        action_patterns = [
            r'(yapılması gereken[^.!?]*[.!?])',
            r'(planlanmaktadır[^.!?]*[.!?])',
            r'(uygulanacak[^.!?]*[.!?])',
            r'(gereklidir[^.!?]*[.!?])',
            r'(önerilir[^.!?]*[.!?])',
            r'(karar verilmiştir[^.!?]*[.!?])'
        ]
        
        action_items = []
        for pattern in action_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            action_items.extend(matches)
            
        return action_items[:5]  # Limit to top 5 action items
        
    def _extract_business_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract business entities like dates, numbers, names"""
        entities = {
            'dates': [],
            'amounts': [],
            'percentages': [],
            'names': []
        }
        
        # Extract dates
        date_patterns = [
            r'\d{1,2}[./]\d{1,2}[./]\d{4}',
            r'\d{4}[./]\d{1,2}[./]\d{1,2}',
            r'\d{1,2}\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            entities['dates'].extend(re.findall(pattern, content))
            
        # Extract monetary amounts
        amount_patterns = [
            r'\d+(?:[.,]\d+)?\s*(?:TL|₺|USD|\$|EUR|€)',
            r'\d+(?:[.,]\d+)?\s*(?:lira|dolar|euro)'
        ]
        
        for pattern in amount_patterns:
            entities['amounts'].extend(re.findall(pattern, content))
            
        # Extract percentages
        percentage_pattern = r'\%\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?\s*\%'
        entities['percentages'] = re.findall(percentage_pattern, content)
        
        # Extract potential names (capitalized words)
        name_pattern = r'\b[A-ZĞÜŞIÖÇ][a-zğüşıöç]+\s+[A-ZĞÜŞIÖÇ][a-zğüşıöç]+\b'
        entities['names'] = re.findall(name_pattern, content)
        
        # Limit results
        for key in entities:
            entities[key] = list(set(entities[key]))[:5]
            
        return entities
        
    def _classify_document_type(self, file_path: str, content: str) -> str:
        """Classify document type based on filename and content"""
        filename = os.path.basename(file_path).lower()
        content_lower = content.lower()
        
        # Document type patterns
        type_patterns = {
            'contract': ['sözleşme', 'kontrat', 'anlaşma'],
            'report': ['rapor', 'analiz', 'değerlendirme'],
            'invoice': ['fatura', 'invoice', 'makbuz'],
            'policy': ['politika', 'prosedür', 'kural'],
            'presentation': ['sunum', 'presentation', 'slide'],
            'manual': ['kılavuz', 'manual', 'rehber'],
            'letter': ['mektup', 'yazı', 'resmi yazı'],
            'memo': ['not', 'memo', 'hatırlatma']
        }
        
        # Check filename first
        for doc_type, keywords in type_patterns.items():
            if any(keyword in filename for keyword in keywords):
                return doc_type
                
        # Check content
        type_scores = {}
        for doc_type, keywords in type_patterns.items():
            score = sum(len(re.findall(r'\b' + re.escape(keyword) + r'\b', content_lower)) for keyword in keywords)
            if score > 0:
                type_scores[doc_type] = score
                
        return max(type_scores, key=type_scores.get) if type_scores else 'general'
        
    def _calculate_readability(self, content: str) -> float:
        """Calculate simple readability score"""
        sentences = len(re.split(r'[.!?]+', content))
        words = len(content.split())
        
        if sentences == 0:
            return 0.0
            
        avg_sentence_length = words / sentences
        
        # Simple readability score (lower is more readable)
        # Based on average sentence length
        if avg_sentence_length < 15:
            return 8.0  # Easy
        elif avg_sentence_length < 25:
            return 6.0  # Medium
        else:
            return 4.0  # Hard
            
    def _detect_urgency(self, content: str) -> List[str]:
        """Detect urgency indicators in content"""
        urgency_keywords = [
            'acil', 'ivedi', 'derhal', 'hemen', 'çabuk', 'hızlı',
            'kritik', 'önemli', 'son tarih', 'deadline', 'asap'
        ]
        
        content_lower = content.lower()
        found_urgency = []
        
        for keyword in urgency_keywords:
            if keyword in content_lower:
                found_urgency.append(keyword)
                
        return found_urgency
        
    def generate_content_trends(self, days_back: int = 30) -> Dict[str, Any]:
        """Analyze content trends over time"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get recent search queries to understand content interest
        cursor.execute('''
            SELECT query, timestamp, results_count
            FROM search_logs 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        ''', (datetime.now() - timedelta(days=days_back),))
        
        searches = cursor.fetchall()
        conn.close()
        
        trends = {
            'topic_trends': self._analyze_topic_trends(searches),
            'search_patterns': self._analyze_search_patterns(searches),
            'content_demand': self._analyze_content_demand(searches),
            'time_patterns': self._analyze_time_patterns(searches)
        }
        
        return trends
        
    def _analyze_topic_trends(self, searches: List) -> Dict[str, Any]:
        """Analyze trending topics from search queries"""
        all_queries = [search['query'].lower() for search in searches if search['query']]
        
        # Extract words from all queries
        all_words = []
        for query in all_queries:
            words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞIÖÇ]{3,}\b', query)
            all_words.extend(words)
            
        # Count word frequencies
        word_freq = Counter(all_words)
        
        # Categorize trending words
        trending_topics = {}
        for category, keywords in self.business_categories.items():
            category_words = []
            for word, freq in word_freq.most_common(50):
                if word in keywords or any(keyword in word for keyword in keywords):
                    category_words.append({'word': word, 'frequency': freq})
            trending_topics[category] = category_words[:5]
            
        return trending_topics
        
    def _analyze_search_patterns(self, searches: List) -> Dict[str, Any]:
        """Analyze search behavior patterns"""
        patterns = {
            'avg_results_per_search': np.mean([s['results_count'] for s in searches]) if searches else 0,
            'zero_result_queries': len([s for s in searches if s['results_count'] == 0]),
            'high_result_queries': len([s for s in searches if s['results_count'] > 10]),
            'query_length_avg': np.mean([len(s['query'].split()) for s in searches if s['query']]) if searches else 0
        }
        
        return patterns
        
    def _analyze_content_demand(self, searches: List) -> List[Dict[str, Any]]:
        """Identify content gaps and high-demand topics"""
        # Queries with zero results indicate content gaps
        zero_result_queries = [s['query'] for s in searches if s['results_count'] == 0 and s['query']]
        
        # Count similar queries
        demand_analysis = []
        query_groups = defaultdict(int)
        
        for query in zero_result_queries:
            # Group similar queries (simple similarity)
            key_words = sorted(re.findall(r'\b[a-zA-ZğüşıöçĞÜŞIÖÇ]{3,}\b', query.lower()))
            if key_words:
                group_key = ' '.join(key_words[:3])  # Use first 3 keywords as group
                query_groups[group_key] += 1
                
        # Convert to list with recommendations
        for topic, frequency in sorted(query_groups.items(), key=lambda x: x[1], reverse=True)[:10]:
            demand_analysis.append({
                'topic': topic,
                'demand_frequency': frequency,
                'recommendation': f"'{topic}' konusunda içerik eksikliği var. Bu alanda belge eklenmesi önerilir."
            })
            
        return demand_analysis
        
    def _analyze_time_patterns(self, searches: List) -> Dict[str, Any]:
        """Analyze temporal patterns in content access"""
        if not searches:
            return {}
            
        # Group by hour
        hourly_patterns = defaultdict(int)
        daily_patterns = defaultdict(int)
        
        for search in searches:
            timestamp = datetime.fromisoformat(search['timestamp'].replace('Z', '+00:00'))
            hour = timestamp.hour
            day = timestamp.strftime('%A')
            
            hourly_patterns[hour] += 1
            daily_patterns[day] += 1
            
        return {
            'peak_hours': sorted(hourly_patterns.items(), key=lambda x: x[1], reverse=True)[:3],
            'busy_days': sorted(daily_patterns.items(), key=lambda x: x[1], reverse=True)[:3],
            'total_searches': len(searches)
        }
        
    def generate_business_recommendations(self, analysis_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable business recommendations based on analysis"""
        recommendations = []
        
        # Content optimization recommendations
        trends = analysis_data.get('content_trends', {})
        content_demand = trends.get('content_demand', [])
        
        if content_demand:
            recommendations.append({
                'type': 'content_gap',
                'priority': 'high',
                'title': 'İçerik Eksikliği Tespit Edildi',
                'description': f"{len(content_demand)} farklı konuda içerik eksikliği var",
                'action': 'Eksik konularda yeni belgeler ekleyin veya mevcut belgeleri genişletin',
                'impact': 'Arama başarı oranını %15-25 artırabilir'
            })
            
        # Search optimization recommendations
        patterns = trends.get('search_patterns', {})
        zero_results = patterns.get('zero_result_queries', 0)
        
        if zero_results > 10:
            recommendations.append({
                'type': 'search_optimization',
                'priority': 'medium',
                'title': 'Arama Başarısızlık Oranı Yüksek',
                'description': f"{zero_results} arama sonuçsuz kaldı",
                'action': 'Belge indexleme ve arama algoritması optimizasyonu yapın',
                'impact': 'Kullanıcı memnuniyetini artırır'
            })
            
        # Usage pattern recommendations
        time_patterns = trends.get('time_patterns', {})
        peak_hours = time_patterns.get('peak_hours', [])
        
        if peak_hours:
            top_hour = peak_hours[0][0]
            recommendations.append({
                'type': 'system_optimization',
                'priority': 'low',
                'title': 'Yoğun Kullanım Saatleri',
                'description': f"Saat {top_hour}:00'da en yoğun kullanım",
                'action': 'Bu saatlerde sistem performansını izleyin',
                'impact': 'Sistem stabilitesini artırır'
            })
            
        # Business intelligence recommendations
        if analysis_data.get('document_analytics'):
            doc_count = analysis_data['document_analytics'].get('total_documents', 0)
            if doc_count < 50:
                recommendations.append({
                    'type': 'content_expansion',
                    'priority': 'medium',
                    'title': 'Belge Arşivi Genişletilmeli',
                    'description': f"Sadece {doc_count} belge mevcut",
                    'action': 'Daha fazla kurumsal belge yükleyerek sistemi zenginleştirin',
                    'impact': 'Arama kalitesini ve kapsamını artırır'
                })
                
        return recommendations
        
    def save_analysis_to_db(self, analysis: Dict[str, Any]):
        """Save document analysis results to database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Create document_analysis table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS document_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE,
                    analysis_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert or update analysis
            cursor.execute('''
                INSERT OR REPLACE INTO document_analysis 
                (file_path, analysis_data, updated_at)
                VALUES (?, ?, ?)
            ''', (
                analysis['file_path'],
                json.dumps(analysis, ensure_ascii=False),
                datetime.now()
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Analysis save error: {e}")
        finally:
            conn.close()
            
    def get_analysis_from_db(self, file_path: str) -> Dict[str, Any]:
        """Retrieve document analysis from database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT analysis_data FROM document_analysis 
                WHERE file_path = ?
            ''', (file_path,))
            
            result = cursor.fetchone()
            if result:
                return json.loads(result['analysis_data'])
                
        except Exception as e:
            print(f"Analysis retrieve error: {e}")
        finally:
            conn.close()
            
        return {}

# Global insights engine instance
insights_engine = DocumentInsightsEngine()