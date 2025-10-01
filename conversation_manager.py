"""
Conversational Interface Manager
Chat session management, context retention ve multi-turn dialogue
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Chat mesajı veri yapısı"""
    id: str
    session_id: str
    user_id: str
    message_type: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Dict[str, Any]
    timestamp: str
    
@dataclass
class ChatSession:
    """Chat session veri yapısı"""
    session_id: str
    user_id: str
    title: str
    created_at: str
    last_activity: str
    context: Dict[str, Any]
    message_count: int
    is_active: bool

class ConversationManager:
    """Conversational Interface Manager"""
    
    def __init__(self, db_path: str = "./config/users.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Chat tabloları oluştur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Chat sessions tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    context TEXT,  -- JSON
                    message_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Chat messages tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,  -- JSON
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
                )
            ''')
            
            # Chat analytics tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    query_type TEXT,
                    response_time REAL,
                    sources_count INTEGER,
                    user_satisfaction INTEGER,  -- 1-5 rating
                    timestamp TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Chat tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize chat tables: {e}")
    
    def create_session(self, user_id: str, title: str = None) -> str:
        """Yeni chat session oluştur"""
        try:
            session_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            if not title:
                title = f"Chat Session - {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO chat_sessions 
                (session_id, user_id, title, created_at, last_activity, context, message_count, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, title, now, now, json.dumps({}), 0, True))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created new chat session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Chat session bilgilerini getir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_id, user_id, title, created_at, last_activity, 
                       context, message_count, is_active
                FROM chat_sessions WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return ChatSession(
                    session_id=row[0],
                    user_id=row[1],
                    title=row[2],
                    created_at=row[3],
                    last_activity=row[4],
                    context=json.loads(row[5] or '{}'),
                    message_count=row[6],
                    is_active=bool(row[7])
                )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get chat session: {e}")
            return None
    
    def add_message(self, session_id: str, user_id: str, message_type: str, 
                   content: str, metadata: Dict[str, Any] = None) -> str:
        """Chat'e mesaj ekle"""
        try:
            message_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            if metadata is None:
                metadata = {}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Mesajı ekle
            cursor.execute('''
                INSERT INTO chat_messages 
                (message_id, session_id, user_id, message_type, content, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (message_id, session_id, user_id, message_type, content, 
                  json.dumps(metadata), now))
            
            # Session'ı güncelle
            cursor.execute('''
                UPDATE chat_sessions 
                SET last_activity = ?, message_count = message_count + 1
                WHERE session_id = ?
            ''', (now, session_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added message to session {session_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return None
    
    def get_session_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """Session'ın mesajlarını getir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT message_id, session_id, user_id, message_type, content, metadata, timestamp
                FROM chat_messages 
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (session_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            messages = []
            for row in reversed(rows):  # En eski mesajdan başla
                messages.append(ChatMessage(
                    id=row[0],
                    session_id=row[1],
                    user_id=row[2],
                    message_type=row[3],
                    content=row[4],
                    metadata=json.loads(row[5] or '{}'),
                    timestamp=row[6]
                ))
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get session messages: {e}")
            return []
    
    def get_user_sessions(self, user_id: str, limit: int = 20) -> List[ChatSession]:
        """Kullanıcının session'larını getir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_id, user_id, title, created_at, last_activity, 
                       context, message_count, is_active
                FROM chat_sessions 
                WHERE user_id = ?
                ORDER BY last_activity DESC
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                sessions.append(ChatSession(
                    session_id=row[0],
                    user_id=row[1],
                    title=row[2],
                    created_at=row[3],
                    last_activity=row[4],
                    context=json.loads(row[5] or '{}'),
                    message_count=row[6],
                    is_active=bool(row[7])
                ))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []
    
    def update_session_context(self, session_id: str, context_update: Dict[str, Any]):
        """Session context'ini güncelle"""
        try:
            # Mevcut context'i al
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Context'i güncelle
            updated_context = session.context.copy()
            updated_context.update(context_update)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE chat_sessions 
                SET context = ?, last_activity = ?
                WHERE session_id = ?
            ''', (json.dumps(updated_context), datetime.now().isoformat(), session_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session context: {e}")
            return False
    
    def generate_follow_up_questions(self, session_id: str, last_response: str) -> List[str]:
        """Takip soruları üret"""
        try:
            # Son mesajları al
            messages = self.get_session_messages(session_id, limit=5)
            
            # Context analizi
            topics = []
            for msg in messages:
                if msg.message_type == 'user':
                    # Anahtar kelime çıkarımı
                    content_lower = msg.content.lower()
                    if 'güvenlik' in content_lower:
                        topics.append('güvenlik')
                    if 'sistem' in content_lower:
                        topics.append('sistem')
                    if 'risk' in content_lower:
                        topics.append('risk')
                    if 'prosedür' in content_lower:
                        topics.append('prosedür')
            
            # Takip soruları üret
            follow_ups = []
            
            if 'güvenlik' in topics:
                follow_ups.extend([
                    "Bu güvenlik prosedürü hangi durumlar için geçerli?",
                    "Acil durum güvenlik protokolleri nelerdir?",
                    "Güvenlik ihlali durumunda ne yapılmalı?"
                ])
            
            if 'sistem' in topics:
                follow_ups.extend([
                    "Sistem gereksinimleri asgari mi yoksa önerilen mi?",
                    "Hangi işletim sistemleri desteklenmektedir?",
                    "Sistem performansı nasıl optimize edilir?"
                ])
            
            if 'risk' in topics:
                follow_ups.extend([
                    "Risk seviyeleri nasıl belirlenir?",
                    "Yüksek riskli durumlar için ek önlemler var mı?",
                    "Risk azaltma stratejileri nelerdir?"
                ])
            
            # Genel takip soruları
            if not follow_ups:
                follow_ups = [
                    "Bu konu hakkında daha detaylı bilgi alabilir miyim?",
                    "İlgili diğer belgeler nelerdir?",
                    "Pratik uygulama örnekleri verebilir misiniz?"
                ]
            
            return follow_ups[:3]  # En fazla 3 soru
            
        except Exception as e:
            logger.error(f"Failed to generate follow-up questions: {e}")
            return []
    
    def analyze_conversation_intent(self, session_id: str) -> Dict[str, Any]:
        """Konuşma intent analizi"""
        try:
            messages = self.get_session_messages(session_id, limit=10)
            
            analysis = {
                'main_topics': [],
                'query_patterns': [],
                'user_intent': 'information_seeking',
                'complexity_level': 'basic',
                'domain_focus': 'general'
            }
            
            user_messages = [msg for msg in messages if msg.message_type == 'user']
            
            if not user_messages:
                return analysis
            
            # Topic analizi
            all_content = ' '.join([msg.content.lower() for msg in user_messages])
            
            defense_terms = ['güvenlik', 'savunma', 'askeri', 'operasyon', 'strateji']
            technical_terms = ['sistem', 'yazılım', 'donanım', 'teknik', 'spesifikasyon']
            process_terms = ['prosedür', 'süreç', 'adım', 'işlem', 'protokol']
            
            if any(term in all_content for term in defense_terms):
                analysis['domain_focus'] = 'defense'
                analysis['main_topics'].append('Savunma Sanayi')
            
            if any(term in all_content for term in technical_terms):
                analysis['main_topics'].append('Teknik Konular')
            
            if any(term in all_content for term in process_terms):
                analysis['main_topics'].append('İşleyiş ve Prosedürler')
            
            # Complexity analizi
            if len(user_messages) > 5:
                analysis['complexity_level'] = 'advanced'
            elif len(user_messages) > 2:
                analysis['complexity_level'] = 'intermediate'
            
            # Intent analizi
            question_words = ['nasıl', 'nedir', 'neler', 'hangi', 'ne zaman', 'nerede']
            if any(word in all_content for word in question_words):
                analysis['user_intent'] = 'detailed_inquiry'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze conversation intent: {e}")
            return {'error': str(e)}
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Konuşma özeti"""
        try:
            session = self.get_session(session_id)
            messages = self.get_session_messages(session_id)
            
            if not session or not messages:
                return {}
            
            user_messages = [msg for msg in messages if msg.message_type == 'user']
            assistant_messages = [msg for msg in messages if msg.message_type == 'assistant']
            
            summary = {
                'session_id': session_id,
                'title': session.title,
                'duration': self._calculate_session_duration(session),
                'total_messages': len(messages),
                'user_messages': len(user_messages),
                'assistant_responses': len(assistant_messages),
                'topics_discussed': self._extract_topics(user_messages),
                'last_activity': session.last_activity,
                'intent_analysis': self.analyze_conversation_intent(session_id)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return {}
    
    def _calculate_session_duration(self, session: ChatSession) -> str:
        """Session süresi hesapla"""
        try:
            created = datetime.fromisoformat(session.created_at)
            last_activity = datetime.fromisoformat(session.last_activity)
            duration = last_activity - created
            
            if duration.total_seconds() < 60:
                return f"{int(duration.total_seconds())} saniye"
            elif duration.total_seconds() < 3600:
                return f"{int(duration.total_seconds() / 60)} dakika"
            else:
                hours = int(duration.total_seconds() / 3600)
                minutes = int((duration.total_seconds() % 3600) / 60)
                return f"{hours} saat {minutes} dakika"
                
        except Exception:
            return "Bilinmiyor"
    
    def _extract_topics(self, messages: List[ChatMessage]) -> List[str]:
        """Mesajlardan topic'leri çıkar"""
        topics = set()
        
        for msg in messages:
            content = msg.content.lower()
            
            if any(word in content for word in ['güvenlik', 'emniyet', 'korunma']):
                topics.add('Güvenlik')
            if any(word in content for word in ['sistem', 'yazılım', 'donanım']):
                topics.add('Sistem/Teknoloji')
            if any(word in content for word in ['prosedür', 'işlem', 'adım']):
                topics.add('Prosedürler')
            if any(word in content for word in ['risk', 'tehlike', 'tehdit']):
                topics.add('Risk Yönetimi')
            if any(word in content for word in ['rapor', 'analiz', 'değerlendirme']):
                topics.add('Raporlama')
        
        return list(topics)

# Global conversation manager
conversation_manager = ConversationManager()