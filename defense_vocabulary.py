"""
Savunma Sanayi Terminolojisi ve Domain-Specific Vocabulary
"""

import json
import re
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)

class DefenseVocabulary:
    """Savunma sanayi domain-specific vocabulary ve term mapping sistemi"""
    
    def __init__(self):
        self.defense_terms = self._load_defense_terms()
        self.synonyms = self._load_synonyms()
        self.abbreviations = self._load_abbreviations()
        self.technical_terms = self._load_technical_terms()
        
    def _load_defense_terms(self) -> Dict[str, List[str]]:
        """Savunma sanayi temel terimleri"""
        return {
            "silah_sistemleri": [
                "füze", "roket", "mermi", "mühimmat", "bomba", "silah", "silahlanma",
                "atış", "hedef", "nişan", "balistik", "güdümlü", "güdümsüz",
                "anti-tank", "anti-hava", "hava-hava", "hava-yer", "yer-yer"
            ],
            "havacilik": [
                "uçak", "helikopter", "drone", "İHA", "SİHA", "radar", "hava aracı",
                "pilot", "uçuş", "havacılık", "aerodinamik", "motor", "türbin",
                "aviyonik", "navigasyon", "otopilot", "autopilot"
            ],
            "denizcilik": [
                "gemi", "denizaltı", "fırkateyn", "korvet", "destroyer", "kruvazör",
                "torpedo", "mayın", "sonar", "radar", "deniz", "denizci",
                "navtex", "GPS", "seyir", "liman"
            ],
            "kara_kuvvetleri": [
                "tank", "zırhlı", "araç", "kara", "piyade", "asker", "er", "subay",
                "komando", "özel", "harekat", "muharebe", "savaş", "cephe",
                "mevzi", "savunma", "saldırı"
            ],
            "guvenlik": [
                "güvenlik", "emniyet", "koruma", "savunma", "tehdit", "risk",
                "analiz", "değerlendirme", "rapor", "prosedür", "protokol",
                "acil", "alarm", "uyarı", "kritik", "gizli", "mahrem"
            ],
            "teknoloji": [
                "sistem", "yazılım", "donanım", "elektronik", "bilgisayar",
                "ağ", "network", "haberleşme", "iletişim", "sinyal", "frekans",
                "band", "spektrum", "dijital", "analog", "sensör", "dedektör"
            ],
            "lojistik": [
                "lojistik", "tedarik", "ikmal", "malzeme", "yedek", "parça",
                "bakım", "onarım", "servis", "depo", "stok", "envanter",
                "taşıma", "nakliye", "dağıtım", "supply"
            ]
        }
    
    def _load_synonyms(self) -> Dict[str, List[str]]:
        """Terim eş anlamlıları"""
        return {
            "İHA": ["İnsansız Hava Aracı", "drone", "UAV", "unmanned"],
            "SİHA": ["Silahlı İnsansız Hava Aracı", "armed drone", "UCAV"],
            "radar": ["radyo algılama", "RF sensor", "detection system"],
            "sonar": ["ses algılama", "acoustic sensor", "underwater detection"],
            "GPS": ["konum belirleme", "positioning", "navigation", "GNSS"],
            "güvenlik": ["emniyet", "security", "safety", "koruma"],
            "tehdit": ["risk", "danger", "threat", "tehlike"],
            "muharebe": ["savaş", "combat", "battle", "çatışma"],
            "prosedür": ["işlem", "procedure", "protokol", "yöntem"],
            "kritik": ["önemli", "critical", "vital", "hayati"],
            "gizli": ["sınıflandırılmış", "classified", "confidential", "mahrem"]
        }
    
    def _load_abbreviations(self) -> Dict[str, str]:
        """Yaygın kısaltmalar"""
        return {
            "TSK": "Türk Silahlı Kuvvetleri",
            "KKK": "Kara Kuvvetleri Komutanlığı",
            "HvKK": "Hava Kuvvetleri Komutanlığı", 
            "DzKK": "Deniz Kuvvetleri Komutanlığı",
            "J&P": "Jandarma ve Polis",
            "MIT": "Milli İstihbarat Teşkilatı",
            "MSB": "Milli Savunma Bakanlığı",
            "SSB": "Savunma Sanayii Başkanlığı",
            "ASELSAN": "Askeri Elektronik Sanayii",
            "TAI": "Türk Havacılık ve Uzay Sanayii",
            "ROKETSAN": "Roket Sanayii",
            "STM": "Savunma Teknolojileri Mühendislik",
            "HAVELSAN": "Hava Elektronik Sanayii",
            "NATO": "North Atlantic Treaty Organization",
            "RF": "Radio Frequency",
            "EW": "Electronic Warfare",
            "C4ISR": "Command Control Communications Computers Intelligence Surveillance Reconnaissance"
        }
    
    def _load_technical_terms(self) -> Dict[str, str]:
        """Teknik terim açıklamaları"""
        return {
            "balistik": "Mermilerin havadaki hareketini inceleyen bilim dalı",
            "aviyonik": "Havacılık elektroniği sistemleri",
            "sonar": "Ses dalgalarıyla su altı tespit sistemi",
            "radar": "Radyo dalgalarıyla nesne tespit sistemi",
            "GPS": "Global Positioning System - Küresel konum belirleme sistemi",
            "İHA": "İnsansız Hava Aracı - Pilot olmadan kontrol edilen uçak",
            "SİHA": "Silahlı İnsansız Hava Aracı - Silah taşıyan drone",
            "EW": "Elektronik Harp - Düşman elektronik sistemlerini etkisizleştirme",
            "C4ISR": "Komuta Kontrol Haberleşme Bilgisayar İstihbarat Gözetleme Keşif sistemi",
            "FLIR": "Forward Looking Infrared - İleri bakış kızılötesi kamera sistemi"
        }
    
    def expand_query(self, query: str) -> str:
        """Query'yi domain-specific terimlerle genişlet"""
        expanded_terms = []
        query_lower = query.lower()
        
        # Kısaltmaları açıklamalarla değiştir
        for abbr, full_form in self.abbreviations.items():
            if abbr.lower() in query_lower:
                expanded_terms.append(full_form)
        
        # Eş anlamlıları ekle
        for term, synonyms in self.synonyms.items():
            if term.lower() in query_lower:
                expanded_terms.extend(synonyms)
        
        # Orijinal query + genişletilmiş terimler
        if expanded_terms:
            return f"{query} {' '.join(expanded_terms)}"
        
        return query
    
    def get_related_terms(self, term: str) -> List[str]:
        """Bir terimle ilgili terimleri getir"""
        term_lower = term.lower()
        related = []
        
        # Aynı kategorideki terimleri bul
        for category, terms in self.defense_terms.items():
            if term_lower in [t.lower() for t in terms]:
                related.extend([t for t in terms if t.lower() != term_lower])
                break
        
        # Eş anlamlıları ekle
        if term in self.synonyms:
            related.extend(self.synonyms[term])
        
        # Tersine eş anlamlı arama
        for key, synonyms in self.synonyms.items():
            if term_lower in [s.lower() for s in synonyms] and key not in related:
                related.append(key)
        
        return list(set(related))[:10]  # En fazla 10 ilgili terim
    
    def is_defense_term(self, term: str) -> bool:
        """Terimin savunma sanayi terimi olup olmadığını kontrol et"""
        term_lower = term.lower()
        
        # Ana kategorilerde ara
        for category, terms in self.defense_terms.items():
            if term_lower in [t.lower() for t in terms]:
                return True
        
        # Kısaltmalarda ara
        if term.upper() in self.abbreviations:
            return True
        
        # Eş anlamlılarda ara
        for key, synonyms in self.synonyms.items():
            if term_lower == key.lower() or term_lower in [s.lower() for s in synonyms]:
                return True
        
        return False
    
    def get_term_importance_weight(self, term: str) -> float:
        """Terimin önem ağırlığını hesapla"""
        term_lower = term.lower()
        
        # Kritik güvenlik terimleri
        critical_terms = ["güvenlik", "tehdit", "risk", "kritik", "gizli", "alarm"]
        if any(ct in term_lower for ct in critical_terms):
            return 2.0
        
        # Teknik terimler
        if term in self.technical_terms or term.upper() in self.abbreviations:
            return 1.5
        
        # Genel savunma terimleri
        if self.is_defense_term(term):
            return 1.2
        
        return 1.0  # Normal terimler
    
    def save_vocabulary_to_file(self, filepath: str):
        """Vocabulary'yi JSON dosyasına kaydet"""
        vocab_data = {
            "defense_terms": self.defense_terms,
            "synonyms": self.synonyms,
            "abbreviations": self.abbreviations,
            "technical_terms": self.technical_terms
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Vocabulary saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving vocabulary: {e}")
    
    def load_vocabulary_from_file(self, filepath: str):
        """JSON dosyasından vocabulary yükle"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                vocab_data = json.load(f)
            
            self.defense_terms = vocab_data.get("defense_terms", {})
            self.synonyms = vocab_data.get("synonyms", {})
            self.abbreviations = vocab_data.get("abbreviations", {})
            self.technical_terms = vocab_data.get("technical_terms", {})
            
            logger.info(f"Vocabulary loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading vocabulary: {e}")

# Test fonksiyonu
def test_defense_vocabulary():
    """Defense vocabulary sistemini test et"""
    vocab = DefenseVocabulary()
    
    print("=== Defense Vocabulary Test ===")
    
    # Test 1: Query expansion
    test_queries = ["İHA güvenlik", "radar sistemi", "TSK prosedür"]
    for query in test_queries:
        expanded = vocab.expand_query(query)
        print(f"Query: {query}")
        print(f"Expanded: {expanded}\n")
    
    # Test 2: Related terms
    test_terms = ["İHA", "güvenlik", "radar"]
    for term in test_terms:
        related = vocab.get_related_terms(term)
        print(f"Term: {term}")
        print(f"Related: {related}\n")
    
    # Test 3: Term importance
    test_importance = ["güvenlik", "tehdit", "sistem", "normal"]
    for term in test_importance:
        weight = vocab.get_term_importance_weight(term)
        print(f"Term: {term}, Weight: {weight}")

if __name__ == "__main__":
    test_defense_vocabulary()